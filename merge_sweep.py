#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""sweep/part_*.json dosyalarını data/ilanlar.json ile birleştirir (URL ve başlık anahtarıyla tekrarı eler)."""
import glob, json, re, sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "scraper"))
from scrape import item_id, title_key, PROVINCES, fold  # noqa: E402

NAME2CODE = {fold(t[1]): t[0] for t in PROVINCES}


def code(p):
    p = str(p).strip()
    return p.zfill(2) if p.isdigit() else NAME2CODE.get(fold(p))


SWEEP = sys.argv[1] if len(sys.argv) > 1 else "/home/claude/sweep"
CATS = {"Sağlık", "Eğitim", "Güvenlik", "Belediye", "Memur / KPSS", "İşçi", "Diğer"}
now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

data = json.loads((ROOT / "data/ilanlar.json").read_text(encoding="utf-8"))
items = data["items"]
by_url = {re.sub(r"[#?].*$", "", i["url"]).rstrip("/"): i for i in items}
by_key = {title_key(i["title"]): i for i in items}
added = dup = bad = 0

for f in sorted(glob.glob(f"{SWEEP}/part_*.json")):
    try:
        rows = json.loads(Path(f).read_text(encoding="utf-8"))
    except Exception as e:
        print("OKUNAMADI", f, e); continue
    for r in rows:
        try:
            title, url = r["title"].strip(), r["url"].strip()
            assert title and url.startswith("http")
            pub = r.get("published")
            if pub:
                datetime.strptime(pub, "%Y-%m-%dT%H:%M:%SZ")
            dl = r.get("deadline")
            if dl:
                datetime.strptime(dl, "%Y-%m-%d")
            cat = r.get("category") if r.get("category") in CATS else "Diğer"
            provs = sorted({c for c in map(code, r.get("provinces", [])) if c})
            provs = [] if len(provs) > 4 else provs
        except Exception:
            bad += 1; continue
        k = re.sub(r"[#?].*$", "", url).rstrip("/")
        old = by_url.get(k) or by_key.get(title_key(title))
        if old:
            dup += 1
            # eksik alanları tamamla
            for fld in ("published", "deadline"):
                if not old.get(fld) and r.get(fld):
                    old[fld] = r[fld]
            continue
        it = {"id": item_id(title), "title": title, "url": url, "source": r.get("source", ""),
              "sources": [r.get("source", "")], "published": pub, "deadline": dl,
              "first_seen": now, "summary": r.get("summary", ""), "provinces": provs, "category": cat}
        items.append(it); by_url[k] = it; by_key[title_key(title)] = it; added += 1

items.sort(key=lambda i: i.get("published") or i["first_seen"], reverse=True)
data["items"] = items
data["count"] = len(items)
data["updated"] = now
(ROOT / "data/ilanlar.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
iller = {p for i in items for p in i["provinces"]}
print(f"eklenen={added} tekrar={dup} gecersiz={bad} toplam={len(items)} il_sayisi={len(iller)}")
