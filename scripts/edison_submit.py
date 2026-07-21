"""Submit and poll Edison Scientific tasks via the edisonscientific endpoint.

The Edison Platform is reached at ``https://api.platform.edisonscientific.com``
(NOT ``https://api.platform.futurehouse.org`` -- that's the public FutureHouse
endpoint, which is different infrastructure with different access controls).
We re-use the open-source ``futurehouse-client`` SDK because it speaks the
same protocol, but every constructor here pins ``service_uri`` to the Edison
host so we can't accidentally talk to the wrong cluster.

Authentication is via the ``EDISON_API_KEY`` environment variable.

Usage examples (run from the repo root):

    # Submit a fresh literature-deep query (paperqa3-high) for generative-CAD
    python scripts/edison_submit.py submit-cad-litreview

    # Submit one iteration of the analysis feedback cycle bundling the design
    # context (README, manuscript, prior analyses, CAD) inline into the query
    python scripts/edison_submit.py submit-analysis 1

    # Poll a previously-submitted task and dump its formatted answer
    python scripts/edison_submit.py poll <task_id>
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
import tempfile
from pathlib import Path

from futurehouse_client import FutureHouseClient, TaskRequest
from futurehouse_client.models.app import RuntimeConfig

# The Edison Scientific platform endpoint. This is the canonical answer to
# "you're using futurehouse, should be using edisonscientific" -- the SDK
# defaults to FutureHouse PROD, so we override.
EDISON_SERVICE_URI = "https://api.platform.edisonscientific.com"

# Edison job names (the SDK's JobNames enum points at older paperqa2 names;
# Edison exposes the paperqa3 family + the data-analysis-crow-high job).
JOB_LITERATURE_HIGH = "job-futurehouse-paperqa3-high"
JOB_ANALYSIS = "job-futurehouse-data-analysis-crow-high"

REPO_ROOT = Path(__file__).resolve().parent.parent

# Files we embed inline (as fenced text blocks) into every analysis iteration
# so Edison sees the full design context without depending on the chunked
# upload endpoint, which currently 404s on the Edison cluster. Total payload
# is ~135 KB -- well within reasonable query size.
CONTEXT_TEXT_FILES: tuple[Path, ...] = (
    REPO_ROOT / "README.md",
    REPO_ROOT / "docs" / "manuscript" / "main.tex",
    REPO_ROOT / "docs" / "edison" / "analysis-v2-corrected-gondola.md",
    REPO_ROOT / "cad" / "README.md",
    REPO_ROOT / "cad" / "excavator.py",
    REPO_ROOT / "cad" / "dfm.py",
)

# Common framing for every iteration of the analysis feedback cycle. The
# gantry-only constraint (no second axis on the bucket) is the load-bearing
# requirement from PR comment 4166621470.
ANALYSIS_PREAMBLE = """\
You are reviewing the powder-excavator project, an open-source bulk powder
dispenser intended to feed a downstream precision gravimetric dispenser inside
a self-driving lab. **Hard constraint:** the entire dispensing motion must be
achievable on a 3-axis gantry (X, Y, Z) -- *no* second actuator on the bucket
itself. All trough rotation / scoop opening / closing must come from passive
mechanical interaction with fixed external features (cam ramps, routed slots,
fixed posts, compliant flexures, etc.) driven by gantry motion alone.

Target powders are dozens of microns in diameter, often cohesive,
hygroscopic, or triboelectrically charged. Manufacturing target is FDM 3D
printing in PETG / nylon / ESD-safe filament with stock dowel-pin pivots.

The full design context (README, LaTeX manuscript, prior Edison analyses,
and the CadQuery parametric model with its DFM checks) is embedded inline
below as fenced code blocks.
"""

ITERATION_PROMPTS = {
    1: """\
**Iteration 1 of 3 -- gantry-only baseline review.**

Given the gantry-only constraint above, please:

1. Identify every place in the current design where the mechanism implicitly
   assumes a second actuator on the bucket and propose a gantry-only
   substitute (cam, slot, compliant bistable mechanism, OT-2-style tip-eject,
   pipette-displacement-driven suction, etc.).
2. Compare the smooth-cam-ramp variant (Panel D) and the routed-slot variant
   (Panel E) for: kinematic determinism, bidirectional return, robustness to
   powder build-up on the cam/slot, and additive-manufacturing complexity.
3. Critique the bimodal scoop suggestion from PR comment 3134394694
   ("scoop position" vs "hold/don't leak position", potentially actuated by
   OT-2 tip-eject style drop or pipette-suction). Is a single passive
   bistable flexure (compliant mechanism) achievable on a 3-axis gantry, or
   does it always require a second axis?
4. Propose three concrete experimental measurements (mass CV, dose-recovery,
   bridging frequency) that would discriminate between the cam-ramp,
   pin-slot, and bistable variants.
5. Recommend an open, pip-installable feedback-loop toolchain that hooks the
   CadQuery parametric model into a measure-and-re-design loop on a Jubilee
   or OpenTrons rig.
""",
    2: """\
**Iteration 2 of 3 -- refinement based on Iteration 1.**

Building on Iteration 1's gantry-only critique (whose verbatim answer will
be embedded below as `analysis-iter1.md`):

1. Pick the single strongest gantry-only actuation strategy from Iteration 1
   and design it in detail: dimensions, materials, tolerances, expected dose
   range, expected CV, failure modes.
2. Identify the 2-3 highest-risk geometric parameters (e.g. bumper chamfer
   angle, slot waypoint spacing, flexure thickness) and propose a
   one-factor-at-a-time sweep that the CadQuery model + Bayesian optimisation
   loop could run.
3. Specify the closed-loop digital-twin instrumentation needed (load cell,
   camera, encoder feedback) and how each measurement would feed back into
   the next CadQuery parameter update.
""",
    3: """\
**Iteration 3 of 3 -- concrete decision and build plan.**

Building on Iterations 1 and 2 (whose verbatim answers will be embedded
below as `analysis-iter1.md` and `analysis-iter2.md`):

1. Recommend a single design to take to first prototype, with a justification
   that explicitly addresses why each rejected variant was rejected.
2. Provide a 5-step build-and-test plan for that prototype (print, assemble,
   instrument, calibrate, characterise) with go/no-go criteria at each step.
3. List the additions / changes that should be made to the manuscript
   (`docs/manuscript/main.tex`) to reflect the chosen design and to defend
   the gantry-only-no-second-axis claim.
4. List the parameters in `cad/excavator.py::ExcavatorParams` that need to
   change to match the chosen design.
""",
}

CAD_LITREVIEW_QUERY = """\
We are designing the actuation and feedback loop for an open-hardware powder
dispenser ("powder-excavator") that must run on a 3-axis gantry with no
second axis on the bucket. The bucket's tilt schedule is therefore programmed
purely by passive mechanical interaction with fixed external features
(cam ramps, routed slots, compliant flexures, OT-2-style tip-ejection,
pipette-displacement-driven suction, etc.) driven by gantry motion alone.

Please synthesise the state of the art across two linked topics, with a
preference for **open and pip-installable** tools (we are using CadQuery as
the parametric authoring layer) and citing peer-reviewed work where possible:

1. **Generative / computational CAD and systems design for mechanical
   hardware**: parametric / algorithmic CAD ecosystems (CadQuery, build123d,
   OpenSCAD, Rhino + Grasshopper + Rhino.Inside, Onshape FeatureScript, Zoo
   Design Studio / KCL); generative / AI-assisted geometry (nTop, Fusion
   Generative Design, DeepCAD, Text2CAD / CAD-LLM, BrepGen, CAD-Recode,
   Shap-E / TRELLIS); systems-design / requirements-driven approaches (SysML
   v2, OpenMDAO, Bayesian-optimisation design loops); and automated DFM /
   printability checks (slicer-side, DFMPro, Castor). Comparative table where
   tools fight in the same niche.

2. **Automated feedback loops and digital-twin-style evaluation for
   mechanical hardware prototypes**: twin maturity (Kritzinger / Tao /
   Grieves), AM-specific twins (NIST AM-Bench, Eclipse Ditto, ROS2 + Gazebo /
   Ignition), closed-loop design->print->measure->re-design pipelines
   (PowderBot, A-Lab, Ada, Bayesian-optimisation of printed parts), in-situ
   AM monitoring (melt-pool, OCT, PrintWatch / Spaghetti Detective), CV-based
   metrology, and what a credible end-to-end loop would look like for the
   powder-excavator specifically (CadQuery -> print -> Jubilee / OpenTrons
   rig + balance + vision -> Bayesian optimiser -> next params).

End with a concrete recommended toolchain (one pick each for: parametric CAD
authoring, generative exploration, DFM check, prototype-feedback loop, and
the wire-it-together path) for an open-source, pip-installable, no-license-
fee build.
"""


def make_client() -> FutureHouseClient:
    """Build a FutureHouseClient pinned to the Edison Scientific endpoint."""
    api_key = os.environ.get("EDISON_API_KEY")
    if not api_key:
        sys.exit("EDISON_API_KEY env var is not set")
    return FutureHouseClient(service_uri=EDISON_SERVICE_URI, api_key=api_key)


def _fence_for(content: str) -> str:
    """Return a backtick fence longer than any run of backticks in ``content``.

    Markdown fenced code blocks terminate on the first line that starts
    with a fence of equal or greater length than the opener, so to safely
    embed arbitrary content (including content that itself contains
    triple-backtick fences) we pick a fence one longer than the longest
    backtick run in the content (with a floor of 3).
    """
    longest = 0
    run = 0
    for ch in content:
        if ch == "`":
            run += 1
            if run > longest:
                longest = run
        else:
            run = 0
    return "`" * max(3, longest + 1)


def _embed_context() -> str:
    """Return the design-context files joined as fenced text blocks."""
    parts: list[str] = []
    for fp in CONTEXT_TEXT_FILES:
        if not fp.exists():
            continue
        rel = fp.relative_to(REPO_ROOT)
        ext = fp.suffix.lstrip(".") or "text"
        # Read with explicit UTF-8 (avoid locale-dependent decode errors)
        # and pick a fence longer than any backtick run in the file so
        # embedded ``` fences (e.g. inside README.md) can't prematurely
        # terminate the wrapper.
        text = fp.read_text(encoding="utf-8")
        fence = _fence_for(text)
        parts.append(f"\n=== file: {rel} ===\n{fence}{ext}\n{text}\n{fence}")
    return "\n".join(parts)


def submit_analysis(iteration: int) -> str:
    """Submit one iteration of the analysis feedback cycle."""
    if iteration not in ITERATION_PROMPTS:
        sys.exit(f"iteration must be one of {sorted(ITERATION_PROMPTS)}")
    client = make_client()
    query = (
        ANALYSIS_PREAMBLE
        + "\n"
        + ITERATION_PROMPTS[iteration]
        + "\n\n--- Embedded repository context follows ---\n"
        + _embed_context()
    )
    task = client.create_task(TaskRequest(name=JOB_ANALYSIS, query=query))
    print(f"submitted analysis iter {iteration}: task_id={task}")
    return str(task)


# File globs (relative to REPO_ROOT) that we ship to Edison as an *uploaded
# directory* alongside the inline-embedded text context. This is the path used
# by ``submit-analysis-with-files`` and is meant to give the analysis job the
# full design state: parametric source, generated CAD (STEP/STL/manifest),
# rendered figures (SVG/PNG/GIF), the LaTeX manuscript + bib, every prior
# Edison analysis, the brainstorming doc, and the original hand sketches.
UPLOAD_GLOBS: tuple[str, ...] = (
    "README.md",
    "powder-excavator-sketch.jpg",
    "PXL_20260423_231729467.jpg",
    "cad/*.py",
    "cad/README.md",
    "cad/tests/*.py",
    "cad/build/*.step",
    "cad/build/*.stl",
    "cad/build/manifest.json",
    "docs/figures/*.svg",
    "docs/figures/*.png",
    "docs/figures/*.gif",
    "docs/figures/cad/*.svg",
    "docs/figures/cad/*.png",
    "docs/manuscript/main.tex",
    "docs/manuscript/references.bib",
    "docs/edison/*.md",
    "docs/brainstorming-and-literature.md",
    "scripts/edison_submit.py",
)

# Question we ask Edison once the bundle is uploaded.
ANALYSIS_WITH_FILES_QUERY = """\
You are reviewing the **current state** of the powder-excavator project,
an open-hardware bulk powder dispenser intended to feed a downstream
precision gravimetric dispenser inside a self-driving lab.

**Hard constraint:** the entire dispensing motion must be achievable on a
3-axis gantry (X, Y, Z) -- *no* second actuator on the bucket itself. All
trough rotation / scoop opening / closing must come from passive mechanical
interaction with fixed external features (cam ramps, routed slots, fixed
posts, compliant flexures, etc.) driven by gantry motion alone.

The full design state has been uploaded to the job bucket and includes:

- ``README.md``, ``powder-excavator-sketch.jpg``, ``PXL_*.jpg``: design
  intent and the original hand sketch.
- ``cad/excavator.py`` + ``cad/build.py`` + ``cad/dfm.py`` + ``cad/render.py``:
  the CadQuery parametric source, exporter, DFM/feedback checks, and figure
  renderer.
- ``cad/tests/*.py``: the unit + regression tests for the CAD model.
- ``cad/build/*.step``, ``cad/build/*.stl``, ``cad/build/manifest.json``:
  STEP + STL exports of every part and the assembly, plus the parameter
  snapshot used to build them.
- ``docs/figures/*.svg`` + ``*.png`` + ``mechanism.gif``: schematic panels
  A-E of the mechanism.
- ``docs/figures/cad/*.svg`` + ``*.png``: hidden-line renders of the
  parametric model (per-part + assembly + 3 assembly views).
- ``docs/manuscript/main.tex`` + ``references.bib``: the manuscript draft.
- ``docs/edison/*.md``: every prior Edison analysis (analysis-v1 through
  analysis-v3) and the literature-review responses.
- ``docs/brainstorming-and-literature.md``: ideation + lit notes.
- ``scripts/edison_submit.py``: the script being used to submit this query.

Please review the current state end-to-end and provide:

1. A geometry / kinematics / statics critique of the parametric CAD as it
   currently stands (do the dimensions in ``ExcavatorParams``, the pivot
   placement, the cam-ramp rise vs. lever arc, the slot-board path, and
   the strike-off bar geometry actually compose into a working
   gantry-only powder-excavation cycle?). Cross-reference the rendered
   PNGs/SVGs against the schematic panels and call out any place the CAD
   and the schematic disagree.
2. Specific, parameter-level edits to ``ExcavatorParams`` you would make
   next, with justification (cite the figures or STEP/STL files when
   relevant).
3. A ranked list of the 3 highest-impact remaining risks to a successful
   first physical prototype, given the gantry-only constraint, and the
   cheapest experiment to retire each one.
4. A check on whether the DFM rules in ``cad/dfm.py`` cover the failure
   modes you would actually expect on a printed PETG / nylon / ESD-safe
   build -- what's missing? what's over-conservative?
5. Concrete next-iteration recommendations for: (a) the manuscript text,
   (b) the schematic figures (panels A-E + mechanism.gif), (c) the
   parametric model, and (d) the test suite.

Reply in the structure above with section headings 1-5.
"""


def _stage_upload_dir() -> Path:
    """Materialise the upload bundle in a temp directory.

    Resolves :data:`UPLOAD_GLOBS` relative to :data:`REPO_ROOT` and copies
    every match into a fresh temp directory, preserving the relative path
    layout so the analysis job sees a familiar structure. Returns the temp
    directory's path; callers are responsible for cleanup (the analysis
    job uploads the directory before we delete it).
    """
    staged = Path(tempfile.mkdtemp(prefix="excavator-edison-upload-"))
    for pattern in UPLOAD_GLOBS:
        for match in REPO_ROOT.glob(pattern):
            if not match.is_file():
                continue
            rel = match.relative_to(REPO_ROOT)
            dest = staged / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(match, dest)
    return staged


# File suffixes we treat as "text" and embed inline as fenced blocks. Anything
# else (PNG / JPG / GIF / STL / STEP) is referenced by a public GitHub raw URL
# on the current branch instead, because the Edison cluster's chunked upload
# endpoint returns 404 (see comment at the top of this file).
TEXT_SUFFIXES = frozenset({
    ".md", ".py", ".tex", ".bib", ".json", ".svg", ".txt", ".cfg", ".toml",
})

# GitHub repo coordinates for raw URLs. Hardcoded because the script ships
# only with this single repo.
GH_OWNER = "vertical-cloud-lab"
GH_REPO = "powder-excavator"


def _git_branch() -> str:
    """Best-effort current branch name for raw URLs (fallback to ``main``)."""
    try:
        import subprocess
        out = subprocess.check_output(
            ["git", "-C", str(REPO_ROOT), "rev-parse", "--abbrev-ref", "HEAD"],
            text=True,
        ).strip()
        return out or "main"
    except Exception:
        return "main"


def _embed_full_bundle() -> str:
    """Inline-embed every file from :data:`UPLOAD_GLOBS` for the analysis job.

    Text files are embedded as fenced code blocks (with a fence longer than
    any backtick run inside the file, so embedded ``` markers can't break
    out). Binary files are listed under "Binary asset references" with
    GitHub raw URLs on the current branch. This is the inline fallback used
    when the chunked upload endpoint is unavailable.
    """
    branch = _git_branch()
    text_parts: list[str] = []
    binary_lines: list[str] = []
    seen: set[Path] = set()
    for pattern in UPLOAD_GLOBS:
        for match in sorted(REPO_ROOT.glob(pattern)):
            if not match.is_file() or match in seen:
                continue
            seen.add(match)
            rel = match.relative_to(REPO_ROOT)
            if match.suffix.lower() in TEXT_SUFFIXES:
                ext = match.suffix.lstrip(".") or "text"
                try:
                    text = match.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    binary_lines.append(
                        f"- `{rel}` (binary, raw URL: "
                        f"https://github.com/{GH_OWNER}/{GH_REPO}/raw/{branch}/{rel})"
                    )
                    continue
                fence = _fence_for(text)
                text_parts.append(
                    f"\n=== file: {rel} ===\n{fence}{ext}\n{text}\n{fence}"
                )
            else:
                binary_lines.append(
                    f"- `{rel}` (raw URL: "
                    f"https://github.com/{GH_OWNER}/{GH_REPO}/raw/{branch}/{rel})"
                )
    bundle = "\n".join(text_parts)
    if binary_lines:
        bundle += (
            "\n\n=== Binary asset references (fetch from GitHub raw URL) ===\n"
            + "\n".join(binary_lines)
        )
    return bundle


def submit_analysis_with_files() -> str:
    """Submit a fresh analysis task bundling the full design state.

    Tries chunked upload first via ``client.upload_file`` (this is the
    "proper" path and is what the Edison docs describe). If the cluster
    returns the known 404 on ``/upload-chunk``, falls back to embedding
    every text-form file inline and listing binary assets (PNG/JPG/GIF/
    STL/STEP) by public GitHub raw URL on the current branch. Either way
    we end up with a single analysis task referencing the full design
    state; this command does **not** poll for results.
    """
    client = make_client()
    upload_id: str | None = None
    staged = _stage_upload_dir()
    n_files = sum(1 for _ in staged.rglob("*") if _.is_file())
    print(f"staged {n_files} files in {staged} for upload")
    try:
        try:
            upload_id = client.upload_file(
                job_name=JOB_ANALYSIS,
                file_path=str(staged),
            )
            print(f"upload complete: upload_id={upload_id}")
        except Exception as exc:  # noqa: BLE001 -- intentional broad catch + fallback
            print(
                f"chunked upload unavailable ({type(exc).__name__}); "
                "falling back to inline embedding + GitHub raw URLs",
                file=sys.stderr,
            )
    finally:
        shutil.rmtree(staged, ignore_errors=True)

    if upload_id is None:
        query = (
            ANALYSIS_WITH_FILES_QUERY
            + "\n\n--- Embedded repository bundle (inline fallback because the "
            "Edison chunked-upload endpoint is unavailable on this cluster) "
            "---\n"
            + _embed_full_bundle()
        )
        task = client.create_task(
            TaskRequest(name=JOB_ANALYSIS, query=query)
        )
        print(f"submitted analysis-with-files (inline): task_id={task}")
    else:
        task = client.create_task(
            TaskRequest(
                name=JOB_ANALYSIS,
                query=ANALYSIS_WITH_FILES_QUERY,
                runtime_config=RuntimeConfig(upload_id=upload_id),
            )
        )
        print(
            f"submitted analysis-with-files: task_id={task} upload_id={upload_id}"
        )
    return str(task)


def submit_cad_litreview() -> str:
    """Resubmit the generative-CAD literature-deep query at the Edison
    endpoint (the previous submission via FutureHouse was cancelled)."""
    client = make_client()
    task = client.create_task(
        TaskRequest(name=JOB_LITERATURE_HIGH, query=CAD_LITREVIEW_QUERY)
    )
    print(f"submitted CAD lit-review (paperqa3-high): task_id={task}")
    return str(task)


def poll(task_id: str) -> None:
    """Print the status and (if available) the formatted answer for a task."""
    client = make_client()
    resp = client.get_task(task_id)
    print(f"task_id : {task_id}")
    print(f"status  : {getattr(resp, 'status', '?')}")
    print(f"job     : {getattr(resp, 'job_name', '?')}")
    answer = getattr(resp, "formatted_answer", None) or getattr(resp, "answer", None)
    if answer:
        print("\n--- answer ---\n")
        print(answer)
    else:
        print("(no answer body yet)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("submit-cad-litreview")
    sub.add_parser("submit-analysis-with-files")
    p_an = sub.add_parser("submit-analysis")
    p_an.add_argument("iteration", type=int, choices=sorted(ITERATION_PROMPTS))
    p_poll = sub.add_parser("poll")
    p_poll.add_argument("task_id")
    args = parser.parse_args()
    if args.cmd == "submit-cad-litreview":
        submit_cad_litreview()
    elif args.cmd == "submit-analysis-with-files":
        submit_analysis_with_files()
    elif args.cmd == "submit-analysis":
        submit_analysis(args.iteration)
    elif args.cmd == "poll":
        poll(args.task_id)


if __name__ == "__main__":
    main()
