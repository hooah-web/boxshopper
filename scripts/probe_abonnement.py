#!/usr/bin/env python3
"""Målrettet tjek: finder udbyderens abonnements-/kasseside og ser efter pris.

Prøver forsiden og et sæt sandsynlige stier. For hver side der svarer 200 gemmes
titel, om der står en pris, og om der står ord om kasse/abonnement/bestilling —
plus et kort uddrag omkring den første prismatch, så det kan læses efter.
"""
import json, os, re, ssl, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/154.0.0.0 Safari/537.36")
CTX = ssl.create_default_context(); CTX.check_hostname = False; CTX.verify_mode = ssl.CERT_NONE
PATHS = ["", "abonnement", "abonnementer", "kasse", "kassen", "produkter", "shop",
         "medlemskab", "maaltidskasse", "box", "kollektioner/alle", "collections/all"]
PRICE = re.compile(r"(\d{1,4}(?:[.\s]\d{3})?)\s*(?:,-|kr\.?|kroner|DKK)", re.I)
BOX = re.compile(r"(abonnement|månedskasse|månedsbox|kasse|kassen|box|medlemskab)", re.I)


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "da"})
    with urllib.request.urlopen(req, timeout=12, context=CTX) as r:
        return r.geturl(), r.read(400000).decode("utf-8", "replace")


def text_of(html):
    html = re.sub(r"(?is)<(script|style|noscript)[^>]*>.*?</\1>", " ", html)
    return re.sub(r"\s+", " ", re.sub(r"(?s)<[^>]+>", " ", html))


def check(slug, domain):
    res = {"slug": slug, "domain": domain, "hits": [], "best": None}
    for p in PATHS:
        url = f"https://{domain}/{p}"
        try:
            final, html = fetch(url)
        except Exception:
            continue
        t = text_of(html)
        prices = [m.group(0) for m in PRICE.finditer(t)][:5]
        box = sorted({w.lower() for w in BOX.findall(t)})[:5]
        if prices or box:
            snippet = ""
            m = PRICE.search(t)
            if m:
                snippet = t[max(0, m.start() - 120):m.end() + 60]
            res["hits"].append({"url": final, "prices": prices, "box": box, "snippet": snippet})
    scored = sorted(res["hits"], key=lambda h: (len(h["prices"]) > 0, len(h["box"])), reverse=True)
    if scored:
        res["best"] = scored[0]
    return res


def main():
    k = json.load(open(os.path.join(ROOT, "src/data/kasser.json")))
    active = [b for b in k if b["status"] == "active" and b.get("provider")]
    out = []
    with ThreadPoolExecutor(8) as ex:
        futs = [ex.submit(check, b["slug"], b["provider"]["domain"]) for b in active]
        for i, f in enumerate(futs):
            r = f.result()
            out.append(r)
            print(f"  {i+1}/{len(active)} {r['slug'][:30]:30} pris={len((r['best'] or {}).get('prices', []))} ord={','.join((r['best'] or {}).get('box', [])[:3])}", flush=True)
    json.dump(out, open(os.path.join(ROOT, "data/probe_abonnement.json"), "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
