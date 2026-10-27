#!/usr/bin/env python3
"""Udtrækker struktur og brødtekst fra de gemte WordPress-sider.

Output: data/pages.json — én række pr. URL med titel, h1, meta, kategori,
publiceringsdato, ren brødtekst fra div.entry-content (uden annoncer,
PHP-warnings og sidepaneler) og udgående links.

Ingen gæt: felter der ikke findes i kilden, er tomme.
"""
import json
import os
import re

from bs4 import BeautifulSoup

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RAW = os.path.join(ROOT, "data", "raw")

NOISE_SELECTORS = [
    "script", "style", "noscript", "form", "nav", "footer", "aside",
    ".widgets_on_page", ".textwidget", ".wp-block-post-author",
    ".wpd-secondary-forms-social-content", ".swar", ".sharedaddy",
    ".jp-relatedposts", ".fc-dialog-content",
]
NOISE_RE = re.compile(
    r"(?i)(adsbygoogle|\.BoxBottom|googlesyndication|/var/www/|"
    r"^(warning|notice|deprecated|fatal error):|window\.__|document\.)")


def clean_text(el):
    for sel in NOISE_SELECTORS:
        for junk in el.select(sel):
            junk.decompose()
    for br in el.find_all("br"):
        br.replace_with("\n")
    for tag in el.find_all(["p", "div", "li", "h1", "h2", "h3", "h4", "tr"]):
        tag.append("\n")
    lines, prev = [], None
    for raw in el.get_text().split("\n"):
        line = re.sub(r"[ \t\xa0]+", " ", raw).strip()
        if not line or NOISE_RE.search(line):
            continue
        if line != prev:
            lines.append(line)
        prev = line
    return "\n".join(lines)


def main():
    pages = []
    for fn in sorted(os.listdir(RAW)):
        if not fn.endswith(".html"):
            continue
        soup = BeautifulSoup(open(os.path.join(RAW, fn), errors="replace").read(), "html.parser")

        def meta(name=None, prop=None):
            el = soup.find("meta", attrs={"name": name} if name else {"property": prop})
            return (el.get("content") or "").strip() if el else ""

        canon = soup.find("link", rel="canonical")
        h1 = soup.find("h1")
        content = soup.select_one("div.entry-content") or soup.find("article") or soup.body
        text = clean_text(content) if content else ""

        cats = [a.get_text(strip=True) for a in soup.select(".taxonomy-category a, a[rel~=category]")]
        links = []
        for a in content.find_all("a", href=True) if content else []:
            h = a["href"]
            if h.startswith("http") and "boxshopper.dk" not in h and "wordpress.org" not in h:
                links.append(h)

        pages.append({
            "file": fn,
            "url": canon.get("href") if canon else "",
            "title": soup.title.get_text(strip=True) if soup.title else "",
            "h1": h1.get_text(strip=True) if h1 else "",
            "desc": meta(name="description"),
            "published": meta(prop="article:published_time"),
            "modified": meta(prop="article:modified_time"),
            "categories": sorted(set(cats)),
            "words": len(text.split()),
            "text": text,
            "ext_links": sorted(set(links)),
        })

    with open(os.path.join(ROOT, "data", "pages.json"), "w") as f:
        json.dump(pages, f, ensure_ascii=False, indent=1)

    print(f"{len(pages)} sider -> data/pages.json")
    print("median ord:", sorted(p["words"] for p in pages)[len(pages) // 2])
    print("under 150 ord:", sum(1 for p in pages if p["words"] < 150))
    print("kategorier:", len({c for p in pages for c in p["categories"]}))


if __name__ == "__main__":
    main()
