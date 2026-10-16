#!/usr/bin/env python3
"""Afterflow extraction + per-powder dosing signatures from the #116 battery.

The uniform powder battery (data/battery/, issue #116) never ran a dedicated
stop-response protocol, but it recorded two things that let afterflow -- mass
that keeps landing after all actuation stops -- be recovered per powder:

  1. Block G dose bulk halts. The frozen three-phase controller polls the
     scale at ~250 ms while the auger runs continuously (55 rpm, tube
     vertical), halts at the anticipation threshold, settles 800 ms and takes
     a stable weigh, logging "+X g while settling". That delta IS afterflow,
     with the at-halt mass taken on the halt-decision poll. 3 doses/powder.
  2. Block D speed trials. 3-rev continuous rotations at 15/45/90 rpm (tube
     tilt 45 deg) with a ~290 ms POLL stream (real t_ms) that ends at
     rotation end, then a settled weigh ~2 s later. afterflow = settled -
     last poll mass (contains up to ~0.3 s of residual rotation delivery --
     flagged in the output). 3 trials/powder.

Flow-at-stop conventions (both are emitted; see columns):
  * flow_mean_g_per_s -- dispensed mass / active dispense time. Matches the
    definition behind the salt tau ~= 1.07 s from the 2026-08-07
    stop-response session, so cross-powder taus are comparable to it.
  * flow_slope_g_per_s -- least-squares slope over the last ~2 s of polls
    before the stop. For slug-mode powders this is trough/crest lottery.

Outputs (data/battery/afterflow-analysis/):
  afterflow_from_battery.csv   tidy per-stop extraction, all powders
  battery_afterflow_correlation.png
  battery_dose_signatures.png
  signature_stats.csv          per-powder dosing-signature metrics
Console: markdown-ready summary tables.

Balance context: the 2026-08-14 known-mass drop tests put the balance filter
at tau_bal ~= 0.16 s, settle-to-2 mg <= 0.9 s -- both settle windows here
(0.8 s + stable wait, ~2 s) capture essentially all afterflow.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
BATTERY = ROOT / "data" / "battery"
OUT = BATTERY / "afterflow-analysis"
OUT.mkdir(exist_ok=True)

DOSE_TARGET = 1.0

# Canonical battery runs (latest per powder; BRF -> the auger-2 rerun).
RUNS = {
    "brown-rice-flour": "20260805T185305Z_brown-rice-flour",
    "white-rice-flour": "20260804T211422Z_white-rice-flour",
    "sodium-alginate": "20260805T145725Z_sodium-alginate",
    "calcium-lactate": "20260805T200002Z_calcium-lactate",
    "carboxymethyl-cellulose": "20260805T215252Z_carboxymethyl-cellulose",
    "xanthan-gum": "20260806T140254Z_xanthan-gum",
    "salt": "20260806T145120Z_salt",
}
# Raw serial logs are missing from the two BRF reruns; the 08-04 first run has
# one (all three BRF runs stalled identically, so it stands in for block G).
RAW_FALLBACK = {"brown-rice-flour": "20260804T204316Z_brown-rice-flour"}

SHORT = {
    "brown-rice-flour": "brown rice flour",
    "white-rice-flour": "white rice flour",
    "sodium-alginate": "sodium alginate",
    "calcium-lactate": "calcium lactate",
    "carboxymethyl-cellulose": "CMC",
    "xanthan-gum": "xanthan gum",
    "salt": "salt",
}

RE_POLL = re.compile(
    r"\[phase 1 bulk\] poll (\d+)( \(unstable\))?: mass (-?[\d.]+) / [\d.]+ g "
    r"\((-?[\d.]+) g to go, \+?(-?[\d.]+) g this poll\), elapsed ([\d.]+) s")
RE_HALT = re.compile(r"\[phase 1 bulk\] auger halted at (-?[\d.]+) g to go")
RE_SETTLED = re.compile(
    r"\[phase 1 bulk\] settled: mass (-?[\d.]+) / [\d.]+ g \((-?[\d.]+) g to go, "
    r"\+?(-?[\d.]+) g while settling\), elapsed ([\d.]+) s")
RE_DOSE_START = re.compile(r"\[dose\] three-phase dose to ([\d.]+) g")
RE_CYCLE = re.compile(
    r"\[phase (\d) (?:fine|tap)\] cycle (\d+): mass (-?[\d.]+) / [\d.]+ g "
    r"\((-?[\d.]+) g to go, \+?(-?[\d.]+) g this cycle\), elapsed ([\d.]+) s")


def parse_bulk_doses(log_path: Path):
    """Per dose: bulk polls, halt mass, settled mass, afterflow, cycle yields."""
    doses, cur = [], None
    for line in log_path.read_text(errors="replace").splitlines():
        if RE_DOSE_START.search(line):
            cur = {"polls": [], "halt_mass": None, "settled": None,
                   "afterflow_g": None, "fine_cycles": [], "tap_cycles": []}
            doses.append(cur)
            continue
        if cur is None:
            continue
        m = RE_POLL.search(line)
        if m:
            cur["polls"].append((int(m.group(1)), float(m.group(3)),
                                 float(m.group(6))))
            continue
        m = RE_HALT.search(line)
        if m:
            cur["halt_mass"] = DOSE_TARGET - float(m.group(1))
            continue
        m = RE_SETTLED.search(line)
        if m:
            cur["settled"] = float(m.group(1))
            cur["afterflow_g"] = float(m.group(3))
            continue
        m = RE_CYCLE.search(line)
        if m:
            key = "fine_cycles" if m.group(1) == "2" else "tap_cycles"
            cur[key].append(float(m.group(5)))
    return doses


def bulk_cadence_s(polls) -> float:
    """Seconds per poll from the integer 'elapsed' column (least squares)."""
    if len(polls) < 4:
        return 0.30
    idx = np.array([p[0] for p in polls], float)
    ela = np.array([p[2] for p in polls], float)
    slope = np.polyfit(idx, ela, 1)[0]
    return float(np.clip(slope, 0.25, 0.60))


def window_slope(t, m, t_end, win):
    sel = (t >= t_end - win) & (t <= t_end + 1e-9)
    if sel.sum() < 3:
        return np.nan
    return float(np.polyfit(t[sel], m[sel], 1)[0])


def extract_bulk_points(powder, doses):
    rows = []
    for n, d in enumerate(doses):
        if d["halt_mass"] is None or d["afterflow_g"] is None or len(d["polls"]) < 4:
            continue
        cad = bulk_cadence_s(d["polls"])
        t = np.array([p[0] for p in d["polls"]], float) * cad
        m = np.array([p[1] for p in d["polls"]], float)
        # active dispense time: first poll with mass above 2 mg -> halt poll
        flowing = np.where(m > 0.002)[0]
        if len(flowing) == 0:
            continue
        t0 = t[flowing[0]] - cad  # flow began within the poll before
        t_halt = t[-1]
        dt = max(t_halt - t0, cad)
        rows.append(dict(
            powder_id=powder, source="G-bulk", detail=f"dose{n}",
            tilt_deg=90.0, rpm=55.0,
            mass_at_stop_g=d["halt_mass"], settled_g=d["settled"],
            afterflow_mg=d["afterflow_g"] * 1000.0,
            flow_mean_g_per_s=d["halt_mass"] / dt,
            flow_slope_g_per_s=window_slope(t, m, t_halt, 2.0),
            flow_slope1_g_per_s=window_slope(t, m, t_halt, 1.0),
            dispense_s=dt, poll_cadence_s=cad,
            note="afterflow from controller's while-settling delta (0.8 s settle + stable weigh)",
        ))
    return rows


def extract_blockd_points(powder, run_dir: Path):
    pf = next(run_dir.glob("polls_*.csv"), None)
    tf = next(run_dir.glob("trials_*.csv"), None)
    if pf is None or tf is None:
        return [], {}
    polls = pd.read_csv(pf)
    trials = pd.read_csv(tf)
    td = trials[trials.block == "D"].reset_index(drop=True)
    rows, traces = [], {}
    for _, tr in td.iterrows():
        rpm = float(tr.rpm)
        pp = polls[(polls.block == "D") & (polls.rpm == rpm)].sort_values("t_ms")
        if len(pp) < 4:
            continue
        t = pp.t_ms.to_numpy(float) / 1000.0
        m = pp.grams.to_numpy(float)
        traces[rpm] = (t - t[0], m - m[0])
        move_s = 180.0 / rpm + rpm / 240.0  # 3 rev + accel/decel ramps (4 rev/s^2)
        afterflow_mg = (float(tr.after_g) - m[-1]) * 1000.0
        rows.append(dict(
            powder_id=powder, source="D-speed", detail=f"{rpm:g}rpm",
            tilt_deg=45.0, rpm=rpm,
            mass_at_stop_g=m[-1] - m[0], settled_g=float(tr.after_g),
            afterflow_mg=afterflow_mg,
            flow_mean_g_per_s=float(tr.delta_g) / move_s,
            flow_slope_g_per_s=window_slope(t, m, t[-1], 2.0),
            flow_slope1_g_per_s=window_slope(t, m, t[-1], 1.0),
            dispense_s=move_s, poll_cadence_s=float(np.median(np.diff(t))),
            note="settled weigh ~2.1 s after last poll; includes <=0.3 s residual rotation",
        ))
    return rows, traces


def fit_tau(flow_g_s, afterflow_mg):
    """Zero-intercept tau (s) = afterflow / flow, least squares, with se."""
    f = np.asarray(flow_g_s, float) * 1000.0  # mg/s
    a = np.asarray(afterflow_mg, float)
    ok = np.isfinite(f) & np.isfinite(a) & (f > 1.0)  # need >1 mg/s to constrain tau
    f, a = f[ok], a[ok]
    if len(f) < 2 or (f ** 2).sum() == 0:
        return np.nan, np.nan, int(len(f))
    tau = float((a * f).sum() / (f ** 2).sum())
    resid = a - tau * f
    se = float(np.sqrt((resid ** 2).sum() / max(len(f) - 1, 1) / (f ** 2).sum()))
    return tau, se, int(len(f))


def slug_metrics(traces):
    """Concentration metrics from the 15-rpm block-D poll trace."""
    if 15.0 not in traces:
        return {}
    t, m = traces[15.0]
    dm = np.diff(m) * 1000.0
    act = np.where(dm > 0.05)[0]
    if len(act) < 6:
        return dict(slug_top20_share=np.nan, slug_max_poll_mg=float(dm.max(initial=0)),
                    slug_active_polls=int(len(act)))
    lo, hi = act[0], act[-1] + 1
    seg = np.clip(dm[lo:hi], 0, None)
    tot = seg.sum()
    k = max(int(round(len(seg) * 0.2)), 1)
    share = float(np.sort(seg)[::-1][:k].sum() / tot) if tot > 0 else np.nan
    return dict(slug_top20_share=share, slug_max_poll_mg=float(seg.max()),
                slug_active_polls=int(len(seg)))


def load_salt_references():
    refs = []
    sr = ROOT / "data/stop-response/2026-08-07_salt/trials_summary.csv"
    if sr.exists():
        d = pd.read_csv(sr)
        refs.append(pd.DataFrame(dict(
            flow_g_per_s=d.flow_g_per_s, afterflow_mg=d.afterflow_mg,
            ref="stop-response 08-07")))
    af = ROOT / "data/afterflow/2026-08-12_salt/afterflow_trials.csv"
    if af.exists():
        d = pd.read_csv(af)
        refs.append(pd.DataFrame(dict(
            flow_g_per_s=d.flow_slope_g_per_s, afterflow_mg=d.afterflow_mg,
            ref="afterflow C6-C8 08-12")))
    lr = ROOT / "data/lowrpm-quantum/2026-08-17_salt/stop_trials.csv"
    if lr.exists():
        d = pd.read_csv(lr)
        refs.append(pd.DataFrame(dict(
            flow_g_per_s=d.flow_at_halt_g_per_s, afterflow_mg=d.afterflow_mg,
            ref="low-rpm stops 08-17")))
    return pd.concat(refs, ignore_index=True) if refs else pd.DataFrame()


def main():
    all_rows, all_traces, all_doses, sig_rows = [], {}, {}, []
    for powder, run in RUNS.items():
        run_dir = BATTERY / run
        raw = next(run_dir.glob("raw_serial_*.log"), None)
        if raw is None and powder in RAW_FALLBACK:
            raw = next((BATTERY / RAW_FALLBACK[powder]).glob("raw_serial_*.log"), None)
        doses = parse_bulk_doses(raw) if raw else []
        all_doses[powder] = doses
        all_rows += extract_bulk_points(powder, doses)
        drows, traces = extract_blockd_points(powder, run_dir)
        all_rows += drows
        all_traces[powder] = traces

        # signature stats
        summ = pd.read_csv(next(run_dir.glob("summary_*.csv")))
        trials = pd.read_csv(next(run_dir.glob("trials_*.csv")))
        dosecsv = pd.read_csv(next(run_dir.glob("doses_*.csv")))
        c = summ[(summ.block == "C")].set_index("tilt_deg")
        e_tap = trials[(trials.block == "E") & (trials.phase == "tap")]
        fine = np.array(sum((d["fine_cycles"] for d in doses), [])) * 1000.0
        tap_cyc = np.array(sum((d["tap_cycles"] for d in doses), [])) * 1000.0
        sm = slug_metrics(traces)
        d_yield = {r["rpm"]: r["mass_at_stop_g"] / 3.0 * 1000.0 +
                   r["afterflow_mg"] / 3.0 for r in drows}
        sig_rows.append(dict(
            powder_id=powder,
            feed_t0_mg_rev=1000 * c.loc[0.0, "mean_g"] if 0.0 in c.index else np.nan,
            feed_t45_mg_rev=1000 * c.loc[45.0, "mean_g"] if 45.0 in c.index else np.nan,
            feed_t90_mg_rev=1000 * c.loc[90.0, "mean_g"] if 90.0 in c.index else np.nan,
            rsd_t45_pct=c.loc[45.0, "rsd_pct"] if 45.0 in c.index else np.nan,
            d15_mg_rev=d_yield.get(15.0, np.nan), d45_mg_rev=d_yield.get(45.0, np.nan),
            d90_mg_rev=d_yield.get(90.0, np.nan),
            tap_t0_mg=1000 * e_tap[e_tap.tilt_deg == 0.0].delta_g.mean(),
            tap_t45_mg=1000 * e_tap[e_tap.tilt_deg == 45.0].delta_g.mean(),
            fine_cycle_mean_mg=fine.mean() if len(fine) else np.nan,
            fine_cycle_cv_pct=100 * fine.std() / fine.mean() if len(fine) and fine.mean() > 0 else np.nan,
            fine_cycle_max_mg=fine.max() if len(fine) else np.nan,
            fine_zero_share=float((fine < 0.5).mean()) if len(fine) else np.nan,
            tapcycle_mean_mg=tap_cyc.mean() if len(tap_cyc) else np.nan,
            dose_status=";".join(dosecsv.status), dose_err_mg=";".join(
                f"{1000 * e:+.1f}" for e in dosecsv.error_g),
            **sm,
        ))

    pts = pd.DataFrame(all_rows)
    taus = {}
    for powder in RUNS:
        sub = pts[pts.powder_id == powder]
        taus[powder] = fit_tau(sub.flow_mean_g_per_s, sub.afterflow_mg)
    salt_ref = load_salt_references()
    tau_ref = fit_tau(salt_ref.flow_g_per_s, salt_ref.afterflow_mg) if len(salt_ref) else (np.nan,) * 3

    pts.to_csv(OUT / "afterflow_from_battery.csv", index=False)
    sig = pd.DataFrame(sig_rows)
    sig.to_csv(OUT / "signature_stats.csv", index=False)

    make_correlation_figure(pts, taus, salt_ref, tau_ref)
    make_signature_figure(all_traces, all_doses, taus)

    # ---- console summary ------------------------------------------------
    pd.set_option("display.width", 200)
    print("\n== afterflow points ==")
    print(pts[["powder_id", "source", "detail", "rpm", "mass_at_stop_g",
               "afterflow_mg", "flow_mean_g_per_s", "flow_slope_g_per_s"]]
          .to_string(index=False))
    print("\n== tau per powder (afterflow = tau * mean flow, battery points) ==")
    for p, (tau, se, n) in taus.items():
        print(f"{SHORT[p]:>18}: tau = {tau:5.2f} +/- {se:4.2f} s  (n={n})")
    print(f"\nsalt dedicated reference: tau = {tau_ref[0]:.2f} +/- {tau_ref[1]:.2f} s "
          f"(n={tau_ref[2]})")
    print("\n== signatures ==")
    print(sig.to_string(index=False))


# --------------------------------------------------------------------------
# figures
# --------------------------------------------------------------------------
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SURFACE, INK, INK2, MUTED, GRID, BASE = ("#fcfcfb", "#0b0b0b", "#52514e",
                                         "#898781", "#e1e0d9", "#c3c2b7")
C_BULK, C_SPEED, C_REF = "#2a78d6", "#eb6834", "#1baf7a"

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE, "text.color": INK,
    "axes.edgecolor": BASE, "axes.labelcolor": INK2,
    "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8,
    "axes.spines.top": False, "axes.spines.right": False,
    "font.size": 9.5, "axes.titlesize": 10.5,
})

ORDER = ["salt", "calcium-lactate", "xanthan-gum", "white-rice-flour",
         "carboxymethyl-cellulose", "sodium-alginate", "brown-rice-flour"]


def make_correlation_figure(pts, taus, salt_ref, tau_ref):
    fig, axes = plt.subplots(2, 4, figsize=(14.5, 7.2))
    fig.suptitle("Afterflow vs flow rate at stop -- recovered from the #116 battery "
                 "(3 dose bulk halts + 3 speed trials per powder)",
                 fontsize=12.5, fontweight="bold", x=0.5, y=0.985)
    tau_salt_ded = tau_ref[0]
    for i, powder in enumerate(ORDER):
        ax = axes.flat[i]
        sub = pts[pts.powder_id == powder]
        tau, se, n = taus[powder]
        fmax_ref = 200.0
        if powder == "salt" and len(salt_ref):
            ax.scatter(salt_ref.flow_g_per_s * 1000, salt_ref.afterflow_mg,
                       s=16, color=C_REF, alpha=0.55, linewidths=0, zorder=2,
                       label="dedicated stop tests (08-07/12/17)")
        for src, color, mk, lbl in [("G-bulk", C_BULK, "o", "dose bulk halt (55 rpm, vertical)"),
                                    ("D-speed", C_SPEED, "s", "speed trial (15/45/90 rpm, tilt 45)")]:
            s = sub[sub.source == src]
            ax.scatter(s.flow_mean_g_per_s * 1000, s.afterflow_mg, s=42,
                       color=color, marker=mk, zorder=3, linewidths=0, label=lbl)
        fmax = max((sub.flow_mean_g_per_s.max() * 1000 if len(sub) else 0) * 1.25, 10)
        if powder == "salt" and len(salt_ref):
            fmax = max(fmax, salt_ref.flow_g_per_s.max() * 1000 * 1.1)
        fx = np.linspace(0, fmax, 50)
        if np.isfinite(tau_salt_ded):
            ax.plot(fx, tau_salt_ded * fx, color=MUTED, lw=1.4, ls="--", zorder=1)
        if np.isfinite(tau):
            ax.plot(fx, tau * fx, color=INK, lw=1.6, zorder=2)
            ax.set_title(f"{SHORT[powder]}   $\\tau$ = {tau:.2f} $\\pm$ {se:.2f} s",
                         loc="left", color=INK)
        else:
            ax.set_title(f"{SHORT[powder]}   no flow -> no afterflow data",
                         loc="left", color=INK)
            ax.text(0.5, 0.5, "auger delivered ~0 mg\n(all 3 doses stalled;\n"
                    "speed trials <=3 mg total)", transform=ax.transAxes,
                    ha="center", va="center", color=INK2, fontsize=9)
        ax.set_xlim(0, fmax)
        ax.set_ylim(bottom=min(0, (sub.afterflow_mg.min() if len(sub) else 0) * 1.2) - 2)
        if i >= 4:
            ax.set_xlabel("mean flow at stop (mg/s)")
        if i % 4 == 0:
            ax.set_ylabel("afterflow (mg)")
        if i == 0:
            ax.legend(loc="upper left", fontsize=7.3, frameon=False)
            ax.annotate(f"dashed gray: salt dedicated fit\n$\\tau$ = {tau_salt_ded:.2f} s",
                        xy=(0.97, 0.06), xycoords="axes fraction", ha="right",
                        fontsize=7.5, color=INK2)
    # summary panel: tau per powder
    ax = axes.flat[7]
    ax.grid(axis="y", visible=False)
    rows = [(SHORT[p], *taus[p]) for p in ORDER if np.isfinite(taus[p][0])]
    ypos = np.arange(len(rows))[::-1]
    for y, (name, tau, se, n) in zip(ypos, rows):
        ax.errorbar(tau, y, xerr=se, fmt="o", color=C_BULK, ms=7,
                    ecolor=BASE, elinewidth=2, capsize=3)
        ax.annotate(f"{name}  (n={n})", xy=(0.02, y), xycoords=("axes fraction", "data"),
                    va="center", fontsize=8.6, color=INK2)
    if np.isfinite(tau_salt_ded):
        ax.axvline(tau_salt_ded, color=MUTED, lw=1.4, ls="--")
        ax.annotate(f"salt dedicated\n{tau_salt_ded:.2f} s", xy=(tau_salt_ded, len(rows) - 0.4),
                    fontsize=7.5, color=INK2, ha="left", xytext=(3, 0),
                    textcoords="offset points")
    ax.set_yticks([])
    ax.set_xlim(0, None)
    ax.set_xlabel("fitted $\\tau$ = afterflow / flow  (s)")
    ax.set_title("one number per powder", loc="left", color=INK)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(OUT / "battery_afterflow_correlation.png", dpi=160)
    plt.close(fig)


def make_signature_figure(all_traces, all_doses, taus):
    n = len(ORDER)
    fig, axes = plt.subplots(n, 2, figsize=(13.5, 2.05 * n),
                             gridspec_kw={"width_ratios": [1.15, 1]})
    fig.suptitle("How each powder doses -- slow-speed delivery texture (left) and the dose "
                 "bulk phase with its afterflow (right)", fontsize=12.5,
                 fontweight="bold", y=0.995)
    for i, powder in enumerate(ORDER):
        axL, axR = axes[i]
        # left: block D 15 rpm trace (4 s per revolution)
        tr = all_traces.get(powder, {})
        if 15.0 in tr:
            t, m = tr[15.0]
            act = np.where(np.diff(m) * 1000 > 0.05)[0]
            t0 = t[act[0]] if len(act) else t[0]
            for k in range(1, 4):
                axL.axvline(t0 + 4.0 * k, color=GRID, lw=1.0, zorder=1)
            axL.plot(t, m * 1000, color=C_BULK, lw=2.0, zorder=3,
                     solid_capstyle="round")
            axL.annotate(f"{(m[-1]) * 1000:.1f} mg / 3 rev", xy=(0.02, 0.86),
                         xycoords="axes fraction", fontsize=8, color=INK2)
            if m.max() * 1000 < 1.0:  # flat no-flow trace: keep a flat-looking scale
                axL.set_ylim(-1, 10)
        axL.set_ylabel(SHORT[powder], fontsize=9.5, color=INK)
        if i == 0:
            axL.set_title("block D: 3 revolutions at 15 rpm, tilt 45 "
                          "(gridlines = one revolution)", loc="left", fontsize=9.5)
        if i == n - 1:
            axL.set_xlabel("time (s)")
        # right: dose 0 bulk polls + settle
        doses = all_doses.get(powder) or []
        d = next((d for d in doses if d["halt_mass"] is not None and len(d["polls"]) > 3),
                 None)
        if d is not None:
            cad = bulk_cadence_s(d["polls"])
            t = np.array([p[0] for p in d["polls"]]) * cad
            m = np.array([p[1] for p in d["polls"]]) * 1000
            axR.plot(t, m, color=C_BULK, lw=2.0, zorder=3, solid_capstyle="round")
            if d["settled"] is not None:
                ts = t[-1] + 2.0
                axR.plot([t[-1], ts], [m[-1], d["settled"] * 1000], color=C_SPEED,
                         lw=2.0, ls=":", zorder=3)
                axR.scatter([t[-1], ts], [m[-1], d["settled"] * 1000], s=[30, 30],
                            color=[INK, C_SPEED], zorder=4, linewidths=0)
                axR.annotate(f"halt", xy=(t[-1], m[-1]), xytext=(-4, 6),
                             textcoords="offset points", ha="right", fontsize=8,
                             color=INK2)
                axR.annotate(f"+{d['afterflow_g'] * 1000:.0f} mg afterflow",
                             xy=(ts, d["settled"] * 1000), xytext=(2, -3),
                             textcoords="offset points", fontsize=8.3, color=INK)
                axR.set_xlim(0, ts * 1.28)
        else:
            axR.text(0.5, 0.5, "bulk stalled: no flow within 4 s\n(3/3 doses, both augers)",
                     transform=axR.transAxes, ha="center", va="center",
                     color=INK2, fontsize=9)
            axR.set_xticks([])
            axR.set_yticks([])
            axR.grid(False)
        if i == 0:
            axR.set_title("dose bulk phase: continuous 55 rpm, tube vertical "
                          "(dotted = settling after halt)", loc="left", fontsize=9.5)
        if i == n - 1:
            axR.set_xlabel("time since dose start (s)")
        axR.set_ylabel("mg", fontsize=8, color=MUTED)
    fig.tight_layout(rect=(0, 0, 1, 0.975))
    fig.savefig(OUT / "battery_dose_signatures.png", dpi=160)
    plt.close(fig)


if __name__ == "__main__":
    main()
