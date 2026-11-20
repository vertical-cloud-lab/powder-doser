#!/usr/bin/env python3
"""Make the README's livestream GIF of a three-phase 1 g salt dose.

The dose is the issue #148 demo of 3 Sep 2026 (1.0040 g for a 1 g target,
90 s; bulk, fine and tap phases), filmed by the bench camera that streams the
doser to YouTube: broadcast ``xjtJNMo8DKw``, 120 s from t = 15158 s.

YouTube refuses the runner's datacenter address, so the clip was fetched with
yt-dlp on the runner through an SSH SOCKS tunnel to the doser's Pi (which only
relayed the traffic; nothing was installed or written on it):

    ssh -f -N -D 127.0.0.1:1080 "$RPI_POWDER_DOSER_USERNAME@$RPI_POWDER_DOSER_HOSTNAME"
    proxychains4 -q -f pc.conf yt-dlp --js-runtimes node -f 136 \\
        --download-sections "*15158-15278" --force-keyframes-at-cuts \\
        -o "salt1g_%(section_start)s.%(ext)s" https://www.youtube.com/watch?v=xjtJNMo8DKw

(``pc.conf`` lists ``socks5 127.0.0.1 1080`` under ``[ProxyList]``.)  The camera
burns its clock (MDT) into the frame; clip t = 0 is 18:18:24 MDT, 00:18:24 UTC.
The phase times below are read off the balance display in the clip and agree
with the run log in #148 (bulk from 00:18:29 UTC, taps from 00:19:27, done at
00:19:54).

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

DURATION = 100  # s of the clip to use, from its start
SPEED = 4
FPS = 4         # output frames per second (one frame per second of the dose)
WIDTH = 320     # the stream is portrait, 720 x 1280
BAND = 84       # px of white band under the video for the labels

# (start, end) in clip seconds, as read off the balance display.  The settings
# are block G's (DOSE_PHASES in hardware/test-module/firmware/powder_battery.py
# on the #116 branches): bulk at 45 deg, turning continuously at 55 rpm, until
# 0.5 g is left; fine at 22.5 deg, 45-deg steps of the auger, until 50 mg is
# left; tap at 0 deg, two taps per cycle, until within 5 mg.
PHASES = [
    (0, 5, "Tare"),
    (5, 10, "1  Bulk: 45°, auger at 55 rpm"),
    (10, 63, "2  Fine: 22.5°, 1/8 turn at a time"),
    (63, 90, "3  Tap: 0°, two taps at a time"),
    (90, DURATION, "Done: 1.0040 g in 90 s"),
]
FOOTER = "×4   1 g of table salt, 3 Sep 2026 (#148)"


def esc(text: str) -> str:
    return text.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'").replace("%", "\\%")


def main() -> None:
    clip = Path(sys.argv[1])
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else REPO / "docs/readme/gifs/livestream_three_phase_dose.gif"
    height = round(WIDTH * 1280 / 720 / 2) * 2
    filters = [
        "hqdn3d=4:4:12:12", f"setpts=PTS/{SPEED}", f"fps={FPS}", f"scale={WIDTH}:{height}:flags=lanczos",
        f"pad={WIDTH}:{height + BAND}:0:0:white",
    ]
    for start, end, label in PHASES:
        a, b = start / SPEED, end / SPEED
        filters.append(
            f"drawtext=fontfile={FONT_BOLD}:text='{esc(label)}':x=12:y={height + 14}:"
            f"fontsize=20:fontcolor=0x222222:enable='gte(t,{a})*lt(t,{b})'"
        )
    filters.append(
        f"drawtext=fontfile={FONT}:text='{esc(FOOTER)}':x=12:y={height + 52}:fontsize=15:fontcolor=0x666666"
    )
    vf = ",".join(filters)
    with tempfile.TemporaryDirectory() as tmp:
        palette, raw = Path(tmp) / "palette.png", Path(tmp) / "raw.gif"
        common = ["ffmpeg", "-v", "error", "-y", "-t", str(DURATION), "-i", str(clip)]
        subprocess.run(common + ["-vf", f"{vf},palettegen=max_colors=96:stats_mode=diff", str(palette)], check=True)
        subprocess.run(common + ["-i", str(palette), "-lavfi",
                                 f"{vf}[v];[v][1:v]paletteuse=dither=bayer:bayer_scale=5:diff_mode=rectangle",
                                 str(raw)], check=True)
        out.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["gifsicle", "-O3", "--lossy=70", str(raw), "-o", str(out)], check=True)
    print(f"{out}  {out.stat().st_size / 1e6:.2f} MB")


if __name__ == "__main__":
    main()
