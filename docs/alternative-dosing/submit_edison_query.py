"""Submit a single Edison Scientific feedback query for the alternative
powder-dosing concepts in ``brainstorm.md`` (issue #12).

Per the issue, this script intentionally **does not wait** for the answer;
it submits, records the task id in ``edison_query.json``, and exits. The
answer is fetched in a subsequent session.

The Edison API key is read from the ``EDISON_API_KEY`` environment
variable and never echoed.
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
QUERY_TAG = "alternative-powder-dosing-concepts-feedback"

QUERY = """We are designing a small open-source powder dispensing
attachment for a Genmitsu 3018-Pro V2 desktop CNC gantry (GRBL, ~300 mm
x 180 mm x 45 mm work envelope, ~3 kg payload on the spindle clamp).
Constraints: must be buildable in roughly one workshop day, 3D printing
is fine, and adding active electromechanical components (motors,
solenoids, microcontrollers) is allowed but each one is treated as a
schedule risk. Target dose range is microgram to low-milligram on
typically cohesive (sub-100-um) inorganic and organic powders.

We have already explored two designs in detail and are looking for
feedback on **alternatives** to those two:

  Design 1 (already prototyped, see PR #2 of vertical-cloud-lab/powder-
  excavator): a 3D-printed semicircular scoop / ladle with side pins
  that catch a fixed ledge on the bed; the pins pivot the scoop and
  dump powder into a vial. Dose control via dip depth (open-loop) or
  closed-loop gravimetric.

  Design 2 (already prototyped, see PR #5 of the same repo): a bistable
  / bimodal compliant trough — a snap-through flexure that holds powder
  in one stable state and dumps it via snap-through into the other.

Please critique the following eight alternative concepts (full
descriptions in our brainstorm doc), and rank them for one-day-build
feasibility on the 3018-Pro V2, expected achievable dose floor and RSD
on cohesive powders, and risk of failure. Where vendor or academic
analogues exist (e.g. Mettler Toledo Quantos, Chemspeed SWILE / GDU-Pfd,
Coperion K-Tron, Jiang et al. 2023 dual-arm spatula, Berkeley A-Lab),
please cite them and contrast our concept with the published behaviour:

  A. Tap-driven sieve cup, where the gantry itself supplies the tap
     impulse by pecking the cup against a fixed anvil on the bed
     (no motor; sieve only releases on tap, exploiting the cohesive
     regime that defeats hopper feeders).

  B. Pez-style positive-displacement chamber strip — a printed strip
     of fixed-volume chambers, pre-loaded by strike-off, advanced one
     pitch per dispense by a fixed pawl on the bed and discharged by
     a fixed ejector. (Conceptually a printable, single-use
     SWILE-like volumetric head.)

  C. Capillary dip + fixed wiper — a fine printed straw fills by
     capillary / jamming on dip into a powder reservoir; the gantry
     drives the straw past a fixed wiper knife to shear off the
     contents into the target. (Direct printable mini-SWILE
     analogue.)

  D. Brush / swab pickup + fixed comb knock-off — natural-bristle
     pickup by van der Waals / electrostatic adhesion, deposited by
     dragging the loaded brush across a fixed comb over the target.

  E. Salt-shaker oscillation — printed cup with calibrated bottom
     mesh, dose metered by the gantry's X-Y oscillation amplitude /
     frequency / duration over the target.

  F. Passive auger via rack-and-pinion against a fixed pin — gantry
     push past a fixed pin ratchets a printed Archimedes screw inside
     a tube to positively displace one auger thread of powder per
     stroke (no motor).

  G. Tap-driven sieve (concept A) augmented with a single ~$2 ERM
     coin vibration motor on the cup, run from a coin cell via a
     SPST switch — minimal added electronics.

  H. Solenoid-tapped sieve closed-loop with an external 0.1 mg
     balance and a microcontroller — the most accurate option, but
     duplicates much of what a Quantos does and is the most
     "electronics-heavy".

Specific questions:

  1. Which of A-H are the strongest candidates for a one-day workshop
     build that is genuinely *different* from the scoop and bimodal
     trough designs above, and why?

  2. For each candidate, what is a realistic minimum dose, expected
     RSD, and dominant failure mode on cohesive sub-100-um powders?

  3. Are there published, peer-reviewed or vendor-documented designs
     for any of A-H (especially A, B, C) that we should be aware of
     and cite / borrow from rather than re-invent? Please be explicit
     when no published analogue exists.

  4. Are there *additional* alternative dispensing styles we haven't
     listed that meet the same gantry / one-day / 3D-print-friendly
     constraints? Concretely, please consider tribo-electric
     spray, electrostatic pickup wands, magnet-assisted dispensing
     (where a ferromagnetic carrier particle is mixed with the
     powder), microfluidic gas-pulse dispensing, and any other
     micro-dose primitives that may not have surfaced in the
     commercial-landscape sweep we did in PR #11 of the same repo.

  5. Where do these eight concepts sit relative to the documented
     "sub-10 mg cohesive-powder dispensing gap" identified in our
     PR #11 commercial-landscape synthesis? Which (if any) plausibly
     close that gap with a single workshop-day's effort?
"""


def main() -> int:
    api_key = os.environ.get("EDISON_API_KEY")
    if not api_key:
        sys.stderr.write(
            "EDISON_API_KEY not set in the environment; cannot submit.\n"
        )
        return 1

    client = EdisonClient(api_key=api_key)
    request = TaskRequest(
        name=JobNames.LITERATURE,
        query=QUERY,
        tags=[QUERY_TAG, "issue-12", "powder-excavator"],
    )
    submitted_at = _dt.datetime.now(tz=_dt.timezone.utc).isoformat()
    task = client.create_task(request)

    # ``EdisonClient.create_task`` returns the new task id as a bare
    # string (UUID); fall back defensively in case the SDK return shape
    # ever changes to a model / dict.
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
            "ERROR: could not extract a task id from EdisonClient.create_task() "
            f"return value (got: {task!r}). Refusing to write edison_query.json "
            "with a null id; please re-run once the SDK return shape is known.\n"
        )
        return 2

    record = {
        "tag": QUERY_TAG,
        "task_id": task_id,
        "job_name": str(JobNames.LITERATURE),
        "submitted_at": submitted_at,
        "wait_policy": (
            "do-not-wait (per issue #12); fetch in next session"
        ),
        "query": QUERY,
    }

    out_path = HERE / "edison_query.json"
    out_path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(f"Submitted Edison task; recorded id at {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
