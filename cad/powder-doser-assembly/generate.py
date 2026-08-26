#!/usr/bin/env python3
"""Generate every Powder Doser part with the zoo.dev (ML-ephant) Text-to-CAD API.

Pipeline, per prompt file in ``prompts/``:

  1. POST the prompt text to the Zoo Text-to-CAD endpoint (KCL model) and poll
     ``GET /user/text-to-cad/{id}`` until it completes.
  2. Save the generated KCL native source to ``exports/<name>/source.kcl``.
  3. Compile the KCL to STEP, GLB and OBJ with the ``zoo`` CLI.
  4. Parse the OBJ to record a bounding box for verification against the spec.

The script is resumable: a part whose ``exports/<name>/source.kcl`` already
exists is skipped unless ``--force`` (or ``--only NAME`` re-runs one part).

Requirements:
  * ``ZOO_API_TOKEN`` in the environment (Zoo / zoo.dev API token).
  * The ``zoo`` CLI on ``PATH`` or pointed to by the ``ZOO_CLI`` env var
    (https://github.com/KittyCAD/cli/releases). STEP/GLB/OBJ export is skipped
    with a warning if the CLI is unavailable.

Usage:
  python3 generate.py                 # generate all missing parts
  python3 generate.py --force         # regenerate everything
  python3 generate.py --only tap-collar
  python3 generate.py --no-export     # KCL only, skip the CLI export
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

import requests

API = "https://api.zoo.dev"
HERE = Path(__file__).resolve().parent
PROMPTS_DIR = HERE / "prompts"
EXPORTS_DIR = HERE / "exports"
USER_AGENT = "powder-doser-agent/1.0 (+https://github.com/vertical-cloud-lab/powder-doser)"
EXPORT_FORMATS = ("step", "glb", "obj")


def _token() -> str:
    tok = os.environ.get("ZOO_API_TOKEN", "").strip()
    if not tok:
        sys.exit("ZOO_API_TOKEN is not set; export your zoo.dev API token first.")
    return tok


def _headers(tok: str) -> dict:
    return {
        "Authorization": "Bearer " + tok,
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
    }


def part_name(prompt_path: Path) -> str:
    """``prompts/06-mounting-plate.md`` -> ``mounting-plate``."""
    return re.sub(r"^\d+-", "", prompt_path.stem)


def text_to_cad(prompt: str, tok: str, poll: float = 8.0, timeout: float = 420.0) -> str:
    """Submit a Text-to-CAD job and return the generated KCL source code."""
    h = _headers(tok)
    resp = requests.post(
        f"{API}/ai/text-to-cad/step?kcl=true",
        headers={**h, "Content-Type": "application/json"},
        json={"prompt": prompt},
        timeout=60,
    )
    resp.raise_for_status()
    job_id = resp.json()["id"]
    deadline = time.time() + timeout
    while time.time() < deadline:
        time.sleep(poll)
        g = requests.get(f"{API}/user/text-to-cad/{job_id}", headers=h, timeout=60).json()
        status = g.get("status")
        if status == "completed":
            code = g.get("code")
            if not code:
                raise RuntimeError(f"job {job_id} completed without KCL code")
            return code
        if status == "failed":
            raise RuntimeError(f"job {job_id} failed: {g.get('error')}")
    raise TimeoutError(f"job {job_id} did not finish within {timeout}s")


def zoo_cli() -> str | None:
    return os.environ.get("ZOO_CLI") or shutil.which("zoo")


def export_kcl(kcl_path: Path, out_dir: Path, cli: str) -> list[str]:
    """Compile a KCL file to each EXPORT_FORMAT; return the formats that worked."""
    done = []
    for fmt in EXPORT_FORMATS:
        try:
            subprocess.run(
                [cli, "kcl", "export", "--output-format", fmt, str(kcl_path), str(out_dir)],
                check=True,
                capture_output=True,
                text=True,
                timeout=300,
            )
            done.append(fmt)
        except subprocess.CalledProcessError as exc:
            print(f"    ! {fmt} export failed: {exc.stderr.strip().splitlines()[-1:]}")
        except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
            print(f"    ! {fmt} export error: {exc}")
    return done


def obj_bbox(obj_path: Path) -> dict | None:
    """Min/max/size bounding box (mm) parsed from an OBJ vertex list."""
    lo = [float("inf")] * 3
    hi = [float("-inf")] * 3
    seen = False
    for line in obj_path.read_text().splitlines():
        if line.startswith("v "):
            parts = line.split()
            if len(parts) >= 4:
                xyz = [float(parts[1]), float(parts[2]), float(parts[3])]
                for i in range(3):
                    lo[i] = min(lo[i], xyz[i])
                    hi[i] = max(hi[i], xyz[i])
                seen = True
    if not seen:
        return None
    return {
        "min": [round(v, 3) for v in lo],
        "max": [round(v, 3) for v in hi],
        "size": [round(hi[i] - lo[i], 3) for i in range(3)],
    }


def generate_part(prompt_path: Path, tok: str, do_export: bool) -> dict:
    name = part_name(prompt_path)
    out_dir = EXPORTS_DIR / name
    out_dir.mkdir(parents=True, exist_ok=True)
    prompt = prompt_path.read_text().strip()

    print(f"==> {name}: submitting Text-to-CAD job ...")
    code = text_to_cad(prompt, tok)
    kcl_path = out_dir / "source.kcl"
    kcl_path.write_text(code)
    print(f"    KCL saved ({len(code)} chars)")

    manifest = {"name": name, "prompt_file": prompt_path.name, "kcl": "source.kcl"}
    cli = zoo_cli()
    if do_export and cli:
        formats = export_kcl(kcl_path, out_dir, cli)
        manifest["exports"] = formats
        obj = out_dir / "output.obj"
        if obj.exists():
            bbox = obj_bbox(obj)
            if bbox:
                manifest["bbox_mm"] = bbox
                print(f"    bbox (mm): {bbox['size']}")
    elif do_export:
        print("    ! zoo CLI not found (set ZOO_CLI or add `zoo` to PATH); skipping export")

    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--force", action="store_true", help="regenerate parts that already exist")
    ap.add_argument("--only", help="generate only the part whose name matches this")
    ap.add_argument("--no-export", action="store_true", help="save KCL only; skip STEP/GLB/OBJ export")
    args = ap.parse_args()

    tok = _token()
    prompts = sorted(PROMPTS_DIR.glob("*.md"))
    if args.only:
        prompts = [p for p in prompts if args.only in part_name(p)]
        if not prompts:
            sys.exit(f"no prompt matches --only {args.only!r}")

    results = []
    for prompt_path in prompts:
        name = part_name(prompt_path)
        existing = EXPORTS_DIR / name / "source.kcl"
        if existing.exists() and not args.force and not args.only:
            print(f"--- {name}: already generated (use --force to redo)")
            continue
        try:
            results.append(generate_part(prompt_path, tok, do_export=not args.no_export))
        except Exception as exc:  # noqa: BLE001 - keep going on a single-part failure
            print(f"!!! {name}: {type(exc).__name__}: {exc}")

    if results:
        print(f"\nGenerated {len(results)} part(s).")


if __name__ == "__main__":
    main()
