"""Onshape API calls: PR #176's direct REST work vs. fsgen 0.1 (``..``) vs. fsgen 0.2.0 (this folder).

Sorts every counted call (2xx/3xx; Onshape doesn't count 4xx) by purpose with the rules in
``../api_calls.py`` and writes ``results/api_calls_by_purpose.json`` and
``renders/api_calls_by_purpose.png``. No Onshape calls.

    python api_calls.py

fsgen 0.2.0 keeps one ledger for the main workspace and both branches (``--document`` picks the
workspace). The calls from ``EXTRA_FROM`` on are the Variable-Studio-only test, which the 0.1 study
didn't run; they are counted separately so the chart compares the same steps.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("api_calls_01", HERE.parent / "api_calls.py")
v01 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(v01)
PURPOSES = v01.PURPOSES
EXTRA_FROM = "20261010-150558"  # first run of the Variable-Studio-only test (its branch)


def rows(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text().splitlines()]


def tally() -> dict:
    out = {"direct_pr176": {k: 0 for k in PURPOSES}, "fsgen_0.1": {k: 0 for k in PURPOSES},
           "fsgen_0.2.0": {k: 0 for k in PURPOSES}, "fsgen_0.2.0_extra_test": {k: 0 for k in PURPOSES}}
    direct = rows(HERE.parent / "results" / "pr176_api_calls.jsonl")
    for r in direct:
        if r["status"] < 400:
            out["direct_pr176"][v01.purpose_direct(r)] += 1
    old = rows(HERE.parent / ".fsgen_api_ledger.jsonl") + rows(HERE.parent / "branch_thinner_table" / ".fsgen_api_ledger.jsonl")
    for r in old:
        if r["counted"]:
            out["fsgen_0.1"][v01.purpose_fsgen(r)] += 1
    new = rows(HERE / ".fsgen_api_ledger.jsonl")
    for r in new:
        if r["counted"]:
            key = "fsgen_0.2.0_extra_test" if r["run"] >= EXTRA_FROM else "fsgen_0.2.0"
            out[key][v01.purpose_fsgen(r)] += 1
    out["totals"] = {"direct_pr176_logged": len(direct), "direct_pr176_counted": sum(out["direct_pr176"].values()),
                     "fsgen_0.1_counted": sum(out["fsgen_0.1"].values()),
                     "fsgen_0.2.0_counted": sum(out["fsgen_0.2.0"].values()),
                     "fsgen_0.2.0_extra_test_counted": sum(out["fsgen_0.2.0_extra_test"].values()),
                     "fsgen_0.2.0_logged": len(new)}
    return out


def plot(t: dict, path: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    surface, ink, ink2, grid = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
    colors = {"direct_pr176": "#2a78d6", "fsgen_0.1": "#eb6834", "fsgen_0.2.0": "#1baf7a"}  # categorical slots 1-3
    tt = t["totals"]
    labels = {"direct_pr176": f"Direct REST API, PR #176 ({tt['direct_pr176_counted']} calls)",
              "fsgen_0.1": f"fsgen 0.1 ({tt['fsgen_0.1_counted']} calls)",
              "fsgen_0.2.0": f"fsgen 0.2.0, same steps ({tt['fsgen_0.2.0_counted']} calls)"}
    fig, ax = plt.subplots(figsize=(9.2, 5.6), dpi=200)
    fig.patch.set_facecolor(surface)
    ax.set_facecolor(surface)
    bar_h, gap = 0.24, 0.03
    vmax = max(max(t[k].values()) for k in colors)
    for i, row in enumerate(PURPOSES):
        for j, key in enumerate(colors):
            v = t[key][row]
            y = i + (j - 1) * (bar_h + gap)
            ax.barh(y, v, height=bar_h, color=colors[key], linewidth=0)
            ax.text(v + 0.35, y, str(v), va="center", ha="left", fontsize=8, color=ink2)
    ax.set_yticks(range(len(PURPOSES)))
    ax.set_yticklabels(PURPOSES, fontsize=9.5, color=ink)
    ax.set_xlim(0, vmax + 3)
    ax.set_ylim(len(PURPOSES) - 0.45, -0.55)
    ax.set_xlabel("Onshape API calls counted against the yearly quota", fontsize=9, color=ink2)
    ax.xaxis.grid(True, color=grid, linewidth=0.8)
    ax.set_axisbelow(True)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(grid)
    ax.tick_params(axis="x", colors=ink2, labelsize=8.5)
    ax.tick_params(axis="y", length=0)
    handles = [plt.Rectangle((0, 0), 1, 1, color=colors[k]) for k in colors]
    ax.legend(handles, [labels[k] for k in colors], loc="lower right", frameon=False, fontsize=9)
    fig.suptitle("Onshape API calls by purpose: PR #176's direct REST work vs. fsgen 0.1 and 0.2.0",
                 x=0.02, ha="left", fontsize=11.5, color=ink, fontweight="bold")
    fig.text(0.02, 0.915, "Same baseplate, same steps: a public document, the 14-feature tree, renders, STEP export, "
             "a version, and the thinner\ntable on a branch. Not shown: the "
             f"{tt['fsgen_0.2.0_extra_test_counted']} calls of 0.2.0's Variable-Studio-only test. "
             "Failed requests (4xx) are free.", fontsize=8.5, color=ink2, ha="left", va="top")
    fig.tight_layout(rect=(0, 0, 1, 0.89))
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, facecolor=surface)
    print("->", path.relative_to(HERE))


if __name__ == "__main__":
    t = tally()
    out = HERE / "results" / "api_calls_by_purpose.json"
    out.write_text(json.dumps(t, indent=1) + "\n")
    print(json.dumps(t, indent=1))
    plot(t, HERE / "renders" / "api_calls_by_purpose.png")
