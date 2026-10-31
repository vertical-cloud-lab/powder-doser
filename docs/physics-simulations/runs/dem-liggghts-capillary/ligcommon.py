"""Shared helpers for the small LIGGGHTS-PUBLIC 3.8 test cases (salt reference powder).

Each method folder carries its own copy so it can be rerun stand-alone.
"""
from __future__ import annotations

import glob
import json
import math
import os
import re
import subprocess
import time

import numpy as np

# Reference powder: table salt (NaCl) as in the PR #180 LIGGGHTS auger twin
SALT = dict(
    density=2165.0,                     # kg/m3, particle density
    diam_mm=(0.361, 0.425, 0.489),      # three sizes
    frac=(0.3, 0.4, 0.3),               # number fractions
    youngs=2.0e5,                       # Pa, reduced (as in #180)
    poisson=0.3,
    restitution=0.5,
    mu_pp=0.5, mu_pw=0.4, mu_roll=0.3,  # sliding pp / pw, EPSD2 rolling
)
# SJKR cohesion energy density for the "cohesive" variant (J/m3); see README for the Bond number
CED_COHESIVE = 6000.0


def rayleigh_dt(d_min, rho=SALT["density"], E=SALT["youngs"], nu=SALT["poisson"]):
    G = E / (2 * (1 + nu))
    r = 0.5 * d_min
    return math.pi * r * math.sqrt(rho / G) / (0.1631 * nu + 0.8766)


def default_dt(scale=1.0):
    return 0.2 * rayleigh_dt(SALT["diam_mm"][0] * 1e-3 * scale)


def mean_particle_volume(scale=1.0):
    d = np.array(SALT["diam_mm"]) * 1e-3 * scale
    return float(np.sum(np.array(SALT["frac"]) * math.pi / 6 * d ** 3))


def bond_number_sjkr(ced, d, E=SALT["youngs"], nu=SALT["poisson"], rho=SALT["density"], g=9.81):
    """Pull-off Bond number of an SJKR (Hertz + k*A) contact between two equal spheres.

    Net normal force F(delta) = (4/3) E* sqrt(R*) delta^1.5 - k*pi*R*delta.  Its most
    attractive value is (4/27) A^3/B^2 with A = k*pi*R, B = (4/3) E* sqrt(R*).
    Bo = that pull-off force / particle weight.
    """
    R = 0.5 * d
    Es = E / (2 * (1 - nu ** 2))
    Rs = R / 2
    A = ced * math.pi * R
    B = 4.0 / 3.0 * Es * math.sqrt(Rs)
    F = 4.0 / 27.0 * A ** 3 / B ** 2
    m = rho * math.pi / 6 * d ** 3
    return F / (m * g), F


def header(box, periodic="f f f", ced=0.0, scale=1.0, mu_pw=None, mu_roll_pw=None, extra_types=0,
           dt=None, gravity=True, cohesion_walls=False, skin=None, extra_pp_props="", pair_cohesion=None):
    """Standard LIGGGHTS header: box, materials (2 types: 1 = grains, 2 = walls), pair style, templates."""
    s = SALT
    mu_pw = s["mu_pw"] if mu_pw is None else mu_pw
    mu_rpw = s["mu_roll"] if mu_roll_pw is None else mu_roll_pw
    r = [0.5 * d * 1e-3 * scale for d in s["diam_mm"]]
    dt = dt or default_dt(scale)
    skin = skin or r[1]
    coh = ""
    ced_line = ""
    if pair_cohesion is not None:
        coh = f"cohesion {pair_cohesion}"
    elif ced > 0:
        coh = "cohesion sjkr"
        ced_line = f"fix m6 all property/global cohesionEnergyDensity peratomtypepair 2 {ced} {ced} {ced} {ced}\n"
    xlo, xhi, ylo, yhi, zlo, zhi = box
    txt = f"""atom_style      granular
atom_modify     map array
boundary        {periodic}
newton          off
communicate     single vel yes
units           si
soft_particles  yes
region          domain block {xlo:.6e} {xhi:.6e} {ylo:.6e} {yhi:.6e} {zlo:.6e} {zhi:.6e} units box
create_box      2 domain
neighbor        {skin:.4e} bin
neigh_modify    delay 0

fix m1 all property/global youngsModulus peratomtype {s['youngs']:.4e} {s['youngs']:.4e}
fix m2 all property/global poissonsRatio peratomtype {s['poisson']} {s['poisson']}
fix m3 all property/global coefficientRestitution peratomtypepair 2 {s['restitution']} {s['restitution']} {s['restitution']} {s['restitution']}
fix m4 all property/global coefficientFriction peratomtypepair 2 {s['mu_pp']} {mu_pw} {mu_pw} {mu_pw}
fix m5 all property/global coefficientRollingFriction peratomtypepair 2 {s['mu_roll']} {mu_rpw} {mu_rpw} {mu_rpw}
{ced_line}{extra_pp_props}
pair_style gran model hertz tangential history {coh} rolling_friction epsd2
pair_coeff * *
timestep {dt:.4e}
"""
    if gravity:
        txt += "fix gravi all gravity 9.81 vector 0.0 0.0 -1.0\n"
    txt += f"""
fix pts1 all particletemplate/sphere 15485863 atom_type 1 density constant {s['density']} radius constant {r[0]:.6e}
fix pts2 all particletemplate/sphere 15485867 atom_type 1 density constant {s['density']} radius constant {r[1]:.6e}
fix pts3 all particletemplate/sphere 32452843 atom_type 1 density constant {s['density']} radius constant {r[2]:.6e}
fix pdd  all particledistribution/discrete/numberbased 49979687 3 pts1 {s['frac'][0]} pts2 {s['frac'][1]} pts3 {s['frac'][2]}
"""
    wall_coh = coh if cohesion_walls else ""
    wall_model = f"model hertz tangential history {wall_coh} rolling_friction epsd2"
    return txt, wall_model, dt


def run_liggghts(workdir, infile, log="log.liggghts", screen="screen.txt"):
    env = dict(os.environ, OMP_NUM_THREADS="1")
    t0 = time.time()
    p = subprocess.run(["liggghts", "-in", infile, "-log", log, "-echo", "none", "-screen", screen],
                       cwd=workdir, capture_output=True, text=True, env=env)
    wall = time.time() - t0
    tail = ""
    try:
        with open(os.path.join(workdir, screen)) as f:
            tail = f.read()[-3000:]
    except OSError:
        pass
    return p.returncode, wall, tail + p.stdout[-1000:] + p.stderr[-1000:]


def read_dump(path):
    """LIGGGHTS 'custom' text dump -> (step, columns dict)."""
    with open(path) as f:
        lines = f.readlines()
    step = int(lines[1])
    n = int(lines[3])
    cols = lines[8].split()[2:]
    if n == 0:
        return step, {c: np.zeros(0) for c in cols}
    A = np.loadtxt(lines[9:9 + n], ndmin=2)
    return step, {c: A[:, i] for i, c in enumerate(cols)}


def dump_series(pattern):
    files = glob.glob(pattern)
    key = lambda p: int(re.findall(r"(\d+)", os.path.basename(p))[-1])  # noqa: E731
    return sorted(files, key=key)


def save_animation(frames, gif_path, mp4_path, fps=10, max_width=640):
    """frames: list of HxWx3 uint8 arrays. GIF is downscaled to <= max_width px."""
    import imageio.v2 as imageio
    import imageio_ffmpeg  # noqa: F401  (provides the ffmpeg binary)
    from PIL import Image

    gif_frames = []
    for fr in frames:
        im = Image.fromarray(fr)
        if im.width > max_width:
            h = int(round(im.height * max_width / im.width))
            im = im.resize((max_width, h), Image.LANCZOS)
        gif_frames.append(np.asarray(im.convert("P", palette=Image.ADAPTIVE, colors=128).convert("RGB")))
    imageio.mimsave(gif_path, gif_frames, duration=1.0 / fps, loop=0)
    # even dims for yuv420p
    h, w = frames[0].shape[:2]
    h2, w2 = h - h % 2, w - w % 2
    writer = imageio.get_writer(mp4_path, fps=fps, codec="libx264", pixelformat="yuv420p",
                                ffmpeg_params=["-crf", "26", "-preset", "medium"], macro_block_size=1)
    for fr in frames:
        writer.append_data(fr[:h2, :w2])
    writer.close()


def fig_to_array(fig):
    fig.canvas.draw()
    buf = np.asarray(fig.canvas.buffer_rgba())[:, :, :3].copy()
    return buf


def write_json(path, obj):
    with open(path, "w") as f:
        json.dump(obj, f, indent=1)


# ---------------- plotting helpers (palette: dataviz default categorical slots) ----------------
COLORS = {"dry": "#2a78d6", "coh": "#eb6834", "cap_low": "#1baf7a", "cap_high": "#eda100"}
INK = "#0b0b0b"
INK2 = "#52514e"
SURF = "#fcfcfb"
SPEED_RAMP = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]


def speed_cmap():
    from matplotlib.colors import LinearSegmentedColormap
    return LinearSegmentedColormap.from_list("speed", SPEED_RAMP)


def style_axes(ax):
    ax.set_facecolor(SURF)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(INK2)
    ax.tick_params(colors=INK2, labelsize=8)
    ax.xaxis.label.set_color(INK)
    ax.yaxis.label.set_color(INK)
    ax.grid(True, color="#e6e5e1", lw=0.6)
    ax.set_axisbelow(True)


def draw_grains(ax, x, z, r, c=None, cmap=None, vmax=None, color="#9a9a96", edge=None):
    from matplotlib.collections import EllipseCollection
    if len(x) == 0:
        return None
    ec = EllipseCollection(2 * r, 2 * r, np.zeros_like(r), units="xy", offsets=np.c_[x, z],
                           offset_transform=ax.transData, linewidths=0)
    if c is not None:
        ec.set_array(c)
        ec.set_cmap(cmap)
        ec.set_clim(0, vmax)
    else:
        ec.set_facecolor(color)
    ax.add_collection(ec)
    return ec
