# Review of 17 Nov 2026: Sam's notes on the v2 figures and tables

Source: Sam's comment on PR #209, 17 Nov 2026. Sam's points are paraphrased below, each with
what was done in the session of 17 Nov and what the next session has to do.

## Why the figures were not re-rendered on 17 Nov

The Claude workflow runs `anthropics/claude-code-action@v1`. That action treats a pull request
as **untrusted** when its author does not have write access, and any `[bot]` account counts as
untrusted. PR #209 was opened by Claude, so the action launched the session with a deny list
covering `python`, `python3`, `pip`, `bash`, `sh`, `make`, `node` and other interpreters
(`src/github/validation/untrusted-pr.ts` in the action). Every figure in `paper/v2/` is drawn
by a Python script, and `pdflatex` (MiKTeX) is not installed on a fresh runner. So this session
could edit text but could not produce a single new image. It did not try to work around the
block.

To unblock, a maintainer can do either of the following:

- **Turn the restriction off for this repository.** In `.github/workflows/claude.yml`, add
  `restrict_untrusted_prs: "false"` under `with:` on both `claude-code-action` steps. The
  action's own warning names this input. The trade-off: on a pull request from a fork, the
  session could then run code from that pull request while it holds the job's tokens. Only
  people with write access can trigger `@claude` here, but they could still trigger it on such a
  pull request.
- **Or ask from an issue instead of this PR.** The restriction applies only to pull requests.
  For example, open an issue that says "`@claude` apply the 17 Nov notes in
  `paper/review_2026-11-17/NOTES.md` on branch `claude/figures-tables-v2` and push there".

## What was done on 17 Nov (no rendering needed)

- New captions for Figs. 1–7 in `paper/v2/build_figures.py` (the source) and
  `paper/v2/FIGURES-AND-TABLES.md`. `figures.tex`, `figures.pdf` and the previews are
  regenerated from `build_figures.py`, so they still show the 11 Nov captions.
- The Fig. 6b data check and the Fig. 6c "waves" check, both below.
- The Fig. 5a/b crop question, answered below.
- Two renders of the flexible snap-in brackets copied in for Fig. 3c:
  `paper/v2/assets/timeline/eng_flexible_bracket_original.png` and
  `eng_flexible_bracket_current.png`, from the Onshape download of #193 (PR #200, commit
  526f90b). Provenance is in `assets/timeline/SOURCES.json`.

## Point by point

| # | Sam's note | Done on 17 Nov | For the next session (with Python) |
|---|---|---|---|
| G | Every figure needs a caption; we will edit them. | Every figure already has a full caption: under each image in the PR description and in `FIGURES-AND-TABLES.md`, and in `figures.pdf`. The previews are rendered without captions (11 Nov review), which is probably why they looked bare. Captions updated for the points below. | Render each preview **with its caption underneath** (crop the pages of `figures.pdf`, not the caption-less `figures-preview.pdf`), so a caption travels with its image. Move the captions out of `build_figures.py` into a `CAPTIONS.md` that the team can edit directly and the build reads. |
| 1.1 | Fig. 1a: overlapping labels, e.g. "section in (c)" over the "20:44 gear pair" line. | Caption no longer refers to the dashed box. | Remove the dashed box and its label; add "(section view in (c))" to the auger-tube callout; re-check every callout line for crossings. |
| 1.2 | Fig. 1b: callouts as close to their parts as makes sense (18, 11, 7, 8, 16, 2, 10, 9, 20, 21 cross the image). Main parts in the caption; screws and other minor parts in the SI. | Caption lists the main parts by bill-of-materials number (19, 25, 21, 23, 15, 20, 9, 12, 14, 4, 7, 2, 1); screws and nuts are left to the SI. | Re-render the #170 exploded view for the main text with **only the 13 main parts** labelled, each balloon beside its part with a short leader, keeping the BOM numbers so the SI table still applies. The full 25-item version, with every screw, moves to SI Fig. S4. |
| 2.1 | Fig. 2a: swap the whole-module request and the bracket drawing, so that the drawing is right next to the bracket made from it, and the "drawing given to the agent" arrow never crosses the timeline. | Caption says the bracket is "shown beside the drawing". | Read as: put the bracket drawing (grey frame, engineer tag) in the AI row directly beside the AI bracket, in the slot the whole-module item had, and give the red arrow a short sideways path between them. The whole-module item moves along one slot and stays an AI item. **To confirm with Sam.** |
| 2.2 | Fig. 2a: tag the engineers' items as the AI items are tagged, in another colour (red or green); every item except perhaps the photographs. | Caption: engineer and tool tags in green. | Tags from the issue authors: bracket drawing, Sam, hand drawing (#46); auger, cap and gear, Sam, Fusion 360 (#120); multi-doser sketch and Onshape model, Sam (27 Oct transcript, 23:37); first glove-box dose, Will (#117), photograph. **Hackathon sketch: author not recorded; to confirm.** |
| 2.3 | Fig. 2b is good; put the two Claude Code rows on one line, each keeping its label. | Caption updated. | One row, two bars: "Claude Code, local: Sonnet 4.6" (23–25 Apr) and "Claude Code, GitHub Actions: …" (from 30 Jun). |
| 3.1 | Fig. 3a: the last picture shows the electronics carriage, which belongs to the multi-doser. Use Ethan's new bracket that holds the solenoid without the tap collar (#203). | Caption updated. | Needs a render or photo of Ethan's solenoid bracket (see the list of pictures needed). |
| 3.2 | Fig. 3b: the first picture should be the very first auger, made after the hackathon; if there is no cross-section, add it to the list of pictures needed. | Caption updated (first auger, #16 → team's Fusion 360 auger). | No committed cross-section exists, but the source does: `cad/auger/archimedes-auger.scad` (PR #16). Render a half-section from it with OpenSCAD in the same style as `ai_storage_auger_xsec.png`. Ask Sam whether to keep the AI storage auger (#49) as a middle image: it is the auger the Fusion 360 part recreated. |
| 3.3 | Fig. 3c: add the later bracket iterations, ending with today's flexible brackets, with authors and tools. | Caption updated; the two flexible-bracket renders are copied in. | Sequence: drawing (Sam, #46) → AI model (Copilot, #47) → the bracket on the tested rig (crop of the 11 Sep photo) → original flexible bracket (Onshape) → current flexible bracket (Onshape). Authors and dates of the two flexible versions are still needed. |
| 4.1 | Fig. 4a: the text boxes can be much smaller; shorter, wider boxes leave more room for the trace below. | n/a (layout). | Request and reply cards in one wider, shorter row; free the height for (c). |
| 4.2 | Fig. 4b: "powder" overlaps the boxes; the feedback loop has a break. | n/a. | Move the "powder" label above the arrow, clear of both boxes; draw the loop back as one continuous path with a single arrowhead. |
| 4.3 | Fig. 4c: use braces (or triangles) for the stages: the leaders read as moments, not spans. Space the labels so nothing overlaps (the "Bulk: 45°" line is too close to the green Claude box); move the Before image left to give the stage images more room. | Caption describes the braces. | Replace the phase leaders with a horizontal brace over each phase's span; shift "Before" to the left edge; re-space the labels. |
| 5.1 | Fig. 5a: the auger is off to the side. Was that our crop? | **Yes, it was our crop.** In the photo the auger is near the middle (about 41–57% across); the crop kept 5–60% of the width, which pushed it to the right edge. | Crop `(0.22, 0.25, 0.77, 1.0)` instead of `(0.05, 0.25, 0.60, 1.0)`: same size, auger centred. |
| 5.2 | Fig. 5b: same problem. | **Yes, our crop again.** The frame is the dose video's side-by-side composite; the crop kept 12–45% of its width and cut off the auger's capped end on the left. | Crop `(0.0, 0.0, 0.33, 1.0)` instead of `(0.12, 0.0, 0.45, 1.0)`: the whole auger and both hands. |
| 5.3 | Fig. 5c: the caption should stress that the aluminium cup is part of the alloy workflow. | Caption: "The aluminium cup is part of the alloy workflow itself: the dose lands directly in the cup used for the next step in making the alloy, so the powder is never transferred." **Sam: please check this wording, and the grade (6063?).** | None beyond the grade. |
| 5.4 | Fig. 5d: Sam will send a better photo of the augers side by side. | Waiting. | Swap in Sam's photo and redo the callouts. |
| 6.1 | Fig. 6a: note the tilt. | Caption: every panel at 22.5° tilt. | Also put "22.5° tilt" in the axis labels or a panel note. |
| 6.2 | Fig. 6b: how can a tap give negative mass (AlSi10Mg, Si)? Check the data and explain. | **Checked: the data are right, but the bars are noise** (see below). Caption explains it. | Stop drawing unresolved tap means as bars: plot them as "not resolved" with the run's noise level, as Table S1 does. |
| 6.3 | Fig. 6c: say it is a representative selection; discuss the flow coming in waves. | Caption: four representative powders; the waves quantified (see below). | Mark one revolution period (4 s) on the axis. Add the waves to the Results/Discussion when the manuscript is rebuilt. |
| 6.4 | Fig. 6: following a row from (a) across to (b) is hard. Also make a second version with banded rows, as in Fig. 7. | n/a. | Version B: alternate rows shaded across (a) and (b), with the powder names repeated or the panels butted together. |
| 7.1 | Fig. 7: say (caption or text) that this is largely a control problem that we are actively working on; each marker is one experiment. | Caption updated. | Same sentence in the Results when the manuscript is rebuilt. |
| 7.2 | Fig. 7: percent of target is a moving reference between the panels; dose error in mg may be more helpful. | Noted. | Version B: the same three panels with error in mg (limit bands ±5, ±10 and ±50 mg). Version C, to compare: all three targets on one axis in mg, plus a box plot of error by target (50 mg, 200 mg, 1 g). |

## Fig. 6b: the negative tap masses

A tap cannot remove powder. The tap value is the balance reading after the tap minus the reading
before it. For AlSi10Mg and the coarse silicon (−110/+200 mesh) the reading had not settled, so
the difference is noise:

- **Noise far larger than a tap.** In each powder's run, protocol A (eight readings at
  22.5°, nothing moving) gave a standard deviation of **29 mg** for AlSi10Mg
  (run `20260821T151337Z_alsi10mg`) and **20 mg** for the coarse silicon
  (`20260820T214823Z_silicon-110-200`). The NaCl run that resolves a 0.9 mg tap
  (`20260812T215154Z_salt`) had a baseline standard deviation of 0.0 mg.
- **Same powder, opposite sign.** NaCl's own noisy run on 21 Aug (`20260821T192031Z_salt`,
  baseline standard deviation 2.9 mg, tap standard deviation 10.7 mg) also gave a negative tap
  mean, −4.1 mg, against +0.9 mg in the quiet 12 Aug run. The sign follows the noise, not the
  powder. The AlSi10Mg, silicon and noisy NaCl runs were all made on 20–21 Aug.
- **Every reading flagged.** The firmware flagged all eight AlSi10Mg tap trials at 22.5° as
  `unsettled`, with a per-reading noise (σ) of 7–15 mg, and seven of the eight silicon trials.
- **Scattered both ways.** The single-tap differences ran from −16.8 to +21.6 mg for AlSi10Mg
  and from −11.6 to +7.1 mg for silicon. The means (−1.9 and −3.5 mg) are within a standard error
  or two of zero.
- **A fresh load just before each tap.** Each tap trial follows a one-revolution re-feed. For
  these fast powders that re-feed drops 0.2–0.8 g into the cup just before the tap, which may
  be part of why the balance had not settled.

So the figure is a faithful plot of the numbers, but a bar is the wrong way to show a value that
is not resolved. Table S1 already prints these in italics ("within the balance noise of its
run"). Until 11 Nov, Fig. 6b also styled them differently; that styling was removed at the 11 Nov
review, which is what made the negative bars look like measurements. Data:
`paper/figures/candidates/data/feed.csv` (phase `tap`, `tilt_deg` 45.0, the recorded tilt for
22.5°) and `trials.csv`.

## Fig. 6c: the waves

Under continuous rotation at 15 rpm (one auger revolution every 4 s), the powder did not stream
evenly; it arrived in surges, one per revolution:

- **AlSi10Mg** (`20260821T151337Z_alsi10mg`): surges at about 3.4–5.4 s, 7.3–9.2 s,
  11.5–13.4 s and 15.7–17.2 s, each adding 190–250 mg, with only 10–30 mg in the 2 s between
  surges.
- **NaCl** (`20260812T215154Z_salt`): surges at about 2.4–4.4 s, 6.4–8.4 s and 10.5–12.5 s, each
  adding 180–215 mg, with 5–15 mg in between. The 21 Aug NaCl run shows the same.

The period matches one auger revolution, so the auger delivers in pulses even when it turns
continuously. That is worth a paragraph in the Results: it sets the resolution of open-loop
dosing, and it is why the controller slows down and taps near the target. Data:
`paper/figures/candidates/data/polls.csv` (`rpm` 15.0).

## Pictures needed

| For | What | From |
|---|---|---|
| Fig. 3a, last image | Ethan's solenoid bracket (#203, first version 7 Nov): a render or a photo, ideally on the doser | Ethan (an Onshape PNG or STEP export is enough). The workflow has no Onshape API keys in `claude.yml`, so the agent cannot export it. |
| Fig. 3b, first image | Cross-section of the first auger (#16) | No picture needed: it can be rendered from `cad/auger/archimedes-auger.scad`. A photo of a cut print would also work, if one exists. |
| Fig. 3c | Who made the two flexible-bracket versions, and when; any bracket between the AI model (14 May) and the flexible bracket | Sam or Ethan |
| Fig. 5d | All the labelled augers side by side | Sam (on the way) |
| Fig. 2a, last engineer slot | The final doser on the new stand | Team |
| SI Fig. S4 | The new stand: CAD or photos, including two heights | Will (see the 12 Nov answer on PR #209) |

## Open questions

1. **Fig. 2a:** is the reading of "swap" in point 2.1 right?
2. **Fig. 2a:** who drew the hackathon sketch (#2)?
3. **Fig. 3b:** replace the AI storage auger with the first auger, or keep it as the middle image?
4. **Fig. 5c:** is the wording about the aluminium cup right, and what is the grade?
