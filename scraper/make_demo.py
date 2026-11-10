#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sayfayı ilk açışta boş görünmesin diye ÖRNEK veri üretir (gerçek haber değildir)."""
import json, sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from scrape import PROVINCES, categorize, detect_provinces, iso, item_id

ROWS = [
 (0.5,  "Ankara Büyükşehir Belediyesi 150 zabıta memuru alacak"),
 (1.5,  "İzmir'de sağlık personeli alımı: 400 sözleşmeli hemşire ve ebe alınacak"),
 (3,    "KPSS şartsız 2 bin sürekli işçi alımı başvuruları başladı"),
 (5,    "Konya'da 60 temizlik personeli alımı yapılacak"),
 (8,    "Şanlıurfa ve Diyarbakır'da polis alımı için başvurular sürüyor"),
 (14,   "Bursa Büyükşehir Belediyesi itfaiye eri alımı ilanı yayımlandı"),
 (22,   "Trabzon'da üniversite öğretim üyesi alımı ilanı"),
 (30,   "Sözleşmeli öğretmen ataması takvimi açıklandı"),
 (40,   "Antalya'da belediye personel alımı: 90 kişi işe alınacak"),
 (55,   "Samsun'da hastane için 120 sağlık personeli alınacak"),
 (70,   "Uzman erbaş alımı başvuru kılavuzu yayımlandı"),
 (96,   "Gaziantep'te 80 işçi alımı için kura çekilecek"),
 (130,  "Erzurum'da engelli memur alımı yapılacak"),
]
now = datetime.now(timezone.utc)
items = []
for h, t in ROWS:
    items.append({
        "id": item_id(t), "title": t, "url": "https://example.com/ornek",
        "source": "Örnek kaynak", "sources": ["Örnek kaynak"],
        "published": iso(now - timedelta(hours=h)), "first_seen": iso(now),
        "summary": "", "demo": True,
        "provinces": detect_provinces(t), "category": categorize(t),
    })
out = {"updated": iso(now), "count": len(items), "demo": True,
       "provinces": [{"plaka": p, "ad": a} for p, a, _ in PROVINCES],
       "kaynak_sayisi": {"basarili": 0, "hatali": 0}, "hatalar": [], "items": items}
dest = Path(__file__).resolve().parent.parent / "data" / "ilanlar.json"
dest.parent.mkdir(exist_ok=True)
dest.write_text(json.dumps(out, ensure_ascii=False, indent=1), "utf-8")
print("Örnek veri yazıldı:", dest)
