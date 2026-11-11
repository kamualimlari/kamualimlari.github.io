#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Arama motorları için statik sayfalar üretir: il/<il>/index.html (81 il + bakanlık/kurum), sitemap.xml, robots.txt.
Veri: data/ilanlar.json.  Çalıştır:  python3 seo_uret.py"""
import html, json, shutil, sys
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


def sayfa(baslik, h1, aciklama, yol, items, bugun, nav, plaka):
    ld = {"@context": "https://schema.org", "@type": "CollectionPage", "name": baslik, "url": f"{BASE}/{yol}",
          "inLanguage": "tr", "isPartOf": {"@type": "WebSite", "name": "Kamu Alımları", "url": BASE + "/"}}
    li = []
    for it in items:
        dl = f" · Son başvuru: {gun(it['deadline'])}" if it.get("deadline") else ""
        li.append(f'<li><h2><a href="{esc(it["url"])}" rel="noopener" target="_blank">{esc(it["title"])}</a></h2>'
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


def main():
    data = json.loads((ROOT / "data" / "ilanlar.json").read_text("utf-8"))
    bugun = datetime.now(TR).date()
    items = [i for i in data["items"] if i.get("published") and aktif(i, bugun)]
    items.sort(key=lambda i: i["published"], reverse=True)
    out = ROOT / "il"
    if out.exists():
        shutil.rmtree(out)
    girisler = [(p[0], p[1], slug(p[1])) for p in PROVINCES]
    nav = "".join(f'<a href="{BASE}/il/{s}/">{esc(ad)}</a>' for _, ad, s in girisler) + f'<a href="{BASE}/il/bakanliklar-kurumlar/">Bakanlıklar / Kurumlar</a>'
    urls = [(f"{BASE}/", data["updated"][:10])]
    yil = bugun.year
    for plaka, ad, s in girisler:
        sec = [i for i in items if plaka in i["provinces"]]
        baslik = f"{ad} Kamu Personel Alımı ve Belediye İş İlanları {yil}"
        ac = f"{ad} ilindeki güncel kamu, belediye, işçi, memur ve zabıta personel alım ilanları; yayın ve son başvuru tarihleriyle. Şu an {len(sec)} açık ilan."
        yol = f"il/{s}/"
        (out / s).mkdir(parents=True, exist_ok=True)
        (out / s / "index.html").write_text(sayfa(baslik, f"{ad} personel alımı ve iş ilanları", ac, yol, sec, bugun, nav, plaka), "utf-8")
        urls.append((f"{BASE}/{yol}", sec[0]["published"][:10] if sec else data["updated"][:10]))
    sec = [i for i in items if not i["provinces"]]
    yol = "il/bakanliklar-kurumlar/"
    (out / "bakanliklar-kurumlar").mkdir(parents=True, exist_ok=True)
    (out / "bakanliklar-kurumlar" / "index.html").write_text(sayfa(
        f"Bakanlık ve Kurum Personel Alımı İlanları {yil}", "Bakanlıklar ve kurumların personel alımı ilanları",
        f"Bakanlık, kurum ve kuruluşların ülke geneli sözleşmeli personel, memur ve işçi alım ilanları. Şu an {len(sec)} açık ilan.",
        yol, sec, bugun, nav, "genel"), "utf-8")
    urls.append((f"{BASE}/{yol}", sec[0]["published"][:10] if sec else data["updated"][:10]))
    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    sm += [f"<url><loc>{u}</loc><lastmod>{d}</lastmod></url>" for u, d in urls] + ["</urlset>"]
    (ROOT / "sitemap.xml").write_text("\n".join(sm) + "\n", "utf-8")
    (ROOT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {BASE}/sitemap.xml\n", "utf-8")
    print(f"{len(urls)} sayfa, {len(items)} açık ilan")


if __name__ == "__main__":
    main()
