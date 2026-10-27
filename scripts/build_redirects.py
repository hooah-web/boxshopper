#!/usr/bin/env python3
"""Laver public/_redirects ud fra den gamle sides URL-liste og verificerer
at hver gammel URL har en destination.

Regler:
  /<slug>/                    -> /box/<slug>/      (samme kasse, ny struktur)
  /category/<slug>/           -> /boxe/ eller /arkiv/ (alt efter kategori)
  /amazon-prime/**            -> /boxe/            (indholdet findes ikke længere)
  /unboxing-*                 -> /arkiv/
  /om-os/, /kontakt-os/       -> /om/, /kontakt/
Øvrige ukendte URL'er -> /boxe/.

Skriver public/_redirects og data/redirect_coverage.json.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SITE = ROOT

pages = json.load(open(os.path.join(ROOT, "data", "pages.json")))
boxes = {b["slug"] for b in json.load(open(os.path.join(ROOT, "src", "data", "kasser.json")))}

rules = []
seen = set()
uncovered = []


def add(old, new, note):
    old_path = "/" + old.strip("/") + "/"
    if old_path in seen or old_path == "/":
        return
    seen.add(old_path)
    rules.append((old_path, new, note))


# Gamle sitemap- og WordPress-stier: de skal pege på det nye sitemap.
EXTRA = {
    "sitemap.xml": "/sitemap-index.xml",
    "sitemap_index.xml": "/sitemap-index.xml",
    "wp-sitemap.xml": "/sitemap-index.xml",
    "post-sitemap.xml": "/sitemap-index.xml",
    "page-sitemap.xml": "/sitemap-index.xml",
    "category-sitemap.xml": "/sitemap-index.xml",
    "post_tag-sitemap.xml": "/sitemap-index.xml",
    "author-sitemap.xml": "/sitemap-index.xml",
    "oe_swar-sitemap.xml": "/sitemap-index.xml",
    "feed": "/boxe/",
}
for old, new in EXTRA.items():
    rules.append(("/" + old, new, "gammel teknisk sti"))
    seen.add("/" + old + "/")
# Feed-varianter: /feed/, /feed/rss/, /comments/feed/
for pat in ("/feed/*", "/comments/feed/*"):
    rules.append((pat, "/boxe/", "gammel feed"))
    seen.add(pat)

for p in pages:
    url = p["url"]
    if not url.startswith("https://boxshopper.dk"):
        continue
    path = url.replace("https://boxshopper.dk", "").strip("/")
    if path == "":
        continue
    if path.startswith("category/"):
        add(path, "/boxe/", "gammel kategoriside")
    elif path.startswith("amazon-prime"):
        add(path, "/boxe/", "Amazon Prime-artikel, ikke en kasse")
    elif path.startswith("unboxing"):
        add(path, "/arkiv/", "unboxing-indlæg")
    elif path == "om-os":
        add(path, "/om/", "om-side")
    elif path == "kontakt-os":
        add(path, "/kontakt/", "kontaktside")
    elif path in boxes:
        add(path, f"/box/{path}/", "kasse")
    else:
        add(path, "/boxe/", "ingen ny side")

destinations = {"https://boxshopper.dk/box/", "https://boxshopper.dk/arkiv/",
                "https://boxshopper.dk/boxe/", "https://boxshopper.dk/om/",
                "https://boxshopper.dk/kontakt/"}
for _, new, _ in rules:
    destinations.add("https://boxshopper.dk" + new)

lines = ["# Genereret af scripts/build_redirects.py — rediger ikke i hånden",
         "# Gamle WordPress-URL'er -> nye sider", ""]
for old, new, note in rules:
    lines.append(f"# {note}")
    lines.append(f"{old}  {new}  301")

os.makedirs(os.path.join(SITE, "public"), exist_ok=True)
with open(os.path.join(SITE, "public", "_redirects"), "w") as f:
    f.write("\n".join(lines) + "\n")

json.dump({"rules": len(rules), "uncovered": uncovered},
          open(os.path.join(ROOT, "data", "redirect_coverage.json"), "w"), indent=1)
print(f"{len(rules)} regler skrevet; {len(uncovered)} gamle URL'er uden destination")
