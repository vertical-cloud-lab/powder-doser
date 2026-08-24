"""Run the CADsmith multi-agent pipeline on the mounting plate and baseplate.

This is the authoring step the issue (#58) asked for. We give CADsmith
its own prompt for each printable part, then write the resulting STEP /
STL / log into ``cadsmith_runs/<part>/``. The mounting-plate and
baseplate STEP files CADsmith produces are also copied into
``step/<part>.cadsmith.step`` so they sit next to the hand-authored
versions for side-by-side comparison.

The hand-authored ``cad_model.py`` is still the single source of truth
for the *assembly* (CADsmith is single-part by design — see README
"CADsmith — pros and cons"), but the individual printable plates are
now genuine CADsmith output.

Requires ``ANTHROPIC_API_KEY`` (exposed as ``MY_ANTHROPIC_API_KEY`` in
the Copilot Coding Agent sandbox; the runner copies it into
``ANTHROPIC_API_KEY`` before calling the pipeline).

Reproduce::

    pip install cadquery anthropic python-dotenv numpy-stl trimesh
    git clone https://github.com/vertical-cloud-lab/CADSmith /tmp/CADSmith
    export ANTHROPIC_API_KEY=...
    PYTHONPATH=/tmp/CADSmith python design/cad/mounting-plate-assembly/run_cadsmith.py
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import time
from pathlib import Path

HERE = Path(__file__).parent
OUT_ROOT = HERE / "cadsmith_runs"
OUT_ROOT.mkdir(exist_ok=True)
STEP_DIR = HERE / "step"

# Allow ``MY_ANTHROPIC_API_KEY`` from the agent sandbox to satisfy CADsmith's
# ``ANTHROPIC_API_KEY`` requirement.
if "ANTHROPIC_API_KEY" not in os.environ and "MY_ANTHROPIC_API_KEY" in os.environ:
    os.environ["ANTHROPIC_API_KEY"] = os.environ["MY_ANTHROPIC_API_KEY"]

# Make the cloned CADsmith repo importable. By convention we clone it at
# /tmp/CADSmith; allow an override via ``CADSMITH_PATH``.
CADSMITH_PATH = Path(os.environ.get("CADSMITH_PATH", "/tmp/CADSmith"))
if CADSMITH_PATH.exists() and str(CADSMITH_PATH) not in sys.path:
    sys.path.insert(0, str(CADSMITH_PATH))

from autofab.pipeline import Pipeline  # noqa: E402


# ---------------------------------------------------------------------------
# Prompts — each is a self-contained natural-language spec for a single part.
# Dimensions match the constants in ``cad_model.py`` so the CADsmith output
# is drop-in compatible with the rest of the hand-authored assembly.
# ---------------------------------------------------------------------------

MOUNTING_PLATE_PROMPT = """\
A rectangular FDM-printable mounting plate, 250 mm long (X) by 80 mm wide
(Y) by 5 mm thick (Z), with 6 mm radius rounded corners. The discharge
end of the plate (X = 0) has a U-shaped notch cut into it, 24 mm deep
along X, 31 mm wide along Y, centred on Y = 0. This notch lets powder
fall straight down past the plate.

The plate has these through-holes for mounting other components from
above (all drilled fully through the 5 mm plate, axes parallel to Z):

  * BRK-D group (auger bracket #1, near the discharge end):
    four 3.4 mm clearance holes for M3 screws in a rectangular pattern,
    38 mm spacing along X and 18 mm spacing along Y, pattern centred on
    (X = 35, Y = 0).
  * TAP group (tap-collar mounting flange):
    four 3.4 mm clearance holes for M3 screws in a rectangular pattern,
    38 mm spacing along X and 18 mm spacing along Y, pattern centred on
    (X = 95, Y = 0).
  * BRK-M group (auger bracket #2, near the motor end):
    four 3.4 mm clearance holes for M3 screws in a rectangular pattern,
    38 mm spacing along X and 18 mm spacing along Y, pattern centred on
    (X = 155, Y = 0).
  * NEMA-17 group (stepper motor mount):
    four 3.4 mm M3 clearance holes on a 31 mm x 31 mm square pattern
    centred on (X = 215, Y = 0), plus a single 22.4 mm diameter pilot
    boss clearance hole through the centre at (X = 215, Y = 0).

Hanging DOWN from the underside of the plate (i.e. solid features
attached to the bottom face, extending toward negative Z), the plate
carries:

  * Two hinge pillars, one at Y = +20.5 and one at Y = -20.5, both
    centred on X = 18. Each pillar is 14 mm along X, 6 mm along Y, and
    extends 24.5 mm downward from the plate underside. Each pillar has a
    5.2 mm horizontal pin hole through its Y-direction face, with the
    pin axis parallel to Y, located 18.5 mm below the plate underside
    so it lies on the auger long axis. The two holes are coaxial — they
    form one continuous hinge pin path.
  * One linear-actuator clevis tab, 16 mm along X, 6 mm along Y, 22 mm
    tall, centred on (X = 73, Y = 0) and extending 22 mm downward from
    the plate underside. It has a single 5.2 mm horizontal clevis pin
    hole through its Y face, 5 mm down from the top of the tab.

The part must print flange-up (top face of the plate on the build plate)
with the hinge pillars and clevis tab as overhangs handled by tree
supports. All other features print without supports. Output a single
solid body (the plate, pillars, and tab fused together) — return STEP
and STL.
"""

BASEPLATE_PROMPT = """\
A rectangular FDM-printable baseplate, 300 mm long (X) by 200 mm wide
(Y) by 6 mm thick (Z), with 8 mm radius rounded corners. The plate is
positioned so it spans X = -30 to X = 270, centred on Y = 0.

The plate has a rectangular discharge cut-out, 70 mm along X and 70 mm
along Y, centred on (X = 18, Y = 0), cut fully through the 6 mm
thickness. Powder falls through this opening to a cup below.

Standing UP from the top face of the plate (extending toward positive Z):

  * Two hinge pillars, one at Y = +27.5 and one at Y = -27.5, both
    centred on X = 18. Each pillar is 14 mm along X, 6 mm along Y, and
    50 mm tall. Each pillar has a 5.2 mm horizontal pin hole through its
    Y face, with the pin axis parallel to Y, located 21 mm above the
    plate top surface (i.e. 4 mm below the top of the pillar). The two
    holes are coaxial — they form one continuous hinge pin path.
  * Two linear-actuator clevis lugs, 14 mm along X, 4 mm along Y, 25 mm
    tall. One is centred on (X = 148, Y = +8) and the other on
    (X = 148, Y = -8). Each has a 5.2 mm horizontal clevis pin hole
    through its Y face, 5 mm below the top of the lug.

Hanging DOWN from the bottom face of the plate (extending toward
negative Z), the plate has four square legs, 18 mm x 18 mm cross
section, each 150 mm tall. The legs are inset 13 mm from the
respective baseplate corners, at:
    (X = -17, Y = -87), (X = -17, Y = +87),
    (X = 257, Y = -87), (X = 257, Y = +87).
Each leg also has a single 4.4 mm M4 clearance hole drilled through its
outermost X face, 15 mm above the bottom of the leg, for an optional
cross-brace rail.

The part must print plate-up (top face on the build plate is fine — flip
in the slicer so the legs print downward, supported only if your printer
needs it). Output a single solid body. Return STEP and STL.
"""

PARTS = [
    ("mounting_plate", MOUNTING_PLATE_PROMPT),
    ("baseplate",      BASEPLATE_PROMPT),
]


def run_one(name: str, prompt: str) -> dict:
    out_dir = OUT_ROOT / name
    out_dir.mkdir(exist_ok=True)
    print(f"\n{'=' * 70}\nCADsmith run: {name}\n{'=' * 70}")
    t0 = time.time()
    pipeline = Pipeline(
        output_dir=str(out_dir),
        max_error_retries=3,
        max_refinement_iterations=5,
        verbose=True,
    )
    result = pipeline.run(prompt, name=name)
    elapsed = time.time() - t0

    summary = {
        "part": name,
        "converged": bool(result.converged),
        "iterations": len(result.iterations),
        "llm_calls": result.total_llm_calls,
        "elapsed_s": round(elapsed, 1),
        "final_step_path": result.final_step_path,
        "final_geometry": getattr(result, "final_geometry", None),
    }
    log_path = out_dir / f"{name}_log.json"
    with open(log_path, "w") as f:
        json.dump(result.to_dict(), f, indent=2, default=str)

    # Copy the converged STEP next to the hand-authored one for
    # side-by-side comparison.
    if result.final_step_path and Path(result.final_step_path).exists():
        STEP_DIR.mkdir(exist_ok=True)
        dst = STEP_DIR / f"{name}.cadsmith.step"
        shutil.copy(result.final_step_path, dst)
        summary["copied_to"] = str(dst.relative_to(HERE))
    else:
        summary["copied_to"] = None

    print(f"\n→ {name}: converged={summary['converged']}, "
          f"{summary['iterations']} iters, "
          f"{summary['llm_calls']} LLM calls, "
          f"{summary['elapsed_s']:.1f}s")
    return summary


def main() -> None:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("ANTHROPIC_API_KEY is not set. Export it and re-run.")
    summaries = [run_one(name, prompt) for name, prompt in PARTS]
    with open(OUT_ROOT / "summary.json", "w") as f:
        json.dump(summaries, f, indent=2)
    print("\n=== CADsmith summary ===")
    for s in summaries:
        print(f"  {s['part']:>16}: converged={s['converged']} "
              f"iters={s['iterations']} llm_calls={s['llm_calls']} "
              f"elapsed={s['elapsed_s']}s")


if __name__ == "__main__":
    main()
