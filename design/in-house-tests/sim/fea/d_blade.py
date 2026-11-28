"""FEA (d), test 9: blade gap change under the spreading force and under its own weight. Computed, not measured.

Geometry: cad/out/step/blade_carriage.step (base block on the stage slider, 65 mm arm, clamp with a 1.6 mm slot).
The 304 blade (25 tall x 50 long) is modelled 1.6 thick so it bonds to the slot walls (clamped by the two
horizontal M3 screws); its edge sits 3 mm below the clamp (z = -25). Base block bottom face fixed (bolted to
the slider); the two M3 gap screws are assumed NOT touching the bed rails (worst case: cantilever).
Spreading force: Rankine passive earth pressure with cohesion on the blade face from the feed heap
(estimate, stated in the README), against 1 N unit loads.
"""
import math
import sys

import numpy as np

from fea_common import *

OUT = HERE / "results"
OUT.mkdir(exist_ok=True)
STEP, PROV = get_step("blade_carriage")
ZB0, ZB1 = -25.0, 0.0
YB0, YB1 = 87.2, 88.8


def build(gmsh):
    occ = gmsh.model.occ
    ents = occ.importShapes(str(STEP))
    blade = occ.addBox(-25.0, YB0, ZB0, 50.0, YB1 - YB0, ZB1 - ZB0)
    out, omap = occ.fragment([(3, t) for d, t in ents if d == 3], [(3, blade)])
    occ.synchronize()
    vb = [t for d, t in omap[1]]
    vc = [t for d, t in out if d == 3 and t not in vb]
    return {"VCARR": (3, vc), "VBLADE": (3, vb)}


def run(lc, E=PLA["E"]):
    nodes, tets, vid, _, _ = mesh_tet10(build, lc)
    x, y, z = nodes.T
    cn = np.zeros(len(nodes) + 1, bool)
    cn[np.unique(tets[vid == "VCARR"])] = True
    bn = np.zeros(len(nodes) + 1, bool)
    bn[np.unique(tets[vid == "VBLADE"])] = True
    cn, bn = cn[1:], bn[1:]
    fix = np.where(cn & (np.abs(z) < 1e-6) & (np.abs(x) <= 25) & (np.abs(y) <= 20))[0] + 1
    edge = np.where(bn & (np.abs(z - ZB0) < 1e-6) & (np.abs(x) <= 15.0))[0] + 1   # coupon width 30
    shared = np.intersect1d(np.unique(tets[vid == "VCARR"]), np.unique(tets[vid == "VBLADE"]))
    ec = edge[np.argmin(np.abs(x[edge - 1]))]
    el = edge[np.argmin(np.abs(x[edge - 1] + 15))]
    er = edge[np.argmin(np.abs(x[edge - 1] - 15))]
    ns = {"NFIX": fix, "NEDGE": edge, "NPROBE": [int(ec), int(el), int(er)]}
    fz = {n: np.array([0, 0, 1.0 / len(edge)]) for n in edge}
    fy = {n: np.array([0, 1.0 / len(edge), 0]) for n in edge}
    mats = {"VCARR": dict(E=E, nu=PLA["nu"], rho=PLA["rho"]), "VBLADE": STEEL}
    steps = ("*BOUNDARY\nNFIX, 1, 3, 0.\n"
             "*STEP\n*STATIC\n*DLOAD\nEALL, GRAV, 9810., 0., 0., -1.\n*NODE PRINT, NSET=NPROBE, GLOBAL=YES\nU\n"
             "*EL PRINT, ELSET=EVCARR\nS\n*END STEP\n"
             "*STEP\n*STATIC\n*DLOAD, OP=NEW\n" + cload_block(fz) + "*NODE PRINT, NSET=NPROBE, GLOBAL=YES\nU\n*END STEP\n"
             "*STEP\n*STATIC\n" + cload_block(fy).replace("*CLOAD\n", "*CLOAD, OP=NEW\n") +
             "*NODE PRINT, NSET=NPROBE, GLOBAL=YES\nU\n*END STEP\n")
    (RUNS / "blade").mkdir(parents=True, exist_ok=True)
    inp = write_inp(RUNS / "blade" / f"blade_{lc}_{int(E)}.inp", nodes, tets, vid, mats, nsets=ns, steps=steps)
    run_ccx(inp)
    bl = [b for b in parse_dat(inp.with_suffix(".dat")) if b["kind"] == "displacements"]
    st = [b for b in parse_dat(inp.with_suffix(".dat")) if b["kind"] == "stresses"][0]["data"][:, 2:8]
    res = dict(lc=lc, E=E, nodes=len(nodes), shared_nodes_blade_clamp=len(shared))
    for name, b in zip(("gravity", "Fz_up_1N", "Fy_drag_1N"), bl):
        u = {int(r[0]): r[1:4] for r in b["data"]}
        res[name] = dict(uz_centre_um=u[ec][2] * 1e3, uz_end_left_um=u[el][2] * 1e3,
                         uz_end_right_um=u[er][2] * 1e3, uy_centre_um=u[ec][1] * 1e3)
    res["gravity"]["vm_max_MPa"] = float(von_mises(st).max())
    return res


def spreading_force(width=30.0, feed_g=0.5, aor_deg=32.0, powders=None):
    """Rankine passive earth pressure with cohesion on a vertical blade pushing the feed heap:
    P = 0.5 Kp gamma h^2 + 2 c sqrt(Kp) h per unit width (Kp = (1 + sin phi)/(1 - sin phi)); heap height h
    from the feed line (triangular section at the AoR). Vertical (lift) component: P tan(phi_w).
    Reference powders from #196 (runs 5, 6)."""
    powders = powders or dict(dry=dict(rho_b=1249.0, phi=24.8, c=6.6, phi_w=21.8),
                              cohesive=dict(rho_b=1023.0, phi=32.3, c=11.9, phi_w=21.8))
    out = {}
    for k, p in powders.items():
        A = feed_g * 1e-3 / (p["rho_b"] * width * 1e-3)        # m2
        h = math.sqrt(A / (1.0 / math.tan(math.radians(aor_deg))))
        Kp = (1 + math.sin(math.radians(p["phi"]))) / (1 - math.sin(math.radians(p["phi"])))
        gam = p["rho_b"] * 9.81
        P = 0.5 * Kp * gam * h ** 2 + 2 * p["c"] * math.sqrt(Kp) * h     # N/m
        Fx = P * width * 1e-3
        out[k] = dict(heap_height_mm=h * 1e3, Kp=Kp, drag_N=Fx, lift_N=Fx * math.tan(math.radians(p["phi_w"])))
    return out


def rods(L=200.0, d=8.0, m_moving_g=150.0):
    """Two Ø8 steel guide rods, simply supported over L: sag at mid-span from the moving mass and self weight;
    gap variation along the stroke is the difference between mid-span and the ends."""
    I = math.pi * d ** 4 / 64
    P = m_moving_g * 1e-3 * 9.81 / 2
    w = 7.85e-9 * math.pi * d ** 2 / 4 * G  # N/mm
    dP = P * L ** 3 / (48 * STEEL["E"] * I)
    dw = 5 * w * L ** 4 / (384 * STEEL["E"] * I)
    return dict(L_mm=L, sag_point_um=dP * 1e3, sag_self_um=dw * 1e3, gap_variation_um=(dP + dw) * 1e3,
                assumption="stage rods 200 mm between end blocks, carriage + slider 150 g")


if __name__ == "__main__":
    res = dict(provenance=PROV, spreading_force=spreading_force(), rods=rods(), fea=[])
    print(res["spreading_force"], res["rods"], flush=True)
    for lc in (4.0, 3.0, 2.6):  # the blade is 1.6 thick: 2.2 would need about 3 GB
        o = run(lc)
        res["fea"].append(o)
        print(o, flush=True)
    o = run(3.0, E=PLA["E_LOW"])
    res["fea"].append(o)
    print(o, flush=True)
    save_json(OUT / "d_blade.json", res)
