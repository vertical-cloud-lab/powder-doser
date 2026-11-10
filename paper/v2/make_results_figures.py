#!/usr/bin/env python3
"""Results figures and tables for the v2 figure set (27 Oct brainstorm).

Reworks the measured-data figures of the current draft as decided on the
whiteboard and in the 27 Oct meeting (paper/meeting_2026-10-27/):

    Fig. 5  open-loop:  keep old 3a (mass per revolution) and 3b (mass-against-
            time traces); old 4b becomes a bar chart of mass per solenoid tap
            for ALL powders, with error bars.
    Fig. 6  closed-loop: old 5a-c; old 5d (time per dose) leaves this figure.
    SI      time per dose on its own (old 5d), and the revolution-to-revolution
            variation without the slow / fast shading (old 3c).
    Tables  old 4a (tilt) becomes a per-powder table; the powder table and the
            closed-loop summary are generated from the same data.

Nothing is re-measured.  All numbers come from the committed tidy CSVs through
the loaders in paper/figures/make_data_figures.py (round-1 protocols A-F,
issue #116, and every closed-loop dose from both rounds), so the unit
conventions stay in one place: recorded revolutions are auger revolutions, and
the physical tube angle is half the recorded battery tilt (0 / 22.5 / 45 deg).

Usage:  python3 make_results_figures.py   (PDFs in figures/, PNGs in preview/,
                                           LaTeX + Markdown tables in tables/)
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
from matplotlib.patches import Patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "figures"))
import make_data_figures as m  # noqa: E402  (loads the tidy CSVs)

FIGS, PREVIEW, TABLES = HERE / "figures", HERE / "preview", HERE / "tables"
for d in (FIGS, PREVIEW, TABLES):
    d.mkdir(exist_ok=True)

SURROGATE, RESEARCH, INK, INK2, MUTED = m.SURROGATE, m.RESEARCH, m.INK, m.INK2, m.MUTED
DNC = m.DID_NOT_CONVEY
REF_TILT = 45.0           # recorded battery tilt; physical tube angle 22.5 deg


def save(fig, stem: str) -> None:
    fig.savefig(FIGS / f"{stem}.pdf", bbox_inches="tight")
    fig.savefig(PREVIEW / f"{stem}.png", dpi=220, bbox_inches="tight",
                facecolor="white")
    plt.close(fig)
    print("wrote", stem)


# ----------------------------------------------------------------------------
# Shared per-powder numbers
# ----------------------------------------------------------------------------
def powder_order() -> tuple[list[str], list[str]]:
    """Conveying powders ranked by mass per revolution (slowest first), then
    the three that conveyed nothing (kept below, never given a value)."""
    conv = [(p, m.per_turn(m.REP_RUN[p], REF_TILT)[0])
            for p in m.REP.powder_id if p not in DNC]
    conv.sort(key=lambda r: r[1])
    return [p for p, _ in conv], list(DNC)


def tap_value(pid: str) -> dict:
    """Mass released by one solenoid tap at 22.5 deg, for any powder.

    Uses the newest QC-valid run in which the tap increment cleared twice its
    standard error (m.best_tap); otherwise the run used for the revolution
    numbers, flagged as not resolved.  Fumed silica's only run failed the
    screening checks and is flagged as such.
    """
    best = m.best_tap(pid, REF_TILT)
    if best is not None:
        rid, mg, se = best
        return dict(run=rid, mg=mg, se=se, resolved=True, screened=True)
    rid = m.REP_RUN[pid]
    row = m.FEED[(m.FEED.run_id == rid) & (m.FEED.phase == "tap")
                 & (m.FEED.tilt_deg == REF_TILT)]
    if row.empty:
        return dict(run=rid, mg=np.nan, se=np.nan, resolved=False, screened=False)
    r = row.iloc[0]
    qc = bool(m.RUNS.loc[m.RUNS.run_id == rid, "qc_valid"].iloc[0])
    return dict(run=rid, mg=float(r.mean_g) * 1000, se=float(r.sem_g or 0) * 1000,
                resolved=False, screened=qc)


SHORT = {
    "alsi10mg": "AlSi10Mg", "silicon-110-200": "Si (−110/+200 mesh)",
    "sodium-sulfate": "Sodium sulfate", "calcium-lactate": "Calcium lactate",
    "barium-chloride": "Barium chloride", "xanthan-gum": "Xanthan gum",
    "salt": "NaCl", "carboxymethyl-cellulose": "CMC",
    "white-rice-flour": "White rice flour", "sodium-alginate": "Sodium alginate",
    "silicon-325": "Si (−325 mesh)", "brown-rice-flour": "Brown rice flour",
    "fumed-silica": "Fumed silica",
}


# ----------------------------------------------------------------------------
# Fig. 5  open-loop: per revolution, per tap, and in time
# ----------------------------------------------------------------------------
def fig5_open_loop() -> None:
    conv, dnc = powder_order()
    rows = dnc + conv                       # bottom -> top
    y = {p: i for i, p in enumerate(rows)}
    n_dnc = len(dnc)

    fig = plt.figure(figsize=(m.DOUBLE_COL_IN, 2.75))
    gs = fig.add_gridspec(1, 3, width_ratios=[1.0, 0.82, 1.05], wspace=0.09)

    # (a) mass per auger revolution at 22.5 deg (old Fig. 3a)
    ax = fig.add_subplot(gs[0, 0])
    ax.axhspan(-0.6, n_dnc - 0.4, color="#f0efec", zorder=0)
    for p in conv:
        mg, se, _ = m.per_turn(m.REP_RUN[p], REF_TILT)
        ax.plot([5, mg], [y[p], y[p]], color=m.colour(p), lw=0.6, alpha=0.35,
                zorder=1)
        ax.errorbar(mg, y[p], xerr=se, fmt=m.marker(p), ms=4.0,
                    color=m.colour(p), ecolor=INK2, elinewidth=0.6, capsize=1.5,
                    markeredgecolor="white", markeredgewidth=0.5, zorder=3)
        ax.text(mg * 1.3, y[p], f"{mg:.0f}", va="center", fontsize=5.3,
                color=INK2)
    ax.text(0.96, (n_dnc - 1) / 2, "no measurable\ndelivery at\nany tilt",
            fontsize=5.2, color=INK2, style="italic", ha="right", va="center",
            transform=ax.get_yaxis_transform())
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([SHORT[p] for p in rows], fontsize=5.8)
    for tl, p in zip(ax.get_yticklabels(), rows):
        tl.set_color(INK2 if p in dnc else m.colour(p))
        if p in dnc:
            tl.set_fontstyle("italic")
    ax.set_xscale("log")
    ax.set_xlim(5, 1500)
    ax.set_ylim(-0.7, len(rows) - 0.3)
    ax.set_xlabel("Mass per auger revolution (mg, log scale)")
    ax.grid(axis="x", which="major", alpha=0.8)
    m.panel_label(ax, "a", x=-0.62)

    # (b) mass per solenoid tap, every powder (old Fig. 4b reworked)
    ax = fig.add_subplot(gs[0, 1], sharey=ax)
    ax.tick_params(labelleft=False)
    ax.axhspan(-0.6, n_dnc - 0.4, color="#f0efec", zorder=0)
    ax.axvline(0, color=INK2, lw=0.5, zorder=1)
    taps = {}
    for p in rows:
        t = tap_value(p)
        taps[p] = t
        c = m.colour(p)
        if not np.isfinite(t["mg"]):
            continue
        ax.barh(y[p], t["mg"], height=0.62, color=c if t["resolved"] else "white",
                edgecolor=c, linewidth=0.8, zorder=2,
                hatch="////" if not t["screened"] else None)
        ax.errorbar(t["mg"], y[p], xerr=t["se"], fmt="none", ecolor=INK2,
                    elinewidth=0.6, capsize=1.4, zorder=3)
        label = f"{t['mg']:.1f} ± {t['se']:.1f}"
        xr = max(t["mg"] + t["se"], 0) + 0.8
        ax.text(xr, y[p], label, va="center", ha="left", fontsize=5.0,
                color=INK if t["resolved"] else INK2)
    ax.set_xlim(-10, 34)
    ax.set_xticks([-10, 0, 10, 20, 30])
    ax.set_xlabel("Mass per solenoid tap (mg)")
    ax.grid(axis="x", alpha=0.8)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    m.panel_label(ax, "b", x=-0.02)
    tap_legend = [Patch(facecolor=INK2, edgecolor=INK2, label="Tap resolved (mean > 2 SE)"),
                  Patch(facecolor="white", edgecolor=INK2, label="Tap within balance noise"),
                  Patch(facecolor="white", edgecolor=INK2, hatch="////",
                        label="Run failed screening")]

    # (c) mass against time under continuous rotation (old Fig. 3b)
    ax = fig.add_subplot(gs[0, 2])
    picks = ["alsi10mg", "salt", "calcium-lactate", "carboxymethyl-cellulose"]
    for p in picks:
        sub = m.POLLS[(m.POLLS.run_id == m.REP_RUN[p]) & (m.POLLS.rpm == 15.0)]
        if sub.empty:
            continue
        t = (sub.t_ms - sub.t_ms.min()).to_numpy() / 1000
        g = (sub.grams - sub.grams.iloc[0]).to_numpy() * 1000
        ax.step(t, g, where="post", color=m.colour(p), lw=1.0,
                ls="-" if p in ("alsi10mg", "salt") else "--")
        ax.text(t[-1] + 0.4, g[-1], SHORT[p], fontsize=5.4, color=INK2,
                va="center")
    ax.set_xlim(0, 25)
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Mass delivered (mg)", labelpad=2)
    ax.grid(alpha=0.8)
    pos = ax.get_position()
    ax.set_position([pos.x0 + 0.075, pos.y0, pos.width - 0.075, pos.height])
    m.panel_label(ax, "c", x=-0.2)

    handles = m.track_handles(3.6) + tap_legend
    fig.legend(handles=handles, loc="lower center", ncol=5,
               bbox_to_anchor=(0.5, -0.08), fontsize=5.4, handletextpad=0.3,
               columnspacing=1.3, handlelength=1.3, handleheight=0.8)
    save(fig, "fig5_open_loop")
    fig5_open_loop.taps = taps


# ----------------------------------------------------------------------------
# Fig. 6  closed-loop dose error (old 5a-c, time per dose removed)
# ----------------------------------------------------------------------------
def fig6_closed_loop() -> None:
    d = m.load_doses()
    targets = [50.0, 200.0, 1000.0]
    rank = {p: (-1 if p in DNC else m.per_turn(m.REP_RUN[p], REF_TILT)[0])
            for p in m.REP.powder_id}
    order = sorted(set(d.powder_id), key=lambda p: rank.get(p, -1))
    ypos = {p: i for i, p in enumerate(order)}
    lim = 35.0

    fig = plt.figure(figsize=(m.DOUBLE_COL_IN, 2.45))
    gs = fig.add_gridspec(1, 3, wspace=0.08)
    for k, tgt in enumerate(targets):
        ax = fig.add_subplot(gs[0, k])
        sub = d[d.target_mg == tgt]
        band = m.acceptance_limit_pct(tgt)
        ax.axvspan(-band, band, color="#e6f4e6", zorder=0)
        ax.axvline(0, color=INK2, lw=0.5, zorder=1)
        for _, r in sub.iterrows():
            x = float(np.clip(r.error_pct, -lim, lim))
            clipped = abs(r.error_pct) > lim
            mk = ("<" if r.error_pct < 0 else ">") if clipped else m.marker(r.powder_id)
            c = m.colour(r.powder_id)
            ax.scatter(x, ypos[r.powder_id], s=13, marker=mk,
                       facecolor=c if r.passes else "white", edgecolor=c,
                       linewidth=0.8, zorder=3, alpha=0.9)
        ax.set_yticks(range(len(order)))
        if k == 0:
            ax.set_yticklabels([SHORT[p] for p in order], fontsize=5.8)
            for tl, p in zip(ax.get_yticklabels(), order):
                tl.set_color(m.colour(p))
        else:
            ax.tick_params(labelleft=False)
        n_pass, n = int(sub.passes.sum()), len(sub)
        ax.set_title(f"{'1 g' if tgt >= 1000 else f'{tgt:.0f} mg'} target\n"
                     f"{n_pass} of {n} within ±{band:.0f}%", fontsize=6.3,
                     color=INK, linespacing=1.3)
        ax.set_ylim(-0.7, len(order) - 0.3)
        ax.set_xlim(-lim - 4, lim + 4)
        ax.set_xticks([-30, -15, 0, 15, 30])
        ax.set_xlabel("Dose error (% of target)")
        ax.grid(axis="x", alpha=0.8)
        m.panel_label(ax, "abc"[k], x=-0.03)
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
               markeredgecolor=INK2, label="Off scale (beyond ±35%)"),
    ]
    fig.legend(handles=handles, loc="lower center", ncol=5,
               bbox_to_anchor=(0.5, -0.09), fontsize=5.3, handletextpad=0.25,
               columnspacing=1.1)
    save(fig, "fig6_closed_loop")
    fig6_closed_loop.doses = d


# ----------------------------------------------------------------------------
# SI: time per dose (old 5d) and revolution-to-revolution variation (old 3c)
# ----------------------------------------------------------------------------
def figS_dose_time() -> None:
    d = m.load_doses()
    fig, ax = plt.subplots(figsize=(m.SINGLE_COL_IN, 2.3))
    for j, tgt in enumerate([50.0, 200.0, 1000.0]):
        sub = d[(d.target_mg == tgt) & (d.time_s > 0)]
        for track, dx in (("surrogate", -0.15), ("research", 0.15)):
            s2 = sub[sub.powder_id.map(m.TRACK) == track]
            c = SURROGATE if track == "surrogate" else RESEARCH
            mk = "o" if track == "surrogate" else "s"
            jit = np.linspace(-0.07, 0.07, max(len(s2), 1))
            for (_, r), jj in zip(s2.sort_values("time_s").iterrows(), jit):
                ax.scatter(j + dx + jj, r.time_s, s=11, marker=mk,
                           facecolor=c if r.passes else "white", edgecolor=c,
                           linewidth=0.7, zorder=3, alpha=0.9)
        med = sub[sub.passes].time_s.median()
        if np.isfinite(med):
            ax.plot([j - 0.34, j + 0.34], [med, med], color=INK, lw=1.0, zorder=4)
            ax.text(j + 0.36, med, f"{med:.0f} s", fontsize=5.4, va="center",
                    color=INK)
    ax.set_yscale("log")
    ax.set_xticks(range(3))
    ax.set_xticklabels(["50 mg", "200 mg", "1 g"])
    ax.set_xlim(-0.6, 2.75)
    ax.set_ylim(4, 2000)
    ax.set_xlabel("Target mass")
    ax.set_ylabel("Time to finish the dose (s, log scale)")
    ax.grid(axis="y", which="major", alpha=0.8)
    handles = [
        Line2D([], [], marker="o", ls="", ms=3.4, color=SURROGATE,
               label="Surrogate, within limit"),
        Line2D([], [], marker="o", ls="", ms=3.4, markerfacecolor="white",
               markeredgecolor=SURROGATE, label="Surrogate, outside"),
        Line2D([], [], marker="s", ls="", ms=3.4, color=RESEARCH,
               label="Research, within limit"),
        Line2D([], [], marker="s", ls="", ms=3.4, markerfacecolor="white",
               markeredgecolor=RESEARCH, label="Research, outside"),
        Line2D([], [], color=INK, lw=1.0, label="Median, doses within limit"),
    ]
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, 1.25),
              ncol=3, fontsize=4.9, handletextpad=0.25, columnspacing=0.8)
    save(fig, "figS_dose_time")


def figS_rev_variation() -> None:
    fig, ax = plt.subplots(figsize=(m.SINGLE_COL_IN, 2.3))
    for p in m.REP.powder_id:
        if p in DNC:
            continue
        mg, se, cv = m.per_turn(m.REP_RUN[p], REF_TILT)
        ax.scatter(mg, cv, s=16, marker=m.marker(p), color=m.colour(p),
                   edgecolor="white", linewidth=0.5, zorder=3)
        ax.annotate(SHORT[p].replace(" (−110/+200 mesh)", " (coarse)"), (mg, cv),
                    xytext=(3, 2), textcoords="offset points", fontsize=4.9,
                    color=INK2)
    ax.set_xscale("log")
    ax.set_xlim(5, 1500)
    ax.set_ylim(0, 45)
    ax.set_xlabel("Mass per auger revolution at 22.5° (mg, log scale)")
    ax.set_ylabel("Variation between revolutions (CV, %)")
    ax.grid(alpha=0.8)
    ax.legend(handles=m.track_handles(3.4), loc="upper right", fontsize=5.2)
    save(fig, "figS_rev_variation")


# ----------------------------------------------------------------------------
# Tables
# ----------------------------------------------------------------------------
BEHAVIOUR = {  # observed behaviour, carried from main.tex Table 2 (#116, #157)
    "alsi10mg": "Fastest powder; fluid-like; overshoots small targets",
    "silicon-110-200": "Free-flowing",
    "sodium-sulfate": "Free-flowing; overshoots small targets",
    "calcium-lactate": "Free-flowing; largest tap increment",
    "barium-chloride": "Absorbed moisture and caked in the tube in round 2",
    "xanthan-gum": "Flows under rotation; can clog after bursts",
    "salt": "Free-flowing baseline (control)",
    "carboxymethyl-cellulose": "Slow; charges electrostatically",
    "white-rice-flour": "Slow and pulsing; most variable between revolutions",
    "sodium-alginate": "Slowest powder that moved",
    "silicon-325": "No delivery at 0 or 22.5°; one pulse at 45°",
    "brown-rice-flour": "No delivery at any tilt",
    "fumed-silica": "No delivery; very light and fluffy",
}
LONG = dict(SHORT)
LONG.update({"alsi10mg": "AlSi10Mg (gas-atomized)",
             "salt": "Sodium chloride (NaCl)",
             "carboxymethyl-cellulose": "Carboxymethyl cellulose (CMC)",
             "silicon-110-200": "Silicon, −110/+200 mesh",
             "silicon-325": "Silicon, −325 mesh"})


def _tex(s: str) -> str:
    return (s.replace("−", "$-$").replace("±", r"$\pm$").replace("°", r"$^\circ$")
            .replace("%", r"\%").replace("&", r"\&"))


def _write(stem: str, md: list[str], tex: list[str]) -> None:
    (TABLES / f"{stem}.md").write_text("\n".join(md) + "\n")
    (TABLES / f"{stem}.tex").write_text("\n".join(tex) + "\n")
    print("wrote", stem)


def table_powders() -> None:
    """Main-text powder table, every number generated from the data."""
    d = m.load_doses()
    conv, dnc = powder_order()
    rows = list(reversed(conv)) + dnc
    md = ["| Powder | Group | mg per rev. (22.5°) | 50 mg | 200 mg | 1 g | Observed behaviour |",
          "|---|---|---:|:---:|:---:|:---:|---|"]
    tex = [
        "% Generated by paper/v2/make_results_figures.py -- do not edit by hand.",
        r"\begin{table*}[t]", r"\small",
        r"  \caption{\ The 13 powders. Mass per auger revolution: protocol~C mean at 22.5$^\circ$ "
        r"(Fig.~\ref{fgr:v2openloop}a). Closed-loop columns: valid doses that finished within the "
        r"acceptance limit ($\pm$10\% at 50~mg, $\pm$5\% at 200~mg and 1~g) out of the number run "
        r"(Fig.~\ref{fgr:v2closedloop}); a dash means not run. The silicon grades are named by sieve size: "
        r"$-$325 mesh passes a 44~$\mu$m sieve, and $-$110/+200 mesh lies between about 75 and 150~$\mu$m.}",
        r"  \label{tbl:v2powders}",
        r"  \begin{tabular*}{\textwidth}{@{\extracolsep{\fill}}llrccc p{5.4cm}}",
        r"    \hline",
        r"    Powder & Group & mg per rev. & 50~mg & 200~mg & 1~g & Observed behaviour \\",
        r"    \hline",
    ]
    for p in rows:
        grp = "Research" if m.TRACK[p] == "research" else "Surrogate"
        mg = "none" if p in dnc else f"{m.per_turn(m.REP_RUN[p], REF_TILT)[0]:.0f}"
        cells = []
        for tgt in (50.0, 200.0, 1000.0):
            s = d[(d.powder_id == p) & (d.target_mg == tgt)]
            cells.append("--" if s.empty else f"{int(s.passes.sum())}/{len(s)}")
        md.append(f"| {LONG[p]} | {grp} | {mg} | {cells[0]} | {cells[1]} | {cells[2]} | {BEHAVIOUR[p]} |")
        tex.append(f"    {_tex(LONG[p])} & {grp} & {mg} & {cells[0]} & {cells[1]} & {cells[2]} & "
                   f"{_tex(BEHAVIOUR[p])} \\\\")
    tex += [r"    \hline", r"  \end{tabular*}", r"\end{table*}"]
    _write("table_powders", md, tex)


def table_open_loop() -> None:
    """Old Fig. 4a as a table: delivery per revolution at three tilts, its
    variation, and the tap increment, for every powder (SI)."""
    conv, dnc = powder_order()
    rows = list(reversed(conv)) + dnc
    taps = getattr(fig5_open_loop, "taps", None) or {p: tap_value(p) for p in rows}

    def cell(mg, se):
        if not np.isfinite(mg):
            return "--"
        if not m.resolved(mg, se):
            return "n.r."
        return f"{mg:.0f} ± {se:.0f}" if mg >= 10 else f"{mg:.1f} ± {se:.1f}"

    md = ["| Powder | Group | 0° | 22.5° | 45° | CV at 22.5° (%) | Per tap at 22.5° (mg) |",
          "|---|---|---:|---:|---:|---:|---:|"]
    tex = [
        "% Generated by paper/v2/make_results_figures.py -- do not edit by hand.",
        r"\begin{table*}[t]", r"\small",
        r"  \caption{\ Open-loop delivery for every powder (protocols C and E, round 1, one run per powder). "
        r"Mass per auger revolution (mg, mean $\pm$ standard error of six revolutions) with the tube horizontal "
        r"(0$^\circ$) and tilted to 22.5$^\circ$ and 45$^\circ$; the revolution-to-revolution coefficient of "
        r"variation (CV) at 22.5$^\circ$; and the mass released by one solenoid tap at 22.5$^\circ$ "
        r"(mean $\pm$ standard error of eight taps). n.r.: not resolved, meaning the mean did not exceed twice its "
        r"standard error. Tap values in italics are within the balance noise of their run; fumed silica's only run "
        r"failed screening. Replaces the tilt panel of the earlier draft (Fig.~4a).}",
        r"  \label{tbl:v2openloop}",
        r"  \begin{tabular*}{\textwidth}{@{\extracolsep{\fill}}llrrrrr}",
        r"    \hline",
        r"    Powder & Group & 0$^\circ$ & 22.5$^\circ$ & 45$^\circ$ & CV at 22.5$^\circ$ (\%) & Per tap (mg) \\",
        r"    \hline",
    ]
    for p in rows:
        grp = "Research" if m.TRACK[p] == "research" else "Surrogate"
        rid = m.REP_RUN[p]
        vals = [m.per_turn(rid, t) for t in (0.0, 45.0, 90.0)]
        cs = [cell(v[0], v[1]) for v in vals]
        cv = vals[1][2]
        cv_s = "--" if (p in dnc or not np.isfinite(cv)) else f"{cv:.0f}"
        t = taps[p]
        if np.isfinite(t["mg"]):
            ts = f"{t['mg']:.1f} ± {t['se']:.1f}"
            ts_md = ts if t["resolved"] else f"*{ts}*"
            ts_tex = _tex(ts) if t["resolved"] else r"\textit{" + _tex(ts) + "}"
            if not t["screened"]:
                ts_md += " †"
                ts_tex += r"$^\dagger$"
        else:
            ts_md = ts_tex = "--"
        md.append(f"| {LONG[p]} | {grp} | {cs[0]} | {cs[1]} | {cs[2]} | {cv_s} | {ts_md} |")
        tex.append(f"    {_tex(LONG[p])} & {grp} & {_tex(cs[0])} & {_tex(cs[1])} & {_tex(cs[2])} & "
                   f"{cv_s} & {ts_tex} \\\\")
    tex += [r"    \hline", r"  \end{tabular*}", r"\end{table*}"]
    md.append("")
    md.append("n.r.: not resolved (mean not more than twice its standard error). Italic: tap "
              "increment within the balance noise of its run. †: fumed silica's only run failed screening.")
    _write("table_open_loop", md, tex)


def table_closed_loop() -> None:
    """Compact closed-loop summary by target: passes, mean |error|, median time."""
    d = m.load_doses()
    md = ["| Target | Limit | Valid doses | Within limit | Powders | Median time, doses within limit (s) | Overshoots among misses |",
          "|---|---|---:|---:|---:|---:|---:|"]
    tex = [
        "% Generated by paper/v2/make_results_figures.py -- do not edit by hand.",
        r"\begin{table}[h]", r"\small",
        r"  \caption{\ Closed-loop doses by target mass (protocols G and H, both rounds). Times are given here "
        r"rather than as a figure panel; SI Fig.~\siref{fgr:v2dosetime} shows every dose.}",
        r"  \label{tbl:v2closedloop}",
        r"  \begin{tabular*}{0.48\textwidth}{@{\extracolsep{\fill}}lrrrr}",
        r"    \hline",
        r"    Target & Limit & Within limit & Median time (s) & Misses that overshot \\",
        r"    \hline",
    ]
    for tgt in (50.0, 200.0, 1000.0):
        s = d[d.target_mg == tgt]
        lim = m.acceptance_limit_pct(tgt)
        npass, n = int(s.passes.sum()), len(s)
        med = s[s.passes].time_s.median()
        miss = s[~s.passes]
        over = int((miss.error_pct > 0).sum())
        name = "1 g" if tgt >= 1000 else f"{tgt:.0f} mg"
        md.append(f"| {name} | ±{lim:.0f}% | {n} | {npass} | {s.powder_id.nunique()} | {med:.0f} | {over} of {len(miss)} |")
        tex.append(f"    {name.replace(' ', '~')} & $\\pm${lim:.0f}\\% & {npass} of {n} & {med:.0f} & {over} of {len(miss)} \\\\")
    tex += [r"    \hline", r"  \end{tabular*}", r"\end{table}"]
    _write("table_closed_loop", md, tex)


if __name__ == "__main__":
    fig5_open_loop()
    fig6_closed_loop()
    figS_dose_time()
    figS_rev_variation()
    table_powders()
    table_open_loop()
    table_closed_loop()
