# Optimization manuscript (issue #179)

Draft of the second powder-doser paper: per-powder calibration of the auger doser as multi-objective,
multi-task Bayesian optimization, and dosing response as a probe of powder flow (DEM-based inference of
effective cohesion and friction, checked against standard flow tests). Target: *Additive Manufacturing*
(Elsevier, `elsarticle`).

| File | What |
|---|---|
| [`main.tex`](main.tex) / [`main.pdf`](main.pdf) | The draft |
| [`OUTLINE.md`](OUTLINE.md) | Outline, claim-by-claim status, and **everything that still needs to be prepared** |
| [`refs.bib`](refs.bib), [`references_validation.md`](references_validation.md) | Bibliography (DOI entries built from Crossref metadata) and the per-entry check |
| [`figures/make_figures.py`](figures/make_figures.py) | Builds every figure from [`data/`](data/) |
| [`data/README.md`](data/README.md) | Provenance of every data file (source branch, commit, PR) |
| [`scripts/validate_refs.py`](scripts/validate_refs.py) | Re-runs the reference check |
| [`mock_review/`](mock_review/) | Edison mock editor/reviewer pass on the draft |

Placeholders: orange bracketed text in the PDF marks values that wait on data; figure panels from
invented numbers carry a diagonal "SYNTHETIC DATA" mark and a caption starting "[Placeholder: synthetic
data.]".

Build (MiKTeX or TeX Live; Python with numpy, pandas, scipy, matplotlib):

```sh
cd paper/optimization
make figures   # python3 figures/make_figures.py
make           # pdflatex + bibtex
make refs      # python3 scripts/validate_refs.py refs.bib (network)
```
