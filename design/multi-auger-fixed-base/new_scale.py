"""The tri-star over the lab's new balance, with a side door free (issue #204, 23 Nov).

Ethan gave rough dimensions for the balance the doser will be built around:

  * base about 260 mm long (front to back) x 190 mm wide;
  * enclosure (draft shield) on top, about 183 mm wide x 240 mm long, front to back at its widest;
  * about 320 mm tall overall.

and asked: what has to change for the tri-star to fit easily over it, keeping the linear actuators,
with room to open at least one side door?  And is what we worked out before compatible with it?

The balance is modelled as two boxes (conservative: the real one has rounded or sloped faces):

  * base 190 x 260 from the bench to H_BASE (assumed 90 mm; not given), its back flush with the
    enclosure's back, so its extra 20 mm of length sticks out at the front, under the display;
  * enclosure 183 x 240 from H_BASE to 320 mm;
  * the pan centre on the enclosure's centre line, F mm behind its front face.  F is not known:
    120 (pan centred) is the baseline and 80-160 is swept.  The pan centre sits on the beaker axis.

Side doors: a box-type draft shield has a sliding glass door on each long side.  "Room to open a side
door" is taken as a clear space beside it, as long as the enclosure and from H_BASE to 320 mm tall,
going out at least 100 mm (a hand with a beaker), plus room for the door to slide back past the
enclosure's back (a 20 mm strip beside the side, behind the enclosure).  The top door has to be open
while dosing, so the room behind the top for it to slide back into is reported too.

Every layout from leg_room.py (L0 today's S2 through L5 the hinge-axis drive) is swept with the shelf's
underside 340 mm above the bench (20 mm over the balance), the balance turned in 5 deg steps, and the
actuators at every tilt 0-90 deg (and 0-60 deg).  New layouts that keep the P16s are added (see LAYOUTS).

    pip install cadquery trimesh python-fcl rtree vtk pillow numpy matplotlib scipy
    xvfb-run -a python new_scale.py            # writes new_scale.json and renders/newscale_*.png

Frames as in scale_room.py: station frame (beaker axis = z, modules at bearings 90 (back), 210, 330,
the front gap at 270, towards the user).  Balance frame: origin on the bench under the pan centre,
+x towards the balance's back, +y to the user's left when facing its display, z up.  The balance's back
points at bearing phi; phi = 90 means it faces the user squarely.
"""
from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path

import numpy as np

import doserlib as D
import base as B
import leg_room as LR
import scale_room as SR

HERE = Path(__file__).resolve().parent
OUT = HERE / "renders"

# --------------------------------------------------------------------------- #
# the new balance (Ethan, 23 Nov: rough numbers) and what we assume about it
# --------------------------------------------------------------------------- #
NB = dict(base_w=190.0, base_l=260.0, encl_w=183.0, encl_l=240.0, top=320.0,
          h_base=90.0,            # assumed: where the enclosure starts (not given)
          F=120.0,                # assumed: pan centre behind the enclosure's front (centred)
          access=100.0,           # clear depth wanted beside a side door
          slide_strip=20.0,       # a sliding side door's glass and handle, beside the side, behind the back
          slide_len=200.0)        # how far behind the back an opened door could reach (assumed)
F_SWEEP = (80.0, 100.0, 120.0, 140.0, 160.0)
PHIS = tuple(range(0, 360, 5))
EASY = 10.0                       # "fits easily": 10 mm all round
GAP = 2.0                         # the mechanism's own target, as everywhere else
S = LR.S                          # 340: shelf underside above the bench
ZB = LR.ZB


def balance_prims(F=None, nb=NB):
    """The balance as SR-style convex prisms (balance frame), and its key x/y extents."""
    F = nb["F"] if F is None else F
    w, wb = nb["encl_w"] / 2, nb["base_w"] / 2
    x0, x1 = -F, nb["encl_l"] - F                      # enclosure front / back
    xb0 = x1 - nb["base_l"]                            # base front (20 mm ahead of the enclosure)
    rect = lambda a0, a1, b0, b1: [(a0, b0), (a1, b0), (a1, b1), (a0, b1)]
    prims = [("xy", rect(xb0, x1, -wb, wb), 0.0, nb["h_base"]),
             ("xy", rect(x0, x1, -w, w), nb["h_base"], nb["top"])]
    return prims, dict(x0=x0, x1=x1, xb0=xb0, w=w, wb=wb)


# --------------------------------------------------------------------------- #
# what hangs under the shelf, per layout
# --------------------------------------------------------------------------- #
def obstacles(key):
    """Station-frame samples of everything under the shelf for layout ``key``: (points, tilt, kind),
    tilt = -1 for fixed parts, kind 0 = actuator (P16, rod, bracket, clevis block, pin, tail), 1 = leg."""
    if key == "L5w":                                   # L5 with its posts on L2's outrigger arms
        sh = LR.leg_post(LR.OPTIONS["L2"]["post_y"], tab=None)
        legs = np.vstack([LR.samples(sh, D.place(th, LR.SP, 0.0), 2.0) for th in LR.BEARINGS])
        legs = legs[legs[:, 2] < LR.BOT]
        P, T = np.zeros((0, 3)), np.zeros(0)
    else:
        base_key = key
        P, T = LR.hanging_samples(base_key)
        legs = LR.leg_samples(base_key)
    A3 = LR.rot3(P) if len(P) else np.zeros((0, 3))
    T3 = np.tile(T, 3) if len(T) else np.zeros(0)
    pts = np.vstack([A3, legs])
    tilt = np.concatenate([T3, np.full(len(legs), -1.0)])
    kind = np.concatenate([np.zeros(len(A3)), np.ones(len(legs))])
    return pts, tilt, kind


# --------------------------------------------------------------------------- #
# the sweep
# --------------------------------------------------------------------------- #
def evaluate(obs, phi, F, tmax=90.0, nb=NB):
    """Closest approach of the balance to everything under the shelf (tilts up to tmax), and the clear
    room beside each side door, behind each side (sliding door) and behind the top (top door)."""
    pts, tilt, kind = obs
    sel = tilt <= tmax
    Pb = SR.to_balance(pts[sel], phi, ZB)
    prims, e = balance_prims(F, nb)
    d = SR.sdf(Pb, prims)
    k = int(np.argmin(d))
    out = dict(phi=phi, F=F, fit=round(float(d[k]), 1), fit_what="actuator" if kind[sel][k] == 0 else "leg",
               fit_tilt=int(tilt[sel][k]), shelf=round(S - nb["top"], 1))
    x, y, z = Pb[:, 0], Pb[:, 1], Pb[:, 2]
    zin = (z >= nb["h_base"]) & (z <= nb["top"])
    span = (x >= e["x0"]) & (x <= e["x1"]) & zin
    for side, sg in (("left", 1.0), ("right", -1.0)):
        yy = sg * y - e["w"]                         # distance out from that side face
        m = span & (yy > 0)
        out[f"door_{side}"] = round(float(yy[m].min()), 1) if m.any() else 999.0
        m2 = (x > e["x1"]) & zin & (yy > -5.0) & (yy < nb["slide_strip"])
        out[f"slide_{side}"] = round(float((x[m2] - e["x1"]).min()), 1) if m2.any() else 999.0
    m3 = (x > e["x1"]) & (np.abs(y) < e["w"]) & (z > nb["top"] - 30.0) & (z < nb["top"] + 10.0)
    out["top_slide"] = round(float((x[m3] - e["x1"]).min()), 1) if m3.any() else 999.0
    return out


def door_ok(r, nb=NB, side=None):
    sides = ("left", "right") if side is None else (side,)
    return [s for s in sides if r[f"door_{s}"] >= nb["access"] and r[f"slide_{s}"] >= nb["slide_len"]]


def best_rows(rows, nb=NB):
    """Best orientation for fit alone; and best with a usable side door (fit >= EASY first)."""
    bf = max(rows, key=lambda r: (r["fit"], max(r["door_left"], r["door_right"])))
    cand = [r for r in rows if r["fit"] >= EASY and door_ok(r, nb)]
    lvl = "easy"
    if not cand:
        cand = [r for r in rows if r["fit"] >= GAP and door_ok(r, nb)]
        lvl = "tight"
    if cand:
        bd = max(cand, key=lambda r: (min(r["fit"], 40.0) + max(r["door_left"], r["door_right"]) / 10.0
                                      - abs(((r["phi"] - 90 + 180) % 360) - 180) / 30.0))
    else:
        bd, lvl = None, "none"
    return bf, bd, lvl


def sweep(key, obs, tmax=90.0, Fs=F_SWEEP, nb=NB):
    res = {}
    for F in Fs:
        rows = [evaluate(obs, phi, F, tmax, nb) for phi in PHIS]
        bf, bd, lvl = best_rows(rows, nb)
        res[str(int(F))] = dict(best_fit=bf, best_with_door=bd, door_level=lvl,
                                n_fit_easy=sum(r["fit"] >= EASY for r in rows),
                                n_fit=sum(r["fit"] >= GAP for r in rows),
                                n_door=sum(bool(door_ok(r, nb)) and r["fit"] >= GAP for r in rows),
                                rows=rows)
    return res


def main():
    t0 = time.time()
    LR.prepare()
    keys = ["L0", "L1", "L2", "L3", "L4", "L5", "L5w"]
    res = dict(balance=NB, shelf_underside_above_bench=S, phis_step=5, easy_mm=EASY, layouts={})
    for key in keys:
        obs = obstacles(key)
        r = dict(any_tilt=sweep(key, obs, 90.0))
        if key in ("L0", "L3"):
            r["tilts_to_60"] = sweep(key, obs, 60.0)
        res["layouts"][key] = r
        for lab, sw in r.items():
            for F, v in sw.items():
                bf, bd = v["best_fit"], v["best_with_door"]
                print(f"{key:4s} {lab:10s} F={F:>3s} best fit {bf['fit']:6.1f} at phi {bf['phi']:3d} "
                      f"(door L/R {bf['door_left']:.0f}/{bf['door_right']:.0f}) | n_easy {v['n_fit_easy']:2d} n_fit {v['n_fit']:2d} "
                      f"n_door {v['n_door']:2d} | door: " +
                      ("-" if bd is None else f"phi {bd['phi']} fit {bd['fit']} L/R {bd['door_left']:.0f}/{bd['door_right']:.0f} "
                                            f"slide {bd['slide_left']:.0f}/{bd['slide_right']:.0f} top {bd['top_slide']:.0f} [{v['door_level']}]"),
                      flush=True)
        print("   ", round(time.time() - t0), "s", flush=True)
    if "--no-json" not in sys.argv:
        slim = json.loads(json.dumps(res, default=float))
        (HERE / "new_scale.json").write_text(json.dumps(slim, indent=1) + "\n")


if __name__ == "__main__":
    main()
