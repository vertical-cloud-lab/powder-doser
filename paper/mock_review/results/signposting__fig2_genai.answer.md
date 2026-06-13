The current figure/caption does **not yet make the HUMAN vs AI split unambiguous enough** for a reader who sees Fig. 2 in isolation.

Why:
- The current caption names AI repeatedly, but usually leaves the human role implicit. For example, panel (b) says the part was improved by “iterative review in the programmatic workflow” and later redesigned in Zoo Design Studio, but it does not state that the **human team** made the design decisions, supplied drawings/specifications, reviewed outputs, and then printed/tested parts.
- Panel set (e–h) comes closest by naming a “human-side error” (stale input files), but still doesn’t clearly say that the **AI contribution was modelling the geometry** while the **human contribution was specifying, checking, and correcting the workflow inputs**.
- This falls short of the explicit signposting requested in `pr97_comments.md`: “it should always be clear who did what” (`pr97_comments.md`, lines 23–25), and “Only distinguish what was human vs. what was AI … no CAD UI such as Fusion 360 or Solidworks was used” (`pr97_comments.md`, lines 31–36, 128–130).

Grounding in supplied files
- The caption under review is `caption_fig2_genai.md`. It currently reads as a failure/success narrative for AI outputs, but not as a clean division of labour. In particular:
  - panel (a): “First AI-generated tap collar…”
  - panel (b): “after iterative review in the programmatic workflow…”
  - panels (e–h): “The root cause was stale input files—a human-side error…”
- The figure-generation source `make_figures.py` reinforces the same emphasis. Its panel titles are:
  - (a) “Tap collar, first AI proposal: interferences, bad tolerancing, no component clearance”
  - (b) “Tap collar after review iterations (final part redesigned in Zoo)”
  - (c) “Geared auger + pinion (part-by-part workflow)”
  - (d) “Whole-assembly attempt (single prompt, v1 module)”
  - (e–h) four mounting-plate iterations ending with “correct inputs → clean plate”
  These titles identify AI outputs and workflow state, but not the human role explicitly.
- The manuscript text in `main.pdf` is clearer than the caption and should be matched. On page 2, the paper states: “the human team made the design decisions, supplied specifications and drawings, reviewed every output, and printed and tested the parts, while the AI tools did the modelling.” That sentence is the cleanest available statement of division of labour and should be echoed in the caption.
- `pr97_comments.md` adds two important constraints that the caption should respect:
  1. “it should always be clear who did what” (lines 23–25)
  2. “eventually, ai was only being used to model the parts, not to make design decisions beyond calculating relevant dimensions and tolerancing” (lines 68–71)
- `pr97_comments.md` also corrects the interpretation of panel (a): it is bad because of “interferences, incorrect tolerancing, no space for relevant components, and a general lack of spatial reasoning” (lines 38–45). The current caption already incorporates that correction well.
- The same comment file also says the tap collar “ended up resorting to zoo” and that Zoo Design Studio was “the best option by the researchers” (lines 44–45, 52–56). The current caption mentions this, but should still frame Zoo as an **AI tool used late/exploratorily**, not as human GUI CAD.
- The branch tree identifies relevant provenance files that support the human-specification side of the workflow, even though they are not included in this bundle for direct inspection. Most relevant are:
  - `cad/mounting-plate/drawing/engineering_drawing.pdf`
  - `cad/mounting-plate/drawing/engineering_drawing.png`
  - `cad/mounting-plate/drawing/engineering_drawing.svg`
  - `cad/mounting-plate/engineering_drawing.py`
  These branch-tree paths are consistent with the manuscript/review claim that humans supplied annotated or dimensioned drawings.
- The branch tree also names files consistent with late Zoo-based programmatic CAD rather than conventional GUI CAD, for example:
  - `cad/meta-tools/logs/zoo-text-to-cad.log`
  - `cad/meta-tools/zoo-output/full-system/full_system.kcl`
  - `cad/mounting-plate-assembly/kcl/mounting_plate.kcl`
  - `cad/mounting-plate-assembly/imported-parts/tap-collar/tap_collar.step`
  Those paths support the manuscript’s framing that CAD remained code/chat mediated.

Panel-by-panel signposting judgment
- **(a) Tap collar, first AI proposal**: AI role is clear; human role is missing. The caption should say this was an AI-generated parametric model reviewed against human-defined functional requirements/components.
- **(b) Reviewed / final tap collar**: currently ambiguous. “after iterative review” could mean anything. It should say that humans reviewed and rejected successive AI-generated models, and that the final production collar was still AI-modelled, but in Zoo Design Studio, after human direction.
- **(c) Geared auger + pinion**: currently reads like a success case for workflow, but does not say that humans chose the part decomposition and interfaces while AI modelled the geometry.
- **(d) Whole-assembly attempt**: AI failure is clear; human comparison baseline is implied but not explicit. It should say the human team judged this route less efficient than decomposing the design into parts.
- **(e–h) Mounting plate iterations**: the current caption is accurate and useful, especially the human-side stale-input note. But it should explicitly say that the human team supplied/corrected upstream part references and reviewed each revision, while the AI generated the plate geometry from those inputs.

Recommended rewritten caption

**Figure 2. Generative-AI CAD outcomes, good and bad, with division of labour made explicit.** In all panels, the **human team** made the design decisions, supplied the specifications and annotated/dimensioned drawings, reviewed each generated result, and later printed/tested parts; the **AI tools** generated the parametric CAD geometry. No conventional GUI CAD package was used; modelling was done through programmatic CAD workflows and, late in the project, Zoo Design Studio. **(a)** First AI-generated tap-collar model: an unimplementable amalgamation of functions, with part-to-part interferences, incorrect tolerancing, no clearance for the solenoid and vibration motor it had to carry, and poor spatial reasoning. **(b)** Subsequent tap-collar model after human review of AI-generated iterations in the repository-based workflow; the production tap collar was later re-modelled with Zoo Design Studio in three iterations to reach a usable part. **(c)** Geared auger and stepper pinion from the part-by-part workflow: humans defined the decomposition and interfaces, and the AI modelled the individual parts. **(d)** Whole-assembly generation attempt from a single prompt: visually plausible, but mechanically inconsistent, with interferences and floating components that took longer for humans to diagnose than the part-by-part route took to build. **(e–h)** Four AI-generated mounting-plate revisions reviewed by humans: the model first introduced an unexplained hole (**e**), then raised platforms (**f**), then a gap that left the motor plate floating (**g**); only after the human team supplied the correct upstream part files did the AI produce a clean plate (**h**). The failure mode here was stale human-supplied inputs that the AI silently designed around.

Why this rewrite is more accurate
- It matches the manuscript’s explicit division of labour in `main.pdf` page 2.
- It matches the review instruction in `pr97_comments.md` lines 23–25 and 68–71.
- It keeps Zoo Design Studio in scope, but correctly as a late AI-assisted text/chat-driven CAD tool rather than manual GUI CAD (`pr97_comments.md`, lines 31–36, 128–130).
- It avoids naming individuals, as requested.

One more figure-level issue
- The bundle says this is `fig2_genai`, but the compiled `main.pdf` shows this content as **Fig. 3**, while **Fig. 2** in the manuscript is “Design specifics.” That mismatch may just reflect a local naming/export convention (`README.md` says “main.tex, Figure 2”), but it is worth checking so caption insertion lands on the intended figure.

Prioritized action list
- **1. Replace the caption lead sentence** with an explicit HUMAN/AI division-of-labour sentence, using the manuscript wording as the source of truth.
- **2. Revise panels (b), (c), and (e–h)** so they explicitly say humans supplied specifications/drawings or corrected inputs, while AI generated the CAD geometry.
- **3. Add one clause stating that no conventional GUI CAD was used**, to stay consistent with `pr97_comments.md` and the manuscript.
- **4. Check the figure numbering mismatch** between `README.md`/`caption_fig2_genai.md` and the compiled `main.pdf` before editing `main.tex`.

- Used the manuscript text in `main.pdf` as the primary source of truth for the HUMAN/AI division of labour because it is more explicit than the current caption.
- Treated `pr97_comments.md` as the controlling constraint for interpretation where it corrected or sharpened figure wording, especially for panel (a) and AI-vs-human signposting.
- Used `all_branches_file_tree.txt` only to name likely relevant provenance files and branch-tree paths, without claiming contents that were not present in the supplied bundle.
- Did not infer any individual-specific attribution; all attribution was collapsed to HUMAN vs AI as instructed.
- Flagged the apparent figure-number mismatch because `README.md` says Figure 2 while `main.pdf` displays the reviewed panel set as Fig. 3.