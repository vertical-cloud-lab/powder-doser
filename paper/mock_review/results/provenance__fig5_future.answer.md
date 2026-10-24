## Figure 5 (`fig5_future`) — provenance & reproducibility audit

### Is the figure reproducible from the supplied repository sources?

**Yes, with one caveat.** Running `fig5()` from the supplied `make_figures.py` against the supplied `assets/` directory regenerates a PDF that is visually identical to the under-review `fig5_future.pdf` (same panels, same layout, same text). Pixel-difference against a high-resolution raster of both PDFs gave a mean abs RGB diff of ~9/255 and ~13% of pixels differing by >5 — fully attributable to matplotlib bbox/anti-aliasing jitter (the regenerated raster is 352 px tall vs. 355 px for the supplied one). The figure script depends only on `numpy`, `matplotlib`, `PIL`, the single asset `assets/inward_collection_cup_iso.png`, and `RNG = np.random.default_rng(42)` (unused by `fig5`). No hidden inputs.

Caveat: `make_figures.py` and the asset live on the branch `origin/copilot/draft-base-manuscript` (`paper/figures/make_figures.py`, `paper/figures/assets/inward_collection_cup_iso.png`). They are not on `origin/main` at the time of the snapshot.

### Panel-by-panel source audit

**Panel (a) — "N-channel radial array (concept)"**

- This panel is **not a CAD render**. `fig5()` draws it from scratch in matplotlib: 8 hard-coded rotated `patches.Rectangle` channels at radius 2.4 and a `patches.Circle` "shared cup" of radius 0.9 (see `def fig5()` in `make_figures.py`).
- **No CAD or code file in the repository corresponds to this schematic.** Searches across all 45 branches for `multi.?doser`, `multi.?channel`, `n.?channel`, `radial`, `carousel`, `turret` return only text:
  - `origin/copilot/zoo-design-studio-multi-doser`: `paper/background/15-zoo-design-studio-multi-doser.md`, `paper/background/23-zds-transcript-editing-session.md` (notes/transcripts, no CAD).
  - Branch name `origin/copilot/design-channel-sealing-cap` is the only other "channel" hit, unrelated to the radial array.
- Caption claim "N-channel radial array concept around a shared collection cup" is therefore backed by *prose/transcript* artifacts only, not by a parametric model or render. The "8" is also a free choice in the plotting code, not a design parameter pulled from anywhere.

**Panel (b) — "Inward-tilting channels over shared cup (CAD)"**

- Consumed asset: `assets/inward_collection_cup_iso.png` (the only file referenced via `show(ax, "inward_collection_cup_iso.png")`).
- **Authoritative source is on `origin/copilot/brainstorming-design-possibilities`:**
  - `design/cad/inward-collection-cup/cad_model.py` — programmatic CAD that produced the model
  - `design/cad/inward-collection-cup/inward_collection_cup.step` — STEP geometry
  - `design/cad/inward-collection-cup/inward_collection_cup_iso.png` — the iso render shown in panel (b)
  - `design/cad/inward-collection-cup/inward_collection_cup_iso.svg`, `..._top.png`, `..._top.svg`, `sketch_2d.py`, `sketch_top_side.png`, `README.md` — sibling artifacts/views
- This is the only branch in the snapshot containing `inward-collection-cup`; the version under `paper/figures/assets/` on `draft-base-manuscript` is an extracted copy, consistent with the `make_figures.py` docstring: *"Real CAD renders are pulled from paper/figures/assets/ (extracted from the design branches of this repository)."*
- Consistent with the PR-comments note that no GUI CAD was used: the source is `cad_model.py` plus an exported `.step` — programmatic CAD only.

### Caption-vs-evidence check

The caption (`caption_fig5_future.md`):
- "(a) N-channel radial array concept around a shared collection cup on a single balance." — **partially supported.** No CAD file supports the "radial array" geometry. The "on a single balance" claim is not visualized in panel (a) at all (no balance is drawn) and there is no balance asset under `design/cad/inward-collection-cup/` either. The body text (main.pdf p. 7) makes the stronger forward-looking claim that "the multi-doser geometry and the cartridge-sealing concepts already have working CAD in the repository," which the branch tree does **not** corroborate for the *radial multi-doser* geometry — only for the *single* inward-tilting collection-cup study and (separately) the channel sealing cap (`origin/copilot/design-channel-sealing-cap`).
- "(b) CAD study of inward-tilting channels over the shared cup." — **fully supported** by `design/cad/inward-collection-cup/` on `origin/copilot/brainstorming-design-possibilities`.

### Files that should be cited / archived to substantiate this figure

For panel (b), archive (and cite in the caption or SI):
- `origin/copilot/brainstorming-design-possibilities :: design/cad/inward-collection-cup/cad_model.py`
- `origin/copilot/brainstorming-design-possibilities :: design/cad/inward-collection-cup/inward_collection_cup.step`
- `origin/copilot/brainstorming-design-possibilities :: design/cad/inward-collection-cup/inward_collection_cup_iso.png` (and the `.svg` + `_top.*` siblings, plus `sketch_2d.py` / `sketch_top_side.png`, plus the local `README.md`)

For panel (a), there is **no underlying CAD/code source to cite**. The only supporting prose lives on `origin/copilot/zoo-design-studio-multi-doser`:
- `paper/background/15-zoo-design-studio-multi-doser.md`
- `paper/background/23-zds-transcript-editing-session.md`

For the figure-generation pipeline itself:
- `origin/copilot/draft-base-manuscript :: paper/figures/make_figures.py` (specifically `def fig5()`)
- `origin/copilot/draft-base-manuscript :: paper/figures/assets/inward_collection_cup_iso.png`

### Panels with sources I cannot locate

**Panel (a)** has no traceable CAD/code source anywhere in the 45-branch tree. It is a hand-tuned matplotlib schematic generated inside `make_figures.py::fig5`. If the manuscript intends panel (a) to represent a designed concept (rather than a marketing schematic), a CAD or sketch source is missing. Two acceptable remedies:
1. Demote panel (a) to "schematic" in the caption and disclose in-text that it was drawn directly in matplotlib (it is an AI-authored visual abstract, not a design artifact).
2. Add a real parametric CAD model (or even a `cad_model.py` analogous to the inward-collection-cup one) on a new branch and re-render the panel from it.

### Cross-cuts with the PR thread (`pr97_comments.md`)

- The reviewer's request to "clarify where AI was used" and "signpost the design contributions of AI versus engineers" applies directly here: panel (a) is wholly AI-drafted with no underlying engineering artifact; panel (b)'s `cad_model.py` is also programmatic (LLM-coding-agent territory). Both should be explicitly tagged as AI-authored in the caption or methods.
- The "no GUI CAD" claim is consistent with what is on disk for panel (b): a `.py` + `.step` + PNG/SVG renders, no `.f3d`/`.SLDPRT`.

### Reproduction check

I ran `fig5()` against the supplied asset; the regenerated PDF matched the supplied one (mean ΔRGB ≈ 9/255, layout identical, no missing/extra elements). `make_figures.py` is byte-deterministic for `fig5` (no RNG draws inside the function body).

---

### Prioritized action list for this figure

1. **(must) Provide a source for panel (a).** Either: (i) add a `design/cad/multi-channel-radial/` directory (analogous to `inward-collection-cup/`) with a `cad_model.py` and a real render, then point `make_figures.py` at it; or (ii) rewrite the caption + body text to call panel (a) a *schematic concept drawn for the manuscript*, not a CAD study.
2. **(must) Tone down the body claim on main.pdf p. 7** ("the multi-doser geometry … already have working CAD in the repository"). The repository contains a single inward-tilting cup study and a sealing-cap branch — *not* a complete multi-doser geometry.
3. **(must) Drop "on a single balance" from caption (a)** or render a balance into the schematic — currently the asset doesn't include one.
4. **(should) Archive the panel (b) source bundle** with the manuscript: `design/cad/inward-collection-cup/{README.md, cad_model.py, inward_collection_cup.step, *_iso.{png,svg}, *_top.{png,svg}, sketch_2d.py, sketch_top_side.png}` from `origin/copilot/brainstorming-design-possibilities`, plus `paper/figures/make_figures.py` from `origin/copilot/draft-base-manuscript`. Cite them in the caption or SI.
5. **(should) Add an AI-vs-HUMAN attribution line to the caption** (per `@swcharles`'s PR-thread comment at `paper/main.tex` ~line 189): panel (a) matplotlib schematic and panel (b) `cad_model.py` are AI-authored; human contributions for this figure appear limited to review/curation.
6. **(nice) Merge the two source branches onto `main`** (or onto a tagged release used for archival/Zenodo DOI) so the figure's inputs live on a single, citeable ref.

### Discretionary decisions made during the analysis

- Used `pypdfium2` at 3×-scale rasterization for pixel comparison; a different rasterizer or DPI would change exact diff fractions but not the qualitative match.
- Considered the asset-path match (`paper/figures/assets/inward_collection_cup_iso.png` ↔ `design/cad/inward-collection-cup/inward_collection_cup_iso.png`) sufficient to establish provenance, given the `make_figures.py` docstring; I did not attempt a byte-for-byte comparison of the two PNGs because only one is supplied.
- Treated the absence of any branch-tree hit for `multi-doser` CAD as dispositive for panel (a). I did not pull live `git` refs to double-check (the tree file is the supplied ground truth).
- Set the threshold for "pixels differing" at >5/255 per RGB channel for the reproduction check.