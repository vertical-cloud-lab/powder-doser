"""Where every screw and nut goes, for both servo layouts.

Ported from PR #170's ``cad/full-assembly/hardware.py`` (``fastener_placements``),
which reads each joint off the hole geometry of the lab's STEP files.  A
fastener's seat frame has +Z along the direction it is driven in, with the
origin where its head (or a nut's bearing face) seats; ``lib.fasteners``
returns the step.parts models in that frame.

Servos-above: the servo screws and nuts turn 180 deg about the hinge with
the servos, and the two leg screws go with the legs.  Everything but the
board screws also moves down with the doser (``frames.lower``).
"""
from __future__ import annotations

import numpy as np

from lib import frames as F

# McMaster-Carr part numbers (PR #170's BOM; confirmed in McMaster's catalog)
MCMASTER = {
    "bhcs_m5x45": "92095A223", "locknut_m5": "93625A200", "shcs_m3x14": "91292A027",
    "locknut_m3": "93625A100", "hexnut_m3": "91828A211", "shcs_m3x10": "91292A113",
    "bhcs_m3x20": "92095A185", "bhcs_m3x25": "92095A186", "fhcs_m3x30": "92125A140",
    "shcs_m3x5": "91292A110", "shcs_m2p5x8": "91292A012", "wood_10x1p25": "93360A609",
}

BOARD_HOLES = [(sx * 80.0, y) for sx in (1, -1) for y in (65.4, 95.4)]
BOARD_HOLES_ABOVE = [(sx * 80.0, y) for sx in (1, -1) for y in (122.0, 155.0)]
LEG_HOLES = [(sx * 70.0, -19.0) for sx in (1, -1)]
LEG_FRONT_Y = 50.4


def seat_frame(origin, z_dir, x_hint=(0.0, 0.0, 1.0)) -> np.ndarray:
    z = np.asarray(z_dir, float)
    z /= np.linalg.norm(z)
    h = np.asarray(x_hint, float)
    if abs(np.dot(h, z)) > 0.9:
        h = np.array([1.0, 0.0, 0.0]) if abs(z[0]) < 0.9 else np.array([0.0, 1.0, 0.0])
    x = h - np.dot(h, z) * z
    x /= np.linalg.norm(x)
    y = np.cross(z, x)
    M = np.eye(4)
    M[:3, 0], M[:3, 1], M[:3, 2], M[:3, 3] = x, y, z, origin
    return M


def fastener_placements(tilt_deg: float = 0.0, variant: str = "below",
                        with_board: bool = True) -> list[tuple[str, str, str, str, np.ndarray]]:
    """[(instance name, hardware key, joint, carrier part, world 4x4)].
    The carrier is the placement the fastener moves with (frames.placements)."""
    P = F.placements(tilt_deg, variant)
    W = {n: M for n, (_, M) in P.items()}
    low = F.lower(variant)
    side = low @ (F.FLIP if variant == "above" else np.eye(4))
    out = []

    def add(name, key, joint, carrier, parent_M, origin, z_dir):
        out.append((name, key, joint, carrier, parent_M @ seat_frame(origin, z_dir)))

    for s, tag in ((1, "+X"), (-1, "-X")):
        add(f"Hinge screw ({tag})", "bhcs_m5x45", "hinge", "Baseplate", low,
            (s * 16.1, F.HINGE_Y, F.HINGE_Z), (s, 0, 0))
        add(f"Hinge locknut ({tag})", "locknut_m5", "hinge", "Baseplate", low,
            (s * 54.1, F.HINGE_Y, F.HINGE_Z), (s, 0, 0))

    for b in ("rear", "front"):
        name = f"Bracket ({b})"
        M = W[name]
        for sx in (-1, 1):
            t = "+" if sx > 0 else "-"
            add(f"Bracket screw ({b}, {t})", "bhcs_m3x20", "brackets", name, M,
                (sx * 24.0, 6.0, -6.0), (0, 0, 1))
            add(f"Bracket nut ({b}, {t})", "locknut_m3", "brackets", name, M,
                (sx * 24.0, 6.0, 8.0), (0, 0, 1))
        add(f"Bracket clamp screw ({b})", "shcs_m3x14", "brackets", name, M, (4.0, 6.0, 49.2), (-1, 0, 0))
        add(f"Bracket clamp nut ({b})", "locknut_m3", "brackets", name, M, (-4.0, 6.0, 49.2), (-1, 0, 0))

    name = "Tap collar base"
    M = W[name]
    add("Tap base screw (-)", "bhcs_m3x25", "tap collar", name, M, (-24.0, 0.0, -6.0), (0, 0, 1))
    add("Tap base nut (-)", "locknut_m3", "tap collar", name, M, (-24.0, 0.0, 14.0), (0, 0, 1))
    add("Tap base screw (+)", "fhcs_m3x30", "tap collar", name, M, (24.0, 0.0, 21.0), (0, 0, -1))
    add("Tap base nut (+)", "hexnut_m3", "tap collar", name, M, (24.0, 0.0, -6.0), (0, 0, -1))

    name = "Tap collar"
    M = W[name]
    add("Tap collar clamp screw", "bhcs_m3x20", "tap collar", name, M, (-20.2, 8.5, 6.9), (0, 0, -1))
    add("Tap collar clamp nut", "locknut_m3", "tap collar", name, M, (-20.2, 8.5, -6.9), (0, 0, -1))
    for x, z, tag in ((-9.1, 33.0, "lower"), (9.1, 49.0, "upper")):
        add(f"Solenoid screw ({tag})", "shcs_m3x5", "solenoid", name, M, (x, 17.0, z), (0, -1, 0))

    name = "Mounting plate"
    M = W[name]
    for sy in (-1, 1):
        for sz in (-1, 1):
            add(f"Stepper screw ({'+' if sy > 0 else '-'}{'+' if sz > 0 else '-'})", "shcs_m2p5x8",
                "stepper", name, M, (-83.33, sy * 11.5, -9.8 + sz * 11.5), (-1, 0, 0))

    for s, tag in ((1, "+X"), (-1, "-X")):
        for y in (11.5, 59.54):
            for z in (11.48, 20.52):
                pos = f"{tag}, y{y:.0f} z{z:.0f}"
                add(f"Servo screw ({pos})", "shcs_m3x14", "servos", "Baseplate", side,
                    (s * 72.1, y, z), (-s, 0, 0))
                add(f"Servo nut ({pos})", "locknut_m3", "servos", "Baseplate", side,
                    (s * 64.6, y, z), (-s, 0, 0))
        pin = f"Servo pinion ({tag})"
        add(f"Servo pinion screw ({tag})", "shcs_m3x10", "servos", pin, W[pin], (0.0, 0.0, 1.25), (0, 0, 1))

    if with_board:
        for x, y in (BOARD_HOLES if variant == "below" else BOARD_HOLES_ABOVE):
            add(f"Board screw ({'+' if x > 0 else '-'}X, y{y:.0f})", "wood_10x1p25", "board",
                "Baseplate", np.eye(4), (x, y, 6.0), (0, 0, -1))
        if variant == "below":
            for x, z in LEG_HOLES:
                add(f"Board screw (leg {'+' if x > 0 else '-'}X)", "wood_10x1p25", "board",
                    "Baseplate", np.eye(4), (x, LEG_FRONT_Y, z), (0, 1, 0))
    return out
