#!/usr/bin/env python3
"""Would the screening design plus a linear model have found the same settings? (retrospective)

Fits ordinary least squares, main effects only, to the 28 doses dosed before the optimizer's phase of
campaign 1 (16 corners, 8 centre points, 4 hand-tuned), on log(time) and on |error| (jams at their
failure-limit encoding, as the campaign gave them to Ax). Predicts both objectives at all 2^8 corners of
the search box and lists the predicted Pareto set, with the rank of the corner that bo-005 occupies.
No dose is simulated; this only asks where a simpler strategy would have pointed.
Writes analysis/results/linear_screen_baseline.json.
"""
from __future__ import annotations

import itertools
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gp_diagnostics as g  # noqa: E402


def pareto(t, e):
    return np.array([not ((t <= t[i]) & (e <= e[i]) & ((t < t[i]) | (e < e[i]))).any() for i in range(len(t))])


def main():
    df, X, bounds = g.load()
    pre = ~df.label.str.startswith("bo-")
    Xp, t, e = X[pre.values], df.t.values[pre.values], df.e.values[pre.values]
    A = np.c_[np.ones(len(Xp)), Xp]
    bt, *_ = np.linalg.lstsq(A, np.log(t), rcond=None)
    be, *_ = np.linalg.lstsq(A, e, rcond=None)
    corners = np.array(list(itertools.product([0.0, 1.0], repeat=X.shape[1])))
    C = np.c_[np.ones(len(corners)), corners]
    pt, pe = np.exp(C @ bt), C @ be
    pm = pareto(pt, pe)
    camp = [json.loads(l) for l in open(g.SALT / "campaign_records.jsonl")]
    bo5 = next(r for r in camp if r["label"] == "bo-005")
    x5 = g.x_of(bo5["params"], bounds)
    k5 = int(np.argmin(np.abs(corners - x5).sum(1)))
    names = g.PARAMS
    rows = []
    for i in np.where(pm)[0]:
        rows.append({"corner": {n: ("hi" if v else "lo") for n, v in zip(names, corners[i])},
                     "pred_t_s": round(float(pt[i]), 1), "pred_abs_mg": round(float(pe[i]), 2)})
    rows.sort(key=lambda r: r["pred_t_s"])
    out = {"n_doses": int(pre.sum()), "coef_log_t": dict(zip(["intercept"] + names, map(float, bt))),
           "coef_abs": dict(zip(["intercept"] + names, map(float, be))), "pareto_corners": rows,
           "bo005_corner_on_pareto": bool(pm[k5]),
           "bo005_corner_pred": {"t_s": round(float(pt[k5]), 1), "abs_mg": round(float(pe[k5]), 2)},
           "bo005_exactly_at_corner": bool(np.allclose(corners[k5], x5))}
    json.dump(out, open(HERE / "results" / "linear_screen_baseline.json", "w"), indent=1)
    print(json.dumps({k: v for k, v in out.items() if k not in ("coef_log_t", "coef_abs")}, indent=1)[:3000])


if __name__ == "__main__":
    main()
