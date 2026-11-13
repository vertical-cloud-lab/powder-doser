"""Measure the auger's 44T gear from the lab STEP (PR #170) and fit its involute.

Slices `reference/auger-threaded-storage.step` (the paternoster's copy) at the
gear's mid-plane, bins the outer boundary by radius, and fits the half tooth
angle psi(r) = s/(2 r_p) + inv(phi) - inv(alpha_r), cos(alpha_r) = r_b / r, for
the pressure angle phi and the pitch-circle tooth thickness s. Writes
out/gear_geometry.json.

    python measure_gear.py
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "paternoster"))
from step_io import read_step_parts  # noqa: E402

STEP = HERE.parent / "paternoster" / "reference" / "auger-threaded-storage.step"
N_TEETH = 44


def inv(a):
    return np.tan(a) - a


def section_points(shape, z: float) -> np.ndarray:
    import cadquery as cq
    from OCP.BRepAlgoAPI import BRepAlgoAPI_Section
    from OCP.gp import gp_Dir, gp_Pln, gp_Pnt
    s = BRepAlgoAPI_Section(shape.wrapped, gp_Pln(gp_Pnt(0, 0, z), gp_Dir(0, 0, 1)))
    s.Build()
    pts = []
    for e in cq.Shape.cast(s.Shape()).Edges():
        for t in np.linspace(0, 1, 200):
            p = e.positionAt(t)
            pts.append((p.x, p.y))
    return np.array(pts)


def main() -> dict:
    aug = next(iter(read_step_parts(STEP).values()))
    # gear side faces: the planar faces normal to z whose outline reaches past the tube (r 12.5)
    zf = []
    for f in aug.Faces():
        if f.geomType() == "PLANE" and abs(f.normalAt().z) > 0.999:
            bb = f.BoundingBox()
            if max(abs(bb.xmin), abs(bb.xmax), abs(bb.ymin), abs(bb.ymax)) > 20.0:
                zf.append(0.5 * (bb.zmin + bb.zmax))
    z0, z1 = min(zf), max(zf)
    zm = 0.5 * (z0 + z1)
    p = section_points(aug, zm)
    r = np.hypot(p[:, 0], p[:, 1])
    th = np.arctan2(p[:, 1], p[:, 0])
    m = r > 20.5
    r, th = r[m], th[m]
    pitch = 2 * math.pi / N_TEETH
    tip = r > r.max() - 0.05
    c = math.atan2(np.mean(np.sin(np.mod(th[tip], pitch) * N_TEETH)), np.mean(np.cos(np.mod(th[tip], pitch) * N_TEETH))) / N_TEETH
    rel = np.mod(th - c + pitch / 2, pitch) - pitch / 2
    bins = np.linspace(r.min() + 0.05, r.max() - 0.02, 28)
    prof = []
    for a, b in zip(bins[:-1], bins[1:]):
        k = (r >= a) & (r < b)
        if k.sum() >= 5:
            prof.append(((a + b) / 2, float(np.median(np.abs(rel[k])))))
    prof = np.array(prof)
    ra, rf = float(r.max()), float(r.min())
    mod = 2 * ra / (N_TEETH + 2)
    rp = mod * N_TEETH / 2
    sel = (prof[:, 0] > rf + 0.45) & (prof[:, 0] < ra - 0.12)

    def model(x, rr):
        phi, s = x
        rb = rp * math.cos(phi)
        return s / (2 * rp) + inv(phi) - inv(np.arccos(np.clip(rb / rr, -1, 1)))

    fit = least_squares(lambda x: model(x, prof[sel, 0]) - prof[sel, 1], x0=[math.radians(20), 1.5])
    phi, s = fit.x
    out = dict(source=str(STEP.relative_to(HERE.parent.parent)), teeth=N_TEETH, module_mm=round(mod, 4),
               face_z_mm=[round(z0, 2), round(z1, 2)], face_width_mm=round(z1 - z0, 2),
               tip_radius_mm=round(ra, 3), root_radius_mm=round(rf, 3), pitch_radius_mm=round(rp, 3),
               pressure_angle_deg=round(math.degrees(phi), 3), tooth_thickness_pitch_mm=round(s, 4),
               tooth_thickness_std_mm=round(math.pi * mod / 2, 4),
               fit_rms_deg=float(math.degrees(np.sqrt(np.mean(fit.fun ** 2)))),
               half_angle_profile=[[round(a, 3), round(math.degrees(b), 4)] for a, b in prof])
    (HERE / "out").mkdir(exist_ok=True)
    (HERE / "out" / "gear_geometry.json").write_text(json.dumps(out, indent=1))
    print(json.dumps({k: v for k, v in out.items() if k != "half_angle_profile"}, indent=1))
    return out


if __name__ == "__main__":
    main()
