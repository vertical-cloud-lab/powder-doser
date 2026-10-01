"""Annotate the reference-view render the way the June figure was labelled.

Reads ``renders/assembly_iso_az090.png`` and the projected anchor points in
``renders/anchors_az090.json`` (both written by ``build.py``), draws the
powder stream and leader-line labels, and writes
``renders/assembly_iso_az090_annotated.png``.

The June figure also labelled "Vibration". There is no vibration motor on
the current rig (the driver never worked and the manuscript dropped it), so
that label is gone; pass ``--vibration`` to put it back on the tap collar.

    python3 annotate.py
    python3 annotate.py --src assembly_iso_az090_hires.png \
        --out assembly_iso_az090_hires_annotated.png      # print resolution
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
RENDERS = HERE / "renders"
FONT_CANDIDATES = (
    "/usr/share/fonts/truetype/crosextra/Carlito-Regular.ttf",   # Calibri metrics
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
)
LEADER = (128, 128, 128)
TEXT = (20, 20, 20)
BG = (247, 247, 250)   # the render's (transparent) background colour


def _font(size: int) -> ImageFont.FreeTypeFont:
    for f in FONT_CANDIDATES:
        if Path(f).exists():
            return ImageFont.truetype(f, size)
    return ImageFont.load_default()


def content_bbox(im: Image.Image) -> tuple[int, int, int, int]:
    alpha = np.asarray(im.convert("RGBA"))[:, :, 3]
    ys, xs = np.nonzero(alpha > 0)
    return xs.min(), ys.min(), xs.max(), ys.max()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--vibration", action="store_true",
                    help="also label 'Vibration' (June figure; no motor on the rig now)")
    ap.add_argument("--src", default="assembly_iso_az090.png")
    ap.add_argument("--out", default="assembly_iso_az090_annotated.png")
    args = ap.parse_args()

    im = Image.open(RENDERS / args.src).convert("RGBA")
    # anchors were projected at 1400 x 1000; the --hires render is 4x that
    k = im.width / 1400.0
    anchors = json.loads((RENDERS / "anchors_az090.json").read_text())
    x0, y0, x1, y1 = content_bbox(im)

    # canvas = the June crop proportions: labels above and to the right
    pad_l, pad_t, pad_r, pad_b = (round(v * k) for v in (20, 95, 215, 40))
    W = (x1 - x0) + pad_l + pad_r
    H = (y1 - y0) + pad_t + pad_b
    # transparent canvas, like the June figure (the render's background has
    # alpha 0)
    canvas = Image.new("RGBA", (W, H), BG + (0,))
    canvas.alpha_composite(im.crop((x0, y0, x1 + 1, y1 + 1)), (pad_l, pad_t))
    dx, dy = pad_l - x0, pad_t - y0

    def P(name):
        x, y = anchors[name]
        return (x * k + dx, y * k + dy)

    def off(xy, ox, oy):
        return (xy[0] + ox * k, xy[1] + oy * k)

    d = ImageDraw.Draw(canvas)
    font = _font(round(46 * k))

    # powder stream: dots, larger near the outlet
    stream = [(x * k + dx, y * k + dy) for x, y in anchors["stream"]]
    for i, (x, y) in enumerate(stream):
        r = (2.6 - 1.0 * i / len(stream)) * k
        d.ellipse((x - r, y - r, x + r, y + r), fill=(25, 25, 25, 255))
    stream_end = max(stream, key=lambda p: p[1])

    def label(text, xy_text, anchor_xy, start=None):
        tb = d.textbbox(xy_text, text, font=font)
        if start is None:   # leader leaves from the text edge nearest the anchor
            cx = min(max(anchor_xy[0], tb[0]), tb[2])
            cy = tb[3] + 6 * k if anchor_xy[1] > tb[3] else tb[1] - 6 * k
            if tb[1] <= anchor_xy[1] <= tb[3]:
                cy = (tb[1] + tb[3]) / 2
                cx = tb[0] - 8 * k if anchor_xy[0] < tb[0] else tb[2] + 8 * k
            start = (cx, cy)
        d.line([start, anchor_xy], fill=LEADER + (255,), width=max(1, round(3 * k)))
        d.text(xy_text, text, font=font, fill=TEXT + (255,))

    rot = P("Rotation")
    tap = P("Tapping")
    tilt = P("Tilt")
    label("Rotation", (rot[0] - 175 * k, 18 * k), off(rot, 4, -4))
    label("Tapping", (tap[0] + 30 * k, 18 * k), off(tap, 3, -3))
    tilt_txt = off(tilt, 95, -78)
    label("Tilt", tilt_txt, off(tilt, 18, 6), start=off(tilt_txt, -10, 30))
    ps_txt = off(stream_end, 75, -30)
    label("Powder stream", ps_txt, off(stream_end, 8, -4), start=off(ps_txt, -8, 22))
    if args.vibration:
        label("Vibration", (tap[0] + 120 * k, 85 * k), off(tap, -10, 55))

    canvas.save(RENDERS / args.out)
    print(f"  -> {(RENDERS / args.out).relative_to(HERE)}  ({W}x{H})")
    # flattened copy for viewing on GitHub (dark mode hides black-on-clear)
    white = Image.new("RGBA", canvas.size, (255, 255, 255, 255))
    white.alpha_composite(canvas)
    flat = RENDERS / args.out.replace(".png", "_white.png")
    white.convert("RGB").save(flat)
    print(f"  -> {flat.relative_to(HERE)}")


if __name__ == "__main__":
    main()
