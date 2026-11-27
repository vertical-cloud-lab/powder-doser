"""Tables for sim/README.md from out/*.json (run12.py's results): python summarize12.py > out/summary.md"""
from __future__ import annotations

import collections
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent / "out"


def load(name):
    p = OUT / f"{name}.json"
    return json.loads(p.read_text())["runs"] if p.exists() else []


def entry_tables():
    E = load("entry")
    print("#### Entry: one index into the station, then the seek (12 arrival phases per row; the pinion free during the index)\n")
    print("| Design | Clevis roll stiffness (N·m/rad) | Tolerance stack (mm) | Meshed on arrival | On the tips, cleared by the seek | ... by the second try | Left on the tips | Jammed | Peak chain force (N) | Centre distance after (mm) |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    order = ["v12", "4 N spring", "pivot 10 mm nearer the gear", "leading arm", "one seat"]
    for lab in order:
        g0 = [r for r in E if r.get("label") == lab]
        for kr in sorted({r["k_roll"] for r in g0}):
            for e in sorted({r["a_err"] for r in g0 if r["k_roll"] == kr}):
                g = [r for r in g0 if r["k_roll"] == kr and r["a_err"] == e]
                c = collections.Counter(r["outcome"] for r in g)
                n = len(g)
                left = sum(v for k, v in c.items() if k.startswith("stub left"))
                print(f"| {lab} | {kr:g} | {e:+.2f} | {c['meshed']}/{n} | {c['stub, cleared by the seek']}/{n} | {c['stub, cleared by the second try']}/{n} | "
                      f"{left}/{n} | **{c['jam']}/{n}** | {max(r['chain_force_max_N'] for r in g):.1f} | "
                      f"{min(r['cd_end'] for r in g):.2f}-{max(r['cd_end'] for r in g):.2f} |")
    print()
    tot = collections.Counter()
    for r in E:
        tot[(r["label"], r["outcome"])] += 1
    for lab in order:
        g = [r for r in E if r.get("label") == lab]
        if not g:
            continue
        c = collections.Counter(r["outcome"] for r in g)
        hall_final = sum(1 for r in g if r["hall"][-1] == (not (r["cds"][-1] < 34.7)))
        print(f"- **{lab}**: {len(g)} indexes, {c['meshed']} meshed on arrival, {c['stub, cleared by the seek']} cleared by the first seek, "
              f"{c['stub, cleared by the second try']} by the second try, {sum(v for k, v in c.items() if k.startswith('stub left'))} left on the tips, "
              f"**{c['jam']} jammed**; the switch's reading after the seek right in {hall_final}/{len(g)}.")
    print()


def robust_table():
    R = load("entry_robust")
    if not R:
        return
    print("#### Entry: what the outcome depends on (v12 as drawn, nominal tolerances, 12 arrival phases each)\n")
    print("| Change | Meshed | On the tips, cleared by the seek | ... by the second try | Left | Jammed | Peak chain force (N) |")
    print("|---|---|---|---|---|---|---|")
    for lab in dict.fromkeys(r["label"] for r in R):
        g = [r for r in R if r["label"] == lab]
        c = collections.Counter(r["outcome"] for r in g)
        n = len(g)
        print(f"| {lab} | {c['meshed']}/{n} | {c['stub, cleared by the seek']}/{n} | {c['stub, cleared by the second try']}/{n} | "
              f"{sum(v for k, v in c.items() if k.startswith('stub left'))}/{n} | **{c['jam']}/{n}** | {max(r['chain_force_max_N'] for r in g):.1f} |")
    print()


def exit_table():
    X = load("exit")
    if not X:
        return
    print("#### Exit: the next index pulls the gear out\n")
    print("| Pinion | Tolerance stack (mm) | Clevis (N·m/rad) | Peak chain force (N) | Peak tooth force (N) | Chain lag (mm) |")
    print("|---|---|---|---|---|---|")
    for r in X:
        print(f"| {r['mode']} | {r['a_err']:+.2f} | {r['k_roll']:g} | {r['chain_force_max_N']:.1f} | {r['tooth_force_max_N']:.1f} | {r['chain_lag_max_mm']:.3f} |")
    print()


def _cfg_name(c):
    if not c:
        return "v12 as drawn"
    parts = []
    for k, v in c.items():
        parts.append({"cradle": "v11 as drawn (rigid)" if v is False else "", "a_err": f"tolerance {v:+g} mm", "k_roll": f"clevis {v:g} N·m/rad",
                      "f_spring": f"{v:g} N spring", "piv_dz": f"pivot {v:g} mm nearer the gear", "piv_dy": "leading pivot" if v > 0 else "",
                      "seats": f"{v} seat"}.get(k, f"{k} {v}"))
    return ", ".join(p for p in parts if p)


def cycle_tables():
    C = load("cycle")
    if not C:
        return
    print("#### Station cycle: tilt to 30 deg, dose 1 s (30 rpm, 20 mN m with a slug per turn, 4 N solenoid taps every 0.25 s), on to 90 deg, dose, back down, one reverse turn at rest\n")
    print("| Case | Phase | Tilt reached (deg) | Centre distance (mm) | P16 force (N) | T on the lips (N) | Teeth, 10 ms avg max (N) | EC roll (deg) | Seats at the end (N) |")
    print("|---|---|---|---|---|---|---|---|---|")
    for r in C:
        if r["stall_at"] is not None:
            continue
        nm = _cfg_name(r["cfg"])
        for ph, v in r["phases"].items():
            print(f"| {nm} | {ph} | {v['tilt_end']} | {v['cd_mm'][0]:.2f}-{v['cd_mm'][1]:.2f} | {v['p16_N'][0]:.0f} to {v['p16_N'][1]:.0f} | "
                  f"{v['t_contact_N'][1]:.0f} | {v['tooth_N_10ms_max']:.0f} | {v['ec_roll_deg'][0]:+.2f} to {v['ec_roll_deg'][1]:+.2f} | {v['seat_N_end']:.1f} |")
        print(f"| {nm} | tooth jumps over the cycle | {r['tooth_jumps']} | | | | | | |")
    print()
    print("#### Stall ramps: the auger's load rises until something gives (30 rpm, 450 mA)\n")
    print("| Case | Tilt (deg) | What gives | At (N·m at the auger) | Centre distance then (mm) |")
    print("|---|---|---|---|---|")
    for r in sorted([r for r in C if r["stall_at"] is not None], key=lambda r: (_cfg_name(r["cfg"]), r["stall_at"])):
        st = r["steps"][0].get("stall") or {}
        print(f"| {_cfg_name(r['cfg'])} | {r['stall_at']:g} | {st.get('mode')} | {st.get('load_Nm')} | {st.get('cd_mm')} |")
    print()


if __name__ == "__main__":
    entry_tables()
    robust_table()
    exit_table()
    cycle_tables()
