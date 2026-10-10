"""Twin discharge of the printed open-end auger vs the CAD cone-exit auger (27.5 deg, 60 rpm).

Reads the exported outflow series of ``results/cases/rig_open_t27p5_r60`` and
``results/cases/rig_t27p5_r60`` and writes ``open_end_vs_cad.png`` and
``open_end_vs_cad.json`` (mass per revolution and per 45 deg sector).
"""

import json
import os

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
CASES = os.path.join(os.path.dirname(HERE), "results", "cases")
INK, INK2, SURF, GRID = "#0b0b0b", "#52514e", "#fcfcfb", "#e4e3df"
OPEN, CAD = "#2a78d6", "#eb6834"
RIG_MG_PER_REV = 105.0  # PR #166 centre point, 27.5 deg / 60 rpm


def load(name):
    d = os.path.join(CASES, name)
    case = json.load(open(os.path.join(d, "case.json")))
    O = np.loadtxt(os.path.join(d, "outflow.txt"), comments=("#", "t_s"), ndmin=2)
    t0, T, revs = case["settle_s"], case["period_s"], case["cfg"]["revs"]
    rev = (O[:, 0] - t0) / T
    m = O[:, 1] * 1e6 - np.interp(t0, O[:, 0], O[:, 1] * 1e6)
    return rev, m, revs, case


def summary(rev, m, revs):
    t_end = min(revs, rev[-1])
    per_rev = [float(np.interp(k + 1, rev, m) - np.interp(k, rev, m)) for k in range(int(np.floor(t_end + 1e-9)))]
    edges = np.arange(0, t_end + 1e-9, 1 / 8)
    sectors = np.diff(np.interp(edges, rev, m))
    return per_rev, edges, sectors


def main():
    r_o, m_o, revs_o, case_o = load("rig_open_t27p5_r60")
    r_c, m_c, revs_c, _ = load("rig_t27p5_r60")
    pr_o, e_o, s_o = summary(r_o, m_o, revs_o)
    pr_c, e_c, s_c = summary(r_c, m_c, revs_c)
    t_stop = revs_o
    after_o = float(m_o[-1] - np.interp(t_stop, r_o, m_o)) if r_o[-1] > t_stop else None
    out = {"open_end": {"per_rev_mg": pr_o, "sector45_mg": s_o.round(1).tolist(), "afterflow_mg": after_o,
                        "n_init": case_o["n_init"]},
           "cad": {"per_rev_mg": pr_c, "sector45_mg": s_c.round(1).tolist()},
           "rig_mg_per_rev": RIG_MG_PER_REV}
    json.dump(out, open(os.path.join(HERE, "open_end_vs_cad.json"), "w"), indent=1)

    fig, axs = plt.subplots(1, 2, figsize=(10.5, 4.2), facecolor=SURF, gridspec_kw={"width_ratios": [1.1, 1]})
    ax = axs[0]
    ax.set_facecolor(SURF)
    on_o, on_c = r_o <= revs_o + 1e-9, r_c <= revs_c + 1e-9  # motor-on part only (afterflow is in the json)
    ax.plot(r_o[on_o], m_o[on_o], color=OPEN, lw=2, label="printed open end")
    ax.plot(r_c[on_c], m_c[on_c], color=CAD, lw=2, label="CAD cone + Ø3 exit")
    xx = np.array([0, max(revs_o, revs_c)])
    ax.plot(xx, RIG_MG_PER_REV * xx, color=INK2, lw=1.2, ls=(0, (4, 3)), label="rig, 105 mg/rev")
    ax.set_xlim(-0.05, max(revs_o, revs_c) + 0.05)
    ax.set_xlabel("auger revolutions since the exit opened", fontsize=8.5, color=INK2)
    ax.set_ylabel("dispensed salt (mg)", fontsize=8.5, color=INK2)
    ax.set_title("Cumulative discharge, twin at 27.5°, 60 rpm", fontsize=9.5, color=INK, loc="left")
    ax.legend(fontsize=8, frameon=False, loc="upper left")
    ax2 = axs[1]
    ax2.set_facecolor(SURF)
    w = 1 / 8
    ax2.bar(e_o[:-1] + w / 2, s_o, width=w * 0.86, color=OPEN, label="printed open end")
    ax2.bar(e_c[:-1] + w / 2, s_c, width=w * 0.86, color=CAD, label="CAD cone + Ø3 exit")
    ax2.set_xlabel("auger revolutions since the exit opened", fontsize=8.5, color=INK2)
    ax2.set_ylabel("salt per 45° of rotation (mg)", fontsize=8.5, color=INK2)
    ax2.set_title("Pulses: mass per 45° sector", fontsize=9.5, color=INK, loc="left")
    ax2.legend(fontsize=8, frameon=False, loc="upper right")
    for a in axs:
        a.grid(color=GRID, lw=0.6)
        a.set_axisbelow(True)
        a.tick_params(labelsize=7.5, colors=INK2)
        for sp in a.spines.values():
            sp.set_color("#c3c2b7")
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "open_end_vs_cad.png"), dpi=130, facecolor=SURF)
    print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk != "sector45_mg"} if isinstance(v, dict) else v
                      for k, v in out.items()}, indent=1))


if __name__ == "__main__":
    main()
