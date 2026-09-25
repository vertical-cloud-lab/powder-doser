Revised-figure verdict for **SI Fig. S1 / `figS1_nozzles`**

**What is now resolved from the round-1 flags**

- **Panel letters are now present and match the caption.** The revised PDF visibly labels the four panels as **(a)–(d)** under **Type 1–4**. This is also explicit in `make_figures.py`, where `figs1()` calls `panel_label(ax, "abcd"[k - 1])` for each panel and titles them `Type 1` through `Type 4`. The caption refers to “Types 1–4, panels (a)–(d)”, so the figure/caption mapping is now internally consistent.
- **The SI text now makes the non-results status clear without synthetic-performance claims.** In `si.pdf`, §S3 says: **“Four printed exit-nozzle geometries were produced for dispense testing (Fig. S1); the dispensing campaign will report flow-initiation and dribble behaviour per nozzle and per powder.”** That resolves the earlier risk that the figure itself might imply measured comparison data. It now reads as a geometry-only support figure for a future dispense campaign.
- **The caption is narrower than a full hardware/system description and does not introduce hopper/load-cell/sensor errors.** `caption_figS1_nozzles.md` is limited to geometry: **“Cross-sections of the four exit-nozzle variant CAD models … differing in exit constriction and chamfer geometry.”** Given the round-1 instruction to keep the legend narrow unless verified, this part is cleaned up.

**Previously flagged issues that are not yet resolved**

- **Caption still does not say enough that the reader can verify from the panels alone.** Round 1 explicitly flagged the phrase **“differing in exit constriction and chamfer geometry”** as too abstract unless tied to visible evidence. That exact wording is still present in both `caption_figS1_nozzles.md` and `si.pdf` Figure S1 caption.
- **The figure is still not cropped to the tip region, despite being called “exit-nozzle variants.”** In the revised PDF, most of each panel is the same lower-auger cross-section; only the bottom tip region changes. `make_figures.py` still uses the full assets `assets/nozzle_type1_cross_section.png` through `assets/nozzle_type4_cross_section.png` with no zoom or inset. So the round-1 “either crop tighter or rename the figure” issue is still open.
- **There are still no geometry annotations or dimensions.** No exit diameter, minimum constriction diameter, chamfer angle, axial length, or scale bar is present in the PDF, caption, or `make_figures.py`. That leaves unresolved the round-1 requests for dimensioned/annotated geometry.
- **Type-to-source provenance is still undocumented in the figure materials.** The caption and code do not cite the likely authoritative CAD sources named in the branch tree: `cad/auger-geared/nozzle-variants.scad` and `cad/auger-geared/archimedes-auger-test-nozzle1.scad` through `archimedes-auger-test-nozzle4.scad` under the branch-tree listing. That matters because `main.pdf` §2.3.0.2 documents a prior verification failure: **“the agent produced four miniature test nozzles with two of the four silently swapped relative to their documentation”**. The revised figure gives no audit trail showing that the current Type 1–4 labels were checked against those source files.
- **No HUMAN vs AI attribution/signposting was added for this figure.** Round 1 flagged this across the manuscript. For S1, neither `caption_figS1_nozzles.md` nor the Figure S1 caption in `si.pdf` says whether the geometries/renders were AI-modelled, human-reviewed, or derived from programmatic CAD only. That omission remains, and the PR snapshot explicitly asked for this distinction at `paper/main.tex` line ~189.

**Remaining concrete inconsistencies or unsupported claims that can be fixed without new bench data**

- **“Exit-nozzle variants” overstates what the current framing shows.** The figure shows full lower-auger cross-sections, not isolated nozzle details. In the PDF, roughly the upper majority of each panel is repeated auger flighting, while the distinguishing geometry is confined to the tip. So either:
  - crop/zoom the outlet region, or
  - rename the figure/caption to something like **“lower-auger cross-sections showing exit-nozzle variants”**.
  As written, the title/caption points the reader to the nozzle, but the visual emphasis points elsewhere.
- **The caption’s singular phrasing is slippery:** **“CAD models … of the test auger”**. The branch tree names four separate source files: `cad/auger-geared/archimedes-auger-test-nozzle1.scad` to `...4.scad`. That reads like four test-auger variants, not one test auger with four detachable nozzles. Unless the source files show otherwise, the safer wording is that the panels are **four CAD variants of the test auger with different exit-nozzle geometries**.
- **The “differing in exit constriction and chamfer geometry” claim is not fully reader-auditable at current scale.** The revised PDF does show bottom-tip differences, but without arrows/insets a reader cannot reliably tell which feature is the constriction and which is the chamfer in each type. Type 2 is the clearest example: its outlet region reads very differently from Types 1/3/4, but the exact controlled parameter is not labelled.
- **The manuscript’s documented label-swap incident is not connected back to this figure.** `main.pdf` §2.3.0.2 gives a concrete warning specific to four miniature test nozzles. Because this SI figure is exactly the four nozzle variants, the absence of a provenance note is a real support gap, not just a nice-to-have. A one-line caption addition naming the checked source files would fix this.
- **The caption does not distinguish printed parts from CAD render content cleanly.** `si.pdf` §S3 says **“Four printed exit-nozzle geometries were produced”**, while the caption says **“Cross-sections of the four exit-nozzle variant CAD models”**. Those are not contradictory, but the figure itself is a CAD-render figure, not a photograph of printed parts. If you want zero ambiguity, say so directly: the figure shows CAD cross-sections; printed parts were also produced for later testing.
- **No branch/file provenance is given even though the repository tree names the likely sources.** The most relevant branch-tree paths to cite are:
  - `cad/auger-geared/nozzle-variants.scad`
  - `cad/auger-geared/archimedes-auger-test-nozzle1.scad`
  - `cad/auger-geared/archimedes-auger-test-nozzle2.scad`
  - `cad/auger-geared/archimedes-auger-test-nozzle3.scad`
  - `cad/auger-geared/archimedes-auger-test-nozzle4.scad`
  - rendered assets already bundled as `paper/figures/assets/nozzle_type1_cross_section.png` through `...type4...`
  If the printed-set photo is wanted as optional support, the branch tree names `docs/assets/printed/nozzle-augers-issue48-printed-set.jpg`.

**Short prioritized action list: implementable fixes still remaining**

1. **Rewrite the Figure S1 caption** so it matches exactly what a reader can verify: say these are CAD cross-sections of four test-auger variants, and name the varying features only if they are annotated or sourced.
2. **Add source provenance for Type 1–4** in the caption or nearby SI text, using the branch-tree CAD files `cad/auger-geared/archimedes-auger-test-nozzle1.scad` to `...4.scad` and, if helpful, `cad/auger-geared/nozzle-variants.scad`.
3. **Crop to the outlet region or add a second zoomed row/insets** so the “exit-nozzle variants” claim matches the visual emphasis.
4. **Add non-invented geometric annotations** from the CAD source files: at minimum outlet/constriction diameter, chamfer angle, and a mm scale bar.
5. **Add one brief provenance/signposting sentence** stating HUMAN vs AI roles and that the geometries were produced with programmatic CAD, not a GUI CAD package; if Zoo Design Studio / Zookeeper was not used for this figure specifically, don’t imply that it was.
6. **Optionally add one note about label verification** in light of the swap anecdote in `main.pdf` §2.3.0.2.

- Treated `si.pdf` and the exported `figS1_nozzles.pdf` as the primary evidence for what a reviewer would actually see, with `caption_figS1_nozzles.md` and `make_figures.py` used to verify caption-text and rendering logic.
- Counted an issue as resolved only when the revised PDF/caption/code showed the fix directly; I did not assume fixes from round-1 recommendations alone.
- Used `all_branches_file_tree.txt` only to name relevant source/provenance files, not to infer their unseen contents.
- Treated the label-swap anecdote in `main.pdf` §2.3.0.2 as a provenance risk that raises the bar for documenting Type 1–4 mapping, not as proof that the revised labels are currently wrong.
- Did not re-open the known synthetic-dispensing-data issue, per instruction, because Figure S1 is a geometry figure and `si.pdf` already frames the performance campaign as future work.