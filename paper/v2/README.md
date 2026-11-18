# v2 figures and tables

The restart agreed on 27 Oct 2026: title and abstract first, then every figure and
table, and only then the full manuscript rebuilt around them. Sources:

- the whiteboard from the meeting, [`sources/brainstorm-whiteboard-2026-10-27.png`](sources/brainstorm-whiteboard-2026-10-27.png)
  (green = main text, blue = SI);
- the meeting itself, [`../meeting_2026-10-27/TRANSCRIPT-corrected.md`](../meeting_2026-10-27/TRANSCRIPT-corrected.md)
  (timestamps below are into that recording).

`main.tex`, `si.tex` and `paper/figures/` are untouched. Title and abstract are in
[`TITLE-ABSTRACT.md`](TITLE-ABSTRACT.md); every figure and table, each figure with its draft
caption as text underneath, is in [`FIGURES-AND-TABLES.md`](FIGURES-AND-TABLES.md).

**Review of 11 Nov 2026.** Sterling's video review of this set is transcribed in
[`../review_2026-11-11/TRANSCRIPT.md`](../review_2026-11-11/TRANSCRIPT.md), and every point is
listed with what was done in [`../review_2026-11-11/NOTES.md`](../review_2026-11-11/NOTES.md).
The main changes: the multi-panel figures are LaTeX subfigures ([`figures.tex`](figures.tex),
compiled to [`figures.pdf`](figures.pdf)); captions are shown as text, never inside an image,
and open with the takeaway; and Fig. 2b became its own figure, Fig. 3, so the later figures
moved up by one (old 3 → 4, 4 → 5, 5 → 6, 6 → 7).

**Review of 17 Nov 2026.** Sam's notes on Figs. 1–7 are listed point by point in
[`../review_2026-11-17/NOTES.md`](../review_2026-11-17/NOTES.md), with the data checks for
Fig. 6 (the negative tap means are balance noise; the flow comes in one surge per auger
revolution) and the pictures still needed. They were implemented on 18 Nov, once Python could
run on this PR. Captions now live in [`CAPTIONS.md`](CAPTIONS.md), which the team edits directly,
and every preview image carries its caption. Fig. 6 has a version B with banded rows, and Fig. 7
has versions B and C in milligrams; each follows its figure in
[`FIGURES-AND-TABLES.md`](FIGURES-AND-TABLES.md) and comes last in `figures.pdf`.

## Whiteboard, transcript, and what was made

| Whiteboard | Meeting | v2 item | Status |
|---|---|---|---|
| **Fig 1** (green) "w/ callouts: schematic + real doser image, final version"; "assembled + exploded"; callout → "auger section view" | Real assembled doser with an exploded view and callouts, one large image (08:24, 24:45, 25:37); photo of powder in the beaker on the balance (23:09); commercial systems left out (08:46) | **Fig. 1** | done; photo is the as-tested rig (11 Sep), see decision 1 |
| **Fig 2. AI** (green): timeline Apr '26 → Oct '26, AI on top, "Engineer (incl. drawings)" below, "Agent + Model" band; "Orig Gen AI" → "Human-redesign" pairs | AI parts beside the human redesigns, e.g. tap collar (10:40), final version (12:13); timeline of key designs, AI top / engineers bottom (13:25) with agent and model (13:44) and hand drawings (24:30); carries the "AI version, then redesign" story (17:56) | **Fig. 2** (a) timeline, (b) agents and models; **Fig. 3** AI part → replacement (was Fig. 2b) | done |
| "Keyframe reels" → "schematic"; **Fig 1)** (green) "dosing stages + parameters(?)"; "Claude pings 'dose 8 g'" | Dosing stages as keyframes from the videos (18:47–19:45) beside the feedback block diagram and the Claude ping that starts a dose (21:53–22:51); the Claude ping goes in the main text (26:32) | **Fig. 4** (was 3) | done; phase keyframes are CAD, see decision 3 |
| **Fig 2)** (green) "loading powder, installing, swapping augers" | Basic use (loading, installing, swapping) in the main text (20:09, 26:32) | **Fig. 5** (a–c) (was 4) | done |
| **Fig** (green, "maybe inset") "photo of dosers lined up" | All the dosers lined up with callouts of what is inside each; "mainly shock value", main text, perhaps an inset (23:20, 27:16) | **Fig. 5** (d) (was 4d) | done; 8 labelled augers with their measured delivery |
| "Keep Fig 3b, 3a"; "drop 3c or SI"; "4b, use all powders" | Fig. 3 is fine (29:26); 3c's slow/fast split not needed (29:41–30:20); 4b with every powder, a bar graph of mass per tap with error bars (30:49–31:39) | **Fig. 6** (old 3a, 3b + tap bars for all 13 powders); old 3c → **SI Fig. S2** without the shading | done |
| "4a better as table, maybe SI" | 30:32 | **Table S1** | done |
| "5d, separate, drop or SI" | Fig. 5d implies a link to the y-axis that isn't there; drop it or give times in the text (32:03–32:50) | **Fig. 7** (old 5a–c); times in **Table 3**; old 5d → **SI Fig. S3** on its own | done |
| "Generative CAD comparisons": "tap collar", "Zoo comparison" → **Fig** (blue), "CADSmith", "Mounting plate gap" | Tool comparison as text in the main text, images in the SI (15:50–16:53); show CADSmith's results (16:04); mounting-plate gap optional (17:05) | **SI Fig. S1** (one prompt, three tools; tap collar; plates) | done |
| **Fig 3)** (blue) "Assembly steps / instructions, plates, adjusting height" | Instructions and adjusting the height in the SI (26:32); Will's laser-cut modular stand (20:49) | **SI Fig. S4** | exploded view with every BOM item (18 Nov, from Fig. 1b's re-render); the build steps and the new stand are still to come (decision 6) |
| "discussion section: lessons learned" | 17:23 | text, not a figure | for the manuscript pass |
| (not on the board) | Fig. 6 of the draft (Sam's sketch beside his own Onshape model) reads as "drawing, then what the AI made" (23:37) | multi-doser sketch and Onshape model moved into the engineer row of Fig. 2; no separate future-work figure | done (decision 7) |

## Figures and tables

| | Main text | SI |
|---|---|---|
| Figures | 1 the doser · 2 AI and engineers over time · 3 original AI parts and what replaced them · 4 how a dose runs · 5 using the doser · 6 open-loop delivery · 7 closed-loop doses | S1 generative-CAD comparison · S2 variation between revolutions · S3 time per dose · S4 every part (exploded view and bill of materials) |
| Tables | 1 the 13 powders · 2 test protocols · 3 closed loop by target · 4 AI tools, dates and models | S1 open-loop per powder |

Panel PDFs (one per subfigure, at print size, no panel letters) are in [`figures/`](figures/);
[`figures.tex`](figures.tex) assembles them with `subcaption` and holds every caption and table.
Figs. 4 and 7 and the SI figures are single images: their panels share axes or leader lines.
PNG previews in [`preview/`](preview/) are rendered from the compiled LaTeX, each with its
caption. LaTeX and Markdown tables are in [`tables/`](tables/). Every image is a committed render, photograph or video frame;
[`assets/`](assets/) holds the copies used, and each `SOURCES.json` gives the comment, branch
or commit it came from.

## Decisions for Sam and Sterling

1. **Which doser in Fig. 1?** The photo is the rig as tested (11 Sep). Since then the stand was
   replaced (2 Oct) and the tap-collar block changed (Oct–Nov, #203). Every result in the paper
   comes from the 11 Sep configuration, so the as-tested photo may be the right one, with the
   final version as a new photo at the end of Fig. 2a (placeholder there now). Or take a new
   photo for Fig. 1.
2. **Brand names in photos.** The balance's maker and model are legible in Figs. 1a and 5c;
   Digital Discovery prefers no brand names in figures. Keep, crop, or blur?
3. **Real keyframes for the dose phases.** No downloadable footage shows bulk, fine and tap
   clearly, so Fig. 4c uses CAD renders for the tube positions and livestream stills only for
   before and after. The clearest real footage is the 4 Sep 1 g salt dose on the livestream
   (YouTube `xjtJNMo8DKw`, 4:12:58–4:14:23), which can be fetched on the Pi.
4. **Two doses in Fig. 4.** The request and reply are the 8 g AlSi10Mg atomizer charge
   (29 Sep), which used the optimized settings from the salt campaign; the trace is a campaign
   1 g NaCl dose with the frozen settings. Use one dose for both instead?
5. **Timeline content.** Which AI designs stay in Fig. 2a (now 9) and which engineer items (now
   8 plus the final photo)? CADSmith appears only in the band and in SI Fig. S1.
6. **Stand and height adjustment (SI).** Nothing in the repository shows Will's new stand
   being assembled or adjusted. A few phone photos, or an export of the Onshape document, would
   let SI Fig. S4 cover it.
7. **Future-work figure.** The draft's Fig. 6 (Sam's sketch beside his Onshape model) read as
   "drawing, then AI model" (23:37). The sketch and model now sit in the engineer row of
   Fig. 2a, and there is no separate future-work figure. Keep it that way?

Open questions from the 11 Nov review are listed at the end of
[`../review_2026-11-11/NOTES.md`](../review_2026-11-11/NOTES.md): what "mount cap" meant for
Fig. 1d, the aluminium grade of the cup in Fig. 5c, whether Fig. 7 should become one panel,
and Sam's replacement photo for Fig. 5d.

## Rebuild

```bash
cd paper/v2
python3 make_results_figures.py     # Figs. 6 (3 panels) and 6B, 7, 7B, 7C, S2, S3; Tables 1, 3, S1
python3 make_fig2_timeline.py       # Fig. 2 (2 panels), Fig. 3 (3 panels)
python3 make_photo_figures.py       # Figs. 1 and 5 (4 panels each), 4 (Fig. 4c reads the raw serial log from git)
python3 make_exploded_view.py       # Fig. 1b balloons and SI Fig. S4 (every BOM item)
python3 make_si_cad_comparison.py   # SI Fig. S1
python3 make_tables.py              # Tables 2, 4 and the failure-modes table
python3 build_figures.py            # CAPTIONS.md + figures.tex -> figures.pdf, preview/*.png, FIGURES-AND-TABLES.md
```

**Captions** are edited in [`CAPTIONS.md`](CAPTIONS.md), never in the generated files: one
`## Fig. N Title` heading per figure, the caption below it (line breaks inside a caption are
ignored, so each panel can have its own line). `build_figures.py` reads it, typesets each caption
under its figure in `figures.pdf`, renders each figure with its caption to `preview/`, and folds
the caption text, with its links, under each image in `FIGURES-AND-TABLES.md`. The subfigure
layout of each figure is in `build_figures.py`.

**LaTeX.** `build_figures.py` needs `pdflatex` and `pdftoppm`; MiKTeX provides `pdflatex` and
installs the LaTeX packages it needs on first use (`subcaption`, `caption`, `newunicodechar`,
`hyperref`, `extsizes`, `lm`). On Ubuntu 26.04 runners the MiKTeX apt package does not install
(its build for 24.04 needs libraries 26.04 no longer has), so the 18 Nov build used MiKTeX's
official Docker image through [`tools/pdflatex-miktex-docker.sh`](tools/pdflatex-miktex-docker.sh),
installed as `~/bin/pdflatex` (the script says how). `pdftoppm` is in `poppler-utils`.

**Exploded views.** `make_exploded_view.py` places the balloons on a committed render
(`assets/exploded/`, with a part-ID map), so it needs only matplotlib and SciPy.
`render_exploded_view.py` redoes the render itself from the PR #170 assembly (branch
`claude/issue-165-20261001-1931`, commit `7f5b3b7`, `cad/full-assembly/`); it needs CadQuery
and VTK in a Python 3.12 environment under `xvfb-run`, and only has to be re-run if the CAD
changes. Provenance is in `assets/exploded/SOURCES.json`.

`make_si_cad_comparison.py` renders the Zoo tap-collar STL once from the issue #104
attachment (see `assets/cadcompare/SOURCES.json`); the rendered PNG is committed, so later
runs do not need the download. `make_photo_figures.py` imports helpers from
`paper/figures/make_figures.py`, `make_data_figures.py` and `data/build_dose_traces.py`.
