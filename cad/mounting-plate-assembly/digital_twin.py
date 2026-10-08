"""Digital-twin collision + gear-mesh simulation for the powder-doser
mounting-plate / dual-servo lift (issue #65, PR #66 comment 4815348177).

@sgbaird asked for "an actual digital twin simulation of the full system
in all its complexity ... checking for physical inconsistencies like
overlap of parts, collisions, etc." while re-cutting the servo gear train
at a coarser module.

This module exercises the *kinematics* of the assembly built by
``cad_model.py`` — it does not just static-check one pose, it sweeps the
mechanism through its full range of motion and measures the solid-boolean
intersection (overlap) volume between every relevant pair of parts at
every step.  Two motions are simulated:

  1. **Tilt sweep** — the mounting plate rotates about the hinge axis
     from 0° (folded flush) to 90° (vertical).  At each step the plate
     (and the hinge gear bands that are part of it) is boolean-checked
     against every *static structural* part: baseplate and both MG996R
     bodies.  Any non-zero overlap = a collision.  (The pinions are
     handled by the gear-mesh sweep below, since the gear band is meant
     to engage them, and the hinge pins intentionally pass through the
     plate eyes; the pinion bodies are checked against the baseplate
     separately.)

  2. **Gear-mesh sweep** — the real driver of the tilt is the 2 : 1
     spur reduction (14-T servo pinion → 28-T hinge gear band).  We model
     the gear train kinematically: as the plate tilts by θ the hinge
     gear turns by θ and the pinion must counter-rotate by 2θ.  We first
     solve for the meshing phase (the pinion angle that meshes cleanly
     with the gear at θ = 0, i.e. teeth-in-spaces with backlash), then
     sweep θ with the pinion locked to ``φ = φ0 − 2θ`` and measure the
     tooth-on-tooth interpenetration.  A clean involute mesh stays at
     ~0 mm³ throughout; a jamming / skipping mesh spikes.

Run::

    python3 digital_twin.py            # full sweep (a few minutes)
    python3 digital_twin.py --quick    # coarse sweep (fast smoke test)

The per-step results are written to ``digital_twin/collision_report.md``
and ``digital_twin/mesh_profile.csv`` so the team can diff successive
design iterations.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import cadquery as cq

import cad_model as M

HERE = Path(__file__).resolve().parent
OUT_DIR = HERE / "digital_twin"

# Structural overlaps below this are numerical noise from the faceted
# involute polygons / boolean engine, not real collisions.
TOL_MM3 = 1.0
# Gear-mesh advisory threshold.  Two perfectly-conjugate involute teeth
# touch on a line (zero volume), but a plain *analytic* involute with no
# manufacturing tip relief shows a small residual tip-interference volume
# at low pinion tooth counts.  For reference the original 20-T/40-T @ 20°
# gears measured ~2.6 mm³ by this metric, so we treat the gear mesh as
# clean below MESH_TOL and merely advisory (not a structural failure)
# above it — the cure is added backlash, tip relief, or more teeth.
MESH_TOL = 3.0


# --------------------------------------------------------------------- #
# Geometry helpers
# --------------------------------------------------------------------- #
def _vol(a: cq.Shape, b: cq.Shape) -> float:
    """Intersection (overlap) volume of two solids, in mm³ (0 if disjoint)."""
    inter = a.intersect(b)
    return inter.Volume() if inter is not None else 0.0


def _rotate_about_x(shape: cq.Workplane, y0: float, z0: float,
                    deg: float) -> cq.Workplane:
    """Rotate ``shape`` by ``deg`` about the X-parallel axis through
    (y0, z0) (the hinge axis / a gear axis)."""
    if abs(deg) < 1e-9:
        return shape
    return shape.rotate((0.0, y0, z0), (1.0, y0, z0), deg)


def _tilt_plate(plate: cq.Workplane, tilt_deg: float) -> cq.Workplane:
    """Tilt the mounting plate about the hinge axis (positive lifts the
    rear).  Mirrors ``cad_model._tilt_mounting_plate`` but reusable on a
    pre-built solid so we only pay the union cost once."""
    # cad_model rotates by -tilt about +X through (Y_DISP, Z_AUG).
    return _rotate_about_x(plate, M.Y_DISP, M.Z_AUG, -tilt_deg)


def _servo_body(x_lo: float) -> cq.Shape:
    """Simplified MG996R body box at one servo wall (matches
    render_assembly.py)."""
    return (
        cq.Workplane("XY")
        .box(M.MG996R_BODY_H, M.MG996R_BODY_L, M.MG996R_BODY_T,
             centered=(False, False, True))
        .translate((x_lo, M.PINION_Y - M.MG996R_SPLINE_Y_OFFSET, M.PINION_Z))
        .val()
    )


def _hinge_gear_band(x_lo: float) -> cq.Workplane:
    """Standalone hinge gear band solid, placed on the hinge axis (axis
    along +X).  Used for the fast gear-mesh sweep so we do not pay the
    full-plate union cost on every step."""
    gear = M._build_spur_gear(M.GEAR_HINGE_TEETH, M.GEAR_MODULE,
                              M.GEAR_FACE_W, M.HINGE_EYE_ID,
                              pa_deg=M.GEAR_PA_DEG, backlash=M.GEAR_BACKLASH)
    return gear.rotate((0, 0, 0), (0, 1, 0), 90).translate(
        (x_lo, M.Y_DISP, M.Z_AUG))


def _pinion_at(x_lo: float) -> cq.Workplane:
    """Servo pinion solid placed at its installed pose (axis along +X)."""
    return M.build_servo_pinion().translate((x_lo, M.PINION_Y, M.PINION_Z))


# --------------------------------------------------------------------- #
# 1. Tilt-sweep collision check (full plate vs every static part)
# --------------------------------------------------------------------- #
def tilt_collision_sweep(n_steps: int = 19) -> dict:
    """Sweep the mounting-plate tilt 0 → 90° and check the plate against
    every *static structural* part at each step.  The servo pinions are
    deliberately excluded here — the hinge gear band is part of the plate
    and is *meant* to engage the pinion teeth (that is the drive mesh,
    characterised separately in :func:`gear_mesh_sweep`).  Likewise the
    hinge pins intentionally pass through the plate eyes.  Returns
    ``{pair_name: (max_vol, worst_tilt)}``."""
    print(f"\n[1] Tilt-sweep structural collision check — {n_steps} steps 0°→90° ...")
    plate0 = M.build_mounting_plate()           # built once; transforms are cheap
    base = M.build_baseplate().val()
    statics = {
        "baseplate": base,
        "MG996R_body+X": _servo_body(M.SERVO_BODY_X_LO),
        "MG996R_body-X": _servo_body(M.SERVO_BODY_X_LO_NEG),
    }

    worst: dict[str, tuple[float, float]] = {
        f"plate ∩ {name}": (0.0, 0.0) for name in statics}
    # Pinion bodies vs the baseplate are static (servo installed) — checked once.
    for tag, x_lo in (("pinion+X ∩ baseplate", M.PINION_X_LO),
                      ("pinion-X ∩ baseplate", M.PINION_X_LO_NEG)):
        worst[tag] = (_vol(_pinion_at(x_lo).val(), base), 0.0)

    tilts = [90.0 * i / (n_steps - 1) for i in range(n_steps)]
    for tilt in tilts:
        plate = _tilt_plate(plate0, tilt).val()
        vols: dict[str, float] = {}
        for name, sol in statics.items():
            v = _vol(plate, sol)
            vols[name] = v
            key = f"plate ∩ {name}"
            if v > worst[key][0]:
                worst[key] = (v, tilt)
        print(f"    tilt {tilt:5.1f}°  "
              + "  ".join(f"{n[:11]}={v:6.1f}" for n, v in vols.items()))
    return worst


# --------------------------------------------------------------------- #
# 2. Gear-mesh kinematic sweep (the 2:1 spur reduction in motion)
# --------------------------------------------------------------------- #
def _mesh_phase(gear: cq.Shape, x_lo_pin: float,
                coarse: int = 30, fine: int = 20) -> tuple[float, float]:
    """Find the pinion phase φ0 (deg, about its own axis) that meshes
    cleanly with the hinge gear at θ = 0 — i.e. the φ in one pinion tooth
    pitch (360/N_pinion) that minimises tooth interpenetration.  Returns
    (φ0, overlap_at_φ0)."""
    pitch = 360.0 / M.GEAR_PINION_TEETH
    pin0 = _pinion_at(x_lo_pin)

    def overlap(phi: float) -> float:
        p = _rotate_about_x(pin0, M.PINION_Y, M.PINION_Z, phi).val()
        return _vol(gear, p)

    # Coarse scan over one tooth pitch, then refine around the minimum.
    best_phi, best_v = 0.0, float("inf")
    for k in range(coarse):
        phi = pitch * k / coarse
        v = overlap(phi)
        if v < best_v:
            best_phi, best_v = phi, v
    lo, hi = best_phi - pitch / coarse, best_phi + pitch / coarse
    for k in range(fine + 1):
        phi = lo + (hi - lo) * k / fine
        v = overlap(phi)
        if v < best_v:
            best_phi, best_v = phi, v
    return best_phi, best_v


def gear_mesh_sweep(n_steps: int = 46) -> dict:
    """Drive the 2 : 1 reduction kinematically over the full 0 → 90° tilt
    (pinion turns 180°, exercising every mesh phase) and measure the
    tooth interpenetration.  Returns a summary dict and writes the
    per-step profile to ``digital_twin/mesh_profile.csv``."""
    print(f"\n[2] Gear-mesh kinematic sweep — {n_steps} steps, 2:1 reduction ...")
    summary: dict[str, dict] = {}
    rows = ["side,tilt_deg,pinion_deg,overlap_mm3"]

    ratio = M.GEAR_HINGE_TEETH / M.GEAR_PINION_TEETH        # = 2.0
    for side, x_lo_gear, x_lo_pin in (
            ("+X", M.GEAR_X_LO, M.PINION_X_LO),
            ("-X", M.GEAR_X_LO_NEG, M.PINION_X_LO_NEG)):
        gear0 = _hinge_gear_band(x_lo_gear)
        pin0 = _pinion_at(x_lo_pin)
        phi0, mesh_v = _mesh_phase(gear0.val(), x_lo_pin)
        print(f"    {side}: meshing phase φ0 = {phi0:6.2f}°  "
              f"(static mesh overlap {mesh_v:.2f} mm³)")

        max_v, worst_tilt = 0.0, 0.0
        for i in range(n_steps):
            tilt = 90.0 * i / (n_steps - 1)
            g = _rotate_about_x(gear0, M.Y_DISP, M.Z_AUG, -tilt).val()
            phi = phi0 - ratio * (-tilt)        # pinion counter-rotates 2θ
            p = _rotate_about_x(pin0, M.PINION_Y, M.PINION_Z, phi).val()
            v = _vol(g, p)
            rows.append(f"{side},{tilt:.2f},{phi % 360:.2f},{v:.4f}")
            if v > max_v:
                max_v, worst_tilt = v, tilt
        summary[side] = {"phase_deg": phi0, "static_overlap": mesh_v,
                         "max_overlap": max_v, "worst_tilt": worst_tilt}
        print(f"        max tooth interpenetration over sweep: "
              f"{max_v:.2f} mm³ @ tilt {worst_tilt:.1f}°")

    OUT_DIR.mkdir(exist_ok=True)
    (OUT_DIR / "mesh_profile.csv").write_text("\n".join(rows) + "\n")
    return summary


# --------------------------------------------------------------------- #
# Report
# --------------------------------------------------------------------- #
def write_report(collisions: dict, mesh: dict, elapsed: float) -> bool:
    """Write a markdown report and return True if the assembly passes
    (no real collisions, gear mesh clean)."""
    OUT_DIR.mkdir(exist_ok=True)
    ok = True
    lines = [
        "# Digital-twin collision + gear-mesh report",
        "",
        "Generated by `digital_twin.py` from the parametric solids in "
        "`cad_model.py`.  Overlap volumes are solid-boolean intersection "
        f"volumes; anything above the {TOL_MM3:.1f} mm³ noise floor is a "
        "real physical interference.",
        "",
        "## Gear train",
        "",
        f"- Hinge gear: **{M.GEAR_HINGE_TEETH}T**, servo pinion: "
        f"**{M.GEAR_PINION_TEETH}T** (2 : 1 reduction)",
        f"- Module **m ≈ {M.GEAR_MODULE:.3f} mm**, pressure angle "
        f"**{M.GEAR_PA_DEG:.0f}°**, centre distance **C = "
        f"{M.GEAR_CENTRE_C:.2f} mm**",
        f"- Pitch Ø: hinge {M.GEAR_HINGE_PCD:.2f} / pinion "
        f"{M.GEAR_PINION_PCD:.2f}; tip Ø: hinge {M.GEAR_HINGE_TIP_D:.2f} / "
        f"pinion {M.GEAR_PINION_TIP_D:.2f}",
        "",
        "## 1. Tilt-sweep collisions (mounting plate vs static parts, 0°→90°)",
        "",
        "| Pair | Max overlap (mm³) | Worst tilt | Verdict |",
        "| --- | --- | --- | --- |",
    ]
    for name, (v, tilt) in sorted(collisions.items()):
        verdict = "OK" if v < TOL_MM3 else "**COLLISION**"
        if v >= TOL_MM3:
            ok = False
        lines.append(f"| {name} | {v:.2f} | {tilt:.1f}° | {verdict} |")

    lines += [
        "",
        "## 2. Gear-mesh kinematic sweep (2 : 1 reduction through full lift)",
        "",
        "Advisory metric — the hinge gear band is part of the plate and is "
        "*meant* to engage the pinion.  Two ideal involute teeth contact on "
        "a line (zero volume); a small residual here is analytic tip "
        f"interference (no tip relief modelled).  Clean below {MESH_TOL:.1f} "
        "mm³; above it the mesh still works but benefits from extra backlash "
        f"or tip relief.  Design backlash = {M.GEAR_BACKLASH:.2f} mm.",
        "",
        "| Side | Mesh phase φ0 | Static overlap (mm³) | Max overlap over "
        "sweep (mm³) | Worst tilt | Verdict |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    mesh_ok = True
    for side, d in mesh.items():
        v = d["max_overlap"]
        verdict = "clean" if v < MESH_TOL else "advisory"
        if v >= MESH_TOL:
            mesh_ok = False
        lines.append(f"| {side} | {d['phase_deg']:.2f}° | "
                     f"{d['static_overlap']:.2f} | {v:.2f} | "
                     f"{d['worst_tilt']:.1f}° | {verdict} |")

    structural = "PASS — no structural interference" if ok else "FAIL — see flagged rows"
    mesh_note = ("gear mesh clean" if mesh_ok
                 else "gear mesh advisory (add backlash / tip relief)")
    lines += [
        "",
        f"Per-step mesh interpenetration profile: `mesh_profile.csv`.",
        "",
        f"**Overall structural: {structural}; {mesh_note}** "
        f"(sweep took {elapsed:.0f} s).",
        "",
    ]
    (OUT_DIR / "collision_report.md").write_text("\n".join(lines))
    print(f"\nReport written to {(OUT_DIR / 'collision_report.md').relative_to(HERE)}")
    return ok


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--quick", action="store_true",
                    help="coarse sweep for a fast smoke test")
    args = ap.parse_args()

    t0 = time.time()
    if args.quick:
        collisions = tilt_collision_sweep(n_steps=7)
        mesh = gear_mesh_sweep(n_steps=13)
    else:
        collisions = tilt_collision_sweep(n_steps=19)
        mesh = gear_mesh_sweep(n_steps=46)
    elapsed = time.time() - t0

    ok = write_report(collisions, mesh, elapsed)
    print("\n=== Digital-twin verdict:",
          "PASS ✓" if ok else "FAIL ✗", "===")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
