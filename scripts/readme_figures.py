#!/usr/bin/env python3
"""Make the README's figure images from the paper's preview images.

The paper's previews (``paper/v2/preview/*.png``, built by
``paper/v2/build_figures.py`` on PR #209) are each figure as typeset with its
caption underneath.  The README carries the captions as text, so this script
crops the typeset caption off each preview and writes the figure alone to
``docs/readme/``.

The caption is found from the blank rows: walking up from the bottom of the
page, the lines of the caption are separated by gaps of a few pixels, and the
first gap of 15 px or more is the space between the figure and its caption.

    python3 scripts/readme_figures.py [PREVIEW_DIR] [OUT_DIR]

PREVIEW_DIR defaults to paper/v2/preview and OUT_DIR to docs/readme.  Needs
Pillow and NumPy.  Check each output by eye after a re-run.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image

REPO = Path(__file__).resolve().parents[1]
FIGURES = [
    "fig1_doser", "fig2_timeline", "fig3_redesign", "fig4_dosing", "fig5_use",
    "fig6_open_loop", "fig7_closed_loop", "fig7C_closed_loop_mg_overlay",
    "figS1_cad_comparison", "figS4_assembly_exploded",
]
INK = 200        # a pixel darker than this (0-255 grey) is ink
CAPTION_GAP = 15  # px; the gaps between caption lines are 3-4 px
PAD = 12          # px of white kept around the figure


def blank_runs(blank: np.ndarray) -> list[tuple[int, int]]:
    """(start, length) of each run of blank rows."""
    runs, i, n = [], 0, len(blank)
    while i < n:
        if blank[i]:
            j = i
            while j < n and blank[j]:
                j += 1
            runs.append((i, j - i))
            i = j
        else:
            i += 1
    return runs


def crop_caption(path: Path) -> Image.Image:
    im = Image.open(path).convert("RGB")
    a = np.asarray(im.convert("L"))
    h = a.shape[0]
    runs = [r for r in blank_runs((a < INK).sum(axis=1) == 0) if 0 < r[0] and r[0] + r[1] < h]
    cut = next(start for start, length in reversed(runs) if length >= CAPTION_GAP)
    fig = a[:cut] < INK
    rows, cols = np.where(fig.any(axis=1))[0], np.where(fig.any(axis=0))[0]
    return im.crop((max(cols[0] - PAD, 0), max(rows[0] - PAD, 0),
                    min(cols[-1] + PAD + 1, a.shape[1]), min(rows[-1] + PAD + 1, cut)))


def main() -> None:
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "paper/v2/preview"
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else REPO / "docs/readme"
    out.mkdir(parents=True, exist_ok=True)
    for stem in FIGURES:
        img = crop_caption(src / f"{stem}.png")
        img.save(out / f"{stem}.png", optimize=True)
        print(f"{stem}.png  {img.size[0]} x {img.size[1]}")


if __name__ == "__main__":
    main()
