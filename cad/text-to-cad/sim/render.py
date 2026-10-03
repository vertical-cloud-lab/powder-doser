"""Figures and the sequence GIF for the DEM scenarios (issue #172).

    /tmp/simenv/bin/python sim/render.py [gif] [plots]

Reads sim/results/*.json and the frame dumps in /tmp/simframes; writes to
renders/sim/.
"""
from __future__ import annotations

import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

import dem  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
OUT = os.path.normpath(os.path.join(HERE, "..", "renders", "sim"))
FRAMES = os.environ.get("SIM_FRAMES", "/tmp/simframes")
os.makedirs(OUT, exist_ok=True)

# reference categorical palette (fixed order) + inks
PAL = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"]
SURF, INK, INK2, MUTED, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e4e3df"
WALL = "#c9c7c0"
plt.rcParams.update({"figure.facecolor": SURF, "axes.facecolor": SURF, "axes.edgecolor": MUTED,
                     "axes.labelcolor": INK2, "xtick.color": MUTED, "ytick.color": MUTED,
                     "text.color": INK, "font.size": 9, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.grid": True, "grid.color": GRID,
                     "grid.linewidth": 0.6, "lines.linewidth": 2.0, "legend.frameon": False})
MMf = 1e3   # m -> mm


def load(name):
    with open(os.path.join(RES, f"{name}.json")) as f:
        return json.load(f)


def to_lab(z, y, beta):
    """Tube-frame (z along axis, y up at zero tilt) -> lab side view, rotated about the outlet."""
    c, s = np.cos(beta), np.sin(beta)
    return z * c - y * s, z * s + y * c


def r_bore(z):
    return np.where(z < dem.Z_FUN, dem.R_EXIT + (dem.R_BORE - dem.R_EXIT) * z / dem.Z_FUN, dem.R_BORE)


def draw_auger(ax, beta, theta, z_top, artists):
    """Side section of the tube (wall + core filled), flight edge at the bore, capture plane."""
    R, Ro = dem.R_BORE * MMf, 12.5
    zt = z_top * MMf
    zf, re, rc, rt = dem.Z_FUN * MMf, dem.R_EXIT * MMf, dem.R_CORE * MMf, dem.R_TIP * MMf
    for sgn in (1, -1):
        poly = np.array([(0, sgn * re), (0, sgn * Ro), (zt + 6, sgn * Ro), (zt + 6, sgn * R), (zf, sgn * R)])
        X, Y = to_lab(poly[:, 0], poly[:, 1], beta)
        artists += ax.fill(X, Y, color=WALL, lw=0, zorder=1)
    core = np.array([(0, -rt), (zf, -rc), (zt + 6, -rc), (zt + 6, rc), (zf, rc), (0, rt)])
    X, Y = to_lab(core[:, 0], core[:, 1], beta)
    artists += ax.fill(X, Y, color=WALL, lw=0, zorder=1)
    # flight edge where it meets the bore (front half solid, back half dashed)
    phi = np.linspace(-np.pi, np.pi * 8, 4000)
    zz = (0.5 * dem.T_FLIGHT + dem.PITCH * (phi - theta) / (2 * np.pi)) * MMf
    ok = (zz >= 0) & (zz <= zt)
    yy = r_bore(zz / MMf) * MMf * np.sin(phi)
    front = np.cos(phi) >= 0
    for m, ls, a in ((front, "-", 0.9), (~front, ":", 0.6)):
        zm = np.where(ok & m, zz, np.nan)
        X, Y = to_lab(zm, yy, beta)
        artists += ax.plot(X, Y, ls, color=INK2, lw=1.2, alpha=a, zorder=3)
    # capture plane and artificial top of the simulated section
    zc = 6.0
    X, Y = to_lab(np.array([zc, zc]), np.array([-r_bore(zc / MMf) * MMf, r_bore(zc / MMf) * MMf]), beta)
    artists += ax.plot(X, Y, "--", color=PAL[7], lw=1.0, zorder=4)
    X, Y = to_lab(np.array([zt, zt]), np.array([-R, R]), beta)
    artists += ax.plot(X, Y, ":", color=MUTED, lw=1.0, zorder=4)
    return artists


def make_gif(name="sequence", out="dem_sequence.gif", fps=15):
    d = np.load(os.path.join(FRAMES, f"{name}_frames.npz"))
    res = load(name)
    log = res["log"]
    t_log = np.array(log["t"])
    m_log = np.array(log["m_disp_mg"])
    rad = d["rad"]
    ch0 = d["chamber0"] if "chamber0" in d.files else np.zeros(len(rad), int)
    ch = ch0 - ch0.min()
    cols = np.array(PAL)[np.clip(ch, 0, len(PAL) - 1)]
    z_top = res["z_top_mm"] / MMf
    fig = plt.figure(figsize=(8.0, 5.2), dpi=100)
    ax = fig.add_axes([0.02, 0.02, 0.62, 0.90])
    ax.set_aspect("equal")
    ax.set_xlim(-22, 46)
    ax.set_ylim(-40, 38)
    ax.axis("off")
    axm = fig.add_axes([0.71, 0.56, 0.26, 0.30])
    axm.plot(t_log, m_log, color=GRID, lw=2)
    line, = axm.plot([], [], color=PAL[0], lw=2)
    dot, = axm.plot([], [], "o", color=PAL[0], ms=6, mec=SURF, mew=2)
    for tk in res.get("tap_times_s", []):
        axm.axvline(tk, color=PAL[1], lw=0.8, alpha=0.7)
    axm.set_xlabel("time (s)")
    axm.set_title("dispensed mass (mg)", fontsize=9, color=INK2, loc="left")
    axm.set_xlim(0, t_log[-1])
    axm.set_ylim(0, max(1.0, m_log.max() * 1.1))
    txt = fig.text(0.70, 0.46, "", va="top", ha="left", fontsize=10, color=INK, family="monospace")
    fig.text(0.02, 0.965, "DEM: powder in the auger outlet section (side section, lab frame)",
             fontsize=11, color=INK, weight="bold")
    fig.text(0.70, 0.17, "colour = flight chamber at t = 0\n"
             "-- red dashed: capture plane (z = 6 mm)\n"
             "grey: tube wall + core; lines: flight edge\n"
             f"{res['n_particles']} spheres, d = {res['d_range_mm'][0]:.1f}-{res['d_range_mm'][1]:.1f} mm\n"
             "playback 0.5x real time", fontsize=7.5, color=INK2, va="top")
    ppmm = ax.get_window_extent().width / 72 / 68 * 72   # points per mm (68 mm x-span)
    images = []
    for f in range(len(d["t"])):
        artists = []
        beta = np.radians(d["tilt"][f])
        theta = d["theta"][f]
        draw_auger(ax, beta, theta, z_top, artists)
        a = d["active"][f]
        p = d["pos"][f][a] * MMf
        order = np.argsort(p[:, 0])           # far (x < 0) first
        X, Y = to_lab(p[order, 2], p[order, 1], beta)
        sc = ax.scatter(X, Y, s=(2 * rad[a][order] * MMf * ppmm * 0.9) ** 2, c=cols[a][order],
                        lw=0.25, edgecolors=SURF, zorder=2)
        artists.append(sc)
        # cup under the outlet, filled in proportion to the dispensed mass (illustrative)
        m = d["m_disp"][f] * 1e6
        cup = ax.fill([-9, 9, 9, -9], [-38, -38, -22, -22], fc="none", ec=MUTED, lw=1.2, zorder=1)
        hfill = 16 * m / max(1.0, m_log.max())
        fill = ax.fill([-9, 9, 9, -9], [-38, -38, -38 + hfill, -38 + hfill], color=PAL[0], alpha=0.35,
                       lw=0, zorder=1)
        artists += cup + fill
        tt = d["t"][f]
        k = t_log <= tt + 1e-9
        line.set_data(t_log[k], m_log[k])
        dot.set_data([tt], [np.interp(tt, t_log, m_log)])
        txt.set_text(f"{str(d['phase'][f]):<17}\n"
                     f"t        {tt:5.2f} s\n"
                     f"tilt     {d['tilt'][f]:5.1f} deg\n"
                     f"tube     {np.degrees(theta):5.0f} deg\n"
                     f"cup      {m:5.0f} mg")
        fig.canvas.draw()
        img = Image.frombuffer("RGBA", fig.canvas.get_width_height(), fig.canvas.buffer_rgba()).convert("RGB")
        images.append(img.quantize(colors=64, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE))
        for art in artists:
            art.remove()
    fn = os.path.join(OUT, out)
    images[0].save(fn, save_all=True, append_images=images[1:], duration=int(1000 / fps), loop=0,
                   optimize=True)
    # a still of the most informative frame (mid-rotation) for the README
    mid = int(np.argmin(np.abs(d["t"] - (res["times"]["rot0"] + 0.55)))) if "times" in res else len(images) // 2
    images[mid].convert("RGB").save(os.path.join(OUT, out.replace(".gif", "_still.png")))
    plt.close(fig)
    print("wrote", fn, f"{os.path.getsize(fn) / 1e6:.2f} MB", len(images), "frames")


def plot_sequence():
    res = load("sequence")
    log = res["log"]
    t = np.array(log["t"])
    fig, axs = plt.subplots(3, 1, figsize=(7, 5.6), sharex=True, gridspec_kw=dict(height_ratios=[2, 1, 1]))
    axs[0].plot(t, log["m_disp_mg"], color=PAL[0])
    axs[0].set_ylabel("dispensed (mg)")
    axs[1].plot(t, log["tilt_deg"], color=PAL[0])
    axs[1].set_ylabel("tilt (deg)")
    axs[2].plot(t, np.array(log["theta_deg"]) / 360, color=PAL[0])
    axs[2].set_ylabel("tube revs")
    axs[2].set_xlabel("time (s)")
    T = res["times"]
    for ax in axs:
        ax.axvspan(T["rot0"], T["rot2"], color=PAL[2], alpha=0.10, lw=0)
        for tk in res["tap_times_s"]:
            ax.axvline(tk, color=PAL[1], lw=1, alpha=0.8)
    axs[0].text(0.5 * (T["rot0"] + T["rot2"]), axs[0].get_ylim()[1] * 0.92, "rotation", ha="center",
                color=INK2, fontsize=8)
    axs[0].text(res["tap_times_s"][0], axs[0].get_ylim()[1] * 0.92, " taps", color=INK2, fontsize=8)
    axs[0].set_title(f"Sequence: tilt 0 -> {res['tilt_deg']:.0f} deg, 1 rev at {res['rpm_tube']:.0f} rpm, "
                     f"{len(res['tap_times_s'])} taps, tilt back", loc="left", fontsize=10)
    fig.tight_layout()
    fn = os.path.join(OUT, "dem_sequence_mass.png")
    fig.savefig(fn, dpi=150)
    plt.close(fig)
    print("wrote", fn)


def plot_dose():
    tilts = []
    for tl in (0.0, 22.5, 45.0):
        p = os.path.join(RES, f"dose_tilt{tl:g}.json")
        if os.path.exists(p):
            tilts.append(load(f"dose_tilt{tl:g}"))
    if not tilts:
        return
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9, 3.6), gridspec_kw=dict(width_ratios=[1.6, 1]))
    for k, r in enumerate(tilts):
        th = np.array(r["log"]["theta_deg"]) / 360
        m = np.array(r["log"]["m_disp_mg"])
        a1.plot(th, m, color=PAL[k], label=f"{r['tilt_deg']:g} deg")
        a1.text(th[-1] + 0.02, m[-1], f"{r['tilt_deg']:g} deg", color=INK2, fontsize=8, va="center")
    a1.set_xlabel("tube revolutions")
    a1.set_ylabel("dispensed (mg)")
    a1.set_title("Cumulative dose vs tube rotation", loc="left", fontsize=10)
    a1.legend(loc="upper left")
    x = np.arange(len(tilts))
    first = [r["dose_first_rev_mg"] for r in tilts]
    allr = [r["m_total_disp_mg"] / (r["log"]["theta_deg"][-1] / 360) for r in tilts]
    w = 0.38
    a2.bar(x - w / 2 - 0.01, first, w, color=PAL[0], label="1st rev")
    a2.bar(x + w / 2 + 0.01, allr, w, color=PAL[1], label="run average")
    for xi, v1, v2 in zip(x, first, allr):
        a2.text(xi - w / 2, v1, f"{v1:.0f}", ha="center", va="bottom", fontsize=8, color=INK2)
        a2.text(xi + w / 2, v2, f"{v2:.0f}", ha="center", va="bottom", fontsize=8, color=INK2)
    a2.set_xticks(x, [f"{r['tilt_deg']:g} deg" for r in tilts])
    a2.set_ylabel("mg per rev")
    a2.set_title("Dose per revolution vs tilt", loc="left", fontsize=10)
    a2.legend(loc="upper left")
    a2.grid(axis="x", visible=False)
    fig.tight_layout()
    fn = os.path.join(OUT, "dem_dose_vs_tilt.png")
    fig.savefig(fn, dpi=150)
    plt.close(fig)
    print("wrote", fn)


def plot_taps():
    if not os.path.exists(os.path.join(RES, "leaktap.json")):
        return
    r = load("leaktap")
    t = np.array(r["log"]["t"])
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9, 3.4), gridspec_kw=dict(width_ratios=[1.6, 1]))
    a1.plot(t, r["log"]["ke_uJ"], color=PAL[0])
    for tk in r["tap_times_s"]:
        a1.axvline(tk, color=PAL[1], lw=1, alpha=0.8)
    a1.set_ylim(bottom=0)
    a1.axvspan(0, 0.25, color=GRID, alpha=0.5, lw=0)
    a1.text(0.125, a1.get_ylim()[1] * 0.9, "tilt", ha="center", fontsize=8, color=INK2)
    a1.text(0.98, 0.9, f"dispensed: {r['log']['m_disp_mg'][-1]:.0f} mg (whole run)", transform=a1.transAxes,
            ha="right", fontsize=9, color=INK)
    a1.set_xlabel("time (s)")
    a1.set_ylabel("bed kinetic energy (uJ)")
    a1.set_title("45 deg, no rotation: hold, then 4 taps (orange lines)", loc="left", fontsize=10)
    labels = [f"tap {k + 1}" for k in range(len(r["mass_per_tap_mg"]))]
    a2.bar(np.arange(len(labels)), r["mass_per_tap_mg"], 0.6, color=PAL[1], label="no rotation (45 deg)")
    if os.path.exists(os.path.join(RES, "sequence.json")):
        s = load("sequence")
        a2.plot(np.arange(len(s["m_per_tap_mg"])), s["m_per_tap_mg"], "o", color=PAL[0], ms=8, mec=SURF,
                mew=2, label=f"after 1 rev ({s['tilt_deg']:.0f} deg)")
    for k, v in enumerate(r["mass_per_tap_mg"]):
        a2.text(k, v + 0.1, f"{v:.0f}", ha="center", va="bottom", fontsize=8, color=PAL[1])
    a2.set_xticks(np.arange(len(labels)), labels)
    a2.set_ylabel("mg per tap")
    a2.set_title("Mass per tap", loc="left", fontsize=10)
    a2.legend(loc="upper right")
    a2.grid(axis="x", visible=False)
    fig.tight_layout()
    fn = os.path.join(OUT, "dem_tap_response.png")
    fig.savefig(fn, dpi=150)
    plt.close(fig)
    print("wrote", fn)


def plot_repose():
    if not os.path.exists(os.path.join(RES, "repose.json")):
        return
    r = load("repose")
    fig, ax = plt.subplots(figsize=(5, 3))
    rr, hh = np.array(r["profile_r_mm"]), np.array(r["profile_h_mm"])
    ax.plot(rr, hh, "o-", color=PAL[0], ms=4, lw=1.5)
    ax.set_xlabel("radius (mm)")
    ax.set_ylabel("heap surface height (mm)")
    ax.set_aspect("equal")
    ax.set_title(f"Lifted-cylinder heap: angle of repose {r['angle_of_repose_deg']:.0f} deg",
                 loc="left", fontsize=10)
    fig.tight_layout()
    fn = os.path.join(OUT, "dem_repose.png")
    fig.savefig(fn, dpi=150)
    plt.close(fig)
    print("wrote", fn)


if __name__ == "__main__":
    what = sys.argv[1:] or ["gif", "plots"]
    if "gif" in what:
        make_gif()
    if "plots" in what:
        plot_sequence()
        plot_dose()
        plot_taps()
        plot_repose()
