"""Render LIGGGHTS auger dumps to a cut-away movie (OVITO + matplotlib).

Left panel: OVITO Tachyon render in the lab frame (gravity down, exit at
the lower right). The near half of the rotating auger mesh is clipped
away so the grains inside the flights are visible; grains are coloured
by speed. Right panel: cumulative dispensed mass from ``outflow.txt``
with the motor state.

Usage:
    python render.py --case /tmp/dem/runs/baseline --out baseline.mp4 --gif baseline.gif
"""

from __future__ import annotations

import argparse
import glob
import json
import math
import os
import re
import subprocess
import sys
import tempfile

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def read_stl(path):
    V = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line.startswith("vertex"):
                V.append([float(x) for x in line.split()[1:]])
    V = np.asarray(V) * 1e-3
    return V.reshape(-1, 3, 3)


def rot_z(th):
    c, s = math.cos(th), math.sin(th)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1.0]])


def rot_y(b):
    c, s = math.cos(b), math.sin(b)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def read_dump(path):
    with open(path) as f:
        f.readline()
        step = int(f.readline())
        f.readline()
        n = int(f.readline())
        for _ in range(5):
            f.readline()
        A = np.loadtxt(f, ndmin=2) if n else np.zeros((0, 9))
    return step, A


def speed_colors(v, vmax):
    import matplotlib
    cmap = matplotlib.colormaps["inferno"]
    s = np.clip(v / vmax, 0, 1)
    c = cmap(0.15 + 0.8 * s)[:, :3]
    return c


def face_colors(tris_mm, geo):
    """Colour the auger mesh by part: tube/funnel wall, flight, solid core."""
    c = tris_mm.mean(axis=1)
    r = np.hypot(c[:, 0], c[:, 1])
    z = c[:, 2]
    slope = (geo["funnel_top_r"] - geo["exit_r"]) / geo["funnel_h"]
    r_out = np.where(z >= geo["funnel_h"], geo["bore_r"], geo["exit_r"] + slope * np.clip(z, 0, None))
    col = np.tile([0.05, 0.22, 0.55], (len(c), 1))           # flight: blue (Tachyon lighting brightens a lot)
    col[r > r_out - 0.15] = [0.50, 0.58, 0.68]               # tube and funnel wall: grey-blue
    if geo.get("shaft_r", 0) > 0:
        tip = geo.get("tip_r")
        if tip is not None:
            r_in = np.where(z >= geo["funnel_h"], geo["shaft_r"],
                            tip + (geo["shaft_r"] - tip) * np.clip(z, 0, None) / geo["funnel_h"])
        else:
            r_in = np.full_like(z, geo["shaft_r"])
        col[(r < r_in + 0.15) & ((z > geo["funnel_h"] - 0.2) | (tip is not None))] = [0.70, 0.36, 0.05]  # core: amber
    return col


def render_frame(A, tris, theta, beta, png, size, vmax, view_center, fov, colors=None):
    from ovito.data import DataCollection, Particles, TriangleMesh, SimulationCell
    from ovito.pipeline import Pipeline, StaticSource
    from ovito.vis import Viewport, TachyonRenderer, TriangleMeshVis, ParticlesVis

    Rd = rot_y(beta)
    data = DataCollection()
    cell = data.create_cell(np.array([[1e-3, 0, 0, -1], [0, 1e-3, 0, -1], [0, 0, 1e-3, -1]]), pbc=(False, False, False))
    cell.vis.enabled = False
    if len(A):
        pos = A[:, 3:6] @ Rd.T
        parts = data.create_particles(count=len(A))
        parts.create_property("Position", data=pos)
        parts.create_property("Radius", data=A[:, 2])
        sp = np.linalg.norm(A[:, 6:9], axis=1)
        parts.create_property("Color", data=speed_colors(sp, vmax))
    # rotate mesh with the auger, clip the half nearest the camera (y < 0)
    T = tris @ rot_z(theta).T
    cen_y = T.mean(axis=1)[:, 1]
    keep = cen_y > -2e-4
    T = T[keep] @ Rd.T
    # one TriangleMesh per part so each gets its own colour (wall / flight / core)
    cols = colors[keep] if colors is not None else np.tile([0.62, 0.72, 0.85], (len(T), 1))
    for col in np.unique(cols, axis=0):
        sel = np.all(cols == col, axis=1)
        mesh = TriangleMesh()
        verts = T[sel].reshape(-1, 3)
        mesh.set_vertices(verts)
        mesh.set_faces(np.arange(len(verts)).reshape(-1, 3))
        mesh.vis = TriangleMeshVis(color=tuple(col), transparency=0.08, highlight_edges=False)
        data.objects.append(mesh)
    pipe = Pipeline(source=StaticSource(data=data))
    pipe.add_to_scene()
    vp = Viewport(type=Viewport.Type.Ortho, camera_dir=(0, 1, 0), camera_up=(0, 0, 1),
                  camera_pos=view_center, fov=fov)
    vp.render_image(size=size, filename=png, background=(1, 1, 1),
                    renderer=TachyonRenderer(ambient_occlusion=False, shadows=False, antialiasing_samples=4))
    pipe.remove_from_scene()


def mass_panel(t_now, t, m, meta, png, size, exp_rate=None, ymax=None):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    w, h = size
    fig, ax = plt.subplots(figsize=(w / 100, h / 100), dpi=100)
    t0 = meta["settle_s"]
    t_stop = t0 + meta["cfg"]["revs"] * meta["period_s"]
    sel = t <= t_now + 1e-9
    m0 = np.interp(t0, t, m)
    ax.plot(t[sel] - t0, m[sel] - m0, color="#1f5fa8", lw=2.2, label="DEM twin (cumulative)")
    if exp_rate is not None:
        tt = np.array([0, t_stop - t0])
        ax.plot(tt, exp_rate * tt, color="#c0504d", lw=1.5, ls="--", label=f"rig mean rate ({exp_rate:.0f} mg/s)")
    ax.axvspan(0, t_stop - t0, color="#e8f0e0", zorder=0)
    ax.axvline(t_stop - t0, color="0.4", lw=1, ls=":")
    ax.text(0.02, 0.97, "motor on", transform=ax.transAxes, va="top", fontsize=9, color="#4a7a2a")
    t_end = t_stop + meta["cfg"]["stop_s"]
    ax.set_xlim(-t0, t_end - t0)
    if ymax is None:
        ymax = max(1.0, (m[-1] - m0) * 1.08, (exp_rate or 0) * (t_stop - t0) * 1.05)
    ax.set_ylim(min(0.0, -0.02 * ymax), ymax)
    ax.set_xlabel("time since motor start (s)")
    ax.set_ylabel("dispensed mass (mg)")
    rev = max(0.0, (t_now - t0) / meta["period_s"])
    ax.set_title(f"t = {t_now - t0:5.2f} s   rotation = {min(rev, meta['cfg']['revs']):4.2f} rev", fontsize=10)
    ax.legend(loc="lower right", fontsize=8, frameon=False)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(png)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", required=True)
    ap.add_argument("--out", required=True, help="mp4 path")
    ap.add_argument("--gif", default=None)
    ap.add_argument("--every", type=int, default=1, help="use every n-th dump")
    ap.add_argument("--gif-every", type=int, default=2)
    ap.add_argument("--gif-width", type=int, default=720)
    ap.add_argument("--exp-rate", type=float, default=None, help="rig mean flow rate (mg/s) for the reference line")
    ap.add_argument("--title", default="")
    ap.add_argument("--fps", type=int, default=25)
    ap.add_argument("--max-frames", type=int, default=100000)
    ap.add_argument("--frames-dir", default=None, help="persistent frame cache (enables incremental rendering)")
    ap.add_argument("--frames-only", action="store_true", help="render missing frames, skip video assembly")
    ap.add_argument("--ymax", type=float, default=None)
    ap.add_argument("--stride", type=int, default=1, help="render only frames i with i %% stride == offset (parallel workers)")
    ap.add_argument("--offset", type=int, default=0)
    a = ap.parse_args()

    from PIL import Image, ImageDraw, ImageFont

    meta = json.load(open(os.path.join(a.case, "case.json")))
    cfg = meta["cfg"]
    tris = read_stl(os.path.join(a.case, "auger.stl"))
    fcol = face_colors(tris * 1e3, meta["geometry"])
    O = np.loadtxt(os.path.join(a.case, "outflow.txt"), comments="#", ndmin=2)
    t_log, m_log = O[:, 0], O[:, 1] * 1e6
    beta = math.radians(cfg["incline_deg"] - 90.0)
    files = sorted(glob.glob(os.path.join(a.case, "dump", "p.*.txt")), key=lambda p: int(re.findall(r"p\.(\d+)\.txt", p)[0]))
    if a.frames_only and files:
        files = files[:-1]  # the newest dump may still be being written
    files = files[:: a.every][: a.max_frames]
    dt = meta["dt"]
    omega = 2 * math.pi / meta["period_s"]
    t_stop = meta["settle_s"] + cfg["revs"] * meta["period_s"]
    # view: bounding box of the mesh in display frame
    Rd = rot_y(beta)
    bb = (tris.reshape(-1, 3) @ Rd.T)
    lo, hi = bb.min(0), bb.max(0)
    lo[2] -= 4e-3
    center = (lo + hi) / 2
    fov = 0.55 * max(hi[0] - lo[0], hi[2] - lo[2])
    W, H = 1280, 640
    tmp = a.frames_dir or tempfile.mkdtemp(prefix="render_")
    os.makedirs(tmp, exist_ok=True)
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 15)
        font_s = ImageFont.truetype("DejaVuSans.ttf", 14)
    except OSError:
        font = font_s = ImageFont.load_default()
    geo = meta["geometry"]
    z_top = geo["funnel_h"] + geo["n_turns"] * geo["pitch"] + geo["flight_t"] + geo["feed_h"]
    for i, fpath in enumerate(files):
        if i % a.stride != a.offset or os.path.exists(os.path.join(tmp, f"f{i:05d}.png")):
            continue
        step, A = read_dump(fpath)
        # hide feed-zone spill that leaves through the open top of the meshed section
        # (it is deleted at the box edge and never reaches the outlet)
        if len(A):
            zz, rr = A[:, 5] * 1e3, np.hypot(A[:, 3], A[:, 4]) * 1e3
            A = A[(zz < z_top - 0.2) & ~((rr > geo["bore_r"] + 0.3) & (zz > 0))]
        t = step * dt
        theta = omega * min(max(0.0, t - meta["settle_s"]), max(0.0, t_stop - meta["settle_s"]))
        left = os.path.join(tmp, f"l{os.getpid()}.png")
        right = os.path.join(tmp, f"r{os.getpid()}.png")
        render_frame(A, tris, theta, beta, left, (W - 480, H), vmax=0.08, view_center=tuple(center), fov=fov, colors=fcol)
        mass_panel(t, t_log, m_log, meta, right, (480, H), a.exp_rate, a.ymax)
        img = Image.new("RGB", (W, H), "white")
        img.paste(Image.open(left).convert("RGB"), (0, 0))
        img.paste(Image.open(right).convert("RGB"), (W - 480, 0))
        d = ImageDraw.Draw(img)
        d.text((14, 10), a.title, fill=(20, 20, 20), font=font)
        d.text((14, H - 26), f"{len(A):,} grains | colour = speed (0-0.08 m/s) | near half of auger cut away | gravity down",
               fill=(60, 60, 60), font=font_s)
        img.save(os.path.join(tmp, f"f{i:05d}.png"))
        if i % 20 == 0:
            print(f"frame {i}/{len(files)} t={t:.3f}", flush=True)
    if a.frames_only:
        return
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(a.fps), "-i", os.path.join(tmp, "f%05d.png"),
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "23", "-movflags", "+faststart", a.out], check=True)
    if a.gif:
        pal = os.path.join(tmp, "pal.png")
        vf = f"select='not(mod(n\\,{a.gif_every}))',setpts=N/({a.fps}*TB),scale={a.gif_width}:-1:flags=lanczos"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(a.fps), "-i", os.path.join(tmp, "f%05d.png"),
                        "-vf", vf + ",palettegen=max_colors=128", pal], check=True)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(a.fps), "-i", os.path.join(tmp, "f%05d.png"),
                        "-i", pal, "-lavfi", vf + " [x]; [x][1:v] paletteuse=dither=bayer:bayer_scale=4", a.gif], check=True)
    print("wrote", a.out, a.gif or "")


if __name__ == "__main__":
    main()
