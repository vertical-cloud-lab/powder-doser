"""How close can the auger get to the beaker? (Sam, PR #185, 2026-11-17: "assuming we have a beaker on top of a scale with no
draft cage, how close can we get the auger while not sacrificing the good aspects of the electronics carriage designs? Give me an
attempt at that balance between parameters.")

    python drop_study.py --measure   # OCC: what hangs over the beaker's footprint, v7 (cage off) and v9 -> checks/drop_study.json
    python drop_study.py             # the ladder -> renders/v9/drop_study.png

With the cage gone, the beaker on the pan can rise until it meets the lowest part that ever comes over its footprint: the EC
parked, rising, docked or tilting, the station module, or any module passing the station. --measure finds that part for v7's
CAD (cage off, beaker under the exit) and for v9's. The rim is set 3 mm under it. The P16 sets a second limit: the balance's
back edge has to stay under the P16's body, so a short beaker (the 25 mL low form, 49 mm) caps how high the balance can go.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CLEAR = 3.0                               # rim under the lowest part over it
R_FOOT = 22.0                             # the 25 mL beaker's lip (radius 20) + 2 mm


def measure() -> None:
    import os
    import cadquery as cq
    from OCP.BRepAlgoAPI import BRepAlgoAPI_Common

    def run(d: Path, dx: float) -> dict:
        sys.path.insert(0, str(d))
        os.chdir(d)
        for m in [k for k in sys.modules if k in ("layout", "params", "parts", "parts3", "parts4", "parts5", "parts6", "parts7", "parts9", "kinematics")]:
            del sys.modules[m]
        import layout as L
        import params as PRM
        ex = L.DOSE_POINT
        xc, yc = ex[0] + dx, ex[1]
        cyl = cq.Solid.makeCylinder(R_FOOT, 300.0, cq.Vector(xc, yc, ex[2] - 200.0), cq.Vector(0, 0, 1))
        slab = cq.Solid.makeBox(2 * R_FOOT, 600.0, 300.0, cq.Vector(xc - R_FOOT, -300.0, ex[2] - 200.0))

        def zmin(s, tool):
            c = cq.Shape.cast(BRepAlgoAPI_Common(s.wrapped, tool.wrapped).Shape())
            return c.BoundingBox().zmin if c.Volume() > 1e-3 else None
        low = {}

        def note(tag, key, z):
            if z is not None and (f"{tag}:{key}" not in low or z < low[f"{tag}:{key}"]):
                low[f"{tag}:{key}"] = z
        k_st = L.carriage_at(L.CARRIAGE_LINK0, 0.0)
        poses = [("parked", L.State(ext=0.0, enclosure=False, scale=False))]
        poses += [("rise", L.State(ext=e, enclosure=False, scale=False)) for e in (PRM.PARK_DROP7 / 2, PRM.PARK_DROP7)]
        poses += [("tilt", L.State(tilt=t, enclosure=False, scale=False)) for t in (5, 10, 20, 30, 45, 60, 75, 90)]
        for tag, st in poses:
            for p in L.placements(st):
                stn = p.group in ("station_ec", "station_act", "station")
                mod1 = p.module == k_st and p.group == "modules"
                if not (stn or mod1) or (tag != "parked" and not (p.group in ("station_ec", "station_act") or mod1)):
                    continue
                s = L.moved(p.key, p.M)
                note("cycle" if (stn or tag != "parked") else "module", p.key, zmin(s, cyl))
        for p in L.placements(L.State(ext=0.0, enclosure=False, scale=False, station=False)):
            if p.module == k_st and p.group == "modules":
                note("passing", p.key, zmin(L.moved(p.key, p.M), slab))
        sys.path.remove(str(d))
        return {k: round(ex[2] - v, 2) for k, v in sorted(low.items(), key=lambda kv: kv[1])}
    v7 = run(HERE.parent / "chain-carousel-v7", 0.0)
    v9 = run(HERE, -7.0)
    old = json.loads((HERE / "checks" / "drop_study.json").read_text()) if (HERE / "checks" / "drop_study.json").exists() else {}
    old.setdefault("v7_cage_off", {})["depth"] = v7
    old.setdefault("v9", {})["depth"] = v9
    (HERE / "checks" / "drop_study.json").write_text(json.dumps(old, indent=1) + "\n")


# the ladder: (label, drop mm, drawn?, what sets it)
def ladder(js: dict) -> list:
    d7, d9 = js["v7_cage_off"]["depth"], js["v9"]["depth"]
    ec7 = max(v for k, v in d7.items() if k.endswith("sam_electronics_carriage"))
    sol7 = max(v for k, v in d7.items() if k.endswith("solenoid"))
    fin9 = max(v for k, v in d9.items() if k.endswith("sam_electronics_carriage"))
    strip = max(v for k, v in d9.items() if k.endswith("door_shutter"))
    tube = max(v for k, v in d9.items() if k.endswith(":auger"))
    p16 = 435.65 - (js["p16_over_balance"]["z"] - CLEAR + 10.0 + 49.0)        # base top + 10 to the pan + the 49 mm beaker
    return [("v7 as drawn: draft cage, beaker on a riser", 154.0, True, "the cage's lid under the EC"),
            ("v8: EC behind the balance, carousel 104 mm lower", 50.0, True, "clip 1 and the door bar over the cage"),
            ("v7, cage off, balance on a block, EC as drawn", round(ec7 + CLEAR, 1), False, f"the EC's front, parked ({ec7:.1f}); its solenoid {sol7:.1f}"),
            ("+ the EC's front cut back, solenoid behind the gear", round(35.1 + CLEAR, 1), False, "v7's door finger, parked (35.1)"),
            ("v9: + the door finger made a slim arm", round(fin9 + CLEAR, 1), True, f"the slim finger, parked ({fin9:.1f})"),
            ("+ the door's strip turned back under its housing", round(max(p16, strip + CLEAR), 1), False,
             f"the P16 over the balance's back edge with a 49 mm beaker ({p16:.1f}); the strips {strip:.0f}"),
            ("+ a 70 mm tall beaker, a door clear of the tube", round(tube + CLEAR, 1), False, f"the auger's tube ({tube:.1f})")]


def plot() -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    js = json.loads((HERE / "checks" / "drop_study.json").read_text())
    rows = ladder(js)
    INK, INK2, MUTED, SURF, GRID = "#0b0b0b", "#52514e", "#8a8984", "#fcfcfb", "#ecebe8"
    BLUE, ORANGE = "#2a78d6", "#eb6834"
    fig, ax = plt.subplots(figsize=(13.0, 5.4), facecolor=SURF)
    ax.set_facecolor(SURF)
    n = len(rows)
    for i, (lab, v, drawn, why) in enumerate(rows):
        y = n - 1 - i
        ax.barh(y, v, height=0.42, color=BLUE if drawn else ORANGE, hatch=None if drawn else "////", edgecolor=SURF, linewidth=0.0, zorder=3)
        ax.text(v + 2.0, y, f"{v:.0f} mm:  {why}", va="center", ha="left", fontsize=9, color=INK, fontweight="bold" if lab.startswith("v9") else "normal",
                bbox=dict(fc=SURF, ec="none", pad=0.6), zorder=4)
        ax.text(-3.0, y, lab, va="center", ha="right", fontsize=9.5, color=INK, fontweight="bold" if lab.startswith("v9") else "normal")
    ax.axvline(85.0, color=MUTED, lw=1.0, ls=(0, (4, 3)), zorder=2)
    ax.text(86.5, n - 0.45, "single doser, about 85", fontsize=8.5, color=INK2, va="bottom", ha="left")
    ax.set_xlim(0, 300)
    ax.set_ylim(-0.6, n - 0.2)
    ax.set_yticks([])
    ax.set_xlabel("exit to the beaker's rim, mm", color=INK2, fontsize=9)
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)
    ax.spines["bottom"].set_color(MUTED)
    ax.tick_params(colors=MUTED, labelsize=8.5)
    ax.grid(axis="x", color=GRID, lw=0.6, zorder=0)
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(fc=BLUE, label="a drawn version"), Patch(fc=ORANGE, hatch="////", ec=SURF, label="a step measured from the CAD, not drawn")],
              loc="lower right", frameon=False, fontsize=8.5)
    fig.suptitle("How close the auger can get with no draft cage: each step down, and what stops it", x=0.01, ha="left", fontsize=12.5, color=INK)
    fig.text(0.01, 0.015, "Each row: the lowest part over the 25 mL beaker's footprint (lip + 2 mm) through the whole cycle (parked, docking, "
             "0-90 deg, every module passing), 3 mm above the rim. OCC booleans on v7's and v9's CAD (checks/drop_study.json).",
             fontsize=8, color=INK2, ha="left")
    fig.tight_layout(rect=(0.25, 0.05, 1, 0.94))
    out = HERE / "renders" / "v9" / "drop_study.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=130, facecolor=SURF)
    for r in rows:
        print(f"{r[1]:6.1f}  {'drawn' if r[2] else 'step '}  {r[0]}  <- {r[3]}")


if __name__ == "__main__":
    measure() if "--measure" in sys.argv else plot()
