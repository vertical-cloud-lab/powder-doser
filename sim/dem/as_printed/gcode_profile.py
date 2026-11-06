"""Recover the internal geometry of a printed auger from its sliced G-code.

Bambu print jobs (``*.3mf`` in the printer's ``/cache``) carry the G-code but no
mesh, so this rebuilds the part from the toolpaths: every extruding ``G1`` and
arc (``G2``/``G3``) move, layer by layer, tagged with the slicer's
``; FEATURE:`` comments. The auger is printed exit-down, so print z = 0 is the
exit plane, the same frame as ``geometry.py``.

Per layer it finds the closed outer-wall loops (bins of radius whose wall
points cover most of the circle), converts toolpath radii to surface radii
(half a line width out of a solid, into a hole), and reports the bore, core
and outer radii. It also gets the flight pitch and handedness (from the angle
of the flight in the gap between core and bore), and the gear tooth count.

    python gcode_profile.py auger_open_end.3mf --out auger_open_end
"""

from __future__ import annotations

import argparse
import json
import math
import re
import zipfile

import numpy as np

LINE_W = 0.42  # mm, Bambu 0.4 mm nozzle default wall line width


def read_gcode(path):
    if path.endswith(".3mf"):
        with zipfile.ZipFile(path) as z:
            return z.read("Metadata/plate_1.gcode").decode(errors="replace").splitlines()
    with open(path, errors="replace") as f:
        return f.read().splitlines()


def extrusion_segments(lines):
    """(z, x0, y0, x1, y1) and feature name for every extruding move; arcs become chords."""
    x = y = z = 0.0
    absolute, e_rel, feat = True, True, ""
    segs, feats = [], []
    num = re.compile(r"^-?\d*\.?\d+$")
    for ln in lines:
        if ln.startswith("; FEATURE:"):
            feat = ln.split(":", 1)[1].strip()
            continue
        w = ln.split(";", 1)[0].split()
        if not w:
            continue
        c = w[0]
        if c in ("G90", "G91"):
            absolute = c == "G90"
            continue
        if c in ("M82", "M83"):
            e_rel = c == "M83"
            continue
        if c not in ("G0", "G1", "G2", "G3"):
            continue
        p = {t[0]: float(t[1:]) for t in w[1:] if t[0] in "XYZEIJ" and num.match(t[1:])}
        if absolute:
            nx, ny, nz = p.get("X", x), p.get("Y", y), p.get("Z", z)
        else:
            nx, ny, nz = x + p.get("X", 0.0), y + p.get("Y", 0.0), z + p.get("Z", 0.0)
        if p.get("E", 0.0) > 0 and e_rel:
            if c == "G1" and ("X" in p or "Y" in p):
                segs.append((nz, x, y, nx, ny))
                feats.append(feat)
            elif c in ("G2", "G3"):
                cx, cy = x + p.get("I", 0.0), y + p.get("J", 0.0)
                a0, a1 = math.atan2(y - cy, x - cx), math.atan2(ny - cy, nx - cx)
                r = math.hypot(x - cx, y - cy)
                if c == "G3":
                    while a1 <= a0:
                        a1 += 2 * math.pi
                else:
                    while a1 >= a0:
                        a1 -= 2 * math.pi
                n = max(2, int(abs(a1 - a0) * r / 0.3) + 1)
                px, py = x, y
                for k in range(1, n + 1):
                    a = a0 + (a1 - a0) * k / n
                    qx, qy = cx + r * math.cos(a), cy + r * math.sin(a)
                    segs.append((nz, px, py, qx, qy))
                    feats.append(feat)
                    px, py = qx, qy
        x, y, z = nx, ny, nz
    S = np.round(np.array(segs, float), 3)
    return S, np.array(feats)


def sample(S, step=0.05):
    """Points every `step` mm along the segments (centred coordinates)."""
    out = []
    for s in S:
        n = max(2, int(math.hypot(s[3] - s[1], s[4] - s[2]) / step))
        t = np.linspace(0.0, 1.0, n)
        out.append(np.c_[s[1] + t * (s[3] - s[1]), s[2] + t * (s[4] - s[2])])
    return np.vstack(out) if out else np.zeros((0, 2))


def wall_loops(P, cover=0.7, dr=0.05, rmax=40.0):
    """Radii of (nearly) closed circular wall loops among points P (centred)."""
    r = np.hypot(P[:, 0], P[:, 1])
    th = np.degrees(np.arctan2(P[:, 1], P[:, 0]))
    bins = np.arange(0.0, rmax, dr)
    k = np.digitize(r, bins) - 1
    cov = np.zeros(len(bins))
    for i in np.unique(k):
        if 0 <= i < len(bins):
            cov[i] = len(np.unique(np.floor(th[k == i] / 2.0))) / 180.0
    cov = np.convolve(cov, np.ones(5), "same")  # a polygonal loop wobbles over a few bins
    return bins[cov > cover] + dr / 2


def profile(S, feat, bore_window=(9.0, 11.5)):
    keep = ~np.char.startswith(feat.astype(str), "Support")
    S, feat = S[keep], feat[keep]
    zs = np.unique(S[:, 0])
    ow = feat == "Outer wall"
    # axis: algebraic circle fit to the outer walls of the middle third of the print
    zmid = np.median(zs)
    m = ow & (np.abs(S[:, 0] - zmid) < (zs.max() - zs.min()) / 6)
    P = np.vstack([S[m][:, 1:3], S[m][:, 3:5]])
    A = np.c_[2 * P[:, 0], 2 * P[:, 1], np.ones(len(P))]
    cx, cy, _ = np.linalg.lstsq(A, (P ** 2).sum(1), rcond=None)[0]
    S = S.copy()
    S[:, [1, 3]] -= cx
    S[:, [2, 4]] -= cy
    rows = []
    for z in zs:
        lay = S[:, 0] == z
        loops = wall_loops(sample(S[lay & ow]))
        bore = loops[(loops >= bore_window[0]) & (loops < bore_window[1])]
        core = loops[loops < bore_window[0]]
        out = loops[loops >= bore_window[1]]
        allp = sample(S[lay])
        ra = np.hypot(allp[:, 0], allp[:, 1])
        th = np.arctan2(allp[:, 1], allp[:, 0])
        bore_r = bore.min() - LINE_W / 2 if len(bore) else np.nan
        core_r = core.max() + LINE_W / 2 if len(core) else 0.0
        # flight: material in the gap between core and bore
        gap = (ra > core_r + 0.6) & (ra < (bore_r if np.isfinite(bore_r) else 10.0) - 0.6)
        ang = float(np.angle(np.mean(np.exp(1j * th[gap])))) if gap.sum() > 20 else np.nan
        rows.append((z, bore_r, core_r, out.max() + LINE_W / 2 if len(out) else np.nan, ra.max(), ang))
    return np.array(rows), S, (cx, cy)


def flight_pitch(R, zlo, zhi):
    ok = np.isfinite(R[:, 5]) & (R[:, 0] > zlo) & (R[:, 0] < zhi)
    k, _ = np.polyfit(R[ok, 0], np.unwrap(R[ok, 5]), 1)
    return 2 * math.pi / abs(k), "right" if k > 0 else "left"


def gear_teeth(S, R, bore_window):
    big = R[:, 4] > bore_window[1] + 5
    if not big.any():
        return None, None
    zg = R[big, 0]
    z = zg[len(zg) // 2]
    P = sample(S[S[:, 0] == z])
    r = np.hypot(P[:, 0], P[:, 1])
    th = np.arctan2(P[:, 1], P[:, 0])
    sel = r > np.percentile(r, 50)
    prof = np.zeros(720)
    for k, rr in zip(((th[sel] + np.pi) / (2 * np.pi) * 720).astype(int) % 720, r[sel]):
        prof[k] = max(prof[k], rr)
    for i in range(720):
        if prof[i] == 0:
            prof[i] = prof[i - 1]
    tips = prof > 0.5 * (prof.max() + np.percentile(prof, 10))
    return int(np.sum(tips & ~np.roll(tips, 1))), (float(zg.min()), float(zg.max()), float(prof.max()))


def section_figure(S, zsel, title, out, rlim=14.0):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    zs = np.unique(S[:, 0])
    cols = 4
    rows = math.ceil(len(zsel) / cols)
    fig, axs = plt.subplots(rows, cols, figsize=(2.6 * cols, 2.7 * rows))
    for ax, zz in zip(axs.flat, zsel):
        z = zs[np.argmin(np.abs(zs - zz))]
        for s in S[S[:, 0] == z]:
            ax.plot([s[1], s[3]], [s[2], s[4]], lw=0.5, color="#1f5fa8")
        ax.set_title(f"z = {z:.1f} mm", fontsize=8)
        ax.set_aspect("equal")
        ax.set_xlim(-rlim, rlim)
        ax.set_ylim(-rlim, rlim)
        ax.tick_params(labelsize=6)
    for ax in list(axs.flat)[len(zsel):]:
        ax.axis("off")
    fig.suptitle(title, fontsize=9)
    fig.tight_layout()
    fig.savefig(out, dpi=120)
    plt.close(fig)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("gcode", help="sliced .3mf (Bambu print job) or .gcode")
    ap.add_argument("--out", required=True, help="output prefix")
    ap.add_argument("--title", default="")
    ap.add_argument("--zsel", default="0.4,2,4,6,8,10,12,20,40,60,84,100")
    ap.add_argument("--pitch-z", default="14,70", help="z range (mm) of the straight flighted section")
    a = ap.parse_args()
    S, feat = extrusion_segments(read_gcode(a.gcode))
    win = (9.0, 11.5)
    R, Sc, centre = profile(S, feat, win)
    zlo, zhi = (float(v) for v in a.pitch_z.split(","))
    pitch, hand = flight_pitch(R, zlo, zhi)
    teeth, gear = gear_teeth(Sc, R, win)
    np.savetxt(a.out + "_profile.csv", R[:, :5], fmt="%.3f", delimiter=",",
               header="z_mm,bore_r_mm,core_r_mm,outer_r_mm,max_r_any_mm", comments="")
    summary = {"layers": int(len(R)), "height_mm": float(R[:, 0].max()), "flight_pitch_mm": round(pitch, 2),
               "flight_hand": hand, "gear_teeth": teeth,
               "gear_z_mm": gear[:2] if gear else None, "gear_tip_r_mm": gear[2] if gear else None}
    for zz in (0.4, 1, 2, 4, 6, 8, 10, 12, 20, 40, 60):
        i = int(np.argmin(np.abs(R[:, 0] - zz)))
        summary[f"z{zz:g}"] = {"bore_r": round(float(R[i, 1]), 2), "core_r": round(float(R[i, 2]), 2)}
    with open(a.out + "_summary.json", "w") as f:
        json.dump(summary, f, indent=1)
    print(json.dumps(summary, indent=1))
    section_figure(Sc, [float(v) for v in a.zsel.split(",")],
                   a.title or "G-code toolpaths, exit plane at z = 0", a.out + "_sections.png")
