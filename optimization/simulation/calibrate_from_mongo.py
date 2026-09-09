#!/usr/bin/env python3
"""Calibrate the digital twin's per-powder coefficients from real battery data.

The `battery_runs` collection in MongoDB (`powder_doser` db) holds a uniform
characterization battery per powder (issue #116 / PR #131): baseline noise,
then rotation / speed / tap / refeed trials swept across tilt angle, then three
closed-loop three-phase doses.  The rotation block measures grams conveyed per
360 deg (== one auger revolution) at three commanded tilts, which is exactly the
twin's feed factor as a function of tilt -- so we can fit the twin's
`feed_factor_g_per_rev` (reference condition) and its tilt-gain shape
(`tilt_g0`, `tilt_exp`) directly from data instead of the provisional
plausible-order guesses currently in powder_sim.POWDERS.

Pipeline:
    1. pull battery_runs from MongoDB (falls back to the committed
       battery_snapshot.json when offline / no credentials);
    2. also (re)write battery_snapshot.json so the fit is reproducible offline;
    3. aggregate rotation yield per tilt per powder (median over reps),
       skipping runs flagged qc invalid_for_cross_powder_comparison;
    4. fit reference feed factor + tilt gain per powder;
    5. map the three benchmark slots (salt / lactose / AlSi10Mg) onto the
       best-matching real powders and write calibrated_powders.json.

Coordinate note: the battery `tilt_deg` is the COMMANDED servo/horn angle
(0 / 45 / 90 deg).  The twin speaks mounting-plate degrees (plate = horn / 2,
0..45), and the gear ratio is 2:1, so horn {0, 45, 90} -> plate {0, 22.5, 45}.
The twin's tilt gain is normalized to 1 at plate 45 deg (rig "vertical",
steepness s = sin(plate)/sin(45) = 1).  We fit in steepness space.

Usage:
    python calibrate_from_mongo.py                 # pull + fit + write JSON
    python calibrate_from_mongo.py --offline       # snapshot only, no Mongo
    python calibrate_from_mongo.py --report        # print fit table, no write
"""
from __future__ import annotations

import argparse
import json
import math
import os
import statistics
from pathlib import Path

HERE = Path(__file__).parent
SNAPSHOT = HERE / "battery_snapshot.json"
CAL_OUT = HERE / "calibrated_powders.json"

# horn (commanded) tilt -> plate deg -> steepness s = sin(plate)/sin(45)
SIN45 = math.sin(math.radians(45.0))


def horn_to_steepness(horn_deg: float) -> float:
    plate = horn_deg / 2.0
    return math.sin(math.radians(plate)) / SIN45


# --------------------------------------------------------------------------
# 1-2. pull battery_runs (Mongo) or load the committed snapshot
# --------------------------------------------------------------------------

def pull_from_mongo() -> list[dict]:
    """Fetch the fields we need from battery_runs.  Never prints credentials."""
    from pymongo import MongoClient

    uri = os.environ["MONGODB_URI"]
    client = MongoClient(uri, serverSelectionTimeoutMS=20000)
    db = client["powder_doser"]
    keep = {"_id": 0, "powder_id": 0}  # placeholder; we project explicitly below
    runs = []
    for r in db.battery_runs.find(
        {},
        {"_id": 0, "powder_id": 1, "powder": 1, "schema_version": 1,
         "started_utc": 1, "operator": 1, "notes": 1, "qc": 1,
         "dose_summary": 1, "trials": 1},
    ):
        runs.append({
            "powder_id": r.get("powder_id"),
            "powder": r.get("powder"),
            "schema_version": r.get("schema_version"),
            "started_utc": str(r.get("started_utc")),
            "operator": r.get("operator"),
            "notes": r.get("notes"),
            "qc": r.get("qc", {}),
            "dose_summary": r.get("dose_summary", {}),
            # keep only the compact numeric fields of each trial
            "trials": [
                {k: t.get(k) for k in
                 ("block", "phase", "tilt_deg", "trial", "rpm",
                  "before_g", "after_g", "delta_g", "flag")}
                for t in r.get("trials", [])
            ],
        })
    client.close()
    return runs


def load_runs(offline: bool) -> tuple[list[dict], str]:
    if not offline and os.environ.get("MONGODB_URI"):
        try:
            runs = pull_from_mongo()
            SNAPSHOT.write_text(json.dumps(runs, indent=1))
            return runs, f"MongoDB battery_runs (n={len(runs)}); snapshot refreshed"
        except Exception as exc:  # pragma: no cover - network dependent
            print(f"  ! Mongo pull failed ({type(exc).__name__}: {exc}); "
                  f"falling back to snapshot")
    if SNAPSHOT.exists():
        runs = json.loads(SNAPSHOT.read_text())
        return runs, f"committed snapshot {SNAPSHOT.name} (n={len(runs)})"
    raise SystemExit("no MONGODB_URI and no battery_snapshot.json to fall back on")


# --------------------------------------------------------------------------
# 3. aggregate rotation yield per tilt per powder
# --------------------------------------------------------------------------

def rotation_by_tilt(run: dict) -> dict[float, float]:
    """Median grams per 360 deg (one auger rev) at each commanded tilt."""
    by = {}
    for t in run["trials"]:
        if t.get("phase") != "rotation" or t.get("delta_g") is None:
            continue
        by.setdefault(t["tilt_deg"], []).append(t["delta_g"])
    return {tilt: statistics.median(v) for tilt, v in by.items() if v}


def tap_refeed_by_tilt(run: dict) -> dict[str, dict[float, float]]:
    out = {"tap": {}, "refeed": {}}
    for t in run["trials"]:
        if t.get("phase") in ("tap", "refeed") and t.get("delta_g") is not None:
            out[t["phase"]].setdefault(t["tilt_deg"], []).append(t["delta_g"])
    return {ph: {tilt: statistics.median(v) for tilt, v in d.items() if v}
            for ph, d in out.items()}


def valid(run: dict) -> bool:
    return bool(run.get("qc", {}).get("valid_for_cross_powder_comparison"))


def latest_valid_run(runs: list[dict], powder_id: str) -> dict | None:
    cand = [r for r in runs if r["powder_id"] == powder_id and valid(r)]
    if not cand:
        return None
    return max(cand, key=lambda r: r["started_utc"])


# --------------------------------------------------------------------------
# 4. fit reference feed factor + tilt gain
# --------------------------------------------------------------------------

def fit_tilt_gain(rot: dict[float, float]) -> dict:
    """Fit  ff(s) = base * G(s),  G(s) = g0 + (1-g0) s^p,  G(1)=1.

    Rotation gives ff at commanded tilts {0, 45, 90} horn deg -> steepness
    {0, ~0.541, 1}.  base = ff at s=1 (reference); g0 = ff(0)/ff(1);
    p solves the middle point exactly.  Falls back gracefully if the steep
    point is missing or the shape is non-monotonic (clamps p to [0.3, 3])."""
    pts = sorted((horn_to_steepness(h), y) for h, y in rot.items())
    s_vals = [s for s, _ in pts]
    y_vals = [y for _, y in pts]
    # reference = yield at the steepest available tilt (closest to s=1)
    base = y_vals[-1]
    if base <= 0:
        return {"base_g_per_rev": 0.0, "tilt_g0": 0.4, "tilt_exp": 1.0,
                "note": "no conveyance at steepest tilt"}
    # g0 from the flattest point (s ~ 0)
    s0, y0 = pts[0]
    g0 = max(0.02, min(0.98, y0 / base)) if s0 < 0.05 else 0.4
    # p from an intermediate point if one exists strictly between 0 and 1
    p = 1.0
    mids = [(s, y) for s, y in pts if 0.05 < s < 0.999]
    if mids:
        s_m, y_m = mids[len(mids) // 2]
        rhs = (y_m / base - g0) / (1.0 - g0)
        if 0.0 < rhs < 1.0:
            p = math.log(rhs) / math.log(s_m)
    p = max(0.3, min(3.0, p))
    return {"base_g_per_rev": round(base, 5), "tilt_g0": round(g0, 4),
            "tilt_exp": round(p, 3)}


def flow_index(rot: dict[float, float]) -> float:
    """A crude free-flow score in [0,1]: high when horizontal conveyance is a
    large fraction of steep conveyance (flows even flat)."""
    if not rot:
        return 0.3
    s_sorted = sorted(rot.items(), key=lambda kv: horn_to_steepness(kv[0]))
    y0, y_top = s_sorted[0][1], s_sorted[-1][1]
    if y_top <= 0:
        return 0.0
    return max(0.0, min(1.0, y0 / y_top))


def lowflow_rate(run: dict) -> float:
    """Fraction of conveying trials (rotation + refeed) flagged 'lowflow' -- the
    battery's own marker that the auger delivered essentially nothing, i.e. the
    powder failed to feed.  This is the cleanest cohesion signal in the data."""
    conv = [t for t in run["trials"]
            if t.get("phase") in ("rotation", "refeed")]
    if not conv:
        return 0.0
    return sum(1 for t in conv if (t.get("flag") or "") == "lowflow") / len(conv)


def fit_powder(run: dict) -> dict:
    rot = rotation_by_tilt(run)
    tr = tap_refeed_by_tilt(run)
    gain = fit_tilt_gain(rot)
    fi = flow_index(rot)
    tap45 = tr["tap"].get(45.0, 0.0)
    refeed45 = tr["refeed"].get(45.0, 1e-6)
    tap_release = tap45 / refeed45 if refeed45 > 1e-6 else 0.0
    # cohesion proxy (a documented heuristic, NOT a clean inversion).  Keyed on
    # signals that actually track poor flow rather than tilt geometry: the rate
    # of 'lowflow'-flagged trials (auger delivered ~nothing) and a low absolute
    # reference feed factor.  Tilt-sensitivity is NOT used -- every powder
    # conveys far more when steep, so the horizontal/steep ratio measures
    # geometry, not cohesion (it wrongly labelled free-flowing salt cohesive).
    lf = lowflow_rate(run)
    base = gain.get("base_g_per_rev", 0.0)
    low_ff_term = max(0.0, 1.0 - base / 0.15)   # ramps in below ~0.15 g/rev
    cohesion = round(max(0.03, min(0.9, 0.05 + 0.7 * lf + 0.25 * low_ff_term)), 3)
    return {
        "lowflow_rate": round(lf, 3),
        "source_powder_id": run["powder_id"],
        "source_run_utc": run["started_utc"][:10],
        "n_rotation_tilts": len(rot),
        "rotation_g_per_rev_by_horn_deg": {str(k): round(v, 5)
                                           for k, v in sorted(rot.items())},
        "fit": gain,
        "flow_index": round(fi, 3),
        "tap_release_ratio": round(tap_release, 3),
        "cohesion_proxy": cohesion,
        "qc_verdict": run.get("qc", {}).get("verdict"),
    }


# --------------------------------------------------------------------------
# 5. map benchmark slots -> real powders, emit calibrated twin params
# --------------------------------------------------------------------------

# Which real battery powder feeds each benchmark slot, and any prior params
# that stay fixed (not identifiable from the rotation battery).  Provenance and
# limitations are recorded in the JSON so the benchmark report can cite them.
SLOT_MAP = {
    # free-flowing reference; 08-12 run (tilt camera-verified) over 08-06
    "salt": {"source": "salt", "density_g_per_cm3": 1.20,
             "particle_size_um": 400.0, "moisture_sensitivity": 1.5,
             "hygroscopicity": 0.05, "angle_of_repose_deg": 32.0},
    # moderately cohesive pharma-relevant powder with a full valid tilt sweep
    "lactose": {"source": "calcium-lactate", "density_g_per_cm3": 0.80,
                "particle_size_um": 60.0, "moisture_sensitivity": 2.2,
                "hygroscopicity": 0.06, "angle_of_repose_deg": 42.0},
    # dense free-flowing metal; its own run had a TILT-SERVO FAULT (plate stuck
    # at 0 deg), so the tilt sweep is invalid -- we take the valid horizontal
    # feed factor and borrow a free-flowing tilt-gain prior, flagged below.
    "AlSi10Mg": {"source": "alsi10mg", "density_g_per_cm3": 1.45,
                 "particle_size_um": 45.0, "moisture_sensitivity": 0.8,
                 "hygroscopicity": 0.005, "angle_of_repose_deg": 27.0},
}


def build_calibrated(runs: list[dict]) -> dict:
    # fit every powder that has any rotation data, for the record
    all_fits = {}
    for pid in sorted({r["powder_id"] for r in runs}):
        run = latest_valid_run(runs, pid)
        tag = "valid"
        if run is None:  # fit the newest run anyway but mark invalid
            cand = [r for r in runs if r["powder_id"] == pid]
            run = max(cand, key=lambda r: r["started_utc"])
            tag = "qc-invalid"
        fit = fit_powder(run)
        fit["used"] = tag
        all_fits[pid] = fit

    slots = {}
    for slot, cfg in SLOT_MAP.items():
        src = cfg["source"]
        run = latest_valid_run(runs, src)
        note = ""
        if run is None:
            # AlSi10Mg case: no valid run; use the newest and flag the fault
            cand = [r for r in runs if r["powder_id"] == src]
            run = max(cand, key=lambda r: r["started_utc"])
            note = ("tilt-servo fault: tilt sweep invalid, feed factor taken "
                    "from the horizontal (plate 0) trials; tilt gain is a "
                    "free-flowing prior, not fit")
        fit = fit_powder(run)
        base = fit["fit"]["base_g_per_rev"]
        g0 = fit["fit"]["tilt_g0"]
        p = fit["fit"]["tilt_exp"]
        if note:  # AlSi10Mg: base here is the horizontal yield -> reconstruct
            # reference (plate 45) using a free-flowing gain prior (g0=0.6)
            horiz = fit["rotation_g_per_rev_by_horn_deg"].get("0.0", base)
            g0, p = 0.60, 0.8
            base = round(float(horiz) / g0, 5)
        slots[slot] = {
            "name": slot,
            "feed_factor_g_per_rev": base,
            "tilt_g0": g0,
            "tilt_exp": p,
            "cohesion": fit["cohesion_proxy"],
            "density_g_per_cm3": cfg["density_g_per_cm3"],
            "particle_size_um": cfg["particle_size_um"],
            "moisture_sensitivity": cfg["moisture_sensitivity"],
            "hygroscopicity": cfg["hygroscopicity"],
            "angle_of_repose_deg": cfg["angle_of_repose_deg"],
            "_provenance": {
                "source_powder_id": src,
                "source_run_utc": fit["source_run_utc"],
                "fit_from": "battery rotation block (g per 360 deg vs tilt)",
                "flow_index": fit["flow_index"],
                "limitation": note or "full valid tilt sweep",
            },
        }
    return {"slots": slots, "all_powder_fits": all_fits}


TWIN_KEYS = ("feed_factor_g_per_rev", "density_g_per_cm3", "cohesion",
             "moisture_sensitivity", "hygroscopicity", "angle_of_repose_deg",
             "particle_size_um", "tilt_g0", "tilt_exp")


def apply_calibration(powders: dict, path: Path = CAL_OUT) -> dict:
    """Return a copy of a POWDERS dict with the calibrated slots overridden.

    Used by the benchmark; leaves the module-level POWDERS untouched so the
    twin's unit tests keep their default-coefficient expectations."""
    from dataclasses import replace

    if not path.exists():
        return powders
    cal = json.loads(path.read_text())["slots"]
    out = dict(powders)
    for slot, params in cal.items():
        overrides = {k: params[k] for k in TWIN_KEYS if k in params}
        if slot in out:
            out[slot] = replace(out[slot], **overrides)
    return out


# --------------------------------------------------------------------------

def print_report(cal: dict) -> None:
    print("\n== per-powder rotation fits (all battery powders) ==")
    print(f"{'powder':<26}{'used':<12}{'ref g/rev':>10}{'g0':>7}{'exp':>7}"
          f"{'flow':>7}{'coh':>7}  qc")
    for pid, f in cal["all_powder_fits"].items():
        fit = f["fit"]
        print(f"{pid:<26}{f['used']:<12}{fit.get('base_g_per_rev', 0):>10.4f}"
              f"{fit.get('tilt_g0', 0):>7.2f}{fit.get('tilt_exp', 0):>7.2f}"
              f"{f['flow_index']:>7.2f}{f['cohesion_proxy']:>7.2f}  "
              f"{f.get('qc_verdict')}")
    print("\n== benchmark slots (twin overrides) ==")
    for slot, p in cal["slots"].items():
        prov = p["_provenance"]
        print(f"  {slot:<10} <- {prov['source_powder_id']:<16} "
              f"ff={p['feed_factor_g_per_rev']:.4f} g/rev  g0={p['tilt_g0']:.2f}"
              f"  exp={p['tilt_exp']:.2f}  coh={p['cohesion']:.2f}")
        print(f"             {prov['limitation']}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true",
                    help="use battery_snapshot.json, do not touch Mongo")
    ap.add_argument("--report", action="store_true",
                    help="print the fit table without writing calibrated JSON")
    args = ap.parse_args()

    runs, source = load_runs(args.offline)
    print(f"loaded {len(runs)} battery runs from {source}")
    cal = build_calibrated(runs)
    print_report(cal)
    if not args.report:
        CAL_OUT.write_text(json.dumps(cal, indent=1))
        print(f"\nwrote {CAL_OUT}")


if __name__ == "__main__":
    main()
