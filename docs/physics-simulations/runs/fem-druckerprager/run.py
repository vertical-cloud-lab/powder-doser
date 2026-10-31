#!/usr/bin/env python3
"""Self-written 2D plane-strain small-strain elastoplastic FEM (numpy/scipy):
8-node serendipity quads, 2x2 reduced integration (as in Griffiths & Lane 1999 slope stability),
associated Drucker-Prager matched to Mohr-Coulomb in plane strain, closed-form return mapping
(cone + apex), initial-stiffness (modified Newton) iterations with a factorised elastic K.
Problem: 'trapdoor' arching test - cohesive powder layer of height Hs over an open slot of width B
(the doser's 3 mm exit, treated as a plane slot), self-weight increased by factor lam until no
equilibrium can be found (iteration ceiling = collapse criterion). Symmetric half model."""
import os, sys, json, time
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla

SCR = "/tmp/sims-scratch/fem-druckerprager"; os.makedirs(SCR, exist_ok=True)
rho, g = 1250.0, 9.81                      # bulk density assumed (salt bed 1200-1300 kg/m^3)
E, nu = 1.0e6, 0.3
Gm = E / (2 * (1 + nu)); Km = E / (3 * (1 - 2 * nu)); lamL = Km - 2 * Gm / 3

def mesh(B, Hs, Wd, nx, ny):
    xs = np.linspace(0, Wd, 2 * nx + 1); ys = np.linspace(0, Hs, 2 * ny + 1)
    used = np.ones((2 * nx + 1, 2 * ny + 1), bool); used[1::2, 1::2] = False
    idx = -np.ones(used.shape, int); idx[used] = np.arange(used.sum())
    I, J = np.nonzero(used)
    XY = np.zeros((used.sum(), 2)); XY[idx[I, J], 0] = xs[I]; XY[idx[I, J], 1] = ys[J]
    con = []
    for ex in range(nx):
        for ey in range(ny):
            i, j = 2 * ex, 2 * ey
            con.append([idx[i, j], idx[i + 2, j], idx[i + 2, j + 2], idx[i, j + 2],
                        idx[i + 1, j], idx[i + 2, j + 1], idx[i + 1, j + 2], idx[i, j + 1]])
    return XY, np.array(con)

xi_n = np.array([-1, 1, 1, -1, 0, 1, 0, -1.0]); eta_n = np.array([-1, -1, 1, 1, -1, 0, 1, 0.0])
def shape(xi, eta):
    N = np.zeros(8); dN = np.zeros((2, 8))
    for k in range(8):
        a, b = xi_n[k], eta_n[k]
        if k < 4:
            N[k] = 0.25 * (1 + xi * a) * (1 + eta * b) * (xi * a + eta * b - 1)
            dN[0, k] = 0.25 * a * (1 + eta * b) * (2 * xi * a + eta * b)
            dN[1, k] = 0.25 * b * (1 + xi * a) * (xi * a + 2 * eta * b)
        elif a == 0:
            N[k] = 0.5 * (1 - xi * xi) * (1 + eta * b); dN[0, k] = -xi * (1 + eta * b); dN[1, k] = 0.5 * b * (1 - xi * xi)
        else:
            N[k] = 0.5 * (1 + xi * a) * (1 - eta * eta); dN[0, k] = 0.5 * a * (1 - eta * eta); dN[1, k] = -eta * (1 + xi * a)
    return N, dN

def assemble(XY, con):
    D = np.zeros((4, 4)); D[:3, :3] = lamL; D[[0, 1, 2], [0, 1, 2]] = lamL + 2 * Gm; D[3, 3] = Gm
    gp = np.array([-1, 1]) / np.sqrt(3.0)
    rows, cols, vals = [], [], []; Fb = np.zeros(2 * len(XY)); wts = []; gxy = []
    ngp = 0
    for e, c in enumerate(con):
        xe = XY[c]; dofs = np.ravel(np.column_stack([2 * c, 2 * c + 1]))
        for xi in gp:
            for eta in gp:
                N, dN = shape(xi, eta); Jm = dN @ xe; dJ = np.linalg.det(Jm)
                dNx = np.linalg.solve(Jm, dN)
                Bm = np.zeros((4, 16)); Bm[0, 0::2] = dNx[0]; Bm[1, 1::2] = dNx[1]
                Bm[3, 0::2] = dNx[1]; Bm[3, 1::2] = dNx[0]
                for r in range(4):
                    rows.extend([4 * ngp + r] * 16); cols.extend(dofs); vals.extend(Bm[r])
                Fb[dofs[1::2]] += -rho * g * N * dJ
                wts.append(dJ); gxy.append(N @ xe); ngp += 1
    Bg = sp.csr_matrix((vals, (rows, cols)), shape=(4 * ngp, 2 * len(XY)))
    w = np.array(wts); Dbig = sp.kron(sp.diags(w), sp.csr_matrix(D))
    Kg = (Bg.T @ Dbig @ Bg).tocsc()
    return Kg, Bg, Fb, w, np.array(gxy), D

def dp_return(sig_tr, alpha, k):
    """associated DP, perfect plasticity; sig = [xx,yy,zz,xy] (tension +). Returns sig, dlam"""
    p = sig_tr[:, :3].mean(1); s = sig_tr.copy(); s[:, :3] -= p[:, None]
    q = np.sqrt(0.5 * (s[:, 0] ** 2 + s[:, 1] ** 2 + s[:, 2] ** 2) + s[:, 3] ** 2)
    f = q + 3 * alpha * p - k
    out = sig_tr.copy(); dl = np.zeros(len(p))
    pl = f > 0
    if pl.any():
        dlam = f[pl] / (Gm + 9 * Km * alpha ** 2)
        qn = q[pl] - Gm * dlam
        cone = qn > 0
        sc = np.where(cone, qn / np.maximum(q[pl], 1e-30), 0.0)
        pn = np.where(cone, p[pl] - 3 * Km * alpha * dlam, k / (3 * alpha))
        sn = s[pl] * sc[:, None]; sn[:, :3] += pn[:, None]
        out[pl] = sn; dl[pl] = dlam
    return out, dl

def solve_case(c, phi_deg, B=3e-3, Hs=9e-3, Wd=9e-3, nx=36, ny=36, lam_step=0.25, itmax=800, tol=1e-4):
    tp = np.tan(np.radians(phi_deg)); den = np.sqrt(9 + 12 * tp * tp)
    alpha, k = tp / den, 3 * c / den
    XY, con = mesh(B, Hs, Wd, nx, ny)
    Kg, Bg, Fb, w, gxy, D = assemble(XY, con)
    nd = 2 * len(XY); fixed = np.zeros(nd, bool)
    x, y = XY[:, 0], XY[:, 1]; tolx = 1e-12
    fixed[2 * np.nonzero(x < tolx)[0]] = True                  # symmetry plane: u_x = 0
    fixed[2 * np.nonzero(x > Wd - tolx)[0]] = True             # smooth side wall: u_x = 0
    sup = np.nonzero((y < tolx) & (x > B / 2 - tolx))[0]       # rough floor beside the slot
    fixed[2 * sup] = True; fixed[2 * sup + 1] = True
    free = ~fixed
    Kff = Kg[free][:, free].tocsc(); lu = spla.splu(Kff)
    ngp = len(w); sig = np.zeros((ngp, 4)); u = np.zeros(nd); eqp = np.zeros(ngp)
    lam, last_ok, hist = 0.0, 0.0, []
    probe = np.nonzero((x < tolx) & (y < tolx))[0][0]          # slot centre node
    state_ok = (u.copy(), sig.copy(), eqp.copy())
    dlam_cur = lam_step; nbis = 0; failed_at = None
    while nbis < 4 and lam < 20:
        lam_try = last_ok + dlam_cur
        u, sig, eqp = (a.copy() for a in state_ok)
        sig_n = sig.copy(); du_inc = np.zeros(nd); Fext = lam_try * Fb
        conv = False
        for it in range(itmax):
            eps_inc = (Bg @ du_inc).reshape(-1, 4)
            sig_t = sig_n + eps_inc @ D.T
            sig_new, dl = dp_return(sig_t, alpha, k)
            Fint = Bg.T @ (sig_new * w[:, None]).ravel()
            R = Fext - Fint
            rn = np.linalg.norm(R[free]) / np.linalg.norm(Fext[free])
            if rn < tol and it > 0:
                conv = True; break
            ddu = np.zeros(nd); ddu[free] = lu.solve(R[free]); du_inc += ddu
        if conv:
            u = state_ok[0] + du_inc; sig = sig_new; eqp = state_ok[2] + dl
            state_ok = (u.copy(), sig.copy(), eqp.copy()); last_ok = lam_try
            hist.append((lam_try, -u[2 * probe + 1], it))
            if failed_at is not None:
                dlam_cur *= 0.5; nbis += 1
        else:
            failed_at = lam_try; dlam_cur *= 0.5; nbis += 1
        lam = last_ok
    lam_c = 0.5 * (last_ok + (failed_at if failed_at is not None else last_ok))
    N = lam_c * rho * g * B / c
    np.savez_compressed(f"{SCR}/state_c{int(c)}.npz", XY=XY, con=con, u=state_ok[0], eqp=state_ok[2], gxy=gxy,
                        hist=np.array(hist))
    return dict(cohesion_Pa=c, phi_deg=phi_deg, B_m=B, Hs_m=Hs, half_width_m=Wd, elements=int(nx * ny),
                dofs=int(nd), gauss_points=int(ngp), last_converged_lam=float(last_ok),
                first_failed_lam=None if failed_at is None else float(failed_at), lam_collapse=float(lam_c),
                stability_number_N=float(N), c_crit_at_1g_Pa=float(rho * g * B / N),
                history=[[float(a), float(b), int(cc)] for a, b, cc in hist])

if __name__ == "__main__":
    T0 = time.time(); out = {"cases": []}
    for c in [10.0, 20.0, 40.0]:
        t0 = time.time(); r = solve_case(c, 34.0); r["wall_s"] = round(time.time() - t0, 1)
        out["cases"].append(r); print({k: v for k, v in r.items() if k != "history"}, flush=True)
    t0 = time.time(); r = solve_case(20.0, 25.0); r["wall_s"] = round(time.time() - t0, 1)
    out["cases"].append(r); print({k: v for k, v in r.items() if k != "history"}, flush=True)
    out["total_wall_s"] = round(time.time() - T0, 1)
    json.dump(out, open(f"{SCR}/raw_results.json", "w"), indent=1)
    print("DONE", out["total_wall_s"])
