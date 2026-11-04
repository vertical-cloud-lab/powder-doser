"""Edison Scientific LITERATURE_HIGH runner for the geared-auger design ask.

Background
----------
@sgbaird asked (PR #51, comment 4546247154) for a high-effort Edison Scientific
literature query about the design problem stated in
https://github.com/vertical-cloud-lab/powder-doser/issues/48#issuecomment-4513155870
(the parent ask that produced this PR's geared-auger + NEMA-11 pinion design).

This runner submits a LITERATURE_HIGH (`job-futurehouse-paperqa3-high`) crow with
a verbatim restatement of the design problem and the specific engineering
questions that the v1..v3 review cycle surfaced (annular gear-band integration,
NEMA-11 / auger collision avoidance, helix-presence in a printable geared
auger).  Artifacts are written next to this script as:

  cad/auger-geared/edison_artifacts/
    geared-auger.task.json     -- the submitted task envelope (queue id, query)
    geared-auger.answer.md     -- final formatted answer (Edison markdown)
    geared-auger.references.md -- bibliography pulled from the response

Following the convention in the repo memory ("Edison Scientific LITERATURE_HIGH
query artifacts ... live as <key>.task.json + .answer.md + .references.md,
dispatched by edison_run*.py runners that embed prompts verbatim").
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

from edison_client import EdisonClient, JobNames

EDISON_API_KEY = os.environ["EDISON_API_KEY"]
ENDPOINT = "https://api.platform.edisonscientific.com"

ARTIFACT_DIR = Path(__file__).parent / "edison_artifacts"
KEY = "geared-auger"

# Prompt: re-states the design problem from issue #48 comment-4513155870
# verbatim, then layers on the specific engineering questions surfaced by the
# v1..v3 review cycle in PR #51.  Kept here in source so future readers can
# trace exactly what was asked.
QUERY = """\
We are designing a 3D-printed metering auger for a low-cost benchtop powder
dispenser ("powder-doser"). The auger is a vertical hollow cylinder (OD 25 mm,
ID 21 mm, length 250 mm) with an internal Archimedean screw (Ø8 mm central
shaft, 10 mm-pitch single-start helical fin, 2 mm fin thickness) and a conical
exit funnel + Ø3 mm exit hole at the bottom. The original design (PR #16) is
driven directly by an M3 spindle that screws into a boss above a top loading
cap.

The v2 ask (issue #48, comment 4513155870) was to add an EXTERNAL spur-gear
band wrapped around the auger about one-third of the way from the dispensing
end, so the auger can be rotated by a NEMA 11 stepper motor mounted alongside
the auger (parallel-axis offset drive). The external gear-band must not
interfere with the internal Archimedean screw, the bore, the exit funnel, or
the top cap loading slots. The print-and-test cycle produced two specific
failure modes that motivate this query:

1. (v1) Building the gear band as `linear_extrude(spur_gear_2d(...))` with
   spur_gear_2d returning a filled root-circle disc sealed the auger bore at
   the gear-band's axial slice, turning a hollow metering tube into a closed
   cup. v2 fixed this by making spur_gear_2d optionally return an annular
   2-D shape (root-circle minus bore circle), so the bore stays open through
   the gear's axial slice.
2. (v1) Choosing a Z_p/Z_g pair that minimised gear-band radius produced a
   centre distance C = 21 mm at module m = 1 mm. With the auger OR = 12.5 mm
   and the NEMA 11 frame extending 14.1 mm from its shaft axis, the motor
   body would have intersected the auger tube by 5.6 mm. v2 fixed this by
   picking Z_p = 16, Z_g = 48, m = 1.0 -> C = 32 mm, leaving a 5.4 mm radial
   air gap between the auger OD and the motor body face.
3. (v2) An over-aggressive copy of the PR #16 v5 file (which had previously
   removed the central shaft + helix to avoid stringing during a single H2D
   FDM test print) left the geared auger with an empty bore and no
   Archimedean lift; v3 re-introduced the v4.1-era shaft + helix sweep as a
   single linear_extrude with proportional twist so the helical surface is
   continuous from the funnel mouth through the gear-band z-range up to the
   underside of the top cap.

Please conduct a thorough literature review covering, with explicit citations:

(a) Design and analysis of plastic 3D-printed spur gears for low-torque,
    low-RPM intermittent service (e.g. PLA / PETG, module 0.5-2 mm, FDM 0.4
    mm nozzle). What tooth-form choices (full-depth vs stub, profile-shift,
    addendum modification, fillet radius), pressure angles, face widths, and
    backlash budgets does the literature recommend for printed gears in this
    size class? How does the literature characterise wear and dimensional
    drift versus injection-moulded counterparts?

(b) Parallel-axis offset drive of vertical metering augers / screw feeders.
    What centre-distance, gear-ratio, and reduction-stage choices appear in
    the powder-handling, pharmaceutical-feeder, and additive-manufacturing-
    powder-dosing literature for the 0.01-10 g/s dosing regime? Are there
    published failure modes specific to driving a screw feeder through an
    external gear band (e.g. gear-induced vibration coupling into bridging
    or rat-holing of cohesive powders, eccentric loading on the screw
    spindle bearing)?

(c) Single-flight Archimedean screw feeders for cohesive powders (xanthan
    gum, flour, fine ceramic / metal powders). What design rules exist for
    pitch, fin thickness, flight clearance, and shaft diameter as a function
    of particle d50 and Hausner ratio? What is the published evidence on the
    relative metering accuracy of (i) screw rotation alone vs (ii) screw
    rotation + percussive de-bridging (solenoid tap) vs (iii) screw +
    vibration-motor agitation, for sub-gram dosing accuracy?

(d) NEMA 11 (28 mm frame) stepper motor selection for benchtop metering /
    autotrickler-class powder dispensers. What torque, microstepping, and
    closed-loop strategies appear in the published literature for accurate
    sub-gram metering, and what gear reductions are typical for the 28-32 mm
    stepper class driving a vertical screw feeder?

(e) Print-orientation and slicer-setting recommendations for a tall (>= 180
    mm) printed hollow auger with an internal helical fin printed without
    inner-fin support material -- specifically, the trade-off between
    printing the auger vertically (long unsupported helical bridges at the
    fin's inner edge) vs printing in segments and bonding/threading them.

Where the literature is sparse, please note that explicitly and identify
relevant adjacent prior art (vending dispensers, salt cellars, lab-scale
mass-flow controllers, etc.) along with their key design parameters.
"""


def submit() -> str:
    """Submit the LITERATURE_HIGH task; return the task uuid."""
    client = EdisonClient(api_key=EDISON_API_KEY)
    task_data = {
        "name": JobNames.LITERATURE_HIGH,
        "query": QUERY,
    }
    uuid = client.create_task(task_data)
    return uuid


def wait_for_completion(uuid: str, *, first_wait_s: int = 15 * 60,
                        poll_s: int = 5 * 60, max_wait_s: int = 90 * 60) -> dict:
    """Block until the task reports a terminal status; return final dump."""
    client = EdisonClient(api_key=EDISON_API_KEY)

    print(f"[edison] sleeping {first_wait_s}s before first poll", flush=True)
    time.sleep(first_wait_s)

    waited = first_wait_s
    while waited <= max_wait_s:
        r = client.get_task(uuid)
        dump = r.model_dump() if hasattr(r, "model_dump") else dict(r)
        status = str(dump.get("status", "")).lower()
        print(f"[edison] t+{waited}s status={status!r}", flush=True)
        if status in {"success", "completed", "fail", "failed", "cancelled",
                       "error", "crashed"}:
            return dump
        time.sleep(poll_s)
        waited += poll_s
    raise TimeoutError(f"task {uuid} did not complete within {max_wait_s}s")


def persist(uuid: str, dump: dict) -> None:
    """Write task envelope + answer.md + references.md."""
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

    # Task envelope (queue uuid + the verbatim query, no large blobs)
    envelope = {
        "uuid": uuid,
        "job_name": str(JobNames.LITERATURE_HIGH.value),
        "endpoint": ENDPOINT,
        "status": dump.get("status"),
        "query": QUERY,
    }
    (ARTIFACT_DIR / f"{KEY}.task.json").write_text(
        json.dumps(envelope, indent=2) + "\n"
    )

    # Formatted answer.  PQATaskResponse exposes formatted_answer (markdown);
    # fall back to "answer" if absent.
    answer = dump.get("formatted_answer") or dump.get("answer") or ""
    if not isinstance(answer, str):
        answer = json.dumps(answer, indent=2)
    (ARTIFACT_DIR / f"{KEY}.answer.md").write_text(
        f"<!-- Edison task {uuid} via {JobNames.LITERATURE_HIGH.value} -->\n\n"
        + answer
        + ("\n" if not answer.endswith("\n") else "")
    )

    # References / bibliography.  paperqa3 returns these under several keys
    # depending on version; try a few.
    refs = (
        dump.get("formatted_references")
        or dump.get("references")
        or dump.get("bibliography")
        or ""
    )
    if not isinstance(refs, str):
        refs = json.dumps(refs, indent=2)
    (ARTIFACT_DIR / f"{KEY}.references.md").write_text(
        f"<!-- Edison task {uuid} references -->\n\n"
        + (refs or "_(no separate references field returned by the server; "
                   "see citation footnotes inside `geared-auger.answer.md`)_")
        + ("\n" if refs and not refs.endswith("\n") else "\n")
    )


def main() -> int:
    if "--fetch" in sys.argv:
        uuid = sys.argv[sys.argv.index("--fetch") + 1]
        print(f"[edison] fetching existing task {uuid}", flush=True)
    else:
        uuid = submit()
        print(f"[edison] submitted task uuid={uuid}", flush=True)
        (ARTIFACT_DIR / f"{KEY}.task.json").parent.mkdir(parents=True, exist_ok=True)
        # Write a stub immediately so the uuid is recorded even if we crash.
        (ARTIFACT_DIR / f"{KEY}.task.json").write_text(
            json.dumps({"uuid": uuid, "status": "submitted",
                        "job_name": str(JobNames.LITERATURE_HIGH.value),
                        "query": QUERY}, indent=2) + "\n"
        )

    dump = wait_for_completion(uuid)
    persist(uuid, dump)
    print(f"[edison] done; status={dump.get('status')!r}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
