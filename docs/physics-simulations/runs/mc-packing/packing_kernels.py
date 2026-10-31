"""Numba kernels for geometric / Monte Carlo sphere packing (3D).

All lengths are dimensionless (units of a reference diameter d_ref).
Lateral directions x, y are periodic with box side L.  Deposition has a
flat floor at z = 0; RSA and compression are fully periodic cubes.

Algorithms
----------
rsa_run          random sequential addition, sizes drawn per attempt
deposit          sequential gravitational deposition: vertical drop, roll on
                 one sphere, roll in the groove of two, stop on a stable
                 3-contact (or floor / 2-contact groove-bottom) position
                 (Visscher-Bolsterli 1972; Jullien-Meakin 1987).  With
                 probability p_stick a particle stops at each new contact
                 (p_stick = 1 is ballistic deposition, the cohesive limit).
compress         force-biased overlap-removal compression (Jodrey-Tory /
                 Moscinski-Bargiel type): grow all radii in steps, push
                 overlapping pairs apart, stop when overlaps can no longer
                 be removed (jamming) -> random-close-packing analog.
"""
import math
import numpy as np
import numba as nb


@nb.njit(cache=True)
def mi(dx, L):
    return dx - L * math.floor(dx / L + 0.5)


@nb.njit(cache=True)
def draw_radius(kind, p1, p2, p3, p4):
    # kind 0: mono radius p1; 1: diameter uniform in [p1,p2]; 2: truncated
    # log-normal diameter, number-weighted median p1, sigma p2, range [p3,p4]
    if kind == 0:
        return p1
    elif kind == 1:
        return 0.5 * (p1 + (p2 - p1) * np.random.random())
    else:
        while True:
            d = p1 * math.exp(p2 * np.random.standard_normal())
            if d >= p3 and d <= p4:
                return 0.5 * d


# ---------------------------------------------------------------- RSA
@nb.njit(cache=True)
def rsa_run(kind, p1, p2, p3, p4, rmax, L, n_att, checkpoints, seed, cap):
    np.random.seed(seed)
    ncx = int(L // (2.0 * rmax))
    cs = L / ncx
    count = np.zeros((ncx, ncx, ncx), np.int32)
    items = np.empty((ncx, ncx, ncx, cap), np.int32)
    nmax = 400000
    pos = np.empty((nmax, 3))
    rad = np.empty(nmax)
    n = 0
    vol = 0.0
    hist = np.empty(checkpoints.size)
    ck = 0
    overflow = 0
    for a in range(n_att):
        r = draw_radius(kind, p1, p2, p3, p4)
        x = np.random.random() * L
        y = np.random.random() * L
        z = np.random.random() * L
        ix = int(x / cs) % ncx
        iy = int(y / cs) % ncx
        iz = int(z / cs) % ncx
        ok = True
        for ddx in range(-1, 2):
            if not ok:
                break
            cx = (ix + ddx) % ncx
            for ddy in range(-1, 2):
                if not ok:
                    break
                cy = (iy + ddy) % ncx
                for ddz in range(-1, 2):
                    cz = (iz + ddz) % ncx
                    for q in range(count[cx, cy, cz]):
                        m = items[cx, cy, cz, q]
                        dx = mi(pos[m, 0] - x, L)
                        dy = mi(pos[m, 1] - y, L)
                        dz = mi(pos[m, 2] - z, L)
                        R = r + rad[m]
                        if dx * dx + dy * dy + dz * dz < R * R:
                            ok = False
                            break
                    if not ok:
                        break
        if ok and n < nmax:
            c = count[ix, iy, iz]
            if c < cap:
                pos[n, 0] = x
                pos[n, 1] = y
                pos[n, 2] = z
                rad[n] = r
                items[ix, iy, iz, c] = n
                count[ix, iy, iz] = c + 1
                n += 1
                vol += 4.0 / 3.0 * math.pi * r ** 3
            else:
                overflow += 1
        while ck < checkpoints.size and a + 1 >= checkpoints[ck]:
            hist[ck] = vol / L ** 3
            ck += 1
    return pos[:n].copy(), rad[:n].copy(), hist, overflow


# --------------------------------------------------------- deposition
@nb.njit(cache=True)
def _gather(cjx, cjy, cjz, rng, L, cs, ncx, nz, count, items, pos, out):
    # all placed particles whose centre is within rng of (cjx,cjy,cjz)
    nr = int(math.ceil(rng / cs))
    ix = int(math.floor(cjx / cs)) % ncx
    iy = int(math.floor(cjy / cs)) % ncx
    iz = int(math.floor(cjz / cs))
    nc = 0
    if 2 * nr + 1 >= ncx:
        xs = np.arange(ncx)
    else:
        xs = np.empty(2 * nr + 1, np.int64)
        for t in range(2 * nr + 1):
            xs[t] = (ix - nr + t) % ncx
    if 2 * nr + 1 >= ncx:
        ys = np.arange(ncx)
    else:
        ys = np.empty(2 * nr + 1, np.int64)
        for t in range(2 * nr + 1):
            ys[t] = (iy - nr + t) % ncx
    for cz in range(max(iz - nr, 0), min(iz + nr, nz - 1) + 1):
        for cx in xs:
            for cy in ys:
                for q in range(count[cx, cy, cz]):
                    m = items[cx, cy, cz, q]
                    dx = mi(pos[m, 0] - cjx, L)
                    dy = mi(pos[m, 1] - cjy, L)
                    dz = pos[m, 2] - cjz
                    if dx * dx + dy * dy + dz * dz < rng * rng:
                        if nc < out.size:
                            out[nc] = m
                            nc += 1
    return nc


@nb.njit(cache=True)
def deposit(rad, L, p_stick, seed, cap, max_trans):
    np.random.seed(seed)
    N = rad.size
    rmax = rad.max()
    ncx = int(L // (2.0 * rmax))
    cs = L / ncx
    vol = 0.0
    for i in range(N):
        vol += 4.0 / 3.0 * math.pi * rad[i] ** 3
    Hest = vol / (0.08 * L * L) + 20.0 * rmax
    nz = int(Hest / cs) + 4
    count = np.zeros((ncx, ncx, nz), np.int32)
    items = np.empty((ncx, ncx, nz, cap), np.int32)
    pos = np.zeros((N, 3))
    ncon = np.zeros(N, np.int32)
    cand = np.empty(20000, np.int64)
    stuck = 0
    overflow = 0
    ztop = 0.0
    tiny = 1e-10
    for i in range(N):
        r = rad[i]
        px = np.random.random() * L
        py = np.random.random() * L
        pz = ztop + r + 1e-6
        state = 0
        j = -1
        k = -1
        l = -1
        ex1 = -1
        ex2 = -1
        ex3 = -1
        ntr = 0
        nc_final = 0
        while True:
            ntr += 1
            if ntr > max_trans:
                stuck += 1
                nc_final = -1
                break
            if state == 0:
                # ---- vertical free fall
                best = r
                bj = -1
                ix = int(math.floor(px / cs)) % ncx
                iy = int(math.floor(py / cs)) % ncx
                izmax = min(int(pz / cs) + 1, nz - 1)
                for iz in range(izmax, -1, -1):
                    if (iz + 1) * cs + r + rmax < best:
                        break
                    for ddx in range(-1, 2):
                        cx = (ix + ddx) % ncx
                        for ddy in range(-1, 2):
                            cy = (iy + ddy) % ncx
                            for q in range(count[cx, cy, iz]):
                                m = items[cx, cy, iz, q]
                                if m == ex1 or m == ex2 or m == ex3:
                                    continue
                                dx = mi(pos[m, 0] - px, L)
                                dy = mi(pos[m, 1] - py, L)
                                R = r + rad[m]
                                d2 = dx * dx + dy * dy
                                if d2 < R * R:
                                    zc = pos[m, 2] + math.sqrt(R * R - d2)
                                    if zc <= pz + 1e-9 and zc > best:
                                        best = zc
                                        bj = m
                pz = best
                ex1 = -1
                ex2 = -1
                ex3 = -1
                if bj < 0:
                    nc_final = 1  # floor
                    break
                if np.random.random() < p_stick:
                    nc_final = 1
                    break
                j = bj
                state = 1
            elif state == 1:
                # ---- roll on sphere j (steepest descent on its surface)
                cjx = px + mi(pos[j, 0] - px, L)
                cjy = py + mi(pos[j, 1] - py, L)
                cjz = pos[j, 2]
                Rj = r + rad[j]
                hx = px - cjx
                hy = py - cjy
                hn = math.sqrt(hx * hx + hy * hy)
                if hn < 1e-12:
                    ang = 2.0 * math.pi * np.random.random()
                    hx = math.cos(ang)
                    hy = math.sin(ang)
                else:
                    hx /= hn
                    hy /= hn
                c0 = (pz - cjz) / Rj
                if c0 > 1.0:
                    c0 = 1.0
                if c0 <= 0.0:
                    # at/below equator: cannot be carried by j alone
                    state = 0
                    ex1 = j
                    ex2 = -1
                    continue
                th0 = math.acos(c0)
                th_ev = 0.5 * math.pi
                ev = 0  # 0 equator, 1 floor, 2 contact
                kk = -1
                cf = (r - cjz) / Rj
                if cf >= 0.0 and cf < c0:
                    thf = math.acos(cf)
                    if thf < th_ev:
                        th_ev = thf
                        ev = 1
                nc = _gather(cjx, cjy, cjz, Rj + r + rmax, L, cs, ncx, nz,
                             count, items, pos, cand)
                for t in range(nc):
                    m = cand[t]
                    if m == j:
                        continue
                    wx = -mi(pos[m, 0] - cjx, L)
                    wy = -mi(pos[m, 1] - cjy, L)
                    wz = cjz - pos[m, 2]
                    Rm = r + rad[m]
                    A = 2.0 * Rj * (wx * hx + wy * hy)
                    B = 2.0 * Rj * wz
                    C = Rm * Rm - (wx * wx + wy * wy + wz * wz) - Rj * Rj
                    Rr = math.sqrt(A * A + B * B)
                    if Rr < 1e-14 or abs(C) > Rr:
                        continue
                    al = math.atan2(B, A)
                    s = math.asin(C / Rr)
                    for root in (s - al, math.pi - s - al):
                        th = root % (2.0 * math.pi)
                        if th > th0 + tiny and th < th_ev:
                            # entering: d/dth (A sin + B cos) < 0
                            if A * math.cos(th) - B * math.sin(th) < 0.0:
                                th_ev = th
                                ev = 2
                                kk = m
                px = cjx + Rj * math.sin(th_ev) * hx
                py = cjy + Rj * math.sin(th_ev) * hy
                pz = cjz + Rj * math.cos(th_ev)
                if ev == 0:
                    state = 0
                    ex1 = j
                    ex2 = -1
                elif ev == 1:
                    pz = r
                    nc_final = 2
                    break
                else:
                    if np.random.random() < p_stick:
                        nc_final = 2
                        break
                    k = kk
                    state = 2
            elif state == 2:
                # ---- roll in the groove of spheres j and k
                cjx = px + mi(pos[j, 0] - px, L)
                cjy = py + mi(pos[j, 1] - py, L)
                cjz = pos[j, 2]
                ckx = px + mi(pos[k, 0] - px, L)
                cky = py + mi(pos[k, 1] - py, L)
                ckz = pos[k, 2]
                Rj = r + rad[j]
                Rk = r + rad[k]
                njx = (px - cjx) / Rj
                njy = (py - cjy) / Rj
                njz = (pz - cjz) / Rj
                nkx = (px - ckx) / Rk
                nky = (py - cky) / Rk
                nkz = (pz - ckz) / Rk
                cc = njx * nkx + njy * nky + njz * nkz
                fj = njz - cc * nkz
                fk = nkz - cc * njz
                if fj < 0.0 and fk < 0.0:
                    state = 0
                    ex1 = j
                    ex2 = k
                    continue
                if fj < 0.0:
                    j = k
                    state = 1
                    continue
                if fk < 0.0:
                    state = 1
                    continue
                ux = ckx - cjx
                uy = cky - cjy
                uz = ckz - cjz
                sdist = math.sqrt(ux * ux + uy * uy + uz * uz)
                ux /= sdist
                uy /= sdist
                uz /= sdist
                a = (sdist * sdist + Rj * Rj - Rk * Rk) / (2.0 * sdist)
                rho2 = Rj * Rj - a * a
                rho = math.sqrt(rho2) if rho2 > 0.0 else 0.0
                mx = cjx + a * ux
                my = cjy + a * uy
                mz = cjz + a * uz
                en = math.sqrt(max(1.0 - uz * uz, 0.0))
                if en < 1e-9 or rho < 1e-12:
                    nc_final = 2
                    break
                e1x = uz * ux / en
                e1y = uz * uy / en
                e1z = (uz * uz - 1.0) / en
                e2x = uy * e1z - uz * e1y
                e2y = uz * e1x - ux * e1z
                e2z = ux * e1y - uy * e1x
                qx = px - mx
                qy = py - my
                qz = pz - mz
                psi0 = math.atan2(qx * e2x + qy * e2y + qz * e2z,
                                  qx * e1x + qy * e1y + qz * e1z)
                sg = 1.0 if psi0 >= 0.0 else -1.0
                tb = abs(psi0)
                t_ev = tb
                ev = 0  # 0 bottom (stable 2-contact), 1 floor, 2 detach j, 3 detach k, 4 contact
                ll = -1
                zcur = pz
                zbot = mz + rho * e1z
                # detachment heights (f linear in z along the path)
                for which in range(2):
                    if which == 0:
                        den = 1.0 / Rj - cc / Rk
                        num = cjz / Rj - cc * ckz / Rk
                    else:
                        den = 1.0 / Rk - cc / Rj
                        num = ckz / Rk - cc * cjz / Rj
                    if abs(den) < 1e-14:
                        continue
                    zs = num / den
                    if zs < zcur - 1e-12 and zs > zbot:
                        cps = (zs - mz) / (rho * e1z)
                        if cps > 1.0:
                            cps = 1.0
                        if cps < -1.0:
                            cps = -1.0
                        tt = tb - math.acos(cps)
                        if tt > tiny and tt < t_ev:
                            t_ev = tt
                            ev = 2 + which
                if r < zcur and r > zbot:
                    cps = (r - mz) / (rho * e1z)
                    if cps > 1.0:
                        cps = 1.0
                    if cps < -1.0:
                        cps = -1.0
                    tt = tb - math.acos(cps)
                    if tt > tiny and tt < t_ev:
                        t_ev = tt
                        ev = 1
                nc = _gather(cjx, cjy, cjz, Rj + r + rmax, L, cs, ncx, nz,
                             count, items, pos, cand)
                for t in range(nc):
                    m = cand[t]
                    if m == j or m == k:
                        continue
                    wx = mx - (cjx + mi(pos[m, 0] - cjx, L))
                    wy = my - (cjy + mi(pos[m, 1] - cjy, L))
                    wz = mz - pos[m, 2]
                    Rm = r + rad[m]
                    P = 2.0 * rho * (wx * e1x + wy * e1y + wz * e1z)
                    Q = 2.0 * rho * (wx * e2x + wy * e2y + wz * e2z)
                    C = Rm * Rm - (wx * wx + wy * wy + wz * wz) - rho * rho
                    Rr = math.sqrt(P * P + Q * Q)
                    if Rr < 1e-14 or abs(C) > Rr:
                        continue
                    be = math.atan2(Q, P)
                    acs = math.acos(C / Rr)
                    for psr in (be + acs, be - acs):
                        tt = (sg * (psi0 - psr)) % (2.0 * math.pi)
                        if tt > tiny and tt < t_ev:
                            ps = psi0 - sg * tt
                            dd = -sg * (-P * math.sin(ps) + Q * math.cos(ps))
                            if dd < 0.0:
                                t_ev = tt
                                ev = 4
                                ll = m
                ps = psi0 - sg * t_ev
                cps = math.cos(ps)
                sps = math.sin(ps)
                px = mx + rho * (cps * e1x + sps * e2x)
                py = my + rho * (cps * e1y + sps * e2y)
                pz = mz + rho * (cps * e1z + sps * e2z)
                if ev == 0:
                    nc_final = 2
                    break
                elif ev == 1:
                    pz = r
                    nc_final = 3
                    break
                elif ev == 2:
                    j = k
                    state = 1
                elif ev == 3:
                    state = 1
                else:
                    if np.random.random() < p_stick:
                        nc_final = 3
                        break
                    l = ll
                    state = 3
            else:
                # ---- three contacts: stable if all normal forces >= 0,
                # otherwise pick the active set (pair, single or none) whose
                # forces are >= 0 and whose motion does not enter the others
                Nm = np.empty((3, 3))
                ids = (j, k, l)
                for c in range(3):
                    m = ids[c]
                    cx_ = px + mi(pos[m, 0] - px, L)
                    cy_ = py + mi(pos[m, 1] - py, L)
                    Rm = r + rad[m]
                    Nm[c, 0] = (px - cx_) / Rm
                    Nm[c, 1] = (py - cy_) / Rm
                    Nm[c, 2] = (pz - pos[m, 2]) / Rm
                det = np.linalg.det(Nm)
                if abs(det) < 1e-12:
                    nc_final = 3
                    break
                f = np.linalg.solve(Nm.T.copy(), np.array([0.0, 0.0, 1.0]))
                if f[0] >= -1e-12 and f[1] >= -1e-12 and f[2] >= -1e-12:
                    nc_final = 3
                    break
                found = 0
                for pr in range(3):
                    if pr == 0:
                        ia, ib, ic = 0, 1, 2
                    elif pr == 1:
                        ia, ib, ic = 0, 2, 1
                    else:
                        ia, ib, ic = 1, 2, 0
                    cc = Nm[ia, 0] * Nm[ib, 0] + Nm[ia, 1] * Nm[ib, 1] + Nm[ia, 2] * Nm[ib, 2]
                    fa = Nm[ia, 2] - cc * Nm[ib, 2]
                    fb = Nm[ib, 2] - cc * Nm[ia, 2]
                    if fa < 0.0 or fb < 0.0:
                        continue
                    tx = Nm[ia, 1] * Nm[ib, 2] - Nm[ia, 2] * Nm[ib, 1]
                    ty = Nm[ia, 2] * Nm[ib, 0] - Nm[ia, 0] * Nm[ib, 2]
                    tz = Nm[ia, 0] * Nm[ib, 1] - Nm[ia, 1] * Nm[ib, 0]
                    tn = math.sqrt(tx * tx + ty * ty + tz * tz)
                    if tn < 1e-12:
                        continue
                    tx /= tn
                    ty /= tn
                    tz /= tn
                    if abs(tz) < 1e-12:
                        found = 3
                        break
                    vx = -tz * tx
                    vy = -tz * ty
                    vz = -tz * tz
                    if vx * Nm[ic, 0] + vy * Nm[ic, 1] + vz * Nm[ic, 2] >= -1e-12:
                        j = ids[ia]
                        k = ids[ib]
                        found = 2
                        break
                if found == 0:
                    for ia in range(3):
                        if Nm[ia, 2] < 0.0:
                            continue
                        vx = Nm[ia, 2] * Nm[ia, 0]
                        vy = Nm[ia, 2] * Nm[ia, 1]
                        vz = -1.0 + Nm[ia, 2] * Nm[ia, 2]
                        okk = True
                        for ib in range(3):
                            if ib != ia:
                                if vx * Nm[ib, 0] + vy * Nm[ib, 1] + vz * Nm[ib, 2] < -1e-12:
                                    okk = False
                        if okk:
                            j = ids[ia]
                            found = 1
                            break
                if found == 0:
                    if Nm[0, 2] <= 1e-12 and Nm[1, 2] <= 1e-12 and Nm[2, 2] <= 1e-12:
                        ex1 = j
                        ex2 = k
                        ex3 = l
                        state = 0
                    else:
                        stuck += 1
                        nc_final = -1
                        break
                elif found == 3:
                    nc_final = 2
                    break
                else:
                    state = found
        px = px % L
        py = py % L
        pos[i, 0] = px
        pos[i, 1] = py
        pos[i, 2] = pz
        ncon[i] = nc_final
        ix = int(px / cs) % ncx
        iy = int(py / cs) % ncx
        iz = int(pz / cs)
        if iz >= nz:
            iz = nz - 1
            overflow += 1
        c = count[ix, iy, iz]
        if c < cap:
            items[ix, iy, iz, c] = i
            count[ix, iy, iz] = c + 1
        else:
            overflow += 1
        if pz + r > ztop:
            ztop = pz + r
    return pos, ncon, stuck, overflow


# -------------------------------------------------- overlap diagnostics
@nb.njit(cache=True)
def max_overlap(pos, rad, L, periodic_z):
    N = rad.size
    worst = 0.0
    for i in range(N):
        for j in range(i + 1, N):
            dx = mi(pos[j, 0] - pos[i, 0], L)
            dy = mi(pos[j, 1] - pos[i, 1], L)
            dz = pos[j, 2] - pos[i, 2]
            if periodic_z:
                dz = mi(dz, L)
            R = rad[i] + rad[j]
            d2 = dx * dx + dy * dy + dz * dz
            if d2 < R * R:
                ov = (R - math.sqrt(d2)) / R
                if ov > worst:
                    worst = ov
    return worst


@nb.njit(cache=True)
def slab_fraction(pos, rad, L, zlo, zhi):
    v = 0.0
    for i in range(rad.size):
        r = rad[i]
        a = max(zlo, pos[i, 2] - r)
        b = min(zhi, pos[i, 2] + r)
        if b > a:
            zc = pos[i, 2]
            v += math.pi * (r * r * (b - a) - ((b - zc) ** 3 - (a - zc) ** 3) / 3.0)
    return v / (L * L * (zhi - zlo))


@nb.njit(cache=True)
def surface_map(pos, rad, L, G):
    H = np.zeros((G, G))
    h = L / G
    for i in range(rad.size):
        r = rad[i]
        x0 = pos[i, 0]
        y0 = pos[i, 1]
        n = int(math.ceil(r / h)) + 1
        gx0 = int(x0 / h)
        gy0 = int(y0 / h)
        for a in range(gx0 - n, gx0 + n + 1):
            for b in range(gy0 - n, gy0 + n + 1):
                gx = (a + 0.5) * h
                gy = (b + 0.5) * h
                dx = mi(gx - x0, L)
                dy = mi(gy - y0, L)
                d2 = dx * dx + dy * dy
                if d2 < r * r:
                    zt = pos[i, 2] + math.sqrt(r * r - d2)
                    ia = a % G
                    ib = b % G
                    if zt > H[ia, ib]:
                        H[ia, ib] = zt
    return H


# ------------------------------------------------ force-biased compression
@nb.njit(cache=True)
def _relax(pos, a, L, max_it, tol, cap):
    # FIRE minimisation (Bitzek et al. 2006) of harmonic overlap energy;
    # converged when the largest overlap / (a_i + a_j) < tol
    N = a.size
    amax = a.max()
    ncx = int(L // (2.0 * amax))
    if ncx < 3:
        ncx = 3
    cs = L / ncx
    count = np.zeros((ncx, ncx, ncx), np.int32)
    items = np.empty((ncx, ncx, ncx, cap), np.int32)
    F = np.zeros((N, 3))
    v = np.zeros((N, 3))
    dt = 0.05
    dtmax = 0.3
    alpha0 = 0.1
    alpha = alpha0
    npos = 0
    maxov = 0.0
    for it in range(max_it):
        count[:] = 0
        for i in range(N):
            ix = int(pos[i, 0] / cs) % ncx
            iy = int(pos[i, 1] / cs) % ncx
            iz = int(pos[i, 2] / cs) % ncx
            c = count[ix, iy, iz]
            if c < cap:
                items[ix, iy, iz, c] = i
                count[ix, iy, iz] = c + 1
        F[:] = 0.0
        maxov = 0.0
        for i in range(N):
            ix = int(pos[i, 0] / cs) % ncx
            iy = int(pos[i, 1] / cs) % ncx
            iz = int(pos[i, 2] / cs) % ncx
            for ddx in range(-1, 2):
                cx = (ix + ddx) % ncx
                for ddy in range(-1, 2):
                    cy = (iy + ddy) % ncx
                    for ddz in range(-1, 2):
                        cz = (iz + ddz) % ncx
                        for q in range(count[cx, cy, cz]):
                            j = items[cx, cy, cz, q]
                            if j <= i:
                                continue
                            dx = mi(pos[j, 0] - pos[i, 0], L)
                            dy = mi(pos[j, 1] - pos[i, 1], L)
                            dz = mi(pos[j, 2] - pos[i, 2], L)
                            R = a[i] + a[j]
                            d2 = dx * dx + dy * dy + dz * dz
                            if d2 < R * R:
                                d = math.sqrt(d2)
                                ov = R - d
                                if ov / R > maxov:
                                    maxov = ov / R
                                if d < 1e-12:
                                    dx = 1.0
                                    dy = 0.0
                                    dz = 0.0
                                    d = 1.0
                                s = ov / d
                                F[i, 0] -= s * dx
                                F[i, 1] -= s * dy
                                F[i, 2] -= s * dz
                                F[j, 0] += s * dx
                                F[j, 1] += s * dy
                                F[j, 2] += s * dz
        if maxov < tol:
            return True, maxov, it
        P = 0.0
        fn = 0.0
        vn = 0.0
        for i in range(N):
            for c in range(3):
                P += F[i, c] * v[i, c]
                fn += F[i, c] * F[i, c]
                vn += v[i, c] * v[i, c]
        fn = math.sqrt(fn)
        vn = math.sqrt(vn)
        if P > 0.0:
            for i in range(N):
                for c in range(3):
                    v[i, c] = (1.0 - alpha) * v[i, c] + alpha * vn * F[i, c] / fn
            npos += 1
            if npos > 5:
                dt = min(dt * 1.1, dtmax)
                alpha *= 0.99
        else:
            v[:] = 0.0
            dt *= 0.5
            alpha = alpha0
            npos = 0
        for i in range(N):
            for c in range(3):
                v[i, c] += F[i, c] * dt
                pos[i, c] = (pos[i, c] + v[i, c] * dt) % L
    return False, maxov, max_it


@nb.njit(cache=True)
def compress(rad, phi0, seed, ds0, ds_min, max_it, tol, cap, nsnap):
    np.random.seed(seed)
    N = rad.size
    v = 0.0
    for i in range(N):
        v += 4.0 / 3.0 * math.pi * rad[i] ** 3
    L = (v / phi0) ** (1.0 / 3.0)
    pos = np.empty((N, 3))
    for i in range(N):
        for c in range(3):
            pos[i, c] = np.random.random() * L
    s = 1.0
    ds = ds0
    a = rad * s
    ok, mo, it = _relax(pos, a, L, 20 * max_it, tol, cap)
    good = pos.copy()
    s_good = s
    phis = np.empty(10000)
    its = np.empty(10000)
    nh = 0
    snaps = np.empty((nsnap, N, 3))
    snap_s = np.empty(nsnap)
    ns = 0
    while ds > ds_min and nh < 10000:
        s_try = s_good * (1.0 + ds)
        pos[:] = good
        a = rad * s_try
        ok, mo, it = _relax(pos, a, L, max_it, tol, cap)
        if ok:
            good[:] = pos
            s_good = s_try
            phis[nh] = v * s_good ** 3 / L ** 3
            its[nh] = it
            nh += 1
            if ns < nsnap:
                snaps[ns] = good
                snap_s[ns] = s_good
                ns += 1
            else:
                # keep the latest states: shift
                for q in range(nsnap - 1):
                    snaps[q] = snaps[q + 1]
                    snap_s[q] = snap_s[q + 1]
                snaps[nsnap - 1] = good
                snap_s[nsnap - 1] = s_good
        else:
            ds *= 0.5
    return good, rad * s_good, L, v * s_good ** 3 / L ** 3, phis[:nh].copy(), its[:nh].copy(), snaps[:ns].copy(), snap_s[:ns].copy()
