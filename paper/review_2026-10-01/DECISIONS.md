# Decisions for the next revision (2026-10-01, round 2)

**How to use this file.** Open it in the GitHub editor
([edit link](https://github.com/vertical-cloud-lab/powder-doser/edit/copilot/draft-base-manuscript/paper/review_2026-10-01/DECISIONS.md)),
change `[ ]` to `[x]` for your answers, add anything extra after **Notes:**, and
commit straight to the branch. Then ask `@claude` on PR #97 to implement it.

- **Choose one** means tick a single box; **choose any** means tick as many as apply.
- Ticked boxes show what the draft does **now** (commit `6b6950d` or later). Leave
  them ticked to keep that, or move the tick to change it.
- Questions with nothing ticked are facts only the team knows.

This file replaces [`paper/OPEN-DECISIONS.md`](../OPEN-DECISIONS.md), which nobody had
filled in yet. Its open questions are carried over in section D, so there is one place
to answer. Items 1–4 matter most.

Sources: Sam's [part-1 video notes](NOTES-part1.md), the 1 Oct Sam/Sterling meeting
([`Powder Doser Manuscript Overview.txt`](../../Powder%20Doser%20Manuscript%20Overview.txt)),
Sterling's 1 Oct comment on PR #97, PR #170 (current-design render and Fusion files),
and the round-3 Edison mock review (section E).

---

## A. Facts I changed from Sam's notes; please confirm

### 1. Which auger ran the 13-powder tests?

**Choose one.** The draft now describes Sam's Fusion 360 "Auger Threaded Storage"
([#117](https://github.com/vertical-cloud-lab/powder-doser/issues/117#issuecomment-5004533979),
[share link](https://a360.co/4y1oz2H)) as the auger for every test. The tube is filled
through a screw-on cap, the flight covers only the third nearest the outlet, and there
are no loading slots. Fig. 1c is a section through this file.

- [x] Yes: every test (rounds 1 and 2) used this threaded auger with its cap (current)
- [ ] Round 2 only; round 1 (4–21 Aug) used an earlier auger (which one in Notes)
- [ ] Another auger (in Notes)

**Did each powder get its own printed auger?** The design log (entry e114, "Labelled
campaign augers with separate caps") suggests so. **Choose one.**

- [ ] Yes, one auger per powder (I'll add one sentence to the Experimental section)
- [ ] No, one auger, cleaned between powders (I'll say how it was cleaned; method in Notes)
- [ ] Mixed (in Notes)

**Notes:**

### 2. Auger dimensions, measured from the Fusion STL

**Choose one.** I measured `Threaded Auger Final.stl` (from the #117 zip, in PR #170):
250 mm long, 25 mm outside, 21 mm bore, 8 mm core, a single-start flight **0.5 mm thick**
with **10.4 mm pitch** (250/24 mm) on the 83 mm nearest the outlet, a 3 mm exit hole,
a 44-tooth module-1 gear 78–88 mm from the outlet, and a cap thread on the last 27 mm.
Sam said in the video that he needed to check the flight. The 0.5 mm flight is much
thinner than the AI design's 2 mm.

- [x] These match the printed auger (current text and Fig. 1c)
- [ ] Some values are wrong; correct ones in Notes
- [ ] Someone will measure a printed auger with calipers

**Notes:**

### 3. Which parts of the tested rig were printed from the team's Fusion 360 / Onshape files?

**Choose any.** SI Table S2 now lists the eight Fusion 360 share links found in PR #170.
The text says only that the auger, its cap and the stepper pinion are team-made, and that
the tap collar was redesigned. Sam mentioned in the meeting that many parts are now in
Onshape.

- [x] Auger and cap
- [x] Stepper pinion
- [ ] Servo pinions
- [ ] Tap collar
- [ ] Auger brackets
- [ ] Mounting plate
- [ ] Baseplate
- [ ] Some of these are in Onshape rather than Fusion 360 (which ones, with links, in Notes)
- [ ] All printed parts of the tested rig are team-made (Fusion 360 or Onshape)

**Notes:**

### 4. The tap collar on the tested rig

**Choose one.** The draft tells two stories that need reconciling. Fig. 2b and Table 2
say the production tap collar was remodelled in Zoo Design Studio (three iterations).
Sam said in the video that the current tap collar and solenoid are different, and PR #170
has a Fusion file called `tapcollar`.

- [ ] The Zoo collar was on the rig for all tests; the new collar came later
- [ ] The Fusion/Onshape collar was on the rig for all tests (I'll qualify the Zoo story)
- [ ] It changed during the campaign (dates in Notes)

**Notes:**

### 5. CADSmith

**Choose one.** Sam said CADSmith was tried and found about the same as the Copilot coding
agent. The June draft said CADSmith "converged quickly on brackets and plates".

- [x] About as well as the coding agent (Sam's version, current)
- [ ] Converged quickly on brackets and plates (June version)
- [ ] Something else (in Notes)

**Notes:**

### 6. The vibration motor

**Choose one.** The driver never worked, so there are no vibration data. The new render
from PR #170 has no vibration motor, and Fig. 1a now labels only rotation, tapping and
tilt. The text says a vibration motor "was also planned, but its driver never worked".
The BOM still lists it.

- [x] Keep that sentence and the BOM line (current)
- [ ] It is still mounted on the rig; say "fitted but unused"
- [ ] Remove it from the BOM and the build guide too

**Notes:**

---

## B. Figure 1

### 7. Panel (a): the CAD render

**Choose one.** Panel (a) is now the PR #170 render of the current design, from the same
camera as the June render. Its auger, cap and pinion are the real files. The solenoid
and tap collar are modelled from photos, and the plates, brackets and stepper are still
June stand-ins. Sam asked for real models of the stepper and solenoid.

- [x] Keep it until PR #170 swaps in the remaining Fusion/Onshape parts, then refresh (current)
- [ ] Replace it with a photo of the current rig (who takes it, in Notes)
- [ ] Go back to the June render

**Notes:**

### 8. Panel (b): the as-built photo

**Choose one.** The caption now says the photo was taken inside a glove box, as Sam asked.
The photo shows the rig during its first automated dispense, so its tap collar and
solenoid may be older than those in panel (a).

- [x] Keep this photo (current)
- [ ] Replace it with a new photo of the current rig from the same viewpoint
- [ ] Use the 11 Sep rig photo from #156

**Where was the glove box? Choose one.**

- [ ] BYU
- [ ] University of Utah (Lessard Lab), which I'll name in the caption
- [ ] Don't name it

**Notes:**

### 9. Panel (c): the auger section

**Choose one.** Sam liked the old schematic's layout but found it inaccurate and suggested
a CAD section view. Panel (c) is now a true section cut through the Fusion STL, drawn
upright, with the cap, fill opening, plain reservoir, 44-tooth gear, flight, core and
outlet labelled. Preview: [fig1_overview.png](../figures/preview/fig1_overview.png).

- [x] Keep the 2-D section (current)
- [ ] Use a shaded 3-D cut-away render instead
- [ ] Draw it horizontal, as the tube sits when parked

**Notes:**

---

## C. Wording and scope (from Sam's video and the meeting)

### 10. Serial (Oxford) comma

**Choose one.** Sam asked for one. The draft didn't use it, so I applied it throughout
main text, captions and SI ("reviewed, printed, and tested").

- [x] Serial comma everywhere (current)
- [ ] Remove it everywhere (RSC house style allows either)

### 11. What to call the design stages

**Choose one.** Sterling asked for "versions".

- [x] Versions (current)
- [ ] Phases
- [ ] Sprints

### 12. Plain word for the auger's helix in the abstract

**Choose one.**

- [x] "a tube with a screw inside" (current)
- [ ] "an Archimedes screw: a tube with a spiral blade inside"
- [ ] "a tube with a spiral inside"

### 13. "The kind that makes a phone vibrate"

**Choose one.** Sam thought it unnecessary, so I removed it.

- [x] Removed (current)
- [ ] Restore it

### 14. Hackathon origin

**Choose one.** At the meeting, Sterling said the first version (the "powder excavator")
came from a one- or two-day hackathon, and that it has been the same team since. The
draft says only that the project "began as a hand-sketched mechanical scoop".

- [x] Leave it as is (current)
- [ ] Add one sentence: the first concept came from a hackathon (event and dates in Notes)

**Notes:**

### 15. The atomizer

**Choose one.** The meeting summary says to mention using the doser with "the atomizer".
I found nothing about an atomizer in the repository, so I left it out.

- [x] Leave it out (current)
- [ ] Add a sentence (what was done, when, and where it is recorded, in Notes)

**Notes:**

### 16. Will's newer small-dose data

**Choose one.** Sam said Will's control work gives more reliable small doses. The abstract
now says "ongoing controller work targets this", and the future-work paragraph says better
control should make 50 and 200 mg doses more reliable. No new data were added; Sterling
said all the data for this paper are in.

- [x] Mention only, no new data (current)
- [ ] Add a short SI section with Will's newer doses (point me to the issue or PR)

**Notes:**

### 17. Raw tilt settings in the SI

**Choose one.** Nothing in the manuscript says or implies a 90° tilt; tilts run from 0° to
the 45° maximum. One SI sentence (Section S6) explains that the raw records store tilt as
a servo setting of 0, 45 or 90, which the 2:1 gear turns into 0°, 22.5° and 45°. That lets
readers match the raw files to the paper.

- [x] Keep that SI sentence (current)
- [ ] Remove it from the SI; keep the mapping only in the data README

---

## D. Carried over from `OPEN-DECISIONS.md` (still unanswered)

### 18. Title

**Choose one.**

- [x] An open-source, 3D-printed auger powder doser designed with generative artificial intelligence (current)
- [ ] An open-source, 3D-printed auger powder doser **first** designed with generative artificial intelligence
- [ ] Other (in Notes)

### 19. How prominently to say the tested rig uses redrawn parts

**Choose one.**

- [x] Abstract, introduction and Experimental (current)
- [ ] Introduction and Experimental only
- [ ] Experimental only

### 20. Corresponding authors' e-mails and affiliation

**Sam's e-mail. Choose one.**

- [ ] Use the address on Sam's git commits
- [ ] Use this address (in Notes)

**Sterling's affiliation and e-mail. Choose one.** The draft lists Utah MSE with
`sterling.baird@byu.edu`.

- [ ] University of Utah MSE, with a Utah e-mail (in Notes)
- [ ] BYU (department in Notes), keep `sterling.baird@byu.edu`
- [ ] Both affiliations (details in Notes)

**Notes:**

### 21. Acknowledgements

**Choose any.**

- [ ] Acknowledge Devora Najjar (first Archimedes-auger OpenSCAD model, April 2026)
- [ ] Acknowledge Marcus Madsen (uploaded files on 4 August 2026)
- [ ] Acknowledge the lab members who printed or assembled parts (names in Notes)
- [ ] None of these

**Notes:**

### 22. Design files and design log before submission

**Choose any.** The Data availability statement promises all design files and the
128-entry design log. Neither is on `main` yet.

- [ ] Merge PR #170 (Fusion STEP/STL files and the current-design render)
- [ ] Merge PR #74 (`DESIGN-LOG.md`, updated today to 128 entries)
- [ ] Also add the Onshape parts (exports or share links) to the repository
- [ ] Write an illustrated, step-by-step build guide (for example from Sam's narrated videos)

**Notes:**

### 23. PR #150 (the old test-protocol table)

**Choose one.** Its files still say "90° = vertical", and Table 3 in the main text now
covers the same ground in tube angles. A dated correction note is on the PR description.

- [ ] Close PR #150 as superseded by Table 3
- [ ] Fix its files to 0/22.5/45° and keep it open

### 24. Smaller items (defaults are the current draft)

- Speed sweep: [x] text only, as an indication (current) · [ ] add an SI plot · [ ] drop it
- Fumed silica: [x] keep, with the screening disclosure (current) · [ ] Table 1 only · [ ] remove
- SEM or powder characterisation: [x] none (current) · [ ] add the #163 literature values as an SI table
- U of U glovebox demonstration: [x] leave out (current) · [ ] add a short qualitative paragraph
- SI Fig. S3 (AI activity per week): [x] keep (current) · [ ] CAD work only · [ ] drop
- Generative-AI section: [x] current length (current) · [ ] add a quantitative design-log analysis to the SI
- Fusion vs Zoo time comparison: [x] keep as rough (current) · [ ] actual hours (in Notes) · [ ] remove

**Notes:**

---

## E. From the round-3 Edison mock review

*(Added after the review returns; see
[`mock_review_r3.answer.md`](../mock_review/mock_review_r3.answer.md).)*

---

## F. Next steps

**Choose any.**

- [ ] Implement the writing-only items from the round-3 review
- [ ] Wait for part 2 of Sam's video review, then do both together
- [ ] Another plain-language pass after these edits

**Notes:**
