"""Measure the real auger's internal geometry from the STEP (cadquery/OCP -> trimesh).

Writes out/auger/auger_geometry_raw.json (ray-cast hits); the tessellated STLs go to a temp cache.
"""
import json, os, sys, tempfile
import numpy as np
import cadquery as cq
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
REF = os.path.join(HERE, "..", "reference")
OUT = os.path.join(HERE, "out", "auger")
os.makedirs(OUT, exist_ok=True)


def load(name, tol=0.05):
    shp = cq.importers.importStep(os.path.join(REF, name))
    cache = os.path.join(tempfile.gettempdir(), "auger_sim_cache")   # 21 MB of STL; kept out of the repo
    os.makedirs(cache, exist_ok=True)
    stl = os.path.join(cache, name.replace(".step", ".stl"))
    cq.exporters.export(shp, stl, tolerance=tol, angularTolerance=0.1)
    m = trimesh.load(stl)
    return shp, m


def radial_profile(m, z, n_theta=72, rmax=30.0):
    """Ray-cast outward from the axis at height z; return list of (theta, [r hits])."""
    th = np.linspace(0, 2 * np.pi, n_theta, endpoint=False)
    origins = np.zeros((n_theta, 3)); origins[:, 2] = z
    dirs = np.stack([np.cos(th), np.sin(th), np.zeros_like(th)], 1)
    locs, idx_ray, _ = m.ray.intersects_location(origins, dirs, multiple_hits=True)
    hits = [[] for _ in th]
    for p, i in zip(locs, idx_ray):
        hits[i].append(float(np.hypot(p[0], p[1])))
    return th, [sorted(h) for h in hits]


def axial_hits(m, x, y, z0=-5, z1=260):
    o = np.array([[x, y, z0]]); d = np.array([[0, 0, 1.0]])
    locs, _, _ = m.ray.intersects_location(o, d, multiple_hits=True)
    return np.sort(locs[:, 2]) if len(locs) else np.array([])


if __name__ == "__main__":
    shp, m = load("auger-threaded-storage.step")
    bb = shp.val().BoundingBox()
    print("auger bbox", bb.xmin, bb.xmax, bb.ymin, bb.ymax, bb.zmin, bb.zmax)
    print("watertight", m.is_watertight, "faces", len(m.faces), "volume_mm3", m.volume)
    res = {"bbox_mm": [bb.xmin, bb.xmax, bb.ymin, bb.ymax, bb.zmin, bb.zmax],
           "solid_volume_mm3": float(m.volume)}
    prof = {}
    for z in [0.2, 1, 2, 4, 6, 8, 10, 11.5, 12.5, 15, 20, 30, 50, 80, 84, 100, 150, 200, 240, 245, 248, 249.5]:
        th, hits = radial_profile(m, z)
        first = [h[0] if h else None for h in hits]
        nh = [len(h) for h in hits]
        # summarise: min/max of first hit, typical hit list for theta=0
        f = np.array([v for v in first if v is not None]) if any(v is not None for v in first) else np.array([np.nan])
        prof[z] = {"first_hit_min": float(np.nanmin(f)), "first_hit_max": float(np.nanmax(f)),
                   "hits_theta0": [round(v, 3) for v in hits[0]], "hits_theta90": [round(v, 3) for v in hits[18]],
                   "nhits_min": int(min(nh)), "nhits_max": int(max(nh))}
        print(f"z={z:6.1f} first-hit r min/max {np.nanmin(f):6.2f}/{np.nanmax(f):6.2f}  th0 {prof[z]['hits_theta0'][:8]}  th90 {prof[z]['hits_theta90'][:8]}")
    res["radial_profile"] = {str(k): v for k, v in prof.items()}
    # axial rays at several radii to find flight crossings
    ax = {}
    for r in [0.0, 1.0, 2.0, 3.0, 4.5, 6.0, 8.0, 9.5, 10.2]:
        zs = axial_hits(m, r, 0.0)
        ax[r] = [round(float(v), 3) for v in zs]
        print(f"axial r={r}: n={len(zs)} first {ax[r][:14]} ... last {ax[r][-6:]}")
    res["axial_hits_theta0"] = {str(k): v for k, v in ax.items()}
    json.dump(res, open(os.path.join(OUT, "auger_geometry_raw.json"), "w"), indent=1)
    shp2, m2 = load("auger-cap-threaded.step")
    bb2 = shp2.val().BoundingBox()
    print("cap bbox", bb2.xmin, bb2.xmax, bb2.ymin, bb2.ymax, bb2.zmin, bb2.zmax, "vol", m2.volume)
