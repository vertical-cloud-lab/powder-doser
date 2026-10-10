"""The real doser on the livestream next to this CAD (reference/as-built/).

* ``frames``: one frame per moment in ``FRAMES`` from the bench livestream
  (YouTube ``@byu-vcl-hardware-streams``, "powder doser stream picam-d1pr",
  8 h broadcasts).  Only the DASH init segment and the one fragment around
  each moment are fetched (about 0.3 MB each), rate-capped.  YouTube refuses
  datacenter IPs, so from CI pass ``--proxy`` on a residential connection,
  e.g. ``ssh -D 1080 <pi>`` behind ``pproxy -l http://127.0.0.1:8118 -r
  socks5://127.0.0.1:1080``.
* ``figures``: the dated timeline strip, and the Oct 9 frame next to the
  current assembly rendered from the camera's direction, numbered.
* ``onshape``: thumbnails of the lab's Onshape documents in ``ONSHAPE_DOCS``
  and one shaded view of the new baseplate's Part Studio (7 metered calls,
  see ../onshape/README.md).

    python3 scripts/as_built.py frames --proxy http://127.0.0.1:8118
    python3 scripts/as_built.py figures
    python3 scripts/as_built.py onshape
"""
from __future__ import annotations

import argparse
import base64
import json
import struct
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reference" / "as-built"
TMP = ROOT / "tmp" / "as_built"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

# name: (broadcast id, seconds into it, caption).  Each "<date> UTC 19:00"
# broadcast starts at 13:00 MDT, so 10800 s is 16:00 on the burned-in clock.
FRAMES = {
    "sep15": ("zQw_n-QoatM", 10800, ("Sep 15", "plank on a PVC stand")),
    "oct01": ("zscvKh7fNQ4", 10800, ("Oct 1", "fume hood, white board")),
    "oct02": ("VADmn4CjoBQ", 15200, ("Oct 2, 17:14", "new stand going in")),
    "oct04": ("ZWnj2jIUnhM", 10800, ("Oct 3-5", "camera at the wall")),
    "oct05": ("iSMf4j8W4e0", 6600, ("Oct 5, 14:51", "on the bench, CB 154")),
    "oct09": ("lkpjVhCktPA", 10800, ("Oct 9", "new stand")),
}

# Camera roughly where the livestream's is: in front of the outlet (-Y),
# above, looking back along the auger.
CAD_CAMERA = '{"position": [0, -400, 300], "target": [0, 60, 20], "up": [0, 0, 1]}'
# Numbered markers, (x, y) in the 720 x 1280 frame / 1080 x 1280 render.
LIVE_CROP, CAD_CROP = (0, 100, 720, 1000), (40, 170, 1040, 1100)
LIVE_MARKS = {1: [(238, 668), (505, 668)], 2: [(333, 240)], 3: [(118, 545), (612, 545)],
              5: [(398, 323)], 6: [(422, 196)], 7: [(96, 868)], 8: [(478, 268)]}
CAD_MARKS = {1: [(200, 800), (880, 800)], 4: [(110, 1010)], 6: [(540, 282)], 8: [(955, 610)]}

# Lab Onshape documents (Vertical Cloud Lab company): id, workspace, label.
ONSHAPE_DOCS = [
    ("5fc80753dffbfac5a3c30e5c", "d80d497892347f4d7f77097c", "Baseplate"),
    ("c6615a33e0a79dd2d62e03c5", "7c78d31ef0dd1cf3407da973", "mounting_plate (2).step"),
    ("3cfb5a3df7e248205be3a795", "eda154a8876394789e5b52c5", "Doser Centering Device"),
    ("dbe25c92dd19b12edac1581f", "52445ffc48dc8eb88d74b3b0", "PCB Housing"),
]
BASEPLATE_PARTS = ("5fc80753dffbfac5a3c30e5c", "d80d497892347f4d7f77097c",
                   "e65b66d40f5ee502b1c40ba0")  # Part Studio "Baseplate parts"


# --- frames ----------------------------------------------------------------------------

def _opener(proxy):
    handlers = [urllib.request.ProxyHandler({"http": proxy, "https": proxy})] if proxy else []
    return urllib.request.build_opener(*handlers)


def _fetch(op, url, a, b, budget):
    for k in range(5):
        try:
            req = urllib.request.Request(url, headers={"Range": f"bytes={a}-{b}"})
            with op.open(req, timeout=60) as r:
                data = r.read()
            break
        except OSError:
            if k == 4:
                raise
            time.sleep(2 * (k + 1))
    budget["bytes"] += len(data)
    time.sleep(max(0.0, budget["bytes"] / budget["rate"] - (time.time() - budget["t0"])))
    return data


def grab(vid: str, t: float, dest: Path, proxy: str | None, rate: float) -> None:
    """Save the frame at ``t`` s into broadcast ``vid`` (720p DASH, format 136)."""
    args = ["yt-dlp", "--no-warnings", "-f", "136", "-g", f"https://youtu.be/{vid}"]
    if proxy:
        args[1:1] = ["--proxy", proxy]
    url = subprocess.run(args, capture_output=True, text=True, check=True).stdout.split()[0]
    op, budget = _opener(proxy), {"bytes": 0, "rate": rate, "t0": time.time()}
    head = _fetch(op, url, 0, 150_000, budget)
    off = init_end = 0
    while off + 8 <= len(head):
        size, typ = struct.unpack(">I4s", head[off:off + 8])
        if typ == b"moov":
            init_end = off + size
        if typ == b"sidx":
            break
        off += size
    if off + size > len(head):
        head += _fetch(op, url, len(head), off + size - 1, budget)
    b = head[off:off + size]
    p = 12
    timescale = struct.unpack(">I", b[p + 4:p + 8])[0]
    p += 8
    if b[8] == 0:
        ept, first = struct.unpack(">II", b[p:p + 8]); p += 8
    else:
        ept, first = struct.unpack(">QQ", b[p:p + 16]); p += 16
    count = struct.unpack(">H", b[p + 2:p + 4])[0]
    p += 4
    pos, t0, frag = off + size + first, ept / timescale, None
    for _ in range(count):
        rs, dur, _ = struct.unpack(">III", b[p:p + 12]); p += 12
        if t0 <= t < t0 + dur / timescale:
            frag = (pos, rs & 0x7FFFFFFF, t0)
            break
        pos += rs & 0x7FFFFFFF
        t0 += dur / timescale
    data = _fetch(op, url, frag[0], frag[0] + frag[1] - 1, budget)
    clip = dest.with_suffix(".mp4")
    clip.write_bytes(head[:init_end] + data)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t - frag[2]:.2f}", "-i", str(clip),
                    "-frames:v", "1", "-q:v", "2", str(dest)], check=True)
    clip.unlink()


def frames(proxy: str | None, rate: float) -> None:
    TMP.mkdir(parents=True, exist_ok=True)
    for name, (vid, t, _) in FRAMES.items():
        grab(vid, t, TMP / f"{name}.jpg", proxy, rate)
        print(f"{name}: https://youtu.be/{vid}?t={t}")


# --- figures ---------------------------------------------------------------------------

def timeline(w: int = 230, crop_top: int = 60) -> None:
    """The six moments side by side, burned-in clock cropped off, dated."""
    fb, fr = ImageFont.truetype(FONT_B, 17), ImageFont.truetype(FONT, 15)
    hh = int(w * (1280 - crop_top) / 720)
    img = Image.new("RGB", (len(FRAMES) * (w + 8) - 8, hh + 50), "white")
    d = ImageDraw.Draw(img)
    for k, (name, (_, _, (date, what))) in enumerate(FRAMES.items()):
        im = Image.open(TMP / f"{name}.jpg").convert("RGB").crop((0, crop_top, 720, 1280))
        x = k * (w + 8)
        img.paste(im.resize((w, hh), Image.LANCZOS), (x, 0))
        d.text((x + 4, hh + 6), date, fill="black", font=fb)
        d.text((x + 4, hh + 27), what, fill=(60, 60, 60), font=fr)
    img.save(OUT / "timeline.jpg", quality=88)


def compare(h: int = 900, top: int = 44) -> None:
    """Oct 9 frame next to the current assembly from the camera's direction."""
    render = TMP / "assembly_current_camera.png"
    subprocess.run(["cadgen", "step", "snapshot", "STEP/assembly_current.step", str(render),
                    "--camera", CAD_CAMERA, "--width", "1080", "--height", "1280"],
                   check=True, cwd=ROOT)
    panels = []
    for src, box, marks in ((TMP / "oct09.jpg", LIVE_CROP, LIVE_MARKS),
                            (render, CAD_CROP, CAD_MARKS)):
        im = Image.open(src).convert("RGB").crop(box)
        s = h / im.height
        panels.append((im.resize((int(im.width * s), h), Image.LANCZOS), box, s, marks))
    img = Image.new("RGB", (panels[0][0].width + panels[1][0].width + 16, h + top), "white")
    d = ImageDraw.Draw(img)
    fb = ImageFont.truetype(FONT_B, 22)
    x0 = 0
    for (im, box, s, marks), title in zip(panels, ("livestream, Oct 9 16:01",
                                                   "this PR's CAD (PR #170 layout), same direction")):
        img.paste(im, (x0, top))
        d.text((x0 + 8, 10), title, fill="black", font=fb)
        for n, pts in marks.items():
            for x, y in pts:
                cx, cy, r = x0 + (x - box[0]) * s, top + (y - box[1]) * s, 17
                d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(230, 40, 40), outline="white", width=3)
                d.text((cx - d.textlength(str(n), font=fb) / 2, cy - 13), str(n), fill="white", font=fb)
        x0 += im.width + 16
    img.save(OUT / "livestream_vs_cad.jpg", quality=90)


# --- onshape ---------------------------------------------------------------------------

def onshape() -> None:
    sys.path.insert(0, str(ROOT / "onshape"))
    from onshape_client import Onshape

    api = Onshape(budget=len(ONSHAPE_DOCS) + 1, run="as-built")
    tiles = []
    for did, ws, label in ONSHAPE_DOCS:
        r = api.get(f"/thumbnails/d/{did}/w/{ws}/s/600x340", raw=True, headers={"Accept": "image/png"})
        png = TMP / f"onshape_{did[:8]}.png"
        png.write_bytes(r.content)
        tiles.append((label, Image.open(png).convert("RGB")))
    did, ws, eid = BASEPLATE_PARTS
    r = api.get(f"/partstudios/d/{did}/w/{ws}/e/{eid}/shadedviews?viewMatrix=isometric"
                "&outputHeight=800&outputWidth=1100&pixelSize=0&edges=show")
    (OUT / "onshape_baseplate_parts.png").write_bytes(base64.b64decode(r["images"][0]))
    w, hh = 600, 340
    img = Image.new("RGB", (2 * w, 2 * (hh + 28)), "white")
    d = ImageDraw.Draw(img)
    fb = ImageFont.truetype(FONT_B, 18)
    for k, (label, im) in enumerate(tiles):
        x, y = (k % 2) * w, (k // 2) * (hh + 28)
        img.paste(im, (x, y + 28))
        d.text((x + 6, y + 4), label, fill="black", font=fb)
    img.save(OUT / "onshape_thumbnails.png")
    print("Onshape calls:", api.calls)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["frames", "figures", "onshape"])
    ap.add_argument("--proxy", help="HTTP proxy for YouTube (needed from datacenter IPs)")
    ap.add_argument("--rate", type=float, default=300e3, help="download cap, bytes/s")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    TMP.mkdir(parents=True, exist_ok=True)
    if a.what == "frames":
        frames(a.proxy, a.rate)
    elif a.what == "figures":
        timeline()
        compare()
    else:
        onshape()


if __name__ == "__main__":
    main()
