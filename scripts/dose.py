#!/usr/bin/env python3
"""Production dosing from a saved profile (issue #164 §1.4; Pi Zero).

Looks up the newest validated ``dosing_profiles`` document for the
powder (falling back to the local cache written at campaign end, so
dosing works with no internet), pushes the FULL parameter set --
searched values, frozen snapshot, and the fitted tau_afterflow -- to
the Pico, runs the dose, and logs the result to ``opt_trials`` with a
``mode: "production"`` stamp, so production doses keep feeding the
same ledger a later cross-powder model will want.

    python3 scripts/dose.py --powder-id salt --target-g 0.5

Profiles are validated at one target mass; dosing another target is
expected to work and is logged as such (the trial document carries
both the profile id and the target actually dosed).
"""

import argparse
import json
import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import opt_common as oc                                       # noqa: E402
import opt_dose_capture as odc                                # noqa: E402

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROFILE_CACHE = os.path.join(REPO_ROOT, "data", "profiles")


def log(msg):
    print("[dose] {}".format(msg), file=sys.stderr, flush=True)


def load_profile(powder_id, profile_id=None):
    """Newest validated profile from Mongo, else the local cache."""
    try:
        db = oc.mongo_db()
    except Exception as exc:
        log("Mongo unreachable ({}); trying the local cache".format(exc))
        db = None
    if db is not None:
        query = {"powder_id": powder_id}
        if profile_id:
            query["profile_id"] = profile_id
        else:
            query["validated"] = True
        doc = db[oc.COLL_PROFILES].find_one(
            query, sort=[("created_utc", -1)])
        if doc is not None:
            doc.pop("_id", None)
            cache_profile(doc)
            return doc, "mongodb"
        log("no matching profile in Mongo; trying the local cache")
    cache = os.path.join(PROFILE_CACHE, "{}.json".format(powder_id))
    if os.path.exists(cache):
        with open(cache) as f:
            doc = json.load(f)
        if profile_id and doc.get("profile_id") != profile_id:
            return None, None
        return doc, cache
    return None, None


def cache_profile(doc):
    os.makedirs(PROFILE_CACHE, exist_ok=True)
    cache = os.path.join(PROFILE_CACHE,
                         "{}.json".format(doc["powder_id"]))
    with open(cache, "w") as f:
        json.dump(doc, f, indent=1)


def full_set_lines(profile):
    """Frozen snapshot first, then the searched values + tau on top.

    The searched 8 are hard-required (a failed echo aborts); frozen
    keys a newer firmware no longer knows are warned about and
    skipped -- the profile still dominates where it matters.
    """
    frozen = dict(profile.get("frozen_params") or {})
    frozen.pop("goal_mass_g", None)          # the CLI target wins
    soft = []
    for key in sorted(frozen):
        value = frozen[key]
        if isinstance(value, bool):
            soft.append("set {} {}".format(key, 1 if value else 0))
        elif isinstance(value, (int, float)):
            soft.append("set {} {:.6g}".format(key, value))
    params = dict(profile["parameters"])
    if profile.get("tau_afterflow_s") is not None:
        params["tau_afterflow_s"] = profile["tau_afterflow_s"]
    hard = oc.firmware_set_lines(oc.validate_params(params))
    return soft, hard


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--powder-id", required=True)
    ap.add_argument("--target-g", type=float, required=True)
    ap.add_argument("--profile", help="specific profile_id (default: "
                                      "newest validated)")
    ap.add_argument("--port", default="/dev/ttyACM0")
    ap.add_argument("--baud", type=int, default=115200)
    ap.add_argument("--out", default=odc.DEFAULT_OUT)
    ap.add_argument("--operator")
    ap.add_argument("--timeout-s", type=float, default=720.0)
    ap.add_argument("--pico-dir", default=oc.PICO_FIRMWARE_DIR,
                    help="trickle_tap folder on the Pico's flash")
    ap.add_argument("--takeover", action="store_true",
                    help="ctrl-C whatever runs on the shared Pico first")
    ap.add_argument("--no-upload", action="store_true")
    args = ap.parse_args(argv)

    powder_id = oc.normalize_powder_id(args.powder_id)
    profile, source = load_profile(powder_id, args.profile)
    if profile is None:
        raise SystemExit("no dosing profile for {!r} (run a campaign + "
                         "--validate-params first)".format(powder_id))
    if profile.get("simulated"):
        raise SystemExit("profile {} came from a --simulate campaign -- "
                         "refusing to dose real powder from it".format(
                             profile.get("profile_id")))
    log("profile {} from {} (validated={}, tau={} s)".format(
        profile.get("profile_id"), source, profile.get("validated"),
        profile.get("tau_afterflow_s")))

    campaign_id = "production-{}".format(powder_id)
    trial_uuid = str(uuid.uuid4())
    started = oc.utcnow_iso()
    spool = oc.spool_dir(args.out, campaign_id)
    raw_log = os.path.join(spool, "serial_{}.log".format(trial_uuid))

    soft, hard = full_set_lines(profile)
    try:
        sess = odc.PicoSession(args.port, args.baud, raw_log)
    except odc.RigBusy as exc:
        raise SystemExit("rig busy, not dosing: {}".format(exc))
    try:
        try:
            odc.ensure_runner(sess, pico_dir=args.pico_dir,
                              takeover=args.takeover)
        except odc.RigBusy as exc:
            raise SystemExit("rig busy, not dosing: {}".format(exc))
        for line in soft:
            key = line.split()[1]
            sess.send(line)
            ok, seen = sess.collect_until(
                lambda l: "[set] {} = ".format(key) in l, 5)
            if ok is None:
                log("frozen key {!r} not accepted by this firmware; "
                    "skipping".format(key))
        for line in hard:
            key = line.split()[1]
            sess.send(line)
            ok, _ = sess.collect_until(
                lambda l: "[set] {} = ".format(key) in l, 5)
            if ok is None:
                raise SystemExit("profile parameter {!r} rejected by the "
                                 "firmware -- not dosing".format(key))
        result_doc, status = odc.run_dose(sess, args.target_g,
                                          args.timeout_s)
        telemetry = odc.pull_telemetry(sess) if result_doc else (None, [])
    finally:
        sess.close()

    doc = oc.build_trial_doc(
        campaign_id=campaign_id, trial_uuid=trial_uuid, trial_index=-1,
        powder_id=powder_id, target_g=args.target_g, mode="production",
        params=profile["parameters"], result_doc=result_doc,
        telemetry_rows=telemetry[1], telemetry_header=telemetry[0],
        covariates={"profile_id": profile.get("profile_id"),
                    "profile_target_g": profile.get("target_g")},
        operator=args.operator, started_utc=started,
        repo_root=REPO_ROOT, raw_status=status)
    spool_path = oc.spool_trial(args.out, doc)
    uploaded = False
    if not args.no_upload:
        try:
            uploaded = oc.upload_trial(doc)
        except Exception as exc:
            log("upload failed ({}); spooled at {}".format(exc,
                                                           spool_path))
    out = doc["outcomes"]
    log("dose {}: {} in {} s, error {} mg (uploaded={})".format(
        trial_uuid[:8], doc["flags"]["status"], out["t_total_s"],
        out["error_mg"], uploaded))
    print(json.dumps(oc.trial_summary(doc, spool_path=spool_path,
                                      uploaded=uploaded)))
    return 0 if not doc["flags"]["infra_error"] else 4


if __name__ == "__main__":
    sys.exit(main())
