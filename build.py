#!/usr/bin/env python3
"""src/page.html dosyasından bağımsız index.html üretir:  python3 build.py"""
from pathlib import Path
root = Path(__file__).resolve().parent
page = (root / "src" / "page.html").read_text("utf-8")
head = ('<!doctype html>\n<html lang="tr">\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n'
        '<link rel="manifest" href="manifest.webmanifest">\n'
        '<link rel="icon" href="icons/icon-192.png">\n'
        '<link rel="apple-touch-icon" href="icons/apple-touch-icon.png">\n'
        '<meta name="theme-color" content="#1d232b">\n'
        '<meta name="apple-mobile-web-app-capable" content="yes">\n'
        '<meta name="mobile-web-app-capable" content="yes">\n'
        '<link rel="canonical" href="https://kamualimlari.github.io/">\n'
        '<meta property="og:type" content="website">\n'
        '<meta property="og:site_name" content="Kamu Alımları">\n'
        '<meta property="og:title" content="Kamu Alımları: il il personel alımı ilanları">\n'
        '<meta property="og:description" content="İlini seç, o ildeki kamu ve belediye personel alımlarını son başvuru tarihleriyle gör.">\n'
        '<meta property="og:url" content="https://kamualimlari.github.io/">\n'
        '<meta property="og:image" content="https://kamualimlari.github.io/icons/icon-512.png">\n'
        '<meta property="og:locale" content="tr_TR">\n')
sw = ('<script>if("serviceWorker" in navigator&&location.protocol!=="file:")'
      'addEventListener("load",()=>navigator.serviceWorker.register("sw.js").catch(()=>{}));</script>\n')
page = page.replace("<title>Kamu Alımları</title>", "<title>Kamu Alımları: Memur, İşçi, Belediye Personel Alımı ve Kamu İş İlanları 2026</title>")
page = page.replace('<meta name="description" content="Haber sitelerinden derlenen kamu ve belediye personel alımı haberleri. İl seçip o ilin alımlarını gör.">',
                    '<meta name="description" content="81 ilde güncel kamu iş ilanları: belediye personel alımı, memur alımı, işçi alımı, zabıta, KPSS ve sağlık personeli ilanları. İlini seç, son başvuru tarihini gör.">')
import sys
sys.path.insert(0, str(root / "scraper"))
from scrape import PROVINCES, fold
nav = ('<nav style="max-width:892px;margin:0 auto;padding:8px 16px 40px;display:flex;flex-wrap:wrap;gap:6px 14px;font-size:14px" aria-label="İller">'
       + "".join(f'<a href="il/{fold(p[1]).replace(" ", "-")}/">{p[1]} iş ilanları</a>' for p in PROVINCES)
       + '<a href="il/bakanliklar-kurumlar/">Bakanlıklar / Kurumlar</a></nav>\n')
(root / "index.html").write_text(head + page + "\n" + nav + sw + "</html>\n", "utf-8")
print("index.html yazıldı")
