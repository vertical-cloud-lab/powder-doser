#!/usr/bin/env python3
"""Read open-access full texts in a headed Chrome whose traffic leaves through the doser Pi.

Same plumbing as cad/vendor/ on the #128 branch and the costs in PR #190: a headed Chrome (Playwright, under
Xvfb) uses the Pi as a SOCKS5 proxy (`pi_socks.sh` opens it on 127.0.0.1:1080), moves the real pointer to each
link and clicks it, and is throttled to 400 kB/s for the Pi's Wi-Fi. Nothing is installed on the Pi.

Only open-access pages are opened (arXiv, MDPI, Nature Scientific Reports, JOSS, EPJ Web of Conferences,
institutional repositories). The texts stay in the git-ignored files/ folder because the repo is public;
manifest.json records the URL, size, sha256 and date of each one so a rebuild can check it read the same bytes.

Usage (from docs/physics-simulations/fulltext/):
  ./pi_socks.sh
  xvfb-run -a python fetch_fulltexts.py            # all papers
  xvfb-run -a python fetch_fulltexts.py imole2016  # one paper
"""
from __future__ import annotations

import hashlib
import io
import json
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
FILES = HERE / "files"
MANIFEST = HERE / "manifest.json"
PROXY = "socks5://127.0.0.1:1080"
THROTTLE_BPS = 400_000

# key: (citation, landing page, how to get the text)
#   ("pdf", css/text selector of the PDF link on the landing page)  -> pointer clicks the link, PDF bytes captured
#   ("html", css selector of the article body)                       -> article text read from the page
PAPERS = {
    "imole2016_dosing_dem": (
        "Imole, Krijgsman, Weinhart, Magnanimo, Chavez Montes, Ramaioli, Luding (2016) Experiments and discrete "
        "element simulation of the dosing of cohesive powders in a simplified geometry. Powder Technology 287:108. "
        "arXiv:1410.2886", "https://arxiv.org/abs/1410.2886", ("pdf", "a.download-pdf")),
    "meier2019_cohesion_metal_powders": (
        "Meier, Weissbach, Weinberg, Wall, Hart (2019) Modeling and characterization of cohesion in fine metal "
        "powders with a focus on additive manufacturing process simulations. Powder Technology 343:855. "
        "arXiv:1804.06816", "https://arxiv.org/abs/1804.06816", ("pdf", "a.download-pdf")),
    "karkala2019_dys_shearcell": (
        "Karkala, Davis, Wassgren, Shi, Liu, Riemann, Yacobian, Ramachandran (2019) Calibration of discrete-element-"
        "method parameters for cohesive materials using dynamic-yield-strength and shear-cell experiments. "
        "Processes 7(5):278", "https://www.mdpi.com/2227-9717/7/5/278/htm", ("html", "article, .html-body, body")),
    "processes2021_9_1715": (
        "Processes 9(10):1715 (2021), MDPI (DEM calibration, cohesive powder)",
        "https://www.mdpi.com/2227-9717/9/10/1715/htm", ("html", "article, .html-body, body")),
    "scirep2024_feeder_dem": (
        "Scientific Reports (2024) doi:10.1038/s41598-024-72288-0 (DEM of a powder feeder, Ghent University)",
        "https://www.nature.com/articles/s41598-024-72288-0", ("html", "article, main, body")),
    "cheng2024_grainlearning_joss": (
        "Cheng, Orozco, Lubbe, Jansen, Hartmann, Thoeni (2024) GrainLearning: a Bayesian uncertainty "
        "quantification toolbox for discrete and continuum numerical models of granular materials. JOSS 9(97):6338",
        "https://joss.theoj.org/papers/10.21105/joss.06338", ("pdf", "a[href$='.pdf'], a:has-text('Download paper')")),
    "pourandi2025_wet_drum_calibration": (
        "Pourandi et al. (2025) Calibration of a DEM contact model for wet industrial granular materials. "
        "arXiv:2512.08685 (Powder Technology 476:122404)", "https://arxiv.org/abs/2512.08685",
        ("pdf", "a.download-pdf")),
    "haeri2018_cohesion_powder_bed": (
        "Haeri, Wang, Ghita, Sun (2018) On the impact of powder cohesion on the bulk properties of a powder bed in "
        "additive manufacturing (Strathprints accepted manuscript)", "https://strathprints.strath.ac.uk/64501/",
        ("pdf", "a[href$='.pdf']")),
    "weissbach2023_roller_spreading": (
        "Weissbach, Praegla, Wall, Hart, Meier (2023) Exploration of improved, roller-based spreading strategies "
        "for cohesive powders in additive manufacturing via coupled DEM-FEM simulations. arXiv:2306.06013",
        "https://arxiv.org/abs/2306.06013", ("pdf", "a.download-pdf")),
    "lambert2014_capillary_models": (
        "Comparison of different capillary bridge models for application in the discrete element method. "
        "arXiv:1403.7926", "https://arxiv.org/abs/1403.7926", ("pdf", "a.download-pdf")),
    "mercurydpm2024_capillary": (
        "Discrete element simulations of particles interacting via capillary forces using MercuryDPM. "
        "arXiv:2411.02042", "https://arxiv.org/abs/2411.02042", ("pdf", "a.download-pdf")),
    "epjconf2017_caking_dem": (
        "EPJ Web of Conferences 140, 13003 (2017): DEM of caking by capillary condensation under humidity cycles",
        "https://www.epj-conferences.org/articles/epjconf/abs/2017/09/epjconf161905/epjconf161905.html",
        ("pdf", "a[href$='.pdf']")),
    "nasa2013_tribocharging": (
        "NASA NTRS 20130010420 (tribocharging / electrostatics of granular materials)",
        "https://ntrs.nasa.gov/citations/20130010420", ("pdf", "a[href*='downloads'], a:has-text('Download')")),
    "staron2014_silo_mui": (
        "Staron, Lagree, Popinet (2014) Continuum simulation of the discharge of the granular silo: a validation "
        "test for the mu(I) visco-plastic flow law. Eur. Phys. J. E 37:5. arXiv:1306.6279",
        "https://arxiv.org/abs/1306.6279", ("pdf", "a.download-pdf")),
    "dunatunga2015_mpm_granular": (
        "Dunatunga, Kamrin (2015) Continuum modelling and simulation of granular flows through their many phases. "
        "J. Fluid Mech. 779:483. arXiv:1411.5447", "https://arxiv.org/abs/1411.5447", ("pdf", "a.download-pdf")),
    "choi2024_inverse_gns": (
        "Choi, Kumar (2024) Inverse analysis of granular flows using differentiable graph neural network simulator. "
        "arXiv:2401.13695", "https://arxiv.org/abs/2401.13695", ("pdf", "a.download-pdf")),
}


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def human_move(page, x: float, y: float) -> None:
    page.mouse.move(x + random.uniform(-2, 2), y + random.uniform(-2, 2), steps=random.randint(14, 26))


def human_click(page, locator, timeout: float = 20000) -> None:
    locator.scroll_into_view_if_needed(timeout=timeout)
    box = locator.bounding_box(timeout=timeout)
    if box is None:
        raise RuntimeError("element has no box")
    x = box["x"] + box["width"] * random.uniform(0.35, 0.65)
    y = box["y"] + box["height"] * random.uniform(0.35, 0.65)
    human_move(page, x, y)
    time.sleep(random.uniform(0.3, 0.8))
    page.mouse.click(x, y)


def open_browser(pw):
    browser = pw.chromium.launch(channel="chrome", headless=False, proxy={"server": PROXY},
                                 args=["--window-size=1366,900", "--disable-blink-features=AutomationControlled"])
    ctx = browser.new_context(viewport={"width": 1366, "height": 860}, accept_downloads=True, locale="en-US",
                              timezone_id="America/Denver")
    page = ctx.new_page()
    cdp = ctx.new_cdp_session(page)
    cdp.send("Network.enable")
    cdp.send("Network.emulateNetworkConditions", {"offline": False, "latency": 40,
                                                   "downloadThroughput": THROTTLE_BPS, "uploadThroughput": 100_000})
    return browser, ctx, page


def pdf_text(data: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    return "\n\n".join(f"[page {i + 1}]\n" + (p.extract_text() or "") for i, p in enumerate(reader.pages))


def fetch_one(page, ctx, key: str, landing: str, how: tuple) -> dict:
    mode, sel = how
    resp = page.goto(landing, wait_until="domcontentloaded", timeout=90000)
    time.sleep(random.uniform(1.5, 3.0))
    human_move(page, random.uniform(300, 900), random.uniform(200, 600))
    page.mouse.wheel(0, random.randint(200, 500))
    time.sleep(random.uniform(0.8, 1.6))
    status = resp.status if resp else None
    if mode == "html":
        text = ""
        for s in sel.split(","):
            loc = page.locator(s.strip()).first
            if loc.count():
                text = loc.inner_text(timeout=30000)
                if len(text) > 5000:
                    break
        raw = text.encode()
        return dict(kind="html", status=status, url=page.url, bytes=len(raw), sha256=sha256(raw), text=text)
    # pdf: move the pointer onto the PDF link and click it; capture the PDF bytes from the network
    link = page.locator(sel).first
    href = link.get_attribute("href", timeout=20000)
    pdf_url = page.urljoin(href) if hasattr(page, "urljoin") else None
    if not pdf_url:
        from urllib.parse import urljoin
        pdf_url = urljoin(page.url, href)
    captured: dict = {}

    def on_response(r):
        ct = (r.headers.get("content-type") or "").lower()
        if "pdf" in ct and "data" not in captured:
            try:
                captured["data"] = r.body()
                captured["url"] = r.url
            except Exception as exc:  # noqa: BLE001
                captured["err"] = repr(exc)

    page.on("response", on_response)
    try:
        with ctx.expect_page(timeout=8000) as newp:
            human_click(page, link)
        tab = newp.value
        tab.wait_for_load_state("domcontentloaded", timeout=90000)
    except Exception:  # noqa: BLE001 - link opened in the same tab, or as a download
        tab = None
    t0 = time.time()
    while "data" not in captured and time.time() - t0 < 12:
        time.sleep(0.5)
    page.remove_listener("response", on_response)
    if "data" not in captured:
        # same browser context and proxy; small files only
        r = ctx.request.get(pdf_url, timeout=90000)
        if r.ok and len(r.body()) < 15_000_000:
            captured["data"] = r.body()
            captured["url"] = pdf_url
            captured["via"] = "context request after click"
    if tab is not None:
        tab.close()
    data = captured.get("data", b"")
    if not data.startswith(b"%PDF"):
        raise RuntimeError(f"no PDF captured (status {status}, {captured.get('err', '')})")
    return dict(kind="pdf", status=status, url=captured["url"], bytes=len(data), sha256=sha256(data),
                text=pdf_text(data), pdf=data, via=captured.get("via", "page response after click"))


def main(keys: list[str]) -> None:
    from playwright.sync_api import sync_playwright

    FILES.mkdir(exist_ok=True)
    manifest = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {}
    with sync_playwright() as pw:
        browser, ctx, page = open_browser(pw)
        for key, (cite, landing, how) in PAPERS.items():
            if keys and key not in keys:
                continue
            t0 = time.time()
            try:
                res = fetch_one(page, ctx, key, landing, how)
                (FILES / f"{key}.txt").write_text(res["text"])
                if res.get("pdf"):
                    (FILES / f"{key}.pdf").write_bytes(res["pdf"])
                manifest[key] = dict(citation=cite, landing=landing, url=res["url"], kind=res["kind"],
                                     http_status=res["status"], bytes=res["bytes"], sha256=res["sha256"],
                                     text_chars=len(res["text"]), via=res.get("via", ""),
                                     route="headed Chrome (Playwright, Xvfb) through the doser Pi as SOCKS5, 400 kB/s",
                                     retrieved_utc=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                                     seconds=round(time.time() - t0, 1), ok=True)
                print(f"{key}: ok {res['kind']} {res['bytes']} B, {len(res['text'])} chars, "
                      f"{time.time() - t0:.0f} s", flush=True)
            except Exception as exc:  # noqa: BLE001
                manifest[key] = dict(citation=cite, landing=landing, ok=False, error=f"{type(exc).__name__}: {exc}"[:300],
                                     retrieved_utc=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
                print(f"{key}: FAILED {type(exc).__name__}: {str(exc)[:160]}", flush=True)
            MANIFEST.write_text(json.dumps(manifest, indent=1) + "\n")
            time.sleep(random.uniform(1.5, 4.0))
        browser.close()


if __name__ == "__main__":
    main(sys.argv[1:])
