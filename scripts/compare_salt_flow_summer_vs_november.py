"""Why do the November stepped-tilt salt trials stall when summer runs at the same
angles did not?  Compares, from data already on this branch:

  A. salt delivered per auger revolution vs plate angle, summer vs November
  B. the longest stretch without a 2 mg gain while the auger spun, per trial,
     i.e. whether the November trials' stock stall rule (no 2 mg gain in 8 s)
     would ever have fired on the summer runs.

Run from the repo root:  python scripts/compare_salt_flow_summer_vs_november.py
"""
import collections, csv, glob, math, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = "data/three-phase/2026-11-19_why-stalls"
SUMMER, NOV = "#2a78d6", "#eb6834"          # validated categorical slots 1-2
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
GAIN_G, STALL_S = 0.002, 8.0                # stock bulk stall rule (phase 1)


def longest_dry(ts, ms, gain=GAIN_G):
    """Longest time the mass went without rising `gain` above its last reference."""
    t_ref = m_ref = None
    worst = 0.0
    for t, m in zip(ts, ms):
        if m is None or math.isnan(m):
            continue
        if t_ref is None or m - m_ref >= gain:
            t_ref, m_ref = t, m
        worst = max(worst, t - t_ref)
    return worst


rows = []   # era, session, kind, angle, rpm, mg_per_rev, longest_dry_s, note

# --- summer 1: 2026-07-31 wide-angle tap session, the 1-rev re-feed at 30 rpm (auger only)
for r in csv.DictReader(open("data/tap-characterization/2026-07-31_salt_angles/trials_summary.csv")):
    rows.append(("summer", "2026-07-31", "1 rev, auger only", float(r["angle_plate_deg"]), 30,
                 float(r["prime_mg_per_rev"]), "", "53 g salt in tube (weighed)"))

# --- summer 2: 2026-08-12/13 afterflow battery (C6 taps+auger, C7/C8 auger only, B4/B5 6 s runs)
meta, by = {}, collections.defaultdict(lambda: ([], []))
for line in open("data/afterflow/2026-08-12_salt/afterflow_battery_salt.log"):
    if line.startswith("E,") and "=== trial" in line:
        p = line.split("=== trial")[1].split()
        meta[int(p[0])] = (p[2], float(p[4]), float(p[8]), p[12])   # test, tilt, rpm, mode
    elif line.startswith("D,"):
        f = line.strip().split(",")
        if f[3] == "dispense":
            by[int(f[2])][0].append(int(f[1]) / 1000.0)
            by[int(f[2])][1].append(float(f[4]))
for tr, (ts, ms) in sorted(by.items()):
    if tr not in meta:
        continue
    test, tilt, rpm, mode = meta[tr]
    good = [m for m in ms if not math.isnan(m)]
    revs = (ts[-1] - ts[0]) * rpm / 60.0
    mpr = (good[-1] - good[0]) * 1000.0 / revs if revs > 0 and good else float("nan")
    kind = "auger only" if mode in ("auger", "cont") else "auger + taps"
    rows.append(("summer", "2026-08-12/13", "{} {}".format(test, kind), tilt, rpm, mpr,
                 longest_dry(ts, ms), "71 g at session start (weighed), about 30-50 g by C7"))

# --- summer 3: 2026-08-17 KF bang-bang, auger only at 55 deg (55/90 rpm)
by = collections.defaultdict(lambda: ([], [], []))
for r in csv.DictReader(open("data/kf-bangbang/2026-08-17_salt/samples.csv")):
    try:
        rpm, m = float(r["rpm"] or 0), float(r["mass"])
    except ValueError:
        continue
    if rpm > 0 and not math.isnan(m):
        k = (r["pass"], int(r["trial"]))
        by[k][0].append(int(r["t_ms"]) / 1000.0); by[k][1].append(m); by[k][2].append(rpm)
for k, (ts, ms, rp) in sorted(by.items()):
    revs = (ts[-1] - ts[0]) * rp[0] / 60.0
    mpr = (ms[-1] - ms[0]) * 1000.0 / revs if revs >= 2 else float("nan")
    rows.append(("summer", "2026-08-17", "KF stop, auger only", 55.0, rp[0], mpr,
                 longest_dry(ts, ms), "tube likely refilled, not weighed"))

# --- November: the 12 stepped-tilt trials, bulk stage split by commanded angle
for f in sorted(glob.glob("data/three-phase/2026-11-1*_salt_tilt-schedule*/launch*/trial_*.csv")):
    sess = f.split("three-phase/")[1].split("/")[0]
    tube = "new tube" if "new-auger" in sess else "old tube"
    day = sess[:10]
    if "50-30" in sess:
        day += " pm"
    elif sess.startswith("2026-11-18"):
        day += " am"
    ts, ms, seg = [], [], collections.OrderedDict()
    for r in csv.DictReader(open(f)):
        if r["stage"] != "bulk":
            continue
        t, m, a = float(r["t_s"]), float(r["mass_abs_g"]), float(r["tilt_deg"])
        ts.append(t); ms.append(m)
        seg.setdefault(a, []).append((t, m))
    rows.append(("november", day, "trial ({}), whole bulk".format(tube), float("nan"), 55,
                 float("nan"), longest_dry(ts, ms), os.path.basename(f)))
    for a, pts in seg.items():
        revs = (pts[-1][0] - pts[0][0]) * 55 / 60.0
        if revs >= 1.5:
            rows.append(("november", day, "trial bulk at one angle ({})".format(tube), a, 55,
                         (pts[-1][1] - pts[0][1]) * 1000.0 / revs, "", os.path.basename(f)))

# --- November probes (2.75 rev at 55 rpm per angle) and 0 deg priming spins, from the READMEs
probes = [
    ("2026-11-18 am", "old tube", {55: 42, 50: 26, 45: 60, 40: 103, 35: 93, 30: 90}, [112, -11], (542, 36.7)),
    ("2026-11-18 pm", "old tube", {30: 9.2}, [], (1.6, 36.7)),
    ("2026-11-19", "new tube", {55: 15.0, 50: 14.0, 45: 4.0, 40: 3.7, 35: 12.2, 30: 13.5}, [1.9, 1.1], (147, 22.5)),
]
for day, tube, d, at60, (pmg, prev) in probes:
    for a, mg in d.items():
        rows.append(("november", day, "probe 2.75 rev ({})".format(tube), float(a), 55, mg / 2.75, "", "README"))
    for mg in at60:
        rows.append(("november", day, "probe 2.75 rev ({})".format(tube), 60.0, 55, mg / 2.75, "", "README"))
    rows.append(("november", day, "0 deg priming spin ({})".format(tube), 0.0, 55, pmg / prev, "", "README"))

os.makedirs(OUT, exist_ok=True)
with open(os.path.join(OUT, "flow_then_vs_now.csv"), "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["era", "session", "kind", "plate_deg", "auger_rpm", "mg_per_rev",
                "longest_no_2mg_gain_s", "note"])
    for r in rows:
        w.writerow([r[0], r[1], r[2], "" if isinstance(r[3], float) and math.isnan(r[3]) else r[3], r[4],
                    "" if isinstance(r[5], float) and math.isnan(r[5]) else round(r[5], 2),
                    "" if r[6] == "" else round(r[6], 2), r[7]])

# ------------------------------------------------------------------ figure
plt.rcParams.update({"font.size": 10, "axes.edgecolor": INK2, "axes.labelcolor": INK,
                     "xtick.color": INK2, "ytick.color": INK2, "axes.titlecolor": INK})
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.5, 6.2), gridspec_kw={"width_ratios": [1.6, 1]})
fig.patch.set_facecolor("#fcfcfb")
for ax in (ax1, ax2):
    ax.set_facecolor("#fcfcfb")
    ax.grid(True, color=GRID, lw=0.8); ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)

marks = {  # (era, kind prefix) -> marker
    ("summer", "1 rev"): ("o", "07-31: 1 rev at 30 rpm, auger only (53 g in tube)"),
    ("summer", "C7"): ("s", "08-12/13: 55 rpm, auger only (C7/C8/B4/B5)"),
    ("summer", "C8 auger"): ("s", None), ("summer", "B4"): ("s", None), ("summer", "B5"): ("s", None),
    ("summer", "KF"): ("^", "08-17: 55-90 rpm, auger only (KF stop runs)"),
    ("november", "probe"): ("D", "Nov: 2.75-rev probe right after a tilt move"),
    ("november", "0 deg"): ("P", "Nov: 0° priming spin"),
    ("november", "trial bulk"): ("v", "Nov: trial bulk, per angle (stall-limited)"),
}
seen = set()
for r in rows:
    era, sess, kind, a, rpm, mpr = r[:6]
    if isinstance(a, float) and math.isnan(a) or math.isnan(mpr):
        continue
    key = next((k for k in marks if k[0] == era and kind.startswith(k[1])), None)
    if key is None:
        continue          # skip C6/C8 tap-while-rotating rows: November's bulk had no taps
    mk, lab = marks[key]
    col = SUMMER if era == "summer" else NOV
    hollow = era == "november" and "new tube" in kind
    ax1.scatter([a], [max(mpr, 0)], s=46, marker=mk, facecolor="#fcfcfb" if hollow else col,
                edgecolor=col, lw=1.4, zorder=3,
                label=lab if lab and lab not in seen else None)
    if lab:
        seen.add(lab)
ax1.scatter([], [], s=46, marker="D", facecolor="#fcfcfb", edgecolor=NOV, lw=1.4, label="hollow = new tube (11-19)")
ax1.set_xlabel("plate angle (°)")
ax1.set_ylabel("salt per auger revolution (mg)")
ax1.set_title("A. Same angles, far less salt per turn in November", loc="left", fontsize=11)
ax1.set_xlim(-4, 74)
ax1.set_ylim(-5, None)
ax1.legend(frameon=False, fontsize=8.5, loc="upper center", bbox_to_anchor=(0.5, -0.13), ncol=2, labelcolor=INK)

# panel B
import random
random.seed(1)
sd = [r[6] for r in rows if r[0] == "summer" and r[6] != ""]
nd = [r[6] for r in rows if r[0] == "november" and r[6] != ""]
ax2.scatter([0 + random.uniform(-0.18, 0.18) for _ in sd], sd, s=22, color=SUMMER, edgecolor="#fcfcfb", lw=0.6, zorder=3)
ax2.scatter([1 + random.uniform(-0.18, 0.18) for _ in nd], nd, s=30, color=NOV, edgecolor="#fcfcfb", lw=0.6, zorder=3)
ax2.axhline(STALL_S, color=INK2, lw=1.2, ls=(0, (4, 3)))
ax2.text(0.5, STALL_S + 0.25, "stall rule fires at 8 s", ha="center", va="bottom", color=INK2, fontsize=9)
ax2.set_xticks([0, 1])
ax2.set_xticklabels(["Summer\n40–70°, 55–90 rpm\n{} trials".format(len(sd)),
                     "November\n40–60°, 55 rpm\n{} trials".format(len(nd))])
ax2.set_xlim(-0.6, 1.6)
ax2.set_ylim(0, 11)
ax2.set_ylabel("longest stretch with < 2 mg gain\nwhile the auger spun (s)")
ax2.set_title("B. Summer flow never paused for 8 s", loc="left", fontsize=11)
ax2.text(0, max(sd) + 0.5, "max {:.1f} s".format(max(sd)), ha="center", color=INK, fontsize=9)
ax2.text(1, 9.9, "each trial ends when\nthe rule fires", ha="center", color=INK, fontsize=9)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "flow_then_vs_now.png"), dpi=150, facecolor=fig.get_facecolor())
print("summer trials:", len(sd), "max dry %.2f s" % max(sd), "| november trials:", len(nd),
      "dry range %.1f-%.1f s" % (min(nd), max(nd)))
