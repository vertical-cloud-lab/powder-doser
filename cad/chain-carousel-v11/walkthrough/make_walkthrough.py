"""Build the narrated v11 walkthrough video from the repo's own clips and stills.

Narration is synthesised offline with Piper (the public-domain LJ Speech voice), so no text leaves the runner. Every chapter's
pictures come from this repo (renders/, renders/v11/, sim/out/, ../../print/): each is fitted to its narration's length, with a
chapter bar on top and the narration as a caption at the bottom. Outputs, next to this file:

    walkthrough_v11.mp4     1280 x 720, 30 fps, H.264 + AAC
    walkthrough_v11.srt     the narration as captions (for YouTube's caption upload)
    chapters.txt            YouTube chapter timestamps for the description

    python make_walkthrough.py --voice /tmp/piper/en_US-ljspeech-high.onnx
"""
from __future__ import annotations

import argparse
import json
import math
import re
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

import imageio.v2 as imageio
import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
V11 = HERE.parent
W, H, FPS = 1280, 720, 30
BAR_H, CAP_H = 46, 92
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FF = imageio_ffmpeg.get_ffmpeg_exe()

sys.path.insert(0, str(HERE))
from script_v11 import CHAPTERS, TITLE  # noqa: E402


def font(sz, bold=False):
    return ImageFont.truetype(FONT_B if bold else FONT, sz)


def tts(text: str, voice: str, out: Path, length_scale: float = 1.0) -> float:
    """Piper (offline) -> wav; returns seconds."""
    p = subprocess.run([sys.executable, "-m", "piper", "-m", voice, "-f", str(out), "--length-scale", str(length_scale),
                        "--sentence-silence", "0.25"], input=text.encode(), capture_output=True)
    if p.returncode != 0:
        raise RuntimeError(p.stderr.decode()[-500:])
    with wave.open(str(out)) as w:
        return w.getnframes() / w.getframerate()


def read_wav(p: Path) -> tuple[np.ndarray, int]:
    with wave.open(str(p)) as w:
        sr = w.getframerate()
        a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    return a, sr


def fit(img: Image.Image, box_w: int, box_h: int, bg=(255, 255, 255)) -> Image.Image:
    """Letterbox an image into box_w x box_h."""
    img = img.convert("RGB")
    s = min(box_w / img.width, box_h / img.height)
    im2 = img.resize((max(1, int(img.width * s)), max(1, int(img.height * s))), Image.LANCZOS)
    out = Image.new("RGB", (box_w, box_h), bg)
    out.paste(im2, ((box_w - im2.width) // 2, (box_h - im2.height) // 2))
    return out


class Source:
    """A still (held) or a clip (mp4/gif, played at its own rate, then held on its last frame or looped)."""

    def __init__(self, path: Path, start: float = 0.0, end: float | None = None, loop: bool = False, speed: float = 1.0, crop_bottom: int = 0):
        self.path = Path(path)
        self.crop_bottom = crop_bottom
        self.still = self.path.suffix.lower() in (".png", ".jpg", ".jpeg")
        self.frames = []
        if self.still:
            self.frames = [Image.open(self.path).convert("RGB")]
            self.fps = FPS
        else:
            r = imageio.get_reader(str(self.path))
            meta = r.get_meta_data()
            fps = meta.get("fps") or (1000.0 / meta["duration"] if meta.get("duration") else 10.0)
            self.fps = fps * speed
            for i, fr in enumerate(r):
                t = i / fps
                if t < start:
                    continue
                if end is not None and t > end:
                    break
                arr = np.asarray(fr)[..., :3]
                if crop_bottom:
                    arr = arr[: arr.shape[0] - crop_bottom]          # drop the clip's own caption box (the narration's caption replaces it)
                self.frames.append(Image.fromarray(arr))
            r.close()
        self.loop = loop

    def duration(self) -> float:
        return 3.0 if self.still else len(self.frames) / self.fps

    def frame(self, t: float) -> Image.Image:
        if self.still:
            return self.frames[0]
        i = int(t * self.fps)
        if self.loop:
            i %= len(self.frames)
        return self.frames[min(i, len(self.frames) - 1)]


def wrap(text: str, f, width: int) -> list[str]:
    words, lines, cur = text.split(), [], ""
    for w_ in words:
        t = (cur + " " + w_).strip()
        if f.getlength(t) <= width:
            cur = t
        else:
            lines.append(cur)
            cur = w_
    if cur:
        lines.append(cur)
    return lines


def sentences(text: str) -> list[str]:
    s = re.split(r"(?<=[.!?])\s+", text.strip())
    return [x for x in s if x]


def card(title: str, lines: list[str], out: Path) -> Path:
    """A text card (white, a title and bullet lines) for chapters without a single picture."""
    img = Image.new("RGB", (W, H - BAR_H - CAP_H), (255, 255, 255))
    d = ImageDraw.Draw(img)
    d.text((60, 36), title, font=font(34, True), fill=(28, 46, 92))
    y = 104
    f = font(25)
    for ln in lines:
        for k, w_ in enumerate(wrap(ln, f, W - 170)):
            d.text((90 if k else 66, y), ("" if k else "\u2022  ") + w_, font=f, fill=(25, 25, 25))
            y += 36
        y += 12
    img.save(out)
    return out


def _source(v: dict, tmp: Path, k: int) -> "Source":
    if "card" in v:
        p = card(v["card"]["title"], v["card"]["lines"], tmp / f"card_{k}_{abs(hash(v['card']['title'])) % 10**8}.png")
        return Source(p)
    path = V11 / v["path"] if not str(v["path"]).startswith("/") else Path(v["path"])
    crop = v.get("crop_bottom", 100 if "renders/v11/" in str(v["path"]) and str(v["path"]).endswith(".mp4") and "mesh_" not in str(v["path"]) else 0)
    return Source(path, v.get("start", 0.0), v.get("end"), v.get("loop", False), v.get("speed", 1.0), crop)


def chapter_frames(ch: dict, dur: float, idx: int, n: int, tmp: Path = Path(tempfile.gettempdir())):
    """Yield (PIL frame) for one chapter of length dur."""
    srcs = [_source(v, tmp, k) for k, v in enumerate(ch["visuals"])]
    # share the chapter's time among its sources: clips get their own length (or a share), stills share what is left
    weights = [s.get("weight", 1.0) for s in ch["visuals"]]
    clip_d = [src.duration() for src in srcs]
    tot_w = sum(weights)
    spans = [dur * w / tot_w for w in weights]
    bounds = np.cumsum([0.0] + spans)
    sents = sentences(ch["text"])
    lens = np.array([len(s) for s in sents], float)
    sb = np.cumsum(np.r_[0.0, lens / lens.sum() * dur])
    fb, fc = font(24, True), font(23)
    nfr = int(round(dur * FPS))
    for k in range(nfr):
        t = k / FPS
        j = int(np.searchsorted(bounds, t, side="right") - 1)
        j = min(max(j, 0), len(srcs) - 1)
        tl = t - bounds[j]
        src = srcs[j]
        if not src.still and not src.loop and clip_d[j] > spans[j] * 1.02:
            tl = tl * clip_d[j] / spans[j]          # a clip longer than its share plays faster to fit
        img = fit(src.frame(tl), W, H - BAR_H - CAP_H)
        frame = Image.new("RGB", (W, H), (255, 255, 255))
        frame.paste(img, (0, BAR_H))
        d = ImageDraw.Draw(frame)
        d.rectangle([0, 0, W, BAR_H], fill=(28, 46, 92))
        d.text((16, 9), f"{idx}/{n}  {ch['title']}", font=fb, fill=(255, 255, 255))
        d.text((W - 16, 12), TITLE, font=font(18), fill=(200, 210, 235), anchor="ra")
        si = int(np.searchsorted(sb, t, side="right") - 1)
        si = min(max(si, 0), len(sents) - 1)
        d.rectangle([0, H - CAP_H, W, H], fill=(245, 245, 242))
        lines = wrap(sents[si], fc, W - 60)[:3]
        y0 = H - CAP_H + (CAP_H - 30 * len(lines)) // 2
        for i, ln in enumerate(lines):
            d.text((W // 2, y0 + 30 * i), ln, font=fc, fill=(20, 20, 20), anchor="ma")
        yield frame


def srt_time(t: float) -> str:
    h, r = divmod(t, 3600)
    m, s = divmod(r, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int(round((s - int(s)) * 1000)):03d}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--voice", default="/tmp/piper/en_US-ljspeech-high.onnx")
    ap.add_argument("--out", default=str(HERE / "walkthrough_v11.mp4"))
    ap.add_argument("--only", type=int, default=None, help="render one chapter (1-based) for checking")
    ap.add_argument("--crf", type=int, default=27)
    a = ap.parse_args()
    tmp = Path(tempfile.mkdtemp(prefix="wt11_"))
    chs = CHAPTERS if a.only is None else [CHAPTERS[a.only - 1]]
    n = len(CHAPTERS)
    # 1. narration
    durs, wavs = [], []
    for i, ch in enumerate(chs):
        wp = tmp / f"ch{i:02d}.wav"
        d = tts(ch["text"], a.voice, wp, ch.get("pace", 1.0))
        wavs.append(wp)
        durs.append(d + ch.get("pad", 0.9))
        print(f"chapter {i + 1}: {d:5.1f} s narration", flush=True)
    # 2. pictures
    silent = tmp / "video.mp4"
    wr = imageio.get_writer(str(silent), fps=FPS, codec="libx264", quality=None, ffmpeg_params=["-crf", str(a.crf), "-preset", "medium", "-pix_fmt", "yuv420p"],
                            macro_block_size=8)
    for i, (ch, d) in enumerate(zip(chs, durs)):
        num = (a.only or 0) if a.only else i + 1
        for fr in chapter_frames(ch, d, num, n, tmp):
            wr.append_data(np.asarray(fr))
        print(f"chapter {i + 1} pictures done", flush=True)
    wr.close()
    # 3. sound: each chapter's narration, padded to its length, at 22.05 kHz
    parts = []
    sr0 = None
    for wp, d in zip(wavs, durs):
        x, sr = read_wav(wp)
        sr0 = sr0 or sr
        y = np.zeros(int(round(d * sr)), np.float32)
        y[int(0.3 * sr):int(0.3 * sr) + len(x)] = x[: max(0, len(y) - int(0.3 * sr))]
        parts.append(y)
    audio = np.concatenate(parts)
    ap_ = tmp / "audio.wav"
    with wave.open(str(ap_), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr0)
        w.writeframes((np.clip(audio, -1, 1) * 32767).astype(np.int16).tobytes())
    subprocess.run([FF, "-y", "-loglevel", "error", "-i", str(silent), "-i", str(ap_), "-c:v", "copy", "-c:a", "aac", "-b:a", "96k",
                    "-shortest", "-movflags", "+faststart", a.out], check=True)
    # 4. chapters and captions
    if a.only is None:
        t = 0.0
        chap_lines, srt, k = [], [], 1
        for ch, d in zip(chs, durs):
            chap_lines.append(f"{int(t // 60)}:{int(t % 60):02d} {ch['title']}")
            sents = sentences(ch["text"])
            lens = np.array([len(s) for s in sents], float)
            sb = np.cumsum(np.r_[0.0, lens / lens.sum() * (d - 0.9)]) + t + 0.3
            for s, t0, t1 in zip(sents, sb[:-1], sb[1:]):
                srt.append(f"{k}\n{srt_time(t0)} --> {srt_time(t1)}\n{s}\n")
                k += 1
            t += d
        (HERE / "chapters.txt").write_text("\n".join(chap_lines) + "\n")
        head = (HERE / "description_head.txt").read_text() if (HERE / "description_head.txt").exists() else ""
        (HERE / "description.txt").write_text(head + "\n".join(chap_lines) + "\n")
        (HERE / "walkthrough_v11.srt").write_text("\n".join(srt))
        print(f"total {t / 60:.1f} min", flush=True)
    print("wrote", a.out)


if __name__ == "__main__":
    main()
