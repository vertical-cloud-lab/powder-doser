#!/usr/bin/env python3
"""Figure: the citation network of El Kassem et al. (2021), KONA 38:235-250.

(a) The works that cite it, by year and by what they do, linked to the paper; the same group's own papers in orange.
(b) The references the citing works share with it (co-citation counts).
Reads network.json (build_network.py). Writes citation_network.png.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = Path(__file__).resolve().parent
NET = json.loads((HERE / "network.json").read_text())

BLUE, ORANGE = "#2a78d6", "#eb6834"          # categorical slots 1-2 (validated light-mode palette)
INK, INK2, MUTED, EDGE, GRID = "#0b0b0b", "#52514e", "#8a8984", "#c9c8c2", "#ecebe7"
GROUP = {"Bilal El Kassem", "Nizar Salloum", "Thomas Brinz", "Yousef Heider", "Bernd A. Markert", "Bernd Markert"}

# Lanes: what each citing work does, read from titles, abstracts and (where open) full texts.
LANES = [
    ("A", "Calibrates DEM from a\nfeeder or doser response"),
    ("B", "Other DEM calibration\nmethods"),
    ("C", "Dosing and feeding devices,\nno inverse calibration"),
    ("D", "Other uses of DEM"),
]
# doi -> (lane, short label)
WORKS = {
    "10.2320/matertrans.m-m2021806": ("A", "Katagiri 2021: GA calibration,\nvibration feeder (e-waste items)"),
    "10.1016/j.powtec.2020.10.067": ("B", "Westbrink 2020: multi-objective RL"),
    "10.1016/j.powtec.2021.01.029": ("B", "Nasato 2021: coarse-graining + ANN"),
    "10.21660/2023.106.g12219": ("B", "Naito 2023: avalanche, several flows"),
    "10.14356/kona.2024016": ("B", "Lima 2024: rotating disc parameters"),
    "10.3390/polym17202748": ("B", "García Montagut 2025: polymer grains"),
    "10.1016/j.partic.2026.07.019": ("B", "Díaz Muñoz 2026: multi-response, polyhedra"),
    "10.1016/j.jddst.2020.101950": ("C", "El Kassem 2020: 10 powders,\n30 attributes, PCA"),
    "10.1080/10837450.2021.1901915": ("C", "El Kassem 2021: vertical\nloss-in-weight feeder"),
    "10.1063/5.0255757": ("C", "Sementsov 2024: sieve dispenser"),
    "10.1016/j.powtec.2025.121261": ("C", "Gallego 2025: capsule filler"),
    "10.54097/wvbec931": ("C", "Guo 2025: vertical fine screw"),
    "10.1002/nag.3196": ("D", "Heider 2021: poromechanics + NN"),
    "10.3390/min11090978": ("D", "Magalhães 2021-23:\nsamplers (3 works)"),
    "10.11606/d.3.2022.tde-31102022-112806": ("D", None),
    "10.3390/min13111460": ("D", None),
    "10.1002/9783527835935.ch7": ("D", "Zheng 2023: pharma DEM chapter"),
    "10.14356/kona.2024017": ("D", "Hadi 2024: segregation review"),
    "10.1016/j.powtec.2024.120413": ("D", "Salloum 2024: pharma mixer"),
    "10.1016/j.autcon.2024.105617": ("D", "Li 2024: lunar regolith drum"),
    "10.1016/j.apt.2025.105162": ("D", "Fukushima 2026: rotary kiln"),
}
# Publication years as printed (OpenAlex dates some by online-first year)
YEAR = {"10.14356/kona.2024017": 2024, "10.14356/kona.2024016": 2024, "10.1063/5.0255757": 2024}


SHORT_REFS = {
    "A discrete numerical model": "Cundall & Strack 1979: DEM",
    "Review: Calibration of the discrete": "Coetzee 2017: calibration review",
    "Development of a standard calibration": "Roessler 2019: ambiguous parameter sets",
    "A multivariate regression parametric": "El-Kassem 2020: DoE of DEM inputs",
    "Rolling friction as a technique": "Wensrich 2012: rolling friction",
    "Discrete Element Method (DEM) for Industrial": "Marigo & Stitt 2015: calibration",
    "DEM parameter calibration of cohesive bulk": "Roessler 2019: cohesive AoR test",
    "DEM speedup": "Lommen 2014: stiffness speed-up",
    "Ueber die Ber": "Hertz 1882: contact",
    "Calibration of DEM models for granular": "Johnstone 2010: bulk tests",
}


def short_ref(title: str) -> str:
    for k, v in SHORT_REFS.items():
        if title.startswith(k):
            return v
    return title[:34]


def main() -> None:
    citing = {c["doi"]: c for c in NET["citing"] if c.get("doi")}
    fig = plt.figure(figsize=(15.5, 9.2), dpi=150)
    gs = fig.add_gridspec(1, 2, width_ratios=[2.05, 1], wspace=0.55)
    ax = fig.add_subplot(gs[0, 0])
    bx = fig.add_subplot(gs[0, 1])

    # ---- (a) one row per paper, grouped by what it does; x = publication year
    rows = []  # (kind, label, year, own, citations, doi)
    rows.append(("head", "The paper", None, None, None, None))
    rows.append(("focal", "El Kassem 2021 (KONA): vertical micro-auger, one free-flowing\nlactose, 20-run DoE, contour overlay", 2021, True, NET["focal"].get("cited_by_count") or 0, None))
    rows.append(("head", "Earlier papers by the same authors that it builds on", None, None, None, None))
    rows.append(("pre", "El Kassem 2018 (PAMM): auger dosing of pharma powders, DEM", 2018, True, 6, None))
    rows.append(("pre", "El-Kassem 2020 (CPM): DoE of DEM inputs, two lactoses", 2020, True, 39, None))
    seen_magalhaes = False
    for lane, title in LANES:
        rows.append(("head", title.replace("\n", " "), None, None, None, None))
        for doi, (ln, label) in WORKS.items():
            if ln != lane:
                continue
            if label is None:
                continue  # merged into the Magalhaes row
            c = citing.get(doi, {})
            yr = YEAR.get(doi, c.get("year") or 2025)
            own = bool(GROUP & set(c.get("authors") or []))
            if doi == "10.3390/min11090978":
                seen_magalhaes = True
                rows.append(("cite", "Magalhães 2021, 2022, 2023: DEM of ore samplers (3 works)", [2021, 2022, 2023], False,
                             c.get("cited_by_count") or 0, doi))
                continue
            rows.append(("cite", label.replace("\n", " "), yr, own, c.get("cited_by_count") or 0, doi))
        if lane == "A":
            rows.append(("ours", "This work (TMS 2027): tilted auger, 13+ powders, Bayesian\ninference, held-out shear-cell and Hall-flow checks", 2027, None, 0, None))
    n = len(rows)
    ys = {}
    y = n
    for i, r in enumerate(rows):
        y -= 1 if r[0] != "head" else 0.85
        ys[i] = y
    for i, (kind, label, yr, own, cb, doi) in enumerate(rows):
        yy = ys[i]
        if kind == "head":
            ax.text(2017.35, yy, label, fontsize=9.5, fontweight="bold", color=INK, va="center", ha="left")
            ax.axhline(yy - 0.42, color=GRID, lw=0.8, zorder=0)
            continue
        ax.text(2017.25, yy, label, fontsize=8.4, color=INK, va="center", ha="right", linespacing=1.05)
        ax.plot([2017.4, 2027.4], [yy, yy], color="#f3f2ee", lw=0.8, zorder=0)
        if kind == "focal":
            ax.scatter([yr], [yy], s=300, marker="*", color=ORANGE, edgecolor=INK, lw=0.8, zorder=4)
        elif kind == "pre":
            ax.scatter([yr], [yy], s=55, marker="s", facecolor="white", edgecolor=ORANGE, lw=1.6, zorder=3)
        elif kind == "ours":
            ax.scatter([yr], [yy], s=110, marker="D", facecolor="white", edgecolor=INK, lw=1.4, zorder=4)
        else:
            for x in (yr if isinstance(yr, list) else [yr]):
                ax.scatter([x], [yy], s=28 + 45 * math.log10(1 + cb), color=ORANGE if own else BLUE,
                           edgecolor="white", lw=1.0, zorder=3)
    ax.axvline(2021, color=ORANGE, lw=0.8, ls=(0, (2, 3)), alpha=0.6, zorder=0)
    ax.set_xlim(2017.4, 2027.5)
    ax.set_ylim(min(ys.values()) - 0.8, n + 0.2)
    ax.set_yticks([])
    ax.set_xticks(range(2018, 2028))
    ax.xaxis.tick_top()
    ax.tick_params(axis="x", colors=INK2, labelsize=9, length=0)
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.set_title("(a) El Kassem et al. (2021) and the 21 works that cite it (OpenAlex, Semantic Scholar, "
                 "OpenCitations), by what they do", fontsize=11, color=INK, loc="right", pad=24)
    from matplotlib.lines import Line2D
    handles = [
        Line2D([], [], marker="o", ls="", color=BLUE, markersize=7, label="citing work, other authors"),
        Line2D([], [], marker="o", ls="", color=ORANGE, markersize=7, label="citing work, same authors"),
        Line2D([], [], marker="s", ls="", markerfacecolor="white", markeredgecolor=ORANGE, markersize=7,
               label="earlier work it builds on"),
        Line2D([], [], marker="D", ls="", markerfacecolor="white", markeredgecolor=INK, markersize=7,
               label="ours (not yet published)"),
    ]
    ax.legend(handles=handles, loc="upper left", bbox_to_anchor=(-0.02, -0.01), ncol=4, frameon=False,
              fontsize=8.5, labelcolor=INK2, handletextpad=0.3, columnspacing=1.0)

    # ---- (b) co-citation bars
    cc = list(NET["cocitation_counts"].items())[:10]
    labels = [short_ref(t) for t, _ in cc][::-1]
    vals = [k for _, k in cc][::-1]
    bx.barh(range(len(vals)), vals, color=BLUE, height=0.62, zorder=2)
    for i, v in enumerate(vals):
        bx.text(v + 0.2, i, str(v), va="center", fontsize=8.5, color=INK2)
    bx.set_yticks(range(len(vals)))
    bx.set_yticklabels(labels, fontsize=8.5, color=INK)
    bx.set_xlim(0, 21)
    bx.set_xticks([0, 5, 10, 15, 20])
    bx.tick_params(axis="x", colors=INK2, labelsize=8.5, length=0)
    bx.tick_params(axis="y", length=0, pad=4)
    bx.grid(axis="x", color=GRID, lw=0.8, zorder=0)
    for sp in bx.spines.values():
        sp.set_visible(False)
    bx.set_xlabel("of the 21 citing works, how many also cite it", fontsize=9, color=INK2)
    bx.set_title("(b) References the citing works share\nwith the KONA paper", fontsize=11, color=INK,
                 loc="left", pad=24)
    fig.text(0.01, -0.01, f"Retrieved {NET['retrieved_utc'][:10]} with build_network.py. Marker area grows with "
             "log(citations). Groups were assigned from titles, abstracts and the open full texts read through the Pi.",
             fontsize=7.5, color=MUTED)
    fig.savefig(HERE / "citation_network.png", bbox_inches="tight", facecolor="#fcfcfb")
    print("wrote citation_network.png")


if __name__ == "__main__":
    main()
