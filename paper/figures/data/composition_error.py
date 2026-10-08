#!/usr/bin/env python3
"""Composition error allowed by the per-dose acceptance limits (SI table).

The main text scores doses against acceptance limits of +/-10 % of the
requested mass below 100 mg and +/-5 % at or above it, and states that these
limits keep the composition error from dosing below one atomic percent for a
typical five-component blend.  This script tests that statement for an
equimolar five-component blend and for blends from the Vertical Cloud Lab
alloy workflow, at the batch sizes planned for it (10, 100 and 500 g), and
writes

  composition_error.csv            one row per blend x batch x basis x element
  composition_error_table.tex      compact booktabs table (\\label{tbl:comperror})

Run from anywhere:  python paper/figures/data/composition_error.py

Model
-----
A blend is made from feedstocks f (elemental or pre-alloyed powders).
Feedstock f has nominal mass m_f and element mass fractions c_fk, so element k
receives e_k = sum_f m_f c_fk.  The mole fraction of k is x_k = n_k / N with
n_k = e_k / M_k and N = sum_j n_j.  If feedstock f is delivered with a
relative mass error eps_f, then to first order

    delta x_k = sum_f S_kf eps_f,
    S_kf = (m_f / N) * (c_fk / M_k - x_k * sum_j c_fj / M_j).

For elemental feedstocks (c_fk = 1 if f = k, else 0) this reduces to

    delta x_i = x_i * (eps_i - sum_j x_j eps_j),

so with a common limit L the worst case is 2 x_i (1 - x_i) L (1.6 at% for
x_i = 0.2 and L = 5 %).  Mass fractions w_k follow from the same algebra with
every M set to 1 (column basis = "wt"; basis = "at" is atomic percent).

Columns (percentage points of at% or wt%; the table shows the largest value
over the elements of each blend)
  worst_pct            first order: every eps_f at its limit L_f (10 % if
                       m_f < 100 mg, else 5 %) with the signs that maximise
                       |delta x_k|, i.e. sum_f |S_kf| L_f.
  worst_exact_pct      the same without linearising: the largest shift over
                       every sign pattern of the feedstock errors (table value).
  sd_uniform_pct       independent errors uniform within the limits,
                       sigma_f = L_f / sqrt(3).
  sd_measured_pct      independent errors with the measured root-mean-square
                       relative error of the valid doses that finished within
                       their limit (doses_all.csv), taken at the tested target
                       nearest to and not above the feedstock mass (50 mg,
                       200 mg or 1 g).  Using the 1 g value for heavier
                       feedstocks is conservative if dose errors are
                       independent or roughly fixed in mg, as the controller's
                       +/-5 mg stopping band suggests.
  sd_measured_research_pct   as above, for the three research-relevant powders
                       (AlSi10Mg, coarse silicon, sodium sulfate) only.
  sd_balance_0p1mg_pct, sd_balance_5mg_pct
                       composition computed from the recorded masses, so the
                       only error is the balance uncertainty u of each recorded
                       feedstock mass: eps_f = u / m_f, for u = 0.1 mg
                       (readability of the A&D HR-100A) and u = 5 mg (a noisy
                       bench, e.g. a fume hood with airflow).
  p_within_1pt_uniform, p_all_within_1pt_uniform
                       Monte Carlo (exact, 200 000 draws, uniform errors):
                       probability that this element, or every element, ends
                       within 1 percentage point of its nominal value.

Notes
-----
* A feedstock built from several doses that each pass is also within the
  limit: if |m_k - t_k| <= 0.05 t_k for every dose k, the summed mass is within
  5 % of the summed target.
* Nominal feedstock compositions: AlSi10Mg at the midpoints of its Si 9-11 and
  Mg 0.20-0.45 wt% ranges (as in byu-vcl thermo-calc-100g-mixture-composition.md);
  Al-10Zr master alloy as 10 wt% Zr; every other feedstock as the pure element.
* Atomic weights: IUPAC standard atomic weights, abridged.
"""
from __future__ import annotations

import csv
import itertools
import math
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
DOSES_CSV = HERE / "doses_all.csv"
OUT_CSV = HERE / "composition_error.csv"
OUT_TEX = HERE / "composition_error_table.tex"

BATCHES_G = (10.0, 100.0, 500.0)
BALANCE_U_MG = (0.1, 5.0)
SMALL_DOSE_MG = 100.0  # below this the +/-10 % limit applies
LIMIT_SMALL, LIMIT_LARGE = 0.10, 0.05
RESEARCH_POWDERS = ("alsi10mg", "silicon-110-200", "sodium-sulfate")

# g/mol, IUPAC standard atomic weights (abridged)
M = {
    "Al": 26.982, "Si": 28.085, "Mg": 24.305, "Mn": 54.938, "Cr": 51.996,
    "Zr": 91.224, "Ti": 47.867, "Co": 58.933, "Fe": 55.845, "Ni": 58.693,
}

# element mass fractions of each feedstock
FEEDSTOCK = {
    "Al": {"Al": 1.0},
    "Si": {"Si": 1.0},
    "Mn": {"Mn": 1.0},
    "Cr": {"Cr": 1.0},
    "Ti": {"Ti": 1.0},
    "Co": {"Co": 1.0},
    "Fe": {"Fe": 1.0},
    "Ni": {"Ni": 1.0},
    "AlSi10Mg": {"Al": 0.89675, "Si": 0.100, "Mg": 0.00325},
    "Al-10Zr": {"Al": 0.90, "Zr": 0.10},
}


def equimolar(elements):
    """Feedstock mass fractions for an equimolar blend of pure elements."""
    tot = sum(M[e] for e in elements)
    return {e: M[e] / tot for e in elements}


# Blends: feedstock mass fractions (normalised below) plus labels.
BLENDS = [
    {
        "key": "equimolar5",
        "label": "Equimolar AlCoCrFeNi",
        "tex": "Equimolar AlCoCrFeNi",
        "source": "five-component blend named in the main text; the at% dosing "
                  "results hold for any equimolar blend of five pure elements",
        "feed": equimolar(["Al", "Co", "Cr", "Fe", "Ni"]),
    },
    {
        "key": "al_mn_cr_zr_ti",
        "label": "Al-5Mn-2Cr-2Zr-0.5Ti (wt%), Zr as Al-10Zr",
        "tex": "Al-5Mn-2Cr-2Zr-0.5Ti",
        "source": "byu-vcl powder-acquisition/purchase-quantity-model.md, "
                  "Al-Mn-Cr-Zr(+Ti) family at its maximum solute levels",
        "feed": {"Al": 72.5, "Al-10Zr": 20.0, "Mn": 5.0, "Cr": 2.0, "Ti": 0.5},
    },
    {
        "key": "al_si_hypereutectic",
        "label": "Al-24Si-0.1Mg (wt%) from Al + Si + AlSi10Mg",
        "tex": "Al-24Si-0.1Mg",
        "source": "byu-vcl issue #16, 100 g atomizer test blend "
                  "(38.164 g Al, 20.304 g Si, 41.547 g AlSi10Mg)",
        "feed": {"Al": 38.164, "Si": 20.3042, "AlSi10Mg": 41.5472},
    },
]


# --------------------------------------------------------------------------
# composition algebra
# --------------------------------------------------------------------------
def setup(feed_g: dict[str, float]):
    """Return feedstock list, element list, masses (g) and C matrix (f x k)."""
    feeds = list(feed_g)
    def element_mass(e):
        return sum(feed_g[f] * FEEDSTOCK[f].get(e, 0.0) for f in feeds)

    # heaviest element first; ties (e.g. 2 wt% Cr and 2 wt% Zr) by name
    elems = sorted({k for f in feeds for k in FEEDSTOCK[f]},
                   key=lambda e: (-round(element_mass(e), 9), e))
    m = np.array([feed_g[f] for f in feeds], dtype=float)
    C = np.array([[FEEDSTOCK[f].get(k, 0.0) for k in elems] for f in feeds])
    return feeds, elems, m, C


def fractions(m, C, molar):
    """Mole (molar = atomic weights) or mass (molar = ones) fractions."""
    n = (m[:, None] * C).sum(axis=0) / molar
    return n / n.sum()


def sensitivity(m, C, molar):
    """S[k, f] = d x_k / d eps_f at eps = 0 (x = mole or mass fraction)."""
    n = (m[:, None] * C).sum(axis=0) / molar
    N = n.sum()
    x = n / N
    a = C / molar[None, :]                 # (f, k): c_fk / M_k
    rowsum = a.sum(axis=1)                 # (f,):  sum_j c_fj / M_j
    S = (m[:, None] / N) * (a - x[None, :] * rowsum[:, None])   # (f, k)
    return S.T                             # (k, f)


def mc_within(m, C, molar, limits, threshold=0.01, n=200_000, seed=1):
    """Monte Carlo (exact, not linearised) with errors uniform within the limits.

    Returns per-element P(|delta x_k| < threshold) and P(all elements within).
    """
    rng = np.random.default_rng(seed)
    eps = rng.uniform(-1.0, 1.0, size=(n, len(m))) * limits[None, :]
    x0 = fractions(m, C, molar)
    nk = ((m[None, :] * (1.0 + eps)) @ C) / molar[None, :]
    dx = np.abs(nk / nk.sum(axis=1, keepdims=True) - x0[None, :])
    inside = dx < threshold
    return inside.mean(axis=0), float(inside.all(axis=1).mean())


def exact_worst(m, C, molar, limits):
    """Exact max |delta x_k| over every sign pattern of the feedstock errors."""
    x0 = fractions(m, C, molar)
    worst = np.zeros_like(x0)
    for signs in itertools.product((-1.0, 1.0), repeat=len(m)):
        x = fractions(m * (1.0 + np.array(signs) * limits), C, molar)
        worst = np.maximum(worst, np.abs(x - x0))
    return worst


# --------------------------------------------------------------------------
# measured dose errors
# --------------------------------------------------------------------------
def measured_errors():
    """RMS / SD of the relative error (fraction) of valid doses, per target."""
    rows = list(csv.DictReader(DOSES_CSV.open()))
    out = {}
    for target in (50.0, 200.0, 1000.0):
        limit = LIMIT_SMALL if target < SMALL_DOSE_MG else LIMIT_LARGE
        valid = [r for r in rows
                 if r["dose_valid"] == "True" and float(r["target_mg"]) == target]
        groups = {
            "accepted_all": [r for r in valid
                             if abs(float(r["error_pct"])) <= 100 * limit],
            "research_all_valid": [r for r in valid
                                   if r["powder_id"] in RESEARCH_POWDERS],
            "research_accepted": [r for r in valid
                                  if r["powder_id"] in RESEARCH_POWDERS
                                  and abs(float(r["error_pct"])) <= 100 * limit],
        }
        for name, sel in groups.items():
            e = np.array([float(r["error_pct"]) / 100 for r in sel])
            out[(target, name)] = {
                "n": len(e),
                "n_valid": len(valid),
                "mean": float(e.mean()) if len(e) else math.nan,
                "sd": float(e.std(ddof=1)) if len(e) > 1 else math.nan,
                "rms": float(np.sqrt((e ** 2).mean())) if len(e) else math.nan,
                "max_abs": float(np.abs(e).max()) if len(e) else math.nan,
            }
    return out


def measured_rms_for_mass(mass_mg, meas, group="accepted_all"):
    """Measured RMS relative error at the tested target nearest below mass."""
    if mass_mg < 200.0:
        target = 50.0
    elif mass_mg < 1000.0:
        target = 200.0
    else:
        target = 1000.0
    return meas[(target, group)]["rms"], target


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------
def analyse():
    meas = measured_errors()
    records = []
    for blend in BLENDS:
        total = sum(blend["feed"].values())
        frac = {f: v / total for f, v in blend["feed"].items()}
        for batch in BATCHES_G:
            feed_g = {f: w * batch for f, w in frac.items()}
            feeds, elems, m, C = setup(feed_g)
            m_mg = 1000.0 * m
            limits = np.where(m_mg < SMALL_DOSE_MG, LIMIT_SMALL, LIMIT_LARGE)
            sig_unif = limits / math.sqrt(3.0)
            sig_meas = np.array([measured_rms_for_mass(v, meas)[0] for v in m_mg])
            sig_meas_res = np.array(
                [measured_rms_for_mass(v, meas, "research_accepted")[0] for v in m_mg])
            imin = int(np.argmin(m))
            for basis, molar in (("at", np.array([M[e] for e in elems])),
                                 ("wt", np.ones(len(elems)))):
                x0 = fractions(m, C, molar)
                S = sensitivity(m, C, molar)
                worst_lin = np.abs(S) @ limits
                worst_ex = exact_worst(m, C, molar, limits)
                sd_unif = np.sqrt((S ** 2) @ sig_unif ** 2)
                sd_meas = np.sqrt((S ** 2) @ sig_meas ** 2)
                sd_meas_res = np.sqrt((S ** 2) @ sig_meas_res ** 2)
                sd_bal = {u: np.sqrt((S ** 2) @ (u / m_mg) ** 2) for u in BALANCE_U_MG}
                p_el, p_all = mc_within(m, C, molar, limits)
                for k, el in enumerate(elems):
                    records.append({
                        "blend": blend["key"],
                        "blend_label": blend["label"],
                        "batch_g": batch,
                        "basis": basis,
                        "element": el,
                        "nominal_pct": 100 * x0[k],
                        "worst_pct": 100 * worst_lin[k],
                        "worst_exact_pct": 100 * worst_ex[k],
                        "sd_uniform_pct": 100 * sd_unif[k],
                        "sd_measured_pct": 100 * sd_meas[k],
                        "sd_measured_research_pct": 100 * sd_meas_res[k],
                        "sd_balance_0p1mg_pct": 100 * sd_bal[0.1][k],
                        "sd_balance_5mg_pct": 100 * sd_bal[5.0][k],
                        "p_within_1pt_uniform": float(p_el[k]),
                        "p_all_within_1pt_uniform": p_all,
                        "feedstocks": "; ".join(
                            f"{f} {v:.4g} g (limit {100 * L:.0f}%)"
                            for f, v, L in zip(feeds, m, limits)),
                        "smallest_feedstock": feeds[imin],
                        "smallest_feedstock_mg": m_mg[imin],
                        "smallest_limit_pct": 100 * limits[imin],
                        "source": blend["source"],
                    })
    return records, meas


def write_csv(records):
    keys = list(records[0])
    with OUT_CSV.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        for r in records:
            w.writerow({k: (f"{v:.6g}" if isinstance(v, float) else v)
                        for k, v in r.items()})


def summary(records):
    """Largest value over elements, per blend x batch x basis."""
    out = {}
    for r in records:
        key = (r["blend"], r["batch_g"], r["basis"])
        s = out.setdefault(key, {"r": r, "worst_el": None,
                                 "p_all": r["p_all_within_1pt_uniform"]})
        for col in ("worst_pct", "worst_exact_pct", "sd_uniform_pct",
                    "sd_measured_pct", "sd_measured_research_pct",
                    "sd_balance_0p1mg_pct", "sd_balance_5mg_pct"):
            if col not in s or r[col] > s[col]:
                s[col] = r[col]
                if col == "worst_pct":
                    s["worst_el"] = r["element"]
    return out


def fmt(v):
    if v < 0.001:
        return "$<$0.001"
    if v < 0.01:
        return f"{v:.3f}"
    return f"{v:.2f}"


def fmt_g(grams):
    """Feedstock mass in g to three significant figures."""
    if grams < 1:
        return f"{grams:.3f}"
    if grams < 10:
        return f"{grams:.2f}"
    if grams < 100:
        return f"{grams:.1f}"
    return f"{grams:.0f}"


def write_tex(records, meas):
    s = summary(records)
    acc = {t: meas[(t, "accepted_all")] for t in (50.0, 200.0, 1000.0)}
    lines = [
        "% Generated by paper/figures/data/composition_error.py -- do not edit by hand.",
        "\\begin{table}[htbp]",
        "\\centering",
        "\\small",
        "\\setlength{\\tabcolsep}{4pt}",
        "\\caption{Composition error added by dosing, given as the largest absolute "
        "error of any element in the blend. Each feedstock is dosed within its "
        "acceptance limit ($\\pm$10\\% of its mass below 100~mg, $\\pm$5\\% at or "
        "above). \\emph{Worst}: every feedstock at its limit, with the signs that "
        "give the largest error. \\emph{SD}: independent errors, either uniform "
        "within the limit (SD equal to the limit divided by $\\sqrt{3}$) or with the "
        "measured root-mean-square error of accepted doses "
        f"({100 * acc[50.0]['rms']:.1f}\\%, {100 * acc[200.0]['rms']:.1f}\\%, and "
        f"{100 * acc[1000.0]['rms']:.1f}\\% at 50~mg, 200~mg, and 1~g). "
        "\\emph{Recorded masses}: SD when the composition is calculated from the "
        "recorded masses, each with a standard uncertainty of 0.1~mg or 5~mg. "
        "Al-5Mn-2Cr-2Zr-0.5Ti (wt\\%, Zr added as an Al-10Zr master alloy) and "
        "Al-24Si-0.1Mg (made from Al, Si, and AlSi10Mg for atomization trials) "
        "are blends from our alloy-discovery workflow. Values for every element are in "
        "\\texttt{paper/figures/data/composition\\_error.csv}.}",
        "\\label{tbl:comperror}",
        "\\begin{tabular}{@{}lrrrrrrrr@{}}",
        "\\toprule",
        " & & & \\multicolumn{4}{c}{Dosing within the limits} & "
        "\\multicolumn{2}{c}{Recorded masses} \\\\",
        "\\cmidrule(lr){4-7}\\cmidrule(l){8-9}",
        " & Batch & Smallest & Worst & Worst & SD, & SD, & 0.1~mg & 5~mg \\\\",
        "Blend & (g) & feedstock (g) & (at\\%) & (wt\\%) & uniform (at\\%) & "
        "measured (at\\%) & (at\\%) & (at\\%) \\\\",
        "\\midrule",
    ]
    for bi, blend in enumerate(BLENDS):
        for i, batch in enumerate(BATCHES_G):
            a = s[(blend["key"], batch, "at")]
            w = s[(blend["key"], batch, "wt")]
            r = a["r"]
            small = f"{fmt_g(r['smallest_feedstock_mg'] / 1000)} ({r['smallest_feedstock']})"
            name = blend["tex"] if i == 0 else ""
            lines.append(
                f"{name} & {batch:.0f} & {small} & {fmt(a['worst_exact_pct'])} & "
                f"{fmt(w['worst_exact_pct'])} & {fmt(a['sd_uniform_pct'])} & "
                f"{fmt(a['sd_measured_pct'])} & {fmt(a['sd_balance_0p1mg_pct'])} & "
                f"{fmt(a['sd_balance_5mg_pct'])} \\\\")
        if bi < len(BLENDS) - 1:
            lines.append("\\midrule")
    lines += ["\\bottomrule", "\\end{tabular}", "\\end{table}", ""]
    OUT_TEX.write_text("\n".join(lines))


def report(records, meas):
    print("Measured relative errors of valid doses (fractions):")
    for (t, g), v in sorted(meas.items()):
        print(f"  {t:6.0f} mg {g:20s} n={v['n']:2d}/{v['n_valid']:2d} "
              f"mean={v['mean']:+.4f} sd={v['sd']:.4f} rms={v['rms']:.4f} "
              f"max|e|={v['max_abs']:.4f}")
    s = summary(records)
    print("\nLargest element error per blend x batch (percentage points):")
    for (b, batch, basis), v in s.items():
        print(f"  {b:20s} {batch:5.0f} g {basis}  worst={v['worst_pct']:.3f} "
              f"(exact {v['worst_exact_pct']:.3f}, {v['worst_el']})  "
              f"sd_unif={v['sd_uniform_pct']:.3f}  sd_meas={v['sd_measured_pct']:.3f}  "
              f"sd_meas_research={v['sd_measured_research_pct']:.3f}  "
              f"bal0.1={v['sd_balance_0p1mg_pct']:.2e}  bal5={v['sd_balance_5mg_pct']:.2e}  "
              f"P(all<1pt)={v['p_all']:.3f}  "
              f"smallest={v['r']['smallest_feedstock']} {v['r']['smallest_feedstock_mg']:.0f} mg")


def main():
    records, meas = analyse()
    write_csv(records)
    write_tex(records, meas)
    report(records, meas)
    print(f"\nwrote {OUT_CSV.name} ({len(records)} rows) and {OUT_TEX.name}")


if __name__ == "__main__":
    main()
