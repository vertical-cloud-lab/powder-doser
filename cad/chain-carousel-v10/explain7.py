"""v7's clips (Sam, PR #185, 2026-11-10: "provide a similar table of changes with gifs showing every change"). One clip per
change and an overview; every frame is the v7 CAD (layout.placements) in the state described, moving by the model's own
kinematics (explain.py's Clip: the parts a step is about keep their colours, the rest is washed out, callouts name the parts).

    xvfb-run -a python explain7.py overview|ladder|plate|ec|station|tilt90|guides|balance [--preview]
    -> renders/v7/<name>_v7.{mp4,gif}
"""
from __future__ import annotations

import math
import sys

import numpy as np

import explain as E
import layout as L
import render as R
import render_balance as RB
from params import (BEAKER_H, BEAKER_RIM_Z, DOOR_TRAVEL, EC7_PIN, EC7_SHOE_X, EC7_SHOE_Y, GUIDE7_FUNNEL, HINGE_X, KC7_A, KC7_B, KC7_C, KC7_TIP,
                    MODULE_LINKS, PARK_DROP7, RUN_DIRECTION, BAL7_DOOR_OPEN, BAL7_LID_HOLE, CLIP2_X, CAP_CRADLE_X, KEEPER6_X, LATCH_Y6)

E.OUT = R.OUT / "v7"


class _FastView(R.View):
    """No multisampling: under llvmpipe 4x MSAA took 15 s a frame, without it 1.7 s (the GIFs are downscaled anyway)."""
    def __init__(self, w=1600, h=1000, bg=(1, 1, 1), samples=0):
        super().__init__(w, h, bg, 0)


R.View = _FastView
H = L.HINGE_STATION
D = L.DOSE_POINT
SY = L.STATION_Y
PAN = L.scale_pan_target()
part, sam, ec, world = E.part, E.sam, E.ec, E.world
TAG = "chain carousel v7 · PR #185 · 2026-11-10"
S0 = dict(enclosure=False)
FPS = E.FPS
GLASSY = ("bal7_glass", "bal7_door_left", "bal7_door_right", "bal7_lid", "beaker")


def opac(pl, extra=None):
    o = {}
    for k, p in R.keyed(pl):
        if p.key in GLASSY:
            o[k] = 0.3
        elif p.key.startswith(("panel_", "hatch_")):
            o[k] = 0.18
        elif extra and p.key in extra:
            o[k] = extra[p.key]
    return o


def ext_ro(st: L.State) -> str:
    return f"P16 {L.p16_7_ext(st.tilt, st.ext):5.1f} of 150 mm out"


def tilt_ro(st: L.State) -> str:
    return f"tilt {st.tilt:4.1f} deg\n" + ext_ro(st)


def rise_ro(st: L.State) -> str:
    return f"EC rise {st.ext:4.1f} of {PARK_DROP7:.0f} mm\n" + ext_ro(st)


def wide(p) -> bool:
    return p.group in ("enclosure", "elec")


def near_cut(p) -> bool:
    """Section on the station from -y: everything on the near (-y) side goes, except the station's own parts. The -y guide
    (the cone) stands in front of the EC's tail, so it goes too; the balance loses its -y door."""
    if wide(p):
        return True
    y = p.M[1, 3]
    if p.group == "scale":
        return p.key == "bal7_door_left"
    if p.key == "guide7_cone":
        return True
    if p.group in ("station_act", "station_ec") or (p.group == "modules" and p.module == 0) or p.key == "guide7_vee":
        return False
    if p.group == "station":
        return y < SY - 100.0
    if p.key in ("cross7", "rung"):
        return y < SY - 100.0
    return y < SY - 35.0


CAM_SIDE = ((128.0, SY, 330.0), (0.0, -1.0, 0.08), 660)          # the whole station, side section
CAM_SIDE90 = ((128.0, SY, 400.0), (0.0, -1.0, 0.05), 880)        # ... with room for the module at 90 deg


# ---------------------------------------------------------------- 1. overview
def overview(preview=False):
    c = E.Clip("overview_v7", TAG, 4, preview)
    camA = ((120, 0, 470), (-1.0, -1.05, 0.5), 1750)
    camB = ((120, 0, 470), (-1.1, 0.9, 0.42), 1750)
    lab = [("13 modules outside the loop\n(v6's long plates)", sam(6, (150, 0, 0)), "R"),
           ("Station: one P16-150 under\nthe EC, behind the balance", part("actuator_body", local=(0, 0, 60.0)), "R"),
           ("Balance: a base and a draft\ncage, nothing tall behind it", part("bal7_frame", local=(0.0, -98.0, 200.0)), "L"),
           ("Ladder rungs and two new\ncross bars between them", part("cross7", name="guide", local=(0, 0, 60.0)), "L")]
    c.chapter(1, "Chain carousel v7")
    c.move(3.5, lambda t, i, n: dict(st=L.State(ext=0.0, **S0), cam=R.cam_lerp(camA, camB, t), hide=wide, labels=lab if t > 0.25 else (),
                                     opacity=opac,
                                     text="v7 mixes v6 and v5 with Sam's second Nov 10 note: v6's ladder (now with cross bars to mount things in the "
                                          "middle) and long plate; one P16 under the station again, as v2-v5; the dock on posts printed on the plate, so "
                                          "the EC is Sam's short carriage; the balance re-modelled as a base and a draft cage.",
                                     save_as="o1" if preview else None))
    c.chapter(2, "Index one module")
    c.move(2.0, lambda t, i, n: dict(st=L.State(shift=-RUN_DIRECTION * MODULE_LINKS * (1 - t), ext=0.0, **S0), cam=R.cam_lerp(camB, CAM_SIDE, t),
                                     hide=lambda p: wide(p) if t < 0.6 else near_cut(p), opacity=opac,
                                     readout=lambda st: f"chain {abs(st.shift) * 9.525:4.1f} mm to go", text="The NEMA 34 moves both chains 8 links.",
                                     save_as="o2" if preview else None))
    c.chapter(3, "Dock, tilt to 30 deg and dose, with one P16")
    c.move(1.5, lambda t, i, n: dict(st=L.State(ext=PARK_DROP7 * t, **S0), cam=CAM_SIDE, hide=near_cut, opacity=opac, readout=rise_ro,
                                     text="The P16 lifts the EC 10 mm out of its guides onto the posts' dock.", save_as="o3" if preview else None))
    c.move(1.5, lambda t, i, n: dict(st=L.State(tilt=30.0 * t, **S0), cam=CAM_SIDE, hide=near_cut, opacity=opac, readout=tilt_ro,
                                     text="Extending further, the same P16 turns the docked EC and the module about the hinge.", save_as="o4" if preview else None))
    g = {"g": None}
    z_land = BEAKER_RIM_Z - BEAKER_H + 6.0

    def dose(t, i, n):
        if g["g"] is None:
            g["g"] = RB.Grains(c.v)
        tt = i / FPS
        return dict(st=L.State(tilt=30.0, spin=2 * math.pi * 1.5 * t, **S0), cam=CAM_SIDE, hide=near_cut, opacity=opac,
                    before=lambda v, s: g["g"].set(tt, True, z_land), readout=lambda st: f"tilt 30.0 deg\nauger {st.spin / (2 * math.pi):3.1f} turns",
                    text="The NEMA 11 turns the auger; the dose falls through the hole in the balance's lid into the beaker.",
                    save_as="o5" if preview else None)
    c.move(1.5, dose, eased=False)
    if g["g"] is not None:
        g["g"].set(0.0, False, z_land)
    c.chapter(4, "...on to 90 deg, back, and down")
    c.move(2.0, lambda t, i, n: dict(st=L.State(tilt=30.0 + 60.0 * t, **S0), cam=CAM_SIDE90, hide=near_cut, opacity=opac, readout=tilt_ro,
                                     text="The full range is 0-90 deg: 130 of the P16's 150 mm.", save_as="o6" if preview else None))
    c.move(2.0, lambda t, i, n: dict(st=L.State(tilt=90.0 * (1 - t), **S0), cam=CAM_SIDE90, hide=near_cut, opacity=opac, readout=tilt_ro, text="",
                                     save_as="o7" if preview else None))
    c.move(1.0, lambda t, i, n: dict(st=L.State(ext=PARK_DROP7 * (1 - t), **S0), cam=CAM_SIDE90, hide=near_cut, opacity=opac, readout=rise_ro, text="",
                                     save_as="o8" if preview else None))
    c.hold(1.0)
    c.done()


# ---------------------------------------------------------------- 2. the ladder and the cross bars
def ladder(preview=False):
    c = E.Clip("ladder_v7", TAG, 3, preview)
    cam0 = ((150, 0, 300), (-1.0, -1.25, 0.6), 1400)
    cam1 = ((150, 0, 300), (-1.25, 0.75, 0.5), 1400)
    frame_only = lambda p: p.group in ("frame", "plates", "bearings", "shafts", "sprockets")                     # noqa: E731
    stn = lambda p: p.group in ("station", "station_act", "station_ec") and p.key not in ("hold_down", "hall_switch", "insert_m5", "m5x16_shcs",
                                                                                         "side_tab", "side_tab_m", "m5x8_shcs", "latch_rail")   # noqa: E731
    rung_col = lambda p: (0.95, 0.55, 0.12) if p.key == "rung" else ((0.90, 0.12, 0.10) if p.key == "cross7" else None)   # noqa: E731
    lab1 = [("Rungs between the front and\nback posts (v6, kept)", part("rung", name="lower +y", local=(0, 0, 220.0)), "R"),
            ("Upper rungs", part("rung", name="upper -y", local=(0, 0, 220.0)), "L")]
    lab2 = [("NEW cross bar on the lower\nrungs: the P16's clevis", part("cross7", name="P16", local=(0, 0, 90.0)), "R"),
            ("NEW cross bar on the upper\nrungs: the two guides", part("cross7", name="guide", local=(0, 0, 250.0)), "L")]
    lab3 = [("P16-150 on its clevis", part("actuator_body", local=(0, 0, 50.0)), "R"),
            ("Guides (funnel mouths,\ncone and vee seats)", part("guide7_vee"), "L"),
            ("EC v7 on the P16's rod end", part("sam_electronics_carriage", local=(40.0, 0.0, 40.0)), "L")]
    steps = [("1. The ladder rungs stay", lambda p: not frame_only(p), lab1,
              "v6's ladder: on each side two 2020 rungs run between the front and back posts, on corner brackets. Nothing stands on the base "
              "rails but the corner posts. v7 moves the lower rungs down to 200 mm to carry the P16's cross bar."),
             ("2. NEW: two cross bars between the rungs", lambda p: not frame_only(p), lab1 + lab2,
              "Sam: \"You can add another cross bar ... so you can attach things in the middle\". Two 2020 cross bars (red) run between the "
              "rungs: one on the lower rungs at x 250 for the P16's clevis, one on the upper rungs just behind the balance for the guides."),
             ("3. What hangs on them", lambda p: not (frame_only(p) or stn(p)), lab2 + lab3,
              "The P16's clevis bolts onto the lower cross bar, the two guides onto the upper one; nothing is on the side plates or the "
              "base rails, and the dose falls clear of every bar.")]
    cam2a = ((170, 0, 270), (-1.0, -0.75, 0.22), 950)
    cam2b = ((170, 0, 270), (-1.0, 0.55, 0.18), 950)
    for i, (title, hide, labs, text) in enumerate(steps):
        c.chapter(i + 1, title)
        c.move(2.8, lambda t, ii, n, hide=hide, text=text, i=i, labs=labs: dict(
            st=L.State(ext=0.0, enclosure=False, scale=False),
            cam=R.cam_lerp(cam0, cam1, (i + t) / 2.0) if i < 2 else R.cam_lerp(cam2a, cam2b, t), hide=hide,
            accent=rung_col if i > 0 else (lambda p: (0.95, 0.55, 0.12) if p.key == "rung" else None), labels=labs, text=text,
            save_as=f"g{i}" if preview else None), eased=False)
        c.hold(0.8)
    c.done()


# ---------------------------------------------------------------- 3. mounting plate v7: the dock on posts
def plate(preview=False):
    c = E.Clip("plate_v7", TAG, 2, preview)
    k = 3                                                     # module 4: at the loading position (+y side, facing the side hatch)
    Lf = L.load_frame()
    cen = L.to_world(Lf, (0.0, L.HINGE_W, HINGE_X + 95.0))
    cam_a = (tuple(cen), (0.45, 1.0, 0.35), 430)
    cam_b = (tuple(cen), (-0.35, 1.0, 0.2), 470)
    mod = lambda p: p.module == k and p.group == "modules"                     # noqa: E731
    lab = [("Post A: printed dome,\nsits in the EC's cone", sam(k, (KC7_A[0], KC7_A[1], KC7_TIP + 3.0)), "L"),
           ("Post B: dome, in the vee", sam(k, (KC7_B[0], KC7_B[1], KC7_TIP + 3.0)), "L"),
           ("Post C: flat tip,\nball C lands on it", sam(k, (KC7_C[0], KC7_C[1], KC7_TIP)), "R"),
           ("A magnet in each post\n(dropped in at a print pause)", part("kc6_magnet", module=k, nth=2, local=(0, 0, 1.6)), "R"),
           ("v6's long plate: clip 2,\ncap saddle, keeper (kept)", sam(k, (156.0, 0.0, -16.5)), "R")]
    cen0 = tuple(L.to_world(L.sam_frame(L.station_frame(), 0.0), (58.0, 0.0, 4.0)))
    cam_s0 = (cen0, (-0.65, -1.0, -0.50), 250)
    cam_s1 = (cen0, (0.30, -1.0, -0.35), 230)
    mod0 = lambda p: p.module == 0 and p.group == "modules"                    # noqa: E731
    hide0 = lambda p: not (p.module == 0 and p.group in ("modules", "carriages"))   # noqa: E731
    lab = [("Post A: printed dome,\nsits in the EC's cone", sam(0, (KC7_A[0], KC7_A[1], KC7_TIP + 3.0)), "L"),
           ("Post B: dome, in the vee", sam(0, (KC7_B[0], KC7_B[1], KC7_TIP + 3.0)), "R"),
           ("Post C: flat tip,\nball C lands on it", sam(0, (KC7_C[0], KC7_C[1], KC7_TIP)), "R"),
           ("A magnet in each post\n(dropped in at a print pause)", sam(0, (KC7_A[0], KC7_A[1], KC7_TIP - 3.4)), "L"),
           ("v6's long plate: clip 2,\ncap saddle, keeper (kept)", sam(0, (156.0, -16.0, -14.0)), "R")]
    c.chapter(1, "1. Mounting plate v7: the plate reaches past the auger")
    c.move(4.5, lambda t, i, n: dict(st=L.State(ext=0.0, **S0), cam=R.cam_lerp(cam_s0, cam_s1, t), hide=hide0, focus=mod0, labels=lab if t > 0.3 else (),
                                     opacity=lambda pl: {kk: 0.55 for kk, p in R.keyed(pl) if p.module == 0 and p.key == "sam_mounting_plate"},
                                     text="v4-v6 put the dock on the plate's face, so the EC had to reach round the auger to it. v7 prints three "
                                          "posts on the plate beside the tube, out past the auger to the side the scale is on: domes on A and B, "
                                          "a flat on C, a magnet under each tip. The EC now meets them just beyond the auger.",
                                     save_as="p1" if preview else None))
    c.hold(1.5)
    c.chapter(2, "2. The auger still pulls straight off")
    lab2 = [("The posts stand beside the\ntube: the auger passes between", sam(k, (KC7_A[0], 0.0, KC7_TIP)), "R")]
    c.move(4.0, lambda t, i, n: dict(st=L.State(out_auger=k, auger_out=75.0 * math.sin(math.pi * t), hatch_side=110.0, **S0), cam=cam_b, hide=wide,
                                     focus=mod, labels=lab2, readout=lambda st: f"auger {st.auger_out:4.1f} mm off",
                                     text="The posts are 31 mm apart round a 25 mm tube and stop short of the 44T gear, so at the side hatch the auger "
                                          "still comes straight out of both clips, and a full one snaps back in.", save_as="p2" if preview else None),
           eased=False)
    c.hold(0.8)
    c.done()


# ---------------------------------------------------------------- 4. EC v7: short, docking on the posts
def ec_clip(preview=False):
    c = E.Clip("ec_v7", TAG, 2, preview)
    cen = (H[0] + 50.0, SY, H[2] - 26.0)
    cam_a = (cen, (-0.22, -1.0, -0.22), 270)
    cam_b = (cen, (0.06, -1.0, -0.06), 245)
    foc = lambda p: p.group == "station_ec" or (p.module == 0 and p.key in ("sam_mounting_plate", "kc6_magnet", "door_housing", "door_shutter"))  # noqa: E731
    hide = lambda p: near_cut(p) or p.group in ("scale", "station_act") or p.key in ("guide7_vee", "guide7_cone")    # noqa: E731
    lab = [("Cone (A) on an ear", ec((KC7_A[0], KC7_A[1], 24.0)), "L"),
           ("Ball C on its ear", ec((KC7_C[0], KC7_C[1], 21.0)), "R"),
           ("Door finger", ec((-2.0, 7.5, 24.0)), "L"),
           ("Tail: the P16's pin\nand two guide shoes", ec((EC7_PIN[0] + 12.0, -18.5, 50.0)), "R"),
           ("NEMA 11 and 20T pinion\n(Sam's carriage, turned over)", ec((40.0, 0.0, 38.0)), "R")]
    lab2 = [("Post A's dome", sam(0, (KC7_A[0], KC7_A[1], KC7_TIP + 2.0)), "L"),
            ("Post C's flat", sam(0, (KC7_C[0], KC7_C[1], KC7_TIP)), "R"),
            ("Outlet door", part("door_shutter", module=0), "L")]
    c.chapter(1, "1. EC v7: Sam's carriage turned over, no arms")
    c.move(4.0, lambda t, i, n: dict(st=L.State(ext=0.0, **S0), cam=R.cam_lerp(cam_a, cam_b, t), hide=hide, focus=foc, labels=lab if t > 0.2 else (),
                                     readout=rise_ro,
                                     text="v4-v6's EC carried two tall arms that reached round the auger to the plate. v7's is Sam's compact "
                                          "carriage with three ears at its rim: the cone (A), the dowel vee (B) and ball C, a magnet behind each. "
                                          "A tail behind its back wall, under the 44T gear, takes the P16's pin and two guide shoes.",
                                     save_as="e1" if preview else None))
    c.chapter(2, "2. 10 mm up onto the posts; the door opens")
    c.move(4.5, lambda t, i, n: dict(st=L.State(ext=PARK_DROP7 * t, **S0), cam=cam_b, hide=hide, focus=foc, labels=lab2,
                                     readout=lambda st: rise_ro(st) + f"\ndoor {L.door_open(st):3.1f} of {DOOR_TRAVEL:.0f} mm open",
                                     text="The P16 lifts the EC 10 mm (v6: 28): the domes drop into the cone and the vee and ball C lands on post C's "
                                          "flat. In the last 6 mm the finger pushes the outlet door open. Parked, the EC clears the passing modules' "
                                          "gears by 8 mm and their domes by 7.8 mm.",
                                     save_as="e2" if preview else None))
    c.hold(1.5)
    c.done()


# ---------------------------------------------------------------- 5. the station: one P16
def station(preview=False):
    c = E.Clip("station_v7", TAG, 3, preview)
    foc = lambda p: p.group in ("station_act", "station_ec") or p.key in ("clevis_bracket", "cross7", "guide7_vee") or p.module == 0  # noqa: E731
    lab = [("One P16-150 (pot feedback)", part("actuator_body", local=(0, 0, 70.0)), "R"),
           ("Its clevis on the P16\ncross bar (lower rungs)", part("clevis_bracket"), "R"),
           ("Rod-end pin on\nthe EC's tail", ec((EC7_PIN[0], 0.0, EC7_PIN[1])), "R"),
           ("Guide on the upper\ncross bar", part("guide7_vee", local=(L.SHOE7_XC, 27.0, 345.0)), "R"),
           ("Draft cage: the P16\npasses over its back", part("bal7_frame", local=(85.0, 0.0, 307.0)), "L")]

    c.chapter(1, "1. One actuator, under the station again")
    c.move(3.0, lambda t, i, n: dict(st=L.State(ext=0.0, **S0), cam=CAM_SIDE, hide=near_cut, focus=foc, opacity=opac, labels=lab if t > 0.15 else (),
                                     readout=rise_ro,
                                     text="v6's lift frame (two P16-50s, bars and hooks under the dose) and its tilt P16 on the back plate are gone. "
                                          "One P16-150 leans 44.5 deg from a clevis on a cross bar behind the balance, over the draft cage's "
                                          "back corner, to a pin on the EC's tail.",
                                     save_as="s1" if preview else None))
    c.chapter(2, "2. It lifts the EC onto the dock")
    c.move(2.0, lambda t, i, n: dict(st=L.State(ext=PARK_DROP7 * t, **S0), cam=CAM_SIDE, hide=near_cut, focus=foc, opacity=opac, readout=rise_ro,
                                     text="Extending 7.3 mm lifts the EC 10 mm up its two guides; the shoes leave the guides' funnel mouths in the last "
                                          "4 mm and the EC seats on the plate's posts.", save_as="s2" if preview else None))
    c.chapter(3, "3. ...then tilts the module and doses")
    c.move(2.5, lambda t, i, n: dict(st=L.State(tilt=30.0 * t, **S0), cam=CAM_SIDE, hide=near_cut, focus=foc, opacity=opac, readout=tilt_ro,
                                     text="Extending further turns the docked EC and module about the hinge: 30 deg (the default) is 35 mm out. "
                                          "No bar or hook is under the dose.", save_as="s3" if preview else None))
    g = {"g": None}
    z_land = BEAKER_RIM_Z - BEAKER_H + 6.0

    def dose(t, i, n):
        if g["g"] is None:
            g["g"] = RB.Grains(c.v)
        tt = i / FPS
        return dict(st=L.State(tilt=30.0, spin=2 * math.pi * 1.5 * t, **S0), cam=CAM_SIDE, hide=near_cut, focus=foc, opacity=opac,
                    before=lambda v, s: g["g"].set(tt, True, z_land), readout=lambda st: f"tilt 30.0 deg\nauger {st.spin / (2 * math.pi):3.1f} turns",
                    text="The NEMA 11 turns the auger and the dose falls through the hole in the balance's lid into the beaker.",
                    save_as="s4" if preview else None)
    c.move(2.0, dose, eased=False)
    if g["g"] is not None:
        g["g"].set(0.0, False, z_land)
    c.hold(1.0)
    c.done()


# ---------------------------------------------------------------- 6. 90 degrees
def tilt90(preview=False):
    c = E.Clip("tilt90_v7", TAG, 2, preview)
    foc = lambda p: p.group in ("station_act", "station_ec") or p.key in ("clevis_bracket",) or p.module == 0 or p.key == "carriage"  # noqa: E731
    lab = [("P16: 130 of 150 mm\nout at 90 deg", part("actuator_rod", local=(0, 0, 150.0)), "R"),
           ("It passes behind the EC,\nthrough the carriage's opening", ec((EC7_PIN[0] - 20.0, 0.0, EC7_PIN[1] + 6.0)), "R"),
           ("Plate edge: clear of the\ncarriage's opening (v6's)", sam(0, (-5.0, 0.0, -16.0)), "L")]
    c.chapter(1, "1. 0 to 90 deg with the same P16")
    c.move(5.5, lambda t, i, n: dict(st=L.State(tilt=90.0 * t, **S0), cam=CAM_SIDE90, hide=near_cut, focus=foc, opacity=opac,
                                     labels=lab if t > 0.85 else (), readout=tilt_ro,
                                     text="The P16's pin is 78 mm behind and 54 mm under the hinge axis, so the whole 0-90 deg takes 122 mm of "
                                          "stroke, and its lever arm about the hinge grows from 21 mm docked to 95 mm at 64 deg. Nothing wide turns "
                                          "with the module (v5's lift bar climbed into the corner modules from 42 deg).",
                                     save_as="t1" if preview else None))
    c.hold(1.5)
    c.chapter(2, "2. Back to 0, and down onto the guides' seats")
    c.move(3.5, lambda t, i, n: dict(st=L.State(tilt=90.0 * (1 - t), **S0), cam=CAM_SIDE90, hide=near_cut, focus=foc, opacity=opac, readout=tilt_ro,
                                     text="Retracting brings it back (gravity helps); below 0 deg the EC comes off the dock and the guides take it "
                                          "down to its seats.", save_as="t2" if preview else None))
    c.move(1.5, lambda t, i, n: dict(st=L.State(ext=PARK_DROP7 * (1 - t), **S0), cam=CAM_SIDE90, hide=near_cut, focus=foc, opacity=opac,
                                     readout=rise_ro, text="", save_as="t3" if preview else None))
    c.hold(0.8)
    c.done()


# ---------------------------------------------------------------- 7. the guides' funnels and seats, round the EC's tail
def guides(preview=False):
    c = E.Clip("guides_v7", TAG, 2, preview)
    foc = lambda p: p.key in ("guide7_cone", "guide7_vee", "cross7", "sam_electronics_carriage")    # noqa: E731
    hide = lambda p: wide(p) or p.group in ("modules", "carriages", "chain", "scale", "drive") or p.key in (   # noqa: E731
        "side_plate_front", "side_plate_back", "nema34", "latch_rail", "hold_down", "hall_switch", "side_tab", "side_tab_m", "insert_m5",
        "m5x16_shcs", "m5x8_shcs", "ext_x", "ext_y", "ext_post", "foot", "tnut_m5")
    z_top = L.GUIDE7_TOP_Z
    seat = L.GUIDE7_SEAT_Z

    def st_at(t):
        e = PARK_DROP7 * (1 - t)
        zs = seat + 0.5 + e                                  # the shoe's underside
        f = min(1.0, max(0.0, (zs - (z_top - GUIDE7_FUNNEL)) / GUIDE7_FUNNEL))
        return L.State(ext=e, lift_dx=2.0 * f, **S0)
    for i, (side, key, nm, kind) in enumerate(((1, "guide7_vee", "+y", "vee"), (-1, "guide7_cone", "-y", "cone"))):
        cen = (L.SHOE7_XC, SY + side * L.SHOE7_YC, 362.0)
        cam = (cen, (0.60, side * 1.0, 0.38), 200)
        yl = L.SHOE7_YC
        lab = [(f"Guide {nm} on the upper\ncross bar", part(key, local=(L.SHOE7_XC + 9.0, yl + 4.0, 345.0)), "L"),
               ("Funnel mouth: 4 mm\neach side, 45 deg", part(key, local=(L.SHOE7_XC - 7.1 - 2.0, yl, z_top - 1.0)), "L"),
               ("Shoe on the EC's tail,\nconical nose", ec(((EC7_SHOE_X[0] + EC7_SHOE_X[1]) / 2, -side * (EC7_SHOE_Y[0] + EC7_SHOE_Y[1]) / 2, 50.0)), "R"),
               (f"{kind.capitalize()} seat in the floor", part(key, local=(L.SHOE7_XC, yl, seat - 2.0)), "R")]
        c.chapter(i + 1, f"{i + 1}. Guide {nm}: funnel in, {kind} seat at the bottom")
        c.move(4.5, lambda t, ii, n, lab=lab, cam=cam, key=key, kind=kind: dict(
            st=st_at(t), cam=cam, hide=hide, focus=foc, labels=lab, opacity=lambda pl, key=key: opac(pl, {key: 0.45}),
            readout=lambda st: f"EC {st.lift_dx:3.1f} mm off line\nshoe {seat + 0.5 + st.ext - seat:4.1f} mm over the seat",
            text=(f"v6's funnels and seats, moved to the EC's tail (Sam: \"apply them wherever we move the guides\"). Coming down 2 mm off line, "
                  f"the shoe meets the 45 deg funnel, which centres it in the channel; at the bottom its 90 deg nose sits in a {kind}: the cone "
                  f"fixes that shoe, the vee only its x, so the EC parks in the same place every time."), save_as=f"u{i}" if preview else None),
            eased=False)
        c.hold(1.0)
    c.done()


# ---------------------------------------------------------------- 8. the balance
def balance(preview=False):
    c = E.Clip("balance_v7", TAG, 4, preview)
    ghost = [L.Placement("hr202i_body", "v5's HR-202i model (A&D's rear housing)", L.T(None, (PAN[0], PAN[1], 0.0)), 12, (0.9, 0.1, 0.1), "ghost")]
    red = lambda p: (0.90, 0.12, 0.10) if p.group == "ghost" else None              # noqa: E731
    foc = lambda p: p.group in ("scale", "ghost", "station_act") or p.key in ("clevis_bracket", "cross7")      # noqa: E731
    camI = ((PAN[0] + 70.0, SY, 230.0), (-0.75, -1.0, 0.45), 900)
    cam_side = ((110.0, SY, 260.0), (0.0, -1.0, 0.1), 780)
    lab0 = [("v5/v6: A&D's rear housing\n(from their drawing)", world((PAN[0] + 200.0, SY - 100.0, 200.0)), "R")]
    lab1 = [("Draft cage: v5's chamber,\n183 x 164.5 x 250 mm", part("bal7_frame", local=(-86.5, -98.0, 250.0)), "L"),
            ("Weighing base and display", part("bal7_base", local=(-120.0, 0.0, 30.0)), "L"),
            ("Nothing behind the cage:\nthe P16 stands there", part("actuator_body", local=(0, 0, 60.0)), "R")]
    lab2 = [("Dosing lid: a 30 mm hole\nunder the exit (no top door)", part("bal7_lid", local=(0.0, 0.0, 306.0)), "L"),
            ("Beaker on v5's riser", part("beaker"), "L")]
    hide1 = lambda p: wide(p) or (p.group == "scale")              # noqa: E731
    hide2 = lambda p: wide(p) or p.group == "ghost"                # noqa: E731
    c.chapter(1, "1. v5 and v6 drew A&D's rear housing")
    c.move(3.0, lambda t, i, n: dict(st=L.State(ext=0.0, extra=list(ghost), **S0), cam=camI, hide=hide1, focus=foc, accent=red, labels=lab0,
                                     text="v5 and v6 drew the HR-202i from A&D's manual and DXF, with a housing behind the chamber (red). Sam: the lab's "
                                          "balances have no large module at the back; the draft cage is the main feature, on the weighing base.",
                                     save_as="b1" if preview else None))
    c.chapter(2, "2. v7: a weighing base and a draft cage")
    c.move(3.0, lambda t, i, n: dict(st=L.State(ext=0.0, **S0), cam=R.cam_lerp(camI, cam_side, t), hide=lambda p: near_cut(p) if t > 0.5 else hide2(p),
                                     focus=foc, opacity=opac, labels=lab1 if t > 0.3 else (),
                                     text="The cage keeps v5's chamber, pan and display, so the beaker and the fall are v5's; 200 x 253 x 311 mm, about the "
                                          "HR-100A's outline. The room behind the cage now holds the P16, which leans over the cage's back corner.",
                                     save_as="b2" if preview else None))
    g = {"g": None}
    z_land = BEAKER_RIM_Z - BEAKER_H + 6.0
    cam_lid = ((PAN[0] + 10.0, SY, 330.0), (0.25, -1.0, 0.35), 330)

    def dose(t, i, n):
        if g["g"] is None:
            g["g"] = RB.Grains(c.v)
        tt = i / FPS
        return dict(st=L.State(tilt=30.0, spin=2 * math.pi * 1.5 * t, **S0), cam=cam_lid, hide=near_cut, focus=lambda p: p.group == "scale" or p.module == 0,
                    opacity=opac, before=lambda v, s: g["g"].set(tt, True, z_land), labels=lab2,
                    readout=lambda st: "tilt 30.0 deg", text="The exit is on the hinge axis, so at every tilt the stream falls through the same 30 mm "
                                                             "hole in the lid that replaces the top door, into the beaker; nothing else opens.",
                    save_as="b3" if preview else None)
    c.chapter(3, "3. The dose falls through the lid's hole")
    c.move(3.0, dose, eased=False)
    if g["g"] is not None:
        g["g"].set(0.0, False, z_land)
    c.chapter(4, "4. The beaker comes out through a side door")
    cam_door = ((PAN[0] - 20.0, SY - 60.0, 200.0), (-0.45, -1.0, 0.35), 620)

    def door(t, i, n):
        d = BAL7_DOOR_OPEN * min(1.0, t / 0.35)
        u = max(0.0, (t - 0.35) / 0.65)
        dz = 8.0 * min(1.0, u / 0.2)
        dx = -50.0 * min(1.0, max(0.0, (u - 0.2) / 0.3))
        dy = -150.0 * max(0.0, (u - 0.5) / 0.5)
        return dict(st=L.State(ext=0.0, side_door=d, beaker_dx=dx, beaker_dy=dy, beaker_dz=dz, **S0), cam=cam_door, hide=wide,
                    focus=lambda p: p.group == "scale", opacity=opac, readout=lambda st: f"side door {st.side_door:4.1f} of {BAL7_DOOR_OPEN:.0f} mm",
                    text="The -y side door slides back 70 mm, enough for the 38 mm beaker, and stops short of the P16's cross bar.",
                    save_as="b4" if preview else None)
    c.move(3.5, door, eased=False)
    c.hold(0.8)
    c.done()


CLIPS = {"overview": overview, "ladder": ladder, "plate": plate, "ec": ec_clip, "station": station, "tilt90": tilt90, "guides": guides,
         "balance": balance}

if __name__ == "__main__":
    pv = "--preview" in sys.argv
    for a in sys.argv[1:]:
        if a in CLIPS:
            CLIPS[a](pv)
