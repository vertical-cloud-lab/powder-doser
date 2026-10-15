"""Hole positions of the recreated mounting plate against the Fusion part.

    python3 checks/mounting_plate_holes.py [NEW.step] [REF.step] [--tol 0.2]

A hole is a set of concave cylindrical faces with one radius and one axis
line that together go all the way round (360 deg) over one stretch of the
axis; the faces' own axis and extent give its centre (mid-length point on
the axis), so no tessellation is involved.  Every reference hole is paired
with the nearest new hole of the same diameter and axis direction, and the
check reports the axis offset (distance between the two axis lines), the
centre distance and the length difference.  Fails (exit 1) when a hole is
missing or extra, or an axis offset or centre distance exceeds --tol (mm).
"""
from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
NEW = HERE.parent / "STEP" / "parts" / "mounting_plate.step"
REF = Path("/tmp/pr170/cad/full-assembly/components/fusion-step/mounting-plate.step")


def holes(path: Path) -> list[dict]:
    from build123d import GeomType, import_step
    from OCP.BRepAdaptor import BRepAdaptor_Surface

    groups: dict[tuple, list[dict]] = {}
    for body, solid in enumerate(import_step(str(path)).solids()):
        for face in solid.faces():
            if face.geom_type != GeomType.CYLINDER:
                continue
            surf = BRepAdaptor_Surface(face.wrapped)
            cyl = surf.Cylinder()
            ax = cyl.Axis()
            d = np.array([ax.Direction().X(), ax.Direction().Y(), ax.Direction().Z()])
            d = d if d[np.argmax(np.abs(d))] > 0 else -d          # canonical sign
            loc = np.array([ax.Location().X(), ax.Location().Y(), ax.Location().Z()])
            p0 = loc - d * loc.dot(d)                              # axis point nearest the origin
            # concave (a hole) when the outward normal points at the axis
            pnt = face.position_at(0.5, 0.5)
            radial = np.array([pnt.X, pnt.Y, pnt.Z]) - p0
            radial -= d * radial.dot(d)
            n = face.normal_at(pnt)
            if np.dot([n.X, n.Y, n.Z], radial) >= 0:
                continue
            ts = [np.dot([vx.X, vx.Y, vx.Z], d) for vx in face.vertices()]
            key = (round(cyl.Radius(), 3), *np.round(d, 4), *np.round(p0, 3))
            groups.setdefault(key, []).append(dict(
                span=surf.LastUParameter() - surf.FirstUParameter(),
                t=(min(ts), max(ts)), body=body))
    out = []
    for key, faces in groups.items():
        r, d, p0 = key[0], np.array(key[1:4]), np.array(key[4:7])
        faces.sort(key=lambda f: f["t"][0])
        runs: list[list[dict]] = []
        for f in faces:                                  # split by stretch of the axis
            if runs and f["t"][0] < max(g["t"][1] for g in runs[-1]) - 1e-6:
                runs[-1].append(f)
            else:
                runs.append([f])
        for run in runs:
            if sum(f["span"] for f in run) < 2 * math.pi - 1e-3:
                continue                                 # a concave arc, not a hole
            t0, t1 = min(f["t"][0] for f in run), max(f["t"][1] for f in run)
            out.append(dict(d_mm=2 * r, axis=d, p0=p0, centre=p0 + d * 0.5 * (t0 + t1),
                            length=t1 - t0, bodies=sorted({f["body"] for f in run})))
    return sorted(out, key=lambda h: (-h["d_mm"], *np.round(h["centre"], 2)))


def axis_offset(a: dict, b: dict) -> float:
    w = b["p0"] - a["p0"]
    return float(np.linalg.norm(w - a["axis"] * w.dot(a["axis"])))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("new", nargs="?", default=str(NEW))
    ap.add_argument("ref", nargs="?", default=str(REF))
    ap.add_argument("--tol", type=float, default=0.2)
    a = ap.parse_args()
    new, ref = holes(Path(a.new)), holes(Path(a.ref))
    unused = list(range(len(new)))
    worst, failures = 0.0, []
    names = {(0, 1, 0): "floor", (1, 0, 0): "stepper", (0, 0, 1): "hinge"}
    print(f"{'hole':8s} {'dia':>6s} {'ref centre (x, y, z)':>30s} {'axis off':>9s} "
          f"{'centre d':>9s} {'len d':>7s}")
    for h in ref:
        cands = [i for i in unused if abs(new[i]["d_mm"] - h["d_mm"]) < 0.01
                 and abs(abs(new[i]["axis"].dot(h["axis"])) - 1) < 1e-6]
        if not cands:
            failures.append(f"missing Ø{h['d_mm']:.2f} at {np.round(h['centre'], 3)}")
            continue
        i = min(cands, key=lambda i: np.linalg.norm(new[i]["centre"] - h["centre"]))
        unused.remove(i)
        off = axis_offset(h, new[i])
        dc = float(np.linalg.norm(new[i]["centre"] - h["centre"]))
        dl = new[i]["length"] - h["length"]
        worst = max(worst, off, dc)
        kind = names.get(tuple(int(round(abs(c))) for c in h["axis"]), "?")
        c = ", ".join(f"{v:8.3f}" for v in h["centre"])
        print(f"{kind:8s} {h['d_mm']:6.2f} ({c}) {off:9.4f} {dc:9.4f} {dl:7.3f}")
        if off > a.tol or dc > a.tol:
            failures.append(f"Ø{h['d_mm']:.2f} at {np.round(h['centre'], 3)}: off {off:.3f}, centre {dc:.3f}")
    for i in unused:
        failures.append(f"extra Ø{new[i]['d_mm']:.2f} at {np.round(new[i]['centre'], 3)}")
    print(f"\n{len(ref)} reference holes, {len(new)} new; worst axis offset / centre "
          f"distance {worst:.4f} mm (tolerance {a.tol} mm)")
    if failures:
        print("FAIL\n  " + "\n  ".join(failures))
        sys.exit(1)
    print("PASS")


if __name__ == "__main__":
    main()
