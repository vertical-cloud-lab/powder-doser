"""Contact sheets of every slide build, for review.

    python3 make_contact_sheet.py   # -> contact_sheet.png, contact_sheet_versions.png

``contact_sheet.png`` has one row per slide, in talk order, with every step
of its main version (the procedure video as six moments).
``contact_sheet_versions.png`` has the last step of every version.
"""
from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
TW, TH = 480, 270
GAP = 12
LABEL_H = 44
FONT = ImageFont.truetype("/usr/share/fonts/truetype/lato/Lato-Regular.ttf", 26)
BOLD = ImageFont.truetype("/usr/share/fonts/truetype/lato/Lato-Bold.ttf", 26)

ROWS = [   # (title, slide/version)
    ("1  How a dose runs (video)", "procedure"),
    ("2  The math: Pareto front and hypervolume", "front-math/example"),
    ("3  The math: model and next dose", "model-math/example"),
    ("4  Result: Pareto front", "pareto/linear"),
    ("5  Result: mass in the cup over time", "traces/pair"),
    ("6  Result: what changed", "knobs/dumbbell"),
]
VERSIONS = ["procedure", "front-math/example", "model-math/example", "pareto/linear",
            "pareto/model", "pareto/log", "traces/pair", "traces/all", "knobs/dumbbell"]
VIDEO_TIMES = [0.5, 3.5, 9.5, 14.0, 18.0, 21.0]


def video_frames(mp4: Path, times):
    out = []
    with tempfile.TemporaryDirectory() as tmp:
        for i, t in enumerate(times):
            p = Path(tmp) / f"{i}.png"
            subprocess.run([shutil.which("ffmpeg"), "-y", "-loglevel", "error", "-ss", f"{t}",
                            "-i", str(mp4), "-frames:v", "1", str(p)], check=True)
            out.append(Image.open(p).convert("RGB"))
    return out


def steps(rel: str):
    if rel == "procedure":
        return video_frames(HERE / "procedure/procedure_annotated.mp4", VIDEO_TIMES)
    d = HERE / rel
    files = sorted(d.glob("step_*.png"), key=lambda p: int(p.stem.split("_")[1]))
    return [Image.open(p).convert("RGB") for p in files]


def thumb(im):
    t = im.resize((TW, TH), Image.LANCZOS)
    d = ImageDraw.Draw(t)
    d.rectangle([0, 0, TW - 1, TH - 1], outline=(190, 190, 190))
    return t


def sheet(rows, out: Path, ncols=None):
    ncols = ncols or max(len(r[1]) for r in rows)
    W = GAP + ncols * (TW + GAP)
    H = GAP + len(rows) * (LABEL_H + TH + GAP)
    S = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(S)
    y = GAP
    for title, ims in rows:
        d.text((GAP, y + 6), title, font=BOLD, fill=(11, 11, 11))
        y += LABEL_H
        for j, im in enumerate(ims):
            S.paste(thumb(im), (GAP + j * (TW + GAP), y))
        y += TH + GAP
    S.save(out, optimize=True)
    print(f"  -> {out.name} ({W} x {H})")


def main():
    sheet([(t, steps(rel)) for t, rel in ROWS], HERE / "contact_sheet.png")
    finals = [steps(rel)[-1] for rel in VERSIONS]
    rows = [("Last step of every version: " + ", ".join(VERSIONS[:5]), finals[:5]),
            ("" + ", ".join(VERSIONS[5:]), finals[5:])]
    sheet(rows, HERE / "contact_sheet_versions.png", ncols=5)


if __name__ == "__main__":
    main()
