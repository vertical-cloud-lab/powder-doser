# Decisions for the next revision (2026-10-01, round 2)

**How to use this file.** Open it in the GitHub editor
([edit link](https://github.com/vertical-cloud-lab/powder-doser/edit/copilot/draft-base-manuscript/paper/review_2026-10-01/DECISIONS.md)),
change `[ ]` to `[x]` for your answers, add anything extra after **Notes:**, and
commit straight to the branch. Then ask `@claude` on PR #97 to implement it.

- **Choose one** means tick a single box; **choose any** means tick as many as apply.
- Ticked boxes show what the draft does **now** (commit `964f9ab` or later). Leave
  them ticked to keep that, or move the tick to change it.
- Questions with nothing ticked are facts only the team knows.

This file replaces [`paper/OPEN-DECISIONS.md`](../OPEN-DECISIONS.md), which nobody had
filled in yet; its open questions are carried over in section D. A parallel session
wrote [`paper/meeting_2026-10-01/MEETING-DECISIONS.md`](../meeting_2026-10-01/MEETING-DECISIONS.md)
for questions raised at the 1 Oct meeting. Where the two overlap, the question here
just points there, so nothing has to be answered twice. Items 1, 2, 4 and section E
matter most.

> **Status, 8 October 2026.** This file was not changed in the 8 October round, so every
> pre-ticked default stands and nothing unticked was implemented, with two exceptions
> that came from elsewhere: item 5 (CADSmith) now follows Sterling's 2 October PR comment
> ("only able to generate very simplified kind of blocky geometries"), and item 27's
> tool months were added because MEETING-DECISIONS.md item 13 asked for them. Item 8 is
> answered by the evidence: the Fig. 1b frame is from the 24 July session in the
> University of Utah glove box (#117), and the caption now says so. Still open: items 1
> (one auger per powder?), 4, 20–23 and 25–27.

Sources: Sam's [part-1 video notes](NOTES-part1.md), the 1 Oct Sam/Sterling meeting
([corrected transcript](../meeting_2026-10-01/TRANSCRIPT-corrected.md)),
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

- [x] Yes, one auger per powder (I'll add one sentence to the Experimental section)
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

**Answer in [MEETING-DECISIONS.md](../meeting_2026-10-01/MEETING-DECISIONS.md), items 1–4.** For reference, SI Table S2 now lists the eight Fusion 360 share links from PR #170, and the text says the auger, its cap and the stepper pinion were on the rig for every test.

### 4. The tap collar on the tested rig

**Choose one.** The draft tells two stories that need reconciling. Fig. 2b and Table 2
say the production tap collar was remodelled in Zoo Design Studio (three iterations).
Sam said in the video that the current tap collar and solenoid are different, and PR #170
has a Fusion file called `tapcollar`.

- [ ] The Zoo collar was on the rig for all tests; the new collar came later
- [ ] The Fusion/Onshape collar was on the rig for all tests (I'll qualify the Zoo story)
- [ ] It changed during the campaign (dates in Notes)

The plate the collar sits on is a separate question:
[MEETING-DECISIONS.md](../meeting_2026-10-01/MEETING-DECISIONS.md), item 4.

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
camera as the June render. Its auger, cap and pinion are the real files; the solenoid
and tap collar are modelled from photos, and the plates, brackets and stepper are still
June stand-ins. Who makes the refreshed render, and whether it should show who modelled
what, are in [MEETING-DECISIONS.md](../meeting_2026-10-01/MEETING-DECISIONS.md), item 5.

- [x] Keep the #170 render, and refresh it when the remaining real parts are swapped in (current)
- [ ] Replace it with a photo of the current rig
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

- [ ] Keep the 2-D section (current)
- [x] Use a shaded 3-D cut-away render instead
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

- [ ] "a tube with a screw inside" (current)
- [ ] "an Archimedes screw: a tube with a spiral blade inside"
- [x] "a tube with a spiral inside"

### 13. "The kind that makes a phone vibrate"

**Choose one.** Sam thought it unnecessary, so I removed it.

- [x] Removed (current)
- [ ] Restore it

### 14. Hackathon origin

**Answer in [MEETING-DECISIONS.md](../meeting_2026-10-01/MEETING-DECISIONS.md), item 12.**

### 15. The atomizer

**Answer in [MEETING-DECISIONS.md](../meeting_2026-10-01/MEETING-DECISIONS.md), item 10.**

### 16. Will's newer small-dose data

**Answer in [MEETING-DECISIONS.md](../meeting_2026-10-01/MEETING-DECISIONS.md), item 11.** The abstract now says "ongoing controller work targets this", and the future-work paragraph says better control should make 50 and 200 mg doses more reliable.

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

**Choose one.** The exact abstract wording is
[MEETING-DECISIONS.md](../meeting_2026-10-01/MEETING-DECISIONS.md), item 3; this is
only where it is said.

- [x] Abstract, introduction and Experimental (current)
- [ ] Introduction and Experimental only
- [ ] Experimental only

### 20. Corresponding authors' e-mails and affiliation

**Sam's e-mail. Choose one.**

- [x] Use the address on Sam's git commits
- [ ] Use this address (in Notes)

**Sterling's affiliation and e-mail. Choose one.** The draft lists Utah MSE with
`sterling.baird@byu.edu`.

- [ ] University of Utah MSE, with a Utah e-mail (in Notes)
- [x] BYU (department in Notes), keep `sterling.baird@byu.edu`
- [ ] Both affiliations (details in Notes)

**Notes:**

### 21. Acknowledgements

**Choose any.**

- [x] Acknowledge Devora Najjar (first Archimedes-auger OpenSCAD model, April 2026)
- [ ] Acknowledge Marcus Madsen (uploaded files on 4 August 2026)
- [ ] Acknowledge the lab members who printed or assembled parts (names in Notes)
- [ ] None of these

**Notes:**

### 22. Design files and design log before submission

**Choose any.** The Data availability statement promises all design files and the
128-entry design log. Neither is on `main` yet.

- [ ] Merge PR #74 (`DESIGN-LOG.md`, updated today to 128 entries)
- [x] Archive a tagged release with a DOI (for example Zenodo) at submission, and cite it

PR #170, the Onshape parts and the build guide are in
[MEETING-DECISIONS.md](../meeting_2026-10-01/MEETING-DECISIONS.md), items 7–9.

**Notes:**

### 23. PR #150 (the old test-protocol table)

**Choose one.** Its files still say "90° = vertical", and Table 3 in the main text now
covers the same ground in tube angles. A dated correction note is on the PR description.

- [ ] Close PR #150 as superseded by Table 3
- [x] Fix its files to 0/22.5/45° and keep it open

### 24. Smaller items (defaults are the current draft)

- Speed sweep: [x] text only, as an indication (current) · [ ] add an SI plot · [ ] drop it
- Fumed silica: [x] keep, with the screening disclosure (current) · [ ] Table 1 only · [ ] remove
- SEM or powder characterisation: [x] none (current) · [ ] add the #163 literature values as an SI table
- U of U glovebox demonstration: [ ] leave out (current) · [x] add a short qualitative paragraph, and also put Philip Lampkin in the acknowledgements (maybe there was one other person, too?)
- SI Fig. S3 (AI activity per week): [x] keep (current) · [ ] CAD work only · [ ] drop
- Generative-AI section: [x] current length (current) · [ ] add a quantitative design-log analysis to the SI
- Fusion vs Zoo time comparison: [x] keep as rough (current) · [ ] actual hours (in Notes) · [ ] remove

**Notes:**

---

## E. From the round-3 Edison mock review

The [round-3 review](../mock_review/mock_review_r3.answer.md) (editor plus three reviewers,
#91 personas) recommends **major revision** from all three reviewers. The real data fixed
the main round-2 objection. Writing-only fixes are already in (commit `964f9ab`): the 24 of
39 dose count, "conveyed no measurable amount", section numbering, the per-dose record,
caption provenance, cost exclusions, and four plainer sentences. The rest needs your call.

### 25. New analysis of data we already have

**Choose any.** Each of these uses only existing records.

- [x] SI table of every dose attempt: valid, excluded (with reason), and not attempted, by powder and target (all three reviewers)
- [x] Representative mass-against-time traces of closed-loop doses at 50 mg, 200 mg and 1 g, with phase changes marked (Abolhasani)
- [x] Balance noise after actuation, and whether pass/fail at 50 mg survives that noise, split by round and location (Khinast), in SI
- [x] CAD-only analysis of the design log: parts, iterations, failure types, and what caught each (automated check or person) (Schulz; also old item 16), keeping it brief, probably tabular, and only in SI
- [x] Table of the tested auger's dimensions against the AI-modelled auger's (Khinast), tabular and based on a comparison of what changed
- [x] Derive the "less than one atomic percent" composition-error claim in the SI, or soften it (Khinast), noting that you should be looking at byu-vcl a lot and that you can send your own Edison query. Note that for our own alloy workflows, we'll probably be processing total batch sizes between 10-500 grams 
- [ ] None for now

**Notes:**

### 26. New experiments before submission

**Choose any.** The review asks for these. Each one can instead be stated as a limitation.

- [ ] Hand-weighing baseline: the same targets dosed by a person with a spatula, timed (Abolhasani)
- [ ] Bulk and tapped density (or particle size) of the 13 powders (Khinast; see #163)
- [ ] Doses at defined fill levels, and residual powder left in the tube (Khinast)
- [ ] Repeated-use wear and fouling of the PLA auger with AlSi10Mg (Khinast)
- [ ] A run of consecutive unattended doses, logging every human intervention (Abolhasani)
- [ ] Fix the vibration driver and run protocol F (Khinast)
- [x] None; state these as limitations (current)

**Notes:**

### 27. Writing-only changes the review asked for

**Choose any.**

- [x] One-page AI-CAD workflow in the SI: an example dimensioned drawing, the interface checklist, and when a part counted as finished (Schulz)
- [x] List the human tasks between doses (filling, positioning, taring, clearing faults) (Abolhasani), in the SI
- [x] Drop the "one or two Zoo iterations matched seven or eight coding-agent iterations" numbers, as they are impressions (Schulz)
- [x] Give the months each AI tool was used, with model names where the logs record them (Schulz)

**Notes:**

---

## F. Next steps

**Choose any.**

- [ ] Implement the writing-only items from the round-3 review
- [ ] Wait for part 2 of Sam's video review, then do both together
- [ ] Another plain-language pass after these edits
- [x] use cringe-filter package

**Notes:**
