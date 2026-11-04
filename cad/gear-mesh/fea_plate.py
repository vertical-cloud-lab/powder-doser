"""3D FEA of Sam's Oct 13 mounting plate under the docked loads (gmsh tets + scikit-fem, quadratic).

The magnet pulls the steel tab (two M3 screws in the plate's back strip) down onto the carriage,
the carriage rim holds the plate up at its four pads, the hinge pins hold the knuckles, and the
gear's separating force pushes the auger up in the two clamp rings beside the gear. The question:
how far does the plate bend, and does it move the gear (the centre distance)?

    python fea_plate.py
Writes out/fea_plate.json and out/fea_plate_deflection.png.
"""
from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path

import numpy as np

import common as C
import vizstyle as V

HERE = Path(__file__).resolve().parent
TMP = Path("/tmp/gear-mesh-fea")
TMP.mkdir(exist_ok=True)


def plate_step() -> Path:
    sys.path.insert(0, str(HERE.parent / "paternoster"))
    from step_io import read_step_parts
    import cadquery as cq
    p = TMP / "plate.step"
    if not p.exists():
        sam = read_step_parts(HERE.parent / "paternoster" / "reference" / "sam-oct13-mounting-plate-and-carriage.step")
        cq.exporters.export(cq.Workplane().add(sam["Mounting Plate"]), str(p))
    return p


def mesh(h=1.6, h_fine=0.7):
    import gmsh
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 0)
    gmsh.model.add("plate")
    gmsh.model.occ.importShapes(str(plate_step()))
    gmsh.model.occ.synchronize()
    gmsh.option.setNumber("Mesh.MeshSizeMax", h)
    gmsh.option.setNumber("Mesh.MeshSizeMin", h_fine)
    gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 12)
    gmsh.option.setNumber("Mesh.Algorithm3D", 1)
    gmsh.model.mesh.generate(3)
    nt, nc, _ = gmsh.model.mesh.getNodes()
    et, etags, enodes = gmsh.model.mesh.getElements(3)
    gmsh.finalize()
    xyz = nc.reshape(-1, 3)
    idx = {t: i for i, t in enumerate(nt)}
    k = [i for i, t in enumerate(et) if t == 4][0]                 # 4-node tets
    tet = np.array([idx[t] for t in enodes[k]]).reshape(-1, 4)
    used = np.unique(tet)
    remap = -np.ones(len(xyz), int)
    remap[used] = np.arange(len(used))
    return xyz[used], remap[tet]


def solve(f_mag=12.0, f_sep=5.5, w_mod=0.99, E=2000.0, nu=0.38):
    import skfem as fem
    from skfem.models.elasticity import lame_parameters, linear_elasticity
    t0 = time.time()
    xyz, tet = mesh()
    m = fem.MeshTet(xyz.T.copy(), tet.T.copy())
    e = fem.ElementVector(fem.ElementTetP2())
    ib = fem.Basis(m, e, intorder=3)
    lam, mu = lame_parameters(E, nu)
    K = fem.asm(linear_elasticity(lam, mu), ib)
    X = ib.doflocs                                                # (3, ndofs) dof coordinates (each dof: x/y/z comp)
    ndof = ib.N
    f = np.zeros(ndof)
    comp = np.tile([0, 1, 2], ndof // 3) if False else None
    # dof component index: skfem orders ElementVector dofs as interleaved per node? use nodal_dofs/facet etc.
    def dofs_where(pred, c):
        """Global dofs of component c whose location satisfies pred(x, y, z)."""
        out = []
        for arr in (ib.nodal_dofs, ib.edge_dofs) if hasattr(ib, "edge_dofs") else (ib.nodal_dofs,):
            if arr.size == 0:
                continue
            d = arr[c]
            loc = X[:, d]
            k = pred(loc[0], loc[1], loc[2])
            out.append(d[k])
        return np.concatenate(out) if out else np.array([], int)

    zb = -18.0
    # rim pads: z fixed on the underside over x 25-29 and 69.3-73.3, |y| 14-18
    pad = lambda x, y, z: (np.abs(z - zb) < 0.3) & (((x > 25) & (x < 29)) | ((x > 69.3) & (x < 73.3))) & (np.abs(y) > 14) & (np.abs(y) < 18)
    D_pad = dofs_where(pad, 2)
    # hinge: knuckle bores (r 2.65 about the y axis at x = z = 0), all components fixed on the bore surface
    bore = lambda x, y, z: (np.hypot(x, z) < 2.9) & (np.abs(y) > 14.5)
    D_h = np.concatenate([dofs_where(bore, c) for c in (0, 1, 2)])
    # rigid-body x/y: the bores take them
    D = np.unique(np.concatenate([D_pad, D_h]))
    # loads (nodal, spread over patches): magnet at the two screw bosses (x 94, y +-10, underside), down
    def spread(pred, c, F):
        d = dofs_where(pred, c)
        if len(d):
            f[d] += F / len(d)
        return len(d)
    n1 = spread(lambda x, y, z: (np.abs(z - zb) < 0.3) & (np.hypot(x - 94.0, np.abs(y) - 10.0) < 3.0), 2, -f_mag)
    # gear separating force: up, on the clamp ring seats (auger tube r 12.5) at x 68.8-78.7 and 88.8-98.8, lower half
    seat = lambda x, y, z: (np.abs(np.hypot(y, z) - 12.5) < 0.6) & (z < -4.0) & (((x > 68.8) & (x < 78.7)) | ((x > 88.8) & (x < 98.8)))
    n2 = spread(seat, 2, +f_sep)
    # the module's weight (auger + powder resting in the clamps), down at the same seats
    n3 = spread(seat, 2, -w_mod)
    u = fem.solve(*fem.condense(K, f, D=D))
    # displacement of the clamp-ring seats (the auger axis) and the screw bosses
    def mean_u(pred, c):
        d = dofs_where(pred, c)
        return float(u[d].mean()) if len(d) else float("nan")
    gear_seat_dz = mean_u(seat, 2)
    boss_dz = mean_u(lambda x, y, z: (np.abs(z - zb) < 0.3) & (np.hypot(x - 94.0, np.abs(y) - 10.0) < 3.0), 2)
    back_end_dz = mean_u(lambda x, y, z: (x > 97.5) & (np.abs(z - zb) < 0.3), 2)
    # von Mises at quadrature points
    du = ib.interpolate(u)
    g = du.grad
    eps = 0.5 * (g + np.transpose(g, (1, 0, 2, 3)))
    tr = eps[0, 0] + eps[1, 1] + eps[2, 2]
    s = 2 * mu * eps
    for i in range(3):
        s[i, i] += lam * tr
    vm = np.sqrt(0.5 * ((s[0, 0] - s[1, 1]) ** 2 + (s[1, 1] - s[2, 2]) ** 2 + (s[2, 2] - s[0, 0]) ** 2) + 3 * (s[0, 1] ** 2 + s[1, 2] ** 2 + s[0, 2] ** 2))
    res = dict(f_mag_N=f_mag, f_sep_N=f_sep, E_MPa=E, nodes=int(m.p.shape[1]), tets=int(m.t.shape[1]), dofs=int(ndof),
               loaded_dofs=dict(magnet=n1, seat=n2), fixed_dofs=int(len(D)),
               gear_seat_dz_um=round(gear_seat_dz * 1000, 2), screw_boss_dz_um=round(boss_dz * 1000, 2),
               back_end_dz_um=round(back_end_dz * 1000, 2), max_von_mises_MPa=round(float(np.percentile(vm, 99.9)), 3),
               wall_s=round(time.time() - t0, 1))
    return res, (m, ib, u)


def main():
    out = {}
    for name, fm, fs in (("magnet only (12 N)", 12.0, 0.0), ("magnet + stall separating force", 12.0, 5.5),
                         ("magnet 20 N (touching) + stall", 20.0, 5.5), ("no magnet, stall separating force", 0.0, 5.5)):
        r, sol = solve(fm, fs)
        out[name] = r
        print(name, r, flush=True)
        if name == "magnet + stall separating force":
            keep = sol
    out["note"] = ("PETG E 2000 MPa (printed, conservative for the 5 mm plate's perimeters); z fixed at the carriage rim pads, "
                   "knuckle bores pinned; loads as nodal patches. Negative dz = toward the carriage (closes the gear "
                   "centre distance); the gear seat dz is the mean over the two clamp rings beside the gear")
    (C.OUT / "fea_plate.json").write_text(json.dumps(out, indent=1))
    # figure: z displacement on the underside, plan view
    V.setup()
    import matplotlib.pyplot as plt
    import matplotlib.tri as mtri
    m, ib, u = keep
    import skfem as fem
    zcomp = u[ib.nodal_dofs[2]]
    P = m.p
    bot = np.abs(P[2] - (-18.0)) < 0.3
    fig, ax = plt.subplots(figsize=(7.8, 3.8))
    tr = mtri.Triangulation(P[0, bot], P[1, bot])
    xy = np.c_[P[0, bot], P[1, bot]]
    edge = np.max([np.hypot(*(xy[tr.triangles[:, i]] - xy[tr.triangles[:, (i + 1) % 3]]).T) for i in range(3)], axis=0)
    tr.set_mask(edge > 4.0)                                       # don't paint across the gear window
    cs = ax.tricontourf(tr, zcomp[bot] * 1000, levels=18, cmap="Blues_r")
    ax.set_aspect("equal")
    ax.set_xlabel("Sam's x from the hinge (mm)")
    ax.set_ylabel("y (mm)")
    ax.set_title("Sam's plate, underside: z deflection under the magnet (12 N) and the stall separating force (5.5 N)", fontsize=9.5)
    cb = fig.colorbar(cs, ax=ax, shrink=0.85)
    cb.set_label("z (µm), negative = toward the carriage")
    fig.tight_layout()
    fig.savefig(C.OUT / "fea_plate_deflection.png", dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    main()
