"""
Generate the four design subpanels and the mechanism animation for the
powder-excavator, in the **corrected longitudinal-pivot / sideways-tilt**
geometry that incorporates the Edison Scientific design-review feedback
(see ``docs/edison/analysis-v2-corrected-gondola.md``).

Outputs (all under ``docs/figures/``):

* ``panel-A-orthographic.svg``  -- end / side / top views, dimensions
* ``panel-B-pivot-detail.svg``  -- close-up of one end-cap pivot boss + pin
* ``panel-C-isometric.svg``     -- 3D / isometric of the assembly on a gantry
* ``panel-D-mechanism.svg``     -- 4-step mechanism (J-plunge -> strike-off
                                   -> transport -> sideways tilt against cam)
* ``panel-E-pin-slot.svg``      -- pin-defined-path actuation variant: peg on
                                   stem rides in a routed slot in a fixed
                                   external board; slot path = tilt schedule
* ``mechanism.gif``             -- animation of the cam-engagement + sideways
                                   tilt step

The script is intentionally a single, self-contained file so the figure set
can be regenerated with one command after geometry tweaks::

    python scripts/generate_figures.py

It depends only on the Python standard library, ``cairosvg``, and ``Pillow``;
``cairosvg`` is used purely to rasterise the per-frame SVGs of the animation
into PNG bytes that ``Pillow`` then concatenates into an animated GIF.
"""

from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_FIG_DIR = REPO_ROOT / "docs" / "figures"
# Module-level handle that ``main`` rebinds when ``--output-dir`` is given;
# kept so ``render_gif`` (which doesn't take an argument) writes to the same
# directory as the panels.
FIG_DIR = DEFAULT_FIG_DIR

# ---------------------------------------------------------------------------
# Shared SVG building blocks
# ---------------------------------------------------------------------------

SVG_DEFS = """\
  <defs>
    <linearGradient id="metal" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0"   stop-color="#dfe4ea"/>
      <stop offset="0.5" stop-color="#aab2bd"/>
      <stop offset="1"   stop-color="#7e8794"/>
    </linearGradient>
    <linearGradient id="metalH" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0"   stop-color="#dfe4ea"/>
      <stop offset="0.5" stop-color="#aab2bd"/>
      <stop offset="1"   stop-color="#7e8794"/>
    </linearGradient>
    <pattern id="powder" width="6" height="6" patternUnits="userSpaceOnUse">
      <rect width="6" height="6" fill="#e8d9a8"/>
      <circle cx="1.5" cy="1.5" r="0.6" fill="#b89a55"/>
      <circle cx="4"   cy="3.5" r="0.6" fill="#b89a55"/>
      <circle cx="2"   cy="5"   r="0.5" fill="#b89a55"/>
    </pattern>
    <marker id="arrowK" viewBox="0 0 10 10" refX="9" refY="5"
            markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M0,0 L10,5 L0,10 z" fill="#222"/>
    </marker>
    <marker id="arrowB" viewBox="0 0 10 10" refX="9" refY="5"
            markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M0,0 L10,5 L0,10 z" fill="#1f5fbf"/>
    </marker>
    <marker id="arrowR" viewBox="0 0 10 10" refX="9" refY="5"
            markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M0,0 L10,5 L0,10 z" fill="#c0392b"/>
    </marker>
  </defs>
"""


def _svg_open(width: int, height: int, font_size: int = 13) -> str:
    return (
        f'<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'font-family="Helvetica, Arial, sans-serif" font-size="{font_size}">\n'
        f"{SVG_DEFS}"
    )


def _svg_close() -> str:
    return "</svg>\n"


# ---------------------------------------------------------------------------
# Trough cross-section primitive
# ---------------------------------------------------------------------------
#
# The trough cross-section (looking along its long axis L) is a half-cylinder
# with a continuous chamfered lip on the OUTSIDE of each long-side rim.  The
# lips run the full trough length L (this primitive shows their cross-section
# only); a localised "spout" is deliberately avoided because it would
# reintroduce a powder-arching bottleneck at the pour edge (Edison v2 §3).
# The chamfer (a) detaches the powder stream cleanly, (b) defines a sharp
# geometric tip-over angle, and (c) doubles as the cam-engagement surface
# when the trough rolls about its longitudinal pivot pin.

def trough_cross_section(
    cx: float,
    cy: float,
    radius: float,
    rotate_deg: float = 0.0,
    powder_fill_frac: float = 1.0,
    *,
    bumper: bool = True,
) -> str:
    """Return SVG for the trough cross-section, rolled by ``rotate_deg`` about
    its central pivot axis.

    The semicircle's flat (open) edge runs across the top when ``rotate_deg=0``;
    positive ``rotate_deg`` rolls the trough so its right rim drops (pouring
    direction).  When ``bumper`` is true, a chamfered lip is drawn on EACH
    long-side rim (left and right) — the trough is symmetric, so either rim
    can be the pour edge / cam-engagement surface depending on roll direction.
    """
    r = radius
    shell = (
        f'M {-r} 0 L {r} 0 '
        f'A {r} {r} 0 0 1 {-r} 0 Z'
    )
    fill_h = r * powder_fill_frac
    powder_path = (
        f'M {-r * 0.985} {r - fill_h} L {r * 0.985} {r - fill_h} '
        f'A {r * 0.985} {r * 0.985} 0 0 1 {-r * 0.985} {r - fill_h} Z'
    )
    parts = [
        f'<g transform="translate({cx},{cy}) rotate({rotate_deg})">',
        f'  <path d="{shell}" fill="url(#metal)" stroke="#222" stroke-width="2"/>',
        f'  <path d="{powder_path}" fill="url(#powder)" opacity="0.95"/>',
    ]
    if bumper:
        # Continuous chamfered lip on each long-side rim.  The lip extends
        # OUTWARD (away from the trough centre line) and UPWARD, with a
        # chamfer on its outside-upper corner — this is the surface that
        # both rides the cam ramp and detaches the powder stream cleanly
        # at the pour edge.  Drawn symmetrically on both rims because the
        # trough is symmetric and may dump in either direction.
        parts.append(
            # right rim lip
            f'  <path d="M {r} 0 L {r + 6} -2 L {r + 6} 4 L {r} 6 Z" '
            f'fill="#7e8794" stroke="#222" stroke-width="1.2"/>'
        )
        parts.append(
            # left rim lip (mirror of the right)
            f'  <path d="M {-r} 0 L {-(r + 6)} -2 L {-(r + 6)} 4 L {-r} 6 Z" '
            f'fill="#7e8794" stroke="#222" stroke-width="1.2"/>'
        )
    parts.append("</g>")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Panel A — Orthographic
# ---------------------------------------------------------------------------

def panel_A() -> str:
    W, H = 1200, 720
    s = [_svg_open(W, H)]
    s.append(
        f'<text x="{W//2}" y="34" text-anchor="middle" font-size="22" font-weight="700">'
        "Subpanel A — Orthographic views (end, side, top)</text>"
    )
    s.append(
        f'<text x="{W//2}" y="56" text-anchor="middle" font-size="13" fill="#555" font-style="italic">'
        "longitudinal pivot axis along L; arms grip the two short end caps; trough rolls SIDEWAYS to pour</text>"
    )

    # End view (looking down the long axis L) — leftmost.
    # Looking down L, both arms project to the same X; we draw the near arm
    # solid and a faint dashed ghost of the far arm directly behind it so the
    # viewer registers that there are *two* arms (one per end cap).
    g_end_x, g_end_y = 60, 110
    s.append(f'<g transform="translate({g_end_x},{g_end_y})">')
    s.append('<text x="160" y="0" text-anchor="middle" font-size="16" font-weight="600">End view (along L)</text>')
    s.append('<rect x="155" y="20" width="10" height="160" fill="url(#metal)" stroke="#333"/>')
    # Ghost of the far arm (hidden behind the near arm, drawn slightly offset)
    s.append('<rect x="158" y="22" width="10" height="160" fill="none" stroke="#888" '
             'stroke-width="1" stroke-dasharray="3 3"/>')
    s.append('<text x="170" y="35" font-size="11" fill="#444">arms (TWO, one per end cap;</text>')
    s.append('<text x="170" y="49" font-size="11" fill="#444">far arm shown dashed/hidden)</text>')
    R = 60
    cx, cy = 160, 180
    s.append(trough_cross_section(cx, cy, R, rotate_deg=0, powder_fill_frac=0.85))
    # Pin appears END-ON: draw as red circle with crosshair (⊕) so the viewer
    # reads it as "axis pointing into the page", not just a generic dot.
    s.append(f'<circle cx="{cx}" cy="{cy}" r="7" fill="#c0392b" stroke="#7a1f15" stroke-width="1.5"/>')
    s.append(f'<line x1="{cx - 5}" y1="{cy}" x2="{cx + 5}" y2="{cy}" stroke="#fff" stroke-width="1.4"/>')
    s.append(f'<line x1="{cx}" y1="{cy - 5}" x2="{cx}" y2="{cy + 5}" stroke="#fff" stroke-width="1.4"/>')
    s.append(f'<text x="{cx + 14}" y="{cy + 4}" font-size="11" fill="#c0392b">pivot pin (axis ⊥ page = along L)</text>')
    s.append(f'<line x1="{cx - R}" y1="{cy + R + 30}" x2="{cx + R}" y2="{cy + R + 30}" '
             'stroke="#222" stroke-width="1.2" marker-start="url(#arrowK)" marker-end="url(#arrowK)"/>')
    s.append(f'<text x="{cx}" y="{cy + R + 50}" text-anchor="middle" font-size="13">D ≈ 27 mm</text>')
    s.append('</g>')

    # Side view (looking perpendicular to L, from the long side) — middle.
    # Arms are drawn slightly OUTBOARD of the trough body (not flush with its
    # end walls) so the eye reads them as "the pin sticks out of each end cap
    # into a bushing on the arm" rather than "the arms are bolted onto the
    # end walls".  The pin is shown as a solid red line where it's exposed
    # (between body and arms) and a dashed red line for the segment hidden
    # inside the body.
    g_side_x, g_side_y = 430, 110
    s.append(f'<g transform="translate({g_side_x},{g_side_y})">')
    s.append('<text x="200" y="0" text-anchor="middle" font-size="16" font-weight="600">Side view (along pin axis)</text>')
    L_px = 280
    body_x0 = 60
    body_x1 = body_x0 + L_px
    arm_gap = 22                 # how far each arm is offset outboard of the body
    arm_h = 140
    arm_top = 20
    arm_xL = body_x0 - arm_gap
    arm_xR = body_x1 + arm_gap
    for ax in (arm_xL, arm_xR):
        s.append(f'<rect x="{ax - 6}" y="{arm_top}" width="12" height="{arm_h}" fill="url(#metal)" stroke="#333"/>')
    body_top = arm_top + arm_h - 20
    body_h = 60
    # Trough body (semicircle bottom + top edge)
    s.append(
        f'<path d="M {body_x0} {body_top} '
        f'L {body_x1} {body_top} '
        f'L {body_x1} {body_top + 10} '
        f'Q {(body_x0 + body_x1) / 2} {body_top + body_h} '
        f'{body_x0} {body_top + 10} Z" '
        f'fill="url(#metalH)" stroke="#222" stroke-width="2"/>'
    )
    # Powder fill
    s.append(
        f'<path d="M {body_x0 + 10} {body_top + 4} L {body_x1 - 10} {body_top + 4} '
        f'L {body_x1 - 10} {body_top + 12} Q {(body_x0 + body_x1) / 2} {body_top + body_h - 6} '
        f'{body_x0 + 10} {body_top + 12} Z" fill="url(#powder)" opacity="0.95"/>'
    )
    # Longitudinal pin: dashed (hidden) inside the body, solid where exposed
    pin_y = body_top + 8
    s.append(f'<line x1="{arm_xL - 8}" y1="{pin_y}" x2="{body_x0}" y2="{pin_y}" '
             'stroke="#c0392b" stroke-width="3"/>')                                          # left exposed stub
    s.append(f'<line x1="{body_x0}" y1="{pin_y}" x2="{body_x1}" y2="{pin_y}" '
             'stroke="#c0392b" stroke-width="2.2" stroke-dasharray="6 4" opacity="0.7"/>')   # hidden inside body
    s.append(f'<line x1="{body_x1}" y1="{pin_y}" x2="{arm_xR + 8}" y2="{pin_y}" '
             'stroke="#c0392b" stroke-width="3"/>')                                          # right exposed stub
    # Pin-stub indicator dots where the pin enters each arm
    for sx in (arm_xL, arm_xR):
        s.append(f'<circle cx="{sx}" cy="{pin_y}" r="4" fill="#c0392b" stroke="#7a1f15" stroke-width="1.2"/>')
    s.append(f'<text x="{(body_x0 + body_x1) / 2}" y="{pin_y - 6}" text-anchor="middle" font-size="11" fill="#c0392b">'
             'pin stubs (red dots) sit in bushings on each arm — pin axis runs ALONG L</text>')
    s.append(f'<text x="{(body_x0 + body_x1) / 2}" y="{pin_y + 26}" text-anchor="middle" font-size="10" fill="#c0392b" font-style="italic">'
             '(dashed segment = pin hidden inside trough body)</text>')
    # L-dimension (along the trough body, between end caps)
    s.append(f'<line x1="{body_x0}" y1="{body_top + body_h + 30}" x2="{body_x1}" y2="{body_top + body_h + 30}" '
             'stroke="#222" stroke-width="1.2" marker-start="url(#arrowK)" marker-end="url(#arrowK)"/>')
    s.append(f'<text x="{(body_x0 + body_x1) / 2}" y="{body_top + body_h + 50}" text-anchor="middle" font-size="13">L ≈ 3 D ≈ 80 mm</text>')
    # Continuous chamfered lip running the FULL length L on the long-side
    # rim (in this side view, only the near rim is visible; the far rim
    # carries an identical lip, since the trough is symmetric).  Drawn as
    # one continuous strip — explicitly NOT a localised spout, to avoid
    # reintroducing a powder-arching bottleneck at the pour edge.
    lip_top_y = body_top - 5
    s.append(
        f'<path d="M {body_x0} {body_top} L {body_x1} {body_top} '
        f'L {body_x1} {lip_top_y} L {body_x0} {lip_top_y} Z" '
        'fill="#7e8794" stroke="#222" stroke-width="1.2"/>'
    )
    s.append(f'<text x="{(body_x0 + body_x1) / 2}" y="{body_top - 12}" text-anchor="middle" font-size="11" fill="#444">'
             'continuous chamfered lip (full length L; both long sides) — also rides cam ramp</text>')
    # Arm labels
    s.append(f'<text x="{arm_xL - 8}" y="{arm_top - 6}" text-anchor="middle" font-size="10" fill="#444">arm L</text>')
    s.append(f'<text x="{arm_xR + 8}" y="{arm_top - 6}" text-anchor="middle" font-size="10" fill="#444">arm R</text>')
    s.append('</g>')

    # Top view — rightmost.  Pin shown as dashed red line through the body
    # with red stub circles at each arm so the longitudinal extent is
    # unambiguous.
    g_top_x, g_top_y = 880, 110
    s.append(f'<g transform="translate({g_top_x},{g_top_y})">')
    s.append('<text x="130" y="0" text-anchor="middle" font-size="16" font-weight="600">Top view</text>')
    L_top = 220
    W_top = 50
    body_x0_t = 20
    body_x1_t = body_x0_t + L_top
    arm_off = 14            # arms sit slightly outboard of body
    s.append(f'<rect x="{body_x0_t}" y="40" width="{L_top}" height="{W_top}" fill="url(#metalH)" stroke="#222" stroke-width="2"/>')
    s.append(f'<rect x="{body_x0_t + 6}" y="46" width="{L_top - 12}" height="{W_top - 12}" fill="url(#powder)" opacity="0.95"/>')
    pin_y_t = 40 + W_top / 2
    # Pin: solid stub on each side (between arm and body), dashed inside body.
    s.append(f'<line x1="{body_x0_t - arm_off - 6}" y1="{pin_y_t}" x2="{body_x0_t}" y2="{pin_y_t}" '
             'stroke="#c0392b" stroke-width="3"/>')
    s.append(f'<line x1="{body_x0_t}" y1="{pin_y_t}" x2="{body_x1_t}" y2="{pin_y_t}" '
             'stroke="#c0392b" stroke-width="2.2" stroke-dasharray="6 4" opacity="0.7"/>')
    s.append(f'<line x1="{body_x1_t}" y1="{pin_y_t}" x2="{body_x1_t + arm_off + 6}" y2="{pin_y_t}" '
             'stroke="#c0392b" stroke-width="3"/>')
    s.append(f'<text x="{body_x0_t + L_top / 2}" y="{40 + W_top + 18}" text-anchor="middle" font-size="11" fill="#c0392b">'
             'pivot pin axis (along centre line of trough length)</text>')
    # Arms shown outboard, with pin-stub dots on their inboard face
    for ax, sx in ((body_x0_t - arm_off, body_x0_t - arm_off), (body_x1_t + arm_off, body_x1_t + arm_off)):
        s.append(f'<rect x="{ax - 6}" y="{40 - 6}" width="12" height="{W_top + 12}" fill="url(#metal)" stroke="#333"/>')
        s.append(f'<circle cx="{sx}" cy="{pin_y_t}" r="4" fill="#c0392b" stroke="#7a1f15" stroke-width="1.2"/>')
    s.append(f'<text x="-8" y="32" font-size="11" fill="#444">arms grip the two end caps via pin stubs</text>')
    s.append(f'<line x1="{body_x0_t + L_top / 2 - 50}" y1="{40 + W_top + 50}" '
             f'x2="{body_x0_t + L_top / 2 + 50}" y2="{40 + W_top + 50}" stroke="#5a4a30" stroke-width="6"/>')
    s.append(f'<text x="{body_x0_t + L_top / 2}" y="{40 + W_top + 70}" text-anchor="middle" font-size="11" fill="#5a4a30">'
             'fixed strike-off bar (bed-edge mounted)</text>')
    s.append('</g>')

    s.append(
        f'<text x="{W//2}" y="{H - 60}" text-anchor="middle" font-size="13" fill="#444" font-style="italic">'
        "The pivot pin runs along the trough's LONG axis L (not across its width).  Arms grip the two end caps,"
        "</text>"
    )
    s.append(
        f'<text x="{W//2}" y="{H - 40}" text-anchor="middle" font-size="13" fill="#444" font-style="italic">'
        "so when the trough rolls about the pin it pours over the FULL 80 mm long edge — eliminating the narrow-bottleneck"
        "</text>"
    )
    s.append(
        f'<text x="{W//2}" y="{H - 20}" text-anchor="middle" font-size="13" fill="#444" font-style="italic">'
        "and trapped-volume problems of an end-over-end tilt of a half-cylinder (Edison analysis-v2 §3)."
        "</text>"
    )
    s.append(_svg_close())
    return "".join(s)


# ---------------------------------------------------------------------------
# Panel B — Pivot detail
# ---------------------------------------------------------------------------

def panel_B() -> str:
    W, H = 900, 600
    s = [_svg_open(W, H)]
    s.append(
        f'<text x="{W//2}" y="34" text-anchor="middle" font-size="22" font-weight="700">'
        "Subpanel B — Pivot pin / end-cap detail (longitudinal axis)</text>"
    )
    s.append(
        f'<text x="{W//2}" y="56" text-anchor="middle" font-size="13" fill="#555" font-style="italic">'
        "single horizontal pin runs ALONG L, through both end caps and both arms; quick-release to swap troughs"
        "</text>"
    )
    cx, cy, R = 350, 320, 130
    s.append(f'<path d="M {cx - R} {cy} L {cx + R} {cy} A {R} {R} 0 0 1 {cx - R} {cy} Z" '
             'fill="url(#metal)" stroke="#222" stroke-width="2.5"/>')
    s.append(f'<text x="{cx}" y="{cy + R + 30}" text-anchor="middle" font-size="12" fill="#444">'
             'trough end cap (cross-section, looking down L)</text>')
    s.append(f'<circle cx="{cx}" cy="{cy}" r="20" fill="#7e8794" stroke="#222" stroke-width="2"/>')
    s.append(f'<text x="{cx + 28}" y="{cy - 24}" font-size="11" fill="#444">pivot boss (printed</text>')
    s.append(f'<text x="{cx + 28}" y="{cy - 12}" font-size="11" fill="#444">into end cap)</text>')
    s.append(f'<rect x="{cx - 8}" y="{cy - 200}" width="16" height="180" fill="url(#metal)" stroke="#333"/>')
    s.append(f'<text x="{cx + 18}" y="{cy - 160}" font-size="12" fill="#444">arm (one of two; bolted to gantry carriage)</text>')
    s.append(f'<line x1="{cx - 80}" y1="{cy}" x2="{cx + 90}" y2="{cy}" stroke="#c0392b" stroke-width="6"/>')
    s.append(f'<circle cx="{cx + 95}" cy="{cy}" r="6" fill="#c0392b" stroke="#7a1f15" stroke-width="1.5"/>')
    s.append(f'<text x="{cx + 105}" y="{cy + 5}" font-size="12" fill="#c0392b">pin (along L)</text>')
    s.append(f'<path d="M {cx + 100} {cy - 18} q 14 18 0 36" fill="none" stroke="#c0392b" stroke-width="2"/>')
    s.append(f'<text x="{cx + 110}" y="{cy + 30}" font-size="11" fill="#c0392b">e-clip / retaining ring</text>')
    com_y = cy + 38
    s.append(f'<line x1="{cx - 7}" y1="{com_y}" x2="{cx + 7}" y2="{com_y}" stroke="#222" stroke-width="1.6"/>')
    s.append(f'<line x1="{cx}" y1="{com_y - 7}" x2="{cx}" y2="{com_y + 7}" stroke="#222" stroke-width="1.6"/>')
    s.append(f'<circle cx="{cx}" cy="{com_y}" r="9" fill="none" stroke="#222" stroke-width="1.2"/>')
    s.append(f'<text x="{cx + 16}" y="{com_y + 5}" font-size="11" fill="#222">centre of mass (loaded)</text>')
    s.append(f'<text x="{cx - 240}" y="{cy + 100}" font-size="12" fill="#222">'
             'pivot pin sits ~3 mm above loaded COM</text>')
    s.append(f'<text x="{cx - 240}" y="{cy + 116}" font-size="12" fill="#222">'
             '→ gravity returns trough to "open-up" (stable pendulum)</text>')
    s.append(f'<text x="{cx - 240}" y="{cy + 152}" font-size="11" fill="#5a3a8a">'
             'metal pivot pin doubles as ground path for an</text>')
    s.append(f'<text x="{cx - 240}" y="{cy + 168}" font-size="11" fill="#5a3a8a">'
             'optional conductive (e.g. copper-tape) trough lining,</text>')
    s.append(f'<text x="{cx - 240}" y="{cy + 184}" font-size="11" fill="#5a3a8a">'
             'mitigating triboelectric charging on fine inorganic powders.</text>')
    s.append(_svg_close())
    return "".join(s)


# ---------------------------------------------------------------------------
# Panel C — Isometric
# ---------------------------------------------------------------------------

def panel_C() -> str:
    W, H = 1000, 680
    s = [_svg_open(W, H)]
    s.append(
        f'<text x="{W//2}" y="34" text-anchor="middle" font-size="22" font-weight="700">'
        "Subpanel C — 3D / isometric view of the assembly on a gantry"
        "</text>"
    )
    s.append(
        f'<text x="{W//2}" y="56" text-anchor="middle" font-size="13" fill="#555" font-style="italic">'
        "two arms grip the two end caps via pin stubs (red dots); cam track on a fixed post drives the sideways tilt"
        "</text>"
    )
    # Gantry carriage rail (drawn perpendicular to L; carriage travels in/out
    # of the page in true X, but we project it as a horizontal bar with
    # an axes inset clarifying the convention).
    s.append('<rect x="180" y="80" width="640" height="22" fill="url(#metalH)" stroke="#222" stroke-width="1.5"/>')
    s.append('<text x="500" y="76" text-anchor="middle" font-size="12" fill="#444">gantry carriage (carries the two arms; X / Z stage)</text>')
    # Two arms — moved outboard of the trough body so they read as end-cap
    # mounts, not as side-of-body grips.
    arm_left_x = 250
    arm_right_x = 690
    s.append(f'<polygon points="{arm_left_x},102 {arm_left_x + 18},102 {arm_left_x + 18},308 {arm_left_x},308" fill="url(#metal)" stroke="#333"/>')
    s.append(f'<polygon points="{arm_right_x},102 {arm_right_x + 18},102 {arm_right_x + 28},298 {arm_right_x + 10},298" fill="url(#metal)" stroke="#333"/>')
    s.append(f'<text x="{arm_left_x - 4}" y="98" text-anchor="end" font-size="11" fill="#444">arm L</text>')
    s.append(f'<text x="{arm_right_x + 32}" y="98" text-anchor="start" font-size="11" fill="#444">arm R</text>')
    # Trough body (sits between the two arms; its end caps face the arms)
    body_x0 = arm_left_x + 30
    body_x1 = arm_right_x - 4
    s.append(
        f'<polygon points="{body_x0},300 {body_x1},290 {body_x1},260 {body_x0},270" '
        'fill="#dfe4ea" stroke="#222" stroke-width="2"/>'
    )
    s.append(
        f'<path d="M {body_x0},270 '
        f'C {body_x0 + 70},420 {body_x1 - 70},410 {body_x1},260 '
        f'L {body_x1},290 '
        f'C {body_x1 - 70},440 {body_x0 + 70},450 {body_x0},300 Z" '
        'fill="url(#metalH)" stroke="#222" stroke-width="2"/>'
    )
    s.append(
        f'<polygon points="{body_x0 + 6},295 {body_x1 - 6},287 {body_x1 - 6},265 {body_x0 + 6},275" '
        'fill="url(#powder)" opacity="0.95"/>'
    )
    # Longitudinal pin: solid stubs in the air gaps between arm and body,
    # dashed (hidden) inside the body.
    pin_y0 = 285   # at left arm end
    pin_y1 = 275   # at right arm end (skewed for iso)
    # Left exposed stub (arm to body)
    s.append(f'<line x1="{arm_left_x + 18}" y1="{pin_y0}" x2="{body_x0}" y2="{pin_y0 - 1}" '
             'stroke="#c0392b" stroke-width="5"/>')
    # Hidden segment inside body (dashed)
    s.append(f'<line x1="{body_x0}" y1="{pin_y0 - 1}" x2="{body_x1}" y2="{pin_y1 + 1}" '
             'stroke="#c0392b" stroke-width="3" stroke-dasharray="7 4" opacity="0.65"/>')
    # Right exposed stub (body to arm)
    s.append(f'<line x1="{body_x1}" y1="{pin_y1 + 1}" x2="{arm_right_x + 12}" y2="{pin_y1}" '
             'stroke="#c0392b" stroke-width="5"/>')
    # Pin-stub indicator dots at both arms
    s.append(f'<circle cx="{arm_left_x + 9}" cy="{pin_y0 + 1}" r="6" fill="#c0392b" stroke="#7a1f15" stroke-width="1.5"/>')
    s.append(f'<circle cx="{arm_right_x + 19}" cy="{pin_y1 - 1}" r="6" fill="#c0392b" stroke="#7a1f15" stroke-width="1.5"/>')
    # Leader lines / labels for end-cap connection points
    s.append(f'<line x1="{arm_left_x + 9}" y1="{pin_y0 + 12}" x2="{arm_left_x - 30}" y2="{pin_y0 + 60}" '
             'stroke="#c0392b" stroke-width="1"/>')
    s.append(f'<text x="{arm_left_x - 36}" y="{pin_y0 + 72}" text-anchor="end" font-size="11" fill="#c0392b">'
             'pin stub through end cap → bushing on arm L</text>')
    s.append(f'<line x1="{arm_right_x + 19}" y1="{pin_y1 + 12}" x2="{arm_right_x + 60}" y2="{pin_y1 + 60}" '
             'stroke="#c0392b" stroke-width="1"/>')
    s.append(f'<text x="{arm_right_x + 64}" y="{pin_y1 + 72}" text-anchor="start" font-size="11" fill="#c0392b">'
             'pin stub through end cap → bushing on arm R</text>')
    s.append(f'<text x="{(body_x0 + body_x1) // 2}" y="248" text-anchor="middle" font-size="11" fill="#c0392b" font-style="italic">'
             '(dashed segment = pin hidden inside trough body)</text>')
    # Continuous chamfered lip running the full length L on the long-side
    # rim (drawn here for the near rim; the far rim carries an identical
    # lip, since the trough is symmetric and may dump in either direction).
    s.append(
        f'<polygon points="{body_x0 + 6},272 {body_x1 - 6},262 '
        f'{body_x1 - 6},254 {body_x0 + 6},264" '
        'fill="#7e8794" stroke="#222" stroke-width="1.2"/>'
    )
    s.append(f'<text x="{(body_x0 + body_x1) // 2}" y="{232}" text-anchor="middle" font-size="11" fill="#444">'
             'continuous chamfered lip (full length L; both long sides) — also rides the cam ramp</text>')
    # Cam post + ramp (unchanged)
    s.append('<rect x="850" y="180" width="18" height="320" fill="#8a7a5e" stroke="#444"/>')
    s.append('<text x="858" y="510" text-anchor="middle" font-size="11" fill="#5a4a30">fixed post</text>')
    s.append('<polygon points="730,300 850,300 850,250 730,300" fill="#8a7a5e" stroke="#444" stroke-width="1.5"/>')
    s.append('<text x="780" y="320" text-anchor="middle" font-size="12" fill="#5a4a30">smooth inclined cam track</text>')
    s.append('<text x="780" y="336" text-anchor="middle" font-size="11" fill="#7a6a4a">'
             '(replaces sawtooth; rim lip slides up its hypotenuse)</text>')
    # Strike-off bar
    s.append('<rect x="220" y="510" width="350" height="10" fill="#5a4a30" stroke="#222"/>')
    s.append('<text x="395" y="535" text-anchor="middle" font-size="11" fill="#5a4a30">'
             'fixed strike-off bar (bed-edge mounted; trough wipes under during the lift-out)</text>')
    s.append('<rect x="180" y="555" width="430" height="55" fill="url(#powder)" stroke="#7a5a1a"/>')
    s.append('<text x="395" y="595" text-anchor="middle" font-size="12" fill="#7a5a1a">powder bed</text>')
    # Axes inset (top right) clarifying L vs gantry-X convention
    ax0, ay0 = 880, 590
    s.append(f'<g transform="translate({ax0},{ay0})">')
    s.append('<rect x="-6" y="-46" width="100" height="64" fill="#fff" stroke="#aaa" stroke-width="1" rx="3"/>')
    s.append('<line x1="0" y1="0" x2="40" y2="0" stroke="#222" stroke-width="2" marker-end="url(#arrowK)"/>')
    s.append('<text x="44" y="4" font-size="10" fill="#222">L (pin axis)</text>')
    s.append('<line x1="0" y1="0" x2="0" y2="-30" stroke="#1f5fbf" stroke-width="2" marker-end="url(#arrowB)"/>')
    s.append('<text x="4" y="-32" font-size="10" fill="#1f5fbf">Z gantry</text>')
    s.append('<circle cx="0" cy="0" r="3" fill="#c0392b"/><circle cx="0" cy="0" r="6" fill="none" stroke="#c0392b"/>')
    s.append('<text x="-10" y="14" font-size="10" fill="#c0392b" text-anchor="end">X (out of page)</text>')
    s.append('</g>')
    s.append(_svg_close())
    return "".join(s)


# ---------------------------------------------------------------------------
# Panel D — Mechanism (4 steps now: J-plunge, strike-off, transport, tilt)
# ---------------------------------------------------------------------------

## Shared layout constants for the 4-step Panel D frames.
## Every frame uses identical X/Y so the eye can compare them.
PANEL_D_FRAME_W = 400        # nominal viewbox of one frame
PANEL_D_BED_Y = 360          # top of powder bed
PANEL_D_BED_H = 50
PANEL_D_PIVOT_X = 200        # arm/pivot X within frame (centred)
PANEL_D_PIVOT_Y = 270        # pivot pin Y (above the bed)
PANEL_D_ARM_TOP = 40
PANEL_D_TROUGH_R = 38
PANEL_D_STRIKEOFF_Y = PANEL_D_PIVOT_Y - 4   # bar sits at the trough rim height
PANEL_D_GROUND_Y = PANEL_D_BED_Y            # for cam base alignment


def _draw_step_frame(
    title: str,
    *,
    show_bed: bool,
    show_cam: bool,
    powder_pour: bool,
    show_strike_off: bool,
    trough_rotate: float = 0.0,
    extra: str = "",
) -> str:
    """Draw one Panel D step in a fixed local coordinate frame.

    All four frames share PANEL_D_PIVOT_X / PANEL_D_PIVOT_Y / PANEL_D_BED_Y, so
    when they are placed side-by-side in panel_D() the powder bed, pivot pin
    and arm line up across the row.  Per-step variation is limited to which
    scenery objects are shown and the trough roll angle.
    """
    px = PANEL_D_PIVOT_X
    py = PANEL_D_PIVOT_Y
    R = PANEL_D_TROUGH_R
    parts = []
    parts.append(
        f'<text x="{PANEL_D_FRAME_W // 2}" y="0" text-anchor="middle" '
        'font-size="17" font-weight="600">' + title + '</text>'
    )
    # Always-visible "ground" / bed line to anchor the eye, even on steps
    # where we hide the bed colour fill.
    parts.append(
        f'<line x1="0" y1="{PANEL_D_BED_Y}" x2="{PANEL_D_FRAME_W}" y2="{PANEL_D_BED_Y}" '
        'stroke="#bdb085" stroke-width="1" stroke-dasharray="4 3"/>'
    )
    if show_bed:
        parts.append(
            f'<rect x="0" y="{PANEL_D_BED_Y}" width="{PANEL_D_FRAME_W}" '
            f'height="{PANEL_D_BED_H}" fill="url(#powder)" stroke="#7a5a1a"/>'
        )
        parts.append(
            f'<text x="{PANEL_D_FRAME_W // 2}" y="{PANEL_D_BED_Y + PANEL_D_BED_H + 14}" '
            'text-anchor="middle" font-size="11" fill="#7a5a1a">powder bed</text>'
        )
    if show_strike_off:
        # Strike-off bar at trough rim height, just to the right of the pivot
        # so the rim wipes past it as the gantry travels +X (lift-out).
        bar_x0 = px + R - 4
        bar_x1 = px + R + 110
        parts.append(
            f'<rect x="{bar_x0}" y="{PANEL_D_STRIKEOFF_Y - 3}" '
            f'width="{bar_x1 - bar_x0}" height="6" fill="#5a4a30" stroke="#222"/>'
        )
        parts.append(
            f'<text x="{(bar_x0 + bar_x1) // 2}" y="{PANEL_D_STRIKEOFF_Y - 8}" '
            'text-anchor="middle" font-size="10" fill="#5a4a30">strike-off bar</text>'
        )
    if show_cam:
        # Position the cam ramp so its apex actually meets the rotated rim.
        # Bumper world position (in frame coords) given current trough roll:
        import math
        rad = math.radians(trough_rotate)
        bumper_x = px + R * math.cos(rad)
        bumper_y = py + R * math.sin(rad)
        # Ramp: hypotenuse from (bumper_x, bumper_y) at the apex, sloping
        # down-right to a vertical post that drops to the bed line.
        cam_run = 70
        cam_base_x = bumper_x + cam_run
        cam_base_y = PANEL_D_BED_Y
        post_x = cam_base_x + 6
        parts.append(
            f'<rect x="{post_x:.1f}" y="{bumper_y - 8:.1f}" width="14" '
            f'height="{cam_base_y - (bumper_y - 8):.1f}" fill="#8a7a5e" stroke="#444"/>'
        )
        parts.append(
            f'<polygon points="{bumper_x:.1f},{bumper_y:.1f} '
            f'{cam_base_x:.1f},{cam_base_y} '
            f'{post_x:.1f},{cam_base_y} '
            f'{post_x:.1f},{bumper_y - 8:.1f}" '
            'fill="#8a7a5e" stroke="#444" stroke-width="1.5"/>'
        )
        parts.append(
            f'<text x="{(bumper_x + cam_base_x) / 2:.1f}" y="{cam_base_y + 14}" '
            'text-anchor="middle" font-size="10" fill="#5a4a30">smooth cam ramp</text>'
        )
        # Contact dot at the rim/cam touch point
        parts.append(
            f'<circle cx="{bumper_x:.1f}" cy="{bumper_y:.1f}" r="4" '
            'fill="#c0392b" stroke="#7a1f15" stroke-width="1.2"/>'
        )
    # Arm — top anchored to PANEL_D_ARM_TOP so all arms line up vertically
    arm_h = py - PANEL_D_ARM_TOP
    parts.append(
        f'<rect x="{px - 8}" y="{PANEL_D_ARM_TOP}" width="16" height="{arm_h}" '
        'fill="url(#metal)" stroke="#333"/>'
    )
    parts.append(
        f'<circle cx="{px}" cy="{py}" r="7" fill="#c0392b" stroke="#7a1f15" stroke-width="1.5"/>'
    )
    parts.append(trough_cross_section(px, py, R, rotate_deg=trough_rotate))
    if powder_pour:
        # Pour stream emerges from the lowered (right) rim of the rotated
        # trough — so its top must sit at the rim's actual rotated position,
        # not at a hard-coded location.
        import math
        rad = math.radians(trough_rotate)
        rim_x = px + R * math.cos(rad)
        rim_y = py + R * math.sin(rad)
        stream_bottom_y = PANEL_D_BED_Y - 2
        parts.append(
            '<g fill="url(#powder)" opacity="0.95">'
            f'<path d="M {rim_x - 6} {rim_y} '
            f'Q {rim_x + 4} {(rim_y + stream_bottom_y) / 2} '
            f'{rim_x + 14} {stream_bottom_y} '
            f'L {rim_x + 30} {stream_bottom_y} '
            f'Q {rim_x + 26} {(rim_y + stream_bottom_y) / 2} '
            f'{rim_x + 14} {rim_y - 4} Z"/>'
            '</g>'
        )
        parts.append(
            f'<text x="{rim_x + 12}" y="{stream_bottom_y + 16}" text-anchor="middle" '
            'font-size="11" fill="#7a5a1a">powder pours over FULL long edge</text>'
        )
    parts.append(extra)
    return "\n".join(parts)


def panel_D() -> str:
    # 4 frames, each PANEL_D_FRAME_W wide, separated by 60 px gutter for arrow.
    gutter = 60
    n = 4
    W = n * PANEL_D_FRAME_W + (n - 1) * gutter + 80
    H = 600
    s = [_svg_open(W, H)]
    s.append(
        f'<text x="{W//2}" y="34" text-anchor="middle" font-size="22" font-weight="700">'
        "Subpanel D — Mechanism of action (side view, 4 steps)"
        "</text>"
    )
    s.append(
        f'<text x="{W//2}" y="56" text-anchor="middle" font-size="13" fill="#555" font-style="italic">'
        "all four frames share the same powder-bed line, pivot height and arm length so motion is comparable"
        "</text>"
    )
    R = PANEL_D_TROUGH_R
    top = 80
    py = PANEL_D_PIVOT_Y
    bed_y = PANEL_D_BED_Y
    frame_x = [40 + i * (PANEL_D_FRAME_W + gutter) for i in range(n)]

    # Step 1 — J-curve plunge
    s.append(f'<g transform="translate({frame_x[0]},{top})">')
    s.append(_draw_step_frame(
        "1. J-curve plunge",
        show_bed=True, show_cam=False, powder_pour=False,
        show_strike_off=False, trough_rotate=0,
        extra=(
            f'<path d="M 60 60 L 60 {py - 60} Q 60 {py - 10} {PANEL_D_PIVOT_X - R - 10} {py - 4}" '
            'fill="none" stroke="#1f5fbf" stroke-width="3" marker-end="url(#arrowB)"/>'
            '<text x="48" y="160" font-size="11" fill="#1f5fbf" '
            'transform="rotate(-90 48 160)" text-anchor="middle">Z ↓</text>'
            f'<text x="120" y="{py + 4}" font-size="11" fill="#1f5fbf">then X →</text>'
            '<text x="20" y="20" font-size="10" fill="#1f5fbf">J-curve avoids flat-blunt compaction</text>'
        ),
    ))
    s.append('</g>')

    # Step 2 — strike-off (lift)
    s.append(f'<g transform="translate({frame_x[1]},{top})">')
    s.append(_draw_step_frame(
        "2. Lift past strike-off bar",
        show_bed=True, show_cam=False, powder_pour=False,
        show_strike_off=True, trough_rotate=0,
        extra=(
            f'<line x1="40" y1="{py + 30}" x2="40" y2="{PANEL_D_ARM_TOP + 40}" '
            'stroke="#1f5fbf" stroke-width="3" marker-end="url(#arrowB)"/>'
            '<text x="26" y="200" font-size="11" fill="#1f5fbf" '
            'transform="rotate(-90 26 200)" text-anchor="middle">Z ↑</text>'
            f'<text x="{PANEL_D_PIVOT_X + R + 60}" y="{PANEL_D_STRIKEOFF_Y + 28}" '
            'text-anchor="middle" font-size="10" fill="#5a4a30">'
            'rim wipes past bar → defines fill volume</text>'
        ),
    ))
    s.append('</g>')

    # Step 3 — transport
    s.append(f'<g transform="translate({frame_x[2]},{top})">')
    s.append(_draw_step_frame(
        "3. Transport (X →)",
        show_bed=False, show_cam=False, powder_pour=False,
        show_strike_off=False, trough_rotate=0,
        extra=(
            f'<line x1="{PANEL_D_PIVOT_X - 80}" y1="{PANEL_D_ARM_TOP + 80}" '
            f'x2="{PANEL_D_PIVOT_X + 80}" y2="{PANEL_D_ARM_TOP + 80}" '
            'stroke="#1f5fbf" stroke-width="3" marker-end="url(#arrowB)"/>'
            f'<text x="{PANEL_D_PIVOT_X}" y="{PANEL_D_ARM_TOP + 70}" '
            'font-size="12" fill="#1f5fbf" text-anchor="middle">X →</text>'
            f'<text x="{PANEL_D_PIVOT_X}" y="{py + R + 30}" font-size="10" fill="#444" '
            'text-anchor="middle">trough hangs level under gravity</text>'
        ),
    ))
    s.append('</g>')

    # Step 4 — sideways tilt against cam
    s.append(f'<g transform="translate({frame_x[3]},{top})">')
    s.append(_draw_step_frame(
        "4. Sideways tilt → deposit",
        show_bed=False, show_cam=True, powder_pour=True,
        show_strike_off=False, trough_rotate=55,
        extra=(
            f'<line x1="20" y1="{PANEL_D_ARM_TOP + 20}" x2="80" y2="{PANEL_D_ARM_TOP + 20}" '
            'stroke="#1f5fbf" stroke-width="3" marker-end="url(#arrowB)"/>'
            f'<text x="50" y="{PANEL_D_ARM_TOP + 12}" text-anchor="middle" '
            'font-size="11" fill="#1f5fbf">gantry pushes X →</text>'
            f'<path d="M {PANEL_D_PIVOT_X - 60} {py + 10} '
            f'a 36 36 0 0 1 38 -42" fill="none" stroke="#1f5fbf" stroke-width="2.5" '
            'marker-end="url(#arrowB)"/>'
            f'<text x="{PANEL_D_PIVOT_X - 50}" y="{py + 32}" font-size="10" fill="#1f5fbf">'
            'trough rolls sideways</text>'
            f'<text x="{PANEL_D_PIVOT_X - 50}" y="{py + 46}" font-size="10" fill="#1f5fbf">'
            'about its long axis</text>'
            f'<text x="{PANEL_D_PIVOT_X + R + 4}" y="{py - R - 6}" font-size="10" fill="#c0392b">'
            'rim lip rides up cam</text>'
        ),
    ))
    s.append('</g>')

    # Inter-frame chevron arrows aligned to pivot height
    for i in range(n - 1):
        ax = frame_x[i] + PANEL_D_FRAME_W + 8
        bx = frame_x[i + 1] - 8
        s.append(
            f'<line x1="{ax}" y1="{top + py}" x2="{bx}" y2="{top + py}" '
            'stroke="#222" stroke-width="2.5" marker-end="url(#arrowK)"/>'
        )

    s.append(
        f'<text x="{W//2}" y="{H - 50}" text-anchor="middle" font-size="13" fill="#444" font-style="italic">'
        "Pure-X gantry travel works because the smooth cam ramp gives a continuously varying engagement point"
        "</text>"
    )
    s.append(
        f'<text x="{W//2}" y="{H - 30}" text-anchor="middle" font-size="13" fill="#444" font-style="italic">'
        "(unlike a fixed sawtooth tooth, which is kinematically incompatible with a horizontally-translating pivot — Edison v2 §1)."
        "</text>"
    )
    s.append(_svg_close())
    return "".join(s)


# ---------------------------------------------------------------------------
# Animation: cam-engagement + sideways tilt
# ---------------------------------------------------------------------------

def _frame_svg(t: float) -> str:
    """Render a single GIF frame at parameter ``t`` in [0, 1].

    The motion is parameterised so the trough's right-side bumper actually
    rides on the cam ramp's hypotenuse throughout the rotation phase, instead
    of tilting in mid-air far away from the cam (PR review r3134723829).

    Phases:

    * ``0.00`` – ``0.30``  Approach: the trough translates horizontally in
      ``+X``; trough still level (``roll = 0``).
    * ``0.30`` – ``0.75``  Cam engagement: the trough's right bumper rides up
      and over the smooth cam apex; ``roll`` increases linearly with X-travel
      so contact is maintained.  The trough's pivot continues to translate
      ``+X`` (gantry-driven), and the bumper traces the cam's hypotenuse.
    * ``0.75`` – ``1.00``  Pour: trough holds maximum tilt at the deposit
      pose while powder drains over the lowered long edge.

    Returns the SVG markup for the single frame as a ``str``.
    """
    import math

    W, H = 760, 460
    R = 50
    pivot_y = 230
    max_roll_deg = 55.0

    # --- Cam geometry (fixed in world frame) ---------------------------------
    # Cam apex sits at the right-rim height of the level trough; the cam's
    # vertical drop is capped at R·sin(max_roll) so the bumper can physically
    # reach the cam base without the asin saturating.  Cam horizontal run is
    # picked so the slope is roughly 45 ° (visually readable).
    cam_apex_x = 380
    cam_apex_y = pivot_y
    cam_drop = R * math.sin(math.radians(max_roll_deg))     # ~41 px
    cam_run = cam_drop                                      # 45 ° ramp
    cam_base_x = cam_apex_x + cam_run
    cam_base_y = cam_apex_y + cam_drop

    # --- Pivot / roll schedule ----------------------------------------------
    if t < 0.30:
        # Approach: rim travels from x=120 to where it just touches cam apex
        # (rim x = pivot_x + R, so pivot_x ends at cam_apex_x - R)
        u = t / 0.30
        pivot_x = 120 + u * ((cam_apex_x - R) - 120)
        roll_deg = 0.0
    else:
        # Rotation phase (and pour phase, which just holds at max).  Roll
        # increases linearly with normalised progress through the contact
        # phase, capped at max_roll_deg.  Pivot_x is then derived so the
        # bumper stays on the cam hypotenuse.
        if t < 0.75:
            u = (t - 0.30) / 0.45
        else:
            u = 1.0
        roll_deg = u * max_roll_deg
        roll_rad = math.radians(roll_deg)
        # Bumper world Y is fixed by the roll angle:
        by = pivot_y + R * math.sin(roll_rad)
        # Find bumper world X by intersecting that Y with the cam hypotenuse:
        if cam_base_y == cam_apex_y:
            bx = cam_apex_x
        else:
            f = (by - cam_apex_y) / (cam_base_y - cam_apex_y)
            f = max(0.0, min(1.0, f))
            bx = cam_apex_x + f * (cam_base_x - cam_apex_x)
        pivot_x = bx - R * math.cos(roll_rad)

    # --- Render --------------------------------------------------------------
    s_out = [_svg_open(W, H, font_size=12)]
    # Gantry rail
    s_out.append('<rect x="40" y="20" width="680" height="14" fill="url(#metalH)" stroke="#222"/>')
    # Arm
    s_out.append(
        f'<rect x="{pivot_x - 8}" y="34" width="16" height="{pivot_y - 34}" '
        'fill="url(#metal)" stroke="#333"/>'
    )
    # Powder bed (left half)
    s_out.append('<rect x="40" y="400" width="320" height="40" fill="url(#powder)" stroke="#7a5a1a"/>')
    # Strike-off bar at the bed's right edge
    s_out.append('<rect x="320" y="386" width="50" height="6" fill="#5a4a30" stroke="#222"/>')
    # Cam: post + ramp.  The ramp is drawn as a triangle whose hypotenuse
    # exactly coincides with the bumper trajectory line above.
    cam_post_x = cam_base_x + 6
    s_out.append(
        f'<rect x="{cam_post_x}" y="{cam_apex_y - 10}" width="14" '
        f'height="{440 - cam_apex_y + 10}" fill="#8a7a5e" stroke="#444"/>'
    )
    s_out.append(
        f'<polygon points="{cam_apex_x},{cam_apex_y} '
        f'{cam_base_x},{cam_base_y} '
        f'{cam_post_x},{cam_base_y} '
        f'{cam_post_x},{cam_apex_y}" '
        'fill="#8a7a5e" stroke="#444" stroke-width="1.5"/>'
    )
    # Pivot pin
    s_out.append(
        f'<circle cx="{pivot_x:.1f}" cy="{pivot_y}" r="7" '
        'fill="#c0392b" stroke="#7a1f15" stroke-width="1.5"/>'
    )
    # Trough cross-section, rolled
    s_out.append(trough_cross_section(pivot_x, pivot_y, R, rotate_deg=roll_deg, powder_fill_frac=0.85))
    # If we are in/past the cam-engagement phase, draw a small contact dot at
    # the cam-bumper contact point so the eye registers the contact.
    if t >= 0.30:
        bx = pivot_x + R * math.cos(math.radians(roll_deg))
        by = pivot_y + R * math.sin(math.radians(roll_deg))
        s_out.append(
            f'<circle cx="{bx:.1f}" cy="{by:.1f}" r="5" fill="#c0392b" '
            'stroke="#7a1f15" stroke-width="1.2" opacity="0.95"/>'
        )
        s_out.append(
            f'<text x="{bx + 8:.1f}" y="{by - 8:.1f}" font-size="10" fill="#c0392b">'
            'rim ⨉ cam contact</text>'
        )
    # Pour stream during pour phase, anchored at the rotated rim
    if t > 0.75:
        a = (t - 0.75) / 0.25
        pour_top_x = pivot_x + R * math.cos(math.radians(roll_deg))
        pour_top_y = pivot_y + R * math.sin(math.radians(roll_deg))
        pour_bot_y = 440
        s_out.append(
            f'<g fill="url(#powder)" opacity="{0.6 + 0.35 * a:.2f}">'
            f'<path d="M {pour_top_x - 6:.1f} {pour_top_y - 4:.1f} '
            f'Q {pour_top_x + 4:.1f} {(pour_top_y + pour_bot_y) / 2:.1f} '
            f'{pour_top_x + 16:.1f} {pour_bot_y:.1f} '
            f'L {pour_top_x + 36:.1f} {pour_bot_y:.1f} '
            f'Q {pour_top_x + 30:.1f} {(pour_top_y + pour_bot_y) / 2:.1f} '
            f'{pour_top_x + 18:.1f} {pour_top_y - 6:.1f} Z"/>'
            f'</g>'
        )
    # Headings
    s_out.append(
        '<text x="380" y="50" text-anchor="middle" font-size="13" font-weight="600">'
        'Sideways tilt against a smooth cam (corrected geometry)</text>'
    )
    s_out.append(
        '<text x="380" y="68" text-anchor="middle" font-size="11" fill="#555" font-style="italic">'
        'rim stays in contact with cam ramp throughout rotation; pours over full long edge</text>'
    )
    s_out.append(_svg_close())
    return "".join(s_out)


def panel_E() -> str:
    """Pin-defined-path actuation variant.

    A vertical stem hangs from the gantry carriage on a pin pivot; a
    transverse peg at the top of the stem rides in a routed slot cut into a
    fixed external board (mounted at fixed height in the work area).  As the
    gantry translates in X, the peg follows the slot path; the difference
    between the carriage's straight-line trajectory and the slot's routed
    path forces the stem (and the trough rigidly attached to it) to rotate
    about the carriage pivot.

    The figure shows three frozen poses (scoop / transport / pour) overlaid
    against a single fixed slot board, so the slot's "program" for tilt-vs-X
    is visible at a glance.
    """
    W, H = 760, 560
    s: list[str] = [_svg_open(W, H)]
    # Title
    s.append(
        '<text x="380" y="28" text-anchor="middle" font-size="15" '
        'font-weight="600">Pin-defined-path actuation (cam-slot variant)</text>'
    )
    s.append(
        '<text x="380" y="46" text-anchor="middle" font-size="11" fill="#555" '
        'font-style="italic">peg on top of stem rides in routed slot in a fixed external board; '
        'slot path = tilt schedule</text>'
    )

    # Fixed external board with the routed slot.  Mounted at a fixed Y.
    board_y = 100
    board_h = 56
    s.append(
        f'<rect x="60" y="{board_y}" width="640" height="{board_h}" '
        'fill="#e8e2cc" stroke="#7a6f4a" stroke-width="2" rx="3"/>'
    )
    s.append(
        f'<text x="68" y="{board_y - 6}" font-size="10" fill="#555">'
        'fixed external slot board (mounted to lab frame)</text>'
    )
    # Routed slot path: flat over the bed (left), flat over transport
    # (middle), then rising over the deposit station (right) — encoding the
    # tilt schedule. Drawn as a darker channel inside the board.
    slot_y_flat = board_y + board_h - 12     # near the BOTTOM edge of the board
    slot_y_top = board_y + 12                # rises near the TOP edge — bigger excursion
    slot_w = 14                              # slot width (peg diameter ~slot)
    # Centerline polyline for the slot path:
    pts = [
        (90,  slot_y_flat),     # leftmost: scoop X
        (260, slot_y_flat),     # transport
        (430, slot_y_flat),     # transport
        (520, slot_y_flat - 12),# start to rise
        (600, slot_y_top),      # tilt-hold detent at deposit
        (680, slot_y_top),
    ]
    # Draw slot as a thick stroked polyline (looks like a routed channel)
    pl = " ".join(f"{x},{y}" for x, y in pts)
    s.append(
        f'<polyline points="{pl}" fill="none" stroke="#3a342a" '
        f'stroke-width="{slot_w}" stroke-linecap="round" stroke-linejoin="round"/>'
    )
    s.append(
        f'<polyline points="{pl}" fill="none" stroke="#857a5a" '
        f'stroke-width="{slot_w - 4}" stroke-linecap="round" stroke-linejoin="round"/>'
    )

    # Carriage pivot Y (the pin on the gantry that the stem hangs from)
    carriage_y = 240
    # Trough centre Y (below the carriage, hanging on the stem) — moved up so
    # the trough is large relative to the stem (was dwarfed previously).
    trough_y = 340
    trough_radius = 38                       # bigger trough so it actually reads
    stem_len = trough_y - carriage_y         # stem length (carriage pivot -> trough)
    # Distance from the carriage pivot up to where the peg sits in the slot
    # when the slot is at its flat Y.  Must be larger than the slot's
    # maximum vertical excursion so the peg can always reach the slot.
    peg_offset_above_pivot = carriage_y - slot_y_flat

    # Three frozen poses to draw, each at a different gantry X.
    # For each pose: compute the slot Y at that X (linear interp on the
    # polyline above) and the resulting stem tilt angle.
    import math

    def slot_y_at(x: float) -> float:
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            if x0 <= x <= x1:
                if x1 == x0:
                    return y0
                return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
        return pts[-1][1]

    poses = [
        (140, "Scoop", "trough flat, peg in flat section of slot"),
        (380, "Transport", "trough still flat (slot still flat)"),
        (640, "Pour", "slot rises -> stem tilts -> trough rolls sideways"),
    ]

    for px, label, sub in poses:
        # Where the peg sits in the slot at this gantry X:
        peg_y = slot_y_at(px)
        # Carriage pivot is at (px, carriage_y); peg sits "peg_offset_above_pivot"
        # above pivot along the stem.  Solve for stem angle (theta from
        # vertical) such that pivot + peg_offset_above_pivot * (sin t, -cos t)
        # lands on (px, peg_y):
        dy = carriage_y - peg_y          # how far peg is above pivot vertically
        # stem length above pivot is fixed (peg_offset_above_pivot); the peg can
        # only reach the slot if the slot Y is within reach. By construction
        # we made peg_offset_above_pivot > maximum dy, so:
        # sin(theta) = (peg_x - px) / peg_offset_above_pivot   but peg_x = px (peg
        # is constrained in *Y* by the slot, X follows the carriage), so the
        # stem leans only if the slot moves vertically -> peg_offset_above_pivot
        # must shorten vertically. Approximate angle by:
        #     cos(theta) = dy / peg_offset_above_pivot
        ratio = max(-1.0, min(1.0, dy / peg_offset_above_pivot))
        theta = math.acos(ratio)         # radians, 0 = vertical
        theta_deg = math.degrees(theta)

        # Carriage rail tick mark:
        s.append(
            f'<rect x="{px - 22}" y="{carriage_y - 10}" width="44" height="20" '
            'fill="#cfd8dc" stroke="#37474f" stroke-width="1.5" rx="2"/>'
        )
        s.append(
            f'<text x="{px}" y="{carriage_y - 14}" text-anchor="middle" '
            f'font-size="10" fill="#37474f">carriage</text>'
        )
        # Carriage pivot dot:
        s.append(
            f'<circle cx="{px}" cy="{carriage_y}" r="3" fill="#222"/>'
        )
        # Stem (rotated about carriage pivot)
        s.append(
            f'<g transform="translate({px},{carriage_y}) rotate({theta_deg})">'
        )
        # stem above pivot (up to peg)
        s.append(
            f'  <line x1="0" y1="0" x2="0" y2="{-peg_offset_above_pivot}" '
            'stroke="#444" stroke-width="3"/>'
        )
        # peg (small horizontal cylinder at top of stem)
        s.append(
            f'  <rect x="-9" y="{-peg_offset_above_pivot - 4}" width="18" height="8" '
            'fill="#9aa0a6" stroke="#222" stroke-width="1.2" rx="1"/>'
        )
        # stem below pivot (down to trough)
        s.append(
            f'  <line x1="0" y1="0" x2="0" y2="{stem_len}" '
            'stroke="#444" stroke-width="3"/>'
        )
        # Trough cross-section, rotated by the stem tilt.  At "pour" pose we
        # tilt the trough further to make pouring visually clear.
        extra = 45.0 if label == "Pour" else 0.0
        # The trough is rigid with the stem, so it rotates with the stem; the
        # ``transform`` group above already handles that. We pass extra tilt
        # only to show the pour reveal.
        s.append(
            "  " + trough_cross_section(
                cx=0, cy=stem_len, radius=trough_radius,
                rotate_deg=extra,
                powder_fill_frac=0.7 if label != "Pour" else 0.25,
                bumper=False,
            )
        )
        s.append("</g>")
        # Pose label
        s.append(
            f'<text x="{px}" y="{trough_y + trough_radius + 60}" text-anchor="middle" '
            f'font-size="12" font-weight="600">{label}</text>'
        )
        s.append(
            f'<text x="{px}" y="{trough_y + trough_radius + 76}" text-anchor="middle" '
            f'font-size="10" fill="#555">{sub}</text>'
        )

    # Annotate the slot regions:
    s.append(
        '<text x="170" y="180" text-anchor="middle" font-size="10" '
        'fill="#3a342a">flat slot section -> trough level</text>'
    )
    s.append(
        '<text x="555" y="86" text-anchor="middle" font-size="10" '
        'fill="#3a342a">rising slot section -> stem leans -> trough tilts</text>'
    )
    # Bed and target plate as scenery — anchored so the trough RIM sits ON
    # them in the scoop / pour poses.
    bed_top_y = trough_y + trough_radius - 4    # rim just dips into bed
    s.append(
        f'<rect x="80" y="{bed_top_y}" width="130" height="34" '
        'fill="url(#powder)" stroke="#7a6a3a" stroke-width="1.2"/>'
    )
    s.append(
        f'<text x="145" y="{bed_top_y + 50}" text-anchor="middle" font-size="10" '
        'fill="#7a6a3a">stock powder bed</text>'
    )
    plate_y = trough_y + trough_radius + 16
    s.append(
        f'<rect x="580" y="{plate_y}" width="120" height="6" '
        'fill="#cfd8dc" stroke="#37474f" stroke-width="1"/>'
    )
    s.append(
        f'<text x="640" y="{plate_y + 22}" text-anchor="middle" font-size="10" '
        'fill="#555">deposit / target plate</text>'
    )

    # Footer pointer to corresponding section
    s.append(
        '<text x="380" y="540" text-anchor="middle" font-size="10" fill="#555" '
        'font-style="italic">See manuscript Sec. "Pin-defined-path actuation" for the trade-off vs. the smooth cam ramp.</text>'
    )
    s.append(_svg_close())
    return "".join(s)


def render_gif() -> None:
    try:
        import cairosvg  # type: ignore
        from PIL import Image  # type: ignore
    except ImportError as e:  # pragma: no cover
        raise SystemExit(
            "cairosvg and Pillow are required to render the animation: "
            f"pip install cairosvg Pillow ({e})"
        )

    n_frames = 24
    images = []
    for i in range(n_frames):
        t = i / (n_frames - 1)
        png_bytes = cairosvg.svg2png(bytestring=_frame_svg(t).encode("utf-8"))
        images.append(Image.open(io.BytesIO(png_bytes)).convert("P", palette=Image.ADAPTIVE))
    out = FIG_DIR / "mechanism.gif"
    images[0].save(
        out,
        save_all=True,
        append_images=images[1:] + list(reversed(images[1:-1])),
        duration=110,
        loop=0,
        optimize=True,
        disposal=2,
    )
    print(f"wrote {out}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_FIG_DIR,
        help=(
            "Directory to write the generated panels and GIF into. Defaults "
            "to docs/figures/ relative to the repository root."
        ),
    )
    args = parser.parse_args()
    global FIG_DIR
    FIG_DIR = args.output_dir
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    panels = {
        "panel-A-orthographic.svg": panel_A,
        "panel-B-pivot-detail.svg": panel_B,
        "panel-C-isometric.svg": panel_C,
        "panel-D-mechanism.svg": panel_D,
        "panel-E-pin-slot.svg": panel_E,
    }
    for name, fn in panels.items():
        path = FIG_DIR / name
        path.write_text(fn())
        print(f"wrote {path}")
    render_gif()


if __name__ == "__main__":
    main()
