# v2 figures and tables

The restart agreed on 27 Oct 2026: title and abstract first, then every figure and
table, and only then the full manuscript rebuilt around them. Sources:

- the whiteboard from the meeting, [`sources/brainstorm-whiteboard-2026-10-27.png`](sources/brainstorm-whiteboard-2026-10-27.png)
  (green = main text, blue = SI);
- the meeting itself, [`../meeting_2026-10-27/TRANSCRIPT-corrected.md`](../meeting_2026-10-27/TRANSCRIPT-corrected.md)
  (timestamps below are into that recording).

`main.tex`, `si.tex` and `paper/figures/` are untouched. Title and abstract are in
[`TITLE-ABSTRACT.md`](TITLE-ABSTRACT.md); every figure and table, with draft captions, is in
[`FIGURES-AND-TABLES.md`](FIGURES-AND-TABLES.md).

## Whiteboard, transcript, and what was made

| Whiteboard | Meeting | v2 item | Status |
|---|---|---|---|
| **Fig 1** (green) "w/ callouts: schematic + real doser image, final version"; "assembled + exploded"; callout → "auger section view" | Real assembled doser with an exploded view and callouts, one large image (08:24, 24:45, 25:37); photo of powder in the beaker on the balance (23:09); commercial systems left out (08:46) | **Fig. 1** | done; photo is the as-tested rig (11 Sep), see decision 1 |
| **Fig 2. AI** (green): timeline Apr '26 → Oct '26, AI on top, "Engineer (incl. drawings)" below, "Agent + Model" band; "Orig Gen AI" → "Human-redesign" pairs | AI parts beside the human redesigns, e.g. tap collar (10:40), final version (12:13); timeline of key designs, AI top / engineers bottom (13:25) with agent and model (13:44) and hand drawings (24:30); carries the "AI version, then redesign" story (17:56) | **Fig. 2** (a) timeline, (b) AI part → replacement | done |
| "Keyframe reels" → "schematic"; **Fig 1)** (green) "dosing stages + parameters(?)"; "Claude pings 'dose 8 g'" | Dosing stages as keyframes from the videos (18:47–19:45) beside the feedback block diagram and the Claude ping that starts a dose (21:53–22:51); the Claude ping goes in the main text (26:32) | **Fig. 3** | done; phase keyframes are CAD, see decision 3 |
| **Fig 2)** (green) "loading powder, installing, swapping augers" | Basic use (loading, installing, swapping) in the main text (20:09, 26:32) | **Fig. 4** (a–c) | done |
| **Fig** (green, "maybe inset") "photo of dosers lined up" | All the dosers lined up with callouts of what is inside each; "mainly shock value", main text, perhaps an inset (23:20, 27:16) | **Fig. 4** (d) | done; 8 labelled augers with their measured delivery |
| "Keep Fig 3b, 3a"; "drop 3c or SI"; "4b, use all powders" | Fig. 3 is fine (29:26); 3c's slow/fast split not needed (29:41–30:20); 4b with every powder, a bar graph of mass per tap with error bars (30:49–31:39) | **Fig. 5** (old 3a, 3b + tap bars for all 13 powders); old 3c → **SI Fig. S2** without the shading | done |
| "4a better as table, maybe SI" | 30:32 | **Table S1** | done |
| "5d, separate, drop or SI" | Fig. 5d implies a link to the y-axis that isn't there; drop it or give times in the text (32:03–32:50) | **Fig. 6** (old 5a–c); times in **Table 3**; old 5d → **SI Fig. S3** on its own | done |
| "Generative CAD comparisons": "tap collar", "Zoo comparison" → **Fig** (blue), "CADSmith", "Mounting plate gap" | Tool comparison as text in the main text, images in the SI (15:50–16:53); show CADSmith's results (16:04); mounting-plate gap optional (17:05) | **SI Fig. S1** (one prompt, three tools; tap collar; plates) | done |
| **Fig 3)** (blue) "Assembly steps / instructions, plates, adjusting height" | Instructions and adjusting the height in the SI (26:32); Will's laser-cut modular stand (20:49) | **SI Fig. S4** | not remade: no photos or video of the new stand exist (decision 6) |
| "discussion section: lessons learned" | 17:23 | text, not a figure | for the manuscript pass |
| (not on the board) | Fig. 6 of the draft (Sam's sketch beside his own Onshape model) reads as "drawing, then what the AI made" (23:37) | multi-doser sketch and Onshape model moved into the engineer row of Fig. 2; no separate future-work figure | done (decision 7) |

## Figures and tables

| | Main text | SI |
|---|---|---|
| Figures | 1 the doser · 2 AI and engineers over time · 3 how a dose runs · 4 using the doser · 5 open-loop delivery · 6 closed-loop doses | S1 generative-CAD comparison · S2 variation between revolutions · S3 time per dose · S4 assembly (existing) |
| Tables | 1 the 13 powders · 2 test protocols · 3 closed loop by target · 4 AI tools, dates and models | S1 open-loop per powder |

PDFs are in [`figures/`](figures/), PNG previews in [`preview/`](preview/), LaTeX and Markdown
tables in [`tables/`](tables/). Every image is a committed render, photograph or video frame;
[`assets/`](assets/) holds the copies used, and each `SOURCES.json` gives the comment, branch
or commit it came from.

## Decisions for Sam and Sterling

1. **Which doser in Fig. 1?** The photo is the rig as tested (11 Sep). Since then the stand was
   replaced (2 Oct) and the tap-collar block changed (Oct–Nov, #203). Every result in the paper
   comes from the 11 Sep configuration, so the as-tested photo may be the right one, with the
   final version as a new photo at the end of Fig. 2a (placeholder there now). Or take a new
   photo for Fig. 1.
2. **Brand names in photos.** The balance's maker and model are legible in Figs. 1a and 4c;
   Digital Discovery prefers no brand names in figures. Keep, crop, or blur?
3. **Real keyframes for the dose phases.** No downloadable footage shows bulk, fine and tap
   clearly, so Fig. 3c uses CAD renders for the tube positions and livestream stills only for
   before and after. The clearest real footage is the 4 Sep 1 g salt dose on the livestream
   (YouTube `xjtJNMo8DKw`, 4:12:58–4:14:23), which can be fetched on the Pi.
4. **Two doses in Fig. 3.** The request and reply are the 8 g AlSi10Mg atomizer charge
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

## Rebuild

```bash
cd paper/v2
python3 make_results_figures.py     # Figs. 5, 6, S2, S3; Tables 1, 3, S1
python3 make_fig2_timeline.py       # Fig. 2a, 2b
python3 make_photo_figures.py       # Figs. 1, 3, 4 (Fig. 3c reads the raw serial log from git)
python3 make_si_cad_comparison.py   # SI Fig. S1
python3 make_tables.py              # Tables 2, 4 and the failure-modes table
```

`make_si_cad_comparison.py` renders the Zoo tap-collar STL once from the issue #104
attachment (see `assets/cadcompare/SOURCES.json`); the rendered PNG is committed, so later
runs do not need the download. `make_photo_figures.py` imports helpers from
`paper/figures/make_figures.py`, `make_data_figures.py` and `data/build_dose_traces.py`.
