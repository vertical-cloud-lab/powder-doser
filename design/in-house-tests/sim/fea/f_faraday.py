"""FEA (f), test 10 Faraday cup: axisymmetric electrostatics (scikit-fem P2, gmsh mesh). Computed, not measured.

Geometry (r, z in mm; z = 0 is the top of the can floor):
  grounded can (shield)  ID 70, wall 1 mm (r 35-36, z -1..80), floor 1 mm (z -1..0)
  printed base (PLA)     r < 34.5, z 0-3                                  eps_r 3.0
  PTFE standoffs         three Ø8 x 10 at r = 12 -> equivalent ring r 11.15-12.85, z 3-13 (same volume), eps_r 2.1
  inner cup (electrode)  Ø40 x 50, wall 1 mm: r 19-20 for z 13-63, bottom z 13-14
  printed lid (PLA)      plate r 8.8-38, z 80-83; skirt r 33-34.8, z 74-80; re-entrant funnel shell
                         (4.8, 80)-(6, 80)-(10, 68)-(8.8, 68): clear inlet Ø9.6        eps_r 3.0
  exterior               air to a grounded box r = 150, z -60..260 (balance chamber, doser)
Case A: lid as printed (dielectric only). Case B: lid top face (and edge, and the overhang underside out to the
can) covered with grounded metal tape, so the aperture is the Ø17.6 hole of the plate.

Weak form: int eps_r grad(phi).grad(v) r dr dz = int (rho/eps0) v r dr dz. Capacitance from the energy:
C = 2 pi eps0 u^T K u (cup at 1 V, everything else at 0 V). Collection efficiency by Green reciprocity: a point
charge q at x induces -q phi_1(x) on the cup held at 0 V (charge amplifier), phi_1 = potential with the cup at 1 V.
"""
import json
import math
import sys
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.tri as mtri
from matplotlib.path import Path as MPath
import numpy as np
import skfem
from skfem import BilinearForm, LinearForm, MeshTri, Basis, ElementTriP2, ElementTriP0, asm, condense, solve
from skfem.helpers import dot, grad

from fea_common import HERE, PAL, INK, INK2, style, save_json

EPS0 = 8.8541878128e-15        # F/mm
EPS = {"air": 1.0, "pla": 3.0, "ptfe": 2.1, "heap": 1.0}
FUNNEL = [(4.8, 80.0), (6.0, 80.0), (10.0, 68.0), (8.8, 68.0)]
Z_OUTLET = 98.0                # doser outlet: 15 mm above the lid top (z 83)
Q_HEAP = 100e-9                # C, top of SPEC's 1-100 nC range
HEAP = (15.0, 14.0, 17.0)      # r_max, z0, z1
TOL = 1e-6
OUT = HERE / "results"
OUT.mkdir(exist_ok=True)


# ----------------------------------------------------------------------------------------------
# meshes
# ----------------------------------------------------------------------------------------------
def gmsh_to_skfem(gmsh):
    ntags, coords, _ = gmsh.model.mesh.getNodes()
    xy = coords.reshape(-1, 3)[:, :2]
    idx = {int(t): i for i, t in enumerate(ntags)}
    tris = []
    for d, ent in gmsh.model.getEntities(2):
        et, _, en = gmsh.model.mesh.getElements(2, ent)
        for t, e in zip(et, en):
            if t == 2:
                tris.append(np.asarray(e, dtype=np.int64).reshape(-1, 3))
    tri = np.vectorize(idx.get)(np.vstack(tris))
    used = np.unique(tri)
    remap = -np.ones(len(xy), dtype=np.int64)
    remap[used] = np.arange(len(used))
    return MeshTri(np.ascontiguousarray(xy[used].T), np.ascontiguousarray(remap[tri].T))


def cup_mesh(h_in, h_inlet, h_out):
    import gmsh
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 0)
    occ = gmsh.model.occ
    outer = occ.addRectangle(0, -60, 0, 150, 320)
    tools = [occ.addRectangle(35, -1, 0, 1, 81), occ.addRectangle(0, -1, 0, 36, 1),     # can
             occ.addRectangle(19, 13, 0, 1, 50), occ.addRectangle(0, 13, 0, 20, 1)]      # cup
    dom, _ = occ.cut([(2, outer)], [(2, t) for t in tools])
    pts = [occ.addPoint(r, z, 0) for r, z in FUNNEL]
    lines = [occ.addLine(pts[i], pts[(i + 1) % 4]) for i in range(4)]
    funnel = occ.addPlaneSurface([occ.addCurveLoop(lines)])
    parts = [occ.addRectangle(0, 0, 0, 34.5, 3), occ.addRectangle(11.15, 3, 0, 1.7, 10),
             occ.addRectangle(8.8, 80, 0, 29.2, 3), occ.addRectangle(33, 74, 0, 1.8, 6), funnel,
             occ.addRectangle(0, HEAP[1], 0, HEAP[0], HEAP[2] - HEAP[1])]
    occ.fragment(dom, [(2, t) for t in parts])
    occ.synchronize()
    f1 = gmsh.model.mesh.field.add("Box")
    for k, v in dict(VIn=h_in, VOut=h_out, XMin=0, XMax=42, YMin=-4, YMax=105, Thickness=40).items():
        gmsh.model.mesh.field.setNumber(f1, k, v)
    f2 = gmsh.model.mesh.field.add("Box")
    for k, v in dict(VIn=h_inlet, VOut=h_out, XMin=0, XMax=16, YMin=58, YMax=105, Thickness=10).items():
        gmsh.model.mesh.field.setNumber(f2, k, v)
    f3 = gmsh.model.mesh.field.add("Min")
    gmsh.model.mesh.field.setNumbers(f3, "FieldsList", [f1, f2])
    gmsh.model.mesh.field.setAsBackgroundMesh(f3)
    gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 0)
    gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 0)
    gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 0)
    gmsh.option.setNumber("Mesh.Algorithm", 6)
    gmsh.model.mesh.generate(2)
    m = gmsh_to_skfem(gmsh)
    gmsh.finalize()
    return m


def labels_of(mesh):
    c = mesh.p[:, mesh.t].mean(axis=1)
    r, z = c
    lab = np.full(mesh.t.shape[1], "air", dtype=object)
    lab[(r < 34.5) & (z > 0) & (z < 3)] = "pla"
    lab[(r > 11.15) & (r < 12.85) & (z > 3) & (z < 13)] = "ptfe"
    lab[(r > 8.8) & (r < 38) & (z > 80) & (z < 83)] = "pla"
    lab[(r > 33) & (r < 34.8) & (z > 74) & (z < 80)] = "pla"
    lab[MPath(FUNNEL).contains_points(c.T)] = "pla"
    lab[(r < HEAP[0]) & (z > HEAP[1]) & (z < HEAP[2])] = "heap"
    return lab


def dof_sets(basis):
    r, z = basis.doflocs
    t = TOL
    can = (((abs(r - 35) < t) & (z >= -t) & (z <= 80 + t)) | ((abs(r - 36) < t) & (z >= -1 - t) & (z <= 80 + t))
           | ((abs(z - 80) < t) & (r >= 35 - t) & (r <= 36 + t)) | ((abs(z) < t) & (r <= 35 + t))
           | ((abs(z + 1) < t) & (r <= 36 + t)))
    outer = (abs(r - 150) < t) | (abs(z + 60) < t) | (abs(z - 260) < t)
    cup = (((abs(z - 13) < t) & (r <= 20 + t)) | ((abs(r - 20) < t) & (z >= 13 - t) & (z <= 63 + t))
           | ((abs(z - 63) < t) & (r >= 19 - t) & (r <= 20 + t)) | ((abs(r - 19) < t) & (z >= 14 - t) & (z <= 63 + t))
           | ((abs(z - 14) < t) & (r <= 19 + t)))
    tape = (((abs(z - 83) < t) & (r >= 8.8 - t) & (r <= 38 + t)) | ((abs(r - 38) < t) & (z >= 80 - t) & (z <= 83 + t))
            | ((abs(z - 80) < t) & (r >= 36 - t) & (r <= 38 + t)))
    return dict(can=np.where(can)[0], outer=np.where(outer)[0], cup=np.where(cup)[0], tape=np.where(tape)[0])


@BilinearForm
def a_form(u, v, w):
    return w["eps"] * dot(grad(u), grad(v)) * w.x[0]


@LinearForm
def l_form(v, w):
    return w["rho"] * v * w.x[0]


class Model:
    def __init__(self, mesh, eps=EPS):
        self.mesh = mesh
        self.lab = labels_of(mesh)
        self.basis = Basis(mesh, ElementTriP2())
        self.b0 = self.basis.with_element(ElementTriP0())
        epsr = np.array([eps[l] for l in self.lab], dtype=float)
        self.K = asm(a_form, self.basis, eps=self.b0.interpolate(epsr))
        self.sets = dof_sets(self.basis)
        self.N = self.basis.N

    def solve(self, case, cup_v=1.0, rho_heap=0.0):
        D = np.concatenate([self.sets["can"], self.sets["outer"], self.sets["cup"]]
                           + ([self.sets["tape"]] if case == "B" else []))
        D = np.unique(D)
        x0 = np.zeros(self.N)
        x0[self.sets["cup"]] = cup_v
        rho = np.where(self.lab == "heap", rho_heap, 0.0)
        f = asm(l_form, self.basis, rho=self.b0.interpolate(rho)) if rho_heap else np.zeros(self.N)
        return solve(*condense(self.K, f, x=x0, D=D))

    def capacitance(self, u):
        return 2 * math.pi * EPS0 * float(u @ (self.K @ u))

    def probe(self, u, r, z):
        P = self.basis.probes(np.vstack([np.asarray(r, float), np.asarray(z, float)]))
        return P @ u

    def field(self, u):
        g = self.basis.interpolate(u).grad
        return np.sqrt(g[0] ** 2 + g[1] ** 2) * 1e3  # V/m


# ----------------------------------------------------------------------------------------------
# validation: concentric spheres (a 10, b 30 mm)
# ----------------------------------------------------------------------------------------------
def spheres(h, a=10.0, b=30.0):
    import gmsh
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 0)
    occ = gmsh.model.occ
    d1, d2 = occ.addDisk(0, 0, 0, b, b), occ.addDisk(0, 0, 0, a, a)
    ann, _ = occ.cut([(2, d1)], [(2, d2)])
    half, _ = occ.intersect(ann, [(2, occ.addRectangle(0, -b - 1, 0, b + 1, 2 * b + 2))])
    occ.synchronize()
    gmsh.option.setNumber("Mesh.MeshSizeMax", h)
    gmsh.option.setNumber("Mesh.MeshSizeMin", h / 3)
    gmsh.model.mesh.generate(2)
    m = gmsh_to_skfem(gmsh)
    gmsh.finalize()
    basis = Basis(m, ElementTriP2())
    b0 = basis.with_element(ElementTriP0())
    K = asm(a_form, basis, eps=b0.interpolate(np.ones(m.t.shape[1])))
    rr = np.hypot(*basis.doflocs)
    inner = np.where(np.abs(rr - a) < 1e-3 * a)[0]
    outer = np.where(np.abs(rr - b) < 1e-3 * b)[0]
    # straight-sided triangles: boundary dofs at facet midpoints sit slightly inside the circle; pick them by
    # the boundary facets instead
    bf = m.boundary_facets()
    fm = m.p[:, m.facets[:, bf]].mean(axis=1)
    rf = np.hypot(*fm)
    fin = bf[np.abs(rf - a) < 0.05 * a]
    fout = bf[np.abs(rf - b) < 0.05 * b]
    inner = basis.get_dofs(facets=fin).all()
    outer = basis.get_dofs(facets=fout).all()
    x0 = np.zeros(basis.N)
    x0[inner] = 1.0
    u = solve(*condense(K, np.zeros(basis.N), x=x0, D=np.union1d(inner, outer)))
    C = 2 * math.pi * EPS0 * float(u @ (K @ u))
    C_exact = 4 * math.pi * EPS0 * a * b / (b - a)
    return dict(h=h, dofs=basis.N, C_pF=C * 1e12, C_exact_pF=C_exact * 1e12, rel_err=C / C_exact - 1)


# ----------------------------------------------------------------------------------------------
# main
# ----------------------------------------------------------------------------------------------
def crossing(z, eta, level):
    """Highest z (coming down from above) where eta reaches level."""
    above = eta >= level
    if not above.any():
        return None
    i = int(np.argmax(above))          # z is sorted descending
    if i == 0:
        return float(z[0])
    z0, z1, e0, e1 = z[i - 1], z[i], eta[i - 1], eta[i]
    return float(z0 + (level - e0) * (z1 - z0) / (e1 - e0))


def main():
    t0 = time.time()
    res = dict(note="computed, not measured; units mm, pF, V/m", eps=EPS,
               assumptions=dict(ptfe="three Ø8 x 10 standoffs at r 12 -> ring r 11.15-12.85 (same volume)",
                                heap=f"Q = {Q_HEAP * 1e9:.0f} nC uniform in r < 15, z 14-17 (eps_r 1)",
                                outlet_z=Z_OUTLET, exterior="grounded box r 150, z -60..260"))
    # validation
    res["validation_spheres"] = [spheres(h) for h in (4.0, 2.0, 1.0)]
    print("spheres", [(v["dofs"], round(v["C_pF"], 5), f"{v['rel_err']:.2e}") for v in res["validation_spheres"]],
          flush=True)
    # convergence on the cup
    levels = [(2.0, 1.0, 10.0), (1.2, 0.6, 6.0), (0.72, 0.36, 3.6)]
    conv, models = [], []
    for h in levels:
        m = cup_mesh(*h)
        M = Model(m)
        row = dict(h_in=h[0], h_inlet=h[1], h_out=h[2], elements=m.t.shape[1], dofs=M.N)
        for case in ("A", "B"):
            u = M.solve(case)
            row[f"C_{case}_pF"] = M.capacitance(u) * 1e12
            e = M.probe(u, [0, 0], [70.0, Z_OUTLET])
            row[f"eta_{case}_z70"], row[f"eta_{case}_z98"] = float(e[0]), float(e[1])
        conv.append(row)
        models.append(M)
        print("conv", row, round(time.time() - t0, 1), flush=True)
    res["convergence"] = conv
    M = models[-1]
    # finest mesh: profiles and derived numbers
    zs = np.linspace(250.0, 14.5, 2400)
    prof = {}
    sol = {}
    for case in ("A", "B"):
        u = M.solve(case)
        sol[case] = u
        prof[case] = {f"r{r:g}": M.probe(u, np.full_like(zs, r), zs) for r in (0.0, 4.0, 8.0)}
    lv = [0.99, 0.9, 0.5, 0.1, 0.01]
    res["eta_levels_z_mm"] = {c: {f"r{r:g}": {str(l): crossing(zs, prof[c][f"r{r:g}"], l) for l in lv}
                                  for r in (0.0, 4.0, 8.0)} for c in ("A", "B")}
    zq = [150.0, 130.0, 110.0, Z_OUTLET, 90.0, 83.0, 80.0, 75.0, 70.0, 63.0, 55.0, 40.0]
    res["eta_at"] = {c: {f"r{r:g}": dict(zip(map(str, zq), map(float, M.probe(sol[c], np.full(len(zq), r), zq))))
                         for r in (0.0, 4.0, 8.0, 12.5)} for c in ("A", "B")}
    res["C_pF"] = {c: conv[-1][f"C_{c}_pF"] for c in ("A", "B")}
    # grains on the heap, and grains stuck on the inside of the printed funnel (charge counted, mass not weighed)
    res["eta_heap_axis"] = {c: dict(zip(("z17", "z20", "z30"), map(float, M.probe(sol[c], [0, 0, 0], [17.0, 20.0, 30.0]))))
                            for c in ("A", "B")}
    fz = np.array([76.0, 72.0, 68.5])
    fr = 4.8 + (80.0 - fz) / 3.0 - 0.05
    res["eta_funnel_inner_surface"] = {c: {f"z{z:g}_r{r:.2f}": float(v) for z, r, v in zip(fz, fr, M.probe(sol[c], fr, fz))}
                                       for c in ("A", "B")}
    # external charge (auger tip / tube rim), induced charge per nC (sign: opposite)
    ext = {}
    for c in ("A", "B"):
        ext[c] = {f"z{z:g}": {"axis_nC_per_nC": float(M.probe(sol[c], [0.0], [z])[0]),
                              "ring_r12.5_nC_per_nC": float(M.probe(sol[c], [12.5], [z])[0])}
                  for z in (98.0, 110.0, 130.0, 150.0)}
    res["external_charge_induced_fraction"] = ext
    res["shielding_factor_A_over_B"] = {k: ext["A"][k]["axis_nC_per_nC"] / ext["B"][k]["axis_nC_per_nC"]
                                        for k in ext["A"]}
    # read-out rule: last grain from the outlet at 1 m/s to eta = 0.99 on the axis and at r = 8
    rd = {}
    for c in ("A", "B"):
        z99 = min(v for v in (res["eta_levels_z_mm"][c]["r0"]["0.99"], res["eta_levels_z_mm"][c]["r8"]["0.99"]) if v)
        rd[c] = dict(z_eta99_worst_mm=z99, t_ms_at_1m_s=(Z_OUTLET - z99) / 1.0)
    res["readout"] = rd
    # field from the collected charge (cup at 0 V: charge amplifier)
    vol = math.pi * HEAP[0] ** 2 * (HEAP[2] - HEAP[1])
    rho = Q_HEAP / vol / EPS0          # V/mm^2
    fld = {}
    for c in ("A", "B"):
        u = M.solve(c, cup_v=0.0, rho_heap=rho)
        E = M.field(u)
        air = M.lab == "air"
        heap = M.lab == "heap"
        ez = M.probe(u, [0.0, 0.0], [79.95, 80.05])
        E_in = abs(ez[1] - ez[0]) / 0.1 * 1e3
        e_air = float(E[air].max())
        fld[c] = dict(E_inlet_V_m=E_in, E_max_air_V_m=e_air, E_max_heap_V_m=float(E[heap].max()),
                      Q_for_3MV_m_nC=Q_HEAP * 1e9 * 3e6 / e_air,
                      qE_over_mg_inlet_q_m_1em4=1e-4 * E_in / 9.81)
        # where is the max in air
        k = np.unravel_index(np.argmax(np.where(air[:, None], E, 0)), E.shape)
        xq = M.basis.mapping.F(M.basis.quadrature[0])
        fld[c]["E_max_air_at_rz"] = [float(xq[0][k]), float(xq[1][k])]
    res["field_from_collected_charge"] = fld
    Cb = res["C_pF"]["B"] * 1e-12
    res["voltage_mode_V_at_100nC"] = Q_HEAP / (Cb + 100e-12)
    # hand check
    co = 2 * math.pi * 8.8541878128e-12 * 0.050 / math.log(35.0 / 20.0)
    a_bot = math.pi * 0.020 ** 2
    a_ptfe = 2 * math.pi * 0.012 * 0.0017
    d_air, d_pla = 0.010, 0.003
    c_bot = 8.8541878128e-12 * ((a_bot - a_ptfe) / (d_air + d_pla / 3.0) + a_ptfe / (d_air / 2.1 + d_pla / 3.0))
    res["hand_check"] = dict(coax_side_pF=co * 1e12, bottom_pF=c_bot * 1e12, sum_pF=(co + c_bot) * 1e12,
                             fringe_A_pF=res["C_pF"]["A"] - (co + c_bot) * 1e12,
                             fringe_B_pF=res["C_pF"]["B"] - (co + c_bot) * 1e12)
    res["runtime_s"] = time.time() - t0
    save_json(OUT / "f_faraday.json", res)
    print(json.dumps({k: res[k] for k in ("C_pF", "hand_check", "eta_levels_z_mm", "readout", "field_from_collected_charge",
                                          "shielding_factor_A_over_B", "voltage_mode_V_at_100nC")}, indent=1, default=str),
          flush=True)
    figure(M, sol, zs, prof, res)
    print("done", round(time.time() - t0, 1))


def figure(M, sol, zs, prof, res):
    fig, axs = plt.subplots(1, 3, figsize=(14.5, 5.2), gridspec_kw=dict(width_ratios=[1.05, 1.2, 1.0]))
    ax = axs[0]
    m = M.mesh
    nv = m.p.shape[1]
    uB = sol["B"][:nv]
    tri = mtri.Triangulation(np.concatenate([m.p[0], -m.p[0]]), np.concatenate([m.p[1], m.p[1]]),
                             np.vstack([m.t.T, m.t.T + nv]))
    lev = [0.01, 0.03, 0.1, 0.3, 0.5, 0.7, 0.9, 0.97, 0.99]
    cs = ax.tricontour(tri, np.concatenate([uB, uB]), levels=lev, colors=[PAL[0]], linewidths=1.0)
    ax.clabel(cs, fmt="%.2f", fontsize=6, inline=True)
    rects = [((35, -1), 1, 81, "#4d4d4d"), ((0, -1), 36, 1, "#4d4d4d"), ((19, 13), 1, 50, "#b35900"),
             ((0, 13), 20, 1, "#b35900"), ((0, 0), 34.5, 3, "#d9d9d9"), ((11.15, 3), 1.7, 10, "#cfe8ff"),
             ((8.8, 80), 29.2, 3, "#d9d9d9"), ((33, 74), 1.8, 6, "#d9d9d9"), ((8.8, 83), 29.2, 0.6, "#4d4d4d")]
    for s in (1, -1):
        for (x, y), w, h, col in rects:
            x0 = x if s == 1 else -(x + w)
            ax.add_patch(plt.Rectangle((x0, y), w, h, color=col, lw=0))
        ax.add_patch(plt.Polygon([(s * r, z) for r, z in FUNNEL], color="#d9d9d9", lw=0))
    ax.set_xlim(-50, 50)
    ax.set_ylim(-5, 120)
    ax.set_aspect("equal")
    ax.axhline(Z_OUTLET, color=INK2, lw=0.8, ls=":")
    ax.text(-48, Z_OUTLET + 2, "doser outlet", color=INK2, fontsize=7)
    style(ax, "Case B (grounded lid): equipotentials, cup at 1 V", "r (mm)", "z (mm)")
    ax.text(21, 40, "inner cup", color="#b35900", fontsize=7, rotation=90)
    ax.text(37, 30, "can", color="#4d4d4d", fontsize=7, rotation=90)
    ax = axs[1]
    for c, col, nm in (("A", PAL[1], "A: printed lid"), ("B", PAL[0], "B: lid top grounded")):
        ax.semilogy(zs, np.clip(prof[c]["r0"], 1e-6, None), color=col, lw=2, label=f"{nm}, axis")
        ax.semilogy(zs, np.clip(prof[c]["r8"], 1e-6, None), color=col, lw=1.2, ls="--", label=f"{nm}, r = 8 mm")
    for zz, t in ((63, "cup rim"), (83, "lid top"), (Z_OUTLET, "outlet")):
        ax.axvline(zz, color=INK2, lw=0.8, ls=":")
        ax.text(zz + 1, 1.3e-4, t, color=INK2, fontsize=7, rotation=90, va="bottom")
    ax.set_ylim(1e-4, 1.5)
    ax.set_xlim(10, 220)
    style(ax, "Collection efficiency η(z): share of a grain's charge seen by the cup", "height z (mm)", "η")
    ax.legend(frameon=False, fontsize=7, loc="upper right")
    ax = axs[2]
    conv = res["convergence"]
    d = [c["dofs"] for c in conv]
    for c, col in (("A", PAL[1]), ("B", PAL[0])):
        ref = conv[-1][f"C_{c}_pF"]
        ax.loglog(d[:-1], [abs(x[f"C_{c}_pF"] / ref - 1) for x in conv[:-1]], "o-", color=col, lw=2, ms=7,
                  label=f"cup C, case {c} (vs finest)")
    sp = res["validation_spheres"]
    ax.loglog([s["dofs"] for s in sp], [abs(s["rel_err"]) for s in sp], "s-", color=PAL[2], lw=2, ms=7,
              label="concentric spheres (vs exact)")
    style(ax, "Mesh convergence: capacitance", "degrees of freedom", "relative error")
    ax.legend(frameon=False, fontsize=7)
    fig.tight_layout()
    fig.savefig(HERE / "f_faraday.png", dpi=150)


if __name__ == "__main__":
    main()
