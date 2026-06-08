# Best practices for using Zoo Design Studio with the multi-doser design (response to issue #92)

This file responds to issue #92 ("Zoo Design Studio - testing out with multi-doser
design"), which asks us to recommend best practices for how we would actually go about
using these tools for the powder doser. It leads with **general guidance distilled from
zoo.dev's official documentation**, then adds the lessons from our own first ZDS run
(captured in the PR #7 thread) and how they map onto the multi-doser architecture from
issue #30 / PR #31.

Related xrefs:

- Zoo Design Studio trial + exported transcript: https://github.com/vertical-cloud-lab/powder-doser/pull/7#issuecomment-4482605596
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

- **Desktop app is the supported path; the browser is a test environment only.** Zoo
  recommends downloading the native desktop app; the in-browser version "is meant to be used
  as more of a testing environment." ([FAQ](https://zoo.dev/docs/faq))
- **It is cloud-backed and needs an internet connection** (the geometry engine runs in the
  cloud). ([FAQ](https://zoo.dev/docs/faq))
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
- **Drop into KCL for anything complex or repeated.** Hand-editing KCL unlocks parametric
  modeling, scripting, and modular reuse beyond point-and-click — ideal for the doser's
  16-way repeated channel. Reference the [KCL book](https://zoo.dev/docs/kcl-book) and the
  Create-from-Sample starter parts.
- **Version-control the KCL** with git, since it is plain text.

**Support / learning:** Zoo's [docs](https://zoo.dev/docs), the
[Community Forum](https://community.zoo.dev/), Discord, and the
[YouTube channel](https://www.youtube.com/@zoodotdev) are the official channels for tutorials
and help.

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
   (e.g. correct the two-station framing) rather than restarting.
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
