#!/usr/bin/env python3
"""Citation network of El Kassem et al. (2021), KONA Powder and Particle Journal 38:235-250.

Pulls the focal paper's references and citing works from four open indexes (Crossref, OpenAlex, Semantic Scholar
with citation contexts, OpenCitations), merges them by DOI, adds the same group's other auger-dosing and DEM papers
with their own citing works, and counts which references the citing papers share (co-citation).

Usage:  python build_network.py [cache_dir]     (default cache: /tmp/kona/api; responses are cached as JSON)
Writes: network.json and citing_works.md next to this script.
No credentials are used. Requests carry a generic User-Agent and are spaced out.
"""
from __future__ import annotations

import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
CACHE = Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/kona/api")
CACHE.mkdir(parents=True, exist_ok=True)
UA = {"User-Agent": "powder-doser-citation-map/0.1"}
FOCAL_DOI = "10.14356/kona.2021010"
# The same group's auger-dosing and DEM papers (Robert Bosch GmbH / RWTH Aachen, Institute of General Mechanics).
GROUP_DOIS = {
    "10.1002/pamm.201800261": "PAMM 2018: auger dosing of pharmaceutical powders, experiment and DEM",
    "10.1016/j.jddst.2020.101950": "JDDST 2020: multivariate statistics of material attributes and process parameters in auger dosing",
    "10.1007/s40571-020-00315-8": "CPM 2021: multivariate regression study of DEM inputs, free-flowing and cohesive lactose",
    FOCAL_DOI: "KONA 2021: semi-automated DEM calibration from auger-dosing bulk responses (focal)",
}


def get(url: str, name: str, tries: int = 6) -> object:
    path = CACHE / name
    if path.exists():
        return json.loads(path.read_text())
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=60) as r:
                data = json.loads(r.read().decode("utf-8"))
            path.write_text(json.dumps(data))
            time.sleep(1.1)
            return data
        except Exception as exc:  # noqa: BLE001 - 429s from the unauthenticated Semantic Scholar pool
            print(f"  {name}: {type(exc).__name__} {getattr(exc, 'code', '')}; retry {attempt + 1}", flush=True)
            time.sleep(5 * (attempt + 1))
    return None


def norm_doi(d: str | None) -> str | None:
    if not d:
        return None
    d = d.lower().strip()
    for p in ("https://doi.org/", "http://doi.org/", "doi:"):
        if d.startswith(p):
            d = d[len(p):]
    return d


OA_FIELDS = ("id,doi,title,publication_year,type,primary_location,open_access,cited_by_count,authorships,"
             "referenced_works,best_oa_location")


def oa_work_summary(w: dict) -> dict:
    loc = w.get("primary_location") or {}
    src = (loc.get("source") or {})
    best = w.get("best_oa_location") or {}
    return {
        "openalex": w.get("id", "").rsplit("/", 1)[-1],
        "doi": norm_doi(w.get("doi")),
        "title": w.get("title"),
        "year": w.get("publication_year"),
        "type": w.get("type"),
        "venue": src.get("display_name"),
        "authors": [a.get("author", {}).get("display_name") for a in (w.get("authorships") or [])],
        "institutions": sorted({i.get("display_name") for a in (w.get("authorships") or [])
                                for i in (a.get("institutions") or []) if i.get("display_name")}),
        "countries": sorted({c for a in (w.get("authorships") or []) for c in (a.get("countries") or [])}),
        "cited_by_count": w.get("cited_by_count"),
        "is_oa": (w.get("open_access") or {}).get("is_oa"),
        "oa_status": (w.get("open_access") or {}).get("oa_status"),
        "license": best.get("license") or loc.get("license"),
        "oa_url": (w.get("open_access") or {}).get("oa_url"),
        "referenced_works": [r.rsplit("/", 1)[-1] for r in (w.get("referenced_works") or [])],
    }


def oa_citing(openalex_id: str, tag: str) -> list[dict]:
    url = (f"https://api.openalex.org/works?filter=cites:{openalex_id}&per-page=200&select={OA_FIELDS}")
    d = get(url, f"oa_citing_{tag}.json") or {}
    return [oa_work_summary(w) for w in d.get("results", [])]


def oa_by_ids(ids: list[str], tag: str) -> list[dict]:
    out = []
    for i in range(0, len(ids), 50):
        chunk = ids[i:i + 50]
        url = (f"https://api.openalex.org/works?filter=openalex:{'|'.join(chunk)}&per-page=100&select={OA_FIELDS}")
        d = get(url, f"oa_ids_{tag}_{i}.json") or {}
        out += [oa_work_summary(w) for w in d.get("results", [])]
    return out


def oa_by_doi(doi: str) -> dict | None:
    d = get(f"https://api.openalex.org/works/doi:{doi}?select={OA_FIELDS}", f"oa_doi_{doi.replace('/', '_')}.json")
    return oa_work_summary(d) if d else None


def main() -> None:
    focal = oa_by_doi(FOCAL_DOI)
    cr = get(f"https://api.crossref.org/works/{FOCAL_DOI}", "crossref.json")["message"]
    s2c = get("https://api.semanticscholar.org/graph/v1/paper/DOI:" + FOCAL_DOI +
              "/citations?fields=title,year,venue,externalIds,contexts,intents,isInfluential,openAccessPdf,authors"
              "&limit=100", "s2_citations.json") or {"data": []}
    s2r = get("https://api.semanticscholar.org/graph/v1/paper/DOI:" + FOCAL_DOI +
              "/references?fields=title,year,venue,externalIds,contexts,intents,isInfluential&limit=100",
              "s2_references.json") or {"data": []}
    occ = get("https://api.opencitations.net/index/v2/citations/doi:" + FOCAL_DOI, "oc_citations.json") or []

    # ---- forward citations, merged by DOI (title as a fallback key)
    citing: dict[str, dict] = {}

    def key_of(doi, title):
        return norm_doi(doi) or ("title:" + (title or "").lower().strip()[:80])

    for w in oa_citing(focal["openalex"], "focal"):
        k = key_of(w["doi"], w["title"])
        citing.setdefault(k, {**w, "sources": []})["sources"].append("OpenAlex")
    for c in s2c.get("data", []):
        p = c["citingPaper"]
        doi = norm_doi((p.get("externalIds") or {}).get("DOI"))
        k = key_of(doi, p.get("title"))
        ent = citing.setdefault(k, {"doi": doi, "title": p.get("title"), "year": p.get("year"),
                                    "venue": p.get("venue"), "sources": []})
        ent["sources"].append("SemanticScholar")
        ent["s2_contexts"] = c.get("contexts") or []
        ent["s2_intents"] = c.get("intents") or []
        ent["s2_influential"] = c.get("isInfluential")
    for c in occ:
        doi = next((norm_doi(t[4:]) for t in c["citing"].split() if t.startswith("doi:")), None)
        k = key_of(doi, None)
        ent = citing.setdefault(k, {"doi": doi, "title": None, "sources": []})
        ent["sources"].append("OpenCitations")
        ent["oc_creation"] = c.get("creation")
    # Fill metadata for works that only one index knows about
    for k, ent in citing.items():
        if ent.get("openalex") is None and ent.get("doi"):
            w = oa_by_doi(ent["doi"])
            if w:
                srcs = ent["sources"]
                ent.update({kk: vv for kk, vv in w.items() if vv is not None and kk not in ent or ent.get(kk) is None})
                ent["sources"] = srcs

    # ---- backward: Crossref reference list (with DOIs where deposited), plus OpenAlex metadata
    refs = []
    for r in cr.get("reference", []):
        refs.append({"key": r.get("key"), "doi": norm_doi(r.get("DOI")),
                     "unstructured": r.get("unstructured"), "author": r.get("author"),
                     "year": r.get("year"), "title": r.get("article-title"), "journal": r.get("journal-title")})
    ref_meta = {w["openalex"]: w for w in oa_by_ids(focal["referenced_works"], "focalrefs")}
    by_doi = {w["doi"]: w for w in ref_meta.values() if w["doi"]}
    for r in refs:
        w = by_doi.get(r["doi"]) if r["doi"] else None
        if w:
            r.update({"openalex": w["openalex"], "title": r["title"] or w["title"], "year": r["year"] or w["year"],
                      "venue": w["venue"], "cited_by_count": w["cited_by_count"]})

    # ---- co-citation: which of the focal paper's references do the citing papers also cite?
    focal_refs = set(focal["referenced_works"])
    cocite = {}
    for ent in citing.values():
        for r in ent.get("referenced_works", []):
            if r in focal_refs:
                cocite[r] = cocite.get(r, 0) + 1
    # Links between citing papers (one citing paper citing another)
    ids = {ent.get("openalex"): k for k, ent in citing.items() if ent.get("openalex")}
    intra = []
    for k, ent in citing.items():
        for r in ent.get("referenced_works", []):
            if r in ids:
                intra.append([k, ids[r]])

    # ---- the group's cluster
    group = {}
    for doi, label in GROUP_DOIS.items():
        w = oa_by_doi(doi)
        if not w:
            continue
        cw = oa_citing(w["openalex"], doi.replace("/", "_")) if doi != FOCAL_DOI else []
        group[doi] = {"label": label, **{k: w[k] for k in ("openalex", "title", "year", "venue", "cited_by_count")},
                      "citing": [{k: c[k] for k in ("openalex", "doi", "title", "year", "venue")} for c in cw],
                      "cites_focal": FOCAL_DOI in [norm_doi(None)] or focal["openalex"] in w["referenced_works"]}

    # Other works by the first author (OpenAlex author record of the focal paper's first author)
    fa = None
    fd = get(f"https://api.openalex.org/works/doi:{FOCAL_DOI}", "oa_focal_full.json")
    for a in fd.get("authorships", []):
        if a.get("author_position") == "first":
            fa = a["author"]["id"].rsplit("/", 1)[-1]
    first_author_works = []
    if fa:
        d = get(f"https://api.openalex.org/works?filter=author.id:{fa}&per-page=100&select={OA_FIELDS}",
                f"oa_author_{fa}.json") or {}
        first_author_works = [{k: w[k] for k in ("openalex", "doi", "title", "year", "venue", "cited_by_count", "type")}
                              for w in map(oa_work_summary, d.get("results", []))]

    net = {
        "focal": {**{k: focal[k] for k in ("openalex", "doi", "title", "year", "venue", "authors", "institutions",
                                            "cited_by_count", "license", "oa_url")},
                  "crossref_reference_count": cr.get("reference-count"),
                  "crossref_cited_by_count": cr.get("is-referenced-by-count"),
                  "semantic_scholar_reference_count": len(s2r.get("data", []))},
        "retrieved_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "citing": sorted(citing.values(), key=lambda e: (e.get("year") or 0, e.get("title") or "")),
        "citing_links": intra,
        "references": refs,
        "cocitation_counts": {ref_meta[r]["title"] if r in ref_meta else r: n
                              for r, n in sorted(cocite.items(), key=lambda kv: -kv[1])},
        "group_papers": group,
        "first_author_openalex": fa,
        "first_author_works": first_author_works,
        "s2_reference_contexts": [{"title": (x.get("citedPaper") or {}).get("title"),
                                   "contexts": x.get("contexts") or [], "intents": x.get("intents") or []}
                                  for x in s2r.get("data", [])],
    }
    (HERE / "network.json").write_text(json.dumps(net, indent=1, ensure_ascii=False) + "\n")

    lines = ["| year | citing work | venue | indexes | OA | cited by |", "|---|---|---|---|---|---|"]
    for e in net["citing"]:
        doi = e.get("doi")
        t = (e.get("title") or "?").replace("|", "/")
        link = f"[{t}](https://doi.org/{doi})" if doi else t
        lines.append(f"| {e.get('year') or ''} | {link} | {e.get('venue') or ''} | "
                     f"{', '.join(sorted(set(e['sources'])))} | {e.get('oa_status') or ''} | "
                     f"{e.get('cited_by_count') if e.get('cited_by_count') is not None else ''} |")
    (HERE / "citing_works.md").write_text(
        f"# Works citing El Kassem et al. (2021), KONA 38:235-250\n\nRetrieved {net['retrieved_utc']} from "
        "OpenAlex, Semantic Scholar and OpenCitations by `build_network.py`.\n\n" + "\n".join(lines) + "\n")
    print(f"citing works: {len(net['citing'])}; references: {len(refs)} "
          f"({sum(1 for r in refs if r['doi'])} with DOI); links among citing works: {len(intra)}")
    print("co-cited references (top):")
    for t, n in list(net["cocitation_counts"].items())[:12]:
        print(f"  {n} x {str(t)[:100]}")
    print("first author works:", len(first_author_works))


if __name__ == "__main__":
    main()
