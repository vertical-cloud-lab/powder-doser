#!/usr/bin/env python3
"""Measured-data figures for the powder-doser manuscript (Figs. 3-5).

Every panel is built from committed tidy CSVs:

    candidates/data/*.csv        round-1 test-protocol battery (A-G), issue #116,
                                 2026-08-04 -> 2026-08-21 (build_dataset.py)
    data/doses_all.csv           every closed-loop dose from both rounds
                                 (protocols G and H), built by
                                 data/build_closed_loop_doses.py (reads git)

Units. As built, a 20-tooth pinion on the stepper drives a 44-tooth gear on the
auger (2.2:1; PR #124 review), and a 2:1 gear pair drives the tilt plate from
the servos.  The dosing firmware (main_three_phase.py, used by every test-protocol
run) folds the 44:20 ratio into its steps-per-revolution, so every recorded
revolution, rpm and rotation angle is already an AUGER quantity: no rotation
conversion is needed.  Tilt is different: the test battery records a servo-horn
style "tilt" (0 / 45 / 90, where 90 was the "vertical" preset) and halves it at
the servo boundary, so the physical plate and tube angle is PLATE_PER_TILT x the
recorded tilt: 0, 22.5 and 45 deg.  Both conversions live here and nowhere else;
the raw CSVs keep the firmware's labels.  (The CAD file
cad/auger-geared/stepper-pinion.scad describes an earlier 16:48 pair and the
manuscript once said 2.25:1; the firmware ratio is confirmed by the one-slug-
per-revolution period in the protocol-D traces, 3.94 s at a commanded 15 rpm.)

Reader-facing rules (paper/meeting_2026-09-01/REVISION-SPEC.md, S04-S12):
no explanatory text inside the figures (captions carry it), powders that did not
convey are named but never given a numeric position, no jitter at n = 3, and the
surrogate / research-relevant colour split is kept in every panel.

Usage:  python3 make_data_figures.py      (writes PDFs here, PNG previews in preview/)
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D

HERE = Path(__file__).resolve().parent
ROUND1 = HERE / "candidates" / "data"
DOSES_CSV = HERE / "data" / "doses_all.csv"
PREVIEW = HERE / "preview"

# Recorded revolutions are auger revolutions (44:20 folded into the firmware).
AUGER_REV_PER_RECORDED_REV = 1.0
# Physical plate / tube angle per recorded battery "tilt" degree (2:1 servo gear).
PLATE_PER_TILT = 0.5


def plate(tilt: float) -> float:
    """Physical tube angle from horizontal for a recorded battery tilt."""
    return tilt * PLATE_PER_TILT

SINGLE_COL_IN = 8.3 / 2.54
DOUBLE_COL_IN = 17.1 / 2.54

# Categorical slots 1-2 of the validated reference palette, used for the one
# identity split every panel shares; status colours only for dose outcomes.
SURROGATE = "#2a78d6"
RESEARCH = "#eb6834"
GOOD, CRITICAL = "#0ca30c", "#d03b3b"
TILT_RAMP = {0.0: "#86b6ef", 45.0: "#2a78d6", 90.0: "#104281"}
INK, INK2, MUTED = "#0b0b0b", "#52514e", "#b8b6ae"

plt.rcParams.update({
    "font.size": 6.5,
    "font.family": "sans-serif",
    "axes.linewidth": 0.6,
    "axes.edgecolor": MUTED,
    "axes.labelcolor": INK,
    "axes.titlesize": 6.8,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "xtick.color": INK2,
    "ytick.color": INK2,
    "xtick.major.width": 0.5,
    "ytick.major.width": 0.5,
    "xtick.minor.width": 0.4,
    "ytick.minor.width": 0.4,
    "grid.color": "#e8e6e0",
    "grid.linewidth": 0.5,
    "legend.frameon": False,
    "legend.fontsize": 5.8,
    "lines.linewidth": 1.1,
    "savefig.dpi": 600,
})

# --- round-1 data -----------------------------------------------------------
RUNS = pd.read_csv(ROUND1 / "runs.csv")
FEED = pd.read_csv(ROUND1 / "feed.csv")
TRIALS = pd.read_csv(ROUND1 / "trials.csv")
POLLS = pd.read_csv(ROUND1 / "polls.csv")
DISPLAY = dict(zip(RUNS.powder_id, RUNS.display))
DISPLAY["salt"] = "NaCl"
DISPLAY["silicon-325"] = "Si (−325 mesh)"
DISPLAY["silicon-110-200"] = "Si (−110/+200 mesh)"
TRACK = dict(zip(RUNS.powder_id, RUNS.track))

# Powders that conveyed nothing resolvable at the 45 deg reference tilt. They
# are named in a "did not convey" band, never placed on a numeric axis.
DID_NOT_CONVEY = ["brown-rice-flour", "silicon-325", "fumed-silica"]


def representative_runs() -> pd.DataFrame:
    """One run per powder: QC-valid, preferring pooled runs, newest first."""
    ok = RUNS[RUNS.qc_valid | RUNS.powder_id.isin(DID_NOT_CONVEY)].copy()
    ok["rank"] = (~ok.poolable).astype(int)
    ok = ok.sort_values(["powder_id", "rank", "started_utc"],
                        ascending=[True, True, False])
    return ok.groupby("powder_id", as_index=False).first()


REP = representative_runs()
REP_RUN = dict(zip(REP.powder_id, REP.run_id))


def per_turn(run_id: str, tilt: float) -> tuple[float, float, float]:
    """Protocol C at one recorded tilt: mass per auger revolution.

    Each protocol-C trial is one full auger revolution.  Returns
    (mg per auger revolution, its standard error, revolution-to-revolution
    coefficient of variation in %).
    """
    row = FEED[(FEED.run_id == run_id) & (FEED.phase == "rotation")
               & (FEED.tilt_deg == tilt)]
    if row.empty:
        return np.nan, np.nan, np.nan
    r = row.iloc[0]
    k = 1000 * AUGER_REV_PER_RECORDED_REV
    return (float(r.mean_g) * k, float(r.sem_g) * k, float(r.rsd_pct))


def resolved(mean: float, se: float) -> bool:
    """A mean counts as a measurement only if it clears twice its own SE."""
    return np.isfinite(mean) and mean > 0 and se > 0 and mean > 2 * se


def colour(pid: str) -> str:
    return RESEARCH if TRACK[pid] == "research" else SURROGATE


def marker(pid: str) -> str:
    return "s" if TRACK[pid] == "research" else "o"


def track_handles(ms: float = 4.0) -> list[Line2D]:
    return [
        Line2D([], [], marker="o", ls="", ms=ms, color=SURROGATE,
               label="Food-safe surrogate"),
        Line2D([], [], marker="s", ls="", ms=ms, color=RESEARCH,
               label="Research-relevant"),
    ]


def panel_label(ax, letter: str, x: float = -0.02, y: float = 1.02) -> None:
    ax.text(x, y, f"({letter})", transform=ax.transAxes, fontsize=7.5,
            fontweight="bold", ha="right", va="bottom", color=INK)


def did_not_convey_band(ax, names: list[str], x: float, y0: float) -> None:
    """Struck-through names, no numeric position (spec S05)."""
    ax.text(x, y0, "did not convey", fontsize=5.6, color=INK2,
            style="italic", ha="left", va="center",
            transform=ax.get_yaxis_transform())


def save(fig, stem: str) -> None:
    fig.savefig(HERE / f"{stem}.pdf", bbox_inches="tight")
    PREVIEW.mkdir(exist_ok=True)
    fig.savefig(PREVIEW / f"{stem}.png", dpi=220, bbox_inches="tight",
                facecolor="white")
    plt.close(fig)
    print(f"wrote {stem}")


# ----------------------------------------------------------------------------
# Figure 3 - open-loop conveyance
# ----------------------------------------------------------------------------
def fig3_conveyance() -> None:
    fig = plt.figure(figsize=(DOUBLE_COL_IN, 2.55))
    gs = fig.add_gridspec(1, 3, width_ratios=[1.05, 1.0, 1.0], wspace=0.55)

    # (a) mass per auger revolution at the middle tilt (22.5 deg), ranked
    ax = fig.add_subplot(gs[0, 0])
    conv = []
    for pid in REP.powder_id:
        if pid in DID_NOT_CONVEY:
            continue
        mg, se, _ = per_turn(REP_RUN[pid], 45.0)
        conv.append((pid, mg, se))
    conv.sort(key=lambda r: r[1])
    n_dnc = len(DID_NOT_CONVEY)
    ypos = {}
    for i, (pid, mg, se) in enumerate(conv):
        y = i + n_dnc + 0.8
        ypos[pid] = y
        ax.plot([5, mg], [y, y], color=colour(pid), lw=0.6, alpha=0.35,
                zorder=1)
        ax.errorbar(mg, y, xerr=se, fmt=marker(pid), ms=4.2, color=colour(pid),
                    ecolor=INK2, elinewidth=0.6, capsize=1.5, zorder=3,
                    markeredgecolor="white", markeredgewidth=0.5)
        ax.text(mg * 1.28, y, f"{mg:.0f}", va="center", fontsize=5.4,
                color=INK2)
    # did-not-convey band below the measured powders
    ax.axhspan(-0.6, n_dnc - 0.2, color="#f0efec", zorder=0)
    labels, ticks = [], []
    for k, pid in enumerate(DID_NOT_CONVEY):
        ticks.append(k)
        labels.append(DISPLAY[pid])
    for pid, mg, _ in conv:
        ticks.append(ypos[pid])
        labels.append(DISPLAY[pid])
    ax.set_yticks(ticks)
    ax.set_yticklabels(labels, fontsize=5.8)
    for k, tl in enumerate(ax.get_yticklabels()):
        pid = DID_NOT_CONVEY[k] if k < n_dnc else None
        if pid:
            tl.set_color(INK2)
            tl.set_fontstyle("italic")
        else:
            tl.set_color(colour(conv[k - n_dnc][0]))
    ax.text(0.97, (n_dnc - 1) / 2, "did not convey\nat any tilt", fontsize=5.4,
            color=INK2, style="italic", ha="right", va="center",
            transform=ax.get_yaxis_transform())
    ax.set_xscale("log")
    ax.set_xlim(5, 1200)
    ax.set_ylim(-0.7, len(conv) + n_dnc + 0.3)
    ax.set_xlabel("Mass per auger revolution at 22.5° (mg, log scale)")
    ax.grid(axis="x", which="major", alpha=0.8)
    ax.legend(handles=track_handles(3.6), loc="lower right",
              bbox_to_anchor=(1.0, 0.24), fontsize=5.4, handletextpad=0.2)
    panel_label(ax, "a", x=-0.52)

    # (b) streamed balance traces during continuous rotation
    ax = fig.add_subplot(gs[0, 1])
    picks = ["alsi10mg", "salt", "calcium-lactate", "carboxymethyl-cellulose"]
    ends = []
    for pid in picks:
        rid = REP_RUN[pid]
        sub = POLLS[(POLLS.run_id == rid) & (POLLS.rpm == 15.0)]
        if sub.empty:
            continue
        t = (sub.t_ms - sub.t_ms.min()).to_numpy() / 1000
        m = (sub.grams - sub.grams.iloc[0]).to_numpy() * 1000
        ax.step(t, m, where="post", color=colour(pid), lw=1.0,
                ls="-" if pid in ("alsi10mg", "salt") else "--")
        ends.append((pid, t[-1], m[-1]))
    for pid, t_end, m_end in ends:
        ax.text(t_end + 0.4, m_end, DISPLAY[pid], fontsize=5.5,
                color=INK2, va="center")
    ax.set_xlim(0, 24)
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Mass delivered (mg)")
    ax.grid(alpha=0.8)
    panel_label(ax, "b", x=-0.2)

    # (c) operating map: throughput vs turn-to-turn scatter
    ax = fig.add_subplot(gs[0, 2])
    ax.axvspan(5, 60, color="#fdf3dc", zorder=0)
    ax.axvspan(60, 1200, color="#e6f4e6", zorder=0)
    pts = []
    for pid in REP.powder_id:
        if pid in DID_NOT_CONVEY:
            continue
        mg, se, cv = per_turn(REP_RUN[pid], 45.0)
        ax.scatter(mg, cv, s=16, marker=marker(pid), color=colour(pid),
                   edgecolor="white", linewidth=0.5, zorder=3)
        pts.append((pid, mg, cv))
    # Short names, placed by hand: the free-flowing cluster sits within a
    # factor of 1.6 in throughput, so its labels fan out to the right.
    short = {
        "alsi10mg": "AlSi10Mg", "silicon-110-200": "Si (coarse)",
        "sodium-sulfate": "Na$_2$SO$_4$", "calcium-lactate": "Ca lactate",
        "barium-chloride": "BaCl$_2$", "xanthan-gum": "Xanthan",
        "salt": "NaCl", "carboxymethyl-cellulose": "CMC",
        "white-rice-flour": "White rice flour", "sodium-alginate": "Na alginate",
    }
    spots = {
        "salt": (77, 23.5), "barium-chloride": (420, 21.0),
        "sodium-sulfate": (420, 17.2), "alsi10mg": (420, 13.4),
        "xanthan-gum": (420, 10.2), "silicon-110-200": (420, 6.6),
        "calcium-lactate": (420, 2.6),
    }
    for pid, mg, cv in pts:
        if pid in spots:
            tx, ty = spots[pid]
            ax.annotate(short[pid], (mg, cv), xytext=(tx, ty),
                        textcoords="data", fontsize=5.1, color=INK2,
                        ha="left" if tx > mg else "right", va="center",
                        arrowprops=dict(arrowstyle="-", lw=0.4, color=MUTED,
                                        shrinkA=0, shrinkB=2))
        else:
            dy = -7 if pid == "sodium-alginate" else 3
            ax.annotate(short[pid], (mg, cv), xytext=(3, dy),
                        textcoords="offset points", fontsize=5.1, color=INK2)
    ax.set_xscale("log")
    ax.set_xlim(5, 1200)
    ax.set_ylim(0, 45)
    ax.set_xlabel("Mass per auger revolution at 22.5° (mg, log scale)")
    ax.set_ylabel("Variation between revolutions (CV, %)")
    ax.text(17, 43, "slow", fontsize=5.4, color="#9a6a00", ha="center",
            va="top")
    ax.text(260, 43, "readily dosed", fontsize=5.4, color="#0a7a0a",
            ha="center", va="top")
    ax.grid(alpha=0.8)
    panel_label(ax, "c", x=-0.2)

    save(fig, "fig3_conveyance")


# ----------------------------------------------------------------------------
# Figure 4 - the actuation settings, one at a time
# ----------------------------------------------------------------------------
def best_tap(pid: str, tilt: float = 45.0):
    """Resolved mass per solenoid tap for a powder (protocol E).

    Searches every QC-valid run and keeps the newest one where the tap mean
    clears twice its standard error; a tap increment smaller than its own
    error bar is the bench moving, not the solenoid.
    """
    best = None
    for rid in RUNS[RUNS.qc_valid & (RUNS.powder_id == pid)].run_id:
        row = FEED[(FEED.run_id == rid) & (FEED.phase == "tap")
                   & (FEED.tilt_deg == tilt)]
        if row.empty:
            continue
        mg = float(row.mean_g.iloc[0]) * 1000
        se = float(row.sem_g.iloc[0] or 0) * 1000
        if pid != "fumed-silica" and resolved(mg, se):
            if best is None or rid > best[0]:
                best = (rid, mg, se)
    return best


def fig4_knobs() -> None:
    fig = plt.figure(figsize=(DOUBLE_COL_IN, 2.35))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.25, 1.0], wspace=0.42)

    # (a) tilt: mass per auger revolution at 0 / 45 / 90 deg
    ax = fig.add_subplot(gs[0, 0])
    ends = []
    for pid in REP.powder_id:
        if pid in DID_NOT_CONVEY:
            continue
        xs, ys = [], []
        for tilt in (0.0, 45.0, 90.0):
            mg, se, _ = per_turn(REP_RUN[pid], tilt)
            if resolved(mg, se):
                xs.append(plate(tilt))
                ys.append(mg)
        ax.plot(xs, ys, marker=marker(pid), ms=3.2, color=colour(pid),
                lw=0.9, alpha=0.9, markeredgecolor="white",
                markeredgewidth=0.4)
        ends.append((pid, ys[-1]))
    # The seven free-flowing powders end within a factor of two of one
    # another; one bracket names the group, the cohesive powders get their own
    # label at the end of their own line.
    ends_map = dict(ends)
    cohesive = ["white-rice-flour", "carboxymethyl-cellulose", "sodium-alginate"]
    top = [p for p, _ in ends if p not in cohesive]
    lo, hi = min(ends_map[p] for p in top), max(ends_map[p] for p in top)
    ax.plot([49, 50.5, 50.5, 49], [lo, lo, hi, hi], color=INK2, lw=0.6)
    ax.text(52, np.sqrt(lo * hi), "7 free-flowing\npowders",
            fontsize=5.2, color=INK2, va="center")
    last_x = {}
    for pid in cohesive:
        for tilt in (90.0, 45.0, 0.0):
            mg, se, _ = per_turn(REP_RUN[pid], tilt)
            if resolved(mg, se):
                last_x[pid] = (tilt, mg)
                break
    nudge = {"white-rice-flour": 1.0, "carboxymethyl-cellulose": 1.18,
             "sodium-alginate": 0.85}
    for pid in cohesive:
        tilt, mg = last_x[pid]
        ax.text(plate(tilt) + 2, mg * nudge[pid], DISPLAY[pid], fontsize=5.2,
                color=INK2, va="center")
    ax.set_yscale("log")
    ax.set_xticks([0, 22.5, 45])
    ax.set_xticklabels(["0°\n(horizontal)", "22.5°", "45°"])
    ax.set_xlim(-3, 75)
    ax.set_xlabel("Tube angle above horizontal")
    ax.set_ylabel("Mass per auger revolution (mg, log scale)")
    ax.grid(axis="y", which="major", alpha=0.8)
    ax.spines["bottom"].set_bounds(0, 45)
    panel_label(ax, "a", x=-0.2)

    # (b) mass per solenoid tap against mass per auger revolution
    ax = fig.add_subplot(gs[0, 1])
    items, unresolved = [], []
    for pid in REP.powder_id:
        if pid in DID_NOT_CONVEY:
            continue
        mg, _, _ = per_turn(REP_RUN[pid], 45.0)
        tap = best_tap(pid)
        if tap is None:
            unresolved.append(pid)
            continue
        _, tmg, tse = tap
        ax.errorbar(mg, tmg, yerr=tse, fmt=marker(pid), ms=3.8,
                    color=colour(pid), ecolor=INK2, elinewidth=0.6,
                    capsize=1.5, markeredgecolor="white",
                    markeredgewidth=0.4, zorder=3)
        items.append((pid, mg, tmg))
    offsets = {"calcium-lactate": (-4, 3), "barium-chloride": (4, -5),
               "xanthan-gum": (-4, 3), "salt": (-4, 3),
               "sodium-sulfate": (4, 2), "sodium-alginate": (4, 2)}
    for pid, mg, tmg in items:
        dx, dy = offsets.get(pid, (3, 3))
        ax.annotate(DISPLAY[pid], (mg, tmg), xytext=(dx, dy),
                    textcoords="offset points", fontsize=5.2, color=INK2,
                    ha="left" if dx >= 0 else "right")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(5, 500)
    ax.set_ylim(0.1, 60)
    ax.set_xlabel("Mass per auger revolution at 22.5° (mg)")
    ax.set_ylabel("Mass per solenoid tap (mg)")
    ax.grid(alpha=0.8, which="major")
    ax.legend(handles=track_handles(3.4), loc="lower right", fontsize=5.4,
              handletextpad=0.2)
    panel_label(ax, "b", x=-0.2)
    fig4_knobs.unresolved_taps = [DISPLAY[p] for p in unresolved]

    save(fig, "fig4_knobs")


# ----------------------------------------------------------------------------
# SI Figure S2 - the bench noise floor, run by run
# ----------------------------------------------------------------------------
def figS2_bench() -> None:
    """Protocol A spread for every round-1 run, in date order.

    Protocol A takes eight readings with nothing moving; their spread (max -
    min) is the floor every other number in that run is read against.
    """
    rows = []
    for _, r in RUNS.iterrows():
        base = TRIALS[(TRIALS.run_id == r.run_id) & (TRIALS.block == "A")]
        if base.empty:
            continue
        rows.append((r.run_id, r.powder_id,
                     (base.delta_g.max() - base.delta_g.min()) * 1000))
    df = pd.DataFrame(rows, columns=["run_id", "pid", "spread"])
    df = df.sort_values("run_id").reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(DOUBLE_COL_IN, 2.3))
    for i, r in df.iterrows():
        ax.bar(i, max(r.spread, 0.3), color=colour(r.pid), width=0.65,
               zorder=3)
    ax.axhline(5, color=CRITICAL, lw=0.8, ls="--", zorder=2)
    ax.text(len(df) - 0.4, 5.6, "±5 mg dose tolerance", fontsize=5.4,
            color=CRITICAL, ha="right", va="bottom")
    ax.set_xticks(range(len(df)))
    ax.set_xticklabels([f"{r.run_id[4:6]}-{r.run_id[6:8]}  {DISPLAY[r.pid]}"
                        for _, r in df.iterrows()], rotation=55, ha="right",
                       fontsize=5.4)
    ax.set_yscale("log")
    ax.set_ylim(0.2, 200)
    ax.set_ylabel("Spread of eight readings, nothing moving (mg)")
    ax.grid(axis="y", alpha=0.8)
    ax.legend(handles=[Line2D([], [], marker="s", ls="", ms=4, color=SURROGATE,
                              label="Food-safe surrogate"),
                       Line2D([], [], marker="s", ls="", ms=4, color=RESEARCH,
                              label="Research-relevant")],
              loc="upper left", fontsize=5.4)
    save(fig, "figS2_bench")


# ----------------------------------------------------------------------------
# SI Table S2 - closed-loop dose summary (LaTeX, generated)
# ----------------------------------------------------------------------------
def tableS2_doses() -> None:
    d = load_doses()
    rows = []
    for (pid, tgt), g in d.groupby(["powder_id", "target_mg"]):
        rounds = ",".join(sorted({str(x) for x in g["round"]}))
        rows.append(dict(
            powder=DISPLAY[pid], tgt=tgt, rounds=rounds, n=len(g),
            mean=g.error_mg.mean(), sd=g.error_mg.std(ddof=1) if len(g) > 1 else np.nan,
            within=int(g.passes.sum()), fw_ok=int((g.status == "ok").sum()),
            t_med=g.time_s.median(),
            order=-per_turn(REP_RUN[pid], 45.0)[0] if pid not in DID_NOT_CONVEY else 1))
    df = pd.DataFrame(rows).sort_values(["tgt", "order"])
    lines = [
        "% Generated by paper/figures/make_data_figures.py -- do not edit by hand.",
        r"\begin{longtable}{llcrrrccr}",
        r"\caption{Closed-loop dose summary for every valid dose (protocol G at 1~g; protocol H at 50 and 200~mg). Error is delivered minus requested mass. \emph{Within limit}: doses inside the acceptance limit ($\pm$10\% at 50~mg, $\pm$5\% at 200~mg and 1~g). \emph{Firmware ok}: doses the controller ended inside its own $\pm$5~mg stopping band. Round 1: August 2026, balance read on its stability flag; round 2: September 2026, bracketed readings. Per-dose records, including invalid doses and the reason each was excluded, are in \texttt{paper/figures/data/doses\_all.csv}.}\label{tbl:doses}\\",
        r"\toprule",
        r"Powder & Target & Round & $n$ & Mean error (mg) & SD (mg) & Within limit & Firmware ok & Median time (s) \\",
        r"\midrule\endfirsthead",
        r"\toprule",
        r"Powder & Target & Round & $n$ & Mean error (mg) & SD (mg) & Within limit & Firmware ok & Median time (s) \\",
        r"\midrule\endhead",
    ]
    for tgt, g in df.groupby("tgt", sort=True):
        for _, r in g.iterrows():
            t = f"{r.tgt:.0f} mg" if r.tgt < 1000 else "1 g"
            sd = "--" if not np.isfinite(r.sd) else f"{r.sd:.1f}"
            name = r.powder.replace("−", "$-$")
            lines.append(f"{name} & {t} & {r.rounds} & {r.n} & {r['mean']:+.1f} & {sd} & "
                         f"{r.within}/{r.n} & {r.fw_ok}/{r.n} & {r.t_med:.0f} \\\\")
        lines.append(r"\midrule")
    lines[-1] = r"\bottomrule"
    lines.append(r"\end{longtable}")
    out = HERE / "data" / "dose_summary_table.tex"
    out.write_text("\n".join(lines) + "\n")
    print("wrote", out.name)




# ----------------------------------------------------------------------------
# Figure 5 - closed-loop dosing (protocols G and H, both rounds)
# ----------------------------------------------------------------------------
def acceptance_limit_pct(target_mg: float) -> float:
    """Declared acceptance limit: +/-10 % below 100 mg, +/-5 % at or above."""
    return 10.0 if target_mg < 100 else 5.0


def load_doses() -> pd.DataFrame:
    d = pd.read_csv(DOSES_CSV)
    d = d[(d.dose_valid == True) & d.protocol.isin(["G", "H"])].copy()  # noqa: E712
    d["limit_pct"] = d.target_mg.map(acceptance_limit_pct)
    d["passes"] = d.error_pct.abs() <= d.limit_pct + 1e-9
    return d


def fig5_closed_loop() -> None:
    d = load_doses()
    targets = [50.0, 200.0, 1000.0]
    # Powders in order of mass per revolution (Fig. 3a), fastest at the top.
    rank = {}
    for pid in REP.powder_id:
        mg, _, _ = per_turn(REP_RUN[pid], 45.0)
        rank[pid] = -1 if pid in DID_NOT_CONVEY else mg
    order = sorted(set(d.powder_id), key=lambda p: rank.get(p, -1))
    ypos = {p: i for i, p in enumerate(order)}
    lim = 35.0

    fig = plt.figure(figsize=(DOUBLE_COL_IN, 2.6))
    gs = fig.add_gridspec(1, 4, width_ratios=[1, 1, 1, 1.05], wspace=0.14)
    axes = [fig.add_subplot(gs[0, k]) for k in range(3)]
    for k, (ax, tgt) in enumerate(zip(axes, targets)):
        sub = d[d.target_mg == tgt]
        band = acceptance_limit_pct(tgt)
        ax.axvspan(-band, band, color="#e6f4e6", zorder=0)
        ax.axvline(0, color=INK2, lw=0.5, zorder=1)
        for _, r in sub.iterrows():
            y = ypos[r.powder_id]
            x = float(np.clip(r.error_pct, -lim, lim))
            clipped = abs(r.error_pct) > lim
            mk = ("<" if r.error_pct < 0 else ">") if clipped else marker(r.powder_id)
            c = colour(r.powder_id)
            ax.scatter(x, y, s=12 if not clipped else 14, marker=mk,
                       facecolor=c if r.passes else "white", edgecolor=c,
                       linewidth=0.8, zorder=3, alpha=0.9)
        ax.set_yticks(range(len(order)))
        if k == 0:
            ax.set_yticklabels([DISPLAY[p] for p in order], fontsize=5.6)
            for tl, p in zip(ax.get_yticklabels(), order):
                tl.set_color(colour(p))
        else:
            ax.tick_params(labelleft=False)
        ax.set_ylim(-0.7, len(order) - 0.3)
        ax.set_xlim(-lim - 4, lim + 4)
        ax.set_xticks([-30, -15, 0, 15, 30])
        ax.set_title(f"{tgt:.0f} mg target" if tgt < 1000 else "1 g target",
                     fontsize=6.6, color=INK)
        ax.set_xlabel("Dose error (% of target)")
        ax.grid(axis="x", alpha=0.8)
        panel_label(ax, "abc"[k], x=-0.03 if k else -0.03)

    # (d) time per dose, by target mass
    ax = fig.add_subplot(gs[0, 3])
    for j, tgt in enumerate(targets):
        sub = d[(d.target_mg == tgt) & (d.time_s > 0)]
        for track, dx in (("surrogate", -0.14), ("research", 0.14)):
            s2 = sub[sub.powder_id.map(TRACK) == track]
            c = SURROGATE if track == "surrogate" else RESEARCH
            m = "o" if track == "surrogate" else "s"
            for _, r in s2.iterrows():
                ax.scatter(j + dx, r.time_s, s=10, marker=m,
                           facecolor=c if r.passes else "white", edgecolor=c,
                           linewidth=0.7, zorder=3, alpha=0.9)
        med = sub[sub.passes].time_s.median()
        if np.isfinite(med):
            ax.plot([j - 0.32, j + 0.32], [med, med], color=INK, lw=1.0,
                    zorder=4)
    ax.set_yscale("log")
    ax.set_xticks(range(3))
    ax.set_xticklabels(["50 mg", "200 mg", "1 g"])
    ax.set_xlim(-0.6, 2.6)
    ax.set_ylim(4, 2000)
    ax.set_xlabel("Target mass")
    ax.set_ylabel("Time to finish the dose (s)", labelpad=1)
    ax.yaxis.set_label_position("right")
    ax.yaxis.tick_right()
    ax.spines["right"].set_visible(True)
    ax.spines["left"].set_visible(False)
    ax.grid(axis="y", which="major", alpha=0.8)
    panel_label(ax, "d", x=-0.03)

    handles = [
        Line2D([], [], marker="o", ls="", ms=3.6, color=SURROGATE,
               label="Surrogate, within limit"),
        Line2D([], [], marker="o", ls="", ms=3.6, markerfacecolor="white",
               markeredgecolor=SURROGATE, label="Surrogate, outside limit"),
        Line2D([], [], marker="s", ls="", ms=3.6, color=RESEARCH,
               label="Research-relevant, within limit"),
        Line2D([], [], marker="s", ls="", ms=3.6, markerfacecolor="white",
               markeredgecolor=RESEARCH, label="Research-relevant, outside limit"),
        Line2D([], [], marker="<", ls="", ms=3.6, markerfacecolor="white",
               markeredgecolor=INK2, label="Off scale"),
        Line2D([], [], color=INK, lw=1.0, label="Median time, doses within limit"),
    ]
    fig.legend(handles=handles, loc="lower center", ncol=6,
               bbox_to_anchor=(0.5, -0.1), fontsize=5.2, handletextpad=0.25,
               columnspacing=1.0)
    save(fig, "fig5_closed_loop")
    fig5_closed_loop.doses = d


if __name__ == "__main__":
    fig3_conveyance()
    fig4_knobs()
    fig5_closed_loop()
    figS2_bench()
    tableS2_doses()
