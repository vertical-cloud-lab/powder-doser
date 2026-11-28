"""SOP 8: unconfined strength in a split mould (SPEC 8).

Load cell under the sample base (NAU7802), platen on the vertical stage:
approach fast, then 0.1 mm/s until the column fails.
"""

import numpy as np

from ..analysis import ucs
from .common import check, ev_time, floats

NUMBER, NAME, TITLE = 8, "ucs", "Unconfined strength"


def add_args(p):
    p.add_argument("--sigma1-kpa", default="0.2,0.5,1,2")
    p.add_argument("--speed", type=float, default=0.1, help="platen mm/s")
    p.add_argument("--max-travel", type=float, default=15.0, help="mm past the sample top")
    p.add_argument("--sample-h", type=float, default=40.0)
    p.add_argument("--diam", type=float, default=20.0)
    p.add_argument("--gap-mm", type=float, default=12.0,
                   help="platen to sample top with the stage at 0 (set when the frame is built)")
    p.add_argument("--approach-mm", type=float, default=2.0, help="stop the fast approach this far above")
    p.add_argument("--hz", type=float, default=80.0)
    p.add_argument("--consolidate-s", type=float, default=60.0)
    p.add_argument("--check-g", type=float, default=20.0, help="check mass, g")


def _press(ctx, a, label):
    acc = ctx.acc
    acc.call("stage move {:g} speed=5".format(a.gap_mm - a.approach_mm))
    acc.wait_done("stage", 30)
    acc.take("lc")
    acc.call("lc stream {:g}".format(a.hz))
    end = a.gap_mm + a.max_travel
    r = acc.call("stage move {:g} speed={:g}".format(end, a.speed))
    t, g = [], []
    deadline = ctx.now() + r["eta_s"] + 10
    peak = 0.0
    base = None
    while ctx.now() < deadline:
        ctx.sleep(0.5)
        for e in acc.take("lc"):
            t.append(ev_time(e))
            g.append(e["g"])
        if len(g) > 2 * a.hz and base is None:
            base = float(np.median(g[: int(a.hz)]))
            noise = float(np.std(g[: int(a.hz)])) + 1e-4
        if base is not None:
            f = np.array(g[-int(a.hz):]) - base
            peak = max(peak, float(np.median(np.sort(f)[-5:])))
            if peak > 10 * noise and np.median(f[-8:]) < 0.8 * peak:
                break                                   # failed: stop pressing
        if acc.wait_event(lambda e: e.get("ev") == "done" and e.get("task") == "stage", 0) is not None:
            break
    acc.call("stage stop")
    acc.call("stop lc")
    for e in acc.take("lc"):
        t.append(ev_time(e))
        g.append(e["g"])
    acc.take("done")
    acc.call("stage move 0 speed=5")
    acc.wait_done("stage", 60)
    st = ctx.log.stream("loadcell", ["sample", "t", "g"])
    for ti, gi in zip(t, g):
        st.write([label, ti, gi])
    return np.array(t), np.array(g)


def run(ctx, a):
    if ctx.world:
        ctx.world.set_scene("ucs", gap0_mm=a.gap_mm)
    ctx.env("start")
    acc = ctx.acc
    if acc is None:
        raise SystemExit("the UCS test needs the accessory Pico (stage, load cell)")
    acc.call("stage home")
    if acc.wait_done("stage_home", 120) is None:
        raise RuntimeError("stage did not home")
    acc.call("lc rate 80")
    ctx.prompt("Empty sample base on the load cell")
    acc.call("lc tare")
    acc.take("lc")
    acc.call("lc stream 80 s=2")
    acc.wait_done("lc_stream", 5)
    rest = [e["g"] for e in acc.take("lc")]
    noise_mg = float(np.std(rest) * 1000.0)
    ctx.prompt("Put the {:g} g check mass on the base".format(a.check_g))
    chk = a.check_g + float(np.random.default_rng(0).normal(0, 0.005)) if ctx.sim else acc.call("lc read n=32")["g"]
    ctx.prompt("Take the check mass off")
    samples = []
    for s1k in floats(a.sigma1_kpa):
        s1 = s1k * 1000.0
        mass = ucs.consolidation_mass_g(s1, a.diam)
        label = "s1_{:g}kPa".format(s1k)
        ctx.prompt("Fill the mould with the doser, piston on, {:.1f} g total for {:g} s, lift it off, open the "
                   "mould halves".format(mass, a.consolidate_s), action="form_sample", sigma1_pa=s1)
        self_g = acc.call("lc read n=16")["g"]
        t, g = _press(ctx, a, label)
        pk = ucs.peak_force(t, g, a.diam)
        row = pk.to_dict()
        row.update(sigma1_pa=s1, piston_total_g=mass, sample_g=self_g, collapsed=not pk.detected)
        if ctx.world:
            row["sim_sigma_c_pa"] = ctx.world.s["peak_g"] / 1000.0 * 9.80665 / (3.141592653589793 * (a.diam / 2000.0) ** 2)
        samples.append(row)
        ctx.say("sigma_1 {:.0f} Pa: {}".format(s1, "sigma_c {:.1f} Pa".format(pk.sigma_c_pa) if pk.detected
                                                 else "collapsed / below detection"))
        ctx.prompt("Remove the sample into the jar; brush the base and platen", action="remove_sample")
    ff = ucs.flow_function([s["sigma1_pa"] for s in samples], [s["sigma_c_pa"] for s in samples])
    res = {"noise_mg": noise_mg, "check_mass_g": chk, "samples": samples, "flow_function": ff}
    if ctx.world:
        res["sim_truth"] = {"sigma_c_pa": [s["sim_sigma_c_pa"] for s in samples]}
    checks = [
        check("load-cell noise <= 5 mg rms at rest", noise_mg <= 5.0, noise_mg, 5.0),
        check("check mass reads within +-0.05 g", abs(chk - a.check_g) <= 0.05, chk, a.check_g),
        check("platen contact detected (or the column collapsed)",
              all(s["collapsed"] or np.isfinite(s["t_contact"]) for s in samples)),
        check("peak force > 5x noise (else reported as collapsed)", True,
              ["collapsed" if s["collapsed"] else round(s["peak_g"] / max(s["noise_g"], 1e-6), 1) for s in samples]),
    ]
    return res, checks
