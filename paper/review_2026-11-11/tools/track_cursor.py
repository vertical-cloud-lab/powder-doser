"""Track the mouse cursor in a screen recording by frame differencing.

python3 track_cursor.py <video> <out_json> [fps]
Per frame: changed-pixel count (scroll detection) and small motion blobs; the cursor
position is the blob farthest from the previous position when two blobs appear.
"""
import sys, json, subprocess
import numpy as np, cv2
video, out = sys.argv[1], sys.argv[2]
fps = float(sys.argv[3]) if len(sys.argv) > 3 else 10.0
W, H = 1850, 1154
cmd = ['ffmpeg', '-v', 'error', '-i', video, '-vf', f'fps={fps},format=gray', '-f', 'rawvideo', '-']
p = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=W * H * 4)
prev = None
k = 0
pos = None
rows = []
kern = np.ones((5, 5), np.uint8)
while True:
    buf = p.stdout.read(W * H)
    if len(buf) < W * H:
        break
    f = np.frombuffer(buf, np.uint8).reshape(H, W)
    t = k / fps
    rec = {'k': k, 't': round(t, 2)}
    if prev is not None:
        d = cv2.absdiff(f, prev)
        m = (d > 40).astype(np.uint8)
        n = int(m.sum())
        rec['n'] = n
        if n > 25000:
            rec['scroll'] = True
        else:
            m2 = cv2.dilate(m, kern)
            num, lab, stats, cent = cv2.connectedComponentsWithStats(m2, 8)
            blobs = []
            for i in range(1, num):
                x, y, w, h, a = stats[i]
                if w <= 90 and h <= 90 and a >= 30:
                    blobs.append([int(x), int(y), int(w), int(h), int(a)])
            rec['blobs'] = blobs
            if blobs:
                cs = [(b[0] + b[2] / 2, b[1] + b[3] / 2) for b in blobs]
                if pos is None or len(cs) == 1:
                    c = max(cs, key=lambda c: 0) if len(cs) == 1 else cs[-1]
                    if len(cs) > 1 and pos is None:
                        c = cs[0]
                    pos = c
                else:
                    pos = max(cs, key=lambda c: (c[0] - pos[0]) ** 2 + (c[1] - pos[1]) ** 2)
    rec['pos'] = [round(pos[0]), round(pos[1])] if pos else None
    rows.append(rec)
    prev = f
    k += 1
json.dump({'fps': fps, 'W': W, 'H': H, 'frames': rows}, open(out, 'w'))
print('frames', k, 'scroll frames', sum(1 for r in rows if r.get('scroll')),
      'with blobs', sum(1 for r in rows if r.get('blobs')))
