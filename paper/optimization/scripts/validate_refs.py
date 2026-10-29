#!/usr/bin/env python3
"""Validate every entry of refs.bib against Crossref / arXiv.

For each BibTeX entry:
  * DOI present   -> fetch Crossref metadata, compare title (fuzzy),
                     year and first-author family name.
  * arXiv eprint  -> fetch arXiv API metadata, compare title.
  * neither       -> flag for manual verification (standards, web pages,
                     theses, software without a DOI).

Writes ``references_validation.md`` next to ``refs.bib`` with one row per
entry and a summary of the entries that need a human to check them.

Usage:  python scripts/validate_refs.py [path/to/refs.bib]
"""
from __future__ import annotations

import difflib
import re
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import bibtexparser
import requests

HERE = Path(__file__).resolve().parent.parent
UA = {"User-Agent": "powder-doser-refcheck/1.0 (mailto:sterling.baird@byu.edu)"}
TITLE_OK = 0.90  # fuzzy-ratio threshold for a title match


def norm(s: str) -> str:
    s = re.sub(r"\\[a-zA-Z]+\s*", " ", s or "")  # strip LaTeX commands
    s = re.sub(r"[{}$\\^_~'`\"]", "", s)
    s = re.sub(r"[^a-z0-9 ]", " ", s.lower())
    return re.sub(r"\s+", " ", s).strip()


def ratio(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, norm(a), norm(b)).ratio()


def first_family(author_field: str) -> str:
    first = (author_field or "").split(" and ")[0].strip()
    if "," in first:
        return norm(first.split(",")[0]).split(" ")[-1] if norm(first.split(",")[0]) else ""
    parts = norm(first).split(" ")
    return parts[-1] if parts else ""


def crossref(doi: str) -> dict | None:
    for attempt in range(3):
        try:
            r = requests.get(f"https://api.crossref.org/works/{doi}", headers=UA, timeout=30)
        except requests.RequestException:
            time.sleep(2 * (attempt + 1))
            continue
        if r.status_code == 200:
            return r.json()["message"]
        if r.status_code == 404:
            return None
        time.sleep(2 * (attempt + 1))
    return None


def doi_resolves(doi: str) -> str:
    """Return the HTTP status of the doi.org handle lookup (not the publisher page,
    which often blocks bots); 'ok' when the handle exists."""
    try:
        r = requests.get(f"https://doi.org/api/handles/{doi}", headers=UA, timeout=30)
        if r.status_code == 200 and r.json().get("responseCode") == 1:
            return "ok"
        return f"handle {r.status_code}"
    except requests.RequestException as exc:  # pragma: no cover - network
        return f"error {type(exc).__name__}"


def arxiv(eid: str) -> dict | None:
    try:
        r = requests.get("http://export.arxiv.org/api/query", params={"id_list": eid}, headers=UA, timeout=30)
    except requests.RequestException:
        return None
    if r.status_code != 200:
        return None
    ns = {"a": "http://www.w3.org/2005/Atom"}
    root = ET.fromstring(r.text)
    entry = root.find("a:entry", ns)
    if entry is None or entry.find("a:title", ns) is None:
        return None
    title = " ".join(entry.find("a:title", ns).text.split())
    authors = [a.find("a:name", ns).text for a in entry.findall("a:author", ns)]
    published = entry.find("a:published", ns).text[:4]
    return {"title": title, "authors": authors, "year": published}


def main(bib_path: Path) -> int:
    with open(bib_path, encoding="utf-8") as fh:
        db = bibtexparser.load(fh)
    rows, manual = [], []
    for e in sorted(db.entries, key=lambda x: x["ID"].lower()):
        key, title = e["ID"], e.get("title", "")
        year, fam = e.get("year", ""), first_family(e.get("author", ""))
        doi = e.get("doi", "").strip()
        eprint = e.get("eprint", "").strip() if e.get("archiveprefix", e.get("eprinttype", "")).lower() == "arxiv" else ""
        status, note = "", ""
        if doi:
            meta = crossref(doi)
            handle = doi_resolves(doi)
            if meta is None:
                status = "MANUAL"
                note = f"DOI not in Crossref (doi.org handle: {handle})"
            else:
                ct = (meta.get("title") or [""])[0]
                r = ratio(title, ct)
                cy = str((meta.get("issued", {}).get("date-parts") or [[None]])[0][0] or "")
                cfam = norm((meta.get("author") or [{}])[0].get("family", "")) if meta.get("author") else ""
                problems = []
                if r < TITLE_OK:
                    problems.append(f"title ratio {r:.2f}; Crossref: '{ct}'")
                if year and cy and year != cy:
                    problems.append(f"year {year} vs Crossref {cy}")
                if fam and cfam and fam != cfam and fam not in cfam and cfam not in fam:
                    problems.append(f"first author '{fam}' vs Crossref '{cfam}'")
                status = "OK" if not problems else "CHECK"
                note = "; ".join(problems) if problems else f"title ratio {r:.2f}, handle {handle}"
        elif eprint:
            meta = arxiv(eprint)
            if meta is None:
                status, note = "MANUAL", f"arXiv {eprint} not found"
            else:
                r = ratio(title, meta["title"])
                status = "OK" if r >= TITLE_OK else "CHECK"
                note = f"arXiv title ratio {r:.2f}" + ("" if r >= TITLE_OK else f"; arXiv: '{meta['title']}'")
        elif e.get("url", "").strip():
            url = e["url"].strip()
            try:
                r = requests.get(url, headers=UA, timeout=30)
                page = re.sub(r"\s+", " ", r.text)
                found = norm(title) and norm(title) in norm(page)
                status = "OK" if (r.status_code == 200 and found) else "MANUAL"
                note = f"URL HTTP {r.status_code}; title {'found' if found else 'not found'} on page"
            except requests.RequestException as exc:  # pragma: no cover - network
                status, note = "MANUAL", f"URL error {type(exc).__name__}"
        else:
            status = "MANUAL"
            note = "no DOI, arXiv id or URL (standard, thesis or unpublished); verify by hand"
        rows.append((key, status, doi or (f"arXiv:{eprint}" if eprint else ""), note))
        if status != "OK":
            manual.append((key, status, note))
        time.sleep(0.3)

    n_ok = sum(1 for r in rows if r[1] == "OK")
    out = [
        "# Reference validation",
        "",
        f"Generated by `scripts/validate_refs.py` on {time.strftime('%Y-%m-%d', time.gmtime())}. "
        f"{len(rows)} entries: **{n_ok} OK** (DOI found in Crossref or arXiv id found, title match "
        f"ratio >= {TITLE_OK}, year and first author consistent), "
        f"**{sum(1 for r in rows if r[1] == 'CHECK')} CHECK** (metadata disagree), "
        f"**{sum(1 for r in rows if r[1] == 'MANUAL')} MANUAL** (no machine-checkable identifier).",
        "",
        "## Needs a human",
        "",
        "| key | status | note |",
        "|---|---|---|",
    ]
    out += [f"| `{k}` | {s} | {n.replace('|', '/')} |" for k, s, n in manual] or ["| (none) | | |"]
    out += ["", "## All entries", "", "| key | status | identifier | note |", "|---|---|---|---|"]
    out += [f"| `{k}` | {s} | {i} | {n.replace('|', '/')} |" for k, s, i, n in rows]
    (bib_path.parent / "references_validation.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"{len(rows)} entries: {n_ok} OK, {len(manual)} need attention")
    return 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "refs.bib"))
