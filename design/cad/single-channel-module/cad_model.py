"""
Parametric CadQuery model of the single-channel powder-doser module ("Idea B"
archetype, §2.2 of design/brainstorming.md).

The module is the unit that gets *replicated N times* around a shared
collection cup to build the full doser. It packages, around one PR-#16
Archimedes auger rotor, the full PR-#25 actuator stack:

  - NEMA 11 bipolar stepper, direct-coupled to the auger via a 5 mm flexible
    shaft coupler (rotates the auger; meters powder by step count)
  - JF-0530B push-pull 5 V solenoid bracketed against a stationary tap
    collar (percussive de-bridging at the dispense end)
  - ERM coin vibration motor adhered to the same stationary tap collar
    (continuous low-amplitude shake)
  - DRV8825, DRV8871, DRV2605L driver carriers on a side electronics tray

The geometry here is *manufacturing intent* — not the same as the
schematic visualization in `design/cad/inward-collection-cup/`. Printable
parts are exported individually as STL; the full assembly (printed parts
+ vendor placeholders) is exported as a single STEP and as isometric /
front / top SVGs/PNGs.

Coordinate frame:
  +Z = up, +X to the right (solenoid side), +Y away from viewer
  Z = 0 at the bottom of the base plate
  All dimensions in millimetres.

Run:
    python cad_model.py
which writes everything into ./renders/ and ./ for the .step / .stl files.
"""

from __future__ import annotations

from pathlib import Path
import math

import cadquery as cq

OUT_DIR = Path(__file__).parent
RENDER_DIR = OUT_DIR / "renders"
STL_DIR = OUT_DIR / "stl"
RENDER_DIR.mkdir(exist_ok=True)
STL_DIR.mkdir(exist_ok=True)


# ============================================================================
# Design constants — single source of truth for the whole module
# (mirrored in sketch_2d.py and quoted in README.md).
# ============================================================================

# --- Auger rotor (from cad/auger/archimedes-auger.scad v4, PR #16) ---------
AUGER_OD = 25.0
AUGER_LEN = 250.0
AUGER_EXIT_HOLE_D = 3.0
AUGER_M3_BOSS_R = 4.0       # central spindle boss radius at the top cap
AUGER_M3_BOSS_H = 6.0       # boss height above the top cap
AUGER_TOP_CAP_H = 6.0

# --- NEMA 11 bipolar stepper (PR #25 item 10) -----------------------------
# 28 mm faceplate, ~45 mm body length, 5 mm shaft, 4× M2.5 on 23 mm bolt
# circle (NEMA 11 standard), 22 mm faceplate boss.
NEMA11_FACE = 28.0
NEMA11_BODY_L = 45.0
NEMA11_SHAFT_D = 5.0
NEMA11_SHAFT_L = 20.0
NEMA11_BOSS_D = 22.0
NEMA11_BOSS_H = 1.5
NEMA11_BOLT_PCD = 23.0

# --- 5 mm <-> M3 flexible shaft coupler (PR #25 item 12) -------------------
COUPLER_OD = 14.0
COUPLER_L = 25.0

# --- JF-0530B push-pull solenoid (PR #25 item 4) ---------------------------
SOL_W = 9.6     # X
SOL_H = 19.0    # Y (long axis perpendicular to plunger)
SOL_L = 22.0    # plunger axis
SOL_PLUNGER_D = 4.0
SOL_PLUNGER_STROKE = 4.5
SOL_FLANGE_T = 1.0     # mounting flange (the JF-0530B has 2× M2 mounting
                       # tabs; modelled as a thin plate on the back face)

# --- ERM coin vibration motor (PR #25 item 2) ------------------------------
ERM_D = 10.0
ERM_T = 2.7

# --- Driver-carrier breakouts (PR #25 items 1, 5, 11) ----------------------
DRV8825_W, DRV8825_H, DRV8825_T = 20.0, 15.5, 8.0
DRV8871_W, DRV8871_H, DRV8871_T = 21.0, 17.0, 8.0
DRV2605L_W, DRV2605L_H, DRV2605L_T = 18.0, 20.0, 8.0

# --- Module frame (printed) ------------------------------------------------
PLATE_W = 80.0           # base / top plate footprint (square)
PLATE_T = 6.0
POST_OD = 10.0
POST_BORE_D = 4.4        # M4 clearance bore through the printed posts
POST_INSET = 8.0         # corner post centre is INSET in from plate edge
EXIT_GAP = 8.0           # bottom of auger rotor sits this high above plate
                         # top — leaves room for the collection cup rim
EXIT_CLEARANCE_HOLE_D = 30.0   # base plate clearance hole around the
                               # rotor's bottom + falling powder column

# Tap collar: stationary ring around the rotor near the dispense end. The
# solenoid taps it on +X, the ERM coin is glued to it on -X. Sized for
# ~1 mm radial clearance to the rotor so the collar can vibrate without
# binding the rotor.
COLLAR_OD = 40.0
COLLAR_ID = AUGER_OD + 2.0
COLLAR_H = 22.0
COLLAR_Z0 = PLATE_T + EXIT_GAP + 4.0   # collar bottom 4 mm above rotor bottom

# Solenoid bracket wing on +X face of collar
SOL_WING_W = 30.0   # along Y
SOL_WING_T = 4.0    # along X (wall thickness)
SOL_WING_H = SOL_H + 4.0
SOL_BOLT_PITCH = 14.0   # M2 mounting holes 14 mm apart (matches JF-0530B
                        # mounting flange spacing)

# ERM mounting pad on -X face of collar — just a flat with a shallow recess
ERM_RECESS_DEPTH = 0.6
ERM_PAD_W = 14.0
ERM_PAD_H = 14.0
ERM_PAD_T = 2.0      # flat thickness sticking out from collar OD

# Top plate hosts the NEMA 11; cut-outs:
#   - central hole 22 mm Ø for stepper boss
#   - 4× M2.5 clearance (Ø3 mm) on 23 mm BHC for stepper bolts
TOP_PLATE_BORE = NEMA11_BOSS_D + 1.0
NEMA11_BOLT_CLEAR_D = 3.0

# Module total height: base + post + top, sized so the stepper face-down
# bolts to the top plate and the coupler bridges down to the auger M3 boss.
# Z layout (top of base plate at Z=PLATE_T):
#   rotor bottom (exit) at:     Z = PLATE_T + EXIT_GAP
#   rotor top cap top at:       Z = PLATE_T + EXIT_GAP + AUGER_LEN
#   M3 boss top at:             Z = PLATE_T + EXIT_GAP + AUGER_LEN + AUGER_M3_BOSS_H
#   coupler top at:             Z = PLATE_T + EXIT_GAP + AUGER_LEN + AUGER_M3_BOSS_H + COUPLER_L
#   stepper face plane at:      Z = coupler_top + small_clearance  (top of top plate)
COUPLER_TOP_CLEAR = 2.0
TOP_PLATE_TOP_Z = (
    PLATE_T + EXIT_GAP + AUGER_LEN + AUGER_M3_BOSS_H + COUPLER_L + COUPLER_TOP_CLEAR
)
TOP_PLATE_BOT_Z = TOP_PLATE_TOP_Z - PLATE_T
POST_LEN = TOP_PLATE_BOT_Z - PLATE_T

# Electronics tray: side panel mounted to the +Y face of the corner posts
TRAY_W = 70.0
TRAY_H = 100.0
TRAY_T = 3.0
TRAY_Z0 = PLATE_T + 60.0   # well above the collar / solenoid envelope


# ============================================================================
# Helpers
# ============================================================================

def _corner_xy():
    """Return the (x, y) of the four corner posts."""
    a = PLATE_W / 2 - POST_INSET
    return [(+a, +a), (-a, +a), (-a, -a), (+a, -a)]


# ============================================================================
# Printed parts
# ============================================================================

def make_base_plate() -> cq.Workplane:
    """Square base plate with central exit hole, corner post bores, and
    two M3 mounting bosses for the tap collar."""
    bp = (
        cq.Workplane("XY")
        .box(PLATE_W, PLATE_W, PLATE_T, centered=(True, True, False))
        .faces(">Z")
        .workplane()
        .hole(EXIT_CLEARANCE_HOLE_D)
    )
    # Corner post bores (M4 clearance)
    bp = (
        bp.faces(">Z")
        .workplane()
        .pushPoints(_corner_xy())
        .hole(POST_BORE_D)
    )
    # Tap-collar mounting bosses on +Y and -Y near the centre
    boss_offsets = [(0, +(COLLAR_OD / 2 + 5)), (0, -(COLLAR_OD / 2 + 5))]
    bp = (
        bp.faces(">Z")
        .workplane()
        .pushPoints(boss_offsets)
        .circle(3.5)
        .extrude(4.0)
    )
    bp = (
        bp.faces(">Z")
        .workplane()
        .pushPoints(boss_offsets)
        .hole(2.6)   # M3 self-tap pilot
    )
    return bp


def make_top_plate() -> cq.Workplane:
    """Top plate carrying the NEMA 11 stepper (bolts down through the
    plate; faceplate boss recesses into the central bore)."""
    tp = (
        cq.Workplane("XY")
        .workplane(offset=TOP_PLATE_BOT_Z)
        .box(PLATE_W, PLATE_W, PLATE_T, centered=(True, True, False))
        .faces(">Z")
        .workplane()
        .hole(TOP_PLATE_BORE)
    )
    # Corner post bores
    tp = (
        tp.faces(">Z")
        .workplane()
        .pushPoints(_corner_xy())
        .hole(POST_BORE_D)
    )
    # NEMA 11 mounting holes on 23 mm bolt circle
    bolt_xy = [
        (+NEMA11_BOLT_PCD / 2, +NEMA11_BOLT_PCD / 2),
        (-NEMA11_BOLT_PCD / 2, +NEMA11_BOLT_PCD / 2),
        (-NEMA11_BOLT_PCD / 2, -NEMA11_BOLT_PCD / 2),
        (+NEMA11_BOLT_PCD / 2, -NEMA11_BOLT_PCD / 2),
    ]
    tp = (
        tp.faces(">Z")
        .workplane()
        .pushPoints(bolt_xy)
        .hole(NEMA11_BOLT_CLEAR_D)
    )
    return tp


def make_corner_post() -> cq.Workplane:
    """Single corner post — Ø POST_OD column, axial M4 clearance bore."""
    post = (
        cq.Workplane("XY")
        .workplane(offset=PLATE_T)
        .circle(POST_OD / 2)
        .extrude(POST_LEN)
        .faces(">Z")
        .workplane(invert=True)
        .hole(POST_BORE_D)
    )
    return post


def make_tap_collar() -> cq.Workplane:
    """Stationary ring around the rotor's dispense end. Hosts the
    solenoid bracket on +X and the ERM coin pad on -X."""
    body = (
        cq.Workplane("XY")
        .workplane(offset=COLLAR_Z0)
        .circle(COLLAR_OD / 2)
        .circle(COLLAR_ID / 2)
        .extrude(COLLAR_H)
    )

    # Solenoid wing on +X
    wing = (
        cq.Workplane("XY")
        .workplane(offset=COLLAR_Z0 + (COLLAR_H - SOL_WING_H) / 2)
        .moveTo(COLLAR_OD / 2 - 0.5, -SOL_WING_W / 2)
        .rect(SOL_WING_T + 0.5, SOL_WING_W, centered=False)
        .extrude(SOL_WING_H)
    )
    # The plunger tip pokes through the wing to reach the rotor wall;
    # cut a clearance hole for the plunger to pass through.
    plunger_cz = COLLAR_Z0 + COLLAR_H / 2
    wing = (
        wing.faces(">X")
        .workplane(centerOption="CenterOfBoundBox")
        .center(0, plunger_cz - (COLLAR_Z0 + COLLAR_H / 2))
        .hole(SOL_PLUNGER_D + 1.5)
    )
    # 2× M2 solenoid mounting holes on the wing
    wing = (
        wing.faces(">X")
        .workplane(centerOption="CenterOfBoundBox")
        .pushPoints([(+SOL_BOLT_PITCH / 2, 0), (-SOL_BOLT_PITCH / 2, 0)])
        .hole(2.4)   # M2 clearance
    )

    # ERM coin pad on -X
    pad = (
        cq.Workplane("XY")
        .workplane(offset=COLLAR_Z0 + (COLLAR_H - ERM_PAD_H) / 2)
        .moveTo(-COLLAR_OD / 2 - ERM_PAD_T + 0.5, -ERM_PAD_W / 2)
        .rect(ERM_PAD_T, ERM_PAD_W, centered=False)
        .extrude(ERM_PAD_H)
    )
    # Shallow circular recess on the -X face for the ERM coin
    pad = (
        pad.faces("<X")
        .workplane(centerOption="CenterOfBoundBox")
        .hole(ERM_D + 0.4, ERM_RECESS_DEPTH)
    )

    collar = body.union(wing).union(pad)

    # 2× M3 mounting bosses underneath, mating the base-plate bosses
    boss_xy = [(0, +(COLLAR_OD / 2 + 5)), (0, -(COLLAR_OD / 2 + 5))]
    foot = (
        cq.Workplane("XY")
        .workplane(offset=COLLAR_Z0 - 4.0)
        .pushPoints(boss_xy)
        .circle(3.5)
        .extrude(4.0)
        .faces(">Z")
        .workplane()
        .pushPoints(boss_xy)
        .hole(3.2)   # M3 clearance
    )
    return collar.union(foot)


def make_electronics_tray() -> cq.Workplane:
    """Side panel hosting the three driver carriers. Bolts to the +Y
    face of the +Y corner posts via two 'C' clamps printed in.
    Modelled as a flat plate with PCB-mounting hole patterns; the
    clamp brackets are simplified into two side ribs."""
    plate = (
        cq.Workplane("YZ")
        .workplane(offset=PLATE_W / 2 - POST_INSET + POST_OD / 2)
        .moveTo(-TRAY_W / 2, TRAY_Z0)
        .rect(TRAY_W, TRAY_H, centered=False)
        .extrude(TRAY_T)
    )
    # Side ribs that hook around the +Y posts
    rib_xy = [(+(PLATE_W / 2 - POST_INSET), 0), (-(PLATE_W / 2 - POST_INSET), 0)]
    for x_post, _ in rib_xy:
        rib = (
            cq.Workplane("XY")
            .workplane(offset=TRAY_Z0)
            .moveTo(x_post - 6, PLATE_W / 2 - POST_INSET - 1)
            .rect(12, 8, centered=False)
            .extrude(TRAY_H)
        )
        plate = plate.union(rib)
    return plate


# ============================================================================
# Vendor / placeholder solids
# ============================================================================

def make_auger_envelope() -> cq.Workplane:
    """Solid-cylinder envelope of the PR-#16 v4 auger rotor (the real
    helical geometry lives in cad/auger/archimedes-auger.scad — the
    envelope here is for fit-checking only)."""
    z0 = PLATE_T + EXIT_GAP
    body = (
        cq.Workplane("XY")
        .workplane(offset=z0)
        .circle(AUGER_OD / 2)
        .extrude(AUGER_LEN)
    )
    # Conical bottom funnel + exit hole (for visual)
    bottom_cap = (
        cq.Workplane("XY")
        .workplane(offset=z0)
        .circle(AUGER_EXIT_HOLE_D / 2)
        .extrude(-2.0)
    )
    # M3 boss above the top cap
    boss = (
        cq.Workplane("XY")
        .workplane(offset=z0 + AUGER_LEN)
        .circle(AUGER_M3_BOSS_R)
        .extrude(AUGER_M3_BOSS_H)
    )
    return body.union(boss).union(bottom_cap)


def make_coupler() -> cq.Workplane:
    z0 = PLATE_T + EXIT_GAP + AUGER_LEN + AUGER_M3_BOSS_H
    return (
        cq.Workplane("XY")
        .workplane(offset=z0)
        .circle(COUPLER_OD / 2)
        .extrude(COUPLER_L)
    )


def make_stepper() -> cq.Workplane:
    """NEMA 11 stepper sitting *on top of* the top plate, faceplate
    bolted down to it; shaft pokes down through the plate into the
    coupler."""
    face_z = TOP_PLATE_TOP_Z
    body = (
        cq.Workplane("XY")
        .workplane(offset=face_z)
        .box(NEMA11_FACE, NEMA11_FACE, NEMA11_BODY_L, centered=(True, True, False))
    )
    boss = (
        cq.Workplane("XY")
        .workplane(offset=face_z - NEMA11_BOSS_H)
        .circle(NEMA11_BOSS_D / 2)
        .extrude(NEMA11_BOSS_H)
    )
    shaft = (
        cq.Workplane("XY")
        .workplane(offset=face_z - NEMA11_SHAFT_L)
        .circle(NEMA11_SHAFT_D / 2)
        .extrude(NEMA11_SHAFT_L)
    )
    return body.union(boss).union(shaft)


def make_solenoid() -> cq.Workplane:
    """JF-0530B solenoid sitting on the +X face of the tap-collar wing,
    plunger pointing in -X (towards the rotor wall)."""
    cz = COLLAR_Z0 + COLLAR_H / 2
    # Body sits with its back face flush on the wing's +X face.
    wing_x = COLLAR_OD / 2 + SOL_WING_T
    body = (
        cq.Workplane("YZ")
        .workplane(offset=wing_x)
        .moveTo(-SOL_H / 2, cz - SOL_W / 2)
        .rect(SOL_H, SOL_W, centered=False)
        .extrude(SOL_L)
    )
    # Plunger pokes inward through the wing
    plunger = (
        cq.Workplane("XY")
        .workplane(offset=cz - SOL_PLUNGER_D / 2)
        .moveTo(wing_x - SOL_PLUNGER_STROKE - 2, 0)
        .circle(SOL_PLUNGER_D / 2)
        .extrude(SOL_PLUNGER_D)
    )
    return body


def make_erm() -> cq.Workplane:
    """ERM coin glued to the -X pad on the tap collar."""
    cz = COLLAR_Z0 + COLLAR_H / 2
    px = -(COLLAR_OD / 2 + ERM_PAD_T + ERM_T / 2)
    return (
        cq.Workplane("YZ")
        .workplane(offset=px - ERM_T / 2)
        .moveTo(0, cz)
        .circle(ERM_D / 2)
        .extrude(ERM_T)
    )


def _pcb(w, h, t, name="pcb"):
    return cq.Workplane("XY").box(w, h, t, centered=(True, True, False))


def make_drivers():
    """Three driver carriers laid out on the electronics tray (+Y face)."""
    tray_y = PLATE_W / 2 - POST_INSET + POST_OD / 2 + TRAY_T  # outer face
    tray_z = TRAY_Z0
    parts = []
    # Place along Z, centred on the tray width (X)
    layout = [
        ("DRV8825", DRV8825_W, DRV8825_H, DRV8825_T, tray_z + 12),
        ("DRV8871", DRV8871_W, DRV8871_H, DRV8871_T, tray_z + 12 + DRV8825_H + 8),
        ("DRV2605L", DRV2605L_W, DRV2605L_H, DRV2605L_T, tray_z + 12 + DRV8825_H + 8 + DRV8871_H + 8),
    ]
    for name, w, h, t, z0 in layout:
        pcb = (
            cq.Workplane("XZ")
            .workplane(offset=tray_y + t / 2)
            .moveTo(0, z0 + h / 2)
            .rect(w, h)
            .extrude(t, both=True)
        )
        parts.append((name, pcb))
    return parts


# ============================================================================
# Assembly
# ============================================================================

base_plate = make_base_plate()
top_plate = make_top_plate()
post = make_corner_post()
collar = make_tap_collar()
tray = make_electronics_tray()

auger = make_auger_envelope()
coupler = make_coupler()
stepper = make_stepper()
solenoid = make_solenoid()
erm = make_erm()
drivers = make_drivers()

asm = cq.Assembly(name="single_channel_module")

# Printed parts (shown in PETG/PLA-like colour)
PRINTED = cq.Color(0.85, 0.85, 0.90)
asm.add(base_plate, name="base_plate", color=PRINTED)
asm.add(top_plate, name="top_plate", color=PRINTED)
for i, (x, y) in enumerate(_corner_xy()):
    asm.add(post.translate((x, y, 0)), name=f"corner_post_{i+1}", color=PRINTED)
asm.add(collar, name="tap_collar", color=PRINTED)
asm.add(tray, name="electronics_tray", color=cq.Color(0.75, 0.75, 0.85))

# Vendor placeholders
asm.add(auger, name="auger_rotor_envelope_PR16", color=cq.Color(1.0, 0.95, 0.6))
asm.add(coupler, name="flex_coupler_5mm_M3", color=cq.Color(0.6, 0.6, 0.6))
asm.add(stepper, name="NEMA11_stepper", color=cq.Color(0.25, 0.25, 0.28))
asm.add(solenoid, name="JF0530B_solenoid", color=cq.Color(0.4, 0.25, 0.2))
asm.add(erm, name="ERM_coin_vibration", color=cq.Color(0.9, 0.6, 0.2))
for name, p in drivers:
    asm.add(p, name=f"driver_{name}", color=cq.Color(0.15, 0.45, 0.20))


# ============================================================================
# Exports
# ============================================================================

step_path = OUT_DIR / "single_channel_module.step"
asm.save(str(step_path))
print(f"wrote {step_path}")

# STL exports of each printable part (slicer-ready)
for name, part in [
    ("base_plate", base_plate),
    ("top_plate", top_plate),
    ("corner_post", post),
    ("tap_collar", collar),
    ("electronics_tray", tray),
]:
    stl_path = STL_DIR / f"{name}.stl"
    cq.exporters.export(part, str(stl_path), tolerance=0.1, angularTolerance=0.2)
    print(f"wrote {stl_path}")


# Combined solid for clean SVG line work — Assembly SVG export is uglier.
def _union_all(parts):
    out = None
    for p in parts:
        out = p if out is None else out.union(p)
    return out


print("unioning combined solid for SVG renders ...")
combined = _union_all([
    base_plate, top_plate,
    *[post.translate((x, y, 0)) for (x, y) in _corner_xy()],
    collar, tray,
    auger, coupler, stepper, solenoid, erm,
    *[p for _, p in drivers],
])

opts_iso = {
    "width": 1400,
    "height": 1100,
    "marginLeft": 12,
    "marginTop": 12,
    "showAxes": False,
    "projectionDir": (1.4, -1.1, 0.7),
    "strokeWidth": 0.4,
    "strokeColor": (20, 20, 20),
    "hiddenColor": (170, 170, 170),
    "showHidden": True,
}
svg_iso = RENDER_DIR / "single_channel_module_iso.svg"
cq.exporters.export(combined, str(svg_iso), opt=opts_iso)
print(f"wrote {svg_iso}")

opts_front = dict(opts_iso, projectionDir=(0, -1, 0))
svg_front = RENDER_DIR / "single_channel_module_front.svg"
cq.exporters.export(combined, str(svg_front), opt=opts_front)
print(f"wrote {svg_front}")

opts_top = dict(opts_iso, projectionDir=(0, 0, 1))
svg_top = RENDER_DIR / "single_channel_module_top.svg"
cq.exporters.export(combined, str(svg_top), opt=opts_top)
print(f"wrote {svg_top}")

# Side projection (looking down +X) shows the solenoid + ERM stack edge-on
opts_side = dict(opts_iso, projectionDir=(1, 0, 0))
svg_side = RENDER_DIR / "single_channel_module_side.svg"
cq.exporters.export(combined, str(svg_side), opt=opts_side)
print(f"wrote {svg_side}")

print("done.")
