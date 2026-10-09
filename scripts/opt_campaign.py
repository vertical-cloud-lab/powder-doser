#!/usr/bin/env python3
"""Issue #164 optimization campaign loop (runs on the laptop).

William's ``ax-platform==0.4.3`` Honegumi sample pointed at the rig
(docs/optimization/campaign-setup.md): ask Ax for a parameter set, run
ONE dose on the Pi Zero over SSH (``opt_dose_capture.py``), tell Ax the
outcomes, snapshot, repeat.  The only manual act is starting it:

    python scripts/opt_campaign.py --powder-id salt --target-g 0.5 \
        --budget 40 --host pi@<zero-hostname>

Campaign order per powder (section 2.4): a 2^(8-4) resolution-IV
screening fraction (16 corners) + 4 center points, bracketed by two
doses at the hand-tuned baseline (section 2.9), then the per-powder
tau_afterflow fit from the screening stop events (section 2.8), then
the centers and baselines re-dosed under the fitted tau, then the BO
phase (SOBOL sanity probes -> SAASBO / qNEHVI over the two objectives
minimize(t_total_s, abs_error_mg) with the locked 180 s / 20 mg
thresholds), then the Pareto readout.  All screening doses are attached
to Ax as existing data (the sample's ``attach_trial`` block) so BO
starts warm.  Every dose first pushes the campaign's frozen snapshot of
trickle_params.py, so the hand-tuned constants are what actually runs.

Operator interaction (section 1.2): between doses a short countdown
auto-continues -- touch nothing and the next dose starts, recorded as
"no spill"; ``s`` flags a spill on the dose just finished (penalized
per section 2.3), ``e`` says the hopper/auger ran empty (the dose is
voided -- kept in the ledger, never modeled -- and dosed again after
the refill), ``p`` pauses; several untouched countdowns in a row park
the loop.  A dose that ends ``stalled`` (no powder flow) never
auto-continues: the operator says whether the hopper ran empty or the
powder really jammed.  The cup-empty / hopper-top-up cadence prompt
(``--cup-every``) hard-blocks, because it needs hands at the rig.

Interruptions are safe anywhere (section 5.4).  Every dose is atomic on
the Zero (same-uuid re-invocation returns the stored result), and the
laptop writes the trial uuid into the campaign document before it
doses, so a dose that finished while the loop was down (Ctrl-C, SSH
drop, crash) is fetched from the Zero and recorded, never forgotten or
re-dosed.  The Ax experiment is snapshotted after every ask and tell,
an Ax trial that was asked but never told is dosed again with the same
parameters, and ``--resume`` (no id = this powder's latest campaign)
continues from the local state, or from the MongoDB mirror when the
local copy is gone.  The powder file (data/powder_models/<powder>.json
and the ``powder_models`` document) carries a ``latest_campaign`` block
with the campaign id, phase, iteration number, last dose, and the
resume command.

``--unattended`` is for a session with nobody at the rig (an overnight
run from CI): no countdown, no cadence stop (the cup is never emptied),
spills recorded as unobserved, and the campaign ENDS -- readout, status
``finished``, no resume expected -- at the first limit: the cup budget
(``--cup-budget-g``: powder the balance can still take on top of the
cup), the ``--stop-at`` deadline, a streak of stalls or jams (an empty
hopper nobody can refill), or a rig fault that one retry did not clear.
An unattended validation block that hits a limit just stops: no
profile, status ``validation-stopped``, the campaign's readout untouched.

``--simulate`` runs the identical loop against the PR #124 virtual
plant (the trickle_tap sim rig) instead of SSH -- no hardware, used by
scripts/tests and for shaking down the loop before a rig session.

``--variant three-stage-margin`` (section 7) searches a 9th knob on top
of the three-stage dose: ``cutoff_margin_g``, how far short of the goal
the PI trickle's predicted final mass halts it and the taps take over
(0-35 mg; the trickle was hand-tuned at 35).  By default it warm-starts
from the powder's latest three-stage campaign (``--warm-start``): every
usable dose of that campaign goes to Ax as data at its own 35 mg, the
screening block re-doses that campaign's 16 corners at 0 mg (the old
fraction crossed with the margin), and four checks at the fitted tau
(the parent's fastest validated point at 35 mg, twice; the box center
at 17.5 mg, twice) replace the anchors.  The parent's frozen snapshot
and tau fit carry over unchanged, so the margin is the only controller
change.  With no parent (``--warm-start none``, or a powder without a
three-stage campaign) it screens a fresh 2^(9-4)_IV fraction (32
corners) instead.  Margin campaigns score an overshoot (a dose that
ends past the band) like a jam, and a validation block containing one
fails.

``--variant bulk-tap`` (section 6) optimizes the bulk -> tap dose
instead: no PI trickle (firmware TRICKLE_ENABLED = 0), and the search
space swaps the trim taps, trim tilt, and bulk->trim threshold for the
predictive bulk's approach rpm, taper start, and stop margin.  The loop,
executor, tau fit, anchors, BO, readout, and validation are the same;
screening runs on the powder's fitted tau (0.83 s without one), since
the bulk halt itself is the prediction.

Validation (section 2.4 step 5): after picking a point off the front,

    python scripts/opt_campaign.py --powder-id salt --host pi@zero \
        --validate-point bo-003 --replicates 8

doses the replicates inside the powder's latest campaign (or
``--resume <id>``), so they run on its fitted tau, and writes the
``dosing_profiles`` document (plus a local cache under data/profiles/)
that ``dose.py`` dispenses from.  ``--validate-point`` takes the label
of one of the campaign's doses (report.md, pareto.json);
``--validate-params '{"bulk_tap": "off", ...}'`` takes any 8 values
instead.  Each block is listed in the campaign document's
``profiles`` (section 5.7).

Dependencies (laptop only): ``pip install ax-platform==0.4.3 pymongo``
(section 5.1; on Linux install the CPU torch wheel first).
"""

import argparse
import datetime
import json
import os
import shlex
import subprocess
import sys
import time
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import opt_common as oc                                       # noqa: E402

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIRMWARE_DIR = os.path.join(REPO_ROOT, "hardware", "test-module",
                            "firmware", "trickle_tap")
DEFAULT_STATE = os.path.join(REPO_ROOT, "data", "opt")
PROFILE_CACHE = os.path.join(REPO_ROOT, "data", "profiles")

N_CENTERS = 4
N_BASELINES = 2         # hand-tuned baseline doses (section 2.9)
# Screening labels re-dosed under the fitted tau (section 2.8).
ANCHOR_PREFIXES = ("center-", "baseline-")
# A warm-started margin campaign's checks (section 7.2): the parent's
# fastest validated point at the parent's margin, and the box center.
N_CHECKS = 2
N_MARGIN_CENTERS = 2
# Fixed reference doses the readout compares the front against.
REFERENCE_PREFIXES = ("baseline-", "rebaseline-", "check-")

# The resolution-IV fractions, by factor count: the number of base
# factors (a full 2^n), and for each generated factor the base factors
# it multiplies (0 = A).
#   8 factors, 16 runs: A-D, E=BCD, F=ACD, G=ABC, H=ABD
#   9 factors, 32 runs: A-E, F=BCDE, G=ACDE, H=ABDE, J=ABCE
DESIGNS = {
    8: (4, ((1, 2, 3), (0, 2, 3), (0, 1, 2), (0, 1, 3))),
    9: (5, ((1, 2, 3, 4), (0, 2, 3, 4), (0, 1, 3, 4), (0, 1, 2, 4))),
}
# The factors of each variant's screen, base factors first.
SCREEN_FACTORS = {
    oc.VARIANT_THREE_STAGE: (
        "bulk_tilt_deg", "trickle_tilt_deg", "tap_tilt_deg", "bulk_rpm",
        "trickle_start_remaining_g", "tolerance_g", "bulk_tap", "trim_tap"),
    oc.VARIANT_BULK_TAP: (
        "bulk_tilt_deg", "bulk_min_rpm", "tap_tilt_deg", "bulk_rpm",
        "bulk_stop_margin_g", "tolerance_g", "bulk_tap",
        "bulk_taper_start_g"),
    oc.VARIANT_THREE_STAGE_MARGIN: (
        "bulk_tilt_deg", "trickle_tilt_deg", "tap_tilt_deg", "bulk_rpm",
        "cutoff_margin_g", "trickle_start_remaining_g", "tolerance_g",
        "bulk_tap", "trim_tap"),
}
# Campaign-id tag per variant (salt-margin-20261009T...Z).
CID_TAGS = {oc.VARIANT_BULK_TAP: "bulktap-",
            oc.VARIANT_THREE_STAGE_MARGIN: "margin-"}
# The bulk -> tap screen's tau when the powder has no fitted one: salt's
# PR #131 stop tests (the bulk halt IS the prediction there, so the
# three-stage screen's tuned 0.30 s would overshoot by design).
BULK_TAP_TAU_PRIOR_S = 0.83


def log(msg):
    print("[campaign] {}".format(msg), flush=True)


class CampaignEnd(Exception):
    """An --unattended campaign hit a limit: stop dosing, read out."""


def utcstamp():
    return datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y%m%dT%H%M%SZ")


# ---------------------------------------------------------------------------
# Screening design: 2^(8-4)_IV + centers (section 2.4, from #162 section 5)
# ---------------------------------------------------------------------------

def design_rows(n_factors):
    """The +-1 rows of the ``DESIGNS`` fraction for ``n_factors``, in
    standard order (base factor A alternating fastest)."""
    n_base, generators = DESIGNS[n_factors]
    rows = []
    for i in range(2 ** n_base):
        signs = [1 if i >> j & 1 else -1 for j in range(n_base)]
        for gen in generators:
            sign = 1
            for j in gen:
                sign *= signs[j]
            signs.append(sign)
        rows.append(signs)
    return rows


def screening_plan(seed=42, baseline=None, baseline_reps=N_BASELINES,
                   variant=oc.VARIANT_THREE_STAGE):
    """The resolution-IV corners + 4 centers as campaign parameter
    dicts, bracketed by ``baseline_reps`` doses at ``baseline``.

    Eight factors (both 8-knob variants): 16 corners.  Base factors A-D
    are the four tilts/RPM (full 2^4); the generators E=BCD, F=ACD,
    G=ABC, H=ABD (the standard minimum-aberration 2^(8-4)_IV set) carry
    the threshold, the tolerance band, and the two tap categoricals --
    which slot in natively as two-level factors (``SCREEN_FACTORS`` has
    the bulk -> tap variant's order).  Nine (a cold-started margin
    campaign): 32 corners, A-E full 2^5 with the margin as E, and
    F=BCDE, G=ACDE, H=ABDE, J=ABCE.  Corner order is shuffled (seeded)
    per DOE practice; centers run at the box midpoints with the
    cadences off.

    ``baseline`` is the hand-tuned point (section 2.9).  It sits inside
    every box but not at its midpoint, so it rides along as extra
    doses rather than replacing the centers.  The first baseline dose
    opens the block on known-good settings and the second closes it,
    so drift across the block shows up at a fixed point.  The DOE's
    main-effect analysis uses corners + centers only.
    """
    bounds = {p["name"]: p.get("bounds")
              for p in oc.search_space_ax(variant)}

    def level(name, hi):
        if bounds[name] is None:                 # categorical off / on
            return oc.CAT_ON if hi > 0 else oc.CAT_OFF
        lo_v, hi_v = bounds[name]
        return hi_v if hi > 0 else lo_v

    factors = SCREEN_FACTORS[variant]
    corners = [{name: level(name, sign) for name, sign in zip(factors, row)}
               for row in design_rows(len(factors))]
    import random
    random.Random(seed).shuffle(corners)
    center = {name: (b[0] + b[1]) / 2.0
              for name, b in bounds.items() if b}
    center.update({name: oc.CAT_OFF
                   for name, b in bounds.items() if b is None})
    plan = [("corner-{:02d}".format(i), p) for i, p in enumerate(corners)]
    plan += [("center-{:02d}".format(i), dict(center))
             for i in range(N_CENTERS)]
    if baseline and baseline_reps > 0:
        base = [("baseline-{:02d}".format(i), dict(baseline))
                for i in range(baseline_reps)]
        half = (baseline_reps + 1) // 2
        plan = base[:half] + plan + base[half:]
    return plan


def warm_start_plans(parent_doc, baseline):
    """A margin campaign on top of a three-stage ``parent_doc`` (section
    7.2) -> (screening plan, anchor plan, check point label).

    Screening: the parent's 16 corners again at the margin box's floor
    (0 mg), at the parent's screening tau like the originals, so the
    two blocks together are the parent's 2^(8-4)_IV fraction crossed
    with the margin.  Anchors, at the fitted tau: the parent's fastest
    validated point at the parent's own margin (a drift check against
    its validation block; the hand-tuned ``baseline`` without one), and
    the 9-knob box center.
    """
    space = oc.search_space_ax(oc.VARIANT_THREE_STAGE_MARGIN)
    bounds = {p["name"]: p.get("bounds") for p in space}
    lo, hi = bounds["cutoff_margin_g"]
    tuned = float(parent_doc["frozen_params"]["cutoff_margin_g"])
    if not lo <= tuned <= hi:
        raise SystemExit(
            "the parent campaign ran at cutoff_margin_g {} g, outside the "
            "margin box {}-{} g, so its doses cannot be attached".format(
                tuned, lo, hi))
    plan = [(label, dict(params, cutoff_margin_g=lo))
            for label, params in parent_doc["screening_plan"]
            if label.startswith("corner-")]
    validated = [p for p in parent_doc.get("profiles") or []
                 if p.get("validated") and p.get("point")
                 and (p.get("validation") or {}).get("median_t_total_s")
                 is not None]
    if validated:
        best = min(validated,
                   key=lambda p: p["validation"]["median_t_total_s"])
        point = best["point"]
        check = {k: best["parameters"][k] for k, _f, _t in oc.SEARCH_PARAMS}
    else:
        point = "baseline"
        check = {k: baseline[k] for k, _f, _t in oc.SEARCH_PARAMS}
    center = {name: (b[0] + b[1]) / 2.0 for name, b in bounds.items() if b}
    center.update({name: oc.CAT_OFF
                   for name, b in bounds.items() if b is None})
    anchors = [("check-{}-{:02d}".format(point, i),
                dict(check, cutoff_margin_g=tuned)) for i in range(N_CHECKS)]
    anchors += [("center-{:02d}".format(i), dict(center))
                for i in range(N_MARGIN_CENTERS)]
    return plan, anchors, point


def frozen_override(item, frozen, variant):
    """``--frozen-set KEY=VALUE`` -> (key, value typed like the
    snapshot's).  Searched knobs, the variant's switch, and the target
    are set per trial, so they are refused here."""
    key, sep, raw = item.partition("=")
    key, raw = key.strip().lower(), raw.strip().lower()
    if not sep or key not in frozen:
        raise SystemExit("--frozen-set {!r}: expected KEY=VALUE with a "
                         "trickle_params key".format(item))
    per_trial = {k for _n, k, _t in oc.search_params(variant)}
    per_trial |= set(oc.VARIANTS[variant]["mode"]) | {"goal_mass_g"}
    if key in per_trial:
        raise SystemExit("--frozen-set {}: set per trial in a {} campaign, "
                         "not frozen".format(key, variant))
    old = frozen[key]
    try:
        if isinstance(old, bool):
            value = {"true": True, "on": True, "false": False,
                     "off": False}.get(raw)
            if value is None:
                value = bool(int(float(raw)))
        elif isinstance(old, int):
            value = int(float(raw))
        else:
            value = float(raw)
    except ValueError:
        raise SystemExit("--frozen-set {}: {!r} is not a number".format(
            key, raw))
    return key, value


def frozen_snapshot():
    """Every trickle_params value, lowercase-keyed -- the campaign
    document's frozen-parameter record (section 1.3)."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "trickle_params_snapshot",
        os.path.join(FIRMWARE_DIR, "trickle_params.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return {n.lower(): getattr(mod, n) for n in dir(mod)
            if n.isupper() and not n.startswith("_")}


# ---------------------------------------------------------------------------
# Executors: SSH to the Zero, or the PR #124 virtual plant
# ---------------------------------------------------------------------------

# The Zero's venv is the only interpreter there with pymongo (PR #131).
DEFAULT_REMOTE_PYTHON = "~/powder-doser-venv/bin/python"
# The Pico is shared with other sessions (campaign-setup section 5.1).
BUSY_HINT = ("another session is using the Pico, nothing was dosed; wait "
             "for it (or agree a handover)")


def _shell_path(path):
    """shlex.quote that keeps a leading ``~/`` expandable on the remote
    shell -- a quoted tilde is a literal tilde, so the documented
    ``~/powder-doser`` defaults would otherwise never resolve."""
    if path == "~":
        return "~"
    if path.startswith("~/"):
        return "~/" + shlex.quote(path[2:])
    return shlex.quote(path)


class SSHExecutor:
    def __init__(self, host, remote_repo, port, operator,
                 remote_python=DEFAULT_REMOTE_PYTHON, takeover=False):
        self.host = host
        self.remote = remote_repo.rstrip("/")
        self.port = port
        self.operator = operator
        self.remote_python = remote_python
        self.takeover = takeover

    def _remote_cmd(self, extra):
        """The one sh line run on the Zero per invocation.

        Non-interactive SSH reads no rc files, so the #131 credential
        file is sourced explicitly when present (opt_common also reads
        it directly as a fallback); the venv interpreter is preferred
        with a plain-python3 fallback for hosts without the venv.
        """
        args = " ".join(shlex.quote(c)
                        for c in ["scripts/opt_dose_capture.py"] + extra)
        env_file = _shell_path(oc.MONGODB_ENV_FILE)
        return ("[ -f {env} ] && . {env}; "
                "cd {repo} || exit 9; "
                'PY={py}; [ -x "$PY" ] || PY=python3; '
                'exec "$PY" {args}').format(
                    env=env_file, repo=_shell_path(self.remote),
                    py=_shell_path(self.remote_python), args=args)

    def _invoke(self, extra, timeout_s):
        ssh = ["ssh", "-o", "BatchMode=yes", self.host,
               self._remote_cmd(extra)]
        proc = subprocess.run(ssh, capture_output=True, text=True,
                              timeout=timeout_s)
        sys.stderr.write(proc.stderr)
        for line in reversed(proc.stdout.splitlines()):
            line = line.strip()
            if line.startswith("{"):
                summary = json.loads(line)
                # an older executor answers statuses with fewer keys
                return dict(oc.status_summary(summary.get("trial_uuid"),
                                              summary.get("status")),
                            **summary)
        raise RuntimeError("no summary line from the Zero "
                           "(exit {})".format(proc.returncode))

    def dose(self, campaign_id, trial_uuid, trial_index, powder_id,
             target_g, mode, params, covariates, frozen=None):
        extra = ["--powder-id", powder_id, "--target-g", str(target_g),
                 "--campaign-id", campaign_id, "--trial", trial_uuid,
                 "--trial-index", str(trial_index), "--mode", mode,
                 "--params", json.dumps(params),
                 "--covariates", json.dumps(covariates)]
        if frozen:
            extra += ["--frozen", json.dumps(frozen, sort_keys=True)]
        if self.port:
            extra += ["--port", self.port]
        if self.operator:
            extra += ["--operator", self.operator]
        if self.takeover:
            extra += ["--takeover"]
        try:
            return self._invoke(extra, timeout_s=900)
        except (subprocess.TimeoutExpired, RuntimeError, OSError,
                ValueError) as exc:
            log("dose invocation failed ({}); trying to fetch the "
                "stored result".format(exc))
            return self.fetch(trial_uuid, campaign_id)

    def fetch(self, trial_uuid, campaign_id, attempts=4, wait_s=30,
              max_wait_s=900):
        """What the Zero knows about one trial uuid (never doses).

        -> the stored summary, or a status-only summary: ``not-found``
        (never started: nothing dosed), ``interrupted`` (the executor
        died mid-dose), or ``unreachable`` (SSH failed ``attempts``
        times, or the dose was still running after ``max_wait_s``).
        An ``in-progress`` answer is waited out.
        """
        deadline = time.monotonic() + max_wait_s
        failures = 0
        while True:
            try:
                summary = self._invoke(
                    ["--fetch", trial_uuid, "--campaign-id", campaign_id],
                    timeout_s=60)
                if summary.get("status") != "in-progress":
                    return summary
                log("trial {} is still dosing on the Zero; asking again "
                    "in {} s".format(trial_uuid[:8], wait_s))
            except Exception as exc:
                failures += 1
                log("fetch attempt {}/{} failed: {}".format(
                    failures, attempts, exc))
                if failures >= attempts:
                    break
            if time.monotonic() + wait_s > deadline:
                break
            time.sleep(wait_s)
        return oc.status_summary(trial_uuid, "unreachable")


class SimExecutor:
    """The identical loop against the trickle_tap virtual plant."""

    def __init__(self, out_root, seed=0):
        import importlib.util
        sim_path = os.path.join(FIRMWARE_DIR, "sim", "test_trickle_tap.py")
        spec = importlib.util.spec_from_file_location("trickle_sim",
                                                      sim_path)
        self.sim = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.sim)
        self.out_root = out_root
        self.seed = seed

    def dose(self, campaign_id, trial_uuid, trial_index, powder_id,
             target_g, mode, params, covariates, frozen=None):
        # The same push as the rig: the frozen snapshot (minus the
        # flash/console switches, which stay sim-quiet), then the
        # searched values, the variant's switch, and tau.
        p_over = {k: v for k, v in (frozen or {}).items()
                  if k not in ("log_to_flash", "print_every_n_polls")}
        p_over.update(oc.firmware_values(params))
        plant = self.sim.Plant(seed=self.seed + trial_index,
                               afterflow_s=0.83)
        lines = []
        doser = self.sim.make_doser(
            plant, p_over=p_over,
            log=lambda msg="": lines.append(str(msg)))[0]
        doser.dose(target_g)
        result_doc = None
        for ln in lines:
            if ln.startswith(oc.RESULT_PREFIX):
                result_doc = json.loads(ln[len(oc.RESULT_PREFIX):])
        doc = oc.build_trial_doc(
            campaign_id=campaign_id, trial_uuid=trial_uuid,
            trial_index=trial_index, powder_id=powder_id,
            target_g=target_g, mode=mode, params=params,
            result_doc=result_doc, telemetry_rows=[],
            telemetry_header=None, covariates=covariates,
            operator="sim", started_utc=oc.utcnow_iso(),
            repo_root=REPO_ROOT)
        spool = oc.spool_trial(self.out_root, doc)
        return oc.trial_summary(doc, spool_path=spool, uploaded=False)

    def fetch(self, trial_uuid, campaign_id):
        doc = oc.find_spooled_trial(self.out_root, trial_uuid, campaign_id)
        return (oc.trial_summary(doc) if doc
                else oc.status_summary(trial_uuid, "not-found"))


# ---------------------------------------------------------------------------
# Operator interaction (section 1.2)
# ---------------------------------------------------------------------------

def _read_key_with_timeout(seconds):
    """One keypress inside ``seconds`` (None on timeout).  POSIX uses
    select on stdin; Windows polls msvcrt; a non-TTY (tests, --simulate
    in CI) never waits."""
    if not sys.stdin.isatty():
        return None
    try:
        import msvcrt                                   # Windows
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            if msvcrt.kbhit():
                return msvcrt.getwch()
            time.sleep(0.05)
        return None
    except ImportError:
        import select
        r, _, _ = select.select([sys.stdin], [], [], seconds)
        if not r:
            return None
        return sys.stdin.readline().strip()[:1] or "\n"


VOID_EMPTY = "hopper-empty"


class Operator:
    def __init__(self, countdown_s, cup_every, park_after, simulate,
                 unattended=False):
        self.countdown_s = countdown_s
        self.cup_every = cup_every
        self.park_after = park_after
        self.simulate = simulate
        self.unattended = unattended
        self.untouched = 0
        self.doses_since_empty = 0
        self.recycle_count = 0
        self.hopper_refills = 0

    def covariates(self):
        return {"doses_since_cup_empty": self.doses_since_empty,
                "recycle_count": self.recycle_count,
                "hopper_refills": self.hopper_refills}

    def after_dose(self, summary):
        """The spill countdown -> (spill, void, keep_going).

        ``void`` is VOID_EMPTY when the operator says the hopper/auger
        ran empty: the dose stays in the ledger but is never modeled,
        and its parameters are dosed again after the refill.
        """
        self.doses_since_empty += 1
        if self.unattended:
            # Nobody can see a spill (None = unobserved, never
            # penalized) or tell an empty hopper from a jam: a stall
            # stays a penalized jam, and the Runner ends the campaign
            # on a streak of them instead of asking.
            return None, None, True
        if self.simulate or self.countdown_s <= 0:
            return False, None, True
        if summary.get("jam_reason") == "stall":
            return self._stall_prompt(summary)
        print("    countdown {}s -- [Enter]=next  s=SPILL on that dose  "
              "e=hopper ran EMPTY (void it)  p=pause".format(
                  self.countdown_s), flush=True)
        key = _read_key_with_timeout(self.countdown_s)
        if key is None:
            self.untouched += 1
            if self.park_after and self.untouched >= self.park_after:
                print("    {} untouched countdowns -- parking; press "
                      "Enter to resume".format(self.untouched), flush=True)
                try:
                    input()
                except EOFError:
                    return False, None, False
                self.untouched = 0
            return False, None, True
        self.untouched = 0
        if key in ("s", "S"):
            print("    SPILL recorded on trial {}".format(
                summary["trial_uuid"][:8]), flush=True)
            return True, None, True
        if key in ("e", "E"):
            return False, self._refill(), True
        if key in ("p", "P"):
            print("    paused; press Enter to resume (Ctrl-C to stop "
                  "-- --resume continues later)", flush=True)
            try:
                input()
            except EOFError:
                return False, None, False
        return False, None, True

    def _stall_prompt(self, summary):
        """A stall means no powder flowed.  An empty hopper/auger looks
        exactly like a powder that jams, and only a person can tell them
        apart, so this never auto-continues."""
        self.untouched = 0
        print("\n*** trial {} STALLED: no powder flow.  Look at the hopper "
              "and auger:\n    e = it ran EMPTY: refill; the dose is voided "
              "and dosed again\n    j = the powder really jammed at these "
              "settings: keep it (penalized)\n    s = keep it, and flag a "
              "spill ***".format(summary["trial_uuid"][:8]), flush=True)
        while True:
            try:
                key = input("    e/j/s: ").strip()[:1].lower()
            except EOFError:               # nobody there: keep it, stop
                return False, None, False
            if key == "e":
                return False, self._refill(), True
            if key == "j":
                return False, None, True
            if key == "s":
                return True, None, True

    def _refill(self):
        print("    VOID: refill the hopper (re-prime the auger if it ran "
              "dry), then press Enter -- the same parameters dose "
              "again", flush=True)
        try:
            input()
        except EOFError:
            pass
        self.hopper_refills += 1
        return VOID_EMPTY

    def cadence_prompt(self):
        if self.simulate or self.unattended or not self.cup_every:
            return
        if self.doses_since_empty >= self.cup_every:
            print("\n*** CADENCE STOP: empty the cup back into the "
                  "hopper, top the hopper up, put the cup back, then "
                  "press Enter ***", flush=True)
            try:
                input()
            except EOFError:
                pass
            self.doses_since_empty = 0
            self.recycle_count += 1


# ---------------------------------------------------------------------------
# Campaign state (local-first; Mongo is the queryable mirror)
# ---------------------------------------------------------------------------

MIRROR_BACKOFF_S = 300

class Campaign:
    def __init__(self, campaign_id, state_root):
        self.campaign_id = campaign_id
        self.dir = oc.spool_dir(state_root, campaign_id)
        self.path = os.path.join(self.dir, "campaign.json")
        self.snapshot_path = os.path.join(self.dir, "ax_snapshot.json")
        # Distinct from the executor-side trials.jsonl spool (which in
        # --simulate lands in the same directory): this one is the
        # laptop's own ledger, one line per dose with label/mode/spill.
        self.records_path = os.path.join(self.dir,
                                         "campaign_records.jsonl")
        self.doc = None
        self.mirror_retry_at = 0.0

    def exists(self):
        return os.path.exists(self.path)

    def load(self):
        with open(self.path) as f:
            self.doc = json.load(f)
        return self.doc

    def save(self, records=None, mirror=True):
        """Local JSON first (atomic replace), then the Mongo mirror:
        the doc + the Ax snapshot + every dose record, which is enough
        for ``restore_from_mongo`` to rebuild this directory elsewhere.
        -> the Mongo handle when the mirror succeeded, else None."""
        self.doc["updated_utc"] = oc.utcnow_iso()
        tmp = self.path + ".tmp"
        with open(tmp, "w") as f:
            json.dump(self.doc, f, indent=1)
        os.replace(tmp, self.path)
        # Offline, every attempt waits out the 10 s server selection, so
        # after a failure the mirror rests a few minutes; the next
        # successful save carries the full state anyway.
        if not mirror or time.monotonic() < self.mirror_retry_at:
            return None
        try:
            db = oc.mongo_db()
            if db is not None:
                doc = dict(self.doc)
                if os.path.exists(self.snapshot_path):
                    with open(self.snapshot_path) as f:
                        doc["ax_snapshot"] = f.read()
                if records is not None:
                    doc["records"] = records
                db[oc.COLL_CAMPAIGNS].replace_one(
                    {"campaign_id": self.campaign_id}, doc, upsert=True)
                return db
        except Exception as exc:
            self.mirror_retry_at = time.monotonic() + MIRROR_BACKOFF_S
            log("campaign mirror to Mongo failed ({}); local state is "
                "authoritative, retrying in {} s".format(
                    exc, MIRROR_BACKOFF_S))
        return None

    def restore_from_mongo(self):
        """Rebuild this campaign's local directory from its
        ``opt_campaigns`` mirror (another laptop, or a wiped data/opt/).
        -> True when restored."""
        try:
            db = oc.mongo_db()
            found = (db[oc.COLL_CAMPAIGNS].find_one(
                {"campaign_id": self.campaign_id})
                if db is not None else None)
        except Exception as exc:
            log("could not read the Mongo mirror ({})".format(exc))
            return False
        if not found:
            return False
        found.pop("_id", None)
        snapshot = found.pop("ax_snapshot", None)
        records = found.pop("records", None) or []
        if snapshot:
            with open(self.snapshot_path, "w") as f:
                f.write(snapshot)
        with open(self.records_path, "w") as f:
            for record in records:
                f.write(json.dumps(record) + "\n")
        self.doc = found
        self.save(mirror=False)
        log("restored {} from MongoDB: {} dose records{}".format(
            self.campaign_id, len(records),
            " + the Ax snapshot" if snapshot else ""))
        return True

    def records(self):
        if not os.path.exists(self.records_path):
            return []
        with open(self.records_path) as f:
            return [json.loads(l) for l in f if l.strip()]

    def append_record(self, record):
        with open(self.records_path, "a") as f:
            f.write(json.dumps(record) + "\n")


# ---------------------------------------------------------------------------
# Ax (the pinned Honegumi template)
# ---------------------------------------------------------------------------

def make_ax_client(model_name, sobol_trials, seed):
    from ax.service.ax_client import AxClient
    from ax.modelbridge.factory import Models
    from ax.modelbridge.generation_strategy import (GenerationStep,
                                                    GenerationStrategy)
    model = Models.SAASBO if model_name == "saasbo" else Models.MOO
    sobol_trials = max(1, int(sobol_trials))
    gs = GenerationStrategy(steps=[
        GenerationStep(model=Models.SOBOL, num_trials=sobol_trials,
                       min_trials_observed=1,
                       max_parallelism=1, model_kwargs={"seed": seed}),
        GenerationStep(model=model, num_trials=-1, max_parallelism=1),
    ])
    return AxClient(generation_strategy=gs, verbose_logging=False)


def create_experiment(ax_client, name, variant=oc.VARIANT_THREE_STAGE):
    from ax.service.ax_client import ObjectiveProperties
    ax_client.create_experiment(
        name=name,
        parameters=[dict(p) for p in oc.search_space_ax(variant)],
        objectives={
            # Thresholds passed EXPLICITLY -- Ax silently infers them
            # when omitted, which must not score our hypervolume
            # (campaign-setup section 5.3).
            "t_total_s": ObjectiveProperties(
                minimize=True, threshold=oc.THRESHOLD_T_TOTAL_S),
            "abs_error_mg": ObjectiveProperties(
                minimize=True, threshold=oc.THRESHOLD_ABS_ERROR_MG),
        },
    )


def in_search_space(params, variant):
    """True when every searched value of ``params`` sits inside the
    variant's box (Ax refuses to attach anything else)."""
    for p in oc.search_space_ax(variant):
        value = params.get(p["name"])
        if p.get("bounds"):
            lo, hi = p["bounds"]
            if value is None or not lo <= float(value) <= hi:
                return False
        elif value not in p["values"]:
            return False
    return True


def ax_parameterization(params):
    """Campaign params -> the Ax search-space dict (drops tau)."""
    return {name: params[name] for name, _k, _kind
            in oc.search_params(oc.variant_of(params))}


# ---------------------------------------------------------------------------
# The loop
# ---------------------------------------------------------------------------

DEFAULT_BUDGET = 40
# Summaries whose dose provably never reached the powder.
NOTHING_DOSED = ("rig-busy", "not-found")


def latest_campaign_id(state_root, powder_id, simulate, variant=None):
    """This powder's most recently updated campaign -> id or None.

    Looks under ``state_root`` first (a --simulate run only resumes
    simulated campaigns, and a real run only real ones), then at the
    powder file's ``latest_campaign`` pointer, locally and in Mongo,
    which ``Campaign.restore_from_mongo`` can then fetch.  ``variant``
    (``--variant``) narrows it to that variant's campaigns.
    """
    best = None
    if os.path.isdir(state_root):
        for name in os.listdir(state_root):
            try:
                with open(os.path.join(state_root, name,
                                       "campaign.json")) as f:
                    doc = json.load(f)
            except (OSError, ValueError):
                continue
            if (doc.get("kind") != "opt_campaign"
                    or doc.get("powder_id") != powder_id
                    or bool(doc.get("simulate")) != bool(simulate)
                    or (variant and doc.get(
                        "variant", oc.VARIANT_THREE_STAGE) != variant)):
                continue
            key = doc.get("updated_utc") or doc.get("created_utc") or ""
            if best is None or key > best[0]:
                best = (key, doc["campaign_id"])
    if best is not None:
        return best[1]
    if simulate:
        return None
    import fit_tau_afterflow as ft
    model = ft.load_powder_model(powder_id)
    if model is None:
        try:
            db = oc.mongo_db()
            if db is not None:
                model = db[oc.COLL_POWDER_MODELS].find_one(
                    {"powder_id": powder_id})
        except Exception as exc:
            log("could not read powder_models ({})".format(exc))
    latest = (model or {}).get("latest_campaign") or {}
    if variant and latest.get("variant",
                              oc.VARIANT_THREE_STAGE) != variant:
        return None
    return latest.get("campaign_id")


class Runner:
    def __init__(self, args):
        self.args = args
        self.powder_id = oc.normalize_powder_id(args.powder_id)
        state_root = args.state_dir
        cid = args.resume
        if cid == "latest":
            cid = latest_campaign_id(state_root, self.powder_id,
                                     args.simulate, args.variant)
            if cid is not None:
                log("resuming {}'s latest {}campaign: {}".format(
                    self.powder_id, "simulated " if args.simulate else "",
                    cid))
            elif not args.validate_params:  # a point label needs one too
                raise SystemExit("no {}campaign for powder {!r} to "
                                 "resume".format(
                                     "simulated " if args.simulate
                                     else "", self.powder_id))
        resumed = bool(cid)
        if resumed:
            self.campaign = Campaign(cid, state_root)
            if not self.campaign.exists() and not args.simulate:
                self.campaign.restore_from_mongo()
            if not self.campaign.exists():
                raise SystemExit("no local state for campaign {!r} under "
                                 "{} and no MongoDB mirror".format(
                                     cid, state_root))
            self.campaign.load()
        else:
            variant = args.variant or oc.VARIANT_THREE_STAGE
            cid = "{}-{}{}".format(self.powder_id, CID_TAGS.get(variant, ""),
                                   utcstamp())
            self.campaign = Campaign(cid, state_root)
            frozen = frozen_snapshot()
            parent = None
            if variant == oc.VARIANT_THREE_STAGE_MARGIN:
                parent = self.warm_start_parent()
            if parent is not None:
                # The parent's controller, exactly: its snapshot over
                # today's file (knobs it predates keep today's defaults,
                # which reproduce its dose).
                frozen.update(parent.doc["frozen_params"])
                if args.frozen_set:
                    raise SystemExit(
                        "--frozen-set: a warm-started margin campaign runs "
                        "its parent's controller so the parent's doses stay "
                        "valid data; use --warm-start none to change it")
            # the snapshot is what runs (dose.py pushes a profile's copy)
            frozen.update(oc.VARIANTS[variant]["mode"])
            if variant == oc.VARIANT_BULK_TAP:
                frozen["tau_afterflow_s"] = self.tau_prior(args.simulate)
            for item in args.frozen_set:
                key, value = frozen_override(item, frozen, variant)
                log("frozen {} = {} (was {})".format(key, value,
                                                     frozen[key]))
                frozen[key] = value
            baseline = oc.baseline_params(frozen, variant)
            if parent is not None:
                plan, anchors, point = warm_start_plans(parent.doc, baseline)
            else:
                plan = screening_plan(args.seed, baseline,
                                      args.baseline_reps, variant)
            self.campaign.doc = {
                "kind": "opt_campaign",
                "schema_version": oc.SCHEMA_VERSION,
                "campaign_id": cid,
                "variant": variant,
                "powder_id": self.powder_id,
                "target_g": args.target_g,
                "status": "running",
                "phase": "screen",
                "created_utc": oc.utcnow_iso(),
                "operator": args.operator,
                "git_commit": oc.git_commit(REPO_ROOT),
                "simulate": bool(args.simulate),
                "search_space": oc.search_space_ax(variant),
                "objectives": {"t_total_s": oc.THRESHOLD_T_TOTAL_S,
                               "abs_error_mg": oc.THRESHOLD_ABS_ERROR_MG},
                "frozen_params": frozen,
                "baseline_params": baseline,
                "screening_plan": plan,
                "budget": DEFAULT_BUDGET,
                "tau_afterflow": None,
                "in_flight": None,
                "generation": {"model": args.model,
                               "sobol_trials": args.sobol_trials,
                               "seed": args.seed,
                               "ax_platform": "0.4.3"},
            }
            if variant == oc.VARIANT_THREE_STAGE_MARGIN:
                # the margin trades overshoot risk for tap time, and an
                # overshoot cannot be undone in production (section 7.3)
                self.campaign.doc["scoring"] = {"overshoot": "penalized"}
            if parent is not None:
                pdoc = parent.doc
                tau = pdoc.get("tau_afterflow") or {}
                self.campaign.doc.update({
                    "warm_start": {
                        "campaign_id": pdoc["campaign_id"],
                        "cutoff_margin_g": float(
                            pdoc["frozen_params"]["cutoff_margin_g"]),
                        "check_point": point,
                        "attached": None},    # filled when BO starts
                    "anchor_plan": anchors,
                    # the margin is the only change: no tau refit
                    "tau_afterflow": dict(tau) if tau.get("tau0_s")
                    else None,
                    "frozen_overrides": dict(
                        pdoc.get("frozen_overrides") or {}),
                })
                log("warm start from {}: its {} corners again at {:.1f} mg"
                    ", then {} checks at tau {} s".format(
                        pdoc["campaign_id"], len(plan), 1000.0 * float(
                            plan[0][1]["cutoff_margin_g"]) if plan else 0.0,
                        len(anchors), tau.get("tau0_s")))
        if resumed and args.frozen_set:
            log("--frozen-set ignored: {} keeps the snapshot it was "
                "created with".format(cid))
        doc = self.campaign.doc
        if doc["powder_id"] != self.powder_id:
            raise SystemExit("campaign {} is for powder {!r}".format(
                doc["campaign_id"], doc["powder_id"]))
        self.variant = doc.get("variant", oc.VARIANT_THREE_STAGE)
        if args.variant and args.variant != self.variant:
            raise SystemExit("campaign {} is a {} campaign, not {}".format(
                doc["campaign_id"], self.variant, args.variant))
        if args.budget is not None:
            doc["budget"] = args.budget
        doc.setdefault("budget", DEFAULT_BUDGET)

        if args.simulate:
            self.executor = SimExecutor(state_root, seed=args.seed)
        else:
            if not args.host:
                raise SystemExit("--host is required unless --simulate")
            self.executor = SSHExecutor(args.host, args.remote_repo,
                                        args.pico_port, args.operator,
                                        args.remote_python, args.takeover)
        self.operator = Operator(args.countdown, args.cup_every,
                                 args.park_after, args.simulate,
                                 unattended=args.unattended)
        self.stop_at = None
        if args.stop_at:
            self.stop_at = datetime.datetime.fromisoformat(
                args.stop_at.replace("Z", "+00:00")).timestamp()
        self.validating = bool(args.validate_params or args.validate_point)
        # A validation block keeps the campaign's own unattended record;
        # its profile says whether anyone was watching for spills.
        if args.unattended and not self.validating:
            doc["unattended"] = {
                "cup_budget_g": args.cup_budget_g,
                "stop_at": args.stop_at,
                "max_stall_streak": args.max_stall_streak,
                "max_jam_streak": args.max_jam_streak}
        # Logging-only overrides, so a resumed campaign may change them.
        overrides = dict(doc.get("frozen_overrides") or {})
        if args.no_flash_log:
            overrides["log_to_flash"] = False
        if args.log_max_rows is not None:
            overrides["log_max_rows"] = args.log_max_rows
        if overrides:
            doc["frozen_overrides"] = overrides
        self.dose_wall_s = []           # laptop wall clock per dose
        self.ask_wall_s = []            # per Ax suggestion
        self.infra_streak = 0
        self.records = self.campaign.records()
        if self.records:
            last = self.records[-1]
            last_cov = last.get("covariates") or {}
            self.operator.recycle_count = last_cov.get("recycle_count", 0)
            self.operator.hopper_refills = last_cov.get("hopper_refills", 0)
            self.operator.doses_since_empty = (
                last_cov.get("doses_since_cup_empty", 0)
                + (0 if last["summary"]["status"] in NOTHING_DOSED else 1))
        self.ax = None
        self.save()

    def warm_start_parent(self):
        """--warm-start: the three-stage campaign a new margin campaign
        builds on (section 7.2) -> its loaded Campaign, or None for a
        cold start.  Default: this powder's latest three-stage campaign
        (a --simulate run only looks at simulated ones)."""
        args = self.args
        want = args.warm_start
        if want and want.lower() == "none":
            log("--warm-start none: a cold margin campaign")
            return None
        cid = want or latest_campaign_id(args.state_dir, self.powder_id,
                                         args.simulate,
                                         oc.VARIANT_THREE_STAGE)
        if cid is None:
            log("no three-stage {}campaign for {!r} to warm-start from: "
                "a cold margin campaign".format(
                    "simulated " if args.simulate else "", self.powder_id))
            return None
        parent = self.parent_campaign(cid)
        pdoc = parent.doc
        if (pdoc.get("variant", oc.VARIANT_THREE_STAGE)
                != oc.VARIANT_THREE_STAGE
                or pdoc.get("powder_id") != self.powder_id
                or bool(pdoc.get("simulate")) != bool(args.simulate)):
            raise SystemExit(
                "--warm-start {}: needs a {}three-stage campaign of powder "
                "{!r}".format(cid, "simulated " if args.simulate else "",
                              self.powder_id))
        return parent

    def parent_campaign(self, cid):
        parent = Campaign(cid, self.args.state_dir)
        if not parent.exists() and not self.args.simulate:
            parent.restore_from_mongo()
        if not parent.exists():
            raise SystemExit("warm start: no local state for campaign {!r} "
                             "under {} and no MongoDB mirror".format(
                                 cid, self.args.state_dir))
        parent.load()
        return parent

    def tau_prior(self, simulate):
        """The bulk -> tap screen's tau: the powder's fitted value, else
        BULK_TAP_TAU_PRIOR_S (a --simulate campaign never reads the
        real powder file)."""
        if not simulate:
            import fit_tau_afterflow as ft
            model = ft.load_powder_model(self.powder_id) or {}
            fitted = (model.get("tau_afterflow") or {}).get("tau0_s")
            if fitted:
                log("bulk-tap screening runs on {}'s fitted tau {} s".format(
                    self.powder_id, fitted))
                return float(fitted)
        log("bulk-tap screening runs on the {} s tau prior".format(
            BULK_TAP_TAU_PRIOR_S))
        return BULK_TAP_TAU_PRIOR_S

    # -- persistence ----------------------------------------------------

    def save(self):
        """Campaign doc (local, then the Mongo mirror with every record),
        then the powder file's ``latest_campaign`` block.  --simulate
        state never leaves the campaign directory."""
        sim = bool(self.args.simulate)
        db = self.campaign.save(self.records, mirror=not sim)
        import fit_tau_afterflow as ft
        try:
            ft.update_powder_model(
                self.powder_id, {"latest_campaign": self.run_status()},
                cache_dir=self.campaign.dir if sim else None,
                upload=db is not None, db=db)
        except Exception as exc:
            log("powder file update failed ({})".format(exc))

    def run_status(self):
        """Where this campaign stands and how to continue it -- the
        powder file's ``latest_campaign`` block (section 5.4)."""
        doc = self.campaign.doc
        plan = doc["screening_plan"]
        n_anchors = len(self.anchor_plan())
        last = self.records[-1] if self.records else None
        flight = doc.get("in_flight")
        resume = "python scripts/opt_campaign.py --powder-id {} " \
                 "--resume {}".format(self.powder_id, doc["campaign_id"])
        resume += (" --simulate" if doc.get("simulate")
                   else " --host <user>@<zero-hostname>")
        if os.path.abspath(self.args.state_dir) != DEFAULT_STATE:
            resume += " --state-dir {}".format(self.args.state_dir)
        state_dir = os.path.abspath(self.campaign.dir)
        if state_dir.startswith(REPO_ROOT + os.sep):
            state_dir = os.path.relpath(state_dir, REPO_ROOT)
        return {
            "campaign_id": doc["campaign_id"],
            "variant": self.variant,
            "simulate": bool(doc.get("simulate")),
            "target_g": doc["target_g"],
            "status": doc["status"],
            "phase": doc["phase"],
            # doses recorded so far = the next dose's trial_index
            "iteration": len(self.records),
            "bo_iteration": self._n_usable("bo"),
            "progress": {
                "screen": [self._n_usable("screen"), len(plan)],
                "recenter": [self._n_usable("recenter"), n_anchors],
                "bo": [self._n_usable("bo"), doc.get("budget")],
                "validation": self._n_usable("validation"),
            },
            "last_dose": None if last is None else {
                "trial_index": last["trial_index"],
                "label": last["label"],
                "mode": last["mode"],
                "trial_uuid": last["trial_uuid"],
                "status": last["summary"]["status"],
                "t_total_s": last["summary"]["t_total_s"],
                "abs_error_mg": last["summary"]["abs_error_mg"],
                "jam": last["summary"]["jam"],
                "spill": last["spill"],
                "void": last.get("void"),
                "utc": last["utc"],
            },
            "in_flight": None if not flight else {
                "label": flight["label"],
                "trial_uuid": flight["trial_uuid"],
                "utc": flight["utc"],
            },
            "tau_afterflow_s": (doc.get("tau_afterflow") or {}).get(
                "tau0_s"),
            "state_dir": state_dir,
            "resume": resume,
        }

    def frozen_push(self):
        """The frozen snapshot each dose pushes before its searched
        values (section 2.9): the hand-tuned constants, exactly."""
        doc = self.campaign.doc
        frozen = dict(doc.get("frozen_params") or {})
        # Controller-neutral switches only (e.g. log_to_flash off when
        # the shared Pico's flash is nearly full -- the executor pulls
        # the telemetry over serial anyway).
        frozen.update(doc.get("frozen_overrides") or {})
        pushed = [key for _n, key, _k in oc.search_params(self.variant)]
        pushed += list(oc.VARIANTS[self.variant]["mode"])
        return {k: v for k, v in frozen.items()
                if k not in pushed and k != "goal_mass_g"}

    # -- unattended limits ----------------------------------------------

    def _guard_g(self):
        frozen = self.campaign.doc.get("frozen_params") or {}
        return float(frozen.get("overshoot_abort_g") or 0.1)

    def cup_load_g(self):
        """Powder in the cup since it was last emptied, g: every dose's
        settled reading; a dose that may have run without one counts as
        target + the overshoot guard."""
        doc = self.campaign.doc
        rc = self.operator.recycle_count
        total = 0.0
        for r in self.records:
            if (r.get("covariates") or {}).get("recycle_count", 0) != rc:
                continue
            s = r["summary"]
            if s["status"] in NOTHING_DOSED:
                continue
            g = s.get("settled_final_g")
            total += (max(0.0, g) if g is not None
                      else doc["target_g"] + self._guard_g())
        return total

    def check_limits(self, ask=False):
        """--unattended: CampaignEnd when the next dose (plus its Ax
        suggestion, when ``ask``) would overfill the cup or run past
        --stop-at."""
        args = self.args
        if not args.unattended:
            return
        doc = self.campaign.doc
        if args.cup_budget_g:
            load = self.cup_load_g()
            nxt = doc["target_g"] + self._guard_g()
            if load + nxt > args.cup_budget_g:
                raise CampaignEnd(
                    "cup budget: {:.2f} g in the cup, and the next dose "
                    "could add {:.2f} g over the {:.1f} g budget".format(
                        load, nxt, args.cup_budget_g))
        if self.stop_at is not None:
            import statistics
            recent = self.dose_wall_s[-5:]
            est = statistics.median(recent) if recent else 240.0
            if ask:
                est += self.ask_wall_s[-1] if self.ask_wall_s else 60.0
            left = self.stop_at - time.time()
            if est > left:
                raise CampaignEnd(
                    "deadline: {:.0f} s left before {}, the next dose "
                    "needs about {:.0f} s".format(max(0.0, left),
                                                  args.stop_at, est))

    def check_streaks(self):
        """--unattended: a run of stalls means the hopper/auger ran
        empty (nobody can refill it); a run of jams, that something
        physical is wrong.  Either ends the campaign."""
        args = self.args
        if not args.unattended:
            return
        stalls = jams = 0
        for r in reversed(self.records):
            s = r["summary"]
            if not self.usable(r) or not s["jam"]:
                break
            if s.get("jam_reason") == "stall" and stalls == jams:
                stalls += 1
            jams += 1
        if args.max_stall_streak and stalls >= args.max_stall_streak:
            raise CampaignEnd(
                "{} stalls in a row: the hopper or auger has probably run "
                "empty".format(stalls))
        if args.max_jam_streak and jams >= args.max_jam_streak:
            raise CampaignEnd("{} jams in a row".format(jams))

    # -- one dose, soup to nuts ----------------------------------------

    def run_trial(self, label, params, mode, ax_trial_index=None):
        doc = self.campaign.doc
        trial_index = len(self.records)
        trial_uuid = str(uuid.uuid4())
        self.check_limits()
        self.operator.cadence_prompt()
        tau = doc.get("tau_afterflow") or {}
        if mode in ("recenter", "bo", "validation") and tau.get("tau0_s"):
            params = dict(params, tau_afterflow_s=tau["tau0_s"])
        log("dose {} [{} {}]: {}".format(
            trial_index, mode, label,
            {k: (round(v, 4) if isinstance(v, float) else v)
             for k, v in params.items()}))
        # Write-ahead: until this dose's record lands, --resume asks the
        # Zero about this uuid instead of forgetting or re-dosing it.
        doc["in_flight"] = {
            "trial_uuid": trial_uuid, "trial_index": trial_index,
            "label": label, "mode": mode, "params": params,
            "covariates": dict(self.operator.covariates(),
                               cup_load_g=round(self.cup_load_g(), 4)),
            "ax_trial_index": ax_trial_index, "utc": oc.utcnow_iso()}
        self.save()
        t0 = time.monotonic()
        summary = self.executor.dose(
            doc["campaign_id"], trial_uuid, trial_index, self.powder_id,
            doc["target_g"], mode, oc.validate_params(params),
            doc["in_flight"]["covariates"], frozen=self.frozen_push())
        if summary["status"] == "unreachable":
            log("could not learn how {} ended: the Zero is unreachable. "
                "Nothing was re-dosed; --resume {} asks the Zero again"
                .format(label, doc["campaign_id"]))
            if self.args.unattended:
                raise CampaignEnd("the Zero became unreachable during "
                                  "{}".format(label))
            raise KeyboardInterrupt
        if summary["status"] not in NOTHING_DOSED:
            self.dose_wall_s.append(time.monotonic() - t0)
        record = self._finish_trial(doc["in_flight"], summary)
        if not summary["infra_error"]:
            self.infra_streak = 0
        self.check_streaks()
        return record

    def _finish_trial(self, flight, summary, recovered=False):
        log("  -> status={} t={} s |err|={} mg jam={}{}{}".format(
            summary["status"], summary["t_total_s"],
            summary["abs_error_mg"], summary["jam"],
            " INFRA-ERROR" if summary["infra_error"] else "",
            " (recovered from the Zero)" if recovered else ""))
        if summary["status"] in NOTHING_DOSED:   # no countdown, no
            spill, void, keep_going = False, None, True  # cadence tick
        else:
            if recovered and not self.args.simulate:
                print("    {} finished while the loop was down; flag it "
                      "now if it spilled or ran empty".format(
                          flight["label"]), flush=True)
            spill, void, keep_going = self.operator.after_dose(summary)
        record = {
            "label": flight["label"], "mode": flight["mode"],
            "trial_index": flight["trial_index"],
            "trial_uuid": flight["trial_uuid"],
            "ax_trial_index": flight.get("ax_trial_index"),
            "params": flight["params"],
            "summary": {k: v for k, v in summary.items()
                        if k != "stop_events"},
            "stop_events": summary.get("stop_events") or [],
            "spill": spill,
            "void": void,
            "recovered": recovered,
            "covariates": flight["covariates"],
            "utc": oc.utcnow_iso(),
        }
        self.records.append(record)
        self.campaign.append_record(record)
        self.campaign.doc["in_flight"] = None
        self.save()
        if (spill or void) and not self.args.simulate:
            try:
                db = oc.mongo_db()
                if db is not None:
                    db[oc.COLL_TRIALS].update_one(
                        {"trial_uuid": record["trial_uuid"]},
                        {"$set": {"flags.spill": spill,
                                  "flags.void": void}})
            except Exception as exc:
                log("spill/void flag mirror failed ({}); recorded locally"
                    .format(exc))
        if not keep_going:
            raise KeyboardInterrupt
        return record

    def reconcile(self):
        """Settle the dose that was in flight when the loop last stopped
        (section 5.4): record it from the Zero's spool if it ran, drop
        it if it never started -- never re-dose it blindly."""
        doc = self.campaign.doc
        flight = doc.get("in_flight")
        if not flight:
            return
        if any(r["trial_uuid"] == flight["trial_uuid"]
               for r in self.records):
            doc["in_flight"] = None               # recorded; stopped just
            self.save()                           # before clearing it
            return
        log("{} (trial {}) was in flight when the loop stopped -- asking "
            "the Zero how it ended".format(flight["label"],
                                           flight["trial_uuid"][:8]))
        summary = self.executor.fetch(flight["trial_uuid"],
                                      doc["campaign_id"])
        if summary["status"] == "unreachable":
            raise SystemExit(
                "cannot settle {} while the Zero is unreachable; nothing "
                "was re-dosed.  Run --resume again once SSH works".format(
                    flight["label"]))
        if summary["status"] == "not-found":
            log("the Zero never started it -- nothing was dosed; it will "
                "be dosed again")
            doc["in_flight"] = None
            self.save()
            return
        self._finish_trial(flight, summary, recovered=True)

    @staticmethod
    def usable(record):
        """A dose the model learns from: it ran to a real outcome (no
        infrastructure fault) and the operator did not void it."""
        return not record["summary"]["infra_error"] and not record.get("void")

    def _n_usable(self, mode):
        return sum(1 for r in self.records
                   if r["mode"] == mode and self.usable(r))

    def _done_labels(self, mode):
        return {r["label"] for r in self.records
                if r["mode"] == mode and self.usable(r)}

    def _stop_for(self, record):
        s = record["summary"]
        hint = {"rig-busy": BUSY_HINT,
                "not-found": "the Zero never ran it -- if its stderr above "
                             "shows an argparse error, its checkout is "
                             "older than this laptop's: git pull --ff-only "
                             "in ~/powder-doser"}.get(s["status"],
                                                     "fix the rig")
        if self.args.unattended:
            self.infra_streak += 1
            if s["status"] in ("rig-busy", "not-found") or \
                    self.infra_streak > 1:
                raise CampaignEnd("{} on {} ({})".format(
                    s["status"], record["label"], hint))
            log("{} on {} -- retrying the same point once in 30 s".format(
                s["status"], record["label"]))
            time.sleep(0 if self.args.simulate else 30)
            return
        log("{} on {} -- {}, then --resume {}".format(
            s["status"], record["label"], hint,
            self.campaign.doc["campaign_id"]))
        raise KeyboardInterrupt

    def overshoot_penalized(self, record):
        """Section 7.3: a margin campaign scores a dose that ended past
        the band like a jam (older campaigns keep the raw |error|)."""
        scoring = self.campaign.doc.get("scoring") or {}
        return (scoring.get("overshoot") == "penalized"
                and record["summary"]["status"] == "overshoot")

    def raw_data(self, record):
        s = record["summary"]
        return oc.ax_raw_data(
            {"t_total_s": s["t_total_s"], "abs_error_mg":
             s["abs_error_mg"]},
            jam=s["jam"], spill=record["spill"],
            overshoot=self.overshoot_penalized(record))

    # -- phases ---------------------------------------------------------

    def screening(self):
        doc = self.campaign.doc
        announced = False
        while True:
            done = self._done_labels("screen")
            plan = [(l, p) for l, p in doc["screening_plan"]
                    if l not in done]
            if not plan:
                break
            if not announced:
                log("screening: {} of {} doses remaining".format(
                    len(plan), len(doc["screening_plan"])))
                announced = True
            label, params = plan[0]         # a voided dose goes again
            record = self.run_trial(label, params, "screen")
            if record["summary"]["infra_error"]:
                self._stop_for(record)
        # tau fit from the screening stop events (section 2.8)
        if doc.get("tau_afterflow") is None:
            import fit_tau_afterflow as ft
            events = []
            for r in self.records:
                if r["mode"] == "screen" and self.usable(r) \
                        and not r["summary"]["jam"] and not r["spill"]:
                    events += r["stop_events"]
            fit = ft.fit_events(events)
            doc["tau_afterflow"] = fit
            log("tau_afterflow fit: {}".format(fit))
            if fit.get("tau0_s"):
                try:
                    # A --simulate fit must never shadow a real powder
                    # model: it stays in the campaign dir, off Mongo.
                    ft.upsert_powder_model(
                        self.powder_id, fit, doc["campaign_id"],
                        cache_dir=(self.campaign.dir
                                   if self.args.simulate else None),
                        upload=not self.args.simulate)
                except Exception as exc:
                    log("powder_models upsert failed ({}); fit kept in "
                        "the campaign doc".format(exc))
        else:
            log("tau_afterflow {} s carried over from {} -- no refit".format(
                doc["tau_afterflow"].get("tau0_s"),
                (doc.get("warm_start") or {}).get("campaign_id")))
        doc["phase"] = "recenter"
        self.save()

    def anchor_plan(self):
        """The doses re-run under the fitted tau: the screening plan's
        centers + baselines, or a warm-started campaign's checks."""
        doc = self.campaign.doc
        if doc.get("anchor_plan") is not None:
            return [(l, p) for l, p in doc["anchor_plan"]]
        return [("re" + l, p) for l, p in doc["screening_plan"]
                if l.startswith(ANCHOR_PREFIXES)]

    def recenter(self):
        """Re-dose every replicated anchor (centers + hand-tuned
        baselines) under the fitted tau, so the warm-start data and the
        BO regime share reference points (section 2.8).  A warm-started
        margin campaign runs its checks here instead (section 7.2)."""
        doc = self.campaign.doc
        if not (doc.get("tau_afterflow") or {}).get("tau0_s"):
            log("no usable tau fit -- skipping the re-centered anchors")
            doc["phase"] = "bo"
            self.save()
            return
        anchors = self.anchor_plan()
        while True:
            done = self._done_labels("recenter")
            todo = [(l, p) for l, p in anchors if l not in done]
            if not todo:
                break
            label, params = todo[0]
            record = self.run_trial(label, params, "recenter")
            if record["summary"]["infra_error"]:
                self._stop_for(record)
        doc["phase"] = "bo"
        self.save()

    def _init_ax(self):
        from ax.service.ax_client import AxClient
        if os.path.exists(self.campaign.snapshot_path):
            self.ax = AxClient.load_from_json_file(
                self.campaign.snapshot_path)
            return
        args = self.args
        self.ax = make_ax_client(args.model, args.sobol_trials, args.seed)
        create_experiment(self.ax, "{}_campaign".format(self.powder_id),
                          self.variant)
        doc = self.campaign.doc
        # Warm start: attach every screening + recenter dose as existing
        # data (the sample's attach_trial block); a margin campaign's
        # parent's usable doses go first, at the parent's own margin.
        attached = []
        warm = doc.get("warm_start")
        if warm:
            parent = self.parent_campaign(warm["campaign_id"])
            outside = []
            for r in parent.records():
                if not self.usable(r):
                    continue
                params = {k: v for k, v in r["params"].items()
                          if k != "tau_afterflow_s"}
                params["cutoff_margin_g"] = warm["cutoff_margin_g"]
                if not in_search_space(params, self.variant):
                    outside.append(r["label"])  # e.g. hand-picked values
                    continue
                _, idx = self.ax.attach_trial(ax_parameterization(params))
                self.ax.complete_trial(trial_index=idx,
                                       raw_data=self.raw_data(r))
                attached.append("{}/{}".format(warm["campaign_id"],
                                               r["label"]))
            warm["attached"] = len(attached)
            log("attached {} doses of {} at cutoff_margin_g {} g{}".format(
                len(attached), warm["campaign_id"], warm["cutoff_margin_g"],
                "; left out {} outside the box: {}".format(
                    len(outside), ", ".join(outside)) if outside else ""))
        n_parent = len(attached)
        for r in self.records:
            if r["mode"] not in ("screen", "recenter") or \
                    not self.usable(r):
                continue
            parameterization = ax_parameterization(r["params"])
            _, idx = self.ax.attach_trial(parameterization)
            self.ax.complete_trial(trial_index=idx,
                                   raw_data=self.raw_data(r))
            attached.append(r["label"])
        log("attached {} screening/anchor doses as existing data".format(
            len(attached) - n_parent))
        # Ax trial index -> dose label (oc.ax_trial_labels)
        doc["ax_attached"] = attached
        self.ax.save_to_json_file(self.campaign.snapshot_path)
        self.save()

    def _sync_ax(self):
        """Tell Ax every recorded BO dose it was never told -- the loop
        stopped between the record and complete_trial (a Ctrl-C at the
        countdown, a pause, a crash)."""
        from ax.core.base_trial import TrialStatus
        told = 0
        for r in self.records:
            idx = r.get("ax_trial_index")
            if r["mode"] != "bo" or idx is None or not self.usable(r):
                continue
            trial = self.ax.experiment.trials.get(idx)
            if trial is not None and trial.status == TrialStatus.RUNNING:
                self.ax.complete_trial(trial_index=idx,
                                       raw_data=self.raw_data(r))
                told += 1
        if told:
            log("told Ax {} recorded dose(s) it had not heard about".format(
                told))
            self.ax.save_to_json_file(self.campaign.snapshot_path)

    def _open_ax_trial(self):
        """-> (index, params) of an Ax trial that was asked but never
        told, else (None, None).  Dosing it again keeps the suggestion
        and Ax's one-running-trial limit (a stale RUNNING trial makes
        get_next_trial raise MaxParallelismReachedException)."""
        from ax.core.base_trial import TrialStatus
        for idx in sorted(self.ax.experiment.trials):
            trial = self.ax.experiment.trials[idx]
            if trial.status in (TrialStatus.RUNNING, TrialStatus.CANDIDATE,
                                TrialStatus.STAGED):
                return idx, dict(trial.arm.parameters)
        return None, None

    def bo(self):
        doc = self.campaign.doc
        self._init_ax()
        self._sync_ax()
        budget = doc["budget"]
        while True:
            done = self._n_usable("bo")
            if done >= budget:
                break
            idx, params = self._open_ax_trial()
            if idx is None:
                self.check_limits(ask=True)
                log("asking Ax for suggestion {}/{} (SAAS refits can take "
                    "minutes late in a campaign)".format(done + 1, budget))
                t0 = time.monotonic()
                params, idx = self.ax.get_next_trial()
                self.ask_wall_s.append(time.monotonic() - t0)
                # on disk before its dose starts
                self.ax.save_to_json_file(self.campaign.snapshot_path)
            else:
                log("dosing Ax trial {} again: it was asked before the "
                    "loop stopped, and never told".format(idx))
            record = self.run_trial("bo-{:03d}".format(done), params, "bo",
                                    ax_trial_index=idx)
            if record["summary"]["infra_error"]:
                self._stop_for(record)      # the trial stays open
                continue                    # (unattended: one retry)
            if not self.usable(record):
                continue                    # voided: same point again
            self.ax.complete_trial(trial_index=idx,
                                   raw_data=self.raw_data(record))
            self.ax.save_to_json_file(self.campaign.snapshot_path)
            self.save()
        doc["phase"] = "readout"
        self.save()

    def baseline_summary(self):
        """Medians of the clean hand-tuned baseline doses (a warm-started
        margin campaign: its checks), per tau regime (screening: the
        tuned 0.30 s; anchors: the fitted tau)."""
        import statistics
        out = {}
        for mode, key in (("screen", "tuned_tau"),
                          ("recenter", "fitted_tau")):
            rs = [r for r in self.records
                  if r["mode"] == mode and self.usable(r)
                  and r["label"].startswith(REFERENCE_PREFIXES)
                  and not r["summary"]["jam"] and not r["spill"]
                  and r["summary"]["t_total_s"] is not None]
            if rs:
                out[key] = {
                    "n": len(rs),
                    "median_t_total_s": statistics.median(
                        r["summary"]["t_total_s"] for r in rs),
                    "median_abs_error_mg": statistics.median(
                        r["summary"]["abs_error_mg"] for r in rs),
                }
        return out or None

    def readout(self):
        doc = self.campaign.doc
        # Observed feasible front: usable, no jam, no spill, and inside
        # the 180 s / 20 mg reference box (anything outside it adds no
        # hypervolume and is no operating point).
        pts = [(r["summary"]["t_total_s"], r["summary"]["abs_error_mg"],
                r) for r in self.records
               if self.usable(r) and not r["summary"]["jam"]
               and not r["spill"]
               and r["summary"]["t_total_s"] is not None
               and r["summary"]["abs_error_mg"] is not None
               and r["summary"]["t_total_s"] <= oc.THRESHOLD_T_TOTAL_S
               and r["summary"]["abs_error_mg"]
               <= oc.THRESHOLD_ABS_ERROR_MG
               and not self.overshoot_penalized(r)]
        front = []
        for t, e, r in sorted(pts, key=lambda x: (x[0], x[1])):
            if all(not (t2 <= t and e2 <= e and (t2 < t or e2 < e))
                   for t2, e2, _ in pts):
                front.append({"t_total_s": t, "abs_error_mg": e,
                              "label": r["label"], "mode": r["mode"],
                              "params": r["params"]})
        model_front = None
        if self.ax is None and os.path.exists(self.campaign.snapshot_path):
            from ax.service.ax_client import AxClient
            self.ax = AxClient.load_from_json_file(
                self.campaign.snapshot_path)
        if self.ax is not None:
            try:
                pareto = self.ax.get_pareto_optimal_parameters(
                    use_model_predictions=True)
                labels = oc.ax_trial_labels(self.records,
                                            doc.get("ax_attached"))
                model_front = [
                    {"trial_index": k, "label": labels.get(k),
                     "params": v[0], "predicted_means": v[1][0]}
                    for k, v in pareto.items()]
            except Exception as exc:
                log("model Pareto readout unavailable ({})".format(exc))
        base = self.baseline_summary()
        ref = (base or {}).get("fitted_tau") or (base or {}).get("tuned_tau")
        beating = [p for p in front
                   if ref and not any(x in p["label"]
                                      for x in ("baseline-", "check-"))
                   and p["t_total_s"] <= ref["median_t_total_s"]
                   and p["abs_error_mg"] <= ref["median_abs_error_mg"]]
        warm = doc.get("warm_start")
        ref_name = ("check point {} at {:.0f} mg".format(
            warm["check_point"], 1000.0 * warm["cutoff_margin_g"])
            if warm else "hand-tuned baseline")
        out = {"campaign_id": doc["campaign_id"],
               "observed_feasible_front": front,
               "model_pareto": model_front,
               "baseline": base,
               "reference": ref_name,
               "front_points_beating_baseline": [p["label"]
                                                 for p in beating]}
        path = os.path.join(self.campaign.dir, "pareto.json")
        with open(path, "w") as f:
            json.dump(out, f, indent=1, default=str)
        doc["status"] = ("finished" if self.args.unattended
                         else "readout-ready")
        self.save()
        log("=== observed feasible front ({} points) -> {}".format(
            len(front), path))
        for p in front:
            log("  t={:6.1f} s  |err|={:5.1f} mg  {}  {}".format(
                p["t_total_s"], p["abs_error_mg"], p["mode"], p["label"]))
        if ref:
            log("{} ({} doses): median t={:.1f} s, "
                "|err|={:.1f} mg; {} front point(s) match or beat it on "
                "both objectives".format(
                    ref_name, ref["n"], ref["median_t_total_s"],
                    ref["median_abs_error_mg"], len(beating)))
        log("pick a point, then run --validate-params with its params "
            "(see pareto.json)")

    # -- validation / profile (section 2.4 step 5) ----------------------

    def point_params(self, label):
        """--validate-point: the searched values the campaign's dose
        ``label`` ran with (its tau is the campaign's to set)."""
        doc = self.campaign.doc
        doses = [r for r in self.records if r["mode"] != "validation"]
        runs = [r for r in doses if r["label"] == label]
        if not runs:
            raise SystemExit(
                "campaign {} has no dose labelled {!r}; pick a label from "
                "its report.md or pareto.json (it has {} ... {})".format(
                    doc["campaign_id"], label,
                    ", ".join(r["label"] for r in doses[:2]),
                    ", ".join(r["label"] for r in doses[-2:])))
        params = {k: v for k, v in runs[-1]["params"].items()
                  if k != "tau_afterflow_s"}
        log("validating {} of campaign {}: {}".format(
            label, doc["campaign_id"], params))
        return oc.validate_params(params, self.variant)

    def validate(self, params, replicates, point=None):
        import statistics
        doc = self.campaign.doc
        params = {k: v for k, v in params.items()}
        prefix = "val-{}-".format(point) if point else "val-"
        results = []
        for i in range(replicates):
            while True:                     # a voided replicate goes again
                record = self.run_trial("{}{:02d}".format(prefix, i),
                                        dict(params), "validation")
                if record["summary"]["infra_error"]:
                    self._stop_for(record)
                if self.usable(record):
                    break
            results.append(record)
        errs = [r["summary"]["abs_error_mg"] for r in results
                if r["summary"]["abs_error_mg"] is not None]
        times = [r["summary"]["t_total_s"] for r in results
                 if r["summary"]["t_total_s"] is not None]
        clean = [r for r in results
                 if not r["summary"]["jam"] and not r["spill"]
                 and not self.overshoot_penalized(r)]
        stats = {
            "replicates": len(results),
            "clean": len(clean),
            "median_abs_error_mg": statistics.median(errs) if errs
            else None,
            "p95_abs_error_mg": (sorted(errs)[max(0, int(0.95 * len(errs))
                                                  - 1)] if errs else None),
            "p_within_10mg": (sum(1 for e in errs if e <= 10.0)
                              / len(errs)) if errs else None,
            "median_t_total_s": statistics.median(times) if times
            else None,
            # --unattended: nobody could flag a spill (records say None)
            "spills_observed": not self.args.unattended,
        }
        tau = (doc.get("tau_afterflow") or {}).get("tau0_s")
        profile = {
            "kind": "dosing_profile",
            "schema_version": oc.SCHEMA_VERSION,
            "profile_id": "{}-{}{}".format(
                doc["campaign_id"], point + "-" if point else "",
                utcstamp()),
            "powder_id": self.powder_id,
            "target_g": doc["target_g"],
            "variant": self.variant,
            "parameters": {k: params[k] for k, _f, _t
                           in oc.search_params(self.variant)},
            "point": point,                 # the dose it came from, if any
            "tau_afterflow_s": tau,
            # what the replicates ran: the snapshot plus its overrides
            # (e.g. log_to_flash off), so dose.py replays exactly that
            "frozen_params": dict(doc["frozen_params"],
                                  **(doc.get("frozen_overrides") or {})),
            "validation": stats,
            "validated": bool(errs) and len(clean) == len(results),
            "simulated": bool(self.args.simulate),
            "campaign_id": doc["campaign_id"],
            "git_commit": doc["git_commit"],
            "created_utc": oc.utcnow_iso(),
        }
        # A --simulate profile must never be dosed from: it stays in
        # the campaign dir (next to, not over, the sim powder file) and
        # off Mongo, where dose.py never looks.
        if self.args.simulate:
            cache = os.path.join(self.campaign.dir,
                                 "profile_{}.json".format(self.powder_id))
        else:
            os.makedirs(PROFILE_CACHE, exist_ok=True)
            cache = os.path.join(PROFILE_CACHE,
                                 "{}.json".format(self.powder_id))
        with open(cache, "w") as f:
            json.dump(profile, f, indent=1)
        uploaded = False
        if not self.args.simulate:
            try:
                db = oc.mongo_db()
                if db is not None:
                    db[oc.COLL_PROFILES].insert_one(dict(profile))
                    uploaded = True
            except Exception as exc:
                log("profile upload failed ({}); cached at {}".format(
                    exc, cache))
        doc["last_profile"] = {"profile_id": profile["profile_id"],
                               "point": point,
                               "validated": profile["validated"],
                               "validation": stats}
        # Every block, so several candidate points can be compared later
        # (opt_report.py lists them); the cache above keeps only the last.
        doc.setdefault("profiles", []).append(dict(
            doc["last_profile"], parameters=profile["parameters"],
            created_utc=profile["created_utc"]))
        doc["status"] = ("validated" if profile["validated"]
                         else "validation-failed")
        self.save()
        log("validation stats: {}".format(stats))
        log("profile {}{} (validated={}, uploaded={}) cached at {}".format(
            profile["profile_id"], " for " + point if point else "",
            profile["validated"], uploaded, cache))

    # -- top level -------------------------------------------------------

    def run(self):
        doc = self.campaign.doc
        args = self.args
        point = None
        if args.validate_point:             # a typo fails before any SSH
            point = args.validate_point
            params = self.point_params(point)
        elif args.validate_params:
            params = oc.validate_params(json.loads(args.validate_params),
                                        self.variant)
        try:
            self.reconcile()
            if args.validate_params or point:
                doc["status"] = "validating"
                self.validate(params, args.replicates, point=point)
                return
            doc["status"] = "running"
            if doc["phase"] == "screen":
                self.screening()
            if args.screen_only:
                doc["status"] = "paused"
                self.save()
                log("--screen-only: stopping after screening + tau fit; "
                    "--resume {} continues into BO".format(
                        doc["campaign_id"]))
                return
            if doc["phase"] == "recenter":
                self.recenter()
            if doc["phase"] == "bo":
                self.bo()
            if doc["phase"] == "readout":
                if args.unattended:
                    doc["stop_reason"] = "BO budget reached"
                self.readout()
        except CampaignEnd as end:
            if self.validating:
                # An unattended block cut short keeps its replicates in
                # the records but writes no profile, and leaves the
                # campaign's readout (pareto.json) and stop_reason alone.
                log("unattended validation block ends early: {}; no "
                    "profile written".format(end))
                doc["status"] = "validation-stopped"
                doc["validation_stop_reason"] = str(end)
                self.save()
                return
            # --unattended: no one will resume this; read out what the
            # campaign learned and mark it finished.
            log("unattended campaign ends: {}".format(end))
            doc["stop_reason"] = str(end)
            if self.ax is not None:
                self.ax.save_to_json_file(self.campaign.snapshot_path)
            self.save()
            self.readout()
        except KeyboardInterrupt:
            doc["status"] = "paused"
            if self.ax is not None:
                self.ax.save_to_json_file(self.campaign.snapshot_path)
            self.save()
            log("paused cleanly -- continue with: opt_campaign.py "
                "--powder-id {} --resume {}".format(
                    self.powder_id, doc["campaign_id"]))


def parse_args(argv=None):
    ap = argparse.ArgumentParser(
        description="issue #164 optimization campaign loop")
    ap.add_argument("--powder-id", required=True)
    ap.add_argument("--variant", choices=sorted(oc.VARIANTS), default=None,
                    help="new campaigns: three-stage (bulk -> PI trickle "
                         "-> taps, the default), three-stage-margin (the "
                         "same plus the trickle's cutoff margin, section "
                         "7), or bulk-tap (no PI trickle, section 6); with "
                         "--resume, only that variant's campaigns")
    ap.add_argument("--warm-start", metavar="CAMPAIGN_ID", default=None,
                    help="new three-stage-margin campaigns: the three-stage "
                         "campaign whose doses it attaches at their own "
                         "margin and whose corners it re-doses at 0 mg "
                         "(default: this powder's latest; 'none' = a cold "
                         "2^(9-4) screen)")
    ap.add_argument("--target-g", type=float, default=0.5)
    ap.add_argument("--budget", type=int, default=None,
                    help="BO doses after the screening block (default "
                         "{}; a resumed campaign keeps its own unless "
                         "this is given)".format(DEFAULT_BUDGET))
    ap.add_argument("--host", help="SSH target for the Pi Zero, "
                                   "e.g. pi@<zero-hostname>")
    ap.add_argument("--remote-repo", default="~/powder-doser",
                    help="repo checkout path on the Zero")
    ap.add_argument("--remote-python", default=DEFAULT_REMOTE_PYTHON,
                    help="interpreter on the Zero (falls back to "
                         "python3 when the path is absent)")
    ap.add_argument("--pico-port", default=None,
                    help="serial port on the Zero (default /dev/ttyACM0)")
    ap.add_argument("--takeover", action="store_true",
                    help="let each dose ctrl-C whatever another session "
                         "left running on the shared Pico (default: stop "
                         "with status rig-busy instead)")
    ap.add_argument("--resume", metavar="CAMPAIGN_ID", nargs="?",
                    const="latest",
                    help="continue a campaign; with no id, this powder's "
                         "latest one (the powder file's latest_campaign)")
    ap.add_argument("--baseline-reps", type=int, default=N_BASELINES,
                    help="doses at the hand-tuned trickle_params.py point "
                         "bracketing the screening block (0 = none; new "
                         "campaigns only)")
    ap.add_argument("--screen-only", action="store_true")
    ap.add_argument("--simulate", action="store_true",
                    help="dry-run the loop against the virtual plant")
    ap.add_argument("--model", choices=["saasbo", "moo"],
                    default="saasbo",
                    help="BO step model (moo = faster MAP-GP fallback)")
    ap.add_argument("--sobol-trials", type=int, default=2)
    ap.add_argument("--seed", type=int, default=999)
    ap.add_argument("--countdown", type=float, default=10.0)
    ap.add_argument("--cup-every", type=int, default=20)
    ap.add_argument("--park-after", type=int, default=10)
    ap.add_argument("--unattended", action="store_true",
                    help="nobody at the rig: no prompts, the cup is never "
                         "emptied, and the campaign ends (readout, no "
                         "resume) at the first limit below")
    ap.add_argument("--cup-budget-g", type=float, default=None,
                    help="--unattended: powder the balance can still take "
                         "on top of the cup, g (HR-100A: 102 g capacity "
                         "minus the cup); no dose starts that could "
                         "exceed it")
    ap.add_argument("--stop-at", metavar="UTC_ISO", default=None,
                    help="--unattended: start no dose that would not "
                         "finish by this time, e.g. 2026-09-29T04:00Z")
    ap.add_argument("--max-stall-streak", type=int, default=2,
                    help="--unattended: consecutive stalled doses that end "
                         "the campaign (empty hopper; 0 = never)")
    ap.add_argument("--max-jam-streak", type=int, default=3,
                    help="--unattended: consecutive jams that end the "
                         "campaign (0 = never)")
    ap.add_argument("--frozen-set", metavar="KEY=VALUE", action="append",
                    default=[],
                    help="new campaigns: change one frozen trickle_params "
                         "value for the whole campaign (repeatable), e.g. "
                         "bulk_halt_kf=1 or tap_burst_above_g=0.01")
    ap.add_argument("--no-flash-log", action="store_true",
                    help="push log_to_flash 0 with the frozen snapshot "
                         "(telemetry still comes back over serial)")
    ap.add_argument("--log-max-rows", type=int, default=None,
                    help="push this telemetry size with the frozen snapshot "
                         "(resumed campaigns too).  The Pico allocates the "
                         "buffer at boot (1200 rows on the 2026-09-30 "
                         "build); re-sizing it later to an older "
                         "snapshot's 2400 failed on the rig and turned "
                         "telemetry off for the dose")
    ap.add_argument("--state-dir", default=DEFAULT_STATE)
    ap.add_argument("--operator", default=None)
    val = ap.add_mutually_exclusive_group()
    val.add_argument("--validate-params", metavar="JSON",
                     help="run validation replicates at these params and "
                          "write the dosing profile (inside the powder's "
                          "latest campaign unless --resume names one)")
    val.add_argument("--validate-point", metavar="LABEL",
                     help="the same, at the values one of the campaign's "
                          "doses ran with, by its label in report.md or "
                          "pareto.json (e.g. bo-003, corner-09)")
    ap.add_argument("--replicates", type=int, default=8)
    args = ap.parse_args(argv)
    if (args.validate_params or args.validate_point) and not args.resume:
        args.resume = "latest"
    if args.validate_params and not args.variant:
        # validate inside the latest campaign of the params' own variant
        args.variant = oc.variant_of(json.loads(args.validate_params))
    return args


def main(argv=None):
    args = parse_args(argv)
    uri, source = oc.resolve_mongo_uri()
    if args.simulate:
        log("--simulate: state stays under {}; nothing goes to "
            "MongoDB".format(args.state_dir))
    elif uri:
        log("MongoDB ledger: {} database via {}".format(oc.DB_NAME,
                                                        source))
    elif not args.simulate:
        log("warning: no MongoDB URI found (checked ${}, ${}, {}) -- "
            "running local-only; the Zero still spools/uploads on its "
            "side".format(oc.MONGODB_URI_ENV,
                          oc.MONGODB_URI_ENV_FALLBACKS[0],
                          oc.MONGODB_ENV_FILE))
    Runner(args).run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
