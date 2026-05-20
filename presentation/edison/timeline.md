# Time-sorted instruction/comment log

Compiled from issue comments, PR comments, and PR session
follow-ups across the powder-excavator repo. Used as the
source for the wrap-up deck's narrative re-alignment.

| When (UTC) | Source | Who | Substance |
|---|---|---|---|
| 2026-04-23 20:27 | Issue #1 (open) | sgbaird | Initial sketch + idea: "pure mechanical approach connected to a gantry, push up against a wall to drop powder." |
| 2026-04-23 20:37 | PR #2 comment | sgbaird | "Send the idea to Edison for feedback (high effort literature search)" — also pull every instance of powder handling, intro-of-Digital-Discovery framing. |
| 2026-04-23 20:37 | PR #2 comment | sgbaird | `cc @devoranajjar` — explicitly looped Devora into the project at the start. |
| 2026-04-23 21:27 | PR #2 comment | sgbaird | "Try accessing that website again. Send that Edison query if you haven't." |
| 2026-04-23 21:29 | Issue #1 comment | **devoranajjar** | "Idea: attach magnets to the bucket that can be used to tip/reset the bucket?" — first non-Sterling design input. |
| 2026-04-23 22:19 | PR #2 comment | sgbaird | New Edison query: state-of-the-art generative CAD / systems design (Rhino, Grasshopper) + automatic-feedback / digital-twin angle. |
| 2026-04-23 22:27 | Issue #3 (open) | **devoranajjar** | Authored the **technical-viability writeup** — dose control (dip-depth vs closed-loop gravimetric), powder adhesion (PTFE + ERM motor), pivot repeatability, 3D-print at small scale. This is the source of the "surface forces, not gravity" quote in the deck. |
| 2026-04-23 22:34 | Issue #3 comment | devoranajjar | Expanded Challenge 1 (dose control) into Options A/B with concrete numbers. |
| 2026-04-23 22:42 | Issue #3 comment | devoranajjar | Resolved most open questions: 0.05 mg load cell on hand, gantry interface confirmed, target dose error tolerance. |
| 2026-04-23 23:04 | Issue #3 comment | devoranajjar | Software integration plan: one Python script driving GRBL gantry + USB load cell in a closed-loop dispense cycle. |
| 2026-04-23 23:33 | Issue #4 (open) | sgbaird | "Consider the bimodal compliant mechanism feature again as a secondary idea" → seeds PR #5. |
| 2026-04-24 00:03 | PR #2 (Copilot reply) | Copilot | First CadQuery commit — included the line "chosen over Rhino/Grasshopper, Fusion, nTop, Onshape because it's pure-Python and pip-installable." |
| 2026-04-24 00:27 | Issue #6 (open) | sgbaird | **Pushback** on the pure-Python dismissal: "You have a full dev environment. Try to install each of these." This is the hinge moment quoted in the deck. |
| 2026-04-24 00:30 | PR #7 comment | sgbaird | "Fetch this Edison task: c0f412d3-…" → kicks off PR #7's evidence-based scoreboard. |
| 2026-04-24 01:13 | PR #5 comment | sgbaird | "Help me get your designs 3D printed to try prototyping and testing it out." |
| 2026-04-24 01:39 | Issue #8 (open) | sgbaird | Bare-bones Digital Discovery LaTeX template (parallel doc track). |
| 2026-04-24 01:40 | Issue #10 (open) | sgbaird | "Search for commercial powder dispensing solutions, several Edison queries." |
| 2026-04-24 01:51 | PR #2 comment | sgbaird | "Include full assembly image from CAD (embed in your comment reply)." |
| 2026-04-24 04:31 | PR #2 comment | sgbaird | "Implement the most recent Edison feedback. All points check out." |
| 2026-04-24 04:32 | PR #5 comment | sgbaird | "Apply changes based on the comments in [reviewer thread]." |
| 2026-04-24 04:46 | PR #5 comment | sgbaird-alt | "Pick up from where you left off before you hit the rate limit. Render and recompile." |
| 2026-04-24 04:49 | PR #11 comment | sgbaird-alt | "Pick up from where you left off. Edison queries stuck at 99% — re-run just one. Don't wait." |
| 2026-04-24 04:51 | PR #2 comment | sgbaird-alt | "Apply changes based on [reviewer thread]; pick up from where you left off (higher priority)." |
| 2026-04-24 05:11 | PR #11 comment | sgbaird-alt | "Some of the images you pulled don't make much sense (chemspeed swing image, Unchained Labs). Go through one by one." |
| 2026-04-24 05:14 | PR #2 comment | sgbaird-alt | **Permanent rule:** "If you make changes to CAD drawings, recompile/render them (images, GIFs, STLs, etc.)." |
| 2026-04-24 05:16 | PR #2 comment | sgbaird-alt | "Send the latest designs (code, data, CAD, images) to Edison analysis. Don't wait." |
| 2026-04-24 05:21 | PR #7 comment | sgbaird-alt | "Created an OnShape Educator account; need to request developer API access." |
| 2026-04-24 05:31 | PR #5 comment | sgbaird-alt | "Added a new API key. Resubmit the jobs you were waiting for. Do I actually need the GitHub Actions workflow file?" |
| 2026-04-24 05:45 | PR #11 comment | sgbaird-alt | "Fetch new Edison queries and incorporate new findings." |
| 2026-04-24 05:49 | PR #5 comment | sgbaird-alt | "Implement the suggestions in 08; the others were for #11." |
| 2026-04-24 05:55 | Issue #12 (open) | sgbaird-alt | Consider alternative dosing styles other than #2 / #5 — seeds PR #13. |
| 2026-04-24 05:56 | PR #5 comment | sgbaird-alt | "Send a new follow-up Edison query (analysis mode with image + code uploaded per official Edison docs) for design feedback." |
| 2026-04-24 06:18 | PR #13 comment | sgbaird-alt | "Try again" — leads to the eight-alternatives composite (sieve cup, Pez strip, capillary dip, brush, salt-shaker, passive auger, ERM-augmented sieve, solenoid-tap). |
| 2026-04-24 06:48 | PR #13 comment | sgbaird-alt | "Fetch the Edison result. Incorporate the feedback." (Edison promotes ERM-augmented sieve, Besenhard 2015.) |
| 2026-04-24 07:00 | PR #13 comment | sgbaird-alt | "Create a preliminary design for the top recommended systems, following procedure from #2 and #5 and tools from #7." |
| 2026-04-24 18:50 | Issue #15 (open) | sgbaird | Six candidate powders identified, hand-tested videos posted. |
| 2026-04-24 18:55 | Issue #15 comment | sgbaird | Per-powder hand-test videos (rice flour, brown rice flour, sodium alginate, calcium lactate, CMC, xanthan gum, mix-of-six). |
| 2026-04-24 19:00 | **PR #16 (open)** | **devoranajjar** | **Authored the initial Archimedes auger CAD** (OpenSCAD): one-piece rotating helical dispenser, 20 mm OD × 100 mm, M3 spindle mount, 2.5 mm exit. |
| 2026-04-24 19:06 | Issue #1 comment | sgbaird | **"Devora, Ron, and I talked. We're moving towards a vertical auger / Archimedes screw — based system with a sieve at the end, possibly a solenoid for tapping and a small disc vibration motor."** This is the actual pivot — a three-person decision, not a solo agent recommendation. |
| 2026-04-24 19:45 | PR #13 comment | sgbaird | "Noting that we're going to try a vertical auger. #16." |
| 2026-04-24 19:48 | PR #16 comment | sgbaird | "Get this file ready for 3D printing — convert to STL, prep for an Ultimaker with 2.4 mm filament. Follow the practices from #13, #7, #2." |
| 2026-04-24 20:17 | PR #16 comment | sgbaird | "Make a STP file instead. Looks like that's what's assumed and required." |
| 2026-04-24 20:30 | PR #7 comment | sgbaird | "What's the best approach for STEP files instead of only STL? Ultimaker and others would need STEP." |
| 2026-04-24 20:31 | PR #7 comment | sgbaird | "Consider CuraEngine and Cura." |
| 2026-04-24 20:41 | PR #16 comment | sgbaird | "Send code, figures, design files, and data to Edison analysis. Then get two sliced versions per #7." |
| 2026-04-24 20:43 | PR #16 comment | sgbaird | "When I said I didn't see the STL, I meant on the Ultimaker. Same for the Ender. Same for the STEP." |
| 2026-04-24 22:17 | PR #16 comment | sgbaird | "I don't have a desktop right now — slice it manually. Goes to an Ender via USB drive." |
| 2026-04-24 22:41 | PR #16 comment | sgbaird | "Are you slicing this with PrusaSlicer?" |
| 2026-04-24 22:49 | PR #16 comment | sgbaird | "Try with cura-engine. Also is it supposed to be able to spin in the middle freely?" |
| 2026-04-24 23:04 | PR #16 comment | sgbaird | **"It's supposed to be two parts. Use the real auger design. Assume the shaft will be fixed and the outer tube will be rotated."** — final architecture call. |
| 2026-04-24 23:14 | PR #16 comment | sgbaird | "When you're done, make it very very short so it's easy to print quickly. We are almost done with the workshop." |
| 2026-04-24 23:24 | Issue #17 (open) | sgbaird | Wrap-up presentation request: include funny gifs, before/after, Edison's role, final design; follow Jean-Luc Doumont principles; submit to Edison `analysis` for review. |
| 2026-04-25 (workshop) | external | **Nasa** | Helped run the actual Ultimaker 3 Extended print of the auger that appears in the final-photo and print-video slides. |
| 2026-04-25 02:07 | PR #7 comment | sgbaird | "What if I wanted to send it to a Bambu printer programmatically?" |
| 2026-04-25 02:09 | PR #13 comment | sgbaird | "I'm not really sure what's going on in any of these designs" → leads to per-concept annotated explainer panels. |
| 2026-04-25 (PR #18 thread) | PR #18 review | sgbaird | "How do I present it with the videos? You missed some of the hilarious gifs." |
| 2026-04-25 (PR #18 thread) | PR #18 review | sgbaird | "By hilarious gifs I meant the two that showed the excavator system moving to the right in 2D and dumping powder. Could you host the html on a webpage?" |
| 2026-04-25 (PR #18 thread) | PR #18 review | sgbaird | "7 min presentation is right length. Don't worry about number of slides, just number of messages. Not a huge fan of the current iteration — tone. Fetch Edison feedback and apply." |
| 2026-04-25 (PR #18 thread) | PR #18 review | sgbaird | "Apply changes based on [reviewer thread]." (fail-fast on missing Edison files; Jean-Luc capitalization.) |
| 2026-04-25 (PR #18 thread) | PR #18 review | sgbaird | "Help me get this pointing to this branch so I don't have to merge into main for GitHub Pages." |
| 2026-04-25 (PR #18 thread) | PR #18 review | sgbaird | "It's not working. Verify by checking that web page." → was a CDN cache; deploy was healthy. |
| 2026-04-25 (PR #18 thread) | PR #18 review | sgbaird | **"Some of the messages are misaligned. Time-sort every instruction from me and Devora. Plan the narrative update. Devora and Ron were on the team — put on title slide. Nasa helped with the Ultimaker print (non-intrusive accreditation)."** This file + the deck edits are the response. |

## Team

- **Sterling Baird** (`@sgbaird`, `@sgbaird-alt`) — PI, ran the
  workshop, drove the agent, made the architecture calls.
- **Devora Najjar** (`@devoranajjar`) — collaborator. Authored
  the technical-viability writeup (issue #3) and the initial
  Archimedes auger CAD (PR #16), and was in the in-person
  conversation that produced the pivot.
- **Ron** — in-person collaborator; part of the three-person
  conversation that produced the auger pivot (issue #1).
- **Nasa** — helped run the Ultimaker 3 Extended print of the
  auger seen in the final-photo and print-video slides.

## Narrative re-alignment plan

1. **Title slide** — list the team and credit Nasa for the print.
2. **Opening problem slide** — replace "one engineer, one coding
   agent" with the actual team framing; attribute the
   "surface forces, not gravity" quote to Devora.
3. **Pivot slide** — surface "Devora, Ron, and I talked" as the
   real hinge so the auger pivot doesn't read as a solo
   agent recommendation.
4. **Auger CAD slide** — note that PR #16 was opened by Devora;
   the agent finished the prep (STL/STEP, slicer, two-part
   split, short height for the workshop deadline).
5. **Final-photo / print-video slides** — credit Nasa for the
   Ultimaker print run (non-intrusive line, not a slide of
   its own).
