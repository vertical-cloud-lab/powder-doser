"""Comparison panels for the README / issue: the June figure next to the new
render, and the new outlet-end view next to the 11 Sep rig photo.

    python3 compare.py   # after build.py + annotate.py
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
R = HERE / "renders"
REF = HERE / "reference" / "june-render-annotated.png"
PHOTO = HERE / "reference" / "rig-2026-09-11-front.jpg"
FONT = "/usr/share/fonts/truetype/crosextra/Carlito-Regular.ttf"


def _font(size):
    try:
        return ImageFont.truetype(FONT, size)
    except OSError:
        return ImageFont.load_default()


def _flat(path, h):
    im = Image.open(path).convert("RGBA")
    white = Image.new("RGBA", im.size, (255, 255, 255, 255))
    white.alpha_composite(im)
    im = white.convert("RGB")
    return im.resize((round(im.width * h / im.height), h), Image.LANCZOS)


def _trim(im, pad=12):
    """Crop a white-background image to its content plus a margin."""
    from PIL import ImageChops
    bg = Image.new("RGB", im.size, (255, 255, 255))
    box = ImageChops.difference(im, bg).getbbox()
    if not box:
        return im
    x0, y0, x1, y1 = box
    return im.crop((max(0, x0 - pad), max(0, y0 - pad),
                    min(im.width, x1 + pad), min(im.height, y1 + pad)))


def panel(images, captions, out, h=620):
    ims = [_flat(p, h) if isinstance(p, Path) else p for p in images]
    gap, cap_h = 40, 60
    W = sum(i.width for i in ims) + gap * (len(ims) + 1)
    canvas = Image.new("RGB", (W, h + cap_h + 2 * gap), "white")
    d = ImageDraw.Draw(canvas)
    x = gap
    for im, cap in zip(ims, captions):
        canvas.paste(im, (x, gap))
        tw = d.textlength(cap, font=_font(30))
        d.text((x + (im.width - tw) / 2, gap + h + 12), cap, font=_font(30), fill="black")
        x += im.width + gap
    canvas.save(out)
    print(f"  -> {out.relative_to(HERE)}")


def main():
    panel([REF, R / "assembly_iso_az090_annotated.png"],
          ["June render (issue #165 / Fig. 1a)", "Current design, same camera"],
          R / "compare_june_vs_current.png")
    front = _trim(_flat(R / "assembly_front_from_outlet.png", 1000))
    photo = Image.open(PHOTO).convert("RGB")
    h = 620
    panel([front.resize((round(front.width * h / front.height), h), Image.LANCZOS),
           photo.resize((round(photo.width * h / photo.height), h), Image.LANCZOS)],
          ["New assembly, from the outlet end", "Rig, 11 Sep 2026 (#156)"],
          R / "compare_front_vs_photo.png", h=h)


if __name__ == "__main__":
    main()
