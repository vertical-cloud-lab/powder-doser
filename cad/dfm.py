"""Design-for-manufacturing and gantry-kinematics feedback for the CAD model.

This is the closed-loop feedback half of the open CAD pipeline. It reads the
parametric model in :mod:`cad.excavator`, runs a battery of automated checks,
and prints a summary plus a non-zero exit code if any check fails. Each
check is intentionally conservative; the goal is to catch obvious mistakes
the next time a parameter is changed, not to replace a slicer or a real
simulator.

Run from the repo root::

    python -m cad.dfm

Categories of checks:

* **FDM printability** -- min wall thickness, FDM overhang angles
  (cam-ramp slope, rim-lip chamfer), dowel-pin clearance.

* **Gantry-only kinematics** (per the user's hard constraint that the rig
  has only the existing gantry X / Y / Z axes; no second axis on the
  bucket). The dispense cycle has to be achievable with pure carriage
  motion. The two actuator variants are checked separately:

  - **Smooth cam ramp:** (a) the rim lip must be tall enough to engage the
    ramp before the trough body would clash with the ramp's
    base; (b) the cam ramp's angle has to be shallow enough to avoid
    lift-off, but not so shallow that it doesn't fit in the gantry's X
    travel.

  - **Pin-defined slot:** (a) every slot waypoint must lie inside the
    board; (b) the slot path must always be reachable -- i.e. the gantry
    X travel covers the slot's X range; (c) consecutive waypoints must
    not double back in X (which would require negative gantry-X motion
    relative to the schedule -- still legal, but flagged so the user is
    aware that it requires bidirectional gantry motion).

* **Sanity checks** -- positive dimensions, no zero-width arms, etc.

Exit code is 0 if every check passes, 1 if any check fails (i.e. suitable
for use in CI). Warnings do not fail the run.
"""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass

from .excavator import ExcavatorParams


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str
    severity: str = "error"   # "error" or "warning"

    def render(self) -> str:
        marker = {
            ("error", True):    "[OK]   ",
            ("error", False):   "[FAIL] ",
            ("warning", True):  "[OK]   ",
            ("warning", False): "[WARN] ",
        }[(self.severity, self.ok)]
        return f"{marker}{self.name}: {self.detail}"


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------


def _check(name: str, ok: bool, detail: str, severity: str = "error") -> CheckResult:
    return CheckResult(name=name, ok=ok, detail=detail, severity=severity)


def check_sanity(p: ExcavatorParams) -> list[CheckResult]:
    rs: list[CheckResult] = []
    for f in (
        "trough_length", "trough_radius", "trough_wall", "end_cap_thickness",
        "pin_diameter", "arm_thickness", "arm_width", "arm_length",
        "cam_ramp_length", "cam_ramp_rise", "slot_board_length",
        "slot_board_height", "slot_board_thickness",
    ):
        v = getattr(p, f)
        rs.append(_check(
            f"sanity.positive.{f}", v > 0,
            f"{f} = {v} (must be > 0)",
        ))
    return rs


def check_printability(p: ExcavatorParams) -> list[CheckResult]:
    rs: list[CheckResult] = []
    rs.append(_check(
        "fdm.min_wall.trough",
        p.trough_wall >= p.min_wall,
        f"trough_wall = {p.trough_wall:.2f} mm "
        f"(>= min_wall = {p.min_wall:.2f} mm required for FDM)",
    ))
    # Cam-ramp face is at angle atan(rise / length) from horizontal; the
    # printable overhang angle is measured from VERTICAL, so the worst
    # overhang on the ramp's underside is (90 deg - ramp angle). We want
    # the worst overhang to stay <= max_overhang_deg.
    ramp_angle_deg = math.degrees(math.atan2(p.cam_ramp_rise, p.cam_ramp_length))
    underside_overhang = 90.0 - ramp_angle_deg
    rs.append(_check(
        "fdm.overhang.cam_ramp_underside",
        underside_overhang <= p.max_overhang_deg,
        f"cam-ramp underside overhang = {underside_overhang:.1f} deg "
        f"(<= max_overhang_deg = {p.max_overhang_deg:.1f} deg)",
        severity="warning",  # overhangs can be supported, just slower
    ))
    rs.append(_check(
        "fdm.overhang.bumper_chamfer",
        p.bumper_chamfer > 0,
        f"bumper_chamfer = {p.bumper_chamfer:.2f} mm "
        "(must be > 0 to avoid a sharp 90 deg overhang on the rim lip)",
    ))
    rs.append(_check(
        "fdm.pin_clearance.positive",
        p.pin_clearance > 0,
        f"pin_clearance = {p.pin_clearance:.2f} mm "
        "(must be > 0 for the printed pivot hole to slide on the dowel)",
    ))
    return rs


def check_gantry_only_cam_ramp(p: ExcavatorParams) -> list[CheckResult]:
    rs: list[CheckResult] = []
    # The chamfered rim lip must be at least as tall as the ramp's first
    # ~1 mm, otherwise the trough body will hit the ramp's base before the
    # lip engages.
    rs.append(_check(
        "kinematics.cam.bumper_engages_ramp",
        p.bumper_height >= 2.0,
        f"bumper_height = {p.bumper_height:.2f} mm "
        "(rim lip must be >= 2 mm tall to reliably engage the ramp's leading edge)",
    ))
    # Whole cam stroke must fit inside the gantry's X travel.
    rs.append(_check(
        "kinematics.cam.fits_in_x_travel",
        p.cam_ramp_length <= p.gantry_x_travel,
        f"cam_ramp_length = {p.cam_ramp_length} mm "
        f"(<= gantry_x_travel = {p.gantry_x_travel} mm)",
    ))
    # Ramp angle: too steep (> 45 deg from horizontal) and the trough will
    # tend to skip over the bumper on the return stroke; too shallow and the
    # tilt resolution per mm of gantry X is poor.
    ramp_angle_deg = math.degrees(math.atan2(p.cam_ramp_rise, p.cam_ramp_length))
    rs.append(_check(
        "kinematics.cam.angle_in_band",
        15.0 <= ramp_angle_deg <= 45.0,
        f"ramp angle = {ramp_angle_deg:.1f} deg "
        "(15 deg <= angle <= 45 deg for clean engagement and useful resolution)",
        severity="warning",
    ))
    return rs


def check_gantry_only_slot_board(p: ExcavatorParams) -> list[CheckResult]:
    rs: list[CheckResult] = []
    if len(p.slot_path) < 2:
        rs.append(_check(
            "kinematics.slot.has_path",
            False,
            f"slot_path has {len(p.slot_path)} waypoints (need >= 2)",
        ))
        return rs

    # Every waypoint must lie strictly inside the board, with at least
    # slot_width/2 margin to the edges (so the routed slot doesn't break out).
    margin = p.slot_width / 2 + 1.0
    out_of_board: list[tuple[float, float]] = []
    for x, z in p.slot_path:
        if not (margin <= x <= p.slot_board_length - margin and
                margin <= z <= p.slot_board_height - margin):
            out_of_board.append((x, z))
    rs.append(_check(
        "kinematics.slot.waypoints_inside_board",
        not out_of_board,
        ("all waypoints inside the board with margin "
         f"{margin:.1f} mm" if not out_of_board
         else f"out-of-board waypoints: {out_of_board}"),
    ))

    # The slot's X span must fit in the gantry's X travel, since gantry X
    # is what walks the peg through the slot.
    xs = [pt[0] for pt in p.slot_path]
    x_span = max(xs) - min(xs)
    rs.append(_check(
        "kinematics.slot.x_span_in_gantry_travel",
        x_span <= p.gantry_x_travel,
        f"slot X span = {x_span:.1f} mm (<= gantry_x_travel = {p.gantry_x_travel} mm)",
    ))

    # Hard constraint per user comment 4166621470: "we have a gantry system
    # and would like to avoid installing a second axis." The pin-slot
    # actuation mechanism honours this iff the slot is monotonic in X over
    # each stage of the dispense (i.e. the gantry can walk the peg through
    # the slot by pure +X / pure -X motion). We don't require strict
    # monotonicity over the whole path -- multi-stage paths with a reversal
    # are fine -- but we flag any non-monotonic *segment*, since that would
    # require the peg to physically move sideways inside the slot, which is
    # impossible without a second axis on the bucket.
    non_monotonic: list[int] = []
    last_dx_sign = 0
    for i, ((x0, _), (x1, _)) in enumerate(zip(p.slot_path, p.slot_path[1:])):
        dx = x1 - x0
        sign = 0 if dx == 0 else (1 if dx > 0 else -1)
        if sign != 0 and last_dx_sign != 0 and sign != last_dx_sign:
            # Sign reversal between adjacent segments -- record the index of
            # the second of the two segments. This is a *legal* design
            # (the gantry just reverses), so we report it as a warning, not
            # an error.
            non_monotonic.append(i)
        if sign != 0:
            last_dx_sign = sign
    rs.append(_check(
        "kinematics.slot.gantry_x_only",
        not non_monotonic,
        ("slot path requires only gantry-X motion to traverse"
         + (f" (with {len(non_monotonic)} reversal(s) at segment indices {non_monotonic})"
            if non_monotonic else "")),
        severity="warning" if non_monotonic else "error",
    ))

    # The peg must always be reachable: at every X along the slot, the slot
    # must stay within the gantry's Z travel (roughly).
    zs = [pt[1] for pt in p.slot_path]
    z_span = max(zs) - min(zs)
    rs.append(_check(
        "kinematics.slot.z_span_in_gantry_travel",
        z_span <= p.gantry_z_travel,
        f"slot Z span = {z_span:.1f} mm (<= gantry_z_travel = {p.gantry_z_travel} mm)",
    ))

    # Pin-slot friction proxy (Edison v3 sec. 4): sharp corners in the
    # slot path spike the normal force on the peg and bind the mechanism.
    # We measure the largest direction change across any interior
    # waypoint and fail if it exceeds slot_max_corner_deg.
    worst_corner_deg = 0.0
    worst_idx = -1
    for i in range(1, len(p.slot_path) - 1):
        x0, z0 = p.slot_path[i - 1]
        x1, z1 = p.slot_path[i]
        x2, z2 = p.slot_path[i + 1]
        a1 = math.atan2(z1 - z0, x1 - x0)
        a2 = math.atan2(z2 - z1, x2 - x1)
        d = math.degrees(abs(a2 - a1))
        if d > 180.0:
            d = 360.0 - d
        if d > worst_corner_deg:
            worst_corner_deg = d
            worst_idx = i
    rs.append(_check(
        "kinematics.slot.peg_friction.corner_angle",
        worst_corner_deg <= p.slot_max_corner_deg,
        (f"largest slot-path corner = {worst_corner_deg:.1f} deg at waypoint "
         f"{worst_idx} (<= slot_max_corner_deg = {p.slot_max_corner_deg:.1f} deg "
         "to avoid binding the peg)") if worst_idx >= 0
        else "no interior waypoints to evaluate corner angle",
    ))
    return rs


# ---------------------------------------------------------------------------
# Physics-of-mechanism checks (Edison v3 sec. 4)
# ---------------------------------------------------------------------------


def _loaded_cg_y(p: ExcavatorParams) -> tuple[float, float]:
    """Return ``(cg_y_mm, total_mass_g)`` for the loaded trough.

    Treats the half-cylinder shell as a thin-walled half-cylinder (centroid
    at -2 r / pi from the rim), the powder column as a uniform half-disk
    extruded by the cavity length (centroid at -4 r / (3 pi) from the
    rim), and each rim lip as a small rectangular bar at Y ~ +bumper_height/2.
    Densities come from ``p.print_material_density`` and
    ``p.powder_bulk_density`` (g/cm^3); lengths in mm so volumes are in
    mm^3 and masses divided by 1000 give grams.
    """
    r_in = p.trough_radius                           # mm
    r_out = p.trough_radius + p.trough_wall          # mm
    L = p.trough_length                              # mm
    cavity_len = L - 2 * p.end_cap_thickness         # mm
    rho_p = p.print_material_density / 1000.0        # g/mm^3
    rho_pw = p.powder_bulk_density / 1000.0          # g/mm^3

    # Thin-walled half-cylinder shell, full length L.
    shell_vol = 0.5 * math.pi * (r_out ** 2 - r_in ** 2) * L
    shell_cg_y = -2 * ((r_out + r_in) / 2) / math.pi  # ~ -2 r_mean / pi
    # End caps (two thin half-disks at +/- L/2). Their CG is the half-disk
    # centroid at -4 r_out / (3 pi).
    cap_vol = 2 * 0.5 * math.pi * r_out ** 2 * p.end_cap_thickness
    cap_cg_y = -4 * r_out / (3 * math.pi)
    # Powder column: uniform half-disk of inner radius r_in extruded by
    # cavity length.
    powder_vol = 0.5 * math.pi * r_in ** 2 * cavity_len
    powder_cg_y = -4 * r_in / (3 * math.pi)
    # Two rim lips along the full length L. Each lip is a bumper_width x
    # bumper_height x L bar. The chamfer trims a corner, but for the CG
    # estimate we approximate the lip as a solid bar centred at
    # Y = bumper_height/2.
    lip_vol = 2 * (p.bumper_width * p.bumper_height * L)
    lip_cg_y = p.bumper_height / 2.0
    # Pivot bosses (two short cylinders, axis along Z) at Y = pivot_offset_y.
    boss_vol = 2 * math.pi * (p.pivot_boss_diameter / 2) ** 2 * p.pivot_boss_thickness
    boss_cg_y = p.pivot_offset_y

    pieces = [
        (shell_vol, shell_cg_y, rho_p),
        (cap_vol, cap_cg_y, rho_p),
        (lip_vol, lip_cg_y, rho_p),
        (boss_vol, boss_cg_y, rho_p),
        (powder_vol, powder_cg_y, rho_pw),
    ]
    total_m = sum(v * rho for v, _, rho in pieces)
    if total_m <= 0:
        return (0.0, 0.0)
    cg_y = sum(v * rho * y for v, y, rho in pieces) / total_m
    return (cg_y, total_m)


def check_pendulum_stability(p: ExcavatorParams) -> list[CheckResult]:
    """The loaded CG must sit BELOW the pivot for a stable pendulum."""
    cg_y, mass_g = _loaded_cg_y(p)
    margin = p.pivot_offset_y - cg_y  # positive => pivot above CG => stable
    return [_check(
        "physics.pendulum.cg_below_pivot",
        margin > 0.5,
        (f"loaded CG at Y = {cg_y:+.2f} mm, pivot at Y = {p.pivot_offset_y:+.2f} mm, "
         f"margin = {margin:+.2f} mm (need pivot >= 0.5 mm above CG for a "
         f"stable pendulum; loaded mass ~ {mass_g:.1f} g)"),
    )]


def _cam_lever_arm(p: ExcavatorParams) -> float:
    """Distance from the pivot pin to the outer corner of the rim lip.

    The cam ramp pushes on the outer-top corner of one rim lip; the
    moment arm for the cam reaction is the distance from that corner to
    the pivot. Used for both the sensitivity and the rise-utilisation
    checks below.
    """
    outer_r = p.trough_radius + p.trough_wall
    lip_outer_x = outer_r + p.bumper_width
    lip_outer_y = p.bumper_height
    return math.hypot(lip_outer_x, lip_outer_y - p.pivot_offset_y)


def check_cam_sensitivity(p: ExcavatorParams) -> list[CheckResult]:
    """Cam tilt sensitivity d(theta)/d(X) must stay finite at the target tilt.

    Modelling the lip's outer corner as a point on a rigid lever of
    length ``R`` rotating about the pivot, the horizontal contact
    point with the ramp moves like ``X(theta) = R * sin(theta + phi0)``
    where ``phi0`` is the lever's initial angle from horizontal. So
    ``dX/dtheta = R * cos(theta + phi0)`` and the sensitivity
    ``dtheta/dX = 1 / (R * cos(theta + phi0))`` blows up to infinity
    as the lever passes vertical. (Edison v3 sec. 1 "Cam Singularity".)
    """
    outer_r = p.trough_radius + p.trough_wall
    lip_outer_x = outer_r + p.bumper_width
    lip_outer_y = p.bumper_height
    R = _cam_lever_arm(p)
    phi0 = math.atan2(lip_outer_y - p.pivot_offset_y, lip_outer_x)
    target = math.radians(p.cam_target_tilt_deg)
    cos_term = math.cos(target + phi0)
    if cos_term <= 0:
        return [_check(
            "physics.cam.sensitivity",
            False,
            (f"cam lever passes vertical before reaching target tilt "
             f"{p.cam_target_tilt_deg:.0f} deg (lever R = {R:.1f} mm, "
             f"initial phi0 = {math.degrees(phi0):.1f} deg); sensitivity is "
             "infinite (snap-through singularity)"),
        )]
    sens_deg_per_mm = math.degrees(1.0 / (R * cos_term))
    return [_check(
        "physics.cam.sensitivity",
        sens_deg_per_mm <= p.cam_sensitivity_ceiling_deg_per_mm,
        (f"cam dtheta/dX at target tilt {p.cam_target_tilt_deg:.0f} deg = "
         f"{sens_deg_per_mm:.2f} deg/mm (<= "
         f"{p.cam_sensitivity_ceiling_deg_per_mm:.1f} deg/mm; lever R = "
         f"{R:.1f} mm)"),
    )]


def check_cam_rise_utilisation(p: ExcavatorParams) -> list[CheckResult]:
    """The configured ramp rise must not exceed what the lever can lift.

    Over a 0->target_tilt sweep, the lip's outer corner rises by
    ``R * (sin(target + phi0) - sin(phi0))``. If ``cam_ramp_rise``
    exceeds this, the extra material is unreachable -- the ramp is
    physically taller than the cam can ride up. (Edison v3 sec. 1 -- the
    20 mm cam_ramp_rise was wasted because the lever could only lift
    ~9.5 mm.)
    """
    outer_r = p.trough_radius + p.trough_wall
    lip_outer_x = outer_r + p.bumper_width
    lip_outer_y = p.bumper_height
    R = _cam_lever_arm(p)
    phi0 = math.atan2(lip_outer_y - p.pivot_offset_y, lip_outer_x)
    target = math.radians(p.cam_target_tilt_deg)
    max_rise = R * (math.sin(target + phi0) - math.sin(phi0))
    if max_rise <= 0:
        return [_check(
            "physics.cam.rise_utilisation",
            False,
            (f"cam lever cannot lift over a 0 -> {p.cam_target_tilt_deg:.0f} deg "
             f"sweep (R = {R:.1f} mm, phi0 = {math.degrees(phi0):.1f} deg)"),
        )]
    return [_check(
        "physics.cam.rise_utilisation",
        p.cam_ramp_rise <= max_rise + 0.5,
        (f"cam_ramp_rise = {p.cam_ramp_rise:.1f} mm vs max achievable rise "
         f"= {max_rise:.1f} mm at target tilt {p.cam_target_tilt_deg:.0f} deg "
         "(extra ramp height above this is unreachable)"),
        severity="warning",
    )]


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def run_all(p: ExcavatorParams | None = None) -> list[CheckResult]:
    p = p or ExcavatorParams()
    return (
        check_sanity(p)
        + check_printability(p)
        + check_gantry_only_cam_ramp(p)
        + check_gantry_only_slot_board(p)
        + check_pendulum_stability(p)
        + check_cam_sensitivity(p)
        + check_cam_rise_utilisation(p)
    )


def main() -> int:
    p = ExcavatorParams()
    results = run_all(p)
    for r in results:
        print(r.render())
    n_fail = sum(1 for r in results if not r.ok and r.severity == "error")
    n_warn = sum(1 for r in results if not r.ok and r.severity == "warning")
    print()
    print(f"summary: {len(results)} checks, "
          f"{n_fail} failure(s), {n_warn} warning(s).")
    return 1 if n_fail else 0


if __name__ == "__main__":
    sys.exit(main())
