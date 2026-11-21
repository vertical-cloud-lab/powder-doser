"""Heat: where the rig's electrical losses go, how hot the parts get, and what that does to the printed parts and the
balance. CalculiX steady and transient heat transfer (DC3D10), with natural convection and radiation on every
exposed face, coupled to an energy balance of the acrylic enclosure.

    python cases/thermal.py            # every case
    python cases/thermal.py motor ec   # some

Heat sources (copper loss I^2 R; the motors turn so slowly that their iron loss is negligible):
  NEMA 34 34HS59-6004D-E1000 at 6.0 A (the docs set the CL86T to 6.0 A), 0.7 ohm per phase (StepperOnline's 12 N*m
  34HS59 listings; the exact part's sheet was not reachable): 2 I^2 R = 50.4 W cold at full current, at standstill or
  at these low speeds. How much of that the CL86T actually draws depends on its mode: open loop or a full holding
  current gives all of it; closed loop adjusts the current to the load. So the motor is run at four currents: 100 %
  (6.0 A), 70 %, 50 % and 25 % of 6.0 A. The winding's resistance rises 0.393 %/K, so the loss is iterated with its
  temperature.
  The driver (CL86T) and the 48 V supply sit on the electronics board outside the enclosure, so their losses don't count.
  NEMA 11 11HS18-0674S on its DRV8825 at the 450 mA limit, 6.8 ohm: I^2 R = 1.38 W cold, whenever it is enabled
  (microstepping keeps I_A^2 + I_B^2 at the limit squared).
  Dock electromagnet P20/15 (Adafruit 3872) at 5 V, 0.22 A: 1.1 W cold while the dock holds (v3); on a fixed 5 V its
  current, its loss and its pull all fall as its coil warms.
  P16 (20 % duty cycle), the solenoid's 10 ms taps and the ERM: a fraction of a watt on average, left out.

Convection: laminar natural-convection correlations for air (h = 1.42 (dT/L)^0.25 on vertical faces, 1.32 up-facing,
0.59 down-facing, W/(m^2 K)), iterated on each part's mean surface temperature. Radiation to the surroundings: black
paint 0.9 (motors), mill-finish 6061 0.10, black-anodised 6061 0.85, printed PETG 0.9.
Inside an enclosure the sinks are its air (convection) and its walls (radiation); the walls lose heat to the room by
convection and radiation outside (h_out 8.5 W/(m^2 K)) and the inside air reaches its walls with h_in 3 W/(m^2 K).
No air leaks out; any leakage only lowers the rises.
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
from cases import frame as FR  # noqa: E402

MODULE = "thermal"
T_ROOM = 22.0
ALPHA_CU = 0.00393                     # copper's resistance, per K
R34_20 = 0.7                           # ohm per phase at 20 C
I34 = 6.0                              # A, the docs' CL86T setting
R11_20 = 6.8
I11 = 0.45
EM_W_20 = 1.1                          # P20/15 at 5 V, 0.22 A
H_OUT = 8.5                            # enclosure walls to the room: convection 3 + radiation 5.5 (acrylic is black in the IR)
H_IN = 3.0                             # enclosure air to its walls
ENCL_AREA = {"chain-carousel-v3": 3365e3 / 3.0 / 1e6, "chain-carousel-v4": 4313e3 / 3.0 / 1e6}  # m^2: acrylic volume / 3 mm
EPS = {"motor": 0.9, "al_mill": 0.10, "al_black": 0.85, "petg": 0.9, "steel": 0.6, "magnet": 0.3}
# thermal properties: k W/(m K), cp J/(kg K)
K = {"AL6061": (167.0, 896.0), "STEEL_PLATE": (51.9, 486.0), "MOTOR": (25.0, 480.0), "PETG": (0.20, 1200.0),
     "N11": (20.0, 480.0), "EM": (30.0, 450.0)}
# PETG HF's heat deflection temperature (0.45 MPa), Bambu's comparison table; keep sustained-loaded parts 20 K under it
HDT = {"PLA": 57.0, "PETG HF": 69.0, "ABS": 87.0, "ASA": 100.0, "PC": 117.0, "PA6-CF": 186.0, "PAHT-CF": 194.0}


# ------------------------------------------------------------------------------------------------ helpers
def exterior_faces(m: fem.Mesh) -> list:
    """Every tet face on the outside of the mesh (belongs to one tet only): (elem, label, corner nodes, centroid,
    outward normal, area)."""
    cnt = {}
    for e, t in enumerate(m.tet):
        for lab, (a, b, c) in fem.TET_FACES.items():
            key = tuple(sorted((int(t[a]), int(t[b]), int(t[c]))))
            if key in cnt:
                cnt[key] = None
            else:
                cnt[key] = (e, lab, (int(t[a]), int(t[b]), int(t[c])))
    out = []
    for v in cnt.values():
        if v is None:
            continue
        e, lab, tri = v
        p = m.xyz[list(tri)]
        c = p.mean(0)
        n = np.cross(p[1] - p[0], p[2] - p[0])
        nn = np.linalg.norm(n)
        if nn == 0:
            continue
        n /= nn
        if np.dot(n, c - m.xyz[m.tet[e, :4]].mean(0)) < 0:
            n = -n
        out.append((e, lab, tri, c, n, 0.5 * nn))
    return out


def h_nat(dT: float, L_m: float, normal_z: float) -> float:
    """Laminar natural convection in air, W/(m^2 K): vertical, hot face up, hot face down."""
    dT = max(abs(dT), 0.5)
    if normal_z > 0.7:
        c = 1.32 if dT > 0 else 0.59
    elif normal_z < -0.7:
        c = 0.59 if dT > 0 else 1.32
    else:
        c = 1.42
    return c * (dT / L_m) ** 0.25


def boundary(hd: fem.HeatDeck, faces: list, part_of: dict, eps_of: dict, L_of: dict, T_air: float, T_wall: float,
             T_guess: dict):
    """Film and radiation on every exterior face, grouped by part and orientation."""
    m = hd.m
    hd.films, hd.rads = [], []
    for f in faces:
        nm = m.names[m.part[f[0]]]
        g = part_of.get(nm, nm)
        h = h_nat(T_guess.get(g, T_air + 10.0) - T_air, L_of.get(g, 0.1), f[4][2])
        hd.films.append((f[0] + 1, f[1], T_air, h * 1e-3))
        hd.rads.append((f[0] + 1, f[1], T_wall, eps_of[g]))


def face_heat(res: fem.HeatResult, faces: list, part_of: dict, eps_of: dict, L_of: dict, T_air: float, T_wall: float,
              T_guess: dict) -> dict:
    """Heat each group sheds by convection and radiation (W), from the solved temperatures."""
    m = res.deck.m
    out = {}
    for f in faces:
        nm = m.names[m.part[f[0]]]
        g = part_of.get(nm, nm)
        T = float(np.mean(res.T[list(f[2])]))
        A = f[5] * 1e-6
        h = h_nat(T_guess.get(g, T_air + 10.0) - T_air, L_of.get(g, 0.1), f[4][2])
        qc = h * A * (T - T_air)
        qr = eps_of[g] * 5.669e-8 * A * ((T + 273.15) ** 4 - (T_wall + 273.15) ** 4)
        o = out.setdefault(g, dict(conv=0.0, rad=0.0, area=0.0, Tsum=0.0))
        o["conv"] += qc
        o["rad"] += qr
        o["area"] += A
        o["Tsum"] += T * A
    for g, o in out.items():
        o["T_surface_mean"] = o.pop("Tsum") / o["area"]
    return out


def enclosure_temps(P_conv: float, P_rad: float, A: float) -> tuple:
    """(air, walls) of a closed acrylic enclosure: everything leaves through its walls; the radiated part reaches them
    directly, the convected part through the inside air."""
    T_wall = T_ROOM + (P_conv + P_rad) / (H_OUT * A)
    T_air = T_wall + P_conv / (H_IN * A)
    return T_air, T_wall


# ------------------------------------------------------------------------------------------------ the NEMA 34 on its wall
def motor_parts(design: str, plate_mat: str = "AL6061"):
    D = FR.design_data(design)
    P = D["P"]
    FR.add_material("MOTOR", 70000.0, 0.3, LD.M_NEMA34 * 1e-3 / FR._motor_volume(P), 1e9, "NEMA 34 envelope (5.6 kg)")
    if plate_mat == "STEEL_PLATE":
        MAT.add(MAT.Material("STEEL_PLATE", 205000.0, 0.29, 7.87e-9, 250.0, "A36 / 1018 steel plate"))
    parts = [fem.Part("NEMA 34", FR._motor_envelope(D["motor"], P), None, "MOTOR")]
    if design == "paternoster":
        parts.append(fem.Part("motor plate", fem.step_path(design, "motor_plate"), D["motor_plate"][0], plate_mat))
        for i, Ms in enumerate(D["standoffs"]):
            parts.append(fem.Part(f"standoff {i + 1}", fem.step_path(design, "standoff"), Ms, "AL6061"))
        parts.append(fem.Part("side_plate_back", fem.step_path(design, "side_plate_back"),
                              [M for k, M in D["plates"] if k == "side_plate_back"][0], "AL6061"))
    else:
        parts.append(fem.Part("side_plate_back", fem.step_path(design, "side_plate_back"),
                              [M for k, M in D["plates"] if k == "side_plate_back"][0], plate_mat))
    return D, parts


def printed_on_back_plate(design: str, D: dict, m: fem.Mesh) -> dict:
    """Printed parts screwed to the back side plate, and the plate's nodes under each (within 12 mm of its origin)."""
    ip = m.names.index("side_plate_back")
    pn = m.nodes_of("side_plate_back")
    x0, x1 = m.xyz[pn, 0].min(), m.xyz[pn, 0].max()
    keys = ("tensioner_block", "hold_down", "side_tab", "side_tab_m", "latch_rail", "cradle", "clevis_bracket")
    out = {}
    for p in D["pl"]:
        if p["key"] not in keys:
            continue
        o = np.array(p["M"])[:3, 3]
        if not (x0 - 25.0 <= o[0] <= x1 + 25.0):
            continue
        d = np.linalg.norm(m.xyz[pn][:, 1:] - o[1:], axis=1)
        sel = pn[d < 12.0]
        if len(sel):
            out[p["name"]] = sel
    return out


def solve_motor(design: str, frac: float, plate_mat: str = "AL6061", finish: str = "al_mill", h: float = 7.0,
                tag: str | None = None, iters: int = 4) -> dict:
    D, parts = motor_parts(design, plate_mat)
    key = (design, plate_mat, h)
    if key not in _MESH:
        _MESH[key] = fem.mesh_parts(parts, size=h, size_min=2.0, curv=6)
    m = _MESH[key]
    faces = exterior_faces(m)
    enclosed = design in ENCL_AREA
    k = {nm: K[("MOTOR" if nm == "NEMA 34" else (plate_mat if nm in ("side_plate_back", "motor plate") else "AL6061"))][0]
         for nm in m.names}
    cp = {nm: K[("MOTOR" if nm == "NEMA 34" else (plate_mat if nm in ("side_plate_back", "motor plate") else "AL6061"))][1]
          for nm in m.names}
    part_of = {nm: ("motor" if nm == "NEMA 34" else "plate") for nm in m.names}
    eps_of = {"motor": EPS["motor"], "plate": EPS["steel"] if plate_mat == "STEEL_PLATE" else EPS[finish]}
    L_of = {"motor": 0.086, "plate": 0.30}
    T_air, T_wall = T_ROOM, T_ROOM
    T_guess = {"motor": T_ROOM + 30.0 * frac ** 2, "plate": T_ROOM + 15.0 * frac ** 2}
    T_wind = T_ROOM + 40.0 * frac ** 2
    hist = []
    for it in range(iters):
        P = 2 * (frac * I34) ** 2 * R34_20 * (1 + ALPHA_CU * (T_wind - 20.0))
        hd = fem.HeatDeck(m, k=k, cp=cp, T0=T_air)
        hd.source("NEMA 34", P)
        boundary(hd, faces, part_of, eps_of, L_of, T_air, T_wall, T_guess)
        res = hd.solve(f"thermal/{tag or design}_{int(frac * 100)}_{plate_mat}_{finish}")
        q = face_heat(res, faces, part_of, eps_of, L_of, T_air, T_wall, T_guess)
        T_guess = {g: o["T_surface_mean"] for g, o in q.items()}
        Pc = sum(o["conv"] for o in q.values())
        Pr = sum(o["rad"] for o in q.values())
        tmo = res.T_of("NEMA 34")
        T_wind = tmo[2] + 0.15 * P                   # the winding sits about 0.15 K/W above the case's hottest point
        hist.append(dict(P_W=round(P, 2), T_air=round(T_air, 2), motor_max=round(tmo[2], 1), shed_W=round(Pc + Pr, 2)))
        if enclosed:
            T_air, T_wall = enclosure_temps(Pc, Pr, ENCL_AREA[design])
    tp = res.T_of("side_plate_back")
    mp = FR.motor_points(D)
    enc = res.T[FR.nearest(m, mp["enc"], "NEMA 34")]
    printed = {nm: round(float(np.nanmax(res.T[idx])), 1) for nm, idx in printed_on_back_plate(design, D, m).items()}
    rec = dict(module=MODULE, case=tag or f"{design}_motor_{int(frac * 100)}", design=design, current_A=round(frac * I34, 2),
               current_frac=frac, P_motor_W=round(P, 2), plate=plate_mat, plate_finish=finish if plate_mat == "AL6061" else "steel",
               T_room=T_ROOM, T_enclosure_air=round(T_air, 1) if enclosed else None, T_enclosure_walls=round(T_wall, 1) if enclosed else None,
               motor_case_max=round(tmo[2], 1), motor_case_mean=round(tmo[1], 1), winding_est=round(T_wind, 1),
               encoder_end=round(float(enc), 1), plate_max=round(tp[2], 1), plate_mean=round(tp[1], 1),
               printed_parts_on_back_plate_max_C=printed,
               shed_conv_W=round(Pc, 2), shed_rad_W=round(Pr, 2), by_group={g: {kk: round(v, 2) for kk, v in o.items()} for g, o in q.items()},
               iterations=hist, nodes=int(m.n), wall_s=round(res.wall, 1))
    if standoffs := [nm for nm in m.names if nm.startswith("standoff")]:
        rec["standoffs_max"] = round(max(res.T_of(s)[2] for s in standoffs), 1)
    d = common.OUT / MODULE
    d.mkdir(parents=True, exist_ok=True)
    try:
        view = (-1.0, -1.1, 0.45) if design != "paternoster" else (1.3, -1.0, 0.5)   # from the motor's side
        fem.render_T(res, d / f"{rec['case']}.png", title=f"{design}: NEMA 34 at {frac * I34:.1f} A ({P:.0f} W)"
                     + (f", enclosure air {T_air:.0f} °C" if enclosed else f", room {T_ROOM:.0f} °C"), view=view)
        rec["png"] = f"out/{MODULE}/{rec['case']}.png"
    except Exception as e:                                # noqa: BLE001
        rec["png_error"] = str(e)[:200]
    (d / f"{rec['case']}.json").write_text(json.dumps(rec, indent=1, default=float))
    print(rec["case"], f"P {P:.1f} W, motor {tmo[2]:.1f} C, plate {tp[2]:.1f} C, air {T_air:.1f} C", flush=True)
    return rec


def warmup(design: str = "chain-carousel-v3", frac: float = 1.0, hours: float = 3.0, h: float = 10.0) -> dict:
    """Transient: the motor switched on at frac x 6.0 A in a cold rig; the enclosure air follows its own lumped balance
    (taken from the steady result), so this is the motor and plate warming toward the steady state."""
    ss = json.loads((common.OUT / MODULE / f"{design}_motor_{int(frac * 100)}.json").read_text())
    D, parts = motor_parts(design)
    m = _MESH.get((design, "AL6061", h)) or fem.mesh_parts(parts, size=h, size_min=2.0, curv=6)
    faces = exterior_faces(m)
    k = {nm: K["MOTOR" if nm == "NEMA 34" else "AL6061"][0] for nm in m.names}
    cp = {nm: K["MOTOR" if nm == "NEMA 34" else "AL6061"][1] for nm in m.names}
    part_of = {nm: ("motor" if nm == "NEMA 34" else "plate") for nm in m.names}
    eps_of = {"motor": EPS["motor"], "plate": EPS["al_mill"]}
    L_of = {"motor": 0.086, "plate": 0.30}
    T_air = ss["T_enclosure_air"] or T_ROOM
    T_wall = ss["T_enclosure_walls"] or T_ROOM
    T_guess = {g: v["T_surface_mean"] for g, v in ss["by_group"].items()}
    hd = fem.HeatDeck(m, k=k, cp=cp, T0=T_ROOM)
    hd.source("NEMA 34", ss["P_motor_W"])
    boundary(hd, faces, part_of, eps_of, L_of, T_air, T_wall, T_guess)
    mp = FR.motor_points(D)
    hd.probe("MOTORCOM", [FR.nearest(m, mp["com"], "NEMA 34")])
    hd.probe("PLATE", m.nodes_of("side_plate_back"))
    hd.transient(hours * 3600.0, dt0=30.0, dt_max=300.0)
    res = hd.solve(f"thermal/{design}_warmup_{int(frac * 100)}")
    hc = res.history.get("MOTORCOM", [])
    hp = res.history.get("PLATE", [])
    t = np.array([a for a, b, c in hc])
    Tm = np.array([b for a, b, c in hc])
    out = dict(module=MODULE, case=f"{design}_warmup_{int(frac * 100)}", P_W=ss["P_motor_W"],
               note="enclosure air and walls held at their steady values (an upper bound early on: the air warms too)",
               t_s=t.tolist()[::4], motor_com_C=Tm.tolist()[::4], plate_max_C=[c for a, b, c in hp][::4])
    if len(t):
        rise = Tm - T_ROOM
        for frac_ in (0.632, 0.9, 0.95):
            k_ = np.argmax(rise >= frac_ * (ss["motor_case_mean"] - T_ROOM)) if (rise >= frac_ * (ss["motor_case_mean"] - T_ROOM)).any() else -1
            out[f"t_{int(frac_ * 100)}pct_min"] = round(float(t[k_]) / 60.0, 1) if k_ >= 0 else None
    (common.OUT / MODULE / f"{out['case']}.json").write_text(json.dumps(out, indent=1, default=float))
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.plot(t / 60, Tm, label="motor (centre of the body)", color="#c0392b")
        ax.plot(np.array([a for a, b, c in hp]) / 60, [c for a, b, c in hp], label="back plate (hottest point)", color="#2c7fb8")
        ax.axhline(ss["motor_case_mean"], color="#c0392b", lw=0.8, ls=":")
        ax.set_xlabel("minutes after switch-on")
        ax.set_ylabel("°C")
        ax.set_title(f"{design}: NEMA 34 at {frac * I34:.1f} A ({ss['P_motor_W']:.0f} W) warming up")
        ax.legend(frameon=False)
        ax.grid(alpha=0.3)
        fig.tight_layout()
        fig.savefig(common.OUT / MODULE / f"{out['case']}.png", dpi=130)
        out["png"] = f"out/{MODULE}/{out['case']}.png"
        (common.OUT / MODULE / f"{out['case']}.json").write_text(json.dumps(out, indent=1, default=float))
    except Exception as e:                                 # noqa: BLE001
        out["png_error"] = str(e)[:200]
    print(out["case"], {k_: v for k_, v in out.items() if k_.startswith("t_")}, flush=True)
    return out


# ------------------------------------------------------------------------------------------------ the station's carriage
def ec_parts(v: str = "v3"):
    from cases import station as ST
    P = ST.params(v)
    MAT.add(MAT.Material("N11", 205000.0, 0.29, 0.18e-3 / (28.0 * 28.0 * 45.0), 1e9, "NEMA 11 envelope (0.18 kg)"))
    MAT.add(MAT.Material("EM", 205000.0, 0.29, 0.035e-3 / (math.pi * 100.0 * 15.0), 1e9, "P20/15 electromagnet (35 g)"))
    x1 = round(P.NEMA11_X * 3) / 3.0              # the wall's inner face is at x 68.333 in the STEP (params' 68.3 is rounded)
    z11 = P.NEMA11_Z if v == "v3" else -P.NEMA11_Z

    def n11(g):
        return [g.model.occ.addBox(x1 - 45.0, -14.0, z11 - 14.0, 45.0, 28.0, 28.0)]
    parts = [fem.Part("NEMA 11", n11, None, "N11")]
    if v == "v3":
        dr = P.DOCK_RISE_V3
        face = -18.0 - 2.0 - 0.15 - dr
        cx, cy = P.DOCK_MAG_XY3

        def em(g):
            return [g.model.occ.addCylinder(cx, cy, face - 15.0, 0, 0, 15.0, 10.0)]
        parts.append(fem.Part("electromagnet", em, None, "EM"))
    parts.append(fem.Part("EC", ST.ec_shape(v), None, "PETG"))
    return parts


def solve_ec(v: str = "v3", n11_on: bool = True, em_on: bool = True, T_air: float = T_ROOM, transient_min: float | None = None,
             h: float = 2.5) -> dict:
    parts = ec_parts(v)
    key = ("ec", v, h)
    if key not in _MESH:
        _MESH[key] = fem.mesh_parts(parts, size=h, size_min=0.8, curv=8)
    m = _MESH[key]
    faces = exterior_faces(m)
    kk = {"NEMA 11": K["N11"], "electromagnet": K["EM"], "EC": K["PETG"]}
    k = {nm: kk[nm][0] for nm in m.names}
    cp = {nm: kk[nm][1] for nm in m.names}
    part_of = {nm: nm for nm in m.names}
    eps_of = {"NEMA 11": EPS["motor"], "electromagnet": EPS["magnet"], "EC": EPS["petg"]}
    L_of = {"NEMA 11": 0.028, "electromagnet": 0.02, "EC": 0.06}
    T_guess = {nm: T_air + 20.0 for nm in m.names}
    T11, Tem = T_air + 30.0, T_air + 30.0
    hist = []
    for it in range(1 if transient_min else 4):
        P11 = I11 ** 2 * R11_20 * (1 + ALPHA_CU * (T11 - 20.0)) if n11_on else 0.0
        Pem = EM_W_20 / (1 + ALPHA_CU * (Tem - 20.0)) if (em_on and "electromagnet" in m.names) else 0.0
        hd = fem.HeatDeck(m, k=k, cp=cp, T0=T_air)
        if P11:
            hd.source("NEMA 11", P11)
        if Pem:
            hd.source("electromagnet", Pem)
        boundary(hd, faces, part_of, eps_of, L_of, T_air, T_air, T_guess)
        if transient_min:
            hd.probe("N11", m.nodes_of("NEMA 11"))
            if "electromagnet" in m.names:
                hd.probe("EM", m.nodes_of("electromagnet"))
            hd.probe("ECP", m.nodes_of("EC"))
            hd.transient(transient_min * 60.0, dt0=5.0, dt_max=60.0)
        tag = (f"ec_{v}_{'n11' if n11_on else ''}{'_em' if em_on else ''}" + (f"_{int(transient_min)}min" if transient_min else "")
               + (f"_air{T_air:.0f}" if abs(T_air - T_ROOM) > 0.05 else ""))
        res = hd.solve(f"thermal/{tag}")
        q = face_heat(res, faces, part_of, eps_of, L_of, T_air, T_air, T_guess)
        T_guess = {g: o["T_surface_mean"] for g, o in q.items()}
        T11 = res.T_of("NEMA 11")[2] + 3.0
        Tem = (res.T_of("electromagnet")[2] + 2.0) if "electromagnet" in m.names else T_air
        hist.append(dict(P11=round(P11, 3), Pem=round(Pem, 3), n11_max=round(res.T_of("NEMA 11")[2], 1)))
    ec = res.T_of("EC")
    # PETG next to each source: within 3 mm of it
    from scipy.spatial import cKDTree
    pe = m.nodes_of("EC")
    near = {}
    for src in ("NEMA 11", "electromagnet"):
        if src in m.names:
            dd, _ = cKDTree(m.xyz[m.nodes_of(src)]).query(m.xyz[pe])
            near[src] = round(float(np.nanmax(res.T[pe[dd < 3.0]])), 1)
    rec = dict(module=MODULE, case=tag, design=v, T_air=T_air, P_nema11_W=round(P11, 3), P_electromagnet_W=round(Pem, 3),
               nema11_max=round(res.T_of("NEMA 11")[2], 1), electromagnet_max=round(Tem - 2.0, 1) if Pem else None,
               petg_max=round(ec[2], 1), petg_next_to=near, iterations=hist, nodes=int(m.n), wall_s=round(res.wall, 1))
    if Pem:
        # on a fixed 5 V: I falls as R rises; the pull goes as I^2 (an unsaturated magnet)
        r = 1 + ALPHA_CU * (Tem - 2.0 - 20.0)
        rec["electromagnet_current_frac"] = round(1 / r, 3)
        rec["electromagnet_pull_frac"] = round(1 / r ** 2, 3)
    if transient_min:
        rec["history"] = {kk_: [(round(a, 0), round(b, 2), round(c, 2)) for a, b, c in vv][::3] for kk_, vv in res.history.items()}
    d = common.OUT / MODULE
    d.mkdir(parents=True, exist_ok=True)
    if not transient_min:
        try:
            fem.render_T(res, d / f"{tag}.png", title=f"{v} electronics carriage: NEMA 11 {P11:.2f} W"
                         + (f", electromagnet {Pem:.2f} W" if Pem else "") + f", air {T_air:.0f} °C", view=(-0.6, -1.0, -0.5), up=(0, 0, -1))
            rec["png"] = f"out/{MODULE}/{tag}.png"
        except Exception as e:                            # noqa: BLE001
            rec["png_error"] = str(e)[:200]
    (d / f"{tag}.json").write_text(json.dumps(rec, indent=1, default=float))
    print(tag, f"NEMA 11 {rec['nema11_max']} C, PETG {rec['petg_max']} C, near {near}", flush=True)
    return rec


_MESH = {}


def run(which=("motor", "ec")):
    out = {}
    if "motor" in which:
        for des in ("chain-carousel-v3", "chain-carousel-v4", "paternoster"):
            for frac in (1.0, 0.7, 0.5, 0.25):
                out[f"{des}_{frac}"] = solve_motor(des, frac)
        # material and finish of v4's back plate: black-anodised 6061, or steel (the stiffer plate the vibration
        # study looks at)
        out["v4_black"] = solve_motor("chain-carousel-v4", 1.0, finish="al_black", tag="chain-carousel-v4_motor_100_black")
        out["v4_steel"] = solve_motor("chain-carousel-v4", 1.0, plate_mat="STEEL_PLATE", tag="chain-carousel-v4_motor_100_steel")
        out["v3_black_50"] = solve_motor("chain-carousel-v3", 0.5, finish="al_black", tag="chain-carousel-v3_motor_50_black")
    if "warmup" in which:
        out["warmup"] = warmup("chain-carousel-v3", 1.0)
    if "ec" in which:
        T_in = T_ROOM
        f = common.OUT / MODULE / "chain-carousel-v3_motor_50.json"
        if f.exists():
            T_in = json.loads(f.read_text())["T_enclosure_air"]
        out["ec_room"] = solve_ec("v3", T_air=T_ROOM)
        out["ec_hot"] = solve_ec("v3", T_air=T_in)
        out["ec_30min"] = solve_ec("v3", T_air=T_ROOM, transient_min=30.0)
        out["ec_v4"] = solve_ec("v4", em_on=False, T_air=T_ROOM)
    return out


if __name__ == "__main__":
    run(tuple(sys.argv[1:]) or ("motor", "warmup", "ec"))


def summary() -> str:
    """out/thermal/SUMMARY.md from the cases' JSON."""
    d = common.OUT / MODULE
    L = ["# Heat (generated by cases/thermal.py)", "",
         f"Room {T_ROOM:.0f} °C. The NEMA 34's loss is 2 I^2 R with R 0.7 ohm per phase at 20 °C, rising with its winding's "
         "temperature; v3 and v4 put it inside their closed acrylic enclosures, the paternoster in the room. Motor and plate "
         "shed heat by natural convection and radiation; the enclosure passes it to the room through its walls.", "",
         "## The NEMA 34 on its wall", "",
         "| design | current (A) | loss (W) | motor case, hottest (°C) | winding, estimated (°C) | encoder end (°C) | back plate, hottest (°C) | "
         "printed parts on the back plate, hottest (°C) | enclosure air (°C) |", "|---|---|---|---|---|---|---|---|---|"]
    rows = []
    for f in sorted(d.glob("*_motor_*.json")):
        r = json.loads(f.read_text())
        rows.append(r)
    order = {"chain-carousel-v3": 0, "chain-carousel-v4": 1, "paternoster": 2}
    rows.sort(key=lambda r: (order.get(r["design"], 9), -r["current_frac"], r["case"]))
    for r in rows:
        tag = r["design"].replace("chain-carousel-", "")
        extra = []
        if r["plate"] == "STEEL_PLATE":
            extra.append("steel back plate")
        elif r.get("plate_finish") == "al_black":
            extra.append("black-anodised back plate")
        if extra:
            tag += f" ({', '.join(extra)})"
        pp = r["printed_parts_on_back_plate_max_C"]
        ppt = f"{max(pp.values()):.0f} ({max(pp, key=pp.get)})" if pp else "-"
        L.append(f"| {tag} | {r['current_A']:.1f} | {r['P_motor_W']:.1f} | {r['motor_case_max']:.0f} | {r['winding_est']:.0f} | "
                 f"{r['encoder_end']:.0f} | {r['plate_max']:.0f} | {ppt} | "
                 f"{r['T_enclosure_air']:.1f} |" if r["T_enclosure_air"] is not None else
                 f"| {tag} | {r['current_A']:.1f} | {r['P_motor_W']:.1f} | {r['motor_case_max']:.0f} | {r['winding_est']:.0f} | "
                 f"{r['encoder_end']:.0f} | {r['plate_max']:.0f} | {ppt} | room |")
    for f in sorted(d.glob("*_warmup_*.json")):
        r = json.loads(f.read_text())
        L += ["", f"**Warm-up** ({r['case']}, {r['P_W']:.0f} W): the motor gets 63 % of the way to its steady temperature in "
                  f"{r.get('t_63pct_min')} min, 90 % in {r.get('t_90pct_min')} min and 95 % in {r.get('t_95pct_min')} min."]
    L += ["", "## The station's electronics carriage (printed PETG) with its NEMA 11 and dock electromagnet", "",
          "| case | air (°C) | NEMA 11 (W) | electromagnet (W) | NEMA 11, hottest (°C) | electromagnet (°C) | PETG next to the NEMA 11 (°C) | "
          "PETG next to the electromagnet (°C) | the electromagnet's pull, of cold |", "|---|---|---|---|---|---|---|---|---|"]
    for f in sorted(d.glob("ec_*.json")):
        r = json.loads(f.read_text())
        if "history" in r:
            continue
        nt = r["petg_next_to"]
        L.append(f"| {r['case']} | {r['T_air']:.1f} | {r['P_nema11_W']:.2f} | {r['P_electromagnet_W']:.2f} | {r['nema11_max']:.0f} | "
                 f"{r['electromagnet_max'] if r['electromagnet_max'] is not None else '-'} | {nt.get('NEMA 11', '-')} | {nt.get('electromagnet', '-')} | "
                 f"{r.get('electromagnet_pull_frac', '-')} |")
    for f in sorted(d.glob("ec_*min.json")):
        r = json.loads(f.read_text())
        h = r.get("history", {})
        parts = []
        for k, lab in (("N11", "NEMA 11"), ("EM", "electromagnet"), ("ECP", "PETG")):
            if k in h and h[k]:
                parts.append(f"{lab} {h[k][-1][2]:.0f} °C")
        L += ["", f"**After 30 minutes switched on** (from cold, air {r['T_air']:.0f} °C): " + ", ".join(parts) + "."]
    txt = "\n".join(L) + "\n"
    (d / "SUMMARY.md").write_text(txt)
    return txt
