"""FEA (b), test 7 drum shaft and drum. Computed, not measured.

1. Beam theory (hand check) for the Ø25/Ø21 printed tube on two bearings with the drum overhung beyond the
   front one: sag and tilt at the drum, deflection from the gear forces at stall, twist gear -> drum,
   runout from bearing clearance and flange wobble.
2. 3D FEA (CalculiX C3D10) of the shaft (tube + flange + gear ring as a solid ring at the root circle) with
   the CAD drum body (cad/out/step/drum_body.step) bonded to the flange. Gravity + drum payload, the gear
   force at stall, and the stall torque with the drum held.
3. 2D plane-stress FEA (scikit-fem, P2) of one 44T m1 20 deg tooth with a root fillet, tip load at stall,
   against the Lewis equation.
Bearing positions are not in the repo: assumed front bearing centred 35 mm and rear 227.5 mm from the drum
end of the shaft (the auger's z = 15 and 207.5), 10 mm long each; the front one is varied.
"""
import math
import sys

import numpy as np

from fea_common import *

OUT = HERE / "results"
OUT.mkdir(exist_ok=True)
sys.path.insert(0, str(CAD))
import parts as _cad  # noqa: E402

EXT = _cad.DRUM_EXT                     # 20: shaft z of the auger's outlet face
Z_GEAR = EXT + _cad.GEAR_Z0             # gear band starts (98.33)
B_GEAR = 10.0
RO, RI = 12.5, 10.5
L_SHAFT = 225 + EXT
T_STALL = 0.10 * 2.2 * 1e3              # N mm at the 44T gear: 10 N cm holding torque x 2.2
R_PITCH = 22.0
F_T = T_STALL / R_PITCH                 # 10 N
F_R = F_T * math.tan(math.radians(20))  # 3.64 N
M_DRUM = 41.0e-6                        # tonne: body 19 g + bezel 3.5 + window 4.6 + screws 3 + powder 9.4 + disc 1.7
Z_DRUM_CG = -10.0
BEAR = dict(front=(30.0, 40.0), rear=(222.5, 232.5))


# ----------------------------------------------------------------------------------------------
# 1. beam theory
# ----------------------------------------------------------------------------------------------
def beam(E=PLA["E"], zf=35.0, zr=227.5):
    I = math.pi * (2 * RO) ** 4 / 64 - math.pi * (2 * RI) ** 4 / 64
    J = 2 * I
    Gm = E / (2 * (1 + PLA["nu"]))
    L = zr - zf
    a = zf - Z_DRUM_CG                   # overhang, front bearing -> drum CG
    P = M_DRUM * G                       # N
    w_tube = math.pi * (RO ** 2 - RI ** 2) * PLA["rho"] * G   # N/mm
    EI = E * I
    # overhung point load P at distance a beyond support A (span L): tip deflection, tilt at the tip
    d_tip = P * a ** 2 * (L + a) / (3 * EI)
    th_tip = P * a * (2 * L + 3 * a) / (6 * EI)
    # tube self weight over the overhang part (z from 0 to zf, length zf) as a UDL: small; superpose
    q, c = w_tube, zf
    d_q = q * c ** 3 * (4 * L + 3 * c) / (24 * EI)  # overhang UDL tip deflection (simply supported span)
    # gear force (resultant of F_t and F_r) at the gear centre between the bearings, worst direction
    F = math.hypot(F_T, F_R)
    b = Z_GEAR + B_GEAR / 2 - zf        # from A
    bp = L - b
    th_A = F * bp * (L ** 2 - bp ** 2) / (6 * L * EI)
    d_drum_gear = th_A * a              # overhang moves by slope x arm (opposite side)
    twist = T_STALL * (Z_GEAR + B_GEAR / 2) / (Gm * J)
    return dict(E=E, front_bearing_z=zf, rear_bearing_z=zr, span=L, overhang_to_drum_cg=a, I_mm4=I,
                drum_load_N=P, sag_drum_um=(d_tip + d_q) * 1e3, tilt_drum_deg=math.degrees(th_tip),
                gear_force_N=F, drum_shift_at_stall_um=d_drum_gear * 1e3,
                twist_gear_to_drum_deg=math.degrees(twist))


def runout(c_front=0.15, c_rear=0.15, zf=35.0, zr=227.5, flange_tilt_deg=0.2, ecc=0.05):
    """Radial runout at the drum: static offset from bearing clearance (not rotating), plus rotating terms:
    print eccentricity of the tube at the bearings (ecc) amplified by the overhang, and the flange tilt."""
    L = zr - zf
    a = zf - Z_DRUM_CG
    static_offset = c_front + (c_front + c_rear) * a / L
    rot_ecc = ecc * (1 + 2 * a / L)  # both bearing journals eccentric by ecc, opposite phase (worst)
    wobble_rim = 28.0 * math.radians(flange_tilt_deg)  # axial wobble at the drum rim r = 28
    lateral_from_tilt = abs(Z_DRUM_CG) * math.radians(flange_tilt_deg) * 2
    return dict(static_offset_mm=static_offset, rotating_runout_TIR_mm=2 * rot_ecc + lateral_from_tilt,
                axial_wobble_rim_TIR_mm=2 * wobble_rim, assumptions=dict(c_front=c_front, c_rear=c_rear,
                ecc=ecc, flange_tilt_deg=flange_tilt_deg))


# ----------------------------------------------------------------------------------------------
# 2. 3D FEA
# ----------------------------------------------------------------------------------------------
DSTEP, DPROV = get_step("drum_body")


def build(gmsh):
    occ = gmsh.model.occ
    tube = occ.addCylinder(0, 0, 0, 0, 0, L_SHAFT, RO)
    bore = occ.addCylinder(0, 0, 4.0, 0, 0, L_SHAFT, RI)
    fl = occ.addCylinder(0, 0, 0, 0, 0, 4.0, 20.0)
    hole = occ.addCylinder(0, 0, -1, 0, 0, 6, 4.0)
    ring = occ.addCylinder(0, 0, Z_GEAR, 0, 0, B_GEAR, 20.75)
    s, _ = occ.fuse([(3, tube)], [(3, fl), (3, ring)])
    s, _ = occ.cut(s, [(3, bore), (3, hole)])
    drum = occ.importShapes(str(DSTEP))
    occ.rotate(drum, 0, 0, 0, 1, 0, 0, math.pi)  # window faces away from the shaft (-z), rear wall on the flange
    occ.synchronize()
    # fuse: the drum body is screwed to the flange; one PLA solid. The window, bezel, screws and powder
    # (22 g) are added as nodal loads on the drum wall.
    out, _ = occ.fuse(s, [(3, t) for d, t in drum if d == 3])
    occ.synchronize()
    return {"VSHAFT": (3, [t for d, t in out if d == 3])}


def fea(lc, E=PLA["E"], tag=""):
    nodes, tets, vid, _, _ = mesh_tet10(build, lc)
    shaft_nodes = np.zeros(len(nodes) + 1, bool)
    shaft_nodes[np.unique(tets[vid == "VSHAFT"])] = True
    sn = shaft_nodes[1:]
    r = np.hypot(nodes[:, 0], nodes[:, 1])
    z = nodes[:, 2]
    onout = sn & (np.abs(r - RO) < 0.02)
    bf = np.where(onout & (z >= BEAR["front"][0] - 1e-6) & (z <= BEAR["front"][1] + 1e-6))[0] + 1
    br = np.where(onout & (z >= BEAR["rear"][0] - 1e-6) & (z <= BEAR["rear"][1] + 1e-6))[0] + 1
    anchor = [int(br[np.argmax(nodes[br - 1, 0])])]
    gear = np.where(sn & (np.abs(r - 20.75) < 0.02) & (z > Z_GEAR - 1e-6) & (z < Z_GEAR + B_GEAR + 1e-6))[0] + 1
    gear_top = gear[nodes[gear - 1, 1] > 20.0]   # contact patch at +y (pinion side, worst with gravity -y)
    dn = sn & (nodes[:, 2] <= 1e-6)
    drum_wall = np.where(dn & (np.abs(np.hypot(nodes[:, 0], nodes[:, 1]) - 20.0) < 0.05))[0] + 1
    # probes: drum window flange centre-ish points and drum rim
    def near(p, mask):
        d = np.linalg.norm(nodes - np.asarray(p), axis=1)
        d[~mask] = np.inf
        return int(np.argmin(d)) + 1
    probes = dict(P_DRUM_TOP=near((0, 25, -19.5), dn), P_DRUM_BOT=near((0, -25, -19.5), dn),
                  P_DRUM_REAR_TOP=near((0, 25, -1.5), dn), P_DRUM_REAR_BOT=near((0, -25, -1.5), dn),
                  P_GEAR=near((0, 20.75, Z_GEAR + 5), sn), P_FL=near((0, 19, 2), sn))
    ns = {"NBF": bf, "NBR": br, "NBEAR": np.union1d(bf, br), "NANCH": anchor, "NGEARTOP": gear_top,
          "NGEAR": gear, "NDW": drum_wall, "NPROBE": list(probes.values())}
    for k, v in probes.items():
        ns[k] = [v]
    # loads
    f_gear = {n: np.array([0.0, -math.hypot(F_T, F_R) / len(gear_top), 0.0]) for n in gear_top}
    # stall torque about +z on the gear rim: tangential forces proportional to nothing special (uniform)
    f_tq = {}
    rg = r[gear - 1]
    for n in gear:
        x, y = nodes[n - 1, 0], nodes[n - 1, 1]
        ft = T_STALL / (len(gear) * 20.75)
        f_tq[n] = np.array([-y / 20.75 * ft, x / 20.75 * ft, 0.0])
    m_extra = M_DRUM - 15304.0 * PLA["rho"]   # payload beyond the drum body itself
    f_pay = {n: np.array([0.0, -m_extra * G / len(drum_wall), 0.0]) for n in drum_wall}
    mats = {"VSHAFT": dict(E=E, nu=PLA["nu"], rho=PLA["rho"])}
    model = ("*TRANSFORM, NSET=NBEAR, TYPE=C\n0., 0., 0., 0., 0., 1.\n"
             "*TRANSFORM, NSET=NDW, TYPE=C\n0., 0., 0., 0., 0., 1.\n")
    steps = ("*BOUNDARY\nNBEAR, 1, 1, 0.\nNBR, 3, 3, 0.\nNANCH, 2, 2, 0.\n"
             "*STEP\n*STATIC\n*DLOAD\nEALL, GRAV, 9810., 0., -1., 0.\n" + cload_block(f_pay) +
             "*NODE PRINT, NSET=NPROBE, GLOBAL=YES\nU\n*EL PRINT, ELSET=EVSHAFT\nS\n*END STEP\n"
             "*STEP\n*STATIC\n*DLOAD, OP=NEW\n" + cload_block(f_gear).replace("*CLOAD\n", "*CLOAD, OP=NEW\n") +
             "*NODE PRINT, NSET=NPROBE, GLOBAL=YES\nU\n*EL PRINT, ELSET=EVSHAFT\nS\n*END STEP\n"
             "*STEP\n*STATIC\n*BOUNDARY, OP=NEW\nNBEAR, 1, 1, 0.\nNBR, 3, 3, 0.\nNDW, 2, 2, 0.\n*CLOAD, OP=NEW\n" + cload_block(f_tq).replace("*CLOAD\n", "") +
             "*NODE PRINT, NSET=NGEAR, GLOBAL=YES\nU\n*EL PRINT, ELSET=EVSHAFT\nS\n*END STEP\n")
    name = f"drum_lc{lc}_E{int(E)}{tag}"
    (RUNS / "drum").mkdir(parents=True, exist_ok=True)
    inp = write_inp(RUNS / "drum" / f"{name}.inp", nodes, tets, vid, mats, nsets=ns, extra_model=model, steps=steps)
    run_ccx(inp)
    blocks = parse_dat(inp.with_suffix(".dat"))
    disp = [b for b in blocks if b["kind"] == "displacements"]
    strs = [b for b in blocks if b["kind"] == "stresses"]
    out = dict(lc=lc, nodes=len(nodes), tets=len(tets), E=E)
    for k, b in zip(("gravity", "gear_force_stall"), disp[:2]):
        u = {int(row[0]): row[1:4] for row in b["data"]}
        U = {kk: u[v] for kk, v in probes.items()}
        sag = 0.5 * (U["P_DRUM_TOP"][1] + U["P_DRUM_BOT"][1])
        sag_rear = 0.5 * (U["P_DRUM_REAR_TOP"][1] + U["P_DRUM_REAR_BOT"][1])
        tilt = (sag - sag_rear) / (-19.5 + 1.5)  # dy/dz
        out[k] = dict(drum_front_uy_um=sag * 1e3, drum_rear_uy_um=sag_rear * 1e3,
                      drum_tilt_deg=math.degrees(tilt), gear_uy_um=U["P_GEAR"][1] * 1e3)
    for k, b in zip(("gravity", "gear_force_stall", "stall_torque"), strs):
        s = b["data"][:, 2:8]
        out.setdefault(k, {})["vm_max_MPa"] = float(von_mises(s).max())
        out[k]["vm_p99_MPa"] = float(np.percentile(von_mises(s), 99))
    g = disp[2]["data"]
    xy = nodes[g[:, 0].astype(int) - 1, :2]
    th = np.mean((xy[:, 0] * g[:, 2] - xy[:, 1] * g[:, 1]) / (xy[:, 0] ** 2 + xy[:, 1] ** 2))
    out["stall_torque"]["twist_gear_vs_drum_deg"] = math.degrees(th)
    return out


# ----------------------------------------------------------------------------------------------
# 3. one tooth, 2D plane stress (scikit-fem)
# ----------------------------------------------------------------------------------------------
def tooth_geometry(m=1.0, z=44, pa=20.0, rho_f=0.38, n=40):
    """Right and left flanks of the tooth centred on +x, with a circular root fillet of radius rho_f*m
    tangent to the involute (or the radial extension below the base circle) and to the root circle."""
    pa = math.radians(pa)
    rp, ra, rf = m * z / 2, m * z / 2 + m, m * z / 2 - 1.25 * m
    rb = rp * math.cos(pa)
    inv = lambda a: math.tan(a) - a  # noqa: E731
    half = math.pi / (2 * z) + inv(pa)          # half tooth angle at the base circle (involute start)
    rr = rho_f * m
    # flank (upper half, y > 0 side is the 'left' flank): polar angle phi(r) = half - inv(acos(rb/r))
    def flank_phi(r):
        if r <= rb:
            return half
        return half - inv(math.acos(rb / r))
    # find the fillet: circle tangent to the root circle (centre at radius rf + rr) and to the flank
    # (approximate: tangent to the flank near r_start); solve for the centre angle numerically
    r_lo = max(rb, rf) + 0.05 * m
    def flank_pt(r):
        ph = flank_phi(r)
        return np.array([r * math.cos(ph), r * math.sin(ph)])
    def dist_to_flank(c):
        rs = np.linspace(rf, ra, 400)
        pts = np.array([[r * math.cos(max(flank_phi(r), -1)), r * math.sin(flank_phi(r))] for r in rs])
        return np.min(np.linalg.norm(pts - c, axis=1))
    # centre on circle radius rf + rr, at polar angle psi > half (in the gap); find psi where dist = rr
    lo, hi = half, half + math.pi / z
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        c = (rf + rr) * np.array([math.cos(mid), math.sin(mid)])
        if dist_to_flank(c) > rr:
            hi = mid
        else:
            lo = mid
    psi = 0.5 * (lo + hi)
    c = (rf + rr) * np.array([math.cos(psi), math.sin(psi)])
    # tangent point on the flank: closest flank point to c
    rs = np.linspace(rf, ra, 4000)
    pts = np.array([[r * math.cos(flank_phi(r)), r * math.sin(flank_phi(r))] for r in rs])
    k = int(np.argmin(np.linalg.norm(pts - c, axis=1)))
    r_t = rs[k]
    return dict(rp=rp, ra=ra, rf=rf, rb=rb, half=half, psi=psi, centre=c, rr=rr, r_tangent=r_t,
                flank=pts[k:], gap_half_angle=math.pi / z)


def tooth_fea(h_fine, rho_f=0.38, m=1.0, z=44, F_line=None, E=PLA["E"], nu=PLA["nu"], face=B_GEAR):
    import gmsh
    import skfem
    from skfem.models.elasticity import linear_elasticity, lame_parameters
    tg = tooth_geometry(m, z, rho_f=rho_f)
    pitch = 2 * math.pi / z
    r_in = 10.5
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 0)
    occ = gmsh.model.occ
    # one tooth + body sector of +-1.5 pitch; outline built from the upper (left) half, mirrored
    def half_outline():
        pts = []
        # from the tooth tip centre line to the flank top
        phi_tip = math.atan2(tg["flank"][-1][1], tg["flank"][-1][0])
        for t in np.linspace(0, phi_tip, 6):
            pts.append((tg["ra"] * math.cos(t), tg["ra"] * math.sin(t)))
        fl = tg["flank"][::-1]
        idx = np.linspace(0, len(fl) - 1, 40).astype(int)
        pts += [tuple(fl[i]) for i in idx]
        # fillet arc from the flank tangent point to the root circle tangent point (centre c)
        c = tg["centre"]
        a0 = math.atan2(fl[-1][1] - c[1], fl[-1][0] - c[0])
        a1 = math.atan2(-c[1], -c[0])  # towards the gear centre = root-circle tangent point
        if a1 < a0:
            a1 += 2 * math.pi
        if a1 - a0 > math.pi:
            a1 -= 2 * math.pi
        for t in np.linspace(a0, a1, 14)[1:]:
            pts.append((c[0] + tg["rr"] * math.cos(t), c[1] + tg["rr"] * math.sin(t)))
        # root circle to the middle of the gap
        p_end = math.atan2(pts[-1][1], pts[-1][0])
        for t in np.linspace(p_end, tg["gap_half_angle"], 6)[1:]:
            pts.append((tg["rf"] * math.cos(t), tg["rf"] * math.sin(t)))
        return pts
    up = half_outline()
    # body: continue the sector to +-1.5 pitch along the root circle, then down to r_in
    th_end = 1.5 * pitch
    up_ext = list(up)
    # next tooth is not modelled: the body continues along the root circle (conservative: no neighbour)
    for t in np.linspace(tg["gap_half_angle"], th_end, 8)[1:]:
        up_ext.append((tg["rf"] * math.cos(t), tg["rf"] * math.sin(t)))
    lower = [(x, -y) for (x, y) in up_ext[::-1]]
    outline = lower[:-1] + up_ext  # from -th_end around the tooth to +th_end
    # inner arc
    inner = [(r_in * math.cos(t), r_in * math.sin(t)) for t in np.linspace(th_end, -th_end, 16)]
    poly = []
    for q in outline + inner:
        if not poly or math.dist(q, poly[-1]) > 1e-4:
            poly.append(q)
    if math.dist(poly[0], poly[-1]) < 1e-4:
        poly.pop()
    ptags = [occ.addPoint(x, y, 0) for (x, y) in poly]
    lines = [occ.addLine(ptags[i], ptags[(i + 1) % len(ptags)]) for i in range(len(ptags))]
    cl = occ.addCurveLoop(lines)
    surf = occ.addPlaneSurface([cl])
    occ.synchronize()
    gmsh.model.addPhysicalGroup(2, [surf], 1)
    # size field: fine near both root fillets
    fpts = [occ.addPoint(tg["centre"][0], s * tg["centre"][1], 0) for s in (1, -1)]
    occ.synchronize()
    f1 = gmsh.model.mesh.field.add("Distance")
    gmsh.model.mesh.field.setNumbers(f1, "PointsList", fpts)
    f2 = gmsh.model.mesh.field.add("Threshold")
    gmsh.model.mesh.field.setNumber(f2, "InField", f1)
    gmsh.model.mesh.field.setNumber(f2, "SizeMin", h_fine)
    gmsh.model.mesh.field.setNumber(f2, "SizeMax", 0.5)
    gmsh.model.mesh.field.setNumber(f2, "DistMin", tg["rr"] + 0.3)
    gmsh.model.mesh.field.setNumber(f2, "DistMax", 3.0)
    gmsh.model.mesh.field.setAsBackgroundMesh(f2)
    gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 0)
    gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 0)
    gmsh.model.mesh.generate(2)
    _, coords, _ = gmsh.model.mesh.getNodes()
    ntags, _, _ = gmsh.model.mesh.getNodes()
    et, etags, enodes = gmsh.model.mesh.getElements(2, surf)
    tri = np.asarray(enodes[0], dtype=np.int64).reshape(-1, 3)
    gmsh.finalize()
    xy = coords.reshape(-1, 3)[:, :2]
    idmap = {int(t): i for i, t in enumerate(ntags)}
    tri = np.vectorize(idmap.get)(tri)
    used = np.unique(tri)
    remap = -np.ones(len(xy), int)
    remap[used] = np.arange(len(used))
    mesh = skfem.MeshTri(xy[used].T, remap[tri].T)
    e = skfem.ElementVector(skfem.ElementTriP2())
    basis = skfem.Basis(mesh, e)
    # plane stress: modified lambda
    lam, mu = lame_parameters(E, nu)
    lam_ps = 2 * lam * mu / (lam + 2 * mu)
    K = skfem.asm(linear_elasticity(lam_ps, mu), basis)
    # tip load: total F_line (N per mm of face) on the tip corner of the +y flank, along the line of action
    # (tangent to the base circle), pushing the flank: direction from the contact point
    pc = np.array(up[5])  # flank top point
    rb = tg["rb"]
    # tangent from pc to the base circle: unit vector normal to the involute at pc
    rr_pc = np.linalg.norm(pc)
    alpha = math.acos(rb / rr_pc)
    phi = math.atan2(pc[1], pc[0])
    nvec = -np.array([math.cos(phi - alpha + math.pi / 2), math.sin(phi - alpha + math.pi / 2)])
    # make sure the force pushes into the tooth (towards -y side)
    if nvec[1] > 0:
        nvec = -nvec
    # normal tooth load along the line of action: F_n = T / r_b (same at every contact point)
    F_line = F_line if F_line is not None else T_STALL / (tg["rb"] * face)
    # apply as a point force at the dof nearest pc
    dofs = basis.get_dofs()  # noqa
    xdofs = basis.doflocs
    k_near = np.argmin(np.linalg.norm(xdofs.T - pc, axis=1))
    # the two components at that location
    cand = np.where(np.linalg.norm(xdofs.T - xdofs.T[k_near], axis=1) < 1e-9)[0]
    f = np.zeros(basis.N)
    f[cand[0]] += F_line * nvec[0]
    f[cand[1]] += F_line * nvec[1]
    inner = basis.get_dofs(lambda x: np.hypot(x[0], x[1]) < r_in + 1e-6).all()
    u = skfem.solve(*skfem.condense(K, f, D=inner))
    # stresses at P2 nodes via projection of the P1-discontinuous gradient
    from skfem.helpers import sym_grad
    basis0 = basis.with_element(skfem.ElementTriDG(skfem.ElementTriP2()))
    uh = basis.interpolate(u)
    eps = sym_grad(uh)
    exx, eyy, exy = eps[0, 0], eps[1, 1], eps[0, 1]
    sxx = (E / (1 - nu ** 2)) * (exx + nu * eyy)
    syy = (E / (1 - nu ** 2)) * (eyy + nu * exx)
    sxy = (E / (1 + nu)) * exy
    s1 = 0.5 * (sxx + syy) + np.sqrt((0.5 * (sxx - syy)) ** 2 + sxy ** 2)
    s3 = 0.5 * (sxx + syy) - np.sqrt((0.5 * (sxx - syy)) ** 2 + sxy ** 2)
    xq = basis.mapping.F(basis.quadrature[0])
    # restrict to the root region (exclude the load point)
    rq = np.hypot(xq[0], xq[1])
    root = rq < tg["rf"] + 1.2 * m
    s1_root = float(s1[root].max())
    s3_root = float(s3[root].min())
    return dict(h_fine=h_fine, rho_f=rho_f, n_elem=mesh.t.shape[1], n_dof=basis.N,
                s1_root_MPa=s1_root, s3_root_MPa=s3_root, load_N_per_mm=F_line,
                r_tangent=tg["r_tangent"], mesh=mesh, s1=s1, xq=xq)


def lewis(Ft=F_T, b=B_GEAR, m=1.0, Y=0.399, v=None):
    """Lewis: sigma = Kv Ft / (b m Y); Y(44T, 20 deg full depth) = 0.399 (Shigley Table 14-2, interpolated
    between 43T 0.397 and 50T 0.409); Barth Kv = (6.1 + V)/6.1 with V in m/s (cut profile)."""
    V = v if v is not None else math.pi * 0.044 * 109 / 60
    Kv = (6.1 + V) / 6.1
    return dict(Ft_N=Ft, b_mm=b, m=m, Y=Y, V_m_s=V, Kv=Kv, sigma_MPa=Kv * Ft / (b * m * Y))


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    res = dict(provenance=dict(drum_body=DPROV, shaft="simplified from cad/parts.py drum_shaft: tube Ø25/Ø21 x 245, "
                               "flange Ø40 x 4, gear modelled as a solid ring to the root circle Ø41.5"),
               assumptions=dict(bearings=BEAR, drum_payload_g=M_DRUM * 1e6, drum_cg_z=Z_DRUM_CG,
                                stall_torque_Nmm=T_STALL, F_t=F_T, F_r=F_R))
    if which in ("beam", "all", "beamfea"):
        res["beam"] = [beam(E=E, zf=zf) for E in (PLA["E"], PLA["E_LOW"]) for zf in (25.0, 35.0, 55.0)]
        res["runout"] = runout()
        res["lewis"] = lewis()
        print(res["beam"][1], res["runout"], res["lewis"], flush=True)
    if which in ("tooth", "all"):
        tl = []
        for rho in (0.38, 0.2):
            for h in (0.12, 0.06, 0.03):
                t = tooth_fea(h, rho_f=rho)
                t.pop("mesh"); t.pop("s1"); t.pop("xq")
                tl.append(t)
                print("tooth", rho, h, t["n_dof"], round(t["s1_root_MPa"], 3), round(t["s3_root_MPa"], 3), flush=True)
        res["tooth"] = tl
    if which in ("fea", "all", "beamfea"):
        fl = []
        for lc in (5.0, 4.0, 3.0):
            o = fea(lc)
            fl.append(o)
            print("fea", lc, o["nodes"], o["gravity"], o["gear_force_stall"], o["stall_torque"], flush=True)
        o = fea(4.0, E=PLA["E_LOW"])
        fl.append(o)
        print("fea E_low", o, flush=True)
        res["fea"] = fl
    save_json(OUT / f"b_drum_shaft_{which}.json", res)
