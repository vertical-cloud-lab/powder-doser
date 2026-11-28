"""Shared matplotlib style for sim/cfd (dataviz skill reference palette, light mode)."""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

CAT = ["#257de0", "#f47230", "#00b894", "#f2a600", "#ee7fac", "#008a17", "#6a4ce2", "#ec4647"]
TEXT = "#191919"
TEXT2 = "#666666"
GRID = "#e5e5e5"

plt.rcParams.update({
    "font.size": 9,
    "axes.edgecolor": TEXT2,
    "axes.labelcolor": TEXT,
    "axes.titlesize": 10,
    "axes.titleweight": "bold",
    "xtick.color": TEXT2,
    "ytick.color": TEXT2,
    "text.color": TEXT,
    "lines.linewidth": 2.0,
    "legend.frameon": False,
    "savefig.facecolor": "white",
})


def tidy(ax, grid=True):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    if grid:
        ax.grid(True, color=GRID, lw=0.6)
        ax.set_axisbelow(True)
