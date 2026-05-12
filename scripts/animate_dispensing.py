#!/usr/bin/env python3
"""animate_dispensing.py — per-concept 2-D dispensing animations (A–H).

Architecture
------------
Each concept is built from small, independently positioned **sub-components**
(``draw_vial``, ``draw_anvil``, ``draw_cup_with_mesh``, ``draw_hopper``,
``draw_pez_strip``, ``draw_capillary``, ``draw_brush_disc``, ``draw_auger``,
``draw_erm_motor``, ``draw_solenoid_actuator``, ``draw_balance``, ``draw_powder_pad``,
``draw_falling_stream``) layered on top of a shared :class:`Stage` that
**defines fixed anchors used by every concept** — most importantly:

* ``stage.frame_w / frame_h``                 — same canvas size for all 8
* ``stage.bed_y``                             — fixed bed-line, same Y across all
* ``stage.vial_cx / stage.vial_top_y``        — vial mouth at the same point
* ``stage.gantry_top_y``                      — gantry rail at the same point
* ``stage.mech_home_x``                       — mechanism rest column

The same anchors are used by every render, so when the eight panels are tiled
into ``composite-animation.gif`` the bed-line, vial mouths, gantry rails and
mechanism columns line up across tiles.

Timing is governed by a **shared phase clock** :func:`shared_phase` mapping
the global cycle ``t_norm ∈ [0,1)`` to four named stages used by every
concept (LOAD → APPROACH → DISPENSE → SETTLE) with fixed boundaries
(0.00, 0.25, 0.42, 0.85, 1.00). Each concept renders its mechanism in
the right pose for the current shared phase, so the composite tile shows
all eight mechanisms loading at the same time, approaching the vial at
the same time, dispensing at the same time, and settling at the same time.

Pure Pillow — no OpenSCAD / Blender / browser required.

    python scripts/animate_dispensing.py
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List, Tuple

from PIL import Image, ImageDraw, ImageFont

REPO = Path(__file__).resolve().parent.parent
OUT_DIR = REPO / "cad" / "alternatives"

# ---------------------------------------------------------------------------
# Canvas + colours
# ---------------------------------------------------------------------------

W, H = 480, 360
FPS = 12
DURATION_S = 5.0
N_FRAMES = int(FPS * DURATION_S)

BG = (255, 255, 255, 0)
TITLE_BG = (32, 56, 92, 255)
TITLE_FG = (255, 255, 255, 255)
PART = (90, 100, 120, 255)
PART_FILL = (220, 225, 235, 255)
ACCENT = (0, 110, 200, 255)
ACCENT2 = (220, 90, 60, 255)
POWDER = (160, 100, 40, 255)
ANVIL = (60, 70, 90, 255)
LABEL = (24, 24, 28, 255)
MUTED = (90, 95, 110, 255)
GANTRY = (140, 145, 155, 255)


def _font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
        if bold
        else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    for c in candidates:
        if Path(c).exists():
            return ImageFont.truetype(c, size)
    return ImageFont.load_default()


F_TITLE = _font(15, bold=True)
F_PHASE = _font(12, bold=True)
F_LABEL = _font(10)
F_SMALL = _font(9)


# ---------------------------------------------------------------------------
# Shared stage + phase clock — anchors used by every concept
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Stage:
    """Fixed anchors used by every concept so tiles line up spatially."""

    frame_w: int = W
    frame_h: int = H
    title_h: int = 30
    footer_h: int = 22
    # gantry rail (top horizontal beam — shared across all 8)
    gantry_top_y: int = 46
    gantry_bot_y: int = 56
    # mechanism rest column (the cup / strip / capillary / disc / auger
    # body sits centred on this X when the gantry is at the home/load
    # position)
    mech_home_x: int = 150
    # vial position is fixed across every concept so the vials line up
    # across the composite tile
    vial_cx: int = 360
    vial_top_y: int = 270
    vial_w: int = 50
    vial_h: int = 60
    # bed-line (anvil / shaker holes / balance / source-pad sit on this Y)
    bed_y: int = 260


STAGE = Stage()


# Shared phase boundaries (in normalised time t∈[0,1]). Every concept maps
# its mechanism action onto these stages, so the composite tile shows all
# eight mechanisms in the same logical phase at the same time.
PHASES = [
    ("LOAD",     0.00, 0.25),  # mechanism is loading powder at the source
    ("APPROACH", 0.25, 0.42),  # mechanism translates to the vial
    ("DISPENSE", 0.42, 0.85),  # active dispensing into vial
    ("SETTLE",   0.85, 1.00),  # mechanism stops; powder lands; readout
]


def shared_phase(t_norm: float) -> Tuple[str, float]:
    """Return (phase_name, progress_in_phase∈[0,1]) at normalised time."""
    t = t_norm % 1.0
    for name, t0, t1 in PHASES:
        if t < t1:
            return name, max(0.0, (t - t0) / max(t1 - t0, 1e-9))
    name, t0, t1 = PHASES[-1]
    return name, 1.0


def fill_frac_for(phase: str, p: float) -> float:
    """Vial-fill fraction shared across all concepts so vials grow in sync."""
    if phase == "LOAD":
        return 0.04
    if phase == "APPROACH":
        return 0.04
    if phase == "DISPENSE":
        return 0.04 + 0.55 * p
    return 0.59  # SETTLE


# ---------------------------------------------------------------------------
# Sub-component drawing primitives — pure functions taking explicit anchors
# ---------------------------------------------------------------------------

def _new_frame() -> Tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGBA", (STAGE.frame_w, STAGE.frame_h), BG)
    return img, ImageDraw.Draw(img)


def draw_title(draw: ImageDraw.ImageDraw, title: str, phase: str,
               phase_local: str = "") -> None:
    draw.rectangle([(0, 0), (STAGE.frame_w, STAGE.title_h)], fill=TITLE_BG)
    draw.text((10, 7), title, fill=TITLE_FG, font=F_TITLE)
    sub = f"phase: {phase}" + (f" — {phase_local}" if phase_local else "")
    draw.text((10, STAGE.frame_h - 18), sub, fill=MUTED, font=F_PHASE)


def draw_gantry_rail(draw: ImageDraw.ImageDraw, head_x: int) -> None:
    """Shared gantry rail at the top, with a moving head at head_x."""
    draw.rectangle([(20, STAGE.gantry_top_y),
                    (STAGE.frame_w - 20, STAGE.gantry_bot_y)],
                   fill=GANTRY, outline=PART, width=1)
    # head/clamp
    draw.rectangle([(head_x - 14, STAGE.gantry_bot_y - 2),
                    (head_x + 14, STAGE.gantry_bot_y + 10)],
                   fill=PART, outline=PART)
    # spindle stem down to the mechanism (drawn separately)
    draw.line([(head_x, STAGE.gantry_bot_y + 10),
               (head_x, STAGE.gantry_bot_y + 18)],
              fill=PART, width=3)


def draw_bed_line(draw: ImageDraw.ImageDraw) -> None:
    """Shared bed-line so anvils, shakers, balances all sit at the same Y."""
    draw.line([(20, STAGE.bed_y + 10),
               (STAGE.frame_w - 20, STAGE.bed_y + 10)],
              fill=ANVIL, width=2)


def draw_vial(draw: ImageDraw.ImageDraw, fill_frac: float = 0.0,
              cx: int | None = None, top_y: int | None = None) -> None:
    cx = STAGE.vial_cx if cx is None else cx
    top_y = STAGE.vial_top_y if top_y is None else top_y
    w, h = STAGE.vial_w, STAGE.vial_h
    x0, x1 = cx - w // 2, cx + w // 2
    y0, y1 = top_y, top_y + h
    draw.rounded_rectangle([(x0, y0), (x1, y1)], radius=6, outline=PART,
                           width=2, fill=(245, 248, 252, 255))
    if fill_frac > 0:
        fh = int((h - 6) * min(1.0, fill_frac))
        draw.rectangle([(x0 + 3, y1 - fh - 3), (x1 - 3, y1 - 3)], fill=POWDER)
    draw.line([(x0, y0), (x1, y0)], fill=PART, width=2)
    draw.text((cx - 18, y0 - 12), "vial", fill=MUTED, font=F_SMALL)


def _powder_grains(draw: ImageDraw.ImageDraw,
                   bbox: Tuple[int, int, int, int],
                   n: int, seed: int = 0, radius: int = 2) -> None:
    rng = random.Random(seed)
    x0, y0, x1, y1 = bbox
    if x1 <= x0 or y1 <= y0 or n <= 0:
        return
    for _ in range(n):
        x = rng.uniform(x0, x1)
        y = rng.uniform(y0, y1)
        draw.ellipse([(x - radius, y - radius), (x + radius, y + radius)],
                     fill=POWDER)


def draw_falling_stream(draw: ImageDraw.ImageDraw,
                        x_center: int, x_spread: int,
                        y_top: int, y_bottom: int,
                        n: int, t: float, seed: int = 0) -> None:
    """Animate n grains falling from y_top to y_bottom in a column.

    The column is centred at x_center with half-width x_spread; this is
    the single primitive used by every concept's dispense step so the
    streams look consistent across tiles.
    """
    rng = random.Random(seed)
    if y_bottom <= y_top or n <= 0:
        return
    for i in range(n):
        cx = rng.uniform(x_center - x_spread, x_center + x_spread)
        phase = (t + i / max(n, 1)) % 1.0
        y = y_top + phase * (y_bottom - y_top)
        draw.ellipse([(cx - 2, y - 2), (cx + 2, y + 2)], fill=POWDER)


def draw_powder_pad(draw: ImageDraw.ImageDraw,
                    cx: int, half_w: int = 50,
                    y_top: int | None = None, h: int = 24,
                    label: str = "powder source",
                    seed: int = 3, n_grains: int = 35) -> None:
    y_top = STAGE.bed_y - h if y_top is None else y_top
    x0, x1 = cx - half_w, cx + half_w
    y1 = y_top + h
    draw.rectangle([(x0, y_top), (x1, y1)], outline=PART, width=2,
                   fill=(235, 225, 200, 255))
    _powder_grains(draw, (x0 + 4, y_top + 4, x1 - 4, y1 - 4),
                   n=n_grains, seed=seed)
    draw.text((cx - 30, y1 + 2), label, fill=MUTED, font=F_SMALL)


def draw_hopper(draw: ImageDraw.ImageDraw, cx: int, y_top: int,
                top_w: int = 60, bot_w: int = 24, h: int = 50,
                seed: int = 7, n_grains: int = 25) -> None:
    pts = [(cx - top_w // 2, y_top), (cx + top_w // 2, y_top),
           (cx + bot_w // 2, y_top + h), (cx - bot_w // 2, y_top + h)]
    draw.polygon(pts, outline=PART, width=2, fill=PART_FILL)
    _powder_grains(draw,
                   (cx - top_w // 2 + 4, y_top + 4,
                    cx + top_w // 2 - 4, y_top + h - 8),
                   n=n_grains, seed=seed)


def draw_cup_with_mesh(draw: ImageDraw.ImageDraw,
                       cx: int, top_y: int,
                       w: int = 80, h: int = 90,
                       pile_frac: float = 1.0,
                       jitter: Tuple[int, int] = (0, 0),
                       seed: int = 1,
                       strike_pad_active: bool = False) -> Tuple[int, int]:
    """Draw the powder-cup with a mesh floor.

    Returns (mesh_cx, mesh_y) so callers can anchor the dispense stream.
    """
    jx, jy = jitter
    x0, x1 = cx - w // 2 + jx, cx + w // 2 + jx
    y0, y1 = top_y + jy, top_y + h + jy
    draw.rectangle([(x0, y0), (x1, y1)], outline=PART, width=2, fill=PART_FILL)
    pile_top = y0 + 18 + int((h - 28) * (1 - max(0.0, min(pile_frac, 1.0))))
    if pile_top < y1 - 8:
        _powder_grains(draw, (x0 + 6, pile_top, x1 - 6, y1 - 8),
                       n=int(40 * pile_frac), seed=seed)
    # mesh
    draw.line([(x0 + 4, y1), (x1 - 4, y1)], fill=ANVIL, width=2)
    for i in range(x0 + 8, x1 - 4, 5):
        draw.line([(i, y1 - 4), (i, y1)], fill=PART, width=1)
    if strike_pad_active:
        draw.rectangle([(x0 - 3, y1 - 4), (x0 + 4, y1 + 2)], fill=ACCENT)
        draw.rectangle([(x1 - 4, y1 - 4), (x1 + 3, y1 + 2)], fill=ACCENT)
    return (x0 + x1) // 2, y1


def draw_anvil(draw: ImageDraw.ImageDraw, cx: int) -> Tuple[int, int]:
    """Bed-mounted strike anvil with a central bore. Returns (bore_cx, bore_y)."""
    y = STAGE.bed_y
    draw.rectangle([(cx - 60, y), (cx + 60, y + 8)], fill=ANVIL)
    draw.polygon([(cx - 14, y), (cx, y - 12), (cx + 14, y)], fill=ANVIL)
    draw.rectangle([(cx - 6, y - 12), (cx + 6, y)], fill=ANVIL)
    return cx, y


def draw_pez_strip(draw: ImageDraw.ImageDraw, x0: int, y0: int,
                   n_chambers: int = 6, ch_w: int = 32, ch_h: int = 32,
                   filled_until_x: int | None = None) -> None:
    """Pez chamber strip. Chambers left of ``filled_until_x`` are full."""
    draw.rectangle([(x0 - 8, y0), (x0 + n_chambers * ch_w + 8, y0 + ch_h)],
                   outline=PART, width=2, fill=PART_FILL)
    for i in range(n_chambers):
        cx0 = x0 + i * ch_w + 3
        cx1 = cx0 + ch_w - 6
        draw.rectangle([(cx0, y0 + 3), (cx1, y0 + ch_h - 3)],
                       outline=PART, width=1)
        ch_center_x = (cx0 + cx1) // 2
        if filled_until_x is not None and ch_center_x < filled_until_x:
            _powder_grains(draw, (cx0 + 2, y0 + 5, cx1 - 2, y0 + ch_h - 5),
                           n=7, seed=i)


def draw_capillary(draw: ImageDraw.ImageDraw, tip_cx: int, tip_y_bot: int,
                   shank_top_y: int, tip_w: int = 8, tip_h: int = 26,
                   load_frac: float = 0.0, plug_loaded: bool = False) -> None:
    draw.rectangle([(tip_cx - 4, shank_top_y), (tip_cx + 4, tip_y_bot - tip_h)],
                   fill=PART, outline=PART)
    draw.rectangle([(tip_cx - tip_w // 2, tip_y_bot - tip_h),
                    (tip_cx + tip_w // 2, tip_y_bot)],
                   outline=PART, width=2, fill=(255, 255, 255, 255))
    if plug_loaded:
        draw.rectangle([(tip_cx - tip_w // 2 + 1, tip_y_bot - tip_h + 2),
                        (tip_cx + tip_w // 2 - 1, tip_y_bot - 1)], fill=POWDER)
    elif load_frac > 0:
        fh = max(1, int((tip_h - 2) * min(1.0, load_frac)))
        draw.rectangle([(tip_cx - tip_w // 2 + 1, tip_y_bot - fh),
                        (tip_cx + tip_w // 2 - 1, tip_y_bot - 1)], fill=POWDER)


def draw_brush_disc(draw: ImageDraw.ImageDraw, cx: int, cy: int,
                    radius: int = 16,
                    laden_frac: float = 0.0, seed: int = 99) -> None:
    draw.ellipse([(cx - radius, cy - radius), (cx + radius, cy + radius)],
                 outline=PART, width=2, fill=PART_FILL)
    for ang_deg in range(180, 361, 12):
        ang = math.radians(ang_deg)
        x1 = cx + (radius + 1) * math.cos(ang)
        y1 = cy + (radius + 1) * math.sin(ang)
        x2 = cx + (radius + 7) * math.cos(ang)
        y2 = cy + (radius + 7) * math.sin(ang)
        draw.line([(x1, y1), (x2, y2)], fill=PART, width=1)
    if laden_frac > 0:
        rng = random.Random(seed)
        for _ in range(int(20 * laden_frac)):
            ang_deg = rng.randint(180, 360)
            ang = math.radians(ang_deg)
            r = radius + 3 + rng.uniform(0, 4)
            x = cx + r * math.cos(ang)
            y = cy + r * math.sin(ang)
            draw.ellipse([(x - 1, y - 1), (x + 1, y + 1)], fill=POWDER)


def draw_comb(draw: ImageDraw.ImageDraw, cx: int) -> Tuple[int, int]:
    """Bed-mounted comb that sits on the shared bed-line. Returns (cx, top_y)."""
    top_y = STAGE.bed_y - 30
    for i in range(-22, 23, 6):
        draw.line([(cx + i, top_y), (cx + i, STAGE.bed_y)],
                  fill=ANVIL, width=2)
    draw.line([(cx - 26, top_y - 2), (cx + 26, top_y - 2)],
              fill=ANVIL, width=2)
    draw.text((cx + 28, top_y), "comb", fill=MUTED, font=F_SMALL)
    return cx, top_y


def draw_auger(draw: ImageDraw.ImageDraw, cx: int, top_y: int,
               tube_w: int = 32, tube_h: int = 110,
               rot_deg: float = 0.0) -> Tuple[int, int]:
    """Vertical auger tube. Returns (outlet_cx, outlet_y)."""
    x0, x1 = cx - tube_w // 2, cx + tube_w // 2
    y0, y1 = top_y, top_y + tube_h
    draw.rectangle([(x0, y0), (x1, y1)], outline=PART, width=2, fill=PART_FILL)
    rot_off = rot_deg / 360.0
    n_steps = 30
    for i in range(n_steps):
        f = (i / n_steps + rot_off * 0.05) % 1.0
        y = y0 + 8 + f * (tube_h - 16)
        phase_w = math.sin((i + rot_off * 6) * math.pi / 3)
        x = cx + int(tube_w * 0.32 * phase_w)
        draw.ellipse([(x - 2, y - 1), (x + 2, y + 1)], fill=ACCENT)
    return cx, y1


def draw_pinion(draw: ImageDraw.ImageDraw, cx: int, cy: int,
                radius: int = 11, rot_deg: float = 0.0) -> None:
    draw.ellipse([(cx - radius, cy - radius), (cx + radius, cy + radius)],
                 outline=PART, width=2, fill=PART_FILL)
    for ang_deg in range(0, 360, 30):
        ang = math.radians(ang_deg + rot_deg)
        x1 = cx + radius * math.cos(ang)
        y1 = cy + radius * math.sin(ang)
        x2 = cx + (radius + 4) * math.cos(ang)
        y2 = cy + (radius + 4) * math.sin(ang)
        draw.line([(x1, y1), (x2, y2)], fill=PART, width=2)


def draw_rack(draw: ImageDraw.ImageDraw, x0: int, x1: int, y: int) -> None:
    draw.rectangle([(x0, y), (x1, y + 12)], outline=ANVIL, width=2,
                   fill=PART_FILL)
    for i in range(x0 + 4, x1 - 2, 8):
        draw.polygon([(i, y), (i + 4, y - 6), (i + 8, y)], fill=ANVIL)


def draw_erm_motor(draw: ImageDraw.ImageDraw, cx: int, cy: int,
                   active: bool = False, t_anim: float = 0.0) -> None:
    color = ACCENT if active else PART
    draw.ellipse([(cx - 9, cy - 9), (cx + 9, cy + 9)],
                 outline=color, width=2, fill=PART_FILL)
    draw.text((cx + 12, cy - 6), "ERM", fill=MUTED, font=F_SMALL)
    if active:
        for k in range(3):
            r = 12 + k * 5
            ang = (t_anim * 6 + k) * 30
            draw.arc([(cx - r, cy - r), (cx + r, cy + r)],
                     start=ang, end=ang + 60, fill=ACCENT, width=1)


def draw_solenoid_actuator(draw: ImageDraw.ImageDraw, cx: int, cy: int,
                           extend: int = 0) -> None:
    draw.rectangle([(cx - 14, cy - 6), (cx + 12, cy + 6)],
                   outline=PART, width=2, fill=PART_FILL)
    draw.text((cx - 16, cy + 9), "solenoid", fill=MUTED, font=F_SMALL)
    draw.rectangle([(cx + 12, cy - 2), (cx + 16 + extend, cy + 2)],
                   fill=ACCENT)


def draw_balance(draw: ImageDraw.ImageDraw, mass_mg: float, target_mg: float,
                 hit_target: bool) -> None:
    bal_y = STAGE.vial_top_y + STAGE.vial_h + 4
    draw.rectangle([(STAGE.vial_cx - 80, bal_y),
                    (STAGE.vial_cx + 80, bal_y + 14)],
                   outline=PART, width=2, fill=PART_FILL)
    color = ACCENT if hit_target else LABEL
    draw.text((STAGE.vial_cx - 70, bal_y + 2),
              f"{mass_mg:0.2f}/{target_mg:0.1f} mg",
              fill=color, font=F_SMALL)


# ---------------------------------------------------------------------------
# Per-concept renderers — each composes sub-components against STAGE anchors
# ---------------------------------------------------------------------------

def _gantry_x(phase: str, p: float, source_x: int) -> int:
    """Common gantry-head X trajectory: home above source → to vial → back."""
    if phase == "LOAD":
        return source_x
    if phase == "APPROACH":
        return int(source_x + (STAGE.vial_cx - source_x) * p)
    if phase == "DISPENSE":
        return STAGE.vial_cx
    return STAGE.vial_cx  # SETTLE


def _gantry_y_for_cup(phase: str, p: float,
                      cup_h: int = 90,
                      hover_above_vial: int = 30) -> int:
    """Cup top-Y trajectory: high → low above vial → low while dispensing."""
    high = STAGE.gantry_bot_y + 18
    low = STAGE.vial_top_y - hover_above_vial - cup_h
    if phase == "LOAD":
        return high
    if phase == "APPROACH":
        return high + int((low - high) * p)
    return low


def render_A(t_norm: float) -> Image.Image:
    """A — Tap-driven sieve cup against a fixed bed-anvil."""
    phase, p = shared_phase(t_norm)
    img, draw = _new_frame()

    source_x = 150  # the cup sits over the anvil; the anvil is at the vial X
    # Tap concept: the anvil + vial sit together; the cup goes home → vial-anvil
    anvil_cx = STAGE.vial_cx
    head_x = _gantry_x(phase, p, source_x)
    # Special: during DISPENSE the cup pecks the anvil (rapid bounce)
    cup_h = 80
    cup_top_y = _gantry_y_for_cup(phase, p, cup_h=cup_h, hover_above_vial=30)
    striking = False
    if phase == "DISPENSE":
        # 4 pecks across phase
        peck = math.sin(p * math.pi * 8)
        if peck > 0.0:
            cup_top_y += int(8 * peck)
            striking = peck > 0.7

    draw_gantry_rail(draw, head_x)
    draw_bed_line(draw)
    bore_cx, bore_y = draw_anvil(draw, anvil_cx)
    pile_frac = 1.0 if phase == "LOAD" else max(0.3, 1.0 - 0.7 * (
        p if phase == "DISPENSE" else 0.0))
    mesh_cx, mesh_y = draw_cup_with_mesh(
        draw, head_x, cup_top_y, w=70, h=cup_h,
        pile_frac=pile_frac if phase != "SETTLE" else 0.3,
        seed=1, strike_pad_active=striking)
    draw_vial(draw, fill_frac=fill_frac_for(phase, p))
    if phase == "DISPENSE" and striking:
        draw_falling_stream(draw, x_center=bore_cx, x_spread=4,
                            y_top=mesh_y, y_bottom=STAGE.vial_top_y,
                            n=8, t=p, seed=42)
    draw_title(draw, "A — Tap-driven sieve cup", phase,
               {"LOAD": "powder loaded into cup",
                "APPROACH": "gantry traverses to anvil",
                "DISPENSE": "peck cycle: cup strikes anvil",
                "SETTLE": "stop, retract, count"}[phase])
    return img


def render_B(t_norm: float) -> Image.Image:
    """B — Pez chamber strip: hopper fills chambers, pawl punches dose."""
    phase, p = shared_phase(t_norm)
    img, draw = _new_frame()

    source_x = 150
    head_x = _gantry_x(phase, p, source_x)
    draw_gantry_rail(draw, head_x)
    draw_bed_line(draw)

    # Hopper is part of the moving head (above the strip)
    strip_y = STAGE.bed_y - 50
    hopper_cx = head_x - 35
    draw_hopper(draw, hopper_cx, strip_y - 50, top_w=44, bot_w=18, h=42,
                n_grains=22, seed=7)
    # Strip slides right under the hopper as we move toward the vial
    if phase == "LOAD":
        strip_offset = 0
    elif phase == "APPROACH":
        strip_offset = int(34 * p)
    else:  # DISPENSE / SETTLE — strip indexed under the pawl
        strip_offset = 34
    strip_x0 = head_x - 70 + strip_offset
    # chambers left of the hopper-bottom are filled
    fill_x = hopper_cx + 6
    draw_pez_strip(draw, strip_x0, strip_y, n_chambers=5, ch_w=28, ch_h=28,
                   filled_until_x=fill_x)

    # Pawl is bed-mounted at the vial X, pushes through the chamber over the
    # vial during DISPENSE
    pawl_x = STAGE.vial_cx
    pawl_top_y = strip_y - 24
    pawl_dy = 0
    if phase == "DISPENSE":
        pawl_dy = int(20 * math.sin(p * math.pi))
    draw.rectangle([(pawl_x - 4, pawl_top_y - 8 + pawl_dy),
                    (pawl_x + 4, pawl_top_y + 8 + pawl_dy)],
                   fill=ACCENT)
    draw.line([(pawl_x, STAGE.gantry_bot_y + 18),
               (pawl_x, pawl_top_y - 8 + pawl_dy)],
              fill=ACCENT, width=2)
    draw.text((pawl_x + 8, pawl_top_y - 14), "bed pawl", fill=MUTED, font=F_SMALL)

    draw_vial(draw, fill_frac=fill_frac_for(phase, p))
    if phase == "DISPENSE":
        draw_falling_stream(draw, x_center=pawl_x, x_spread=4,
                            y_top=strip_y + 28, y_bottom=STAGE.vial_top_y,
                            n=5, t=p, seed=11)
    draw_title(draw, "B — Pez chamber strip", phase,
               {"LOAD": "hopper fills chambers via strike-off",
                "APPROACH": "strip indexes one chamber to vial",
                "DISPENSE": "bed pawl punches dose into vial",
                "SETTLE": "advance for next dose"}[phase])
    return img


def render_C(t_norm: float) -> Image.Image:
    """C — Capillary dip + fixed wiper."""
    phase, p = shared_phase(t_norm)
    img, draw = _new_frame()

    source_x = 130
    head_x = _gantry_x(phase, p, source_x)
    draw_gantry_rail(draw, head_x)
    draw_bed_line(draw)
    draw_powder_pad(draw, cx=source_x, half_w=50, label="source pad")

    # Fixed wiper between pad and vial
    wiper_x = (source_x + STAGE.vial_cx) // 2
    draw.rectangle([(wiper_x - 4, STAGE.bed_y - 80), (wiper_x + 4, STAGE.bed_y - 30)],
                   fill=ANVIL)
    draw.text((wiper_x + 6, STAGE.bed_y - 86), "wiper", fill=MUTED, font=F_SMALL)

    # Capillary tip Y trajectory tied to phase
    if phase == "LOAD":
        # plunge into pad
        tip_y_bot = STAGE.bed_y - 24 + int(20 * p)
        load_frac = p
        plug = False
    elif phase == "APPROACH":
        # retract through wiper while traversing
        tip_y_bot = STAGE.bed_y - 4 - int(70 * p)
        load_frac = 0
        plug = True
    elif phase == "DISPENSE":
        # plunge over vial → eject
        tip_y_bot = STAGE.vial_top_y - 8 + int(8 * math.sin(p * math.pi))
        load_frac = 0
        plug = p < 0.3
    else:  # SETTLE
        tip_y_bot = STAGE.vial_top_y - 30
        load_frac = 0
        plug = False

    draw_capillary(draw, tip_cx=head_x, tip_y_bot=tip_y_bot,
                   shank_top_y=STAGE.gantry_bot_y + 18,
                   tip_w=8, tip_h=24,
                   load_frac=load_frac, plug_loaded=plug)
    draw_vial(draw, fill_frac=fill_frac_for(phase, p))
    if phase == "DISPENSE" and not plug:
        draw_falling_stream(draw, x_center=head_x, x_spread=3,
                            y_top=tip_y_bot, y_bottom=STAGE.vial_top_y,
                            n=4, t=p, seed=21)
    draw_title(draw, "C — Capillary dip + wiper", phase,
               {"LOAD": "capillary plunges into pad",
                "APPROACH": "retract through wiper to vial",
                "DISPENSE": "plunger ejects volumetric plug",
                "SETTLE": "retract"}[phase])
    return img


def render_D(t_norm: float) -> Image.Image:
    """D — Brush disc + fixed comb knock-off."""
    phase, p = shared_phase(t_norm)
    img, draw = _new_frame()

    source_x = 130
    head_x = _gantry_x(phase, p, source_x)
    draw_gantry_rail(draw, head_x)
    draw_bed_line(draw)
    draw_powder_pad(draw, cx=source_x, half_w=55, label="source pad")

    comb_cx, comb_top = draw_comb(draw, STAGE.vial_cx)

    # Disc Y depends on phase
    if phase == "LOAD":
        disc_cy = STAGE.bed_y - 14
        laden = p
    elif phase == "APPROACH":
        disc_cy = STAGE.bed_y - 14 - int(40 * math.sin(p * math.pi))
        laden = 1.0
    elif phase == "DISPENSE":
        disc_cy = comb_top - 4
        laden = max(0.0, 1.0 - p)
    else:
        disc_cy = comb_top - 60 - int(20 * p)
        laden = 0.0

    draw_brush_disc(draw, cx=head_x, cy=disc_cy, radius=16,
                    laden_frac=laden, seed=99)
    draw_vial(draw, fill_frac=fill_frac_for(phase, p))
    if phase == "DISPENSE":
        draw_falling_stream(draw, x_center=comb_cx, x_spread=6,
                            y_top=STAGE.bed_y, y_bottom=STAGE.vial_top_y,
                            n=6, t=p, seed=33)
    draw_title(draw, "D — Brush + fixed comb", phase,
               {"LOAD": "disc sweeps powder pad",
                "APPROACH": "translate to comb",
                "DISPENSE": "comb scrapes laden bristles",
                "SETTLE": "retract"}[phase])
    return img


def render_E(t_norm: float) -> Image.Image:
    """E — Salt-shaker oscillation over a multi-hole floor."""
    phase, p = shared_phase(t_norm)
    img, draw = _new_frame()

    source_x = STAGE.vial_cx  # source cup is the dispenser; load happens off-screen
    head_x = _gantry_x(phase, p, source_x)
    draw_gantry_rail(draw, head_x)
    draw_bed_line(draw)

    # During DISPENSE, the head jitters X so the cup oscillates
    jx = 0
    if phase == "DISPENSE":
        jx = int(8 * math.sin(p * math.pi * 8))
    cup_w, cup_h = 80, 78
    cup_top_y = _gantry_y_for_cup(phase, p, cup_h=cup_h, hover_above_vial=20)
    pile_frac = 1.0 if phase in ("LOAD", "APPROACH") else max(
        0.3, 1.0 - 0.6 * (p if phase == "DISPENSE" else 1.0))
    mesh_cx, mesh_y = draw_cup_with_mesh(
        draw, head_x, cup_top_y, w=cup_w, h=cup_h, pile_frac=pile_frac,
        jitter=(jx, 0), seed=2)
    # extra holes shown in mesh
    for i in range(mesh_cx - cup_w // 2 + 14, mesh_cx + cup_w // 2 - 8, 9):
        draw.ellipse([(i, mesh_y - 2), (i + 4, mesh_y + 2)], fill=BG)
    if phase == "DISPENSE":
        # double-headed arrows for X oscillation
        for sx, dx in ((mesh_cx - cup_w // 2 - 18, -8),
                       (mesh_cx + cup_w // 2 + 18, 8)):
            draw.line([(sx, cup_top_y + cup_h // 2),
                       (sx + dx, cup_top_y + cup_h // 2)],
                      fill=ACCENT, width=2)
        draw_falling_stream(draw, x_center=mesh_cx, x_spread=cup_w // 2 - 12,
                            y_top=mesh_y + 2, y_bottom=STAGE.vial_top_y,
                            n=12, t=p * 4, seed=44)
    draw_vial(draw, fill_frac=fill_frac_for(phase, p))
    draw_title(draw, "E — Salt-shaker oscillation", phase,
               {"LOAD": "powder pre-loaded in cup",
                "APPROACH": "lower over vial",
                "DISPENSE": "X-Y shake — leak through holes",
                "SETTLE": "stop on target mass"}[phase])
    return img


def render_F(t_norm: float) -> Image.Image:
    """F — Passive auger driven by a bed-mounted rack & pinion."""
    phase, p = shared_phase(t_norm)
    img, draw = _new_frame()

    source_x = 130
    head_x = _gantry_x(phase, p, source_x)
    draw_gantry_rail(draw, head_x)
    draw_bed_line(draw)

    # Rack on the bed, near the vial
    rack_y = STAGE.bed_y - 60
    rack_x0 = STAGE.vial_cx - 90
    rack_x1 = STAGE.vial_cx + 60
    draw_rack(draw, rack_x0, rack_x1, rack_y)
    draw.text((rack_x0 + 4, rack_y + 16), "fixed bed-rack",
              fill=MUTED, font=F_SMALL)

    # Auger module hanging off the gantry head; aux pinion meshes during APPROACH/DISPENSE
    rot_deg = 0.0
    if phase == "APPROACH":
        rot_deg = 180 * p
    elif phase == "DISPENSE":
        rot_deg = 540 * p

    tube_top_y = STAGE.gantry_bot_y + 18
    draw_hopper(draw, head_x, tube_top_y - 30, top_w=46, bot_w=20, h=24,
                n_grains=18, seed=8)
    outlet_cx, outlet_y = draw_auger(draw, cx=head_x, top_y=tube_top_y,
                                     tube_w=30, tube_h=130, rot_deg=rot_deg)
    draw_pinion(draw, cx=head_x + 22, cy=tube_top_y + 8,
                radius=10, rot_deg=rot_deg)
    if phase == "DISPENSE":
        draw_falling_stream(draw, x_center=outlet_cx, x_spread=4,
                            y_top=outlet_y, y_bottom=STAGE.vial_top_y,
                            n=5, t=p * 2, seed=55)
    draw_vial(draw, fill_frac=fill_frac_for(phase, p))
    draw_title(draw, "F — Passive auger (rack & pinion)", phase,
               {"LOAD": "hopper pre-charged",
                "APPROACH": "pinion meshes with bed-rack",
                "DISPENSE": "auger turns → quantized dose",
                "SETTLE": "retract"}[phase])
    return img


def render_G(t_norm: float) -> Image.Image:
    """G — ERM-augmented sieve (continuous bounded vibration). Top pick."""
    phase, p = shared_phase(t_norm)
    img, draw = _new_frame()

    source_x = STAGE.vial_cx
    head_x = _gantry_x(phase, p, source_x)
    draw_gantry_rail(draw, head_x)
    draw_bed_line(draw)

    cup_w, cup_h = 80, 84
    cup_top_y = _gantry_y_for_cup(phase, p, cup_h=cup_h, hover_above_vial=24)
    erm_active = phase == "DISPENSE"
    jx, jy = 0, 0
    if erm_active:
        jx = int(2 * math.sin(p * math.pi * 30))
        jy = int(2 * math.cos(p * math.pi * 30))

    pile_frac = 1.0 if phase in ("LOAD", "APPROACH") else max(
        0.3, 1.0 - 0.6 * (p if phase == "DISPENSE" else 1.0))
    mesh_cx, mesh_y = draw_cup_with_mesh(
        draw, head_x, cup_top_y, w=cup_w, h=cup_h, pile_frac=pile_frac,
        jitter=(jx, jy), seed=4)
    erm_cx = mesh_cx + cup_w // 2 + 12
    erm_cy = cup_top_y + cup_h // 2 + jy
    draw_erm_motor(draw, cx=erm_cx, cy=erm_cy, active=erm_active,
                   t_anim=p if erm_active else 0.0)
    if erm_active:
        draw_falling_stream(draw, x_center=mesh_cx, x_spread=cup_w // 2 - 14,
                            y_top=mesh_y + 2, y_bottom=STAGE.vial_top_y,
                            n=20, t=p * 6, seed=66)
    draw_vial(draw, fill_frac=fill_frac_for(phase, p))
    draw_title(draw, "G — ERM-augmented sieve (top pick)", phase,
               {"LOAD": "powder + ERM seated in cup",
                "APPROACH": "lower over vial",
                "DISPENSE": "ERM ON — bounded continuous flow",
                "SETTLE": "ERM OFF on target mass"}[phase])
    return img


def render_H(t_norm: float) -> Image.Image:
    """H — Solenoid-tapped sieve, closed-loop with a balance."""
    phase, p = shared_phase(t_norm)
    img, draw = _new_frame()

    source_x = STAGE.vial_cx
    head_x = _gantry_x(phase, p, source_x)
    draw_gantry_rail(draw, head_x)
    draw_bed_line(draw)

    cup_w, cup_h = 80, 80
    cup_top_y = _gantry_y_for_cup(phase, p, cup_h=cup_h, hover_above_vial=22)
    # During DISPENSE, the solenoid pulses and nudges the cup right
    extend = 0
    cup_kick = 0
    if phase == "DISPENSE":
        pulse = max(0.0, math.sin(p * math.pi * 12))
        extend = int(8 * pulse)
        cup_kick = int(3 * pulse)
    pile_frac = 1.0 if phase in ("LOAD", "APPROACH") else max(
        0.4, 1.0 - 0.5 * (p if phase == "DISPENSE" else 1.0))
    mesh_cx, mesh_y = draw_cup_with_mesh(
        draw, head_x + cup_kick, cup_top_y, w=cup_w, h=cup_h,
        pile_frac=pile_frac, seed=6)

    # Solenoid bracket fixed to the gantry head (left side of cup)
    sol_cx = head_x - cup_w // 2 - 12
    sol_cy = cup_top_y + cup_h // 2
    draw_solenoid_actuator(draw, cx=sol_cx, cy=sol_cy, extend=extend)

    fill = fill_frac_for(phase, p)
    target_mg = 5.0
    mass_mg = fill * target_mg / 0.59
    draw_vial(draw, fill_frac=fill)
    draw_balance(draw, mass_mg=mass_mg, target_mg=target_mg,
                 hit_target=phase == "SETTLE")
    if phase == "DISPENSE" and extend > 4:
        draw_falling_stream(draw, x_center=mesh_cx, x_spread=cup_w // 2 - 12,
                            y_top=mesh_y + 2, y_bottom=STAGE.vial_top_y,
                            n=8, t=p * 6, seed=77)
    draw_title(draw, "H — Solenoid sieve (closed loop)", phase,
               {"LOAD": "powder + balance tare",
                "APPROACH": "lower over balance + vial",
                "DISPENSE": "solenoid pulses; balance feedback",
                "SETTLE": "hit target → stop"}[phase])
    return img


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

CONCEPTS: List[Tuple[str, str, Callable[[float], Image.Image]]] = [
    ("A", "tap-sieve", render_A),
    ("B", "pez-strip", render_B),
    ("C", "capillary-wiper", render_C),
    ("D", "brush-comb", render_D),
    ("E", "shaker", render_E),
    ("F", "passive-auger", render_F),
    ("G", "erm-sieve", render_G),
    ("H", "solenoid-sieve", render_H),
]


def _save_animation(frames: List[Image.Image], path: Path,
                    optimize: bool = False) -> None:
    """Save a frame list as a GIF.

    ``optimize`` is **off by default** because Pillow's GIF optimizer drops
    visually-identical frames, which would desync the per-concept GIFs (each
    concept has a different number of "interesting" frames) and break the
    composite tile, which seeks frame index N across all eight per-concept
    GIFs and expects them to be in the same phase at the same index.
    """
    palettised = []
    for fr in frames:
        bg = Image.new("RGBA", fr.size, (255, 255, 255, 255))
        bg.alpha_composite(fr.convert("RGBA"))
        palettised.append(bg.convert("P", palette=Image.ADAPTIVE, colors=255))
    palettised[0].save(
        path, save_all=True, append_images=palettised[1:],
        duration=int(1000 / FPS), loop=0, optimize=optimize, disposal=2,
    )


def _make_composite(out_path: Path) -> None:
    """Build the 4×2 composite frame-by-frame **directly from render fns**.

    This bypasses any GIF de-duplication / frame-dropping that would
    otherwise desync the per-concept seek positions, guaranteeing that
    every tile of the composite is rendered at the same ``t_norm`` and
    therefore in the same shared phase (LOAD / APPROACH / DISPENSE /
    SETTLE) as every other tile.
    """
    cols, rows = 4, 2
    sub_w, sub_h = W // 2, H // 2
    cw, ch = sub_w * cols, sub_h * rows
    composite_frames: List[Image.Image] = []
    for fi in range(N_FRAMES):
        t_norm = fi / N_FRAMES
        canvas = Image.new("RGBA", (cw, ch), (255, 255, 255, 255))
        for idx, (_, _, fn) in enumerate(CONCEPTS):
            sub = fn(t_norm).resize((sub_w, sub_h), Image.LANCZOS)
            r, c = divmod(idx, cols)
            canvas.paste(sub, (c * sub_w, r * sub_h), sub)
        composite_frames.append(canvas)
    _save_animation(composite_frames, out_path)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for letter, slug, fn in CONCEPTS:
        frames = []
        for fi in range(N_FRAMES):
            t_norm = fi / N_FRAMES
            frames.append(fn(t_norm))
        out = OUT_DIR / f"{letter}-{slug}-animation.gif"
        _save_animation(frames, out)
        print(f"  wrote {out.relative_to(REPO)}")

    composite = OUT_DIR / "composite-animation.gif"
    _make_composite(composite)
    print(f"  wrote {composite.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
