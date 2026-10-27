#!/usr/bin/env python3
"""Udtrækker tags, kategorier, billeder og post-indhold fra en WordPress-eksport.

Skriver data/wxr.json med:
  tags        navn, slug, beskrivelse (wp:tag_description)
  categories  navn, slug, beskrivelse
  attachments id -> url, titel, alt, parent (post/attachment)
  posts       slug -> titel, dato, indhold (HTML), attachments[url...]

Kommentarer læses ikke og gemmes ikke (de indeholder personoplysninger).
"""
import json
import os
import re
import sys
import xml.etree.ElementTree as ET

NS = {
    "wp": "http://wordpress.org/export/1.2/",
    "content": "http://purl.org/rss/1.0/modules/content/",
    "excerpt": "http://wordpress.org/export/1.2/excerpt/",
    "dc": "http://purl.org/dc/elements/1.1/",
}
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def txt(el, path):
    found = el.find(path, NS)
    return (found.text or "").strip() if found is not None and found.text else ""


def main():
    src = sys.argv[1]
    tree = ET.parse(src)
    channel = tree.getroot().find("channel")

    tags = [{"slug": txt(t, "wp:tag_slug", ), "name": txt(t, "wp:tag_name"),
             "description": txt(t, "wp:tag_description")}
            for t in channel.findall("wp:tag", NS)]
    cats = [{"slug": txt(c, "wp:category_nicename"), "name": txt(c, "wp:category_title"),
             "description": txt(c, "wp:category_description")}
            for c in channel.findall("wp:category", NS)]

    items = channel.findall("item")
    attachments, posts = {}, {}
    for it in items:
        ptype = txt(it, "wp:post_type")
        status = txt(it, "wp:status")
        post_id = txt(it, "wp:post_id")
        if ptype == "attachment":
            attachments[post_id] = {
                "id": post_id,
                "url": txt(it, "wp:attachment_url"),
                "title": txt(it, "title"),
                "parent": txt(it, "wp:post_parent"),
                "alt": next((m.text for m in it.findall("wp:postmeta", NS)
                             if m.find("wp:meta_key", NS) is not None
                             and (m.find("wp:meta_key", NS).text or "") == "_wp_attachment_image_alt"), ""),
            }
        elif ptype in ("post", "page") and status == "publish":
            slug = txt(it, "wp:post_name")
            body = txt(it, "content:encoded")
            posts[slug] = {
                "id": post_id,
                "slug": slug,
                "type": ptype,
                "title": txt(it, "title"),
                "date": txt(it, "wp:post_date")[:10],
                "content": body,
                "excerpt": txt(it, "excerpt:encoded"),
                "tags": [c.text for c in it.findall("category[@domain='post_tag']")],
                "categories": [c.text for c in it.findall("category[@domain='category']")],
                "image_ids": [post_id],
            }

    # Billeder knyttes til det indlæg, de er uploadet til.
    by_id = {p["id"]: p for p in posts.values()}
    for a in attachments.values():
        parent = by_id.get(a["parent"])
        if parent:
            parent.setdefault("images", []).append(a["url"])
    # Billeder der refereres i indholdet, men ikke er uploadet til indlægget
    for p in posts.values():
        urls = re.findall(r"https://boxshopper\.dk/wp-content/uploads/[^\"\s>)]+", p["content"])
        imgs = p.setdefault("images", [])
        for u in urls:
            if u not in imgs:
                imgs.append(u)

    out = {"tags": tags, "categories": cats, "attachments": list(attachments.values()),
           "posts": posts}
    with open(os.path.join(ROOT, "data", "wxr.json"), "w") as f:
        json.dump(out, f, ensure_ascii=False)
    print("tags:", len(tags), "| kategorier:", len(cats), "| billeder:", len(attachments),
          "| indlæg:", len(posts))
    withimg = sum(1 for p in posts.values() if p.get("images"))
    print("indlæg med mindst ét billede:", withimg)
    print("tags med beskrivelse:", sum(1 for t in tags if t["description"]))


if __name__ == "__main__":
    main()
