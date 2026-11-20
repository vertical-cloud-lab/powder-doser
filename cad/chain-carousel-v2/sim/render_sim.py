"""Render a carousel_sim.py trajectory with the real CAD (VTK, offscreen).

    xvfb-run -a python sim/render_sim.py sim/results/lap_v50_h10 --mp4 --gif
    xvfb-run -a python sim/render_sim.py sim/results/lap_v50_h10 --stills 0 0.5 1.0   # PNG at these times (s)

Every part keeps the look of render.py. Static parts sit where layout.py
puts them; the chains, carriages, modules, shafts and sprockets follow the
simulated poses in poses.npz; the drive chain and the motor sprocket turn
with the drive shaft. The station is drawn retracted (layout.State(ext=0)),
as it is whenever the chain moves.
"""
from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import numpy as np
import vtk
import vtk.util.numpy_support  # noqa: F401
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import layout as L  # noqa: E402
import render as RD  # noqa: E402
from params import *  # noqa: E402,F401,F403

def _actor(pz) -> vtk.vtkActor:
    """A VTK actor for a placement, with render.py's tessellation cache and material."""
    if pz.key not in RD._PD:
        RD._PD[pz.key] = RD.polydata(pz.key)
    m = vtk.vtkPolyDataMapper()
    m.SetInputData(RD._PD[pz.key])
    a = vtk.vtkActor()
    a.SetMapper(m)
    pr = a.GetProperty()
    pr.SetAmbient(0.25)
    pr.SetDiffuse(0.75)
    pr.SetSpecular(0.15)
    pr.SetSpecularPower(20)
    pr.SetColor(*pz.color)
    a.SetUserMatrix(RD.vmat(pz.M))
    return a


C_FRONT = L.T(L.cols((-1, 0, 0), (0, -1, 0), (0, 0, 1)))     # parts.py link frame relative to the sim link frame
C_BACK = L.T(L.cols((1, 0, 0), (0, -1, 0), (0, 0, -1)))


def advance_loop(pins: np.ndarray, s_mm: float) -> np.ndarray:
    """Pin positions of a chain loop advanced by s_mm along its own path."""
    n = len(pins)
    seg = np.linalg.norm(np.roll(pins, -1, axis=0) - pins, axis=1)
    cum = np.concatenate([[0.0], np.cumsum(seg)])
    total = cum[-1]
    out = np.zeros_like(pins)
    for j in range(n):
        d = (cum[j] + s_mm) % total
        k = int(np.searchsorted(cum, d, side="right") - 1) % n
        f = (d - cum[k]) / seg[k]
        out[j] = pins[k] + f * (pins[(k + 1) % n] - pins[k])
    return out


class SimScene:
    def __init__(self, run_dir: Path, hide=None, docked=False):
        self.data = np.load(run_dir / "poses.npz")
        self.t = self.data["t"]
        self.hide = hide
        pl = L.placements(L.State(ext=0.0))             # the station retracted, as it is whenever the chain moves
        self.view = RD.View(w=1600, h=1000)
        self.static = []
        self.dyn = []                        # (actor, kind, index, rel)
        carriages = {k: L.carriage_frame(li) for k, li in enumerate(L.carriage_links())}
        sams = {k: L.sam_frame(C) for k, C in carriages.items()}
        corners = {n: L.T(None, (0.0, y, z)) for n, (y, z) in L.CORNERS.items()}
        self.corner_names = list(L.CORNERS)
        chain_i = {False: 0, True: 0}
        self.drive_links = []
        for pz in pl:
            name, key = pz.name, pz.key
            chain_idx = None
            if pz.group == "chain":                            # main chain links, in placement order (front 0-103, then back)
                back = "(back)" in name or pz.M[0, 3] > CHAIN_L / 2
                chain_idx = (back, chain_i[back])
                chain_i[back] += 1
            if hide is not None and hide(pz):
                continue
            a = _actor(pz)
            self.view.ren.AddActor(a)
            if chain_idx is not None:
                back, i = chain_idx
                self.dyn.append((a, "chain_back" if back else "chain_front", i, C_BACK if back else C_FRONT))
            elif pz.module >= 0 and (pz.group == "carriages" or key in ("clevis_pin", "eclip")):
                rel = np.linalg.inv(carriages[pz.module]) @ pz.M        # carriage, tab screws, nuts, magnets, hinge pins
                self.dyn.append((a, "carriages", pz.module, rel))
            elif pz.module >= 0 and pz.group == "modules":
                rel = np.linalg.inv(sams[pz.module]) @ pz.M             # plate, steel tab, auger, cap: turn on the hinge
                self.dyn.append((a, "modules", pz.module, rel))
            elif pz.step == 5 and (key.startswith("sprocket_32") or key.startswith("shaft")):
                cn = name.split()[2] if key.startswith("sprocket") else name.split()[1]
                rel = np.linalg.inv(corners[cn]) @ pz.M
                self.dyn.append((a, "corner", self.corner_names.index(cn), rel))
            elif pz.step == 6 and key in ("sprocket_15_shaft", "sprocket_15_motor"):
                centre = L.T(None, (pz.M[0, 3], LOOP_Y, Z_BOT if key == "sprocket_15_shaft" else Z_MOTOR))
                rel = np.linalg.inv(centre) @ pz.M
                self.dyn.append((a, "spin", (centre, 1.0), rel))
            elif pz.step == 6 and key in ("chain_outer", "chain_inner"):
                self.drive_links.append((a, len(self.drive_links)))
        self.drive_pins = L.drive_chain_pins()

    @staticmethod
    def _vm(M):
        vm = vtk.vtkMatrix4x4()
        for i in range(4):
            for j in range(4):
                vm.SetElement(i, j, float(M[i, j]))
        return vm

    def set_frame(self, f: int):
        d = self.data
        ang = d["corner_angles"][f]
        for a, kind, idx, rel in self.dyn:
            if kind in ("chain_front", "chain_back", "carriages", "modules"):
                M = d[kind][f, idx] @ rel
            elif kind == "corner":
                th = ang[idx]
                n = self.corner_names[idx]
                y, z = L.CORNERS[n]
                M = L.T(None, (0, y, z)) @ L.T(L.Rx(th)) @ L.T(None, (0, -y, -z)) @ (L.T(None, (0, y, z)) @ rel)
            elif kind == "spin":
                centre, ratio = idx
                th = ang[self.corner_names.index(L.DRIVE)] * ratio
                M = centre @ L.T(L.Rx(th)) @ rel
            a.SetUserMatrix(self._vm(M))
        # drive chain: advance along its own loop by the drive sprocket's arc
        th = ang[self.corner_names.index(L.DRIVE)]
        pins = advance_loop(self.drive_pins, -th * PD15 / 2)
        n = len(pins)
        for a, j in self.drive_links:
            a_, b_ = pins[j], pins[(j + 1) % n]
            ty, tz = (b_ - a_) / np.linalg.norm(b_ - a_)
            M = L.T(L.cols((0, -ty, -tz), (0, tz, -ty), (1, 0, 0)), (L.X_DRV, (a_[0] + b_[0]) / 2, (a_[1] + b_[1]) / 2))
            a.SetUserMatrix(self._vm(M))

    def image(self, f: int, cam: dict, label: str = "") -> Image.Image:
        self.set_frame(f)
        self.view.camera(**cam)
        img = self.view.image()
        if label:
            d = ImageDraw.Draw(img)
            d.rectangle((0, 0, img.width, 44), fill=(255, 255, 255))
            d.text((20, 8), label, fill=(30, 30, 30), font=RD.font(26))
        return img


_DZ = Z_RUN - 210.0                          # the cameras were set up with the bottom run at 210 mm; the loop was raised
CAMS = {
    "loop": dict(focal=(120, 0, 370 + _DZ), direction=(-1.0, -0.42, 0.22), dist=1250),
    "iso": dict(focal=(150, 0, 330 + _DZ), direction=(-0.9, -1.0, 0.55), dist=1600),
    "station": dict(focal=(90, 0, 215 + _DZ), direction=(-1.0, -0.65, -0.25), dist=620),
    "corner": dict(focal=(70, 80, 245 + _DZ), direction=(-1.0, 0.28, 0.1), dist=470),
    "top": dict(focal=(120, 0, 520 + _DZ), direction=(-1.0, -0.3, 0.35), dist=600),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir")
    ap.add_argument("--cam", default="loop", choices=list(CAMS))
    ap.add_argument("--mp4", action="store_true")
    ap.add_argument("--gif", action="store_true")
    ap.add_argument("--stills", type=float, nargs="*")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--every", type=int, default=1, help="render every n-th stored frame")
    ap.add_argument("--open", action="store_true", help="hide the front plate and its hardware (default for loop/station/corner)")
    ap.add_argument("--label", default="")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    run_dir = Path(a.run_dir)
    hide = RD.front_open if (a.open or a.cam in ("loop", "station", "corner", "top")) else None
    scene = SimScene(run_dir, hide=hide)
    cam = CAMS[a.cam]
    out = Path(a.out) if a.out else run_dir
    out.mkdir(parents=True, exist_ok=True)
    tag = f"{run_dir.name}_{a.cam}"
    if a.stills is not None:
        for ts in (a.stills or [0.0]):
            f = int(np.argmin(np.abs(scene.t - ts)))
            img = scene.image(f, cam, f"{a.label}  t = {scene.t[f]:.2f} s".strip())
            img.save(out / f"{tag}_t{ts:05.2f}.png")
            print("wrote", out / f"{tag}_t{ts:05.2f}.png")
        return
    frames = []
    idx = list(range(0, len(scene.t), a.every))
    for n, f in enumerate(idx):
        img = scene.image(f, cam, f"{a.label}  t = {scene.t[f]:.2f} s".strip())
        frames.append(img)
        if n % 50 == 0:
            print(f"frame {n}/{len(idx)}", flush=True)
    if a.mp4:
        import imageio.v2 as imageio
        w = imageio.get_writer(str(out / f"{tag}.mp4"), fps=a.fps, codec="libx264", quality=8, macro_block_size=8,
                               ffmpeg_params=["-pix_fmt", "yuv420p"])
        for im in frames:
            w.append_data(np.asarray(im))
        w.close()
        print("wrote", out / f"{tag}.mp4")
    if a.gif:
        small = [im.resize((800, int(800 * im.height / im.width)), Image.LANCZOS).quantize(colors=128, method=Image.MEDIANCUT)
                 for im in frames[::3]]
        small[0].save(out / f"{tag}.gif", save_all=True, append_images=small[1:], duration=int(3000 / a.fps), loop=0, optimize=True)
        print("wrote", out / f"{tag}.gif")


if __name__ == "__main__":
    main()
