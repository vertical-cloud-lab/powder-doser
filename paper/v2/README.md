# v2 figures and tables

The restart agreed on 27 Oct 2026: title and abstract first, then every figure and
table, and only then the full manuscript rebuilt around them. Sources:

- the whiteboard from the meeting, [`sources/brainstorm-whiteboard-2026-10-27.png`](sources/brainstorm-whiteboard-2026-10-27.png)
  (green = main text, blue = SI);
- the meeting itself, [`../meeting_2026-10-27/TRANSCRIPT-corrected.md`](../meeting_2026-10-27/TRANSCRIPT-corrected.md)
  (timestamps below are into that recording).

`main.tex`, `si.tex` and `paper/figures/` are untouched. Title and abstract are in
[`TITLE-ABSTRACT.md`](TITLE-ABSTRACT.md).

## Whiteboard, transcript, and what was made

| Whiteboard | Meeting | v2 item | Status |
|---|---|---|---|
| **Fig 1** (green) "w/ callouts: schematic + real doser image, final version"; "assembled + exploded"; callout → "auger section view" | Real assembled doser with an exploded view and callouts, one large image (08:24, 24:45, 25:37); photo of powder in the beaker on the balance (23:09); commercial systems left out (08:46) | **Fig. 1** | see below |
| **Fig 2. AI** (green): timeline Apr '26 → Oct '26, AI on top, "Engineer (incl. drawings)" below, "Agent + Model" band; "Orig Gen AI" → "Human-redesign" pairs | AI parts beside the human redesigns, e.g. tap collar (10:40), final version (12:13); timeline of key designs, AI top / engineers bottom (13:25) with agent and model (13:44) and hand drawings (24:30); carries the "AI version, then redesign" story (17:56) | **Fig. 2** | see below |
| "Keyframe reels" → "schematic"; **Fig 1)** (green) "dosing stages + parameters(?)"; "Claude pings 'dose 8 g'" | Dosing stages as keyframes from the videos (18:47–19:45) beside the feedback block diagram and the Claude ping that starts a dose (21:53–22:51); the Claude ping goes in the main text (26:32) | **Fig. 3** | see below |
| **Fig 2)** (green) "loading powder, installing, swapping augers" | Basic use (loading, installing, swapping) in the main text (20:09, 26:32) | **Fig. 4** | see below |
| **Fig** (green, "maybe inset") "photo of dosers lined up" | All the dosers lined up with callouts of what is inside each; "mainly shock value", main text, perhaps an inset (23:20, 27:16) | **Fig. 4** inset | see below |
| "Keep Fig 3b, 3a"; "drop 3c or SI"; "4b, use all powders" | Fig. 3 is fine (29:26); 3c's slow/fast split not needed (29:41–30:20); 4b with every powder, a bar graph of mass per tap with error bars (30:49–31:39) | **Fig. 5** (old 3a, 3b + tap bars for all 13 powders); old 3c → **SI Fig. S2** without the shading | done |
| "4a better as table, maybe SI" | 30:32 | **Table S1** | done |
| "5d, separate, drop or SI" | Fig. 5d implies a link to the y-axis that isn't there; drop it or give times in the text (32:03–32:50) | **Fig. 6** (old 5a–c); times in **Table 3**; old 5d → **SI Fig. S3** on its own | done |
| "Generative CAD comparisons": "tap collar", "Zoo comparison" → **Fig** (blue), "CADSmith", "Mounting plate gap" | Tool comparison as text in the main text, images in the SI (15:50–16:53); show CADSmith's results (16:04); mounting-plate gap optional (17:05) | **SI Fig. S1** | see below |
| **Fig 3)** (blue) "Assembly steps / instructions, plates, adjusting height" | Instructions and adjusting the height in the SI (26:32); Will's laser-cut modular stand (20:49) | **SI Fig. S4** | see below |
| "discussion section: lessons learned" | 17:23 | text, not a figure | for the manuscript pass |
| (not on the board) | Fig. 6 of the draft (Sam's sketch beside his own Onshape model) reads as "drawing, then what the AI made" (23:37) | multi-doser moved into the engineer row of Fig. 2 | see Fig. 2 |

## Figures

Main text: Figs. 1–6. SI: Figs. S1–S4. Scripts write PDFs to [`figures/`](figures/) and PNG
previews to [`preview/`](preview/).

## Tables

Main text: Table 1 (the 13 powders), Table 2 (test protocols, carried from the draft),
Table 3 (closed-loop by target), Table 4 (AI tools, dates and models). SI: Table S1
(open-loop per powder, replacing old Fig. 4a). Generated LaTeX and Markdown are in
[`tables/`](tables/).

## Rebuild

```bash
cd paper/v2
python3 make_results_figures.py     # Figs. 5, 6, S2, S3; Tables 1, 3, S1
```
