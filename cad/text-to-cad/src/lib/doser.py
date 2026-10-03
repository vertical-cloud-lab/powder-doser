"""The whole doser as one labelled build123d tree, for either servo layout.

``build_doser(variant)`` is called by the two assembly models
(``assembly_current.py``: servos below, ``assembly_servos_above.py``).  It
places every recreated part with ``lib.frames``, every fastener with
``lib.hardware_placements`` (geometry from ``lib.fasteners``: step.parts
models in PR #170's seat frames), the electronics, and the 38.1 mm board.

Tree (labels are unique, so kinematics and animation can name any leaf):

    doser_<variant>
      board, baseplate, servo_pos/neg, servo_pinion_pos/neg_group,
      baseplate_hw/...            (hinge, servo and board fasteners)
      tilt_group/                 (everything the servos tilt)
        mounting_plate, bracket_front/rear, tap_collar_base, tap_collar,
        solenoid/{frame, plunger, spring}, stepper, stepper_pinion,
        auger_group/{auger, auger_cap}, tilt_hw/...
      electronics/...

``kinematics(variant)`` declares the mates: the hinge (0-45 deg, outlet
down), both servo pinions geared to it at -2 (28T:14T), the auger turning
in the brackets with the stepper pinion geared at -44/20, and the solenoid
plunger (7.6 mm stroke).  ``animation(variant)`` returns the JS module with
two clips: ``motion`` (tilt, turn, tap) and ``assembly`` (the build, step by
step).
"""
from __future__ import annotations

import json
import re

import numpy as np

from cadgen import build123d as bd

from lib import frames as F
from lib import hardware_placements as H

# colours: PR #170's June palette (gold auger, purple tapping, grey tilt)
COLORS = {
    "board": (0.80, 0.68, 0.50), "baseplate": (0.55, 0.57, 0.60),
    "mounting_plate": (0.70, 0.71, 0.73), "auger": (0.80, 0.63, 0.25),
    "auger_cap": (0.20, 0.32, 0.65), "bracket": (0.45, 0.62, 0.75),
    "tap_collar": (0.55, 0.35, 0.70), "tap_collar_base": (0.35, 0.55, 0.70),
    "stepper_pinion": (0.30, 0.60, 0.40), "servo_pinion": (0.30, 0.60, 0.40),
    "mg996r": (0.12, 0.12, 0.13), "nema11": (0.20, 0.20, 0.22),
}

PLUNGER_STROKE = 7.6


def slug(name: str) -> str:
    """'Bracket screw (rear, +)' -> 'bracket_screw_rear_p'."""
    s = name.replace("+X", "pos").replace("-X", "neg").replace("+", "p").replace("-", "n")
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")


def _part_models():
    """The child models, imported lazily so this module stays cheap."""
    from auger import auger
    from auger_cap import auger_cap
    from baseplate import baseplate
    from baseplate_servos_above import baseplate_servos_above
    from bracket import bracket
    from mg996r import mg996r
    from mounting_plate import mounting_plate
    from mounting_plate_servos_above import mounting_plate_servos_above
    from nema11 import nema11
    from servo_pinion import servo_pinion
    from solenoid_412 import solenoid_412
    from stepper_pinion import stepper_pinion
    from tap_collar import tap_collar
    from tap_collar_base import tap_collar_base
    return {
        "auger": auger, "auger_cap": auger_cap, "baseplate": baseplate,
        "baseplate_servos_above": baseplate_servos_above, "bracket": bracket,
        "mg996r": mg996r, "mounting_plate": mounting_plate,
        "mounting_plate_servos_above": mounting_plate_servos_above, "nema11": nema11,
        "servo_pinion": servo_pinion, "solenoid_412": solenoid_412,
        "stepper_pinion": stepper_pinion, "tap_collar": tap_collar,
        "tap_collar_base": tap_collar_base,
    }


LABELS = {
    "Baseplate": "baseplate", "Mounting plate": "mounting_plate", "Auger": "auger",
    "Auger cap": "auger_cap", "Bracket (rear)": "bracket_rear", "Bracket (front)": "bracket_front",
    "Tap collar base": "tap_collar_base", "Tap collar": "tap_collar",
    "Solenoid (Adafruit 412)": "solenoid", "Stepper pinion": "stepper_pinion",
    "Stepper (NEMA 11)": "stepper", "Servo pinion (+X)": "servo_pinion_pos",
    "Servo pinion (-X)": "servo_pinion_neg", "Servo MG996R (+X)": "servo_pos",
    "Servo MG996R (-X)": "servo_neg",
}
TILTING = {"Mounting plate", "Auger", "Auger cap", "Bracket (rear)", "Bracket (front)",
           "Tap collar base", "Tap collar", "Solenoid (Adafruit 412)", "Stepper pinion",
           "Stepper (NEMA 11)"}


def _instance(shape, M, label: str, color=None):
    """A placed copy of a child model's tree with fresh, unique labels
    (``<label>_<child label>``), so that two servos or fifty nuts never
    share a label.  Leaves keep their own colour, else get ``color``."""
    loc = F.to_location(M)

    def rec(node, lab):
        kids = getattr(node, "children", ()) or ()
        if kids:
            return bd.Compound(children=[rec(ch, f"{label}_{ch.label or i}")
                                         for i, ch in enumerate(kids)], label=lab)
        out = node.moved(loc)
        out.label = lab
        c = getattr(node, "color", None)
        if c is not None:
            out.color = c
        elif color is not None:
            out.color = bd.Color(*color)
        return out

    return rec(shape, label)


def board_shape(variant: str = "below"):
    """Any flat board or bench top, 1.5 in thick (PR #170: 250 x 220 mm)."""
    b = bd.Box(250.0, 220.0, F.BOARD_T, align=(bd.Align.CENTER, bd.Align.MIN, bd.Align.MAX))
    return b.moved(F.to_location(F.board_placement(variant)))


def build_doser(variant: str, *, electronics=None) -> bd.Compound:
    """The assembled doser at rest (tilt 0).  ``electronics`` is an optional
    already-placed shape (the PCB assembly and its mount)."""
    from lib.fasteners import fastener

    models = _part_models()
    cache = {}

    def geom(key):
        if key not in cache:
            cache[key] = models[key]()
        return cache[key]

    places = F.placements(0.0, variant)
    hw = H.fastener_placements(0.0, variant, with_board=True)
    hw_cache = {}

    def hw_geom(key):
        if key not in hw_cache:
            hw_cache[key] = fastener(key)
        return hw_cache[key]

    top, tilt_children, auger_children = [], [], []
    pinion_groups = {}
    for name, (key, M) in places.items():
        label = LABELS[name]
        shp = _instance(geom(key), M, label, COLORS.get(key.replace("_servos_above", "")))
        if name in ("Auger", "Auger cap"):
            auger_children.append(shp)
        elif name in TILTING:
            tilt_children.append(shp)
        elif name.startswith("Servo pinion"):
            pinion_groups[name] = [shp]
        else:
            top.append(shp)

    base_hw = []
    for name, key, joint, carrier, M in hw:
        shp = _instance(hw_geom(key), M, slug(name))
        if carrier in TILTING:
            tilt_children.append(shp)
        elif carrier.startswith("Servo pinion"):
            pinion_groups[carrier].append(shp)
        else:
            base_hw.append(shp)

    auger_group = bd.Compound(children=auger_children, label="auger_group")
    tilt_group = bd.Compound(children=tilt_children + [auger_group], label="tilt_group")
    groups = [bd.Compound(children=v, label=LABELS[k] + "_group") for k, v in pinion_groups.items()]
    board = board_shape(variant)
    board.label = "board"
    board.color = bd.Color(*COLORS["board"])
    children = [board, *top, *groups, tilt_group,
                bd.Compound(children=base_hw, label="baseplate_hw")]
    if electronics is not None:
        children.append(electronics)
    return bd.Compound(children=children, label=f"doser_{variant}")


# --------------------------------------------------------------------------- #
# kinematics (pure data in the STEP sidecar)
# --------------------------------------------------------------------------- #
def _axis_point(M, p=(0.0, 0.0, 0.0)):
    return [round(float(v), 4) for v in (M @ np.array([*p, 1.0]))[:3]]


def _axis_dir(M, d=(0.0, 0.0, 1.0)):
    return [round(float(v), 6) for v in (M[:3, :3] @ np.array(d))]


def kinematics(variant: str) -> dict:
    import cadgen

    P = F.placements(0.0, variant)
    sol = P["Solenoid (Adafruit 412)"][1]
    pin_pos, pin_neg = P["Servo pinion (+X)"][1], P["Servo pinion (-X)"][1]
    step_pin = P["Stepper pinion"][1]
    return {
        "mates": [
            cadgen.revolute("tilt", parent="#baseplate", child="#tilt_group",
                            origin=list(F.HINGE), direction=[1, 0, 0], limits=(0, 45)),
            cadgen.revolute("servo_pinion_pos", parent="#baseplate", child="#servo_pinion_pos_group",
                            origin=_axis_point(pin_pos), direction=[1, 0, 0], limits=(-90, 0)),
            cadgen.revolute("servo_pinion_neg", parent="#baseplate", child="#servo_pinion_neg_group",
                            origin=_axis_point(pin_neg), direction=[1, 0, 0], limits=(-90, 0)),
            cadgen.revolute("auger_spin", parent="#mounting_plate", child="#auger_group",
                            origin=[round(float(v), 4) for v in F.outlet_point(0.0)],
                            direction=[0, 1, 0], limits=(0, 720)),
            cadgen.revolute("stepper_pinion_spin", parent="#mounting_plate", child="#stepper_pinion",
                            origin=_axis_point(step_pin), direction=[0, 1, 0],
                            limits=(-1584, 0)),
            cadgen.slider("plunger", parent="#tap_collar", child="#solenoid_plunger",
                          origin=_axis_point(sol), direction=_axis_dir(sol, (0, 0, -1)),
                          limits=(0, PLUNGER_STROKE)),
        ],
        "couplings": [
            cadgen.couple("tilt_drive", {"tilt": 1, "servo_pinion_pos": -F.SERVO_RATIO,
                                         "servo_pinion_neg": -F.SERVO_RATIO}, limits=(0, 45)),
            cadgen.couple("auger_drive", {"auger_spin": 1,
                                          "stepper_pinion_spin": -F.STEPPER_RATIO},
                          limits=(0, 720)),
        ],
        "poses": {"rest": {"tilt_drive": 0}, "dispense_22": {"tilt_drive": 22.5},
                  "dispense_45": {"tilt_drive": 45}},
    }


# --------------------------------------------------------------------------- #
# animation clips (a self-contained JS module in the sidecar)
# --------------------------------------------------------------------------- #
def leaf_labels(shape) -> list[str]:
    out = []
    kids = getattr(shape, "children", ()) or ()
    if not kids:
        return [shape.label] if shape.label else []
    for ch in kids:
        out += leaf_labels(ch)
    return out


def animation(variant: str, tree: bd.Compound, steps: list[dict]) -> str:
    """JS module: ``motion`` and ``assembly`` clips for this tree."""
    P = F.placements(0.0, variant)
    groups = {ch.label: ch for ch in tree.children}
    tilt = groups["tilt_group"]
    auger_grp = next(c for c in tilt.children if c.label == "auger_group")
    data = {
        "hinge": list(F.HINGE),
        "tilt_parts": leaf_labels(tilt),
        "auger_parts": leaf_labels(auger_grp),
        "outlet": [float(v) for v in F.outlet_point(0.0)],
        "stepper_axis": _axis_point(P["Stepper pinion"][1]),
        "pinion_pos": leaf_labels(groups["servo_pinion_pos_group"]),
        "pinion_neg": leaf_labels(groups["servo_pinion_neg_group"]),
        "pinion_pos_axis": _axis_point(P["Servo pinion (+X)"][1]),
        "pinion_neg_axis": _axis_point(P["Servo pinion (-X)"][1]),
        "plunger": [lbl for lbl in leaf_labels(tilt) if lbl.endswith("plunger")],
        "plunger_dir": _axis_dir(P["Solenoid (Adafruit 412)"][1], (0, 0, -1)),
        "stroke": PLUNGER_STROKE, "servo_ratio": F.SERVO_RATIO,
        "stepper_ratio": F.STEPPER_RATIO, "steps": steps,
    }
    return "const D = " + json.dumps(data) + ";\n" + _JS


_JS = r"""
const ease = (s) => (s <= 0 ? 0 : s >= 1 ? 1 : 0.5 - 0.5 * Math.cos(Math.PI * s));

// tilt, auger angle and plunger travel as functions of time
function motionState(t) {
  let tilt = 0, turn = 0, tap = 0;
  if (t < 3) tilt = 30 * ease(t / 3);
  else if (t < 12) tilt = 30;
  else tilt = 30 * (1 - ease((t - 12) / 2));
  if (t >= 3 && t < 9) turn = 360 * ((t - 3) / 6) * 1.5;      // 1.5 auger turns
  else if (t >= 9) turn = 540;
  if (t >= 9 && t < 12) {                                       // 4 taps, 0.75 s apart
    const k = (t - 9) % 0.75;
    tap = k < 0.08 ? D.stroke * (k / 0.08) : k < 0.3 ? D.stroke * (1 - (k - 0.08) / 0.22) : 0;
  }
  return { tilt, turn, tap };
}

function pose(m, tilt, turn, tap) {
  const X = [1, 0, 0], Y = [0, 1, 0];
  const own = new Set([...D.auger_parts, "stepper_pinion", ...D.plunger]);
  for (const p of D.auger_parts) m.get(p).rotate(Y, turn, D.outlet);
  m.get("stepper_pinion").rotate(Y, -D.stepper_ratio * turn, D.stepper_axis);
  for (const p of D.plunger) {
    const d = D.plunger_dir;
    m.get(p).translate([d[0] * tap, d[1] * tap, d[2] * tap]);
  }
  for (const p of D.tilt_parts) m.get(p).rotate(X, tilt, D.hinge);
  for (const p of D.pinion_pos) m.get(p).rotate(X, -D.servo_ratio * tilt, D.pinion_pos_axis);
  for (const p of D.pinion_neg) m.get(p).rotate(X, -D.servo_ratio * tilt, D.pinion_neg_axis);
  void own;
}

function assemblyAt(t, m) {
  for (const s of D.steps) {
    const s0 = s.t0, s1 = s.t0 + s.move;
    for (const p of s.parts) {
      if (t < s0) { m.get(p).visible(false); continue; }
      const k = 1 - ease((t - s0) / (s1 - s0));
      if (k > 0) m.get(p).translate([s.dir[0] * k, s.dir[1] * k, s.dir[2] * k]);
    }
  }
}

const assemblyEnd = D.steps.length ? Math.max(...D.steps.map((s) => s.t0 + s.move + s.hold)) : 1;

export const clips = {
  motion: {
    label: "Tilt, turn, tap",
    duration: 14,
    loop: true,
    update(t, m) {
      const s = motionState(t);
      pose(m, s.tilt, s.turn, s.tap);
    },
  },
  assembly: {
    label: "Assembly, step by step",
    duration: assemblyEnd,
    loop: false,
    update(t, m) { assemblyAt(t, m); },
  },
};
"""
