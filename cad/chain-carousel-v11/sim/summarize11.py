"""Tables for sim/README.md from out/entry.json, out/entry_robust.json, out/exit.json and out/cycle.json (run11.py).

    python summarize11.py > out/summary.md
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

OUT = Path(__file__).resolve().parent / "out"


def pct(n, d):
    return f"{100 * n / d:.0f} %" if d else "-"


def entry_tables():
    E = json.loads((OUT / "entry.json").read_text())["runs"]
    print("### Entry: outcomes by tolerance (12 starting phases each, the pinion free, 5 mN m auger drag)\n")
    rows = defaultdict(list)
    for r in E:
        if r["mode"] != "free" or abs(r["drag_mNm"] - 5.0) > 1e-6:
            continue
        rows[(r["spring"], r["k_roll"], r["a_err"])].append(r)
    print("| Design | Clevis roll stiffness (N·m/rad) | Pinion offset (mm) | Meshed | Stubbed, cleared by the seek | Jammed | Peak tooth force, 2 ms avg (N) | Teeth at rest (N) |")
    print("|---|---|---|---|---|---|---|---|")
    for (sp, kr, e), rs in sorted(rows.items(), key=lambda kv: (kv[0][0], kv[0][1], kv[0][2])):
        n = len(rs)
        m = sum(r["outcome"] == "meshed" for r in rs)
        s = sum(r["outcome"].startswith("stub") for r in rs)
        j = sum(r["jam"] for r in rs)
        ok = [r for r in rs if not r["jam"]]
        fmax = max((r["tooth_force_2ms_max_N"] for r in ok), default=float("nan"))
        rest = sorted(r["end_tooth_force_N"] for r in ok)
        rest_s = f"{rest[len(rest) // 2]:.1f}" if rest else "-"
        print(f"| {'spring-loaded' if sp else 'as drawn'} | {kr:g} | {e:+.2f} | {m}/{n} | {s}/{n} | **{j}/{n}** | {fmax:.0f} | {rest_s} |")
    print()
    print("### Entry: pinion mode and auger drag (as drawn, clevis 10 N·m/rad, nominal)\n")
    print("| Pinion during the index | Auger drag (mN·m) | Meshed | Stubbed | Jammed |")
    print("|---|---|---|---|---|")
    for mode, drag in (("free", 5.0), ("held", 5.0), ("seek", 5.0), ("free", 30.0)):
        rs = [r for r in E if r["mode"] == mode and abs(r["drag_mNm"] - drag) < 1e-6 and not r["spring"] and r["k_roll"] == 10.0 and r["a_err"] == 0.0]
        n = len(rs)
        print(f"| {mode} | {drag:g} | {sum(r['outcome'] == 'meshed' for r in rs)}/{n} | {sum(r['outcome'].startswith('stub') for r in rs)}/{n} | "
              f"**{sum(r['jam'] for r in rs)}/{n}** |")
    print()
    spr = [r for r in E if r["spring"]]
    print(f"Spring-loaded, every run: {len(spr)} runs, {sum(r['jam'] for r in spr)} jams, "
          f"{sum(r['outcome'].startswith('stub') for r in spr)} stubbed, of which {sum(r['outcome'] == 'stub, cleared by the seek' for r in spr)} cleared by the seek.\n")


def robust_table():
    p = OUT / "entry_robust.json"
    if not p.exists():
        return
    E = json.loads(p.read_text())["runs"]
    print("### Entry: what the jams depend on (12 phases each, nominal tolerance)\n")
    print("| Change | Design | Meshed | Stubbed (cleared) | Jammed |")
    print("|---|---|---|---|---|")
    groups = defaultdict(list)
    for r in E:
        c = dict(r["cfg"])
        sp = c.pop("spring", False)
        lab = ", ".join(f"{k} {v:g}" for k, v in c.items()) or "-"
        if r["v"] != 50.0:
            lab = f"index at {r['v']:g} mm/s" + ("" if lab == "-" else ", " + lab)
        groups[(lab, sp)].append(r)
    for (lab, sp), rs in sorted(groups.items()):
        n = len(rs)
        print(f"| {lab} | {'spring-loaded' if sp else 'as drawn'} | {sum(r['outcome'] == 'meshed' for r in rs)}/{n} | "
              f"{sum(r['outcome'].startswith('stub') for r in rs)}/{n} ({sum(r['outcome'] == 'stub, cleared by the seek' for r in rs)}) | **{sum(r['jam'] for r in rs)}/{n}** |")
    print()


def exit_table():
    X = json.loads((OUT / "exit.json").read_text())["runs"]
    print("### Exit: the next index pulls the gear out\n")
    print("| Design | Pinion | Offset (mm) | Clevis (N·m/rad) | Peak chain force (N) | Peak tooth force (N) | Chain lag (mm) |")
    print("|---|---|---|---|---|---|---|")
    for r in X:
        print(f"| {'spring-loaded' if r.get('spring') else 'as drawn'} | {r['mode']} | {r.get('a_err', 0):+.2f} | {r.get('k_roll', 10):g} | "
              f"{r['chain_force_max_N']:.1f} | {r['tooth_force_max_N']:.1f} | {r['chain_lag_max_mm']:.3f} |")
    print()


def cycle_tables():
    C = json.loads((OUT / "cycle.json").read_text())["runs"]
    print("### Station cycle: tilt to 30 deg, dose 1 s (30 rpm, 20 mN m with a slug per turn, 4 N solenoid taps every 0.25 s), on to 90 deg, "
          "dose, back down, one reverse turn at rest\n")
    print("| Case | Phase | Tilt reached (deg) | Centre distance (mm) | P16 force (N) | T on the lips (N) | Teeth, 10 ms avg max (N) | EC roll (deg) | EC sideways (mm) | Seat at the end (N) |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for r in C:
        if r["stall_at"] is not None:
            continue
        c = r["cfg"]
        lab = ("spring-loaded" if c.get("spring") else "as drawn") + "".join(f", {k} {v:g}" for k, v in c.items() if k != "spring")
        for ph, v in r["phases"].items():
            print(f"| {lab} | {ph} | {v['tilt_end']:.1f} | {v['cd_mm'][0]:.2f}-{v['cd_mm'][1]:.2f} | {v['p16_N'][0]:.0f} to {v['p16_N'][1]:.0f} | "
                  f"{v['t_contact_N'][1]:.0f} | {v.get('tooth_N_10ms_max', v['tooth_N_max']):.0f} | {v['ec_roll_deg'][0]:+.2f} to {v['ec_roll_deg'][1]:+.2f} | "
                  f"{v['ec_lat_mm'][0]:+.2f} to {v['ec_lat_mm'][1]:+.2f} | {v['seat_N_end']:.1f} |")
        print(f"| {lab} | tooth jumps over the cycle | {r['tooth_jumps']} | | | | | | | |")
    print()
    print("### Stall ramps: the auger's load rises until something gives (30 rpm)\n")
    print("| Design | Offset (mm) | Tilt (deg) | What gives | At (N·m at the auger) | Centre distance then (mm) |")
    print("|---|---|---|---|---|---|")
    for r in C:
        if r["stall_at"] is None:
            continue
        c = r["cfg"]
        st = r["steps"][0].get("stall", {}) if r["steps"] else {}
        lab = ("spring-loaded" if c.get("spring") else "as drawn") + (f", {c.get('f_spring', 6):g} N" if c.get("spring") else "")
        print(f"| {lab} | {c.get('a_err', 0.0):+.2f} | {r['stall_at']:g} | {st.get('mode') or 'held to 0.30'} | {st.get('load_Nm') if st.get('load_Nm') is not None else '-'} | "
              f"{st.get('cd_mm', '-')} |")
    print()


if __name__ == "__main__":
    entry_tables()
    robust_table()
    exit_table()
    cycle_tables()
