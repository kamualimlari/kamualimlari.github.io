#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Yeni eklenen ilan sayfalarını IndexNow ile arama motorlarına (Bing, Yandex ve ortakları) bildirir.
Google IndexNow kullanmaz; onun için Search Console'a sitemap.xml eklenir. Hata olursa sessizce geçer."""
import json, re, sys, urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HOST = "kamualimlari.github.io"
KEY = "fe9a09faa969d773fbf5a4c24c266b1f"
data = json.loads((ROOT / "data" / "ilanlar.json").read_text("utf-8"))
esik = (datetime.now(timezone.utc) - timedelta(minutes=int(sys.argv[1]) if len(sys.argv) > 1 else 150)).strftime("%Y-%m-%dT%H:%M:%SZ")
yeni = [i for i in data["items"] if i.get("first_seen", "") >= esik and re.match(r"^[A-Za-z0-9_-]+$", i["id"])]
if not yeni:
    print("IndexNow: yeni ilan yok"); sys.exit(0)
urls = [f"https://{HOST}/", f"https://{HOST}/son-gun-ilanlar/"] + [f"https://{HOST}/ilan/{i['id']}/" for i in yeni][:200]
body = json.dumps({"host": HOST, "key": KEY, "keyLocation": f"https://{HOST}/{KEY}.txt", "urlList": urls}).encode()
try:
    req = urllib.request.Request("https://api.indexnow.org/indexnow", data=body, headers={"Content-Type": "application/json; charset=utf-8"})
    with urllib.request.urlopen(req, timeout=20) as r:
        print("IndexNow:", r.status, len(urls), "adres")
except Exception as e:  # noqa: BLE001
    print("IndexNow gönderilemedi:", e)
