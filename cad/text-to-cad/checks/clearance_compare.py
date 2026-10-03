"""Nozzle-to-cup clearance: current design (servos below) vs servos above.

For each layout and tilt, a cup of radius r centred under the outlet hole is
raised until its rim touches a part or the mounting board (see
nozzle_clearance.py).  Writes checks/results/nozzle_clearance.json and
renders/checks/nozzle_clearance.png.

    python3 checks/clearance_compare.py [--source recreated|reference]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import parts_index
from lib import frames
from nozzle_clearance import clearance

ROOT = Path(__file__).resolve().parents[1]
TILTS = (0.0, 22.5, 45.0)
RADII = (5.0, 10.0, 15.0, 20.0, 25.0, 30.0, 40.0)


def run(source: str) -> dict:
    res = {"source": source, "radii_mm": RADII, "tilts_deg": TILTS, "rows": []}
    for variant in ("below", "above"):
        for tilt in TILTS:
            parts = parts_index.assembly(tilt, variant, source)
            outlet = frames.outlet_point(tilt)
            for row in clearance(parts, tuple(outlet), RADII):
                row.update(variant=variant, tilt_deg=tilt,
                           outlet_mm=[round(v, 2) for v in outlet])
                res["rows"].append(row)
                print(variant, tilt, row["cup_radius_mm"], row["gap_mm"], row["limited_by"])
    return res


def plot(res: dict, out: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, len(TILTS), figsize=(12, 3.8), sharey=True)
    colors = {"below": "#8a8f98", "above": "#2a6fdb"}
    labels = {"below": "servos below (current)", "above": "servos above (variant)"}
    for ax, tilt in zip(axes, TILTS):
        for variant in ("below", "above"):
            rows = [r for r in res["rows"] if r["variant"] == variant and r["tilt_deg"] == tilt]
            ax.plot([2 * r["cup_radius_mm"] for r in rows], [r["gap_mm"] for r in rows],
                    "o-", color=colors[variant], label=labels[variant], lw=2)
        ax.set_title(f"tilt {tilt:g}°")
        ax.set_xlabel("cup diameter (mm)")
        ax.grid(alpha=0.3)
    axes[0].set_ylabel("closest nozzle-to-rim gap (mm)")
    axes[0].legend(frameon=False)
    fig.suptitle("How close a cup centred under the outlet can come")
    fig.tight_layout()
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=150)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default="recreated", choices=["recreated", "reference"])
    a = ap.parse_args()
    res = run(a.source)
    suffix = "" if a.source == "recreated" else "_reference"
    out = ROOT / "checks" / "results" / f"nozzle_clearance{suffix}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, indent=1) + "\n")
    plot(res, ROOT / "renders" / "checks" / f"nozzle_clearance{suffix}.png")


if __name__ == "__main__":
    main()
