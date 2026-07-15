#!/usr/bin/env python3
"""Demo of the powder-doser digital twin: run the firmware's three-phase
policy (host-side mimic of main_three_phase.py, default parameters) against
several powders/contexts and plot dose trajectories plus the twin's behavior
curves.

Run with:  python optimization/simulation/demo_digital_twin.py
Writes demo_dose_profiles.png and demo_behaviors.png next to this file."""
import math
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).parent))
from powder_sim import Context, POWDERS, PowderDoserSim

HERE = Path(__file__).parent

# Reference categorical palette (validated order), light-mode chrome.
SERIES = ["#2a78d6", "#008300", "#e87ba4", "#eda100", "#1baf7a"]
SURFACE, INK, MUTED, GRID = "#fcfcfb", "#0b0b0b", "#898781", "#e1e0d9"
PHASE_WASH = ["#dce9fa", "#f0efec", "#fdf3dc"]  # bulk / fine / tap spans

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE, "text.color": INK,
    "axes.edgecolor": "#c3c2b7", "axes.labelcolor": "#52514e",
    "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8,
    "axes.spines.top": False, "axes.spines.right": False,
    "font.family": "sans-serif", "font.size": 10,
})


# ---------------------------------------------------------------------------
# Host-side mimic of main_three_phase.py (default parameters, velocity bulk)
# ---------------------------------------------------------------------------

def stable_read(sim, timeout_s=8.0):
    t0 = sim.t_s
    while sim.t_s - t0 < timeout_s:
        grams, stable = sim.read_balance()
        if stable:
            return grams
        sim.step(0.2)
    return sim.read_balance()[0]


def three_phase_dose(sim, target_g, t1=0.5, t2=0.05, tol=0.005,
                     max_time_s=240.0, log=None):
    """Bulk (continuous, plate 45) -> fine increments (22.5) -> taps (0)."""
    def snap(phase):
        if log is not None:
            tel = sim.telemetry()
            log.append((tel.t_s, tel.dispensed_g, tel.balance_g,
                        tel.dose_rate_g_per_s, phase))

    sim.tare()
    snap(1)
    # --- phase 1: bulk, velocity mode, anticipation 0.1 g ---
    sim.set_tilt_deg(45.0)
    sim.step(1.0)
    if target_g - stable_read(sim) > t1:
        sim.set_auger_rpm(55.0)
        while sim.t_s < max_time_s:
            sim.step(0.25)
            snap(1)
            if target_g - sim.read_balance()[0] <= t1 + 0.1:
                break
        sim.set_auger_rpm(0.0)
        sim.step(0.8)
        snap(1)
    # --- phase 2: fine increments ---
    sim.set_tilt_deg(22.5)
    sim.step(0.6)
    while sim.t_s < max_time_s and target_g - stable_read(sim) > t2:
        sim.rotate_auger_deg(30.0, 30.0)
        sim.step(1.5)
        snap(2)
    # --- phase 3: taps, with auger nudge on stall ---
    sim.set_tilt_deg(0.0)
    sim.step(0.6)
    stall = 0
    while sim.t_s < max_time_s:
        m = stable_read(sim)
        snap(3)
        if target_g - m <= tol:
            break
        before = m
        for _ in range(2):
            sim.tap()
            sim.step(0.25)
        sim.step(1.2)
        snap(3)
        if stable_read(sim) - before < 0.0005:
            stall += 1
            if stall >= 3:   # lip empty: nudge the auger a few degrees
                sim.rotate_auger_deg(5.0, 10.0)
                sim.step(0.8)
                stall = 0
        else:
            stall = 0
    snap(3)
    return sim.read_balance()[0]


# ---------------------------------------------------------------------------
# Figure 1: dose trajectories, small multiples
# ---------------------------------------------------------------------------

def fig_dose_profiles():
    target = 2.0
    cases = [
        ("salt, dry (30 %RH)", POWDERS["salt"], Context(humidity_pct_rh=30.0), 1),
        ("salt, humid + 48 h exposed (85 %RH)", POWDERS["salt"],
         Context(humidity_pct_rh=85.0, exposure_hours=48.0), 2),
        ("AlSi10Mg, dry", POWDERS["AlSi10Mg"], Context(humidity_pct_rh=30.0), 3),
    ]
    fig, axes = plt.subplots(len(cases), 1, figsize=(8.6, 8.2), sharex=True)
    for ax, color, (label, powder, ctx, seed) in zip(axes, SERIES, cases):
        sim = PowderDoserSim(powder, ctx, seed=seed)
        log = []
        final = three_phase_dose(sim, target, log=log)
        t = [r[0] for r in log]
        true_m = [r[1] for r in log]
        bal = [r[2] for r in log]
        ph = [r[4] for r in log]
        # phase spans
        for p in (1, 2, 3):
            ts = [ti for ti, pi in zip(t, ph) if pi == p]
            if ts:
                ax.axvspan(min(ts), max(ts), color=PHASE_WASH[p - 1], zorder=0)
        ax.axhline(target, color=MUTED, lw=1.0, ls=(0, (4, 3)))
        ax.plot(t, bal, color=color, lw=1.0, alpha=0.45, zorder=2)
        ax.plot(t, true_m, color=color, lw=2.0, zorder=3)
        err_mg = (final - target) * 1000.0
        ax.set_title(f"{label} — {final:.4f} g in {t[-1]:.0f} s "
                     f"({err_mg:+.1f} mg)", loc="left", fontsize=10, color=INK)
        if err_mg > 5.0:  # untuned defaults on a fast powder: the failure
            ax.text(0.5, 0.45, "overshoot: balance lag + in-flight powder\n"
                    "(untuned bulk phase on a fast powder — the failure\n"
                    "mode the no-overshoot constraint must prevent)",
                    transform=ax.transAxes, color="#52514e", fontsize=8.5,
                    ha="left")
        ax.set_ylabel("mass (g)")
        ax.set_ylim(-0.05, target * 1.12)
        ax.text(t[-1], true_m[-1] - 0.02, "  true mass", color=color,
                fontsize=8.5, va="top", ha="right")
        ax.text(0.99, 0.06, "thin line: balance reading", transform=ax.transAxes,
                color=MUTED, fontsize=8, ha="right")
        # phase labels on the top subplot only
        if ax is axes[0]:
            for p, name in ((1, "bulk"), (2, "fine"), (3, "tap")):
                ts = [ti for ti, pi in zip(t, ph) if pi == p]
                if ts:
                    ax.text((min(ts) + max(ts)) / 2, target * 1.06, name,
                            color=MUTED, fontsize=8.5, ha="center")
    axes[-1].set_xlabel("time (s)")
    fig.suptitle("Digital twin: three-phase 2 g dose (firmware default parameters)",
                 x=0.02, ha="left", fontsize=12, color=INK)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    fig.savefig(HERE / "demo_dose_profiles.png", dpi=150)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Figure 2: behavior curves (2x2)
# ---------------------------------------------------------------------------

def avg_tap_yield(powder, ctx, tilt, lip=0.20, n=30, seed=0):
    s = PowderDoserSim(powder, ctx, seed=seed)
    s.set_tilt_deg(tilt)
    s.step(1.0)
    total = 0.0
    for _ in range(n):
        s.lip_g = lip
        total += s.tap()
    return 1000.0 * total / n  # mg


def fig_behaviors():
    fig, axes = plt.subplots(2, 2, figsize=(9.6, 7.2))
    (ax_a, ax_b), (ax_c, ax_d) = axes

    # (a) per-tap yield vs tilt
    tilts = list(range(0, 46, 3))
    for i, name in enumerate(("salt", "lactose")):
        y = [avg_tap_yield(POWDERS[name], Context(), t, seed=1) for t in tilts]
        ax_a.plot(tilts, y, color=SERIES[i], lw=2.0)
        ax_a.text(tilts[-1], y[-1], f" {name}", color=SERIES[i], fontsize=9,
                  va="center")
    ax_a.set_xlabel("tilt (plate deg)")
    ax_a.set_ylabel("mg per tap (0.2 g on lip)")
    ax_a.set_title("Steeper tilt ejects more per tap", loc="left", fontsize=10)
    ax_a.set_xlim(0, 56)

    # (b) feed factor vs hopper fill
    fills = [i / 50 for i in range(1, 51)]
    for i, name in enumerate(("salt", "AlSi10Mg", "stainless_316L")):
        y = []
        for f in fills:
            s = PowderDoserSim(POWDERS[name], Context(hopper_fill_frac=f), seed=2)
            s.set_tilt_deg(45.0)
            s.step(1.0)
            y.append(1000.0 * s.feed_factor_g_per_rev())
        ax_b.plot([f * 100 for f in fills], y, color=SERIES[i], lw=2.0)
        ax_b.text(101, y[-1], f" {name}", color=SERIES[i], fontsize=9, va="center")
    ax_b.set_xlabel("hopper fill (%)")
    ax_b.set_ylabel("feed factor (mg/rev, 45 deg)")
    ax_b.set_title("Starved screw below ~30 % fill", loc="left", fontsize=10)
    ax_b.set_xlim(0, 145)

    # (c) rotate-then-tap interaction: tap yields with/without replenishment
    # (mean over seeds -- single runs are dominated by clump quantization)
    n_seeds = 25
    per_tap = [[] for _ in range(12)]
    for seed in range(n_seeds):
        s = PowderDoserSim(POWDERS["salt"], Context(), seed=100 + seed)
        s.set_tilt_deg(10.0)
        s.step(1.0)
        s.rotate_auger_deg(540.0, 40.0)
        s.step(0.3)
        for i in range(8):
            per_tap[i].append(1000.0 * s.tap())
            s.step(0.3)
        s.rotate_auger_deg(180.0, 40.0)  # replenish the lip
        s.step(0.3)
        for i in range(8, 12):
            per_tap[i].append(1000.0 * s.tap())
            s.step(0.3)
    seq = [sum(v) / len(v) for v in per_tap]
    idx = list(range(1, len(seq) + 1))
    ax_c.bar(idx, seq, color=[SERIES[0]] * 8 + [SERIES[1]] * 4, width=0.72)
    ax_c.axvline(8.5, color=MUTED, lw=1.0, ls=(0, (4, 3)))
    ax_c.text(8.6, max(seq) * 0.95, "auger rotation\nreplenishes lip",
              color="#52514e", fontsize=8.5, va="top")
    ax_c.set_xlabel("tap number")
    ax_c.set_ylabel(f"mg per tap (mean of {n_seeds} runs)")
    ax_c.set_title("Repeated taps deplete the lip; rotation restores yield",
                   loc="left", fontsize=10)

    # (d) effective cohesion vs exposure at several RH
    hours = list(range(0, 97, 4))
    for i, rh in enumerate((20.0, 50.0, 85.0)):
        y = [PowderDoserSim(POWDERS["silicon"],
                            Context(humidity_pct_rh=rh, exposure_hours=h),
                            seed=0).effective_cohesion() for h in hours]
        ax_d.plot(hours, y, color=SERIES[i], lw=2.0)
        ax_d.text(hours[-1], y[-1], f" {rh:.0f} %RH", color=SERIES[i],
                  fontsize=9, va="center")
    ax_d.set_xlabel("open-air exposure (h)")
    ax_d.set_ylabel("effective cohesion (0-1)")
    ax_d.set_title("Humidity exposure degrades flow (silicon)", loc="left",
                   fontsize=10)
    ax_d.set_xlim(0, 125)

    fig.suptitle("Digital twin behavior curves", x=0.02, ha="left",
                 fontsize=12, color=INK)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(HERE / "demo_behaviors.png", dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    fig_dose_profiles()
    print("wrote demo_dose_profiles.png")
    fig_behaviors()
    print("wrote demo_behaviors.png")
