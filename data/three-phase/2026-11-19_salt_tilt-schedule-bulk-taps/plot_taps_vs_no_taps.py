#!/usr/bin/env python3
"""New auger tube, 2026-11-19: salt flow with and without taps (PR #131).

Panel A: mass in the beaker against time since the bulk started, for every
trial on the new tube: the four tap-free trials (script 2026-11-19a) and the
five with taps (2026-11-19b/c).
Panel B: salt per auger revolution in every stretch at one plate angle
while the auger spun, against how much salt had already come out of the
new tube (the balance was 0.0000 g with the empty beaker at 19:45 UTC, so
the absolute reading is the running total).  The 0 deg priming spins and
the per-angle probe/check steps are included.

Writes flow_segments.csv and taps_vs_no_taps.png next to this script.
usage: python plot_taps_vs_no_taps.py
"""
import csv
import glob
import os
import statistics

HERE = os.path.dirname(os.path.abspath(__file__))
OLD = os.path.join(HERE, "..", "2026-11-19_salt_tilt-schedule-new-auger")
NO_TAPS = "#eb6834"      # categorical slot 2 (orange)
TAPS = "#2a78d6"         # categorical slot 1 (blue)
INK, INK2, SURFACE = "#0b0b0b", "#52514e", "#fcfcfb"
FLOOR = 0.1              # mg/rev: log-axis floor; smaller values sit on it
MIN_SEG_S = 1.5


def rows(path):
    return list(csv.DictReader(open(path)))


def fnum(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def trial_files():
    out = []
    for d, cond in ((os.path.join(OLD, "launch1_1947Z"), "no taps"),
                    (os.path.join(OLD, "launch2_1953Z"), "no taps"),
                    (os.path.join(HERE, "launch1_2041Z"), "taps (bulk)"),
                    (os.path.join(HERE, "launch2_2052Z"), "taps (bulk + fine)")):
        for p in sorted(glob.glob(os.path.join(d, "trial_*.csv"))):
            out.append((p, cond, os.path.basename(d)))
    return out


def segments(path, cond, launch):
    rs = [r for r in rows(path) if fnum(r["mass_abs_g"]) is not None]
    segs, cur = [], None
    for r in rs:
        rpm = fnum(r["auger_rpm"]) or 0.0
        key = (r["stage"], r["tilt_deg"]) if (
            rpm > 0 and r["stage"] in ("bulk", "fine")) else None
        if cur is not None and key != cur["key"]:
            segs.append(cur)
            cur = None
        if key is not None:
            if cur is None:
                cur = {"key": key, "rows": []}
            cur["rows"].append(r)
    if cur is not None:
        segs.append(cur)
    out = []
    for s in segs:
        rr = s["rows"]
        t0, t1 = float(rr[0]["t_s"]), float(rr[-1]["t_s"])
        if t1 - t0 < MIN_SEG_S or len(rr) < 6:
            continue
        m0 = statistics.median(float(r["mass_abs_g"]) for r in rr[:3])
        m1 = statistics.median(float(r["mass_abs_g"]) for r in rr[-3:])
        rpm = float(rr[0]["auger_rpm"])
        revs = rpm / 60.0 * (t1 - t0)
        taps = int(rr[-1]["taps_cum"]) - int(rr[0]["taps_cum"])
        out.append({"source": "trial", "launch": launch,
                    "file": os.path.basename(path),
                    # by what the stretch itself did: 2026-11-19b's fine
                    # stage spun without taps
                    "condition": "taps" if taps > 0 else "no taps",
                    "stage": s["key"][0], "tilt_deg": float(s["key"][1]),
                    "time_utc": rr[0]["time_utc"],
                    "out_of_tube_g": round(m0, 4), "spin_s": round(t1 - t0, 2),
                    "revs": round(revs, 2), "gain_mg": round(1000 * (m1 - m0), 1),
                    "taps": taps,
                    "mg_per_rev": round(1000 * (m1 - m0) / revs, 3)})
    return out


def probe_points():
    out = []
    p = os.path.join(OLD, "launch2_1953Z", "flow_probe_by_angle.csv")
    rs = rows(p)
    names = []
    for r in rs:
        if r["step"].startswith("spin") and r["step"] not in names:
            names.append(r["step"])
    for name in names:
        n = name[len("spin"):]                       # e.g. 55_1
        tilt = float(n.split("_")[0])
        before = [float(r["mass_abs_g"]) for r in rs
                  if r["step"] == "tilt" + n and r["mass_abs_g"]]
        after = [float(r["mass_abs_g"]) for r in rs
                 if r["step"] == "settle" + n and r["mass_abs_g"]]
        spin = [r for r in rs if r["step"] == name]
        m0 = statistics.median(before[-6:])
        m1 = statistics.median(after[-8:])
        out.append({"source": "probe 11-19 19:52", "launch": "launch2_1953Z",
                    "file": "flow_probe_by_angle.csv", "condition": "no taps",
                    "stage": "probe", "tilt_deg": tilt,
                    "time_utc": spin[0]["time_utc"],
                    "out_of_tube_g": round(m0, 4), "spin_s": 3.0, "revs": 2.75,
                    "gain_mg": round(1000 * (m1 - m0), 1), "taps": 0,
                    "mg_per_rev": round(1000 * (m1 - m0) / 2.75, 3)})
    # 0 deg priming spin, 11-19 19:52 (no taps): numbers from that README
    # (+0.147 g in 22.5 revs; the spin's own log ended in a MemoryError)
    out.append({"source": "prime 11-19 19:52", "launch": "launch2_1953Z",
                "file": "prime_spin_0deg.csv", "condition": "no taps",
                "stage": "prime", "tilt_deg": 0.0, "time_utc": "19:52:08",
                "out_of_tube_g": 0.169, "spin_s": 24.6, "revs": 22.5,
                "gain_mg": 147.0, "taps": 0, "mg_per_rev": round(147.0 / 22.5, 3)})
    for r in rows(os.path.join(HERE, "primecheck_2111Z", "prime_check_steps.csv")):
        taps = int(r["taps"])
        out.append({"source": "check 11-19 21:11", "launch": "primecheck_2111Z",
                    "file": "prime_check_steps.csv",
                    "condition": "taps (check)" if taps else "no taps",
                    "stage": "prime" if r["step"].startswith("prime") else "probe",
                    "tilt_deg": float(r["tilt_deg"]), "time_utc": "",
                    "out_of_tube_g": float(r["m0_abs_g"]),
                    "spin_s": float(r["spin_s"]), "revs": float(r["revs"]),
                    "gain_mg": float(r["gain_mg"]), "taps": taps,
                    "mg_per_rev": float(r["mg_per_rev"])})
    return out


def main():
    segs = []
    traces = []
    for p, cond, launch in trial_files():
        segs += segments(p, cond, launch)
        rs = [r for r in rows(p) if fnum(r["mass_g"]) is not None]
        tb = next((float(r["t_s"]) for r in rs if r["stage"] == "bulk"), None)
        if tb is None:
            continue
        traces.append((cond, launch, os.path.basename(p),
                       [float(r["t_s"]) - tb for r in rs if float(r["t_s"]) >= tb],
                       [float(r["mass_g"]) for r in rs if float(r["t_s"]) >= tb]))
    segs += probe_points()
    keys = ["source", "launch", "file", "condition", "stage", "tilt_deg",
            "time_utc", "out_of_tube_g", "spin_s", "revs", "gain_mg", "taps",
            "mg_per_rev"]
    with open(os.path.join(HERE, "flow_segments.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["powder_id"] + keys)
        w.writeheader()
        for s in segs:
            w.writerow(dict(powder_id="salt", **{k: s[k] for k in keys}))

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.size": 10, "axes.edgecolor": INK2,
                         "axes.labelcolor": INK, "xtick.color": INK2,
                         "ytick.color": INK2, "axes.spines.top": False,
                         "axes.spines.right": False})
    fig, (a, b) = plt.subplots(1, 2, figsize=(13, 5.4), facecolor=SURFACE)
    for ax in (a, b):
        ax.set_facecolor(SURFACE)
        ax.grid(True, color="#e4e3df", linewidth=0.8)
        ax.set_axisbelow(True)

    # A: mass vs time since the bulk started
    n_tap = 0
    for cond, launch, name, ts, ms in traces:
        tapped = cond.startswith("taps")
        a.plot(ts, ms, color=TAPS if tapped else NO_TAPS, linewidth=2,
               alpha=1.0 if tapped else 0.85)
        if tapped:
            n_tap += 1
            a.annotate("{}".format(n_tap), (ts[-1], ms[-1]),
                       xytext=(4, 0), textcoords="offset points",
                       color=INK, fontsize=9, va="center")
    a.axhline(1.0, color=INK2, linewidth=1, linestyle=(0, (4, 3)))
    a.text(610, 1.02, "target 1 g", color=INK2, fontsize=9, ha="right")
    a.set_xlabel("time since the bulk started (s)")
    a.set_ylabel("salt in the beaker this trial (g)")
    a.set_title("A. Each trial on the new tube", loc="left", color=INK,
                fontsize=11)
    a.plot([], [], color=NO_TAPS, linewidth=2,
           label="no taps (19:47-19:55, 4 trials)")
    a.plot([], [], color=TAPS, linewidth=2,
           label="with taps (20:41-21:09), numbered in run order")
    a.legend(loc="upper left", frameon=False, fontsize=9,
             bbox_to_anchor=(0.0, 0.88))
    a.set_ylim(-0.05, 1.1)

    # B: mg per auger rev vs salt already out of the tube
    def pts(sel):
        xs = [s["out_of_tube_g"] for s in sel]
        ys = [max(FLOOR, s["mg_per_rev"]) for s in sel]
        return xs, ys
    groups = [
        ("no taps: trial stretches at one angle", lambda s: s["condition"] == "no taps" and s["source"] == "trial", "o", NO_TAPS, False),
        ("no taps: 2.75-rev probe / 10 s check steps", lambda s: s["condition"] == "no taps" and s["stage"] == "probe", "D", NO_TAPS, False),
        ("no taps: 0° priming spin", lambda s: s["condition"] == "no taps" and s["stage"] == "prime", "s", NO_TAPS, False),
        ("taps: trial stretches at one angle", lambda s: s["condition"].startswith("taps") and s["source"] == "trial", "o", TAPS, True),
        ("taps: 10 s check step at 45°", lambda s: s["condition"] == "taps (check)" and s["stage"] == "probe", "D", TAPS, True),
        ("taps: 0° priming spin", lambda s: s["condition"] == "taps (check)" and s["stage"] == "prime", "s", TAPS, True),
    ]
    for label, f, mk, col, filled in groups:
        sel = [s for s in segs if f(s)]
        if not sel:
            continue
        xs, ys = pts(sel)
        b.scatter(xs, ys, s=46 if mk != "s" else 70, marker=mk,
                  facecolors=col if filled else SURFACE, edgecolors=col,
                  linewidths=2 if not filled else 1.2, label=label, zorder=3)
    b.set_yscale("log")
    b.set_ylim(FLOOR * 0.8, 200)
    b.axhline(FLOOR, color=INK2, linewidth=0.8, linestyle=(0, (2, 3)))
    b.text(3.32, FLOOR * 1.08, "< 0.1 mg/rev\nsits on this line",
           color=INK2, fontsize=8, ha="right", va="bottom")
    b.set_xlim(-0.05, 3.35)
    b.set_xlabel("salt already out of the new tube (g)")
    b.set_ylabel("salt per auger revolution (mg, log scale)")
    b.set_title("B. Taps raised the flow at first; it fell to ~0 by 3.1 g out",
                loc="left", color=INK, fontsize=11)
    b.legend(loc="upper right", frameon=False, fontsize=8)
    fig.tight_layout()
    out = os.path.join(HERE, "taps_vs_no_taps.png")
    fig.savefig(out, dpi=150, facecolor=SURFACE)
    print("wrote", out, "segments", len(segs))


if __name__ == "__main__":
    main()
