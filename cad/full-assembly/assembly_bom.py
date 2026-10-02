"""Bill of materials, assembly GIF and BOM call-out views of the current design.

Writes, from the same parts and positions as ``build.py``:

* ``BOM.md`` and ``assembly/bom.csv``: every part in the CAD assembly, in
  build order, with quantities, sources and (for fasteners) McMaster-Carr
  part numbers;
* ``renders/assembly_steps.gif``: the doser put together in 14 steps from
  a fully exploded start, with the BOM alongside and the rows of the step
  in progress highlighted, ending with a 0-45-0 deg tilt;
* ``renders/assembly_exploded_bom.png``: the exploded start with a
  numbered balloon on every BOM item;
* ``renders/assembly_bom_callouts.png``: the same balloons on the
  assembled doser.

Each part moves in along its own insertion direction, and parts ride on
the part they are attached to (the "parent") until their own step, so the
exploded start is the sum of every offset up the chain.

    xvfb-run -a python3 assembly_bom.py
"""
from __future__ import annotations

import csv
import math
from pathlib import Path

import numpy as np
import vtk
from PIL import Image, ImageDraw, ImageFont

import build
import hardware
import layout

HERE = Path(__file__).resolve().parent
RENDERS = HERE / "renders"
FONT_R = "/usr/share/fonts/truetype/crosextra/Carlito-Regular.ttf"
FONT_B = "/usr/share/fonts/truetype/crosextra/Carlito-Bold.ttf"

FUSION = {
    "Baseplate": "https://a360.co/4AOA7sI",
    "Mounting plate": "https://a360.co/4xXUj8L",
    "Auger": "https://a360.co/4y1oz2H",
    "Auger cap": "https://a360.co/4w9kRE5",
    "Bracket": "https://a360.co/46XtYN1",
    "Tap collar": "https://a360.co/4AIIgyz",
    "Servo pinion": "https://a360.co/4dcGSdF",
    "Stepper pinion": "https://a360.co/4yqSHFz",
}

# --------------------------------------------------------------------------- #
# Assembly steps: (title, [(instance or fastener-name prefix, parent, offset)])
# Offsets are world mm at tilt 0 (world = Fusion baseplate frame: Z up,
# outlet towards -Y, stepper on -X).  "fastener" uses the generic offset:
# a screw backs out along its own axis, a nut lifts off its seat.  The
# mounting board doesn't move: it is the bench everything is built on.
# --------------------------------------------------------------------------- #
UP = (0.0, 0.0, 1.0)
STEPS = [
    ("Baseplate onto the board", [("Mounting board", None, (0, 0, 0)),
                                  ("Baseplate", "Mounting board", (0, 0, 70))]),
    ("Screws into the board", [("Board screw", "Mounting board", "fastener")]),
    ("Servos into the posts", [("Servo MG996R (+X)", "Baseplate", (0, 0, 95)),
                               ("Servo MG996R (-X)", "Baseplate", (0, 0, 95))]),
    ("Servo screws and nuts", [("Servo screw", "Baseplate", "fastener"),
                               ("Servo nut", "Baseplate", "fastener")]),
    ("Servo pinions", [("Servo pinion (+X)", "Servo MG996R (+X)", (-34, 0, 0)),
                       ("Servo pinion (-X)", "Servo MG996R (-X)", (34, 0, 0)),
                       ("Servo pinion screw (+X)", "Servo pinion (+X)", "fastener"),
                       ("Servo pinion screw (-X)", "Servo pinion (-X)", "fastener")]),
    ("Mounting plate onto the hinge", [("Mounting plate", "Baseplate", (0, 0, 120))]),
    ("Hinge screws and locknuts", [("Hinge screw", "Baseplate", "fastener"),
                                   ("Hinge locknut", "Baseplate", "fastener")]),
    ("Stepper", [("Stepper (NEMA 11)", "Mounting plate", (0, 80, 0)),
                 ("Stepper screw", "Mounting plate", "fastener")]),
    ("Stepper pinion", [("Stepper pinion", "Stepper (NEMA 11)", (0, -40, 0))]),
    ("Tap-collar base", [("Tap collar base (AI)", "Mounting plate", (0, 0, 55)),
                         ("Tap base screw (-)", "Mounting plate", "fastener"),
                         ("Tap base nut (-)", "Tap collar base (AI)", "fastener"),
                         ("Tap base screw (+)", "Tap collar base (AI)", "fastener"),
                         ("Tap base nut (+)", "Mounting plate", "fastener")]),
    ("Auger with brackets and tap collar", [("Auger", "Mounting plate", (0, 0, 110)),
                                            ("Bracket (rear)", "Auger", (0, 0, 0)),
                                            ("Bracket (front)", "Auger", (0, 0, 0)),
                                            ("Tap collar", "Auger", (0, 0, 0))]),
    ("Bracket and collar screws", [("Bracket screw", "Mounting plate", "fastener"),
                                   ("Bracket nut", "Bracket", "fastener"),
                                   ("Bracket clamp", "Bracket", "fastener"),
                                   ("Tap collar clamp", "Tap collar", "fastener")]),
    ("Solenoid", [("Solenoid (Adafruit 412)", "Tap collar", "solenoid"),
                  ("Solenoid screw", "Tap collar", "fastener")]),
    ("Auger cap", [("Auger cap", "Auger", (0, 70, 0))]),
]

# BOM item for every instance (fasteners: by hardware key)
ITEM_OF_PART = {
    "Baseplate": "Baseplate", "Mounting plate": "Mounting plate", "Auger": "Auger",
    "Auger cap": "Auger cap", "Bracket (rear)": "Bracket", "Bracket (front)": "Bracket",
    "Tap collar base (AI)": "Tap-collar base", "Tap collar": "Tap collar",
    "Solenoid (Adafruit 412)": "Solenoid", "Stepper pinion": "Stepper pinion",
    "Stepper (NEMA 11)": "Stepper motor", "Servo pinion (+X)": "Servo pinion",
    "Servo pinion (-X)": "Servo pinion", "Servo MG996R (+X)": "Servo",
    "Servo MG996R (-X)": "Servo", "Mounting board": "Mounting board",
}
ITEM_INFO = {
    "Mounting board": ("User-supplied", "any flat board or bench top, 38 mm (1.5 in) thick "
                       "(drawn 250 x 220 mm)", ""),
    "Baseplate": ("Printed (PLA)", "Fusion 360, lab account", FUSION["Baseplate"]),
    "Servo": ("Purchased", "MG996R metal-gear servo",
              "https://askelectronics.co.ke/product/servo-motor-mg996r-high-torque-metal-gear/"),
    "Servo pinion": ("Printed (PLA)", "Fusion 360, lab account; 14 T", FUSION["Servo pinion"]),
    "Mounting plate": ("Printed (PLA)", "Fusion 360, lab account", FUSION["Mounting plate"]),
    "Stepper motor": ("Purchased", "NEMA 11, StepperOnline 11HS18-0674S",
                      "https://www.omc-stepperonline.com/nema-11-bipolar-1-8deg-9-5ncm-13-5oz-in-0-67a-4-6v-28x28x45mm-4-wires-11hs18-0674s"),
    "Stepper pinion": ("Printed (PLA)", "Fusion 360, lab account; 20 T module 1", FUSION["Stepper pinion"]),
    "Tap-collar base": ("Printed (PLA)", "AI-modelled (PR #51), the one AI part left on the rig",
                        "components/ai-step/tap-collar-base.step"),
    "Auger": ("Printed (PLA)", "Fusion 360, lab account; 44 T gear on the tube", FUSION["Auger"]),
    "Bracket": ("Printed (PLA)", "Fusion 360, lab account", FUSION["Bracket"]),
    "Tap collar": ("Printed (PLA)", "Fusion 360, lab account", FUSION["Tap collar"]),
    "Solenoid": ("Purchased", "Adafruit 412, 12 V push-pull", "https://www.adafruit.com/product/412"),
    "Auger cap": ("Printed (PLA)", "Fusion 360, lab account", FUSION["Auger cap"]),
}
SHORT = {  # short fastener names for the table
    "bhcs_m5x45": "M5×45 button head screw",
    "locknut_m5": "M5 nylon-insert locknut",
    "shcs_m3x14": "M3×14 socket head screw",
    "shcs_m3x10": "M3×10 socket head screw",
    "locknut_m3": "M3 nylon-insert locknut",
    "shcs_m3x5": "M3×5 socket head screw",
    "bhcs_m3x20": "M3×20 button head screw",
    "bhcs_m3x25": "M3×25 button head screw",
    "fhcs_m3x30": "M3×30 flat head screw",
    "hexnut_m3": "M3 hex nut",
    "shcs_m2p5x8": "M2.5×8 socket head screw",
    "wood_10x1p25": "#10×1¼ in pan head wood screw",
}


def _T(t) -> np.ndarray:
    M = np.eye(4)
    M[:3, 3] = t
    return M


# --------------------------------------------------------------------------- #
# Scene graph
# --------------------------------------------------------------------------- #
def poses(tilt_deg: float = 0.0, auger_deg: float = 0.0) -> dict[str, np.ndarray]:
    """World 4x4 of every instance (parts, board, fasteners) at a tilt and
    auger angle; the gears turn with them (layout.placements)."""
    P = {**layout.placements(tilt_deg, auger_deg=auger_deg), **layout.mount_placements()}
    out = {n: M for n, (_, M) in P.items()}
    out.update({n: M for n, _, _, M in hardware.fastener_placements(tilt_deg, with_board=True)})
    return out


def scene(tilt_deg: float = 0.0):
    """Instances in build order: dicts with name, item, polydata, colour,
    world 4x4 (final), parent, offset (world vector) and step index."""
    P = {**layout.placements(tilt_deg), **layout.mount_placements()}
    F = hardware.fastener_placements(tilt_deg, with_board=True)
    inst = {}
    for name, (rel, M) in P.items():
        inst[name] = dict(name=name, item=ITEM_OF_PART[name], pd=build._step_polydata(rel),
                          colour=build.COLOURS[name], M=M, metal=False)
    for name, key, joint, M in F:
        inst[name] = dict(name=name, item=key, pd=build._fastener_polydata(key),
                          colour=build.COL_STEEL, M=M, metal=True, key=key)
    order = []
    for k, (title, entries) in enumerate(STEPS):
        for pattern, parent, off in entries:
            if off == "fastener":      # every fastener whose name starts with the pattern
                names = [n for n in inst if n.startswith(pattern) and "key" in inst[n]]
            else:
                names = [pattern]
            names = [n for n in names if "step" not in inst[n]]
            assert names, pattern
            for n in names:
                d = inst[n]
                d["step"] = k
                # brackets' screws etc. name their own bracket as the parent
                par = parent
                if parent == "Bracket":
                    par = "Bracket (rear)" if "rear" in n else "Bracket (front)"
                d["parent"] = par
                if off == "fastener":
                    z = d["M"][:3, 2]
                    L = hardware.HARDWARE[d["key"]].get("L", 0.0)
                    nut = hardware.HARDWARE[d["key"]]["kind"] == "nut"
                    d["off"] = z * (14.0 if nut else -(L + 10.0))
                elif off == "solenoid":
                    d["off"] = d["M"][:3, 2] * 45.0     # back out along the plunger axis
                else:
                    d["off"] = np.asarray(off, float)
                order.append(n)
    missing = [n for n in inst if "step" not in inst[n]]
    assert not missing, missing
    return [inst[n] for n in order], inst


def displacement(d, inst, s_of_step) -> np.ndarray:
    """World translation of an instance when step k is s_of_step(k) done."""
    v = np.zeros(3)
    while d is not None:
        v += d["off"] * (1.0 - s_of_step(d["step"]))
        d = inst.get(d["parent"]) if d["parent"] else None
    return v


# --------------------------------------------------------------------------- #
# BOM
# --------------------------------------------------------------------------- #
def bom(order) -> list[dict]:
    rows, seen = [], {}
    for d in order:
        it = d["item"]
        if it in seen:
            seen[it]["qty"] += 1
            continue
        if it in hardware.HARDWARE:
            spec = hardware.HARDWARE[it]
            pn = hardware.MCMASTER.get(it, "")
            row = dict(name=SHORT[it], kind="Fastener", desc=spec["desc"],
                       source=f"McMaster-Carr {pn}" if pn else "McMaster-Carr (see note)",
                       link=f"https://www.mcmaster.com/{pn}/" if pn else "")
        else:
            kind, desc, link = ITEM_INFO[it]
            row = dict(name=it, kind=kind, desc=desc, source=desc, link=link)
        row.update(item=it, qty=1, step=d["step"])
        rows.append(row)
        seen[it] = row
    for i, r in enumerate(rows, 1):
        r["no"] = i
    return rows


def write_bom(rows, order) -> None:
    with open(HERE / "assembly" / "bom.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["No.", "Part", "Qty", "Type", "Description / source", "Link", "Step"])
        for r in rows:
            w.writerow([r["no"], r["name"], r["qty"], r["kind"], r["desc"], r["link"], r["step"] + 1])
    lines = ["# Bill of materials: current powder-doser module", "",
             "Every part in the CAD assembly, numbered in build order (the numbers match the",
             "balloons in `renders/assembly_exploded_bom.png`, `renders/assembly_bom_callouts.png`",
             "and `renders/assembly_steps.gif`).  Generated by `assembly_bom.py`; also in",
             "`assembly/bom.csv`.  Electronics, wiring and the balance are not in the CAD;",
             "see the SI bill of materials in PR #97.  Item 1 is whatever the doser is",
             "screwed down to: any flat board or bench top 38 mm (1.5 in) thick, which is",
             "the depth the baseplate's legs are made for.", "",
             "| No. | Part | Qty | Type | Source | Step |", "|---:|---|---:|---|---|---:|"]
    for r in rows:
        src = f"[{r['source']}]({r['link']})" if r["link"].startswith("http") else (
            f"{r['source']} (`{r['link']}`)" if r["link"] else r["source"])
        lines.append(f"| {r['no']} | {r['name']} | {r['qty']} | {r['kind']} | {src} | {r['step'] + 1} |")
    n_fast = sum(r["qty"] for r in rows if r["kind"] == "Fastener")
    n_print = sum(r["qty"] for r in rows if r["kind"].startswith("Printed"))
    n_own = sum(r["qty"] for r in rows if r["kind"] == "User-supplied")
    lines += ["", f"{len(rows)} line items: {n_print} printed parts, "
              f"{sum(r['qty'] for r in rows if r['kind'] == 'Purchased')} purchased parts, "
              f"{n_fast} fasteners and {n_own} board you supply.", "", "## Build steps", ""]
    for k, (title, _) in enumerate(STEPS):
        used = [r for r in rows if any(d["step"] == k and d["item"] == r["item"] for d in order)]
        nos = ", ".join(str(r["no"]) for r in used)
        lines.append(f"{k + 1}. {title} (item{'s' if len(used) > 1 else ''} {nos})")
    (HERE / "BOM.md").write_text("\n".join(lines) + "\n")
    print("  -> BOM.md, assembly/bom.csv")


# --------------------------------------------------------------------------- #
# Rendering
# --------------------------------------------------------------------------- #
def _font(size, bold=False):
    try:
        return ImageFont.truetype(FONT_B if bold else FONT_R, size)
    except OSError:
        return ImageFont.load_default()


class View:
    def __init__(self, order, inst, size, tilt=0.0):
        self.order, self.inst = order, inst
        self.ren = vtk.vtkRenderer()
        self.ren.SetBackground(1, 1, 1)
        self.win = vtk.vtkRenderWindow()
        self.win.SetOffScreenRendering(1)
        self.win.SetSize(*size)
        self.win.AddRenderer(self.ren)
        self.actors = {}
        for d in order:
            a = build._actor(d["pd"], d["colour"], build.W2J @ d["M"], metal=d["metal"])
            if d["item"] == "Mounting board":      # matte, so its top doesn't go dark
                a.GetProperty().SetAmbient(0.45)
                a.GetProperty().SetDiffuse(0.6)
                a.GetProperty().SetSpecular(0.0)
            self.ren.AddActor(a)
            self.actors[d["name"]] = a

    def pose(self, s_of_step, visible_from=None, tilt_M=None):
        for d in self.order:
            v = displacement(d, self.inst, s_of_step)
            M = d["M"] if tilt_M is None else tilt_M[d["name"]]
            self.actors[d["name"]].SetUserTransform(build._vtk_matrix(build.W2J @ _T(v) @ M))
            self.actors[d["name"]].SetVisibility(visible_from is None or d["step"] <= visible_from)

    def camera(self, pts_world, margin=0.94):
        """Look along the Fig. 1a direction and fit the given world points."""
        cam = self.ren.GetActiveCamera()
        cam.SetViewUp(0, 0, 1)
        c = build.JUNE_AZ090_CAMERA
        dirv = np.subtract(c["position"], c["focal_point"])
        dirv /= np.linalg.norm(dirv)
        pts = np.c_[pts_world, np.ones(len(pts_world))]
        cj = (build.W2J @ pts.T).T[:, :3]
        ctr = (cj.min(0) + cj.max(0)) / 2
        cam.SetFocalPoint(*ctr)
        cam.SetPosition(*(ctr + dirv * 1500))
        cam.SetViewAngle(18.0)
        self.ren.ResetCamera(*np.ravel(list(zip(cj.min(0), cj.max(0)))))
        W, H = self.win.GetSize()
        for _ in range(3):          # fill the viewport with the projected box
            px = np.array([self.project(p) for p in cj])
            (x0, y0), (x1, y1) = px.min(0), px.max(0)
            f = margin * min(W / (x1 - x0), H / (y1 - y0))
            # pan so the projected box is centred, then zoom
            mid = np.array([(x0 + x1) / 2, (y0 + y1) / 2])
            c = vtk.vtkCoordinate()
            c.SetCoordinateSystemToDisplay()
            c.SetValue(mid[0], H - mid[1], 0)
            fp = np.array(cam.GetFocalPoint())
            ray = np.array(c.GetComputedWorldValue(self.ren)) - np.array(cam.GetPosition())
            ray /= np.linalg.norm(ray)
            dop = np.array(cam.GetDirectionOfProjection())
            t = np.dot(fp - np.array(cam.GetPosition()), dop) / np.dot(ray, dop)
            new_fp = np.array(cam.GetPosition()) + ray * t
            shift = new_fp - fp
            cam.SetFocalPoint(*(fp + shift))
            cam.SetPosition(*(np.array(cam.GetPosition()) + shift))
            cam.Zoom(f)
        self.ren.ResetCameraClippingRange()

    def image(self) -> Image.Image:
        self.win.Render()
        w2i = vtk.vtkWindowToImageFilter()
        w2i.SetInput(self.win)
        w2i.ReadFrontBufferOff()
        w2i.Update()
        from vtkmodules.util.numpy_support import vtk_to_numpy
        img = w2i.GetOutput()
        w, h, _ = img.GetDimensions()
        a = vtk_to_numpy(img.GetPointData().GetScalars()).reshape(h, w, -1)[::-1, :, :3]
        return Image.fromarray(np.ascontiguousarray(a))

    def project(self, p_june):
        c = vtk.vtkCoordinate()
        c.SetCoordinateSystemToWorld()
        c.SetValue(*p_june)
        x, y = c.GetComputedDoubleDisplayValue(self.ren)
        return x, self.win.GetSize()[1] - y


def _points(order, inst, s_of_step, tilt_M=None, every=25):
    """A thinned cloud of world-space vertices of every instance."""
    from vtkmodules.util.numpy_support import vtk_to_numpy
    out = []
    for d in order:
        v = vtk_to_numpy(d["pd"].GetPoints().GetData())[::every]
        M = d["M"] if tilt_M is None else tilt_M[d["name"]]
        M = _T(displacement(d, inst, s_of_step)) @ M
        out.append(v @ M[:3, :3].T + M[:3, 3])
    return np.vstack(out)


def _bounds(order, inst, s_of_step):
    lo, hi = np.full(3, 1e9), np.full(3, -1e9)
    for d in order:
        b = d["pd"].GetBounds()
        pts = np.array([[x, y, z, 1.0] for x in b[:2] for y in b[2:4] for z in b[4:]])
        w = (_T(displacement(d, inst, s_of_step)) @ d["M"] @ pts.T).T[:, :3]
        lo, hi = np.minimum(lo, w.min(0)), np.maximum(hi, w.max(0))
    return lo, hi


def anchor_world(d, inst, s_of_step):
    """A point on the instance for its balloon leader: the centre of its
    bounding box, pulled towards the side facing the camera."""
    b = d["pd"].GetBounds()
    c = np.array([(b[0] + b[1]) / 2, (b[2] + b[3]) / 2, (b[4] + b[5]) / 2, 1.0])
    p = (_T(displacement(d, inst, s_of_step)) @ d["M"] @ c)[:3]
    return p


def draw_balloons(img, view, rows, order, inst, s_of_step, items=None, r=13, avoid=None):
    """Numbered balloons with leaders; one per BOM row (first instance)."""
    d_img = ImageDraw.Draw(img)
    font = _font(int(r * 1.45), bold=True)
    W, H = img.size
    first = {}
    for d in order:
        if d["item"] not in first and (items is None or d["item"] in items):
            first[d["item"]] = d
    pts = []
    for row in rows:
        d = first.get(row["item"])
        if d is None:
            continue
        pj = (build.W2J @ np.append(anchor_world(d, inst, s_of_step), 1.0))[:3]
        pts.append((row["no"], np.array(view.project(pj))))
    if not pts:
        return
    ctr = np.mean([p for _, p in pts], axis=0)
    # parts' silhouette: balloons go on the white background, not on parts
    arr = np.asarray(img.convert("RGB")).astype(int)
    solid = (arr.sum(axis=2) < 3 * 245)

    def on_parts(b):
        x0, x1 = int(max(0, b[0] - r)), int(min(W, b[0] + r + 1))
        y0, y1 = int(max(0, b[1] - r)), int(min(H, b[1] + r + 1))
        return solid[y0:y1, x0:x1].mean() if x1 > x0 and y1 > y0 else 0.0

    # initial balloon positions: pushed out radially until off the parts,
    # then relaxed apart (and kept off the parts)
    pos = []
    for no, p in pts:
        v = p - ctr
        n = np.linalg.norm(v) or 1.0
        u = v / n
        b = p + u * 40
        for _ in range(60):
            if on_parts(b) < 0.02:
                break
            b = b + u * 8
        pos.append(b + u * 12)
    pos = np.array(pos, float)
    for _ in range(300):
        for i in range(len(pos)):
            for j in range(i + 1, len(pos)):
                dv = pos[i] - pos[j]
                dist = np.linalg.norm(dv)
                if dist < 2.5 * r:
                    push = (dv / (dist or 1.0)) * (2.5 * r - dist) / 2
                    pos[i] += push
                    pos[j] -= push
        for i in range(len(pos)):          # drift back off any part
            if on_parts(pos[i]) > 0.02:
                v = pos[i] - ctr
                pos[i] += v / (np.linalg.norm(v) or 1.0) * 3
        pos[:, 0] = np.clip(pos[:, 0], r + 4, W - r - 4)
        pos[:, 1] = np.clip(pos[:, 1], r + 4, H - r - 4)
    for (no, p), b in zip(pts, pos):
        d_img.line([tuple(p), tuple(b)], fill=(90, 90, 90), width=2)
        d_img.ellipse((p[0] - 3, p[1] - 3, p[0] + 3, p[1] + 3), fill=(60, 60, 60))
        d_img.ellipse((b[0] - r, b[1] - r, b[0] + r, b[1] + r), fill=(255, 255, 255),
                      outline=(40, 40, 40), width=2)
        d_img.text(tuple(b), str(no), font=font, fill=(20, 20, 20), anchor="mm")


def bom_panel(rows, size, highlight=(), title="Bill of materials", step_title=None):
    W, H = size
    img = Image.new("RGB", size, (255, 255, 255))
    d = ImageDraw.Draw(img)
    pad = 14
    d.text((pad, pad), title, font=_font(26, bold=True), fill=(20, 20, 20))
    y = pad + 34
    if step_title:
        d.text((pad, y), step_title, font=_font(19, bold=True), fill=(46, 100, 160))
    y += 30
    row_h = (H - y - pad) / (len(rows) + 1)
    f = _font(int(min(18, row_h * 0.72)))
    fb = _font(int(min(18, row_h * 0.72)), bold=True)
    cols = (pad, pad + 34, W - pad - 128, W - pad - 88)
    for x, t in zip(cols, ("No.", "Part", "Qty", "Type")):
        d.text((x, y), t, font=fb, fill=(60, 60, 60))
    y += row_h
    d.line([(pad, y - 3), (W - pad, y - 3)], fill=(150, 150, 150), width=1)
    for r in rows:
        on = r["no"] in highlight
        if on:
            d.rectangle((pad - 4, y - 2, W - pad + 4, y + row_h - 4), fill=(255, 236, 170))
        col = (20, 20, 20) if on or not highlight else (90, 90, 90)
        ff = fb if on else f
        d.text((cols[0], y), f"{r['no']}", font=ff, fill=col)
        d.text((cols[1], y), r["name"], font=ff, fill=col)
        d.text((cols[2], y), f"{r['qty']}", font=ff, fill=col)
        kind = {"Printed (PLA)": "printed", "User-supplied": "yours"}.get(r["kind"], r["kind"].lower())
        d.text((cols[3], y), kind, font=ff, fill=col)
        y += row_h
    return img


def main() -> None:
    order, inst = scene()
    rows = bom(order)
    write_bom(rows, order)
    nsteps = len(STEPS)

    view_size, panel_w = (900, 680), 470
    view = View(order, inst, view_size)
    lo0, hi0 = _bounds(order, inst, lambda k: 0.0)     # exploded
    lo1, hi1 = _bounds(order, inst, lambda k: 1.0)     # assembled
    cam = view.ren.GetActiveCamera()

    def cam_state():
        return [np.array(cam.GetPosition()), np.array(cam.GetFocalPoint())]

    def set_cam(st):
        cam.SetPosition(*st[0])
        cam.SetFocalPoint(*st[1])
        view.ren.ResetCameraClippingRange()

    def tilt_Ms(t):
        return poses(float(t))

    one = lambda k: 1.0       # noqa: E731
    pts1 = _points(order, inst, one)
    pts45 = _points(order, inst, one, tilt_M=tilt_Ms(45.0))
    view.camera(np.vstack([pts1, pts45]), margin=0.9)
    cam_assembled = cam_state()
    view.camera(pts1, margin=0.78)          # room for the balloons
    cam_callouts = cam_state()
    view.camera(np.vstack([_points(order, inst, lambda k: 0.0), pts1]), margin=0.9)
    cam_exploded = cam_state()

    def compose(view_img, highlight, step_title):
        canvas = Image.new("RGB", (view_size[0] + panel_w, view_size[1]), "white")
        canvas.paste(view_img, (0, 0))
        canvas.paste(bom_panel(rows, (panel_w, view_size[1]), highlight, step_title=step_title),
                     (view_size[0], 0))
        return canvas

    # static views: exploded start and assembled, every item ballooned
    for tag, s in (("exploded", 0.0), ("callouts", 1.0)):
        set_cam(cam_exploded if s == 0 else cam_callouts)
        view.pose(lambda k, s=s: s)
        img = view.image()
        draw_balloons(img, view, rows, order, inst, lambda k, s=s: s)
        out = RENDERS / ("assembly_exploded_bom.png" if s == 0 else "assembly_bom_callouts.png")
        compose(img, (), "Exploded view" if s == 0 else "Assembled").save(out)
        print(f"  -> {out.relative_to(HERE)}")

    # animation
    frames, durations = [], []

    def add(img, ms):
        frames.append(img)
        durations.append(ms)

    set_cam(cam_exploded)
    view.pose(lambda k: 0.0)
    img = view.image()
    draw_balloons(img, view, rows, order, inst, lambda k: 0.0)
    add(compose(img, (), "All parts"), 2500)
    n_move = 9
    for k in range(nsteps):
        nos = [r["no"] for r in rows if any(d["step"] == k and d["item"] == r["item"] for d in order)]
        items = {d["item"] for d in order if d["step"] == k}
        title = f"Step {k + 1}/{nsteps}: {STEPS[k][0]}"
        for i in range(1, n_move + 1):
            e = i / n_move
            e = e * e * (3 - 2 * e)      # ease in-out
            s_of = (lambda kk, k=k, e=e: 1.0 if kk < k else (e if kk == k else 0.0))
            view.pose(s_of)
            img = view.image()
            if i == n_move:
                draw_balloons(img, view, rows, order, inst, s_of, items=items)
            add(compose(img, nos, title), 70 if i < n_move else 900)
    # zoom in on the assembled doser, then tilt 0 -> 45 -> 0 about the hinge
    view.pose(lambda k: 1.0)
    for i in range(1, 9):
        e = i / 8
        e = e * e * (3 - 2 * e)
        set_cam([a + (b - a) * e for a, b in zip(cam_exploded, cam_assembled)])
        add(compose(view.image(), (), "Assembled"), 70)
    img = view.image()
    draw_balloons(img, view, rows, order, inst, lambda k: 1.0)
    add(compose(img, (), "Assembled"), 2000)
    tilt_frames = list(np.linspace(0, 45, 10)) + [45.0] * 3 + list(np.linspace(45, 0, 10))
    _, inst_t = None, None
    for t in tilt_frames:
        view.pose(lambda k: 1.0, tilt_M=tilt_Ms(t))
        add(compose(view.image(), (), f"Tilt {t:.0f}° (max 45°)"), 90)
    durations[-1] = 1500

    # one global palette keeps frame-to-frame deltas small
    picks = [frames[i] for i in np.linspace(0, len(frames) - 1, 8).astype(int)]
    mosaic = Image.new("RGB", (picks[0].width, picks[0].height * len(picks)))
    for i, f in enumerate(picks):
        mosaic.paste(f, (0, i * f.height))
    pal = mosaic.quantize(colors=160, method=Image.Quantize.MEDIANCUT)
    q = [f.quantize(palette=pal, dither=Image.Dither.NONE) for f in frames]
    out = RENDERS / "assembly_steps.gif"
    q[0].save(out, save_all=True, append_images=q[1:], duration=durations, loop=0,
              optimize=False, disposal=1)
    print(f"  -> {out.relative_to(HERE)}  ({len(frames)} frames, "
          f"{out.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
