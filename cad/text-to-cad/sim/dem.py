"""Small soft-sphere DEM engine (numba) for the powder-doser auger (issue #172).

Model (SI units throughout):
* linear spring-dashpot normal force  F_n = k_n*delta - g_n*v_n  (no tension),
  g_n = 2*zeta*sqrt(m_eff*k_n), zeta set from the restitution coefficient e;
* Cundall-Strack tangential spring k_t = 2/7 k_n with damping and a Coulomb
  limit |F_t| <= mu*F_n (separate mu for particle-particle and particle-wall);
* elastic-plastic spring-dashpot rolling resistance (EPSD, Ai et al. 2011
  "type C"): rolling spring k_r = 2.25*k_n*mu_r^2*R*^2 on the relative rolling
  rotation, torque capped at mu_r*R**F_n, viscous damping (ratio eta_r) while
  below the cap;
* optional cohesion: constant pull-off force F_coh (Bond number F_coh/(m g))
  while in contact or within a small gap;
* semi-implicit Euler integration, cell-list neighbour search; every particle
  sums its own contacts (full neighbour list) so the force loop is a plain
  parallel loop with per-particle contact history (ping-pong buffers).

The auger is an analytic signed-distance description of the tube interior in
the non-rotating tube frame (z = tube axis, outlet face at z = 0, +y = "up"
when the tube is horizontal).  The tube rotates by theta(t) about +z; only the
helical flight depends on theta.  Walls move with v = Omega z x r for the
friction calculation.  Tilt enters as the gravity direction in the tube frame
and a solenoid tap as an extra pseudo-acceleration (see scenarios.py).
"""
from __future__ import annotations

import math

import numpy as np
from numba import njit, prange

MM = 1e-3
G = 9.81

# ---- auger geometry, body frame (from src/parts/auger.py) -------------------
R_BORE = 10.5 * MM            # bore radius
Z_FUN = 12.0 * MM             # funnel length (cone from r = 1.5 at z=0 to 10.5)
R_EXIT = 1.5 * MM             # funnel exit radius in the end face
R_CORE = 4.0 * MM             # core shaft radius (z = 12 .. 83.333)
R_TIP = 0.4 * MM              # core tip radius at z = 0
Z_CORE_TOP = 83.333 * MM
PITCH = 83.33 / 8 * MM        # right-handed flight, starts on +X at z = 0
T_FLIGHT = 0.5 * MM           # axial flight thickness

NW = 5          # wall primitives per particle (auger: bore, cone, core, flight, top cap)
MAXC = 16       # max particle-particle contacts stored per particle

# indices into the parameter vector
(P_KN, P_KT, P_MUPP, P_MUPW, P_MURPP, P_MURPW, P_ZETA, P_ZTOP, P_ZCAP, P_RCYL, P_RDISC,
 P_ETAR, P_FCOH, P_GAP) = range(14)
NPRM = 14


def zeta_from_e(e: float) -> float:
    """Damping ratio of the linear spring-dashpot giving restitution e."""
    le = math.log(e)
    return -le / math.sqrt(math.pi ** 2 + le ** 2)


@njit(inline="always", fastmath=True)
def wall_geom(k, x, y, z, theta, mode, prm):
    """Signed distance s of a point from wall primitive k (>0 in the free space)
    and the unit normal (nx, ny, nz) pointing from the wall into the free space."""
    BIG = 1.0
    r = math.sqrt(x * x + y * y) + 1e-12
    ex = x / r
    ey = y / r
    if mode == 0:
        if k == 0:                                   # bore cylinder r = R_BORE
            return R_BORE - r, -ex, -ey, 0.0
        elif k == 1:                                 # funnel cone (infinite line; with the
            dr = R_BORE - R_EXIT                     # cylinder it forms the exact concave corner)
            L = math.sqrt(dr * dr + Z_FUN * Z_FUN)
            s = (-(r - R_EXIT) * Z_FUN + z * dr) / L
            return s, -Z_FUN / L * ex, -Z_FUN / L * ey, dr / L
        elif k == 2:                                 # core: cone tip + cylinder, (r, z) polyline
            abr = R_CORE - R_TIP
            t = ((r - R_TIP) * abr + z * Z_FUN) / (abr * abr + Z_FUN * Z_FUN)
            t = min(max(t, 0.0), 1.0)
            qr = R_TIP + t * abr
            qz = t * Z_FUN
            d1 = math.sqrt((r - qr) ** 2 + (z - qz) ** 2)
            zc = min(max(z, Z_FUN), Z_CORE_TOP)
            d2 = math.sqrt((r - R_CORE) ** 2 + (z - zc) ** 2)
            if d2 < d1:
                qr = R_CORE
                qz = zc
                d1 = d2
            if z < Z_FUN:
                inside = r < R_TIP + abr * z / Z_FUN
            else:
                inside = (r < R_CORE) and (z < Z_CORE_TOP)
            if d1 < 1e-12:
                return 0.0, ex, ey, 0.0
            nr = (r - qr) / d1
            nz = (z - qz) / d1
            if inside:
                return -d1, -nr * ex, -nr * ey, -nz
            return d1, nr * ex, nr * ey, nz
        elif k == 3:                                 # helicoid flight sheet
            if z > Z_CORE_TOP:
                return BIG, 0.0, 0.0, 1.0
            phi = math.atan2(y, x) - theta           # body-frame angle
            dz = z - 0.5 * T_FLIGHT - PITCH * phi / (2.0 * math.pi)
            dz -= PITCH * math.floor(dz / PITCH + 0.5)
            q = PITCH / (2.0 * math.pi * r)
            c = 1.0 / math.sqrt(1.0 + q * q)
            sg = 1.0 if dz >= 0.0 else -1.0
            # grad(z - p*phi/2pi) = z_hat - q*phi_hat, phi_hat = (-ey, ex, 0)
            return (abs(dz) - 0.5 * T_FLIGHT) * c, sg * q * ey * c, -sg * q * ex * c, sg * c
        else:                                        # artificial top cap of the simulated section
            return prm[P_ZTOP] - z, 0.0, 0.0, -1.0
    else:                                            # angle-of-repose test
        if k == 0:                                   # rough base disc z = 0, r < P_RDISC
            if r < prm[P_RDISC]:
                return z, 0.0, 0.0, 1.0
            return BIG, 0.0, 0.0, 1.0
        elif k == 1 and prm[P_RCYL] > 0.0 and z > prm[P_ZCAP]:   # lifting cylinder
            return prm[P_RCYL] - r, -ex, -ey, 0.0      # (P_ZCAP = its lower edge here)
        return BIG, 0.0, 0.0, 1.0


@njit(fastmath=True)
def build_cells(pos, active, lo, h, nx, ny, nz, cstart, ccount, cfill, order, pcell):
    """Counting-sort cell list."""
    N = pos.shape[0]
    ccount[:] = 0
    for i in range(N):
        if active[i]:
            ix = min(max(int((pos[i, 0] - lo[0]) / h), 0), nx - 1)
            iy = min(max(int((pos[i, 1] - lo[1]) / h), 0), ny - 1)
            iz = min(max(int((pos[i, 2] - lo[2]) / h), 0), nz - 1)
            c = ix + nx * (iy + ny * iz)
            pcell[i] = c
            ccount[c] += 1
    s = 0
    for c in range(ccount.shape[0]):
        cstart[c] = s
        cfill[c] = s
        s += ccount[c]
    for i in range(N):
        if active[i]:
            c = pcell[i]
            order[cfill[c]] = i
            cfill[c] += 1


@njit(inline="always", fastmath=True)
def _contact(ri, nx_, ny_, nz_, delta, vrx, vry, vrz, wrx, wry, wrz, sx, sy, sz,
             mx, my, mz, kn, kt, zeta, mu, mur, Reff, meff, Ir, etar, fcoh, dt):
    """One contact (pair or wall).  n points into particle i; (vr) contact-point
    velocity of i relative to the partner; (wr) relative angular velocity;
    (s) tangential spring; (m) rolling-spring torque.  Returns force, torque and
    the updated springs."""
    vn = vrx * nx_ + vry * ny_ + vrz * nz_
    Frep = kn * delta - 2.0 * zeta * math.sqrt(meff * kn) * vn
    if Frep < 0.0:
        Frep = 0.0
    Fn = Frep - fcoh
    Fcap = Frep + fcoh                       # load that sets the friction limits
    vtx = vrx - vn * nx_
    vty = vry - vn * ny_
    vtz = vrz - vn * nz_
    sn = sx * nx_ + sy * ny_ + sz * nz_
    sx += -sn * nx_ + vtx * dt
    sy += -sn * ny_ + vty * dt
    sz += -sn * nz_ + vtz * dt
    gt = 2.0 * zeta * math.sqrt(meff * kt)
    ftx = -kt * sx - gt * vtx
    fty = -kt * sy - gt * vty
    ftz = -kt * sz - gt * vtz
    ft = math.sqrt(ftx * ftx + fty * fty + ftz * ftz)
    fmax = mu * Fcap
    if ft > fmax:
        sc = fmax / ft if ft > 0.0 else 0.0
        ftx *= sc
        fty *= sc
        ftz *= sc
        sx = -ftx / kt
        sy = -fty / kt
        sz = -ftz / kt
    fx = Fn * nx_ + ftx
    fy = Fn * ny_ + fty
    fz = Fn * nz_ + ftz
    # torque of F_t applied at -r_i n
    tx = -ri * (ny_ * ftz - nz_ * fty)
    ty = -ri * (nz_ * ftx - nx_ * ftz)
    tz = -ri * (nx_ * fty - ny_ * ftx)
    # EPSD rolling resistance on the tangential part of the relative rotation
    wn = wrx * nx_ + wry * ny_ + wrz * nz_
    wrx -= wn * nx_
    wry -= wn * ny_
    wrz -= wn * nz_
    mn = mx * nx_ + my * ny_ + mz * nz_
    mx -= mn * nx_
    my -= mn * ny_
    mz -= mn * nz_
    if mur > 0.0:
        kr = 2.25 * kn * mur * mur * Reff * Reff
        mx -= kr * wrx * dt
        my -= kr * wry * dt
        mz -= kr * wrz * dt
        mm = math.sqrt(mx * mx + my * my + mz * mz)
        mmax = mur * Reff * Fcap
        if mm > mmax:
            sc = mmax / mm
            mx *= sc
            my *= sc
            mz *= sc
            tx += mx
            ty += my
            tz += mz
        else:
            cr = 2.0 * etar * math.sqrt(Ir * kr)
            tx += mx - cr * wrx
            ty += my - cr * wry
            tz += mz - cr * wrz
    else:
        mx = 0.0
        my = 0.0
        mz = 0.0
    return fx, fy, fz, tx, ty, tz, sx, sy, sz, mx, my, mz


@njit(parallel=True, fastmath=True)
def compute_forces(pos, vel, angv, rad, mass, inert, active, fixed,
                   lo, h, dims, cstart, ccount, order, hr, hw, wxi, wmr,
                   prm, mode, theta, Omega, g3, dt, force, torque, ovl):
    N = pos.shape[0]
    hid, hxi, hmr = hr                  # contact history read buffers
    nid, nxi, nmr = hw                  # ... and write buffers
    nx, ny, nz = dims[0], dims[1], dims[2]
    gx, gy, gz = g3[0], g3[1], g3[2]
    kn = prm[P_KN]
    kt = prm[P_KT]
    zeta = prm[P_ZETA]
    etar = prm[P_ETAR]
    fcoh = prm[P_FCOH]
    gap = prm[P_GAP]
    for i in prange(N):
        if not active[i] or fixed[i]:
            continue
        xi_ = pos[i, 0]
        yi = pos[i, 1]
        zi = pos[i, 2]
        ri = rad[i]
        mi = mass[i]
        Ii = inert[i]
        fx = mi * gx
        fy = mi * gy
        fz = mi * gz
        tx = 0.0
        ty = 0.0
        tz = 0.0
        omax = 0.0
        nc = 0
        ix = min(max(int((xi_ - lo[0]) / h), 0), nx - 1)
        iy = min(max(int((yi - lo[1]) / h), 0), ny - 1)
        iz = min(max(int((zi - lo[2]) / h), 0), nz - 1)
        for cz in range(max(iz - 1, 0), min(iz + 2, nz)):
            for cy in range(max(iy - 1, 0), min(iy + 2, ny)):
                for cx in range(max(ix - 1, 0), min(ix + 2, nx)):
                    c = cx + nx * (cy + ny * cz)
                    for a in range(cstart[c], cstart[c] + ccount[c]):
                        j = order[a]
                        if j == i:
                            continue
                        dx = xi_ - pos[j, 0]
                        dy = yi - pos[j, 1]
                        dz = zi - pos[j, 2]
                        rj = rad[j]
                        rs = ri + rj
                        d2 = dx * dx + dy * dy + dz * dz
                        if d2 >= (rs + gap) * (rs + gap):
                            continue
                        d = math.sqrt(d2)
                        nxv = dx / d
                        nyv = dy / d
                        nzv = dz / d
                        delta = rs - d
                        if delta <= 0.0:             # cohesive gap only: pull-off force
                            fx -= fcoh * nxv
                            fy -= fcoh * nyv
                            fz -= fcoh * nzv
                            continue
                        if delta / (2.0 * ri) > omax:
                            omax = delta / (2.0 * ri)
                        mj = mass[j]
                        vrx = (vel[i, 0] - vel[j, 0]) - ri * (angv[i, 1] * nzv - angv[i, 2] * nyv) \
                            - rj * (angv[j, 1] * nzv - angv[j, 2] * nyv)
                        vry = (vel[i, 1] - vel[j, 1]) - ri * (angv[i, 2] * nxv - angv[i, 0] * nzv) \
                            - rj * (angv[j, 2] * nxv - angv[j, 0] * nzv)
                        vrz = (vel[i, 2] - vel[j, 2]) - ri * (angv[i, 0] * nyv - angv[i, 1] * nxv) \
                            - rj * (angv[j, 0] * nyv - angv[j, 1] * nxv)
                        sx = 0.0
                        sy = 0.0
                        sz = 0.0
                        mx = 0.0
                        my = 0.0
                        mz = 0.0
                        for b in range(MAXC):
                            if hid[i, b] == j:
                                sx = hxi[i, b, 0]
                                sy = hxi[i, b, 1]
                                sz = hxi[i, b, 2]
                                mx = hmr[i, b, 0]
                                my = hmr[i, b, 1]
                                mz = hmr[i, b, 2]
                                break
                            if hid[i, b] < 0:
                                break
                        Ij = inert[j]
                        Ir = 1.0 / (1.0 / (Ii + mi * ri * ri) + 1.0 / (Ij + mj * rj * rj))
                        cf = _contact(ri, nxv, nyv, nzv, delta, vrx, vry, vrz,
                                      angv[i, 0] - angv[j, 0], angv[i, 1] - angv[j, 1],
                                      angv[i, 2] - angv[j, 2], sx, sy, sz, mx, my, mz,
                                      kn, kt, zeta, prm[P_MUPP], prm[P_MURPP], ri * rj / rs,
                                      mi * mj / (mi + mj), Ir, etar, fcoh, dt)
                        fx += cf[0]
                        fy += cf[1]
                        fz += cf[2]
                        tx += cf[3]
                        ty += cf[4]
                        tz += cf[5]
                        if nc < MAXC:
                            nid[i, nc] = j
                            nxi[i, nc, 0] = cf[6]
                            nxi[i, nc, 1] = cf[7]
                            nxi[i, nc, 2] = cf[8]
                            nmr[i, nc, 0] = cf[9]
                            nmr[i, nc, 1] = cf[10]
                            nmr[i, nc, 2] = cf[11]
                            nc += 1
        for b in range(nc, MAXC):
            nid[i, b] = -1
        # ---- walls ----
        for k in range(NW):
            s, wnx, wny, wnz = wall_geom(k, xi_, yi, zi, theta, mode, prm)
            delta = ri - s
            if delta <= 0.0:
                for c3 in range(3):
                    wxi[i, k, c3] = 0.0
                    wmr[i, k, c3] = 0.0
                if delta > -gap and not (mode == 0 and k == 4):   # cohesion to the wall
                    fx -= fcoh * wnx
                    fy -= fcoh * wny
                    fz -= fcoh * wnz
                continue
            if delta / (2.0 * ri) > omax:
                omax = delta / (2.0 * ri)
            rcx = -ri * wnx
            rcy = -ri * wny
            rcz = -ri * wnz
            if mode == 0:                            # wall point velocity Omega z x r
                vwx = -Omega * (yi + rcy)
                vwy = Omega * (xi_ + rcx)
                wwz = Omega
                mu = prm[P_MUPW] if k != 4 else 0.0  # top lid is frictionless, not cohesive
                mur = prm[P_MURPW] if k != 4 else 0.0
                fc = fcoh if k != 4 else 0.0
            else:
                vwx = 0.0
                vwy = 0.0
                wwz = 0.0
                mu = prm[P_MUPW] if k == 0 else 0.0  # base disc uses the wall values,
                mur = prm[P_MURPW] if k == 0 else 0.0  # the lifted cylinder is frictionless
                fc = fcoh if k == 0 else 0.0
            vrx = vel[i, 0] + (angv[i, 1] * rcz - angv[i, 2] * rcy) - vwx
            vry = vel[i, 1] + (angv[i, 2] * rcx - angv[i, 0] * rcz) - vwy
            vrz = vel[i, 2] + (angv[i, 0] * rcy - angv[i, 1] * rcx)
            cf = _contact(ri, wnx, wny, wnz, delta, vrx, vry, vrz,
                          angv[i, 0], angv[i, 1], angv[i, 2] - wwz,
                          wxi[i, k, 0], wxi[i, k, 1], wxi[i, k, 2],
                          wmr[i, k, 0], wmr[i, k, 1], wmr[i, k, 2],
                          kn, kt, zeta, mu, mur, ri, mi, Ii + mi * ri * ri,
                          etar, fc, dt)
            fx += cf[0]
            fy += cf[1]
            fz += cf[2]
            tx += cf[3]
            ty += cf[4]
            tz += cf[5]
            wxi[i, k, 0] = cf[6]
            wxi[i, k, 1] = cf[7]
            wxi[i, k, 2] = cf[8]
            wmr[i, k, 0] = cf[9]
            wmr[i, k, 1] = cf[10]
            wmr[i, k, 2] = cf[11]
        force[i, 0] = fx
        force[i, 1] = fy
        force[i, 2] = fz
        torque[i, 0] = tx
        torque[i, 1] = ty
        torque[i, 2] = tz
        ovl[i] = omax


@njit(fastmath=True)
def run_block(nsteps, dt, pos, vel, angv, rad, mass, inert, active, fixed,
              lo, h, nx, ny, nz, cstart, ccount, cfill, order, pcell,
              hid_a, hxi_a, hmr_a, hid_b, hxi_b, hmr_b, wxi, wmr, prm, mode,
              theta0, Omega, gvec, force, torque, ovl, captured, cap_t, t0):
    """Advance nsteps (even) with per-step tube speed Omega[s] and gravity
    (incl. tap pseudo-acceleration) gvec[s].  Particles whose centre crosses
    the capture plane z < z_cap are removed (dispensed); returns the new tube
    angle, dispensed mass, number lost (left the domain) and the max overlap."""
    N = pos.shape[0]
    theta = theta0
    dims = np.array([nx, ny, nz])
    ha = (hid_a, hxi_a, hmr_a)
    hb = (hid_b, hxi_b, hmr_b)
    mdisp = 0.0
    nlost = 0
    omax = 0.0
    for s in range(nsteps):
        build_cells(pos, active, lo, h, nx, ny, nz, cstart, ccount, cfill, order, pcell)
        if s % 2 == 0:
            compute_forces(pos, vel, angv, rad, mass, inert, active, fixed, lo, h, dims,
                           cstart, ccount, order, ha, hb, wxi, wmr, prm, mode, theta, Omega[s],
                           gvec[s], dt, force, torque, ovl)
        else:
            compute_forces(pos, vel, angv, rad, mass, inert, active, fixed, lo, h, dims,
                           cstart, ccount, order, hb, ha, wxi, wmr, prm, mode, theta, Omega[s],
                           gvec[s], dt, force, torque, ovl)
        for i in range(N):
            if not active[i] or fixed[i]:
                continue
            if ovl[i] > omax:
                omax = ovl[i]
            im = 1.0 / mass[i]
            ii = 1.0 / inert[i]
            for c in range(3):
                vel[i, c] += force[i, c] * im * dt
                pos[i, c] += vel[i, c] * dt
                angv[i, c] += torque[i, c] * ii * dt
            if mode == 0:
                if pos[i, 2] < prm[P_ZCAP]:
                    active[i] = False
                    mdisp += mass[i]
                    captured[i] = True
                    cap_t[i] = t0 + (s + 1) * dt
                elif (pos[i, 0] ** 2 + pos[i, 1] ** 2 > (R_BORE + 2 * rad[i]) ** 2
                      or pos[i, 2] > prm[P_ZTOP] + 2 * rad[i]) or not (abs(pos[i, 2]) < 1.0):
                    active[i] = False
                    nlost += 1
            else:
                if pos[i, 2] < -2 * rad[i] or not (abs(pos[i, 0]) < 1.0):
                    active[i] = False
                    nlost += 1
        theta += Omega[s] * dt
    return theta, mdisp, nlost, omax


class DEM:
    """State container + driver.  Geometry mode 0 = auger section, 1 = repose test."""

    def __init__(self, pos, rad, rho, mode, prm, dt, lo, hi, fixed=None):
        self.N = len(rad)
        self.pos = np.ascontiguousarray(pos, dtype=np.float64)
        self.vel = np.zeros_like(self.pos)
        self.angv = np.zeros_like(self.pos)
        self.rad = np.asarray(rad, dtype=np.float64)
        self.mass = rho * 4.0 / 3.0 * np.pi * self.rad ** 3
        self.inert = 0.4 * self.mass * self.rad ** 2
        self.active = np.ones(self.N, dtype=np.bool_)
        self.fixed = np.zeros(self.N, dtype=np.bool_) if fixed is None else np.asarray(fixed, np.bool_)
        self.captured = np.zeros(self.N, dtype=np.bool_)
        self.cap_t = np.full(self.N, np.nan)
        self.mode = mode
        self.prm = np.asarray(prm, dtype=np.float64)
        self.dt = dt
        self.h = (2.0 * self.rad.max() + self.prm[P_GAP]) * 1.001
        self.lo = np.asarray(lo, dtype=np.float64)
        n = np.ceil((np.asarray(hi) - self.lo) / self.h).astype(int) + 1
        self.nx, self.ny, self.nz = int(n[0]), int(n[1]), int(n[2])
        nc = self.nx * self.ny * self.nz
        self.cstart = np.zeros(nc, np.int64)
        self.ccount = np.zeros(nc, np.int64)
        self.cfill = np.zeros(nc, np.int64)
        self.order = np.zeros(self.N, np.int64)
        self.pcell = np.zeros(self.N, np.int64)
        self.hid_a = -np.ones((self.N, MAXC), np.int64)
        self.hid_b = -np.ones((self.N, MAXC), np.int64)
        self.hxi_a = np.zeros((self.N, MAXC, 3))
        self.hxi_b = np.zeros((self.N, MAXC, 3))
        self.hmr_a = np.zeros((self.N, MAXC, 3))
        self.hmr_b = np.zeros((self.N, MAXC, 3))
        self.wxi = np.zeros((self.N, NW, 3))
        self.wmr = np.zeros((self.N, NW, 3))
        self.force = np.zeros((self.N, 3))
        self.torque = np.zeros((self.N, 3))
        self.ovl = np.zeros(self.N)
        self.t = 0.0
        self.theta = 0.0
        self.m_disp = 0.0
        self.n_lost = 0

    def advance(self, nsteps, Omega, gvec):
        theta, md, nl, om = run_block(
            nsteps, self.dt, self.pos, self.vel, self.angv, self.rad, self.mass, self.inert,
            self.active, self.fixed, self.lo, self.h, self.nx, self.ny, self.nz, self.cstart,
            self.ccount, self.cfill, self.order, self.pcell, self.hid_a, self.hxi_a, self.hmr_a,
            self.hid_b, self.hxi_b, self.hmr_b, self.wxi, self.wmr, self.prm, self.mode,
            self.theta, Omega, gvec, self.force, self.torque, self.ovl, self.captured,
            self.cap_t, self.t)
        self.theta = theta
        self.m_disp += md
        self.n_lost += nl
        self.t += nsteps * self.dt
        return om

    def kinetic_energy(self):
        a = self.active & ~self.fixed
        return float(0.5 * np.sum(self.mass[a] * np.sum(self.vel[a] ** 2, axis=1)))

    def save(self, fn):
        np.savez_compressed(fn, pos=self.pos, vel=self.vel, angv=self.angv, rad=self.rad,
                            active=self.active, hid=self.hid_a, hxi=self.hxi_a, hmr=self.hmr_a,
                            wxi=self.wxi, wmr=self.wmr, t=self.t, theta=self.theta)

    def load(self, fn):
        d = np.load(fn)
        self.pos[:] = d["pos"]
        self.vel[:] = d["vel"]
        self.angv[:] = d["angv"]
        self.active[:] = d["active"]
        self.hid_a[:] = d["hid"]
        self.hxi_a[:] = d["hxi"]
        self.hmr_a[:] = d["hmr"]
        self.wxi[:] = d["wxi"]
        self.wmr[:] = d["wmr"]
        self.theta = float(d["theta"])


def flight_chamber(pos, theta):
    """Index of the helical channel (flight turn) a tube-frame point sits in."""
    phi = np.arctan2(pos[:, 1], pos[:, 0]) - theta
    u = (pos[:, 2] - 0.5 * T_FLIGHT - PITCH * phi / (2 * np.pi)) / PITCH
    return np.floor(u).astype(int)


def free_space_ok(pts, rad, prm, theta=0.0, mode=0, margin=0.0):
    """True where a sphere of radius rad (+margin) at pts clears all walls."""
    ok = np.ones(len(pts), dtype=bool)
    for i, p in enumerate(pts):
        for k in range(NW):
            s = wall_geom(k, p[0], p[1], p[2], theta, mode, prm)[0]
            if s < rad[i] + margin:
                ok[i] = False
                break
    return ok
