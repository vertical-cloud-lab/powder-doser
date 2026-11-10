"""Labelled explainer clips for v5 (Sam, PR #185, 2026-11-10): "a detailed gif of how each aspect of the dosing station
should function, including the clips, linear actuators, etc. Also ... how every aspect of the auger carriages should
function."

Every frame is the CAD (layout.placements) in the state the step describes, so each motion is the model's own: the chain
path, the latch rail's ramp, the two P16s' pins, the guide shoes, the dock, the door finger, the hinge, the auger drive.
The parts a step is about keep their colours and the rest is washed out; callouts name the parts.

    xvfb-run -a python explain.py station             # renders/explain/station_explained.{mp4,gif}
    xvfb-run -a python explain.py carriage            # renders/explain/carriage_explained.{mp4,gif}
    xvfb-run -a python explain.py station --preview   # one frame per step: renders/explain/preview/
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import vtk
from PIL import Image, ImageDraw, ImageFont

import layout as L
import render as R
import render_balance as RB
from params import (ACT_RETRACTED, BEAKER_H, BEAKER_RIM_Z, DOOR_TRAVEL, HATCH_OPEN_DEG, HOOK_SLIDE, KC4_A, KC4_B, KC4_BALL_Z, KC4_C,
                    LATCH_TRAVEL, MODULE_LINKS, N_LINKS, PARK_DROP, RUN_DIRECTION, SCREW_OUT, SHOE, TILT_DOSE_WORLD, TUBE_REST_X)

OUT = R.OUT / "explain"
FPS = 8
GIF_EVERY = 2                      # the GIF keeps every 2nd frame: 4 fps
GIF_W = 960
W3, H3 = 1280, 574                 # 3D viewport
TOP, BOT = 56, 90                  # title band, caption band (three lines)
WM = L.world_matrix()
TF = L.frame_dose_tilt(TILT_DOSE_WORLD)
H = L.HINGE_STATION
D = L.DOSE_POINT
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
_F: dict = {}


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    k = (size, bold)
    if k not in _F:
        _F[k] = ImageFont.truetype(BOLD if bold else FONT, size)
    return _F[k]


# ---------------------------------------------------------------- anchors (world points for the callouts)
def _centre(key: str) -> tuple:
    pd = R._PD.get(key)
    if pd is None:
        return (0.0, 0.0, 0.0)
    b = pd.GetBounds()
    return ((b[0] + b[1]) / 2, (b[2] + b[3]) / 2, (b[4] + b[5]) / 2)


def part(key: str, module: int | None = None, name: str | None = None, local=None, nth: int = 0, group: str | None = None):
    """Anchor on a placement: its local point `local` (default: the centre of its mesh's bounds)."""
    def f(pl, st):
        c = [p for p in pl if p.key == key and (module is None or p.module == module) and (name is None or name in p.name)
             and (group is None or p.group == group)]
        if len(c) <= nth:
            return None
        p = c[nth]
        loc = _centre(key) if local is None else local
        return (WM @ p.M @ np.r_[np.asarray(loc, float), 1.0])[:3]
    return f


def world(xyz):
    return lambda pl, st: np.asarray(xyz, float)


def sam(module: int, local):
    """A point in module `module`'s Sam frame (its mounting plate's frame)."""
    return part("sam_mounting_plate", module=module, local=local)


def ec(local):
    """A point in the EC's frame."""
    return part("sam_electronics_carriage", local=local)


def project(v: R.View, xyz) -> tuple[float, float, float]:
    c = vtk.vtkCoordinate()
    c.SetCoordinateSystemToWorld()
    c.SetValue(*[float(a) for a in xyz])
    x, y = c.GetComputedDoubleDisplayValue(v.ren)
    cam = v.ren.GetActiveCamera()
    front = float(np.dot(np.asarray(xyz) - np.asarray(cam.GetPosition()), np.asarray(cam.GetDirectionOfProjection())))
    return x, H3 - y, front


# ---------------------------------------------------------------- drawing
def callouts(img: Image.Image, items: list, top: int) -> None:
    """items: (text, (x, y) in the 3D viewport, side 'L'/'R'/None). Labels stack in a column on each side, sorted by their
    anchor's height, with a leader line to a dot on the anchor."""
    d = ImageDraw.Draw(img, "RGBA")
    f = font(19)
    W = img.width
    cols = {"L": [], "R": []}
    for text, (x, y), side in items:
        if not (-20 < x < W + 20 and -20 < y < H3 + 20):
            continue
        cols[side or ("L" if x < W / 2 else "R")].append((text, x, y))
    for side, col in cols.items():
        if not col:
            continue
        col.sort(key=lambda it: it[2])
        sizes = []
        for text, x, y in col:
            lines = text.split("\n")
            tw = max(d.textlength(s, font=f) for s in lines)
            sizes.append((tw + 18, 23 * len(lines) + 9))
        maxw = max(w for w, _ in sizes)
        if side == "L":
            xr = min(max(12 + maxw, min(x for _, x, _ in col) - 60), W / 2 - 40)
        else:
            xl = max(min(W - 12 - maxw, max(x for _, x, _ in col) + 60), W / 2 + 40)
        ys, prev = [], 6.0
        for (text, x, y), (w, h) in zip(col, sizes):
            yy = max(prev, y - h / 2)
            ys.append(yy)
            prev = yy + h + 8
        over = prev - (H3 - 4)
        if over > 0:
            ys = [max(4.0, yy - over) for yy in ys]
            for i in range(1, len(ys)):
                ys[i] = max(ys[i], ys[i - 1] + sizes[i - 1][1] + 8)
        for (text, x, y), (w, h), yy in zip(col, sizes, ys):
            bx0 = xr - w if side == "L" else xl
            box = (bx0, top + yy, bx0 + w, top + yy + h)
            ex = box[2] if side == "L" else box[0]
            ey = top + yy + h / 2
            d.line([(ex, ey), (x, top + y)], fill=(255, 255, 255, 230), width=5)
            d.line([(ex, ey), (x, top + y)], fill=(30, 30, 38, 255), width=2)
            d.rounded_rectangle(box, 7, fill=(255, 255, 255, 236), outline=(30, 30, 38, 255), width=2)
            d.multiline_text((bx0 + 9, top + yy + 4), text, fill=(15, 15, 22), font=f, spacing=4)
            d.ellipse([x - 6, top + y - 6, x + 6, top + y + 6], fill=(225, 50, 30, 255), outline=(255, 255, 255, 255), width=2)


def compose(img3: Image.Image, chap: tuple, title: str, text: str, items: list, readout: str | None, tag: str) -> Image.Image:
    W = W3
    out = Image.new("RGB", (W, TOP + H3 + BOT), (255, 255, 255))
    out.paste(img3, (0, TOP))
    d = ImageDraw.Draw(out, "RGBA")
    i, n = chap
    badge = f"{i}/{n}" if i else ""
    x = 14
    if badge:
        bw = d.textlength(badge, font=font(24, True)) + 22
        d.rounded_rectangle((x, 10, x + bw, 46), 8, fill=(30, 60, 140))
        d.text((x + 11, 13), badge, fill=(255, 255, 255), font=font(24, True))
        x += bw + 14
    d.text((x, 12), title, fill=(15, 15, 25), font=font(27, True))
    tw = d.textlength(tag, font=font(15))
    d.text((W - tw - 14, 4), tag, fill=(120, 120, 130), font=font(15))
    if n:
        seg = (W - 28) / n
        for k in range(n):
            col = (30, 60, 140) if k < i else (215, 218, 226)
            d.rectangle((14 + k * seg + 1, TOP - 5, 14 + (k + 1) * seg - 1, TOP - 2), fill=col)
    callouts(out, items, TOP)
    if readout:
        f = font(21, True)
        lines = readout.split("\n")
        rw = max(d.textlength(s, font=f) for s in lines) + 24
        rh = 28 * len(lines) + 10
        d.rounded_rectangle((W - rw - 12, TOP + 10, W - 12, TOP + 10 + rh), 8, fill=(25, 30, 40, 230))
        d.multiline_text((W - rw, TOP + 15), readout, fill=(150, 255, 150), font=f, spacing=6)
    d.rectangle((0, TOP + H3, W, TOP + H3 + BOT), fill=(244, 246, 250))
    d.line((0, TOP + H3, W, TOP + H3), fill=(200, 205, 215), width=2)
    d.multiline_text((16, TOP + H3 + 7), text, fill=(30, 30, 40), font=font(19), spacing=6)
    return out


def wrap(text: str, width: int = 118) -> str:
    import textwrap
    return "\n".join(textwrap.wrap(text, width))


# ---------------------------------------------------------------- output
class Clip:
    def __init__(self, name: str, tag: str, n_chapters: int, preview: bool = False):
        import imageio.v2 as iio
        OUT.mkdir(parents=True, exist_ok=True)
        self.name, self.tag, self.n, self.preview = name, tag, n_chapters, preview
        self.v = R.View(W3, H3, samples=4)
        self.chap = (0, n_chapters)
        self.title = ""
        self.count = 0
        self.last = None
        self.gif: list[Image.Image] = []
        if preview:
            (OUT / "preview").mkdir(parents=True, exist_ok=True)
            self.writer = None
        else:
            self.writer = iio.get_writer(OUT / f"{name}.mp4", fps=FPS, codec="libx264", quality=7, macro_block_size=8,
                                         ffmpeg_params=["-pix_fmt", "yuv420p"])
        self.extra_actors = []

    def chapter(self, i: int, title: str) -> None:
        self.chap = (i, self.n)
        self.title = title
        print(f"  [{self.name}] {i}/{self.n} {title}", flush=True)

    def frame(self, st: L.State, cam, hide=None, focus=None, accent=None, labels=(), text="", readout=None, opacity=None, before=None,
              save_as: str | None = None, offsets=None) -> None:
        pl = L.placements(st)
        hide_k = R.hidden(pl, hide)
        cols = {}
        for k, p in R.keyed(pl):
            base = R.TINT.get(p.key, p.color)
            if accent is not None and accent(p):
                cols[k] = accent(p) if isinstance(accent(p), tuple) else (0.92, 0.22, 0.12)
            elif focus is None or focus(p):
                cols[k] = base
            else:
                cols[k] = tuple(0.74 + 0.22 * c for c in base)
        op = opacity(pl) if callable(opacity) else opacity
        self.v.show(pl, colors=cols, hide=hide_k, opacity=op, offsets=offsets)
        self.v.camera(*cam)
        if before:
            before(self.v, st)
        img3 = self.v.image()
        items = []
        for lab in labels:
            text_, fn = lab[0], lab[1]
            side = None                    # each label goes to the side its part is on
            p3 = fn(pl, st)
            if p3 is None:
                continue
            x, y, front = project(self.v, p3)
            if front > 0:
                items.append((text_, (x, y), side))
        ro = readout(st) if callable(readout) else readout
        img = compose(img3, self.chap, self.title, wrap(text), items, ro, self.tag)
        self.emit(img)
        if save_as:
            img.save(OUT / "preview" / f"{save_as}.png")

    def emit(self, img: Image.Image) -> None:
        self.last = img
        if self.preview:
            img.save(OUT / "preview" / f"{self.name}_{self.chap[0]:02d}_{self.count:03d}.png")
            self.count += 1
            return
        self.writer.append_data(np.asarray(img))
        if self.count % GIF_EVERY == 0:
            self.gif.append(img.resize((GIF_W, int(GIF_W * img.height / img.width)), Image.LANCZOS))
        self.count += 1

    def hold(self, secs: float) -> None:
        if self.preview or self.last is None:
            return
        for _ in range(max(1, round(secs * FPS))):
            self.emit(self.last)

    def move(self, secs: float, fn, eased: bool = True) -> None:
        """fn(t, i, n) -> kwargs for frame(); t runs 0..1 (eased)."""
        n = max(2, round(secs * FPS))
        idx = [n - 1] if self.preview else range(n)
        for i in idx:
            t = i / (n - 1)
            self.frame(**fn(R.ease(t) if eased else t, i, n))

    def done(self) -> None:
        if self.preview:
            return
        self.writer.close()
        # one palette for every frame (from a sample across the clip), no dither: steady colours and small frame deltas
        sample = self.gif[:: max(1, len(self.gif) // 24)]
        w, h = sample[0].size
        mont = Image.new("RGB", (w, h * len(sample)))
        for i, im in enumerate(sample):
            mont.paste(im, (0, i * h))
        pal = mont.quantize(colors=160, method=Image.Quantize.MEDIANCUT)
        frames = [im.quantize(palette=pal, dither=Image.Dither.NONE) for im in self.gif]
        g = OUT / f"{self.name}.gif"
        frames[0].save(g, save_all=True, append_images=frames[1:], duration=int(1000 * GIF_EVERY / FPS), loop=0, optimize=False)
        print(f"  {self.name}: {self.count} frames ({self.count / FPS:.1f} s), gif {g.stat().st_size / 1e6:.1f} MB, "
              f"mp4 {(OUT / (self.name + '.mp4')).stat().st_size / 1e6:.1f} MB", flush=True)


# ---------------------------------------------------------------- shared predicates and cameras
LATCH_MOD = ("carriage", "sam_mounting_plate", "latch_bolt", "latch_follower", "latch_spring", "auger", "kc_ball", "flat_pad_v4", "m3x12_bhcs",
             "nut_m3", "magnet", "clevis_pin", "eclip")


def latch_hide(p) -> bool:
    if p.key == "latch_rail":
        return False
    if p.module == 0 and p.key in LATCH_MOD:
        return False
    if p.group == "chain" and abs(p.M[1, 3] - L.STATION_Y) < 90 and p.M[2, 3] < 480:
        return False
    return True


def is_station(p) -> bool:
    return p.group in ("station", "station_ec", "station_act")


def station_bits(p) -> bool:
    return is_station(p) or p.module == 0


def keys(*ks):
    return lambda p: p.key in ks


def no_enclosure(p) -> bool:
    return p.group == "enclosure"


def wide_cut(p) -> bool:
    return p.group in ("enclosure", "elec")


def section_cut(p) -> bool:
    return RB.cut_section(p) or p.group == "elec"


def front_cut(p) -> bool:
    return RB.cut_front(p) or p.group == "elec"


CAM_OVER = ((120, 0, 420), (-0.9, -1.0, 0.42), 1650)
CAM_INDEX = ((-30, L.STATION_Y - 10, 458), (-1.0, -0.6, 0.25), 330)
CAM_LATCH = ((146, -14, 430), (0.35, -0.55, -1.0), 240)
CAM_FRONT = ((70, D[1], 300), (-1.0, -0.18, 0.16), 1050)
CAM_GUIDE = ((91, 150, 345), (-0.85, 0.75, 0.35), 330)
CAM_DOCK = ((85, 5, 445), (-0.55, -1.0, -0.3), 210)
CAM_DOOR = ((D[0] - 2, D[1] - 4, D[2] - 4), (-1.0, -0.75, -0.25), 150)
CAM_SECTION = ((D[0] + 60, D[1], 390), (0.0, 1.0, 0.03), 700)
CAM_SECTION_LOW = ((D[0] + 50, D[1], 320), (0.0, 1.0, 0.04), 1000)
CAM_DRIVE = ((H[0] + 60, H[1], H[2] - 12), (-0.2, -1.0, 0.1), 230)

TAG_S = "chain carousel v5 · the dosing station · PR #185"
TAG_C = "chain carousel v5 · an auger carriage · PR #185"


def stroke(st: L.State) -> float:
    B, Pp = L.p16_pins(st.tilt, st.ext, -1)
    return float(np.linalg.norm(Pp - B) - ACT_RETRACTED)


def shift_mm(st: L.State) -> float:
    return abs(st.shift) * 9.525


# ---------------------------------------------------------------- the station
def station(preview: bool = False) -> None:
    N = 12
    c = Clip("station_explained", TAG_S, N, preview)
    k_next = 0
    S0 = dict(enclosure=False)

    # 1. where it is
    c.chapter(1, "The dosing station: where it is")
    lab1 = [("Station on the bottom run:\nmodule 1 is over it", sam(0, (150, 0, 0)), "R"),
            ("A&D HR-202i balance\n220 g x 0.1 mg", part("hr202i_body", local=(100, 0, 200)), "L"),
            ("Two Actuonix P16\nlinear actuators", part("actuator_body", name="+y"), "R"),
            ("Electronics carriage (EC)\non its lift bar", part("sam_electronics_carriage"), "L"),
            ("13 auger modules on\ntwo #35 roller chains", sam(6, (150, 0, 0)), "R"),
            ("Latch rail and tube rest", part("latch_rail"), "L")]
    c.move(2.4, lambda t, i, n: dict(st=L.State(ext=0.0, **S0), cam=R.cam_lerp(R.HERO, CAM_OVER, t), hide=wide_cut,
                                     focus=lambda p: is_station(p) or p.group == "scale" or p.module == 0,
                                     labels=lab1 if t > 0.99 else (),
                                     text="Each module comes round on the chains to the station under the bottom run. There the EC rises, docks onto "
                                          "the module, tilts it and doses straight down into a beaker on the balance. The enclosure is hidden here.",
                                     save_as="s01" if preview else None))
    c.hold(3.5)

    # 2. index
    c.chapter(2, "Index: the chain brings the next module")
    foc2 = lambda p: p.group in ("chain", "carriages") or p.key in ("hold_down", "hall_switch", "magnet")  # noqa: E731
    lab2 = [("Front hold-down\n+ INDEX hall switch", part("hall_switch", name="INDEX"), "L"),
            ("Carriage tongue", part("carriage", module=0, local=(0, -8.85, -18.0)), "L"),
            ("Index magnet\nin the tongue", part("magnet", module=0, nth=0), "R"),
            ("A-1 attachment link\n(every 8th link)", part("chain_a1", name="front", nth=0), "R")]

    def a1_near(pl, st):
        cm = next(p.M for p in pl if p.key == "carriage" and p.module == 0)
        best = min((p for p in pl if p.key == "chain_a1" and "front" in p.name), key=lambda p: np.linalg.norm(p.M[:3, 3] - cm[:3, 3]))
        return (WM @ best.M @ np.r_[_centre("chain_a1"), 1.0])[:3]
    lab2[3] = ("A-1 attachment link\n(every 8th link)", a1_near, "R")
    c.move(3.5, lambda t, i, n: dict(st=L.State(shift=-RUN_DIRECTION * MODULE_LINKS * (1 - t), ext=0.0, **S0), cam=CAM_INDEX,
                                     hide=lambda p: R.front_open(p) or p.group in ("enclosure", "elec", "scale") or p.key == "side_plate_back",
                                     focus=foc2, labels=lab2,
                                     readout=lambda st: f"chain {shift_mm(st):4.1f} mm to go",
                                     text="The NEMA 34 turns 1000 steps: both chains move 8 links (76.2 mm), one module. The carriage's tongues slide "
                                          "into the hold-downs on both side plates; the hall switches see its magnet (INDEX at the front; HOME at "
                                          "the back sees carriage 1's second magnet).", save_as="s02" if preview else None))
    c.hold(2.0)

    # 3. latch rail opens the latch
    c.chapter(3, "The latch rail opens the plate's clip")
    foc3 = lambda p: p.key in ("latch_bolt", "latch_follower", "latch_spring", "latch_rail") or (p.module == 0 and p.key in (  # noqa: E731
        "sam_mounting_plate", "carriage"))
    lab3 = [("Station's latch rail: a cam with\n25 deg ramps and a flat", part("latch_rail", local=(119.0, 31.0, 22.0)), "R"),
            ("Follower (3 mm dowel)\nrides the cam", part("latch_follower", module=0, local=(0.0, 0.0, 21.0)), "R"),
            ("4 mm latch pin, pushed\nout of the keeper", part("latch_bolt", module=0, local=(108.0, 19.0, -13.5)), "L"),
            ("Keeper on the plate\n(4.2 mm hole)", sam(0, (99.0, 23.0, -10.0)), "L"),
            ("Spring pushes\nthe pin home", part("latch_spring", module=0), "R"),
            ("Tube rest: the module\nsettles 0.5 mm onto it", part("latch_rail", local=(111.0, -25.0, 13.5)), "L")]
    hide3 = latch_hide
    c.move(4.0, lambda t, i, n: dict(st=L.State(shift=-RUN_DIRECTION * 2.2 * (1 - t), ext=0.0, **S0), cam=CAM_LATCH, hide=hide3, focus=foc3,
                                     labels=lab3, readout=lambda st: f"latch pin {L.latch_open(0, st):3.1f} of {LATCH_TRAVEL} mm out",
                                     text="Every carriage has a spring latch: its 4 mm pin sits 4 mm deep in a hole in the plate's keeper, so the module "
                                          "can't swing off in any orientation. At the station the follower meets the latch rail's cam: its 25 deg ramp "
                                          "pushes the follower, and the pin with it, 4.5 mm out of the keeper. The module then rests on the tube rest.", save_as="s03" if preview else None), eased=False)
    c.hold(2.0)

    # 4. the two P16s lift the bar
    c.chapter(4, "Two P16 linear actuators lift the EC")
    foc4 = lambda p: is_station(p) and p.key not in ("latch_rail", "hold_down", "hall_switch", "m5x16_shcs", "insert_m5")  # noqa: E731
    lab4 = [("Actuonix P16-150-22-12-P\n(-y side)", part("actuator_body", name="-y"), "L"),
            ("Actuonix P16-150-22-12-P\n(+y side)", part("actuator_body", name="+y"), "R"),
            ("Base pin: 4 x 16 shoulder screw\non a printed shelf", part("clevis_bracket", name="-y"), "L"),
            ("Lift bar: 8 mm steel shaft,\nclamped in the EC", part("lift_bar", local=(0.0, -70.0, 0.0)), "L"),
            ("Bar end block: the rod end's\npin in 2 mm slots", part("bar_end", name="+y"), "R"),
            ("Guide on the station post", part("guide_block", name="+y"), "R"),
            ("EC", part("sam_electronics_carriage"), "R")]
    c.move(4.0, lambda t, i, n: dict(st=L.State(ext=PARK_DROP * t, top_door=RB.TOP_OPEN, **S0), cam=CAM_FRONT, hide=front_cut, focus=foc4,
                                     labels=lab4, readout=lambda st: f"rise {st.ext:4.1f} of {PARK_DROP:.0f} mm",
                                     text="Each P16 (150 mm stroke, potentiometer feedback) has its own LAC board, and both get the same target. The bar's "
                                          "ends sit in 2 mm slots, so the two P16s needn't stop at exactly the same place. The P16s stand beside the "
                                          "balance, not in it.", save_as="s04" if preview else None))
    c.hold(2.0)

    # 5. guide shoes
    c.chapter(5, "Guide shoes keep the EC square while it rises")
    foc5 = keys("guide_block", "bar_end", "lift_bar", "actuator_rod", "actuator_body", "clevis_screw", "nut_m3_clevis", "ext_station_post",
                "sam_electronics_carriage", "p16_shelf")
    lab5 = [("Guide: a 14.2 mm slot\non the station post", part("guide_block", name="+y", local=(0.0, 0.0, 330.0)), "L"),
            ("Shoe on the bar end\n(14 x 10 x 20 mm)", part("bar_end", name="+y", local=(0.0, 13.1, 0.0)), "R"),
            ("Rod end's shoulder screw\nin a 2 mm slot", part("clevis_screw", name="rod end +y"), "R"),
            ("The slot ends where the EC seats:\nthen the dock decides", world((91.0, 170.0, L.GUIDE_TOP_Z)), "L")]

    def in_slot(st):
        z = L.p16_pins(st.tilt, st.ext, 1)[1][2] - SHOE[2] / 2
        return "shoe in its slot" if z < L.GUIDE_TOP_Z - 0.2 else "shoe clear of the slot"
    c.move(3.5, lambda t, i, n: dict(st=L.State(ext=PARK_DROP * t, **S0), cam=CAM_GUIDE,
                                     hide=lambda p: R.station_cut(p) or p.group in ("elec", "enclosure") or (p.module >= 0 and p.module != 0) or
                                     p.key in ("side_plate_back",), focus=foc5, labels=lab5,
                                     readout=lambda st: f"rise {st.ext:4.1f} mm\n{in_slot(st)}",
                                     text="Each bar end carries a shoe in a vertical slot, so the bar, and the EC clamped to it, can't tip while they rise "
                                          "(v3/v4's single P16 let the EC topple). The slots stop just as the EC seats, so the dock, not the guides, "
                                          "decides where the EC sits.", save_as="s05" if preview else None))
    c.hold(1.5)

    # 6. the kinematic dock
    c.chapter(6, "Kinematic dock: three balls, six contacts, magnets")
    foc6 = lambda p: p.key in ("kc_ball", "vee_dowel", "kc_magnet", "flat_pad_v4", "sam_electronics_carriage")  # noqa: E731
    lab6 = [("Plate ball A drops\ninto the cone", part("kc_ball", module=0, nth=0), "R"),
            ("Plate ball B drops into\nthe vee (two dowels)", part("kc_ball", module=0, nth=1), "L"),
            ("EC ball C lands on a\nsteel washer (the flat)", part("flat_pad_v4", module=0), "R"),
            ("N52 magnet behind\neach seat", part("kc_magnet", nth=1), "L"),
            ("EC arms reach round\nthe auger", ec((44.0, -19.5, 5.0)), "L")]
    c.move(4.0, lambda t, i, n: dict(st=L.State(ext=14.0 + (PARK_DROP - 14.0) * t, **S0), cam=CAM_DOCK, hide=lambda p: R.dock_cut(p) or p.group == "elec",
                                     focus=foc6, opacity=lambda pl: {**R.ghost_plate(pl, 0.3), **{k: 0.4 for k, p in R.keyed(pl) if p.key in ("sam_electronics_carriage", "nema11", "solenoid")}},
                                     accent=lambda p: (0.85, 0.12, 0.10) if p.key == "kc_magnet" else ((0.55, 0.57, 0.62) if p.key in ("kc_ball", "vee_dowel", "flat_pad_v4") else None),
                                     labels=lab6,
                                     readout=lambda st: f"{PARK_DROP - st.ext:4.1f} mm to seat",
                                     text="Two 1/4 in balls in the plate drop into a cone and a vee on the EC's arms, and the EC's third ball lands on a "
                                          "steel washer in the plate: six contacts, so the module sits the same way every time. N52 magnets hold it "
                                          "(about 8 N per ball: TEST-PLAN T6c). The EC now carries the module, off its tube rest.",
                                     save_as="s06" if preview else None))
    c.hold(2.0)

    # 7. the outlet door
    c.chapter(7, "The outlet door opens in the dock's last 6 mm")
    foc7 = keys("door_housing", "door_shutter", "door_spring", "door_spring_open", "sam_electronics_carriage", "m2x8_shcs")
    lab7 = [("Shutter over the\n3 mm exit", part("door_shutter", module=0), "L"),
            ("Spring shuts it", part("door_spring", module=0), "R"),
            ("Door housing", part("door_housing", module=0, local=(18.0, -13.0, 4.0)), "R"),
            ("EC's finger pushes\nthe shutter", ec((-2.1, 7.5, 20.0)), "L"),
            ("Auger exit", world(D), "L")]
    lab7b = [lab7[0], ("Spring (compressed)", part("door_spring_open", module=0), "R")] + lab7[2:]

    def door_frame(t, i, n):
        st = L.State(ext=PARK_DROP - DOOR_TRAVEL - 2.0 + (DOOR_TRAVEL + 2.0) * t, **S0)
        return dict(st=st, cam=CAM_DOOR, hide=lambda p: R.dock_cut(p) or p.group == "elec", focus=foc7,
                    opacity=lambda pl: {k: 0.45 for k, p in R.keyed(pl) if p.key == "door_housing" and p.module == 0},
                    labels=lab7b if L.door_open(st) > 0.5 else lab7, readout=f"door {L.door_open(st):3.1f} of {DOOR_TRAVEL:.0f} mm open",
                    text="The exit is covered by a spring-loaded shutter everywhere but here. In the dock's last 6 mm the EC's finger "
                         "pushes the shutter clear of the 3 mm exit. When the EC leaves, the spring shuts it again before the EC parks.",
                    save_as="s07" if preview else None)
    c.move(3.5, door_frame)
    c.hold(1.5)

    # 8. tilt
    c.chapter(8, "Tilt: module and EC swing up through the carriage")
    foc8 = lambda p: p.module == 0 or p.group in ("station_ec", "station_act") or p.key in ("p16_shelf", "clevis_bracket", "clevis_screw")  # noqa: E731
    lab8 = [("Hinge: two 5 mm pins,\nthe module turns about them", part("clevis_pin", module=0, nth=0), "L"),
            ("The exit is on the hinge axis:\nit stays over the beaker", world(D), "L"),
            ("Carriage opening\n(51.6 mm wide)", part("carriage", module=0, local=(0.0, -8.85, 150.0)), "R"),
            ("P16 extends\n(both together)", part("actuator_rod", name="-y"), "R"),
            ("Lift bar on the\nEC's pin axis", part("lift_bar"), "R")]
    c.move(3.5, lambda t, i, n: dict(st=L.State(ext=PARK_DROP, tilt=TF * t, magnet_on=True, top_door=RB.TOP_OPEN, **S0), cam=CAM_SECTION,
                                     hide=section_cut, focus=foc8, labels=lab8,
                                     readout=lambda st: f"tilt {st.tilt:4.1f} deg\nP16 stroke {stroke(st):5.1f} mm",
                                     text="Both P16s keep extending. The bar is on the EC's pin axis, so the EC and the module turn together about the "
                                          "module's own hinge, up through the carriage's opening into the loop. 30 deg is the default; v5 stops at "
                                          "40 deg, where the bar would reach modules 2 and 13.", save_as="s08" if preview else None))
    c.hold(1.5)

    # 9. auger drive
    c.chapter(9, "The auger drive: NEMA 11, pinion, gear, tapper")
    foc9 = keys("nema11", "pinion", "auger", "solenoid", "auger_cap")
    lab9 = [("NEMA 11 stepper\n(in the EC)", part("nema11"), "L"),
            ("20T steel pinion", part("pinion"), "L"),
            ("44T gear on the auger", sam(0, (83.4, 0.0, 0.0)), "R"),
            ("Solenoid taps\nthe tube", part("solenoid"), "L"),
            ("Auger turns", sam(0, (150.0, 0.0, 0.0)), "R")]

    def drive_frame(t, i, n):
        st = L.State(ext=PARK_DROP, tilt=TF, magnet_on=True, spin=2 * math.pi * 1.5 * t, tap=2.0 if (i // 3) % 2 == 0 and t > 0.5 else 0.0,
                     top_door=RB.TOP_OPEN, **S0)
        return dict(st=st, cam=CAM_DRIVE, hide=lambda p: not (p.module == 0 and p.key in ("sam_mounting_plate", "auger", "auger_cap", "door_housing", "door_shutter", "kc_ball", "flat_pad_v4") or p.group == "station_ec" and p.key not in ("lift_bar", "bar_end", "clevis_screw", "nut_m3_clevis")),
                    focus=foc9, labels=lab9,
                    opacity=lambda pl: {k: (0.35 if p.key == "sam_electronics_carriage" else 0.55) for k, p in R.keyed(pl) if p.key in ("sam_electronics_carriage", "sam_mounting_plate")},
                    readout=f"auger {st.spin / (2 * math.pi):4.2f} turns",
                    text="The NEMA 11 in the EC turns the auger through a 20T steel pinion and the auger's 44T gear; the dock holds "
                         "their centre distance. A solenoid taps the tube to keep the powder moving.", save_as="s09" if preview else None)
    c.move(3.0, drive_frame, eased=False)
    c.hold(1.0)

    # 10. dose onto the balance
    c.chapter(10, "Dose: straight into a beaker on the balance")
    g = RB.Grains(c.v)
    z_land = BEAKER_RIM_Z - BEAKER_H + 6.0
    foc10 = lambda p: p.group == "scale" or p.module == 0  # noqa: E731
    lab10 = [("Top door slid back:\nthe only opening", part("hr202i_top_door"), "R"),
             ("25 mL beaker on a\nprinted riser", part("beaker"), "R"),
             ("Pan of the HR-202i", part("hr202i_pan"), "L"),
             (f"{D[2] - BEAKER_RIM_Z:.0f} mm fall from the exit,\nno funnel", world((D[0] - 4, D[1], (D[2] + BEAKER_RIM_Z) / 2)), "L")]
    state = {"t": 0.0}

    def dose_frame(t, i, n):
        state["t"] = i / FPS
        m = 0.105 * state["t"]
        st = L.State(ext=PARK_DROP, tilt=TF, magnet_on=True, spin=2 * math.pi * state["t"], top_door=RB.TOP_OPEN, **S0)
        return dict(st=st, cam=CAM_SECTION_LOW, hide=section_cut, focus=foc10, labels=lab10,
                    opacity=lambda pl: RB.opac(pl), before=lambda v, s: g.set(state["t"], True, z_land),
                    readout=f"HR-202i  {m:8.4f} g",
                    text="The dose falls through the balance's open top door into a 25 mL beaker on a riser on the pan. The Pi reads the "
                         "balance over RS-232 after every quarter turn and stops at the target (chain_rig.py dose-to). The reading is "
                         "illustrative.", save_as="s10" if preview else None)
    c.move(4.0, dose_frame, eased=False)
    g.set(0.0, False, z_land)
    c.hold(1.0)

    # 11. undock
    c.chapter(11, "After the dose: tilt back, reverse, undock, park")
    foc11 = lambda p: p.module == 0 or p.group in ("station_ec", "station_act") or p.key in ("guide_block",)  # noqa: E731
    lab11 = [("Module back on\nits tube rest", part("latch_rail", local=(111.0, 0.0, 14.0)), "R"),
             ("EC parks 28 mm under\nits dock, 12 mm over\nthe balance", part("sam_electronics_carriage"), "R"),
             ("Door shuts as\nthe EC leaves", part("door_shutter", module=0), "L")]

    def back_frame(t, i, n):
        if t < 0.4:
            u = t / 0.4
            st = L.State(ext=PARK_DROP, tilt=TF * (1 - R.ease(u)), magnet_on=True, spin=2 * math.pi, top_door=RB.TOP_OPEN, **S0)
            txt, ro = "Hold 0.5 s, then tilt back to level.", f"tilt {TF * (1 - R.ease(u)):4.1f} deg"
        elif t < 0.6:
            u = (t - 0.4) / 0.2
            st = L.State(ext=PARK_DROP, magnet_on=True, spin=2 * math.pi * (1 - u), top_door=RB.TOP_OPEN, **S0)
            txt, ro = "At rest, the auger reverses one turn: it pulls powder back from the exit before the door shuts.", f"reverse {u:4.2f} turn"
        else:
            u = R.ease((t - 0.6) / 0.4)
            st = L.State(ext=PARK_DROP * (1 - u), top_door=RB.TOP_OPEN * (1 - u), **S0)
            txt, ro = ("The P16s lower the EC: the module settles back onto the tube rest, the door's spring shuts the exit, the "
                       "shoes drop back into their slots, and the EC parks. The balance's top door shuts; read the stable mass."), \
                f"EC {PARK_DROP * (1 - u):4.1f} mm up"
        return dict(st=st, cam=CAM_SECTION, hide=section_cut, focus=foc11, labels=lab11 if t >= 0.6 else lab11[2:], text=txt,
                    readout=ro, save_as="s11" if preview else None)
    c.move(6.0, back_frame, eased=False)
    c.hold(1.5)

    # 12. release
    c.chapter(12, "Release: the clip closes as the carriage leaves")
    c.move(4.0, lambda t, i, n: dict(st=L.State(shift=RUN_DIRECTION * 2.2 * t, ext=0.0, **S0), cam=CAM_LATCH, hide=hide3, focus=foc3, labels=lab3,
                                     readout=lambda st: f"latch pin {L.latch_open(0, st):3.1f} of {LATCH_TRAVEL} mm out",
                                     text="The next index carries the follower down the cam's far ramp, and the spring pushes the pin back into the "
                                          "keeper before the carriage leaves the station. The module is held shut on its carriage again for the rest "
                                          "of the lap.", save_as="s12" if preview else None), eased=False)
    c.hold(2.5)
    c.done()


# ---------------------------------------------------------------- an auger carriage
def carriage(preview: bool = False) -> None:
    N = 8
    c = Clip("carriage_explained", TAG_C, N, preview)
    k0 = 3                                            # carriage 4: at the loading position at home
    S0 = dict(enclosure=False, scale=False)
    Lf = L.load_frame()
    z_load = float(Lf[2, 3])
    CAM_LOAD = ((150, 150, z_load - 10), (0.35, 1.0, 0.30), 760)
    CAM_LOAD_CLOSE = ((150, 110, z_load + 5), (-0.35, 1.0, 0.45), 560)
    CAM_LOOP = ((120, 0, 600), (-1.0, -0.42, 0.22), 1150)

    # 1. overview
    c.chapter(1, "An auger carriage: what it is")
    foc1 = lambda p: p.module == k0 or p.group == "chain"  # noqa: E731
    lab1 = [("Carriage 4 of 13\n(one every 8 links)", part("carriage", module=k0), "R"),
            ("Auger module on the\ncarriage's outer face", sam(k0, (150.0, 0.0, 0.0)), "R"),
            ("Two #35 roller chains,\n305 mm apart", part("chain_outer", nth=40), "L"),
            ("Module 1 at the station", sam(0, (150.0, 0.0, 0.0)), "L")]
    c.move(2.5, lambda t, i, n: dict(st=L.State(ext=0.0, **S0), cam=CAM_LOOP, hide=lambda p: R.front_open(p) or p.group in ("elec", "scale"),
                                     focus=foc1, labels=lab1 if t > 0.99 else (),
                                     text="13 printed carriages ride on the two chains, one every 8 links. Each carries one auger module (Sam's "
                                          "mounting plate and the lab auger) on its outer face, outside the loop.", save_as="c01" if preview else None))
    c.hold(3.0)

    # 2. the carriage on the chains (bare, then its screws)
    c.chapter(2, "The carriage hooks over and bolts to both chains")
    mods = tuple(k for k in range(13) if k != k0)
    foc2 = lambda p: p.module == k0 or p.key in ("chain_a1", "side_tab", "side_tab_m")  # noqa: E731

    def a1(back: bool):
        def f(pl, st):
            cm = next(p.M for p in pl if p.key == "carriage" and p.module == k0)
            cands = [p for p in pl if p.key == "chain_a1" and (("back" in p.name) == back)]
            best = min(cands, key=lambda p: np.linalg.norm(p.M[:3, 3] - cm[:3, 3] - (np.array([305.0, 0, 0]) if back else 0)))
            return (WM @ best.M @ np.r_[_centre("chain_a1"), 1.0])[:3]
        return f
    lab2 = [("Printed PETG carriage\n(351 mm long)", part("carriage", module=k0, local=(0.0, -8.85, 200.0)), "R"),
            ("A-1 tab on the\nfront chain", a1(False), "L"),
            ("A-1 tab on the\nback chain", a1(True), "R"),
            ("M3 x 12 button head\nthrough the tab", part("m3x12_bhcs", module=k0, nth=0), "L"),
            ("Nylock in the\nprinted hook", part("nut_m3", module=k0, nth=0), "L"),
            ("Tongue", part("carriage", module=k0, local=(0.0, -8.85, -18.0)), "L"),
            ("Index magnet", part("magnet", module=k0, nth=0), "R")]

    def on_frame(t, i, n):
        if t < 0.45:
            u = R.ease(t / 0.45)
            st = L.State(carriages=tuple(range(13)), modules=mods, ext=0.0, out_carriage=k0, out_slide=HOOK_SLIDE, out_lift=120.0 * (1 - u),
                         screws_out=SCREW_OUT, **S0)
            txt = "In through the side hatch, 10 mm along from its place: the hooks pass beside the A-1 tabs."
        elif t < 0.7:
            u = R.ease((t - 0.45) / 0.25)
            st = L.State(carriages=tuple(range(13)), modules=mods, ext=0.0, out_carriage=k0, out_slide=HOOK_SLIDE * (1 - u), out_lift=0.0,
                         screws_out=SCREW_OUT, **S0)
            txt = "Slide 10 mm: a printed hook closes over each A-1 tab, and the tongues go into the side tabs."
        else:
            u = R.ease((t - 0.7) / 0.3)
            st = L.State(carriages=tuple(range(13)), modules=mods, ext=0.0, out_carriage=k0, out_slide=0.0, out_lift=0.0,
                         screws_out=SCREW_OUT * (1 - u), **S0)
            txt = ("Two M3 x 12 button heads go through the carriage and the tabs into nylocks held in the hooks. The tongues carry "
                   "the index magnet (carriage 1 has a second, for HOME).")
        return dict(st=st, cam=CAM_LOAD_CLOSE, hide=lambda p: R.front_open(p) or p.group in ("elec", "station_ec", "station_act", "scale") or (p.module >= 0 and p.module != k0) or (p.group == "station" and p.key not in ("side_tab", "side_tab_m", "m5x8_shcs")) or p.key == "side_plate_back",
                    focus=foc2, labels=lab2, text=txt, save_as="c02" if preview else None)
    c.move(6.0, on_frame, eased=False)
    c.hold(2.0)

    # 3. the module and its parts (bench), onto the carriage
    c.chapter(3, "The module: plate, auger, dock half, door")
    bench = dict(carriages=(k0,), modules=(k0,), ext=0.0, out_carriage=k0, out_slide=HOOK_SLIDE, out_lift=170.0, screws_out=SCREW_OUT,
                 enclosure=False, scale=False, station=False)
    pl_b = L.placements(L.State(**bench))
    Cb = next(p.M for p in pl_b if p.key == "carriage" and p.module == k0)
    u_dir, w_dir = Cb[:3, 0], Cb[:3, 1]
    mod_keys = ("sam_mounting_plate", "flat_pad_v4", "auger", "auger_cap", "kc_ball", "door_housing", "door_shutter", "door_spring", "m2x8_shcs")
    away = w_dir * 110.0

    def explode(p, t_auger, t_dock, t_door, t_on, t_pins):
        if p.key in ("clevis_pin", "eclip"):
            su = 1.0 if float(u_dir @ (p.M[:3, 3] - Cb[:3, 3])) > 0 else -1.0
            return su * u_dir * 40.0 * (1 - t_pins)
        if p.key not in mod_keys:
            return None
        o = away * (1 - t_on)
        if p.key in ("auger", "auger_cap"):
            o = o + np.array([-170.0 * (1 - t_auger), 0, 0])
        if p.key in ("kc_ball", "flat_pad_v4"):
            o = o - w_dir * 25.0 * (1 - t_dock)
        if p.key in ("door_housing", "door_shutter", "door_spring", "m2x8_shcs"):
            o = o + np.array([-45.0 * (1 - t_door), 0, 0])
        return o
    lab3 = [("Mounting plate: Sam's Oct 13 plate\n+ dock pockets and the keeper", sam(k0, (60.0, -22.0, -15.5)), "L"),
            ("Lab auger (threaded storage)\nand its cap", sam(k0, (160.0, 0.0, 0.0)), "R"),
            ("44T gear (driven by\nthe EC's pinion)", sam(k0, (83.4, 0.0, -10.0)), "R"),
            ("Two 1/4 in steel balls\n(the dock's plate half)", part("kc_ball", module=k0, nth=0), "L"),
            ("Steel washer: the flat", part("flat_pad_v4", module=k0), "R"),
            ("Outlet door: housing,\nshutter, spring", part("door_housing", module=k0), "L"),
            ("Keeper (4.2 mm hole)\nfor the latch pin", sam(k0, (102.0, 19.0, -13.5)), "R"),
            ("Hinge pins 5 mm\n+ e-clips", part("clevis_pin", module=k0, nth=0), "L")]

    def bench_frame(t, i, n):
        seg = [(0.0, 0.22), (0.22, 0.4), (0.4, 0.58), (0.58, 0.8), (0.8, 1.0)]
        ts = [R.ease(min(1.0, max(0.0, (t - a) / (b - a)))) for a, b in seg]
        pl = L.placements(L.State(**bench))
        offs = {}
        for k, p in R.keyed(pl):
            if p.module == k0:
                o = explode(p, *ts)
                if o is not None:
                    offs[k] = np.asarray(o, float)
        steps = ["The auger slides into the plate's clamps; its 44T gear sits beside the outlet.",
                 "Two 1/4 in steel balls press into the plate's auger side; a steel washer goes in beside them (the dock's plate half).",
                 "The outlet door (housing, shutter and spring) screws on over the exit with two M2 screws.",
                 "The module goes onto the carriage's outer face between its hinge lugs; the keeper meets the latch pin.",
                 "Two 5 mm grooved pins go through the lugs into the plate's knuckles; e-clips hold them."]
        s_i = min(4, sum(1 for a, b in seg if t >= b))
        return dict(st=L.State(**bench), cam=((160.0, float(Cb[1, 3]) + 40, float(Cb[2, 3])), (0.25, 1.0, 0.55), 470),
                    focus=lambda p: p.module == k0, hide=lambda p: p.module != k0, labels=lab3 if t > 0.99 else (), text=steps[s_i],
                    save_as="c03" if preview else None, offsets=offs)
    c.move(9.0, bench_frame, eased=False)
    c.hold(3.5)

    # 4. the hinge and the opening (the station tilts it)
    c.chapter(4, "The hinge and the opening: how the module tilts")
    foc4 = lambda p: p.module == 0  # noqa: E731
    lab4 = [("Hinge lugs on the\ncarriage's outer face", part("carriage", module=0, local=(28.0, -26.0, 33.0)), "L"),
            ("5 mm pins in Sam's\n5.3 mm knuckle holes", part("clevis_pin", module=0, nth=1), "L"),
            ("Opening in the carriage:\nthe module swings up\nthrough it into the loop", part("carriage", module=0, local=(0.0, -8.85, 200.0)), "R"),
            ("Outlet on the hinge axis", world(D), "L")]
    c.move(5.0, lambda t, i, n: dict(st=L.State(ext=PARK_DROP, tilt=40.0 * math.sin(math.pi * t), magnet_on=True, **S0),
                                     cam=((H[0] + 110, H[1], H[2] + 30), (-0.45, -1.0, 0.35), 620),
                                     hide=lambda p: R.station_cut(p) or p.group in ("elec", "station_ec", "station_act", "frame", "plates", "drive") or p.key in ("latch_rail", "hold_down", "hall_switch") or (p.module >= 0 and p.module != 0),
                                     focus=foc4, labels=lab4, readout=lambda st: f"tilt {st.tilt:4.1f} deg",
                                     text="Only at the station, where the EC carries it (hidden here): the module turns about its two hinge pins, cap "
                                          "end up, through the carriage's opening into the loop. The outlet stays on the hinge axis. 40 deg at most.",
                                     save_as="c04" if preview else None), eased=False)
    c.hold(1.0)

    # 5. the latch
    c.chapter(5, "The plate's clip: a spring latch pin")
    foc5 = lambda p: p.key in ("latch_bolt", "latch_follower", "latch_spring", "latch_rail") or (p.module == 0 and p.key in ("sam_mounting_plate", "carriage"))  # noqa: E731
    lab5 = [("4 mm pin in the keeper's hole:\nholds the plate either way", part("latch_bolt", module=0), "L"),
            ("Keeper on the plate", sam(0, (102.0, 19.0, -13.5)), "L"),
            ("Spring", part("latch_spring", module=0), "R"),
            ("Follower (3 mm dowel)", part("latch_follower", module=0), "R"),
            ("Only the station's cam\npushes the pin out", part("latch_rail", local=(119.0, 31.0, 22.0)), "R")]
    hide5 = latch_hide
    c.move(6.0, lambda t, i, n: dict(st=L.State(shift=-RUN_DIRECTION * 2.2 * (1 - 2 * t), ext=0.0, **S0), cam=CAM_LATCH, hide=hide5, focus=foc5,
                                     labels=lab5, readout=lambda st: f"latch pin {max(L.latch_open(k, st) for k in range(13)):3.1f} of {LATCH_TRAVEL} mm out",
                                     text="The latch rides on the carriage: a spring keeps its 4 mm pin 4 mm deep in the plate's keeper, so the module "
                                          "can't swing off whichever way up it is. Passing the station, the follower rides the station cam's ramps: "
                                          "the pin is pushed out, then springs back in.", save_as="c05" if preview else None), eased=False)
    c.hold(1.5)

    # 6. round the loop
    c.chapter(6, "Round the loop: hanging, sideways, on top")
    foc6 = lambda p: p.module == 0 or p.group == "chain"  # noqa: E731
    lab6 = [("Carriage 1 and its module", sam(0, (150.0, 0.0, 0.0)), "R"),
            ("Hinge pins and the latch pin\nhold the plate to the carriage", part("latch_bolt", module=0), "L")]

    def orient(st):
        C = L.carriage_frame(int(round(L.slot_of(0, st.shift))) % N_LINKS, 0.0)
        w = C[:3, 1]
        if w[2] > 0.7:
            return "module hangs under the run"
        if w[2] < -0.7:
            return "module sits on top of the run"
        return "module on its side"

    def loop_frame(t, i, n):
        s = RUN_DIRECTION * 52.0 * t
        st = L.State(shift=s, ext=0.0, **S0)
        pl = L.placements(st)
        cm = next(p.M for p in pl if p.key == "carriage" and p.module == 0)
        foc_pt = (WM @ cm @ np.r_[0.0, -30.0, 150.0, 1.0])[:3]
        cam = ((float(foc_pt[0]), float(foc_pt[1]) * 0.8, float(foc_pt[2]) * 0.8 + 0.2 * 628), (-1.0, -0.3, 0.15), 620)
        return dict(st=st, cam=cam, hide=lambda p: R.front_open(p) or p.group in ("elec",), focus=foc6, labels=lab6,
                    readout=f"chain {abs(s) * 9.525:5.0f} mm\n{orient(st)}",
                    text="Half a lap: under the bottom run the module hangs, up the side it is on its side, on the top run it sits on "
                         "the loop. Nothing but its two hinge pins and the latch pin holds it, and the outlet door stays shut.",
                    save_as="c06" if preview else None)
    c.move(7.0, loop_frame, eased=True)
    c.hold(1.0)

    # 7. the door, from the carriage's side
    c.chapter(7, "The outlet door: shut except at the station")
    foc7 = keys("door_housing", "door_shutter", "door_spring", "door_spring_open", "sam_electronics_carriage")
    lab7 = [("Shutter over the 3 mm exit", part("door_shutter", module=0), "L"),
            ("Spring", part("door_spring", module=0), "R"),
            ("EC's finger (station)", ec((-2.1, 7.5, 20.0)), "L")]
    lab7b = [lab7[0], ("Spring (compressed)", part("door_spring_open", module=0), "R"), lab7[2]]
    c.move(3.5, lambda t, i, n: dict(st=L.State(ext=PARK_DROP - DOOR_TRAVEL - 2.0 + (DOOR_TRAVEL + 2.0) * math.sin(math.pi * t), **S0),
                                     cam=CAM_DOOR, hide=lambda p: R.dock_cut(p) or p.group == "elec", focus=foc7,
                                     opacity=lambda pl: {k: 0.45 for k, p in R.keyed(pl) if p.key == "door_housing" and p.module == 0},
                                     labels=lab7, readout=lambda st: f"door {L.door_open(st):3.1f} of {DOOR_TRAVEL:.0f} mm open",
                                     text="The spring keeps the shutter over the exit everywhere on the loop. Only the docked EC's finger opens it "
                                          "(6 mm), and it shuts again as the EC leaves.", save_as="c07" if preview else None), eased=False)
    c.hold(1.0)

    # 8. swap
    c.chapter(8, "Swap at the side hatch: the side tabs take the pull")
    foc8 = lambda p: p.module == k0 or p.key in ("side_tab", "side_tab_m", "m5x8_shcs", "hatch_side")  # noqa: E731
    lab8 = [("Side tab (front plate):\nits foot 1 mm outside the tongue", part("side_tab"), "L"),
            ("Side tab (back plate)", part("side_tab_m"), "R"),
            ("Pull the auger straight\noff its plate", sam(k0, (180.0, 0.0, 0.0)), "R"),
            ("Plate, door and carriage\nstay on the chain", sam(k0, (60.0, 22.0, -15.0)), "L"),
            ("Side hatch", part("hatch_side"), "R")]

    def swap_frame(t, i, n):
        if t < 0.5:
            out_, col = 140.0 * R.ease(t / 0.5), None
            txt = ("At the loading position, behind the side hatch: pull the auger straight out of its plate's clamps. The pull goes "
                   "into the side tabs, not the chain.")
        else:
            out_, col = 140.0 * (1 - R.ease((t - 0.5) / 0.5)), (0.1, 0.65, 0.35)
            txt = "A different powder's auger (green) clips into the same plate. A whole carriage comes off the same way it went on."
        st = L.State(ext=0.0, hatch_side=HATCH_OPEN_DEG, out_auger=k0, auger_out=out_, enclosure=True, scale=False)
        acc = (lambda p: col if (col and p.module == k0 and p.key in ("auger", "auger_cap")) else None) if col else None
        return dict(st=st, cam=CAM_LOAD, hide=lambda p: p.group == "elec" or (p.group == "enclosure" and p.key not in ("hatch_side", "panel_side_hatch", "hinge_leaf", "catch")),
                    focus=foc8, accent=acc, labels=lab8, text=txt, save_as="c08" if preview else None)
    c.move(6.0, swap_frame, eased=False)
    c.hold(2.5)
    c.done()


if __name__ == "__main__":
    pv = "--preview" in sys.argv
    if "station" in sys.argv:
        station(pv)
    if "carriage" in sys.argv:
        carriage(pv)
