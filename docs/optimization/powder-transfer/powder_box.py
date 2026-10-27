#!/usr/bin/env python3
"""Powder properties -> a smaller, warm-started BO search (PR #166 example).

An example, not part of the campaign loop: it shows how a few cheap powder
measurements (a "fingerprint") can cut the search box of
``scripts/opt_campaign.py`` and carry data over from a related powder.
Nothing here changes how a campaign runs today.

The fingerprint is a handful of numbers the doser itself measures:

    q20, q100   bulk feed rate at 40 deg tilt, 20 and 100 rpm (g/s): the
                trailing-2 s slope at the bulk halt, which every RESULT stop
                event already records
    tau         tau_afterflow (s), the existing per-powder fit
                (scripts/fit_tau_afterflow.py)
    tap15       mass per tap cycle at tap tilt 15 deg (mg), pooled over the
                "[phase 3 tap] cycle N: ... (+X g this cycle)" log lines
    min_tilt    the lowest tilt at which the powder was seen to feed (deg)

Salt's come from its own campaign doses at those settings (what a short
fingerprint block before a campaign would measure), one set per session
group, because the rig changed between 10-06 and 10-13.  AlSi10Mg's bulk
feed is salt's scaled by the #116 battery's feed-factor ratio at 45 deg
(a powder property measured once per powder), and its tau and tap15 come from
its 09-29 production dose.  Al 4047's come from its clogged 09-30 doses.

Two rules turn a fingerprint into hard limits on the box.  Both only remove
regions the physics says fail, and both err toward keeping points:

R1  afterflow: the bulk halts ``thr + LEAD_G`` short of the goal (LEAD_G is
    measured on the salt halts) and then delivers about tau * Q(rpm) more,
    with Q linear in rpm between q20 and q100.  A dose whose afterflow can
    eat that gap overshoots, so keep thr + LEAD_G - tau * Q(rpm) >= SAFETY_G.
    That is one linear constraint in (bulk_rpm, trickle_start_remaining_g),
    which Ax takes as a parameter constraint.
R4  no feed: tilts below min_tilt do not feed.  If that leaves no trickle
    tilt in the box, the three-stage dose is the wrong structure (Al 4047
    with its clog: bulk-only, which landed +0.95 mg on 09-30).

Everything else the fingerprint knows (tap yield above all) is NOT turned
into a bound: tap tilt 0 looks hopeless at 0.2-0.6 mg per cycle, yet the
margin campaign's fastest dose (corner-03, 28 s) ran there because its
trickle finished the dose without a single tap.  Those properties go into the
model instead, as context inputs (``context()``; see ax_warm_start.py).

    python docs/optimization/powder-transfer/powder_box.py
    python docs/optimization/powder-transfer/powder_box.py --json boxes.json
"""
from __future__ import annotations

import argparse
import glob
import json
import math
import os
import random
import re
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(REPO, "scripts"))
import opt_common as oc  # noqa: E402

SALT_CAMPAIGNS = ("salt-20260929T014732Z", "salt-margin-20261013T191339Z")
TARGET_G = 0.5
# Session groups: 09-29 and 10-06 ran on a well-fed auger; on 10-13 and
# 10-15 the taps moved about 5x less per cycle and on 10-15 the feed
# collapsed (data/opt/salt-margin-20261013T191339Z/run_20261015.md).
SALT_SESSIONS = {"salt (09-29, 10-06)": ("2026-09-29", "2026-10-06"),
                 "salt (10-13, 10-15)": ("2026-10-13", "2026-10-15")}
# #116 battery feed factor at 45 deg tilt, mg/rev (as tabulated for #163 on
# branch claude/issue-163-20260918-2102 at e7b7964,
# data/powder-properties/battery_responses.csv)
FF45_MG_PER_REV = {"salt": 160.92, "alsi10mg": 230.95}
SAFETY_G = 0.010            # land the bulk at least 10 mg short of the band

TAP_LINE = re.compile(r"\[phase 3 tap\] cycle \d+: .*, ([-+]\d*\.\d+) g this "
                      r"cycle\)")


# ---------------------------------------------------------------------------
# Real doses
# ---------------------------------------------------------------------------

def tap_cycles_g(log_path):
    """Mass delivered by each tap cycle of one dose (g), in order."""
    if not os.path.exists(log_path):
        return []
    with open(log_path, errors="replace") as f:
        return [float(m.group(1)) for m in map(TAP_LINE.search, f) if m]


def _stop(events, phase):
    for e in events or []:
        if e.get("phase") == phase:
            return e
    return None


def salt_doses():
    """Every usable salt dose of both campaigns (validation included), with
    what the rules and the warm start need."""
    out = []
    for cid in SALT_CAMPAIGNS:
        root = os.path.join(REPO, "data", "opt", cid)
        times = {}
        for path in glob.glob(os.path.join(root, "zero", "trial_*.json")):
            with open(path) as f:
                doc = json.load(f)
            times[doc["trial_uuid"]] = doc["outcomes"]
        with open(os.path.join(root, "campaign_records.jsonl")) as f:
            records = [json.loads(line) for line in f if line.strip()]
        for r in records:
            s = r["summary"]
            if s.get("infra_error") or r.get("void"):
                continue
            p = dict(r["params"])
            p.setdefault("cutoff_margin_g", 0.035)  # the hand-tuned value
            bulk = _stop(r.get("stop_events"), "bulk")
            cycles = tap_cycles_g(os.path.join(
                root, "zero", "serial_{}.log".format(r["trial_uuid"])))
            out.append({
                "campaign_id": cid, "label": r["label"], "mode": r["mode"],
                "date": r["utc"][:10], "params": p, "status": s["status"],
                "jam": bool(s.get("jam")),
                "t_total_s": s["t_total_s"], "abs_error_mg": s["abs_error_mg"],
                "t_tap_s": (times.get(r["trial_uuid"]) or {}).get("t_tap_s"),
                "bulk": bulk, "tap_cycles_g": cycles,
                "feasible": (s["status"] == "ok"
                             and s["t_total_s"] <= oc.THRESHOLD_T_TOTAL_S
                             and s["abs_error_mg"] <= oc.THRESHOLD_ABS_ERROR_MG),
            })
    return out


def _median(values):
    values = [v for v in values if v is not None]
    return statistics.median(values) if values else None


def lead_g(doses):
    """How far short of the goal, beyond the threshold, the bulk halts:
    the firmware's fixed bulk anticipation less the halt's own lag."""
    return _median((TARGET_G - d["bulk"]["m_stop_g"])
                   - d["params"]["trickle_start_remaining_g"]
                   for d in doses if d["bulk"])


def pooled_tap_mg(doses, tilt=15.0):
    """Mass per tap cycle (mg) pooled over every cycle at ``tilt``:
    what sets how long a deficit takes to tap in."""
    cyc = [c for d in doses if d["params"]["tap_tilt_deg"] == tilt
           for c in d["tap_cycles_g"]]
    return 1000.0 * sum(cyc) / len(cyc) if cyc else None


def _q_at(doses, rpm):
    return _median(d["bulk"]["rate_slope_gps"] for d in doses
                   if d["bulk"] and d["params"]["bulk_tilt_deg"] == 40.0
                   and d["params"]["bulk_rpm"] == rpm)


# ---------------------------------------------------------------------------
# Fingerprints
# ---------------------------------------------------------------------------

def fingerprints(doses):
    with open(os.path.join(REPO, "data", "powder_models", "salt.json")) as f:
        tau_salt = json.load(f)["tau_afterflow"]["tau0_s"]
    fps = {}
    for name, dates in SALT_SESSIONS.items():
        sub = [d for d in doses if d["date"] in dates]
        fps[name] = {"q20": _q_at(sub, 20.0), "q100": _q_at(sub, 100.0),
                     "tau": tau_salt, "tap15": pooled_tap_mg(sub),
                     # every salt tilt in the box fed (trickle at 10 deg,
                     # taps at 0 deg)
                     "min_tilt": 0.0, "source": "{} salt doses".format(len(sub)),
                     "estimated": []}
    salt = fps["salt (09-29, 10-06)"]

    # AlSi10Mg: its one production dose (09-29, 8 g, bo-005 settings)
    root = os.path.join(REPO, "data", "opt", "production-alsi10mg", "zero")
    doc = json.load(open(glob.glob(os.path.join(root, "trial_*.json"))[0]))
    bulk = _stop(doc["stop_events"], "bulk")
    cyc = tap_cycles_g(os.path.join(root, "serial_{}.log".format(
        doc["trial_uuid"])))
    ratio = FF45_MG_PER_REV["alsi10mg"] / FF45_MG_PER_REV["salt"]
    fps["AlSi10Mg"] = {
        # the 8 g dose's halt came after 57 s of bulk, at steady flow
        # (0.265 g/s); a 0.5 g dose halts before that, so salt's 0.5 g
        # halt rates scaled by the #116 feed ratio stand in for it
        "q20": salt["q20"] * ratio, "q100": salt["q100"] * ratio,
        "q100_steady_8g": bulk["rate_slope_gps"],
        "tau": bulk["afterflow_g"] / bulk["rate_slope_gps"],   # one halt
        "tap15": 1000.0 * sum(cyc) / len(cyc),
        "min_tilt": 10.0,          # its trickle fed at 10 deg
        "source": "1 production dose + #116 feed ratio {:.2f}".format(ratio),
        "estimated": ["q20", "q100"]}

    # Al 4047 9fxeqt with the 09-30 clog (production-al4047-9fxeqt/README.md):
    # bulk at 40 deg / 100 rpm fell to 15 mg/s, the 10 deg trickle stalled
    # within 8 s, 240 tap cycles at 15 deg added about 14 mg, and the
    # bulk-only top-up fed at 40 deg only
    root = os.path.join(REPO, "data", "opt", "production-al4047-9fxeqt", "zero")
    doc = json.load(open(os.path.join(
        root, "trial_de4dd913-beca-41af-b61c-574960aacda6.json")))
    bulk = _stop(doc["stop_events"], "bulk")
    fps["Al 4047 (clogged)"] = {
        "q100": bulk["rate_slope_gps"],
        "q20": bulk["rate_slope_gps"] * salt["q20"] / salt["q100"],
        "tau": tau_salt, "tap15": 14.0 / 240, "min_tilt": 35.0,
        "source": "3 production doses", "estimated": ["q20", "tau"]}
    return fps


def context(fp):
    """The fingerprint as GP inputs: log10 of the bulk feed at 40 deg /
    20 rpm (g/s) and of the mass per tap cycle at 15 deg (mg)."""
    return {"ctx_log10_feed": round(math.log10(fp["q20"]), 4),
            "ctx_log10_tap": round(math.log10(fp["tap15"]), 4)}


# ---------------------------------------------------------------------------
# Fingerprint -> box
# ---------------------------------------------------------------------------

def afterflow_constraint(fp, lead):
    """R1 as (c, d): c*bulk_rpm - trickle_start_remaining_g <= d."""
    c = fp["tau"] * (fp["q100"] - fp["q20"]) / 80.0    # g per rpm
    d = lead - SAFETY_G - fp["tau"] * fp["q20"] + 20.0 * c
    return c, d


def reduced_box(fp, lead, variant=oc.VARIANT_THREE_STAGE_MARGIN):
    """Fingerprint -> {"variant", "space" (Ax parameters), "constraints"
    (Ax strings), "rules" (what each rule did)}."""
    space = {p["name"]: dict(p, bounds=list(p["bounds"])) if p.get("bounds")
             else dict(p) for p in oc.search_space_ax(variant)}
    rules, constraints = [], []

    # R4: no feed below min_tilt
    lo, hi = space["trickle_tilt_deg"]["bounds"]
    if fp["min_tilt"] > hi:
        rules.append(("R4", "no feed below {:.0f} deg, above the trickle-tilt "
                      "box's {:.0f} deg: search a bulk-only or bulk-tap dose "
                      "instead".format(fp["min_tilt"], hi)))
        return {"variant": "bulk-only", "space": None, "constraints": [],
                "rules": rules}
    for name in ("bulk_tilt_deg", "trickle_tilt_deg"):
        lo, hi = space[name]["bounds"]
        if fp["min_tilt"] > lo:
            space[name]["bounds"] = [fp["min_tilt"], hi]
            rules.append(("R4", "{} >= {:.0f}".format(name, fp["min_tilt"])))

    # R1: afterflow
    c, d = afterflow_constraint(fp, lead)
    rpm_lo, rpm_hi = space["bulk_rpm"]["bounds"]
    thr_lo, thr_hi = space["trickle_start_remaining_g"]["bounds"]
    need = lambda rpm: c * rpm - d                      # noqa: E731
    if need(rpm_hi) > thr_lo:
        if need(rpm_lo) > thr_lo:
            space["trickle_start_remaining_g"]["bounds"] = [
                round(min(need(rpm_lo), thr_hi), 4), thr_hi]
        if need(rpm_hi) > thr_hi:
            space["bulk_rpm"]["bounds"] = [rpm_lo, round((thr_hi + d) / c, 1)]
        constraints.append("{:.6g}*bulk_rpm - trickle_start_remaining_g <= "
                           "{:.6g}".format(c, d))
        rules.append(("R1", "threshold >= {:.3f} g at 20 rpm, {:.3f} g at "
                      "100 rpm".format(need(20.0), need(100.0))))
    return {"variant": variant, "space": list(space.values()),
            "constraints": constraints, "rules": rules}


def inside(params, box):
    """Is a parameterization inside a reduced box (bounds + constraints)?"""
    if box["space"] is None:
        return False
    for p in box["space"]:
        if p.get("bounds") and p["name"] in params:
            lo, hi = p["bounds"]
            if not lo - 1e-9 <= float(params[p["name"]]) <= hi + 1e-9:
                return False
    for con in box["constraints"]:
        lhs, rhs = con.split(" <= ")
        total, sign = 0.0, 1.0
        for tok in lhs.split():
            if tok in ("+", "-"):
                sign = 1.0 if tok == "+" else -1.0
                continue
            coef, _, name = tok.rpartition("*")
            total += sign * (float(coef) if coef else 1.0) * float(params[name])
        if total > float(rhs) + 1e-9:
            return False
    return True


def volume_fraction(box, variant=oc.VARIANT_THREE_STAGE_MARGIN, n=100000):
    """Share of the full box's continuous volume the reduced box keeps."""
    if box["space"] is None:
        return 0.0
    rng = random.Random(0)
    full = [p for p in oc.search_space_ax(variant) if p.get("bounds")]
    keep = sum(inside({p["name"]: rng.uniform(*p["bounds"]) for p in full},
                      box) for _ in range(n))
    return keep / n


# ---------------------------------------------------------------------------
# Checks against the salt doses
# ---------------------------------------------------------------------------

def afterflow_check(doses, fps, lead):
    """Per salt bulk halt: predicted vs measured afterflow, and whether the
    bulk alone overshot the band."""
    rows = []
    for name, dates in SALT_SESSIONS.items():
        fp = fps[name]
        for d in doses:
            b = d["bulk"]
            if d["date"] not in dates or not b or b.get("afterflow_g") is None:
                continue
            p = d["params"]
            q = fp["q20"] + (fp["q100"] - fp["q20"]) * (p["bulk_rpm"] - 20) / 80
            rows.append({
                "label": d["label"], "date": d["date"], "session": name,
                "rpm": p["bulk_rpm"], "thr": p["trickle_start_remaining_g"],
                "afterflow_g": b["afterflow_g"],
                "afterflow_halt_rate_g": fp["tau"] * b["rate_slope_gps"],
                "afterflow_prior_g": fp["tau"] * q,
                "bulk_overshoot": (b["settled_g"] - TARGET_G
                                   > p["tolerance_g"]),
                "overshoot": d["status"] == "overshoot",
                "excluded": not inside(p, {"space": [], "constraints": [
                    "{:.6g}*bulk_rpm - trickle_start_remaining_g <= {:.6g}"
                    .format(*afterflow_constraint(fp, lead))]}),
                "feasible": d["feasible"]})
    return rows


def retrospective(doses, boxes):
    """What each session's R1 box would have done to that session's
    campaign doses (validation replicates aside)."""
    out = {}
    for name, dates in SALT_SESSIONS.items():
        sub = [d for d in doses if d["date"] in dates
               and d["mode"] != "validation"]
        box = dict(boxes[name], space=[])          # R1 only: salt fed everywhere
        gone = [d for d in sub if not inside(d["params"], box)]
        out[name] = {
            "doses": len(sub),
            "overshoots": sum(d["status"] == "overshoot" for d in sub),
            "excluded": [(d["label"], d["status"], d["t_total_s"],
                          d["abs_error_mg"]) for d in gone],
            "excluded_overshoots": sum(d["status"] == "overshoot"
                                       for d in gone),
            "excluded_feasible": sum(d["feasible"] for d in gone),
            "feasible": sum(d["feasible"] for d in sub)}
    return out


def build():
    doses = salt_doses()
    lead = lead_g(doses)
    fps = fingerprints(doses)
    boxes = {}
    for name, fp in fps.items():
        boxes[name] = reduced_box(fp, lead)
        boxes[name]["volume_fraction"] = round(volume_fraction(boxes[name]), 4)
        boxes[name]["context"] = context(fp)
    return {"lead_g": round(lead, 4), "safety_g": SAFETY_G,
            "fingerprints": fps, "boxes": boxes,
            "retrospective": retrospective(doses, boxes),
            "afterflow_check": afterflow_check(doses, fps, lead)}, doses


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--json", help="write fingerprints, boxes and checks here")
    args = ap.parse_args(argv)
    res, _doses = build()
    print("LEAD_G = {lead_g} g (median over the salt bulk halts), SAFETY_G = "
          "{safety_g} g".format(**res))
    for name, fp in res["fingerprints"].items():
        box = res["boxes"][name]
        print("\n== {}  ({}; estimated: {})".format(
            name, fp["source"], ", ".join(fp["estimated"]) or "none"))
        print("   q20 {:.3f} g/s  q100 {:.3f} g/s  tau {:.2f} s  tap15 {:.2f} mg"
              "  min tilt {:.0f} deg  context {}".format(
                  fp["q20"], fp["q100"], fp["tau"], fp["tap15"],
                  fp["min_tilt"], box["context"]))
        for rule, text in box["rules"]:
            print("   {}: {}".format(rule, text))
        for con in box["constraints"]:
            print("   Ax parameter constraint: {}".format(con))
        changed = [p for p in box["space"] or [] if p.get("bounds") and
                   p["bounds"] != [b for q in oc.search_space_ax(
                       oc.VARIANT_THREE_STAGE_MARGIN) if q["name"] == p["name"]
                       for b in [q["bounds"]]][0]]
        for p in changed:
            print("   bounds: {} {}".format(p["name"], p["bounds"]))
        print("   keeps {:.1%} of the box's continuous volume, variant {}".format(
            box["volume_fraction"], box["variant"]))
    for name, r in res["retrospective"].items():
        print("\nretrospective, {}: {} campaign doses, {} overshoots; R1 "
              "excludes {} ({} overshoots, {} feasible); {} feasible in all"
              .format(name, r["doses"], r["overshoots"], len(r["excluded"]),
                      r["excluded_overshoots"], r["excluded_feasible"],
                      r["feasible"]))
        for lab in r["excluded"]:
            print("   excluded:", lab)
    rows = res["afterflow_check"]
    bulk_os = [r for r in rows if r["bulk_overshoot"]]
    print("\nbulk halts: {}; bulk alone overshot the band in {}, of which R1 "
          "excludes {}; R1 excludes {} halts in all".format(
              len(rows), len(bulk_os), sum(r["excluded"] for r in bulk_os),
              sum(r["excluded"] for r in rows)))
    if args.json:
        with open(args.json, "w") as f:
            json.dump(res, f, indent=1)
        print("wrote", args.json)


if __name__ == "__main__":
    main()
