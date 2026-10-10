# Decisions before submission (2026-10-10)

**How to use this file.** Open it in the GitHub editor
([edit link](https://github.com/vertical-cloud-lab/powder-doser/edit/copilot/draft-base-manuscript/paper/submission/SUBMISSION-DECISIONS.md)),
change `[ ]` to `[x]` for your answers, add anything extra after **Notes:**, and
commit straight to the branch. Then ask `@claude` on PR #97 to implement it.

- **Choose one** means tick a single box; **choose any** means tick as many as apply.
- Ticked boxes show what the draft does **now**. Leave them ticked to keep that, or
  move the tick to change it.
- Questions with nothing ticked are facts or choices only the team can supply.

The background for most items is the guidelines audit,
[`GUIDELINES-AUDIT.md`](GUIDELINES-AUDIT.md). Items 1, 5, 9, 10 and 16 matter most.

---

## A. Authors

### 1. Author list

**Choose one.** RSC follows the ICMJE criteria: every author must have contributed
substantially to the design, data or analysis, **and** critically reviewed the draft,
**and** approved the final version, **and** agreed to be accountable for the work.
Contributors who don't meet all four go in the Acknowledgements. Author changes after
submission are "only considered in exceptional circumstances" and need everyone's
agreement, so it is worth settling now.
([RSC author responsibilities](https://www.rsc.org/publishing/journals/processes-and-policies/author-responsibilities))

What the repository records, 23 Apr to 10 Oct 2026. Printing, assembly, bench work,
lab time, Slack and meetings are **not** recorded on GitHub, so treat this as one input
only.

| Author | GitHub | Issues opened | Comments | Commits (own or AI-made on their request) | Requests to AI agents | Active |
|---|---|---|---|---|---|---|
| Sam Charles | swcharles | 28 | 259 | 169 | 160 | 7 May–8 Oct |
| Will Mulberry | williamulbz | 16 | 210 | 83 | 83 | 7 May–9 Oct |
| Luke Winters | lbwinters | 7 | 109 | 14 | 48 | 3 Jun–9 Oct |
| Carl Robison | carl-robison | 0 | 6, all on #116 | 0 | 0 | 30 Jun–9 Jul |
| Gage Erickson | gage-erickson | 0 | 0 | 0 | 0 | assigned himself to #116 (15 Jul) |
| Sterling G. Baird | sgbaird (and two alt accounts) | 51 | 692 | 447 | 436 | 23 Apr–10 Oct |

- Carl's comments include hand tests of eight powders with videos
  ([#116](https://github.com/vertical-cloud-lab/powder-doser/issues/116#issuecomment-4877520306)),
  which later analyses cite.
- Gage's doser-related comments are in `byu-vcl` (sizing a glove box for the doser,
  auger capacity and particle size), and #163 credits him with the angle-of-repose idea.
- The CRediT roles in the draft were written by an AI agent on 11 Jun, before Carl or
  Gage had any recorded activity. They now use standard CRediT names (item 2).

- [x] Keep all six authors (current)
- [ ] Four authors: Sam, Will, Luke and Sterling; thank Carl and Gage in the Acknowledgements
- [ ] Five authors: keep Carl; thank Gage in the Acknowledgements
- [ ] Other (Notes)

**Notes:**

### 2. Author roles (CRediT)

**Choose one.** The roles now read: S.C. conceptualization, methodology, investigation,
validation, writing – original draft. W.M. investigation, validation. L.W. investigation,
software. C.R. investigation, resources. G.E. investigation, resources. S.G.B.
conceptualization, supervision, funding acquisition, writing – review & editing.
("CAD review" became validation and "hardware fabrication" became resources.) Anyone
who reviewed the draft should also get writing – review & editing.

- [x] Keep these roles (current)
- [ ] Change them (who gets what, in Notes)

**Notes:**

### 3. Sterling's affiliations

**Choose one.** Your 21 Jun note on PR #103 asked for the Acceleration Consortium as
an additional affiliation, so the draft now lists it, in the form used on your Honegumi
paper.

- [x] BYU Mechanical Engineering, plus Acceleration Consortium, University of Toronto,
  80 St George St, Toronto, ON M5S 3H6, Canada (current)
- [ ] BYU Mechanical Engineering only

### 4. Sam's e-mail

**Choose one.** Your 8 Oct answer chose Sam's commit address; your 21 Jun note on
PR #103 gave a student address.

- [x] samuelwcharles@gmail.com (current)
- [ ] swc19@student.byu.edu

---

## B. Required by the journal, needs your input

### 5. Licences

**Choose one for the hardware, one for the data.** The repository has only an MIT
licence. The DD guidelines state "a strong preference for open-source hardware
licenses, such as the CERN Open Hardware License", and the Data availability statement
currently says only "an open license (see the repository)". Code stays MIT.

- [ ] Hardware: CERN-OHL-S-2.0 (strongly reciprocal: modified designs must stay open)
- [ ] Hardware: CERN-OHL-W-2.0 (weakly reciprocal)
- [ ] Hardware: CERN-OHL-P-2.0 (permissive, like MIT)
- [ ] Hardware: keep MIT for everything

- [ ] Data: CC BY 4.0
- [ ] Data: CC0
- [ ] Data: keep MIT

### 6. Funding

**Choose one.** The draft said the work was "supported in part by a Utah NASA Space
Grant Consortium undergraduate fellowship". Your 21 Jun note said there is no NASA
Space Grant funding, so that sentence is gone, and the paper now names no funder.
RSC asks authors to "declare all sources of funding", with grant numbers.

- [ ] No specific funding: add "This work received no specific grant funding."
- [ ] Funded by (funder and grant number in Notes)

**Notes:**

### 7. Safety

**Choose any.** RSC requires hazards to be stated "very clearly". The new Safety
subsection warns readers about combustible fine metal and silicon dust, barium
chloride, breathable dusts, AIBN and pinch points. It does not say what the team did.

- [x] Keep the hazard warnings (current)
- [ ] Add the precautions the team actually used (PPE, fume hood, dust handling, storage; in Notes)

**Notes:**

### 8. Brand names in figures

**Choose one.** DD: "Figures including logos, trademarks or brands names ... should not
be used." The balance model is gone from Fig. 1e, but the photo in Fig. 1b shows a
METTLER TOLEDO logo on the balance in the glove box. Cropping would cut the doser.

- [ ] Blur the logo with a plain (non-AI) blur and say so in the caption
- [ ] Use another photo or video frame without a visible logo (which one, in Notes)
- [ ] Leave it and let the editor decide

**Notes:**

### 9. AI session logs are being deleted

**Choose one.** DD requires "log files that include the inputs and outputs used in
their study". GitHub deletes Actions logs 90 days after each run. Logs for runs up to
about 11 July (all the Copilot sessions that modelled the AI parts) already return
"410 Gone", and a few more expire every day. This session downloaded every log still
available, plus the Claude execution-log artifacts, and stored them as described in
the status note below. The paper now says the April to early-July logs are gone.

- [ ] Publish the archive as a GitHub release now and include it in the Zenodo release
- [ ] Keep it unpublished until the Zenodo release
- [ ] Other (Notes)

**Notes:**

### 10. Files the paper cites that are not on `main`

**Choose any.** A Zenodo archive of `main` would miss them.

- [ ] Merge PR #74 (the 128-entry design log)
- [ ] Merge PR #170 (Fusion 360 STEP files, full parts list, assembly views)
- [ ] Copy the AI-modelled CAD from its design branches into `main`
- [ ] Add the board files of the PCB on the tested rig, and a wiring diagram
- [ ] Make the Onshape document public (it was private on 8 Oct)

### 11. Zenodo DOI and code version

**Choose one.** DD wants DOIs for the current and archived code versions in the Data
availability statement, at the latest at acceptance. The draft says a release "was
archived on Zenodo" at submission, with a placeholder DOI.

- [x] Archive at submission (current text)
- [ ] Archive at acceptance, and say so in the statement

### 12. Comparison with commercial dosers

**Choose one.** The DD hardware editorial (Hein and Schrier, 2024) asks for "at a
minimum, an analysis of capabilities, cost, adaptability, and construction time". The
draft compares cost only, and its commercial price range has no source.

- [ ] Add an SI table (capabilities, dose range, price with sources, build time) and one sentence in the main text
- [ ] Leave as is

### 13. A "hello world" first test

**Choose one.** The same editorial says authors "must provide a minimal 'hello world'
style example experiment".

- [ ] Add one to the SI build guide: run protocol C on salt (expect about 146 mg per
  revolution), then dose 1.000 g (expect within ±50 mg), with the commands to type
- [ ] Leave as is

### 14. Conflicts and free access

**Choose any.** The statement now reads "There are no conflicts to declare."

- [ ] No free credits, early access or other ties with any tool maker (keep as is)
- [ ] We had free credits or early access from (tool and terms in Notes): Edison Scientific / Zoo / CADSmith / GitHub / Anthropic

**Notes:**

### 15. Preprint

**Choose one.** The manuscript PDFs are already public in the repository, which the
cover letter discloses.

- [ ] Post on ChemRxiv at submission
- [ ] No preprint

### 16. Cover letter

The draft is [`paper/cover_letter/cover_letter.tex`](../cover_letter/cover_letter.tex)
([PDF](../cover_letter/cover_letter.pdf)), modelled on your signed letter in
`sgbaird/interp5DOF-paper` (`tensegrity-optimization` has only grant cover pages). It
includes the AI-use declaration that RSC requires in the letter, discloses that the
drafts are public in the repository, and names both co-corresponding authors. The
signatures, Zenodo DOI and preprint status are marked `[TODO]` in red.

**Addressee. Choose one.** Prof. Aspuru-Guzik directs the Acceleration Consortium,
now your second affiliation. The DD guidelines suggest addressing "the relevant
Associate Editor or Executive Editor". An optional sentence asking for a handling
editor without ties to the Consortium is in the `.tex` comments.

- [x] Prof. Alán Aspuru-Guzik, Editor-in-Chief (current)
- [ ] Dr Anna Rulka, Executive Editor
- [ ] An Associate Editor (name in Notes)

**Signed by. Choose any.**

- [x] Sam Charles
- [x] Sterling G. Baird

**Referees.** DD says not to list them in the letter, so they go in the submission
system. The scouted list is in
[`17-suggested-reviewers.md`](../mock_review/inputs/17-suggested-reviewers.md).
Milad Abolhasani and Joshua Schrier are DD Associate Editors, and Keith A. Brown and
Schrier have co-authored with you, so check those for conflicts. Names (4–6) in Notes:

**Notes:**

---

## C. Can wait until revision

### 17. Figure text and resolution

**Choose one.** The smallest printed text in Figs. 3–5 is 4.4–5.4 pt (aim for at
least 6–7 pt), and Figs. 1, 2 and 6 are scaled up so their photos fall below 600 dpi.

- [ ] Redraw the figures at final size now
- [ ] At revision

### 18. Table-of-contents graphic (8 × 4 cm, due at revision)

**Choose one.**

- [ ] The versatility figure from PR #173, cropped to 8 × 4 cm
- [ ] The Fig. 1a render
- [ ] Decide at revision

---

## D. Other

### 19. Tilt wording

**Choose one.** The paper now calls 45° "the steepest tilt used in this work" and adds:
"The servos can turn further, but steeper tilts were not tested." The firmware allows
0–180° at the servo, which the 2:1 gear makes 0–90° at the tube, but nobody has checked
that the hinge clears beyond 45°.

- [x] Keep (current)
- [ ] State the measured mechanical limit (angle in Notes)
- [ ] Drop the sentence about the servos

**Notes:**

### 20. Browser stack on the Pi

**Choose one.** Chromium, Xvfb, xdotool, Selenium and Playwright are installed on the
Pi and use no memory unless a browser is running
([docs](../../docs/pi-browser-automation.md)).

- [x] Keep installed (current)
- [ ] Remove it
