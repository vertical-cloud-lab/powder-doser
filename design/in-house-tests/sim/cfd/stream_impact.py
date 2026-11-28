"""Tests 1 and 10: grain speed at impact and the air the stream drags, from stream_model.

Drops: 12 mm (outlet to the heap on the test-1 pedestal), 50 and 77 mm (outlet to the Faraday cup's
floor: 10 mm to the lid + 67 mm inside), 100 mm. Feeds 0.1 and 1 g/s. Grains: the two reference
powders (#196) and the battery powders (d50, true density, bulk density from the #196 CSV).
'single' = one grain released at the outlet speed into still air; 'stream' = the same grain size
inside the stream (air co-flow from the plume model); 'vacuum' = sqrt(v0^2 + 2 g s).
Writes stream.json and stream.png.
"""
import json

import numpy as np

import stream_model as sm
from orifice_air import battery
import plotstyle as ps

DROPS = [0.012, 0.050, 0.077, 0.100]


def main():
    powders = [dict(name="salt-like dry (ref)", rho_b=1249.0, rho_p=2165.0, d50=425e-6),
               dict(name="cohesive (ref, Bo 5)", rho_b=1023.0, rho_p=2165.0, d50=425e-6)] + battery()
    out = dict(drops_mm=[d * 1e3 for d in DROPS], powders={})
    for p in powders:
        row = {}
        for mdot in (1e-4, 1e-3):
            st = sm.stream(mdot, p["d50"], p["rho_p"], p["rho_b"], s_end=0.1001)
            sg = sm.single_grain(p["d50"], p["rho_p"], st["v0"], 0.1001)
            r = {}
            for s in DROPS:
                vs = float(np.interp(s, st["s"], st["v"]))
                v1 = float(sg.sol(s)[0])
                vv = float(sm.vacuum_speed(st["v0"], s))
                r[f"{s*1e3:.0f}"] = dict(v_vacuum=vv, v_single=v1, v_stream=vs,
                                         single_over_vacuum=v1 / vv, stream_over_vacuum=vs / vv,
                                         air_speed_in_stream=float(np.interp(s, st["s"], st["u"])),
                                         entrained_Q_mL_s=float(np.interp(s, st["s"], st["Q"]) * 1e6),
                                         plume_radius_mm=float(np.interp(s, st["s"], st["b"]) * 1e3))
            row[f"{mdot*1e3:.1f}_g_s"] = dict(v_outlet=float(st["v0"]), drops=r)
        tp = sm.tau_p(p["d50"], p["rho_p"])
        vt = p["rho_p"] * p["d50"] ** 2 * sm.G / (18 * sm.MU)
        row["tau_p_s"] = float(tp)
        row["stokes_terminal_m_s"] = float(vt)
        out["powders"][p["name"]] = row
    json.dump(out, open("stream.json", "w"), indent=1)

    # figure
    show = ["salt-like dry (ref)", "white-rice-flour", "alsi10mg", "silicon-325"]
    fig, axs = ps.plt.subplots(1, 2, figsize=(10, 4))
    s = np.linspace(0, 0.1, 200)
    for k, name in enumerate(show):
        p = [q for q in powders if q["name"] == name][0]
        st = sm.stream(1e-3, p["d50"], p["rho_p"], p["rho_b"], s_end=0.1001)
        sg = sm.single_grain(p["d50"], p["rho_p"], st["v0"], 0.1001)
        lab = f"{name} ({p['d50']*1e6:.0f} um)"
        axs[0].plot(st["s"] * 1e3, st["v"], color=ps.CAT[k], lw=2, label=lab + ", in a 1 g/s stream")
        axs[0].plot(s * 1e3, [sg.sol(x)[0] for x in s], color=ps.CAT[k], lw=1.2, ls="--")
        for mdot, ls in ((1e-3, "-"), (1e-4, ":")):
            st2 = sm.stream(mdot, p["d50"], p["rho_p"], p["rho_b"], s_end=0.1001)
            axs[1].plot(st2["s"] * 1e3, st2["Q"] * 1e6, color=ps.CAT[k], lw=2 if ls == "-" else 1.5, ls=ls,
                        label=f"{name}, {mdot*1e3:.1f} g/s")
    axs[0].plot(s * 1e3, sm.vacuum_speed(0.0, s), color=ps.TEXT, lw=1.2, ls="-.", label="no air, from rest")
    axs[0].set_xlabel("drop below the outlet (mm)")
    axs[0].set_ylabel("grain speed (m/s)")
    axs[0].set_title("Grain speed: in the stream (solid), alone (dashed)", loc="left", fontsize=9)
    axs[1].set_xlabel("drop below the outlet (mm)")
    axs[1].set_ylabel("air dragged down by the stream (mL/s)")
    axs[1].set_yscale("log")
    axs[1].set_title("Entrained air, free stream (plume model, alpha 0.1)", loc="left", fontsize=9)
    for a in axs:
        ps.tidy(a)
    axs[0].legend(fontsize=7)
    axs[1].legend(fontsize=6.5, ncol=1)
    fig.text(0.01, 0.005, "Computed, not measured.", color=ps.TEXT2, fontsize=8)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig("stream.png", dpi=150)
    for name in show + ["cohesive (ref, Bo 5)"]:
        r = out["powders"][name]
        print(name, {k: (round(v["single_over_vacuum"], 3), round(v["stream_over_vacuum"], 3),
                         round(v["entrained_Q_mL_s"], 1)) for k, v in r["1.0_g_s"]["drops"].items()})


if __name__ == "__main__":
    main()
