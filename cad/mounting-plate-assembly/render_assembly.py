"""Assembly-level diagrams for the mounting-plate sub-system.

Produces (under assembly/):

* assembly_iso.png, assembly_front.png, assembly_side.png, assembly_top.png
  — full assembly with all parts placed (mounting plate + baseplate + auger +
  brackets + tap-collar mount + NEMA + linear actuator + hinge pin + cup +
  scale).

* installation_diagram.png — top-down view with every mounting hole labelled
  (NEMA mount, bracket-front mount, bracket-rear mount, tap-collar mount,
  hinge eyes, actuator lug).  Matplotlib annotation.

* rotation_0_45_90.png — three side views showing the assembly tilted by 0,
  45 and 90 degrees about the hinge axis (driven by linear-actuator length).

* powder_flow.png — side view with arrows tracing powder from inside the
  auger to the cup on the scale.
"""
from __future__ import annotations

import math
from pathlib import Path

import cadquery as cq
import matplotlib.pyplot as plt
import numpy as np
import vtk

import cad_model
from cad_model import P, HINGE_Z

ASM_DIR = Path(__file__).resolve().parent / "assembly"
ASM_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Build a placed assembly as a dict of named CadQuery shapes.
# All placements use the global frame defined in cad_model.py:
#   * Mounting-plate top surface at Z=0 (when tilt=0).
#   * Hinge axis = X direction through (0, plateLen/2 + yokeArmLen, HINGE_Z)
#     i.e. at the dispense-hole position.

def _translate(part, dx, dy, dz):
    return part.translate((dx, dy, dz))


def _rotate_about_hinge(part, tilt_deg):
    """Rotate a CadQuery Workplane about the hinge axis (X, through dispense pt)."""
    hinge_y = P["plateLen"] / 2 + P["yokeArmLen"]
    hinge_z = HINGE_Z
    pivot = cq.Vector(0, hinge_y, hinge_z)
    axis = cq.Vector(1, 0, 0)
    return part.rotate(pivot, pivot + axis, tilt_deg)


def build_assembly(tilt_deg: float = 0.0) -> dict:
    """Return ``{name: cq.Workplane}`` of the assembly tilted by tilt_deg
    about the hinge axis."""
    p = P

    mp = cad_model.mounting_plate()
    bp = cad_model.baseplate()
    aug = cad_model.auger_placeholder()
    brkF = cad_model.bracket_placeholder()
    brkR = cad_model.bracket_placeholder()
    tap = cad_model.tap_collar_mount_placeholder()
    nema = cad_model.nema17_placeholder()
    cup = cad_model.cup_placeholder()
    scale = cad_model.scale_placeholder()
    pin = cad_model.hinge_pin()
    act = cad_model.linear_actuator()

    # Position everything in the MOUNTING-PLATE-LOCAL frame first (tilt=0).
    # Auger: along +Y from 0 to augerLen, but it should sit BELOW the plate
    # such that the dispense hole at (0, augerLen-dispOffset, 0) — in auger
    # local coords — lines up with the hinge point at
    # (0, plateLen/2 + yokeArmLen, HINGE_Z).
    aug_target_y = p["plateLen"] / 2 + p["yokeArmLen"]
    # In cad_model.py the auger was extruded along -Y (Y∈[-augerLen, 0]) with
    # the dispense hole at local Y = augerLen - dispOffset of the extruded
    # interval — actually let's just translate so the +Y tip of the auger
    # (which is at local y=0) lands at aug_target_y + dispOffset.
    aug_placed = _translate(aug,
                            0,
                            aug_target_y + p["dispOffset"],
                            HINGE_Z)

    # Brackets: bracket plate built at Z∈[0, brkPlateT], collar Z∈[-collarH, 0].
    # We want the bracket plate TOP to sit against the mounting plate UNDERSIDE
    # (Z=-plateT), so we translate the whole bracket down by (-plateT - brkPlateT).
    # Then collar centre lands at Z = -plateT - brkPlateT - collarH/2 = -16
    # which exactly equals HINGE_Z, so the auger sits in the collars.
    brk_dz = -p["plateT"] - p["brkPlateT"]
    brkF_placed = _translate(brkF, 0, p["brkFrontY"], brk_dz)
    brkR_placed = _translate(brkR, 0, p["brkRearY"], brk_dz)

    # Tap collar mount plate: same mounting convention (plate top against
    # mounting-plate underside), so translate down by (-plateT - brkPlateT).
    tap_placed = _translate(tap, 0, p["tapPlateY"], brk_dz)

    # NEMA 17 motor: body hangs below the plate, shaft pokes up THROUGH the
    # plate via the pilot hole.  Body top sits at Z = -plateT.
    nema_placed = _translate(nema, 0, p["nemaCentreY"], -p["plateT"])

    # Hinge pin: passes along X through both yoke eyes AND the central
    # baseplate clevis tang.  Pin axis = X, at Y=eyeY, Z=HINGE_Z.
    # The pin geometry (built in cad_model.hinge_pin) is a YZ-plane circle
    # extruded in +X (length = yokeEyeGap + 2*yokeEyeOd + 2 ≈ 54 mm) — we
    # translate it so its centre lands at the eye Y/Z and X≈-(pinLen/2).
    pin_len = p["yokeEyeGap"] + 2 * p["yokeEyeOd"] + 2.0
    pin_placed = _translate(pin, -pin_len / 2, aug_target_y, HINGE_Z)

    # Everything above tilts together about the hinge.
    tilted = {}
    for name, part in (
        ("mounting_plate", mp),
        ("auger", aug_placed),
        ("bracket_front", brkF_placed),
        ("bracket_rear", brkR_placed),
        ("tap_collar_mount", tap_placed),
        ("nema17", nema_placed),
        ("hinge_pin", pin_placed),
    ):
        tilted[name] = _rotate_about_hinge(part, tilt_deg)

    # Baseplate placement: we want the clevis bore (local Z = baseT + clevisH/2)
    # to land at world Z = HINGE_Z so the hinge pin passes cleanly through
    # both yoke eyes AND the central tang.  So dz = HINGE_Z - (baseT + clevisH/2).
    bp_dz = HINGE_Z - (p["baseT"] + p["clevisH"] / 2)
    bp_top_z = p["baseT"] + bp_dz                  # absolute Z of baseplate top
    bp_placed = _translate(bp, 0, 0, bp_dz)
    tilted["baseplate"] = bp_placed

    # Cup + scale sit on the FLOOR (= bottom of the legs).
    floor_z = bp_dz - p["legH"]
    scale_placed = scale.translate((0, aug_target_y, floor_z))
    tilted["scale"] = scale_placed
    cup_z = floor_z + 29.0  # scale body 25 + platter 4
    cup_placed = cup.translate((0, aug_target_y, cup_z))
    tilted["cup"] = cup_placed

    # Linear actuator placeholder: drawn at its tilt=0 pose.  The rear pin is
    # at (0, actBaseY, bp_top_z + actClevisH - 4); we just place the body so
    # its base sits on the baseplate rear clevis.
    act_base_x = 0
    act_base_y = p["actBaseY"]
    act_base_z = bp_top_z + 14.0  # sits on the rear clevis ear
    act_placed = act.translate((act_base_x, act_base_y, act_base_z))
    tilted["actuator"] = act_placed

    return tilted


# ---------------------------------------------------------------------------
# 3-D rendering via VTK.

PART_COLOURS = {
    "mounting_plate": (0.45, 0.65, 0.85),
    "baseplate": (0.85, 0.70, 0.45),
    "auger": (0.75, 0.75, 0.78),
    "bracket_front": (0.55, 0.85, 0.55),
    "bracket_rear": (0.55, 0.85, 0.55),
    "tap_collar_mount": (0.92, 0.62, 0.50),
    "nema17": (0.30, 0.30, 0.30),
    "hinge_pin": (0.95, 0.85, 0.30),
    "actuator": (0.50, 0.40, 0.55),
    "cup": (0.95, 0.95, 0.95),
    "scale": (0.20, 0.20, 0.20),
}


def _vtk_actor(shape, colour):
    pd = shape.toVtkPolyData(tolerance=0.15, angularTolerance=0.4)
    mp = vtk.vtkPolyDataMapper()
    mp.SetInputData(pd)
    a = vtk.vtkActor()
    a.SetMapper(mp)
    a.GetProperty().SetColor(*colour)
    a.GetProperty().SetSpecular(0.2)
    return a


def render_assembly_vtk(parts: dict, out_path: Path, *, view: str = "iso",
                        size=(1400, 1000)) -> None:
    ren = vtk.vtkRenderer()
    ren.SetBackground(1, 1, 1)
    overall_bb = None
    for name, wp in parts.items():
        shape = wp.val()
        ren.AddActor(_vtk_actor(shape, PART_COLOURS.get(name, (0.7, 0.7, 0.7))))
        bb = shape.BoundingBox()
        if overall_bb is None:
            overall_bb = [bb.xmin, bb.xmax, bb.ymin, bb.ymax, bb.zmin, bb.zmax]
        else:
            overall_bb[0] = min(overall_bb[0], bb.xmin)
            overall_bb[1] = max(overall_bb[1], bb.xmax)
            overall_bb[2] = min(overall_bb[2], bb.ymin)
            overall_bb[3] = max(overall_bb[3], bb.ymax)
            overall_bb[4] = min(overall_bb[4], bb.zmin)
            overall_bb[5] = max(overall_bb[5], bb.zmax)

    cx = (overall_bb[0] + overall_bb[1]) / 2
    cy = (overall_bb[2] + overall_bb[3]) / 2
    cz = (overall_bb[4] + overall_bb[5]) / 2
    diag = math.sqrt(
        (overall_bb[1] - overall_bb[0]) ** 2
        + (overall_bb[3] - overall_bb[2]) ** 2
        + (overall_bb[5] - overall_bb[4]) ** 2
    )

    cam = ren.GetActiveCamera()
    cam.SetFocalPoint(cx, cy, cz)
    cam.SetPosition(cx, cy - diag * 1.5, cz)
    cam.SetViewUp(0, 0, 1)
    if view == "iso":
        cam.Azimuth(40); cam.Elevation(28)
    elif view == "front":
        pass
    elif view == "top":
        cam.SetPosition(cx, cy, cz + diag * 1.5); cam.SetViewUp(0, 1, 0)
    elif view == "side":
        cam.SetPosition(cx + diag * 1.5, cy, cz); cam.SetViewUp(0, 0, 1)
    ren.ResetCameraClippingRange()

    for pos in ((1, -1, 1.0), (-1, -1, 0.4), (0, 1, 0.4)):
        light = vtk.vtkLight()
        light.SetPosition(cx + pos[0] * diag,
                          cy + pos[1] * diag,
                          cz + pos[2] * diag)
        light.SetFocalPoint(cx, cy, cz)
        light.SetIntensity(0.55)
        ren.AddLight(light)

    win = vtk.vtkRenderWindow()
    win.SetOffScreenRendering(1)
    win.AddRenderer(ren)
    win.SetSize(*size)
    win.Render()

    w2i = vtk.vtkWindowToImageFilter()
    w2i.SetInput(win)
    w2i.Update()
    writer = vtk.vtkPNGWriter()
    writer.SetFileName(str(out_path))
    writer.SetInputConnection(w2i.GetOutputPort())
    writer.Write()
    print(f"  wrote {out_path.relative_to(out_path.parent.parent)}")


# ---------------------------------------------------------------------------
# Matplotlib-based 2D diagrams.

def _draw_plate_top(ax):
    """Top-down outline of the mounting plate + every mounting-hole label."""
    p = P
    # Plate outline (rounded rectangle approximated by lines).
    w, l = p["plateWidth"], p["plateLen"]
    rect = plt.Rectangle((-w / 2, -l / 2), w, l, fill=False, lw=1.5,
                         edgecolor="#1f3a68")
    ax.add_patch(rect)

    # Yoke arms + eyes.
    armOffsetX = p["yokeEyeGap"] / 2 + p["yokeEyeOd"] / 2
    eyeY = l / 2 + p["yokeArmLen"]
    for sx in (+armOffsetX, -armOffsetX):
        ax.add_patch(plt.Rectangle((sx - p["yokeEyeOd"] / 2, l / 2 - 2),
                                   p["yokeEyeOd"], p["yokeArmLen"] + 2,
                                   fill=False, lw=1.2, edgecolor="#1f3a68"))
        ax.add_patch(plt.Circle((sx, eyeY), p["yokeEyeOd"] / 2, fill=False,
                                lw=1.2, edgecolor="#1f3a68"))
        ax.add_patch(plt.Circle((sx, eyeY), p["yokeEyeId"] / 2, fill=False,
                                lw=1.0, edgecolor="#9b1c1c"))
        ax.annotate(f"Hinge eye ({'+' if sx>0 else '−'}X)",
                    xy=(sx, eyeY), xytext=(sx + (12 if sx > 0 else -50), eyeY + 6),
                    fontsize=7, color="#9b1c1c",
                    arrowprops=dict(arrowstyle="->", color="#9b1c1c", lw=0.6))

    # Powder-fall slot.
    slotW = p["yokeEyeGap"]
    slotL = 35.0
    ax.add_patch(plt.Rectangle((-slotW / 2, l / 2 - slotL - 1),
                               slotW, slotL + 1, fill=True,
                               facecolor="#fff3c4", edgecolor="#a4810a",
                               lw=0.8, hatch="...", alpha=0.6))
    ax.text(0, l / 2 - slotL / 2, "powder\nslot", ha="center", va="center",
            fontsize=7, color="#5c4a06")

    # Bracket, tap-collar, NEMA hole patterns.
    def _holes(cy, hx, hy, d, label, colour):
        for sy in (-hy / 2, +hy / 2):
            for sx in (-hx / 2, +hx / 2):
                ax.add_patch(plt.Circle((sx, cy + sy), d / 2, fill=True,
                                        facecolor=colour, edgecolor="k", lw=0.4))
        ax.annotate(label, xy=(hx / 2, cy + hy / 2),
                    xytext=(hx / 2 + 8, cy + hy / 2 + 5),
                    fontsize=7, color="#1f3a68",
                    arrowprops=dict(arrowstyle="->", color="#1f3a68", lw=0.5))

    _holes(p["brkFrontY"], p["brkHoleSpanX"], p["brkHoleSpanY"], p["m3Clear"],
           "Bracket FRONT — 4× M3 (#46)", "#8fcf8f")
    _holes(p["brkRearY"], p["brkHoleSpanX"], p["brkHoleSpanY"], p["m3Clear"],
           "Bracket REAR — 4× M3 (#46)", "#8fcf8f")
    _holes(p["tapPlateY"], p["brkHoleSpanX"], p["brkHoleSpanY"], p["m3Clear"],
           "Tap-collar mount — 4× M3 (#50)", "#e8a07c")

    # NEMA 17.
    for sy in (-p["nemaHoleSpan"] / 2, +p["nemaHoleSpan"] / 2):
        for sx in (-p["nemaHoleSpan"] / 2, +p["nemaHoleSpan"] / 2):
            ax.add_patch(plt.Circle((sx, p["nemaCentreY"] + sy), p["m3Clear"] / 2,
                                    fill=True, facecolor="#888", edgecolor="k", lw=0.4))
    ax.add_patch(plt.Circle((0, p["nemaCentreY"]), p["nemaPilotDia"] / 2,
                            fill=False, lw=1.0, edgecolor="#444",
                            linestyle="--"))
    ax.annotate("NEMA 17 — 4× M3 + Ø22.5 pilot",
                xy=(p["nemaHoleSpan"] / 2, p["nemaCentreY"] + p["nemaHoleSpan"] / 2),
                xytext=(p["nemaHoleSpan"] / 2 + 8, p["nemaCentreY"] + p["nemaHoleSpan"] / 2 + 4),
                fontsize=7, color="#1f3a68",
                arrowprops=dict(arrowstyle="->", color="#1f3a68", lw=0.5))

    # Actuator lug (drawn as small rectangle on underside; show centre as ring).
    ax.add_patch(plt.Circle((0, p["actRodPlateY"]), 1.6, fill=False,
                            edgecolor="#5b3a8b", lw=1.0))
    ax.annotate("Actuator rod-end pivot (M5)",
                xy=(0, p["actRodPlateY"]), xytext=(8, p["actRodPlateY"] - 4),
                fontsize=7, color="#5b3a8b",
                arrowprops=dict(arrowstyle="->", color="#5b3a8b", lw=0.5))

    # Axis arrows.
    ax.annotate("", xy=(40, -90), xytext=(28, -90),
                arrowprops=dict(arrowstyle="->", color="k"))
    ax.text(42, -90, "+X", fontsize=8, va="center")
    ax.annotate("", xy=(28, -78), xytext=(28, -90),
                arrowprops=dict(arrowstyle="->", color="k"))
    ax.text(28, -76, "+Y (auger)", fontsize=8, ha="center")


def installation_diagram(out_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(8, 12))
    _draw_plate_top(ax)
    ax.set_aspect("equal")
    ax.set_xlim(-90, 90)
    ax.set_ylim(-110, 140)
    ax.set_title("Mounting plate — installation diagram (top view)\n"
                 "Issue #56 (powder-doser).  Holes labelled by mating part.")
    ax.set_xlabel("X (mm) — perpendicular to auger")
    ax.set_ylabel("Y (mm) — along auger axis")
    ax.grid(True, alpha=0.2)
    fig.tight_layout()
    fig.savefig(out_path, dpi=140)
    plt.close(fig)
    print(f"  wrote {out_path.relative_to(out_path.parent.parent)}")


# ---- rotation 0/45/90 ----

def _draw_side(ax, tilt_deg: float):
    """Schematic side (XZ) view of the assembly tilted by tilt_deg."""
    p = P
    hinge_y = p["plateLen"] / 2 + p["yokeArmLen"]
    hinge_z = HINGE_Z

    # Baseplate (fixed).
    bp_dz = HINGE_Z - (p["baseT"] + p["clevisH"] / 2)
    bp_top_z = p["baseT"] + bp_dz
    bp_bot_z = bp_dz
    floor_z = bp_dz - p["legH"]
    ax.add_patch(plt.Rectangle((-p["baseLen"] / 2, bp_bot_z),
                               p["baseLen"], p["baseT"],
                               fill=True, facecolor="#e7c889",
                               edgecolor="#7a5a1f", lw=1.0))
    # Legs (front & rear pair, projected).
    ax.add_patch(plt.Rectangle((p["baseLen"] / 2 - p["legT"], floor_z),
                               p["legT"], p["legH"],
                               fill=True, facecolor="#e7c889",
                               edgecolor="#7a5a1f", lw=0.8))
    ax.add_patch(plt.Rectangle((-p["baseLen"] / 2, floor_z),
                               p["legT"], p["legH"],
                               fill=True, facecolor="#e7c889",
                               edgecolor="#7a5a1f", lw=0.8))
    # Hinge clevis (single tang).
    clev_y_extent = p["clevisRoot"]
    ax.add_patch(plt.Rectangle((hinge_y - clev_y_extent / 2, bp_top_z),
                               clev_y_extent, p["clevisH"],
                               fill=True, facecolor="#cfa86a",
                               edgecolor="#7a5a1f", lw=0.8))

    # Mounting plate as a thin slab in the Y-Z plane, pivoted about hinge.
    # Plate footprint in Y: [-plateLen/2, +plateLen/2] (before yoke arms),
    # but the dispense end where the yoke meets the hinge axis is at +Y.
    # Z: top at 0, bottom at -plateT.
    plate_pts = np.array([
        [-p["plateLen"] / 2,       0],
        [+p["plateLen"] / 2,       0],
        [+p["plateLen"] / 2 + p["yokeArmLen"], 0],
        [+p["plateLen"] / 2 + p["yokeArmLen"], -p["plateT"]],
        [+p["plateLen"] / 2,      -p["plateT"]],
        [-p["plateLen"] / 2,      -p["plateT"]],
    ])
    # Auger: cylinder centred along Y axis below plate.
    aug_pts = np.array([
        [-(p["augerLen"] - p["dispOffset"]) + hinge_y,        hinge_z - p["augerOd"] / 2],
        [hinge_y + p["dispOffset"],                            hinge_z - p["augerOd"] / 2],
        [hinge_y + p["dispOffset"],                            hinge_z + p["augerOd"] / 2],
        [-(p["augerLen"] - p["dispOffset"]) + hinge_y,        hinge_z + p["augerOd"] / 2],
    ])
    # NEMA body (square in side view).
    nema_pts = np.array([
        [p["nemaCentreY"] - p["nemaBody"] / 2, -p["plateT"] - 42],
        [p["nemaCentreY"] + p["nemaBody"] / 2, -p["plateT"] - 42],
        [p["nemaCentreY"] + p["nemaBody"] / 2, -p["plateT"]],
        [p["nemaCentreY"] - p["nemaBody"] / 2, -p["plateT"]],
    ])

    def rot_pts(pts):
        ang = math.radians(-tilt_deg)  # positive tilt = nose up (rotate about +X axis)
        c, s = math.cos(ang), math.sin(ang)
        out = []
        for y, z in pts:
            dy, dz = y - hinge_y, z - hinge_z
            ry = c * dy - s * dz + hinge_y
            rz = s * dy + c * dz + hinge_z
            out.append((ry, rz))
        return np.array(out)

    plate_r = rot_pts(plate_pts)
    aug_r   = rot_pts(aug_pts)
    nema_r  = rot_pts(nema_pts)

    ax.add_patch(plt.Polygon(plate_r, closed=True, facecolor="#a9c6e8",
                             edgecolor="#1f3a68", lw=1.0))
    ax.add_patch(plt.Polygon(aug_r, closed=True, facecolor="#cccccc",
                             edgecolor="#444", lw=0.8))
    ax.add_patch(plt.Polygon(nema_r, closed=True, facecolor="#444",
                             edgecolor="#000", lw=0.6))

    # Hinge centre marker.
    ax.plot(hinge_y, hinge_z, "o", color="#9b1c1c", ms=6)

    # Cup & scale on the floor (centred at hinge Y).
    ax.add_patch(plt.Rectangle((hinge_y - 50, floor_z), 100, 25,
                               fill=True, facecolor="#222", lw=0.6))
    ax.add_patch(plt.Rectangle((hinge_y - 19, floor_z + 29), 38, 45,
                               fill=True, facecolor="#eeeeee",
                               edgecolor="#444", lw=0.6))

    # Linear actuator as a line from baseplate rear clevis to mounting-plate
    # actuator lug (after tilt).
    act_base = np.array([p["actBaseY"], bp_top_z + 14.0])
    lug_local = np.array([p["actRodPlateY"], -p["plateT"] - 16 + 5])
    lug_world = rot_pts(np.array([lug_local]))[0]
    ax.plot([act_base[0], lug_world[0]], [act_base[1], lug_world[1]],
            color="#5b3a8b", lw=3.5, solid_capstyle="round")
    ax.plot([act_base[0], lug_world[0]], [act_base[1], lug_world[1]],
            color="#cdb6e0", lw=1.5)
    L = math.hypot(lug_world[0] - act_base[0], lug_world[1] - act_base[1])
    ax.annotate(f"actuator L = {L:.0f} mm",
                xy=((act_base[0] + lug_world[0]) / 2,
                    (act_base[1] + lug_world[1]) / 2),
                xytext=(8, 8), textcoords="offset points",
                fontsize=7, color="#5b3a8b")

    ax.set_title(f"Tilt = {tilt_deg:.0f}°")
    ax.set_xlabel("Y (mm)")
    ax.set_ylabel("Z (mm)")
    ax.set_aspect("equal")
    ax.set_xlim(-140, 170)
    ax.set_ylim(floor_z - 8, 200)
    ax.grid(True, alpha=0.2)


def rotation_diagram(out_path: Path) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(18, 7))
    for ax, tilt in zip(axes, (0.0, 45.0, 90.0)):
        _draw_side(ax, tilt)
    fig.suptitle("Rotation about the hinge axis (= auger dispense axis), "
                 "driven by the linear actuator.\n"
                 "0° → auger horizontal,   90° → auger vertical (powder column straight down).",
                 fontsize=11)
    fig.tight_layout()
    fig.savefig(out_path, dpi=140)
    plt.close(fig)
    print(f"  wrote {out_path.relative_to(out_path.parent.parent)}")


def powder_flow_diagram(out_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(9, 9))
    _draw_side(ax, 35.0)
    p = P
    hinge_y = p["plateLen"] / 2 + p["yokeArmLen"]
    floor_z = HINGE_Z - p["clevisH"] - p["baseT"] - p["legH"]

    # Arrows: along auger (powder transported), through dispense hole, down
    # through baseplate window, into cup.
    ax.annotate("", xy=(hinge_y - 5, HINGE_Z),
                xytext=(p["nemaCentreY"] + 30, HINGE_Z - 6),
                arrowprops=dict(arrowstyle="->", color="#0a6e1f", lw=2.5,
                                connectionstyle="arc3,rad=-0.15"))
    ax.text(p["nemaCentreY"] + 50, HINGE_Z - 22,
            "1) powder driven\nalong auger\nby rotation", fontsize=8,
            color="#0a6e1f")

    ax.annotate("", xy=(hinge_y, HINGE_Z - 25),
                xytext=(hinge_y, HINGE_Z + 2),
                arrowprops=dict(arrowstyle="->", color="#0a6e1f", lw=2.5))
    ax.text(hinge_y + 4, HINGE_Z - 14,
            "2) falls through dispense\nhole + yoke gap", fontsize=8,
            color="#0a6e1f")

    ax.annotate("", xy=(hinge_y, floor_z + 30),
                xytext=(hinge_y, HINGE_Z - 28),
                arrowprops=dict(arrowstyle="->", color="#0a6e1f", lw=2.5))
    ax.text(hinge_y + 4, (HINGE_Z + floor_z) / 2,
            "3) baseplate window\n→ cup on scale", fontsize=8, color="#0a6e1f")

    ax.set_title("Powder flow: auger → dispense hole → yoke slot → baseplate\n"
                 "window → cup on scale.  Path is unobstructed at every tilt.")
    fig.tight_layout()
    fig.savefig(out_path, dpi=140)
    plt.close(fig)
    print(f"  wrote {out_path.relative_to(out_path.parent.parent)}")


# ---------------------------------------------------------------------------

def main():
    print("Building tilt=0 assembly ...")
    asm = build_assembly(0.0)

    print("Rendering 3-D views ...")
    render_assembly_vtk(asm, ASM_DIR / "assembly_iso.png",   view="iso")
    render_assembly_vtk(asm, ASM_DIR / "assembly_front.png", view="front")
    render_assembly_vtk(asm, ASM_DIR / "assembly_top.png",   view="top")
    render_assembly_vtk(asm, ASM_DIR / "assembly_side.png",  view="side")

    print("Rendering installation diagram ...")
    installation_diagram(ASM_DIR / "installation_diagram.png")

    print("Rendering rotation diagram ...")
    rotation_diagram(ASM_DIR / "rotation_0_45_90.png")

    print("Rendering powder-flow diagram ...")
    powder_flow_diagram(ASM_DIR / "powder_flow.png")

    print("Exporting tilt=0 assembly STEP ...")
    asm_compound = cq.Compound.makeCompound([w.val() for w in asm.values()])
    cq.exporters.export(cq.Workplane().add(asm_compound),
                        str(ASM_DIR / "full_assembly.step"))
    print(f"  wrote {(ASM_DIR / 'full_assembly.step').relative_to(ASM_DIR.parent)}")


if __name__ == "__main__":
    main()
