"""Download Actuonix's own P16 datasheet and 3-D model (and the LAC board's) through the doser Pi.

Opens actuonix.com/datasheets in a headed Chromium whose traffic leaves through the Pi
(actuonix.com refuses datacenter IPs), moves the pointer to each link and clicks it, and
records each file in manifest_actuonix.json with its sha256.

    /tmp/pi_socks.sh                      # SOCKS5 tunnel through the Pi on 127.0.0.1:1080
    xvfb-run -a python fetch_actuonix.py
"""
from __future__ import annotations

import sys
import zipfile
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import FILES, human_move, open_browser, pause, record  # noqa: E402

PAGE = "https://www.actuonix.com/datasheets"
WANT = [  # (link text on the page, manifest key, kind)
    ("P16 Datasheet", "actuonix_p16", "datasheet"),
    ("P16 Series 3D Model (STP)", "actuonix_p16", "zip"),
    ("Actuonix LAC Datasheet", "actuonix_lac", "datasheet"),
    ("LAC 3D Model", "actuonix_lac", "zip"),
]


def main() -> None:
    out = FILES / "actuonix"
    out.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        browser, ctx, page = open_browser(pw)
        page.goto(PAGE, wait_until="domcontentloaded", timeout=90000)
        pause(4, 6)
        page.screenshot(path=str(out / "datasheets_page.png"))
        for text, key, kind in WANT:
            link = page.get_by_role("link", name=text, exact=True).first
            href = link.evaluate("a => a.href")   # absolute URL
            link.scroll_into_view_if_needed()
            box = link.bounding_box()
            human_move(page, box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)   # pointer onto the link
            r = ctx.request.get(href, timeout=600000)   # same browser context, so the same Pi proxy
            if not r.ok:
                print(f"  {text}: HTTP {r.status}")
                continue
            dest = out / Path(href.split("?")[0]).name.replace("%20", "_")
            dest.write_bytes(r.body())
            ent = record("actuonix", key, dest, PAGE, href, kind)
            print(f"  {dest.name}: {ent['bytes'] / 1e6:.2f} MB")
            if kind == "zip":
                with zipfile.ZipFile(dest) as z:
                    for n in z.namelist():
                        if n.lower().endswith((".stp", ".step")):
                            p = out / Path(n).name
                            p.write_bytes(z.read(n))
                            record("actuonix", f"{key}:{Path(n).stem}", p, PAGE, href + "#" + n, "step",
                                   note=f"extracted from {dest.name}")
            pause()
        browser.close()


if __name__ == "__main__":
    main()
