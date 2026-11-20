#!/usr/bin/env python3
"""Analyze a rapid-dispense stop-response log (PR #131).

Parses the CSV telemetry emitted by
``hardware/test-module/firmware/stop_response.py`` and produces:

  * a text report (static noise floor, in-dispense noise, per-trial
    trigger/settled masses, afterflow overshoot, settle times),
  * ``trials_summary.csv`` (one row per trial),
  * two figures: the settling traces aligned at the halt trigger, and a
    per-angle summary of overshoot components / dispense time / noise.

Usage:
    python scripts/analyze_stop_response.py \
        data/stop-response/2026-08-07_salt/stop_response_salt.log
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
# Sequential single-hue ramp (light->dark) for tilt angle = a magnitude.
ANGLE_RAMP = ["#b3cdf0", "#7fabe4", "#5492dc", "#2a78d6", "#1a4e90"]
ACCENT = "#eb6834"  # orange: the afterflow component
SETTLE_TOL_G = 0.002


def parse(path):
    meta, events, samples, points, trials = {}, [], [], [], []
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
        elif f[0] == "P" and len(f) >= 7:
            points.append({
                "t": int(f[1]) / 1000.0, "trial": int(f[2]),
                "angle": float(f[3]), "rep": int(f[4]), "kind": f[5],
                "mass": None if f[6] == "nan" else float(f[6])})
        elif f[0] == "R" and len(f) >= 10:
            trials.append({
                "trial": int(f[1]), "angle": float(f[2]),
                "rep": int(f[3]), "m_trig": float(f[4]),
                "t_disp_s": float(f[5]), "m_settled": float(f[6]),
                "m_settled2": float(f[7]), "taps": int(f[8]),
                "verdict": f[9]})
    return meta, events, samples, points, trials


def second_diff_sigma(masses):
    """High-frequency noise via second differences.

    sd(m[i+1] - 2 m[i] + m[i-1]) / sqrt(6) estimates per-sample sigma
    while cancelling any locally-linear trend -- unlike a rolling-median
    residual, which is identically ~0 on a monotone-rising dose trace.
    During dispensing this still includes real slug arrivals; that is
    unavoidable and stated where reported.
    """
    if len(masses) < 3:
        return 0.0
    d2 = [masses[i + 1] - 2 * masses[i] + masses[i - 1]
          for i in range(1, len(masses) - 1)]
    return statistics.pstdev(d2) / 6 ** 0.5


def mg(x):
    return x * 1000.0


def main(path):
    meta, events, samples, points, trials = parse(path)
    outdir = Path(path).parent
    trig_g = float(meta.get("trigger_g", 0.5))

    # ---- static noise baseline (trial 0, phase "noise") --------------
    noise = [s for s in samples
             if s["trial"] == 0 and s["phase"] == "noise"
             and s["mass"] is not None]
    nm = [s["mass"] for s in noise]
    n_dur = noise[-1]["t"] - noise[0]["t"]
    rate = (len(noise) - 1) / n_dur
    stable_frac = sum(1 for s in noise if s["flag"] == "S") / len(noise)
    # the first ~14 s after tare carry a mechanical/tare transient --
    # report the full stream AND the quiet region separately
    t_quiet = noise[0]["t"] + 15.0
    quiet = [s["mass"] for s in noise if s["t"] > t_quiet]
    quiet_sd = statistics.pstdev(quiet)
    quiet_hf = second_diff_sigma(quiet)
    drift = (statistics.mean(quiet[-len(quiet) // 4:])
             - statistics.mean(quiet[:len(quiet) // 4]))
    print("== static noise baseline (one-time, 0 deg, nothing moving) ==")
    print(f"  samples: {len(noise)} over {n_dur:.1f} s "
          f"({rate:.1f} Hz raw poll); stable fraction {stable_frac:.2f}")
    print(f"  full stream: sd {mg(statistics.pstdev(nm)):.2f} mg, "
          f"p2p {mg(max(nm) - min(nm)):.1f} mg "
          f"(dominated by a post-tare transient dying by ~14 s)")
    print(f"  quiet region (t>15 s): sd {mg(quiet_sd):.3f} mg, "
          f"p2p {mg(max(quiet) - min(quiet)):.2f} mg, "
          f"drift {mg(drift):+.2f} mg across the window")
    print(f"  sample-to-sample (2nd-diff) sigma: {mg(quiet_hf):.3f} mg "
          f"(display quantum 0.1 mg)")

    # ---- per-trial ---------------------------------------------------
    # trigger event times (absolute, per trial)
    trig_t = {}
    for t, txt in events:
        if txt.startswith("TRIGGER"):
            # attribute to the trial whose dispense contains this time
            for s in samples:
                if s["phase"] == "dispense" and abs(s["t"] - t / 1000.0) < 5:
                    trig_t[s["trial"]] = t / 1000.0
                    break
    disp_d2, disp_rates = [], []
    rows = []
    print("\n== trials ==")
    print("angle rep  m_trig  t_disp  flow(g/s)  m_settled  afterflow  "
          "total_over  tau_s  settle_t  taps")
    for tr in trials:
        n = tr["trial"]
        disp = [s for s in samples
                if s["trial"] == n and s["phase"] == "dispense"
                and s["mass"] is not None]
        sett = [s for s in samples
                if s["trial"] == n and s["phase"] == "settle"
                and s["mass"] is not None]
        t0 = trig_t.get(n, disp[-1]["t"] if disp else None)
        dm = [s["mass"] for s in disp]
        disp_d2 += [dm[i + 1] - 2 * dm[i] + dm[i - 1]
                    for i in range(1, len(dm) - 1)]
        flow = tr["m_trig"] / tr["t_disp_s"]
        disp_rates.append((len(disp) - 1) / (disp[-1]["t"] - disp[0]["t"]))
        after = tr["m_settled2"] - tr["m_trig"]
        total = tr["m_settled2"] - trig_g
        tau = after / flow if flow > 0 else float("nan")
        # settle time: last settle-phase sample > tol from final
        settle_t = 0.0
        for s in sett:
            if abs(s["mass"] - tr["m_settled2"]) > SETTLE_TOL_G:
                settle_t = s["t"] - t0
        rows.append({**tr, "afterflow_mg": mg(after),
                     "total_overshoot_mg": mg(total),
                     "trig_overshoot_mg": mg(tr["m_trig"] - trig_g),
                     "flow_g_per_s": flow, "tau_inflight_s": tau,
                     "settle_time_s": settle_t, "t_trig_abs_s": t0})
        print(f"{tr['angle']:5.0f} {tr['rep']:3d}  {tr['m_trig']:.4f}  "
              f"{tr['t_disp_s']:5.2f}  {flow:8.3f}  "
              f"{tr['m_settled2']:.4f}   {mg(after):+7.1f}    "
              f"{mg(total):+7.1f}  {tau:5.2f}  {settle_t:6.2f}  "
              f"{tr['taps']:4d}")

    disp_hf = statistics.pstdev(disp_d2) / 6 ** 0.5
    taus = [r["tau_inflight_s"] for r in rows]
    print(f"\n  in-dispense high-frequency (2nd-diff) sigma: "
          f"{mg(disp_hf):.2f} mg/sample -- includes real slug arrivals; "
          f"vs {mg(quiet_hf):.3f} mg static")
    print(f"  in-flight time constant tau = afterflow/flow: "
          f"{statistics.mean(taus):.2f} +/- {statistics.pstdev(taus):.2f} s "
          f"(cf. PID T_ANT_S = 1.1 s)")
    print(f"  mean raw poll rate during dispense: "
          f"{statistics.mean(disp_rates):.1f} Hz")

    # inter-trial mass released by the tilt move (pretare_n - settled2_{n-1})
    pre = {p["trial"]: p["mass"] for p in points if p["kind"] == "pretare"}
    print("\n== mass released by moving the tilt between trials ==")
    for tr in trials[1:]:
        prev = next(x for x in trials if x["trial"] == tr["trial"] - 1)
        # both are absolute-cup values only within the same tare; pretare
        # is pre-tare absolute, settled2 is post-tare of the previous
        # trial -- comparable because tare persists between trials.
        d = pre[tr["trial"]] - prev["m_settled2"]
        print(f"  trial {prev['trial']}->{tr['trial']} "
              f"(tilt {prev['angle']:.0f}->{tr['angle']:.0f} deg): "
              f"{mg(d):+6.1f} mg")

    # ---- CSV ---------------------------------------------------------
    with open(outdir / "trials_summary.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=[
            "powder_id", "trial", "angle", "rep", "m_trig", "t_disp_s",
            "flow_g_per_s", "m_settled", "m_settled2", "trig_overshoot_mg",
            "afterflow_mg", "total_overshoot_mg", "tau_inflight_s",
            "settle_time_s", "taps", "verdict"])
        w.writeheader()
        for r in rows:
            w.writerow({k: (f"{v:.4f}" if isinstance(v, float) else v)
                        for k, v in r.items()
                        if k in w.fieldnames} | {"powder_id": "salt"})

    # ---- figure 1: settling traces aligned at the trigger ------------
    fig, (ax, axb) = plt.subplots(
        1, 2, figsize=(12.5, 5.2), width_ratios=[1.55, 1])
    fig.patch.set_facecolor(SURFACE)
    angles = sorted({tr["angle"] for tr in trials})
    color = {a: ANGLE_RAMP[i] for i, a in enumerate(angles)}
    for r in rows:
        n, t0 = r["trial"], r["t_trig_abs_s"]
        pts = [(s["t"] - t0, s["mass"]) for s in samples
               if s["trial"] == n and s["phase"] in ("dispense", "settle")
               and s["mass"] is not None and -3 <= s["t"] - t0 <= 15]
        xs, ys = zip(*pts)
        ax.plot(xs, [mg(y) for y in ys], lw=2, color=color[r["angle"]],
                solid_capstyle="round",
                alpha=0.95 if r["rep"] == 1 else 0.65)
    # direct labels at rep-1 line ends, dodged apart vertically
    lab = sorted(((mg(r["m_settled2"]), r["angle"]) for r in rows
                  if r["rep"] == 1))
    ys_lab = [y for y, _ in lab]
    for i in range(1, len(ys_lab)):
        if ys_lab[i] - ys_lab[i - 1] < 16:
            ys_lab[i] = ys_lab[i - 1] + 16
    for (y0, a), y in zip(lab, ys_lab):
        ax.annotate(f"{a:.0f}°", (15.0, y), xytext=(6, 0),
                    textcoords="offset points", va="center",
                    color=color[a], fontsize=10, fontweight="bold")
    ax.axhline(mg(trig_g), color=TEXT_2, lw=1, ls=(0, (4, 3)))
    ax.annotate("0.5 g halt threshold", (-2.9, mg(trig_g)),
                xytext=(0, 5), textcoords="offset points",
                color=TEXT_2, fontsize=9)
    ax.axvline(0, color=TEXT_2, lw=1, ls=(0, (2, 3)))
    ax.annotate("ALL STOP", (0, 60), xytext=(4, 0),
                textcoords="offset points", color=TEXT_2, fontsize=9)
    ax.set_xlim(-3, 16.8)
    ax.set_xlabel("time from halt trigger (s)", color=TEXT_2)
    ax.set_ylabel("cup mass (mg, per-trial tare)", color=TEXT_2)
    ax.set_title("Rapid dispense, halt at first ≥0.5 g reading — "
                 "what lands after the stop", color=TEXT_1, loc="left",
                 fontsize=12, fontweight="bold")

    # panel b: overshoot components per trial, stacked
    xs = range(len(rows))
    trig_part = [r["trig_overshoot_mg"] for r in rows]
    after_part = [r["afterflow_mg"] for r in rows]
    axb.bar(xs, trig_part, 0.72, color=[color[r["angle"]] for r in rows],
            edgecolor=SURFACE, linewidth=2, label="trigger reading − 0.5 g")
    axb.bar(xs, after_part, 0.72, bottom=trig_part, color=ACCENT,
            edgecolor=SURFACE, linewidth=2, label="afterflow (settled − trigger)")
    for i, r in enumerate(rows):
        axb.annotate(f"{r['total_overshoot_mg']:+.0f}",
                     (i, trig_part[i] + after_part[i]), xytext=(0, 3),
                     textcoords="offset points", ha="center",
                     color=TEXT_1, fontsize=8.5)
    axb.set_xticks(list(xs))
    axb.set_xticklabels(
        [f"{r['angle']:.0f}°\nr{r['rep']}" for r in rows],
        fontsize=8.5, color=TEXT_2)
    axb.set_ylabel("overshoot past 0.5 g (mg)", color=TEXT_2)
    axb.set_title("Overshoot = late trigger + afterflow", color=TEXT_1,
                  loc="left", fontsize=12, fontweight="bold")
    axb.legend(frameon=False, fontsize=9, loc="upper right")
    for a in (ax, axb):
        a.set_facecolor(SURFACE)
        a.grid(axis="y", color=GRID, lw=0.8)
        a.set_axisbelow(True)
        for sp in a.spines.values():
            sp.set_visible(False)
        a.tick_params(colors=TEXT_2)
    fig.tight_layout()
    fig.savefig(outdir / "stop_response_traces.png", dpi=160)

    # ---- figure 2: dispense speed + noise ----------------------------
    fig2, (c, d) = plt.subplots(1, 2, figsize=(11, 4.6))
    fig2.patch.set_facecolor(SURFACE)
    for r in rows:
        c.plot(r["angle"], r["flow_g_per_s"], "o", ms=9,
               color=color[r["angle"]],
               markeredgecolor=SURFACE, markeredgewidth=1.5)
    for a in angles:
        vals = [r["flow_g_per_s"] for r in rows if r["angle"] == a]
        c.annotate(f"{statistics.mean(vals):.3f}",
                   (a, max(vals)), xytext=(0, 8),
                   textcoords="offset points", ha="center",
                   color=TEXT_2, fontsize=9)
    c.set_xlabel("plate tilt (deg)", color=TEXT_2)
    c.set_ylabel("mean dispense rate (g/s)", color=TEXT_2)
    c.set_title("Dispense rate to 0.5 g (55 rpm + taps)",
                color=TEXT_1, loc="left", fontsize=12, fontweight="bold")
    c.set_ylim(bottom=0)

    labels = ["static\nsample-to-sample", "static\n60 s window",
              "during\ndispense"]
    vals = [mg(quiet_hf), mg(quiet_sd), mg(disp_hf)]
    bars = d.bar(labels, vals, 0.55,
                 color=["#2a78d6", "#7fabe4", ACCENT],
                 edgecolor=SURFACE, linewidth=2)
    for b, v in zip(bars, vals):
        d.annotate(f"{v:.2f} mg", (b.get_x() + b.get_width() / 2, v),
                   xytext=(0, 4), textcoords="offset points",
                   ha="center", color=TEXT_1, fontsize=10,
                   fontweight="bold")
    d.set_ylabel("sigma (mg)", color=TEXT_2)
    d.set_title("Scale noise: static vs dispensing\n"
                "(dispense value includes real slug arrivals)",
                color=TEXT_1, loc="left", fontsize=11,
                fontweight="bold")
    for a in (c, d):
        a.set_facecolor(SURFACE)
        a.grid(axis="y", color=GRID, lw=0.8)
        a.set_axisbelow(True)
        for sp in a.spines.values():
            sp.set_visible(False)
        a.tick_params(colors=TEXT_2)
    fig2.tight_layout()
    fig2.savefig(outdir / "stop_response_summary.png", dpi=160)
    print(f"\nwrote trials_summary.csv + 2 figures to {outdir}/")


if __name__ == "__main__":
    main(sys.argv[1])
