"""Whole frames of both carousels, with the NEMA 34 hanging off the back side plate.

What is in the model (both designs, positions from each design's placements.json):
* the two 1/4 in 6061 side plates, as cut (every hole and slot, from step/components/side_plate_*.step);
* every 2020 member as an equivalent 20 x 20 bar (materials.equivalent_bar: the bending stiffness, torsional
  stiffness and mass per length of a webbed 2020 section, from verify.py), bonded where members butt;
* each side plate joined to its two posts only at its M5 screws: a 14 mm pad (the clamped zone under a screw
  head and T-nut) bridging a 0.3 mm gap, so the plate can lift off the post between screws as a real one can
  (variant "bonded": the whole overlap glued, a stiff bound);
* the NEMA 34 as its CAD envelope (86 mm flange, 150 + 19 mm body) with its density set to 5.6 kg, bonded to
  its mount where the flange face touches it (preloaded M5s keep that joint shut: the weight moment changes
  each bolt's load by about 70 N against a few kN of preload); paternoster: the 120 mm motor plate on four
  10 mm aluminium standoffs as drawn (tubes, 5 mm bore: conservative for M6-tapped standoffs);
* four shafts (5/8 in steel) in bearing proxies (the stamped flange and the insert's hub), sprocket discs
  carrying the mass of their sprocket and their share of the loop (chains, carriages or gondolas, modules);
  paternoster: the two through shafts below and the four stub idler axles above;
* the bench: the four feet's pads held.

Load cases: gravity; gravity + chain tension + the drive in normal running; gravity + a jam at the NEMA 34's
12 N*m; a 100 N push on the top rail (sideways and along); natural frequencies with every mass on.
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

MODULE = "frame"
GAP = 0.3                       # plate-to-post gap outside the screw pads
PAD_R = 7.0                     # clamped zone round each M5 side-plate screw

EXT = None


def ext_material():
    """The 2020 equivalent bar's properties from verify.py's webbed section (A 182 mm^2, I 7502 mm^4 from the
    section; EI and GJ from CalculiX on a 100 mm length)."""
    global EXT
    if EXT is None:
        v = json.loads((fem.HERE / "out" / "verify.json").read_text())["extrusion_2020"]
        E = MAT.get("AL6063").E
        EI = E * v["Ixx_mm4"]                      # section value (the 100 mm test includes shear deflection)
        EXT = MAT.equivalent_bar("EXT2020", EI, v["GJ_fem"], v["A_mm2"] * 2.70e-9, label="2020 extrusion (equivalent bar)")
    return EXT


def add_material(key, E, nu, rho, allow, label):
    return MAT.add(MAT.Material(key, E, nu, rho, allow, label))


# --------------------------------------------------------------------------------------------- geometry helpers
def box_from_step(design, key, M):
    """World-aligned box of a 2020 member: its CAD bounding box (part frame) moved by the placement."""
    import gmsh
    lo = np.array([-10.0, -10.0, 0.0])
    L = {"ext_post": None}.get(key)
    p = fem.step_path(design, key)
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 0)
    t = gmsh.model.occ.importShapes(str(p))
    gmsh.model.occ.synchronize()
    bb = gmsh.model.getBoundingBox(-1, -1)
    gmsh.finalize()
    hi = np.array([10.0, 10.0, bb[5]])
    corners = np.array([[x, y, z, 1.0] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])])
    w = (np.asarray(M) @ corners.T).T[:, :3]
    return w.min(0), w.max(0)


def gbox(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    return lambda g: [g.model.occ.addBox(*a, *(b - a))]


def gcyl(p0, axis, r, L, r_in=0.0):
    def f(g):
        c = g.model.occ.addCylinder(*p0, *(np.asarray(axis, float) * L), r)
        if r_in > 0:
            h = g.model.occ.addCylinder(*p0, *(np.asarray(axis, float) * L), r_in)
            out, _ = g.model.occ.cut([(3, c)], [(3, h)])
            return [t for d, t in out if d == 3]
        return [c]
    return f


def gunion(*fs):
    def f(g):
        tags = []
        for ff in fs:
            tags += ff(g)
        if len(tags) == 1:
            return tags
        out, _ = g.model.occ.fuse([(3, tags[0])], [(3, t) for t in tags[1:]])
        return [t for d, t in out if d == 3]
    return f


def gcut(fa, fb):
    def f(g):
        a = fa(g)
        b = fb(g)
        out, _ = g.model.occ.cut([(3, t) for t in a], [(3, t) for t in b])
        return [t for d, t in out if d == 3]
    return f


# --------------------------------------------------------------------------------------------- the two frames
def design_data(design: str) -> dict:
    """Everything the frame model needs from a design, in world coordinates."""
    pl = fem.placements(design)
    sys.path.insert(0, str(fem.CAD / design))
    for k in ("params",):
        sys.modules.pop(k, None)
    import importlib
    P = importlib.import_module("params")
    d = dict(design=design, P=P, pl=pl)
    d["ext"] = [(p["key"], p["name"], np.array(p["M"])) for p in pl if p["key"].startswith("ext_") and
                p["key"] in ("ext_post", "ext_x", "ext_y")]
    d["plates"] = [(p["key"], np.array(p["M"])) for p in pl if p["key"] in ("side_plate_front", "side_plate_back")]
    d["motor"] = [np.array(p["M"]) for p in pl if p["key"] == "nema34"][0]
    d["feet"] = [np.array(p["M"])[:3, 3] for p in pl if p["key"] == "foot"]
    d["bearings"] = [(p["name"], np.array(p["M"])) for p in pl if p["key"] == "flange_bearing"]
    d["shafts"] = [(p["key"], p["name"], np.array(p["M"])) for p in pl if p["key"] in ("shaft", "shaft_drive", "shaft_idle")]
    d["sprockets"] = [(p["key"], p["name"], np.array(p["M"])) for p in pl if p["key"] in ("sprocket_32", "sprocket_32_idler")]
    d["idlers"] = [(p["name"], np.array(p["M"])) for p in pl if p["key"] == "idler_axle"]
    d["standoffs"] = [np.array(p["M"]) for p in pl if p["key"] == "standoff"]
    d["motor_plate"] = [np.array(p["M"]) for p in pl if p["key"] == "motor_plate"]
    d["screws"] = [np.array(p["M"])[:3, 3] for p in pl if p["name"].startswith("Side plate screw")]
    if design == "paternoster":                      # paternoster's placements carry no side-plate screws: holes
        import layout as LY                          # noqa: F401  (side_holes is cheap; layout imports cadquery)
        scr = []
        for back in (False, True):
            x_out = (P.SIDE_IN - P.PLATE_T_SIDE) if not back else (P.CHAIN_L - P.SIDE_IN + P.PLATE_T_SIDE)
            for kind, y, z, *rest in LY.side_holes(back):
                if kind == "round" and abs(abs(y) - P.POST_Y) < 0.1:
                    scr.append(np.array([x_out, y, z]))
        d["screws"] = scr
    # loop mass per sprocket (8 of them), kg
    if design == "chain-carousel-v2":
        loop = LD.V2_N_MODULES * (LD.V2_MODULE_KG + LD.V2_CARRIAGE_KG) + 2 * LD.CHAIN_KG_M * P.N_LINKS * P.P / 1000
    else:
        loop = LD.PAT_N_MODULES * LD.PAT_LOADED_KG + 2 * LD.CHAIN_KG_M * P.N_LINKS * P.P / 1000
    d["loop_kg"] = loop
    return d


def build(design: str, variant: str = "pads", h: float = 8.0, motor_refine: float = 2.5):
    """Parts list + named locations for one design's frame."""
    D = design_data(design)
    P = D["P"]
    ext_material()
    add_material("MOTOR", 70000.0, 0.3, LD.M_NEMA34 * 1e-3 / 1108.5e3, 1e9, "NEMA 34 envelope (5.6 kg)")
    add_material("BEARING", 200000.0, 0.29, 7.85e-9, 1e9, "flange bearing proxy")
    sp_kg = 0.49 + D["loop_kg"] / 8.0                 # sprocket 35BS32 (62.4 cm^3 of steel) + loop share
    parts = []
    # side plates (the CAD's own, holes and all)
    plate_x = {}
    for key, M in D["plates"]:
        parts.append(fem.Part(key, fem.step_path(design, key), M, "AL6061"))
        bb = _plate_x(design, key, M)
        plate_x[key] = bb
    # 2020 members: equivalent bars; posts pulled back from the plates by GAP (pads bridge the gap)
    names = set()
    post_side = {}                                   # plate -> (x of the face on the posts, outward sign)
    for key, name, M in D["ext"]:
        if key != "ext_post":
            continue
        a, b = box_from_step(design, key, M)
        for pk, (x0, x1) in plate_x.items():
            if abs(b[0] - x0) < 0.05:
                post_side[pk] = (x0, -1.0)
            if abs(a[0] - x1) < 0.05:
                post_side[pk] = (x1, +1.0)
    for key, name, M in D["ext"]:
        a, b = box_from_step(design, key, M)
        if key == "ext_post" and variant == "pads":
            for pk, (x0, x1) in plate_x.items():
                if abs(a[0] - x1) < 0.05:            # post's inner face on the plate's outer face (+x side)
                    a = a.copy(); a[0] += GAP
                if abs(b[0] - x0) < 0.05:
                    b = b.copy(); b[0] -= GAP
        L = b - a
        axis = int(np.argmax(L))
        ax = np.eye(3)[axis]
        other = np.eye(3)[(axis + 1) % 3]
        nm = name
        k = 2
        while nm in names:
            nm = f"{name} ({k})"; k += 1
        names.add(nm)
        parts.append(fem.Part(nm, gbox(a, b), material="EXT2020", orient=(tuple(ax), tuple(other))))
    # screw pads between the plates and the posts
    pads = []
    if variant == "pads":
        for s in D["screws"]:
            for pk, (x0, x1) in plate_x.items():
                if x0 - 1.0 <= s[0] <= x1 + 1.0:
                    xs, outward = post_side[pk]
                    p0 = (xs, s[1], s[2])
                    nm = f"pad {pk[11:]} y{s[1]:+.0f} z{s[2]:.0f}"
                    parts.append(fem.Part(nm, gcyl(p0, (outward, 0, 0), PAD_R, GAP), material="AL6063"))
                    pads.append((nm, np.array(p0)))
    # motor
    Mm = D["motor"]
    parts.append(fem.Part("NEMA 34", fem.step_path("chain-carousel-v2", "nema34"), Mm, "MOTOR"))
    if design == "paternoster":
        Mp = D["motor_plate"][0]
        parts.append(fem.Part("motor plate", fem.step_path(design, "motor_plate"), Mp, "AL6061"))
        for i, Ms in enumerate(D["standoffs"]):
            parts.append(fem.Part(f"standoff {i + 1}", fem.step_path(design, "standoff"), Ms, "AL6061"))
    # shafts, bearing proxies, sprocket discs
    for key, name, M in D["shafts"]:
        parts.append(fem.Part(name, fem.step_path(design, key), M, "STEEL1018"))
    for name, M in D["bearings"]:
        parts.append(fem.Part(name, _bearing_proxy(M, P), None, "BEARING"))
    for key, name, M in D["sprockets"]:
        parts.append(fem.Part(name, _sprocket_disc(M, P), None, "SPROCKET"))
    if design == "paternoster":
        for name, M in D["idlers"]:
            parts.append(fem.Part(name, fem.step_path(design, "idler_axle"), M, "STEEL1045"))
    # sprocket disc density: its mass + loop share over the disc's volume (pitch-diameter disc + hub, see below)
    vol = math.pi / 4 * (P.PD ** 2 - P.SHAFT_D ** 2) * P.TOOTH_W + math.pi / 4 * (P.HUB_D ** 2 - P.SHAFT_D ** 2) * (P.LTB - P.TOOTH_W)
    add_material("SPROCKET", 205000.0, 0.29, sp_kg * 1e-3 / vol, 1e9, "sprocket disc + loop mass")
    # mesh refinement: round the motor's bolts/slots and the standoffs
    refine = []
    o = Mm[:3, 3]
    if design == "chain-carousel-v2":
        for dy in (-1, 1):
            for dz in (-1, 1):
                refine.append(((o[0], o[1] + dy * P.M34_BOLT_SQ / 2, o[2] + dz * P.M34_BOLT_SQ / 2), 9.0, motor_refine))
        refine.append(((o[0], o[1], o[2]), 48.0, 4.0))
    else:
        for Ms in D["standoffs"]:
            t = Ms[:3, 3]
            refine.append(((t[0], t[1], t[2]), 8.0, motor_refine))
            refine.append(((t[0] + 79.0, t[1], t[2]), 8.0, motor_refine))
    for nm, p0 in pads:
        refine.append((tuple(p0), PAD_R + 2.0, 3.0))
    return D, parts, refine, pads


def _plate_x(design, key, M):
    import gmsh
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 0)
    t = gmsh.model.occ.importShapes(str(fem.step_path(design, key)))
    gmsh.model.occ.affineTransform(t, list(np.asarray(M)[:3, :].ravel()))
    gmsh.model.occ.synchronize()
    bb = gmsh.model.getBoundingBox(-1, -1)
    gmsh.finalize()
    return (bb[0], bb[3])


def _bearing_proxy(M, P):
    """SBSFL202-10 stand-in: the 3 mm stamped flange (81 x 58.7 mm) on the plate, and the insert's hub round
    the shaft (OD 30 mm, from IN behind the flange face to OUT in front). Part frame of the CAD bearing:
    z = shaft axis, flange's plate face at z = 0, insert outward +z."""
    B = P.BRG
    def f(g):
        fl = g.model.occ.addBox(-B["W"] / 2, -B["L"] / 2, 0.0, B["W"], B["L"], B["T"])
        hub = g.model.occ.addCylinder(0, 0, -B["IN"], 0, 0, B["IN"] + B["OUT"], 15.0)
        out, _ = g.model.occ.fuse([(3, fl)], [(3, hub)])
        tags = [t for d, t in out if d == 3]
        g.model.occ.affineTransform([(3, t) for t in tags], list(np.asarray(M)[:3, :].ravel()))
        return tags
    return f


def _sprocket_disc(M, P):
    """A sprocket as its pitch-diameter disc (tooth width) plus hub, in the CAD sprocket's frame
    (tooth plate at z in [-TOOTH_W/2, TOOTH_W/2], hub toward -z)."""
    def f(g):
        d = g.model.occ.addCylinder(0, 0, -P.TOOTH_W / 2, 0, 0, P.TOOTH_W, P.PD / 2)
        hub = g.model.occ.addCylinder(0, 0, -P.LTB + P.TOOTH_W / 2, 0, 0, P.LTB - P.TOOTH_W, P.HUB_D / 2)
        out, _ = g.model.occ.fuse([(3, d)], [(3, hub)])
        tags = [t for dd, t in out if dd == 3]
        g.model.occ.affineTransform([(3, t) for t in tags], list(np.asarray(M)[:3, :].ravel()))
        return tags
    return f


_MESH = {}


def frame_mesh(design: str, variant: str = "pads", h: float = 8.0):
    k = (design, variant, h)
    if k not in _MESH:
        D, parts, refine, pads = build(design, variant, h)
        m = fem.mesh_parts(parts, size=h, size_min=1.2, curv=8, refine=refine)
        _MESH[k] = (D, m, pads)
    return _MESH[k]


def feet_fix(d: fem.Deck, D: dict):
    m = d.m
    idx = []
    for f in D["feet"]:
        z0 = f[2] + D["P"].FOOT_H
        idx += list(m.nodes_where(lambda p: (np.abs(p[:, 2] - z0) < 0.05) & (np.hypot(p[:, 0] - f[0], p[:, 1] - f[1]) < 15.0)))
    return d.fix(idx, name="FEET")


def motor_points(D: dict):
    """Motor COM (world), its encoder end's centre, and its shaft tip, from its placement."""
    M = D["motor"]
    def w(p):
        return (M @ np.array([*p, 1.0]))[:3]
    return dict(com=w((0, 0, -80.0)), enc=w((0, 0, -169.0)), face=w((0, 0, 0)), shaft=w((0, 0, 37.0)))


def nearest(m: fem.Mesh, p, part: str | None = None):
    idx = m.nodes_of(part) if part else np.arange(m.n)
    return idx[np.argmin(np.linalg.norm(m.xyz[idx] - np.asarray(p), axis=1))]


def _shaft_patch(m, D, name, x_lo, x_hi):
    idx = m.nodes_of(name)
    return idx[(m.xyz[idx, 0] >= x_lo) & (m.xyz[idx, 0] <= x_hi)]


# --------------------------------------------------------------------------------------------- load cases
def chain_tension_loads(d: fem.Deck, D: dict, T: float):
    """Each chain pulls each of its four corner sprockets toward the loop's centre along the 45 deg diagonal
    with T * sqrt(2) (90 deg wraps); applied on the sprocket discs' nodes (spread evenly)."""
    m = d.m
    P = D["P"]
    zc = 0.5 * (P.Z_BOT + P.Z_TOP)
    for key, name, M in D["sprockets"]:
        c = M[:3, 3]
        v = np.array([0.0, -c[1], zc - c[2]])
        v /= np.linalg.norm(v)
        nodes = m.nodes_of(name)
        d.force(nodes, T * math.sqrt(2) * v)


def solve_static(design, variant, case, h=8.0):
    D, m, pads = frame_mesh(design, variant, h)
    P = D["P"]
    d = fem.Deck(m)
    feet_fix(d, D)
    d.print_reactions("FEET")
    mp = motor_points(D)
    desc = {}
    if case in ("gravity", "running", "jam"):
        d.gravity()
        desc["gravity"] = "all parts, motor 5.6 kg, loop %.2f kg on the 8 sprockets" % D["loop_kg"]
    if case in ("running", "jam"):
        T = LD.V2_TENSION_N if design == "chain-carousel-v2" else LD.PAT_TENSION_N
        chain_tension_loads(d, D, T)
        desc["chain tension"] = f"{T:.0f} N per chain"
    if case in ("running", "jam"):
        if design == "chain-carousel-v2":
            torque = LD.V2_DRIVE_NM if case == "running" else LD.NEMA34_HOLD_NM
            F = torque * 1000.0 / LD.V2_R15_MM + 10.0          # tight side + 10 N slack side
            # the drive chain pulls the motor's shaft up toward the B+ shaft and the B+ shaft down
            spm = [np.array(p["M"])[:3, 3] for p in D["pl"] if p["key"] == "sprocket_15_motor"][0]
            sps = [np.array(p["M"])[:3, 3] for p in D["pl"] if p["key"] == "sprocket_15_shaft"][0]
            nb = [n for k, n, M in D["shafts"] if "B+" in n][0]
            ib = m.nodes_of(nb)
            sh = ib[(np.abs(m.xyz[ib, 0] - sps[0]) < 9.0)]
            mo = m.nodes_of("NEMA 34")
            tip = mo[(np.abs(m.xyz[mo, 0] - spm[0]) < 9.0) & (np.hypot(m.xyz[mo, 1] - spm[1], m.xyz[mo, 2] - spm[2]) < 7.5)]
            d.force(tip, (0, 0, +F))
            d.force(sh, (0, 0, -F))
            desc["drive chain"] = f"{F:.0f} N between the 15T sprockets ({torque} N*m)"
        else:
            torque = LD.PAT_DRIVE_NM if case == "running" else LD.NEMA34_HOLD_NM
            r, q = d.rigid_patch(m.nodes_of("NEMA 34"), "MOTORBODY")
            ax = D["motor"][:3, 2]
            d.node_load(r, M=tuple(torque * 1000.0 * ax), rot=q)
            # the same torque goes out through the shaft into the chain at both bottom sprockets of the drive shaft
            name = [n for k, n, M in D["shafts"] if "drive" in n][0]
            sps = [n for k, n, M in D["sprockets"] if "+1y" in n and "bottom" in n]
            for i, sn in enumerate(sps):
                rr, qq = d.rigid_patch(m.nodes_of(sn), f"SP{i}")
                d.node_load(rr, M=tuple(-0.5 * torque * 1000.0 * ax), rot=qq)
            desc["drive torque"] = f"{torque} N*m: reaction on the motor, out through both drive sprockets"
    if case.startswith("lean"):
        d.gravity()
        nm = [n for n in m.names if n.startswith("Top rail") and "+y" in n][0]
        idx = m.nodes_of(nm)
        xm = np.median(m.xyz[idx, 0])
        sel = idx[np.abs(m.xyz[idx, 0] - xm) < 15]
        F = (0, -LD.LEAN_N, 0) if case == "lean_y" else (LD.LEAN_N, 0, 0)
        d.force(sel, F)
        desc["push"] = f"{LD.LEAN_N:.0f} N on the +y top rail's middle, {'toward -y' if case == 'lean_y' else 'toward +x'}"
    res = d.solve(f"frame/{design}_{variant}_{case}_h{h}")
    # function: motor sag and tilt, drive-chain / coupling alignment
    U = res.U
    i_com, i_enc, i_face, i_sh = (nearest(m, mp[k], "NEMA 34") for k in ("com", "enc", "face", "shaft"))
    kd = {"motor COM dz": U[i_com, 2], "motor encoder end dz": U[i_enc, 2], "motor shaft tip dz": U[i_sh, 2],
          "motor shaft tip dy": U[i_sh, 1], "motor face centre dx": U[i_face, 0]}
    ax = D["motor"][:3, 2]
    tilt = (U[i_sh] - U[i_enc]) / np.linalg.norm(mp["shaft"] - mp["enc"])
    kd["motor axis tilt (mrad, vertical plane)"] = 1000.0 * tilt[2]
    if design == "paternoster":
        name = [n for k, n, M in D["shafts"] if "drive" in n][0]
        idx = m.nodes_of(name)
        xe = m.xyz[idx, 0].max()
        end = idx[m.xyz[idx, 0] > xe - 2.0]
        u_end = U[end].mean(0)
        kd["coupling parallel offset (mm)"] = float(np.hypot(*(U[i_sh, 1:] - u_end[1:])))
    plates = [k for k, M in D["plates"]]
    fixed = d.nsets["FEET"] - 1
    excl = np.concatenate([fixed] + [m.nodes_of(n) for n, p in pads]) if pads else fixed
    rec = common.record(MODULE, f"{design}_{variant}_{case}", design=design, part="frame + NEMA 34",
                        load_case=case, res=res, parts=plates + (["motor plate"] + [f"standoff {i}" for i in range(1, 5)]
                                                                  if design == "paternoster" else []),
                        exclude=excl, exclude_r=4.0, key_disp=kd, loads_desc=desc,
                        notes=f"plate-to-post joint: {variant}", extra=dict(feet_reaction_N=res.reactions("FEET").tolist(),
                                                                             total_mass_kg=round(m.mass() * 1000, 3)),
                        png_kw=dict(field="vm", view=(1.2, -1.0, 0.6) if design == "paternoster" else (1.2, -1.0, 0.6),
                                    clim=None))
    return rec


def solve_modes(design, variant="pads", h=8.0, n=12):
    D, m, pads = frame_mesh(design, variant, h)
    d = fem.Deck(m)
    feet_fix(d, D)
    d.frequency(n)
    res = d.solve(f"frame/{design}_{variant}_modes_h{h}")
    out = dict(module=MODULE, case=f"{design}_{variant}_modes", design=design, part="frame + NEMA 34", load_case="modes",
               freqs_Hz=[round(f, 2) for f in res.freqs], nodes=int(m.n), elements=int(len(m.tet)),
               total_mass_kg=round(m.mass() * 1000, 3), wall_s=round(res.wall, 1), notes=f"plate-to-post joint: {variant}")
    # what moves in each mode: share of kinetic energy (mass-weighted |u|^2) by part
    vol = m.volumes()
    rho = np.array([MAT.get(mt).rho for mt in m.materials])[m.part]
    nm = np.zeros(m.n)
    np.add.at(nm, m.tet[:, :4].ravel(), np.repeat(vol * rho / 4.0, 4))
    shares = []
    for U in res.modes[:n]:
        e = nm * (U ** 2).sum(1)
        tot = e.sum()
        per = {}
        for ip, name in enumerate(m.names):
            idx = np.unique(m.tet[m.part == ip, :4])
            g = _group(name)
            per[g] = per.get(g, 0.0) + e[idx].sum() / tot
        dom = sorted(per.items(), key=lambda kv: -kv[1])[:3]
        u = U / np.abs(U).max()
        dirn = np.abs((nm[:, None] * U ** 2).sum(0))
        shares.append(dict(top=[(k, round(v, 2)) for k, v in dom], direction="xyz"[int(np.argmax(dirn))]))
    out["modes"] = shares
    d_out = common.OUT / MODULE
    d_out.mkdir(parents=True, exist_ok=True)
    for i in range(min(4, len(res.modes))):
        fem.render(res, d_out / f"{design}_{variant}_mode{i + 1}.png", field="u", mode=i,
                   title=f"{design}: mode {i + 1}, {res.freqs[i]:.1f} Hz", view=(1.2, -1.0, 0.6))
    out["png"] = [f"out/{MODULE}/{design}_{variant}_mode{i + 1}.png" for i in range(min(4, len(res.modes)))]
    (d_out / f"{design}_{variant}_modes.json").write_text(json.dumps(out, indent=1))
    try:
        mode_gif(res, d_out / f"{design}_{variant}_mode1.gif", 0, f"{design}: mode 1, {res.freqs[0]:.1f} Hz")
        out["gif"] = f"out/{MODULE}/{design}_{variant}_mode1.gif"
        (d_out / f"{design}_{variant}_modes.json").write_text(json.dumps(out, indent=1))
    except Exception as e:                                # noqa: BLE001
        out["gif_error"] = str(e)[:200]
    return out


def _group(name: str) -> str:
    n = name.lower()
    for k in ("nema 34", "motor plate", "standoff", "side_plate", "post", "rail", "shaft", "sprocket", "idler", "bearing", "pad"):
        if k in n:
            return {"side_plate": "side plates", "post": "posts", "rail": "rails"}.get(k, k)
    return name


def mode_gif(res, path, i, title, frames=24):
    import imageio.v2 as imageio
    import pyvista as pv
    m = res.deck.m
    U = res.modes[i]
    L = float(np.ptp(m.xyz, axis=0).max())
    s0 = 0.05 * L / np.abs(U).max()
    imgs = []
    g0 = fem.grid(m)
    edges0 = g0.extract_surface(algorithm="dataset_surface").extract_feature_edges(35)
    umag = np.linalg.norm(U, axis=1)
    for k in range(frames):
        s = s0 * math.sin(2 * math.pi * k / frames)
        g = fem.grid(m, U, s)
        g["v"] = umag / umag.max()
        pl = pv.Plotter(off_screen=True, window_size=(900, 700))
        pl.set_background("white")
        pl.add_mesh(edges0, color="#b0b4b8", line_width=1, opacity=0.5)
        surf = g.extract_surface(algorithm="dataset_surface")
        pl.add_mesh(surf, scalars="v", cmap="viridis", clim=(0, 1), show_scalar_bar=False, smooth_shading=True)
        c = m.xyz.mean(0)
        v = np.array([1.2, -1.0, 0.6])
        pl.camera.focal_point = c
        pl.camera.position = c + v / np.linalg.norm(v) * L * 2.2
        pl.camera.up = (0, 0, 1)
        pl.reset_camera()
        pl.add_text(title, position="upper_left", font_size=11, color="black")
        imgs.append(pl.screenshot(return_img=True))
        pl.close()
    imageio.mimsave(path, imgs, duration=0.06, loop=0)


CASES = {}
for _d in ("chain-carousel-v2", "paternoster"):
    for _c in ("gravity", "running", "jam", "lean_y", "lean_x"):
        CASES[f"{_d}_pads_{_c}"] = (lambda d=_d, c=_c: solve_static(d, "pads", c))
    CASES[f"{_d}_bonded_gravity"] = (lambda d=_d: solve_static(d, "bonded", "gravity"))
    CASES[f"{_d}_pads_modes"] = (lambda d=_d: solve_modes(d, "pads"))
    CASES[f"{_d}_bonded_modes"] = (lambda d=_d: solve_modes(d, "bonded"))


if __name__ == "__main__":
    import time
    which = sys.argv[1:] or list(CASES)
    for k in which:
        t0 = time.time()
        r = CASES[k]()
        print(k, json.dumps({kk: r.get(kk) for kk in ("freqs_Hz", "key_disp", "parts") if kk in r}, default=float)[:1500],
              f"{time.time() - t0:.0f} s", flush=True)
