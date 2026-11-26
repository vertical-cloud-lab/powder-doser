"""Profile views of v11's keyed rail and door ramp (Sam, PR #185, 2026-11-25: "I'm still confused about how the T rail thing works. Give
me a profile view. Why is there a ramp? I was assuming each carriage would just move straight through it--I think a ramp would be
helpful for alignment ... not lifting if it's not necessary.").

True sections of the v11 CAD (OCC: each solid cut by a plane), drawn in 2-D with matplotlib, seen with the station's up (the loop's
inside) at the top:
- top left: the rail along the travel, cut through the T's middle (Sam x = 60): the T slides in from the right, the way the machine
  runs, through the slot's flared mouth and along level lips. Nothing lifts it.
- top right: the rail across the travel, cut at the station (Sam y = 0): the T's head under the EC's ceiling, over the lips, the stem
  between them, with the clearances.
- bottom: the door ramp along the travel, cut through the door rod (Sam x = -2.85): the lips catch the rod's head and draw it 6 mm
  toward the loop, which opens the shutter; this is the one ramp that moves something.
Positions come from the model: the module's offset along the run, parts11.door_open_at for the door.

    python rail_profile.py [--preview]   -> renders/v11/rail_profile_v11.{gif,mp4} (+ rail_profile_v11.png, the mid-entry still)
"""
from __future__ import annotations

import sys
from pathlib import Path

import cadquery as cq
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt               # noqa: E402
from matplotlib.patches import PathPatch      # noqa: E402
from matplotlib.path import Path as MPath     # noqa: E402
import numpy as np                            # noqa: E402

import layout as L                            # noqa: E402
import parts3 as P3                           # noqa: E402
import parts10 as P10                         # noqa: E402
import parts11 as P11                         # noqa: E402
from params import (DOOR11_HEAD, DOOR11_HEAD_Z0, DOOR_TRAVEL, RAIL11_CLEAR, RAIL11_FLAT, RAIL11_FUNNEL, RAIL11_FUNNEL_L,  # noqa: E402
                    RAIL11_LIP_GAP, T11_HEAD_X, T11_HEAD_Z, T11_HY, DOOR11_RAMP, DOOR11_RAMP_FLAT, DOOR11_SLOT, DOOR11_LIP_W, RAIL11_FUNNEL_DOWN)

HERE = Path(__file__).resolve().parent
OUT = HERE / "renders" / "v11"
OUT.mkdir(parents=True, exist_ok=True)
COL = {"ec": (0.20, 0.45, 0.95), "t": (0.95, 0.55, 0.12), "plate": (0.10, 0.25, 0.85), "door": (0.18, 0.18, 0.20), "rod": (0.55, 0.57, 0.60),
       "house": (0.95, 0.55, 0.12), "ghost": (0.86, 0.87, 0.90)}
XT = 54.5                                         # through a lip and the T's head over it (the stem runs between the lips at x 57-63)
XR = P11.DOOR11_ROD_X                             # the door rod, its housing and shutter
XL = XR - DOOR11_SLOT / 2 - DOOR11_LIP_W / 2      # through one of the door ramp's lips and the rod's head over it


def _loop(wire, axes) -> np.ndarray:
    n = int(max(24, min(900, wire.Length() / 0.1)))
    pts = wire.positions(np.linspace(0.0, 1.0, n))
    return np.array([(getattr(p, axes[0]), getattr(p, axes[1])) for p in pts])


def section(shape: cq.Shape, normal: str, at: float) -> list:
    """Faces of a solid cut by the plane <normal> = at: [(outer, [holes])] in the plane's two other axes (x-plane -> (y, z); y-plane ->
    (x, z))."""
    d = {"x": (1.0, 0.0, 0.0), "y": (0.0, 1.0, 0.0)}[normal]
    base = tuple(at * v for v in d)
    face = cq.Face.makePlane(2000.0, 2000.0, basePnt=base, dir=d)
    axes = ("y", "z") if normal == "x" else ("x", "z")
    try:
        res = shape.intersect(face)
    except Exception:                              # noqa: BLE001
        return []
    out = []
    for f in res.Faces():
        out.append((_loop(f.outerWire(), axes), [_loop(w, axes) for w in f.innerWires()]))
    return out


def patch(polys, dy=0.0, dz=0.0, **kw):
    verts, codes = [], []
    for o, holes in polys:
        for ring in [o] + holes:
            r = ring + np.array([dy, dz])
            r = np.c_[r[:, 0], -r[:, 1]]                  # Sam z toward the plate -> draw the loop's inside up
            verts += r.tolist() + [r[0].tolist()]
            codes += [MPath.MOVETO] + [MPath.LINETO] * (len(r) - 1) + [MPath.CLOSEPOLY]
    return PathPatch(MPath(verts, codes), **kw) if verts else None


def solid(w):
    v = w.vals()
    return v[0] if len(v) == 1 else cq.Compound.makeCompound(v)


EC = solid(P11.ec_v11(L.SY_P16_11))
TB = solid(P11.t_bracket_v11())
PLATE = solid(L.reference_parts()["sam_mounting_plate"])
SHUT = solid(P10.door_shutter_v10())
HOUSE = solid(P10.door_housing_v10())
ROD = solid(P11.door_rod_v11())
HEAD = solid(P11.door_head_v11())

S_EC_X = section(EC, "x", XT)
S_EC_Y = section(EC, "y", 0.0)
S_EC_D = section(EC, "x", XL)
S_T_X = section(TB, "x", XT)
S_T_Y = section(TB, "y", 0.0)
S_PL_X = section(PLATE, "x", XT)
S_PL_Y = section(PLATE, "y", 0.0)
S_HOUSE = section(HOUSE, "x", XR)
S_ROD = section(ROD, "x", XR)
S_HEAD = section(HEAD, "x", XL)
S_SHUT = section(SHUT, "x", XR)


def draw(off: float, path=None, note: str = ""):
    """off: the arriving module's centre, mm from the station along Sam y (positive: still coming in)."""
    fig = plt.figure(figsize=(12.8, 7.2), dpi=100)
    gs = fig.add_gridspec(2, 2, width_ratios=[1.75, 1.0], height_ratios=[1.0, 0.82], left=0.05, right=0.985, top=0.86, bottom=0.07,
                          wspace=0.12, hspace=0.42)
    a1, a2, a3 = fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1]), fig.add_subplot(gs[1, :])
    fig.text(0.05, 0.955, "v11's keyed rail and door ramp in profile (true sections of the CAD)", fontsize=15, weight="bold", color=(0.08, 0.12, 0.3))
    fig.text(0.05, 0.915, "the station's inside-the-loop side up; the module arrives from the right, the way the machine runs" + (f"   |   {note}" if note else ""),
             fontsize=10.5, color=(0.25, 0.25, 0.3))
    fig.text(0.985, 0.955, "chain carousel v11 · PR #185 · 2026-11-25", fontsize=9, color=(0.5, 0.5, 0.55), ha="right")
    # 1. along the travel at x = 60
    for polys, c, z, dyy in ((S_PL_X, COL["plate"], 1, off), (S_EC_X, COL["ec"], 2, 0.0), (S_T_X, COL["t"], 3, off)):
        p = patch(polys, dy=dyy, fc=c, ec=(0.1, 0.1, 0.15), lw=0.6, alpha=0.9 if c != COL["plate"] else 0.35, zorder=z)
        if p:
            a1.add_patch(p)
    a1.set_xlim(-36, 36)
    a1.set_ylim(14.5, 35.5)
    a1.set_aspect("equal")
    a1.set_title("1. Along the travel, through a lip and the T's head: straight through, level lips", fontsize=11, loc="left")
    a1.set_xlabel("along the run (mm from the station)", fontsize=9)
    a1.set_ylabel("from the auger's axis, toward the loop (mm)", fontsize=9)
    zl = -(T11_HEAD_Z[0] + RAIL11_LIP_GAP)
    BB = dict(boxstyle="round,pad=0.25", fc="white", ec=(0.75, 0.75, 0.8), lw=0.6, alpha=0.92)
    a1.annotate("lips level over the straight part:\nthe T never rides up, nothing lifts", xy=(-3.0, zl - 0.15), xytext=(-34.0, 30.0), fontsize=8.6,
                arrowprops=dict(arrowstyle="->", lw=0.8), bbox=BB, zorder=8)
    ye = RAIL11_FLAT + RAIL11_FUNNEL_L
    a1.annotate(f"flared mouth over {RAIL11_FUNNEL_L:g} mm: {RAIL11_FUNNEL:g} mm wider sideways and toward the loop,\n{RAIL11_FUNNEL_DOWN:g} mm toward the plate, so a T a little off line is steered\nto the middle (alignment only)",
                xy=(-(ye - 1.0), zl - 1.0), xytext=(-34.0, 15.2), fontsize=8.2, arrowprops=dict(arrowstyle="->", lw=0.8), bbox=BB, zorder=8)

    a1.text(-35, 33.8, "EC (fixed at the station)", fontsize=8.5, color=COL["ec"])
    a1.text(off - 6, 31.0 if abs(off) > 13 else 30.6, "T-bracket", fontsize=8.5, color=(0.6, 0.3, 0.0))
    # 2. across the travel at the station
    for polys, c, z in ((S_PL_Y, COL["plate"], 1), (S_EC_Y, COL["ec"], 2)):
        p = patch(polys, fc=c, ec=(0.1, 0.1, 0.15), lw=0.6, alpha=0.9 if c != COL["plate"] else 0.35, zorder=z)
        if p:
            a2.add_patch(p)
    if abs(off) <= T11_HY:
        p = patch(S_T_Y, fc=COL["t"], ec=(0.1, 0.1, 0.15), lw=0.6, zorder=3)
        a2.add_patch(p)
        a2.annotate(f"{RAIL11_LIP_GAP:g} mm over the lips\nat rest: the module\nrests on its carriage;\nthe lips take it only\nwhen the P16 pulls",
                    xy=(T11_HEAD_X[1] - 1.0, zl + 0.1), xytext=(66.0, 30.2), fontsize=7.8, arrowprops=dict(arrowstyle="->", lw=0.8),
                    bbox=dict(boxstyle="round,pad=0.25", fc="white", ec=(0.75, 0.75, 0.8), lw=0.6, alpha=0.92), zorder=8)
        a2.annotate(f"{RAIL11_CLEAR:g} mm each side", xy=(T11_HEAD_X[0] - 0.15, 25.5), xytext=(36.5, 31.6), fontsize=8.2, arrowprops=dict(arrowstyle="->", lw=0.8))
    else:
        a2.text(46.5, 25.5, "(the T reaches this\nsection at the station)", fontsize=8.5, color=(0.45, 0.45, 0.5))
    a2.set_xlim(36, 84)
    a2.set_ylim(14.5, 35.5)
    a2.set_aspect("equal")
    a2.set_title("2. Across the travel, at the station", fontsize=11, loc="left")
    a2.set_xlabel("along the auger, from the hinge (mm)", fontsize=9)
    # 3. the door ramp, along the travel through the rod
    dz = P11.door_open_at(off)
    for polys, c, z, dyy, dzz, al in ((S_HOUSE, COL["house"], 1, off, 0.0, 0.55), (S_SHUT, COL["door"], 2, off, -dz, 0.9), (S_EC_D, COL["ec"], 2, 0.0, 0.0, 0.9),
                                      (S_ROD, COL["rod"], 3, off, -dz, 1.0), (S_HEAD, COL["door"], 4, off, -dz, 1.0)):
        p = patch(polys, dy=dyy, dz=dzz, fc=c, ec=(0.1, 0.1, 0.15), lw=0.6, alpha=al, zorder=z)
        if p:
            a3.add_patch(p)
    a3.set_xlim(-60, 60)
    a3.set_ylim(-8.0, 36.5)
    a3.set_aspect("equal")
    a3.set_title(f"3. The door ramp at the EC's front: door open {dz:.1f} of {DOOR_TRAVEL:g} mm",
                 fontsize=11, loc="left")
    a3.set_xlabel("along the run (mm from the station)", fontsize=9)
    zf = -(DOOR11_HEAD_Z0 - DOOR_TRAVEL)
    a3.annotate(f"the lips catch the rod's head and draw it {DOOR_TRAVEL:g} mm toward the loop\nover {DOOR11_RAMP:g} mm; the shutter on the rod's other end opens",
                xy=(DOOR11_RAMP_FLAT + DOOR11_RAMP * 0.5, zf - 3.5), xytext=(16.0, -6.5), fontsize=8.4, arrowprops=dict(arrowstyle="->", lw=0.8), bbox=BB, zorder=8)
    a3.annotate("shutter over the 3 mm exit\n(spring-closed); cut through\nthe rod, the EC through a lip", xy=(off - 0.0, 1.0 + dz), xytext=(-58.0, -6.5), fontsize=8.4,
                arrowprops=dict(arrowstyle="->", lw=0.8), bbox=BB, zorder=8)
    a3.text(-58, 33.5, "EC's door ramp (fixed)", fontsize=8.5, color=COL["ec"])
    for a in (a1, a2, a3):
        a.tick_params(labelsize=8)
        a.grid(alpha=0.25, lw=0.5)
    if path:
        fig.savefig(path)
    fig.canvas.draw()
    img = np.asarray(fig.canvas.buffer_rgba())[:, :, :3].copy()
    plt.close(fig)
    return img


def main():
    import imageio.v2 as iio
    from PIL import Image
    if "--preview" in sys.argv:
        for o in (22.0, 9.0, 0.0):
            draw(o, OUT / f"rail_profile_preview_{o:g}.png")
        return
    offs = list(np.linspace(24.0, 0.0, 44)) + [0.0] * 10 + list(np.linspace(0.0, -24.0, 30)) + [-24.0] * 4
    w = iio.get_writer(OUT / "rail_profile_v11.mp4", fps=10, codec="libx264", quality=7, macro_block_size=8, ffmpeg_params=["-pix_fmt", "yuv420p"])
    gif = []
    for i, o in enumerate(offs):
        note = "coming in" if o > 0.01 else ("at the station" if abs(o) < 0.01 else "going out (next index)")
        img = draw(float(o), OUT / "rail_profile_v11.png" if i == 30 else None, note)
        w.append_data(img)
        if i % 2 == 0:
            gif.append(Image.fromarray(img).resize((960, 540), Image.LANCZOS))
    w.close()
    pal = gif[len(gif) // 2].quantize(colors=128, method=Image.Quantize.MEDIANCUT)
    frames = [g.quantize(palette=pal, dither=Image.Dither.NONE) for g in gif]
    frames[0].save(OUT / "rail_profile_v11.gif", save_all=True, append_images=frames[1:], duration=200, loop=0)
    print("rail_profile_v11:", len(offs), "frames")


if __name__ == "__main__":
    main()
