#!/usr/bin/env python3
"""Collect runs/*/result.json into one table (results.md and results.json) for the README and the PR.

Usage (from docs/physics-simulations/): python collect_results.py
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNS = HERE / "runs"

ORDER = [
    # particle methods
    "dem-liggghts-auger-short", "dem-liggghts-aor", "dem-liggghts-drum", "dem-liggghts-hall", "dem-liggghts-tap",
    "dem-liggghts-shear", "dem-liggghts-spread", "dem-liggghts-capillary",
    "dem-lammps-shear-mui", "dem-lammps-charge", "dem-yade-capillary", "dem-yade-directshear", "dem-mercurydpm",
    "dem-chrono-cpu", "dem-tribocharge-numba",
    # continuum and reduced order
    "mpm-taichi", "sph-granular", "fem-druckerprager", "mui-rheology", "analytic-orifice-screw",
    # stochastic and moisture
    "ca-avalanche", "mc-packing", "moisture-sorption",
    # inference and learned simulators
    "bayes-grainlearning", "bayes-gp-emulator-mcmc", "gns-gnn-simulator",
]


def fmt(v) -> str:
    if isinstance(v, float):
        return f"{v:.3g}"
    if isinstance(v, (list, tuple)):
        return "[" + ", ".join(fmt(x) for x in v[:6]) + (", …" if len(v) > 6 else "") + "]"
    if isinstance(v, dict):
        return "{" + ", ".join(f"{k}: {fmt(x)}" for k, x in list(v.items())[:4]) + "}"
    return str(v)


def main() -> None:
    rows, data = [], {}
    ids = [p.name for p in sorted(RUNS.iterdir()) if p.is_dir()]
    ids = [i for i in ORDER if i in ids] + [i for i in ids if i not in ORDER]
    for rid in ids:
        p = RUNS / rid / "result.json"
        if not p.exists():
            rows.append(f"| `{rid}` | — | — | no result.json | — |")
            continue
        r = json.loads(p.read_text())
        data[rid] = r
        files = sorted(x.name for x in (RUNS / rid).iterdir() if x.suffix in {".png", ".gif", ".mp4"})
        wall = r.get("wall_s")
        wall_s = f"{wall / 60:.1f} min" if isinstance(wall, (int, float)) and wall >= 60 else (f"{wall:.0f} s" if isinstance(wall, (int, float)) else "—")
        kr = r.get("key_results") or {}
        key = "; ".join(f"{k}: {fmt(v)}" for k, v in list(kr.items())[:3])
        rows.append(f"| [`{rid}`](runs/{rid}/) | {r.get('code', '')} {r.get('version', '')} | **{r.get('status', '?')}** | "
                    f"{wall_s} | {key[:220]} |")
    head = "| Run | Code | Status | Wall time | Key results |\n|---|---|---|---|---|\n"
    (HERE / "results.md").write_text(head + "\n".join(rows) + "\n")
    (HERE / "results.json").write_text(json.dumps(data, indent=1) + "\n")
    print(head + "\n".join(rows))


if __name__ == "__main__":
    main()
