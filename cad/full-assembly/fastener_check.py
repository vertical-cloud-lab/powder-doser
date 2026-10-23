"""Each fastener stand-in next to McMaster-Carr's own picture and numbers.

For every part number in hardware.MCMASTER (including the wood screws
that hold the baseplate to its board) this draws one row:
McMaster's product image for the family, the stand-in as the renders used
it until 2 Oct 2026, the stand-in now, and McMaster's catalog dimensions
for that exact part number against the model's.  Both renders use
McMaster's "front orientation": a screw lies along the picture with its
head on the right and its tip rising to the left, seen from the head end;
a nut sits on its bearing face, seen from about 30 degrees above, with a
flat towards the viewer.

McMaster's figures and the image files come from components/mcmaster/
(parts.json, and img/, which is not committed; see the README there).

    xvfb-run -a python3 fastener_check.py      # -> renders/fastener_check.png
"""
from __future__ import annotations

import json
import textwrap
from pathlib import Path

import numpy as np
import vtk
from PIL import Image, ImageDraw, ImageFont
from vtkmodules.util.numpy_support import vtk_to_numpy

import build
import hardware

HERE = Path(__file__).resolve().parent
MCM = HERE / "components" / "mcmaster"
OUT = HERE / "renders" / "fastener_check.png"
FONT_R = "/usr/share/fonts/truetype/crosextra/Carlito-Regular.ttf"
FONT_B = "/usr/share/fonts/truetype/crosextra/Carlito-Bold.ttf"
FONT_SYM = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"     # has the tick and cross
NYLON = (0.93, 0.93, 0.90)

# The stand-ins as rendered until 2 Oct 2026 (cosmetic=False, and these specs)
BEFORE = {"fhcs_m3x30": {"k": 1.5}}
NEW = {"wood_10x1p25": "added 2 Oct with the mounting board"}

# Camera direction (from the part towards the camera) in the display frame:
# screws along X, head at +X; nuts standing on Z.  Matched by eye to
# McMaster's images (components/mcmaster/img).
VIEW = {
    "shcs": (0.50, -1.0, 0.42),
    "bhcs": (0.80, -1.0, 0.42),
    "fhcs": (1.25, -1.0, 0.55),
    "wood": (0.80, -1.0, 0.42),
    "nut": (0.0, -1.0, 0.45),
}


def _font(size, bold=False):
    try:
        return ImageFont.truetype(FONT_B if bold else FONT_R, size)
    except OSError:
        return ImageFont.load_default()


def _display_matrix(kind: str) -> np.ndarray:
    """Seat frame -> display frame: a screw's shank (+Z) points to -X."""
    M = np.eye(4)
    if kind != "nut":
        M[:3, :3] = [[0, 0, -1], [0, 1, 0], [1, 0, 0]]     # +Z -> -X, head (z < 0) -> +X
    return M


def render(shapes_colours, kind: str, size=(1200, 800)) -> Image.Image:
    ren = vtk.vtkRenderer()
    ren.SetBackground(1, 1, 1)
    M = _display_matrix(kind)
    for shape, colour in shapes_colours:
        ren.AddActor(build._actor(build._polydata(shape), colour, M, metal=colour != NYLON))
    kit = vtk.vtkLightKit()
    kit.SetKeyLightIntensity(0.85)
    kit.AddLightsToRenderer(ren)
    win = vtk.vtkRenderWindow()
    win.SetOffScreenRendering(1)
    win.SetSize(*size)
    win.SetMultiSamples(8)
    win.AddRenderer(ren)
    cam = ren.GetActiveCamera()
    d = np.array(VIEW["nut" if kind == "nut" else kind], float)
    d /= np.linalg.norm(d)
    cam.SetFocalPoint(0, 0, 0)
    cam.SetPosition(*(d * 500))
    cam.SetViewUp(0, 0, 1)
    cam.SetViewAngle(15)
    ren.ResetCamera()
    cam.Zoom(1.25)
    win.Render()
    w2i = vtk.vtkWindowToImageFilter()
    w2i.SetInput(win)
    w2i.ReadFrontBufferOff()
    w2i.Update()
    img = w2i.GetOutput()
    w, h, _ = img.GetDimensions()
    a = vtk_to_numpy(img.GetPointData().GetScalars()).reshape(h, w, -1)[::-1, :, :3]
    return Image.fromarray(np.ascontiguousarray(a))


def fit(img: Image.Image, box, bg=(255, 255, 255)) -> Image.Image:
    """Crop to the part (non-background pixels) and fit it in box (w, h)."""
    rgba = img.convert("RGBA")
    if rgba.getextrema()[3][0] < 255:          # transparent background
        flat = Image.new("RGBA", rgba.size, bg + (255,))
        flat.alpha_composite(rgba)
        mask = np.array(rgba)[:, :, 3] > 8
        rgba = flat
    else:
        mask = (np.abs(np.array(rgba)[:, :, :3].astype(int) - np.array(bg)).sum(2) > 18)
    ys, xs = np.nonzero(mask)
    crop = rgba.convert("RGB").crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
    s = min(box[0] / crop.width, box[1] / crop.height)
    crop = crop.resize((max(1, int(crop.width * s)), max(1, int(crop.height * s))), Image.LANCZOS)
    cell = Image.new("RGB", box, bg)
    cell.paste(crop, ((box[0] - crop.width) // 2, (box[1] - crop.height) // 2))
    return cell


def compare_rows(key: str, spec: dict, mc: dict) -> list[tuple[str, str, str, bool]]:
    """(quantity, McMaster, model, match) for the dimensions McMaster lists."""
    old = dict(spec, **BEFORE.get(key, {}))
    rows = []
    if spec["kind"] == "nut":
        rows.append(("width across flats", f"{mc['width_mm']:g}", f"{spec['s']:g}", abs(mc["width_mm"] - spec["s"]) < 1e-6))
        rows.append(("height", f"{mc['height_mm']:g}", f"{spec['m']:g}", abs(mc["height_mm"] - spec["m"]) < 1e-6))
    else:
        rows.append(("length", f"{mc['length_mm']:g}", f"{spec['L']:g}", abs(mc["length_mm"] - spec["L"]) < 1e-6))
        rows.append(("head diameter", f"{mc['head_dia_mm']:g}", f"{spec['dk']:g}", abs(mc["head_dia_mm"] - spec["dk"]) < 1e-6))
        k_txt = f"{spec['k']:g}" + (f" (was {old['k']:g})" if old["k"] != spec["k"] else "")
        rows.append(("head height", f"{mc['head_ht_mm']:g}", k_txt, abs(mc["head_ht_mm"] - spec["k"]) < 1e-6))
        if spec["kind"] == "wood":
            rows.append(("thread length", f"{mc['thread_length_mm']:g}", f"{spec['thread_len']:g}",
                         abs(mc["thread_length_mm"] - spec["thread_len"]) < 1e-6))
        else:
            rows.append(("threading", mc["threading"].lower(), "fully threaded (was plain)", True))
    if spec.get("insert"):
        rows.append(("nylon insert", "yes", "yes (was a plain hex)", True))
    return rows


def main() -> None:
    db = json.loads((MCM / "parts.json").read_text())
    qty = {r["key"]: (r["qty"], ", ".join(r["joints"])) for r in hardware.bom_rows(with_board=True)}
    keys = list(hardware.HARDWARE)
    cell = (300, 150)
    pad, label_w, table_w, row_h, head_h = 16, 270, 520, 186, 64
    W = pad + label_w + 3 * (cell[0] + pad) + table_w + pad
    H = head_h + len(keys) * row_h + 40
    sheet = Image.new("RGB", (W, H), "white")
    dr = ImageDraw.Draw(sheet)
    x_img = pad + label_w
    xs = [x_img + i * (cell[0] + pad) for i in range(3)]
    x_tab = xs[2] + cell[0] + 2 * pad
    dr.text((pad, 14), "Fasteners: McMaster-Carr vs. the CAD stand-ins, in McMaster's orientation",
            font=_font(26, True), fill=(20, 20, 20))
    for x, t in zip(xs + [x_tab], ("McMaster-Carr product image (family)", "Stand-in until 2 Oct",
                                   "Stand-in now", "McMaster catalog row vs. model (mm)")):
        dr.text((x, head_h - 20), t, font=_font(17, True), fill=(70, 70, 70))
    n_bad = 0
    for i, key in enumerate(keys):
        spec = hardware.HARDWARE[key]
        pn = hardware.MCMASTER[key]
        part = db["parts"][pn]
        fam = db["families"][part["family"]]
        mc = part["mcmaster"]
        y = head_h + i * row_h
        dr.line([(pad, y), (W - pad, y)], fill=(215, 215, 215), width=1)
        y += 10
        n, joints = qty[key]
        dr.text((pad, y + 4), pn, font=_font(22, True), fill=(20, 20, 20))
        dr.text((pad, y + 32), hardware.SHORT[key], font=_font(18), fill=(30, 30, 30))
        dr.text((pad, y + 56), f"qty {n}: {joints}", font=_font(16), fill=(90, 90, 90))
        for j, line in enumerate(textwrap.wrap(fam["family"], 34)):
            dr.text((pad, y + 80 + 17 * j), line, font=_font(14), fill=(120, 120, 120))
        img_path = MCM / "img" / fam["image"]
        if img_path.exists():
            sheet.paste(fit(Image.open(img_path), cell), (xs[0], y))
        else:
            dr.text((xs[0] + 10, y + 60), "(image not fetched: see\ncomponents/mcmaster/README.md)",
                    font=_font(15), fill=(150, 60, 60))
        kind = "nut" if spec["kind"] == "nut" else spec["kind"]
        old = dict(spec, **BEFORE.get(key, {}))
        before = [(hardware._iso_model(old, cosmetic=False).val(), build.COL_STEEL)]
        now = [(hardware._iso_model(spec).val(), build.COL_STEEL)]
        ins = hardware.nylon_insert(spec)
        if ins is not None:
            now.append((ins, NYLON))
        if key in NEW:
            dr.text((xs[1] + 10, y + 60), f"(none: {NEW[key]})", font=_font(15), fill=(120, 120, 120))
        else:
            sheet.paste(fit(render(before, kind), cell), (xs[1], y))
        sheet.paste(fit(render(now, kind), cell), (xs[2], y))
        ty = y + 2
        dr.text((x_tab + 150, ty), "McMaster", font=_font(14), fill=(120, 120, 120))
        dr.text((x_tab + 285, ty), "model", font=_font(14), fill=(120, 120, 120))
        ty += 20
        for q, a, b, ok in compare_rows(key, spec, mc):
            n_bad += not ok
            dr.text((x_tab, ty), q, font=_font(16), fill=(60, 60, 60))
            dr.text((x_tab + 150, ty), a, font=_font(16, True), fill=(20, 20, 20))
            dr.text((x_tab + 285, ty), b, font=_font(16), fill=(20, 20, 20))
            dr.text((x_tab + table_w - 26, ty), "✓" if ok else "✗", font=ImageFont.truetype(FONT_SYM, 17),
                    fill=(30, 130, 60) if ok else (190, 40, 40))
            ty += 24
    dr.text((pad, H - 30), "McMaster images and figures: mcmaster.com catalog pages, read 2 Oct 2026 "
            "(components/mcmaster/parts.json). The family image is one size of the family, so its "
            "length-to-diameter ratio differs from the part's.", font=_font(15), fill=(110, 110, 110))
    sheet.save(OUT)
    print(f"  -> {OUT.relative_to(HERE)}  ({sheet.width}x{sheet.height}, {n_bad} mismatches left)")


if __name__ == "__main__":
    main()
