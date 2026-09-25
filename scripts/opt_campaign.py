#!/usr/bin/env python3
"""Issue #164 optimization campaign loop (runs on the laptop).

William's ``ax-platform==0.4.3`` Honegumi sample pointed at the rig
(docs/optimization/campaign-setup.md): ask Ax for a parameter set, run
ONE dose on the Pi Zero over SSH (``opt_dose_capture.py``), tell Ax the
outcomes, snapshot, repeat.  The only manual act is starting it:

    python scripts/opt_campaign.py --powder-id salt --target-g 0.5 \
        --budget 40 --host pi@<zero-hostname>

Campaign order per powder (section 2.4): a 2^(8-4) resolution-IV
screening fraction (16 corners) + 4 center points, then the per-powder
tau_afterflow fit from the screening stop events (section 2.8), then
the 4 centers re-dosed under the fitted tau, then the BO phase (SOBOL
sanity probes -> SAASBO / qNEHVI over the two objectives
minimize(t_total_s, abs_error_mg) with the locked 180 s / 20 mg
thresholds), then the Pareto readout.  All screening doses are attached
to Ax as existing data (the sample's ``attach_trial`` block) so BO
starts warm.

Operator interaction (section 1.2): between doses a short countdown
auto-continues -- touch nothing and the next dose starts, recorded as
"no spill"; ``s`` flags a spill on the dose just finished (penalized
per section 2.3), ``p`` pauses; several untouched countdowns in a row
park the loop.  The cup-empty / hopper-top-up cadence prompt
(``--cup-every``) hard-blocks, because it needs hands at the rig.

Interruptions are safe anywhere: every dose is atomic on the Zero
(same-uuid re-invocation returns the stored result), the Ax experiment
is snapshotted after every tell, and ``--resume <campaign_id>``
continues from the local state + snapshot without re-dosing.

``--simulate`` runs the identical loop against the PR #124 virtual
plant (the trickle_tap sim rig) instead of SSH -- no hardware, used by
scripts/tests and for shaking down the loop before a rig session.

Validation (section 2.4 step 5): after picking a point off the front,

    python scripts/opt_campaign.py --powder-id salt --target-g 0.5 \
        --host pi@zero --validate-params '{"bulk_tap": "off", ...}' \
        --replicates 8

doses the replicates and writes the ``dosing_profiles`` document (plus
a local cache under data/profiles/) that ``dose.py`` dispenses from.

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

N_CORNERS = 16          # 2^(8-4) resolution-IV fraction
N_CENTERS = 4


def log(msg):
    print("[campaign] {}".format(msg), flush=True)


def utcstamp():
    return datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y%m%dT%H%M%SZ")


# ---------------------------------------------------------------------------
# Screening design: 2^(8-4)_IV + centers (section 2.4, from #162 section 5)
# ---------------------------------------------------------------------------

def screening_plan(seed=42):
    """16 resolution-IV corners + 4 centers as campaign parameter dicts.

    Base factors A-D are the four tilts/RPM (full 2^4); the generators
    E=BCD, F=ACD, G=ABC, H=ABD (the standard minimum-aberration
    2^(8-4)_IV set) carry the threshold, the tolerance band, and the
    two tap categoricals -- which slot in natively as two-level
    factors.  Corner order is shuffled (seeded) per DOE practice;
    centers run at the box midpoints with both cadences off.
    """
    bounds = {p["name"]: p.get("bounds") for p in oc.SEARCH_SPACE_AX}

    def level(name, hi):
        lo_v, hi_v = bounds[name]
        return hi_v if hi > 0 else lo_v

    corners = []
    for i in range(N_CORNERS):
        a = 1 if i & 1 else -1
        b = 1 if i & 2 else -1
        c = 1 if i & 4 else -1
        d = 1 if i & 8 else -1
        e, f, g, h = b * c * d, a * c * d, a * b * c, a * b * d
        corners.append({
            "bulk_tilt_deg": level("bulk_tilt_deg", a),
            "trickle_tilt_deg": level("trickle_tilt_deg", b),
            "tap_tilt_deg": level("tap_tilt_deg", c),
            "bulk_rpm": level("bulk_rpm", d),
            "trickle_start_remaining_g": level("trickle_start_remaining_g",
                                               e),
            "tolerance_g": level("tolerance_g", f),
            "bulk_tap": oc.CAT_ON if g > 0 else oc.CAT_OFF,
            "trim_tap": oc.CAT_ON if h > 0 else oc.CAT_OFF,
        })
    import random
    random.Random(seed).shuffle(corners)
    center = {name: (b[0] + b[1]) / 2.0
              for name, b in bounds.items() if b}
    center.update({"bulk_tap": oc.CAT_OFF, "trim_tap": oc.CAT_OFF})
    plan = [("corner-{:02d}".format(i), p) for i, p in enumerate(corners)]
    plan += [("center-{:02d}".format(i), dict(center))
             for i in range(N_CENTERS)]
    return plan


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
                return json.loads(line)
        raise RuntimeError("no summary line from the Zero "
                           "(exit {})".format(proc.returncode))

    def dose(self, campaign_id, trial_uuid, trial_index, powder_id,
             target_g, mode, params, covariates):
        extra = ["--powder-id", powder_id, "--target-g", str(target_g),
                 "--campaign-id", campaign_id, "--trial", trial_uuid,
                 "--trial-index", str(trial_index), "--mode", mode,
                 "--params", json.dumps(params),
                 "--covariates", json.dumps(covariates)]
        if self.port:
            extra += ["--port", self.port]
        if self.operator:
            extra += ["--operator", self.operator]
        if self.takeover:
            extra += ["--takeover"]
        try:
            return self._invoke(extra, timeout_s=900)
        except (subprocess.TimeoutExpired, RuntimeError, OSError) as exc:
            log("dose invocation failed ({}); trying to fetch the "
                "stored result".format(exc))
            return self.fetch(trial_uuid, campaign_id)

    def fetch(self, trial_uuid, campaign_id, attempts=4, wait_s=30):
        for i in range(attempts):
            try:
                summary = self._invoke(
                    ["--fetch", trial_uuid, "--campaign-id", campaign_id],
                    timeout_s=60)
                if summary.get("status") != "not-found":
                    return summary
            except Exception as exc:
                log("fetch attempt {}/{} failed: {}".format(
                    i + 1, attempts, exc))
            if i + 1 < attempts:
                log("dose may still be running on the Zero; retrying the "
                    "fetch in {} s".format(wait_s))
                time.sleep(wait_s)
        return {"kind": "opt_trial_summary", "trial_uuid": trial_uuid,
                "status": "serial-error", "jam": False,
                "jam_reason": None, "infra_error": True,
                "t_total_s": None, "abs_error_mg": None,
                "error_mg": None, "settled_final_g": None, "taps": None,
                "stop_events": [], "parameters": None, "uploaded": False}


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
             target_g, mode, params, covariates):
        p_over = {
            "bulk_tap": params["bulk_tap"] == oc.CAT_ON,
            "trickle_tap": params["trim_tap"] == oc.CAT_ON,
            "bulk_tilt_deg": params["bulk_tilt_deg"],
            "trickle_tilt_deg": params["trickle_tilt_deg"],
            "tap_tilt_deg": params["tap_tilt_deg"],
            "bulk_rpm": params["bulk_rpm"],
            "trickle_start_remaining_g":
                params["trickle_start_remaining_g"],
            "tolerance_g": params["tolerance_g"],
        }
        if params.get("tau_afterflow_s") is not None:
            p_over["tau_afterflow_s"] = params["tau_afterflow_s"]
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
        return oc.trial_summary(doc) if doc else None


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


class Operator:
    def __init__(self, countdown_s, cup_every, park_after, simulate):
        self.countdown_s = countdown_s
        self.cup_every = cup_every
        self.park_after = park_after
        self.simulate = simulate
        self.untouched = 0
        self.doses_since_empty = 0
        self.recycle_count = 0

    def covariates(self):
        return {"doses_since_cup_empty": self.doses_since_empty,
                "recycle_count": self.recycle_count}

    def after_dose(self, summary):
        """The spill countdown.  Returns (spill, keep_going)."""
        self.doses_since_empty += 1
        if self.simulate or self.countdown_s <= 0:
            return False, True
        print("    countdown {}s -- [Enter]=next  s=SPILL on that dose  "
              "p=pause".format(self.countdown_s), flush=True)
        key = _read_key_with_timeout(self.countdown_s)
        if key is None:
            self.untouched += 1
            if self.park_after and self.untouched >= self.park_after:
                print("    {} untouched countdowns -- parking; press "
                      "Enter to resume".format(self.untouched), flush=True)
                try:
                    input()
                except EOFError:
                    return False, False
                self.untouched = 0
            return False, True
        self.untouched = 0
        if key in ("s", "S"):
            print("    SPILL recorded on trial {}".format(
                summary["trial_uuid"][:8]), flush=True)
            return True, True
        if key in ("p", "P"):
            print("    paused; press Enter to resume (Ctrl-C to stop "
                  "-- --resume continues later)", flush=True)
            try:
                input()
            except EOFError:
                return False, False
        return False, True

    def cadence_prompt(self):
        if self.simulate or not self.cup_every:
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

    def exists(self):
        return os.path.exists(self.path)

    def load(self):
        with open(self.path) as f:
            self.doc = json.load(f)
        return self.doc

    def save(self):
        self.doc["updated_utc"] = oc.utcnow_iso()
        with open(self.path, "w") as f:
            json.dump(self.doc, f, indent=1)
        try:
            db = oc.mongo_db()
            if db is not None:
                mirror = dict(self.doc)
                if os.path.exists(self.snapshot_path):
                    with open(self.snapshot_path) as f:
                        mirror["ax_snapshot"] = f.read()
                db[oc.COLL_CAMPAIGNS].replace_one(
                    {"campaign_id": self.campaign_id}, mirror, upsert=True)
        except Exception as exc:
            log("campaign mirror to Mongo failed ({}); local state is "
                "authoritative".format(exc))

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


def create_experiment(ax_client, name):
    from ax.service.ax_client import ObjectiveProperties
    ax_client.create_experiment(
        name=name,
        parameters=[dict(p) for p in oc.SEARCH_SPACE_AX],
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


def ax_parameterization(params):
    """Campaign params -> the Ax search-space dict (drops tau)."""
    return {name: params[name] for name, _k, _kind in oc.SEARCH_PARAMS}


# ---------------------------------------------------------------------------
# The loop
# ---------------------------------------------------------------------------

class Runner:
    def __init__(self, args):
        self.args = args
        self.powder_id = oc.normalize_powder_id(args.powder_id)
        state_root = args.state_dir
        if args.resume:
            self.campaign = Campaign(args.resume, state_root)
            if not self.campaign.exists():
                raise SystemExit("no local state for campaign {!r} under "
                                 "{}".format(args.resume, state_root))
            self.campaign.load()
        else:
            cid = "{}-{}".format(self.powder_id, utcstamp())
            self.campaign = Campaign(cid, state_root)
            self.campaign.doc = {
                "kind": "opt_campaign",
                "schema_version": oc.SCHEMA_VERSION,
                "campaign_id": cid,
                "powder_id": self.powder_id,
                "target_g": args.target_g,
                "status": "running",
                "phase": "screen",
                "created_utc": oc.utcnow_iso(),
                "operator": args.operator,
                "git_commit": oc.git_commit(REPO_ROOT),
                "simulate": bool(args.simulate),
                "search_space": oc.SEARCH_SPACE_AX,
                "objectives": {"t_total_s": oc.THRESHOLD_T_TOTAL_S,
                               "abs_error_mg": oc.THRESHOLD_ABS_ERROR_MG},
                "frozen_params": frozen_snapshot(),
                "screening_plan": screening_plan(args.seed),
                "tau_afterflow": None,
                "generation": {"model": args.model,
                               "sobol_trials": args.sobol_trials,
                               "seed": args.seed,
                               "ax_platform": "0.4.3"},
            }
            self.campaign.save()
        doc = self.campaign.doc
        if doc["powder_id"] != self.powder_id:
            raise SystemExit("campaign {} is for powder {!r}".format(
                doc["campaign_id"], doc["powder_id"]))

        if args.simulate:
            self.executor = SimExecutor(state_root, seed=args.seed)
        else:
            if not args.host:
                raise SystemExit("--host is required unless --simulate")
            self.executor = SSHExecutor(args.host, args.remote_repo,
                                        args.pico_port, args.operator,
                                        args.remote_python, args.takeover)
        self.operator = Operator(args.countdown, args.cup_every,
                                 args.park_after, args.simulate)
        self.records = self.campaign.records()
        if self.records:
            last_cov = self.records[-1].get("covariates") or {}
            self.operator.recycle_count = last_cov.get("recycle_count", 0)
        self.ax = None

    # -- one dose, soup to nuts ----------------------------------------

    def run_trial(self, label, params, mode):
        doc = self.campaign.doc
        trial_index = len(self.records)
        trial_uuid = str(uuid.uuid4())
        self.operator.cadence_prompt()
        tau = doc.get("tau_afterflow") or {}
        if mode in ("recenter", "bo", "validation") and tau.get("tau0_s"):
            params = dict(params, tau_afterflow_s=tau["tau0_s"])
        log("dose {} [{} {}]: {}".format(
            trial_index, mode, label,
            {k: (round(v, 4) if isinstance(v, float) else v)
             for k, v in params.items()}))
        covariates = self.operator.covariates()
        summary = self.executor.dose(
            doc["campaign_id"], trial_uuid, trial_index, self.powder_id,
            doc["target_g"], mode, oc.validate_params(params),
            covariates)
        log("  -> status={} t={} s |err|={} mg jam={}{}".format(
            summary["status"], summary["t_total_s"],
            summary["abs_error_mg"], summary["jam"],
            " INFRA-ERROR" if summary["infra_error"] else ""))
        if summary["status"] == "rig-busy":   # nothing dosed: no countdown,
            spill, keep_going = False, True   # no cup-cadence tick
        else:
            spill, keep_going = self.operator.after_dose(summary)
        record = {
            "label": label, "mode": mode, "trial_index": trial_index,
            "trial_uuid": trial_uuid, "params": params,
            "summary": {k: v for k, v in summary.items()
                        if k != "stop_events"},
            "stop_events": summary.get("stop_events") or [],
            "spill": spill,
            "covariates": covariates,
            "utc": oc.utcnow_iso(),
        }
        self.records.append(record)
        self.campaign.append_record(record)
        if spill:
            try:
                db = oc.mongo_db()
                if db is not None:
                    db[oc.COLL_TRIALS].update_one(
                        {"trial_uuid": trial_uuid},
                        {"$set": {"flags.spill": True}})
            except Exception as exc:
                log("spill flag mirror failed ({}); recorded locally"
                    .format(exc))
        if not keep_going:
            raise KeyboardInterrupt
        return record

    @staticmethod
    def usable(record):
        s = record["summary"]
        return not s["infra_error"]

    @staticmethod
    def raw_data(record):
        s = record["summary"]
        return oc.ax_raw_data(
            {"t_total_s": s["t_total_s"], "abs_error_mg":
             s["abs_error_mg"]},
            jam=s["jam"], spill=record["spill"])

    # -- phases ---------------------------------------------------------

    def screening(self):
        doc = self.campaign.doc
        done = {r["label"] for r in self.records if r["mode"] == "screen"
                and self.usable(r)}
        plan = [(l, p) for l, p in doc["screening_plan"] if l not in done]
        if plan:
            log("screening: {} of {} doses remaining".format(
                len(plan), len(doc["screening_plan"])))
        for label, params in plan:
            record = self.run_trial(label, params, "screen")
            if not self.usable(record):
                log("{} on {} -- {} and re-run with --resume {}".format(
                    record["summary"]["status"], label,
                    BUSY_HINT if record["summary"]["status"] == "rig-busy"
                    else "fix the rig", doc["campaign_id"]))
                raise KeyboardInterrupt
            self.campaign.save()
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
            doc["phase"] = "recenter"
            self.campaign.save()

    def recenter(self):
        doc = self.campaign.doc
        if not (doc.get("tau_afterflow") or {}).get("tau0_s"):
            log("no usable tau fit -- skipping the re-centered anchors")
            doc["phase"] = "bo"
            self.campaign.save()
            return
        done = sum(1 for r in self.records if r["mode"] == "recenter"
                   and self.usable(r))
        centers = [(l, p) for l, p in doc["screening_plan"]
                   if l.startswith("center")]
        for i in range(done, len(centers)):
            label, params = centers[i]
            record = self.run_trial("re" + label, params, "recenter")
            self.campaign.save()
            if not self.usable(record):
                log("{} on re{} -- {}, then --resume {}".format(
                    record["summary"]["status"], label,
                    BUSY_HINT if record["summary"]["status"] == "rig-busy"
                    else "fix the rig", doc["campaign_id"]))
                raise KeyboardInterrupt
        doc["phase"] = "bo"
        self.campaign.save()

    def _init_ax(self):
        from ax.service.ax_client import AxClient
        if os.path.exists(self.campaign.snapshot_path):
            self.ax = AxClient.load_from_json_file(
                self.campaign.snapshot_path)
            return
        args = self.args
        self.ax = make_ax_client(args.model, args.sobol_trials, args.seed)
        create_experiment(self.ax, "{}_campaign".format(self.powder_id))
        # Warm start: attach every screening + recenter dose as existing
        # data (the sample's attach_trial block).
        attached = 0
        for r in self.records:
            if r["mode"] not in ("screen", "recenter") or \
                    not self.usable(r):
                continue
            parameterization = ax_parameterization(r["params"])
            _, idx = self.ax.attach_trial(parameterization)
            self.ax.complete_trial(trial_index=idx,
                                   raw_data=self.raw_data(r))
            attached += 1
        log("attached {} screening/anchor doses as existing data".format(
            attached))
        self.ax.save_to_json_file(self.campaign.snapshot_path)

    def bo(self):
        doc = self.campaign.doc
        self._init_ax()
        done = sum(1 for r in self.records
                   if r["mode"] == "bo" and self.usable(r))
        budget = self.args.budget
        while done < budget:
            log("asking Ax for suggestion {}/{} (SAAS refits can take "
                "minutes late in a campaign)".format(done + 1, budget))
            params, idx = self.ax.get_next_trial()
            record = self.run_trial("bo-{:03d}".format(done), params, "bo")
            if not self.usable(record):
                self.ax.log_trial_failure(trial_index=idx)
                self.ax.save_to_json_file(self.campaign.snapshot_path)
                log("{} -- {}, then --resume {}".format(
                    record["summary"]["status"],
                    BUSY_HINT if record["summary"]["status"] == "rig-busy"
                    else "fix the rig", doc["campaign_id"]))
                raise KeyboardInterrupt
            self.ax.complete_trial(trial_index=idx,
                                   raw_data=self.raw_data(record))
            self.ax.save_to_json_file(self.campaign.snapshot_path)
            self.campaign.save()
            done += 1
        doc["phase"] = "readout"
        self.campaign.save()

    def readout(self):
        doc = self.campaign.doc
        # Observed feasible front: usable, no jam, no spill.
        pts = [(r["summary"]["t_total_s"], r["summary"]["abs_error_mg"],
                r) for r in self.records
               if self.usable(r) and not r["summary"]["jam"]
               and not r["spill"]
               and r["summary"]["t_total_s"] is not None]
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
                model_front = [
                    {"trial_index": k, "params": v[0],
                     "predicted_means": v[1][0]}
                    for k, v in pareto.items()]
            except Exception as exc:
                log("model Pareto readout unavailable ({})".format(exc))
        out = {"campaign_id": doc["campaign_id"],
               "observed_feasible_front": front,
               "model_pareto": model_front}
        path = os.path.join(self.campaign.dir, "pareto.json")
        with open(path, "w") as f:
            json.dump(out, f, indent=1, default=str)
        doc["status"] = "readout-ready"
        self.campaign.save()
        log("=== observed feasible front ({} points) -> {}".format(
            len(front), path))
        for p in front:
            log("  t={:6.1f} s  |err|={:5.1f} mg  {}  {}".format(
                p["t_total_s"], p["abs_error_mg"], p["mode"], p["label"]))
        log("pick a point, then run --validate-params with its params "
            "(see pareto.json)")

    # -- validation / profile (section 2.4 step 5) ----------------------

    def validate(self, params, replicates):
        import statistics
        doc = self.campaign.doc
        params = {k: v for k, v in params.items()}
        results = []
        for i in range(replicates):
            record = self.run_trial("val-{:02d}".format(i), dict(params),
                                    "validation")
            if self.usable(record):
                results.append(record)
            self.campaign.save()
        errs = [r["summary"]["abs_error_mg"] for r in results
                if r["summary"]["abs_error_mg"] is not None]
        times = [r["summary"]["t_total_s"] for r in results
                 if r["summary"]["t_total_s"] is not None]
        clean = [r for r in results
                 if not r["summary"]["jam"] and not r["spill"]]
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
        }
        tau = (doc.get("tau_afterflow") or {}).get("tau0_s")
        profile = {
            "kind": "dosing_profile",
            "schema_version": oc.SCHEMA_VERSION,
            "profile_id": "{}-{}".format(doc["campaign_id"], utcstamp()),
            "powder_id": self.powder_id,
            "target_g": doc["target_g"],
            "parameters": {k: params[k]
                           for k, _f, _t in oc.SEARCH_PARAMS},
            "tau_afterflow_s": tau,
            "frozen_params": doc["frozen_params"],
            "validation": stats,
            "validated": bool(errs) and len(clean) == len(results),
            "simulated": bool(self.args.simulate),
            "campaign_id": doc["campaign_id"],
            "git_commit": doc["git_commit"],
            "created_utc": oc.utcnow_iso(),
        }
        # A --simulate profile must never be dosed from: it stays in
        # the campaign dir and off Mongo, where dose.py never looks.
        cache_dir = (self.campaign.dir if self.args.simulate
                     else PROFILE_CACHE)
        os.makedirs(cache_dir, exist_ok=True)
        cache = os.path.join(cache_dir,
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
        log("validation stats: {}".format(stats))
        log("profile {} (validated={}, uploaded={}) cached at {}".format(
            profile["profile_id"], profile["validated"], uploaded, cache))

    # -- top level -------------------------------------------------------

    def run(self):
        doc = self.campaign.doc
        args = self.args
        if args.validate_params:
            self.validate(oc.validate_params(
                json.loads(args.validate_params)), args.replicates)
            return
        try:
            if doc["phase"] == "screen":
                self.screening()
            if args.screen_only:
                log("--screen-only: stopping after screening + tau fit; "
                    "--resume {} continues into BO".format(
                        doc["campaign_id"]))
                return
            if doc["phase"] == "recenter":
                self.recenter()
            if doc["phase"] == "bo":
                self.bo()
            if doc["phase"] == "readout":
                self.readout()
        except KeyboardInterrupt:
            doc["status"] = "paused"
            self.campaign.save()
            if self.ax is not None:
                self.ax.save_to_json_file(self.campaign.snapshot_path)
            log("paused cleanly -- continue with: opt_campaign.py "
                "--powder-id {} --resume {}".format(
                    self.powder_id, doc["campaign_id"]))


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="issue #164 optimization campaign loop")
    ap.add_argument("--powder-id", required=True)
    ap.add_argument("--target-g", type=float, default=0.5)
    ap.add_argument("--budget", type=int, default=40,
                    help="BO doses after the screening block")
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
    ap.add_argument("--resume", metavar="CAMPAIGN_ID")
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
    ap.add_argument("--state-dir", default=DEFAULT_STATE)
    ap.add_argument("--operator", default=None)
    ap.add_argument("--validate-params", metavar="JSON",
                    help="run validation replicates at these params and "
                         "write the dosing profile")
    ap.add_argument("--replicates", type=int, default=8)
    args = ap.parse_args(argv)
    uri, source = oc.resolve_mongo_uri()
    if uri:
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
