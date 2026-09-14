#!/usr/bin/env python3
"""Full-campaign battery coverage figure: every powder x every block.

Companion to the round-1 EDA's R1_coverage.png (PR #97): same layout, but
aggregated over the whole campaign (2026-08-04 -> 2026-09-10), both rounds --
round 1 = characterization batteries (blocks A-E, some with G), round 2 =
closed-loop dose campaigns (blocks G at 1 g and H at 50/200 mg).

Data flow:
    --refresh   pull every document from MongoDB powder_doser.battery_runs
                (connection string in the MONGODB_URI environment variable)
                and write the committed snapshot data/battery_runs_index.csv
    (default)   read the snapshot and render out/battery_coverage.png

The snapshot is committed so the figure rebuilds without database credentials.
Counts in the matrix sum QC-valid runs only; cells whose only data comes from
runs excluded from cross-powder comparison are hatched and dagger-marked.
"""

from __future__ import annotations

import argparse
import csv
import os
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
SNAPSHOT = HERE / "data" / "battery_runs_index.csv"
OUT = HERE / "out" / "battery_coverage.png"

TRIAL_BLOCKS = ["A", "B", "C", "D", "E", "F"]
ALL_BLOCKS = TRIAL_BLOCKS + ["G", "H"]

# Display names and grouping, matching the round-1 EDA figure.
POWDERS = [
    # (powder_id, display name, group)  group: research | food
    ("alsi10mg", "AlSi10Mg", "research"),
    ("barium-chloride", "Barium chloride", "research"),
    ("fumed-silica", "Fumed silica", "research"),
    ("silicon-325", "Si (-325 mesh)", "research"),
    ("silicon-110-200", "Si (110/200 mesh)", "research"),
    ("sodium-sulfate", "Sodium sulfate", "research"),
    ("brown-rice-flour", "Brown rice flour", "food"),
    ("carboxymethyl-cellulose", "CMC", "food"),
    ("calcium-lactate", "Calcium lactate", "food"),
    ("salt", "NaCl (control)", "food"),
    ("sodium-alginate", "Sodium alginate", "food"),
    ("white-rice-flour", "White rice flour", "food"),
    ("xanthan-gum", "Xanthan gum", "food"),
]

# Per-powder status line (rightmost column) and deliberate close-outs.
# 'dagger' cells hold data only from QC-excluded runs; 'closed' cells were
# deliberately not run -- both are explained in the footnotes.
VERDICTS = {
    "alsi10mg": ("ok", "good", ""),
    "barium-chloride": ("ok", "good", "G+H caked †"),
    "fumed-silica": ("no valid run", "bad", "outlet unverified †"),
    "silicon-325": ("conveying-slowly", "good", ""),
    "silicon-110-200": ("ok", "good", "G+H stood down ‡"),
    "sodium-sulfate": ("ok", "good", ""),
    "brown-rice-flour": ("conveying-slowly", "good", "dosing descoped ‡"),
    "carboxymethyl-cellulose": ("ok", "good", ""),
    "calcium-lactate": ("ok", "good", ""),
    "salt": ("ok", "good", ""),
    "sodium-alginate": ("ok", "good", ""),
    "white-rice-flour": ("ok", "good", ""),
    "xanthan-gum": ("ok", "good", ""),
}
CLOSED_CELLS = {  # deliberately not run -> em-dash with double dagger
    ("silicon-110-200", "G"), ("silicon-110-200", "H"),
    ("brown-rice-flour", "H"),
    ("fumed-silica", "G"), ("fumed-silica", "H"),
}

FIELDS = [
    "started_utc", "powder_id", "batch", "status", "qc_valid", "qc_verdict",
    "A", "B", "C", "D", "E", "F", "doses_1g", "doses_sub_g", "dispensed_g",
    "mongo_id",
]


def refresh_snapshot() -> None:
    """Rebuild the committed run index from MongoDB (needs MONGODB_URI)."""
    from pymongo import MongoClient  # imported here: render path needs no pymongo

    client = MongoClient(os.environ["MONGODB_URI"], serverSelectionTimeoutMS=30000)
    coll = client["powder_doser"]["battery_runs"]
    rows, seen = [], set()
    for doc in coll.find():
        key = (str(doc.get("started_utc")), doc.get("powder_id"))
        if key in seen:  # the 2026-09-03T17:04 salt run was uploaded twice
            continue
        seen.add(key)
        qc = doc.get("qc") or {}
        trials = doc.get("trials") or []
        doses = doc.get("doses") or []
        blocks = defaultdict(int)
        for t in trials:
            blocks[t.get("block")] += 1
        dispensed = sum(max(t.get("delta_g") or 0.0, 0.0) for t in trials)
        dispensed += sum(d.get("dispensed_g") or 0.0 for d in doses)
        rows.append({
            "started_utc": str(doc.get("started_utc")),
            "powder_id": doc.get("powder_id"),
            "batch": doc.get("batch") or "",
            "status": doc.get("status") or "",
            "qc_valid": bool(qc.get("valid_for_cross_powder_comparison")),
            "qc_verdict": qc.get("verdict") or "",
            **{b: blocks.get(b, 0) for b in TRIAL_BLOCKS},
            "doses_1g": sum(1 for d in doses if (d.get("target_g") or 0) >= 0.5),
            "doses_sub_g": sum(1 for d in doses if 0 < (d.get("target_g") or 0) < 0.5),
            "dispensed_g": round(dispensed, 4),
            "mongo_id": str(doc.get("_id")),
        })
    rows.sort(key=lambda r: r["started_utc"])
    SNAPSHOT.parent.mkdir(parents=True, exist_ok=True)
    with SNAPSHOT.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {SNAPSHOT.relative_to(HERE)}: {len(rows)} runs "
          f"({sum(1 for r in rows if r['qc_valid'])} QC-valid)")


def load_rows() -> list[dict]:
    with SNAPSHOT.open() as fh:
        rows = list(csv.DictReader(fh))
    for r in rows:
        r["qc_valid"] = r["qc_valid"] == "True"
        for b in TRIAL_BLOCKS + ["doses_1g", "doses_sub_g"]:
            r[b] = int(r[b])
        r["dispensed_g"] = float(r["dispensed_g"])
    return rows


def aggregate(rows: list[dict]):
    """Sum counts per powder x block over valid runs; separately over excluded."""
    valid = defaultdict(lambda: defaultdict(int))
    excluded = defaultdict(lambda: defaultdict(int))
    runs = defaultdict(lambda: [0, 0])  # powder -> [char runs, dose runs] (valid)
    grams = defaultdict(float)
    for r in rows:
        tgt = valid if r["qc_valid"] else excluded
        pid = r["powder_id"]
        for b in TRIAL_BLOCKS:
            tgt[pid][b] += r[b]
        tgt[pid]["G"] += r["doses_1g"]
        tgt[pid]["H"] += r["doses_sub_g"]
        if r["qc_valid"]:
            runs[pid][0 if sum(r[b] for b in TRIAL_BLOCKS) else 1] += 1
            grams[pid] += r["dispensed_g"]
    return valid, excluded, runs, grams


def render() -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle

    rows = load_rows()
    valid, excluded, runs, grams = aggregate(rows)

    n_valid = sum(1 for r in rows if r["qc_valid"])
    n_char = sum(1 for r in rows if r["qc_valid"] and sum(r[b] for b in TRIAL_BLOCKS))
    n_trials = sum(sum(r[b] for b in TRIAL_BLOCKS) for r in rows if r["qc_valid"])
    n_doses = sum(r["doses_1g"] + r["doses_sub_g"] for r in rows if r["qc_valid"])
    g_total = sum(grams.values())

    # Sequential fill: one hue, light -> dark by count (bins), per dataviz method.
    def fill(count: int) -> tuple[str, str]:
        for hi, face, ink in ((3, "#cfe1f2", "#1f2937"), (9, "#a6cbe4", "#1f2937"),
                              (19, "#6faed6", "#12263a"), (49, "#3181bd", "#ffffff")):
            if count <= hi:
                return face, ink
        return "#08519c", "#ffffff"

    ink, muted, faint = "#1f2937", "#5b6572", "#94a3b8"
    group_color = {"research": "#d9480f", "food": "#1c7ed6"}
    good, bad = "#1a7f37", "#c62828"

    col_labels = [("A", "noise"), ("B", "hold"), ("C", "tilt"), ("D", "speed"),
                  ("E", "tap"), ("F", "vib"), ("G", "dose 1 g"), ("H", "dose 50/200 mg")]
    nrows = len(POWDERS)

    fig, ax = plt.subplots(figsize=(17.0, 9.8), dpi=150)
    ax.set_xlim(-3.4, 13.4)
    ax.set_ylim(-2.6, nrows + 1.4)
    ax.axis("off")
    ax.invert_yaxis()

    cw, ch = 0.96, 0.78  # cell width/height inside a 1.0-unit pitch

    for i, (pid, name, group) in enumerate(POWDERS):
        y = i
        ax.text(-0.25, y + ch / 2, name, ha="right", va="center",
                fontsize=12.5, color=group_color[group])
        for j, b in enumerate(ALL_BLOCKS):
            x = j
            v, ex = valid[pid][b], excluded[pid][b]
            cx, cy = x + cw / 2, y + ch / 2
            if v:
                face, tink = fill(v)
                ax.add_patch(Rectangle((x, y), cw, ch, facecolor=face,
                                       edgecolor="white", linewidth=1.5))
                ax.text(cx, cy, str(v), ha="center", va="center",
                        fontsize=12, color=tink)
            elif ex and (pid, b) not in CLOSED_CELLS:
                ax.add_patch(Rectangle((x, y), cw, ch, facecolor="#f1f3f5",
                                       edgecolor="#c3cad2", linewidth=0.9,
                                       hatch="////"))
                ax.text(cx, cy, f"{ex}†", ha="center", va="center",
                        fontsize=11.5, color="#495057")
            elif (pid, b) in CLOSED_CELLS:
                ax.text(cx, cy, "—‡", ha="center", va="center",
                        fontsize=11.5, color=faint)
            else:
                ax.text(cx, cy, "--", ha="center", va="center",
                        fontsize=11.5, color=faint)
        nc, nd = runs[pid]
        ax.text(8.75, y + ch / 2, f"{nc} + {nd}", ha="center", va="center",
                fontsize=11.5, color=ink)
        g = grams[pid]
        ax.text(10.15, y + ch / 2,
                "--" if not g else (f"{g:.1f} g" if g >= 1 else f"{g:.2f} g"),
                ha="right", va="center", fontsize=11.5,
                color=ink if g else faint)
        verdict, kind, note = VERDICTS[pid]
        vcolor = good if kind == "good" else bad
        if note:
            ax.text(10.75, y + 0.22, verdict, ha="left", va="center",
                    fontsize=11.5, color=vcolor)
            ax.text(10.75, y + 0.60, note, ha="left", va="center",
                    fontsize=10, color=muted)
        else:
            ax.text(10.75, y + ch / 2, verdict, ha="left", va="center",
                    fontsize=11.5, color=vcolor)

    # separator between the research-relevant and food-safe groups
    n_research = sum(1 for _, _, g in POWDERS if g == "research")
    ax.plot([-3.3, 13.3], [n_research - 0.11, n_research - 0.11],
            color="#dde2e8", linewidth=1.2, zorder=0)

    # column labels below the grid
    for j, (letter, sub) in enumerate(col_labels):
        ax.text(j + cw / 2, nrows + 0.28, letter, ha="center", va="top",
                fontsize=12.5, color=ink)
        ax.text(j + cw / 2, nrows + 0.75, sub, ha="center", va="top",
                fontsize=10.5, color=muted)
    for x, lines in ((8.75, "valid runs\nA–E + dose"),
                     (9.75, "powder\nmetered"), (11.4, "status")):
        ax.text(x, nrows + 0.28, lines, ha="center", va="top",
                fontsize=10.5, color=muted)

    ax.text(-3.3, -1.9, "Battery coverage, full campaign — every powder × every block",
            fontsize=17.5, fontweight="bold", color="#111827", va="top")
    ax.text(-3.3, -1.15,
            f"2026-08-04 → 2026-09-10 · cells sum QC-valid runs: measured trials (A–F) "
            f"or closed-loop doses (G = 3×1 g, H = 3×50 mg + 3×200 mg) · "
            f"{n_valid} valid runs ({n_char} characterization + {n_valid - n_char} dose) · "
            f"{n_trials} trials · {n_doses} doses · {g_total:.0f} g metered",
            fontsize=11.5, color=muted, va="top")

    footnotes = [
        "orange = research-relevant powder    blue = food-safe surrogate    -- = not recorded",
        "‡  deliberately not run — Si 110/200 G+H stood down at the environment dose gate (pre-flight banked: 316.5 mg/rev, 9.5 mg/tap) · "
        "brown rice flour + fumed silica descoped from dosing (operator: “powders we know don’t dispense”)",
        "†  recorded only in runs excluded from cross-powder comparison — fumed silica A–E (no conveyance, outlet unverified) · "
        "barium chloride G+H (hygroscopic caking/arching; dry-room re-run planned)",
        "block F never produced a trial campaign-wide (DRV2605L haptic driver dead); vibration assistance is excluded from the manuscript’s baseline procedure",
        "NaCl aggregates 3 valid A–E runs · calcium lactate H: 6 delivered, 5 recorded (capture interrupt) · "
        "G spans the round-1 frozen controller and the round-2 tuned controller",
    ]
    for k, line in enumerate(footnotes):
        ax.text(-3.3, nrows + 1.55 + 0.42 * k, line, fontsize=9.8,
                color=muted, va="top")

    fig.subplots_adjust(left=0.01, right=0.995, top=0.99, bottom=0.01)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, facecolor="white", bbox_inches="tight")
    print(f"wrote {OUT.relative_to(HERE)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true",
                        help="rebuild data/battery_runs_index.csv from MongoDB")
    args = parser.parse_args()
    if args.refresh:
        refresh_snapshot()
    render()
