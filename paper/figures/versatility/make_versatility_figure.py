#!/usr/bin/env python3
"""Versatility figure: one doser, one set of settings, 13 powders.

A slide-sized redraw of manuscript Fig. 3a paired with the 1 g column of
Fig. 5, sharing one powder axis:

    left   how much powder one auger turn moves (protocol C mean at 22.5 deg
           tilt, six revolutions at 30 rpm; error bars are the standard error)
    right  how much arrived when the closed-loop controller was asked for 1 g
           (every valid 1 g dose, protocol G, both test rounds)

Every number comes from the helpers in ../make_data_figures.py, so the run
selection, the "did not convey" rule and the gear/tilt unit conversions are
the manuscript's own and cannot drift.

Outputs, all written next to this script:
    versatility.pdf, versatility.png   the finished figure, no headline
    versatility_build.gif              progressive reveal with a headline per step
    versatility_build_plain.gif        the same reveal without headlines
    steps/step_NN.png                  each reveal step, for click-to-advance slides
    versatility_data.csv               the plotted values (table view)

Usage:  python3 make_versatility_figure.py
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import make_data_figures as mdf  # noqa: E402  (shared data and unit conversions)

# Paper palette (validated categorical slots 1-2) and text tokens.
SURROGATE, RESEARCH = mdf.SURROGATE, mdf.RESEARCH
INK, INK2, MUTED = mdf.INK, mdf.INK2, mdf.MUTED
FAINT = "#8a8983"
GRID = "#e8e6e0"
BAND_OK = "#e6f4e6"
BAND_NONE = "#f0efec"

# Slide geometry: 13.33 x 7.5 in at 144 dpi is a 1920 x 1080 frame.
FIG_IN = (13.3334, 7.5)
DPI = 144
HEAD_PX = 110  # height of the headline band at the top of a GIF frame

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.size": 15,
    "axes.titlesize": 17,
    "axes.labelsize": 15,
    "axes.linewidth": 1.0,
    "axes.edgecolor": MUTED,
    "axes.labelcolor": INK,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "xtick.labelsize": 14,
    "ytick.labelsize": 15,
    "xtick.color": INK2,
    "ytick.color": INK,
    "xtick.major.width": 1.0,
    "xtick.minor.width": 0.7,
    "ytick.major.size": 0,
    "legend.frameon": False,
    "legend.fontsize": 14,
})

# Plain names for a general audience; sieve sizes give the silicon grades.
NAMES = {
    "alsi10mg": "AlSi10Mg alloy",
    "silicon-110-200": "Silicon (75–150 µm)",
    "sodium-sulfate": "Sodium sulfate",
    "calcium-lactate": "Calcium lactate",
    "barium-chloride": "Barium chloride",
    "xanthan-gum": "Xanthan gum",
    "salt": "Table salt (NaCl)",
    "carboxymethyl-cellulose": "CMC (cellulose gum)",
    "white-rice-flour": "White rice flour",
    "sodium-alginate": "Sodium alginate",
    "fumed-silica": "Fumed silica",
    "silicon-325": "Silicon (<44 µm)",
    "brown-rice-flour": "Brown rice flour",
}

# Build order. Each entry: (headline, seconds the step is held in the GIF).
STEPS = [
    ("13 powders, one auger, the same settings", 2.5),
    ("Table salt: 146 mg of powder per turn", 2.5),
    ("Food-safe stand-ins: 10 to 198 mg per turn", 3.0),
    ("Research-relevant powders: 185 to 231 mg per turn", 3.5),
    ("Three powders did not flow at all", 3.0),
    ("Next, the doser was asked for 1 g of each powder", 2.5),
    ("Seven powders, from metal alloy to food thickener, landed within ±5%", 4.0),
    ("The two slowest fell short, and non-flowing powders delivered nothing", 4.0),
    ("One doser, 13 powders: 10 flowed, 7 dosed to 1 g within ±5%", 6.0),
]
S_AXES, S_SALT, S_FOOD, S_RESEARCH, S_NOFLOW, S_DOSE_AXES, S_HITS, S_MISSES, S_ALL = range(len(STEPS))

TARGET_G = 1.0
LIMIT = 0.05  # +/-5 % acceptance limit at 1 g


# ----------------------------------------------------------------------------
# data
# ----------------------------------------------------------------------------
def load() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Per-powder conveyance (with plot rows) and the valid 1 g doses."""
    rows = []
    for pid in mdf.REP.powder_id:
        flows = pid not in mdf.DID_NOT_CONVEY
        mg, se, _ = mdf.per_turn(mdf.REP_RUN[pid], 45.0)  # recorded 45 = 22.5 deg
        rows.append(dict(powder_id=pid, name=NAMES[pid], track=mdf.TRACK[pid],
                         flows=flows,
                         mg_per_turn=mg if flows else np.nan,
                         se_mg=se if flows else np.nan))
    conv = pd.DataFrame(rows)

    # Rows: the non-flowing powders at the bottom (paper order), then the
    # flowing ones from slowest to fastest, with a half-row gap between.
    dnc = list(mdf.DID_NOT_CONVEY)
    flowing = conv[conv.flows].sort_values("mg_per_turn").powder_id.tolist()
    y = {pid: float(k) for k, pid in enumerate(dnc)}
    y.update({pid: len(dnc) + 0.6 + k for k, pid in enumerate(flowing)})
    conv["y"] = conv.powder_id.map(y)

    d = mdf.load_doses()
    d = d[d.target_mg == 1000.0].copy()
    d["delivered_g"] = d.delivered_mg / 1000.0
    d["y"] = d.powder_id.map(y)
    return conv.sort_values("y"), d


def write_table(conv: pd.DataFrame, doses: pd.DataFrame) -> None:
    g = doses.groupby("powder_id")
    t = conv[["powder_id", "name", "track", "flows", "mg_per_turn", "se_mg"]].copy()
    t["doses_1g"] = t.powder_id.map(g.size()).fillna(0).astype(int)
    t["within_5pct_1g"] = t.powder_id.map(g.passes.sum()).fillna(0).astype(int)
    t["min_delivered_g"] = t.powder_id.map(g.delivered_g.min())
    t["max_delivered_g"] = t.powder_id.map(g.delivered_g.max())
    t = t.iloc[::-1]
    t.round(4).to_csv(HERE / "versatility_data.csv", index=False)


# ----------------------------------------------------------------------------
# drawing
# ----------------------------------------------------------------------------
def colour(track: str) -> str:
    return RESEARCH if track == "research" else SURROGATE


def mark(track: str) -> tuple[str, float]:
    """Marker and size: squares read larger than circles at equal size."""
    return ("s", 10.5) if track == "research" else ("o", 12.0)


def revealed_at(row) -> int:
    """Step at which a powder's conveyance point appears."""
    if not row.flows:
        return S_NOFLOW
    if row.powder_id == "salt":
        return S_SALT
    return S_FOOD if row.track == "surrogate" else S_RESEARCH


def draw(step: int, headline: bool):
    conv, doses = DATA
    fig = plt.figure(figsize=FIG_IN, dpi=DPI)
    fig.patch.set_facecolor("white")
    ax = fig.add_axes([0.185, 0.185, 0.43, 0.66])
    bx = fig.add_axes([0.665, 0.185, 0.315, 0.66], sharey=ax)

    n_dnc = len(mdf.DID_NOT_CONVEY)
    top = conv.y.max()
    ylim = (-0.65, top + 1.55)

    # ---- (a) mass per auger turn --------------------------------------------
    ax.set_xscale("log")
    ax.set_xlim(5, 1500)
    ax.set_ylim(*ylim)
    ax.set_xticks([10, 100, 1000])
    ax.set_xticklabels(["10", "100", "1,000"])
    ax.grid(axis="x", which="major", color=GRID, lw=1.0, zorder=0)
    ax.set_xlabel("Powder moved per auger turn (mg, log scale)")
    ax.set_title("How much one turn of the auger moves", loc="left",
                 fontweight="bold", pad=10)
    ax.set_yticks(conv.y)
    ax.set_yticklabels(conv.name)
    for tl, flows in zip(ax.get_yticklabels(), conv.flows):
        if not flows and step >= S_NOFLOW:
            tl.set_color(INK2)
            tl.set_fontstyle("italic")

    if step >= S_NOFLOW:
        for a in (ax, bx):
            a.axhspan(-0.6, n_dnc - 0.4, color=BAND_NONE, zorder=0, lw=0)
        ax.text(0.97, (n_dnc - 1) / 2, "no measurable flow", ha="right",
                va="center", style="italic", color=INK2,
                transform=ax.get_yaxis_transform())

    for row in conv.itertuples():
        if not row.flows or step < revealed_at(row):
            continue
        c = colour(row.track)
        m, ms = mark(row.track)
        ax.plot([5, row.mg_per_turn], [row.y, row.y], color=c, lw=1.4,
                alpha=0.3, zorder=1, solid_capstyle="butt")
        ax.errorbar(row.mg_per_turn, row.y, xerr=row.se_mg, fmt=m, ms=ms,
                    color=c, ecolor=INK2, elinewidth=1.0, capsize=3,
                    markeredgecolor="white", markeredgewidth=1.6, zorder=3)
    # Selective direct labels: the reference powder and the two ends.
    labels = {"salt": S_SALT, "sodium-alginate": S_FOOD, "alsi10mg": S_RESEARCH}
    for pid, s in labels.items():
        if step < s:
            continue
        r = conv[conv.powder_id == pid].iloc[0]
        ax.text(r.mg_per_turn * 1.32, r.y, f"{r.mg_per_turn:.0f} mg",
                va="center", ha="left", color=INK2, fontsize=14)

    if step >= S_RESEARCH:
        flowing = conv[conv.flows]
        lo, hi = flowing.mg_per_turn.min(), flowing.mg_per_turn.max()
        yb = top + 0.8
        ax.annotate("", xy=(hi, yb), xytext=(lo, yb),
                    arrowprops=dict(arrowstyle="<|-|>", color=INK2, lw=1.2,
                                    shrinkA=0, shrinkB=0, mutation_scale=12))
        ax.text(np.sqrt(lo * hi), yb + 0.12, f"{hi / lo:.0f}× range",
                ha="center", va="bottom", color=INK, fontsize=14)

    # ---- (b) delivered at a 1 g request -------------------------------------
    bx.set_xlim(-0.06, 1.16)
    bx.set_xticks([0, 0.25, 0.5, 0.75, 1.0])
    bx.set_xticklabels(["0", "0.25", "0.5", "0.75", "1"])
    bx.tick_params(axis="y", labelleft=False)
    bx.set_xlabel("Powder delivered (g)")
    bx.set_title("Delivered when asked for 1 g", loc="left",
                 fontweight="bold", pad=10)
    if step < S_DOSE_AXES:
        bx.set_visible(False)
    else:
        bx.axvspan(TARGET_G * (1 - LIMIT), TARGET_G * (1 + LIMIT),
                   color=BAND_OK, zorder=0, lw=0)
        bx.axvline(TARGET_G, color=INK2, lw=1.2, zorder=1)
        bx.grid(axis="x", color=GRID, lw=1.0, zorder=0)
        for yy in conv.y:
            bx.axhline(yy, color="#f3f2ee", lw=1.0, zorder=0)
        bx.text(TARGET_G, top + 0.92, "1 g ± 5%", ha="center", va="bottom",
                color=INK, fontsize=14)

    if step >= S_HITS:
        for r in doses.itertuples():
            if not r.passes and step < S_MISSES:
                continue
            c = colour(mdf.TRACK[r.powder_id])
            m, ms = mark(mdf.TRACK[r.powder_id])
            if r.passes:
                # No surface ring here: replicates sit within a few pixels of
                # each other, and a ring would read as an open (missed) marker.
                bx.plot(r.delivered_g, r.y, m, ms=ms, color=c, zorder=3,
                        markeredgewidth=0)
            else:
                bx.plot(r.delivered_g, r.y, m, ms=ms - 1.5, color=c, zorder=3,
                        markerfacecolor="white", markeredgewidth=2.0)
    if step >= S_MISSES:
        untested = conv[~conv.powder_id.isin(doses.powder_id)]
        for r in untested.itertuples():
            bx.text(0.5, r.y, "not tested at 1 g", ha="center", va="center",
                    style="italic", color=FAINT, fontsize=13)

    # ---- legend: entries appear with the marks they explain ------------------
    handles = [
        Line2D([], [], marker="o", ls="", ms=12, color=SURROGATE,
               markeredgecolor="white", label="Food-safe stand-in"),
        Line2D([], [], marker="s", ls="", ms=10.5, color=RESEARCH,
               markeredgecolor="white", label="Research-relevant"),
        Line2D([], [], marker="o", ls="", ms=10.5, color=INK2,
               markerfacecolor="white", markeredgewidth=2.0,
               label="Dose outside ±5% of 1 g"),
    ]
    leg = fig.legend(handles=handles, loc="lower center", ncol=3,
                     bbox_to_anchor=(0.5, 0.005), handletextpad=0.3,
                     columnspacing=2.2)
    shown = [step >= S_SALT, step >= S_RESEARCH, step >= S_MISSES]
    for h, t, on in zip(leg.legend_handles, leg.get_texts(), shown):
        if not on:
            h.set_alpha(0)
            t.set_alpha(0)

    if headline:
        h = fig.text(0.02, 0.975, STEPS[step][0], ha="left", va="top",
                     fontsize=24, fontweight="bold", color=INK)
        # Shrink a long headline until it fits the frame width.
        renderer = fig.canvas.get_renderer()
        while (h.get_window_extent(renderer).width > 0.96 * fig.bbox.width
               and h.get_fontsize() > 16):
            h.set_fontsize(h.get_fontsize() - 0.5)
    return fig


def render(step: int, headline: bool) -> Image.Image:
    fig = draw(step, headline)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=DPI, facecolor="white")
    plt.close(fig)
    buf.seek(0)
    return Image.open(buf).convert("RGB")


def transition(a: Image.Image, b: Image.Image, t: float) -> Image.Image:
    """Cross-fade the plot; dip the headline through white so that two
    headlines are never drawn on top of each other."""
    im = Image.blend(a, b, t)
    box = (0, 0, a.width, HEAD_PX)
    src, k = (a, 1 - 2 * t) if t < 0.5 else (b, 2 * t - 1)
    white = Image.new("RGB", (a.width, HEAD_PX), "white")
    im.paste(Image.blend(white, src.crop(box), k), box)
    return im


def write_gif(frames: list[Image.Image], path: Path, fade: int = 3,
              fade_ms: int = 70) -> None:
    """Hold each step, with a short cross-fade into the next.

    One global palette (taken from the final frame plus a mid-fade sample)
    keeps the static parts identical from frame to frame, so the GIF stores
    only the regions that change.
    """
    seq, durations = [], []
    for k, im in enumerate(frames):
        if k:
            for j in range(1, fade + 1):
                seq.append(transition(frames[k - 1], im, j / (fade + 1)))
                durations.append(fade_ms)
        seq.append(im)
        durations.append(int(STEPS[k][1] * 1000))
    sample = Image.new("RGB", (frames[-1].width, frames[-1].height * 2), "white")
    sample.paste(frames[-1], (0, 0))
    sample.paste(Image.blend(frames[0], frames[-1], 0.5), (0, frames[-1].height))
    pal = sample.quantize(colors=256, method=Image.Quantize.MEDIANCUT)
    # Pillow's palette lookup is coarse near white, so snap every near-white
    # entry to pure white; otherwise the background renders as light grey.
    entries = np.array(pal.getpalette()[:256 * 3]).reshape(-1, 3)
    entries[(entries >= 248).all(axis=1)] = 255
    pal.putpalette(entries.flatten().tolist())
    pseq = [f.quantize(palette=pal, dither=Image.Dither.NONE) for f in seq]
    pseq[0].save(path, save_all=True, append_images=pseq[1:],
                 duration=durations, loop=0, optimize=True, disposal=1)
    print(f"wrote {path.name}: {len(pseq)} frames, "
          f"{sum(durations) / 1000:.1f} s, {path.stat().st_size / 1e6:.2f} MB")


DATA = load()


def main() -> None:
    conv, doses = DATA
    write_table(conv, doses)

    # Finished figure: vector PDF and a high-resolution PNG, no headline.
    fig = draw(S_ALL, headline=False)
    fig.savefig(HERE / "versatility.pdf", bbox_inches="tight")
    fig.savefig(HERE / "versatility.png", dpi=200, bbox_inches="tight",
                facecolor="white")
    plt.close(fig)
    print("wrote versatility.pdf, versatility.png")

    steps_dir = HERE / "steps"
    steps_dir.mkdir(exist_ok=True)
    plain = [render(k, headline=False) for k in range(len(STEPS))]
    # The last step only changes the headline, so without one it repeats the
    # step before it; the slide set stops there.
    for k, im in enumerate(plain[:S_ALL], start=1):
        im.save(steps_dir / f"step_{k:02d}.png", optimize=True)
    print(f"wrote steps/step_01..{S_ALL:02d}.png")

    write_gif([render(k, headline=True) for k in range(len(STEPS))],
              HERE / "versatility_build.gif")
    write_gif(plain, HERE / "versatility_build_plain.gif")


if __name__ == "__main__":
    main()
