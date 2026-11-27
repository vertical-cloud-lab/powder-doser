"""renders/ec11_fixed.png: EC v11 as fixed on 2026-11-27, with the parts it meets (the 24T pinion and the NEMA 11 in it, the guide and
its beam, module 1's plate, auger and gear), so the fixes are visible: the spine stops short of the pinion and two bars run beside it to
the motor's cheeks; the guide shoe hangs from a bracket behind the arm, its nose in the guide's seat.

    xvfb-run -a python ec_fix_still.py [dir_x dir_y dir_z dist]
"""
from __future__ import annotations

import sys

import numpy as np

import layout as L
import render as R

KEEP = {"ec11", "pinion24", "nema11", "guide11", "solenoid", "ec_pin_screw"}
KEEP_MOD = {"auger"}


def main(direction=(0.35, -0.9, 0.55), dist=290.0, out="renders/ec11_fixed.png"):
    st = L.State(enclosure=False)
    pl = L.placements(st)
    k0 = L.carriage_at(L.CARRIAGE_LINK0, 0.0)
    show = [p for p in pl if p.key in KEEP or (p.module == k0 and p.key in KEEP_MOD)]
    v = R.View(1600, 1000)
    col = {"ec11": (0.30, 0.72, 0.45), "pinion24": (0.95, 0.45, 0.05), "guide11": (0.93, 0.6, 0.15)}
    opacity = {}
    for k, p in R.keyed(show):
        if p.key == "auger":
            opacity[k] = 0.25
        if p.key == "guide11":
            opacity[k] = 0.45
    v.show(show, colors={k: col[p.key] for k, p in R.keyed(show) if p.key in col}, opacity=opacity)
    focal = L.to_world(L.sam_frame(L.station_frame(), 0.0), (100.0, 18.0, -32.0))
    v.camera(focal, direction, dist, view_angle=32.0)
    img = v.image()
    img = R.caption(img, "EC v11 as fixed (2026-11-27): one solid, clear of the pinion, its shoe in the guide's seat",
                    "the spine stops short of the pinion, bars run beside it to the motor; the shoe hangs behind the arm, in the guide's seat (see-through)")
    img.save(out)
    print("wrote", out)


if __name__ == "__main__":
    if len(sys.argv) >= 5:
        main(tuple(float(a) for a in sys.argv[1:4]), float(sys.argv[4]))
    else:
        main()
