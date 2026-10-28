#!/usr/bin/env python3
"""Extract one still per build step from the assembly walkthrough GIF of PR #170.

The walkthrough (cad/full-assembly/renders/assembly_walkthrough.gif on branch
claude/issue-165-20261001-1931, commit ce256c3) shows the 19 build steps of
cad/full-assembly/BOM.md in order.  Each step ends on a caption hold of 2 s or
more, so the first 19 frames that long are the finished states of steps 1-19.
Each still is cropped to the rendered view (the step counter and caption text
are dropped; SI Fig. S2 gives its own labels) and saved as
assets/assembly_steps/stepNN.png for make_figures.py.

Usage (from the repository root):
    git show ce256c3:cad/full-assembly/renders/assembly_walkthrough.gif > /tmp/walkthrough.gif
    python3 paper/figures/data/extract_assembly_steps.py /tmp/walkthrough.gif
"""

from __future__ import annotations

import pathlib
import sys

import numpy as np
from PIL import Image, ImageSequence

OUT = pathlib.Path(__file__).resolve().parents[1] / "assets" / "assembly_steps"
N_STEPS = 19
HOLD_MS = 2000
# 960 x 720 frames: title and step counter above y = 40, caption below y = 628
RENDER_BOX = (0, 40, 960, 628)


def trim(img: Image.Image, pad: int = 8) -> Image.Image:
    """Crop the near-white background around the rendered parts."""
    arr = np.asarray(img.convert("RGB")).astype(int)
    mask = (arr < 240).any(axis=2)
    rows = np.flatnonzero(mask.any(axis=1))
    cols = np.flatnonzero(mask.any(axis=0))
    if not rows.size:
        return img
    r0, r1 = max(rows[0] - pad, 0), min(rows[-1] + pad, arr.shape[0])
    c0, c1 = max(cols[0] - pad, 0), min(cols[-1] + pad, arr.shape[1])
    return img.crop((c0, r0, c1, r1))


def main(gif_path: str) -> None:
    gif = Image.open(gif_path)
    holds = [frame.convert("RGB").copy()
             for frame in ImageSequence.Iterator(gif)
             if frame.info.get("duration", 0) >= HOLD_MS][:N_STEPS]
    if len(holds) != N_STEPS:
        raise SystemExit(f"expected {N_STEPS} step holds, found {len(holds)}")
    OUT.mkdir(parents=True, exist_ok=True)
    for k, frame in enumerate(holds, start=1):
        trim(frame.crop(RENDER_BOX)).save(OUT / f"step{k:02d}.png", optimize=True)
    print(f"wrote {N_STEPS} stills to {OUT}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "/tmp/walkthrough.gif")
