# TMS 2027 — Hidden-Gem Scan Across All 106 Symposia

**Method.** All 106 official TMS 2027 Call-for-Abstracts flyers were downloaded, text-extracted, and parsed
into [`tms2027_symposia.yaml`](tms2027_symposia.yaml) (scope, sponsors, organizers + brief researched
backgrounds). Every scope text was then keyword-scored against powder-doser project themes (powder
handling/dosing, autonomous & closed-loop experimentation, Bayesian optimization, ML calibration,
feedstock, atomization, open-source/low-cost instrumentation, generative AI), and top-scoring or otherwise
notable scopes were read in full. Sanity check: the already-shortlisted symposia (021 AI-Enabled Materials
Processing, 024 AI-ICME, 022 AI/ML/Data Informatics, 059 Atomization & Powder Metallurgy, 075 Powder
Materials Processing) rank at the top of the score list, as expected. Everything below is *in addition to*
those.

## Unexpected suggestions

### 1. Symposium 105 — Accelerating Innovation in Materials and Manufacturing: the pitch competition
The Special Topics flyer reveals a detail not visible from the title: a **midday pitch competition for
students, postdoctoral researchers, and early-career professionals**, embedded in a one-day program of
invited talks and moderated panels spanning industry, investors, academia, and government. A short pitch of
the open-source, low-cost doser (an "emerging idea" with commercialization/democratization framing) is a
very low-cost, high-visibility play — and it does not consume the one-symposium-per-abstract budget the
same way a technical talk does. Note the technical sessions themselves appear to be invited + panel format,
so the pitch competition is likely the practical entry point.

### 2. Symposium 056 — Advances in Metal Matrix Composites (Materials Synthesis & Processing track)
Unexpectedly good audience for the **powder-dosing abstract**: MMC processing is fundamentally
multi-powder blending (metallic matrix + ceramic/carbon reinforcement), and the scope explicitly calls out
"tailored reinforcement distributions," powder-metallurgy routes, and AM approaches. A programmable
30-reservoir doser that meters and blends dissimilar powders (with cross-contamination prevented by dedicated per-powder augers and automated auger swapping) is
directly usable MMC feedstock-prep infrastructure. The scope also lists machine learning and
high-throughput methods among its focus areas.

### 3. Symposium 025 — Avoiding Plot Holes: Telling Compelling Stories (with Data)
The genuine wildcard. This Data-Driven-track symposium is about research storytelling and communication
craft — and explicitly welcomes "navigating the brave new world of AI writing assistants." The project's
`DESIGN-LOG.md` chronological design history plus the engineer-led / AI-modeled CAD lessons-learned
narrative (discussion #39) *is* a compelling research story about working with AI tools, with a built-in
arc (AI-generated designs unusable → engineers design, AI models → iterate past hallucinations). If the
generative-AI-CAD abstract doesn't find a technical home, this is an unexpected but legitimate venue for
exactly that story.

### 4. Symposium 070 — Materials and Manufacturing in Space (speculative)
Theme (c) of the scope is "transforming traditional manufacturing technologies so they can be used in
space," where autonomous, human-free operation is a hard requirement. Autonomous powder metering/handling is
an enabling capability for space-based powder AM (with the honest caveat that powder flow physics changes
in microgravity — the doser's tap/vibration/tilt flow-promotion strategy is a gravity-fed design). Only
worth pursuing as a forward-looking framing, not with the current abstract.

### 5. Organizer-network gem: Wenwu Xu (San Diego State University)
Cross-referencing organizers across all 106 flyers, exactly one person co-organizes symposia in **both**
target areas: Wenwu Xu organizes **024 AI-ICME** *and* **075 Powder Materials Processing and Fundamental
Understanding** (plus 028, 065). Submitting the calibration-optimization abstract to 075 (rather than only
the crowded AI symposia) would land ML-calibration content with an organizer who demonstrably values the
AI-for-processing intersection — and 075's scope ("fundamental mechanisms governing powder behavior,"
explicitly welcoming data-science approaches) fits the parameter-sweep / powder-behavior-mapping story.

## Near-misses considered and set aside

- **012 Rapid Acquisition & Processing of Large Datasets** — "autonomous experimental approaches" appears
  in the scope, but the symposium is scoped to *characterization* datasets (SEM/TEM/APT/XCT), not
  synthesis/processing hardware.
- **031 Hume-Rothery Symposium (honoring Chris Wolverton)** — data-driven discovery language, but
  computational/phase-stability focus and honorary-symposium format; the doser is off-scope.
- **061 Circular Metallurgy** — "AI-enhanced recovery networks" and closed-loop language, but the loop is
  material recycling, not experimentation.
- **055 Cold Spray IV** — powder feedstock optimization is on-topic, but the symposium centers on
  deposition/bonding physics rather than upstream powder logistics.
- **032 Mechanistic & Experimental Thermodynamics/Kinetics** — "high-throughput experimental methods"
  appears, but the scope is measurement of thermodynamic/kinetic quantities.

## Bottom line

The earlier top-5 rankings stand. The genuinely new, actionable items are: **(a)** the 105 pitch
competition as a free shot at industry/investor visibility; **(b)** 056 (MMC) as a strong alternate
audience for the powder-dosing abstract; **(c)** 075 with the Wenwu Xu connection as a smarter home for the
calibration-optimization abstract than a third AI symposium; and **(d)** 025 as an off-beat but real venue
for the AI-CAD lessons-learned story.
