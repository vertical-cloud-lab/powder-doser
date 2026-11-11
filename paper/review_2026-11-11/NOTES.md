# Sterling's review of the v2 figures and tables (11 Nov 2026)

Feedback from the [12-minute screen recording](https://youtu.be/jVrScVe-4QI) of
[PR #209](https://github.com/vertical-cloud-lab/powder-doser/pull/209) at `113750b`. Each
timestamp links to that moment in the video; the corrected transcript, with where the cursor
was, is in [TRANSCRIPT.md](TRANSCRIPT.md). Remarks are grouped by figure. Where a later remark
refers back to an earlier one (the arrows, the captions, the legends, LaTeX subfigures), the
two are merged into one item.

**Status (11 Nov 2026, evening).** Everything below is implemented in `paper/v2/` unless it
is marked as an open question. The renders are in
[`paper/v2/FIGURES-AND-TABLES.md`](../v2/FIGURES-AND-TABLES.md) and in the PR description.
Figure numbers in the headings are the new ones: 2b became Fig. 3, so old Figs. 3–6 are now
Figs. 4–7.

## Applies to every figure

| # | Feedback | What was done |
|---|---|---|
| G1 | **Show each caption with its figure, as text, not inside the image** ([00:12](https://youtu.be/jVrScVe-4QI?t=12), [08:54](https://youtu.be/jVrScVe-4QI?t=534)). | The PR description and `paper/v2/FIGURES-AND-TABLES.md` now show the full draft caption as text directly under every figure. No caption or title text is drawn inside any image. |
| G2 | **The caption's first or second sentence states the takeaway** ([08:54](https://youtu.be/jVrScVe-4QI?t=534)). Prompted by Fig. 6 and by not remembering the point of Fig. 2b ([02:34](https://youtu.be/jVrScVe-4QI?t=154)). | Every caption now opens with a bold title and then one sentence stating its message. |
| G3 | **Use LaTeX subfigures** for Figs. 1, 2, 4 and 5 and for the new figure made from 2b. Fig. 3 (how a dose runs) is the exception ([09:51](https://youtu.be/jVrScVe-4QI?t=591), [10:28](https://youtu.be/jVrScVe-4QI?t=628)). The closed-loop figure was also "maybe not for this one" ([09:51](https://youtu.be/jVrScVe-4QI?t=591)). | Each panel of those figures (new Figs. 1, 2, 3, 5, 6) is now its own PDF at print size, with no panel letter. [`paper/v2/figures.tex`](../v2/figures.tex) assembles them with `subcaption`, which typesets (a), (b), … with a short subcaption, and holds every caption. It compiles to [`figures.pdf`](../v2/figures.pdf). The dosing figure (new Fig. 4) and the closed-loop figure (new Fig. 7) stay as single images, because the leader lines and the shared powder axis cross panels. The previews are rendered from the compiled LaTeX (MiKTeX). |
| G4 | **A line, not an arrow, where the arrowhead means nothing** ([11:14](https://youtu.be/jVrScVe-4QI?t=674)). Said of the leaders from the dosing keyframes to the trace, "in general". | The keyframe leaders and the timeline connectors are plain lines. Arrows remain only where they show a direction or sequence: request → reply, the control loop, step 1 → 2 → 3, AI part → replacement, and the drawing that was given to the agent. |
| G5 | **Left-align multi-line labels** (Fig. 2a labels [00:32](https://youtu.be/jVrScVe-4QI?t=32); Fig. 6 titles [09:17](https://youtu.be/jVrScVe-4QI?t=557)). | Done in both, and in the other figures with multi-line labels. |
| G6 | **Legends belong where they apply, and only when they add something** (Fig. 5 [05:57](https://youtu.be/jVrScVe-4QI?t=357); Fig. 6 [08:19](https://youtu.be/jVrScVe-4QI?t=499)). | Fig. 5's powder-group legend is inside panel (a); the tap-category legend is gone; Fig. 6's legend is reduced to the two powder groups and the off-scale marker. |
| G7 | **Show the actual tables in Markdown** ([11:29](https://youtu.be/jVrScVe-4QI?t=689)). | The PR description now contains every table in full, not a summary of them. |
| G8 | **Make the latest version easy to find**; older comments will be hidden ([11:57](https://youtu.be/jVrScVe-4QI?t=717)). | The PR description is kept as the current version: figures, captions and tables at the latest commit. Older versions stay in its edit history. |

## Fig. 1 The doser

| # | Feedback | What was done |
|---|---|---|
| 1.1 | "I like this overall" ([00:01](https://youtu.be/jVrScVe-4QI?t=1)). | Layout kept. |
| 1.2 | (c) and (d) are "a little lackluster"; (d), the beaker photo, "could probably be replaced with a mount [cam?], maybe" ([00:04](https://youtu.be/jVrScVe-4QI?t=4)). | **Uncertain wording.** Whisper heard "mount cap" (large-v3, medium.en) or "round cap" (large-v2); the cursor was on the beaker photo. Read as "mounted camera". (d) is now the fixed livestream camera's view of the cup after a 0.5 g NaCl dose (15 Sep), labelled with the delivered mass. (c), the auger section, is unchanged apart from being its own subfigure, because no change was named for it. **Please confirm what "mount cap" meant, and what would make (c) less lackluster.** |

## Fig. 2 AI agents and engineers (timeline)

| # | Feedback | What was done |
|---|---|---|
| 2.1 | "Looking pretty good" ([00:23](https://youtu.be/jVrScVe-4QI?t=23)). | Layout kept. |
| 2.2 | The "Whole module, one request" image is too small and low-resolution, and could be vertical ([00:25](https://youtu.be/jVrScVe-4QI?t=25)). | The side view was a thin wireframe filling a small part of a 1400 × 1100 black canvas. It is replaced by the isometric view of the same model (PR #35, same commit), which stands upright. That view is rendered from its SVG at 2× with thicker lines, and fills its frame like the other images. |
| 2.3 | Left-align the labels ([00:32](https://youtu.be/jVrScVe-4QI?t=32)). | Labels are left-aligned to each frame's left edge. |
| 2.4 | Separate the agent (Copilot) from the model (Opus 4.7), e.g. a lighter colour for the model ([00:39](https://youtu.be/jVrScVe-4QI?t=39)). | Part name in black, agent or tool in the AI purple, model in light grey italic. |
| 2.5 | Connectors should attach to the frames, and should go "up, to the side, and back up" instead of straight diagonals ([00:56](https://youtu.be/jVrScVe-4QI?t=56), [01:11](https://youtu.be/jVrScVe-4QI?t=71)). | Each connector is a right-angled line, up from the date, along, then up (or down) into the middle of its frame, and it touches the frame. |
| 2.6 | The caption should point out specifics, with links to "certain places" ([01:23](https://youtu.be/jVrScVe-4QI?t=83)). | The caption names what each step shows and gives its issue or PR number. In Markdown these are links. |
| 2.7 | (a) and (b) were shown as two separate images; together they make a huge figure. Make (b) its own figure: tap collar on top, auger and bracket below, a three-part figure ([01:52](https://youtu.be/jVrScVe-4QI?t=112), [02:15](https://youtu.be/jVrScVe-4QI?t=135)). | Done. **Fig. 3 (new)** has (a) tap collar across the top, and (b) auger and (c) bracket side by side below. Fig. 2 is now (a) the timeline and (b) the agent and model bars, which are subfigures sharing the date axis. Later figures move up by one. |

## Fig. 3 (was 2b) The original AI parts and what replaced them

| # | Feedback | What was done |
|---|---|---|
| 3.1 | "I kind of forgot what the point of this was" ([02:34](https://youtu.be/jVrScVe-4QI?t=154)). | The caption now opens with the point: each AI-modelled part was reviewed, printed and tested, and the part on the tested doser is a later redesign. |

## Fig. 4 (was 3) How a dose runs

| # | Feedback | What was done |
|---|---|---|
| 4.1 | The small phone screenshot next to the chat is "weird" ([02:49](https://youtu.be/jVrScVe-4QI?t=169)). | Removed. |
| 4.2 | (c) looks fine ([03:03](https://youtu.be/jVrScVe-4QI?t=183)). | Kept. |
| 4.3 | (b), the feedback loop, is confusing; make it "linear, with a loop back in on itself" ([03:03](https://youtu.be/jVrScVe-4QI?t=183)). | Redrawn as one left-to-right row (dose request → three-phase controller → auger, taps and tilt → balance, with "powder" on the last arrow). A single "measured mass, read after every step" line loops back under the row from the balance to the controller. |
| 4.4 | Keyframe leaders: line, not arrow ([11:14](https://youtu.be/jVrScVe-4QI?t=674)). | Done. |
| 4.5 | The only figure that is not subfigures ([10:28](https://youtu.be/jVrScVe-4QI?t=628)). | Kept as one image. |

## Fig. 5 (was 4) Using the doser

| # | Feedback | What was done |
|---|---|---|
| 5.1 | Good: cap, fitting, over the cup ([03:35](https://youtu.be/jVrScVe-4QI?t=215)). | Kept. |
| 5.2 | (c) needs a callout for the aluminium cup, "6063?" ([03:49](https://youtu.be/jVrScVe-4QI?t=229)). | Callout added, "Aluminium cup (6063?)". **Please confirm the alloy grade.** The question mark stays until then. |
| 5.3 | (d) is nice; Sam may replace the photo ([04:01](https://youtu.be/jVrScVe-4QI?t=241)). | Kept until Sam's photo arrives. |
| 5.4 | Align (a)–(d); (d) sits lower ([04:07](https://youtu.be/jVrScVe-4QI?t=247)). | All four are subfigures of the same height, top-aligned. |
| 5.5 | Drop "Label, and delivery per revolution at 22.5°"; put 22.5° in the caption, with an asterisk on one "per rev." ([04:28](https://youtu.be/jVrScVe-4QI?t=268)). | Header removed. "146 mg per rev.\*" on the first label, and the caption says "\*at 22.5° tilt". |

## Fig. 6 (was 5) Open-loop delivery

| # | Feedback | What was done |
|---|---|---|
| 6.1 | (a) is fine; (c) is good ([04:47](https://youtu.be/jVrScVe-4QI?t=287), [05:30](https://youtu.be/jVrScVe-4QI?t=330)). | Kept. |
| 6.2 | (b): keep showing the **standard deviation of a single tap**; it predicts what a tap will do ([04:55](https://youtu.be/jVrScVe-4QI?t=295)). | The error bars were standard errors of the mean. They are now the standard deviation of the eight taps, and the caption says so. |
| 6.3 | Drop "log scale" from the x label ([05:33](https://youtu.be/jVrScVe-4QI?t=333)). | Now "Mass per auger revolution (mg)". |
| 6.4 | (a)'s x label runs into (b) ([05:33](https://youtu.be/jVrScVe-4QI?t=333)). | Separate subfigures, so the panels no longer touch. |
| 6.5 | Move the blue/orange legend into (a)'s unused white space ([05:57](https://youtu.be/jVrScVe-4QI?t=357)). | It now sits inside (a), right of the slow powders and above the grey band. |
| 6.6 | "Tap resolved / within balance noise / run failed screening" is confusing at this scale; drop it ([06:25](https://youtu.be/jVrScVe-4QI?t=385)). | Removed from (b): every bar is filled in its powder's colour, with no hollow or hatched bars and no legend. The SI table keeps the detail (italic = within balance noise; † = failed screening). |

## Fig. 7 (was 6) Closed-loop doses

| # | Feedback | What was done |
|---|---|---|
| 7.1 | Too many dots, with no clear separation between (a), (b) and (c) ([07:09](https://youtu.be/jVrScVe-4QI?t=429)). | Wider gaps between panels, a frame around each panel, light bands on alternate rows, and smaller markers. |
| 7.2 | Show all three targets at once? (undecided: "I don't really know how to deal with this") ([07:21](https://youtu.be/jVrScVe-4QI?t=441)). | Not changed: three panels remain, because percent-of-target error does not share a scale across targets. **Open question.** |
| 7.3 | Legend: is "research-relevant, outside limit" needed when the green band already shows it ([08:19](https://youtu.be/jVrScVe-4QI?t=499))? | Removed, along with the filled/hollow distinction: every marker is filled, colour and shape give the powder group, and the band gives the limit. The legend has four entries: the two groups, the band, and the off-scale marker. |
| 7.4 | Refine it to convey a message; caption leads with the takeaway ([08:46](https://youtu.be/jVrScVe-4QI?t=526)). | The caption opens with the message: 1 g doses landed within ±5% for every powder that delivered at least 26 mg per revolution, and smaller doses missed more often, with fast powders tending to overshoot and slow ones to fall short. Rows are ordered by flow rate so the pattern reads top to bottom, and each panel's title gives its pass count. |
| 7.5 | Left-align the two-line titles ([09:17](https://youtu.be/jVrScVe-4QI?t=557)). | Done. |
| 7.6 | The off-scale markers at the right of (a) collide with "(b)" ([09:30](https://youtu.be/jVrScVe-4QI?t=570)). | Panel letters moved into each title line, and the panels are further apart. |

## Tables

| # | Feedback | What was done |
|---|---|---|
| T1 | Show the actual tables in Markdown ([11:29](https://youtu.be/jVrScVe-4QI?t=689)). | Tables 1–4, Table S1 and the candidate failure-modes table are now written out in full in the PR description. |

## Open questions from this review

1. **"Mount cap" ([00:06](https://youtu.be/jVrScVe-4QI?t=6)).** Was this "mount cam" (the fixed camera's view, now used in Fig. 1d), or something else?
2. **Aluminium grade ([03:49](https://youtu.be/jVrScVe-4QI?t=229)).** Is the cup 6063?
3. **Fig. 7 as one panel ([07:21](https://youtu.be/jVrScVe-4QI?t=441)).** Keep three panels, or try one combined plot (e.g. error in mg on a symmetric log axis)?
4. **Sam's replacement photo for Fig. 5d ([04:01](https://youtu.be/jVrScVe-4QI?t=241)).**
