# Best practices for using Zoo Design Studio with the multi-doser design (response to issue #92)

This file responds to issue #92 ("Zoo Design Studio - testing out with multi-doser
design"), which asks us to recommend best practices for how we would actually go about
using these tools for the powder doser. It leads with **general guidance distilled from
zoo.dev's official documentation** (including the Zoo Design Studio feature reference), then
adds the lessons from our own ZDS runs — the first one captured in the PR #7 thread and the
team's hands-on trials reported in issue #92 — and how they map onto the multi-doser
architecture from issue #30 / PR #31.

Related xrefs:

- Zoo Design Studio docs (feature subtree): https://zoo.dev/docs/zoo-design-studio
- Zoo Design Studio trial + exported transcript: https://github.com/vertical-cloud-lab/powder-doser/pull/7#issuecomment-4482605596
- Team trial observations (editing/interaction feedback): issue #92 (https://github.com/vertical-cloud-lab/powder-doser/issues/92#issuecomment-4672557336)
- Multi-doser brainstorming (architecture options, no shared wetted path before the cup): issue #30
- Synthesized dispenser-architecture write-up (per-channel auger, gravimetric weighing, A&D balance): PR #31

## What Zoo Design Studio is (per zoo.dev)

Zoo Design Studio (ZDS) is a unified CAD platform built on Zoo's own geometry engine that
combines traditional sketch + feature-tree modeling with **Zookeeper**, an ML/LLM-powered
conversational CAD agent. Zoo's stated position is that Zookeeper "works alongside existing
CAD tools rather than replacing them," turning natural-language intent into editable
parametric **KCL** (KittyCAD Language) geometry.
([docs](https://zoo.dev/docs/zoo-design-studio/zookeeper))

A few official platform facts worth knowing before adopting it:

- **Desktop app is the full-featured path; the browser version is for quick access.** Zoo
  ships native desktop apps for Windows/macOS/Linux and recommends them; the in-browser
  version "is meant to be used as more of a testing environment." Web caveats: project files
  live in browser-managed storage (not a folder on disk) and full desktop-style multi-project
  workflows are not supported in the browser. ([FAQ](https://zoo.dev/docs/faq),
  [system requirements](https://zoo.dev/docs/zoo-design-studio/features/system-requirements))
- **It is cloud-backed and needs an internet connection** (the geometry engine runs in the
  cloud). The interactive session runs on Zoo's cloud compute and **streams the rendered
  viewport** back to you ("Zoo Stream"), so responsiveness/lag is tied to the stream and the
  app rather than to local GPU horsepower — and a stable network matters more than a fast
  workstation. ([FAQ](https://zoo.dev/docs/faq),
  [Zoo Stream](https://zoo.dev/docs/zoo-design-studio/features/system-requirements/zoo-stream))
- **Pricing / metering**: the free tier includes **20 minutes of Zookeeper reasoning time**;
  paid tiers add more (or unlimited) reasoning time. Budget reasoning time, not just seats.
  ([FAQ](https://zoo.dev/docs/faq), [pricing](https://zoo.dev/zoo-pricing))
- **Interoperability** — Import: STEP/STP, SLDPRT, KCL, STL, glTF/GLB, OBJ, FBX, PLY.
  Export: STEP, STL, glTF, OBJ, PLY, FBX. ([FAQ](https://zoo.dev/docs/faq))
- **KCL is plain-text and git-friendly**, which Zoo explicitly calls out as making designs
  "highly portable and readily version-controllable."
  ([getting started](https://zoo.dev/docs/zoo-design-studio/getting-started))

## Official zoo.dev best practices

These are the guidelines Zoo itself publishes; they should be our baseline house style for
any ZDS work.

**Prompting (Text-to-CAD / Zookeeper):**

- **Be specific and quantitative.** State the part type and purpose, the full bounding-box /
  exterior dimensions with **explicit units (mm preferred)**, and every feature with *what*
  (hole/slot/fillet/chamfer), *how big* (diameter/depth/radius), and *where* (centered, "8 mm
  from edge", pattern). Specify mating parts and clearances when a fit matters.
- **Build incrementally, not in one shot.** Zookeeper is designed around "incremental,
  structured natural-language commands" — create a feature, adjust dimensions, refine
  constraints, repeat. Zoo's guidance is to **change one detail and re-render** when a result
  is off, rather than restarting from a fresh prompt.
  ([Zookeeper docs](https://zoo.dev/docs/zoo-design-studio/zookeeper))
- **Let the agent scope first.** Zookeeper can act as a domain expert, propose constraints
  and parameters, and produce a design plan *before* geometry; use that planning step and
  answer its clarifying questions precisely.
- **Use selection awareness.** Point at a face/edge/feature and let the agent act on the
  selection instead of describing the location in words.
- **Use its model-aware tools** (mass, volume, surface area, center of mass) to check a model
  in the same loop instead of switching tools.

**Modeling:**

- **Set units before sketching** (mm/inch), and add real dimensions/constraints — KCL
  dimensions can be parameter- and formula-driven for parametric edits.
  ([getting started](https://zoo.dev/docs/zoo-design-studio/getting-started))
- **Holes: extrude the base solid first, then cut.** Per Zoo, sketching a circle inside a
  closed profile on the *same* sketch may not produce a hole; create the hole as a separate
  cutting feature / Boolean subtract.
  ([getting started](https://zoo.dev/docs/zoo-design-studio/getting-started))
- **Prefer the parametric Hole feature for fastener holes.** Rather than hand-sketching
  pockets, ZDS has a [Hole feature](https://zoo.dev/docs/zoo-design-studio/features/3d-design/parametric-modeling/solid-modeling/modify-solids/hole)
  that drives clearance/threaded/counterbore/countersink holes from explicit parameters
  (face, X/Y location, blind/through, diameter, drill-point angle). Its clearance guidance —
  add 0.2–0.5 mm to nominal screw size (M3 → 3.2–3.4 mm, M5 → 5.3–5.5 mm) — is a good default
  for the doser's mounting holes.
- **Choose the right Extrude `bodyType`.** Extrude defaults to a watertight `solid`; set
  `bodyType` to `surface` only for open reference/patch geometry. For the doser's load-bearing
  parts you want solids (so Boolean union/subtract and mass/volume queries work). The same
  Extrude tool covers both modes.
  ([surface extrude](https://zoo.dev/docs/zoo-design-studio/features/3d-design/parametric-modeling/surface-modeling/create-surfaces/extrude))
- **Drop into KCL for anything complex or repeated.** Hand-editing KCL unlocks parametric
  modeling, scripting, and modular reuse beyond point-and-click — ideal for the doser's
  16-way repeated channel. Reference the [KCL book](https://zoo.dev/docs/kcl-book) and the
  Create-from-Sample starter parts.
- **Version-control the KCL** with git, since it is plain text.

**Support / learning:** Zoo's [docs](https://zoo.dev/docs), the
[Community Forum](https://community.zoo.dev/), Discord, and the
[YouTube channel](https://www.youtube.com/@zoodotdev) are the official channels for tutorials
and help.

## Editing the agent's output (how the interaction model actually works)

Our testers found editing more constrained than a traditional history-based CAD tool —
specifically: only being able to nudge parameters the agent had set, manual values "failing"
when typed over a driven dimension, not being able to sketch on an arbitrary face, and
parameters built from other parameters being hard to untangle (issue #92
[comment](https://github.com/vertical-cloud-lab/powder-doser/issues/92#issuecomment-4672557336)).
The official docs explain why and give the supported path for each:

- **KCL is the single source of truth; graphical and code edits stay linked.** Point-and-click
  edits are *not* a separate layer — they regenerate the KCL, so the clean way to override a
  value is at its definition (the dimension, the feature, or the code), not on a derived
  readout. ([code editor](https://zoo.dev/docs/zoo-design-studio/features/workspace/code-editor))
- **The Variables Pane is read-only.** It shows *evaluated* program memory (what each parameter
  currently resolves to) and lets you inspect/copy — it is not where you change values, and it
  intentionally pauses updates while you are actively sketching. Use it to trace what a
  parameter-of-parameters evaluates to, then edit the underlying definition.
  ([variables pane](https://zoo.dev/docs/zoo-design-studio/features/workspace/variables-pane))
- **To change a driving dimension, double-click the dimension label** (in the sketch or the
  feature-tree operation) and type the new value; dimensions can be parameters/formulas. If a
  new value "won't take", the sketch is likely **over-constrained** — ZDS highlights the
  conflicting geometry/dimension in **red**, and you loosen one competing constraint before it
  re-solves. ([dimensions](https://zoo.dev/docs/zoo-design-studio/features/3d-design/parametric-modeling/sketching/dimensions))
- **Sketch-on-a-face is supported, but it is scene-driven.** Select the face in the modeling
  area to start a sketch directly on it; the feature tree explicitly notes that "some
  sketch-on-face or offset-plane workflows still require scene-based editing" and that
  user-defined function/module operations must be edited in code, not from the tree. For an
  arbitrary datum, add an
  [offset/construction plane](https://zoo.dev/docs/zoo-design-studio/features/3d-design/parametric-modeling/construction-geometry/offset-plane)
  first. ([sketching](https://zoo.dev/docs/zoo-design-studio/features/3d-design/parametric-modeling/sketching),
  [feature tree](https://zoo.dev/docs/zoo-design-studio/features/workspace/feature-tree))
- **When the agent gets stuck, steer it instead of restarting.** ZDS gives three official
  levers, all better than re-prompting from scratch:
  - **Selection awareness** — select the face/edge/feature and let Zookeeper act on the
    selection rather than describing the location in words.
    ([Zookeeper](https://zoo.dev/docs/zoo-design-studio/zookeeper))
  - **Zoodle** — screenshot the viewport, circle/arrow the exact target, attach it to the
    prompt ("move this hole 8 mm toward the marked edge"); ideal when an edit depends on a
    specific face/edge that's awkward to name.
    ([Zoodle](https://zoo.dev/docs/zoo-design-studio/features/ml-ai/zoodle))
  - **Queue and Steer / Cancel** — queue the next step while it works, *steer* a running task
    to redirect it mid-flight, or *cancel* to interrupt without losing the conversation.
    ([queue and steer](https://zoo.dev/docs/zoo-design-studio/features/ml-ai/queue-and-steer))

## How this maps to the multi-doser (what we saw in our run)

Our first real ZDS run on the doser prompt ("16 unique powders, 50–250 mL per powder, no
cross-contamination, A&D balance, ±0.1 mg") is in the PR #7 thread. Aligning it with the
official guidance above:

- The agent followed Zoo's **scope-first** pattern well: it asked the right clarifying
  questions (dispenser count, dose accuracy, per-powder vs. total volume, inert-atmosphere
  need) before modeling, and encoded our key constraint — **no shared funnel/manifold upstream
  of the collection cup** (per-channel gates + secondary shutter) — matching the issue #30 /
  PR #31 consensus.
- It self-validated by linting, executing, constraint-checking, and rendering multi-view +
  close-up snapshots — the kind of in-loop checking Zoo's model-aware tooling is built for.
- **Watch-out (read the encoded assumptions):** it partly conflated our two stations
  (high-res ±0.1 mg trim vs. higher-capacity coarse) into one cup, then flagged the
  discrepancy itself. Treat the agent's final assumption summary as something to verify, not
  accept. The fix is the official "change one detail and re-render" loop, not a restart.
- The output was **concept-grade geometry**: 16 cloned cartridge bodies with no boolean
  union, placeholder tolerances/fasteners. Good for layout exploration, not manufacture.

### KCL gotchas observed (useful when reviewing ZDS output)

These tripped the agent mid-run and are worth knowing:

- **KCL has length units only.** Mass (`g`) and volume (`mm^3`) literals are invalid; express
  those as plain numbers or derive them, or execution fails with a syntax error.
- **`revolve` axis must lie in the sketch plane** (sketching on `XZ` then revolving about `Z`
  failed; the axis had to be `Y`).
- **Off-origin sketch points accidentally coincident with the origin** broke region resolution
  ("unable to create a region that contains the requested query point"); anchor points need
  explicit constraints.
- **Validate at the project level** — per-file mock-execute fails on imports
  (`No such file or directory: parameters.kcl`).

## Recommended workflow for the team

1. **Install the desktop app** (browser only for quick throwaway tests), and confirm
   reasoning-time budget against the [pricing tiers](https://zoo.dev/zoo-pricing) before a
   session.
2. **Frame the prompt as a spec sheet** following Zoo's "be specific" guidance: dispenser
   count, per-channel capacity, dose tolerance (±mg/±%), balance model, "no shared wetted path
   before the cup", inert-gas requirement, and overall envelope. Reuse the issue #30 / PR #31
   language verbatim.
3. **Iterate incrementally** — answer clarifying questions, then change one detail per turn
   (e.g. correct the two-station framing) rather than restarting. When the agent stalls or
   misplaces a feature, **steer it** rather than re-prompt: select the geometry, use **Zoodle**
   markup to point at the exact face/edge, and **Queue/Steer** the running task. Edit driving
   values at their definition (double-click the dimension or edit the KCL), not on the
   read-only Variables Pane.
4. **Read the agent's encoded assumptions** in its summary and correct misreads.
5. **Commit the artifacts** for reproducibility: the plain-text KCL project, the conversation
   transcript (as PR #7 did), and representative renders. Keep ZDS concept explorations in a
   clearly "concept-only" location, distinct from the authoritative parametric parts in
   `cad/<part-name>/`.
6. **Hand off to our own pipeline** (CadQuery / committed `.step` + `.stl` +
   `render_views.py`) for anything needing real tolerances, interference checks, or manufacture.
   ZDS sets direction; it does not replace that pipeline. Note also that the headless `zoo`
   CLI / KittyCAD API path is separately rate-limited and has returned HTTP 402
   `missing_payment_method` even when logged in, so do not assume an API token alone unblocks
   automated export/render in CI — keep a CadQuery mirror as a fallback.
7. **Keep humans in the loop on safety.** Zookeeper's internet-aware reasoning surfaced
   combustible-metal-dust pointers (OSHA, NFPA 660) unprompted, which is useful, but a real
   Dust Hazard Analysis and process-safety review for Al/Mg/Fe/Si fines are non-negotiable and
   out of scope for the tool.

## Limitations

- Outputs are concept-grade geometry: placeholder dimensions, no assembly booleans, no real
  fastener/interface modeling, no DFM.
- Non-deterministic: the same prompt can yield different layouts; pin a run by committing its
  KCL + transcript.
- Reasoning-time metering and the desktop-first / cloud-dependent model can gate a session.
- Not a safety or compliance authority.

## Next steps

- Re-run the prompt with the corrected two-station framing (high-res ±0.1 mg trim station +
  higher-capacity coarse station sharing one shuttled cup) and commit the KCL + transcript.
- Stand up a clearly-labeled concept folder for ZDS exports plus a short reviewer checklist
  (assumptions read? KCL gotchas checked? transcript committed? handed to CadQuery for any
  load-bearing geometry?).
- Compare the ZDS radial-carousel concept against the inward-collection-cup geometry from
  PR #31 to decide which layout to carry into the authoritative `cad/` models.
