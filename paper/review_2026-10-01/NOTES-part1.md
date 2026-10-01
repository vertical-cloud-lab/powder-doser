# Sam's review notes, video part 1 (2026-10-01)

Notes and suggested changes from Sam Charles's voiceover review of the manuscript,
[part 1](https://youtu.be/GAxXC-pha8Q) (24 min). The video covers the title and abstract through §2.2.1, then the Fig. 1
caption. Each timestamp links to that moment in the video. Line numbers refer to
[`paper/main.tex` @ `ae02647`](https://github.com/vertical-cloud-lab/powder-doser/blob/ae02647/paper/main.tex).
The full corrected transcript is in [TRANSCRIPT-part1.md](TRANSCRIPT-part1.md).

Part 2 has not been recorded yet.

**Status (2026-10-01, evening).** Everything below has been implemented except where noted;
open questions moved to [DECISIONS.md](DECISIONS.md).

| # | Item | Status |
|---|---|---|
| 1 | Tilt range | Settled at the meeting: 45° is the maximum. Nothing in the paper mentions a 90° tilt; firmware docstrings on the battery branches corrected. |
| 2 | No loading slots | Text, Fig. 1c and SI now describe the capped fill opening. Which auger ran the tests: DECISIONS item 1. |
| 3 | Supports | "Most parts need support material." |
| 4 | Fig. 1a out of date | Now the PR #170 render of the current design (real auger, cap, pinion; approximated collar and solenoid). DECISIONS item 7. |
| 5 | Fig. 1c | Replaced by a CAD section through the Fusion auger and cap, with the gear, the flight on the outlet third and the cap. |
| 6 | Auger dimensions | Measured from the Fusion STL (flight 0.5 mm thick, 10.4 mm pitch). DECISIONS item 2. |
| 7 | Will's small-dose data | Abstract and future work now mention the controller work; no new data. DECISIONS item 16. |
| 8 | Design log | Updated on PR #74's branch to 128 entries; count refreshed. |
| 9 | Zoo "late in the project" | Now "we explored Zoo Design Studio". |
| 10 | Carousel | "Later versions will dose several powders." |
| 11 | "Generations" | Now "versions". |
| 12 | CADSmith | "Performed about as well as the coding agent." DECISIONS item 5. |
| — | Wording edits | All applied, including the serial comma throughout (DECISIONS item 10) and removing the phone gloss (item 13). |

## To raise with Sterling: facts to check and decisions

1. **Tilt range** ([14:43](https://youtu.be/GAxXC-pha8Q?t=883), [23:01](https://youtu.be/GAxXC-pha8Q?t=1381)). The paper says every test used 0–45° (L170, L177). Sam thinks the 13-powder runs went all the way to vertical.
   - **Where the 45° comes from:** Will's comment on [PR #124](https://github.com/vertical-cloud-lab/powder-doser/pull/124#issuecomment-4960959001) (13 Jul): *"'vertical' had always set the rig to 45 degrees"*. The analysis therefore halves the battery's recorded tilts of 0/45/90 to 0/22.5/45°.
   - **The conflict:** the battery firmware's own [docstring](https://github.com/vertical-cloud-lab/powder-doser/blob/2522858/hardware/test-module/firmware/powder_battery.py#L48-L52) says tilt 90 = tube vertical.
   - **If the rig did reach vertical:** every tilt number in the text, Fig. 3 and Fig. 4 doubles (22.5° → 45°, 45° → 90°).
   - **Who can settle it:** Will.
2. **There are no loading slots any more** ([22:32](https://youtu.be/GAxXC-pha8Q?t=1352)). The tube is filled through an opening at the top, which has a cap. "Loaded through slots" still appears in L170, the Fig. 1 caption (L177), and Experimental (L336, L348).
   - Confirm which auger the 13-powder tests used: L348 says each run began "by filling the auger tube through its loading slots". If the tested auger had slots, the paper should describe that one and mention the change.
3. **"All structural parts are printed in PLA without supports" is wrong** ([15:45](https://youtu.be/GAxXC-pha8Q?t=945)). Most parts need supports (L172).
4. **Fig. 1a is slightly out of date** ([11:15](https://youtu.be/GAxXC-pha8Q?t=675)). The tap collar is different, the solenoid is different, and the render should show the screw-on cap on the end. Sam will link where the current files are.
5. **Fig. 1c is inaccurate and unclear** ([13:13](https://youtu.be/GAxXC-pha8Q?t=793), [22:03](https://youtu.be/GAxXC-pha8Q?t=1323)):
   - The gear on the outside of the tube is missing, and it matters.
   - The flight no longer runs the full length of the tube.
   - It shows loading slots instead of the capped top opening.
   - Sam liked the layout, but suggested replacing it with a CAD section (cut-away) view.
6. **Auger dimensions** ([12:18](https://youtu.be/GAxXC-pha8Q?t=738)). Sam confirmed the 25 mm outer diameter and 21 mm bore. The flight (single start, 10 mm pitch) still needs checking against the Fusion 360 auger. This is the same open question as item 3 in [OPEN-DECISIONS.md](../OPEN-DECISIONS.md).
7. **Will has newer, more reliable small-dose data** ([03:20](https://youtu.be/GAxXC-pha8Q?t=200)) from his control-optimisation work. The abstract says the 50 and 200 mg doses were "less reliable". Sam asked for one closing future-work line: better control should make small doses more reliable. Decide whether any of Will's data goes into this paper.
8. **The 97-entry design log is stale** ([16:37](https://youtu.be/GAxXC-pha8Q?t=997)). It should be updated (`DESIGN-LOG.md`) and the count refreshed (L183, L362, L384).
9. **Drop "Zoo was used late in the project"?** ([08:07](https://youtu.be/GAxXC-pha8Q?t=487)). Sam would rather give an overview of the tools tried and what each gave. Sterling asked for this emphasis in his June review, so they should agree on it. It appears in L127, L164, L187 and L219.
10. **Don't assume a carousel** ([06:46](https://youtu.be/GAxXC-pha8Q?t=406)). "Later versions can arrange several channels around one cup" (L162) should just say later versions will dose several powders. The Conclusions (L365) and Fig. 6 already describe the roller-chain design instead.
11. **"Generations" sounds odd** ([18:04](https://youtu.be/GAxXC-pha8Q?t=1084)). The project has had mostly the same team since the start. Alternatives Sam floated were "sprints" or "research thrusts" (L183).
12. **CADSmith is introduced, then dropped** ([20:58](https://youtu.be/GAxXC-pha8Q?t=1258)). Sam wants a line saying it was tried and found about the same as Copilot. The draft's tool comparison (L219, after where the video stops) says "CADSmith converged quickly on brackets and plates". Which is right?

## Wording and jargon, in reading order

The main aim is less jargon ([00:46](https://youtu.be/GAxXC-pha8Q?t=46)). The readers are academics, but the paper should be easy for anyone to read.

**Abstract (L127)**
- [01:17](https://youtu.be/GAxXC-pha8Q?t=77): "helical flight" is too technical. Use "screw" or "Archimedes screw". The same point came up for §2.1 at [12:50](https://youtu.be/GAxXC-pha8Q?t=770), where "helix", "spiral" or "screw" would work.
- [01:59](https://youtu.be/GAxXC-pha8Q?t=119): "asking for one part at a time … worked" → "worked better".
- [03:02](https://youtu.be/GAxXC-pha8Q?t=182): give the powder categories (food-safe and alloy-relevant) instead of listing table salt, food thickeners and so on.

**Introduction**
- [04:20](https://youtu.be/GAxXC-pha8Q?t=260), L158: Sam paused on "most SDL demonstrations" (cursor on "SDL"). It doesn't say which demonstrations; "most SDLs" is simpler.
- [04:47](https://youtu.be/GAxXC-pha8Q?t=287), L158: "rely on a person to weigh out *the* powders" → "weigh out powders", to match "work only with liquids".
- [07:36](https://youtu.be/GAxXC-pha8Q?t=456), L164: "The second contribution" → "This study's second contribution", to make it more specific.
- [08:44](https://youtu.be/GAxXC-pha8Q?t=524), L164: "LLMs can now write CAD programs" reads as if they write SolidWorks itself. Use "CAD scripts" or "CAD code".
- [09:47](https://youtu.be/GAxXC-pha8Q?t=587), L164: at the Fusion 360 recreation sentence, mention that those sessions were recorded too, so they are also documented.
- [10:03](https://youtu.be/GAxXC-pha8Q?t=603) and [15:34](https://youtu.be/GAxXC-pha8Q?t=934): it isn't clear what "(Experimental)" means. It's meant as a pointer to the Experimental section; spell it out as "(see Experimental)" or a section number. It appears 5 times: L164, L172, L253, L277, L307.
- [10:37](https://youtu.be/GAxXC-pha8Q?t=637), L164: "and, increasingly, supplied fully dimensioned drawings" → "eventually", or similar.

**§2.1 The dosing module**
- [14:16](https://youtu.be/GAxXC-pha8Q?t=856): "the kind that makes a phone vibrate" is probably unnecessary, but fine to keep.

**Fig. 1 caption (L177)**
- (a) [21:22](https://youtu.be/GAxXC-pha8Q?t=1282): use a view angle that shows the tapping and vibration hardware, or add arrows.
- (b) [21:46](https://youtu.be/GAxXC-pha8Q?t=1306): say it's inside a glove box, which Sam thinks is significant.
- (d) [22:55](https://youtu.be/GAxXC-pha8Q?t=1375): label 90° "(vertical)" to match "0° (horizontal park)", for consistency. Also check the 0–45° claim (item 1).
- (e) [23:28](https://youtu.be/GAxXC-pha8Q?t=1408): say that the three-phase controller (bulk → fine → tap) drives the actuators until the two masses agree.
- [23:18](https://youtu.be/GAxXC-pha8Q?t=1398): Oxford comma in "reviewed, printed, and tested". The draft omits serial commas throughout, so if it's adopted, it should be applied everywhere.

**§2.2 How the parts were designed**
- [17:36](https://youtu.be/GAxXC-pha8Q?t=1056), L183: "each was modelled, reviewed and printed on its own" → say who did what: modelled by AI, then reviewed and printed by the engineers.
- [17:55](https://youtu.be/GAxXC-pha8Q?t=1075), L183: the four outlet geometries came early, between the first and second generations, not after the fourth.
- [18:57](https://youtu.be/GAxXC-pha8Q?t=1137), L185: start the "specifications grew more detailed" story at the system level. The first requests described what the whole system had to do; only later what each part had to do.
- [19:49](https://youtu.be/GAxXC-pha8Q?t=1189), L187: "Automated checks that run on every change (continuous integration) then rendered views of the part…" reads as a fragment with no subject. "Rendered" parses as an adjective, so the sentence needs rewriting.

## Things Sam liked (keep)

- The abstract, mostly ([02:50](https://youtu.be/GAxXC-pha8Q?t=170)).
- The Fig. 1a,b pairing ([11:11](https://youtu.be/GAxXC-pha8Q?t=671)).
- "…including where the current design fails" ([07:31](https://youtu.be/GAxXC-pha8Q?t=451)).
- "like an Archimedes screw" ([13:04](https://youtu.be/GAxXC-pha8Q?t=784)).
- Fig. 1e, the closed-loop diagram ([15:15](https://youtu.be/GAxXC-pha8Q?t=915)).
- The cost paragraph ([16:19](https://youtu.be/GAxXC-pha8Q?t=979)).
- "Every design decision stayed with the team" ([18:55](https://youtu.be/GAxXC-pha8Q?t=1135)).
- "Every prompt … is preserved" ([20:55](https://youtu.be/GAxXC-pha8Q?t=1255)).
