"""Render a 360 degree turntable-spin GIF of an OpenSCAD model.

Used to generate the preview GIFs of the alternative-dosing top-ranked
designs (cad/sieve_cup.scad and cad/tap_anvil.scad) that accompany
docs/preliminary-design-sieve-cup.md.

Invokes OpenSCAD's headless PNG renderer at a sequence of azimuth
angles, then stitches the frames together with Pillow into a GIF.
Wraps OpenSCAD in ``xvfb-run`` automatically when no ``$DISPLAY``
is set so it works on headless CI runners.

Run from the repository root::

    sudo apt-get install -y openscad xvfb         # one-time, ~80 MB
    pip install pillow

    python -m scripts.render_sieve_cup --variant passive
    python -m scripts.render_sieve_cup --variant erm
    python -m scripts.render_sieve_cup --variant anvil

Outputs (default):
    cad/sieve-cup-spin.gif        (passive concept-A cup)
    cad/sieve-cup-erm-spin.gif    (concept-G cup with ERM pocket)
    cad/tap-anvil-spin.gif        (bed-mounted anvil)
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Sequence

from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[1]

VARIANTS = {
    "passive": {
        "scad":   REPO_ROOT / "cad" / "sieve_cup.scad",
        "out":    REPO_ROOT / "cad" / "sieve-cup-spin.gif",
        "defs":   ["erm_motor_pocket=false"],
        "camera": (0, 0, 18, 55, 0, 25, 260),
    },
    "erm": {
        "scad":   REPO_ROOT / "cad" / "sieve_cup.scad",
        "out":    REPO_ROOT / "cad" / "sieve-cup-erm-spin.gif",
        "defs":   ["erm_motor_pocket=true"],
        "camera": (0, 0, 18, 55, 0, 25, 260),
    },
    "anvil": {
        "scad":   REPO_ROOT / "cad" / "tap_anvil.scad",
        "out":    REPO_ROOT / "cad" / "tap-anvil-spin.gif",
        "defs":   [],
        "camera": (0, 0, 8, 55, 0, 25, 200),
    },
}


def _openscad_command() -> list[str]:
    """Return the command prefix for invoking OpenSCAD.

    OpenSCAD's ``-o file.png`` mode still spins up a GL context, so on
    headless CI runners (no ``$DISPLAY``) it segfaults on launch. If we
    detect a headless environment and ``xvfb-run`` is available,
    transparently wrap the call.
    """
    cmd = ["openscad"]
    if not os.environ.get("DISPLAY") and shutil.which("xvfb-run"):
        cmd = ["xvfb-run", "-a", "--server-args=-screen 0 1024x768x24"] + cmd
    return cmd


def render_frame(
    scad: Path,
    png: Path,
    defs: Sequence[str],
    camera: tuple,
    azimuth_deg: float,
    imgsize: tuple[int, int] = (640, 480),
) -> None:
    """Render a single PNG frame at the given azimuth."""
    cx, cy, cz, rx, ry, rz, dist = camera
    cmd = _openscad_command() + [
        "-o", str(png),
        f"--imgsize={imgsize[0]},{imgsize[1]}",
        f"--camera={cx},{cy},{cz},{rx},{ry},{rz + azimuth_deg},{dist}",
        "--colorscheme=Tomorrow",
    ]
    for d in defs:
        cmd += ["-D", d]
    cmd.append(str(scad))
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL)


def render_spin(
    variant: str,
    n_frames: int = 36,
    imgsize: tuple[int, int] = (640, 480),
    fps: int = 18,
) -> Path:
    cfg = VARIANTS[variant]
    out: Path = cfg["out"]
    with tempfile.TemporaryDirectory() as td:
        frames = []
        for i in range(n_frames):
            az = 360.0 * i / n_frames
            png = Path(td) / f"frame_{i:03d}.png"
            render_frame(
                scad=cfg["scad"],
                png=png,
                defs=cfg["defs"],
                camera=cfg["camera"],
                azimuth_deg=az,
                imgsize=imgsize,
            )
            with Image.open(png) as frame:
                frames.append(
                    frame.convert("P", palette=Image.ADAPTIVE).copy()
                )
        out.parent.mkdir(parents=True, exist_ok=True)
        frames[0].save(
            out,
            save_all=True,
            append_images=frames[1:],
            duration=int(1000 / fps),
            loop=0,
            optimize=True,
            disposal=2,
        )
    return out


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    p.add_argument(
        "--variant",
        choices=list(VARIANTS),
        default="passive",
        help="Which model to render (default: %(default)s).",
    )
    p.add_argument("--frames", type=int, default=36)
    p.add_argument("--width", type=int, default=640)
    p.add_argument("--height", type=int, default=480)
    p.add_argument("--fps", type=int, default=18)
    args = p.parse_args(argv)

    if not shutil.which("openscad"):
        sys.stderr.write("openscad not found on PATH; install it first.\n")
        return 1
    if args.frames < 1:
        sys.stderr.write("--frames must be >= 1\n")
        return 2
    if args.fps < 1:
        sys.stderr.write("--fps must be >= 1\n")
        return 2
    if args.width < 1 or args.height < 1:
        sys.stderr.write("--width and --height must be >= 1\n")
        return 2

    out = render_spin(
        variant=args.variant,
        n_frames=args.frames,
        imgsize=(args.width, args.height),
        fps=args.fps,
    )
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
