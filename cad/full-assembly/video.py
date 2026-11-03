"""Presentation version of the assembly walkthrough (``animate.py``): a
1280x720, 30 fps H.264 MP4.  The only text is one short line for each of
the three electronics as it is shown working (CAPTIONS); there is no
title, step counter, step caption, label or part number.

The assembly runs 2.4 times as fast as in the GIF (28 s, not 67.5 s).
The caption holds are gone, the parts take 1 s and the screws and nuts
0.5 s, and in a step with both, the fasteners go in after the part they
fix. The camera flies between views instead of cutting. The doser working at the end (the
tilt, one tilt gear pair, the stepper drive, the solenoid tap) runs at the
GIF's speed, sampled at 30 fps instead of 10, with a 1 s longer still
before each captioned motion.

Same parts, build order, insertion directions and cameras as the GIF;
each frame is rendered at twice the size and scaled down (anti-aliasing).

    xvfb-run -a python3 video.py      # -> renders/assembly_presentation_720p.mp4
                                      #    renders/assembly_presentation_720p_frames.png (contact sheet)
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import get_context

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import animate as an
import assembly_bom as ab
import layout

SIZE = (1280, 720)
FPS = 30
OUT = ab.RENDERS / "assembly_presentation_720p.mp4"
SHEET = ab.RENDERS / "assembly_presentation_720p_frames.png"

# The assembly, sped up (seconds)
INTRO_S = 0.6         # the board, the baseplate over it
CAM_S = 0.75          # camera move from one step's view to the next
PART_S = 1.0          # a part sliding into place
FAST_S = 0.5          # screws and nuts
FAST_AFTER = 0.7      # with a part in the same step, its fasteners start this far into its move
HOLD_S = 0.35         # pause after a step
HOLD_FAST_S = 0.2     # pause after a fasteners-only step

# The doser working, at the GIF's speed (animate.py).  Its cuts to the
# close-ups become FLY_S camera flights, taken out of the still before each
# motion.  The GIF's two stills of the assembled doser before the tilt
# (1.5 s each, for two captions) are one ASSEMBLED_S still here, and its
# 4 s end (the part numbers) is END_S.
ASSEMBLED_S = 1.5
FLY_S = 0.7
TILT = [(0.0, 0.0), (0.9, 45.0), (1.8, 45.0), (2.7, 0.0), (2.8, 0.0)]          # (s, deg)
TILT_CLOSE = [(0.0, 0.0), (0.9, 45.0), (1.1, 45.0), (2.0, 0.0), (2.1, 0.0)]
GEAR_STILL_S, DRIVE_STILL_S, TAP_STILL_S = 1.5, 1.5, 1.2

# The only text in the video: one short line for each of the three
# electronics as it is shown working.  Each caption starts when the camera
# arrives at that feature's view and stays for TEXT_S (fading in and out
# over TEXT_FADE_S), and the still before the motion is PAUSE_S longer than
# it would otherwise be, so the line can be read before anything moves.
CAPTIONS = {"servos": "Servos for precise tilting",
            "stepper": "Stepper motor for rotation",
            "solenoid": "Solenoid for tapping"}
TEXT_S = 4.0
TEXT_FADE_S = 0.3
PAUSE_S = 1.0
TEXT_FONT = "/usr/share/fonts/truetype/crosextra/Carlito-Regular.ttf"
TEXT_PX = 44                   # font size at 1280x720
TEXT_MARGIN = (40, 34)         # from the left and bottom edges
AUGER_RATE = 6.0 / layout.STEPPER_RATIO / 0.07    # deg/s: the pinion 6 deg every 70 ms
AUGER_S = 2.8
TAP = [(0.04, 0.5), (0.12, 1.0), (0.06, 0.6), (0.06, 0.25), (0.40, 0.0)]       # (s, share of the stroke)
N_TAPS = 4
END_S = 2.0


def same(a, b) -> bool:
    return all(np.allclose(x, y) for x, y in zip(a, b))


def cam_lerp(a, b, u: float):
    """Camera u of the way from a to b: the view direction turns on a great
    circle about the moving focal point, and the zoom (tan of half the view
    angle) changes at a steady rate."""
    (pa, fa, va), (pb, fb, vb) = a, b
    da, db = pa - fa, pb - fb
    ra, rb = np.linalg.norm(da), np.linalg.norm(db)
    ua, ub = da / ra, db / rb
    om = np.arccos(np.clip(ua @ ub, -1.0, 1.0))
    d = ua if om < 1e-6 else (np.sin((1 - u) * om) * ua + np.sin(u * om) * ub) / np.sin(om)
    f = fa + (fb - fa) * u
    ta, tb = np.tan(np.radians(va) / 2), np.tan(np.radians(vb) / 2)
    return f + d * (ra + (rb - ra) * u), f, np.degrees(2 * np.arctan(ta * (tb / ta) ** u))


class Timeline:
    """One spec per output frame: the camera and what to pose.  kind
    "build": step k, its parts ep and its fasteners ef of the way in; kind
    "pose": the assembled doser at a tilt and auger angle, with the
    solenoid's plunger tap of its stroke down (None: the one-piece model)."""

    def __init__(self):
        self.frames = []
        self.text = []        # per frame: (caption, alpha 0..1) or None, composited after rendering
        self.captions = []    # (text, first frame, frames, fade frames), see caption()

    def add(self, cam, kind, **kw):
        cam = [np.round(np.ravel(np.asarray(c, float)), 6).tolist() for c in cam]
        self.frames.append(dict(cam=cam, kind=kind, **kw))
        self.text.append(None)

    def hold(self, seconds):
        n = round(seconds * FPS)
        self.frames += [self.frames[-1]] * n
        self.text += [None] * n

    def caption(self, key: str, seconds: float = TEXT_S, fade: float = TEXT_FADE_S) -> None:
        """Show CAPTIONS[key] over the next `seconds` of frames (added later;
        resolve_text() fills the entries in once the timeline is complete)."""
        self.captions.append((CAPTIONS[key], len(self.frames), round(seconds * FPS), round(fade * FPS)))

    def resolve_text(self) -> None:
        for text, start, n, nf in self.captions:
            for i in range(n):
                j = start + i
                if j >= len(self.frames):
                    break
                self.text[j] = (text, min(1.0, (i + 1) / nf, (n - i) / nf))

    def fly(self, a, b, seconds, **pose):
        for i in range(1, round(seconds * FPS) + 1):
            self.add(cam_lerp(a, b, an.ease(i / (seconds * FPS))), "pose", **pose)


def assembly(tl, order, overall, cams):
    """The 19 steps: camera move, then the parts, then their fasteners."""
    cur = overall
    tl.add(cur, "build", k=0, ep=0.0, ef=0.0)
    tl.hold(INTRO_S)
    for k in range(len(ab.STEPS)):
        movers = [d for d in order if k in d["steps"]]
        part = any(not d["metal"] for d in movers)
        fast = any(d["metal"] for d in movers)
        tc = 0.0 if same(cur, cams[k]) else CAM_S
        p0 = 0.4 * tc                                   # parts start as the camera settles
        f0 = p0 + FAST_AFTER * PART_S if part else 0.5 * tc
        end = max(tc, p0 + PART_S if part else 0.0, f0 + FAST_S if fast else 0.0)
        for i in range(1, round(end * FPS) + 1):
            t = i / FPS
            cam = cam_lerp(cur, cams[k], an.ease(t / tc)) if tc else cams[k]
            tl.add(cam, "build", k=k, ep=an.ease((t - p0) / PART_S) if part else 1.0,
                   ef=an.ease((t - f0) / FAST_S) if fast else 1.0)
        tl.hold(HOLD_S if part else HOLD_FAST_S)
        cur = cams[k]
    return cur


def doser_working(tl, cur, overall, cam_tilt, cam_gear, cam_drive, cam_tap):
    """Tilt, a tilt gear pair close up, the stepper drive, the solenoid tap.
    cam_tilt is the whole doser with room for the 45 deg tilt (in 16:9 the
    tilted tube leaves the overall view at the top)."""
    tl.fly(cur, cam_tilt, CAM_S, tilt=0.0, auger=0.0, tap=None)
    tl.caption("servos")
    tl.hold(ASSEMBLED_S - CAM_S + PAUSE_S)

    def tilt_track(cam, knots):
        ts, vs = zip(*knots)
        for i in range(1, round(ts[-1] * FPS) + 1):
            tl.add(cam, "pose", tilt=float(np.interp(i / FPS, ts, vs)), auger=0.0, tap=None)

    tilt_track(cam_tilt, TILT)
    tl.fly(cam_tilt, cam_gear, FLY_S, tilt=0.0, auger=0.0, tap=None)
    tl.hold(GEAR_STILL_S - FLY_S)
    tilt_track(cam_gear, TILT_CLOSE)
    tl.fly(cam_gear, cam_drive, FLY_S, tilt=0.0, auger=0.0, tap=None)
    tl.caption("stepper")
    tl.hold(DRIVE_STILL_S - FLY_S + PAUSE_S)
    n = round(AUGER_S * FPS)
    for i in range(1, n + 1):
        tl.add(cam_drive, "pose", tilt=0.0, auger=-AUGER_RATE * i / FPS, tap=None)
    # the auger stays where the drive left it (no jump back to 0 in view);
    # the solenoid is the three-piece model from here on
    a_end = -AUGER_RATE * n / FPS
    tl.fly(cam_drive, cam_tap, FLY_S, tilt=0.0, auger=a_end, tap=0.0)
    tl.caption("solenoid")
    tl.hold(TAP_STILL_S - FLY_S + PAUSE_S)
    period = sum(s for s, _ in TAP)
    for i in range(round(N_TAPS * period * FPS)):
        t, s_tap = (i / FPS) % period, 0.0
        for dur, s in TAP:
            if t < dur:
                s_tap = s
                break
            t -= dur
        tl.add(cam_tap, "pose", tilt=0.0, auger=a_end, tap=s_tap)
    tl.fly(cam_tap, overall, CAM_S, tilt=0.0, auger=a_end, tap=0.0)
    tl.hold(END_S)


# --------------------------------------------------------------------------- #
# Rendering, in worker processes (each with its own scene and window)
# --------------------------------------------------------------------------- #
_W = {}


def _init_worker(scale: int) -> None:
    order, inst = ab.scene()
    view = ab.View(order, inst, (SIZE[0] * scale, SIZE[1] * scale))
    _W.update(view=view, sol=an.solenoid_actors(view),
              M_sol=ab.poses()["Solenoid (Adafruit 412)"])


def _render(job) -> None:
    path, spec = job
    view, sol = _W["view"], _W["sol"]
    if spec["kind"] == "build":
        k = spec["k"]
        view.pose(an.s_upto(k, spec["ep"]), visible_from=k, fast_of_step=an.s_upto(k, spec["ef"]))
        tap = None
    else:
        view.pose(lambda kk: 1.0, tilt_M=ab.poses(spec["tilt"], spec["auger"]))
        tap = spec["tap"]
    for a in sol.values():
        a.SetVisibility(tap is not None)
    if tap is not None:
        view.actors["Solenoid (Adafruit 412)"].SetVisibility(False)
        an.tap_pose(sol, _W["M_sol"], tap * an.STROKE)
    cam = view.ren.GetActiveCamera()
    pos, fp, angle = spec["cam"]
    cam.SetPosition(*pos)
    cam.SetFocalPoint(*fp)
    cam.SetViewAngle(float(angle[0]))
    cam.SetViewUp(0, 0, 1)
    view.ren.ResetCameraClippingRange()
    view.image().resize(SIZE, Image.LANCZOS).save(path, compress_level=1)


def with_text(img: Image.Image, text: str, alpha: float) -> Image.Image:
    """The caption, bottom left, dark on the white background, faded by alpha."""
    img = img.convert("RGBA")
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    try:
        font = ImageFont.truetype(TEXT_FONT, TEXT_PX)
    except OSError:
        font = ImageFont.load_default(TEXT_PX)
    d = ImageDraw.Draw(layer)
    x, y = TEXT_MARGIN[0], SIZE[1] - TEXT_MARGIN[1]
    a = int(round(255 * max(0.0, min(1.0, alpha))))
    # a soft white plate under the text, in case a part is behind it
    bbox = d.textbbox((x, y), text, font=font, anchor="ls")
    d.rounded_rectangle((bbox[0] - 16, bbox[1] - 12, bbox[2] + 16, bbox[3] + 12), radius=10,
                        fill=(255, 255, 255, int(0.85 * a)))
    d.text((x, y), text, font=font, fill=(25, 25, 25, a), anchor="ls")
    img.alpha_composite(layer)
    return img.convert("RGB")


def contact_sheet(frames, out, cols=4, rows=3) -> None:
    w, h = SIZE[0] // cols, SIZE[1] // cols
    sheet = Image.new("RGB", (w * cols + 4 * (cols - 1), h * rows + 4 * (rows - 1)), (200, 200, 200))
    for i, im in enumerate(frames[:cols * rows]):
        sheet.paste(im.resize((w, h), Image.LANCZOS), ((i % cols) * (w + 4), (i // cols) * (h + 4)))
    sheet.save(out)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--jobs", type=int, default=2, help="render processes")
    ap.add_argument("--scale", type=int, default=2, help="render at this many times the size, then scale down")
    ap.add_argument("--seconds", type=float, help="only the first N seconds (a test)")
    ap.add_argument("--start", type=float, default=0.0, help="skip the first N seconds (a test)")
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args()

    order, inst = ab.scene()
    view = ab.View(order, inst, SIZE)
    overall, cams = an.step_cameras(view, order, inst, band=(0, 0))
    cam_gear, cam_drive, cam_tap = an.motion_cameras(view, order, inst, band=(0, 0))
    one = lambda kk: 1.0       # noqa: E731
    cam_tilt = an.fit_camera(view, np.vstack([an.pts(order, inst, None, one), ab._points(
        order, inst, one, tilt_M=ab.poses(45.0), every=7)]), an.FIG1A, margin=0.86, band=(0, 0))
    tl = Timeline()
    cur = assembly(tl, order, overall, cams)
    t_assembly = len(tl.frames) / FPS
    doser_working(tl, cur, overall, cam_tilt, cam_gear, cam_drive, cam_tap)
    tl.resolve_text()
    frames, texts = tl.frames, tl.text
    if args.seconds:
        frames, texts = frames[:round(args.seconds * FPS)], texts[:round(args.seconds * FPS)]
    if args.start:
        frames, texts = frames[round(args.start * FPS):], texts[round(args.start * FPS):]
    keys = [json.dumps(f, sort_keys=True) for f in frames]
    uniq = list(dict.fromkeys(keys))
    shown = [(i / FPS, t[0]) for i, t in enumerate(texts) if t and (i == 0 or texts[i - 1] is None)]
    print(f"  {len(frames)} frames, {len(frames) / FPS:.1f} s (assembly {t_assembly:.1f} s), "
          f"{len(uniq)} to render; captions at " + ", ".join(f"{s:.1f} s '{t}'" for s, t in shown),
          flush=True)

    with tempfile.TemporaryDirectory() as tmp:
        paths = [f"{tmp}/{i:05d}.png" for i in range(len(uniq))]
        with ProcessPoolExecutor(args.jobs, mp_context=get_context("spawn"),
                                 initializer=_init_worker, initargs=(args.scale,)) as ex:
            for n, _ in enumerate(ex.map(_render, zip(paths, map(json.loads, uniq)), chunksize=4), 1):
                if n % 100 == 0 or n == len(uniq):
                    print(f"  rendered {n}/{len(uniq)}", flush=True)
        idx = {k: i for i, k in enumerate(uniq)}
        ff = subprocess.Popen(
            [shutil.which("ffmpeg"), "-y", "-loglevel", "error",
             "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{SIZE[0]}x{SIZE[1]}", "-r", str(FPS), "-i", "-",
             "-vf", "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p",
             "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-profile:v", "high", "-g", str(2 * FPS),
             "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
             "-movflags", "+faststart", args.out], stdin=subprocess.PIPE)
        def frame(i: int) -> Image.Image:
            im = Image.open(paths[idx[keys[i]]]).convert("RGB")
            return with_text(im, *texts[i]) if texts[i] else im

        last, raw = None, b""
        for i, k in enumerate(keys):
            if (idx[k], texts[i]) != last:
                last = (idx[k], texts[i])
                raw = frame(i).tobytes()
            ff.stdin.write(raw)
        ff.stdin.close()
        assert ff.wait() == 0
        # contact sheet: 12 moments, evenly spread
        contact_sheet([frame(i) for i in np.linspace(0, len(keys) - 1, 12).astype(int)], SHEET)
    print(f"  -> {args.out}  ({len(frames) / FPS:.1f} s, {SIZE[0]}x{SIZE[1]}, {FPS} fps)")


if __name__ == "__main__":
    main()
