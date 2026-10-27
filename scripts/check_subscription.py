#!/usr/bin/env python3
"""Tjekker om et domæne faktisk sælger et abonnement: henter forsiden og
leder efter abonnementsord på dansk/engelsk. Skriver belæg (ord fundet) til
data/subscription_check.json — ingen konklusioner, kun fund."""
import json, os, re, ssl, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/154.0.0.0 Safari/537.36")
CTX = ssl.create_default_context(); CTX.check_hostname = False; CTX.verify_mode = ssl.CERT_NONE
WORDS = ["abonnement", "abonnér", "abonner", "månedlig", "hver måned", "subscription",
         "subscribe", "medlemskab", "kasse", "box", "levering"]


def check(domain):
    try:
        req = urllib.request.Request(f"https://{domain}/", headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=15, context=CTX) as r:
            body = r.read(400000).decode("utf-8", "replace").lower()
            title = re.search(r"(?is)<title[^>]*>(.*?)</title>", body)
            return {"domain": domain, "status": r.status, "final": r.geturl(),
                    "title": re.sub(r"\s+", " ", title.group(1)).strip()[:120] if title else "",
                    "hits": sorted({w for w in WORDS if w in body})}
    except Exception as e:
        return {"domain": domain, "status": 0, "error": str(e)[:60], "hits": []}


if __name__ == "__main__":
    doms = json.load(open(os.path.join(ROOT, "data", "candidates.json")))
    out = []
    with ThreadPoolExecutor(10) as ex:
        for r in ex.map(check, doms):
            out.append(r)
    json.dump(out, open(os.path.join(ROOT, "data", "subscription_check.json"), "w"),
              ensure_ascii=False, indent=1)
    for r in sorted(out, key=lambda x: -len(x["hits"])):
        print(f"{r['status']:>4} {len(r['hits'])} {r['domain']:28} {r.get('title','')[:55]}")
