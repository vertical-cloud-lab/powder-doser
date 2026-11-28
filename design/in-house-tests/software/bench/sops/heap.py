"""SOP 1: heap angle of repose (SPEC 1).

Tilt 45 deg; turn the auger one revolution at a time; photo and balance
after each; stop when the heap grows < 2 % per rev for 3 revs; 3 pours.
"""

import numpy as np

from ..analysis import heap
from .common import check

NUMBER, NAME, TITLE = 1, "heap", "Heap angle of repose"


def add_args(p):
    p.add_argument("--pours", type=int, default=3)
    p.add_argument("--tilt", type=float, default=45.0, help="doser plate degrees")
    p.add_argument("--rpm", type=float, default=None, help="auger rpm (needs the doser rpm patch)")
    p.add_argument("--max-revs", type=int, default=40)
    p.add_argument("--stop-growth", type=float, default=0.02)
    p.add_argument("--stop-n", type=int, default=3)
    p.add_argument("--pedestal-mm", type=float, default=20.0)
    p.add_argument("--px-per-mm", type=float, default=28.6, help="from the camera calibration")
    p.add_argument("--settle-s", type=float, default=2.0)


def run(ctx, a):
    if ctx.world:
        ctx.world.set_scene("heap", pedestal_mm=a.pedestal_mm, px_per_mm=a.px_per_mm)
    ctx.env("start")
    cam = ctx.camera("silhouette")
    if ctx.acc:
        ctx.acc.call("light on", check=False)
    ctx.doser.tilt(a.tilt)
    ctx.set_rpm(a.rpm)
    bal = ctx.log.stream("balance", ["t", "pour", "rev", "g"])
    growth = ctx.log.stream("heap_growth", ["pour", "rev", "g", "left_deg", "right_deg", "height_mm"])
    pours = []
    for k in range(1, a.pours + 1):
        ctx.prompt("Pour {}: clear the pedestal (tip any heap back into the jar), close the breeze break".format(k),
                   action="new_heap")
        ctx.doser.tare()
        ctx.sleep(a.settle_s)
        ref = ctx.camera("silhouette").capture()
        ctx.log.image("pour{}_rev00_ref".format(k), ref)
        masses = []
        stopped = False
        for rev in range(1, a.max_revs + 1):
            ctx.doser.rotate(360)
            ctx.sleep(a.settle_s)
            g = ctx.weigh()
            masses.append(g)
            bal.write([ctx.now(), k, rev, g])
            img = cam.capture()
            ctx.log.image("pour{}_rev{:02d}".format(k, rev), img)
            try:
                r = heap.analyze_heap(img, a.px_per_mm, ref=ref, mass_g=g)
                growth.write([k, rev, g, r.left_deg, r.right_deg, r.height_mm])
            except ValueError:
                growth.write([k, rev, g, None, None, None])
            if heap.growth_stopped(masses, a.stop_growth, a.stop_n):
                stopped = True
                break
        img = cam.capture()
        ctx.log.image("pour{}_final".format(k), img)
        r = heap.analyze_heap(img, a.px_per_mm, ref=ref, mass_g=masses[-1])
        d = r.to_dict()
        d.update(pour=k, revs=len(masses), stopped=stopped, avalanches_g=heap.avalanche_drops(masses))
        pours.append(d)
        ctx.say("pour {}: flanks {:.1f} / {:.1f} deg, apex {:.1f} deg, {:.3f} g, {:.0f} kg/m3".format(
            k, r.left_deg, r.right_deg, r.apex_deg, masses[-1], r.density_kg_m3 or float("nan")))
    flank = np.array([p["flank_deg"] for p in pours])
    res = {
        "pours": pours,
        "flank_deg_mean": float(flank.mean()),
        "flank_deg_sd": float(flank.std(ddof=1)) if len(flank) > 1 else None,
        "apex_deg_mean": float(np.mean([p["apex_deg"] for p in pours])),
        "density_kg_m3_mean": float(np.mean([p["density_kg_m3"] for p in pours])),
        "heap_g_mean": float(np.mean([p["mass_g"] for p in pours])),
        "avalanches_n": int(sum(len(p["avalanches_g"]) for p in pours)),
    }
    if ctx.world:
        res["sim_truth_aor_deg"] = ctx.world.p["aor"]
    sd = res["flank_deg_sd"]
    checks = [
        check("heap stopped growing (< {:.0%}/rev for {} revs)".format(a.stop_growth, a.stop_n),
              all(p["stopped"] for p in pours), [p["revs"] for p in pours]),
        check("flank fit RMS residual <= 0.1 mm", all(max(p["rms_left_px"], p["rms_right_px"]) / a.px_per_mm <= 0.1
                                                       for p in pours),
              [round(max(p["rms_left_px"], p["rms_right_px"]) / a.px_per_mm, 4) for p in pours], 0.1),
        check("left-right flank difference <= 3 deg",
              all(abs(p["left_deg"] - p["right_deg"]) <= 3.0 for p in pours),
              [round(p["left_deg"] - p["right_deg"], 2) for p in pours], 3.0),
        check("SD of the flank angle over pours <= 1 deg", sd is not None and sd <= 1.0, sd, 1.0),
    ]
    return res, checks
