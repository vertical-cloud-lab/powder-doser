# Open decisions for the manuscript (2026-10-01)

> **Superseded** by [`review_2026-10-01/DECISIONS.md`](review_2026-10-01/DECISIONS.md), which carries over every question still open here. Please answer there.

**How to use this file.** Open it in the GitHub editor
([edit link](https://github.com/vertical-cloud-lab/powder-doser/edit/copilot/draft-base-manuscript/paper/OPEN-DECISIONS.md)),
change `[ ]` to `[x]` for your answers, type anything extra after **Notes:**, and
commit straight to the branch. Then ask `@claude` on PR #97 to implement it.

- **Choose one** means pick a single box; **Choose any** means tick as many as apply.
- Boxes that are already ticked show what the draft does **now** (commit `96bf760` or later).
  Leave them ticked to keep that, or move the tick to change it.
- Unticked questions with no default are things only the team knows.

Items 1, 2, 3 and 6 matter most; everything after item 9 is lower stakes.

---

## A. What the tested doser was made of

### 1. Which parts on the tested rig were printed from the Fusion 360 recreations?

**Choose any.** The draft currently says only that the auger (with its 44-tooth gear
band) and the 20-tooth stepper pinion are Fusion 360 recreations. That follows from
the 20:44 gear ratio and your comment; the AI-modelled files specify 16:48. Recordings
are in the [#120 playlist](https://www.youtube.com/playlist?list=PLZTWCFxzhTQv42fTuW2Tjs9o1KuWA_b-I).

- [x] Storage auger with gear ([video](https://youtu.be/EID3ppxmE1U))
- [x] Stepper pinion ([video](https://youtu.be/EO9qnYssKRQ))
- [ ] Servo pinion ([video](https://youtu.be/X1pHIL-XZiQ))
- [ ] Tap collar ([video](https://youtu.be/9xfo0sK6lpc)) *(if ticked, the "final tap collar came from Zoo Design Studio" story needs a qualifier)*
- [ ] Mounting plate ([video](https://youtu.be/v8my5C7718w))
- [ ] Baseplate ([video](https://youtu.be/zOh_KagOwOU))
- [ ] Bracket / flexible brackets ([video](https://youtu.be/8fVVT5tipzY))
- [ ] Cap ([video](https://youtu.be/sKrvGBTUc8U))
- [ ] All of the above: the whole tested rig was printed from the recreations

**Notes:**

### 2. How prominently should the paper say the tested rig used redrawn parts?

**Choose one.** The headline claim is that the parts were designed by AI; the dosing
results come from a rig that carries at least some human-redrawn parts. A reviewer
will want to know that, so the draft says it in the abstract.

- [x] Abstract + introduction + Experimental (current)
- [ ] Introduction + Experimental only (drop it from the abstract)
- [ ] Experimental only

**Notes:**

### 3. Do the auger dimensions in the Experimental section describe the printed auger?

**Choose one.** The draft gives 25 mm outer diameter, 21 mm bore, 8 mm core, 2 mm flight,
10 mm pitch, four 4 × 7 mm loading slots and a 3 mm exit hole. These come from the
AI-modelled files. If the tested auger is the Fusion 360 recreation, some may differ.

- [ ] Yes, they match the printed (recreated) auger
- [ ] No, here are the correct values (in Notes)
- [ ] Not sure; someone will measure the printed auger

**Notes:**

### 4. Fusion 360 files for the recreated parts

**Choose one.** No Fusion 360 files for the doser parts are in the repository (only
vendor `.f3d` files are). The Data availability statement promises all design files,
and the tested rig depends on the recreations.

- [ ] We'll upload the `.f3d`/STEP files (and public share links) before submission
- [ ] Public share links only, listed in the README
- [ ] Neither; the paper will say the recreations are shown in the videos only

**Notes:**

### 5. Title

**Choose one.**

- [x] An open-source, 3D-printed auger powder doser designed with generative artificial intelligence (current)
- [ ] An open-source, 3D-printed auger powder doser **first** designed with generative artificial intelligence
- [ ] Other (in Notes)

**Notes:**

---

## B. Authors

### 6. Corresponding authors' e-mails and affiliation

Both Sam and Sterling are now marked as corresponding authors. Two details are open.

**Sam's e-mail. Choose one.**

- [ ] Use the address on Sam's git commits
- [ ] Use this BYU address (in Notes)

**Sterling's e-mail and affiliation. Choose one.** The draft lists Sterling under
Materials Science & Engineering, University of Utah, with `sterling.baird@byu.edu`
(the address on Sterling's GitHub profile and commits), which may not match.

- [ ] Keep University of Utah MSE, with a Utah e-mail (in Notes)
- [ ] Change to BYU (department in Notes), keep `sterling.baird@byu.edu`
- [ ] Both affiliations (details in Notes)

**Notes:**

### 7. Acknowledgements for other contributors

**Choose any.** Two people outside the author list have commits on the project:
Devora Najjar wrote the first Archimedes-auger OpenSCAD model (April 2026), and
Marcus Madsen uploaded files on 4 August 2026.

- [ ] Acknowledge Devora Najjar
- [ ] Acknowledge Marcus Madsen
- [ ] Neither (not part of this paper's work)
- [ ] Discuss authorship for Devora Najjar with the team

**Notes:**

---

## C. Data and limitations

### 8. Bench noise and the dust plate (#157)

**Choose one.** You asked whether the #157 dust-plate root cause needs mentioning. My
answer was no, so the draft no longer mentions it, in the main text or the SI. What
stays is the noise floor itself. It decides which small effects (single taps,
static holds) can be resolved, and it is confounded with powder group: every
research-relevant powder was measured in the noisier period.

- [x] Keep the noise floor, drop the root cause (current)
- [ ] Also drop the noise-floor discussion and SI Fig. S2
- [ ] Put the dust-plate root cause back, as one sentence in the SI

**Notes:**

### 9. Speed sweep (protocol D)

**Choose one.** Each speed was measured once, always in the same order, and a firmware
timing error over-rotated the auger by 15 to 54%. Since all data are in, the draft no
longer promises a repeat. It reports the exponents (median 0.78) as an indication only
and does not plot them.

- [x] Text only, as an indication (current)
- [ ] Add an SI plot with these caveats in its caption
- [ ] Drop the speed-sweep results entirely

**Notes:**

### 10. Fumed silica

**Choose one.** Fumed silica's only run failed screening, because the bench camera could
not show the outlet to rule out a blockage. The figures still list it as "did not
move", and the draft now says so explicitly in the Experimental section.

- [x] Keep it, with that disclosure (current)
- [ ] Keep it in Table 1 only, as "not reliably tested", and remove it from Fig. 3
- [ ] Remove fumed silica from the results

**Notes:**

### 11. Vibration motor

**Choose one.** The vibration driver never worked, so there are no vibration data. The
draft still describes the motor as part of the design (Fig. 1a, BOM) and says plainly
that it was never characterised.

- [x] Keep it in the design and BOM, with the "never characterised" statement (current)
- [ ] Remove it from the design description, Fig. 1a labels and the BOM

**Notes:**

### 12. SEM or other powder characterisation

**Choose one.** SEM images came up at the 1 September meeting, but none are in the
repository. The draft has no SEM figure and says particle size and shape were not
measured.

- [x] None exist; no SEM figure (current)
- [ ] They exist; I'll point you to the files (location in Notes)
- [ ] Add the literature particle-size and density values from #163 as an SI table, labelled as literature values

**Notes:**

### 13. Glovebox demonstration at the U of U Lessard Lab

**Choose one.** The playlist has glovebox videos from the Lessard Lab, including a
successful three-phase dispense. The paper does not mention them.

- [x] Leave out (current)
- [ ] Add a short, qualitative paragraph (an outside lab using the doser in a glovebox)

**Notes:**

---

## D. Figures and scope

### 14. Fig. 6: future multi-doser

**Choose one.** Fig. 6 used to show the old radial AI-CAD concept. It now shows the
#128 hand sketch and Onshape model of the roller-chain design.

- [x] Sketch + Onshape model from #128 (current)
- [ ] Use a photo or video still of the printed prototype instead (point me to one)
- [ ] Go back to the old radial concept
- [ ] Drop Fig. 6 and keep the text only

**Should the paper say the multi-doser was modelled in conventional CAD, not by AI? Choose one.**

- [x] Yes, one sentence (current)
- [ ] Yes, and say why (reason in Notes)
- [ ] No, leave the tool unstated

**Notes:**

### 15. SI Fig. S3: AI-agent activity per week (new)

**Choose one.** This is new. Per week, it shows requests to the agents (754 in total)
and commits by author (the agents wrote 789 of 877). The counts cover all repository
work (CAD, firmware, analysis and writing), not only part design. Preview:
[figS3_ai_usage.png](figures/preview/figS3_ai_usage.png).

- [x] Keep as is (current)
- [ ] Restrict to CAD-design work only (needs per-issue labelling, slower)
- [ ] Drop it

**Notes:**

### 16. The generative-AI half of the paper (spec Q5)

**Choose one.** It currently has Table 2 (failure modes) and three paragraphs. The
round-2 Edison reviewer asked for a quantitative design-log analysis.

- [x] Keep the current length (current)
- [ ] Add a quantitative design-log analysis to the SI (acceptance rates, defect counts by tool)
- [ ] Expand in the main text too

**Notes:**

### 17. Rough time comparison

**Choose one.** The draft compares about 3 h of edited Fusion 360 recordings (nine
parts) with a single 3 h Zoo Design Studio session. Edited video is shorter than the
actual working time.

- [x] Keep as a rough comparison (current)
- [ ] Replace with actual working hours (values in Notes)
- [ ] Remove the comparison

**Notes:**

---

## E. Next steps

### 18. After these decisions

**Choose any.**

- [ ] Check the manuscript against the journal's hardware-paper requirements and report gaps (spec Q4)
- [ ] Run another Edison mock review (editor + three reviewers, #91 personas)
- [ ] Do the jargon and flow pass again after the edits

**Notes:**

### 19. Anything else

**Notes:**
