"""Put the rendered doser frames together into the procedure slide video.

    python3 compose_procedure.py --frames /tmp/procedure_frames

Writes, next to this script:

- ``procedure_annotated.mp4`` (1920 x 1080, 30 fps) and ``.gif`` (1280 x 720,
  15 fps): the doser on the left; on the right, the three stages appear one
  at a time with the settings the optimizer chose for them (in blue), the
  earlier stages greyed out, and the balance reading of the real dose
  drawing itself underneath.
- ``procedure_plain.mp4`` (1920 x 1080: the square doser view centred on
  white) and ``procedure_plain_square.mp4`` / ``.gif`` (1080 x 1080 / 720 x
  720): the doser only.  The one piece of text is the playback speed (``x6``)
  in the bottom-left corner, as in the #174 video.
- ``procedure_still_start.png``, ``procedure_still_end.png``: the first and
  last annotated frames, for the slides before and after the video.

The frames come from ``render_procedure.py`` (one 1080 x 1080 PNG per entry
of ``timeline.json``); the stage, playback speed and balance reading for
each frame come from ``timeline_overlay.json`` (``make_timeline.py``).
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import slide_style as ss  # noqa: E402
from slide_style import BLUE, FAINT, FS, GREY, INK, INK2  # noqa: E402

plt = ss.plt
W, H = 1920, 1080
SQ = 1080
FPS = 30
LATO = "/usr/share/fonts/truetype/lato/Lato-Regular.ttf"

# What each stage does, and the knobs the optimizer set for it (bo-005).  The
# blue parts are the optimizer's knobs; the rest is how the stage works.
STAGES = [
    ("Bulk", [[("tilt ", INK), ("40°", BLUE), (", ", INK), ("100 rpm", BLUE),
               (", taps ", INK), ("on", BLUE)],
              [("until ", INK), ("300 mg", BLUE), (" to go", INK)]]),
    ("Trickle", [[("tilt ", INK), ("10°", BLUE), (", taps ", INK), ("off", BLUE)],
                 [("speed set by the controller", INK)]]),
    ("Taps", [[("tilt ", INK), ("15°", BLUE), (", one tap at a time", INK)],
              [("until within ", INK), ("3 mg", BLUE)]]),
]
ORDER = {"Ready": 0, "Bulk": 1, "Trickle": 2, "Taps": 3, "Done": 4}


def _text_runs(fig, x, y, runs, color_override=None, size=FS):
    """Draw coloured runs of text on one line, left to right (figure coords)."""
    r = fig.canvas.get_renderer()
    for txt, col in runs:
        txt = txt.replace(" ", "\u00a0")
        t = fig.text(x, y, txt, fontsize=size, color=color_override or col, ha="left",
                     va="baseline")
        bb = t.get_window_extent(renderer=r)
        x += bb.width / fig.bbox.width


class Panel:
    """The right-hand panel, 840 x 1080."""

    def __init__(self, meta):
        self.meta = meta
        self.tt = np.array(meta["trace_t"])
        self.mm = np.array(meta["trace_m"])
        self.total = meta["outcomes"]["t_total_s"]

    def draw(self, f) -> Image.Image:
        fig = plt.figure(figsize=((W - SQ) / ss.DPI_SCREEN, H / ss.DPI_SCREEN))
        fig.canvas.draw()
        cur = ORDER[f["stage"]]
        y = 0.945
        for k, (name, lines) in enumerate(STAGES, start=1):
            if k > cur and cur < 4:
                break
            done = cur == 4
            active = k == cur
            col = None if (active or done) else FAINT
            fig.text(0.04, y, f"{k}", fontsize=FS, color=col or INK2, ha="left", va="baseline")
            fig.text(0.11, y, name, fontsize=FS, color=col or INK, ha="left", va="baseline",
                     fontweight="bold")
            for j, runs in enumerate(lines):
                _text_runs(fig, 0.11, y - 0.052 * (j + 1), runs, color_override=col)
            y -= 0.175
        if cur >= 1:
            _text_runs(fig, 0.04, 0.405, [("blue", BLUE), (": set by the optimizer", GREY)])
        # balance reading of the real dose, drawn up to now
        ax = fig.add_axes([0.17, 0.115, 0.76, 0.185])
        ss.style_axes(ax, (-2, 102), (-0.02, 0.53), [0, 50, 100], [0, 0.5],
                      xfmt=lambda v: f"{v:g} s" if v == 100 else f"{v:g}",
                      yfmt=lambda v: f"{v:g}")
        ax.text(-0.17, 1.17, "Powder in the cup (g)", transform=ax.transAxes, fontsize=FS,
                color=INK, ha="left", va="bottom")
        ax.axhline(0.5, color=GREY, lw=1.5, ls=(0, (5, 4)), zorder=1)
        rt = f["real_s"]
        sel = self.tt <= rt
        xs = np.append(self.tt[sel], rt)
        ys = np.append(self.mm[sel], np.interp(rt, self.tt, self.mm))
        ax.plot(xs, ys, color=INK, lw=2.6, zorder=3)
        if cur >= 1:
            ax.scatter([rt], [ys[-1]], s=60, color=INK, zorder=4, clip_on=False)
            ax.text(1.0, 1.17, f"{ys[-1]:.3f} g", transform=ax.transAxes, fontsize=FS,
                    color=INK, ha="right", va="bottom")
        img = ss.to_image(fig)
        plt.close(fig)
        return img.resize((W - SQ, H), Image.LANCZOS) if img.size != (W - SQ, H) else img


def speed_label(f) -> str | None:
    if f["seg"] in ("rest", "home", "end") or f["speed"] <= 0:
        return None
    s = f["speed"]
    return "×1" if abs(s - 1) < 0.05 else f"×{s:.0f}" if s >= 1.5 else f"×{s:.1f}"


def put_speed(img: Image.Image, label: str | None, size: int) -> Image.Image:
    if not label:
        return img
    d = ImageDraw.Draw(img)
    font = ImageFont.truetype(LATO, size)
    d.text((round(size * 0.6), img.height - round(size * 0.6)), label, font=font,
           fill=(131, 130, 125), anchor="ls")
    return img


def encode(frames_iter, size, out: Path, fps=FPS):
    w, h = size
    ff = subprocess.Popen(
        [shutil.which("ffmpeg"), "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
         "-s", f"{w}x{h}", "-r", str(fps), "-i", "-",
         "-vf", "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p",
         "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-profile:v", "high",
         "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
         "-movflags", "+faststart", str(out)], stdin=subprocess.PIPE)
    for im in frames_iter:
        ff.stdin.write(im.convert("RGB").tobytes())
    ff.stdin.close()
    assert ff.wait() == 0


def gif_from_mp4(mp4: Path, gif: Path, width: int, fps: int = 15):
    """Palette-optimised GIF of an MP4 (ffmpeg two-pass palette)."""
    pal = gif.with_suffix(".palette.png")
    vf = f"fps={fps},scale={width}:-1:flags=lanczos"
    subprocess.run([shutil.which("ffmpeg"), "-y", "-loglevel", "error", "-i", str(mp4), "-vf",
                    f"{vf},palettegen=max_colors=160:stats_mode=diff", str(pal)], check=True)
    subprocess.run([shutil.which("ffmpeg"), "-y", "-loglevel", "error", "-i", str(mp4), "-i",
                    str(pal), "-lavfi", f"{vf} [x]; [x][1:v] paletteuse=dither=bayer:bayer_scale=4"
                    ":diff_mode=rectangle", "-loop", "0", str(gif)], check=True)
    pal.unlink()


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--frames", default="/tmp/procedure_frames")
    ap.add_argument("--out", default=str(HERE))
    ap.add_argument("--only", choices=("annotated", "plain"), help="one version only")
    args = ap.parse_args()
    ov = json.load(open(HERE / "timeline_overlay.json"))
    frames, meta = ov["frames"], ov["meta"]
    out = Path(args.out)
    src = Path(args.frames)

    def cad(i):
        p = src / f"frame_{i:05d}.png"
        return Image.open(p).convert("RGB") if p.exists() else Image.new("RGB", (SQ, SQ), "white")

    panel = Panel(meta)
    cache = {}

    def annotated():
        for i, f in enumerate(frames):
            key = (f["stage"], round(f["real_s"], 2))
            right = cache.get(key)
            if right is None:
                right = panel.draw(f)
                cache.clear()
                cache[key] = right
            im = Image.new("RGB", (W, H), "white")
            im.paste(put_speed(cad(i), speed_label(f), 48), (0, 0))
            im.paste(right, (SQ, 0))
            if i == 0:
                im.save(out / "procedure_still_start.png")
            if i == len(frames) - 1:
                im.save(out / "procedure_still_end.png")
            yield im

    def plain_square():
        for i, f in enumerate(frames):
            yield put_speed(cad(i), speed_label(f), 48)

    def plain_wide():
        for im in plain_square():
            w = Image.new("RGB", (W, H), "white")
            w.paste(im, ((W - SQ) // 2, 0))
            yield w

    if args.only in (None, "annotated"):
        encode(annotated(), (W, H), out / "procedure_annotated.mp4")
        gif_from_mp4(out / "procedure_annotated.mp4", out / "procedure_annotated.gif", 1280)
        print("  annotated done")
    if args.only in (None, "plain"):
        encode(plain_wide(), (W, H), out / "procedure_plain.mp4")
        encode(plain_square(), (SQ, SQ), out / "procedure_plain_square.mp4")
        gif_from_mp4(out / "procedure_plain_square.mp4", out / "procedure_plain_square.gif", 720)
        print("  plain done")


if __name__ == "__main__":
    main()
