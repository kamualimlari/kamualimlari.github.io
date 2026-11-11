#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Doğrulayan tarayıcı (yalnızca Python 3 standart kütüphanesi).

Memurlar.net kategori listelerinde yeni ilanları bulur, her yeni ilanın SAYFASINI açıp
yayın tarihini ("İlan Giriş") ve son başvuru tarihini sayfadan okur, data/ilanlar.json'a ekler.
Yayın tarihi okunamayan ilan eklenmez. Başlık toplayan haber/Google kaynakları kullanılmaz.

Kullanım:  python3 scraper/ilan_tara.py [--en-fazla 40] [--cikti data/ilanlar.json]
"""
import argparse
import hashlib
import html
import json
import re
import sys
import time
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scrape import categorize, detect_provinces, fold, title_key  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
TR = timezone(timedelta(hours=3))
UA = "Mozilla/5.0 (compatible; KamuAlimlariBot/2.0; +https://kamualimlari.github.io)"
BASE = "https://ilan.memurlar.net"
KATEGORILER = [
    "mahalli-ilanlari", "kpss-b-ilanlari", "4b-ilanlari", "gecici-isci-ilanlari",
    "daimi-isci-ilanlari", "sydv-ilanlari", "akademik-ilanlar-devlet", "kpss-a-ilanlari",
    "lakinma-ajansi",
]
AYLAR = {"ocak": 1, "subat": 2, "mart": 3, "nisan": 4, "mayis": 5, "haziran": 6, "temmuz": 7,
         "agustos": 8, "eylul": 9, "ekim": 10, "kasim": 11, "aralik": 12}
KEEP_DAYS = 180
GRACE_DAYS = 30          # son başvurusu en fazla bu kadar önce dolmuş ilanlar alınır
LINK = re.compile(r'href="((?:https?://ilan\.memurlar\.net)?/ilan/(\d+)/[^"#?]*\.html)"', re.I)


KAYNAK_ADLARI = {
    "memurlar.net": "Memurlar.net", "memurlar.net ilan": "Memurlar.net", "ilan.memurlar.net": "Memurlar.net",
    "kamuilantakvimi.com": "Kamu İlan Takvimi", "kamu ilan takvimi": "Kamu İlan Takvimi",
    "işinolsa": "İşin Olsa", "işin olsa": "İşin Olsa",
}


def kaynak_adi(ad: str) -> str:
    """Aynı sitenin farklı yazılışlarını (Memurlar.Net, memurlar.net, adres) tek ada indirger."""
    ad = (ad or "").strip()
    if ad.startswith("http"):
        ad = re.sub(r"^https?://(www\.)?", "", ad).split("/")[0]
    return KAYNAK_ADLARI.get(ad.replace("İ", "i").replace("I", "ı").lower(), ad)


def fetch(url: str, timeout: int = 25) -> str:
    last = None
    for i in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,*/*"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                raw = r.read()
                ctype = r.headers.get_content_charset()
            for enc in filter(None, [ctype, "utf-8", "windows-1254"]):
                try:
                    return raw.decode(enc)
                except (UnicodeDecodeError, LookupError):
                    continue
            return raw.decode("utf-8", "replace")
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(1.5 * (i + 1))
    raise last


def text_of(page: str) -> str:
    page = re.sub(r"(?is)<(script|style|noscript)\b.*?</\1>", " ", page)
    page = re.sub(r"(?s)<[^>]+>", " ", page)
    return re.sub(r"\s+", " ", html.unescape(page)).strip()


def list_ids(page: str):
    """Liste sayfasındaki ilan bağlantıları: [(id, tam_url)] sırayla, tekrarsız."""
    seen, out = set(), []
    for m in LINK.finditer(page):
        iid = m.group(2)
        if iid in seen:
            continue
        seen.add(iid)
        u = m.group(1)
        out.append((iid, u if u.startswith("http") else BASE + u))
    return out


def parse_tr_date(day, mon, year, hh=None, mm=None):
    mo = AYLAR.get(fold(mon))
    if not mo:
        return None
    try:
        return datetime(int(year), mo, int(day), int(hh or 0), int(mm or 0), tzinfo=TR)
    except ValueError:
        return None


DATE_RE = r"(\d{1,2})\s+([A-Za-zÇĞİÖŞÜçğıöşü]+)\s+(\d{4})"


def parse_ilan(page: str):
    """İlan sayfasından (başlık, yayın, son başvuru) çıkarır. Okunamayan alan None."""
    title = None
    for pat in (r'(?is)<h1[^>]*>(.*?)</h1>', r'(?is)<meta[^>]+property="og:title"[^>]+content="([^"]+)"',
                r'(?is)<title[^>]*>(.*?)</title>'):
        m = re.search(pat, page)
        if m:
            t = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", m.group(1)))).strip()
            t = re.sub(r"\s*[-|–]\s*Memurlar\.?net.*$", "", t, flags=re.I).strip()
            if t:
                title = t
                break
    txt = text_of(page)
    pub = None
    m = re.search(r"İlan\s*Giriş[^0-9]{0,20}" + DATE_RE + r"(?:\s+(\d{1,2}):(\d{2}))?", txt, re.I)
    if m:
        pub = parse_tr_date(m.group(1), m.group(2), m.group(3), m.group(4), m.group(5))
    dl = None
    m = re.search(r"Son\s*Başvuru\s*(?:Tarihi)?[^0-9]{0,20}" + DATE_RE, txt, re.I)
    if m:
        d = parse_tr_date(m.group(1), m.group(2), m.group(3))
        dl = d.date() if d else None
    return title, pub, dl


def body_province(page: str):
    """Başlıkta il yoksa ilan metninden il bulur: "Isparta ili ..." ve "Eğirdir/ISPARTA" kalıpları.
    Yalnızca tek bir il çıkarsa döner, belirsizse boş liste (Bakanlıklar / Kurumlar'da kalır)."""
    txt = text_of(page)
    cands = re.findall(r"([A-Za-zÇĞİÖŞÜçğıöşü]+)\s+ili\b", txt)
    cands += re.findall(r"[A-Za-zÇĞİÖŞÜçğıöşü]+\s*/\s*([A-ZÇĞİÖŞÜ]{3,})\b", txt)
    found = set()
    for c in cands:
        found.update(detect_provinces(c))
    return sorted(found) if len(found) == 1 else []


def iso(dt):
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_item(title, url, pub, dl, cat_hint, extra_prov=None):
    prov = detect_provinces(title) or (extra_prov or [])
    cat = categorize(title)
    if cat == "Diğer" and cat_hint:
        cat = cat_hint
    pub_txt = pub.astimezone(TR).strftime("%d.%m.%Y")
    parts = [f"{title}. İlan Memurlar.net'te {pub_txt} tarihinde yayımlandı."]
    if dl:
        parts.append(f"Sayfada son başvuru tarihi {dl.strftime('%d.%m.%Y')} olarak yazıyor.")
    parts.append("Başvuru yeri ve şartlar için ilanın tamamına bakın.")
    return {
        "id": hashlib.sha1((title_key(title) + url).encode()).hexdigest()[:12],
        "title": title, "url": url, "source": "Memurlar.net", "sources": ["Memurlar.net"],
        "published": iso(pub), "deadline": dl.isoformat() if dl else None,
        "first_seen": iso(datetime.now(timezone.utc)), "summary": " ".join(parts),
        "provinces": prov, "category": cat,
    }


CAT_HINT = {"kpss-b-ilanlari": "Memur / KPSS", "4b-ilanlari": "Memur / KPSS", "kpss-a-ilanlari": "Memur / KPSS",
            "gecici-isci-ilanlari": "İşçi", "daimi-isci-ilanlari": "İşçi", "sydv-ilanlari": "İşçi",
            "mahalli-ilanlari": "Belediye", "akademik-ilanlar-devlet": "Eğitim", "lakinma-ajansi": "Diğer"}


def ilan_id(url):
    m = re.search(r"/ilan/(\d+)/", url)
    return m.group(1) if m else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--en-fazla", type=int, default=40, help="bir çalışmada açılacak en çok yeni sayfa")
    ap.add_argument("--cikti", default=str(ROOT / "data" / "ilanlar.json"))
    args = ap.parse_args()
    out = Path(args.cikti)
    data = json.loads(out.read_text("utf-8"))
    items = data["items"]
    skipped_ids = set(data.get("atlanan_idler", []))
    known_ids = {ilan_id(i["url"]) for i in items if ilan_id(i["url"])} | skipped_ids
    known_keys = {}  # başlık anahtarı -> o başlıkla kayıtlı yayın tarihleri
    for i in items:
        known_keys.setdefault(title_key(i["title"]), []).append(i["published"])
    errors, ok_lists = [], 0

    cands = []  # (id, url, kategori)
    for kat in KATEGORILER:
        try:
            page = fetch(f"{BASE}/kategori/{kat}/?Expire=false")
            ok_lists += 1
            for iid, url in list_ids(page):
                if iid not in known_ids and all(iid != c[0] for c in cands):
                    cands.append((iid, url, kat))
        except Exception as e:  # noqa: BLE001
            errors.append({"kaynak": kat, "hata": f"{type(e).__name__}: {e}"[:160]})
    if ok_lists == 0:
        print("HATA: hiçbir liste açılamadı; veri değişmedi.", file=sys.stderr)
        sys.exit(1)

    now = datetime.now(timezone.utc)
    added = skipped = failed = 0
    for iid, url, kat in sorted(cands, key=lambda c: -int(c[0]))[: args.en_fazla]:
        try:
            sayfa = fetch(url)
            title, pub, dl = parse_ilan(sayfa)
        except Exception as e:  # noqa: BLE001
            failed += 1
            errors.append({"kaynak": url, "hata": f"{type(e).__name__}: {e}"[:160]})
            continue
        known_ids.add(iid)
        skipped_ids.add(iid)
        if not title or not pub or pub > now + timedelta(hours=1):
            skipped += 1
            continue
        if len(title) < 12 or len(title) > 220 or fold(title).startswith("memurlar") or not re.search(r"alacak|alim|alinacak|alinir|ilan|personel|isci|memur|ogretim|uzman|zabita|itfaiye", fold(title)):
            skipped += 1
            continue
        if dl and dl < pub.astimezone(TR).date():
            dl = None
        if dl and dl < (now - timedelta(days=GRACE_DAYS)).astimezone(TR).date():
            skipped += 1
            continue
        if pub < now - timedelta(days=60) and not dl:
            skipped += 1
            continue
        if re.search(r"vak[iıİ]f(?!kebir)|özel okul|kocaeli sağlık ve teknoloji|bilgi üniversitesi|kültür üniversitesi|bahçeşehir|sabancı|koç üniversitesi|özyeğin|medipol|atılım|başkent üniversitesi|bilkent|ostim|kadir has|yeditepe|maltepe üniversitesi|işık üniversitesi|okan üniversitesi|istinye|acıbadem|biruni|nişantaşı|altınbaş|haliç|üsküdar üniversitesi|fenerbahçe üniversitesi|hasan kalyoncu|çankaya üniversitesi|tobb|ufuk üniversitesi|lokman hekim|bezmialem", title, re.I):
            skipped += 1
            continue
        # Aynı başlık yalnızca yayın tarihi de yakınsa (3 gün) tekrar sayılır; kurumlar aynı başlıkla yeni ilan verir.
        if any(abs((pub - datetime.strptime(p, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)).days) < 3
               for p in known_keys.get(title_key(title), [])):
            skipped += 1
            continue
        items.append(build_item(title, url, pub, dl, CAT_HINT.get(kat),
                                body_province(sayfa) if not detect_provinces(title) else None))
        skipped_ids.discard(iid)
        known_keys.setdefault(title_key(title), []).append(iso(pub))
        added += 1
        time.sleep(0.6)

    cutoff = now - timedelta(days=KEEP_DAYS)
    items = [i for i in items if datetime.strptime(i["published"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc) >= cutoff]
    items.sort(key=lambda i: i["published"], reverse=True)
    for i in items:
        i["source"] = kaynak_adi(i.get("source"))
        i["sources"] = list(dict.fromkeys(kaynak_adi(x) for x in i.get("sources") or [i["source"]]))
    data["items"] = items
    data["count"] = len(items)
    data["updated"] = iso(now)
    data["kaynak_sayisi"] = {"basarili": ok_lists, "hatali": len(KATEGORILER) - ok_lists}
    data["hatalar"] = errors[:20]
    data["atlanan_idler"] = sorted(skipped_ids, key=int)[-3000:]
    out.write_text(json.dumps(data, ensure_ascii=False, indent=1), "utf-8")
    print(f"adaylar={len(cands)} eklenen={added} atlanan={skipped} hata={failed} toplam={len(items)}")


if __name__ == "__main__":
    main()
