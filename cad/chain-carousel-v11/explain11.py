"""v11's clips (Sam, PR #185, 2026-11-25: "Make this a v11 and give gifs of all the interesting changes and interactions"). Every frame is
the v11 CAD (layout.placements) in the state described, moving by the model's own kinematics (the chain, the P16's two pins, the door
ramp); explain.py's Clip keeps the parts a step is about in colour and washes the rest out.

    xvfb-run -a python explain11.py overview|tilt90|rail|door|solenoid|balance [--preview]
    -> renders/v11/<name>_v11.{mp4,gif}
The profile view of the rail and the door ramp is rail_profile.py.
"""
from __future__ import annotations

import math
import sys

import numpy as np

import explain as E
import layout as L
import parts11 as P11
import render as R
import render_balance as RB
from params import (ACT_STROKE, BEAKER_H, CHAIN_L, DOOR_TRAVEL, HINGE_X, MODULE_LINKS, P, RUN_DIRECTION, SOL11_X)

E.OUT = R.OUT / "v11"
H = L.HINGE_STATION
D = L.DOSE_POINT
SY = L.STATION_Y
PAN = L.scale_pan_target()
part, sam, world = E.part, E.sam, E.world
TAG = "chain carousel v11 · PR #185 · 2026-11-25"
S0 = dict(enclosure=False)
FPS = E.FPS
RIM = float(P11.BEAKER11_RIM)
Z_LAND = RIM - BEAKER_H + 6.0
SEE = ("panel_", "hatch_", "bal11_glass", "bal11_door", "bal11_lid")
DROP = float(H[2]) - RIM


def ec(local):
    return part("ec11", local=local)


def opac(pl, extra=None):
    o = {}
    for k, p in R.keyed(pl):
        if p.key == "beaker":
            o[k] = 0.4
        elif p.key.startswith(SEE):
            o[k] = 0.18
        if extra and p.key in extra:
            o[k] = extra[p.key]
    return o


def near_cut(p) -> bool:
    """A section on the station from -y: what stands between the camera and the station goes (the -y frame, the beam and the guide,
    the -y carriages and modules, the -y side of the balance's cage); the station's own parts and the P16 stay."""
    if p.group in ("enclosure", "elec"):
        return True
    if p.key in ("beam10", "guide11", "bal11_door_left", "m5x35_shcs"):
        return True
    if p.group in ("station_act", "station_ec", "cable") or p.module == 0 or p.key in ("p16_bracket11", "bar11"):
        return False
    if p.group == "scale":
        return False
    y = p.M[1, 3]
    if p.group == "station":
        return y < SY - 60.0
    if p.key in ("shaft", "shaft_drive", "sprocket_32", "flange_bearing", "bolt_m6x25", "nut_m6", "tensioner_block", "m5x30_shcs", "m5x10_shcs", "nut_m5"):
        return y < -20.0
    if p.key in ("rung", "ext_x", "ext_post", "corner_bracket"):
        return y < SY - 100.0
    return y < SY - 35.0


def front_cut(p) -> bool:
    """near_cut, and everything in front of the front chain that isn't the station's, a module's or the P16's mount, for close-ups."""
    if near_cut(p):
        return True
    if p.group in ("modules", "carriages", "station_ec", "station_act", "cable", "scale") or p.key in ("p16_bracket11", "bar11"):
        return False
    return p.M[0, 3] < 5.0


def close_cut(p) -> bool:
    if front_cut(p):
        return True
    if p.module >= 0 and p.group in ("modules", "carriages"):
        y, z = p.M[1, 3], p.M[2, 3]
        return abs(y - SY) > 1.3 * MODULE_LINKS * P or z > 430.0
    return False


def ext_ro(st: L.State) -> str:
    return f"P16-150 {L.p16_11_ext(st.tilt):5.1f} of {ACT_STROKE:.0f} mm out\nlever {L.p16_11_lever(st.tilt):4.0f} mm"


def tilt_ro(st: L.State) -> str:
    return f"tilt {max(st.tilt, 0.0):4.1f} deg\n" + ext_ro(st)


def off_ro(st: L.State) -> str:
    k = L.carriage_at(L.CARRIAGE_LINK0, round(st.shift), tol=0.6)
    off = L.module_offset(k, st) if k >= 0 else 0.0
    return f"module {abs(off):4.1f} mm from the station\nlift 0 deg, door {P11.door_open_at(off):3.1f} of {DOOR_TRAVEL:.0f} mm"


def incoming(t: float) -> float:
    """Chain shift that brings the next module (from the +y side, the way the machine runs) in to the station as t goes 0 -> 1."""
    return -RUN_DIRECTION * MODULE_LINKS * (1.0 - t)


def _dose(c: E.Clip, secs: float, foc=None, text: str = "", cam=None, hide=near_cut, save=None, tilt=30.0, op=None) -> None:
    g = {"g": None}

    def fr(t, i, n):
        if g["g"] is None:
            g["g"] = RB.Grains(c.v)
        tt = i / FPS
        return dict(st=L.State(tilt=tilt, spin=2 * math.pi * 1.5 * t, tap=(2.0 if (i // 2) % 3 == 0 else 0.0), **S0), cam=cam, hide=hide, focus=foc,
                    opacity=op or opac, before=lambda v, s: g["g"].set(tt, True, Z_LAND),
                    readout=lambda st: f"tilt {tilt:.1f} deg\nauger {st.spin / (2 * math.pi):3.1f} turns", text=text, save_as=save)
    c.move(secs, fr, eased=False)
    if g["g"] is not None:
        g["g"].set(0.0, False, Z_LAND)


HX, HZ = float(H[0]), float(H[2])
CAM_SIDE = ((HX + 10.0, SY, HZ + 85.0), (0.0, -1.0, 0.08), 760)          # the station and the P16 to the front plate, side section from -y
CAM_SIDE_HI = ((HX - 5.0, SY, HZ + 120.0), (0.0, -1.0, 0.06), 900)       # ... with the module up at 90 deg
CAM_FRONT = ((-48.0, -31.0, 575.0), (-0.78, -0.62, 0.30), 380)            # outside the front plate: the bar, the clevis, the slot
CAM_RAIL = ((HX + 62.0, SY + 2.0, HZ + 26.0), (-0.62, -0.62, 0.48), 230)  # the rail, the T and the gear meeting the pinion
CAM_GEAR = ((HX + 84.0, SY, HZ + 22.0), (-0.97, -0.10, 0.22), 150)       # the gear meeting the pinion, from the front
CAM_DOOR = ((HX - 3.0, SY, HZ + 22.0), (-0.72, -0.52, 0.46), 165)        # the door ramp over the outlet
CAM_SOL = ((HX + SOL11_X, SY, HZ + 25.0), (-0.35, -0.86, 0.36), 190)    # the solenoid over clip 1
CAM_BAL = ((HX - 20.0, SY, 260.0), (-1.0, -1.05, 0.42), 1250)            # the balance under the station, from the front
CAM_DROP = ((HX - 4.0, SY, HZ - 22.0), (0.0, -1.0, 0.05), 205)           # the exit, the lid and the beaker


# ---------------------------------------------------------------- 1. overview
def overview(preview=False):
    c = E.Clip("overview_v11", TAG, 3, preview)
    camA = ((110, 0, 400), (-1.0, -1.1, 0.5), 1800)
    camB = ((110, 0, 400), (-1.15, 0.75, 0.42), 1800)
    lab = [("P16-150 through the front side plate,\nbase on a new bar across the front posts", part("actuator_body", local=(0, 0, 40.0)), "R"),
           ("EC v11 inside the loop, from over\nthe outlet back past the motor", ec((60.0, 0.0, -36.0)), "R"),
           ("Carriages 40 mm longer\n(chains 345 mm apart)", part("carriage", module=3, local=(0.0, -8.0, CHAIN_L / 2)), "L"),
           ("Tall-cage balance on the bench;\nbeaker on a pillar inside it", world((PAN[0] - 60.0, PAN[1] - 100.0, 200.0)), "L")]
    c.chapter(1, "Chain carousel v11: v10's station, with 0-90 deg and no lift")
    c.move(4.5, lambda t, i, n: dict(st=L.State(), cam=R.cam_lerp(camA, camB, t), hide=lambda p: p.group == "elec", labels=lab if t > 0.2 else (),
                                     opacity=lambda pl: opac(pl, {"panel_side": 0.1, "panel_side_hatch": 0.1, "panel_top": 0.08}),
                                     text="v10's station inside the loop, with the carriages 40 mm longer, the hinge 5 mm nearer the carriage, a "
                                          "straight rail, the door opened by the EC itself, the solenoid near the outlet, a P16-150 through the front "
                                          "plate for 0-90 deg, and the carousel lowered over a balance with its tall draft cage.",
                                     save_as="o1" if preview else None))
    c.chapter(2, "Index: the next module slides straight into the EC's rail")
    c.move(2.5, lambda t, i, n: dict(st=L.State(shift=incoming(t), **S0), cam=R.cam_lerp(camB, CAM_SIDE, min(1.0, 2 * t)),
                                     hide=near_cut if t > 0.4 else (lambda p: p.group == "elec"), opacity=opac, readout=off_ro,
                                     text="The NEMA 34 moves both chains 8 links. The T-bracket slides straight through the slot under the EC (its "
                                          "ends only flare, to steer it in); the 44T gear meets the pinion at rest, and the EC's front ramp opens "
                                          "the outlet door.", save_as="o2" if preview else None))
    c.chapter(3, "Pull up, dose, on to 90 deg, and back")
    c.move(1.8, lambda t, i, n: dict(st=L.State(tilt=30.0 * t, **S0), cam=R.cam_lerp(CAM_SIDE, CAM_SIDE_HI, t), hide=near_cut,
                                     opacity=opac, readout=tilt_ro, text="The P16 retracts: it pulls the EC, and the module coupled to it, up about the hinge.",
                                     save_as="o3" if preview else None))
    _dose(c, 1.8, cam=CAM_SIDE_HI, text=f"The NEMA 11 turns the auger and the solenoid taps near the outlet; the dose falls {DROP:.0f} mm "
                                        "through the lid into the beaker.", save="o4" if preview else None)
    c.move(2.2, lambda t, i, n: dict(st=L.State(tilt=30.0 + 60.0 * t, **S0), cam=CAM_SIDE_HI, hide=near_cut, opacity=opac, readout=tilt_ro,
                                     text="On to 90 deg: the longer carriage leaves the EC room in front of the hinge, and the P16 has room "
                                          "through the front plate.", save_as="o5" if preview else None))
    c.move(2.2, lambda t, i, n: dict(st=L.State(tilt=90.0 * (1 - t), **S0), cam=R.cam_lerp(CAM_SIDE_HI, CAM_SIDE, t), hide=near_cut,
                                     opacity=opac, readout=tilt_ro, text="The P16 extends again: the module sets down on its own carriage, the EC on its guide.",
                                     save_as="o6" if preview else None))
    c.move(2.0, lambda t, i, n: dict(st=L.State(shift=RUN_DIRECTION * MODULE_LINKS * t, **S0), cam=CAM_SIDE,
                                     hide=near_cut, opacity=opac, readout=off_ro, text="The next index slides it straight out the other end; the door shuts.",
                                     save_as="o7" if preview else None))
    c.hold(1.0)
    c.done()


# ---------------------------------------------------------------- 2. 90 deg: the longer carriage and the P16 through the front plate
def tilt90(preview=False):
    c = E.Clip("tilt90_v11", TAG, 2, preview)
    foc = lambda p: p.group in ("station_act", "station_ec") or p.key in ("p16_bracket11", "bar11", "side_plate_front", "carriage") and (p.key != "carriage" or p.module == 0) or p.module == 0  # noqa: E731
    lab = [("P16-150, its base outside\nthe front side plate", part("actuator_body", local=(-8.0, 0, 60.0)), "L"),
           ("Its clevis hangs from a new\n2020 bar across the front posts", part("bar11", local=(0.0, 0.0, 200.0)), "L"),
           ("Slot through the front side plate", world((-33.0, -31.0, 560.0)), "L"),
           (f"Hinge {HINGE_X:.0f} mm behind the front chain\n(v10: 33): the carriage is 40 mm longer", world((HX, SY, HZ)), "R")]
    c.chapter(1, "1. 0 to 90 deg with one P16")
    c.move(6.0, lambda t, i, n: dict(st=L.State(tilt=90.0 * t, **S0), cam=CAM_SIDE_HI, hide=near_cut, focus=foc, opacity=opac,
                                     labels=lab, readout=tilt_ro,
                                     text="Everything on the plate's side swings forward as the module tilts. v10's hinge was 33 mm behind the front "
                                          "chain and its EC reached the chain at 70 deg; v11's is 73 mm back (40 mm longer carriages). 0-90 deg takes "
                                          "131 mm of the P16's travel, so it's a P16-150, based outside the front plate.", save_as="t1" if preview else None))
    c.move(3.0, lambda t, i, n: dict(st=L.State(tilt=90.0 * (1 - t), **S0), cam=CAM_SIDE_HI, hide=near_cut, focus=foc, opacity=opac, readout=tilt_ro,
                                     text="", save_as="t2" if preview else None))
    c.chapter(2, "2. Outside the front plate: the bar, the clevis and the slot")
    foc2 = lambda p: p.group in ("station_act",) or p.key in ("p16_bracket11", "bar11", "side_plate_front", "m5x35_shcs", "clevis_screw", "nut_m3_clevis")  # noqa: E731
    hide2 = lambda p: p.group in ("enclosure", "elec", "scale") or (p.module >= 0 and p.module != 0)  # noqa: E731
    lab2 = [("2020 bar on the front posts'\nfront faces (z 620-640)", part("bar11", local=(0.0, 0.0, 120.0)), "L"),
            ("Printed clevis, two M5\ninto T-nuts in the bar", part("p16_bracket11", local=(-66.35, -31.0, 616.0)), "L"),
            ("Slot for the P16 (22 x 68 mm)", world((-36.4, -31.0, 545.0)), "R")]
    c.move(5.0, lambda t, i, n: dict(st=L.State(tilt=90.0 * math.sin(math.pi * t), **S0), cam=CAM_FRONT, hide=hide2, focus=foc2, labels=lab2,
                                     opacity=lambda pl: opac(pl, {"side_plate_front": 0.6}), readout=tilt_ro,
                                     text="Sam's hole through the metal plate: a 22 x 68 mm slot clears the P16's housing and tube over 0-90 deg. Its "
                                          "base pin is 26 mm in front of the plate, on a printed clevis under a new 2020 bar across the front posts. "
                                          "The front acrylic panel moves out to 30 mm standoffs to clear them.",
                                     save_as="t3" if preview else None))
    c.hold(0.8)
    c.done()


# ---------------------------------------------------------------- 3. the rail in 3D: straight in, the gear meets the pinion at rest
def rail(preview=False):
    c = E.Clip("rail_v11", TAG, 2, preview)
    foc = lambda p: p.key in ("ec11", "t_bracket", "pinion24", "nema11", "door_head11", "door_rod11") or (p.group == "modules" and p.key in ("auger",))  # noqa: E731
    op = lambda pl: opac(pl, {"ec11": 0.6})                                                                             # noqa: E731
    lab = [("T-bracket on the plate", part("t_bracket", module=0, local=(60.0, 0.0, -26.0)), "L"),
           ("The EC's T-slot: level lips,\nflared ends", ec((60.0, -11.0, -24.0)), "R"),
           ("24T pinion on the EC", ec((83.0, 0.0, -34.25)), "R"),
           ("44T gear on the auger", sam(0, (83.0, 0.0, -20.0)), "L")]
    c.chapter(1, "1. The T slides straight through; nothing lifts")
    c.move(6.0, lambda t, i, n: dict(st=L.State(shift=incoming(0.3 + 0.7 * t), **S0), cam=CAM_RAIL, hide=close_cut, focus=foc, opacity=op,
                                     labels=lab if t > 0.1 else (), readout=off_ro,
                                     text="v10's ramps lifted each module 4 deg to bring its gear up to the pinion. v11's hinge is 5 mm nearer the "
                                          "carriage, so the gear pokes 5 mm past it at rest and a 24T pinion meets it there. The lips are level; the "
                                          "ends flare only to steer a T that arrives a little off line.",
                                     save_as="r1" if preview else None))
    c.chapter(2, "2. The gear meets the pinion from the side, at rest")
    c.move(4.0, lambda t, i, n: dict(st=L.State(shift=incoming(0.75 + 0.25 * t), **S0), cam=CAM_GEAR, hide=close_cut, focus=foc,
                                     opacity=lambda pl: opac(pl, {"ec11": 0.35, "sam_mounting_plate": 0.5, "t_bracket": 0.6, "door_housing": 0.5}), readout=off_ro,
                                     text="The gear slides into mesh sideways over its last 11 mm, as in v10. Leave the NEMA 11 free (or turn it "
                                          "slowly) while the chain indexes, so the pinion turns out of the gear's way.",
                                     save_as="r2" if preview else None))
    c.hold(1.0)
    c.done()


# ---------------------------------------------------------------- 4. the door, opened by the EC itself
def door(preview=False):
    c = E.Clip("door_v11", TAG, 1, preview)
    foc = lambda p: p.key in ("ec11", "door_shutter", "door_housing", "door_rod11", "door_head11")                      # noqa: E731
    lab = [("Rod's head (printed)", part("door_head11", module=0, local=(P11.DOOR11_ROD_X, 0.0, -24.5)), "R"),
           ("The 3 mm exit, on the hinge axis", sam(0, (0.0, 0.0, 0.0)), "R"),
           ("The EC's door ramp, over the outlet", ec((-3.0, -13.0, -26.0)), "L"),
           ("1.5 mm stainless rod up the\nspring's axis, through the cap", part("door_rod11", module=0, local=(P11.DOOR11_ROD_X, 0.0, -14.0)), "L"),
           ("Shutter over the 3 mm exit", sam(0, (-1.0, 0.0, 2.0)), "L")]
    c.chapter(1, "The EC reaches over the outlet and draws the door open")
    c.move(6.0, lambda t, i, n: dict(st=L.State(shift=incoming(0.45 + 0.55 * t), **S0), cam=CAM_DOOR, hide=close_cut, focus=foc,
                                     opacity=lambda pl: opac(pl, {"ec11": 0.7}), labels=lab, readout=off_ro,
                                     text="Sam: \"it can extend all the way down to the dispensing end of the auger ... so it can directly open it.\" "
                                          "A stainless rod runs from each shutter up through its spring and cap to a small head; the EC's front ramp "
                                          "catches the head and draws it 6 mm as the module arrives. The spring shuts the door as it leaves. No cable.",
                                     save_as="d1" if preview else None))
    c.hold(1.0)
    c.done()


# ---------------------------------------------------------------- 5. the solenoid in the auger's first third
def solenoid(preview=False):
    c = E.Clip("solenoid_v11", TAG, 1, preview)
    foc = lambda p: p.key in ("ec11", "solenoid") or p.module == 0 and p.key in ("sam_mounting_plate", "auger")         # noqa: E731
    lab = [("Solenoid over clip 1", part("solenoid", local=(0.0, 0.0, -14.0)), "R"),
           (f"Clip 1: {SOL11_X:.0f} mm behind the exit\n(13 % of the auger; v10: 62 %)", sam(0, (SOL11_X, 0.0, 12.0)), "L")]
    c.chapter(1, "The solenoid taps in the auger's first third")
    c.move(5.0, lambda t, i, n: dict(st=L.State(tilt=30.0 * min(1.0, 2.5 * t), tap=(2.5 if (i // 2) % 2 == 0 and t > 0.45 else 0.0), **S0), cam=CAM_SOL,
                                     hide=close_cut, focus=foc, opacity=lambda pl: opac(pl, {"ec11": 0.5}), labels=lab, readout=tilt_ro,
                                     text="Sam: \"move the solenoid up to the first third of the auger. That's where we get the most effective taps.\" "
                                          "It now stands in the EC just behind the outlet, its plunger 1.2 mm off the plate where clip 1 holds the "
                                          "tube, and taps there at every tilt (it turns with the module).",
                                     save_as="s1" if preview else None))
    c.hold(1.0)
    c.done()


# ---------------------------------------------------------------- 6. the balance with its tall cage, the pillar, the lid, the doorway
def balance(preview=False):
    c = E.Clip("balance_v11", TAG, 2, preview)
    foc = lambda p: p.group == "scale" or p.module == 0 or p.key in ("panel_front_door11",)                              # noqa: E731
    hide = lambda p: p.group == "elec" or p.key in ("panel_side",)                                                      # noqa: E731
    lab = [("Balance with its tall draft cage\n(315 mm, the HR-100A's height), on the bench", world((PAN[0] - 60.0, PAN[1] - 100.0, 160.0)), "L"),
           ("Beaker on a cylindrical pillar", world((PAN[0], PAN[1] - 25.0, 200.0)), "R"),
           ("Front panel: an open doorway\nfor the balance", world((L.ENC_XF, SY + 120.0, 328.0)), "R")]
    c.chapter(1, "1. The carousel lowered over a balance with its tall draft cage")
    c.move(5.0, lambda t, i, n: dict(st=L.State(), cam=R.cam_lerp(CAM_BAL, ((HX - 10.0, SY, 250.0), (-1.0, 0.7, 0.4), 1250), t), hide=hide, focus=foc,
                                     labels=lab, opacity=lambda pl: opac(pl, {"panel_front_door11": 0.25, "panel_side_hatch": 0.12, "panel_top": 0.1, "panel_back": 0.1}),
                                     text="Sam: \"scale it to fit the scale with the higher draft cage (with the beaker sitting on a cylindrical "
                                          "pillar).\" The carousel is 98.5 mm lower than v10, so the passing 44T gears clear the cage's top by 4 mm. "
                                          "The front panel has an open doorway the balance slides through; no bay window, no weighing chamber.",
                                     save_as="b1" if preview else None))
    c.chapter(2, f"2. A dosing lid in the cage's top; the dose falls {DROP:.0f} mm into the beaker")
    labd = [("Exit (on the hinge axis)", world((D[0], D[1], D[2])), "R"), ("Dosing lid in the top frame,\n24 mm hole under the exit", part("bal11_lid", local=(20.0, 0.0, 314.0)), "R"),
            (f"Beaker's rim {DROP:.0f} mm under the exit", world((PAN[0] - 19.0, D[1], RIM)), "L")]
    opd = lambda pl: opac(pl, {"bal11_frame": 0.16})                                                                    # noqa: E731
    c.move(1.5, lambda t, i, n: dict(st=L.State(tilt=30.0 * t, **S0), cam=CAM_DROP, hide=near_cut, focus=foc, opacity=opd, readout=tilt_ro, labels=labd,
                                     text="The top door slides out and a 3 mm lid with a 24 mm hole sits in its place, flush with the frame.",
                                     save_as="b2" if preview else None))
    _dose(c, 2.4, foc=foc, cam=CAM_DROP, op=opd, text=f"{DROP:.0f} mm from the exit to the rim (v10, with no cage: 18). A smaller balance on a block with no "
                                                      "cage could bring the rim up to 14 mm under the exit.", save="b3" if preview else None)
    c.hold(1.0)
    c.done()


CLIPS = {"overview": overview, "tilt90": tilt90, "rail": rail, "door": door, "solenoid": solenoid, "balance": balance}

if __name__ == "__main__":
    pv = "--preview" in sys.argv
    for name in [a for a in sys.argv[1:] if not a.startswith("--")] or list(CLIPS):
        CLIPS[name](pv)
