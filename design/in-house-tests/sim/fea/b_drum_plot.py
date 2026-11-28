"""Figure for FEA (b): tooth root stress field, tooth and shaft mesh convergence. Computed, not measured."""
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.tri as mtri
import numpy as np
import b_drum_shaft as b
from fea_common import HERE, PAL, INK, INK2, style

t = b.tooth_fea(0.06, rho_f=0.38)
lw = b.lewis()
tooth = json.loads((HERE / "results" / "b_drum_shaft_all.json").read_text())["tooth"]
fea = json.loads((HERE / "results" / "b_drum_shaft_beamfea.json").read_text())["fea"]
fig, axs = plt.subplots(1, 3, figsize=(13.5, 4.2))
ax = axs[0]
xq = t["xq"]
s1 = t["s1"]
pts = xq.reshape(2, -1).T
vals = s1.reshape(-1)
sel = (pts[:, 0] > 18.0)
cs = ax.scatter(pts[sel, 0], pts[sel, 1], c=np.clip(vals[sel], 0, None), s=2, cmap="Blues", vmin=0, vmax=5.5,
                linewidths=0)
fig.colorbar(cs, ax=ax, label="max principal stress (MPa)")
ax.set_aspect("equal")
style(ax, "44T m1 tooth, stall torque, tip load", "x (mm)", "y (mm)")
ax = axs[1]
for j, rho in enumerate((0.38, 0.2)):
    rows = [r for r in tooth if r["rho_f"] == rho]
    ax.plot([r["n_dof"] for r in rows], [r["s1_root_MPa"] for r in rows], "o-", color=PAL[j], lw=2, ms=7,
            label=f"FEA, root fillet {rho} mm")
ax.axhline(lw["sigma_MPa"], color=PAL[2], lw=2, ls="--", label=f"Lewis {lw['sigma_MPa']:.2f} MPa")
ax.axhline(15.0, color=INK2, lw=1, ls=":")
ax.text(7000, 14.2, "15 MPa fatigue limit (assumed)", color=INK2, fontsize=8)
ax.set_xscale("log")
ax.set_ylim(0, 16)
style(ax, "Root tensile stress vs mesh", "degrees of freedom", "stress at stall (MPa)")
ax.legend(frameon=False, fontsize=8, loc="center right")
ax = axs[2]
f35 = [f for f in fea if f["E"] == 3500.0]
ax.plot([f["lc"] for f in f35], [f["gear_force_stall"]["drum_front_uy_um"] for f in f35], "o-", color=PAL[0], lw=2, ms=7,
        label="drum shift, gear force at stall")
ax.plot([f["lc"] for f in f35], [100 * f["stall_torque"]["twist_gear_vs_drum_deg"] for f in f35], "s-", color=PAL[1],
        lw=2, ms=7, label="twist gear to drum (0.01°)")
ax.plot([f["lc"] for f in f35], [10 * abs(f["gravity"]["drum_front_uy_um"]) for f in f35], "^-", color=PAL[2], lw=2,
        ms=7, label="sag under gravity (0.1 µm)")
ax.invert_xaxis()
ax.set_ylim(0, 20)
style(ax, "Shaft + drum 3D FEA vs mesh", "max element size (mm)", "value (units in legend)")
ax.legend(frameon=False, fontsize=8, loc="lower left")
fig.tight_layout()
fig.savefig(HERE / "b_drum_shaft.png", dpi=150)
print("saved")
