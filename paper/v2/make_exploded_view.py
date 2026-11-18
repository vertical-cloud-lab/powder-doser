#!/usr/bin/env python3
"""Fig. 1b and SI Fig. S4 (v2): the exploded view with each balloon beside its part.

Review of 17 Nov 2026, point 1.2 (paper/review_2026-11-17/NOTES.md): in
Fig. 1b the balloons should sit as close to their parts as makes sense
(before, leaders such as 18, 11, 7, 8, 16, 2, 10, 9, 20 and 21 crossed the
whole image), and only the main parts belong in the main text; screws and
nuts go to the SI.

Reads the balloon-free render, the part-ID map and the part list written by
render_exploded_view.py (assets/exploded/), and places each balloon on the
white background as near to its own part as it fits, with a short leader to
a point inside that part.  Balloon numbers are PR #170's bill-of-materials
numbers, so the SI table still applies.

    python3 make_exploded_view.py           # both versions

Writes:
    figures/doser_b_exploded.pdf          Fig. 1b: the 13 main parts
    figures/figS_assembly_exploded.pdf    SI Fig. S4: all 25 BOM items, with the BOM
    assets/exploded/exploded_main_balloons.png, exploded_full_bom.png  (PNG copies)
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle
from PIL import Image
from scipy import ndimage

HERE = Path(__file__).resolve().parent
EXP = HERE / "assets" / "exploded"
FIGS = HERE / "figures"
INK, INK2 = "#0b0b0b", "#52514e"
W_IN = 17.1 / 2.54
plt.rcParams.update({"font.size": 6.0, "font.family": "sans-serif", "savefig.dpi": 600})

# The 13 main parts of Fig. 1b (BOM numbers of PR #170), named as in the caption.
MAIN = [1, 2, 4, 7, 9, 12, 14, 15, 19, 20, 21, 23, 25]
# Items with two instances: a balloon on each, unless the two sit together
# (the servo pinions), where one balloon gets a leader to each.
GROUP_ONE_BALLOON = {7}


def load():
    meta = json.loads((EXP / "exploded_parts.json").read_text())
    img = np.asarray(Image.open(EXP / "exploded_render.png").convert("RGB"))
    ids = np.asarray(Image.open(EXP / "exploded_ids.png"))
    return meta, img, ids


def labels_for(meta, numbers, ids):
    """[(BOM no, [instance ids])]: one entry per balloon."""
    out = []
    for no in numbers:
        inst = [p for p in meta["parts"] if p["no"] == no and (ids == p["id"]).sum() > 30]
        if not inst:
            continue
        kind = next(b["kind"] for b in meta["bom"] if b["no"] == no)
        if kind == "Fastener":
            # one balloon, on the most visible of the item's instances
            inst = [max(inst, key=lambda p: (ids == p["id"]).sum())]
            out.append((no, [inst[0]["id"]]))
        elif len(inst) > 1 and no not in GROUP_ONE_BALLOON:
            out.extend((no, [p["id"]]) for p in inst)
        else:
            out.append((no, [p["id"] for p in inst]))
    return out


def place(labels, img, ids, r, gap, box):
    """Greedy placement: each balloon on background, near its part, short
    leaders that avoid other parts, balloons and leaders.  Coordinates in
    render pixels; box = (x0, y0, x1, y1) the region balloons may use."""
    H, W = ids.shape
    solid = img.sum(axis=2) < 3 * 246
    free_dist = ndimage.distance_transform_edt(~solid)          # px to the nearest part
    interior = {}
    for _, inst in labels:
        for i in inst:
            m = ids == i
            dt = ndimage.distance_transform_edt(m)
            keep = dt >= min(5.0, dt.max() * 0.5)                # dots well inside the part
            ys, xs = np.nonzero(keep)
            step = max(1, len(xs) // 4000)
            interior[i] = np.c_[xs[::step], ys[::step]].astype(float)

    placed, leaders = [], []

    def seg_cross(a, b, c, d):
        def ccw(p, q, s):
            return (s[1] - p[1]) * (q[0] - p[0]) - (q[1] - p[1]) * (s[0] - p[0])
        return (ccw(a, c, d) * ccw(b, c, d) < 0) and (ccw(a, b, c) * ccw(a, b, d) < 0)

    def leader_cost(p, c, own):
        n = max(int(np.hypot(*(c - p)) / 4), 2)
        t = np.linspace(0, 1, n)
        xs = np.clip((p[0] + t * (c[0] - p[0])).astype(int), 0, W - 1)
        ys = np.clip((p[1] + t * (c[1] - p[1])).astype(int), 0, H - 1)
        v = ids[ys, xs]
        other = (v != 0) & ~np.isin(v, own)
        return other.mean() * np.hypot(*(c - p))               # length over other parts

    def candidates(inst):
        pts = np.vstack([interior[i] for i in inst])
        ctr = pts.mean(0)
        out = []
        for ang in np.radians(np.arange(0, 360, 7.5)):
            u = np.array([np.cos(ang), np.sin(ang)])
            for dist in np.arange(r + gap, 900, 10.0):
                c = ctr + u * dist
                if not (box[0] + r < c[0] < box[2] - r and box[1] + r < c[1] < box[3] - r):
                    break
                if free_dist[int(c[1]), int(c[0])] < r + gap:
                    continue
                out.append(c)
                break                                           # nearest free spot on this ray
        return out

    order = []
    for no, inst in labels:
        cands = candidates(inst)
        order.append((len(cands), no, inst, cands))
    order.sort(key=lambda t: t[0])
    result = []
    for _, no, inst, cands in order:
        best, best_cost = None, np.inf
        for c in cands:
            if any(np.hypot(*(c - q)) < 2 * r + 6 for q in placed):
                continue
            ends, cost = [], 0.0
            for i in inst:
                pts = interior[i]
                k = np.argmin(np.hypot(pts[:, 0] - c[0], pts[:, 1] - c[1]))
                p = pts[k]
                ends.append(p)
                length = np.hypot(*(c - p))
                cost += length + 4.0 * leader_cost(p, c, inst)
                for a, b in leaders:
                    if seg_cross(p, c, a, b):
                        cost += 400.0
                for q in placed:                                # leader through a balloon
                    d = c - p
                    t = np.clip(np.dot(q - p, d) / max(np.dot(d, d), 1e-9), 0, 1)
                    if np.hypot(*(p + t * d - q)) < r + 2:
                        cost += 400.0
            if cost < best_cost:
                best, best_cost, best_ends = c, cost, ends
        if best is None:
            raise SystemExit(f"no room for balloon {no}")
        placed.append(best)
        for p in best_ends:
            leaders.append((p, best))
        result.append((no, best, best_ends))
    return result


def draw(ax, result, r, fs):
    for no, c, ends in result:
        for p in ends:
            d = c - p
            e = c - d / np.hypot(*d) * r                        # stop at the balloon's edge
            ax.plot([p[0], e[0]], [p[1], e[1]], color=INK2, lw=0.5, zorder=4,
                    solid_capstyle="butt")
            ax.plot(*p, "o", ms=1.6, color=INK, zorder=5)
        ax.add_patch(Circle(c, r, fc="white", ec=INK, lw=0.55, zorder=6))
        ax.text(c[0], c[1], str(no), ha="center", va="center_baseline", fontsize=fs,
                fontweight="bold", color=INK, zorder=7)


def crop_box(img, pad):
    solid = img.sum(axis=2) < 3 * 246
    ys, xs = np.nonzero(solid)
    return (xs.min() - pad, ys.min() - pad, xs.max() + pad, ys.max() + pad)


def main_panel(w_in: float = 3.182, h_in: float = 2.49) -> None:
    """Fig. 1b: the 13 main parts.  Same print size as PR #170's panel."""
    meta, img, ids = load()
    H, W = ids.shape
    # frame: the parts, centred, with the panel's aspect ratio
    x0, y0, x1, y1 = crop_box(img, 40)
    hh = (y1 - y0)
    ww = hh * w_in / h_in
    cx = (x0 + x1) / 2
    fx0, fx1 = max(cx - ww / 2, 0), min(cx + ww / 2, W)
    fy0, fy1 = max(y0, 0), min(y1, H)
    px_per_in = (fy1 - fy0) / h_in
    r = 0.058 * px_per_in                                        # balloon radius
    labels = labels_for(meta, MAIN, ids)
    result = place(labels, img, ids, r, gap=0.035 * px_per_in, box=(fx0, fy0, fx1, fy1))
    fig = plt.figure(figsize=(w_in, h_in))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.imshow(img, interpolation="lanczos")
    ax.set_xlim(fx0, fx1), ax.set_ylim(fy1, fy0)
    ax.set_axis_off()
    draw(ax, result, r, fs=5.3)
    FIGS.mkdir(exist_ok=True)
    fig.savefig(FIGS / "doser_b_exploded.pdf")
    fig.savefig(EXP / "exploded_main_balloons.png", dpi=300)
    plt.close(fig)
    print("wrote doser_b_exploded:", ", ".join(str(n) for n, _ in labels))


def si_panel(w_in: float = W_IN) -> None:
    """SI Fig. S4 (exploded view): every BOM item ballooned, with the BOM."""
    meta, img, ids = load()
    H, W = ids.shape
    x0, y0, x1, y1 = crop_box(img, 60)
    view_w = 0.60 * w_in
    hh = y1 - y0
    h_in = view_w * hh / (x1 - x0 + 2 * 0.15 * (x1 - x0))
    ww = hh * view_w / h_in
    cx = (x0 + x1) / 2
    fx0, fx1 = max(cx - ww / 2, 0), min(cx + ww / 2, W)
    px_per_in = hh / h_in
    r = 0.06 * px_per_in
    labels = labels_for(meta, [b["no"] for b in meta["bom"]], ids)
    result = place(labels, img, ids, r, gap=0.03 * px_per_in, box=(fx0, y0, fx1, y1))
    fig = plt.figure(figsize=(w_in, h_in))
    ax = fig.add_axes([0, 0, view_w / w_in, 1])
    ax.imshow(img, interpolation="lanczos")
    ax.set_xlim(fx0, fx1), ax.set_ylim(y1, y0)
    ax.set_axis_off()
    draw(ax, result, r, fs=5.2)
    # the bill of materials beside it
    axt = fig.add_axes([view_w / w_in + 0.01, 0.02, 1 - view_w / w_in - 0.01, 0.96])
    axt.set_axis_off()
    axt.set_xlim(0, 1), axt.set_ylim(0, 1)
    rows = meta["bom"]
    dy = 0.94 / (len(rows) + 1)
    y = 0.98
    cols = (0.0, 0.075, 0.735, 0.815)
    for x, t in zip(cols, ("No.", "Part", "Qty", "Type")):
        axt.text(x, y, t, fontsize=5.6, fontweight="bold", va="top", color=INK)
    y -= dy
    axt.plot([0, 1], [y + 0.25 * dy, y + 0.25 * dy], color=INK2, lw=0.4)
    for b in rows:
        kind = {"Printed (PLA)": "printed", "User-supplied": "yours"}.get(b["kind"], b["kind"].lower())
        main = b["no"] in MAIN
        for x, t in zip(cols, (str(b["no"]), b["name"], str(b["qty"]), kind)):
            axt.text(x, y, t, fontsize=5.4, va="top", color=INK,
                     fontweight="bold" if (main and x == cols[0]) else "normal")
        y -= dy
    fig.savefig(FIGS / "figS_assembly_exploded.pdf")
    fig.savefig(EXP / "exploded_full_bom.png", dpi=300)
    plt.close(fig)
    print("wrote figS_assembly_exploded:", len(labels), "balloons")


if __name__ == "__main__":
    main_panel()
    si_panel()
