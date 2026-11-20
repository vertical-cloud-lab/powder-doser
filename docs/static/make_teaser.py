#!/usr/bin/env python3
"""Teaser for the project page: loading Al 4047, then Claude dosing it from a phone (30 Sep 2026).

A re-cut of #174's slide video (`docs/videos/2026-09-30-al4047-claude-dose/make_slide_video.py`
on `claude/slide-video-al4047-20261004`, ed26df4) for the top of `docs/index.html`. It uses
the same three recordings of the PR #166 dose and the same sync, but the bench livestream
stays a full panel on the right the whole way through, so the dose itself is visible, and
the left panel switches from the camera on the bench to the phone's screen recording of
the PR thread: Claude's checklist, the @claude follow-up typed on the phone, Claude's plan
and its report.

    python make_teaser.py download   # windows of the three recordings into /tmp/teaser-src
    python make_teaser.py render     # videos/teaser_al4047_dose.mp4 and its poster frame
    python make_teaser.py contact    # /tmp/teaser-src/contact_sheet.jpg, every 1 s

YouTube refuses datacenter IPs, so from CI pass `--proxy socks5h://127.0.0.1:1080` with an
SSH SOCKS tunnel through a lab Pi (`ssh -D 1080 -N <pi>`). Only the fragments that cover
the edit's wall-clock windows are fetched (about 140 MB), rate-capped.
"""
import argparse
import json
import struct
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
SRC = Path("/tmp/teaser-src")
OUT = HERE / "videos" / "teaser_al4047_dose.mp4"
POSTER = HERE / "images" / "teaser_al4047_dose.jpg"
FPS = 30
W, H = 1920, 1080            # composed at the slide video's size, encoded at OUT_W wide
OUT_W = 1280
LEFT, GAP = 1080, 6          # left panel: 1080 x 1080 square
RIGHT = W - LEFT - GAP       # right panel (livestream): 834 x 1080
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def clock(s):
    """'HH:MM:SS[.s]' (MDT, 2026-09-30) -> seconds since midnight."""
    h, m, x = s.split(":")
    return int(h) * 3600 + int(m) * 60 + float(x)


# Wall clock (MDT) = t0 + t in each recording; offsets from #174's README "How the sync works".
SOURCES = {
    # fixed phone camera on the bench, 1080 x 1920; ends at 14:42:05
    "phone": dict(id="QXSj0j1OqL8", fmt="137", size=(1080, 1920), t0=clock("14:19:51.55")),
    # the phone's screen recording of the PR thread; 856 x 1920 (the 1080 x 2424 recording)
    "screen": dict(id="dXRB7c6GeDw", fmt="137", size=(856, 1920), t0=clock("14:59:01.57")),
    # bench livestream, 720 x 1280: the burned-in clock turns 14-30-00 at broadcast t = 5335.5 s
    # (t = 739.2 s of #174's window, which starts at broadcast t = 4596.3 s)
    "live": dict(id="yOK01jYPknA", fmt="136", size=(720, 1280), t0=clock("14:30:00") - 5335.5),
}

# Crops, as in #174. Phone camera: the 1080 square starts at row PHONE_Y0. Livestream: 696 x 900
# from just below the burned-in clock to below the balance, scaled to the right panel.
# Phone screen: an 856 x 856 square at row y0 (y1: pan to another row by the end of the beat);
# intro=<s> first shows the whole phone, pillarboxed, then zooms into the square over zoom_in s.
PHONE_Y0 = 440
LIVE_CROP = (696, 900, 12, 84)

# Edit decision list: wall-clock windows (MDT), each played at `speed` in both panels at once.
EDL = [
    # the cartridge, filled with Al 4047 at the back of the bench, is fitted to the doser
    dict(start="14:36:31", end="14:37:31", speed=15, left="phone"),
    # last checks at the balance; the cartridge is in place
    dict(start="14:40:36", end="14:42:04", speed=30, left="phone", fade_in=True),
    # Claude's checklist on the phone while the first pass doses: the tube at 40°, 2.2 -> 2.9 g
    dict(start="14:59:03", end="14:59:51", speed=8, left="screen", y0=390, intro=1.0,
         zoom_in=0.8, fade_in=True),
    # after a clog, the follow-up typed on the phone; the taps of the second pass. Slower while
    # "@claude" is typed in front of it and GitHub offers to complete the mention
    dict(start="15:29:52", end="15:30:35", speed=30, left="screen", y0=280, fade_in=True),
    dict(start="15:30:35", end="15:30:42", speed=5, left="screen", y0=280),
    dict(start="15:30:42", end="15:32:18", speed=30, left="screen", y0=280),
    # Claude's plan for a bulk-only top-up, which then runs: 0 -> 0.32 g at 40°
    dict(start="15:50:18", end="15:51:42", speed=14, left="screen", y0=300, fade_in=True),
    # Claude's report: the dose trace
    dict(start="15:57:10", end="15:57:40", speed=8, left="screen", y0=220, fade_in=True,
         fade_out=0.6),
]
XFADE = 8  # frames


# --- download -------------------------------------------------------------------------

def windows(key, pad=8.0):
    """Merged wall-clock windows of `key` that the EDL needs, padded, as recording times."""
    spans = []
    for seg in EDL:
        if key == "live" or seg["left"] == key:
            spans.append([clock(seg["start"]) - pad, clock(seg["end"]) + pad])
    spans.sort()
    merged = []
    for a, b in spans:
        if merged and a <= merged[-1][1] + 60:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])
    t0 = SOURCES[key]["t0"]
    return [(max(0.0, a - t0), b - t0) for a, b in merged]


def fetch_window(session, url, t0, t1, dest, rate):
    """Fetch the fragments of a single-file DASH format that cover [t0, t1] s (from #174).

    Reads the sidx index, then pulls 1 MiB ranges, capped at `rate` bytes/s. Returns the
    recording time of the first fragment, which is t = 0 of the written file.
    """
    def get(a, b):
        for k in range(5):
            try:
                r = session.get(url, headers={"Range": f"bytes={a}-{b}"}, timeout=60)
                r.raise_for_status()
                return r.content
            except Exception:
                if k == 4:
                    raise
                time.sleep(2 * (k + 1))

    head = get(0, 400_000)
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

    def chunk(span):
        data = get(*span)
        done[0] += len(data)
        time.sleep(max(0.0, done[0] / rate - (time.time() - start)))
        return data

    tmp = dest.with_suffix(".frag.mp4")
    with open(tmp, "wb") as f, ThreadPoolExecutor(4) as ex:
        f.write(head[:init_end])
        for data in ex.map(chunk, spans):
            f.write(data)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(tmp), "-c", "copy",
                    "-movflags", "+faststart", str(dest)], check=True)
    tmp.unlink()
    print(f"{dest.name}: t {sel[0][2]:.1f}-{t1:.1f} s, {(z - a + 1) / 1e6:.0f} MB", flush=True)
    return sel[0][2]


def download(proxy, rate):
    import requests
    SRC.mkdir(exist_ok=True)
    manifest = []
    session = requests.Session()
    if proxy:
        session.proxies = {"http": proxy, "https": proxy}
    for key, s in SOURCES.items():
        args = ["yt-dlp", "--no-warnings", "--js-runtimes", "node", "--remote-components",
                "ejs:github", "-f", s["fmt"], "-g", f"https://youtu.be/{s['id']}"]
        if proxy:
            args[1:1] = ["--proxy", proxy.replace("socks5h://", "socks5://")]
        url = subprocess.run(args, capture_output=True, text=True, check=True).stdout.split()[0]
        for i, (a, b) in enumerate(windows(key)):
            dest = SRC / f"{key}_{s['id']}_{int(a)}-{int(b)}.mp4"
            first = fetch_window(session, url, a, b, dest, rate)
            manifest.append(dict(key=key, file=dest.name, t_first=first, t_end=b))
    (SRC / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")


def locate(key, a, b):
    """The fetched file holding recording times [a, b] of `key`, and a's time in that file."""
    for m in json.loads((SRC / "manifest.json").read_text()):
        if m["key"] == key and m["t_first"] <= a and b <= m["t_end"] + 1:
            return SRC / m["file"], a - m["t_first"]
    raise SystemExit(f"{key} {a:.1f}-{b:.1f} s not downloaded; run `download`")


# --- render ---------------------------------------------------------------------------

def reader(key, wall0, wall1, n, vf, w, h):
    """Yield n RGB frames (h, w, 3) of `key` from wall clock wall0 to wall1."""
    t0 = SOURCES[key]["t0"]
    path, t = locate(key, wall0 - t0, wall1 - t0)
    dur = wall1 - wall0
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
    img = img.crop(img.getbbox())
    return np.asarray(img).astype(np.float32) / 255.0


def overlay(canvas, patch, alpha=1.0):
    """Blend the label into the bottom-right corner."""
    if patch is None or alpha <= 0:
        return canvas
    ph, pw = patch.shape[:2]
    y0, x0 = H - ph - 34, W - pw - 26
    region = canvas[y0:y0 + ph, x0:x0 + pw].astype(np.float32)
    a = patch[..., 3:4] * alpha
    canvas[y0:y0 + ph, x0:x0 + pw] = (region * (1 - a) + patch[..., :3] * 255 * a).astype(np.uint8)
    return canvas


def compose(seg, i, n, lf, rf):
    """One output frame for segment `seg` at frame i of n, from the left/right source frames."""
    canvas = np.zeros((H, W, 3), np.uint8)
    if seg["left"] == "phone":
        canvas[:, :LEFT] = lf[PHONE_Y0:PHONE_Y0 + 1080]
    else:
        sw, sh = SOURCES["screen"]["size"]
        y0 = seg.get("y0", 0)
        y = y0 + (seg.get("y1", y0) - y0) * ease(i / max(n - 1, 1))
        intro, z = seg.get("intro", 0) * FPS, seg.get("zoom_in", 0) * FPS
        a = ease((i - intro) / z) if z else 1.0     # 0: the whole phone, 1: the square
        ch = sh + (sw - sh) * a
        crop = Image.fromarray(lf).crop((0, int(round(y * a)), sw, int(round(y * a + ch))))
        dw = min(LEFT, int(round(sw * H / ch)))
        panel = Image.new("RGB", (LEFT, H))
        panel.paste(crop.resize((dw, H), Image.LANCZOS), ((LEFT - dw) // 2, 0))
        canvas[:, :LEFT] = np.asarray(panel)
    canvas[:, LEFT + GAP:] = rf
    return canvas


def render(crf=29):
    font = ImageFont.truetype(FONT, 34)
    enc = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
         "-r", str(FPS), "-i", "-", "-vf", f"scale={OUT_W}:-2:flags=lanczos", "-c:v", "libx264",
         "-preset", "slow", "-crf", str(crf), "-pix_fmt", "yuv420p", "-movflags", "+faststart",
         "-an", str(OUT)], stdin=subprocess.PIPE)
    prev, first, timeline, t_out = None, None, [], 0.0
    for seg in EDL:
        w0, w1 = clock(seg["start"]), clock(seg["end"])
        n = int(round((w1 - w0) / seg["speed"] * FPS))
        right = reader("live", w0, w1, n,
                       "crop={}:{}:{}:{},scale={}:{}:flags=lanczos".format(*LIVE_CROP, RIGHT, H),
                       RIGHT, H)
        key = seg["left"]
        left = reader(key, w0, w1, n, "", *SOURCES[key]["size"])
        tag = label(seg["speed"], font)
        timeline.append(dict(seg, out_start=round(t_out, 2), out_end=round(t_out + n / FPS, 2)))
        for i, (lf, rf) in enumerate(zip(left, right)):
            canvas = compose(seg, i, n, lf, rf)
            canvas = overlay(canvas, tag, min(1.0, (i + 1) / 6, (n - i) / 6))
            if seg.get("fade_in") and prev is not None and i < XFADE:
                a = ease((i + 1) / (XFADE + 1))
                canvas = (prev.astype(np.float32) * (1 - a) + canvas * a).astype(np.uint8)
            fo = seg.get("fade_out")
            if fo and i >= n - fo * FPS:
                canvas = (canvas.astype(np.float32) * ease((n - i) / (fo * FPS))).astype(np.uint8)
            enc.stdin.write(canvas.tobytes())
            if first is None:
                first = canvas
            last = canvas
        prev = last
        t_out += n / FPS
    enc.stdin.close()
    enc.wait()
    Image.fromarray(first).resize((OUT_W, OUT_W * H // W), Image.LANCZOS).save(
        POSTER, quality=82, optimize=True, progressive=True)
    (SRC / "edl.json").write_text(json.dumps(timeline, indent=1) + "\n")
    print(f"wrote {OUT.name}: {t_out:.1f} s, {OUT.stat().st_size / 1e6:.2f} MB")


def contact(every=1.0, cols=6, width=480):
    """Grid of frames every `every` seconds of the rendered teaser, tagged with their time."""
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                "-of", "csv=p=0", str(OUT)], capture_output=True, text=True).stdout)
    ts = np.arange(every / 2, dur, every)
    h = int(width * H / W)
    font = ImageFont.truetype(FONT.replace("-Bold", ""), 18)
    rows = (len(ts) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * width, rows * h), "white")
    for i, t in enumerate(ts):
        raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", str(OUT),
                              "-frames:v", "1", "-vf", f"scale={width}:{h}", "-f", "rawvideo",
                              "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
        im = Image.frombytes("RGB", (width, h), raw)
        d = ImageDraw.Draw(im)
        d.rectangle((0, 0, 62, 24), fill=(0, 0, 0))
        d.text((5, 2), f"{t:4.1f}s", font=font, fill="white")
        sheet.paste(im, ((i % cols) * width, (i // cols) * h))
    sheet.save(SRC / "contact_sheet.jpg", quality=88)
    print(f"wrote {SRC / 'contact_sheet.jpg'}: {len(ts)} frames")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", choices=["download", "render", "contact"])
    ap.add_argument("--proxy", help="proxy for YouTube, e.g. socks5h://127.0.0.1:1080")
    ap.add_argument("--rate", type=float, default=2e6, help="download cap, bytes/s")
    ap.add_argument("--crf", type=int, default=29)
    a = ap.parse_args()
    if a.cmd == "download":
        download(a.proxy, a.rate)
    elif a.cmd == "render":
        render(a.crf)
    else:
        contact()
