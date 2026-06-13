#!/usr/bin/env python3
"""Run batches of Edison Scientific ANALYSIS tasks, one task per manuscript
figure, to obtain figure-level reviewer/editor feedback and consistency checks
for the base powder-doser Digital Discovery manuscript.

Per @sgbaird (PR #97): "run as many iterations as you can with Edison scientific
analysis, in batches, with a batch size the same as the number of figures
currently in the manuscript. For each query, upload the manuscript, the figure,
the caption, and any source files (code, images, etc.) used to generate the
figure. Also upload the static copy of the comments ... Also upload the full
naming tree of all files across all branches in the repository."

Each figure gets its own zipped input collection (per the ANALYSIS upload
convention) containing:
  - main.pdf (and si.pdf for the SI figure)            -- the manuscript
  - <figure>.pdf                                        -- the figure itself
  - caption_<fig>.md                                    -- the figure caption
  - make_figures.py                                     -- figure source code
  - assets/<png>...                                     -- the CAD renders used
  - pr97_comments.md                                    -- static PR comments
  - all_branches_file_tree.txt                          -- full cross-branch tree
  - README.md                                           -- what this bundle is

A "batch" dispatches one ANALYSIS task per figure (6 figures => 6 tasks). Each
batch uses a different analytical lens (see BATCHES). Task ids are recorded in
figure_review_task_ids.json so a later session can fetch results via
``client.get_task(task_id, verbose=True)``.

Usage:
  export EDISON_API_KEY=...   # or EDISON_PLATFORM_API_KEY
  python figure_review_batches.py [--batches 1 2 3] [--minutes 55]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import time
from pathlib import Path

from edison_client import EdisonClient, JobNames

HERE = Path(__file__).resolve().parent
PAPER = HERE.parent
REPO = PAPER.parent
FIGDIR = PAPER / "figures"
ASSETS = FIGDIR / "assets"
BUILD = Path("/tmp/edison_build")
COMMENTS = HERE / "inputs" / "pr97_comments.md"
TREE = HERE / "inputs" / "all_branches_file_tree.txt"

# figure -> (pdf, includes_si, asset pngs used by make_figures.py)
FIGURES = {
    "fig1_overview": {
        "pdf": "fig1_overview.pdf",
        "si": False,
        "assets": [
            "assembly_iso_final.png",
            "single_channel_module_powder_flow.png",
            "rotation_0_45_90.png",
        ],
        "label": "fgr:overview",
        "where": "main.tex, Figure 1 (platform overview)",
    },
    "fig2_genai": {
        "pdf": "fig2_genai.pdf",
        "si": False,
        "assets": [
            "tap_collar_v1_iso.png",
            "tap_collar_final_iso.png",
            "auger_assembly_iso.png",
            "single_channel_module_iso.png",
            "plate_iter1_hole_top.png",
            "plate_iter2_platforms_iso.png",
            "plate_iter3_gap_top.png",
            "plate_iter4_final_top.png",
        ],
        "label": "fgr:genai",
        "where": "main.tex, Figure 2 (generative-AI CAD outcomes)",
    },
    "fig3_dispense": {
        "pdf": "fig3_dispense.pdf",
        "si": False,
        "assets": [],  # fully synthetic plot, watermarked
        "label": "fgr:dispense",
        "where": "main.tex, Figure 3 (dispensing characterization, SYNTHETIC)",
    },
    "fig4_design": {
        "pdf": "fig4_design.pdf",
        "si": False,
        "assets": [
            "auger_geared_cross_section.png",
            "tap_collar_final_iso.png",
        ],
        "label": "fgr:design",
        "where": "main.tex, Figure 4 (design specifics)",
    },
    "fig5_future": {
        "pdf": "fig5_future.pdf",
        "si": False,
        "assets": ["inward_collection_cup_iso.png"],
        "label": "fgr:future",
        "where": "main.tex, Figure 5 (future work, multi-powder doser)",
    },
    "figS1_nozzles": {
        "pdf": "figS1_nozzles.pdf",
        "si": True,
        "assets": [
            "nozzle_type1_cross_section.png",
            "nozzle_type2_cross_section.png",
            "nozzle_type3_cross_section.png",
            "nozzle_type4_cross_section.png",
        ],
        "label": "fgr:nozzles",
        "where": "si.tex, Figure S1 (exit-nozzle variants)",
    },
}

COMMON = (
    "This collection concerns ONE figure of a manuscript drafted for Digital "
    "Discovery (RSC) as an open-hardware Full Paper on a 3D-printed auger powder "
    "doser designed with generative AI. The bundle contains: the full manuscript "
    "(main.pdf; si.pdf for the SI figure), the single figure PDF under review, "
    "its caption (caption_*.md), the figure-generation source (make_figures.py) "
    "and the CAD-render assets it consumes (assets/), a static snapshot of all "
    "human + bot review comments on the pull request (pr97_comments.md), and the "
    "full file-naming tree across all 45 repository branches "
    "(all_branches_file_tree.txt). Ground every claim in the supplied files; when "
    "you suspect a relevant file exists, name it from the branch tree. When "
    "attributing work, distinguish only HUMAN vs AI contributions (never name "
    "individuals), and note that no GUI CAD package (Fusion 360/SolidWorks) was "
    "ever used \u2014 only programmatic CAD (LLM coding agents writing parametric "
    "CAD code) and, late and exploratorily, Zoo Design Studio (chat-driven, with "
    "its Zookeeper agent)."
)

# Each batch is a distinct analytical lens applied per figure.
BATCHES = {
    "consistency": (
        "FOCUS: Internal consistency. Cross-check this figure, its caption, and "
        "its source assets against (a) the claims made about it in the "
        "manuscript body, and (b) the human reviewer comments in "
        "pr97_comments.md. List every inconsistency, contradiction, or unsupported "
        "claim you find (e.g. a caption asserting something the render does not "
        "show, a balance/sensor or hopper description conflicting with the "
        "HR-100A-no-hopper corrections, or AI-vs-human attributions that the "
        "comments contradict). For each, cite the exact passage/file and propose "
        "a corrected wording."
    ),
    "reviewer": (
        "FOCUS: Peer-review critique of this figure. As an expert reviewer for "
        "Digital Discovery (spanning self-driving labs, powder-dosing metrology, "
        "and generative CAD), assess whether this figure earns its place: is it "
        "necessary, legible, and sufficient? What data, scale bars, dimensions, "
        "units, error bars, or panels are missing? Is anything (e.g. synthetic "
        "data) over-claimed? Give numbered, actionable major and minor comments "
        "specific to this figure and caption."
    ),
    "provenance": (
        "FOCUS: Provenance and reproducibility. Using make_figures.py, the "
        "assets/ renders, and the cross-branch file tree, verify that the figure "
        "is reproducible from repository sources and that its caption claims are "
        "backed by real design files. Identify, BY NAME from the branch tree, the "
        "source CAD/code files that should be cited or archived to substantiate "
        "each panel, and flag any panel whose underlying source you cannot locate."
    ),
    "improvement": (
        "FOCUS: Concrete improvements. Propose a specific, prioritized redesign "
        "of this figure and its caption for a top-tier hardware paper: panel "
        "layout, what to add/remove, annotations, and a tightened caption draft. "
        "Keep recommendations implementable with the existing assets where "
        "possible, and note which would require new renders or bench data."
    ),
    "signposting": (
        "FOCUS: AI-vs-human signposting. Judge whether this figure and caption "
        "make unambiguous which contributions were HUMAN (design decisions, "
        "annotated/dimensioned drawings, review, printing/testing) versus AI "
        "(parametric modelling), consistent with pr97_comments.md. Rewrite the "
        "caption so the human/AI division of labour is explicit and accurate, "
        "without naming individuals."
    ),
    "narrative": (
        "FOCUS: Narrative role. Explain the job this figure does in the paper's "
        "argument and whether the surrounding text and other figures make that "
        "role coherent and non-redundant. Recommend whether to keep, merge, move "
        "to SI, or cut it, with justification grounded in the manuscript."
    ),
}


def _api_key() -> str:
    key = os.environ.get("EDISON_API_KEY") or os.environ.get(
        "EDISON_PLATFORM_API_KEY"
    )
    if not key:
        raise SystemExit("No EDISON_API_KEY / EDISON_PLATFORM_API_KEY set.")
    return key


def extract_caption(fig: str, meta: dict) -> str:
    src = (PAPER / ("si.tex" if meta["si"] else "main.tex")).read_text()
    # find the \caption{...} in the figure environment containing the label
    label = meta["label"]
    idx = src.find("\\label{" + label + "}")
    if idx == -1:
        idx = src.find(meta["pdf"].replace(".pdf", ""))
    cap_start = src.rfind("\\caption{", 0, idx if idx != -1 else len(src))
    if cap_start == -1:
        cap_start = src.find("\\caption{")
    # balance braces
    i = cap_start + len("\\caption{")
    depth = 1
    while i < len(src) and depth:
        if src[i] == "{":
            depth += 1
        elif src[i] == "}":
            depth -= 1
        i += 1
    return src[cap_start + len("\\caption{"): i - 1].strip()


def build_bundle(fig: str, meta: dict) -> Path:
    bdir = BUILD / "bundles" / fig
    if bdir.exists():
        shutil.rmtree(bdir)
    (bdir / "assets").mkdir(parents=True)
    shutil.copy2(PAPER / "main.pdf", bdir / "main.pdf")
    if meta["si"]:
        shutil.copy2(PAPER / "si.pdf", bdir / "si.pdf")
    shutil.copy2(FIGDIR / meta["pdf"], bdir / meta["pdf"])
    shutil.copy2(FIGDIR / "make_figures.py", bdir / "make_figures.py")
    for a in meta["assets"]:
        ap = ASSETS / a
        if ap.exists():
            shutil.copy2(ap, bdir / "assets" / a)
    shutil.copy2(COMMENTS, bdir / "pr97_comments.md")
    shutil.copy2(TREE, bdir / "all_branches_file_tree.txt")
    caption = extract_caption(fig, meta)
    (bdir / f"caption_{fig}.md").write_text(
        f"# Caption for {fig} ({meta['where']})\n\n{caption}\n"
    )
    asset_list = "\n".join(f"  - assets/{a}" for a in meta["assets"]) or "  (none; synthetic plot)"
    (bdir / "README.md").write_text(
        f"# Figure-review bundle: {fig}\n\n"
        f"Location in manuscript: {meta['where']}\n\n"
        f"Figure PDF: {meta['pdf']}\n"
        f"Caption: caption_{fig}.md\n"
        f"Source code: make_figures.py (function generating this figure)\n"
        f"CAD-render assets consumed:\n{asset_list}\n\n"
        f"Also included: main.pdf"
        f"{' + si.pdf' if meta['si'] else ''}, pr97_comments.md, "
        f"all_branches_file_tree.txt\n"
    )
    return bdir


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--batches", nargs="*", default=["consistency"],
                    choices=list(BATCHES))
    ap.add_argument("--minutes", type=float, default=55.0)
    ap.add_argument("--throttle", type=float, default=8.0,
                    help="seconds to wait between create_task calls (429 guard)")
    args = ap.parse_args()

    deadline = time.time() + args.minutes * 60
    client = EdisonClient(api_key=_api_key())

    # Upload each figure bundle once; reuse the data_entry across batches.
    ids_path = HERE / "figure_review_task_ids.json"
    record = json.loads(ids_path.read_text()) if ids_path.exists() else {}
    record.setdefault("uploads", {})
    record.setdefault("batches", {})

    uploads: dict[str, str] = dict(record["uploads"])
    for fig, meta in FIGURES.items():
        if fig in uploads:
            print(f"Reusing upload for {fig}: {uploads[fig]}", flush=True)
            continue
        bdir = build_bundle(fig, meta)
        print(f"Uploading bundle for {fig} ...", flush=True)
        stored = client.store_file_content(
            name=f"powder_doser_{fig}_bundle",
            file_path=str(bdir),
            as_collection=True,
        )
        uploads[fig] = f"data_entry:{stored.data_storage.id}"
        print(f"  -> {uploads[fig]}", flush=True)
    record["uploads"].update(uploads)
    ids_path.write_text(json.dumps(record, indent=2))

    for batch in args.batches:
        if time.time() > deadline:
            print("Time budget exhausted; stopping before batch", batch)
            break
        lens = BATCHES[batch]
        record["batches"].setdefault(batch, {})
        for fig, meta in FIGURES.items():
            if fig in record["batches"][batch]:
                continue  # resume: already dispatched
            if time.time() > deadline:
                print("Time budget exhausted mid-batch", batch)
                break
            query = (
                f"{COMMON}\n\nThe figure under review is {fig} "
                f"({meta['where']}).\n\n{lens}\n\n"
                "Be concrete and cite specific files, passages, panels, and "
                "branch-tree paths. End with a short prioritized action list for "
                "this figure."
            )
            task = {
                "name": JobNames.ANALYSIS,
                "query": query,
                "tags": [f"powder-doser-fig-review-{batch}", fig],
            }
            tid = str(client.create_task(task, files=[uploads[fig]]))
            record["batches"][batch][fig] = tid
            ids_path.write_text(json.dumps(record, indent=2))
            print(f"  dispatched {batch}/{fig} -> {tid}", flush=True)
            time.sleep(args.throttle)

    print(f"Recorded task ids in {ids_path}", flush=True)


if __name__ == "__main__":
    main()
