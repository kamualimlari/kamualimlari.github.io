#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Çevrimdışı test: sahte sayfalarla. Çalıştır: python3 -I scraper/test_ilan_tara.py"""
import json, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import ilan_tara as t

LISTE = '''<ul><li><a href="/ilan/90005/sariidris-belediyesi-1-memur-alacak.html">x</a></li>
<li><a href="/ilan/90001/antalya-akseki-belediyesi-1-memur-alacak.html" title="x">Antalya Akseki Belediyesi 1 Memur Alacak</a></li>
<li><a href="https://ilan.memurlar.net/ilan/90002/sanliurfa-eyyubiye-belediyesi-9-zabita-memuru-alacak.html">x</a></li>
<li><a href="/ilan/90003/vakif-universitesi-ogretim-uyesi.html">x</a></li>
<li><a href="/ilan/90001/antalya-akseki-belediyesi-1-memur-alacak.html">tekrar</a></li></ul>'''
SAYFA = {
 "90001": '<html><head><title>Antalya Akseki Belediyesi 1 Memur Alacak - Memurlar.Net</title></head><body><h1>Antalya Akseki Belediyesi 1 Memur Alacak</h1><div>İlan Giriş: 06 Kasım 2026 12:30</div><p>Son başvuru tarihi: 20 Kasım 2026</p></body></html>',
 "90002": '<html><body><h1>Şanlıurfa Eyyübiye Belediyesi 9 Zabıta Memuru Alacak</h1><span>İlan Giriş :</span> <b>29 Ekim 2026 00:15</b> <span>Son Başvuru Tarihi</span> <b>10 Aralık 2026</b></body></html>',
 "90003": '<html><body><h1>Örnek Vakıf Üniversitesi öğretim üyesi alacak</h1><div>İlan Giriş: 05 Kasım 2026 10:00</div></body></html>',
 "90005": '<html><body><h1>Sarıidris Belediyesi 1 Memur Alacak</h1><div>İlan Giriş: 12 Ekim 2026 01:05</div><p>Son Başvuru Tarihi 20 Kasım 2026</p><p>Isparta ili Sarıidris Belediye Başkanlığı bünyesinde</p><p>Sarıidris Kasabası Eğirdir/ISPARTA adresinde</p></body></html>',
 "90004": '<html><body><h1>Tarihsiz İlan 3 işçi alacak</h1></body></html>',
}
fails = 0
def check(ad, ok):
    global fails
    print(("OK   " if ok else "FAIL ") + ad); fails += 0 if ok else 1

check("liste: 4 ilan, tekrarsız", [i for i, _ in t.list_ids(LISTE)] == ["90005", "90001", "90002", "90003"])
ti, pub, dl = t.parse_ilan(SAYFA["90001"])
check("sayfa 1: başlık/yayın/son", ti == "Antalya Akseki Belediyesi 1 Memur Alacak" and pub.isoformat().startswith("2026-11-06T12:30") and str(dl) == "2026-11-20")
ti, pub, dl = t.parse_ilan(SAYFA["90002"])
check("sayfa 2: etiketler ayrı etiketlerde", pub and pub.day == 29 and pub.month == 10 and str(dl) == "2026-12-10")
check("sayfa 4: tarihsiz → None", t.parse_ilan(SAYFA["90004"])[1] is None)

# uçtan uca
tmp = Path(tempfile.mkdtemp()); out = tmp / "ilanlar.json"
json.dump({"updated": "x", "count": 0, "provinces": [], "kaynak_sayisi": {}, "hatalar": [], "items": []}, open(out, "w"))
def fake(url, timeout=25):
    if "/kategori/mahalli-ilanlari/" in url: return LISTE
    if "/kategori/" in url: return "<html></html>"
    for k, v in SAYFA.items():
        if f"/ilan/{k}/" in url: return v
    raise RuntimeError("404")
t.fetch = fake; t.time.sleep = lambda s: None
sys.argv = ["x", "--cikti", str(out)]
t.main()
d = json.load(open(out))
tit = [i["title"] for i in d["items"]]
check("uçtan uca: 3 ilan eklendi, vakıf atlandı", len(tit) == 3 and not any("Vakıf" in x for x in tit))
ey = [i for i in d["items"] if "Eyyübiye" in i["title"]][0]
check("Eyyübiye: il 63, yayın UTC, son başvuru", ey["provinces"] == ["63"] and ey["published"] == "2026-10-28T21:15:00Z" and ey["deadline"] == "2026-12-10")
sa = [i for i in d["items"] if "Sarıidris" in i["title"]]
check("başlıkta il yok: metinden Isparta (32)", len(sa) == 1 and sa[0]["provinces"] == ["32"])
before = len(d["items"]); t.main(); d = json.load(open(out))
check("ikinci çalışma: tekrar eklemez", len(d["items"]) == before)
print(f"\n{'hepsi geçti' if not fails else str(fails)+' hata'}"); sys.exit(1 if fails else 0)
