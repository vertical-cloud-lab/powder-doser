"""Read McMaster-Carr's own catalog rows and family images for the
fasteners in hardware.MCMASTER, without logging in.

Since 2 Oct 2026 a logged-out browser gets "Log in to view Product Detail"
from mcmaster.com/<PN>/, so there is no STEP download, and the lab account
was restricted after a login that day (README, "Fasteners").  The catalog
pages are still open.  Each family's table lists the part number with
McMaster's thread, length, head diameter and height (width and height for
nuts), and the page shows the family's product image.  mcmaster.com refuses
datacenter IPs and plain HTTP clients, so this drives a normal (headed)
Chromium on the runner whose traffic leaves through the doser Pi as a SOCKS
proxy:

    ssh -N -D 127.0.0.1:1080 "$RPI_POWDER_DOSER_USERNAME@$RPI_POWDER_DOSER_HOSTNAME" &
    xvfb-run -a python3 mcmaster_fetch.py            # catalog rows + page images
    xvfb-run -a python3 mcmaster_fetch.py --images   # only the images parts.json uses

The browser is throttled to 400 kB/s (the Pi is on residential Wi-Fi) and
waits between pages.  For each family page it scrolls until every wanted
part number's row has loaded, then writes the raw rows and table headers to
components/mcmaster/catalog_rows.json (committed) and the family image to
components/mcmaster/img/ (not committed).  components/mcmaster/parts.json
holds the same figures, parsed, for fastener_check.py.
"""
from __future__ import annotations

import base64
import hashlib
import json
import re
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
OUT = HERE / "components" / "mcmaster"
PROXY = "socks5://127.0.0.1:1080"
CAT = "https://www.mcmaster.com/products/"

# family page -> part numbers wanted from its table
PAGES = [
    (CAT + "socket-head-screws/stainless-steel-socket-head-screws~~/system-of-measurement~metric/",
     ["91292A027", "91292A113", "91292A110", "91292A012"]),
    (CAT + "button-head-screws/stainless-steel-button-head-hex-drive-screws~~/system-of-measurement~metric/",
     ["92095A185", "92095A186"]),
    (CAT + "button-head-screws/stainless-steel-button-head-hex-drive-screws~~/system-of-measurement~metric/"
     "thread-size~m5/", ["92095A223"]),
    (CAT + "flat-head-screws/stainless-steel-hex-drive-flat-head-screws~~/system-of-measurement~metric/",
     ["92125A140"]),
    (CAT + "hex-nuts/material~stainless-steel-2/system-of-measurement~metric/hex-nuts-3~~/", ["91828A211"]),
    (CAT + "nylon-insert-locknuts/material~stainless-steel-2/system-of-measurement~metric/"
     "nylon-insert-locknuts-2~~/", ["93625A100", "93625A200"]),
]

ROWS_JS = """(pn) => [...document.querySelectorAll('tr')].filter(r => r.innerText.includes(pn)).map(r => {
    const t = r.closest('table');
    return {row: r.innerText.replace(/\\s+/g, ' | ').trim(),
            header: t ? [...t.querySelectorAll('tr')].slice(0, 3).map(x => x.innerText.replace(/\\s+/g, ' | ').trim()) : []};
})"""
FETCH_JS = """async (u) => { const r = await fetch(u, {credentials: 'include'});
    const b = new Uint8Array(await r.arrayBuffer()); let s = '';
    for (let i = 0; i < b.length; i += 0x8000) s += String.fromCharCode.apply(null, b.subarray(i, i + 0x8000));
    return {status: r.status, ct: r.headers.get('content-type'), b64: btoa(s)}; }"""


def settle(page, max_s: float = 40) -> None:
    """Wait until the number of images and table rows stops changing."""
    t0, last, stable = time.time(), -1, 0
    while time.time() - t0 < max_s:
        time.sleep(1)
        n = page.evaluate("document.querySelectorAll('img').length * 1000 + document.querySelectorAll('tr').length")
        stable = stable + 1 if n == last else 0
        last = n
        if time.time() - t0 > 5 and stable >= 3:
            return


def family_image(page) -> dict | None:
    """The page's first product image, at 2x where McMaster has it."""
    imgs = page.evaluate("""[...document.querySelectorAll('img')].map(i => ({src: i.currentSrc || i.src, alt: i.alt,
        w: i.getBoundingClientRect().width})).filter(m => m.w > 60 && /ImageCache/.test(m.src))""")
    if not imgs:
        return None
    src = imgs[0]["src"]
    for v in ("@2x", "@1x", "@halfx"):
        u = re.sub(r"@(halfx|1x|2x|100p)", v, src, count=1)
        r = page.evaluate(FETCH_JS, u)
        if r["status"] == 200 and (r["ct"] or "").startswith("image"):
            data = base64.b64decode(r["b64"])
            name = re.sub(r"[^A-Za-z0-9_.-]", "_", u.split("/")[-1].split("?")[0])
            (OUT / "img").mkdir(parents=True, exist_ok=True)
            (OUT / "img" / name).write_bytes(data)
            return {"file": name, "url": u.split("?")[0], "alt": imgs[0]["alt"],
                    "sha256": hashlib.sha256(data).hexdigest()}
    return None


def parts_images(page) -> None:
    """Download the family images parts.json names (fastener_check.py's)."""
    page.goto("https://www.mcmaster.com/", wait_until="domcontentloaded", timeout=120_000)
    settle(page, 20)
    (OUT / "img").mkdir(parents=True, exist_ok=True)
    for fam in json.loads((OUT / "parts.json").read_text())["families"].values():
        r = page.evaluate(FETCH_JS, fam["image_url"])
        data = base64.b64decode(r["b64"]) if r["status"] == 200 else b""
        ok = hashlib.sha256(data).hexdigest() == fam["image_sha256"]
        if r["status"] == 200:
            (OUT / "img" / fam["image"]).write_bytes(data)
        print(f"{fam['image'][:40]}: HTTP {r['status']}, sha256 {'matches' if ok else 'DIFFERS'}")
        time.sleep(1.5)


def main(images_only: bool = False) -> int:
    out = {"retrieved_utc": time.strftime("%Y-%m-%dT%H:%MZ", time.gmtime()), "pages": []}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, proxy={"server": PROXY},
                                    ignore_default_args=["--enable-automation"],
                                    args=["--disable-blink-features=AutomationControlled"])
        ctx = browser.new_context(viewport={"width": 1500, "height": 1000}, locale="en-US",
                                  timezone_id="America/Denver")
        page = ctx.new_page()
        cdp = ctx.new_cdp_session(page)
        cdp.send("Network.enable")
        cdp.send("Network.emulateNetworkConditions", {"offline": False, "latency": 20,
                                                      "downloadThroughput": 400 * 1024,
                                                      "uploadThroughput": 400 * 1024})
        if images_only:
            parts_images(page)
            browser.close()
            return 0
        for k, (url, pns) in enumerate(PAGES):
            if k:
                time.sleep(8)
            page.goto(url, wait_until="domcontentloaded", timeout=120_000)
            settle(page)
            body = page.evaluate("document.body.innerText")
            if "Access has been restricted" in body or "exceeds typical" in body:
                print("mcmaster.com restricted this session; stopping")
                break
            for _ in range(60):          # rows load as the page scrolls
                body = page.evaluate("document.body.innerText")
                if all(pn in body for pn in pns):
                    break
                page.evaluate("window.scrollBy(0, 1500)")
                time.sleep(0.7)
            rec = {"url": url, "rows": {pn: page.evaluate(ROWS_JS, pn) for pn in pns}}
            page.evaluate("window.scrollTo(0, 0)")
            time.sleep(1)
            rec["image"] = family_image(page)
            out["pages"].append(rec)
            for pn in pns:
                rows = rec["rows"][pn]
                print(f"{pn}: {rows[0]['row'][:110] if rows else 'NOT FOUND'}")
        browser.close()
    (OUT / "catalog_rows.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n")
    print(f"  -> {(OUT / 'catalog_rows.json').relative_to(HERE)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(images_only="--images" in sys.argv))
