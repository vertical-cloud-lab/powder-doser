"""Which exit does the H2D's 6-7 Oct auger have? Its timelapse vs the two exit designs.

The H2D keeps no job files for cloud prints, but its timelapse records one frame per
layer. Augers print exit-down, so the first frames show the exit end. This script
crops the auger's top layer from frames of ``video_2026-10-07_01-11-34.mp4`` and
draws, at the same heights, the cross-sections of

* the CAD ``threaded-auger-final`` (12 mm cone to a Ø3 hole; the twin's rig auger), and
* the A1 mini's ``auger_open_end`` (no cone; profile from ``../auger_open_end_profile.csv``).

Layer height: 0.08 mm/frame. 3164 frames make 253 mm (the CAD is 250 mm), and the gear
starts at frame about 980 and ends at about 1110, which is 78.4-88.8 mm against the
CAD's 78.6-88.6 mm.

    python h2d_exit_evidence.py [path/to/video_2026-10-07_01-11-34.mp4]

Without the video, the committed crops in ``frames/`` are used.
"""

import os
import subprocess
import sys

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Ellipse, Polygon  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
FRAMES = os.path.join(HERE, "frames")
INK, INK2, SURF = "#0b0b0b", "#52514e", "#fcfcfb"
WALL, CORE = "#2a78d6", "#eb6834"  # wall / flight and core, as in ../compare_profiles.py

LAYER_MM = 0.08
LAYERS = [4, 15, 30, 60, 90, 120, 150, 200]
BOX = (826, 296, 966, 381)  # auger top-layer crop in the 1680x1080 frame
FINAL = 3100
FINAL_BOX = (700, 300, 1040, 1080)
SQUASH = 0.32  # the camera sees the top layer almost edge-on


def extract(video):
    import imageio_ffmpeg
    from PIL import Image

    os.makedirs(FRAMES, exist_ok=True)
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    sel = "+".join(f"eq(n\\,{n})" for n in LAYERS + [FINAL])
    tmp = os.path.join(FRAMES, "_raw_%02d.png")
    subprocess.run([ff, "-hide_banner", "-loglevel", "error", "-y", "-i", video, "-vf", f"select='{sel}'",
                    "-vsync", "vfr", tmp], check=True)
    for k, n in enumerate(LAYERS + [FINAL]):
        raw = tmp % (k + 1)
        im = Image.open(raw).convert("RGB")
        box = FINAL_BOX if n == FINAL else BOX
        im.crop(box).save(os.path.join(FRAMES, f"layer_{n:04d}.jpg"), quality=92)
        os.remove(raw)


def cad_radii(z):
    """threaded-auger-final near the exit: bore 1.5 -> 10.45 and core 0.43 -> 3.98 over 12 mm."""
    f = np.clip(z / 12.0, 0, 1)
    return 1.5 + f * (10.45 - 1.5), 0.43 + f * (3.98 - 0.43), 12.5


def open_radii(z, prof):
    zp, bore, core, outer = prof[:, 0], prof[:, 1], prof[:, 2], prof[:, 3]
    # below z = 2 the core is a pin too thin to close a wall loop; continue its cone (r = 1.04 + z/2)
    core = np.where(core > 0, core, 1.04 + 0.5 * zp)
    return np.interp(z, zp, bore), np.interp(z, zp, core), np.interp(z, zp, outer)


def section(ax, bore, core, outer, z, pitch):
    """Top layer at height z as the camera sees it: material blue/orange, open bore light."""
    sq = SQUASH
    ax.add_patch(Ellipse((0, 0), 2 * outer, 2 * outer * sq, color=WALL, alpha=0.85, lw=0))
    ax.add_patch(Ellipse((0, 0), 2 * bore, 2 * bore * sq, color=SURF, lw=0))
    ax.add_patch(Ellipse((0, 0), 2 * bore, 2 * bore * sq, fill=False, ec=WALL, lw=0.6))
    # single-start flight: one radial strip from the core to the bore wall
    th = 2 * np.pi * z / pitch
    c, s = np.cos(th), np.sin(th)
    nx, ny = -s * 0.25, c * 0.25
    pts = [(core * c + nx, (core * s + ny) * sq), (bore * c + nx, (bore * s + ny) * sq),
           (bore * c - nx, (bore * s - ny) * sq), (core * c - nx, (core * s - ny) * sq)]
    ax.add_patch(Polygon(pts, closed=True, color=WALL, alpha=0.85, lw=0))
    ax.add_patch(Ellipse((0, 0), 2 * core, 2 * core * sq, color=CORE, alpha=0.9, lw=0))
    ax.set_xlim(-13.5, 13.5)
    ax.set_ylim(-13.5 * sq * 1.6, 13.5 * sq * 1.6)
    ax.set_aspect("equal")
    ax.axis("off")


def main():
    from PIL import Image

    if len(sys.argv) > 1:
        extract(sys.argv[1])
    prof = np.loadtxt(os.path.join(HERE, "..", "auger_open_end_profile.csv"), delimiter=",", skiprows=1)

    ncol = len(LAYERS)
    fig = plt.figure(figsize=(15, 4.9), facecolor=SURF)
    gs = fig.add_gridspec(3, ncol + 2, width_ratios=[2.0, 0.5] + [1] * ncol, height_ratios=[1.0, 0.5, 0.5],
                          wspace=0.05, hspace=0.08, left=0.005, right=0.995, top=0.85, bottom=0.11)
    ax0 = fig.add_subplot(gs[:, 0])
    ax0.imshow(Image.open(os.path.join(FRAMES, f"layer_{FINAL:04d}.jpg")))
    ax0.set_title("H2D timelapse, last layers (finished 04:49 UTC, 7 Oct)", fontsize=8.5, color=INK, loc="left")
    ax0.axis("off")
    for k, n in enumerate(LAYERS):
        z = n * LAYER_MM
        a = fig.add_subplot(gs[0, k + 2])
        a.imshow(Image.open(os.path.join(FRAMES, f"layer_{n:04d}.jpg")))
        a.set_title(f"layer {n}\nz ≈ {z:.1f} mm", fontsize=8, color=INK)
        a.axis("off")
        b = fig.add_subplot(gs[1, k + 2])
        section(b, *cad_radii(z), z, 10.4)
        c = fig.add_subplot(gs[2, k + 2])
        section(c, *open_radii(z, prof), z, 10.42)
        if k == 0:
            a.text(-0.08, 0.5, "H2D print,\ntop layer", transform=a.transAxes, ha="right", va="center",
                   fontsize=8, color=INK)
            b.text(-0.08, 0.5, "CAD cone\n(Ø3 exit)", transform=b.transAxes, ha="right", va="center",
                   fontsize=8, color=INK)
            c.text(-0.08, 0.5, "A1 mini\nopen end", transform=c.transAxes, ha="right", va="center",
                   fontsize=8, color=INK)
    fig.suptitle("The H2D's 6–7 Oct auger has the cone exit: its first 12 mm print as a nearly solid disk that opens up "
                 "into the tube", fontsize=10.5, color=INK, x=0.01, ha="left")
    fig.text(0.01, 0.015,
             "Top row: the auger's top layer in the H2D timelapse (one frame per 0.08 mm layer; the camera sees it "
             "almost edge-on, and the diagonal lines are sparse infill inside solid plastic).\nLower rows: the two "
             "exit designs' cross-sections at the same heights, drawn at the same viewing angle "
             "(wall and flight blue, core orange, open bore light).",
             fontsize=7.5, color=INK2, ha="left", va="bottom")
    out = os.path.join(HERE, "h2d_oct7_exit_evidence.png")
    fig.savefig(out, dpi=110, facecolor=SURF)
    print(out)


if __name__ == "__main__":
    main()
