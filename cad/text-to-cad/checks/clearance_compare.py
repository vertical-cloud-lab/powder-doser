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
RADII = (10.0, 20.0, 29.0, 42.5, 50.0, 60.0)
# (name, servo layout, board front edge y or None for the layout's own, label)
CONFIGS = [
    ("below", "below", None, "servos below (current); board edge at the legs, y = 55.4"),
    ("below_board_back", "below", 100.0,
     "servos below, board edge moved back to y = 100 (legs hang free)"),
    ("above", "above", None, "servos above (variant, 5 mm lower); plate overhangs the board, edge at y = 100"),
]


def run(source: str) -> dict:
    res = {"source": source, "radii_mm": RADII, "tilts_deg": TILTS,
           "configs": {c[0]: c[3] for c in CONFIGS}, "rows": []}
    for cfg, variant, board_y, _ in CONFIGS:
        for tilt in TILTS:
            parts = parts_index.assembly(tilt, variant, source, board_front_y=board_y)
            outlet = frames.outlet_point(tilt, variant)
            for row in clearance(parts, tuple(outlet), RADII):
                row.update(config=cfg, variant=variant, tilt_deg=tilt,
                           outlet_mm=[round(v, 2) for v in outlet])
                res["rows"].append(row)
                print(cfg, tilt, row["cup_radius_mm"], row["gap_mm"], row["limited_by"], flush=True)
    return res


def plot(res: dict, out: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, len(TILTS), figsize=(13, 4.2), sharey=True)
    colors = {"below": "#8a8f98", "below_board_back": "#d08a2c", "above": "#2a6fdb"}
    styles = {"below": "o-", "below_board_back": "s--", "above": "o-"}
    labels = {"below": "servos below (current), board edge at legs",
              "below_board_back": "servos below, board edge moved back",
              "above": "servos above (variant), plate overhangs board"}
    for ax, tilt in zip(axes, TILTS):
        for cfg in labels:
            rows = [r for r in res["rows"] if r["config"] == cfg and r["tilt_deg"] == tilt]
            ax.plot([2 * r["cup_radius_mm"] for r in rows], [r["gap_mm"] for r in rows],
                    styles[cfg], color=colors[cfg], label=labels[cfg], lw=2)
        ax.set_title(f"tilt {tilt:g}°")
        ax.set_xlabel("cup diameter (mm)")
        ax.grid(alpha=0.3)
    axes[0].set_ylabel("closest nozzle-to-rim gap (mm)")
    axes[0].legend(frameon=False, fontsize=8, loc="upper left")
    fig.suptitle("How close a cup (or any receiver) centred under the outlet can come")
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
