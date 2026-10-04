#!/usr/bin/env python3
"""Slide video: loading Al 4047, then Claude dosing it while the bench livestream runs.

Three recordings of the 2026-09-30 Al 4047 (9fxeqt) dose (PR #166), time-synced and cut
into one 16:9 clip for a full-screen PowerPoint slide:

- left, square: the fixed phone camera on the bench (QXSj0j1OqL8, loading the powder),
  then the phone's screen recording of the PR thread (dXRB7c6GeDw) once the dose starts
- right: the bench livestream (yOK01jYPknA, picam-d1pr), always at the same wall-clock
  moment as the left panel

The only overlay is the speed multiplier in the bottom-right corner.

    python make_slide_video.py download [--proxy URL]   # sources into ./sources (gitignored)
    python make_slide_video.py render                   # al4047_claude_dose_slide.mp4
    python make_slide_video.py contact                  # contact_sheet.jpg

YouTube refuses datacenter IPs ("Sign in to confirm you're not a bot"); from CI, pass a
proxy on a residential connection (e.g. `ssh -D 1080 <pi>` plus an HTTP front such as
`pproxy -l http://127.0.0.1:8118 -r socks5://127.0.0.1:1080`).
"""
import argparse
import json
import struct
import subprocess
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
SRC = HERE / "sources"
OUT = HERE / "al4047_claude_dose_slide.mp4"
FPS = 30
W, H = 1920, 1080
LEFT = 1080            # left panel: 1080 x 1080 square
GAP = 6
RIGHT = W - LEFT - GAP  # right panel: 834 x 1080
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def clock(s):
    """'HH:MM:SS[.s]' (MDT, 2026-09-30) -> seconds since midnight."""
    h, m, x = s.split(":")
    return int(h) * 3600 + int(m) * 60 + float(x)


# Wall clock (MDT) of each source's t = 0, i.e. wall = T0 + t. See README "How the sync works".
SOURCES = {
    "phone": dict(id="QXSj0j1OqL8", fmt="137", file="phone_QXSj0j1OqL8.mp4",
                  # motion cross-correlation against the livestream (single peak, 0.25 s steps)
                  t0=clock("14:19:51.55")),
    "screen": dict(id="dXRB7c6GeDw", fmt="271", file="screen_dXRB7c6GeDw.webm",
                   # status-bar clock turns 2:59 -> 3:00 at t = 58.43 s
                   t0=clock("14:59:01.57")),
    "live": dict(id="yOK01jYPknA", fmt="136", file="live_yOK01jYPknA_4596-11050.mp4",
                 # 720p DASH fragments from broadcast t = 4596.3 s; the burned-in clock turns
                 # 14-30-00 at t = 739.2 s of this file
                 t0=clock("14:30:00") - 739.2, window=(4600, 11050)),
}

# Crops: phone (1080x1920) square at y0; screen (1080x2424) square at y0; livestream (720x1280)
# 696 x 900 from just below the burned-in clock (rows 0-78) to below the balance, scaled to
# the 834 x 1080 right panel.
PHONE_Y0 = 440
LIVE_CROP = (696, 900, 12, 84)

# Edit decision list. Wall-clock windows (MDT) play at `speed` in both panels at once.
EDL = [
    # Loading: the whole bench for 2 s (portrait, pillarboxed), then into the square
    dict(start="14:25:21", end="14:25:41", speed=10, left="phone-full"),
    dict(start="14:25:41", end="14:36:31", speed=100, left="phone", zoom_in=0.6),
    #   cartridge filled at the back of the bench, then fitted to the doser
    dict(start="14:36:31", end="14:37:31", speed=12, left="phone"),
    dict(start="14:40:36", end="14:42:04", speed=20, left="phone", fade_in=True),
    # Claude's first dose: the PR checklist on the phone, powder pouring on the stream
    dict(start="14:59:03", end="14:59:43", speed=8, left="screen", y0=260, fade_in=True),
    # watching (and scrubbing) the livestream on the phone
    dict(start="15:00:58", end="15:01:18", speed=4, left="screen", y0=270, fade_in=True),
    # after the clog: typing the plain-language follow-up to @claude
    dict(start="15:29:52", end="15:32:18", speed=30, left="screen", y0=380, fade_in=True),
    # Claude's bulk-only top-up to 8 g
    dict(start="15:50:18", end="15:51:42", speed=10, left="screen", y0=800, fade_in=True),
    # Claude's report with the dose trace
    dict(start="15:57:10", end="15:58:22", speed=12, left="screen", y0=300, fade_in=True,
         fade_out=0.8),
]
XFADE = 8  # frames


def reader(path, t, dur, n, vf, w, h):
    """Yield n RGB frames (h, w, 3) from path, starting at t, played at dur/n*FPS speed."""
    speed = dur * FPS / n
    cmd = ["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-t", f"{dur + 2:.3f}", "-i", str(path),
           "-vf", f"setpts=(PTS-STARTPTS)/{speed:.6f},fps={FPS}" + (f",{vf}" if vf else ""),
           "-frames:v", str(n), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    size = w * h * 3
    last = None
    for _ in range(n):
        buf = p.stdout.read(size)
        if len(buf) == size:
            last = np.frombuffer(buf, np.uint8).reshape(h, w, 3)
        yield last
    p.stdout.close()
    p.wait()


def ease(a):
    a = min(max(a, 0.0), 1.0)
    return a * a * (3 - 2 * a)


def phone_panel(frame, a):
    """Phone frame (1920x1080) in the 1080 square: a=0 whole frame pillarboxed, a=1 square crop."""
    sh = 1920 + (1080 - 1920) * a
    sy = PHONE_Y0 * a
    crop = Image.fromarray(frame).crop((0, int(round(sy)), 1080, int(round(sy + sh))))
    dw = int(round(1080 * 1080 / sh))
    panel = Image.new("RGB", (LEFT, H))
    panel.paste(crop.resize((dw, H), Image.LANCZOS), ((LEFT - dw) // 2, 0))
    return np.asarray(panel)


def label(speed, font):
    """Speed multiplier as an RGBA patch, or None at 1x."""
    if speed <= 1:
        return None
    text = f"×{speed:g}"
    img = Image.new("RGBA", (220, 70), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    box = d.textbbox((0, 0), text, font=font)
    x, y = 220 - (box[2] - box[0]) - 6, 70 - (box[3] - box[1]) - 12
    d.text((x + 2, y + 2), text, font=font, fill=(0, 0, 0, 110))
    d.text((x, y), text, font=font, fill=(255, 255, 255, 200))
    return np.asarray(img).astype(np.float32) / 255.0


def overlay(canvas, patch, alpha=1.0):
    if patch is None or alpha <= 0:
        return canvas
    ph, pw = patch.shape[:2]
    y0, x0 = H - ph - 22, W - pw - 26
    region = canvas[y0:y0 + ph, x0:x0 + pw].astype(np.float32)
    a = patch[..., 3:4] * alpha
    canvas[y0:y0 + ph, x0:x0 + pw] = (region * (1 - a) + patch[..., :3] * 255 * a).astype(np.uint8)
    return canvas


def render(out=OUT, crf=20):
    font = ImageFont.truetype(FONT, 34)
    enc = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
         "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", str(crf),
         "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(out)], stdin=subprocess.PIPE)
    lv = SOURCES["live"]
    prev = None
    timeline = []
    t_out = 0.0
    for seg in EDL:
        w0, w1 = clock(seg["start"]), clock(seg["end"])
        n = int(round((w1 - w0) / seg["speed"] * FPS))
        right = reader(SRC / lv["file"], w0 - lv["t0"], w1 - w0, n,
                       "crop={}:{}:{}:{},scale={}:{}:flags=lanczos".format(*LIVE_CROP, RIGHT, H),
                       RIGHT, H)
        if seg["left"].startswith("phone"):
            ph = SOURCES["phone"]
            left = reader(SRC / ph["file"], w0 - ph["t0"], w1 - w0, n, "", 1080, 1920)
        else:
            sc = SOURCES["screen"]
            left = reader(SRC / sc["file"], w0 - sc["t0"], w1 - w0, n,
                          f"crop=1080:1080:0:{seg['y0']}", LEFT, H)
        tag = label(seg["speed"], font)
        timeline.append(dict(seg, out_start=round(t_out, 2), out_end=round(t_out + n / FPS, 2)))
        for i, (lf, rf) in enumerate(zip(left, right)):
            canvas = np.zeros((H, W, 3), np.uint8)
            if seg["left"] == "phone-full":
                lp = phone_panel(lf, 0.0)
            elif seg["left"] == "phone":
                z = seg.get("zoom_in")
                lp = phone_panel(lf, ease(i / (z * FPS)) if z else 1.0)
            else:
                lp = lf
            canvas[:, :LEFT] = lp
            canvas[:, LEFT + GAP:] = rf
            fade_tag = min(1.0, (i + 1) / 6, (n - i) / 6)
            canvas = overlay(canvas, tag, fade_tag)
            if seg.get("fade_in") and prev is not None and i < XFADE:
                a = ease((i + 1) / (XFADE + 1))
                canvas = (prev.astype(np.float32) * (1 - a) + canvas * a).astype(np.uint8)
            fo = seg.get("fade_out")
            if fo and i >= n - fo * FPS:
                k = (n - i) / (fo * FPS)
                canvas = (canvas.astype(np.float32) * ease(k)).astype(np.uint8)
            enc.stdin.write(canvas.tobytes())
            last = canvas
        prev = last
        t_out += n / FPS
    enc.stdin.close()
    enc.wait()
    (HERE / "edl.json").write_text(json.dumps(timeline, indent=1) + "\n")
    print(f"wrote {out.name}: {t_out:.1f} s")


def contact(video=OUT, every=2.0, cols=6, width=480):
    """Grid of frames every `every` seconds, each tagged with its output time."""
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                "-of", "csv=p=0", str(video)], capture_output=True, text=True).stdout)
    ts = np.arange(every / 2, dur, every)
    h = int(width * H / W)
    font = ImageFont.truetype(FONT.replace("-Bold", ""), 18)
    rows = (len(ts) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * width, rows * h), "white")
    for i, t in enumerate(ts):
        raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", str(video),
                              "-frames:v", "1", "-vf", f"scale={width}:{h}", "-f", "rawvideo",
                              "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
        im = Image.frombytes("RGB", (width, h), raw)
        d = ImageDraw.Draw(im)
        d.rectangle((0, 0, 62, 24), fill=(0, 0, 0))
        d.text((5, 2), f"{t:4.1f}s", font=font, fill="white")
        sheet.paste(im, ((i % cols) * width, (i // cols) * h))
    sheet.save(HERE / "contact_sheet.jpg", quality=88)
    print(f"wrote contact_sheet.jpg: {len(ts)} frames")


# --- download -------------------------------------------------------------------------

def _fetch(opener, url, a, b):
    req = urllib.request.Request(url, headers={"Range": f"bytes={a}-{b}"})
    with opener.open(req, timeout=60) as r:
        return r.read()


def dash_window(vid, fmt, t0, t1, dest, proxy, rate=3e6):
    """Fetch only the fragments of a single-file DASH format that cover [t0, t1] s.

    Reads the sidx index, then pulls 1 MiB ranges (YouTube throttles long single ranges),
    capped at `rate` bytes/s overall. Writes init + fragments as a fragmented MP4.
    """
    args = ["yt-dlp", "--no-warnings", "-f", fmt, "-g", f"https://youtu.be/{vid}"]
    if proxy:
        args[1:1] = ["--proxy", proxy]
    url = subprocess.run(args, capture_output=True, text=True, check=True).stdout.split()[0]
    handlers = [urllib.request.ProxyHandler({"http": proxy, "https": proxy})] if proxy else []
    opener = urllib.request.build_opener(*handlers)
    head = _fetch(opener, url, 0, 400_000)
    off, init_end = 0, None
    while off + 8 <= len(head):
        size, typ = struct.unpack(">I4s", head[off:off + 8])
        if typ == b"moov":
            init_end = off + size
        if typ == b"sidx":
            break
        off += size
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
    pos, t, sel = off + size + first, ept / timescale, []
    for _ in range(count):
        rs, dur, _ = struct.unpack(">III", b[p:p + 12]); p += 12
        if t + dur / timescale >= t0 and t <= t1:
            sel.append((pos, rs & 0x7FFFFFFF, t))
        pos += rs & 0x7FFFFFFF
        t += dur / timescale
    a, z = sel[0][0], sel[-1][0] + sel[-1][1] - 1
    spans = [(s, min(s + (1 << 20) - 1, z)) for s in range(a, z + 1, 1 << 20)]
    start, done = time.time(), [0]

    def get(span):
        for k in range(5):
            try:
                data = _fetch(opener, url, *span)
                break
            except OSError:
                time.sleep(2 * (k + 1))
        done[0] += len(data)
        time.sleep(max(0.0, done[0] / rate - (time.time() - start)))
        return data

    tmp = dest.with_suffix(".frag.mp4")
    with open(tmp, "wb") as f, ThreadPoolExecutor(4) as ex:
        f.write(head[:init_end])
        for data in ex.map(get, spans):
            f.write(data)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(tmp), "-c", "copy",
                    "-movflags", "+faststart", str(dest)], check=True)
    tmp.unlink()
    print(f"{dest.name}: broadcast t {sel[0][2]:.1f}-{t1} s, {(z - a + 1) / 1e6:.0f} MB")


def download(proxy=None, rate="2M"):
    SRC.mkdir(exist_ok=True)
    for key in ("phone", "screen"):
        s = SOURCES[key]
        args = ["yt-dlp", "--no-warnings", "-r", rate, "-f", s["fmt"], "-o", str(SRC / s["file"]),
                f"https://youtu.be/{s['id']}"]
        if proxy:
            args[1:1] = ["--proxy", proxy]
        subprocess.run(args, check=True)
    lv = SOURCES["live"]
    dash_window(lv["id"], lv["fmt"], *lv["window"], SRC / lv["file"], proxy)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", choices=["download", "render", "contact"])
    ap.add_argument("--proxy", help="HTTP proxy for YouTube (needed from datacenter IPs)")
    ap.add_argument("--crf", type=int, default=20)
    a = ap.parse_args()
    if a.cmd == "download":
        download(a.proxy)
    elif a.cmd == "render":
        render(crf=a.crf)
    else:
        contact()
    sys.exit(0)
