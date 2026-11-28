"""Figure for FEA c, d, e, g (computed, not measured)."""
import json
import math

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from fea_common import HERE, PAL, INK, INK2, style

R = HERE / "results"
c = json.loads((R / "c_ucs_all.json").read_text())
cf = json.loads((R / "c_ucs_frame.json").read_text()) if (R / "c_ucs_frame.json").exists() else c
d = json.loads((R / "d_blade.json").read_text())
e = json.loads((R / "e_tapper.json").read_text())
g = json.loads((R / "g_tripod_all.json").read_text())

fig, axs = plt.subplots(2, 3, figsize=(14, 8.2))

# c1: Janssen in the mould
ax = axs[0, 0]
for j, pw in enumerate(("dry", "cohesive")):
    jj = [x for x in c["janssen"] if x["powder"] == pw and x["sigma0_Pa"] == 2000.0][0]
    ax.plot(jj["sigma_v_Pa"], jj["z_mm"], color=PAL[j], lw=2, label=f"σv, {pw}")
    ax.plot(jj["sigma_h_Pa"], jj["z_mm"], color=PAL[j], lw=2, ls="--", label=f"σh (wall), {pw}")
ax.invert_yaxis()
style(ax, "c. Mould: Janssen under a 2 kPa top load", "stress (Pa)", "depth below the piston (mm)")
ax.legend(frameon=False, fontsize=8, loc="lower right")

# c2: compliance budget of the UCS force loop
ax = axs[0, 1]
pl = [x for x in cf["platen"] if x["E"] == 3500.0][-1]["compliance_um_per_N"]
bs = [x for x in cf["base"] if x["support"] == "bench" and x["E"] == 3500.0][-1]["frame_compliance_um_per_N"]
bc = [x for x in cf["base"] if x["support"] == "corners"][-1]["frame_compliance_um_per_N"]
cell = cf["tal221"]
samp = cf["sample"]
names = ["platen\nbracket", "base +\ncolumn", "TAL221\n(estimate)", "sample to\nfailure"]
lo = [pl, min(abs(bs), abs(bc)), cell["range_um_per_N"][0], min(s["compliance_um_per_N"] for s in samp)]
hi = [pl, max(abs(bs), abs(bc)), cell["range_um_per_N"][1], max(s["compliance_um_per_N"] for s in samp)]
for i, (a, b) in enumerate(zip(lo, hi)):
    ax.plot([i, i], [a, b], color=PAL[i], lw=10, solid_capstyle="round")
    ax.text(i + 0.14, math.sqrt(a * b), f"{a:.3g}" + ("" if b == a else f"–{b:.3g}"), va="center", fontsize=8, color=INK)
ax.set_yscale("log")
ax.set_xticks(range(4))
ax.set_xticklabels(names, fontsize=8)
ax.set_xlim(-0.5, 3.9)
style(ax, "c. UCS force loop: compliance (µm per N)", None, "µm per N (log)")

# d: blade gap change per N and at the estimated spreading force
ax = axs[0, 2]
fe = [x for x in d["fea"] if x["E"] == 3500.0][-1]
fz = fe["Fz_up_1N"]["uz_centre_um"]
fy = fe["Fy_drag_1N"]["uz_centre_um"]
F = np.logspace(-3, 1, 50)
ax.loglog(F, np.abs(fz) * F, color=PAL[0], lw=2, label=f"lift on the edge: {abs(fz):.1f} µm/N")
ax.loglog(F, np.abs(fy) * F, color=PAL[1], lw=2, label=f"drag on the edge: {abs(fy):.1f} µm/N")
for k, (pw, v) in enumerate(d["spreading_force"].items()):
    ax.plot([v["drag_N"]], [abs(fy) * v["drag_N"]], "o", color=PAL[1], ms=8)
    ax.plot([v["lift_N"]], [abs(fz) * v["lift_N"]], "o", color=PAL[0], ms=8)
ax.axhline(d["rods"]["gap_variation_um"], color=INK2, lw=1, ls="--")
ax.text(1.2e-3, d["rods"]["gap_variation_um"] * 1.25, f"guide-rod sag along the stroke {d['rods']['gap_variation_um']:.1f} µm",
        color=INK2, fontsize=8)
ax.axhline(10.0, color=INK2, lw=1, ls=":")
ax.text(1.2e-3, 12.5, "10 µm = 5 % of a 0.2 mm gap", color=INK2, fontsize=8)
ax.annotate("passive earth\npressure estimates", (6e-3, abs(fy) * 6e-3), xytext=(2e-2, 2e-3), fontsize=8, color=INK2,
            arrowprops=dict(arrowstyle="-", color=INK2, lw=0.8))
style(ax, "d. Blade gap change vs force on the edge", "force (N)", "gap change (µm)")
ax.legend(frameon=False, fontsize=8, loc="upper left")

# e: tapper peak force and deceleration
ax = axs[1, 0]
for j, El in enumerate(("E 2.3 GPa", "E 3.5 GPa")):
    rows = [x for x in e["impact"] if x["E"] == El and x["h_mm"] == 3.0]
    ax.plot([r["m_g"] for r in rows], [r["F_peak_N"] for r in rows], "o-", color=PAL[j], lw=2, ms=7, label=f"peak force, {El}")
ax2_vals = [x for x in e["impact"] if x["E"] == "E 2.3 GPa" and x["h_mm"] == 3.0]
for r in ax2_vals:
    ax.annotate(f"{r['a_peak_g']:.0f} g, {r['contact_ms']:.2f} ms", (r["m_g"], r["F_peak_N"]), textcoords="offset points",
                xytext=(0, -14), ha="center", fontsize=7, color=INK2)
style(ax, "e. Tapper impact (3 mm drop, flat PLA on the anvil)", "falling mass (g)", "peak contact force (N)")
ax.legend(frameon=False, fontsize=8, loc="upper left")

# e2: stresses vs fatigue
ax = axs[1, 1]
st = e["stress"][-1]
edge = e["edge_impact"]
labels = ["carriage body\n(away from face)", "striker face\n(flat contact)"] + [f"anvil edge r {x['R_eq_mm']:.1f}\n(tilted, Hertz p0)" for x in edge[:2]]
vals = [st["s1_max_away_MPa"], st["vm_max_MPa"]] + [x["p0_MPa"] for x in edge[:2]]
ax.bar(range(len(vals)), vals, color=[PAL[0], PAL[0], PAL[7], PAL[7]], width=0.6)
ax.axhline(15, color=INK2, ls="--", lw=1)
ax.text(-0.3, 17, "fatigue limit 15 MPa (assumed)", fontsize=8, color=INK2)
ax.axhline(50, color=INK2, ls=":", lw=1)
ax.text(-0.3, 55, "strength 50 MPa", fontsize=8, color=INK2)
ax.set_yscale("log")
ax.set_xticks(range(len(vals)))
ax.set_xticklabels(labels, fontsize=7)
for i, v in enumerate(vals):
    ax.text(i, v * 1.12, f"{v:.0f}" if v >= 10 else f"{v:.1f}", ha="center", fontsize=8, color=INK)
style(ax, "e. Stress per tap (MPa, log)", None, "MPa")

# g: tripod tip force vs leg height (test 10) and test 5 CG
ax = axs[1, 2]
Hs = sorted(int(k) for k in g["tip"].keys())
ax.plot(Hs, [g["tip"][str(H)]["test10_faraday"]["F_tip_edge_N"] for H in Hs], "o-", color=PAL[0], lw=2, ms=7,
        label="test 10, push toward an edge")
ax.plot(Hs, [g["tip"][str(H)]["test10_faraday"]["F_tip_leg_N"] for H in Hs], "s-", color=PAL[1], lw=2, ms=7,
        label="test 10, push toward a leg")
ax.plot(Hs, [g["tip"][str(H)]["test5_cup_holder_toward_leg"]["F_tip_at_top_N"] for H in Hs], "^-", color=PAL[7], lw=2,
        ms=7, label="test 5 holder pointed at a leg")
ax.axhline(0.3, color=INK2, ls="--", lw=1)
ax.text(Hs[0], 0.32, "0.3 N: a BNC or STEMMA cable tug", fontsize=8, color=INK2)
ax.set_ylim(0, 1.0)
style(ax, "g. Tripod: lateral force at the top that tips it", "leg length (mm)", "force (N)")
ax.legend(frameon=False, fontsize=8, loc="upper right")
fig.tight_layout()
fig.savefig(HERE / "fea_cdeg.png", dpi=150)
print("saved")
