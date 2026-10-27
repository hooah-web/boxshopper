#!/usr/bin/env python3
"""Finder og tjekker udbyderdomæner for hver kasse på den gamle side.

Kandidater: domæner nævnt i teksten, partner-ads-links, og gæt ud fra navnet.
Et domæne accepteres kun hvis siden svarer 200 og titlen (eller et 2xx-redirect-mål)
indeholder et ord fra kassenavnet. Alt andet registreres som ikke fundet.
"""
import json
import os
import re
import ssl
import unicodedata
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/154.0.0.0 Safari/537.36")
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE
STOP = {"www", "shop", "dk", "com"}


def slugify(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-z0-9]+", "", s.lower())
    return s


def candidates(page):
    text = page["text"]
    name = page["h1"] or page["title"]
    out = []
    for m in re.finditer(r"\b((?:[a-z0-9-]+\.)+(?:dk|com|se|no|de|net))\b", text, re.I):
        d = m.group(1).lower()
        if not d.endswith(("googleapis.com", "google.com", "facebook.com", "instagram.com",
                           "youtube.com", "wikipedia.org", "wordpress.org", "twitter.com",
                           "pinterest.com", "linkedin.com", "gstatic.com", "boxshopper.dk")):
            out.append(d)
    for u in page["ext_links"]:
        host = u.split("/")[2].lower()
        if "partner-ads" in host or "adtraction" in host or "adrecord" in host:
            continue
        out.append(host)
    base = slugify(name.split("–")[0].split("-")[0].strip())
    if base:
        out += [base + ".dk", "www." + base + ".dk", base + ".com"]
    seen, uniq = set(), []
    for d in out:
        d = d.removeprefix("www.")
        if d not in seen:
            seen.add(d)
            uniq.append(d)
    return uniq[:10]


def probe(domain):
    for scheme in ("https", "http"):
        url = f"{scheme}://{domain}/"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "da"})
            with urllib.request.urlopen(req, timeout=15, context=CTX) as r:
                body = r.read(200000).decode("utf-8", "replace")
                title = re.search(r"(?is)<title[^>]*>(.*?)</title>", body)
                return {"domain": domain, "status": r.status, "final": r.geturl(),
                        "title": re.sub(r"\s+", " ", title.group(1)).strip()[:140] if title else ""}
        except urllib.error.HTTPError as e:
            return {"domain": domain, "status": e.code, "final": url, "title": ""}
        except Exception as e:
            last = str(e)[:80]
    return {"domain": domain, "status": 0, "final": "", "title": "", "error": last}


def matches(name, title):
    toks = [t for t in re.split(r"[^a-zA-ZæøåÆØÅ0-9]+", name.lower()) if len(t) > 3]
    tl = title.lower()
    return any(t in tl for t in toks)


def main():
    pages = json.load(open(os.path.join(ROOT, "data", "pages.json")))
    boxes = [p for p in pages if "/category/" not in p["url"] and "/amazon-prime" not in p["url"]
             and "/unboxing" not in p["url"] and p["words"] > 100]
    all_domains = sorted({d for b in boxes for d in candidates(b)})
    print(f"{len(boxes)} kasser, {len(all_domains)} kandidatdomæner", flush=True)
    results = {}
    with ThreadPoolExecutor(12) as ex:
        for i, r in enumerate(ex.map(probe, all_domains)):
            results[r["domain"]] = r
            if i % 50 == 0:
                print("  ", i, flush=True)
    out = []
    for b in boxes:
        verified = None
        for d in candidates(b):
            r = results.get(d)
            if r and r["status"] == 200 and matches(b["h1"] or b["title"], r["title"]):
                verified = r
                break
        out.append({"url": b["url"], "name": b["h1"] or b["title"], "categories": b["categories"],
                    "published": b["published"][:10], "words": b["words"],
                    "verified_domain": verified["domain"] if verified else "",
                    "provider_title": verified["title"] if verified else "",
                    "final_url": verified["final"] if verified else ""})
    json.dump(out, open(os.path.join(ROOT, "data", "domain_check.json"), "w"), ensure_ascii=False, indent=1)
    print("verificeret:", sum(1 for o in out if o["verified_domain"]), "af", len(out))


if __name__ == "__main__":
    main()
