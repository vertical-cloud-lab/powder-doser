"""Submit a single Edison Scientific **analysis** task with all the
per-concept design data, code, and images attached.

**Correct upload protocol** (per the official ``edison_client`` REST
client docstring at ``rest_client.py:1166``): the ``files=`` argument to
``EdisonClient.create_task`` expects a list of *data-entry URIs* in the
form ``"data_entry:{uuid}"`` — **not** local file paths. Local paths
must first be uploaded via ``client.upload_file(path)`` which stages the
content in the data-storage service and returns a usable URI. Passing
raw local paths writes them verbatim into ``runtime_config.environment_config.data_storage_uris``
and Edison fails the task server-side with ``status=fail`` and
``answer=None``. (Prior 4 analysis tasks on this PR all failed exactly
that way — see ``edison_analysis_result.md``.) This script now does the
upload step explicitly before calling ``create_task``.

Per comment 4316944381 on PR #13 (issue #12) — submit, don't wait,
fetch in next session. The submitted bundle includes:

- brainstorm + per-concept design notes
- all 8 SCAD sources (cad/alternatives/A..H)
- all 8 iso PNGs and cutaway PNGs
- composite-spin.gif and composite-cutaway.png
- render-report.txt
- the pipeline driver script (scripts/render_alternatives.py)

The Edison API key is read from ``EDISON_API_KEY`` and never echoed.
"""
from __future__ import annotations

import datetime as _dt
import json
import os
import pathlib
import sys

from edison_client import EdisonClient, JobNames
from edison_client.models.app import TaskRequest

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent.parent
QUERY_TAG = "alternative-powder-dosing-per-concept-feedback"

QUERY = """We have refined eight alternative powder-dosing concepts (A
through H, see attached `brainstorm.md` and `per-concept-designs.md`)
into preliminary printable CAD on a Genmitsu 3018-Pro V2 desktop CNC
gantry (~300 x 180 x 45 mm work envelope, ~3 kg payload, GRBL). Each
concept is treated individually: parametric OpenSCAD source -> binary
STL (manifold checked with admesh, 0 bad edges across all 8) -> iso
PNG -> half-cutaway PNG -> 36-frame transparent rotating GIF ->
PrusaSlicer slice on the MK3S+ profile (PETG, 0.2 mm, 3 perimeters,
30% gyroid infill, 4 mm brim, supports on -- all 8 sliced cleanly).

**NEW in this submission (PR-#13 comment 4427631537):**

1. The dispensing visualisations are now grounded in **real CAD
   geometry** built with CadQuery (8 STEP-203 files, one per concept,
   attached as A_scene.step ... H_scene.step). Each scene contains the
   3018-Pro V2 bed slab, gantry rail and 15 mm-OD vial in a single
   shared millimetre world frame, plus the per-concept mechanism in
   its LOAD pose. A single `SideProjector` then maps every part's
   CadQuery AABB to pixels for every animation tile, so the bed-line,
   vial mouths, gantry rail and mechanism home column line up across
   all eight tiles **by construction** instead of by manual numeric
   matching. See `cad/alternatives_cq/README.md`, the new
   `composite_animation.gif`, and the per-concept phase stills
   (`<X>_frame_<LOAD|APPROACH|DISPENSE|SETTLE>.png`).

2. The Edison file-upload protocol was wrong on all 4 prior analysis
   tasks: we passed raw local paths to `create_task(files=...)`, but
   that argument expects `data_entry:{uuid}` URIs returned by
   `client.upload_file()`. The submitter now uploads every file via
   the data-storage service first, captures the returned URIs, and
   only then calls `create_task`. This submission is the first that
   actually delivers attachments to the analysis run.

Please give us a critical engineering review covering:

1. Per-concept printability and mechanism viability on the 3018-Pro
   V2: pull from the SCAD parameters, the cutaway cross sections, and
   the new CAD-grounded scenes (STEP files attached). Flag any
   geometry where the cutaway suggests a bridging / overhang /
   wall-thickness problem.

2. Per-concept dose floor and RSD vs the published analogues already
   cited (Besenhard 2015, Faulhammer 2014, Alsenz 2011 PowderPicking,
   Hou 2024, Jiang 2023). We previously concluded G then A. With the
   geometry now visible in scale-correct mm and the motion in a
   shared world frame, do you still agree, or does any other concept
   now look more promising?

3. Cohesive sub-100-um powder failure modes specific to each geometry
   and motion sequence: bridging in B's chambers, capillary plug
   variability in C, brush retention in D, hole-clogging in E,
   helix pull-down in F, etc.

4. Specific incremental design or motion-cycle changes (a sentence or
   two each per concept) that would most reduce variability or
   improve one-day-build success.

5. Anything obviously missing.

Don't wait more than ~10 min — we will fetch next session.
"""


def _collect_files() -> list[str]:
    paths: list[pathlib.Path] = []
    paths += [
        HERE / "brainstorm.md",
        HERE / "per-concept-designs.md",
        HERE / "edison_result.md",
        REPO / "scripts" / "render_alternatives.py",
        REPO / "scripts" / "annotate_alternatives.py",
        REPO / "scripts" / "animate_dispensing.py",
        REPO / "scripts" / "scene_world_frame.py",
        REPO / "scripts" / "scene_cad.py",
        REPO / "scripts" / "animate_dispensing_cad.py",
        REPO / "cad" / "alternatives" / "render-report.txt",
        REPO / "cad" / "alternatives" / "composite-spin.gif",
        REPO / "cad" / "alternatives" / "composite-cutaway.png",
        REPO / "cad" / "alternatives" / "composite-panel.png",
        REPO / "cad" / "alternatives" / "composite-animation.gif",
        REPO / "cad" / "alternatives" / "README.md",
        REPO / "cad" / "alternatives_cq" / "README.md",
        REPO / "cad" / "alternatives_cq" / "manifest.json",
        REPO / "cad" / "alternatives_cq" / "composite_animation.gif",
    ]
    alt_dir = REPO / "cad" / "alternatives"
    paths += sorted(alt_dir.glob("[A-H]_*.scad"))
    paths += sorted(alt_dir.glob("[A-H]-*-iso.png"))
    paths += sorted(alt_dir.glob("[A-H]-*-cutaway.png"))
    paths += sorted(alt_dir.glob("[A-H]-*-panel.png"))
    paths += sorted(alt_dir.glob("[A-H]-*-animation.gif"))
    # New CAD-grounded scenes + per-concept animations
    cq_dir = REPO / "cad" / "alternatives_cq"
    paths += sorted(cq_dir.glob("[A-H]_scene.step"))
    paths += sorted(cq_dir.glob("[A-H]_animation.gif"))
    paths += sorted(cq_dir.glob("[A-H]_frame_*.png"))
    return [str(p) for p in paths if p.exists()]


def main() -> int:
    api_key = os.environ.get("EDISON_API_KEY")
    if not api_key:
        sys.stderr.write("EDISON_API_KEY is not set\n")
        return 1

    local_files = _collect_files()
    if not local_files:
        sys.stderr.write("no files collected for upload; aborting\n")
        return 2
    sys.stderr.write(f"uploading {len(local_files)} attachments via data-storage service\n")

    client = EdisonClient(api_key=api_key)

    # Edison's ``create_task(files=...)`` expects a list of
    # ``data_entry:{uuid}`` URIs returned by ``upload_file`` — passing
    # raw local paths writes them verbatim into ``data_storage_uris``
    # and the task fails server-side (status=fail, answer=None). The
    # 4 prior analysis tasks on this PR all failed for this reason;
    # see docs/alternative-dosing/edison_analysis_result.md.
    file_uris: list[str] = []
    upload_errors: list[tuple[str, str]] = []
    for path in local_files:
        try:
            uri = client.upload_file(
                path,
                description=f"Attachment for {QUERY_TAG} (PR #13)",
                tags=[QUERY_TAG, "issue-12", "pr-13"],
            )
            file_uris.append(uri)
            sys.stderr.write(f"  uploaded {os.path.relpath(path, REPO)} -> {uri}\n")
        except Exception as exc:  # noqa: BLE001 — best-effort per-file
            upload_errors.append((os.path.relpath(path, REPO), str(exc)))
            sys.stderr.write(
                f"  WARN: upload failed for {path}: {exc}\n"
            )

    if not file_uris:
        sys.stderr.write(
            "ERROR: no files uploaded successfully; refusing to submit "
            "an analysis task with zero attachments.\n"
        )
        return 4

    request = TaskRequest(
        name=JobNames.ANALYSIS,
        query=QUERY,
        tags=[QUERY_TAG, "issue-12", "pr-13", "powder-excavator"],
    )
    submitted_at = _dt.datetime.now(tz=_dt.timezone.utc).isoformat()
    task = client.create_task(request, files=file_uris)

    if isinstance(task, str):
        task_id: str | None = task
    else:
        task_id = (
            getattr(task, "id", None)
            or getattr(task, "task_id", None)
        )
        if task_id is None and isinstance(task, dict):
            task_id = task.get("id") or task.get("task_id")
        task_id = str(task_id) if task_id is not None else None

    if not task_id:
        sys.stderr.write(
            "ERROR: could not extract a task id from create_task() "
            f"return value (got: {task!r}); refusing to write a null "
            "record.\n"
        )
        return 3

    record = {
        "tag": QUERY_TAG,
        "task_id": task_id,
        "job_name": str(JobNames.ANALYSIS),
        "submitted_at": submitted_at,
        "wait_policy": "do-not-wait (per comment 4316944381); fetch in next session",
        "query": QUERY,
        "attached_files": [os.path.relpath(f, REPO) for f in local_files],
        "uploaded_file_uris": file_uris,
        "upload_errors": [
            {"path": p, "error": e} for p, e in upload_errors
        ],
    }

    out_path = HERE / "edison_analysis_query.json"
    out_path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(f"Submitted Edison analysis task {task_id}; recorded at {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
