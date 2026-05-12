#!/usr/bin/env python3
"""Render per-concept and composite dispensing animations from the
**CAD-grounded** scene module :mod:`scripts.scene_cad`.

Every frame is built from parts whose ``(x, z, dx, dz)`` rectangles
come straight out of CadQuery assemblies in the shared world frame
(:mod:`scripts.scene_world_frame`). The same :data:`PROJ.project` /
:data:`PROJ.project_box` transform is applied to every concept on
every frame — so the bed-line, gantry rail, vial mouths and mechanism
home column land on the same pixel rows/columns across all eight
tiles, by construction. (Per @sgbaird-yolo's PR-#13 comment asking
for the visualisation to be grounded in something physical.)

Outputs (all under ``cad/alternatives_cq/``):

* ``<X>_animation.gif`` — per-concept GIF (X ∈ {A,…,H}).
* ``composite_animation.gif`` — 4×2 composite of all eight (built
  frame-by-frame from the per-concept frames so tiles never desync).
* ``<X>_frame_<phase>.png`` — one still per phase per concept.

Run:

    python scripts/animate_dispensing_cad.py
"""
from __future__ import annotations

import io
from pathlib import Path
from typing import Iterable, List, Tuple

from PIL import Image, ImageDraw, ImageFont

from scene_cad import CONCEPTS, phase_at, shared_parts, Part
from scene_world_frame import PROJ, WORLD

# ---------------------------------------------------------------------------
# Style
# ---------------------------------------------------------------------------

PALETTE = {
    "body":    {"fill": (220, 225, 235, 255), "outline": (90, 100, 120, 255)},
    "accent":  {"fill": (190, 220, 250, 255), "outline": (0, 110, 200, 255)},
    "accent2": {"fill": (250, 210, 195, 255), "outline": (220, 90, 60, 255)},
    "powder":  {"fill": (180, 130, 70, 255),  "outline": (120, 80, 30, 255)},
    "gantry":  {"fill": (180, 185, 195, 255), "outline": (90, 95, 110, 255)},
    "bed":     {"fill": (90, 100, 115, 255),  "outline": (60, 70, 90, 255)},
    "vial":    {"fill": (245, 248, 252, 255), "outline": (90, 100, 120, 255)},
}

BG = (255, 255, 255, 255)
TITLE_BG = (32, 56, 92, 255)
TITLE_FG = (255, 255, 255, 255)
LABEL_FG = (24, 24, 28, 255)
MUTED_FG = (90, 95, 110, 255)


def _font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
        if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    for c in candidates:
        if Path(c).exists():
            return ImageFont.truetype(c, size)
    return ImageFont.load_default()


F_TITLE = _font(14, bold=True)
F_PHASE = _font(11, bold=True)
F_SMALL = _font(9)


# ---------------------------------------------------------------------------
# Frame builders
# ---------------------------------------------------------------------------

FPS = 12
DURATION_S = 5.0
N_FRAMES = int(FPS * DURATION_S)


def _draw_part(draw: ImageDraw.ImageDraw, part: Part) -> None:
    box = PROJ.project_box(part.x_mm, part.z_mm, part.dx_mm, part.dz_mm)
    x0, y0, x1, y1 = box
    if x1 - x0 < 1 or y1 - y0 < 1:
        return
    pal = PALETTE.get(part.color, PALETTE["body"])
    if part.color in ("powder",):
        draw.rectangle([x0, y0, x1, y1], fill=pal["fill"], outline=None)
    else:
        draw.rectangle([x0, y0, x1, y1], fill=pal["fill"], outline=pal["outline"])


def _draw_anchors(draw: ImageDraw.ImageDraw) -> None:
    """Dotted reference lines for the shared world anchors, for clarity."""
    # Bed line
    bx0, by = PROJ.project(WORLD.work_xmin, WORLD.bed_z)
    bx1, _ = PROJ.project(WORLD.work_xmax, WORLD.bed_z)
    for x in range(int(bx0), int(bx1), 6):
        draw.line([(x, by), (x + 3, by)], fill=(170, 175, 185, 255), width=1)
    # Vial-centre vertical reference
    vx, vy0 = PROJ.project(WORLD.vial_x, WORLD.bed_z)
    _, vy1 = PROJ.project(WORLD.vial_x, WORLD.vial_h)
    for y in range(int(vy1), int(vy0), 6):
        draw.line([(vx, y), (vx, y + 3)], fill=(200, 205, 215, 255), width=1)


def _draw_chrome(draw: ImageDraw.ImageDraw, title: str, phase: str,
                 p: float) -> None:
    draw.rectangle([0, 0, PROJ.frame_w_px, PROJ.title_h_px], fill=TITLE_BG)
    draw.text((10, 7), title, fill=TITLE_FG, font=F_TITLE)
    # phase strip just under title
    strip_y = PROJ.title_h_px
    draw.rectangle([0, strip_y, PROJ.frame_w_px, strip_y + 2],
                   fill=(220, 225, 235, 255))
    width = int((PROJ.frame_w_px) * min(1.0, max(0.0, p)))
    color = {
        "LOAD": (60, 150, 110, 255),
        "APPROACH": (60, 110, 200, 255),
        "DISPENSE": (220, 90, 60, 255),
        "SETTLE": (140, 140, 150, 255),
    }.get(phase, (90, 95, 110, 255))
    draw.rectangle([0, strip_y, width, strip_y + 2], fill=color)
    # phase label at the footer
    text = f"phase: {phase}"
    draw.text((10, PROJ.frame_h_px - PROJ.footer_h_px + 4),
              text, fill=color, font=F_PHASE)
    # scale bar (10 mm) — proves the shared transform is metric
    mm10_px = 10.0 / PROJ.mm_per_px()
    sb_y = PROJ.frame_h_px - 6
    sb_x = PROJ.frame_w_px - 20 - int(mm10_px)
    draw.line([(sb_x, sb_y), (sb_x + mm10_px, sb_y)],
              fill=MUTED_FG, width=2)
    draw.text((sb_x, sb_y - 14), "10 mm", fill=MUTED_FG, font=F_SMALL)


def render_frame(key: str, t: float) -> Image.Image:
    """Render one frame for the given concept key at normalised time t."""
    img = Image.new("RGBA", (PROJ.frame_w_px, PROJ.frame_h_px), BG)
    draw = ImageDraw.Draw(img)
    _draw_anchors(draw)
    # Shared bed + rail + vial first (so mechanism overlays)
    for sp in shared_parts():
        _draw_part(draw, sp)
    title, parts, _asy = CONCEPTS[key](t)
    for part in parts:
        _draw_part(draw, part)
    phase, p = phase_at(t)
    _draw_chrome(draw, f"{key}: {title.split('—', 1)[-1].strip()}", phase, p)
    return img


# ---------------------------------------------------------------------------
# GIF builders
# ---------------------------------------------------------------------------

def render_concept_gif(key: str, out_path: Path) -> None:
    frames: List[Image.Image] = []
    for i in range(N_FRAMES):
        t = i / N_FRAMES
        frames.append(render_frame(key, t).convert("P", palette=Image.ADAPTIVE))
    duration_ms = int(1000 / FPS)
    frames[0].save(
        out_path, save_all=True, append_images=frames[1:],
        duration=duration_ms, loop=0, disposal=2, optimize=False,
    )


def render_composite_gif(keys: Iterable[str], out_path: Path,
                         cols: int = 4) -> None:
    """Composite N×M GIF built frame-by-frame so tiles never desync."""
    keys = list(keys)
    rows = (len(keys) + cols - 1) // cols
    tw, th = PROJ.frame_w_px, PROJ.frame_h_px
    cw, ch = cols * tw, rows * th
    frames: List[Image.Image] = []
    for i in range(N_FRAMES):
        t = i / N_FRAMES
        canvas = Image.new("RGB", (cw, ch), (255, 255, 255))
        for j, key in enumerate(keys):
            tile = render_frame(key, t).convert("RGB")
            r, c = j // cols, j % cols
            canvas.paste(tile, (c * tw, r * th))
        frames.append(canvas.convert("P", palette=Image.ADAPTIVE))
    duration_ms = int(1000 / FPS)
    frames[0].save(
        out_path, save_all=True, append_images=frames[1:],
        duration=duration_ms, loop=0, disposal=2, optimize=False,
    )


def render_phase_stills(key: str, out_dir: Path) -> List[Path]:
    """One PNG per phase mid-point (LOAD, APPROACH, DISPENSE, SETTLE)."""
    out: List[Path] = []
    centers = {"LOAD": 0.125, "APPROACH": 0.335, "DISPENSE": 0.635, "SETTLE": 0.925}
    for phase, t in centers.items():
        img = render_frame(key, t)
        p = out_dir / f"{key}_frame_{phase}.png"
        img.save(p)
        out.append(p)
    return out


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    repo = Path(__file__).resolve().parent.parent
    out_dir = repo / "cad" / "alternatives_cq"
    out_dir.mkdir(parents=True, exist_ok=True)
    keys = list(CONCEPTS.keys())
    print(f"Rendering {len(keys)} concepts × {N_FRAMES} frames "
          f"@ {FPS} fps → {out_dir.relative_to(repo)}")
    for k in keys:
        render_concept_gif(k, out_dir / f"{k}_animation.gif")
        render_phase_stills(k, out_dir)
        print(f"  {k}: animation + 4 phase stills")
    render_composite_gif(keys, out_dir / "composite_animation.gif", cols=4)
    print("  composite_animation.gif (4×2)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
