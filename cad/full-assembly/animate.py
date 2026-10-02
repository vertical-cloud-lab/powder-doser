"""Step-by-step assembly GIF in the style of the OT-2 lid-camera mount's
(byu-vcl PR #234, ``ot2-overhead-camera/lid-mount/cad/animate.py``): one
large view, each part sliding in along its own insertion direction, a
plain-language caption for every step, a step counter, a 2-3 s hold so the
caption can be read, and close-ups for the small fasteners.  It ends on the
assembled doser tilting 0-45-0 deg, with the McMaster-Carr part numbers.

The parts, positions, build order and insertion directions are the ones
``assembly_bom.py`` uses for the BOM GIF (which stays as it is).

    xvfb-run -a python3 animate.py      # -> renders/assembly_walkthrough.gif
"""
from __future__ import annotations

import textwrap

import numpy as np
import vtk
from PIL import Image, ImageDraw, ImageFont

import assembly_bom as ab
import build
import hardware
import layout

SIZE = (960, 720)
FPS = 10
WRAP = 92                      # characters per caption line
TITLE = "Powder doser: assembly"
FONT = "/usr/share/fonts/truetype/crosextra/Carlito-Regular.ttf"

# Camera directions in the June frame (outlet towards +Y, stepper on +X).
FIG1A = (0.64, 0.64, 0.38)     # the Fig. 1a direction
STEPPER_SIDE = (0.95, 0.12, 0.42)
TOP_FRONT = (0.25, 0.55, 0.80)
OUTLET_END = (0.30, 0.92, 0.35)

# One entry per assembly_bom.STEPS entry: caption, the instance-name
# prefixes to frame (None = the whole doser), camera direction, motion
# frames.  Facts are from hardware.py, layout.py and the README.
WALK = [
    ("Start with the printed baseplate: hinge towers and servo posts up.",
     None, FIG1A, 12),
    ("Lower the two MG996R servos between the baseplate's posts, output spline up. Each spline "
     "ends up right under the hinge axis.", None, FIG1A, 18),
    ("Fix each servo with 4 x M3 x 14 socket head screws, in through the post and the servo's "
     "flange, and an M3 nylon-insert locknut on the flange side.",
     ["Servo MG996R (-X)", "Servo screw (-X", "Servo nut (-X"], STEPPER_SIDE, 18),
    ("Push a 14T pinion onto each servo spline and fix it with an M3 x 10 socket head screw into "
     "the servo shaft.", ["Servo MG996R (-X)", "Servo pinion (-X)", "Servo pinion screw (-X)"],
     STEPPER_SIDE, 18),
    ("Set the mounting plate on the hinge: its knuckles go just inside the baseplate's towers, "
     "and its two 28T gears just outside them, on the servo pinions.", None, FIG1A, 20),
    ("From inside each knuckle, push an M5 x 45 button head screw out through the knuckle, tower "
     "and gear. An M5 nylon-insert locknut goes on outside the gear; the plate pivots on the "
     "two shanks.", ["Hinge screw (-X)", "Hinge locknut (-X)", "Servo pinion (-X)"],
     STEPPER_SIDE, 20),
    ("Bolt the NEMA 11 stepper to the back of the plate's motor face with 4 x M2.5 x 8 socket "
     "head screws, in from the front.", ["Stepper (NEMA 11)", "Stepper screw"], STEPPER_SIDE, 18),
    ("Push the 20T pinion onto the stepper's D-shaft (there's no set screw).",
     ["Stepper (NEMA 11)", "Stepper pinion"], STEPPER_SIDE, 14),
    ("Tap-collar base on the plate: an M3 x 25 button head up from under the floor with a "
     "locknut on top, and an M3 x 30 flat head down into the countersunk hole, with a plain M3 "
     "nut under the floor (only 2 mm there, too thin for a locknut).",
     ["Tap collar base (AI)", "Tap base"], TOP_FRONT, 20),
    ("Slide the two brackets and the tap collar onto the auger tube, then lower it onto the plate "
     "so its 44T gear meshes with the stepper pinion.", None, FIG1A, 20),
    ("Brackets: 2 x M3 x 20 button heads each, up from under the floor with locknuts on top, and "
     "an M3 x 14 with a locknut across each split clamp. Tap collar: an M3 x 20 button head down "
     "through its ears, locknut underneath, collar rolled 30 deg away from the stepper.",
     ["Bracket", "Tap collar", "Tap collar clamp"], FIG1A, 20),
    ("Fix the Adafruit 412 solenoid to the tap collar's plate with 2 x M3 x 5 socket head screws "
     "into its frame.", ["Tap collar", "Solenoid"], OUTLET_END, 18),
    ("Screw the cap onto the back end of the auger tube.", None, FIG1A, 16),
]
assert len(WALK) == len(ab.STEPS)


def _font(size):
    try:
        return ImageFont.truetype(FONT, size)
    except OSError:
        return ImageFont.load_default()


def ease(u: float) -> float:
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


def overlay(img: Image.Image, label: str, caption: str) -> Image.Image:
    """Title top left, step counter top right, caption along the bottom."""
    img = img.convert("RGBA")
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    f = _font(20)
    d.text((14, 10), TITLE, font=f, fill=(0, 0, 0, 255))
    if label:
        w = d.textlength(label, font=f)
        d.text((SIZE[0] - 14 - w, 10), label, font=f, fill=(90, 90, 90, 255))
    lines = textwrap.wrap(" ".join(caption.split()), WRAP)
    if lines:
        lh = 25
        y0 = SIZE[1] - 12 - lh * len(lines)
        d.rectangle((8, y0 - 6, SIZE[0] - 8, SIZE[1] - 6), fill=(255, 255, 255, 220))
        for i, line in enumerate(lines):
            d.text((14, y0 + i * lh), line, font=f, fill=(0, 0, 0, 255))
    img.alpha_composite(layer)
    return img.convert("RGB")


def fit_camera(view, pts_world: np.ndarray, dirv, margin: float = 0.8):
    """Camera looking along -dirv (June frame) that fits pts_world; the
    caption band at the bottom is kept clear.  Returns (position, focal,
    view angle): Zoom() narrows the view angle, so it is part of the state."""
    cam = view.ren.GetActiveCamera()
    cam.SetViewUp(0, 0, 1)
    dirv = np.asarray(dirv, float)
    dirv /= np.linalg.norm(dirv)
    cj = (build.W2J @ np.c_[pts_world, np.ones(len(pts_world))].T).T[:, :3]
    ctr = (cj.min(0) + cj.max(0)) / 2
    cam.SetFocalPoint(*ctr)
    cam.SetPosition(*(ctr + dirv * 1500))
    cam.SetViewAngle(18.0)
    view.ren.ResetCameraClippingRange()
    W, H = SIZE
    usable = (60, H - 110)             # below the title, above the caption
    for _ in range(4):
        px = np.array([view.project(p) for p in cj])
        (x0, y0), (x1, y1) = px.min(0), px.max(0)
        f = margin * min(W / (x1 - x0), (usable[1] - usable[0]) / (y1 - y0))
        target = np.array([W / 2, (usable[0] + usable[1]) / 2])
        mid = np.array([(x0 + x1) / 2, (y0 + y1) / 2])
        # move the focal point so the box centre lands on the target pixel
        c = vtk.vtkCoordinate()
        c.SetCoordinateSystemToDisplay()
        fp = np.array(cam.GetFocalPoint())
        pos = np.array(cam.GetPosition())
        dop = np.array(cam.GetDirectionOfProjection())

        def ray(px_xy):
            c.SetValue(px_xy[0], H - px_xy[1], 0)
            r = np.array(c.GetComputedWorldValue(view.ren)) - pos
            return r / np.linalg.norm(r)

        t = np.dot(fp - pos, dop)
        p_mid = pos + ray(mid) * t / np.dot(ray(mid), dop)
        p_tgt = pos + ray(target) * t / np.dot(ray(target), dop)
        shift = p_mid - p_tgt
        cam.SetFocalPoint(*(fp + shift))
        cam.SetPosition(*(pos + shift))
        cam.Zoom(f)
        view.ren.ResetCameraClippingRange()
    return np.array(cam.GetPosition()), np.array(cam.GetFocalPoint()), np.array(cam.GetViewAngle())


def main() -> None:
    order, inst = ab.scene()
    view = ab.View(order, inst, SIZE)
    cam = view.ren.GetActiveCamera()
    nsteps = len(ab.STEPS)

    def set_cam(st):
        cam.SetPosition(*st[0])
        cam.SetFocalPoint(*st[1])
        cam.SetViewAngle(float(st[2]))
        cam.SetViewUp(0, 0, 1)
        view.ren.ResetCameraClippingRange()

    def pts(names_prefixes, s_of):
        sel = order if names_prefixes is None else [
            d for d in order if any(d["name"].startswith(p) for p in names_prefixes)]
        return ab._points(sel, inst, s_of, every=7)

    def s_upto(k, e):
        return lambda kk: 1.0 if kk < k else (e if kk == k else 0.0)

    # cameras: the assembled doser, and one per step
    one = lambda kk: 1.0       # noqa: E731
    overall = fit_camera(view, pts(None, one), FIG1A, margin=0.86)
    cams = []
    for k, (_, focus, dirv, _) in enumerate(WALK):
        if focus is None:
            cams.append(overall)
        else:
            p = np.vstack([pts(focus, s_upto(k, 0.0)), pts(focus, s_upto(k, 1.0))])
            cams.append(fit_camera(view, p, dirv, margin=0.78))

    frames, durations = [], []

    def add(img, ms):
        frames.append(img)
        durations.append(ms)

    # intro: the baseplate alone, then step by step
    cur = overall
    for k, (caption, focus, dirv, n) in enumerate(WALK):
        label = f"{k + 1} / {nsteps}"
        start = cur
        n = max(8, round(0.75 * n))
        for i in range(1, n + 1):
            e = ease(i / n)
            # the camera settles in the first half, so the rest of the motion
            # only redraws the moving parts (smaller GIF)
            set_cam([a + (b - a) * ease(min(1.0, 2.0 * i / n)) for a, b in zip(start, cams[k])])
            view.pose(s_upto(k, e), visible_from=k)
            add(overlay(view.image(), label, caption), 1000 // FPS)
        hold = int(np.clip(len(caption) / 9.0, 20, 32))
        add(overlay(view.image(), label, caption), hold * 1000 // FPS)
        cur = cams[k]

    # back out to the whole doser, then tilt 0 -> 45 -> 0 about the hinge
    view.pose(one)
    cap = "Assembled: 11 printed parts, 4 purchased parts and 46 fasteners."
    for i in range(1, 9):
        set_cam([a + (b - a) * ease(i / 8) for a, b in zip(cur, overall)])
        add(overlay(view.image(), "", cap), 1000 // FPS)
    add(overlay(view.image(), "", cap), 1500)

    def tilt_Ms(t):
        P = layout.placements(float(t))
        Fp = {nm: M for nm, _, _, M in hardware.fastener_placements(float(t))}
        return {d["name"]: (P[d["name"]][1] if d["name"] in P else Fp[d["name"]]) for d in order}

    cap = "The two servos tilt the mounting plate about the hinge, up to 45 deg."
    for t in list(np.linspace(0, 45, 10)) + list(np.linspace(45, 0, 10)):
        view.pose(one, tilt_M=tilt_Ms(t))
        add(overlay(view.image(), f"tilt {t:.0f} deg", cap), 1000 // FPS)
    durations[-11] = 900                 # pause at 45 deg
    pns = ", ".join(dict.fromkeys(hardware.MCMASTER.values()))
    add(overlay(view.image(), "", f"Assembled. Fasteners (McMaster-Carr): {pns}."), 4000)

    # one shared palette keeps the colours steady from frame to frame
    picks = [frames[i] for i in np.linspace(0, len(frames) - 1, 12).astype(int)]
    mosaic = Image.new("RGB", (SIZE[0], SIZE[1] * len(picks)))
    for i, f in enumerate(picks):
        mosaic.paste(f, (0, i * SIZE[1]))
    pal = mosaic.quantize(colors=96, method=Image.Quantize.MEDIANCUT)
    q = [f.quantize(palette=pal, dither=Image.Dither.NONE) for f in frames]
    out = ab.RENDERS / "assembly_walkthrough.gif"
    q[0].save(out, save_all=True, append_images=q[1:], duration=durations, loop=0,
              optimize=False, disposal=1)
    print(f"  -> {out.relative_to(ab.HERE)}  ({len(frames)} frames, {sum(durations) / 1000:.0f} s, "
          f"{out.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
