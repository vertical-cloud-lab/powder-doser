"""FEA (e), test 2 cam-drop tapper: impact of the carriage + cylinder + powder after a 3 mm drop on the 304
anvil. Computed, not measured.

1. Impact velocity v = sqrt(2 g h) (h = 3.0 +/- 0.2 mm; PTFE-on-steel bushing friction neglected).
2. Contact stiffness chain from FEA: carriage floor under the Ø25 anvil footprint (cad/out/step/
   tapper_carriage.step) in series with the printed base floor under the anvil (tapper_base.step); steel
   anvil (Ø25 x 6.35) as rigid. Spring-mass: F = v sqrt(k m), a = F/m, contact time pi sqrt(m/k).
3. Quasi-static FEA of the carriage at the peak deceleration: anvil pressure on the striker footprint, the
   cylinder's inertia on the foot pocket floor and the carriage's own inertia as a body force (balanced, 3-2-1
   restraint) -> peak stresses -> fatigue against 15 MPa (assumed endurance, see README).
4. Edge impact if the carriage tilts in the rod clearance (Hertz, PLA flat on the anvil edge).
"""
import math
import sys

import numpy as np

from fea_common import *

OUT = HERE / "results"
OUT.mkdir(exist_ok=True)
sys.path.insert(0, str(CAD))
import parts as _cad  # noqa: E402

CSTEP, CPROV = get_step("tapper_carriage")
BSTEP, BPROV = get_step("tapper_base")
Z_STRIKE = _cad.ANVIL_TOP                      # striker face of the carriage (resting on the anvil)
Z_POCKET = Z_STRIKE + 5.01                     # foot pocket floor (CAD: hex pocket starts at z0 + 5.01)
R_ANVIL = 12.5
M_CYL = 36e-3                                  # kg, 10 mL Class A cylinder: glass tube 14 g + hex foot 22 g (estimate)
M_POWDER = 6e-3
FILL = 0.65                                    # solid fraction of the printed carriage (40 % infill, 3 walls): assumption


def carriage_mass():
    import gmsh
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 0)
    ents = gmsh.model.occ.importShapes(str(CSTEP))
    gmsh.model.occ.synchronize()
    v = sum(gmsh.model.occ.getMass(3, t) for d, t in ents if d == 3)
    gmsh.finalize()
    return v, v * 1.24e-3 * FILL * 1e-3   # mm3, kg


def k_carriage(lc, E):
    def build(gmsh):
        ents = gmsh.model.occ.importShapes(str(CSTEP))
        gmsh.model.occ.synchronize()
        return {"VC": (3, [t for d, t in ents if d == 3])}
    nodes, tets, vid, _, _ = mesh_tet10(build, lc)
    x, y, z = nodes.T
    foot = np.where((np.abs(z - Z_STRIKE) < 1e-6) & (np.hypot(x, y) <= R_ANVIL))[0] + 1
    pocket = np.where(np.abs(z - Z_POCKET) < 1e-6)[0] + 1
    c = int(foot[np.argmin(np.hypot(x[foot - 1], y[foot - 1]))])
    f = {n: np.array([0, 0, 1.0 / len(foot)]) for n in foot}
    ns = {"NFOOT": foot, "NPOCK": pocket, "NC": [c]}
    steps = ("*BOUNDARY\nNPOCK, 1, 3, 0.\n*STEP\n*STATIC\n" + cload_block(f) +
             "*NODE PRINT, NSET=NFOOT, GLOBAL=YES\nU\n*END STEP\n")
    (RUNS / "tap").mkdir(parents=True, exist_ok=True)
    inp = write_inp(RUNS / "tap" / f"kc_{lc}_{int(E)}.inp", nodes, tets, vid, {"VC": dict(E=E, nu=PLA["nu"], rho=PLA["rho"])},
                    nsets=ns, steps=steps)
    run_ccx(inp)
    u = [b for b in parse_dat(inp.with_suffix(".dat")) if b["kind"] == "displacements"][0]["data"]
    return dict(lc=lc, E=E, nodes=len(nodes), k_N_per_mm=1.0 / float(u[:, 3].mean()))


def k_base(lc, E):
    def build(gmsh):
        ents = gmsh.model.occ.importShapes(str(BSTEP))
        gmsh.model.occ.synchronize()
        return {"VB": (3, [t for d, t in ents if d == 3])}
    nodes, tets, vid, _, _ = mesh_tet10(build, lc)
    x, y, z = nodes.T
    zf = _cad.ANVIL_TOP - _cad.ANVIL_T
    floor = np.where((np.abs(z - zf) < 1e-6) & (np.hypot(x, y) <= 12.6))[0] + 1
    bot = np.where(np.abs(z) < 1e-6)[0] + 1
    a = int(bot[np.argmin(np.hypot(x[bot - 1] - 40, y[bot - 1] + 45))])
    b = int(bot[np.argmin(np.hypot(x[bot - 1] + 40, y[bot - 1] + 45))])
    f = {n: np.array([0, 0, -1.0 / len(floor)]) for n in floor}
    ns = {"NFL": floor, "NBOT": bot, "NA": [a], "NB": [b]}
    steps = ("*BOUNDARY\nNBOT, 3, 3, 0.\nNA, 1, 2, 0.\nNB, 2, 2, 0.\n*STEP\n*STATIC\n" + cload_block(f) +
             "*NODE PRINT, NSET=NFL, GLOBAL=YES\nU\n*END STEP\n")
    (RUNS / "tap").mkdir(parents=True, exist_ok=True)
    inp = write_inp(RUNS / "tap" / f"kb_{lc}_{int(E)}.inp", nodes, tets, vid, {"VB": dict(E=E, nu=PLA["nu"], rho=PLA["rho"])},
                    nsets=ns, steps=steps)
    run_ccx(inp)
    u = [b for b in parse_dat(inp.with_suffix(".dat")) if b["kind"] == "displacements"][0]["data"]
    return dict(lc=lc, E=E, nodes=len(nodes), k_N_per_mm=-1.0 / float(u[:, 3].mean()))


def impact(k_N_mm, m_kg, h_mm=3.0):
    v = math.sqrt(2 * 9.81 * h_mm * 1e-3)
    k = k_N_mm * 1e3
    F = v * math.sqrt(k * m_kg)
    return dict(h_mm=h_mm, v_m_s=v, k_N_per_mm=k_N_mm, m_g=m_kg * 1e3, F_peak_N=F, a_peak_g=F / m_kg / 9.81,
                contact_ms=math.pi * math.sqrt(m_kg / k) * 1e3, energy_mJ=0.5 * m_kg * v ** 2 * 1e3)


def stress_fea(lc, F, m_carr, E):
    """Carriage at the peak deceleration a = F / m_total: anvil footprint pressure (up), cylinder + powder
    inertia on the pocket floor (down), carriage inertia as a body force (down); 3-2-1 restraint."""
    def build(gmsh):
        ents = gmsh.model.occ.importShapes(str(CSTEP))
        gmsh.model.occ.synchronize()
        return {"VC": (3, [t for d, t in ents if d == 3])}
    nodes, tets, vid, _, _ = mesh_tet10(build, lc)
    x, y, z = nodes.T
    m_tot = m_carr + M_CYL + M_POWDER
    a = F / m_tot                         # m/s2
    foot = np.where((np.abs(z - Z_STRIKE) < 1e-6) & (np.hypot(x, y) <= R_ANVIL))[0] + 1
    pocket = np.where((np.abs(z - Z_POCKET) < 1e-6) & (np.hypot(x, y) <= 19.0))[0] + 1
    f = {}
    for n in foot:
        f[n] = np.array([0, 0, F / len(foot)])
    for n in pocket:
        f[n] = f.get(n, 0) + np.array([0, 0, -(M_CYL + M_POWDER) * a / len(pocket)])
    c = int(foot[np.argmin(np.hypot(x[foot - 1], y[foot - 1]))])
    e1 = int(foot[np.argmin(np.hypot(x[foot - 1] - 10, y[foot - 1]))])
    e2 = int(foot[np.argmin(np.hypot(x[foot - 1], y[foot - 1] - 10))])
    ns = {"NFOOT": foot, "NC": [c], "NE1": [e1], "NE2": [e2]}
    rho_eff = m_carr * 1e-3 / carriage_mass()[0]   # t/mm3 so that the FEA mass equals m_carr
    steps = ("*BOUNDARY\nNC, 1, 3, 0.\nNE1, 2, 3, 0.\nNE2, 3, 3, 0.\n*STEP\n*STATIC\n"
             f"*DLOAD\nEALL, GRAV, {a * 1e3:.6e}, 0., 0., -1.\n" + cload_block(f) +
             "*NODE PRINT, NSET=NC, TOTALS=ONLY\nRF\n*EL PRINT, ELSET=EALL\nS\n*END STEP\n")
    (RUNS / "tap").mkdir(parents=True, exist_ok=True)
    inp = write_inp(RUNS / "tap" / f"st_{lc}_{int(E)}.inp", nodes, tets, vid, {"VC": dict(E=E, nu=PLA["nu"], rho=rho_eff)},
                    nsets=ns, steps=steps)
    run_ccx(inp)
    bl = parse_dat(inp.with_suffix(".dat"))
    s = [b for b in bl if b["kind"] == "stresses"][0]["data"]
    s6 = s[:, 2:8]
    vm = von_mises(s6)
    s1 = principal_max(s6)
    # stresses away from the loaded footprint (exclude elements whose centroid is within 1 mm of the striker
    # face, where the nodal load lumping concentrates): report both
    cent = np.array([nodes[t[:4] - 1].mean(axis=0) for t in tets])
    away = cent[:, 2] > Z_STRIKE + 1.0
    eid = s[:, 0].astype(int) - 1
    mask = away[eid]
    rf = [b for b in bl if b["kind"] == "total force"]
    return dict(lc=lc, E=E, nodes=len(nodes), a_m_s2=a, s1_max_MPa=float(s1.max()), vm_max_MPa=float(vm.max()),
                s1_max_away_MPa=float(s1[mask].max()), vm_max_away_MPa=float(vm[mask].max()),
                s1_p999_MPa=float(np.percentile(s1, 99.9)),
                residual_reaction_N=(rf[0]["data"].tolist() if rf else None))


def hertz_edge(m_kg, h_mm=3.0, r_edge=0.5, R_ring=12.5, E1=PLA["E"], nu1=PLA["nu"], E2=STEEL["E"], nu2=STEEL["nu"],
               lever_ratio=0.8):
    """Tilted carriage hitting the anvil edge: PLA flat on the anvil's edge round (r_edge) along its rim
    circle (R_ring): equivalent sphere radius sqrt(r_edge R_ring); effective mass lever_ratio * m."""
    Es = 1.0 / ((1 - nu1 ** 2) / E1 + (1 - nu2 ** 2) / E2) * 1e6   # Pa
    R = math.sqrt(r_edge * R_ring) * 1e-3
    m = lever_ratio * m_kg
    v = math.sqrt(2 * 9.81 * h_mm * 1e-3)
    dmax = (15 * m * v ** 2 / (16 * Es * math.sqrt(R))) ** 0.4
    F = 4 / 3 * Es * math.sqrt(R) * dmax ** 1.5
    a = math.sqrt(R * dmax)
    p0 = 3 * F / (2 * math.pi * a ** 2)
    return dict(R_eq_mm=R * 1e3, F_peak_N=F, contact_radius_mm=a * 1e3, p0_MPa=p0 / 1e6,
                tau_max_MPa=0.31 * p0 / 1e6, depth_tau_max_mm=0.48 * a * 1e3)


def fatigue(s_max, s_e=PLA["s_fat"], s_u=PLA["sy"], taps_per_test=1250, tests_per_year=2000, b=-0.083):
    """Each tap is a 0 -> s_max cycle (R = 0): amplitude = mean = s_max / 2. Goodman: s_a / s_e + s_m / s_u.
    Life from Basquin with endurance s_e at 1e7 cycles and exponent b (assumed), if Goodman > 1."""
    sa = sm = s_max / 2
    g = sa / s_e + sm / s_u
    yearly = taps_per_test * tests_per_year
    if g <= 1:
        life = math.inf
    elif sm >= s_u:
        life = 0.0
    else:
        sa_eq = sa / (1 - sm / s_u)
        life = 1e7 * (sa_eq / s_e) ** (1 / b)
    return dict(s_max_MPa=s_max, goodman=g, taps_per_year=yearly, life_taps=life,
                life_years=life / yearly if math.isfinite(life) else math.inf)


if __name__ == "__main__":
    vol, m_carr = carriage_mass()
    m_tot = m_carr + M_CYL + M_POWDER
    res = dict(provenance=dict(carriage=CPROV, base=BPROV), carriage_volume_mm3=vol, carriage_mass_g=m_carr * 1e3,
               fill_fraction=FILL, m_cylinder_g=M_CYL * 1e3, m_powder_g=M_POWDER * 1e3, m_total_g=m_tot * 1e3,
               spec_mass_g=70.0)
    print(res, flush=True)
    kc = [k_carriage(lc, PLA["E_LOW"]) for lc in (4.0, 3.0, 2.2)]
    kc.append(k_carriage(3.0, PLA["E"]))
    kb = [k_base(lc, PLA["E_LOW"]) for lc in (5.0, 4.0, 3.0)]
    kb.append(k_base(4.0, PLA["E"]))
    print(kc, kb, flush=True)
    res["k_carriage"], res["k_base"] = kc, kb
    imp = []
    for E_lab, kcar, kbas in (("E 2.3 GPa", kc[2]["k_N_per_mm"], kb[2]["k_N_per_mm"]),
                              ("E 3.5 GPa", kc[3]["k_N_per_mm"], kb[3]["k_N_per_mm"])):
        k = 1 / (1 / kcar + 1 / kbas)
        for m in (0.070, m_tot, 0.110):
            for h in (2.8, 3.0, 3.2):
                d = impact(k, m, h)
                d["E"] = E_lab
                imp.append(d)
    res["impact"] = imp
    nom = [d for d in imp if d["E"] == "E 2.3 GPa" and abs(d["m_g"] - m_tot * 1e3) < 1e-6 and d["h_mm"] == 3.0][0]
    hi = max(d["F_peak_N"] for d in imp)
    print("impact nominal", nom, "max F", hi, flush=True)
    st = [stress_fea(lc, nom["F_peak_N"], m_carr, PLA["E_LOW"]) for lc in (4.0, 3.0, 2.2)]
    res["stress"] = st
    print(st, flush=True)
    s_hi = st[-1]["s1_max_away_MPa"] * hi / nom["F_peak_N"]
    res["fatigue_nominal"] = fatigue(st[-1]["s1_max_away_MPa"])
    res["fatigue_worst_force"] = fatigue(s_hi)
    res["edge_impact"] = [hertz_edge(m_tot, r_edge=r) for r in (0.2, 0.5, 2.0)]
    tilt = 2 * 0.25 / 69.0
    res["tilt_in_rod_clearance"] = dict(radial_clearance_mm=0.25, bushing_spacing_mm=69.0, tilt_deg=math.degrees(tilt),
                                        edge_lift_over_anvil_mm=25.0 * tilt)
    e_rest = (0.6, 0.8)
    res["bounce"] = [dict(e=e, height_mm=e ** 2 * 3.0, airtime_ms=2 * math.sqrt(2 * e ** 2 * 3e-3 / 9.81) * 1e3)
                     for e in e_rest]
    res["tap_period_ms"] = 60e3 / 250
    res["free_fall_ms"] = math.sqrt(2 * 3e-3 / 9.81) * 1e3
    save_json(OUT / "e_tapper.json", res)
    print(res["fatigue_nominal"], res["fatigue_worst_force"], res["edge_impact"], flush=True)
