#!/usr/bin/env python3
"""
annotate_alternatives.py — turn the per-concept iso / cutaway renders in
``cad/alternatives/`` into self-explanatory panels.

For every concept A–H this script composes a single PNG that contains:

* a title bar with the concept letter, name, and one-line tagline
* the iso render and the half-cutaway render side-by-side, captioned
* a numbered parts list (what each labelled part is) and a 3-step
  operation cycle (what *happens* when the gantry runs the part)

It then stitches the eight panels together into a single tall composite
PNG (``composite-panel.png``) so a reader can scan all eight refined
alternatives without opening separate files.

Pure Pillow — no OpenSCAD or external rendering required; relies on the
existing iso/cutaway PNGs already produced by ``render_alternatives.py``.
"""

from __future__ import annotations

import sys
from pathlib import Path
from textwrap import wrap

from PIL import Image, ImageDraw, ImageFont

REPO = Path(__file__).resolve().parent.parent
ALT_DIR = REPO / "cad" / "alternatives"

# ---------------------------------------------------------------------------
# Per-concept content
# ---------------------------------------------------------------------------

CONCEPTS = [
    {
        "letter": "A",
        "slug": "tap-sieve",
        "name": "Tap-driven sieve cup (passive)",
        "tagline": (
            "Gantry pecks the cup down onto a fixed bed-anvil; each impact "
            "kicks ~mg of powder through the bottom mesh."
        ),
        "parts": [
            "Spindle-clamp boss (Ø43 mm, wrench-flats for the 3018-Pro V2)",
            "Powder reservoir",
            "Anti-bridging cone above the mesh",
            "Mesh window (swappable polyester / stainless disc)",
            "Strike pad on the cup rim (impacts the anvil)",
        ],
        "cycle": [
            "Lower cup until strike pad meets a fixed printed bed-anvil.",
            "Impact pulse dislodges sub-10 mg of powder through the mesh.",
            "Retract; repeat tap count until target mass is reached.",
        ],
    },
    {
        "letter": "B",
        "slug": "pez-strip",
        "name": "Pez-style chamber strip (single-use volumetric)",
        "tagline": (
            "Pre-loaded linear cartridge of small chambers; a fixed bed "
            "pawl punches each one as the gantry steps the strip."
        ),
        "parts": [
            "Loading slot (top, pre-filled then struck off)",
            "Indexed chamber array (~5 mm³ each, 10 chambers in series)",
            "Exit ports on the chamber floors",
            "Strike-off lip (defines the dose volume)",
            "Bed-mounted advance pawl (separate trivial part)",
        ],
        "cycle": [
            "Slot-fill all chambers, slide under a fixed knife to strike off.",
            "Gantry steps the strip one pitch under a fixed bed pawl.",
            "Pawl punches the chamber's plug down through its exit port.",
        ],
    },
    {
        "letter": "C",
        "slug": "capillary-wiper",
        "name": "Capillary dip + fixed wiper",
        "tagline": (
            "A printable mini-SWILE: hollow tip dips into the powder bed, "
            "fixed wiper strikes off the excess on retract."
        ),
        "parts": [
            "Spindle-mount shank",
            "Hollow capillary tip (Ø1–2 mm bore)",
            "Internal printed plunger (ejects plug at the target)",
            "Bed-mounted wiper bar (strikes off the excess)",
            "Source powder bed (separate, on the 3018 bed)",
        ],
        "cycle": [
            "Gantry plunges the tip into the powder bed; cohesive fines pack in.",
            "Retract through the fixed bed wiper bar → excess is sheared off.",
            "Position over the vial; tap or plunge to eject the powder plug.",
        ],
    },
    {
        "letter": "D",
        "slug": "brush-comb",
        "name": "Brush / swab pickup + fixed comb knock-off",
        "tagline": (
            "A printed bristle disc picks up cohesive powder; a fixed bed "
            "comb scrapes the catch off into the receiving vial."
        ),
        "parts": [
            "Spindle-mount disc carrier",
            "Printed bristle ring (Ø0.6 mm pins, PETG/TPU)",
            "Bed-mounted comb teeth (separate part on the 3018 bed)",
            "Powder source pad (separate; on the bed)",
            "Receiving vial (directly below the comb)",
        ],
        "cycle": [
            "Sweep the disc across the powder source — fines adhere to bristles.",
            "Translate over the fixed comb → teeth scrape powder off bristles.",
            "Powder falls through the comb into the vial below.",
        ],
    },
    {
        "letter": "E",
        "slug": "shaker",
        "name": "Salt-shaker oscillation",
        "tagline": (
            "Multi-hole floor instead of a fine mesh; gantry shakes the cup "
            "in X-Y over the vial — rate ∝ amplitude × hole pattern."
        ),
        "parts": [
            "Spindle-clamp boss",
            "Powder reservoir",
            "Patterned multi-hole floor (Ø1–2 mm holes on a grid)",
            "Anti-bridging cone above the floor",
            "Receiving vial directly below",
        ],
        "cycle": [
            "Lower cup over the vial; gantry oscillates X-Y at ~5–20 Hz.",
            "Powder leaks through the holes at a rate set by amplitude.",
            "Stop oscillation once the balance reads the target mass.",
        ],
    },
    {
        "letter": "F",
        "slug": "passive-auger",
        "name": "Passive auger (rack-and-pinion, no motor)",
        "tagline": (
            "Lateral gantry motion drives a pinion against a fixed bed "
            "rack — the spindle never has to spin."
        ),
        "parts": [
            "Vertical Archimedes auger inside an outer tube",
            "Top pinion keyed to the auger shaft",
            "Outer tube + bottom outlet over the vial",
            "Fixed bed-mounted rack (separate part on the 3018 bed)",
            "Powder reservoir feeding the auger from above",
        ],
        "cycle": [
            "Gantry rapids horizontally → pinion meshes with the bed rack.",
            "Pinion rotates the auger; flighting pushes a fixed volume down.",
            "Each pinion-tooth pitch = one quantized dose into the vial.",
        ],
    },
    {
        "letter": "G",
        "slug": "erm-sieve",
        "name": "ERM-augmented sieve (top pick, Edison-revised)",
        "tagline": (
            "Continuous bounded vibration from a $2 coin ERM matches the "
            "Besenhard-2015 vibratory-sieve-chute regime."
        ),
        "parts": [
            "Spindle-clamp boss",
            "Powder reservoir + anti-bridging cone",
            "Mesh window in the floor",
            "Coin-ERM motor pocket (Ø10 mm, in the wall)",
            "CR2032 battery pocket + wire-relief slot",
        ],
        "cycle": [
            "Lower the cup so the mesh sits a few mm above the vial.",
            "Energize the ERM — continuous mg-scale flow through the mesh.",
            "Cut power once the balance reads the target mass.",
        ],
    },
    {
        "letter": "H",
        "slug": "solenoid-sieve",
        "name": "Solenoid-tapped sieve (closed-loop with balance)",
        "tagline": (
            "Concept A's cup, but a 5 V solenoid + microcontroller fires "
            "tap pulses against a balance reading until target is hit."
        ),
        "parts": [
            "Sieve cup (geometry shared with concept A)",
            "Side L-bracket clipped onto the cup wall",
            "5 V push-pull solenoid (10 × 20 mm)",
            "Solenoid strike anvil on the cup wall",
            "Off-board 0.1 mg balance + microcontroller (not modelled)",
        ],
        "cycle": [
            "Lower the cup over a vial sitting on a 0.1 mg balance.",
            "Microcontroller fires the solenoid → impulse on the cup wall.",
            "Repeat with adaptive pulse rate until the balance reads target.",
        ],
    },
]


# ---------------------------------------------------------------------------
# Drawing helpers
# ---------------------------------------------------------------------------

# Layout (px). Each panel: title (60) + view row (480) + caption block (260)
PANEL_W = 1100
PANEL_H = 800
VIEW_W = 480
VIEW_H = 480
TITLE_H = 60
GUTTER = 20
MARGIN = 20

# Brand-ish colours
BG = (250, 250, 252)
TITLE_BG = (32, 56, 92)
TITLE_FG = (255, 255, 255)
TEXT = (24, 24, 28)
MUTED = (90, 95, 110)
ACCENT = (0, 110, 200)
RULE = (210, 215, 225)


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
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


def _wrap(draw: ImageDraw.ImageDraw, text: str, font, max_w: int) -> list[str]:
    """Greedy width-aware wrap that respects font metrics."""
    words = text.split()
    lines: list[str] = []
    cur = ""
    for w in words:
        trial = (cur + " " + w).strip()
        if draw.textlength(trial, font=font) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def _draw_view(panel: Image.Image, src: Path, x: int, y: int, label: str) -> None:
    """Paste an image into a fixed VIEW_W × VIEW_H slot with a caption strip."""
    draw = ImageDraw.Draw(panel)
    # background card
    draw.rectangle([x, y, x + VIEW_W, y + VIEW_H + 28], outline=RULE, width=1)
    if src.exists():
        img = Image.open(src).convert("RGB")
        img.thumbnail((VIEW_W - 4, VIEW_H - 4), Image.LANCZOS)
        ix = x + (VIEW_W - img.width) // 2
        iy = y + (VIEW_H - img.height) // 2
        panel.paste(img, (ix, iy))
    else:
        f = _font(20)
        draw.text(
            (x + VIEW_W // 2 - 80, y + VIEW_H // 2),
            f"missing: {src.name}",
            fill=(180, 80, 80),
            font=f,
        )
    cap_font = _font(16, bold=True)
    tw = draw.textlength(label, font=cap_font)
    draw.text(
        (x + (VIEW_W - tw) // 2, y + VIEW_H + 5),
        label,
        fill=MUTED,
        font=cap_font,
    )


def _build_panel(concept: dict) -> Image.Image:
    panel = Image.new("RGB", (PANEL_W, PANEL_H), BG)
    draw = ImageDraw.Draw(panel)

    # --- Title bar ---------------------------------------------------------
    draw.rectangle([0, 0, PANEL_W, TITLE_H], fill=TITLE_BG)
    letter_font = _font(36, bold=True)
    name_font = _font(22, bold=True)
    tag_font = _font(15)
    draw.text((MARGIN, 10), concept["letter"], fill=TITLE_FG, font=letter_font)
    draw.text(
        (MARGIN + 50, 6),
        concept["name"],
        fill=TITLE_FG,
        font=name_font,
    )
    # Tagline below the name on the title bar
    tag_lines = _wrap(draw, concept["tagline"], tag_font, PANEL_W - MARGIN - 60)
    draw.text(
        (MARGIN + 50, 33),
        tag_lines[0] if tag_lines else "",
        fill=(210, 220, 235),
        font=tag_font,
    )

    # --- Views (iso | cutaway) --------------------------------------------
    iso = ALT_DIR / f"{concept['letter']}-{concept['slug']}-iso.png"
    cut = ALT_DIR / f"{concept['letter']}-{concept['slug']}-cutaway.png"
    view_y = TITLE_H + GUTTER
    _draw_view(panel, iso, MARGIN, view_y, "ISO VIEW")
    _draw_view(
        panel, cut, MARGIN + VIEW_W + GUTTER, view_y, "HALF CROSS-SECTION"
    )

    # --- Caption block (parts list + operation cycle) ---------------------
    caption_y = view_y + VIEW_H + 28 + GUTTER
    head_font = _font(16, bold=True)
    body_font = _font(15)
    col_w = (PANEL_W - 2 * MARGIN - GUTTER) // 2

    # Left col: numbered parts list
    draw.text((MARGIN, caption_y), "KEY PARTS", fill=ACCENT, font=head_font)
    y = caption_y + 22
    for i, part in enumerate(concept["parts"], 1):
        bullet = f"{i}.  "
        bullet_w = draw.textlength(bullet, font=body_font)
        draw.text((MARGIN, y), bullet, fill=TEXT, font=body_font)
        for line in _wrap(draw, part, body_font, col_w - int(bullet_w) - 4):
            draw.text((MARGIN + int(bullet_w), y), line, fill=TEXT, font=body_font)
            y += 20

    # Right col: operation cycle
    rx = MARGIN + col_w + GUTTER
    draw.text(
        (rx, caption_y),
        "OPERATION CYCLE",
        fill=ACCENT,
        font=head_font,
    )
    y = caption_y + 22
    for i, step in enumerate(concept["cycle"], 1):
        bullet = f"{i}.  "
        bullet_w = draw.textlength(bullet, font=body_font)
        draw.text((rx, y), bullet, fill=TEXT, font=body_font)
        for line in _wrap(draw, step, body_font, col_w - int(bullet_w) - 4):
            draw.text((rx + int(bullet_w), y), line, fill=TEXT, font=body_font)
            y += 20
        y += 4  # extra spacing between cycle steps

    # Bottom rule
    draw.line([(0, PANEL_H - 1), (PANEL_W, PANEL_H - 1)], fill=RULE)
    return panel


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

def main() -> int:
    panels: list[Image.Image] = []
    for concept in CONCEPTS:
        panel = _build_panel(concept)
        out = ALT_DIR / f"{concept['letter']}-{concept['slug']}-panel.png"
        panel.save(out, optimize=True)
        panels.append(panel)
        print(f"wrote {out.relative_to(REPO)}")

    # Composite: 2 columns × 4 rows
    cols, rows = 2, 4
    cw, ch = PANEL_W, PANEL_H
    composite = Image.new("RGB", (cw * cols, ch * rows), BG)
    for idx, p in enumerate(panels):
        r, c = divmod(idx, cols)
        composite.paste(p, (c * cw, r * ch))

    # The 2200×3200 raw composite is too big for a comment; downscale to
    # 1600 px wide and save both. Inline-friendly composite is what we
    # embed in the reply; full-res is kept for reference.
    full = ALT_DIR / "composite-panel-full.png"
    composite.save(full, optimize=True)
    print(f"wrote {full.relative_to(REPO)} ({composite.size[0]}×{composite.size[1]})")

    inline_w = 1600
    inline_h = int(composite.size[1] * inline_w / composite.size[0])
    inline = composite.resize((inline_w, inline_h), Image.LANCZOS)
    inline_out = ALT_DIR / "composite-panel.png"
    inline.save(inline_out, optimize=True)
    print(f"wrote {inline_out.relative_to(REPO)} ({inline.size[0]}×{inline.size[1]})")

    return 0


if __name__ == "__main__":
    sys.exit(main())
