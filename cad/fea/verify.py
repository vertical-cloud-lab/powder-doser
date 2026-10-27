"""Check the pipeline (gmsh C3D10 -> CalculiX -> reader) against hand solutions before trusting it on the parts.

    python verify.py            -> out/verify.json

1. Cantilever 20 x 20 x 200 mm steel bar, 100 N at the tip: Timoshenko deflection and the bending stress at
   mid-span, at three mesh sizes (convergence).
2. The same bar's first two bending frequencies (Euler-Bernoulli, with the Timoshenko correction).
3. A 1/4 in 6061 strip cantilever, 200 x 50 mm, with 1, 2 and 3 elements through the thickness: how coarse
   can the side plates be meshed.
4. The 2020 extrusion as drawn in the CAD (parts.extrusion_2020): its area and second moment from the CAD's
   section, its bending and torsional stiffness from CalculiX (100 mm bar), against the catalogue's 0.72 cm^4;
   then the equivalent solid bar (materials.equivalent_bar) used in the frame models must give the same tip
   deflection and twist.
5. Euler buckling of a pinned 6 mm steel rod (the *BUCKLE step).
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

import fem
import materials as MAT

OUT = fem.HERE / "out"


def box(x, y, z, dx, dy, dz):
    return lambda g: [g.model.occ.addBox(x, y, z, dx, dy, dz)]


def cantilever(h: float, L=200.0, b=20.0, P=100.0):
    m = fem.mesh_parts([fem.Part("bar", box(0, -b / 2, -b / 2, L, b, b), material="STEEL1018")], size=h, size_min=h / 2, curv=0)
    d = fem.Deck(m)
    d.fix(m.nodes_where(lambda p: p[:, 0] < 1e-6), name="ROOT")
    r, q = d.rigid_patch(m.nodes_where(lambda p: p[:, 0] > L - 1e-6), "TIP", at=(L, 0, 0))
    d.node_load(r, F=(0, 0, -P))
    d.print_reactions("ROOT")
    res = d.solve(f"verify/cant_h{h}")
    E, nu = MAT.get("STEEL1018").E, MAT.get("STEEL1018").nu
    I = b ** 4 / 12
    G = E / (2 * (1 + nu))
    exact = P * L ** 3 / (3 * E * I) + P * L / (5 / 6 * G * b * b)
    tip = -res.rigid_disp("TIP")[2]
    # bending stress at mid-span on the top fibre: sigma_x = M c / I
    k = m.nodes_where(lambda p: (abs(p[:, 0] - L / 2) < h * 0.6) & (p[:, 2] > b / 2 - 1e-6) & (abs(p[:, 1]) < b / 4))
    sx = float(np.mean(res.S[k, 0]))
    return dict(h=h, nodes=m.n, elems=len(m.tet), tip_mm=tip, exact_mm=exact, err_pct=100 * (tip / exact - 1),
                sx_mid_MPa=sx, sx_exact_MPa=P * L / 2 * (b / 2) / I, rf_z=float(res.reactions("ROOT")[2]), wall_s=res.wall)


def cantilever_modes(h=5.0, L=200.0, b=20.0):
    m = fem.mesh_parts([fem.Part("bar", box(0, -b / 2, -b / 2, L, b, b), material="STEEL1018")], size=h, size_min=h / 2, curv=0)
    d = fem.Deck(m)
    d.fix(m.nodes_where(lambda p: p[:, 0] < 1e-6))
    d.frequency(6)
    res = d.solve("verify/cant_modes")
    mt = MAT.get("STEEL1018")
    I, A = b ** 4 / 12, b * b
    base = math.sqrt(mt.E * I / (mt.rho * A * L ** 4)) / (2 * math.pi)
    eb = [1.8751 ** 2 * base, 4.6941 ** 2 * base]
    return dict(h=h, fem_Hz=res.freqs[:6], euler_bernoulli_Hz=eb,
                note="modes 1-2 bend (two equal planes), mode 3-4 second bending or torsion; EB ignores shear and rotary inertia")


def strip(n_thick: int, L=200.0, b=50.0, t=6.35, P=20.0):
    h = t / n_thick
    m = fem.mesh_parts([fem.Part("strip", box(0, -b / 2, 0, L, b, t), material="AL6061")], size=max(h * 1.6, 2.0), size_min=h, curv=0)
    d = fem.Deck(m)
    d.fix(m.nodes_where(lambda p: p[:, 0] < 1e-6))
    r, q = d.rigid_patch(m.nodes_where(lambda p: p[:, 0] > L - 1e-6), "TIP", at=(L, 0, t / 2))
    d.node_load(r, F=(0, 0, -P))
    res = d.solve(f"verify/strip_{n_thick}")
    E, nu = MAT.get("AL6061").E, MAT.get("AL6061").nu
    I = b * t ** 3 / 12
    beam = P * L ** 3 / (3 * E * I)
    tip = -res.rigid_disp("TIP")[2]
    return dict(elems_through_t=n_thick, size_mm=m.h, nodes=m.n, tip_mm=tip, beam_mm=beam,
                plate_mm=beam * (1 - nu ** 2), err_vs_beam_pct=100 * (tip / beam - 1))


def profile_2020(L: float):
    """The CAD's 2020 (parts.extrusion_2020: Misumi HFS5-2020 slot dimensions) plus the four diagonal webs a real
    profile has between its core and its corners. The CAD leaves them out (it is drawn for looks), and without
    them its core and its four corners are five separate bars: a 100 mm length of it bends 3.4x more than the
    catalogue section (check below)."""
    sys.path.insert(0, str(fem.CAD / "chain-carousel-v2"))
    import cadquery as cq
    import parts as PT
    prof = PT.extrusion_2020(L)
    tw = 1.6                                                   # web thickness
    for a in (45, 135, 225, 315):
        web = (cq.Workplane("XY").center(6.6, 0).rect(5.6, tw).extrude(L)
               .rotate((0, 0, 0), (0, 0, 1), a))
        prof = prof.union(web)
    return prof.cut(cq.Workplane("XY").circle(4.2 / 2).extrude(L))


def extrusion_2020():
    import cadquery as cq
    from OCP.BRepGProp import BRepGProp
    from OCP.GProp import GProp_GProps
    L = 100.0
    prof = profile_2020(L)
    sec = prof.section(L / 2).val()
    g = GProp_GProps()
    BRepGProp.SurfaceProperties_s(sec.wrapped, g)
    A = g.Mass()
    Mi = g.MatrixOfInertia()
    Ixx, Iyy = Mi.Value(1, 1), Mi.Value(2, 2)                 # about the centroid's x and y axes (in the section plane)
    step = fem.WORK / "verify" / "ext2020.step"
    step.parent.mkdir(parents=True, exist_ok=True)
    cq.exporters.export(prof, str(step))
    m = fem.mesh_parts([fem.Part("ext", step, material="AL6063")], size=1.2, size_min=0.5, curv=8)
    E, nu = MAT.get("AL6063").E, MAT.get("AL6063").nu
    Gm = E / (2 * (1 + nu))
    out = dict(A_mm2=A, Ixx_mm4=Ixx, Iyy_mm4=Iyy, catalogue_I_mm4=7200.0, catalogue_mass_kg_m=0.50,
               mass_per_m_kg=A * 2.70e-6 * 1000, nodes=m.n,
               cad_profile_note="the CAD's own 2020 profile (no webs) bent 3.4x more than this in the same test: its core and corners are disconnected")
    # bending: tip load on a rigid end
    d = fem.Deck(m)
    d.fix(m.nodes_where(lambda p: p[:, 2] < 1e-6))
    r, q = d.rigid_patch(m.nodes_where(lambda p: p[:, 2] > L - 1e-6), "TIP", at=(0, 0, L))
    P = 100.0
    d.node_load(r, F=(P, 0, 0))
    res = d.solve("verify/ext_bend")
    tip = res.rigid_disp("TIP")[0]
    EI = P * L ** 3 / (3 * tip)                              # shear deflection is under 1 % here; ignore it
    # torsion
    d = fem.Deck(m)
    d.fix(m.nodes_where(lambda p: p[:, 2] < 1e-6))
    r, q = d.rigid_patch(m.nodes_where(lambda p: p[:, 2] > L - 1e-6), "TIP", at=(0, 0, L))
    T = 1000.0
    d.node_load(r, M=(0, 0, T), rot=q)
    res = d.solve("verify/ext_twist")
    phi = res.rigid_disp("TIP")[5]
    GJ = T * L / phi
    out.update(EI_fem=EI, I_fem_mm4=EI / E, GJ_fem=GJ, J_fem_mm4=GJ / Gm)
    # the equivalent bar must match
    MAT.equivalent_bar("EXT2020", EI, GJ, A * 2.70e-9, label="2020 equivalent bar")
    out["equivalent_bar"] = MAT.get("EXT2020").ortho
    mb = fem.mesh_parts([fem.Part("bar", box(-10, -10, 0, 20, 20, L), material="EXT2020", orient=((0, 0, 1), (1, 0, 0)))],
                        size=5.0, size_min=2.5, curv=0)
    d = fem.Deck(mb)
    d.fix(mb.nodes_where(lambda p: p[:, 2] < 1e-6))
    r, q = d.rigid_patch(mb.nodes_where(lambda p: p[:, 2] > L - 1e-6), "TIP", at=(0, 0, L))
    d.node_load(r, F=(P, 0, 0))
    tip_eq = d.solve("verify/eqbar_bend").rigid_disp("TIP")[0]
    d = fem.Deck(mb)
    d.fix(mb.nodes_where(lambda p: p[:, 2] < 1e-6))
    r, q = d.rigid_patch(mb.nodes_where(lambda p: p[:, 2] > L - 1e-6), "TIP", at=(0, 0, L))
    d.node_load(r, M=(0, 0, T), rot=q)
    phi_eq = d.solve("verify/eqbar_twist").rigid_disp("TIP")[5]
    out.update(eqbar_tip_mm=tip_eq, profile_tip_mm=tip, eqbar_twist_rad=phi_eq, profile_twist_rad=phi)
    return out


def buckling(L=200.0, dia=6.0):
    """Cantilever column, 6 mm steel rod, 200 mm, load on the free end's face: K = 2 Euler load.
    Run with 4 OpenMP threads this build of CalculiX 2.21 returned 0.98 N (and 19.7 N with default Lanczos
    settings) for this 805 N column; single-threaded it is right, so fem.Deck.solve runs ccx on one thread."""
    def rod(g):
        return [g.model.occ.addCylinder(0, 0, 0, 0, 0, L, dia / 2)]
    m = fem.mesh_parts([fem.Part("rod", rod, material="STEEL1018")], size=1.5, size_min=0.8, curv=12)
    d = fem.Deck(m)
    d.fix(m.nodes_where(lambda p: p[:, 2] < 1e-6))
    d.traction(m.faces_where(lambda c, n: n[2] > 0.99), (0, 0, -1.0))
    d.buckle(2)
    res = d.solve("verify/buckle")
    E = MAT.get("STEEL1018").E
    I = math.pi * dia ** 4 / 64
    return dict(fem_N=res.factors[:2], euler_N=math.pi ** 2 * E * I / (4 * L ** 2))


def main():
    out = {}
    out["cantilever"] = [cantilever(h) for h in (10.0, 5.0, 2.5)]
    out["cantilever_modes"] = cantilever_modes()
    out["plate_strip"] = [strip(n) for n in (1, 2, 3)]
    out["extrusion_2020"] = extrusion_2020()
    try:
        out["buckling"] = buckling()
    except Exception as e:                                    # noqa: BLE001
        out["buckling"] = {"error": str(e)}
    OUT.mkdir(exist_ok=True)
    (OUT / "verify.json").write_text(json.dumps(out, indent=1, default=float))
    print(json.dumps(out, indent=1, default=float))


if __name__ == "__main__":
    main()
