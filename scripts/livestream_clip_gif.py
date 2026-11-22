#!/usr/bin/env python3
"""Make the README's livestream GIF of Al 4047 going into the aluminium cup.

The footage is the first pass of the 8 g Al 4047 (sample 9fxeqt) dose that
Claude ran for an atomizer charge on 30 Sep 2026 (PR #166, trial
``3e7490c2``; the run note, trial documents and raw serial logs are in
``data/opt/production-al4047-9fxeqt/`` on the PR #166 branch, commit
``964ec6c``).  The powder falls through a paper funnel into the aluminium cup
that stands in the glass beaker on the balance (Fig. 5c).  The bench camera
that streams the doser to YouTube filmed it: broadcast ``yOK01jYPknA``
("powder doser stream picam-d1pr, 2026-09-30 UTC 19:00"), 180 s from
t = 7020 s.  The balance display is in this camera's view, so the mass in the
GIF is the balance's own reading.

YouTube refuses the runner's datacenter address, so the clip was fetched with
yt-dlp on the runner through an SSH SOCKS tunnel to the doser's Pi (which only
relayed the traffic; nothing was installed or written on it).  Format 232 is
the stream's HLS copy (720 x 1280, 30 fps); ``--download-sections`` without
``--force-keyframes-at-cuts`` copies it without re-encoding:

    ssh -f -N -D 127.0.0.1:1080 "$RPI_POWDER_DOSER_USERNAME@$RPI_POWDER_DOSER_HOSTNAME"
    proxychains4 -q -f pc.conf yt-dlp --js-runtimes node -f 232 --limit-rate 2M \\
        --download-sections "*7020-7200" -o al_pass1_copy.%(ext)s \\
        https://www.youtube.com/watch?v=yOK01jYPknA

(``pc.conf`` lists ``socks5 127.0.0.1 1080`` under ``[ProxyList]``; the
challenge solver comes with ``pip install "yt-dlp[default]"``.)

Timing.  The camera burns its clock (MDT) into the frame; in this clip it
ticks at t = 0.5 s, 1.5 s, ... and reads 14:58:05 from t = 0.5 s, so every
time below is on that clock, in seconds after 14:58:00 MDT.  (A fresh download
may start a little differently: set CLOCK_AT_T0 from its first clock tick.)
The camera's clock runs about 15 s ahead of the Zero's, so the times are
placed from the footage and checked against the serial log:

* 32.5 s: ``g 8.0000`` (the log's elapsed 0 s); the balance is tared.
* 37.0-38.5 s: the tube tilts from 0 to 40 deg, the bulk tilt.
* 39 s: the first powder reaches the cup (log: 9.5 mg at elapsed 6 s).  The
  first 1.2 g arrives within 7 s (176 mg/s); then the feed slows steadily,
  from 73 mg/s over the next 7 s to 14 mg/s over the last 20 s.  The auger
  turns at 100 rpm, with one 60 ms solenoid tap every 500 ms.
* 132.5 s: the firmware's telemetry log ran out of memory at elapsed 100 s
  (``MemoryError``, fixed in ``fa59ef8``), which stopped the auger with
  3.4721 g in the cup by the controller's last poll.  The reading settles
  at 3.488-3.491 g.

The second pass and a bulk-only top-up later brought the cup to 8.0010 g.

Smoothness.  The 15 Sep salt clip this replaces kept 4 GIF frames per second
at 4x, one sharp frame per second of the dose, so every move was a jump.  This
one keeps 20 frames per second at 5x, and each GIF frame is the mean of the
7-8 camera frames it stands for, so the tilt and the auger blur instead of
jumping.  To keep the file small, a pixel is redrawn only when it changes by
more than HOLD; otherwise camera noise changes every pixel of every frame and
the GIF has to store each frame whole (about four times the size).

    python3 scripts/livestream_clip_gif.py CLIP.mp4 [OUT.gif]

Needs ffmpeg, gifsicle, numpy, Pillow and the Lato font (fonts-lato).
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

REPO = Path(__file__).resolve().parents[1]
FONT_BOLD = "/usr/share/fonts/truetype/lato/Lato-Bold.ttf"
FONT = "/usr/share/fonts/truetype/lato/Lato-Regular.ttf"

CLOCK_AT_T0 = 4.5          # camera clock (s after 14:58:00 MDT) at clip t = 0
START, END = 33.5, 141.0   # camera clock window used
DOSE_T0 = 32.5             # camera clock at the log's elapsed 0 s (the 'g' command)
SPEED = 5
FPS = 20                   # GIF frames per second (50 ms each)
BLEND = round(SPEED * 30 / FPS)  # camera frames averaged into each GIF frame
CROP = (480, 854, 120, 76)  # w, h, x, y in the 720 x 1280 frame: the doser down to the balance's keys
WIDTH = 360
BAND = 70                  # px of white band under the video for the labels
HOLD = 9                   # a pixel is redrawn only when it changes by more than this (0-255)
COLORS = 160
LOSSY = 40

PHASES = [
    (START, 37.0, "Taring the balance"),
    (37.0, 39.0, "Tilting the tube to 40°"),
    (39.0, 132.5, "Bulk: 100 rpm, a tap every 0.5 s"),
    (132.5, END + 1, "The auger stops: 3.49 g in 100 s"),
]
CAPTION = "Al 4047 into the aluminium cup, 30 Sep 2026 (#166)"


def video_frames(clip: Path, w: int, h: int):
    """Cropped frames, SPEED times faster, each the mean of the BLEND camera frames it stands for."""
    cw, ch, cx, cy = CROP
    vf = ",".join([f"crop={cw}:{ch}:{cx}:{cy}", f"setpts=PTS/{SPEED}", f"tmix=frames={BLEND}",
                   f"fps={FPS}", f"scale={w}:{h}:flags=lanczos"])
    cmd = ["ffmpeg", "-v", "error", "-ss", f"{START - CLOCK_AT_T0:.3f}", "-t", f"{END - START:.3f}",
           "-i", str(clip), "-vf", vf, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    with subprocess.Popen(cmd, stdout=subprocess.PIPE) as proc:
        size = w * h * 3
        while len(buf := proc.stdout.read(size)) == size:
            yield np.frombuffer(buf, np.uint8).reshape(h, w, 3)


def held(frames):
    """Keep a pixel from the previous frame unless it changed by more than HOLD.

    Camera noise otherwise changes every pixel of every frame, and the GIF has
    to store each frame whole.  The change is box-blurred (3 x 3) before the
    test, and the redrawn area is grown by a pixel so that edges don't fringe.
    """
    ref = None
    for frame in frames:
        f = frame.astype(np.int16)
        if ref is None:
            ref = f.copy()
        else:
            d = np.pad(np.abs(f - ref).max(axis=2), 1, mode="edge").astype(np.float32)
            d = sum(d[i:i + f.shape[0], j:j + f.shape[1]] for i in range(3) for j in range(3)) / 9
            m = np.pad(d > HOLD, 1)
            m = np.logical_or.reduce([m[i:i + f.shape[0], j:j + f.shape[1]] for i in range(3) for j in range(3)])
            ref[m] = f[m]
        yield ref.astype(np.uint8)


def band(t: float, w: int, fonts) -> np.ndarray:
    """The labels under the video at GIF time t."""
    clock = START + t * SPEED
    phase = next(text for a, b, text in PHASES if a <= clock < b)
    secs = int(clock - DOSE_T0)
    img = Image.new("RGB", (w, BAND), "white")
    draw = ImageDraw.Draw(img)
    draw.text((10, 7), phase, font=fonts[0], fill=(34, 34, 34))
    draw.text((10, 31), CAPTION, font=fonts[1], fill=(26, 79, 139))
    draw.text((10, 50), f"dose time {secs // 60}:{secs % 60:02d}    ×{SPEED} speed", font=fonts[2], fill=(102, 102, 102))
    return np.asarray(img)


def main() -> None:
    clip = Path(sys.argv[1])
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else REPO / "docs/readme/gifs/livestream_al4047_dose.gif"
    cw, ch, _, _ = CROP
    height = round(WIDTH * ch / cw / 2) * 2
    fonts = (ImageFont.truetype(FONT_BOLD, 17), ImageFont.truetype(FONT, 14), ImageFont.truetype(FONT, 13))
    with tempfile.TemporaryDirectory() as tmp:
        lossless, palette, raw = Path(tmp) / "held.mkv", Path(tmp) / "palette.png", Path(tmp) / "raw.gif"
        enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                                "-s", f"{WIDTH}x{height + BAND}", "-r", str(FPS), "-i", "-",
                                "-c:v", "ffv1", str(lossless)], stdin=subprocess.PIPE)
        for k, frame in enumerate(held(video_frames(clip, WIDTH, height))):
            enc.stdin.write(np.vstack([frame, band(k / FPS, WIDTH, fonts)]).tobytes())
        enc.stdin.close()
        enc.wait()
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(lossless), "-vf",
                        f"palettegen=max_colors={COLORS}:stats_mode=full", str(palette)], check=True)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(lossless), "-i", str(palette), "-lavfi",
                        "paletteuse=dither=bayer:bayer_scale=3:diff_mode=rectangle", str(raw)], check=True)
        out.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["gifsicle", "-O3", f"--lossy={LOSSY}", str(raw), "-o", str(out)], check=True)
    print(f"{out}  {out.stat().st_size / 1e6:.2f} MB")


if __name__ == "__main__":
    main()
