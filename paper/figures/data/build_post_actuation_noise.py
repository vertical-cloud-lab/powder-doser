#!/usr/bin/env python3
"""Balance noise right after the doser moves, per run and per small dose.

The closed-loop controller decides when to stop from a reading taken 1.5 s
after each actuation.  The idle noise floor (protocol A, SI Fig. "bench
noise") says nothing about those readings, so this script measures the noise
in them directly, compares it with readings taken at rest in the same runs,
and asks whether the pass/fail call of every valid 50 mg and 200 mg dose is
larger than that noise.

Inputs (read only; the working tree is never modified outside OUT)
  git REF:data/battery/<run>/raw_serial_<powder>.log   per-cycle controller lines
  data/doses_all.csv, data/runs_all.csv                 tidy dose and run tables
                                                        (build_closed_loop_doses.py)
  candidates/data/trials.csv, candidates/data/runs.csv  round-1 protocols A, B, E;
                                                        display names and tracks

Outputs
  data/post_actuation_noise.csv          one row per run directory (37)
  data/post_actuation_noise_doses.csv    one row per valid 50 mg and 200 mg dose (58)
  data/post_actuation_noise_table.tex    SI table: how many calls survive the noise
  figS_noise_after_actuation.pdf         SI figure (PNG preview in preview/)

Metric
------
Every controller cycle logs ``mass X / T g (... g to go, +/-D g this cycle)``,
where D is the change between two settled readings, each taken 1.5 s after an
actuation.  In the tap phase the tube is horizontal and each cycle is two 60 ms
solenoid taps, so real powder adds at most a few mg per cycle and the cup can
never lose mass.  The post-actuation noise of a run is

    noise_mg = 1.4826 x median(|D - median(D)|)     over all tap-phase cycles

i.e. the robust standard deviation of the per-cycle change.  The median
absolute deviation ignores the occasional real slug of powder, and on quiet
runs the statistic is an upper bound because it also contains the
tap-to-tap variation in delivered mass.  It is computed on changes between
two readings, which is also what a dose is (final reading minus tare reading).
At least MIN_N = 8 cycles are required (the size of a protocol-E set).  Two
runs never reached the tap phase because nothing was delivered (fine silicon
and caked barium chloride, both 10 Sep); for them the fine-phase cycles, each
a 45 deg auger step with no powder arriving, are used instead.  Values below
the balance's 0.1 mg readability are reported as computed and floored at
0.1 mg wherever they are used as a noise scale.

At rest.  The same statistic is applied to the first reading of each dose
minus its tare reading, two readings with nothing moving in between (taken
3-6 s after the previous dose ended, since unattended runs re-tare without
emptying the cup).  Round-2 doses that logged no ``[dose] tared:`` line
(3 Sep morning, before the baseline fix) are skipped because their tare was
refused and the first reading is not a change.

Pass/fail robustness (per valid dose)
  limit_mg   5 mg at 50 mg (+/-10 %), 10 mg at 200 mg (+/-5 %): the declared
             acceptance limits of make_data_figures.acceptance_limit_pct
  margin_mg  limit_mg - |error_mg|; positive for doses within the limit
  call       robust          |margin| > 2 x noise
             marginal        noise < |margin| <= 2 x noise
             not resolvable  |margin| <= noise
  with noise = the run's noise_mg (floored at 0.1 mg).  Sensitivity columns
  repeat the call with noise / sqrt(2) (a noise-free tare reading), with the
  dose's own tap-phase scatter (doses with >= MIN_N tap cycles), and with the
  RMS of the run's negative tap-phase changes (changes that can only be noise).

Independent check.  When a tare is refused, the firmware keeps the pan
reading as a baseline.  If two consecutive doses both did this, the
difference of their baselines is the mass added between the two tare
readings, so  next_tare_check_mg = (next baseline - this baseline) - delivered
compares each dose's final reading with a quiet reading a few seconds later.

Usage:  python3 build_post_actuation_noise.py [--repo PATH] [--ref REF]
"""

from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

HERE = Path(__file__).resolve().parent
FIG_DIR = HERE.parent
DEFAULT_REPO = str(HERE.parents[2])
DEFAULT_REF = "origin/claude/issue-116-20260915-1622"

MIN_N = 8               # changes needed for a robust SD (one protocol-E set)
READABILITY_MG = 0.1    # A&D HR-100A
MAD_TO_SD = 1.4826
STEM = "figS_noise_after_actuation"

# --- house style, mirrored from make_data_figures.py -------------------------
SURROGATE, RESEARCH = "#2a78d6", "#eb6834"
CRITICAL = "#d03b3b"
INK, INK2, MUTED = "#0b0b0b", "#52514e", "#b8b6ae"
ZONE1, ZONE2 = "#d6d4cd", "#ebe9e4"     # within 1x / 2x noise of a limit
BAND_EDGE = "#8ccc8c"                   # edge of the green acceptance band
SI_TEXT_IN = 16.6 / 2.54
plt.rcParams.update({
    "font.size": 6.5, "font.family": "sans-serif",
    "axes.linewidth": 0.6, "axes.edgecolor": MUTED, "axes.labelcolor": INK,
    "axes.titlesize": 6.8, "axes.spines.top": False, "axes.spines.right": False,
    "xtick.color": INK2, "ytick.color": INK2,
    "xtick.major.width": 0.5, "ytick.major.width": 0.5,
    "xtick.minor.width": 0.4, "ytick.minor.width": 0.4,
    "grid.color": "#e8e6e0", "grid.linewidth": 0.5,
    "legend.frameon": False, "legend.fontsize": 5.8,
    "lines.linewidth": 1.1, "savefig.dpi": 600,
})

# --- raw-log grammar (main_three_phase.py, battery_version 1-3) -------------
DOSE_START = re.compile(r"^\[dose\] three-phase dose to ([0-9.]+) g")
TARED = re.compile(r"^\[dose\] tared: baseline ([+-]?[0-9.]+) mg \(subtracted\), "
                   r"drift ([+-]?[0-9.]+) mg/min, read noise ([0-9.]+) mg")
TARE_WARN = re.compile(r"^\[dose\] WARNING the tare did not take -- pan reads ([+-]?[0-9.]+) g")
PHASE_LINE = re.compile(r"^=== phase (\d)/3 '(\w+)' (start|skipped)[:\s]+\(?([+-]?[0-9.]+) g to go")
CYCLE = re.compile(r"^\[phase (\d) (\w+)\] cycle (\d+): mass ([+-]?[0-9.]+) / ([0-9.]+) g "
                   r"\(([+-]?[0-9.]+) g to go, ([+-]?[0-9.]+) g this cycle\), elapsed ([0-9.]+) s")
SETTLED = re.compile(r"^\[phase 1 bulk\] settled: mass ([+-]?[0-9.]+) / .*while settling\), "
                     r"elapsed ([0-9.]+) s")
NUDGE = re.compile(r"^\[phase (\d) (\w+)\] lip empty; nudging auger")


def git(repo: str, *args: str) -> str:
    out = subprocess.run(["git", "-C", repo, *args], check=True, capture_output=True)
    return out.stdout.decode("utf-8", "replace")


def robust_sd(x) -> float:
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    if len(x) < 2:
        return np.nan
    return float(MAD_TO_SD * np.median(np.abs(x - np.median(x))))


def rms_negative(x) -> float:
    """RMS of the negative changes, counting non-negative ones as zero."""
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    if len(x) == 0:
        return np.nan
    return float(np.sqrt(np.mean(np.minimum(x, 0.0) ** 2)))


def floored(v: float) -> float:
    return max(v, READABILITY_MG) if np.isfinite(v) else np.nan


# ----------------------------------------------------------------------------
# Raw serial log -> one dict per dose with its cycle list
# ----------------------------------------------------------------------------
def parse_log(text: str) -> list[dict]:
    doses, cur = [], None
    for raw in text.splitlines():
        line = raw.strip("\r")
        m = DOSE_START.match(line)
        if m:
            if cur is not None:              # previous dose never got a DOSE row
                doses.append(cur)
            cur = dict(target_g=float(m.group(1)), tared=False, tare_warning=False,
                       baseline_mg=None, tare_drift=None, tare_noise=None,
                       first_reading_mg=None, cycles=[], block=None, n=None,
                       last_phase=None, _first=False, _nudge=False)
            continue
        if cur is None:
            continue
        if TARE_WARN.match(line):
            cur["tare_warning"] = True
        elif (m := TARED.match(line)):
            cur.update(tared=True, baseline_mg=float(m.group(1)),
                       tare_drift=float(m.group(2)), tare_noise=float(m.group(3)))
        elif (m := PHASE_LINE.match(line)):
            if cur["first_reading_mg"] is None and m.group(1) == "1":
                # "X g to go" before any actuation = target - first reading
                cur["first_reading_mg"] = round(1000 * (cur["target_g"] - float(m.group(4))), 1)
            if m.group(3) == "start":
                cur["_first"] = True
        elif (m := CYCLE.match(line)):
            cur["cycles"].append(dict(
                phase=m.group(2), cycle=int(m.group(3)),
                mass_mg=round(1000 * float(m.group(4)), 1),
                change_mg=round(1000 * float(m.group(7)), 1),
                elapsed_s=float(m.group(8)),
                first_of_phase=cur["_first"], after_nudge=cur["_nudge"]))
            cur["_first"] = cur["_nudge"] = False
            cur["last_phase"] = m.group(2)
        elif SETTLED.match(line):
            cur["last_phase"] = "bulk"
        elif NUDGE.match(line):
            cur["_nudge"] = True
        elif line.startswith("DOSE,"):
            f = line.split(",")
            cur["n"] = int(f[1])
            cur["block"] = f[11] if len(f) > 11 and f[11] else "G"
            doses.append(cur)
            cur = None
    if cur is not None:
        doses.append(cur)                    # e.g. calcium lactate H5 (serial lost)
    return doses


def assign_unclosed(doses: list[dict]) -> None:
    """Give a dose whose DOSE row was lost the next (block, n) in sequence."""
    for i, d in enumerate(doses):
        if d["n"] is None and i > 0 and doses[i - 1]["n"] is not None:
            d["block"], d["n"] = doses[i - 1]["block"], doses[i - 1]["n"] + 1


# ----------------------------------------------------------------------------
def build(repo: str, ref: str):
    runs = pd.read_csv(HERE / "runs_all.csv")
    alld = pd.read_csv(HERE / "doses_all.csv")
    r1runs = pd.read_csv(FIG_DIR / "candidates" / "data" / "runs.csv")
    trials = pd.read_csv(FIG_DIR / "candidates" / "data" / "trials.csv")
    track = dict(zip(r1runs.powder_id, r1runs.track))
    track["salt-demo"] = "surrogate"

    cyc_rows, dose_ctx = [], {}
    for run_id in runs.run_id:
        base = f"data/battery/{run_id}"
        files = [f for f in git(repo, "ls-tree", "--name-only", f"{ref}:{base}").splitlines()
                 if f.startswith("raw_serial_") and f.endswith(".log")]
        if not files:
            continue
        doses = parse_log(git(repo, "show", f"{ref}:{base}/{files[0]}"))
        assign_unclosed(doses)
        for k, d in enumerate(doses):
            d["next"] = doses[k + 1] if k + 1 < len(doses) else None
            dose_ctx[(run_id, d["block"], d["n"])] = d
            for c in d["cycles"]:
                cyc_rows.append(dict(run_id=run_id, block=d["block"], dose_n=d["n"],
                                     target_mg=1000 * d["target_g"], **c))
    cyc = pd.DataFrame(cyc_rows)

    # ---- per run ------------------------------------------------------------
    out = []
    for _, r in runs.iterrows():
        rid = r.run_id
        row = dict(run_id=rid, round=r["round"], location=r.location, read_path=r.read_path,
                   kind=r.kind, powder_id=r.powder_id, display=r.display,
                   track=track.get(r.powder_id, ""), qc_valid=bool(r.qc_valid),
                   qc_verdict=r.qc_verdict, started_utc=r.started_utc)
        c = cyc[cyc.run_id == rid] if len(cyc) else cyc
        for ph in ("tap", "fine"):
            x = c[c.phase == ph].change_mg.to_numpy() if len(c) else np.array([])
            row[f"{ph}_n"] = len(x)
            row[f"{ph}_median_mg"] = float(np.median(x)) if len(x) else np.nan
            row[f"{ph}_robust_sd_mg"] = robust_sd(x)
            row[f"{ph}_sd_mg"] = float(np.std(x, ddof=1)) if len(x) > 1 else np.nan
            row[f"{ph}_frac_negative"] = float(np.mean(x < 0)) if len(x) else np.nan
            row[f"{ph}_rms_negative_mg"] = rms_negative(x)
            row[f"{ph}_min_mg"] = float(x.min()) if len(x) else np.nan
            row[f"{ph}_max_mg"] = float(x.max()) if len(x) else np.nan
        xt = c[(c.phase == "tap") & ~c.first_of_phase].change_mg if len(c) else []
        row["tap_robust_sd_excl_tilt_step_mg"] = robust_sd(xt)
        # first tap cycle of each dose: includes lowering the tube 22.5 -> 0 deg
        x1 = c[(c.phase == "tap") & c.first_of_phase].change_mg if len(c) else []
        row["tap_first_cycle_n"] = len(x1)
        row["tap_first_cycle_median_mg"] = float(np.median(x1)) if len(x1) else np.nan
        # noise source
        if row["tap_n"] >= MIN_N:
            src, val, n = "tap phase", row["tap_robust_sd_mg"], row["tap_n"]
        elif (row["fine_n"] >= MIN_N and row["tap_n"] == 0
              and abs(row["fine_median_mg"]) <= 2 * READABILITY_MG):
            src, val, n = "fine phase, nothing delivered", row["fine_robust_sd_mg"], row["fine_n"]
        else:
            src, val, n = "", np.nan, 0
        row.update(noise_source=src, noise_n=n, noise_mg=val, noise_floored_mg=floored(val))
        # at rest: first reading of each dose minus its tare reading
        ctx = [d for (rr, _, _), d in dose_ctx.items() if rr == rid]
        idle = [d["first_reading_mg"] for d in ctx if d["first_reading_mg"] is not None
                and (d["tared"] or str(r["round"]) == "1")]
        idle = np.asarray(idle, float)
        row.update(rest_n=len(idle), rest_robust_sd_mg=robust_sd(idle),
                   rest_rms_mg=float(np.sqrt(np.mean(idle ** 2))) if len(idle) else np.nan,
                   rest_max_abs_mg=float(np.abs(idle).max()) if len(idle) else np.nan)
        row["rest_floored_mg"] = floored(row["rest_robust_sd_mg"])
        tn = [d["tare_noise"] for d in ctx if d["tare_noise"] is not None]
        td = [abs(d["tare_drift"]) for d in ctx if d["tare_drift"] is not None]
        row.update(tare_n=len(tn),
                   tare_read_noise_median_mg=float(np.median(tn)) if tn else np.nan,
                   tare_read_noise_max_mg=float(np.max(tn)) if tn else np.nan,
                   tare_abs_drift_median_mg_per_min=float(np.median(td)) if td else np.nan)
        # round-1 battery protocols (tilt 0 = tube horizontal)
        t = trials[trials.run_id == rid]
        e = t[(t.block == "E") & (t.phase == "tap") & (t.tilt_deg == 0.0)].delta_g * 1000
        a = t[t.block == "A"].delta_g * 1000
        b = t[(t.block == "B") & (t.tilt_deg == 0.0)].delta_g * 1000
        row.update(protoE_tap0_n=len(e), protoE_tap0_robust_sd_mg=robust_sd(e),
                   protoE_tap0_median_mg=float(e.median()) if len(e) else np.nan,
                   protoE_tap0_frac_negative=float((e < 0).mean()) if len(e) else np.nan,
                   protoA_n=len(a), protoA_robust_sd_mg=robust_sd(a),
                   protoA_spread_mg=float(a.max() - a.min()) if len(a) else np.nan,
                   protoB_hold0_change_mg=float(b.iloc[0]) if len(b) else np.nan)
        row["in_figure"] = bool(src) and r.kind == "battery"
        out.append(row)
    per_run = pd.DataFrame(out)

    # ---- per valid 50 / 200 mg dose -----------------------------------------
    d = alld[(alld.dose_valid == True) & alld.target_mg.isin([50.0, 200.0])].copy()  # noqa: E712
    nz = per_run.set_index("run_id")
    rows = []
    for _, x in d.iterrows():
        ctx = dose_ctx.get((x.run_id, x.block, int(x.dose_n)), {})
        limit = 5.0 if x.target_mg < 100 else 10.0
        err = float(x.error_mg)
        margin = round(limit - abs(err), 1)
        rn = nz.loc[x.run_id]
        sigma = rn.noise_floored_mg
        own = [c["change_mg"] for c in ctx.get("cycles", []) if c["phase"] == "tap"]
        own_sd = robust_sd(own) if len(own) >= MIN_N else np.nan
        nxt = ctx.get("next")
        check = np.nan
        if (ctx.get("tare_warning") and nxt is not None and nxt.get("tare_warning")
                and np.isfinite(x.delivered_mg)):
            check = round(nxt["baseline_mg"] - ctx["baseline_mg"] - float(x.delivered_mg), 1)
        rows.append(dict(
            run_id=x.run_id, powder_id=x.powder_id, display=x.display,
            track=track.get(x.powder_id, ""), round=x["round"], location=x.location,
            read_path=x.read_path, block=x.block, dose_n=int(x.dose_n),
            target_mg=x.target_mg, error_mg=err, status=x.status, limit_mg=limit,
            within_limit=abs(err) <= limit + 1e-9, margin_mg=margin,
            final_reading_after=ctx.get("last_phase") or "",
            dose_tap_n=len(own), dose_tap_robust_sd_mg=own_sd,
            run_noise_source=rn.noise_source, run_noise_mg=sigma,
            call=classify(margin, sigma),
            call_if_tare_noise_free=classify(margin, floored(sigma / np.sqrt(2))),
            call_own_dose_noise=classify(margin, floored(own_sd) if np.isfinite(own_sd) else sigma),
            call_rms_negative=classify(margin, floored(rn.tap_rms_negative_mg)
                                       if rn.noise_source == "tap phase" else sigma),
            rest_first_reading_mg=ctx.get("first_reading_mg"),
            tare_read_noise_mg=ctx.get("tare_noise"),
            tare_drift_mg_per_min=ctx.get("tare_drift"),
            next_tare_check_mg=check))
    per_dose = pd.DataFrame(rows)
    return per_run, per_dose


def classify(margin: float, sigma: float) -> str:
    if not np.isfinite(sigma):
        return ""
    if abs(margin) > 2 * sigma:
        return "robust"
    if abs(margin) > sigma:
        return "marginal"
    return "not resolvable"


# ----------------------------------------------------------------------------
# Tables
# ----------------------------------------------------------------------------
CALLS = ["robust", "marginal", "not resolvable"]


def counts(per_dose: pd.DataFrame, col: str = "call") -> pd.DataFrame:
    rows = []
    for tgt in (50.0, 200.0):
        for ok in (True, False):
            g = per_dose[(per_dose.target_mg == tgt) & (per_dose.within_limit == ok)]
            rows.append(dict(target_mg=tgt, within_limit=ok, n=len(g),
                             **{c: int((g[col] == c).sum()) for c in CALLS}))
    return pd.DataFrame(rows)


def write_table(per_dose: pd.DataFrame, per_run: pd.DataFrame, path: Path) -> None:
    c = counts(per_dose)
    lines = [
        "% Generated by paper/figures/data/build_post_actuation_noise.py -- do not edit by hand.",
        r"\begin{table}[h]",
        r"\centering",
        r"\caption{Pass/fail calls of the valid 50 and 200~mg doses compared with the "
        r"balance noise after actuation in their own runs (Fig.~\ref{fgr:noiseact}). "
        r"The margin is the acceptance limit minus the absolute dose error, and the noise is "
        r"the robust standard deviation of the change between consecutive tap-phase readings. "
        r"A call is robust when the margin exceeds twice the noise, marginal when it lies "
        r"between one and two times the noise, and not resolvable otherwise. All these doses "
        r"are from the second round, in the new fume hood, with bracketed readings. Per-dose "
        r"values are in \texttt{paper/figures/data/post\_actuation\_noise\_doses.csv}.}",
        r"\label{tbl:noiseact}",
        r"\begin{tabular}{llrrrr}",
        r"\toprule",
        r"Target & Outcome & $n$ & Robust & Marginal & Not resolvable \\",
        r"\midrule",
    ]
    for _, r in c.iterrows():
        lim = "$\\pm$5~mg" if r.target_mg < 100 else "$\\pm$10~mg"
        out = f"within {lim}" if r.within_limit else f"outside {lim}"
        lines.append(f"{r.target_mg:.0f}~mg & {out} & {r.n} & {r['robust']} & "
                     f"{r['marginal']} & {r['not resolvable']} \\\\")
    lines += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    path.write_text("\n".join(lines) + "\n")
    print("wrote", path.name)


# ----------------------------------------------------------------------------
# Figure
# ----------------------------------------------------------------------------
SHORT = {"salt": "NaCl", "white-rice-flour": "White rice flour", "xanthan-gum": "Xanthan gum",
         "carboxymethyl-cellulose": "CMC", "sodium-alginate": "Sodium alginate",
         "calcium-lactate": "Calcium lactate", "sodium-sulfate": "Sodium sulfate",
         "barium-chloride": "Barium chloride", "alsi10mg": "AlSi10Mg",
         "silicon-325": "Si (fine)", "silicon-110-200": "Si (coarse)",
         "brown-rice-flour": "Brown rice flour", "fumed-silica": "Fumed silica"}
GROUPS = [("1", "lab_pre_hood", "Round 1, lab bench\nstability flag"),
          ("1", "shared_fume_hood", "Round 1, shared hood\nstability flag"),
          ("2", "new_fume_hood", "Round 2, new hood\n5-reading bracket")]


def colour(track: str) -> str:
    return RESEARCH if track == "research" else SURROGATE


def mk(track: str) -> str:
    return "s" if track == "research" else "o"


def panel_label(ax, letter: str, x: float = -0.02, y: float = 1.02) -> None:
    ax.text(x, y, f"({letter})", transform=ax.transAxes, fontsize=7.5,
            fontweight="bold", ha="right", va="bottom", color=INK)


def panel_runs(ax, per_run: pd.DataFrame) -> None:
    f = per_run[per_run.in_figure].sort_values("started_utc")
    xpos, labels, x, spans = [], [], 0.0, []
    for rnd, loc, title in GROUPS:
        g = f[(f["round"].astype(str) == rnd) & (f.location == loc)]
        if g.empty:
            continue
        x0 = x
        for _, r in g.iterrows():
            xpos.append((x, r))
            dagger = "" if r.qc_valid else "†"
            labels.append(f"{r.started_utc[5:7]}-{r.started_utc[8:10]}  "
                          f"{SHORT.get(r.powder_id, r.powder_id)}{dagger}")
            x += 1
        spans.append((x0 - 0.5, x - 0.5, title))
        x += 1.6
    for k, (a, b, title) in enumerate(spans):
        if k % 2 == 0:
            ax.axvspan(a, b, color="#f4f3ef", zorder=0, lw=0)
        ax.text((a + b) / 2, 1.0, title, transform=ax.get_xaxis_transform(),
                ha="center", va="top", fontsize=5.6, color=INK2, linespacing=1.15)
    for xx, r in xpos:
        post, rest = r.noise_floored_mg, r.rest_floored_mg
        if np.isfinite(rest):
            ax.plot([xx, xx], [rest, post], color=MUTED, lw=0.6, zorder=2)
            ax.scatter(xx, rest, s=13, marker=mk(r.track), facecolor="white",
                       edgecolor=INK2, linewidth=0.6, zorder=3)
        ax.scatter(xx, post, s=19, marker=mk(r.track), color=colour(r.track),
                   edgecolor="white", linewidth=0.5, zorder=4)
    x_end = xpos[-1][0] + 0.6
    # Half of each acceptance limit: above it no dose at that target can be
    # a robust pass (the largest possible margin, the full limit, is < 2x noise).
    for y, txt in ((2.5, "50 mg"), (5.0, "200 mg")):
        ax.hlines(y, -0.7, x_end, color=CRITICAL, lw=0.7, linestyles=(0, (3, 2)), zorder=1)
        ax.text(x_end + 0.15, y, txt, fontsize=5.2, color=CRITICAL, ha="left", va="center")
    ax.set_xticks([p for p, _ in xpos])
    ax.set_xticklabels(labels, rotation=55, ha="right", fontsize=5.4,
                       rotation_mode="anchor")
    ax.tick_params(axis="x", length=2, pad=1.5)
    ax.set_xlim(-0.7, x_end + 1.9)
    ax.set_yscale("log")
    ax.set_ylim(0.07, 120)
    ax.set_yticks([0.1, 1, 10, 100])
    ax.set_yticklabels(["≤0.1", "1", "10", "100"])
    ax.set_ylabel("Scatter of the change between\nconsecutive readings (mg)")
    ax.grid(axis="y", alpha=0.8, zorder=0)
    ax.legend(handles=[
        Line2D([], [], marker="o", ls="", ms=4.2, color=SURROGATE, markeredgecolor="white",
               label="After actuation, food-safe surrogate"),
        Line2D([], [], marker="s", ls="", ms=4.0, color=RESEARCH, markeredgecolor="white",
               label="After actuation, research-relevant"),
        Line2D([], [], marker="o", ls="", ms=3.6, markerfacecolor="white",
               markeredgecolor=INK2, label="At rest, start of each dose")],
        loc="upper left", bbox_to_anchor=(0.0, 0.86), fontsize=5.4, handletextpad=0.2,
        borderaxespad=0.2)


def panel_doses(ax, per_dose: pd.DataFrame, target: float, ylim: float) -> None:
    sub = per_dose[per_dose.target_mg == target]
    lim = 5.0 if target < 100 else 10.0
    xs = np.logspace(np.log10(0.05), np.log10(60), 400)
    ax.axhspan(-lim, lim, color="#e6f4e6", zorder=0, lw=0)
    # Union of the zones around both limits, drawn opaque so overlaps never
    # darken: within 2x noise (light), then within 1x noise (darker) on top.
    for k, colour_k in ((2.0, ZONE2), (1.0, ZONE1)):
        w = k * xs
        merged = w >= lim          # the two zones meet once k x noise >= limit
        ax.fill_between(xs, -lim - w, np.where(merged, lim + w, -lim + w),
                        color=colour_k, lw=0, zorder=1)
        ax.fill_between(xs, np.where(merged, -lim - w, lim - w), lim + w,
                        color=colour_k, lw=0, zorder=1)
    for edge in (-lim, lim):
        ax.axhline(edge, color=BAND_EDGE, lw=0.6, zorder=2)
    ax.axhline(0, color=INK2, lw=0.5, zorder=2)
    for _, r in sub.iterrows():
        x, e = r.run_noise_mg, r.error_mg
        c = colour(r.track)
        if abs(e) > ylim:
            yy, m = np.sign(e) * (ylim - 0.04 * ylim), "^" if e > 0 else "v"
            ax.scatter(x, yy, s=16, marker=m, facecolor="white", edgecolor=c,
                       linewidth=0.8, zorder=4)
        else:
            ax.scatter(x, e, s=14, marker=mk(r.track),
                       facecolor=c if r.within_limit else "white", edgecolor=c,
                       linewidth=0.8, zorder=4, alpha=0.95)
    ax.set_xscale("log")
    ax.set_xlim(0.07, 40)
    ax.set_xticks([0.1, 1, 10])
    ax.set_xticklabels(["≤0.1", "1", "10"])
    ax.set_ylim(-ylim, ylim)
    ax.set_xlabel("Noise after actuation in the dose's run (mg)")
    ax.set_ylabel(f"Error of {target:.0f} mg doses (mg)")
    ax.grid(axis="both", which="major", alpha=0.8, zorder=0)


TOP = {"salt": "NaCl", "white-rice-flour": "Rice flour", "xanthan-gum": "xanthan",
       "carboxymethyl-cellulose": "CMC", "sodium-alginate": "Alginate",
       "calcium-lactate": "Ca lactate", "sodium-sulfate": "Na$_2$SO$_4$",
       "alsi10mg": "AlSi10Mg", "silicon-325": "Si (fine)", "silicon-110-200": "Si (coarse)"}


def run_labels(ax, per_dose: pd.DataFrame) -> None:
    """Name each run at its noise position on a top axis (runs closer than
    0.05 decades share one label)."""
    pos = (per_dose.groupby("powder_id").run_noise_mg.first().sort_values())
    ticks, names = [], []
    for pid, x in pos.items():
        if ticks and np.log10(x) - np.log10(ticks[-1]) < 0.05:
            names[-1] = names[-1] + ", " + TOP[pid]
            ticks[-1] = np.sqrt(ticks[-1] * x)
            continue
        ticks.append(x)
        names.append(TOP[pid])
    top = ax.secondary_xaxis("top")
    top.set_xticks(ticks)
    top.set_xticklabels(names, rotation=90, fontsize=5.0, color=INK2)
    top.tick_params(axis="x", length=1.5, pad=1, color=MUTED)
    top.xaxis.set_minor_locator(matplotlib.ticker.NullLocator())
    top.spines["top"].set_visible(False)


def make_figure(per_run: pd.DataFrame, per_dose: pd.DataFrame) -> None:
    fig = plt.figure(figsize=(SI_TEXT_IN, 5.55))
    gs = fig.add_gridspec(2, 2, height_ratios=[1.0, 1.0], hspace=1.32, wspace=0.26)
    ax = fig.add_subplot(gs[0, :])
    panel_runs(ax, per_run)
    panel_label(ax, "a", x=-0.055)
    for k, (tgt, ylim) in enumerate(((50.0, 30.0), (200.0, 40.0))):
        ax = fig.add_subplot(gs[1, k])
        panel_doses(ax, per_dose, tgt, ylim)
        run_labels(ax, per_dose[per_dose.target_mg == tgt])
        panel_label(ax, "bc"[k], x=-0.12, y=1.08)
    handles = [
        Line2D([], [], marker="o", ls="", ms=3.6, color=SURROGATE, label="Surrogate, within limit"),
        Line2D([], [], marker="o", ls="", ms=3.6, markerfacecolor="white",
               markeredgecolor=SURROGATE, label="Surrogate, outside limit"),
        Line2D([], [], marker="s", ls="", ms=3.6, color=RESEARCH,
               label="Research-relevant, within limit"),
        Line2D([], [], marker="s", ls="", ms=3.6, markerfacecolor="white",
               markeredgecolor=RESEARCH, label="Research-relevant, outside limit"),
        Line2D([], [], marker="^", ls="", ms=3.6, markerfacecolor="white",
               markeredgecolor=INK2, label="Off scale"),
        Patch(facecolor="#e6f4e6", label="Acceptance limit"),
        Patch(facecolor=ZONE1, label="Within 1× noise of a limit"),
        Patch(facecolor=ZONE2, label="Within 2× noise of a limit"),
    ]
    fig.legend(handles=handles, loc="lower center", ncol=4, bbox_to_anchor=(0.5, -0.02),
               fontsize=5.4, handletextpad=0.3, columnspacing=1.6, handlelength=1.4)
    fig.savefig(FIG_DIR / f"{STEM}.pdf", bbox_inches="tight")
    (FIG_DIR / "preview").mkdir(exist_ok=True)
    fig.savefig(FIG_DIR / "preview" / f"{STEM}.png", dpi=200, bbox_inches="tight",
                facecolor="white")
    plt.close(fig)
    print("wrote", STEM)


# ----------------------------------------------------------------------------
def report(per_run: pd.DataFrame, per_dose: pd.DataFrame) -> None:
    pd.set_option("display.width", 220)
    f = per_run[per_run.noise_source != ""]
    print(f[["run_id", "round", "location", "read_path", "noise_source", "noise_n", "noise_mg",
             "tap_frac_negative", "tap_rms_negative_mg", "rest_n", "rest_robust_sd_mg"]]
          .round(2).to_string(index=False))
    for col in ("call", "call_if_tare_noise_free", "call_own_dose_noise", "call_rms_negative"):
        print(f"\n{col}\n", counts(per_dose, col).to_string(index=False))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--repo", default=DEFAULT_REPO)
    ap.add_argument("--ref", default=DEFAULT_REF)
    a = ap.parse_args()
    per_run, per_dose = build(a.repo, a.ref)
    num = per_run.select_dtypes("number").columns
    per_run[num] = per_run[num].round(3)
    per_run.to_csv(HERE / "post_actuation_noise.csv", index=False)
    per_dose.round(3).to_csv(HERE / "post_actuation_noise_doses.csv", index=False)
    print(f"wrote post_actuation_noise.csv ({len(per_run)} runs), "
          f"post_actuation_noise_doses.csv ({len(per_dose)} doses)")
    write_table(per_dose, per_run, HERE / "post_actuation_noise_table.tex")
    make_figure(per_run, per_dose)
    report(per_run, per_dose)


if __name__ == "__main__":
    main()
