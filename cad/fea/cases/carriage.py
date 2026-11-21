"""The printed carriages of chain carousel v3 and v4 and the joints that hold the module on them.

    python cases/carriage.py [case ...]        -> out/carriage/<case>.json, .png
    python cases/carriage.py hand              -> out/carriage/hand_checks.json (closed-form checks of pins, keepers, seats)
    python cases/carriage.py table             -> the raw case table at the end of out/carriage/SUMMARY.md (its findings
                                                  and the curated table above it are written by hand from these)

Every model is in the carriage's own frame (the frame the CAD draws it in): X = u along the travel, Y = w radially
inward (into the loop), Z = x front -> back, origin on the front chain's pitch line between the A-1 link's pins.
Sam's module frame maps to it as x_c = x_s + HINGE_X and (v3) u = y_s, w = z_s + 11.65; (v4) u = -y_s, w = -29.35 - z_s.

What holds a carriage, and how it is modelled:
* the two A-1 tabs, one M3 x 12 each (plate -> tab -> nylon locknut in the printed hook): the screw's bore, the
  tab's 7.9 x 9.3 mm footprint on the plate's inner face and the screw head's counterbore floor are one rigid patch
  per tab. The patch's centre is held in translation. Its rotation about u (the carriage bending along the
  augers) goes into a 1.27 mm steel tab, a semi-rigid joint: a rotational spring of E*I/L = 200 GPa * (7.9 *
  1.27^3 / 12) / 4.5 mm = 6.0e4 N*mm/rad (4.5 mm of free tab between its bend and the hole). Rotation about w (tab
  in its own plane) is held. Roll about x (the chain articulates) is held at the front tab only, as the v2 loop
  simulation did (front rigid, back a ball joint), so the carriage is not a mechanism.
* at the station the hold-down lips 2 mm over both tongues (|u| <= 13 flat, the full tongue length): when the P16
  pushes, the carriage lifts the 2 mm and the lips take the push. The chain lets the tabs move radially at about
  2.8 N/mm per chain on the bottom run (80 N tension, 57 mm to each sprocket), so the tabs are held along u and x only.
* at the loading position the side tabs: lip (v3, 2 mm inside the tongue) or foot (v4, 1 mm outside it) over the
  tongue's -u 8 mm (u -20..-12), x_c -23..-9 front and 314..328 back.

The module (plate + auger + powder + door + dock parts) is a rigid body; its weight and the hand and actuator loads
reach the carriage through its real contacts, statically: the hinge pin in the two lugs (a cosine bearing pressure on
each lug's 2.2 mm of bore), the plate's back corners on the two pads (v3, the module right side up), and the latch
(v3: the bolt in its housing slot; v4: the 4 mm pin in its housing bore), each latch reaction split into the
housing's front-edge bearing and the tail's prying reaction by the bolt's own lever.

Materials: PETG short-term (E 1810 MPa, allowable 23 MPa: across-layer strength) for the hand and actuator
cases; PETG creep (E 1000 MPa, allowable 8 MPa) for gravity, which a module parked in the loop carries for days.
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

MODULE = "carriage"
DESIGNS = {"v3": "chain-carousel-v3", "v4": "chain-carousel-v4"}

# --- geometry (params.py of v3/v4; carriage frame) --------------------------------------------------------------
A1_X = (9.525, 305.0 - 9.525)        # A-1 tab holes (A1_HOLE_C from each chain)
A1_FOOT = ((4.96, 14.3), (290.7, 300.04))   # tab on the plate's inner face: chain's outer plate (OUTER_W / 2) -> X = 14.3
A1_HALF_W = 3.95                     # N = 7.9 mm
W1, W0 = -6.35, -11.35               # plate's inner (CAR_W0) and outer faces
HINGE_X = 33.0
HINGE_W = {"v3": 11.65, "v4": -29.35}
LUG_U = {"v3": 25.5, "v4": 26.0}     # lug inner faces (|u|), 4 mm thick, the outer 1.8 mm a counterbore for the pin head
LUG_T, BORE_L = 4.0, 2.2
PIN_R = (5.0 + 0.15) / 2
TONGUES = ((-23.0, -7.0), (312.0, 328.0))   # tongue x_c ranges (hold-down lips cover them fully, |u| <= 13 flat)
SIDE_TAB_U = (-20.0, -12.0)                 # side tabs over the tongue's -u 8 mm
SIDE_TAB_X = ((-23.0, -9.0), (314.0, 328.0))

# --- the module, from the exported STEP parts (massprops in the parent's notes) ------------------------------------
# v3: plate v3 33.6 g at Sam x 53.4; armature 10.4 g at 105.8; armature screws + inserts 1.4 g; dock balls 2.1 g at 30;
#     door housing + shutter + spring + M2 screws 3.4 g at the outlet; auger 66.2 g at 103.4; cap 5.4 g at 241.4 (v2 sim
#     masses); 100 g of powder at 126.3, -4.1 (backed out of the v2 sim's module COM, 107.5, 0, -4.4, with its masses).
# v4: plate v4 35.5 g, dock balls 2.1 g, flat washer 0.4 g, door 3.2 g, no armature; the same auger, cap and powder.
MOD_KG = {"v3": 0.2224, "v4": 0.2129}
MOD_X = {"v3": 107.4, "v4": 107.2}   # COM along the auger from the hinge (Sam x)
MOD_ZS = {"v3": -4.6, "v4": -4.4}    # COM height in Sam z (above the plate's underside by 13.4)
PINS_KG = 0.0061                     # two 5 mm hinge pins + e-clips, carried straight by the lugs
LATCH_XS = {"v3": 101.5, "v4": 104.0}   # latch reaction on the keeper (v3 bolt lap 100-103; v4 pin in the hole 102-106)
PAD_X = (123.5, 136.0)               # v3 pads under the plate's back corners (Sam x 90.5 to the plate's end at 103)
PAD_U = (15.5, 23.5)
# latch bolt lever: tip load at LATCH_XS; front bearing at the housing's mouth, tail bearing near the bolt's end (Sam x)
LATCH_FRONT = {"v3": (105.5, 108.5), "v4": (106.5, 109.5)}
LATCH_TAIL = {"v3": (120.0, 123.0), "v4": (121.0, 124.0)}
LATCH_U = {"v3": -19.0, "v4": -19.0}            # bolt / pin centre in u (v4: Sam y +19 -> u -19)
LATCH_SLOT_W = {"v3": (-1.15, 2.25)}            # v3 slot floor and ceiling (w)
LATCH_BORE = {"v4": (-15.85, 2.15)}             # v4 pin bore axis (w) and radius

# --- loads --------------------------------------------------------------------------------------------------------
DYN = LD.V2_HOOK_MAX_N / LD.V2_HOOK_STATIC_N    # 1.27: loop-sim peak / static latch demand at 100 mm/s (v2 hooks)
P16_N = LD.P16_MAX_N                            # 50 N stall, all of it through the hinge (the module blocked near it)
PULL_N = 2.0 * LD.HAND_N                        # 40 N: pulling an auger off its plate at the loading position
PULL_XS = 101.5                                 # ... applied at the latch: the latch takes all of it (worst for the latch);
                                                # pulled at mid-plate (x 50) the hinge and latch share it about equally
K_TAB_ROT = 200000.0 * (7.9 * 1.27 ** 3 / 12.0) / 4.5   # 6.0e4 N*mm/rad
H = 2.2                                         # element size: 2+ quadratic tets through the 4-5 mm walls


V4_BRIDGE = (-33.0, -25.0, -20.85, -11.35, 139.5, 171.0)   # u0, u1, w0, w1, x0, x1


def v4_bridged_step() -> Path:
    """v4's carriage as exported has its latch housing as a separate solid: the housing (u -25.5..-12.5) sits wholly inside
    the 51.6 mm opening (|u| <= 25.8), 0.3 mm short of the -u side strip, so nothing holds it. The FEA analyses the
    smallest fix: the housing's -u wall carried out over the strip's outer face to the carriage's edge (u -33..-25,
    w -20.85..-11.35, the housing's length), which bonds it to the strip over 7.2 x 31.5 mm. Built from v4's own source."""
    out = fem.exported("chain-carousel-v4") / "components" / "carriage_bridged.step"
    if out.exists():
        return out
    import subprocess
    code = (
        "import sys; sys.path.insert(0, %r)\n"
        "import cadquery as cq, parts4 as P4\n"
        "u0, u1, w0, w1, x0, x1 = %r\n"
        "c = P4.carriage_v4().union(cq.Workplane('XY').box(u1 - u0, w1 - w0, x1 - x0, centered=False).translate((u0, w0, x0)))\n"
        "print(len(c.solids().vals()))\n"
        "cq.exporters.export(c, %r)\n") % (str(fem.CAD / "chain-carousel-v4"), V4_BRIDGE, str(out))
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=str(fem.CAD / "chain-carousel-v4"))
    if r.returncode != 0 or not out.exists():
        raise RuntimeError(r.stderr[-800:])
    return out


def carriage_mesh(tag: str, material: str, h: float = H):
    src = v4_bridged_step() if tag == "v4" else fem.step_path(DESIGNS[tag], "carriage")
    p = fem.Part("carriage", src, None, material)
    hw = HINGE_W[tag]
    refine = [((s * (LUG_U[tag] + 1.0), hw, HINGE_X), 6.0, 0.9) for s in (-1, 1)]
    refine += [((0.0, -8.0, x), 6.0, 1.0) for x in A1_X]
    return fem.mesh_parts([p], size=h, size_min=0.6, curv=8, refine=refine)


_MESH = {}


def mesh(tag, material):
    k = (tag, material)
    if k not in _MESH:
        _MESH[k] = carriage_mesh(tag, material)
    return _MESH[k]


# --------------------------------------------------------------------------------------------- supports
def a1_patches(d: fem.Deck, tag: str, translate=(1, 2, 3), rotations: bool = True) -> list:
    """Rigid patch per A-1 tab (bore + tab footprint + head seat), held as described in the module docstring.
    rotations=False (station and loading cases, where the lips or side tabs hold the carriage radially and the chain only
    along u and x): the tabs are plain pins, no rotational restraint."""
    m = d.m
    p = m.xyz
    out = []
    for i, (xh, (f0, f1)) in enumerate(zip(A1_X, A1_FOOT)):
        r = np.hypot(p[:, 0], p[:, 2] - xh)
        foot = (np.abs(p[:, 1] - W1) < 0.05) & (np.abs(p[:, 0]) <= A1_HALF_W) & (p[:, 2] >= f0) & (p[:, 2] <= f1)
        bore = (np.abs(r - 1.7) < 0.15) & (p[:, 1] > W0 - 0.05) & (p[:, 1] < W1 + 0.05)
        seat = (np.abs(p[:, 1] - (W0 + 1.8)) < 0.05) & (r <= 3.25)
        idx = np.where(foot | bore | seat)[0]
        ref, rot = d.rigid_patch(idx, f"TAB{i}", at=(0.0, W1, xh))
        d.fix_ids([ref], dofs=translate, name=f"TABT{i}")
        if rotations:
            d.fix_ids([rot], dofs=(2,) if i == 1 else (2, 3), name=f"TABR{i}")     # rot about w; about x at the front only
            d.spring(rot, 1, K_TAB_ROT)                                             # rot about u: the bent tab
        out.append((ref, rot, idx))
    return out


def lip_support(d: fem.Deck, kind: str) -> np.ndarray:
    """Hold-down lips over both tongues (station) or side-tab lip / foot over the tongues' -u 8 mm (loading)."""
    m = d.m
    p = m.xyz
    sel = np.zeros(m.n, bool)
    if kind == "hold_down":
        for (x0, x1) in TONGUES:
            sel |= (np.abs(p[:, 1] - W1) < 0.05) & (np.abs(p[:, 0]) <= 13.0) & (p[:, 2] >= x0) & (p[:, 2] <= x1)
    else:
        wf = W1 if kind == "side_lip" else W0
        for (x0, x1) in SIDE_TAB_X:
            sel |= ((np.abs(p[:, 1] - wf) < 0.05) & (p[:, 0] >= SIDE_TAB_U[0]) & (p[:, 0] <= SIDE_TAB_U[1])
                    & (p[:, 2] >= x0) & (p[:, 2] <= x1))
    idx = np.where(sel)[0]
    d.fix(idx, dofs=(2,), name="LIPS")
    d.print_reactions("LIPS")
    return idx


# --------------------------------------------------------------------------------------------- module loads
def lug_faces(m: fem.Mesh, tag: str, side: int):
    hw = HINGE_W[tag]
    lu = LUG_U[tag]

    def pred(c, n):
        r = math.hypot(c[1] - hw, c[2] - HINGE_X)
        return abs(r - PIN_R) < 0.3 and lu - 0.05 <= side * c[0] <= lu + BORE_L + 0.05
    return m.faces_where(pred)


def hinge_load(d: fem.Deck, tag: str, F) -> None:
    """Total hinge reaction F (3,) on the carriage, half on each lug's bore, as bearing pressure (radial part) and a
    traction on the lug's inner face (the knuckle's thrust, along u)."""
    F = np.asarray(F, float)
    m = d.m
    hw = HINGE_W[tag]
    rad = F.copy()
    rad[0] = 0.0
    for s in (-1, 1):
        if np.linalg.norm(rad) > 1e-9:
            d.bearing(lug_faces(m, tag, s), rad / 2, (0.0, hw, HINGE_X), (1, 0, 0))
    if abs(F[0]) > 1e-9:
        s = 1 if F[0] > 0 else -1                        # the knuckle pushes the lug it slides toward
        lu = LUG_U[tag]
        faces = m.faces_where(lambda c, n: abs(s * c[0] - lu) < 0.05 and abs(n[0]) > 0.9 and
                              PIN_R + 0.1 < math.hypot(c[1] - hw, c[2] - HINGE_X) < 5.0)
        d.traction(faces, (F[0], 0.0, 0.0))


def pad_load(d: fem.Deck, F_w: float) -> None:
    m = d.m
    faces = m.faces_where(lambda c, n: abs(c[1] - W1) < 0.05 and n[1] > 0.9 and PAD_U[0] <= abs(c[0]) <= PAD_U[1]
                          and PAD_X[0] <= c[2] <= PAD_X[1])
    d.traction(faces, (0.0, F_w, 0.0))


def latch_load(d: fem.Deck, tag: str, F_w: float) -> None:
    """Latch reaction F_w (along w, + = inward) at the keeper, through the bolt's lever into its housing."""
    xs = LATCH_XS[tag]
    f0, f1 = LATCH_FRONT[tag]
    t0, t1 = LATCH_TAIL[tag]
    xf, xt = 0.5 * (f0 + f1), 0.5 * (t0 + t1)
    R1 = F_w * (xt - xs) / (xt - xf)                 # front edge, same sense as F_w
    R2 = F_w - R1                                    # tail (signed): the opposite sense, R1 + R2 = F_w
    m = d.m
    uc = LATCH_U[tag]
    if tag == "v3":
        lo, hi = LATCH_SLOT_W["v3"]
        for (a, b), R in (((f0, f1), R1), ((t0, t1), R2)):
            wface = hi if R > 0 else lo                  # pushed inward: the slot's ceiling; outward: its floor
            faces = m.faces_where(lambda c, n, a=a, b=b, wface=wface: abs(c[1] - wface) < 0.06 and abs(n[1]) > 0.9 and
                                  abs(c[0] - uc) <= 4.25 and a + HINGE_X <= c[2] <= b + HINGE_X)
            d.traction(faces, (0.0, R, 0.0))
    else:
        wb, rb = LATCH_BORE["v4"]
        faces = m.faces_where(lambda c, n: abs(math.hypot(c[0] - uc, c[1] - wb) - rb) < 0.25 and
                              f0 + HINGE_X <= c[2] <= f1 + HINGE_X)
        d.bearing(faces, (0.0, R1, 0.0), (uc, wb, 0.0), (0, 0, 1))      # the pin in the bore's mouth
        # the pin's printed carrier block at the tail bears on its channel (w -18.85 .. -12.85, u -23.2 .. -14.8)
        wface = -12.85 if R2 > 0 else -18.85
        faces = m.faces_where(lambda c, n: abs(c[1] - wface) < 0.06 and abs(n[1]) > 0.9 and abs(c[0] - uc) <= 4.25 and
                              t0 + HINGE_X <= c[2] <= t1 + HINGE_X)
        d.traction(faces, (0.0, R2, 0.0))


def module_reactions(tag: str, g_dir, extra: dict | None = None) -> dict:
    """The module's weight (direction g_dir, carriage frame) split statically onto hinge / pads / latch. Returns
    {'hinge': F (3,), 'pad_w': float, 'latch_w': float} in newtons (loads ON the carriage)."""
    W = MOD_KG[tag] * LD.G_MS2
    g = np.asarray(g_dir, float)
    xs = MOD_X[tag]
    out = {"hinge": np.zeros(3), "pad_w": 0.0, "latch_w": 0.0}
    gw, gu = g[1] * W, g[0] * W
    if abs(gw) > 1e-9:
        rest_on_carriage = (gw < 0) if tag == "v3" else False          # v3: module inside, weight toward the carriage
        if rest_on_carriage:
            xp = 0.5 * (90.5 + 103.0)                                   # pad contact centroid (Sam x)
            out["pad_w"] = gw * xs / xp
            out["hinge"][1] += gw - out["pad_w"]
        else:
            out["latch_w"] = gw * xs / LATCH_XS[tag]
            out["hinge"][1] += gw - out["latch_w"]
    if abs(gu) > 1e-9:                                                  # vertical runs: along the hinge pin
        out["hinge"][0] += gu                                           # the knuckle's thrust on a lug
        out["yaw_x_each_N"] = abs(gu) * xs / (2 * LUG_U[tag] + LUG_T)   # yaw couple on the lugs (x), for the hand check
    return out


# --------------------------------------------------------------------------------------------- cases
def gravity_case(tag: str, run: str, creep: bool = True, dyn: float = 1.0):
    """Carriage + module in the loop: run = bottom | top | up | down (vertical runs: gravity -u / +u)."""
    mat = "PETG_CREEP" if creep else "PETG"
    m = mesh(tag, mat)
    gdir = {"bottom": (0, -1, 0), "top": (0, 1, 0), "up": (-1, 0, 0), "down": (1, 0, 0)}[run]
    d = fem.Deck(m)
    pt = a1_patches(d, tag)
    d.gravity(gdir, factor=dyn)
    R = module_reactions(tag, gdir)
    Fh = R["hinge"] * dyn + np.asarray(gdir, float) * PINS_KG * LD.G_MS2 * dyn
    hinge_load(d, tag, Fh)
    if R["pad_w"]:
        pad_load(d, R["pad_w"] * dyn)
    if R["latch_w"]:
        latch_load(d, tag, R["latch_w"] * dyn)
    res = d.solve(f"carriage/{tag}_{run}_{mat}_d{dyn:.2f}")
    return d, res, R, Fh


def functional(tag: str, res, d) -> dict:
    """Displacements that matter for function: at the hinge axis (the module's pivot), at the latch, mid-span."""
    m = d.m
    U = res.U

    def near(p, r=2.5):
        k = np.where(np.linalg.norm(m.xyz - np.asarray(p), axis=1) < r)[0]
        if len(k) == 0:
            k = [int(np.argmin(np.linalg.norm(m.xyz - np.asarray(p), axis=1)))]
        return U[k].mean(0)
    hw = HINGE_W[tag]
    out = {}
    for s, nm in ((-1, "-u"), (1, "+u")):
        u = near((s * (LUG_U[tag] + 1.0), hw + PIN_R + 0.5, HINGE_X), 1.5)
        out[f"hinge lug {nm} dw (mm)"] = u[1]
    if tag == "v3":
        u = near((LATCH_U[tag], 2.25, LATCH_FRONT[tag][0] + HINGE_X + 1.0), 2.0)
    else:
        u = near((LATCH_U[tag], LATCH_BORE["v4"][0] + 2.2, LATCH_FRONT[tag][0] + HINGE_X + 1.0), 2.0)
    out["latch housing mouth dw (mm)"] = u[1]
    mid = m.nodes_where(lambda p: (np.abs(p[:, 2] - 152.5) < 2.0) & (np.abs(p[:, 1] - W0) < 0.05) & (np.abs(p[:, 0]) >= 26.0))
    out["mid-span edge strips dw (mm)"] = float(U[mid, 1].mean()) if len(mid) else float("nan")
    ul = out["latch housing mouth dw (mm)"]
    uh = 0.5 * (out["hinge lug -u dw (mm)"] + out["hinge lug +u dw (mm)"])
    # the module turns with the line hinge -> latch: its tip (cap end, Sam x 250) moves by the extrapolation
    out["auger cap end dw from carriage bending (mm)"] = uh + (ul - uh) * 250.0 / LATCH_XS[tag]
    return out


def run_gravity(tag: str, run: str, dyn: float = 1.0):
    d, res, R, Fh = gravity_case(tag, run, creep=True, dyn=dyn)
    kd = functional(tag, res, d)
    kd["short-term factor on these (E 1810 vs 1000)"] = 1000.0 / 1810.0
    excl = np.concatenate([idx for _, _, idx in [(0, 0, d.nsets[f"TAB{i}"] - 1) for i in (0, 1)]])
    desc = {"gravity": f"carriage + module {MOD_KG[tag] * 1000:.0f} g at Sam x {MOD_X[tag]}, x{dyn:.2f}",
            "hinge on carriage (N)": np.round(Fh, 3).tolist(), "pads (N, w)": round(R["pad_w"] * dyn, 3),
            "latch (N, w)": round(R["latch_w"] * dyn, 3)}
    case = f"{tag}_{run}" + ("" if dyn == 1.0 else "_dyn")
    view = (1.0, 0.9, 0.5)
    return common.record(MODULE, case, design=DESIGNS[tag], part=f"carriage {tag}", load_case=f"{run} run, gravity (creep E)",
                         res=res, exclude=excl, exclude_r=3.0, key_disp=kd, loads_desc=desc,
                         png_kw=dict(field="vm", view=view, up=(0, 1, 0)), render=(dyn == 1.0 and run in ("top", "bottom")))


def run_station(tag: str):
    """P16 stall at the station: 50 N up (+w) through the hinge, plus gravity (station = bottom run); the carriage
    lifts its 2 mm into the hold-down lips."""
    m = mesh(tag, "PETG")
    d = fem.Deck(m)
    a1_patches(d, tag, translate=(1, 3), rotations=False)
    lips = lip_support(d, "hold_down")
    d.gravity((0, -1, 0))
    R = module_reactions(tag, (0, -1, 0))
    Fh = R["hinge"] + np.array([0.0, P16_N, 0.0]) + np.array([0, -1, 0]) * PINS_KG * LD.G_MS2
    hinge_load(d, tag, Fh)
    if R["pad_w"]:
        pad_load(d, R["pad_w"])
    if R["latch_w"]:
        latch_load(d, tag, R["latch_w"])
    res = d.solve(f"carriage/{tag}_station_p16")
    kd = functional(tag, res, d)
    kd["lips reaction w (N)"] = float(res.reactions("LIPS")[1])
    if tag == "v3":                   # the 1 mm gaps between each lug's ends (x_c 25, 41) and its rib's cut (24, 42)
        notch = m.nodes_where(lambda q: (np.abs(q[:, 0]) >= 23.5) & (((q[:, 2] >= 40.5) & (q[:, 2] <= 42.5)) | ((q[:, 2] >= 23.5) & (q[:, 2] <= 25.5))))
        kd["von Mises in the lug-rib notches (MPa)"] = float(res.vm[notch].max())
    excl = np.concatenate([d.nsets["TAB0"] - 1, d.nsets["TAB1"] - 1, lips])
    return common.record(MODULE, f"{tag}_station_p16", design=DESIGNS[tag], part=f"carriage {tag}",
                         load_case="station: P16 stall 50 N through the hinge, carriage in the hold-down lips", res=res,
                         exclude=excl, exclude_r=2.5, key_disp=kd,
                         loads_desc={"hinge (N)": np.round(Fh, 2).tolist(), "supports": "hold-down lips (w), A-1 tabs (u, x)"},
                         png_kw=dict(field="vm", view=(1.0, 0.8, -0.6) if tag == "v3" else (1.0, -0.8, -0.6), up=(0, 1, 0),
                                     clim=(0, 16)))


def run_pull(tag: str, x_pull: float = PULL_XS):
    """Pulling an auger off its plate at the loading position (+y side, carriage vertical, u up): PULL_N away from the
    plate (v3 inward +w, v4 outward -w) at Sam x x_pull, through the hinge and the closed latch; the carriage's tongues
    go into the side tabs (v3 lips, v4 feet). Gravity along -u."""
    m = mesh(tag, "PETG")
    d = fem.Deck(m)
    a1_patches(d, tag, translate=(1, 3), rotations=False)
    sup = lip_support(d, "side_lip" if tag == "v3" else "side_foot")
    sgn = 1.0 if tag == "v3" else -1.0
    F = sgn * PULL_N
    xs = LATCH_XS[tag]
    F_latch = F * x_pull / xs
    F_hinge_w = F - F_latch
    d.gravity((-1, 0, 0))
    Rg = module_reactions(tag, (-1, 0, 0))
    Fh = Rg["hinge"] + np.array([0.0, F_hinge_w, 0.0]) + np.array([-1, 0, 0]) * PINS_KG * LD.G_MS2
    hinge_load(d, tag, Fh)
    latch_load(d, tag, F_latch)
    res = d.solve(f"carriage/{tag}_pull_x{x_pull:.0f}")
    kd = functional(tag, res, d)
    kd["side tabs reaction w (N)"] = float(res.reactions("LIPS")[1])
    excl = np.concatenate([d.nsets["TAB0"] - 1, d.nsets["TAB1"] - 1, sup])
    case = f"{tag}_pull" + ("" if x_pull == PULL_XS else f"_x{x_pull:.0f}")
    return common.record(MODULE, case, design=DESIGNS[tag], part=f"carriage {tag}",
                         load_case=f"loading: {PULL_N:.0f} N auger pull at Sam x {x_pull:.0f} (latch closed), tongues in the side tabs",
                         res=res, exclude=excl, exclude_r=2.5, key_disp=kd,
                         loads_desc={"latch (N, w)": round(F_latch, 2), "hinge (N)": np.round(Fh, 2).tolist()},
                         png_kw=dict(field="vm", view=(1.0, 0.9, 0.5) if tag == "v3" else (1.0, -0.9, 0.5), up=(0, 1, 0),
                                     clim=(0, 25)),
                         render=(x_pull == PULL_XS))


# --------------------------------------------------------------------------------------------- the latch bolt (v3)
def run_latch_bolt(F: float = PULL_N, name: str = "v3_latch_bolt_pull"):
    """v3's printed latch bolt alone (Sam's frame, closed): the keeper pushes its tip lap (x 100-103, underside z -12.6)
    up with F; the bolt bears on its housing slot's ceiling at the mouth (x 105.5-108.5, top face z -9.6) and on the
    floor at its tail (x 120-123). Printed flat (3 mm tall), so its bending stress runs along its layers: the X-Y
    strength (34 MPa) is the allowable."""
    MAT.add(MAT.Material("PETG_XY", 1810.0, 0.38, 1.27e-9, 34.0, "PETG (printed, along the layers)"))
    m = fem.mesh_parts([fem.Part("latch bolt", fem.step_path("chain-carousel-v3", "latch_bolt"), None, "PETG_XY")],
                       size=0.8, size_min=0.3, curv=8)
    d = fem.Deck(m)
    p = m.xyz
    top = np.where((np.abs(p[:, 2] + 9.6) < 0.03) & (p[:, 0] >= 105.5) & (p[:, 0] <= 108.5))[0]
    bot = np.where((np.abs(p[:, 2] + 12.6) < 0.03) & (p[:, 0] >= 120.0) & (p[:, 0] <= 123.0))[0]
    d.fix(top, dofs=(3,), name="MOUTH")
    d.fix(bot, dofs=(3,), name="TAIL")
    side = np.where((np.abs(p[:, 1] + 19.0 + 4.0) < 0.03) & (p[:, 0] >= 105.5))[0]
    d.fix(side, dofs=(2,), name="SIDE")
    d.fix(m.nodes_where(lambda q: np.abs(q[:, 0] - 123.0) < 0.03), dofs=(1,), name="SPRINGEND")
    lap = m.faces_where(lambda c, n: abs(c[2] + 12.6) < 0.03 and n[2] < -0.9 and 100.0 <= c[0] <= 103.0)
    d.traction(lap, (0.0, 0.0, F))
    d.print_reactions("MOUTH")
    res = d.solve(f"carriage/{name}")
    tipn = m.nodes_where(lambda q: q[:, 0] < 100.05)
    excl = np.concatenate([top, bot])
    b, hh = 8.0, 3.0                          # lever: the flat lap's centre (102.1, past the 1.2 mm tip chamfer) to the
    hand = 6 * F * (105.5 - 102.1) / (b * hh ** 2)   # mouth's edge (105.5), a cantilever root there
    return common.record(MODULE, name, design="chain-carousel-v3", part="latch bolt (printed)",
                         load_case=f"keeper pushes the bolt's lap with {F:.1f} N", res=res, exclude=excl, exclude_r=0.8,
                         key_disp={"bolt tip dz (mm)": float(res.U[tipn, 2].mean()),
                                   "hand: 6 F a / (b h^2) at the mouth (MPa)": hand,
                                   "mouth reaction (N)": float(res.reactions("MOUTH")[2])},
                         png_kw=dict(field="vm", view=(0.4, -1.0, 0.6), up=(0, 0, 1)))


# --------------------------------------------------------------------------------------------- the side tab
def run_side_tab(tag: str, F: float):
    """A side tab (front, parts3.side_tab in its own frame: X = u, Y = w, Z from the side plate's inner face) with the
    tongue pressing F on its lip (v3, +w) or foot (v4, -w) over the overlap (u -20..-12, Z 7..21). Held where its web
    sits on the side plate (Z = 0 face) and at its two M5 x 8 heads (counterbore floors)."""
    design = DESIGNS[tag]
    m = fem.mesh_parts([fem.Part("side tab", fem.step_path(design, "side_tab"), None, "PETG")], size=1.2, size_min=0.4, curv=8)
    d = fem.Deck(m)
    p = m.xyz
    base = np.where(np.abs(p[:, 2]) < 0.03)[0]
    d.fix(base, dofs=(3,), name="BASE")
    heads = []
    for (u, w) in ((-20.0, W1 + 2.0 + 14.0), (-8.0, W1 + 2.0 + 14.0)):
        k = np.where((np.abs(p[:, 2] - 1.5) < 0.03) & (np.hypot(p[:, 0] - u, p[:, 1] - w) < 4.7))[0]
        bore = np.where((np.abs(np.hypot(p[:, 0] - u, p[:, 1] - w) - 2.75) < 0.1) & (p[:, 2] < 1.5))[0]
        heads.append(k)
        d.fix(np.concatenate([k, bore]), dofs=(1, 2, 3), name=f"HEAD{len(heads)}")
    if tag == "v3":
        wf = W1 + 2.0
        faces = m.faces_where(lambda c, n: abs(c[1] - wf) < 0.03 and n[1] < -0.9 and -20.0 <= c[0] <= -12.0 and 7.0 <= c[2] <= 21.0)
        Fv = (0.0, F, 0.0)
    else:
        wf = W0 - 1.0
        faces = m.faces_where(lambda c, n: abs(c[1] - wf) < 0.03 and n[1] > 0.9 and -20.0 <= c[0] <= -12.0 and 7.0 <= c[2] <= 21.0)
        Fv = (0.0, -F, 0.0)
    d.traction(faces, Fv)
    res = d.solve(f"carriage/{tag}_side_tab")
    excl = np.concatenate([base] + heads)
    tip = m.nodes_where(lambda q: (np.abs(q[:, 1] - wf) < 0.05) & (q[:, 2] > 19.0) & (q[:, 0] > -20) & (q[:, 0] < -12))
    wl = (wf, wf + 3.0) if tag == "v3" else (wf - 3.0, wf)
    arm = m.nodes_where(lambda q: (q[:, 2] >= 6.5) & (q[:, 1] >= wl[0] - 0.01) & (q[:, 1] <= wl[1] + 0.01) & (q[:, 0] <= -12.0))
    beam = 6 * F * (14.0 - 5.5) / (12.0 * 3.0 ** 2)     # 12 x 3 mm cantilever from Z 5.5, load centroid at Z 14
    return common.record(MODULE, f"{tag}_side_tab", design=design, part="side tab (front, printed)",
                         load_case=f"tongue pushes the {'lip' if tag == 'v3' else 'foot'} with {F:.1f} N (auger pull)",
                         res=res, exclude=excl, exclude_r=1.0,
                         key_disp={f"{'lip' if tag == 'v3' else 'foot'} tip dw (mm)": float(res.U[tip, 1].mean()) if len(tip) else 0.0,
                                   "von Mises 1 mm off the sharp root corner (MPa)": float(res.vm[arm].max()),
                                   "beam estimate 6 F a / (b h^2) at the root (MPa)": beam},
                         png_kw=dict(field="vm", view=(-0.6, 0.5, 1.0) if tag == "v3" else (-0.6, -0.5, 1.0), up=(0, 1, 0),
                                     clim=(0, 25)))


# --------------------------------------------------------------------------------------------- hand checks
def hand_checks() -> dict:
    """Closed-form checks of the small steel parts and contacts (no FEA needed at these loads)."""
    out = {}
    W = {t: MOD_KG[t] * LD.G_MS2 for t in DESIGNS}
    # hinge pin: 5 mm 18-8 clevis pin, the knuckle 0.5 mm from the lug: single shear per lug, 50 N P16 stall on two lugs
    A = math.pi * 2.5 ** 2
    V = P16_N / 2
    out["hinge pin shear at the P16 stall (MPa)"] = V / A
    out["hinge pin bending, 25 N over a 0.5 mm gap + half the 2.2 mm bore and half a 10 mm knuckle (MPa)"] = \
        V * (0.5 + 1.1 + 2.5) / (math.pi * 5.0 ** 3 / 32)
    out["lug bearing at the P16 stall, 25 N on 5 x 2.2 mm (MPa)"] = V / (5.0 * BORE_L)
    # lug tear-out (v3: 6 mm from the pin centre to the lug's top, minus the hole's radius, two shear planes, 2.2 + 1.8 mm)
    out["v3 lug tear-out shear at the P16 stall (MPa)"] = V / (2 * (6.0 - PIN_R) * LUG_T)
    # vertical runs: the module's yaw couple on the lugs
    for t in DESIGNS:
        out[f"{t} vertical run: lug x-bearing from the yaw couple (N each)"] = W[t] * MOD_X[t] / (2 * LUG_U[t] + LUG_T)
    # v4 latch pin: 4 mm steel dowel in the keeper's 4.2 mm hole, 4 mm engaged; module weight x DYN, and the 40 N pull
    for nm, F in (("module x1.27", W["v4"] * MOD_X["v4"] / LATCH_XS["v4"] * DYN), ("40 N pull", PULL_N * PULL_XS / LATCH_XS["v4"])):
        out[f"v4 latch pin, {nm}: keeper bearing on 4 x 4 mm (MPa)"] = F / 16.0
        out[f"v4 latch pin, {nm}: pin bending over 2.5 mm to the bore (MPa)"] = F * 2.5 / (math.pi * 4.0 ** 3 / 32)
        out[f"v4 latch keeper, {nm}: shear-out of the hole's 2.9 mm wall (MPa)"] = F / (2 * 2.9 * 4.0)
    # v3 keeper: the bolt's lap pushes the keeper's top face over 3 x 8 mm; the keeper is 5 mm of plate-side block
    for nm, F in (("module x1.27", W["v3"] * MOD_X["v3"] / LATCH_XS["v3"] * DYN), ("40 N pull", PULL_N * PULL_XS / LATCH_XS["v3"])):
        out[f"v3 keeper, {nm}: bearing under the bolt's 3 x 8 mm lap (MPa)"] = F / 24.0
        out[f"v3 keeper, {nm}: shear at its root, 5 x 10 mm (MPa)"] = F / 50.0
    # A-1 joint: the M3 x 12's head on the counterbore floor (button head 5.7 mm on a 3.4 mm hole) and the hole in the tab
    A_head = math.pi / 4 * (5.7 ** 2 - 3.4 ** 2)
    out["A-1 screw head on the printed seat: 300 N preload (MPa)"] = 300.0 / A_head
    out["A-1 screw head seat area (mm^2)"] = A_head
    out["A-1 tab hole bearing, 46 N P16 front-tab share on 3 x 1.27 mm (MPa)"] = 46.0 / (3.0 * 1.27)
    out["A-1 screw in the printed plate's hole, 46 N on 3 x 5 mm (MPa)"] = 46.0 / (3.0 * 5.0)
    # E-stop: 0.68 m/s^2 coast-down against 9.81 gravity: 7 % of the module weight, along the travel
    out["E-stop deceleration / g"] = LD.ESTOP_DECEL / LD.G_MS2
    return out


# --------------------------------------------------------------------------------------------- summary table
FUNC_KEYS = ("hinge lug -u dw (mm)", "latch housing mouth dw (mm)", "mid-span edge strips dw (mm)",
             "auger cap end dw from carriage bending (mm)", "bolt tip dz (mm)", "lip tip dw (mm)", "foot tip dw (mm)")


def table_rows() -> list:
    rows = []
    for f in sorted((common.OUT / MODULE).glob("*.json")):
        if f.name == "hand_checks.json":
            continue
        r = json.loads(f.read_text())
        kd = r.get("key_disp", {})
        func = []
        for k in FUNC_KEYS:
            if k in kd:
                func.append(f"{k.replace(' (mm)', '')} {kd[k]:+.3f} mm")
        for k in ("von Mises in the lug-rib notches (MPa)", "von Mises 1 mm off the sharp root corner (MPa)",
                  "beam estimate 6 F a / (b h^2) at the root (MPa)", "hand: 6 F a / (b h^2) at the mouth (MPa)",
                  "lips reaction w (N)", "side tabs reaction w (N)"):
            if k in kd:
                func.append(f"{k} {kd[k]:.3g}")
        for pr in r["parts"]:
            rows.append(dict(case=r["case"], part=pr["part"], design=r["design"].replace("chain-carousel-", ""),
                             load=r["load_case"], umax=pr["umax_mm"], vm=pr["vm_excl_MPa"], vm_raw=pr["vm_max_MPa"],
                             at=pr["vm_excl_at"], allow=pr["allow_MPa"], sf=pr["sf"], func="; ".join(func),
                             png=r.get("png", "")))
    return rows


def summary_table() -> str:
    L = ["| case | part | design | load case | max displacement (mm) | peak von Mises, supports excluded (MPa) "
         "| allowable (MPa) | SF | functional numbers |", "|---|---|---|---|---|---|---|---|---|"]
    for r in table_rows():
        L.append(f"| `{r['case']}` | {r['part']} | {r['design']} | {r['load']} | {r['umax']:.3f} | {r['vm']:.2f} "
                 f"(raw {r['vm_raw']:.2f}, at {r['at']}) | {r['allow']:.0f} | {r['sf']:.2f} | {r['func']} |")
    return "\n".join(L)


CASES = {}
for _t in DESIGNS:
    for _r in ("bottom", "top", "up", "down"):
        CASES[f"{_t}_{_r}"] = (lambda t=_t, r=_r: run_gravity(t, r))
    CASES[f"{_t}_top_dyn"] = (lambda t=_t: run_gravity(t, "top", dyn=DYN))
    CASES[f"{_t}_station_p16"] = (lambda t=_t: run_station(t))
    CASES[f"{_t}_pull"] = (lambda t=_t: run_pull(t))
    CASES[f"{_t}_pull_x50"] = (lambda t=_t: run_pull(t, 50.0))
CASES["v4_bottom_dyn"] = lambda: run_gravity("v4", "bottom", dyn=DYN)
CASES["v3_latch_bolt_pull"] = lambda: run_latch_bolt(PULL_N * PULL_XS / LATCH_XS["v3"])
CASES["v3_latch_bolt_top_dyn"] = lambda: run_latch_bolt(MOD_KG["v3"] * LD.G_MS2 * MOD_X["v3"] / LATCH_XS["v3"] * DYN,
                                                        "v3_latch_bolt_top_dyn")
CASES["v3_side_tab"] = lambda: run_side_tab("v3", 25.0)
CASES["v4_side_tab"] = lambda: run_side_tab("v4", 25.0)


if __name__ == "__main__":
    import time
    which = sys.argv[1:] or list(CASES)
    if which == ["table"]:
        print(summary_table())
        sys.exit()
    if which == ["hand"]:
        h = hand_checks()
        (common.OUT / MODULE).mkdir(parents=True, exist_ok=True)
        (common.OUT / MODULE / "hand_checks.json").write_text(json.dumps(h, indent=1))
        print(json.dumps(h, indent=1))
        sys.exit()
    for k in which:
        t0 = time.time()
        r = CASES[k]()
        print(k, json.dumps({kk: r.get(kk) for kk in ("key_disp", "parts", "loads") if kk in r}, default=float)[:1800],
              f"{time.time() - t0:.0f} s", flush=True)
