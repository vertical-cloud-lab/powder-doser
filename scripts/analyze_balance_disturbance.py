#!/usr/bin/env python3
"""Analyze a blocked-auger balance-disturbance log (balance_disturbance.py).

With the auger mechanically blocked, nothing the actuators do can deliver
mass, so every deviation in the stream is measurement disturbance:
vibration coupling from the tapper / stepper / servo plus the fume-hood
environment (issue #157).  This script quantifies, per actuation state:

  * sigma of the detrended deviation (all frames, and datum-changed
    frames only -- the balance updates at ~5 Hz while we poll at ~16 Hz);
  * peak-to-peak deviation and net offset walked per block;
  * the stable-flag (ST) fraction;
  * tap impulse responses (superposed epochs) and post-block settling
    time back to the quiet floor;
  * the quiet-floor sigma + drift itself, from the two 120 s anchors.

Usage:
    python scripts/analyze_balance_disturbance.py <log> <outdir>

Writes samples.csv, blocks_summary.csv, tap_epochs.csv, summary.json and
three PNG figures into <outdir>.
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
S5_MAGENTA = "#e87ba4"

BLOCK_KIND = {
    "quiet_pre": "quiet", "quiet_mid1": "quiet", "quiet_mid2": "quiet",
    "quiet_mid3": "quiet", "quiet_mid4": "quiet", "quiet_post": "quiet",
    "tap_single": "tap", "tap_burst": "tap",
    "stepper_hold": "hold", "auger_steps": "auger",
    "combined": "combined", "post_combined": "post",
    "servo_moves": "servo",
}
KIND_TINT = {"quiet": None, "tap": S2_ORANGE, "auger": S1_BLUE,
             "hold": S4_YELLOW, "combined": S5_MAGENTA, "servo": S3_AQUA,
             "post": MUTED}


def kind_of(block):
    if block.startswith(("auger", "post_auger")):
        return "post" if block.startswith("post_") else "auger"
    return BLOCK_KIND.get(block, "other")


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
    """Mask of frames where the balance datum actually updated."""
    m = g["mass_g"].values
    chg = np.ones(len(m), dtype=bool)
    chg[1:] = m[1:] != m[:-1]
    return chg


def block_stats(df, quiet_floor_mg):
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
        resid_chg = resid[chg]
        rows.append({
            "block": blk, "kind": kind_of(blk),
            "t_start_s": t[0], "t_end_s": t[-1],
            "n_frames": len(g), "n_datums": int(chg.sum()),
            "sigma_mg": float(np.std(resid)),
            "sigma_datum_mg": float(np.std(resid_chg)),
            "p2p_mg": float(d.max() - d.min()),
            "drift_mg_per_min": float(coef[0] * 60.0),
            "net_offset_mg": float(np.mean(d[-8:]) - np.mean(d[:8])),
            "st_frac": float((g["flag"] == "S").mean()),
            "over_floor_x": float(np.std(resid_chg) / quiet_floor_mg)
            if quiet_floor_mg else np.nan,
        })
    return pd.DataFrame(rows)


def tap_epochs(df, ev, pattern, pre_s=1.0, post_s=4.5):
    out = []
    for _, e in ev.iterrows():
        if not re.match(pattern, e["text"]):
            continue
        t0 = e["t_ms"]
        w = df[(df["t_ms"] >= t0 - pre_s * 1000)
               & (df["t_ms"] <= t0 + post_s * 1000)].dropna(subset=["mass_g"])
        if len(w) < 5:
            continue
        base = w[w["t_ms"] < t0]["dev_mg"].mean()
        for _, r in w.iterrows():
            out.append({"event": e["text"], "t_rel_s":
                        (r["t_ms"] - t0) / 1000.0,
                        "dev_mg": r["dev_mg"] - base,
                        "flag": r["flag"]})
    return pd.DataFrame(out)


def settle_time(df, t_halt_ms, floor_mg, win_s=2.0, horizon_s=15.0):
    """Seconds after t_halt until rolling win_s sigma <= 2x floor."""
    g = df[(df["t_ms"] >= t_halt_ms)
           & (df["t_ms"] <= t_halt_ms + horizon_s * 1000)].dropna(
        subset=["mass_g"])
    t = g["t_ms"].values
    d = g["dev_mg"].values
    for i in range(len(g)):
        sel = (t >= t[i]) & (t <= t[i] + win_s * 1000)
        if sel.sum() < 5:
            break
        if np.std(d[sel] - np.polyval(
                np.polyfit(t[sel] / 1000, d[sel], 1), t[sel] / 1000)) \
                <= 2.0 * floor_mg:
            return (t[i] - t_halt_ms) / 1000.0
    return np.nan


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

    # deviation from the session's opening quiet level, in mg
    ref = df[df["block"] == "quiet_pre"]["mass_g"].dropna()
    ref0 = ref.iloc[: max(5, len(ref) // 4)].median()
    df["dev_mg"] = (df["mass_g"] - ref0) * 1000.0

    # quiet floor: pooled detrended sigma of the two 120 s anchors,
    # datum-changed frames only
    floors = []
    for blk in ("quiet_pre", "quiet_post"):
        g = df[df["block"] == blk].dropna(subset=["mass_g"])
        if len(g) < 20:
            continue
        t = g["t_ms"].values / 1000.0
        d = g["dev_mg"].values
        resid = d - np.polyval(np.polyfit(t, d, 1), t)
        floors.append(np.std(resid[datum_changed(g)]))
    quiet_floor = float(np.mean(floors)) if floors else np.nan

    blocks = block_stats(df, quiet_floor)
    blocks.to_csv(outdir / "blocks_summary.csv", index=False)
    df.to_csv(outdir / "samples.csv", index=False)

    singles = tap_epochs(df, ev, r"^TAP,")
    bursts = tap_epochs(df, ev, r"^BURST,")
    singles.to_csv(outdir / "tap_epochs.csv", index=False)

    # settling after each actuation block end
    settles = {}
    for _, e in ev.iterrows():
        m = re.match(r"^BLOCK_END,(auger\d+_p\d|combined|stepper_hold"
                     r"|auger_steps|tap_single|tap_burst)$", e["text"])
        if m:
            settles[m.group(1)] = settle_time(df, e["t_ms"], quiet_floor)

    # drift over the whole session
    q = df[df["block"].isin(["quiet_pre", "quiet_post"])].dropna(
        subset=["mass_g"])
    tq = q["t_ms"].values / 60000.0
    drift_session = float(np.polyfit(tq, q["dev_mg"].values, 1)[0])

    net_session_mg = float(
        df[df["block"] == "quiet_post"]["dev_mg"].dropna().tail(40).mean()
        - df[df["block"] == "quiet_pre"]["dev_mg"].dropna().head(40).mean())

    # effective datum rate
    allg = df.dropna(subset=["mass_g"])
    chg = datum_changed(allg)
    datum_dt = np.diff(allg["t_ms"].values[chg]) / 1000.0
    datum_hz = float(1.0 / np.median(datum_dt)) if len(datum_dt) else np.nan

    summary = {
        "meta": meta,
        "quiet_floor_sigma_datum_mg": quiet_floor,
        "session_drift_mg_per_min": drift_session,
        "net_session_offset_mg": net_session_mg,
        "datum_rate_hz": datum_hz,
        "settle_after_block_s": settles,
        "n_frames": int(len(df)),
        "guard_tripped": bool(ev["text"].str.contains("MASS_GUARD").any()),
    }
    (outdir / "summary.json").write_text(json.dumps(summary, indent=2))

    # ---------------- figure 1: session overview ----------------
    fig, (ax, ax2) = plt.subplots(
        2, 1, figsize=(11.5, 5.6), sharex=True, dpi=160,
        gridspec_kw={"height_ratios": [2.4, 1.0], "hspace": 0.10})
    fig.patch.set_facecolor(SURFACE)
    g = df.dropna(subset=["mass_g"])
    ax.plot(g["t_ms"] / 1000, g["dev_mg"], color=INK, lw=0.7)
    seen = set()
    for _, b in blocks.iterrows():
        tint = KIND_TINT.get(b["kind"])
        if tint:
            ax.axvspan(b["t_start_s"], b["t_end_s"], color=tint,
                       alpha=0.13, lw=0)
            ax2.axvspan(b["t_start_s"], b["t_end_s"], color=tint,
                        alpha=0.13, lw=0)
            seen.add(b["kind"])
    ax.set_ylabel("balance deviation (mg)", color=INK2, fontsize=9)
    ax.set_title(
        "Blocked auger: everything the balance reports during actuation "
        "is disturbance, not mass", color=INK, fontsize=11, loc="left")
    style_ax(ax)
    handles = [plt.Rectangle((0, 0), 1, 1, color=KIND_TINT[k], alpha=0.35)
               for k in ("tap", "auger", "hold", "combined", "servo")
               if k in seen]
    labels = [k for k in ("tap", "auger", "hold", "combined", "servo")
              if k in seen]
    ax.legend(handles, labels, loc="upper left", ncol=len(labels),
              frameon=False, fontsize=8, labelcolor=INK2)
    ax2.plot(g["t_ms"] / 1000, g["rpm"], color=S1_BLUE, lw=1.2,
             label="auger rpm")
    ax2.plot(g["t_ms"] / 1000, g["servo_deg"], color=S3_AQUA, lw=1.2,
             label="servo (plate deg)")
    tap_t = ev[ev["text"].str.match(r"^(TAP|BURST),")]["t_ms"] / 1000
    ax2.plot(tap_t, np.full(len(tap_t), -6), ls="none", marker="|",
             ms=7, color=S2_ORANGE, label="tap events")
    ax2.set_ylabel("actuation", color=INK2, fontsize=9)
    ax2.set_xlabel("session time (s)", color=INK2, fontsize=9)
    ax2.legend(loc="upper left", ncol=3, frameon=False, fontsize=8,
               labelcolor=INK2)
    style_ax(ax2)
    fig.savefig(outdir / "disturbance_overview.png", bbox_inches="tight",
                facecolor=SURFACE)
    plt.close(fig)

    # ---------------- figure 2: per-state noise ----------------
    b = blocks[~blocks["kind"].isin(["post"])].copy()
    b = b.sort_values("sigma_datum_mg")
    fig, (axa, axb) = plt.subplots(
        1, 2, figsize=(11.5, 0.34 * len(b) + 1.6), dpi=160,
        gridspec_kw={"width_ratios": [2.0, 1.0], "wspace": 0.08},
        sharey=True)
    fig.patch.set_facecolor(SURFACE)
    y = np.arange(len(b))
    axa.barh(y, b["sigma_datum_mg"], height=0.62, color=S1_BLUE)
    axa.set_yticks(y, b["block"], fontsize=8, color=INK2)
    for yi, v in zip(y, b["sigma_datum_mg"]):
        axa.text(v * 1.05, yi, f"{v:.2f}", va="center", fontsize=7.5,
                 color=INK2)
    axa.axvline(quiet_floor, color=MUTED, ls="--", lw=1)
    axa.text(quiet_floor * 1.05, len(b) - 0.4,
             f"quiet floor {quiet_floor:.2f} mg", fontsize=7.5,
             color=INK2, rotation=0)
    axa.set_xscale("log")
    axa.set_xlabel("detrended sigma, datum frames (mg, log)", color=INK2,
                   fontsize=9)
    axa.set_title("Noise by actuation state", color=INK, fontsize=11,
                  loc="left")
    style_ax(axa)
    axa.grid(True, axis="x", color=MUTED, alpha=0.22, linewidth=0.6)
    axa.grid(False, axis="y")
    axb.barh(y, 100 * b["st_frac"], height=0.62, color=S3_AQUA)
    for yi, v in zip(y, 100 * b["st_frac"]):
        axb.text(min(v + 2, 92), yi, f"{v:.0f}%", va="center",
                 fontsize=7.5, color=INK2)
    axb.set_xlim(0, 105)
    axb.set_xlabel("stable-flag (ST) frames (%)", color=INK2, fontsize=9)
    axb.set_title("Balance calls itself stable", color=INK, fontsize=11,
                  loc="left")
    style_ax(axb)
    axb.grid(True, axis="x", color=MUTED, alpha=0.22, linewidth=0.6)
    axb.grid(False, axis="y")
    fig.savefig(outdir / "disturbance_by_state.png", bbox_inches="tight",
                facecolor=SURFACE)
    plt.close(fig)

    # ---------------- figure 3: tap impulse + rpm coupling ----------------
    fig, (axl, axr) = plt.subplots(1, 2, figsize=(11.5, 3.8), dpi=160,
                                   gridspec_kw={"wspace": 0.22})
    fig.patch.set_facecolor(SURFACE)
    if len(singles):
        for _, grp in singles.groupby("event"):
            axl.plot(grp["t_rel_s"], grp["dev_mg"], color=MUTED,
                     lw=0.7, alpha=0.4)
        bins = np.arange(-1.0, 4.5, 0.2)
        singles["bin"] = pd.cut(singles["t_rel_s"], bins)
        m = singles.groupby("bin", observed=True).agg(
            t=("t_rel_s", "mean"), d=("dev_mg", "mean"))
        axl.plot(m["t"], m["d"], color=S2_ORANGE, lw=2.0,
                 label="mean of {} taps".format(
                     singles["event"].nunique()))
        axl.axvline(0, color=INK2, lw=0.8, ls=":")
        axl.text(0.05, axl.get_ylim()[1] * 0.9 if axl.get_ylim()[1] > 0
                 else 0.5, "tap", fontsize=8, color=INK2)
    axl.set_xlabel("time since tap (s)", color=INK2, fontsize=9)
    axl.set_ylabel("deviation vs pre-tap (mg)", color=INK2, fontsize=9)
    axl.set_title("Single-tap impulse response (no powder)", color=INK,
                  fontsize=11, loc="left")
    axl.legend(frameon=False, fontsize=8, labelcolor=INK2)
    style_ax(axl)
    lad = blocks[blocks["block"].str.match(r"^auger\d+_p\d$")].copy()
    if len(lad):
        lad["rpm"] = lad["block"].str.extract(
            r"auger(\d+)_").astype(float)
        lad["pass"] = lad["block"].str.extract(r"_p(\d)").astype(int)
        for pnum, colr, mk in ((1, S1_BLUE, "o"), (2, S2_ORANGE, "s")):
            sel = lad[lad["pass"] == pnum].sort_values("rpm")
            axr.plot(sel["rpm"], sel["sigma_datum_mg"], color=colr,
                     lw=1.6, marker=mk, ms=6,
                     label="pass {}".format(pnum))
    axr.axhline(quiet_floor, color=MUTED, ls="--", lw=1)
    axr.text(16, quiet_floor * 1.1, "quiet floor", fontsize=7.5,
             color=INK2)
    axr.set_xlabel("auger speed (rpm)", color=INK2, fontsize=9)
    axr.set_ylabel("detrended sigma (mg)", color=INK2, fontsize=9)
    axr.set_title("Auger-spin coupling vs speed", color=INK, fontsize=11,
                  loc="left")
    axr.legend(frameon=False, fontsize=8, labelcolor=INK2)
    style_ax(axr)
    fig.savefig(outdir / "disturbance_tap_rpm.png", bbox_inches="tight",
                facecolor=SURFACE)
    plt.close(fig)

    print(json.dumps(summary, indent=2)[:2200])
    print(blocks.to_string(index=False, float_format=lambda v: f"{v:.3f}"))


if __name__ == "__main__":
    main()
