"""Test 5 orifice cup: air counter-flow through a dilating bed for fine powders.

Beverloo:  W_B = C rho_b sqrt(g) (D - k d)^2.5,  C = 0.58, k = 1.5.
Crewdson, Ormond and Nedderman (1977) showed that fine grains discharge more slowly than Beverloo
because an interstitial pressure gradient at the orifice opposes gravity:
    W = W_B sqrt(1 - |dp/dz| / (rho_b g)).
Here the gradient is computed, not measured: the bed dilates from its poured void ratio e0 to e0 + de
at the orifice, so air must flow into the dilation zone at Q_air = (W / rho_p) de.  The zone is fed
in parallel through the orifice zone (length L_o = D/2, area A_o, Carman-Kozeny permeability at the
dilated porosity) and down through the packed bed above (height H, cup area A_cup):
    |dp/dz| = (Q_air R_bot / L_o) * R_top / (R_top + R_bot),   R = mu L / (k A).
"Deep bed" bound: R_top >> R_bot (all air through the orifice, as in a tall hopper).
W follows from the quadratic W = W_B sqrt(1 - beta W).  Grain size where W/W_B = 0.95 and 0.80.
Writes orifice_air.json and orifice_air.png.
"""
import json
import subprocess

import numpy as np
from scipy.optimize import brentq

import plotstyle as ps

G, MU = 9.81, 1.85e-5
C_BEV, K_BEV = 0.58, 1.5
D_CUP = 0.025
ORIFICES = [1.0e-3, 1.5e-3, 2.0e-3, 2.54e-3, 3.0e-3, 4.0e-3, 5.08e-3, 6.0e-3]


def carman(d, eps):
    return d * d * eps ** 3 / (180 * (1 - eps) ** 2)


def beverloo(D, d, rho_b):
    x = max(D - K_BEV * d, 0.0)
    return C_BEV * rho_b * np.sqrt(G) * x ** 2.5


def ratio(D, d, rho_p, rho_b, deps=0.04, H=0.020, deep=False):
    """W / W_B for one powder and orifice."""
    eps0 = 1 - rho_b / rho_p
    eps_o = min(eps0 + deps, 0.95)
    de = eps_o / (1 - eps_o) - eps0 / (1 - eps0)
    Ao = np.pi * D * D / 4
    Lo = D / 2
    k_o = carman(d, eps_o)
    k_b = carman(d, eps0)
    Rbot = MU * Lo / (k_o * Ao)
    Rtop = MU * H / (k_b * np.pi * D_CUP ** 2 / 4)
    frac = 1.0 if deep else Rtop / (Rtop + Rbot)
    # |dp/dz| = beta_p * W  with  Q_air = W de / rho_p
    beta = (de / rho_p) * Rbot / Lo * frac / (rho_b * G)
    WB = beverloo(D, d, rho_b)
    if WB <= 0:
        return float("nan"), WB          # D < k d: Beverloo has no flow at all (not an air effect)
    W = (-beta * WB ** 2 + np.sqrt(beta ** 2 * WB ** 4 + 4 * WB ** 2)) / 2
    return W / WB, WB


def d_crit(D, rho_p, rho_b, target, **kw):
    f = lambda logd: ratio(D, np.exp(logd), rho_p, rho_b, **kw)[0] - target
    lo, hi = np.log(1e-6), np.log(min(D / K_BEV * 0.999, 2e-3))
    if f(hi) < 0:
        return None
    if f(lo) > 0:
        return 0.0
    return float(np.exp(brentq(f, lo, hi)))


def battery():
    txt = subprocess.run(["git", "show", "e8811bd:docs/physics-simulations/runs/heldout-powders/data/"
                          "literature_powder_properties.csv"], capture_output=True, text=True,
                         cwd="/home/runner/work/powder-doser/powder-doser").stdout
    rows = [l.split(",") for l in txt.strip().splitlines()]
    hdr = rows[0]
    out = []
    for r in rows[1:]:
        d = dict(zip(hdr, r))
        out.append(dict(name=d["powder_id"], rho_b=float(d["bulk_density_g_ml"]) * 1e3,
                        rho_p=float(d["true_density_g_cm3"]) * 1e3, d50=float(d["d50_um"]) * 1e-6))
    return out


def main():
    powders = [dict(name="salt-like dry (ref)", rho_b=1249.0, rho_p=2165.0, d50=425e-6),
               dict(name="cohesive (ref, Bo 5)", rho_b=1023.0, rho_p=2165.0, d50=425e-6)] + battery()
    res = dict(model=__doc__.split("Writes")[0].strip(), C=C_BEV, k=K_BEV, cases={})
    for deep in (False, True):
        for deps in (0.02, 0.04, 0.06):
            key = f"{'deep' if deep else 'cup_H20mm'}_deps{deps:.2f}"
            tab = {}
            for p in powders:
                row = {}
                for D in ORIFICES:
                    r, WB = ratio(D, p["d50"], p["rho_p"], p["rho_b"], deps=deps, deep=deep)
                    row[f"{D*1e3:.2f}"] = dict(W_over_WB=float(r), W_B_g_s=float(WB * 1e3))
                tab[p["name"]] = row
            crit = {}
            for D in ORIFICES:
                crit[f"{D*1e3:.2f}"] = dict(
                    d_5pct_um_rho2165_eps0p42=_um(d_crit(D, 2165.0, 2165.0 * 0.58, 0.95, deps=deps, deep=deep)),
                    d_20pct_um_rho2165_eps0p42=_um(d_crit(D, 2165.0, 2165.0 * 0.58, 0.80, deps=deps, deep=deep)),
                    d_5pct_um_rho1450_eps0p53=_um(d_crit(D, 1450.0, 680.0, 0.95, deps=deps, deep=deep)),
                    d_20pct_um_rho1450_eps0p53=_um(d_crit(D, 1450.0, 680.0, 0.80, deps=deps, deep=deep)))
            res["cases"][key] = dict(powders=tab, critical_size=crit)
    # bed-height dependence (the cup drains from about 40 mm of powder to zero)
    hd = {}
    for p in powders:
        if p["name"] not in ("silicon-325", "alsi10mg", "carboxymethyl-cellulose", "white-rice-flour"):
            continue
        hd[p["name"]] = {f"D{D*1e3:.2f}": {f"H{H*1e3:.0f}": round(float(ratio(D, p["d50"], p["rho_p"], p["rho_b"],
                                                                                 deps=0.04, H=H)[0]), 3)
                                             for H in (0.005, 0.010, 0.020, 0.040)}
                         for D in (2.54e-3, 5.08e-3)}
    res["bed_height_dependence_deps0.04"] = hd
    print("bed height", hd)
    json.dump(res, open("orifice_air.json", "w"), indent=1)

    # figure: W/W_B vs d for D = 2.54 and 5.08 mm, cup (H = 20 mm) and deep-bed bound, de = 0.04
    fig, axs = ps.plt.subplots(1, 2, figsize=(10, 4))
    dd = np.logspace(np.log10(5e-6), np.log10(6e-4), 200)
    for k, D in enumerate((1.5e-3, 3.0e-3, 6.0e-3)):
        for ax, deep in zip(axs, (False, True)):
            y = [ratio(D, d, 2165.0, 2165 * 0.58, deps=0.04, deep=deep)[0] for d in dd]
            ax.plot(dd * 1e6, y, color=ps.CAT[k], lw=2, label=f"orifice {D*1e3:.1f} mm")
    for ax, t in zip(axs, ("Orifice cup, bed 20 mm deep (air also enters from above)",
                           "Deep-bed bound (all air through the orifice)")):
        ax.set_xscale("log")
        ax.axhline(0.95, color=ps.TEXT2, lw=0.8, ls="--")
        ax.axhline(0.80, color=ps.TEXT2, lw=0.8, ls=":")
        ax.text(6, 0.955, "-5 %", color=ps.TEXT2, fontsize=8)
        ax.text(6, 0.805, "-20 %", color=ps.TEXT2, fontsize=8)
        ax.set_xlabel("grain size d50 (um)  [rho_p 2165 kg/m³, porosity 0.42, dilation +0.04]")
        ax.set_ylim(0, 1.05)
        ax.set_title(t, loc="left", fontsize=9)
        ps.tidy(ax)
    axs[0].set_ylabel("flow rate / Beverloo flow rate")
    axs[0].legend(fontsize=8, loc="lower right")
    axs[1].legend(fontsize=8, loc="lower right")
    fig.text(0.01, 0.005, "Computed, not measured (Carman-Kozeny + Crewdson-type correction).",
             color=ps.TEXT2, fontsize=8)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig("orifice_air.png", dpi=150)
    # print a compact summary
    for key in ("cup_H20mm_deps0.04", "deep_deps0.04"):
        print(key)
        for D in ("1.00", "3.00", "6.00"):
            print("  D", D, res["cases"][key]["critical_size"][D])
        for name in ("salt-like dry (ref)", "silicon-325", "alsi10mg", "carboxymethyl-cellulose", "xanthan-gum",
                     "white-rice-flour"):
            r = res["cases"][key]["powders"][name]
            print("  ", name, {D: round(r[D]["W_over_WB"], 3) for D in ("1.50", "2.54", "5.08")})


def _um(x):
    return None if x is None else round(x * 1e6, 1)


if __name__ == "__main__":
    main()
