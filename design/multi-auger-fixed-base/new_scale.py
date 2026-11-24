"""The tri-star over the lab's new balance, with a side door free (issue #204, 23 Nov).

Ethan gave rough dimensions for the balance the doser will be built around:

  * base about 260 mm long (front to back) x 190 mm wide;
  * enclosure (draft shield) on top, about 183 mm wide x 240 mm long, front to back at its widest;
  * about 320 mm tall overall.

and asked: what has to change for the tri-star to fit easily over it, keeping the linear actuators, with room
to open at least one side door?  And is what we worked out before compatible with it?

The balance is modelled as two boxes (conservative: the real one has rounded or sloped faces):

  * base 190 x 260 from the bench to H_BASE (assumed 90 mm; not given), its back flush with the
    enclosure's back, so its extra 20 mm of length sticks out at the front, under the display;
  * enclosure 183 x 240 from H_BASE to 320 mm;
  * the pan centre on the enclosure's centre line, F mm behind its front face.  F is not known:
    120 (pan centred) is the baseline and 80-160 is swept.  The pan centre sits on the beaker axis.

Side doors.  A box-type draft shield has a sliding glass door on each long side.  Two things are checked
beside each one:
  * reach-in: the clear depth beside the door, over the enclosure's full length and from H_BASE to 320 mm.
    100 mm is taken as enough for a hand with a beaker;
  * slide-back: if the door slides back past the enclosure's back, the clear length of a 20 mm strip beside
    that side, behind the enclosure.  200 mm is taken as enough;
and behind the top: the clear length for the top door to slide back (it has to be open while dosing).

Layouts, each with the shelf's underside S mm above the bench:
  L0-L5, L5w  leg_room.py's six layouts (and L5 with its posts out at r 247), at S = 340
  L2r, L4r    L2 and L4 with the shelf raised to S = 380
  T0          today's P16-150s straight down, on hangers, the shelf raised until they end above the balance;
              posts on L2's outrigger arms (r 247)
  L6          crank_drive.py: a P16-50 on a crank at each hinge, above the shelf, so only the legs (L5w's
              posts, r 247) are under it; S = 340
Every actuator is swept over 0-90 deg in 5 deg steps (and 0-60 deg for L0 and L3), the balance turned in 5 deg
steps.  A fast pass: surface samples of the doser and stand (1.5-2 mm apart) against the balance's exact boxes.

    pip install cadquery trimesh python-fcl rtree vtk pillow numpy matplotlib scipy
    xvfb-run -a python new_scale.py               # about 17 min; new_scale.json, renders/newscale_*.png, crank_drive.png
    xvfb-run -a python new_scale.py --figures-only

Frames as in scale_room.py: station frame (beaker axis = z, modules at bearings 90 (back), 210, 330, gaps
at 30, 150 and 270).  Balance frame: origin on the bench under the pan centre, +x towards the balance's back,
+y to the user's left when facing its display, z up.  The balance's back points at bearing phi; phi = 90
means its display faces the gap at 270 squarely.
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
import components as K
import leg_room as LR
import scale_room as SR
import crank_drive as CD

HERE = Path(__file__).resolve().parent
OUT = HERE / "renders"
CACHE = Path("/tmp/new_scale_samples.npz")

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
BOT = LR.BOT                      # shelf underside, station z (-43.25)
S_STD = 340.0                     # shelf underside above the bench: 20 mm over the balance
S_RAISED = 380.0

LAYOUTS = {
    "L0": dict(title="Today (S2)", src="L0", S=S_STD, keep="P16-150 under the plate, straight down", tmax=(90, 60)),
    "L1": dict(title="Legs splayed", src="L1", S=S_STD, keep="P16-150, straight down"),
    "L2": dict(title="P16s leaning 25° out", src="L2", S=S_STD, keep="P16-150, leaning out"),
    "L2r": dict(title="P16s leaning 25° out, shelf at 380", src="L2", S=S_RAISED, keep="P16-150, leaning out"),
    "L3": dict(title="Longer lever, P16-200", src="L3", S=S_STD, keep="P16-200, straight down", tmax=(90, 60)),
    "L4": dict(title="Lever + lean, P16-200", src="L4", S=S_STD, keep="P16-200, leaning out"),
    "L4r": dict(title="Lever + lean, shelf at 380", src="L4", S=S_RAISED, keep="P16-200, leaning out"),
    "L5": dict(title="Gearmotor on the hinge (S2 posts)", src="L5", S=S_STD, keep="no linear actuator"),
    "L5w": dict(title="Gearmotor on the hinge, posts at r 247", src="L5w", S=S_STD, keep="no linear actuator"),
    "T0": dict(title="Today's P16s above the balance (tall stand)", src="T0", S=None, keep="P16-150, straight down, as today"),
    "L6": dict(title="P16-50 on a crank, above the shelf", src="L6", S=S_STD, keep="P16-50 above the shelf"),
}


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


def from_gap(phi):
    """How far (deg) the balance's display is turned from facing a gap squarely."""
    front = (phi + 180.0) % 360.0
    return min(abs(((front - g + 180.0) % 360.0) - 180.0) for g in (30.0, 150.0, 270.0))


# --------------------------------------------------------------------------- #
# what is under the shelf, per layout
# --------------------------------------------------------------------------- #
def set_height(S):
    """Rebuild leg_room.py's legs for a shelf S mm above the bench (its module globals)."""
    LR.S, LR.ZB = S, BOT - S
    for k in list(LR._S):
        if k in ("post0",) or (isinstance(k, tuple) and k[0] in ("post", "splay")):
            del LR._S[k]


def outrigger_posts(S):
    """L5w's legs: L2's outrigger arms and posts (r 247), no tabs, at shelf height S."""
    set_height(S)
    sh = LR.leg_post(LR.OPTIONS["L2"]["post_y"], tab=None)
    legs = np.vstack([LR.samples(sh, D.place(th, LR.SP, 0.0), 2.0) for th in LR.BEARINGS])
    return legs[legs[:, 2] < BOT], sh


def t0_height():
    """T0: the shelf height at which today's P16s, on hangers, end 10 mm above the balance."""
    P, _ = LR.hanging_samples("L0")
    hg = LR.samples(K.hanger(), D.place(90.0, LR.SP, 0.0), 1.5)
    low = BOT - min(float(P[:, 2].min()), float(hg[:, 2].min()))
    return float(math.ceil((NB["top"] + EASY + low) / 5.0) * 5.0), round(low, 1)


def obstacles(key):
    """Station-frame samples of everything under the shelf for a layout: (points, tilt, kind, S);
    tilt = -1 for fixed parts; kind 0 = actuator or its hanger, 1 = leg."""
    L = LAYOUTS[key]
    src, S = L["src"], L["S"]
    if src == "T0":
        S, _ = t0_height()
        L["S"] = S
    if src in ("L5w", "L6"):
        P, T = np.zeros((0, 3)), np.zeros(0)
        legs, _ = outrigger_posts(S)
        extra = np.zeros((0, 3))
    elif src == "T0":
        P, T = LR.hanging_samples("L0")
        legs, _ = outrigger_posts(S)
        hg = LR.samples(K.hanger(), D.place(90.0, LR.SP, 0.0), 1.5)
        extra = LR.rot3(hg)
    else:
        set_height(S)
        P, T = LR.hanging_samples(src)
        legs = LR.leg_samples(src)
        extra = np.zeros((0, 3))
    A3 = LR.rot3(P) if len(P) else np.zeros((0, 3))
    T3 = np.tile(T, 3) if len(T) else np.zeros(0)
    pts = np.vstack([A3, extra, legs])
    tilt = np.concatenate([T3, np.full(len(extra) + len(legs), -1.0)])
    kind = np.concatenate([np.zeros(len(A3) + len(extra)), np.ones(len(legs))])
    return pts, tilt, kind, S


# --------------------------------------------------------------------------- #
# the sweep
# --------------------------------------------------------------------------- #
def evaluate_pb(Pb, tilt_s, kind_s, phi, F, S, nb=NB):
    """Closest approach of the balance to the samples already in the balance frame, and the clear room
    beside each side door (reach-in), behind each side (sliding door) and behind the top (top door)."""
    prims, e = balance_prims(F, nb)
    d = SR.sdf(Pb, prims)
    k = int(np.argmin(d))
    out = dict(phi=phi, F=F, fit=round(float(d[k]), 1), fit_what="actuator" if kind_s[k] == 0 else "leg",
               fit_tilt=int(tilt_s[k]), shelf=round(S - nb["top"], 1), from_gap=from_gap(phi))
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


def level(r, nb=NB):
    """3 = fits easily and a side door has reach-in and slide-back room; 2 = fits easily, reach-in only;
    1 = fits easily, no door; 0.5 = fits, but under 10 mm; 0 = collides (under 2 mm)."""
    if r["fit"] < GAP:
        return 0.0, None
    if r["fit"] < EASY:
        return 0.5, None
    full = [s for s in ("left", "right") if r[f"door_{s}"] >= nb["access"] and r[f"slide_{s}"] >= nb["slide_len"]]
    if full:
        return 3.0, max(full, key=lambda s: (r[f"slide_{s}"], r[f"door_{s}"]))
    reach = [s for s in ("left", "right") if r[f"door_{s}"] >= nb["access"]]
    if reach:
        return 2.0, max(reach, key=lambda s: (r[f"slide_{s}"], r[f"door_{s}"]))
    return 1.0, None


def rank(r):
    """Best door first, then the display facing a gap (in 15 deg steps), then the clearance, the top door's
    room and the room beside the door."""
    lv, side = level(r)
    sl = min(r[f"slide_{side}"], 300.0) if side else 0.0
    dr = min(r[f"door_{side}"], 150.0) if side else max(min(r["door_left"], 150.0), min(r["door_right"], 150.0))
    return (lv, sl >= NB["slide_len"], -round(r["from_gap"] / 15.0), round(sl / 25.0),
            round(min(r["fit"], 30.0) / 5.0), round(min(r["top_slide"], 150.0) / 25.0), dr)


def rebest(res):
    """Recompute each sweep's best configuration from its rows (after a change to rank())."""
    for r in res["layouts"].values():
        for lab in ("any_tilt", "tilts_to_60"):
            for F, v in r.get(lab, {}).items():
                best = max(v["rows"], key=rank)
                lv, side = level(best)
                v["best"] = dict(best, level=lv, door_side=side)
    return res


def sweep(obs, tmax=90.0, Fs=F_SWEEP, nb=NB):
    pts, tilt, kind, S = obs
    sel = tilt <= tmax
    P, T, Kd = pts[sel], tilt[sel], kind[sel]
    zb = BOT - S
    res = {str(int(F)): [] for F in Fs}
    for phi in PHIS:
        Pb = SR.to_balance(P, phi, zb)
        keep = (Pb[:, 2] < nb["top"] + 40.0) & (np.abs(Pb[:, 0]) < 520.0) & (np.abs(Pb[:, 1]) < 520.0)
        Pb, Tk, Kk = Pb[keep], T[keep], Kd[keep]
        for F in Fs:
            res[str(int(F))].append(evaluate_pb(Pb, Tk, Kk, phi, F, S, nb))
    out = {}
    for F, rows in res.items():
        best = max(rows, key=rank)
        lv, side = level(best)
        bf = max(rows, key=lambda r: r["fit"])
        out[F] = dict(best=dict(best, level=lv, door_side=side), best_fit=bf,
                      n_fit=sum(r["fit"] >= GAP for r in rows), n_fit_easy=sum(r["fit"] >= EASY for r in rows),
                      n_reach=sum(level(r)[0] >= 2 for r in rows), n_full=sum(level(r)[0] >= 3 for r in rows),
                      rows=rows)
    return out


def summary_line(key, v):
    b = v["best"]
    s = b["door_side"]
    return (f"{key:4s} level {b['level']:3.1f} phi {b['phi']:3d} (from gap {b['from_gap']:4.0f}) fit {b['fit']:6.1f} "
            f"({b['fit_what']},{b['fit_tilt']}) door {s} reach L/R {b['door_left']:.0f}/{b['door_right']:.0f} "
            f"slide L/R {b['slide_left']:.0f}/{b['slide_right']:.0f} top {b['top_slide']:.0f} | best fit "
            f"{v['best_fit']['fit']} | n fit {v['n_fit']} easy {v['n_fit_easy']} reach {v['n_reach']} full {v['n_full']}")


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #
def compute():
    t0 = time.time()
    LR.prepare()
    S_t0, low_t0 = t0_height()
    res = dict(balance=NB, f_sweep=list(F_SWEEP), phis_step=5, easy_mm=EASY, gap_mm=GAP,
               t0=dict(shelf_mm=S_t0, hangs_below_shelf_mm=low_t0), layouts={})
    samples = {}
    for key, L in LAYOUTS.items():
        obs = obstacles(key)
        pts, tilt, kind, S = obs
        r = dict(title=L["title"], keeps=L["keep"], shelf_mm=S,
                 hangs_below_shelf_mm=round(float(BOT - pts[kind == 0][:, 2].min()), 1) if (kind == 0).any() else 0.0)
        r["any_tilt"] = sweep(obs, 90.0)
        if 60 in L.get("tmax", ()):
            r["tilts_to_60"] = sweep(obs, 60.0)
        res["layouts"][key] = r
        samples[key] = obs
        for lab in ("any_tilt", "tilts_to_60"):
            if lab in r:
                print(f"{key} {lab} S={S}: " + summary_line(key, r[lab]["120"]), round(time.time() - t0), "s", flush=True)
    np.savez_compressed(CACHE, **{f"{k}_P": v[0] for k, v in samples.items()}, **{f"{k}_T": v[1] for k, v in samples.items()},
                        **{f"{k}_K": v[2] for k, v in samples.items()}, **{f"{k}_S": np.array(v[3]) for k, v in samples.items()})
    return res, samples


def main():
    OUT.mkdir(exist_ok=True)
    if "--figures-only" in sys.argv:
        res = rebest(json.loads((HERE / "new_scale.json").read_text()))
        (HERE / "new_scale.json").write_text(json.dumps(res, indent=1, default=float) + "\n")
        z = np.load(CACHE)
        samples = {k: (z[f"{k}_P"], z[f"{k}_T"], z[f"{k}_K"], float(z[f"{k}_S"])) for k in LAYOUTS}
    else:
        res, samples = compute()
        (HERE / "new_scale.json").write_text(json.dumps(res, indent=1, default=float) + "\n")
    if "--no-figures" not in sys.argv:
        import new_scale_figs as NF
        NF.all_figures(res, samples)


if __name__ == "__main__":
    main()
