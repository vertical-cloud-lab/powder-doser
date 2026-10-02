"""Step-by-step assembly GIF in the style of the OT-2 lid-camera mount's
(byu-vcl PR #234, ``ot2-overhead-camera/lid-mount/cad/animate.py``): one
large view, each part sliding in along its own insertion direction, a
plain-language caption for every step, a step counter, a 2-3 s hold so the
caption can be read, and close-ups for the small fasteners.  It starts
from the board the doser is screwed to and ends with the doser working:
the servos tilting the plate 0-45-0 deg (both gears of each pair
turning), the stepper turning the auger through its 20T/44T gears, and
the solenoid tapping the tube, then the McMaster-Carr part numbers.

The parts, positions, build order and insertion directions are the ones
``assembly_bom.py`` uses for the BOM GIF; the gear ratios are in
``onshape/layout.py``.

    xvfb-run -a python3 animate.py      # -> renders/assembly_walkthrough.gif
                                        #    renders/doser_motion.gif (the working part only)
"""
from __future__ import annotations

import shutil
import subprocess
import textwrap

import cadquery as cq
import numpy as np
import vtk
from PIL import Image, ImageDraw, ImageFont

import assembly_bom as ab
import build
import hardware
import layout
import purchased_parts as pp

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
DRIVE = (0.62, 0.62, 0.48)     # stepper pinion and 44T gear, over the front bracket

TUBE_R = 12.5                  # auger tube radius under the tap collar (auger.step)

# One entry per assembly_bom.STEPS entry: caption, the instance-name
# prefixes to frame (None = the whole doser), camera direction, motion
# frames.  Facts are from hardware.py, layout.py and the README.
WALK = [
    ("Start with a flat board or bench top, 38 mm (1.5 in) thick. Set the printed baseplate on it, "
     "hinge towers and servo posts up: its rear sits flat on the board and its two legs hang over "
     "the front edge.", None, FIG1A, 14),
    ("Screw the baseplate down with 6 x #10 x 1-1/4 in pan head wood screws: 4 down through its "
     "corner holes, and 2 through the legs into the board's front edge.",
     ["Baseplate", "Board screw"], FIG1A, 18),
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


def box(lo, hi) -> np.ndarray:
    """The 8 corners of a world-space box (a region for fit_camera)."""
    return np.array([[x, y, z] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])],
                    float)


def tagged(view, img: Image.Image, tags) -> Image.Image:
    """Small labels with leaders: (text, world point, label offset in px)."""
    d = ImageDraw.Draw(img)
    f = _font(17)
    for text, p, (dx, dy) in tags:
        x, y = view.project((build.W2J @ np.append(p, 1.0))[:3])
        w = d.textlength(text, font=f)
        lx, ly = x + dx, y + dy
        bx = lx - w if dx < 0 else lx
        d.line([(x, y), (lx, ly)], fill=(70, 70, 70), width=2)
        d.ellipse((x - 3, y - 3, x + 3, y + 3), fill=(50, 50, 50))
        d.rectangle((bx - 5, ly - 12, bx + w + 5, ly + 12), fill=(255, 255, 255), outline=(120, 120, 120))
        d.text((bx, ly), text, font=f, fill=(0, 0, 0), anchor="lm")
    return img


def solenoid_actors(view) -> dict:
    """The solenoid's frame, plunger and spring as separate actors (hidden),
    so the tap can move the plunger and squash the spring."""
    out = {}
    for k, wp in pp.adafruit412_pieces().items():
        pd = build._polydata(cq.Compound.makeCompound(wp.solids().vals()))
        a = build._actor(pd, build.COL_SOLENOID, np.eye(4))
        a.SetVisibility(False)
        view.ren.AddActor(a)
        out[k] = a
    return out


def tap_pose(actors: dict, M_sol: np.ndarray, s: float) -> None:
    """Plunger s mm down its axis (towards the tube); the spring between the
    frame top and the plunger's cap squashes to fit."""
    h = pp.SOL_BODY_L
    z_cap = h / 2 + (pp.SOL_LEN_TOTAL - h - pp.SOL_BOTTOM_STICKOUT) - 1.0    # cap underside
    f = (z_cap - s - h / 2) / (z_cap - h / 2)
    S = ab._T((0, 0, h / 2)) @ np.diag([1.0, 1.0, f, 1.0]) @ ab._T((0, 0, -h / 2))
    M = build.W2J @ M_sol
    actors["frame"].SetUserTransform(build._vtk_matrix(M))
    actors["plunger"].SetUserTransform(build._vtk_matrix(M @ ab._T((0, 0, -s))))
    actors["spring"].SetUserTransform(build._vtk_matrix(M @ S))


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

    # ---- the doser working ------------------------------------------------
    rows = ab.bom(order)
    n_of = lambda kind: sum(r["qty"] for r in rows if r["kind"] == kind)      # noqa: E731
    view.pose(one)
    cap = (f"Assembled: {n_of('Printed (PLA)')} printed parts, {n_of('Purchased')} purchased parts "
           f"and {n_of('Fastener')} fasteners, on the board.")
    for i in range(1, 9):
        set_cam([a + (b - a) * ease(i / 8) for a, b in zip(cur, overall)])
        add(overlay(view.image(), "", cap), 1000 // FPS)
    add(overlay(view.image(), "", cap), 1500)
    cur = overall
    sol = solenoid_actors(view)

    def go_to(cam_to):
        """Cut to a close-up (camera moves redraw every pixel: costly in a GIF)."""
        nonlocal cur
        set_cam(cam_to)
        cur = cam_to

    # 1. tilt, whole doser: both gears of each pair turn
    cap = ("The two servos tilt the mounting plate about the hinge, up to 45 deg. Each servo's 14T "
           "pinion turns its 28T gear, so the pinion turns twice as far, the other way.")
    add(overlay(view.image(), "tilt 0 deg", cap), 1500)
    for t in list(np.linspace(0, 45, 10)) + list(np.linspace(45, 0, 10)):
        view.pose(one, tilt_M=ab.poses(t))
        add(overlay(view.image(), f"tilt {t:.0f} deg", cap), 1000 // FPS)
    durations[-11] = 900                 # pause at 45 deg
    motion_from = len(frames)
    # close-ups: 5 deg of tilt and 6 deg of stepper pinion a frame, a third of a
    # tooth or less, so the teeth don't strobe backwards
    tilts = list(np.linspace(0, 45, 10)) + [45.0] + list(np.linspace(45, 0, 10))

    # 2. the same, close up on one gear pair
    gear_c = np.array([48.0, layout.HINGE_Y, layout.HINGE_Z])
    pin_c = np.array([48.0, layout.HINGE_Y, layout.SERVO_SPLINE_Z])
    cam_gear = fit_camera(view, box((41, 24, 4), (55, 67, 64)), FIG1A, margin=0.85)
    cap = ("Close up: the 14T servo pinion (bottom) and the plate's 28T gear. 45 deg of tilt is "
           "90 deg at the servo.")
    view.pose(one)
    go_to(cam_gear)

    def gear_tags(t):
        return [("28T gear (plate)", gear_c + (0, 0, 16), (-150, -60)),
                (f"14T servo pinion, {-2 * t:.0f} deg", pin_c + (0, 0, -9), (-200, 40))]

    add(tagged(view, overlay(view.image(), "tilt 0 deg", cap), gear_tags(0)), 1500)
    for t in tilts:
        view.pose(one, tilt_M=ab.poses(t))
        add(tagged(view, overlay(view.image(), f"tilt {t:.0f} deg", cap), gear_tags(t)), 1000 // FPS)

    # 3. stepper drive: 20T pinion on the motor, 44T gear on the auger
    pin_s = np.array([-32.0, layout.HINGE_Y + 71.73, layout.HINGE_Z])
    gear_s = np.array([0.0, layout.HINGE_Y + 71.73, layout.HINGE_Z])
    cam_drive = fit_camera(view, box((-44, 110, 19), (24, 125, 67)), DRIVE, margin=0.85)
    cap = ("The stepper's 20T pinion turns the 44T gear on the auger tube: 2.2 turns of the motor per "
           "turn of the auger. The brackets and the tap collar stay put; the cap turns with the tube.")
    view.pose(one)
    go_to(cam_drive)

    def drive_tags(a):
        return [(f"20T pinion, {layout.STEPPER_RATIO * a:.0f} deg", pin_s + (0, 0, -13), (-170, 60)),
                (f"44T gear, {a:.0f} deg", gear_s + (0, 0, 25), (40, -60))]

    add(tagged(view, overlay(view.image(), "auger 0 deg", cap), drive_tags(0)), 1500)
    step = 6.0 / layout.STEPPER_RATIO       # pinion 6 deg a frame
    for i in range(1, 41):
        a = -step * i                       # pinion +6 deg a frame
        view.pose(one, tilt_M=ab.poses(0.0, a))
        add(tagged(view, overlay(view.image(), f"auger {abs(a):.0f} deg", cap), drive_tags(-a)), 70)
    view.pose(one)

    # 4. solenoid tapping: the plunger hits the tube through the collar's hole
    M_sol = ab.poses()["Solenoid (Adafruit 412)"]
    stroke = layout.SOLENOID_IN_COLLAR[2, 3] - (pp.SOL_BODY_L / 2 + pp.SOL_BOTTOM_STICKOUT) - TUBE_R
    cam_tap = fit_camera(view, pts(["Solenoid"], one), OUTLET_END, margin=0.75)
    cap = (f"The solenoid taps: its plunger drops {stroke:.1f} mm through the hole in the tap collar and "
           "hits the auger tube, then the spring pulls it back, to shake the powder loose.")
    go_to(cam_tap)
    view.actors["Solenoid (Adafruit 412)"].SetVisibility(False)
    for a in sol.values():
        a.SetVisibility(True)
    tap_pose(sol, M_sol, 0.0)
    add(overlay(view.image(), "tap", cap), 1200)
    for k in range(4):
        for s_mm, ms in ((0.5, 40), (1.0, 120), (0.6, 60), (0.25, 60), (0.0, 400)):
            tap_pose(sol, M_sol, s_mm * stroke)
            add(overlay(view.image(), f"tap {k + 1}", cap), ms)
    for a in sol.values():
        a.SetVisibility(False)
    view.actors["Solenoid (Adafruit 412)"].SetVisibility(True)
    motion_to = len(frames)

    go_to(overall)
    pns = ", ".join(dict.fromkeys(hardware.MCMASTER.values()))
    add(overlay(view.image(), "", f"Assembled. Fasteners (McMaster-Carr): {pns}."), 4000)

    save_gif(frames, durations, ab.RENDERS / "assembly_walkthrough.gif")
    save_gif(frames[motion_from:motion_to], durations[motion_from:motion_to],
             ab.RENDERS / "doser_motion.gif")


def save_gif(frames, durations, out, colors=128):
    """One shared palette, from every 6th frame at half size, keeps the
    colours steady from frame to frame; gifsicle -O3 (lossless) then stores
    only what changes."""
    w, h = SIZE[0] // 2, SIZE[1] // 2
    picks = [f.resize((w, h)) for f in frames[::6]]
    mosaic = Image.new("RGB", (w, h * len(picks)))
    for i, f in enumerate(picks):
        mosaic.paste(f, (0, i * h))
    pal = mosaic.quantize(colors=colors, method=Image.Quantize.MEDIANCUT)
    q = [f.quantize(palette=pal, dither=Image.Dither.NONE) for f in frames]
    q[0].save(out, save_all=True, append_images=q[1:], duration=durations, loop=0,
              optimize=False, disposal=1)
    if shutil.which("gifsicle"):
        subprocess.run(["gifsicle", "-O3", "--batch", str(out)], check=True)
    print(f"  -> {out.relative_to(ab.HERE)}  ({len(frames)} frames, {sum(durations) / 1000:.0f} s, "
          f"{out.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
