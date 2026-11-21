"""The dosing station of chain carousel v3 and v4 (#185 at 45e9740): kinematic dock, guide cradle, clevis and its
bracket, the latch rail (v4: latch rail + tube rest), the hold-downs.

    python cases/station.py            # every case
    python cases/station.py hertz      # the dock's statics and contact stresses only (seconds)

Frames: Sam's studio frame at the station (x along the auger from the hinge axis, y along the hinge axis, z away from
the plate on the auger's side), docked; the electronics carriage (EC) STEPs are drawn DOCK_RISE (v3 +0.9, v4 -0.9 mm)
off their docked position. v3: Sam's z is the world's up at the station (the module rides on top of its carriage on the
bottom run); v4: Sam's z is the world's down (the module hangs under the bottom run, the EC docks from below).

How the station carries load (both designs): the module is hinged to its carriage; the EC docks on the plate through
three ball contacts (cone A, vee B along y, flat C) held shut by magnets; the P16 pushes the EC at a pin in a 2 mm
slotted clevis. Docked, EC + module are one body on two supports, the hinge pins and the P16, so the P16's force
follows from moments about the hinge, and the six contact-force components then follow from the EC's own equilibrium
(it is held only by the P16 and the three contacts). The contact forces go into the FEA of the EC as tractions; the EC is
held at its clevis pin, whose reaction is checked against the P16 force from the statics.
"""
from __future__ import annotations

import importlib.util
import json
import math
import sys
import time
from functools import lru_cache
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import fem  # noqa: E402
import loads as LD  # noqa: E402
import materials as MAT  # noqa: E402
from cases import common  # noqa: E402

MODULE = "station"
OUT = common.OUT / MODULE
GEO = Path("/tmp/station")                    # geo_dump.py output (station frames from each design's layout)

# ------------------------------------------------------------------------------------------------ loads (N, kg, mm)
# Module masses from the exported STEP volumes (b882c33) at 1.27 g/cm^3 (PETG, solid) and 7.85 (steel), plus v2's
# sim table for what is not drawn (100 g powder, 3.5 g hinge pins):
#   v3: plate 26.46 cm^3 33.6 g, auger 53.36 cm^3 67.8 g, cap 5.5 g, armature 1.32 cm^3 steel 10.4 g, door housing,
#       shutter and spring 2.9 g, two 1/4 in balls 2.1 g -> 0.226 kg
#   v4: plate 27.98 cm^3 35.5 g, no armature, the C pad 0.5 g -> 0.218 kg
M_MODULE = {"v3": 0.226, "v4": 0.218}
COM_MODULE = (107.5, 0.0, -4.4)               # loads.V2_MODULE_COM_SAM (the v3/v4 changes move it < 1 mm)
# EC: loads.ECAR_KG (0.305 kg, Sam's carriage 18.6 cm^3 printed + NEMA 11, solenoid, electromagnet, pinion, wiring)
# + the printed additions (v3: EC STEP 32.3 cm^3 -> +13.7 cm^3, 17 g; v4: 38.2 cm^3 -> +19.6 cm^3, 25 g) + steel balls,
# dowels and seat magnets (v3 8 g, v4 10 g); v4 has no electromagnet (about 30 g less).
M_EC = {"v3": 0.33, "v4": 0.31}
COM_EC_DRAWN = {"v3": (54.0, 0.0, -36.0), "v4": (54.0, 0.0, 36.0)}   # v2's (52, -33.6) moved by the base; v4 mirrored
F_EM = LD.MAGNET_DESIGN_N                     # dock electromagnet (v3 only) at its 0.15 mm design gap: 10.6 N (24.5 at 0)
F_EM_RANGE = (5.0, LD.MAGNET_HOLD_N)
# Seat magnets (K&J D44-N52, 1/4 x 1/4 in) on a 1/4 in chrome-steel ball: magnet_ball_pull() below (a high-permeability
# sphere, M = 3H, in the cylinder magnet's field from its surface current, Br 1.45 T): 7.5 N touching, 4.3 N at 0.6 mm,
# 3.0 N at 1.0 mm. An estimate (+-50 %); K&J's own figure for this magnet on a thick plate is several times higher.
GAP_A = 0.6                                   # KC_MAG_GAP: cone magnet's face under the plate ball
GAP_B = 2.4                                   # vee magnet's face under its ball (it sits below the two dowels)
F_C_MAGNET_V4 = 2.0                           # v4: magnet behind ball C pulling the plate's steel washer through the ball (guess)
F_SEP_STALL = LD.GEAR_SEP_STALL_N             # 3.7 N separating force at the 20T:44T mesh, NEMA 11 at stall (v2 station sim)
F_T_STALL = F_SEP_STALL / math.tan(math.radians(20.0))   # the tangential force that goes with it (20 deg teeth): 10.2 N
MESH_V3 = (83.3, 0.0, -22.25)                 # pitch point: pinion (x 78.3-88.3, axis z -32.25 docked) under the gear (axis z 0)
MESH_V4 = (83.3, 0.0, 22.25)
P16_STALL = LD.P16_MAX_N                      # 50 N
P16_BACKDRIVE = LD.P16_BACKDRIVE_N            # 75 N
LATCH_SPRING_OPEN = 2.0                       # params LATCH_SPRING: 0.25 N/mm, 2.0 N open
RAMP_DEG = 25.0
CHAIN_PULL_JAM = LD.NEMA34_HOLD_NM * 1000.0 / (9.525 / (2 * math.sin(math.pi / 32)))   # 12 N*m on the 32T pitch radius: 247 N

E_STEEL, NU_STEEL = 205000.0, 0.29
E_PETG, NU_PETG = MAT.get("PETG").E, MAT.get("PETG").nu
E_PETG_CREEP = MAT.get("PETG_CREEP").E
R_BALL = 6.35 / 2
R_DOWEL = 3.175 / 2
# contact allowables (first subsurface yield, Hertz): p0 = 1.60 Y (point) / 1.67 Y (line), von Mises
Y_PETG_COMP = 44.0                            # compressive yield ~1.3 x the 34 MPa XY tensile strength (Bambu PETG HF TDS)
P_ALLOW = {"petg_line": 1.67 * Y_PETG_COMP,
           "hardened": 4000.0,                # 52100 ball / 58-62 HRC dowel: ISO 76 static limit for hardened bearing steel
           "mild_steel": 1.60 * 180.0,        # low-carbon armature (materials.STEEL_LC yield 180)
           "case_hardened": 1.60 * 600.0}     # case-hardened washer, a conservative core-and-case figure

DES = {"v3": "chain-carousel-v3", "v4": "chain-carousel-v4"}


def params(v: str):
    name = f"params_{v}"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, fem.CAD / DES[v] / "params.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def geo(v: str) -> dict:
    p = GEO / f"geo_{v}.json"
    if not p.exists():
        import subprocess
        GEO.mkdir(exist_ok=True)
        subprocess.run([sys.executable, str(Path(__file__).with_name("station_geo_dump.py")), str(p)], cwd=fem.CAD / DES[v], check=True)
    return json.loads(p.read_text())


# ------------------------------------------------------------------------------------------------ magnets
@lru_cache(None)
def magnet_ball_pull(gap: float, Br: float = 1.45, a: float = 3.175, h: float = 6.35, R: float = R_BALL) -> float:
    """Pull (N) of a cylinder magnet (radius a, height h, face at z = 0) on a high-permeability ball of radius R whose
    lowest point is `gap` above the face: F = 3/(2 mu0) * integral of d(B^2)/dz over the ball (M = 3H)."""
    from scipy.special import ellipe, ellipk

    def B(rho, z, nz=60):
        Bz = np.zeros_like(rho)
        Bp = np.zeros_like(rho)
        dz = h / nz
        for z0 in (np.arange(nz) + 0.5) * dz - h:
            zz = z - z0
            rr = np.maximum(rho, 1e-9)
            q = (a + rr) ** 2 + zz ** 2
            k2 = 4 * a * rr / q
            K, E = ellipk(k2), ellipe(k2)
            d = (a - rr) ** 2 + zz ** 2
            c = Br * dz / (2 * np.pi) / np.sqrt(q)
            Bz += c * (K + (a * a - rr * rr - zz * zz) / d * E)
            Bp += c * zz / rr * (-K + (a * a + rr * rr + zz * zz) / d * E)
        return Bz, Bp
    n = 28
    xs = (np.arange(n) + 0.5) / n * 2 * R - R
    X, Y, Z = np.meshgrid(xs, xs, xs, indexing="ij")
    ins = X ** 2 + Y ** 2 + Z ** 2 <= R * R
    rho, z = np.hypot(X, Y)[ins], Z[ins] + gap + R
    e = 1e-3
    b1, p1 = B(rho, z + e)
    b0, p0 = B(rho, z - e)
    dB2 = ((b1 ** 2 + p1 ** 2) - (b0 ** 2 + p0 ** 2)) / (2 * e)
    mu0 = 4e-7 * math.pi
    return float(-3 / (2 * mu0) * dB2.sum() * (2 * R / n) ** 3 * 1e-6)


# ------------------------------------------------------------------------------------------------ dock statics
VARIANT: dict = {}                              # design-change variants: set by variants() (B=(x, y), C=(x, y), gap_b, pin_x)


def dock_geometry(v: str) -> dict:
    """Docked Sam-frame positions of everything that loads the EC, and which way 'toward the plate' is."""
    P = params(v)
    G = _dock_geometry(v, P)
    var = VARIANT.get(v, {})
    for k in ("B", "C"):
        if k in var:
            G[k] = np.array([var[k][0], var[k][1], G[k][2]])
    if "B" in var:                                   # the vee's magnet moves with it
        m = list(G["mags"][1])
        m[0] = (var["B"][0], var["B"][1], m[0][2])
        G["mags"][1] = tuple(m)
    if "C" in var and v == "v4":
        m = list(G["mags"][2])
        m[0] = (var["C"][0], var["C"][1], m[0][2])
        G["mags"][2] = tuple(m)
    if "gap_b" in var:
        m = list(G["mags"][1])
        m[1] = magnet_ball_pull(var["gap_b"])
        G["mags"][1] = tuple(m)
    if "pin_x" in var:
        G["pin"] = np.array([var["pin_x"], G["pin"][1], G["pin"][2]])
    # the vee's groove points at the cone (Kelvin clamp): it reacts across the groove (in the plate's plane) and along z
    g = G["A"][:2] - G["B"][:2]
    g = g / np.linalg.norm(g)
    G["vee_n"] = np.array([-g[1], g[0], 0.0])
    return G


def _dock_geometry(v: str, P) -> dict:
    if v == "v3":
        s = -1.0                                   # the plate is at +z of the EC: contact forces on the EC point -z
        zball = P.KC_BALL_Z
        A = (P.KC_A[0], P.KC_A[1], zball)
        B = (P.KC_B[0], P.KC_B[1], zball)
        C = (P.KC_C[0], P.KC_C[1], -20.0)          # ball C's top on the armature's underside
        mags = [((P.KC_A[0], P.KC_A[1], zball - R_BALL - GAP_A), magnet_ball_pull(GAP_A)),
                ((P.KC_B[0], P.KC_B[1], zball - R_BALL - GAP_B), magnet_ball_pull(GAP_B)),
                ((P.DOCK_MAG_XY3[0], P.DOCK_MAG_XY3[1], -20.15), F_EM)]
        mesh = MESH_V3
        pin = (P.EC_PIN[0], 0.0, P.EC_PIN[1] + P.DOCK_RISE_V3)
        com = tuple(np.add(COM_EC_DRAWN[v], (0, 0, P.DOCK_RISE_V3)))
        dr = P.DOCK_RISE_V3
    else:
        s = +1.0                                   # plate at -z of the EC: contact forces on the EC point +z
        zball = P.KC4_BALL_Z
        A = (P.KC4_A[0], P.KC4_A[1], zball)
        B = (P.KC4_B[0], P.KC4_B[1], zball)
        C = (P.KC4_C[0], P.KC4_C[1], -13.0)        # ball C's tip on the plate's washer (its face at z -13)
        mags = [((P.KC4_A[0], P.KC4_A[1], zball + R_BALL + GAP_A), magnet_ball_pull(GAP_A)),
                ((P.KC4_B[0], P.KC4_B[1], zball + R_BALL + 2.28), magnet_ball_pull(2.28)),
                ((P.KC4_C[0], P.KC4_C[1], -6.15), F_C_MAGNET_V4)]
        mesh = MESH_V4
        pin = (P.EC_PIN[0], 0.0, -P.EC_PIN[1] + P.DOCK_RISE_V4)
        com = tuple(np.add(COM_EC_DRAWN[v], (0, 0, P.DOCK_RISE_V4)))
        dr = P.DOCK_RISE_V4
    return dict(s=s, A=np.array(A), B=np.array(B), C=np.array(C), mags=mags, mesh=np.array(mesh), pin=np.array(pin),
                com=np.array(com), dr=dr)


def gravity_sam(v: str, tilt: float) -> np.ndarray:
    """World gravity (unit) in the tilted Sam frame at the station."""
    t = math.radians(tilt)
    return np.array([-math.sin(t), 0.0, -math.cos(t) if v == "v3" else math.cos(t)])


def p16_axis_sam(v: str, tilt: float) -> np.ndarray:
    g = geo(v)
    key = f"{float(tilt):.1f}"
    if key not in g:                                # interpolate between the dumped tilts
        ks = sorted(float(k) for k in g if k.replace(".", "").isdigit())
        lo = max(k for k in ks if k <= tilt)
        hi = min(k for k in ks if k >= tilt)
        f = 0 if hi == lo else (tilt - lo) / (hi - lo)
        return (1 - f) * p16_axis_sam(v, lo) + f * p16_axis_sam(v, hi)
    M = np.array(g[key]["sam"])
    B, Pp = np.array(g[key]["B"]), np.array(g[key]["P"])
    u = (Pp - B) / np.linalg.norm(Pp - B)
    return M[:3, :3].T @ u


def cross_y(r, F):
    return r[2] * F[0] - r[0] * F[2]


def dock_forces(v: str, tilt: float, case: str, f_em: float | None = None, ft_sign: float = 1.0, gear_scale: float = 1.0) -> dict:
    """Contact forces ON THE EC from the plate (A: 3 components, B: x and z, C: z), the P16 force and every load on the EC.

    case: 'float' (v3 at tilt 0: the module rests on its carriage, the P16 pin floats mid-slot, the magnets hold the EC up),
          'lift'  (quasi-static lift/tilt: the P16 force from moments about the hinge, gear idle),
          'lift_gear' (as lift, the NEMA 11 at stall: separating + tangential force at the mesh),
          'stall' (the P16 at its 50 N stall into a module that can't move: latch not open, or v4 at the top run)."""
    G = dock_geometry(v)
    s = G["s"]
    g = gravity_sam(v, tilt)
    W_ec = M_EC[v] * LD.G_MS2
    W_m = M_MODULE[v] * LD.G_MS2
    u = p16_axis_sam(v, tilt)
    loads = []                                       # (name, point, force) on the EC
    loads.append(("EC weight", G["com"], W_ec * g))
    mags = list(G["mags"])
    if f_em is not None and v == "v3":
        mags[2] = (mags[2][0], f_em)
    for i, (p, f) in enumerate(mags):
        loads.append((["seat magnet A", "seat magnet B", "electromagnet" if v == "v3" else "C magnet"][i], np.array(p), np.array([0, 0, -s * f])))
    if case.endswith("tap"):                         # solenoid tap: plunger up into the tube, the EC pushed away (3 N, 10 ms)
        P_ = params(v)
        z_sol = (P_.SOL_Z + G["dr"]) if v == "v3" else (-P_.SOL_Z + G["dr"])
        loads.append(("solenoid tap", np.array([P_.SOL_X, 0.0, z_sol]), np.array([0.0, 0.0, s * LD.SOLENOID_TAP_N])))
    if case.endswith("gear"):
        loads.append(("gear mesh", G["mesh"], np.array([0.0, ft_sign * F_T_STALL * gear_scale, s * F_SEP_STALL * gear_scale])))
    if case.startswith("float"):
        Fp = 0.0
    elif case == "stall":
        Fp = P16_STALL
    else:                                            # moments about the hinge (y axis through the origin) of EC + module
        m = cross_y(np.array(COM_MODULE), W_m * g) + cross_y(G["com"], W_ec * g)
        Fp = -m / cross_y(G["pin"], u)
    loads.append(("P16", G["pin"], Fp * u))
    # unknowns: Ax Ay Az, B across its groove, Bz, Cz (forces on the EC at A, B, C)
    pts = [G["A"], G["A"], G["A"], G["B"], G["B"], G["C"]]
    dirs = [np.eye(3)[0], np.eye(3)[1], np.eye(3)[2], G["vee_n"], np.eye(3)[2], np.eye(3)[2]]
    Amat = np.zeros((6, 6))
    for j, (p, d) in enumerate(zip(pts, dirs)):
        Amat[:3, j] = d
        Amat[3:, j] = np.cross(p, d)
    rhs = np.zeros(6)
    for _, p, f in loads:
        rhs[:3] -= f
        rhs[3:] -= np.cross(p, f)
    x = np.linalg.solve(Amat, rhs)
    FA, FC = x[:3], np.array([0.0, 0.0, x[5]])
    FB = x[3] * G["vee_n"] + x[4] * np.eye(3)[2]
    # normal (into the seat) components: compressive is positive (s: the sign of z of a compressive force on the EC)
    nA, nB, nC = s * FA[2], s * FB[2], s * FC[2]
    return dict(v=v, tilt=tilt, case=case, P16_N=float(Fp), FA=FA, FB=FB, FC=FC, nA=float(nA), nB=float(nB), nC=float(nC),
                B_across=float(np.dot(FB, G["vee_n"])),
                latA=float(np.hypot(FA[0], FA[1])), loads=loads, ok=None)


def seated(r: dict, mu: float = 0.0) -> bool:
    """Every ball stays in its seat (rigid balls): normals compressive; the cone's resultant within 45 deg + friction of
    its axis; the vee's resultant (in the x-z plane) within 45 deg + friction of the seat's axis. With friction, the flat
    C also resists yaw about A (mu N_C over C's lever from A), which takes that much of the A-B couple off the vee."""
    if min(r["nA"], r["nB"], r["nC"]) <= 0:
        return False
    lim = math.tan(math.radians(45.0) + math.atan(mu))
    G = dock_geometry(r["v"])
    bx = abs(r["B_across"])
    if mu > 0:
        lever_c = abs(G["C"][0] - G["A"][0])
        bx = max(0.0, bx - mu * r["nC"] * lever_c / abs(G["A"][1] - G["B"][1]))
    return r["latA"] <= lim * r["nA"] and bx <= lim * r["nB"]


def gear_capacity_sign(v: str, tilt: float, case: str, sg: float, mu: float = 0.0) -> float:
    if not seated(dock_forces(v, tilt, case, ft_sign=sg, gear_scale=0.0), mu):
        return 0.0
    lo, hi = 0.0, 10.0
    for _ in range(40):
        mid = 0.5 * (lo + hi)
        if seated(dock_forces(v, tilt, case, ft_sign=sg, gear_scale=mid), mu):
            lo = mid
        else:
            hi = mid
    return lo


def gear_capacity(v: str, tilt: float, case: str, mu: float = 0.0) -> float:
    """Fraction of the NEMA 11's stall mesh load (3.7 N separating, 10.2 N tangential) at which the dock first unseats
    (either direction of the tangential force); > 1: it holds a stalled NEMA 11."""
    best = 10.0
    for sg in (1.0, -1.0):
        lo, hi = 0.0, 10.0
        if not seated(dock_forces(v, tilt, case, ft_sign=sg, gear_scale=0.0), mu):
            return 0.0
        for _ in range(40):
            mid = 0.5 * (lo + hi)
            if seated(dock_forces(v, tilt, case, ft_sign=sg, gear_scale=mid), mu):
                lo = mid
            else:
                hi = mid
        best = min(best, lo)
    return best


def variants() -> dict:
    """The dock with the changes this study proposes, against the design as drawn: the worst B and A normals over the
    tilt sweep (motor idle, and with a solenoid tap), and the NEMA 11 mesh load it holds seated (mu 0.15 at every contact)."""
    global VARIANT
    tilts = {"v3": (0.0, 15.0, 30.0, 45.0), "v4": (0.0, 15.0, 30.0, 50.0)}
    defs = {"v3 as drawn": ("v3", {}),
            "v3, vee magnet 0.6 mm under its ball (as the cone's)": ("v3", {"gap_b": 0.6}),
            "v4 as drawn": ("v4", {}),
            "v4, clevis pin at x 48 (inside the contact triangle)": ("v4", {"pin_x": 48.0}),
            "v4, vee moved to (64, -19.5), its groove toward the cone": ("v4", {"B": (64.0, -19.5)}),
            "v4, vee to (64, -19.5) + magnets at 0.6 mm": ("v4", {"B": (64.0, -19.5), "gap_b": 0.6})}
    out = {}
    for name, (v, var) in defs.items():
        VARIANT = {v: var}
        rows = []
        for t in tilts[v]:
            for c in ("lift", "lift_tap") + (("float", "float_tap") if (v == "v3" and t == 0.0) else ()):
                r = dock_forces(v, t, c)
                rows.append((t, c, r["nA"], r["nB"], r["nC"], bool(seated(r))))
            rows.append((t, "P16 stall", *[dock_forces(v, t, "stall")[k] for k in ("nA", "nB", "nC")], bool(seated(dock_forces(v, t, "stall")))))
        cap = min(gear_capacity(v, t, "lift_gear", 0.15) for t in tilts[v])
        out[name] = dict(min_normal_N=dict(A=round(min(r_[2] for r_ in rows if r_[1] != "P16 stall"), 2),
                                           B=round(min(r_[3] for r_ in rows if r_[1] != "P16 stall"), 2),
                                           C=round(min(r_[4] for r_ in rows if r_[1] != "P16 stall"), 2)),
                         seated_everywhere=all(r_[5] for r_ in rows if r_[1] != "P16 stall"),
                         seated_at_P16_stall=all(r_[5] for r_ in rows if r_[1] == "P16 stall"),
                         gear_capacity_mu015=round(cap, 3),
                         unseated=[f"{r_[0]:.0f} deg {r_[1]}" for r_ in rows if not r_[5]])
    VARIANT = {}
    return out


# ------------------------------------------------------------------------------------------------ Hertz
def estar(E1, n1, E2, n2):
    return 1.0 / ((1 - n1 ** 2) / E1 + (1 - n2 ** 2) / E2)


def hertz_point(W: float, R1x: float, R1y: float, R2x: float, R2y: float, Es: float) -> dict:
    """Elliptical point contact, Hamrock-Brewe approximations. Radii in two principal planes (inf = flat)."""
    inv = lambda r: 0.0 if math.isinf(r) else 1.0 / r   # noqa: E731
    Rx = 1.0 / (inv(R1x) + inv(R2x))
    Ry = 1.0 / (inv(R1y) + inv(R2y))
    if Ry < Rx:
        Rx, Ry = Ry, Rx
    R = 1.0 / (1 / Rx + 1 / Ry)
    al = Ry / Rx
    k = 1.0339 * al ** 0.636
    Eb = 1.0003 + 0.5968 / al
    Fb = 1.5277 + 0.6023 * math.log(al)
    Ep = 2.0 * Es
    a = (6 * k * k * Eb * W * R / (math.pi * Ep)) ** (1 / 3)        # semi-axis along y (the larger)
    b = (6 * Eb * W * R / (math.pi * k * Ep)) ** (1 / 3)
    p0 = 3 * W / (2 * math.pi * a * b)
    delta = Fb * ((9 / (2 * Eb * R)) * (W / (math.pi * k * Ep)) ** 2) ** (1 / 3)
    return dict(W_N=W, a_mm=a, b_mm=b, p0_MPa=p0, approach_um=1000 * delta)


def hertz_ball_flat(W: float, R: float, Es: float) -> dict:
    a = (3 * W * R / (4 * Es)) ** (1 / 3)
    return dict(W_N=W, a_mm=a, p0_MPa=3 * W / (2 * math.pi * a * a), approach_um=1000 * a * a / R)


def hertz_line(q: float, R: float, Es: float) -> dict:
    """Line contact, load q per unit length on a cylinder of radius R (the ball's meridian) against a straight
    generator (the cone): half-width b, peak p0, normal approach (Johnson, 2-D, 'depth' about 4R)."""
    b = math.sqrt(4 * q * R / (math.pi * Es))
    p0 = 2 * q / (math.pi * b)
    delta = q / (math.pi * Es) * (2 * math.log(4 * R / b) - 1)
    return dict(q_N_mm=q, b_mm=b, p0_MPa=p0, approach_um=1000 * delta)


def cone_contact(N_ax: float, F_lat: float, half=45.0, E=E_PETG) -> dict:
    """Ball in a printed cone: axial N_ax and lateral F_lat (N) as a line load round the contact circle,
    q(phi) = q0 + q1 cos(phi). Peak q = q0 + q1; q1 > q0 means one side lifts off (the ball would climb, frictionless)."""
    b = math.radians(half)
    rc = R_BALL * math.cos(b)                        # contact circle radius (ball centre on the axis)
    q0 = N_ax / (2 * math.pi * rc * math.sin(b))
    q1 = F_lat / (math.pi * rc * math.cos(b))
    Es = estar(E_STEEL, NU_STEEL, E, NU_PETG)
    h = hertz_line(q0 + q1, R_BALL, Es)
    h.update(rc_mm=rc, q0=q0, q1=q1, lat_over_ax=F_lat / max(N_ax, 1e-9), climbs=bool(q1 > q0),
             axial_approach_um=h["approach_um"] / math.sin(b))
    return h


def vee_contacts(FB_on_ec: np.ndarray, s: float, vee_n: np.ndarray | None = None) -> tuple:
    """Split the vee's reaction (across its groove, z) into its two dowel normals (90 deg vee, normals 45 deg off the
    seat axis); as drawn the groove runs along y, so 'across' is x."""
    F = -FB_on_ec                                    # force on the plate's ball from the dowels
    if vee_n is not None and abs(vee_n[0]) < 0.999:  # a turned groove: work in (across, z)
        F = np.array([np.dot(F, vee_n) * np.sign(vee_n[0] or 1.0), 0.0, F[2]])
    a = math.radians(45.0)
    n1 = np.array([math.sin(a), 0, -s * math.cos(a)])
    n2 = np.array([-math.sin(a), 0, -s * math.cos(a)])
    M = np.array([[n1[0], n2[0]], [n1[2], n2[2]]])
    N1, N2 = np.linalg.solve(M, np.array([F[0], F[2]]))
    return float(N1), float(N2)


def hertz_all() -> dict:
    """Every dock state (both designs, tilt sweep, NEMA 11 idle and at stall, the P16 stall) -> contact forces and stresses."""
    Es_ss = estar(E_STEEL, NU_STEEL, E_STEEL, NU_STEEL)
    out = {"assumptions": {
        "seat_magnet_pull_N": {f"gap {g} mm": round(magnet_ball_pull(g), 2) for g in (0.0, 0.3, 0.6, 1.0, 2.3)},
        "electromagnet_N": F_EM, "gear_sep_N": F_SEP_STALL, "gear_tangential_N": round(F_T_STALL, 2),
        "module_kg": M_MODULE, "ec_kg": M_EC, "P16_stall_N": P16_STALL,
        "allowables_MPa": P_ALLOW, "E_star_steel_petg": round(estar(E_STEEL, NU_STEEL, E_PETG, NU_PETG), 1),
        "E_star_steel_petg_creep": round(estar(E_STEEL, NU_STEEL, E_PETG_CREEP, NU_PETG), 1)}, "states": []}
    worst = {}
    tilts = {"v3": (0.0, 15.0, 30.0, 45.0), "v4": (0.0, 15.0, 30.0, 50.0)}
    for v in ("v3", "v4"):
        G = dock_geometry(v)
        cases = [(0.0, "float", 1.0), (0.0, "float_tap", 1.0), (0.0, "float_gear", 1.0), (0.0, "float_gear", -1.0)] if v == "v3" else []
        for t in tilts[v]:
            cases += [(t, "lift", 1.0), (t, "lift_tap", 1.0), (t, "lift_gear", 1.0), (t, "lift_gear", -1.0)]
        cases += [(0.0, "stall", 1.0)] + ([(50.0, "stall", 1.0)] if v == "v4" else [])
        for t, c, sg in cases:
            r = dock_forces(v, t, c, ft_sign=sg)
            cone = cone_contact(max(r["nA"], 1e-6), r["latA"])
            cone_creep = cone_contact(max(r["nA"], 1e-6), r["latA"], E=E_PETG_CREEP)
            N1, N2 = vee_contacts(r["FB"], G["s"])
            Nd = max(N1, N2, 1e-6)
            vee = hertz_point(Nd, R_BALL, R_BALL, R_DOWEL, math.inf, Es_ss)
            flat = hertz_ball_flat(max(r["nC"], 1e-6), R_BALL, Es_ss)
            flat_allow = P_ALLOW["mild_steel"] if v == "v3" else P_ALLOW["case_hardened"]
            rec = dict(design=v, tilt_deg=t, case=c + ("" if sg > 0 else " (gear reversed)"), P16_N=round(r["P16_N"], 2),
                       normal_N=dict(A=round(r["nA"], 2), B=round(r["nB"], 2), C=round(r["nC"], 2)),
                       A_lateral_N=round(r["latA"], 2), B_lateral_N=round(abs(r["B_across"]), 2), dock_closed=bool(seated(r)),
                       cone=dict(p0_MPa=round(cone["p0_MPa"], 1), half_width_mm=round(cone["b_mm"], 3),
                                 axial_approach_um=round(cone["axial_approach_um"], 2),
                                 axial_approach_creep_um=round(cone_creep["axial_approach_um"], 2),
                                 lateral_over_axial=round(cone["lat_over_ax"], 2), one_side_lifts=cone["climbs"],
                                 sf=round(P_ALLOW["petg_line"] / cone["p0_MPa"], 2)),
                       vee=dict(N_per_dowel=(round(N1, 2), round(N2, 2)), p0_MPa=round(vee["p0_MPa"], 0),
                                approach_um=round(vee["approach_um"], 2), sf=round(P_ALLOW["hardened"] / vee["p0_MPa"], 2)),
                       flat=dict(material="low-carbon steel armature" if v == "v3" else "case-hardened M5 washer",
                                 p0_MPa=round(flat["p0_MPa"], 0), radius_mm=round(flat["a_mm"], 4),
                                 approach_um=round(flat["approach_um"], 2), sf=round(flat_allow / flat["p0_MPa"], 2)))
            out["states"].append(rec)
            for k, val in (("cone_p0", rec["cone"]["p0_MPa"]), ("vee_p0", rec["vee"]["p0_MPa"]), ("flat_p0", rec["flat"]["p0_MPa"])):
                key = (v, k, c == "stall")
                if val > worst.get(key, (0, None))[0]:
                    worst[key] = (val, rec)
    cap = {}
    for v in ("v3", "v4"):
        for t in tilts[v]:
            for c in (("float_gear", "lift_gear") if (v == "v3" and t == 0.0) else ("lift_gear",)):
                cap[f"{v} {c} {t:.0f} deg"] = dict(frictionless=round(gear_capacity(v, t, c, 0.0), 3),
                                                   mu_0p15=round(gear_capacity(v, t, c, 0.15), 3),
                                                   mu_0p3=round(gear_capacity(v, t, c, 0.3), 3))
    out["gear_capacity"] = dict(note="fraction of the NEMA 11 stall mesh load (3.7 N separating + 10.2 N tangential, about 0.10 N*m "
                                     "at the 20T pinion) at which the first ball leaves its seat; 0 = unseated with the motor idle. "
                                     "For scale (cad/gear-mesh): heavy running, 0.03 N*m at the auger = 0.0136 N*m at the pinion = 0.134; "
                                     "the DRV8825 0.45 A stall, 0.067 N*m at the pinion = 0.66",
                                heavy_running=0.134, driver_stall=0.66, cases=cap)
    out["unseated_states"] = [f"{s_['design']} {s_['tilt_deg']:.0f} deg {s_['case']}" for s_ in out["states"] if not s_["dock_closed"]]
    out["variants"] = variants()
    out["worst"] = {f"{k[0]} {k[1]} {'P16 stall' if k[2] else 'operating'}": dict(value=w[0], tilt=w[1]["tilt_deg"], case=w[1]["case"])
                    for k, w in sorted(worst.items())}
    # flat: plastic dent in the v3 armature (fully plastic mean pressure about 3 Y): depth after the first docks
    W = max(max(s["normal_N"]["C"] for s in out["states"] if s["design"] == "v3" and "stall" not in s["case"]), 1e-6)
    a = math.sqrt(W / (math.pi * 3 * 180.0))
    out["armature_dent"] = dict(W_N=round(W, 2), radius_mm=round(a, 4), depth_um=round(1000 * a * a / (2 * R_BALL), 2),
                                note="mean pressure 3Y over the dent; after it forms, repeat docks at the same spot are elastic")
    # cradle seats under the parked EC (the EC's weight on its three base balls, sustained: creep modulus)
    out["cradle_seats"] = cradle_seat_loads()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "hertz.json").write_text(json.dumps(out, indent=1, default=float))
    return out


def cradle_seat_loads() -> dict:
    """The parked EC on the cradle's Kelvin seat (cone at EC_BALLS[0], vee [1], flat [2]): the EC's weight, and the
    P16 pulling down at stall through the bottom of the clevis slot (a retract past the seat)."""
    P = params("v3")
    (x1, y1), (x2, y2), (x3, y3) = P.EC_BALLS
    out = {}
    for v in ("v3", "v4"):
        W = M_EC[v] * LD.G_MS2
        xc = COM_EC_DRAWN[v][0]
        xp = P.EC_PIN[0]
        res = {}
        for nm, F, x in (("parked (EC weight)", W, xc), ("P16 retract stall + weight", None, None)):
            if F is None:                          # weight at xc + 50 N at the pin
                f13 = (W * (xc - x3) + P16_STALL * (xp - x3)) / (x1 - x3)
                f3 = W + P16_STALL - f13
            else:
                f13 = F * (x - x3) / (x1 - x3)
                f3 = F - f13
            fc = fv = f13 / 2
            cone = cone_contact(fc, 0.0)
            cone_c = cone_contact(fc, 0.0, E=E_PETG_CREEP)
            N1 = fv / (2 * math.cos(math.radians(45)))
            vee = hertz_point(N1, R_BALL, R_BALL, R_DOWEL, math.inf, estar(E_STEEL, NU_STEEL, E_STEEL, NU_STEEL))
            flat = hertz_ball_flat(f3, R_BALL, estar(E_STEEL, NU_STEEL, E_STEEL, NU_STEEL))
            res[nm] = dict(cone_N=round(fc, 2), vee_N=round(fv, 2), flat_N=round(f3, 2), cone_p0_MPa=round(cone["p0_MPa"], 1),
                           cone_axial_approach_um=round(cone["axial_approach_um"], 2),
                           cone_axial_approach_creep_um=round(cone_c["axial_approach_um"], 2),
                           vee_p0_MPa=round(vee["p0_MPa"], 0), flat_p0_MPa=round(flat["p0_MPa"], 0),
                           flat_sf_plain_washer=round(1.6 * 250.0 / flat["p0_MPa"], 2))
        out[v] = res
    return out


# ------------------------------------------------------------------------------------------------ FEA helpers
def mat_setup():
    MAT.add(MAT.Material("PETG_EC", E_PETG, NU_PETG, 1.27e-9, MAT.get("PETG").allow, "PETG (printed, short-term)"))


def nodes_near_circle(m, idx, centre, axis, radius, half_band=0.6, along=None):
    """Mesh nodes (of idx) on a ring: within half_band of `radius` from an axis through centre, and (if along) within
    +-along[1] of along[0] measured along the axis."""
    c = np.asarray(centre, float)
    a = np.asarray(axis, float) / np.linalg.norm(axis)
    d = m.xyz[idx] - c
    t = d @ a
    r = np.linalg.norm(d - np.outer(t, a), axis=1)
    ok = np.abs(r - radius) < half_band
    if along is not None:
        ok &= np.abs(t - along[0]) < along[1]
    return idx[ok]


def faces_in_ball(m, centre, radius, normal_pred=None, parts=None):
    c = np.asarray(centre, float)

    def pred(cc, n):
        return np.linalg.norm(cc - c) < radius and (normal_pred is None or normal_pred(n))
    return m.faces_where(pred, parts)


def ec_shape(v: str) -> Path:
    """The EC as exported, for v3 with two bridge ribs added: as drawn (45e9740) the electromagnet cup and ball C's
    boss are a separate solid, 3.6 mm from the bracket arms (arms end at x 90 at |y| 12-15, the cup is r 12 about x 100).
    The ribs (x 88-99.5, |y| 10.4-12.4, the bracket's full height) are this FEA's proposal for the joint."""
    src = fem.step_path(DES[v], "sam_electronics_carriage")
    if v != "v3":
        return src
    dst = fem.WORK / "station" / "ec_v3_bridged.step"
    if dst.exists():
        return dst
    import cadquery as cq
    s = cq.importers.importStep(str(src))
    sol = s.solids().vals()
    w = cq.Workplane("XY").add(sol[0])
    for x in sol[1:]:
        w = w.union(cq.Workplane("XY").add(x))
    P = params("v3")
    DR = P.DOCK_RISE_V3
    mag_face = -18.0 - 2.0 - 0.15 - DR
    ztop, zbot = mag_face - 0.3, mag_face - 17.0
    for sy in (-1, 1):
        y0, y1 = (10.4, 12.4) if sy > 0 else (-12.4, -10.4)
        w = w.union(cq.Workplane("XY").box(11.5, y1 - y0, ztop - zbot, centered=False).translate((88.0, y0, zbot)))
    n = len(w.solids().vals())
    dst.parent.mkdir(parents=True, exist_ok=True)
    cq.exporters.export(w, str(dst))
    print("EC v3 bridged:", n, "solid(s)", flush=True)
    return dst


def _rigid_reaction(res, name: str):
    """Reaction force (ref node) and moment (rot node) of a fixed rigid patch, from the .dat's R_<name> block."""
    r, q = [(a, b) for (n, a, b) in res.deck.rigid if n == name][0]
    txt = res.dat
    i = txt.find(f"forces (fx,fy,fz) for set R_{name.upper()}")
    out = {}
    for line in txt[i:].splitlines()[2:6]:
        parts = line.split()
        if len(parts) >= 4 and parts[0].isdigit():
            out[int(parts[0])] = np.array([float(v) for v in parts[1:4]])
    return out.get(r, np.zeros(3)), out.get(q, np.zeros(3))


# ------------------------------------------------------------------------------------------------ EC FEA
def ec_case(v: str, tilt: float, case: str, ft_sign: float = 1.0, h: float = 2.2, gear_limit: bool = False):
    """EC (printed PETG, one part) docked: every load from dock_forces() applied, held at its clevis pin.
    gear_limit: the mesh load at 98 % of the largest the dock carries seated (the direction that allows more)."""
    mat_setup()
    G = dock_geometry(v)
    P = params(v)
    dr = G["dr"]
    gs = 1.0
    if gear_limit:
        caps = {sg: gear_capacity_sign(v, tilt, case, sg) for sg in (1.0, -1.0)}
        ft_sign = max(caps, key=caps.get)
        gs = 0.98 * caps[ft_sign]
    r = dock_forces(v, tilt, case, ft_sign=ft_sign, gear_scale=gs)
    if not seated(r):
        print(f"warning: {v} {case} {tilt}: the dock is not seated in this state (loads applied as if it held)", flush=True)
    sh = np.array([0.0, 0.0, -dr])                   # docked -> as drawn
    A, B, C, pin = G["A"] + sh, G["B"] + sh, G["C"] + sh, G["pin"] + sh
    refine = [(tuple(A), 5.0, 0.7), (tuple(B), 6.0, 0.7), (tuple(C), 5.0, 0.8), (tuple(pin), 7.0, 0.8)]
    m = fem.mesh_parts([fem.Part("EC", ec_shape(v), None, "PETG_EC")], size=h, size_min=0.5, curv=12, refine=refine)
    d = fem.Deck(m)
    s = G["s"]
    # mass: printed body scaled so the mesh carries the whole EC's weight (motor, solenoid, magnets: smeared)
    V = m.volumes().sum()
    rho = M_EC[v] * 1e-3 / V
    MAT.add(MAT.Material("PETG_ECM", E_PETG, NU_PETG, rho, MAT.get("PETG").allow, "PETG (printed, short-term)"))
    d.mat_override = {"EC": "PETG_ECM"}
    vol = m.volumes()
    com = (m.xyz[m.tet[:, :4]].mean(1) * vol[:, None]).sum(0) / vol.sum()
    # the statics used COM_EC_DRAWN; the smeared mesh's own COM is what the FEA loads with: report both
    g = gravity_sam(v, tilt)
    d.gravity(direction=tuple(g), g=fem.G)
    idx = np.arange(m.n)
    # --- A: cone ring (the ball's contact circle)
    beta = math.radians(P.KC_CONE_HALF)
    zc = A[2] + s * (-1) * 0 + (-R_BALL * math.cos(beta) if v == "v3" else R_BALL * math.cos(beta))
    rc = R_BALL * math.sin(beta)
    fa = m.faces_where(lambda c, n: abs(math.hypot(c[0] - A[0], c[1] - A[1]) - rc) < 0.9 and abs(c[2] - zc) < 0.9)
    d.traction(fa, r["FA"])
    # --- B: the two dowel holes (bearing), split into the two dowel normals
    N1, N2 = vee_contacts(r["FB"], s)
    bx, by = B[0], B[1]
    hgt = math.sqrt((R_BALL + R_DOWEL) ** 2 - (P.VEE_SPACING / 2) ** 2)
    zd = B[2] + (-hgt if v == "v3" else hgt)
    a45 = math.radians(45.0)
    n1 = np.array([math.sin(a45), 0, -s * math.cos(a45)])
    n2 = np.array([-math.sin(a45), 0, -s * math.cos(a45)])
    for sx, Nn, nn in ((-1, N1, n1), (+1, N2, n2)):          # n1 is the push of the -x dowel on the ball (toward +x)
        x0 = bx + sx * P.VEE_SPACING / 2
        fb = m.faces_where(lambda c, n, x0=x0: abs(math.hypot(c[0] - x0, c[2] - zd) - (R_DOWEL - 0.02)) < 0.35 and abs(c[1] - by) < 4.0)
        if abs(Nn) > 1e-9:
            # the ball pushes the dowel along -nn (nn is the dowel's push on the ball); the dowel bears on its hole
            if not fb:
                raise RuntimeError(f"no faces for the vee dowel hole at x {x0:.2f}")
            d.bearing(fb, -Nn * nn, (x0, by, zd), (0, 1, 0))
    # --- C
    if v == "v3":
        cpt = np.array([P.KC_C[0], P.KC_C[1], -18.0 - 2.0 - R_BALL - dr])      # ball C's centre, as drawn
    else:
        c_face = (-13.0 - dr) + (6.35 - 2.6)
        cpt = np.array([P.KC4_C[0], P.KC4_C[1], c_face + 2.6 - R_BALL])
    fc = m.faces_where(lambda c, n: np.linalg.norm(c - cpt) < R_BALL + 0.3 and abs(math.hypot(c[0] - cpt[0], c[1] - cpt[1])) < 3.3)
    d.traction(fc, r["FC"])
    # --- magnets: on their pockets' floors (seat magnets) / the electromagnet cup's floor
    for (nm, p, f) in r["loads"]:
        if "magnet" in nm:
            q = np.array(p) + sh
            fm = m.faces_where(lambda c, n, q=q: math.hypot(c[0] - q[0], c[1] - q[1]) < (10.2 if nm == "electromagnet" else 3.4)
                               and -s * (c[2] - q[2]) * 0 + abs(c[2] - q[2]) < (16.0 if nm == "electromagnet" else 7.0)
                               and abs(n[2]) > 0.9)
            if fm:
                d.traction(fm, f)
        elif nm == "gear mesh":
            # pinion -> NEMA 11 -> its face on the back wall's inner face (x 68.3 (v3) as drawn): rigid patch, ref at the mesh
            wall = m.nodes_where(lambda p_: (np.abs(p_[:, 0] - P.NEMA11_X) < 0.15) & (np.abs(p_[:, 1]) < 14.0)
                                 & (np.abs(p_[:, 2] - (P.NEMA11_Z if v == "v3" else -P.NEMA11_Z)) < 14.0))
            if len(wall) > 10:
                rr, qq = d.rigid_patch(wall, "MOTOR", at=np.array(p) + sh)
                d.node_load(rr, F=tuple(f))
    # --- the clevis pin: the slot's end the pin bears on (pushing toward the plate: the slot's plate-side end)
    pz = pin[2]
    end = pz + (1.0 if v == "v3" else -1.0) * (-s)    # slot end centre (slot 2 mm of travel: ends 1 mm off the pin's mid)
    if case == "float":
        end = pz
    slot = m.nodes_where(lambda p_: (np.abs(np.hypot(p_[:, 0] - pin[0], p_[:, 2] - end) - 2.05) < 0.25)
                         & (np.abs(p_[:, 1]) > 4.7) & (np.abs(p_[:, 1]) < 9.9) & ((-s) * (p_[:, 2] - end) >= -0.3))
    rr, qq = d.rigid_patch(slot, "PIN", at=(pin[0], 0.0, end))
    d.fix_ids([rr, qq], dofs=(1, 2, 3), name="PINFIX")
    d.print_reactions("PINFIX")
    tag = f"ec_{v}_{case}_t{int(tilt)}" + ("_gearlimit" if gear_limit else ("" if ft_sign > 0 else "_rev"))
    res = d.solve(f"station/{tag}")
    # functional numbers: the pinion's (NEMA 11 face patch) and the three contacts' movement relative to the pin
    U = res.U
    def at(p_):
        k = np.argmin(np.linalg.norm(m.xyz - p_, axis=1))
        return U[k]
    uA, uB, uC = at(A), at(B), at(cpt)
    wall_c = np.array([P.NEMA11_X, 0.0, P.NEMA11_Z if v == "v3" else -P.NEMA11_Z])
    uM = at(wall_c)
    # pinion-to-dock: the plate sits on A, B, C; the gear's centre distance changes with the pinion's z relative to the
    # plane through the contacts (at the pinion's x): interpolate the contacts' z displacement
    xm = MESH_V3[0]
    uz_dock = uA[2] + (uC[2] - 0.5 * (uA[2] + uB[2])) * (xm - A[0]) / (cpt[0] - A[0]) * 1.0 + 0.5 * (uB[2] - uA[2]) * 0.0
    key = {"cone A |u|": np.linalg.norm(uA), "vee B |u|": np.linalg.norm(uB), "flat C |u|": np.linalg.norm(uC),
           "motor face |u|": np.linalg.norm(uM),
           "centre-distance change at the mesh (mm, + opens)": float(-s * (uM[2] - uz_dock))}
    rf = res.reactions("PINFIX")
    pin_rd = _rigid_reaction(res, "PIN")                 # (force at the ref node, moment at the rot node): the statics check
    exc = np.concatenate([d.nsets["PIN"] - 1])
    rec = common.record(MODULE, tag, design=DES[v], part="electronics carriage (printed PETG)",
                        load_case=f"{case} at {tilt:.0f} deg" + (f", mesh load {gs:.3f} x the NEMA 11 stall (the seated limit)" if gear_limit else ""), res=res,
                        exclude=exc, exclude_r=1.5, key_disp=key,
                        loads_desc=dict(P16_N=round(r["P16_N"], 2), contact_normal_N=dict(A=round(r["nA"], 2), B=round(r["nB"], 2), C=round(r["nC"], 2)),
                                        A_lateral_N=round(r["latA"], 2), pin_reaction_N=[round(x, 2) for x in pin_rd[0]],
                                        pin_reaction_moment_Nmm=[round(x, 1) for x in pin_rd[1]],
                                        statics_P16_vector_N=[round(x, 2) for x in (r["P16_N"] * p16_axis_sam(v, tilt))],
                                        gear_scale=round(gs, 4) if case.endswith("gear") else 0.0, seated=seated(r)),
                        notes=("v3 EC as drawn has its electromagnet cup and ball C's boss as a separate solid; two bridge ribs "
                               "added for this run" if v == "v3" else "EC v4 as drawn (one solid)")
                              + f"; EC weight smeared over the printed body (mesh COM {np.round(com, 1).tolist()} vs statics {list(COM_EC_DRAWN[v])})",
                        png_kw=dict(view=(1.0, -1.3, 0.7) if v == "v3" else (1.0, -1.3, -0.7), up=(0, 0, 1) if v == "v3" else (0, 0, -1)),
                        render=True)
    return rec


def ec_modes(v: str = "v4", h: float = 2.2, n: int = 6):
    """EC v4 approaching the dock (no contacts yet): held at its clevis pin, natural frequencies (the arms)."""
    mat_setup()
    G = dock_geometry(v)
    sh = np.array([0.0, 0.0, -G["dr"]])
    pin = G["pin"] + sh
    A = G["A"] + sh
    m = fem.mesh_parts([fem.Part("EC", ec_shape(v), None, "PETG_EC")], size=h, size_min=0.6, curv=12,
                       refine=[(tuple(pin), 7.0, 0.8), (tuple(A), 6.0, 1.0)])
    V = m.volumes().sum()
    rho = M_EC[v] * 1e-3 / V
    MAT.add(MAT.Material("PETG_ECM", E_PETG, NU_PETG, rho, MAT.get("PETG").allow, "PETG (printed, short-term)"))
    d = fem.Deck(m, materials={"EC": "PETG_ECM"})
    slot = m.nodes_where(lambda p_: (np.abs(np.hypot(p_[:, 0] - pin[0], p_[:, 2] - pin[2]) - 2.05) < 0.3)
                         & (np.abs(p_[:, 1]) > 4.7) & (np.abs(p_[:, 1]) < 9.9))
    d.fix(slot, name="SLOT")
    # the EC also leans on the P16 rod end's tab between the cheeks; with the pin alone it can rock: hold the base's
    # seat-ball pockets' rim too (it sits just off the cradle while rising) -> a lower bound on the arms' frequency
    d.frequency(n)
    res = d.solve(f"station/ec_{v}_modes")
    out = dict(module=MODULE, case=f"ec_{v}_modes", design=DES[v], part="electronics carriage v4 (arms)", load_case="modes, held at the clevis pin",
               freqs_Hz=[round(f, 1) for f in res.freqs], nodes=int(m.n), elements=int(len(m.tet)))
    # which part moves: the arms' tips vs the body
    for i, U in enumerate(res.modes[:n]):
        um = np.linalg.norm(U, axis=1)
        k = int(np.argmax(um))
        out.setdefault("mode_peak_at", []).append([round(x, 1) for x in m.xyz[k]])
    OUT.mkdir(parents=True, exist_ok=True)
    try:
        fem.render(res, OUT / f"ec_{v}_mode1.png", field="u", mode=0, title=f"{DES[v]}: EC held at its clevis pin, mode 1 {res.freqs[0]:.0f} Hz",
                   view=(1.0, -1.3, -0.7), up=(0, 0, -1))
        out["png"] = f"out/{MODULE}/ec_{v}_mode1.png"
    except Exception as e:                             # noqa: BLE001
        out["png_error"] = str(e)[:200]
    (OUT / f"ec_{v}_modes.json").write_text(json.dumps(out, indent=1))
    return out


# ------------------------------------------------------------------------------------------------ cradle
def cradle_case(v: str, case: str = "retract_stall", h: float = 2.2):
    """The guide cradle on its 2020 post (M6 into the post's top through the arm's pad): the parked EC on its three base
    balls, plus (retract_stall) the P16 pulling the EC down through the bottom of the clevis slot at 50 N, plus a 2 N
    lean of the rising EC on the front wall."""
    mat_setup()
    P = params("v3")
    g = geo(v)
    src = fem.step_path(DES[v], "cradle")
    zb0 = P.EC_BASE_Z - P.EC_BASE_T
    ball_z = zb0 + 2.6 - R_BALL / 1.0 * 1.0 - (R_BALL - 3.175)      # base balls' centres (cradle frame = parked EC as drawn)
    ball_z = zb0 + 2.6 - 6.35 / 2
    sz = 1.0 if v == "v3" else -1.0                                 # v4's cradle is v3's mirrored z -> -z
    (x1, y1), (x2, y2), (x3, y3) = P.EC_BALLS
    post = (58.0, -32.0) if v == "v3" else tuple(g["CRADLE_POST_S"])
    refine = [((x1, y1, sz * ball_z), 5.0, 0.7), ((x2, y2, sz * ball_z), 6.0, 0.7), ((x3, y3, sz * ball_z), 6.0, 0.8)]
    m = fem.mesh_parts([fem.Part("cradle", src, None, "PETG")], size=h, size_min=0.5, curv=12, refine=refine)
    d = fem.Deck(m)
    f0 = zb0 + 2.6 - 3.175 - 1.0 - 6.0                               # floor's underside (= the arm pad's underside)
    pad = m.nodes_where(lambda p: (np.abs(p[:, 2] - sz * f0) < 0.05) & (np.abs(p[:, 0] - post[0]) < 10.0) & (np.abs(p[:, 1] - post[1]) < 10.0))
    d.fix(pad, name="POST")
    d.print_reactions("POST")
    W = M_EC[v] * LD.G_MS2
    xc, xp = COM_EC_DRAWN[v][0], P.EC_PIN[0]
    if case == "parked":
        f13 = W * (xc - x3) / (x1 - x3)
        f3 = W - f13
    else:
        f13 = (W * (xc - x3) + P16_STALL * (xp - x3)) / (x1 - x3)
        f3 = W + P16_STALL - f13
    down = np.array([0, 0, -sz])                                    # toward the cradle's floor
    # cone (x1, y1): ring at the contact circle
    zc = sz * (ball_z - R_BALL * math.cos(math.radians(45)))
    fcone = m.faces_where(lambda c, n: abs(math.hypot(c[0] - x1, c[1] - y1) - R_BALL * math.sin(math.radians(45))) < 0.9 and abs(c[2] - zc) < 0.9)
    d.traction(fcone, 0.5 * f13 * down)
    # vee (x2, y2): the two dowel holes
    hgt = math.sqrt((R_BALL + R_DOWEL) ** 2 - (P.VEE_SPACING / 2) ** 2)
    zd = sz * (ball_z - hgt)
    Nd = 0.5 * f13 / 2 / math.cos(math.radians(45))
    for sx in (-1, 1):
        x0 = x2 + sx * P.VEE_SPACING / 2
        fb = m.faces_where(lambda c, n, x0=x0: abs(math.hypot(c[0] - x0, c[2] - zd) - (R_DOWEL - 0.02)) < 0.35 and abs(c[1] - y2) < 4.0)
        F = Nd * np.array([sx * math.sin(math.radians(45)), 0, -sz * math.cos(math.radians(45))])
        if fb:
            d.bearing(fb, F, (x0, y2, zd), (0, 1, 0))
    # flat (x3, y3): the washer's pocket floor
    zf = sz * (ball_z - R_BALL - 1.0)
    ff = m.faces_where(lambda c, n: math.hypot(c[0] - x3, c[1] - y3) < 4.0 and abs(c[2] - zf) < 0.05)
    d.traction(ff, f3 * down)
    if case != "parked":                                            # lean on the front wall, inner face, near its top
        xf = 2.3 - P.GUIDE_CLEAR
        fw = m.faces_where(lambda c, n: abs(c[0] - xf) < 0.05 and abs(c[1]) < 15.0 and abs(c[2] - sz * (-35.0)) < 6.0)
        if fw:
            d.traction(fw, (-2.0, 0, 0))
    tag = f"cradle_{v}_{case}"
    res = d.solve(f"station/{tag}")
    U = res.U
    def uz(p):
        k = np.argmin(np.linalg.norm(m.xyz - np.asarray(p), axis=1))
        return float(U[k, 2] * sz)
    key = {"cone seat dz (mm, toward the floor -)": uz((x1, y1, zc)), "vee seat dz": uz((x2, y2, zd)),
           "flat seat dz": uz((x3, y3, zf)), "worst seat dz": min(uz((x1, y1, zc)), uz((x2, y2, zd)), uz((x3, y3, zf)))}
    rec = common.record(MODULE, tag, design=DES[v], part="guide cradle (printed PETG)", load_case=case, res=res,
                        exclude=d.nsets["POST"] - 1, exclude_r=2.0, key_disp=key,
                        loads_desc=dict(cone_N=round(f13 / 2, 2), vee_N=round(f13 / 2, 2), flat_N=round(f3, 2),
                                        post_reaction_N=[round(x, 2) for x in res.reactions("POST")]),
                        notes="arm pad bonded to the post's top (an M6 into its centre bore); ball loads from the parked EC + P16",
                        png_kw=dict(view=(1.0, -1.4, 0.8 * sz), up=(0, 0, sz)))
    return rec


# ------------------------------------------------------------------------------------------------ base clevis bracket
def clevis_case(v: str, F: float, tilt: float, label: str, h: float = 1.6):
    """The P16's base clevis (printed) on the station rail: its foot held at its two M5 T-nut screws and on the rail's
    top under it (compression only would need contact: here the foot's underside is held), the pin's load as a bearing
    load on both cheeks' holes along the actuator's axis (pushing: the bracket is pushed down)."""
    src = fem.step_path(DES[v], "clevis_bracket")
    m = fem.mesh_parts([fem.Part("clevis bracket", src, None, "PETG")], size=h, size_min=0.4, curv=12,
                       refine=[((0, 0, 0), 7.0, 0.6)])
    d = fem.Deck(m)
    zmin = m.xyz[:, 2].min()
    foot = m.nodes_where(lambda p: np.abs(p[:, 2] - zmin) < 0.05)
    d.fix(foot, name="FOOT")
    d.print_reactions("FOOT")
    # actuator axis in the world: from geo (B -> P); the bracket's frame = world axes at B
    gg = geo(v)
    key_ = f"{float(tilt):.1f}"
    B, Pp = np.array(gg[key_]["B"]), np.array(gg[key_]["P"])
    u = (Pp - B) / np.linalg.norm(Pp - B)
    Fv = -F * u                                                   # the P16 pushes its base pin down/back
    holes = m.faces_where(lambda c, n: abs(math.hypot(c[0], c[2]) - 2.075) < 0.3 and abs(c[1]) > 4.0)
    d.bearing(holes, Fv, (0, 0, 0), (0, 1, 0))
    tag = f"clevis_{v}_{label}"
    res = d.solve(f"station/{tag}")
    hole_n = np.unique(np.concatenate([f[2] for f in holes]))
    k = hole_n[np.argmax(np.linalg.norm(res.U[hole_n], axis=1))]
    rec = common.record(MODULE, tag, design=DES[v], part="P16 base clevis bracket (printed PETG)",
                        load_case=f"{F:.0f} N along the P16 at {tilt:.0f} deg ({label})", res=res,
                        exclude=d.nsets["FOOT"] - 1, exclude_r=1.0, key_disp={"pin hole |u|": float(np.linalg.norm(res.U[k]))},
                        loads_desc=dict(F_N=F, direction=np.round(Fv / F, 3).tolist(), foot_reaction=[round(x, 2) for x in res.reactions("FOOT")]),
                        notes="foot's underside held (bonded) on the rail; cheeks 3.7 mm, the 4 mm shoulder screw in 4.2 mm holes",
                        png_kw=dict(view=(1.0, -1.5, 0.6)))
    return rec


# ------------------------------------------------------------------------------------------------ latch rail / v4 rails
def latch_rail_case(v: str, case: str, h: float = 1.6):
    """v3: the latch rail (cam) and its arm on the latch-rail post; v4: the one-piece latch rail + tube rest + web on its
    post. Loads: 'follower' - a follower riding the 25 deg ramp against the open latch's 2.0 N spring (normal force on
    the ramp 2.2 N, x1.5 for friction); 'tube' (v4) - the module resting by its tube on the rest while the latch is open;
    'unit' - 10 N on the ramp to scale the jam case (a follower that can't move, pushed by the drive)."""
    src = fem.step_path(DES[v], "latch_rail")
    P = params(v)
    gg = geo(v)
    post = (131.0, -19.0) if v == "v3" else tuple(gg["LATCH_POST_S"])
    if v == "v3":
        post = (P.LATCH_FOLLOW_X + 11.0, P.LATCH_Y)
    m = fem.mesh_parts([fem.Part("latch rail", src, None, "PETG")], size=h, size_min=0.4, curv=12)
    d = fem.Deck(m)
    # the post's top: v3 the arm's underside (z LATCH_RAIL_Z0 = -29.6) over the post; v4 the web/pad's outer face (z 31)
    if v == "v3":
        zp = m.xyz[:, 2].min()
    else:
        zp = m.xyz[:, 2].max()
    pad = m.nodes_where(lambda p: (np.abs(p[:, 2] - zp) < 0.05) & (np.abs(p[:, 0] - post[0]) < 10.0) & (np.abs(p[:, 1] - post[1]) < 10.0))
    d.fix(pad, name="POST")
    d.print_reactions("POST")
    xf = P.LATCH_FOLLOW_X + 1.5 + P.LATCH_TRAVEL
    half = P.LATCH_RAIL_FLAT
    ramp = P.LATCH_TRAVEL / math.tan(math.radians(RAMP_DEG))
    if v == "v3":
        zr = (-23.6 - 6.0 + -23.6) / 2
    else:
        zr = 22.0
    # ramp face at the +y end: from (xf, half) to (xf + travel, half + ramp); the follower midway
    py = P.LATCH_Y + half + ramp / 2
    px = xf + P.LATCH_TRAVEL / 2
    nrm = np.array([-math.sin(math.radians(RAMP_DEG)), math.cos(math.radians(RAMP_DEG)), 0.0])   # rough outward normal
    sel = m.faces_where(lambda c, n: abs(c[0] - px) < 1.6 and abs(c[1] - py) < 3.5 and abs(c[2] - zr) < 3.0 and n[0] < -0.5)
    if case == "unit":
        Fn = 10.0
    else:
        Fn = 1.5 * LATCH_SPRING_OPEN / math.cos(math.radians(RAMP_DEG))
    n_in = np.array([math.cos(math.radians(RAMP_DEG)), -math.sin(math.radians(RAMP_DEG)), 0.0])     # into the rail
    if sel:
        d.traction(sel, Fn * n_in)
    if v == "v4" and case == "tube":
        x0, x1 = P.TUBE_REST_X
        zf = 12.5 + P.CAP_REST_GAP
        sel2 = m.faces_where(lambda c, n: x0 - 0.1 <= c[0] <= x1 + 0.1 and abs(c[1]) < 6.0 and abs(c[2] - zf) < 0.1)
        Wm = M_MODULE[v] * LD.G_MS2 * (COM_MODULE[0] / (0.5 * (x0 + x1)))     # the rest carries the module's moment about the hinge
        d.traction(sel2, (0, 0, Wm))                       # the tube pushes the rest outward (Sam +z = down in v4)
    tag = f"latch_rail_{v}_{case}"
    res = d.solve(f"station/{tag}")
    k = np.argmax(np.linalg.norm(res.U, axis=1))
    rec = common.record(MODULE, tag, design=DES[v], part="latch rail" + (" + tube rest (printed PETG)" if v == "v4" else " (printed PETG)"),
                        load_case=case, res=res, exclude=d.nsets["POST"] - 1, exclude_r=1.5,
                        key_disp={"max |u| (mm)": float(np.linalg.norm(res.U[k])), "ramp normal force N": Fn},
                        loads_desc=dict(ramp_N=round(Fn, 2), post_reaction=[round(x, 2) for x in res.reactions("POST")]),
                        notes="its post pad bonded to the 2020 post's end (an M6 into the centre bore)",
                        png_kw=dict(view=(1.0, -1.2, 0.9)))
    return rec


# ------------------------------------------------------------------------------------------------ hold-down
def hold_down_case(F_total: float = 25.0, label: str = "p16_stall", h: float = 1.8):
    """v2's hold-down (used unchanged by v3 and v4 at the station), frame X = u (travel), Y = w (inward), Z = off the side
    plate. The station carriage's tongue pushes its lip inward (up at the station) when the P16 lifts against a module that
    can't swing (latch not open, v4 at the top run): 50 N at the P16 -> about 25 N per hold-down. Held at its two M5
    heat-set inserts (bonded), the face on the side plate held normal to the plate."""
    P = params("v3")
    src = fem.step_path(DES["v3"], "hold_down")
    m = fem.mesh_parts([fem.Part("hold-down", src, None, "PETG")], size=h, size_min=0.5, curv=12)
    d = fem.Deck(m)
    w_foot = P.CAR_W0 - P.CAR_T - P.HOLD_DOWN_FOOT_GAP
    ins = m.nodes_where(lambda p: ((np.hypot(p[:, 0] - 12.0, p[:, 1] - (w_foot - 11)) < 3.35) | (np.hypot(p[:, 0] + 12.0, p[:, 1] - (w_foot - 11)) < 3.35))
                        & (p[:, 2] < 10.05))
    d.fix(ins, name="INSERTS")
    face = m.nodes_where(lambda p: np.abs(p[:, 2]) < 0.02)
    d.fix(face, dofs=(3,), name="PLATEFACE")
    d.print_reactions("INSERTS")
    tz = P.CAR_W0 + P.HOLD_DOWN_GAP
    tongue_end = P.SIDE_GAP + P.CAR_X0
    lip = m.faces_where(lambda c, n: abs(c[1] - tz) < 0.05 and n[1] < -0.9 and c[2] > tongue_end + 0.2 and abs(c[0]) < 13.0)
    d.traction(lip, (0, F_total, 0))
    tag = f"hold_down_{label}"
    res = d.solve(f"station/{tag}")
    lipn = np.unique(np.concatenate([f[2] for f in lip]))
    rec = common.record(MODULE, tag, design="chain-carousel-v3 / v4", part="hold-down (printed PETG)",
                        load_case=f"{F_total:.0f} N up on the lip from the carriage tongue", res=res,
                        exclude=np.concatenate([d.nsets["INSERTS"] - 1]), exclude_r=1.5,
                        key_disp={"lip max |u| (mm)": float(np.linalg.norm(res.U[lipn], axis=1).max()),
                                  "lip gap (mm)": P.HOLD_DOWN_GAP},
                        loads_desc=dict(F_N=F_total, insert_reaction=[round(x, 2) for x in res.reactions("INSERTS")]),
                        notes="inserts bonded; the face on the side plate held normal to it (it can't lift off in this linear model)",
                        png_kw=dict(view=(1.2, 1.0, 0.9)))
    return rec


CASES = {
    "hertz": hertz_all,
    "ec_v3_lift_gear_t30": lambda: ec_case("v3", 30.0, "lift_gear", gear_limit=True),   # the largest mesh load it holds seated
    "ec_v3_stall_t0": lambda: ec_case("v3", 0.0, "stall"),
    "ec_v4_lift_t0": lambda: ec_case("v4", 0.0, "lift"),                                 # v4's only seated docked state
    "ec_v4_stall_t0": lambda: ec_case("v4", 0.0, "stall"),
    "ec_v4_modes": lambda: ec_modes("v4"),
    "cradle_v3_retract_stall": lambda: cradle_case("v3"),
    "cradle_v4_retract_stall": lambda: cradle_case("v4"),
    "cradle_v3_parked": lambda: cradle_case("v3", "parked"),
    "clevis_v3_stall": lambda: clevis_case("v3", P16_STALL, 0.0, "stall_t0"),
    "clevis_v3_backdrive": lambda: clevis_case("v3", P16_BACKDRIVE, 30.0, "backdrive_t30"),
    "latch_rail_v3_unit": lambda: latch_rail_case("v3", "unit"),
    "latch_rail_v4_tube": lambda: latch_rail_case("v4", "tube"),
    "latch_rail_v4_unit": lambda: latch_rail_case("v4", "unit"),
    "hold_down_p16_stall": lambda: hold_down_case(),
}


if __name__ == "__main__":
    which = sys.argv[1:] or list(CASES)
    for k in which:
        t0 = time.time()
        try:
            r = CASES[k]()
        except Exception as e:                       # noqa: BLE001
            print(k, "FAILED", repr(e)[:600], flush=True)
            continue
        if k == "hertz":
            print(k, json.dumps(r["worst"], default=float)[:3000], flush=True)
        else:
            print(k, json.dumps({kk: r.get(kk) for kk in ("freqs_Hz", "key_disp", "parts", "loads") if kk in r}, default=float)[:1800],
                  f"{time.time() - t0:.0f} s", flush=True)
