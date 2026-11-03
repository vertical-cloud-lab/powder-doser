"""Figures and animation for heldout-powders (reads predictions.json, doser_path.json, aor_path.json and,
for the animation, the particle dumps in the scratch folders)."""
from __future__ import annotations

import json
import math
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ligcommon as L  # noqa: E402
import predict as P  # noqa: E402

SCRATCH = os.environ.get("SCRATCH", "/tmp/sims-scratch/heldout-powders")
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
SHORT = {"alsi10mg": "AlSi10Mg", "silicon-110-200": "Si 75–150 µm", "sodium-sulfate": "Na₂SO₄",
         "calcium-lactate": "Ca lactate", "barium-chloride": "BaCl₂", "xanthan-gum": "xanthan",
         "salt": "salt", "carboxymethyl-cellulose": "CMC", "white-rice-flour": "white rice flour",
         "sodium-alginate": "alginate", "brown-rice-flour": "brown rice flour", "silicon-325": "Si <44 µm"}
U_LABEL = {-1.0: "P0\nsmooth", 0.0: "P1\nsalt"}
# label placement for crowded points: (dx, dy in points, horizontal alignment)
LABEL_OFFSETS = {
    ("salt", "45"): (-6, 2, "right"), ("sodium-sulfate", "45"): (6, -9, "left"), ("alsi10mg", "45"): (5, 4, "left"),
    ("barium-chloride", "45"): (-6, -9, "right"), ("xanthan-gum", "45"): (6, -9, "left"),
    ("silicon-110-200", "45"): (5, 4, "left"), ("carboxymethyl-cellulose", "45"): (-6, -9, "right"),
    ("salt", "22p5"): (6, -9, "left"), ("sodium-sulfate", "22p5"): (-6, 4, "right"), ("alsi10mg", "22p5"): (-6, 4, "right"),
    ("barium-chloride", "22p5"): (-4, 6, "right"), ("xanthan-gum", "22p5"): (6, -9, "left"),
    ("silicon-110-200", "22p5"): (5, 5, "left"), ("calcium-lactate", "22p5"): (6, 3, "left"),
}


def u_ticks(us):
    return [U_LABEL.get(u, f"{u:g}") for u in us]


def fig_path(chain, aor_rows, doser_rows, powders, shift):
    fig, axs = plt.subplots(1, 2, figsize=(11.5, 4.4))
    fig.patch.set_facecolor(L.SURF)
    # (a) repose angle along the path
    ax = axs[0]
    L.style_axes(ax)
    rows = sorted(aor_rows, key=lambda r: P.u_of(r["point"]))
    u = np.array([P.u_of(r["point"]) for r in rows])
    ax.plot(u, [r["angle_iso_deg"] for r in rows], "-o", color=BLUE, lw=2, ms=6, label="ISO apex, atan(H/R)")
    ax.plot(u, [r["angle_fit_deg"] for r in rows], "--s", color=L.INK2, lw=1.2, ms=5, label="profile fit")
    for p in powders:
        a = p["aor"] - shift
        ax.plot([u[-1] + 0.35, u[-1] + 0.75], [a, a], color=ORANGE if p["mg_rev"]["45"] < P.FLOW_THRESHOLD else AQUA, lw=2)
    ax.text(u[-1] + 0.55, 54.5, f"literature AoR\n− {shift:g}°", fontsize=7, color=L.INK2, ha="center")
    ax.plot([], [], color=AQUA, lw=2, label="literature AoR − offset: powders that convey (≥ 50 mg/rev at 45°)")
    ax.plot([], [], color=ORANGE, lw=2, label="… powders that do not")
    ax.set_xticks(u)
    ax.set_xticklabels(u_ticks(u), fontsize=7)
    ax.set_xlim(u[0] - 0.4, u[-1] + 1.0)
    ax.set_ylim(5, 60)
    ax.set_xlabel("path point (k = SJKR cohesion energy density, kJ/m³)", fontsize=8)
    ax.set_ylabel("DEM repose angle (deg)", fontsize=8)
    ax.set_title("(a) Poured angle of repose along the path (4000 grains, 12 mm base)", fontsize=9, color=L.INK)
    ax.legend(fontsize=7, frameon=False, loc="upper left")
    # Bond numbers on top
    top = ax.secondary_xaxis("top")
    top.set_xticks([x for x in u if x > 0])
    top.set_xticklabels([f"{L.bond_number_sjkr(x * 1000.0, 0.425e-3)[0]:.2g}" for x in u if x > 0], fontsize=6)
    top.set_xlabel("pull-off Bond number of a 0.425 mm pair", fontsize=7, color=L.INK2)
    # (b) doser along the path
    ax = axs[1]
    L.style_axes(ax)
    for key, col, lab in (("45", BLUE, "45° tilt"), ("22p5", L.INK2, "22.5° tilt")):
        rs = sorted([r for r in doser_rows if r.get("tilt_deg") is not None and abs(r["tilt_deg"] - P.TILTS[key]) < 1e-6
                     and r.get("rpm", 30) == 30 and P.dem_rate(r) is not None], key=lambda r: P.u_of(r["path_point"]))
        if not rs:
            continue
        uu = [P.u_of(r["path_point"]) for r in rs]
        yy = [max(P.dem_rate(r), P.FLOOR) for r in rs]
        ax.plot(uu, yy, "-o", color=col, lw=2, ms=6, label=f"DEM twin, {lab}, 30 rpm")
        for r in rs:
            if P.dem_rate(r) < P.FLOOR:
                ax.annotate("0", (P.u_of(r["path_point"]), P.FLOOR), textcoords="offset points", xytext=(4, 4), fontsize=7, color=col)
    salt = next(p for p in powders if p["powder_id"] == "salt")
    us_all = sorted({P.u_of(r["path_point"]) for r in doser_rows if r.get("path_point")})
    ax.axhline(salt["mg_rev"]["45"], color=BLUE, lw=1, ls=":")
    ax.text(us_all[-1], salt["mg_rev"]["45"] * 1.15, f"salt measured, 45°: {salt['mg_rev']['45']:.0f} mg/rev", fontsize=7, color=L.INK2, ha="right")
    ax.axhline(salt["mg_rev"]["22p5"], color=L.INK2, lw=1, ls=":")
    ax.text(us_all[-1], salt["mg_rev"]["22p5"] * 0.62, f"salt measured, 22.5°: {salt['mg_rev']['22p5']:.0f} mg/rev", fontsize=7, color=L.INK2, ha="right")
    ax.set_yscale("log")
    ax.set_ylim(0.05, 1000)
    us = sorted({P.u_of(r["path_point"]) for r in doser_rows if r.get("path_point")})
    ax.set_xticks(us)
    ax.set_xticklabels(u_ticks(us), fontsize=7)
    ax.set_xlabel("path point (k = SJKR cohesion energy density, kJ/m³)", fontsize=8)
    ax.set_ylabel("mg per revolution (after the first ¼ rev)", fontsize=8)
    ax.set_title("(b) #180 auger twin along the same path (salt-sized grains)", fontsize=9, color=L.INK)
    ax.legend(fontsize=7, frameon=False, loc="lower left")
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "dem_path.png"), dpi=120, facecolor=L.SURF)
    plt.close(fig)


def fig_aor_vs_dose(chain, powders, summary):
    fig, axs = plt.subplots(1, 2, figsize=(12, 4.8), sharey=True)
    fig.patch.set_facecolor(L.SURF)
    agrid = np.linspace(26, 50, 241)
    for ax, key in zip(axs, ("45", "22p5")):
        L.style_axes(ax)
        aor = np.array([p["aor"] for p in powders])
        y = np.array([max(p["mg_rev"][key], P.FLOOR) for p in powders])
        lo = np.array([p["aor_lo"] for p in powders])
        hi = np.array([p["aor_hi"] for p in powders])
        ax.errorbar(aor, y, xerr=[aor - lo, hi - aor], fmt="none", ecolor="#c9c8c3", elinewidth=1.5, capsize=0, zorder=1)
        ax.scatter(aor, y, s=46, color=L.INK, zorder=3, label="measured (Sam's battery, protocol C, 30 rpm)")
        for p, a, yy in zip(powders, aor, y):
            dx, dy, ha = LABEL_OFFSETS.get((p["powder_id"], key), (5, 3, "left"))
            ax.annotate(SHORT[p["powder_id"]], (a, yy), textcoords="offset points", xytext=(dx, dy), ha=ha,
                        fontsize=6.5, color=L.INK2)
        # all-powder OLS on AoR (what the baseline fits)
        b = P.ols(aor, np.log10(y))
        ax.plot(agrid, 10 ** (b[0] + b[1] * agrid), color=ORANGE, lw=2, label="linear fit of log mg/rev on AoR (all 12)")
        if chain is not None and key in chain.doser:
            fits = summary["tilts"][key]["fitted"]["dem_shift"]
            s_med = float(np.median(fits)) if fits else 0.0
            for s, ls, lab in ((0.0, "--", "DEM chain, no fitted parameter"),
                               (s_med, "-", f"DEM chain, AoR offset {s_med:g}° (median of the LOPO fits)")):
                yy = [10 ** chain.logmg(chain.u_from_aor(a - s), key) for a in agrid]
                ax.plot(agrid, yy, ls, color=BLUE, lw=2, label=lab)
        ax.set_yscale("log")
        ax.set_ylim(0.05, 1500)
        ax.set_xlim(25, 56)
        ax.set_xlabel("literature angle of repose (deg); grey bars: range of the literature values", fontsize=8)
        ax.set_title(f"{'45' if key == '45' else '22.5'}° tilt", fontsize=9, color=L.INK)
    axs[0].set_ylabel("mg per revolution (values below 0.1 drawn at 0.1)", fontsize=8)
    axs[0].legend(fontsize=7, frameon=False, loc="lower left")
    fig.suptitle("Dosing rate against literature repose angle: the 12 powders, an AoR regression and the DEM chain (DEM curves at salt density)",
                 fontsize=9.5, color=L.INK)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "heldout_aor_vs_dose.png"), dpi=120, facecolor=L.SURF)
    plt.close(fig)


def fig_lopo(per_powder, summary):
    fig, axs = plt.subplots(1, 2, figsize=(11, 5.0))
    fig.patch.set_facecolor(L.SURF)
    models = [("aor_ols", ORANGE, "o", "AoR regression"), ("dem_shift", BLUE, "D", "DEM chain, fitted AoR offset"),
              ("bev0", AQUA, "s", "Beverloo through the annulus, no fit")]
    for ax, key in zip(axs, ("45", "22p5")):
        L.style_axes(ax)
        lim = (-1.3, 3.3)
        ax.plot(lim, lim, color=L.INK2, lw=1)
        ax.fill_between(lim, [lim[0] - 0.477, lim[1] - 0.477], [lim[0] + 0.477, lim[1] + 0.477], color="#eeeeea", zorder=0)
        sc = summary["tilts"][key]["scores"]
        for m, col, mk, lab in models:
            if m not in sc:
                continue
            xs, ys = [], []
            for pid, r in per_powder.items():
                v = r.get("lopo_log10_pred", {}).get(key, {}).get(m)
                if v is None:
                    continue
                xs.append(P.logy(r["measured"][key]))
                ys.append(v)
            ax.scatter(xs, ys, s=44, marker=mk, color=col, edgecolor=L.SURF, linewidth=1.2, zorder=3,
                       label=f"{lab}: RMSE {sc[m]['rmse_log10']:.2f}, ρ {sc[m]['spearman_rho']:+.2f}")
        ax.set_xlim(lim)
        ax.set_ylim(lim)
        tk = [-1, 0, 1, 2, 3]
        ax.set_xticks(tk)
        ax.set_yticks(tk)
        ax.set_xticklabels(["0.1", "1", "10", "100", "1000"])
        ax.set_yticklabels(["0.1", "1", "10", "100", "1000"])
        ax.set_aspect("equal")
        ax.set_xlabel("measured mg/rev", fontsize=8)
        ax.set_ylabel("predicted for the held-out powder (mg/rev)", fontsize=8)
        ax.set_title(f"Leave-one-powder-out, {'45' if key == '45' else '22.5'}° tilt (band: within 3×)", fontsize=9, color=L.INK)
        ax.legend(fontsize=6.8, frameon=False, loc="upper left")
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "heldout_lopo.png"), dpi=120, facecolor=L.SURF)
    plt.close(fig)


def animation(cases=("d45_P1", "d45_k1500", "d45_k3000")):
    labels = {c: c for c in cases}
    for c in cases:
        f = os.path.join(SCRATCH, c, "case.json")
        if os.path.exists(f):
            cfg = json.load(open(f))["cfg"]
            labels[c] = f"k = {cfg['ced'] / 1000:g} kJ/m³" + (" (salt twin)" if cfg["ced"] == 0 else "")
    series = {c: L.dump_series(os.path.join(SCRATCH, c, "dump", "p.*.txt")) for c in cases}
    n = min(len(v) for v in series.values()) if all(series.values()) else 0
    if n == 0:
        return False
    dts = {c: json.load(open(os.path.join(SCRATCH, c, "case.json")))["dt"] for c in cases}
    outs = {c: np.loadtxt(os.path.join(SCRATCH, c, "outflow.txt"), ndmin=2) for c in cases}
    frames = []
    for i in range(n):
        fig, axs = plt.subplots(1, len(cases), figsize=(3.4 * len(cases), 4.6))
        fig.patch.set_facecolor(L.SURF)
        t = 0.0
        for ax, c in zip(axs, cases):
            L.style_axes(ax)
            step, d = L.read_dump(series[c][i])
            t = step * dts[c]
            mm = np.abs(d["y"]) < 1.0e-3
            sp = np.sqrt(d["vx"] ** 2 + d["vy"] ** 2 + d["vz"] ** 2)[mm]
            L.draw_grains(ax, d["x"][mm] * 1e3, d["z"][mm] * 1e3, d["radius"][mm] * 1e3, c=sp, cmap=L.speed_cmap(), vmax=0.1)
            A = outs[c]
            m_open = float(np.interp(0.12, A[:, 0], A[:, 1])) * 1e6
            m_now = float(np.interp(t, A[:, 0], A[:, 1])) * 1e6
            ax.set_aspect("equal")
            ax.set_xlim(-14, 12)
            ax.set_ylim(-6, 30)
            ax.set_xticks([])
            ax.set_yticks([])
            ax.set_title(f"{labels[c]}\n{max(m_now - m_open, 0):.1f} mg out since the exit opened", fontsize=8, color=L.INK)
        phase = "settling, exit plugged" if t < 0.12 else f"{(t - 0.12) / 2.0 * 360:.0f}° of auger rotation"
        fig.suptitle(f"#180 twin at 45° tilt, 30 rpm, slice |y| < 1 mm, t = {t:.2f} s ({phase}); colour = grain speed, 0–0.1 m/s",
                     fontsize=8, color=L.INK)
        fig.tight_layout()
        frames.append(L.fig_to_array(fig))
        plt.close(fig)
    L.save_animation(frames, os.path.join(HERE, "dem_path_doser.gif"), os.path.join(HERE, "dem_path_doser.mp4"), fps=6, max_width=900)
    return True


def main():
    summary_all = json.load(open(os.path.join(HERE, "predictions.json")))
    summary, per_powder = summary_all["summary"], summary_all["per_powder"]
    powders = P.load_powders()
    doser = json.load(open(os.path.join(HERE, "doser_path.json")))
    aor = [r for r in json.load(open(os.path.join(HERE, "aor_path.json"))) if r.get("rc") == 0]
    chain = P.DemChain(doser, aor)
    fits = summary["tilts"]["45"]["fitted"].get("dem_shift") or [0.0]
    fig_path(chain, aor, doser, powders, float(np.median(fits)))
    fig_aor_vs_dose(chain, powders, summary)
    fig_lopo(per_powder, summary)
    if "--no-anim" not in sys.argv:
        print("animation:", animation())


if __name__ == "__main__":
    main()
