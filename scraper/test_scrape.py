#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sınıflandırma testleri. Çalıştır:  python3 scraper/test_scrape.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scrape import categorize, detect_provinces, is_relevant, parse_feed  # noqa: E402

# (başlık, ilgili mi?, beklenen iller, beklenen kategori ya da None)
CASES = [
    ("Ankara Büyükşehir Belediyesi 150 zabıta alımı yapacak", True, ["06"], "Belediye"),
    ("Ordu'da 50 sürekli işçi alınacak", True, ["52"], "İşçi"),
    ("TSK'ya ordu mensubu uzman erbaş alımı ilanı yayımlandı", True, [], "Güvenlik"),
    ("Konyaaltı Belediyesi işçi alımı yapacak", True, ["07"], "Belediye"),
    ("Ankaragücü yeni transfer için ilan verdi", False, None, None),
    ("Muş'ta 40 sağlık personeli alınacak", True, ["49"], "Sağlık"),
    ("Fenerbahçe kadro ilan etti, süper lig maçı için", False, None, None),
    ("81 ilde sözleşmeli personel alımı ilanı yayımlandı", True, [], "Memur / KPSS"),
    ("İstanbul, Ankara, İzmir, Bursa, Antalya için memur alımı", True, [], "Memur / KPSS"),
    ("İzmir'de 200 öğretmen ataması yapılacak", True, ["35"], "Eğitim"),
    ("VAN'DA 30 işçi alımı yapılacak", True, ["65"], "İşçi"),
    ("Van Büyükşehir Belediyesi personel alımı başvuruları başladı", True, ["65"], "Belediye"),
    ("Musa Bey yeni işçi alacak", True, [], None),
    ("Dolar kuru bugün yükseldi", False, None, None),
    ("Şanlıurfa ve Diyarbakır'da polis alımı için başvuru", True, ["21", "63"], "Güvenlik"),
    ("Kahramanmaraş Sütçü İmam Üniversitesi öğretim üyesi alacak", True, ["46"], "Eğitim"),
    ("Bornova Belediyesi 40 zabıta memuru alacak", True, ["35"], "Belediye"),
    ("Harran Üniversitesi 406 personel alacak", True, ["63"], None),
    ("Tarsus ve Silifke'de işçi alımı yapılacak", True, ["33"], "İşçi"),
    ("İBB 122 itfaiye eri ve 75 memur alacak", True, ["34"], None),
    ("Fatih Belediyesi personel alımı yapacak", True, ["34"], "Belediye"),
    ("Fatih Terim'in ekibi için personel ilanı yayımlandı", True, [], None),
    ("Perşembe günü işçi alımı ilanı yayımlandı", True, [], "İşçi"),
    ("Perşembe Belediyesi işçi alımı yapacak", True, ["52"], "Belediye"),
    ("Gebze ve Darıca'da 60 zabıta alımı", True, ["41"], "Belediye"),
]

fails = 0
for title, rel, provs, cat in CASES:
    got_rel = is_relevant(title)
    ok = got_rel == rel
    if rel and ok:
        got_p = detect_provinces(title)
        got_c = categorize(title)
        ok = (got_p == provs) and (cat is None or got_c == cat)
        detail = f"iller={got_p} kategori={got_c}"
    else:
        detail = f"ilgili={got_rel}"
    print(("OK   " if ok else "FAIL ") + title + "  →  " + detail)
    fails += 0 if ok else 1

RSS = b"""<?xml version="1.0"?><rss><channel>
<item><title>Test &amp; Ba\xc5\x9fl\xc4\xb1k</title><link>https://ex.com/a</link>
<description>&lt;p&gt;Ozet&lt;/p&gt;</description><pubDate>Tue, 10 Nov 2026 10:00:00 +0300</pubDate></item>
</channel></rss>"""
feed = parse_feed(RSS)
ok = len(feed) == 1 and feed[0]["title"] == "Test & Başlık" and feed[0]["link"] == "https://ex.com/a"
print(("OK   " if ok else "FAIL ") + "RSS ayrıştırma")
fails += 0 if ok else 1

print(f"\n{len(CASES) + 1 - fails}/{len(CASES) + 1} test geçti")
sys.exit(1 if fails else 0)
