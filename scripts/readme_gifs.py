#!/usr/bin/env python3
"""Fetch the README's animations from the branches they were made on.

Every GIF in ``docs/readme/gifs/`` was first posted on an issue or PR and
lives on that PR's branch, which is not merged.  This script downloads each one
from the commit it was posted at, so the README keeps working after those
branches are deleted, and shrinks the larger ones with gifsicle so the README
stays quick to load.  One GIF is cut from an MP4 on a PR branch (CLIPS), which
also needs ffmpeg.

    python3 scripts/readme_gifs.py [OUT_DIR]

OUT_DIR defaults to docs/readme/gifs.  Needs gifsicle on the PATH and network
access to github.com (the repository is public).  ``docs/readme/gifs/README.md``
lists where each GIF came from.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RAW = "https://github.com/vertical-cloud-lab/powder-doser/raw"

# (output name, commit, path at that commit, width to scale to or None)
GIFS = [
    # PR #170 (head): the team's parts assembled in CAD, step by step, with the bill of materials
    ("assembly.gif", "7f5b3b7", "cad/full-assembly/renders/assembly_steps.gif", None),
    # PR #170: tilt, auger rotation and solenoid tap, close up
    ("doser_motion.gif", "7f5b3b7", "cad/full-assembly/renders/doser_motion.gif", 800),
    # PR #175: the three-phase dose (bulk, trickle, taps) replayed on the CAD from a logged dose
    ("three_phase_dose.gif", "ff074df", "docs/optimization/slides/procedure/procedure_annotated.gif", 960),
    # PR #173: one doser, 13 powders
    ("thirteen_powders.gif", "d75b7b7", "paper/figures/versatility/versatility_build.gif", 1280),
    # Issue #116: white rice flour, block C at 90 degrees tilt, from the bench livestream (4x)
    ("livestream_white_rice_flour.gif", "e51e8e8", "docs/battery-runs/clips/wrf_C90.gif", None),
    # PR #176: an agent's code-CAD recreation of the doser, tilting, turning and tapping
    ("ai_recreation_motion.gif", "61717c7", "cad/text-to-cad/renders/assembly/assembly_servos_above_motion.gif", None),
    # Issue #158: DEM digital twin of the rig's auger, 29k salt grains
    ("dem_twin.gif", "ac9580e", "sim/dem/results/rig_t27p5_r60.gif", None),
    # PR #185: the multi-doser chain carousel, v10 (CAD only, not built)
    ("multi_doser_v10.gif", "c72c5bc", "cad/chain-carousel-v10/renders/v10/overview_v10.gif", 800),
]

# Clips cut from MP4s: (output name, commit, path, start s, end s, width, frames per second)
CLIPS = [
    # PR #174: loading an auger with Al 4047 and fitting it to the doser (30 Sep 2026); left, the
    # phone camera on the bench; right, the bench livestream; the speed is in the bottom corners
    ("loading_al4047.gif", "ed26df4",
     "docs/videos/2026-09-30-al4047-claude-dose/al4047_claude_dose_slide.mp4", 0.0, 17.8, 560, 5),
]


def main() -> None:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "docs/readme/gifs"
    out.mkdir(parents=True, exist_ok=True)
    if shutil.which("gifsicle") is None:
        sys.exit("gifsicle not found (apt-get install gifsicle)")
    for name, commit, path, width in GIFS:
        raw = out / f".{name}.orig"
        with urllib.request.urlopen(f"{RAW}/{commit}/{path}") as r:
            raw.write_bytes(r.read())
        cmd = ["gifsicle", "-O3", "--lossy=30", "--no-comments", "--no-extensions"]
        if width:
            cmd += ["--resize-width", str(width)]
        cmd += [str(raw), "-o", str(out / name)]
        subprocess.run(cmd, check=True)
        before, after = raw.stat().st_size, (out / name).stat().st_size
        raw.unlink()
        print(f"{name:34s} {before / 1e6:5.2f} MB -> {after / 1e6:5.2f} MB  ({commit}:{path})")
    for name, commit, path, start, end, width, fps in CLIPS:
        raw = out / f".{name}.mp4"
        with urllib.request.urlopen(f"{RAW}/{commit}/{path}") as r:
            raw.write_bytes(r.read())
        vf = f"trim={start}:{end},setpts=PTS-STARTPTS,hqdn3d=2:2:6:6,fps={fps},scale={width}:-2:flags=lanczos"
        palette, gif = out / f".{name}.png", out / f".{name}.raw.gif"
        ff = ["ffmpeg", "-v", "error", "-y", "-i", str(raw)]
        subprocess.run(ff + ["-vf", f"{vf},palettegen=max_colors=128:stats_mode=diff", str(palette)], check=True)
        subprocess.run(ff + ["-i", str(palette), "-lavfi",
                             f"{vf}[v];[v][1:v]paletteuse=dither=bayer:bayer_scale=5:diff_mode=rectangle",
                             str(gif)], check=True)
        subprocess.run(["gifsicle", "-O3", "--lossy=80", str(gif), "-o", str(out / name)], check=True)
        for f in (raw, palette, gif):
            f.unlink()
        print(f"{name:34s} {(out / name).stat().st_size / 1e6:5.2f} MB  ({commit}:{path}, {start}-{end} s)")


if __name__ == "__main__":
    main()
