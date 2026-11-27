"""Contact sheets of 1-fps frames: python3 contact.py <frames_dir> <out_dir> <step_s> <cols> <rows> <tile_w> [start_s] [end_s]"""
import sys, os
from PIL import Image, ImageDraw, ImageFont
fd, od, step, cols, rows, tw = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]), int(sys.argv[6])
start = int(sys.argv[7]) if len(sys.argv) > 7 else 0
end = int(sys.argv[8]) if len(sys.argv) > 8 else 10**9
os.makedirs(od, exist_ok=True)
n = len([f for f in os.listdir(fd) if f.endswith('.jpg')])
ts = [t for t in range(start, min(n, end + 1), step)]
th = round(tw * 1154 / 1850)
try:
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 22)
except Exception:
    font = ImageFont.load_default()
per = cols * rows
for si in range(0, len(ts), per):
    chunk = ts[si:si + per]
    sheet = Image.new('RGB', (cols * tw, rows * th), 'white')
    d = ImageDraw.Draw(sheet)
    for k, t in enumerate(chunk):
        im = Image.open(os.path.join(fd, f't{t+1:04d}.jpg')).convert('RGB').resize((tw, th), Image.LANCZOS)
        x, y = (k % cols) * tw, (k // cols) * th
        sheet.paste(im, (x, y))
        lab = f'{t//60:02d}:{t%60:02d}'
        d.rectangle([x, y, x + 78, y + 28], fill='yellow')
        d.text((x + 4, y + 2), lab, fill='black', font=font)
        d.rectangle([x, y, x + tw - 1, y + th - 1], outline='red', width=2)
    out = os.path.join(od, f'sheet_{chunk[0]:04d}-{chunk[-1]:04d}.jpg')
    sheet.save(out, quality=85)
    print(out)
