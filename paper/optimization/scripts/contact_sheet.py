"""Render every page of a PDF and tile the pages into one labelled contact sheet.

Usage: python3 contact_sheet.py main.pdf out.png [--cols 6] [--dpi 50]
"""
import argparse, glob, os, subprocess, tempfile
from PIL import Image, ImageDraw, ImageFont

ap = argparse.ArgumentParser()
ap.add_argument("pdf"); ap.add_argument("out")
ap.add_argument("--cols", type=int, default=6)
ap.add_argument("--dpi", type=int, default=50)
ap.add_argument("--title", default="")
a = ap.parse_args()

tmp = tempfile.mkdtemp()
subprocess.run(["pdftoppm", "-r", str(a.dpi), "-png", a.pdf, os.path.join(tmp, "p")], check=True)
pages = sorted(glob.glob(os.path.join(tmp, "p-*.png")))
imgs = [Image.open(p).convert("RGB") for p in pages]
w = max(i.width for i in imgs); h = max(i.height for i in imgs)
n = len(imgs); cols = a.cols; rows = -(-n // cols)
gap = 14; label_h = 26; title_h = 46 if a.title else 0
W = cols * w + (cols + 1) * gap
H = title_h + rows * (h + label_h + gap) + gap
sheet = Image.new("RGB", (W, H), (235, 235, 235))
draw = ImageDraw.Draw(sheet)
font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
font = ImageFont.truetype(font_path, 16) if os.path.exists(font_path) else ImageFont.load_default()
tfont = ImageFont.truetype(font_path, 24) if os.path.exists(font_path) else font
if a.title:
    draw.text((gap, 10), a.title, fill=(30, 30, 30), font=tfont)
for k, im in enumerate(imgs):
    r, c = divmod(k, cols)
    x = gap + c * (w + gap); y = title_h + gap + r * (h + label_h + gap)
    draw.rectangle([x - 1, y - 1, x + im.width, y + im.height], outline=(150, 150, 150))
    sheet.paste(im, (x, y))
    draw.text((x, y + im.height + 4), f"p. {k + 1}", fill=(60, 60, 60), font=font)
sheet.save(a.out, optimize=True)
print(f"{n} pages -> {a.out} ({W}x{H})")
