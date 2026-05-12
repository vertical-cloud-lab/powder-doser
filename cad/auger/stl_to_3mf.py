#!/usr/bin/env python3
"""Convert the auger STL to a model-only 3MF (Bambu Studio / PrusaSlicer / Cura).

This produces a *generic* 3MF (3D/3dmodel.model + _rels + [Content_Types]), not
a Bambu project 3MF with embedded gcode/config. That is intentional: Bambu
Studio's "Import 3MF" / "Add object" flow expects a model 3MF and errors out
on project 3MFs sliced for a different machine (see PR #16 / tensegrity
discussion for the gcode-3MF import-error history).

Usage:
    python3 stl_to_3mf.py <input.stl> <output.3mf>
"""
from __future__ import annotations

import sys
from pathlib import Path


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__, file=sys.stderr)
        return 2
    src = Path(argv[1])
    dst = Path(argv[2])
    import trimesh  # imported lazily so --help works without the dep

    mesh = trimesh.load(src, force="mesh")
    if not mesh.is_watertight:
        print(f"WARNING: {src} is not watertight", file=sys.stderr)
    dst.parent.mkdir(parents=True, exist_ok=True)
    mesh.export(dst)

    # Sanity-check round-trip so a corrupted export can't slip through silently.
    rt = trimesh.load(dst, force="mesh")
    print(
        f"{dst.name}: {len(mesh.faces)} faces, "
        f"volume={mesh.volume / 1000:.2f} cm^3, "
        f"bbox={mesh.bounds.tolist()}, "
        f"roundtrip_volume={rt.volume / 1000:.2f} cm^3"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
