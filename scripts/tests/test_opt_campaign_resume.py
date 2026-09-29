"""Halt-and-resume tests for the issue #164 campaign loop -- no hardware.

Drives ``opt_campaign.Runner`` against the trickle_tap virtual plant
(``--simulate``) through a fault-injecting executor, and checks the
campaign-setup section 5.4 guarantees: a dose that happened is recorded
exactly once and never dosed again, a dose that never started is dosed
once, a voided (hopper-empty) dose is dosed again and never modeled,
Ax never keeps a stale running trial, and the powder file carries the
latest run with its iteration number.

The BO checks need ``ax-platform==0.4.3`` and are skipped without it
(the screening/anchor checks do not).

Run:  python3 scripts/tests/test_opt_campaign_resume.py
"""

import contextlib
import io
import json
import os
import shutil
import sys
import tempfile

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))            # scripts/

import opt_common as oc                                # noqa: E402

# Never touch the real ledger from a test.
for _name in (oc.MONGODB_URI_ENV,) + oc.MONGODB_URI_ENV_FALLBACKS:
    os.environ.pop(_name, None)
oc.MONGODB_ENV_FILE = os.path.join(tempfile.gettempdir(), "no-such-env")

import opt_campaign as ocamp                           # noqa: E402

_FAILURES = []


def check(what, ok):
    print("  {} {}".format("PASS" if ok else "FAIL", what))
    if not ok:
        _FAILURES.append(what)


try:
    import ax                                          # noqa: F401
    HAVE_AX = True
except ImportError:
    HAVE_AX = False


class Faulty:
    """The SimExecutor with scripted faults, keyed by dose attempt.

    before      -- the laptop stops before the Zero hears of the dose
    after       -- the dose runs and spools, then the laptop dies
    unreachable -- the dose runs and spools, but the result never
                   comes back over SSH
    rig-busy    -- the Zero refuses: another session holds the Pico
    """

    def __init__(self, inner, faults=None):
        self.inner = inner
        self.faults = dict(faults or {})
        self.attempts = 0
        self.dosed = []                # uuids that physically dosed

    def dose(self, campaign_id, trial_uuid, *args, **kw):
        fault = self.faults.pop(self.attempts, None)
        self.attempts += 1
        if fault == "before":
            raise KeyboardInterrupt
        if fault == "rig-busy":
            return oc.status_summary(trial_uuid, "rig-busy")
        summary = self.inner.dose(campaign_id, trial_uuid, *args, **kw)
        self.dosed.append(trial_uuid)
        if fault == "after":
            raise KeyboardInterrupt
        if fault == "unreachable":
            return oc.status_summary(trial_uuid, "unreachable")
        return summary

    def fetch(self, trial_uuid, campaign_id):
        return self.inner.fetch(trial_uuid, campaign_id)


def _args(state, *extra):
    return ocamp.parse_args(["--powder-id", "salt", "--simulate",
                             "--state-dir", state, "--model", "moo",
                             "--sobol-trials", "2"] + list(extra))


def _runner(state, faults=None, *extra):
    runner = ocamp.Runner(_args(state, *extra))
    runner.executor = Faulty(runner.executor, faults)
    return runner


def _quiet(fn, *args):
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
        return fn(*args)


def _powder_file(runner):
    with open(os.path.join(runner.campaign.dir, "salt.json")) as f:
        return json.load(f)["latest_campaign"]


def test_screening_halts():
    state = tempfile.mkdtemp(prefix="optresume-")
    try:
        # dose 3 runs, then the laptop dies before hearing the result
        r = _runner(state, {3: "after"}, "--screen-only")
        _quiet(r.run)
        cid = r.campaign.doc["campaign_id"]
        lost = r.executor.dosed[-1]
        check("laptop died mid-dose: loop paused with the dose in flight",
              r.campaign.doc["status"] == "paused"
              and r.campaign.doc["in_flight"]["trial_uuid"] == lost
              and len(r.records) == 3)
        pf = _powder_file(r)
        check("powder file: paused, iteration 3, in-flight dose named",
              pf["status"] == "paused" and pf["iteration"] == 3
              and pf["in_flight"]["trial_uuid"] == lost
              and "--resume {}".format(cid) in pf["resume"])

        # resume with no id: the Zero's stored result is recorded, and
        # that uuid is never dosed again
        r2 = _runner(state, {2: "unreachable"}, "--resume",
                     "--screen-only")
        check("--resume with no id finds the latest campaign",
              r2.campaign.doc["campaign_id"] == cid)
        _quiet(r2.run)
        rec = [x for x in r2.records if x["trial_uuid"] == lost]
        check("in-flight dose recovered from the Zero, not re-dosed",
              len(rec) == 1 and rec[0]["recovered"]
              and rec[0]["trial_index"] == 3
              and lost not in r2.executor.dosed)
        lost2 = r2.executor.dosed[-1]
        check("SSH result lost: paused, dose kept in flight",
              r2.campaign.doc["status"] == "paused"
              and r2.campaign.doc["in_flight"]["trial_uuid"] == lost2)

        # the laptop stops before the Zero ever hears of the next dose
        r3 = _runner(state, {0: "before"}, "--resume", cid,
                     "--screen-only")
        _quiet(r3.run)
        check("unreachable dose recovered on the next resume",
              sum(1 for x in r3.records if x["trial_uuid"] == lost2) == 1
              and lost2 not in r3.executor.dosed)
        never = r3.campaign.doc["in_flight"]["trial_uuid"]
        check("stopped before dosing: nothing dosed, still in flight",
              r3.executor.dosed == [] and never is not None)
        label = r3.campaign.doc["in_flight"]["label"]

        # a hopper-empty void on the first dose after resuming
        r4 = _runner(state, None, "--resume", cid, "--screen-only")
        real_after = r4.operator.after_dose

        def void_once(summary):          # the operator presses e, refills
            r4.operator.after_dose = real_after
            r4.operator.hopper_refills += 1
            return False, ocamp.VOID_EMPTY, True
        r4.operator.after_dose = void_once
        _quiet(r4.run)
        check("never-started dose dropped, then dosed exactly once",
              all(x["trial_uuid"] != never for x in r4.records)
              and sum(1 for x in r4.records if x["label"] == label
                      and r4.usable(x)) == 1)
        voided = [x for x in r4.records if x.get("void")]
        check("voided dose kept in the ledger, same point dosed again",
              len(voided) == 1 and voided[0]["label"] == label
              and r4.records[r4.records.index(voided[0]) + 1]["label"]
              == label)
        plan = r4.campaign.doc["screening_plan"]
        labels = [x["label"] for x in r4.records if r4.usable(x)]
        check("screening complete: every planned label exactly once",
              sorted(labels) == sorted(l for l, _ in plan))
        uuids = [x["trial_uuid"] for x in r4.records]
        check("no trial uuid recorded twice", len(uuids) == len(set(uuids)))
        check("tau fitted without the voided dose's stop events",
              (r4.campaign.doc.get("tau_afterflow") or {}).get("tau0_s")
              is not None)
        check("hopper refill counted as a covariate",
              r4.records[-1]["covariates"]["hopper_refills"] == 1)
        check("baseline doses open and close the block",
              plan[0][0] == "baseline-00" and plan[-1][0] == "baseline-01"
              and plan[0][1] == r4.campaign.doc["baseline_params"])
    finally:
        shutil.rmtree(state, ignore_errors=True)


def test_bo_halts():
    if not HAVE_AX:
        print("  SKIP ax-platform not installed")
        return
    import warnings
    warnings.filterwarnings("ignore")
    import logging
    logging.getLogger("ax").setLevel(logging.ERROR)
    from ax.core.base_trial import TrialStatus
    state = tempfile.mkdtemp(prefix="optresume-bo-")
    try:
        r = _runner(state, None, "--budget", "2", "--baseline-reps", "0")
        n_anchor = 20 + 4
        # dose n_anchor is the first BO dose: Ctrl-C at its countdown
        real_after = r.operator.after_dose

        def after(summary):
            if len(r.records) == n_anchor:
                raise KeyboardInterrupt
            return real_after(summary)
        r.operator.after_dose = after
        _quiet(r.run)
        bo_uuid = r.campaign.doc["in_flight"]["trial_uuid"]
        idx = r.campaign.doc["in_flight"]["ax_trial_index"]
        check("Ctrl-C at a BO countdown: paused, Ax trial left running",
              r.campaign.doc["status"] == "paused"
              and r.ax.experiment.trials[idx].status == TrialStatus.RUNNING)

        # resume: the dose is recorded and told; Ax does not raise
        # MaxParallelismReachedException; the next BO dose then hits a
        # busy rig
        r2 = _runner(state, {0: "rig-busy"}, "--resume")
        _quiet(r2.run)
        told = r2.ax.experiment.trials[idx]
        check("recovered BO dose told to Ax on resume",
              told.status == TrialStatus.COMPLETED
              and bo_uuid not in r2.executor.dosed)
        busy_idx = r2.records[-1]["ax_trial_index"]
        busy_params = dict(r2.ax.experiment.trials[busy_idx].arm.parameters)
        check("rig-busy on a BO dose: paused, its Ax trial kept open",
              r2.records[-1]["summary"]["status"] == "rig-busy"
              and r2.ax.experiment.trials[busy_idx].status
              == TrialStatus.RUNNING)

        r3 = _runner(state, None, "--resume")
        _quiet(r3.run)
        redo = [x for x in r3.records if x["ax_trial_index"] == busy_idx
                and r3.usable(x)]
        check("the open Ax trial is dosed again with the same parameters",
              len(redo) == 1
              and ocamp.ax_parameterization(redo[0]["params"])
              == busy_params)
        statuses = [t.status for t in r3.ax.experiment.trials.values()]
        check("campaign finishes: budget met, nothing left running",
              r3.campaign.doc["phase"] == "readout"
              and r3._n_usable("bo") == 2
              and TrialStatus.RUNNING not in statuses)
        pf = _powder_file(r3)
        check("powder file: readout-ready, bo 2/2, last dose named",
              pf["status"] == "readout-ready"
              and pf["progress"]["bo"] == [2, 2]
              and pf["last_dose"]["mode"] == "bo"
              and pf["iteration"] == len(r3.records))
    finally:
        shutil.rmtree(state, ignore_errors=True)


class _FakeCollection:
    def __init__(self):
        self.docs = {}

    def replace_one(self, flt, doc, upsert=False):
        self.docs[json.dumps(flt, sort_keys=True)] = json.loads(
            json.dumps(doc))

    def update_one(self, flt, update, upsert=False):
        key = json.dumps(flt, sort_keys=True)
        doc = self.docs.setdefault(key, dict(flt))
        doc.update(update.get("$set", {}))

    def find_one(self, flt):
        doc = self.docs.get(json.dumps(flt, sort_keys=True))
        return dict(doc, _id="x") if doc is not None else None


def test_restore_from_mongo():
    import fit_tau_afterflow as ft
    state = tempfile.mkdtemp(prefix="optresume-mongo-")
    colls = {}
    fake_db = type("DB", (), {"__getitem__": lambda self, name:
                              colls.setdefault(name, _FakeCollection())})()
    real, real_cache = oc.mongo_db, ft.MODEL_CACHE
    oc.mongo_db = lambda uri=None: fake_db
    ft.MODEL_CACHE = os.path.join(state, "powder_models")
    try:
        r = _runner(state, {5: "after"}, "--screen-only")
        r.args.simulate = False     # mirror as a real campaign would
        _quiet(r.run)
        cid = r.campaign.doc["campaign_id"]
        n = len(r.records)
        flight = r.campaign.doc["in_flight"]["trial_uuid"]
        shutil.rmtree(r.campaign.dir)                # laptop lost
        camp = ocamp.Campaign(cid, state)
        ok = _quiet(camp.restore_from_mongo)
        check("campaign rebuilt from the Mongo mirror",
              ok and len(camp.records()) == n
              and camp.load()["in_flight"]["trial_uuid"] == flight)
        pm = colls[oc.COLL_POWDER_MODELS].find_one({"powder_id": "salt"})
        check("powder_models carries latest_campaign in Mongo",
              pm is not None
              and pm["latest_campaign"]["campaign_id"] == cid
              and pm["latest_campaign"]["iteration"] == n)
    finally:
        oc.mongo_db, ft.MODEL_CACHE = real, real_cache
        shutil.rmtree(state, ignore_errors=True)


def main():
    for fn in (test_screening_halts, test_bo_halts,
               test_restore_from_mongo):
        print(fn.__name__)
        fn()
    if _FAILURES:
        print("\n{} check(s) FAILED: {}".format(len(_FAILURES),
                                                "; ".join(_FAILURES)))
        return 1
    print("\nall campaign halt/resume checks pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
