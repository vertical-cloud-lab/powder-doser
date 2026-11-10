#!/usr/bin/env python3
"""Closed-loop dose traces: per-dose phase times and the SI trace figure.

Every closed-loop dose logs one balance reading per controller step to the
Pico's serial port.  This script reads those raw serial logs straight out of
git (``git show REF:data/battery/<run>/raw_serial_<powder>.log``, the same
REF as build_closed_loop_doses.py), so the working tree is never touched,
splits them into doses, and matches each dose to its row in doses_all.csv by
(run, block, dose number).

Outputs
-------
  data/dose_phase_summary.csv       one row per VALID dose (doses_all.csv,
                                    dose_valid), with the time spent in each
                                    phase and the final increment
  figS_dose_traces.pdf              SI figure: mass against time, 50 mg /
  preview/figS_dose_traces.png      200 mg / 1 g, one fast and one slow powder

Log lines used (firmware main_three_phase.py, unchanged across both rounds)::

    [dose] three-phase dose to 0.0500 g; taring scale
    [dose] tared: baseline +0.2 mg (subtracted), drift ..., read noise ...
    === phase 1/3 'bulk' skipped (...)
    === phase 2/3 'fine' start: 0.0498 g to go, exit at 0.0250 g to go; ...
    [phase 1 bulk] poll 3 (unstable): mass X / T g (... this poll), elapsed S s
    [phase 1 bulk] settled: mass X / T g (... while settling), elapsed S s
    [phase 2 fine] cycle 2: mass X / T g (..., +G g this cycle), elapsed S s
    [phase 3 tap] lip empty; nudging auger 5.0 deg (nudge 1/10)
    === phase 3/3 'tap' end (46 cycles): mass X / T g (... this phase), elapsed S s
    DOSE,n,target,delivered,error,status,elapsed,auger_rev,taps,cycles,t_ms[,block]

Conventions (read these before quoting the numbers)
---------------------------------------------------
* Clock.  ``elapsed`` is the controller's own clock, MicroPython integer
  seconds since the dose started; the dose starts BEFORE the tare.  Every time
  here therefore has 1 s resolution.
* Phase time = elapsed at the end of the phase minus elapsed at the end of the
  previous phase that ran; the first phase that ran is measured from 0 s, so
  it includes the tare and the first reading.  A phase that was skipped, or
  never reached because the dose ended earlier, counts 0 s.  The phase times
  of a dose add up to its DOSE-row time (asserted; the DOSE row can be 1 s
  later).  ``first_reading_s`` is the elapsed time of the first logged
  reading; for a dose that starts in the bulk phase (readings every 250 ms)
  it is close to the tare overhead (1-3 s in round 1, 4-14 s, median 6 s,
  in round 2).
* Final increment = mass added by the last actuation before the controller
  stopped: the last fine cycle (one 45 deg auger step) or tap cycle (two taps,
  plus a 5 deg nudge if one immediately preceded it) as logged, reading after
  minus reading before; or, if the dose ended in the bulk phase, the whole
  continuous spin (phase gain), because that spin is one actuation.  For doses
  that stalled or ran out of cycles or time the final increment is, by
  construction, near zero.  Every reading is one balance read, so on noisy
  runs the increment carries the reading noise.
* Reading noise.  ``tap_noise_mg`` is a robust SD of one reading during the
  tap phase (1.4826 x MAD of the cycle-to-cycle changes, final cycle
  excluded, / sqrt 2; true tap gains are 0-2 mg on most powders), and
  ``tap_last5_mean_mg`` the mean of the five tap readings before the final
  one; both need at least eight tap cycles.  A final reading far above that
  mean, on a run with a large ``tap_noise_mg``, means the dose stopped on a
  high reading rather than on a settled mass.
* Bulk entry at small targets.  For protocol H the bulk hand-over threshold
  equals the target, so a dose whose first reading is a fraction of a
  milligram below zero enters the bulk phase for one 250 ms poll.  The spin is
  real (the log shows the start, the poll, and the halt), but when it starts
  and stops within one tick of the integer-second clock the firmware records
  0.00 auger revolutions.  ``bulk_spin`` flags these doses.
* Groups: free-flowing = the seven powders above 140 mg per revolution
  (Fig. 3a); slow = CMC, white rice flour and sodium alginate; no conveyance =
  fine silicon and brown rice flour.
* Figure.  Rows: AlSi10Mg (run 20260910T194447Z, protocols G and H in one run)
  and white rice flour (round-2 run 20260904T190011Z at 50 and 200 mg; its
  1 g doses exist only in round-1 run 20260804T211422Z).  In each set of three
  doses the thick line is the one with the median time; the other two are
  thin.  Shading and the strip above each panel show the phases of the thick
  dose.  Markers as in Fig. 5: filled within the acceptance limit, open
  outside; squares research-relevant, circles food-safe surrogate.

Usage::

    python3 build_dose_traces.py [--repo PATH] [--ref REF]
"""

from __future__ import annotations

import argparse
import re
import statistics
import subprocess
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

HERE = Path(__file__).resolve().parent            # paper/figures/data
FIGDIR = HERE.parent                              # paper/figures
PREVIEW = FIGDIR / "preview"
DEFAULT_REPO = str(HERE.parents[2])
DEFAULT_REF = "origin/claude/issue-116-20260915-1622"
DOSES_CSV = HERE / "doses_all.csv"
OUT_CSV = HERE / "dose_phase_summary.csv"
STEM = "figS_dose_traces"

PHASES = ("bulk", "fine", "tap")

FREE_FLOWING = {"alsi10mg", "silicon-110-200", "sodium-sulfate", "calcium-lactate",
                "barium-chloride", "xanthan-gum", "salt"}
SLOW = {"carboxymethyl-cellulose", "white-rice-flour", "sodium-alginate"}
RESEARCH = {"alsi10mg", "silicon-110-200", "silicon-325", "sodium-sulfate",
            "barium-chloride", "fumed-silica"}


def flow_group(pid: str) -> str:
    if pid in FREE_FLOWING:
        return "free-flowing"
    if pid in SLOW:
        return "slow"
    return "no conveyance"


def acceptance_limit_mg(target_mg: float) -> float:
    """+/-10 % below 100 mg, +/-5 % at or above (as in make_data_figures.py)."""
    return target_mg * (0.10 if target_mg < 100 else 0.05)


# ----------------------------------------------------------------------------
# Log parsing
# ----------------------------------------------------------------------------
NUM = r"[+-]?[0-9.]+"
RE_START = re.compile(r"^\[dose\] three-phase dose to (" + NUM + r") g")
RE_TARE_WARN = re.compile(r"^\[dose\] WARNING the tare did not take")
RE_SKIP = re.compile(r"^=== phase (\d)/3 '(\w+)' skipped")
RE_PSTART = re.compile(r"^=== phase (\d)/3 '(\w+)' start: (" + NUM + r") g to go")
RE_PEND = re.compile(r"^=== phase (\d)/3 '(\w+)' end \((\d+) cycles\): mass (" + NUM +
                     r") / (" + NUM + r") g \((" + NUM + r") g to go, (" + NUM +
                     r") g this phase\), elapsed (" + NUM + r") s")
RE_READ = re.compile(r"^\[phase (\d) (\w+)\] (poll (\d+)(?: \(unstable\))?|settled|cycle (\d+)):"
                     r" mass (" + NUM + r") / (" + NUM + r") g \((" + NUM + r") g to go, ("
                     + NUM + r") g (?:this poll|while settling|this cycle)\), elapsed ("
                     + NUM + r") s")
RE_NUDGE = re.compile(r"^\[phase (\d) (\w+)\] lip empty; nudging auger (" + NUM +
                      r") deg \(nudge (\d+)/(\d+)\)")
RE_HALT = re.compile(r"^\[phase (\d) (\w+)\] (no powder flow|cycle budget|dose timeout)")


def git(repo: str, *args: str) -> str:
    out = subprocess.run(["git", "-C", repo, *args], check=True, capture_output=True)
    return out.stdout.decode("utf-8", "replace")


def raw_log(repo: str, ref: str, run_id: str) -> str | None:
    base = f"data/battery/{run_id}"
    try:
        names = git(repo, "ls-tree", "--name-only", f"{ref}:{base}").split()
    except subprocess.CalledProcessError:
        return None
    raw = [n for n in names if n.startswith("raw_serial_") and n.endswith(".log")]
    return git(repo, "show", f"{ref}:{base}/{raw[0]}") if raw else None


def parse_log(text: str) -> list[dict]:
    """Split a raw serial log into doses, in log order.

    Each dose is a dict with the DOSE-row fields (block, n, status, ...),
    ``events`` (every logged reading: t, mass_mg, phase, kind, gain_mg),
    ``phases`` (per phase: start_remaining_mg, end_s, cycles, gain_mg,
    end_mass_mg), the skipped phases, nudges, and ``complete`` (False when
    the log stops before the DOSE row, i.e. the serial link failed).
    """
    doses, cur = [], None

    def close(d, complete):
        d["complete"] = complete
        doses.append(d)

    for raw in text.splitlines():
        line = raw.strip("\r").strip()
        m = RE_START.match(line)
        if m:
            if cur is not None:                     # previous dose never closed
                close(cur, False)
            cur = dict(log_target_g=float(m.group(1)), events=[], phases={},
                       skipped=[], order=[], nudges=[], tare_warning=False,
                       halt_reason=None)
            continue
        if cur is None:
            continue
        if RE_TARE_WARN.match(line):
            cur["tare_warning"] = True
        elif (m := RE_SKIP.match(line)):
            cur["skipped"].append(m.group(2))
        elif (m := RE_PSTART.match(line)):
            ph = m.group(2)
            cur["order"].append(ph)
            cur["phases"][ph] = dict(start_remaining_mg=1000 * float(m.group(3)))
        elif (m := RE_READ.match(line)):
            ph = m.group(2)
            what = m.group(3)
            kind = "settled" if what == "settled" else what.split()[0]
            cur["events"].append(dict(
                phase=ph, kind=kind, t=float(m.group(10)),
                mass_mg=1000 * float(m.group(6)), gain_mg=1000 * float(m.group(9)),
                nudged=False))
        elif (m := RE_NUDGE.match(line)):
            cur["nudges"].append(dict(phase=m.group(2), after_event=len(cur["events"]) - 1,
                                      t=cur["events"][-1]["t"] if cur["events"] else None))
        elif (m := RE_HALT.match(line)):
            cur["halt_reason"] = m.group(3)
        elif (m := RE_PEND.match(line)):
            ph = m.group(2)
            cur["phases"].setdefault(ph, {})
            cur["phases"][ph].update(cycles=int(m.group(3)), end_mass_mg=1000 * float(m.group(4)),
                                     gain_mg=1000 * float(m.group(7)), end_s=float(m.group(8)))
        elif line.startswith("DOSE,"):
            f = line.split(",")
            try:
                cur.update(n=int(f[1]), target_g=float(f[2]), delivered_g=float(f[3]),
                           status=f[5], elapsed_s=float(f[6]), auger_rev=float(f[7]),
                           taps=int(f[8]), phase_cycles=f[9],
                           block=f[11] if len(f) > 11 and f[11] else "G")
            except (IndexError, ValueError):
                continue                            # garbled row: treat as lost
            close(cur, True)
            cur = None
    if cur is not None:
        close(cur, False)
    return doses


def nudge_flags(dose: dict) -> None:
    """Mark each tap cycle that immediately follows a nudge."""
    after = {nd["after_event"] for nd in dose["nudges"]}
    for i, ev in enumerate(dose["events"]):
        ev["nudged"] = ev["kind"] == "cycle" and (i - 1) in after


def summarise_dose(dose: dict) -> dict:
    """Phase times, final increment, and step sizes for one parsed dose."""
    nudge_flags(dose)
    ev = dose["events"]
    ph = dose["phases"]
    order = [p for p in dose["order"] if "end_s" in ph.get(p, {})]
    out = dict(phases_run="+".join(dose["order"]) or "none",
               first_reading_s=ev[0]["t"] if ev else np.nan,
               n_nudges=len(dose["nudges"]),
               tare_warning=dose["tare_warning"], halt_reason=dose["halt_reason"] or "",
               trace_complete=dose["complete"])
    prev = 0.0
    for p in PHASES:
        info = ph.get(p, {})
        if p in order:
            out[f"{p}_s"] = info["end_s"] - prev
            out[f"{p}_cycles"] = info["cycles"]
            out[f"{p}_gain_mg"] = round(info["gain_mg"], 1)
            prev = info["end_s"]
        elif p in dose["order"]:
            # Started but never logged its end: the serial link was lost.
            out[f"{p}_s"] = out[f"{p}_cycles"] = out[f"{p}_gain_mg"] = np.nan
        else:
            # Skipped, or never reached because the dose ended earlier.
            out[f"{p}_s"], out[f"{p}_cycles"], out[f"{p}_gain_mg"] = 0.0, 0, 0.0
    out["phase_sum_s"] = prev if dose["complete"] else np.nan
    out["bulk_spin"] = "bulk" in dose["order"]
    fine = [e["gain_mg"] for e in ev if e["phase"] == "fine" and e["kind"] == "cycle"]
    out["fine_step_median_mg"] = round(statistics.median(fine), 1) if fine else np.nan
    out["fine_step_max_mg"] = round(max(fine), 1) if fine else np.nan
    taps = [e for e in ev if e["phase"] == "tap" and e["kind"] == "cycle"]
    gains = np.array([e["gain_mg"] for e in taps])
    out["tap_step_median_mg"] = round(float(np.median(gains)), 2) if len(taps) else np.nan
    # Reading scatter during the tap phase, where true gains are small: a
    # robust SD of the cycle-to-cycle changes (final cycle excluded), /sqrt 2
    # for one reading.  Only with at least eight tap cycles.
    if len(taps) >= 8:
        g = gains[:-1]
        mad = float(np.median(np.abs(g - np.median(g))))
        out["tap_noise_mg"] = round(1.4826 * mad / np.sqrt(2), 2)
        out["tap_last5_mean_mg"] = round(float(np.mean([e["mass_mg"] for e in taps[-6:-1]])), 1)
    else:
        out["tap_noise_mg"] = out["tap_last5_mean_mg"] = np.nan
    if not dose["complete"] or not order:
        out.update(final_phase="", final_step="trace lost (serial link failed)"
                   if not dose["complete"] else "", final_increment_mg=np.nan,
                   mass_before_final_mg=np.nan, final_mass_mg=np.nan)
        return out
    last = order[-1]
    out["final_phase"] = last
    final_mass = ph[last]["end_mass_mg"]
    if last == "bulk":
        inc = ph["bulk"]["gain_mg"]
        step = "bulk spin"
    else:
        cyc = [e for e in ev if e["phase"] == last and e["kind"] == "cycle"]
        inc = cyc[-1]["gain_mg"]
        step = "45 deg rotation" if last == "fine" else (
            "nudge + 2 taps" if cyc[-1]["nudged"] else "2 taps")
    out.update(final_step=step, final_increment_mg=round(inc, 1),
               mass_before_final_mg=round(final_mass - inc, 1),
               final_mass_mg=round(final_mass, 1))
    return out


def load_all(repo: str, ref: str, doses: pd.DataFrame):
    """Parse every run's log; return {(run, block, n): parsed dose}."""
    parsed, missing = {}, []
    for run_id in sorted(set(doses.run_id)):
        if "(#148)" in run_id:                     # comment-only demo, no log
            continue
        text = raw_log(repo, ref, run_id)
        if text is None:
            missing.append(run_id)
            continue
        for d in parse_log(text):
            if "n" not in d:                        # dose lost to serial corruption
                d.update(block="H" if d["log_target_g"] < 1.0 else "G")
            parsed.setdefault(run_id, []).append(d)
    keyed = {}
    for run_id, lst in parsed.items():
        rows = doses[doses.run_id == run_id]
        for d in lst:
            if "n" in d:
                keyed[(run_id, d["block"], d["n"])] = d
        # A dose whose DOSE row was lost: match it to the reconstructed row.
        lost = [d for d in lst if "n" not in d]
        recon = rows[rows.reconstructed == True]  # noqa: E712
        for d, (_, r) in zip(lost, recon.iterrows()):
            keyed[(run_id, r.block, int(r.dose_n))] = d
    return keyed, missing


# ----------------------------------------------------------------------------
# Per-dose table
# ----------------------------------------------------------------------------
def build_summary(doses: pd.DataFrame, parsed: dict) -> pd.DataFrame:
    rows = []
    for _, r in doses[doses.dose_valid == True].iterrows():  # noqa: E712
        key = (r.run_id, r.block, int(r.dose_n))
        d = parsed.get(key)
        base = dict(run_id=r.run_id, round=r["round"], block=r.block, dose_n=int(r.dose_n),
                    powder_id=r.powder_id, display=r.display, flow_group=flow_group(r.powder_id),
                    target_mg=r.target_mg, delivered_mg=r.delivered_mg, error_mg=r.error_mg,
                    limit_mg=acceptance_limit_mg(r.target_mg),
                    within_limit=abs(r.error_mg) <= acceptance_limit_mg(r.target_mg) + 1e-9,
                    status=r.status, time_s=r.time_s, read_path=r.read_path,
                    source="serial log" if d is not None else "DOSE row only (no serial log)")
        if d is None:
            # No serial log (2026-08-05 brown rice flour): the DOSE row's own
            # cycle counts say every cycle was bulk, so all time is bulk time.
            cyc = {k: (int(v) if pd.notna(v) else 0) for k, v in
                   (("bulk", r.bulk_cycles), ("fine", r.fine_cycles), ("tap", r.tap_cycles))}
            only = [q for q in PHASES if cyc[q] > 0]
            base.update(phases_run="+".join(only), trace_complete=False,
                        bulk_spin=cyc["bulk"] > 0)
            for p in PHASES:
                base[f"{p}_cycles"] = cyc[p]
                base[f"{p}_s"] = r.time_s if only == [p] else (0.0 if cyc[p] == 0 else np.nan)
            base["phase_sum_s"] = r.time_s if len(only) == 1 else np.nan
            rows.append(base)
            continue
        s = summarise_dose(d)
        if d["complete"]:
            # The trace and the DOSE row must agree (0.1 mg, and +/-1 s).
            assert abs(s["final_mass_mg"] - r.delivered_mg) < 0.15, (key, s["final_mass_mg"])
            assert abs(d["elapsed_s"] - r.time_s) < 0.01, key
            assert 0 <= d["elapsed_s"] - s["phase_sum_s"] <= 1.0, (key, s["phase_sum_s"])
        base.update(s)
        rows.append(base)
    cols = ["run_id", "round", "block", "dose_n", "powder_id", "display", "flow_group",
            "target_mg", "delivered_mg", "error_mg", "limit_mg", "within_limit", "status",
            "time_s", "phases_run", "first_reading_s", "bulk_s", "fine_s", "tap_s",
            "phase_sum_s", "bulk_cycles", "fine_cycles", "tap_cycles", "bulk_gain_mg",
            "fine_gain_mg", "tap_gain_mg", "n_nudges", "final_phase", "final_step",
            "final_increment_mg", "mass_before_final_mg", "final_mass_mg",
            "fine_step_median_mg", "fine_step_max_mg", "tap_step_median_mg", "tap_noise_mg",
            "tap_last5_mean_mg", "bulk_spin", "tare_warning", "halt_reason", "read_path",
            "trace_complete", "source"]
    df = pd.DataFrame(rows)
    return df[[c for c in cols if c in df.columns]]


def print_medians(df: pd.DataFrame) -> None:
    """Medians quoted in the SI text (doses with a complete serial trace)."""
    ok = df[df.trace_complete == True]  # noqa: E712
    print(f"\nvalid doses: {len(df)}; with a complete serial trace: {len(ok)}")
    pd.set_option("display.width", 200)
    for group in (None, "free-flowing", "slow"):
        sub = ok if group is None else ok[ok.flow_group == group]
        rows = []
        for tgt, g in sub.groupby("target_mg"):
            t = g.time_s
            rows.append(dict(
                target=tgt, n=len(g), time=t.median(),
                bulk=g.bulk_s.median(), fine=g.fine_s.median(), tap=g.tap_s.median(),
                tap_share=(g.tap_s / g.time_s).median(),
                final_inc=g.final_increment_mg.median(),
                final_inc_okover=g[g.status.isin(["ok", "overshoot"])].final_increment_mg.median(),
                fine_step=g.fine_step_median_mg.median(),
                n_bulk_spin=int((g.bulk_spin & (g.target_mg < 1000)).sum())))
        print(f"\n-- medians, {group or 'all valid doses'} --")
        print(pd.DataFrame(rows).round(1).to_string(index=False))


# ----------------------------------------------------------------------------
# Figure
# ----------------------------------------------------------------------------
DOUBLE_COL_IN = 17.1 / 2.54
SURROGATE_C = "#2a78d6"
RESEARCH_C = "#eb6834"
INK, INK2, MUTED = "#0b0b0b", "#52514e", "#b8b6ae"
BAND = "#e6f4e6"
# Ordinal neutral shading: coarse (bulk) darkest, finest (tap) lightest.
PHASE_SHADE = {"bulk": "#dcdad2", "fine": "#ebeae4", "tap": "#f6f5f1"}

plt.rcParams.update({
    "font.size": 6.5, "font.family": "sans-serif", "axes.linewidth": 0.6,
    "axes.edgecolor": MUTED, "axes.labelcolor": INK, "axes.titlesize": 6.8,
    "axes.spines.top": False, "axes.spines.right": False, "xtick.color": INK2,
    "ytick.color": INK2, "xtick.major.width": 0.5, "ytick.major.width": 0.5,
    "grid.color": "#e8e6e0", "grid.linewidth": 0.5, "legend.frameon": False,
    "legend.fontsize": 5.8, "lines.linewidth": 1.1, "savefig.dpi": 600,
})

# (run, block) per row x target; within each set the highlighted dose is the
# replicate with the median dose time (see choose_highlight).
ROWS = [
    ("alsi10mg", "AlSi10Mg", {50.0: ("20260910T194447Z_alsi10mg", "H"),
                              200.0: ("20260910T194447Z_alsi10mg", "H"),
                              1000.0: ("20260910T194447Z_alsi10mg", "G")}),
    ("white-rice-flour", "White rice flour",
     {50.0: ("20260904T190011Z_white-rice-flour", "H"),
      200.0: ("20260904T190011Z_white-rice-flour", "H"),
      1000.0: ("20260804T211422Z_white-rice-flour", "G")}),
]
TARGETS = (50.0, 200.0, 1000.0)


def trace_xy(d: dict) -> tuple[np.ndarray, np.ndarray]:
    """(t, mass) from the tare (0 s, 0 mg) through every logged reading."""
    t = [0.0] + [e["t"] for e in d["events"]]
    m = [0.0] + [e["mass_mg"] for e in d["events"]]
    return np.asarray(t), np.asarray(m)


def choose_highlight(reps: pd.DataFrame) -> int:
    """Dose number of the replicate with the median time (lower median)."""
    s = reps.sort_values(["time_s", "dose_n"]).reset_index(drop=True)
    return int(s.dose_n.iloc[(len(s) - 1) // 2])


def outcome_text(r) -> str:
    label = {"cycle-budget": "cycle budget"}.get(r.status, r.status)
    err = r.error_mg
    e = (f"{err:+.1f}" if abs(err) < 100 else f"{err:+.0f}").replace("-", "\u2212")
    return f"{e} mg, {label}"


YLIM = {50.0: (-25, 108), 200.0: (-35, 232), 1000.0: (-40, 1080)}
# Phase strip above each panel: same ordinal greys, one step darker so the
# strip reads on the white page.
STRIP_SHADE = {"bulk": "#c9c7bf", "fine": "#dcdad3", "tap": "#ebeae5"}


def place_outcome(ax, traces, text: str) -> None:
    """Outcome of the highlighted dose in the lower right, or the upper right
    if a trace runs through the lower-right corner."""
    x0, x1 = ax.get_xlim()
    y0, y1 = ax.get_ylim()
    busy = any(((t >= x0 + 0.55 * (x1 - x0)) & (m <= y0 + 0.2 * (y1 - y0))).any()
               for _, _, t, m in traces)
    ax.text(0.98, 0.9 if busy else 0.04, text, transform=ax.transAxes, ha="right",
            va="top" if busy else "bottom", fontsize=5.8, color=INK2, zorder=7)


def phase_strip(ax, dose: dict, xmax: float) -> None:
    """Thin labelled bar above the axes: the phases of the highlighted dose."""
    strip = ax.inset_axes([0, 1.02, 1, 0.075], sharex=ax)
    strip.set_ylim(0, 1)
    strip.axis("off")
    prev = 0.0
    for p in dose["order"]:
        end = dose["phases"][p]["end_s"]
        strip.axvspan(prev, end, color=STRIP_SHADE[p], lw=0)
        if prev > 0:
            strip.axvline(prev, color="white", lw=0.8)
        if (end - prev) / xmax >= 0.1:
            strip.text((prev + end) / 2, 0.5, p, ha="center", va="center",
                       fontsize=5.3, color=INK)
        prev = end


def fig_traces(doses: pd.DataFrame, parsed: dict) -> list[dict]:
    fig, axes = plt.subplots(2, 3, figsize=(DOUBLE_COL_IN, 4.55),
                             gridspec_kw=dict(hspace=0.62, wspace=0.25, left=0.075, right=0.97))
    picked = []
    for i, (pid, name, sets) in enumerate(ROWS):
        colour = RESEARCH_C if pid in RESEARCH else SURROGATE_C
        mk = "s" if pid in RESEARCH else "o"
        for j, tgt in enumerate(TARGETS):
            ax = axes[i, j]
            run_id, block = sets[tgt]
            reps = doses[(doses.run_id == run_id) & (doses.block == block)
                         & (doses.target_mg == tgt) & (doses.dose_valid == True)]  # noqa: E712
            hi = choose_highlight(reps)
            lim = acceptance_limit_mg(tgt)
            traces = []
            for _, r in reps.sort_values("dose_n").iterrows():
                d = parsed[(run_id, block, int(r.dose_n))]
                traces.append((r, d, *trace_xy(d)))
            xmax = max(t[-1] for _, _, t, _ in traces) * 1.04
            r_hi, d_hi = [(r, d) for r, d, _, _ in traces if int(r.dose_n) == hi][0]
            # Phases of the highlighted dose: shading and boundaries.
            prev = 0.0
            for p in d_hi["order"]:
                end = d_hi["phases"][p]["end_s"]
                ax.axvspan(prev, end, color=PHASE_SHADE[p], lw=0, zorder=0)
                if prev > 0:
                    ax.axvline(prev, color=MUTED, lw=0.5, zorder=1)
                prev = end
            ax.axhspan(tgt - lim, tgt + lim, color=BAND, alpha=0.85, lw=0, zorder=2)
            ax.axhline(tgt, color=INK2, lw=0.5, ls=(0, (3, 2)), zorder=2)
            for r, d, t, m in traces:
                main = int(r.dose_n) == hi
                ax.step(t, m, where="post", color=colour, lw=1.05 if main else 0.55,
                        alpha=1.0 if main else 0.4, zorder=4 if main else 3)
                inside = abs(r.error_mg) <= lim + 1e-9
                ax.plot(t[-1], m[-1], marker=mk, ms=3.8 if main else 2.8,
                        mfc=colour if inside else "white", mec=colour,
                        mew=0.8 if main else 0.6, alpha=1.0 if main else 0.6,
                        zorder=5, ls="")
            picked.append(dict(row=name, target_mg=tgt, run_id=run_id, block=block,
                               dose_n=hi, status=r_hi.status, error_mg=r_hi.error_mg,
                               time_s=r_hi.time_s, phases="+".join(d_hi["order"]),
                               others=[(int(r.dose_n), r.time_s, r.error_mg, r.status)
                                       for r, _, _, _ in traces if int(r.dose_n) != hi]))
            ax.set_xlim(0, xmax)
            ax.set_ylim(*YLIM[tgt])
            ax.grid(alpha=0.8)
            ax.set_axisbelow(True)
            phase_strip(ax, d_hi, xmax)
            place_outcome(ax, traces, outcome_text(r_hi))
            tlabel = f"{tgt:.0f} mg" if tgt < 1000 else "1 g"
            ax.set_title(f"{name}, {tlabel}", fontsize=6.6, color=INK, loc="left", pad=11)
            if j == 0:
                ax.set_ylabel("Mass delivered (mg)")
            if i == 1:
                ax.set_xlabel("Time since the dose started (s)")
            ax.text(-0.03, 1.115, f"({'abcdef'[3 * i + j]})", transform=ax.transAxes,
                    fontsize=7.5, fontweight="bold", ha="right", va="bottom", color=INK)
    blank = Line2D([], [], ls="", label=" ")
    shade = [Patch(facecolor=STRIP_SHADE[p], edgecolor="none", label=f"{p.capitalize()} phase")
             for p in PHASES]
    handles = [shade[0], Line2D([], [], color=INK2, lw=1.05, label="Dose with the median time"),
               shade[1], Line2D([], [], color=INK2, lw=0.55, alpha=0.5,
                                label="Other doses of the set"),
               shade[2], Line2D([], [], marker="o", ls="", ms=3.4, color=INK2,
                                label="Within limit"),
               Patch(facecolor=BAND, edgecolor="none", label="Acceptance limit"),
               Line2D([], [], marker="o", ls="", ms=3.4, mfc="white", mec=INK2,
                      label="Outside limit"),
               Line2D([], [], color=INK2, lw=0.5, ls=(0, (3, 2)), label="Target"), blank]
    fig.legend(handles=handles, loc="lower center", ncol=5, bbox_to_anchor=(0.5, -0.07),
               fontsize=5.6, handlelength=1.7, columnspacing=1.6, handletextpad=0.45)
    fig.savefig(FIGDIR / f"{STEM}.pdf", bbox_inches="tight")
    PREVIEW.mkdir(exist_ok=True)
    fig.savefig(PREVIEW / f"{STEM}.png", dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"wrote {STEM}")
    return picked


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--repo", default=DEFAULT_REPO)
    ap.add_argument("--ref", default=DEFAULT_REF)
    a = ap.parse_args()
    doses = pd.read_csv(DOSES_CSV)
    parsed, missing = load_all(a.repo, a.ref, doses)
    print("runs without a serial log:", ", ".join(missing) or "none")
    summary = build_summary(doses, parsed)
    summary.to_csv(OUT_CSV, index=False, float_format="%.6g")
    print(f"wrote {OUT_CSV.name} ({len(summary)} valid doses)")
    print_medians(summary)
    for p in fig_traces(doses, parsed):
        print("plotted:", p)


if __name__ == "__main__":
    main()
