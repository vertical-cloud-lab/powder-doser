#!/usr/bin/env python3
# ================================================================
# Powder Doser -- Auger powder-capacity model (no CAD software)
# ================================================================
#
# Computes the *maximum possible powder volume* of the geared
# Archimedes auger -- the empty (void) space inside the barrel that
# powder can occupy -- for any of the four dispensing-nozzle variants
# from vertical-cloud-lab/powder-doser issue #48 comment 4513155870,
# and for any barrel length.
#
#   1) direct cut-off of the screw to a large open funnel
#   2) screw continues to just before the exit (small funnel)
#   3) direct cut-off of the screw before the shaft tapers
#   4) screw continues AS the shaft tapers (combines 2 + 3)  <-- focus
#
# Method (see ./README.md for the full survey + rationale): the
# auger is a solid of revolution (tube wall, bottom funnel cone,
# central shaft, top cap) plus one helical fin (a flat radial blade
# swept up the shaft).  Every one of those pieces has a cross-section
# that is known in closed form at any height z, so the void area at
# height z is just
#
#     A_void(z) = A_open_bore(z) - A_shaft(z) - A_fin_in_bore(z)
#
# and the capacity is the integral of A_void(z) over the powder-
# holding length of the barrel.  No CAD kernel or mesh is needed; the
# integral is evaluated numerically by thin z-slices.
#
# The geometry constants below are copied verbatim from the OpenSCAD
# sources committed alongside this file:
#     cad/auger-geared/auger-core.scad
#     cad/auger-geared/nozzle-variants.scad
# so this script stands alone and never has to call OpenSCAD.
#
# Validation: `--validate` re-derives the *solid* volume of a test
# print from the same slice model and compares it against the signed
# volume of the committed STL mesh
# (cad/auger-geared/archimedes-auger-test-nozzle<N>.stl).  Agreement
# to <~1 % confirms the geometry model, and therefore the void figure
# that is computed from the identical parameters.
#
# Usage:
#   python3 auger_capacity.py                 # Auger 4 summary + table
#   python3 auger_capacity.py --variant 4 --length 127
#   python3 auger_capacity.py --all           # all four variants
#   python3 auger_capacity.py --validate      # check vs committed STLs
#   python3 auger_capacity.py --csv out.csv   # write V(length) table
# ================================================================

import argparse
import csv
import math
import os
import sys

PI = math.pi

# ----------------------------------------------------------------
# Geometry constants -- from auger-core.scad / nozzle-variants.scad
# ----------------------------------------------------------------
OUTER_R = 12.5            # outer_diameter/2
INNER_R = 10.5            # (outer_diameter - 2*wall_thickness)/2
EXIT_R = 3.0 / 2          # exit_hole_d / 2
BOTTOM_CAP_H = 12.0       # bottom_cap_h (large funnel height)
TOP_CAP_HEIGHT = 6.0      # top_cap_height
SHAFT_R = 4.0             # shaft_r
FIN_THICKNESS = 2.0       # fin_thickness
FIN_PITCH = 10.0          # fin_pitch
FIN_INNER_SINK = 0.4      # fin_inner_sink
FIN_OUTER_SINK = 0.2      # fin_outer_sink
TAPER_TIP_BOTTOM_R = 0.4  # taper_tip_bottom_r (v3/v4 cone tip)
SMALL_FUNNEL_H = 3.0      # small_funnel_h (v2 short funnel)
FUNNEL_TOP_R = INNER_R - 0.5      # cone top radius (10.0 mm)
OUTER_EDGE = INNER_R + FIN_OUTER_SINK  # fin outer edge (10.7 mm)
M3_BOSS_H = 6.0
M3_PILOT_D = 2.5
SLOT_COUNT = 4
SLOT_WIDTH = 4.0
SLOT_LENGTH = 7.0
TEST_PIECE_LENGTH = 90.0  # mm, the printed-test length for variants 1-4

# Height inside the large funnel where the cone radius equals shaft_r
# (auger-core.scad shaft_bottom_z): 12*(4-1.5)/(10-1.5) = 3.529 mm
SHAFT_BOTTOM_Z = BOTTOM_CAP_H * (SHAFT_R - EXIT_R) / (FUNNEL_TOP_R - EXIT_R)

MM3_PER_ML = 1000.0       # 1 mL = 1 cm^3 = 1000 mm^3
MM_PER_IN = 25.4


def _lerp(z, z0, z1, r0, r1):
    return r0 + (r1 - r0) * (z - z0) / (z1 - z0)


def open_bore_radius(z, variant):
    """Open interior radius of the housing (no screw) at height z."""
    if variant == 2:
        # short funnel only SMALL_FUNNEL_H tall; full bore above it
        if z < SMALL_FUNNEL_H:
            return _lerp(z, 0.0, SMALL_FUNNEL_H, EXIT_R, FUNNEL_TOP_R)
        return INNER_R
    # variants 1, 3, 4 share the large PR#16 funnel
    if z < BOTTOM_CAP_H:
        return _lerp(z, 0.0, BOTTOM_CAP_H, EXIT_R, FUNNEL_TOP_R)
    return INNER_R


def shaft_radius(z, variant, total_h):
    """Radius of the central shaft at height z (0 where absent)."""
    top = total_h - TOP_CAP_HEIGHT
    if z > top:
        return 0.0
    if variant == 1:
        return SHAFT_R if z >= SHAFT_BOTTOM_Z else 0.0
    if variant == 2:
        return SHAFT_R if z >= SMALL_FUNNEL_H else 0.0
    # variants 3, 4: conical tip 0..BOTTOM_CAP_H then straight
    if z < BOTTOM_CAP_H:
        return _lerp(z, 0.0, BOTTOM_CAP_H, TAPER_TIP_BOTTOM_R, SHAFT_R)
    return SHAFT_R


def _fin_span(variant, total_h):
    """(z0, z1, inner_edge) of the helical fin for this variant."""
    top = total_h - TOP_CAP_HEIGHT
    if variant == 1:
        return SHAFT_BOTTOM_Z, top, SHAFT_R - FIN_INNER_SINK
    if variant == 2:
        return SMALL_FUNNEL_H, top, SHAFT_R - FIN_INNER_SINK
    if variant == 3:
        return BOTTOM_CAP_H, top, SHAFT_R - FIN_INNER_SINK
    # variant 4: fin follows the cone down to just above the exit
    return 0.5, top, TAPER_TIP_BOTTOM_R


def fin_area_in_bore(z, variant, total_h):
    """Cross-sectional area of the fin blade lying in the *open* bore.

    The fin is a flat radial blade FIN_THICKNESS thick.  Only the part
    that is outside the shaft and inside the housing wall actually
    displaces powder; the inner/outer 'sink' overlaps are absorbed by
    the shaft/wall in the union and do not count twice.
    """
    z0, z1, inner_edge = _fin_span(variant, total_h)
    if not (z0 <= z <= z1):
        return 0.0
    rs = shaft_radius(z, variant, total_h)
    rh = open_bore_radius(z, variant)
    lo = max(inner_edge, rs)
    hi = min(OUTER_EDGE, rh)
    return FIN_THICKNESS * max(0.0, hi - lo)


def powder_capacity_mm3(variant, total_h, dz=0.002):
    """Maximum powder void volume (mm^3) for a barrel of length total_h."""
    n = int(round(total_h / dz))
    top = total_h - TOP_CAP_HEIGHT
    total = 0.0
    for i in range(n):
        z = (i + 0.5) * dz
        if z > top:
            break
        rh = open_bore_radius(z, variant)
        rs = shaft_radius(z, variant, total_h)
        a = PI * rh * rh - PI * rs * rs - fin_area_in_bore(z, variant, total_h)
        total += a * dz
    return total


def linear_model(variant, dz=0.002):
    """Fit V(L) = slope*L + intercept (exact for the straight barrel)."""
    l0, l1 = 60.0, 250.0
    v0 = powder_capacity_mm3(variant, l0, dz)
    v1 = powder_capacity_mm3(variant, l1, dz)
    slope = (v1 - v0) / (l1 - l0)
    intercept = v0 - slope * l0
    return slope, intercept


# ----------------------------------------------------------------
# Scaling / sizing helpers -- "how do we reach a target volume?"
# ----------------------------------------------------------------
# The current Ø25 mm barrel tops out near 67 mL even at 250 mm length
# (length alone is hopeless for a 250 mL goal: 250 mL / 283 mm^3/mm
# ~= 884 mm ~= 35 in).  Capacity instead scales with bore *area*, so
# the practical lever is barrel diameter.  These helpers size the bore
# diameter needed to hit a target volume at a chosen length, holding
# the Ø8 mm shaft, 2 mm fin and 2 mm wall fixed (the parts tied to the
# drive shaft, print strength and tube wall), so they answer
# "what would it take to get to 250 mL without a hopper?".

WALL_THICKNESS = OUTER_R - INNER_R   # 2.0 mm


def straight_slope(bore_r, shaft_r=SHAFT_R, fin_thickness=FIN_THICKNESS):
    """Void volume per mm of straight barrel (mm^3/mm) for a given bore."""
    annulus = PI * (bore_r * bore_r - shaft_r * shaft_r)
    fin = fin_thickness * (bore_r - shaft_r)
    return annulus - fin


def bore_radius_for_target(target_ml, length_mm, shaft_r=SHAFT_R,
                           fin_thickness=FIN_THICKNESS, intercept=None):
    """Bore radius (mm) needed to hold target_ml over a length_mm barrel.

    Inverts the linear straight-barrel model
    ``V = straight_slope(R)*L + intercept`` for R, holding the shaft,
    fin and the Auger-4 end-effect intercept fixed.  The intercept is a
    small (~ -4 mL) funnel/top-cap correction, so the sizing is accurate
    to a few percent -- enough to choose a diameter; confirm the final
    pick by re-running the full slice model on the resized geometry.
    """
    if intercept is None:
        _, intercept = linear_model(4)
    target_mm3 = target_ml * MM3_PER_ML
    slope = (target_mm3 - intercept) / length_mm
    # slope = pi*(R^2 - shaft_r^2) - fin*(R - shaft_r)
    #  =>  pi*R^2 - fin*R - (slope + pi*shaft_r^2 - fin*shaft_r) = 0
    a = PI
    b = -fin_thickness
    c = -(slope + PI * shaft_r * shaft_r - fin_thickness * shaft_r)
    disc = b * b - 4 * a * c
    if disc < 0:
        return None
    return (-b + math.sqrt(disc)) / (2 * a)


def print_sizing_table(target_ml, shaft_r=SHAFT_R):
    """How big must the barrel be (vs length) to reach target_ml?"""
    _, intercept = linear_model(4)
    print(f"Sizing to reach {target_ml:.0f} mL of powder void "
          f"(no hopper) -- bore grows with capacity ~ diameter^2.")
    print(f"  Held fixed: Ø{2 * shaft_r:.0f} mm shaft, "
          f"{FIN_THICKNESS:.0f} mm fin, {WALL_THICKNESS:.0f} mm wall, "
          f"{FIN_PITCH:.0f} mm pitch.\n")
    print(f"  {'length (mm)':>11}  {'length (in)':>11}  "
          f"{'bore Ø (mm)':>11}  {'outer Ø (mm)':>12}  "
          f"{'mL/rev':>7}  {'×Ø25 now':>8}")
    for length in (150, 200, 250, 300, 350):
        rb = bore_radius_for_target(target_ml, float(length), shaft_r,
                                    intercept=intercept)
        if rb is None or rb <= shaft_r:
            print(f"  {length:11.0f}  {length / MM_PER_IN:11.2f}  "
                  f"{'(infeasible)':>11}")
            continue
        outer_d = 2 * rb + 2 * WALL_THICKNESS
        per_rev = straight_slope(rb, shaft_r) * FIN_PITCH / MM3_PER_ML
        ratio = (2 * rb + 2 * WALL_THICKNESS) / (2 * OUTER_R)
        print(f"  {length:11.0f}  {length / MM_PER_IN:11.2f}  "
              f"{2 * rb:11.1f}  {outer_d:12.1f}  "
              f"{per_rev:7.1f}  {ratio:7.2f}×")
    print("\n  Note: capacity grows as the square of the diameter but the "
          "per-revolution\n  dose grows with it too, so a bigger barrel "
          "trades metering resolution for\n  volume (drop the 10 mm pitch "
          "to claw resolution back).  A bigger gear band,\n  bracket bore "
          "and likely a larger motor than the NEMA 11 follow from the "
          "wider tube.")


# ----------------------------------------------------------------
# Solid-volume model (only used by --validate against the STL mesh)
# ----------------------------------------------------------------
def solid_volume_mm3(variant, total_h, dz=0.002):
    """Total printed-solid volume from the same slice model."""
    n = int(round(total_h / dz))
    top = total_h - TOP_CAP_HEIGHT
    m3_pilot_depth = TOP_CAP_HEIGHT + M3_BOSS_H
    total = 0.0
    for i in range(n):
        z = (i + 0.5) * dz
        rh = open_bore_radius(z, variant)
        rs = shaft_radius(z, variant, total_h)
        if z <= top:
            solid = PI * (OUTER_R * OUTER_R - rh * rh) + PI * rs * rs
        else:
            # top cap: full disc minus the four loading slots
            solid = PI * OUTER_R * OUTER_R - SLOT_COUNT * SLOT_LENGTH * SLOT_WIDTH
        # add the fin blade where it sits in the open bore
        solid += fin_area_in_bore(z, variant, total_h)
        # subtract the M3 spindle pilot bore through cap + boss
        if z >= total_h - m3_pilot_depth:
            solid -= PI * (M3_PILOT_D / 2) ** 2
        total += solid * dz
    return total


def stl_signed_volume(path):
    """Signed volume of an ASCII or binary STL (divergence theorem)."""
    import struct
    with open(path, "rb") as f:
        head = f.read(5)
        f.seek(0)
        if head == b"solid":
            text = f.read().decode("ascii", "replace")
            tris = []
            cur = []
            for line in text.splitlines():
                line = line.strip()
                if line.startswith("vertex"):
                    p = line.split()
                    cur.append((float(p[1]), float(p[2]), float(p[3])))
                    if len(cur) == 3:
                        tris.append(cur)
                        cur = []
            if tris:
                return _tri_volume(tris)
            # fall through: header said "solid" but body is binary
            f.seek(0)
        f.read(80)
        (count,) = struct.unpack("<I", f.read(4))
        tris = []
        for _ in range(count):
            f.read(12)  # normal
            v = struct.unpack("<9f", f.read(36))
            tris.append([(v[0], v[1], v[2]), (v[3], v[4], v[5]),
                         (v[6], v[7], v[8])])
            f.read(2)
        return _tri_volume(tris)


def _tri_volume(tris):
    vol = 0.0
    for (ax, ay, az), (bx, by, bz), (cx, cy, cz) in tris:
        # a . (b x c) / 6
        cross = (by * cz - bz * cy, bz * cx - bx * cz, bx * cy - by * cx)
        vol += ax * cross[0] + ay * cross[1] + az * cross[2]
    return vol / 6.0


# ----------------------------------------------------------------
# Reporting helpers
# ----------------------------------------------------------------
VARIANT_DESC = {
    1: "direct cut-off into a large open funnel",
    2: "screw continues to just before the exit (small funnel)",
    3: "direct cut-off before the shaft tapers",
    4: "screw continues as the shaft tapers (combines 2 + 3)",
}


def fmt_capacity(variant, total_h):
    v = powder_capacity_mm3(variant, total_h)
    return v, v / MM3_PER_ML


def print_summary(variant, length, bulk_density):
    v_mm3, v_ml = fmt_capacity(variant, length)
    slope, intercept = linear_model(variant)
    print(f"Auger variant {variant}: {VARIANT_DESC[variant]}")
    print(f"  Barrel length              : {length:.1f} mm "
          f"({length / MM_PER_IN:.2f} in)")
    print(f"  Maximum powder void volume : {v_mm3:.0f} mm^3 = {v_ml:.2f} mL")
    print(f"  Capacity as a function of length (L in mm):")
    print(f"      V(L) = {slope:.3f} * L - {abs(intercept):.0f}   [mm^3]")
    print(f"      i.e. {slope * MM_PER_IN / MM3_PER_ML:.3f} mL per inch "
          f"of barrel above the fixed ends")
    print(f"  Volumetric dose per screw revolution (pitch = "
          f"{FIN_PITCH:.0f} mm):")
    print(f"      {slope * FIN_PITCH:.0f} mm^3/rev = "
          f"{slope * FIN_PITCH / MM3_PER_ML:.3f} mL/rev")
    if bulk_density:
        print(f"  At a powder bulk density of {bulk_density:.2f} g/mL: "
              f"{v_ml * bulk_density:.1f} g held at full pack")


def print_length_table(variant):
    print(f"\nMaximum powder capacity vs barrel length (variant {variant}):")
    print(f"  {'length (mm)':>11}  {'length (in)':>11}  "
          f"{'V (mm^3)':>10}  {'V (mL)':>8}")
    for length in (60, 90, 100, 127, 150, 180, 200, 250):
        v_mm3, v_ml = fmt_capacity(variant, float(length))
        print(f"  {length:11.0f}  {length / MM_PER_IN:11.2f}  "
              f"{v_mm3:10.0f}  {v_ml:8.2f}")


def run_validation():
    here = os.path.dirname(os.path.abspath(__file__))
    print("Validation: slice solid model vs committed STL mesh "
          "(test pieces, L = 90 mm)\n")
    print(f"  {'variant':>7}  {'model (mm^3)':>12}  {'STL (mm^3)':>11}  "
          f"{'error':>7}")
    ok = True
    compared = 0
    for variant in (1, 2, 3, 4):
        stl = os.path.join(
            here, "..", f"archimedes-auger-test-nozzle{variant}.stl")
        model = solid_volume_mm3(variant, TEST_PIECE_LENGTH)
        if not os.path.exists(stl):
            print(f"  {variant:7d}  {model:12.1f}  {'(missing)':>11}  "
                  f"{'--':>7}")
            continue
        mesh = stl_signed_volume(stl)
        err = (model - mesh) / mesh
        if abs(err) > 0.02:
            ok = False
        compared += 1
        print(f"  {variant:7d}  {model:12.1f}  {mesh:11.1f}  "
              f"{err * 100:6.2f}%")
    if compared == 0:
        print("\n  No STL meshes found next to this script (they live with "
              "the auger\n  test pieces in cad/auger-geared/); nothing to "
              "validate against.")
    elif ok:
        print(f"\n  All {compared} compared variant(s) agree to within 2 %.")
    else:
        print("\n  WARNING: a variant disagrees by more than 2 %.")
    return ok


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Maximum powder-capacity model for the geared "
                    "Archimedes auger (no CAD software required).")
    ap.add_argument("--variant", type=int, default=4, choices=(1, 2, 3, 4),
                    help="nozzle variant (default 4)")
    ap.add_argument("--length", type=float, default=127.0,
                    help="barrel length in mm (default 127 mm = 5 in)")
    ap.add_argument("--bulk-density", type=float, default=1.2,
                    help="powder bulk density g/mL for a mass estimate "
                         "(default 1.2, fine NaCl)")
    ap.add_argument("--all", action="store_true",
                    help="summarise all four variants")
    ap.add_argument("--validate", action="store_true",
                    help="check the model against the committed STLs")
    ap.add_argument("--target-ml", type=float, metavar="ML",
                    help="size the bore/length needed to reach ML of void "
                         "(e.g. 250) instead of reporting a fixed barrel")
    ap.add_argument("--csv", metavar="PATH",
                    help="write a V(length) table to PATH")
    args = ap.parse_args(argv)

    if args.validate:
        return 0 if run_validation() else 1

    if args.target_ml:
        print_sizing_table(args.target_ml)
        return 0

    if args.csv:
        with open(args.csv, "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["variant", "length_mm", "length_in",
                        "powder_mm3", "powder_mL"])
            for variant in (1, 2, 3, 4):
                for length in range(40, 261, 5):
                    v_mm3, v_ml = fmt_capacity(variant, float(length))
                    w.writerow([variant, length, round(length / MM_PER_IN, 3),
                                round(v_mm3, 1), round(v_ml, 3)])
        print(f"Wrote {args.csv}")
        return 0

    variants = (1, 2, 3, 4) if args.all else (args.variant,)
    for variant in variants:
        print_summary(variant, args.length, args.bulk_density)
        print()
    print_length_table(args.variant)
    return 0


if __name__ == "__main__":
    sys.exit(main())
