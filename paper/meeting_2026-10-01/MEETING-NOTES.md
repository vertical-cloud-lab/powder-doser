# 1 October 2026 meeting: Sam and Sterling on the manuscript

The meeting ran for 55 minutes, 13:17–14:12 MDT (19:17–20:12 UTC). These notes draw on
two sources: the raw Tactiq transcript
([`Powder Doser Manuscript Overview.txt`](../../Powder%20Doser%20Manuscript%20Overview.txt))
and the GitHub activity during the meeting. The corrected transcript is
[TRANSCRIPT-corrected.md](TRANSCRIPT-corrected.md). The questions for Sterling and Sam
are in [MEETING-DECISIONS.md](MEETING-DECISIONS.md).

Sam brought the points from his part-1 review video
([NOTES-part1.md](../review_2026-10-01/NOTES-part1.md)). The first 13 minutes covered
the manuscript. Most of the rest went to collecting the current CAD files, so that Claude
can rebuild the assembly ([#170](https://github.com/vertical-cloud-lab/powder-doser/pull/170)).

Meeting times below are offsets into the transcript. They line up with GitHub to within
about a minute (see the timeline).

## Timeline: the meeting against GitHub

| Meeting time | UTC | What happened |
|---|---|---|
| 02:30 | 19:19 | Sterling asks Claude on #97 to check the livestreams for the tilt range ("max 2 sentences") |
| 14:02 | 19:31 | Sterling asks Claude on #165 for a new assembly and render: "Some files are still on Fusion, some on OnShape" |
| 23:12 | 19:40 | Sam commits the Onshape keys to `claude.yml` on `main` ([`52ec03a`](https://github.com/vertical-cloud-lab/powder-doser/commit/52ec03a)) |
| about 37:00 | 19:54 | Claude replies on #97: the battery's "tilt 90" was a tube angle of about 45° |
| 45:36 | 20:02 | Sterling opens PR #170 from the #165 branch. Sam posts the Fusion 360 links and the assembly prompt 21 s later |
| 53:59 | 20:10 | Sam posts links for the filling stand and the two smaller augers on #170 |
| after the meeting | 20:24, 20:31 | Sterling on #97: "you're sure it's not 60 degrees?", then "it seems to be 45 degrees as max", "Use 'versions'", "can just be that we explored zoo" |

## Sam's part-1 points: what the meeting said and where they stand

Status is as of commit `9698a67`. Almost everything was implemented by the parallel
session (job [36922265580](https://github.com/vertical-cloud-lab/powder-doser/actions/runs/36922265580)).

| # | Point | In the meeting | Status |
|---|---|---|---|
| 1 | Tilt range | 00:48. Sam thinks the runs went to vertical; Sterling asks Claude to check | **Settled after the meeting: 45° maximum.** Done everywhere |
| 2 | Loading slots | 04:40: "you've gotten rid of that like months ago" | Done: the tube is filled through its capped end |
| 3 | Supports | 04:40: "we're using supports in the printing" | Done: "most of them with support material" |
| 4 | Fig. 1a out of date | 12:01–12:55: stand-in stepper, no solenoid, old tap collar. "It should be updated" | Replaced with the #170 render. Open: [question 5](MEETING-DECISIONS.md#5-fig-1a-who-makes-the-refreshed-render-and-should-it-show-who-modelled-what) |
| 5 | Fig. 1c | 09:03: the new auger "has the reservoir for two-thirds", and the screw does not run throughout | Done: a CAD section of the Fusion auger, with the flight on the third nearest the outlet |
| 6 | Auger dimensions | 09:03: "make sure that the data in here is still accurate" | Done from the Fusion file: 25 mm OD, 21 mm bore, 250 mm long, 10.4 mm pitch, 8 mm core. The parallel session asks you to confirm it is the printed file |
| 7 | Smaller doses and controls | 05:14 and 08:14: "now it's just a control problem, so we're working on that" | Done in the abstract and Conclusions. Open: [DECISIONS.md](../review_2026-10-01/DECISIONS.md) item 16 |
| 8 | Design log | 05:30: "it just needs to be refreshed" | Done: 97 to 128 entries |
| 9 | "Zoo, late in the project" | 05:30: "I think that's unnecessary" | Done: "we explored Zoo" |
| 10 | Carousel | 05:30: "not necessarily the way we're gonna do it" | Done: "later versions will dose several powders" |
| 11 | "Generations" | 05:30–06:46: "it's been us the whole time ... less than a year of work" | Done: "versions". Open: the hackathon origin, [question 11](MEETING-DECISIONS.md#11-how-the-project-started-and-who-did-it) |
| 12 | CADSmith | Not discussed | Done by the parallel session: "performed about as well as the coding agent" |

## New points from the meeting

1. **The tested doser may be almost all human-modelled parts**
   ([questions 1–4](MEETING-DECISIONS.md#a-what-the-tested-doser-was-made-of)).
   - Sam's list of assembly files covers the same eight parts that #120 recreated in
     Fusion 360.
   - Sam said only the tap-collar base is "still AI's version".
   - The draft says the tested doser uses only "some" recreated parts. The new SI
     parts table, meanwhile, says all of them are Fusion 360 parts, and it omits the
     tap-collar base.
   - This is the most consequential open point for the paper's headline claim.
2. **Reproducible build instructions** (09:03–10:09;
   [question 7](MEETING-DECISIONS.md#7-build-instructions)). Point readers, and Claude,
   to "the file that you print" for each part, with assembly steps. One idea was to
   record a video and have Claude write it up.
3. **"Atomizer"** (08:14; [question 10](MEETING-DECISIONS.md#10-atomizer)). It is not
   clear from the transcript.
4. **AI tools change quickly** (35:04–36:40, 46:57–49:52;
   [question 12](MEETING-DECISIONS.md#12-ai-tools-change-quickly)). The worry was that
   the tool comparison will soon be dated. Sterling showed agent-driven design in
   Onshape.

## Actions agreed or done during the meeting

| Who | What | Status |
|---|---|---|
| Sam | Create an Onshape developer API key and add it as repository secrets `ONSHAPE_ACCESS_KEY` and `ONSHAPE_SECRET_KEY`, passed to Claude in `claude.yml` on `main` | Done (`52ec03a`, 19:40 UTC) |
| Sam | Public Fusion 360 share links, with downloads on, for the eight assembly parts | Done (#170, 20:02 UTC) |
| Sam | Links for the auger filling stand and the 3.32 mL and 9.18 mL augers | Done (#170, 20:10 UTC) |
| Sam | Find the AI-modelled tap-collar base | Open. The likeliest file is in [question 4](MEETING-DECISIONS.md#4-the-tap-collar-base) |
| Sterling | Open PR #170 and give Claude the assembly task | Done (20:02 UTC). The session has downloaded the eight Fusion files through the Pi as STEP. The simplified stepper, solenoid and servo models, the Onshape upload and the assembly are in progress |
| Brandon, Ethan | An updated render or photograph for Fig. 1a | Open ([question 5](MEETING-DECISIONS.md#5-fig-1a-who-makes-the-refreshed-render-and-should-it-show-who-modelled-what)) |
| Not assigned | An assembly GIF with the full bill of materials (Sterling's note on #170) | Open ([question 6](MEETING-DECISIONS.md#6-an-assembly-view-with-the-bill-of-materials)) |

## Tooling notes from the meeting (not for the paper)

- **Edit `claude.yml` on `main`.** Claude reads `.github/workflows/claude.yml` only from
  `main`, so new secrets must be added to it there. It is also where `@claude+opus` and
  similar triggers are parsed. Repository instructions for Claude go in `CLAUDE.md`;
  #155 asks for Onshape instructions there.
- **Onshape quota.** The BYU Vertical Cloud Lab key has a quota of 2,500 calls, so each
  lab member should use their own developer key. When one runs out, switch to another
  person's. The key added today is Sam's.
- **Fusion 360 files.** Fusion 360 has no API that helps here, but Claude can download
  from public share links. Autodesk often blocks those downloads from the GitHub
  runner, so they go through the Raspberry Pi.
- **Where the CAD lives.** The current CAD is split between the lab's Fusion 360 account
  and Onshape. The multi-doser work has moved to Onshape. Old versions, such as the
  earlier cap designs, stay in Fusion 360, and are deliberately not linked so that
  Claude doesn't pick them up.

## What to check in the video

The raw transcript's speaker labels are unreliable. Tactiq credits 00:00–10:25 to
Sterling and everything from 11:17 to Sam, but both spoke throughout. The labels in the
corrected transcript are inferred from context, and those marked "?" are guesses.

When the video arrives, check these points:
- 04:40 and 06:10: who said "you've gotten rid of that months ago", and who mentioned
  the hackathon and the "two people".
- 08:14: the word transcribed as "atomizer".
- 09:03: "the reservoir for two-thirds".
- 12:55: the names of the lab helpers. The transcript has Brandon and Ethan; the
  auto-summary adds Anna.
- 28:35: the isolated "90°".
- 35:04–35:50: which tool gained agent features.
- 53:52–54:36: the Ansys workflow, and who ran it.

The auto-summary at the top of the raw file is also unreliable:
- It cites timestamps up to 1:14:30 for a 55-minute meeting.
- It says to "confirm that [the] tests went to 90°", which is the opposite of what was
  settled.
- It assigns action items that were not discussed, such as Sterling providing wording
  for the abstract.
