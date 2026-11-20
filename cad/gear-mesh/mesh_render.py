"""Render recorded mesh runs (mesh_mujoco.py run ... --record) to MP4 + GIF.

    MUJOCO_GL=glfw xvfb-run -a -s "-screen 0 1920x1080x24" python mesh_render.py compare
Two runs side by side at the same tilt and speed, slowed down, with a close-up camera on the
mesh: Sam's carriage as drawn (gravity holds the plate) against the proposed station
(magnet, steel pinion, rod-end pin at the carriage's centre of mass, locating pins).
"""
from __future__ import annotations

import json
import math
import sys

import mujoco
import numpy as np
from PIL import Image, ImageDraw, ImageFont

import mesh_mujoco as M

W, H = 640, 480


def font(sz):
    try:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", sz)
    except OSError:
        return ImageFont.load_default()


def frames_for(config, tilt, rpm, t_run, load, ecc, perr, tag):
    r, S = M.run(tilt=tilt, rpm=rpm, config=config, t_run=t_run, load=load, ecc=ecc, pitch_err=perr, record=True, tag=tag)
    z = np.load(M.OUT / f"{tag}.npz")
    return r, S, z["frames"], z["log"]


def tilt_camera(S, cam="side", centre=(0.105, 0.0, -0.11), dist=0.62):
    """Point a camera along +y and roll it with the station tilt, so the world's vertical is vertical in the image
    (the model keeps Sam's frame fixed and turns gravity instead)."""
    m = S.m
    th = math.radians(S.info["tilt"])
    right = np.array([math.cos(th), 0.0, -math.sin(th)])
    up = np.array([math.sin(th), 0.0, math.cos(th)])
    zc = np.cross(right, up)
    q = np.zeros(4)
    mujoco.mju_mat2Quat(q, np.column_stack([right, up, zc]).flatten())
    i = m.camera(cam).id
    m.cam_quat[i] = q
    m.cam_pos[i] = np.array(centre) + zc * dist
    m.cam_fovy[i] = 38.0
    m.cam_mode[i] = 0


def render_frames(S, frames, cam, label, sub, every=1):
    m, d = S.m, S.d
    if cam == "side":
        tilt_camera(S)
    rnd = mujoco.Renderer(m, H, W)
    opt = mujoco.MjvOption()
    out = []
    f1, f2 = font(18), font(14)
    for k, q in enumerate(frames[::every]):
        d.qpos[:] = q
        mujoco.mj_forward(m, d)
        rnd.update_scene(d, camera=cam, scene_option=opt)
        img = Image.fromarray(rnd.render())
        dr = ImageDraw.Draw(img)
        dr.rectangle([0, 0, W, 54], fill=(252, 252, 251))
        dr.text((10, 6), label, fill=(11, 11, 11), font=f1)
        dr.text((10, 31), sub(k * every), fill=(82, 81, 78), font=f2)
        out.append(np.asarray(img))
    rnd.close()
    return out


def compare(tilt=30.0, rpm=60.0, t_run=1.0, slow=4.0):
    import imageio.v2 as imageio
    runs = []
    for cfg, label in (("as drawn", "Sam's carriage as drawn: weight holds the plate"),
                       ("final", "As built: magnet, steel pinion, pivot at the carriage's COM")):
        tag = f"video_{cfg.replace(' ', '_')}_t{tilt:g}_r{rpm:g}"
        r, S, fr, log = frames_for(cfg, tilt, rpm, t_run, 0.03, 0.05, 0.0006, tag)
        runs.append((cfg, label, r, S, fr, log))
    n = min(len(x[4]) for x in runs)
    fps_rec = 240.0
    every = 1
    tiles = []
    for cfg, label, r, S, fr, log in runs:
        t = log[:, 0]

        def sub(k, log=log, t=t, r=r):
            tk = t[0] + k / fps_rec
            i = min(np.searchsorted(t, tk), len(t) - 1)
            cd = log[i, 5]
            return (f"{tilt:g} deg, auger {rpm:g} rpm, 0.05 mm runout | t {tk - t[0]:.2f} s | "
                    + (f"centre distance {cd:.2f} mm" if cd < 40 else "carriage off the plate") + f" | jumps {int(abs(round(log[i, 3])))}")
        tiles.append(render_frames(S, fr[:n], "side", label, sub, every))
    frames = [np.concatenate([a, b], axis=1) for a, b in zip(*tiles)]
    out_mp4 = M.OUT / f"compare_t{tilt:g}_r{rpm:g}.mp4"
    fps = fps_rec / slow
    imageio.mimwrite(out_mp4, frames, fps=fps, codec="libx264", quality=7, macro_block_size=16)
    small = [np.asarray(Image.fromarray(f).resize((W, H // 2))) for f in frames[::2]]
    imageio.mimwrite(M.OUT / f"compare_t{tilt:g}_r{rpm:g}.gif", small, duration=1000 * 2 / fps, loop=0)
    Image.fromarray(frames[len(frames) // 2]).save(M.OUT / f"compare_t{tilt:g}_r{rpm:g}_still.png")
    print(out_mp4, len(frames))


if __name__ == "__main__":
    compare(float(sys.argv[2]) if len(sys.argv) > 2 else 30.0, float(sys.argv[3]) if len(sys.argv) > 3 else 60.0)
