"""Exploratory analysis of the issue #116 battery, restricted to dose *rate*.

The uniform battery (``hardware/test-module/firmware/powder_battery.py``) is
explicitly not an optimization workflow: every parameter is frozen at the
tuned-salt values and the point is to see what each knob does to the mass a
powder delivers.  Blocks A-F are exactly that experiment.  Block G (the
three-phase closed-loop dose) is the controller, and is deliberately excluded
here except as a sanity reference.

    Block A  8 no-actuation reads at tilt 45              -> detection floor
    Block B  15 s static hold at tilt 0/45/90, no actuator -> gravity-only flow
    Block C  6 x 360 deg at 30 RPM, at tilt 0/45/90        -> mg/rev vs tilt
    Block D  3 rev continuous at 15/45/90 RPM, tilt 45     -> mg/s vs speed
             (+ streamed balance polls -> semi-instantaneous rate)
    Block E  8 x (360 deg re-feed + 1 solenoid tap), tilt 0/45 -> mg/tap
    Block F  same shape with the ERM motor                 -> never ran (EIO)

Inputs are the tidy CSVs in ``../candidates/data/`` (built by
``../candidates/build_dataset.py`` from the run artifacts on the
``claude/issue-116-*`` branches).

Usage:
    python eda_dose_rate.py [outdir]
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D

HERE = Path(__file__).parent
DATA = HERE.parent / "candidates" / "data"

# --- palette: identical to ../candidates/make_candidate_figures.py -----------
SURROGATE = "#2a78d6"   # categorical slot 1, blue
RESEARCH = "#eb6834"    # categorical slot 2, orange
ACCENT = "#1baf7a"      # categorical slot 3, aqua
# Tilt and RPM are ordered magnitudes -> one-hue ordinal ramp, never hues.
TILT_RAMP = {0.0: "#86b6ef", 45.0: "#2a78d6", 90.0: "#104281"}
RPM_RAMP = {15.0: "#86b6ef", 45.0: "#2a78d6", 90.0: "#104281"}
GOOD, WARNING, SERIOUS, CRITICAL = "#0ca30c", "#fab219", "#ec835a", "#d03b3b"
INK, INK2, MUTED = "#0b0b0b", "#52514e", "#b8b6ae"
SURFACE = "#fcfcfb"

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE, "font.size": 9,
    "axes.edgecolor": MUTED, "axes.labelcolor": INK, "axes.titlesize": 10,
    "axes.titleweight": "bold", "axes.titlecolor": INK, "axes.linewidth": 0.8,
    "xtick.color": INK2, "ytick.color": INK2, "text.color": INK,
    "grid.color": "#e8e6e0", "grid.linewidth": 0.7, "legend.frameon": False,
    "axes.spines.top": False, "axes.spines.right": False,
})

RUNS = pd.read_csv(DATA / "runs.csv")
TRIALS = pd.read_csv(DATA / "trials.csv")
FEED = pd.read_csv(DATA / "feed.csv")
POLLS = pd.read_csv(DATA / "polls.csv")
DOSES = pd.read_csv(DATA / "doses.csv")

META = RUNS.set_index("run_id")[["display", "powder_id", "track",
                                 "qc_valid", "poolable", "qc_verdict"]]
TRIALS = TRIALS.drop(columns=["powder_id"]).join(META, on="run_id")
POLLS = POLLS.drop(columns=["powder_id"]).join(META, on="run_id")

# Powders the battery could not resolve above its own floor.  Their numbers are
# upper bounds, never measurements, and are drawn with a bound arrow.
BOUNDED = {"brown-rice-flour": 0.3, "silicon-325": 1.2, "fumed-silica": 0.25}

# Block E on fumed silica carries a documented solenoid-impulse artifact (the
# balance sees the strike, not powder) and is never read as a tap quantum.
TAP_ARTIFACT = {"fumed-silica"}

ROTATION_RPM = 30.0     # blocks C and E re-feed
HOLD_S = 15.0           # block B
NOMINAL_REVS = 3.0      # block D, commanded


def representative_runs() -> pd.DataFrame:
    """One run per powder -- mirrors ../candidates/make_candidate_figures.py."""
    ok = RUNS[RUNS.qc_valid | RUNS.powder_id.isin(BOUNDED)].copy()
    ok["rank"] = (~ok.poolable).astype(int)
    ok = ok.sort_values(["powder_id", "rank", "started_utc"],
                        ascending=[True, True, False])
    return ok.groupby("powder_id", as_index=False).first()


REP = representative_runs()
REP_IDS = list(REP.run_id)


def track_colour(track: str) -> str:
    return RESEARCH if track == "research" else SURROGATE


def spin_seconds() -> pd.DataFrame:
    """Reconstruct how long the block-D motor actually ran, per (run, RPM).

    The firmware's speed loop advances its own clock by the *nominal* poll
    period (``waited_ms += speed_poll_ms``) but each iteration also waits for a
    balance read, so the loop -- and the auger, which is in velocity mode for
    its whole duration -- overruns the commanded three revolutions by the ratio
    of achieved to nominal poll cadence.  The poll timestamps recover it.
    """
    rows = []
    for (rid, rpm), g in POLLS.groupby(["run_id", "rpm"]):
        g = g.sort_values("t_ms")
        dt = np.diff(g.t_ms.values) / 1000.0
        if len(dt) == 0:
            continue
        med = float(np.median(dt))
        rows.append(dict(run_id=rid, rpm=rpm, n_polls=len(g), poll_dt_s=med,
                         spin_s=len(g) * med, revs_actual=rpm * len(g) * med / 60.0))
    return pd.DataFrame(rows)


SPIN = spin_seconds()


def block_d() -> pd.DataFrame:
    d = TRIALS[TRIALS.block == "D"].copy()
    d["mg"] = d.delta_g * 1000
    d = d.merge(SPIN, on=["run_id", "rpm"])
    d["nominal_s"] = 60.0 * NOMINAL_REVS / d.rpm
    d["mg_s_nominal"] = d.mg / d.nominal_s
    d["mg_s"] = d.mg / d.spin_s
    d["mg_rev_nominal"] = d.mg / NOMINAL_REVS
    d["mg_rev"] = d.mg / d.revs_actual
    return d


D = block_d()


def instantaneous(rid: str, rpm: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Poll trace -> (t_s from start, cumulative mg, per-interval mg/s)."""
    g = POLLS[(POLLS.run_id == rid) & (POLLS.rpm == rpm)].sort_values("t_ms")
    t = (g.t_ms.values - g.t_ms.values[0]) / 1000.0
    m = (g.grams.values - g.grams.values[0]) * 1000.0
    rate = np.diff(m) / np.diff(t)
    return t, m, rate


def power_law() -> pd.DataFrame:
    """Fit mg/s ~ RPM^alpha per run.  alpha = 1 means mass/rev is speed-free."""
    rows = []
    for (rid, disp, track), g in D.groupby(["run_id", "display", "track"]):
        g = g[g.mg_s > 0]
        if len(g) < 3:
            continue
        alpha = np.polyfit(np.log(g.rpm), np.log(g.mg_s), 1)[0]
        r = np.corrcoef(np.log(g.rpm), np.log(g.mg_s))[0, 1]
        rows.append(dict(run_id=rid, display=disp, track=track,
                         alpha=alpha, r2=r ** 2))
    return pd.DataFrame(rows)


ALPHA = power_law()



def log_ticks(ax, axis="x", ticks=(15, 45, 90)):
    """Fixed major ticks and no minor labels -- log minor labels are clutter."""
    from matplotlib.ticker import FixedLocator, NullLocator, ScalarFormatter
    a = ax.xaxis if axis == "x" else ax.yaxis
    a.set_major_locator(FixedLocator(list(ticks)))
    a.set_major_formatter(ScalarFormatter())
    a.set_minor_locator(NullLocator())


def spread(values, gap):
    """Nudge label positions apart in log space, preserving order."""
    order = np.argsort(values)
    out = np.array(values, dtype=float)
    for k in range(1, len(order)):
        i, j = order[k - 1], order[k]
        if out[j] - out[i] < gap:
            out[j] = out[i] + gap
    return out


def noise_floor(run_id: str) -> float:
    """Block A |delta| ceiling for this run -- the run's own detection floor.

    Blocks B and E measure milligrams against a balance that, after the
    2026-08-20 fume-hood move, drifts tens of milligrams over a comparable
    window.  Anything inside this bound is the bench, not the powder.
    """
    a = TRIALS[(TRIALS.run_id == run_id) & (TRIALS.block == "A")].delta_g
    if a.empty:
        return 0.0005
    return max(float(a.abs().max()) * 1000, 0.5)


def save(fig, name, outdir):
    path = Path(outdir) / f"{name}.png"
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"  {path.name}")


# ---------------------------------------------------------------------------
# R1  what the campaign actually measured
# ---------------------------------------------------------------------------
def fig_coverage(outdir):
    blocks = list("ABCDEFG")
    order = (REP.sort_values(["track", "display"], ascending=[True, True])
             .reset_index(drop=True))
    counts = np.zeros((len(order), len(blocks)))
    for i, row in order.iterrows():
        t = TRIALS[TRIALS.run_id == row.run_id]
        for j, b in enumerate(blocks):
            counts[i, j] = (t.block == b).sum()
        counts[i, blocks.index("G")] = len(
            DOSES[DOSES.run_id == row.run_id])

    fig, ax = plt.subplots(figsize=(7.6, 5.0))
    shown = np.where(counts > 0, counts, np.nan)
    ax.imshow(np.log10(shown + 1), cmap="Blues", vmin=0, vmax=np.log10(65),
              aspect="auto", alpha=0.85)
    for i in range(len(order)):
        for j in range(len(blocks)):
            n = int(counts[i, j])
            ax.text(j, i, str(n) if n else "--", ha="center", va="center",
                    fontsize=8,
                    color=INK if n < 30 else SURFACE)
    ax.set_xticks(range(len(blocks)))
    ax.set_xticklabels(["A\nnoise", "B\nhold", "C\ntilt", "D\nspeed",
                        "E\ntap", "F\nvib", "G\ndose"], fontsize=8)
    ax.set_yticks(range(len(order)))
    ax.set_yticklabels(
        [f"{r.display}" for _, r in order.iterrows()], fontsize=8)
    for tick, (_, r) in zip(ax.get_yticklabels(), order.iterrows()):
        tick.set_color(track_colour(r.track))
    ax.set_xticks(np.arange(-.5, len(blocks), 1), minor=True)
    ax.set_yticks(np.arange(-.5, len(order), 1), minor=True)
    ax.grid(which="minor", color=SURFACE, linewidth=2)
    ax.tick_params(which="minor", length=0)
    for s in ax.spines.values():
        s.set_visible(False)

    # QC verdict as a labelled margin, status colour + text (never colour alone)
    for i, (_, r) in enumerate(order.iterrows()):
        col = GOOD if r.qc_valid else CRITICAL
        ax.text(len(blocks) + 0.85, i, str(r.qc_verdict), fontsize=7,
                color=col, va="center", ha="left")
    # margin column: total mass this powder actually pushed through the auger
    ax.text(len(blocks) - 0.30, -0.85, "dispensed", fontsize=7.5, color=INK2,
            ha="left")
    ax.text(len(blocks) + 0.85, -0.85, "QC verdict", fontsize=7.5, color=INK2,
            ha="left")
    for i, (_, r) in enumerate(order.iterrows()):
        t = TRIALS[TRIALS.run_id == r.run_id]
        g = t[t.block.isin(list("BCDE"))].delta_g.clip(lower=0).sum()
        ax.text(len(blocks) - 0.30, i, f"{g:.2f} g", fontsize=7.5, color=INK2,
                va="center", ha="left")
    ax.set_title("R1  Round-1 battery coverage: measured trials per block\n"
                 "one representative run per powder; block G counts "
                 "closed-loop doses, not trials", loc="left", pad=26)
    ax.text(0.0, -0.155,
            "blue = food-safe surrogate    orange = research-relevant"
            "        block F never ran: the DRV2605L haptic driver reports EIO"
            "\ndispensed = mass collected across blocks B-E, i.e. what this "
            "powder actually pushed through the auger in one run",
            fontsize=7.5, color=INK2, ha="left", va="top",
            transform=ax.transAxes)
    save(fig, "R1_coverage", outdir)


# ---------------------------------------------------------------------------
# R2  the rate ladder at the reference condition
# ---------------------------------------------------------------------------
def reference_rate() -> pd.DataFrame:
    """Block C at tilt 45, 30 RPM: mg/rev and the mg/s it implies."""
    rows = []
    for _, r in REP.iterrows():
        t = TRIALS[(TRIALS.run_id == r.run_id) & (TRIALS.block == "C")
                   & (TRIALS.tilt_deg == 45.0)]
        mg = t.delta_g.values * 1000
        bound = r.powder_id in BOUNDED
        val = BOUNDED[r.powder_id] if bound else mg.mean()
        rows.append(dict(powder_id=r.powder_id, display=r.display,
                         track=r.track, run_id=r.run_id, bounded=bound,
                         mg_rev=val, rsd=100 * mg.std(ddof=1) / mg.mean()
                         if mg.mean() > 0 else np.nan,
                         mg_s=val * ROTATION_RPM / 60.0))
    return pd.DataFrame(rows).sort_values("mg_rev")


def fig_ladder(outdir):
    L = reference_rate()
    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    y = np.arange(len(L))
    for i, (_, r) in enumerate(L.iterrows()):
        c = track_colour(r.track)
        ax.plot([r.mg_s * 0.02, r.mg_s], [i, i], color=c, lw=2, alpha=0.35,
                solid_capstyle="round")
        if r.bounded:
            ax.plot(r.mg_s, i, "<", ms=9, mfc=SURFACE, mec=c, mew=2)
            ax.annotate("", xy=(r.mg_s * 0.35, i), xytext=(r.mg_s, i),
                        arrowprops=dict(arrowstyle="->", color=c, lw=1.4))
        else:
            ax.plot(r.mg_s, i, "o", ms=9, color=c, mec=SURFACE, mew=2)
        label = (f"$\\leq${r.mg_s:.2f}" if r.bounded
                 else (f"{r.mg_s:.1f}" if r.mg_s >= 1 else f"{r.mg_s:.2f}"))
        ax.text(r.mg_s * 1.45, i, label, va="center", fontsize=8, color=INK)
    ax.set_yticks(y)
    ax.set_yticklabels(L.display, fontsize=8.5)
    for tick, tr in zip(ax.get_yticklabels(), L.track):
        tick.set_color(track_colour(tr))
    ax.set_xscale("log")
    ax.set_xlim(0.05, 420)
    ax.set_xlabel("mean dose rate at the reference condition  (mg s$^{-1}$)")
    ax.grid(axis="x", alpha=0.6)
    ax.set_axisbelow(True)
    ax.set_title("R2  Dose rate spans three decades under one frozen parameter set\n"
                 "block C: 30 RPM, tilt 45$^\\circ$, mean of six single revolutions",
                 loc="left")
    # right-hand text column: the per-revolution quantum behind each rate
    ax.text(1.02, 1.02, "mg/rev", transform=ax.transAxes, fontsize=8,
            color=INK2, ha="left", va="bottom")
    for i, (_, r) in enumerate(L.iterrows()):
        txt = (f"$\\leq${r.mg_rev:.2f}" if r.bounded else f"{r.mg_rev:.1f}")
        ax.text(1.02, i, txt, transform=ax.get_yaxis_transform(), fontsize=8,
                color=INK2, va="center", ha="left")
    ax.legend(handles=[Line2D([], [], marker="o", ls="", color=SURROGATE,
                              label="food-safe surrogate"),
                       Line2D([], [], marker="o", ls="", color=RESEARCH,
                              label="research-relevant"),
                       Line2D([], [], marker="<", ls="", mfc=SURFACE,
                              mec=INK2, label="upper bound (no resolvable flow)")],
              loc="lower right", fontsize=8)
    save(fig, "R2_rate_ladder", outdir)


# ---------------------------------------------------------------------------
# R3  tilt
# ---------------------------------------------------------------------------
def fig_tilt(outdir):
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(10.6, 4.6),
                                  gridspec_kw=dict(width_ratios=[1.3, 1],
                                                   wspace=0.42))
    ratios, ends, labs, cols = [], [], [], []
    for _, r in REP.iterrows():
        t = TRIALS[(TRIALS.run_id == r.run_id) & (TRIALS.block == "C")]
        m = t.groupby("tilt_deg").delta_g.mean() * 1000
        if m.max() < 0.5:
            continue
        c = track_colour(r.track)
        floor = 0.06
        y = np.maximum(m.values, floor)
        censored = m.values <= floor
        ax.plot(m.index, y, "-", color=c, lw=1.6, alpha=0.85)
        ax.plot(m.index[~censored], y[~censored], "o", color=c, ms=5,
                mec=SURFACE, mew=1)
        # a revolution that moved nothing measurable is a bound, not a zero
        ax.plot(m.index[censored], y[censored], "v", color=SURFACE, ms=7,
                mec=c, mew=1.6)
        ends.append(np.log10(y[-1])); labs.append(r.display); cols.append(c)
        if m.get(0.0, 0) > 0.5:
            ratios.append((r.display, r.track, m[90.0] / m[0.0]))
    for yy, lab, c in zip(spread(ends, 0.105), labs, cols):
        ax.text(93, 10 ** yy, " " + lab, fontsize=7.5, color=c, va="center")
    ax.set_yscale("log")
    ax.set_xticks([0, 45, 90])
    ax.set_xlim(-6, 210)
    ax.set_ylim(0.045, 1600)
    ax.set_xlabel("tube tilt (deg; 0 = horizontal, 90 = vertical)")
    ax.set_ylabel("mass per auger revolution (mg)")
    ax.grid(alpha=0.6)
    ax.set_axisbelow(True)
    ax.set_title("R3a  Tilt is the strongest knob the firmware owns",
                 loc="left", pad=10)
    ax.plot([], [], "v", color=SURFACE, mec=INK2, mew=1.6,
            label="no resolvable flow (bound)")
    ax.legend(fontsize=7.5, loc="lower right")

    R = pd.DataFrame(ratios, columns=["display", "track", "ratio"]
                     ).sort_values("ratio")
    ax2.barh(np.arange(len(R)), R.ratio,
             color=[track_colour(t) for t in R.track], height=0.62)
    ax2.axvline(1, color=INK2, lw=1, ls="--")
    ax2.set_yticks(np.arange(len(R)))
    ax2.set_yticklabels(R.display, fontsize=8)
    for tick, tr in zip(ax2.get_yticklabels(), R.track):
        tick.set_color(track_colour(tr))
    for i, v in enumerate(R.ratio):
        ax2.text(v * 1.05, i, f"{v:.1f}$\\times$", va="center", fontsize=8,
                 color=INK)
    ax2.set_xscale("log")
    ax2.set_xlim(0.8, 45)
    log_ticks(ax2, "x", (1, 3, 10, 30))
    ax2.set_xlabel("gravity assist:  mg/rev at 90$^\\circ$ / mg/rev at 0$^\\circ$")
    ax2.grid(axis="x", alpha=0.6)
    ax2.set_axisbelow(True)
    ax2.set_title("R3b  How much of the flow is gravity, not the auger",
                  loc="left", pad=10)
    save(fig, "R3_tilt", outdir)


# ---------------------------------------------------------------------------
# R4  speed -- the headline
# ---------------------------------------------------------------------------
def fig_speed(outdir):
    fig, axs = plt.subplots(1, 3, figsize=(13.4, 4.6),
                            gridspec_kw=dict(width_ratios=[1.2, 1.1, 1.05],
                                             wspace=0.46))
    ax, axb, axc = axs
    A = ALPHA.set_index("run_id")
    ends, labs, cols = [], [], []
    for rid in REP_IDS:
        g = D[(D.run_id == rid) & (D.mg_s > 0)].sort_values("rpm")
        if len(g) < 3 or rid not in A.index:
            continue
        a_ = A.loc[rid, "alpha"]
        c = ACCENT if a_ >= 1 else track_colour(g.track.iloc[0])
        ax.plot(g.rpm, g.mg_s, "-o", color=c, lw=1.6, ms=5, alpha=0.85,
                mec=SURFACE, mew=1)
        ends.append(np.log10(g.mg_s.iloc[-1]))
        labs.append(g.display.iloc[0]); cols.append(c)
        base = g[g.rpm == 15.0].mg_rev.iloc[0]
        axb.plot(g.rpm, g.mg_rev / base, "-o", color=c, lw=1.6, ms=5,
                 alpha=0.85, mec=SURFACE, mew=1)
    for yy, lab, c in zip(spread(ends, 0.075), labs, cols):
        ax.text(95, 10 ** yy, " " + lab, fontsize=7.5, color=c, va="center")
    # guide: what a purely volumetric (fill-independent) auger would deliver
    ax.plot([15, 90], [7, 42], ls=(0, (4, 3)), color=INK2, lw=1.2)
    ax.text(34, 26, "slope 1\n(volumetric)", fontsize=7.5, color=INK2,
            ha="center")
    ax.set_xscale("log"); ax.set_yscale("log")
    log_ticks(ax, "x")
    ax.set_xlim(12, 260)
    ax.set_xlabel("auger speed (RPM)")
    ax.set_ylabel("dose rate (mg s$^{-1}$)")
    ax.grid(alpha=0.6); ax.set_axisbelow(True)
    ax.set_title("R4a  Six times the speed buys about\nthree times the rate",
                 loc="left", pad=10)

    axb.axhline(1, color=INK2, lw=1, ls="--")
    axb.set_xscale("log")
    log_ticks(axb, "x")
    axb.set_xlim(13, 105)
    axb.set_xlabel("auger speed (RPM)")
    axb.set_ylabel("mass per revolution, relative to 15 RPM")
    axb.grid(alpha=0.6); axb.set_axisbelow(True)
    axb.set_title("R4b  Flights fill by time,\nnot by turn", loc="left", pad=10)

    S = ALPHA[ALPHA.run_id.isin(REP_IDS)].sort_values("alpha")
    cs = [ACCENT if a_ >= 1 else track_colour(t)
          for a_, t in zip(S.alpha, S.track)]
    axc.barh(np.arange(len(S)), S.alpha, color=cs, height=0.62)
    axc.axvline(1, color=INK2, lw=1.2, ls="--")
    axc.set_yticks(np.arange(len(S)))
    axc.set_yticklabels(S.display, fontsize=8)
    for tick, c in zip(axc.get_yticklabels(), cs):
        tick.set_color(c)
    for i, v in enumerate(S.alpha):
        axc.text(v + 0.03, i, f"{v:.2f}", va="center", fontsize=8, color=INK)
    axc.set_xlim(0, 1.72)
    axc.set_ylim(-0.6, len(S) - 0.4)
    axc.text(1.03, -0.45, "volumetric", fontsize=7.5, color=INK2, va="center")
    axc.set_xlabel("speed exponent $\\alpha$   (rate $\\propto$ RPM$^{\\alpha}$)")
    axc.grid(axis="x", alpha=0.6); axc.set_axisbelow(True)
    axc.set_title("R4c  Two regimes", loc="left", pad=10)
    axc.legend(handles=[
        Line2D([], [], marker="s", ls="", color=SURROGATE,
               label="$\\alpha<1$  fill-limited, surrogate"),
        Line2D([], [], marker="s", ls="", color=RESEARCH,
               label="$\\alpha<1$  fill-limited, research"),
        Line2D([], [], marker="s", ls="", color=ACCENT,
               label="$\\alpha\\geq1$  mobilisation-limited")],
        loc="upper center", bbox_to_anchor=(0.5, -0.20), fontsize=7.5)
    save(fig, "R4_speed", outdir)


# ---------------------------------------------------------------------------
# R5  semi-instantaneous rate
# ---------------------------------------------------------------------------
def fig_instantaneous(outdir):
    picks = ["salt", "alsi10mg", "xanthan-gum", "silicon-110-200"]
    fig = plt.figure(figsize=(12.4, 6.4))
    gs = fig.add_gridspec(2, 4, height_ratios=[1, 1], hspace=0.62,
                          wspace=0.36, top=0.86)

    for k, pid in enumerate(picks):
        rid = REP[REP.powder_id == pid].run_id.iloc[0]
        axk = fig.add_subplot(gs[0, k])
        t, m, _ = instantaneous(rid, 15.0)
        axk.step(t, m, where="post", color=TILT_RAMP[45.0], lw=1.8)
        period = 60.0 / 15.0
        for r in np.arange(period, t.max(), period):
            axk.axvline(r, color=MUTED, lw=0.8, ls=":")
        axk.set_title(REP[REP.powder_id == pid].display.iloc[0],
                      loc="left", fontsize=9)
        axk.set_xlabel("time (s)")
        if k == 0:
            axk.set_ylabel("cumulative mass (mg)")
        axk.grid(alpha=0.5); axk.set_axisbelow(True)

    # autocorrelation of the instantaneous rate, all resolvable 15 RPM traces
    axa = fig.add_subplot(gs[1, :2])
    periods = []
    for rid in REP_IDS:
        g = POLLS[(POLLS.run_id == rid) & (POLLS.rpm == 15.0)]
        if g.empty:
            continue
        t, m, rate = instantaneous(rid, 15.0)
        if m[-1] < 20:
            continue
        dt = float(np.median(np.diff(t)))
        x = rate - rate.mean()
        ac = np.correlate(x, x, "full")[len(x) - 1:]
        ac = ac / ac[0]
        lags = np.arange(len(ac)) * dt
        keep = lags <= 8
        axa.plot(lags[keep], ac[keep], color=SURROGATE, lw=1.2, alpha=0.45)
        lo, hi = int(2.0 / dt), int(6.5 / dt)
        if hi > lo:
            periods.append(lags[lo + int(np.argmax(ac[lo:hi]))])
    axa.axvline(4.0, color=RESEARCH, lw=1.6)
    axa.text(4.12, 0.82, "one auger revolution\nat 15 RPM (4.0 s)",
             color=RESEARCH, fontsize=8)
    axa.axhline(0, color=INK2, lw=0.8)
    axa.set_xlabel("lag (s)")
    axa.set_ylabel("autocorrelation of the\nsemi-instantaneous rate")
    axa.grid(alpha=0.5); axa.set_axisbelow(True)
    axa.set_title(f"R5b  Discharge locks to the revolution:\nmedian "
                  f"autocorrelation peak at {np.median(periods):.2f} s "
                  f"(n={len(periods)} powders)", loc="left", pad=10)

    # crest factor: how peaky the delivery is, per speed
    axc = fig.add_subplot(gs[1, 2:])
    rows = []
    for rid in REP_IDS:
        for rpm in (15.0, 45.0, 90.0):
            g = POLLS[(POLLS.run_id == rid) & (POLLS.rpm == rpm)]
            if g.empty:
                continue
            t, m, rate = instantaneous(rid, rpm)
            mean = m[-1] / t[-1]
            if mean < 5:
                continue
            rows.append(dict(rpm=rpm, crest=np.percentile(rate, 95) / mean,
                             polls_per_rev=(60.0 / rpm)
                             / float(np.median(np.diff(t)))))
    Cf = pd.DataFrame(rows)
    for rpm, g in Cf.groupby("rpm"):
        x = rpm * np.exp(np.linspace(-0.06, 0.06, len(g)))
        axc.plot(x, g.crest, "o", color=RPM_RAMP[rpm], ms=7, mec=SURFACE,
                 mew=1.2)
        axc.plot([rpm * 0.88, rpm * 1.14], [g.crest.median()] * 2,
                 color=RPM_RAMP[rpm], lw=2.4)
        axc.text(rpm, g.crest.max() + 0.16, f"median {g.crest.median():.1f}",
                 ha="center", fontsize=8, color=RPM_RAMP[rpm])
    axc.axhline(1, color=INK2, lw=1, ls="--")
    axc.text(16, 1.06, "perfectly steady flow", fontsize=7.5, color=INK2)
    axc.set_xscale("log")
    log_ticks(axc, "x")
    axc.set_xlim(12, 120)
    axc.set_xlabel("auger speed (RPM)")
    axc.set_ylabel("crest factor  (95th pct rate / mean rate)")
    axc.grid(alpha=0.5); axc.set_axisbelow(True)
    axc.set_title("R5c  Pulsation is real at 15 RPM --\nbut 45 and 90 RPM "
                  "are under-sampled", loc="left", pad=10)
    axc.text(0.0, -0.40, "the balance polls every 0.29-0.39 s, so a 0.67 s "
             "revolution at 90 RPM gets fewer than two\nsamples: those crest "
             "factors are aliased floors, not measurements.",
             transform=axc.transAxes, fontsize=7.5, color=INK2)
    fig.suptitle("R5  Semi-instantaneous rate: the auger delivers one slug "
                 "per revolution\nblock D streamed balance polls, tilt "
                 "45$^\\circ$; top row is 15 RPM, dotted lines mark "
                 "revolutions",
                 x=0.008, y=0.99, ha="left", va="top", fontsize=10.5,
                 fontweight="bold")
    save(fig, "R5_instantaneous", outdir)


# ---------------------------------------------------------------------------
# R6  every actuation knob on one axis
# ---------------------------------------------------------------------------
def fig_knobs(outdir):
    rows = []
    for _, r in REP.iterrows():
        t = TRIALS[TRIALS.run_id == r.run_id]
        c = t[t.block == "C"].groupby("tilt_deg").delta_g.mean() * 1000
        e = t[t.block == "E"]
        b = t[t.block == "B"].set_index("tilt_deg").delta_g * 1000
        floor = noise_floor(r.run_id)

        artifact = r.powder_id in TAP_ARTIFACT

        def keep(v, tap=False):
            """Blocks B and E are milligram signals; drop anything the run's
            own no-actuation baseline cannot distinguish from bench drift."""
            if tap and artifact:
                return np.nan
            return v if (pd.notna(v) and v > floor) else np.nan

        rows.append(dict(
            display=r.display, track=r.track, powder_id=r.powder_id,
            floor_mg=floor,
            rev0=c.get(0.0, np.nan), rev45=c.get(45.0, np.nan),
            rev90=c.get(90.0, np.nan),
            tap0=keep(e[(e.phase == "tap") & (e.tilt_deg == 0.0)]
                      .delta_g.mean() * 1000, tap=True),
            tap45=keep(e[(e.phase == "tap") & (e.tilt_deg == 45.0)]
                       .delta_g.mean() * 1000, tap=True),
            hold90=keep(b.get(90.0, np.nan))))
    K = pd.DataFrame(rows).sort_values("rev45")
    fig, ax = plt.subplots(figsize=(8.6, 5.0))
    cols = {"rev0": TILT_RAMP[0.0], "rev45": TILT_RAMP[45.0],
            "rev90": TILT_RAMP[90.0], "tap0": ACCENT, "tap45": "#0d7a55",
            "hold90": MUTED}
    marks = {"rev0": "o", "rev45": "o", "rev90": "o", "tap0": "^",
             "tap45": "^", "hold90": "s"}
    for i, (_, r) in enumerate(K.iterrows()):
        vals = [(k, r[k]) for k in cols if pd.notna(r[k])]
        good = [v for _, v in vals if v > 0.05]
        if good:
            ax.plot([min(good), max(good)], [i, i], color=MUTED, lw=1,
                    zorder=0)
        for k, v in vals:
            if v <= 0.05:
                continue
            ax.plot(v, i, marks[k], color=cols[k], ms=7, mec=SURFACE, mew=1.2)
    ax.set_yticks(np.arange(len(K)))
    ax.set_yticklabels(K.display, fontsize=8.5)
    for tick, tr in zip(ax.get_yticklabels(), K.track):
        tick.set_color(track_colour(tr))
    ax.set_xscale("log")
    ax.set_xlim(0.04, 900)
    ax.set_xlabel("mass delivered per actuation event (mg)")
    ax.grid(axis="x", alpha=0.6); ax.set_axisbelow(True)
    ax.set_title("R6  What each control knob is worth, per event\n"
                 "one revolution at 30 RPM; one solenoid tap; 15 s of gravity "
                 "alone.  Taps and holds inside the run's own\nno-actuation "
                 "noise band are omitted -- which is why most rows have no "
                 "hold marker at all.", loc="left")
    ax.legend(handles=[
        Line2D([], [], marker="o", ls="", color=TILT_RAMP[0.0], label="1 rev, tilt 0$^\\circ$"),
        Line2D([], [], marker="o", ls="", color=TILT_RAMP[45.0], label="1 rev, tilt 45$^\\circ$"),
        Line2D([], [], marker="o", ls="", color=TILT_RAMP[90.0], label="1 rev, tilt 90$^\\circ$"),
        Line2D([], [], marker="^", ls="", color=ACCENT, label="1 tap, tilt 0$^\\circ$"),
        Line2D([], [], marker="^", ls="", color="#0d7a55", label="1 tap, tilt 45$^\\circ$"),
        Line2D([], [], marker="s", ls="", color=MUTED, label="15 s hold, tilt 90$^\\circ$"),
    ], loc="lower right", fontsize=7.5, ncol=2)
    save(fig, "R6_knobs", outdir)


# ---------------------------------------------------------------------------
# R7  the block-D normalisation defect, and the cross-block check that finds it
# ---------------------------------------------------------------------------
def fig_normalisation(outdir):
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(10.6, 4.6),
                                  gridspec_kw=dict(wspace=0.34))
    S = SPIN.merge(RUNS[["run_id", "started_utc", "display"]], on="run_id")
    S["date"] = pd.to_datetime(S.started_utc, format="mixed", utc=True)
    for rpm, g in S.groupby("rpm"):
        g = g.sort_values("date")
        ax.plot(g.date, g.spin_s / (60.0 * NOMINAL_REVS / g.rpm), "-o",
                color=RPM_RAMP[rpm], lw=1.4, ms=6, mec=SURFACE, mew=1,
                label=f"{int(rpm)} RPM")
    ax.axhline(1, color=INK2, lw=1.2, ls="--")
    ax.text(S.date.min(), 1.02, "commanded 3 revolutions", fontsize=8,
            color=INK2)
    ax.text(0.0, -0.36, "the speed loop advances its own clock by the "
            "nominal poll period; the balance sets the real one, so the "
            "auger\nkeeps turning. Total mass and mg/s are unaffected -- only "
            "the per-revolution normalisation is.",
            transform=ax.transAxes, fontsize=7.5, color=INK2)
    ax.set_ylabel("actual / commanded rotation")
    ax.set_ylim(0.9, 1.7)
    ax.set_title("R7a  Block D over-rotates, by a factor that\n"
                 "stepped mid-campaign", loc="left", pad=10)
    ax.legend(fontsize=8, loc="upper left")
    ax.grid(alpha=0.6); ax.set_axisbelow(True)
    for lbl in ax.get_xticklabels():
        lbl.set_rotation(30)
        lbl.set_ha("right")

    # cross-block check: block C at 30 RPM vs block D at 45 RPM
    xs, y_nom, y_cor, names, tracks = [], [], [], [], []
    for _, r in REP.iterrows():
        c = TRIALS[(TRIALS.run_id == r.run_id) & (TRIALS.block == "C")
                   & (TRIALS.tilt_deg == 45.0)].delta_g.mean() * 1000
        d = D[(D.run_id == r.run_id) & (D.rpm == 45.0)]
        if d.empty or c < 5:
            continue
        xs.append(c); y_nom.append(d.mg_rev_nominal.iloc[0])
        y_cor.append(d.mg_rev.iloc[0]); names.append(r.display)
        tracks.append(r.track)
    xs = np.array(xs); y_nom = np.array(y_nom); y_cor = np.array(y_cor)
    lim = [4, 500]
    beta = float(np.median([np.polyfit(np.log(g.rpm), np.log(g.mg_rev), 1)[0]
                            for _, g in D[D.run_id.isin(REP_IDS)
                                          & (D.mg_rev > 0)].groupby("run_id")
                            if len(g) == 3]))
    expect = (45.0 / ROTATION_RPM) ** beta
    ax2.plot(lim, lim, color=INK2, lw=1.2, ls="--")
    ax2.plot(lim, [v * expect for v in lim], color=ACCENT, lw=1.4,
             ls=(0, (5, 3)))
    ax2.text(160, 190, "1:1", color=INK2, fontsize=8)
    ax2.text(9, 4.6, f"{expect:.2f}:1 -- what the fitted speed exponent\n"
             f"$\\beta$={beta:.2f} predicts for 30 $\\to$ 45 RPM",
             color=ACCENT, fontsize=7.5)
    ax2.plot(xs, y_nom, "o", color=MUTED, ms=7, mec=SURFACE, mew=1.2,
             label=f"as recorded (median {np.median(y_nom/xs):.2f}$\\times$)")
    ax2.plot(xs, y_cor, "o", color=SURROGATE, ms=7, mec=SURFACE, mew=1.2,
             label=f"spin-corrected (median {np.median(y_cor/xs):.2f}$\\times$)")
    for x, a, b in zip(xs, y_nom, y_cor):
        ax2.plot([x, x], [a, b], color=MUTED, lw=0.8, zorder=0)
    ax2.set_xscale("log"); ax2.set_yscale("log")
    ax2.set_xlim(*lim); ax2.set_ylim(*lim)
    ax2.set_xlabel("block C, 30 RPM, tilt 45$^\\circ$   (mg/rev)")
    ax2.set_ylabel("block D, 45 RPM, tilt 45$^\\circ$   (mg/rev)")
    ax2.grid(alpha=0.6); ax2.set_axisbelow(True)
    ax2.legend(fontsize=8, loc="upper left")
    ax2.set_title("R7b  Correcting it reconciles two independent\n"
                  "measurements of the same quantity", loc="left", pad=10)
    save(fig, "R7_normalisation", outdir)


# ---------------------------------------------------------------------------
# R8  which parameter actually explains the rate
# ---------------------------------------------------------------------------
def fig_variance(outdir):
    """Nested variance decomposition of log10(mass per revolution)."""
    rows = []
    for _, r in REP.iterrows():
        t = TRIALS[(TRIALS.run_id == r.run_id) & (TRIALS.block == "C")]
        for _, x in t.iterrows():
            mg = x.delta_g * 1000
            if mg <= 0.05:
                continue
            rows.append(dict(powder=r.display, tilt=x.tilt_deg,
                             y=np.log10(mg)))
    V = pd.DataFrame(rows)
    total = V.y.var(ddof=0) * len(V)

    def ss(cols):
        g = V.groupby(cols).y.transform("mean")
        return ((g - V.y.mean()) ** 2).sum()

    ss_p, ss_t, ss_pt = ss(["powder"]), ss(["tilt"]), ss(["powder", "tilt"])
    parts = {
        "powder identity": ss_p / total,
        "tilt angle": ss_t / total,
        "powder $\\times$ tilt\ninteraction": (ss_pt - ss_p - ss_t) / total,
        "residual\n(revolution-to-revolution)": (total - ss_pt) / total,
    }
    # speed, measured on a different axis, reported alongside as its own share
    sp = []
    for rid in REP_IDS:
        g = D[(D.run_id == rid) & (D.mg_s > 0)]
        if len(g) == 3:
            sp.append(np.log10(g.mg_rev.max() / g.mg_rev.min()))

    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(9.6, 3.9),
                                  gridspec_kw=dict(width_ratios=[1.4, 1]))
    keys = list(parts)
    vals = [parts[k] * 100 for k in keys]
    ax.barh(np.arange(len(keys)), vals, color=[SURROGATE, TILT_RAMP[90.0],
                                               ACCENT, MUTED], height=0.6)
    ax.set_yticks(np.arange(len(keys)))
    ax.set_yticklabels(keys, fontsize=8.5)
    ax.invert_yaxis()
    for i, v in enumerate(vals):
        ax.text(v + 1, i, f"{v:.0f}%", va="center", fontsize=9, color=INK)
    ax.set_xlim(0, 100)
    ax.set_xlabel("share of variance in log$_{10}$(mass per revolution)")
    ax.grid(axis="x", alpha=0.6); ax.set_axisbelow(True)
    ax.set_title("R8a  Which knob explains the rate\n"
                 "block C, all resolvable revolutions of every powder",
                 loc="left")

    spans = {
        "powder\n(at 45$^\\circ$, 30 RPM)": np.log10(
            reference_rate().query("not bounded").mg_rev.max()
            / reference_rate().query("not bounded").mg_rev.min()),
        "tilt\n(0$^\\circ$ to 90$^\\circ$)": np.log10(
            np.median([TRIALS[(TRIALS.run_id == r) & (TRIALS.block == "C")]
                       .groupby("tilt_deg").delta_g.mean().max()
                       / max(TRIALS[(TRIALS.run_id == r) & (TRIALS.block == "C")]
                             .groupby("tilt_deg").delta_g.mean().min(), 1e-6)
                       for r in REP_IDS
                       if TRIALS[(TRIALS.run_id == r) & (TRIALS.block == "C")]
                       .groupby("tilt_deg").delta_g.mean().min() > 5e-4])),
        "speed\n(15 to 90 RPM)": float(np.median(sp)),
    }
    ax2.barh(np.arange(len(spans)), list(spans.values()),
             color=[SURROGATE, TILT_RAMP[90.0], ACCENT], height=0.6)
    ax2.set_yticks(np.arange(len(spans)))
    ax2.set_yticklabels(list(spans), fontsize=8.5)
    ax2.invert_yaxis()
    for i, v in enumerate(spans.values()):
        ax2.text(v + 0.05, i, f"{10**v:.0f}$\\times$", va="center", fontsize=9,
                 color=INK)
    ax2.set_xlim(0, 3.6)
    ax2.set_xlabel("decades of dynamic range\n(median over powders; censored powders excluded)")
    ax2.grid(axis="x", alpha=0.6); ax2.set_axisbelow(True)
    ax2.set_title("R8b  ...and how much range each one covers", loc="left")
    save(fig, "R8_variance", outdir)


def write_tables(outdir):
    """Every derived rate quantity, one row per powder, for reuse in the paper."""
    L = reference_rate().set_index("powder_id")
    A = ALPHA.set_index("run_id")
    rows = []
    for _, r in REP.iterrows():
        t = TRIALS[TRIALS.run_id == r.run_id]
        c = t[t.block == "C"].groupby("tilt_deg").delta_g.agg(["mean", "std"]) * 1000
        e = t[t.block == "E"]
        d = D[D.run_id == r.run_id].set_index("rpm")
        floor = noise_floor(r.run_id)
        rows.append(dict(
            powder_id=r.powder_id, display=r.display, track=r.track,
            run_id=r.run_id, qc_valid=r.qc_valid, qc_verdict=r.qc_verdict,
            noise_floor_mg=round(floor, 2),
            mg_rev_tilt0=round(c["mean"].get(0.0, np.nan), 2),
            mg_rev_tilt45=round(c["mean"].get(45.0, np.nan), 2),
            mg_rev_tilt90=round(c["mean"].get(90.0, np.nan), 2),
            rsd_pct_tilt45=round(100 * c["std"].get(45.0, np.nan)
                                 / c["mean"].get(45.0, np.nan), 1)
            if c["mean"].get(45.0, 0) > 0 else np.nan,
            gravity_assist=round(c["mean"].get(90.0, np.nan)
                                 / c["mean"].get(0.0, np.nan), 2)
            if c["mean"].get(0.0, 0) > 0.5 else np.nan,
            censored=bool(L.loc[r.powder_id, "bounded"]),
            mg_s_ref_30rpm_tilt45=round(L.loc[r.powder_id, "mg_s"], 3),
            mg_s_15rpm=round(d.mg_s.get(15.0, np.nan), 1),
            mg_s_45rpm=round(d.mg_s.get(45.0, np.nan), 1),
            mg_s_90rpm=round(d.mg_s.get(90.0, np.nan), 1),
            mg_rev_15rpm=round(d.mg_rev.get(15.0, np.nan), 1),
            mg_rev_45rpm=round(d.mg_rev.get(45.0, np.nan), 1),
            mg_rev_90rpm=round(d.mg_rev.get(90.0, np.nan), 1),
            speed_exponent_alpha=round(A.alpha.get(r.run_id, np.nan), 3),
            speed_exponent_r2=round(A.r2.get(r.run_id, np.nan), 3),
            mg_per_tap_tilt0=round(e[(e.phase == "tap") & (e.tilt_deg == 0.0)]
                                   .delta_g.mean() * 1000, 2),
            mg_per_tap_tilt45=round(e[(e.phase == "tap") & (e.tilt_deg == 45.0)]
                                    .delta_g.mean() * 1000, 2),
            tap_resolvable=bool(max(
                e[(e.phase == "tap") & (e.tilt_deg == 0.0)].delta_g.mean() * 1000,
                e[(e.phase == "tap") & (e.tilt_deg == 45.0)].delta_g.mean() * 1000)
                > floor) and r.powder_id not in TAP_ARTIFACT,
            hold15s_tilt90_mg=round(
                t[(t.block == "B") & (t.tilt_deg == 90.0)].delta_g.mean() * 1000, 1),
        ))
    out = pd.DataFrame(rows).sort_values("mg_rev_tilt45", ascending=False)
    path = Path(outdir) / "rate_summary.csv"
    out.to_csv(path, index=False)
    print(f"  {path.name}  ({len(out)} powders)")


def main(outdir):
    Path(outdir).mkdir(parents=True, exist_ok=True)
    print("writing tables:")
    write_tables(outdir)
    print("writing figures:")
    fig_coverage(outdir)
    fig_ladder(outdir)
    fig_tilt(outdir)
    fig_speed(outdir)
    fig_instantaneous(outdir)
    fig_knobs(outdir)
    fig_normalisation(outdir)
    fig_variance(outdir)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else HERE / "out")
