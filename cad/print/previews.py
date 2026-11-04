"""Toolpath previews of the sliced plates, from the G-code inside each .gcode.3mf, and the contact sheet plates.png.

    python previews.py          # after slice.py

Each plate's extrusion moves are drawn in an isometric view, oldest layer first, coloured by feature
(Bambu's "; FEATURE:" comments), over the outline of the printable area (the H2D's left nozzle 325 x 320,
the A1 mini's 180 x 180). Writes <design>/plates/<plate>_toolpath.png; plates that are copies of another
(same printer, parts and positions) share one drawing. plates.png puts, for every distinct plate, Bambu
Studio's own picture of it (when slice.py could make one) beside the toolpaths.
"""
from __future__ import annotations

import json
import math
import re
import shutil
import textwrap
import zipfile
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.collections import LineCollection  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from PIL import Image  # noqa: E402

HERE = Path(__file__).resolve().parent
DESIGNS = ("paternoster", "chain-carousel-v2")
# feature -> group; groups in fixed categorical order (validated palette, dataviz skill)
GROUPS = [("Outer wall", "#2a78d6"), ("Inner wall", "#eb6834"), ("Infill", "#1baf7a"),
          ("Top / bottom surface", "#eda100"), ("Bridge / overhang", "#e87ba4"), ("Support / brim", "#008300")]
FEATURE_GROUP = {"Outer wall": 0, "Inner wall": 1, "Sparse infill": 2, "Internal solid infill": 2, "Gap infill": 2,
                 "Top surface": 3, "Bottom surface": 3, "Bridge": 4, "Internal Bridge": 4, "Overhang wall": 4,
                 "Support": 5, "Support interface": 5, "Support transition": 5, "Brim": 5, "Skirt": 5}
C30, S30 = math.cos(math.radians(30)), math.sin(math.radians(30))
WORD = re.compile(r"([XYZE])(-?[\d.]+)")


def segments(gcode: str):
    """(x0, y0, x1, y1, z, group) of every extrusion move in a known feature."""
    x = y = z = 0.0
    rel = True
    group = None
    out = []
    for line in gcode.splitlines():
        if line.startswith(";"):
            if line.startswith("; FEATURE:"):
                group = FEATURE_GROUP.get(line[10:].strip())
            continue
        if line.startswith("M83"):
            rel = True
        elif line.startswith("M82"):
            rel = False
        if not (line.startswith("G1 ") or line.startswith("G0 ") or line.startswith("G2 ") or line.startswith("G3 ")):
            continue
        w = dict(WORD.findall(line.split(";")[0]))
        nx, ny = float(w.get("X", x)), float(w.get("Y", y))
        if "Z" in w:
            z = float(w["Z"])
        e = float(w.get("E", 0.0))
        if group is not None and e > 0 and rel and (nx != x or ny != y):
            out.append((x, y, nx, ny, z, group))
        x, y = nx, ny
    return np.array(out, dtype=float).reshape(-1, 6)


def iso(x, y, z):
    return (x - y) * C30, (x + y) * S30 + z


def draw(seg: np.ndarray, bed: tuple[float, float], title: str, path: Path) -> None:
    order = np.lexsort((-(seg[:, 0] + seg[:, 1]), seg[:, 4]))
    s = seg[order]
    p0 = np.stack(iso(s[:, 0], s[:, 1], s[:, 4]), axis=1)
    p1 = np.stack(iso(s[:, 2], s[:, 3], s[:, 4]), axis=1)
    cols = np.array([GROUPS[int(g)][1] for g in range(len(GROUPS))])[s[:, 5].astype(int)]
    fig, ax = plt.subplots(figsize=(7.0, 5.6), dpi=150)
    bx = np.array([0, bed[0], bed[0], 0, 0])
    by = np.array([0, 0, bed[1], bed[1], 0])
    ax.fill(*iso(bx, by, 0 * bx), color="#ecebe6", zorder=0)
    ax.plot(*iso(bx, by, 0 * bx), color="#9b9a94", lw=0.8, zorder=1)
    ax.add_collection(LineCollection(np.stack([p0, p1], axis=1), colors=cols, linewidths=0.35, zorder=2))
    ax.set_aspect("equal")
    ax.autoscale_view()
    ax.axis("off")
    present = sorted(set(s[:, 5].astype(int)))
    ax.legend(handles=[Line2D([0], [0], color=GROUPS[g][1], lw=2.5, label=GROUPS[g][0]) for g in present],
              loc="upper left", frameon=False, fontsize=7.5, labelcolor="#33332f")
    ax.set_title(title, fontsize=9, color="#1f1f1c", loc="left")
    fig.tight_layout()
    fig.savefig(path, facecolor="white")
    plt.close(fig)


def caption(p: dict, n_same: int) -> str:
    parts = ", ".join(f"{k} x{v}" for k, v in p["parts"].items())
    rep = f" (x{n_same} identical plates)" if n_same > 1 else ""
    return (f"{p['plate']}{rep}: {p['printer']}\n{parts}\n{p.get('print_time')}, {p.get('filament_g')} g PETG, "
            f"{p.get('layers')} layers, support {'on' if p.get('support_used') else 'off'}")


def main() -> None:
    tiles = []
    for design in DESIGNS:
        rep = json.loads((HERE / design / "slice_report.json").read_text())
        done = {}
        for p in rep["plates"]:
            sig = json.dumps([p["printer_key"], p["parts"], p["positions"]])
            out = HERE / design / "plates" / f"{p['plate']}_toolpath.png"
            if sig in done:
                shutil.copy(done[sig][0], out)
                done[sig][1] += 1
                p["toolpath_png"] = f"plates/{out.name}"
                continue
            f3 = HERE / design / (p.get("gcode_3mf") or "")
            if not f3.is_file():
                continue
            with zipfile.ZipFile(f3) as z:
                g = z.read(next(n for n in z.namelist() if re.match(r"Metadata/plate_\d+\.gcode$", n))).decode(errors="replace")
            seg = segments(g)
            draw(seg, tuple(p["bed_mm"]), f"{design} / {p['plate']}: sliced toolpaths ({p['printer']})", out)
            p["toolpath_png"] = f"plates/{out.name}"
            done[sig] = [out, 1]
            tiles.append([design, p, sig, 1])
            print(f"  {design}/{p['plate']}: {len(seg)} extrusion moves -> {out.name}", flush=True)
        (HERE / design / "slice_report.json").write_text(json.dumps(rep, indent=1) + "\n")
        for t in tiles:
            if t[0] == design:
                t[3] = done[t[2]][1]
    sheet(tiles)


def _crop(im: Image.Image) -> Image.Image:
    """Flatten onto white and crop to the drawing."""
    im = im.convert("RGBA")
    flat = Image.alpha_composite(Image.new("RGBA", im.size, (255, 255, 255, 255)), im).convert("RGB")
    box = Image.eval(flat.convert("L"), lambda v: 255 if v < 250 else 0).getbbox()
    return flat.crop(box) if box else flat


def _fit(im: Image.Image, w: int, h: int) -> Image.Image:
    k = min(w / im.width, h / im.height)
    return im.resize((max(1, int(im.width * k)), max(1, int(im.height * k))), Image.LANCZOS)


def sheet(tiles) -> None:
    """plates.png: one row per distinct plate, Studio's picture | toolpaths | caption."""
    from PIL import ImageDraw, ImageFont
    font_path = Path(matplotlib.get_data_path()) / "fonts" / "ttf" / "DejaVuSans.ttf"
    f_txt, f_head = ImageFont.truetype(str(font_path), 17), ImageFont.truetype(str(font_path), 22)
    W, H, CAP, PAD = 640, 420, 96, 24
    head = 84
    img = Image.new("RGB", (2 * W + 3 * PAD, head + len(tiles) * (H + CAP + PAD)), "white")
    d = ImageDraw.Draw(img)
    d.text((PAD, 14), "3D-printed parts of both carousels, sliced in Bambu Studio 02.08.02.61: PETG, 0.20 mm layers, 3 walls, 25 % infill,\n"
           "supports off. Left: Studio's own plate picture; right: the sliced toolpaths", fill="#1f1f1c", font=f_head, spacing=6)
    y = head
    for design, p, _, n in tiles:
        studio = HERE / design / (p.get("studio_png") or "")
        if studio.is_file():
            a = _fit(_crop(Image.open(studio)), W, H)
            img.paste(a, (PAD + (W - a.width) // 2, y + (H - a.height) // 2))
        b = _fit(_crop(Image.open(HERE / design / p["toolpath_png"])), W, H)
        img.paste(b, (2 * PAD + W + (W - b.width) // 2, y + (H - b.height) // 2))
        first, parts, last = caption(p, n).split("\n")
        lines = [f"{design}  |  {first}"] + textwrap.wrap(parts, 135) + [last]
        d.text((PAD, y + H + 4), "\n".join(lines[:4]), fill="#1f1f1c", font=f_txt, spacing=5)
        y += H + CAP + PAD
        d.line([(PAD, y - PAD // 2), (img.width - PAD, y - PAD // 2)], fill="#d8d7d0", width=1)
    img.save(HERE / "plates.png", optimize=True)
    rows = len(tiles)
    print(f"plates.png: {rows} distinct plates")


if __name__ == "__main__":
    main()
