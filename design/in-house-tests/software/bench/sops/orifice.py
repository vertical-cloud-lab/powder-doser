"""SOP 5: orifice cup (SPEC 5).

Fill the cup to 5 g with the gate shut; open; log the balance; step down
the discs until nothing flows in 60 s; repeat the smallest with taps.
"""

import numpy as np

from ..analysis import orifice
from .common import check, dose_to, floats

NUMBER, NAME, TITLE = 5, "orifice", "Orifice cup"


def add_args(p):
    p.add_argument("--discs", default="6,5.08,4,3,2.54,2,1.5,1", help="mm, largest first")
    p.add_argument("--fill-g", type=float, default=5.0)
    p.add_argument("--no-flow-s", type=float, default=60.0)
    p.add_argument("--tap-rate", type=float, default=60.0, help="taps/min")
    p.add_argument("--tap-s", type=float, default=30.0, help="how long to tap a disc that does not flow")
    p.add_argument("--rho-b", type=float, default=None, help="bulk density, kg/m3 (test 2)")
    p.add_argument("--d50-um", type=float, default=None, help="median size, um (test 4)")
    p.add_argument("--hz", type=float, default=10.0, help="balance polling rate")
    p.add_argument("--lag-s", type=float, default=0.25, help="balance response time (SOP 5 setup)")
    p.add_argument("--tilt", type=float, default=45.0)


def _discharge(ctx, a, fill_g, tapping=False):
    """Stream the balance until the cup is empty, or no_flow_s passes with
    nothing arriving. Returns t, m arrays."""
    t, m = [], []
    t_open = ctx.now()
    limit = a.tap_s if tapping else a.no_flow_s
    while True:
        chunk = ctx.doser.weigh_stream(a.hz, 2.0)
        for ti, g, _ in chunk:
            t.append(ti)
            m.append(g)
        el = ctx.now() - t_open
        got = max(m) - m[0] if m else 0.0
        if got >= 0.97 * fill_g and len(m) > 20 and max(m[-int(2 * a.hz):]) - min(m[-int(2 * a.hz):]) < 0.002:
            break
        if el >= limit and got < 0.05:
            break
        if el >= max(limit, 600.0):
            break
    return np.array(t), np.array(m)


def run(ctx, a):
    discs = sorted(floats(a.discs), reverse=True)
    if ctx.world:
        ctx.world.set_scene("orifice", disc_mm=discs[0])
    ctx.env("start")
    acc = ctx.acc
    if acc is None:
        raise SystemExit("the orifice cup needs the accessory Pico (gate servo, tapper)")
    ctx.doser.tilt(a.tilt)
    bal = ctx.log.stream("balance", ["disc_mm", "tapped", "t", "g"])
    rows = []
    stop_untapped = False
    for D in discs:
        ctx.prompt("Fit the {:g} mm disc; gate shut; empty cup on the pan adapter under the doser".format(D),
                   action="new_disc", disc_mm=D)
        acc.call("gate close")
        acc.wait_done("gate", 5)
        ctx.doser.tare()
        fill, revs = dose_to(ctx, a.fill_g, tol_g=0.05)
        ctx.prompt("Move the cup to its holder on the tripod, over the catch beaker", action="cup_to_holder")
        ctx.doser.tare()
        row = {"disc_mm": D, "fill_g": fill, "fill_revs": revs}
        attempts = [False] if not stop_untapped else []
        attempts.append(True)
        for tapped in attempts:
            if tapped:
                n = int(a.tap_rate * a.tap_s / 60.0)
                acc.call("tap {} rate={:g}".format(n, a.tap_rate))
            acc.call("gate open")
            t, m = _discharge(ctx, a, fill, tapping=tapped)
            acc.call("gate close")
            if tapped:
                acc.call("stop tap", check=False)
            for ti, g in zip(t, m):
                bal.write([D, int(tapped), ti, g])
            ok = orifice.flowed(t, m, 0.05, t[0], a.no_flow_s)
            key = "tapped" if tapped else "untapped"
            row["flowed_" + key] = ok
            if ok:
                try:
                    f = orifice.flow_rate(t, m, lag_s=a.lag_s)
                    row["rate_g_s_" + key] = f.rate_g_s
                    row["fit_" + key] = f.to_dict()
                except ValueError:
                    row["flowed_" + key] = False
            if not tapped and ok:
                break                                       # flowed untapped: no need to tap
            if not tapped and not ok:
                stop_untapped = True
                ctx.prompt("Nothing flowed in {:g} s; refill the cup on the balance for the tapped try".format(
                    a.no_flow_s), action="new_disc", disc_mm=D)
                ctx.doser.tare()
                fill, _ = dose_to(ctx, a.fill_g, tol_g=0.05)
                ctx.prompt("Cup back on its holder", action="cup_to_holder")
                ctx.doser.tare()
        rows.append(row)
        ctx.say("disc {:g} mm: {}".format(D, ", ".join(
            "{} {}".format(k, "{:.3f} g/s".format(row["rate_g_s_" + k]) if row.get("rate_g_s_" + k) else
                           ("flowed" if row.get("flowed_" + k) else "no flow")) for k in ("untapped", "tapped")
            if "flowed_" + k in row)))
        if row.get("flowed_tapped") is False:
            break
        ctx.prompt("Empty the catch beaker back into the jar; brush the cup and disc")
    res = {"discs": rows}
    untapped = {r["disc_mm"]: r["flowed_untapped"] for r in rows if "flowed_untapped" in r}
    tapped = {r["disc_mm"]: (r.get("flowed_untapped") or r.get("flowed_tapped", False)) for r in rows}
    d_no, d_yes, dc = orifice.critical_orifice(untapped)
    t_no, t_yes, dct = orifice.critical_orifice(tapped)
    res.update({"dc_bracket_mm": [d_no, d_yes], "dc_mm": dc, "dc_tapped_bracket_mm": [t_no, t_yes],
                "dc_tapped_mm": dct})
    flowing = [(r["disc_mm"], r["rate_g_s_untapped"]) for r in rows if r.get("rate_g_s_untapped")]
    if a.rho_b and a.d50_um and len(flowing) >= 3:
        bf = orifice.beverloo_fit([x[0] for x in flowing], [x[1] for x in flowing], a.rho_b, a.d50_um / 1000.0)
        res["beverloo"] = bf.to_dict()
    if a.rho_b and dc:
        res["sigma_c_arching_pa"] = orifice.sigma_c_from_dc(a.rho_b, dc)
    if ctx.world:
        p = ctx.world.p
        res["sim_truth"] = {"C": p["bev_C"], "k": p["bev_k"], "dc_mm": p["dc_mm"], "dc_tap_mm": p["dc_tap_mm"]}
    fits = [r["fit_untapped"] for r in rows if "fit_untapped" in r]
    checks = [
        check("fill mass 5.0 +- 0.1 g", all(abs(r["fill_g"] - a.fill_g) <= 0.1 for r in rows),
              [round(r["fill_g"], 3) for r in rows], 0.1),
        check("steady-flow fit R^2 >= 0.99", all(f["method"] != "fit" or f["r2"] >= 0.99 for f in fits) and bool(fits),
              [round(f["r2"], 4) if f["method"] == "fit" else f["method"] for f in fits], 0.99),
        check(">= 3 flowing discs for the Beverloo fit", len(flowing) >= 3, len(flowing), 3),
        check("D_c bracketed by a flowing and a non-flowing disc", d_no is not None and d_yes is not None,
              [d_no, d_yes]),
        check("D_c,tapped bracketed", t_no is not None and t_yes is not None, [t_no, t_yes]),
    ]
    return res, checks
