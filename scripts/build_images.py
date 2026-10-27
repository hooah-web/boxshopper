#!/usr/bin/env python3
"""Vælger ét billede pr. kasse, kopierer det til sitet og opdaterer kasser.json.

Kilde: data/wxr.json (billeder knyttet til indlæg via post_parent og indhold)
og data/images_raw/ (de hentede filer).

Regler:
  - kun rigtige billedfiler (mp3/pdf frasorteres)
  - foretræk billeder uploadet til netop det indlæg
  - foretræk kvadratisk eller liggende, mindst 250 px, størst areal
  - logoer fra boxshopper selv og generiske ikoner frasorteres
  - output: public/billeder/<slug>.png, max 600 px, gennemsigtighed bevaret
"""
import json
import os
import re
import unicodedata

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RAW = os.path.join(ROOT, "data", "images_raw")
OUT = os.path.join(ROOT, "public", "billeder")
MAXW = 600

SKIP = re.compile(r"(boxshopper|logo|banner|p4-trekanten|ugeavisen|favicon|screenshot)", re.I)
OK_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp"}


def slugify(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def raw_name(url):
    return url.split("/wp-content/uploads/")[-1].replace("/", "_")


def score(path, name, brand):
    """Højere er bedre. Returnerer None hvis filen ikke kan bruges."""
    try:
        im = Image.open(path)
        w, h = im.size
    except Exception:
        return None
    if w < 200 or h < 120:
        return None
    ar = w / h
    s = min(w, h)
    if brand and brand.lower()[:6] in name.lower():
        s *= 1.35
    if SKIP.search(name):
        s *= 0.35
    if 0.8 <= ar <= 1.6:
        s *= 1.2
    if ar > 2.6:
        s *= 0.5
    return s


def main():
    wxr = json.load(open(os.path.join(ROOT, "data", "wxr.json")))
    boxes = json.load(open(os.path.join(ROOT, "src", "data", "kasser.json")))
    posts = wxr["posts"]
    by_name = {}
    for p in posts.values():
        by_name.setdefault(p["title"].strip().lower(), p)

    os.makedirs(OUT, exist_ok=True)
    used, missing = 0, []
    for b in boxes:
        post = posts.get(b["slug"]) or by_name.get(b["name"].strip().lower())
        b["tags"] = post["tags"] if post else []
        best, best_score = None, 0
        if post:
            for url in post.get("images", []):
                if os.path.splitext(url)[1].lower() not in OK_EXT:
                    continue
                fn = raw_name(url)
                path = os.path.join(RAW, fn)
                if not os.path.exists(path):
                    continue
                s = score(path, fn, b["name"])
                if s and s > best_score:
                    best, best_score = path, s
        if not best:
            missing.append(b["slug"])
            b.pop("image", None)
            b.pop("imageAlt", None)
            continue
        im = Image.open(best)
        if im.mode not in ("RGB", "RGBA"):
            im = im.convert("RGBA")
        if im.width > MAXW:
            im = im.resize((MAXW, round(im.height * MAXW / im.width)), Image.LANCZOS)
        dest = os.path.join(OUT, slugify(b["slug"]) + ".webp")
        im.save(dest, "WEBP", quality=88, method=6)
        b["image"] = f"/billeder/{slugify(b['slug'])}.webp"
        b["imageAlt"] = b["name"]
        used += 1

    json.dump(boxes, open(os.path.join(ROOT, "src", "data", "kasser.json"), "w"),
              ensure_ascii=False, indent=1)
    total = sum(os.path.getsize(os.path.join(OUT, f)) for f in os.listdir(OUT))
    print(f"billeder brugt: {used} af {len(boxes)} kasser")
    print(f"uden billede: {len(missing)}")
    print(f"samlet størrelse: {total/1024:.0f} KB ({total/max(used,1)/1024:.0f} KB pr. billede)")


if __name__ == "__main__":
    main()
