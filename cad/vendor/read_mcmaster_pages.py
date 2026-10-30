"""Read McMaster-Carr pages for the v3/v4 carousels' new hardware, logged out, through the doser Pi.

Lighter than fetch_mcmaster.py: no CAD downloads, only what the BoM needs. Two kinds of argument:

    pn:<PN>    the product page https://www.mcmaster.com/<PN>/: title, price line and spec table, added to
               mcmaster_specs.json the way fetch_mcmaster.py adds them (without the step/drawing keys)
    url:<URL>  a family or category page: its table rows (part number, columns) and its text, saved to
               files/mcmaster/pages/<slug>.json for choosing a part number (not committed)

    ./pi_socks.sh
    xvfb-run -a python read_mcmaster_pages.py pn:9642K23 url:https://www.mcmaster.com/98381A/

Same browser as the other fetchers (common.open_browser): headed Chromium, SOCKS5 through the Pi on
127.0.0.1:1080, throttled to 400 kB/s, real pointer moves, pauses between pages. It never logs in.
"""
from __future__ import annotations

import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import FILES, VENDOR, human_move, open_browser, pause  # noqa: E402
from fetch_mcmaster import spec_table, wait_content  # noqa: E402

SPECS = VENDOR / "mcmaster_specs.json"
PN_RE = re.compile(r"\b\d{4,5}[A-Z]\d{1,4}\b")
ROWS_JS = """() => [...document.querySelectorAll('tr')].map(r => r.innerText.replace(/\\s+/g, ' | ').trim()).filter(t => t)"""


def read_pn(page, pn: str, out: Path) -> dict:
    url = f"https://www.mcmaster.com/{pn}/"
    page.goto(url, wait_until="domcontentloaded", timeout=120000)
    txt = wait_content(page)
    human_move(page, 680, 420)
    pause(1.0, 2.0)
    txt = page.evaluate("document.body.innerText")
    if "Log in to view" in txt or len(txt) < 1500:
        return dict(pn=pn, url=url, error="product page needs a login or did not load")
    lines = [ln.strip() for ln in txt.splitlines() if ln.strip()]
    i = lines.index(pn) if pn in lines else -1
    title = " / ".join(lines[max(0, i - 3):i]) if i > 0 else ""
    price = next((ln for ln in lines[i:i + 12] if ln.startswith("$")), "") if i >= 0 else ""
    if price and "per" not in price and i >= 0:          # "$12.10" then "per pack of 50" on its own line
        j = lines.index(price, i)
        nxt = lines[j + 1] if j + 1 < len(lines) else ""
        if nxt.lower().startswith(("per", "each")):
            price = f"{price} {nxt}"
    rec = dict(pn=pn, url=url, title=title, price=price, specs=spec_table(page),
               read=datetime.now(timezone.utc).strftime("%Y-%m-%d"), note="read for the v3/v4 BoM (no CAD fetched)")
    page.screenshot(path=str(out / f"{pn}_page.png"))
    (out / f"{pn}_page.txt").write_text(txt)
    return rec


def read_url(page, url: str, out: Path) -> dict:
    page.goto(url, wait_until="domcontentloaded", timeout=120000)
    t0, last, stable = time.time(), -1, 0
    while time.time() - t0 < 60:
        time.sleep(1.5)
        n = len(page.evaluate("document.body.innerText"))
        stable = stable + 1 if n == last else 0
        last = n
        if time.time() - t0 > 8 and stable >= 3 and n > 1500:
            break
    for _ in range(5):                                   # tables load lazily: scroll down with the wheel
        human_move(page, 700, 500)
        page.mouse.wheel(0, 1600)
        time.sleep(1.2)
    time.sleep(2)
    rows = page.evaluate(ROWS_JS)
    txt = page.evaluate("document.body.innerText")
    links = page.evaluate("() => [...document.querySelectorAll('a')].map(a => [a.innerText.trim().slice(0, 80), a.href])"
                          ".filter(x => x[1].includes('/products/') || /\\/\\d{4,5}[A-Z]/.test(x[1]))")
    slug = re.sub(r"[^a-z0-9]+", "_", url.lower().split("mcmaster.com/")[-1]).strip("_")[:80] or "root"
    rec = dict(url=url, final_url=page.url, title=page.title(), rows=rows, text=txt, links=links,
               read=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"))
    (out / f"{slug}.json").write_text(json.dumps(rec, indent=1) + "\n")
    page.screenshot(path=str(out / f"{slug}.png"))
    print(f"  saved {out / (slug + '.json')}: {len(rows)} rows, {len(txt)} chars, final {page.url[:100]}", flush=True)
    return rec


def main(args: list[str]) -> None:
    out = FILES / "mcmaster"
    pages = out / "pages"
    pages.mkdir(parents=True, exist_ok=True)
    specs = json.loads(SPECS.read_text()) if SPECS.exists() else {}
    with sync_playwright() as pw:
        browser, ctx, page = open_browser(pw)
        for a in args:
            kind, _, val = a.partition(":")
            t0 = time.time()
            try:
                if kind == "pn":
                    rec = read_pn(page, val, out)
                    if "error" not in rec or val not in specs:
                        specs[val] = {**specs.get(val, {}), **rec}   # keep an earlier run's step/drawing keys
                        SPECS.write_text(json.dumps(specs, indent=1, sort_keys=True) + "\n")
                    print(f"{val}: {rec.get('title', '')[:90]} | {rec.get('price', '')} | {rec.get('error', '')} "
                          f"({time.time() - t0:.0f} s)", flush=True)
                    keep = ("Diameter", "Length", "Material", "Grade", "Hardness", "OD", "ID", "Thickness", "Thread Size",
                            "Outside Diameter", "Inside Diameter", "Compressed Length", "Spring Rate", "System of Measurement")
                    for k, v in rec.get("specs", {}).items():
                        if any(s.lower() in k.lower() for s in keep):
                            print(f"    {k}: {v}", flush=True)
                else:
                    read_url(page, val if kind == "url" else a, pages)
            except Exception as e:
                print(f"{a}: ERROR {e!r}"[:300], flush=True)
            pause(2.0, 4.0)
        browser.close()


if __name__ == "__main__":
    main(sys.argv[1:])
