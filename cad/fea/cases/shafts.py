"""Shafts and axles: the four 5/8 in corner shafts of chain carousels v3 and v4 (v2's shafts, bearings and sprockets), the
paternoster's two bottom shafts and its four stub idler axles.

Corner shafts: CalculiX solid (C3D10) of the round 1018 shaft. The two SBSFL202-10 inserts are self-aligning, so each is a
pin support: a rigid ring of the shaft's surface over the insert's race (12 mm) whose reference node is held in translation
only (axially at the front bearing only). Each sprocket loads the shaft through a rigid patch over its bore, reference node on
the tooth plane: the two chain spans' tensions, and on the drive shaft the 15T's pull and the torque. Beam theory
(simply supported, point loads) checks the FEA. The keyway (3/16 x 3/32 in along the whole shaft) is not meshed: it enters
through Peterson's stress concentration factors for an end-milled keyseat (bending 2.14, torsion 2.62 at r/d 0.021) in the
fatigue check, since a shaft turning under a fixed load sees fully reversed bending every revolution.

Chain spans per chain (frictionless sprockets): the bottom run at the set tension T; each side run picks up its own weight
going up; the runs' weights are split by their links (straight links plus half of each adjacent 8-link wrap).

Stub idler axles (paternoster): the CAD's axle (15 mm seat, 22 mm shoulder, M10 stem) clamped by its nut: the shoulder's
face on the plate held, the two 6202s' loads as cosine bearing pressures on the seat, split by the lever rule about the
idler's tooth plane.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import fem  # noqa: E402
import loads as LD  # noqa: E402
import materials as MAT  # noqa: E402
from cases import common  # noqa: E402

MODULE = "shafts"
G = LD.G_MS2
R15 = LD.V2_R15_MM
SLACK_N = 10.0                      # drive chain's slack side
RACE_W = 12.0                       # insert bearing race width carried as the pin support
KT_BEND, KT_TORS = 2.14, 2.62       # Peterson, end-milled keyseat in bending / torsion (r/d 0.021)
Q_NOTCH = 0.65                      # notch sensitivity of 1018 at a 0.33 mm keyseat fillet (Peterson's chart)
SUT_1018 = 440.0                    # MPa, 1018 cold drawn


def design_params(design: str):
    import importlib
    sys.path.insert(0, str(fem.CAD / design))
    sys.modules.pop("params", None)
    P = importlib.import_module("params")
    sys.path.pop(0)
    return P


def spans(design: str, P) -> dict:
    """Per-chain span tensions (N) and run weights for a design's loop."""
    if design.startswith("chain-carousel"):
        mod, car = {"chain-carousel-v3": (LD.V3_MODULE_KG, LD.V3_CARRIAGE_KG),
                    "chain-carousel-v4": (LD.V4_MODULE_KG, LD.V4_CARRIAGE_KG)}[design]
        W_chain = 0.5 * (LD.V2_N_MODULES * (mod + car)) * G + LD.CHAIN_KG_M * P.N_LINKS * P.P / 1000 * G
        Wf = Wb = W_chain
        T = LD.V2_TENSION_N
    else:
        W_g = LD.PAT_N_MODULES * LD.PAT_LOADED_KG * G
        chain = LD.CHAIN_KG_M * P.N_LINKS * P.P / 1000 * G
        Wf, Wb = LD.PAT_FRONT_SHARE * W_g + chain, (1 - LD.PAT_FRONT_SHARE) * W_g + chain
        W_chain = Wf
        T = LD.PAT_TENSION_N
    wrap = P.N_TEETH / 4
    n = P.N_LINKS

    def runs(W):
        return dict(bottom=W * (P.LOOP_M + wrap) / n, side=W * (P.LOOP_N + wrap) / n, top=W * (P.LOOP_M + wrap) / n)
    return dict(T=T, front=runs(Wf), back=runs(Wb), W_chain=W_chain)


def corner_force(corner: str, ysign: float, T: float, w: dict, extra: float = 0.0, tight: str = "bottom") -> np.ndarray:
    """Force (y, z) the chain puts on a corner sprocket; ysign = the corner's side (+1 at +y). extra: added tension in the
    `tight` span (drive torque)."""
    inward = -ysign
    if corner == "bottom":
        Tb = T + (extra if tight == "bottom" else 0.0)
        Ts = T + (extra if tight == "side" else 0.0)
        return np.array([0.0, inward * Tb, Ts - w["bottom"] / 2])
    Ts = T + w["side"]
    return np.array([0.0, inward * Ts, -Ts - w["top"] / 2])


# --------------------------------------------------------------------------------------------- corner shafts (solid)
def shaft_mesh(x0: float, x1: float, y0: float, z0: float, d: float, refine_x: list, h: float = 3.0):
    def geo(g):
        return [g.model.occ.addCylinder(x0, y0, z0, x1 - x0, 0, 0, d / 2)]
    ref = [((x, y0, z0), 10.0, 1.4) for x in refine_x]
    return fem.mesh_parts([fem.Part("shaft", geo, material="STEEL1018")], size=h, size_min=1.0, curv=14, refine=ref)


def ring(m, x_lo, x_hi, y0, z0, r):
    idx = np.arange(m.n)
    p = m.xyz
    rr = np.hypot(p[:, 1] - y0, p[:, 2] - z0)
    return idx[(p[:, 0] >= x_lo) & (p[:, 0] <= x_hi) & (rr > r - 0.02)]


def beam_check(x_b: list, loads: list, d: float) -> dict:
    """Simply supported beam (bearings at x_b), point loads (x, Fy, Fz): reactions and the peak bending moment."""
    xa, xb = x_b
    L = xb - xa
    out = {}
    Mmax, xm = 0.0, None
    xs = sorted({xa, xb, *[l[0] for l in loads]} | set(np.linspace(min(xa, *[l[0] for l in loads]), max(xb, *[l[0] for l in loads]), 400)))
    Rb = np.zeros(2)
    for x, Fy, Fz in loads:
        Rb += np.array([Fy, Fz]) * (x - xa) / L
    Ra = -np.sum([[l[1], l[2]] for l in loads], axis=0) + Rb
    Rb = -Rb
    for x in xs:
        M = np.zeros(2)
        if x > xa:
            M += Ra * (x - xa)
        if x > xb:
            M += Rb * (x - xb)
        for xl, Fy, Fz in loads:
            if x > xl:
                M += np.array([Fy, Fz]) * (x - xl)
        mm = float(np.hypot(*M))
        if mm > Mmax:
            Mmax, xm = mm, x
    Z = math.pi * d ** 3 / 32
    out.update(R_front_N=np.round(Ra, 2).tolist(), R_back_N=np.round(Rb, 2).tolist(), M_max_Nmm=round(Mmax, 1), at_x=round(xm, 1),
               sigma_nominal_MPa=round(Mmax / Z, 2))
    return out


def fatigue(sig_a: float, tau_m: float, d: float) -> dict:
    """Shigley: Marin-corrected endurance limit, keyseat Kf, DE-Goodman safety factor (bending fully reversed, torsion steady)."""
    ka = 4.51 * SUT_1018 ** -0.265          # machined
    kb = 1.24 * d ** -0.107
    ke = 0.814                              # 99 % reliability
    Se = 0.5 * SUT_1018 * ka * kb * ke
    Kf = 1 + Q_NOTCH * (KT_BEND - 1)
    Kfs = 1 + Q_NOTCH * (KT_TORS - 1)
    sa = Kf * sig_a
    sm = math.sqrt(3) * Kfs * tau_m
    n = 1.0 / (sa / Se + sm / SUT_1018) if (sa + sm) > 0 else float("inf")
    return dict(Se_MPa=round(Se, 1), Kf=round(Kf, 2), Kfs=round(Kfs, 2), sigma_a_MPa=round(sa, 2), sigma_m_MPa=round(sm, 2), n_goodman=round(n, 2))


def corner_shaft(design: str, which: str, case: str) -> dict:
    """which: 'B+' (drive), 'B-', 'T+', 'T-' (v3/v4) or 'drive' / 'idle' (paternoster bottom shafts)."""
    P = design_params(design)
    pl = fem.placements(design)
    S = spans(design, P)
    if design.startswith("chain-carousel"):
        sh = [p for p in pl if p["key"] in ("shaft", "shaft_drive") and f"Shaft {which} " in p["name"]][0]
    else:
        sh = [p for p in pl if p["key"] in ("shaft_drive", "shaft_idle") and ("drive" in p["name"]) == (which == "drive")][0]
    M = np.array(sh["M"])
    o = M[:3, 3]
    y0, z0 = o[1], o[2]
    import gmsh
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 0)
    gmsh.model.occ.importShapes(str(fem.step_path(design, sh["key"])))
    gmsh.model.occ.synchronize()
    Lsh = gmsh.model.getBoundingBox(-1, -1)[5]
    gmsh.finalize()
    x0, x1 = o[0], o[0] + Lsh
    near = lambda p: abs(p[1] - y0) < 1 and abs(p[2] - z0) < 1          # noqa: E731
    brg = [np.array(p["M"]) for p in pl if p["key"] == "flange_bearing" and near(np.array(p["M"])[:3, 3])]
    xb = sorted(B[0, 3] + B[:3, 2][0] * (P.BRG["OUT"] - P.BRG["IN"]) / 2 for B in brg)
    sps = [(p["name"], np.array(p["M"])) for p in pl if p["key"] in ("sprocket_32",) and near(np.array(p["M"])[:3, 3])]
    ysign = math.copysign(1.0, y0)
    corner = "bottom" if (design.startswith("chain") and which.startswith("B")) or not design.startswith("chain") else "top"
    torque = (LD.V2_DRIVE_NM if design.startswith("chain") else LD.PAT_DRIVE_NM) if case == "running" else LD.NEMA34_HOLD_NM
    is_drive = (which == "B+") or (which == "drive")
    loads_pt = []                                                          # (x, F (3,), Mx, x_lo, x_hi)
    tight = "side" if case.endswith("_side") else "bottom"
    for name, Ms in sps:
        xs = Ms[0, 3]
        hub_dir = -Ms[:3, 2][0]                                            # the hub runs toward -z of the sprocket frame
        lo, hi = sorted((xs + Ms[:3, 2][0] * P.TOOTH_W / 2, xs + hub_dir * (P.LTB - P.TOOTH_W / 2)))
        w = S["front"] if xs < 150 else S["back"]
        extra = 0.5 * torque * 1000.0 / P.R if is_drive else 0.0
        F = corner_force(corner, ysign, S["T"], w, extra, tight)
        Mx = -0.5 * torque * 1000.0 if is_drive else 0.0
        loads_pt.append((xs, F, Mx, lo, hi, name))
    if is_drive and torque > 0:
        if design.startswith("chain"):
            s15 = [np.array(p["M"]) for p in pl if p["key"] == "sprocket_15_shaft"][0]
            xs = s15[0, 3]
            lo, hi = sorted((xs + s15[:3, 2][0] * 2.0, xs - s15[:3, 2][0] * (P.LTB15 - 2.0)))
            F = np.array([0.0, 0.0, -(torque * 1000.0 / R15 + 2 * SLACK_N)])
            loads_pt.append((xs, F, torque * 1000.0, lo, hi, "15T drive sprocket"))
        else:
            loads_pt.append((x1 - 8.0, np.zeros(3), torque * 1000.0, x1 - 16.0, x1, "jaw coupling"))
    m = shaft_mesh(x0, x1, y0, z0, P.SHAFT_D, xb + [l[0] for l in loads_pt])
    d = fem.Deck(m)
    rad = P.SHAFT_D / 2
    for i, x in enumerate(xb):
        r, q = d.rigid_patch(ring(m, x - RACE_W / 2, x + RACE_W / 2, y0, z0, rad), f"BRG{i}", at=(x, y0, z0))
        d.fix_ids([r], dofs=(1, 2, 3) if i == 0 else (2, 3), name=f"PIN{i}")
    held_rot = False
    for k, (xs, F, Mx, lo, hi, name) in enumerate(loads_pt):
        r, q = d.rigid_patch(ring(m, lo, hi, y0, z0, rad), f"LD{k}", at=(xs, y0, z0))
        if Mx != 0 and not held_rot and name.startswith("Sprocket"):
            d.fix_ids([q], dofs=(1,), name="TORQ")                         # this sprocket reacts the torque
            held_rot = True
            d.node_load(r, F=tuple(F))
        else:
            d.node_load(r, F=tuple(F), M=(Mx, 0, 0) if Mx else None, rot=q)
    if not held_rot:
        r0 = [rr for (nn, rr, qq) in d.rigid if nn == "BRG0"][0]
        q0 = [qq for (nn, rr, qq) in d.rigid if nn == "BRG0"][0]
        d.fix_ids([q0], dofs=(1,), name="TORQ")
    d.gravity()
    res = d.solve(f"{MODULE}/{design}_{which}_{case}")
    # function: deflection at each sprocket's tooth plane, slope at the bearings
    kd = {}
    for k, (xs, F, Mx, lo, hi, name) in enumerate(loads_pt):
        u = res.rigid_disp(f"LD{k}")
        kd[f"{name}: deflection (mm)"] = float(np.hypot(u[1], u[2]))
    for i, x in enumerate(xb):
        u = res.rigid_disp(f"BRG{i}")
        kd[f"bearing {i + 1} slope (mrad)"] = 1000.0 * float(np.hypot(u[4], u[5]))
    bl = [(l[0], l[1][1], l[1][2]) for l in loads_pt]
    bc = beam_check(xb, bl, P.SHAFT_D)
    excl = np.concatenate([d.nsets[n] - 1 for n in d.nsets if n.startswith(("BRG", "LD"))])
    vm_x, at = res.vm_max("shaft", exclude=excl, exclude_r=2.5)
    tau = 16 * torque * 1000.0 / (math.pi * P.SHAFT_D ** 3) if is_drive else 0.0
    fat = fatigue(bc["sigma_nominal_MPa"], tau, P.SHAFT_D)
    rec = common.record(MODULE, f"{design}_{which}_{case}", design=design, part=f"shaft {which}", load_case=case, res=res,
                        exclude=excl, exclude_r=2.5, key_disp=kd,
                        loads_desc={l[5]: f"F (y, z) = ({l[1][1]:.1f}, {l[1][2]:.1f}) N, Mx = {l[2] / 1000:.2f} N*m" for l in loads_pt},
                        extra=dict(beam=bc, fatigue=fat, torsion_nominal_MPa=round(tau, 2), bearings_x=[round(v, 2) for v in xb]),
                        notes="pin-supported at the insert bearings; keyway through Kt (not meshed)",
                        png_kw=dict(field="vm", view=(0.3, -1.0, 0.5), zoom=1.6, size=(1600, 700)))
    return rec


# --------------------------------------------------------------------------------------------- paternoster stub idler axles
def idler_axle(case: str = "running", where: str = "front +1y") -> dict:
    design = "paternoster"
    P = design_params(design)
    pl = fem.placements(design)
    S = spans(design, P)
    ax = [p for p in pl if p["key"] == "idler_axle" and p["name"].endswith(where)][0]
    M = np.array(ax["M"])
    m = fem.mesh_parts([fem.Part("idler axle", fem.step_path(design, "idler_axle"), None, "STEEL1045")], size=1.6, size_min=0.5, curv=16)
    # axle frame: z along the axle (shoulder face z = 0 on the plate's inner face, seat toward +z)
    brs = sorted((np.linalg.inv(M) @ np.array([*np.array(p["M"])[:3, 3], 1.0]))[2] for p in pl
                 if p["key"] == "bearing_6202" and p["name"].startswith(f"6202-2RS {where}"))
    sp = [np.array(p["M"]) for p in pl if p["key"] == "sprocket_32_idler" and p["name"].endswith(where)][0]
    z_tooth = (np.linalg.inv(M) @ np.array([*sp[:3, 3], 1.0]))[2]
    # 6202: 11 mm wide, placed by its centre (the outer one ends at the circlip groove, z 32.7)
    seats = [(b - 5.5, b + 5.5) for b in brs]
    cen = [0.5 * (a + b) for a, b in seats]
    w = S["front"] if "front" in where else S["back"]
    ysign = 1.0 if "+1y" in where else -1.0
    F_world = corner_force("top", ysign, S["T"], w)
    Rw = M[:3, :3]
    F_loc = Rw.T @ F_world
    # lever rule about the tooth plane
    a, b = cen
    fa = (b - z_tooth) / (b - a)
    shares = [fa, 1 - fa]
    d = fem.Deck(m)
    fix = m.nodes_where(lambda p: (np.abs(p[:, 2]) < 1e-3) & (np.hypot(p[:, 0], p[:, 1]) > 5.0 - 1e-3))
    stem = m.nodes_where(lambda p: (p[:, 2] < 0) & (p[:, 2] > -P.PLATE_T_SIDE) & (np.hypot(p[:, 0], p[:, 1]) > 4.9))
    d.fix(np.concatenate([fix, stem]), name="CLAMP")
    d.print_reactions("CLAMP")
    for (lo, hi), s in zip(seats, shares):
        faces = m.faces_where(lambda c, n, lo=lo, hi=hi: (lo <= c[2] <= hi) and abs(np.hypot(c[0], c[1]) - 7.5) < 0.3)
        d.bearing(faces, F_loc * s, (0, 0, 0), (0, 0, 1))
    res = d.solve(f"{MODULE}/pat_idler_{where.replace(' ', '_')}_{case}")
    u_tip = res.umag()[np.argmax(m.xyz[:, 2])]
    Fm = float(np.linalg.norm(F_world))
    # hand: cantilever at the shoulder, load at the tooth plane: sigma = F z / (pi d^3 / 32) at the 15 mm seat's root
    sig_hand = Fm * (z_tooth - 4.0) / (math.pi * 15.0 ** 3 / 32)      # the 15 mm seat starts at the 4 mm shoulder
    excl = d.nsets["CLAMP"] - 1
    rec = common.record(MODULE, f"paternoster_idler_{where.replace(' ', '_')}_{case}", design=design,
                        part=f"idler axle {where}", load_case=case, res=res, exclude=excl, exclude_r=1.0,
                        key_disp={"axle end deflection (mm)": float(u_tip)},
                        loads_desc={"chain on the idler": f"{Fm:.1f} N (world y, z = {F_world[1]:.1f}, {F_world[2]:.1f})",
                                    "bearing shares": [round(s, 3) for s in shares]},
                        extra=dict(hand_sigma_root_MPa=round(sig_hand, 2), tooth_plane_z=round(float(z_tooth), 2),
                                   seats=[[round(v, 2) for v in s] for s in seats], clamp_reaction_N=res.reactions("CLAMP").tolist()),
                        notes="shoulder face and stem held (nut preload); 6202 loads as cosine pressures",
                        png_kw=dict(field="vm", view=(1.0, -1.0, 0.6), zoom=1.3))
    return rec


# --------------------------------------------------------------------------------------------- printed tensioner block
def tensioner_block(design: str = "chain-carousel-v3", material: str = "PETG_CREEP") -> dict:
    """The printed jack block under each top bearing (parts.tensioner_block): if the bearing's two flange bolts slip, its jack
    screw carries the top corner's whole vertical chain load, through the trapped M5 nut into the block and out through its
    two M5 screws into the plate. Block frame: x across (world y), y up, its back face (on the plate) at z = 0."""
    P = design_params(design)
    S = spans(design, P)
    F_top = -corner_force("top", 1.0, S["T"], S["front"])[2]              # N, down, at one top sprocket
    # the front bearing carries the front sprocket's load times its share of the span (sprocket at x 0, bearings 387.8 apart)
    xa, xb = -41.4, 346.4
    F = F_top * (xb - 0.0) / (xb - xa) + F_top * (xb - 305.0) / (xb - xa)  # and the back sprocket's small share
    m = fem.mesh_parts([fem.Part("tensioner block", fem.step_path(design, "tensioner_block"), None, material)], size=1.2,
                       size_min=0.4, curv=12)
    d = fem.Deck(m)
    # held: the M5 screws' heads (counterbore floors, z = 4) and shanks, and the back face round each screw (clamped)
    held = m.nodes_where(lambda q: ((np.hypot(q[:, 0] - 10, q[:, 1] + 12) < 4.85) | (np.hypot(q[:, 0] + 10, q[:, 1] + 12) < 4.85))
                         & ((np.abs(q[:, 2] - 4.0) < 1e-3) | (q[:, 2] < 1e-3) |
                            ((np.minimum(np.hypot(q[:, 0] - 10, q[:, 1] + 12), np.hypot(q[:, 0] + 10, q[:, 1] + 12)) < 2.8) & (q[:, 2] < 4.0))))
    d.fix(held, name="SCREWS")
    d.print_reactions("SCREWS")
    nut = m.faces_where(lambda c, n: abs(c[1] - (-6.2 - 2.7)) < 0.05 and n[1] > 0.9 and abs(c[0]) < 4.8 and c[2] > 1.5)
    d.traction(nut, (0.0, -F, 0.0))
    res = d.solve(f"{MODULE}/{design}_tensioner_{material}")
    excl = d.nsets["SCREWS"] - 1
    vm, at = res.vm_max("tensioner block", exclude=excl, exclude_r=0.8)
    nut_n = np.unique(np.concatenate([f[2] for f in nut]))
    rec = common.record(MODULE, f"{design}_tensioner_block_{material}", design=design, part="tensioner block (printed)",
                        load_case="top bearing's flange bolts slipped: the jack screw carries it", res=res, exclude=excl, exclude_r=0.8,
                        key_disp={"nut seat drop (mm)": float(np.abs(res.U[nut_n, 1]).mean())},
                        loads_desc={"jack screw": f"{F:.1f} N down on the nut's seat"},
                        extra=dict(screw_reaction_N=res.reactions("SCREWS").tolist()),
                        notes="sustained (chain tension): PETG creep modulus and allowable",
                        png_kw=dict(field="vm", view=(0.6, -0.4, 1.0), up=(0, 1, 0), zoom=1.2))
    return rec


CASES = {}
for _d, _ws in (("chain-carousel-v3", ("B+", "B-", "T+", "T-")), ("chain-carousel-v4", ("B+", "T+")), ("paternoster", ("drive", "idle"))):
    for _w in _ws:
        for _c in ("running", "jam") if _w in ("B+", "drive") else ("running",):
            CASES[f"{_d}_{_w}_{_c}"] = (lambda d=_d, w=_w, c=_c: corner_shaft(d, w, c))
    if _d == "chain-carousel-v3":
        CASES[f"{_d}_B+_jam_side"] = (lambda d=_d: corner_shaft(d, "B+", "jam_side"))
CASES["paternoster_idler_front"] = lambda: idler_axle("running", "front +1y")
CASES["paternoster_idler_back"] = lambda: idler_axle("running", "back +1y")
CASES["chain-carousel-v3_tensioner"] = lambda: tensioner_block("chain-carousel-v3", "PETG_CREEP")


if __name__ == "__main__":
    import time
    which = sys.argv[1:] or list(CASES)
    for k in which:
        t0 = time.time()
        r = CASES[k]()
        print(k, json.dumps({kk: r.get(kk) for kk in ("key_disp", "beam", "fatigue")}, default=float)[:900],
              [(p["part"], p["vm_excl_MPa"], p["sf"]) for p in r["parts"]], f"{time.time() - t0:.0f} s", flush=True)
