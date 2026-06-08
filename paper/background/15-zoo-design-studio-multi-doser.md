# Best practices for using Zoo Design Studio with the multi-doser design (response to issue #92)

This file responds to issue #92 ("Zoo Design Studio - testing out with multi-doser
design"), which asks us to recommend best practices for how we would actually go about
using these tools for the powder doser. It is grounded in the first real Zoo Design Studio
(ZDS) run against the multi-doser prompt, captured in the PR #7 thread, and in the
multi-doser architecture discussion in issue #30 / PR #31.

Related xrefs:

- Zoo Design Studio trial + exported transcript: https://github.com/vertical-cloud-lab/powder-doser/pull/7#issuecomment-4482605596
- Multi-doser brainstorming (architecture options, no shared wetted path before the cup): issue #30
- Synthesized dispenser-architecture write-up (per-channel auger, gravimetric weighing, A&D balance): PR #31

## What Zoo Design Studio is

Zoo Design Studio (zoo.dev) is an agentic, browser-based (and downloadable) CAD app. A
"Zookeeper" agent turns a natural-language prompt into a parametric **KCL** (KittyCAD
Language) project, then lints, executes, constraint-checks, and renders the model so it can
self-review the geometry. It is the text-to-CAD counterpart to the open-source `zoo` CLI /
KittyCAD API already noted elsewhere in this repo (KCL source, `ZOO_API_TOKEN`,
text-to-CAD endpoints).

In our trial it correctly decomposed the prompt ("16 unique powders, 50–250 mL per powder,
no cross-contamination, A&D balance, ±0.1 mg") into a sensible concept: 16 isolated radial
cartridges at 22.5° spacing, dedicated coarse-auger + fine-trim feed paths per channel, no
shared manifold upstream of a common 200 mL collection cup, and a balance bay sized to a
real A&D FZ-523 envelope. It also unprompted surfaced combustible-metal-dust safety
(OSHA / NFPA 660) — useful, but to be treated as a draft pointer, not a compliance sign-off.

## Summary recommendation (direct)

- Use Zoo Design Studio as a **fast concept-generation and design-exploration tool**, not as
  the source of record for manufacturable geometry. Treat every ZDS output as a first-draft
  concept that a human engineer refines (and that our existing CadQuery / KCL parametric
  models under `cad/<part-name>/` remain authoritative for).
- **Always commit the KCL sources and the conversation transcript** alongside renders so a run
  is reproducible and reviewable, exactly as PR #7 did by attaching the exported transcript.
- Drive it with **explicit, quantified specs and hard constraints up front** (counts,
  tolerances, capacities, "no shared path" rules); the agent's quality is dominated by how
  precisely the prompt is framed.

## How it performed on the multi-doser prompt (observations to learn from)

Good:

- Asked the right clarifying questions before modeling (how many dispensers, dose accuracy,
  per-powder vs. total volume, inert-atmosphere requirement).
- Encoded our key architectural constraint correctly: **no shared funnel/manifold upstream of
  the collection cup**, with per-channel gates and a secondary shutter — matching the issue
  #30 / PR #31 consensus.
- Self-validated: ran lint, format, mock-execute, full execute, constraint check, and rendered
  multi-view + close-up snapshots to visually confirm the layout.

Watch-outs:

- It partly misread "two stations" (high-res trim vs. high-capacity coarse) and folded them
  into one cup, then flagged the discrepancy itself — i.e. **read the agent's stated
  assumptions, they are not always what you asked for**.
- All 16 cartridges were cloned bodies with no boolean union / final assembly; tolerances,
  fasteners, and real balance interfaces were placeholders. Dimensional accuracy is concept-
  grade only.

## KCL gotchas observed (so reviewers can sanity-check ZDS output)

These tripped the agent mid-run and are worth knowing when reading or re-running its KCL:

- **KCL only has length units.** Mass (`g`) and volume (`mm^3`) constants are not valid units;
  express those as plain numbers or derive them, or execution fails with a syntax error.
- **`revolve` axis must lie in the sketch plane.** Sketching on `XZ` and revolving about `Z`
  failed; the axis had to be `Y`. Check revolve axes against the sketch plane.
- **Off-origin sketch points accidentally coincident with the sketch origin** broke region
  resolution ("unable to create a region that contains the requested query point"). Anchors
  must be explicitly constrained.
- **Per-file `mock execute` fails on imports** (`No such file or directory: parameters.kcl`);
  validate at the **project level**, not file-by-file.

## Account, cost, and export considerations

- ZDS is **credit-metered**. Our trial ran out of credits, and **exporting the conversation
  history required adding a billing method**. Budget for this before a session if the
  transcript matters (it does, for reproducibility).
- The unlimited plan was ~$99/month at trial time; reasonable for a focused exploration month,
  then downgrade. Avoid leaving long agentic sessions running idle.
- The headless `zoo` CLI / KittyCAD API path is separately rate-limited and has previously
  returned HTTP 402 `missing_payment_method` even when `zoo auth status` reports logged in, so
  do **not** assume an API token alone unblocks automated export/render in CI; keep a CadQuery
  mirror as a fallback for any geometry we depend on.

## Recommended workflow for the team

1. **Frame the prompt as a spec sheet**, not a wish: dispenser count, per-channel capacity,
   dose tolerance (±mg/±%), balance model, "no shared wetted path before the cup", inert-gas
   requirement, and overall envelope. Reuse the issue #30 / PR #31 language verbatim.
2. **Let it ask clarifying questions and answer them precisely** before saying "model it."
3. **Read the agent's encoded assumptions** in its final summary and correct any misreads
   (e.g. the two-station mix-up) in a follow-up turn rather than restarting.
4. **Export and commit the artifacts**: the KCL project files, the conversation transcript
   (markdown), and representative renders. Store concept explorations under a clearly
   "concept-only" location, distinct from the authoritative parametric parts in
   `cad/<part-name>/`.
5. **Hand off to our own parametric pipeline** (CadQuery / committed `.step` + `.stl` +
   `render_views.py`) for anything that needs real tolerances, interference checks, or
   manufacture. ZDS sets direction; it does not replace that pipeline.
6. **Keep humans in the loop on safety.** ZDS's combustible-dust pointers (OSHA, NFPA 660)
   are a starting checklist only; a real Dust Hazard Analysis and process-safety review are
   non-negotiable for Al/Mg/Fe/Si fines and are out of scope for the tool.

## Limitations

- Outputs are concept-grade geometry: placeholder dimensions, no assembly booleans, no real
  fastener/interface modeling, no DFM.
- Non-deterministic: the same prompt can yield different layouts; pin a run by committing its
  KCL + transcript.
- Credit/billing gating can block export at an inconvenient moment.
- Not a safety or compliance authority.

## Next steps

- Re-run the prompt with the corrected two-station framing (high-res ±0.1 mg trim station +
  higher-capacity coarse station sharing one shuttled cup) and commit the KCL + transcript.
- Stand up a clearly-labeled concept folder for ZDS exports and a short checklist for
  reviewers (assumptions read? KCL gotchas checked? transcript committed? handed to CadQuery
  for any load-bearing geometry?).
- Compare the ZDS radial-carousel concept against the inward-collection-cup geometry from
  PR #31 to decide which layout to carry into the authoritative `cad/` models.
