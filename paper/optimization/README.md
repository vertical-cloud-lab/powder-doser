# Optimization manuscript (issue #179)

Draft of the second powder-doser paper: per-powder calibration of the auger doser as multi-objective
Bayesian optimization, and the calibration records as a probe of powder flow. The draft reports the two
salt campaigns, the metal-feedstock doses and the property correlations from real data. Multi-task
calibration, DEM inference and same-lot property measurements are placeholders. Target: *Additive
Manufacturing* (Elsevier, `elsarticle`). Where it stands and what is missing: [`OUTLINE.md`](OUTLINE.md)
§0 and §4.

| File | What |
|---|---|
| [`main.tex`](main.tex) / [`main.pdf`](main.pdf) | The draft |
| [`si.tex`](si.tex) / [`si.pdf`](si.pdf) | Supplementary information: every dose, the model checks, the ML-requirements table, the property table |
| [`OUTLINE.md`](OUTLINE.md) | Where it stands, claim-by-claim status, the boundary with the hardware paper (#97), and **what is missing, with run counts, owners and dates** |
| [`SUBMISSION.md`](SUBMISSION.md) | The journal's requirements (live guide, 27 Nov 2026) and what is done or open |
| [`ROUTES.md`](ROUTES.md) | Three ways to scope the paper (focused article, Methods paper, full scope), with experiments, rig days and dates, for the scope decision |
| [`mock_review_r2/`](mock_review_r2/) | Second Edison mock review (27 Nov): editor, three reviewers, statistics audit, overlap audit against the hardware paper |
| [`cover_letter.md`](cover_letter.md) | Cover-letter draft (not sent) |
| [`analysis/`](analysis/) | `opt_stats.py` (every number in the text, into `results/stats.json`), `gp_diagnostics.py` (leave-one-out checks of the GP model), `si_tables.py`, `export_opt_trials.py` (re-exports the MongoDB snapshot) |
| [`refs.bib`](refs.bib), [`references_validation.md`](references_validation.md) | Bibliography (DOI entries built from Crossref metadata) and the per-entry check |
| [`figures/make_figures.py`](figures/make_figures.py) | Builds every figure from [`data/`](data/) |
| [`figures/make_overview_relations.py`](figures/make_overview_relations.py) | Overview schematic from the 28 Oct whiteboard sketch (no data): (a) cheap doser measurements, (b) the relational matrix that physics-based ML learns, with the powder's state and history as inputs, (c) the standard powder tests. Each card carries a 3D still from [`figures/stills/`](figures/stills/) |
| [`figures/render3d/render_stills.py`](figures/render3d/render_stills.py) | Renders those stills (PyVista/VTK): the standard tests from the PR #190 powder-test animations, the doser measurements as new scenes around the doser CAD from PR #170 |
| [`data/README.md`](data/README.md) | Provenance of every data file (source branch, commit, PR). `data/opt_trials/` holds all 125 MongoDB `opt_trials` records (29 Sep to 20 Oct 2026) |
| [`scripts/validate_refs.py`](scripts/validate_refs.py) | Re-runs the reference check |
| [`contact_sheet.png`](contact_sheet.png), [`scripts/contact_sheet.py`](scripts/contact_sheet.py) | Every page of `main.pdf` on one sheet, for a quick look at the layout (`make contact`) |
| [`mock_review/`](mock_review/) | Edison mock editor/reviewer pass on the draft |
| [`tms-2027/`](tms-2027/) | TMS 2027 abstract, submitted and revised (28 Oct 2026), and that session's transcript |
| [`meetings/`](meetings/) | Corrected transcripts of author meetings (28 Oct 2026: Sterling and Will), with the raw Whisper output |

Placeholders: orange bracketed text in the PDF marks values that wait on data; figure panels from
invented numbers carry a diagonal "SYNTHETIC DATA" mark and a caption starting "[Placeholder: synthetic
data.]".

Build (MiKTeX or TeX Live; Python with numpy, pandas, scipy, matplotlib):

```sh
cd paper/optimization
make analysis  # stats.json, gp_cv.json and the SI tables from data/ (gp_diagnostics needs botorch[fully_bayesian])
make figures   # python3 figures/make_figures.py, figures/make_overview_relations.py
make stills    # re-renders figures/stills/ (pyvista, vtk, cadquery, xvfb-run; see render_stills.py)
make           # main.pdf and si.pdf (pdflatex + bibtex)
make docker-pdf  # the same with MiKTeX in Docker
make refs      # python3 scripts/validate_refs.py refs.bib (network)
make contact   # contact sheet of main.pdf (pdftoppm + Pillow)
```
