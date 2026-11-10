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
        '<meta name="mobile-web-app-capable" content="yes">\n')
sw = ('<script>if("serviceWorker" in navigator&&location.protocol!=="file:")'
      'addEventListener("load",()=>navigator.serviceWorker.register("sw.js").catch(()=>{}));</script>\n')
(root / "index.html").write_text(head + page + "\n" + sw + "</html>\n", "utf-8")
print("index.html yazıldı")
