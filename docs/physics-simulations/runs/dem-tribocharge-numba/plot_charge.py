"""Figure + animation for the tribocharging DEM. Usage: python plot_charge.py SCRATCH REPO_OUT"""
import json
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import EllipseCollection
import imageio.v2 as imageio
import imageio_ffmpeg

SCR, OUT = sys.argv[1], sys.argv[2]
res = json.load(open(os.path.join(SCR, "charge_runs.json")))
CTRL = sys.argv[3] if len(sys.argv) > 3 else None
ctrl = json.load(open(CTRL))["runs"]["uncharged"] if CTRL and os.path.exists(CTRL) else None
gases = list(res["runs"].keys())
RD = 10.45
cols = {"air": "C0", "argon": "C3"}
qref = None


def draw(ax, x, q, r, qnorm, title):
    ax.add_patch(plt.Circle((0, 0), RD, fill=False, lw=1.5, color="0.3"))
    ec = EllipseCollection(2 * r * 1e3, 2 * r * 1e3, np.zeros_like(r), units="xy", offsets=x * 1e3,
                           offset_transform=ax.transData, array=q / qnorm, cmap="coolwarm", clim=(-1, 1),
                           edgecolors="none")
    ax.add_collection(ec)
    ax.set_xlim(-RD * 1.05, RD * 1.05); ax.set_ylim(-RD * 1.05, RD * 1.05); ax.set_aspect("equal")
    ax.set_title(title, fontsize=9)
    return ec


fig = plt.figure(figsize=(14, 8.4))
gs = fig.add_gridspec(2, 3)
a1 = fig.add_subplot(gs[0, 0]); a2 = fig.add_subplot(gs[0, 1]); a3 = fig.add_subplot(gs[0, 2])
for g in gases:
    h = res["runs"][g]["hist"]
    rev = [d["rev"] for d in h]
    a1.plot(rev, [d["q_over_m_uC_per_kg"] for d in h], color=cols.get(g), label=f"{g} (cap {res['sigma_cap'][g] * 1e6:.1f} $\\mu$C/m$^2$)")
    a2.plot(rev, [100 * d["frac_stuck_top"] for d in h], color=cols.get(g), label=g)
    a3.plot(rev, [100 * d["frac_wall_contact"] for d in h], color=cols.get(g), label=g)
if ctrl is not None:
    hc = ctrl["hist"]
    a2.plot([d["rev"] for d in hc], [100 * d["frac_stuck_top"] for d in hc], color="0.4", ls="--", label="uncharged control")
    a3.plot([d["rev"] for d in hc], [100 * d["frac_wall_contact"] for d in hc], color="0.4", ls="--", label="uncharged control")
a1.set_xlabel("drum revolutions after charging starts" + ("" if res["K_ACC"] == 1 else " (time-compressed x%g)" % res["K_ACC"]))
a1.set_ylabel("mean charge-to-mass ratio ($\\mu$C/kg)")
a1.set_title("salt charging against PLA wall"); a1.legend(fontsize=8)
a2.set_xlabel("drum revolutions"); a2.set_ylabel("grains on the wall above y = 0.6 R (%)")
a2.set_title("carried over the top by adhesion"); a2.legend(fontsize=8)
a3.set_xlabel("drum revolutions"); a3.set_ylabel("grains touching the wall (%)")
a3.set_title("grains touching the wall (whole circumference)"); a3.legend(fontsize=8)
qnorm = max(float(np.load(os.path.join(SCR, f"frames_{g}.npz"))["qcap"].mean()) for g in gases)
for k, g in enumerate(gases[:2]):
    z = np.load(os.path.join(SCR, f"frames_{g}.npz"))
    ax = fig.add_subplot(gs[1, k])
    ec = draw(ax, z["x"][-1], z["q"][-1], z["r"], qnorm, f"{g}: end state, {res['runs'][g]['hist'][-1]['rev']:.0f} rev")
    ax.set_xlabel("x (mm)"); ax.set_ylabel("y (mm)")
cb = fig.colorbar(ec, ax=fig.axes[-1], fraction=0.046)
cb.set_label("q / q_cap,air (-)")
ax = fig.add_subplot(gs[1, 2])
for g in gases:
    z = np.load(os.path.join(SCR, f"frames_{g}.npz"))
    qm = z["q"][-1] / (2165 * 4 / 3 * np.pi * z["r"] ** 3) * 1e6
    ax.hist(qm, bins=40, alpha=0.5, color=cols.get(g), label=g)
ax.set_xlabel("per-grain q/m at end ($\\mu$C/kg)"); ax.set_ylabel("count (grains)")
ax.set_title("charge distribution"); ax.legend(fontsize=8)
fig.suptitle("dem-tribocharge-numba: self-written quasi-2D numba DEM, condenser-model contact charging, "
             "%d salt grains in a 20.9 mm PLA tube at 60 rpm, air vs dry argon" % res["N"], fontsize=11)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "tribocharge.png"), dpi=95)

# ---------- animation ----------
zs = {g: np.load(os.path.join(SCR, f"frames_{g}.npz")) for g in gases}
nfr = min(z["x"].shape[0] for z in zs.values())
frames = []
for k in range(nfr):
    f, axs = plt.subplots(1, len(gases), figsize=(6.4, 3.4), dpi=100)
    axs = np.atleast_1d(axs)
    for a, g in zip(axs, gases):
        z = zs[g]
        hk = res["runs"][g]["hist"][k]
        draw(a, z["x"][k], z["q"][k], z["r"], qnorm,
             f"{g}: rev {hk['rev']:.2f}, q/m = {hk['q_over_m_uC_per_kg']:.0f} $\\mu$C/kg")
        a.tick_params(labelsize=6)
        a.set_xlabel("x (mm)", fontsize=7)
    f.suptitle("dem-tribocharge-numba (numba DEM): colour = q / q_cap,air", fontsize=8)
    f.tight_layout()
    f.canvas.draw()
    frames.append(np.asarray(f.canvas.buffer_rgba())[:, :, :3].copy())
    plt.close(f)
h, w = frames[0].shape[:2]
frames = [fr[:h - h % 2, :w - w % 2] for fr in frames]
imageio.mimsave(os.path.join(OUT, "tribocharge.gif"), frames, duration=1 / 12, loop=0)
os.environ.setdefault("IMAGEIO_FFMPEG_EXE", imageio_ffmpeg.get_ffmpeg_exe())
wr = imageio.get_writer(os.path.join(OUT, "tribocharge.mp4"), fps=12, codec="libx264", pixelformat="yuv420p",
                        macro_block_size=1, ffmpeg_params=["-crf", "28"])
for fr in frames:
    wr.append_data(fr)
wr.close()
print("frames", len(frames), frames[0].shape)

# ---------- result.json ----------
def stats(h, key, rmin=1.0):
    v = np.array([d[key] for d in h if d["rev"] >= rmin])
    return float(v.mean()), float(v.std())


kr = {"N_grains": res["N"], "revolutions_charged": res["NREV"], "time_compression_K_ACC": res["K_ACC"],
      "breakdown_field_V_per_m": {"air": res["E_b_air_V_per_m"], "argon": res["E_b_argon_V_per_m"]},
      "sigma_cap_C_per_m2": {g: res["sigma_cap"][g] for g in ("air", "argon")},
      "q_over_m_cap_single_grain_uC_per_kg_d042": {g: res["sigma_cap"][g] * np.pi * 0.42e-3 ** 2 /
                                                   (2165 * np.pi / 6 * 0.42e-3 ** 3) * 1e6 for g in ("air", "argon")}}
for g in gases:
    h = res["runs"][g]["hist"]
    qm = np.array([d["q_over_m_uC_per_kg"] for d in h]); rv = np.array([d["rev"] for d in h])
    sat = qm[rv >= 1.0].mean()
    t95 = float(rv[np.argmax(qm >= 0.95 * sat)])
    kr[g] = {"q_over_m_saturated_uC_per_kg": round(float(sat), 3),
             "rev_to_95pct_saturation": t95,
             "stuck_top_pct_mean_sd_rev1to6": [round(100 * x, 2) for x in stats(h, "frac_stuck_top")],
             "wall_contact_pct_mean_sd_rev1to6": [round(100 * x, 2) for x in stats(h, "frac_wall_contact")],
             "frac_grains_at_cap_end": h[-1]["frac_at_cap"],
             "wall_patches_at_cap_end": res["runs"][g]["wall_patch_frac_at_cap"],
             "charge_conservation_error_C": res["runs"][g]["charge_conservation_C"],
             "wall_s": round(res["runs"][g]["wall_s"], 1)}
if ctrl is not None:
    kr["uncharged_control"] = {"stuck_top_pct_mean_sd": [round(100 * x, 2) for x in stats(ctrl["hist"], "frac_stuck_top", 0.0)],
                               "wall_contact_pct_mean_sd": [round(100 * x, 2) for x in stats(ctrl["hist"], "frac_wall_contact", 0.0)],
                               "revolutions": ctrl["hist"][-1]["rev"], "wall_s": round(ctrl["wall_s"], 1)}
if "air" in kr and "argon" in kr:
    kr["argon_over_air_q_over_m"] = round(kr["argon"]["q_over_m_saturated_uC_per_kg"] / kr["air"]["q_over_m_saturated_uC_per_kg"], 3)
wall_total = res["wall_s"] + (ctrl["wall_s"] if ctrl is not None else 0.0)
out = {"id": "dem-tribocharge-numba",
       "method": "Self-written quasi-2D DEM (numba) of salt in a rotating PLA tube cross-section with condenser-model "
                 "contact charging, Coulomb + image forces, gas-breakdown charge caps (air vs dry argon)",
       "code": "self-written Python/numba (run.py)", "version": "numba %s, numpy %s" % (__import__("numba").__version__, np.__version__),
       "status": "ran", "wall_s": round(wall_total, 1), "cores": 1, "key_results": kr,
       "notes": "Quasi-2D monolayer, 600 grains, soft contacts (k_n = 5 N/m), no grain rotation, no humidity leakage. "
                "Wall counter-charge capped at the same breakdown density over patch area (arc x one grain diameter); "
                "this wall capacity, not the per-grain cap, limits q/m. No time compression (K_ACC = 1)."}
with open(os.path.join(OUT, "result.json"), "w") as f:
    json.dump(out, f, indent=1)
print(json.dumps(kr, indent=1))
