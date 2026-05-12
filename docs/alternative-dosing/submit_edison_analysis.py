"""Submit a single Edison Scientific **analysis** task with all the
per-concept design data, code, and images attached.

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

NEW since the prior analysis submission: the project reviewer asked
that the per-concept dispensing animations "actually line up
spatially" and that "the timing sequence for each component is
sync'ing up with each other". We rewrote `scripts/animate_dispensing.py`
around a shared `Stage` object that exposes fixed anchors used by
**every** concept (same canvas size, same bed-line Y, same vial mouth
position, same gantry-rail Y, same mechanism rest column) and a
**shared phase clock** mapping the global cycle t in [0,1) to four
named stages used by every concept (LOAD -> APPROACH -> DISPENSE ->
SETTLE) at fixed boundaries (0.00, 0.25, 0.42, 0.85, 1.00). Each
concept is composed from small independently-positioned sub-component
draw functions (`draw_vial`, `draw_anvil`, `draw_cup_with_mesh`,
`draw_pez_strip`, `draw_capillary`, `draw_brush_disc`, `draw_auger`,
`draw_erm_motor`, `draw_solenoid_actuator`, `draw_balance`,
`draw_powder_pad`, `draw_falling_stream`) layered on top of the
shared Stage. The 4x2 `composite-animation.gif` is now built directly
from the per-concept render functions (not from the on-disk per-tile
GIFs) to bypass GIF palette/de-dup so tiles never desync. Net effect:
the bed-line, vial mouths, gantry rails, and mechanism columns line
up across tiles, and all eight mechanisms load/approach/dispense/
settle at the same global t. The composite-animation.gif is the best
single artefact to read first now; please use it as the entry point.

The eight SCAD sources, iso renders, cutaway sections, the four
composite previews (composite-animation.gif, composite-panel.png,
composite-spin.gif, composite-cutaway.png), the eight per-concept
panels, and the eight per-concept dispensing animations are all
attached. The pipeline driver (scripts/render_alternatives.py),
the panel annotator (scripts/annotate_alternatives.py), and the
new dispensing animator (scripts/animate_dispensing.py) are also
attached so you can see exactly what was generated.

Please give us a critical engineering review covering:

1. Per-concept printability and mechanism viability on the 3018-Pro
   V2: pull from the SCAD parameters and the cutaway cross sections.
   In particular flag any geometry where the cutaway suggests a
   bridging / overhang / wall-thickness problem that the slicer
   warned about but we may have missed.

2. Per-concept dose floor and RSD vs the published analogues
   already cited in our prior literature query (Besenhard 2015
   vibratory sieve-chute, Faulhammer 2014 dosator, Alsenz 2011
   PowderPicking, Hou 2024, Jiang 2023). We previously concluded G
   then A. With the geometry and motion now both visible, do you
   still agree, or does any other concept now look more promising?

3. Cohesive sub-100-um powder failure modes specific to each
   geometry and motion sequence: bridging in B's chambers,
   capillary plug variability in C, brush retention in D,
   hole-clogging in E, helix pull-down in F, etc. Cite
   peer-reviewed sources where available.

4. Specific incremental design or motion-cycle changes (a sentence
   or two each per concept) that would most reduce variability or
   improve one-day-build success. Be concrete -- we are about to
   print these.

5. Anything obviously missing (a concept we should add, a
   peer-reviewed analogue we should be benchmarking against, a
   safety/EHS concern with HV / solenoid / heated alternatives).

Don't wait more than ~10 min — we will fetch then.
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
        REPO / "cad" / "alternatives" / "render-report.txt",
        REPO / "cad" / "alternatives" / "composite-spin.gif",
        REPO / "cad" / "alternatives" / "composite-cutaway.png",
        REPO / "cad" / "alternatives" / "composite-panel.png",
        REPO / "cad" / "alternatives" / "composite-animation.gif",
        REPO / "cad" / "alternatives" / "README.md",
    ]
    alt_dir = REPO / "cad" / "alternatives"
    paths += sorted(alt_dir.glob("[A-H]_*.scad"))
    paths += sorted(alt_dir.glob("[A-H]-*-iso.png"))
    paths += sorted(alt_dir.glob("[A-H]-*-cutaway.png"))
    paths += sorted(alt_dir.glob("[A-H]-*-panel.png"))
    paths += sorted(alt_dir.glob("[A-H]-*-animation.gif"))
    return [str(p) for p in paths if p.exists()]


def main() -> int:
    api_key = os.environ.get("EDISON_API_KEY")
    if not api_key:
        sys.stderr.write("EDISON_API_KEY is not set\n")
        return 1

    files = _collect_files()
    if not files:
        sys.stderr.write("no files collected for upload; aborting\n")
        return 2
    sys.stderr.write(f"submitting {len(files)} attachments\n")

    client = EdisonClient(api_key=api_key)
    request = TaskRequest(
        name=JobNames.ANALYSIS,
        query=QUERY,
        tags=[QUERY_TAG, "issue-12", "pr-13", "powder-excavator"],
    )
    submitted_at = _dt.datetime.now(tz=_dt.timezone.utc).isoformat()
    task = client.create_task(request, files=files)

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
        "attached_files": [os.path.relpath(f, REPO) for f in files],
    }

    out_path = HERE / "edison_analysis_query.json"
    out_path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(f"Submitted Edison analysis task {task_id}; recorded at {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
