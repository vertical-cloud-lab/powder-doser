#!/usr/bin/env python3
"""Slide video: loading Al 4047, then Claude dosing it while the bench livestream runs.

Three recordings of the 2026-09-30 Al 4047 (9fxeqt) dose (PR #166), time-synced and cut
into one 16:9 clip for a full-screen PowerPoint slide:

- loading: the fixed phone camera on the bench (QXSj0j1OqL8) in a 1080 square on the left,
  the bench livestream (yOK01jYPknA, picam-d1pr) on the right, same wall-clock moment
- dosing: the phone's screen recording of the PR thread (dXRB7c6GeDw). The whole phone is
  shown once, then the view zooms to a 16:9 crop of it that fills the frame so the text is
  readable; the livestream continues as a small picture-in-picture

The only overlay is the speed multiplier in a bottom corner.

    python make_slide_video.py download [--proxy URL]   # sources into ./sources (gitignored)
    python make_slide_video.py render                   # al4047_claude_dose_slide.mp4 + edl.json
    python make_slide_video.py storyboard               # storyboard.jpg (one frame per beat)
    python make_slide_video.py contact                  # contact_sheet.jpg (every 2 s)
    python make_slide_video.py upload                   # unlisted YouTube upload, prints the URL

YouTube refuses datacenter IPs ("Sign in to confirm you're not a bot"); from CI, pass a
proxy on a residential connection (e.g. `ssh -D 1080 <pi>` plus an HTTP front such as
`pproxy -l http://127.0.0.1:8118 -r socks5://127.0.0.1:1080`).

Uploading needs a YouTube Data API OAuth token in `YOUTUBE_OAUTH_TOKEN_JSON` (the
"authorized user" JSON with client_id, client_secret and refresh_token). Make one on a
laptop with `python make_slide_video.py auth client_secret.json` and store its output as a
repository secret; see README "Uploading to YouTube".
"""
import argparse
import json
import os
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
LEFT = 1080            # loading layout, left panel: 1080 x 1080 square
GAP = 6
RIGHT = W - LEFT - GAP  # loading layout, right panel: 834 x 1080
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

# Crops. Phone camera (1080x1920): the 1080 square starts at row PHONE_Y0. Livestream
# (720x1280): 696 x 900 from just below the burned-in clock (rows 0-78) to below the
# balance, scaled to the 834 x 1080 right panel. Phone screen (1080x2424): a 16:9 crop
# 1080 x 607.5 at row y0, scaled to the whole 1920 x 1080 frame (1.78x), see screen_frame().
PHONE_Y0 = 440
LIVE_CROP = (696, 900, 12, 84)
SCREEN_W, SCREEN_H = 1080, 2424
LAND_H = 607.5                              # 1080 x 607.5 is exactly 16:9
PIP_H = 300                                 # livestream picture-in-picture height
PIP_W = int(round(PIP_H * LIVE_CROP[0] / LIVE_CROP[1]))
PIP_MARGIN, PIP_BORDER = 24, 3

# Edit decision list. Wall-clock windows (MDT) play at `speed` in both sources at once.
#   left="phone-full" / "phone": loading layout (phone camera square + livestream panel);
#     zoom_in=<s> animates whole frame -> square over the first <s> seconds.
#   left="screen": the phone's screen recording fills the frame as a 16:9 crop at row y0
#     (panning to y1 if given). intro=<s> first shows the whole phone, pillarboxed, for
#     <s> seconds and then zooms into the crop over zoom_in seconds; whole=True keeps the
#     whole phone for the entire segment. pip="br"/"bl"/"tr"/"tl"/None places the
#     livestream picture-in-picture.
#   fade_in: 8-frame crossfade from the previous segment. fade_out=<s>: fade to black.
EDL = [
    # Loading: the whole bench for 2 s (portrait, pillarboxed), then into the square
    dict(start="14:25:21", end="14:25:41", speed=10, left="phone-full"),
    dict(start="14:25:41", end="14:36:31", speed=100, left="phone", zoom_in=0.6),
    #   cartridge filled at the back of the bench, then fitted to the doser
    dict(start="14:36:31", end="14:37:31", speed=12, left="phone"),
    dict(start="14:40:36", end="14:42:04", speed=20, left="phone", fade_in=True),
    # Claude's first dose: the whole phone once, then into the PR checklist; powder pours
    dict(start="14:59:03", end="14:59:43", speed=8, left="screen", y0=500, intro=1.4,
         zoom_in=1.0, fade_in=True),
    # watching (and scrubbing) the livestream on the phone: the whole phone, no zoom
    dict(start="15:00:58", end="15:01:18", speed=4, left="screen", whole=True, fade_in=True),
    # after the clog: typing the plain-language follow-up to @claude
    dict(start="15:29:52", end="15:32:18", speed=30, left="screen", y0=420, fade_in=True),
    # Claude's plan for the bulk-only top-up to 8 g
    dict(start="15:50:18", end="15:51:42", speed=10, left="screen", y0=520, fade_in=True),
    # Claude's report: the dose trace
    dict(start="15:57:10", end="15:57:40", speed=5, left="screen", y0=380, fade_in=True,
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


def screen_frame(frame, a, y0):
    """Phone screen (1080x2424) on the whole 1920x1080 canvas.

    a=0: the whole phone, pillarboxed (481 px wide). a=1: the 1080 x 607.5 crop at row y0,
    scaled 1.78x to fill the frame. In between, the crop shrinks towards y0 (eased by the
    caller) and is always fitted to the frame height.
    """
    sh = SCREEN_H + (LAND_H - SCREEN_H) * a
    sy = y0 * a
    crop = Image.fromarray(frame).crop((0, int(round(sy)), SCREEN_W, int(round(sy + sh))))
    dw = min(W, int(round(SCREEN_W * H / sh)))
    canvas = Image.new("RGB", (W, H))
    canvas.paste(crop.resize((dw, H), Image.LANCZOS), ((W - dw) // 2, 0))
    return np.array(canvas)


def pip(canvas, live, corner):
    """Paste the livestream panel as a bordered picture-in-picture in the given corner."""
    if not corner:
        return canvas
    im = Image.fromarray(live).resize((PIP_W, PIP_H), Image.LANCZOS)
    b = PIP_BORDER
    x = PIP_MARGIN if corner[1] == "l" else W - PIP_W - 2 * b - PIP_MARGIN
    y = PIP_MARGIN if corner[0] == "t" else H - PIP_H - 2 * b - PIP_MARGIN
    canvas[y:y + PIP_H + 2 * b, x:x + PIP_W + 2 * b] = 235
    canvas[y + b:y + b + PIP_H, x + b:x + b + PIP_W] = np.asarray(im)
    return canvas


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


def overlay(canvas, patch, alpha=1.0, right=True):
    """Blend the label into the bottom-right (or bottom-left) corner."""
    if patch is None or alpha <= 0:
        return canvas
    ph, pw = patch.shape[:2]
    y0, x0 = H - ph - 34, W - pw - 26 if right else 26
    region = canvas[y0:y0 + ph, x0:x0 + pw].astype(np.float32)
    a = patch[..., 3:4] * alpha
    canvas[y0:y0 + ph, x0:x0 + pw] = (region * (1 - a) + patch[..., :3] * 255 * a).astype(np.uint8)
    return canvas


def compose(seg, i, n, lf, rf):
    """One output frame for segment `seg` at frame i of n, from the left/right source frames."""
    canvas = np.zeros((H, W, 3), np.uint8)
    if seg["left"] == "phone-full":
        canvas[:, :LEFT] = phone_panel(lf, 0.0)
        canvas[:, LEFT + GAP:] = rf
    elif seg["left"] == "phone":
        z = seg.get("zoom_in")
        canvas[:, :LEFT] = phone_panel(lf, ease(i / (z * FPS)) if z else 1.0)
        canvas[:, LEFT + GAP:] = rf
    else:
        intro = seg.get("intro", 0) * FPS
        z = seg.get("zoom_in", 0) * FPS
        a = 0.0 if seg.get("whole") else ease((i - intro) / z) if z else 1.0
        y0 = seg.get("y0", 0)
        y = y0 + (seg.get("y1", y0) - y0) * i / max(n - 1, 1)
        canvas = screen_frame(lf, a, y)
        canvas = pip(canvas, rf, seg.get("pip", "br"))
    return canvas


def render(out=OUT, crf=20, only=None):
    font = ImageFont.truetype(FONT, 34)
    enc = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
         "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", str(crf),
         "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(out)], stdin=subprocess.PIPE)
    lv = SOURCES["live"]
    prev = None
    timeline = []
    t_out = 0.0
    for k, seg in enumerate(EDL):
        if only is not None and k not in only:
            continue
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
            left = reader(SRC / sc["file"], w0 - sc["t0"], w1 - w0, n, "", SCREEN_W, SCREEN_H)
        tag = label(seg["speed"], font)
        tag_right = not (seg["left"] == "screen" and seg.get("pip", "br") == "br")
        timeline.append(dict(seg, out_start=round(t_out, 2), out_end=round(t_out + n / FPS, 2)))
        for i, (lf, rf) in enumerate(zip(left, right)):
            canvas = compose(seg, i, n, lf, rf)
            fade_tag = min(1.0, (i + 1) / 6, (n - i) / 6)
            canvas = overlay(canvas, tag, fade_tag, tag_right)
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
    if only is None:
        (HERE / "edl.json").write_text(json.dumps(timeline, indent=1) + "\n")
    print(f"wrote {out.name}: {t_out:.1f} s")


def _grab(video, t, width, height):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", str(video),
                          "-frames:v", "1", "-vf", f"scale={width}:{height}", "-f", "rawvideo",
                          "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    return Image.frombytes("RGB", (width, height), raw)


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
        im = _grab(video, t, width, h)
        d = ImageDraw.Draw(im)
        d.rectangle((0, 0, 62, 24), fill=(0, 0, 0))
        d.text((5, 2), f"{t:4.1f}s", font=font, fill="white")
        sheet.paste(im, ((i % cols) * width, (i // cols) * h))
    sheet.save(HERE / "contact_sheet.jpg", quality=88)
    print(f"wrote contact_sheet.jpg: {len(ts)} frames")


def storyboard(video=OUT, cols=3, width=640, at=0.55):
    """One frame per EDL segment (at fraction `at` of it), labelled with out time and wall clock."""
    edl = json.loads((HERE / "edl.json").read_text())
    h = int(width * H / W)
    font = ImageFont.truetype(FONT.replace("-Bold", ""), 20)
    rows = (len(edl) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * width, rows * (h + 30)), "white")
    for i, seg in enumerate(edl):
        t = seg["out_start"] + at * (seg["out_end"] - seg["out_start"])
        im = _grab(video, t, width, h)
        x, y = (i % cols) * width, (i // cols) * (h + 30)
        sheet.paste(im, (x, y))
        ImageDraw.Draw(sheet).text(
            (x + 6, y + h + 5), f"{seg['out_start']:.1f}-{seg['out_end']:.1f} s   "
            f"{seg['start']}-{seg['end']} MDT   ×{seg['speed']}", font=font, fill="black")
    sheet.save(HERE / "storyboard.jpg", quality=88)
    print(f"wrote storyboard.jpg: {len(edl)} frames")


# --- YouTube upload -------------------------------------------------------------------

TITLE = "Loading Al 4047, then Claude dosing it with the livestream (powder doser, 2026-09-30)"
DESCRIPTION = """\
Al 4047 (9fxeqt) powder is loaded into the powder doser, then Claude doses 8 g of it from
a GitHub PR thread while the bench livestream runs. About 1.5 h of wall clock in 47 s; the
multiplier in the corner is the playback speed. Made for a 16:9 slide.

Left/top: fixed phone camera on the bench, then the phone's screen recording of the PR
thread. Right/inset: the picam-d1pr livestream at the same wall-clock moment.

How it was made, beat table and sources:
https://github.com/vertical-cloud-lab/powder-doser/tree/main/docs/videos/2026-09-30-al4047-claude-dose
The dose itself: https://github.com/vertical-cloud-lab/powder-doser/pull/166

Sources: https://youtu.be/QXSj0j1OqL8 (phone camera), https://youtu.be/dXRB7c6GeDw
(screen recording), https://youtu.be/yOK01jYPknA (livestream).
"""


def auth(client_secret):
    """Mint an authorized-user token on a laptop; prints JSON to store as YOUTUBE_OAUTH_TOKEN_JSON."""
    from google_auth_oauthlib.flow import InstalledAppFlow
    flow = InstalledAppFlow.from_client_secrets_file(
        client_secret, ["https://www.googleapis.com/auth/youtube.upload"])
    creds = flow.run_local_server(port=0)
    print(creds.to_json())


def upload(video=OUT, privacy="unlisted"):
    """Resumable upload of the rendered video; prints the YouTube URL."""
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    token = os.environ.get("YOUTUBE_OAUTH_TOKEN_JSON")
    if not token:
        sys.exit("YOUTUBE_OAUTH_TOKEN_JSON is not set; see README 'Uploading to YouTube'")
    creds = Credentials.from_authorized_user_info(
        json.loads(token), ["https://www.googleapis.com/auth/youtube.upload"])
    yt = build("youtube", "v3", credentials=creds)
    body = {"snippet": {"title": TITLE, "description": DESCRIPTION, "categoryId": "28"},
            "status": {"privacyStatus": privacy, "selfDeclaredMadeForKids": False}}
    req = yt.videos().insert(part="snippet,status", body=body,
                             media_body=MediaFileUpload(str(video), chunksize=8 << 20,
                                                        resumable=True))
    resp = None
    while resp is None:
        _, resp = req.next_chunk()
    print(f"https://youtu.be/{resp['id']}")


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
    ap.add_argument("cmd", choices=["download", "render", "storyboard", "contact", "upload", "auth"])
    ap.add_argument("arg", nargs="?", help="auth: path to the OAuth client_secret.json")
    ap.add_argument("--proxy", help="HTTP proxy for YouTube (needed from datacenter IPs)")
    ap.add_argument("--crf", type=int, default=20)
    ap.add_argument("--privacy", default="unlisted", choices=["unlisted", "private", "public"])
    a = ap.parse_args()
    if a.cmd == "download":
        download(a.proxy)
    elif a.cmd == "render":
        render(crf=a.crf)
    elif a.cmd == "storyboard":
        storyboard()
    elif a.cmd == "contact":
        contact()
    elif a.cmd == "upload":
        upload(privacy=a.privacy)
    else:
        auth(a.arg)
    sys.exit(0)
