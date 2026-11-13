#!/usr/bin/env python3
"""Figure and result.json for fem-druckerprager from /tmp/sims-scratch/fem-druckerprager outputs."""
import os, json
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.tri as mtri

OUT = os.path.dirname(os.path.abspath(__file__)); SCR = "/tmp/sims-scratch/fem-druckerprager"
R = json.load(open(f"{SCR}/raw_results.json")); rho, g = 1250.0, 9.81
fig, ax = plt.subplots(1, 3, figsize=(14, 4.2))
S = np.load(f"{SCR}/state_c20.npz")
gxy, eqp, XY, u = S["gxy"], S["eqp"], S["XY"], S["u"]
tri = mtri.Triangulation(gxy[:, 0] * 1e3, gxy[:, 1] * 1e3)
tc = ax[0].tripcolor(tri, np.log10(np.maximum(eqp, 1e-9)), shading="gouraud", cmap="magma", vmin=-7, vmax=np.log10(eqp.max() + 1e-12))
plt.colorbar(tc, ax=ax[0], label="log10 accumulated plastic multiplier (-)")
sc = 0.6e-3 / max(np.abs(u).max(), 1e-30)
ax[0].quiver(XY[::7, 0] * 1e3, XY[::7, 1] * 1e3, u[0::2][::7], u[1::2][::7], color="c", scale=1 / sc / 1e3, scale_units="xy", width=0.004)
ax[0].plot([0, 1.5], [0, 0], color="lime", lw=4, label="open slot (half, B/2 = 1.5 mm)")
ax[0].plot([1.5, 9], [0, 0], color="k", lw=4, label="rough floor")
ax[0].set_aspect("equal"); ax[0].set_xlabel("x from slot centre (mm)"); ax[0].set_ylabel("height above outlet (mm)")
ax[0].set_title("(a) c = 20 Pa, φ = 34°: last converged state\n(λ just below collapse); arrows = displacement", fontsize=9)
ax[0].legend(fontsize=7, loc="upper right")
cc = ["#1f6fb4", "#2a9d5c", "#d9622b", "#7b4fa0"]
for c, col in zip(R["cases"], cc):
    h = np.array(c["history"])
    ax[1].plot(h[:, 1] * 1e6, h[:, 0], "o-", ms=3, color=col, label=f"c = {c['cohesion_Pa']:.0f} Pa, φ = {c['phi_deg']:.0f}°: λc = {c['lam_collapse']:.2f}")
ax[1].axhline(1.0, color="k", ls="--", lw=1); ax[1].text(0.02, 1.03, "1 g", transform=ax[1].get_yaxis_transform())
ax[1].set_xlabel("slot-centre settlement (µm)"); ax[1].set_ylabel("gravity multiplier λ (-)")
ax[1].set_title("(b) load–settlement to the iteration-ceiling collapse", fontsize=9); ax[1].legend(fontsize=7)
B = np.linspace(0.5e-3, 6e-3, 100)
for c, col in zip(R["cases"], cc):
    if c["cohesion_Pa"] == 20.0:
        ax[2].plot(B * 1e3, rho * g * B / c["stability_number_N"], color=col, lw=2,
                   label=f"FEM, φ = {c['phi_deg']:.0f}° (N = {c['stability_number_N']:.2f})")
for phi, ls in [(34, "--"), (25, ":")]:
    s = np.sin(np.radians(phi)); cJ = rho * g * B * (1 - s) / (2 * np.cos(np.radians(phi)))
    ax[2].plot(B * 1e3, cJ, "k", ls=ls, lw=1, label=f"Jenike-type σc = ρgB (plane), φ = {phi}°")
ax[2].axvline(3.0, color="0.5", lw=1); ax[2].text(3.05, 2, "Ø3 mm exit", fontsize=7)
ax[2].axvline(1.07, color="0.5", lw=1, ls="-."); ax[2].text(1.1, 6, "annulus gap 1.07 mm", fontsize=7, rotation=90)
ax[2].set_xlabel("slot width B (mm)"); ax[2].set_ylabel("cohesion needed for a stable arch, c_crit (Pa)")
ax[2].set_title("(c) critical cohesion vs outlet width (ρ_b = 1250 kg/m³, 1 g)", fontsize=9); ax[2].legend(fontsize=7)
fig.suptitle("FEM, plane strain, associated Drucker–Prager (MC-matched), Q8 reduced integration — self-written numpy/scipy code", fontsize=10)
fig.tight_layout(); fig.savefig(f"{OUT}/fem_druckerprager.png", dpi=105); plt.close(fig)

base = [c for c in R["cases"] if c["phi_deg"] == 34.0]
Ns = np.array([c["stability_number_N"] for c in base])
c34 = rho * g * 3e-3 / Ns.mean(); s = np.sin(np.radians(34)); co = np.cos(np.radians(34))
sigc = 2 * c34 * co / (1 - s)
res = {"id": "fem-druckerprager", "method": "2D plane-strain small-strain elastoplastic FEM, associated Drucker-Prager (Mohr-Coulomb plane-strain match), trapdoor/arching collapse by gravity increase",
       "code": "self-written numpy/scipy FEM (run.py): Q8 serendipity, 2x2 reduced integration, closed-form DP return mapping, modified Newton with factorised elastic stiffness",
       "version": "numpy 2.5.4, scipy 1.18.1, python 3.12",
       "status": "ran", "wall_s": R["total_wall_s"], "cores": 1,
       "key_results": {"cases": [{k: v for k, v in c.items() if k != "history"} for c in R["cases"]],
                       "stability_number_phi34_mean": float(Ns.mean()), "stability_number_phi34_spread": float(Ns.max() - Ns.min()),
                       "c_crit_3mm_slot_phi34_Pa": float(c34), "sigma_c_crit_3mm_slot_phi34_Pa": float(sigc),
                       "ffc_threshold_at_sigma1_400Pa": float(400.0 / sigc),
                       "jenike_type_c_crit_3mm_phi34_Pa": float(rho * g * 3e-3 * (1 - s) / (2 * co))},
       "notes": "Collapse = no convergence (residual 1e-4) within 800 modified-Newton iterations, bracketed by 4 bisections; sigma1 = 400 Pa is an assumed consolidation stress taken from the Janssen estimate in analytic-orifice-screw."}
json.dump(res, open(f"{OUT}/result.json", "w"), indent=1)
print(json.dumps(res["key_results"], indent=1)); print(os.path.getsize(f"{OUT}/fem_druckerprager.png") // 1024, "kB")
