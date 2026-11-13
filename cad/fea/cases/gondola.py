"""The paternoster's printed PETG gondola (paternoster/parts.gondola), in its own frame: x along the pivot axis from the
front chain's centre plane, z up (it always hangs upright, centre of mass under the pivots).

It hangs from two shoulder screws through flanged bronze bushings in its end plates: each bushing bore is a rigid ring
whose reference node is held in translation; the rotation about the pivot axis is held at the front ring only (the
gondola is a pendulum, a linear solve has nothing else to stop it turning). Sam's plate sits on the floor strips beside
the station window and is pinned in the hinge lugs.

Cases:
* hanging: its own weight plus the module (loads.PAT_MODULE_KG) on the floor strips, short-term and with the creep
  modulus (a module sits in its gondola for days);
* station stall: the P16 pushes the module up with its 50 N stall force (loads.P16_MAX_N) and the module can't tilt, so the
  whole push comes out through the hinge pin in the lugs; the pivots hold the gondola down (the hold-down strips would
  share this; leaving them out is conservative for the end plates).
The shoulder screws are checked by hand: each is a 4 mm pin in bending over its 10 mm shoulder.
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
from cases import common  # noqa: E402

MODULE = "gondola"
DESIGN = "paternoster"


def params():
    import importlib
    sys.path.insert(0, str(fem.CAD / DESIGN))
    sys.modules.pop("params", None)
    P = importlib.import_module("params")
    sys.path.pop(0)
    return P


_M = {}


def mesh(material: str):
    if material not in _M:
        _M[material] = fem.mesh_parts([fem.Part("gondola", fem.step_path(DESIGN, "gondola"), None, material)], size=3.0,
                                      size_min=0.8, curv=10)
    return _M[material]


def solve(case: str, material: str = "PETG") -> dict:
    P = params()
    m = mesh(material)
    d = fem.Deck(m)
    rb = P.BUSHING_OD / 2
    x_end = [(P.END_X0, P.END_X1), (P.CHAIN_L - P.END_X1, P.CHAIN_L - P.END_X0)]
    rings = []
    for i, (a, b) in enumerate(x_end):
        idx = m.nodes_where(lambda p, a=a, b=b: (p[:, 0] >= a - 1e-3) & (p[:, 0] <= b + 1e-3)
                            & (np.abs(np.hypot(p[:, 1], p[:, 2]) - rb) < 0.05))
        r, q = d.rigid_patch(idx, f"PIVOT{i}", at=(0.5 * (a + b), 0.0, 0.0))
        d.fix_ids([r], dofs=(1, 2, 3) if i == 0 else (2, 3), name=f"PIN{i}")
        if i == 0:
            d.fix_ids([q], dofs=(1,), name="SWING")
        rings.append(idx)
    desc = {}
    fz1 = P.HINGE_Z - P.SAM_DROP
    floor = m.faces_where(lambda c, n: n[2] > 0.9 and abs(c[2] - fz1) < 0.05)
    Wm = LD.PAT_MODULE_KG * LD.G_MS2
    d.gravity()
    if case == "hanging":
        d.traction(floor, (0.0, 0.0, -Wm))
        desc["module"] = f"{Wm:.2f} N on the floor strips ({sum(f[5] for f in floor):.0f} mm^2)"
    elif case == "stall":
        lug = m.faces_where(lambda c, n: abs(c[1]) > P.LUG_IN - 0.05 and
                            abs(math.hypot(c[0] - P.HINGE_X, c[2] - P.HINGE_Z) - P.INSERT_D / 2) < 0.1 and abs(n[1]) < 0.3)
        F = LD.P16_MAX_N
        for sgn in (-1, 1):
            d.bearing([f for f in lug if np.sign(f[3][1]) == sgn], (0.0, 0.0, F / 2), (P.HINGE_X, 0.0, P.HINGE_Z), (0, 1, 0))
        desc["P16 stall"] = f"{F:.0f} N up through the hinge pin, half in each lug"
    res = d.solve(f"{MODULE}/{case}_{material}")
    excl = np.concatenate(rings)
    # function: the floor's sag under the plate relative to the pivots, the lugs' lift
    fn = np.unique(np.concatenate([f[2] for f in floor]))
    kd = {"floor sag, worst (mm)": float(-res.U[fn, 2].min())}
    if case == "stall":
        ln = m.nodes_where(lambda p: (np.abs(p[:, 1]) > P.LUG_IN) & (np.hypot(p[:, 0] - P.HINGE_X, p[:, 2] - P.HINGE_Z) < P.INSERT_D / 2 + 0.3))
        kd["hinge lugs lift (mm)"] = float(res.U[ln, 2].mean())
    title = {"hanging": "hanging: own weight + module on the floor", "stall": "station: P16 stall (50 N) up through the hinge"}[case]
    return common.record(MODULE, f"{case}_{material}", design=DESIGN, part="gondola (printed PETG)", load_case=title, res=res,
                         exclude=excl, exclude_r=1.5, key_disp=kd, loads_desc=desc,
                         notes=f"material {material}; pivots pinned, swing held at the front pivot",
                         allow={"gondola": 8.0} if material == "PETG_CREEP" else None,
                         png_kw=dict(field="vm", view=(0.5, -1.0, 0.6), zoom=1.4, size=(1600, 900)))


def shoulder_screw_hand() -> dict:
    """18-8 shoulder screw, 4 mm shoulder, loaded at the middle of the bushing (6 mm) 6 mm from where the thread clamps
    it in the SA-1 tab: bending stress per pivot for the hanging gondola (front chain's 56 %) and for half the stall."""
    P = params()
    d = P.SHOULDER_D
    Z = math.pi * d ** 3 / 32
    arm = 0.8 + 6.0 / 2 + 0.6                       # thrust washer, half the bushing, the clearance
    out = {}
    for name, F in (("hanging (front pivot, 56 %)", LD.PAT_LOADED_KG * LD.G_MS2 * LD.PAT_FRONT_SHARE),
                    ("P16 stall, half at each pivot", LD.P16_MAX_N / 2)):
        s = F * arm / Z
        out[name] = dict(F_N=round(F, 2), arm_mm=arm, sigma_MPa=round(s, 2), sf_vs_205=round(205.0 / s, 1),
                         bushing_pressure_MPa=round(F / (d * 6.0), 3))
    (common.OUT / MODULE).mkdir(parents=True, exist_ok=True)
    (common.OUT / MODULE / "shoulder_screw_hand.json").write_text(json.dumps(out, indent=1))
    return out


CASES = {
    "hanging_PETG": lambda: solve("hanging", "PETG"),
    "hanging_PETG_CREEP": lambda: solve("hanging", "PETG_CREEP"),
    "stall_PETG": lambda: solve("stall", "PETG"),
    "shoulder_screw": shoulder_screw_hand,
}

if __name__ == "__main__":
    import time
    for k in sys.argv[1:] or list(CASES):
        t0 = time.time()
        r = CASES[k]()
        print(k, json.dumps({kk: r.get(kk) for kk in ("key_disp",)} if "parts" in r else r, default=float)[:600],
              [(p["part"], p["vm_excl_MPa"], p["sf"]) for p in r.get("parts", [])], f"{time.time() - t0:.0f} s", flush=True)
