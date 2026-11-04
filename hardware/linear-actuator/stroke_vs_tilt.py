"""Rod travel the dosing station's linear actuator needs, against module tilt (issue #202).

The station geometry is copied from the rig scripts on PR #185's branch (claude/issue-128-20261013-2050 @ a94824f):

* v3  cad/chain-carousel-v3/test/chain_rig.py  tilt_to_ext(): EC clevis pin at Sam's (58, -76), +0.9 when docked;
      the EC parks 20 mm under its dock.
* v4  cad/chain-carousel-v4/test/chain_rig.py  tilt_to_ext(): EC v4 pin at (58, 76), -0.9 when docked; 28 mm park;
      50 deg at most (the cap reaches the top run at about 55 deg).
* v2 and the paternoster (U-yoke)  cad/chain-carousel-v2/test/chain_rig.py  tilt_to_ext(): stub pins at (32, -34),
      +0.9 docked, on a 60 mm U-fork; 20 mm dock.

Sam's frame has the hinge axis at the origin. The actuator is pinned at both ends, and its base pin sits (closed length
+ park) directly under the docked rod-end pin, as in those scripts, so a different actuator only moves the base pin.
"Stroke needed" adds a 3 mm reserve: 1 mm the rig pushes past each target to load the 2 mm lost-motion slots, and 2 mm
kept off the end stop (Actuonix's LAC guide advises setting the limits short of the physical stops).

Vendor numbers are from the makers' datasheets and product pages, read 2026-11-03 (see README.md).

The full-stroke tilts and the v4 extend limit (added 2026-11-04) back the README's check against ac-dev-lab: where
each stroke would stop if nothing else did, set against v3's 90 deg hinge stop and v4's cap contact at about 55 deg.

    python stroke_vs_tilt.py              # writes stroke_vs_tilt.png and stroke_vs_tilt.json next to this file
    python stroke_vs_tilt.py --json-only  # just the JSON (no matplotlib needed)
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESERVE = 3.0          # mm: 1 mm slot push + 2 mm off the end stop
DUTY = 0.20            # every candidate's datasheet duty-cycle limit
HOLD_N = 10.0          # N: about the largest steady load in the MuJoCo station runs (9.2 N peak in v3's cycle)
SLOT_PUSH = 1.0        # mm the rig pushes past each tilt target to load the 2 mm lost-motion slots
HINGE_STOP = 90.0      # deg: TILT_MAX_FRAME in v3/v4 params.py, the hinge's own travel limit
V4_CAP_CONTACT = 55.0  # deg: v4's module cap reaches the top run at about 55 (v4 README; its rig refuses > 50)
LAC_FULL_SCALE = 1023  # LAC position counts over the full stroke (advanced configuration guide)

DESIGNS = {
    #        rod-end pin (x, z) docked, park/dock travel, yoke length, tilt limit, direction of tilt
    "v3": dict(pin=(58.0, -76.0 + 0.9), park=20.0, yoke=0.0, tilt_max=90.0, sign=+1),
    "v4": dict(pin=(58.0, 76.0 - 0.9), park=28.0, yoke=0.0, tilt_max=50.0, sign=-1),
    "v2": dict(pin=(32.0, -34.0 + 0.9), park=20.0, yoke=60.0, tilt_max=90.0, sign=+1),
}


def _pin(d: dict, deg: float) -> tuple[float, float]:
    x0, z0 = d["pin"]
    a = math.radians(deg)
    if d["sign"] > 0:      # v3 / v2: the pin turns counter-clockwise in Sam's x-z
        return x0 * math.cos(a) - z0 * math.sin(a), x0 * math.sin(a) + z0 * math.cos(a)
    return x0 * math.cos(a) + z0 * math.sin(a), -x0 * math.sin(a) + z0 * math.cos(a)   # v4 (z points down)


def _base(d: dict, closed: float) -> tuple[float, float]:
    x0, z0 = d["pin"]
    drop = closed + d["park"] + d["yoke"]
    return (x0, z0 - drop) if d["sign"] > 0 else (x0, z0 + drop)


def extension(design: str, closed: float, deg: float) -> float:
    """Rod extension from fully retracted (mm, dock travel included) to hold the module at `deg`."""
    d = DESIGNS[design]
    (px, pz), (bx, bz) = _pin(d, deg), _base(d, closed)
    return math.hypot(px - bx, pz - bz) - closed - d["yoke"]


def moment_arm(design: str, closed: float, deg: float) -> float:
    """Perpendicular distance (mm) from the hinge to the actuator's line of action."""
    d = DESIGNS[design]
    (px, pz), (bx, bz) = _pin(d, deg), _base(d, closed)
    L = math.hypot(px - bx, pz - bz)
    ux, uz = (px - bx) / L, (pz - bz) / L
    return abs(px * uz - pz * ux)


def reach(design: str, closed: float, stroke: float) -> float:
    """Largest tilt (deg) the stroke reaches with RESERVE kept back, capped at the design's limit."""
    hi = DESIGNS[design]["tilt_max"]
    if extension(design, closed, hi) + RESERVE <= stroke:
        return hi
    lo = 0.0
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        lo, hi = (mid, hi) if extension(design, closed, mid) + RESERVE <= stroke else (lo, mid)
    return lo


def full_stroke_tilt(design: str, closed: float, stroke: float) -> float:
    """Tilt (deg) at full extension with no reserve and no design limit, up to the hinge stop: where the rod would
    stop if nothing else stopped it."""
    lo, hi = 0.0, HINGE_STOP
    if extension(design, closed, hi) <= stroke:
        return hi
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        lo, hi = (mid, hi) if extension(design, closed, mid) <= stroke else (lo, mid)
    return lo


def dose_travel(design: str, closed: float, deg: float = 30.0) -> float:
    """Rod travel (mm) for one dose in the rig's sequence: lift to 3 mm short, seat (+1), back to the dock, tilt (+1),
    back to level, park = 2 x extension + 4."""
    return 2.0 * extension(design, closed, deg) + 4.0


# Candidates: vendor data read 2026-11-03. closed = hole to hole, retracted (mm). v0 no-load speed (mm/s);
# f_pe, v_pe = peak-efficiency point; f_max = max force; backdrive (N); side = max side load (N).
CANDIDATES = [
    dict(name="Actuonix P16-150-22-12-P", short="P16-150 22:1", stroke=150, closed=197, v0=46, f_pe=25, v_pe=34,
         f_max=50, backdrive=75, side=10, repeat=0.6, mass=125, ip="IP54", price=90.0),
    dict(name="Actuonix P16-150-64-12-P", short="P16-150 64:1", stroke=150, closed=197, v0=18, f_pe=40, v_pe=14,
         f_max=90, backdrive=200, side=10, repeat=0.6, mass=125, ip="IP54", price=90.0),
    dict(name="Actuonix P16-100-22-12-P", short="P16-100 22:1", stroke=100, closed=147, v0=46, f_pe=25, v_pe=34,
         f_max=50, backdrive=75, side=15, repeat=0.4, mass=110, ip="IP54", price=90.0),
    dict(name="Actuonix L16-140-63-12-P", short="L16-140 63:1", stroke=140, closed=208, v0=20, f_pe=38, v_pe=15,
         f_max=100, backdrive=46, side=20, repeat=0.5, mass=84, ip="IP54", price=80.0),
    dict(name="Actuonix L16-140-35-12-P", short="L16-140 35:1", stroke=140, closed=208, v0=32, f_pe=24, v_pe=24,
         f_max=50, backdrive=31, side=20, repeat=0.5, mass=84, ip="IP54", price=80.0),
    dict(name="Actuonix P8-100-165-12-P", short="P8-100 165:1", stroke=100, closed=135, v0=9.2, f_pe=35, v_pe=7.5,
         f_max=110, backdrive=40, side=2, repeat=0.5, mass=41, ip="IP54", price=85.0),
    dict(name="Progressive Automations PA-MC1-6-8-POT-12VDC", short="PA-MC1 6 in 8 lb", stroke=152, closed=223,
         v0=48, f_pe=35, v_pe=28.5, f_max=35, backdrive=20, side=None, repeat=None, mass=None, ip="IP65", price=77.99),
]


def loaded_speed(c: dict, force: float = HOLD_N) -> float:
    """Speed at `force`, on the straight line through the no-load and peak-efficiency points of the load curve."""
    return c["v0"] - (c["v0"] - c["v_pe"]) * force / c["f_pe"]


def table() -> dict:
    rows = []
    for c in CANDIDATES:
        r = dict(c)
        for v in ("v3", "v4", "v2"):
            r[f"reach_{v}_deg"] = round(reach(v, c["closed"], c["stroke"]), 1)
        for v in ("v3", "v4"):
            r[f"full_stroke_tilt_{v}_deg"] = round(full_stroke_tilt(v, c["closed"], c["stroke"]), 1)
        v = loaded_speed(c)
        r["speed_at_10N_mm_s"] = round(v, 1)
        for d in ("v3", "v4"):
            t = dose_travel(d, c["closed"]) / v
            r[f"motion_per_30deg_dose_{d}_s"] = round(t, 1)
            r[f"min_dose_spacing_{d}_s"] = round(t / DUTY)
        r["moment_arm_30deg_v3_mm"] = round(moment_arm("v3", c["closed"], 30.0), 1)
        r["frame_height_change_mm"] = round(c["closed"] - 197.4, 1)
        rows.append(r)
    curves = {d: {str(a): round(extension(d, 197.4, a), 1) for a in range(0, int(DESIGNS[d]["tilt_max"]) + 1, 5)}
              for d in DESIGNS}
    return dict(reserve_mm=RESERVE, duty=DUTY, hold_N=HOLD_N,
                extension_mm_vs_tilt_for_P16_150=curves,
                stroke_needed_mm={d: {a: round(extension(d, 197.4, a) + RESERVE, 1) for a in (20, 30, 40, 50, 90)
                                      if a <= DESIGNS[d]["tilt_max"]} for d in DESIGNS},
                v4_limit=v4_limit(),
                candidates=rows)


def v4_limit(closed: float = 197.4, stroke: float = 150.0) -> dict:
    """Where v4's cap meets the top run, and the LAC extend limit that stops the P16-150 at 50 deg instead."""
    limit = extension("v4", closed, 50.0) + SLOT_PUSH
    contact = extension("v4", closed, V4_CAP_CONTACT)
    return dict(cap_contact_deg=V4_CAP_CONTACT, cap_contact_extension_mm=round(contact, 1),
                stroke_past_contact_mm=round(stroke - contact, 1),
                extend_limit_mm=round(limit, 1),
                extend_limit_lac_counts=round(limit * LAC_FULL_SCALE / stroke),
                cap_contact_lac_counts=round(contact * LAC_FULL_SCALE / stroke))


def plot(path: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    surface, ink, ink2, muted, grid, axis = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
    colors = {"v3": "#2a78d6", "v4": "#eb6834", "v2": "#1baf7a"}   # categorical slots 1-3 (validated, light mode)
    names = {"v3": "v3, augers inside the loop", "v4": "v4, augers outside (50° limit)",
             "v2": "v2 / paternoster U-yoke"}
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10.5})
    fig, ax = plt.subplots(figsize=(9.2, 5.4), dpi=150)
    fig.patch.set_facecolor(surface)
    ax.set_facecolor(surface)

    ax.axvspan(20, 40, color="#f0efec", zorder=0, lw=0)
    ax.text(30, 4, "dose window\n20–40°", ha="center", va="bottom", color=ink2, fontsize=9.5)

    for s, lab in ((100, "100 mm stroke: P16-100, P8-100"), (140, "140 mm: L16-140"),
                   (150, "150 mm: P16-150, as drawn")):
        ax.axhline(s, color=muted, lw=1.0, zorder=1)
        ax.text(1, s + 1.5, lab, ha="left", va="bottom", color=ink2, fontsize=9.5)

    for d in ("v3", "v4", "v2"):
        tmax = DESIGNS[d]["tilt_max"]
        xs = [i * tmax / 200 for i in range(201)]
        ys = [extension(d, 197.4, x) + RESERVE for x in xs]
        ax.plot(xs, ys, color=colors[d], lw=2.0, solid_capstyle="round", solid_joinstyle="round", zorder=3,
                label=names[d])
        ax.plot([xs[-1]], [ys[-1]], "o", ms=8, color=colors[d], mec=surface, mew=2, zorder=4)
        dy = {"v3": 3, "v4": 4, "v2": 4}[d]
        ha = {"v3": "right", "v4": "left", "v2": "right"}[d]
        dx = {"v3": -2, "v4": 2, "v2": -1}[d]
        ax.text(xs[-1] + dx, ys[-1] + dy, f"{names[d].split(',')[0]}: {ys[-1]:.0f} mm at {tmax:.0f}°",
                ha=ha, va="bottom", color=ink, fontsize=9.5)

    # where the 100 and 150 mm strokes run out on the newest designs
    for d, s in (("v3", 100), ("v4", 100), ("v3", 150)):
        a = reach(d, 197.4, s)
        if a < DESIGNS[d]["tilt_max"]:
            ax.plot([a], [s], "o", ms=8, color=colors[d], mec=surface, mew=2, zorder=5)
            if d == "v3":
                ax.text(a + 1.2, s - 3.5, f"{a:.0f}°", ha="left", va="top", color=ink, fontsize=9.5)
            else:
                ax.text(a - 1.2, s + 3.0, f"{a:.0f}°", ha="right", va="bottom", color=ink, fontsize=9.5)

    ax.set_xlim(0, 92)
    ax.set_ylim(0, 175)
    ax.set_xticks(range(0, 91, 10))
    ax.set_xticklabels([f"{t}°" for t in range(0, 91, 10)])
    ax.set_xlabel("Module tilt at the station", color=ink2)
    ax.set_ylabel("Stroke needed (mm)", color=ink2)
    ax.grid(axis="y", color=grid, lw=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(axis)
        ax.spines[side].set_linewidth(0.8)
    ax.tick_params(colors=muted, labelcolor=ink2, length=0)
    leg = ax.legend(loc="lower right", bbox_to_anchor=(1.0, 0.04), frameon=False, fontsize=9.5)
    for t in leg.get_texts():
        t.set_color(ink)
    fig.text(0.075, 0.955, "Stroke the station actuator needs, from the #185 rig geometry", ha="left", va="bottom",
             fontsize=12.5, color=ink, fontweight="bold")
    fig.text(0.075, 0.875, "Rod travel from fully retracted, dock lift included, plus a 3 mm reserve.\n"
             "Within 1 mm of these curves for any closed length from 135 to 247 mm.", ha="left", va="bottom",
             fontsize=9.5, color=ink2, linespacing=1.4)
    fig.subplots_adjust(left=0.075, right=0.985, top=0.845, bottom=0.11)
    fig.savefig(path, facecolor=surface)


if __name__ == "__main__":
    out = table()
    (HERE / "stroke_vs_tilt.json").write_text(json.dumps(out, indent=1) + "\n")
    if "--json-only" not in sys.argv:
        plot(HERE / "stroke_vs_tilt.png")
    for d, v in out["stroke_needed_mm"].items():
        print(d, v)
    for r in out["candidates"]:
        print(f"{r['short']:18s} reach v3 {r['reach_v3_deg']:5.1f}  v4 {r['reach_v4_deg']:5.1f}  v2 {r['reach_v2_deg']:5.1f} | "
              f"{r['speed_at_10N_mm_s']:5.1f} mm/s @10 N | 30° dose motion v3 {r['motion_per_30deg_dose_v3_s']:4.1f} s, "
              f"v4 {r['motion_per_30deg_dose_v4_s']:4.1f} s | min spacing v3 {r['min_dose_spacing_v3_s']:3d} s, "
              f"v4 {r['min_dose_spacing_v4_s']:3d} s | arm30 {r['moment_arm_30deg_v3_mm']} | dH {r['frame_height_change_mm']}")
    for r in out["candidates"]:
        print(f"{r['short']:18s} full stroke: v3 {r['full_stroke_tilt_v3_deg']:5.1f} deg, v4 {r['full_stroke_tilt_v4_deg']:5.1f} deg")
    print("v4 limit", out["v4_limit"])
