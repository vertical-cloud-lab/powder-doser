#!/usr/bin/env python3
"""Analyze the low-rpm stop battery + quantum-vs-tilt battery (PR #131,
2026-08-17).

Parses the CSV-over-stdout telemetry from
``hardware/test-module/firmware/lowrpm_quantum.py`` and produces:

  Test D  -- low-rpm stop battery.  afterflow (settled - m_halt) vs auger
             rpm and vs the fitted flow-at-halt, with an OLS
             ``afterflow = AF0 + tau * flow`` per tilt.  The question is
             whether AF0 is a real speed-independent intercept that stays
             flat below 15 rpm, or whether it was an artifact of
             extrapolating a 15-75 rpm fit.
  Test D2 -- the same battery at a second tilt: does AF0 scale with tilt
             (lip charge) rather than being a constant?
  Test Q  -- quantum vs tilt at trim speed.  Per-increment yield for 20 deg
             increments weighed at rest, at 3 tilts: mg/deg, its scatter,
             and the phase structure.
  Flow checks -- 1-revolution matched-revolution yield before each block,
             used as a fill / stationarity index (drawdown control).

Usage:  python scripts/analyze_lowrpm_quantum.py <log> <outdir>
"""
import sys
import os
import csv

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

NAN = float("nan")


def fv(x):
    try:
        return NAN if x == "nan" else float(x)
    except ValueError:
        return NAN


def parse(path):
    meta = {}
    S, Q, F, D = [], [], [], []
    with open(path) as f:
        for line in f:
            p = line.rstrip("\n").split(",")
            if not p:
                continue
            k = p[0]
            try:
                if k == "M" and len(p) >= 3:
                    meta[p[1]] = p[2]
                elif k == "S" and len(p) >= 18:
                    S.append(dict(
                        trial=int(p[1]), test=p[2], block=int(p[3]),
                        tilt=float(p[4]), rep=int(p[5]), rpm=float(p[6]),
                        cruise=int(p[7]), phase_cmd=float(p[8]),
                        rev_tot=fv(p[9]), m_base=fv(p[10]), m_halt=fv(p[11]),
                        t_move=fv(p[12]), m_set=fv(p[13]), after=fv(p[14]),
                        disp=fv(p[15]), absm=fv(p[16]), verdict=p[17]))
                elif k == "Q" and len(p) >= 14:
                    Q.append(dict(
                        trial=int(p[1]), scan=int(p[2]), incr=int(p[3]),
                        tilt=float(p[4]), rpm=float(p[5]),
                        incr_deg=float(p[6]), cum_deg=float(p[7]),
                        phase_deg=float(p[8]), rev=fv(p[9]),
                        m_before=fv(p[10]), m_after=fv(p[11]),
                        yld=fv(p[12]), stab=p[13]))
                elif k == "F" and len(p) >= 9:
                    F.append(dict(block=int(p[1]), label=p[2],
                                  tilt=float(p[3]), rpm=float(p[4]),
                                  revs=int(p[5]), m0=fv(p[6]), m1=fv(p[7]),
                                  yld=fv(p[8])))
                elif k == "D" and len(p) >= 9:
                    D.append(dict(t=int(p[1]), trial=int(p[2]), phase=p[3],
                                  mass=fv(p[4]), stab=p[5], rpm=float(p[6]),
                                  rev=fv(p[7]), phase_deg=fv(p[8])))
            except (ValueError, IndexError):
                continue
    return meta, S, Q, F, D


# ---------- small stats helpers (no numpy on purpose: matches repo style) --
def mean(xs):
    xs = [x for x in xs if x == x]
    return sum(xs) / len(xs) if xs else NAN


def sd(xs):
    xs = [x for x in xs if x == x]
    if len(xs) < 2:
        return NAN
    m = sum(xs) / len(xs)
    return (sum((x - m) ** 2 for x in xs) / (len(xs) - 1)) ** 0.5


def sem(xs):
    xs = [x for x in xs if x == x]
    return sd(xs) / len(xs) ** 0.5 if len(xs) >= 2 else NAN


def ols(xs, ys):
    """y = a + b x.  Returns (a, b, se_a, se_b, r2, n)."""
    pts = [(x, y) for x, y in zip(xs, ys) if x == x and y == y]
    n = len(pts)
    if n < 3:
        return (NAN,) * 5 + (n,)
    mx = sum(p[0] for p in pts) / n
    my = sum(p[1] for p in pts) / n
    sxx = sum((p[0] - mx) ** 2 for p in pts)
    if sxx <= 0:
        return (NAN,) * 5 + (n,)
    b = sum((p[0] - mx) * (p[1] - my) for p in pts) / sxx
    a = my - b * mx
    resid = [p[1] - (a + b * p[0]) for p in pts]
    sse = sum(r * r for r in resid)
    sst = sum((p[1] - my) ** 2 for p in pts)
    s2 = sse / (n - 2)
    se_b = (s2 / sxx) ** 0.5
    se_a = (s2 * (1.0 / n + mx * mx / sxx)) ** 0.5
    r2 = 1.0 - sse / sst if sst > 0 else NAN
    return a, b, se_a, se_b, r2, n


def flow_at_halt(D, trial, frac=0.5):
    """OLS slope (g/s) of the streamed mass over the last `frac` of the
    cruise move for one trial -- the flow rate the auger was delivering when
    it was halted."""
    pts = [(d["t"] / 1000.0, d["mass"]) for d in D
           if d["trial"] == trial and d["phase"] == "move" and d["mass"] == d["mass"]]
    if len(pts) < 6:
        return NAN, 0
    t0, t1 = pts[0][0], pts[-1][0]
    cut = t1 - frac * (t1 - t0)
    use = [p for p in pts if p[0] >= cut]
    if len(use) < 5:
        use = pts
    _, b, _, _, _, n = ols([p[0] for p in use], [p[1] for p in use])
    return b, n


def main():
    log, outdir = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    meta, S, Q, F, D = parse(log)
    powder = meta.get("powder_id", "unknown")

    # ---------------- Test D / D2 -----------------------------------
    for s in S:
        s["flow"], s["nflow"] = flow_at_halt(D, s["trial"])
        s["after_mg"] = s["after"] * 1000.0
        s["ff_g_rev"] = s["disp"] / s["cruise"] if s["cruise"] else NAN

    with open(os.path.join(outdir, "stop_trials.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["powder_id", "trial", "test", "block", "tilt", "rep",
                    "rpm", "cruise_revs", "halt_phase_deg", "m_base",
                    "m_halt", "m_settled", "afterflow_mg", "dispensed_g",
                    "ff_g_per_rev", "flow_at_halt_g_per_s", "t_move_s",
                    "abs_mass_g", "verdict"])
        for s in S:
            w.writerow([powder, s["trial"], s["test"], s["block"],
                        "%.0f" % s["tilt"], s["rep"], "%.0f" % s["rpm"],
                        s["cruise"], "%.0f" % s["phase_cmd"],
                        "%.4f" % s["m_base"], "%.4f" % s["m_halt"],
                        "%.4f" % s["m_set"], "%.1f" % s["after_mg"],
                        "%.4f" % s["disp"], "%.4f" % s["ff_g_rev"],
                        "%.5f" % s["flow"], "%.2f" % s["t_move"],
                        "%.3f" % s["absm"], s["verdict"]])

    with open(os.path.join(outdir, "flow_checks.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["powder_id", "block", "label", "tilt", "rpm", "revs",
                    "m_before", "m_after", "yield_g_per_rev"])
        for r in F:
            w.writerow([powder, r["block"], r["label"], "%.0f" % r["tilt"],
                        "%.0f" % r["rpm"], r["revs"], "%.4f" % r["m0"],
                        "%.4f" % r["m1"], "%.4f" % (r["yld"] / r["revs"])])

    with open(os.path.join(outdir, "quantum.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["powder_id", "trial", "scan", "incr", "tilt", "rpm",
                    "incr_deg", "cum_deg", "phase_deg", "auger_rev",
                    "m_before", "m_after", "yield_mg", "mg_per_deg",
                    "stable"])
        for q in Q:
            w.writerow([powder, q["trial"], q["scan"], q["incr"],
                        "%.0f" % q["tilt"], "%.0f" % q["rpm"],
                        "%.0f" % q["incr_deg"], "%.0f" % q["cum_deg"],
                        "%.2f" % q["phase_deg"], "%.4f" % q["rev"],
                        "%.4f" % q["m_before"], "%.4f" % q["m_after"],
                        "%.1f" % (q["yld"] * 1000.0),
                        "%.3f" % (q["yld"] * 1000.0 / q["incr_deg"]),
                        q["stab"]])

    # ---- summaries -------------------------------------------------
    tilts_S = sorted(set(s["tilt"] for s in S))
    lines = []
    lines.append("# Low-rpm stop battery + quantum vs tilt -- %s" % powder)
    lines.append("")
    lines.append("## Flow checks (1 rev @ %s, fill/stationarity index)"
                 % meta.get("flow_check", "?"))
    lines.append("")
    lines.append("| block | label | g/rev |")
    lines.append("|---|---|---|")
    for r in F:
        lines.append("| %d | %s | %.4f |"
                     % (r["block"], r["label"], r["yld"] / r["revs"]))
    fy = [r["yld"] / r["revs"] for r in F]
    if len(fy) >= 2:
        lines.append("")
        lines.append("first %.4f -> last %.4f g/rev (ratio %.2f); "
                     "mean %.4f, sd %.4f (CV %.0f%%)"
                     % (fy[0], fy[-1], fy[-1] / fy[0] if fy[0] else NAN,
                        mean(fy), sd(fy), 100 * sd(fy) / mean(fy)))

    fits = {}
    for tilt in tilts_S:
        rows = [s for s in S if s["tilt"] == tilt]
        lines.append("")
        lines.append("## Stop battery at tilt %.0f deg (n=%d)"
                     % (tilt, len(rows)))
        lines.append("")
        lines.append("| rpm | n | afterflow mean +/- sem (mg) | sd (mg) | "
                     "flow at halt (g/s) | ff (g/rev) |")
        lines.append("|---|---|---|---|---|---|")
        for rpm in sorted(set(r["rpm"] for r in rows)):
            g = [r for r in rows if r["rpm"] == rpm]
            a = [r["after_mg"] for r in g]
            lines.append("| %.0f | %d | %.1f +/- %.1f | %.1f | %.4f | %.4f |"
                         % (rpm, len(g), mean(a), sem(a), sd(a),
                            mean([r["flow"] for r in g]),
                            mean([r["ff_g_rev"] for r in g])))
        a0, b, sa, sb, r2, n = ols([r["flow"] for r in rows],
                                   [r["after_mg"] for r in rows])
        fits[tilt] = (a0, b, sa, sb, r2, n)
        lines.append("")
        lines.append("OLS afterflow(mg) = AF0 + tau * flow(g/s):  "
                     "**AF0 = %.1f +/- %.1f mg**, tau = %.3f +/- %.3f s "
                     "(as mg per g/s: %.0f), R2 = %.2f, n = %d"
                     % (a0, sa, b / 1000.0, sb / 1000.0, b, r2, n))
        # low-rpm-only fit: is AF0 flat below 15 rpm?
        low = [r for r in rows if r["rpm"] <= 15.0]
        if len(low) >= 3:
            la, lb, lsa, lsb, lr2, ln = ols([r["flow"] for r in low],
                                            [r["after_mg"] for r in low])
            lines.append("")
            lines.append("restricted to rpm <= 15 (n=%d): AF0 = %.1f +/- "
                         "%.1f mg, tau = %.3f +/- %.3f s, R2 = %.2f"
                         % (ln, la, lsa, lb / 1000.0, lsb / 1000.0, lr2))
        slow = [r["after_mg"] for r in rows if r["rpm"] == min(
            r2_["rpm"] for r2_ in rows)]
        lines.append("")
        lines.append("slowest-rpm afterflow (the direct AF0 probe): "
                     "%.1f +/- %.1f mg (n=%d)"
                     % (mean(slow), sem(slow), len(slow)))

    if len(tilts_S) >= 2:
        lines.append("")
        lines.append("## Does AF0 scale with tilt?")
        lines.append("")
        lines.append("| tilt | AF0 (mg) | tau (s) | R2 | n |")
        lines.append("|---|---|---|---|---|")
        for tilt in tilts_S:
            a0, b, sa, sb, r2, n = fits[tilt]
            lines.append("| %.0f | %.1f +/- %.1f | %.3f +/- %.3f | %.2f | %d |"
                         % (tilt, a0, sa, b / 1000.0, sb / 1000.0, r2, n))

    # ---- Test Q ----
    tilts_Q = sorted(set(q["tilt"] for q in Q))
    lines.append("")
    lines.append("## Quantum vs tilt at trim speed (%s rpm, %s deg "
                 "increments, weighed at rest)"
                 % (meta.get("rpm_Q", "?"), meta.get("incr_deg_Q", "?")))
    lines.append("")
    lines.append("| tilt | n | mean yield (mg) | sd (mg) | CV | mg/deg | "
                 "sd mg/deg | min..max (mg) | implied g/rev |")
    lines.append("|---|---|---|---|---|---|---|---|---|")
    for tilt in tilts_Q:
        g = [q for q in Q if q["tilt"] == tilt]
        ys = [q["yld"] * 1000.0 for q in g]
        deg = g[0]["incr_deg"]
        lines.append("| %.0f | %d | %.2f | %.2f | %.0f%% | %.3f | %.3f | "
                     "%.1f..%.1f | %.4f |"
                     % (tilt, len(g), mean(ys), sd(ys),
                        100 * sd(ys) / mean(ys) if mean(ys) else NAN,
                        mean(ys) / deg, sd(ys) / deg, min(ys), max(ys),
                        mean(ys) * 360.0 / deg / 1000.0))

    # ---- diagnostics: is the increment scatter real, or a weighing artifact?
    lines.append("")
    lines.append("## Diagnostics -- is the per-increment scatter real powder?")
    lines.append("")
    lines.append("A yield is a DIFFERENCE of two consecutive weighs, so reading")
    lines.append("noise e appears as +e then -e: independent true yields give a")
    lines.append("lag-1 autocorrelation of 0, pure reading noise gives -0.5, and")
    lines.append("the sd of the sum of k consecutive increments grows as sqrt(k)")
    lines.append("only if the increments are independent.")
    lines.append("")
    lines.append("| tilt | n | lag-1 acf | sd(1 incr) | sd(sum of 18) | "
                 "sqrt(18)*sd if independent |")
    lines.append("|---|---|---|---|---|---|")
    for tilt in tilts_Q:
        per_scan = []
        for scan in sorted(set(q["scan"] for q in Q)):
            v = [q["yld"] * 1000.0 for q in
                 sorted([r for r in Q if r["tilt"] == tilt
                         and r["scan"] == scan], key=lambda r: r["incr"])]
            if len(v) > 3:
                per_scan.append(v)
        allv = [x for v in per_scan for x in v]
        m = mean(allv)
        num = sum(sum((v[i] - m) * (v[i + 1] - m) for i in range(len(v) - 1))
                  for v in per_scan)
        den = sum((x - m) ** 2 for x in allv)
        acf = num / den if den else NAN
        s1 = sd(allv)
        sums = [sum(v) for v in per_scan]
        lines.append("| %.0f | %d | %+.2f | %.1f mg | %.1f mg | %.1f mg |"
                     % (tilt, len(allv), acf, s1,
                        sd(sums) if len(sums) > 1 else NAN,
                        s1 * len(per_scan[0]) ** 0.5))

    # noise floor + consecutive-weigh agreement (no powder moved in between)
    noise = [d["mass"] for d in D if d["phase"] == "noise"]
    if len(noise) > 5:
        lines.append("")
        lines.append("Static noise stream (servo home, nothing actuating): "
                     "sd %.2f mg, p2p %.2f mg, n=%d"
                     % (sd(noise) * 1000, (max(noise) - min(noise)) * 1000,
                        len(noise)))
    base = {}
    setl = {}
    for d in []:
        pass
    Pl = []
    with open(log) as f:
        for line in f:
            p = line.rstrip("\n").split(",")
            if p[0] == "P" and len(p) >= 6 and p[4] != "nan":
                Pl.append((int(p[1]), int(p[2]), p[3], float(p[4])))
    for t, tr, kind, m in Pl:
        if kind == "base":
            base[tr] = (t, m)
        elif kind == "settled":
            setl[tr] = (t, m)
    gaps = []
    trs = sorted(setl)
    for i, tr in enumerate(trs[:-1]):
        nxt = trs[i + 1]
        if nxt in base and (base[nxt][0] - setl[tr][0]) / 1000.0 < 3.0:
            gaps.append((base[nxt][1] - setl[tr][1]) * 1000)
    if gaps:
        lines.append("")
        lines.append("Consecutive at-rest weighs with NO powder moved between "
                     "them (settled of trial N -> base of trial N+1, ~1.4 s "
                     "apart, servo re-tilt in between): mean %+.2f mg, sd "
                     "%.2f mg, p2p %.2f mg, n=%d -- the balance itself is "
                     "quiet." % (mean(gaps), sd(gaps),
                                 max(gaps) - min(gaps), len(gaps)))

    # afterflow decomposition: step at de-energise vs settling tail
    lines.append("")
    lines.append("## Afterflow decomposition (step at de-energise vs tail)")
    lines.append("")
    lines.append("| tilt | rpm | n | step at de-energise (mg) | settling tail "
                 "(mg) | total afterflow (mg) |")
    lines.append("|---|---|---|---|---|---|")
    for tilt in tilts_S:
        for rpm in sorted(set(s["rpm"] for s in S if s["tilt"] == tilt)):
            g = [s for s in S if s["tilt"] == tilt and s["rpm"] == rpm]
            steps, tails = [], []
            for s in g:
                mv = sorted([d for d in D if d["trial"] == s["trial"]
                             and d["phase"] == "move"], key=lambda d: d["t"])
                se = sorted([d for d in D if d["trial"] == s["trial"]
                             and d["phase"] == "settle"], key=lambda d: d["t"])
                if not mv or not se:
                    continue
                steps.append((se[0]["mass"] - mv[-1]["mass"]) * 1000)
                tails.append((s["m_set"] - se[0]["mass"]) * 1000)
            lines.append("| %.0f | %.0f | %d | %+.1f +/- %.1f | %+.1f +/- "
                         "%.1f | %+.1f +/- %.1f |"
                         % (tilt, rpm, len(g), mean(steps), sd(steps),
                            mean(tails), sd(tails),
                            mean([s["after_mg"] for s in g]),
                            sd([s["after_mg"] for s in g])))

    # flow vs rpm: is the auger metering by angle or by time?
    lines.append("")
    lines.append("## Is delivery angle-metered or time-metered?")
    lines.append("")
    lines.append("| tilt | rpm | n | flow = dispensed/t_move (g/s) | "
                 "ff = dispensed/rev (g/rev) |")
    lines.append("|---|---|---|---|---|")
    for tilt in tilts_S:
        rows = [s for s in S if s["tilt"] == tilt]
        for rpm in sorted(set(r["rpm"] for r in rows)):
            g = [r for r in rows if r["rpm"] == rpm]
            fl = [r["disp"] / r["t_move"] for r in g]
            lines.append("| %.0f | %.0f | %d | %.4f +/- %.4f | %.4f +/- %.4f |"
                         % (tilt, rpm, len(g), mean(fl), sd(fl),
                            mean([r["ff_g_rev"] for r in g]),
                            sd([r["ff_g_rev"] for r in g])))
        rpms = sorted(set(r["rpm"] for r in rows))
        fl_mu = [mean([r["disp"] / r["t_move"] for r in rows
                       if r["rpm"] == x]) for x in rpms]
        ff_mu = [mean([r["ff_g_rev"] for r in rows if r["rpm"] == x])
                 for x in rpms]
        _, sl, _, sse, _, _ = ols(rpms, fl_mu)
        lines.append("")
        lines.append("tilt %.0f: across a %.0fx rpm range the per-rpm MEAN "
                     "flow spans only %.2fx (%.4f-%.4f g/s, OLS slope %.5f "
                     "+/- %.5f g/s per rpm) while mean g/rev spans %.2fx "
                     "(%.4f-%.4f, ~1/rpm) -- delivery is set by auger-ON "
                     "TIME, not by angle."
                     % (tilt, max(rpms) / min(rpms),
                        max(fl_mu) / min(fl_mu), min(fl_mu), max(fl_mu),
                        sl, sse, max(ff_mu) / min(ff_mu), min(ff_mu),
                        max(ff_mu)))

    with open(os.path.join(outdir, "summary.md"), "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))

    # ---------------- figures ---------------------------------------
    colors = {}
    palette = ["#2b6cb0", "#c05621", "#2f855a", "#6b46c1"]
    for i, t in enumerate(sorted(set(tilts_S) | set(tilts_Q))):
        colors[t] = palette[i % len(palette)]

    # Figure 1: Test D
    fig, ax = plt.subplots(2, 2, figsize=(13, 9))
    a = ax[0][0]
    for tilt in tilts_S:
        rows = [s for s in S if s["tilt"] == tilt]
        a.scatter([r["rpm"] for r in rows], [r["after_mg"] for r in rows],
                  s=22, alpha=.45, color=colors[tilt])
        rpms = sorted(set(r["rpm"] for r in rows))
        mu = [mean([r["after_mg"] for r in rows if r["rpm"] == x])
              for x in rpms]
        er = [sem([r["after_mg"] for r in rows if r["rpm"] == x])
              for x in rpms]
        a.errorbar(rpms, mu, yerr=er, marker="o", lw=2, capsize=4,
                   color=colors[tilt], label="tilt %.0f deg" % tilt)
    a.set_xlabel("auger rpm")
    a.set_ylabel("afterflow (mg)")
    a.set_title("Afterflow vs auger rpm\n(phase-locked halt, %s rev cruise, "
                "auger-only)" % meta.get("cruise_revs_D", "?"))
    a.grid(alpha=.3)
    a.legend()

    a = ax[0][1]
    for tilt in tilts_S:
        rows = [s for s in S if s["tilt"] == tilt]
        a.scatter([r["flow"] for r in rows], [r["after_mg"] for r in rows],
                  s=26, alpha=.6, color=colors[tilt],
                  label="tilt %.0f deg" % tilt)
        a0, b, sa, sb, r2, n = fits[tilt]
        xs = [x / 100.0 for x in range(0, 101)]
        xmax = max([r["flow"] for r in rows if r["flow"] == r["flow"]] or [0])
        xs = [x * xmax * 1.05 for x in [i / 50.0 for i in range(51)]]
        a.plot(xs, [a0 + b * x for x in xs], "--", color=colors[tilt], lw=1.6)
        a.plot([0], [a0], marker="*", ms=15, color=colors[tilt])
        a.annotate("AF0 = %.1f mg" % a0, (0, a0),
                   textcoords="offset points", xytext=(8, 6),
                   color=colors[tilt], fontsize=9)
    a.axhline(14.7, color="grey", ls=":", lw=1.2)
    a.annotate("C7 extrapolated AF0 = 14.7 mg", (0, 14.7),
               textcoords="offset points", xytext=(10, -14),
               color="grey", fontsize=8)
    a.set_xlabel("flow at halt (g/s, fitted from the cruise stream)")
    a.set_ylabel("afterflow (mg)")
    a.set_title("Afterflow vs flow -- the intercept IS AF0")
    a.grid(alpha=.3)
    a.legend()

    a = ax[1][0]
    a.plot(range(1, len(F) + 1), [r["yld"] / r["revs"] for r in F],
           marker="s", color="#2f855a")
    a.set_xticks(range(1, len(F) + 1))
    a.set_xticklabels([r["label"].replace("_", "\n") for r in F], fontsize=7)
    a.set_xlabel("flow check (in session order)")
    a.set_ylabel("g per revolution")
    a.set_title("Fill / stationarity index\n(matched 1-rev yield between "
                "blocks)")
    a.grid(alpha=.3)

    a = ax[1][1]
    for tilt in tilts_S:
        rows = [s for s in S if s["tilt"] == tilt]
        rpms = sorted(set(r["rpm"] for r in rows))
        a.errorbar(rpms,
                   [mean([r["flow"] for r in rows if r["rpm"] == x])
                    for x in rpms],
                   yerr=[sem([r["flow"] for r in rows if r["rpm"] == x])
                         for x in rpms],
                   marker="o", capsize=4, color=colors[tilt],
                   label="tilt %.0f deg" % tilt)
    a.set_xlabel("auger rpm")
    a.set_ylabel("flow at halt (g/s)")
    a.set_title("Delivered flow vs commanded rpm")
    a.grid(alpha=.3)
    a.legend()
    fig.suptitle("Test D -- low-rpm stop battery (%s), matched fill by "
                 "design" % powder, fontsize=13)
    fig.tight_layout(rect=(0, 0, 1, .96))
    fig.savefig(os.path.join(outdir, "lowrpm_afterflow.png"), dpi=140)
    plt.close(fig)

    # Figure 2: Test Q
    fig, ax = plt.subplots(2, 2, figsize=(13, 9))
    a = ax[0][0]
    for tilt in tilts_Q:
        g = sorted([q for q in Q if q["tilt"] == tilt],
                   key=lambda r: (r["scan"], r["incr"]))
        a.plot(range(1, len(g) + 1), [q["yld"] * 1000.0 for q in g],
               marker="o", ms=3, lw=1, color=colors[tilt],
               label="tilt %.0f deg" % tilt)
    a.axhline(0, color="k", lw=.8)
    a.set_xlabel("increment # (scan 1 then scan 2)")
    a.set_ylabel("yield per %s deg increment (mg)" % meta.get("incr_deg_Q", ""))
    a.set_title("Per-increment yield at trim speed (%s rpm), weighed at rest"
                % meta.get("rpm_Q", "?"))
    a.grid(alpha=.3)
    a.legend()

    a = ax[0][1]
    data = [[q["yld"] * 1000.0 for q in Q if q["tilt"] == t] for t in tilts_Q]
    try:
        bp = a.boxplot(data, tick_labels=["%.0f" % t for t in tilts_Q],
                       showmeans=True, patch_artist=True)
    except TypeError:      # matplotlib < 3.9
        bp = a.boxplot(data, labels=["%.0f" % t for t in tilts_Q],
                       showmeans=True, patch_artist=True)
    for patch, t in zip(bp["boxes"], tilts_Q):
        patch.set_facecolor(colors[t])
        patch.set_alpha(.35)
    a.set_xlabel("tilt (plate deg)")
    a.set_ylabel("yield per increment (mg)")
    a.set_title("Quantum distribution -- this is what sizes the increment")
    a.grid(alpha=.3)

    a = ax[1][0]
    mu = [mean([q["yld"] * 1000.0 / q["incr_deg"] for q in Q
                if q["tilt"] == t]) for t in tilts_Q]
    sg = [sd([q["yld"] * 1000.0 / q["incr_deg"] for q in Q
              if q["tilt"] == t]) for t in tilts_Q]
    a.errorbar(tilts_Q, mu, yerr=sg, marker="o", lw=2, capsize=5,
               color="#2b6cb0", label="mean +/- 1 sd")
    a.set_xlabel("tilt (plate deg)")
    a.set_ylabel("mg per degree of auger")
    a.set_title("Trim gain and its scatter vs tilt")
    a.grid(alpha=.3)
    a.legend()

    a = ax[1][1]
    nb = 6
    for tilt in tilts_Q:
        g = [q for q in Q if q["tilt"] == tilt]
        bins = [[] for _ in range(nb)]
        for q in g:
            bins[int(q["phase_deg"] // (360.0 / nb)) % nb].append(
                q["yld"] * 1000.0)
        centres = [(i + .5) * 360.0 / nb for i in range(nb)]
        a.errorbar(centres, [mean(b) for b in bins],
                   yerr=[sem(b) for b in bins], marker="o", capsize=4,
                   color=colors[tilt], label="tilt %.0f deg" % tilt)
    a.set_xlabel("auger phase at end of increment (deg)")
    a.set_ylabel("yield (mg)")
    a.set_title("Phase structure of the trim quantum")
    a.grid(alpha=.3)
    a.legend()
    fig.suptitle("Test Q -- quantum vs tilt at the trim operating point (%s)"
                 % powder, fontsize=13)
    fig.tight_layout(rect=(0, 0, 1, .96))
    fig.savefig(os.path.join(outdir, "quantum_vs_tilt.png"), dpi=140)
    plt.close(fig)
    print("\nwrote figures + CSVs to %s" % outdir)


if __name__ == "__main__":
    main()
