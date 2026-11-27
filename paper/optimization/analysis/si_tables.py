#!/usr/bin/env python3
"""LaTeX bodies of the SI tables that are not per-dose listings.

  tables/si_main_effects.tex   screening main effects of campaign 1 (16 corners)
  tables/si_gp_cv.tex          leave-one-out cross-validation of the four models
  tables/si_properties.tex     literature properties of the 12 powders used in the correlations

Run after opt_stats.py and gp_diagnostics.py (from paper/optimization/):
  python3 analysis/si_tables.py
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
RES = HERE / "results"
TAB = RES / "tables"

FACTORS = [("bulk_tap", "Taps during bulk stage", ("off", "2hz"), "off / 2~Hz"),
           ("trim_tap", "Taps during trickle stage", ("off", "2hz"), "off / 2~Hz"),
           ("bulk_tilt_deg", r"Bulk tilt ($^\circ$)", (15.0, 40.0), "15 / 40"),
           ("trickle_tilt_deg", r"Trickle tilt ($^\circ$)", (10.0, 30.0), "10 / 30"),
           ("tap_tilt_deg", r"Tap tilt ($^\circ$)", (0.0, 15.0), "0 / 15"),
           ("bulk_rpm", "Bulk speed (rpm)", (20.0, 100.0), "20 / 100"),
           ("trickle_start_remaining_g", "Switch to trickle (g to go)", (0.05, 0.3), "0.05 / 0.30"),
           ("tolerance_g", r"Stopping band $\pm\delta$ (mg)", (0.003, 0.015), "3 / 15")]


def main_effects():
    d = pd.read_csv(RES / "doses_salt_20260929.csv")
    c = d[d.group == "corner"]
    lines = []
    for key, name, (lo, hi), levels in FACTORS:
        row = [name, levels]
        for lev in (lo, hi):
            g = c[c[key] == lev]
            ok = g[g.status == "ok"]
            row.append(f"{ok.t.mean():.0f} ({len(ok)})" if len(ok) else "--")
        for lev in (lo, hi):
            g = c[c[key] == lev]
            row.append(f"{g['abs'].mean():.1f}")
        for lev in (lo, hi):
            g = c[c[key] == lev]
            row.append(str(int((g.status != "ok").sum())))
        lines.append(" & ".join(row) + r" \\")
    (TAB / "si_main_effects.tex").write_text("\n".join(lines) + "\n")


def gp_cv():
    r = json.load(open(RES / "gp_cv.json"))
    names = {"constant": "Constant (mean of the other doses)", "linear": "Linear, main effects (OLS)",
             "gp-map": "GP, Mat\\'ern-5/2, MAP", "saas": "SAAS GP, NUTS (campaign model)",
             "saas-log": "SAAS GP on log time"}
    lines = []
    for obj, lab, unit in (("t", "Time", "s"), ("e", "$|e|$", "mg")):
        for m, v in r[obj].items():
            rho = "--" if m == "constant" else f"{v['spearman_rho']:.2f} ({v['spearman_p']:.3f})"
            rmse = f"{v['rmse']:.2f}" if m == "saas-log" else f"{v['rmse']:.1f}"
            u = "log s" if m == "saas-log" else unit
            lines.append(f"{lab} & {names[m]} & {rho} & {rmse}~{u} & {100 * v['coverage95']:.0f} & "
                         f"{v['z_sd']:.2f} & {v['shapiro_p']:.3f} \\\\")
        lines.append(r"\midrule")
    lines = lines[:-1]
    (TAB / "si_gp_cv.tex").write_text("\n".join(lines) + "\n")
    ff = r["full_fit"]
    rel = []
    for obj in ("t", "e"):
        w = ff[obj]["median_inverse_lengthscale"]
        rel.append(" & ".join(f"{w[k]:.2f}" for k, *_ in FACTORS))
    (TAB / "si_gp_relevance.tex").write_text(
        f"Time & {rel[0]} \\\\\n$|e|$ & {rel[1]} \\\\\n")


def properties():
    lit = pd.read_csv(ROOT / "data" / "powders" / "literature_powder_properties.csv")
    short = {"salt": "NaCl", "white-rice-flour": "White rice flour", "brown-rice-flour": "Brown rice flour",
             "sodium-alginate": "Sodium alginate", "calcium-lactate": "Calcium lactate",
             "carboxymethyl-cellulose": "Carboxymethyl cellulose", "xanthan-gum": "Xanthan gum",
             "sodium-sulfate": "Na$_2$SO$_4$", "silicon-110-200": r"Si, 75--150~\si{\micro\metre}",
             "silicon-325": r"Si, $<$44~\si{\micro\metre}", "alsi10mg": "AlSi10Mg", "barium-chloride": r"BaCl$_2\cdot$2H$_2$O"}
    lines = []
    for _, r in lit.iterrows():
        def f(x, nd=2):
            return "--" if pd.isna(x) else f"{x:.{nd}f}"
        lines.append(f"{short.get(r.powder_id, r.powder_id)} & {f(r.bulk_density_g_ml)} & {f(r.tapped_density_g_ml)} & "
                     f"{f(r.hausner_ratio)} & {f(r.d50_um, 0)} & {f(r.angle_repose_deg, 0)} & {f(r.moisture_pct)} & "
                     f"{str(r.hr_provenance).replace('_', '-')} \\\\")
    (TAB / "si_properties.tex").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    TAB.mkdir(parents=True, exist_ok=True)
    main_effects()
    gp_cv()
    properties()
    print("wrote", TAB)
