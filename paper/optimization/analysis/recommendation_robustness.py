#!/usr/bin/env python3
"""Does campaign 1's recommendation depend on how time is modelled?

Refits the SAAS GP (as in gp_diagnostics.py) on all 42 doses twice, once on raw time and once on
log(time), with the absolute error as the second objective, and lists the model Pareto set (Pareto set
of the posterior means over the 42 dosed settings, as the campaign's recommendation was chosen).
Writes analysis/results/recommendation_robustness.json.

Usage (from paper/optimization/):  python3 analysis/recommendation_robustness.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gp_diagnostics as g  # noqa: E402


def pareto(t, e):
    keep = []
    for i in range(len(t)):
        dom = (t <= t[i]) & (e <= e[i]) & ((t < t[i]) | (e < e[i]))
        keep.append(not dom.any())
    return np.array(keep)


def main():
    df, X, _ = g.load()
    y_t, y_e = df.t.values.astype(float), df.e.values.astype(float)
    m_e = g.fit_saas(X, y_e, seed=2)
    mu_e, _ = g.saas_predict(m_e, X)
    out = {}
    for name, yt, back in (("raw_time", y_t, lambda v: v), ("log_time", np.log(y_t), np.exp)):
        m_t = g.fit_saas(X, yt, seed=3)
        mu_t, _ = g.saas_predict(m_t, X)
        mu_t = back(mu_t)
        pm = pareto(mu_t, mu_e)
        rows = sorted(({"label": df.label[i], "pred_t_s": round(float(mu_t[i]), 1),
                        "pred_abs_mg": round(float(mu_e[i]), 2)} for i in np.where(pm)[0]),
                      key=lambda r: r["pred_t_s"])
        out[name] = rows
        print(name, [(r["label"], r["pred_t_s"], r["pred_abs_mg"]) for r in rows])
    json.dump(out, open(HERE / "results" / "recommendation_robustness.json", "w"), indent=1)


if __name__ == "__main__":
    main()
