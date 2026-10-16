"""Render the carousel videos (MP4 H.264 1280x720 30 fps + GIF) by re-running the simulations.

    MUJOCO_GL=glfw xvfb-run -a -s "-screen 0 1920x1080x24" python render.py [lap|station|fastlap|test]

Chains are drawn per link from kinematics.pin_positions (visual only) and the
sprockets carry three spokes turned by kinematics.sprocket_angle.
"""
from __future__ import annotations

import math
import os
import subprocess
import sys

import imageio
import imageio_ffmpeg
import mujoco
import numpy as np
from PIL import Image, ImageDraw, ImageFont

import carousel_sim as C
import model as M
from model import KN, MM, PR

W, H = 1280, 720
OUT = M.OUT
try:
    FONT = ImageFont.load_default(size=20)
    FONT_B = ImageFont.load_default(size=24)
except TypeError:  # old Pillow
    FONT = FONT_B = ImageFont.load_default()

CORNERS = [(PR.CORNER_Y, PR.Z_BOT), (PR.CORNER_Y, PR.Z_TOP), (-PR.CORNER_Y, PR.Z_TOP), (-PR.CORNER_Y, PR.Z_BOT)]


def _cap(scn, a, b, r, rgba):
    if scn.ngeom >= scn.maxgeom:
        return
    g = scn.geoms[scn.ngeom]
    mujoco.mjv_initGeom(g, mujoco.mjtGeom.mjGEOM_CAPSULE, np.zeros(3), np.zeros(3), np.eye(3).flatten(),
                        np.asarray(rgba, np.float32))
    mujoco.mjv_connector(g, mujoco.mjtGeom.mjGEOM_CAPSULE, r, np.asarray(a, float), np.asarray(b, float))
    scn.ngeom += 1


def add_chain(scn, shift):
    pins = KN.pin_positions(shift) * MM
    nxt = np.roll(pins, -1, axis=0)
    sa1 = {M.PR.MODULE_LINKS * k % PR.N_LINKS for k in range(M.NK)}
    for x in (0.0, M.L_X):
        for j in range(PR.N_LINKS):
            col = (0.85, 0.25, 0.20, 1) if j in sa1 else ((0.30, 0.31, 0.33, 1) if j % 2 else (0.55, 0.56, 0.58, 1))
            _cap(scn, (x, *pins[j]), (x, *nxt[j]), 0.0028, col)
    a = KN.sprocket_angle(shift)
    for cy, cz in CORNERS:
        for x in (-0.0035, M.L_X + 0.0035):
            for i in range(3):
                ang = a + 2 * math.pi * i / 3
                _cap(scn, (x, cy * MM, cz * MM), (x, cy * MM + 0.042 * math.cos(ang), cz * MM + 0.042 * math.sin(ang)),
                     0.0030, (0.85, 0.85, 0.20, 1))


def overlay(frame, lines, title):
    im = Image.fromarray(frame)
    dr = ImageDraw.Draw(im, "RGBA")
    dr.rectangle([0, 0, W, 34], fill=(20, 22, 26, 200))
    dr.text((12, 5), title, fill=(255, 255, 255, 255), font=FONT_B)
    y = H - 12 - 26 * len(lines)
    dr.rectangle([0, y - 8, 760, H], fill=(20, 22, 26, 170))
    for ln in lines:
        dr.text((12, y), ln, fill=(255, 255, 255, 255), font=FONT)
        y += 26
    return np.asarray(im)


class Recorder:
    def __init__(self, name, cams, title, text_fn, fade_others=False, every=1, shadows=True, samples=8):
        self.name, self.cams, self.title, self.text_fn = name, cams, title, text_fn
        self.every, self.shadows, self.samples, self.k = every, shadows, samples, 0
        self.r = None
        self.fade = fade_others
        self.path = os.path.join(OUT, f"{name}.mp4")
        self.w = imageio.get_writer(self.path, fps=30, codec="libx264", quality=7, pixelformat="yuv420p",
                                    macro_block_size=8, ffmpeg_params=["-preset", "medium"])
        self.n = 0

    def __call__(self, m, d, info):
        self.k += 1
        if (self.k - 1) % self.every:
            return
        if self.r is None:
            m.vis.quality.offsamples = self.samples
            if self.fade:
                others = {m.body(f"g{k}").id for k in range(1, M.NK)}
                for gi in range(m.ngeom):
                    nm = mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_GEOM, gi) or ""
                    if nm.startswith("strip"):
                        continue
                    if m.geom_bodyid[gi] in others or (m.geom_bodyid[gi] == 0 and m.geom_size[gi][0] < 0.02 and m.geom_type[gi] == mujoco.mjtGeom.mjGEOM_BOX):
                        m.geom_matid[gi] = -1
                        m.geom_rgba[gi] = (0.95, 0.6, 0.3, 0.15)
            self.r = mujoco.Renderer(m, H, W // len(self.cams), max_geom=4000)
            self.r.scene.flags[mujoco.mjtRndFlag.mjRND_SHADOW] = self.shadows
        imgs = []
        for cam in self.cams:
            self.r.update_scene(d, camera=cam)
            add_chain(self.r.scene, info["shift"])
            imgs.append(self.r.render().copy())
        frame = np.concatenate(imgs, axis=1)
        frame = overlay(frame, self.text_fn(info), self.title)
        for _ in range(self.every):
            self.w.append_data(frame)
            self.n += 1
        if self.n % 60 == 0:
            print(self.name, self.n, "frames", flush=True)

    def close(self, gif_fps=10, gif_w=720):
        self.w.close()
        gif = os.path.join(OUT, f"{self.name}.gif")
        ff = imageio_ffmpeg.get_ffmpeg_exe()
        vf = (f"fps={gif_fps},scale={gif_w}:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=128:stats_mode=diff[p];"
              "[s1][p]paletteuse=dither=bayer:bayer_scale=4:diff_mode=rectangle")
        subprocess.run([ff, "-y", "-loglevel", "error", "-i", self.path, "-vf", vf, gif], check=True)
        if os.path.getsize(gif) > 10e6:
            subprocess.run([ff, "-y", "-loglevel", "error", "-i", self.path, "-vf", vf.replace(f"fps={gif_fps}", "fps=7").replace(f"scale={gif_w}", "scale=640"), gif], check=True)
        print(self.path, os.path.getsize(self.path) / 1e6, "MB;", gif, os.path.getsize(gif) / 1e6, "MB;", self.n, "frames")


def lap(name="lap_index", T=1.5, title=None):
    """Recommended profile: trapezoid whose acceleration lasts one pendulum period, 1.5 s per index."""
    fz = C.pendulum()["f_Hz"]
    kw = dict(fa=1 / fz / T)
    sh, stops = M.sequence(KN.HOME_SHIFT, [(PR.MODULE_LINKS, T, "trap", 0.5, kw)] * 12)
    hist = []

    def txt(info):
        th = np.abs(info["th"]) * C.RAD
        hist.append(th.max())
        k = int(np.argmax(th))
        done = (info["shift"] - KN.HOME_SHIFT) / PR.MODULE_LINKS
        idx = int(min(12, math.ceil(done - 1e-6)))
        return [f"t = {info['t']:5.2f} s   chain shift = {info['shift'] - KN.HOME_SHIFT:6.2f} links   index {idx}/12",
                f"largest swing now {th.max():4.1f} deg (module {k})   max so far {max(hist):4.1f} deg   pendulum {fz:.2f} Hz"]
    rec = Recorder(name, ["side", "iso"], title or f"RECOMMENDED: trapezoid, accel = one pendulum period ({1 / fz:.2f} s), {T:.1f} s per index",
                   txt, every=2, shadows=False, samples=4)
    C.run_carousel(sh, dict(damping=1e-4), frame_cb=rec)
    rec.close()


def fastlap(name="fastlap_10s", Tlap=10.0, fa=0.1):
    sh, _ = M.sequence(KN.HOME_SHIFT, [(PR.N_LINKS, Tlap, "scurve", 1.5, dict(fa=fa))])
    hist = []

    def txt(info):
        th = np.abs(info["th"]) * C.RAD
        hist.append(th.max())
        return [f"t = {info['t']:5.2f} s   chain shift = {info['shift'] - KN.HOME_SHIFT:6.2f} links",
                f"largest swing now {th.max():4.1f} deg   max so far {max(hist):4.1f} deg"]
    rec = Recorder(name, ["side", "iso"], f"Continuous lap in {Tlap:g} s (S-curve speed profile)", txt)
    C.run_carousel(sh, dict(damping=1e-4), frame_cb=rec)
    rec.close()


def station(name="station"):
    def txt(info):
        return [f"t = {info['t']:5.2f} s   {info['phase']}{'   TAP' if info['tap'] else ''}",
                f"module tilt {info['tilt']:5.1f} deg   actuator force {info['Fact']:5.2f} N   docked: {'yes' if info['docked'] else 'no'}",
                f"station gondola swing {info['swing']:+.3f} deg   front pivot rise {info.get('rise_f', 0.0):+.2f} mm   strip force {info.get('strip_f', 0.0):.1f} N"]
    rec = Recorder(name, ["st_side", "st_iso"], "Station (CAD rig + chain hold-down strips): dock, tilt to 90 deg, auger + solenoid taps",
                   txt, fade_others=True, every=2, shadows=False, samples=2)
    KS = 4 * C.T_CHAIN / (PR.LOOP_B * MM)
    C.run_station({}, dict(damping=1e-4, chain=dict(k_tab=C.K_TAB, k_span=KS, gap=0.5 * MM)), frame_cb=rec)
    rec.close()


def test():
    xml, info = M.build_xml(KN.HOME_SHIFT + 3.0, station=dict(C.STATION_BASE))
    m = mujoco.MjModel.from_xml_string(xml)
    d = mujoco.MjData(m)
    mujoco.mj_forward(m, d)
    r = mujoco.Renderer(m, H, W // 2, max_geom=4000)
    for cam in ("side", "iso", "st_side", "st_iso"):
        r.update_scene(d, camera=cam)
        add_chain(r.scene, KN.HOME_SHIFT + 3.0)
        Image.fromarray(r.render()).save(os.path.join(OUT, f"_test_{cam}.png"))


if __name__ == "__main__":
    what = sys.argv[1:] or ["lap", "station"]
    for w_ in what:
        {"lap": lap, "station": station, "fastlap": fastlap, "test": test}[w_]()
