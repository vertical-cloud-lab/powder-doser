"""Burst contact sheet: python3 burst.py <video> <out.jpg> <start_s> <end_s> <fps> <x0> <y0> <x1> <y1> <cols> <tile_w>"""
import sys, subprocess, numpy as np
from PIL import Image, ImageDraw, ImageFont
v, out = sys.argv[1], sys.argv[2]
a, b, fps = float(sys.argv[3]), float(sys.argv[4]), float(sys.argv[5])
x0, y0, x1, y1 = map(int, sys.argv[6:10]); cols, tw = int(sys.argv[10]), int(sys.argv[11])
W, H = 1850, 1154
cw, ch = x1 - x0, y1 - y0
cmd = ['ffmpeg', '-v', 'error', '-ss', f'{a}', '-i', v, '-t', f'{b-a}', '-vf', f'fps={fps},crop={cw}:{ch}:{x0}:{y0}', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-']
raw = subprocess.run(cmd, capture_output=True).stdout
n = len(raw) // (cw * ch * 3)
th = round(tw * ch / cw)
rows = (n + cols - 1) // cols
sheet = Image.new('RGB', (cols * tw, rows * th), 'white')
d = ImageDraw.Draw(sheet)
font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 16)
for i in range(n):
    fr = np.frombuffer(raw[i*cw*ch*3:(i+1)*cw*ch*3], np.uint8).reshape(ch, cw, 3)
    im = Image.fromarray(fr).resize((tw, th), Image.LANCZOS)
    x, y = (i % cols) * tw, (i // cols) * th
    sheet.paste(im, (x, y))
    t = a + i / fps
    d.rectangle([x, y, x + 70, y + 20], fill='yellow'); d.text((x + 3, y + 1), f'{int(t)//60}:{t%60:04.1f}', fill='black', font=font)
    d.rectangle([x, y, x + tw - 1, y + th - 1], outline='red')
sheet.save(out, quality=85); print(out, n, 'frames')
