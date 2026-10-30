"""2D plane-stress FEA of the station's gear teeth (gmsh + scikit-fem, quadratic triangles).

* 44T auger gear: the real outline, sliced from the lab STEP at the gear's mid-plane
  (Onshape's generated teeth and fillets, exactly as printed).
* 20T pinion: a standard module-1, 20 deg involute generated here, root fillet 0.38 m
  (basic-rack tip radius).

A three-tooth sector is clamped on an inner arc and the middle tooth is loaded along
the line of action, over the Hertzian contact width, at (a) the tip, to compare with
Lewis (Shigley Eq. 14-8, Table 14-2), and (b) the highest point of single-tooth contact
(HPSTC) at the docked 32.1 mm centre distance. Outputs: root-fillet stress, the tooth's
compliance along the line of action, and a single-pair mesh stiffness used by
mesh_dynamics.py. Writes out/fea_tooth.json and out/fea_tooth_*.png.

    python fea_tooth.py
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

import common as C
import vizstyle as V

HERE = Path(__file__).resolve().parent
B_FACE = C.FACE


def inv(a):
    return np.tan(a) - a


# ---------------------------------------------------------------- outlines
def gear_outline_from_step(z_mid: float) -> np.ndarray:
    sys.path.insert(0, str(HERE.parent / "paternoster"))
    from step_io import read_step_parts
    import cadquery as cq
    from OCP.BRepAlgoAPI import BRepAlgoAPI_Section
    from OCP.gp import gp_Dir, gp_Pln, gp_Pnt
    aug = next(iter(read_step_parts(HERE.parent / "paternoster" / "reference" / "auger-threaded-storage.step").values()))
    s = BRepAlgoAPI_Section(aug.wrapped, gp_Pln(gp_Pnt(0, 0, z_mid), gp_Dir(0, 0, 1)))
    s.Build()
    pts = []
    for e in cq.Shape.cast(s.Shape()).Edges():
        L = e.Length()
        n = max(4, int(L / 0.01))
        for t in np.linspace(0, 1, n):
            p = e.positionAt(t)
            pts.append((p.x, p.y))
    p = np.array(pts)
    r = np.hypot(p[:, 0], p[:, 1])
    p = p[r > 20.0]
    th = np.arctan2(p[:, 1], p[:, 0])
    o = np.argsort(th)
    p = p[o]
    keep = np.r_[True, np.hypot(*np.diff(p, axis=0).T) > 1e-4]
    return p[keep]


def pinion_outline(z=C.Z1, m=C.M, rf=C.RF1, ra=C.RA1, rho=0.38) -> np.ndarray:
    """Standard involute outline (sharp root corners; the fillet is added by a shapely closing)."""
    rp = m * z / 2
    rb = rp * math.cos(C.PHI)
    s = math.pi * m / 2
    psi = lambda r: s / (2 * rp) + inv(C.PHI) - inv(np.arccos(np.clip(rb / r, -1, 1)))
    pts = []
    pitch = 2 * math.pi / z
    for k in range(z):
        tc = k * pitch
        r_inv = np.linspace(rb, ra, 60)
        r_rad = np.linspace(rf - 0.3, rb, 8)[:-1]
        # left flank (increasing angle side) goes root -> tip at tc - psi ... use symmetric halves
        right = [(r, tc - psi(rb)) for r in r_rad] + [(r, tc - psi(r)) for r in r_inv]
        left = [(r, tc + psi(r)) for r in r_inv[::-1]] + [(r, tc + psi(rb)) for r in r_rad[::-1]]
        tip = [(ra, a) for a in np.linspace(tc - psi(ra), tc + psi(ra), 6)[1:-1]]
        tooth = right + tip + left
        pts += [(r * math.cos(a), r * math.sin(a)) for r, a in tooth]
        # root arc to the next tooth
        a0, a1 = tc + psi(rb), tc + pitch - psi(rb)
        pts += [(rf * math.cos(a), rf * math.sin(a)) for a in np.linspace(a0, a1, 10)[1:-1]]
    from shapely.geometry import Polygon
    poly = Polygon(pts)
    disc = Polygon([(rf * math.cos(a), rf * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 400)])
    poly = poly.union(disc).buffer(rho * m, join_style=1, quad_segs=24).buffer(-rho * m, join_style=1, quad_segs=24)
    return np.array(poly.exterior.coords)[:-1]


def sector(outline: np.ndarray, z: int, r_in: float, n_side=1.5):
    """Three-tooth sector with the middle tooth on +y; returns polygon coords and the rotation used."""
    r = np.hypot(outline[:, 0], outline[:, 1])
    th = np.arctan2(outline[:, 1], outline[:, 0])
    pitch = 2 * math.pi / z
    tip = r > r.max() - 0.03
    c = math.atan2(np.mean(np.sin(np.mod(th[tip], pitch) * z)), np.mean(np.cos(np.mod(th[tip], pitch) * z))) / z
    rot = math.pi / 2 - c
    th2 = np.mod(th + rot + math.pi, 2 * math.pi) - math.pi
    lo, hi = math.pi / 2 - n_side * pitch, math.pi / 2 + n_side * pitch
    k = (th2 >= lo) & (th2 <= hi)
    o = np.argsort(th2[k])
    arc = np.c_[r[k][o] * np.cos(th2[k][o]), r[k][o] * np.sin(th2[k][o])]
    # close with radial cuts and the inner arc
    ia = np.linspace(hi, lo, 60)
    inner = np.c_[r_in * np.cos(ia), r_in * np.sin(ia)]
    return np.vstack([arc, inner]), lo, hi, len(arc)


# ---------------------------------------------------------------- mesh + solve
def mesh_polygon(coords: np.ndarray, n_outer: int, h: float, fine_pts: list):
    """Mesh the sector: coords[:n_outer] is the toothed outer arc (one spline), the rest the inner arc."""
    import gmsh
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 0)
    gmsh.model.add("tooth")
    outer = coords[:n_outer]
    # resample the outer arc to about 0.03 mm so the spline follows the fillets exactly
    seg = np.hypot(*np.diff(outer, axis=0).T)
    s = np.r_[0, np.cumsum(seg)]
    ss = np.linspace(0, s[-1], int(s[-1] / 0.03) + 2)
    outer = np.c_[np.interp(ss, s, outer[:, 0]), np.interp(ss, s, outer[:, 1])]
    inner = coords[n_outer:]
    po = [gmsh.model.geo.addPoint(x, y, 0, h) for x, y in outer]
    pi = [gmsh.model.geo.addPoint(x, y, 0, h) for x, y in inner]
    c1 = gmsh.model.geo.addSpline(po)
    c2 = gmsh.model.geo.addLine(po[-1], pi[0])
    c3 = gmsh.model.geo.addSpline(pi)
    c4 = gmsh.model.geo.addLine(pi[-1], po[0])
    loop = gmsh.model.geo.addCurveLoop([c1, c2, c3, c4])
    gmsh.model.geo.addPlaneSurface([loop])
    gmsh.model.geo.synchronize()
    fields = []
    for (x, y), hf, rf in fine_pts:
        p = gmsh.model.geo.addPoint(x, y, 0, hf)
        gmsh.model.geo.synchronize()
        f = gmsh.model.mesh.field.add("Distance")
        gmsh.model.mesh.field.setNumbers(f, "PointsList", [p])
        t = gmsh.model.mesh.field.add("Threshold")
        gmsh.model.mesh.field.setNumber(t, "InField", f)
        gmsh.model.mesh.field.setNumber(t, "SizeMin", hf)
        gmsh.model.mesh.field.setNumber(t, "SizeMax", h)
        gmsh.model.mesh.field.setNumber(t, "DistMin", rf)
        gmsh.model.mesh.field.setNumber(t, "DistMax", rf * 8)
        fields.append(t)
    mn = gmsh.model.mesh.field.add("Min")
    gmsh.model.mesh.field.setNumbers(mn, "FieldsList", fields)
    gmsh.model.mesh.field.setAsBackgroundMesh(mn)
    gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 0)
    gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 0)
    gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 0)
    gmsh.option.setNumber("Mesh.Algorithm", 6)
    gmsh.model.mesh.generate(2)
    nt, nc, _ = gmsh.model.mesh.getNodes()
    et, etags, enodes = gmsh.model.mesh.getElements(2)
    gmsh.finalize()
    xyz = nc.reshape(-1, 3)[:, :2]
    idx = {t: i for i, t in enumerate(nt)}
    tri = np.array([idx[t] for t in enodes[0]]).reshape(-1, 3)
    used = np.unique(tri)
    remap = -np.ones(len(xyz), int)
    remap[used] = np.arange(len(used))
    return xyz[used], remap[tri]


def solve(xy, tri, E, nu, load_xy, load_dir, wn, half_width, clamp_r):
    """Plane stress, thickness B_FACE. wn: normal load (N) spread over +-half_width along the boundary."""
    import skfem as fem
    from skfem.models.elasticity import lame_parameters, linear_elasticity
    m = fem.MeshTri(xy.T.copy(), tri.T.copy())
    e = fem.ElementVector(fem.ElementTriP2())
    ib = fem.Basis(m, e, intorder=4)
    lam, mu = lame_parameters(E, nu)
    lam_ps = 2 * lam * mu / (lam + 2 * mu)                  # plane stress
    K = fem.asm(linear_elasticity(lam_ps, mu), ib) * B_FACE
    # traction on boundary facets within half_width of the load point (arc length approx by distance)
    fb = fem.FacetBasis(m, e, intorder=4)
    d = np.asarray(load_dir, float)
    d /= np.linalg.norm(d)
    lx, ly = load_xy

    @fem.LinearForm
    def trac(v, w):
        x, y = w.x
        dist = np.sqrt((x - lx) ** 2 + (y - ly) ** 2)
        q = np.where(dist <= half_width, wn / (2 * half_width * B_FACE), 0.0)   # N/mm^2 over the patch
        return (q * d[0]) * v[0] + (q * d[1]) * v[1]

    f = fem.asm(trac, fb) * B_FACE
    # make the applied total exactly wn (patch quadrature on a polyline)
    one = fem.asm(fem.LinearForm(lambda v, w: np.where(np.sqrt((w.x[0] - lx) ** 2 + (w.x[1] - ly) ** 2) <= half_width, 1.0, 0.0) * (d[0] * v[0] + d[1] * v[1])), fb) * B_FACE
    tot = (f @ np.tile(d, ib.N // 2)) if False else None
    Ux = ib.project(lambda x: np.array([np.ones_like(x[0]), np.zeros_like(x[0])]))   # rigid translations (all P2 dofs)
    Uy = ib.project(lambda x: np.array([np.zeros_like(x[0]), np.ones_like(x[0])]))
    fx0, fy0 = f @ Ux, f @ Uy
    f = f * (wn / max(np.hypot(fx0, fy0), 1e-12))            # patch quadrature on a short polyline: restore the exact total
    clamp = ib.get_dofs(lambda x: np.hypot(x[0], x[1]) < clamp_r + 1e-6)
    u = fem.solve(*fem.condense(K, f, D=clamp))
    # applied force check
    fx, fy = f @ Ux, f @ Uy
    # stresses at quadrature points
    du = ib.interpolate(u)
    gu = du.grad                                                   # (2,2,nel,nq)
    exx, eyy = gu[0, 0], gu[1, 1]
    exy = 0.5 * (gu[0, 1] + gu[1, 0])
    c = E / (1 - nu ** 2)
    sxx = c * (exx + nu * eyy)
    syy = c * (eyy + nu * exx)
    sxy = E / (1 + nu) * exy
    s1 = 0.5 * (sxx + syy) + np.sqrt((0.5 * (sxx - syy)) ** 2 + sxy ** 2)
    s3 = 0.5 * (sxx + syy) - np.sqrt((0.5 * (sxx - syy)) ** 2 + sxy ** 2)
    xq = ib.global_coordinates().value                            # (2,nel,nq)
    # displacement at the load point along the load (interpolate nodal P1 part)
    px, py = lx + 0.03 * d[0], ly + 0.03 * d[1]           # just inside the flank (d points into the tooth)
    probe = ib.probes(np.array([[px], [py]]))
    uL = probe @ u
    return dict(mesh=m, basis=ib, u=u, s1=s1, s3=s3, xq=xq, u_load=np.array(uL).ravel(), f_applied=(fx, fy))


def hertz_half_width(wn, rho1, rho2, m1, m2):
    estar = 1 / ((1 - m1["nu"] ** 2) / m1["E"] + (1 - m2["nu"] ** 2) / m2["E"])
    req = rho1 * rho2 / (rho1 + rho2)
    return math.sqrt(4 * (wn / B_FACE) * req / (math.pi * estar)), estar


def flank_point(outline_arc, r_target, z, side=+1):
    """Point on the middle tooth's flank (the x>0 side for side=+1) at radius r_target, and the inward normal."""
    p = outline_arc
    r = np.hypot(p[:, 0], p[:, 1])
    th = np.arctan2(p[:, 1], p[:, 0])
    k = np.where((np.abs(th - math.pi / 2) < math.pi / z) & ((p[:, 0] * side) > 0) & (r > r.min() + 0.2))[0]
    i = k[np.argmin(np.abs(r[k] - r_target))]
    t = p[min(i + 1, len(p) - 1)] - p[max(i - 1, 0)]
    t /= np.linalg.norm(t)
    n = np.array([-t[1], t[0]])
    if np.dot(n, np.array([0.0, r_target]) - p[i]) < 0:      # point toward the tooth's centre line
        n = -n
    return p[i], n


def run_tooth(name, outline, z, r_in, cases, nu, rho_mate_fn):
    """Solve each load case once with E = 1 MPa; compliance scales as 1/E, stress does not depend on E."""
    import time
    coords, lo, hi, n_outer = sector(outline, z, r_in)
    res = {}
    for cname, r_load in cases.items():
        t0 = time.time()
        P, n = flank_point(coords[:n_outer], r_load, z, side=+1)
        wn = 10.0 / math.cos(C.PHI)                      # 10 N tangential at the pitch circle
        rho_s = math.sqrt(max(r_load ** 2 - (C.M * z / 2 * math.cos(C.PHI)) ** 2, 1e-6))
        bh, _ = hertz_half_width(wn, rho_s, rho_mate_fn(r_load), C.MAT["PETG (printed)"], C.MAT["PETG (printed)"])
        hw = max(bh, 0.03)
        rf = np.hypot(*coords[:n_outer].T).min()
        fill = [((r * math.cos(a), r * math.sin(a)), 0.012, 0.35) for r in (rf + 0.25,) for a in (math.pi / 2 - math.pi / z, math.pi / 2 + math.pi / z)]
        xy, tri = mesh_polygon(coords, n_outer, h=0.15, fine_pts=[(tuple(P), 0.006, 0.1)] + fill)
        sol = solve(xy, tri, 1.0, nu, P, n, wn, hw, r_in)
        xq = sol["xq"]
        rq = np.hypot(xq[0], xq[1])
        thq = np.arctan2(xq[1], xq[0])
        zone = (rq < rf + 1.0 * C.M) & (np.abs(thq - math.pi / 2) < 2 * math.pi / z) & (rq > rf - 1.5)
        res[cname] = dict(r_load_mm=round(r_load, 3), Wn_N=round(wn, 3), contact_half_width_mm=round(hw, 4),
                          root_tension_MPa=round(float(sol["s1"][zone].max()), 3),
                          root_compression_MPa=round(float(sol["s3"][zone].min()), 3),
                          defl_E1_mm=float(np.dot(sol["u_load"], n)), nodes=int(len(xy)), elements=int(len(tri)),
                          applied_check_N=round(float(np.hypot(*sol["f_applied"])), 3), solve_s=round(time.time() - t0, 1))
        res[cname]["_sol"] = sol
        res[cname]["_P"] = (P, n)
        print(name, cname, {k: v for k, v in res[cname].items() if not k.startswith("_")}, flush=True)
    return coords, res


def main():
    V.setup()
    import matplotlib.pyplot as plt
    import matplotlib.tri as mtri
    gg = json.loads((C.OUT / "gear_geometry.json").read_text())
    z_mid = sum(gg["face_z_mm"]) / 2
    gear = gear_outline_from_step(z_mid)
    pin = pinion_outline()
    a = C.A_DOCK
    pa = C.operating_pressure_angle(a)
    T1T2 = a * math.sin(pa)
    T1E = math.sqrt(C.RA1 ** 2 - C.RB1 ** 2)
    T2A = math.sqrt(C.RA2 ** 2 - C.RB2 ** 2)
    T1A = T1T2 - T2A
    hpstc_p = math.sqrt(C.RB1 ** 2 + (T1A + C.PB) ** 2)
    hpstc_g = math.sqrt(C.RB2 ** 2 + (T1T2 - (T1E - C.PB)) ** 2)
    rho_g = lambda r: T1T2 - math.sqrt(max(r ** 2 - C.RB1 ** 2, 0))        # mate's curvature radius at the same contact
    rho_p = lambda r: T1T2 - math.sqrt(max(r ** 2 - C.RB2 ** 2, 0))
    out = dict(centre_distance_mm=a, line_of_action=dict(T1T2=round(T1T2, 4), T1A=round(T1A, 4), T1E=round(T1E, 4),
                                                       hpstc_pinion_r=round(hpstc_p, 4), hpstc_gear_r=round(hpstc_g, 4)))
    teeth = {}
    figs = []
    for name, outline, z, r_in, cases, nu in (
            ("gear44", gear, C.Z2, 15.0, {"tip": C.RA2 - 0.06, "HPSTC": hpstc_g}, C.MAT["PETG (printed)"]["nu"]),
            ("pinion20", pin, C.Z1, 5.5, {"tip": C.RA1 - 0.06, "HPSTC": hpstc_p}, C.MAT["PETG (printed)"]["nu"]),
    ):
        coords, res = run_tooth(name, outline, z, r_in, cases, nu, rho_g if name == "pinion20" else rho_p)
        teeth[name] = res
        figs.append((name, coords, res["HPSTC"]))
    import shigley as S
    lewis = {"gear44": 10.0 / (C.FACE * C.M * S.lewis_Y(C.Z2)), "pinion20": 10.0 / (C.FACE * C.M * S.lewis_Y(C.Z1))}
    table = {}
    for name, res in teeth.items():
        t = {}
        for cname, d in res.items():
            dd = {k: v for k, v in d.items() if not k.startswith("_") and k != "defl_E1_mm"}
            for mat in ("PETG (printed)", "steel"):
                E = C.MAT[mat]["E"]
                defl_um = d["defl_E1_mm"] / E * 1000
                dd[f"compliance_um_per_N, {mat}"] = round(defl_um / d["Wn_N"], 5)
                dd[f"stiffness_N_per_um, {mat}"] = round(d["Wn_N"] / defl_um, 4)
            t[cname] = dd
        t["lewis_tip_MPa"] = round(lewis[name], 3)
        t["fea_tip_over_lewis"] = round(res["tip"]["root_tension_MPa"] / lewis[name], 3)
        table[name] = t

    def kpair(pin_mat):
        cp = table["pinion20"]["HPSTC"][f"compliance_um_per_N, {pin_mat}"] + table["gear44"]["HPSTC"]["compliance_um_per_N, PETG (printed)"]
        return 1.0 / cp
    out["mesh_stiffness_single_pair_N_per_um"] = {"PETG pinion / PETG gear": round(kpair("PETG (printed)"), 4),
                                                  "steel pinion / PETG gear": round(kpair("steel"), 4)}
    out["teeth"] = table
    out["note"] = ("plane stress, face 10 mm, load 10 N tangential (10.64 N normal) along the line of action over the PETG/PETG "
                   "Hertz width; three-tooth sectors clamped on an inner arc; compliance includes bending, shear, rim and local "
                   "contact deformation of each tooth; solved with E = 1 MPa and scaled")
    (C.OUT / "fea_tooth.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))

    # figure: max principal stress, PETG/PETG at HPSTC, both teeth
    fig, axs = plt.subplots(1, 2, figsize=(9.6, 4.6))
    for ax, (key, coords, r) in zip(axs, figs):
        sol = r["_sol"]
        m = sol["mesh"]
        ib = sol["basis"]
        # nodal max principal by projecting the quadrature values to P1
        import skfem as fem
        b1 = fem.Basis(m, fem.ElementTriP1())
        s1q = sol["s1"]
        s1n = fem.solve(fem.asm(fem.BilinearForm(lambda u, v, w: u * v), b1),
                        fem.asm(fem.LinearForm(lambda v, w: w["s"] * v), b1, s=b1.interpolate(np.zeros(b1.N)).value * 0 + _proj(ib, b1, s1q)))
        tr = mtri.Triangulation(m.p[0], m.p[1], m.t.T)
        lim = np.percentile(np.abs(s1n), 99.7)
        cs = ax.tripcolor(tr, s1n, shading="gouraud", cmap="RdBu_r", vmin=-lim, vmax=lim)
        P, n = r["_P"]
        ax.annotate("", xy=P, xytext=P - n * 1.6, arrowprops=dict(arrowstyle="-|>", color=V.INK, lw=1.2))
        ax.set_aspect("equal")
        ax.set_xlim(-3.2, 3.2)
        rr = np.hypot(*coords.T).max()
        ax.set_ylim(rr - 5.2, rr + 0.6)
        ax.set_title(("44T auger gear (STEP outline)" if key.startswith("gear") else "20T pinion") + ", load at HPSTC", fontsize=10)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.grid(False)
        cb = fig.colorbar(cs, ax=ax, shrink=0.8)
        cb.set_label("max principal stress (MPa), 10 N tangential")
    fig.tight_layout()
    fig.savefig(C.OUT / "fea_tooth_stress.png", dpi=150)
    plt.close(fig)


def _proj(ib, b1, q):
    """Quadrature values q (nel, nq) on ib's quadrature -> a DiscreteField-like array on b1's quadrature (same intorder assumed)."""
    if q.shape == b1.interpolate(np.zeros(b1.N)).value.shape:
        return q
    # different quadrature: average per element
    return np.repeat(q.mean(axis=1, keepdims=True), b1.interpolate(np.zeros(b1.N)).value.shape[1], axis=1)


if __name__ == "__main__":
    main()
