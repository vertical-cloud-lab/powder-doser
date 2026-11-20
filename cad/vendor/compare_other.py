"""Our model of each purchased part (not McMaster, not Actuonix) beside the vendor's own drawing, photo or spec table,
with the key dimensions (vendor vs model) listed, so a reader can check them at a glance: compare/<key>.png.

    xvfb-run -a nice -n 10 /tmp/venv/bin/python cad/vendor/compare_other.py [key ...]

The model is rendered offscreen (pyvista) from the design's own builder (parts.py, current params), with rulers on
its bounding box. The vendor panel is a crop of the screenshot / PDF page that fetch_other.py saved in files/<vendor>/
(git-ignored); if it is missing the panel says so. AUDIT_other.md has the same numbers and their sources.
"""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

import numpy as np

VENDOR = Path(__file__).resolve().parent
CAD = VENDOR.parent
FILES = VENDOR / "files"
OUT = VENDOR / "compare"

DESIGNS = {"pat": CAD / "paternoster", "v2": CAD / "chain-carousel-v2"}
_MODS: dict[str, object] = {}


def design(name: str):
    """Import a design's parts.py (each design has its own params.py, so swap them in and out of sys.modules)."""
    if name not in _MODS:
        for m in ("params", "parts", "step_io"):
            sys.modules.pop(m, None)
        sys.path.insert(0, str(DESIGNS[name]))
        try:
            _MODS[name] = importlib.import_module("parts")
        finally:
            sys.path.pop(0)
            for m in ("params", "parts", "step_io"):
                sys.modules.pop(m, None)
    return _MODS[name]


def render(wp, size=(640, 560), view=(1.0, -1.3, 0.9), color=(0.72, 0.74, 0.78)):
    import cadquery as cq
    import pyvista as pv

    shapes = [v for v in (wp.vals() if hasattr(wp, "vals") else [wp]) if isinstance(v, cq.Shape)]
    comp = cq.Compound.makeCompound(shapes)
    verts, tris = comp.tessellate(0.02, 0.2)
    pts = np.array([(v.x, v.y, v.z) for v in verts])
    faces = np.hstack([[3, *t] for t in tris]).astype(np.int64)
    mesh = pv.PolyData(pts, faces)
    p = pv.Plotter(off_screen=True, window_size=size)
    p.set_background("white")
    p.add_mesh(mesh, color=color, smooth_shading=True, specular=0.3)
    p.add_mesh(mesh.extract_feature_edges(35), color="black", line_width=1)
    bb = comp.BoundingBox()
    x0, x1, y0, y1, z0, z1 = bb.xmin, bb.xmax, bb.ymin, bb.ymax, bb.zmin, bb.zmax
    off = 0.08 * max(bb.xlen, bb.ylen, bb.zlen)
    for a, b, t in (((x0, y0 - off, z0), (x1, y0 - off, z0), f"x {bb.xlen:.2f}"),
                    ((x1 + off, y0, z0), (x1 + off, y1, z0), f"y {bb.ylen:.2f}"),
                    ((x0 - off, y0, z0), (x0 - off, y0, z1), f"z {bb.zlen:.2f}")):
        try:
            p.add_ruler(a, b, title=t, number_labels=2, font_size_factor=0.8, label_size_factor=0.6)
        except Exception:  # noqa: BLE001  (older pyvista)
            pass
    p.camera_position = [tuple(np.array(view) * 3 * max(bb.xlen, bb.ylen, bb.zlen) + np.array(bb.center.toTuple())),
                         bb.center.toTuple(), (0, 0, 1)]
    p.reset_camera()
    p.camera.zoom(1.1)
    img = p.screenshot(return_img=True)
    p.close()
    return img, bb


def vendor_image(src):
    """src = (vendor, file, crop box or None, pdf page) -> PIL image or None."""
    from PIL import Image

    if src is None:
        return None
    vendor, name, box, page = (list(src) + [None, None])[:4]
    f = FILES / vendor / name
    if not f.exists():
        return None
    if f.suffix.lower() == ".pdf":
        import pypdfium2 as pdfium
        im = pdfium.PdfDocument(str(f))[page or 0].render(scale=2.5).to_pil()
        if box:  # box in fractions of the page
            w, h = im.size
            im = im.crop((int(box[0] * w), int(box[1] * h), int(box[2] * w), int(box[3] * h)))
        return im
    im = Image.open(f).convert("RGB")
    return im.crop(box) if box else im


def figure(item: dict) -> Path:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    mod = design(item["design"])
    wp = getattr(mod, item["builder"])(*item.get("args", ()))
    img, bb = render(wp, view=item.get("view", (1.0, -1.3, 0.9)))
    vim = vendor_image(item.get("vendor_img"))
    fig = plt.figure(figsize=(16, 6.2), dpi=110)
    gs = fig.add_gridspec(1, 3, width_ratios=[1.0, 1.15, 1.0])
    ax0, ax1, ax2 = fig.add_subplot(gs[0]), fig.add_subplot(gs[1]), fig.add_subplot(gs[2])
    ax0.imshow(img)
    ax0.set_title(f"our model: {item['design']}/parts.py:{item['builder']}()", fontsize=10)
    ax1.set_title(f"vendor: {item['source']}", fontsize=10)
    if vim is not None:
        ax1.imshow(vim)
    else:
        ax1.text(0.5, 0.5, "vendor file not on disk\n(run fetch_other.py)", ha="center", va="center", fontsize=12)
    for a in (ax0, ax1, ax2):
        a.set_axis_off()
    rows = [("dimension", "vendor", "model")] + [tuple(r) for r in item["rows"]]
    rows.append(("model bounding box", "", f"{bb.xlen:.2f} x {bb.ylen:.2f} x {bb.zlen:.2f}"))
    y = 0.97
    for i, (a, b, c) in enumerate(rows):
        w = "bold" if i == 0 else "normal"
        ax2.text(0.0, y, a, fontsize=9, weight=w, va="top", wrap=True)
        ax2.text(0.50, y, b, fontsize=9, weight=w, va="top")
        ax2.text(0.76, y, c, fontsize=9, weight=w, va="top")
        y -= 0.062 if len(a) < 34 else 0.09
    ax2.text(0.0, max(y - 0.02, 0.02), "verdict: " + item["verdict"], fontsize=10, weight="bold", va="top",
             color=("#2a7a2a" if item["verdict"].startswith(("match", "fixed")) else "#a05a00"))
    fig.suptitle(item["title"], fontsize=13, weight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    OUT.mkdir(exist_ok=True)
    out = OUT / f"{item['key']}.png"
    fig.savefig(out)
    plt.close(fig)
    return out


# key dims are mm; vendor values as the vendor states them (in, converted). "was" = the model before this audit.
ITEMS: list[dict] = [
    dict(key="chain_rc35", design="v2", builder="chain_outer_link", title="ANSI #35 roller chain: Nitro RC35-1R-10FT (outer link)",
         source="nitrochain.com/35-roller-chain-10ft (dimension table)", vendor_img=("nitro", "chain_RC35.png", (110, 1190, 1250, 1900)),
         rows=[("pitch P", "3/8 in (9.525)", "9.525"), ("inner width b1", "3/16 in (4.76)", "4.78"),
               ("bushing d1 (rollerless)", "0.200 in (5.08)", "5.08"), ("pin d2", "0.141 in (3.58)", "3.58 (v2 was 5.0)"),
               ("plate height h2", "0.346 in (8.79)", "8.79 (was 9.0)"), ("plate T", "0.050 in (1.27)", "1.27"),
               ("overall width L (pins)", "0.488 in (12.40)", "12.40 (was 10.81/11.81)")],
         verdict="fixed (plate height, pin length; v2 pin diameter)"),
    dict(key="a1_cl35", design="v2", builder="chain_a1_link", title="#35 A-1 attachment connecting link: Nitro CL35-A1 (v2)",
         source="nitrochain.com/35-a1-standard-attachment-connecting-link", vendor_img=("nitro", "a1_CL35-A1.png", (110, 1060, 1260, 1560)),
         rows=[("tab width G", "0.312 in (7.92)", "7.9"), ("centreline to tab end W", "0.562 in (14.27)", "14.3"),
               ("width to hole F", "0.375 in (9.525)", "9.525"), ("hole d4", "0.133 in (3.38)", "3.38"),
               ("attachment height h4", "0.250 in (6.35)", "6.35"), ("plate T", "0.050 in (1.27)", "1.27")],
         verdict="match"),
    dict(key="sprocket_35bs32", design="pat", builder="sprocket_32", title="Sprocket 35BS32-5/8 (Surplus Center 601139): Martin's table",
         source="Martin 35BS32 5/8 via tristate-bearing.com", vendor_img=("martin", "sprocket_35BS32-5-8.png", (100, 230, 1270, 1100)),
         view=(0.6, -1.4, 0.8),
         rows=[("outside diameter", "4.032 in (102.4)", "102.4"), ("pitch diameter", "3.826 in (97.18)", "97.13"),
               ("hub diameter", "2 in (50.8)", "50.8"), ("length thru bore", "7/8 in (22.2)", "22.2"),
               ("bore, keyway", "5/8, 3/16 x 3/32", "15.875, 4.76 x 2.38"), ("set screws", "2 (1/4-20)", "2 (paternoster was 1)")],
         verdict="fixed (second set screw, paternoster)"),
    dict(key="sprocket_35bs15h", design="v2", builder="sprocket_15_shaft", title="Sprocket 35BS15H-5/8 (Surplus Center 601078): Tritan's listing",
         source="Tritan 35BS15H X 5/8 via hvhindustrial.com", vendor_img=("tritan", "sprocket_35BS15H-5-8_hvh.png", (0, 150, 1351, 1100)),
         rows=[("outside diameter", "1.99 in (50.5)", "50.5"), ("pitch diameter", "1.804 in (45.8)", "45.81"),
               ("hub diameter", "1-3/8 in (34.9)", "34.1 (BoM: 1-11/32)"), ("length thru bore", "3/4 in (19.05)", "19.05"),
               ("hub projection", "0.582 in (14.8)", "14.8")],
         verdict="match except the hub (Surplus Center's own page unreadable)"),
    dict(key="flange_sbsfl202", design="v2", builder="flange_bearing", title="2-bolt pressed-steel flange bearing SBSFL202-10 (= SBPFL202-10)",
         source="usabearingsandbelts.com SBPFL202-10 table + drawing", vendor_img=("flange", "flange_SBPFL202-10_usab.png", (150, 820, 790, 1245)),
         rows=[("length a", "3-3/16 in (81.0)", "81.0 (was 81.5)"), ("bolt centres e", "2-1/2 in (63.5)", "63.5"),
               ("width B", "2-5/16 in (58.7)", "58.7"), ("sheet t (x2 halves)", "0.079 in (2.0)", "lobes 4.0 (was 3.0)"),
               ("dome to dome b", "5/8 in (15.9)", "15.9 (was 19.2)"), ("inner ring L", "0.8661 in (22.0)", "22.0: 16.05 out / 5.95 in (was 12.6 / 9.6)"),
               ("bolt hole S", "9/32 in (7.1)", "7.15")],
         verdict="fixed (ring position read off the drawing)"),
    dict(key="electromagnet_3872", design="v2", builder="dock_magnet", title="Holding electromagnet P20/15: Adafruit 3872",
         source="Adafruit 3872 diagram (product-files/3872)", vendor_img=("adafruit", "3872_diagram.png", None), view=(0.8, -1.2, -0.9),
         rows=[("diameter", "20", "20"), ("height", "15", "15"), ("centre pole", "8", "8 (was a ring mark)"),
               ("mounting", "M4 x 10 in the back", "M4 x 10 (added)")],
         verdict="fixed (face, thread)"),
    dict(key="pinion_ss1_20a", design="v2", builder="pinion_20t", title="Steel pinion KHK SS1-20A (hub faced off by design)",
         source="KHK 2D sales drawing (khkgears.co.jp) + catalog", vendor_img=("khk", "SS1-20A_2D_sales_drawing.tab.png", (0, 0, 1070, 745)),
         rows=[("module, teeth, angle", "1, 20, 20 deg", "1, 20, 20 deg involute"), ("outside diameter", "22", "22 (was 21.6 20-gon)"),
               ("pitch diameter", "20", "20"), ("tooth depth", "2.25", "2.25"), ("face width", "10", "10"),
               ("bore", "5 H8", "5"), ("hub", "16 x 10 + M4", "faced off")],
         verdict="fixed (tooth form)"),
    dict(key="nema11_11hs18", design="v2", builder="nema11_envelope", title="NEMA 11 11HS18-0674S: StepperOnline",
         source="StepperOnline product page (PDF 403, STEP needs login)", vendor_img=("stepperonline", "11HS18-0674S_Full_Datasheet.tab.png", (0, 180, 1366, 790)),
         rows=[("frame", "28 x 28", "28 x 28"), ("body length", "45", "45"), ("shaft", "5 x 20", "5 x 20"),
               ("D-cut length", "15", "15 (added)"), ("boss", "(no drawing)", "22 x 1.5")],
         verdict="fixed (D-cut); boss unverified"),
    dict(key="nema34_34hs59", design="v2", builder="nema34", title="NEMA 34 34HS59-6004D-E1000: StepperOnline's STEP in v2 (lead cut at the body)",
         source="StepperOnline product page (drawing PDF 403)", vendor_img=("stepperonline", "nema34_34HS59-6004D-E1000.png", (0, 150, 1351, 1000)),
         view=(1.2, -1.0, 0.7),
         rows=[("frame", "86 x 86", "86 x 86"), ("shaft", "14 x 37, 25 keyed", "14 x 36.5"), ("pilot", "(no drawing)", "73 x 2.0"),
               ("bolt square, holes", "(no drawing)", "69.6, 4 x 6.5"), ("body + encoder", "175 (page)", "169 (STEP)")],
         verdict="STEP used; body length unresolved"),
    dict(key="extrusion_8020_2020", design="pat", builder="extrusion_2020", args=(30.0,), title="80/20 20-2020 profile (paternoster)",
         source="8020.net/20-2020 profile drawing", vendor_img=("8020", "extrusion_20-2020.image1.jpg", None), view=(0.04, -0.75, 1.0),
         rows=[("square", "20.00", "20.00"), ("slot opening", "5.26", "5.26 (was 6.2)"), ("lips", "1.50", "1.50 (was 1.8)"),
               ("slot under the lips", "11.99", "11.99 (was 11.0)"), ("face to core", "6.34", "6.34 (was 6.1)"),
               ("centre bore", "4.19", "4.19"), ("area", "1.591 cm2", "1.69 cm2 (was 5 loose solids)")],
         verdict="fixed"),
    dict(key="bracket_8020_14059", design="pat", builder="corner_bracket", title="80/20 14059 corner bracket (paternoster)",
         source="8020.net/14059 drawing + table", vendor_img=("8020", "bracket_14059.image1.png", None), view=(1.0, -1.4, 0.8),
         rows=[("legs A, B", "18, 18", "18, 18 (was 20)"), ("width K", "18", "18"), ("leg thickness F", "3.0", "3.0 (was 3.5)"),
               ("slots J x G", "5.3 x 7.0", "5.3 x 7.0 (was 5.5 holes)"), ("slot from corner D", "10.5", "10.5 (was 12)")],
         verdict="fixed"),
    dict(key="foot_lf020a", design="v2", builder="leveling_foot", title="Leveling foot: TNUTZ LF-020-A",
         source="tnutz.com/product/lf-020-a (text + photo)", vendor_img=("tnutz", "foot_LF-020-A.png", (80, 220, 450, 580)),
         rows=[("stud", "M6 x 40", "6.0 (was 5.0), cut to 21"), ("base", "dia 20 nylon", "dia 20 (was 30)"),
               ("ball end", "dia 10", "dia 10"), ("base height", "(photo)", "9")],
         verdict="fixed (base height from the photo)"),
    dict(key="loadcell_tal221", design="v2", builder="load_cell", title="Load cell SparkFun SEN-14727 (TAL221, 100 g)",
         source="TAL221 datasheet (cdn.sparkfun.com)", vendor_img=("sparkfun", "TAL221.pdf", (0.05, 0.22, 0.75, 0.52), 0),
         rows=[("bar", "47 x 12 x 6", "47 x 12 x 6 (was 80 x 12.7 x 12.7)"), ("fixed-end holes", "2 x M3, 6 apart", "2 x M3"),
               ("free-end holes", "2 x dia 3.2", "2 x dia 3.2"), ("hole spacing along", "40", "40"),
               ("spacers (ours)", "-", "2 x 3.35 (stack 12.7)")],
         verdict="fixed (moves the cup/post interface, see AUDIT)"),
    dict(key="solenoid_412", design="v2", builder="solenoid_412", title="Push-pull solenoid: Adafruit 412 (TAU0730TM)",
         source="Adafruit 412 drawing (product-files/412)", vendor_img=("adafruit", "412_C514-B_diagram.pdf", (0.04, 0.08, 0.66, 0.92), 0),
         rows=[("frame", "17 x 14 x 29.7", "17 x 14 x 29.7 (was 15 x 12 x 32)"), ("plunger", "dia 5", "dia 5 (was 4.5)"),
               ("push end out", "15.4 on, 20.3 off", "8 (kept, AUDIT)"), ("stroke", "4.9", "-")],
         verdict="fixed (frame, plunger dia)"),
    dict(key="hall_us5881", design="v2", builder="hall_switch", title="Hall switch US5881LUA (TO-92 UA): Adafruit 158",
         source="Melexis US5881 datasheet, UA package", vendor_img=("adafruit", "US5881_rev007.pdf", (0.05, 0.05, 0.95, 0.6), 9),
         rows=[("body width", "4.08", "4.08 (was 4.0)"), ("body height", "3.00", "3.00"), ("thickness", "1.51", "1.51 (was 1.5)"),
               ("lead pitch", "1.27", "1.27")],
         verdict="fixed"),
    dict(key="magnet_d42", design="v2", builder="magnet", title="Disc magnet 1/4 x 1/8 in N52: K&J D42-N52",
         source="kjmagnetics.com product page", vendor_img=("kj", "magnet_D42-N52.png", (0, 0, 1351, 900)),
         rows=[("diameter", "1/4 in (6.35)", "6.35"), ("thickness", "1/8 in (3.17)", "3.18")], verdict="match"),
    dict(key="bearing_6202", design="pat", builder="bearing_6202", title="Deep-groove ball bearing 6202-2RS (top idlers)",
         source="SKF 6202-2RSH product page", vendor_img=("skf", "bearing_6202-2RSH.png", (0, 0, 1351, 1100)),
         rows=[("bore", "15", "15"), ("outside diameter", "35", "35"), ("width", "11", "11")], verdict="match"),
    dict(key="vial_986546", design="v2", builder="vial", title="20 mL scintillation vial: Wheaton 986546",
         source="pfstar.com (DWK listing)", vendor_img=("pfstar", "vial_986546.png", (0, 0, 1351, 1100)),
         rows=[("OD x H", "28 x 61 (cap on)", "28 x 61 (cap off)")], verdict="estimated (bare-glass height not published)"),
]


def main(keys: list[str]) -> None:
    for it in ITEMS:
        if keys and it["key"] not in keys:
            continue
        try:
            print("wrote", figure(it).relative_to(CAD.parent), flush=True)
        except Exception as e:  # noqa: BLE001
            print(f"{it['key']}: FAILED {type(e).__name__}: {e}", flush=True)


if __name__ == "__main__":
    main(sys.argv[1:])
