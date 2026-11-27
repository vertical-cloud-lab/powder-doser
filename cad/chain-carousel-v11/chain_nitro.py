"""The chain v11 models, against the chain to buy (Sam, PR #185, 2026-11-25: "we're not sure the chain model is correct. Find a cheap but
still good quality chain online, link it here, and apply those dimensions to the chain in the model so it matches an actual chain we can
actually buy").

Nitro Chain RC35-1R-10FT (N2 series), $23.53 per 10 ft roll, read 2026-11-26: https://www.nitrochain.com/35-roller-chain-10ft
Its A-1 attachment connecting link CL35-A1, $2.55: https://www.nitrochain.com/35-a1-standard-attachment-connecting-link
Its connecting link CL35, $0.79: https://www.nitrochain.com/35-standard-connecting-link

Draws true sections of v11's link builders (parts.chain_outer_link / chain_inner_link / chain_a1_link): the side view (the plates'
outline in the chain's plane) and the cut through the pins' plane (widths), with Nitro's numbers next to each.

    python chain_nitro.py   -> renders/v11/chain_nitro_v11.png
"""
from __future__ import annotations

from pathlib import Path

import cadquery as cq
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt               # noqa: E402
from matplotlib.patches import PathPatch      # noqa: E402
from matplotlib.path import Path as MPath     # noqa: E402
import numpy as np                            # noqa: E402

import parts as PT                            # noqa: E402
from params import (A1_C, A1_HOLE_C, A1_HOLE_D, A1_TAB_L, A1_X, BUSH_D, CHAIN_PIN_D, INNER_W, OUTER_W, P, PIN_LEN, PIN_LEN_CL,  # noqa: E402
                    PLATE_H, PLATE_H_OUT, PLATE_T, PLATE_WAIST, PLATE_WAIST_OUT, W_IN)

OUT = Path(__file__).resolve().parent / "renders" / "v11"
OUT.mkdir(parents=True, exist_ok=True)
IN = 25.4


def _loop(wire, axes):
    n = int(max(24, min(1200, wire.Length() / 0.03)))
    pts = wire.positions(np.linspace(0.0, 1.0, n))
    return np.array([(getattr(p, axes[0]), getattr(p, axes[1])) for p in pts])


def section(shape, normal, at):
    d = {"x": (1.0, 0.0, 0.0), "y": (0.0, 1.0, 0.0), "z": (0.0, 0.0, 1.0)}[normal]
    face = cq.Face.makePlane(400.0, 400.0, basePnt=tuple(at * v for v in d), dir=d)
    axes = {"x": ("y", "z"), "y": ("x", "z"), "z": ("x", "y")}[normal]
    res = shape.intersect(face)
    return [(_loop(f.outerWire(), axes), [_loop(w, axes) for w in f.innerWires()]) for f in res.Faces()]


def patch(polys, dx=0.0, dy=0.0, **kw):
    verts, codes = [], []
    for o, holes in polys:
        for ring in [o] + holes:
            r = ring + np.array([dx, dy])
            verts += r.tolist() + [r[0].tolist()]
            codes += [MPath.MOVETO] + [MPath.LINETO] * (len(r) - 1) + [MPath.CLOSEPOLY]
    return PathPatch(MPath(verts, codes), **kw)


def solid(w):
    v = w.vals()
    return v[0] if len(v) == 1 else cq.Compound.makeCompound(v)


def main():
    outer, inner, a1 = solid(PT.chain_outer_link()), solid(PT.chain_inner_link()), solid(PT.chain_a1_link())
    fig = plt.figure(figsize=(12.8, 7.6), dpi=110)
    fig.text(0.04, 0.955, "v11's chain: Nitro RC35-1R-10FT ($23.53 per 10 ft) and CL35-A1 links", fontsize=15, weight="bold", color=(0.08, 0.12, 0.3))
    fig.text(0.04, 0.918, "true sections of the model's link builders, with Nitro's published dimensions (inches, then mm)", fontsize=10.5, color=(0.3, 0.3, 0.35))
    fig.text(0.985, 0.955, "chain carousel v11 · PR #185 · 2026-11-26", fontsize=9, color=(0.5, 0.5, 0.55), ha="right")
    a1x = fig.add_axes([0.04, 0.47, 0.58, 0.40])
    a2x = fig.add_axes([0.66, 0.47, 0.32, 0.40])
    a3x = fig.add_axes([0.04, 0.04, 0.94, 0.36])
    # side view: inner link, outer link, A-1 connecting link, each in the chain's plane (cut through the near plate)
    zc_o = OUTER_W / 2 - PLATE_T / 2
    zc_i = INNER_W / 2 - PLATE_T / 2
    for k, (shape, zc, dx, col, nm) in enumerate(((outer, zc_o, 0.0, (0.55, 0.57, 0.6), "outer link"), (inner, zc_i, P, (0.75, 0.76, 0.78), "inner link"),
                                                    (outer, zc_o, 2 * P, (0.55, 0.57, 0.6), "outer link"), (a1, zc_o, 3 * P, (0.36, 0.45, 0.62), "A-1 connecting link (CL35-A1)"))):
        a1x.add_patch(patch(section(shape, "z", zc), dx=dx, fc=col, ec=(0.1, 0.1, 0.15), lw=0.7, alpha=0.95, zorder=2 + (k % 2 == 0)))
    a1x.set_xlim(-9.5, 3 * P + 12)
    a1x.set_ylim(-7.5, 11.5)
    a1x.set_aspect("equal")
    a1x.set_title("Side view (the chain's plane): waisted plates; the connecting link's plates straight-sided", fontsize=10.5, loc="left")
    a1x.annotate("", xy=(0.0, -6.2), xytext=(P, -6.2), arrowprops=dict(arrowstyle="<->", lw=0.8))
    a1x.text(P / 2, -7.3, f'pitch 0.375" ({P:.3f})', ha="center", fontsize=8.5)
    a1x.annotate("", xy=(P / 2 - P / 2, -PLATE_H / 2), xytext=(-P / 2, PLATE_H / 2), arrowprops=dict(arrowstyle="-", lw=0.0))
    a1x.annotate("", xy=(3 * P + 7.0, -PLATE_H / 2), xytext=(3 * P + 7.0, PLATE_H / 2), arrowprops=dict(arrowstyle="<->", lw=0.8))
    a1x.text(3 * P + 7.6, -6.0, f'h2 0.346" ({PLATE_H:.2f})', ha="center", va="center", fontsize=8.5)
    a1x.annotate(f"inner plates: waist {PLATE_WAIST:.2f}; outer plates {PLATE_H_OUT:.2f} high,\nwaist {PLATE_WAIST_OUT:.2f} (McMaster 6261K172's CAD, read\nthrough the Pi 2026-11-27; Nitro publishes neither)",
                 xy=(P * 1.5, PLATE_WAIST / 2), xytext=(-9.2, 7.6), fontsize=7.6, arrowprops=dict(arrowstyle="->", lw=0.8))
    a1x.annotate("A-1 tab, bent along the pins\n(seen end on here)", xy=(3 * P, A1_C), xytext=(2.0 * P, 10.4), fontsize=8.5, arrowprops=dict(arrowstyle="->", lw=0.8))
    for i, nm in enumerate(("outer", "inner", "outer", "A-1 (connecting)")):
        a1x.text(i * P, -4.9, nm, ha="center", fontsize=7.5, color=(0.25, 0.25, 0.3))
    a1x.grid(alpha=0.2, lw=0.5)
    # cut through the pins: widths
    for k, (shape, dx, col) in enumerate(((outer, 0.0, (0.55, 0.57, 0.6)), (a1, 16.0, (0.36, 0.45, 0.62)))):
        a2x.add_patch(patch(section(shape, "x", -P / 2), dx=dx, fc=col, ec=(0.1, 0.1, 0.15), lw=0.6))
    a2x.add_patch(patch(section(inner, "x", -P / 2 + 0.001), dx=-16.0, fc=(0.75, 0.76, 0.78), ec=(0.1, 0.1, 0.15), lw=0.6))
    a2x.set_xlim(-24, 26)
    a2x.set_ylim(-16, 16)
    a2x.set_aspect("equal")
    a2x.set_title("Cut through a pin: the widths", fontsize=10.5, loc="left")
    a2x.text(-16, -15.4, f'inner link\nb1 3/16" ({W_IN:.2f})\nbushing 0.200" ({BUSH_D:.2f})', ha="center", fontsize=7.6)
    a2x.text(0, -15.4, f'riveted pins\nL 0.488" ({PIN_LEN:.2f})\npin 0.141" ({CHAIN_PIN_D:.2f})', ha="center", fontsize=7.6)
    a2x.text(16, -15.4, f'connecting link\n0.518" ({PIN_LEN_CL:.2f}), clip side\nT 0.050" ({PLATE_T:.2f})', ha="center", fontsize=7.6)
    a2x.text(16, 14.2, f'A-1 tab: S 0.250", C 0.375",\nX 0.562", N 0.312", hole 0.133"', ha="center", fontsize=7.4, color=(0.2, 0.25, 0.45))
    a2x.grid(alpha=0.2, lw=0.5)
    # table
    a3x.axis("off")
    rows = [("Dimension", "Nitro RC35 / CL35 / CL35-A1 (published)", "v2-v10 model", "v11 model"),
            ("Pitch", '0.375" (9.525)', "9.525", "9.525"),
            ("Bushing diameter (#35 has no rollers)", '0.200" (5.08)', "5.08", "5.08"),
            ("Width between inner plates, b1", '3/16" (4.78)', "4.78", "4.78"),
            ("Pin diameter, d2", '0.141" (3.58)', "3.58", "3.58"),
            ("Plate height, h2 (inner / outer)", '0.346" (8.79), one value', "8.79 / 8.79", f"8.79 / {PLATE_H_OUT:.2f} (McMaster's CAD)"),
            ("Plate thickness, T", '0.050" (1.27)', "1.27", "1.27"),
            ("Width over riveted pins, L", '0.488" (12.40)', "12.40", "12.40"),
            ("Width over a connecting link (CL35, CL35-A1)", '0.518" (13.16)', "12.40 (as riveted)", "13.16"),
            ("Plates' waist (inner / outer)", "waisted (figure-8), not dimensioned; CL plates straight", "7.69, all plates", f"{PLATE_WAIST:.2f} / {PLATE_WAIST_OUT:.2f}; CL straight"),
            ("A-1 tab: S / C / X / N / hole", '0.250 / 0.375 / 0.562 / 0.312 / 0.133"', "same", "same")]
    tb = a3x.table(cellText=rows[1:], colLabels=rows[0], loc="upper left", cellLoc="left", colWidths=[0.30, 0.31, 0.17, 0.22])
    tb.auto_set_font_size(False)
    tb.set_fontsize(8.6)
    tb.scale(1.0, 1.32)
    for (r, cidx), cell in tb.get_celld().items():
        cell.set_edgecolor((0.8, 0.8, 0.84))
        if r == 0:
            cell.set_facecolor((0.88, 0.9, 0.96))
            cell.set_text_props(weight="bold")
        elif rows[r][2] != rows[r][3]:
            cell.set_facecolor((1.0, 0.96, 0.86))
    fig.text(0.04, 0.012, "Sources: nitrochain.com/35-roller-chain-10ft (P, b1, d1, d2, L, h2), its size chart (T), /35-standard-connecting-link (0.518\"), "
             "/35-a1-standard-attachment-connecting-link (A-1). Highlighted rows changed in v11.", fontsize=8, color=(0.35, 0.35, 0.4))
    fig.savefig(OUT / "chain_nitro_v11.png")
    print("chain_nitro_v11.png")


if __name__ == "__main__":
    main()
