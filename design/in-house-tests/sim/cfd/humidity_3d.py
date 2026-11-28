"""Test 6 humidity chamber, diffusion only (no fan), 3D finite volume (scalar.py).

Box 180 x 120 x 90 mm (x, y, z) internal. Slurry tray 150 x 90 x 15 on the floor, centred,
slurry surface at z = 10 mm held at the salt's RH. Perforated shelf (2 mm, 30 % open) at
z = 45-47 mm, 5 mm clear of the walls. Ø60 dish on the shelf centre; sample surface at
z = 50 mm. SHT45 at (140, 60, 60) mm. Water vapour D = 2.5e-5 m2/s, c_sat 23.0 g/m3 (25 C).

Case a: lid closed on room air (RH 0.40) over a NaCl slurry (0.753). Time for the RH at the
  sample and at the sensor to reach 95 % and 99 % of the set point.
Case b: a 2 g rice-flour-like sample (GAB isotherm, 1 mm layer, porous diffusion with local
  sorption equilibrium) is put in after a 10 s lid opening (air above the shelf half
  replaced by room air, below the shelf 10 %). Coupled air + layer, backward Euler.
Case c: deliquescent NaCl sample (surface held at its DRH 0.753) in a KCl box (0.843):
  steady supply-limited uptake rate.
Usage: python humidity_3d.py <h_mm> [cases]   (h = 5 or 2.5)
"""
import json
import sys
import time

import numpy as np

from scalar import Grid, Transport

D = 2.5e-5          # m2/s
CSAT = 0.0230       # kg/m3 at 25 C
LX, LY, LZ = 0.180, 0.120, 0.090
RH_ROOM = 0.40
RH_SET = 0.753      # NaCl, Greenspan 1977, 25 C
SENSOR = (0.140, 0.060, 0.060)
DISH_C = (0.090, 0.060)
DISH_R = 0.030
Z_SLURRY, Z_SHELF0, Z_SHELF1, Z_SAMPLE = 0.010, 0.045, 0.047, 0.050
PHI_OPEN = 0.30
A_SLURRY_REAL = 0.146 * 0.086     # inside 2 mm tray walls

# rice-flour-like sorbent (assumed, typical starchy-food GAB constants at 25 C)
GAB = dict(Xm=0.070, C=10.0, K=0.75)
RHO_B = 680.0       # kg/m3 (bulk, from the battery CSV)
RHO_P = 1450.0
EPS = 1 - RHO_B / RHO_P
TAU = 1.5
D_EFF = D * EPS / TAU
SAMPLE_MASS = 0.002  # kg


def gab(a, Xm=GAB["Xm"], C=GAB["C"], K=GAB["K"]):
    a = np.clip(a, 0.0, 0.99)
    return Xm * C * K * a / ((1 - K * a) * (1 - K * a + C * K * a))


def gab_slope(a, da=1e-4):
    return (gab(a + da) - gab(a - da)) / (2 * da)


def build(h):
    nx, ny, nz = int(round(LX / h)), int(round(LY / h)), int(round(LZ / h))
    xc = (np.arange(nx) + 0.5) * h
    yc = (np.arange(ny) + 0.5) * h
    zc = (np.arange(nz) + 0.5) * h
    X, Y, Z = np.meshgrid(xc, yc, zc, indexing="ij")
    solid = np.zeros((nx, ny, nz), bool)
    Dc = np.full((nx, ny, nz), D)
    # tray: footprint 15..165 x 15..105, walls one cell thick, height 15 mm
    tray = (X > 0.015) & (X < 0.165) & (Y > 0.015) & (Y < 0.105) & (Z < 0.015)
    inner = (X > 0.015 + h) & (X < 0.165 - h) & (Y > 0.015 + h) & (Y < 0.105 - h)
    solid |= tray & ~inner                      # walls
    solid |= inner & (Z < Z_SLURRY)             # slurry (boundary at its top face)
    # shelf layer
    shelf_k = int(Z_SHELF0 / h + 1e-9)
    shelf = (Z > Z_SHELF0) & (Z < Z_SHELF0 + h) & (X > 0.005) & (X < 0.175) & (Y > 0.005) & (Y < 0.115)
    t = Z_SHELF1 - Z_SHELF0
    Dc[shelf] = h / (t / (D * PHI_OPEN) + (h - t) / D)
    # dish (solid) from the shelf to the sample surface, r <= 30 mm
    R = np.hypot(X - DISH_C[0], Y - DISH_C[1])
    dish = (R <= DISH_R) & (Z > Z_SHELF0) & (Z < Z_SAMPLE)
    solid |= dish
    g = Grid((nx, ny, nz), h, Dc, solid=solid, csat=CSAT)
    # Dirichlet faces on the slurry
    ks = int(round(Z_SLURRY / h))
    sl = inner[:, :, ks] & ~solid[:, :, ks]
    cells = g.idx[:, :, ks][sl]
    a_grid = cells.size * h * h
    Gs = D * h * h / (h / 2) * CSAT * (A_SLURRY_REAL / a_grid)
    # cells above the dish
    kd = int(round(Z_SAMPLE / h))
    dtop = (R[:, :, kd] <= DISH_R) & ~solid[:, :, kd]
    dish_cells = g.idx[:, :, kd][dtop]
    i_s = int(SENSOR[0] / h)
    j_s = int(SENSOR[1] / h)
    k_s = int(SENSOR[2] / h)
    sensor = g.idx[i_s, j_s, k_s]
    info = dict(h=h, shape=(nx, ny, nz), n_cells=int(g.n), n_solid=int(solid.sum()),
                slurry_area_grid_mm2=a_grid * 1e6, dish_cells=int(dish_cells.size),
                dish_area_grid_mm2=dish_cells.size * h * h * 1e6)
    return g, cells, Gs, dish_cells, sensor, Z, info


def t_cross(t, y, lev):
    t, y = np.asarray(t), np.asarray(y)
    if y[-1] < lev:
        return None
    k = int(np.argmax(y >= lev))
    if k == 0:
        return 0.0
    return float(np.interp(lev, [y[k - 1], y[k]], [t[k - 1], t[k]]))


def dt_schedule(t, dt_small=1.0, t_small=1500.0, dt_max=30.0):
    if t < t_small:
        return dt_small
    return min(dt_max, dt_small * 1.04 ** ((t - t_small) / dt_small))


def case_a(h, t_end=3600.0):
    g, scells, Gs, dcells, sensor, Z, info = build(h)
    tr = Transport(g, dirichlet=(scells, np.full(scells.size, Gs), RH_SET))
    phi = np.full(g.n, RH_ROOM)
    phi[g.solid.ravel()] = 0.0
    ts, rs, rsens, rmin, rmax = [0.0], [RH_ROOM], [RH_ROOM], [RH_ROOM], [RH_ROOM]
    fl = ~g.solid.ravel()
    t = 0.0
    while t < t_end:
        dt = dt_schedule(t)
        phi = tr.step(phi, dt, solver="cg")
        t += dt
        ts.append(t)
        rs.append(float(phi[dcells].mean()))
        rsens.append(float(phi[sensor]))
        rmin.append(float(phi[fl].min()))
        rmax.append(float(phi[fl].max()))
    res = dict(info=info)
    for name, y in (("sample", rs), ("sensor", rsens), ("box_min", rmin)):
        res[name] = {
            "t_95pct_of_setpoint_s": t_cross(ts, y, 0.95 * RH_SET),
            "t_99pct_of_setpoint_s": t_cross(ts, y, 0.99 * RH_SET),
            "t_95pct_of_step_s": t_cross(ts, y, RH_ROOM + 0.95 * (RH_SET - RH_ROOM)),
            "t_99pct_of_step_s": t_cross(ts, y, RH_ROOM + 0.99 * (RH_SET - RH_ROOM)),
        }
    res["series"] = dict(t=ts, sample=rs, sensor=rsens, box_min=rmin, box_max=rmax)
    # snapshot of a vertical slice through the dish centre at t about 120 s and 300 s
    return res


def layer_setup(g, dcells, h, L, nL):
    A = np.pi * DISH_R ** 2
    dz = L / nL
    n0 = g.n
    # links: layer cell k to k+1; top layer cell (index 0) to the air cells above the dish
    i = np.arange(nL - 1) + n0
    j = i + 1
    Gl = np.full(nL - 1, D_EFF * A / dz * CSAT)
    a_grid = dcells.size * h * h
    Gtop = CSAT * h * h / ((dz / 2) / D_EFF + (h / 2) / D) * (A / a_grid)
    links = (np.concatenate([i, np.full(dcells.size, n0)]), np.concatenate([j, dcells]),
             np.concatenate([Gl, np.full(dcells.size, Gtop)]))
    return A, dz, links


def layer_capacity(phiL, A, dz):
    return A * dz * (EPS * CSAT + RHO_B * gab_slope(phiL))


def case_b(h, L=None, nL=10, t_end=6 * 3600.0, mix_above=0.5, mix_below=0.1):
    g, scells, Gs, dcells, sensor, Z, info = build(h)
    A = np.pi * DISH_R ** 2
    if L is None:
        L = SAMPLE_MASS / (RHO_B * A)
    A, dz, links = layer_setup(g, dcells, h, L, nL)
    phiL = np.full(nL, RH_ROOM)
    C = np.zeros(g.n + nL)
    C[:g.n] = g.vol * CSAT
    C[:g.n][g.solid.ravel()] = 0.0
    C[g.n:] = layer_capacity(phiL, A, dz)
    tr = Transport(g, extra_C=C[g.n:], extra_links=links,
                   dirichlet=(scells, np.full(scells.size, Gs), RH_SET))
    phi = np.zeros(g.n + nL)
    zf = Z.ravel()
    phi[:g.n] = np.where(zf > Z_SHELF1, RH_SET - mix_above * (RH_SET - RH_ROOM),
                         RH_SET - mix_below * (RH_SET - RH_ROOM))
    phi[:g.n][g.solid.ravel()] = 0.0
    phi[g.n:] = phiL
    water0 = RHO_B * A * L * gab(RH_ROOM)
    ts, rs_air, rs_surf, rsens, up, flux_in = [0.0], [float(phi[dcells].mean())], [RH_ROOM], \
        [float(phi[sensor])], [0.0], [0.0]
    t = 0.0
    while t < t_end:
        dt = dt_schedule(t, dt_small=2.0, t_small=600.0, dt_max=60.0)
        C[g.n:] = layer_capacity(phi[g.n:], A, dz)   # Picard (tangent at the old state)
        phi = tr.step(phi, dt, C=C, solver="cg")
        t += dt
        pl = phi[g.n:]
        ts.append(t)
        rs_air.append(float(phi[dcells].mean()))
        rs_surf.append(float(pl[0]))
        rsens.append(float(phi[sensor]))
        water = RHO_B * A * dz * gab(pl).sum()
        up.append(float((water - water0) / SAMPLE_MASS * 1e3))   # mg per g
    # ideal reference: the same layer with its surface held exactly at the set point
    ideal = layer_only(L, nL, t_end)
    eq_uptake = float((gab(RH_SET) - gab(RH_ROOM)) * 1e3)  # mg/g (dry basis)
    res = dict(info=info, layer_thickness_mm=L * 1e3, sample_mass_g=SAMPLE_MASS * 1e3,
               D_eff=D_EFF, eps=EPS, tau=TAU, gab=GAB, rho_b=RHO_B,
               equilibrium_uptake_mg_per_g=eq_uptake,
               water_needed_mg=eq_uptake * SAMPLE_MASS * 1e3,
               box_vapour_at_setpoint_mg=float(LX * LY * LZ * CSAT * RH_SET * 1e6),
               mix_above=mix_above, mix_below=mix_below)
    for name, y in (("sample_air", rs_air), ("sample_surface", rs_surf), ("sensor", rsens)):
        res[name] = {"t_95pct_of_setpoint_s": t_cross(ts, y, 0.95 * RH_SET),
                     "t_99pct_of_setpoint_s": t_cross(ts, y, 0.99 * RH_SET),
                     "min_RH": float(np.min(y))}
    upa = np.array(up)
    res["uptake_t50_s"] = t_cross(ts, upa, 0.5 * eq_uptake)
    res["uptake_t95_s"] = t_cross(ts, upa, 0.95 * eq_uptake)
    res["ideal_uptake_t50_s"] = t_cross(ideal["t"], ideal["uptake"], 0.5 * eq_uptake)
    res["ideal_uptake_t95_s"] = t_cross(ideal["t"], ideal["uptake"], 0.95 * eq_uptake)
    res["max_sensor_minus_sample_RH"] = float(np.max(np.array(rsens) - np.array(rs_surf)))
    res["series"] = dict(t=ts, sample_air=rs_air, sample_surface=rs_surf, sensor=rsens, uptake=up,
                         ideal_t=ideal["t"], ideal_uptake=ideal["uptake"])
    return res


def layer_only(L, nL, t_end, surf=RH_SET, phi0=RH_ROOM):
    """Powder layer alone with its top held at `surf` (no air-side resistance)."""
    A = 1.0
    dz = L / nL
    phi = np.full(nL, phi0)
    ts, up = [0.0], [0.0]
    w0 = gab(phi0) * nL
    t = 0.0
    import scipy.sparse as sp
    import scipy.sparse.linalg as spla
    G = D_EFF / dz * CSAT
    while t < t_end:
        dt = 2.0 if t < 600 else min(60.0, 2.0 * 1.04 ** ((t - 600) / 2.0))
        Cc = dz * (EPS * CSAT + RHO_B * gab_slope(phi))
        main = Cc / dt + 0.0
        dgl = np.zeros(nL)
        dgl[:-1] += G
        dgl[1:] += G
        dgl[0] += D_EFF / (dz / 2) * CSAT
        M = sp.diags([main + dgl, -G * np.ones(nL - 1), -G * np.ones(nL - 1)], [0, 1, -1]).tocsc()
        b = Cc / dt * phi
        b[0] += D_EFF / (dz / 2) * CSAT * surf
        phi = spla.spsolve(M, b)
        t += dt
        ts.append(t)
        up.append(float((gab(phi).sum() - w0) / nL * 1e3))
    return dict(t=ts, uptake=up)


def case_c(h, rh_box=0.843, rh_surf=0.753):
    g, scells, Gs, dcells, sensor, Z, info = build(h)
    a_grid = dcells.size * h * h
    A = np.pi * DISH_R ** 2
    Gd = CSAT * D * h * h / (h / 2) * (A / a_grid)
    cells = np.concatenate([scells, dcells])
    G = np.concatenate([np.full(scells.size, Gs), np.full(dcells.size, Gd)])
    val = np.concatenate([np.full(scells.size, rh_box), np.full(dcells.size, rh_surf)])
    tr = Transport(g, dirichlet=(cells, G, val))
    phi = tr.steady()
    flux = float(np.sum(Gd * (phi[dcells] - rh_surf)))     # kg/s into the sample
    return dict(info=info, rh_box=rh_box, rh_surface=rh_surf, uptake_rate_mg_per_h=flux * 1e6 * 3600,
                sensor_RH=float(phi[sensor]), air_above_sample_RH=float(phi[dcells].mean()))


def main():
    h = float(sys.argv[1]) * 1e-3 if len(sys.argv) > 1 else 0.005
    cases = sys.argv[2] if len(sys.argv) > 2 else "abc"
    out = {}
    t0 = time.time()
    if "a" in cases:
        out["case_a"] = case_a(h)
        print("case a", {k: out["case_a"][k] for k in ("sample", "sensor")}, f"{time.time()-t0:.0f} s", flush=True)
    if "b" in cases:
        out["case_b"] = case_b(h)
        r = out["case_b"]
        print("case b", r["sample_surface"], r["sensor"], r["uptake_t50_s"], r["uptake_t95_s"],
              r["ideal_uptake_t50_s"], r["ideal_uptake_t95_s"], f"{time.time()-t0:.0f} s", flush=True)
    if "c" in cases:
        out["case_c"] = case_c(h)
        print("case c", out["case_c"], f"{time.time()-t0:.0f} s", flush=True)
    out["wall_s"] = time.time() - t0
    fn = f"humidity_3d_h{h*1e3:.1f}mm.json"
    try:                      # merge with cases already on disk (cases can be run separately)
        old = json.load(open(fn))
        old.update(out)
        out = old
    except (OSError, ValueError):
        pass
    with open(fn, "w") as f:
        json.dump(out, f, indent=1)


if __name__ == "__main__":
    main()
