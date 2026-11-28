"""Accuracy of the measurement chain on synthetic data with known answers.

    python -m bench.accuracy                 # tables + figures into figures/
    python -m bench.accuracy --quick         # fewer cases (about 1 min)

Part 1 runs each analysis on many synthetic images or streams (noise,
blur, roughness, touching grains, balance lag) and reports the error
against the truth. Part 2 runs every SOP end to end in --sim (the real
accessory firmware on fakes, the mock doser through the bridge code, the
simulated powder) and compares its result with the simulated truth.
"""

import argparse
import json
import math
import os
import tempfile

import numpy as np

from . import synth
from .analysis import column, drum, faraday, heap, humidity, orifice, plate, psd, spread, ucs

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(os.path.dirname(HERE), "figures")


def _stats(err):
    e = np.asarray(err, float)
    return {"n": int(e.size), "mean": float(e.mean()), "max_abs": float(np.abs(e).max()),
            "rms": float(np.sqrt(np.mean(e ** 2)))}


def part1(quick=False):
    rows = []
    rng = np.random.default_rng(0)

    def add(test, quantity, unit, err, target, note=""):
        s = _stats(err)
        rows.append({"test": test, "quantity": quantity, "unit": unit, **s, "target": target, "note": note})

    # 1 heap: flank angle vs grain-scale roughness
    angles = [25.0, 30.0, 35.0, 40.0, 45.0, 50.0] if not quick else [28.0, 38.0, 48.0]
    heap_sweep = {}
    for rough in (0.0, 0.03, 0.05, 0.1):
        err, apex, vol = [], [], []
        for k, a in enumerate(angles):
            for asym in (0.0, 3.0):
                img, tr = synth.heap_image(a, a + asym, round_mm=1.0 + 0.5 * (k % 2), rough_mm=rough,
                                           seed=int(a * 10 + asym + rough * 1000))
                ref, _ = synth.heap_image(a, a + asym, empty=True, seed=1)
                r = heap.analyze_heap(img, 28.6, ref=ref)
                err += [r.left_deg - tr["left_deg"], r.right_deg - tr["right_deg"]]
                apex.append(r.apex_deg - tr["apex_deg"])
                vol.append(100.0 * (r.volume_mm3 / tr["volume_mm3"] - 1))
        heap_sweep[rough] = (angles, err)
        add("1 heap", "flank angle, roughness {:g} mm".format(rough), "deg", err, "0.5",
            "noise 0.02, blur 1 px, rounded apex")
        if rough == 0.03:
            add("1 heap", "apex angle atan(2h/D)", "deg", apex, "-")
            add("1 heap", "heap volume", "%", vol, "-")

    # 2 column height, Kawakita
    err = []
    for i in range(8 if not quick else 4):
        h = rng.uniform(15, 70)
        img, _ = synth.column_image(h, tilt_mm=rng.uniform(0, 0.3), bump_mm=rng.uniform(-0.3, 0.3), seed=i)
        err.append(column.column_top(img, 16.0, 1220, (72, 248), axis_x=159.5).top_mm - h)
    add("2 density", "column height (16 px/mm)", "mm", err, "0.05", "mound/crater and tilt, graduations")
    ea, eb = [], []
    for i in range(20):
        a, ib = rng.uniform(0.08, 0.35), rng.uniform(5, 40)
        taps = [0, 1, 2, 5, 10, 20, 50, 100, 200, 500, 1250]
        v = synth.kawakita_volumes(taps, 8.0, a, 1 / ib) + rng.normal(0, 0.003, 11)
        d = column.densities(6.0, taps, v)
        ea.append(d.kawakita_a - a)
        eb.append(100 * (d.kawakita_inv_b / ib - 1))
    add("2 density", "Kawakita a (volume noise 0.003 mL)", "-", ea, "-")
    add("2 density", "Kawakita 1/b", "%", eb, "-")

    # 3 plate: slip angle from frames + IMU; wall friction
    es = []
    for i in range(6 if not quick else 3):
        st = rng.uniform(20, 45)
        ts = np.arange(0, st + 3, 0.2)
        fr = synth.ring_frames(ts, st, seed=i)
        t_s, _ = plate.detect_slip(ts, plate.ring_displacement(fr, 12.0))
        t, deg, jolt = synth.imu_ramp(0.5, st + 3, 20, 0.0, slip_t=st, seed=i)
        es.append(plate.ramp_angle_at(t_s, t, deg, t_s) - 0.5 * st)
    add("3 plate", "slip angle (5 fps camera, 20 Hz IMU)", "deg", es, "0.5 (about +-2 on phi_w)")
    ep, ec = [], []
    area = math.pi * 12.5 ** 2
    for i in range(30):
        phi, cw = rng.uniform(15, 35), rng.uniform(0, 30)
        sig, tau = [], []
        for lid in (0, 5, 15):
            for _ in range(3):
                m = 5.5 + lid
                s_, t_ = plate.stresses_at_slip(m, synth.slip_angle_for(m, area, phi, cw) + rng.normal(0, 0.25), area)
                sig.append(s_)
                tau.append(t_)
        wf = plate.wall_friction_fit(sig, tau)
        ep.append(wf.phi_w_deg - phi)
        ec.append(wf.c_w_pa - cw)
    add("3 plate", "phi_w (3 lids x 3, slip SD 0.25 deg)", "deg", ep, "2")
    add("3 plate", "wall adhesion c_w", "Pa", ec, "-")

    # 4 PSD
    psd_runs = []
    for rep in range(3 if not quick else 1):
        tabs, truths = [], []
        for f in range(6):
            img, tr = synth.particle_field(n=170, d50_px=30, gsd=1.4, seed=100 * rep + f)
            tabs.append(psd.analyze_field(img, 1.0, field=f))
            truths.append(tr)
        s = psd.psd_summary(psd.merge(tabs), n_boot=100, by_field=True, um_per_px=1.0)
        psd_runs.append((s, tabs, truths))
    for q, key in ((0.1, "d10_n"), (0.5, "d50_n"), (0.9, "d90_n")):
        add("4 PSD", "{} (number), 6 fields, 15 % touching".format(key[:3]), "%",
            [100 * (r[0][key] / synth.lognormal_quantile(30, 1.4, q) - 1) for r in psd_runs], "5")
    add("4 PSD", "d50 (volume)", "%", [100 * (r[0]["d50_v"] / synth.lognormal_quantile(30, 1.4, 0.5, "volume") - 1)
                                       for r in psd_runs], "-", "few big grains set it: sampling error")
    add("4 PSD", "grain count after watershed", "%",
        [100 * (r[0]["n"] / sum(int((~t["edge"]).sum()) for t in r[2]) - 1) for r in psd_runs], "-")

    # 5 orifice
    ew = []
    for D in (6.0, 5.08, 4.0, 3.0, 2.54, 2.0, 1.5):
        W = synth.beverloo_rate_g_s(D, 0.58, 1.5, 0.4, 1200)
        t, m, _ = synth.balance_stream(W, 5.0, hz=10, lag_s=0.25, seed=int(D * 100))
        ew.append(100 * (orifice.flow_rate(t, m, lag_s=0.25).rate_g_s / W - 1))
    add("5 orifice", "flow rate, 10 Hz, 0.25 s balance lag corrected", "%", ew, "-")
    eC, ek = [], []
    for i in range(20):
        Ds = [6.0, 5.08, 4.0, 3.0, 2.54, 2.0]
        W = [synth.beverloo_rate_g_s(D, 0.58, 1.5, 0.4, 1200) * rng.normal(1, 0.02) for D in Ds]
        bf = orifice.beverloo_fit(Ds, W, 1200, 0.4)
        eC.append(100 * (bf.C / 0.58 - 1))
        ek.append(bf.k - 1.5)
    add("5 orifice", "Beverloo C (2 % rate scatter)", "%", eC, "-")
    add("5 orifice", "Beverloo k", "-", ek, "-")

    # 6 humidity
    eu, et = [], []
    for i in range(20):
        ue, tau = rng.uniform(1, 80), rng.uniform(1, 8)
        t, u = synth.uptake_series(ue, tau, noise=0.02 * ue + 0.05, seed=i)
        f = humidity.uptake_fit(t, u)
        eu.append(100 * (f.u_eq / ue - 1))
        et.append(100 * (f.tau_h / tau - 1))
    add("6 humidity", "u_eq (6 weighings, 2 % noise)", "%", eu, "-")
    add("6 humidity", "tau", "%", et, "-")

    # 7 drum
    ed = []
    for i, ang in enumerate(np.linspace(20, 55, 8 if not quick else 4)):
        img, tr = synth.drum_image(float(ang), seed=i, curve_px=0.0)
        xs, ys = drum.surface_profile(img, tr["center"], tr["radius_px"])
        ed.append(drum.surface_angle(xs, ys).angle_deg - ang)
    add("7 drum", "free-surface angle (12 px/mm)", "deg", ed, "0.5")
    es_, eo = [], []
    for i in range(5):
        t, a, tr = synth.drum_angle_series(1.0, 120, 10, 42, 34, 1.0, noise=0.2, seed=i)
        av = drum.avalanches(t, a, deg_per_frame=0.6)
        es_.append(av.start_mean - np.mean(tr["starts"]))
        eo.append(av.stop_mean - np.mean(tr["stops"]))
    add("7 drum", "avalanche start angle (1 rpm, 10 fps)", "deg", es_, "-")
    add("7 drum", "avalanche stop angle", "deg", eo, "-")

    # 8 UCS
    ep = []
    for i, pk in enumerate((0.3, 1.0, 3.2, 8.0, 20.0)):
        t, g, _ = synth.ucs_stream(pk, seed=i)
        ep.append(100 * (ucs.peak_force(t, g).peak_g / pk - 1))
    add("8 UCS", "peak force (2 mg noise, 80 Hz)", "%", ep, "-")

    # 9 spreading
    ec_, es2 = [], []
    for i in range(6):
        img, tr = synth.spread_image(coverage_void=rng.uniform(0.02, 0.2), n_streaks=int(rng.integers(1, 5)), seed=i)
        m = spread.covered_mask(img)
        ec_.append(100 * (spread.coverage(m) - tr["coverage"]))
        es2.append(100 * (spread.streaks(m)[0] / tr["streak_frac"] - 1))
    add("9 spread", "coverage", "% points", ec_, "-")
    add("9 spread", "streak area", "%", es2, "-")

    # 10 Faraday
    eq = []
    for i in range(10):
        dq = rng.uniform(1, 100)
        t, q, _ = synth.charge_stream(dq, drift_nc_s=rng.uniform(-0.02, 0.02), seed=i)
        eq.append(faraday.charge_step(t, q, 5.0, 8.0).dq_nc - dq)
    add("10 Faraday", "charge step (drift corrected)", "nC", eq, "-")
    return rows, heap_sweep, psd_runs


SIM_RUNS = [
    ("1 heap", ["heap", "--jar", "NaCl-01", "--pours", "3"],
     lambda r: [("flank angle", "deg", r["flank_deg_mean"], r["sim_truth_aor_deg"])]),
    ("2 density", ["density", "--jar", "NaCl-01"],
     lambda r: [("bulk density", "kg/m3", r["rho_bulk"], r["sim_truth"]["rho_bulk"]),
                ("Kawakita a", "-", r["kawakita_a"], r["sim_truth"]["kawakita_a"]),
                ("Kawakita 1/b", "taps", r["kawakita_inv_b"], r["sim_truth"]["kawakita_inv_b"])]),
    ("3 plate", ["plate", "--jar", "NaCl-01", "--lids", "0,5,15", "--repeats", "2", "--fast-to", "20"],
     lambda r: [("phi_w", "deg", r["wall_friction"]["phi_w_deg"], r["sim_truth"]["phi_w_deg"]),
                ("c_w", "Pa", r["wall_friction"]["c_w_pa"], r["sim_truth"]["c_w_pa"])]),
    ("4 PSD", ["psd", "--jar", "NaCl-01", "--fields", "6", "--min-grains", "600", "--boot", "200"],
     lambda r: [("d50 (number)", "um", r["d50_n"], r["sim_truth"]["d50_n_um"])]),
    ("5 orifice", ["orifice", "--jar", "NaCl-01", "--rho-b", "1250", "--d50-um", "425",
                   "--discs", "6,5.08,4,3,2.54,2,1.5,1,0.8"],
     lambda r: [("Beverloo C", "-", r["beverloo"]["C"], r["sim_truth"]["C"]),
                ("Beverloo k", "-", r["beverloo"]["k"], r["sim_truth"]["k"]),
                ("D_c", "mm", r["dc_mm"], r["sim_truth"]["dc_mm"]),
                ("D_c tapped", "mm", r["dc_tapped_mm"], r["sim_truth"]["dc_tap_mm"])]),
    ("6 humidity", ["humidity", "--jar", "NaCl-01", "--box", "NaCl"],
     lambda r: [("u_eq at 75 % RH", "mg/g", r["fit"]["u_eq"], r["sim_truth"]["u_eq"])]),
    ("7 drum", ["drum", "--jar", "NaCl-01", "--rpms", "1,10", "--seconds", "12", "--fps", "5", "--save-every", "60"],
     lambda r: [("dynamic angle at 10 rpm", "deg", r["speeds"][1]["dynamic_deg"],
                 r["sim_truth"]["dynamic_at_rpm"]["10.0"]),
                ("avalanche start at 1 rpm", "deg", r["speeds"][0]["avalanches"]["start_mean"], r["sim_truth"]["start"]),
                ("avalanche stop at 1 rpm", "deg", r["speeds"][0]["avalanches"]["stop_mean"], r["sim_truth"]["stop"])]),
    ("8 UCS", ["ucs", "--jar", "flour-01", "--sigma1-kpa", "0.5,1,2", "--max-travel", "4"],
     lambda r: [("sigma_c at 1 kPa", "Pa", r["samples"][1]["sigma_c_pa"], r["sim_truth"]["sigma_c_pa"][1])]),
    ("9 spread", ["spread", "--jar", "NaCl-01", "--speeds", "30", "--layers", "2", "--rho-true", "2165"],
     lambda r: [("coverage", "-", r["layers"][0]["coverage"], r["layers"][0]["sim_truth"]["coverage"])]),
    ("10 Faraday", ["faraday", "--jar", "NaCl-01"],
     lambda r: [("q/m", "uC/kg", 1e6 * r["q_per_m_mean_c_kg"], 1e6 * r["sim_truth_q_per_m_c_kg"])]),
]


def part2():
    import contextlib
    import io

    from . import run as bench_run
    rows = []
    with tempfile.TemporaryDirectory() as tmp:
        for test, argv, pick in SIM_RUNS:
            out = os.path.join(tmp, test.split()[1])
            with contextlib.redirect_stdout(io.StringIO()):
                bench_run.main(argv + ["--sim", "--out", out])
            d = sorted(os.listdir(out))[-1]
            with open(os.path.join(out, d, "results.json")) as f:
                res = json.load(f)
            n_pass = sum(c["pass"] for c in res["checks"])
            for q, unit, got, truth in pick(res["results"]):
                rows.append({"test": test, "quantity": q, "unit": unit, "measured": got, "truth": truth,
                             "error": got - truth, "checks": "{}/{}".format(n_pass, len(res["checks"]))})
    return rows


def figures(heap_sweep, psd_runs):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    blue, orange, aqua = "#257de0", "#f47230", "#00b894"
    ink, ink2, grid = "#191919", "#666666", "#e6e6e6"
    plt.rcParams.update({"font.size": 9, "axes.edgecolor": ink2, "axes.labelcolor": ink, "xtick.color": ink2,
                         "ytick.color": ink2, "axes.spines.top": False, "axes.spines.right": False,
                         "axes.grid": True, "grid.color": grid, "grid.linewidth": 0.6})
    os.makedirs(FIG, exist_ok=True)

    # Figure 1: heap fit overlay + angle error vs roughness
    img, tr = synth.heap_image(33.0, 36.0, round_mm=1.2, rough_mm=0.03, seed=5)
    ref, _ = synth.heap_image(33.0, 36.0, empty=True, seed=1)
    r = heap.analyze_heap(img, 28.6, ref=ref)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 3.8), gridspec_kw={"width_ratios": [1.25, 1]})
    a1.imshow(img, cmap="gray", vmin=0, vmax=1)
    a1.grid(False)
    h = r.base_row - r.apex_row
    ys = np.linspace(r.base_row - 0.85 * h, r.base_row - 0.15 * h, 2)
    for side, color, name in (("left", blue, "left"), ("right", orange, "right")):
        f = r.fits[side]
        ys_full = np.linspace(r.apex_row - 10, r.base_row, 2)
        a1.plot(f["slope"] * ys_full + f["intercept"], ys_full, color=color, lw=1, ls=(0, (3, 2)))
        a1.plot(f["slope"] * ys + f["intercept"], ys, color=color, lw=2)
    a1.axhline(r.base_row, color=aqua, lw=1)
    a1.text(130, 140, "left  {:.2f} deg (true 33.00)\nright {:.2f} deg (true 36.00)".format(
        r.left_deg, r.right_deg), color=ink, fontsize=8, family="monospace", va="top")
    a1.set_xlim(120, 780)
    a1.set_ylim(520, 110)
    a1.set_xticks([])
    a1.set_yticks([])
    a1.set_title("Synthetic heap: flank fits (solid: 15-85 % of height), base line from\nthe empty-pedestal "
                 "image (aqua)", fontsize=9, color=ink, loc="left")
    for rough, color, label in ((0.0, blue, "smooth"), (0.05, orange, "0.05 mm rough"), (0.1, aqua, "0.1 mm rough")):
        angles, err = heap_sweep[rough]
        xs = np.repeat(angles, 4)
        a2.plot(xs + {0.0: -0.6, 0.05: 0.0, 0.1: 0.6}[rough], err, "o", ms=4, color=color, mec="white", mew=0.6,
                label=label)
    a2.axhspan(-0.5, 0.5, color="#f2f2f2", zorder=0)
    a2.axhline(0, color=ink2, lw=0.8)
    a2.set_xlabel("true flank angle (deg)")
    a2.set_ylabel("fitted minus true (deg)")
    a2.set_title("Flank angle error; band = 0.5 deg target", fontsize=9, color=ink, loc="left")
    a2.legend(frameon=False, fontsize=8, loc="lower left")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "heap_fit.png"), dpi=130)
    plt.close(fig)

    # Figure 2: PSD recovery
    s, tabs, truths = psd_runs[0]
    img, tr = synth.particle_field(n=170, d50_px=30, gsd=1.4, seed=0)
    mask = psd.segment(img)
    lab = psd.split_touching(mask)
    from skimage.segmentation import find_boundaries
    fig, (b1, b2) = plt.subplots(1, 2, figsize=(10, 3.8), gridspec_kw={"width_ratios": [1.25, 1]})
    crop = (slice(0, 384), slice(0, 512))
    b1.imshow(img[crop], cmap="gray", vmin=0, vmax=1)
    bd = find_boundaries(lab[crop], mode="inner")
    yy, xx = np.nonzero(bd)
    b1.plot(xx, yy, ",", color=orange)
    b1.grid(False)
    b1.set_xticks([])
    b1.set_yticks([])
    b1.set_title("Synthetic field: watershed outlines (touching grains split)", fontsize=9, color=ink, loc="left")
    ecd = np.concatenate([t["ecd_um"] for t in tabs])
    w = np.concatenate([t["weight"] for t in tabs])
    o = np.argsort(ecd)
    cw = np.cumsum(w[o]) / w.sum()
    x = np.linspace(10, 80, 300)
    from scipy.stats import norm
    b2.plot(x, norm.cdf(np.log(x / 30.0) / math.log(1.4)), color=blue, lw=2, label="true lognormal (d50 30 px)")
    b2.step(ecd[o], cw, where="post", color=orange, lw=1.2, label="measured, {} grains".format(ecd.size))
    b2.axvline(s["d50_n"], color=ink2, lw=0.8, ls=(0, (3, 2)))
    b2.text(s["d50_n"] + 1, 0.08, "d50 {:.1f} px".format(s["d50_n"]), color=ink, fontsize=8)
    b2.set_xlabel("area-equivalent diameter (px)")
    b2.set_ylabel("cumulative number fraction")
    b2.set_title("Number distribution recovered", fontsize=9, color=ink, loc="left")
    b2.legend(frameon=False, fontsize=8, loc="lower right")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "psd_recovery.png"), dpi=130)
    plt.close(fig)


def plate_figure():
    """IMU angle around a slip: the jolt reads as tilt; the ramp fitted just
    before the event does not. Ring displacement and the 0.5 mm threshold."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    blue, orange, aqua = "#257de0", "#f47230", "#00b894"
    ink, ink2 = "#191919", "#666666"
    rng = np.random.default_rng(3)
    slip_t, rate = 41.37, 0.5
    t100 = np.arange(36.0, 44.0, 0.01)
    true = rate * t100
    a_along = np.sin(np.radians(true)) + rng.normal(0, 0.0005, t100.size)
    a_norm = np.cos(np.radians(true))
    jolt = np.where((t100 >= slip_t) & (t100 < slip_t + 0.04), 0.05, 0.0)
    raw = np.degrees(np.arctan2(a_along + jolt, a_norm))
    avg = np.convolve(raw, np.ones(8) / 8, mode="full")[: raw.size]
    t20, d20 = t100[::5], avg[::5]
    frames_t = np.arange(36.0, 44.0, 0.2)
    frames = synth.ring_frames(frames_t, slip_t, seed=2, x0_mm=5.0)
    disp = plate.ring_displacement(frames, 12.0)
    t_s, _ = plate.detect_slip(frames_t, disp)
    fit_at = plate.ramp_angle_at(t_s, t20, d20, t_s)
    naive = plate.angle_at(t_s, t20, d20)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 3.4))
    a1.plot(t20, d20, color=blue, lw=1.2, label="IMU angle, 20 Hz (8-sample mean)")
    tt = np.linspace(slip_t - 5.2, slip_t + 1.0, 2)
    a1.plot(tt, rate * tt, color=orange, lw=1.2, ls=(0, (4, 2)), label="ramp fitted 5 s before the event")
    a1.plot([t_s], [fit_at], "o", ms=6, color=orange, mec="white", mew=0.8)
    a1.plot([t_s], [naive], "o", ms=6, color=blue, mec="white", mew=0.8)
    a1.annotate("fit: {:.2f} deg (true {:.2f})".format(fit_at, rate * slip_t), (t_s, fit_at), (37.0, 21.2),
                fontsize=8, color=ink, arrowprops=dict(arrowstyle="-", color=ink2, lw=0.6))
    a1.annotate("IMU sample: {:.2f} deg".format(naive), (t_s, naive), (37.0, 22.0), fontsize=8, color=ink,
                arrowprops=dict(arrowstyle="-", color=ink2, lw=0.6))
    a1.set_xlim(36, 44)
    a1.set_xlabel("time (s)")
    a1.set_ylabel("plate angle (deg)")
    a1.set_title("A 0.05 g slip jolt reads as about 1.3 deg of tilt", fontsize=9, color=ink, loc="left")
    a1.legend(frameon=False, fontsize=8, loc="lower right")
    a2.plot(frames_t, disp, "o-", ms=3, lw=1.0, color=aqua, label="ring displacement, 5 fps")
    a2.axhline(0.5, color=ink2, lw=0.8, ls=(0, (3, 2)))
    a2.text(36.2, 0.7, "0.5 mm slip threshold", fontsize=8, color=ink)
    a2.axvline(t_s, color=ink2, lw=0.8)
    a2.text(t_s + 0.1, 3.0, "slip detected\n{:.2f} s (true {:.2f})".format(t_s, slip_t), fontsize=8, color=ink)
    a2.set_xlim(36, 44)
    a2.set_ylim(-0.5, 6)
    a2.set_xlabel("time (s)")
    a2.set_ylabel("displacement (mm)")
    a2.set_title("Side camera: the ring moves at the slip", fontsize=9, color=ink, loc="left")
    fig.tight_layout()
    os.makedirs(FIG, exist_ok=True)
    fig.savefig(os.path.join(FIG, "plate_slip.png"), dpi=130)
    plt.close(fig)


def markdown(rows1, rows2):
    out = ["| Test | Quantity | Unit | n | Mean error | Max abs error | RMS | Target |", "|---|---|---|---|---|---|---|---|"]
    for r in rows1:
        out.append("| {test} | {quantity} | {unit} | {n} | {mean:+.3g} | {max_abs:.3g} | {rms:.3g} | {target} |".format(**r))
    out += ["", "| Test | Quantity | Unit | Simulated run | Truth | Error | Checks passed |", "|---|---|---|---|---|---|---|"]
    for r in rows2:
        out.append("| {test} | {quantity} | {unit} | {measured:.4g} | {truth:.4g} | {error:+.3g} | {checks} |".format(**r))
    return "\n".join(out) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description="synthetic accuracy of the measurement chain")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-sim", action="store_true", help="skip the end-to-end --sim runs")
    ap.add_argument("--figures-only", action="store_true", help="redraw the figures, keep the tables")
    a = ap.parse_args(argv)
    rows1, heap_sweep, psd_runs = part1(a.quick)
    if a.figures_only:
        figures(heap_sweep, psd_runs)
        plate_figure()
        return
    rows2 = [] if a.no_sim else part2()
    os.makedirs(FIG, exist_ok=True)
    with open(os.path.join(FIG, "accuracy.json"), "w") as f:
        json.dump({"analysis": rows1, "sim_runs": rows2}, f, indent=2)
    md = markdown(rows1, rows2)
    with open(os.path.join(FIG, "accuracy.md"), "w") as f:
        f.write(md)
    figures(heap_sweep, psd_runs)
    plate_figure()
    print(md)


if __name__ == "__main__":
    main()
