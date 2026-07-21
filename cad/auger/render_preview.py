"""
Pure Python preview renderer for the Archimedes auger v2.
No dependencies — uses only stdlib math to generate an SVG.
Run: python3 cad/auger/render_preview.py
Output: cad/auger/preview.svg
"""
import math

# ── Design parameters — must match archimedes-auger.scad v2 ──────────
OUTER_R         = 10.0   # mm
INNER_R         = 8.0    # mm (outer_diameter - 2*wall_thickness) / 2
WALL            = 2.0    # mm
HEIGHT          = 100.0  # mm
TOP_CAP_H       = 6.0    # mm  (z = 94 to 100)
M3_BOSS_R       = 4.0    # mm  boss radius
M3_BOSS_H       = 6.0    # mm  boss height below cap (z = 88 to 94)
M3_PILOT_D      = 2.5    # mm  pilot hole diameter
M3_PILOT_DEPTH  = 12.0   # mm  = top_cap_h + m3_boss_h
EXIT_D          = 3.0    # mm  CAD diameter (prints ~2.5mm)
BOTTOM_CAP_H    = 6.0    # mm  conical funnel height (z = 0 to 6)
PITCH           = 10.0   # mm/turn
FIN_INNER_R     = 2.0    # mm
FIN_THICK       = 2.0    # mm
HELIX_START     = BOTTOM_CAP_H                             # 6 mm
HELIX_END       = HEIGHT - TOP_CAP_H - M3_BOSS_H           # 88 mm
HELIX_HEIGHT    = HELIX_END - HELIX_START                  # 82 mm
TURNS           = HELIX_HEIGHT / PITCH                     # 8.2

# Funnel geometry (bottom_funnel module):
#   r1 = exit_hole_d/2 = 1.5mm at z=0 (exit)
#   r2 = inner_r - 0.5 = 7.5mm at z=6 (top of funnel)
FUNNEL_R_BOTTOM = EXIT_D / 2        # 1.5 mm
FUNNEL_R_TOP    = INNER_R - 0.5     # 7.5 mm

# ── SVG layout ────────────────────────────────────────────────────────
SCALE   = 5.0   # px per mm
PAD     = 60    # px

# Cross-section panel
CS_X0   = PAD
CS_W    = int(2 * OUTER_R * SCALE)   # 100px
CS_H    = int(HEIGHT * SCALE)         # 500px
CS_CX   = CS_X0 + CS_W // 2

# Detail insets panel (right of cross-section)
DET_X0  = CS_X0 + CS_W + PAD * 2
DET_W   = 120

# Helix projection panel
HX_X0   = DET_X0 + DET_W + PAD
HX_W    = int(2 * OUTER_R * SCALE)   # 100px
HX_CX   = HX_X0 + HX_W // 2

TOTAL_W = HX_X0 + HX_W + PAD * 2
TOTAL_H = CS_H + PAD * 3 + 50

# ── Helpers ───────────────────────────────────────────────────────────
def mm(v):
    return v * SCALE

def y(z_mm):
    """Z coord (mm, 0=bottom) → SVG y (0=top of diagram)."""
    return PAD + 40 + (HEIGHT - z_mm) * SCALE

lines = []

def svg_open():
    lines.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{TOTAL_W}" height="{TOTAL_H}" '
        f'style="background:white; font-family:Arial,sans-serif;">'
    )

def svg_close():
    lines.append('</svg>')

def rect(x, yp, w, h, fill, stroke='#333', sw=1.5, opacity=1.0, rx=0):
    lines.append(
        f'<rect x="{x:.1f}" y="{yp:.1f}" width="{w:.1f}" height="{h:.1f}" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}" '
        f'opacity="{opacity}" rx="{rx}"/>'
    )

def poly(points_mm_list, fill='none', stroke='#333', sw=1.5, opacity=1.0):
    """points_mm_list: list of (svg_x, svg_y) already in px."""
    pts = ' '.join(f'{px:.1f},{py:.1f}' for px, py in points_mm_list)
    lines.append(
        f'<polygon points="{pts}" fill="{fill}" stroke="{stroke}" '
        f'stroke-width="{sw}" opacity="{opacity}"/>'
    )

def polyline(pts, color, sw=1.5, opacity=1.0):
    pts_str = ' '.join(f'{px:.1f},{py:.1f}' for px, py in pts)
    lines.append(
        f'<polyline points="{pts_str}" fill="none" stroke="{color}" '
        f'stroke-width="{sw}" opacity="{opacity}"/>'
    )

def line(x1, y1, x2, y2, color='#333', sw=1.5, dash=''):
    d = f' stroke-dasharray="{dash}"' if dash else ''
    lines.append(
        f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
        f'stroke="{color}" stroke-width="{sw}"{d}/>'
    )

def text(x, yp, content, size=11, anchor='middle', color='#222', bold=False, italic=False):
    style = f'font-size:{size}px; text-anchor:{anchor}; fill:{color};'
    if bold:   style += ' font-weight:bold;'
    if italic: style += ' font-style:italic;'
    lines.append(f'<text x="{x:.1f}" y="{yp:.1f}" style="{style}">{content}</text>')

def arrow(x1, y1, x2, y2, color='#333', sw=1.2):
    line(x1, y1, x2, y2, color=color, sw=sw)
    dx, dy = x2 - x1, y2 - y1
    L = math.hypot(dx, dy)
    if L < 1:
        return
    ux, uy = dx / L, dy / L
    px, py = -uy, ux
    s = 5
    pts = (f'{x2:.1f},{y2:.1f} '
           f'{x2-ux*s+px*3:.1f},{y2-uy*s+py*3:.1f} '
           f'{x2-ux*s-px*3:.1f},{y2-uy*s-py*3:.1f}')
    lines.append(f'<polygon points="{pts}" fill="{color}"/>')

def dim_v(x, y1, y2, label, side='right'):
    arrow(x, y1, x, y1 + 5, color='#888', sw=1)
    arrow(x, y2, x, y2 - 5, color='#888', sw=1)
    line(x, y1, x, y2, color='#888', sw=1, dash='4,3')
    lx = x + 8 if side == 'right' else x - 8
    anchor = 'start' if side == 'right' else 'end'
    text(lx, (y1 + y2) / 2 + 4, label, size=9, anchor=anchor, color='#666')

def dim_h(x1, x2, yp, label):
    arrow(x1, yp, x1 + 5, yp, color='#888', sw=1)
    arrow(x2, yp, x2 - 5, yp, color='#888', sw=1)
    line(x1, yp, x2, yp, color='#888', sw=1, dash='4,3')
    text((x1 + x2) / 2, yp - 4, label, size=9, color='#666')

# ── BUILD SVG ─────────────────────────────────────────────────────────
svg_open()

# Title
text(TOTAL_W // 2, 22, 'Archimedes Auger v2 — Design Preview', size=15, bold=True)
text(TOTAL_W // 2, 38,
     '20mm OD × 100mm height | M3 spindle mount (12mm engagement) | '
     '3.0mm exit hole (conical funnel) | PLA/PETG FDM',
     size=10, color='#555', italic=True)

# ══════════════════════════════════════════════════════════════════════
# PANEL 1: CROSS-SECTION (halved — left side = left wall, right side = right wall)
# Shows internal geometry as if the auger is cut in half vertically.
# ══════════════════════════════════════════════════════════════════════
text(CS_CX, y(HEIGHT) - 16, 'Cross-Section (Half View)', size=12, bold=True)

left_x   = CS_X0                            # outer left wall x
right_x  = CS_X0 + int(2 * OUTER_R * SCALE) # outer right wall x
cx       = CS_CX

wall_w_px = mm(WALL)
inner_left  = left_x + wall_w_px
inner_right = right_x - wall_w_px

# ─── Outer tube walls (full height, left + right bands) ──────────────
rect(left_x,    y(HEIGHT), wall_w_px, mm(HEIGHT), '#a8c8e8', '#1a5276', sw=2)
rect(inner_right, y(HEIGHT), wall_w_px, mm(HEIGHT), '#a8c8e8', '#1a5276', sw=2)

# ─── Empty interior (hollow tube body, z=6 to z=88) ──────────────────
rect(inner_left, y(HELIX_END), mm(INNER_R * 2), mm(HELIX_HEIGHT),
     '#eef5fb', stroke='none')

# ─── Conical funnel bottom (z=0 to z=6) ──────────────────────────────
# Solid outer block at full OD, then conical void cut out of it.
# Void: r1=1.5mm at z=0, r2=7.5mm at z=6
# Left side of section: funnel left wall is a diagonal line from
#   (cx - mm(FUNNEL_R_BOTTOM), y(0)) to (inner_left, y(BOTTOM_CAP_H))
# Right side mirrors it.
funnel_pts_right = [
    (inner_right,              y(BOTTOM_CAP_H)),
    (right_x,                  y(BOTTOM_CAP_H)),
    (right_x,                  y(0)),
    (cx + mm(FUNNEL_R_BOTTOM), y(0)),
]
funnel_pts_left = [
    (left_x,                   y(BOTTOM_CAP_H)),
    (inner_left,               y(BOTTOM_CAP_H)),
    (cx - mm(FUNNEL_R_BOTTOM), y(0)),
    (left_x,                   y(0)),
]
poly(funnel_pts_left,  fill='#2e86c1', stroke='#1a5276', sw=2)
poly(funnel_pts_right, fill='#2e86c1', stroke='#1a5276', sw=2)

# Exit hole gap at very bottom (open)
rect(cx - mm(FUNNEL_R_BOTTOM), y(0), mm(EXIT_D), 3,
     fill='white', stroke='none')

# Funnel void interior (show it as lighter color)
funnel_void_pts = [
    (inner_left,               y(BOTTOM_CAP_H)),
    (inner_right,              y(BOTTOM_CAP_H)),
    (cx + mm(FUNNEL_R_BOTTOM), y(0)),
    (cx - mm(FUNNEL_R_BOTTOM), y(0)),
]
poly(funnel_void_pts, fill='#ddeeff', stroke='none', opacity=0.6)

# Diagonal funnel wall lines (the actual slanted surface)
line(inner_left,               y(BOTTOM_CAP_H),
     cx - mm(FUNNEL_R_BOTTOM), y(0),
     color='#1a5276', sw=1.5)
line(inner_right,              y(BOTTOM_CAP_H),
     cx + mm(FUNNEL_R_BOTTOM), y(0),
     color='#1a5276', sw=1.5)

# ─── Top cap solid disc (z=94 to z=100) ──────────────────────────────
rect(left_x, y(HEIGHT), mm(2 * OUTER_R), mm(TOP_CAP_H),
     fill='#2e86c1', stroke='#1a5276', sw=2)

# ─── M3 boss cylinder (z=88 to z=94, r=0 to 4mm) ────────────────────
# Boss is only at center: from cx-mm(M3_BOSS_R) to cx+mm(M3_BOSS_R)
boss_left  = cx - mm(M3_BOSS_R)
boss_right = cx + mm(M3_BOSS_R)
rect(boss_left, y(HELIX_END + M3_BOSS_H), mm(2 * M3_BOSS_R), mm(M3_BOSS_H),
     fill='#2e86c1', stroke='#1a5276', sw=1.5)

# ─── M3 pilot hole void (z=88 to z=100, d=2.5mm) ─────────────────────
pilot_left  = cx - mm(M3_PILOT_D / 2)
pilot_right = cx + mm(M3_PILOT_D / 2)
rect(pilot_left, y(HEIGHT), mm(M3_PILOT_D), mm(M3_PILOT_DEPTH) + 2,
     fill='white', stroke='none')
# Draw the hole outline
line(pilot_left,  y(HEIGHT),                  pilot_left,  y(HEIGHT - M3_PILOT_DEPTH), '#555', 1)
line(pilot_right, y(HEIGHT),                  pilot_right, y(HEIGHT - M3_PILOT_DEPTH), '#555', 1)
line(pilot_left,  y(HEIGHT - M3_PILOT_DEPTH), pilot_right, y(HEIGHT - M3_PILOT_DEPTH), '#555', 1)

# ─── Loading slots (show 2 of 4, visible in section) ─────────────────
# Slots at radius=5mm, width=4mm, length=6mm, cut through top cap
slot_r   = 5.0
slot_w   = 4.0
slot_l   = 6.0
# Left slot visible at x = cx - mm(slot_r) - mm(slot_l/2) ... + mm(slot_l/2)
for sign in [-1, 1]:
    sx = cx + sign * mm(slot_r) - mm(slot_w / 2)
    rect(sx, y(HEIGHT), mm(slot_w), mm(TOP_CAP_H) + 2,
         fill='white', stroke='none')

# ─── Helical fin cross-sections (horizontal cuts at each half-pitch) ──
n_fins = int((HELIX_END - HELIX_START) / (PITCH / 2)) + 1
for i in range(n_fins):
    z_fin = HELIX_START + i * (PITCH / 2)
    if z_fin > HELIX_END:
        break
    fy = y(z_fin)
    # Left fin: from inner_left to inner_left + mm(INNER_R - FIN_INNER_R)
    # Right fin: mirror
    fin_len = mm(INNER_R - FIN_INNER_R)
    line(inner_left,            fy, inner_left + fin_len,            fy, '#c0392b', 2)
    line(inner_right - fin_len, fy, inner_right,                     fy, '#c0392b', 2)

# ─── Outer wall outlines ──────────────────────────────────────────────
line(left_x,   y(0), left_x,   y(HEIGHT), '#1a5276', 2)
line(right_x,  y(0), right_x,  y(HEIGHT), '#1a5276', 2)
line(left_x,   y(0), right_x,  y(0),      '#1a5276', 2)

# ─── Dimension callouts ───────────────────────────────────────────────
dim_v(right_x + 28, y(HEIGHT), y(0), '100mm', 'right')
dim_h(left_x, right_x, y(0) + 20, '20mm OD')
dim_h(left_x, inner_left, y(HEIGHT / 3), '2mm')
dim_v(left_x - 20, y(BOTTOM_CAP_H), y(0), '6mm', 'left')
dim_v(left_x - 20, y(HEIGHT), y(HEIGHT - TOP_CAP_H), '6mm cap', 'left')
dim_v(left_x - 38, y(HEIGHT), y(HEIGHT - M3_PILOT_DEPTH), '12mm M3', 'left')

p1 = HELIX_START + PITCH * 2
p2 = p1 + PITCH
dim_v(inner_left - 18, y(p1), y(p2), '10mm pitch', 'left')

# ─── Labels ───────────────────────────────────────────────────────────
text(cx, y(0) + 32,         f'Exit hole dia.{EXIT_D}mm (conical funnel)',
     size=9, color='#27ae60', bold=True)
text(cx, y(HEIGHT) - 5,     f'M3 pilot hole dia.{M3_PILOT_D}mm x 12mm deep + 4 loading slots',
     size=9, color='#7d3c98', bold=True)
text(inner_left - 5, y(HELIX_START + 10),   'Helical fin', size=9, color='#c0392b', anchor='end')
text(inner_left - 5, y(HELIX_START + 10) + 11, '(8.2 turns)', size=8, color='#888', anchor='end')
text(cx + mm(M3_BOSS_R) + 5, y(HELIX_END + M3_BOSS_H / 2), 'M3 boss',
     size=8, color='#2c7fba', anchor='start')
text(cx - mm(INNER_R) - 5,  y(BOTTOM_CAP_H / 2), 'Conical',
     size=8, color='#1a5276', anchor='end')
text(cx - mm(INNER_R) - 5,  y(BOTTOM_CAP_H / 2) + 10, 'funnel',
     size=8, color='#1a5276', anchor='end')

# ══════════════════════════════════════════════════════════════════════
# PANEL 2: DETAIL INSETS (top mount and bottom funnel)
# ══════════════════════════════════════════════════════════════════════
DET_SCALE = 8.0   # px/mm for detail views (larger)

def dy(z_mm, z_base, panel_top_y):
    """Detail panel y: z=z_base is at panel_top_y + panel_height."""
    return panel_top_y + (z_base - z_mm) * DET_SCALE

det_cx = DET_X0 + DET_W // 2

text(det_cx, y(HEIGHT) - 16, 'Detail Views', size=11, bold=True)

# ── Detail A: Bottom funnel (z=0 to z=8) ─────────────────────────────
det_a_z_top = 8.0
det_a_h_px  = int(det_a_z_top * DET_SCALE)
det_a_y0    = y(HEIGHT) + 10   # top of detail panel in SVG px

text(det_cx, det_a_y0 - 2, 'Detail A — Funnel Bottom', size=9, bold=True, color='#333')

dcx = det_cx

# Outer wall left/right
dwall = WALL * DET_SCALE
dout_l = dcx - OUTER_R * DET_SCALE
dout_r = dcx + OUTER_R * DET_SCALE
din_l  = dout_l + dwall
din_r  = dout_r - dwall

def da_y(z):
    return det_a_y0 + (det_a_z_top - z) * DET_SCALE

# Left outer wall
rect(dout_l, da_y(det_a_z_top), dwall, det_a_h_px, '#a8c8e8', '#1a5276', sw=1.5)
# Right outer wall
rect(din_r,  da_y(det_a_z_top), dwall, det_a_h_px, '#a8c8e8', '#1a5276', sw=1.5)
# Funnel solid left
poly([
    (dout_l,                              da_y(BOTTOM_CAP_H)),
    (din_l,                               da_y(BOTTOM_CAP_H)),
    (dcx - FUNNEL_R_BOTTOM * DET_SCALE,   da_y(0)),
    (dout_l,                              da_y(0)),
], fill='#2e86c1', stroke='#1a5276', sw=1.5)
# Funnel solid right
poly([
    (din_r,                               da_y(BOTTOM_CAP_H)),
    (dout_r,                              da_y(BOTTOM_CAP_H)),
    (dout_r,                              da_y(0)),
    (dcx + FUNNEL_R_BOTTOM * DET_SCALE,   da_y(0)),
], fill='#2e86c1', stroke='#1a5276', sw=1.5)
# Void
poly([
    (din_l,                               da_y(BOTTOM_CAP_H)),
    (din_r,                               da_y(BOTTOM_CAP_H)),
    (dcx + FUNNEL_R_BOTTOM * DET_SCALE,   da_y(0)),
    (dcx - FUNNEL_R_BOTTOM * DET_SCALE,   da_y(0)),
], fill='#ddeeff', stroke='none')
# Funnel wall lines
line(din_l, da_y(BOTTOM_CAP_H), dcx - FUNNEL_R_BOTTOM * DET_SCALE, da_y(0), '#1a5276', 1.5)
line(din_r, da_y(BOTTOM_CAP_H), dcx + FUNNEL_R_BOTTOM * DET_SCALE, da_y(0), '#1a5276', 1.5)
# Exit hole
rect(dcx - FUNNEL_R_BOTTOM * DET_SCALE, da_y(0), EXIT_D * DET_SCALE, 3, 'white', 'none')

text(dcx, da_y(BOTTOM_CAP_H) - 4, f'r={FUNNEL_R_TOP}mm at top', size=8, color='#555')
text(dcx, da_y(0) + 14,           f'exit r={FUNNEL_R_BOTTOM}mm', size=8, color='#27ae60', bold=True)

# ── Detail B: M3 boss top mount (z=86 to z=100) ──────────────────────
det_b_z_bot = 86.0
det_b_z_top = HEIGHT
det_b_h     = det_b_z_top - det_b_z_bot
det_b_h_px  = int(det_b_h * DET_SCALE)
det_b_y0    = det_a_y0 + det_a_h_px + 30

text(det_cx, det_b_y0 - 2, 'Detail B — M3 Boss Top Mount', size=9, bold=True, color='#333')

def db_y(z):
    return det_b_y0 + (det_b_z_top - z) * DET_SCALE

# Top cap solid
rect(dout_l, db_y(HEIGHT), 2 * OUTER_R * DET_SCALE, TOP_CAP_H * DET_SCALE,
     '#2e86c1', '#1a5276', sw=1.5)
# M3 boss
boss_l = dcx - M3_BOSS_R * DET_SCALE
boss_r = dcx + M3_BOSS_R * DET_SCALE
rect(boss_l, db_y(HEIGHT - TOP_CAP_H),
     2 * M3_BOSS_R * DET_SCALE, M3_BOSS_H * DET_SCALE,
     '#2e86c1', '#1a5276', sw=1.5)
# Outer walls above boss level
rect(dout_l, db_y(HEIGHT - TOP_CAP_H), dwall,
     (det_b_h - TOP_CAP_H) * DET_SCALE, '#a8c8e8', '#1a5276', sw=1.5)
rect(din_r,  db_y(HEIGHT - TOP_CAP_H), dwall,
     (det_b_h - TOP_CAP_H) * DET_SCALE, '#a8c8e8', '#1a5276', sw=1.5)
# Interior space beside boss
rect(din_l,  db_y(HEIGHT - TOP_CAP_H),
     M3_BOSS_R * DET_SCALE - dwall, (det_b_h - TOP_CAP_H) * DET_SCALE,
     '#eef5fb', stroke='none')
rect(boss_r, db_y(HEIGHT - TOP_CAP_H),
     M3_BOSS_R * DET_SCALE - dwall, (det_b_h - TOP_CAP_H) * DET_SCALE,
     '#eef5fb', stroke='none')
# M3 pilot hole
pilot_l = dcx - (M3_PILOT_D / 2) * DET_SCALE
pilot_r = dcx + (M3_PILOT_D / 2) * DET_SCALE
rect(pilot_l, db_y(HEIGHT), M3_PILOT_D * DET_SCALE,
     M3_PILOT_DEPTH * DET_SCALE + 2, 'white', 'none')
line(pilot_l, db_y(HEIGHT),               pilot_l, db_y(HEIGHT - M3_PILOT_DEPTH), '#555', 1)
line(pilot_r, db_y(HEIGHT),               pilot_r, db_y(HEIGHT - M3_PILOT_DEPTH), '#555', 1)
line(pilot_l, db_y(HEIGHT - M3_PILOT_DEPTH), pilot_r, db_y(HEIGHT - M3_PILOT_DEPTH), '#555', 1)

text(dcx, db_y(HEIGHT - TOP_CAP_H / 2) + 4,   'solid cap 6mm', size=8, color='white', bold=True)
text(dcx, db_y(HEIGHT - TOP_CAP_H - M3_BOSS_H / 2) + 4, 'boss r=4mm', size=8, color='white', bold=True)
text(dcx, db_y(HEIGHT - M3_PILOT_DEPTH) + 14, 'M3 pilot 12mm deep', size=8, color='#555')

# ══════════════════════════════════════════════════════════════════════
# PANEL 3: HELIX FRONT PROJECTION
# ══════════════════════════════════════════════════════════════════════
text(HX_CX, y(HEIGHT) - 16, 'Helix Front Projection', size=12, bold=True)

# Outer tube fill
rect(HX_X0, y(HEIGHT), mm(2 * OUTER_R), mm(HEIGHT),
     '#ddeeff', '#1a5276', sw=2, opacity=0.3)
# Tube walls
rect(HX_X0, y(HEIGHT), mm(WALL), mm(HEIGHT), '#a8c8e8', 'none', opacity=0.7)
rect(HX_X0 + mm(2 * OUTER_R) - mm(WALL), y(HEIGHT), mm(WALL), mm(HEIGHT),
     '#a8c8e8', 'none', opacity=0.7)
line(HX_X0,              y(0), HX_X0,              y(HEIGHT), '#1a5276', 2)
line(HX_X0 + mm(2*OUTER_R), y(0), HX_X0 + mm(2*OUTER_R), y(HEIGHT), '#1a5276', 2)

# Bottom funnel
rect(HX_X0, y(BOTTOM_CAP_H), mm(2 * OUTER_R), mm(BOTTOM_CAP_H),
     '#2e86c1', 'none', opacity=0.6)
# Top cap
rect(HX_X0, y(HEIGHT), mm(2 * OUTER_R), mm(TOP_CAP_H),
     '#2e86c1', 'none', opacity=0.6)
# M3 boss
rect(HX_CX - mm(M3_BOSS_R), y(HEIGHT - TOP_CAP_H),
     mm(2 * M3_BOSS_R), mm(M3_BOSS_H),
     '#3a9bd5', 'none', opacity=0.7)

# Helix paths (outer and inner edges)
n_pts = 500
pts_outer = []
pts_inner = []
for i in range(n_pts + 1):
    t = i / n_pts
    z_val = HELIX_START + t * (HELIX_END - HELIX_START)
    angle = t * TURNS * 2 * math.pi
    xo = (INNER_R - 0.1) * math.cos(angle)
    xi = FIN_INNER_R * math.cos(angle)
    pts_outer.append((HX_CX + mm(xo), y(z_val)))
    pts_inner.append((HX_CX + mm(xi), y(z_val)))

polyline(pts_outer, '#c0392b', sw=2.0)
polyline(pts_inner, '#e74c3c', sw=1.2)

# Exit hole and M3 markers
lines.append(f'<circle cx="{HX_CX:.1f}" cy="{y(0):.1f}" r="5" '
             f'fill="#27ae60" stroke="white" stroke-width="1.5"/>')
lines.append(f'<circle cx="{HX_CX:.1f}" cy="{y(HEIGHT):.1f}" r="5" '
             f'fill="#7d3c98" stroke="white" stroke-width="1.5"/>')

text(HX_X0 + mm(2*OUTER_R) + 8, y(0),        '← Exit 3mm', size=9, color='#27ae60', anchor='start')
text(HX_X0 + mm(2*OUTER_R) + 8, y(HEIGHT)+4,  '← M3 mount', size=9, color='#7d3c98', anchor='start')
text(HX_X0 + mm(2*OUTER_R) + 8, y(HELIX_START + HELIX_HEIGHT/2),
     '8.2 turns', size=9, color='#c0392b', anchor='start')

# ══════════════════════════════════════════════════════════════════════
# SPEC TABLE
# ══════════════════════════════════════════════════════════════════════
ty = TOTAL_H - PAD + 8
specs = [
    ('Outer diam.',     '20 mm'),
    ('Total height',    '100 mm'),
    ('Wall',            '2 mm'),
    ('Inner diam.',     '16 mm'),
    ('Helix pitch',     '10 mm/turn'),
    ('Turns',           '8.2'),
    ('Exit hole (CAD)', 'dia.3.0 mm'),
    ('M3 pilot',        'dia.2.5 x 12mm'),
    ('Boss radius',     '4 mm'),
    ('Funnel r bottom', '1.5 mm'),
    ('Print',           'PLA/PETG 0.2mm vertical'),
]
col_w = (TOTAL_W - 2 * PAD) / len(specs)
for i, (k, v) in enumerate(specs):
    sx = PAD + i * col_w + col_w / 2
    text(sx, ty,      k, size=8, color='#555')
    text(sx, ty + 13, v, size=9, color='#111', bold=True)

line(PAD, ty - 8, TOTAL_W - PAD, ty - 8, color='#ccc', sw=1)

svg_close()

output_path = '/Users/devoranajjar/Github/powder-excavator/cad/auger/preview.svg'
with open(output_path, 'w') as f:
    f.write('\n'.join(lines))

print(f'Saved: {output_path}')
print(f'Canvas: {TOTAL_W} x {TOTAL_H} px')
