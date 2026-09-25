"""Shared shapes and helpers for the issue #164 optimization campaign.

Imported by BOTH sides of the campaign so the Pi Zero executor
(``opt_dose_capture.py``, ``dose.py``) and the laptop optimizer
(``opt_campaign.py``, ``fit_tau_afterflow.py``) write identical
documents -- the "schema/helpers module" of
``docs/optimization/campaign-setup.md`` section 3.

Deliberately **stdlib-only** (the Zero has no numpy/torch); ``pymongo``
is imported lazily and only when a Mongo helper is actually used, so
offline captures spool locally exactly as PR #131 does.
"""

import datetime
import json
import os
import re
import subprocess

SCHEMA_VERSION = 1

# MongoDB layout -- same database + env-var conventions as PR #131.
DB_NAME = "powder_doser"
COLL_CAMPAIGNS = "opt_campaigns"
COLL_TRIALS = "opt_trials"
COLL_PROFILES = "dosing_profiles"
COLL_POWDER_MODELS = "powder_models"
MONGODB_URI_ENV = "MONGODB_URI"
# The repo's CI secret holding the rig-scoped Atlas user (readWrite on
# powder_doser only) -- the same value the Zero keeps on-device.
MONGODB_URI_ENV_FALLBACKS = ("PI_MONGODB_URI",)
# PR #131's on-device convention: `export MONGODB_URI='...'`, mode 600.
# Parsed directly (not shell-sourced) so credentials still resolve when
# the executor arrives over a non-interactive SSH invocation that never
# reads .bashrc/.profile.
MONGODB_ENV_FILE = "~/.config/powder-doser/env"

# The firmware's machine-parseable dose summary (trickle_controller).
RESULT_PREFIX = "RESULT "

# The trickle_tap build this code speaks to (trickle_controller.
# FIRMWARE_ID; the tests cross-check the two).  The Pico is shared with
# other sessions that load other firmware, so the executor refuses to
# dose on anything else.  That build lives in its own folder on the
# Pico's flash so its config.py / main_three_phase.py never replace
# the root-level modules other firmware imports (section 5.1).
FIRMWARE_ID = "trickle_tap/2026-09-25"
PICO_FIRMWARE_DIR = "/trickle_tap"

# Objective reference thresholds, locked 2026-09-22 (campaign-setup
# section 2.2).  Also the penalization ceilings for jam/spill doses.
THRESHOLD_T_TOTAL_S = 180.0
THRESHOLD_ABS_ERROR_MG = 20.0

# The 8-parameter search space (campaign-setup section 2.1 / 5.3).
# Campaign-space name -> firmware ``set`` key.  The two categoricals
# take CAT_VALUES; "on" means the fixed 2 Hz cadence.
CAT_OFF, CAT_ON = "off", "2hz"
CAT_VALUES = (CAT_OFF, CAT_ON)
SEARCH_PARAMS = (
    ("bulk_tap", "bulk_tap", "cat"),
    ("trim_tap", "trickle_tap", "cat"),
    ("bulk_tilt_deg", "bulk_tilt_deg", "float"),
    ("trickle_tilt_deg", "trickle_tilt_deg", "float"),
    ("tap_tilt_deg", "tap_tilt_deg", "float"),
    ("bulk_rpm", "bulk_rpm", "float"),
    ("trickle_start_remaining_g", "trickle_start_remaining_g", "float"),
    ("tolerance_g", "tolerance_g", "float"),
)
SEARCH_SPACE_AX = [
    {"name": "bulk_tap", "type": "choice", "is_ordered": False,
     "values": list(CAT_VALUES)},
    {"name": "trim_tap", "type": "choice", "is_ordered": False,
     "values": list(CAT_VALUES)},
    {"name": "bulk_tilt_deg", "type": "range", "bounds": [15.0, 40.0]},
    {"name": "trickle_tilt_deg", "type": "range", "bounds": [10.0, 30.0]},
    {"name": "tap_tilt_deg", "type": "range", "bounds": [0.0, 15.0]},
    {"name": "bulk_rpm", "type": "range", "bounds": [20.0, 100.0]},
    {"name": "trickle_start_remaining_g", "type": "range",
     "bounds": [0.05, 0.30]},
    {"name": "tolerance_g", "type": "range", "bounds": [0.003, 0.015]},
]
OBJECTIVE_NAMES = ("t_total_s", "abs_error_mg")

# Firmware DoseResult.status -> jam classification (campaign-setup
# section 2.3).  Everything else is either fine ("ok"/"overshoot") or
# an infrastructure fault that should be retried, not modeled.
JAM_REASONS = {
    "stalled": "stall",
    "cycle-budget": "tap-budget",
    "timeout": "timeout",
}
INFRA_STATUSES = ("scale-error", "not-tared", "no-result", "serial-error",
                  "rig-busy")


def utcnow_iso():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def normalize_powder_id(value):
    """Same slug rule as PR #131's characterize_capture."""
    slug = (value or "").strip().lower().replace(" ", "-")
    if not re.match(r"^[a-z0-9][a-z0-9._-]*$", slug):
        raise ValueError(
            "invalid powder id {!r}: use letters/digits/dash/underscore/"
            "dot, e.g. salt, xanthan, flour".format(value))
    return slug


def git_commit(repo_root=None):
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root or os.path.dirname(os.path.abspath(__file__)),
            stderr=subprocess.DEVNULL).decode().strip()
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Parameter translation: campaign space <-> firmware ``set`` lines
# ---------------------------------------------------------------------------

def validate_params(params):
    """Check a campaign-space parameterization; returns a clean copy."""
    clean = {}
    for name, _key, kind in SEARCH_PARAMS:
        if name not in params:
            raise ValueError("missing search parameter {!r}".format(name))
        value = params[name]
        if kind == "cat":
            if value not in CAT_VALUES:
                raise ValueError("{}={!r} not in {}".format(
                    name, value, CAT_VALUES))
            clean[name] = value
        else:
            clean[name] = float(value)
    extra = set(params) - set(clean) - {"tau_afterflow_s"}
    if extra:
        raise ValueError("unknown parameters: {}".format(sorted(extra)))
    if "tau_afterflow_s" in params and params["tau_afterflow_s"] is not None:
        clean["tau_afterflow_s"] = float(params["tau_afterflow_s"])
    return clean


def firmware_set_lines(params):
    """Campaign parameterization -> ordered ``set <key> <value>`` lines.

    Categoricals become the firmware's boolean knobs (``2hz`` -> 1,
    ``off`` -> 0); the optional ``tau_afterflow_s`` rides along when the
    campaign has a fitted per-powder value to push (section 2.8).
    """
    lines = []
    for name, key, kind in SEARCH_PARAMS:
        value = params[name]
        if kind == "cat":
            lines.append("set {} {}".format(key, 1 if value == CAT_ON else 0))
        else:
            lines.append("set {} {:.6g}".format(key, float(value)))
    if params.get("tau_afterflow_s") is not None:
        lines.append("set tau_afterflow_s {:.6g}".format(
            float(params["tau_afterflow_s"])))
    return lines


# ---------------------------------------------------------------------------
# Outcomes, flags, penalization
# ---------------------------------------------------------------------------

def classify_status(status):
    """-> (jam: bool, jam_reason: str|None, infra_error: bool)."""
    if status in JAM_REASONS:
        return True, JAM_REASONS[status], False
    if status in INFRA_STATUSES:
        return False, None, True
    return False, None, False


def outcomes_from_result(result_doc):
    """The section 2.6 outcome block from a firmware RESULT document."""
    err_mg = result_doc.get("error_mg")
    return {
        "t_bulk_s": result_doc.get("t_bulk_s"),
        "t_trickle_s": result_doc.get("t_trickle_s"),
        "t_tap_s": result_doc.get("t_tap_s"),
        "t_settle_s": result_doc.get("t_settle_s"),
        "t_total_s": result_doc.get("t_total_s"),
        "settled_final_g": result_doc.get("final_g"),
        "settled_final": bool(result_doc.get("settled_final")),
        "error_mg": err_mg,
        "abs_error_mg": abs(err_mg) if err_mg is not None else None,
        "overshoot": result_doc.get("status") == "overshoot",
        "taps": result_doc.get("taps"),
        "nudges": result_doc.get("nudges"),
        "auger_rev": result_doc.get("auger_rev"),
        "ff_g_per_rev": result_doc.get("ff_g_per_rev"),
    }


def ax_raw_data(outcomes, jam=False, spill=False):
    """Objective values for Ax, penalized per campaign-setup 2.3.

    A jam/spill dose reports the timeout ceiling / error cap (or the
    true value if worse) so the surrogate learns the region is bad
    instead of the trial being discarded.
    """
    t = outcomes.get("t_total_s")
    e = outcomes.get("abs_error_mg")
    if jam or spill or t is None or e is None:
        t = max(t or 0.0, THRESHOLD_T_TOTAL_S)
        e = max(e or 0.0, THRESHOLD_ABS_ERROR_MG)
    return {"t_total_s": float(t), "abs_error_mg": float(e)}


# ---------------------------------------------------------------------------
# Document builders
# ---------------------------------------------------------------------------

def build_trial_doc(campaign_id, trial_uuid, trial_index, powder_id,
                    target_g, mode, params, result_doc, telemetry_rows,
                    telemetry_header, covariates=None, operator=None,
                    started_utc=None, repo_root=None, raw_status=None):
    """One ``opt_trials`` document (campaign-setup sections 1.3 / 2.6)."""
    status = raw_status or (result_doc or {}).get("status") or "no-result"
    jam, jam_reason, infra = classify_status(status)
    outcomes = outcomes_from_result(result_doc or {})
    return {
        "kind": "opt_trial",
        "schema_version": SCHEMA_VERSION,
        "campaign_id": campaign_id,
        "trial_uuid": trial_uuid,
        "trial_index": trial_index,
        "powder_id": powder_id,
        "target_g": target_g,
        "mode": mode,
        "started_utc": started_utc,
        "ended_utc": utcnow_iso(),
        "operator": operator,
        "git_commit": git_commit(repo_root),
        "parameters": params,
        "parameters_executed": (result_doc or {}).get("params"),
        "outcomes": outcomes,
        "stop_events": (result_doc or {}).get("stop_events") or [],
        "flags": {
            "status": status,
            "jam": jam,
            "jam_reason": jam_reason,
            "infra_error": infra,
            # The balance cannot see spilled powder; the operator flags
            # it during the laptop countdown, which patches this field.
            "spill": None,
            "aborted": status not in ("ok", "overshoot"),
        },
        "covariates": covariates or {},
        "device": {
            "log_path": (result_doc or {}).get("log_path"),
            "dose_n": (result_doc or {}).get("dose_n"),
            "read_retries": (result_doc or {}).get("read_retries"),
            "baseline_g": (result_doc or {}).get("baseline_g"),
            "firmware": (result_doc or {}).get("fw"),
        },
        "telemetry": {
            "header": telemetry_header,
            "rows": telemetry_rows or [],
        },
    }


def trial_summary(doc, spool_path=None, uploaded=None):
    """The one-line JSON the executor prints to stdout for the laptop."""
    flags = doc["flags"]
    out = doc["outcomes"]
    return {
        "kind": "opt_trial_summary",
        "trial_uuid": doc["trial_uuid"],
        "trial_index": doc["trial_index"],
        "campaign_id": doc["campaign_id"],
        "mode": doc["mode"],
        "status": flags["status"],
        "jam": flags["jam"],
        "jam_reason": flags["jam_reason"],
        "infra_error": flags["infra_error"],
        "t_total_s": out["t_total_s"],
        "abs_error_mg": out["abs_error_mg"],
        "error_mg": out["error_mg"],
        "settled_final_g": out["settled_final_g"],
        "taps": out["taps"],
        "stop_events": doc["stop_events"],
        "parameters": doc["parameters"],
        "spool": spool_path,
        "uploaded": uploaded,
    }


# ---------------------------------------------------------------------------
# Spool + Mongo (write-local-first, PR #131 rule)
# ---------------------------------------------------------------------------

def spool_dir(out_root, campaign_id):
    path = os.path.join(out_root, campaign_id)
    os.makedirs(path, exist_ok=True)
    return path


def spool_trial(out_root, doc):
    """Write the full trial doc + append its summary line; returns path."""
    path = spool_dir(out_root, doc["campaign_id"])
    full = os.path.join(path, "trial_{}.json".format(doc["trial_uuid"]))
    with open(full, "w") as f:
        json.dump(doc, f)
    with open(os.path.join(path, "trials.jsonl"), "a") as f:
        f.write(json.dumps(trial_summary(doc, spool_path=full)) + "\n")
    return full


def find_spooled_trial(out_root, trial_uuid, campaign_id=None):
    """Locate a spooled trial doc by uuid; returns dict or None."""
    roots = ([os.path.join(out_root, campaign_id)] if campaign_id
             else [os.path.join(out_root, d)
                   for d in sorted(os.listdir(out_root))
                   if os.path.isdir(os.path.join(out_root, d))]
             if os.path.isdir(out_root) else [])
    name = "trial_{}.json".format(trial_uuid)
    for root in roots:
        full = os.path.join(root, name)
        if os.path.exists(full):
            with open(full) as f:
                return json.load(f)
    return None


def _env_file_uri(path, keys=(MONGODB_URI_ENV,) + MONGODB_URI_ENV_FALLBACKS):
    """First matching KEY=value from a #131-style env file, or None.

    Understands ``export KEY=value`` and bare ``KEY=value`` lines with
    optional single/double quotes -- enough for the file the Zero
    actually has, without shelling out.
    """
    try:
        with open(path) as f:
            lines = f.read().splitlines()
    except OSError:
        return None
    found = {}
    for line in lines:
        m = re.match(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)=(.*)$",
                     line)
        if not m:
            continue
        value = m.group(2).strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        found[m.group(1)] = value
    for key in keys:
        if found.get(key):
            return found[key]
    return None


def resolve_mongo_uri(uri=None, env_file=MONGODB_ENV_FILE):
    """-> (connection string or None, human-readable source label).

    Resolution order: explicit argument, ``$MONGODB_URI``,
    ``$PI_MONGODB_URI`` (the CI secret for the rig-scoped user), then
    the Zero's ``~/.config/powder-doser/env`` file.  The label names
    where the URI came from and never contains the URI itself, so it is
    always safe to log.
    """
    if uri:
        return uri, "explicit --uri"
    for name in (MONGODB_URI_ENV,) + MONGODB_URI_ENV_FALLBACKS:
        value = os.environ.get(name)
        if value:
            return value, "${}".format(name)
    path = os.path.expanduser(env_file)
    value = _env_file_uri(path)
    if value:
        return value, env_file
    return None, None


def mongo_db(uri=None):
    """The powder_doser database handle, or None (no URI / no pymongo).

    Never raises for a missing configuration -- offline operation must
    keep working -- but does raise on a genuinely bad connection so the
    caller can say so.
    """
    uri, _ = resolve_mongo_uri(uri)
    if not uri:
        return None
    import pymongo                      # lazy: optional on the Zero
    client = pymongo.MongoClient(uri, serverSelectionTimeoutMS=10000)
    return client[DB_NAME]


def upload_trial(doc, uri=None):
    """Upsert one trial document by trial_uuid; returns True on success."""
    db = mongo_db(uri)
    if db is None:
        return False
    db[COLL_TRIALS].replace_one({"trial_uuid": doc["trial_uuid"]},
                                doc, upsert=True)
    return True
