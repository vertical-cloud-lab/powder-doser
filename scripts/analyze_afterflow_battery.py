#!/usr/bin/env python3
"""Analyze the afterflow characterization battery (PR #131, tests C6-C8/B4/B5).

Parses the CSV telemetry emitted by
``hardware/test-module/firmware/afterflow_battery.py`` and produces:

  * a text report (noise floor, per-test afterflow / tau summaries),
  * ``afterflow_trials.csv`` (one row per stop-response trial),
  * ``afterflow_flow.csv`` (one row per continuous B4/B5 run),
  * two figures: (1) the afterflow decomposition + tau across C6 (tilt x
    halt mass) and C7 (vs auger speed); (2) the actuator decomposition
    (C8), the max-rate feed map (B4) and the fill drawdown (B5).

Flow-at-halt for tau is estimated from the *slope of the pre-halt mass
trajectory* (last ~1.5 s of dispense samples), not from m_trig/t_disp --
so the tau numerator (afterflow) and denominator (flow) come from
disjoint parts of the trace, avoiding the ratio self-correlation Edison
flagged for the 08-07 pilot.

Usage:
    python scripts/analyze_afterflow_battery.py \
        data/afterflow/2026-08-12_salt/afterflow_battery_salt.log
"""

import csv
import statistics
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

SURFACE = "#fcfcfb"
TEXT_1 = "#0b0b0b"
TEXT_2 = "#52514e"
GRID = "#e5e4e0"
# sequential single-hue ramp (light->dark) for tilt = a magnitude
ANGLE_RAMP = ["#b3cdf0", "#7fabe4", "#5492dc", "#2a78d6", "#1a4e90"]
ACCENT = "#eb6834"   # orange: afterflow component
ACCENT2 = "#12855f"  # green: second series
FLOW_WIN_S = 1.5     # pre-halt window for the flow slope


def mg(x):
    return x * 1000.0


def parse(path):
    meta, events, samples, trials = {}, [], [], []
    for line in Path(path).read_text().splitlines():
        f = line.split(",")
        if f[0] == "M" and len(f) >= 3:
            meta[f[1]] = ",".join(f[2:])
        elif f[0] == "E" and len(f) >= 3:
            events.append((int(f[1]), ",".join(f[2:])))
        elif f[0] == "D" and len(f) >= 8:
            samples.append({
                "t": int(f[1]) / 1000.0, "trial": int(f[2]),
                "phase": f[3],
                "mass": None if f[4] == "nan" else float(f[4]),
                "flag": f[5], "rpm": float(f[6]), "taps": int(f[7])})
        elif f[0] == "R" and len(f) >= 16:
            def fl(x):
                return None if x == "nan" else float(x)
            trials.append({
                "trial": int(f[1]), "test": f[2], "tilt": float(f[3]),
                "rep": int(f[4]), "rpm": float(f[5]), "halt_g": float(f[6]),
                "mode": f[7], "m_trig": fl(f[8]), "t_disp_s": float(f[9]),
                "m_settled": fl(f[10]), "m_settled2": fl(f[11]),
                "dispensed": fl(f[12]), "cum": float(f[13]),
                "taps": int(f[14]), "verdict": f[15]})
    return meta, events, samples, trials


def slope(pts):
    """Least-squares slope (g/s) of (t, mass) points; None if <3 pts."""
    n = len(pts)
    if n < 3:
        return None
    sx = sum(t for t, _ in pts)
    sy = sum(m for _, m in pts)
    sxx = sum(t * t for t, _ in pts)
    sxy = sum(t * m for t, m in pts)
    den = n * sxx - sx * sx
    if abs(den) < 1e-9:
        return None
    return (n * sxy - sx * sy) / den


def second_diff_sigma(masses):
    if len(masses) < 3:
        return 0.0
    d2 = [masses[i + 1] - 2 * masses[i] + masses[i - 1]
          for i in range(1, len(masses) - 1)]
    return statistics.pstdev(d2) / 6 ** 0.5


def flow_at_halt(samples, trial):
    """Slope of the last FLOW_WIN_S of the dispense phase (g/s)."""
    disp = [(s["t"], s["mass"]) for s in samples
            if s["trial"] == trial and s["phase"] == "dispense"
            and s["mass"] is not None]
    if len(disp) < 3:
        return None
    t_end = disp[-1][0]
    win = [(t, m) for t, m in disp if t >= t_end - FLOW_WIN_S]
    return slope(win if len(win) >= 3 else disp)


def main(path):
    meta, events, samples, trials = parse(path)
    outdir = Path(path).parent
    powder = meta.get("powder_id", "salt")

    # ---- static noise baseline (trial 0, phase noise) ----------------
    noise = [s for s in samples if s["trial"] == 0 and s["phase"] == "noise"
             and s["mass"] is not None]
    nm = [s["mass"] for s in noise]
    n_dur = noise[-1]["t"] - noise[0]["t"]
    rate = (len(noise) - 1) / n_dur
    t_quiet = noise[0]["t"] + 12.0
    quiet = [s["mass"] for s in noise if s["t"] > t_quiet]
    quiet_sd = statistics.pstdev(quiet)
    quiet_hf = second_diff_sigma(quiet)
    print("== static noise baseline (0 deg, nothing moving) ==")
    print(f"  {len(noise)} samples / {n_dur:.1f} s ({rate:.1f} Hz); "
          f"full sd {mg(statistics.pstdev(nm)):.2f} mg")
    print(f"  quiet region: sd {mg(quiet_sd):.3f} mg, "
          f"2nd-diff sigma {mg(quiet_hf):.3f} mg (0.1 mg quantum)")

    # ---- per-trial enrichment ---------------------------------------
    rows = []
    for tr in trials:
        r = dict(tr)
        r["flow_slope"] = flow_at_halt(samples, tr["trial"])
        if tr["mode"] in ("rot", "auger") and tr["m_trig"] is not None \
                and tr["m_settled2"] is not None:
            r["afterflow"] = tr["m_settled2"] - tr["m_trig"]
            r["trig_over"] = tr["m_trig"] - tr["halt_g"]
            fl = r["flow_slope"]
            r["tau"] = (r["afterflow"] / fl) if (fl and fl > 1e-4) else None
        else:
            r["afterflow"] = r["trig_over"] = r["tau"] = None
        rows.append(r)

    # ---- C6: factorial stop-response (tilt x halt mass) --------------
    print("\n== C6: afterflow & tau (tap-while-rotating, 55 rpm) ==")
    print("tilt halt  n  afterflow_mg(sd)  flow_g/s   tau_s(sd)")
    c6 = [r for r in rows if r["test"] == "C6" and r["afterflow"] is not None]
    c6_cells = {}
    for tilt in sorted({r["tilt"] for r in c6}):
        for halt in sorted({r["halt_g"] for r in c6 if r["tilt"] == tilt}):
            cell = [r for r in c6 if r["tilt"] == tilt and r["halt_g"] == halt]
            af = [mg(r["afterflow"]) for r in cell]
            fl = [r["flow_slope"] for r in cell if r["flow_slope"]]
            ta = [r["tau"] for r in cell if r["tau"]]
            c6_cells[(tilt, halt)] = {
                "af": af, "flow": fl, "tau": ta,
                "af_m": statistics.mean(af),
                "af_sd": statistics.pstdev(af) if len(af) > 1 else 0.0,
                "tau_m": statistics.mean(ta) if ta else float("nan"),
                "tau_sd": statistics.pstdev(ta) if len(ta) > 1 else 0.0,
                "flow_m": statistics.mean(fl) if fl else float("nan")}
            c = c6_cells[(tilt, halt)]
            print(f"{tilt:4.0f} {halt:4.2f} {len(af):2d}  "
                  f"{c['af_m']:6.1f} ({c['af_sd']:4.1f})   "
                  f"{c['flow_m']:6.3f}   {c['tau_m']:4.2f} ({c['tau_sd']:.2f})")
    all_tau = [r["tau"] for r in c6 if r["tau"]]
    print(f"  pooled C6 tau = {statistics.mean(all_tau):.2f} +/- "
          f"{statistics.pstdev(all_tau):.2f} s (n={len(all_tau)})")

    # ---- C7: afterflow vs auger speed (55 deg, auger-only) -----------
    print("\n== C7: afterflow vs auger speed (55 deg, auger-only, 0.5 g) ==")
    print("rpm  n  afterflow_mg(sd)  flow_g/s(sd)   tau_s")
    c7 = [r for r in rows if r["test"] == "C7" and r["afterflow"] is not None]
    c7_pts = []
    for rpm in sorted({r["rpm"] for r in c7}):
        cell = [r for r in c7 if r["rpm"] == rpm]
        af = [mg(r["afterflow"]) for r in cell]
        fl = [r["flow_slope"] for r in cell if r["flow_slope"]]
        ta = [r["tau"] for r in cell if r["tau"]]
        c7_pts.append({
            "rpm": rpm, "af_m": statistics.mean(af),
            "af_sd": statistics.pstdev(af) if len(af) > 1 else 0.0,
            "flow_m": statistics.mean(fl) if fl else float("nan"),
            "flow_sd": statistics.pstdev(fl) if len(fl) > 1 else 0.0,
            "tau_m": statistics.mean(ta) if ta else float("nan")})
        p = c7_pts[-1]
        print(f"{rpm:3.0f} {len(af):2d}  {p['af_m']:6.1f} ({p['af_sd']:4.1f})"
              f"   {p['flow_m']:.3f} ({p['flow_sd']:.3f})   {p['tau_m']:.2f}")
    # linearity: afterflow (g) = a + b*flow ; b has units of s (tau)
    fx = [p["flow_m"] for p in c7_pts if p["flow_m"] == p["flow_m"]]
    fy = [p["af_m"] / 1000.0 for p in c7_pts if p["flow_m"] == p["flow_m"]]
    if len(fx) >= 2:
        b = slope(list(zip(fx, fy)))
        a = statistics.mean(fy) - b * statistics.mean(fx)
        print(f"  linear fit afterflow = {mg(a):+.1f} mg + {b:.2f} s * flow")
        print(f"  -> intercept {mg(a):+.1f} mg (speed-independent lip dump), "
              f"slope tau={b:.2f} s")

    # ---- C8: actuator decomposition (55 deg / 0.5 g) -----------------
    print("\n== C8: actuator decomposition (55 deg, 0.5 g) ==")
    c8 = [r for r in rows if r["test"] == "C8"]
    c8_summary = {}
    for mode in ("auger", "rot", "taponly"):
        cell = [r for r in c8 if r["mode"] == mode]
        if mode == "taponly":
            # taponly: 'dispensed' is total from 15 single taps after prime
            vals = [mg(r["dispensed"]) for r in cell if r["dispensed"] is not None]
            if vals:
                c8_summary[mode] = {"metric": "15-tap total (mg)",
                                    "m": statistics.mean(vals),
                                    "sd": statistics.pstdev(vals) if len(vals) > 1 else 0.0,
                                    "n": len(vals)}
        else:
            af = [mg(r["afterflow"]) for r in cell if r["afterflow"] is not None]
            if af:
                c8_summary[mode] = {"metric": "afterflow (mg)",
                                    "m": statistics.mean(af),
                                    "sd": statistics.pstdev(af) if len(af) > 1 else 0.0,
                                    "n": len(af)}
    for mode, s in c8_summary.items():
        print(f"  {mode:8s} {s['metric']:20s}: {s['m']:6.1f} "
              f"(sd {s['sd']:4.1f}, n={s['n']})")
    if "auger" in c8_summary and "rot" in c8_summary:
        d = c8_summary["rot"]["m"] - c8_summary["auger"]["m"]
        print(f"  tap contribution to afterflow (rot - auger): {d:+.1f} mg")

    # ---- B4: max-rate feed map (continuous) --------------------------
    print("\n== B4: max-rate feed map (6 s continuous, 55 rpm) ==")
    b4 = [r for r in rows if r["test"] == "B4" and r["m_settled2"] is not None]
    b4_pts = []
    for tilt in sorted({r["tilt"] for r in b4}):
        cell = [r for r in b4 if r["tilt"] == tilt]
        fl = [r["m_settled2"] / r["t_disp_s"] for r in cell
              if r["m_settled2"] and r["t_disp_s"]]
        if fl:
            b4_pts.append({"tilt": tilt, "flow_m": statistics.mean(fl),
                           "flow_sd": statistics.pstdev(fl) if len(fl) > 1 else 0.0})
            print(f"  tilt {tilt:4.0f} deg: flow "
                  f"{b4_pts[-1]['flow_m']:.4f} +/- {b4_pts[-1]['flow_sd']:.4f} g/s "
                  f"(n={len(fl)})")

    # ---- B5: fill drawdown at 55 deg (early vs late) -----------------
    print("\n== B5: fill drawdown (55 deg, 55 rpm continuous) ==")
    b5 = [r for r in rows if r["test"] == "B5" and r["m_settled2"] is not None
          and r["t_disp_s"]]
    b5_pts = []
    for r in sorted(b5, key=lambda x: x["trial"]):
        fl = r["m_settled2"] / r["t_disp_s"]
        b5_pts.append({"trial": r["trial"], "cum": r["cum"], "flow": fl})
        print(f"  trial {r['trial']:2d} (cum {r['cum']:5.2f} g dispensed): "
              f"flow {fl:.4f} g/s")

    # ---- CSVs --------------------------------------------------------
    with open(outdir / "afterflow_trials.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["powder_id", "trial", "test", "tilt", "rep", "rpm",
                    "halt_g", "mode", "m_trig", "t_disp_s", "m_settled2",
                    "flow_slope_g_per_s", "trig_over_mg", "afterflow_mg",
                    "tau_s", "taps", "verdict"])
        for r in rows:
            if r["mode"] not in ("rot", "auger"):
                continue
            w.writerow([powder, r["trial"], r["test"], r["tilt"], r["rep"],
                        f"{r['rpm']:.0f}", f"{r['halt_g']:.2f}", r["mode"],
                        "" if r["m_trig"] is None else f"{r['m_trig']:.4f}",
                        f"{r['t_disp_s']:.2f}",
                        "" if r["m_settled2"] is None else f"{r['m_settled2']:.4f}",
                        "" if r["flow_slope"] is None else f"{r['flow_slope']:.4f}",
                        "" if r["trig_over"] is None else f"{mg(r['trig_over']):.1f}",
                        "" if r["afterflow"] is None else f"{mg(r['afterflow']):.1f}",
                        "" if r["tau"] is None else f"{r['tau']:.3f}",
                        r["taps"], r["verdict"]])
    with open(outdir / "afterflow_flow.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["powder_id", "trial", "test", "tilt", "rpm",
                    "t_disp_s", "m_settled2", "flow_g_per_s", "cum_g"])
        for r in rows:
            if r["mode"] != "cont" or r["m_settled2"] is None:
                continue
            w.writerow([powder, r["trial"], r["test"], f"{r['tilt']:.0f}",
                        f"{r['rpm']:.0f}", f"{r['t_disp_s']:.2f}",
                        f"{r['m_settled2']:.4f}",
                        f"{r['m_settled2'] / r['t_disp_s']:.4f}", f"{r['cum']:.2f}"])

    _figures(outdir, powder, c6_cells, c7_pts, c8_summary, b4_pts, b5_pts,
             quiet_hf)
    print(f"\nwrote afterflow_trials.csv, afterflow_flow.csv + 2 figures "
          f"to {outdir}/")


def _style(ax):
    ax.set_facecolor(SURFACE)
    ax.grid(axis="y", color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.tick_params(colors=TEXT_2)


def _figures(outdir, powder, c6_cells, c7_pts, c8_summary, b4_pts, b5_pts, hf):
    # === figure 1: C6 (tilt x halt) afterflow + tau, and C7 linearity ==
    fig, (a1, a2, a3) = plt.subplots(1, 3, figsize=(15.5, 5.0))
    fig.patch.set_facecolor(SURFACE)
    tilts = sorted({t for t, _ in c6_cells})
    halts = sorted({h for _, h in c6_cells})
    color = {t: ANGLE_RAMP[i] for i, t in enumerate(tilts)}

    # a1: afterflow vs tilt, one line per halt mass
    for h in halts:
        xs = [t for t in tilts if (t, h) in c6_cells]
        ys = [c6_cells[(t, h)]["af_m"] for t in xs]
        es = [c6_cells[(t, h)]["af_sd"] for t in xs]
        a1.errorbar(xs, ys, yerr=es, marker="o", ms=8, lw=2, capsize=4,
                    color=ANGLE_RAMP[min(halts.index(h) + 1, 4)],
                    label=f"halt {h:.2f} g")
    a1.set_xlabel("plate tilt (deg)", color=TEXT_2)
    a1.set_ylabel("afterflow: settled − trigger (mg)", color=TEXT_2)
    a1.set_title("C6 · afterflow vs tilt & halt mass\n(55 rpm, tap-while-rotating)",
                 color=TEXT_1, loc="left", fontsize=11.5, fontweight="bold")
    a1.legend(frameon=False, fontsize=9)
    a1.set_ylim(bottom=0)

    # a2: tau vs tilt (should be ~flat if afterflow = flow*tau)
    for h in halts:
        xs = [t for t in tilts if (t, h) in c6_cells and c6_cells[(t, h)]["tau"]]
        ys = [c6_cells[(t, h)]["tau_m"] for t in xs]
        es = [c6_cells[(t, h)]["tau_sd"] for t in xs]
        a2.errorbar(xs, ys, yerr=es, marker="s", ms=8, lw=2, capsize=4,
                    color=ANGLE_RAMP[min(halts.index(h) + 1, 4)],
                    label=f"halt {h:.2f} g")
    all_tau = [t for c in c6_cells.values() for t in c["tau"]]
    if all_tau:
        mu = statistics.mean(all_tau)
        a2.axhline(mu, color=ACCENT, lw=1.4, ls=(0, (4, 3)))
        a2.annotate(f"pooled τ = {mu:.2f} s", (tilts[0], mu),
                    xytext=(2, 6), textcoords="offset points",
                    color=ACCENT, fontsize=10, fontweight="bold")
    a2.set_xlabel("plate tilt (deg)", color=TEXT_2)
    a2.set_ylabel("τ = afterflow / flow-at-halt (s)", color=TEXT_2)
    a2.set_title("C6 · in-flight time constant τ\n(flat ⇒ afterflow = flow × τ)",
                 color=TEXT_1, loc="left", fontsize=11.5, fontweight="bold")
    a2.set_ylim(bottom=0)

    # a3: C7 afterflow vs flow (linearity, intercept = lip dump)
    fx = [p["flow_m"] for p in c7_pts if p["flow_m"] == p["flow_m"]]
    fy = [p["af_m"] for p in c7_pts if p["flow_m"] == p["flow_m"]]
    es = [p["af_sd"] for p in c7_pts if p["flow_m"] == p["flow_m"]]
    a3.errorbar(fx, fy, yerr=es, fmt="o", ms=9, capsize=4, color="#2a78d6",
                markeredgecolor=SURFACE, markeredgewidth=1.5, zorder=3)
    for p in c7_pts:
        if p["flow_m"] == p["flow_m"]:
            a3.annotate(f"{p['rpm']:.0f} rpm", (p["flow_m"], p["af_m"]),
                        xytext=(6, -2), textcoords="offset points",
                        color=TEXT_2, fontsize=8.5)
    if len(fx) >= 2:
        b = slope(list(zip(fx, [y / 1000.0 for y in fy])))
        a = statistics.mean([y / 1000.0 for y in fy]) - b * statistics.mean(fx)
        xr = [0] + sorted(fx)
        a3.plot(xr, [mg(a + b * x) for x in xr], color=ACCENT, lw=2,
                ls=(0, (5, 3)), zorder=2,
                label=f"fit: {mg(a):+.0f} mg + {b:.2f}s·flow")
        a3.axhline(mg(a), color=TEXT_2, lw=0.9, ls=(0, (2, 3)))
        a3.legend(frameon=False, fontsize=9, loc="upper left")
    a3.set_xlabel("flow-at-halt (g/s, pre-halt slope)", color=TEXT_2)
    a3.set_ylabel("afterflow (mg)", color=TEXT_2)
    a3.set_title("C7 · afterflow vs speed (55°, auger-only)\n"
                 "intercept = speed-independent lip dump",
                 color=TEXT_1, loc="left", fontsize=11.5, fontweight="bold")
    a3.set_xlim(left=0)
    a3.set_ylim(bottom=0)
    for ax in (a1, a2, a3):
        _style(ax)
    fig.tight_layout()
    fig.savefig(outdir / "afterflow_decomposition.png", dpi=160)

    # === figure 2: C8 decomposition, B4 feed map, B5 drawdown =========
    fig2, (b1, b2, b3) = plt.subplots(1, 3, figsize=(15.5, 4.8))
    fig2.patch.set_facecolor(SURFACE)

    # b1: C8 actuator decomposition
    order = [m for m in ("auger", "rot", "taponly") if m in c8_summary]
    labels = {"auger": "auger-only\nafterflow", "rot": "tap-while-rot\nafterflow",
              "taponly": "tap-only\n15-tap total"}
    cols = {"auger": "#2a78d6", "rot": ACCENT, "taponly": ACCENT2}
    xs = range(len(order))
    ys = [c8_summary[m]["m"] for m in order]
    es = [c8_summary[m]["sd"] for m in order]
    bars = b1.bar(xs, ys, 0.6, yerr=es, capsize=5,
                  color=[cols[m] for m in order],
                  edgecolor=SURFACE, linewidth=2)
    for i, m in enumerate(order):
        b1.annotate(f"{ys[i]:.1f} mg\n(n={c8_summary[m]['n']})",
                    (i, ys[i] + es[i]), xytext=(0, 4),
                    textcoords="offset points", ha="center",
                    color=TEXT_1, fontsize=9)
    b1.set_xticks(list(xs))
    b1.set_xticklabels([labels[m] for m in order], fontsize=9, color=TEXT_2)
    b1.set_ylabel("mass (mg)", color=TEXT_2)
    b1.set_title("C8 · actuator decomposition (55°, 0.5 g)",
                 color=TEXT_1, loc="left", fontsize=11.5, fontweight="bold")
    b1.set_ylim(bottom=0)

    # b2: B4 max-rate feed map flow(tilt)
    xs = [p["tilt"] for p in b4_pts]
    ys = [p["flow_m"] for p in b4_pts]
    es = [p["flow_sd"] for p in b4_pts]
    b2.errorbar(xs, ys, yerr=es, marker="o", ms=9, lw=2, capsize=4,
                color="#1a4e90", markeredgecolor=SURFACE, markeredgewidth=1.5)
    for p in b4_pts:
        b2.annotate(f"{p['flow_m']:.3f}", (p["tilt"], p["flow_m"]),
                    xytext=(0, 8), textcoords="offset points", ha="center",
                    color=TEXT_2, fontsize=8.5)
    b2.set_xlabel("plate tilt (deg)", color=TEXT_2)
    b2.set_ylabel("max-rate flow (g/s)", color=TEXT_2)
    b2.set_title("B4 · max-rate feed map (55 rpm, 6 s)",
                 color=TEXT_1, loc="left", fontsize=11.5, fontweight="bold")
    b2.set_ylim(bottom=0)

    # b3: B5 fill drawdown, flow vs cumulative dispensed
    xs = [p["cum"] for p in b5_pts]
    ys = [p["flow"] for p in b5_pts]
    b3.plot(xs, ys, "-o", ms=10, lw=2, color=ACCENT2,
            markeredgecolor=SURFACE, markeredgewidth=1.5)
    for p in b5_pts:
        tag = "early" if p["trial"] < 5 else "late"
        b3.annotate(f"{tag}\ntrial {p['trial']}", (p["cum"], p["flow"]),
                    xytext=(0, -22 if tag == "early" else 8),
                    textcoords="offset points", ha="center",
                    color=TEXT_2, fontsize=8.5)
    b3.set_xlabel("cumulative dispensed (g) — fill drawdown surrogate",
                  color=TEXT_2)
    b3.set_ylabel("flow at 55° (g/s)", color=TEXT_2)
    b3.set_title("B5 · fill drawdown (55°, 55 rpm)",
                 color=TEXT_1, loc="left", fontsize=11.5, fontweight="bold")
    b3.set_ylim(bottom=0)
    for ax in (b1, b2, b3):
        _style(ax)
    fig2.tight_layout()
    fig2.savefig(outdir / "afterflow_models.png", dpi=160)


if __name__ == "__main__":
    main(sys.argv[1])
