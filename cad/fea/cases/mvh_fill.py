"""Fill MATERIALS-VIBRATION-HEAT.md's tables from the cases' JSON (run after thermal.py, vibration.py, materials_study.py).

    python cases/mvh_fill.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from cases import common  # noqa: E402

OUT = common.OUT
DOC = OUT.parent / "MATERIALS-VIBRATION-HEAT.md"
NAMES = {"chain-carousel-v3_pads": "v3", "chain-carousel-v4_pads": "v4", "chain-carousel-v4_motorpost2": "v4 + two motor posts",
         "paternoster_pads": "paternoster"}


def j(p):
    f = OUT / p
    return json.loads(f.read_text()) if f.exists() else None


def joints_table() -> tuple:
    jj = j("vibration/joints.json")
    if not jj:
        return "(vibration/joints.json not run)", "?", "?"
    rows = ["| frame | joint | sideways load at the worst speed | friction holds | safety factor | slips at a ripple of |",
            "|---|---|---|---|---|---|"]
    slip, plate = [], []
    for r in jj["joints"]:
        nm = NAMES.get(r["design"], r["design"])
        if "dynamic_N" in r:
            short = "motor's 4 M5s (3 N*m)" if r["joint"].startswith("NEMA") else "side plate's M5 T-nut screws (2.5 N*m)"
            rows.append(f"| {nm} | {short} | {r['dynamic_N']:.1f} N at {r['at_mm_s']:.0f} mm/s | {r['friction_cap_N']} N | {r['sf']:.0f} | "
                        f"{r['slips_at_ripple_Nm']:.1f} N*m |")
            if r["joint"].startswith("side"):
                slip.append(r["slips_at_ripple_Nm"])
        else:
            plate.append(r["dynamic_MPa"])
    txt = "\n".join(("   " + x) if i else x for i, x in enumerate(rows))
    by = {r["design"]: r["slips_at_ripple_Nm"] for r in jj["joints"] if r["joint"].startswith("side")}
    sl = ", ".join(f"{v:.1f} N*m in {NAMES.get(k, k)}" for k, v in sorted(by.items(), key=lambda kv: kv[1]))
    return txt, sl, f"{max(plate):.1f}" if plate else "?"


def vib_detail() -> str:
    L = ["| frame | resonance | chain speed | motor's encoder end moves | top rail moves | peak plate stress | worst side-plate screw, sideways |",
         "|---|---|---|---|---|---|---|"]
    rip = 0.4
    for c, nm in NAMES.items():
        r = j(f"vibration/{c}_frf.json")
        if not r:
            continue
        import numpy as np
        f = np.array(r["f_Hz"])
        for p in r["resonances"]:
            k = int(np.argmin(np.abs(f - p["f_Hz"])))
            enc = r["per_Nm"].get("enc", {}).get("u_um", [0] * len(f))[k] * rip
            top = r["per_Nm"].get("top_rail", {}).get("u_um", [0] * len(f))[k] * rip
            L.append(f"| {nm} | {p['f_Hz']:.1f} Hz | {p['speed_mm_s']:.0f} mm/s | {enc:.0f} µm | {top:.0f} µm | {p['plate_vm_per_Nm'] * rip:.1f} MPa | "
                     f"{p.get('pad_transverse_per_Nm_N', 0) * rip:.0f} N |")
    L.append("")
    L.append("Amplitudes at a 0.4 N*m ripple and 2 % damping; at 1 % damping the resonant peaks double. Each frame's whole sweep "
             "(5-140 Hz) is in `out/vibration/<frame>_frf.json` and the plot below.")
    return "\n".join(L)


def panels() -> str:
    out = []
    for des in ("chain-carousel-v3", "chain-carousel-v4"):
        p = j(f"vibration/panels_{des}.json")
        if not p:
            continue
        fs = [v["freqs_Hz"][0] for v in p.values() if "freqs_Hz" in v]
        if fs:
            out.append(f"{des.replace('chain-carousel-', '')}'s panels' first modes are {min(fs):.0f}-{max(fs):.0f} Hz")
    if not out:
        return "(panel modes not run)."
    lo = min(min(v["freqs_Hz"][0] for v in j(f"vibration/panels_{d}.json").values() if "freqs_Hz" in v)
             for d in ("chain-carousel-v3", "chain-carousel-v4") if j(f"vibration/panels_{d}.json"))
    return ("(" + "; ".join(out) + ", and each has more modes up to 75 Hz). The full-step rate reaches the lowest at "
            f"{lo * 304.8 / 200:.0f} mm/s and crosses more of them all the way to 100 mm/s, so some panel will buzz at most speeds.")


def thermal_table() -> str:
    L = ["| design | NEMA 34 current | loss | motor case | back plate, hottest | printed parts on it | enclosure air |", "|---|---|---|---|---|---|---|"]
    for des in ("chain-carousel-v3", "chain-carousel-v4", "paternoster"):
        for frac in (100, 70, 50, 25):
            r = j(f"thermal/{des}_motor_{frac}.json")
            if not r:
                continue
            pp = r["printed_parts_on_back_plate_max_C"]
            ppt = f"{min(pp.values()):.0f}-{max(pp.values()):.0f} °C" if pp else "-"
            air = f"{r['T_enclosure_air']:.1f} °C" if r["T_enclosure_air"] is not None else "room (22 °C)"
            plate = f"{r['plate_max']:.0f} °C" + (f" (motor plate and standoffs {r['standoffs_max']:.0f} °C)" if r.get("standoffs_max") else "")
            L.append(f"| {des.replace('chain-carousel-', '')} | {r['current_A']:.1f} A | {r['P_motor_W']:.0f} W | {r['motor_case_max']:.0f} °C | "
                     f"{plate} | {ppt} | {air} |")
    for tag, lab in (("chain-carousel-v3_motor_50_black", "v3, black back plate"), ("chain-carousel-v4_motor_100_black", "v4, black back plate"),
                     ("chain-carousel-v4_motor_100_steel", "v4, steel back plate")):
        r = j(f"thermal/{tag}.json")
        if r:
            pp = r["printed_parts_on_back_plate_max_C"]
            L.append(f"| {lab} | {r['current_A']:.1f} A | {r['P_motor_W']:.0f} W | {r['motor_case_max']:.0f} °C | {r['plate_max']:.0f} °C | "
                     f"{min(pp.values()):.0f}-{max(pp.values()):.0f} °C | {r['T_enclosure_air']:.1f} °C |")
    L.append("")
    L.append("The station's electronics carriage (v3), in still air:")
    L.append("")
    L.append("| case | NEMA 11 | electromagnet | PETG next to the NEMA 11 | PETG next to the electromagnet | electromagnet's pull |")
    L.append("|---|---|---|---|---|---|")
    for f in sorted((OUT / "thermal").glob("ec_*.json")):
        r = json.loads(f.read_text())
        if "history" in r:
            continue
        nt = r["petg_next_to"]
        em = f"{r['electromagnet_max']:.0f} °C ({r['P_electromagnet_W']:.2f} W)" if r.get("electromagnet_max") else "off"
        L.append(f"| {r['design']}, air {r['T_air']:.1f} °C | {r['nema11_max']:.0f} °C ({r['P_nema11_W']:.2f} W) | {em} | {nt.get('NEMA 11', '-')} °C | "
                 f"{nt.get('electromagnet', '-')}{' °C' if 'electromagnet' in nt else ''} | "
                 f"{str(round(100 * r['electromagnet_pull_frac'])) + ' % of cold' if r.get('electromagnet_pull_frac') else '-'} |")
    return "\n".join(L)


def warmup() -> str:
    out = []
    for frac in (100, 50):
        r = j(f"thermal/chain-carousel-v3_warmup_{frac}.json")
        if r and r.get("t_63pct_min"):
            out.append(f"at {frac} % current the motor gets 63 % of the way to its steady temperature in {r['t_63pct_min']:.0f} min and "
                       f"95 % in {r['t_95pct_min']:.0f} min" if r.get("t_95pct_min") else
                       f"at {frac} % current the motor gets 63 % of the way in {r['t_63pct_min']:.0f} min")
    if not out:
        return ""
    return ("**Warm-up** (v3, transient, from cold, with the enclosure air held at its steady value): " + "; ".join(out) +
            ". The enclosure's air follows on a similar time scale, so allow about an hour after power-up before taring the "
            "balance for a precise run.\n\n![v3 warm-up](out/thermal/chain-carousel-v3_warmup_100.png)")


def steel_thermal() -> str:
    a, s = j("thermal/chain-carousel-v4_motor_100.json"), j("thermal/chain-carousel-v4_motor_100_steel.json")
    if not (a and s):
        return "at full current the steel plate's run was not finished."
    return (f"at full current the motor runs at {s['motor_case_max']:.0f} °C on steel against {a['motor_case_max']:.0f} °C on 6061, and the "
            f"plate's hottest point is {s['plate_max']:.0f} °C against {a['plate_max']:.0f} °C.")


def materials_table() -> str:
    t = (OUT / "materials" / "SUMMARY.md").read_text() if (OUT / "materials" / "SUMMARY.md").exists() else ""
    i = t.find("## Printed parts")
    k = t.find("## Candidates")
    body = t[i:k].replace("## ", "### ") if i >= 0 else ""
    return body + "\nThe candidates (HDT, cost, moisture, notes) and v4's steel back plate: [out/materials/SUMMARY.md](out/materials/SUMMARY.md)."


def main():
    s = DOC.read_text()
    jt, slip, plate = joints_table()
    rep = {"VIBRATION_JOINTS_TABLE": jt, "VIB_SLIP_MIN": slip, "VIB_PLATE_MAX": plate, "PANEL_SENTENCE": panels(),
           "STEEL_THERMAL": steel_thermal(), "THERMAL_TABLE": thermal_table(), "WARMUP_SENTENCE": warmup(),
           "VIBRATION_DETAIL": vib_detail(), "MATERIALS_TABLE": materials_table()}
    for k, v in rep.items():
        s = s.replace(k, v)
    DOC.write_text(s)
    left = [k for k in rep if k in s]
    print("filled;", "left:", left)


if __name__ == "__main__":
    main()
