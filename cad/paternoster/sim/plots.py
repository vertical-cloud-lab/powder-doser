"""Plots for carousel_sim.py (PNG in sim/out/)."""
from __future__ import annotations

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

import model as M  # noqa: E402

OUT = M.OUT
S = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
MUTED = "#b9bcc2"
INK = "#303338"
plt.rcParams.update({"axes.edgecolor": "#8a8d93", "axes.labelcolor": INK, "xtick.color": INK, "ytick.color": INK,
                     "axes.grid": True, "grid.color": "#e6e7ea", "grid.linewidth": 0.8, "axes.spines.top": False,
                     "axes.spines.right": False, "font.size": 10, "legend.frameon": False, "lines.linewidth": 1.6})
RAD = 180 / np.pi


def _save(fig, name):
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, name), dpi=130)
    plt.close(fig)


def station_trace(L, stops):
    """Swing of whichever module is at the station (u nearest 10) at each instant."""
    u = M.module_u(L["s"], np.arange(M.NK))
    k = np.argmin(np.abs(((u - 10.0 + 60) % 120) - 60), axis=1)
    return L["th"][np.arange(len(k)), k] * RAD


def make_all(R, LOGS, ST, DEC, fz):
    # 1. index profiles: station gondola swing
    fig, axs = plt.subplots(1, 2, figsize=(12, 4.2), sharey=True)
    for ax, T in zip(axs, ("1.0", "1.5")):
        for i, kind in enumerate(("trap", "scurve", "zv", "trapTn")):
            L, stops = LOGS[f"index_{kind}_{T}s"]
            ax.plot(L["t"], station_trace(L, stops), color=S[i], lw=1.3,
                    label={"trap": "trapezoidal, t_acc = T/3", "scurve": "S-curve (jerk-limited)",
                           "zv": f"S-curve + ZV shaper ({fz:.2f} Hz)", "trapTn": f"trapezoidal, t_acc = pendulum period ({1 / fz:.2f} s)"}[kind])
        for ts in stops:
            ax.axvline(ts, color=MUTED, lw=0.8, ls="--")
        ax.axhspan(-0.5, 0.5, color="#e6e7ea", alpha=0.6, lw=0)
        ax.set_title(f"Station gondola swing, 3 indexes of {T} s (dashed: stops)")
        ax.set_xlabel("time (s)")
    axs[0].set_ylabel("swing about pivot axis (deg)")
    axs[0].legend(loc="upper right")
    _save(fig, "swing_index_profiles.png")

    # 2. full lap of indexing, all gondolas
    fig, axs = plt.subplots(2, 1, figsize=(12, 6.5), sharex=True, sharey=True)
    for ax, kind, ttl in zip(axs, ("lap12_trap_1.0s", "lap12_trapTn_1.5s"), ("trapezoidal 1.0 s (baseline)", "trapezoidal 1.5 s, t_acc = pendulum period (recommended)")):
        L, stops = LOGS[kind]
        for k in range(1, M.NK):
            ax.plot(L["t"], L["th"][:, k] * RAD, color=MUTED, lw=0.8, label="other 11 gondolas" if k == 1 else None)
        ax.plot(L["t"], L["th"][:, 0] * RAD, color=S[0], lw=1.6, label="module 0 (blue gondola)")
        ax.plot(L["t"], station_trace(L, stops), color=S[1], lw=1.2, label="gondola at the station")
        ax.set_title(f"Full lap, 12 indexes, {ttl}")
        ax.set_ylabel("swing (deg)")
    axs[0].legend(loc="upper right", ncol=3)
    axs[1].set_xlabel("time (s)")
    _save(fig, "swing_lap12.png")

    # 3. max swing by region, continuous laps
    laps = [k for k in R["runs"] if k.startswith("fastlap_")]
    regs = [r[0] for r in M.REGIONS]
    fig, ax = plt.subplots(figsize=(12, 4.2))
    w = 0.8 / len(laps)
    for i, k in enumerate(laps):
        vals = [R["runs"][k]["max_swing_by_region_deg"][r] or 0 for r in regs]
        ax.bar(np.arange(len(regs)) + (i - (len(laps) - 1) / 2) * w, vals, width=w * 0.92, color=S[i],
               label=f"lap in {k.split('_')[1]}")
    ax.set_xticks(np.arange(len(regs)), regs)
    ax.set_ylabel("max |swing| (deg)")
    ax.set_title("Continuous laps (S-curve speed profile): max swing by where the gondola is")
    ax.legend(ncol=4)
    _save(fig, "swing_by_region_fastlaps.png")

    # 4. clearance
    fig, ax = plt.subplots(figsize=(12, 4.2))
    for i, k in enumerate(laps):
        L, _ = LOGS[k]
        ax.plot(L["t"], L["clr"].min(1), color=S[i], lw=1.2, label=f"lap in {k.split('_')[1]}: min {L['clr'].min():.1f} mm")
    ax.axhline(R["runs"][laps[0]]["min_neighbour_clearance_upright_mm"], color=INK, lw=0.8, ls="--",
               label="all upright (kinematic) min")
    ax.axhline(0, color=S[7], lw=1)
    ax.set_xlabel("time (s)")
    ax.set_ylabel("min gap between neighbours (mm)")
    ax.set_title("Smallest neighbour gap over all 12 pairs, swung envelopes (62 x 57 mm)")
    ax.legend(ncol=3, loc="lower right")
    _save(fig, "clearance_fastlaps.png")

    # 5. motor torque
    fig, ax = plt.subplots(figsize=(12, 4.0))
    for i, k in enumerate(("index_trap_1.0s", "index_trapTn_1.5s", "fastlap_10s", "fastlap_4s")):
        L, _ = LOGS[k]
        ax.plot(L["t"], L["torque"], color=S[i], lw=1.1, label=f"{k}: peak {np.abs(L['torque']).max():.2f} N*m")
    ax.set_xlabel("time (s)")
    ax.set_ylabel("drive shaft torque (N*m)")
    ax.set_title("Motor torque at the drive shaft (pivot forces by virtual work + chain/sprocket/rotor inertia)")
    ax.legend(ncol=2)
    _save(fig, "motor_torque.png")

    # 6. free decay
    fig, ax = plt.subplots(figsize=(12, 4.0))
    for i, (k, fd) in enumerate(DEC.items()):
        ax.plot(fd["t"], fd["th"], color=S[i], lw=1.0, label=k)
    ax.axhspan(-0.5, 0.5, color="#e6e7ea", alpha=0.6, lw=0)
    ax.set_xlim(0, 8)
    ax.set_xlabel("time (s)")
    ax.set_ylabel("swing (deg)")
    ax.set_title("Free decay from 5 deg: viscous damping c (N*m*s/rad) and pivot Coulomb friction mu")
    ax.legend(ncol=3, loc="upper right")
    _save(fig, "free_decay.png")

    # 7. station (current CAD rig: rod-end pin at Sam's (40, -72) mm, base 289.4 mm below the hinge)
    names = [n for n in ("station_cad_rigidchain", "station_cad_chain_nostrip", "station_cad_strip", "station_cad_strip_tab50") if n in ST]
    lab = {"station_cad_rigidchain": "rigid chain", "station_cad_chain_nostrip": "40 N chain, tab 2 N/mm, no strip",
           "station_cad_strip": "hold-down strip, tab 2 N/mm", "station_cad_strip_tab50": "hold-down strip, tab 50 N/mm"}
    fig, axs = plt.subplots(2, 3, figsize=(17, 8))
    Lg, T, geo = ST[names[0]]
    ax = axs[0, 0]
    ax.plot(Lg["t"], Lg["tilt"], color=S[0], label="module tilt (deg)")
    ax.plot(Lg["t"], Lg["slide"], color=S[1], label="actuator extension (mm)")
    ax.set_title("Station sequence: tilt and stroke")
    ax.set_xlabel("time (s)")
    ax.legend()
    ax = axs[0, 1]
    up = (Lg["t"] >= T["tilt0"] + 0.15) & (Lg["t"] < T["tilt1"])
    ax.plot(Lg["tilt"][up], Lg["Fact"][up], color=S[0], label="simulation (rigid chain)")
    ax.plot([g["tilt_deg"] for g in geo], [g["force_N"] for g in geo], color=S[0], ls="--", lw=1, label="static estimate")
    ax.set_xlabel("tilt (deg)")
    ax.set_ylabel("actuator force (N)")
    ax.set_title("P16-P force vs tilt (limit 50 N)")
    ax.legend()
    ax = axs[0, 2]
    for i, nm in enumerate(names[1:], start=1):
        Lg, T, geo = ST[nm]
        ax.plot(Lg["t"], Lg["rise_f"], color=S[i], label=f"{lab[nm]}: front")
        ax.plot(Lg["t"], Lg["rise_b"], color=S[i], ls="--", lw=1.0, label="back")
    ax.set_xlabel("time (s)")
    ax.set_ylabel("pivot rise (mm)")
    ax.set_title("Station gondola pivot rise")
    ax.legend(fontsize=8, ncol=2)
    ax = axs[1, 0]
    for i, nm in enumerate(names):
        Lg, T, geo = ST[nm]
        ax.plot(Lg["t"], Lg["Ffz"], color=S[i], lw=1.2, label=f"{lab[nm]}: front")
        if i in (0, 2):
            ax.plot(Lg["t"], Lg["Fbz"], color=S[i], ls="--", lw=1.0, label="back")
    ax.axhline(0, color=S[7], lw=1)
    ax.set_xlabel("time (s)")
    ax.set_ylabel("vertical force chain -> gondola (N)")
    ax.set_title("Pivot vertical force (below 0 = pulls the chain up)")
    ax.legend(fontsize=8)
    ax = axs[1, 1]
    for i, nm in enumerate(names[2:], start=2):
        Lg, T, geo = ST[nm]
        ax.plot(Lg["t"], Lg["strip_f"], color=S[i], label=f"{lab[nm]}: front")
        ax.plot(Lg["t"], Lg["strip_b"], color=S[i], ls="--", lw=1.0, label="back")
    ax.set_xlabel("time (s)")
    ax.set_ylabel("strip contact force (N)")
    ax.set_title("Hold-down strip force on the chain")
    ax.legend(fontsize=8)
    ax = axs[1, 2]
    for i, nm in enumerate(names):
        Lg, T, geo = ST[nm]
        ax.plot(Lg["t"], Lg["swing"], color=S[i], lw=1.1, label=lab[nm])
    ax.set_xlabel("time (s)")
    ax.set_ylabel("station gondola swing (deg)")
    ax.set_title("Swing: docked, tilted, taps (3 N, 10 ms), auger")
    ax.legend(fontsize=8)
    _save(fig, "station.png")
