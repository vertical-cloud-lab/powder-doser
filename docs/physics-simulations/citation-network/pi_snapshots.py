#!/usr/bin/env python3
"""Open the KONA paper and the open-access papers around it in a headed Chrome whose traffic leaves through the doser Pi.

Reuses ../fulltext/fetch_fulltexts.py: Playwright drives the runner's Chrome under Xvfb, the Pi is a SOCKS5 proxy
(../fulltext/pi_socks.sh opens it on 127.0.0.1:1080), the pointer moves to each PDF link and clicks it, and the
browser is throttled to 400 kB/s. Nothing is installed or written on the Pi.

For each paper: a screenshot of the landing page, then the PDF (captured from the navigation the click starts).
On the KONA landing page it also scrolls to J-STAGE's "Cited by" list and screenshots it.
PDFs and screenshots go to OUT (default /tmp/kona); only figure crops of CC BY papers are committed (see
extract_figures.py). manifest.json records URL, bytes, sha256 and time of every PDF read.

Usage:  ../fulltext/pi_socks.sh && xvfb-run -a python pi_snapshots.py [key ...]
"""
from __future__ import annotations

import json
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "fulltext"))
from fetch_fulltexts import fetch_one, human_click, human_move, open_browser, pdf_text, sha256  # noqa: E402

OUT = Path("/tmp/kona")
MANIFEST = HERE / "manifest.json"

# key: (citation, licence, landing page, PDF-link selector)
PAPERS = {
    "elkassem2021_kona": (
        "El Kassem, Salloum, Brinz, Heider, Markert (2021) A semi-automated DEM parameter calibration technique of "
        "powders based on different bulk responses extracted from auger dosing experiments. KONA 38:235-250. "
        "doi:10.14356/kona.2021010", "CC BY 2.0 (J-STAGE)",
        "https://www.jstage.jst.go.jp/article/kona/38/0/38_2021010/_article",
        "a[href*='38_2021010/_pdf']"),
    "elkassem2021_cpm": (
        "El-Kassem, Salloum, Brinz, Heider, Markert (2021) A multivariate regression parametric study on DEM input "
        "parameters of free-flowing and cohesive powders with experimental data-based validation. Comput. Part. "
        "Mech. 8:87-111. doi:10.1007/s40571-020-00315-8", "CC BY 4.0 (Springer open choice)",
        "https://link.springer.com/article/10.1007/s40571-020-00315-8",
        "a[data-article-pdf='true'], a.c-pdf-download__link, a[href*='/content/pdf/']"),
    "matertrans2021_vibration_feeder": (
        "Genetic algorithm based automatic input parameter calibration method for the discrete element modeling of "
        "vibration feeders. Materials Transactions 62(4) (2021). doi:10.2320/matertrans.M-M2021806",
        "free to read; no open licence (not reused)",
        "https://www.jstage.jst.go.jp/article/matertrans/62/4/62_M-M2021806/_article",
        "a[href*='62_M-M2021806/_pdf']"),
    "polymers2025_calibration": (
        "Development of a non-spherical polymeric particles calibration procedure for numerical simulations based on "
        "the discrete element method. Polymers 17(20):2748 (2025). doi:10.3390/polym17202748", "CC BY 4.0 (MDPI)",
        "https://www.mdpi.com/2073-4360/17/20/2748",
        "a.UD_ArticlePDF, a[href$='2748/pdf'], a[href*='2748/pdf?version']"),
    # Named by Edison q13 (23 Nov 2026) as two more calibrations against a screw's own output; read to check that.
    "imole2016_arxiv": (
        "Imole, Krijgsman, Weinhart, Magnanimo, Chavez Montes, Ramaioli, Luding (2016) Experiments and discrete "
        "element simulation of the dosing of cohesive powders in a simplified geometry. Powder Technology 287:108. "
        "arXiv:1410.2886", "arXiv non-exclusive licence (not reused)",
        "https://arxiv.org/abs/1410.2886", "a.download-pdf"),
    "shen2021_jeng": (
        "Shen, Li, Xu (2021) Calibration of discrete element simulation parameters for powder screw conveying. "
        "Journal of Engineering 2021:6671511. doi:10.1155/2021/6671511", "CC BY 4.0 (Hindawi/Wiley)",
        "https://onlinelibrary.wiley.com/doi/10.1155/2021/6671511",
        "a.pdf-download, a[href*='/doi/pdf/10.1155'], a[href*='/doi/epdf/10.1155']"),
    "ajst2025_vertical_screw": (
        "Study on the influence characteristics of vertical fine screw transport. Academic Journal of Science and "
        "Technology (2025). doi:10.54097/wvbec931", "CC BY 4.0 (per OpenAlex)",
        "https://doi.org/10.54097/wvbec931",
        "a.obj_galley_link.pdf, a.obj_galley_link, a[href*='/download/']"),
}


def shot(page, path: Path, full: bool = False) -> None:
    page.screenshot(path=str(path), full_page=full)


def dismiss_cookies(page) -> None:
    """Decline optional cookies when a consent banner covers the page (Springer, MDPI)."""
    for label in ("Reject optional cookies", "Reject all", "Reject All", "Only necessary", "Decline"):
        loc = page.locator(f"button:has-text('{label}')").first
        try:
            if loc.count() and loc.is_visible():
                human_click(page, loc)
                time.sleep(1.0)
                return
        except Exception:  # noqa: BLE001
            continue


def fetch_download(page, sel: str) -> dict:
    """Fallback for PDF links served as attachments: click the link and take the browser download."""
    link = page.locator(sel).first
    with page.expect_download(timeout=120000) as dl:
        human_click(page, link)
    path = dl.value.path()
    data = Path(path).read_bytes()
    if not data.startswith(b"%PDF"):
        raise RuntimeError("download is not a PDF")
    return dict(url=dl.value.url, bytes=len(data), sha256=sha256(data), text=pdf_text(data), pdf=data,
                via="browser download after the click")


def main(keys: list[str]) -> None:
    from playwright.sync_api import sync_playwright

    (OUT / "pdf").mkdir(parents=True, exist_ok=True)
    (OUT / "shots").mkdir(parents=True, exist_ok=True)
    manifest = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {}
    with sync_playwright() as pw:
        browser, ctx, page = open_browser(pw)
        for key, (cite, lic, landing, sel) in PAPERS.items():
            if keys and key not in keys:
                continue
            t0 = time.time()
            try:
                page.goto(landing, wait_until="domcontentloaded", timeout=120000)
                time.sleep(random.uniform(2.0, 3.5))
                human_move(page, random.uniform(300, 900), random.uniform(200, 600))
                shot(page, OUT / "shots" / f"{key}_landing.png")
                if key == "elkassem2021_kona":
                    # J-STAGE lists the works that cite the article (from its own and Crossref's cited-by data)
                    for label in ("Cited by", "Citing articles"):
                        loc = page.locator(f"text={label}").first
                        if loc.count():
                            try:
                                loc.scroll_into_view_if_needed(timeout=10000)
                                time.sleep(1.5)
                                shot(page, OUT / "shots" / f"{key}_citedby.png")
                            except Exception as exc:  # noqa: BLE001
                                print(f"  cited-by shot failed: {type(exc).__name__}", flush=True)
                            break
                    shot(page, OUT / "shots" / f"{key}_full.png", full=True)
                    page.mouse.wheel(0, -20000)
                    time.sleep(1.0)
                dismiss_cookies(page)
                try:
                    res = fetch_one(page, ctx, key, page.url, ("pdf", sel))
                except Exception as exc:  # noqa: BLE001 - e.g. Springer serves the PDF as an attachment
                    print(f"  {key}: navigation capture failed ({type(exc).__name__}); trying the download", flush=True)
                    page.goto(landing, wait_until="domcontentloaded", timeout=120000)
                    time.sleep(2.0)
                    dismiss_cookies(page)
                    res = fetch_download(page, sel)
                (OUT / "pdf" / f"{key}.pdf").write_bytes(res["pdf"])
                (OUT / "pdf" / f"{key}.txt").write_text(res["text"])
                manifest[key] = dict(citation=cite, licence=lic, landing=landing, url=res["url"],
                                     bytes=res["bytes"], sha256=res["sha256"], text_chars=len(res["text"]),
                                     via=res.get("via", ""),
                                     route="headed Chrome (Playwright, Xvfb) through the doser Pi as SOCKS5, 400 kB/s",
                                     retrieved_utc=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                                     seconds=round(time.time() - t0, 1), ok=True)
                print(f"{key}: ok {res['bytes']} B, {len(res['text'])} chars, {time.time() - t0:.0f} s", flush=True)
            except Exception as exc:  # noqa: BLE001
                manifest[key] = dict(citation=cite, licence=lic, landing=landing, ok=False,
                                     error=f"{type(exc).__name__}: {exc}"[:300],
                                     retrieved_utc=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
                print(f"{key}: FAILED {type(exc).__name__}: {str(exc)[:200]}", flush=True)
                try:
                    shot(page, OUT / "shots" / f"{key}_failed.png")
                except Exception:  # noqa: BLE001
                    pass
            MANIFEST.write_text(json.dumps(manifest, indent=1) + "\n")
            time.sleep(random.uniform(1.5, 3.5))
        browser.close()


if __name__ == "__main__":
    main(sys.argv[1:])
