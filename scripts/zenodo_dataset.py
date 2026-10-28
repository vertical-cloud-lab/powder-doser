"""Build and upload the experimental dataset behind the Digital Discovery paper to Zenodo.

The software release (v1.0.0) is archived by Zenodo's GitHub integration. This script
archives the *data* separately, as a dataset record owned by the shared ``byu-vcl``
Zenodo account, following the pattern of sparks-baird/matsci-opt-benchmarks
(``zenodo_client``). The bundle holds:

- ``powder-doser-raw-runs.zip``: every raw run directory (``data/battery/<run>/``) the
  paper uses, taken from the issue #116 campaign branch at a pinned commit, because
  these files are not on ``main``;
- ``powder-doser-tidy-data.zip``: the tidy CSVs in ``paper/figures/data/`` behind the
  figures and SI tables;
- ``README.md`` and ``DATA-DICTIONARY.md``, which are also uploaded as plain files.

Tokens come from the environment: ``ZENODO_API_TOKEN`` (production) and
``ZENODO_SANDBOX_API_TOKEN`` (sandbox). Never print them.

Usage (run from the repo root):

    python scripts/zenodo_dataset.py build                 # bundle into build/zenodo-dataset/
    python scripts/zenodo_dataset.py upload --sandbox      # create and PUBLISH on sandbox
    python scripts/zenodo_dataset.py upload --production --license cc-by-4.0
                                                           # DRAFT on zenodo.org, DOI reserved

Production uploads are never published by this script. A person publishes the draft in
the Zenodo web interface, because a published DOI cannot be withdrawn. Each target keeps
its deposition id in ``paper/zenodo/dataset_<target>.json``; a later upload to the same
target adds a new version instead of a new record.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "build" / "zenodo-dataset"
STATE_DIR = REPO / "paper" / "zenodo"
TIDY_DIR = REPO / "paper" / "figures" / "data"
RUNS_CSV = TIDY_DIR / "runs_all.csv"

# Issue #116 campaign branch holding all 37 raw run directories listed in runs_all.csv.
RAW_BRANCH = "claude/issue-116-20260915-1622"
RAW_COMMIT = "f7544503d010356feb2a5c56377b526d0a112ff3"
RAW_PATH = "data/battery"

TITLE = (
    "Raw and processed test data for an open-source, 3D-printed auger powder doser: "
    "13 powders, open-loop conveyance protocols and closed-loop dosing"
)
VERSION = "1.0.0"
SANDBOX_LICENSE = "cc-by-4.0"  # sandbox only; production needs --license

# What each file kind in a raw run directory holds. Tilt in the raw records is the
# servo setting; the tube angle is half of it (2:1 tilt gear), so 45 -> 22.5 deg.
RAW_FILES = {
    "run_<powder>.json": "Run metadata: status, start and end times (UTC and lab time), "
    "block timeline, powder and batch, operator (GitHub handle) and notes, quality checks, "
    "environment checks, retries, firmware commit and parameters, and copies of the trial, "
    "poll and dose records.",
    "preflight_<powder>.json": "Pre-run feed check: verdict, mass per revolution and per tap, "
    "tilt (servo setting) and rpm used.",
    "trials_<powder>.csv": "One row per trial of protocols A-F: block (protocol letter), "
    "tilt_deg (servo setting), phase, action, rpm, balance reading before and after (g), "
    "delta_g, noise and drift estimates (g), retries and a quality flag; t_ms is firmware "
    "time in milliseconds.",
    "summary_<powder>.csv": "Per protocol, tilt and phase: n, mean, standard deviation, "
    "standard error, min and max of delta_g (g), and relative standard deviation (%).",
    "polls_<powder>.csv": "Balance readings streamed during protocol D (speed sweep): "
    "tilt_deg (servo setting), rpm, t_ms, grams, and the balance's stability flag.",
    "doses_<powder>.csv": "One row per closed-loop dose (protocols G and H): target_g, "
    "dispensed_g, error_g, firmware status (ok, overshoot, stalled, cycle budget, timeout), "
    "elapsed_s, auger revolutions, taps, cycles per phase.",
    "timeline_<powder>.csv": "Start time and elapsed time of each protocol block.",
    "raw_serial_<powder>.log": "Verbatim serial transcript between the host and the "
    "Raspberry Pi Pico W firmware.",
    "*.png": "Quick-look plots written by the host during the run.",
}


def git(*args: str) -> str:
    env = {**os.environ, "MSYS_NO_PATHCONV": "1"}
    return subprocess.run(
        ["git", *args], cwd=REPO, check=True, capture_output=True, text=True, env=env
    ).stdout


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def raw_ref() -> str:
    """Return a ref for the pinned raw-data commit, fetching the branch if needed."""
    try:
        git("cat-file", "-e", f"{RAW_COMMIT}^{{commit}}")
    except subprocess.CalledProcessError:
        git("fetch", "origin", RAW_BRANCH)
    return RAW_COMMIT


def build_raw_zip(dest: Path) -> list[str]:
    ref = raw_ref()
    with RUNS_CSV.open(encoding="utf-8") as f:
        wanted = [row["data_dir"] for row in csv.DictReader(f)]
    have = set(git("ls-tree", "-d", "--name-only", ref, f"{RAW_PATH}/").split())
    missing = [d for d in wanted if d not in have]
    if missing:
        sys.exit(f"raw runs missing at {ref[:7]}: {missing}")
    git("archive", "--format=zip", f"--prefix=powder-doser-raw-runs/", "-o", str(dest), ref, *wanted)
    return wanted


def build_tidy_zip(dest: Path) -> list[Path]:
    csvs = sorted(TIDY_DIR.glob("*.csv"))
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as z:
        for p in csvs:
            z.write(p, f"powder-doser-tidy-data/{p.name}")
    return csvs


def infer_type(values: list[str]) -> str:
    vals = [v for v in values if v != ""]
    if not vals:
        return "empty"
    for kind, cast in (("integer", int), ("number", float)):
        try:
            for v in vals:
                cast(v)
            return kind
        except ValueError:
            pass
    if all(v in {"True", "False", "true", "false"} for v in vals):
        return "boolean"
    return "text"


def data_dictionary(csvs: list[Path]) -> str:
    lines = [
        "# Data dictionary",
        "",
        "## Raw run directories (`powder-doser-raw-runs.zip`)",
        "",
        "Each directory is named `<UTC start>_<powder id>` and holds the files below. "
        "Masses are in grams and firmware times (`t_ms`) in milliseconds. **Tilt in the raw "
        "records is the servo setting; the tube angle is half of it** (2:1 tilt gear), so the "
        "settings 0, 45 and 90 are tube angles of 0, 22.5 and 45 degrees. The block letter is "
        "the test protocol (A-H) of the paper's Table 2.",
        "",
        "| File | Contents |",
        "|---|---|",
        *[f"| `{k}` | {v} |" for k, v in RAW_FILES.items()],
        "",
        "## Tidy tables (`powder-doser-tidy-data.zip`)",
        "",
        "Built by the scripts in `paper/figures/data/` of the software release, mostly from "
        "the raw runs; `ai_*`, `auger_comparison` and `design_log_cad` instead summarize the "
        "AI-tool usage and design log. Types are inferred from the values. Tilt values copied "
        "from the raw records, such as `preflight_tilt_deg` in `runs_all.csv`, are servo "
        "settings too.",
        "",
    ]
    for p in csvs:
        with p.open(encoding="utf-8", newline="") as f:
            rows = list(csv.reader(f))
        if not rows:
            continue
        header, body = rows[0], rows[1:]
        lines += [f"### `{p.name}` ({len(body)} rows)", "", "| Column | Type | Example |", "|---|---|---|"]
        for i, col in enumerate(header):
            vals = [r[i] for r in body if i < len(r)]
            example = next((v for v in vals if v != ""), "").replace("|", "\\|").replace("\n", " ")
            if len(example) > 60:
                example = example[:57] + "..."
            lines.append(f"| `{col}` | {infer_type(vals)} | {example} |")
        lines.append("")
    return "\n".join(lines)


def readme(runs: list[str], files: list[Path], head: str) -> str:
    rows = "\n".join(f"| `{p.name}` | {p.stat().st_size / 1e6:.2f} MB | `{sha256(p)}` |" for p in files)
    return f"""# {TITLE}

Version {VERSION}. Data for the article "An open-source, 3D-printed auger powder doser
designed with generative artificial intelligence" (*Digital Discovery*, submitted). The
design files, firmware and analysis code are archived separately as the software release of
https://github.com/vertical-cloud-lab/powder-doser.

The campaign covered 13 powders in two rounds (4-21 August and 3-15 September 2026):
open-loop protocols A-F (balance baseline, static hold, rotation, speed sweep, tap,
vibration) and closed-loop doses of 50 mg, 200 mg and 1 g (protocols G and H). The bundle
holds all {len(runs)} raw run directories the paper analyses, including runs excluded by
screening; `runs_all.csv` in the tidy tables gives each run's screening verdict and reason.

## Files

| File | Size | SHA-256 |
|---|---|---|
{rows}

## Provenance

- Raw runs: branch `{RAW_BRANCH}` at commit `{RAW_COMMIT}` (issue #116).
- Tidy tables: `paper/figures/data/` at commit `{head}`.
- Bundle built {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")} by
  `scripts/zenodo_dataset.py`.

See `DATA-DICTIONARY.md` for the file formats and columns.
"""


def build() -> list[Path]:
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    raw_zip, tidy_zip = OUT / "powder-doser-raw-runs.zip", OUT / "powder-doser-tidy-data.zip"
    runs = build_raw_zip(raw_zip)
    csvs = build_tidy_zip(tidy_zip)
    dd = OUT / "DATA-DICTIONARY.md"
    dd.write_text(data_dictionary(csvs), encoding="utf-8")
    head = git("rev-parse", "--short=7", "HEAD").strip()
    rd = OUT / "README.md"
    rd.write_text(readme(runs, [raw_zip, tidy_zip, dd], head), encoding="utf-8")
    files = [rd, dd, raw_zip, tidy_zip]
    for p in files:
        print(f"{p.relative_to(REPO)}  {p.stat().st_size / 1e6:.2f} MB")
    print(f"{len(runs)} raw runs, {len(csvs)} tidy CSVs")
    return files


def metadata(license_id: str, production: bool) -> dict:
    zj = json.loads((REPO / ".zenodo.json").read_text(encoding="utf-8"))
    md = {
        "title": TITLE,
        "upload_type": "dataset",
        "version": VERSION,
        "description": (
            "<p>Raw balance records and processed tables from the test campaign of an "
            "open-source, 3D-printed, single-channel auger powder doser: 13 powders (seven "
            "food-safe surrogates and six relevant to alloy discovery) under fixed open-loop "
            "test protocols, and closed-loop doses of 50 mg, 200 mg and 1 g.</p><p>See "
            "README.md and DATA-DICTIONARY.md. The design files, firmware and analysis code "
            "are archived separately as the software release of "
            "https://github.com/vertical-cloud-lab/powder-doser.</p>"
        ),
        "creators": zj["creators"],
        "keywords": zj["keywords"] + ["powder flow", "gravimetric data"],
        "access_right": "open",
        "license": license_id,
        "related_identifiers": [
            {
                "identifier": "https://github.com/vertical-cloud-lab/powder-doser",
                "relation": "isSupplementTo",
                "resource_type": "software",
                "scheme": "url",
            }
        ],
        "prereserve_doi": True,
    }
    if production:
        md["communities"] = [{"identifier": "vcl"}]
    return {"metadata": md}


def upload(production: bool, license_id: str | None) -> None:
    from zenodo_client import Zenodo

    target = "production" if production else "sandbox"
    if production and (not license_id or license_id.upper().startswith("TODO")):
        sys.exit("production upload needs --license (SUBMISSION-DECISIONS.md item 5)")
    var = "ZENODO_API_TOKEN" if production else "ZENODO_SANDBOX_API_TOKEN"
    token = os.environ.get(var)
    if not token:
        sys.exit(f"{var} is not set")

    files = build()
    client = Zenodo(access_token=token, sandbox=not production)
    state_file = STATE_DIR / f"dataset_{target}.json"
    # Production stays a draft; a person publishes it on zenodo.org.
    publish = not production
    if state_file.exists():
        dep_id = json.loads(state_file.read_text(encoding="utf-8"))["deposition_id"]
        res = client.update(str(dep_id), files, publish=publish)
    else:
        res = client.create(metadata(license_id or SANDBOX_LICENSE, production), files, publish=publish)
    res.raise_for_status()
    dep = res.json()
    md = dep.get("metadata", {})
    state = {
        "target": target,
        "deposition_id": dep["id"],
        "concept_id": dep.get("conceptrecid"),
        "doi": dep.get("doi") or md.get("doi") or md.get("prereserve_doi", {}).get("doi"),
        "concept_doi": dep.get("conceptdoi"),
        "state": dep.get("state"),
        "submitted": dep.get("submitted"),
        "html": dep.get("links", {}).get("html"),
        "files": [f["filename"] for f in dep.get("files", [])],
        "updated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    state_file.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(state, indent=2))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("build", help="bundle the dataset into build/zenodo-dataset/")
    up = sub.add_parser("upload", help="build, then upload")
    g = up.add_mutually_exclusive_group(required=True)
    g.add_argument("--sandbox", action="store_true", help="create and publish on sandbox.zenodo.org")
    g.add_argument("--production", action="store_true", help="draft on zenodo.org, DOI reserved, not published")
    up.add_argument("--license", help="Zenodo licence id, e.g. cc-by-4.0 or cc0-1.0 (required for production)")
    args = ap.parse_args()
    if args.cmd == "build":
        build()
    else:
        upload(args.production, args.license)


if __name__ == "__main__":
    main()
