"""Rigid-body physics simulation of the v2 chain carousel (PyBullet, Featherstone multibody).

    python sim/carousel_sim.py index --speed 50 --moves 2        # two index moves and a dwell
    python sim/carousel_sim.py lap --speed 50                    # one full lap (104 pitches)
    python sim/carousel_sim.py lap --speed 100 --hook 5          # faster, weaker snap hooks
    python sim/carousel_sim.py estop --speed 100                 # power cut mid-move: the loop coasts

Everything comes from the CAD: ``layout.chain_pins()`` gives the exact pin
positions of both chains, ``layout.carriage_frame()`` the carriages, and
``params.py`` the sprocket tooth form, the link masses and the module
geometry. The model:

* **Each chain is one articulated body** (Featherstone / reduced
  coordinates, so the chain cannot stretch): 104 pin-jointed links, closed
  by a point-constraint hinge. **Each carriage is a body** bolted to its
  A-1 link on both chains with fixed constraints, carrying its module
  (Sam's plate + auger + cap + powder) on a revolute joint with a limit at
  the closed position (the hard stop). The snap hooks are a detent: a
  holding torque up to ``--hook`` newtons at the hook, released once the
  plate lifts past the hooks' 0.8 mm overlap.
* **4 corner shafts**, each a revolute body carrying its front and back 32T
  sprocket. Every tooth is a convex prism with the ANSI 35 flanks (17 deg
  from radial off the seat circle) on a root disc at the seat bottom, so the chain is driven by tooth-on-bushing
  contact, not by a kinematic trick. The B+ shaft has the motor (velocity
  control, 12 N*m limit); the other three are free idlers with bearing
  drag. The two top shafts ride vertical slides and are pushed up with the
  jack-screw force, which is how the real rig tensions the chains.
* **Static obstacles** for clash detection: side plates, the station
  hold-downs, the motor and the retracted electronics carriage.

Units inside the engine are cm, kg, s (g = 981 cm/s^2); everything logged
and printed is in mm, N and N*m. Results go to ``sim/results/<run>/``:
metrics.json, timeseries.csv and poses.npz for ``render_sim.py``.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
import pybullet as p

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import layout as L  # noqa: E402
from params import *  # noqa: E402,F401,F403

S = 0.1                       # mm -> cm
G = 981.0                     # cm/s^2
NM = 1e4                      # 1 N*m = 1e4 kg cm^2/s^2
NEWTON = 100.0                # 1 N = 100 kg cm/s^2
ALPHA = 2 * math.pi / N_TEETH
HULL_MARGIN_MM = 0.4           # btConvexHullShape default margin (0.04 engine units = 0.4 mm here)
TOOTH_LINK_MASS = 0.25         # the tooth rings ride on fixed child links; keep their mass sane for the solver
TOOTH_LINK_I = 5.0

GRP_STATIC, GRP_SPROCKET, GRP_BUSH, GRP_PLATE, GRP_CARRIAGE, GRP_MODULE = 1, 2, 4, 8, 16, 32


def quat_from_R(R3: np.ndarray):
    """x, y, z, w quaternion of a 3x3 rotation matrix."""
    m = np.asarray(R3, float)
    t = np.trace(m)
    if t > 0:
        s = math.sqrt(t + 1.0) * 2
        w, x, y, z = 0.25 * s, (m[2, 1] - m[1, 2]) / s, (m[0, 2] - m[2, 0]) / s, (m[1, 0] - m[0, 1]) / s
    elif m[0, 0] > m[1, 1] and m[0, 0] > m[2, 2]:
        s = math.sqrt(1.0 + m[0, 0] - m[1, 1] - m[2, 2]) * 2
        w, x, y, z = (m[2, 1] - m[1, 2]) / s, 0.25 * s, (m[0, 1] + m[1, 0]) / s, (m[0, 2] + m[2, 0]) / s
    elif m[1, 1] > m[2, 2]:
        s = math.sqrt(1.0 + m[1, 1] - m[0, 0] - m[2, 2]) * 2
        w, x, y, z = (m[0, 2] - m[2, 0]) / s, (m[0, 1] + m[1, 0]) / s, 0.25 * s, (m[1, 2] + m[2, 1]) / s
    else:
        s = math.sqrt(1.0 + m[2, 2] - m[0, 0] - m[1, 1]) * 2
        w, x, y, z = (m[1, 0] - m[0, 1]) / s, (m[0, 2] + m[2, 0]) / s, (m[1, 2] + m[2, 1]) / s, 0.25 * s
    return [x, y, z, w]


def M_of(pos, orn, com_offset=None) -> np.ndarray:
    """4x4 transform (mm) from a PyBullet pose (cm); com_offset (cm, local) converts a COM pose to a frame pose."""
    R3 = np.array(p.getMatrixFromQuaternion(orn)).reshape(3, 3)
    M = np.eye(4)
    M[:3, :3] = R3
    t = np.asarray(pos, float)
    if com_offset is not None:
        t = t - R3 @ np.asarray(com_offset, float)
    M[:3, 3] = t / S
    return M


# ---------------------------------------------------------------- sprocket teeth
def tooth_outline_pieces(n_sub: int = 1):
    """Convex pieces (lists of (y, z) mm points) covering one tooth of the
    32T sprocket, gap 0 centred on +y, tooth 0 between gaps 0 and 1. The
    tooth is the trapezoid between the two flanks of the adjacent gaps
    (ANSI 35 form: the flanks leave the seat circle's side points at 17 deg
    from radial), clipped by the tip circle. The seat bottom itself is the
    root disc (radius R - seat radius), so a bushing rests on the disc and
    is pushed by the flank, as in the real sprocket."""
    m = HULL_MARGIN_MM                 # Bullet adds this outside every convex hull: erode the tooth by it
    rs = SEAT_D / 2 + m
    half = math.radians(17.0)
    r0 = R - 0.2
    pts = []
    for sign, ang in ((1, 0.0), (-1, ALPHA)):
        # flank of gap at `ang`, on the tooth side (sign): starts at (r0, sign*rs) in the gap's frame
        c, s_ = math.cos(ang), math.sin(ang)
        for t in (0.0, 1.0):
            rr = r0 + t * (OD / 2 + 0.5 - r0)
            ty = sign * (rs + (rr - r0) * math.tan(half))
            x, y = rr * c - ty * s_, rr * s_ + ty * c
            pts.append((x, y))
    # clip radius to the tip circle (eroded by the margin too)
    tip = OD / 2 - m
    out = []
    for x, y in pts:
        rr = math.hypot(x, y)
        if rr > tip:
            x, y = x * tip / rr, y * tip / rr
        out.append((x, y))
    am = ALPHA / 2
    out.append((tip * math.cos(am), tip * math.sin(am)))
    return [out]


class Carousel:
    def __init__(self, dt=1e-3, hook_N=10.0, salt_g=100.0, bearing_drag=0.02, station_docked=False, tension_N=80.0,
                 erp=0.2, iters=150, sliders=False):
        self.sliders = sliders
        self.dt = dt
        self.hook_N = hook_N
        self.salt_g = salt_g
        self.tension_N = tension_N
        self.bearing_drag = bearing_drag
        self.station_docked = station_docked
        self.hooks_locked = True
        self.erp = erp
        self.cid = p.connect(p.DIRECT)
        p.resetSimulation()
        p.setGravity(0, 0, -G)
        p.setPhysicsEngineParameter(fixedTimeStep=dt, numSolverIterations=iters, numSubSteps=1,
                                    contactBreakingThreshold=0.02, erp=0.2, contactERP=0.2, frictionERP=0.2,
                                    enableConeFriction=0, deterministicOverlappingPairs=1, solverResidualThreshold=1e-7)
        self.corner_ids: dict[str, int] = {}
        self.static_ids: dict[int, str] = {}
        self.names: dict[tuple, str] = {}
        self.module_open = [False] * N_MODULES
        self.module_max_tilt = [0.0] * N_MODULES
        self.pb_index: dict[tuple, int] = {}
        self.closures: list = []
        self.bolts: list = []
        self.sensors: list = []
        self._mesh_count = 0
        self._build_static()
        self._build_corners()
        self._build_loop()
        self._set_filters()

    # ------------------------------------------------------------ shapes
    def _box(self, half, pos=(0, 0, 0), orn=(0, 0, 0, 1)):
        return (p.GEOM_BOX, dict(halfExtents=[h * S for h in half]), [c * S for c in pos], orn)

    def _cyl(self, r, length, pos, axis="x"):
        orn = p.getQuaternionFromEuler([0, math.pi / 2, 0]) if axis == "x" else (0, 0, 0, 1)
        return (p.GEOM_CYLINDER, dict(radius=r * S, height=length * S), [c * S for c in pos], orn)

    def _mesh(self, verts, pos=(0, 0, 0)):
        """Convex hull of ``verts`` (mm) as a tiny OBJ, so it can go in a compound."""
        from scipy.spatial import ConvexHull
        cache = HERE / ".cache"
        cache.mkdir(exist_ok=True)
        self._mesh_count += 1
        f = cache / f"hull_{self._mesh_count:04d}.obj"
        V = np.asarray(verts, float) * S
        hull = ConvexHull(V)
        lines = [f"v {x:.5f} {y:.5f} {z:.5f}" for x, y, z in V]
        lines += [f"f {a + 1} {b + 1} {c + 1}" for a, b, c in hull.simplices]
        f.write_text("\n".join(lines) + "\n")
        return (p.GEOM_MESH, dict(fileName=str(f)), [c * S for c in pos], (0, 0, 0, 1))

    def _compound(self, shapes):
        kw = dict(shapeTypes=[t for t, _, _, _ in shapes],
                  halfExtents=[d.get("halfExtents", [0, 0, 0]) for _, d, _, _ in shapes],
                  radii=[d.get("radius", 0) for _, d, _, _ in shapes],
                  lengths=[d.get("height", 0) for _, d, _, _ in shapes],
                  fileNames=[d.get("fileName", "") for _, d, _, _ in shapes],
                  meshScales=[[1, 1, 1] for _ in shapes],
                  collisionFramePositions=[pos for _, _, pos, _ in shapes],
                  collisionFrameOrientations=[orn for _, _, _, orn in shapes])
        return p.createCollisionShapeArray(**kw)

    # ------------------------------------------------------------ static
    def _build_static(self):
        feats = []
        xf, xb = -SIDE_GAP - PLATE_T_SIDE / 2, CHAIN_L + SIDE_GAP + PLATE_T_SIDE / 2
        feats.append(("side plate front", [self._box((PLATE_T_SIDE / 2, SIDE_W / 2, (SIDE_Z[1] - SIDE_Z[0]) / 2),
                                                     (xf, 0, (SIDE_Z[0] + SIDE_Z[1]) / 2))]))
        feats.append(("side plate back", [self._box((PLATE_T_SIDE / 2, SIDE_W / 2, (SIDE_Z_BACK[1] - SIDE_Z_BACK[0]) / 2),
                                                    (xb, 0, (SIDE_Z_BACK[0] + SIDE_Z_BACK[1]) / 2))]))
        sy = L.STATION_Y
        tz = Z_RUN + CAR_W0 + HOLD_DOWN_GAP                   # lip underside
        w_foot = Z_RUN + CAR_W0 - CAR_T - HOLD_DOWN_FOOT_GAP   # foot top
        m = HULL_MARGIN_MM
        for nm, (x0, x1), (xa, xb_) in (("hold-down front", (-SIDE_GAP, -7.0), (-SIDE_GAP, -SIDE_GAP + 16)),
                                        ("hold-down back", (CHAIN_L + 7.0, CHAIN_L + SIDE_GAP), (CHAIN_L + SIDE_GAP - 16, CHAIN_L + SIDE_GAP))):
            # lip and foot as prisms with the printed part's 2.5 mm lead-in chamfers over the last 7 mm (eroded by the margin)
            ld = HOLD_DOWN_LEAD
            lip = [(sy - 20 + m, tz + ld + m), (sy - 13, tz + m), (sy + 13, tz + m), (sy + 20 - m, tz + ld + m),
                   (sy + 20 - m, tz + 9 - m), (sy - 20 + m, tz + 9 - m)]
            foot = [(sy - 20 + m, w_foot - ld - m), (sy - 13, w_foot - m), (sy + 13, w_foot - m), (sy + 20 - m, w_foot - ld - m),
                    (sy + 20 - m, w_foot - 22 + m), (sy - 20 + m, w_foot - 22 + m)]
            shapes = [self._mesh([(x0 + m, y, z) for y, z in lip] + [(x1 - m, y, z) for y, z in lip]),
                      self._mesh([(xa + m, y, z) for y, z in foot] + [(xb_ - m, y, z) for y, z in foot])]
            feats.append((nm, shapes))
        # slider rails under the station carriage (UHMW on aluminium bars): the carriage plate rides on them, so the
        # station height does not depend on chain sag
        z_rail = Z_RUN + CAR_W0 - CAR_T - SLIDER_GAP
        for nm, (x0, x1) in ((("slider rail front", SLIDER_X[0]), ("slider rail back", SLIDER_X[1])) if self.sliders else ()):
            # UHMW strip with lead-in ramps (SLIDER_RAMP mm drop over SLIDER_RAMP_L mm at each end)
            hl, rd, rl = SLIDER_HALF_L, SLIDER_RAMP, SLIDER_RAMP_L
            prof = [(sy - hl + m, z_rail - rd - m), (sy - hl + rl, z_rail - m), (sy + hl - rl, z_rail - m), (sy + hl - m, z_rail - rd - m),
                    (sy + hl - m, z_rail - 6 + m), (sy - hl + m, z_rail - 6 + m)]
            feats.append((nm, [self._mesh([(x0 + m, y, z) for y, z in prof] + [(x1 - m, y, z) for y, z in prof])]))
        feats.append(("NEMA 34", [self._box((M34_BODY_L / 2, M34_FLANGE / 2, M34_FLANGE / 2),
                                            (CHAIN_L + SIDE_GAP - M34_BODY_L / 2, LOOP_Y, Z_MOTOR))]))
        c = L.to_world(L.sam_frame(L.station_frame()), (37.8, 0, -39.85))
        drop = 0.0 if self.station_docked else 35.0
        feats.append(("electronics carriage", [self._box((35.5, 18, 20.95), (c[0], c[1], c[2] - drop))]))
        feats.append(("bench", [self._box((400, 400, 5), (150, 0, -5))]))
        for nm, shapes in feats:
            bid = p.createMultiBody(0, self._compound(shapes), basePosition=[0, 0, 0])
            p.changeDynamics(bid, -1, lateralFriction=0.3)
            self.static_ids[bid] = nm
            self.names[(bid, -1)] = nm

    # ------------------------------------------------------------ corners
    def _build_corners(self):
        pieces = tooth_outline_pieces()
        tooth_files = []
        for k in range(N_TEETH):
            a = k * ALPHA
            c, s = math.cos(a), math.sin(a)
            for pts in pieces:
                pr = [(x * c - y * s, x * s + y * c) for x, y in pts]
                hw = TOOTH_W / 2 - HULL_MARGIN_MM
                verts = [(-hw, yy, zz) for yy, zz in pr] + [(hw, yy, zz) for yy, zz in pr]
                tooth_files.append(self._mesh(verts)[1]["fileName"])
        # PyBullet compounds hold at most 16 children, so the shaft + hubs + root discs are one link and the
        # 32 teeth of each sprocket ride on two fixed child links of 16 teeth each.
        for name, (y, z) in L.CORNERS.items():
            core = [self._cyl(SHAFT_D / 2, L.SHAFT_L, (L.SHAFT_X0 + L.SHAFT_L / 2, 0, 0))]
            tooth_links = []
            for xs in (0.0, CHAIN_L):
                hx = -1 if xs == 0.0 else 1
                core.append(self._cyl(HUB_D / 2, LTB - TOOTH_W, (xs + hx * (TOOTH_W / 2 + (LTB - TOOTH_W) / 2), 0, 0)))
                core.append(self._cyl(R - SEAT_D / 2, TOOTH_W, (xs, 0, 0)))          # root disc = seat bottom
                for half in (tooth_files[:16], tooth_files[16:]):
                    tooth_links.append(self._compound([(p.GEOM_MESH, dict(fileName=fn), [xs * S, 0, 0], (0, 0, 0, 1)) for fn in half]))
            col = self._compound(core)
            top = name.startswith("T")
            mass = 2 * 0.49 + 0.63
            nt = len(tooth_links)
            bid = p.createMultiBody(baseMass=0.5 if top else 0, baseCollisionShapeIndex=-1, basePosition=[0, y * S, z * S],
                                    linkMasses=[mass] + [TOOTH_LINK_MASS] * nt, linkCollisionShapeIndices=[col] + tooth_links,
                                    linkVisualShapeIndices=[-1] * (1 + nt),
                                    linkPositions=[[0, 0, 0]] * (1 + nt), linkOrientations=[[0, 0, 0, 1]] * (1 + nt),
                                    linkInertialFramePositions=[[(L.SHAFT_X0 + L.SHAFT_L / 2) * S, 0, 0]] + [[0, 0, 0]] * nt,
                                    linkInertialFrameOrientations=[[0, 0, 0, 1]] * (1 + nt),
                                    linkParentIndices=[0] + [1] * nt,
                                    linkJointTypes=[p.JOINT_REVOLUTE] + [p.JOINT_FIXED] * nt,
                                    linkJointAxis=[[1, 0, 0]] * (1 + nt))
            p.changeDynamics(bid, 0, localInertiaDiagonal=[13.0, 90.0, 90.0], lateralFriction=0.25, linearDamping=0.0, angularDamping=0.0)
            for j in range(1, nt + 1):
                p.changeDynamics(bid, j, localInertiaDiagonal=[TOOTH_LINK_I] * 3, lateralFriction=0.25)
                self.names[(bid, j)] = f"shaft/sprockets {name}"
            p.setJointMotorControl2(bid, 0, p.VELOCITY_CONTROL, targetVelocity=0, force=0)
            if top:
                c = p.createConstraint(bid, -1, -1, -1, p.JOINT_PRISMATIC, [0, 0, 1], [0, 0, 0], [0, y * S, z * S])
                p.changeConstraint(c, maxForce=1e7)
                p.changeDynamics(bid, -1, linearDamping=0.95, angularDamping=0.95, localInertiaDiagonal=[1, 1, 1])
            self.corner_ids[name] = bid
            self.corner_nlinks = 1 + nt
            self.names[(bid, 0)] = f"shaft/sprockets {name}"
            self.names[(bid, -1)] = f"bearing {name}"

    # ------------------------------------------------------------ the loop as one articulated body
    def _link_frames(self, back: bool):
        """Frame of link i: origin at pin i, u along the chain, w inward, x front->back."""
        out = []
        pins = L.chain_pins()
        for i in range(N_LINKS):
            F = L.carriage_frame(i).copy()
            F[:3, 3] = (CHAIN_L if back else 0.0, pins[i][0], pins[i][1])
            out.append(F)
        return out

    def _carriage_shapes(self):
        sh = []
        w0, w1 = CAR_W0 - CAR_T, CAR_W0
        xa, xb = -8.0, CHAIN_L + 8.0
        wx0, wx1 = WIN_X
        sh.append(self._box((CAR_W / 2, CAR_T / 2, (wx0 - xa) / 2), (0, (w0 + w1) / 2, (xa + wx0) / 2)))
        sh.append(self._box((CAR_W / 2, CAR_T / 2, (xb - wx1) / 2), (0, (w0 + w1) / 2, (wx1 + xb) / 2)))
        for su in (-1, 1):
            sh.append(self._box(((CAR_W / 2 - WIN_U) / 2, CAR_T / 2, (wx1 - wx0) / 2),
                                (su * (WIN_U + (CAR_W / 2 - WIN_U) / 2), (w0 + w1) / 2, (wx0 + wx1) / 2)))
        for x0, x1 in ((CAR_X0, xa), (xb, CAR_X1)):
            sh.append(self._box((TONGUE_W / 2, CAR_T / 2, (x1 - x0) / 2), (0, (w0 + w1) / 2, (x0 + x1) / 2)))
        rw, rh = RIB
        lug_top = HINGE_W + 6.0
        m = HULL_MARGIN_MM
        for su in (-1, 1):
            sh.append(self._box((rw / 2, rh / 2, (CHAIN_L - 34) / 2), (su * (CAR_W / 2 - rw / 2), w1 + rh / 2, CHAIN_L / 2)))
            # hinge lug, chamfered to |u| + w <= INNER_CORNER like the printed part (eroded by the hull margin)
            u_in, u_out = LUG_U + m, LUG_U + LUG_T - m
            prof = [(u_in, w1 + m), (u_out, w1 + m), (u_out, INNER_CORNER - u_out - m), (INNER_CORNER - lug_top - m, lug_top - m),
                    (u_in, lug_top - m)]
            verts = [(su * u, w, HINGE_X - 8.0 + m) for u, w in prof] + [(su * u, w, HINGE_X + 8.0 - m) for u, w in prof]
            sh.append(self._mesh(verts))
        return sh

    def _module_shapes(self):
        """Sam's plate + auger + cap, in Sam's frame (hinge axis = y, auger along x at z = 0)."""
        sh = [self._box((52.0, 25.0, 8.3), (46.9, 0, -9.7)), self._box((5.0, 25.0, 4.0), (0.0, 0, -4.0)),
              self._cyl(12.5, AUGER_LEN, (AUGER_Z0_XS + AUGER_LEN / 2, 0, 0)),
              self._cyl(GEAR_R, 10.0, (AUGER_Z0_XS + 83.3, 0, 0)),
              self._cyl(14.5, 27.7, (AUGER_Z0_XS + AUGER_LEN - 11.85, 0, 0))]     # the cap screws on over the last 25.7 mm
        for xr in (33.8, 73.7, 93.8):
            sh.append(self._cyl(14.55, 10.0, (xr, 0, 0)))
        return sh

    def _build_loop(self):
        """Two rigid chains (one articulated body each, 104 links, closed by a
        point-constraint hinge) and 13 carriage bodies (carriage base +
        module on a limited revolute joint) bolted to both chains with
        fixed constraints. PyBullet caps a body at 127 links, so this is the
        split with the fewest soft joints."""
        cl = L.carriage_links()
        inner_shapes = [self._cyl(BUSH_D / 2, W_IN, (0, 0, 0), axis="z"), self._cyl(BUSH_D / 2, W_IN, (P, 0, 0), axis="z"),
                        self._box((P / 2 + PLATE_H / 2, PLATE_H / 2, PLATE_T / 2), (P / 2, 0, (W_IN + PLATE_T) / 2)),
                        self._box((P / 2 + PLATE_H / 2, PLATE_H / 2, PLATE_T / 2), (P / 2, 0, -(W_IN + PLATE_T) / 2))]
        outer_shapes = [self._box((P / 2 + PLATE_H / 2, PLATE_H / 2, PLATE_T / 2), (P / 2, 0, (OUTER_GAP + PLATE_T) / 2)),
                        self._box((P / 2 + PLATE_H / 2, PLATE_H / 2, PLATE_T / 2), (P / 2, 0, -(OUTER_GAP + PLATE_T) / 2))]
        self.col_inner, self.col_outer = self._compound(inner_shapes), self._compound(outer_shapes)
        self.link_com = np.array([P / 2 * S, 0.0, 0.0])
        self.I_in, self.I_out = [1.5e-4, 3e-4, 3e-4], [2e-4, 4e-4, 4e-4]
        self.chain = {False: self._build_chain(False), True: self._build_chain(True)}
        self._build_carriages()

    def _build_chain(self, back: bool) -> int:
        fr = self._link_frames(back)
        cl = set(L.carriage_links())
        masses, cols, poss, orns, parents = [], [], [], [], []
        for i in range(1, N_LINKS):
            inner = i % 2 == 1
            rel = np.linalg.inv(fr[i - 1]) @ fr[i]
            masses.append(0.0033 if inner else (0.0051 if i in cl else 0.0042))
            cols.append(self.col_inner if inner else self.col_outer)
            poss.append((rel[:3, 3] * S).tolist())
            orns.append(quat_from_R(rel[:3, :3]))
            parents.append(i - 1)                      # 0 = base (link 0), k = link index k-1
        n = len(masses)
        bid = p.createMultiBody(baseMass=0.0042, baseCollisionShapeIndex=self.col_outer,
                                basePosition=(fr[0][:3, 3] * S).tolist(), baseOrientation=quat_from_R(fr[0][:3, :3]),
                                baseInertialFramePosition=self.link_com.tolist(),
                                linkMasses=masses, linkCollisionShapeIndices=cols, linkVisualShapeIndices=[-1] * n,
                                linkPositions=poss, linkOrientations=orns, linkInertialFramePositions=[self.link_com.tolist()] * n,
                                linkInertialFrameOrientations=[[0, 0, 0, 1]] * n, linkParentIndices=parents,
                                linkJointTypes=[p.JOINT_REVOLUTE] * n, linkJointAxis=[[0, 0, 1]] * n)
        assert p.getNumJoints(bid) == n
        kind = "back" if back else "front"
        for i in range(N_LINKS):
            idx = i - 1
            self.pb_index[(kind, i)] = idx
            p.changeDynamics(bid, idx, localInertiaDiagonal=self.I_in if i % 2 else self.I_out, lateralFriction=0.25,
                             linearDamping=0.01, angularDamping=0.01, jointDamping=0.0005)
            self.names[(bid, idx)] = f"{kind} link {i}"
        for dz in (-0.4, 0.4):                         # close the loop: pin 0 between link 103 and link 0
            c = p.createConstraint(bid, N_LINKS - 2, bid, -1, p.JOINT_POINT2POINT, [0, 0, 0], [P / 2 * S, 0, dz], [-P / 2 * S, 0, dz])
            p.changeConstraint(c, maxForce=1e7, erp=self.erp)
            self.closures.append(c)
        for i in range(8, N_LINKS, 16):
            self.sensors.append((bid, i - 1, back))
            p.enableJointForceTorqueSensor(bid, i - 1, 1)
        return bid

    def _build_carriages(self):
        col_car, col_mod = self._compound(self._carriage_shapes()), self._compound(self._module_shapes())
        m_plate, m_auger, m_cap = 0.0345 + 0.0092 + 0.0035, 0.0662, 0.0054   # plate + steel armature tab + pins/e-clips/screws
        m_salt = self.salt_g / 1000.0
        m_mod = m_plate + m_auger + m_cap + m_salt
        com_x = (m_plate * 52.2 + (m_auger + m_salt) * (103.0 + AUGER_Z0_XS) + m_cap * 262.0) / m_mod
        com_z = (m_plate * -11.3) / m_mod
        self.mod_com = np.array([com_x * S, 0.0, com_z * S])
        self.car_com = np.array([0.0, -0.74, 16.25])
        Lcm = AUGER_LEN * S
        I_long = m_mod * Lcm ** 2 / 12 + m_mod * (com_x * S - Lcm / 2 - 0.04) ** 2
        I_mod = [0.5 * m_mod * 1.25 ** 2, I_long, I_long]
        self.car_ids = []
        rel = L.SAM_IN_CARRIAGE
        for k, li in enumerate(L.carriage_links()):
            C = L.carriage_frame(li)
            bid = p.createMultiBody(baseMass=0.099, baseCollisionShapeIndex=col_car, basePosition=(C[:3, 3] * S).tolist(),
                                    baseOrientation=quat_from_R(C[:3, :3]), baseInertialFramePosition=self.car_com.tolist(),
                                    linkMasses=[m_mod], linkCollisionShapeIndices=[col_mod], linkVisualShapeIndices=[-1],
                                    linkPositions=[(rel[:3, 3] * S).tolist()], linkOrientations=[quat_from_R(rel[:3, :3])],
                                    linkInertialFramePositions=[self.mod_com.tolist()], linkInertialFrameOrientations=[[0, 0, 0, 1]],
                                    linkParentIndices=[0], linkJointTypes=[p.JOINT_REVOLUTE], linkJointAxis=[[0, 1, 0]])
            p.changeDynamics(bid, -1, localInertiaDiagonal=[1.0, 1.0, 0.05], lateralFriction=0.3, linearDamping=0.01, angularDamping=0.01)
            p.changeDynamics(bid, 0, localInertiaDiagonal=I_mod, lateralFriction=0.3, linearDamping=0.01, angularDamping=0.01,
                             jointLowerLimit=-math.radians(100), jointUpperLimit=0.0, jointLimitForce=1e5, jointDamping=0.001)
            p.setJointMotorControl2(bid, 0, p.POSITION_CONTROL, targetPosition=0.0, force=0.0)
            self.car_ids.append(bid)
            self.names[(bid, -1)] = f"carriage {k + 1}"
            self.names[(bid, 0)] = f"module {k + 1}"
            # bolt the carriage to its A-1 link on both chains: rigid to the front link, a ball joint at the back
            # tab (one M3 through a 1.3 mm tab is a pin, not a moment connection; this also stops the two rigid
            # chains from fighting each other through 13 over-constrained carriages)
            for back, dx in ((False, 0.0), (True, CHAIN_L)):
                cb, idx = self.chain[back], self.pb_index[("back" if back else "front", li)]
                parent_pos = (np.array([-P / 2 * S, 0.0, dx * S]) - self.car_com).tolist()
                if back:
                    c = p.createConstraint(bid, -1, cb, idx, p.JOINT_POINT2POINT, [0, 0, 0], parent_pos, (-self.link_com).tolist())
                else:
                    c = p.createConstraint(bid, -1, cb, idx, p.JOINT_FIXED, [0, 0, 0], parent_pos, (-self.link_com).tolist(),
                                           [0, 0, 0, 1], [0, 0, 0, 1])
                p.changeConstraint(c, maxForce=1e7, erp=self.erp)
                self.bolts.append(c)

    def _set_filters(self):
        for name, bid in self.corner_ids.items():
            for j in range(self.corner_nlinks):
                p.setCollisionFilterGroupMask(bid, j, GRP_SPROCKET, GRP_BUSH | GRP_MODULE | GRP_CARRIAGE)
        for sid in self.static_ids:
            p.setCollisionFilterGroupMask(sid, -1, GRP_STATIC, GRP_BUSH | GRP_MODULE | GRP_CARRIAGE)
        for back in (False, True):
            bid = self.chain[back]
            for i in range(N_LINKS):
                if i % 2 == 1:
                    p.setCollisionFilterGroupMask(bid, i - 1, GRP_BUSH, GRP_SPROCKET | GRP_STATIC)
                else:
                    p.setCollisionFilterGroupMask(bid, i - 1, GRP_PLATE, 0)
        for bid in self.car_ids:
            p.setCollisionFilterGroupMask(bid, -1, GRP_CARRIAGE, GRP_MODULE | GRP_STATIC | GRP_SPROCKET | GRP_CARRIAGE)
            p.setCollisionFilterGroupMask(bid, 0, GRP_MODULE, GRP_MODULE | GRP_STATIC | GRP_SPROCKET | GRP_CARRIAGE)
            p.setCollisionFilterPair(bid, bid, -1, 0, 0)

    # ------------------------------------------------------------ running
    def hinge_angle(self, k: int) -> float:
        """Tilt of module k, degrees, positive = cap end lifted into the loop."""
        return -math.degrees(p.getJointState(self.car_ids[k], 0)[0])

    def apply_hooks(self):
        overlap_deg = math.degrees(math.atan2(SNAP_LAP, SNAP_X - HINGE_X))
        tau_hold = (50.0 if self.hooks_locked else self.hook_N) * NEWTON * (SNAP_X - HINGE_X) * S
        for k in range(N_MODULES):
            bid = self.car_ids[k]
            th = self.hinge_angle(k)
            self.module_max_tilt[k] = max(self.module_max_tilt[k], th)
            if self.module_open[k]:
                continue
            if th > overlap_deg and not self.hooks_locked:
                self.module_open[k] = True
                p.setJointMotorControl2(bid, 0, p.POSITION_CONTROL, targetPosition=0.0, force=0.0)
                continue
            p.setJointMotorControl2(bid, 0, p.POSITION_CONTROL, targetPosition=0.0, force=tau_hold, positionGain=0.5, velocityGain=0.1)

    def drive(self, omega: float, torque_Nm: float = 12.0):
        for name, cid in self.corner_ids.items():
            if name.startswith("T"):
                p.applyExternalForce(cid, -1, [0, 0, 2 * self.tension_N * NEWTON], [(L.SHAFT_X0 + L.SHAFT_L / 2) * S, 0, 0], p.LINK_FRAME)
        p.setJointMotorControl2(self.corner_ids[L.DRIVE], 0, p.VELOCITY_CONTROL, targetVelocity=omega, force=torque_Nm * NM)
        for name, cid in self.corner_ids.items():
            if name != L.DRIVE:
                p.setJointMotorControl2(cid, 0, p.VELOCITY_CONTROL, targetVelocity=0, force=self.bearing_drag * NM)

    def settle(self, seconds: float = 0.6):
        for _ in range(int(seconds / self.dt)):
            self.drive(0.0, 12.0)
            self.apply_hooks()
            p.stepSimulation()
        self.hooks_locked = False
        self.module_max_tilt = [0.0] * N_MODULES

    def top_shaft_lift_mm(self) -> list:
        return [round(p.getBasePositionAndOrientation(self.corner_ids[n])[0][2] / S - z, 3)
                for n, (y, z) in L.CORNERS.items() if n.startswith("T")]

    def drive_torque(self) -> float:
        return p.getJointState(self.corner_ids[L.DRIVE], 0)[3] / NM

    def chain_speed(self) -> float:
        return p.getJointState(self.corner_ids[L.DRIVE], 0)[1] * R

    def carriage_pose(self, k: int) -> np.ndarray:
        pos, orn = p.getBasePositionAndOrientation(self.car_ids[k])
        return M_of(pos, orn, self.car_com)

    def tensions(self, back=None) -> list:
        """Chain tension (N) at the sensor pins: the joint reaction force in the link plane."""
        out = []
        for bid, idx, b in self.sensors:
            if back is not None and b != back:
                continue
            f = p.getJointState(bid, idx)[2]
            out.append(float(np.hypot(f[0], f[1])) / NEWTON)
        return out

    def closure_forces(self) -> list:
        return [float(np.linalg.norm(p.getConstraintState(c))) / NEWTON for c in self.closures + self.bolts]

    def contacts(self):
        """Clash events: modules/carriages against statics, sprockets or other modules/carriages, deeper than 0.2 mm."""
        hits = []
        for cp in p.getContactPoints():
            a, la, b, lb, dist = cp[1], cp[3], cp[2], cp[4], cp[8]
            if dist > -0.02:
                continue
            na, nb = self.names.get((a, la), f"body {a}/{la}"), self.names.get((b, lb), f"body {b}/{lb}")
            if not (na.startswith(("module", "carriage")) or nb.startswith(("module", "carriage"))):
                continue
            if na.startswith(("front", "back")) or nb.startswith(("front", "back")):
                continue
            hits.append((na, nb, round(-dist / S, 2)))
        return hits

    def poses(self) -> dict:
        out = {}
        for back, kind in ((False, "front"), (True, "back")):
            bid = self.chain[back]
            arr = np.zeros((N_LINKS, 4, 4))
            for i in range(N_LINKS):
                if i == 0:
                    pos, orn = p.getBasePositionAndOrientation(bid)
                    arr[i] = M_of(pos, orn, self.link_com)
                else:
                    ls = p.getLinkState(bid, i - 1, computeForwardKinematics=1)
                    arr[i] = M_of(ls[4], ls[5])
                arr[i][:3, 3] += arr[i][:3, :3] @ np.array([P / 2, 0, 0])    # the renderer wants the link midpoint
            out["chain_" + kind] = arr
        cars, mods = np.zeros((N_MODULES, 4, 4)), np.zeros((N_MODULES, 4, 4))
        for k, bid in enumerate(self.car_ids):
            cars[k] = self.carriage_pose(k)
            ls = p.getLinkState(bid, 0, computeForwardKinematics=1)
            mods[k] = M_of(ls[4], ls[5])
        out["carriages"], out["modules"] = cars, mods
        out["corner_angles"] = np.array([p.getJointState(self.corner_ids[n], 0)[0] for n in L.CORNERS])
        out["top_lift"] = np.array(self.top_shaft_lift_mm())
        return out


def speed_profile(kind: str, v_mm_s: float, moves: int, accel: float = 250.0, dwell: float = 1.0, links: float | None = None):
    """Chain speed (mm/s) vs time: trapezoids of one module (index), one lap, or `links` links, with dwells."""
    dist = (links if links else (MODULE_LINKS if kind == "index" else N_LINKS)) * P
    t_acc = v_mm_s / accel
    d_acc = 0.5 * accel * t_acc ** 2
    if 2 * d_acc > dist:
        t_acc = math.sqrt(dist / accel)
        d_acc = dist / 2
        v_mm_s = accel * t_acc
    t_cruise = (dist - 2 * d_acc) / v_mm_s
    seg = 2 * t_acc + t_cruise
    segs = []
    t0 = dwell * 0.5
    for _ in range(moves):
        segs.append((t0, t0 + t_acc, t0 + t_acc + t_cruise, t0 + seg))
        t0 += seg + dwell
    total = t0 + dwell * 0.5

    def v(t: float) -> float:
        for a, b, c, d in segs:
            if a <= t < b:
                return accel * (t - a)
            if b <= t < c:
                return v_mm_s
            if c <= t < d:
                return v_mm_s - accel * (t - c)
        return 0.0

    return v, total, segs


def run(args) -> dict:
    sim = Carousel(hook_N=args.hook, salt_g=args.salt, dt=args.dt, tension_N=args.tension, erp=args.erp, iters=args.iters,
                   sliders=args.sliders)
    sim.settle()
    out_dir = HERE / "results" / args.run
    out_dir.mkdir(parents=True, exist_ok=True)
    v_of_t, total, segs = speed_profile("index" if args.kind == "index" else "lap", args.speed, args.moves, links=args.links)
    estop_at = None
    if args.kind == "estop":
        estop_at = segs[0][1] + 0.5 * (segs[0][2] - segs[0][1])
        total = estop_at + 3.0
    n_steps = int(total / args.dt)
    frame_every = max(1, int(round(1.0 / (args.fps * args.dt))))
    log_every = max(1, int(round(0.01 / args.dt)))
    rows, frames, clashes = [], [], []
    y_cmd = 0.0
    t_wall = time.time()
    coasting = False
    c1_y0 = sim.carriage_pose(0)[1, 3]
    for n in range(n_steps + 1):
        t = n * args.dt
        if estop_at is not None and t >= estop_at:
            coasting = True
        v = 0.0 if coasting else args.direction * v_of_t(t)
        y_cmd += v * args.dt
        sim.drive(v / R, torque_Nm=0.0 if coasting else 12.0)
        sim.apply_hooks()
        p.stepSimulation()
        if n % log_every == 0:
            tens = sim.tensions()
            tilts = [sim.hinge_angle(k) for k in range(N_MODULES)]
            c1 = sim.carriage_pose(0)
            rows.append(dict(t=round(t, 3), v_cmd=round(v, 2), v_chain=round(sim.chain_speed(), 2), torque_Nm=round(sim.drive_torque(), 4),
                             tension_max_N=round(max(tens), 2), tension_mean_N=round(float(np.mean(tens)), 2),
                             closure_max_N=round(max(sim.closure_forces()), 2),
                             tilt_max_deg=round(max(tilts), 3), tilt_min_deg=round(min(tilts), 3), open_modules=sum(sim.module_open),
                             c1_travel_mm=round(c1[1, 3] - c1_y0, 3), chain_cmd_mm=round(y_cmd, 3),
                             c1_x_mm=round(c1[0, 3], 3), c1_z_mm=round(c1[2, 3], 3),
                             top_lift_mm=round(float(np.mean(sim.top_shaft_lift_mm())), 3)))
            for h in sim.contacts():
                clashes.append((round(t, 3), *h))
        if n % frame_every == 0:
            frames.append(sim.poses())
    wall = time.time() - t_wall
    packed = {k: np.stack([f[k] for f in frames]) for k in frames[0]}
    packed["t"] = np.arange(len(frames)) * frame_every * args.dt
    np.savez_compressed(out_dir / "poses.npz", **packed)
    with (out_dir / "timeseries.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    tq = [r["torque_Nm"] for r in rows]
    cmd_total = rows[-1]["chain_cmd_mm"]
    metrics = dict(run=args.run, kind=args.kind, speed_mm_s=args.speed, moves=args.moves, hook_N=args.hook, salt_g=args.salt,
                   tension_N=args.tension, dt=args.dt, sim_time_s=round(total, 2), wall_s=round(wall, 1), steps=n_steps,
                   bodies=p.getNumBodies(), constraints=p.getNumConstraints(),
                   drive_torque_peak_Nm=round(max(abs(x) for x in tq), 3),
                   drive_torque_rms_Nm=round(float(np.sqrt(np.mean(np.square(tq)))), 3),
                   drive_torque_hold_Nm=round(abs(tq[-1]), 3),
                   tension_peak_N=round(max(r["tension_max_N"] for r in rows), 2),
                   tension_mean_N=round(float(np.mean([r["tension_mean_N"] for r in rows])), 2),
                   closure_peak_N=round(max(r["closure_max_N"] for r in rows), 2),
                   top_shaft_lift_mm=sim.top_shaft_lift_mm(),
                   chain_commanded_mm=round(cmd_total, 2),
                   carriage1_travel_mm=round(rows[-1]["c1_travel_mm"], 2),
                   carriage1_position_error_mm=round(rows[-1]["c1_travel_mm"] - cmd_total, 3) if args.kind == "index" else None,
                   run_direction=args.direction, sliders=bool(args.sliders),
                   carriage1_x_drift_mm=round(max(abs(r["c1_x_mm"] - rows[0]["c1_x_mm"]) for r in rows), 3),
                   speed_error_rms_mm_s=round(float(np.sqrt(np.mean([(r["v_chain"] - r["v_cmd"]) ** 2 for r in rows]))), 2),
                   module_max_tilt_deg=[round(x, 3) for x in sim.module_max_tilt],
                   modules_opened=[k + 1 for k, o in enumerate(sim.module_open) if o],
                   clash_events=len(clashes), clashes=sorted({(a, b) for _, a, b, _ in clashes}),
                   clash_max_mm=max([c[3] for c in clashes], default=0.0),
                   final_corner_angles_deg=[round(math.degrees(a), 2) for a in frames[-1]["corner_angles"]])
    (out_dir / "metrics.json").write_text(json.dumps(metrics, indent=1))
    print(json.dumps({k: v for k, v in metrics.items() if k not in ("module_max_tilt_deg", "clashes")}, indent=None))
    print("clashes:", metrics["clashes"][:10])
    p.disconnect()
    return metrics


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("kind", choices=["index", "lap", "estop"])
    ap.add_argument("--speed", type=float, default=50.0, help="chain speed, mm/s")
    ap.add_argument("--moves", type=int, default=1)
    ap.add_argument("--hook", type=float, default=10.0, help="snap-hook holding force, N (both hooks together)")
    ap.add_argument("--salt", type=float, default=100.0, help="powder mass per module, g")
    ap.add_argument("--tension", type=float, default=80.0, help="chain pretension per chain, N (test plan: 3-4 mm under 5 N side push on a 228 mm run = about 80 N)")
    ap.add_argument("--dt", type=float, default=1e-3)
    ap.add_argument("--erp", type=float, default=0.2)
    ap.add_argument("--iters", type=int, default=150)
    ap.add_argument("--fps", type=float, default=30.0)
    ap.add_argument("--sliders", action="store_true", help="add the Oct 16 slider rails under the station carriage")
    ap.add_argument("--direction", type=int, default=RUN_DIRECTION, help="+1: bottom run toward +y; -1 (default): toward -y")
    ap.add_argument("--links", type=float, default=None, help="move this many links instead of one module / one lap")
    ap.add_argument("--run", default=None)
    a = ap.parse_args()
    if a.run is None:
        a.run = f"{a.kind}_v{int(a.speed)}_h{int(a.hook)}_t{int(a.tension)}"
    run(a)


if __name__ == "__main__":
    main()
