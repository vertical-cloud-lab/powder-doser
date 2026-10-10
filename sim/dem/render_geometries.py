"""Cut-away gallery of the simulated auger geometries (no particles).

    python render_geometries.py --cfg /tmp/dem/runs/cfg --out results/geometries.png
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import tempfile

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from geometry import AugerParams, auger_triangles  # noqa: E402
from render import face_colors, render_frame, rot_y  # noqa: E402

PANELS = [
    ("rig_t27p5_r60", "Rig auger (CAD): 21 mm bore, solid core,\ncore tip in the 3 mm exit"),
    ("rig_t27p5_r60_tip2", "Rig auger, as-printed guess:\ncore tip cut 2 mm short"),
    ("micro_open", "Micro: 10 mm bore, open 4 mm core,\n5 mm pitch, 2.5 mm exit"),
    ("micro_shaft", "Micro: solid 4 mm shaft"),
    ("micro_rig", "Micro, rig-style: solid core,\ntip in the exit, 0.5 mm flight"),
    ("micro_exit18", "Micro: 1.8 mm exit"),
    ("micro_pitch3", "Micro: 3 mm pitch"),
    ("micro_2start", "Micro: 2-start flight"),
    ("micro_cone45", "Micro: short 45° funnel (dam)"),
    ("micro_cone17", "Micro: long 17° funnel"),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cfg", default="/tmp/dem/runs/cfg")
    ap.add_argument("--out", default="results/geometries.png")
    a = ap.parse_args()
    from PIL import Image, ImageDraw, ImageFont

    tmp = tempfile.mkdtemp()
    tiles = []
    for key, label in PANELS:
        path = os.path.join(a.cfg, key + ".json")
        if not os.path.exists(path):
            continue
        cfg = json.load(open(path))
        P = AugerParams(**cfg["geometry"])
        tris = auger_triangles(P) * 1e-3
        geo = json.loads(json.dumps(P.__dict__))
        cols = face_colors(tris * 1e3, geo)
        beta = math.radians(15.0 - 90.0)  # show every variant at the same 15 deg tilt
        Rd = rot_y(beta)
        bb = tris.reshape(-1, 3) @ Rd.T
        lo, hi = bb.min(0), bb.max(0)
        png = os.path.join(tmp, key + ".png")
        render_frame(np.zeros((0, 9)), tris, 0.0, beta, png, (420, 300), 0.08, tuple((lo + hi) / 2),
                     0.56 * max(hi[0] - lo[0], hi[2] - lo[2]), colors=cols)
        tiles.append((png, label, 2 * P.bore_r))
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 15)
    except OSError:
        font = ImageFont.load_default()
    ncol = 5
    nrow = math.ceil(len(tiles) / ncol)
    W, H, TH = 420, 300, 46
    img = Image.new("RGB", (ncol * W, nrow * (H + TH)), "white")
    d = ImageDraw.Draw(img)
    for i, (png, label, bore) in enumerate(tiles):
        x, y = (i % ncol) * W, (i // ncol) * (H + TH)
        img.paste(Image.open(png).convert("RGB"), (x, y + TH))
        d.multiline_text((x + 10, y + 4), label, fill=(20, 20, 20), font=font, spacing=2)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    img.save(a.out)
    print("wrote", a.out, len(tiles), "panels (each panel auto-scaled; rig bore 21 mm, micro bore 10 mm)")


if __name__ == "__main__":
    main()
