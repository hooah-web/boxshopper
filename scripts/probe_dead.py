#!/usr/bin/env python3
"""Anden runde for de kasser hvor første domænetjek ikke gav et match.

Prøver flere kandidater (navn uden mellemrum + .dk/.com, bindestreg, 'www'),
og accepterer 200 uanset titel — men gemmer titlen, så den kan vurderes.
Kun til menneskelig gennemsyn; skriver intet til sitets data.
"""
import json, os, re, ssl, unicodedata, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/154.0.0.0 Safari/537.36")
CTX = ssl.create_default_context(); CTX.check_hostname = False; CTX.verify_mode = ssl.CERT_NONE


def norm(s):
    s = s.lower().replace("’", "").replace("'", "")
    s = re.sub(r"\(.*?\)", " ", s)
    s = s.split("–")[0].split("|")[0]
    return re.sub(r"[^a-zæøå0-9]+", "", s)


def ascii_ver(s):
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().replace("æ", "ae").replace("ø", "oe").replace("å", "aa")


def probe(domain):
    for scheme in ("https", "http"):
        try:
            req = urllib.request.Request(f"{scheme}://{domain}/", headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=12, context=CTX) as r:
                body = r.read(150000).decode("utf-8", "replace")
                t = re.search(r"(?is)<title[^>]*>(.*?)</title>", body)
                return {"domain": domain, "status": r.status, "final": r.geturl(),
                        "title": re.sub(r"\s+", " ", t.group(1)).strip()[:120] if t else ""}
        except urllib.error.HTTPError as e:
            if scheme == "http" or e.code not in (404,):
                return {"domain": domain, "status": e.code, "final": "", "title": ""}
        except Exception:
            pass
    return {"domain": domain, "status": 0, "final": "", "title": ""}


def main():
    d = json.load(open(os.path.join(ROOT, "data", "domain_check.json")))
    dead = [x for x in d if not x["verified_domain"]]
    cand = {}
    for x in dead:
        base = norm(x["name"])
        if not base or len(base) < 3:
            continue
        opts = {base + ".dk", base + ".com", ascii_ver(base) + ".dk", ascii_ver(base) + ".com"}
        cand[x["name"]] = [o for o in opts if o]
    flat = sorted({c for v in cand.values() for c in v})
    print(len(dead), "kasser,", len(flat), "kandidater", flush=True)
    res = {}
    with ThreadPoolExecutor(12) as ex:
        for r in ex.map(probe, flat):
            res[r["domain"]] = r
    out = []
    for name, opts in cand.items():
        hits = [res[o] for o in opts if res.get(o, {}).get("status") == 200]
        out.append({"name": name, "hits": hits})
    json.dump(out, open(os.path.join(ROOT, "data", "dead_probe.json"), "w"), ensure_ascii=False, indent=1)
    n = sum(1 for o in out if o["hits"])
    print("kasser med et levende domæne i runde 2:", n)


if __name__ == "__main__":
    main()
