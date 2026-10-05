"""The build, step by step, for the assembly clip and its captions.

Each step names labels in the doser tree (a group's label stands for all
of its leaves), the direction each part comes in from (mm offset at the
start of its move; it slides to rest), and a caption.  ``timed_steps``
resolves the labels to rendered leaves and lays the steps out in time for
``doser.animation``; the GIF captions use the same timing.

Order of the servos-above build (why it has to be this order):
* the mounting plate goes onto the towers before the servos, because the
  servo splines sit over the 28T gears once the servos are in;
* the servos then drop into their open-top cradles from above (their
  splines pass 8 mm over the gears' tips) and the 14T pinions slide onto
  the splines from inside, meshing the gears sideways;
* the stepper goes before the auger: its inner M2.5 heads can't pass the
  44T gear afterwards (PR #170), and the rear bracket goes on last, slid
  along the tube from the cap end, under the stepper (PR #170).
"""
from __future__ import annotations

MOVE, HOLD = 1.6, 1.4      # s per step: sliding in, then holding still


def _pm(label_fmt: str, d: float, axis: int = 0):
    """(+X part, offset), (-X part, mirrored offset)."""
    out = []
    for s, tag in ((1, "pos"), (-1, "neg")):
        v = [0.0, 0.0, 0.0]
        v[axis] = s * d
        out.append((label_fmt.format(tag), v))
    return out


def steps_servos_above() -> list[dict]:
    S = []

    def add(caption, parts):
        S.append({"caption": caption, "parts": parts})

    add("A flat board or bench top, 38 mm (1.5 in) thick", [("board", [0, 0, -40])])
    add("Baseplate onto the board, overhanging its front edge by 44.6 mm; it is relieved "
        "under the mounting plate, so the doser sits 5 mm lower", [("baseplate", [0, 0, 60])])
    add("4 x #10 x 1-1/4 in pan head wood screws through the plate into the board",
        [(f"board_screw_{t}_y{y}", [0, 0, 25]) for t in ("pos", "neg") for y in (115, 155)])
    add("Mounting plate lowered onto the hinge towers: knuckles inside them, "
        "28T gears outside", [("mounting_plate", [0, 0, 70])])
    add("Hinge: M5 x 45 button head from inside each knuckle, "
        "nylon-insert locknut outside each gear",
        _pm("hinge_screw_{}", -25) + _pm("hinge_locknut_{}", 20))
    add("Servos dropped into their open-top cradles from above, splines inwards; "
        "the splines pass 8 mm over the gear tips", [("servo_pos", [0, 0, 60]), ("servo_neg", [0, 0, 60])])
    add("Each servo: 4 x M3 x 14 socket head through the post and ear, locknut inside",
        [(f"servo_screw_{t}_y{y}_z{z}", [s * 18, 0, 0])
         for s, t in ((1, "pos"), (-1, "neg")) for y in (12, 60) for z in (11, 21)]
        + [(f"servo_nut_{t}_y{y}_z{z}", [-s * 12, 0, 0])
           for s, t in ((1, "pos"), (-1, "neg")) for y in (12, 60) for z in (11, 21)])
    add("14T pinions slid onto the splines from inside, meshing the 28T gears from above",
        _pm("servo_pinion_{}", -25))
    add("M3 x 10 socket head into each servo shaft", _pm("servo_pinion_screw_{}", -14))
    add("Tap-collar base (hard stop) on the plate's front hole row: "
        "M3 x 25 button head + M3 x 30 flat head, locknut and nut",
        [("tap_collar_base", [0, 0, 40]), ("tap_base_screw_n", [0, 0, -15]),
         ("tap_base_nut_n", [0, 0, 15]), ("tap_base_screw_p", [0, 0, 15]),
         ("tap_base_nut_p", [0, 0, -15])])
    add("Stepper (NEMA 11) onto its plate from behind: 4 x M2.5 x 8",
        [("stepper", [0, 60, 0])] + [(f"stepper_screw_{a}{b}", [0, -15, 0])
                                     for a in ("p", "n") for b in ("p", "n")])
    add("20T pinion onto the stepper shaft", [("stepper_pinion", [0, -30, 0])])
    add("Auger, with the front bracket and the tap collar slid on from the outlet end, "
        "lowered onto the plate; the 44T gear meshes the pinion",
        [("auger_group", [0, 0, 70]), ("bracket_front", [0, 0, 70]),
         ("tap_collar", [0, 0, 70])])
    add("Rear bracket slid on from the cap end, under the stepper",
        [("bracket_rear", [0, 90, 0])])
    add("Brackets: M3 x 20 button heads up through the plate, locknuts on top; "
        "M3 x 14 clamp screws",
        [(f"bracket_screw_{b}_{t}", [0, 0, -15]) for b in ("rear", "front") for t in ("p", "n")]
        + [(f"bracket_nut_{b}_{t}", [0, 0, 15]) for b in ("rear", "front") for t in ("p", "n")]
        + [(f"bracket_clamp_screw_{b}", [8, 0, 0]) for b in ("rear", "front")]
        + [(f"bracket_clamp_nut_{b}", [-8, 0, 0]) for b in ("rear", "front")])
    add("Tap-collar clamp: M3 x 20 button head and locknut",
        [("tap_collar_clamp_screw", [0, 0, 15]), ("tap_collar_clamp_nut", [0, 0, -15])])
    add("Solenoid onto the collar's plate: 2 x M3 x 5", [("solenoid", [0, 0, 45]),
                                                          ("solenoid_screw_lower", [0, 0, 20]),
                                                          ("solenoid_screw_upper", [0, 0, 20])])
    add("Electronics: the POWDER_DOSER_V2 board on its holder beside the doser, "
        "components facing it; 3 x #10 wood screws", [("electronics", [60, 0, 40])])
    return S


def resolve(tree, label: str) -> list[str]:
    """Leaf labels under the node labelled ``label`` (itself if a leaf)."""
    def find(node):
        if node.label == label:
            return node
        for ch in getattr(node, "children", ()) or ():
            hit = find(ch)
            if hit is not None:
                return hit
        return None

    def leaves(node):
        kids = getattr(node, "children", ()) or ()
        if not kids:
            return [node.label]
        out = []
        for ch in kids:
            out += leaves(ch)
        return out

    node = find(tree)
    return [] if node is None else leaves(node)


def timed_steps(tree, steps: list[dict], move: float = MOVE,
                hold: float = HOLD) -> tuple[list[dict], list[dict]]:
    """(clip steps for doser.animation, caption timeline).  Parts whose
    label isn't in the tree are skipped (e.g. no electronics)."""
    clip, captions, t = [], [], 0.0
    for i, st in enumerate(steps):
        groups = []
        for label, d in st["parts"]:
            # leaves can share a label (the PCB's header pins do); the clip's
            # m.get(label) moves all of them, so each label goes in once
            leaves = list(dict.fromkeys(resolve(tree, label)))
            if leaves:
                groups.append({"parts": leaves, "dir": d, "t0": round(t, 3),
                               "move": move, "hold": hold})
        if not groups:
            continue
        clip += groups
        captions.append({"step": len(captions) + 1, "t0": round(t, 3),
                         "t1": round(t + move + hold, 3), "caption": st["caption"]})
        t += move + hold
    return clip, captions
