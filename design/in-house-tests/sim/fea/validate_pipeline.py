"""Pipeline check: PLA cantilever 100 x 10 x 10 mm, fixed at x = 0, 1 N tip load and free vibration.
Compares CalculiX C3D10 (gmsh mesh) with Euler-Bernoulli + Timoshenko shear correction."""
import math
import numpy as np
from fea_common import *

L, B, H = 100.0, 10.0, 10.0
E, nu, rho = PLA["E"], PLA["nu"], PLA["rho"]

def build(gmsh):
    v = gmsh.model.occ.addBox(0, 0, 0, L, B, H)
    gmsh.model.occ.synchronize()
    fix = surface_entities_in_box(gmsh, 0, 0, 0, 0, B, H)
    tip = surface_entities_in_box(gmsh, L, 0, 0, L, B, H)
    return {"VBEAM": (3, [v]), "FIX": (2, fix), "TIP": (2, tip)}

res = []
for lc in (5.0, 3.0, 2.0):
    nodes, tets, vid, ns, surfs = mesh_tet10(build, lc)
    ftip = {n: np.array([0, 0, -1.0 / len(ns["TIP"])]) for n in ns["TIP"]}  # crude, refined below
    # consistent load: uniform shear traction over the tip face, total 1 N
    area = tri6_area(nodes, surfs["TIP"])
    ftip = pressure_cload(nodes, surfs["TIP"], 1.0 / area, direction=(0, 0, -1))
    steps = ("*BOUNDARY\nFIX, 1, 3, 0.\n*STEP\n*STATIC\n" + cload_block(ftip) +
             "*NODE PRINT, NSET=TIP\nU\n*END STEP\n"
             "*STEP\n*FREQUENCY\n4\n*END STEP\n")
    inp = write_inp(RUNS / "val" / f"cant_{lc}.inp", nodes, tets, vid, {"VBEAM": PLA}, nsets=ns, steps=steps)
    run_ccx(inp)
    blocks = parse_dat(inp.with_suffix(".dat"))
    u = [b for b in blocks if b["kind"] == "displacements"][0]["data"]
    uz = u[:, 3].mean()
    fr = parse_freqs(inp.with_suffix(".dat"))
    res.append((lc, len(nodes), uz, fr[:2]))
    print(lc, len(nodes), uz, fr[:4])

I = B * H**3 / 12
Gm = E / (2 * (1 + nu))
d_eb = 1.0 * L**3 / (3 * E * I)
d_sh = 1.0 * L / ((10 * (1 + nu) / (12 + 11 * nu)) * Gm * B * H)
f1 = (1.8751**2 / (2 * math.pi)) * math.sqrt(E * I / (rho * B * H * L**4))
print("hand: EB", d_eb, "EB+shear", d_eb + d_sh, "f1 EB", f1)
save_json("validate_pipeline.json", dict(case="PLA cantilever 100x10x10, 1 N tip", hand_EB_mm=d_eb,
          hand_EB_shear_mm=d_eb + d_sh, hand_f1_Hz=f1,
          fea=[dict(lc_mm=r[0], nodes=r[1], tip_uz_mm=r[2], f_Hz=r[3]) for r in res]))
