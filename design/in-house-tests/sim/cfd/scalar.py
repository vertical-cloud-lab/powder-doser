"""Finite-volume transient transport of a scalar (here RH = vapour density / saturation).

Extensive form, so extra unknowns (a powder layer) can be attached to the grid:
    C_k (phi_k^{n+1} - phi_k^n) / dt = sum_l G_kl (phi_l - phi_k) + advection + G_kb (phi_b - phi_k)
C_k [kg per unit RH], G [kg/s per unit RH]. Uniform Cartesian grid, 2D or 3D, blocked cells,
per-cell diffusivity (face value = harmonic mean), optional 2D face velocities from mac2d
(hybrid central/upwind), Dirichlet faces, and a generic "extra nodes" block. Backward Euler.
"""
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla


class Grid:
    def __init__(self, shape, h, D, solid=None, csat=0.023):
        self.shape = tuple(shape)
        self.nd = len(shape)
        self.h = float(h)
        self.n = int(np.prod(shape))
        self.solid = np.zeros(shape, bool) if solid is None else solid.astype(bool)
        self.D = np.broadcast_to(np.asarray(D, float), shape).copy()
        self.D[self.solid] = 0.0
        self.csat = csat
        self.vol = self.h ** self.nd          # per unit depth in 2D
        self.area = self.h ** (self.nd - 1)
        self.idx = np.arange(self.n).reshape(shape)

    def diffusion_graph(self):
        """Return (rows, cols, G) for all fluid-fluid face pairs."""
        R, Cc, G = [], [], []
        for ax in range(self.nd):
            sl_a = [slice(None)] * self.nd
            sl_b = [slice(None)] * self.nd
            sl_a[ax] = slice(0, -1)
            sl_b[ax] = slice(1, None)
            Da, Db = self.D[tuple(sl_a)], self.D[tuple(sl_b)]
            with np.errstate(divide="ignore", invalid="ignore"):
                Df = np.where((Da > 0) & (Db > 0), 2 * Da * Db / (Da + Db), 0.0)
            m = Df > 0
            ia = self.idx[tuple(sl_a)][m]
            ib = self.idx[tuple(sl_b)][m]
            g = Df[m] * self.area / self.h * self.csat
            R.append(ia)
            Cc.append(ib)
            G.append(g)
        return np.concatenate(R), np.concatenate(Cc), np.concatenate(G)


class Transport:
    """Assemble and step  M phi^{n+1} = C/dt phi^n + b."""

    def __init__(self, grid, extra_C=None, extra_links=None, dirichlet=None, vel=None,
                 eps_cap=1.0):
        """
        extra_C: capacities of extra nodes (appended after the grid cells)
        extra_links: (i, j, G) arrays linking any nodes (grid or extra, global numbering)
        dirichlet: (cells, G, value) arrays; value may be updated later via set_dirichlet_value
        vel: None or (u, v) 2D MAC face velocities (u: (nx+1, ny), v: (nx, ny+1)), planar
        """
        self.g = grid
        n0 = grid.n
        self.ne = 0 if extra_C is None else len(extra_C)
        self.N = n0 + self.ne
        C = np.zeros(self.N)
        C[:n0] = grid.vol * grid.csat * eps_cap
        C[:n0][grid.solid.ravel()] = 0.0
        if self.ne:
            C[n0:] = extra_C
        self.C = C
        r, c, G = grid.diffusion_graph()
        if extra_links is not None:
            r = np.concatenate([r, extra_links[0]])
            c = np.concatenate([c, extra_links[1]])
            G = np.concatenate([G, extra_links[2]])
        self.links = (r, c, G)
        self.dir_cells = np.array([], int) if dirichlet is None else np.asarray(dirichlet[0], int)
        self.dir_G = np.array([]) if dirichlet is None else np.asarray(dirichlet[1], float)
        self.dir_val = np.array([]) if dirichlet is None else np.broadcast_to(
            np.asarray(dirichlet[2], float), self.dir_cells.shape).copy()
        self.A_adv = None
        if vel is not None:
            self.A_adv = self._advection(*vel)
        self.K = self._laplacian()
        dead = np.zeros(self.N, bool)
        dead[:n0] = grid.solid.ravel()
        self.dead = sp.diags(dead.astype(float))
        self._cache = {}

    def _laplacian(self):
        r, c, G = self.links
        N = self.N
        off = sp.coo_matrix((np.concatenate([-G, -G]), (np.concatenate([r, c]), np.concatenate([c, r]))),
                            shape=(N, N))
        d = np.zeros(N)
        np.add.at(d, r, G)
        np.add.at(d, c, G)
        if self.dir_cells.size:
            np.add.at(d, self.dir_cells, self.dir_G)
        K = (off + sp.diags(d)).tocsr()
        return K

    def _advection(self, u, v):
        """Hybrid (central if cell Peclet <= 2, else upwind) advection matrix, extensive form.
        Row k gives the net outflow  sum_faces F * phi_face  (to be added to the LHS)."""
        g = self.g
        nx, ny = g.shape
        h = g.h
        rows, cols, vals = [], [], []
        Dc = g.D
        # x faces between (i-1, j) and (i, j), i = 1..nx-1
        for ax in (0, 1):
            if ax == 0:
                U = u[1:-1, :]
                ia = g.idx[:-1, :]
                ib = g.idx[1:, :]
                Da, Db = Dc[:-1, :], Dc[1:, :]
            else:
                U = v[:, 1:-1]
                ia = g.idx[:, :-1]
                ib = g.idx[:, 1:]
                Da, Db = Dc[:, :-1], Dc[:, 1:]
            with np.errstate(divide="ignore", invalid="ignore"):
                Df = np.where((Da > 0) & (Db > 0), 2 * Da * Db / (Da + Db), 0.0)
            m = (Df > 0) & (U != 0)
            U, ia, ib, Df = U[m], ia[m], ib[m], Df[m]
            F = U * g.area * g.csat            # kg/s per unit RH, + from a to b
            Pe = np.abs(U) * h / Df
            cen = Pe <= 2.0
            wa = np.where(cen, 0.5, np.where(U > 0, 1.0, 0.0))
            wb = 1.0 - wa
            # outflow from a: +F*(wa*phi_a + wb*phi_b); inflow to b: -F*(...)
            rows += [ia, ia, ib, ib]
            cols += [ia, ib, ia, ib]
            vals += [F * wa, F * wb, -F * wa, -F * wb]
        A = sp.coo_matrix((np.concatenate(vals), (np.concatenate(rows), np.concatenate(cols))),
                          shape=(self.N, self.N)).tocsr()
        return A

    def matrix(self, dt, C=None):
        C = self.C if C is None else C
        M = self.K + sp.diags(C / dt) + self.dead
        if self.A_adv is not None:
            M = M + self.A_adv
        return M.tocsc()

    def step(self, phi, dt, C=None, src=None, solver="lu", x0=None, rebuild=False):
        C = self.C if C is None else C
        b = C / dt * phi
        if self.dir_cells.size:
            np.add.at(b, self.dir_cells, self.dir_G * self.dir_val)
        if src is not None:
            b = b + src
        if solver == "lu":
            key = (round(dt, 9),)
            if rebuild or key not in self._cache:
                if len(self._cache) > 6:
                    self._cache.clear()
                self._cache[key] = spla.splu(self.matrix(dt, C))
            return self._cache[key].solve(b)
        M = self.matrix(dt, C).tocsr()
        d = M.diagonal()
        d[d == 0] = 1.0
        Pinv = sp.diags(1.0 / d)
        fixed = C == 0
        if np.any(fixed & (d == 1.0)):
            pass
        x, info = spla.cg(M, b, x0=phi if x0 is None else x0, rtol=1e-10, atol=0.0, M=Pinv, maxiter=2000)
        if info != 0:
            raise RuntimeError(f"CG did not converge ({info})")
        return x

    def steady(self):
        M = self.K + self.dead
        b = np.zeros(self.N)
        np.add.at(b, self.dir_cells, self.dir_G * self.dir_val)
        if self.A_adv is None and self.g.nd == 3:
            # symmetric: preconditioned CG keeps memory low on 3D grids
            M = M.tocsr()
            d = M.diagonal()
            x, info = spla.cg(M, b, rtol=1e-11, atol=0.0, M=sp.diags(1.0 / d), maxiter=20000)
            return x
        if self.A_adv is not None:
            M = M + self.A_adv
        return spla.spsolve(M.tocsc(), b)
