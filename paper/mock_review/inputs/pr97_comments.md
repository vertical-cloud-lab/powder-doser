# Static copy of PR #97 comments (powder-doser, Digital Discovery base manuscript)

This file is a static snapshot of the human and bot review/conversation comments
on PR #97 ("Draft base manuscript for Digital Discovery (hardware Full Paper)"),
provided so the analysis can check the manuscript and figures for inconsistencies
against what the human researchers actually said, and so it can see which
resources (issues, discussions, branches, files) are available.

Key people: @swcharles (Sam Charles), @sgbaird / @sgbaird-yolo (Sterling Baird),
@lbwinters (Luke Winters), plus other team members (Will Mulberry, Carl Robinson,
Gage Erickson). When attributing work, do NOT separate individuals — only
distinguish HUMAN vs AI contributions.

## Inline review comments (file: paper/main.tex)

### Thread @ paper/main.tex line ~178 — @swcharles
> We haven't talked about or implemented a removeable hopper. We won't have one
> on the end design, just the full auger.

> Also, it's an HR-100A load cell

### Thread @ paper/main.tex line 189 — @swcharles
> Throughout this section, clarify where ai was used. We should be signposting
> the design contributions of ai versus engineers throughout the manuscript--it
> should always be clear who did what.

### Thread @ paper/main.tex line 189 — @sgbaird
> Noting that the only way you'll be able to discern and verify this is via
> comments on GitHub. To this end, use the extracted issue and PR comments that
> have already been downloaded and organized. You can use GitHub mcp if that
> isn't working or you need additional context. In distinguishing, don't
> separate Sterling vs. Sam vs. Will vs. Luke. Only distinguish what was human
> vs. what was AI (and emphasizing that no CAD UI such as Fusion 360 or
> Solidworks was used at all from project start to end, except for the
> introduction of Zoo Design Studio, primarily controlled through chat prompts,
> and in a limited, exploratory capacity except at the very end of the project.

### Thread @ paper/main.tex line 210 (Fig. 2a) — @swcharles
> This is simply incorrect. a) is a bad example for different reasons. a) is bad
> because of interferences, incorrect tolerancing, no space for relevant
> components, and a general lack of spatial reasoning--it would be impossible to
> implement. The 'not connected to its own mounting plate' issue is from the
> bracket in the original design--it doesn't make sense in relation to the tap
> collar. Note that we ended up resorting to zoo for the tap collar:
> https://github.com/vertical-cloud-lab/powder-doser/discussions/39#discussioncomment-17284756

### Thread @ paper/main.tex line 210 — @sgbaird
> For copilot, when reasoning, check specific comments and their authors against
> the broader context (which issue/PR, date in the timeline, comments nearby it).
> You can use your organized and committed version to save time

### Thread @ paper/main.tex line 218 — @swcharles
> Take this into account:
> https://github.com/vertical-cloud-lab/powder-doser/discussions/39#discussioncomment-17284756
> Zoo Design Studio is regarded as the best option by the researchers

### Thread @ paper/main.tex line 218 — @sgbaird
> Might be worth pointing out the nuances about how it seemed slower and lower
> quality than if the mechanical engineers were to design using traditional CAD
> software; however, it led to thorough self-documentation, reproducibility,
> provenance, and transferability.

### Thread @ paper/main.tex line 245 — @swcharles
> Mention Zookeeper as a specific LLM used in Zoo Design Studio. That was an
> important part of our workflow as we turned more toward ZDS later on.

### Thread @ paper/main.tex line 193 — @swcharles
> Mention the specific drawings given, including that some of them had dimensions
> and relations (it went beyond interfaces to full part design--eventually, ai
> was only being used to model the parts, not to make design decisions beyond
> calculating relevant dimensions and tolerancing)

### Thread @ paper/main.tex line 258 (Future work) — @swcharles
> The future work has changed a bit, but progress here has not yet been reported
> on Github. This section and its figures will be changed as updated information
> is uploaded.

## Inline review comments (other files)

### paper/rsc.bst line 507 — @copilot-pull-request-reviewer (RESOLVED)
> `format.doi` currently outputs a DOI only when the DOI field is empty (and
> skips output when a DOI is present). This inverts the intended `if$` branches
> and will suppress DOI rendering throughout the bibliography.
(Fixed: branches swapped so DOI renders only when present.)

### paper/si.tex line 43 — @copilot-pull-request-reviewer (RESOLVED)
> The BOM caption sentence is missing a relative pronoun ("equipment most labs
> already own"), which reads ungrammatically in the compiled SI PDF.
(Fixed: "shared laboratory equipment that most labs already own".)

## PR conversation comments

### @swcharles
> @copilot don't apply these changes until @sgbaird reviews them and tells you to.

### @sgbaird-yolo
> address @swcharles and @sgbaird 's comments in the review.
> When done with edits, upload to Edison analysis scientific for mock reviewer
> and editor feedback based on personas in #91 for DD. Fetch next session.
> Remember to write the manuscript for the reader as part of the cohesive
> narrative, not as if you were responding to us directly.

### @sgbaird
> fetch Edison artifacts per your custom instructions

### @sgbaird (current task)
> run as many iterations as you can with Edison scientific analysis, in batches,
> with a batch size the same as the number of figures currently in the
> manuscript. For each query, upload the manuscript, the figure, the caption,
> and any source files (code, images, etc.) used to generate the figure. Also
> upload the static copy of the comments so that Edison can look through and see
> if there are inconsistencies and also so you can know what resources are
> available. Also upload the full naming tree of all files across all branches in
> the repository so Edison can identify potential files of interest if needed.

## Resource notes (for the analysis)
- Discussion #39 "High-level thoughts about AI throughout this process" (GitHub
  Discussion, not an issue) is the AI-observations journal. Relevant comment:
  discussioncomment-17284756 (tap collar redesigned in Zoo Design Studio, three
  iterations).
- Issue #50: tap-collar redesign. Issue #92: Zoo Design Studio debrief.
- PR #25/#61: BOM / electronics / KiCad control board.
- PR #91: journal editors + suggested reviewers scouting (personas for mock review).
- The 97-entry DESIGN-LOG lives in issue #73 / PR #74.
- Sensing: A&D HR-100A analytical balance (0.1 mg) over RS-232 via MAX3232 — NOT
  an HX711 load cell. No hopper in the end design; the auger tube itself is the
  reservoir, loaded via slots.
- No GUI CAD (Fusion 360 / SolidWorks) was used at any point; only programmatic
  CAD (LLM coding agents authoring parametric CAD code) and, late and
  exploratorily, Zoo Design Studio (chat-driven, with its Zookeeper agent).
