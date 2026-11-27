"""v12's clips (Sterling, PR #185, 2026-11-27: the spring-loaded pinion v11's gear study proposed). Every frame is the v12 CAD
(layout.placements) in the state described: the chain, the P16's two pins and the cradle's turn about its pivot (State.cradle_lift).
The cradle's lift during an index is drawn to the simulations' numbers (sim/README.md), not simulated here: the MuJoCo clips are
sim/viz12.py's.

    xvfb-run -a python explain12.py cradle|seats|overview [--preview]
    -> renders/v12/<name>_v12.{mp4,gif}
"""
from __future__ import annotations

import math
import sys

import numpy as np

import explain as E
import layout as L
import parts11 as P11
import render as R
from params import (CRADLE12_LIFT, CRADLE12_PIV, CRADLE12_STOP, HALL12_LIFT_MM, MODULE_LINKS, P, RUN_DIRECTION, SPRING12_F_STOP,
                    SPRING12_K, SPRING12_X, SETSCREW12_XY, HALL12_XYZ, SHOE11_Y, SHOE12_Y2)

E.OUT = R.OUT / "v12"
H = L.HINGE_STATION
SY = L.STATION_Y
part, sam, world = E.part, E.sam, E.world
TAG = "chain carousel v12 · PR #185 · 2026-11-27"
S0 = dict(enclosure=False)
FPS = E.FPS
HX, HZ = float(H[0]), float(H[2])
PY, PZ = CRADLE12_PIV


def ec(local):
    return part("ec12", local=local)


def opac(pl, extra=None):
    o = {}
    for k, p in R.keyed(pl):
        if p.key.startswith(("panel_", "hatch_", "bal11_glass", "bal11_door", "bal11_lid")):
            o[k] = 0.18
        if extra and p.key in extra:
            o[k] = extra[p.key]
    return o


def near_cut(p) -> bool:
    """What stands between a camera on the world -y side (Sam +y) and the station: the enclosure, the -y frame and the first beam and
    guide, the -y carriages and modules. The station's own parts and the P16 stay."""
    if p.group in ("enclosure", "elec"):
        return True
    if p.key in ("m5x35_shcs",):
        return True
    if p.group in ("station_act", "station_ec", "cable") or p.module == 0 or p.key in ("p16_bracket11", "bar11", "guide12", "guide11"):
        return False
    if p.key == "beam10":
        return p.M[1, 3] < 0
    if p.group == "scale":
        return True
    y = p.M[1, 3]
    if p.group == "station":
        return y < SY - 60.0
    if p.key in ("shaft", "shaft_drive", "sprocket_32", "flange_bearing", "bolt_m6x25", "nut_m6", "tensioner_block", "m5x30_shcs", "m5x10_shcs", "nut_m5"):
        return y < -20.0
    if p.key in ("rung", "ext_x", "ext_post", "corner_bracket"):
        return y < SY - 100.0
    return y < SY - 35.0


def close_cut(p) -> bool:
    if near_cut(p):
        return True
    if p.group in ("station_act",):
        return True
    if p.key in ("side_plate_front", "side_plate_back", "latch_rail11", "hold_down", "hall_switch", "magnet", "insert_m5", "m5x16_shcs"):
        return True
    if p.module >= 0 and p.group in ("modules", "carriages"):
        y, z = p.M[1, 3], p.M[2, 3]
        return abs(y - SY) > 1.3 * MODULE_LINKS * P or z > 430.0
    return False


def incoming(t: float) -> float:
    return -RUN_DIRECTION * MODULE_LINKS * (1.0 - t)


def lift_ro(st: L.State) -> str:
    lf = st.cradle_lift
    f = SPRING12_F_STOP + SPRING12_K * (lf + CRADLE12_STOP)
    sw = "LIFTED" if lf > HALL12_LIFT_MM else "seated"
    where = "on its stop" if lf <= -CRADLE12_STOP + 1e-6 else ("in tight mesh" if abs(lf) < 0.05 else f"{lf:+.1f} mm over tight mesh")
    return f"pinion {where}\nspring {f:3.1f} N   switch: {sw}"


def off_of(st: L.State) -> float:
    k = L.carriage_at(L.CARRIAGE_LINK0, round(st.shift), tol=0.6)
    return L.module_offset(k, st) if k >= 0 else 99.0


TIP = math.sqrt(36.0 ** 2 - (34.0 - CRADLE12_STOP) ** 2)     # 12.9 mm: the gear's tips first touch the pinion's on its stop


def stub_lift(off: float) -> float:
    """The pinion's lift as a gear arrives tip-on-tip (the model's stub case): on its stop until the tips touch, then pushed up to
    the 2.0 mm of a tip on a tip as the gear comes in."""
    a = abs(off)
    if a >= TIP:
        return -CRADLE12_STOP
    return -CRADLE12_STOP + (2.0 + CRADLE12_STOP) * (1.0 - a / TIP) ** 0.6


CAM_CR = ((HX + 108.0, SY - 2.0, HZ + 42.0), (0.30, -0.80, 0.52), 215)     # the cradle from the arm's side (Sam +y), above and behind
CAM_CR2 = ((HX + 100.0, SY - 2.0, HZ + 40.0), (-0.55, -0.70, 0.45), 205)   # ... from in front
CAM_SEAT = ((HX + 139.0, SY, HZ + 28.0), (0.30, 0.15, 0.94), 250)          # both shoes and seats, from above and behind (the beams see-through)
CAM_SEAT2 = ((HX + 130.0, SY, HZ + 35.0), (0.42, -0.38, 0.82), 290)
CAM_SIDE = ((HX + 10.0, SY, HZ + 85.0), (0.0, -1.0, 0.08), 760)
CAM_SIDE_HI = ((HX - 5.0, SY, HZ + 120.0), (0.0, -1.0, 0.06), 900)

FOC_CR = ("cradle12", "nema11_v12", "pinion24", "set_screw_m3x6", "hall_switch12", "hall_magnet12", "pivot_dowel12", "insert_m3_short")


def foc_cr(p):
    return p.key in FOC_CR or p.key.startswith("spring12_") or (p.module == 0 and p.key in ("auger",))


def lab_cr():
    return [("Pivot: two 3 x 12 mm dowels, level with\nthe pinion, on the side the gears come from", ec((85.0, PY, PZ)), "L"),
            ("Spring over the motor: 1 N/mm,\n6 N at the stop", world_ec((SPRING12_X, 0.0, -58.0)), "R"),
            ("Stop: M3 set screw through the\ncradle's lug onto the EC's arm", part("set_screw_m3x6", local=(0.0, 0.0, -3.0)), "R"),
            ("Hall switch on the cradle;\nits magnet in the EC", part("hall_switch12", local=(0.0, 0.0, 0.0)), "R"),
            ("24T pinion on the NEMA 11", part("pinion24", local=(0.0, 0.0, 5.0)), "L")]


def world_ec(local):
    return ec(local)


def cradle(preview=False):
    c = E.Clip("cradle_v12", TAG, 4, preview)
    op = lambda pl: opac(pl, {"ec12": 0.32})                                                                          # noqa: E731
    c.chapter(1, "1. The NEMA 11 and its pinion ride on a spring-loaded cradle")
    c.move(5.0, lambda t, i, n: dict(st=L.State(cradle_lift=0.0, **S0), cam=R.cam_lerp(CAM_CR, CAM_CR2, 0.5 - 0.5 * math.cos(math.pi * t)), hide=close_cut,
                                     focus=foc_cr, opacity=op, labels=lab_cr() if t > 0.1 else (), readout=lift_ro,
                                     text="v11 bolted the motor to the EC, so a gear tooth landing on a pinion tooth had nowhere to go and the index "
                                          "jammed (about 1 in 4 in the model). v12 hangs the motor and pinion on a printed cradle that pivots on two "
                                          "dowels; a 1 N/mm spring presses the pinion into the gear, and a set screw stops it 0.4 mm past tight mesh.",
                                     save_as="c1" if preview else None))
    c.chapter(2, "2. Between modules the cradle rests on its stop")
    c.move(3.0, lambda t, i, n: dict(st=L.State(shift=RUN_DIRECTION * MODULE_LINKS * 0.5 * t, cradle_lift=-CRADLE12_STOP * min(1.0, 3 * t), **S0),
                                     cam=CAM_CR2, hide=close_cut, focus=foc_cr, opacity=op, readout=lift_ro,
                                     text="As the module leaves, the spring pushes the cradle down 0.4 mm onto the set screw, whose tip lands on the "
                                          "EC's arm. The NEMA 11 still clears the passing plates by 1.6 mm.", save_as="c2" if preview else None))

    def fr3(t, i, n):
        s = incoming(0.5 + 0.5 * t)
        st0 = L.State(shift=s, **S0)
        lf = stub_lift(off_of(st0))
        return dict(st=L.State(shift=s, cradle_lift=lf, **S0), cam=CAM_CR2, hide=close_cut, focus=foc_cr, opacity=op, readout=lift_ro,
                    text="The worst arrival: a gear tooth lands on a pinion tooth's tip. The pinion can't turn out of the way, so the "
                         "gear pushes it up 2 mm against the spring (8.4 N) instead of jamming the chain, and the hall switch slides "
                         "under its magnet: \"lifted\".", save_as="c3" if preview else None)
    c.chapter(3, "3. A tooth lands on a tooth: the cradle lifts instead of jamming")
    c.move(4.0, fr3, eased=False)

    def fr4(t, i, n):
        lf = 2.0 if t < 0.35 else (2.0 * max(0.0, 1.0 - (t - 0.35) / 0.25))
        spin = -0.17 * math.sin(math.pi * min(1.0, t / 0.7))
        return dict(st=L.State(cradle_lift=lf, spin=spin, **S0), cam=CAM_CR2, hide=close_cut, focus=foc_cr, opacity=op, readout=lift_ro,
                    text="After every index the driver turns the pinion slowly forward and back (0.25 rev/s, 0.2 s each way). A pinion "
                         "resting on the gear's tips drops into the next gap and the switch reads \"seated\". If it still reads \"lifted\", "
                         "a second try runs the other way round.", save_as="c4" if preview else None)
    c.chapter(4, "4. The seek: forward, then back; the pinion drops into the gap")
    c.move(4.0, fr4, eased=False)
    c.hold(1.0)
    c.done()


def seats(preview=False):
    c = E.Clip("seats_v12", TAG, 3, preview)
    foc = lambda p: p.key in ("ec12", "guide11", "guide12", "beam10") or p.key in FOC_CR or p.key.startswith("spring12_") or p.module == 0  # noqa: E731
    keep = ("station_ec", "station")

    def hide(p):
        if p.group in keep or p.key in ("beam10", "guide11", "guide12"):
            return p.key in ("latch_rail11", "side_tab", "side_tab_m", "m5x12_bhcs", "p16_bracket11", "grommet10", "clevis_screw")
        if p.module == 0 and p.group in ("modules", "carriages"):
            return False
        return True
    lab = [("Guide 1 (v11's), on the station beam", part("guide11", local=None), "L"),
           ("Guide 2 (new): the far side's seat,\non a second beam across the loop", part("guide12", local=None), "R"),
           ("Shoe 1 (v11's)", ec((139.0, SHOE11_Y, -28.0)), "L"),
           ("Shoe 2 (new), on the far side\nof the module", ec((139.0, SHOE12_Y2, -28.0)), "R")]
    c.chapter(1, "1. A second seat on the far side of the module")
    c.move(4.5, lambda t, i, n: dict(st=L.State(**S0), cam=R.cam_lerp(CAM_SEAT, CAM_SEAT2, 0.5 - 0.5 * math.cos(math.pi * t)), hide=hide, focus=foc,
                                     labels=lab if t > 0.1 else (), opacity=lambda pl: opac(pl, {"ec12": 0.8, "beam10": 0.22}),
                                     text="v11's EC rested on the P16's pin and one shoe, both on the P16's side, so it could roll toward the gear "
                                          "on the clevis's play. v12 adds a second shoe on the far side, in a second funnel seat on a second 2020 "
                                          "beam: between modules the EC sits on both (1.0 and 0.8 N in the model), level.",
                                     save_as="s1" if preview else None))
    c.chapter(2, "2. The P16 pulls: both shoes lift out of their seats")
    c.move(3.0, lambda t, i, n: dict(st=L.State(tilt=30.0 * t, **S0), cam=CAM_SEAT2, hide=hide, focus=foc, opacity=lambda pl: opac(pl, {"ec12": 0.8, "beam10": 0.22}),
                                     readout=lambda st: f"tilt {st.tilt:4.1f} deg",
                                     text="With a module meshed, the spring's 6 N pushes the EC up off both seats (its weight is 3 N) and the rail's "
                                          "lips hold it against the module's T instead; the P16 then lifts it clear as it pulls.",
                                     save_as="s2" if preview else None))
    c.chapter(3, "3. Back down: the funnels steer both shoes home")
    c.move(3.0, lambda t, i, n: dict(st=L.State(tilt=30.0 * (1.0 - t), **S0), cam=CAM_SEAT2, hide=hide, focus=foc, opacity=lambda pl: opac(pl, {"ec12": 0.8, "beam10": 0.22}),
                                     readout=lambda st: f"tilt {st.tilt:4.1f} deg", text="", save_as="s3" if preview else None))
    c.hold(1.0)
    c.done()


def overview(preview=False):
    c = E.Clip("overview_v12", TAG, 3, preview)
    camA = ((110, 0, 400), (-1.0, -1.1, 0.5), 1800)
    camB = ((110, 0, 400), (-1.15, 0.75, 0.42), 1800)
    lab = [("EC v12: the NEMA 11 and its pinion\non a spring-loaded cradle", ec((110.0, 0.0, -45.0)), "R"),
           ("Second guide and beam (new)", part("guide12"), "L"),
           ("P16-150 through the front side plate", part("actuator_body", local=(0, 0, 40.0)), "R")]
    c.chapter(1, "Chain carousel v12: v11 with a spring-loaded pinion")
    c.move(4.5, lambda t, i, n: dict(st=L.State(), cam=R.cam_lerp(camA, camB, t), hide=lambda p: p.group == "elec", labels=lab if t > 0.2 else (),
                                     opacity=lambda pl: opac(pl, {"panel_side": 0.1, "panel_side_hatch": 0.1, "panel_top": 0.08}),
                                     text="Everything is v11's except the station's pinion mount: the NEMA 11 and its 24T pinion ride on a cradle "
                                          "that pivots in the EC, pressed into the auger's gear by a 1 N/mm spring, with a set-screw stop and a hall "
                                          "switch; and the EC rests on two guide seats, one each side of the module.",
                                     save_as="o1" if preview else None))

    def fr2(t, i, n):
        s = incoming(t)
        st0 = L.State(shift=s, **S0)
        return dict(st=L.State(shift=s, cradle_lift=min(0.0, stub_lift(off_of(st0))) if t < 0.92 else 0.0, **S0),
                    cam=R.cam_lerp(camB, CAM_SIDE, min(1.0, 2 * t)), hide=near_cut if t > 0.4 else (lambda p: p.group == "elec"), opacity=opac,
                    readout=lift_ro, text="An index: the next module's T slides into the EC's rail and its gear into mesh, the pinion "
                                          "free on its spring; then the seek and the hall switch confirm it's in.", save_as="o2" if preview else None)
    c.chapter(2, "Index, seek, check the switch")
    c.move(2.8, fr2, eased=False)
    c.chapter(3, "Pull up, dose, 90 deg, back")
    c.move(2.0, lambda t, i, n: dict(st=L.State(tilt=30.0 * t, **S0), cam=R.cam_lerp(CAM_SIDE, CAM_SIDE_HI, t), hide=near_cut, opacity=opac,
                                     readout=lambda st: f"tilt {st.tilt:4.1f} deg", text="The P16 retracts and pulls the EC, the cradle and the module up "
                                     "about the hinge; the spring keeps the pinion in the gear at every angle.", save_as="o3" if preview else None))
    c.move(2.2, lambda t, i, n: dict(st=L.State(tilt=30.0 + 60.0 * t, spin=2 * math.pi * t, **S0), cam=CAM_SIDE_HI, hide=near_cut, opacity=opac,
                                     readout=lambda st: f"tilt {st.tilt:4.1f} deg", text="", save_as="o4" if preview else None))
    c.move(2.2, lambda t, i, n: dict(st=L.State(tilt=90.0 * (1 - t), **S0), cam=R.cam_lerp(CAM_SIDE_HI, CAM_SIDE, t), hide=near_cut, opacity=opac,
                                     readout=lambda st: f"tilt {st.tilt:4.1f} deg", text="Back down: the module onto its carriage, the EC's two shoes into "
                                     "their two seats.", save_as="o5" if preview else None))
    c.hold(1.0)
    c.done()


CLIPS = {"cradle": cradle, "seats": seats, "overview": overview}

if __name__ == "__main__":
    pv = "--preview" in sys.argv
    for name in [a for a in sys.argv[1:] if not a.startswith("--")] or list(CLIPS):
        CLIPS[name](pv)
