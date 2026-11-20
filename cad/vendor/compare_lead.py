"""The Actuonix P16 and the McMaster parts beside their vendor's own data, as compare_other.py does for the rest:

    xvfb-run -a nice -n 10 /tmp/venv/bin/python cad/vendor/compare_lead.py

* compare/actuonix_p16.png: our station's P16 (Actuonix's STEP) on its base clevis with the U-yoke on its rod end, a
  section through the yoke's socket, Actuonix's datasheet drawing, and the dimensions that changed.
* compare/mcmaster_parts.png: every McMaster STEP the carousels use, as placed in our builders' frames, with the
  part number, McMaster's description, price and the spec values the fit depends on (mcmaster_specs.json).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

VENDOR = Path(__file__).resolve().parent
sys.path.insert(0, str(VENDOR))
from compare_other import FILES, OUT, design, render  # noqa: E402


def _rot_drawing():
    """Actuonix's dimension drawing (datasheet p. 3, drawn landscape on a portrait page), turned upright."""
    import pypdfium2 as pdfium
    f = FILES / "actuonix" / "ActuonixP16Datasheet.pdf"
    if not f.exists():
        return None
    im = pdfium.PdfDocument(str(f))[2].render(scale=2.2).to_pil()
    w, h = im.size
    return im.crop((int(0.02 * w), int(0.02 * h), int(0.84 * w), int(0.985 * h))).rotate(-90, expand=True)


def p16_figure() -> Path:
    import cadquery as cq
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    m = design("pat")
    P = sys.modules.get("params")  # noqa: F841  (design() swapped params out again)
    body, rod = m.actuator_p16()
    ret = 197.4
    ufork = 60.0
    Y = cq.Location(cq.Vector(0, 0, ret + ufork))
    parts = [body.val(), rod.val(), m.clevis_bracket().val(), m.clevis_shoulder_screw().val().moved(
        cq.Location(cq.Vector(0, -7.9, 0), cq.Vector(1, 0, 0), 90)),
        m.uyoke_base().val().moved(Y), m.yoke_pin().val().moved(Y * cq.Location(cq.Vector(0, 0, -ufork)))]
    whole = cq.Workplane("XY").add(cq.Compound.makeCompound(parts))
    img0, bb = render(whole, size=(520, 760), view=(1.0, -1.6, 0.5))
    # section through the socket: the rod end's 9 x 6 tab in the 9.3 x 6.3 slot, collar in the counterbore, dowel through
    box = cq.Solid.makeBox(60, 30, 40, cq.Vector(-30, 0.0, ret - 20))
    sec = [s.cut(box) for s in (rod.val(), m.uyoke_base().val().moved(Y), m.yoke_pin().val().moved(Y * cq.Location(cq.Vector(0, 0, -ufork))))]
    sec = [s.intersect(cq.Solid.makeBox(60, 60, 40, cq.Vector(-30, -30, ret - 20))) for s in sec]
    img1, _ = render(cq.Workplane("XY").add(cq.Compound.makeCompound(sec)), size=(520, 520), view=(0.12, 1.0, 0.18))
    dwg = _rot_drawing()

    fig = plt.figure(figsize=(19, 7.2), dpi=105)
    gs = fig.add_gridspec(1, 4, width_ratios=[0.75, 0.85, 1.45, 1.25])
    axs = [fig.add_subplot(gs[i]) for i in range(4)]
    for a in axs:
        a.set_axis_off()
    axs[0].imshow(img0)
    axs[0].set_title("our station: Actuonix's STEP on the new\nbase clevis, U-yoke on its rod end", fontsize=10)
    axs[1].imshow(img1)
    axs[1].set_title("section through the yoke's socket:\n9 x 6 tab in a 9.3 x 6.3 slot, 4 mm dowel", fontsize=10)
    if dwg is not None:
        axs[2].imshow(dwg)
    axs[2].set_title("Actuonix P16 datasheet (rev B), dimension drawing", fontsize=10)
    rows = [("dimension", "Actuonix", "before", "now"),
            ("closed hole to hole", "197 (stroke + 47)", "197.4", "197.4 (their STEP)"),
            ("housing", "36 x 20 x 70", "36 x 20 x 79", "their STEP"),
            ("rear clevis", "8 mm tab, dia 4.25", "inside the block", "their STEP"),
            ("base clevis cheeks", "(bracket 11.5 over)", "21 mm apart", "8.4 apart, R4"),
            ("rod", "dia 9 (8.94)", "dia 9", "their STEP"),
            ("rod end", "9 x 6 tab, dia 4.25", "9 x 9 plug", "their STEP"),
            ("yoke socket", "-", "9.3 x 9.3 square", "9.3 x 6.3 slot"),
            ("yoke cross pin", "fits M4 / #8", "M4 x 25 bolt*", "4 x 38 dowel"),
            ("base pin", "-", "4 x 30 shoulder", "4 x 16 (90265A123)"),
            ("max side load (150)", "10 N", "10 N", "10 N"),
            ("duty cycle", "20 %", "-", "noted in BoM")]
    y = 0.98
    for i, r in enumerate(rows):
        w = "bold" if i == 0 else "normal"
        for x, t in zip((0.0, 0.30, 0.56, 0.80), r):
            axs[3].text(x, y, t, fontsize=8.0, weight=w, va="top")
        y -= 0.066
    axs[3].text(0.0, y - 0.01, "* no room for its head or nut: the yoke's steel\n  arms sit flat on both ends of the hole",
                fontsize=8.6, va="top")
    axs[3].text(0.0, y - 0.13, "verdict: fixed (rod end and rear clevis)", fontsize=10, weight="bold", va="top", color="#2a7a2a")
    fig.suptitle("Actuonix P16-150-22-12-P: datasheet and Actuonix's STEP vs our station", fontsize=13, weight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    OUT.mkdir(exist_ok=True)
    out = OUT / "actuonix_p16.png"
    fig.savefig(out)
    plt.close(fig)
    return out


GRID = [  # (part number, builder in the paternoster (pat) or v2 parts.py, args, spec keys worth showing)
    ("7321K31", "pat", "chain_sa1_link", (), ("Mounting Hole Diameter", "Length", "Width", "Pitch")),
    ("90265A121", "pat", "shoulder_screw", (), ("Shoulder Diameter", "Shoulder Length", "Thread Size", "Thread Length")),
    ("90265A123", "pat", "clevis_shoulder_screw", (), ("Shoulder Diameter", "Shoulder Length", "Thread Size", "Thread Length")),
    ("6659K65", "pat", "sleeve_bearing", (), ("ID", "OD", "Length", "Flange OD", "Flange Thickness")),
    ("95630A630", "pat", "thrust_washer", (), ("ID", "OD", "Thickness")),
    ("93625A100", "pat", "locknut", (3.0,), ("Thread Size", "Width", "Height")),
    ("93625A200", "pat", "locknut", (5.0,), ("Thread Size", "Width", "Height")),
    ("95615A120", "pat", "locknut", (6.35,), ("Thread Size", "Width", "Height")),
    ("94459A774", "pat", "heat_set_insert_m5", (), ("Thread Size", "Installed Length", "Hole Diameter", "Length")),
    ("92545A179", "pat", "thumb_screw", (), ("Thread Size", "Length", "Head Diameter", "Head Height")),
    ("91595A128", "pat", "yoke_pin", (), ("Diameter", "Length", "Hardness")),
    ("91595A150", "pat", "loc_pin", (), ("Diameter", "Length", "Hardness")),
    ("92095A183", "v2", "shcs", (3, 12, "button"), ("Thread Size", "Length", "Head Diameter")),
    ("92095A181", "v2", "shcs", (3, 8, "button"), ("Thread Size", "Length", "Head Diameter")),
    ("92095A210", "v2", "shcs", (5, 12, "button"), ("Thread Size", "Length", "Head Diameter")),
    ("92125A126", "v2", "shcs", (3, 6, "flat"), ("Thread Size", "Length", "Head Diameter")),
    ("91292A124", "v2", "shcs", (5, 10, "socket"), ("Thread Size", "Length", "Head Diameter")),
    ("91292A126", "v2", "shcs", (5, 16, "socket"), ("Thread Size", "Length", "Head Diameter")),
    ("91292A129", "v2", "shcs", (5, 25, "socket"), ("Thread Size", "Length", "Head Diameter")),
]


def mcmaster_sheet() -> Path:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    specs = json.loads((VENDOR / "mcmaster_specs.json").read_text())
    n = len(GRID)
    cols = 5
    rows = (n + cols - 1) // cols
    fig = plt.figure(figsize=(cols * 3.9, rows * 3.9), dpi=95)
    for i, (pn, d, fn, args, keys) in enumerate(GRID):
        ax = fig.add_subplot(rows, cols, i + 1)
        ax.set_axis_off()
        try:
            wp = getattr(design(d), fn)(*args)
            img, _ = render(wp, size=(360, 300), view=(1.0, -1.3, 0.9))
            ax.imshow(img)
        except Exception as e:  # noqa: BLE001
            ax.text(0.5, 0.6, f"render failed: {e!r}"[:60], ha="center", fontsize=7)
        r = specs.get(pn, {})
        t = (r.get("title", "") or "").split(" / ")
        name = t[1] if len(t) > 1 else t[0]
        sp = r.get("specs", {})
        vals = "; ".join(f"{k} {sp[k]}" for k in keys if k in sp)
        cad = "McMaster STEP" if "step" in r else "STEP not fetched"
        ax.set_title(f"{pn}  {r.get('price', '')}\n{name[:44]}", fontsize=8.5, weight="bold")
        ax.text(0.5, -0.02, f"{vals[:120]}\n{cad}, read {r.get('read', '?')}", transform=ax.transAxes, ha="center", va="top",
                fontsize=7.2, wrap=True)
    fig.suptitle("McMaster-Carr parts in both carousels, from McMaster's own STEP files placed in our builders' frames "
                 "(pages read logged out through the doser Pi)", fontsize=12, weight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    out = OUT / "mcmaster_parts.png"
    fig.savefig(out)
    plt.close(fig)
    return out


if __name__ == "__main__":
    print(p16_figure())
    if '--p16' not in sys.argv:
        print(mcmaster_sheet())
