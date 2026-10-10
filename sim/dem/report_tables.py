"""Print the markdown result tables used in README.md from results/metrics.jsonl."""

from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

RIG = {
    "rig_t27p5_r60": ("27.5°, 60 rpm", "CAD exit (core tip in the hole)", "105 ± 11 (PR #166 centre point, n = 8)"),
    "rig_t22p5_r90": ("22.5°, 90 rpm", "CAD exit (core tip in the hole)", "106–110 (battery D, two days)"),
    "rig_t00_r60": ("0°, 60 rpm", "CAD exit (core tip in the hole)", "≈28 (battery C: 36 ± 7.5 at 30 rpm, n = 12, scaled by rpm^-0.35)"),
    "rig_t45_r60": ("45°, 60 rpm", "CAD exit (core tip in the hole)", "≈195 (battery C: 248 ± 30 at 30 rpm, n = 12, scaled by rpm^-0.35)"),
    "rig_t27p5_r60_seed2": ("27.5°, 60 rpm", "CAD exit, repeat with a different random packing", "105 ± 11"),
    "rig_t27p5_r60_d035": ("27.5°, 60 rpm", "CAD exit, finer salt (d50 0.35 instead of 0.425 mm)", "105 ± 11"),
    "rig_t27p5_r60_tip0p5": ("27.5°, 60 rpm", "core tip cut 0.5 mm short", "105 ± 11"),
    "rig_t27p5_r60_tip1p0": ("27.5°, 60 rpm", "core tip cut 1.0 mm short", "105 ± 11"),
    "rig_t27p5_r60_tip2": ("27.5°, 60 rpm", "core tip cut 2 mm short", "105 ± 11"),
}
MICRO = [
    ("micro_open", "baseline: open 4 mm core, 1.2 mm flight, 5 mm pitch, 2.5 mm exit, 27° funnel"),
    ("micro_shaft", "solid 4 mm shaft (closed core)"),
    ("micro_rig", "rig-style: solid core, tip in the exit, 0.5 mm flight"),
    ("micro_exit18", "1.8 mm exit"),
    ("micro_pitch3", "3 mm pitch"),
    ("micro_2start", "2-start flight (same 5 mm pitch, lead 10 mm)"),
    ("micro_shaft_pitch3", "solid shaft + 3 mm pitch"),
    ("micro_cone45", "short funnel, 45° half-angle (steep dam at 15° tilt)"),
    ("micro_cone17", "long funnel, 17° half-angle (almost no dam)"),
    ("micro_tilt0", "baseline at 0° tilt"),
    ("micro_hifric", "baseline, high friction (μ 0.7 / 0.6, μr 0.5)"),
    ("micro_cohesive", "solid shaft, cohesive grains (SJKR 20 kJ/m³)"),
    ("micro_best", "combined: solid shaft + 2-start + short 45° funnel"),
    ("micro_rig_d030", "rig-style tip in the exit, finer salt (d 0.30 mm)"),
]


def fmt(x, nd=1):
    return "–" if x is None else f"{x:.{nd}f}"


def main(path=os.path.join(HERE, "results", "metrics.jsonl")):
    rows = {r["case"]: r for r in map(json.loads, open(path))}
    print("| case | tilt, rpm | exit | twin mg/rev (after first ¼ rev) | twin mg/rev (whole run) | rig mg/rev | afterflow (mg) | revs simulated |")
    print("|---|---|---|---|---|---|---|---|")
    for k, (op, exit_, rig) in RIG.items():
        r = rows.get(k)
        if not r:
            continue
        se = r.get("mg_per_rev_se")
        meta = json.load(open(os.path.join(os.path.dirname(os.path.abspath(path)), "cases", k, "case.json")))
        rev_done = min((r["sim_time_s"] - meta["settle_s"]) / meta["period_s"], meta["cfg"]["revs"])
        print(f"| `{k}` | {op} | {exit_} | **{r['mg_per_rev']:.0f}**" + (f" ± {se:.0f}" if se else "") +
              f" | {r.get('mg_per_rev_full', float('nan')):.0f} | {rig} | {fmt(r.get('afterflow_mg'), 0)} | {rev_done:.2f} |")
    print()
    print("| micro-auger variant (15°, 55 rpm, salt d 0.45 mm) | mg/rev | 5° nudge mg (CV) | 15° nudge mg (CV) | empty 5° nudges | afterflow 0.5 s (mg) | funnel inventory (mg) |")
    print("|---|---|---|---|---|---|---|")
    for k, lab in MICRO:
        r = rows.get(k)
        if not r or not r.get("complete"):
            continue
        w5, w15 = r["windows"].get("5", {}), r["windows"].get("15", {})
        se = r.get("mg_per_rev_se")
        print(f"| {lab} | {r['mg_per_rev']:.1f}" + (f" ± {se:.1f}" if se else "") +
              f" | {fmt(w5.get('mean_mg'), 2)} ({fmt(w5.get('cv'), 2)}) | {fmt(w15.get('mean_mg'), 2)} ({fmt(w15.get('cv'), 2)})"
              f" | {100 * w5.get('p_empty', 0):.0f} % | {fmt(r.get('afterflow_mg'), 1)} | {fmt(r.get('funnel_holdup_mg'), 0)} |")


if __name__ == "__main__":
    main(*sys.argv[1:])
