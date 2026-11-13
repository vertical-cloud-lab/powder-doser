"""Material selection: each part's material against its governing FEA case, the temperature it runs at (thermal.py),
and what else a material has to survive here: creep, moisture, static next to powders and a 0.1 mg balance, cleaning,
cost and printing.

    python cases/materials_study.py          # the v4 steel back plate's modes, then out/materials/SUMMARY.md

In a linear model of one material with loads (not displacements) applied, the stress field doesn't depend on the
modulus (and barely on Poisson's ratio). So the FEA's stresses hold for any candidate: its safety factor scales with
its strength and its deflections with 1 / E. Where one part's stiffness against another's decides the answer (v4's
back plate under the 5.6 kg motor), the FEA is rerun with the other material.

Printed-material data: PETG HF from Bambu's TDS (materials.py); heat deflection temperatures (0.45 MPa) from Bambu's
filament comparison table; PAHT-CF's strengths as quoted from Bambu's TDS V3.0 by a third-party review (check the
current TDS before relying on them). The others' across-layer strengths are not in hand here, so the table gives the
across-layer strength each critical part needs for a safety factor of 2 instead.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import fem  # noqa: E402
import materials as MAT  # noqa: E402
from cases import common  # noqa: E402

MODULE = "materials"
OUT = common.OUT

# printed candidates. S_z: tensile strength across the layers (MPa); E: X-Y modulus; hdt: 0.45 MPa (C)
PRINTED = {
    "PETG HF": dict(E=1810, S_xy=34, S_z=23, hdt=69, cost=20, water="low", note="the baseline; tough, cheap, easy"),
    "PLA": dict(hdt=57, cost=20, water="low", note="creeps at 40 C and brittle: not for this rig"),
    "ABS": dict(hdt=87, cost=22, water="low", note="warps on a large flat part like the 351 mm carriage"),
    "ASA": dict(hdt=100, cost=28, water="low", note="ABS's heat resistance, warps less; UV-stable"),
    "PC": dict(hdt=117, cost=35, water="moderate", note="tough and hot; stress-crazes with IPA or acetone under load"),
    "PAHT-CF": dict(S_xy=92, S_z=47, hdt=194, cost=80, water="high: dry it before printing; about 1/3 stiffer dry than wet",
                    note="far less creep; needs a hardened nozzle (the H2D has one); conductive fibres, but not ESD-rated"),
    "PET-CF": dict(hdt=205, cost=75, water="low", note="the stiff, hot, dimensionally stable option; brittle in impact"),
    "ESD PETG (carbon-loaded)": dict(hdt=69, cost=45, water="low",
                                     note="10^6-10^9 ohm/sq: lets charge drain from parts that touch powder"),
}

# the governing printed-part cases (peak MPa from the FEA, short-term unless 'sustained'), and where each part sits
CASES = [
    ("v4 carriage, latch bridged: 40 N auger pull", "carriage/v4_pull.json", "carriage", "air"),
    ("v3 carriage: 40 N auger pull", "carriage/v3_pull.json", "carriage", "air"),
    ("v4 guide cradle: P16 retract stall", "station/cradle_v4_retract_stall.json", "cradle", "air"),
    ("v3 guide cradle: P16 retract stall", "station/cradle_v3_retract_stall.json", "cradle", "air"),
    ("v4 electronics carriage: P16 stall", "station/ec_v4_stall_t0.json", "EC", "ec"),
    ("v3 electronics carriage: P16 stall", "station/ec_v3_stall_t0.json", "EC", "ec"),
    ("v3 carriage: P16 stall at the station", "carriage/v3_station_p16.json", "carriage", "air"),
    ("v4 side tab foot: 25 N (1 mm off its sharp corner)", "carriage/v4_side_tab.json", None, "back"),
    ("v3 side tab lip: 25 N (1 mm off its sharp corner)", "carriage/v3_side_tab.json", None, "back"),
    ("hold-down: half a P16 stall", "station/hold_down_p16_stall.json", None, "back"),
]
SUSTAINED = [
    ("v3 carriage, vertical runs, creep", 3.04, "air"),
    ("tensioner block, bearing bolts slipped", 3.1, "tensioner"),
    ("A-1 screw head on its printed seat (snug)", 18.0, "air"),
    ("A-1 screw head with a DIN 433 washer", 15.0, "air"),
    ("paternoster gondola, hanging", 0.49, "room"),
]
CREEP_RT = 8.0                       # PETG, 1000 h at room temperature (materials.py)


def peak(path: str, part: str | None) -> float:
    j = json.loads((OUT / path).read_text())
    k1 = "von Mises 1 mm off the sharp root corner (MPa)"     # the side tabs: their corner itself is singular
    if k1 in j.get("key_disp", {}):
        return j["key_disp"][k1]
    rows = j["parts"]
    if part:
        rows = [r for r in rows if r["part"] == part] or rows
    return max(r["vm_excl_MPa"] for r in rows)


def temps() -> dict:
    """Temperatures each group of printed parts runs at, from the thermal cases (v3 at 50 % and 100 % current)."""
    t = {}
    for frac in (50, 100):
        f = OUT / "thermal" / f"chain-carousel-v3_motor_{frac}.json"
        if not f.exists():
            continue
        r = json.loads(f.read_text())
        pp = r["printed_parts_on_back_plate_max_C"]
        t[frac] = dict(air=r["T_enclosure_air"], back=max(pp.values()), room=r["T_room"],
                       tensioner=max(v for k, v in pp.items() if k.startswith("Tensioner")))
    for tag, key in (("ec_v3_n11_em", "ec_room"),):
        f = OUT / "thermal" / f"{tag}.json"
        if f.exists():
            r = json.loads(f.read_text())
            for k in t:
                t[k]["ec"] = round(r["petg_max"] - r["T_air"] + t[k]["air"], 1)
    return t


def creep_allowable(T: float, hdt: float = 69.0) -> float:
    """PETG's 1000 h allowable, derated linearly from 8 MPa at 23 C to nothing at its HDT: a rule of thumb, not data."""
    return max(0.0, CREEP_RT * (hdt - T) / (hdt - 23.0))


def steel_back_plate_modes(design: str = "chain-carousel-v4", n: int = 8) -> dict:
    """v4's frame with its back side plate in 1/4 in steel instead of 6061: does it lift the 50.6 Hz motor mode?"""
    from cases import frame as FR
    MAT.add(MAT.Material("STEEL_PLATE", 205000.0, 0.29, 7.87e-9, 250.0, "A36 / 1018 steel plate"))
    D, m, pads = FR.frame_mesh(design, "pads", 12.0)
    d = fem.Deck(m, materials={"side_plate_back": "STEEL_PLATE"})
    FR.feet_fix(d, D)
    d.frequency(n)
    res = d.solve(f"materials/{design}_steel_back_modes")
    base = json.loads((OUT / "frame" / f"{design}_pads_modes.json").read_text())["freqs_Hz"]
    pl = m.nodes_of("side_plate_back")
    vol = m.volumes()[m.part == m.names.index("side_plate_back")].sum()
    out = dict(module=MODULE, case=f"{design}_steel_back_modes", freqs_Hz=[round(f, 2) for f in res.freqs], aluminium_Hz=base[:n],
               plate_mass_kg=dict(steel=round(vol * 7.87e-6, 2), aluminium=round(vol * 2.70e-6, 2)),
               full_step_reaches_mode4_at_mm_s=round(res.freqs[3] * 304.8 / 200, 0) if len(res.freqs) > 3 else None)
    d_out = OUT / MODULE
    d_out.mkdir(parents=True, exist_ok=True)
    try:
        fem.render(res, d_out / f"{design}_steel_back_mode4.png", field="u", mode=3,
                   title=f"{design}, back plate in steel: mode 4, {res.freqs[3]:.1f} Hz", view=(1.2, -1.0, 0.6))
        out["png"] = f"out/{MODULE}/{design}_steel_back_mode4.png"
    except Exception as e:                                # noqa: BLE001
        out["png_error"] = str(e)[:200]
    (d_out / f"{out['case']}.json").write_text(json.dumps(out, indent=1))
    print(out, flush=True)
    return out


def summary() -> str:
    T = temps()
    L = ["# Material selection (generated by cases/materials_study.py)", ""]
    L.append("Stresses are the FEA's; for one material under applied loads they don't depend on its modulus, so each "
             "candidate's safety factor is its strength over the same peak. Temperatures are from `out/thermal/` "
             "(v3, the NEMA 34 at 50 % and 100 % of its 6.0 A).")
    L.append("")
    L.append("## Printed parts against their worst short-term load")
    L.append("")
    L.append("| part and case | peak (MPa) | PETG HF safety factor (23 MPa across layers) | PAHT-CF (47 MPa) | across-layer strength for a safety factor of 2 (MPa) |")
    L.append("|---|---|---|---|---|")
    for name, path, part, where in CASES:
        try:
            p = peak(path, part)
        except Exception:                                   # noqa: BLE001
            continue
        L.append(f"| {name} | {p:.1f} | {23.0 / p:.2f} | {47.0 / p:.2f} | {2 * p:.0f} |")
    L.append("")
    L.append("## Sustained loads: creep, and the temperature each part runs at")
    L.append("")
    hdr = "| part | sustained stress (MPa) | where |"
    sep = "|---|---|---|"
    for k in sorted(T):
        hdr += f" at {k} % current: °C, PETG creep allowable (MPa), safety factor |"
        sep += "---|"
    L += [hdr, sep]
    for name, s, where in SUSTAINED:
        row = f"| {name} | {s:.2f} | {where} |"
        for k in sorted(T):
            t = T[k].get(where, T[k]["air"])
            a = creep_allowable(t)
            row += f" {t:.0f}, {a:.1f}, {a / s:.2f} |" if a > 0 else f" {t:.0f}, 0, 0 |"
        L.append(row)
    L.append("")
    L.append("PETG's 8 MPa (1000 h, room temperature) is derated here in proportion to how far the part sits below "
             "PETG HF's 69 °C HDT, falling to zero at it. That is a rule of thumb, not creep data. The practical rule is "
             "to keep a part under sustained load 20 K or more below its HDT: about 49 °C for PETG, 80 °C for ASA, "
             "97 °C for PC and over 150 °C for the CF nylons and PET-CF.")
    L.append("")
    L.append("## Candidates")
    L.append("")
    L.append("| material | HDT 0.45 MPa (°C) | across layers (MPa) | $/kg | moisture | note |")
    L.append("|---|---|---|---|---|---|")
    for k, v in PRINTED.items():
        L.append(f"| {k} | {v['hdt']} | {v.get('S_z', 'see its TDS')} | {v['cost']} | {v['water']} | {v['note']} |")
    f = OUT / MODULE / "chain-carousel-v4_steel_back_modes.json"
    if f.exists():
        r = json.loads(f.read_text())
        L += ["", "## v4's back plate: 6061 or steel", "",
              f"Modes with the back side plate in 1/4 in steel: {', '.join(f'{x:.1f}' for x in r['freqs_Hz'][:6])} Hz "
              f"(6061: {', '.join(f'{x:.1f}' for x in r['aluminium_Hz'][:6])}). The plate weighs {r['plate_mass_kg']['steel']} kg "
              f"instead of {r['plate_mass_kg']['aluminium']} kg."]
    txt = "\n".join(L) + "\n"
    (OUT / MODULE).mkdir(parents=True, exist_ok=True)
    (OUT / MODULE / "SUMMARY.md").write_text(txt)
    return txt


if __name__ == "__main__":
    if "summary" not in sys.argv[1:]:
        steel_back_plate_modes()
    print(summary())
