"""Assembly animation for one apparatus: components fly in step by step, with captions."""
from __future__ import annotations

import math

import numpy as np

from engine import FPS, Scene, Writer, ease, overlay
import assemblies as A


def view_dist(a):
    b = np.array([c.mesh.bounds @ c.M[:3, :3].T + c.M[:3, 3] for c in a["comps"] if c.kind != "context"])
    diag = float(np.linalg.norm(b.reshape(-1, 3).max(0) - b.reshape(-1, 3).min(0)))
    return 1.7 * diag / a["view"].get("zoom", 1.0)


def assembly_segment(w: Writer, key: str, fly_s=0.8, hold_s=1.0, orbit_s=3.0, title_prefix="Assembly"):
    a = A.ASSEMBLIES[key]()
    sc = Scene(a["comps"])
    v = a["view"]
    dist = view_dist(a)
    nsteps = len(a["steps"])
    total = nsteps * (fly_s + hold_s) + orbit_s
    fly_n, hold_n = int(fly_s * FPS), int(hold_s * FPS)
    t_global = 0.0

    def cam(t):
        sc.camera(v["focus"], v["azimuth"] + 25 * (t / total), v["elevation"], dist)

    for i, c in enumerate(a["comps"]):
        sc.show(i, c.step == 0)
    for s in range(nsteps):
        new = [i for i, c in enumerate(a["comps"]) if c.step == s]
        for i in new:
            sc.show(i, True)
        for f in range(fly_n if s > 0 else 1):
            u = ease((f + 1) / fly_n) if s > 0 else 1.0
            for i in new:
                c = a["comps"][i]
                off = np.array(c.explode) * (1 - u)
                M = c.M.copy()
                M[:3, 3] += off
                sc.pose(i, M)
                if c.opacity < 1:
                    sc.opacity(i, c.opacity * max(u, 0.15))
            cam(t_global)
            t_global += 1 / FPS
            w.add(overlay(sc.grab(), title=a["title"], caption=a["steps"][s], step=f"{s + 1}/{nsteps}",
                          tag=title_prefix))
        for f in range(hold_n):
            cam(t_global)
            t_global += 1 / FPS
            w.add(overlay(sc.grab(), title=a["title"], caption=a["steps"][s], step=f"{s + 1}/{nsteps}",
                          tag=title_prefix))
    n_orb = int(orbit_s * FPS)
    for f in range(n_orb):
        cam(t_global)
        t_global += 1 / FPS
        w.add(overlay(sc.grab(), title=a["title"], caption="Assembled", tag=title_prefix))
    sc.close()
    return a


if __name__ == "__main__":
    import sys
    import time
    key = sys.argv[1]
    t0 = time.time()
    w = Writer(sys.argv[2])
    assembly_segment(w, key)
    w.close()
    print(key, w.n, "frames", round(time.time() - t0, 1), "s")
