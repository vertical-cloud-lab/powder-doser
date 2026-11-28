"""Post-processing for FEA (a): servo-step jolts on the tilt table and the figure. Computed, not measured.

The FEA gives the first mode (the plate rotating about the hinge on the arm + gear + servo compliance).
Model: one degree of freedom, I theta'' + c theta' + k (theta - theta_in(t)) = 0, with k = I w1^2 from the FEA,
I from the plate + coupon + ring masses, damping ratio 0.05 (assumed, printed PLA + gear friction).
theta_in is a servo move of size d (at the table) done as a smooth (cosine) ramp in t_r.
Peak normal acceleration at the ring (r = 90 mm from the hinge) -> early slip:
  slip when g sin(theta) > mu (g cos(theta) - a_n)  ->  d(theta) = -sin(phi_w) a_n / g  [rad]
"""
import json
import math

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.integrate import solve_ivp

from fea_common import HERE, PAL, INK, INK2, style, save_json

R = json.loads((HERE / "results" / "a_tilt_table_fea_all.json").read_text())
mesh = [c for c in R["cases"] if c["study"] == "mesh"]
nom = [c for c in mesh if c["lc"] == 5.0][0]
sens = [c for c in R["cases"] if c["study"] == "sensitivity"]
f1 = nom["modes"][0]["f_Hz"]
# inertia about the hinge (hand): plate 43.2 cm3 PLA (CAD volume) + coupon 39 g + ring/powder/lid 19 g
m_plate = 43.2e-6 * 1240.0
I = m_plate * (0.120 ** 2 / 3 + 0.005 ** 2) + 0.039 * (0.064 ** 2 + 0.1 ** 2 / 12) + 0.019 * 0.090 ** 2
k_eff = I * (2 * math.pi * f1) ** 2
# hand check of f1 from the static FEA: k = M / slope, M = gravity moment of the masses about the hinge
M = 9.81 * (m_plate * 0.060 + 0.039 * 0.064 + 0.019 * 0.090)
k_static = M / math.radians(abs(nom["slope_imu_deg"]))
f1_hand = math.sqrt(k_static / I) / (2 * math.pi)
k_servo_side = 120.0
k_struct = 1.0 / (1.0 / k_static - 1.0 / k_servo_side)


def jolt(d_deg, t_r, f=f1, zeta=0.05, r=0.090):
    w = 2 * math.pi * f
    d = math.radians(d_deg)

    def th_in(t):
        if t <= 0:
            return 0.0, 0.0
        if t >= t_r:
            return d, 0.0
        return d * 0.5 * (1 - math.cos(math.pi * t / t_r)), d * 0.5 * math.pi / t_r * math.sin(math.pi * t / t_r)

    def rhs(t, y):
        th, om = y
        ti, tdi = th_in(t)
        return [om, -w ** 2 * (th - ti) - 2 * zeta * w * (om - tdi)]

    T = t_r + 8 / f
    sol = solve_ivp(rhs, (0, T), [0, 0], max_step=min(t_r, 1 / f) / 60, rtol=1e-8, atol=1e-12)
    acc = np.gradient(sol.y[1], sol.t)
    return float(np.max(np.abs(acc)) * r / 9.81)


steps = [0.045, 0.135, 0.35]   # table deg: 1, 3, 8 us servo deadband at about 11 us/deg servo, 2:1 gear
trs = np.array([0.002, 0.005, 0.01, 0.02, 0.03, 0.05, 0.08, 0.12])
table = {d: [jolt(d, t) for t in trs] for d in steps}
phi_w = math.radians(22.0)
bias = {d: [math.degrees(math.sin(phi_w) * a) for a in table[d]] for d in steps}
# what is needed for < 0.02 g: the move time for each step size
need = {}
for d in steps:
    a = np.array(table[d])
    ok = trs[a < 0.02]
    need[d] = float(ok.min()) if len(ok) else None

out = dict(f1_Hz=f1, f1_hand_from_static_Hz=f1_hand, I_kgm2=I, k_eff_Nm_per_rad=k_eff,
           k_static_Nm_per_rad=k_static, k_struct_arm_lug_plate_Nm_per_rad=k_struct,
           gravity_moment_Nm=M, step_sizes_table_deg=steps, ramp_times_s=trs.tolist(),
           peak_normal_accel_g=table, slip_angle_bias_deg_at_22deg=bias, ramp_time_for_0p02g_s=need,
           erm_band_Hz=[150, 250], modes_nominal=nom["modes"], modes_E2300=sens[0]["modes"],
           note="computed, not measured; damping ratio 0.05 assumed")
save_json(HERE / "results" / "a_tilt_table_jolt.json", out)
print(json.dumps({k: v for k, v in out.items() if k not in ("modes_nominal", "modes_E2300")}, indent=1)[:1500])

fig, axs = plt.subplots(1, 3, figsize=(13.5, 4.0))
ax = axs[0]
lcs = [c["lc"] for c in mesh]
ax.plot(lcs, [-c["uz_tip_centre_um"] for c in mesh], "o-", color=PAL[0], lw=2, ms=7)
style(ax, "Mesh convergence: tip sag, plate level", "max element size (mm)", "tip sag under gravity (µm)")
ax.invert_xaxis()
for c in mesh:
    ax.annotate(f"{c['modes'][0]['f_Hz']:.1f} Hz", (c["lc"], -c["uz_tip_centre_um"]), textcoords="offset points",
                xytext=(0, 8), ha="center", color=INK2, fontsize=8)
ax = axs[1]
labels = ["E 3.5 GPa\nk 120", "E 2.3 GPa\nk 120", "E 3.5 GPa\nk 40", "E 3.5 GPa\nk 400"]
cases = [nom] + sens
for i, c in enumerate(cases):
    for j, m in enumerate(c["modes"][:4]):
        ax.plot([i - 0.3, i + 0.3], [m["f_Hz"]] * 2, color=PAL[j], lw=2.5, label=f"mode {j + 1}" if i == 0 else None)
ax.axhspan(150, 250, color="#f2a600", alpha=0.18, lw=0)
ax.text(3.45, 200, "ERM\n150-250 Hz", ha="right", va="center", color=INK2, fontsize=8)
ax.set_xticks(range(4))
ax.set_xticklabels(labels, fontsize=8)
style(ax, "Natural frequencies (k = servo + gear, N·m/rad)", None, "frequency (Hz)")
ax.set_ylim(0, 540)
ax.legend(frameon=False, fontsize=8, loc="upper left", ncol=4)
ax = axs[2]
for j, d in enumerate(steps):
    ax.loglog(trs * 1e3, table[d], "o-", color=PAL[j], lw=2, ms=6, label=f"{d}° step at the table")
ax.axhline(0.02, color=INK2, lw=1, ls="--")
ax.text(2.1, 0.023, "0.02 g: about 0.4° early slip at φw 22°", color=INK2, fontsize=8)
style(ax, f"Servo step jolt at the ring (mode 1, {f1:.0f} Hz)", "servo move time (ms)", "peak normal acceleration (g)")
ax.legend(frameon=False, fontsize=8, loc="lower left")
fig.tight_layout()
fig.savefig(HERE / "a_tilt_table.png", dpi=150)
print("saved")
