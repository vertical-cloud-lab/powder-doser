#!/usr/bin/env python3
"""Render & slice the eight powder-dosing alternatives (A–H).

For each concept SCAD under ``cad/alternatives/`` this script writes,
next to the source:

  ``<letter>-<slug>.stl``                  binary STL (manifold checked)
  ``<letter>-<slug>-iso.png``              opaque iso preview
  ``<letter>-<slug>-cutaway.png``          half-cutaway cross section
  ``<letter>-<slug>-spin.gif``             36-frame transparent rotating GIF

It also slices each STL with PrusaSlicer for the Original Prusa MK3S+
profile (per the toolchain agreed in PR #7 §6) and dumps the slicer's
single-line summary so print issues surface here, not at the printer.

Finally it composes:

  ``cad/alternatives/composite-spin.gif``     tiled 4×2 spinning preview
  ``cad/alternatives/composite-cutaway.png``  tiled 4×2 cross sections

Usage::

    sudo apt-get install -y openscad admesh prusa-slicer xvfb
    pip install pillow
    python scripts/render_alternatives.py

Mirrors the SCAD → STL → admesh → iso/cutaway PNG → slice flow used by
PR #16's ``cad/auger/render_print.sh`` and PR #5's render script.
"""
from __future__ import annotations

import math
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

REPO = Path(__file__).resolve().parents[1]
ALT_DIR = REPO / "cad" / "alternatives"

CONCEPTS = [
    ("A", "tap-sieve",         "A_tap_sieve.scad"),
    ("B", "pez-strip",         "B_pez_strip.scad"),
    ("C", "capillary-wiper",   "C_capillary_wiper.scad"),
    ("D", "brush-comb",        "D_brush_comb.scad"),
    ("E", "shaker",            "E_shaker.scad"),
    ("F", "passive-auger",     "F_passive_auger.scad"),
    ("G", "erm-sieve",         "G_erm_sieve.scad"),
    ("H", "solenoid-sieve",    "H_solenoid_sieve.scad"),
]

# OpenSCAD's --colorscheme=Tomorrow yields a near-white background that
# Pillow can key out to alpha so the spin GIF is "transparent".
BG_RGB = (255, 255, 255)
BG_TOL = 8

PNG_SIZE = (560, 560)
SPIN_FRAMES = 36
SPIN_FPS = 18


def have(cmd: str) -> bool:
    return shutil.which(cmd) is not None


def run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    if not os.environ.get("DISPLAY") and have("xvfb-run"):
        if cmd[0] in {"openscad"}:
            cmd = ["xvfb-run", "-a"] + cmd
    return subprocess.run(cmd, check=True, **kw)


def render_stl(scad: Path, stl: Path) -> None:
    run(["openscad", "-o", str(stl), "--export-format=binstl", str(scad)])


def admesh_check(stl: Path) -> str:
    if not have("admesh"):
        return "admesh: not installed (skipped)"
    res = subprocess.run(
        ["admesh", "-c", str(stl)],
        capture_output=True, text=True, check=False,
    )
    out = (res.stdout + res.stderr)
    # one-line summary: parts, edges-with-bad-orientation, degenerate
    keys = {"Number of parts": None,
            "Backwards edges": None,
            "Degenerate facets": None,
            "Edges fixed": None,
            "Facets removed": None}
    for line in out.splitlines():
        for k in keys:
            if line.strip().startswith(k):
                # "Key  : N"
                try:
                    keys[k] = int(line.split(":", 1)[1].strip())
                except Exception:
                    pass
    return ("parts={Number of parts}, bad_edges={Backwards edges}, "
            "deg={Degenerate facets}, fix_edges={Edges fixed}, "
            "facets_removed={Facets removed}").format(**keys)


def render_iso(scad: Path, png: Path, *, camera: str | None = None) -> None:
    cam = camera or "0,0,0,55,0,25,140"
    run([
        "openscad", "-o", str(png),
        f"--imgsize={PNG_SIZE[0]},{PNG_SIZE[1]}",
        f"--camera={cam}",
        "--colorscheme=Tomorrow",
        str(scad),
    ])


def render_cutaway(scad: Path, png: Path) -> None:
    """Half-cutaway: subtract a +y half-space from the model."""
    body = scad.read_text(encoding="utf-8")
    cut = (
        body
        + "\n\n// ---- pipeline-injected half-cutaway ----\n"
        + "module __pipeline_cutaway() {\n"
        + "  translate([-200, 0, -200]) cube([400, 400, 600]);\n"
        + "}\n"
    )
    # Wrap last call in a difference() — instead of editing AST we just
    # render a fresh wrapper SCAD that imports the original via include.
    wrapper = (
        f"include <{scad.name}>;\n"
        "// the include above already drew the body; we now subtract a\n"
        "// half-space by rendering a difference() of two copies. This\n"
        "// only works because OpenSCAD treats top-level statements as\n"
        "// additive, so we instead render via a one-shot model:\n"
    )
    # Simpler/correct: render with a separate wrapper that DOES use
    # difference() against `import("body.stl")`. We have the STL already,
    # so import + cutaway is the cleanest path:
    stl_path = png.with_suffix(".stl")
    if not stl_path.exists():
        # caller hasn't built STL yet; do it here
        render_stl(scad, stl_path)
    with tempfile.NamedTemporaryFile(
        "w", suffix=".scad", delete=False, dir=str(scad.parent)
    ) as fh:
        fh.write(
            "$fa = 2; $fs = 0.4;\n"
            f'difference() {{ import("{stl_path.name}"); '
            "translate([-200,0,-200]) cube([400,400,600]); }\n"
        )
        wrap = Path(fh.name)
    try:
        run([
            "openscad", "-o", str(png),
            f"--imgsize={PNG_SIZE[0]},{PNG_SIZE[1]}",
            "--camera=0,0,0,55,0,25,140",
            "--colorscheme=Tomorrow",
            str(wrap),
        ])
    finally:
        wrap.unlink(missing_ok=True)
    _ = wrapper, body, cut  # unused (kept for clarity)


def to_transparent(rgb: Image.Image) -> Image.Image:
    """Key out the near-white OpenSCAD background to alpha."""
    img = rgb.convert("RGBA")
    px = img.load()
    w, h = img.size
    for y in range(h):
        for x in range(w):
            r, g, b, _ = px[x, y]
            if (abs(r - BG_RGB[0]) < BG_TOL
                    and abs(g - BG_RGB[1]) < BG_TOL
                    and abs(b - BG_RGB[2]) < BG_TOL):
                px[x, y] = (255, 255, 255, 0)
    return img


def render_spin(scad: Path, gif: Path) -> None:
    """36-frame turntable GIF with transparency."""
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        frames: list[Image.Image] = []
        for i in range(SPIN_FRAMES):
            az = 360.0 * i / SPIN_FRAMES
            png = tdp / f"f{i:03d}.png"
            cam = f"0,0,0,55,0,{az:.2f},140"
            run([
                "openscad", "-o", str(png),
                f"--imgsize={PNG_SIZE[0]},{PNG_SIZE[1]}",
                f"--camera={cam}",
                "--colorscheme=Tomorrow",
                str(scad),
            ])
            with Image.open(png) as f:
                rgba = to_transparent(f.convert("RGB").copy())
            # palette mode required for animated GIF; use ADAPTIVE w/
            # transparency-preserving conversion
            pal = rgba.convert("P", palette=Image.ADAPTIVE)
            frames.append(pal)
        frames[0].save(
            gif, save_all=True, append_images=frames[1:],
            duration=int(1000 / SPIN_FPS), loop=0,
            disposal=2, transparency=0, optimize=True,
        )


def slice_stl(stl: Path, gcode: Path) -> str:
    """Slice with PrusaSlicer (MK3S+ profile, 0.2 mm, PETG, 3 perim)."""
    if not have("prusa-slicer"):
        return "prusa-slicer: not installed (skipped)"
    cmd = [
        "prusa-slicer", "--export-gcode",
        "--nozzle-diameter", "0.4",
        "--filament-diameter", "1.75",
        "--filament-type", "PETG",
        "--first-layer-height", "0.2",
        "--layer-height", "0.2",
        "--perimeters", "3",
        "--top-solid-layers", "5",
        "--bottom-solid-layers", "4",
        "--fill-density", "30%",
        "--fill-pattern", "gyroid",
        "--brim-width", "4",
        "--support-material",
        "--output", str(gcode),
        str(stl),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=False)
    out = (res.stdout + res.stderr).splitlines()
    # Surface PrusaSlicer's "print stability" warnings — they catch
    # exactly the print issues the user asked us to flag (floating
    # bridges, loose extrusions, etc.).
    warnings: list[str] = []
    for i, line in enumerate(out):
        if "print warning" in line.lower() or "print stability" in line.lower():
            tail = " / ".join(s.strip() for s in out[i:i + 4]
                              if s.strip())
            warnings.append(tail)
    warn_blob = ""
    if warnings:
        warn_blob = " | warn: " + " | warn: ".join(warnings)
    if res.returncode != 0:
        return f"prusa-slicer: FAILED ({res.returncode})" + warn_blob
    if not gcode.exists():
        return "prusa-slicer: no g-code emitted" + warn_blob
    return f"prusa-slicer: ok ({gcode.stat().st_size} B)" + warn_blob


def composite(images: list[Image.Image], cols: int, tile: tuple[int, int],
              transparent: bool) -> Image.Image:
    rows = math.ceil(len(images) / cols)
    mode = "RGBA" if transparent else "RGB"
    bg = (0, 0, 0, 0) if transparent else (255, 255, 255)
    canvas = Image.new(mode, (cols * tile[0], rows * tile[1]), bg)
    for i, im in enumerate(images):
        r, c = divmod(i, cols)
        thumb = im.resize(tile, Image.LANCZOS)
        if transparent and thumb.mode != "RGBA":
            thumb = thumb.convert("RGBA")
        canvas.paste(thumb, (c * tile[0], r * tile[1]),
                     thumb if transparent else None)
    return canvas


def main() -> int:
    if not have("openscad"):
        sys.stderr.write("openscad missing\n"); return 1

    iso_imgs: list[Image.Image] = []
    cut_imgs: list[Image.Image] = []
    spin_first_frames: list[list[Image.Image]] = []
    report: list[str] = []

    for letter, slug, scad_name in CONCEPTS:
        scad = ALT_DIR / scad_name
        base = ALT_DIR / f"{letter}-{slug}"
        stl = base.with_suffix(".stl")
        iso = Path(f"{base}-iso.png")
        cut = Path(f"{base}-cutaway.png")
        spin = Path(f"{base}-spin.gif")
        gcode = Path(tempfile.gettempdir()) / "alt-slices" / f"{letter}-{slug}.MK3S.gcode"
        gcode.parent.mkdir(parents=True, exist_ok=True)

        print(f"==> {letter} {slug}")
        render_stl(scad, stl)
        adm = admesh_check(stl)
        render_iso(scad, iso)
        # cutaway uses the freshly-built STL
        cut_stl = cut.with_suffix(".stl")
        if cut_stl != stl:
            shutil.copy(stl, cut_stl)
        render_cutaway(scad, cut)
        cut_stl.unlink(missing_ok=True)
        render_spin(scad, spin)
        sl = slice_stl(stl, gcode)
        report.append(f"{letter} {slug}: admesh[{adm}] | {sl}")

        iso_imgs.append(Image.open(iso).convert("RGBA"))
        cut_imgs.append(Image.open(cut).convert("RGBA"))
        # collect frames for composite GIF: re-open the spin gif and
        # extract its frames
        frames: list[Image.Image] = []
        with Image.open(spin) as g:
            try:
                for fi in range(SPIN_FRAMES):
                    g.seek(fi)
                    frames.append(g.convert("RGBA").copy())
            except EOFError:
                pass
        spin_first_frames.append(frames)

    # ---- composites ------------------------------------------------
    tile = (240, 240)
    print("==> composite-cutaway.png")
    cut_composite = composite(cut_imgs, cols=4, tile=tile, transparent=False)
    cut_composite.save(ALT_DIR / "composite-cutaway.png")

    print("==> composite-spin.gif")
    n = min(len(f) for f in spin_first_frames)
    composite_frames: list[Image.Image] = []
    for i in range(n):
        per = [f[i] for f in spin_first_frames]
        composite_frames.append(
            composite(per, cols=4, tile=tile, transparent=True)
            .convert("RGBA")
        )
    # save as palette gif with alpha
    pal_frames = [f.convert("P", palette=Image.ADAPTIVE)
                  for f in composite_frames]
    pal_frames[0].save(
        ALT_DIR / "composite-spin.gif",
        save_all=True, append_images=pal_frames[1:],
        duration=int(1000 / SPIN_FPS), loop=0,
        disposal=2, transparency=0, optimize=True,
    )

    # ---- report ----------------------------------------------------
    print("\n--- per-concept report ---")
    for line in report:
        print(line)
    (ALT_DIR / "render-report.txt").write_text(
        "\n".join(report) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
