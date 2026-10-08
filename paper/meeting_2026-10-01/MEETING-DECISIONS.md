# Decisions from the 1 October meeting (Sam and Sterling)

**How to use this file.** Open it in the GitHub editor
([edit link](https://github.com/vertical-cloud-lab/powder-doser/edit/copilot/draft-base-manuscript/paper/meeting_2026-10-01/MEETING-DECISIONS.md)),
change `[ ]` to `[x]` for your answers, type anything extra after **Notes:**, and
commit straight to the branch. Then ask `@claude` on PR #97 to implement it.

- **Choose one** means pick a single box; **Choose any** means tick as many as apply.
- A box that is already ticked shows what the draft does **now** (as of commit `eb08113`).
  Leave it ticked to keep that, or move the tick to change it.
- This file holds only questions raised by the meeting. The main checklist is
  [`review_2026-10-01/DECISIONS.md`](../review_2026-10-01/DECISIONS.md), written by the
  parallel session; it replaces `OPEN-DECISIONS.md`. Where the two overlap, the item
  there points to the question here, so each question is answered once. Section F lists
  meeting evidence for other questions in that file.
- What was said, and what has already been done about it, is in
  [MEETING-NOTES.md](MEETING-NOTES.md). The corrected transcript is
  [TRANSCRIPT-corrected.md](TRANSCRIPT-corrected.md).

Questions 1, 3 and 4 matter most.

---

## A. What the tested doser was made of

### 1. Which printed parts were on the doser for the August and September tests?

**Choose one.** (DECISIONS.md item 3 points here.) During the meeting Sam
listed the lab's Fusion 360 files for the assembly
([#170](https://github.com/vertical-cloud-lab/powder-doser/pull/170#issuecomment-5939517081)):
baseplate, brackets, mounting plate, servo pinion, stepper pinion, tap collar, auger
and auger cap. All eight come from the lab's Fusion 360 account; the Onshape files
mentioned in the meeting are the multi-doser's. They are the same eight parts that were
recreated on video for [#120](https://github.com/vertical-cloud-lab/powder-doser/issues/120),
which began on 2 July, a month before the first test round. Sam also said that the one
part not in Fusion 360, the tap-collar base, is "still AI's version". Together these
suggest the tested doser was printed almost entirely from the team's Fusion 360 parts.

The draft does not say this, and it now disagrees with itself:
- The abstract, the introduction and the Experimental section say the tested doser uses
  *some* recreated parts, "including the auger and its drive gear".
- The new SI parts table says every printed part of the tested doser was modelled in
  Fusion 360, and it leaves out the tap-collar base.
- The Fig. 1a caption says the plates and brackets *in the render* are the earlier
  AI-modelled parts.

- [ ] All eight Fusion 360 parts, plus the AI-modelled tap-collar base
- [x] Some of them, including the auger, cap and stepper pinion; the rest were AI-modelled prints (current text)
- [ ] It changed during testing (which parts, and from when, in Notes)
- [ ] Not sure; someone will check the rig and the test photos

**Notes:**

### 2. How far did the Fusion 360 recreations depart from the AI-modelled parts?

**Choose one.** #120 set out to alter the parts "slightly ... to match original design
intent, not the ai-generated parts". Known changes:
- The gear pair went from 16:48 to 20:44 teeth.
- The tube is filled through a capped end instead of loading slots.
- The flight covers only the third of the tube nearest the outlet. By the measurement in
  DECISIONS.md item 2, it is also 0.5 mm thick rather than 2 mm.
- The tap collar holds a different solenoid.

The draft says the team "recreated its parts in Fusion 360 and changed some of them".

- [x] Same parts, same layout and same connections between them, with changes like those above (current)
- [ ] The AI parts were a starting point; most were redesigned (which ones, in Notes)
- [ ] Other (Notes)

**Notes:**

### 3. How should the abstract describe the tested doser?

**Choose one.** This is the wording; where it is said is DECISIONS.md item 19, and the
title is item 18. It follows from questions 1 and 2.

- [x] "The team later redrew the parts in conventional CAD, and the tested doser uses some of these, including the auger and its drive gear." (current; no longer accurate if the answer to question 1 is "all eight")
- [ ] "The team later redrew the parts in conventional CAD, and the tested doser was printed from these redrawn parts, apart from one AI-modelled part."
- [ ] Present the AI-designed doser as the working prototype and the tested doser as its redrawn successor, with one sentence each in the abstract, the introduction and the Experimental section
- [ ] Other (Notes)

**Notes:**

### 4. The tap-collar base

The tap collar sits on this plate. Sam said it is the one AI-modelled part still in
use, and that it is "probably somewhere in a branch". The likeliest file is
`design/cad/tap-collar/mount_plate.step` on branch
[`copilot/design-tap-collar`](https://github.com/vertical-cloud-lab/powder-doser/tree/copilot/design-tap-collar/design/cad/tap-collar).
It is the plate with a small bump that stops the collar from turning with the auger,
modelled in Python by the Copilot coding agent (last changed 10 June). The #170
session is looking for it too.

**Is that the part on the rig? Choose one.**

- [x] Yes
- [ ] No; the part on the rig came from Zoo Design Studio
- [ ] No; it's another file (link in Notes)

**Where should the paper say so? Choose any.**

- [x] Fabrication (Experimental section)
- [x] The SI parts table, with a link to the file
- [ ] The abstract or the introduction (only if the answer to question 1 is "all eight")
- [ ] Nowhere

**Notes:**

---

## B. Fig. 1

### 5. Fig. 1a: who makes the refreshed render, and should it show who modelled what?

DECISIONS.md item 7 asks whether to keep the #170 render or use a photograph; these two
questions follow on from it. In the meeting Sam said panel (a) was out of date: the
stepper was a stand-in, there was no solenoid, and the tap collar had changed. "I love
the idea of it, but it should be updated." Two ways to update it were discussed: a new
render, which could be a job for Brandon and Ethan in the lab, or a good photograph. The
#170 session is now building a full assembly in Onshape from all eight Fusion parts,
with simple models of the stepper, solenoid and servos.

**Who makes the refreshed render? Choose one.**

- [x] The #170 session, from its Onshape assembly
- [ ] Brandon and Ethan, from the same files
- [ ] Nobody; a photograph replaces it (who takes it, in Notes)

**Colour the parts by who modelled them (AI tools or the team)? Choose one.** Fig. 1
would then show the split between AI and human work that the paper describes.

- [ ] Yes: two colours and a legend
- [x] No (current)

**Notes:**

### 6. An assembly view with the bill of materials

**Choose any.** On #170 you noted that we should later ask for "an assembly GIF with
the full bill of materials".

- [x] An exploded view with numbered bill-of-materials labels, in the SI
- [x] An animated assembly GIF in the repository README, linked from the SI
- [ ] Neither, for this paper

**Notes:**

---

## C. Build instructions and design files

### 7. Build instructions

**Choose any.** (DECISIONS.md item 22 points here.) The
meeting asked "where are the reproducible build instructions for this thing?" A reader,
or an agent, should be able to find the file to print for each part and the order to
assemble them. The SI now has a build outline and a table of the printed parts with
their Fusion 360 links.

- [x] The SI outline and parts table (current)
- [ ] A step-by-step guide with photos in the repository (`hardware/BUILD.md`), linked from the SI
- [x] Turn a new assembly video into illustrated steps
- [x] Include the auger filling stand in the guide

**Notes:**

### 8. Where the design files are published

**Choose any.** (DECISIONS.md item 22 points here for #170 and the Onshape parts; it
keeps the design-log merge and a DOI-backed release.) During the meeting Sam turned on
public sharing, with downloads, for the eight Fusion 360 parts. The #170 session then
exported them as STEP files to `cad/full-assembly/components/fusion-step/`.

- [ ] Merge #170 before submission, so the STEP and STL files the Data availability statement promises are on `main`
- [x] STEP and STL files in the repository (current text; true once #170 is merged)
- [x] Public Fusion 360 links in the SI parts table (current)
- [x] public Onshape document of the assembly (Vertical Cloud Lab classroom), from #170

**Notes:**

### 9. Other parts Sam linked

**Choose any.** Sam also linked the auger filling stand and two smaller augers, of
3.32 mL and 9.18 mL
([#170](https://github.com/vertical-cloud-lab/powder-doser/pull/170#issuecomment-5939645382)).
Smaller augers were asked for in #117 for the University of Utah glovebox trials. The
older cap designs are being kept out, so that nobody, human or agent, picks up a
superseded version.

- [x] List the filling stand in the SI parts table
- [x] Mention the smaller augers in one sentence (the reservoir can be sized to the sample)
- [ ] Neither

**Notes:**

---

## D. Text

### 10. "Atomizer"

**Choose one.** (DECISIONS.md item 15 points here.) At 08:14 the transcript
reads: "And then on top of that adding the fact that we've actually used it with ...
atomizer ... I think that's good ... one of the updates for recent [weeks]." The
manuscript repository doesn't mention an atomizer, but the project's proposals do: the
alloy pipeline feeds dosed powder to an ultrasonic atomizer
([`proposals/byu-nasa-space-grant-2026/proposal.tex`](../../proposals/byu-nasa-space-grant-2026/proposal.tex)).
So this may mean the doser has now been used ahead of the atomizer. It may also be a
transcription error.

- [x] Powder from the doser has gone into the ultrasonic atomizer; add one sentence (details in Notes)
- [ ] It meant the University of Utah glovebox use (the glovebox line in DECISIONS.md item 24)
- [ ] Something else (Notes)
- [x] Leave it out, for example because it was a transcription error (current)
- [x] Also mention the use of it inside the glove box

**Notes:**

### 11. Will's controller work

**Choose one.** (DECISIONS.md item 16 points here.) From the meeting: "now it's just a
control problem, so we're working on that." Nobody asked for new data, and Sterling has
said all the data for this paper are in. The abstract now ends "ongoing controller work
targets this", and the Conclusions say that better control should make small doses more
reliable.

- [x] Mention it only, with no data (current)
- [ ] Also point to the work in the repository (#161, #164, #166)
- [ ] Add a short SI section with Will's newer small-dose results (which runs, in Notes)

**Notes:**

### 12. How the project started, and who did it

**Choose any.** (DECISIONS.md item 14 points here.) The meeting objected to
"generations" because it implied hand-offs between teams; the same team did the whole
project, in less than a year. The draft now says "four versions in its first six
weeks". The meeting also noted that the first version came out of a one- or two-day
hackathon with two other people. DECISIONS.md item 21 asks about acknowledging Devora
Najjar, who committed to the repository on its first day (23 April 2026).

- [x] Say the project began at a hackathon (event and date in Notes)
- [x] Acknowledge the two hackathon collaborators (names in Notes)
- [ ] Add "by the same team" to the design-history sentence
- [ ] None of these

**Notes:**

### 13. AI tools change quickly

**Choose any.** Two points from the meeting:
- An assistant had just gained agent features ("they put an agent in an agent"). The
  transcript doesn't say which tool. Someone noted the paper's tool comparison would be
  "out of date in two months or less".
- Sterling showed a robot-arm wrist-camera mount, designed in a few prompts by an agent
  working in Onshape. #170 is building the doser assembly through the Onshape API in
  the same way.

- [x] Give the months each tool was used, and say the comparison is a snapshot
- [ ] Add one outlook sentence: agents can now drive full CAD packages through their APIs, not only write CAD code
- [ ] Neither
- [ ] mention that we're noticing that the use of onshape with the onshape API is one of the most successful, but that improvements are being seen throughout all handling of these kinds of tasks. Can also cite text-to-cad as one of the promising newer examples

**Which tool gained agent features?** (Notes)

**Notes:**

---

## E. Housekeeping

### 14. The raw transcript

**Choose one.** `Powder Doser Manuscript Overview.txt` at the top of the repository is the
raw Tactiq export. It includes a phone call and some personal conversation. The
corrected transcript in this folder leaves those out. Deleting the raw file would not
remove it from the git history.

- [ ] Leave it where it is (current)
- [ ] Move it into this folder
- [x] Delete it, keeping only the corrected transcript

**Notes:**

### 15. When the video arrives

**Choose any.**

- [x] Re-transcribe it with Whisper large, then correct the transcript and its speaker labels
- [x] Report anything that changes an answer here or in DECISIONS.md
- [ ] Also take screenshots at each decision point, as for the 1 September meeting

**Notes:**

### 16. Anything else

**Notes:**

---

## F. Meeting evidence for other questions in DECISIONS.md (no boxes here)

- **Item 1 (which auger ran the tests).** The slots were removed "months ago" (04:40),
  and the new auger "has the reservoir for two-thirds" (09:03). Both fit the threaded
  Fusion auger being used for every test.
- **Item 4 (the tap collar on the rig).** Sam's #170 list gives the tap collar from the
  lab's Fusion 360 account, which is Will's #120 recreation. That points to the Fusion
  collar, though not to when it went on the rig.
- **Item 8 (where the glove box was).** #117 records a session on 24 July in the
  Lessard Lab glovebox at the University of Utah, with Claude as the control agent. If
  the Fig. 1b photo is from that session, the answer is the University of Utah.
- **Item 21 (acknowledgements).** Devora Najjar's first commit was on the repository's
  first day, which fits the hackathon (question 12 here).
