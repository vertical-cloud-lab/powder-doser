#!/usr/bin/env python3
"""Survey local (Utah County) and online sources for a balance isolation slab.

Runs on the powder-doser Pi so requests come from the BYU campus IP rather than
a GitHub Actions datacenter block -- several retailers 403 datacenter ranges
outright.  Read-only: it fetches public product and search pages, extracts
title/price/availability, and writes JSON.  No credentials, no logins, no
carts.  Rate-limited to one request per DELAY seconds.

    scp scripts/granite_sourcing_survey.py pi:/tmp/
    ssh pi 'cd /tmp && python3 granite_sourcing_survey.py all' > raw-survey.json

What was learned running this on 2026-08-22, so the next person does not
rediscover it:

* **Accept-Encoding must not include ``br``** -- the Pi's requests build has no
  brotli decoder, so Grizzly returns HTTP 200 full of binary garbage and every
  price regex silently finds nothing.  This looks like a parsing bug and is not.
* **Bot walls, by vendor.** Home Depot, Lowe's and Harbor Freight (PerimeterX)
  refuse everything, including their own JSON APIs, from any IP tried; Shars and
  MSC sit behind AWS WAF and return 202 on search but serve product pages fine;
  Grizzly, Zoro, Amazon, Walmart, KSL and every small fabricator site are open.
* **Search engines are the flakiest part.** DuckDuckGo HTML returns 202 and
  Mojeek serves a captcha.  Discovery of local businesses is better done with a
  search API from the runner; this script is for fetching pages you already
  know you want.
"""

import json
import re
import sys
import time
import urllib.parse

import requests

DELAY = 2.5
TIMEOUT = 35

HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate",          # NOT br -- see module docstring
    "sec-ch-ua": '"Chromium";v="128", "Not;A=Brand";v="24", "Google Chrome";v="128"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
}

# Online: machinist granite surface plates, the "order it and be done" route.
PLATES = [
    ("grizzly", "G9649 9x12x2",  "https://www.grizzly.com/products/grizzly-9-x-12-x-2-granite-surface-plate-no-ledge/g9649"),
    ("grizzly", "G9651 12x18x3", "https://www.grizzly.com/products/grizzly-12-x-18-x-3-granite-surface-plate-no-ledge/g9651"),
    ("grizzly", "G9653 18x18x3", "https://www.grizzly.com/products/grizzly-18-x-18-x-3-granite-surface-plate-no-ledge/g9653"),
    ("grizzly", "G9654 18x24x3", "https://www.grizzly.com/products/grizzly-18-x-24-x-3-granite-surface-plate-no-ledge/g9654"),
    ("shars",   "grade A 12x18", "https://www.shars.com/grade-a-12-x-18-black-granite-surface-plate"),
    ("shars",   "grade AA 12x18","https://www.shars.com/grade-aa-12-x-18-black-granite-surface-plate"),
    ("shars",   "grade A 18x24", "https://www.shars.com/grade-a-18-x-24-black-granite-surface-plate"),
    ("zoro",    "search 12x18",  "https://www.zoro.com/search?q=granite+surface+plate+12+x+18"),
    ("amazon",  "search 12x18x3","https://www.amazon.com/s?k=granite+surface+plate+12+x+18+x+3"),
    ("walmart", "category",      "https://www.walmart.com/c/kp/granite-surface-plate"),
    # Kept in the list as a standing check: HF dropped surface plates, and its
    # own search says so. Expect 403 (PerimeterX) rather than a useful answer.
    ("harborfreight", "search",  "https://www.harborfreight.com/search?q=granite+surface+plate"),
]

# Local: Utah County fabricators, for sink cutouts and remnants.
LOCAL = [
    ("Habitat ReStore (Orem)",        "https://www.habitatuc.org/restore/"),
    ("Rock Solid Granite (Orem)",     "https://fablocator.com/fabricators/ut/orem/rock-solid-granite-countertops"),
    ("Big Mountain Countertops",      "https://www.bigmountaincountertops.com/"),
    ("Little Stone Countertops",      "https://www.littlestonecountertops.com/"),
    ("Accent Countertops remnants",   "https://accentcountertops.com/quartz-marble-granite-remnants-nevada-utah/"),
    ("Cobble Creek (Utah County)",    "https://www.cobblecreekcountertops.com/area/utah-county"),
    ("Quality Granite Utah",          "https://qualitygraniteutah.com/"),
    ("Granite Countertops Utah",      "https://granitecountertopsutah.com/"),
    ("BYU Surplus",                   "https://surplus.byu.edu/"),
]

# Local used market. KSL is Utah's dominant classifieds site; the
# /search/keyword/ form renders listing JSON into the page, /search/ does not.
KSL_TERMS = ["surface plate", "granite plate", "granite remnant",
             "countertop remnant", "granite scrap"]


def flat(html, n=300):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html or "")).strip()[:n]


def uniq(seq, n=12):
    out = []
    for x in seq:
        if x not in out:
            out.append(x)
    return out[:n]


def get(session, url, referer=None):
    headers = dict(HEADERS)
    if referer:
        headers["Referer"] = referer
        headers["Sec-Fetch-Site"] = "same-origin"
    try:
        return session.get(url, headers=headers, timeout=TIMEOUT)
    except Exception as exc:  # noqa: BLE001 -- a dead host is a result, not a crash
        return exc


def survey_plates(session):
    rows = []
    for vendor, label, url in PLATES:
        r = get(session, url)
        rec = {"vendor": vendor, "label": label, "url": url,
               "status": getattr(r, "status_code", str(r))}
        body = getattr(r, "text", "")
        if rec["status"] == 200:
            m = re.search(r"<title[^>]*>(.*?)</title>", body, re.S | re.I)
            rec["title"] = flat(m.group(1), 140) if m else None
            rec["json_price"] = uniq(re.findall(r'"price"\s*:\s*"?([0-9]+\.?[0-9]{0,2})"?', body), 8)
            rec["dollars"] = uniq(re.findall(r'\$\s?([0-9][0-9,]*\.[0-9]{2})', body), 10)
            rec["availability"] = uniq(re.findall(r'"availability"\s*:\s*"([^"]+)"', body), 3)
            rec["is_freight"] = uniq(re.findall(r'"IsFreight"\s*:\s*(true|false)', body), 3)
            rec["ship_weight_lb"] = uniq(re.findall(
                r'(?i)shipping weight\D{0,12}([0-9]{1,4}(?:\.[0-9])?)\s*lb',
                body.replace("\\u003c", "<").replace("\\u003e", ">")), 3)
        else:
            rec["excerpt"] = flat(body, 220)
        rows.append(rec)
        print("[plate] {} {} {}".format(rec["status"], vendor, label),
              file=sys.stderr, flush=True)
        time.sleep(DELAY)
    return rows


def survey_local(session):
    rows = []
    for name, url in LOCAL:
        r = get(session, url)
        rec = {"name": name, "url": url, "status": getattr(r, "status_code", str(r))}
        body = getattr(r, "text", "")
        if rec["status"] == 200:
            m = re.search(r"<title[^>]*>(.*?)</title>", body, re.S | re.I)
            rec["title"] = flat(m.group(1), 140) if m else None
            rec["phones"] = uniq(re.findall(r'(\(?\b8\d{2}\)?[ .-]?\d{3}[ .-]?\d{4}\b)', body), 4)
            rec["addresses"] = uniq(re.findall(
                r'([0-9]{2,5}\s+[NSEW]?\.?\s?[A-Za-z0-9 .]{3,40},?\s*'
                r'(?:Orem|Provo|Springville|Lindon|Pleasant Grove|American Fork|'
                r'Spanish Fork|Payson|Lehi)[, ]*(?:UT|Utah)?\s*8[0-9]{4}?)', body), 4)
            rec["remnant_mentions"] = uniq(re.findall(
                r'(?i)([^.<>]{0,80}(?:remnant|sink cut ?out|scrap|offcut|leftover)[^.<>]{0,80})',
                body), 5)
        else:
            rec["excerpt"] = flat(body, 220)
        rows.append(rec)
        print("[local] {} {}".format(rec["status"], name), file=sys.stderr, flush=True)
        time.sleep(DELAY)
    return rows


def survey_ksl(session):
    get(session, "https://classifieds.ksl.com/")
    time.sleep(1.5)
    rows = {}
    for term in KSL_TERMS:
        url = "https://classifieds.ksl.com/search/keyword/" + urllib.parse.quote(term)
        r = get(session, url, referer="https://classifieds.ksl.com/")
        body = getattr(r, "text", "").replace('\\"', '"')
        items, seen = [], set()
        for m in re.finditer(
            r'"title":"([^"]{5,110})".{0,1200}?"price":([0-9.]+).{0,1200}?"city":"([A-Za-z .\'-]{3,28})"',
            body, re.S,
        ):
            if m.group(1) in seen:
                continue
            seen.add(m.group(1))
            items.append({"title": m.group(1), "price": m.group(2), "city": m.group(3)})
            if len(items) >= 18:
                break
        rows[term] = {"url": url, "status": getattr(r, "status_code", str(r)),
                      "items": items}
        print("[ksl] {} {} -> {}".format(rows[term]["status"], term, len(items)),
              file=sys.stderr, flush=True)
        time.sleep(DELAY)
    return rows


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    mode = argv[0] if argv else "all"
    session = requests.Session()
    out = {"mode": mode}
    if mode in ("all", "plates"):
        out["plates"] = survey_plates(session)
    if mode in ("all", "local"):
        out["local"] = survey_local(session)
    if mode in ("all", "ksl"):
        out["ksl"] = survey_ksl(session)
    json.dump(out, sys.stdout, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
