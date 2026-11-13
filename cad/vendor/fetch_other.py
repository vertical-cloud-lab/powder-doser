"""Fetch the vendor pages, drawings, datasheets and CAD for the purchased parts that are not McMaster or Actuonix
(both carousels): sprockets and the flange bearing (Surplus Center), the #35 chain and A-1 link (Nitro), the dock
electromagnet, solenoid and hall switch (Adafruit), the steel pinion (KHK), the NEMA 11 / NEMA 34 (StepperOnline),
the 2020 frame parts (80/20, West3D, TNUTZ), the load cell (SparkFun), the index magnet (K&J), the 6202 (SKF) and
the vial (DWK/Wheaton).

Each page is opened in a headed Chromium leaving through the doser Pi (common.open_browser), scrolled with the real
pointer, screenshotted and its text saved; files named in DOWNLOADS are then fetched through the same browser
context (so the same proxy and throttle). Everything lands in files/<vendor>/ (git-ignored) and is recorded in
manifest_<vendor>.json with its sha256. Vendor material is not committed.

    xvfb-run -a /tmp/venv/bin/python cad/vendor/fetch_other.py                  # PAGES, then DOWNLOADS
    xvfb-run -a /tmp/venv/bin/python cad/vendor/fetch_other.py sprocket         # only keys containing "sprocket"
    ... fetch_other.py --pass2 | --pass3          # the second and third page lists (found from the first)
    ... fetch_other.py --downloads-only           # DOWNLOADS (PDFs, drawings) only
    ... fetch_other.py --gallery                  # 80/20 gallery images (the profile and bracket drawings)
    ... fetch_other.py --clicks                   # files a server only gives to a clicked link (StepperOnline, KHK)
    ... fetch_other.py --adafruit-cad             # list Adafruit_CAD_Parts for 3872 / 412 / 158 (none there)
    ... fetch_other.py --search                   # the DuckDuckGo searches that found the makers' pages
Run ./pi_socks.sh first (SOCKS tunnel through the Pi). AUDIT_other.md records what each source gave.
"""
from __future__ import annotations

import json
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import FILES, human_click, human_move, open_browser, pause, record  # noqa: E402

# Not reachable from the Pi on 2026-10-27, so not fetched: surpluscenter.com (601139, 601078, 601077, 600174) shows a
# Cloudflare 'verify you are human' check that a pointer click does not clear, and the Wayback Machine has no copy of
# those four pages. The makers' tables (Martin, Tritan, the SBPFL202-10 table) stand in, PAGES3 below.
UNREACHABLE = [
    "https://www.surpluscenter.com/32t-5-8-bore-35p-sprocket/",
    "https://www.surpluscenter.com/15t-5-8-bore-35p-sprocket/",
    "https://www.surpluscenter.com/15t-1-2-bore-35p-sprocket/",
    "https://www.surpluscenter.com/5-8-2-bolt-stamped-steel-flange-bearing/",
    "https://www.grainger.com/product/TRITAN-Sprocket-35-36GA28",   # Akamai block page
    "https://www.sasbearings.com/sbpfl202-bore-bolt-stamped-flange-p-1267.html",   # page gone (404)
]

# (vendor, key, page url): pages read for their spec tables (screenshot + text)
PAGES = [
    ("nitro", "chain_RC35", "https://www.nitrochain.com/35-roller-chain-10ft"),
    ("nitro", "a1_CL35-A1", "https://www.nitrochain.com/35-a1-standard-attachment-connecting-link"),
    ("adafruit", "electromagnet_3872", "https://www.adafruit.com/product/3872"),
    ("adafruit", "solenoid_412", "https://www.adafruit.com/product/412"),
    ("adafruit", "hall_158", "https://www.adafruit.com/product/158"),
    ("stepperonline", "nema11_11HS18-0674S",
     "https://www.omc-stepperonline.com/nema-11-bipolar-1-8deg-9-5ncm-13-5oz-in-0-67a-4-6v-28x28x45mm-4-wires-11hs18-0674s"),
    ("stepperonline", "nema34_34HS59-6004D-E1000",
     "https://www.omc-stepperonline.com/s-series-nema-34-closed-loop-stepper-motor-12-0-nm-1699-68oz-in-encoder-1000ppr-4000cpr-34hs59-6004d-e1000"),
    ("8020", "extrusion_20-2020", "https://8020.net/20-2020.html"),
    ("8020", "bracket_14059", "https://8020.net/14059.html"),
    ("west3d", "bracket_NA0394", "https://west3d.com/products/angle-corner-connector-90-degree-like-openbuilds"),
    ("west3d", "tnut_WES5240M5", "https://west3d.com/products/roll-in-drop-in-t-nuts-for-2020-extrusions-m3-3mm-and-m5-5mm-threads"),
    ("tnutz", "foot_LF-020-A", "https://www.tnutz.com/product/lf-020-a/"),
    ("sparkfun", "loadcell_SEN-14727", "https://www.sparkfun.com/products/14727"),
    ("kj", "magnet_D42-N52", "https://www.kjmagnetics.com/d42-n52-neodymium-disc-magnet"),
    ("vevor", "extrusion_vevor2020",
     "https://www.vevor.com/linear-guide-rail-c_10531/10pcs-39-4in-1000mm-t-slot-2020-aluminum-extrusion-anodized-linear-rail-p_010731760492"),
    ("pfstar", "vial_986546", "https://pfstar.com/986546-20-mL-LS-Vial-22-400-Urea-Cap-PE-Cone-Ln"),
]

# second pass (--pass2): pages found from the first pass's links, a site search, or a maker's own page
PAGES2 = [
    ("stepperonline", "nema11_search", "https://www.omc-stepperonline.com/index.php?route=product/search&search=11HS18-0674S"),
    ("adafruit", "electromagnet_3872_links", "https://www.adafruit.com/product/3872"),
    ("openbuilds", "bracket_angle_corner", "https://openbuildspartstore.com/angle-corner-connector/"),
    ("skf", "bearing_6202-2RSH", "https://www.skf.com/group/products/rolling-bearings/ball-bearings/deep-groove-ball-bearings/productid-6202-2RSH"),
]

# third pass (--pass3): maker / distributor pages for the parts whose vendor page could not be read
PAGES3 = [
    ("khk", "gear_SS1-20A", "https://catalog.khkgears.us/item/spur-gears/spur-gears-ss/ss1-20a"),
    ("martin", "sprocket_35BS32-5-8", "https://www.tristate-bearing.com/martin-35bs32-5-8-mar35bs325-8"),
    ("tritan", "sprocket_35BS15H-5-8_hvh", "https://hvhindustrial.com/product/40338"),
    ("flange", "flange_SBPFL202-10_usab",
     "https://www.usabearingsandbelts.com/m7/SBPFL202-10--5-8-2-bolt-pressed-steel-flanged-bearing-unit-sbpfl202-10.html"),
    ("dwk", "vial_986546",
     "https://www.dwk.com/na/wheaton-liquid-scintillation-vials-borosilicate-glass-22-400-white-urea-caps-attached-to-vials-polyethylene-cone-liner-20-ml-986546"),
]

# Searches (DuckDuckGo's HTML results, through the same browser) used to find the maker's page when the vendor's
# own page is not reachable; results are saved like a page (vendor "search").
SEARCHES = [
    ("search_601139", "surpluscenter 601139 35BS32 sprocket hub diameter length thru bore"),
    ("search_35BS32", "Martin 35BS32 5/8 sprocket hub diameter length thru bore"),
    ("search_35BS15H", "35BS15H 5/8 sprocket hub diameter length thru bore"),
    ("search_SBSFL202", "SBSFL202-10 2 bolt stamped steel flange bearing dimensions"),
    ("search_SS1-20A", "KHK SS1-20A spur gear"),
    ("search_TAL221", "TAL221 load cell datasheet dimensions"),
    ("search_US5881", "Melexis US5881 datasheet UA package"),
    ("search_986546", "Wheaton 986546 20 mL liquid scintillation vial dimensions diameter height"),
    ("search_11HS18", "omc-stepperonline 11HS18-0674S"),
]
DDG = "https://html.duckduckgo.com/html/?q="

# (vendor, key, kind, page it was linked from, file url, file name): drawings / datasheets / CAD
DOWNLOADS: list[tuple[str, str, str, str, str, str]] = [
    ("adafruit", "solenoid_412", "drawing", "https://www.adafruit.com/product/412",
     "https://cdn-shop.adafruit.com/product-files/412/412_C514-B_diagram.PDF", "412_C514-B_diagram.pdf"),
    ("adafruit", "solenoid_412", "datasheet", "https://www.adafruit.com/product/412",
     "https://cdn-shop.adafruit.com/product-files/412/C514-datasheet.pdf", "412_C514-datasheet.pdf"),
    ("adafruit", "hall_158", "datasheet", "https://www.adafruit.com/product/158",
     "https://www.adafruit.com/datasheets/US5881_rev007.pdf", "US5881_rev007.pdf"),
    ("adafruit", "electromagnet_3872", "drawing", "https://www.adafruit.com/product/3872",
     "https://cdn-shop.adafruit.com/product-files/3872/3872_diagram.png", "3872_diagram.png"),
    ("stepperonline", "nema11_11HS18-0674S", "datasheet",
     "https://www.omc-stepperonline.com/nema-11-bipolar-1-8deg-9-5ncm-13-5oz-in-0-67a-4-6v-28x28x45mm-4-wires-11hs18-0674s",
     "https://files.omc-stepperonline.com/11HS18-0674S_Full_Datasheet.pdf", "11HS18-0674S_Full_Datasheet.pdf"),
    ("sparkfun", "loadcell_SEN-14727", "datasheet", "https://www.sparkfun.com/products/14727",
     "https://cdn.sparkfun.com/assets/9/9/a/f/3/TAL221.pdf", "TAL221.pdf"),
    ("stepperonline", "nema34_34HS59-6004D-E1000", "datasheet",
     "https://www.omc-stepperonline.com/s-series-nema-34-closed-loop-stepper-motor-12-0-nm-1699-68oz-in-encoder-1000ppr-4000cpr-34hs59-6004d-e1000",
     "https://files.omc-stepperonline.com/34HS59-6004D-E1000_Full_Datasheet.pdf", "34HS59-6004D-E1000_Full_Datasheet.pdf"),
]

LINK_WORDS = ("diagram", "product-files", "pdf", ".step", ".stp", ".zip", ".igs", ".iges", ".dwg", "download", "drawing", "datasheet", "cad", "spec")


def _scroll_like_a_person(page, n: int = 4) -> None:
    human_move(page, random.uniform(400, 900), random.uniform(300, 600))
    for _ in range(n):
        page.mouse.wheel(0, random.uniform(350, 650))
        time.sleep(random.uniform(0.5, 1.2))
    page.mouse.wheel(0, -5000)
    time.sleep(0.6)


def _challenged(page) -> bool:
    t = page.title().lower()
    return "just a moment" in t or "attention required" in t or "security verification" in t


def _pass_challenge(page, wait: float = 75.0) -> bool:
    """Cloudflare's interstitial: wait for it to clear by itself; if it shows its 'Verify you are human' box,
    move the real pointer onto the box and click it once, as a person would. Returns False if it never clears
    (the site is then treated as refusing the Pi, and another source is used)."""
    t0, clicked = time.time(), 0
    while time.time() - t0 < wait:
        if not _challenged(page):
            return True
        if time.time() - t0 > 6 and clicked < 2:
            box = None
            for fr in page.frames:
                if "challenges.cloudflare.com" in fr.url:
                    try:
                        box = fr.frame_element().bounding_box()
                    except Exception:  # noqa: BLE001
                        box = None
            x, y = (box["x"] + 28, box["y"] + box["height"] / 2) if box and box["width"] > 0 else (256, 337)
            human_move(page, x, y)
            time.sleep(random.uniform(0.4, 0.9))
            page.mouse.click(x, y)
            clicked += 1
            time.sleep(8)
        time.sleep(2)
    return not _challenged(page)


def visit(page, vendor: str, key: str, url: str) -> None:
    d = FILES / vendor
    d.mkdir(parents=True, exist_ok=True)
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=120_000)
    except Exception as e:  # noqa: BLE001
        print(f"  {key}: goto failed: {type(e).__name__}: {str(e)[:120]}", flush=True)
        return
    if _challenged(page) and not _pass_challenge(page):
        page.screenshot(path=str(d / f"{key}.refused.png"))
        print(f"  {key}: REFUSED (bot challenge did not clear)", flush=True)
        return
    try:
        page.wait_for_load_state("networkidle", timeout=15_000)
    except Exception:  # noqa: BLE001
        pass
    pause(1.0, 2.5)
    _scroll_like_a_person(page)
    shot = d / f"{key}.png"
    page.screenshot(path=str(shot), full_page=True, timeout=60_000)
    txt = d / f"{key}.txt"
    txt.write_text(f"URL: {page.url}\nTITLE: {page.title()}\n\n" + page.inner_text("body"))
    links = page.eval_on_selector_all("a[href]", "els => els.map(e => [e.innerText.trim().slice(0,80), e.href])")
    keep = [(t, h) for t, h in links if any(w in (h + " " + t).lower() for w in LINK_WORDS)]
    (d / f"{key}.links.json").write_text(json.dumps(dict(candidates=keep, all=links), indent=1))
    record(vendor, key, shot, page.url, page.url, "screenshot", page.title()[:100])
    record(vendor, key, txt, page.url, page.url, "text", "page text (spec table)")
    print(f"  {key}: ok ({len(keep)} candidate links) title={page.title()[:70]!r}", flush=True)


def gallery(ctx, page, vendor: str, key: str, url: str) -> None:
    """Product pages whose drawing is one of the gallery images (80/20's Magento pages, Adafruit, West3D, TNUTZ):
    click each thumbnail with the pointer, and save each full-size image; then open a 'CAD Files' tab if there is one
    and keep its links."""
    d = FILES / vendor
    d.mkdir(parents=True, exist_ok=True)
    page.goto(url, wait_until="domcontentloaded", timeout=120_000)
    try:
        page.wait_for_load_state("networkidle", timeout=15_000)
    except Exception:  # noqa: BLE001
        pass
    for label in ("Accept Cookies", "Accept"):
        try:
            b = page.get_by_role("button", name=label).first
            if b.is_visible(timeout=1500):
                human_click(page, b)
                break
        except Exception:  # noqa: BLE001
            pass
    srcs: list[str] = []
    thumbs = page.locator(".fotorama__nav__frame")
    for i in range(min(thumbs.count(), 8)):
        try:
            human_click(page, thumbs.nth(i))
            time.sleep(1.5)
            fr = page.locator(".fotorama__stage__frame.fotorama__active").first
            u = fr.get_attribute("href") or fr.locator("img").first.get_attribute("src")
            if u and u not in srcs:
                srcs.append(u)
        except Exception as e:  # noqa: BLE001
            print(f"  {key}: thumb {i}: {type(e).__name__}", flush=True)
    for i, u in enumerate(srcs):
        ext = Path(u.split("?")[0]).suffix or ".jpg"
        download(ctx, page, vendor, key, f"image{i}", url, u, f"{key}.image{i}{ext}")
    try:
        tab = page.get_by_text("CAD Files", exact=True).last
        human_click(page, tab)
        time.sleep(3)
        page.screenshot(path=str(d / f"{key}.cadtab.png"), full_page=False)
        links = page.eval_on_selector_all("a[href]", "els => els.map(e => [e.innerText.trim().slice(0,80), e.href])")
        (d / f"{key}.cadtab.links.json").write_text(json.dumps(links, indent=1))
        record(vendor, key, d / f"{key}.cadtab.png", url, url, "screenshot_cad", "CAD Files tab")
    except Exception as e:  # noqa: BLE001
        print(f"  {key}: no CAD tab ({type(e).__name__})", flush=True)
    print(f"  {key}: gallery {len(srcs)} images", flush=True)


def adafruit_cad(ctx) -> list[str]:
    """Adafruit publishes CAD in github.com/adafruit/Adafruit_CAD_Parts, one folder per product id: list the repo's
    tree (through the same browser context) and keep the paths for the products used here."""
    r = ctx.request.get("https://api.github.com/repos/adafruit/Adafruit_CAD_Parts/git/trees/main?recursive=1", timeout=180_000)
    if not r.ok:
        print(f"  adafruit CAD tree: HTTP {r.status}", flush=True)
        return []
    tree = r.json().get("tree", [])
    ids = ("3872", "412 ", "412_", "/412", "158 ", "158_", "/158", "14727", "electromagnet", "solenoid", "US5881", "hall")
    hits = [t["path"] for t in tree if any(i.lower() in t["path"].lower() for i in ids)]
    d = FILES / "adafruit"
    d.mkdir(parents=True, exist_ok=True)
    (d / "Adafruit_CAD_Parts.hits.json").write_text(json.dumps(hits, indent=1))
    print(f"  adafruit CAD tree: {len(tree)} entries, {len(hits)} hits", flush=True)
    return hits


def click_download(ctx, page, vendor: str, key: str, kind: str, src_page: str, href_part: str, name: str) -> None:
    """For files the server only hands to a real navigation (StepperOnline's datasheets answer 403 to a plain request,
    KHK builds its 2D drawing on request): open the product page, click the link with the pointer, and keep the
    download, or a screenshot of the tab it opens."""
    d = FILES / vendor
    d.mkdir(parents=True, exist_ok=True)
    page.goto(src_page, wait_until="domcontentloaded", timeout=120_000)
    _scroll_like_a_person(page, 2)
    pause(2.0, 3.5)
    link = page.locator(f"a[href*='{href_part}']").first
    n0 = len(ctx.pages)
    try:
        with page.expect_download(timeout=45_000) as dl:
            human_click(page, link)
        dl.value.save_as(str(d / name))
        record(vendor, key, d / name, src_page, dl.value.url, kind, name)
        print(f"  {key}/{kind}: downloaded {name}", flush=True)
        return
    except Exception as e:  # noqa: BLE001
        print(f"  {key}/{kind}: no download ({type(e).__name__}); looking for a new tab", flush=True)
    pages = ctx.pages
    tab = pages[-1] if len(pages) > n0 else page
    try:
        tab.wait_for_load_state("load", timeout=60_000)
    except Exception:  # noqa: BLE001
        pass
    time.sleep(6)
    shot = d / (Path(name).stem + ".tab.png")
    tab.screenshot(path=str(shot))
    record(vendor, key, shot, src_page, tab.url, kind + "_screenshot", "the tab the link opened")
    print(f"  {key}/{kind}: tab screenshot {shot.name} ({tab.url[:90]})", flush=True)
    if tab is not page:
        tab.close()


CLICKS = [
    ("stepperonline", "nema11_11HS18-0674S", "datasheet",
     "https://www.omc-stepperonline.com/nema-11-bipolar-1-8deg-9-5ncm-13-5oz-in-0-67a-4-6v-28x28x45mm-4-wires-11hs18-0674s",
     "11HS18-0674S_Full_Datasheet.pdf", "11HS18-0674S_Full_Datasheet.pdf"),
    ("stepperonline", "nema34_34HS59-6004D-E1000", "datasheet",
     "https://www.omc-stepperonline.com/s-series-nema-34-closed-loop-stepper-motor-12-0-nm-1699-68oz-in-encoder-1000ppr-4000cpr-34hs59-6004d-e1000",
     "34HS59-6004D-E1000_Full_Datasheet.pdf", "34HS59-6004D-E1000_Full_Datasheet.pdf"),
    ("khk", "gear_SS1-20A", "drawing", "https://catalog.khkgears.us/item/spur-gears/spur-gears-ss/ss1-20a",
     "FFcreateWK.do", "SS1-20A_2D_sales_drawing.pdf"),
]

GALLERIES = [
    ("8020", "extrusion_20-2020", "https://8020.net/20-2020.html"),
    ("8020", "bracket_14059", "https://8020.net/14059.html"),
]


def download(ctx, page, vendor: str, key: str, kind: str, src_page: str, url: str, name: str) -> None:
    d = FILES / vendor
    d.mkdir(parents=True, exist_ok=True)
    out = d / name
    try:
        r = ctx.request.get(url, timeout=180_000, headers={"Referer": src_page})
        if r.status in (401, 403):   # some sites (StepperOnline) want the product page's cookies first: open it, then retry
            page.goto(src_page, wait_until="domcontentloaded", timeout=120_000)
            _scroll_like_a_person(page, 2)
            pause(2.0, 4.0)
            r = ctx.request.get(url, timeout=180_000, headers={"Referer": src_page})
        if not r.ok:
            print(f"  {key}/{kind}: HTTP {r.status} for {url}", flush=True)
            return
        out.write_bytes(r.body())
    except Exception as e:  # noqa: BLE001
        print(f"  {key}/{kind}: failed: {type(e).__name__}: {str(e)[:120]}", flush=True)
        return
    record(vendor, key, out, src_page, url, kind, name)
    print(f"  {key}/{kind}: {out.stat().st_size} bytes -> {out.relative_to(FILES)}", flush=True)


def main(filters: list[str]) -> None:
    from playwright.sync_api import sync_playwright

    want = (lambda k: any(f in k for f in filters)) if filters else (lambda k: True)
    with sync_playwright() as pw:
        browser, ctx, page = open_browser(pw)
        try:
            if "--search" in sys.argv:
                from urllib.parse import quote_plus
                for key, q in SEARCHES:
                    if want(key):
                        print(f"[search] {key}", flush=True)
                        visit(page, "search", key, DDG + quote_plus(q))
                        pause(3.0, 6.0)
                return
            if "--clicks" in sys.argv:
                for vendor, key, kind, src, href, name in CLICKS:
                    if want(key):
                        print(f"[{vendor}] {key} (click {kind})", flush=True)
                        try:
                            click_download(ctx, page, vendor, key, kind, src, href, name)
                        except Exception as e:  # noqa: BLE001
                            print(f"  {key}: failed {type(e).__name__}: {str(e)[:120]}", flush=True)
                        pause(2.0, 4.0)
                return
            if "--adafruit-cad" in sys.argv:
                adafruit_cad(ctx)
                return
            if "--gallery" in sys.argv:
                for vendor, key, url in GALLERIES:
                    if want(key):
                        print(f"[{vendor}] {key} (gallery)", flush=True)
                        gallery(ctx, page, vendor, key, url)
                        pause(2.0, 4.0)
                return
            for vendor, key, url in (PAGES2 if "--pass2" in sys.argv else PAGES3 if "--pass3" in sys.argv else PAGES):
                if want(key) and "--downloads-only" not in sys.argv:
                    print(f"[{vendor}] {key}", flush=True)
                    visit(page, vendor, key, url)
                    pause(2.0, 4.0)
            for vendor, key, kind, src, url, name in DOWNLOADS:
                if want(key) and "--pages-only" not in sys.argv:
                    download(ctx, page, vendor, key, kind, src, url, name)
                    pause(1.5, 3.0)
        finally:
            browser.close()


if __name__ == "__main__":
    main([a for a in sys.argv[1:] if not a.startswith("--")])
