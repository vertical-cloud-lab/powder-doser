"""Cut-away videos of recorded leakage runs (out/<tag>.npz), one run or two side by side.

    MUJOCO_GL=glfw xvfb-run -a -s "-screen 0 1920x1080x24" python leak_render.py v2_a0_fwd v2_a0_rev --name v2_lap_directions
    MUJOCO_GL=glfw xvfb-run -a -s "-screen 0 1920x1080x24" python leak_render.py r15_a0 r15retrev_a10_R1 --name post_dose

Writes out/<name>.mp4 (H.264, 30 fps) and out/<name>.gif (10 fps, 960 px wide). The near half of
the tube wall and funnel is hidden every frame; grains are coloured by where they started along
the axis. The module's real pose (tilt, roll, nozzle-up pitch) comes from the recording.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

import numpy as np
import mujoco
import imageio.v2 as imageio
import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import leak_sim as LS  # noqa: E402

OUT = LS.OUT


def font(sz):
    for f in ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]:
        if os.path.exists(f):
            return ImageFont.truetype(f, sz)
    return ImageFont.load_default()


def caption(r):
    a = r["alpha_deg"]
    if r["kind"] == "v2lap":
        d = "today's direction (pumps toward the outlet)" if r["direction"] == "fwd" else "reversed direction (retracts)"
        return f"v2 lap, {d}, nozzle up {a:g} deg"
    if r["kind"] == "branch":
        t = {"vib": "vibration ramp to 1.5 g", "pat": "one paternoster index", "taps": "solenoid taps", "still": "still"}[r["transit"]]
        p = {"return": "return", "returnrev": f"return, reverse {r['R_rev']:g} rev", "revdose": f"reverse {r['R_rev']:g} rev at 30 deg, return"}[r["protocol"]]
        return f"after a {r['dose_tilt_world']:g} deg dose: {p}, then {t}; rest nozzle up {a:g} deg"
    return r["tag"]


def render_run(tag, W, H, slow=1):
    r = json.load(open(os.path.join(OUT, f"{tag}.json")))
    z = np.load(os.path.join(OUT, f"{tag}.npz"))
    frames, fq = z["frames"], z["fq"]
    n = frames.shape[1]
    m, _ = LS.build(LS.DOSE_TILT)
    d = mujoco.MjData(m)
    g0 = m.nbody - n
    j = m.joint("frame_free").id
    qa = m.jnt_qposadr[j]
    spin_q = m.jnt_qposadr[m.joint("spin").id]
    bal_q = m.jnt_qposadr[m.joint("balance").id]
    plug = m.geom("plug").id
    m.geom_group[plug] = 5
    m.geom_rgba[plug, 3] = 0
    # colour grains by where they start along the axis (4 bands)
    from scipy.spatial.transform import Rotation as Rot
    q0 = fq[0, 4:8]
    R0 = Rot.from_quat([q0[1], q0[2], q0[3], q0[0]]).as_matrix()
    z0 = ((R0.T @ (frames[0] - LS.O).T).T)[:, 2]
    qs = np.quantile(z0, [0.25, 0.5, 0.75])
    pal = np.array([[0.93, 0.36, 0.25, 1], [0.98, 0.78, 0.30, 1], [0.40, 0.75, 0.45, 1], [0.55, 0.45, 0.85, 1]])
    band = np.searchsorted(qs, z0)
    for i in range(n):
        m.geom_rgba[m.body_geomadr[g0 + i]] = pal[band[i]]
    jadr = np.array([m.jnt_qposadr[m.body_jntadr[g0 + i]] for i in range(n)])
    pidx = (jadr[:, None] + np.arange(3)[None, :]).ravel()
    qidx = (jadr[:, None] + 3 + np.arange(4)[None, :]).ravel()
    names = [mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_GEOM, i) or "" for i in range(m.ngeom)]
    cut = np.array([i for i, s in enumerate(names) if s.startswith(("wall", "funnel"))])
    rend = mujoco.Renderer(m, H, W)
    cam = mujoco.MjvCamera()
    cam.type = mujoco.mjtCamera.mjCAMERA_FREE
    cam.lookat[:] = LS.O + np.array([42.0, 0, -6.0])
    cam.distance = 175.0
    cam.azimuth = 90.0
    cam.elevation = -6.0
    opt = mujoco.MjvOption()
    for gi in range(6):
        opt.geomgroup[gi] = 1
    opt.geomgroup[3] = 0
    opt.geomgroup[5] = 0
    f_big, f_small = font(22), font(17)
    mg = r["m_grain_mg"]
    L = z["log"]                                   # 100 Hz: t, phase, tilt, roll, spin, n_out, n_near_exit, ...
    n_out0 = None
    roll_prev, roll_acc = None, 0.0
    imgs = []
    for k in range(len(frames)):
        tt, ph, spin, bq, qw, qx, qy, qz, nout, nvial = fq[k]
        if n_out0 is None:
            n_out0 = nout
        d.qpos[qa:qa + 3] = LS.O
        d.qpos[qa + 3:qa + 7] = (qw, qx, qy, qz)
        d.qpos[spin_q] = spin
        d.qpos[bal_q] = bq
        d.qpos[pidx] = frames[k].ravel()
        d.qpos[qidx] = np.tile([1.0, 0, 0, 0], n)
        mujoco.mj_forward(m, d)
        near = d.geom_xpos[cut, 1] < -0.5
        m.geom_group[cut] = np.where(near, 3, 0)
        rend.update_scene(d, camera=cam, scene_option=opt)
        img = Image.fromarray(rend.render())
        dr = ImageDraw.Draw(img)
        Rm = Rot.from_quat([qx, qy, qz, qw]).as_matrix()
        ax = Rm[:, 2]
        tilt = np.degrees(np.arctan2(ax[2], np.hypot(ax[0], ax[1])))
        xl = Rm[:, 0]
        roll_w = np.degrees(np.arctan2(xl[1], -xl[2]))
        if roll_prev is not None:
            roll_acc += (roll_w - roll_prev + 180.0) % 360.0 - 180.0     # unwrap across frames
        roll_prev = roll_w
        roll = roll_acc
        dr.rectangle([0, 0, W, 104], fill=(20, 24, 32))
        dr.text((12, 8), caption(r), font=f_small, fill=(235, 235, 235))
        near = float(np.interp(tt, L[:, 0], L[:, 6]))
        what = "pumped out this lap" if r["kind"] == "v2lap" else "out since the stop (falls in the vial)"
        dr.text((12, 36), f"t {tt - fq[0, 0]:4.1f} s  {LS.PHASES[int(ph)]:<20s} tilt {tilt:+5.1f}  roll {roll:+5.0f}",
                font=f_big, fill=(255, 220, 120))
        dr.text((12, 70), f"at the exit {near * mg:5.0f} mg   |   {what} {max(0, nout - n_out0) * mg:4.0f} mg",
                font=f_small, fill=(255, 220, 120))
        imgs.append(np.asarray(img))
    return imgs, r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tags", nargs="+")
    ap.add_argument("--name", required=True)
    ap.add_argument("--start", type=float, default=0.0, help="skip this much of the recording (s)")
    a = ap.parse_args()
    W, H = (960, 540) if len(a.tags) == 2 else (1280, 720)
    runs = [render_run(t, W, H) for t in a.tags]
    nfr = min(len(im) for im, _ in runs)
    k0 = int(a.start * 30)
    frames = [np.hstack([im[k] for im, _ in runs]) for k in range(k0, nfr)]
    mp4 = os.path.join(OUT, f"{a.name}.mp4")
    w = imageio.get_writer(mp4, fps=30, codec="libx264", quality=7, pixelformat="yuv420p", macro_block_size=8)
    for im in frames:
        w.append_data(im)
    w.close()
    gif = os.path.join(OUT, f"{a.name}.gif")
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run([ff, "-y", "-loglevel", "error", "-i", mp4, "-vf",
                    "fps=10,scale=960:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=96[p];[s1][p]paletteuse=dither=bayer:bayer_scale=4",
                    gif], check=True)
    Image.fromarray(frames[int(len(frames) * 0.7)]).save(os.path.join(OUT, f"{a.name}_still.png"))
    print(mp4, os.path.getsize(mp4), gif, os.path.getsize(gif))


if __name__ == "__main__":
    main()
