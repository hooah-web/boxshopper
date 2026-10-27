#!/usr/bin/env python3
"""Tjekker om hver aktiv kasse stadig kan købes på udbyderens egen side.

For hver kasse hentes forsiden, og der ledes efter:
  - en pris (kr., DKK, ,- eller "pr. måned")
  - ord om at købe/tilmelde sig et abonnement eller en kasse
Derefter følges op til tre links, der ser ud som abonnements-/kassesider, og
samme tjek køres der.

Skriver data/active_recheck.json med belæg (fundne priser, ord og URL'er) og en
foreløbig vurdering. Vurderingen er ikke en afgørelse — den skal læses igennem.
"""
import json
import os
import re
import ssl
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/154.0.0.0 Safari/537.36")
CTX = ssl.create_default_context(); CTX.check_hostname = False; CTX.verify_mode = ssl.CERT_NONE

PRICE = re.compile(r"(\d{1,4}(?:[.\s]\d{3})?)\s*(?:,-|kr\.?|kroner|DKK)", re.I)
BUY = re.compile(r"(abonnement|abonnér|abonner|månedskasse|månedsbox|kassen|kasse|"
                 r"box|medlemskab|tegne|bestil|køb nu|tilmeld)", re.I)
STOP = re.compile(r"(cookie|privatliv|handelsbetingelser|login|kurv|checkout|"
                  r"kontakt|om-os|blog|nyheder|vilkår)", re.I)


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "da-DK,da;q=0.9"})
    with urllib.request.urlopen(req, timeout=20, context=CTX) as r:
        return r.geturl(), r.read(500000).decode("utf-8", "replace")


def strip(t):
    t = re.sub(r"(?is)<(script|style|noscript)[^>]*>.*?</\1>", " ", t)
    t = re.sub(r"(?s)<[^>]+>", " ", t)
    return re.sub(r"\s+", " ", t)


def analyse(html):
    text = strip(html)
    prices = sorted({m.group(0).strip() for m in PRICE.finditer(text)})[:8]
    words = sorted({m.group(0).lower() for m in BUY.finditer(text)})[:8]
    return text, prices, words


def links(html, base):
    out = []
    for href in re.findall(r'href="([^"]+)"', html):
        if href.startswith(("mailto:", "tel:", "#", "javascript:")):
            continue
        u = urllib.parse.urljoin(base, href)
        if urllib.parse.urlparse(u).netloc != urllib.parse.urlparse(base).netloc:
            continue
        if STOP.search(u):
            continue
        if re.search(r"(abonnement|kasse|box|shop|produkt|medlemskab)", u, re.I) and u not in out:
            out.append(u)
    return out[:3]


def check(box):
    domain = box["provider"]["domain"]
    out = {"slug": box["slug"], "name": box["name"], "domain": domain,
           "home": {}, "subpages": [], "verdict": "uklar"}
    try:
        final, html = get(f"https://{domain}/")
        text, prices, words = analyse(html)
        out["home"] = {"status": 200, "final": final, "title": (re.search(r"(?is)<title[^>]*>(.*?)</title>", html) or [None, ""])[1][:100] if re.search(r"(?is)<title", html) else "",
                       "prices": prices, "words": words, "chars": len(text)}
        for u in links(html, final):
            try:
                _, h2 = get(u)
                _, p2, w2 = analyse(h2)
                out["subpages"].append({"url": u, "prices": p2, "words": w2})
            except Exception:
                continue
    except Exception as e:
        out["home"] = {"status": 0, "error": str(e)[:80]}
        out["verdict"] = "død"
        return out

    has_price_home = bool(out["home"].get("prices"))
    has_price_sub = any(s["prices"] for s in out["subpages"])
    buy_home = bool(out["home"].get("words"))
    if (has_price_home and buy_home) or has_price_sub:
        out["verdict"] = "køb"
    elif out["home"].get("status") == 200:
        out["verdict"] = "uklar"
    return out


def main():
    k = json.load(open(os.path.join(ROOT, "src", "data", "kasser.json")))
    active = [b for b in k if b["status"] == "active"]
    print(f"tjekker {len(active)} aktive kasser", flush=True)
    res = []
    with ThreadPoolExecutor(6) as ex:
        for i, r in enumerate(ex.map(check, active)):
            res.append(r)
            print(f"  {i+1}/{len(active)} {r['name'][:18]:18} {r['verdict']}", flush=True)
    json.dump(res, open(os.path.join(ROOT, "data", "active_recheck.json"), "w"), ensure_ascii=False, indent=1)
    from collections import Counter
    print(Counter(r["verdict"] for r in res))


if __name__ == "__main__":
    main()
