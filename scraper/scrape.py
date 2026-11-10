#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kamu personel alımı haberlerini toplar.

- Haber sitelerinin RSS akışlarını ve Google Haberler aramalarını tarar
- Personel alımıyla ilgili olanları süzer
- Haberde geçen ili (81 il) tespit eder
- Sonucu data/ilanlar.json dosyasına yazar (öncekilerle birleştirerek)

Yalnızca Python standart kütüphanesini kullanır, kurulum gerekmez.

Kullanım:
    python3 scraper/scrape.py            # tam tarama (genel akışlar + her il için arama)
    python3 scraper/scrape.py --hizli    # il bazlı aramaları atla
"""

import argparse
import hashlib
import html
import json
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from districts import ALIASES, DISTRICTS, RISKY_DISTRICTS  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
CONFIG = Path(__file__).resolve().parent / "sources.json"
DEFAULT_OUT = ROOT / "data" / "ilanlar.json"

KEEP_DAYS = 90        # bundan eski kayıtlar silinir
MAX_ITEMS = 3000
UA = "Mozilla/5.0 (compatible; KamuPersonelTakip/1.0)"
TR_TZ = timezone(timedelta(hours=3))

# --------------------------------------------------------------------------
# İller
# --------------------------------------------------------------------------

PROVINCES = [
    ("01", "Adana", ()), ("02", "Adıyaman", ()), ("03", "Afyonkarahisar", ("Afyon",)),
    ("04", "Ağrı", ()), ("05", "Amasya", ()), ("06", "Ankara", ()), ("07", "Antalya", ()),
    ("08", "Artvin", ()), ("09", "Aydın", ()), ("10", "Balıkesir", ()), ("11", "Bilecik", ()),
    ("12", "Bingöl", ()), ("13", "Bitlis", ()), ("14", "Bolu", ()), ("15", "Burdur", ()),
    ("16", "Bursa", ()), ("17", "Çanakkale", ()), ("18", "Çankırı", ()), ("19", "Çorum", ()),
    ("20", "Denizli", ()), ("21", "Diyarbakır", ()), ("22", "Edirne", ()), ("23", "Elazığ", ()),
    ("24", "Erzincan", ()), ("25", "Erzurum", ()), ("26", "Eskişehir", ()),
    ("27", "Gaziantep", ("Antep",)), ("28", "Giresun", ()), ("29", "Gümüşhane", ()),
    ("30", "Hakkâri", ()), ("31", "Hatay", ()), ("32", "Isparta", ()), ("33", "Mersin", ()),
    ("34", "İstanbul", ()), ("35", "İzmir", ()), ("36", "Kars", ()), ("37", "Kastamonu", ()),
    ("38", "Kayseri", ()), ("39", "Kırklareli", ()), ("40", "Kırşehir", ()), ("41", "Kocaeli", ()),
    ("42", "Konya", ()), ("43", "Kütahya", ()), ("44", "Malatya", ()), ("45", "Manisa", ()),
    ("46", "Kahramanmaraş", ("Maraş",)), ("47", "Mardin", ()), ("48", "Muğla", ()),
    ("49", "Muş", ()), ("50", "Nevşehir", ()), ("51", "Niğde", ()), ("52", "Ordu", ()),
    ("53", "Rize", ()), ("54", "Sakarya", ()), ("55", "Samsun", ()), ("56", "Siirt", ()),
    ("57", "Sinop", ()), ("58", "Sivas", ()), ("59", "Tekirdağ", ()), ("60", "Tokat", ()),
    ("61", "Trabzon", ()), ("62", "Tunceli", ()), ("63", "Şanlıurfa", ("Urfa",)),
    ("64", "Uşak", ()), ("65", "Van", ()), ("66", "Yozgat", ()), ("67", "Zonguldak", ()),
    ("68", "Aksaray", ()), ("69", "Bayburt", ()), ("70", "Karaman", ()), ("71", "Kırıkkale", ()),
    ("72", "Batman", ()), ("73", "Şırnak", ()), ("74", "Bartın", ()), ("75", "Ardahan", ()),
    ("76", "Iğdır", ()), ("77", "Yalova", ()), ("78", "Karabük", ()), ("79", "Kilis", ()),
    ("80", "Osmaniye", ()), ("81", "Düzce", ()),
]

_TR_MAP = str.maketrans({"ç": "c", "ğ": "g", "ı": "i", "ö": "o", "ş": "s", "ü": "u",
                         "â": "a", "î": "i", "û": "u"})


def fold(s: str) -> str:
    """Türkçe harfleri ASCII'ye indirip küçültür; ' işaretlerini sadeleştirir."""
    s = s.replace("İ", "i").replace("I", "ı").lower().translate(_TR_MAP)
    return re.sub(r"[’‘ʼ`´]", "'", s)


# Bu adlar sıradan kelimeyle de karışır (ordu, van, tokat, ağrı, batman):
# yalnızca büyük harfle ve ek/kurum adıyla birlikte geçerse il sayılır.
AMBIGUOUS = {"Van", "Ordu", "Batman", "Tokat", "Ağrı"}
_AMB_NAMES = "Van|VAN|Ordu|ORDU|Batman|BATMAN|Tokat|TOKAT|Ağrı|AĞRI"
AMBIGUOUS_RE = re.compile(
    r"(?<![A-Za-zÇĞİÖŞÜçğıöşü])(" + _AMB_NAMES + r")"
    r"(?:['’ʼ]\w+|\s+(?:Büyükşehir|Belediye\w*|Valili\w*|İli?\b|Üniversite\w*|Adliye\w*"
    r"|Emniyet|Eğitim\w*|Sağlık\w*|Devlet\s+Hastane\w*|Kaymakaml\w*|İl\s+Özel))"
)
AMB_TO_PLAKA = {"van": "65", "ordu": "52", "batman": "72", "tokat": "60", "agri": "04"}

# Ek alabilen ad biçimleri: Ankara'da, Ankarada, Ankara'nın ...
_SUFFIX = r"(?:da|de|ta|te|dan|den|tan|ten|nin|nun|in|un|li|lu|ya|ye|daki|deki)"


def _build_province_patterns():
    pats = []
    for plaka, ad, aliases in PROVINCES:
        if ad in AMBIGUOUS:
            continue
        alts = []
        for n in (ad, *aliases):
            f = re.escape(fold(n))
            if len(fold(n)) >= 5:
                alts.append(f + r"(?:'[a-z]*|" + _SUFFIX + r"(?![a-z])|(?![a-z]))")
            else:  # kısa adlarda (Muş, Rize, Kars, Bolu) yalnızca kesme işareti ya da kelime sonu
                alts.append(f + r"(?:'[a-z]*|(?![a-z]))")
        pats.append((plaka, re.compile(r"(?<![a-z0-9])(?:" + "|".join(alts) + r")")))
    return pats


_PROVINCE_PATTERNS = _build_province_patterns()


def _name_pattern(name: str):
    f = fold(name)
    if len(f) >= 5:
        body = re.escape(f) + r"(?:'[a-z]*|" + _SUFFIX + r"(?![a-z])|(?![a-z]))"
    else:
        body = re.escape(f) + r"(?:'[a-z]*|(?![a-z]))"
    return re.compile(r"(?<![a-z0-9])" + body)


_DISTRICT_PATTERNS = [(p, _name_pattern(n)) for p, n in DISTRICTS]
_RISKY_PATTERNS = [(p, _name_pattern(n)) for p, n in RISKY_DISTRICTS]
_ALIAS_PATTERNS = [(p, re.compile(r"(?<![a-z0-9])" + re.escape(fold(n)) + r"(?![a-z0-9])")) for p, n in ALIASES]
_BELEDIYE_RE = re.compile(r"belediye|kaymakam|ilcesi|ilcede|ilcenin")
_NATIONAL_RE = re.compile(r"\b81 il|tum iller|turkiye genel|butun iller|tum illerde|il genelinde 81")


def detect_provinces(text: str):
    """Metinde geçen il ve ilçelerin plaka kodları (ilçe → bağlı olduğu il).

    4'ten fazla il ya da '81 il' ifadesi → ülke geneli (boş liste).
    """
    f = fold(text)
    if _NATIONAL_RE.search(f):
        return []
    found = set()
    for plaka, rx in _PROVINCE_PATTERNS:
        if rx.search(f):
            found.add(plaka)
    for plaka, rx in _DISTRICT_PATTERNS:
        if rx.search(f):
            found.add(plaka)
    for plaka, rx in _ALIAS_PATTERNS:
        if rx.search(f):
            found.add(plaka)
    if _BELEDIYE_RE.search(f):
        for plaka, rx in _RISKY_PATTERNS:
            if rx.search(f):
                found.add(plaka)
    for m in AMBIGUOUS_RE.finditer(text):
        found.add(AMB_TO_PLAKA[fold(m.group(1))])
    found = sorted(found)
    return [] if len(found) > 4 else found


# --------------------------------------------------------------------------
# İlgililik ve kategori
# --------------------------------------------------------------------------

_ROLE = (r"personel|isci|memur|zabita|kadrolu|sozlesmeli|kpss|ogretmen|bekci|guvenlik gorevlisi|"
         r"polis|jandarma|subay|astsubay|uzman erbas|hemsire|ebe\b|doktor|saglik personeli|itfaiye|"
         r"sofor|temizlik|infaz koruma|gardiyan|imam|din gorevlisi|is ilani|istihdam|eleman|"
         r"muhendis|avukat|hakim|savci|teknisyen|stajyer|hizmetli|bilirkisi|ogretim uyesi|"
         r"arastirma gorevlisi|sivil savunma|isg uzmani|usta ogretici|koruma ve guvenlik")
_INTENT = (r"alim|alinacak|alinir|alacak|aliyor|alimi|ilan|basvuru|istihdam|atama|"
           r"eleman ariyor|ise alim|is firsati|kontenjan|kura")
ROLE_RE = re.compile(r"(?<![a-z])(?:" + _ROLE + r")")
INTENT_RE = re.compile(r"(?<![a-z])(?:" + _INTENT + r")")
EXCLUDE_RE = re.compile(r"super lig|transfer|futbol|teknik direktor|hakem|maci|mac sonu|"
                        r"gol attı|gol atti|basketbol|voleybol|burs ilani|ilan edildi")


def is_relevant(title: str, summary: str = "") -> bool:
    f = fold(f"{title} {summary}")
    if EXCLUDE_RE.search(fold(title)):
        return False
    return bool(ROLE_RE.search(f) and INTENT_RE.search(f))


CATEGORIES = [
    ("Sağlık", r"saglik|hemsire|doktor|ebe\b|hastane|tibbi"),
    ("Eğitim", r"ogretmen|egitim|okul|universite|ogretim uyesi|akademik|arastirma gorevlisi"),
    ("Güvenlik", r"polis|jandarma|subay|astsubay|uzman erbas|bekci|asker|guvenlik|infaz|gardiyan|sivil savunma|mskm|tsk"),
    ("Belediye", r"belediye|zabita|itfaiye|buyuksehir"),
    ("Memur / KPSS", r"memur|kpss|sozlesmeli|kadrolu|bakanlik|mudurlugu|kamu"),
    ("İşçi", r"isci|temizlik|sofor|hizmetli|usta ogretici|typ\b|iskur"),
]


def categorize(title: str, summary: str = "") -> str:
    f = fold(f"{title} {summary}")
    for ad, pat in CATEGORIES:
        if re.search(pat, f):
            return ad
    return "Diğer"


# --------------------------------------------------------------------------
# Ağ ve ayrıştırma
# --------------------------------------------------------------------------

def fetch(url: str, timeout: int = 20, retries: int = 2) -> bytes:
    err = None
    for i in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": UA,
                "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, */*",
            })
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception as e:  # noqa: BLE001
            err = e
            time.sleep(1.5 * (i + 1))
    raise err


def _tag(el) -> str:
    return el.tag.rsplit("}", 1)[-1] if isinstance(el.tag, str) else ""


def parse_feed(data: bytes):
    try:
        root = ET.fromstring(data)
    except ET.ParseError:
        root = ET.fromstring(re.sub(rb"[\x00-\x08\x0b\x0c\x0e-\x1f]", b"", data))
    out = []
    for el in root.iter():
        if _tag(el) not in ("item", "entry"):
            continue
        d = {"title": "", "link": "", "summary": "", "date": "", "source": ""}
        for ch in el:
            t, txt = _tag(ch), (ch.text or "").strip()
            if t == "title" and not d["title"]:
                d["title"] = txt
            elif t == "link" and not d["link"]:
                d["link"] = ch.get("href") or txt
            elif t in ("description", "summary", "content") and not d["summary"]:
                d["summary"] = txt
            elif t in ("pubDate", "published", "updated", "date") and not d["date"]:
                d["date"] = txt
            elif t == "source" and not d["source"]:
                d["source"] = txt
        if d["title"] and d["link"]:
            out.append(d)
    return out


def clean_text(s: str, limit: int = 280) -> str:
    s = re.sub(r"<[^>]+>", " ", html.unescape(s or ""))
    s = re.sub(r"\s+", " ", s).strip()
    return s if len(s) <= limit else s[: limit - 1].rstrip() + "…"


def parse_date(s: str):
    now = datetime.now(timezone.utc)
    dt = None
    if s:
        try:
            dt = parsedate_to_datetime(s)
        except Exception:  # noqa: BLE001
            try:
                dt = datetime.fromisoformat(s.strip().replace("Z", "+00:00"))
            except Exception:  # noqa: BLE001
                dt = None
    if dt is None:
        return now
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=TR_TZ)
    dt = dt.astimezone(timezone.utc)
    return min(dt, now)


def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def title_key(title: str) -> str:
    return re.sub(r"[^a-z0-9]", "", fold(title))[:90]


def item_id(title: str) -> str:
    return hashlib.sha1(title_key(title).encode()).hexdigest()[:12]


def google_news_url(query: str) -> str:
    q = urllib.parse.quote_plus(f"{query} when:30d")
    return f"https://news.google.com/rss/search?q={q}&hl=tr&gl=TR&ceid=TR:tr"


def safe_url(u: str) -> bool:
    return u.startswith("http://") or u.startswith("https://")


# --------------------------------------------------------------------------
# Ana akış
# --------------------------------------------------------------------------

AYLAR = {"ocak": 1, "subat": 2, "mart": 3, "nisan": 4, "mayis": 5, "haziran": 6, "temmuz": 7,
         "agustos": 8, "eylul": 9, "ekim": 10, "kasim": 11, "aralik": 12}
_ROW = re.compile(r'<a[^>]+href="(?P<u>(?:https?://ilan\.memurlar\.net)?/ilan/\d+/[^"]+\.html)"[^>]*>(?P<b>.*?)</a>',
                  re.S | re.I)


def parse_html_list(data: bytes):
    """ilan.memurlar.net liste sayfası: bağlantı + 'N Ay' biçiminde tarih (yıl yok)."""
    txt = data.decode("utf-8", "replace")
    now = datetime.now(TR_TZ)
    out, seen = [], set()
    for m in _ROW.finditer(txt):
        link = m.group("u")
        if link.startswith("/"):
            link = "https://ilan.memurlar.net" + link
        if link in seen:
            continue
        seen.add(link)
        body = clean_text(m.group("b"), 400)
        dm = re.search(r"(\d{1,2})\s+([A-Za-zÇĞİÖŞÜçğıöşü]+)\s*$", body)
        title, date = body, ""
        if dm and fold(dm.group(2)) in AYLAR:
            title = body[: dm.start()].strip()
            mo, dy = AYLAR[fold(dm.group(2))], int(dm.group(1))
            yr = now.year if (mo, dy) <= (now.month, now.day) else now.year - 1
            date = datetime(yr, mo, dy, 12, 0, tzinfo=TR_TZ).isoformat()
        # başlık bağlantı metninde iki kez geçebilir
        h = len(title) // 2
        if h and title[:h].strip() == title[h:].strip():
            title = title[:h].strip()
        if title:
            out.append({"title": title, "link": link, "summary": "", "date": date, "source": ""})
    return out


def collect(job):
    ad, url = job
    try:
        raw = fetch(url)
        entries = parse_html_list(raw) if "/ilan.memurlar.net" in url or url.startswith("https://ilan.memurlar.net") else parse_feed(raw)
        return ad, url, entries, None
    except Exception as e:  # noqa: BLE001
        return ad, url, [], f"{type(e).__name__}: {e}"


def tag_item(it: dict) -> dict:
    text = f'{it["title"]} {it.get("summary", "")}'
    it["provinces"] = detect_provinces(text)
    it["category"] = categorize(it["title"], it.get("summary", ""))
    return it


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hizli", action="store_true", help="il bazlı Google aramalarını atla")
    ap.add_argument("--cikti", default=str(DEFAULT_OUT))
    args = ap.parse_args()
    out_path = Path(args.cikti)

    cfg = json.loads(CONFIG.read_text("utf-8"))
    jobs = [(s["ad"], s["url"]) for s in cfg["rss"]]
    jobs += [(s["ad"], s["url"]) for s in cfg.get("html_listeler", [])]
    jobs += [("Google Haberler", google_news_url(q)) for q in cfg["google_sorgular"]]
    if not args.hizli:
        jobs += [("Google Haberler", google_news_url(cfg["il_sorgusu"].format(il=ad)))
                 for _, ad, _ in PROVINCES]

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=KEEP_DAYS)

    results, errors, ok_sources = [], [], 0
    with ThreadPoolExecutor(max_workers=6) as ex:
        for ad, url, entries, err in ex.map(collect, jobs):
            if err:
                errors.append({"kaynak": ad, "hata": err[:160]})
            else:
                ok_sources += 1
                results.append((ad, entries))

    if ok_sources == 0:
        print("HATA: hiçbir kaynağa ulaşılamadı; mevcut veri korunuyor.", file=sys.stderr)
        for e in errors[:5]:
            print(" -", e["kaynak"], e["hata"], file=sys.stderr)
        sys.exit(1)

    # Önceki kayıtlar
    items = {}
    if out_path.exists():
        try:
            old = json.loads(out_path.read_text("utf-8"))
            for it in old.get("items", []):
                if it.get("demo"):
                    continue
                items[it["id"]] = it
        except Exception:  # noqa: BLE001
            pass

    new_count = 0
    for src_name, entries in results:
        for e in entries:
            title = clean_text(e["title"], 300)
            source = src_name
            if src_name == "Google Haberler":
                if e["source"]:
                    source = clean_text(e["source"], 60)
                    suffix = " - " + source
                    if title.endswith(suffix):
                        title = title[: -len(suffix)].rstrip()
            summary = clean_text(e["summary"])
            if fold(summary)[:40] in fold(title) or src_name == "Google Haberler":
                summary = ""
            link = e["link"].strip()
            if not safe_url(link) or not is_relevant(title, summary):
                continue
            pub = parse_date(e["date"])
            if pub < cutoff:
                continue
            iid = item_id(title)
            if iid in items:
                ex_it = items[iid]
                if source not in ex_it.get("sources", []):
                    ex_it.setdefault("sources", [ex_it["source"]]).append(source)
                if not ex_it.get("summary") and summary:
                    ex_it["summary"] = summary
                continue
            items[iid] = {
                "id": iid, "title": title, "url": link, "source": source,
                "sources": [source], "published": iso(pub), "first_seen": iso(now),
                "summary": summary,
            }
            new_count += 1

    # Eskiyi buda, yeniden etiketle
    final = []
    for it in items.values():
        try:
            pub = datetime.strptime(it["published"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        except Exception:  # noqa: BLE001
            continue
        if pub < cutoff or not is_relevant(it["title"], it.get("summary", "")):
            continue
        final.append(tag_item(it))
    final.sort(key=lambda x: x["published"], reverse=True)
    final = final[:MAX_ITEMS]

    payload = {
        "updated": iso(now),
        "count": len(final),
        "provinces": [{"plaka": p, "ad": ad} for p, ad, _ in PROVINCES],
        "kaynak_sayisi": {"basarili": ok_sources, "hatali": len(errors)},
        "hatalar": errors[:10],
        "items": final,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = out_path.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=1), "utf-8")
    tmp.replace(out_path)

    print(f"{ok_sources}/{len(jobs)} kaynak okundu, {new_count} yeni kayıt, toplam {len(final)} ilan.")
    if errors:
        print(f"{len(errors)} kaynak hata verdi (ilk 3):")
        for e in errors[:3]:
            print(" -", e["kaynak"], e["hata"])


if __name__ == "__main__":
    main()
