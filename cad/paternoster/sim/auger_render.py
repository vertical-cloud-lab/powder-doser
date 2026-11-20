"""Render a recorded auger dosing run (out/auger/run_<tag>.npz) to MP4 (1280x720, 30 fps, H.264) + GIF.

Cut-away: the near half of the rotating tube wall and funnel (the half facing the camera) is hidden every
frame, so the flight (blue), core (amber) and grains are visible.  Grains are coloured by where they started
(bands along the auger axis) so conveying is visible.

  MUJOCO_GL=glfw xvfb-run -a -s "-screen 0 1920x1080x24" python auger_render.py t60_tap
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

import numpy as np
import mujoco
import imageio.v2 as imageio
import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import auger_model as AM  # noqa: E402
import auger_geom as G  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "auger")


def font(sz):
    for f in ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]:
        if os.path.exists(f):
            return ImageFont.truetype(f, sz)
    return ImageFont.load_default()


def main(tag, max_frames=None, slow=2):
    meta = json.load(open(os.path.join(OUT, f"run_{tag}.json")))
    dat = np.load(os.path.join(OUT, f"run_{tag}.npz"))
    frames, fq = dat["frames"], dat["fq"]
    n = frames.shape[1]
    xml, _ = AM.build_xml(tilt_deg=meta["tilt_deg"], n_grains=n, rp_mm=meta["rp_mm"], z_cut=meta["z_cut_mm"],
                          grain_positions_world=frames[0])
    m = mujoco.MjModel.from_xml_string(xml)
    d = mujoco.MjData(m)
    g0 = m.nbody - n
    spin_q = m.jnt_qposadr[m.joint("spin").id]
    mount_q = m.jnt_qposadr[m.joint("mount").id]
    bal_q = m.jnt_qposadr[m.joint("balance").id]
    plug = m.geom("plug").id
    m.geom_group[plug] = 5
    m.geom_rgba[plug, 3] = 0
    # grain colours by initial axial position (4 bands)
    O = np.array([0, 0, meta["H"]])
    Rf = AM.frame_R(meta["tilt_deg"])
    z0 = ((Rf.T @ (frames[0] - O).T).T)[:, 2]
    qs = np.quantile(z0, [0.25, 0.5, 0.75])
    pal = np.array([[0.93, 0.36, 0.25, 1], [0.98, 0.78, 0.30, 1], [0.40, 0.75, 0.45, 1], [0.55, 0.45, 0.85, 1]])
    band = np.searchsorted(qs, z0)
    gadr = [m.body_geomadr[g0 + i] for i in range(n)]
    for i in range(n):
        m.geom_rgba[gadr[i]] = pal[band[i]]
    names = [mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_GEOM, i) or "" for i in range(m.ngeom)]
    cut = np.array([i for i, s in enumerate(names) if s.startswith(("wall", "funnel"))])
    W, H = 1280, 720
    r = mujoco.Renderer(m, H, W)
    cam = mujoco.MjvCamera()
    cam.type = mujoco.mjtCamera.mjCAMERA_FREE
    t = np.radians(meta["tilt_deg"])
    a = np.array([np.cos(t), 0, np.sin(t)])
    cam.lookat[:] = O + a * 10.0 + np.array([8.0, 0, -4.0])
    cam.distance = 235.0
    cam.azimuth = 90.0
    cam.elevation = -8.0
    opt = mujoco.MjvOption()
    for gi in range(6):
        opt.geomgroup[gi] = 1
    opt.geomgroup[3] = 0
    opt.geomgroup[5] = 0
    f_big, f_small = font(27), font(21)
    imgs = []
    mg = meta["m_grain_g"] * 1e3
    nfr = len(frames) if max_frames is None else min(max_frames, len(frames))
    t_rot = meta["revs"] / (meta["rpm"] / 60)
    t_rev = meta["reverse_revs"] / (meta["rpm"] / 60) if meta["reverse_revs"] else 0
    for k in range(nfr):
        tt, spin, mq, bq, nvial, nex = fq[k]
        d.qpos[spin_q] = spin
        d.qpos[mount_q] = mq
        d.qpos[bal_q] = bq
        for i in range(n):
            j = m.jnt_qposadr[m.body_jntadr[g0 + i]]
            d.qpos[j:j + 3] = frames[k, i]
            d.qpos[j + 3:j + 7] = (1, 0, 0, 0)
        mujoco.mj_forward(m, d)
        near = d.geom_xpos[cut, 1] < -0.5
        m.geom_group[cut] = np.where(near, 3, 0)
        r.update_scene(d, camera=cam, scene_option=opt)
        img = Image.fromarray(r.render())
        dr = ImageDraw.Draw(img)
        if tt < t_rot:
            phase = f"{meta['rpm']:.0f} rpm forward"
        elif tt < t_rot + t_rev:
            phase = f"{meta['rpm']:.0f} rpm REVERSE"
        else:
            phase = "motor stopped"
        tap = f"taps {meta['tap_hz']:g} Hz, {meta['tap_n']:g} N x {meta['tap_ms']:g} ms" if meta["tap_hz"] > 0 else "no taps"
        dr.rectangle([0, 0, W, 92], fill=(20, 24, 32))
        dr.text((18, 10), f"MuJoCo granular proxy ({1 / slow:g}x speed)   |   tilt {meta['tilt_deg']:.0f} deg   |   {phase}   |   {tap}",
                font=f_small, fill=(235, 235, 235))
        dr.text((18, 46), f"t = {tt:4.2f} s   rev {spin / (2 * np.pi):+5.2f}   out of auger {nex * mg:5.0f} mg ({int(nex)} grains)"
                f"   in vial {nvial * mg:5.0f} mg", font=f_big, fill=(255, 220, 120))
        dr.text((18, H - 34), f"{n} spheres r = {meta['rp_mm']:g} mm (proxy for 20-200 um powder), exit annulus r {meta['tip_r_mm']:.1f}-{meta['exit_r_mm']:.1f} mm, near half cut away",
                font=f_small, fill=(60, 60, 60))
        imgs.append(np.asarray(img))
        if k % 20 == 0:
            print(f"frame {k}/{nfr}", flush=True)
    mp4 = os.path.join(OUT, f"auger_{tag}.mp4")
    w = imageio.get_writer(mp4, fps=30, codec="libx264", quality=8, pixelformat="yuv420p", macro_block_size=8)
    for im in imgs:
        for _ in range(slow):          # slow motion: each 1/30 s sim frame shown `slow` times
            w.append_data(im)
    w.close()
    gif = os.path.join(OUT, f"auger_{tag}.gif")
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run([ff, "-y", "-loglevel", "error", "-i", mp4, "-vf",
                    "fps=12,scale=720:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=128[p];[s1][p]paletteuse=dither=bayer:bayer_scale=4",
                    gif], check=True)
    Image.fromarray(imgs[min(len(imgs) - 1, int(len(imgs) * 0.6))]).save(os.path.join(OUT, f"auger_{tag}_still.png"))
    print(mp4, os.path.getsize(mp4), gif, os.path.getsize(gif))


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else None)
