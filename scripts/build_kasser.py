#!/usr/bin/env python3
"""Bygger sitets datafil: data/kasser.json.

Kilder:
  data/pages.json            den gamle sides sider (tekst, kategori, dato, URL)
  data/curated_providers.json  håndverificerede udbydere (domæne + kategori)
  data/subscription_check.json belæg for at domænet sælger abonnement

Status:
  active  = udbyderdomæne svarer 200, titlen matcher kassen, og forsiden taler om abonnement
  closed  = domænet er væk, parkeret, eller solgt til noget helt andet (fx casino)
  unknown = ingen af delene kunne afgøres

Ingen priser og ingen påstande om oplevelser: kun det kilderne viser.
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CHECKED = "2026-10-27"

# Rækkefølgen er prioriteret: den første regel der matcher en SPECIFIK kategori vinder.
# Generiske kategorier ("Alle kasser", "Danske kasser", "Lukket") ignoreres helt.
CATEGORY_RULES = [
    ("Kæledyr", ["hund", "katte", "box til dyr", "kæledyr"]),
    ("Tøj & tilbehør", ["undertøj", "tøj", "sokker", "strømper", "mode", "fashion"]),
    ("Kaffe & te", ["kaffe", "kaffe/te", "te-abonnement", "te abonnement"]),
    ("Børn & legetøj", ["børn", "legetøj", "baby", "kreativ"]),
    ("Motion & sundhed", ["fitness", "motion", "vitamin", "kosttilskud"]),
    ("Mænd", ["mænd", "til mand", "til maend", "barber", "shave"]),
    ("Skønhed & pleje", ["kvinder", "kvinde", "makeup", "skønhed", "beauty", "intim", "mode"]),
    ("Mad & drikke", ["mad", "måltid", "grøntsag", "kød", "slik", "vin", "øl", "drikkevarer", "ost", "chokolade", "tapas", "færdig retter"]),
    ("Bolig & livsstil", ["blomster", "diverse", "livsstil", "bolig"]),
]
GENERIC = {"alle kasser", "danske kasser", "udenlandske bokse", "lukket", "unboxing"}

ABBREV = ["bl.a.", "f.eks.", "fx.", "dvs.", "m.fl.", "m.m.", "osv.", "ca.", "evt.", "ift.",
          "pga.", "kr.", "md.", "nr.", "jf.", "tlf.", "ang.", "vedr."]


def category_of(cats, text=""):
    specific = [c for c in cats if c.strip().lower() not in GENERIC]
    joined = " ".join(specific).lower()
    for name, keys in CATEGORY_RULES:
        if any(k in joined for k in keys):
            return name
    # Ingen brugbar kategori på den gamle side: se på teksten, derefter på navnet.
    haystack = (text[:600] + " " + " ".join(specific)).lower()
    for name, keys in CATEGORY_RULES:
        if any(k in haystack for k in keys):
            return name
    return "Bolig & livsstil"


def sentences(text, n=3, maxlen=420):
    t = text.replace("\n", " ")
    for a in ABBREV:
        t = t.replace(a, a.replace(".", "\u0000"))
    parts = re.split(r"(?<=[.!?])\s+", t)
    parts = [p.replace("\u0000", ".").strip() for p in parts if p.strip()]
    out = []
    for p in parts:
        if len(" ".join(out)) + len(p) > maxlen and out:
            break
        out.append(p)
        if len(out) >= n:
            break
    return " ".join(out)


def slug_of(url):
    return url.rstrip("/").split("/")[-1]


def is_closed_text(text):
    return bool(re.search(r"(?i)(er lukket|lukket i danmark|ikke længere|nedlagt|eksisterer ikke)", text))


def main():
    pages = json.load(open(os.path.join(ROOT, "data", "pages.json")))
    curated = json.load(open(os.path.join(ROOT, "data", "curated_providers.json")))
    checks = {c["domain"]: c for c in json.load(open(os.path.join(ROOT, "data", "subscription_check.json")))}

    boxes = {}
    for p in pages:
        u = p["url"]
        if any(x in u for x in ("/category/", "/amazon-prime", "/unboxing", "/author/")):
            continue
        if p["words"] < 60:
            continue
        slug = slug_of(u)
        name = (p["h1"] or p["title"]).strip()
        name = re.sub(r"\s*[–|-]\s*$", "", name)
        # Sider der ikke er en kasse men en artikel, en kategori eller en dublet
        if slug in ("", "om-os", "kontakt-os", "privatlivspolitik", "test", "kasse-test",
                    "hvad-er-boksshopping", "hvad-er-kasse-abonnement", "rabatkoder",
                    "subhub-app-abonnementer-overblik", "boxshopper.dk",
                    "miriale-tono-undertoej-alternativer", "kom-i-gang-med-winefamly",
                    "wine-famly-vin-udvalg", "winefamly-vin-priser", "abonnements-kasse-unboxing",
                    "aarstiderne-lodtraekning", "tilbage"):
            continue
        if slug not in boxes:
            boxes[slug] = {
                "slug": slug, "name": name, "old_url": u,
                "old_categories": p["categories"], "year": (p["published"] or "")[:4],
                "text": p["text"], "desc": p["desc"],
            }

    out = []
    for slug, b in boxes.items():
        c = curated.get(slug)
        status, provider, evidence = "unknown", None, ""
        if c:
            chk = checks.get(c["domain"], {})
            hits = chk.get("hits", [])
            if chk.get("status") == 200 and len(hits) >= 2:
                status = "active"
                provider = {"domain": c["domain"], "url": f"https://{c['domain']}/"}
                evidence = "Forsiden på " + c["domain"] + " svarer 200 og nævner " + ", ".join(hits[:4])
            elif c.get("note"):
                status = "closed"
                evidence = c["note"]
            else:
                # Domænet svarer, men siden bekræfter ikke tydeligt et abonnement.
                # Det er ikke bevis for at kassen er lukket — derfor "unknown".
                status = "unknown"
                evidence = "Domænet svarer, men forsiden bekræfter ikke et abonnement"
        elif any(k in b["text"].lower() for k in ("er lukket", "lukket i danmark", "nedlagt")):
            status = "closed"
            evidence = "Den gamle omtale skriver, at kassen er lukket"
        out.append({
            "slug": slug,
            "name": b["name"],
            "category": (c or {}).get("category") or category_of(b["old_categories"], b["text"]),
            "status": status,
            "provider": provider,
            "evidence": evidence,
            "summary": sentences(b["text"]),
            "old_url": b["old_url"],
            "old_categories": b["old_categories"],
            "year": b["year"],
            "checked": CHECKED,
        })

    out.sort(key=lambda x: (x["status"] != "active", x["category"], x["name"].lower()))
    dest = os.path.join(ROOT, "src", "data")
    os.makedirs(dest, exist_ok=True)
    with open(os.path.join(dest, "kasser.json"), "w") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    from collections import Counter
    print("kasser:", len(out))
    print("status:", Counter(x["status"] for x in out))
    print("kategorier:", Counter(x["category"] for x in out))
    print("aktive pr. kategori:", Counter(x["category"] for x in out if x["status"] == "active"))
    print("uden resumé:", sum(1 for x in out if len(x["summary"]) < 40))


if __name__ == "__main__":
    main()
