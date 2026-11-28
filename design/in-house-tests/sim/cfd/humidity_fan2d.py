"""Test 6 humidity chamber with a 25 mm 5 V fan: 2D vertical section (x-z) through the box centre.

Flow: mac2d (planar), 1 mm grid, constant effective (eddy) viscosity nu_eff, hybrid differencing.
  The fan is a 25 mm tall momentum source (velocity relaxation) of 10 mm length. A round 25 mm
  fan in a 120 mm deep box is represented by a slot of the same momentum flux per unit depth:
  U_slot = U_fan * sqrt(pi D / (4 W)) = 0.405 U_fan.  nu_eff = 0.037 U b_1/2 (plane jet, Pope 2000)
  = 3e-4 m2/s for U = 0.6 m/s, b = 12.5 mm; Sc_t = 0.7. Perforated shelf: pressure-loss coefficient
  K = (1/(0.62 phi) - 1)^2 = 19 for phi = 0.30 on the through-flow, no flow along it.
Vapour: scalar.py on the same grid, D_eff = D + nu_t/Sc_t, slurry and sample surfaces by a wall
  function (laminar flat plate, Sh = 0.664 Re^0.5 Sc^(1/3), times 1 or 2 for fan turbulence).
  2D-to-3D: slurry conductance scaled by 0.717 (its depth 86 of 120 mm), dish by 0.393.
Fan positions: "below" (under the shelf, blowing across the slurry) and "above" (over the dish).
Usage: python humidity_fan2d.py flow <below|above> [nu_eff]   then   python humidity_fan2d.py vapour
"""
import json
import sys
import time

import numpy as np

from mac2d import MAC2D
from scalar import Grid, Transport
import humidity_3d as h3

H = 0.001
LX, LZ = 0.180, 0.090
NX, NZ = int(round(LX / H)), int(round(LZ / H))
NU_AIR = 1.56e-5
SC_T = 0.7
U_FAN = 1.5
U_SLOT = U_FAN * np.sqrt(np.pi * 0.025 / (4 * 0.120))
K_SHELF = (1 / (0.62 * 0.30) - 1) ** 2
F_SLURRY = (0.146 * 0.086) / (0.146 * 0.120)
F_DISH = (np.pi * 0.030 ** 2) / (0.060 * 0.120)
SENSOR = (0.140, 0.060)


def geometry(fan):
    xc = (np.arange(NX) + 0.5) * H
    zc = (np.arange(NZ) + 0.5) * H
    X, Z = np.meshgrid(xc, zc, indexing="ij")
    solid = np.zeros((NX, NZ), bool)
    solid |= ((X > 0.015) & (X < 0.017) | (X > 0.163) & (X < 0.165)) & (Z < 0.015)   # tray walls
    solid |= (X > 0.017) & (X < 0.163) & (Z < 0.010)                                    # slurry
    shelf = (X > 0.005) & (X < 0.175) & (Z > 0.045) & (Z < 0.047)
    dish = (X > 0.060) & (X < 0.120) & (Z > 0.045) & (Z < 0.050)
    rim = ((X > 0.059) & (X < 0.060) | (X > 0.120) & (X < 0.121)) & (Z > 0.045) & (Z < 0.052)
    solid |= dish | rim
    if fan == "below":
        z0, z1 = 0.0175, 0.0425
    else:
        z0, z1 = 0.055, 0.080
    x0, x1 = 0.020, 0.030
    frame = (X > x0) & (X < x1) & (((Z > z0 - 0.001) & (Z < z0)) | ((Z > z1) & (Z < z1 + 0.001)))
    solid |= frame
    fanreg = (X > x0 + 0.002) & (X < x1 - 0.002) & (Z > z0) & (Z < z1)
    return X, Z, solid, shelf & ~solid, fanreg, (x0, x1, z0, z1)


def run_flow(fan, nu_eff=3e-4, t_end=12.0):
    X, Z, solid, shelf, fanreg, box = geometry(fan)
    s = MAC2D(NX, NZ, LX, LZ, nu=nu_eff, top="wall", upwind=0.0)
    s.solid = solid
    s._masks()
    # no horizontal flow inside the shelf: block u faces whose both neighbours are shelf/solid
    sh = shelf | solid
    s.ufix[1:-1, :] |= shelf[:-1, :] | shelf[1:, :]
    s._poisson()
    # fan: relax u to U_SLOT on faces inside the fan region
    cu = np.zeros_like(s.u)
    ut = np.zeros_like(s.u)
    fr = np.zeros_like(s.u, bool)
    fr[1:-1, :] = fanreg[:-1, :] & fanreg[1:, :]
    s.cu = np.where(fr, 200.0, 0.0)
    s.u_target = np.where(fr, U_SLOT, 0.0)
    # shelf through-flow loss on v faces between two shelf cells or at its faces
    vsh = np.zeros_like(s.v, bool)
    vsh[:, 1:-1] = shelf[:, :-1] & shelf[:, 1:]
    nf = max(1, int(round(0.002 / H)) - 1)

    def cv_fun(sol):
        return np.where(vsh, K_SHELF * np.abs(sol.v) / (2 * H * nf), 0.0)

    s.cv_fun = cv_fun
    umax = 1.3 * U_SLOT
    dt = 0.8 * min(0.25 * H * H / nu_eff, 2 * nu_eff / umax ** 2, H / umax)
    t0 = time.time()
    hist = []
    nsteps = int(t_end / dt)
    uacc = np.zeros_like(s.u)
    vacc = np.zeros_like(s.v)
    nacc = 0
    for n in range(nsteps):
        du = s.step(dt)
        if n % 1000 == 0:
            ke = float(0.5 * (np.mean(s.u ** 2) + np.mean(s.v ** 2)))
            hist.append((n * dt, ke, float(du)))
            print(f"  t = {n*dt:.2f} s  KE = {ke:.3e}  du/dt = {du:.2e}", flush=True)
        if n * dt > 0.6 * t_end:
            uacc += s.u
            vacc += s.v
            nacc += 1
    s.u, s.v = uacc / nacc, vacc / nacc        # time average over the last 40 %
    uc, vc = s.cell_velocity()
    spd = np.hypot(uc, vc)
    # tangential speed 2-10 mm above the slurry and the sample
    band_s = (X > 0.017) & (X < 0.163) & (Z > 0.012) & (Z < 0.020)
    band_d = (X > 0.060) & (X < 0.120) & (Z > 0.052) & (Z < 0.060)
    flux_fan = float(np.sum(s.u[int(0.025 / H), :][(Z[0, :] > box[2]) & (Z[0, :] < box[3])]) * H)
    out = dict(fan=fan, nu_eff=nu_eff, U_fan=U_FAN, U_slot=float(U_SLOT), dt=dt, steps=nsteps,
               wall_s=time.time() - t0, hist=hist,
               speed_over_slurry=float(np.mean(np.abs(uc[band_s]))),
               speed_over_dish=float(np.mean(np.abs(uc[band_d]))),
               max_speed=float(spd.max()), mean_speed=float(spd[~solid].mean()),
               fan_flow_per_depth_m2s=flux_fan,
               fan_flow_3d_Lps=flux_fan * 0.120 * 1e3,
               max_div=float(np.abs(s.divergence(s.u, s.v)[~solid]).max()))
    np.savez_compressed(f"fanflow_{fan}_nu{nu_eff:.0e}.npz", u=s.u, v=s.v, solid=solid, shelf=shelf)
    json.dump(out, open(f"fanflow_{fan}_nu{nu_eff:.0e}.json", "w"), indent=1)
    print({k: v for k, v in out.items() if k != "hist"}, flush=True)
    return out


def k_flat(U, L, enh=1.0):
    Sc = NU_AIR / h3.D
    Re = max(U, 1e-6) * L / NU_AIR
    return enh * 0.664 * Re ** 0.5 * Sc ** (1 / 3) * h3.D / L


def vapour_grid(flow, enh=1.0):
    """Build the transport problem for a flow file (or None = still air)."""
    fan = flow["fan"] if flow else "below"
    X, Z, solid, shelf, fanreg, box = geometry(fan)
    if flow:
        d = np.load(f"fanflow_{flow['fan']}_nu{flow['nu_eff']:.0e}.npz")
        vel = (d["u"], d["v"])
        Dt = h3.D + (flow["nu_eff"] - NU_AIR) / SC_T
    else:
        vel = None
        Dt = h3.D
        solid = solid & ~fanreg      # no fan in the still-air case is the same box
    Dc = np.full((NX, NZ), Dt)
    t = 0.002
    Dc[shelf] = H / (t / (Dt * 0.30) + max(H - t, 0) / Dt) if H > t else Dt * 0.30
    g = Grid((NX, NZ), H, Dc, solid=solid, csat=h3.CSAT)
    # slurry surface: first fluid row above z = 10 mm inside the tray walls
    ks = int(round(0.010 / H))
    xs = (X[:, ks] > 0.017) & (X[:, ks] < 0.163)
    scells = g.idx[:, ks][xs]
    if flow:
        km = k_flat(flow["speed_over_slurry"], 0.146, enh)
        Gs = h3.CSAT * H * 1.0 / (1.0 / km + 0) * F_SLURRY
    else:
        km = h3.D / (H / 2)
        Gs = h3.CSAT * H * km * F_SLURRY
    kd = int(round(0.050 / H))
    xd = (X[:, kd] > 0.060) & (X[:, kd] < 0.120)
    dcells = g.idx[:, kd][xd]
    if flow:
        kmd = k_flat(flow["speed_over_dish"], 0.060, enh)
    else:
        kmd = h3.D / (H / 2)
    sensor = g.idx[int(SENSOR[0] / H), int(SENSOR[1] / H)]
    return g, vel, scells, Gs, dcells, kmd, sensor, Z, km


def vapour_case_a(flow, enh=1.0, t_end=1800.0):
    g, vel, scells, Gs, dcells, kmd, sensor, Z, km = vapour_grid(flow, enh)
    tr = Transport(g, dirichlet=(scells, np.full(scells.size, Gs), h3.RH_SET), vel=vel)
    phi = np.full(g.n, h3.RH_ROOM)
    phi[g.solid.ravel()] = 0.0
    fl = ~g.solid.ravel()
    ts, rs, rsen, spread = [0.0], [h3.RH_ROOM], [h3.RH_ROOM], [0.0]
    t = 0.0
    while t < t_end:
        dt = 0.25 if t < 120 else (1.0 if t < 900 else 5.0)
        phi = tr.step(phi, dt, solver="lu")
        t += dt
        ts.append(t)
        rs.append(float(phi[dcells].mean()))
        rsen.append(float(phi[sensor]))
        spread.append(float(phi[fl].max() - phi[fl].min()))
    res = dict(k_slurry=km, k_dish=kmd)
    for name, y in (("sample", rs), ("sensor", rsen)):
        res[name] = {"t_95pct_of_setpoint_s": h3.t_cross(ts, y, 0.95 * h3.RH_SET),
                     "t_99pct_of_setpoint_s": h3.t_cross(ts, y, 0.99 * h3.RH_SET),
                     "t_95pct_of_step_s": h3.t_cross(ts, y, h3.RH_ROOM + 0.95 * (h3.RH_SET - h3.RH_ROOM)),
                     "t_99pct_of_step_s": h3.t_cross(ts, y, h3.RH_ROOM + 0.99 * (h3.RH_SET - h3.RH_ROOM))}
    res["series"] = dict(t=ts[::4], sample=rs[::4], sensor=rsen[::4], spread=spread[::4])
    return res


def vapour_case_b(flow, enh=1.0, t_end=6 * 3600.0, nL=10):
    g, vel, scells, Gs, dcells, kmd, sensor, Z, km = vapour_grid(flow, enh)
    A = 0.060 * F_DISH            # dish area per unit depth of the section
    L = h3.SAMPLE_MASS / (h3.RHO_B * np.pi * h3.DISH_R ** 2)
    dz = L / nL
    n0 = g.n
    i = np.arange(nL - 1) + n0
    Gl = np.full(nL - 1, h3.D_EFF * A / dz * h3.CSAT)
    a_grid = dcells.size * H
    Gtop = h3.CSAT * H / ((dz / 2) / h3.D_EFF + 1.0 / kmd) * (A / a_grid)
    links = (np.concatenate([i, np.full(dcells.size, n0)]), np.concatenate([i + 1, dcells]),
             np.concatenate([Gl, np.full(dcells.size, Gtop)]))
    C = np.zeros(n0 + nL)
    C[:n0] = g.vol * h3.CSAT
    C[:n0][g.solid.ravel()] = 0
    phiL = np.full(nL, h3.RH_ROOM)
    C[n0:] = A * dz * (h3.EPS * h3.CSAT + h3.RHO_B * h3.gab_slope(phiL))
    tr = Transport(g, extra_C=C[n0:], extra_links=links,
                   dirichlet=(scells, np.full(scells.size, Gs), h3.RH_SET), vel=vel)
    phi = np.zeros(n0 + nL)
    zf = Z.ravel()
    phi[:n0] = np.where(zf > 0.047, h3.RH_SET - 0.5 * (h3.RH_SET - h3.RH_ROOM),
                        h3.RH_SET - 0.1 * (h3.RH_SET - h3.RH_ROOM))
    phi[:n0][g.solid.ravel()] = 0
    phi[n0:] = phiL
    w0 = h3.RHO_B * A * dz * h3.gab(phiL).sum()
    mass_dry = h3.RHO_B * A * L
    ts, rsurf, rair, rsen, up = [0.0], [h3.RH_ROOM], [float(phi[dcells].mean())], [float(phi[sensor])], [0.0]
    t = 0.0
    nstep = 0
    while t < t_end:
        dt = 2.0 if t < 600 else min(60.0, 2.0 * 1.05 ** ((t - 600) / 2.0))
        rebuild = nstep % 20 == 0          # layer capacity updated every 20 steps (Picard lag)
        if rebuild:
            C[n0:] = A * dz * (h3.EPS * h3.CSAT + h3.RHO_B * h3.gab_slope(phi[n0:]))
            tr._cache.clear()
        phi = tr.step(phi, round(dt, 3), C=C, solver="lu", rebuild=rebuild)
        nstep += 1
        t += dt
        ts.append(t)
        rsurf.append(float(phi[n0]))
        rair.append(float(phi[dcells].mean()))
        rsen.append(float(phi[sensor]))
        up.append(float((h3.RHO_B * A * dz * h3.gab(phi[n0:]).sum() - w0) / mass_dry * 1e3))
    eq = float((h3.gab(h3.RH_SET) - h3.gab(h3.RH_ROOM)) * 1e3)
    res = dict(k_dish=kmd, equilibrium_uptake_mg_per_g=eq)
    for name, y in (("sample_surface", rsurf), ("sample_air", rair), ("sensor", rsen)):
        res[name] = {"t_95pct_of_setpoint_s": h3.t_cross(ts, y, 0.95 * h3.RH_SET),
                     "t_99pct_of_setpoint_s": h3.t_cross(ts, y, 0.99 * h3.RH_SET),
                     "min_RH": float(np.min(y))}
    res["uptake_t50_s"] = h3.t_cross(ts, up, 0.5 * eq)
    res["uptake_t95_s"] = h3.t_cross(ts, up, 0.95 * eq)
    res["max_sensor_minus_sample_RH"] = float(np.max(np.array(rsen) - np.array(rsurf)))
    k = slice(None, None, 5)
    res["series"] = dict(t=ts[k], sample_surface=rsurf[k], sensor=rsen[k], uptake=up[k])
    return res


def vapour_case_c(flow, enh=1.0, rh_box=0.843, rh_surf=0.753):
    g, vel, scells, Gs, dcells, kmd, sensor, Z, km = vapour_grid(flow, enh)
    A = 0.060 * F_DISH
    a_grid = dcells.size * H
    Gd = h3.CSAT * H * kmd * (A / a_grid)
    cells = np.concatenate([scells, dcells])
    G = np.concatenate([np.full(scells.size, Gs), np.full(dcells.size, Gd)])
    val = np.concatenate([np.full(scells.size, rh_box), np.full(dcells.size, rh_surf)])
    tr = Transport(g, dirichlet=(cells, G, val), vel=vel)
    phi = tr.steady()
    flux = float(np.sum(Gd * (phi[dcells] - rh_surf)))      # kg/s per m depth
    rate = flux * 0.120 * 1e6 * 3600                         # mg/h for the 120 mm deep box
    return dict(uptake_rate_mg_per_h=rate, sensor_RH=float(phi[sensor]),
                air_above_sample_RH=float(phi[dcells].mean()))


def main():
    mode = sys.argv[1]
    if mode == "flow":
        fan = sys.argv[2]
        nu = float(sys.argv[3]) if len(sys.argv) > 3 else 3e-4
        run_flow(fan, nu)
        return
    # vapour: still air (2D) and the fan cases
    out = {}
    flows = {}
    for fn in sys.argv[2:] or ["below_nu3e-04", "above_nu3e-04"]:
        flows[fn] = json.load(open(f"fanflow_{fn}.json"))
    t0 = time.time()
    out["still_2d"] = dict(case_a=vapour_case_a(None), case_c=vapour_case_c(None))
    print("still", out["still_2d"]["case_a"]["sample"], out["still_2d"]["case_c"], f"{time.time()-t0:.0f} s",
          flush=True)
    json.dump(out, open("humidity_fan2d.json", "w"), indent=1)
    for fn, fl in flows.items():
        for enh in ((1.0, 2.0) if fn.startswith("below") else (1.0,)):
            key = f"fan_{fn}_enh{enh:.0f}"
            out[key] = dict(flow={k: v for k, v in fl.items() if k != "hist"},
                            case_a=vapour_case_a(fl, enh), case_c=vapour_case_c(fl, enh))
            if fn.startswith("below"):
                out[key]["case_b"] = vapour_case_b(fl, enh)
            print(key, out[key]["case_a"]["sample"], out[key].get("case_b", {}).get("uptake_t50_s"),
                  out[key]["case_c"], f"{time.time()-t0:.0f} s", flush=True)
            json.dump(out, open("humidity_fan2d.json", "w"), indent=1)


if __name__ == "__main__":
    main()
