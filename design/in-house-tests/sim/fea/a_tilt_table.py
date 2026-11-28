"""FEA (a), test 3 tilt table: plate sag under coupon + ring + lid, natural frequencies on the hinge pin and
the servo gear, and the angle error from servo step jolts. Computed, not measured.

Geometry: cad/out/step/tilt_plate.step (hinge axis along x at y = 0, z = 60; plate y 0-120).
Coupon (steel 100 x 50 x 1, 39 g) and ring + powder + 15 g lid (19 g) are modelled as soft mass layers
(E = 5 MPa) bonded on the pocket floor: they add mass, not stiffness.
Hinge: radial + axial restraint on the Ø5 bore of both lugs (pin), free rotation about the axis.
Gear + servo: a torsional spring k_theta about the hinge axis, spread over the +x lug face the 30T gear
bolts to (SPRING1 springs on global y and z of each face node, sum(k r^2) = k_theta).
"""
import math
import sys

import numpy as np

from fea_common import *

OUT = HERE / "results"
OUT.mkdir(exist_ok=True)
STEP, PROV = get_step("tilt_plate")
sys.path.insert(0, str(CAD))
import parts as _cad  # noqa: E402  (constants that go with the STEP)
AX = np.array([0.0, 0.0, _cad.HINGE_Z])          # point on hinge axis; axis direction +x
Z_BOT = _cad.PLATE_Z0                             # plate underside
Z_FLOOR = _cad.PLATE_Z0 + _cad.PLATE_T - 0.8      # pocket floor
R_PIN = _cad.PIN_D / 2 + 0.05
M_COUPON = 39.0e-6              # tonne (39 g): 304 100 x 50 x 1
M_RING = 19.0e-6                # ring 0.7 g + powder 3 g + lid 15 g
RING_Y = 90.0


def build(gmsh):
    occ = gmsh.model.occ
    ents = occ.importShapes(str(STEP))
    occ.synchronize()
    return {"VPLATE": (3, [t for d, t in ents if d == 3])}


def nearest(nodes, p, mask=None):
    d = np.linalg.norm(nodes - np.asarray(p), axis=1)
    if mask is not None:
        d[~mask] = np.inf
    return int(np.argmin(d)) + 1


def run(lc, E=PLA["E"], ktheta_Nm=120.0, tag=""):
    nodes, tets, vid, _, _ = mesh_tet10(build, lc)
    plate_nodes = np.zeros(len(nodes) + 1, bool)
    plate_nodes[np.unique(tets[vid == "VPLATE"])] = True
    pn = plate_nodes[1:]
    r = np.hypot(nodes[:, 1] - AX[1], nodes[:, 2] - AX[2])
    bore = np.where(pn & (np.abs(r - R_PIN) < 0.02) & (np.abs(nodes[:, 0]) >= 38.0 - 1e-6))[0] + 1
    bore_p = bore[nodes[bore - 1, 0] > 0]
    gface = np.where(pn & (np.abs(nodes[:, 0] - 43.5) < 1e-4))[0] + 1
    rg = np.hypot(nodes[gface - 1, 1], nodes[gface - 1, 2] - AX[2])
    kth = ktheta_Nm * 1e3  # N mm / rad
    kn = kth / np.sum(rg ** 2)
    zfl = float(nodes[pn & (np.abs(nodes[:, 0]) < 20) & (nodes[:, 1] > 30) & (nodes[:, 1] < 100), 2].max())
    probes = {
        "P_IMU1": (0, 54, Z_BOT), "P_IMU2": (0, 66, Z_BOT),
        "P_R1": (0, 80, zfl), "P_R2": (0, 100, zfl),
        "P_RL": (-20, 90, zfl), "P_RR": (20, 90, zfl),
        "P_IL": (-20, 60, Z_BOT), "P_IR": (20, 60, Z_BOT),
        "P_TIPL": (-29, 118, Z_BOT), "P_TIPR": (29, 118, Z_BOT), "P_TIPC": (0, 118, Z_BOT),
    }
    pid = {k: nearest(nodes, p, pn) for k, p in probes.items()}
    nsets = {"NBORE": bore, "NBOREP": bore_p, "NGEAR": gface}
    for k, v in pid.items():
        nsets[k] = [v]
    nsets["NPROBE"] = list(pid.values())
    # payload masses (coupon spread over the pocket floor, ring + powder + lid over a Ø25 patch at y = 90)
    # pocket floor from the mesh (its depth changed between CAD exports: 0.8 -> 0.71 mm)
    inpk = pn & (np.abs(nodes[:, 0]) < 20) & (nodes[:, 1] > 30) & (nodes[:, 1] < 100)
    zf = float(nodes[inpk, 2].max())
    floor = np.where(pn & (np.abs(nodes[:, 2] - zf) < 1e-4) & (np.abs(nodes[:, 0]) <= 25.0)
                     & (nodes[:, 1] >= 14.0) & (nodes[:, 1] <= 114.2))[0] + 1
    rp = np.hypot(nodes[floor - 1, 0], nodes[floor - 1, 1] - RING_Y)
    ringn = floor[rp <= 12.5]
    m_c, m_r = M_COUPON / len(floor), M_RING / len(ringn)
    nsets["NFLOOR"], nsets["NRINGP"] = floor, ringn
    mass_txt = ("*ELEMENT, TYPE=MASS, ELSET=EMC\n" + "\n".join(f"{len(tets) + 1 + i}, {n}" for i, n in enumerate(floor))
                + f"\n*MASS, ELSET=EMC\n{m_c:.6e}\n"
                + "*ELEMENT, TYPE=MASS, ELSET=EMR\n" + "\n".join(f"{len(tets) + len(floor) + 1 + i}, {n}" for i, n in enumerate(ringn))
                + f"\n*MASS, ELSET=EMR\n{m_r:.6e}\n")
    fpay = {}
    for n in floor:
        fpay[n] = fpay.get(n, 0) + np.array([0, 0, -m_c * G])
    for n in ringn:
        fpay[n] = fpay.get(n, 0) + np.array([0, 0, -m_r * G])
    # gear + servo: SPRING1 elements on global y and z of every node of the gear face; for a rotation theta
    # about the hinge axis they resist with sum(kn * r^2) = k_theta (checked in validate_pipeline.py: SPRING1
    # acts on global dofs even on nodes that carry a *TRANSFORM)
    e0 = len(tets) + len(floor) + len(ringn) + 1
    spr = ("*ELEMENT, TYPE=SPRING1, ELSET=ESPR2\n" + "\n".join(f"{e0 + i}, {n}" for i, n in enumerate(gface))
           + f"\n*SPRING, ELSET=ESPR2\n2\n{kn:.6e}\n"
           + "*ELEMENT, TYPE=SPRING1, ELSET=ESPR3\n" + "\n".join(f"{e0 + len(gface) + i}, {n}" for i, n in enumerate(gface))
           + f"\n*SPRING, ELSET=ESPR3\n3\n{kn:.6e}\n")
    model = (f"*TRANSFORM, NSET=NBORE, TYPE=C\n{AX[0]}, {AX[1]}, {AX[2]}, 1., {AX[1]}, {AX[2]}\n" + spr + mass_txt)
    mats = {"VPLATE": dict(E=E, nu=PLA["nu"], rho=PLA["rho"])}
    steps = ("*BOUNDARY\nNBORE, 1, 1, 0.\nNBOREP, 3, 3, 0.\n"
             "*STEP\n*STATIC\n*DLOAD\nEVPLATE, GRAV, 9810., 0., 0., -1.\n" + cload_block(fpay) +
             "*NODE PRINT, NSET=NPROBE, GLOBAL=YES\nU\n*NODE PRINT, NSET=NGEAR, GLOBAL=YES\nU\n"
             "*EL PRINT, ELSET=EVPLATE\nS\n*END STEP\n"
             "*STEP\n*FREQUENCY\n6\n*NODE PRINT, NSET=NPROBE, GLOBAL=YES\nU\n*END STEP\n")
    name = f"tilt_lc{lc}_E{int(E)}_k{int(ktheta_Nm)}{tag}"
    inp = write_inp(RUNS / "tilt" / f"{name}.inp", nodes, tets, vid, mats, nsets=nsets, extra_model=model,
                    steps=steps)
    inp.parent.mkdir(parents=True, exist_ok=True)
    inp = write_inp(RUNS / "tilt" / f"{name}.inp", nodes, tets, vid, mats, nsets=nsets, extra_model=model,
                    steps=steps)
    run_ccx(inp)
    blocks = parse_dat(inp.with_suffix(".dat"))
    disp = [b for b in blocks if b["kind"] == "displacements"]
    st = disp[0]["data"]
    u = {int(row[0]): row[1:4] for row in st}
    U = {k: u[v] for k, v in pid.items()}
    gb = [b for b in disp if b["set"] == "NGEAR"][0]["data"]
    yy = nodes[gb[:, 0].astype(int) - 1, 1] - AX[1]
    zz = nodes[gb[:, 0].astype(int) - 1, 2] - AX[2]
    th_gear = float(np.mean((yy * gb[:, 3] - zz * gb[:, 2]) / (yy ** 2 + zz ** 2)))
    slope_ring = (U["P_R2"][2] - U["P_R1"][2]) / 20.0
    slope_imu = (U["P_IMU2"][2] - U["P_IMU1"][2]) / 12.0
    roll_ring = (U["P_RR"][2] - U["P_RL"][2]) / 40.0
    roll_imu = (U["P_IR"][2] - U["P_IL"][2]) / 40.0
    s = [b for b in blocks if b["kind"] == "stresses"][0]["data"][:, 2:8]
    vm = von_mises(s)
    freqs = parse_freqs(inp.with_suffix(".dat"))
    modes = []
    for i, b in enumerate([b for b in disp if b["set"] == "NPROBE"][1:len(freqs) + 1]):
        uu = {int(row[0]): row[1:4] for row in b["data"]}
        V = {k: uu[v] for k, v in pid.items()}
        tipc, tipl, tipr = V["P_TIPC"][2], V["P_TIPL"][2], V["P_TIPR"][2]
        imu = 0.5 * (V["P_IMU1"][2] + V["P_IMU2"][2])
        lat = max(abs(V[k][0]) for k in V) / (max(abs(V[k][2]) for k in V) + 1e-30)
        if lat > 1.0:
            kind = "in-plane / lateral"
        elif abs(tipl - tipr) > 0.6 * abs(tipl + tipr) / 2 and np.sign(tipl) != np.sign(tipr):
            kind = "torsion (twist about y)"
        elif abs(imu) / (abs(tipc) + 1e-30) > 0.35:
            kind = "rotation on servo/gear spring + bending"
        else:
            kind = "plate bending"
        modes.append(dict(f_Hz=freqs[i], kind=kind))
    # gravity moment about hinge from the model's own masses (hand check of the spring)
    res = dict(lc=lc, nodes=len(nodes), tets=len(tets), E=E, ktheta_Nm_per_rad=ktheta_Nm,
               uz_tip_centre_um=U["P_TIPC"][2] * 1e3, uz_tip_left_um=U["P_TIPL"][2] * 1e3,
               uz_tip_right_um=U["P_TIPR"][2] * 1e3, uz_ring_um=0.5 * (U["P_R1"][2] + U["P_R2"][2]) * 1e3,
               rot_gear_face_deg=math.degrees(th_gear), slope_ring_deg=math.degrees(slope_ring), slope_imu_deg=math.degrees(slope_imu),
               angle_err_ring_vs_imu_deg=math.degrees(slope_ring - slope_imu),
               roll_ring_minus_imu_deg=math.degrees(roll_ring - roll_imu),
               vm_max_MPa=float(vm.max()), vm_p99_MPa=float(np.percentile(vm, 99)), modes=modes)
    return res


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    results = dict(provenance=PROV, cad_constants=dict(HINGE_Z=_cad.HINGE_Z, PLATE_Z0=_cad.PLATE_Z0, PLATE_T=_cad.PLATE_T), cases=[])
    if which in ("conv", "all"):
        for lc in (6.0, 5.0, 4.0):
            r = run(lc)
            print("conv", lc, r["nodes"], round(r["uz_tip_centre_um"], 2), [round(m["f_Hz"], 1) for m in r["modes"][:4]], flush=True)
            results["cases"].append(dict(study="mesh", **r))
    if which in ("sens", "all"):
        for E, k in ((PLA["E_LOW"], 120.0), (PLA["E"], 40.0), (PLA["E"], 400.0)):
                r = run(5.0, E=E, ktheta_Nm=k)
                print("sens", E, k, round(r["uz_tip_centre_um"], 2), [(round(m["f_Hz"], 1), m["kind"][:12]) for m in r["modes"][:4]], flush=True)
                results["cases"].append(dict(study="sensitivity", **r))
    save_json(OUT / f"a_tilt_table_fea_{which}.json", results)
