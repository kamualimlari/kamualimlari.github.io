#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Arama motorları için statik sayfalar üretir: il/<il>/index.html (81 il + bakanlık/kurum), sitemap.xml, robots.txt.
Veri: data/ilanlar.json.  Çalıştır:  python3 seo_uret.py"""
import html, json, re, shutil, sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "scraper"))
from scrape import PROVINCES, fold  # noqa: E402

BASE = "https://kamualimlari.github.io"
TR = timezone(timedelta(hours=3))
AY = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
esc = html.escape


def slug(ad):
    return fold(ad).replace(" ", "-")


def tarih(iso):
    d = datetime.strptime(iso, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).astimezone(TR)
    return f"{d.day} {AY[d.month - 1]} {d.year}"


def gun(s):
    d = datetime.strptime(s, "%Y-%m-%d")
    return f"{d.day} {AY[d.month - 1]} {d.year}"


def aktif(it, bugun):
    p = datetime.strptime(it["published"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).astimezone(TR).date()
    if it.get("deadline"):
        return it["deadline"] >= bugun.isoformat()
    return (bugun - p).days <= 60


CSS = """:root{--bg:#e8ecf0;--card:#fff;--ink:#17202a;--muted:#5b6672;--line:#d3dae1;--road:#0b4f9c}
@media(prefers-color-scheme:dark){:root{--bg:#11161c;--card:#1a212a;--ink:#e9eef3;--muted:#9aa6b2;--line:#2b3541;--road:#6aa8f0}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.55 system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif}
.w{max-width:860px;margin:0 auto;padding:16px}a{color:var(--road)}h1{font-size:clamp(26px,6vw,38px);line-height:1.15;margin:.4em 0 .3em}
.top a{font-weight:700;text-decoration:none;color:var(--ink)}.lead{color:var(--muted)}
ul.l{list-style:none;padding:0;margin:20px 0}ul.l li{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px;margin:0 0 10px}
ul.l h2{font-size:18px;margin:0 0 4px;line-height:1.3}.m{font-size:13px;color:var(--muted)}.s{margin:6px 0 0;font-size:15px}
.btn{display:inline-block;margin:10px 0;padding:10px 16px;border-radius:8px;background:var(--road);color:#fff;text-decoration:none;font-weight:600}
nav.iller{display:flex;flex-wrap:wrap;gap:6px 14px;font-size:14px;margin:24px 0}footer{color:var(--muted);font-size:13px;margin-top:28px}"""


IDOK = re.compile(r"^[A-Za-z0-9_-]+$")
PAD = {p[0]: p[1] for p in PROVINCES}


def ilan_sayfasi(it, bugun, ilgili):
    """Tek ilan sayfası: ilan/<id>/index.html"""
    yol = f"ilan/{it['id']}/"
    doldu = bool(it.get("deadline")) and it["deadline"] < bugun.isoformat()
    son = f"Son başvuru: {gun(it['deadline'])}" if it.get("deadline") else "Son başvuru tarihi ilanda belirtilmemiş"
    baslik = f"{it['title']} | {'Süresi doldu' if doldu else son}"
    ac = (it.get("summary") or it["title"])[:300]
    iller = "".join(f'<a href="{BASE}/il/{slug(PAD[p])}/">{esc(PAD[p])} iş ilanları</a>' for p in it["provinces"] if p in PAD) \
        or f'<a href="{BASE}/il/bakanliklar-kurumlar/">Bakanlıklar / Kurumlar</a>'
    ld = {"@context": "https://schema.org", "@type": "WebPage", "name": it["title"], "url": f"{BASE}/{yol}", "inLanguage": "tr",
          "datePublished": it["published"], "description": ac,
          "isPartOf": {"@type": "WebSite", "name": "Kamu Alımları", "url": BASE + "/"}}
    diger = "".join(f'<li><h2><a href="{BASE}/ilan/{o["id"]}/">{esc(o["title"])}</a></h2>'
                    f'<div class="m">{esc(o["category"])} · Yayın: {tarih(o["published"])}'
                    + (f' · Son başvuru: {gun(o["deadline"])}' if o.get("deadline") else "") + '</div></li>' for o in ilgili)
    uyari = '<p class="x">Bu ilanın başvuru süresi dolmuştur.</p>' if doldu else ""
    kaynaklar = ", ".join(dict.fromkeys(filter(None, it.get("sources") or [it.get("source", "")])))
    return f"""<!doctype html>
<html lang="tr"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(baslik)}</title>
<meta name="description" content="{esc(ac)}">
<link rel="canonical" href="{BASE}/{yol}">
<link rel="icon" href="{BASE}/icons/icon-192.png">
<meta property="og:title" content="{esc(it['title'])}"><meta property="og:description" content="{esc(ac)}">
<meta property="og:type" content="article"><meta property="og:url" content="{BASE}/{yol}"><meta property="og:locale" content="tr_TR">
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
<style>{CSS}
dl{{display:grid;grid-template-columns:auto 1fr;gap:6px 16px;background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px;margin:16px 0}}
dt{{color:var(--muted)}}dd{{margin:0;font-weight:600}}.x{{background:#f2c230;color:#3a2c00;padding:10px 14px;border-radius:8px}}.oz{{font-size:17px;max-width:68ch}}</style>
<div class="w"><div class="top"><a href="{BASE}/">Kamu Alımları</a></div>
<h1>{esc(it['title'])}</h1>
{uyari}
<dl><dt>Alım türü</dt><dd>{esc(it['category'])}</dd>
<dt>Yayın tarihi</dt><dd>{tarih(it['published'])}</dd>
<dt>Son başvuru</dt><dd>{gun(it['deadline']) if it.get('deadline') else 'İlanda belirtilmemiş'}</dd>
<dt>Kaynak</dt><dd>{esc(kaynaklar)}</dd></dl>
<p class="oz">{esc(it.get('summary') or '')}</p>
<a class="btn" href="{esc(it['url'])}" rel="noopener" target="_blank">İlanın tamamını aç</a>
<nav class="iller">{iller}<a href="{BASE}/">Tüm iller</a></nav>
{('<h2>Benzer açık ilanlar</h2><ul class="l">' + diger + '</ul>') if diger else ''}
<footer>Bu sayfa ilanın kısa özetidir ve resmî ilan yerine geçmez. Başvuru koşulları için ilanın kendisine bakın.</footer></div>
</html>
"""


def sayfa(baslik, h1, aciklama, yol, items, bugun, nav, plaka):
    ld = {"@context": "https://schema.org", "@type": "CollectionPage", "name": baslik, "url": f"{BASE}/{yol}",
          "inLanguage": "tr", "isPartOf": {"@type": "WebSite", "name": "Kamu Alımları", "url": BASE + "/"}}
    li = []
    for it in items:
        dl = f" · Son başvuru: {gun(it['deadline'])}" if it.get("deadline") else ""
        li.append(f'<li><h2><a href="{BASE}/ilan/{it["id"]}/">{esc(it["title"])}</a></h2>'
                  f'<div class="m">{esc(it["category"])} · Yayın: {tarih(it["published"])}{dl}</div>'
                  f'<p class="s">{esc(it["summary"])}</p></li>')
    govde = "\n".join(li) if li else '<li>Şu an bu bölümde açık ilan görünmüyor. Sayfa düzenli güncellenir.</li>'
    app = f"{BASE}/#il-{plaka}" if plaka else f"{BASE}/"
    return f"""<!doctype html>
<html lang="tr"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(baslik)}</title>
<meta name="description" content="{esc(aciklama)}">
<link rel="canonical" href="{BASE}/{yol}">
<link rel="icon" href="{BASE}/icons/icon-192.png">
<meta property="og:title" content="{esc(baslik)}"><meta property="og:description" content="{esc(aciklama)}">
<meta property="og:type" content="website"><meta property="og:url" content="{BASE}/{yol}"><meta property="og:locale" content="tr_TR">
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
<style>{CSS}</style>
<div class="w"><div class="top"><a href="{BASE}/">Kamu Alımları</a></div>
<h1>{esc(h1)}</h1><p class="lead">{esc(aciklama)}</p>
<a class="btn" href="{app}">Filtrele ve tüm ilanları gör</a>
<ul class="l">
{govde}
</ul>
<nav class="iller" aria-label="Diğer iller">{nav}</nav>
<footer>Özetler ilan sayfalarından derlenir ve resmî ilan yerine geçmez. Başvuru koşulları için ilanın kendisine bakın. Son güncelleme: {tarih(datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))}.</footer></div>
</html>
"""


# Ülke geneli konu sayfaları: (adres, başlık kalıbı, h1, eşleşme)
def _k(it):
    return fold(it["title"])


KONULAR = [
    ("zabita-alimi", "Zabıta Alımı {yil}: Belediye Zabıta Memuru Alım İlanları", "Zabıta memuru alımı ilanları",
     "zabıta memuru alımı", lambda i: "zabita" in _k(i)),
    ("itfaiye-eri-alimi", "İtfaiye Eri Alımı {yil}: Belediye İtfaiye Personeli İlanları", "İtfaiye eri alımı ilanları",
     "itfaiye eri alımı", lambda i: "itfaiye" in _k(i)),
    ("isci-alimi", "İşçi Alımı {yil}: Kamu ve Belediye İşçi Alım İlanları (İŞKUR)", "Kamu işçi alımı ilanları",
     "kamu ve belediye işçi alımı", lambda i: i["category"] == "İşçi" or "isci" in _k(i)),
    ("memur-alimi", "Memur Alımı {yil}: KPSS'li ve KPSS'siz Memur Alım İlanları", "Memur alımı ilanları",
     "memur alımı", lambda i: i["category"] == "Memur / KPSS" or "memur" in _k(i)),
    ("belediye-personel-alimi", "Belediye Personel Alımı {yil}: Güncel Belediye İş İlanları", "Belediye personel alımı ilanları",
     "belediye personel alımı", lambda i: i["category"] == "Belediye" or "belediye" in _k(i) or "buyuksehir" in _k(i)),
    ("sozlesmeli-personel-alimi", "Sözleşmeli Personel Alımı {yil}: 4/B ve Kurum İlanları", "Sözleşmeli personel alımı ilanları",
     "sözleşmeli personel alımı", lambda i: "sozlesmeli" in _k(i) or "4/b" in _k(i)),
    ("akademik-personel-alimi", "Akademik Personel Alımı {yil}: Öğretim Üyesi ve Öğretim Elemanı İlanları", "Üniversite akademik personel alımı ilanları",
     "devlet üniversitelerinin öğretim üyesi ve öğretim elemanı alımı", lambda i: i["category"] == "Eğitim"),
    ("saglik-personeli-alimi", "Sağlık Personeli Alımı {yil}: Hemşire, Ebe ve Sağlık Teknikeri İlanları", "Sağlık personeli alımı ilanları",
     "sağlık personeli alımı", lambda i: i["category"] == "Sağlık" or "hemsire" in _k(i) or "saglik" in _k(i)),
    ("guvenlik-gorevlisi-alimi", "Güvenlik Görevlisi ve Koruma Alımı {yil}: Kamu İlanları", "Güvenlik görevlisi alımı ilanları",
     "kamu güvenlik görevlisi, bekçi ve koruma alımı", lambda i: i["category"] == "Güvenlik" and "zabita" not in _k(i) and "itfaiye" not in _k(i)),
]


def main():
    data = json.loads((ROOT / "data" / "ilanlar.json").read_text("utf-8"))
    bugun = datetime.now(TR).date()
    items = [i for i in data["items"] if i.get("published") and aktif(i, bugun)]
    items.sort(key=lambda i: i["published"], reverse=True)
    out = ROOT / "il"
    if out.exists():
        shutil.rmtree(out)
    girisler = [(p[0], p[1], slug(p[1])) for p in PROVINCES]
    nav = ("".join(f'<a href="{BASE}/{k[0]}/">{esc(k[2])}</a>' for k in KONULAR) + f'<a href="{BASE}/son-gun-ilanlar/">Son günü yaklaşan ilanlar</a>'
           + "".join(f'<a href="{BASE}/il/{s}/">{esc(ad)}</a>' for _, ad, s in girisler) + f'<a href="{BASE}/il/bakanliklar-kurumlar/">Bakanlıklar / Kurumlar</a>')
    urls = [(f"{BASE}/", data["updated"][:10])]
    yil = bugun.year
    for plaka, ad, s in girisler:
        sec = [i for i in items if plaka in i["provinces"]]
        baslik = f"{ad} İş İlanları {yil}: Belediye, Memur, İşçi ve Kamu Personel Alımı"
        ac = f"{ad} iş ilanları {yil}: güncel belediye personel alımı, memur alımı, işçi alımı, zabıta, KPSS ve kamu iş ilanları. Son başvuru tarihleriyle {len(sec)} açık ilan."
        yol = f"il/{s}/"
        (out / s).mkdir(parents=True, exist_ok=True)
        (out / s / "index.html").write_text(sayfa(baslik, f"{ad} iş ilanları ve kamu personel alımı {yil}", ac, yol, sec, bugun, nav, plaka), "utf-8")
        urls.append((f"{BASE}/{yol}", sec[0]["published"][:10] if sec else data["updated"][:10]))
    sec = [i for i in items if not i["provinces"]]
    yol = "il/bakanliklar-kurumlar/"
    (out / "bakanliklar-kurumlar").mkdir(parents=True, exist_ok=True)
    (out / "bakanliklar-kurumlar" / "index.html").write_text(sayfa(
        f"Bakanlık ve Kurum Personel Alımı {yil}: KPSS, Sözleşmeli Personel ve Memur İlanları", f"Bakanlık ve kurum personel alımı {yil}",
        f"{yil} bakanlık ve kurum personel alımı: ülke geneli sözleşmeli personel, memur alımı, KPSS ve işçi alım ilanları. Şu an {len(sec)} açık ilan.",
        yol, sec, bugun, nav, "genel"), "utf-8")
    urls.append((f"{BASE}/{yol}", sec[0]["published"][:10] if sec else data["updated"][:10]))
    # konu sayfaları (ülke geneli)
    ay_yil = f"{AY[bugun.month - 1]} {yil}"
    for adres, bas, h1, soz, f in KONULAR:
        sec = [i for i in items if f(i)]
        ac = f"{ay_yil} güncel {soz} ilanları, 81 il. Yayın ve son başvuru tarihleriyle {len(sec)} açık ilan; sayfa gün içinde sürekli güncellenir."
        d = ROOT / adres
        if d.exists():
            shutil.rmtree(d)
        d.mkdir()
        (d / "index.html").write_text(sayfa(bas.format(yil=yil), f"{h1} ({ay_yil})", ac, f"{adres}/", sec, bugun, nav, ""), "utf-8")
        urls.append((f"{BASE}/{adres}/", sec[0]["published"][:10] if sec else data["updated"][:10]))
    lim = (bugun + timedelta(days=3)).isoformat()
    sec = sorted([i for i in items if i.get("deadline") and i["deadline"] <= lim], key=lambda i: i["deadline"])
    d = ROOT / "son-gun-ilanlar"
    if d.exists():
        shutil.rmtree(d)
    d.mkdir()
    (d / "index.html").write_text(sayfa(f"Başvurusu Bitmek Üzere Olan Kamu İlanları ({ay_yil})", "Son günü yaklaşan kamu personel alımı ilanları",
                                         f"Son başvuru tarihi 3 gün içinde dolacak kamu, belediye, memur ve işçi alım ilanları. Şu an {len(sec)} ilan.",
                                         "son-gun-ilanlar/", sec, bugun, nav, ""), "utf-8")
    urls.append((f"{BASE}/son-gun-ilanlar/", bugun.isoformat()))
    # tek ilan sayfaları (süresi dolanlar dahil; site haritasına yalnızca açık olanlar girer)
    iout = ROOT / "ilan"
    if iout.exists():
        shutil.rmtree(iout)
    acik = {i["id"] for i in items}
    n_ilan = 0
    for it in data["items"]:
        if not it.get("published") or not IDOK.match(it["id"]):
            continue
        ilgili = [o for o in items if o["id"] != it["id"] and IDOK.match(o["id"]) and (
            (set(o["provinces"]) & set(it["provinces"])) if it["provinces"] else not o["provinces"])][:5]
        (iout / it["id"]).mkdir(parents=True, exist_ok=True)
        (iout / it["id"] / "index.html").write_text(ilan_sayfasi(it, bugun, ilgili), "utf-8")
        n_ilan += 1
        if it["id"] in acik:
            urls.append((f"{BASE}/ilan/{it['id']}/", it["published"][:10]))
    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    sm += [f"<url><loc>{u}</loc><lastmod>{d}</lastmod></url>" for u, d in urls] + ["</urlset>"]
    (ROOT / "sitemap.xml").write_text("\n".join(sm) + "\n", "utf-8")
    (ROOT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {BASE}/sitemap.xml\n", "utf-8")
    print(f"{len(urls)} adres site haritasında, {n_ilan} ilan sayfası, {len(items)} açık ilan")


if __name__ == "__main__":
    main()
