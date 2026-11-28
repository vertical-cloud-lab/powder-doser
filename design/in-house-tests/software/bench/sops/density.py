"""SOP 2: bulk and tapped density (SPEC 2), and the water calibration of
the cylinder ("watercal").

Fill by the doser at 45 deg to 6 g or 8 mL (whichever first); move the
cylinder to the cam-drop tapper; tap in batches 0, 1, 2, 5, ... 1250 at
250 taps/min (3.0 mm drop), photographing after each batch.
"""

import json
import os

import numpy as np

from ..analysis import column
from .common import check, dose_to, ints

NUMBER, NAME, TITLE = 2, "density", "Bulk and tapped density"
GEOM_DEFAULT = {"px_per_mm": 16.0, "datum_row": 1220, "x_range": [72, 248], "axis_x": 159.5, "bore_mm": 13.0}


def add_args(p):
    p.add_argument("--fill-g", type=float, default=6.0)
    p.add_argument("--fill-ml", type=float, default=8.0)
    p.add_argument("--tilt", type=float, default=45.0)
    p.add_argument("--rpm", type=float, default=30.0)
    p.add_argument("--batches", default="0,1,2,5,10,20,50,100,200,500,1250", help="cumulative tap counts")
    p.add_argument("--tap-rate", type=float, default=250.0, help="taps/min")
    p.add_argument("--cal", default=None, help="water calibration CSV from 'watercal'")
    p.add_argument("--images-per-reading", type=int, default=3)


def add_args_watercal(p):
    p.add_argument("--steps", type=int, default=8)
    p.add_argument("--step-ml", type=float, default=1.0)
    p.add_argument("--px-per-mm", type=float, default=GEOM_DEFAULT["px_per_mm"])
    p.add_argument("--datum-row", type=float, default=GEOM_DEFAULT["datum_row"],
                   help="image row of the inside bottom of the cylinder")
    p.add_argument("--x-range", default="{},{}".format(*GEOM_DEFAULT["x_range"]),
                   help="image columns inside the bore, clear of wall glare")
    p.add_argument("--save-cal", default=None, help="where to write the calibration CSV")


def save_cal(path, cal, geom):
    with open(path, "w") as f:
        f.write("# geometry={}\n".format(json.dumps(geom)))
        f.write("# meniscus_ml={:.5f}\n".format(cal.meniscus_ml))
        f.write("height_mm,volume_ml\n")
        for h, v in zip(cal.h, cal.v):
            f.write("{:.4f},{:.5f}\n".format(h, v))


def load_cal(path):
    geom, men = dict(GEOM_DEFAULT), None
    with open(path) as f:
        for line in f:
            if line.startswith("# geometry="):
                geom.update(json.loads(line.split("=", 1)[1]))
            elif line.startswith("# meniscus_ml="):
                men = float(line.split("=", 1)[1])
    d = np.genfromtxt(path, delimiter=",", names=True, comments="#")
    return column.VolumeCalibration(d["height_mm"], d["volume_ml"], men), geom


def read_height(ctx, geom, n=1, mode="axisym", tag=None):
    """Median column top over n images (mm above the datum)."""
    tops, flats = [], []
    for i in range(n):
        img = ctx.camera("silhouette").capture()
        if tag:
            ctx.log.image("{}_{}".format(tag, i), img)
        ct = column.column_top(img, geom["px_per_mm"], geom["datum_row"], geom["x_range"], mode=mode,
                               axis_x=geom.get("axis_x"))
        tops.append(ct.top_mm)
        flats.append(ct.flat_mm)
    return float(np.median(tops)), float(np.median(flats))


def run_watercal(ctx, a):
    if ctx.world:
        ctx.world.set_scene("density")
    env = ctx.env("start")
    temp = env[0] if env else 22.0
    x0, x1 = [int(float(v)) for v in a.x_range.split(",")]
    geom = {"px_per_mm": a.px_per_mm, "datum_row": a.datum_row, "x_range": [x0, x1],
            "axis_x": 0.5 * (x0 + x1 - 1), "bore_mm": 13.0}
    if ctx.acc:
        ctx.acc.call("light on", check=False)
    ctx.prompt("Put the clean, dry cylinder in the fill holder on the pan adapter")
    ctx.doser.tare()
    hs, gs = [], []
    st = ctx.log.stream("watercal", ["step", "water_g", "height_mm"])
    for i in range(1, a.steps + 1):
        ctx.prompt("Pipette about {:.1f} mL of dyed water (1 drop of ink per 10 mL) into the cylinder; "
                   "no drops on the wall".format(a.step_ml), action="add_water", ml=a.step_ml)
        ctx.sleep(2.0)
        g = ctx.weigh()
        h, _ = read_height(ctx, geom, 1, mode="center", tag="water{:02d}".format(i))
        hs.append(h)
        gs.append(g)
        st.write([i, g, h])
    cal = column.VolumeCalibration.from_water(hs, gs, temp)
    path = a.save_cal or os.path.join(ctx.log.dir, "cylinder_cal.csv")
    save_cal(path, cal, geom)
    res = {"calibration": cal.to_dict(), "csv": path, "water_temp_c": temp}
    checks = [check("water calibration residual <= 0.02 mL", cal.residual_ml <= 0.02, cal.residual_ml, 0.02),
              check("fitted bore 13.0 +- 0.3 mm", abs(cal.bore_mm - 13.0) <= 0.3, cal.bore_mm, "12.7-13.3")]
    return res, checks


def run(ctx, a):
    if ctx.world:
        ctx.world.set_scene("density")
    if a.cal:
        cal, geom = load_cal(a.cal)
    elif ctx.sim:
        # --sim without a calibration: calibrate the simulated cylinder first
        hs, vs = [], []
        g = ctx.world.GEOM
        for ml in np.arange(1.0, 9.0):
            ctx.world.s.update(water_ml=ml, powder_g=0.0)
            h, _ = read_height(ctx, GEOM_DEFAULT, 1, mode="center")
            hs.append(h)
            vs.append(ml)
        ctx.world.set_scene("density")
        cal, geom = column.VolumeCalibration(hs, vs), dict(GEOM_DEFAULT)
        ctx.log.event("sim_calibration", bore_mm=cal.bore_mm, residual_ml=cal.residual_ml, bore_true=g["bore_mm"])
    else:
        raise SystemExit("density needs --cal <csv from watercal>")
    ctx.env("start")
    if ctx.acc:
        ctx.acc.call("light on", check=False)
    ctx.prompt("Cylinder in the fill holder on the pan adapter, funnel collar on the rim, under the doser outlet")
    ctx.doser.tilt(a.tilt)
    ctx.set_rpm(a.rpm)
    ctx.doser.tare()
    rho_guess = [None]

    def volume_reached(g):
        # read the camera only once the column could be near the volume limit
        if rho_guess[0] is None or g / rho_guess[0] > 0.7 * a.fill_ml:
            h, _ = read_height(ctx, geom, 1)
            v = float(cal.powder_volume(h))
            rho_guess[0] = g / v if v > 0 else None
            return v >= a.fill_ml
        return False
    mass, revs = dose_to(ctx, a.fill_g, tol_g=0.05, on_step=volume_reached)
    ctx.sleep(2.0)
    mass = ctx.weigh()
    h_fill, flat_fill = read_height(ctx, geom, a.images_per_reading, tag="fill")
    v_fill = float(cal.powder_volume(h_fill))
    ctx.say("filled {:.4f} g in {:.1f} revs; {:.3f} mL as poured".format(mass, revs, v_fill))
    # Home the cam BEFORE the cylinder goes in: homing lifts and drops the
    # empty carriage, which would otherwise tap the sample before "0 taps".
    ctx.acc.call("cam home")
    if ctx.acc.wait_done("cam_home", 30) is None:
        raise RuntimeError("cam did not home")
    ctx.prompt("Move the cylinder gently to the cam-tapper carriage (keep it upright, no knocks)",
               action="move_to_tapper")
    batches = ints(a.batches)
    done = 0
    taps, vols, flats = [], [], []
    st = ctx.log.stream("compaction", ["taps", "height_mm", "volume_ml", "flat_mm", "index_ok"])
    for n in batches:
        index_ok = None
        if n > done:
            r = ctx.acc.call("cam taps {} rate={:g}".format(n - done, a.tap_rate))
            ev = ctx.acc.wait_done("cam", r["eta_s"] + 15)
            if ev is None or ev.get("reason") != "done":
                raise RuntimeError("cam taps did not finish: {}".format(ev))
            index_ok = ev.get("index_ok")
            done = n
            ctx.sleep(1.0)
        h, flat = read_height(ctx, geom, a.images_per_reading, tag="taps{:04d}".format(n))
        v = float(cal.powder_volume(h))
        taps.append(n)
        vols.append(v)
        flats.append(flat)
        st.write([n, h, v, flat, index_ok])
    d = column.densities(mass, taps, vols)
    res = d.to_dict()
    res.update({"fill_revs": revs, "poured_volume_ml_fill_holder": v_fill, "calibration": cal.to_dict()})
    if ctx.world:
        p = ctx.world.p
        res["sim_truth"] = {"rho_bulk": p["rho_bulk"], "kawakita_a": p["kaw_a"], "kawakita_inv_b": p["kaw_inv_b"]}
    target_hit = abs(mass - a.fill_g) <= 0.1 or v_fill >= a.fill_ml * 0.98
    checks = [
        check("water calibration residual <= 0.02 mL", cal.residual_ml <= 0.02, cal.residual_ml, 0.02),
        check("fill mass within 0.1 g of target (or volume limit)", target_hit, mass, a.fill_g),
        check("powder top flat within 0.3 mm", flats[0] <= 0.3, flats[0], 0.3),
        check("volume change over the last two batches < 2 %", d.last_change_pct < 2.0, d.last_change_pct, 2.0),
        check("Kawakita fit R^2 >= 0.99", d.kawakita_r2 >= 0.99, d.kawakita_r2, 0.99),
    ]
    return res, checks
