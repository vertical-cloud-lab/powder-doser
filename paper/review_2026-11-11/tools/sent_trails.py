"""Per-sentence cursor trails. python3 sent_trails.py <cursor_json> <whisper_json> <frames_dir> <out_dir>"""
import sys, os, json, math, re
from PIL import Image, ImageDraw, ImageFont
cj, wj, fd, od = sys.argv[1:5]
os.makedirs(od, exist_ok=True)
C = json.load(open(cj)); fps = C['fps']; F = C['frames']
W = json.load(open(wj))
words = [w for s in W['segments'] for w in s['words']]
# chunk into sentences
chunks, cur = [], []
for i, w in enumerate(words):
    if cur and (w['start'] - cur[-1]['end'] > 1.4 or (cur[-1]['end'] - cur[0]['start'] > 9)):
        chunks.append(cur); cur = []
    cur.append(w)
    if re.search(r'[.?!]$', w['word'].strip()) and cur[-1]['end'] - cur[0]['start'] > 1.5:
        chunks.append(cur); cur = []
if cur: chunks.append(cur)
font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 19)
fbig = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 24)
def col(u):
    u = min(max(u, 0), 1); return (int(40 + 215 * u), int(60 * (1 - u)), int(255 * (1 - u)))
idx = []
for ci, ch in enumerate(chunks):
    a, b = ch[0]['start'] - 0.3, ch[-1]['end'] + 0.3
    fr = [r for r in F if a <= r['t'] <= b]
    # choose the longest non-scroll run
    runs, run = [], []
    for r in fr:
        if r.get('scroll'):
            if run: runs.append(run); run = []
        else: run.append(r)
    if run: runs.append(run)
    if not runs: continue
    nscroll = sum(1 for r in fr if r.get('scroll'))
    for ri, run in enumerate(runs):
        if len(runs) > 1 and len(run) < 6: continue
        ra, rb = run[0]['t'], run[-1]['t']
        k = min(int(math.floor(max(ra, rb - 0.4))) + 1, len(os.listdir(fd)))
        im = Image.open(os.path.join(fd, f't{k:04d}.jpg')).convert('RGB')
        d = ImageDraw.Draw(im, 'RGBA')
        pts = [(r['t'], r['pos']) for r in run if r.get('pos')]
        for (ta, pa), (tb, pb) in zip(pts, pts[1:]):
            if pa != pb:
                d.line([tuple(pa), tuple(pb)], fill=col((ta - ra) / max(rb - ra, 1e-6)) + (220,), width=4)
        for (ta, pa) in pts[::4]:
            u = (ta - ra) / max(rb - ra, 1e-6); d.ellipse([pa[0]-5, pa[1]-5, pa[0]+5, pa[1]+5], fill=col(u) + (255,))
        # word labels at cursor position when spoken
        placed = []
        ws = [w for w in ch if ra - 0.4 <= w['start'] <= rb + 0.4]
        groups, g = [], []
        for w in ws:
            if g and w['start'] - g[0]['start'] > 1.0: groups.append(g); g = []
            g.append(w)
        if g: groups.append(g)
        for g in groups:
            p = None
            for (t, pp) in pts:
                if t <= g[0]['start']: p = pp
            if p is None and pts: p = pts[0][1]
            if p is None: continue
            txt = ''.join(w['word'] for w in g).strip()
            x, y = p[0] + 16, p[1] + 12
            for (px, py) in placed:
                if abs(px - x) < 220 and abs(py - y) < 23: y = py + 23
            placed.append((x, y))
            tw = d.textlength(txt, font=font)
            d.rectangle([x-2, y-1, x+tw+2, y+22], fill=(255, 255, 200, 225), outline=col((g[0]['start'] - ra) / max(rb - ra, 1e-6)) + (255,), width=2)
            d.text((x, y), txt, fill=(0, 0, 0), font=font)
        # crop to region of motion
        xs = [p[0] for _, p in pts] or [925]; ys = [p[1] for _, p in pts] or [577]
        cx0, cx1 = max(min(xs) - 450, 0), min(max(xs) + 450, 1850)
        cy0, cy1 = max(min(ys) - 300, 150), min(max(ys) + 300, 1154)
        if cx1 - cx0 < 1100: 
            m = (cx0 + cx1) / 2; cx0, cx1 = max(0, m - 550), min(1850, m + 550)
        if cy1 - cy0 < 700:
            m = (cy0 + cy1) / 2; cy0, cy1 = max(150, m - 350), min(1154, m + 350)
        im = im.crop((int(cx0), int(cy0), int(cx1), int(cy1)))
        sc = min(1.0, 1200 / im.width)
        im = im.resize((int(im.width * sc), int(im.height * sc)), Image.LANCZOS)
        hdr = f'#{ci:03d}.{ri} {int(ra)//60}:{ra%60:04.1f}-{int(rb)//60}:{rb%60:04.1f}  scroll-frames={nscroll}'
        canvas = Image.new('RGB', (im.width, im.height + 40), (255, 255, 0))
        canvas.paste(im, (0, 40)); dd = ImageDraw.Draw(canvas); dd.text((6, 6), hdr, fill='black', font=fbig)
        out = os.path.join(od, f'c{ci:03d}_{ri}.jpg'); canvas.save(out, quality=86)
        idx.append({'chunk': ci, 'run': ri, 'a': ra, 'b': rb, 'file': out, 'text': ''.join(w['word'] for w in ch).strip()})
json.dump(idx, open(os.path.join(od, 'index.json'), 'w'), indent=1)
for e in idx:
    print(f"c{e['chunk']:03d}_{e['run']} {int(e['a'])//60}:{e['a']%60:04.1f}-{int(e['b'])//60}:{e['b']%60:04.1f} | {e['text']}")
