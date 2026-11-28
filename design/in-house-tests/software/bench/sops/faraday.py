"""SOP 10: Faraday cup (SPEC 10).

Zero (reset), dose N revs, read Q 2 s after the last grain, weigh; q/m.
"""

import numpy as np

from ..analysis import faraday
from .common import check, ev_time

NUMBER, NAME, TITLE = 10, "faraday", "Faraday cup"


def add_args(p):
    p.add_argument("--revs", type=float, default=3.0)
    p.add_argument("--tilt", type=float, default=45.0)
    p.add_argument("--cf-nf", type=float, default=10.0, help="fitted feedback capacitor, nF")
    p.add_argument("--repeats", type=int, default=3)
    p.add_argument("--settle-s", type=float, default=2.0)
    p.add_argument("--baseline-s", type=float, default=5.0)
    p.add_argument("--hz", type=float, default=10.0)


def run(ctx, a):
    if ctx.world:
        ctx.world.set_scene("faraday")
    ctx.env("start")
    acc = ctx.acc
    if acc is None:
        raise SystemExit("the Faraday cup needs the accessory Pico (charge amplifier)")
    acc.call("q cf {:g}".format(a.cf_nf))
    acc.call("q short")
    ctx.doser.tilt(a.tilt)
    st = ctx.log.stream("charge", ["rep", "t", "v", "nc"])
    reps = []
    for k in range(1, a.repeats + 1):
        ctx.prompt("Balance empty; tare", action="empty_cup")
        ctx.doser.tare()
        ctx.prompt("Inner cup on the balance (lead unplugged)", action="cup_on_balance")
        m0 = ctx.weigh()
        ctx.prompt("Cup into the shield under the outlet on its PTFE standoffs; plug the lead; touch the "
                   "grounded can, then keep clear", action="cup_in_shield")
        acc.take("q")
        acc.call("q zero ms=500")
        acc.wait_done("q_zero", 5)
        acc.call("q stream {:g}".format(a.hz))
        ctx.sleep(a.baseline_s)
        t_start = ctx.now()
        ctx.doser.rotate(360.0 * a.revs)
        t_end = ctx.now()
        ctx.sleep(a.settle_s + 2.0)
        acc.call("stop q")
        ev = acc.take("q")
        acc.take("done")
        acc.call("q short")
        t = np.array([ev_time(e) for e in ev])
        q = np.array([e["nc"] for e in ev])
        for e, ti in zip(ev, t):
            st.write([k, ti, e["v"], e["nc"]])
        step = faraday.charge_step(t, q, t_start, t_end, a.settle_s)
        zero = float(np.mean(q[:3])) if q.size >= 3 else float("nan")
        ctx.prompt("Unplug the lead; inner cup onto the balance", action="cup_on_balance")
        m1 = ctx.weigh()
        dm = m1 - m0
        qm = faraday.q_over_m(step.dq_nc, dm) if dm > 0 else float("nan")
        row = step.to_dict()
        row.update(rep=k, mass_g=dm, q_per_m_c_kg=qm, zero_nc=zero, revs=a.revs)
        reps.append(row)
        ctx.say("rep {}: {:+.2f} nC on {:.4f} g -> {:+.3g} C/kg".format(k, step.dq_nc, dm, qm))
        ctx.prompt("Tip the powder back into the jar; wipe the cup with a lint-free cloth")
    qms = np.array([r["q_per_m_c_kg"] for r in reps])
    res = {"reps": reps, "q_per_m_mean_c_kg": float(np.nanmean(qms)),
           "q_per_m_sd_c_kg": float(np.nanstd(qms, ddof=1)) if len(qms) > 1 else None, "cf_nf": a.cf_nf}
    if ctx.world:
        res["sim_truth_q_per_m_c_kg"] = ctx.world.p["q_nc_per_g"] * 1e-6
    checks = [
        check("baseline drift < 0.05 nC/s", all(abs(r["drift_nc_s"]) < 0.05 for r in reps),
              [round(r["drift_nc_s"], 4) for r in reps], 0.05),
        check("zero after 'q zero' within +-0.1 nC", all(abs(r["zero_nc"]) <= 0.1 for r in reps),
              [round(r["zero_nc"], 3) for r in reps], 0.1),
        check("charge settled (< 2 % change over the last 1 s)", all(r["settled"] for r in reps),
              [round(r["settle_change_pct"], 2) for r in reps], 2.0),
        check("powder mass >= 0.2 g", all(r["mass_g"] >= 0.2 for r in reps), [round(r["mass_g"], 4) for r in reps],
              0.2),
        check(">= 3 repeats", len(reps) >= 3, len(reps), 3),
    ]
    return res, checks
