"""Pairwise interference checks of the v12 rig (OCC booleans), in frame coordinates. v12 adds --cradle (the spring-loaded pinion's
cradle over its travel). The rest of this docstring is older:

    python check_interference.py            # home pose (station docked), every pair
    python check_interference.py --sweep    # chain indexed one module (8 pitches) in half-link steps the way it runs;
                                            #   all 13 carriages together pass every point of the loop
    python check_interference.py --tilt     # station: electronics carriage rising (approach), then module +
                                            #   carriage + actuator tilting to the hinge's travel limit
    python check_interference.py --latch    # v11: the station's latch cam against everything while carriage 1 passes it (+-3 links), then
                                            #   with module 1 pulled up to 10, 20 ... 90 deg; each follower's sliver on the cam
    python check_interference.py --swap     # loading position (module 4 at home, side hatch open): the auger pulled straight off its
                                            #   plate through the hatch, then a carriage's screws out, slid 10 mm, lifted out
    python check_interference.py --scale    # v5: the HR-202i (and, as a second check, the lab's HR-100A) at the dose point, against
                                            #   everything; the station parked, then docked and tilted to 30 and 50 deg

A pair is reported when the two solids share more than 0.5 mm^3. Pairs that touch by design (pin in its bore,
screw in its insert or nut, bearing on its shaft, gear mesh) are skipped by part key in SKIP; anything listed is a
real clash. v3 has no snap hooks (the latch replaced them), so nothing is logged as a by-design flex any more. v5: the HR-202i
stands at the dose point in every check (home, tilt, sweep), its top door open while the station tilts; --scale also tries
the HR-100A there. The frame pitch is 0, so the checks run in frame coordinates.
Results go to checks/*.json.
"""
from __future__ import annotations

import itertools
import json
import sys
import time
from functools import lru_cache
from pathlib import Path

import cadquery as cq

import layout as L
from params import PARK_DROP7 as PARK_DROP, HINGE_W, HOOK_SLIDE, MODULE_LINKS, RUN_DIRECTION, SAM_DROP, SCREW_OUT, TILT_MAX_FRAME, HATCH_OPEN_DEG

OUT = Path(__file__).resolve().parent / "checks"

SKIP = {("auger", "auger_cap"), ("auger", "sam_mounting_plate"), ("auger", "pinion"),
        ("clevis_screw", "clevis_bracket"), ("clevis_screw", "actuator_body"), ("clevis_screw", "nut_m3_clevis"),
        ("yoke_pin", "uyoke_base"), ("yoke_pin", "actuator_rod"), ("yoke_pin", "uyoke_arm"),
        # the 15T drive sprockets mesh with the drive chain: 0.3-0.7 mm slivers where the simplified tooth form meets a link as
        # it wraps on or off (0.50 mm3 with Nitro's real plate height); only the drive chain reaches these sprockets
        ("sprocket_15_motor", "chain_inner"), ("sprocket_15_motor", "chain_outer"), ("sprocket_15_shaft", "chain_inner"),
        ("sprocket_15_shaft", "chain_outer"),
        ("carriage", "nut_m3"), ("carriage", "m3x12_bhcs"), ("m3x12_bhcs", "nut_m3"), ("chain_a1", "m3x12_bhcs"),
        ("carriage", "clevis_pin"), ("clevis_pin", "sam_mounting_plate"), ("clevis_pin", "eclip"),
        ("armature_tab", "m3x6_fhcs"), ("insert_m3", "m3x6_fhcs"), ("insert_m3", "sam_mounting_plate"), ("m3x6_fhcs", "sam_mounting_plate"),
        ("m5x12_bhcs", "tnut_m5"), ("ext_post", "tnut_m5"), ("ext_x", "tnut_m5"), ("ext_post", "m5x12_bhcs"),
        ("bolt_m6x25", "nut_m6"), ("m5x25_shcs", "nut_m5"), ("nema34", "sprocket_15_motor"),
        ("nema34", "nut_m5"), ("m5x30_shcs", "nut_m5"), ("m5x10_shcs", "side_plate_front"), ("m5x10_shcs", "side_plate_back"),
        ("hold_down", "insert_m5"), ("insert_m5", "m5x16_shcs"), ("foot", "tnut_m5"), ("ext_x", "foot"), ("foot", "riser"),
        ("shaft", "sprocket_32"), ("shaft_drive", "sprocket_32"), ("shaft", "flange_bearing"), ("shaft_drive", "flange_bearing"),
        ("shaft_drive", "sprocket_15_shaft"),
        ("nema11", "sam_electronics_carriage"), ("solenoid", "sam_electronics_carriage"), ("pinion", "sam_electronics_carriage"),
        ("nema11", "pinion"), ("actuator_body", "actuator_rod"), ("actuator_body", "clevis_bracket"), ("actuator_rod", "station_yoke"),
        ("sam_electronics_carriage", "station_yoke"), ("magnet_bracket", "sam_electronics_carriage"), ("dock_magnet", "magnet_bracket"),
        ("magnet_bracket", "nema11"), ("vial", "vial_funnel"), ("vial", "vial_cup"), ("load_cell", "vial_cup"), ("level_wedge", "load_cell"),
        ("ext_vial_post", "level_wedge"), ("ext_vial_post", "ext_x"), ("ext_fork_post", "ext_y"), ("fork", "fork_arm"), ("ext_fork_post", "fork_arm"),
        ("clevis_bracket", "ext_y"), ("corner_bracket", "ext_y"), ("corner_bracket", "ext_x"), ("corner_bracket", "ext_post"),
        ("loc_pin", "sam_electronics_carriage"), ("loc_pin", "sam_mounting_plate"),
        ("sam_electronics_carriage", "stub_pin"), ("pin_boss", "stub_pin"), ("eclip_stub", "stub_pin"), ("actuator_rod", "uyoke_base"),
        ("uyoke_arm", "uyoke_base"), ("uyoke_arm", "yoke_stop"), ("pin_boss", "sam_electronics_carriage"),
        ("uyoke_arm", "yoke_stop_m"), ("pin_boss_m", "stub_pin"), ("pin_boss_m", "sam_electronics_carriage"),
        # ---- v3: pressed, bonded or seated by design
        ("kc_ball", "sam_mounting_plate"), ("kc_ball", "sam_electronics_carriage"), ("kc_ball", "vee_dowel"), ("kc_ball", "armature_v3"),
        ("kc_ball", "cradle"), ("kc_ball", "flat_pad"), ("vee_dowel", "sam_electronics_carriage"), ("vee_dowel", "cradle"),
        ("flat_pad", "cradle"), ("kc_magnet", "sam_electronics_carriage"), ("dock_magnet", "sam_electronics_carriage"),
        ("armature_v3", "m3x6_fhcs"), ("armature_v3", "sam_mounting_plate"),
        ("door_shutter", "door_housing"), ("door_spring", "door_housing"), ("door_spring", "door_shutter"),
        ("door_spring_open", "door_housing"), ("door_spring_open", "door_shutter"), ("door_shutter", "sam_electronics_carriage"),
        ("m2x8_shcs", "door_housing"), ("m2x8_shcs", "sam_mounting_plate"),
        ("latch_bolt", "carriage"), ("latch_follower", "latch_bolt"), ("latch_follower", "carriage"), ("latch_spring", "carriage"),
        ("latch_spring", "latch_bolt"), ("latch_follower", "latch_rail"),
        ("clevis_screw", "sam_electronics_carriage"), ("clevis_screw", "actuator_rod"), ("nut_m3_clevis", "sam_electronics_carriage"),
        ("ext_cradle_post", "cradle"), ("ext_cradle_post", "ext_y"), ("ext_latch_post", "latch_rail"), ("ext_latch_post", "ext_y"),
        ("side_tab", "insert_m5"), ("side_tab_m", "insert_m5"),
        ("standoff", "ext_post"), ("standoff", "ext_x"), ("standoff", "ext_y"), ("standoff_back", "ext_post"),
        ("standoff", "panel_side"), ("standoff", "panel_side_hatch"), ("standoff", "panel_front_hatch"), ("standoff_back", "panel_back"),
        ("hinge_leaf", "panel_side_hatch"), ("hinge_leaf", "panel_front_hatch"), ("hinge_leaf", "hatch_front"), ("hinge_leaf", "hatch_side"),
        ("catch", "panel_side_hatch"), ("catch", "panel_front_hatch"), ("panel_top", "panel_side"), ("panel_top", "panel_side_hatch"),
        ("panel_top", "panel_front_hatch"), ("panel_top", "panel_back"), ("panel_front_hatch", "panel_side"),
        ("panel_front_hatch", "panel_side_hatch"), ("panel_back", "panel_side"), ("panel_back", "panel_side_hatch"),
        ("hr100a_body", "hr100a_glass"), ("hr100a_body", "hr100a_pan"), ("beaker", "hr100a_pan"), ("hinge_leaf", "hinge_leaf"),
        ("side_tab", "m5x8_shcs"), ("side_tab_m", "m5x8_shcs"), ("m5x8_shcs", "side_plate_front"), ("m5x8_shcs", "side_plate_back"),
        ("flat_pad_v4", "sam_mounting_plate"), ("flat_pad_v4", "kc_ball"),
        ("catch", "hatch_front"), ("catch", "hatch_side"), ("ec_pin_screw", "sam_electronics_carriage"), ("ec_pin_screw", "actuator_rod"),
        ("ec_pin_screw", "nut_m3_clevis"), ("ec_pin_screw", "ptfe_washer"), ("actuator_rod", "ptfe_washer"), ("ptfe_washer", "sam_electronics_carriage"),
        # ---- v5: the lift bar in the EC's saddles and the end blocks' clamps; the rod ends' tabs between the end blocks' cheeks
        # on their shoulder screws; shelves, guides, posts and beams screwed to each other; the balance's own parts; the
        # riser on the pan and the beaker in the riser's cup
        ("lift_bar", "sam_electronics_carriage"), ("bar_end", "lift_bar"), ("bar_end", "clevis_screw"), ("bar_end", "nut_m3_clevis"), ("actuator_rod", "bar_end"),
        ("clevis_bracket", "p16_shelf"), ("ext_station_post", "p16_shelf"), ("ext_station_post", "guide_block"), ("corner_bracket", "ext_station_post"),
        ("corner_bracket", "ext_latch_post5"), ("corner_bracket", "ext_latch_beam"), ("ext_latch_beam", "ext_latch_post5"), ("ext_latch_post5", "ext_x"),
        ("ext_station_post", "ext_x"), ("ext_latch_beam", "latch_rail"),
        ("hr202i_body", "hr202i_display"), ("hr202i_body", "hr202i_front_glass"), ("hr202i_body", "hr202i_pan"), ("hr202i_body", "hr202i_door_left"),
        ("hr202i_body", "hr202i_door_right"), ("hr202i_body", "hr202i_top_door"), ("hr202i_door_left", "hr202i_front_glass"),
        ("hr202i_door_right", "hr202i_front_glass"), ("hr202i_front_glass", "hr202i_top_door"), ("hr202i_door_left", "hr202i_top_door"),
        ("hr202i_door_right", "hr202i_top_door"), ("beaker_riser", "hr202i_pan"), ("beaker", "beaker_riser"), ("beaker", "hr100a_pan"),
        # ---- v6: the lift frame's bars in the end blocks' clamps and the EC's hooks; the rod ends' tabs between the end blocks'
        # cheeks; the shoes' noses on their seats (parked); shelves, guides, rungs and brackets screwed together; the tilt P16
        # on its bracket and its rod end on the EC's tilt arm; magnets pressed into the plate; the latch cam's foot on the back plate
        ("lift_bar", "lift_end"), ("lift_bar", "sam_electronics_carriage"), ("actuator_rod", "lift_end"), ("bar_end", "p16l_rod"), ("p16l_rod", "lift_end"),
        ("clevis_screw", "lift_end"), ("lift_end", "nut_m3_clevis"), ("p16l_body", "p16l_rod"), ("clevis_bracket", "p16l_body"),
        ("clevis_screw", "p16l_body"), ("clevis_screw", "p16l_rod"), ("clevis_bracket", "lift_shelf"), ("lift_shelf", "rung"),
        ("guide_cone", "rung"), ("guide_vee", "rung"), ("corner_bracket", "rung"), ("ext_post", "rung"), ("guide_cone", "lift_end"),
        ("guide_vee", "lift_end"), ("side_plate_back", "tilt_bracket"), ("clevis_screw", "tilt_bracket"), ("actuator_body", "tilt_bracket"),
        ("nut_m3_clevis", "tilt_bracket"), ("kc6_magnet", "sam_mounting_plate"), ("latch_rail", "side_plate_back"), ("latch_rail", "m5x12_bhcs"),
        ("m5x12_bhcs", "side_plate_back"), ("m5x12_bhcs", "tilt_bracket"), ("actuator_rod", "nut_m3_clevis"), ("kc6_magnet", "kc_magnet"),
        # ---- v7: the P16's rod end in the EC's tail clevis on its 4 x 20 shoulder screw (PTFE washers either side); the clevis,
        # the guides and the brackets screwed to the cross bars; the latch spring at its three lengths; the balance's own parts
        ("actuator_rod", "sam_electronics_carriage"), ("actuator_rod", "ec_pin_screw"), ("cross7", "clevis_bracket"), ("cross7", "guide7_cone"),
        ("cross7", "guide7_vee"), ("corner_bracket", "cross7"), ("cross7", "rung"), ("guide7_cone", "m5x12_bhcs"), ("guide7_vee", "m5x12_bhcs"),
        ("cross7", "m5x12_bhcs"), ("latch_spring_cam", "carriage"), ("latch_spring_cam", "latch_bolt"), ("latch_spring_hand", "carriage"),
        ("latch_spring_hand", "latch_bolt"), ("bal7_base", "bal7_frame"), ("bal7_base", "bal7_glass"), ("bal7_base", "bal7_pan"),
        ("bal7_base", "bal7_display"), ("bal7_base", "bal7_door_left"), ("bal7_base", "bal7_door_right"), ("bal7_frame", "bal7_glass"),
        ("bal7_frame", "bal7_door_left"), ("bal7_frame", "bal7_door_right"), ("bal7_frame", "bal7_lid"), ("bal7_glass", "bal7_lid"),
        ("bal7_door_left", "bal7_lid"), ("bal7_door_right", "bal7_lid"), ("bal7_glass", "bal7_door_left"), ("bal7_glass", "bal7_door_right"),
        ("bal7_frame", "bal7_pan"), ("beaker_riser", "bal7_pan"), ("actuator_body", "nut_m3_clevis"),
        # the plate's printed dome B rests on the EC's two vee dowels (line contacts): OCC's boolean of a sphere tangent to a cylinder
        # sometimes returns the whole dowel (62 mm3 at 30 deg, 0 at 0-5 deg for the same relative position), so the pair is skipped
        ("sam_mounting_plate", "vee_dowel"),
        # ---- v9: the balance's own parts, its feet on the block and the beaker on its pan; the bay window's and the weighing chamber's
        # acrylic sheets butted and cemented to each other and to the front panel; the bay door's hinges and turn button
        ("bal9_base", "bal9_pan"), ("bal9_base", "bal9_display"), ("bal9_base", "block9"), ("bal9_pan", "beaker"),
        ("bay9_front", "bay9_side_p"), ("bay9_front", "bay9_side_m"), ("bay9_front", "bay9_top"), ("bay9_top", "bay9_side_p"), ("bay9_top", "bay9_side_m"),
        ("bay9_side_p", "panel_front_bay"), ("bay9_side_m", "panel_front_bay"), ("bay9_top", "panel_front_bay"), ("bay9_door", "bay9_front"),
        ("hinge_leaf", "bay9_front"), ("hinge_leaf", "bay9_door"), ("catch", "bay9_front"), ("catch", "bay9_door"),
        ("deck9", "panel_front_bay"), ("deck9", "baffle9_side_p"), ("deck9", "baffle9_side_m"), ("deck9", "baffle9_back"),
        ("baffle9_side_p", "panel_front_bay"), ("baffle9_side_m", "panel_front_bay"), ("baffle9_side_p", "baffle9_back"), ("baffle9_side_m", "baffle9_back"),
        ("standoff", "panel_front_bay"), ("panel_top", "panel_front_bay"), ("panel_front_bay", "panel_side"), ("panel_front_bay", "panel_side_hatch"),
        # ---- v10: the T-bracket screwed to its plate and riding on the rail's lips; the door's tab on the EC's ramp; the NEMA 11, the
        # pinion and the solenoid in the EC; the P16-100 on its bracket and its rod end in the arm's clevis on their shoulder screws; the
        # guide shoe parked in its seat; the beam screwed through both side plates and carrying the guide's hanger; the grommet in the
        # front plate; the chamber's and the bay's acrylic cemented to each other and the front panel. The cable bundles are tied to
        # what they run along (the EC, the P16, the bracket, the plate, the frame) and flex; their pairs with those are skipped
        ("t_bracket", "sam_mounting_plate"), ("ec10", "t_bracket"), ("door_shutter", "ec10"), ("ec10", "nema11"), ("ec10", "pinion"), ("ec10", "solenoid"),
        ("p16_100_body", "p16_100_rod"), ("p16_100_body", "p16_bracket10"), ("clevis_screw", "p16_bracket10"), ("clevis_screw", "p16_100_body"),
        ("nut_m3_clevis", "p16_bracket10"), ("nut_m3_clevis", "p16_100_body"), ("ec10", "p16_100_rod"), ("ec10", "ec_pin_screw"), ("ec_pin_screw", "p16_100_rod"),
        ("ec10", "nut_m3_clevis"), ("guide10", "beam10"), ("ec10", "guide10"), ("beam10", "side_plate_front"), ("beam10", "side_plate_back"),
        ("beam10", "m5x16_shcs"), ("m5x16_shcs", "side_plate_front"), ("m5x16_shcs", "side_plate_back"), ("grommet10", "side_plate_front"),
        ("p16_bracket10", "side_plate_front"), ("solenoid", "sam_mounting_plate"),
        ("door_guide10", "door_housing"), ("door_guide10", "sam_mounting_plate"), ("door_guide10", "door_shutter"), ("door_guide10", "door_tab10"),
        ("door_tab10", "ec10"), ("door_spring", "door_guide10"), ("door_spring_open", "door_guide10"),
        ("cable10_ec", "ec10"), ("cable10_ec", "nema11"), ("cable10_ec", "p16_100_rod"), ("cable10_ec", "ec_pin_screw"), ("cable10_ec", "nut_m3_clevis"),
        ("cable10_ec", "cable10_p16"), ("cable10_ec", "p16_100_body"), ("cable10_p16", "p16_100_body"), ("cable10_p16", "p16_100_rod"), ("cable10_p16", "cable10_inside"),
        ("cable10_inside", "p16_100_body"), ("cable10_inside", "p16_bracket10"), ("cable10_inside", "grommet10"), ("cable10_inside", "side_plate_front"),
        ("cable10_inside", "cable10_outside"), ("cable10_outside", "grommet10"), ("cable10_outside", "side_plate_front"), ("cable10_outside", "ext_x"),
        ("cable10_outside", "ext_post"), ("cable10_outside", "corner_bracket"), ("cable10_outside", "ext_y"), ("cable10_p16", "nut_m3_clevis"),
        ("cable10_inside", "nut_m3_clevis"), ("cable10_inside", "clevis_screw"),
        ("deck10_front", "panel_front_bay"), ("deck10_front", "baffle10_side_p"), ("deck10_front", "baffle10_side_m"), ("deck10_front", "deck10_riser"),
        ("deck10_riser", "deck10_back"), ("deck10_riser", "baffle10_side_p"), ("deck10_riser", "baffle10_side_m"), ("deck10_back", "baffle10_side_p"),
        ("deck10_back", "baffle10_side_m"), ("deck10_back", "baffle10_back"), ("baffle10_side_p", "panel_front_bay"), ("baffle10_side_m", "panel_front_bay"),
        ("baffle10_side_p", "baffle10_back"), ("baffle10_side_m", "baffle10_back"),
        ("bay10_front", "bay10_side_p"), ("bay10_front", "bay10_side_m"), ("bay10_front", "bay10_top"), ("bay10_top", "bay10_side_p"), ("bay10_top", "bay10_side_m"),
        ("bay10_side_p", "panel_front_bay"), ("bay10_side_m", "panel_front_bay"), ("bay10_top", "panel_front_bay"), ("bay9_door", "bay10_front"),
        ("hinge_leaf", "bay10_front"), ("catch", "bay10_front"),
        # ---- v11: the NEMA 11, the 24T pinion (in mesh with the auger's 44T gear) and the solenoid in the EC; the P16-150's rear tab in
        # its clevis under the front bar and its rod end in the arm's clevis, on their shoulder screws; the clevis and the bar screwed to
        # each other and the bar to the posts; the guide shoe parked in its seat; the door rod pressed into the shutter, through the
        # housing's cap and the spring, its head pressed on and riding on the EC's door ramp; the beaker's pillar on the pan, the
        # beaker in its socket and the balance's own parts; the front panel on its standoffs, butted to the sides and top
        # 2026-11-27: ("ec11", "pinion24") and ("ec11", "guide11") are no longer skipped: skipping them hid the EC's spine running through the
        # pinion (652 mm3) and the guide's seat inside the EC's arm (1759 mm3), both found by slicing the EC in Bambu Studio and now fixed.
        # ("ec11", "nema11") stays: the motor is bolted flat to the EC's plate (4.3 mm3 where the faces meet).
        ("ec11", "nema11"), ("ec11", "solenoid"), ("nema11", "pinion24"), ("auger", "pinion24"),
        ("p16_bracket11", "actuator_body"), ("p16_bracket11", "clevis_screw"), ("p16_bracket11", "nut_m3_clevis"), ("p16_bracket11", "bar11"),
        ("ec11", "actuator_rod"), ("ec11", "ec_pin_screw"), ("ec11", "nut_m3_clevis"), ("guide11", "beam10"),
        ("bar11", "ext_post"), ("bar11", "m5x35_shcs"), ("m5x35_shcs", "ext_post"), ("bar11", "corner_bracket"),
        ("standoff_front11", "ext_post"), ("standoff_front11", "panel_front_door11"), ("standoff_front11", "ext_x"), ("standoff_front11", "ext_y"),
        ("panel_front_door11", "panel_side"), ("panel_front_door11", "panel_side_hatch"), ("panel_top", "panel_front_door11"),
        ("standoff", "panel_front_door11"),
        ("door_rod11", "door_shutter"), ("door_rod11", "door_housing"), ("door_rod11", "door_head11"), ("door_rod11", "door_spring"),
        ("door_rod11", "door_spring_open"), ("door_head11", "ec11"),
        ("bal11_base", "bal11_frame"), ("bal11_base", "bal11_glass"), ("bal11_base", "bal11_pan"), ("bal11_base", "bal11_display"),
        ("bal11_base", "bal11_door_left"), ("bal11_base", "bal11_door_right"), ("bal11_frame", "bal11_glass"), ("bal11_frame", "bal11_door_left"),
        ("bal11_frame", "bal11_door_right"), ("bal11_frame", "bal11_lid"), ("bal11_glass", "bal11_lid"), ("bal11_glass", "bal11_door_left"),
        ("bal11_glass", "bal11_door_right"), ("bal11_frame", "bal11_pan"), ("pillar11", "bal11_pan"), ("beaker", "pillar11"),
        ("bal11_door_left", "bal11_lid"), ("bal11_door_right", "bal11_lid"), ("latch_follower", "latch_rail11"), ("latch_rail11", "side_plate_back"),
        ("latch_rail11", "m5x12_bhcs"),
        # ---- v12: the NEMA 11 bolted flat to the cradle's plate and its pinion on its shaft; the cradle's dowels pressed into the EC's
        # bosses (2.95 holes) and free in the cradle (3.1); the stop's insert melted into the lug and its set screw in the insert; the hall
        # switch in its pocket in the lug and its magnet pressed into the EC's post; the solenoid in its collar and the P16's rod end and pin
        # in the arm's clevis (as v11); the second guide on the second beam (the spring's pairs are skipped by its key's prefix in _skip)
        ("cradle12", "nema11_v12"), ("nema11_v12", "pinion24"), ("cradle12", "pinion24"), ("ec12", "pivot_dowel12"), ("cradle12", "pivot_dowel12"),
        ("cradle12", "insert_m3_short"), ("insert_m3_short", "set_screw_m3x6"), ("cradle12", "set_screw_m3x6"), ("cradle12", "hall_switch12"),
        ("ec12", "hall_magnet12"), ("ec12", "solenoid"), ("ec12", "actuator_rod"), 
        ("guide12", "beam10")}
SKIP = {tuple(sorted(k)) for k in SKIP}
CHAIN = ("chain_inner", "chain_outer", "chain_a1")


def _skip(ka: str, kb: str) -> bool:
    if ka in CHAIN and kb in CHAIN:
        return True                      # links share pins and plates by design
    for k1, k2 in ((ka, kb), (kb, ka)):
        if k1.startswith("spring12_") and k2 in ("cradle12", "ec12"):
            return True                  # v12: the cradle's spring on its seat and in the roof's pocket
    return tuple(sorted((ka, kb))) in SKIP


def _moved(shape, M):
    from OCP.gp import gp_Trsf
    from OCP.TopLoc import TopLoc_Location
    tr = gp_Trsf()
    tr.SetValues(*[float(v) for v in M[:3, :].ravel()])
    return cq.Shape.cast(shape.wrapped.Moved(TopLoc_Location(tr)))


@lru_cache(None)
def _snap_lips() -> cq.Shape:
    """The snap hooks' two lips (the 0.8 mm overhang onto the mounting plate's edge), carriage frame (u, w, x)."""
    top = HINGE_W - SAM_DROP + 5.0                      # the plate's top face where the hooks hold it (parts.carriage)
    z = None
    for su in (-1, 1):
        u0, u1 = sorted((su * (25.2 - SNAP_LAP - 0.01), su * 25.2))
        b = cq.Workplane("XY").box(u1 - u0, 2.22, 12.02, centered=False).translate((u0, top + 0.19, SNAP_X - 6.01))
        z = b if z is None else z.union(b)
    return z.val()


SNAP_LOG: list = []      # (pose, plate, carriage, mm^3): the plate passing the snap lips, reported but not a clash


def overlaps(objs: list, pairs=None, min_vol: float = 0.5, tag: str = "") -> list:
    """Pairs of (key, name, shape, M) sharing more than min_vol. The one by-design contact that can't be skipped by key:
    while the station tilts the module (or the actuator pulls it back), the mounting plate's edge passes the carriage's
    two snap-hook lips, which flex 0.8 mm (SNAP_LAP) out of its way. The part of a plate/carriage overlap inside the lips
    is logged in SNAP_LOG; anything outside them (lugs, ribs, hook arms, window) still counts as a clash."""
    boxes = [o[2].BoundingBox() for o in objs]
    hits = []
    it = pairs if pairs is not None else itertools.combinations(range(len(objs)), 2)
    for i, j in it:
        (ka, na, sa, Ma), (kb, nb, sb, Mb) = objs[i], objs[j]
        a, b = boxes[i], boxes[j]
        if a.xmax < b.xmin or b.xmax < a.xmin or a.ymax < b.ymin or b.ymax < a.ymin or a.zmax < b.zmin or b.zmax < a.zmin:
            continue
        if _skip(ka, kb):
            continue
        common = sa.intersect(sb)
        v = common.Volume()
        if v > min_vol:
            hits.append((na, nb, round(v, 2)))
    return hits


def objects(pl) -> list:
    return [(p.key, p.name, L.moved(p.key, p.M), p.M) for p in pl]


def _report(tag: str, hits: list, extra: dict | None = None) -> None:
    OUT.mkdir(exist_ok=True)
    rec = {"check": tag, "clashes": [{"a": a, "b": b, "mm3": v} for a, b, v in hits], **(extra or {})}
    (OUT / f"{tag}.json").write_text(json.dumps(rec, indent=1) + "\n")
    print(f"{tag}: {len(hits)} clash(es) over 0.5 mm^3")
    for a, b, v in sorted(hits, key=lambda h: -h[2])[:40]:
        print(f"  {v:9.2f} mm^3  {a}  x  {b}")


def home() -> list:
    pl = L.placements(L.State())
    t0 = time.time()
    hits = overlaps(objects(pl))
    _report("home", hits, {"instances": len(pl), "seconds": round(time.time() - t0)})
    return hits


ROT = ("sprocket_32", "shaft", "shaft_drive", "sprocket_15_shaft", "sprocket_15_motor")


def sweep(step: float = 0.5) -> list:
    """Chain travel 0 .. one module (8 links) the way the machine runs (RUN_DIRECTION), in half-link steps.
    Movers: carriages and everything on them, and the chain links (exact polygonal kinematics). The station is
    retracted (actuator at 0) as it is whenever the chain moves."""
    hits = []
    n = int(round(MODULE_LINKS / step))
    static = None
    for i in range(n + 1):
        s = RUN_DIRECTION * i * step
        st = L.State(shift=s, ext=0.0, enclosure=False)
        pl = L.placements(st)
        mv = [p for p in pl if p.module >= 0 or p.key in CHAIN and p.group == "chain"]
        mv_ids = {id(p) for p in mv}
        if static is None:
            static_pl = [p for p in pl if id(p) not in mv_ids and p.key not in ROT and p.group != "drive"]
            static = objects(static_pl)
        rot = [p for p in pl if p.key in ROT or p.group == "drive"]
        mo = objects(mv)
        objs = mo + static + objects(rot)
        nm = len(mo)
        pairs = []
        for a in range(nm):
            for b in range(a + 1, len(objs)):
                if b < nm and mv[a].module == mv[b].module and mv[a].module >= 0:
                    continue             # parts of one carriage move together
                if b < nm and mv[a].key in CHAIN and mv[b].key in CHAIN:
                    continue
                pairs.append((a, b))
        h = overlaps(objs, pairs)
        hits += [(f"{a} @{s:+.1f}", b, v) for a, b, v in h]
        print(f"  shift {s:+5.1f} links: {len(h)} clash(es)", flush=True)
    _report("sweep", hits, {"step_links": step, "poses": n + 1, "direction": RUN_DIRECTION})
    return hits


LATCH_CAM = "latch_rail11"          # v11: v10's cam, its web and foot beside the back hold-down (layout._station_v11)


def latch(step: float = 0.25, span: float = 3.0, angles=(10, 20, 30, 40, 50, 60, 70, 80, 90)) -> list:
    """v11 (v5's check, 2026-11-10, adapted): the station's latch cam (LATCH_CAM) against every other part, first while carriage 1
    passes it in quarter-link steps over +-span links with the station at rest (tilt 0, the EC on its guide), then with module 1
    pulled up at the station to each of `angles` (the EC and the P16-150 with it). v11 has no parked/docked drop (v5's ext poses):
    the EC is inside the loop and only turns with the module. The span is 3 links (28.6 mm) because v10's cam is longer than v5's:
    its +-18 mm flat and 30 deg ramps end at +-25.8 mm (2.7 links), plus the follower's 1.5 mm radius. Also reports how much each
    follower overlaps the cam, a by-design contact the other checks skip: it should stay a sliver (the round follower on the
    ramp, positioned by layout.latch_open's straight-line ramp), never a block."""
    hits, contact = [], []
    poses = [(round(-span + i * step, 4), 0.0) for i in range(int(round(2 * span / step)) + 1)] + [(0.0, float(a)) for a in angles]
    for s, a in poses:
        st = L.State(shift=s, tilt=a, enclosure=False)
        pl = L.placements(st)
        cam = [p for p in pl if p.key == LATCH_CAM]
        assert len(cam) == 1, f"expected one {LATCH_CAM}, found {len(cam)}"
        rest = [p for p in pl if p.key != LATCH_CAM]
        objs = objects(cam) + objects(rest)
        h = overlaps(objs, [(0, j) for j in range(1, len(objs))])
        hits += [(f"{x} @shift {s:+.2f}, tilt {a:.0f}", y, v) for x, y, v in h]
        rb = objs[0][2].BoundingBox()
        for p, (k, nm, sh, M) in zip(rest, objs[1:]):
            if k != "latch_follower":
                continue
            b = sh.BoundingBox()
            if b.xmax < rb.xmin or rb.xmax < b.xmin or b.ymax < rb.ymin or rb.ymax < b.ymin or b.zmax < rb.zmin or rb.zmax < b.zmin:
                continue
            v = objs[0][2].intersect(sh).Volume()
            if v > 1e-4:
                contact.append({"shift": s, "tilt": a, "follower": nm, "bolt_open_mm": round(L.latch_open(p.module, st), 2), "mm3": round(v, 3)})
        print(f"  shift {s:+5.2f}, tilt {a:4.1f}: {len(h)} clash(es)", flush=True)
    _report("latch", hits, {"poses": len(poses), "step_links": step, "span_links": span, "tilts": list(angles), "cam": LATCH_CAM,
                            "follower_on_cam": contact, "follower_on_cam_max_mm3": max((c["mm3"] for c in contact), default=0.0)})
    return hits


MOVING_GROUPS = ("station_ec", "station_act", "cable")   # v7: the EC, the one P16 (body swings on its base pin, rod); plus the station module
TOP_OPEN = 205.0                                          # v5: the HR-202i's top door slid back while the station doses (A&D's DXF)


def tilt(angles=(5, 10, 20, 30, 40, 50, 60, 70, 80, 90), exts=(0.0, 2.5, 5.0, 7.5, PARK_DROP), tag: str = "tilt") -> list:
    """Station: the EC rising out of its cradle (ext 0 -> docked; the door opens over the last 8.5 mm), then module 1 + EC
    + actuator tilting about the hinge, against everything else (carriage 1 included: its window, pads, latch, lugs)."""
    hits = []
    for kind, vals in (("ext", exts), ("tilt", angles)):
        for v in vals:
            st = L.State(ext=v, top_door=TOP_OPEN) if kind == "ext" else L.State(tilt=float(v), top_door=TOP_OPEN)
            pl = L.placements(st)
            k_st = L.carriage_at(L.CARRIAGE_LINK0, 0.0)
            mv = [p for p in pl if p.group in MOVING_GROUPS or (p.group == "modules" and p.module == k_st)]
            ids = {id(p) for p in mv}
            rest = [p for p in pl if id(p) not in ids]
            mo, ro = objects(mv), objects(rest)
            objs = mo + ro
            pairs = [(a, b) for a in range(len(mo)) for b in range(len(mo), len(objs))]
            pairs += [(a, b) for a in range(len(mo)) for b in range(a + 1, len(mo))]
            h = overlaps(objs, pairs, tag=f"{kind}{v:g}")
            hits += [(f"{a} @{kind}{v:g}", b, x) for a, b, x in h]
            print(f"  {kind} {v:5.1f}: {len(h)} clash(es)", flush=True)
    _report(tag, hits, {"angles": list(angles), "exts": list(exts)})
    return hits


def tilt10(angles=(4, 10, 20, 30, 40, 50, 60, 65, 70, 75, 80), tag: str = "tilt") -> list:
    """v10: module 1 coupled to the EC, pulled up about the hinge by the P16-100 from TAU0 to the angles given, the EC, the P16 (its
    body swings on its base pin, its rod slides) and the cable on the EC moving with it, against everything else (carriage 1
    included: its opening, ribs, lugs, latch; the neighbouring modules; the sprockets and the chain; the beam and the guide)."""
    hits = []
    for v in angles:
        st = L.State(tilt=float(v))
        pl = L.placements(st)
        k_st = L.carriage_at(L.CARRIAGE_LINK0, 0.0)
        mv = [p for p in pl if p.group in MOVING_GROUPS or (p.group == "modules" and p.module == k_st)]
        ids = {id(p) for p in mv}
        rest = [p for p in pl if id(p) not in ids]
        mo, ro = objects(mv), objects(rest)
        objs = mo + ro
        pairs = [(a, b) for a in range(len(mo)) for b in range(len(mo), len(objs))]
        h = overlaps(objs, pairs, tag=f"tilt{v:g}")
        hits += [(f"{a} @tilt{v:g}", b, x) for a, b, x in h]
        print(f"  tilt {v:5.1f}: {len(h)} clash(es)", flush=True)
        for a, b, x in sorted(h, key=lambda q: -q[2])[:6]:
            print(f"      {x:8.2f}  {a}  x  {b}", flush=True)
    _report(tag, hits, {"angles": list(angles)})
    return hits


def cradle(lifts=(-0.4, 0.0, 1.0, 2.0, 2.6, 3.2), angles=(0.0, 30.0, 90.0)) -> list:
    """v12: the pinion's cradle over its whole travel (on its stop, in tight mesh, lifted 1, 2 (a tip-on-tip stub), 2.6 and 3.2 mm, the
    roof's pad) at rest and with the module pulled up to 30 and 90 deg: the cradle, the NEMA 11, the pinion, the spring, the stop's set
    screw and insert and the hall switch against everything else (the EC included, its pivot bosses, rail, roof, magnet post and arm)."""
    hits = []
    movers = ("cradle12", "nema11_v12", "pinion24", "set_screw_m3x6", "insert_m3_short", "hall_switch12")
    for a in angles:
        for lf in lifts:
            st = L.State(tilt=float(a), cradle_lift=float(lf))
            pl = L.placements(st)
            mv = [p for p in pl if p.key in movers or p.key.startswith("spring12_")]
            ids = {id(p) for p in mv}
            rest = [p for p in pl if id(p) not in ids]
            mo, ro = objects(mv), objects(rest)
            objs = mo + ro
            pairs = [(i, j) for i in range(len(mo)) for j in range(i + 1, len(objs))]
            h = overlaps(objs, pairs)
            hits += [(f"{x} @tilt{a:g} lift{lf:+g}", y, v) for x, y, v in h]
            print(f"  tilt {a:4.0f}, lift {lf:+.1f}: {len(h)} clash(es)", flush=True)
    _report("cradle", hits, {"lifts_mm": list(lifts), "angles": list(angles)})
    return hits


SWAP_AUGER_OUT = (5.0, 15.0, 30.0, 45.0, 60.0, 80.0, 100.0, 140.0)       # mm off the plate: the auger crosses the +y panel at 43-92
SWAP_LIFT = (0.0, 15.0, 30.0, 45.0, 60.0, 75.0, 90.0, 100.0)               # v11: 15 mm steps; v4's 0, 30, 100 jumped over the panel


def swap() -> list:
    """v4: at the loading position (+y side, module 4 at home), the side hatch open, the auger pulled straight off its plate
    (out of the loop, through the hatch) in steps, against everything else; then the carriage's own removal as v3 (screws
    out, slid 10 mm, lifted out) for completeness. v11: the lifts in 15 mm steps (SWAP_LIFT). The carriage (32.6 mm deep) crosses
    the +y panel's 3 mm between lifts of 58 and 94 mm, which v4's 0, 30 and 100 mm stepped over."""
    hits = []
    k = 3
    for ao in SWAP_AUGER_OUT:
        st = L.State(out_auger=k, auger_out=ao, hatch_side=HATCH_OPEN_DEG)
        pl = L.placements(st)
        mv = [p for p in pl if p.module == k and p.key in ("auger", "auger_cap")]
        ids = {id(p) for p in mv}
        rest = [p for p in pl if id(p) not in ids]
        mo, ro = objects(mv), objects(rest)
        objs = mo + ro
        pairs = [(a, b) for a in range(len(mo)) for b in range(len(mo), len(objs))]
        h = overlaps(objs, pairs)
        hits += [(f"{a} @auger_out{ao:g}", b, x) for a, b, x in h]
        print(f"  auger out {ao:5.1f}: {len(h)} clash(es)", flush=True)
    so = SCREW_OUT
    for so_, sl, lf in [(so, HOOK_SLIDE, lift) for lift in SWAP_LIFT]:
        st = L.State(out_carriage=k, screws_out=so_, out_slide=sl, out_lift=lf, hatch_side=HATCH_OPEN_DEG)
        pl = L.placements(st)
        mv = [p for p in pl if p.module == k]
        ids = {id(p) for p in mv}
        rest = [p for p in pl if id(p) not in ids]
        mo, ro = objects(mv), objects(rest)
        objs = mo + ro
        pairs = [(a, b) for a in range(len(mo)) for b in range(len(mo), len(objs))]
        h = overlaps(objs, pairs)
        hits += [(f"{a} @carriage slide{sl:g}/lift{lf:g}", b, x) for a, b, x in h]
        print(f"  carriage slide {sl:4.1f} lift {lf:5.1f}: {len(h)} clash(es)", flush=True)
    _report("swap", hits, {"module": k + 1, "slot": L.LOAD_SLOT, "hatch_side_deg": HATCH_OPEN_DEG, "auger_out_mm": list(SWAP_AUGER_OUT),
                           "carriage": {"screws_out_mm": so, "slide_mm": HOOK_SLIDE, "lift_mm": list(SWAP_LIFT)}})
    return hits


def scale() -> list:
    """v5: the balance with its pan centre under the dose point, against everything else: the HR-202i with the station
    parked, docked, and tilted to 30 and 50 deg (its top door open), then the lab's HR-100A (stock breeze break) parked and
    at 30 deg. Every hit would be a part in the balance's way; v5 is meant to have none."""
    hits, poses = [], []
    for model, states in (("hr202i", (dict(ext=0.0), dict(ext=PARK_DROP, top_door=TOP_OPEN), dict(tilt=30.0, top_door=TOP_OPEN),
                                       dict(tilt=50.0, top_door=TOP_OPEN))),
                          ("hr100a", (dict(ext=0.0), dict(tilt=30.0)))):
        for kw in states:
            pl = L.placements(L.State(scale_model=model, **kw))
            sc = [p for p in pl if p.group == "scale"]
            rest = [p for p in pl if p.group != "scale"]
            so, ro = objects(sc), objects(rest)
            objs = so + ro
            pairs = [(a, b) for a in range(len(so)) for b in range(len(so), len(objs))]
            h = overlaps(objs, pairs, min_vol=0.0)
            tag = f"{model} {kw}"
            hits += [(f"{a} @{tag}", b, v) for a, b, v in h]
            poses.append(tag)
            print(f"  {tag}: {len(h)} part(s) in the balance's way", flush=True)
    _report("scale", hits, {"pan_centre": [round(float(v), 2) for v in L.scale_pan_target()[:2]], "poses": poses,
                            "note": "v5: the balance at the dose point; any hit is a part in its way (min volume 0)"})
    return hits


if __name__ == "__main__":
    if "--cradle" in sys.argv:
        cradle()
    elif "--sweep" in sys.argv:
        # --step N: a coarser sweep (N links per pose) when time is short; the JSON records the step and pose count
        sweep(float(sys.argv[sys.argv.index("--step") + 1])) if "--step" in sys.argv else sweep()
    elif "--latch" in sys.argv:
        latch()
    elif "--tilt10" in sys.argv or "--tilt11" in sys.argv:
        a = [float(v) for v in sys.argv[sys.argv.index("--angles") + 1].split(",") if v] if "--angles" in sys.argv else (0, 10, 20, 30, 40, 50, 60, 70, 80, 85, 90)
        tg = sys.argv[sys.argv.index("--tag") + 1] if "--tag" in sys.argv else "tilt"
        tilt10(a, tag=tg)
    elif "--tilt" in sys.argv:
        # v6: --angles 5,10 --exts 0,5 --tag tilt_a: subsets run as parallel processes, merged by hand into checks/tilt.json
        a = [float(v) for v in sys.argv[sys.argv.index("--angles") + 1].split(",") if v] if "--angles" in sys.argv else None
        e = [float(v) for v in sys.argv[sys.argv.index("--exts") + 1].split(",") if v] if "--exts" in sys.argv else None
        tg = sys.argv[sys.argv.index("--tag") + 1] if "--tag" in sys.argv else "tilt"
        tilt(**{k: v for k, v in (("angles", a), ("exts", e)) if v is not None}, tag=tg)
    elif "--swap" in sys.argv:
        swap()
    elif "--scale" in sys.argv:
        scale()
    else:
        home()
