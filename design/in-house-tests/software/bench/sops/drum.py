"""SOP 7: rotating drum on the doser's stepper (SPEC 7).

Module horizontal; 1, 2, 5, 10, 20 rpm, 90 s each at 10 fps. Needs the
doser's `rpm` command (software/doser_patches/0001-rpm-command.patch).
"""

import numpy as np

from ..analysis import drum
from .common import check, floats

NUMBER, NAME, TITLE = 7, "drum", "Rotating drum"
DRUM_R_M = 0.020


def add_args(p):
    p.add_argument("--rpms", default="1,2,5,10,20")
    p.add_argument("--seconds", type=float, default=90.0)
    p.add_argument("--fps", type=float, default=10.0)
    p.add_argument("--save-every", type=int, default=1, help="keep every Nth frame as PNG")
    p.add_argument("--center", default=None, help="x,y of the drum axis in px (default: found)")
    p.add_argument("--radius", type=float, default=None, help="drum radius in px (default: found)")


def run(ctx, a):
    if ctx.world:
        ctx.world.set_scene("drum")
    ctx.env("start")
    ctx.prompt("Drum shaft in the auger brackets, drum filled to 40 % (7.5 mL), window on; camera on the axis")
    ctx.doser.preset("horizontal")
    cam = ctx.camera("drum")
    first = cam.capture()
    ctx.log.image("first", first)
    if a.center and a.radius:
        center = tuple(float(v) for v in a.center.split(","))
        radius = a.radius
    else:
        center, radius = drum.find_drum(first)
    fill = drum.fill_fraction(first, center, radius)
    st = ctx.log.stream("angles", ["rpm", "t", "angle_deg", "r2", "valid"])
    speeds = []
    k = 0
    for rpm in floats(a.rpms):
        ctx.set_rpm(rpm, required=True)
        deg = 360.0 * rpm * (a.seconds + 60.0 / rpm + 2.0) / 60.0
        move = ctx.doser.rotate_async(deg, timeout=deg / 360.0 * 60.0 / rpm * 2 + 30)
        ctx.sleep(max(2.0, 60.0 / rpm * 0.5))           # let the bed reach its regime
        frames, ts = [], []
        for i in range(int(a.seconds * a.fps)):
            img = cam.capture()
            frames.append(img)
            ts.append(ctx.now())
            if i % a.save_every == 0:
                ctx.log.image("rpm{:g}_f{:04d}".format(rpm, i), img)
            k += 1
            ctx.sleep(1.0 / a.fps)
        move.wait()
        ang, valid, prof = drum.drum_angles(frames, center, radius)
        for t, x, v in zip(ts, ang, valid):
            st.write([rpm, t, x, None, bool(v)])
        t = np.array(ts)
        good = ang[valid]
        row = {"rpm": rpm, "frames": len(frames), "valid": int(valid.sum()),
               "valid_s": float(valid.sum() / a.fps), "rejected_frac": float(1 - valid.mean()),
               "dynamic_deg": float(good.mean()) if good.size else None,
               "dynamic_sd": float(good.std(ddof=1)) if good.size > 1 else None,
               "froude": drum.froude(rpm, DRUM_R_M),
               "cohesive_index": drum.cohesive_index([p for p, v in zip(prof, valid) if v], radius)}
        if rpm <= 5 and good.size > 5:
            av = drum.avalanches(t[valid], good, deg_per_frame=6.0 * rpm / a.fps)
            row["avalanches"] = av.to_dict()
        speeds.append(row)
        ctx.say("{:g} rpm: {:.1f} +- {:.1f} deg{}".format(
            rpm, row["dynamic_deg"] or float("nan"), row["dynamic_sd"] or float("nan"),
            "; avalanches {:.1f} -> {:.1f} deg".format(row["avalanches"]["start_mean"], row["avalanches"]["stop_mean"])
            if "avalanches" in row and row["avalanches"]["n"] else ""))
    res = {"fill_fraction": fill, "center_px": center, "radius_px": radius, "speeds": speeds}
    if ctx.world:
        p = ctx.world.p
        res["sim_truth"] = {"start": p["drum_start"], "stop": p["drum_stop"], "dynamic_at_rpm":
                            {str(r): p["drum_dyn"] + 0.4 * r for r in floats(a.rpms) if r > 2}}
    need = min(60.0, 0.67 * a.seconds)
    checks = [
        check("fill 40 +- 5 % of the drum", abs(fill - 0.40) <= 0.05, fill, "0.35-0.45"),
        check(">= {:g} s of valid frames per speed".format(need), all(s["valid_s"] >= need for s in speeds),
              [s["valid_s"] for s in speeds], need),
        check("< 10 % of frames rejected (fit R^2 < 0.9)", all(s["rejected_frac"] < 0.10 for s in speeds),
              [round(s["rejected_frac"], 3) for s in speeds], 0.10),
    ]
    return res, checks
