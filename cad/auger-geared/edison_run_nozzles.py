"""Edison Scientific LITERATURE_HIGH runner for the nozzle-type selection ask.

Background
----------
@sgbaird asked (PR #49, comment 4568945170) for a high-effort Edison Scientific
literature query focused specifically on the FOUR candidate nozzle / dispensing-
end designs for the metering auger -- the ones @swcharles enumerated in
https://github.com/vertical-cloud-lab/powder-doser/issues/48#issuecomment-4513155870:

    1) direct cutoff of the screw to a large open funnel leading to the exit
    2) continue the screw until just before the exit (small funnel), shaft
       diameter kept constant (not shrunk)
    3) direct cutoff of the screw above a central shaft that tapers to a point
    4) combine (2) and (3): continue the screw as the central shaft tapers down

The previous Edison query (`edison_run.py`, task 5afb6d0d-...) covered the
broad geared-auger design problem but did NOT make a nozzle-by-nozzle
recommendation.  This runner asks the focused question:

    "Which of the four dispensing-end geometries is likely to meter best -- is
     there a better alternative not in the list, or might the choice not matter
     much?  Ground the answer in the literature and in the behaviour of ALLOY
     and MASTER-ALLOY metal powders relevant to our target workflows."

Artifacts are written next to this script, following the repo convention
(<key>.task.json + .answer.md + .references.md):

  cad/auger-geared/edison_artifacts/
    nozzle-selection.task.json     -- submitted task envelope (queue id, query)
    nozzle-selection.answer.md     -- final formatted answer (Edison markdown)
    nozzle-selection.references.md -- bibliography pulled from the response

Re-run / fetch an already-queued task with:

    python3 edison_run_nozzles.py --fetch <uuid>
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
KEY = "nozzle-selection"

# Prompt: re-states the four nozzle designs from issue #48 comment-4513155870
# verbatim, gives the shared auger geometry, names the target media (alloy and
# master-alloy metal powders), and asks for a literature-grounded
# recommendation among the four (plus any better alternative, or a note that it
# does not matter much).  Kept in source so future readers can trace exactly
# what was asked.
QUERY = """\
We are designing a 3D-printed (FDM) metering auger for a low-cost benchtop
powder dispenser ("powder-doser"). The auger is a vertical hollow cylinder
(OD 25 mm, ID 21 mm) with an internal single-start Archimedean screw (central
shaft Ø8 mm, 10 mm-pitch helical fin, 2 mm fin thickness) that turns inside the
tube and pushes powder down to a conical exit funnel ending in a Ø3 mm exit
hole. The target dispensed media are ALLOY and MASTER-ALLOY METAL POWDERS
(e.g. gas- or water-atomised metal and intermetallic powders, including
master-alloy additions) used in combinatorial / formulation workflows, where we
need accurate, repeatable sub-gram (ideally tens-of-milligram) doses. These
powders span a range of particle size distributions (roughly d50 ~ 10-150 um),
densities (often 4-9 g/cm^3), morphologies (spherical atomised vs irregular),
and flowabilities (free-flowing to moderately cohesive, Hausner ratio ~ 1.1 to
~ 1.5), and some are abrasive.

We have prototyped FOUR candidate DISPENSING-END ("nozzle") geometries that
differ only in how the screw and central shaft terminate near the Ø3 mm exit;
everything above (tube, loading cap, helix pitch/thickness) is identical. The
four designs, exactly as enumerated by our team, are:

  1) A direct cutoff of the screw to a large open funnel leading to the nozzle
     exit. (The helical flight stops well above the exit; below it is just an
     open conical funnel down to the Ø3 mm hole, with no screw or shaft in the
     funnel region.)

  2) Continuing the screw until just before the nozzle exit (with a small
     funnel) WITHOUT shrinking the middle shaft. (The full-diameter Ø8 mm shaft
     and the flight run almost all the way down to a short funnel just above the
     exit hole.)

  3) A direct cutoff of the screw, positioned above a region where the central
     shaft shrinks (tapers) to a near-point at the exit. (The flight stops
     above the taper; the shaft then necks down to a tip, leaving an annular
     gap that widens toward the exit, but with no flight in the taper region.)

  4) Combining (2) and (3): continuing the screw as the middle shaft tapers
     down as well, so the flight follows the shrinking shaft down toward the
     exit.

Please conduct a thorough, high-effort literature review and then give a
reasoned recommendation. Specifically:

(A) Of the four geometries above, which is most likely to give the best
    metering performance -- highest dose accuracy and repeatability, lowest
    dribble / after-flow, least susceptibility to bridging, rat-holing, arching,
    or flooding (uncontrolled gravity flow) -- for the ALLOY / MASTER-ALLOY
    metal powders described? Rank or group the four if a single winner is not
    defensible, and explain the mechanism (e.g. how the screw-to-exit transition
    governs choke feeding vs flood feeding, how a tapered vs constant shaft and
    the annular discharge area affect the powder column and shear zone, and how
    each interacts with the dense, sometimes abrasive metal powder).

(B) Is there an ALTERNATIVE dispensing-end design, not in our list of four, that
    the literature suggests would meter dense metal/alloy powders better? For
    example: a choke / flood-feed transition or step change in flight depth near
    the discharge, a decreasing-pitch or tapered-flight ("compression") screw, a
    short discharge tube / land of a particular length-to-diameter ratio, an
    anti-dribble or shut-off feature, a tapered vs straight nozzle bore, an
    auger tip that protrudes into or stops short of the orifice, or other
    screw/loss-in-weight feeder discharge designs from the powder-handling,
    pharmaceutical / nutraceutical micro-feeder, additive-manufacturing
    metal-powder-dosing, or combinatorial-materials literature. Give concrete
    geometric parameters (pitch-to-diameter ratios, flight clearance, orifice
    and discharge-tube L/D, taper angles) where the literature provides them.

(C) Conversely, is it plausible that the choice among these four matters little
    for our regime -- i.e., that, for these powders and a Ø3 mm exit at low
    fill, dose accuracy is dominated by other factors (screw speed control,
    step resolution, percussive de-bridging / tapping, vibration agitation,
    powder conditioning / flow aids, ambient humidity, gravimetric closed-loop
    feedback) rather than by the exit geometry? If so, say so explicitly and
    cite the evidence, and identify which non-geometry factors dominate.

(D) What does the literature say specifically about screw / auger feeding and
    dosing of METAL and ALLOY powders (as opposed to pharmaceutical excipients
    or food powders) -- abrasion / wear of the screw and bore (relevant since
    ours is FDM plastic), the effect of high bulk density on torque and flow,
    segregation of multi-component master-alloy blends during augering, and any
    documented best practices or failure modes for the discharge / nozzle end.

Where the literature is sparse or absent for any of the above, please note that
explicitly and point to the most relevant adjacent prior art (e.g. volumetric
and loss-in-weight screw feeders for fine chemicals, lab-scale powder
micro-dispensers, metal-AM powder dosing, vibratory trickle chargers) along
with their key discharge-end design parameters.
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
                   "see citation footnotes inside `nozzle-selection.answer.md`)_")
        + ("\n" if refs and not refs.endswith("\n") else "\n")
    )


def main() -> int:
    if "--fetch" in sys.argv:
        uuid = sys.argv[sys.argv.index("--fetch") + 1]
        print(f"[edison] fetching existing task {uuid}", flush=True)
    else:
        uuid = submit()
        print(f"[edison] submitted task uuid={uuid}", flush=True)
        ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
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
