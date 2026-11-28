"""FEA (g), in-chamber tripod (tests 1, 5, 10): deflection, sway frequency and tip stability under the heaviest
payload. Computed, not measured.

Geometry from cad/parts.py (tripod_spider, tripod_leg): spider hub r 20/12 x 6, three arms 10 wide x 6 thick
from r 14 to the legs at r 62 (90, 210, 330 deg), bosses r 7.5; legs 8 x 8 square, H = 40-160 mm, their top
4.5 mm in the spider's sockets (modelled as bonded). Payload (heaviest, test 10): fc_cradle (disc r 42 x 4 +
wall r 42/35.4 x 14, printed) plus the can, cup, lid, base and standoffs as a stiff cylinder r 35 x 80 of
total mass M_PAY on the cradle. Feet: pinned at the pad centre (rocking allowed) or fully fixed (glued).
"""
import math
import sys

import numpy as np

from fea_common import *

OUT = HERE / "results"
OUT.mkdir(exist_ok=True)
sys.path.insert(0, str(CAD))
import parts as _cad  # noqa: E402

R_LEG = _cad.TRIPOD_R
AF = _cad.LEG_AF
ANG = [90.0, 210.0, 330.0]
M_PAY = 120e-6      # tonne: Al can 58 g + cup 20 g + PLA lid 20 g + insulator base 14 g + standoffs, screws 8 g
M_CRADLE = 31e-6    # printed cradle (41.8 cm3 at about 60 % solid)
FILL = 0.6          # printed spider / legs solid fraction (assumption)


def build_factory(H):
    def build(gmsh):
        occ = gmsh.model.occ
        z_sp = H - 4.5
        parts = []
        hub = occ.addCylinder(0, 0, z_sp, 0, 0, 6, 20.0)
        hub_in = occ.addCylinder(0, 0, z_sp - 1, 0, 0, 8, 12.0)
        sp, _ = occ.cut([(3, hub)], [(3, hub_in)])
        parts += sp
        for a in ANG:
            ar = math.radians(a)
            arm = occ.addBox(14, -5, z_sp, R_LEG - 14, 10, 6)
            occ.rotate([(3, arm)], 0, 0, 0, 0, 0, 1, ar)
            boss = occ.addCylinder(R_LEG * math.cos(ar), R_LEG * math.sin(ar), z_sp, 0, 0, 6, 7.5)
            leg = occ.addBox(R_LEG - AF / 2, -AF / 2, 0, AF, AF, H)
            occ.rotate([(3, leg)], 0, 0, 0, 0, 0, 1, ar)
            parts += [(3, arm), (3, boss), (3, leg)]
        tri, _ = occ.fuse(parts[:1], parts[1:])
        cr = occ.addCylinder(0, 0, z_sp + 6, 0, 0, 4, 42.0)
        crw_o = occ.addCylinder(0, 0, z_sp + 10, 0, 0, 14, 42.0)
        crw_i = occ.addCylinder(0, 0, z_sp + 10, 0, 0, 14, 35.4)
        crw, _ = occ.cut([(3, crw_o)], [(3, crw_i)])
        cradle, _ = occ.fuse([(3, cr)], crw)
        pay = occ.addCylinder(0, 0, z_sp + 10, 0, 0, 80, 35.0)
        out, omap = occ.fragment(tri, cradle + [(3, pay)])
        occ.synchronize()
        vt = [t for d, t in omap[0]]
        vp = [t for d, t in omap[-1]]
        vc = [t for d, t in out if d == 3 and t not in vt + vp]
        return {"VTRI": (3, vt), "VCRAD": (3, vc), "VPAY": (3, vp)}
    return build


def run(H, lc, feet="pinned", E=PLA["E"]):
    nodes, tets, vid, _, _ = mesh_tet10(build_factory(H), lc)
    x, y, z = nodes.T
    vol = {k: 0.0 for k in ("VTRI", "VCRAD", "VPAY")}
    for k in vol:
        e = tets[vid == k]
        a, b, c, d = [nodes[e[:, i] - 1] for i in range(4)]
        vol[k] = float(np.abs(np.einsum("ij,ij->i", np.cross(b - a, c - a), d - a)).sum() / 6)
    rho = {"VTRI": PLA["rho"] * FILL, "VCRAD": M_CRADLE / vol["VCRAD"], "VPAY": M_PAY / vol["VPAY"]}
    mats = {"VTRI": dict(E=E, nu=PLA["nu"], rho=rho["VTRI"]), "VCRAD": dict(E=E, nu=PLA["nu"], rho=rho["VCRAD"]),
            "VPAY": dict(E=ALU["E"], nu=ALU["nu"], rho=rho["VPAY"])}
    feet_c, feet_all = [], []
    for a in ANG:
        ar = math.radians(a)
        cx, cy = R_LEG * math.cos(ar), R_LEG * math.sin(ar)
        on = np.where((np.abs(z) < 1e-6) & (np.hypot(x - cx, y - cy) < AF))[0] + 1
        feet_all += list(on)
        feet_c.append(int(on[np.argmin(np.hypot(x[on - 1] - cx, y[on - 1] - cy))]))
    z_sp = H - 4.5
    top = np.where((np.abs(z - (z_sp + 90)) < 1e-6) & (np.hypot(x, y) < 35.0))[0] + 1
    cg_z = z_sp + 10 + 40
    probe = int(np.argmin(np.hypot(x, y) + np.abs(z - (z_sp + 90)))) + 1
    ns = {"NFEET": feet_all if feet == "fixed" else feet_c, "NTOP": top, "NPR": [probe]}
    flat = {n: np.array([1.0 / len(top), 0, 0]) for n in top}
    steps = ("*BOUNDARY\nNFEET, 1, 3, 0.\n"
             "*STEP\n*STATIC\n*DLOAD\nEALL, GRAV, 9810., 0., 0., -1.\n*NODE PRINT, NSET=NPR, GLOBAL=YES\nU\n"
             "*EL PRINT, ELSET=EVTRI\nS\n*NODE PRINT, NSET=NFEET, TOTALS=ONLY\nRF\n*END STEP\n"
             "*STEP\n*STATIC\n*DLOAD, OP=NEW\n" + cload_block(flat) + "*NODE PRINT, NSET=NPR, GLOBAL=YES\nU\n*END STEP\n"
             "*STEP\n*FREQUENCY\n4\n*END STEP\n")
    (RUNS / "tripod").mkdir(parents=True, exist_ok=True)
    inp = write_inp(RUNS / "tripod" / f"tri_H{int(H)}_{feet}_{lc}_{int(E)}.inp", nodes, tets, vid, mats, nsets=ns,
                    steps=steps)
    run_ccx(inp)
    bl = parse_dat(inp.with_suffix(".dat"))
    d = [b for b in bl if b["kind"] == "displacements"]
    s = [b for b in bl if b["kind"] == "stresses"][0]["data"][:, 2:8]
    rf = [b for b in bl if b["kind"] == "total force"]
    fr = parse_freqs(inp.with_suffix(".dat"))
    return dict(H=H, lc=lc, feet=feet, E=E, nodes=len(nodes), mass_g=(sum(rho[k] * vol[k] for k in vol) * 1e6),
                top_sag_um=float(d[0]["data"][0, 3] * 1e3), lateral_um_per_N=float(d[1]["data"][0, 1] * 1e3),
                k_lateral_N_per_mm=float(1.0 / d[1]["data"][0, 1]), vm_max_MPa=float(von_mises(s).max()),
                weight_N=(float(rf[0]["data"][0, 2]) if rf else None), freqs_Hz=fr[:4])


def hand(H, E=PLA["E"]):
    I = AF ** 4 / 12
    m_tri = FILL * PLA["rho"] * 1e3 * (3 * AF ** 2 * H + 13414.0)            # kg-ish: t->kg x 1e3
    m_top = (M_PAY + M_CRADLE) * 1e3 + FILL * PLA["rho"] * 1e3 * 13414.0
    # legs fixed in the spider (rigid ring), pinned at the floor: each k = 3 E I / H^3
    k1 = 3 * 3 * E * I / H ** 3        # N/mm
    k2 = 3 * 12 * E * I / H ** 3       # feet fixed: guided-fixed legs
    f1 = math.sqrt(k1 * 1e3 / m_top) / (2 * math.pi)
    f2 = math.sqrt(k2 * 1e3 / m_top) / (2 * math.pi)
    P_euler = math.pi ** 2 * E * I / (H ** 2)  # pinned-fixed with sway: effective length about H (K = 1)... per leg
    return dict(H=H, k_lat_pinned_N_per_mm=k1, k_lat_fixed_N_per_mm=k2, f_sway_pinned_Hz=f1, f_sway_fixed_Hz=f2,
                m_top_kg=m_top, euler_per_leg_N=P_euler)


def tip(H):
    """Static tipping: lateral force at height h_F that lifts two feet. Support triangle of three feet at
    r = 62: inradius 31 mm (tipping toward an edge), 62 mm toward a leg."""
    g = 9.81
    m_tri = FILL * 1.24e-3 * (3 * AF ** 2 * H + 13414.0) * 1e-3   # kg
    res = {}
    # test 10: centred payload
    m10 = m_tri + (M_PAY + M_CRADLE) * 1e3
    zc10 = (m_tri * H * 0.6 + (M_PAY + M_CRADLE) * 1e3 * (H + 45)) / m10
    hF = H + 90.0
    res["test10_faraday"] = dict(mass_g=m10 * 1e3, cg_height_mm=zc10, cg_offset_mm=0.0,
                                 F_tip_edge_N=m10 * g * 31.0 / hF, F_tip_leg_N=m10 * g * 62.0 / hF, force_height_mm=hF)
    # test 5: cup holder arm along +x (cad cup_holder): cup at x 74, solenoid cradle at (76, 32)
    items = [(13.5e-3, 50.0, 0.0), (22e-3, 74.0, 0.0), (13e-3, 90.0, 0.0), (20e-3, 76.0, 32.0)]
    m5 = m_tri + sum(m for m, _, _ in items)
    cx = sum(m * x for m, x, _ in items) / m5
    cy = sum(m * y for m, _, y in items) / m5
    r_cg = math.hypot(cx, cy)
    ang = math.degrees(math.atan2(cy, cx))
    # distance from the centre to the support boundary along the CG direction
    def boundary(theta_deg):
        best = 1e9
        for e in (30.0, 150.0, 270.0):        # edge normals (midway between legs)
            c = math.cos(math.radians(theta_deg - e))
            if c > 1e-9:
                best = min(best, 31.0 / c)
        return best
    b_cg = boundary(ang)
    res["test5_cup_holder_as_drawn"] = dict(mass_g=m5 * 1e3, cg_offset_mm=r_cg, cg_angle_deg=ang,
                                            support_boundary_along_cg_mm=b_cg, stable=r_cg < b_cg,
                                            items="holder 13.5 g at x 50, cup+disc+gate+powder 22 g at x 74, "
                                                  "micro servo 13 g at x 90, JF-0530B 20 g at (76, 32): estimates")
    # best case: arm pointed at a leg
    res["test5_cup_holder_toward_leg"] = dict(support_boundary_mm=62.0, margin_mm=62.0 - r_cg,
                                              F_tip_at_top_N=max(0.0, m5 * g * (62.0 - r_cg) / (H + 26.0)))
    # ballast needed at the hub (or in the feet, which also lowers the CG) to bring the CG within 20 mm
    need = max(0.0, (m5 * r_cg / 20.0) - m5)
    res["test5_ballast_on_axis_for_20mm_cg_g"] = need * 1e3
    return res


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    res = dict(provenance="geometry rebuilt from cad/parts.py tripod_spider / tripod_leg / fc_cradle "
                          f"(parts.py sha256 {sha12(CAD / 'parts.py')})",
               assumptions=dict(M_payload_g=M_PAY * 1e6, M_cradle_g=M_CRADLE * 1e6, fill=FILL),
               hand=[hand(H) for H in (40, 80, 120, 160)], tip={H: tip(H) for H in (40, 80, 120, 160)}, fea=[])
    print(res["hand"][-1], res["tip"][160], flush=True)
    if which in ("fea", "all"):
        for lc in (5.0, 3.5, 2.5):
            o = run(160.0, lc)
            res["fea"].append(o)
            print(o, flush=True)
        for feet in ("fixed",):
            o = run(160.0, 3.5, feet=feet)
            res["fea"].append(o)
            print(o, flush=True)
        o = run(80.0, 3.5)
        res["fea"].append(o)
        print(o, flush=True)
    save_json(OUT / f"g_tripod_{which}.json", res)
