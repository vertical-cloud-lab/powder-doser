#!/usr/bin/env python3
"""Round-4 Edison ANALYSIS verification pass over the REVISED manuscript figures.

This continues the Edison feedback loop requested on PR #97: after implementing
the concrete, non-bench-data figure-consistency fixes that the first 36-task
per-figure review surfaced (Fig.1 no-hopper schematic + spur-gear callout +
controller-routed closed loop; reworded captions), re-submit the revised
figures to Edison and ask it to (a) confirm which previously-flagged
inconsistencies are now resolved and (b) surface any remaining concrete fixes
that do not depend on real bench data.

Each figure gets a fresh zipped input collection (the figures changed, so the
cached round-1 uploads cannot be reused) built by ``build_bundle`` from
``figure_review_batches.py``, plus the round-1 consolidated digest
(results/CONSOLIDATED.md) so Edison can check its own prior action items.

Task ids are recorded in ``figure_review_round4_task_ids.json``; fetch later
with ``fetch_figure_reviews.py`` (point ``--ids`` at the round-2 file) or
``client.get_task(task_id, verbose=True)``.

Usage:
  export EDISON_API_KEY=...            # or EDISON_PLATFORM_API_KEY
  python figure_review_round2.py [--figures fig1_overview ...] [--minutes 30]
"""
from __future__ import annotations

import argparse
import json
import shutil
import time
from pathlib import Path

from edison_client import EdisonClient, JobNames

import figure_review_batches as r1

HERE = r1.HERE
CONSOLIDATED = HERE / "results" / "CONSOLIDATED.md"

VERIFY_LENS = (
    "FOCUS: Verification of the revised figure. The first review round flagged "
    "concrete inconsistencies for this manuscript; the round-1 consolidated "
    "digest is included as CONSOLIDATED.md. For THIS figure, (1) state which of "
    "the previously-flagged issues are now resolved in the revised figure PDF / "
    "caption / make_figures.py, citing the exact evidence; (2) list any "
    "previously-flagged issue that is NOT yet resolved; and (3) surface any "
    "remaining concrete inconsistency or unsupported claim that can be fixed "
    "WITHOUT new bench measurements (e.g. caption-vs-render mismatches, "
    "hopper/load-cell/sensor wording, AI-vs-human attribution, undocumented "
    "callouts, diagram logic). Do NOT re-litigate that the dispensing data are "
    "synthetic placeholders \u2014 that is known and will be replaced by bench "
    "data. End with a short prioritized action list of only the implementable, "
    "non-bench-data fixes that remain."
)


def build_bundle_r2(fig: str, meta: dict) -> Path:
    bdir = r1.build_bundle(fig, meta)
    if CONSOLIDATED.exists():
        shutil.copy2(CONSOLIDATED, bdir / "round1_CONSOLIDATED.md")
    return bdir


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--figures", nargs="*", default=list(r1.FIGURES),
                    choices=list(r1.FIGURES))
    ap.add_argument("--minutes", type=float, default=30.0)
    ap.add_argument("--throttle", type=float, default=10.0,
                    help="seconds between create_task calls (429 guard)")
    args = ap.parse_args()

    deadline = time.time() + args.minutes * 60
    client = EdisonClient(api_key=r1._api_key())

    ids_path = HERE / "figure_review_round4_task_ids.json"
    record = json.loads(ids_path.read_text()) if ids_path.exists() else {}
    record.setdefault("uploads", {})
    record.setdefault("tasks", {})

    for fig in args.figures:
        if time.time() > deadline:
            print("Time budget exhausted; stopping.", flush=True)
            break
        if fig in record["tasks"]:
            print(f"Already dispatched round-2 for {fig}: {record['tasks'][fig]}",
                  flush=True)
            continue
        meta = r1.FIGURES[fig]
        if fig not in record["uploads"]:
            bdir = build_bundle_r2(fig, meta)
            print(f"Uploading revised bundle for {fig} ...", flush=True)
            stored = client.store_file_content(
                name=f"powder_doser_{fig}_round4_bundle",
                file_path=str(bdir),
                as_collection=True,
            )
            record["uploads"][fig] = f"data_entry:{stored.data_storage.id}"
            ids_path.write_text(json.dumps(record, indent=2))
            print(f"  -> {record['uploads'][fig]}", flush=True)
        query = (
            f"{r1.COMMON}\n\nThe figure under review is {fig} "
            f"({meta['where']}). This is the REVISED version after round-1 "
            f"feedback.\n\n{VERIFY_LENS}\n\n"
            "Be concrete and cite specific files, passages, panels, and "
            "branch-tree paths."
        )
        task = {
            "name": JobNames.ANALYSIS,
            "query": query,
            "tags": ["powder-doser-fig-review-verify", fig],
        }
        tid = str(client.create_task(task, files=[record["uploads"][fig]]))
        record["tasks"][fig] = tid
        ids_path.write_text(json.dumps(record, indent=2))
        print(f"  dispatched verify/{fig} -> {tid}", flush=True)
        time.sleep(args.throttle)

    print(f"Recorded task ids in {ids_path}", flush=True)


if __name__ == "__main__":
    main()
