"""Small 2D incompressible Navier-Stokes solver (planar or axisymmetric r-z).

Staggered MAC grid, explicit (forward Euler) momentum step, pressure projection
with a pre-factorised sparse Poisson matrix. Obstacles are blocked cells. Used by
the validation cases (lid-driven cavity, pipe flow) and the humidity-chamber and
Faraday-cup flows. Written for this folder; numpy/scipy only.

Arrays are indexed [i, j] with i along x (or r) and j along y (or z).
  u: (nx+1, ny) on vertical faces   v: (nx, ny+1) on horizontal faces
  p: (nx, ny) at cell centres (kinematic pressure, p/rho)
"""
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla


class MAC2D:
    def __init__(self, nx, ny, Lx, Ly, nu, axisym=False, solid=None,
                 top="wall", lid_u=0.0, upwind=0.0):
        self.nx, self.ny = nx, ny
        self.dx, self.dy = Lx / nx, Ly / ny
        self.Lx, self.Ly = Lx, Ly
        self.nu = nu
        self.axisym = axisym
        self.top = top            # "wall" or "open" (p = 0 there)
        self.lid_u = lid_u        # tangential velocity of the top wall
        self.w = upwind           # 0 = central, 1 = first-order upwind
        self.xc = (np.arange(nx) + 0.5) * self.dx
        self.xf = np.arange(nx + 1) * self.dx
        self.yc = (np.arange(ny) + 0.5) * self.dy
        self.yf = np.arange(ny + 1) * self.dy
        if axisym:
            self.rc = self.xc.copy()
            self.rf = self.xf.copy()
        else:
            self.rc = np.ones(nx)
            self.rf = np.ones(nx + 1)
        self.solid = np.zeros((nx, ny), bool) if solid is None else solid.astype(bool)
        self.u = np.zeros((nx + 1, ny))
        self.v = np.zeros((nx, ny + 1))
        self.p = np.zeros((nx, ny))
        self.fx = np.zeros_like(self.u)
        self.fy = np.zeros_like(self.v)
        self.ubc = np.zeros_like(self.u)   # values held on fixed u faces (inlets)
        self.vbc = np.zeros_like(self.v)   # values held on fixed v faces (inlets)
        self._masks()
        self._poisson()

    # ------------------------------------------------------------------ masks
    def _masks(self):
        nx, ny, s = self.nx, self.ny, self.solid
        uf = np.zeros((nx + 1, ny), bool)
        uf[0, :] = True               # left wall or axis
        uf[-1, :] = True              # right wall
        uf[1:-1, :] |= s[:-1, :] | s[1:, :]
        vf = np.zeros((nx, ny + 1), bool)
        vf[:, 0] = True               # bottom wall
        if self.top == "wall":
            vf[:, -1] = True
        vf[:, 1:-1] |= s[:, :-1] | s[:, 1:]
        if self.top == "open":
            vf[:, -1] |= s[:, -1]
        self.ufix, self.vfix = uf, vf

    # ---------------------------------------------------------------- poisson
    def _poisson(self):
        nx, ny, dx, dy = self.nx, self.ny, self.dx, self.dy
        N = nx * ny
        idx = np.arange(N).reshape(nx, ny)
        rows, cols, vals = [], [], []
        diag = np.zeros((nx, ny))
        # x-direction faces between cell i-1 and i (i = 1..nx-1)
        for i in range(1, nx):
            open_ = ~self.ufix[i, :]
            jj = np.nonzero(open_)[0]
            c = self.rf[i] / dx ** 2
            a = idx[i - 1, jj]
            b = idx[i, jj]
            ca = c / self.rc[i - 1]
            cb = c / self.rc[i]
            rows += [a, a, b, b]
            cols += [b, a, a, b]
            vals += [np.full(jj.size, ca), np.full(jj.size, -ca),
                     np.full(jj.size, cb), np.full(jj.size, -cb)]
        for j in range(1, ny):
            open_ = ~self.vfix[:, j]
            ii = np.nonzero(open_)[0]
            c = 1.0 / dy ** 2
            a = idx[ii, j - 1]
            b = idx[ii, j]
            rows += [a, a, b, b]
            cols += [b, a, a, b]
            vals += [np.full(ii.size, c), np.full(ii.size, -c),
                     np.full(ii.size, c), np.full(ii.size, -c)]
        if self.top == "open":
            ii = np.nonzero(~self.vfix[:, ny])[0]
            a = idx[ii, ny - 1]
            rows += [a]
            cols += [a]
            vals += [np.full(ii.size, -2.0 / dy ** 2)]
        rows = np.concatenate(rows)
        cols = np.concatenate(cols)
        vals = np.concatenate(vals)
        L = sp.coo_matrix((vals, (rows, cols)), shape=(N, N)).tocsr()
        L = L.tolil()
        sflat = self.solid.ravel()
        for k in np.nonzero(sflat)[0]:
            L.rows[k] = [k]
            L.data[k] = [1.0]
        self.pin = None
        if self.top != "open":
            k = int(np.nonzero(~sflat)[0][0])
            L.rows[k] = [k]
            L.data[k] = [1.0]
            self.pin = k
        self.L = L.tocsc()
        self.lu = spla.splu(self.L)

    # ----------------------------------------------------------- operators
    def divergence(self, u, v):
        div = (self.rf[1:, None] * u[1:, :] - self.rf[:-1, None] * u[:-1, :]) / (
            self.rc[:, None] * self.dx) + (v[:, 1:] - v[:, :-1]) / self.dy
        return div

    def _blend(self, U, phiL, phiR):
        cen = 0.5 * (phiL + phiR)
        if isinstance(self.w, str):          # "hybrid": upwind where the cell Peclet > 2
            w = (np.abs(U) * min(self.dx, self.dy) / float(np.min(self.nu)) > 2.0)
            up = np.where(U >= 0.0, phiL, phiR)
            return np.where(w, up, cen)
        if self.w == 0.0:
            return cen
        up = np.where(U >= 0.0, phiL, phiR)
        return (1.0 - self.w) * cen + self.w * up

    def rhs(self, u, v):
        nx, ny, dx, dy = self.nx, self.ny, self.dx, self.dy
        rc, rf = self.rc, self.rf
        nu = self.nu
        # ---- ghost-padded u in y (for walls halfway between faces)
        top_wall_u = self.lid_u if self.top == "wall" else None
        uN = np.empty_like(u)
        uN[:, :-1] = np.where(self.ufix[:, 1:], -u[:, :-1], u[:, 1:])
        if self.top == "wall":
            uN[:, -1] = 2.0 * top_wall_u - u[:, -1]
        else:
            uN[:, -1] = u[:, -1]
        uS = np.empty_like(u)
        uS[:, 1:] = np.where(self.ufix[:, :-1], -u[:, 1:], u[:, :-1])
        uS[:, 0] = -u[:, 0]
        # ---- ghost-padded v in x
        vE = np.empty_like(v)
        vE[:-1, :] = np.where(self.vfix[1:, :], -v[:-1, :], v[1:, :])
        vE[-1, :] = -v[-1, :]
        vW = np.empty_like(v)
        vW[1:, :] = np.where(self.vfix[:-1, :], -v[1:, :], v[:-1, :])
        vW[0, :] = v[0, :] if self.axisym else -v[0, :]

        # ================= u momentum (interior faces i = 1..nx-1)
        Ru = np.zeros_like(u)
        # x flux at cell centres
        Uc = 0.5 * (u[:-1, :] + u[1:, :])                      # (nx, ny)
        phic = self._blend(Uc, u[:-1, :], u[1:, :])
        Fx = rc[:, None] * Uc * phic
        adv_x = (Fx[1:, :] - Fx[:-1, :]) / (rf[1:-1, None] * dx)   # (nx-1, ny)
        # y flux at corners (i, j+1/2) for j = 0..ny  (ny+1 corners)
        Vcor = np.zeros((nx - 1, ny + 1))
        Vcor[:, :] = 0.5 * (v[:-1, :] + v[1:, :])
        ui = u[1:-1, :]
        uiN = uN[1:-1, :]
        phiN = self._blend(Vcor[:, 1:], ui, uiN)                # corners j+1/2, j=0..ny-1
        uiS = uS[1:-1, :]
        phiS = self._blend(Vcor[:, :-1], uiS, ui)
        Fy_n = Vcor[:, 1:] * phiN
        Fy_s = Vcor[:, :-1] * phiS
        adv_y = (Fy_n - Fy_s) / dy
        # diffusion
        lap_x = (rc[1:, None] * (u[2:, :] - ui) - rc[:-1, None] * (ui - u[:-2, :])) / (
            rf[1:-1, None] * dx ** 2)
        lap_y = (uiN - 2.0 * ui + uiS) / dy ** 2
        lap = lap_x + lap_y
        if self.axisym:
            lap = lap - ui / rf[1:-1, None] ** 2
        Ru[1:-1, :] = -(adv_x + adv_y) + nu * lap + self.fx[1:-1, :]

        # ================= v momentum (interior faces j = 1..ny-1, + open top)
        Rv = np.zeros_like(v)
        vj = v[:, 1:-1]
        # y flux at cell centres
        Vc = 0.5 * (v[:, :-1] + v[:, 1:])                      # (nx, ny)
        phic = self._blend(Vc, v[:, :-1], v[:, 1:])
        Fy = Vc * phic
        adv_y = (Fy[:, 1:] - Fy[:, :-1]) / dy                   # (nx, ny-1)
        # x flux at corners (i+1/2, j) for i = -1/2..nx-1/2  -> faces of u (nx+1)
        Ucor = 0.5 * (u[:, :-1] + u[:, 1:])                     # (nx+1, ny-1)
        phiE = self._blend(Ucor[1:, :], vj, vE[:, 1:-1])
        phiW = self._blend(Ucor[:-1, :], vW[:, 1:-1], vj)
        Fe = rf[1:, None] * Ucor[1:, :] * phiE
        Fw = rf[:-1, None] * Ucor[:-1, :] * phiW
        adv_x = (Fe - Fw) / (rc[:, None] * dx)
        lap_x = (rf[1:, None] * (vE[:, 1:-1] - vj) - rf[:-1, None] * (vj - vW[:, 1:-1])) / (
            rc[:, None] * dx ** 2)
        lap_y = (v[:, 2:] - 2.0 * vj + v[:, :-2]) / dy ** 2
        Rv[:, 1:-1] = -(adv_x + adv_y) + nu * (lap_x + lap_y) + self.fy[:, 1:-1]
        return Ru, Rv

    def project(self, us, vs, dt):
        nx, ny = self.nx, self.ny
        if self.top == "open":
            vs[:, -1] = np.where(self.vfix[:, -1], 0.0, vs[:, -2])
        us[self.ufix] = self.ubc[self.ufix]
        vs[self.vfix] = self.vbc[self.vfix]
        div = self.divergence(us, vs)
        b = (div / dt).ravel()
        b[self.solid.ravel()] = 0.0
        if self.pin is not None:
            b[self.pin] = 0.0
        p = self.lu.solve(b).reshape(nx, ny)
        p[self.solid] = 0.0
        gx = np.zeros_like(us)
        gx[1:-1, :] = (p[1:, :] - p[:-1, :]) / self.dx
        gy = np.zeros_like(vs)
        gy[:, 1:-1] = (p[:, 1:] - p[:, :-1]) / self.dy
        if self.top == "open":
            gy[:, -1] = -2.0 * p[:, -1] / self.dy
        us -= dt * gx
        vs -= dt * gy
        us[self.ufix] = self.ubc[self.ufix]
        vs[self.vfix] = self.vbc[self.vfix]
        return us, vs, p

    def stable_dt(self, umax, safety=0.4):
        h = min(self.dx, self.dy)
        nu = float(np.max(self.nu))
        dt_d = 0.25 * h * h / nu
        dt_c = h / max(umax, 1e-12)
        dt_m = 2.0 * nu / max(umax, 1e-12) ** 2 if self.w < 1.0 else np.inf
        if isinstance(self.w, str):
            return safety * min(dt_d, 0.5 * dt_c)
        return safety * min(dt_d, dt_c, dt_m) if self.w < 1 else safety * min(dt_d, dt_c)

    def step(self, dt):
        Ru, Rv = self.rhs(self.u, self.v)
        us = self.u + dt * Ru
        vs = self.v + dt * Rv
        # optional implicit damping (porous plates, fan relaxation): du/dt = -c (u - target)
        if getattr(self, "cu", None) is not None:
            us = (us + dt * self.cu * self.u_target) / (1.0 + dt * self.cu)
        if getattr(self, "cv_fun", None) is not None:
            cv = self.cv_fun(self)
            vs = vs / (1.0 + dt * cv)
        if getattr(self, "cv", None) is not None:      # relax v towards v_target (particle drag)
            vs = (vs + dt * self.cv * self.v_target) / (1.0 + dt * self.cv)
        us, vs, p = self.project(us, vs, dt)
        du = max(np.abs(us - self.u).max(), np.abs(vs - self.v).max()) / dt
        self.u, self.v, self.p = us, vs, p
        return du

    def run(self, t_end, dt, tol=1e-6, callback=None, every=500, verbose=True):
        t, n = 0.0, 0
        du = np.inf
        while t < t_end:
            du = self.step(dt)
            t += dt
            n += 1
            if callback is not None and n % every == 0:
                callback(self, t)
            if verbose and n % every == 0:
                print(f"  t = {t:.4f}  max|du/dt| = {du:.3e}  max div = "
                      f"{np.abs(self.divergence(self.u, self.v)[~self.solid]).max():.2e}",
                      flush=True)
            if du < tol:
                break
        return t, n, du

    # ------------------------------------------------------------ utilities
    def cell_velocity(self):
        uc = 0.5 * (self.u[:-1, :] + self.u[1:, :])
        vc = 0.5 * (self.v[:, :-1] + self.v[:, 1:])
        return uc, vc

    def streamfunction(self):
        """Planar: psi with u = dpsi/dy. Axisymmetric (Stokes): r u_z = dpsi/dr."""
        nx, ny = self.nx, self.ny
        psi = np.zeros((nx + 1, ny + 1))
        # integrate along x at the bottom (psi=0 on bottom wall) then up in y
        for j in range(ny):
            psi[:, j + 1] = psi[:, j] + self.u[:, j] * self.dy * (self.rf if self.axisym else 1.0)
        return psi
