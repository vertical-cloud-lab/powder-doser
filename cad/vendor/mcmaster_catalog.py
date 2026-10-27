"""Read McMaster-Carr catalog tables (part number, the row's columns and the table's headers) for
the families the carousels still had as "estimate", logged out, through the doser Pi, so every
McMaster line in the BoMs can name a real part number. Writes mcmaster_catalog_rows.json.

    /tmp/pi_socks.sh && xvfb-run -a python mcmaster_catalog.py
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import VENDOR, human_move, open_browser, pause  # noqa: E402

OUT = VENDOR / "mcmaster_catalog_rows.json"
CAT = "https://www.mcmaster.com/products/"
PAGES = {   # McMaster's family pages (https://www.mcmaster.com/<family prefix>/) list every size with its part number
    "90265A": "https://www.mcmaster.com/90265A/",   # 18-8 hex-drive shoulder screws, metric (4 x 16 for the P16 clevis)
    "91585A": "https://www.mcmaster.com/91585A/",   # 18-8 dowel pins, metric
    "91595A": "https://www.mcmaster.com/91595A/",   # hardened dowel pins, metric
    "6408K": "https://www.mcmaster.com/6408K/",     # spider coupling hubs and spiders (L090 bores)
    "92095A": "https://www.mcmaster.com/92095A/",   # 18-8 button head hex drive screws, metric
    "91292A": "https://www.mcmaster.com/91292A/",   # 18-8 socket head screws, metric
    "92125A": "https://www.mcmaster.com/92125A/",   # 18-8 flat head hex drive screws, metric
    "e_rings_metric": "https://www.mcmaster.com/products/e-style-retaining-rings/system-of-measurement~metric/",
}
PN_RE = re.compile(r"\b\d{4,5}[A-Z]\d{1,4}\b")
ROWS_JS = """() => [...document.querySelectorAll('tr')].map(r => {
    const t = r.closest('table');
    return {row: r.innerText.replace(/\\s+/g, ' | ').trim(),
            header: t ? [...t.querySelectorAll('thead tr, tr')].slice(0, 2).map(x => x.innerText.replace(/\\s+/g, ' | ').trim()) : []};
})"""


def settle(page, max_s: float = 60) -> None:
    t0, last, stable = time.time(), -1, 0
    while time.time() - t0 < max_s:
        time.sleep(1.5)
        n = page.evaluate("document.querySelectorAll('tr').length")
        stable = stable + 1 if n == last else 0
        last = n
        if time.time() - t0 > 6 and stable >= 3 and n > 0:
            return


def main(keys: list[str]) -> None:
    data = json.loads(OUT.read_text()) if OUT.exists() else {}
    with sync_playwright() as pw:
        browser, ctx, page = open_browser(pw)
        for k in keys:
            url = PAGES[k]
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=120000)
                settle(page)
                for y in range(6):                     # tables load lazily: scroll down with the wheel
                    human_move(page, 700, 500)
                    page.mouse.wheel(0, 1600)
                    time.sleep(1.2)
                settle(page, 20)
                rows = [r for r in page.evaluate(ROWS_JS) if PN_RE.search(r["row"])]
                data[k] = dict(url=url, final_url=page.url, title=page.title(), rows=rows)
                print(f"{k}: {len(rows)} rows ({page.url[:90]})", flush=True)
            except Exception as e:
                data[k] = dict(url=url, error=repr(e)[:200])
                print(f"{k}: ERROR {e!r}"[:200], flush=True)
            OUT.write_text(json.dumps(data, indent=1) + "\n")
            pause(2, 4)
        browser.close()


if __name__ == "__main__":
    main(sys.argv[1:] or list(PAGES))
