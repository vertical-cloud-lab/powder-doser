"""Check that every grain leaving through the exit was counted, and repair the count if not.

``fix massflow/mesh`` only counts grains that cross the disk 1.5 mm below the
exit. At low tilt (0 deg) gravity points sideways, so some grains fall out of
the simulation box before reaching the disk and are silently dropped. This
script follows grain IDs between consecutive dumps:

* a grain that disappears with its last position near the outlet (z < 3 mm)
  left through the exit, counted or not;
* a grain that disappears near the top of the meshed section is feed-zone spill
  and is irrelevant to the dose.

If outlet exits exceed the counted ones, it writes ``outflow_corrected.txt``
(same columns as ``outflow.txt``, sampled at the dump interval), which
``analyze.py`` then prefers.

    python audit_outlet.py /tmp/dem/runs/rig_t00_r60 [--write]
"""

from __future__ import annotations

import argparse
import glob
import json
import math
import os
import re

import numpy as np


def audit(case, write=False):
    meta = json.load(open(os.path.join(case, "case.json")))
    cfg, g = meta["cfg"], meta["geometry"]
    z_top = g["funnel_h"] + g["n_turns"] * g["pitch"] + g["flight_t"] + g["feed_h"]
    files = sorted(glob.glob(os.path.join(case, "dump", "p.*.txt")),
                   key=lambda p: int(re.findall(r"p\.(\d+)\.txt", p)[0]))
    if len(files) < 2:
        print(os.path.basename(case), "no dumps, cannot audit")
        return None
    O = np.loadtxt(os.path.join(case, "outflow.txt"), comments="#", ndmin=2)
    dt = meta["dt"]
    prev, rows = None, []
    n_out = top = 0
    m_out = 0.0
    for f in files:
        step = int(re.findall(r"p\.(\d+)\.txt", f)[0])
        A = np.loadtxt(f, skiprows=9, ndmin=2)
        cur = {int(i): (z, r) for i, z, r in zip(A[:, 0], A[:, 5] * 1e3, A[:, 2])}
        if prev is not None:
            for i in set(prev) - set(cur):
                z, r = prev[i]
                if z < 3.0:
                    n_out += 1
                    m_out += cfg["density"] * 4 / 3 * math.pi * r ** 3
                elif z > z_top - 6:
                    top += 1
        prev = cur
        rows.append((step * dt, m_out, n_out, len(cur)))
    t_first, t_last = rows[0][0], rows[-1][0]
    counted = np.interp(t_last, O[:, 0], O[:, 2]) - np.interp(t_first, O[:, 0], O[:, 2])
    missed = n_out - counted
    print(f"{os.path.basename(case)}: {n_out} grains left through the exit, {counted:.0f} counted "
          f"({100 * missed / max(n_out, 1):.0f} % missed); {top} feed-zone spill at the top")
    if write and missed > 0.02 * max(n_out, 1):
        with open(os.path.join(case, "outflow_corrected.txt"), "w") as fh:
            fh.write("# outlet exits reconstructed from dumps by audit_outlet.py: t_s mass_kg n_out n_atoms\n")
            for t, m, n, na in rows:
                fh.write(f"{t:.6f} {m:.6e} {n} {na}\n")
        print("  wrote outflow_corrected.txt")
    return missed


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cases", nargs="+")
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    for c in a.cases:
        audit(c, a.write)
