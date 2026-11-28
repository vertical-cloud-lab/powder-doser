"""SOP 9: blade spreading on a coupon (SPEC 9)."""

import numpy as np

from ..analysis import spread
from .common import check, dose_to, floats

NUMBER, NAME, TITLE = 9, "spread", "Blade spreading"
COUPON_MM = (100.0, 30.0)


def add_args(p):
    p.add_argument("--gap-mm", type=float, default=0.15)
    p.add_argument("--speeds", default="10,30,100", help="blade mm/s")
    p.add_argument("--coupon", choices=("steel", "PLA"), default="steel")
    p.add_argument("--line-g", type=float, default=0.3)
    p.add_argument("--layers", type=int, default=3, help="layers per speed")
    p.add_argument("--rho-true", type=float, default=None, help="true (skeletal) density, kg/m3")
    p.add_argument("--travel-mm", type=float, default=95.0)
    p.add_argument("--tilt", type=float, default=45.0)


def run(ctx, a):
    if ctx.world:
        ctx.world.set_scene("spread", coupon=a.coupon)
    ctx.env("start")
    acc = ctx.acc
    if acc is None:
        raise SystemExit("spreading needs the accessory Pico (stage)")
    acc.call("light on", check=False)
    acc.call("stage home")
    if acc.wait_done("stage_home", 120) is None:
        raise RuntimeError("stage did not home")
    ctx.prompt("Set the blade gap to {:g} mm with feeler gauges at both ends".format(a.gap_mm))
    ctx.doser.tilt(a.tilt)
    area = COUPON_MM[0] * COUPON_MM[1]
    st = ctx.log.stream("layers", ["speed", "layer", "line_g", "layer_g", "coverage", "streak_frac", "saturated"])
    rows = []
    for v in floats(a.speeds):
        for k in range(1, a.layers + 1):
            ctx.prompt("Clean {} coupon on the balance".format(a.coupon), action="clean_coupon")
            ctx.doser.tare()
            line, _ = dose_to(ctx, a.line_g, tol_g=0.03, settle_s=1.0)
            ctx.prompt("Move the coupon into the spreading bed, line at the blade side", action="coupon_off")
            acc.call("stage move {:g} speed={:g}".format(a.travel_mm, v))
            acc.wait_done("stage", a.travel_mm / v + 10)
            if ctx.world:
                ctx.world.operator("spread_done", speed=v)
            img = ctx.camera("silhouette").capture()
            ctx.log.image("v{:g}_layer{}".format(v, k), img)
            acc.call("stage move 0 speed=20")
            acc.wait_done("stage", 30)
            mask = spread.covered_mask(img)
            cov = spread.coverage(mask)
            sfrac, n_st = spread.streaks(mask)
            sat = spread.saturated_fraction(img)
            ctx.prompt("Lift the coupon back onto the balance", action="coupon_on")
            layer = ctx.weigh()
            row = {"speed": v, "layer": k, "line_g": line, "layer_g": layer, "coverage": cov, "streak_frac": sfrac,
                   "streaks": n_st, "saturated": sat, "brightness_cv": spread.brightness_cv(img, mask),
                   "areal_mass_g_m2": spread.areal_mass_g_m2(layer, area)}
            if a.rho_true:
                row["packing_fraction"] = spread.packing_fraction(layer, area, a.gap_mm, a.rho_true, cov)
            if ctx.world:
                row["sim_truth"] = dict(ctx.world.s["truth"])
            rows.append(row)
            st.write([v, k, line, layer, cov, sfrac, sat])
    by_speed = {}
    for r in rows:
        by_speed.setdefault(r["speed"], []).append(r)
    summary = {str(v): {"coverage_mean": float(np.mean([r["coverage"] for r in rs])),
                        "coverage_range": float(np.ptp([r["coverage"] for r in rs])),
                        "streak_frac_mean": float(np.mean([r["streak_frac"] for r in rs])),
                        "areal_mass_g_m2": float(np.mean([r["areal_mass_g_m2"] for r in rs])),
                        "packing_fraction": float(np.mean([r["packing_fraction"] for r in rs]))
                        if a.rho_true else None} for v, rs in by_speed.items()}
    res = {"layers": rows, "by_speed": summary, "gap_mm": a.gap_mm, "coupon": a.coupon}
    checks = [
        check("gap checked with feeler gauges", True, a.gap_mm),
        check("line mass 0.2-0.5 g", all(0.2 <= r["line_g"] <= 0.5 for r in rows),
              [round(r["line_g"], 3) for r in rows], "0.2-0.5"),
        check("< 1 % saturated pixels", all(r["saturated"] < 0.01 for r in rows),
              max(r["saturated"] for r in rows), 0.01),
        check("coverage repeatable within +-5 % over the layers",
              all(s["coverage_range"] / 2 <= 0.05 for s in summary.values()),
              [round(s["coverage_range"] / 2, 4) for s in summary.values()], 0.05),
    ]
    return res, checks
