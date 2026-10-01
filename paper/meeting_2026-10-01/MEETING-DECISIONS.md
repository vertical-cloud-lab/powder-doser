# Decisions from the 1 October meeting (Sam and Sterling)

**How to use this file.** Open it in the GitHub editor
([edit link](https://github.com/vertical-cloud-lab/powder-doser/edit/copilot/draft-base-manuscript/paper/meeting_2026-10-01/MEETING-DECISIONS.md)),
change `[ ]` to `[x]` for your answers, type anything extra after **Notes:**, and
commit straight to the branch. Then ask `@claude` on PR #97 to implement it.

- **Choose one** means pick a single box; **Choose any** means tick as many as apply.
- A box that is already ticked shows what the draft does **now** (as of commit `14debac`).
  Leave it ticked to keep that, or move the tick to change it.
- Only questions raised by this meeting are here. This morning's checklist
  ([`OPEN-DECISIONS.md`](../OPEN-DECISIONS.md)) and the one the parallel session is
  writing (`paper/review_2026-10-01/DECISIONS.md`) cover the rest. Where a question
  here replaces one there, it says so.
- What was said, and what has already been done about it, is in
  [MEETING-NOTES.md](MEETING-NOTES.md). The corrected transcript is
  [TRANSCRIPT-corrected.md](TRANSCRIPT-corrected.md).

Questions 1, 3 and 4 matter most.

---

## A. What the tested doser was made of

### 1. Which printed parts were on the doser for the August and September tests?

**Choose one.** During the meeting Sam listed the lab's Fusion 360 files for the
assembly ([#170](https://github.com/vertical-cloud-lab/powder-doser/pull/170#issuecomment-5939517081)):
baseplate, brackets, mounting plate, servo pinion, stepper pinion, tap collar, auger
and auger cap. These are the same eight parts that were recreated on video for
[#120](https://github.com/vertical-cloud-lab/powder-doser/issues/120), which began on
2 July, a month before the first test round. Sam also said that the one part not in
Fusion 360, the tap-collar base, is "still AI's version". Together these suggest the
tested doser was printed almost entirely from the team's Fusion 360 parts.

The draft does not say this, and it now disagrees with itself:
- The abstract, the introduction and the Experimental section say the tested doser uses
  *some* recreated parts, "including the auger and its drive gear".
- The new SI parts table says every printed part of the tested doser was modelled in
  Fusion 360, and it leaves out the tap-collar base.
- The Fig. 1a caption says the plates and brackets *in the render* are the earlier
  AI-modelled parts.

This replaces item 1 of `OPEN-DECISIONS.md`.

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
- The flight covers only the third of the tube nearest the outlet.
- The tap collar holds a different solenoid.

The draft says the team "recreated its parts in Fusion 360 and changed some of them".

- [x] Same parts, same layout and same connections between them, with changes like those above (current)
- [ ] The AI parts were a starting point; most were redesigned (which ones, in Notes)
- [ ] Other (Notes)

**Notes:**

### 3. How should the abstract describe the tested doser?

**Choose one.** This follows from questions 1 and 2. It sits alongside
`OPEN-DECISIONS.md` item 2 (how prominently to say it) and item 5 (the title).

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

- [ ] Yes
- [ ] No; the part on the rig came from Zoo Design Studio
- [ ] No; it's another file (link in Notes)

**Where should the paper say so? Choose any.**

- [ ] Fabrication (Experimental section)
- [ ] The SI parts table, with a link to the file
- [ ] The abstract or the introduction (only if the answer to question 1 is "all eight")
- [ ] Nowhere

**Notes:**

---

## B. Fig. 1

### 5. Fig. 1a, the CAD view of the doser

**Choose one.** In the meeting Sam said panel (a) was out of date: the stepper was a
stand-in, there was no solenoid, and the tap collar had changed. Two fixes were
discussed. One was a new render, which could be a job for Brandon and Ethan in the lab.
The other was a good photograph.

Since then, the parallel session has replaced panel (a) with the #170 render. That
render shows:
- the Fusion auger, cap and pinion;
- a tap collar and solenoid modelled from a photo;
- the June AI-modelled plates and brackets.

The #170 session is now building a full assembly in Onshape from all eight Fusion
parts, with simple models of the stepper, solenoid and servos.

- [x] Keep the #170 render (current)
- [ ] Re-render once the #170 Onshape assembly is complete
- [ ] Brandon and Ethan make a new render
- [ ] Replace the render with a photograph

**Colour the parts by who modelled them (AI tools or the team)? Choose one.** Fig. 1
would then show the split between AI and human work that the paper describes.

- [ ] Yes: two colours and a legend
- [x] No (current)

**Notes:**

### 6. An assembly view with the bill of materials

**Choose any.** On #170 you noted that we should later ask for "an assembly GIF with
the full bill of materials".

- [ ] An exploded view with numbered bill-of-materials labels, in the SI
- [ ] An animated assembly GIF in the repository README, linked from the SI
- [ ] Neither, for this paper

**Notes:**

---

## C. Build instructions and design files

### 7. Build instructions

**Choose any.** The meeting asked "where are the reproducible build instructions for
this thing?" A reader, or an agent, should be able to find the file to print for each
part and the order to assemble them. The SI now has a build outline and a table of the
printed parts with their Fusion 360 links.

- [x] The SI outline and parts table (current)
- [ ] A step-by-step guide with photos in the repository (`hardware/BUILD.md`), linked from the SI
- [ ] Record an assembly video, and have Claude turn it into illustrated steps
- [ ] Include the auger filling stand in the guide

**Notes:**

### 8. Where the design files live

**Choose any.** This updates `OPEN-DECISIONS.md` item 4. During the meeting Sam turned
on public sharing, with downloads, for the eight Fusion 360 parts. The #170 session
then exported them as STEP files to `cad/full-assembly/components/fusion-step/`. The
Data availability statement now promises STEP and STL files in the repository, once
#170 is merged.

- [x] STEP and STL files in the repository, once #170 is merged (current)
- [x] Public Fusion 360 links in the SI parts table (current)
- [ ] A public Onshape document of the assembly (Vertical Cloud Lab classroom), from #170
- [ ] A tagged release archived on Zenodo with a DOI, at submission

**Notes:**

### 9. Other parts Sam linked

**Choose any.** Sam also linked the auger filling stand and two smaller augers, of
3.32 mL and 9.18 mL
([#170](https://github.com/vertical-cloud-lab/powder-doser/pull/170#issuecomment-5939645382)).
Smaller augers were asked for in #117 for the University of Utah glovebox trials. The
older cap designs are being kept out, so that nobody, human or agent, picks up a
superseded version.

- [ ] List the filling stand in the SI parts table
- [ ] Mention the smaller augers in one sentence (the reservoir can be sized to the sample)
- [ ] Neither

**Notes:**

---

## D. Text

### 10. "Atomizer"

**Choose one.** At 08:14 the transcript reads: "And then on top of that adding the fact
that we've actually used it with ... atomizer ... I think that's good ... one of the
updates for recent [weeks]." The alloy pipeline in the proposals feeds dosed powder to
an ultrasonic atomizer, so this may mean the doser has now been used ahead of it. It
may also be a transcription error.

- [ ] Powder from the doser has gone into the ultrasonic atomizer; add one sentence (details in Notes)
- [ ] It meant the University of Utah glovebox use (`OPEN-DECISIONS.md` item 13)
- [ ] Something else (Notes)
- [ ] A transcription error; ignore it

**Notes:**

### 11. Will's controller work

**Choose one.** From the meeting: "now it's just a control problem, so we're working on
that." The abstract now ends "ongoing controller work targets this". The Conclusions say
that better control should make small doses more reliable. Sam's part-1 notes left
open whether any of Will's newer data should go in.

- [x] Mention it only, with no data (current)
- [ ] Also point to the work in the repository (#161, #164, #166)
- [ ] Add preliminary small-dose results from Will's runs (which runs, in Notes)

**Notes:**

### 12. How the project started, and who did it

**Choose any.** The meeting objected to "generations" because it implied hand-offs
between teams; the same team did the whole project, in less than a year. The draft now
says "four versions in its first six weeks". The meeting also noted that the first
version came out of a one- or two-day hackathon with two other people.
`OPEN-DECISIONS.md` item 7 already asks about acknowledging Devora Najjar, who committed
to the repository on its first day (23 April 2026).

- [ ] Say the project began at a hackathon (event and date in Notes)
- [ ] Acknowledge the two hackathon collaborators (names in Notes)
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

- [ ] Give the months each tool was used, and say the comparison is a snapshot
- [ ] Add one outlook sentence: agents can now drive full CAD packages through their APIs, not only write CAD code
- [ ] Neither

**Which tool gained agent features?** (Notes)

**Notes:**

---

## E. Housekeeping

### 14. The raw transcript

**Choose one.** `Powder Doser Manuscript Overview.txt` at the top of the repository is the
raw Tactiq export. It includes a phone call and some personal conversation. The
corrected transcript in this folder leaves those out. Deleting the raw file would not
remove it from the git history.

- [x] Leave it where it is (current)
- [ ] Move it into this folder
- [ ] Delete it, keeping only the corrected transcript

**Notes:**

### 15. When the video arrives

**Choose any.**

- [x] Re-transcribe it with Whisper large, then correct the transcript and its speaker labels
- [x] Report anything that changes an answer above
- [ ] Also take screenshots at each decision point, as for the 1 September meeting

**Notes:**

### 16. Anything else

**Notes:**
