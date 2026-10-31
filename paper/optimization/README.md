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
| [`figures/make_overview_relations.py`](figures/make_overview_relations.py) | Overview schematic from the 28 Oct whiteboard sketch: cheap doser measurements related to standard powder tests (no data). Each card carries a 3D still from [`figures/stills/`](figures/stills/); `--flat` draws the earlier flat icons, `--board` only the links on the sketch |
| [`figures/render3d/render_stills.py`](figures/render3d/render_stills.py) | Renders those stills (PyVista/VTK): the standard tests from the PR #190 powder-test animations, the doser measurements as new scenes around the doser CAD from PR #170 |
| [`data/README.md`](data/README.md) | Provenance of every data file (source branch, commit, PR) |
| [`scripts/validate_refs.py`](scripts/validate_refs.py) | Re-runs the reference check |
| [`mock_review/`](mock_review/) | Edison mock editor/reviewer pass on the draft |
| [`tms-2027/`](tms-2027/) | TMS 2027 abstract, submitted and revised (28 Oct 2026), and that session's transcript |
| [`meetings/`](meetings/) | Corrected transcripts of author meetings (28 Oct 2026: Sterling and Will), with the raw Whisper output |

Placeholders: orange bracketed text in the PDF marks values that wait on data; figure panels from
invented numbers carry a diagonal "SYNTHETIC DATA" mark and a caption starting "[Placeholder: synthetic
data.]".

Build (MiKTeX or TeX Live; Python with numpy, pandas, scipy, matplotlib):

```sh
cd paper/optimization
make figures   # python3 figures/make_figures.py, figures/make_overview_relations.py
make stills    # re-renders figures/stills/ (pyvista, vtk, cadquery, xvfb-run; see render_stills.py)
make           # pdflatex + bibtex
make refs      # python3 scripts/validate_refs.py refs.bib (network)
```
