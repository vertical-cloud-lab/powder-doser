"""v5 renders of the balance under the station: stills and the balance-dose clip (MP4 + GIF).

    xvfb-run -a python render_balance.py            # stills (renders/*.png) and renders/features/balance_dose.{mp4,gif}
    xvfb-run -a python render_balance.py --stills   # stills only
    xvfb-run -a python render_balance.py --clip     # the clip only

The clip: the beaker goes in through the HR-202i's -y side door, the top door slides back, the EC rises on its lift bar
and docks, the module tilts to 30 deg and doses (the grains drawn falling from the exit to the beaker; the reading is the
dose so far at the lab's 0.1 mg readability), tilts back and reverses, the EC parks, the top door shuts, and the beaker
comes out. The dose figures are illustrative (105 mg per auger turn at 60 rpm, powder-doser's salt), not a simulation.
"""
from __future__ import annotations

import math
import sys

import numpy as np
import vtk
from PIL import Image, ImageDraw

import layout as L
import render as R
from params import BEAKER_D, BEAKER_H, BEAKER_RIM_Z, HR2_PAN_TOP, PARK_DROP, TILT_DOSE_WORLD
import parts5 as P5

R.TAG = "chain carousel v5, #128"
OUT = R.OUT
D = L.DOSE_POINT
TF = L.frame_dose_tilt(TILT_DOSE_WORLD)
TOP_OPEN = P5.HR2_TOP_OPEN
SIDE_OPEN = P5.HR2_DOOR_OPEN

GLASSY = ("hr202i_front_glass", "hr202i_door_left", "hr202i_door_right", "hr202i_top_door", "beaker")


def opac(pl, extra=None):
    """See-through: acrylic, the balance's glass and the beaker; optionally more parts by key."""
    o = {}
    for k, p in R.keyed(pl):
        if p.key in GLASSY:
            o[k] = 0.28
        elif p.key.startswith(("panel_", "hatch_")):
            o[k] = 0.18
        elif p.key == "hr100a_body":
            o[k] = 0.95                                 # v5: it fits, so it isn't drawn as v3/v4's ghost
        elif p.key == "hr100a_glass":
            o[k] = 0.3
        elif extra and p.key in extra:
            o[k] = extra[p.key]
    return o


def cut_front(p) -> bool:
    """Look in through the front: no enclosure, no front side plate and nothing bolted outside it (v4's front_open), but keep
    the balance."""
    if p.group == "enclosure":
        return True
    return p.key == "side_plate_front" or (p.M[0, 3] < -30.5 and p.key not in ("ext_x", "foot", "board_panel") and p.group != "scale") or \
        (p.key == "m5x12_bhcs" and p.M[0, 3] < -29.0)


def cut_section(p) -> bool:
    """Side section on the station's centre plane, seen from +y: cut_front, plus everything on the near (+y) side of the
    station: the +y P16, its bar end and shelf, the +y frame members and modules, the NEMA 34 and the balance's +y door. The
    station module, the EC and the lift bar stay; the -y P16 shows behind them."""
    if cut_front(p):
        return True
    y = p.M[1, 3]
    if p.group == "scale":
        return p.key == "hr202i_door_right"
    if p.group in ("station_ec", "station_act") or (p.group == "modules" and p.module == 0):
        return y > L.STATION_Y + 60.0
    if p.group == "drive":
        return True
    return y > L.STATION_Y + 30.0


class Grains:
    """Small spheres for the dose stream, added straight to the renderer."""

    def __init__(self, view: R.View, n: int = 60):
        self.view, self.actors = view, []
        src = vtk.vtkSphereSource()
        src.SetRadius(0.9)
        src.SetThetaResolution(8)
        src.SetPhiResolution(6)
        src.Update()
        for _ in range(n):
            m = vtk.vtkPolyDataMapper()
            m.SetInputData(src.GetOutput())
            a = vtk.vtkActor()
            a.SetMapper(m)
            a.GetProperty().SetColor(0.92, 0.92, 0.88)
            a.VisibilityOff()
            view.ren.AddActor(a)
            self.actors.append(a)
        self.rng = np.random.default_rng(3)
        self.phase = self.rng.uniform(0, 1, n)
        self.jit = self.rng.normal(0, 0.8, (n, 2))

    def set(self, t: float, on: bool, z_land: float) -> None:
        """Grains falling from the exit (on the hinge axis, so it doesn't move with the tilt) to z_land; t in seconds."""
        fall = D[2] - z_land
        tf = math.sqrt(2 * fall / 9810.0)
        for i, a in enumerate(self.actors):
            if not on:
                a.VisibilityOff()
                continue
            u = (t / tf + self.phase[i]) % 1.0
            dz = 0.5 * 9810.0 * (u * tf) ** 2
            x = D[0] - 2.0 + self.jit[i, 0] * (0.4 + u) - 6.0 * u * (u * tf)        # leaves with a little forward speed
            y = D[1] + self.jit[i, 1] * (0.4 + u)
            a.SetPosition(x, y, D[2] - 2.0 - dz)
            a.VisibilityOn()


def reading_box(img: Image.Image, grams: float, stable: bool, note: str = "") -> Image.Image:
    d = ImageDraw.Draw(img)
    W, H = img.size
    s = max(16, W // 62)
    x0, y0 = int(W - s * 15.5), int(H - s * 4.6)
    d.rectangle([x0, y0, W - s, H - int(s * 1.9)], fill=(25, 28, 32))
    d.text((x0 + s * 0.6, y0 + s * 0.3), "A&D HR-202i  220 g x 0.1 mg", fill=(170, 200, 170), font=R.font(int(s * 0.62)))
    d.text((x0 + s * 0.6, y0 + s * 1.05), f"{'ST' if stable else 'US'} {grams:9.4f} g", fill=(140, 255, 140), font=R.font(int(s * 1.15)))
    if note:
        d.text((x0 + s * 0.6, y0 + s * 2.3), note, fill=(150, 170, 150), font=R.font(int(s * 0.55)))
    return img


SECTION = ((D[0] + 40, D[1], 300.0), (0.0, 1.0, 0.0), 1250)
FRONT = ((40.0, D[1], 330.0), (-1.0, -0.62, 0.32), 1500)
LIFT = ((95.0, D[1], 330.0), (0.55, -1.0, 0.28), 900)
CLOSE = ((D[0] + 20, D[1] - 10, 330.0), (-0.35, -1.0, 0.12), 620)


def stills() -> None:
    v = R.View(1600, 1000)
    shots = [
        ("rig_iso", L.State(), None, R.HERO, "Chain carousel v5: the A&D HR-202i under the station (enclosure outlined)"),
        ("rig_balance_front", L.State(top_door=TOP_OPEN), cut_front, FRONT,
         "v5 from the front: the HR-202i under the dose point, the lift bar on two P16s beside it"),
        ("rig_lift_bar", L.State(ext=PARK_DROP, top_door=TOP_OPEN), cut_front, LIFT,
         "The EC docked on its lift bar; the bar's end shoes have just left their guides"),
        ("rig_dose30_section", L.State(tilt=TF, top_door=TOP_OPEN, magnet_on=True), cut_section, SECTION,
         "Section on the station's centre plane: module 1 at 30 deg over the beaker on the HR-202i's pan"),
        ("rig_parked_section", L.State(ext=0.0), cut_section, SECTION,
         "Parked: the EC 28 mm under its dock, 12 mm over the balance's top; the top door shut"),
        ("rig_hr100a", L.State(scale_model="hr100a"), cut_front, FRONT,
         "The lab's HR-100A (stock breeze break) in the same place: nothing in its way but the front hatch door's bottom edge"),
    ]
    for name, st, cut, cam, title in shots:
        pl = L.placements(st)
        v.show(pl, hide=R.hidden(pl, cut), opacity=opac(pl), colors={k: (0.93, 0.93, 0.95) for k, p in R.keyed(pl) if p.key == "hr100a_body"})
        v.camera(*cam)
        img = R.caption(v.image(), title, "", R.TAG)
        img.save(OUT / f"{name}.png")
        print("  ", name, flush=True)


def clip() -> None:
    c = R.Clip("balance_dose", w=1280, h=720, fps=12)
    g = Grains(c.v)
    sec = lambda s: max(2, int(s * 12))  # noqa: E731
    dose_rate = 0.105                      # g per auger turn (salt, 60 rpm): 0.105 g/s
    z_land = BEAKER_RIM_Z - BEAKER_H + 6.0
    state = dict(m=0.0, t=0.0)

    def frame(st, title, sub, cam, cut=cut_section, grains=False, stable=True, note=""):
        pl = L.placements(st)
        c.v.show(pl, hide=R.hidden(pl, cut), opacity=opac(pl))
        g.set(state["t"], grains, z_land)
        c.v.camera(*cam)
        img = R.caption(c.v.image(), title, sub, R.TAG)
        c._emit(reading_box(img, state["m"], stable, note))

    # 1. the beaker in through the -y side door (along y), onto the riser
    for i in range(sec(2.0)):
        t = R.ease(i / (sec(2.0) - 1))
        frame(L.State(ext=0.0, side_door=SIDE_OPEN * t), "Open the front hatch and the balance's -y side door", "", FRONT, cut_front)
    for i in range(sec(2.5)):
        t = R.ease(i / (sec(2.5) - 1))
        st = L.State(ext=0.0, side_door=SIDE_OPEN, beaker=True, beaker_dy=-150.0 * (1 - t), beaker_dz=6.0 * (1 - t))
        frame(st, "The beaker goes onto its riser on the pan", "lifted 6 mm over the riser's cup, then down into it: rim 282 mm up", FRONT, cut_front)
    for i in range(sec(1.5)):
        t = R.ease(i / (sec(1.5) - 1))
        frame(L.State(ext=0.0, side_door=SIDE_OPEN * (1 - t)), "Side door shut; tare", "", FRONT, cut_front, note="tare")
    # 2. top door back, EC up and docks
    for i in range(sec(1.5)):
        t = R.ease(i / (sec(1.5) - 1))
        frame(L.State(ext=0.0, top_door=TOP_OPEN * t), "The top door slides back over the tower", "the only opening into the chamber while it doses",
              SECTION)
    for i in range(sec(3.0)):
        t = R.ease(i / (sec(3.0) - 1))
        frame(L.State(ext=PARK_DROP * t, top_door=TOP_OPEN, magnet_on=t > 0.9), "Two P16s lift the bar; the EC docks",
              f"the bar's end shoes keep it square in their guides until it seats; {PARK_DROP * (1 - t):4.1f} mm to go", SECTION)
    # 3. tilt and dose
    for i in range(sec(2.0)):
        t = R.ease(i / (sec(2.0) - 1))
        frame(L.State(tilt=TF * t, top_door=TOP_OPEN, magnet_on=True), f"Tilt to {TF:.0f} deg", "the exit stays on the hinge axis, over the beaker",
              SECTION)
    n = sec(5.0)
    for i in range(n):
        state["t"] += 1 / 12
        state["m"] = dose_rate * state["t"]
        frame(L.State(tilt=TF, top_door=TOP_OPEN, magnet_on=True, spin=state["t"] * 2 * math.pi), "Dosing straight into the beaker on the pan",
              f"{D[2] - BEAKER_RIM_Z:.0f} mm from the exit to the rim; no funnel; the Pi reads the balance over RS-232 ('Q') and stops at the target", SECTION,
              grains=True, stable=False)
    # 4. back, reverse, park, top door shut
    for i in range(sec(2.0)):
        t = R.ease(i / (sec(2.0) - 1))
        frame(L.State(tilt=TF * (1 - t), top_door=TOP_OPEN, magnet_on=True), "Hold 0.5 s, tilt back, reverse one turn at rest", "", SECTION,
              stable=i > sec(1.5))
    for i in range(sec(2.5)):
        t = R.ease(i / (sec(2.5) - 1))
        frame(L.State(ext=PARK_DROP * (1 - t), top_door=TOP_OPEN * (1 - max(0.0, t - 0.4) / 0.6)),
              "The EC parks; the top door slides shut", "", SECTION, note="settled")
    for i in range(sec(1.5)):
        frame(L.State(ext=0.0), "Read the dose with every door shut", f"{state['m']:.4f} g", FRONT, cut_front, note="stable reading")
    # 5. the beaker out
    for i in range(sec(2.0)):
        t = R.ease(i / (sec(2.0) - 1))
        st = L.State(ext=0.0, side_door=SIDE_OPEN, beaker_dy=-150.0 * t, beaker_dz=6.0 * min(1.0, 4 * t))
        frame(st, "The beaker comes out through the side door", "", FRONT, cut_front)
    for _ in range(sec(1.0)):
        c._emit(c.last)
    c.done()


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    if "--hr100a" in sys.argv:
        v = R.View(1600, 1000)
        pl = L.placements(L.State(scale_model="hr100a"))
        v.show(pl, hide=R.hidden(pl, cut_front), opacity=opac(pl), colors={k: (0.93, 0.93, 0.95) for k, p in R.keyed(pl) if p.key == "hr100a_body"})
        v.camera(*FRONT)
        R.caption(v.image(), "The lab's HR-100A (stock breeze break) in the same place: nothing in its way but the front hatch door's bottom edge",
                  "", R.TAG).save(OUT / "rig_hr100a.png")
        sys.exit()
    if "--clip" not in sys.argv:
        stills()
    if "--stills" not in sys.argv:
        clip()
