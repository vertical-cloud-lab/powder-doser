"""Plot style for the gear-mesh figures: the dataviz reference palette (fixed slot order),
thin marks, solid hairline grid, text in ink colours (never the series colour)."""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK2 = "#52514e"
GRID = "#e4e3df"
CRITICAL = "#d03b3b"
GOOD = "#0ca30c"


def setup():
    plt.rcParams.update({
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
        "axes.edgecolor": GRID, "axes.labelcolor": INK2, "axes.titlecolor": INK, "axes.titlesize": 11,
        "axes.titleweight": "bold", "axes.titlelocation": "left", "axes.labelsize": 9.5,
        "xtick.color": INK2, "ytick.color": INK2, "xtick.labelsize": 8.5, "ytick.labelsize": 8.5,
        "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "grid.linestyle": "-",
        "axes.spines.top": False, "axes.spines.right": False, "legend.frameon": False,
        "legend.fontsize": 8.5, "legend.labelcolor": INK2, "lines.linewidth": 1.6,
        "font.family": "DejaVu Sans", "text.color": INK, "figure.dpi": 110,
    })


def label_end(ax, x, y, text, dx=4, dy=0, color=INK2, **kw):
    """Direct label at a line's end, in ink (not the series colour)."""
    ax.annotate(text, (x, y), xytext=(dx, dy), textcoords="offset points", va="center", fontsize=8.5, color=color, **kw)
