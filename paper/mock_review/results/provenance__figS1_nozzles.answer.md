## Figure S1 (`figS1_nozzles`) — provenance & reproducibility audit

### Verdict
**Reproducible from the bundled sources.** Running `make_figures.py:figs1()` on the four PNGs in `assets/` regenerated a `figS1_nozzles.pdf` that matches the supplied `figS1_nozzles.pdf` to within antialiasing/font-subset noise (mean per-channel absolute pixel diff = 0.43/255 at 200 dpi, ~12% of pixels touched, all of it localized to the four "Type k" title baselines and the antialiased edges of the cross-section line art; file sizes 116 595 vs 116 315 B). The caption file (`caption_figS1_nozzles.md`) matches the rendered caption in `si.pdf` p. 2 ("Cross-sections of the four printed exit-nozzle variants (Types 1–4) of the test auger, differing in exit constriction and chamfer geometry.").

### What the figure-build code actually does
`make_figures.py:figs1()` (lines 409–415) is fully deterministic and parameter-free: it loads exactly four assets — `assets/nozzle_type{1..4}_cross_section.png` — via `load()`, tiles them in a 1×4 grid sized for an RSC double column (`DOUBLE_COL_IN` × 2.4 in), titles each panel `Type k`, and writes `figS1_nozzles.pdf`. There is no `synthetic_watermark` / `placeholder_note` call for S1 (contrast with `fig3()`), so this panel is presented as authentic CAD content, not placeholder data.

### Source files that should be cited / archived (named from `all_branches_file_tree.txt`)

Underlying CAD lives entirely on branch **`origin/copilot/add-new-auger-design`** under `cad/auger-geared/`:

| Panel | Parametric source (SCAD) | Mesh (STL) | Branch render (PNG) | Asset used by `make_figures.py` |
|---|---|---|---|---|
| Type 1 | `cad/auger-geared/archimedes-auger-test-nozzle1.scad` | `…-nozzle1.stl` | `…-nozzle1-cross-section.png` | `paper/figures/assets/nozzle_type1_cross_section.png` |
| Type 2 | `…-nozzle2.scad` | `…-nozzle2.stl` | `…-nozzle2-cross-section.png` | `…/nozzle_type2_cross_section.png` |
| Type 3 | `…-nozzle3.scad` | `…-nozzle3.stl` | `…-nozzle3-cross-section.png` | `…/nozzle_type3_cross_section.png` |
| Type 4 | `…-nozzle4.scad` | `…-nozzle4.stl` | `…-nozzle4-cross-section.png` | `…/nozzle_type4_cross_section.png` |

Supporting source on the same branch:
- `cad/auger-geared/nozzle-variants.scad` — parametric generator covering all four variants
- `cad/auger-geared/edison_run_nozzles.py` — render driver (AI sub-agent)
- `cad/auger-geared/edison_artifacts/nozzle-selection.{task.json,answer.md,references.md}` — AI design rationale for the variant set
- `cad/auger-geared/README.md` — module-level documentation

Paper-side mirrors live on **`origin/copilot/draft-base-manuscript`** at `paper/figures/assets/nozzle_type{1..4}_cross_section.png` and `paper/figures/figS1_nozzles.pdf` (i.e. the renames the build script consumes).

Supplementary physical-print evidence (referenced by the caption word "printed") sits on **`origin/copilot/record-of-designs`** at `docs/assets/printed/nozzle-augers-issue48-printed-set.jpg`.

### Panels with locatable underlying source
All four. No S1 panel is unsourced. There are zero placeholder/watermarked panels in S1 (unlike Figure 3, which is watermarked SYNTHETIC).

### Things to fix or tighten (not blockers, but worth flagging)
1. The branch tree shows the cross-section PNGs only — there is **no separate SCAD-to-PNG render script committed alongside `nozzle-variants.scad`** on the same path (the OpenSCAD invocation that produced each `…-cross-section.png` from each `…-nozzle{k}.scad` is not explicit in the tree; `edison_run_nozzles.py` is the closest candidate but its scope is not visible from filenames). For full reproducibility one would want either a Makefile or a documented `openscad -o … --imgsize=500,900 --camera=…` invocation in `cad/auger-geared/`.
2. PR97 comment snapshot (`pr97_comments.md`, 7 096 chars) contains **no mention** of "nozzle", "S1", "exit-", or "placeholder" — so this figure has not been reviewed in that PR. If PR97 is the venue tracking this manuscript, S1 has slipped through without review.
3. The caption uses "printed" but the figure itself shows CAD cross-sections, not photographs of printed parts. The photo `docs/assets/printed/nozzle-augers-issue48-printed-set.jpg` exists on `origin/copilot/record-of-designs` and would substantiate the "printed" claim if either inset into the figure or cited next to it.
4. Provenance of the rename from `archimedes-auger-test-nozzle{k}-cross-section.png` (design branch) to `nozzle_type{k}_cross_section.png` (paper branch and this bundle's `assets/`) is not documented anywhere visible — it appears to be a manual copy. A scripted copy step in `make_figures.py` or a sibling `prepare_assets.py` would close the loop.

### Prioritized action list for figS1_nozzles
1. **Cite the four SCAD sources directly in the SI Fig. S1 caption or in §S3** as the authoritative geometry, e.g. "Geometries defined by `cad/auger-geared/archimedes-auger-test-nozzle{1..4}.scad` on branch `copilot/add-new-auger-design`."
2. **Archive a deterministic build recipe**: commit the OpenSCAD render command (or expose it in `edison_run_nozzles.py`'s docstring) that maps each `.scad` → `…-cross-section.png`, and add a copy/rename step to `make_figures.py` (or a `Makefile`) so the path from `.scad` → `figS1_nozzles.pdf` is fully scripted.
3. **Add a Zenodo/figshare archive entry** (or git tag) pinning the four `.scad` + `.stl` + cross-section PNGs at the manuscript revision; reference its DOI in the SI.
4. **Either reword the caption** ("Cross-sections of CAD designs for the four exit-nozzle variants…") or **inset a photograph** from `docs/assets/printed/nozzle-augers-issue48-printed-set.jpg` (`origin/copilot/record-of-designs`) so the word "printed" is substantiated by the figure itself.
5. **Solicit review of S1 specifically** — PR97 reviewers (human + bot) did not comment on it; given the SI claims the four geometries drive a forthcoming dispense campaign, the variant rationale in `cad/auger-geared/edison_artifacts/nozzle-selection.answer.md` should be sanity-checked.

### Discretionary decisions
- Used PyMuPDF (`pymupdf`) at 200 dpi for the supplied-vs-regenerated PDF raster diff. A different dpi or renderer (Cairo/Poppler) would give numerically different but qualitatively equivalent diff statistics.
- Treated "frac diff px ≈ 12% concentrated on text baselines + AA edges, mean abs diff < 0.5/255" as evidence of byte-equivalent figure content; no perceptual hash threshold was set a priori.
- Defined "reproducible" as "rerunning `figs1()` against the shipped `assets/` produces a PDF visually identical to the shipped `figS1_nozzles.pdf`". I did not attempt to rebuild the four input PNGs from the upstream `.scad` files because they are not in this bundle and require OpenSCAD; this caveat is reflected in action item 2.
- Took the branch tree (`all_branches_file_tree.txt`) at face value as a faithful inventory; file contents on those branches were not verified.