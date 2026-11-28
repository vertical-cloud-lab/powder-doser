"""Shaded views of the fixed mounting plate, straight from Onshape (1 call per view).

    python render.py <versionId>
"""
from __future__ import annotations

import base64
import sys

from client import HERE, Onshape
from fix_motor_holes import DID, EID

OUT = HERE.parent / "print-files"
# Onshape view matrices (row-major 3x4)
VIEWS = {"iso": "isometric",
         "stepper_face": "-1,0,0,0,0,0,1,0,0,1,0,0"}   # from +Y: the NEMA-11 face of the stepper block


def main(vid: str) -> None:
    o = Onshape(budget=len(VIEWS), run="pr181-render")
    for tag, matrix in VIEWS.items():
        r = o.get(f"partstudios/d/{DID}/v/{vid}/e/{EID}/shadedviews",
                  params={"viewMatrix": matrix, "outputHeight": 700, "outputWidth": 1000, "pixelSize": 0,
                          "edges": "show", "useAntiAliasing": "true"})
        out = OUT / f"mounting_plate_onshape_{tag}.png"
        out.write_bytes(base64.b64decode(r["images"][0]))
        print("saved", out)


if __name__ == "__main__":
    main(sys.argv[1])
