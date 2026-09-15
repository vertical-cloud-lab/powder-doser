#!/usr/bin/env python3
"""Analyze a blocked-auger balance-disturbance log (balance_disturbance.py).

Intended purpose: with the auger mechanically blocked, quantify pure
measurement disturbance per actuation state (issue #157 / the #162 gaps).

What run 1 (2026-09-15) actually showed: the "blocked" auger dispenses.
Quiet windows sit at drift level while every actuation block deposits
real, persistent mass; the 5 g guard halted the session mid-55 rpm.  So
this script reports both readings of the data:

  * the salvage: fume-hood quiet floor + drift from the quiet windows
    (the #162 "R from stationary readings" item, issue #157);
  * the evidence: deposition per tap / per burst / per auger revolution,
    per-block levels, and the post-halt afterflow tails.

Usage:
    python scripts/analyze_balance_disturbance.py <log> <outdir>
"""

import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

# dataviz reference palette (light mode), validated order
INK = "#0b0b0b"
INK2 = "#52514e"
MUTED = "#898781"
SURFACE = "#fcfcfb"
S1_BLUE = "#2a78d6"
S2_ORANGE = "#eb6834"
S3_AQUA = "#1baf7a"
S4_YELLOW = "#eda100"
S5_MAGENTA = "#e87b a4".replace(" ", "")

KIND_TINT = {"tap": S2_ORANGE, "auger": S1_BLUE, "hold": S4_YELLOW,
             "combined": S5_MAGENTA, "servo": S3_AQUA, "post": MUTED}


def kind_of(block):
    if block.startswith("post_"):
        return "post"
    if block.startswith("auger") and block != "auger_steps":
        return "auger"
    return {"tap_single": "tap", "tap_burst": "tap",
            "stepper_hold": "hold", "auger_steps": "auger",
            "combined": "combined", "servo_moves": "servo"}.get(
                block, "quiet" if block.startswith("quiet") else "other")


def parse(log_path):
    samples, events, points, meta = [], [], [], {}
    for line in Path(log_path).read_text().splitlines():
        parts = line.strip().split(",")
        if not parts:
            continue
        if parts[0] == "D" and len(parts) >= 8:
            t, blk, m, fl, rpm, taps, servo = parts[1:8]
            samples.append((int(t), blk,
                            np.nan if m == "nan" else float(m),
                            fl, float(rpm), int(taps), float(servo)))
        elif parts[0] == "E":
            events.append((int(parts[1]), ",".join(parts[2:])))
        elif parts[0] == "P" and len(parts) >= 4:
            points.append((int(parts[1]), parts[2],
                           np.nan if parts[3] == "nan" else float(parts[3])))
        elif parts[0] == "M" and len(parts) >= 3:
            meta[parts[1]] = ",".join(parts[2:])
    df = pd.DataFrame(samples, columns=[
        "t_ms", "block", "mass_g", "flag", "rpm", "taps", "servo_deg"])
    ev = pd.DataFrame(events, columns=["t_ms", "text"])
    pt = pd.DataFrame(points, columns=["t_ms", "kind", "mass_g"])
    return df, ev, pt, meta


def datum_changed(g):
    m = g["mass_g"].values
    chg = np.ones(len(m), dtype=bool)
    chg[1:] = m[1:] != m[:-1]
    return chg


def block_stats(df):
    rows = []
    for blk, g in df.groupby("block", sort=False):
        g = g.dropna(subset=["mass_g"])
        if len(g) < 8:
            continue
        t = g["t_ms"].values / 1000.0
        d = g["dev_mg"].values
        coef = np.polyfit(t, d, 1)
        resid = d - np.polyval(coef, t)
        chg = datum_changed(g)
        rows.append({
            "block": blk, "kind": kind_of(blk),
            "t_start_s": t[0], "t_end_s": t[-1],
            "dur_s": t[-1] - t[0],
            "n_frames": len(g), "n_datums": int(chg.sum()),
            "sigma_detr_mg": float(np.std(resid[chg])),
            "p2p_mg": float(d.max() - d.min()),
            "slope_mg_per_min": float(coef[0] * 60.0),
            "delta_mg": float(np.mean(d[-6:]) - np.mean(d[:6])),
            "st_frac": float((g["flag"] == "S").mean()),
        })
    return pd.DataFrame(rows)


def tap_epochs(df, ev, pattern, pre_s=1.0, post_s=4.5):
    out = []
    for _, e in ev.iterrows():
        if not re.match(pattern, e["text"]):
            continue
        t0 = e["t_ms"]
        w = df[(df["t_ms"] >= t0 - pre_s * 1000)
               & (df["t_ms"] <= t0 + post_s * 1000)].dropna(
            subset=["mass_g"])
        if len(w) < 5:
            continue
        base = w[w["t_ms"] < t0]["dev_mg"].mean()
        for _, r in w.iterrows():
            out.append({"event": e["text"],
                        "t_rel_s": (r["t_ms"] - t0) / 1000.0,
                        "dev_mg": r["dev_mg"] - base,
                        "flag": r["flag"]})
    return pd.DataFrame(out)


def style_ax(ax):
    ax.set_facecolor(SURFACE)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(MUTED)
    ax.tick_params(colors=INK2, labelsize=8)
    ax.grid(True, axis="y", color=MUTED, alpha=0.22, linewidth=0.6)


def main():
    log_path, outdir = sys.argv[1], Path(sys.argv[2])
    outdir.mkdir(parents=True, exist_ok=True)
    df, ev, pt, meta = parse(log_path)

    ref = df[df["block"] == "quiet_pre"]["mass_g"].dropna()
    ref0 = ref.iloc[: max(5, len(ref) // 4)].median()
    df["dev_mg"] = (df["mass_g"] - ref0) * 1000.0

    blocks = block_stats(df)
    blocks.to_csv(outdir / "blocks_summary.csv", index=False)
    df.to_csv(outdir / "samples.csv", index=False)
    singles = tap_epochs(df, ev, r"^TAP,")
    singles.to_csv(outdir / "tap_epochs.csv", index=False)

    # ---- salvage: fume-hood quiet floor + drift ----
    floors, drifts, quiet_st = [], [], []
    for blk in ("quiet_pre", "quiet_mid1", "quiet_mid2", "quiet_post"):
        g = df[df["block"] == blk].dropna(subset=["mass_g"])
        if len(g) < 20:
            continue
        t = g["t_ms"].values / 1000.0
        d = g["dev_mg"].values
        coef = np.polyfit(t, d, 1)
        resid = d - np.polyval(coef, t)
        floors.append(np.std(resid[datum_changed(g)]))
        drifts.append(coef[0] * 60.0)
        quiet_st.append((g["flag"] == "S").mean())
    quiet_floor = float(np.mean(floors)) if floors else np.nan

    # ---- evidence: deposition per actuation ----
    def blk(name):
        r = blocks[blocks["block"] == name]
        return r.iloc[0] if len(r) else None

    dep = {}
    b = blk("tap_single")
    if b is not None:
        n = int(meta.get("n_tap_single", 20))
        dep["single tap (mg/tap)"] = b["delta_mg"] / n
    b = blk("tap_burst")
    if b is not None:
        n = int(meta.get("n_tap_burst", 8))
        dep["3-pulse burst (mg/burst)"] = b["delta_mg"] / n
    for name in blocks["block"]:
        m = re.match(r"^auger(\d+)_p(\d)$", name)
        if not m:
            continue
        rpm = float(m.group(1))
        b = blk(name)
        revs = rpm / 60.0 * b["dur_s"]
        dep["auger {:.0f} rpm (mg/rev)".format(rpm)] = \
            b["delta_mg"] / revs if revs else np.nan
    afterflow = {name: float(blk(name)["delta_mg"])
                 for name in blocks["block"] if name.startswith("post_")}

    guard = bool(ev["text"].str.contains("MASS_GUARD").any())
    allg = df.dropna(subset=["mass_g"])
    chg = datum_changed(allg)
    datum_dt = np.diff(allg["t_ms"].values[chg]) / 1000.0
    summary = {
        "meta": meta,
        "outcome": "mass_guard_halt" if guard else "complete",
        "quiet_floor_sigma_datum_mg": quiet_floor,
        "quiet_floor_per_window_mg": [round(f, 3) for f in floors],
        "quiet_drift_mg_per_min": [round(d, 2) for d in drifts],
        "quiet_st_frac": [round(s, 3) for s in quiet_st],
        "deposition_per_actuation": {k: round(v, 1)
                                     for k, v in dep.items()},
        "afterflow_post_blocks_mg": {k: round(v, 1)
                                     for k, v in afterflow.items()},
        "total_deposited_mg": float(
            allg["dev_mg"].iloc[-1] - allg["dev_mg"].iloc[0]),
        "datum_rate_hz": float(1.0 / np.median(datum_dt))
        if len(datum_dt) else np.nan,
        "n_frames": int(len(df)),
    }
    (outdir / "summary.json").write_text(json.dumps(summary, indent=2))

    # ---------------- figure 1: session overview (the evidence) --------
    fig, (ax, ax2) = plt.subplots(
        2, 1, figsize=(11.5, 5.4), sharex=True, dpi=160,
        gridspec_kw={"height_ratios": [2.4, 1.0], "hspace": 0.10})
    fig.patch.set_facecolor(SURFACE)
    g = allg
    ax.plot(g["t_ms"] / 1000, g["dev_mg"], color=INK, lw=0.8)
    seen = set()
    for _, b in blocks.iterrows():
        tint = KIND_TINT.get(b["kind"])
        if tint and b["kind"] != "post":
            for a in (ax, ax2):
                a.axvspan(b["t_start_s"], b["t_end_s"], color=tint,
                          alpha=0.13, lw=0)
            seen.add(b["kind"])
    ax.set_ylabel("mass vs session start (mg)", color=INK2, fontsize=9)
    ax.set_title(
        'The "blocked" auger dispenses: actuation deposits mass; quiet '
        "windows hold flat (guard halt at 5 g)", color=INK, fontsize=11,
        loc="left")
    style_ax(ax)
    order = [k for k in ("tap", "auger", "hold", "combined", "servo")
             if k in seen]
    ax.legend([plt.Rectangle((0, 0), 1, 1, color=KIND_TINT[k], alpha=0.35)
               for k in order], order, loc="upper left", ncol=len(order),
              frameon=False, fontsize=8, labelcolor=INK2)
    ax2.plot(g["t_ms"] / 1000, g["rpm"], color=S1_BLUE, lw=1.2,
             label="auger rpm")
    tap_t = ev[ev["text"].str.match(r"^(TAP|BURST),")]["t_ms"] / 1000
    ax2.plot(tap_t, np.full(len(tap_t), -5), ls="none", marker="|",
             ms=7, color=S2_ORANGE, label="tap events")
    ax2.set_ylabel("actuation", color=INK2, fontsize=9)
    ax2.set_xlabel("session time (s)", color=INK2, fontsize=9)
    ax2.legend(loc="upper left", ncol=2, frameon=False, fontsize=8,
               labelcolor=INK2)
    style_ax(ax2)
    fig.savefig(outdir / "blocked_auger_overview.png",
                bbox_inches="tight", facecolor=SURFACE)
    plt.close(fig)

    # -------- figure 2: quiet floor | tap steps | deposition ----------
    fig, (axq, axt, axd) = plt.subplots(
        1, 3, figsize=(12.5, 3.6), dpi=160,
        gridspec_kw={"width_ratios": [1.3, 1.0, 1.2], "wspace": 0.62})
    fig.patch.set_facecolor(SURFACE)

    q = df[df["block"] == "quiet_pre"].dropna(subset=["mass_g"])
    tq = q["t_ms"].values / 1000.0
    dq = q["dev_mg"].values
    cf = np.polyfit(tq, dq, 1)
    axq.plot(tq, dq, color=INK, lw=0.8)
    axq.plot(tq, np.polyval(cf, tq), color=S1_BLUE, lw=1.6, ls="--",
             label="drift {:+.2f} mg/min".format(cf[0] * 60))
    axq.set_title("Fume-hood quiet floor (120 s)", color=INK,
                  fontsize=10.5, loc="left")
    axq.set_xlabel("session time (s)", color=INK2, fontsize=9)
    axq.set_ylabel("deviation (mg)", color=INK2, fontsize=9)
    axq.legend(frameon=False, fontsize=8, labelcolor=INK2,
               loc="lower left")
    axq.text(0.02, 0.95, "sigma {:.2f} mg (detrended)".format(floors[0]),
             transform=axq.transAxes, fontsize=8, color=INK2, va="top")
    style_ax(axq)

    if len(singles):
        for _, grp in singles.groupby("event"):
            axt.plot(grp["t_rel_s"], grp["dev_mg"], color=MUTED, lw=0.7,
                     alpha=0.4)
        bins = np.arange(-1.0, 4.5, 0.2)
        sb = singles.copy()
        sb["bin"] = pd.cut(sb["t_rel_s"], bins)
        mm = sb.groupby("bin", observed=True).agg(
            t=("t_rel_s", "mean"), d=("dev_mg", "mean"))
        axt.plot(mm["t"], mm["d"], color=S2_ORANGE, lw=2.0,
                 label="mean of {} taps".format(sb["event"].nunique()))
        axt.axvline(0, color=INK2, lw=0.8, ls=":")
    axt.set_title("Each single tap lands real mass", color=INK,
                  fontsize=10.5, loc="left")
    axt.set_xlabel("time since tap (s)", color=INK2, fontsize=9)
    axt.set_ylabel("mass vs pre-tap (mg)", color=INK2, fontsize=9)
    axt.legend(frameon=False, fontsize=8, labelcolor=INK2)
    style_ax(axt)

    names = list(dep.keys())
    vals = [dep[k] for k in names]
    y = np.arange(len(names))
    axd.barh(y, vals, height=0.6, color=S1_BLUE)
    axd.set_yticks(y, names, fontsize=8, color=INK2)
    for yi, v in zip(y, vals):
        axd.text(v * 1.02, yi, "{:.0f}".format(v), va="center",
                 fontsize=8, color=INK2)
    axd.set_xlabel("deposition (mg per actuation unit)", color=INK2,
                   fontsize=9)
    axd.set_title("Leak rate by actuator", color=INK, fontsize=10.5,
                  loc="left")
    style_ax(axd)
    axd.grid(True, axis="x", color=MUTED, alpha=0.22, linewidth=0.6)
    axd.grid(False, axis="y")
    axd.invert_yaxis()
    fig.savefig(outdir / "quietfloor_and_leak.png", bbox_inches="tight",
                facecolor=SURFACE)
    plt.close(fig)

    print(json.dumps(summary, indent=2))
    print(blocks.to_string(index=False,
                           float_format=lambda v: "{:.3f}".format(v)))


if __name__ == "__main__":
    main()
