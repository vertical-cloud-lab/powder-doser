"""Read McMaster-Carr's own product page for every McMaster part in the two carousels, and download
its 3-D STEP and 2-D PDF drawing, logged out, through the doser Pi.

Since mid-October 2026 a logged-out browser on a residential IP sees product pages again, with the
CAD menu (on 2 Oct they needed a login; see cad/full-assembly/README.md). mcmaster.com refuses
datacenter IPs, so this drives a headed Chromium on the runner whose traffic leaves through the
Pi (SOCKS5 on 127.0.0.1:1080, opened by ./pi_socks.sh), throttled to 400 kB/s, one page at a
time with pauses. For each part number it moves the pointer to the CAD menu, picks "3-D STEP",
clicks Download, then does the same for "2-D PDF". It never logs in.

    ./pi_socks.sh
    xvfb-run -a python fetch_mcmaster.py                 # every part in PARTS
    xvfb-run -a python fetch_mcmaster.py 7321K31 6659K65  # just these

Writes (committed): mcmaster_specs.json, the page's own spec table, title and price per part,
with the date read; manifest_mcmaster.json, sha256 of each downloaded file.
Not committed (files/mcmaster/): <PN>.step, <PN>.pdf and a screenshot of each page.
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
from common import FILES, VENDOR, human_click, human_move, open_browser, pause, record  # noqa: E402

SPECS = VENDOR / "mcmaster_specs.json"

PARTS = [  # every McMaster part number either carousel's CAD or BoM uses
    "7321K31", "5501N12", "5615N15", "95615A120", "6408K14", "6408K75", "91292A126", "93625A200",
    "90265A121", "6659K65", "95630A630", "93625A100", "94459A774", "92545A179",
]


def wait_content(page, min_chars: int = 2500, max_s: float = 90) -> str:
    t0 = time.time()
    txt = ""
    while time.time() - t0 < max_s:
        time.sleep(2)
        txt = page.evaluate("document.body.innerText")
        if len(txt) > min_chars or "Log in to view" in txt or "restricted" in txt.lower():
            break
    return txt


def spec_table(page) -> dict:
    """The product page's attribute table as {name: value}."""
    return page.evaluate("""(() => {
        const out = {};
        for (const tr of document.querySelectorAll('tr')) {
            const td = tr.querySelectorAll('td, th');
            if (td.length === 2) {
                const k = td[0].innerText.trim(), v = td[1].innerText.trim();
                if (k && v && k.length < 60 && v.length < 200) out[k] = v;
            }
        }
        return out; })()""")


def pick_cad(page, label: str) -> str | None:
    """Open the CAD menu with the pointer, choose `label` ("3-D STEP", "2-D PDF"), return the download URL."""
    combo = page.locator("button[role=combobox]").first
    human_click(page, combo)
    time.sleep(1.0)
    opt = page.get_by_role("option", name=label, exact=True)
    if opt.count() == 0:
        opt = page.locator(f"text={label}").first
    human_click(page, opt.first if hasattr(opt, "first") else opt)
    time.sleep(2.0)
    a = page.locator("a[class*=downloadAnchor]").first
    return a.evaluate("e => e.href") if a.count() else None   # absolute URL


def fetch(page, ctx, pn: str, out: Path) -> dict:
    url = f"https://www.mcmaster.com/{pn}/"
    page.goto(url, wait_until="domcontentloaded", timeout=120000)
    txt = wait_content(page)
    human_move(page, 680, 420)
    pause(1.0, 2.0)
    if "Log in to view" in txt or len(txt) < 1500:
        return dict(pn=pn, url=url, error="product page needs a login or did not load")
    lines = [ln.strip() for ln in txt.splitlines() if ln.strip()]
    i = lines.index(pn) if pn in lines else -1
    title = " / ".join(lines[max(0, i - 3):i]) if i > 0 else ""
    price = next((ln for ln in lines[i:i + 8] if ln.startswith("$")), "") if i >= 0 else ""
    rec = dict(pn=pn, url=url, title=title, price=price, specs=spec_table(page),
               read=datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    page.screenshot(path=str(out / f"{pn}_page.png"))
    for label, ext, kind in (("3-D STEP", "step", "step"), ("2-D PDF", "pdf", "drawing")):
        try:
            href = pick_cad(page, label)
            if not href:
                rec[f"{kind}_error"] = "no download link"
                continue
            r = ctx.request.get(href, timeout=300000)
            if not r.ok:
                rec[f"{kind}_error"] = f"HTTP {r.status}"
                continue
            dest = out / f"{pn}.{ext}"
            dest.write_bytes(r.body())
            ent = record("mcmaster", pn, dest, url, href.split("?")[0], kind)
            rec[kind] = dict(file=ent["file"], bytes=ent["bytes"], sha256=ent["sha256"])
        except Exception as e:  # keep going: one part's menu failing shouldn't stop the rest
            rec[f"{kind}_error"] = repr(e)[:200]
        pause(1.5, 3.0)
    return rec


def main(pns: list[str]) -> None:
    out = FILES / "mcmaster"
    out.mkdir(parents=True, exist_ok=True)
    specs = json.loads(SPECS.read_text()) if SPECS.exists() else {}
    with sync_playwright() as pw:
        browser, ctx, page = open_browser(pw)
        for pn in pns:
            t0 = time.time()
            try:
                rec = fetch(page, ctx, pn, out)
            except Exception as e:
                rec = dict(pn=pn, error=repr(e)[:300])
            specs[pn] = rec
            SPECS.write_text(json.dumps(specs, indent=1, sort_keys=True) + "\n")
            got = [k for k in ("step", "drawing") if k in rec]
            print(f"{pn}: {rec.get('title', '')[:70]} | {rec.get('price', '')} | {got} | "
                  f"{rec.get('error', '') or rec.get('step_error', '')} ({time.time() - t0:.0f} s)", flush=True)
            pause(2.0, 4.0)
        browser.close()


if __name__ == "__main__":
    main(sys.argv[1:] or PARTS)
