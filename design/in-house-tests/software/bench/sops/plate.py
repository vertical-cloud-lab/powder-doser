"""SOP 3: tilting plate, wall friction (mode A) and layer start angle
(mode B) (SPEC 3).

Level the table and zero the IMU; tilt fast to a few degrees below the
expected angle, then at 0.5 deg/s while streaming the IMU and taking side
photos; slip = the ring (or layer) moves more than 0.5 mm.
"""

import math

import numpy as np

from ..analysis import plate
from .common import check, ev_time, floats

NUMBER, NAME, TITLE = 3, "plate", "Tilting plate"
RING_AREA_MM2 = math.pi * 12.5 ** 2          # 25 mm ID ring


def add_args(p):
    p.add_argument("--mode", choices=("A", "B"), default="A")
    p.add_argument("--coupon", choices=("PLA", "steel", "glass", "rough"), default="PLA")
    p.add_argument("--lids", default="0,5,15", help="lid masses, g (mode A)")
    p.add_argument("--depths", default="1,2,3,5", help="layer depths, mm (mode B)")
    p.add_argument("--repeats", type=int, default=3)
    p.add_argument("--fast-to", type=float, default=None, help="table deg reached quickly (default: 15 A, 25 B)")
    p.add_argument("--fast-rate", type=float, default=5.0)
    p.add_argument("--rate", type=float, default=0.5, help="table deg/s near the slip")
    p.add_argument("--max-deg", type=float, default=80.0)
    p.add_argument("--fps", type=float, default=5.0)
    p.add_argument("--px-per-mm", type=float, default=12.0)
    p.add_argument("--ring-g", type=float, default=2.5, help="ring mass, g")
    p.add_argument("--powder-g", type=float, default=3.0, help="powder in the ring if not weighed, g")


def _trial(ctx, a, label, load):
    acc = ctx.acc
    cam = ctx.camera("silhouette")
    fast_to = a.fast_to if a.fast_to is not None else (15.0 if a.mode == "A" else 25.0)
    acc.call("table {:g} rate={:g}".format(fast_to, a.fast_rate))
    acc.wait_done("table", fast_to / a.fast_rate * 1.6 + 5)
    acc.take("imu")
    acc.call("table {:g} rate={:g} stream=20".format(a.max_deg, a.rate))
    t_frames, frames, disp = [], [], []
    t_slip = None
    max_s = (a.max_deg - fast_to) / a.rate + 5
    t0 = ctx.now()
    while ctx.now() - t0 < max_s:
        img = cam.capture()
        t_frames.append(ctx.now())
        frames.append(img)
        d = plate.ring_displacement([frames[0], img], a.px_per_mm)[1]
        disp.append(d)
        if d > 0.5 and len(frames) > 3:
            t_slip, _ = plate.detect_slip(t_frames, disp)
            break
        ctx.sleep(1.0 / a.fps)
    acc.call("table stop")
    imu = acc.take("imu")
    acc.take("done")
    t_imu = np.array([ev_time(e) for e in imu])
    deg = np.array([e["deg"] for e in imu])
    jolt = np.array([e.get("jolt", 0.0) for e in imu])
    for i in (0, len(frames) // 2, len(frames) - 1):
        ctx.log.image("{}_f{:03d}".format(label, i), frames[i])
    st = ctx.log.stream("imu", ["trial", "t", "deg", "cmd_deg", "jolt"])
    for e, t in zip(imu, t_imu):
        st.write([label, t, e["deg"], e.get("cmd_deg"), e.get("jolt")])
    fs = ctx.log.stream("ring", ["trial", "t", "disp_mm"])
    for t, d in zip(t_frames, disp):
        fs.write([label, t, d])
    out = {"trial": label, "load": load, "slipped": t_slip is not None}
    if ctx.world:
        out["sim_theta_s"] = ctx.world.s.get("theta_s")
    if t_slip is not None and t_imu.size > 3:
        tj = plate.jolt_time(t_imu, jolt)
        t_first = min(t_slip, tj) if tj is not None else t_slip
        out["theta_cam_deg"] = plate.ramp_angle_at(t_slip, t_imu, deg, t_first)
        out["theta_imu_deg"] = plate.ramp_angle_at(tj, t_imu, deg, t_first) if tj is not None else None
        out["rate_deg_s"] = plate.ramp_rate(t_imu, deg, t_first - 0.2)
    acc.call("table 0 rate={:g}".format(a.fast_rate))
    acc.wait_done("table", a.max_deg / a.fast_rate * 1.6 + 5)
    acc.take("imu")
    return out


def run(ctx, a):
    if ctx.world:
        ctx.world.set_scene("plate", mode=a.mode, coupon=a.coupon, px_per_mm=a.px_per_mm)
    ctx.env("start")
    acc = ctx.acc
    if acc is None:
        raise SystemExit("the tilting plate needs the accessory Pico")
    acc.call("light on", check=False)
    ctx.prompt("Fit the {} coupon; table on its level stop; camera on the plate's side mount".format(a.coupon))
    acc.call("table 0 rate=5")
    acc.wait_done("table", 30)
    z = acc.call("imu zero")
    zero_check = acc.call("imu n=16")["deg"]
    ctx.log.event("imu_zero", offset_deg=z["offset_deg"], check_deg=zero_check)
    loads = floats(a.lids) if a.mode == "A" else floats(a.depths)
    trials = []
    for load in loads:
        for rep in range(1, a.repeats + 1):
            label = "{}{:g}_r{}".format("lid" if a.mode == "A" else "depth", load, rep)
            if a.mode == "A":
                ctx.prompt("Fill the ring with powder, strike it off, add the {:g} g lid, weigh the "
                           "assembly on the balance".format(load))
                mass = a.ring_g + a.powder_g + load if ctx.sim else ctx.weigh()
                ctx.prompt("Set the ring on the plate at the high end, pull the three shim tabs",
                           action="place_ring", mass_g=mass, area_mm2=RING_AREA_MM2)
            else:
                mass = None
                ctx.prompt("Strike off a {:g} mm layer with the frame on the roughened plate".format(load),
                           action="place_ring", mass_g=0.0, depth_mm=load)
            tr = _trial(ctx, a, label, load)
            tr["mass_g"] = mass
            if a.mode == "A" and "theta_cam_deg" in tr:
                tr["sigma_pa"], tr["tau_pa"] = plate.stresses_at_slip(mass, tr["theta_cam_deg"], RING_AREA_MM2)
            trials.append(tr)
            ctx.say("{}: slip at {}".format(label, "{:.2f} deg".format(tr["theta_cam_deg"])
                                            if "theta_cam_deg" in tr else "none"))
            ctx.prompt("Catch the ring at the stop rail, tip the powder back into the jar, brush the coupon")
    slipped = [t for t in trials if "theta_cam_deg" in t]
    res = {"mode": a.mode, "coupon": a.coupon, "trials": trials, "imu_zero_check_deg": zero_check}
    per_load = {}
    for t in slipped:
        per_load.setdefault(t["load"], []).append(t["theta_cam_deg"])
    res["angle_by_load"] = {str(k): {"mean": float(np.mean(v)), "sd": float(np.std(v, ddof=1)) if len(v) > 1 else None,
                                     "n": len(v)} for k, v in per_load.items()}
    checks = [check("IMU reads 0 +- 0.1 deg at the level stop after zeroing", abs(zero_check) <= 0.1, zero_check, 0.1)]
    rates = [t["rate_deg_s"] for t in slipped if np.isfinite(t.get("rate_deg_s", np.nan))]
    checks.append(check("tilt rate at slip 0.5 +- 0.1 deg/s", bool(rates) and all(abs(r - a.rate) <= 0.1 for r in rates),
                        [round(r, 3) for r in rates], "0.4-0.6"))
    pairs = [(t["theta_cam_deg"], t["theta_imu_deg"]) for t in slipped if t.get("theta_imu_deg") is not None]
    checks.append(check("camera and IMU slip angles agree within 1 deg",
                        bool(pairs) and all(abs(x - y) <= 1.0 for x, y in pairs),
                        [round(x - y, 2) for x, y in pairs], 1.0))
    spreads = [max(v) - min(v) for v in per_load.values() if len(v) > 1]
    checks.append(check("repeats per load within +-1 deg", bool(spreads) and all(s <= 2.0 for s in spreads),
                        [round(s / 2, 2) for s in spreads], 1.0))
    if a.mode == "A":
        sig = [t["sigma_pa"] for t in slipped]
        tau = [t["tau_pa"] for t in slipped]
        n_stress = len(set(round(s, -1) for s in sig))
        if len(sig) >= 2:
            wf = plate.wall_friction_fit(sig, tau)
            res["wall_friction"] = wf.to_dict()
            ctx.say("wall friction on {}: phi_w {:.1f} deg, mu_w {:.3f}, c_w {:.1f} Pa".format(
                a.coupon, wf.phi_w_deg, wf.mu_w, wf.c_w_pa))
        checks.append(check("wall fit uses >= 3 normal stresses", n_stress >= 3, n_stress, 3))
        if ctx.world:
            res["sim_truth"] = {"phi_w_deg": ctx.world.p["phi_w"][a.coupon], "c_w_pa": ctx.world.p["c_w"]}
    elif ctx.world:
        res["sim_truth"] = {"layer_start": ctx.world.p["layer_start"]}
    return res, checks
