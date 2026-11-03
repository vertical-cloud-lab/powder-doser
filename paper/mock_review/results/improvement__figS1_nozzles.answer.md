The current Figure S1 is doing the minimum, and that’s the problem. It shows four full-height cross-sections, but almost all of each panel is repeated auger geometry. The variant-defining information is concentrated at the exit tip, while the present layout spends most of the area on parts that do not help the reader compare Types 1–4. You can see this directly in the current generation code: `make_figures.py` builds `figS1_nozzles.pdf` as a plain `plt.subplots(1, 4)` grid with only image placement and a title per panel, no crop, no annotations, and no scale information (`def figs1() ... show(ax, f"nozzle_type{k}_cross_section.png"); ax.set_title(f"Type {k}") ...`). The current caption is also only one sentence: “Cross-sections of the four printed exit-nozzle variants (Types 1--4) of the test auger, differing in exit constriction and chamfer geometry.” (`caption_figS1_nozzles.md`).

What the manuscript says this figure must support is more specific than the figure currently shows. The main text states: “Exit-nozzle geometry strongly affects flow initiation and dribble; four printed nozzle variants are compared in SI Fig. S1.” (`main.pdf`, §2.2). The SI adds: “Four printed exit-nozzle geometries were produced for dispense testing (Fig. S1); the dispensing campaign will report flow-initiation and dribble behaviour per nozzle and per powder.” (`si.pdf`, §S3). So the figure’s job is not just “here are four CAD sections.” Its job is to let a reader quickly understand what varies across the four printed designs, and why those differences matter for future dispense behavior.

My concrete recommendation is a prioritized redesign that keeps the existing assets where possible.

1. Redesign the layout around comparison of the exit region, not the full auger body

Best implementable version with existing assets:
- Replace the current 1×4 row of full-length cross-sections with a 2-row layout.
- Top row: four narrow overview panels, one per type, using the existing full cross-sections but cropped to show only enough of the auger body to orient the reader. About the lower 25–35% of each current PNG is enough. The full 900 px height is wasted at present because the differentiating geometry is near the bottom tip in all four `assets/nozzle_type{1–4}_cross_section.png` files.
- Bottom row: four larger tip-detail panels, each a tight crop around the outlet. This is the critical change. In the current figure, the visible differences among Types 1–4 are almost entirely at the exit. The panels you supplied make that obvious: Type 2 has the blunt/flat outlet, Type 3 the long symmetric conical constriction, and Types 1 and 4 the asymmetric/chamfered forms. At manuscript thumbnail size, those distinctions are easy to miss in the current full-height layout.

Why this should be the first change:
- The present code and PDF devote roughly 80–90% of the figure area to repeated helical channel geometry. That geometry is not what the caption says varies.
- The manuscript’s scientific claim is about “exit constriction and chamfer geometry,” and those features sit at the tip, not along the upper flights.
- A top-tier hardware paper needs the visual hierarchy to match the claim.

Implementation note:
- This can be done with the existing assets alone by changing `figs1()` in `make_figures.py` to place two crops per type from the same PNGs. No new CAD rendering is strictly required for this first-pass fix.

2. Add direct callouts for the two variables named in the caption

What to add to each enlarged tip panel:
- Arrow and label: “exit constriction” pointing to the narrowed outlet section.
- Arrow and label: “chamfer” pointing to the beveled terminal face.
- Optional short type descriptor beneath each panel, if you can defend it from geometry alone, e.g.:
  - Type 1: asymmetric chamfer + constricted tip
  - Type 2: blunt outlet / minimal constriction
  - Type 3: symmetric conical constriction
  - Type 4: constricted tip with short chamfered outlet

Be careful here: only label what is visible in the supplied render, unless you extract exact parameters from source files. I do not have the `.scad` contents in this bundle, only the branch-tree evidence that they exist in `origin/copilot/add-new-auger-design`:
- `cad/auger-geared/nozzle-variants.scad`
- `cad/auger-geared/archimedes-auger-test-nozzle1.scad`
- `cad/auger-geared/archimedes-auger-test-nozzle2.scad`
- `cad/auger-geared/archimedes-auger-test-nozzle3.scad`
- `cad/auger-geared/archimedes-auger-test-nozzle4.scad`

If you pull dimensions from those sources later, the labels can become sharper, for example “2 mm outlet” or “45° chamfer.” Without that, keep labels qualitative.

3. Add at least one dimensional reference

The current figure has no scale bar, no dimension lines, and no stated outlet size. For a hardware paper, that leaves the geometry visually interesting but technically thin.

Two ways to fix this:

Preferred, if source CAD is available:
- Add one simple dimension overlay per tip-detail panel, or one shared dimension schematic alongside the four variants, showing:
  - outlet diameter
  - constriction length
  - chamfer angle or chamfer length
- The branch tree strongly suggests the needed parametric sources exist on `origin/copilot/add-new-auger-design`, especially `cad/auger-geared/nozzle-variants.scad` and the four nozzle `.scad` files.

Fallback with existing assets only:
- Add a caption sentence explicitly saying that the panels are shown at the same scale.
- This is weaker than true dimensions, but still better than leaving scale implicit.

I would not recommend adding a decorative scale bar unless you can compute it correctly from the CAD render/export settings. If you cannot derive it from source, say nothing rather than guessing.

4. Remove or reduce visually distracting repeated auger flights

The current cross-sections show multiple helical flights, and the differences in flight phase/pitch across the panels add visual noise. That matters because the reader’s eye is pulled to the blue helix slices rather than the nozzle exit.

Concrete fix:
- In the overview row, crop so only the last 2–3 flights above the nozzle are visible.
- In the detail row, show just the terminal flight and outlet.
- If you keep a full-height version anywhere, put it in a tiny inset or drop it entirely.

This is fully implementable from the current PNG assets and would immediately improve signal-to-noise.

5. Use panel labeling that carries meaning, not just “Type 1–4”

At present, the only identifiers are titles “Type 1” through “Type 4” in `make_figures.py`. That’s not enough for later discussion.

I’d change the panel headers to a two-line style:
- `Type 1`
- small subtitle: `constricted, asymmetric chamfer`

and likewise for the others, but only if you verify the wording against CAD source. If you do not verify, then keep the type names and move the descriptors into the caption as cautious qualitative phrases.

6. Add one provenance sentence in the caption about what is shown

Because the paper makes a point about AI-assisted parametric CAD and because §2.3 mentions a silent swap problem in the nozzle test set, Figure S1 benefits from one factual provenance sentence. The main text says: “...in one documented case the agent produced four miniature test nozzles with two of the four silently swapped relative to their documentation...” (`main.pdf`, §2.3). That creates a trust issue around the variants.

I would not over-explain that anecdote in the figure caption, but I would make clear what the figure actually shows:
- These are cross-sections of the printed test-nozzle geometries used for the dispense study.
- If true in your workflow, add that the figure was generated from the corresponding parametric CAD variants rather than photographed parts.

Because you asked for attribution discipline: the safe framing is HUMAN vs AI only. Also, the review bundle explicitly says not to imply GUI CAD use; instead, note that the project used programmatic CAD, with late exploratory use of Zoo Design Studio. I would keep that out of the caption unless this SI section is specifically about workflow provenance.

7. Consider a single added panel only if you can do it cleanly

Two optional additions could make the figure stronger, but only one is really worth it.

Option A, better if available from existing repository assets:
- Add a small photo inset of the printed nozzle set for physical reality check.
- The branch tree shows a likely relevant file in `origin/copilot/record-of-designs`: `docs/assets/printed/nozzle-augers-issue48-printed-set.jpg`.
- This would help bridge CAD-to-hardware, which is often appreciated in hardware papers.

But there are two cautions:
- I have not inspected that image in this bundle; I only know it exists from `all_branches_file_tree.txt`.
- If the photo is cluttered or not aligned with the four types one-to-one, don’t force it into S1.

Option B, strongest scientifically but requires new data:
- Add a tiny companion chart or table summarizing measured outcomes per nozzle type, such as flow initiation success and dribble incidence.
- This would directly support the claim in `main.pdf` and `si.pdf` that nozzle geometry affects dispensing behavior.

But right now I cannot recommend this as an immediate figure revision because the manuscript/SI explicitly say those results are not yet reported: “the dispensing campaign will report flow-initiation and dribble behaviour per nozzle and per powder” (`si.pdf`, §S3). No bench data are present in this bundle. I cannot infer or fabricate performance results.

So for this revision cycle, I would treat performance data as out of scope unless you have real measurements elsewhere.

What to remove

- Remove the current giant full-height equal-area treatment of all four sections as the main content. It looks like a CAD asset dump, not a figure designed to answer a scientific question.
- Remove any temptation to add speculative performance language to the caption. The manuscript does not yet provide those data.
- Do not add human/AI workflow detail here unless the SI section explicitly needs it; otherwise it will distract from the hardware comparison.

Tightened caption draft

This draft stays inside what the supplied files support and flags what the figure is for.

Figure S1. Cross-sections of the four printed exit-nozzle variants (Types 1–4) used for dispense testing. The variants differ only at the outlet region, in exit constriction and chamfer geometry; all panels are shown at the same scale. Enlarged views highlight the outlet features expected to influence flow initiation and post-dispense dribble, as discussed in the main text (§2.2) and SI §S3.

If you add dimension annotations from CAD source, use this stronger version:

Figure S1. Cross-sections of the four printed exit-nozzle variants (Types 1–4) used for dispense testing. The variants differ in outlet constriction and chamfer geometry, while the upstream auger body is otherwise unchanged. Enlarged outlet views and annotated dimensions identify the geometric features compared in the planned dispensing study, where flow-initiation and dribble behaviour will be assessed per nozzle and per powder (SI §S3).

If you also add a photo inset of printed parts:

Figure S1. Cross-sections of the four printed exit-nozzle variants (Types 1–4) used for dispense testing, together with a photograph of the printed set. The variants differ at the outlet region in exit constriction and chamfer geometry; enlarged outlet views identify the features compared in the planned dispensing study of flow initiation and dribble behaviour (SI §S3). All CAD cross-sections are shown at the same scale.

Files and passages supporting these recommendations

- Current caption source is minimal: `caption_figS1_nozzles.md`.
- Current figure-generation logic is minimal and unannotated: `make_figures.py`, `def figs1()`.
- Current compiled figure under review: `figS1_nozzles.pdf`.
- Current image assets consumed by the script: `assets/nozzle_type1_cross_section.png`, `assets/nozzle_type2_cross_section.png`, `assets/nozzle_type3_cross_section.png`, `assets/nozzle_type4_cross_section.png`.
- Main-text rationale: `main.pdf`, §2.2: “Exit-nozzle geometry strongly affects flow initiation and dribble; four printed nozzle variants are compared in SI Fig. S1.”
- SI rationale: `si.pdf`, §S3: “Four printed exit-nozzle geometries were produced for dispense testing (Fig. S1); the dispensing campaign will report flow-initiation and dribble behaviour per nozzle and per powder.”
- Branch-tree evidence for likely source CAD and possibly better figure assets on `origin/copilot/add-new-auger-design`:
  - `cad/auger-geared/nozzle-variants.scad`
  - `cad/auger-geared/archimedes-auger-test-nozzle1.scad`
  - `cad/auger-geared/archimedes-auger-test-nozzle2.scad`
  - `cad/auger-geared/archimedes-auger-test-nozzle3.scad`
  - `cad/auger-geared/archimedes-auger-test-nozzle4.scad`
  - `cad/auger-geared/archimedes-auger-test-nozzle1-cross-section.png`
  - `cad/auger-geared/archimedes-auger-test-nozzle2-cross-section.png`
  - `cad/auger-geared/archimedes-auger-test-nozzle3-cross-section.png`
  - `cad/auger-geared/archimedes-auger-test-nozzle4-cross-section.png`
- Branch-tree evidence for a possible printed-part inset on `origin/copilot/record-of-designs`:
  - `docs/assets/printed/nozzle-augers-issue48-printed-set.jpg`

Limits

I cannot recommend exact numeric dimension labels or a performance ranking of Types 1–4 because those values/results are not present in the supplied bundle I could inspect directly. The branch tree indicates likely CAD source files that could provide geometry parameters, but I did not have their contents here. Likewise, no nozzle-specific review comments were present in `pr97_comments.md`.

Prioritized action list for Figure S1

1. Rebuild Figure S1 as overview row + enlarged outlet-detail row using the existing four PNG assets.
2. Add arrowed annotations for “exit constriction” and “chamfer” in the detail panels.
3. State explicitly in the caption that all panels are at the same scale.
4. If available from `nozzle-variants.scad` and the four nozzle `.scad` files, add outlet dimensions/chamfer annotations.
5. Optionally add a small printed-part photo inset from `docs/assets/printed/nozzle-augers-issue48-printed-set.jpg` if it cleanly maps to the four types.
6. Do not add performance claims unless you have real bench data; if such data now exist, a tiny outcomes panel would be the highest-value scientific addition.

- Used the supplied PNG cross-sections as the primary visual evidence for what differentiates the four variants, because the branch tree showed likely CAD sources but not their contents in this bundle.
- Prioritized a crop-and-annotate redesign over requesting new renders, because the existing assets appear sufficient for a substantially better comparison figure.
- Recommended qualitative geometry descriptors unless exact dimensions can be recovered from the `.scad` files, to avoid inventing numeric parameters.
- Treated performance-data additions as optional and contingent on real bench data, because `si.pdf` states those results are planned rather than reported.
- Suggested a printed-part photo inset only as an option, since the branch tree confirms the file exists but its content/quality was not directly inspected here.