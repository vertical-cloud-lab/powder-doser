#!/usr/bin/env python3
"""Account for every closed-loop dose attempt, by powder and target mass.

Reads doses_all.csv (one row per attempt, both rounds, built by
build_closed_loop_doses.py) and writes

  dose_accounting.csv          one row per powder x target (50 mg, 200 mg, 1 g)
                               for all 13 powders, including combinations that
                               were never attempted, plus subtotal and total rows
  dose_accounting_table.tex    the same as an SI longtable (\\label{tbl:doseaccount})

Definitions (identical to make_data_figures.py and the main text)
-----------------------------------------------------------------
* attempt   every dose the controller started (a DOSE row, or the one dose
            reconstructed after a serial-link fault).
* valid     doses_all.csv ``dose_valid``: run passed screening, the dose ended
            in a defined controller state, and an auger rotation or tap was
            logged; demonstration runs are never valid.
* within limit   |error| <= 10 % of target below 100 mg, <= 5 % at or above.
* firmware label ``status`` of a valid dose: ok (inside the +/-5 mg stopping
            band), overshoot, stalled, cycle-budget, timeout.
* excluded  attempt - valid; each excluded attempt gets ONE plain-English
            reason: the run's screening verdict if the run failed screening,
            otherwise the dose-level reason.
* not run   a powder x target with no attempt; the reason is the recorded
            operator decision (issue #116 comment 5625477508, 2026-09-10;
            docs/battery-runs/skipped-powders.md on the #116 branches), or
            plain "not run" when no reason was recorded.

The script asserts the manuscript's headline counts (valid doses within the
limit: 14/30 at 50 mg, 18/30 at 200 mg, 24/39 at 1 g, 56/99 overall, and 24/24
at 1 g on the seven fastest-flowing powders dosed) and stops if they change.

Usage::

    python3 build_dose_accounting.py
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
DOSES_CSV = HERE / "doses_all.csv"
OUT_CSV = HERE / "dose_accounting.csv"
OUT_TEX = HERE / "dose_accounting_table.tex"

TARGETS = (50.0, 200.0, 1000.0)

# All 13 powders, in the order of main-text Table 1: mass per auger revolution
# at 22.5 deg (Fig. 3a), fastest first; the three that conveyed no measurable
# amount last.
POWDERS = [
    ("alsi10mg", "AlSi10Mg"),
    ("silicon-110-200", "Si ($-$110/+200 mesh)"),
    ("sodium-sulfate", "Sodium sulfate"),
    ("calcium-lactate", "Calcium lactate"),
    ("barium-chloride", "Barium chloride"),
    ("xanthan-gum", "Xanthan gum"),
    ("salt", "NaCl"),
    ("carboxymethyl-cellulose", "CMC"),
    ("white-rice-flour", "White rice flour"),
    ("sodium-alginate", "Sodium alginate"),
    ("silicon-325", "Si ($-$325 mesh)"),
    ("brown-rice-flour", "Brown rice flour"),
    ("fumed-silica", "Fumed silica"),
]
DISPLAY = dict(POWDERS)
ORDER = {pid: k for k, (pid, _) in enumerate(POWDERS)}

NUMWORD = {1: "One", 2: "Two", 3: "Three", 4: "Four", 5: "Five", 6: "Six", 7: "Seven"}

# The abstract's favourable subset: every 1 g dose on these seven powders,
# the seven fastest-flowing powders with a valid dose (barium chloride, fourth
# fastest, has none).
FASTEST_SEVEN = ["alsi10mg", "silicon-110-200", "sodium-sulfate", "calcium-lactate",
                 "xanthan-gum", "salt", "carboxymethyl-cellulose"]

# Run screening verdicts (runs_all.csv qc_verdict) in plain English, worded as
# in the run inventory, SI Table S4 (make_run_inventory.py).
RUN_REASON = {
    "doser-scale-unreadable": "balance could not be read",
    "outlet-misaligned": "outlet misaligned",
    "arching-no-feed": "powder caked in the tube",
    "no-tilt-servo-fault": "tilt servo failed",
    "no-conveyance-auger-suspect": "nothing delivered, auger suspected",
}
FW = [("ok", "fw_ok"), ("overshoot", "fw_overshoot"), ("stalled", "fw_stalled"),
      ("cycle-budget", "fw_cycle_budget"), ("timeout", "fw_timeout")]
FW_COLS = [c for _, c in FW]

# Combinations never attempted, with the recorded reason.  The operator
# stopped testing the two powders that had delivered almost nothing in round 1
# (#116 comment 5625477508; skipped-powders.md): brown rice flour (<= 0.3 mg
# per revolution at every tilt; its three 1 g doses stalled) and fumed silica
# (<= 0.25 mg per revolution; no round-1 closed-loop doses either).
NOT_RUN = {
    ("brown-rice-flour", 50.0): "not run: delivered almost nothing in round 1",
    ("brown-rice-flour", 200.0): "not run: delivered almost nothing in round 1",
    ("fumed-silica", 50.0): "not run: delivered almost nothing in round 1",
    ("fumed-silica", 200.0): "not run: delivered almost nothing in round 1",
    ("fumed-silica", 1000.0): "not run: delivered almost nothing in round 1",
}

HEADLINE = {50.0: (30, 14), 200.0: (30, 18), 1000.0: (39, 24), "all": (99, 56)}


def within_limit(error_mg: float, target_mg: float) -> bool:
    pct = 10.0 if target_mg < 100 else 5.0
    return abs(100.0 * error_mg / target_mg) <= pct + 1e-9


def exclusion_reason(r) -> str:
    """One plain-English reason for an attempt that is not a valid dose."""
    if r.protocol == "demo":
        return "demonstration run"
    if not r.run_qc_valid:
        return RUN_REASON[r.run_qc_verdict]
    why = str(r.invalid_reason)
    if "no actuation" in why:
        # Firmware logged 0.00 auger rev and 0 taps.  The serial log shows a
        # sub-second bulk spin the integer-second clock counted as zero
        # (build_dose_traces.py, ``bulk_spin``).
        return "no rotation or tap logged"
    if "no terminal control state" in why:
        return "no final balance reading"
    raise ValueError(f"unmapped exclusion: {r.run_id} {r.dose_n}: {why}")


def load() -> pd.DataFrame:
    d = pd.read_csv(DOSES_CSV)
    d["valid"] = d.dose_valid.astype(bool)
    d["within"] = [v and within_limit(e, t) for v, e, t in zip(d.valid, d.error_mg, d.target_mg)]
    d["reason"] = [None if v else exclusion_reason(r) for v, (_, r) in zip(d.valid, d.iterrows())]
    return d


def tally(g: pd.DataFrame) -> dict:
    v = g[g.valid]
    out = dict(attempts=len(g), valid=len(v), within_limit=int(v.within.sum()),
               excluded=int((~g.valid).sum()))
    for status, col in FW:
        out[col] = int((v.status == status).sum())
    other = set(v.status) - {s for s, _ in FW}
    assert not other, f"unexpected firmware labels on valid doses: {other}"
    reasons = g[~g.valid].reason.value_counts()
    out["excluded_reasons"] = "; ".join(f"{why} ({n})" for why, n in reasons.items())
    out["rounds"] = ",".join(sorted({str(x) for x in g["round"]}))
    out["runs"] = ";".join(sorted(set(g.run_id)))
    return out


def label(tgt: float) -> str:
    return f"{tgt:.0f} mg" if tgt < 1000 else "1 g"


def build(d: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for tgt in TARGETS:
        sub = d[d.target_mg == tgt]
        for pid, name in POWDERS:
            g = sub[sub.powder_id == pid]
            row = dict(row_type="powder", target_mg=tgt, powder_id=pid,
                       display=name.replace("$-$", "-"))
            if len(g):
                row.update(tally(g), not_run_reason="")
            else:
                row.update(attempts=0, valid=0, within_limit=0, excluded=0,
                           **{c: 0 for c in FW_COLS}, excluded_reasons="",
                           not_run_reason=NOT_RUN.get((pid, tgt), "not run"))
            rows.append(row)
        rows.append(dict(row_type="total", target_mg=tgt, powder_id="all",
                         display=f"All powders, {label(tgt)}", **tally(sub)))
        if tgt == 1000.0:
            dosed = set(sub[sub.valid].powder_id)
            rest = sorted(dosed - set(FASTEST_SEVEN), key=ORDER.get)
            rows.append(dict(row_type="subset", target_mg=tgt, powder_id=";".join(FASTEST_SEVEN),
                             display="seven fastest-flowing",
                             **tally(sub[sub.powder_id.isin(FASTEST_SEVEN)])))
            rows.append(dict(row_type="subset", target_mg=tgt, powder_id=";".join(rest),
                             display=f"other {NUMWORD[len(rest)].lower()} dosed",
                             **tally(sub[sub.powder_id.isin(rest)])))
    other = d[~d.target_mg.isin(TARGETS)]
    rows.append(dict(row_type="other", target_mg=float("nan"), powder_id="salt",
                     display="NaCl at 0.5 and 2 g", **tally(other)))
    rows.append(dict(row_type="total", target_mg=float("nan"), powder_id="all",
                     display="All closed-loop attempts", **tally(d)))
    cols = ["row_type", "target_mg", "powder_id", "display", "attempts", "valid",
            "within_limit", *FW_COLS, "excluded", "excluded_reasons", "not_run_reason",
            "rounds", "runs"]
    df = pd.DataFrame(rows)[cols]
    for c in ["attempts", "valid", "within_limit", "excluded", *FW_COLS]:
        df[c] = df[c].astype(int)
    return df


def check(df: pd.DataFrame, d: pd.DataFrame) -> None:
    """Stop if the counts no longer reproduce the manuscript's headline."""
    tot = df[(df.row_type == "total")]
    for tgt in TARGETS:
        r = tot[tot.target_mg == tgt].iloc[0]
        assert (r.valid, r.within_limit) == HEADLINE[tgt], (tgt, r.valid, r.within_limit)
    r = tot[tot.target_mg.isna()].iloc[0]
    assert (r.valid, r.within_limit) == HEADLINE["all"], (r.valid, r.within_limit)
    assert r.attempts == len(d) and r.excluded == len(d) - r.valid
    fast, rest = df[df.row_type == "subset"].itertuples()
    assert (fast.valid, fast.within_limit) == (24, 24), (fast.valid, fast.within_limit)
    assert rest.within_limit == 0 and fast.valid + rest.valid == HEADLINE[1000.0][0]
    # Every attempt is counted exactly once, and every valid dose has one label.
    per = df[df.row_type.isin(["powder", "other"])]
    assert per.attempts.sum() == len(d) and per.valid.sum() == d.valid.sum()
    assert int(per[FW_COLS].to_numpy().sum()) == int(d.valid.sum())


def facts(d: pd.DataFrame, df: pd.DataFrame) -> dict:
    """Numbers quoted in the caption, computed rather than typed."""
    g1 = d[(d.target_mg == 1000.0) & d.valid]
    st = g1[g1.status == "stalled"]
    nr = d[d.reason == "no rotation or tap logged"].sort_values("error_mg", ascending=False)
    rest = df[df.row_type == "subset"].iloc[1]
    recon = d[d.reconstructed & d.valid]
    return dict(stalled_1g=len(st), stalled_1g_within=int(st.within.sum()),
                n_norot=len(nr), norot_targets=sorted(set(nr.target_mg)),
                norot_err=[f"{e:+.1f}" for e in nr.error_mg],
                rest_valid=int(rest.valid),
                rest_names=NUMWORD[len(rest.powder_id.split(";"))].lower() + " ("
                + ", ".join(SHORT[p] for p in rest.powder_id.split(";")[:-1]) + ", and "
                + SHORT[rest.powder_id.split(";")[-1]] + ")",
                recon=recon.iloc[0] if len(recon) else None)


# ----------------------------------------------------------------------------
# LaTeX
# ----------------------------------------------------------------------------
NCOL = 10
# Names as the caption's running text uses them.
SHORT = {"white-rice-flour": "white rice flour", "sodium-alginate": "sodium alginate",
         "silicon-325": "fine silicon", "brown-rice-flour": "brown rice flour"}


def caption(f: dict) -> str:
    norot = " and ".join(f["norot_err"])
    tg = label(f["norot_targets"][0]).replace(" ", "~") if len(f["norot_targets"]) == 1 else ""
    rc = f["recon"]
    return (
        r"Accounting for every closed-loop dose attempt in both test rounds, by powder and "
        r"target mass. \emph{Attempts} counts every dose the controller started. A dose is "
        r"\emph{valid} when its run passed screening, it ended in a defined controller state, "
        r"and the auger or solenoid moved (a continuous spin in the bulk phase counts even when "
        r"it was too short for the firmware's 1~s clock to log a revolution). \emph{Within limit} counts valid "
        r"doses inside the acceptance limit ($\pm$10\% at 50~mg, $\pm$5\% at 200~mg and 1~g). "
        r"The firmware columns give the controller's own end label for each valid dose. "
        r"\emph{ok}: inside its $\pm$5~mg stopping band; \emph{over}: more than 5~mg above "
        r"the target; \emph{stall}: the reading stopped rising; \emph{budget}: 200 cycles of "
        r"one phase; \emph{time}: 900~s. The controller stopped on its own $\pm$5~mg band, "
        r"whereas doses are scored against the acceptance limit, so the two counts differ. "
        rf"At 1~g, for example, {f['stalled_1g_within']} of the {f['stalled_1g']} doses "
        r"labelled stalled were within the $\pm$50~mg limit. The two indented rows split the "
        r"1~g total by powder. The 24 doses within the limit are every dose on the seven "
        r"fastest-flowing powders dosed (24 of 24): AlSi10Mg, coarse silicon, sodium sulfate, "
        r"calcium lactate, xanthan gum, NaCl, and CMC. "
        rf"The {f['rest_valid']} valid doses on the other {f['rest_names']} all missed it. "
        r"The last column gives the reason for each excluded attempt, with the number of "
        r"attempts, or why a combination was not run. "
        + (rf"{NUMWORD[f['n_norot']]} {tg} doses were excluded because the firmware logged no "
           r"rotation or tap. " if f["n_norot"] else "")
        + (rf"One valid {label(rc.target_mg).replace(' ', '~')} "
           rf"{rc.display[0].lower() + rc.display[1:]} dose was reconstructed from its balance "
           r"trace and camera record after the serial link failed. " if rc is not None else "")
        + r"Powders are in the order of Table~1 of the main text. Per-dose records are in "
        r"\texttt{paper/figures/data/doses\_all.csv}.")


def fmt_row(cells: list[str]) -> str:
    return " & ".join(cells) + r" \\"


def tex_cells(r, name: str) -> list[str]:
    if r.attempts == 0:
        return [name, "0"] + ["--"] * 7 + [r.not_run_reason]
    if r.valid == 0:
        nums = ["--"] * 6
    else:
        nums = [str(r.within_limit)] + [str(r[c]) for c in FW_COLS]
    note = r.excluded_reasons if isinstance(r.excluded_reasons, str) else ""
    return [name, str(r.attempts), str(r.valid)] + nums + [note]


def write_tex(df: pd.DataFrame, f: dict) -> None:
    head = (r" & & & Within & \multicolumn{5}{c}{Firmware end label (valid doses)} "
            r"& Excluded attempts, \\" "\n"
            r"\cmidrule(lr){5-9}" "\n"
            r"Powder & Attempts & Valid & limit & ok & over & stall & budget & time "
            r"& or why not run \\")
    lines = [
        "% Generated by paper/figures/data/build_dose_accounting.py -- do not edit by hand.",
        r"\begingroup",
        r"\setlength{\tabcolsep}{3.5pt}",
        r"\begin{longtable}{@{}lrrrrrrrr>{\raggedright\arraybackslash}p{5.3cm}@{}}",
        r"\caption{" + caption(f) + r"}\label{tbl:doseaccount}\\",
        r"\toprule", head, r"\midrule\endfirsthead",
        r"\toprule", head, r"\midrule\endhead",
        r"\midrule\multicolumn{" + str(NCOL) + r"}{r@{}}{\emph{continued on next page}}\\"
        r"\endfoot",
        r"\bottomrule\endlastfoot",
    ]
    for tgt in TARGETS:
        lim = {50.0: "5", 200.0: "10", 1000.0: "50"}[tgt]
        lines.append(r"\multicolumn{" + str(NCOL) + r"}{@{}l}{\textbf{" +
                     label(tgt).replace(" ", "~") + r" target} (acceptance limit $\pm$" +
                     lim + r"~mg)}\\")
        sub = df[df.target_mg == tgt]
        for _, r in sub[sub.row_type == "powder"].iterrows():
            lines.append(fmt_row(tex_cells(r, DISPLAY[r.powder_id])))
        lines.append(r"\cmidrule(l){1-" + str(NCOL) + "}")
        r = sub[sub.row_type == "total"].iloc[0]
        lines.append(fmt_row(tex_cells(r, r"\emph{All powders}")))
        for _, r in sub[sub.row_type == "subset"].iterrows():
            lines.append(fmt_row(tex_cells(r, r"\quad " + r.display)))
        lines.append(r"\midrule")
    r = df[df.row_type == "other"].iloc[0]
    lines.append(fmt_row(tex_cells(r, "NaCl at 0.5 and 2~g")))
    r = df[(df.row_type == "total") & df.target_mg.isna()].iloc[0]
    lines.append(fmt_row(tex_cells(r, r"\emph{All attempts}")))
    lines += [r"\end{longtable}", r"\endgroup"]
    OUT_TEX.write_text("\n".join(lines) + "\n")
    print("wrote", OUT_TEX.name)


def main() -> None:
    d = load()
    df = build(d)
    check(df, d)
    df.to_csv(OUT_CSV, index=False)
    print(f"wrote {OUT_CSV.name} ({len(df)} rows)")
    write_tex(df, facts(d, df))
    tot = df[df.row_type == "total"]
    for _, r in tot.iterrows():
        print(f"{r.display:28s} attempts {r.attempts:3d}  valid {r.valid:3d}  within "
              f"{r.within_limit:3d}  excluded {r.excluded:3d}  fw ok/over/stall/budget/time "
              f"{r.fw_ok}/{r.fw_overshoot}/{r.fw_stalled}/{r.fw_cycle_budget}/{r.fw_timeout}")


if __name__ == "__main__":
    main()
