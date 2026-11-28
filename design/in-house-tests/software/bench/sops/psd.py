"""SOP 4: particle size and shape from images (SPEC 4), and the stage
micrometer calibration ("psdcal")."""

import datetime as dt
import glob
import json
import os

from ..analysis import psd
from .common import check

NUMBER, NAME, TITLE = 4, "psd", "PSD and shape from images"


def add_args(p):
    p.add_argument("--fields", type=int, default=10)
    p.add_argument("--min-grains", type=int, default=2000)
    p.add_argument("--max-fields", type=int, default=40)
    p.add_argument("--um-per-px", type=float, default=None, help="from psdcal (default: today's psdcal run)")
    p.add_argument("--threshold", choices=("otsu", "adaptive"), default="otsu")
    p.add_argument("--h-px", type=float, default=1.5, help="watershed neck depth, px")
    p.add_argument("--boot", type=int, default=500)


def add_args_cal(p):
    p.add_argument("--spacing-um", type=float, default=10.0)


def _todays_scale(root):
    today = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d")
    for d in sorted(glob.glob(os.path.join(root, today + "T*_psdcal_*")), reverse=True):
        f = os.path.join(d, "results.json")
        if os.path.exists(f):
            with open(f) as fh:
                return json.load(fh)["results"]["um_per_px"], d
    return None, None


def run_cal(ctx, a):
    if ctx.world:
        ctx.world.set_scene("psd", spacing_um=a.spacing_um)
    ctx.env("start")
    ctx.prompt("Put the stage micrometer on the slide holder, lines vertical, focus")
    img = ctx.camera("micrometer").capture()
    ctx.log.image("micrometer", img)
    s = psd.scale_from_micrometer(img, a.spacing_um)
    res = {"um_per_px": s, "spacing_um": a.spacing_um, "spacing_px": a.spacing_um / s}
    if ctx.world:
        res["sim_truth_um_per_px"] = ctx.world.s["um_per_px"]
    return res, [check("scale within the lens range 0.9-13 um/px", 0.9 <= s <= 13.5, s, "0.9-13"),
                 check("line spacing >= 4 px (else use the 0.1 mm divisions: --spacing-um 100)",
                       a.spacing_um / s >= 4.0, a.spacing_um / s, 4.0)]


def run(ctx, a):
    scale_src = "argument"
    um = a.um_per_px
    if ctx.world:
        ctx.world.set_scene("psd", um_per_px=um)
        um = um or ctx.world.s["um_per_px"]
        scale_src = "sim"
    if um is None:
        um, d = _todays_scale(a.out)
        scale_src = d
        if um is None:
            raise SystemExit("no --um-per-px and no psdcal run from today in {}".format(a.out))
    ctx.env("start")
    if ctx.acc:
        ctx.acc.call("light on", check=False)
    ctx.prompt("Disperse a few tens of mg on a clean slide (sieve cup on the ERM, or IPA and dry); slide on the stage")
    tables = []
    n = 0
    st = ctx.log.stream("fields", ["field", "grains", "edge_excluded", "cumulative"])
    for f in range(a.max_fields):
        if f >= a.fields and n >= a.min_grains:
            break
        ctx.prompt("Move the stage to field {} (no overlap with earlier fields), focus".format(f + 1))
        img = ctx.camera("microscope").capture()
        ctx.log.image("field{:02d}".format(f + 1), img)
        tab = psd.analyze_field(img, um, field=f, method=a.threshold, h_px=a.h_px)
        tables.append(tab)
        n += tab["ecd_um"].size
        st.write([f + 1, tab["ecd_um"].size, tab["n_edge"], n])
    table = psd.merge(tables)
    gs = ctx.log.stream("grains", ["field", "ecd_um", "feret_max_um", "feret_min_um", "aspect", "circularity",
                                   "solidity", "weight"])
    for i in range(table["ecd_um"].size):
        gs.write([int(table["field"][i])] + [float(table[k][i]) for k in
                                              ("ecd_um", "feret_max_um", "feret_min_um", "aspect", "circularity",
                                               "solidity", "weight")])
    summ = psd.psd_summary(table, n_boot=a.boot, by_field=len(tables) >= 5, um_per_px=um)
    summ.update({"fields": len(tables), "um_per_px": um, "scale_source": scale_src})
    if ctx.world:
        from .. import synth
        p = ctx.world.p
        summ["sim_truth"] = {"d50_n_um": p["d50_um"], "gsd": p["gsd"],
                             "d50_v_um": synth.lognormal_quantile(p["d50_um"], p["gsd"], 0.5, "volume")}
    ci = summ["d50_n_ci"]
    half = 0.5 * (ci[1] - ci[0]) / summ["d50_n"]
    checks = [
        check(">= {} grains over >= {} fields".format(a.min_grains, a.fields),
              summ["n"] >= a.min_grains and len(tables) >= a.fields, [summ["n"], len(tables)]),
        check("scale calibrated the same day", scale_src is not None and scale_src != "argument" or ctx.sim,
              scale_src),
        check("< 5 % of grains under 10 px ECD", summ["frac_under_10px"] < 0.05, summ["frac_under_10px"], 0.05),
        check("bootstrap 95 % CI half-width of d50 <= 3 %", half <= 0.03, half, 0.03),
    ]
    ctx.say("d10/d50/d90 (number) {:.1f} / {:.1f} / {:.1f} um; d50 (volume) {:.1f} um; {} grains".format(
        summ["d10_n"], summ["d50_n"], summ["d90_n"], summ["d50_v"], summ["n"]))
    return summ, checks
