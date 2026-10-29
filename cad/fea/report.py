"""Collect every case's JSON (out/<module>/*.json) into out/SUMMARY.md, plus two hand checks that need the models' masses:
tipping under a push on the top rail, and the frames' natural frequencies against the NEMA 34's step rates.

    python report.py
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import loads as LD  # noqa: E402

OUT = HERE / "out"
LABEL = {"chain-carousel-v3": "v3", "chain-carousel-v4": "v4", "paternoster": "paternoster", "chain-carousel-v2": "v2"}


def load(module: str) -> list[dict]:
    d = OUT / module
    if not d.exists():
        return []
    out = []
    for f in sorted(d.glob("*.json")):
        try:
            r = json.loads(f.read_text())
        except json.JSONDecodeError:
            continue
        if isinstance(r, dict) and "case" in r and r.get("kind") != "mass":
            out.append(r)
    return out


def fmt(v, nd=3):
    if v is None:
        return ""
    if isinstance(v, float):
        if v == 0:
            return "0"
        if abs(v) >= 100:
            return f"{v:.0f}"
        return f"{v:.{nd}g}"
    return str(v)


def static_rows(recs: list[dict]) -> list[str]:
    rows = ["| design | case | part | max displacement (mm) | peak von Mises (MPa) | allowable (MPa) | safety factor | functional numbers |",
            "|---|---|---|---|---|---|---|---|"]
    for r in recs:
        if "parts" not in r:
            continue
        kd = "; ".join(f"{k} {fmt(v)}" for k, v in list(r.get("key_disp", {}).items())[:6])
        for p in r["parts"]:
            part = r["part"] if len(r["parts"]) == 1 else p["part"]
            rows.append(f"| {LABEL.get(r['design'], r['design'])} | {r['load_case']} | {part} | {fmt(p['umax_mm'])} | "
                        f"{fmt(p['vm_excl_MPa'])} | {fmt(p['allow_MPa'])} | {fmt(p['sf'])} | {kd} |")
            kd = ""
    return rows


def frame_modes() -> list[str]:
    rows = []
    recs = [r for r in load("frame") if r.get("load_case") == "modes"]
    if not recs:
        return rows
    v_list = (25.0, 50.0, 100.0, 130.0)
    rows += ["| design | joint | f1-f6 (Hz) | what moves in modes 1-3 |", "|---|---|---|---|"]
    for r in recs:
        f = r.get("freqs_Hz", [])[:6]
        tops = []
        for mm in r.get("modes", [])[:3]:
            tops.append("/".join(f"{k} {int(round(100 * s))} %" for k, s in mm["top"][:2]))
        rows.append(f"| {LABEL.get(r['design'], r['design'])} | {r['notes'].split(': ')[-1]} | {', '.join(f'{x:.1f}' for x in f)} | "
                    f"{'; '.join(tops)} |")
    rows += ["", "Step rates of the NEMA 34 (one 32T revolution per motor revolution in all three designs, 200 full steps per revolution):", "",
             "| chain speed (mm/s) | full-step rate (Hz) | electrical frequency (Hz) | 32T tooth mesh (Hz) |", "|---|---|---|---|"]
    for v in v_list:
        fs = LD.full_step_hz(v)
        rows.append(f"| {v:.0f} | {fs:.1f} | {fs / 4:.1f} | {fs * 32 / 200:.1f} |")
    rows += ["", "Chain speeds (mm/s) at which each excitation lands on a mode under 120 Hz (v3/v4 run up to 100 mm/s, the paternoster "
             "up to 130). A mode is only excited near these speeds, and microstepping weakens the full-step excitation a lot:", "",
             "| design | joint | mode (Hz) | full-step rate at | electrical frequency at | 32T tooth mesh at |", "|---|---|---|---|---|---|"]
    rev = LD.SPROCKET_CIRC_MM
    for r in recs:
        vmax = LD.V_MAX_MM_S if r["design"] == "paternoster" else 100.0
        for f in r.get("freqs_Hz", []):
            if f > 120:
                break
            vs = [f / n * rev for n in (LD.FULL_STEPS_PER_REV, LD.FULL_STEPS_PER_REV / 4, 32)]
            cell = [f"**{v:.0f}**" if v <= vmax else f"{v:.0f}" for v in vs]
            rows.append(f"| {LABEL.get(r['design'], r['design'])} | {r['notes'].split(': ')[-1]} | {f:.1f} | {cell[0]} | {cell[1]} | {cell[2]} |")
    rows += ["", "Bold: inside the design's speed range."]
    return rows


def tipping() -> list[str]:
    """A push F at the top rail tips the frame about the feet's line when F h > W a (a: COM to that line, horizontally)."""
    rows = ["| design | mass on the feet (kg) | push height (mm) | push sideways (y) to tip (N) | push along x to tip (N) |",
            "|---|---|---|---|---|"]
    for f in sorted((OUT / "frame").glob("*_mass.json")):
        r = json.loads(f.read_text())
        feet = np.array(r["feet_xy"])
        com = np.array(r["com_mm"])
        W = r["mass_kg"] * LD.G_MS2
        top = r["top_rail_z"]
        ay = min(abs(com[1] - feet[:, 1].min()), abs(feet[:, 1].max() - com[1]))
        ax = min(abs(com[0] - feet[:, 0].min()), abs(feet[:, 0].max() - com[0]))
        rows.append(f"| {LABEL.get(r['design'], r['design'])} | {r['mass_kg']:.1f} (COM {com[0]:.0f}, {com[1]:.0f}, {com[2]:.0f}) | {top:.0f} | "
                    f"{W * ay / top:.0f} | {W * ax / top:.0f} |")
    return rows


def motor_bolts() -> list[str]:
    """The NEMA 34's four M5 x 25 18-8 screws (through 5.5 mm slots in the back plate, nylon locknuts): do they slip in a jam?
    The drive chain pulls the motor along its slots (they are vertical: the motor slides 4 mm to tension the drive chain)."""
    rows = ["| case | drive chain pull (N) | weight (N) | net along the slots (N) | torque shear per screw (N) | friction capacity, 4 screws (N) | safety factor against slip |",
            "|---|---|---|---|---|---|---|"]
    W = LD.M_NEMA34 * LD.G_MS2
    r_bolt = 69.58 / math.sqrt(2)
    Fp = 2000.0                                   # N per screw: 3 N*m on an 18-8 M5 (T = K F d, K 0.3 for stainless)
    mu = 0.15                                     # aluminium plate / steel flange, dry
    cap = 4 * mu * Fp
    for name, tq in (("running", LD.V2_DRIVE_NM), ("jam", LD.NEMA34_HOLD_NM)):
        Fc = tq * 1000.0 / LD.V2_R15_MM + 10.0
        net = Fc - W
        sh = tq * 1000.0 / (4 * r_bolt)
        need = abs(net) + 4 * sh * 0.5            # the torque's shear adds about half its sum where it lines up with the pull
        rows.append(f"| {name} ({tq} N*m) | {Fc:.0f} | {W:.0f} | {net:.0f} up | {sh:.0f} | {cap:.0f} | {cap / need:.1f} |")
    return rows


def main():
    L = ["# FEA summary (generated by report.py from out/*/*.json)", ""]
    v = json.loads((OUT / "verify.json").read_text()) if (OUT / "verify.json").exists() else None
    if v:
        c = v["cantilever"][-1]
        L += ["## Checks against hand solutions (verify.py)", "",
              "| check | CalculiX | hand | difference |", "|---|---|---|---|",
              f"| cantilever tip deflection, 20 mm bar, h {c['h']} mm | {c['tip_mm']:.5f} mm | {c['exact_mm']:.5f} mm (Timoshenko) | {c['err_pct']:+.2f} % |",
              f"| bending stress at mid-span | {c['sx_mid_MPa']:.2f} MPa | {c['sx_exact_MPa']:.2f} MPa | {100 * (c['sx_mid_MPa'] / c['sx_exact_MPa'] - 1):+.1f} % |",
              f"| first bending mode | {v['cantilever_modes']['fem_Hz'][0]:.1f} Hz | {v['cantilever_modes']['euler_bernoulli_Hz'][0]:.1f} Hz (Euler-Bernoulli) | "
              f"{100 * (v['cantilever_modes']['fem_Hz'][0] / v['cantilever_modes']['euler_bernoulli_Hz'][0] - 1):+.1f} % |",
              f"| 1/4 in plate strip, 1 vs 3 elements through it | {v['plate_strip'][0]['tip_mm']:.4f} mm | {v['plate_strip'][2]['tip_mm']:.4f} mm | "
              f"{100 * (v['plate_strip'][0]['tip_mm'] / v['plate_strip'][2]['tip_mm'] - 1):+.1f} % |",
              f"| Euler buckling, 6 mm rod | {v['buckling']['fem_N'][0]:.1f} N | {v['buckling']['euler_N']:.1f} N | "
              f"{100 * (v['buckling']['fem_N'][0] / v['buckling']['euler_N'] - 1):+.2f} % |",
              f"| 2020 section (webbed) second moment | {v['extrusion_2020']['Ixx_mm4']:.0f} mm^4 | 7200 mm^4 (catalogue) | "
              f"{100 * (v['extrusion_2020']['Ixx_mm4'] / 7200 - 1):+.1f} % |", ""]
    for module, title in (("frame", "Frames and the motor on the wall"), ("shafts", "Shafts and idler axles"),
                          ("carriage", "Carriages, hinges, latches, side tabs"), ("station", "Station")):
        recs = [r for r in load(module) if r.get("load_case") != "modes"]
        if not recs:
            continue
        L += [f"## {title}", ""] + static_rows(recs) + [""]
        if module == "frame":
            L += ["### Natural frequencies", ""] + frame_modes() + ["", "### Tipping", ""] + tipping() + [""]
            L += ["### The motor's screws (v3, v4: four M5 x 25 18-8 through slots, 3 N*m, friction 0.15)", ""] + motor_bolts() + [""]
        if module == "shafts":
            L += ["### Shafts: beam theory and fatigue (keyway through Kf)", "",
                  "| design | case | shaft | M max (N*m) | at x (mm) | bending, nominal (MPa) | torsion (MPa) | von Mises hand (MPa) | von Mises FEA (MPa) | Goodman n |",
                  "|---|---|---|---|---|---|---|---|---|---|"]
            for r in recs:
                if "beam" not in r:
                    continue
                b, fa = r["beam"], r["fatigue"]
                vm_h = math.hypot(b["sigma_nominal_MPa"], math.sqrt(3) * r["torsion_nominal_MPa"])
                L.append(f"| {LABEL.get(r['design'], r['design'])} | {r['load_case']} | {r['part']} | {b['M_max_Nmm'] / 1000:.2f} | {b['at_x']} | "
                         f"{b['sigma_nominal_MPa']:.1f} | {r['torsion_nominal_MPa']:.1f} | {vm_h:.1f} | {r['parts'][0]['vm_excl_MPa']:.1f} | {fa['n_goodman']} |")
            L.append("")
    (OUT / "SUMMARY.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
