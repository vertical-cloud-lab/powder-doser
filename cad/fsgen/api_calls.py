"""Onshape API calls: fsgen (this folder) vs. the direct REST API work in PR #176.

Reads the two call logs, sorts every counted call (2xx/3xx; Onshape doesn't count 4xx) into
what it was for, and writes ``results/api_calls_by_purpose.json`` and
``renders/api_calls_by_purpose.png``. No Onshape calls.

    python api_calls.py

* PR #176: ``results/pr176_api_calls.jsonl``, copied from
  ``cad/text-to-cad/onshape/api_calls.jsonl`` on ``claude/issue-172-20261003-2216`` (ae09e5f).
* fsgen: ``.fsgen_api_ledger.jsonl`` (main workspace) and
  ``branch_thinner_table/.fsgen_api_ledger.jsonl`` (the branch), written by fsgen's client.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
PURPOSES = ["Setup (access, document)", "Build or edit geometry", "Look up ids, faces, features",
            "Checks (box, volume, status)", "Rendered views", "STEP export", "Versions"]


def purpose_direct(row: dict) -> str:
    """PR #176's client logged method + path, plus the step ("run") it belonged to."""
    m, p, run = row["method"], row["path"], row["run"]
    if p in ("/users/sessioninfo", "/companies") or (m == "POST" and p == "/documents"):
        return PURPOSES[0]
    if p.startswith("/blobelements") or (p.startswith("/translations") and run == "import"):
        return PURPOSES[1]
    if p.endswith(("/bodydetails", "/featurespecs", "/elements")) or (m == "GET" and p.endswith("/features")) \
            or (m == "GET" and re.fullmatch(r"/parts/d/\w+/w/\w+/e/\w+", p)):
        return PURPOSES[2]
    if m == "POST" and ("/features" in p or p.startswith("/featurestudios") or p.endswith("/workspaces")):
        return PURPOSES[1]
    if p.endswith(("/boundingboxes", "/massproperties")):
        return PURPOSES[3]
    if p.endswith("/shadedviews"):
        return PURPOSES[4]
    if p.endswith("/translations") or p.startswith("/translations") or "/externaldata/" in p:
        return PURPOSES[5]
    if p.endswith("/versions"):
        return PURPOSES[6]
    raise ValueError(f"unclassified PR #176 call: {m} {p}")


def purpose_fsgen(row: dict) -> str:
    """fsgen's ledger keeps 'METHOD endpoint/{id}/...' only (ids masked)."""
    c = row["call"]
    if c in ("GET companies", "POST documents"):
        return PURPOSES[0]
    if c.endswith("/featurescript") or c.endswith("/massproperties"):
        return PURPOSES[3]   # featurescript = fsgen's batched feature-status check / error diagnosis
    if c.startswith("GET") and c.endswith("/features"):
        return PURPOSES[2]
    if c.endswith("/translations") or "translations/{tid}" in c or "externaldata" in c:
        return PURPOSES[5]
    if c.startswith("POST") and (c.startswith("POST partstudios") or c.startswith("POST variables")
                                 or c.endswith("/workspaces")):
        return PURPOSES[1]
    if c.endswith("/shadedviews"):
        return PURPOSES[4]
    if c.endswith("/versions"):
        return PURPOSES[6]
    raise ValueError(f"unclassified fsgen call: {c}")


def tally() -> dict:
    direct = [json.loads(l) for l in (HERE / "results" / "pr176_api_calls.jsonl").read_text().splitlines()]
    fsgen = []
    for ledger in (HERE / ".fsgen_api_ledger.jsonl", HERE / "branch_thinner_table" / ".fsgen_api_ledger.jsonl"):
        fsgen += [json.loads(l) for l in ledger.read_text().splitlines()]
    out = {"direct_pr176": {k: 0 for k in PURPOSES}, "fsgen": {k: 0 for k in PURPOSES}}
    for r in direct:
        if r["status"] < 400:
            out["direct_pr176"][purpose_direct(r)] += 1
    for r in fsgen:
        if r["counted"]:
            out["fsgen"][purpose_fsgen(r)] += 1
    out["totals"] = {"direct_pr176_logged": len(direct),
                     "direct_pr176_counted": sum(out["direct_pr176"].values()),
                     "fsgen_logged": len(fsgen),
                     "fsgen_counted": sum(out["fsgen"].values())}
    return out


def plot(t: dict, path: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    surface, ink, ink2, grid = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
    colors = {"direct_pr176": "#2a78d6", "fsgen": "#eb6834"}   # categorical slots 1 and 2
    labels = {"direct_pr176": f"Direct REST API, PR #176 ({t['totals']['direct_pr176_counted']} calls)",
              "fsgen": f"fsgen, this PR ({t['totals']['fsgen_counted']} calls)"}
    rows = PURPOSES
    fig, ax = plt.subplots(figsize=(9.2, 5.0), dpi=200)
    fig.patch.set_facecolor(surface)
    ax.set_facecolor(surface)
    bar_h, gap = 0.32, 0.04
    vmax = max(max(t[k].values()) for k in colors)
    for i, row in enumerate(rows):
        for j, key in enumerate(colors):
            v = t[key][row]
            y = i + (j - 0.5) * (bar_h + gap)
            ax.barh(y, v, height=bar_h, color=colors[key], linewidth=0)
            ax.text(v + 0.35, y, str(v), va="center", ha="left", fontsize=8.5, color=ink2)
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels(rows, fontsize=9.5, color=ink)
    ax.invert_yaxis()
    ax.set_xlim(0, vmax + 3)
    ax.set_ylim(len(rows) - 0.4, -0.6)
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
    fig.suptitle("Onshape API calls by purpose: PR #176's direct REST work vs. fsgen",
                 x=0.02, ha="left", fontsize=11.5, color=ink, fontweight="bold")
    fig.text(0.02, 0.905, "PR #176 imported the 100-solid assembly as STEP and edited it in two workspaces; "
             "fsgen built the baseplate as a\n14-feature native tree and made the thinner-table edit on a branch. "
             "Failed requests (4xx) are free and not shown.", fontsize=8.5, color=ink2, ha="left", va="top")
    fig.tight_layout(rect=(0, 0, 1, 0.88))
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, facecolor=surface)
    print("->", path.relative_to(HERE))


if __name__ == "__main__":
    t = tally()
    (HERE / "results" / "api_calls_by_purpose.json").write_text(json.dumps(t, indent=1) + "\n")
    print(json.dumps(t, indent=1))
    plot(t, HERE / "renders" / "api_calls_by_purpose.png")
