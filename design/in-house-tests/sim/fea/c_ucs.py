"""FEA (c), test 8: split mould under consolidation (Janssen wall stress) and the UCS force loop
(platen arm + base/column + TAL221) against the sample's own compliance. Computed, not measured.

Geometry: cad/out/step/split_mould_A.step, ucs_platen.step, ucs_base.step (CAD worker's parts).
"""
import math
import sys

import numpy as np

from fea_common import *

OUT = HERE / "results"
OUT.mkdir(exist_ok=True)
sys.path.insert(0, str(CAD))
import parts as _cad  # noqa: E402

D, H = _cad.MOULD_ID, _cad.MOULD_H
RO_M = _cad.MOULD_OD / 2
POWDERS = dict(dry=dict(rho_b=1249.0, phi_i=24.8, mu_w=0.40),
               cohesive=dict(rho_b=1023.0, phi_i=32.3, mu_w=0.40))


def janssen(sig0, rho_b, phi_i, mu_w, z):
    """Janssen with a top load sig0 (Pa); z (mm) down from the top. K = Rankine active (1 - sin)/(1 + sin)."""
    K = (1 - math.sin(math.radians(phi_i))) / (1 + math.sin(math.radians(phi_i)))
    sinf = rho_b * 9.81 * (D / 1e3) / (4 * mu_w * K)
    e = np.exp(-4 * mu_w * K * np.asarray(z) / D)
    sv = sinf + (sig0 - sinf) * e
    return sv, K * sv, K


# ----------------------------------------------------------------------------------------------
# mould half
# ----------------------------------------------------------------------------------------------
MSTEP, MPROV = get_step("split_mould_A")


def mould_fea(lc, case="closed", sig0=2000.0, powder="dry", E=PLA["E"]):
    def build(gmsh):
        ents = gmsh.model.occ.importShapes(str(MSTEP))
        gmsh.model.occ.synchronize()
        return {"VM": (3, [t for d, t in ents if d == 3])}
    nodes, tets, vid, _, _ = mesh_tet10(build, lc)
    r = np.hypot(nodes[:, 0], nodes[:, 1])
    z = nodes[:, 2]
    bore = np.where(np.abs(r - D / 2) < 0.02)[0] + 1
    part = np.where(np.abs(nodes[:, 1]) < 1e-6)[0] + 1          # parting faces, y = 0
    base = np.where(np.abs(z) < 1e-6)[0] + 1
    # Janssen pressure on the bore: nodal forces from the 6-node faces; build bore faces from tets
    p = POWDERS[powder]
    # lump: each bore node gets p(z) * tributary area; tributary area from a fine sampling of the bore
    # surface (uniform-ish mesh): area per node = bore area / n_nodes weighted by local spacing
    zt = H - z[bore - 1]                                        # depth below the top of the column
    _, sh, K = janssen(sig0, p["rho_b"], p["phi_i"], p["mu_w"], zt)
    area = math.pi * D / 2 * H / len(bore)                      # half bore
    f = {}
    for n, s in zip(bore, sh):
        x, y = nodes[n - 1, 0], nodes[n - 1, 1]
        rr = math.hypot(x, y)
        f[n] = s * 1e-6 * area * np.array([x / rr, y / rr, 0.0])   # Pa -> N/mm2
    ns = {"NBORE": bore, "NPART": part, "NBASE": base}
    probes = {"P_TOP_MID": (0.0, D / 2, H - 1.0), "P_BOT_MID": (0.0, D / 2, 1.0),
              "P_TOP_EDGE": (D / 2, 0.0, H - 1.0), "P_MID_MID": (0.0, D / 2, H / 2),
              "P_OD_MID": (0.0, RO_M, H / 2), "P_PART_OD": (RO_M, 0.0, H / 2)}
    pid = {}
    for k, q in probes.items():
        d = np.linalg.norm(nodes - np.asarray(q), axis=1)
        pid[k] = int(np.argmin(d)) + 1
        ns[k] = [pid[k]]
    ns["NPROBE"] = list(pid.values())
    if case == "closed":
        # rings snug: the parting faces bear on the other half (symmetry), base stops z, one node stops x
        bc = "*BOUNDARY\nNPART, 2, 2, 0.\nNBASE, 3, 3, 0.\nP_TOP_MID, 1, 1, 0.\n"
    else:
        # rings carry it: ring bands z 0-6 and 34-40 touch the OD at y = 15 (crown); parting faces free
        ringc = np.where((np.abs(r - RO_M) < 0.02) & (np.abs(nodes[:, 0]) < 3.0)
                         & ((z <= 6.0) | (z >= H - 6.0)))[0] + 1
        ns["NRING"] = ringc
        bc = "*BOUNDARY\nNRING, 2, 2, 0.\nNBASE, 3, 3, 0.\nP_TOP_MID, 1, 1, 0.\n"
    steps = (bc + "*STEP\n*STATIC\n" + cload_block(f) +
             "*NODE PRINT, NSET=NPROBE, GLOBAL=YES\nU\n*NODE PRINT, NSET=NPART, GLOBAL=YES\nU\n"
             "*EL PRINT, ELSET=EALL\nS\n*END STEP\n")
    (RUNS / "mould").mkdir(parents=True, exist_ok=True)
    inp = write_inp(RUNS / "mould" / f"mould_{case}_{lc}.inp", nodes, tets, vid,
                    {"VM": dict(E=E, nu=PLA["nu"], rho=PLA["rho"])}, nsets=ns, steps=steps)
    run_ccx(inp)
    bl = parse_dat(inp.with_suffix(".dat"))
    d = [b for b in bl if b["kind"] == "displacements"]
    u = {int(row[0]): row[1:4] for row in d[0]["data"]}
    U = {k: u[v] for k, v in pid.items()}
    up = d[1]["data"]
    s = [b for b in bl if b["kind"] == "stresses"][0]["data"][:, 2:8]
    out = dict(lc=lc, case=case, nodes=len(nodes), K=K, sig_h_top_Pa=float(sh.max()), sig_h_bot_Pa=float(sh.min()),
               bore_radial_top_mid_nm=U["P_TOP_MID"][1] * 1e6, bore_radial_mid_nm=U["P_MID_MID"][1] * 1e6,
               parting_line_gap_max_um=0.0, parting_splay_x_max_um=float(np.max(np.abs(up[:, 1]))) * 1e3,
               vm_max_MPa=float(von_mises(s).max()))
    if case != "closed":
        # opening of the parting line = -2 * u_y of the parting-face nodes (both halves move apart)
        out["parting_line_gap_max_um"] = float(2 * max(0.0, up[:, 2].max())) * 1e3
    return out


def mould_hand(sig0=2000.0, powder="dry"):
    p = POWDERS[powder]
    z = np.linspace(0, H, 81)
    sv, sh, K = janssen(sig0, p["rho_b"], p["phi_i"], p["mu_w"], z)
    t = RO_M - D / 2
    # thin ring: radial growth p r^2 / (E t) at the top (closed rings)
    dr = sh.max() * 1e-6 * (D / 2) ** 2 / (PLA["E"] * t)
    # separating force on one parting line: integral of sigma_h * D/2 dz (per half: D * integral / 2)
    Fsep = float(np.trapezoid(sh * 1e-6 * D, z)) / 2
    return dict(powder=powder, sigma0_Pa=sig0, K=K, sigma_v_bottom_Pa=float(sv[-1]),
                sigma_h_top_Pa=float(sh[0]), sigma_h_bottom_Pa=float(sh[-1]),
                bottom_fraction_of_top_load=float(sv[-1] / sig0), radial_growth_thin_ring_nm=dr * 1e6,
                separating_force_per_parting_line_N=Fsep,
                ring_clearance_radial_mm=(_cad.MOULD_OD / 2 + 0.25) - _cad.MOULD_OD / 2,
                z_mm=z.tolist(), sigma_v_Pa=sv.tolist(), sigma_h_Pa=sh.tolist())


# ----------------------------------------------------------------------------------------------
# platen arm
# ----------------------------------------------------------------------------------------------
PSTEP, PPROV = get_step("ucs_platen")


def platen_fea(lc, E=PLA["E"]):
    def build(gmsh):
        ents = gmsh.model.occ.importShapes(str(PSTEP))
        gmsh.model.occ.synchronize()
        return {"VP": (3, [t for d, t in ents if d == 3])}
    nodes, tets, vid, _, surfs = mesh_tet10(build, lc)
    x, y, z = nodes.T
    # current CAD (09:28): vertical plate x 36-42, y +-20, z -16..24, four M3 holes along x at y +-15,
    # z -11 / 19, bolted face-on to the stage slider at x = 42
    holes = np.zeros(len(nodes), bool)
    for hy in (-15.0, 15.0):
        for hz in (-11.0, 19.0):
            holes |= (np.abs(np.hypot(y - hy, z - hz) - 1.7) < 0.02) & (x >= 36.0 - 1e-6)
    face = (np.abs(x - x.max()) < 1e-6)
    fix = np.where(holes | face)[0] + 1
    disc = np.where((np.abs(z) < 1e-6) & (np.hypot(x, y) <= 10.0))[0] + 1      # sample footprint Ø20
    F = 1.0
    f = {n: np.array([0.0, 0.0, F / len(disc)]) for n in disc}
    c = int(np.argmin(np.hypot(x, y) + 10 * np.abs(z))) + 1
    e1 = int(np.argmin(np.hypot(x - 9, y) + 10 * np.abs(z))) + 1
    e2 = int(np.argmin(np.hypot(x + 9, y) + 10 * np.abs(z))) + 1
    ns = {"NFIX": fix, "NPROBE": [c, e1, e2]}
    steps = ("*BOUNDARY\nNFIX, 1, 3, 0.\n*STEP\n*STATIC\n" + cload_block(f) +
             "*NODE PRINT, NSET=NPROBE, GLOBAL=YES\nU\n*EL PRINT, ELSET=EALL\nS\n*END STEP\n")
    (RUNS / "ucs").mkdir(parents=True, exist_ok=True)
    inp = write_inp(RUNS / "ucs" / f"platen_{lc}_{int(E)}.inp", nodes, tets, vid,
                    {"VP": dict(E=E, nu=PLA["nu"], rho=PLA["rho"])}, nsets=ns, steps=steps)
    run_ccx(inp)
    bl = parse_dat(inp.with_suffix(".dat"))
    u = {int(row[0]): row[1:4] for row in [b for b in bl if b["kind"] == "displacements"][0]["data"]}
    s = [b for b in bl if b["kind"] == "stresses"][0]["data"][:, 2:8]
    uz = u[c][2]
    tilt = (u[e1][2] - u[e2][2]) / 18.0
    return dict(lc=lc, E=E, nodes=len(nodes), compliance_um_per_N=uz * 1e3, tilt_deg_per_N=math.degrees(tilt),
                vm_max_MPa_per_N=float(von_mises(s).max()))


# ----------------------------------------------------------------------------------------------
# base + column loop
# ----------------------------------------------------------------------------------------------
BSTEP, BPROV = get_step("ucs_base")
L_CELL = 30.0   # mm, load-cell fixed block centre (x = -38) to the sample axis (TAL221 free end), assumed
D_STAGE = 60.0  # mm, column front face (y = 60) to the sample axis (y = 0): lever of the platen force


def base_fea(lc, E=PLA["E"], support="bench"):
    def build(gmsh):
        ents = gmsh.model.occ.importShapes(str(BSTEP))
        gmsh.model.occ.synchronize()
        return {"VB": (3, [t for d, t in ents if d == 3])}
    nodes, tets, vid, _, _ = mesh_tet10(build, lc)
    x, y, z = nodes.T
    blk = np.where((np.abs(z - 28.0) < 1e-6) & (x >= -48) & (x <= -28) & (np.abs(y) <= 8))[0] + 1
    # column front face = lowest y among nodes high on the column (works for the 09:05 STEP, column
    # y 40-60, and the later parts.py, column y 60-80); the platen force acts y_face in front of it
    hi = z > 100.0
    y_face = float(y[hi].min())
    col = np.where((np.abs(y - y_face) < 1e-6) & (z >= 100) & (z <= 150) & (np.abs(x) <= 15))[0] + 1
    D_ST = y_face
    bot = np.where(np.abs(z) < 1e-6)[0] + 1
    F = 1.0
    # block: F down at the sample axis, carried by the cell as a force + moment F*L_CELL about y
    xb = x[blk - 1]
    xm = xb.mean()
    I2 = np.sum((xb - xm) ** 2)
    f = {}
    for n, xi in zip(blk, xb):
        f[n] = np.array([0, 0, -F / len(blk) - F * L_CELL * (xi - xm) / I2])
    # column stage patch: F up, plus the platen moment F*D_STAGE about x (the sample is in front, -y)
    zc = z[col - 1]
    zm = zc.mean()
    J2 = np.sum((zc - zm) ** 2)
    for n, zi in zip(col, zc):
        # moment about x from an upward force at -D_STAGE in y: equivalent to normal (y) forces varying with z
        # +F (z) at the sample (y = 0) = +F at the face (y = y_face) plus M_x = -y_face * F; a set of y-forces
        # f_y = c (z - zm) gives M_x = -c J2, so c = +F y_face / J2
        f[n] = f.get(n, 0) + np.array([0, F * D_ST * (zi - zm) / J2, F / len(col)])
    ns = {"NBLK": blk, "NCOL": col, "NBOT": bot}
    if support == "bench":
        a = int(np.argmin(np.hypot(x - 52, y + 52) + np.abs(z))) + 1
        b = int(np.argmin(np.hypot(x + 52, y + 52) + np.abs(z))) + 1
        ns.update(NA=[a], NB=[b])
        bc = "*BOUNDARY\nNBOT, 3, 3, 0.\nNA, 1, 2, 0.\nNB, 2, 2, 0.\n"
    else:
        pts = [(52, -52), (-52, -52), (52, float(y.max()) - 8), (-52, float(y.max()) - 8)]
        corner = [int(np.argmin(np.hypot(x - px, y - py) + np.abs(z))) + 1 for px, py in pts]
        ns.update(NC=corner, NA=[corner[0]], NB=[corner[1]])
        bc = "*BOUNDARY\nNC, 3, 3, 0.\nNA, 1, 2, 0.\nNB, 2, 2, 0.\n"
    steps = (bc + "*STEP\n*STATIC\n" + cload_block(f) +
             "*NODE PRINT, NSET=NBLK, GLOBAL=YES\nU\n*NODE PRINT, NSET=NCOL, GLOBAL=YES\nU\n*END STEP\n")
    (RUNS / "ucs").mkdir(parents=True, exist_ok=True)
    inp = write_inp(RUNS / "ucs" / f"base_{support}_{lc}_{int(E)}.inp", nodes, tets, vid,
                    {"VB": dict(E=E, nu=PLA["nu"], rho=PLA["rho"])}, nsets=ns, steps=steps)
    run_ccx(inp)
    bl = [b for b in parse_dat(inp.with_suffix(".dat")) if b["kind"] == "displacements"]
    ub, uc = bl[0]["data"], bl[1]["data"]
    # rigid-body fit of each patch: uz = a + b*x (+ c*y) -> displacement at the sample axis
    xb_ = nodes[ub[:, 0].astype(int) - 1]
    Ab = np.c_[np.ones(len(ub)), xb_[:, 0] - xm, xb_[:, 1]]
    cb = np.linalg.lstsq(Ab, ub[:, 3], rcond=None)[0]
    uz_sample_on_cell = cb[0] + cb[1] * (L_CELL)          # sample axis is L_CELL in +x from the block centre
    xc_ = nodes[uc[:, 0].astype(int) - 1]
    # patch rotation about x: uy varies with z -> theta_x = d(uy)/dz ; vertical at the sample = uz - theta*D
    Ac = np.c_[np.ones(len(uc)), xc_[:, 2] - zm]
    cy = np.linalg.lstsq(Ac, uc[:, 2], rcond=None)[0]
    cz = np.linalg.lstsq(Ac, uc[:, 3], rcond=None)[0]
    theta_x = -cy[1]                                       # rotation of the face about x
    uz_platen_root = cz[0] - theta_x * D_ST
    return dict(lc=lc, E=E, support=support, nodes=len(nodes), column_face_y=y_face, uz_block_mean_um=float(ub[:, 3].mean() * 1e3),
                uz_sample_axis_on_cell_um=float(uz_sample_on_cell * 1e3), uz_stage_um=float(cz[0] * 1e3),
                rot_stage_patch_deg=math.degrees(theta_x),
                frame_compliance_um_per_N=float((uz_platen_root - uz_sample_on_cell) * 1e3))


def tal221(capacity_N=0.981, eps_fs=500e-6, Lf=10.0, t=1.0):
    """Mini bar load cell as a parallel-guided (binocular) flexure: d_FS = eps_FS * Lf^2 / (3 t).
    eps_FS 500 ue (1 mV/V full bridge, GF 2), flexure length Lf 8-12 mm, web 0.7-1.2 mm: assumptions."""
    d = eps_fs * Lf ** 2 / (3 * t)
    lo = eps_fs * 8.0 ** 2 / (3 * 1.2)
    hi = eps_fs * 12.0 ** 2 / (3 * 0.7)
    return dict(deflection_FS_um=d * 1e3, compliance_um_per_N=d * 1e3 / capacity_N,
                range_um_per_N=[lo * 1e3 / capacity_N, hi * 1e3 / capacity_N])


def sample(sig_c_Pa=(100.0, 1000.0), eps_f=(0.01, 0.03), Hs=40.0):
    """Unconfined column Ø20 x Hs: secant stiffness to failure k = sigma_c A / (eps_f Hs)."""
    A = math.pi * (D / 2) ** 2
    out = []
    for s in sig_c_Pa:
        for e in eps_f:
            F = s * 1e-6 * A
            out.append(dict(sigma_c_Pa=s, eps_f=e, F_peak_N=F, delta_fail_um=e * Hs * 1e3,
                            compliance_um_per_N=e * Hs * 1e3 / F))
    return out


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    res = dict(provenance=dict(mould=MPROV, platen=PPROV, base=BPROV),
               assumptions=dict(L_cell_mm=L_CELL, D_stage_mm=D_STAGE, K="Rankine active",
                                mu_w_PLA=0.40, powders=POWDERS))
    res["janssen"] = [mould_hand(s0, pw) for s0 in (200.0, 2000.0) for pw in ("dry", "cohesive")]
    res["tal221"] = tal221()
    res["sample"] = sample()
    if which in ("mould", "all"):
        res["mould"] = []
        for lc in (2.5, 1.8, 1.3):
            o = mould_fea(lc, "closed")
            res["mould"].append(o)
            print("mould closed", o, flush=True)
        for lc in (2.5, 1.8):
            o = mould_fea(lc, "rings")
            res["mould"].append(o)
            print("mould rings", o, flush=True)
    if which in ("frame", "all"):
        res["platen"] = []
        for lc in (4.0, 3.0, 2.0):
            o = platen_fea(lc)
            res["platen"].append(o)
            print("platen", o, flush=True)
        res["platen"].append(platen_fea(3.0, E=PLA["E_LOW"]))
        res["base"] = []
        for lc in (8.0, 6.0, 4.5):
            o = base_fea(lc)
            res["base"].append(o)
            print("base", o, flush=True)
        res["base"].append(base_fea(6.0, support="corners"))
        res["base"].append(base_fea(6.0, E=PLA["E_LOW"]))
        print(res["base"][-2:], flush=True)
    save_json(OUT / f"c_ucs_{which}.json", res)
