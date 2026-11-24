#!/usr/bin/env python3
"""Make the README's GIF of Claude dosing Al 4047, from the project page's teaser.

The project page (``docs/index.html``) opens with a 29 s teaser video,
``docs/static/videos/teaser_al4047_dose.mp4``, which ``docs/static/make_teaser.py``
cuts from the recordings of the 30 Sep 2026 Al 4047 dose (#166, #174).  GitHub
doesn't play a video stored in the repository inside a README, so the README
shows this GIF of it instead.

The GIF keeps the teaser from 7.2 s, once the phone's screen recording of the
#166 thread has faded in, to the end (28.7 s): Claude's checklist while the
first pass runs, the follow-up to Claude typed on the phone after a clog,
Claude's plan for a top-up and its report, beside the fixed camera over the
balance.  The teaser's first 7.2 s, the auger being fitted, would double the
file, so the README links to the page for them.

Every other frame of the teaser is kept (15 fps), 720 px wide.  Frames are
not blended, since blending doubles the text while it scrolls or is typed.  To
keep the file small, a pixel is redrawn only when it changes by more than
HOLD; otherwise the cameras' noise changes every pixel of every frame and the
GIF has to store each frame whole (twice the size here).

    python3 scripts/readme_teaser_gif.py [OUT.gif]

Needs ffmpeg, gifsicle and numpy.  The output is the same byte for byte on
every run.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
TEASER = REPO / "docs/static/videos/teaser_al4047_dose.mp4"  # 1280 x 720, 30 fps, 28.7 s
OUT = REPO / "docs/readme/gifs/al4047_claude_dose.gif"

START = 7.2     # s into the teaser: the screen recording's cross-fade is over
FPS = 15        # every other frame of the teaser
WIDTH = 720
HEIGHT = 405    # 16:9, like the teaser
HOLD = 12       # a pixel is redrawn only when it changes by more than this (0-255)
COLORS = 192
LOSSY = 60


def frames():
    """The teaser from START, at FPS and WIDTH, as RGB arrays."""
    cmd = ["ffmpeg", "-v", "error", "-ss", f"{START}", "-i", str(TEASER),
           "-vf", f"fps={FPS},scale={WIDTH}:{HEIGHT}:flags=lanczos",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    with subprocess.Popen(cmd, stdout=subprocess.PIPE) as proc:
        size = WIDTH * HEIGHT * 3
        while len(buf := proc.stdout.read(size)) == size:
            yield np.frombuffer(buf, np.uint8).reshape(HEIGHT, WIDTH, 3)


def held(frames):
    """Keep a pixel from the previous frame unless it changed by more than HOLD.

    The change is box-blurred (3 x 3) before the test, and the redrawn area is
    grown by a pixel so that the edges of moving things don't fringe.
    """
    h, w = HEIGHT, WIDTH
    ref = None
    for frame in frames:
        f = frame.astype(np.int16)
        if ref is None:
            ref = f.copy()
        else:
            d = np.pad(np.abs(f - ref).max(axis=2), 1, mode="edge").astype(np.float32)
            d = sum(d[i:i + h, j:j + w] for i in range(3) for j in range(3)) / 9
            m = np.pad(d > HOLD, 1)
            m = np.logical_or.reduce([m[i:i + h, j:j + w] for i in range(3) for j in range(3)])
            ref[m] = f[m]
        yield ref.astype(np.uint8)


def main() -> None:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    with tempfile.TemporaryDirectory() as tmp:
        lossless, palette, raw = Path(tmp) / "held.mkv", Path(tmp) / "palette.png", Path(tmp) / "raw.gif"
        enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                                "-s", f"{WIDTH}x{HEIGHT}", "-r", str(FPS), "-i", "-",
                                "-c:v", "ffv1", str(lossless)], stdin=subprocess.PIPE)
        n = 0
        for frame in held(frames()):
            enc.stdin.write(frame.tobytes())
            n += 1
        enc.stdin.close()
        if enc.wait():
            sys.exit("ffmpeg failed to write the held frames")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(lossless), "-vf",
                        f"palettegen=max_colors={COLORS}:stats_mode=full", str(palette)], check=True)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(lossless), "-i", str(palette), "-lavfi",
                        "paletteuse=dither=none:diff_mode=rectangle", str(raw)], check=True)
        out.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["gifsicle", "-O3", f"--lossy={LOSSY}", "--no-comments", "--no-extensions",
                        "--loopcount=forever", str(raw), "-o", str(out)], check=True)
    print(f"{out}  {n} frames, {n / FPS:.1f} s, {out.stat().st_size / 1e6:.2f} MB")


if __name__ == "__main__":
    main()
