"""Edison Scientific ``ANALYSIS`` "judge" runner for the single-channel module.

Triggered by @sgbaird's request on PR #35
(https://github.com/vertical-cloud-lab/powder-doser/pull/35) and motivated by
``paper/background/05-llm-cad-spatial-reasoning-mitigation.md`` (PR #29) which
recommends an independent VLM-Judge agent step in any LLM-CAD workflow.

Each round uploads the parametric CadQuery model + its rendered images and
asks Edison to walk every image, point out mechanical inconsistencies
(reference @williamulbz / @swcharles critiques), and propose specific fixes.

Run with:
    pip install edison_client
    export EDISON_API_KEY=...
    python design/cad/single-channel-module/edison_judge/run_judge.py round1

The runner writes ``round{N}.task.json`` + ``round{N}.answer.md`` next to it
so the provenance is committed and re-runnable.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from edison_client import EdisonClient, JobNames
from edison_client.models.app import TaskRequest

HERE = Path(__file__).resolve().parent
MOD_DIR = HERE.parent

ROUND_FILES = {
    "round1": [
        "cad_model.py",
        "sketch_2d.py",
        "README.md",
        "renders/single_channel_module_iso.png",
        "renders/single_channel_module_front.png",
        "renders/single_channel_module_side.png",
        "renders/single_channel_module_top.png",
        "renders/single_channel_module_sketch.png",
        "renders/single_channel_module_powder_flow.png",
        "renders/single_channel_module_tilt_sweep.png",
    ],
    "round2": [
        "cad_model.py",
        "sketch_2d.py",
        "README.md",
        "renders/single_channel_module_iso.png",
        "renders/single_channel_module_front.png",
        "renders/single_channel_module_side.png",
        "renders/single_channel_module_top.png",
        "renders/single_channel_module_sketch.png",
        "renders/single_channel_module_powder_flow.png",
        "renders/single_channel_module_tilt_sweep.png",
    ],
}

PROMPT = """You are acting as an independent **VLM Judge** for an LLM-generated
CAD package, in the spirit of CADSmith / GenCAD-Self-Repairing
(see paper/background/05-llm-cad-spatial-reasoning-mitigation.md in the
calling repo). Your job is to read the parametric CadQuery code AND look at
every attached render, then produce an actionable, image-by-image critique.

Repository context
------------------
- Repo: vertical-cloud-lab/powder-doser, PR #35
  (https://github.com/vertical-cloud-lab/powder-doser/pull/35).
- Module: ``design/cad/single-channel-module/`` — a self-contained
  single-channel powder doser (auger + stepper + tap solenoid + ERM
  vibration motor on a printable frame), intended to be replicated N times
  around a shared cup.
- Files attached (read them all, including the README and the matplotlib
  sketch script):
    1. ``cad_model.py`` — CadQuery assembly. Builds every printed and vendor
       part. Coordinate frame: +Z up, +Y "front" (toward viewer), +X away
       from spine. Rotor axis at (X=ROTOR_X_OFFSET, Y=0). Spine in YZ
       plane. Z=0 at the bottom of the bearing collar (lowest *frame*
       point); the rotor protrudes ~30 mm below.
    2. ``sketch_2d.py`` — matplotlib 3-panel + powder-flow + tilt-sweep.
    3. ``README.md`` — design rationale, BOM, fastener strategy, roadmap.
    4-10. Rendered PNGs (iso, front, side, top, 3-panel sketch,
          powder-flow cross-section, tilt sweep at 0/45/75/90 deg).

Reviewer history this Judge needs to verify
-------------------------------------------
@williamulbz (PR #35 review-4274628757):
  W1. Vibration motor must actually couple to the auger (was air gap in v1).
  W2. Tap-collar mounting bosses must be integral to the collar body.
  W3. Vendor envelopes must match PR #25 datasheet dimensions.
  W4. Adjustable-angle stand needed; module is normally not vertical.
  W5. Rotor must protrude past frame so powder column clears at low tilt.
  W6. Stepper on top of auger inlet has nowhere for powder to enter -- use
      belt drive or similar.
  W7. The frame should not be top-plate / bottom-plate / 4-corner-post.
  W8. Solenoid bracket must not be a thin cantilever; gusset it.
  W9. Drop the made-up 80 mm cup-rim clearance; the module shouldn't fix
      its own dispense height.
  W10. Cartridge needed for powder entry; want a powder-flow visualization.

@swcharles (PR #35 comment-4276136447):
  S1. Several parts are mechanically nonsensical -- e.g. mounting brackets
      whose two plates do not touch.
  S2. Some parts obstruct flow -- e.g. the belt drive directly under the
      cartridge, the coin motor in the middle of the collar.
  S3. Some parts are unnecessary -- e.g. large outboard plates that waste
      filament without doing structural work.
  S4. Many things are not actually coupled when they should be -- the motor
      "doesn't attach to anything" and the assembly looks like an exploded
      view.
  S5. Powder-flow diagram must use a single continuous arrow with numbered
      nodes (cartridge -> loading slots -> helix -> nozzle -> cup).
  S6. v3 must show the auger at 0, 45, and 90 deg tilt over a generic cup
      with a scale bar.
  S7. The auger is small (Ø25); the printed parts are correspondingly
      small -- flag any that are too thin / fragile to FDM print or that
      look wear-prone.
  S8. Working idea > accurate BOM. Include a generic cup + scale.
  S9. No part may have floating, unattached bodies.

@sgbaird (PR #35 comment-4434514153):
  B1. Cartridge<->auger throat is the most under-specified interface and is
      a likely powder-flow bottleneck.
  B2. Once a powder has touched a rotor, that rotor is contaminated and
      cannot be reused for any other powder. (No "shared auger, swap the
      cartridge" Idea-C variant is possible.)

What you MUST do
----------------
For EACH attached render:
  (a) Describe what the image shows in 1-2 sentences (which view, which
      parts are visible).
  (b) For every part visible: state whether the geometry as rendered makes
      mechanical sense -- is it actually attached to anything load-bearing?
      Does it overlap or "float"? Are wall thicknesses FDM-printable
      (>= 1.6 mm typical)? Is it on the wrong side of a flow path?
  (c) Cross-reference each visible issue against W1-W10, S1-S9, B1-B2.
      State which reviewer concerns each particular issue corresponds to.
  (d) Propose a specific, code-level fix that would resolve the issue --
      ideally citing the function name in ``cad_model.py`` and the
      constant whose value should change. Be concrete: "increase
      MB_FOOT_W from 60 to 90 and shift its Y-centre to MOTOR_AXIS_OFFSET_Y
      so the foot reaches the bracket face" is good; "make it bigger" is
      not.

Then produce a section "Top 5 must-fix items for v3" that ranks the
highest-leverage changes (by likelihood of preventing a print/assembly
failure), and a section "False positives / things that look wrong but
are actually fine" so the human reviewer doesn't waste time relitigating.

End with: "Open questions for the human reviewer:" -- concrete questions
where you do not have enough information from the attached files to make
the call.

Be thorough, be specific, and assume the reader is going to act on every
recommendation in the next 30 minutes. Do not hedge generically.
"""


def main(round_id: str) -> None:
    if round_id not in ROUND_FILES:
        raise SystemExit(f"unknown round: {round_id}; choose from {list(ROUND_FILES)}")
    api_key = os.environ.get("EDISON_API_KEY")
    if not api_key:
        raise SystemExit("EDISON_API_KEY env var not set")

    client = EdisonClient(api_key=api_key)
    uris: list[str] = []
    for rel in ROUND_FILES[round_id]:
        local = MOD_DIR / rel
        if not local.exists():
            print(f"  SKIP missing: {local}")
            continue
        print(f"  uploading {local} ...")
        uri = client.upload_file(local)
        print(f"    -> {uri}")
        uris.append(uri)

    task = TaskRequest(name=JobNames.ANALYSIS, query=PROMPT)
    print(f"submitting ANALYSIS task with {len(uris)} attached files ...")
    [resp] = client.run_tasks_until_done(
        task,
        files=uris,
        verbose=True,
        progress_bar=False,
        timeout=1800,
    )
    out_json = HERE / f"{round_id}.task.json"
    out_md = HERE / f"{round_id}.answer.md"
    out_json.write_text(json.dumps(resp.model_dump(mode="json"), indent=2, default=str))
    answer = getattr(resp, "formatted_answer", None) or getattr(resp, "answer", None) or ""
    out_md.write_text(str(answer))
    print(f"wrote {out_json}")
    print(f"wrote {out_md}")
    print(f"status: {getattr(resp, 'status', '?')}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "round1")
