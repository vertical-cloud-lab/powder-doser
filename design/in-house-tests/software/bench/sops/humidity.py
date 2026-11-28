"""SOP 6: humidity chambers (SPEC 6).

start: check the box RH, weigh the dish and the sample, put it in the box.
weigh: take the dish out, weigh, put it back (at 1, 2, 4, 8, 24 h).
finish: fit the uptake. In --sim the whole schedule runs in one go.
The box sensors are SHT45s on a TCA9548A on the bench Pi's own I2C bus.
"""

import json
import os

import numpy as np

from .. import devices
from ..analysis import humidity as hum
from .common import check, floats

NUMBER, NAME, TITLE = 6, "humidity", "Humidity chambers"
STATE = "humidity_state.json"


def add_args(p):
    p.add_argument("--box", choices=("MgCl2", "MgNO3", "NaCl", "KCl", "silica"), required=True)
    p.add_argument("--stage", choices=("start", "weigh", "finish", "all"), default=None,
                   help="default: all in --sim, else start")
    p.add_argument("--run-dir", default=None, help="the run folder made by --stage start")
    p.add_argument("--times", default="0,1,2,4,8,24", help="hours")
    p.add_argument("--sample-g", type=float, default=3.0)


def _box_reader(ctx):
    if ctx.world:
        return ctx.world.box_reading
    bs = devices.BoxSensors()
    return bs.read


def _load(d):
    with open(os.path.join(d, STATE)) as f:
        return json.load(f)


def _save(d, st):
    with open(os.path.join(d, STATE), "w") as f:
        json.dump(st, f, indent=2)


def stage_start(ctx, a, run_dir):
    read = _box_reader(ctx)
    t_c, rh = read(a.box)
    nominal = hum.nominal_rh(a.box, t_c)
    ctx.prompt("Tare the empty sample dish on the balance", action="dish_off")
    ctx.doser.tare()
    ctx.prompt("Put the empty dish on the balance", action="dish_on_balance")
    dish = ctx.weigh()
    ctx.prompt("Spread {:g} g of powder in a thin layer in the dish".format(a.sample_g))
    if ctx.world:
        ctx.world.operator("sample_in_box", sample_g=a.sample_g)
        ctx.world.s["t_in"] = None
        ctx.world.operator("dish_on_balance")
    m = ctx.weigh()
    ctx.prompt("Put the dish on the shelf in the {} box; close the lid".format(a.box), action="sample_in_box",
               sample_g=m - dish)
    st = {"box": a.box, "t0": ctx.now(), "dish_g": dish, "m0_g": m - dish, "box_rh_start": rh,
          "box_t_start": t_c, "nominal_rh": nominal, "weighings": [[0.0, m - dish, True]]}
    _save(run_dir, st)
    return st


def stage_weigh(ctx, a, run_dir):
    st = _load(run_dir)
    ctx.prompt("Take the dish out of the {} box and put it on the balance".format(st["box"]),
               action="dish_on_balance")
    g, stable = ctx.doser.weigh()
    if not stable:
        ctx.sleep(2.0)
        g, stable = ctx.doser.weigh()
    t_h = (ctx.now() - st["t0"]) / 3600.0
    st["weighings"].append([t_h, g - st["dish_g"], bool(stable)])
    ctx.prompt("Put the dish back in the box; close the lid", action="dish_off")
    _save(run_dir, st)
    return st


def stage_finish(ctx, a, run_dir):
    st = _load(run_dir)
    read = _box_reader(ctx)
    t_c, rh = read(st["box"])
    w = np.array([x[:2] for x in st["weighings"]], float)
    u = hum.uptake_mg_per_g(w[:, 1], st["m0_g"])
    fit = hum.uptake_fit(w[:, 0], u)
    res = {"box": st["box"], "nominal_rh": st["nominal_rh"], "box_rh_start": st["box_rh_start"],
           "box_rh_end": rh, "t_h": w[:, 0].tolist(), "uptake_mg_g": u.tolist(), "fit": fit.to_dict()}
    if ctx.world:
        res["sim_truth"] = {"u_eq": ctx.world.p["uptake"][st["box"]], "tau_h": ctx.world.p["tau_h"]}
    checks = [
        check("box RH within +-2 % RH of nominal before the sample went in",
              abs(st["box_rh_start"] - st["nominal_rh"]) <= 2.0, st["box_rh_start"], st["nominal_rh"]),
        check("stable (ST) balance readings", all(x[2] for x in st["weighings"]),
              [x[2] for x in st["weighings"]]),
        check("first-order uptake fit R^2 >= 0.95", fit.r2 >= 0.95, fit.r2, 0.95),
    ]
    with open(os.path.join(run_dir, "humidity_result.json"), "w") as f:
        json.dump({"results": res, "checks": checks}, f, indent=2)
    return res, checks


def run(ctx, a):
    stage = a.stage or ("all" if ctx.sim else "start")
    if ctx.world:
        ctx.world.set_scene("humidity", box=a.box)
    ctx.env("start")
    if stage in ("start", "all"):
        st = stage_start(ctx, a, ctx.log.dir)
        if stage == "start":
            ctx.say("next: python -m bench.run humidity --box {} --stage weigh --run-dir {} --jar {}".format(
                a.box, ctx.log.dir, a.jar))
            return {"state": st, "run_dir": ctx.log.dir}, [check(
                "box RH within +-2 % RH of nominal", abs(st["box_rh_start"] - st["nominal_rh"]) <= 2.0,
                st["box_rh_start"], st["nominal_rh"])]
    if stage == "all":
        t0 = ctx.now()
        for th in floats(a.times)[1:]:
            ctx.sleep(max(0.0, t0 + th * 3600.0 - ctx.now()))
            stage_weigh(ctx, a, ctx.log.dir)
        return stage_finish(ctx, a, ctx.log.dir)
    if not a.run_dir:
        raise SystemExit("--stage {} needs --run-dir".format(stage))
    if stage == "weigh":
        st = stage_weigh(ctx, a, a.run_dir)
        return {"weighing": st["weighings"][-1], "run_dir": a.run_dir}, []
    return stage_finish(ctx, a, a.run_dir)
