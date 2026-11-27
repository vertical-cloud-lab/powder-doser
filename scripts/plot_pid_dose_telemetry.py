"""Visualize PID dose telemetry (PR #131): 4-panel dashboards + comparison."""
import csv
import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

# palette (dataviz skill reference instance, light mode)
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
BASELINE = "#c3c2b7"
BLUE, BLUE_LT = "#2a78d6", "#86b6ef"
ORANGE = "#eb6834"
AQUA = "#1baf7a"
YELLOW = "#eda100"
WASH = "#f0efec"

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE, "font.size": 9.5,
    "axes.edgecolor": BASELINE, "axes.labelcolor": INK2,
    "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.7,
    "axes.axisbelow": True, "font.family": "DejaVu Sans",
})

BASE = "data/pid-dose/2026-07-29_salt"


def load(run):
    rows = []
    with open(f"{BASE}/telemetry_{run}_salt.csv") as f:
        for r in csv.DictReader(f):
            m = r["mass_g"]
            rows.append(dict(
                t=int(r["t_ms"]) / 1000.0,
                mass=float(m) if m != "nan" else math.nan,
                frame=r["frame"], tilt=float(r["tilt_deg"]),
                rpm=float(r["auger_rpm_cmd"]), taps=int(r["taps_cum"]),
                phase=r["phase"]))
    events = []
    with open(f"{BASE}/events_{run}_salt.csv") as f:
        for r in csv.DictReader(f):
            events.append((int(r["t_ms"]) / 1000.0, r["event"]))
    return rows, events


def phase_spans(rows):
    spans, cur, t0 = [], None, None
    for r in rows:
        if r["phase"] != cur:
            if cur is not None:
                spans.append((cur, t0, r["t"]))
            cur, t0 = r["phase"], r["t"]
    spans.append((cur, t0, rows[-1]["t"]))
    return spans


def style_axis(ax, last=False):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.spines["left"].set_linewidth(0.8)
    ax.spines["bottom"].set_linewidth(0.8)
    ax.grid(axis="y")
    ax.grid(axis="x", visible=False)
    ax.tick_params(length=0)
    if not last:
        ax.tick_params(labelbottom=False)


def dashboard(run, title, subtitle, out, annot):
    rows, events = load(run)
    spans = phase_spans(rows)
    t = [r["t"] for r in rows]
    fig, axes = plt.subplots(4, 1, sharex=True, figsize=(10.5, 9.2),
                             gridspec_kw=dict(hspace=0.16))
    fig.subplots_adjust(top=0.90, bottom=0.065, left=0.085, right=0.97)
    fig.suptitle(title, x=0.085, ha="left", fontsize=14,
                 fontweight="bold", color=INK)
    fig.text(0.085, 0.925, subtitle, fontsize=9.5, color=INK2)

    # phase bands on every panel, labels on the first
    for i, ax in enumerate(axes):
        for j, (ph, a, b) in enumerate(spans):
            if j % 2 == 0:
                ax.axvspan(a, b, color=WASH, zorder=0)
    top = axes[0]
    for ph, a, b in spans:
        if b - a > (t[-1]) * 0.03:
            top.text((a + b) / 2, 1.02, ph, transform=top.get_xaxis_transform(),
                     ha="center", va="bottom", fontsize=8.5, color=MUTED)

    # 1: mass
    ax = axes[0]
    st_t = [r["t"] for r in rows if r["frame"] == "S"]
    st_m = [r["mass"] for r in rows if r["frame"] == "S"]
    us_t = [r["t"] for r in rows if r["frame"] == "U"]
    us_m = [r["mass"] for r in rows if r["frame"] == "U"]
    ax.plot(st_t, st_m, color=BLUE, lw=2, solid_capstyle="round", zorder=3)
    ax.plot(us_t, us_m, ls="none", marker="o", ms=3.4, mfc="none",
            mec=BLUE_LT, mew=1.1, zorder=2)
    ax.axhline(1.0, color=BASELINE, lw=1, ls=(0, (4, 3)), zorder=1)
    ax.text(t[-1] * 0.012, 1.03, "target 1.000 g", color=INK2,
            fontsize=8.5, va="bottom", ha="left")
    ax.set_ylabel("cup mass (g)")
    leg = ax.legend(handles=[
        Line2D([], [], color=BLUE, lw=2, label="stable (ST) frame"),
        Line2D([], [], ls="none", marker="o", mfc="none", mec=BLUE_LT,
               mew=1.1, ms=4, label="unstable (US) frame")],
        loc="lower right", frameon=False, fontsize=8.5, labelcolor=INK2)

    # 2: auger rpm
    ax = axes[1]
    ax.plot(t, [r["rpm"] for r in rows], color=ORANGE, lw=2,
            solid_capstyle="round")
    ax.set_ylabel("auger speed\n(rpm, commanded)")
    ax.set_ylim(bottom=-1)

    # 3: tilt
    ax = axes[2]
    ax.plot(t, [r["tilt"] for r in rows], color=AQUA, lw=2,
            solid_capstyle="round")
    ax.set_ylabel("dispense tilt\n(plate deg)")
    ax.set_ylim(-1, 28)

    # 4: taps
    ax = axes[3]
    ax.step(t, [r["taps"] for r in rows], where="post", color=YELLOW, lw=2)
    ax.set_ylabel("solenoid taps\n(cumulative)")
    ax.set_xlabel("time since capture start (s)")
    tmax = max(r["taps"] for r in rows)
    ax.set_ylim(-max(1, tmax) * 0.06, max(4, tmax * 1.15))
    if tmax:
        ax.text(t[-1] * 0.995, tmax, f"{tmax} taps ", color=INK2,
                fontsize=8.5, va="top", ha="right")

    for i, ax in enumerate(axes):
        style_axis(ax, last=(i == 3))
    annot(axes, rows, events)
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print("wrote", out)


def annot_run2(axes, rows, events):
    ax = axes[0]
    ev = dict((e[1].split(":")[0], e[0]) for e in events)
    for te, txt in events:
        if txt.startswith("tare (Z)"):
            ax.annotate("tare (pre-zero)", (te, 0.35), fontsize=8.5,
                        color=INK2, ha="center",
                        xytext=(te, 0.55), arrowprops=dict(
                            arrowstyle="-", color=MUTED, lw=0.8))
        if txt.startswith("overshoot guard"):
            ax.annotate("guard stops auger\n@ 1.0033 g transient", (te, 1.0033),
                        fontsize=8.5, color=INK2, ha="left",
                        xytext=(te + 3.0, 0.50), arrowprops=dict(
                            arrowstyle="-", color=MUTED, lw=0.8))
        if txt.startswith("final stable weigh"):
            ax.set_ylim(top=2.15)
            ax.annotate("final 1.0012 g (+1.2 mg)", (te, 1.0012),
                        fontsize=8.5, color=INK, fontweight="bold",
                        ha="right", xytext=(te - 1.0, 1.28),
                        arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
    axes[3].text(0.985, 0.82, "0 taps needed — PID alone hit tolerance",
                 transform=axes[3].transAxes, ha="right", fontsize=8.5,
                 color=INK2)


def annot_run1(axes, rows, events):
    ax = axes[0]
    ax.set_ylim(top=1.24)
    ax.annotate("hopper starves @ 0.9406 g (t≈23 s)", (23, 0.9406),
                fontsize=8.5, color=INK, fontweight="bold", ha="left",
                xytext=(60, 0.58), arrowprops=dict(
                    arrowstyle="-", color=MUTED, lw=0.8))
    ax.text(240, 0.74, "40 stall-recovery rounds (auger + tap bursts)\n"
            "add nothing → timeout at 420 s", fontsize=8.5, color=INK2,
            ha="center", va="top")
    ax.annotate("pre-roll shows absolute mass 0.9778 g (cup not empty)",
                (4, 0.9778), fontsize=8.5, color=INK2, ha="left",
                xytext=(42, 1.11), arrowprops=dict(
                    arrowstyle="-", color=MUTED, lw=0.8))
    axes[3].text(0.5, 0.75, "80 taps total, zero yield —\ntaps do nothing for this coarse salt",
                 transform=axes[3].transAxes, ha="center", fontsize=8.5,
                 color=INK2)


def comparison():
    fig, ax = plt.subplots(figsize=(10.5, 5.2))
    fig.subplots_adjust(top=0.86, bottom=0.11, left=0.075, right=0.97)
    fig.suptitle("PID dose phase: salt, both runs (t from dose start)",
                 x=0.075, ha="left", fontsize=14, fontweight="bold", color=INK)
    fig.text(0.075, 0.885, "same controller and gains — the only difference is powder "
             "available at the auger inlet", fontsize=9.5, color=INK2)
    for run, color, lab in (("run2", BLUE, None), ("run1", ORANGE, None)):
        rows, events = load(run)
        d0 = next(r["t"] for r in rows if r["phase"] == "dose")
        rt = [r["t"] - d0 for r in rows if r["phase"] in ("dose", "postroll", "home")]
        rm = [r["mass"] for r in rows if r["phase"] in ("dose", "postroll", "home")]
        ax.plot(rt, rm, color=color, lw=2, solid_capstyle="round")
    ax.axhline(1.0, color=BASELINE, lw=1, ls=(0, (4, 3)))
    ax.text(59.5, 1.005, "target 1.000 g", color=INK2, fontsize=8.5,
            ha="right", va="bottom")
    ax.set_xlim(-1, 60)
    ax.set_ylim(-0.03, 1.12)
    ax.set_xlabel("time since dose start (s)")
    ax.set_ylabel("cup mass since tare (g)")
    ax.text(13.5, 1.05, "run 2 (today): 1.0012 g in ~11 s, 0 taps",
            color=BLUE, fontsize=9.5, fontweight="bold")
    ax.text(26, 0.885, "run 1 (19:36 UTC): starves at 0.9406 g —\n"
            "flat through 80 taps until 420 s timeout", color=ORANGE,
            fontsize=9.5, fontweight="bold", va="top")
    style_axis(ax, last=True)
    out = f"{BASE}/pid_dose_salt_comparison.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print("wrote", out)


dashboard("run2",
          "PID dose telemetry — run 2: 1.0012 g / 1.0000 g (ok, +1.2 mg)",
          "salt · single continuous PID on auger speed (Kp=150 rpm/g, Ki=8, flow anticipation 1.1 s) · "
          "~10 Hz raw scale stream · 10 s pre/post-roll",
          f"{BASE}/pid_dose_run2_salt.png", annot_run2)
dashboard("run1",
          "PID dose telemetry — run 1: hopper starvation (timeout at 0.9406 g)",
          "salt · same PID controller, 19:36 UTC attempt · bulk phase perfect, then the hopper bridged: "
          "auger + 80 taps deliver nothing for 7 min",
          f"{BASE}/pid_dose_run1_salt.png", annot_run1)
comparison()
