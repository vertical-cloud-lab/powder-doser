#!/usr/bin/env python3
"""Analyze balance step-response captures (known-mass drop tests, 2026-08-14).

Input: balance_capture_*.csv streams captured on the bench (rows:
M,<key>,<val> / P,<t_ms>,<label>,<mass> / E,<t_ms>,<msg> /
D,<t_ms>,<mass_g>,<S|U>). Each capture holds ~10 drop / removal cycles of one
known mass (naming: <mass>g_<n><method>, d=drop 5-10 mm, ad=alternating
5-10/20 mm drops, l=slow lay-down).

Per up-step this fits m(t) = m0 + A*(1 - exp(-(t - t0)/tau)) with t0, tau, A
free (m0 fixed to the pre-step baseline) and extracts tau, 10-90 rise,
time to settle within +/-2 mg, stable-flag latency, overshoot, and the
plateau delta (catches bounced drops).

Caveats baked into the method:
 - Dead time is NOT separable: there is no independent marker of the physical
   drop moment (hand drops, no keypress events), so t0 absorbs it.
 - Removals (negative steps) are skipped: grabbing the weight presses the pan
   (spikes to ~2x the load), so they are not clean steps.
 - Lay-down events measure operator hand speed convolved with the balance,
   so their tau is an upper bound / consistency check only.

Usage: python3 scripts/analyze_balance_step.py <data_dir>
Writes events.csv, summary.csv and two PNGs into <data_dir>.
"""

import csv
import math
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import curve_fit
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

# dataviz reference palette (light mode), fixed slot order
C = {
    "blue": "#2a78d6",
    "orange": "#eb6834",
    "aqua": "#1baf7a",
    "yellow": "#eda100",
    "magenta": "#e87ba4",
    "text": "#0b0b0b",
    "text2": "#52514e",
    "surface": "#fcfcfb",
    "grid": "#e4e3df",
}

CONDITIONS = {
    "balance_capture_2g_10d.csv": ("2 g drop", 2.0, C["blue"]),
    "balance_capture_5g_10d.csv": ("5 g drop", 5.0, C["orange"]),
    "balance_capture_10g_10d.csv": ("10 g drop", 10.0, C["aqua"]),
    "balance_capture_5g_10ad.csv": ("5 g alt drop (5-20 mm)", 5.0, C["yellow"]),
    "balance_capture_10g_10l.csv": ("10 g lay-down", 10.0, C["magenta"]),
}

SETTLE_TOL_G = 0.002  # +/-2 mg settling band


def parse(path):
    t, m, flag = [], [], []
    for row in csv.reader(open(path)):
        if row and row[0] == "D":
            t.append(float(row[1]) / 1000.0)
            m.append(float(row[2]))
            flag.append(row[3].strip())
    t = np.array(t)
    return t - t[0], np.array(m), np.array(flag)


def model(t, t0, tau, A, m0):
    out = np.full_like(t, m0)
    rise = t >= t0
    out[rise] = m0 + A * (1.0 - np.exp(-(t[rise] - t0) / tau))
    return out


def analyze_file(path, exp_mass):
    t, m, flag = parse(path)
    half = exp_mass / 2.0
    above = m > half
    ups = [i for i in range(1, len(m)) if above[i] and not above[i - 1]]
    downs = [i for i in range(1, len(m)) if not above[i] and above[i - 1]]

    events = []
    for n, i_up in enumerate(ups, 1):
        i_dn = next((d for d in downs if d > i_up), len(m))
        # baseline before the rise
        pre_sel = (t < t[i_up] - 0.5) & (t > t[i_up] - 3.0)
        pre_sel &= m < half
        m0 = float(np.median(m[pre_sel])) if pre_sel.sum() >= 2 else 0.0
        # top plateau, robust to the hand-press spike at removal
        top = m[i_up:i_dn]
        post = float(np.median(top)) if len(top) else float("nan")
        # fit window ends at the first hand-press frame (m >> plateau) or removal
        end = i_dn
        for j in range(i_up, i_dn):
            if m[j] > post + 0.3:
                # allow the impact-overshoot frame right at the rise
                if t[j] - t[i_up] > 0.8:
                    end = j
                    break
        a = np.searchsorted(t, t[i_up] - 1.2)
        tw, mw = t[a:end], m[a:end]
        top_dur = t[end - 1] - t[i_up] if end - 1 > i_up else 0.0
        delta = post - m0
        partial = abs(delta - exp_mass) > 0.10 * exp_mass or top_dur < 1.2

        t0 = tau = r2 = float("nan")
        if len(tw) >= 5 and not partial:
            try:
                popt, _ = curve_fit(
                    lambda tt, t0, tau, A: model(tt, t0, tau, A, m0),
                    tw, mw, p0=[t[i_up] - 0.2, 0.3, delta],
                    bounds=([t[i_up] - 1.0, 0.02, 0.5 * delta],
                            [t[i_up] + 0.2, 5.0, 1.5 * delta]),
                    maxfev=20000,
                )
                t0, tau, A = popt
                resid = mw - model(tw, t0, tau, A, m0)
                ss_tot = float(np.sum((mw - mw.mean()) ** 2))
                r2 = 1.0 - float(np.sum(resid**2)) / ss_tot if ss_tot > 0 else float("nan")
            except Exception:
                pass

        settle = stable_lat = overshoot = float("nan")
        if not math.isnan(t0):
            idx = [i for i in range(i_up, end) if t[i] >= t0]
            if idx:
                overshoot = float(np.max(m[idx])) - post
            for i in idx:
                # persistently inside the band for ~4 frames (hand-press frames
                # right before removal must not veto an earlier true settle)
                tail = m[i : min(i + 4, end)]
                if len(tail) >= 2 and np.all(np.abs(tail - post) < SETTLE_TOL_G):
                    settle = t[i] - t0
                    break
            for i in idx:
                if flag[i] == "S" and abs(m[i] - post) < 0.01:
                    stable_lat = t[i] - t0
                    break

        events.append(dict(
            event=n, t_up=round(t[i_up], 2), t0=t0, tau=tau, r2=r2,
            delta_g=round(delta, 4), top_dur_s=round(top_dur, 2),
            partial=partial, overshoot_mg=None if math.isnan(overshoot) else round(overshoot * 1000, 1),
            settle_2mg_s=settle, stable_latency_s=stable_lat,
        ))

    # baseline noise: per-frame residuals in quiet low segments
    resid = []
    lo = m < 0.01
    segs, start = [], None
    for i, v in enumerate(lo):
        if v and start is None:
            start = i
        elif not v and start is not None:
            segs.append((start, i)); start = None
    if start is not None:
        segs.append((start, len(m)))
    for s0, s1 in segs:
        if s1 - s0 >= 6:
            seg = m[s0 + 2 : s1 - 2]
            # only truly quiet segments (bounce debris / motion excluded)
            if len(seg) and seg.max() - seg.min() < 0.005:
                resid.extend((seg - np.median(seg)).tolist())
    sigma = float(np.std(resid)) if resid else float("nan")
    return t, m, flag, events, sigma


def main():
    ddir = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    all_events, traces, sigmas = [], {}, {}
    for fname, (label, exp_mass, color) in CONDITIONS.items():
        path = ddir / fname
        if not path.exists():
            print(f"skip {fname} (missing)")
            continue
        t, m, flag, events, sigma = analyze_file(path, exp_mass)
        traces[fname] = (t, m, flag, label, color)
        sigmas[fname] = sigma
        for e in events:
            e.update(file=fname, condition=label)
            all_events.append(e)
        good = [e for e in events if not e["partial"] and not math.isnan(e["tau"]) and e["r2"] > 0.995]
        print(f"{fname}: {len(events)} up-steps ({len(good)} clean), "
              f"baseline sigma {sigma*1000:.2f} mg")

    cols = ["file", "condition", "event", "t_up", "t0", "tau", "r2", "delta_g",
            "top_dur_s", "partial", "overshoot_mg", "settle_2mg_s", "stable_latency_s"]
    with open(ddir / "events.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(all_events)

    def clean(e):
        # lay-downs are operator-limited, never cleanly exponential: relax R2
        r2_min = 0.90 if e["file"].endswith("10l.csv") else 0.995
        return not e["partial"] and not math.isnan(e["tau"]) and e["r2"] > r2_min

    rows = []
    for fname, (label, exp_mass, _) in CONDITIONS.items():
        evs = [e for e in all_events if e["file"] == fname]
        good = [e for e in evs if clean(e)]
        def stats(key):
            vals = [e[key] for e in good if e[key] is not None and not math.isnan(e[key])]
            if not vals:
                return float("nan"), float("nan")
            return float(np.median(vals)), float(np.std(vals))
        tau_med, tau_sd = stats("tau")
        st_med, st_sd = stats("settle_2mg_s")
        sl_med, sl_sd = stats("stable_latency_s")
        ov = [e["overshoot_mg"] for e in good if e["overshoot_mg"] is not None]
        rows.append(dict(
            condition=label, n_events=len(evs), n_clean=len(good),
            n_partial=sum(e["partial"] for e in evs),
            tau_median_s=round(tau_med, 3), tau_sd_s=round(tau_sd, 3),
            rise_10_90_s=round(tau_med * 2.197, 3) if not math.isnan(tau_med) else "",
            settle_2mg_median_s=round(st_med, 2), settle_2mg_sd_s=round(st_sd, 2),
            stable_latency_median_s=round(sl_med, 2), stable_latency_sd_s=round(sl_sd, 2),
            overshoot_median_mg=round(float(np.median(ov)), 1) if ov else "",
            baseline_sigma_mg=round(sigmas[fname] * 1000, 2),
        ))
        print(rows[-1])
    with open(ddir / "summary.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    # pooled tau across true drops only (not lay-downs)
    drop_files = [f for f in CONDITIONS if not f.endswith("10l.csv")]
    pooled = [e["tau"] for e in all_events if e["file"] in drop_files and clean(e)]
    print(f"pooled drop tau: median {np.median(pooled):.3f} s, "
          f"mean {np.mean(pooled):.3f} s, sd {np.std(pooled):.3f} s, n={len(pooled)}")

    plot_overlay(ddir, traces, all_events, clean, float(np.median(pooled)))
    plot_params(ddir, all_events, clean)


def plot_overlay(ddir, traces, all_events, clean, tau_p):
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6), facecolor=C["surface"])
    for ax in axes:
        ax.set_facecolor(C["surface"])
        for s in ax.spines.values():
            s.set_color(C["grid"])
        ax.grid(True, color=C["grid"], lw=0.6, alpha=0.7)
        ax.tick_params(colors=C["text2"], labelsize=9)

    for fname, (t, m, flag, label, color) in traces.items():
        first = True
        for e in [e for e in all_events if e["file"] == fname and clean(e)]:
            t0, A = e["t0"], e["delta_g"]
            sel = (t >= t0 - 0.6) & (t <= t0 + min(2.5, e["top_dur_s"]))
            axes[0].plot(t[sel] - t0, m[sel] / A, "-o", lw=1.0, ms=2.5,
                         color=color, alpha=0.45, label=label if first else None)
            first = False
    tt = np.linspace(-0.6, 2.5, 400)
    yy = np.where(tt >= 0, 1 - np.exp(-tt / tau_p), 0)
    axes[0].plot(tt, yy, "--", lw=2, color=C["text"],
                 label=f"1st-order, tau = {tau_p:.2f} s (pooled drops)")
    axes[0].set_xlabel("time from fitted step start t0 (s)", color=C["text2"])
    axes[0].set_ylabel("normalized response", color=C["text2"])
    axes[0].set_title("Clean up-steps aligned at fitted t0", color=C["text"], fontsize=11)
    axes[0].legend(fontsize=8, framealpha=0.9, loc="lower right")
    axes[0].set_ylim(-0.08, 1.18)

    fname = "balance_capture_5g_10d.csv"
    t, m, flag, label, color = traces[fname]
    axes[1].plot(t, m, "-", lw=1.2, color=color)
    un = flag == "U"
    axes[1].plot(t[un], m[un], ".", ms=3, color=C["text2"], alpha=0.6)
    axes[1].set_xlabel("time (s)", color=C["text2"])
    axes[1].set_ylabel("mass (g)", color=C["text2"])
    axes[1].set_title(f"Raw stream: {label} cycles -- spikes above 5 g are the hand\n"
                      "pressing the pan during removal (gray dots = unstable frames)",
                      color=C["text"], fontsize=10)
    fig.suptitle("HR-100A balance step response -- known-mass drop tests (2026-08-14)",
                 color=C["text"], fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    fig.savefig(ddir / "balance_step_overlay.png", dpi=150)
    plt.close(fig)


def plot_params(ddir, all_events, clean):
    conds = list(CONDITIONS.items())
    fig, axes = plt.subplots(1, 3, figsize=(12.5, 4.4), facecolor=C["surface"])
    metrics = [("tau", "tau (s)", "Fitted lag constant tau"),
               ("settle_2mg_s", "time (s)", "Settle to +/-2 mg (from t0)"),
               ("stable_latency_s", "time (s)", "First stable-flagged frame (from t0)")]
    rng = np.random.RandomState(1)
    for ax, (key, ylab, title) in zip(axes, metrics):
        ax.set_facecolor(C["surface"])
        for s in ax.spines.values():
            s.set_color(C["grid"])
        ax.grid(True, axis="y", color=C["grid"], lw=0.6, alpha=0.7)
        ax.tick_params(colors=C["text2"], labelsize=8)
        for x, (fname, (label, _, color)) in enumerate(conds):
            vals = [e[key] for e in all_events
                    if e["file"] == fname and clean(e)
                    and e[key] is not None and not math.isnan(e[key])]
            if not vals:
                continue
            jitter = (rng.rand(len(vals)) - 0.5) * 0.25
            ax.plot(x + jitter, vals, "o", ms=5, color=color, alpha=0.75)
            med = float(np.median(vals))
            ax.plot([x - 0.22, x + 0.22], [med, med], "-", lw=2, color=C["text"])
            ax.annotate(f"{med:.2f}", (x + 0.27, med), fontsize=8, color=C["text"], va="center")
        ax.set_xticks(range(len(conds)))
        ax.set_xticklabels([lab.replace(" (5-20 mm)", "\n(5-20 mm)").replace(" lay-down", "\nlay-down")
                            for _, (lab, _, _) in conds], fontsize=7.5)
        ax.set_ylabel(ylab, color=C["text2"], fontsize=9)
        ax.set_title(title, color=C["text"], fontsize=10)
        ax.set_ylim(bottom=0)
    fig.suptitle("Per-trial step-response metrics (dots = trials, bar = median; lay-down tau is operator-limited)",
                 color=C["text"], fontsize=11)
    fig.tight_layout(rect=[0, 0, 1, 0.92])
    fig.savefig(ddir / "balance_step_params.png", dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    main()
