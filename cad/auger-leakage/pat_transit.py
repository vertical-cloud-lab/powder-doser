"""Paternoster transit motion as the auger outlet sees it, from the MuJoCo carousel model.

Runs ``cad/paternoster/sim/carousel_sim.run_carousel`` for three index moves with the
recommended profile (trapezoid, 1.5 s per index, ramps of one pendulum period, bronze
pivots with mu = 0.1) and records gondola 1 (the one leaving the station): pivot (y, z),
swing angle. The auger axis passes through Sam's hinge axis, 16 mm below the pivot, so
its point in the gondola is (0, -16) mm, swung by the gondola's angle. Writes
``out/pat_transit.npz`` with t, roll (swing, rad), and the outlet point's acceleration
(ay, az, mm/s^2) after a 10 ms Savitzky-Golay smoothing, plus a summary in
``out/pat_transit.json``.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
from scipy.signal import savgol_filter

HERE = os.path.dirname(os.path.abspath(__file__))
PSIM = os.path.normpath(os.path.join(HERE, "..", "paternoster", "sim"))
OUT = os.path.join(HERE, "out")
sys.path.insert(0, PSIM)
import model as M  # noqa: E402

M.OUT = OUT          # keep the pivot-table cache out of the paternoster tree
import carousel_sim as CS  # noqa: E402


def main():
    os.makedirs(OUT, exist_ok=True)
    pend = CS.pendulum()
    fz = pend["f_Hz"]
    fric = 0.1 * pend["mass_kg"] * M.G * 0.002          # carousel_sim's bronze-pivot friction (mu = 0.1)
    T = 1.5
    sh, stops = M.sequence(M.KN.HOME_SHIFT, [(M.PR.MODULE_LINKS, T, "trap", 0.5, dict(fa=1 / fz / T))] * 3, dwell0=0.3)
    L = CS.run_carousel(sh, dict(damping=1e-4, fric=fric), log_every=1)
    t = L["t"] - L["t"][0]
    k = 0                                                # gondola 1 = module 0, at the station at HOME_SHIFT
    th = L["th"][:, k]
    y = L["py"][:, k] + 16.0 * np.sin(th)
    z = L["pz"][:, k] - 16.0 * np.cos(th)
    dt = float(np.median(np.diff(t)))
    win = int(round(0.010 / dt)) | 1          # 10 ms: the gondola and bushings filter the chordal impacts above about 50 Hz
    ay = savgol_filter(y, max(win, 5), 3, deriv=2, delta=dt)
    az = savgol_filter(z, max(win, 5), 3, deriv=2, delta=dt)
    t_move0 = 0.3
    np.savez_compressed(os.path.join(OUT, "pat_transit.npz"), t=t, roll=th, y=y, z=z, ay=ay, az=az,
                        t_move0=t_move0, stops=np.array(stops))
    sel = (t >= t_move0) & (t < t_move0 + 2.0)
    s = dict(pendulum=pend, profile="trapezoid, 1.5 s per index, ramps = one pendulum period, mu 0.1 pivots",
             index_link=M.PR.MODULE_LINKS, dt_s=dt,
             first_index=dict(swing_max_deg=float(np.degrees(np.abs(th[sel] - th[sel][0]).max())),
                              accel_max_mm_s2=float(np.hypot(ay[sel], az[sel]).max()),
                              accel_rms_mm_s2=float(np.sqrt(np.mean(ay[sel] ** 2 + az[sel] ** 2)))),
             three_indexes=dict(swing_max_deg=float(np.degrees(np.abs(th - th[0]).max())),
                                accel_max_mm_s2=float(np.hypot(ay, az)[t > 0.05].max())))
    with open(os.path.join(OUT, "pat_transit.json"), "w") as f:
        json.dump(s, f, indent=1)
    print(json.dumps(s, indent=1))


if __name__ == "__main__":
    main()
