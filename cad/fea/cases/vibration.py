"""Vibration: will the rig shake itself apart? The frames' forced response to the NEMA 34's torque ripple (CalculiX
*STEADY STATE DYNAMICS on the frame models of frame.py), then what that does to the bolted joints (slip at a joint is
what lets a screw self-loosen), to the plates (fatigue), and how long the rig takes to settle for the balance.

    python cases/vibration.py                 # every case
    python cases/vibration.py frf panels      # some

Excitation. A microstepped hybrid stepper's torque ripples at its full-step rate (four per electrical cycle: detent
torque and the departure of its torque-angle curve from a sine), here f = v / 304.8 mm * 200 (one 32T turn per motor
turn). The ripple's size isn't on the motor's sheet; 3 % of the 12 N*m holding torque (0.4 N*m) is used as the
nominal, and every result is also given per N*m, so it scales. The ripple acts on the stator; at these frequencies the
loop's inertia (about 37x the rotor's) holds the rotor still, so the same ripple goes out through the drive chain: the
frame sees the jam's load pattern (frame.py), oscillating, at 1 N*m. Without microstepping (full steps) every step is
an impulse and this model doesn't apply.
The other sources are much smaller: the 32T sprockets' chordal action (a 0.1 N force ripple on the loop at 100 mm/s),
the P16, the solenoid's 3 N taps on the electronics carriage and the 10 mm ERM on the hopper (both on the module, not
the frame).
Damping: 2 % of critical in every mode (bolted aluminium frames: 1-5 %); 1 % is given as the bound.
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

MODULE = "vibration"
RIPPLE_NM = 0.4                      # nominal torque ripple at the full-step rate (3 % of 12 N*m)
ZETA = 0.02
MU = 0.15                            # friction under a screw head / between clamped parts (steel on aluminium, dry; conservative)
# preloads from a tightening torque: F = T / (K d), K = 0.2 (dry, plain)
def preload(T_Nm: float, d_mm: float, K: float = 0.2) -> float:
    return T_Nm * 1000.0 / (K * d_mm)


AL6061_FATIGUE = 96.5                # MPa, fully reversed at 5e8 cycles (MIL-HDBK-5 / ASM)
BOLT_SQ_34 = 69.6                    # NEMA 34 bolt square, mm


def drive_ripple_loads(d: fem.Deck, D: dict, m: fem.Mesh, torque: float = 1.0) -> dict:
    """The jam's load pattern from frame.solve_static at `torque` N*m and no static parts (no gravity, no pretension,
    no slack-side 10 N): stator reaction on the motor body, drive-chain pull between the 15T sprockets, the bottom
    runs' extra tension pulling B+ and B- together (v3/v4); motor reaction and the two drive sprockets (paternoster)."""
    P = D["P"]
    desc = {}
    if D["design"].startswith("chain-carousel"):
        F = torque * 1000.0 / LD.V2_R15_MM
        spm = [np.array(p["M"])[:3, 3] for p in D["pl"] if p["key"] == "sprocket_15_motor"][0]
        sps = [np.array(p["M"])[:3, 3] for p in D["pl"] if p["key"] == "sprocket_15_shaft"][0]
        nb = [n for k, n, M in D["shafts"] if "B+" in n][0]
        ib = m.nodes_of(nb)
        sh = ib[(np.abs(m.xyz[ib, 0] - sps[0]) < 9.0)]
        mo = m.nodes_of("NEMA 34")
        tip = mo[(np.abs(m.xyz[mo, 0] - spm[0]) < 9.0) & (np.hypot(m.xyz[mo, 1] - spm[1], m.xyz[mo, 2] - spm[2]) < 7.5)]
        d.force(tip, (0, 0, +F))
        d.force(sh, (0, 0, -F))
        ax = D["motor"][:3, 2]
        face = D["motor"][:3, 3]
        ax_c = (m.xyz[mo] - face) @ ax
        body = mo[(ax_c > -100.0) & (ax_c < -60.0)]
        r, q = d.rigid_patch(body, "MOTORBODY")
        d.node_load(r, M=tuple(torque * 1000.0 * ax), rot=q)
        dT = 0.5 * torque * 1000.0 / P.R
        for k2, n2, M2 in D["sprockets"]:
            if "B+" in n2:
                d.force(m.nodes_of(n2), (0, -dT, 0))
            if "B-" in n2:
                d.force(m.nodes_of(n2), (0, +dT, 0))
        desc = dict(chain_pull_N=F, bottom_run_N=dT)
    else:
        r, q = d.rigid_patch(m.nodes_of("NEMA 34"), "MOTORBODY")
        ax = D["motor"][:3, 2]
        d.node_load(r, M=tuple(torque * 1000.0 * ax), rot=q)
        sps = [n for k, n, M in D["sprockets"] if "+1y" in n and "bottom" in n]
        for i, sn in enumerate(sps):
            rr, qq = d.rigid_patch(m.nodes_of(sn), f"SP{i}")
            d.node_load(rr, M=tuple(-0.5 * torque * 1000.0 * ax), rot=qq)
        desc = dict(note="reaction on the motor, out through both drive sprockets")
    return desc


def speed_of(f_hz: float) -> float:
    """Chain speed (mm/s) at which the NEMA 34's full-step rate is f."""
    return f_hz * LD.SPROCKET_CIRC_MM / LD.FULL_STEPS_PER_REV


def probes(D: dict, m: fem.Mesh) -> dict:
    mp = FR.motor_points(D)
    out = {k: FR.nearest(m, mp[k], "NEMA 34") for k in ("com", "enc", "shaft")}
    tr = [n for n in m.names if n.startswith("Top rail") and "+y" in n]
    if tr:
        idx = m.nodes_of(tr[0])
        xm = np.median(m.xyz[idx, 0])
        out["top_rail"] = idx[np.argmin(np.abs(m.xyz[idx, 0] - xm) + 1e-3 * np.abs(m.xyz[idx, 2] - m.xyz[idx, 2].max()))]
    fp = [k for k, M in D["plates"] if k == "side_plate_front"]
    if fp:
        idx = m.nodes_of("side_plate_front")
        top = idx[np.argsort(-m.xyz[idx, 2])[:200]]
        out["front_plate_top"] = top[np.argmin(np.abs(m.xyz[top, 1]))]
    return out


def frf(design: str, variant: str = "pads", f_lo: float = 5.0, f_hi: float = 140.0, n_modes: int = 20, zeta: float = ZETA,
        h: float = 12.0) -> dict:
    D, m, pads = FR.frame_mesh(design, variant, h)
    d = fem.Deck(m)
    FR.feet_fix(d, D)
    desc = drive_ripple_loads(d, D, m, 1.0)
    pr = probes(D, m)
    for k, i in pr.items():
        d.nset(f"PR_{k.upper()}", [i])
    modes = json.loads((common.OUT / "frame" / f"{design}_{variant}_modes.json").read_text())["freqs_Hz"]
    f_motor = {"chain-carousel-v3": modes[3], "chain-carousel-v4": modes[3], "paternoster": modes[3]}.get(design, modes[3])
    # whole fields at the first sway mode and the motor's mode(s) (the paternoster's swings sideways at mode 2 too)
    pick = [0, 3] if design.startswith("chain-carousel") else [1, 3, 4]
    field_at = sorted({round(modes[i], 3) for i in pick if i < len(modes)})
    d.steady_state(f_lo, f_hi, 12, zeta=zeta, n_modes=n_modes, prints=[f"PR_{k.upper()}" for k in pr], field_at=field_at)
    res = d.solve(f"vibration/{design}_{variant}_frf_z{int(zeta * 1000)}")
    H = {}
    for k, i in pr.items():
        hh = res.harmonic.get(f"PR_{k.upper()}")
        if hh is None:
            continue
        H[k] = (hh["f"], hh[i + 1])
    f = next(iter(H.values()))[0]
    # per N*m: displacement amplitude (um), acceleration (m/s^2)
    curves = {k: dict(u_um=(np.linalg.norm(np.abs(v), axis=1) * 1000.0).round(4).tolist(),
                      a_ms2=(np.linalg.norm(np.abs(v), axis=1) * (2 * np.pi * f) ** 2 / 1000.0).round(5).tolist())
              for k, (f_, v) in H.items()}
    # each resonance below 100 Hz: the field -> peak dynamic stress in the plates, the pads' transverse loads, the motor flange
    plates = [k for k, M in D["plates"]] + (["motor plate"] + [f"standoff {i}" for i in range(1, 5)] if design == "paternoster" else [])
    fixed = d.nsets["FEET"] - 1
    excl = np.concatenate([fixed] + [m.nodes_of(n) for n, p in pads]) if pads else fixed
    from scipy.spatial import cKDTree
    dist, _ = cKDTree(m.xyz[excl]).query(m.xyz)
    far = dist > 4.0
    vol = m.volumes()
    rho = np.array([MAT.get(d.mat_override.get(nm, mt)).rho for nm, mt in zip(m.names, m.materials)])[m.part]
    nm_ = np.zeros(m.n)
    np.add.at(nm_, m.tet[:, :4].ravel(), np.repeat(vol * rho / 4.0, 4))
    mo = m.nodes_of("NEMA 34")
    peaks = []
    # each field step gives a few frequencies round its eigenfrequency: keep the one where the motor moves most
    chosen = {}
    for fr, (Uc, Sc) in res.fields.items():
        tgt = min(field_at, key=lambda t: abs(t - fr))
        a = float(np.linalg.norm(np.abs(Uc[pr["com"]])))
        if tgt not in chosen or a > chosen[tgt][0]:
            chosen[tgt] = (a, fr)
    for tgt in sorted(chosen):
        fr = chosen[tgt][1]
        Uc, Sc = res.fields[fr]
        vm = fem.harmonic_vm(Sc)
        row = dict(f_Hz=fr, speed_mm_s=round(speed_of(fr), 1))
        best = (0.0, None)
        for pk in plates:
            idx = m.nodes_of(pk)
            idx = idx[far[idx]]
            k = idx[np.argmax(vm[idx])]
            if vm[k] > best[0]:
                best = (float(vm[k]), pk)
        row["plate_vm_per_Nm"] = round(best[0], 4)
        row["plate_vm_at"] = best[1]
        # pads: traction on the plate-normal plane (x) times the pad's area -> transverse / normal force per screw
        pt = []
        for nmp, p0 in pads:
            idx = m.nodes_of(nmp)
            s = Sc[idx].mean(0)
            Ft = math.pi * FR.PAD_R ** 2 * math.sqrt(abs(s[3]) ** 2 + abs(s[5]) ** 2)
            Fn = math.pi * FR.PAD_R ** 2 * abs(s[0])
            pt.append((Ft, Fn, nmp))
        if pt:
            ft = max(pt)
            row["pad_transverse_per_Nm_N"] = round(ft[0], 4)
            row["pad_normal_per_Nm_N"] = round(max(p[1] for p in pt), 4)
            row["pad_worst"] = ft[2]
        # the motor on its flange: inertial force (w^2 m u) + the chain pull on its shaft, shared by 4 screws, plus the
        # ripple torque about its axis on the 4 screws at r = 49.2 mm
        w2 = (2 * math.pi * fr) ** 2
        Fin = w2 * (nm_[mo, None] * Uc[mo]).sum(0)                  # complex (3,), N (t * mm/s^2)
        if design.startswith("chain-carousel"):
            Fin = Fin + np.array([0, 0, 1000.0 / LD.V2_R15_MM])
        ax = D["motor"][:3, 2]
        Ft_m = Fin - np.dot(Fin, ax) * ax
        F_scr = np.linalg.norm(np.abs(Ft_m)) / 4.0 + 1000.0 / (4 * (BOLT_SQ_34 / 2) * math.sqrt(2))
        row["motor_screw_transverse_per_Nm_N"] = round(float(F_scr), 3)
        row["motor_com_u_um"] = round(float(np.linalg.norm(np.abs(Uc[pr["com"]])) * 1000), 3)
        peaks.append(row)
    rec = dict(module=MODULE, case=f"{design}_{variant}_frf", design=design, variant=variant, zeta=zeta, loads=desc,
               eigen_Hz=[round(x, 2) for x in res.freqs], f_Hz=f.round(3).tolist(), speed_mm_s=[round(speed_of(x), 1) for x in f],
               per_Nm=curves, resonances=peaks, nodes=int(m.n), wall_s=round(res.wall, 1))
    d_out = common.OUT / MODULE
    d_out.mkdir(parents=True, exist_ok=True)
    (d_out / f"{rec['case']}.json").write_text(json.dumps(rec, indent=1, default=float))
    # picture of the worst resonance's stress
    if res.fields:
        worst = max(peaks, key=lambda r: r.get("motor_screw_transverse_per_Nm_N", 0))
        Uc, Sc = res.fields[worst["f_Hz"]]
        res.U = (Uc * np.exp(1j * np.angle(Uc[pr["com"]][np.argmax(np.abs(Uc[pr["com"]]))]) * -1)).real
        res.S = (Sc * np.exp(-1j * np.angle(Uc[pr["com"]][np.argmax(np.abs(Uc[pr["com"]]))]))).real
        res.vm = fem.harmonic_vm(Sc) * RIPPLE_NM
        res.deck.step = ("static", {})
        try:
            fem.render(res, d_out / f"{rec['case']}.png", field="vm", view=(1.2, -1.0, 0.6),
                       title=f"{design}: {RIPPLE_NM} N*m torque ripple at {worst['f_Hz']:.1f} Hz ({worst['speed_mm_s']:.0f} mm/s), "
                             f"{zeta * 100:.0f} % damping\nstress amplitude (MPa)")
            rec["png"] = f"out/{MODULE}/{rec['case']}.png"
        except Exception as e:                             # noqa: BLE001
            rec["png_error"] = str(e)[:200]
        (d_out / f"{rec['case']}.json").write_text(json.dumps(rec, indent=1, default=float))
    print(rec["case"], [(r["f_Hz"], r.get("motor_screw_transverse_per_Nm_N"), r["plate_vm_per_Nm"]) for r in peaks], flush=True)
    return rec


def refresh_curves(case: str, zeta: float = ZETA) -> dict:
    """Re-read a finished run's probe curves from its .dat (the parser once doubled the duplicated eigenfrequency
    points); the resonance rows come from the .frd and are unaffected."""
    f = common.OUT / MODULE / f"{case}_frf.json"
    r = json.loads(f.read_text())
    dat = (fem.WORK / "vibration" / f"{case}_frf_z{int(zeta * 1000)}" / "job.dat").read_text()
    hp = fem._ssd_prints(dat)
    curves = {}
    fr = None
    for name, hh in hp.items():
        k = name[3:].lower()
        nid = [x for x in hh if x != "f"][0]
        fr = hh["f"]
        u = np.linalg.norm(np.abs(hh[nid]), axis=1)
        curves[k] = dict(u_um=(u * 1000.0).round(4).tolist(), a_ms2=(u * (2 * np.pi * fr) ** 2 / 1000.0).round(5).tolist())
    r["per_Nm"] = curves
    r["f_Hz"] = fr.round(3).tolist()
    r["speed_mm_s"] = [round(speed_of(x), 1) for x in fr]
    f.write_text(json.dumps(r, indent=1, default=float))
    return r


def plot_frfs(cases: list):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axs = plt.subplots(2, 1, figsize=(8, 7), sharex=True)
    cols = {"chain-carousel-v3_pads": "#1b9e77", "chain-carousel-v4_pads": "#d95f02", "chain-carousel-v4_motorpost2": "#7570b3",
            "paternoster_pads": "#e7298a"}
    lab = {"chain-carousel-v3_pads": "v3", "chain-carousel-v4_pads": "v4", "chain-carousel-v4_motorpost2": "v4 + two motor posts",
           "paternoster_pads": "paternoster"}
    for c in cases:
        r = json.loads((common.OUT / MODULE / f"{c}_frf.json").read_text())
        v = np.array(r["speed_mm_s"])
        for ax, key, sc, yl in ((axs[0], "enc", 1.0, "motor's encoder end (µm)"), (axs[1], "top_rail", 1.0, "top rail, middle (µm)")):
            if key in r["per_Nm"]:
                ax.semilogy(v, np.array(r["per_Nm"][key]["u_um"]) * RIPPLE_NM, color=cols.get(c), label=lab.get(c, c))
                ax.set_ylabel(yl)
    for ax in axs:
        ax.grid(alpha=0.3, which="both")
        ax.axvspan(0, 100, color="#999999", alpha=0.08)
    axs[0].legend(frameon=False, ncol=2)
    axs[0].set_title(f"Vibration amplitude from a {RIPPLE_NM} N*m torque ripple at the full-step rate ({ZETA * 100:.0f} % damping)")
    axs[1].set_xlabel("chain speed (mm/s); full-step rate = speed / 304.8 mm x 200")
    fig.tight_layout()
    fig.savefig(common.OUT / MODULE / "frf_vs_speed.png", dpi=130)


# ------------------------------------------------------------------------------------------------ joints, by hand
def joints(frfs: dict) -> dict:
    """Every bolted joint the vibration loads: its preload, friction capacity and the dynamic transverse load at the
    worst speed from the FRFs (nominal ripple), and the ripple at which it would slip. A joint that never slips
    can't self-loosen (Junker); nylon inserts and threadlocker are the second line."""
    rows = []
    for c, r in frfs.items():
        worst = max(r["resonances"], key=lambda x: x.get("motor_screw_transverse_per_Nm_N", 0)) if r["resonances"] else None
        if worst is None:
            continue
        Fp = preload(3.0, 5.0)                               # M5 18-8 at 3 N*m (frame.py's motor-screw check)
        cap = MU * Fp
        Fd = worst["motor_screw_transverse_per_Nm_N"] * RIPPLE_NM
        rows.append(dict(design=c, joint="NEMA 34 flange, 4 x M5 18-8 in slots, 3 N*m", preload_N=round(Fp), friction_cap_N=round(cap),
                         dynamic_N=round(Fd, 2), at_Hz=worst["f_Hz"], at_mm_s=worst["speed_mm_s"], sf=round(cap / max(Fd, 1e-9), 1),
                         slips_at_ripple_Nm=round(cap / worst["motor_screw_transverse_per_Nm_N"], 1)))
        pw = max(r["resonances"], key=lambda x: x.get("pad_transverse_per_Nm_N", 0))
        if "pad_transverse_per_Nm_N" in pw:
            Fp2 = preload(2.5, 5.0)                          # M5 button head into a drop-in T-nut, 2.5 N*m (the nut's limit)
            cap2 = MU * Fp2
            Fd2 = pw["pad_transverse_per_Nm_N"] * RIPPLE_NM
            rows.append(dict(design=c, joint="side plate to post, M5 x 12 into a T-nut, 2.5 N*m, blue threadlocker",
                             preload_N=round(Fp2), friction_cap_N=round(cap2), dynamic_N=round(Fd2, 3), at_Hz=pw["f_Hz"],
                             at_mm_s=pw["speed_mm_s"], sf=round(cap2 / max(Fd2, 1e-9), 1),
                             slips_at_ripple_Nm=round(cap2 / max(pw["pad_transverse_per_Nm_N"], 1e-9), 1), worst_pad=pw.get("pad_worst")))
        pv = max(r["resonances"], key=lambda x: x["plate_vm_per_Nm"])
        rows.append(dict(design=c, joint="plate fatigue (6061-T6, 96.5 MPa fully reversed at 5e8 cycles)",
                         dynamic_MPa=round(pv["plate_vm_per_Nm"] * RIPPLE_NM, 3), at_Hz=pv["f_Hz"], at_mm_s=pv["speed_mm_s"],
                         sf=round(AL6061_FATIGUE / max(pv["plate_vm_per_Nm"] * RIPPLE_NM, 1e-9), 0),
                         where=pv["plate_vm_at"]))
    return rows


def hand_checks() -> dict:
    """What the frame model doesn't cover, by hand."""
    out = {}
    # settling after a stop: the slowest mode decays as exp(-zeta w t)
    for des, f1 in (("chain-carousel-v3", 19.35), ("chain-carousel-v4", 15.23), ("paternoster", 15.48)):
        out[f"settle_{des}"] = {f"zeta {z}": dict(to_1pct_s=round(math.log(100) / (z * 2 * math.pi * f1), 2),
                                                 to_0p1pct_s=round(math.log(1000) / (z * 2 * math.pi * f1), 2)) for z in (0.01, 0.02)}
    # the chain's vertical runs as strings carrying the carriages, against the 32T sprockets' tooth-pass rate
    T = LD.V2_TENSION_N
    mu = LD.CHAIN_KG_M + LD.V2_N_MODULES * (LD.V3_MODULE_KG + LD.V3_CARRIAGE_KG) / 2 / (104 * 9.525e-3)
    for run, L in (("vertical run (228.6 mm)", 0.2286), ("horizontal run (114.3 mm)", 0.1143)):
        f1 = 1 / (2 * L) * math.sqrt(T / mu)
        out[f"strand_{run}"] = dict(f1_Hz=round(f1, 1), mesh_rate_reaches_it_at_mm_s=round(f1 * 9.525, 0),
                                    note="32T tooth-pass rate = v / 9.525 mm; the chordal rise is 0.23 mm, so a resonant strand "
                                         "swings a few tenths of a mm to about 1 mm")
    # the back 32T sprockets: two 1/4-20 cup-point set screws on a 5/8 in shaft, each at half its catalogue holding power
    # (4.4 kN at full seating torque), since a set screw on the round of a shaft is rarely seated that well
    hold = 2 * 2200.0 * 15.875 / 2 / 1000.0
    out["set_screws"] = dict(torque_capacity_Nm=round(hold, 1), jam_share_Nm=LD.NEMA34_HOLD_NM / 2, sf=round(hold / (LD.NEMA34_HOLD_NM / 2), 1),
                             note="each start, stop and reversal works a set screw; Loctite 243 and a dimple under each (the BoM) keep it")
    # the A-1 tab screws: M3 through the printed carriage into a nylon-insert nut in the printed hook
    out["a1_screws"] = dict(note="the printed seat creeps (18 MPa under the button head at a 300 N snug clamp, RESULTS change 11), so the "
                                 "preload falls over days; the nylon insert stops the nut turning off but the joint can then fret. "
                                 "The DIN 433 washer and a re-check after a week are the fix")
    return out


# ------------------------------------------------------------------------------------------------ the acrylic panels
def panel_modes(design: str = "chain-carousel-v3", n: int = 8) -> dict:
    """Each 3 mm acrylic panel on its nylon standoffs (held at their 10 mm faces): its modes against the full-step band."""
    MAT.add(MAT.Material("ACRYLIC", 3200.0, 0.37, 1.19e-9, 30.0, "cast acrylic"))
    pl = fem.placements(design)
    st = [np.array(p["M"]) for p in pl if p["key"] in ("standoff", "standoff_back")]
    out = {}
    for key in ("panel_side", "panel_side_hatch", "panel_front_hatch", "panel_back", "panel_top"):
        M = [np.array(p["M"]) for p in pl if p["key"] == key]
        if not M:
            continue
        m = fem.mesh_parts([fem.Part(key, fem.step_path(design, key), M[0], "ACRYLIC")], size=7.0, size_min=1.5, curv=0)
        idx = []
        for S in st:
            o, a = S[:3, 3], S[:3, 2]
            rel = m.xyz - o
            along = rel @ a
            rad = np.linalg.norm(rel - np.outer(along, a), axis=1)
            sel = np.where((rad < 5.0) & (np.abs(along) < 40.0))[0]
            idx += list(sel)
        if len(idx) < 3:
            out[key] = dict(error="no standoffs found on it")
            continue
        d = fem.Deck(m)
        d.fix(idx)
        d.frequency(n)
        res = d.solve(f"vibration/panel_{design}_{key}")
        bb = np.ptp(m.xyz, axis=0)
        n_st = 0
        for S in st:
            rel = m.xyz - S[:3, 3]
            al = rel @ S[:3, 2]
            n_st += int(((np.linalg.norm(rel - np.outer(al, S[:3, 2]), axis=1) < 5.0) & (np.abs(al) < 40.0)).any())
        out[key] = dict(size_mm=sorted([round(float(x)) for x in bb])[1:], standoffs=n_st,
                        freqs_Hz=[round(f, 1) for f in res.freqs],
                        full_step_rate_reaches_mode1_at_mm_s=round(speed_of(res.freqs[0]), 0) if res.freqs else None)
        try:
            fem.render(res, common.OUT / MODULE / f"panel_{design}_{key}_mode1.png", field="u", mode=0,
                       title=f"{design}: {key}, mode 1, {res.freqs[0]:.1f} Hz", view=(1.0, -1.0, 0.6))
        except Exception:                                    # noqa: BLE001
            pass
        print(design, key, out[key], flush=True)
    (common.OUT / MODULE / f"panels_{design}.json").write_text(json.dumps(out, indent=1, default=float))
    return out


CASES = ["chain-carousel-v3_pads", "chain-carousel-v4_pads", "chain-carousel-v4_motorpost2", "paternoster_pads"]


def run(which=("frf", "panels", "joints")):
    (common.OUT / MODULE).mkdir(parents=True, exist_ok=True)
    if "frf" in which:
        for c in CASES:
            des, var = c.rsplit("_", 1)
            frf(des, var)
    if "panels" in which:
        for des in ("chain-carousel-v3", "chain-carousel-v4"):
            panel_modes(des)
    if "joints" in which:
        frfs = {}
        for c in CASES:
            f = common.OUT / MODULE / f"{c}_frf.json"
            if f.exists():
                frfs[c] = json.loads(f.read_text())
        plot_frfs([c for c in CASES if c in frfs])
        out = dict(ripple_Nm=RIPPLE_NM, zeta=ZETA, mu=MU, joints=joints(frfs), hand=hand_checks())
        (common.OUT / MODULE / "joints.json").write_text(json.dumps(out, indent=1, default=float))
        print(json.dumps(out, indent=1, default=float)[:3000])


if __name__ == "__main__":
    run(tuple(sys.argv[1:]) or ("frf", "panels", "joints"))


def summary() -> str:
    d = common.OUT / MODULE
    L = ["# Vibration (generated by cases/vibration.py)", "",
         f"Forced response of each frame (frame.py's screw-pad model, feet held) to the NEMA 34's torque ripple at its full-step "
         f"rate, by modal superposition (CalculiX *STEADY STATE DYNAMICS, {ZETA * 100:.0f} % damping in every mode). Numbers are "
         f"at a {RIPPLE_NM} N*m ripple (3 % of the holding torque) and scale with it.", ""]
    for c in CASES:
        f = d / f"{c}_frf.json"
        if not f.exists():
            continue
        r = json.loads(f.read_text())
        L += [f"## {c.replace('chain-carousel-', '').replace('_pads', '').replace('_motorpost2', ' + two motor posts')}", "",
              f"Modes (Hz): {', '.join(f'{x:.1f}' for x in r['eigen_Hz'][:8])}.", "",
              "| resonance (Hz) | at chain speed (mm/s) | motor centre moves (µm) | peak plate stress (MPa) | where | worst side-plate screw, sideways (N) | "
              "each motor screw, sideways (N) |", "|---|---|---|---|---|---|---|"]
        for p in r["resonances"]:
            L.append(f"| {p['f_Hz']:.1f} | {p['speed_mm_s']:.0f} | {p['motor_com_u_um'] * RIPPLE_NM:.1f} | {p['plate_vm_per_Nm'] * RIPPLE_NM:.2f} | "
                     f"{p['plate_vm_at']} | {p.get('pad_transverse_per_Nm_N', 0) * RIPPLE_NM:.2f} | {p['motor_screw_transverse_per_Nm_N'] * RIPPLE_NM:.1f} |")
        L.append("")
    f = d / "joints.json"
    if f.exists():
        j = json.loads(f.read_text())
        L += ["## Joints: does anything slip (and so self-loosen)?", "",
              f"Friction coefficient {MU}; preload from the tightening torque, F = T / (0.2 d).", "",
              "| design | joint | preload (N) | friction holds (N) | dynamic load (N or MPa) | at (mm/s) | safety factor | slips at a ripple of (N*m) |",
              "|---|---|---|---|---|---|---|---|"]
        for row in j["joints"]:
            dyn = row.get("dynamic_N", row.get("dynamic_MPa"))
            L.append(f"| {row['design'].replace('chain-carousel-', '')} | {row['joint']} | {row.get('preload_N', '-')} | {row.get('friction_cap_N', '-')} | "
                     f"{dyn} | {row['at_mm_s']:.0f} | {row['sf']} | {row.get('slips_at_ripple_Nm', '-')} |")
        h = j["hand"]
        L += ["", "## By hand", ""]
        for k, v in h.items():
            L.append(f"- **{k}**: {json.dumps(v)}")
    for des in ("chain-carousel-v3", "chain-carousel-v4"):
        f = d / f"panels_{des}.json"
        if f.exists():
            pj = json.loads(f.read_text())
            L += ["", f"## {des}: the 3 mm acrylic panels on their standoffs", "",
                  "| panel | size (mm) | modes (Hz) | full-step rate reaches mode 1 at (mm/s) |", "|---|---|---|---|"]
            for k, v in pj.items():
                if "freqs_Hz" in v:
                    L.append(f"| {k} | {' x '.join(str(x) for x in v['size_mm'])} | {', '.join(f'{x:.0f}' for x in v['freqs_Hz'][:6])} | "
                             f"{v['full_step_rate_reaches_mode1_at_mm_s']:.0f} |")
    txt = "\n".join(L) + "\n"
    (d / "SUMMARY.md").write_text(txt)
    return txt
