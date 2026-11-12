"""v8's clips (Sam, PR #185, 2026-11-12: "As usual, include gifs of changes and a link to v8"). One clip per change and an
overview; every frame is the v8 CAD (layout.placements) in the state described, moving by the model's own kinematics
(explain.py's Clip: the parts a step is about keep their colours, the rest is washed out, callouts name the parts).

    xvfb-run -a python explain8.py overview|drop|ec|door|balance|tilt90|frame [--preview]
    -> renders/v8/<name>_v8.{mp4,gif}
"""
from __future__ import annotations

import math
import sys

import explain as E
import explain7 as X7
import layout as L
import render as R
import render_balance as RB
from params import (BEAKER_H, BEAKER_RIM_Z, BAL8_DOOR_OPEN, DOOR_TRAVEL, EC8_PIN, EC8_SHOE_X, H8, KC8_A, KC8_B, KC8_C, KC7_TIP, MODULE_LINKS,
                    MOTOR8_FACE_X, MOTOR8_Z, PAN8_AHEAD, PARK_DROP8, RUN_DIRECTION, SOL8_X, SOL8_TOP, MOTOR8_Y, Z_MOTOR)

E.OUT = R.OUT / "v8"
H = L.HINGE_STATION
D = L.DOSE_POINT
SY = L.STATION_Y
part, sam, ec, world = E.part, E.sam, E.ec, E.world
near_cut, opac, wide = X7.near_cut, X7.opac, X7.wide
TAG = "chain carousel v8 · PR #185 · 2026-11-12"
S0 = dict(enclosure=False)
FPS = E.FPS
Z_LAND = BEAKER_RIM_Z - BEAKER_H + 6.0
CAM_SIDE = ((112.0, SY, 238.0), (0.0, -1.0, 0.06), 610)          # the station, side section from -y
CAM_SIDE90 = ((118.0, SY, 330.0), (0.0, -1.0, 0.05), 860)         # ... with room for the module at 90 deg


def ext_ro(st: L.State) -> str:
    return f"P16 {L.p16_8_ext(st.tilt, st.ext):5.1f} of 150 mm out"


def tilt_ro(st: L.State) -> str:
    return f"tilt {st.tilt:4.1f} deg\n" + ext_ro(st)


def rise_ro(st: L.State) -> str:
    return f"EC rise {st.ext:4.1f} of {PARK_DROP8:.0f} mm\n" + ext_ro(st)


def door_ro(st: L.State) -> str:
    return rise_ro(st) + f"\ndoor {L.door_open(st):3.1f} of {DOOR_TRAVEL:.0f} mm open"


def _dose(c: E.Clip, secs: float, foc=None, text: str = "", cam=CAM_SIDE, save=None) -> None:
    g = {"g": None}

    def fr(t, i, n):
        if g["g"] is None:
            g["g"] = RB.Grains(c.v)
        tt = i / FPS
        return dict(st=L.State(tilt=30.0, spin=2 * math.pi * 1.5 * t, **S0), cam=cam, hide=near_cut, focus=foc, opacity=opac,
                    before=lambda v, s: g["g"].set(tt, True, Z_LAND), readout=lambda st: f"tilt 30.0 deg\nauger {st.spin / (2 * math.pi):3.1f} turns",
                    text=text, save_as=save)
    c.move(secs, fr, eased=False)
    if g["g"] is not None:
        g["g"].set(0.0, False, Z_LAND)


# ---------------------------------------------------------------- 1. overview
def overview(preview=False):
    c = E.Clip("overview_v8", TAG, 3, preview)
    camA = ((110, 0, 330), (-0.45, -1.0, 0.35), 1600)
    camB = ((110, 0, 330), (-1.0, -0.62, 0.3), 1600)
    lab = [("EC v8 (Sam's Aug 27 layout)\nbehind the balance", part("sam_electronics_carriage", local=(110.0, 0.0, 50.0)), "R"),
           ("Exit 50 mm over the\nbeaker's rim (v7: 154)", world((D[0], D[1], D[2] - 6.0)), "L"),
           ("Front panel notched round\nthe balance, brush strips", part("brush_strip_h", local=(4.0, 120.0, 6.0)), "L"),
           ("Carousel 104 mm lower", part("sprocket_32", name="T+ front"), "R")]
    c.chapter(1, "Chain carousel v8")
    c.move(4.0, lambda t, i, n: dict(st=L.State(ext=0.0), cam=R.cam_lerp(camA, camB, t), hide=lambda p: p.group == "elec", labels=lab if t > 0.2 else (),
                                     opacity=lambda pl: opac(pl, {k: 0.2 for k in ("panel_front_hatch",)}),
                                     text="v8 (Sam, Nov 12): a new EC on his Aug 27 layout, behind the balance; the dock, the guides and the P16's pin "
                                          "moved with it; the stream falls near the back of the draft cage, so the carousel comes down 104 mm and the "
                                          "exit sits 50 mm over the beaker's rim.", save_as="o1" if preview else None))
    c.chapter(2, "Index, dock, tilt to 30 deg and dose")
    c.move(1.5, lambda t, i, n: dict(st=L.State(shift=-RUN_DIRECTION * MODULE_LINKS * (1 - t), ext=0.0, **S0), cam=R.cam_lerp(camB, CAM_SIDE, t),
                                     hide=lambda p: wide(p) if t < 0.6 else near_cut(p), opacity=opac,
                                     readout=lambda st: f"chain {abs(st.shift) * 9.525:4.1f} mm to go", text="The NEMA 34 moves both chains 8 links.",
                                     save_as="o2" if preview else None))
    c.move(1.2, lambda t, i, n: dict(st=L.State(ext=PARK_DROP8 * t, **S0), cam=CAM_SIDE, hide=near_cut, opacity=opac, readout=rise_ro,
                                     text="The P16 lifts the EC 10 mm onto the dock behind the gear; the EC's finger opens the outlet door.",
                                     save_as="o3" if preview else None))
    c.move(1.2, lambda t, i, n: dict(st=L.State(tilt=30.0 * t, **S0), cam=CAM_SIDE, hide=near_cut, opacity=opac, readout=tilt_ro,
                                     text="The same P16 turns the docked EC and module about the hinge.", save_as="o4" if preview else None))
    _dose(c, 1.5, text="The NEMA 11 turns the auger; the dose falls 50 mm through the hole in the balance's lid into the beaker.",
          save="o5" if preview else None)
    c.chapter(3, "...on to 90 deg, back, and down")
    c.move(1.8, lambda t, i, n: dict(st=L.State(tilt=30.0 + 60.0 * t, **S0), cam=CAM_SIDE90, hide=near_cut, opacity=opac, readout=tilt_ro,
                                     text="0-90 deg uses 126 of the P16's 150 mm. The EC never swings over the balance.", save_as="o6" if preview else None))
    c.move(1.8, lambda t, i, n: dict(st=L.State(tilt=90.0 * (1 - t), **S0), cam=CAM_SIDE90, hide=near_cut, opacity=opac, readout=tilt_ro, text="",
                                     save_as="o7" if preview else None))
    c.move(0.8, lambda t, i, n: dict(st=L.State(ext=PARK_DROP8 * (1 - t), **S0), cam=CAM_SIDE90, hide=near_cut, opacity=opac, readout=rise_ro,
                                     text="", save_as="o8" if preview else None))
    c.hold(1.0)
    c.done()


# ---------------------------------------------------------------- 2. the drop: the exit 50 mm over the beaker
def drop(preview=False):
    c = E.Clip("drop_v8", TAG, 2, preview)
    foc = lambda p: p.group == "scale" or p.module == 0 or p.group == "station_ec"            # noqa: E731
    cam = ((72.0, SY, 268.0), (0.0, -1.0, 0.05), 430)
    lab = [("Exit: 332 mm up\n(v7: 436)", world((D[0], D[1], D[2])), "L"),
           ("Beaker rim: 282 mm\n(50 mm under the exit)", world((D[0], D[1], BEAKER_RIM_Z)), "L"),
           ("Lid's hole (30 mm),\nunder the exit", world((D[0] + 15.0, D[1], 303.0)), "R"),
           ("The cage ends 3 mm in\nfront of the EC", part("bal7_frame", local=(88.0, 0.0, 311.0)), "R"),
           ("Pan's centre 38 mm in front\nof the exit; offset riser", part("beaker_riser", local=(0.0, 0.0, 150.0)), "L"),
           ("EC v8: all of it behind\nthe balance", part("sam_electronics_carriage", local=(100.0, 0.0, 45.0)), "R")]
    c.chapter(1, "1. The stream falls at the back of the draft cage")
    c.move(4.5, lambda t, i, n: dict(st=L.State(ext=0.0, **S0), cam=cam, hide=near_cut, focus=foc, opacity=opac, labels=lab if t > 0.15 else (),
                                     text="The gear is 78-88 mm behind the exit and the cage's back 89 mm behind the pan's centre: with the pan under "
                                          "the exit, the EC's pinion and solenoid would hang over the cage. With the pan 38 mm forward and an offset "
                                          "riser, the EC clears the cage and the exit sits 50 mm over the rim (v7: 154; single doser: about 85).",
                                     save_as="d1" if preview else None))
    c.chapter(2, "2. Dock, tilt and dose")
    c.move(1.2, lambda t, i, n: dict(st=L.State(ext=PARK_DROP8 * t, **S0), cam=cam, hide=near_cut, focus=foc, opacity=opac, readout=rise_ro,
                                     text="", save_as="d2" if preview else None))
    c.move(1.2, lambda t, i, n: dict(st=L.State(tilt=30.0 * t, **S0), cam=cam, hide=near_cut, focus=foc, opacity=opac, readout=tilt_ro,
                                     text="The exit is on the hinge axis, so the stream falls from the same point at every tilt.", save_as="d3" if preview else None))
    _dose(c, 2.0, foc=foc, cam=cam, text="50 mm from the exit to the rim, 98 mm to the beaker's floor (v7: 154 and 201).", save="d4" if preview else None)
    c.hold(1.0)
    c.done()


# ---------------------------------------------------------------- 3. EC v8
def ec_clip(preview=False):
    c = E.Clip("ec_v8", TAG, 2, preview)
    cen = (H[0] + 100.0, SY, H[2] - 32.0)
    cam_a = (cen, (-0.45, -1.0, -0.55), 300)
    cam_b = (cen, (0.05, -1.0, -0.12), 300)
    foc = lambda p: p.group == "station_ec" or (p.module == 0 and p.key in ("sam_mounting_plate", "kc6_magnet", "door_shutter", "auger"))  # noqa: E731
    hide = lambda p: near_cut(p) or p.group in ("scale", "station_act") or p.key in ("guide7_vee", "guide7_cone", "nema34")   # noqa: E731
    lab = [("Solenoid, just in front of the gear,\nplunger up; faces the front", ec((SOL8_X - 7.0, 0.0, SOL8_TOP + 14.0)), "L"),
           ("20T pinion under the 44T gear", ec((83.3, 0.0, MOTOR8_Z + 11.0)), "L"),
           ("NEMA 11 behind the gear,\nshaft forward (v7: in front)", ec((MOTOR8_FACE_X + 25.0, -14.0, MOTOR8_Z)), "R"),
           ("Cone (A) / vee (B) beside\nthe motor, magnets behind", ec((KC8_A[0], KC8_A[1], 20.0)), "R"),
           ("Ball C", ec((KC8_C[0], KC8_C[1], 20.0)), "R"),
           ("P16's pin under the\nsolenoid's cradle", ec((EC8_PIN[0], 0.0, EC8_PIN[1])), "L"),
           ("Guide shoes", ec(((EC8_SHOE_X[0] + EC8_SHOE_X[1]) / 2, -18.5, 62.0)), "R")]
    c.chapter(1, "1. EC v8: Sam's Aug 27 layout, a flat base")
    c.move(4.5, lambda t, i, n: dict(st=L.State(ext=0.0, **S0), cam=R.cam_lerp(cam_a, cam_b, t), hide=hide, focus=foc, labels=lab if t > 0.2 else (),
                                     readout=rise_ro,
                                     text="Like Sam's first EC: the parts stand on a flat base. The solenoid sits in a cradle just in front of the gear, "
                                          "screwed through the cradle's front wall (it faces the front); the NEMA 11 is now behind the gear with its "
                                          "shaft forward. The dock's cone, vee and ball C sit on ears beside the motor; the shoes at the back.",
                                     save_as="e1" if preview else None))
    c.hold(0.8)
    c.chapter(2, "2. 10 mm up onto the dock, behind the gear")
    lab2 = [("Posts A and B (printed domes),\nnow behind the gear", sam(0, (KC8_A[0], KC8_A[1], KC7_TIP)), "R"),
            ("Post C's flat", sam(0, (KC8_C[0], KC8_C[1], KC7_TIP)), "R")]
    c.move(3.5, lambda t, i, n: dict(st=L.State(ext=PARK_DROP8 * t, **S0), cam=cam_b, hide=hide, focus=foc, labels=lab2, readout=door_ro,
                                     text="The P16 lifts the EC 10 mm: the posts' domes drop into the cone and the vee, ball C lands on post C. "
                                          "Parked, the pinion clears the passing gears by 8 mm.", save_as="e2" if preview else None))
    c.hold(1.0)
    c.done()


# ---------------------------------------------------------------- 4. the door's push bar
def door(preview=False):
    c = E.Clip("door_v8", TAG, 2, preview)
    cen = (H[0] + 30.0, SY, H[2] - 14.0)
    cam_a = (cen, (-0.55, -1.0, -0.65), 210)
    cam_b = (cen, (-0.15, -1.0, -0.25), 190)
    foc = lambda p: p.key in ("door_shutter", "door_housing", "sam_electronics_carriage") and (p.module in (0, -1))   # noqa: E731
    hide = lambda p: near_cut(p) or p.group in ("scale", "station_act") or p.key in ("guide7_vee", "guide7_cone", "nema34", "carriage")  # noqa: E731
    lab = [("Shutter over the 3 mm exit", sam(0, (-0.6, 2.0, 0.0)), "L"),
           ("NEW: its push strip runs on\nback beside the tube as a bar", sam(0, (30.0, 19.5, 9.0)), "R"),
           ("Guide lug on the plate", sam(0, (49.0, 19.5, 4.0)), "R"),
           ("The EC's finger, behind\nthe balance (x 54-58)", ec((56.0, 19.5, 12.0)), "R")]
    c.chapter(1, "1. The outlet door is pushed open from behind the balance")
    c.move(3.0, lambda t, i, n: dict(st=L.State(ext=0.0, **S0), cam=R.cam_lerp(cam_a, cam_b, t), hide=hide, focus=foc, labels=lab if t > 0.2 else (),
                                     readout=door_ro, opacity=lambda pl: {k: 0.35 for k, p in R.keyed(pl) if p.module == 0 and p.key in ("sam_mounting_plate", "auger")},
                                     text="v7's EC reached the door at the outlet; v8's starts 54 mm behind it. So the shutter's push strip carries on "
                                          "back beside the tube as a 3 x 2 mm bar (printed with the shutter), through a guide lug, to where the EC's "
                                          "finger meets it.", save_as="r1" if preview else None))
    c.chapter(2, "2. Docking lifts the bar 6 mm: the door opens")
    c.move(3.5, lambda t, i, n: dict(st=L.State(ext=PARK_DROP8 * t, **S0), cam=cam_b, hide=hide, focus=foc, labels=lab, readout=door_ro,
                                     opacity=lambda pl: {k: 0.35 for k, p in R.keyed(pl) if p.module == 0 and p.key in ("sam_mounting_plate", "auger")},
                                     text="In the dock's last 6 mm the finger lifts the bar and the shutter clears the exit; undocking, the spring shuts "
                                          "it. Where the bar crosses the draft cage's back frame it runs high (10 mm under the axis).",
                                     save_as="r2" if preview else None))
    c.hold(1.0)
    c.done()


# ---------------------------------------------------------------- 5. the balance, the offset riser and the beaker
def balance(preview=False):
    c = E.Clip("balance_v8", TAG, 3, preview)
    foc = lambda p: p.group == "scale"                                                        # noqa: E731
    cam = ((D[0] - 40.0, SY, 200.0), (-0.75, -1.0, 0.35), 520)
    lab = [("Pan's centre: 38 mm in\nfront of the exit", part("bal7_pan", local=(0.0, 0.0, 50.0)), "L"),
           ("Riser v8: its cup 38 mm\nback, under the exit", part("beaker_riser", local=(30.0, 0.0, 180.0)), "R"),
           ("Lid's hole under the exit\n(no collar)", world((D[0], D[1], 303.0)), "R"),
           ("Side door: 85 mm of\ntravel (NEMA 34 behind)", part("bal7_door_left", local=(-40.0, -100.0, 200.0)), "L")]
    c.chapter(1, "1. The balance under v8's station")
    c.move(3.0, lambda t, i, n: dict(st=L.State(ext=0.0, **S0), cam=cam, hide=lambda p: wide(p) or p.key == "guide7_cone", focus=foc, opacity=opac,
                                     labels=lab if t > 0.2 else (),
                                     text="v7's balance (a base and a draft cage) placed with its pan 38 mm in front of the exit: the beaker sits on "
                                          "an offset cup over the back of the pan. Tared with the riser, the offset only scales a dose by the "
                                          "balance's corner-load error.", save_as="b1" if preview else None))
    c.chapter(2, "2. The beaker comes out through a side door")

    def out(t, i, n):
        door = BAL8_DOOR_OPEN * min(1.0, t / 0.3)
        dz = 6.0 * min(1.0, max(0.0, (t - 0.3) / 0.1))
        dx = -66.0 * min(1.0, max(0.0, (t - 0.4) / 0.3))
        dy = -170.0 * min(1.0, max(0.0, (t - 0.7) / 0.3))
        return dict(st=L.State(ext=0.0, side_door=door, beaker_dx=dx, beaker_dy=dy, beaker_dz=dz, **S0), cam=cam,
                    hide=lambda p: wide(p) or p.key == "guide7_cone", focus=foc, opacity=opac, readout=lambda st: f"side door {st.side_door:4.1f} of {BAL8_DOOR_OPEN:.0f} mm",
                    text="Slide the -y door back 85 mm, lift the beaker out of its cup, bring it forward 66 mm and out.", save_as="b2" if preview else None)
    c.move(5.0, out, eased=False)
    c.chapter(3, "3. Dosing")
    _dose(c, 2.0, foc=foc, cam=cam, text="The dose falls 50 mm from the exit to the rim, through the lid's hole.", save="b3" if preview else None)
    c.hold(0.8)
    c.done()


# ---------------------------------------------------------------- 6. 90 degrees
def tilt90(preview=False):
    c = E.Clip("tilt90_v8", TAG, 2, preview)
    foc = lambda p: p.group in ("station_act", "station_ec") or p.key in ("clevis_bracket",) or p.module == 0 or p.key == "carriage"  # noqa: E731
    lab = [("P16: 126 of 150 mm\nout at 90 deg", part("actuator_rod", local=(0, 0, 150.0)), "R"),
           ("The EC turns back and up,\nnever over the balance", ec((70.0, 0.0, 40.0)), "R"),
           ("Draft cage", part("bal7_frame", local=(60.0, 0.0, 300.0)), "L")]
    c.chapter(1, "1. 0 to 90 deg with the one P16")
    c.move(5.0, lambda t, i, n: dict(st=L.State(tilt=90.0 * t, **S0), cam=CAM_SIDE90, hide=near_cut, focus=foc, opacity=opac,
                                     labels=lab if t > 0.85 else (), readout=tilt_ro,
                                     text="The P16's pin is under the solenoid's cradle, 66 mm behind and 62 mm under the hinge (91 mm from it; v7: "
                                          "95). The P16 leans 32 deg back from it to a clevis on a cross bar 95 mm off the bench; 0-90 deg takes "
                                          "126 mm of its 150 and leaves 24 mm spare.", save_as="t1" if preview else None))
    c.hold(1.2)
    c.chapter(2, "2. Back to 0, and down onto the guides' seats")
    c.move(3.0, lambda t, i, n: dict(st=L.State(tilt=90.0 * (1 - t), **S0), cam=CAM_SIDE90, hide=near_cut, focus=foc, opacity=opac, readout=tilt_ro,
                                     text="", save_as="t2" if preview else None))
    c.move(1.2, lambda t, i, n: dict(st=L.State(ext=PARK_DROP8 * (1 - t), **S0), cam=CAM_SIDE90, hide=near_cut, focus=foc, opacity=opac,
                                     readout=rise_ro, text="", save_as="t3" if preview else None))
    c.hold(0.8)
    c.done()


# ---------------------------------------------------------------- 7. the frame: the NEMA 34 moved, the front cover
def frame(preview=False):
    c = E.Clip("frame_v8", TAG, 2, preview)
    cam1 = ((210, 60, 240), (0.9, 1.0, 0.55), 900)
    foc1 = lambda p: p.group == "drive" or p.key in ("nema34", "sam_electronics_carriage", "guide7_vee", "guide7_cone", "rung", "cross7")   # noqa: E731
    lab1 = [("NEMA 34: 35 mm toward +y\n(behind the +y guide)", part("nema34", local=(0, 0, -80.0)), "R"),
            ("Drive chain: 46 links,\nleaning 14 deg to the B+ shaft", part("sprocket_15_motor"), "R"),
            ("EC v8 and its guides, where\nthe NEMA 34 was (v2-v7)", part("sam_electronics_carriage", local=(110.0, 0.0, 50.0)), "L")]
    c.chapter(1, "1. The NEMA 34 makes room for the EC")
    c.move(4.0, lambda t, i, n: dict(st=L.State(ext=0.0, **S0), cam=R.cam_lerp(cam1, ((210, 60, 240), (0.4, 1.0, 0.35), 900), t), hide=lambda p: wide(p),
                                     focus=foc1, labels=lab1 if t > 0.2 else (),
                                     text="v2-v7's NEMA 34 sat inside the frame under the bottom run, right where EC v8 and its guides now are. It "
                                          "moves 35 mm toward +y on the back plate, and its drive chain to the B+ shaft leans 14 deg (46 links).",
                                     save_as="f1" if preview else None))
    c.chapter(2, "2. The front cover: a notch round the balance")
    cam2 = ((-60, 0, 260), (-1.0, -0.55, 0.25), 1100)
    foc2 = lambda p: p.group in ("enclosure", "scale")                                         # noqa: E731
    lab2 = [("Front panel notched round\nthe balance (no front hatch)", part("panel_front_hatch", local=(60.0, 500.0, 0.0)), "R"),
            ("Brush strips on the notch's\nsides and top", part("brush_strip_h", local=(4.0, 60.0, 6.0)), "L"),
            ("The balance's own side doors:\ntheir grips stay outside", part("bal7_door_left", local=(-80.0, -100.0, 150.0)), "L")]
    c.move(4.5, lambda t, i, n: dict(st=L.State(ext=0.0, side_door=BAL8_DOOR_OPEN * max(0.0, (t - 0.5) / 0.5)), cam=cam2,
                                     hide=lambda p: p.group == "elec", focus=foc2, labels=lab2 if t > 0.15 else (),
                                     opacity=lambda pl: opac(pl, {"panel_front_hatch": 0.25}),
                                     readout=lambda st: f"side door {st.side_door:4.1f} of {BAL8_DOOR_OPEN:.0f} mm",
                                     text="The balance stands 110 mm proud of the front panel, so the panel is notched round it up to 2 mm over the "
                                          "draft cage, with brush strips on the notch's edges. No front hatch: the beaker goes in and out through the "
                                          "balance's own side doors, whose grips stay outside the panel.",
                                     save_as="f2" if preview else None))
    c.hold(1.0)
    c.done()


CLIPS = {"overview": overview, "drop": drop, "ec": ec_clip, "door": door, "balance": balance, "tilt90": tilt90, "frame": frame}

if __name__ == "__main__":
    pv = "--preview" in sys.argv
    for name in [a for a in sys.argv[1:] if not a.startswith("--")] or list(CLIPS):
        CLIPS[name](pv)
