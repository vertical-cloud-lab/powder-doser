"""Shared look for the optimization slides.

Every slide is drawn on a 13.333 x 7.5 in canvas, the size of a 16:9
PowerPoint slide, so a matplotlib point is a PowerPoint point when the PNG
fills the slide.  The smallest text anywhere is 24 pt.  The message sits at
the same spot, top left, on every slide; graphs have no titles, horizontal
two-line y labels above the axis, no grid, and faded same-colour callout
lines (no arrowheads) instead of legends.
"""
from __future__ import annotations

import io
import shutil
import subprocess
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib import font_manager  # noqa: E402
from PIL import Image  # noqa: E402

for f in font_manager.findSystemFonts():
    if "Lato" in f:
        font_manager.fontManager.addfont(f)

FIG_IN = (13.3334, 7.5)    # 1920 x 1080 at 144 dpi (13.3333 rounds down to 1919)
DPI_SCREEN = 144          # 1920 x 1080
DPI_PRINT = 300           # 4000 x 2250, for the stills

INK = "#0b0b0b"
INK2 = "#52514e"
GREY = "#83827d"          # de-emphasised marks and labels
LEADER = "#8d8c88"
FAINT = "#c9c7c1"         # earlier steps, pushed back
GHOST = "#e4e2dc"
BLUE = "#2a78d6"          # the optimizer's results
BLUE_LIGHT = "#cde2fb"
ORANGE = "#eb6834"        # hand tuning
ORANGE_LIGHT = "#fbd9c9"

FS = 24                   # floor for every piece of text
FS_TITLE = 32

plt.rcParams.update({
    "font.family": ["Lato", "DejaVu Sans"],
    "font.size": FS,
    "axes.labelsize": FS,
    "xtick.labelsize": FS,
    "ytick.labelsize": FS,
    "axes.edgecolor": INK2,
    "axes.labelcolor": INK,
    "xtick.color": INK2,
    "ytick.color": INK2,
    "xtick.labelcolor": INK,
    "ytick.labelcolor": INK,
    "axes.linewidth": 1.4,
    "xtick.major.width": 1.4,
    "ytick.major.width": 1.4,
    "xtick.major.size": 7,
    "ytick.major.size": 7,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": False,
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "savefig.facecolor": "white",
    "lines.solid_capstyle": "round",
})

TITLE_XY = (0.045, 0.935)


def slide(message: str | None = None):
    """A blank 16:9 slide with the message, if any, at the fixed spot."""
    fig = plt.figure(figsize=FIG_IN)
    if message:
        fig.text(*TITLE_XY, message, fontsize=FS_TITLE, color=INK, ha="left", va="top",
                 linespacing=1.15)
    return fig


def style_axes(ax, xlim, ylim, xticks, yticks, xfmt=None, yfmt=None):
    """Left and bottom axis lines only, pushed out from the data and ending at
    the outermost ticks; ticks at round values only."""
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.set_xticks(xticks)
    ax.set_yticks(yticks)
    if xfmt:
        ax.set_xticklabels([xfmt(v) for v in xticks])
    if yfmt:
        ax.set_yticklabels([yfmt(v) for v in yticks])
    for side in ("left", "bottom"):
        ax.spines[side].set_position(("outward", 14))
    ax.spines["left"].set_bounds(yticks[0], yticks[-1])
    ax.spines["bottom"].set_bounds(xticks[0], xticks[-1])
    ax.tick_params(pad=6)


def ylabel_top(ax, text, x=-0.0, y=1.045):
    """Horizontal y label above the axis, left aligned with it."""
    ax.text(x, y, text, transform=ax.transAxes, ha="left", va="bottom", fontsize=FS,
            color=INK, linespacing=1.2)


def xlabel(ax, text, pad=14):
    ax.set_xlabel(text, fontsize=FS, color=INK, labelpad=pad, loc="left")


def callout(ax, text, xy, xytext, color, ha="left", va="center", alpha=0.45, fs=FS,
            weight="normal", zorder=6, lw=1.8, coords="data"):
    """Text in the series colour, joined to its mark by a faded line with no
    arrowhead."""
    return ax.annotate(text, xy=xy, xytext=xytext, textcoords=coords, fontsize=fs, color=color,
                       ha=ha, va=va, fontweight=weight, zorder=zorder,
                       arrowprops=dict(arrowstyle="-", color=color, alpha=alpha, lw=lw,
                                       shrinkA=6, shrinkB=7))


def save(fig, path: Path, dpi=DPI_SCREEN):
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=dpi)


def to_image(fig, dpi=DPI_SCREEN) -> Image.Image:
    buf = io.BytesIO()
    fig.savefig(buf, dpi=dpi, format="png")
    buf.seek(0)
    return Image.open(buf).convert("RGB")


def _crossfade(frames, holds, fade_s, fps, fades=None):
    """fades: the cross-fade into each frame (s); default fade_s for all."""
    seq = []
    for i, (im, hold) in enumerate(zip(frames, holds)):
        f = fade_s if fades is None else fades[i]
        if i > 0 and f > 0:
            prev = frames[i - 1]
            n = max(1, round(f * fps))
            for k in range(1, n + 1):
                seq.append(Image.blend(prev, im, k / (n + 1)))
        seq += [im] * max(1, round(hold * fps))
    return seq


def write_gif(frames, holds, path: Path, fade_s=0.25, fps=12, width=1280, fades=None):
    """Build GIF: each step held for its time, short cross-fades between.
    Identical consecutive frames are merged so the file stays small."""
    seq = _crossfade(frames, holds, fade_s, fps, fades)
    if width and seq[0].width != width:
        h = round(seq[0].height * width / seq[0].width)
        seq = [im.resize((width, h), Image.LANCZOS) for im in seq]
    merged, durs = [], []
    for im in seq:
        if merged and np.array_equal(np.asarray(merged[-1]), np.asarray(im)):
            durs[-1] += 1000 / fps
        else:
            merged.append(im)
            durs.append(1000 / fps)
    pal = [im.quantize(colors=128, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
           for im in merged]
    path.parent.mkdir(parents=True, exist_ok=True)
    pal[0].save(path, save_all=True, append_images=pal[1:], duration=[round(d) for d in durs],
                loop=0, optimize=True, disposal=2)


def write_mp4(frames, holds, path: Path, fade_s=0.25, fps=30, fades=None):
    """Same build as an H.264 MP4 at the frames' size (1920 x 1080)."""
    seq = _crossfade(frames, holds, fade_s, fps, fades)
    w, h = seq[0].size
    ff = subprocess.Popen(
        [shutil.which("ffmpeg"), "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
         "-s", f"{w}x{h}", "-r", str(fps), "-i", "-",
         "-vf", "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p",
         "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-profile:v", "high",
         "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
         "-movflags", "+faststart", str(path)], stdin=subprocess.PIPE)
    for im in seq:
        ff.stdin.write(im.tobytes())
    ff.stdin.close()
    assert ff.wait() == 0
