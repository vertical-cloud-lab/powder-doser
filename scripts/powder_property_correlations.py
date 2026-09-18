#!/usr/bin/env python3
"""Correlate literature-derived powder properties with issue #116 battery responses.

Inputs
------
data/powder-properties/literature_powder_properties.csv
    One row per powder: best-estimate intrinsic properties compiled from
    supplier datasheets / literature (see literature_powder_properties_long.csv
    for per-value sources). These are NOT measurements of our lots.
data/powder-properties/battery_responses.csv
    One row per powder: curated responses from the issue #116 uniform battery
    (feed factors from docs/battery-runs/run-log.csv on the campaign branches,
    tap quanta and speed slopes from the per-run docs).

Outputs
-------
docs/figures/powder-correlations-scatter.png
docs/figures/powder-correlations-heatmap.png
data/powder-properties/correlation_table.md   (Spearman rho / n / p per pair)

Statistics: Spearman rank correlations (n <= 12, literature-valued predictors;
monotone association is the honest claim). Feed factor spans three decades ->
log10. Block G/H errors use |error| on the subset that actually dosed
(no-conveyance and caking failures are excluded, not imputed).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from pathlib import Path
from scipy import stats

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "powder-properties"
FIGS = ROOT / "docs" / "figures"

# --- palette (dataviz reference instance, light mode) ---
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
BASELINE = "#c3c2b7"
BLUE = "#2a78d6"   # slot 1 -> food-safe batch
ORANGE = "#eb6834"  # slot 2 -> metal batch
DIV_NEG = "#2a78d6"
DIV_MID = "#f0efec"
DIV_POS = "#e34948"

SHORT = {
    "salt": "salt",
    "white-rice-flour": "WRF",
    "brown-rice-flour": "BRF",
    "sodium-alginate": "alginate",
    "calcium-lactate": "Ca-lactate",
    "carboxymethyl-cellulose": "CMC",
    "xanthan-gum": "xanthan",
    "sodium-sulfate": "Na2SO4",
    "silicon-110-200": "Si 75-150",
    "silicon-325": "Si <44",
    "alsi10mg": "AlSi10Mg",
    "barium-chloride": "BaCl2",
}

PREDICTORS = [
    ("bulk_density_g_ml", "bulk density (g/mL)"),
    ("tapped_density_g_ml", "tapped density (g/mL)"),
    ("hausner_ratio", "Hausner ratio"),
    ("carr_index_pct", "Carr index (%)"),
    ("d50_um", "d50 (um)"),
    ("angle_repose_deg", "angle of repose (deg)"),
    ("true_density_g_cm3", "true density (g/cm3)"),
    ("moisture_pct", "equilib. moisture (%)"),
]

RESPONSES = [
    ("log10_ff90", "log10 feed factor @90 (mg/rev)"),
    ("log10_ff45", "log10 feed factor @45 (mg/rev)"),
    ("log10_tap45", "log10 tap quantum @45 (mg)"),
    ("speed_slope_pct", "speed slope (% over 6x RPM)"),
    ("absG_err", "|block G err| @1 g (mg, dosed only)"),
    ("absH200_err", "|block H err| @200 mg (mg, dosed only)"),
]


def load() -> pd.DataFrame:
    props = pd.read_csv(DATA / "literature_powder_properties.csv")
    resp = pd.read_csv(DATA / "battery_responses.csv")
    df = props.merge(resp, on="powder_id", validate="1:1")

    # derive flow indices when only densities are present
    hr = df["tapped_density_g_ml"] / df["bulk_density_g_ml"]
    df["hausner_ratio"] = df.get("hausner_ratio", hr).fillna(hr)
    carr = 100.0 * (df["tapped_density_g_ml"] - df["bulk_density_g_ml"]) / df["tapped_density_g_ml"]
    df["carr_index_pct"] = df.get("carr_index_pct", carr).fillna(carr)

    df["log10_ff90"] = np.log10(df["ff90_mg_per_rev"])
    df["log10_ff45"] = np.log10(df["ff45_mg_per_rev"].where(df["ff45_mg_per_rev"] > 0))
    df["log10_tap45"] = np.log10(df["tap45_mg_per_tap"])
    dosed_g = df["blockG_outcome"].eq("ok")
    df["absG_err"] = df["blockG_mean_err_mg"].abs().where(dosed_g)
    dosed_h = dosed_g & df["blockH_err200_mg"].notna()
    df["absH200_err"] = df["blockH_err200_mg"].abs().where(dosed_h)
    # density-normalised conveying: volume displaced per revolution
    df["vol90_ul_per_rev"] = df["ff90_mg_per_rev"] / df["bulk_density_g_ml"]
    df["label"] = df["powder_id"].map(SHORT)
    return df


def spearman_table(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for pcol, pname in PREDICTORS:
        for rcol, rname in RESPONSES:
            sub = df[[pcol, rcol]].dropna()
            n = len(sub)
            if n < 4:
                rows.append({"predictor": pname, "response": rname, "n": n,
                             "rho": np.nan, "p": np.nan})
                continue
            rho, p = stats.spearmanr(sub[pcol], sub[rcol])
            rows.append({"predictor": pname, "response": rname, "n": n,
                         "rho": rho, "p": p})
    return pd.DataFrame(rows)


def style_axis(ax):
    ax.set_facecolor(SURFACE)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(BASELINE)
    ax.tick_params(colors=MUTED, labelsize=8)
    ax.grid(True, color=GRID, linewidth=0.7, zorder=0)
    ax.set_axisbelow(True)


def label_points(ax, x, y, labels, fontsize=7.5):
    for xi, yi, li in zip(x, y, labels):
        if np.isnan(xi) or np.isnan(yi):
            continue
        ax.annotate(li, (xi, yi), xytext=(4, 4), textcoords="offset points",
                    fontsize=fontsize, color=INK2, zorder=5)


def scatter_panel(ax, df, xcol, ycol, xlabel, ylabel, logy=True):
    for batch, color in (("food-safe-2026-08", BLUE), ("metal-2026-08", ORANGE)):
        sub = df[df["batch"] == batch]
        conveys = sub["conveys"].astype(str).eq("True")
        ax.scatter(sub.loc[conveys, xcol], sub.loc[conveys, ycol], s=55,
                   color=color, edgecolors=SURFACE, linewidths=1.2, zorder=4,
                   label=batch.replace("-2026-08", ""))
        ax.scatter(sub.loc[~conveys, xcol], sub.loc[~conveys, ycol], s=60,
                   color=color, marker="X", edgecolors=SURFACE, linewidths=0.8,
                   zorder=4)
    if logy:
        ax.set_yscale("log")
    label_points(ax, df[xcol].to_numpy(), df[ycol].to_numpy(), df["label"])
    sub = df[[xcol, ycol]].dropna()
    if len(sub) >= 4:
        rho, p = stats.spearmanr(sub[xcol], sub[ycol])
        ax.text(0.02, 0.98, f"Spearman rho = {rho:+.2f}\nn = {len(sub)}, p = {p:.3f}",
                transform=ax.transAxes, va="top", fontsize=8, color=INK)
    ax.set_xlabel(xlabel, fontsize=9, color=INK2)
    ax.set_ylabel(ylabel, fontsize=9, color=INK2)
    style_axis(ax)


def make_scatter_figure(df: pd.DataFrame):
    fig, axes = plt.subplots(2, 2, figsize=(11, 8.6))
    fig.patch.set_facecolor(SURFACE)

    scatter_panel(axes[0, 0], df, "bulk_density_g_ml", "ff90_mg_per_rev",
                  "literature bulk density (g/mL)", "feed factor @90 deg (mg/rev, log)")
    scatter_panel(axes[0, 1], df, "d50_um", "ff90_mg_per_rev",
                  "literature d50 (um)", "feed factor @90 deg (mg/rev, log)")
    axes[0, 1].set_xscale("log")
    scatter_panel(axes[1, 0], df, "hausner_ratio", "ff90_mg_per_rev",
                  "literature Hausner ratio", "feed factor @90 deg (mg/rev, log)")
    scatter_panel(axes[1, 1], df, "carr_index_pct", "tap45_mg_per_tap",
                  "literature Carr index (%)", "tap quantum @45 deg (mg/tap, log)")

    handles, labels_ = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels_, loc="lower center", ncol=2, frameon=False,
               fontsize=9, labelcolor=INK2)
    fig.suptitle("Issue #116 battery responses vs literature powder properties\n"
                 "(X markers: powders that did not convey; properties are datasheet/literature values, not lot measurements)",
                 fontsize=11, color=INK)
    fig.tight_layout(rect=(0, 0.04, 1, 0.93))
    out = FIGS / "powder-correlations-scatter.png"
    fig.savefig(out, dpi=180, facecolor=SURFACE)
    plt.close(fig)
    return out


def make_heatmap(tbl: pd.DataFrame):
    piv_rho = tbl.pivot(index="predictor", columns="response", values="rho")
    piv_n = tbl.pivot(index="predictor", columns="response", values="n")
    piv_p = tbl.pivot(index="predictor", columns="response", values="p")
    # keep declared order
    piv_rho = piv_rho.reindex(index=[p[1] for p in PREDICTORS], columns=[r[1] for r in RESPONSES])
    piv_n = piv_n.reindex_like(piv_rho)
    piv_p = piv_p.reindex_like(piv_rho)

    cmap = LinearSegmentedColormap.from_list("div", [DIV_NEG, DIV_MID, DIV_POS])
    fig, ax = plt.subplots(figsize=(10.5, 6.2))
    fig.patch.set_facecolor(SURFACE)
    im = ax.imshow(piv_rho.to_numpy(dtype=float), cmap=cmap, vmin=-1, vmax=1, aspect="auto")
    ax.set_xticks(range(len(piv_rho.columns)))
    ax.set_xticklabels([c.replace(" (", "\n(") for c in piv_rho.columns], fontsize=8, color=INK2)
    ax.set_yticks(range(len(piv_rho.index)))
    ax.set_yticklabels(piv_rho.index, fontsize=9, color=INK2)
    ax.tick_params(colors=MUTED)
    for i in range(piv_rho.shape[0]):
        for j in range(piv_rho.shape[1]):
            rho = piv_rho.iat[i, j]
            n = piv_n.iat[i, j]
            p = piv_p.iat[i, j]
            if np.isnan(rho):
                txt, color = "n<4", MUTED
            else:
                star = "*" if (p is not None and p < 0.05) else ""
                txt = f"{rho:+.2f}{star}\nn={int(n)}"
                color = "#ffffff" if abs(rho) > 0.62 else INK
            ax.text(j, i, txt, ha="center", va="center", fontsize=8, color=color)
    cbar = fig.colorbar(im, ax=ax, shrink=0.85)
    cbar.set_label("Spearman rho", fontsize=9, color=INK2)
    cbar.ax.tick_params(colors=MUTED, labelsize=8)
    cbar.outline.set_edgecolor(BASELINE)
    ax.set_title("Spearman rank correlation: literature properties (rows) vs battery responses (columns)\n"
                 "* p < 0.05 uncorrected; exploratory, n <= 12", fontsize=11, color=INK)
    fig.tight_layout()
    out = FIGS / "powder-correlations-heatmap.png"
    fig.savefig(out, dpi=180, facecolor=SURFACE)
    plt.close(fig)
    return out


def main():
    df = load()
    tbl = spearman_table(df)
    FIGS.mkdir(parents=True, exist_ok=True)

    out_md = DATA / "correlation_table.md"
    with out_md.open("w") as fh:
        fh.write("# Spearman correlations: literature properties vs #116 battery responses\n\n")
        fh.write("Generated by `scripts/powder_property_correlations.py`. ")
        fh.write("Exploratory (n <= 12, uncorrected p, literature-valued predictors).\n\n")
        fh.write("| predictor | response | n | Spearman rho | p |\n|---|---|---|---|---|\n")
        for _, r in tbl.sort_values("p").iterrows():
            rho = "" if np.isnan(r["rho"]) else f"{r['rho']:+.2f}"
            p = "" if (isinstance(r["p"], float) and np.isnan(r["p"])) else f"{r['p']:.3f}"
            bold = "**" if (p and float(r["p"]) < 0.05) else ""
            fh.write(f"| {r['predictor']} | {r['response']} | {r['n']} | {bold}{rho}{bold} | {bold}{p}{bold} |\n")

    s = make_scatter_figure(df)
    h = make_heatmap(tbl)
    print("wrote", out_md, s, h)

    # console: strongest pairs + volumetric check
    print("\nTop |rho| (n>=6):")
    top = tbl[(tbl["n"] >= 6)].assign(a=lambda d: d["rho"].abs()).sort_values("a", ascending=False)
    print(top.head(12).to_string(index=False))
    sub = df[["vol90_ul_per_rev", "hausner_ratio", "d50_um"]].dropna()
    if len(sub) >= 4:
        for col in ("hausner_ratio", "d50_um"):
            rho, p = stats.spearmanr(np.log10(sub["vol90_ul_per_rev"].clip(lower=0.01)), sub[col])
            print(f"log10(volume/rev @90) vs {col}: rho={rho:+.2f} p={p:.3f} n={len(sub)}")


if __name__ == "__main__":
    main()
