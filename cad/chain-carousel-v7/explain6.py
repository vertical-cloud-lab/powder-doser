"""v6's clips (Sam, PR #185, 2026-11-10: "provide supporting gifs to specifically highlight each change and to give an
overview of the new system"). One clip per change and an overview; every frame is the v6 CAD (layout.placements) in the
state described, moving by the model's own kinematics (explain.py's Clip: the parts a step is about keep their colours,
the rest is washed out, callouts name the parts).

    xvfb-run -a python explain6.py plate|latch|ladder|tilt90|guides|overview [--preview]
    -> renders/v6/<name>.{mp4,gif}
"""
from __future__ import annotations

import math
import sys

import numpy as np

import explain as E
import layout as L
import render as R
import render_balance as RB
from params import (LATCH6_FOLLOW_X, LATCH6_MANUAL, LATCH_TRAVEL, LATCH_Y6, MODULE_LINKS, PARK_DROP, RUN_DIRECTION, SHELF6, SHOE,
                    TILT6_B, TILT6_Y, ACT_RETRACTED, KEEPER6_X, CLIP2_X, CAP_CRADLE_X, KC4_A, KC4_B, KC4_C, OPEN_X6, HINGE_X)
import parts6 as P6

E.OUT = R.OUT / "v6"


class _FastView(R.View):
    """No multisampling: under llvmpipe 4x MSAA took 15 s a frame, without it 1.7 s (the GIFs are downscaled anyway)."""
    def __init__(self, w=1600, h=1000, bg=(1, 1, 1), samples=0):
        super().__init__(w, h, bg, 0)


R.View = _FastView
H = L.HINGE_STATION
D = L.DOSE_POINT
part, sam, ec, world, keys = E.part, E.sam, E.ec, E.world, E.keys
TAG = "chain carousel v6 · PR #185 · 2026-11-10"
S0 = dict(enclosure=False)


def tilt_len(st: L.State) -> float:
    C = L.electronics_frame(st.tilt, st.ext)
    qx, qz = P6.tilt_pin_ec()
    Pt = L.to_world(C, (qx, L.STATION_Y - TILT6_Y, qz))
    return float(np.linalg.norm(Pt - np.array([TILT6_B[0], TILT6_Y, TILT6_B[1]])))


def wide(p) -> bool:
    return p.group in ("enclosure", "elec")


def near_cut(p) -> bool:
    """Section from -y: everything on the near (-y) side goes, except the station's own parts."""
    if wide(p):
        return True
    y = p.M[1, 3]
    if p.group == "scale":
        return p.key == "hr202i_door_left"
    if p.key in ("actuator_body", "actuator_rod", "tilt_bracket") or p.group == "station_ec" or (p.group == "modules" and p.module == 0):
        return False
    if p.group in ("station_lift", "station_act", "station"):
        return y < -100.0
    return y < L.STATION_Y - 35.0


# ---------------------------------------------------------------- 1. the mounting plate
def plate(preview=False):
    c = E.Clip("plate_v6", TAG, 3, preview)
    k = 3                                                     # module 4: at the loading position (+y side, facing the side hatch)
    Lf = L.load_frame()
    cen = L.to_world(Lf, (0.0, L.HINGE_W, HINGE_X + 120.0))
    cam_a = (tuple(cen), (0.35, 1.0, 0.25), 520)
    cam_b = (tuple(cen), (-0.45, 1.0, -0.15), 470)
    mod = lambda p: p.module == k and p.group == "modules"                     # noqa: E731
    lab = [("Sam's clip 1 and gear housing\n(kept as he drew them)", sam(k, (34.0, 0.0, -14.0)), "L"),
           ("NEW clip 2, halfway between\nthe gear and the cap", sam(k, (156.0, 0.0, -16.5)), "R"),
           ("NEW saddle under the cap", sam(k, (236.0, 0.0, -14.0)), "R"),
           ("NEW keeper at the back end:\nthe latch pin goes in here", sam(k, (248.0, LATCH_Y6, -10.0)), "R"),
           ("The plate now runs to the cap\n(v5's stopped at 106 mm)", sam(k, (200.0, -20.0, -15.5)), "L")]
    c.chapter(1, "1. Mounting plate v6: longer, with a second clip")
    c.move(4.0, lambda t, i, n: dict(st=L.State(**S0), cam=R.cam_lerp(cam_a, cam_b, t), hide=wide, focus=mod, labels=lab if t > 0.5 else (),
                                     text="Sam's Oct 13 plate carried the auger only from the outlet to the gear. v6 keeps his front (knuckles, "
                                          "clip 1, gear housing) and carries the plate on to the cap's end: a second C-clip halfway between the gear "
                                          "and the cap, a saddle under the cap, and the latch's keeper on the back end.", save_as="p1" if preview else None))
    c.hold(2.5)
    c.chapter(2, "2. The auger still pulls straight off")
    lab2 = [("Clips open outward: the tube\nsnaps in and pulls out", sam(k, (156.0, 0.0, 8.0)), "R")]
    c.move(3.0, lambda t, i, n: dict(st=L.State(out_auger=k, auger_out=70.0 * math.sin(math.pi * t), hatch_side=110.0, **S0), cam=cam_b, hide=wide,
                                     focus=mod, labels=lab2, readout=lambda st: f"auger {st.auger_out:4.1f} mm off",
                                     text="Both clips are C-shapes open away from the plate, so at the side hatch the auger comes straight out of "
                                          "them and a full one snaps back in. The plate, its door and its carriage stay on the chain.",
                                     save_as="p2" if preview else None), eased=False)
    c.chapter(3, "3. The dock's plate half is printed")
    cam_c = (tuple(L.to_world(L.sam_frame(L.station_frame(), 0.0), (54.0, 0.0, -12.0))), (-0.35, -0.55, -1.0), 230)
    lab3 = [("Dome A (printed):\nsits in the EC's cone", sam(0, (KC4_A[0], KC4_A[1], -9.3)), "L"),
            ("Dome B (printed):\nsits in the EC's vee", sam(0, (KC4_B[0], KC4_B[1], -9.3)), "R"),
            ("Flat C: the plate's own face\n(no washer)", sam(0, (KC4_C[0], KC4_C[1], -13.0)), "L"),
            ("Magnet pressed in under each,\nfor the EC's magnets", part("kc6_magnet", module=0, nth=0, local=(0, 0, 1.6)), "R")]
    c.move(3.0, lambda t, i, n: dict(st=L.State(ext=0.0, **S0), cam=cam_c, hide=lambda p: not ((p.module == 0 and p.group in ("modules", "carriages"))
                                                                                                 and p.key not in ("auger", "auger_cap")),
                                     focus=lambda p: p.module == 0 and p.key in ("sam_mounting_plate", "kc6_magnet"), labels=lab3,
                                     opacity=lambda pl: {kk: 0.55 for kk, p in R.keyed(pl) if p.key == "sam_mounting_plate" and p.module == 0},
                                     text="v5 pressed two 1/4 in steel balls into the plate and bonded a washer in for the third contact. v6 prints "
                                          "them: two domes the shape of the balls' exposed caps (the EC's cone and vee are unchanged) and the plate's "
                                          "own face at C. A small N52 magnet pressed into the underside under each gives the EC's magnets something "
                                          "to pull on.", save_as="p3" if preview else None))
    c.hold(2.0)
    c.done()


# ---------------------------------------------------------------- 2. the latch at the back, and the rest
def latch(preview=False):
    c = E.Clip("latch_v6", TAG, 2, preview)
    S = L.sam_frame(L.station_frame(), 0.0)
    cen = L.to_world(S, (258.0, LATCH_Y6, -2.0))
    cam = (tuple(cen), (-0.55, -0.75, -0.55), 230)
    foc = lambda p: p.key in ("latch_bolt", "latch_follower", "latch_spring", "latch_rail") or (p.module == 0 and p.key in ("sam_mounting_plate", "carriage"))  # noqa: E731
    hide = lambda p: wide(p) or p.group == "scale" or (p.module not in (-1, 0) and p.group in ("modules", "carriages")) or p.key in ("auger", "auger_cap") \
        or p.group in ("station_lift", "station_act", "station_tilt", "station_ec") or p.key in ("side_plate_back", "nema34") or p.group == "drive"  # noqa: E731
    lab = [("Keeper on the plate's back end", sam(0, (248.0, LATCH_Y6, -9.0)), "L"),
           ("4 mm latch pin", part("latch_bolt", module=0, local=(252.0, LATCH_Y6, -13.5)), "L"),
           ("Rest shelf over the keeper", part("latch_bolt", module=0, local=(247.0, LATCH_Y6, -6.0)), "R"),
           ("Follower on the station's cam", part("latch_follower", module=0, local=(0.0, 0.0, 8.0)), "R"),
           ("Station cam, on an arm from\nthe back side plate", part("latch_rail", local=(259.0, LATCH_Y6 + 8.0, 5.0)), "R")]

    def ro(st):
        lo = max(L.latch_open(0, st), st.latch_manual)
        pin = max(0.0, 4.0 - lo)
        shelf = max(0.0, SHELF6[0] - lo)
        return f"bolt back {lo:4.1f} mm\npin in the keeper {pin:3.1f} mm\nshelf over the keeper {shelf:3.1f} mm"
    c.chapter(1, "1. The latch is now at the back, and the module rests on its carriage")
    c.move(4.5, lambda t, i, n: dict(st=L.State(shift=-RUN_DIRECTION * 2.2 * (1 - t), ext=0.0, **S0), cam=cam, hide=hide, focus=foc, labels=lab,
                                     readout=ro, text="One spring bolt behind the plate's back end carries the 4 mm pin and a rest shelf. Arriving at "
                                                      "the station, the cam draws it back 4.5 mm: the pin leaves the keeper, but the shelf is still 3.5 mm "
                                                      "under it, so the module rests on its own carriage (v5 put it on a rest on the station).",
                                     save_as="l1" if preview else None), eased=False)
    c.hold(2.0)
    c.chapter(2, "2. To take a module off: push the bolt back 10 mm")
    c.move(3.0, lambda t, i, n: dict(st=L.State(ext=0.0, latch_manual=LATCH_TRAVEL + (LATCH6_MANUAL - LATCH_TRAVEL) * math.sin(math.pi * t), **S0), cam=cam,
                                     hide=hide, focus=foc, labels=lab, readout=ro,
                                     text="At the back of the carriage, where it's easy to reach: push the bolt back 10 mm by hand and both the pin "
                                          "and the shelf clear the keeper; the module then swings off its hinge pins.", save_as="l2" if preview else None),
           eased=False)
    c.hold(1.5)
    c.done()


# ---------------------------------------------------------------- 3. the ladder
def ladder(preview=False):
    c = E.Clip("ladder_v6", TAG, 4, preview)
    cam0 = ((150, 0, 330), (-1.0, -1.25, 0.55), 1450)
    cam1 = ((150, 0, 330), (-1.25, 0.7, 0.45), 1450)
    base = lambda p: p.group in ("frame", "plates", "bearings", "shafts", "sprockets") and p.key not in ("rung",)    # noqa: E731
    frame_only = lambda p: p.group in ("frame", "plates", "bearings", "shafts", "sprockets")                           # noqa: E731
    stn = lambda p: p.group in ("station", "station_lift", "station_act", "station_tilt", "station_ec")               # noqa: E731
    lab = [("Rungs between the front and\nback posts (lower: P16 shelves)", part("rung", name="lower +y", local=(0, 0, 200.0)), "R"),
           ("Upper rungs: the guides", part("rung", name="upper -y", local=(0, 0, 200.0)), "L"),
           ("Nothing on the base rails\nbut the corner posts", world((150.0, -180.0, 25.0)), "L")]
    lab2 = lab + [("Lift P16-50 on its shelf", part("p16l_body", name="+y"), "R"), ("Guide on the upper rung", part("guide_cone"), "L"),
                  ("Tilt P16 and the latch cam:\non the back side plate", part("tilt_bracket"), "R")]
    ghosts = []
    for sy in (-1, 1):
        ghosts.append(L.Placement("ext_station_post", "v5 station post", L.T(None, (L.STATION_RAIL_X, sy * L.POST_Y, L.Z_BASE + L.EXT)), 1, (0.9, 0.1, 0.1), "ghost"))
    ghosts.append(L.Placement("ext_latch_post5", "v5 latch post", L.T(None, (L.LATCH_RAIL_X, -L.POST_Y, L.Z_BASE + L.EXT)), 1, (0.9, 0.1, 0.1), "ghost"))
    ghosts.append(L.Placement("ext_latch_beam", "v5 latch beam", L.T(L.Rx(-math.pi / 2), (L.LATCH_RAIL_X, -L.POST_Y + L.EXT / 2, L.LATCH_BEAM_ZC)), 1,
                              (0.9, 0.1, 0.1), "ghost"))
    red = lambda p: (0.90, 0.12, 0.10) if p.group == "ghost" else None                  # noqa: E731
    orange = lambda p: (0.95, 0.45, 0.10) if p.key == "rung" else None                  # noqa: E731
    lab0 = [("v5: two station posts and a latch\npost stood on the base rails", world((L.STATION_RAIL_X, 180.0, 200.0)), "R")]
    steps = [("1. v5: posts stood on the base rails", lambda p: not (base(p) or p.group == "ghost"), red, lab0, True,
              "v5 carried its station on two 2020 posts and a latch post (red) standing on the side base rails, inside the frame round the balance."),
             ("2. v6: rungs between the posts, like a ladder", lambda p: not frame_only(p), orange, lab, False,
              "v6 has nothing standing on the base rails but the four corner posts. On each side two 2020 rungs (orange) run between the front and "
              "back posts, each end on a corner bracket."),
             ("3. The station hangs on the rungs", lambda p: not (frame_only(p) or stn(p)), orange, lab2, False,
              "The lift P16s' shelves bolt onto the lower rungs and the guides onto the upper ones; the tilt P16 and the latch cam hang on the "
              "back side plate (four new holes in it). The base is clear for the balance."),
             ("4. With the modules and the balance", lambda p: wide(p), orange, (), False,
              "The same frame with the chains, the 13 modules and the balance.")]
    for i, (title, hide, acc, labs, gh, text) in enumerate(steps):
        c.chapter(i + 1, title)
        c.move(3.0, lambda t, ii, n, hide=hide, acc=acc, text=text, i=i, labs=labs, gh=gh: dict(
            st=L.State(ext=0.0, enclosure=False, scale=i == 3, extra=list(ghosts) if gh else []), cam=R.cam_lerp(cam0, cam1, (i + t) / 4.0),
            hide=hide, accent=acc, labels=labs, text=text, save_as=f"g{i}" if preview else None), eased=False)
        c.hold(1.0)
    c.done()


# ---------------------------------------------------------------- 4. 90 degrees
def tilt90(preview=False):
    c = E.Clip("tilt90_v6", TAG, 3, preview)
    cam = ((H[0] + 95, H[1], H[2] + 25), (0.0, -1.0, 0.06), 780)
    foc = lambda p: p.group in ("station_ec", "station_tilt", "station_lift") or p.key in ("tilt_bracket",) or (p.module == 0)   # noqa: E731
    lab = [("Tilt P16-150 on the\nback side plate", part("actuator_body", local=(0, 0, 60.0)), "R"),
           ("EC's tilt arm and pin", part("sam_electronics_carriage", local=(-20.0, 26.5, 44.0)), "L"),
           ("Lift frame: two bars, it\nstays at the dock height", part("lift_bar", nth=0, local=(0.0, -40.0, 0.0)), "L"),
           ("Hooks: the EC leaves the\nbars only by turning", part("sam_electronics_carriage", local=(60.0, 0.0, 80.0)), "R")]

    def ro(st):
        return f"tilt {st.tilt:4.1f} deg\ntilt P16 {tilt_len(st) - ACT_RETRACTED:5.1f} of 150 mm out"
    c.chapter(1, "1. The lift P16s dock the EC (28 mm)")
    c.move(3.0, lambda t, i, n: dict(st=L.State(ext=PARK_DROP * t, top_door=205.0, **S0), cam=cam, hide=near_cut, focus=foc, labels=lab,
                                     readout=lambda st: f"rise {st.ext:4.1f} of {PARK_DROP:.0f} mm",
                                     text="The two P16-50s lift the frame and the EC hanging on it until the EC seats on the plate's dock; the "
                                          "tilt P16 just follows. The frame then stays at this height.", save_as="t1" if preview else None))
    c.chapter(2, "2. A third P16 swings the module to 90 deg")
    c.move(6.0, lambda t, i, n: dict(st=L.State(tilt=90.0 * t, top_door=205.0, **S0), cam=cam, hide=near_cut, focus=foc, labels=lab, readout=ro,
                                     text="Retracting, the tilt P16 pulls the EC's tilt pin round under the hinge axis: the docked EC and module "
                                          "turn 0-90 deg, out of the hooks. The pin stays 42-60 mm under the axis, so nothing wide rises toward the "
                                          "neighbouring modules (v5's lift bar did, which stopped it at 40 deg).", save_as="t2" if preview else None))
    c.hold(2.0)
    c.chapter(3, "3. Back to 0, into the hooks, and down")
    c.move(4.0, lambda t, i, n: dict(st=L.State(tilt=90.0 * (1 - t), top_door=205.0, **S0), cam=cam, hide=near_cut, focus=foc, labels=(), readout=ro,
                                     text="Extending brings it back; the EC's hooks close round the bars again and the lift P16s lower it.",
                                     save_as="t3" if preview else None))
    c.move(2.0, lambda t, i, n: dict(st=L.State(ext=PARK_DROP * (1 - t), top_door=205.0, **S0), cam=cam, hide=near_cut, focus=foc,
                                     readout=lambda st: f"rise {st.ext:4.1f} of {PARK_DROP:.0f} mm", text="", save_as="t4" if preview else None))
    c.hold(1.0)
    c.done()


# ---------------------------------------------------------------- 5. the guides' funnels and seats
def guides(preview=False):
    c = E.Clip("guides_v6", TAG, 2, preview)
    foc = lambda p: p.key in ("guide_cone", "guide_vee", "lift_end", "lift_bar", "rung", "p16l_rod", "p16l_body", "clevis_screw", "nut_m3_clevis")  # noqa: E731
    hide = lambda p: wide(p) or p.group in ("modules", "carriages", "chain", "scale", "station_tilt", "drive") or p.key in (  # noqa: E731
        "side_plate_front", "side_plate_back", "sam_electronics_carriage", "nema11", "pinion", "solenoid", "kc_ball", "vee_dowel", "kc_magnet",
        "tilt_bracket", "nema34", "latch_rail", "hold_down", "hall_switch", "clevis_screw", "nut_m3_clevis") and not (
        p.key in ("clevis_screw", "nut_m3_clevis") and abs(p.M[1, 3]) > 100)
    z_g = L.GUIDE_TOP_Z

    def st_at(t, side):
        e = PARK_DROP * (1 - t)
        zs = L.BAR_PARK_Z + e - SHOE[2] / 2                 # the shoe's bottom
        f = min(1.0, max(0.0, (zs - (z_g - 4.0)) / 6.0))     # off-line until the funnel has it
        return L.State(ext=e, lift_dx=2.5 * f, **S0)
    for i, (side, nm, seat) in enumerate(((-1, "-y", "cone"), (1, "+y", "vee"))):
        cen = (HINGE_X + 35.0, side * 160.0, 330.0)
        cam = (cen, (0.55, -side * 1.0, 0.35), 240)
        lab = [(f"Guide {nm} on the upper rung", part(f"guide_{seat}", local=(0.0, 4.0, 345.0)), "L"),
               ("Funnel mouth: 4 mm\neach side, 45 deg", part(f"guide_{seat}", local=(0.0, 10.0, z_g)), "R"),
               ("Shoe with a conical nose", part("lift_end", name=nm, local=(0.0, 13.1, -12.0)), "R"),
               (f"{seat.capitalize()} seat in the floor", part(f"guide_{seat}", local=(0.0, 10.9, L.GUIDE6_SEAT_Z - 2.0)), "L")]
        c.chapter(i + 1, f"{i + 1}. Guide {nm}: funnel in, {seat} seat at the bottom")
        c.move(4.5, lambda t, ii, n, side=side, lab=lab, cam=cam, seat=seat: dict(
            st=st_at(t, side), cam=cam, hide=hide, focus=foc, labels=lab,
            readout=lambda st: f"lift frame {st.lift_dx:3.1f} mm off line\nshoe {L.BAR_PARK_Z + st.ext - SHOE[2] / 2 - L.GUIDE6_SEAT_Z:4.1f} mm over the seat",
            text=(f"Coming down 2.5 mm off line, each shoe meets its guide's funnel mouth, which centres it in the slot. At the bottom its 90 deg "
                  f"nose sits in a {seat}: the cone (-y) fixes that end, the vee (+y, along y) only its x, so the two P16s park the frame, and "
                  f"the EC on it, in the same place every time."), save_as=f"u{i}" if preview else None), eased=False)
        c.hold(1.5)
    c.done()


# ---------------------------------------------------------------- 6. overview
def overview(preview=False):
    c = E.Clip("overview_v6", TAG, 4, preview)
    camA = ((120, 0, 470), (-1.0, -1.05, 0.5), 1750)
    camB = ((120, 0, 470), (-1.1, 0.9, 0.42), 1750)
    camS = ((H[0] + 95, H[1], H[2] - 10), (-0.55, -1.0, 0.1), 900)
    lab = [("13 modules on two #35 chains", sam(6, (150, 0, 0)), "R"),
           ("Station: lift frame, EC,\ntilt P16", part("sam_electronics_carriage"), "L"),
           ("A&D HR-202i", part("hr202i_body", local=(100, 0, 200)), "L"),
           ("Ladder rungs", part("rung", name="upper +y", local=(0, 0, 250.0)), "R")]
    c.chapter(1, "Chain carousel v6")
    c.move(4.0, lambda t, i, n: dict(st=L.State(ext=0.0, **S0), cam=R.cam_lerp(camA, camB, t), hide=wide, labels=lab if t > 0.3 else (),
                                     text="Sam's Nov 10 changes: a longer mounting plate with a second clip and printed dock features; the latch at "
                                          "the plate's back end with a rest shelf; ladder rungs instead of posts on the base rails; a separate tilt "
                                          "actuator so the module reaches 90 deg; funnels and seats on the lift guides.", save_as="o1" if preview else None))
    c.chapter(2, "Index one module")
    c.move(3.0, lambda t, i, n: dict(st=L.State(shift=-RUN_DIRECTION * MODULE_LINKS * (1 - t), ext=0.0, **S0), cam=R.cam_lerp(camB, camS, t), hide=wide,
                                     readout=lambda st: f"chain {abs(st.shift) * 9.525:4.1f} mm to go", text="The NEMA 34 moves both chains 8 links.",
                                     save_as="o2" if preview else None))
    c.chapter(3, "Dock, tilt to 30 deg, dose")
    c.move(2.0, lambda t, i, n: dict(st=L.State(ext=PARK_DROP * t, top_door=205.0, **S0), cam=camS, hide=near_cut,
                                     readout=lambda st: f"rise {st.ext:4.1f} mm", text="The lift P16s dock the EC.", save_as="o3" if preview else None))
    c.move(2.5, lambda t, i, n: dict(st=L.State(tilt=30.0 * t, top_door=205.0, **S0), cam=camS, hide=near_cut,
                                     readout=lambda st: f"tilt {st.tilt:4.1f} deg", text="The tilt P16 turns the module to 30 deg.", save_as="o4" if preview else None))
    c.move(2.5, lambda t, i, n: dict(st=L.State(tilt=30.0, spin=2 * math.pi * 2 * t, top_door=205.0, **S0), cam=camS, hide=near_cut,
                                     readout=lambda st: f"auger {st.spin / (2 * math.pi):3.1f} turns", text="The NEMA 11 turns the auger; the dose falls into the beaker.",
                                     save_as="o5" if preview else None), eased=False)
    c.chapter(4, "...and on to 90 deg, then back and down")
    c.move(3.0, lambda t, i, n: dict(st=L.State(tilt=30.0 + 60.0 * t, top_door=205.0, **S0), cam=camS, hide=near_cut,
                                     readout=lambda st: f"tilt {st.tilt:4.1f} deg", text="The full range is 0-90 deg.", save_as="o6" if preview else None))
    c.move(3.0, lambda t, i, n: dict(st=L.State(tilt=90.0 * (1 - t), top_door=205.0, **S0), cam=camS, hide=near_cut,
                                     readout=lambda st: f"tilt {st.tilt:4.1f} deg", text="", save_as="o7" if preview else None))
    c.move(1.5, lambda t, i, n: dict(st=L.State(ext=PARK_DROP * (1 - t), **S0), cam=camS, hide=near_cut, text="", save_as="o8" if preview else None))
    c.hold(1.0)
    c.done()


CLIPS = {"plate": plate, "latch": latch, "ladder": ladder, "tilt90": tilt90, "guides": guides, "overview": overview}

if __name__ == "__main__":
    pv = "--preview" in sys.argv
    for a in sys.argv[1:]:
        if a in CLIPS:
            CLIPS[a](pv)
