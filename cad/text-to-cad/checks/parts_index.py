"""Load a part by its key, recreated (text-to-cad) or reference (PR #170).

Recreated parts are the generated STEP files of the models in src/parts and
src/purchased.  Reference parts are PR #170's files, fetched into
STEP/reference/ by checks/fetch_reference.py.  The servos-above mounting
plate has no reference; for it the reference plate's two gears are turned
180 deg about the hinge, which is what the recreated variant does.
"""
from __future__ import annotations

import functools
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lib import frames  # noqa: E402

RECREATED_DIRS = [ROOT / "STEP" / "parts", ROOT / "STEP" / "purchased"]
REFERENCE_DIR = ROOT / "STEP" / "reference"


def _import(path: Path):
    from build123d import Compound, import_step
    shp = import_step(str(path))
    solids = shp.solids()
    return solids[0] if len(solids) == 1 else Compound(solids)


@functools.lru_cache(maxsize=None)
def load(key: str, source: str = "recreated"):
    """build123d shape of part ``key`` in its own frame."""
    if source == "recreated":
        for d in RECREATED_DIRS:
            p = d / f"{key}.step"
            if p.exists():
                return _import(p)
        raise FileNotFoundError(f"no recreated STEP for {key!r}")
    if key == "mounting_plate_servos_above":
        return _reference_mp_flipped()
    if key == "baseplate_servos_above":          # new part: no reference exists
        return load(key, "recreated")
    return _import(REFERENCE_DIR / f"{key}.step")


def board_box(M):
    """PR #170's board: 250 x 220 x 38.1, top on z = 0, front edge on y = 0."""
    from build123d import Align, Box
    b = Box(250.0, 220.0, frames.BOARD_T, align=(Align.CENTER, Align.MIN, Align.MAX))
    return b.moved(frames.to_location(M))


def _reference_mp_flipped():
    from build123d import Axis, Compound
    ref = _import(REFERENCE_DIR / "mounting_plate.step")
    solids = list(ref.solids())
    # the two 28T gear bodies are the ones centred on the hinge (MP Z axis)
    out = []
    for s in solids:
        bb = s.bounding_box()
        is_gear = abs(bb.max.X - 19.47) < 0.05 and abs(bb.max.Y - 19.47) < 0.05
        out.append(s.rotate(Axis.Z, 180) if is_gear else s)
    return Compound(out)


def placed(key: str, M, source: str = "recreated"):
    return load(key, source).moved(frames.to_location(M))


def assembly(tilt_deg: float = 0.0, variant: str = "below", source: str = "recreated",
             board: bool = True, fallback: bool = True, board_front_y: float | None = None) -> dict:
    """{name: placed shape}.  With ``fallback`` a part missing from the
    recreation is taken from the reference (and named so)."""
    out = {}
    for name, (key, M) in frames.placements(tilt_deg, variant).items():
        try:
            out[name] = placed(key, M, source)
        except FileNotFoundError:
            if not fallback:
                raise
            out[name + " [PR #170 file]"] = placed(key, M, "reference")
    if board:
        out["Mounting board"] = board_box(frames.board_placement(variant, board_front_y))
    return out
