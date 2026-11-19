"""v10's clips (Sam, PR #185, 2026-11-19: "again show close up gifs of any feature changes or interesting interactions or things to
highlight"). Every frame is the v10 CAD (layout.placements) in the state described, moving by the model's own kinematics (the chain,
the rail's lift, the door ramp, the P16's two pins); explain.py's Clip keeps the parts a step is about in colour and washes the rest out.

    xvfb-run -a python explain10.py overview|rail|pull|wiring|guide|drop|limit [--preview]
    -> renders/v10/<name>_v10.{mp4,gif}
"""
from __future__ import annotations

import math
import sys

import numpy as np

import explain as E
import layout as L
import parts10 as P10
import render as R
import render_balance as RB
from params import (BEAKER_H, D10, DOOR_TRAVEL, MODULE_LINKS, P, P16_10_STROKE, RUN_DIRECTION, TAU0, TILT_MAX_V10)

E.OUT = R.OUT / "v10"
H = L.HINGE_STATION
D = L.DOSE_POINT
SY = L.STATION_Y
PAN = L.scale_pan_target()
part, sam, world = E.part, E.sam, E.world
TAG = "chain carousel v10 · PR #185 · 2026-11-19"
S0 = dict(enclosure=False)
FPS = E.FPS
RIM = L.BEAKER10_RIM
Z_LAND = RIM - BEAKER_H + 6.0
SEE = ("panel_", "hatch_", "bay10_", "baffle10_", "deck10_")
TMAX = TILT_MAX_V10


def ec(local):
    return part("ec10", local=local)


def opac(pl, extra=None):
    o = {}
    for k, p in R.keyed(pl):
        if p.key == "beaker":
            o[k] = 0.35
        elif p.key.startswith(SEE):
            o[k] = 0.16
        if extra and p.key in extra:
            o[k] = extra[p.key]
    return o


def near_cut(p) -> bool:
    """A section on the station from -y: what stands between the camera and the station goes (the -y frame, the beam, the -y
    carriages and modules, the -y baffle and the bay's -y side); the station's own parts (EC, P16, guide, cables) stay."""
    if p.group in ("enclosure", "elec"):
        return True
    if p.key in ("baffle10_side_m", "bay10_side_m", "bay10_front", "bay9_door", "beam10", "guide10", "cable10_outside"):
        return True
    if p.group in ("station_act", "station_ec", "cable") or p.module == 0:
        return False
    if p.group == "scale":
        return False
    y = p.M[1, 3]
    if p.group == "station":
        return y < SY - 60.0 and p.key not in ("p16_bracket10",)
    if p.key in ("shaft", "shaft_drive", "sprocket_32", "flange_bearing", "bolt_m6x25", "nut_m6"):
        return y < -20.0
    if p.key in ("rung", "ext_x", "ext_post", "corner_bracket"):
        return y < SY - 100.0
    return y < SY - 35.0


def front_cut(p) -> bool:
    """near_cut, and everything in front of the front chain that isn't the station's or a module's (the front side plate, its
    bearings and hold-down, the front chain and sprockets), for close-ups from the front."""
    if near_cut(p):
        return True
    if p.group in ("modules", "carriages", "station_ec", "station_act", "cable", "scale") or p.key in ("p16_bracket10",):
        return False
    return p.M[0, 3] < 5.0


def close_cut(p) -> bool:
    """front_cut, and every carriage and module more than 1.3 modules along the bottom run from the station (or on another run)."""
    if front_cut(p):
        return True
    if p.module >= 0 and p.group in ("modules", "carriages"):
        y, z = p.M[1, 3], p.M[2, 3]
        return abs(y - SY) > 1.3 * MODULE_LINKS * P or z > 520.0
    return False


def ext_ro(st: L.State) -> str:
    return f"P16-100 {L.p16_10_ext(st.tilt):5.1f} of {P16_10_STROKE:.0f} mm out"


def tilt_ro(st: L.State) -> str:
    return f"tilt {max(st.tilt, TAU0):4.1f} deg\n" + ext_ro(st)


def off_ro(st: L.State) -> str:
    k = L.carriage_at(L.CARRIAGE_LINK0, round(st.shift), tol=0.6)
    off = L.module_offset(k, st) if k >= 0 else 0.0
    return f"module {abs(off):4.1f} mm from the station\nlift {P10.module_lift(off):3.1f} deg, door {P10.door_open_at(off):3.1f} of {DOOR_TRAVEL:.0f} mm"


def incoming(t: float) -> float:
    """Chain shift that brings the next module (from the +y side, the way the machine runs) in to the station as t goes 0 -> 1."""
    return -RUN_DIRECTION * MODULE_LINKS * (1.0 - t)


def _dose(c: E.Clip, secs: float, foc=None, text: str = "", cam=None, hide=near_cut, save=None, tilt=30.0) -> None:
    g = {"g": None}

    def fr(t, i, n):
        if g["g"] is None:
            g["g"] = RB.Grains(c.v)
        tt = i / FPS
        return dict(st=L.State(tilt=tilt, spin=2 * math.pi * 1.5 * t, **S0), cam=cam, hide=hide, focus=foc, opacity=opac,
                    before=lambda v, s: g["g"].set(tt, True, Z_LAND), readout=lambda st: f"tilt {tilt:.1f} deg\nauger {st.spin / (2 * math.pi):3.1f} turns",
                    text=text, save_as=save)
    c.move(secs, fr, eased=False)
    if g["g"] is not None:
        g["g"].set(0.0, False, Z_LAND)


CAM_SIDE = ((95.0, SY, 470.0), (0.0, -1.0, 0.10), 640)          # the station, side section from -y
CAM_SIDE_HI = ((95.0, SY, 520.0), (0.0, -1.0, 0.08), 760)       # ... with room for the module tilted up into the loop
CAM_RAIL = ((75.0, SY + 4.0, 466.0), (-0.86, -0.30, 0.42), 250)  # the rail, the T and the gear, close, from the front, above
CAM_DOOR = ((28.0, SY, 458.0), (-0.80, -0.42, 0.42), 175)       # the door ramp and the tab
CAM_GEAR = ((84.0, SY, 460.0), (-0.97, -0.08, 0.22), 150)        # the gear meeting the pinion, from the front
CAM_GUIDE = ((146.0, -34.0, 476.0), (0.88, -0.38, 0.28), 140)     # the guide shoe in its seat, from behind and below the beam
CAM_FRONT = ((-30.0, -60.0, 560.0), (-1.0, -0.55, 0.30), 760)    # the front side plate, the grommet, the P16's bracket
CAM_DROP = ((36.0, SY, 428.0), (0.0, -1.0, 0.05), 210)            # the exit and the beaker, close


# ---------------------------------------------------------------- 1. overview
def overview(preview=False):
    c = E.Clip("overview_v10", TAG, 3, preview)
    camA = ((90, 0, 470), (-1.0, -1.1, 0.5), 1750)
    camB = ((90, 0, 470), (-1.15, 0.75, 0.42), 1750)
    lab = [("P16-100 inside the loop, base on\nthe front side plate", part("p16_100_body", local=(0, 0, 60.0)), "R"),
           ("EC v10 inside the loop, on the\nplate's side of the module", ec((120.0, 0.0, -45.0)), "R"),
           ("Station beam inside the loop\n(carries the EC's guide)", part("beam10", local=(0, 0, 250.0)), "L"),
           ("Beaker 18 mm under the exit;\nnothing of the station below", world((PAN[0], PAN[1] - 22.0, RIM)), "L")]
    c.chapter(1, "Chain carousel v10: the station turned upside down")
    c.move(4.5, lambda t, i, n: dict(st=L.State(), cam=R.cam_lerp(camA, camB, t), hide=lambda p: p.group == "elec", labels=lab if t > 0.2 else (),
                                     opacity=lambda pl: opac(pl, {"panel_side": 0.1, "panel_side_hatch": 0.1, "panel_top": 0.08}),
                                     text="v9's carousel, balance and enclosure, with the station moved inside the loop: the EC sits on the plate's "
                                          "side of the module and one P16-100 pulls it up to dose. Nothing of the station is under the auger, so the "
                                          "beaker's rim is 18 mm under the exit (v9: 32, v7: 154).",
                                     save_as="o1" if preview else None))
    c.chapter(2, "Index: the next module slides into the EC's rail")
    c.move(2.5, lambda t, i, n: dict(st=L.State(shift=incoming(t), **S0), cam=R.cam_lerp(camB, CAM_SIDE, min(1.0, 2 * t)),
                                     hide=near_cut if t > 0.4 else (lambda p: p.group == "elec"), opacity=opac, readout=off_ro,
                                     text="The NEMA 34 moves both chains 8 links. The plate's T-bracket slides into the slot under the EC; the slot's "
                                          "ramps lift the module 4 deg into mesh with the pinion, and a second ramp opens the outlet door.",
                                     save_as="o2" if preview else None))
    c.chapter(3, "Pull up, dose, and back")
    c.move(1.8, lambda t, i, n: dict(st=L.State(tilt=TAU0 + (30.0 - TAU0) * t, **S0), cam=R.cam_lerp(CAM_SIDE, CAM_SIDE_HI, t), hide=near_cut,
                                     opacity=opac, readout=tilt_ro, text="The P16 retracts: it pulls the EC, and the module coupled to it, up about the hinge.",
                                     save_as="o3" if preview else None))
    _dose(c, 1.8, cam=CAM_SIDE_HI, text="The NEMA 11 turns the auger; the dose falls 18 mm from the exit into the beaker on the pan.", save="o4" if preview else None)
    c.move(1.5, lambda t, i, n: dict(st=L.State(tilt=30.0 + (TMAX - 30.0) * t, **S0), cam=CAM_SIDE_HI, hide=near_cut, opacity=opac, readout=tilt_ro,
                                     text=f"On to {TMAX:.0f} deg, where the EC's front comes up to the front chain.", save_as="o5" if preview else None))
    c.move(2.0, lambda t, i, n: dict(st=L.State(tilt=TMAX - (TMAX - TAU0) * t, **S0), cam=R.cam_lerp(CAM_SIDE_HI, CAM_SIDE, t), hide=near_cut,
                                     opacity=opac, readout=tilt_ro, text="The P16 extends fully again: the EC settles on its guide, the module on the rail.",
                                     save_as="o6" if preview else None))
    c.move(2.0, lambda t, i, n: dict(st=L.State(shift=-RUN_DIRECTION * MODULE_LINKS * t * 0.0 + RUN_DIRECTION * MODULE_LINKS * t, **S0), cam=CAM_SIDE,
                                     hide=near_cut, opacity=opac, text="The next index slides it out the other end: the ramps set it back on its rest, the door shuts.",
                                     save_as="o7" if preview else None))
    c.hold(1.0)
    c.done()


# ---------------------------------------------------------------- 2. the keyed rail: the T in, the lift, the gear and the door
def rail(preview=False):
    c = E.Clip("rail_v10", TAG, 3, preview)
    foc = lambda p: p.key in ("ec10", "t_bracket", "pinion", "nema11", "door_shutter") or p.group == "modules" and p.key in ("auger",)  # noqa: E731
    op = lambda pl: opac(pl, {"ec10": 0.62})                                                                           # noqa: E731
    lab = [("T-bracket on the plate", part("t_bracket", module=0, local=(60.0, 0.0, -29.5)), "L"),
           ("The EC's T-slot: its lips\nramp up toward the station", ec((60.0, -9.5, -24.0)), "R"),
           ("20T pinion on the EC", ec((83.0, 0.0, -32.25)), "R"),
           ("44T gear on the auger", sam(0, (83.0, 0.0, -20.0)), "L")]
    c.chapter(1, "1. The T-bracket slides into the rail; the ramps lift the module")
    c.move(6.0, lambda t, i, n: dict(st=L.State(shift=incoming(0.35 + 0.65 * t), **S0), cam=CAM_RAIL, hide=close_cut, focus=foc, opacity=op,
                                     labels=lab if t > 0.1 else (), readout=off_ro,
                                     text="Every module passes through the slot under the EC. Its lips ramp up over 8 mm at each end, so the T rides "
                                          "up them and the module turns 4 deg about its hinge. That lifts the 44T gear into mesh with the pinion, "
                                          "which stays 4 mm over the passing carriages. The latch is already open (its cam's flat is +-18 mm).",
                                     save_as="r1" if preview else None))
    c.chapter(2, "2. The gear meets the pinion from the side")
    c.move(4.0, lambda t, i, n: dict(st=L.State(shift=incoming(0.75 + 0.25 * t), spin=0.0, **S0), cam=CAM_GEAR, hide=close_cut, focus=foc,
                                     opacity=lambda pl: opac(pl, {"ec10": 0.35, "sam_mounting_plate": 0.5, "t_bracket": 0.6, "door_guide10": 0.5, "door_housing": 0.5}), readout=off_ro,
                                     text="The gear slides into mesh sideways over its last 10 mm. Leave the NEMA 11 free (or turn it slowly) while "
                                          "the chain indexes, so the pinion turns out of the gear's way instead of the auger turning (test T6a).",
                                     save_as="r2" if preview else None))
    c.chapter(3, "3. The door ramp opens the outlet")
    foc3 = lambda p: p.key in ("ec10", "door_shutter", "door_housing", "door_guide10", "door_tab10")                                                  # noqa: E731
    lab3 = [("The cable's tab", part("door_tab10", module=0, local=(28.0, 0.0, -29.0)), "R"), ("The EC's door ramp", ec((30.5, -12.0, -27.0)), "L"),
            ("Cable in a PTFE sleeve, in a guide\nalong the plate's underside", part("door_guide10", module=0, local=(10.0, 0.0, -20.5)), "L"),
            ("Shutter over the 3 mm exit", sam(0, (-1.0, 0.0, 0.0)), "L")]
    c.move(5.0, lambda t, i, n: dict(st=L.State(shift=incoming(0.55 + 0.45 * t), **S0), cam=CAM_DOOR, hide=close_cut, focus=foc3,
                                     opacity=lambda pl: opac(pl, {"ec10": 0.6}), labels=lab3, readout=off_ro,
                                     text="Each door's shutter now hangs on a short cable: up through its spring and the housing's cap, back along the "
                                          "plate's underside in a PTFE sleeve, and up to a tab. A second ramp on the EC lifts the tab 6 mm as the "
                                          "module arrives, so the door is open within 6.5 mm of the station and shut again 16.5 mm out. Nothing of "
                                          "it hangs under the exit any more.",
                                     save_as="r3" if preview else None))
    c.hold(1.0)
    c.done()


# ---------------------------------------------------------------- 3. the P16 inside the loop pulls the module up
def pull(preview=False):
    c = E.Clip("pull_v10", TAG, 2, preview)
    foc = lambda p: p.group in ("station_act", "station_ec", "scale") or p.key in ("p16_bracket10",) or p.module == 0 or p.key == "carriage"  # noqa: E731
    lab = [("P16-100: fully out between doses", part("p16_100_body", local=(0, 0, 100.0)), "R"),
           ("Its base on a bracket on\nthe front side plate", part("p16_bracket10", local=(-20.0, -34.0, 680.0)), "L"),
           ("Rod end on the EC's arm", ec((90.0, 38.0, -32.0)), "R"),
           ("Beaker: rim 18 mm under the exit", world((PAN[0], PAN[1], RIM)), "L")]
    c.chapter(1, "1. Retract to pull the EC and the module up")
    c.move(5.0, lambda t, i, n: dict(st=L.State(tilt=TAU0 + (30.0 - TAU0) * t, **S0), cam=CAM_SIDE_HI, hide=near_cut, focus=foc, opacity=opac,
                                     labels=lab if t < 0.5 else lab[2:], readout=tilt_ro,
                                     text="Sam's idea: the actuator inside the loop, fully extended by default, retracting to dose. The EC is "
                                          "coupled to the module through the rail, so pulling the EC's arm turns both about the hinge. 4-30 deg "
                                          "takes 43 of the P16-100's 100 mm; its lever about the hinge is 20 mm or more all the way.",
                                     save_as="p1" if preview else None))
    _dose(c, 1.6, foc=foc, cam=CAM_SIDE_HI, text="Dose at 30 deg (the studies' 20-40 deg range).", save="p2" if preview else None)
    c.chapter(2, f"2. On to {TMAX:.0f} deg, and back")
    c.move(3.0, lambda t, i, n: dict(st=L.State(tilt=30.0 + (TMAX - 30.0) * t, **S0), cam=CAM_SIDE_HI, hide=near_cut, focus=foc, opacity=opac,
                                     readout=tilt_ro, text=f"{TMAX:.0f} deg takes {100 - L.p16_10_ext(TMAX):.0f} of the 100 mm. The exit stays on the hinge axis; "
                                                           "everything else turns up into the loop, away from the beaker.", save_as="p3" if preview else None))
    c.move(3.0, lambda t, i, n: dict(st=L.State(tilt=TMAX - (TMAX - TAU0) * t, **S0), cam=CAM_SIDE_HI, hide=near_cut, focus=foc, opacity=opac,
                                     readout=tilt_ro, text="", save_as="p4" if preview else None))
    c.hold(0.8)
    c.done()


# ---------------------------------------------------------------- 4. the wiring out the front
def wiring(preview=False):
    c = E.Clip("wiring_v10", TAG, 2, preview)
    foc = lambda p: p.group == "cable" or p.key in ("p16_100_body", "p16_100_rod", "ec10", "nema11", "solenoid", "side_plate_front", "p16_bracket10")  # noqa: E731
    lab = [("Bundle on the EC: NEMA 11\nand solenoid leads", ec((126.0, 24.0, -47.0)), "R"),
           ("Tied along the P16", part("cable10_p16", local=(14.0, 0.0, 80.0)), "R"),
           ("Grommet in the front side plate", part("grommet10", local=(0, 0, 0)), "L"),
           ("Outside: along the front plate,\ndown the -y post, back along\nthe base rail to the board", part("cable10_outside", local=(-46.0, -160.0, 300.0)), "L")]
    hide = lambda p: p.group in ("enclosure", "elec", "scale", "chamber") or (p.module >= 0 and p.module != 0 and p.M[1, 3] < SY - 30.0)  # noqa: E731
    c.chapter(1, "1. No wire crosses the carousel")
    c.move(5.0, lambda t, i, n: dict(st=L.State(**S0), cam=R.cam_lerp(CAM_FRONT, ((60.0, -40.0, 540.0), (-0.75, -0.9, 0.45), 820), t), hide=hide, focus=foc,
                                     labels=lab if t > 0.15 else (), opacity=lambda pl: opac(pl, {"side_plate_front": 0.55}),
                                     text="Sam: \"None of the wires can cross the carousel boundary, so they would have to come out the front.\" "
                                          "Inside the loop the bundle stays on the EC, then rides along the P16 to its base and out through a "
                                          "20 mm grommet in the front side plate. Outside, it runs along the plate to the -y side, clear of the "
                                          "bay window, down beside the post and back along the base rail.",
                                     save_as="w1" if preview else None))
    c.chapter(2, "2. It follows the EC through the tilt")
    c.move(4.0, lambda t, i, n: dict(st=L.State(tilt=TAU0 + (TMAX - TAU0) * math.sin(math.pi * t), **S0), cam=((60.0, -40.0, 540.0), (-0.75, -0.9, 0.45), 820),
                                     hide=hide, focus=foc, opacity=lambda pl: opac(pl, {"side_plate_front": 0.55}), readout=tilt_ro,
                                     text="The bundle bends only at the P16's two pins: a loop at the rod end and one at the base (drawn straight here).",
                                     save_as="w2" if preview else None))
    c.hold(0.8)
    c.done()


# ---------------------------------------------------------------- 5. the guide
def guide(preview=False):
    c = E.Clip("guide_v10", TAG, 1, preview)
    foc = lambda p: p.key in ("guide10", "ec10", "beam10")                                                              # noqa: E731
    lab = [("Conical shoe on the EC's arm", ec((115.0, 38.8, -33.0)), "R"), ("Funnel seat on a hanger\nfrom the station beam", part("guide10", local=(145.6, -34.0, 470.0)), "L"),
           ("Station beam (2020, front\nplate to back plate)", part("beam10", local=(0, 0, 180.0)), "L")]
    hide = lambda p: p.group in ("enclosure", "elec", "scale", "chamber") or (p.M[1, 3] < -75.0 and p.group not in ("station_ec", "station_act"))  # noqa: E731
    c.chapter(1, "The EC parks on a funnel seat, so it can't swing between modules")
    c.move(6.0, lambda t, i, n: dict(st=L.State(tilt=TAU0 + 12.0 * math.sin(math.pi * t), **S0), cam=CAM_GUIDE, hide=hide, focus=foc, labels=lab,
                                     opacity=lambda pl: opac(pl, {"ec10": 0.6}), readout=tilt_ro,
                                     text="Between doses the P16 is fully out and the EC hangs on its pin, so on its own it could swing. Its shoe "
                                          "parks in a 90 deg cone with v6's 45 deg funnel mouth (\"apply them wherever we move the guides\"); the "
                                          "first degrees of the pull lift it straight out, and coming back the funnel steers it in.",
                                     save_as="g1" if preview else None))
    c.hold(0.8)
    c.done()


# ---------------------------------------------------------------- 6. the drop
def drop(preview=False):
    c = E.Clip("drop_v10", TAG, 1, preview)
    foc = lambda p: p.group == "scale" or p.module == 0 or p.key.startswith("deck10")                                    # noqa: E731
    lab = [("Exit (on the hinge axis)", world((D[0], D[1], D[2])), "R"),
           ("Auger tube: 12.5 mm under the exit", sam(0, (60.0, 0.0, 12.5)), "R"),
           ("Front deck, 1.5 mm under the passing\ntubes; a 16 mm hole for the dose", part("deck10_front", local=(10.0, SY, 421.0)), "L"),
           ("Beaker's rim: 18 mm under the exit\n(v9: 32, v7: 154, single doser about 85)", world((PAN[0] - 19.0, D[1], RIM)), "L")]
    c.chapter(1, "Nothing of the station under the auger: the beaker 18 mm under the exit")
    c.move(4.0, lambda t, i, n: dict(st=L.State(**S0), cam=CAM_DROP, hide=near_cut, focus=foc, labels=lab, opacity=opac,
                                     text="With the EC and the P16 inside the loop, the lowest thing over the beaker is the auger's own tube, "
                                          "12.5 mm under the exit. The weighing chamber's front deck goes 1.5 mm under the passing tubes, and the "
                                          "beaker slides in under it with 1 mm to spare: 18 mm from the exit to the rim.",
                                     save_as="d1" if preview else None))
    c.move(1.5, lambda t, i, n: dict(st=L.State(tilt=TAU0 + (30.0 - TAU0) * t, **S0), cam=CAM_DROP, hide=near_cut, focus=foc, opacity=opac, readout=tilt_ro,
                                     text="Tilting turns everything up and back about the exit.", save_as="d2" if preview else None))
    _dose(c, 2.0, foc=foc, cam=CAM_DROP, text="18 mm to the rim, 67 mm to the beaker's floor (v9: 32 and 80).", save="d3" if preview else None)
    c.hold(1.0)
    c.done()


# ---------------------------------------------------------------- 7. the tilt range: where it stops
LIMIT_AT = 70.0                      # the first pose the clash check fails (check_interference --tilt10: 65 clear, 70 not)
LIMIT_TEXT = "the front of the EC (the door ramp's web) reaches the front chain's A-1 link"


def limit(preview=False):
    c = E.Clip("limit_v10", TAG, 2, preview)
    acc = lambda p: (0.92, 0.22, 0.12) if p.key in ("ec10",) else None                                                  # noqa: E731
    foc = lambda p: p.group in ("station_act", "station_ec") or p.module == 0 or p.key in ("chain_a1", "chain_inner", "chain_outer", "sprocket_32", "carriage")  # noqa: E731
    cam = ((30.0, SY, 470.0), (0.0, -1.0, 0.10), 300)
    c.chapter(1, f"1. 4 to {TMAX:.0f} deg: clear")
    c.move(4.0, lambda t, i, n: dict(st=L.State(tilt=TAU0 + (TMAX - TAU0) * t, **S0), cam=cam, hide=near_cut, focus=foc, opacity=opac, readout=tilt_ro,
                                     text=f"On the plate's side, everything near the hinge swings forward and down as the module tilts. v10 keeps "
                                          f"that region shallow (the door cable's guide, the door ramp, the rail), so the station is clear from 4 to "
                                          f"{TMAX:.0f} deg in the clash check.", save_as="l1" if preview else None))
    c.chapter(2, f"2. Past {TMAX:.0f} deg: {LIMIT_TEXT}")
    c.move(2.5, lambda t, i, n: dict(st=L.State(tilt=TMAX + (LIMIT_AT - TMAX) * t, **S0), cam=cam, hide=near_cut, focus=foc, opacity=opac, readout=tilt_ro,
                                     accent=acc if t > 0.6 else None,
                                     text=f"At {LIMIT_AT:.0f} deg {LIMIT_TEXT} (red). 90 deg would need the EC on the auger's side again (v7-v9), "
                                          "which is what put it under the auger.", save_as="l2" if preview else None))
    c.hold(1.2)
    c.done()


CLIPS = {"overview": overview, "rail": rail, "pull": pull, "wiring": wiring, "guide": guide, "drop": drop, "limit": limit}

if __name__ == "__main__":
    pv = "--preview" in sys.argv
    for name in [a for a in sys.argv[1:] if not a.startswith("--")] or list(CLIPS):
        CLIPS[name](pv)
