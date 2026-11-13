"""Shared bookkeeping for the case modules: a uniform result record per case, its picture, its JSON."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))

import fem  # noqa: E402
import loads  # noqa: E402,F401
import materials as MAT  # noqa: E402

OUT = HERE / "out"


def record(module: str, case_id: str, *, design: str, part: str, load_case: str, res: "fem.Result",
           parts: list | None = None, exclude=None, exclude_r: float = 0.0, key_disp: dict | None = None,
           loads_desc: dict | None = None, notes: str = "", png_kw: dict | None = None, allow: dict | None = None,
           extra: dict | None = None, render: bool = True) -> dict:
    """One case's summary: per checked part its peak displacement, peak von Mises (raw and with singular
    support/load patches excluded), its material's allowable and the safety factor; named displacements
    (key_disp: name -> value in mm, the numbers that matter for function); the picture.

    parts: the mesh's part names to check (default all). allow overrides the allowable per part name (MPa)."""
    m = res.deck.m
    names = parts or m.names
    rows = []
    for nm in names:
        mat = MAT.get(res.deck.mat_override.get(nm, m.materials[m.names.index(nm)]))
        vm_raw, at_raw = res.vm_max(nm)
        vm_x, at_x = res.vm_max(nm, exclude=exclude, exclude_r=exclude_r) if exclude is not None else (vm_raw, at_raw)
        a = (allow or {}).get(nm, mat.allow)
        rows.append(dict(part=nm, material=mat.label, umax_mm=round(res.umax(nm), 5), vm_max_MPa=round(vm_raw, 3),
                         vm_max_at=[round(v, 1) for v in at_raw], vm_excl_MPa=round(vm_x, 3),
                         vm_excl_at=[round(v, 1) for v in at_x], allow_MPa=a,
                         sf=round(a / max(vm_x, 1e-9), 2)))
    out = dict(module=module, case=case_id, design=design, part=part, load_case=load_case, loads=loads_desc or {},
               nodes=int(m.n), elements=int(len(m.tet)), mesh_mm=m.h, wall_s=round(res.wall, 1), parts=rows,
               key_disp={k: round(float(v), 5) for k, v in (key_disp or {}).items()}, notes=notes,
               mass_kg=round(m.mass() * 1000, 4))
    if extra:
        out.update(extra)
    d = OUT / module
    d.mkdir(parents=True, exist_ok=True)
    if render:
        kw = dict(field="vm", title=f"{design}: {part}\n{load_case}")
        kw.update(png_kw or {})
        try:
            fem.render(res, d / f"{case_id}.png", **kw)
            out["png"] = f"out/{module}/{case_id}.png"
        except Exception as e:                       # noqa: BLE001
            out["png_error"] = str(e)[:200]
    (d / f"{case_id}.json").write_text(json.dumps(out, indent=1, default=float))
    return out


def worst_sf(rec: dict) -> float:
    return min(r["sf"] for r in rec["parts"])
