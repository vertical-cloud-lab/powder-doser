"""Do the tri-star's actuators need to be that big? (issue #204, 24 Nov)

Ethan asked whether the actuators have to be as big as the Actuonix P16-150s in the renders
(197 mm between holes when closed, hanging about 213 mm under the shelf).

What sets an actuator's size here is its stroke, not its force:

  * the load is the module's weight about its hinge.  This script takes it from the same mass model
    as stands.py (printed parts at 60% of solid PLA, NEMA 11 110 g, solenoid 40 g, powder at the
    auger's middle) on the gearless module with #203's tap bracket: 0.24 N m empty and 0.46 N m with
    250 g of powder, largest at 0 deg and nearly zero at 90 deg (the centre of mass ends up over the
    hinge).  The earlier runs used a flat 0.65 N m, the upper estimate for the geared module; that is
    reported too.
  * the stroke a tilt range needs is set by the lever: for 0-90 deg it is about 1.41 x the distance
    from the hinge to the rod pin (the chord of a 90 deg arc).  Today's pin is 105 mm from the hinge,
    so 0-90 deg takes 149 mm, hence the P16-150.  Every Actuonix model is (stroke + a fixed amount)
    long, so a shorter lever means a shorter actuator, at the cost of more force.

It sizes Actuonix's smaller actuators (P16-50/100, L16, L12, P8, PQ12; numbers from their datasheets)
on two mountings:

  floor  today's: the rod pin 45 mm below the hinge (the clevis block under the plate's floor), a mm
         behind it, the actuator hanging straight down under the shelf (mounts.py's kinematics).
  crank  a crank on the hinge axis beside the module, the actuator above the shelf pulling the crank
         pin up, as in L6 (crank_drive.py, 23 Nov, which places a P16-50 there).  The crank points (span/2) below the horizontal at 0 deg and as
         far above it at the end of the span, so the chord is vertical and the actuator hangs from a
         pivot straight above.

For each actuator, gearing, mounting and tilt span (0-90, 0-60, 0-45 deg) it takes the longest lever
whose stroke still covers the span (1 mm spare at each end; the floor mounting keeps its 5 mm at
0 deg), then reports the force at every tilt, the margins against the datasheet's peak-power force and
back-drive force, the tilt resolution, how long the moves take, and how far the actuator reaches below
the shelf (floor) or above it (crank).  It passes if the largest force is at most half the peak-power
force and at most half the back-drive force (so it holds the tilt with the power off, through taps).

    pip install cadquery trimesh python-fcl rtree vtk pillow numpy matplotlib scipy
    python actuator_size.py                  # about 3 min; actuator_size.json and renders/actuator_*.png
    python actuator_size.py --figures-only   # redraws the figures from actuator_size.json

Frames as in doserlib.py: unit frame of a module, hinge axis on x, +y behind the hinge, z up, hinge at
z = 0; tilt positive = rear up.  Nothing here was bought, printed or modelled in Onshape.
"""
from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path

import numpy as np

import doserlib as D
import components as K
import base as B
import leg_room as LR
import stands as ST

HERE = Path(__file__).resolve().parent
OUT = HERE / "renders"
SP = B.SP                                  # 32 mm: hinge axis to beaker axis
CC = K.CC                                  # 45: floor mounting's rod pin below the hinge
BOT, TOP = B.BOT, B.TOP                    # shelf underside / top, unit frame (-43.25 / -37.25)
G = 9.81e-3                                # N per gram
TILTS = np.arange(0.0, 90.001, 1.0)
SPANS = (90, 60, 45)
POWDERS = (0.0, 50.0, 250.0)
DESIGN_POWDER = 250.0
TAU_FLAT = 650.0                           # N mm: the earlier runs' flat figure (geared module + powder)
PRELOAD = 5.0                              # floor mounting: rod out at 0 deg, as mounts.py
SPARE = 1.0                                # stroke kept in hand at the far end (and at both ends on the crank)
A_MAX = 95.0                               # floor mounting: today's pin, 95 mm behind the hinge
A_MIN = 40.0                               # ... and no nearer than this: the actuator would stand in the vessel's way
R_MAX = 40.0                               # crank: longest crank (its pin stays clear of the shelf at 0 deg)
BRACKET = 9.3                              # U-bracket: pin to its base (L12 9.3, L16 and P16 9.1, P8 8)
FOOT = 4.0                                 # the hanger or post the bracket screws to
ARM = 8.0                                  # crank mounting: the arm over the pivot bracket (crank_drive.py)
MARGIN = 2.0                               # needed: peak-power force and back-drive force >= 2 x the load

# --------------------------------------------------------------------------- #
# Actuonix catalogue.  Sources: L12 datasheet Rev B (2015), L16 datasheet (2019), PQ12 datasheet Rev D
# (2019), P8 datasheet (2022); the P16 from #202's write-up (actuonix.com product pages, 3 Nov 2026) and
# RobotShop's P16-100-22 listing (peak power point; the 64:1's is not listed, so it is taken as 0.8 x its max
# force at half its no-load speed, the 22:1's ratio).  closed = hole-to-hole length, fully retracted.
# pp = peak power point (N, mm/s); v0 = no-load speed; fmax = max force lifted; bd = back-drive force.
# --------------------------------------------------------------------------- #
CAT = {
    "P16": dict(closed=lambda s: s + 47.0, strokes=(50, 100, 150), section=(20.0, 36.0), volts="12 V",
                control="-P + LAC board ($30), or -S", rc=False, price="$90",
                mass={150: None}, repeat={}, backlash=None, side={100: 15.0, 150: 10.0},
                gears={22: dict(pp=(40.0, 26.0), v0=46.0, fmax=50.0, bd=75.0),
                       64: dict(pp=(72.0, 9.0), v0=18.0, fmax=90.0, bd=200.0, pp_estimated=True)},
                draw=dict(housing=(5.0, 70.0), across=(-10.5, 25.5), tube=12.0, rod=8.0, hub=9.0, lug=4.75, tip=15.5)),
    "L16": dict(closed=lambda s: s + 68.0, strokes=(50, 100, 140), section=(18.0, 20.0), volts="12 V (-R 6 V)",
                control="-P + LAC, -S, or -R (RC servo pulse, 6 V)", rc=True, price="$80",
                mass={50: 56, 100: 74, 140: 84}, repeat={50: 0.3, 100: 0.4, 140: 0.5}, backlash=0.25,
                side={50: 40.0, 100: 30.0, 140: 20.0},
                gears={35: dict(pp=(50.0, 16.0), v0=32.0, fmax=50.0, bd=31.0),
                       63: dict(pp=(75.0, 10.0), v0=20.0, fmax=100.0, bd=46.0),
                       150: dict(pp=(175.0, 4.0), v0=8.0, fmax=200.0, bd=102.0)},
                draw=dict(housing=(6.0, 53.0), across=(-8.0, 12.0), tube=12.0, rod=9.0, hub=9.0, lug=5.0, tip=12.0)),
    "L12": dict(closed=lambda s: s + 52.0, strokes=(30, 50, 100), section=(15.0, 18.0), volts="6 or 12 V (-R 6 V)",
                control="-P + LAC, -S, -I, or -R (RC servo pulse, 6 V; 30/50/100 mm)", rc=True, price=None,
                mass={10: 28, 30: 34, 50: 40, 100: 56}, repeat={10: 0.1, 30: 0.2, 50: 0.3, 100: 0.5}, backlash=0.2,
                side={10: 50.0, 30: 40.0, 50: 30.0, 100: 15.0},
                gears={50: dict(pp=(12.0, 11.0), v0=23.0, fmax=12.0, bd=20.0),
                       100: dict(pp=(23.0, 6.0), v0=12.0, fmax=23.0, bd=40.0),
                       210: dict(pp=(45.0, 2.5), v0=5.0, fmax=45.0, bd=80.0)},
                draw=dict(housing=(4.5, 37.0), across=(-7.5, 10.5), tube=12.0, rod=6.0, hub=9.0, lug=4.5, tip=11.0)),
    "P8": dict(closed=lambda s: s + 35.0, strokes=(25, 50, 100), section=(11.0, 25.0), volts="12 V",
               control="-P + LAC or Actuonix's Ext-R board (RC pulse), or -S", rc=False, price="$85 (P8-100)",
               mass={10: 24, 25: 26, 50: 32, 75: 38, 100: 41}, repeat={10: 0.1, 25: 0.2, 50: 0.3, 75: 0.4, 100: 0.5},
               backlash=0.3, side={10: 5.0, 25: 5.0, 50: 3.0, 75: 2.0, 100: 2.0},
               gears={50: dict(pp=(26.0, 15.0), v0=30.0, fmax=35.0, bd=10.0),
                      165: dict(pp=(80.0, 4.8), v0=9.2, fmax=110.0, bd=40.0),
                      252: dict(pp=(122.0, 3.0), v0=6.2, fmax=155.0, bd=65.0)},
               draw=dict(parallel=True, across=(-5.0, 20.0), rod=6.6, hub=6.6, lug=3.3, tip=8.4)),
    "PQ12": dict(closed=lambda s: 42.0, strokes=(20,), section=None, volts="6 or 12 V (-R 6 V)",
                 control="-P + LAC, -S, or -R (RC servo pulse, 6 V)", rc=True, price=None,
                 mass={20: 15}, repeat={20: 0.1}, backlash=0.25, side={20: 10.0},
                 gears={30: dict(pp=(15.0, 15.0), v0=28.0, fmax=18.0, bd=9.0),
                        63: dict(pp=(30.0, 8.0), v0=15.0, fmax=45.0, bd=25.0),
                        100: dict(pp=(40.0, 6.0), v0=10.0, fmax=50.0, bd=35.0)},
                 draw=None),
}
PQ12_NOTE = "closed length 42 mm from a retailer listing (no dimensioned drawing found); not drawn"


def model(fam, stroke, gear):
    tail = {"L12": "-6-R", "L16": "-6-R", "PQ12": "-6-R"}.get(fam, "-12-P")
    return f"{fam}-{stroke}-{gear}{tail}" if fam != "PQ12" else f"PQ12-{gear}{tail}"


# --------------------------------------------------------------------------- #
# the load: gravity torque about the hinge, from stands.py's mass model
# --------------------------------------------------------------------------- #
_TAU: dict = {}


def torque_curve(powder):
    """Torque the actuator has to hold (N mm, + = rear up) at each tilt in TILTS, and the module's mass and
    centre of mass at 0 deg."""
    if powder not in _TAU:
        ST.M_POWDER = powder
        coarse = np.arange(0.0, 90.001, 5.0)
        tau, info = [], None
        for t in coarse:
            ms = ST.masses(LR.module_parts("L5", float(t), np.eye(4), "A"))
            m = sum(x[0] for x in ms)
            cg = sum(x[0] * x[1] for x in ms) / m
            tau.append(m * cg[1] * 9.81e-3)
            if t == 0.0:
                info = dict(mass_g=round(m, 1), cg_behind_hinge_mm=round(float(cg[1]), 1),
                            cg_above_hinge_mm=round(float(cg[2]), 1))
        info["torque_5deg_Nmm"] = [round(float(x), 2) for x in tau]
        _TAU[powder] = (np.interp(TILTS, coarse, tau), info)
    return _TAU[powder]


# --------------------------------------------------------------------------- #
# kinematics (module plane: y behind the hinge, z up)
# --------------------------------------------------------------------------- #
def floor_pin(t, a):
    r = math.radians(t)
    return np.array([a * math.cos(r) + CC * math.sin(r), a * math.sin(r) - CC * math.cos(r)])


def floor_geometry(a, C, span):
    """Pin at (a, -45), base pin straight below it at 0 deg, (C + 5) away.  Lengths over 0..span."""
    Bp = floor_pin(0.0, a) + np.array([0.0, -(C + PRELOAD)])
    tl = TILTS[TILTS <= span + 1e-9]
    L = np.array([np.linalg.norm(floor_pin(t, a) - Bp) for t in tl])
    return dict(tilts=tl, L=L, base=Bp, extend=True)


def crank_pin(t, R, span):
    b = math.radians(-span / 2.0 + t)
    return np.array([R * math.cos(b), R * math.sin(b)])


def crank_geometry(R, C, span):
    """Crank of radius R; the actuator hangs from a pivot straight above the pin's 0 deg position and
    retracts as the module tilts: (C + 1) long at the end of the span."""
    y0 = R * math.cos(math.radians(span / 2.0))
    zt = R * math.sin(math.radians(span / 2.0))           # pin height at the end of the span
    Bp = np.array([y0, zt + C + SPARE])
    tl = TILTS[TILTS <= span + 1e-9]
    L = np.array([np.linalg.norm(crank_pin(t, R, span) - Bp) for t in tl])
    return dict(tilts=tl, L=L, base=Bp, extend=False)


def stroke_ok(g, C, S):
    lo, hi = g["L"].min(), g["L"].max()
    if g["extend"]:
        return hi <= C + S - SPARE and lo >= C + PRELOAD - 1e-6
    return lo >= C + SPARE - 1e-6 and hi <= C + S - SPARE


def fit_lever(mount, C, S, span):
    """Longest lever (0.5 mm steps) whose stroke covers 0..span."""
    if mount == "floor":
        a = A_MAX
        while a >= A_MIN:
            g = floor_geometry(a, C, span)
            if stroke_ok(g, C, S):
                return a, g
            a -= 0.5
        return None, None
    R = R_MAX
    while R >= 3.0:
        g = crank_geometry(R, C, span)
        if stroke_ok(g, C, S):
            return R, g
        R -= 0.5
    return None, None


def evaluate(fam, stroke, gear, mount, span, powder=DESIGN_POWDER):
    c = CAT[fam]
    C, S = c["closed"](stroke), float(stroke)
    lever_mm, g = fit_lever(mount, C, S, span)
    row = dict(model=model(fam, stroke, gear), family=fam, stroke=stroke, gear=gear, closed=C, mount=mount,
               span=span)
    if lever_mm is None:
        row.update(fits=False, why="stroke too short for this span on any lever")
        return row
    tl, L = g["tilts"], g["L"]
    dL = np.abs(np.gradient(L, np.radians(tl)))           # mm of stroke per radian
    tau = torque_curve(powder)[0][: len(tl)]
    F = tau / dL
    Ff = TAU_FLAT / dL
    gr = c["gears"][gear]
    pp = gr["pp"][0] if gr["pp"] else gr["fmax"]
    worst = float(F.max())
    m_pp, m_bd = pp / worst, gr["bd"] / worst
    deg = np.degrees(1.0)
    mm_per_deg = dL / deg
    rep = c["repeat"].get(stroke)
    i30 = int(np.argmin(np.abs(tl - min(30.0, span))))
    d30 = abs(float(L[i30] - L[0]))
    dfull = abs(float(L[-1] - L[0]))
    v_hi, v_lo = gr["v0"], (gr["pp"][1] if gr["pp"] else gr["v0"] / 2.0)
    Bp = g["base"]
    row.update(
        fits=True, lever=lever_mm,
        lever_note="rod pin a mm behind the hinge, 45 mm below it" if mount == "floor" else "crank radius",
        stroke_used=round(dfull, 1), stroke_spare=round(S - dfull, 1),
        force_max_N=round(worst, 1), force_at_tilt=float(tl[int(np.argmax(F))]),
        force_max_flat_N=round(float(Ff.max()), 1),
        peak_power_N=pp, back_drive_N=gr["bd"], fmax_N=gr["fmax"],
        margin_peak_power=round(m_pp, 2), margin_back_drive=round(m_bd, 2),
        margin_peak_power_flat=round(pp / float(Ff.max()), 2), margin_back_drive_flat=round(gr["bd"] / float(Ff.max()), 2),
        passes=bool(m_pp >= MARGIN and m_bd >= MARGIN),
        passes_flat=bool(pp / float(Ff.max()) >= MARGIN and gr["bd"] / float(Ff.max()) >= MARGIN),
        mm_per_deg=[round(float(mm_per_deg.min()), 2), round(float(mm_per_deg.max()), 2)],
        repeatability_mm=rep, repeatability_deg=(round(rep / float(mm_per_deg.min()), 2) if rep else None),
        backlash_deg=(round(c["backlash"] / float(mm_per_deg.min()), 2) if c["backlash"] else None),
        move_0_30_s=[round(d30 / v_hi, 1), round(d30 / v_lo, 1)], move_full_s=[round(dfull / v_hi, 1), round(dfull / v_lo, 1)],
        mass_g=c["mass"].get(stroke), section=c["section"], control=c["control"], rc_servo_input=c["rc"],
        price=c["price"], pivot_yz=[round(float(Bp[0]), 1), round(float(Bp[1]), 1)],
    )
    lug = (c["draw"] or {}).get("lug", 3.0)
    if mount == "floor":                                  # the actuator's own lowest point (rear lug), and with
        row["below_shelf_mm"] = round(BOT - (float(Bp[1]) - lug), 1)          # its bracket and the hanger's foot
        row["below_shelf_with_bracket_mm"] = round(BOT - (float(Bp[1]) - BRACKET - FOOT), 1)
        row["from_beaker_axis_mm"] = round(SP + lever_mm, 1)
        row["above_shelf_mm"] = 0.0
    else:                                                 # the actuator's own top (rear lug), and with the
        row["below_shelf_mm"] = 0.0                       # bracket and the arm it hangs from
        row["above_shelf_mm"] = round(float(Bp[1]) + lug - TOP, 1)
        row["above_shelf_with_bracket_mm"] = round(float(Bp[1]) + BRACKET + ARM - TOP, 1)
        row["crank_pin_lowest_z"] = round(float(min(crank_pin(t, lever_mm, span)[1] for t in tl)), 1)
    return row


def candidates():
    for fam, c in CAT.items():
        for s in c["strokes"]:
            for gear in c["gears"]:
                yield fam, s, gear


# --------------------------------------------------------------------------- #
# results
# --------------------------------------------------------------------------- #
def smallest(rows, mount, span, flat=False):
    """Shortest closed length that passes, per family (same length: the faster gearing)."""
    out = {}
    key = "passes_flat" if flat else "passes"
    speed = lambda r: CAT[r["family"]]["gears"][r["gear"]]["v0"]
    for r in rows:
        if r["mount"] != mount or r["span"] != span or not r.get("fits") or not r[key]:
            continue
        f = r["family"]
        best = out.get(f)
        if best is None or (r["closed"], -speed(r)) < (best["closed"], -speed(best)):
            out[f] = r
    return out


def run():
    t0 = time.time()
    curves = {}
    for pw in POWDERS:
        tau, info = torque_curve(pw)
        curves[str(int(pw))] = dict(info, torque_Nmm={f"{t:g}": round(float(tau[int(t)]), 1) for t in range(0, 91, 15)},
                                    max_Nmm=round(float(tau.max()), 1), at_tilt=float(TILTS[int(np.argmax(tau))]))
    print("torque", json.dumps(curves), round(time.time() - t0), "s", flush=True)
    rows = [evaluate(f, s, g, m, sp) for f, s, g in candidates() for m in ("floor", "crank") for sp in SPANS]
    best = {m: {str(sp): {k: v["model"] for k, v in smallest(rows, m, sp).items()} for sp in SPANS}
            for m in ("floor", "crank")}
    best_flat = {m: {str(sp): {k: v["model"] for k, v in smallest(rows, m, sp, flat=True).items()} for sp in SPANS}
                 for m in ("floor", "crank")}
    return dict(load=curves, design_powder_g=DESIGN_POWDER, flat_torque_Nmm=TAU_FLAT, margin_needed=MARGIN,
                rule="passes if the largest force over the span is at most 1/2 of the peak-power force and 1/2 of "
                     "the back-drive force (modelled load, 250 g of powder); passes_flat uses a flat 0.65 N m",
                pq12_note=PQ12_NOTE, rows=rows, smallest_passing=best, smallest_passing_flat=best_flat)


def pick(res, name, mount, span):
    return next(r for r in res["rows"] if r["model"] == name and r["mount"] == mount and r["span"] == span)


# --------------------------------------------------------------------------- #
# crank mounting: clearance check in 3D (the actuator in L6's plane, beside the module's +X side)
# --------------------------------------------------------------------------- #
CRANK_X = (67.5, 73.5)                     # crank arm, as crank_drive.py (L6)
ACT_X = 79.0                               # actuator plane, as crank_drive.py
CHECKED = [("P8-50-165-12-P", 90), ("L12-50-210-6-R", 90), ("P16-50-22-12-P", 90), ("L12-30-210-6-R", 60)]


def act_solid(fam, C, L_):
    """The actuator as boxes, in its frame: rear hole at the origin, rod hole at (0, 0, L_), pins along x,
    the section's long side towards +y.  Returns (body, rod)."""
    d, sec = CAT[fam]["draw"], CAT[fam]["section"]
    a0, a1 = d["across"]
    lug = D.box(-3.5, 3.5, -d["lug"], d["lug"], -d["lug"], d["lug"])
    if d.get("parallel"):
        body = lug.fuse(D.box(-sec[0] / 2, sec[0] / 2, a0, a1, 3.0, C - d["tip"]))
    else:
        h0, hl = d["housing"]
        body = lug.fuse(D.box(-sec[0] / 2, sec[0] / 2, a0, a1, h0, h0 + hl)).fuse(
            D.box(-d["tube"] / 2, d["tube"] / 2, -d["tube"] / 2, d["tube"] / 2, h0 + hl - 1.0, C - d["tip"]))
    rod = D.box(-d["rod"] / 2, d["rod"] / 2, -d["rod"] / 2, d["rod"] / 2, C - d["tip"] - 1.0, L_ - d["hub"] / 2).fuse(
        D.box(-3.0, 3.0, -d["hub"] / 2, d["hub"] / 2, L_ - d["hub"] / 2, L_ + d["hub"] / 2))
    return body, rod


def crank_solid(R, span):
    """Hub on the hinge axis, arm and boss out to the pin, and the pin through the rod end (tilt 0)."""
    import cadquery as cq
    x0, x1 = CRANK_X
    b = -span / 2.0
    arm = D.box(x0, x1, 0.0, R, -7.0, 7.0).rotate(cq.Vector(0, 0, 0), cq.Vector(1, 0, 0), b)
    py, pz = crank_pin(0.0, R, span)
    crank = D.cyl(8.0, x1 - x0, x0, 0, 0, d=(1, 0, 0)).fuse(arm).fuse(D.cyl(7.0, x1 - x0, x0, py, pz, d=(1, 0, 0)))
    pin = D.cyl(2.0, 86.0 - x0, x0, py, pz, d=(1, 0, 0)).fuse(D.cyl(3.9, 3.2, 83.0, py, pz, d=(1, 0, 0)))
    return crank.clean(), pin.clean()


def crank_drive_parts(r, tilt, Mst, tag):
    fam, C, R, span = r["family"], r["closed"], r["lever"], r["span"]
    Bp = np.array(r["pivot_yz"])
    P = crank_pin(tilt, R, span)
    Pw = (Mst @ np.array([ACT_X, P[0], P[1], 1.0]))[:3]
    Bw = (Mst @ np.array([ACT_X, Bp[0], Bp[1], 1.0]))[:3]
    L_ = float(np.linalg.norm(Pw - Bw))
    wv = (Pw - Bw) / L_
    ax = -Mst[:3, 0] - wv * (-Mst[:3, 0] @ wv)
    ax /= np.linalg.norm(ax)
    Ma = np.eye(4)
    Ma[:3, 0], Ma[:3, 1], Ma[:3, 2], Ma[:3, 3] = ax, np.cross(wv, ax), wv, Bw
    body, rod = act_solid(fam, C, L_)
    crank, pin = crank_solid(R, span)
    Mt = Mst @ D.Rx(float(tilt))
    return [D.Part(f"{tag}:actuator body", body, Ma, FAMC[fam], tag, False),
            D.Part(f"{tag}:actuator rod", rod, Ma, (0.8, 0.8, 0.8), tag, True),
            D.Part(f"{tag}:crank", crank, Mt, (0.9, 0.67, 0.0), tag, True),
            D.Part(f"{tag}:crank pin", pin, Mt, (0.5, 0.5, 0.5), tag, True)]


def crank_check(r, step=10):
    """Closest approach of module A's crank drive (actuator, rod, crank, pin) over 0..span to: A itself at
    the same tilt; the neighbour its +X side faces (C) and the other one (B) at every tilt 0..90; and the
    base.  The shaft, post and arm are not modelled (crank_drive.py has them for the P16-50)."""
    MA, MB_, MC = D.place(90.0, SP, 0.0), D.place(210.0, SP, 0.0), D.place(330.0, SP, 0.0)
    span = r["span"]
    ta_list = [t for t in range(0, 91, step) if t <= span]
    tn = list(range(0, 91, step))
    out = {}
    drives = {t: ST._objs(crank_drive_parts(r, t, MA, "A")) for t in ta_list}
    w = (1e9, None, None, None)
    for t in ta_list:
        for p, op in ST._objs(LR.module_parts("L5", float(t), MA, "A")):
            for q, oq in drives[t]:
                d = ST._dist(op, oq)
                if d < w[0]:
                    w = (d, p.name, q.name, t)
    out["own_module"] = dict(mm=round(w[0], 2), between=f"{w[1]} / {w[2]}", at_tilt=w[3])
    for who, M, u in (("neighbour C", MC, "C"), ("neighbour B", MB_, "B")):
        cache = {tc: ST._objs(LR.module_parts("L5", float(tc), M, u)) for tc in tn}
        w = (1e9, None, None, None, None)
        for ta in ta_list:
            for tc in tn:
                for p, op in cache[tc]:
                    for q, oq in drives[ta]:
                        d = ST._dist(op, oq)
                        if d < w[0]:
                            w = (d, p.name, q.name, ta, tc)
        out[who] = dict(mm=round(w[0], 2), between=f"{w[1]} / {w[2]}", tilt_A=w[3], tilt_other=w[4])
    bo = ST._objs([D.Part("base", LR.base_for("L5"), np.eye(4), (0.6, 0.6, 0.6))])[0][1]
    w = (1e9, None, None)
    for t in ta_list:
        for q, oq in drives[t]:
            d = ST._dist(oq, bo)
            if d < w[0]:
                w = (d, q.name, t)
    out["base"] = dict(mm=round(w[0], 2), part=w[1], at_tilt=w[2])
    # the actuator's swing over the span, and how far out it reaches (x in the module frame)
    out["min_mm"] = round(min(v["mm"] for v in out.values()), 2)
    return out


# --------------------------------------------------------------------------- #
# drawing helpers (2D, to scale)
# --------------------------------------------------------------------------- #
def actuator_outline(fam, C, L_):
    """Polygons of the actuator in its own frame: x along the axis (0 = rear hole, L_ = rod-end hole),
    y across (the drawing's long side of the section).  Returns {"body": [...], "rod": [...]}."""
    d = CAT[fam]["draw"]
    a0, a1 = d["across"]
    box = lambda x0, x1, y0, y1: [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    circ = lambda x, r: [(x + r * math.cos(u), r * math.sin(u)) for u in np.linspace(0, 2 * math.pi, 28)]
    body, rod = [circ(0.0, d["lug"])], []
    if d.get("parallel"):                                     # P8: motor beside the screw, one long block
        tube_end = C - d["tip"]                               # body front 8.4 mm short of the rod hole
        body.append(box(3.0, tube_end, a0, a1))
        rod.append(box(tube_end - 1.0, L_ - d["hub"] / 2, -d["rod"] / 2, d["rod"] / 2))
    else:
        h0, hl = d["housing"]
        body.append(box(h0, h0 + hl, a0, a1))
        tube_end = C - d["tip"]
        body.append(box(h0 + hl - 1.0, tube_end, -d["tube"] / 2, d["tube"] / 2))
        rod.append(box(tube_end - 1.0, L_ - d["hub"] / 2, -d["rod"] / 2, d["rod"] / 2))
    rod.append(circ(L_, d["hub"] / 2))
    return dict(body=body, rod=rod)


def place2d(polys, P0, P1, flip=1.0):
    """Map actuator-frame polygons onto the segment rear hole P0 -> rod hole P1 (2D)."""
    u = (P1 - P0) / np.linalg.norm(P1 - P0)
    n = np.array([-u[1], u[0]]) * flip
    return [[tuple(P0 + x * u + y * n) for x, y in poly] for poly in polys]


_SIL: dict = {}


def module_silhouette(tilt):
    """(colour, triangles in y-z) for one module at ``tilt`` and the base's +X tower and shelf."""
    if tilt not in _SIL:
        tris = []
        parts = LR.module_parts("L5", float(tilt), np.eye(4), "A")
        for p in parts:
            m = D.mesh_of(p.shape, tol=0.4)
            V = (p.M[:3, :3] @ np.asarray(m.vertices).T).T + p.M[:3, 3]
            tris.append((p.colour, V[:, 1:][np.asarray(m.faces)]))
        _SIL[tilt] = tris
    return _SIL[tilt]


def block_silhouette(tilt, a):
    """The clevis block (clevis.py) under the floor, a mm behind the hinge, at ``tilt`` (y-z triangles)."""
    import clevis as CL
    if "block" not in _SIL:
        m = D.mesh_of(CL.block(), tol=0.3)
        _SIL["block"] = (np.asarray(m.vertices), np.asarray(m.faces))
    V, F = _SIL["block"]
    M = D.Rx(tilt) @ D.Tt(0.0, a, K.FLOOR_U)
    W = (M[:3, :3] @ V.T).T + M[:3, 3]
    return W[:, 1:][F]


def tower_silhouette():
    if "tower" not in _SIL:
        tw = B.tower_today()
        m = D.mesh_of(tw, tol=0.3)
        _SIL["tower"] = np.asarray(m.vertices)[:, 1:][np.asarray(m.faces)]
    return _SIL["tower"]


# --------------------------------------------------------------------------- #
# figures
# --------------------------------------------------------------------------- #
INK = "#222222"


def _pale(col, k=0.32):
    """``col`` blended with white (k of the colour), so overlapping pale shapes don't darken."""
    import matplotlib.colors as mc
    c = np.array(mc.to_rgb(col))
    return tuple(1.0 - k * (1.0 - c))
GOOD, BAD = "#1b9e77", "#c0392b"
FAMC = {"P16": "#4d4d4d", "L16": "#7570b3", "L12": "#1b9e77", "P8": "#d95f02", "PQ12": "#e7298a"}


def fig_load_and_levers(res, fn):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axs = plt.subplots(1, 2, figsize=(15.5, 7.2), gridspec_kw=dict(width_ratios=[1.0, 1.6]))
    ax = axs[0]
    for pw, col in zip(POWDERS, ("#9ecae1", "#4292c6", "#08519c")):
        tau = torque_curve(pw)[0]
        ax.plot(TILTS, tau / 1000.0, color=col, lw=2.2, label=f"module + {pw:g} g powder")
    ax.axhline(TAU_FLAT / 1000.0, color="#999999", ls="--", lw=1.4, label="0.65 N·m, the earlier flat figure")
    ax.set_xlabel("tilt (deg)")
    ax.set_ylabel("torque the actuator holds about the hinge (N·m)")
    ax.set_xlim(0, 90)
    ax.set_ylim(0, 0.72)
    ax.set_xticks(range(0, 91, 15))
    ax.grid(alpha=0.3)
    ax.legend(loc="upper right", fontsize=9, frameon=False)
    ax.set_title("The load: the module's weight about its hinge", fontsize=11.5, loc="left")
    # right: what each actuator offers (its stroke; half the smaller of its peak-power and back-drive forces)
    # against what a span needs (the stroke used + spares, and the largest force) as the lever varies
    ax = axs[1]
    tau = torque_curve(DESIGN_POWDER)[0]
    curves = []
    for mount, span, ls, lab in (("crank", 90, "-", "on a crank, 0–90°"), ("crank", 60, "--", "on a crank, 0–60°"),
                                 ("floor", 90, ":", "under the floor, 0–90° (pin 40–95 mm behind the hinge)")):
        xs, ys = [], []
        levers = np.arange(5.0, R_MAX + 0.01, 0.5) if mount == "crank" else np.arange(A_MIN, A_MAX + 0.01, 0.5)
        for lv in levers:
            g = crank_geometry(lv, 100.0, span) if mount == "crank" else floor_geometry(lv, 100.0, span)
            dL = np.abs(np.gradient(g["L"], np.radians(g["tilts"])))
            used = float(g["L"].max() - g["L"].min())
            xs.append(used + (2 * SPARE if mount == "crank" else PRELOAD + SPARE))
            ys.append(float((tau[: len(g["tilts"])] / dL).max()))
        ax.plot(xs, ys, color=INK, ls=ls, lw=1.8, label=f"needed {lab}")
        curves.append((mount, span, np.array(xs), np.array(ys)))
    offs = {"P16": -2.4, "L16": -0.8, "L12": 0.8, "P8": 2.4, "PQ12": 0.0}
    for fam, c in CAT.items():
        for st in c["strokes"]:
            xs = st + offs[fam]
            vals = []
            for gear, gr in c["gears"].items():
                pp = gr["pp"][0] if gr["pp"] else gr["fmax"]
                vals.append((min(pp, gr["bd"]) / MARGIN, gear))
            ys = [v for v, _ in vals]
            ax.plot([xs, xs], [min(ys), max(ys)], color=FAMC[fam], lw=1.0, alpha=0.6)
            for v, gear in vals:
                ax.plot([xs], [v], marker="o", ms=5.5, color=FAMC[fam], mec="white", mew=0.6, zorder=5)
                ax.annotate(f"{gear}:1", (xs, v), xytext=(4, -2), textcoords="offset points", fontsize=6.8,
                            color=FAMC[fam])
    for fam in CAT:
        ax.plot([], [], marker="o", ls="", color=FAMC[fam], label=f"Actuonix {fam}: strokes {', '.join(str(x) for x in CAT[fam]['strokes'])} mm")
    ax.set_yscale("log")
    ax.set_ylim(3, 130)
    ax.set_yticks([3, 5, 10, 20, 50, 100])
    ax.set_yticklabels(["3", "5", "10", "20", "50", "100"])
    ax.set_xlim(0, 160)
    ax.set_xlabel("stroke (mm)")
    ax.set_ylabel("force it can work at: half the smaller of its peak-power\nand back-drive (power-off hold) forces (N)")
    ax.grid(alpha=0.3, which="both")
    h, l = ax.get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", bbox_to_anchor=(0.5, 0.005), ncol=4, fontsize=9, frameon=False)
    ax.set_title("Each dot is one actuator and gearing.  A dot above a curve can do that job\n"
                 "(using its whole stroke on the longest lever it allows), with 2× force to spare", fontsize=11.5,
                 loc="left")
    fig.subplots_adjust(left=0.06, right=0.985, bottom=0.19, top=0.86, wspace=0.22)
    fig.suptitle("What sizes the actuator: the force is small; the stroke follows the lever", fontsize=14, x=0.06,
                 ha="left", y=0.975)
    fig.savefig(fn, dpi=130)
    plt.close(fig)


def fig_lineup(res, fn):
    """Each candidate drawn to scale, closed (solid) and fully out (ghost)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon
    items = [("P16-150-22-12-P", "today (#202's pick): under the floor, 0–90°"),
             ("P16-100-22-12-P", "under the floor, 0–90° (pin 48.5 mm behind the hinge)"),
             ("L12-100-100-6-R", "under the floor, 0–90°; RC servo input"),
             ("P8-100-165-12-P", "under the floor, 0–90°: the shortest there"),
             ("P16-50-22-12-P", "on a crank, 0–90° (the other run's L6)"),
             ("L16-50-63-6-R", "on a crank, 0–90°"),
             ("L12-50-210-6-R", "on a crank, 0–90°; RC servo input"),
             ("P8-50-165-12-P", "on a crank, 0–90°: the shortest there"),
             ("L12-30-210-6-R", "on a crank, 0–60° only; RC servo input"),
             ("P8-25-252-12-P", "on a crank, 0–60° only")]
    fig, ax = plt.subplots(figsize=(15.0, 9.6))
    y = 0.0
    for nm, note in items:
        fam = nm.split("-")[0]
        s = int(nm.split("-")[1])
        C = CAT[fam]["closed"](s)
        col = FAMC[fam]
        for L_, alpha, z in ((C + s, 0.18, 1), (C, 0.95, 2)):
            o = actuator_outline(fam, C, L_)
            for poly in o["body"]:
                ax.add_patch(Polygon([(x, y + v) for x, v in poly], closed=True, fc=col, ec=col, alpha=alpha, lw=0.6, zorder=z))
            for poly in o["rod"]:
                ax.add_patch(Polygon([(x, y + v) for x, v in poly], closed=True, fc="#bbbbbb", ec="#777777",
                                     alpha=min(1.0, alpha + 0.1), lw=0.6, zorder=z))
            if alpha > 0.5:
                for x in (0.0, L_):
                    ax.add_patch(plt.Circle((x, y), 2.125, fc="white", ec="#555555", lw=0.6, zorder=3))
        c = CAT[fam]
        gear = int(nm.split("-")[2])
        gr = c["gears"][gear]
        pp = gr["pp"][0] if gr["pp"] else gr["fmax"]
        sec = c["section"]
        m = c["mass"].get(s)
        line = (f"{nm}: {note}\n"
                f"stroke {s} mm, {C:.0f} mm closed (hole to hole), body {sec[0]:.0f} × {sec[1]:.0f} mm"
                + (f", {m} g" if m else "") + f"\n{pp:.0f} N at peak power, holds {gr['bd']:.0f} N unpowered, "
                f"{gr['v0']:g} mm/s with no load")
        ax.text(362, y, line, fontsize=8.4, color=INK, va="center", linespacing=1.25)
        y -= 46.0
    ax.set_xlim(-16, 640)
    ax.set_ylim(y + 22, 24)
    ax.set_aspect("equal")
    ax.set_xticks(range(0, 351, 50))
    ax.spines["bottom"].set_bounds(0, 350)
    ax.set_yticks([])
    for sp in ("left", "right", "top"):
        ax.spines[sp].set_visible(False)
    ax.set_xlabel("mm from the rear hole (all to the same scale; solid: closed, pale: fully extended)")
    ax.set_title("Actuonix actuators that could tilt a module, to scale", fontsize=14, loc="left")
    fig.text(0.01, 0.01, "Outlines from Actuonix's drawings (P16 Rev B, L12 Rev D, L16 Rev E, P8 Rev A): housing, tube, "
             "rod and end holes; the P8's motor sits beside its screw.  PQ12 (20 mm stroke) not drawn: no dimensioned "
             "drawing found.", fontsize=8.2, color="#555555")
    fig.subplots_adjust(left=0.02, right=0.99, top=0.94, bottom=0.08)
    fig.savefig(fn, dpi=130)
    plt.close(fig)


def fig_layouts(res, panels, fn):
    """Side views of one module with each layout's actuator, all to the same scale."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.collections import PolyCollection
    from matplotlib.patches import Polygon
    n = len(panels)
    fig, axs = plt.subplots(1, n, figsize=(3.7 * n, 8.9), sharey=True)
    tw = tower_silhouette()
    for ax, (title, r) in zip(axs, panels):
        span = r["span"]
        fam = r["family"]
        C = r["closed"]
        # shelf and tower
        ax.add_patch(plt.Rectangle((-45, BOT), 200, TOP - BOT, fc="#c9c9c9", ec="#888888", lw=0.6, zorder=1))
        ax.add_collection(PolyCollection(tw, fc="#c9c9c9", ec="#c9c9c9", lw=0.3, zorder=1))
        for t, pale in ((span, True), (0.0, False)):
            for col, tris in module_silhouette(float(t)):
                c = _pale(col) if pale else col
                ax.add_collection(PolyCollection(tris, fc=c, ec=c, lw=0.2, zorder=2 if pale else 3))
            if r["mount"] == "floor":
                c = _pale(K.STATUS["new"][2]) if pale else K.STATUS["new"][2]
                ax.add_collection(PolyCollection(block_silhouette(float(t), r["lever"]), fc=c, ec=c, lw=0.2,
                                                 zorder=2 if pale else 4))
        for t, alpha, z in ((float(span), 0.0, 2.5), (0.0, 1.0, 5)):
            if r["mount"] == "floor":
                Pp = floor_pin(t, r["lever"])
                Bp = np.array(r["pivot_yz"])
            else:
                Pp = crank_pin(t, r["lever"], span)
                Bp = np.array(r["pivot_yz"])
                hc = "#e6ab02" if alpha else _pale("#e6ab02")
                ax.add_patch(plt.Circle((0, 0), 8.0, fc=hc, ec=hc, lw=0.6, zorder=z))
                ax.plot([0, Pp[0]], [0, Pp[1]], color=hc, lw=6, solid_capstyle="round", zorder=z)
            L_ = float(np.linalg.norm(Pp - Bp))
            o = actuator_outline(fam, C, L_)
            colr = FAMC[fam] if alpha else _pale(FAMC[fam])
            rc_ = "#bbbbbb" if alpha else _pale("#bbbbbb")
            for poly in place2d(o["body"], Bp, Pp, flip=-1.0 if r["mount"] == "floor" else 1.0):
                ax.add_patch(Polygon(poly, closed=True, fc=colr, ec=colr, lw=0.5, zorder=z))
            for poly in place2d(o["rod"], Bp, Pp, flip=-1.0 if r["mount"] == "floor" else 1.0):
                ax.add_patch(Polygon(poly, closed=True, fc=rc_, ec=rc_ if not alpha else "#666666", lw=0.5, zorder=z))
        if r["mount"] == "floor":
            low = BOT - r["below_shelf_mm"]
            ax.annotate("", xy=(150, BOT), xytext=(150, low), arrowprops=dict(arrowstyle="<->", color=BAD, lw=1.2))
            ax.text(153, (BOT + low) / 2, f"{r['below_shelf_mm']:.0f} mm\nunder the\nshelf", color=BAD, fontsize=9,
                    va="center")
            ax.plot([-45, 160], [low, low], color=BAD, lw=0.8, ls="--")
        else:
            hi = TOP + r["above_shelf_mm"]
            ax.annotate("", xy=(150, TOP), xytext=(150, hi), arrowprops=dict(arrowstyle="<->", color=GOOD, lw=1.2))
            ax.text(153, (TOP + hi) / 2, f"{r['above_shelf_mm']:.0f} mm\nabove the\nshelf;\nnothing\nunder it",
                    color=GOOD, fontsize=9, va="center")
        ax.set_aspect("equal")
        ax.set_xlim(-45, 190)
        ax.set_ylim(-322, 215)
        ax.set_xticks([0, 50, 100, 150])
        ax.grid(alpha=0.2)
        ax.set_title(title, fontsize=10.5, loc="left")
        lev = (f"pin {r['lever']:g} mm behind the hinge" if r["mount"] == "floor" else f"crank {r['lever']:g} mm long")
        ax.text(-42, -314, f"{r['model']}, {r['closed']:.0f} mm closed\n{lev}\n"
                f"0–{span}° uses {r['stroke_used']:.0f} of its {r['stroke']} mm\n"
                f"most force {r['force_max_N']:.0f} N; it gives {r['peak_power_N']:.0f} N\n"
                f"at peak power, holds {r['back_drive_N']:.0f} N unpowered",
                fontsize=8.3, va="bottom", color=INK, linespacing=1.2)
        ax.set_xlabel("mm behind the hinge")
    axs[0].set_ylabel("mm above the hinge axis")
    fig.suptitle("One module seen from its +X side at 0° (solid) and at the end of its tilt range (pale), each "
                 "actuator to the same scale.  Grey band: the shelf; grey outline: the hinge tower.\n"
                 "Floor: the clevis block under the plate, as today.  Crank: a crank on the hinge axis beside the "
                 "module, the actuator hanging from a post above the shelf (post not drawn).", fontsize=12, x=0.01,
                 ha="left")
    fig.subplots_adjust(left=0.05, right=0.99, top=0.88, bottom=0.06, wspace=0.08)
    fig.savefig(fn, dpi=125)
    plt.close(fig)


# --------------------------------------------------------------------------- #
def main():
    t0 = time.time()
    OUT.mkdir(exist_ok=True)
    if "--figures-only" in sys.argv:                      # redraw from actuator_size.json
        res = json.loads((HERE / "actuator_size.json").read_text())
        for pw in POWDERS:
            info = res["load"][str(int(pw))]
            _TAU[pw] = (np.interp(TILTS, np.arange(0.0, 90.001, 5.0), info["torque_5deg_Nmm"]), info)
        draw(res)
        print("figures", round(time.time() - t0), "s")
        return
    res = run()
    for m in ("floor", "crank"):
        for sp in SPANS:
            print(m, sp, res["smallest_passing"][m][str(sp)], flush=True)
    keep = ["P16-150-22-12-P", "P16-100-22-12-P", "P16-50-22-12-P", "L12-100-210-6-R", "L12-50-210-6-R",
            "L12-50-100-6-R", "L12-30-210-6-R", "P8-100-165-12-P", "P8-50-165-12-P", "P8-25-165-12-P",
            "L16-50-63-6-R", "L16-100-63-6-R", "PQ12-100-6-R"]
    for r in res["rows"]:
        if r["model"] in keep and r.get("fits"):
            print(f"{r['model']:17s} {r['mount']:5s} 0-{r['span']:2d} lever {r['lever']:5.1f} used {r['stroke_used']:5.1f} "
                  f"F {r['force_max_N']:5.1f} (flat {r['force_max_flat_N']:5.1f}) m_pp {r['margin_peak_power']:5.2f} "
                  f"m_bd {r['margin_back_drive']:5.2f} pass {r['passes']!s:5s} flat {r['passes_flat']!s:5s} "
                  f"below {r['below_shelf_mm']:6.1f} above {r['above_shelf_mm']:6.1f} mm/deg {r['mm_per_deg']} "
                  f"rep {r['repeatability_deg']} t30 {r['move_0_30_s']} tfull {r['move_full_s']}", flush=True)
    if "--no-checks" not in sys.argv:
        res["crank_checks"] = {}
        for nm, sp in CHECKED:
            r = pick(res, nm, "crank", sp)
            ck = crank_check(r, step=10 if "--fast" in sys.argv else 5)
            res["crank_checks"][f"{nm} 0-{sp}"] = ck
            print("check", nm, sp, json.dumps(ck), round(time.time() - t0), "s", flush=True)
    if "--no-json" not in sys.argv:
        (HERE / "actuator_size.json").write_text(json.dumps(res, indent=1, default=float) + "\n")
    if "--no-figures" not in sys.argv:
        draw(res)
    print("done", round(time.time() - t0), "s", flush=True)


def draw(res):
    if True:
        fig_load_and_levers(res, OUT / "actuator_sizing.png")
        fig_lineup(res, OUT / "actuator_lineup.png")
        panels = [("a. Today: P16-150 under the floor, 0–90°", pick(res, "P16-150-22-12-P", "floor", 90)),
                  ("b. Under the floor, 0–90°: P16-100", pick(res, "P16-100-22-12-P", "floor", 90)),
                  ("c. Under the floor, 0–45° only: P8-50", pick(res, "P8-50-165-12-P", "floor", 45)),
                  ("d. On a crank (L6), 0–90°: L12-50", pick(res, "L12-50-210-6-R", "crank", 90)),
                  ("e. On a crank, 0–60° only: L12-30", pick(res, "L12-30-210-6-R", "crank", 60))]
        fig_layouts(res, panels, OUT / "actuator_layouts.png")


if __name__ == "__main__":
    main()
