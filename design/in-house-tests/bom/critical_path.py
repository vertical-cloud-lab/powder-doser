"""Critical path from ordering to a working apparatus: parts in transit, printing, FC-1 boards, assembly.

    python critical_path.py      # -> critical_path.png, critical_path.json

Inputs: lead_times.json (this folder, per apparatus, calendar days from an order on Sat 28 Nov 2026)
and ../print/plates.json (slicer time per plate). Printing is simulated on the lab's two A1 minis and
the H2D, starting Monday 08:00; a person changes plates between 08:00 and 20:00 (30 min each), so a
plate that ends at night waits for the morning. Assembly and commissioning: one working day each,
after both the parts and the prints are in. All of this is a plan, not a measurement.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

HERE = Path(__file__).resolve().parent
PRINT = HERE.parent / "print" / "plates.json"
LEAD = HERE / "lead_times.json"

C_PARTS, C_PRINT, C_PCB, C_ASM = "#257de0", "#f47230", "#00b894", "#f2a600"
TEXT, TEXT2, GRID = "#191919", "#666666", "#e6e6e6"
NAMES = {"1": "1 Heap AoR", "2": "2 Density", "3": "3 Tilting plate", "4": "4 PSD images", "5": "5 Orifice cup",
         "6": "6 Humidity", "7": "7 Drum", "8": "8 UCS", "9": "9 Spreading", "10": "10 Faraday cup"}


def secs(s):
    return sum(int(v) * {"d": 86400, "h": 3600, "m": 60, "s": 1}[u] for v, u in re.findall(r"(\d+)([dhms])", s or ""))


def schedule(plates):
    """Return {plate: (start_day, end_day)} on 2 A1 minis + 1 H2D, operator hours 08-20."""
    def test_of(k):
        m = re.search(r"_t(\d\d)_", k)
        return int(m.group(1)) if m else 0          # shared / misc first
    order = sorted(plates, key=lambda p: (test_of(p["plate"]), -secs(p["time"])))
    free = {"A1M-1": 2 + 8 / 24, "A1M-2": 2 + 8 / 24, "H2D": 2 + 8 / 24}
    out = {}
    for p in order:
        cands = [k for k in free if k.startswith(p["printer"][:3])]
        k = min(cands, key=lambda c: free[c])
        start = free[k]
        hour = (start % 1) * 24
        if hour < 8:
            start = int(start) + 8 / 24
        elif hour > 20:
            start = int(start) + 1 + 8 / 24
        end = start + secs(p["time"]) / 86400
        out[p["plate"]] = (k, start, end)
        free[k] = end + 0.5 / 24
    return out


def main():
    plates = json.loads(PRINT.read_text())
    lead = json.loads(LEAD.read_text())["apparatus"]
    sched = schedule(plates)
    shared_done = max(e for pl, (_, s, e) in sched.items() if not re.search(r"_t\d\d_", pl))
    rows = []
    for t in [str(i) for i in range(1, 11)]:
        mine = [(s, e) for pl, (_, s, e) in sched.items() if f"_t{int(t):02d}_" in pl]
        p0 = min(s for s, _ in mine) if mine else 2 + 8 / 24
        p1 = max([e for _, e in mine] + [shared_done])
        arrive = float(lead[t]["with_shared_max_days"] or 0)
        pcb = (2.0, 11.0) if t == "10" else None          # OSH Park Super Swift, BOM: about day 7-11
        ready = max(p1, arrive, pcb[1] + 0.5 if pcb else 0)
        a0 = ready if (ready % 1) * 24 < 17 else int(ready) + 1 + 8 / 24
        a1 = a0 + 1.0
        rows.append({"test": t, "name": NAMES[t], "parts_days": arrive, "print": [round(p0, 2), round(p1, 2)],
                     "pcb": pcb, "assembly": [round(a0, 2), round(a1, 2)]})
    (HERE / "critical_path.json").write_text(json.dumps({"order": "Sat 28 Nov 2026 (day 0)", "rows": rows,
                                                         "printers": {k: round(max(e for _, (kk, s, e) in
                                                                      [(pl, v) for pl, v in sched.items()] if kk == k), 2)
                                                                      for k in ("A1M-1", "A1M-2", "H2D")}}, indent=1) + "\n")
    fig, ax = plt.subplots(figsize=(11, 5.4), dpi=150)
    h = 0.22
    for i, r in enumerate(rows):
        y = len(rows) - 1 - i
        def bar(x0, x1, yy, col):
            ax.add_patch(FancyBboxPatch((x0, yy - h / 2), max(0.05, x1 - x0), h, boxstyle="round,pad=0,rounding_size=0.08",
                                        linewidth=0, facecolor=col, mutation_aspect=0.25))
        bar(0, r["parts_days"], y + 0.27, C_PARTS)
        bar(r["print"][0], r["print"][1], y, C_PRINT)
        if r["pcb"]:
            bar(r["pcb"][0], r["pcb"][1], y - 0.27, C_PCB)
        bar(r["assembly"][0], r["assembly"][1], y - (0.27 if not r["pcb"] else 0.0) * 0 , C_ASM)
        ax.text(r["assembly"][1] + 0.2, y, f"ready day {r['assembly'][1]:.0f}", va="center", ha="left", fontsize=8.5, color=TEXT)
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([r["name"] for r in reversed(rows)], fontsize=9, color=TEXT)
    ax.set_xlim(0, 16)
    ax.set_ylim(-0.7, len(rows) - 0.35)
    ax.set_xticks(range(0, 17, 2))
    ax.set_xlabel("days after ordering on Sat 28 Nov 2026 (most vendors ship Monday, day 2)", fontsize=9, color=TEXT2)
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color("#bbbbbb")
    ax.tick_params(axis="y", length=0)
    ax.tick_params(axis="x", colors=TEXT2, labelsize=8.5)
    handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in (C_PARTS, C_PRINT, C_PCB, C_ASM)]
    ax.legend(handles, ["bought parts in transit (latest line, incl. shared)", "printing (2 x A1 mini + H2D)",
                        "FC-1 boards (OSH Park)", "assembly and commissioning"], loc="upper center",
              bbox_to_anchor=(0.5, 1.09), ncol=4, frameon=False, fontsize=8.5)
    fig.suptitle("Critical path to working apparatuses (plan; ground shipping)", x=0.01, ha="left", fontsize=11, color=TEXT)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    fig.savefig(HERE / "critical_path.png")
    print(json.dumps(rows, indent=0)[:1500])


if __name__ == "__main__":
    main()
