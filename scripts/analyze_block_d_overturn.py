#!/usr/bin/env python3
"""Reconstruct how far the auger actually turned in block D of the issue #116 battery.

Why this exists
---------------
``powder_battery._block_d_speed`` runs the auger in *velocity* mode and decides
when to stop by counting its own loop iterations::

    while waited_ms < spin_ms:
        self._sleep_ms(self.speed_poll_ms)   # 250 ms
        waited_ms += self.speed_poll_ms      # ... but the iteration is longer
        self.stepper.keep_alive()
        reading = self.scale.read()          # blocks on the balance
        self._emit("POLL", ...)

``waited_ms`` advances by the *nominal* poll period while the iteration also
pays for a balance read, so the loop exits late and the auger -- which is never
told to stop until the loop ends -- keeps turning.  The commanded revolution
count is therefore a lower bound on the delivered one.

Every POLL row carries ``_elapsed_ms()``, so the true iteration period is
recorded in the data and the real revolution count is recoverable exactly.
This script does that, and draws the result.

The battery data lives on the ``claude/issue-116-*`` branches rather than on
``main``, so by default the inputs are read straight out of a git object::

    python scripts/analyze_block_d_overturn.py
    python scripts/analyze_block_d_overturn.py --rev 86f2642
    python scripts/analyze_block_d_overturn.py --data-dir path/to/candidates/data

Outputs ``docs/rig-checks/data/2026-09-01_block-d-poll-intervals.csv`` and
``docs/rig-checks/2026-09-01_block-d-overturn.png``.
"""

from __future__ import annotations

import argparse
import collections
import csv
import io
import math
import statistics
import subprocess
import sys
from pathlib import Path

# The EDA commit on copilot/draft-base-manuscript that carries the tidy CSVs.
DEFAULT_REV = "86f2642"
DATA_IN_REV = "paper/figures/candidates/data"

# Firmware constants, from hardware/test-module/firmware/powder_battery.py.
SPEED_POLL_MS = 250.0     # SPEED_POLL_MS -- what the loop charges itself
SPEED_REVS = 3.0          # SPEED_REVS -- what the run document reports

# Categorical slots 1 and 2 of the validated default palette (all-pairs clean).
ERA_COLOUR = {"before": "#2a78d6", "after": "#eb6834"}
TEXT_PRIMARY = "#0b0b0b"
TEXT_SECONDARY = "#52514e"
TEXT_MUTED = "#8a8880"
SURFACE = "#fcfcfb"

# The move to the polishing-lab fume hood, and the battery_version 1 -> 2
# firmware change, both land in the 2026-08-12 -> 2026-08-20 run gap.
BOUNDARY = "2026-08-20"


def read_csv(name: str, rev: str | None, data_dir: Path | None) -> list[dict]:
    if data_dir is not None:
        return list(csv.DictReader((data_dir / f"{name}.csv").open()))
    blob = subprocess.run(
        ["git", "show", f"{rev}:{DATA_IN_REV}/{name}.csv"],
        capture_output=True, check=True, text=True).stdout
    return list(csv.DictReader(io.StringIO(blob)))


def poll_intervals(polls: list[dict]) -> dict[tuple[str, float], list[float]]:
    """Per (run, rpm), the wall-clock gaps between consecutive block-D polls."""
    stamps: dict[tuple[str, float], list[float]] = collections.defaultdict(list)
    for row in polls:
        if row["block"] != "D":
            continue
        stamps[(row["run_id"], float(row["rpm"]))].append(float(row["t_ms"]))
    return {key: sorted(t) for key, t in stamps.items()}


def summarise(polls: list[dict], runs: list[dict]) -> list[dict]:
    started = {r["run_id"]: r["started_utc"] for r in runs}
    powder = {r["run_id"]: r["powder_id"] for r in runs}
    out = []
    for (run_id, rpm), t in sorted(
            poll_intervals(polls).items(),
            key=lambda kv: (started.get(kv[0][0], ""), kv[0][1])):
        gaps = [b - a for a, b in zip(t, t[1:])]
        if not gaps:
            continue
        # The loop runs a fixed number of iterations: it exits the first time
        # the nominal clock reaches spin_ms, so the count never varies.
        nominal_ms = SPEED_REVS / rpm * 60.0 * 1000.0
        iterations = math.ceil(nominal_ms / SPEED_POLL_MS)
        period = statistics.median(gaps)
        actual_ms = iterations * period
        out.append({
            "run_id": run_id,
            "powder_id": powder.get(run_id, ""),
            "started_utc": started.get(run_id, ""),
            "era": "before" if started.get(run_id, "")[:10] < BOUNDARY else "after",
            "rpm": rpm,
            "n_polls": len(t),
            "iterations": iterations,
            "median_poll_ms": round(period, 1),
            "nominal_spin_s": round(nominal_ms / 1000.0, 2),
            "actual_spin_s": round(actual_ms / 1000.0, 2),
            "commanded_rev": SPEED_REVS,
            "actual_rev": round(rpm / 60.0 * actual_ms / 1000.0, 3),
            "overturn_pct": round(100.0 * (period / SPEED_POLL_MS - 1.0), 1),
        })
    return out


def render(rows: list[dict], polls: list[dict], runs: list[dict], png: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.dates as mdates
    import matplotlib.pyplot as plt
    from datetime import datetime

    started = {r["run_id"]: r["started_utc"] for r in runs}

    def when(run_id: str) -> datetime:
        return datetime.fromisoformat(started[run_id]).replace(tzinfo=None)

    fig, ax = plt.subplots(figsize=(10.5, 5.6))
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)

    # The balance delivers frames on a ~96 ms grid; the loop can only exit on
    # one of those slots, so every admissible loop period is a multiple of it.
    frame_ms = 95.9
    for k in range(1, 6):
        y = frame_ms * k
        ax.axhline(y, color=TEXT_MUTED, lw=0.6, ls=(0, (1, 3)), alpha=0.55, zorder=0)
        ax.text(1.004, y, f"{k}x", transform=ax.get_yaxis_transform(),
                va="center", ha="left", fontsize=7.5, color=TEXT_MUTED)

    ax.axhline(SPEED_POLL_MS, color=TEXT_SECONDARY, lw=1.4, ls=(0, (5, 3)), zorder=1)

    seen = set()
    for (run_id, rpm), t in poll_intervals(polls).items():
        era = "before" if started[run_id][:10] < BOUNDARY else "after"
        gaps = [b - a for a, b in zip(t, t[1:])]
        x0 = mdates.date2num(when(run_id))
        # A little deterministic spread so 1311 points stay countable.
        xs = [x0 + 0.055 * ((i % 11) - 5) / 5.0 for i in range(len(gaps))]
        label = None
        if era not in seen:
            seen.add(era)
            label = ("2026-08-04 → 08-12  (battery_version 1)" if era == "before"
                     else "2026-08-20 → 08-21  (battery_version 2)")
        ax.scatter(xs, gaps, s=7, color=ERA_COLOUR[era], alpha=0.55,
                   linewidths=0, label=label, zorder=3)

    ax.set_ylim(0, 470)
    ax.set_ylabel("block-D loop period per iteration  (ms)", fontsize=10,
                  color=TEXT_SECONDARY)
    ax.set_title("The auger kept turning between polls — and mid-August it gained a whole balance frame",
                 fontsize=12.5, color=TEXT_PRIMARY, pad=30, loc="left")
    ax.text(0, 1.045,
            "Every block-D poll interval in the issue #116 battery (n=1311). "
            "The loop charges itself 250 ms per pass but exits only on a balance frame.",
            transform=ax.transAxes, fontsize=9.2, color=TEXT_SECONDARY, va="bottom")

    ax.annotate("commanded: 250 ms/iteration → 3.00 rev",
                xy=(0.012, SPEED_POLL_MS - 15), xycoords=("axes fraction", "data"),
                fontsize=9, color=TEXT_SECONDARY, va="top")
    ax.annotate("287 ms  =  3 balance frames  →  3.44 rev  (+15 %)",
                xy=(0.012, 300), xycoords=("axes fraction", "data"),
                fontsize=9.5, color=ERA_COLOUR["before"], weight="bold")
    ax.annotate("386 ms  =  4 balance frames  →  4.63 rev  (+54 %)",
                xy=(0.55, 399), xycoords=("axes fraction", "data"),
                fontsize=9.5, color=ERA_COLOUR["after"], weight="bold")

    gap_l, gap_r = when("20260812T215154Z_salt"), when("20260820T175631Z_salt")
    ax.axvspan(mdates.date2num(gap_l) + 0.2, mdates.date2num(gap_r) - 0.2,
               color=TEXT_MUTED, alpha=0.07, zorder=0)
    ax.text((mdates.date2num(gap_l) + mdates.date2num(gap_r)) / 2, 165,
            "no runs 08-13 → 08-19\n\nrig moved to the fume hood 08-19;\n"
            "firmware went battery_version 1 → 2 on 08-20",
            ha="center", va="center", fontsize=8.4, color=TEXT_SECONDARY)

    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=2))
    ax.tick_params(colors=TEXT_SECONDARY, labelsize=9)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(TEXT_MUTED)
        ax.spines[side].set_linewidth(0.8)
    ax.grid(axis="y", color=TEXT_MUTED, alpha=0.12, lw=0.7)
    ax.set_axisbelow(True)

    leg = ax.legend(loc="lower left", frameon=False, fontsize=9,
                    markerscale=2.2, handletextpad=0.5)
    for text in leg.get_texts():
        text.set_color(TEXT_SECONDARY)

    fig.tight_layout()
    png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(png, dpi=170, facecolor=SURFACE)
    print(f"wrote {png}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rev", default=DEFAULT_REV,
                    help=f"git rev holding {DATA_IN_REV} (default: {DEFAULT_REV})")
    ap.add_argument("--data-dir", type=Path,
                    help="read polls.csv / runs.csv from here instead of git")
    ap.add_argument("--csv", type=Path,
                    default=Path("docs/rig-checks/data/2026-09-01_block-d-poll-intervals.csv"))
    ap.add_argument("--png", type=Path,
                    default=Path("docs/rig-checks/2026-09-01_block-d-overturn.png"))
    ap.add_argument("--no-plot", action="store_true")
    args = ap.parse_args(argv)

    polls = read_csv("polls", args.rev, args.data_dir)
    runs = read_csv("runs", args.rev, args.data_dir)
    rows = summarise(polls, runs)

    args.csv.parent.mkdir(parents=True, exist_ok=True)
    with args.csv.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {args.csv}  ({len(rows)} block-D speed points)")

    for era in ("before", "after"):
        sub = [r for r in rows if r["era"] == era]
        if not sub:
            continue
        period = statistics.median(r["median_poll_ms"] for r in sub)
        rev = statistics.median(r["actual_rev"] for r in sub)
        print(f"  {era:6} n={len(sub):2d}  loop period {period:5.0f} ms"
              f"  ->  {rev:.2f} rev commanded as {SPEED_REVS:.0f}"
              f"  (mg/rev inflated {100 * (rev / SPEED_REVS - 1):.0f} %)")

    if not args.no_plot:
        render(rows, polls, runs, args.png)
    return 0


if __name__ == "__main__":
    sys.exit(main())
