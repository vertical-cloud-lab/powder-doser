#!/usr/bin/env python3
"""Make the README's livestream GIF of a 0.5 g salt dose (15 Sep 2026).

The dose is the issue #116 demo of 15 Sep 2026: 0.4963 g of table salt for a
0.5 g target in 100 s, run ``20260915T164228Z_salt-demo`` (the run note, the
raw serial log and the camera stills are at commit 2522858).  The bench camera
that streams the doser to YouTube filmed it: broadcast ``r6ZEN1O8B0Y``
("powder doser stream picam-d1pr, 2026-09-15 UTC 11:00"), 152 s from
t = 20468 s.

YouTube refuses the runner's datacenter address, so the clip was fetched with
yt-dlp on the runner through an SSH SOCKS tunnel to the doser's Pi (which only
relayed the traffic; nothing was installed or written on it):

    ssh -f -N -D 127.0.0.1:1080 "$RPI_POWDER_DOSER_USERNAME@$RPI_POWDER_DOSER_HOSTNAME"
    proxychains4 -q -f pc.conf yt-dlp --js-runtimes node -f 136 \\
        --download-sections "*20468-20620" --force-keyframes-at-cuts \\
        -o "salt0p5g_%(section_start)s.%(ext)s" https://www.youtube.com/watch?v=r6ZEN1O8B0Y

(``pc.conf`` lists ``socks5 127.0.0.1 1080`` under ``[ProxyList]``.)

Timing.  The camera burns its clock (MDT) into the frame; in this clip it
ticks from 10:42:13 to 10:42:14 at t = 0.700 s, so every time below is given
on that clock, in seconds after 10:42:00 MDT.  (A fresh download may start a
second or so differently: set CLOCK_AT_T0 from its first clock tick.)  The
run log's per-cycle times are whole seconds, so the events were placed from
the footage and checked against the log and the firmware
(``powder_battery.py`` and ``main_three_phase.py`` at 2522858):

* 31.9 s: the tube tips down as the run starts, and holds still while the
  balance is zeroed.  No dose phase moves the servos here; the move is fast
  and unramped, like the servo start-up write in ``Servo.__init__``.
* 39.8 s: the fine phase ramps the tube to 22.5 deg (0.75 s), then turns the
  auger 45 deg per cycle.  Each cycle waits for the move plus 2.2 s, settles
  for 1.5 s and weighs, so a weighing ends just before the next turn: one cycle
  every 5.31 s, the same pace as the log (cycles 3-16 logged at 24-93 s).
  Turns 2-16 show in the footage at those times; the first is hidden by the
  tilt just before it.
* 125.0 s: right after the 16th weighing, the tap phase ramps the tube to
  0 deg and taps twice per cycle (pairs at 125.8 and 129.0 s).
* 132.1 s: the second tap cycle's weighing ends the dose: 0.4963 g.

The bulk phase never ran: the dose started with 0.4998 g to go, already
under the bulk phase's 0.5 g hand-over threshold, so the controller went
straight to fine (the log's "phase 1/3 'bulk' skipped").  The cup already
held the salt from the feed check run just before the dose; the balance was
zeroed with it in place.

The balance display is out of this camera's frame, so the masses under the
video are the controller's log, each shown from the weighing that produced it.

    python3 scripts/livestream_clip_gif.py CLIP.mp4 [OUT.gif]

Needs ffmpeg, gifsicle and the Lato font (fonts-lato).
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
FONT_BOLD = "/usr/share/fonts/truetype/lato/Lato-Bold.ttf"
FONT = "/usr/share/fonts/truetype/lato/Lato-Regular.ttf"

CLOCK_AT_T0 = 13.3   # camera clock (s after 10:42:00 MDT) at clip t = 0
START, END = 30.0, 140.0  # camera clock window used
SPEED = 4
FPS = 4              # output frames per second (one per second of the dose)
WIDTH = 360
CROP_H = 1040        # px from the top of the 720 x 1280 frame: clock to cup
BAND = 92            # px of white band under the video for the labels

PHASES = [
    (START, 31.9, "Run starts"),
    (31.9, 39.8, "Tare: zeroing the balance"),
    (39.8, 125.0, "Fine: 22.5°, 1/8 turn at a time"),
    (125.0, 132.1, "Tap: 0°, two taps at a time"),
    (132.1, END, "Done: 0.4963 g in 100 s"),
]

# Mass in the cup after each weighing, from raw_serial_salt-demo.log
# (2522858): the post-tare reading, the 16 fine cycles, the 2 tap cycles.
FINE = [0.0248, 0.0281, 0.0494, 0.0391, 0.0855, 0.1155, 0.1273, 0.1987,
        0.2496, 0.2742, 0.3022, 0.3075, 0.3437, 0.3580, 0.4234, 0.4709]
TAP = [0.4690, 0.4963]
PERIOD = 5.31        # s per fine cycle
READINGS = ([(39.8, 0.0002)]
            + [(125.0 - PERIOD * (16 - k), g) for k, g in enumerate(FINE, 1)]
            + [(128.9, TAP[0]), (132.1, TAP[1])])
FOOTER = "×4   0.5 g of table salt, 15 Sep 2026 (#116)"


def esc(text: str) -> str:
    return text.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'").replace("%", "\\%")


def out_t(clock_s: float) -> float:
    """Output-GIF time of a moment on the camera clock."""
    return (clock_s - START) / SPEED


def label(text: str, y: int, size: int, color: str, font: str, a: float, b: float) -> str:
    return (f"drawtext=fontfile={font}:text='{esc(text)}':x=12:y={y}:fontsize={size}:"
            f"fontcolor={color}:enable='gte(t,{out_t(a):.3f})*lt(t,{out_t(b):.3f})'")


def main() -> None:
    clip = Path(sys.argv[1])
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else REPO / "docs/readme/gifs/livestream_salt_dose.gif"
    height = round(WIDTH * CROP_H / 720 / 2) * 2
    filters = [
        f"crop=720:{CROP_H}:0:0", "hqdn3d=4:4:12:12", f"setpts=PTS/{SPEED}", f"fps={FPS}",
        f"scale={WIDTH}:{height}:flags=lanczos", f"pad={WIDTH}:{height + BAND}:0:0:white",
    ]
    filters += [label(text, height + 10, 19, "0x222222", FONT_BOLD, a, b) for a, b, text in PHASES]
    ends = [t for t, _ in READINGS[1:]] + [END + 1]
    filters += [label(f"In the cup: {g:.4f} g of 0.5 g", height + 39, 17, "0x1a4f8b", FONT, t, nxt)
                for (t, g), nxt in zip(READINGS, ends)]
    filters.append(
        f"drawtext=fontfile={FONT}:text='{esc(FOOTER)}':x=12:y={height + 67}:fontsize=14:fontcolor=0x666666"
    )
    vf = ",".join(filters)
    with tempfile.TemporaryDirectory() as tmp:
        palette, raw = Path(tmp) / "palette.png", Path(tmp) / "raw.gif"
        common = ["ffmpeg", "-v", "error", "-y", "-ss", f"{START - CLOCK_AT_T0:.3f}",
                  "-t", f"{END - START:.3f}", "-i", str(clip)]
        subprocess.run(common + ["-vf", f"{vf},palettegen=max_colors=96:stats_mode=diff", str(palette)], check=True)
        subprocess.run(common + ["-i", str(palette), "-lavfi",
                                 f"{vf}[v];[v][1:v]paletteuse=dither=bayer:bayer_scale=5:diff_mode=rectangle",
                                 str(raw)], check=True)
        out.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["gifsicle", "-O3", "--lossy=70", str(raw), "-o", str(out)], check=True)
    print(f"{out}  {out.stat().st_size / 1e6:.2f} MB")


if __name__ == "__main__":
    main()
