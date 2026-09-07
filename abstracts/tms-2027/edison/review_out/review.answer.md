Question: We are preparing a single abstract for the 2027 TMS Annual Meeting & Exhibition (Orlando, FL; March 14-18, 2027; abstract deadline July 1, 2026; body limited to 150 words, submitted via ProgramMaster). We intend to submit to the symposium "Additive Manufacturing and Innovative Feedstock Processing for Multifunctional Materials" (TMS Functional Materials Division; Additive Manufacturing and Magnetic Materials Committees).

Please act as a panel of MOCK PEER REVIEWERS drawn from that symposium's actual ORGANIZING COMMITTEE. Adopt each person's persona and ground your critique in their recent (last ~5-7 years) published literature, which you should search for and cite:
- Daniel Salazar (BCMaterials, Spain) - hard/soft magnets, permanent-magnet and magnetocaloric powders, additive manufacturing of magnetic materials.
- Markus Chmielus (University of Pittsburgh) - binder-jet and powder-bed additive manufacturing, magnetic shape-memory and functional alloys, powder characterization.
- Henry Colorado (Universidad de Antioquia, Colombia) - advanced/functional materials processing, composites, sustainable and additive manufacturing.
- Riccardo Casati (Politecnico di Milano, Italy) - laser powder bed fusion of aluminum and other structural alloys, feedstock powder and process-property relationships.

For each reviewer, look up representative recent work and review our abstract THROUGH THAT LENS, noting what such a reviewer would want to see, whether the work fits this symposium's scope (powder/wire synthesis and feedstock processing, atomization incl. ultrasonic, L-PBF and other AM routes, magnetic/functional/lightweight-structural materials), and where the abstract over- or under-reaches for this audience.

Provide SPECIFIC, ACTIONABLE TEXTUAL SUGGESTIONS: concrete ADDITIONS (sentences or phrases to insert, and where), REMOVALS (text to cut and why), and MODIFICATIONS (rewordings) so we can edit the abstract directly. Because this is a 150-word abstract, every suggestion must respect that hard limit - if you propose an addition, say what to cut to stay <= 150 words. Then give an overall prioritized punch-list and a table of any claims that need stronger evidence or citation. Keep feedback faithful to what the abstract actually claims; do not invent results. Also assess whether this symposium or one of the AI/ML/autonomous-workflow symposia would be the stronger home for this work.

=== TMS 2027 CALL-FOR-ABSTRACTS FLYER (symposium scope + key dates) ===
# TMS 2027 Call for Abstracts — Flyer (extracted text)

Source: https://www.tms.org/tms2027/downloads/flyers/TMS2027-CFA-Flyer-001.pdf
(Local copy: `TMS2027-CFA-Flyer-001.pdf`)

March 14–18, 2027 · Orlando World Center Marriott · Orlando, Florida, USA · www.tms.org/TMS2027

## Symposium: Additive Manufacturing and Innovative Feedstock Processing for Multifunctional Materials

Powder and Wire Metallurgy (PW/M) is a commonplace fabrication and processing method for high
throughput part production in industrial settings. Additionally, PW/M fabrication and processing
advancement also is an essential counterpart to the advancement of additive manufacturing (AM)
with powder-based AM methods. Novel and intensive research is ongoing in innovative, traditional,
and emerging magnetic materials and functional materials; however, the practical application is
limited by the ability to form these typically brittle materials into the shapes that are designed
for the applications. At this time, advanced powder synthesis and processing, including additive
manufacturing, can provide a way to form these materials into final shapes for applications. The
purpose of this symposium is to tie both magnetic and functional materials to advanced powder
synthesis and additive manufacturing, as well as other advanced processing approaches and discuss
aspects such as process-property relationships, functionality, and/or application performance.

Magnetic and functional material systems of interest include:
- Soft magnets (nano-crystalline alloys, high Si-steel)
- Hard magnets (Nd-Fe-B, Sm-Co, MnAlC, MnBi, alnico, ferrite, exchange-coupled)
- Magnetocaloric materials (Gd-Si-Ge, Gd-Ni-X, RE-RE, RE-Al)
- Magnetic Shape Memory Alloys (Ni-Mn-Ga(-X))
- Shape Memory Alloys (NiTi(X), Fe-based, Cu-based)
- Magnetostrictive materials (Terfenol-D, Ga-Fe, Gd-Co)
- Thermoelectric Materials (Si-Ge, Bi-Te)
- Lightweight Structural Materials

Topics of interest for clean powder and wire synthesis include, but are not limited to:
- Atomization (water, gas, rotational, ultrasonic, plasma)
- Mechanical comminution (multi-jet or single jet milling, high energy ball milling)
- Extrusion of metals and composites
- And other powder and wire synthesis approaches

Topics of interest for advanced powder processing of magnetic/functional materials include, but are
not limited to: i) additive manufacturing (binder jet, directed energy deposition (DED), colloidal
deposition, electron beam melting powder bed fusion (EBM/PBF), laser/powder bed fusion (L-PBF),
fused filament fabrication (FFF), Wire Arc Additive Manufacturing (WAAM), atmospheric pressure
plasma deposition (APPD) and stereolithography), ii) metal injection and compression molding,
iii) spark plasma sintering, iv) vacuum hot pressing, v) Functional post-processing (directional
recrystallization, magnetic annealing (large or moderate magnetic fields)).

Division sponsor: TMS Functional Materials Division
Committee sponsors: TMS Additive Manufacturing Committee; TMS Magnetic Materials Committee

## Organizing Committee (used as mock reviewer personas)
- Daniel Salazar, BCMaterials
- Markus Chmielus, University of Pittsburgh
- Henry Colorado, Universidad de Antioquia
- Riccardo Casati, Politecnico Di Milano

## Key Dates
- July 1, 2026: Abstract Submissions Due
- October 2026: Registration Opens
- January 31, 2027: Discount Registration Deadline

Questions: programming@tms.org


=== ABSTRACT UNDER REVIEW (150-word body) ===
Title: An Open-Source, Low-Cost Powder Doser for Autonomous Metal-Alloy Discovery

---
Meeting: TMS 2027 Annual Meeting & Exhibition (Orlando, FL)
Dates: March 14–18, 2027 (Orlando World Center Marriott)
Submission deadline: July 1, 2026
Format: abstract body limited to 150 words; submitted via ProgramMaster
(https://www.programmaster.org/TMS2027); title and body in Title/sentence case.
Target symposium (best-fit ranking; rationale in README.md):
  1. AI-Enabled Materials Processing: Integrating Accelerated Experimental
     Workflows and Processing-Aware Machine Learning
     (Data-Driven and Computational Materials Design track) — primary
  2. Additive Manufacturing and Innovative Feedstock Processing for
     Multifunctional Materials (Additive Manufacturing track) — alternate
  3. AI/ML/Data Informatics for Materials Discovery: Bridging Experiment,
     Theory, and Modeling (Data-Driven and Computational Materials Design
     track) — alternate
  Submit the abstract to only one symposium.
---

Title: An Open-Source, Low-Cost Powder Doser for Autonomous Metal-Alloy Discovery

Additive manufacturing of aerospace alloys requires rapid, reproducible exploration of powder feedstocks, yet accurately metering and blending dry metal powders remains a manual bottleneck. Commercial dispensers are costly and poorly suited to alloy-development workflows with many powders and frequent recipe changes, and existing open-source designs have not been rigorously tested for laser powder bed fusion (L-PBF). We present an open-source, low-cost, modular powder doser for gravimetric metering of metal feedstocks, designed for integration into a self-driving, Bayesian-optimization alloy-discovery loop feeding ultrasonic atomization and L-PBF. A stepper-driven Archimedean auger with solenoid tapping, vibration-motor agitation, and servo-controlled tilt accommodates diverse powders; proposal targets include up to 30 reservoirs, blends up to 250 mL, and per-powder accuracy of ±1 mg (±0.1 mg stretch) with cross-contamination characterization. Testing progresses from non-hazardous powders to L-PBF feedstocks (AlSi10Mg, silicon, stainless steel). We also report a practitioner-level assessment of agentic-AI and generative-CAD tools for engineer-led instrument design.



# Mock Peer Review of "An Open-Source, Low-Cost Powder Doser for Autonomous Metal-Alloy Discovery"

## Submitted to: Additive Manufacturing and Innovative Feedstock Processing for Multifunctional Materials (TMS 2027)

The following provides four mock reviewer critiques grounded in each organizing committee member's recent published work, followed by specific textual suggestions, a prioritized punch-list, a claims-evidence table, and a symposium-fit assessment.

---

## Reviewer 1: Daniel Salazar (BCMaterials, Spain)

**Research lens.** Salazar's recent work centers on additive manufacturing of magnetocaloric and magnetic shape-memory materials. He has co-authored studies on binder-jet 3D printing of Ni-Mn-Cu-Ga alloys with Chmielus, demonstrating a 1.2 K hysteresis for martensitic para-ferromagnetic partial transformation (Stevens, Salazar et al., *Additive Manufacturing* 2021). He has also published on NiCoMnSn metamagnetic shape-memory ribbon powders, examining how atomic ordering and microstructural features control magnetocaloric performance (Rodríguez-Crespo, Salazar et al., *Materials & Design* 2024), and on sustainable permanent magnets (Salazar et al., ACS Books 2025).

**Critique.**

*Scope fit:* This symposium was designed specifically to bridge magnetic/functional materials with advanced powder synthesis and AM. The abstract describes a powder doser tested with AlSi10Mg, silicon, and stainless steel—none of which are magnetic or functional materials in the symposium's sense. As an organizer who works on Ni-Mn-Ga and NiCoMnSn systems, I would want to see at least a stated plan to handle the specific challenges of these brittle, oxidation-sensitive, and compositionally complex powders. Magnetic materials like MnAlC or Ni-Mn-Ga are notoriously difficult to handle due to their sensitivity to atmosphere and particle morphology.

*What I would want to see:* (1) Explicit mention of magnetic or functional feedstocks as target materials. (2) Discussion of whether the doser's auger mechanism can handle the irregular morphologies typical of melt-spun and mechanically comminuted magnetic powders, which differ substantially from gas-atomized spherical powders. (3) Any evidence that the ±1 mg accuracy specification is meaningful for compositionally sensitive magnetic alloys where a fraction of a weight-percent shift can alter transformation temperatures.

*Over-reach:* The "self-driving, Bayesian-optimization alloy-discovery loop feeding ultrasonic atomization and L-PBF" claim is a full pipeline that most groups spend years developing. Without any demonstrated closure of this loop, this reads as vision, not contribution.

*Under-reach:* No materials science result is presented. The abstract is a hardware description with aspirational specifications.

**Specific textual suggestions:**

- **ADDITION (after "stainless steel"):** Insert ", with planned extension to magnetic feedstocks (e.g., Ni-Mn-Ga, MnAlC)." To compensate, **REMOVE** "Commercial dispensers are costly and" from sentence 2 (saves ~5 words).

- **MODIFICATION:** Change "Additive manufacturing of aerospace alloys" → "Additive manufacturing of functional and structural alloys" to broaden scope alignment.

---

## Reviewer 2: Markus Chmielus (University of Pittsburgh)

**Research lens.** Chmielus has published extensively on binder-jet 3D printing of Ni-Mn-Ga magnetic shape-memory alloys, examining how powder size distribution affects green density, sintering densification, and microstructural evolution (mostafaei2019effectofpowder pages 10-13). His work on L-PBF of Ni-Mn-Ga demonstrated that gas-atomized powder with excess Mn doping can achieve ~98.4% relative density, but that atomic disorder and quenched-in stress from L-PBF fundamentally alter functional properties (laitinen2021characterizationofasbuilt pages 9-10, laitinen2021characterizationofasbuilt pages 1-2). His powder characterization work shows that particle size, packing defects, and shrinkage uniformity are critical to final part quality (mostafaei2019effectofpowder pages 10-13).

**Critique.**

*Powder characterization gap:* My biggest concern is that the abstract focuses on mass accuracy (±1 mg) but says nothing about the powder-quality metrics that actually govern AM processability. In my work on Alloy 625, we showed that powder size distribution directly controls green density (45–52%), shrinkage uniformity, and final porosity (mostafaei2019effectofpowder pages 10-13). For any powder doser targeting L-PBF feedstock preparation, the critical question is not just "did you dispense the right mass?" but "did you preserve powder flowability, particle size distribution, and morphology during handling?" Cross-contamination is mentioned but not operationalized—what analytes, what thresholds, what cleaning protocol?

*What I would want to see:* (1) Powder characterization metrics: PSD, flowability (e.g., avalanche angle or Hall flow), morphology assessment before and after dosing. (2) Evidence that the auger/tapping/vibration mechanism does not damage or segregate particles. (3) Connection to how blended feedstocks will be validated for AM suitability—not just mass accuracy.

*Scope concern:* The abstract's emphasis on Bayesian optimization and autonomous discovery places it closer to an AI/ML symposium. For this symposium, I'd want the focus squarely on the feedstock-processing innovation and its implications for powder quality.

**Specific textual suggestions:**

- **ADDITION (after the accuracy specification):** Insert "Dosing performance is benchmarked against powder size distribution, flowability, and morphology retention." **REMOVE** the entire last sentence ("We also report a practitioner-level assessment of agentic-AI and generative-CAD tools for engineer-led instrument design") to create word budget (~15 words freed). This last sentence is off-topic for this symposium.

- **MODIFICATION:** Change "proposal targets include" → "Current prototype demonstrates [X]; scaling targets include" to distinguish achieved from aspirational results.

---

## Reviewer 3: Henry Colorado (Universidad de Antioquia, Colombia)

**Research lens.** Colorado's recent work spans additive manufacturing of nanocomposites via vat photopolymerization, sustainable 3D printing with waste-derived feedstocks, and functional composites for defense and construction applications (colorado2024exploringtheadvantages pages 15-15, colorado2024exploringtheadvantages pages 14-15). His research emphasizes accessibility, sustainability, multidisciplinary AM applications, and the circular economy of materials.

**Critique.**

*Open-source and accessibility angle:* I appreciate the open-source, low-cost framing—this aligns with my interest in making AM technologies accessible across different research contexts. The modular design philosophy is commendable. However, the abstract should be more explicit about what "low-cost" means quantitatively (a BOM estimate or comparison to commercial systems), and whether the design files will truly be published openly with sufficient documentation for reproduction.

*Sustainability and broader impact:* The abstract misses an opportunity to connect to sustainability themes. Powder waste in AM is a real concern—any dosing system that reduces material waste during feedstock preparation or enables use of recycled/reclaimed powders has environmental relevance. A brief mention would strengthen the abstract for a broader AM audience.

*Multifunctional materials gap:* The symposium title emphasizes "multifunctional materials," yet the abstract presents a general-purpose dispenser. Even a brief mention of how the system could serve composite feedstock preparation (e.g., metal-ceramic blends) or functional-material powder mixing would improve fit.

*Under-specified contribution:* Is the contribution hardware design, dosing performance data, or workflow architecture? The abstract tries to claim all three plus an AI-tools assessment, which is too diffuse for 150 words.

**Specific textual suggestions:**

- **MODIFICATION:** Change "open-source, low-cost, modular powder doser" → "open-source, low-cost (~$X) modular powder doser" if a cost figure is available, or add "with full design files released" to substantiate the open-source claim.

- **REMOVAL:** Remove "We also report a practitioner-level assessment of agentic-AI and generative-CAD tools for engineer-led instrument design." This is a separate contribution and dilutes the already-tight 150 words.

---

## Reviewer 4: Riccardo Casati (Politecnico di Milano, Italy)

**Research lens.** Casati's work focuses on L-PBF process-property relationships and feedstock powder quality. His study on AlSi10Mg powder aging demonstrated that oxygen pick-up during handling causes 4× increase in oxygen content, leading to porosity rising from 3.16% to 6.5% and significant degradation in tensile strength (fedina2022influenceofalsi10mg pages 1-2, fedina2022influenceofalsi10mg pages 10-11). He has also published on powder atomization route effects on steel properties, TiB2-reinforced Al-2618 alloys for L-PBF, and novel alloy development through modified powder compositions (lupi2025microstructureandtensile pages 12-13).

**Critique.**

*Powder degradation during handling—the elephant in the room:* My central concern is that the abstract describes a multi-powder metering and blending system but says nothing about atmosphere control, oxidation mitigation, or moisture management. In my work on AlSi10Mg, we showed that even storage and handling introduce oxygen that fundamentally degrades L-PBF processability—aged powder produced parts with nearly double the porosity (fedina2022influenceofalsi10mg pages 1-2). An open-air auger-based dosing system repeatedly exposing metal powders to atmosphere, vibration, and mechanical contact raises serious powder-quality concerns that must be addressed. Is there inert-gas blanketing? What is the exposure time per dose cycle?

*AlSi10Mg is a good test case but needs rigor:* I note the abstract plans to test AlSi10Mg. This is excellent because it is well-characterized in the literature. However, the abstract should state what powder-quality metrics will be assessed post-dosing. Simple mass accuracy is insufficient if the dosing process introduces oxidation, particle damage, or size-fraction segregation that compromises L-PBF outcomes.

*Process-property linkage missing:* This symposium explicitly calls for "process-property relationships." The abstract describes a process (dosing) but makes no connection to downstream part properties. Even a plan to correlate dosed-blend homogeneity with L-PBF single-track or coupon quality would strengthen the submission.

*Accuracy specification concerns:* The ±1 mg target is stated without context. For what powder mass? ±1 mg of a 100 mg dose is 1%, which is significant; ±1 mg of a 10 g dose is 0.01%, which may be unnecessarily precise. The specification needs to be stated relative to dose size and compared to what commercial systems or manual methods achieve.

**Specific textual suggestions:**

- **ADDITION (after "diverse powders"):** Insert "under controlled atmosphere to limit oxidation during handling." **REMOVE** "and existing open-source designs have not been rigorously tested for laser powder bed fusion (L-PBF)" to create space (~14 words freed).

- **MODIFICATION:** Change "per-powder accuracy of ±1 mg" → "per-powder accuracy of ±1 mg at [dose size] doses" to contextualize the specification.

- **MODIFICATION:** Change "Testing progresses from non-hazardous powders to L-PBF feedstocks" → "Testing progresses from surrogate to L-PBF feedstocks, with post-dosing powder-quality assessment" to signal awareness of feedstock degradation.

---

## Prioritized Revision Punch-List

The following table ranks the most impactful edits for improving the abstract's fit with this symposium while respecting the 150-word limit:

| Priority | Action (specific edit) | Type (Add/Remove/Modify) | Rationale | Word-Budget Impact |
|---|---|---|---|---|
| 1 | Remove the final sentence: "We also report a practitioner-level assessment of agentic-AI and generative-CAD tools for engineer-led instrument design." | Remove | Off-topic for this symposium; frees space for feedstock/process content more aligned with AM and powder-processing audiences. | -15 |
| 2 | Add an explicit link to functional/magnetic materials, e.g., "with planned extension to magnetic feedstocks (e.g., Ni-Mn-Ga, MnAlC)." | Add | The symposium centers on magnetic/functional materials; the current abstract names only AlSi10Mg, silicon, and stainless steel. This edit improves scope fit. | +10 |
| 3 | Replace "Additive manufacturing of aerospace alloys requires" with "Additive manufacturing and feedstock development for metal-alloy powders require" or "Rapid exploration of metal-alloy powder feedstocks requires". | Modify | "Aerospace alloys" is too narrow for this symposium, which spans magnetic, functional, and lightweight structural materials. | 0 |
| 4 | Add one short sentence on powder metrics to be reported, e.g., "Performance will be benchmarked across powder size distribution, flowability, and particle morphology." | Add | Powder characterization is central to reviewer expectations in binder-jet/L-PBF and feedstock literature; powder quality strongly affects processability and part quality (mostafaei2019effectofpowder pages 10-13, fedina2022influenceofalsi10mg pages 1-2, zrodowski2021novelcoldcrucible pages 1-3). | +8 |
| 5 | Change "proposal targets include" to clearly separate present results from future goals, e.g., "Current results establish gravimetric dosing repeatability; planned scaling targets include..." | Modify | The abstract currently blurs demonstrated achievements and aspirational specifications; reviewers will want a clean completed-vs-planned distinction. | 0 |
| 6 | Remove or compress "Commercial dispensers are costly and" from the problem statement. | Remove | Too much background for a 150-word abstract; the audience already understands instrumentation constraints, and the saved words can support evidence-bearing technical content. | -5 |
| 7 | Specify the ultrasonic atomization role in the workflow, e.g., "for blended precursor charges that will be re-melted for ultrasonic atomization before L-PBF evaluation." | Modify | Ultrasonic atomization is a named symposium topic; the current abstract only mentions it without explaining how the doser interfaces with that stage (sojoodi2025integrationofcircular pages 2-3, bałasz2024aninvestigationof pages 2-4). | +5 |
| 8 | Modify the title to foreground feedstock processing, e.g., "An Open-Source Powder Doser for Autonomous Metal Feedstock Development" or "...for Autonomous Feedstock Blending and Alloy Discovery." | Modify | Better alignment with the symposium emphasis on innovative feedstock processing and AM process-property relationships. | 0 |


*Table: This table gives the highest-value edits to improve fit with the TMS multifunctional-materials/feedstock symposium while staying within the 150-word abstract limit. It also highlights where reviewer expectations from powder characterization and feedstock-processing literature are most likely to affect reception.*

## Claims Requiring Stronger Evidence or Citation

The following table identifies claims in the abstract that reviewers would flag as needing substantiation:

| Claim (quote from abstract) | Issue (what's problematic) | Recommendation (what to do) |
|---|---|---|
| "per-powder accuracy of ±1 mg (±0.1 mg stretch)" | Very aggressive specification for dry metal-powder dispensing, but the abstract gives neither benchmark data nor prior-art comparison; for this symposium, reviewers focused on powder/process rigor will expect evidence that such precision is meaningful across different powders and not just an aspirational design target (mostafaei2019effectofpowder pages 10-13, fedina2022influenceofalsi10mg pages 1-2, zrodowski2021novelcoldcrucible pages 1-3). | If demonstrated, replace with measured performance on named powders and number of trials; if not yet demonstrated, recast as "design target" and cut the stretch goal. Add one metric tied to relevance, e.g., mass error across AlSi10Mg or 316L dosing runs. |
| "Commercial dispensers are costly and poorly suited to alloy-development workflows" | "Costly" and "poorly suited" are broad market claims with no evidence, no examples, and no criteria for suitability. In a 150-word abstract, unsupported comparative claims read as sales language rather than technical framing. | Replace with a narrower, defensible statement such as "Commercial dispensers may limit rapid recipe changes and multi-powder screening" or cite a specific workflow limitation (changeover time, number of reservoirs, cleanout burden). |
| "existing open-source designs have not been rigorously tested for laser powder bed fusion (L-PBF)" | The claim identifies a literature gap but cites no designs, no review basis, and no definition of "rigorously tested." Reviewers may ask: which systems, tested how, and against what L-PBF-relevant criteria? | Name the comparison class briefly (e.g., hobbyist auger/vibratory powder feeders) or soften to "to our knowledge, open-source powder dosers remain sparsely validated for L-PBF feedstocks." |
| "proposal targets include up to 30 reservoirs, blends up to 250 mL" | This is clearly proposal-level capability, not presented as demonstrated hardware performance. The abstract currently blurs completed work and planned scale-up, which weakens credibility (adapa2025rapiddevelopmentof pages 1-2, xie2025anoverviewof pages 11-12). | Separate achieved versus planned: e.g., "current prototype supports X reservoirs; planned expansion targets 30 reservoirs and 250 mL blends." If no demonstrated value is available, remove one of the two targets. |
| "with cross-contamination characterization" | Important claim for powder-feedstock work, but no method, analyte, threshold, or cleaning protocol is stated. For AM feedstocks, contamination can affect oxidation, flowability, and part quality, so reviewers will want at least a hint of the metric (fedina2022influenceofalsi10mg pages 1-2, fedina2022influenceofalsi10mg pages 12-12). | Add a short method phrase such as "cross-contamination will be quantified by tracer or composition analysis after reservoir changeover"; if space is tight, replace the phrase with one threshold-based clause. |
| "We also report a practitioner-level assessment of agentic-AI and generative-CAD tools for engineer-led instrument design." | This reads as a second paper embedded in the abstract. It is not obviously a feedstock-processing, powder-metallurgy, or AM process-property contribution, and no evidence is given that it advances materials science for this audience (colorado2024exploringtheadvantages pages 15-15, colorado2024exploringtheadvantages pages 14-15). | Remove this sentence for this symposium, or move it to a separate AI/ML/autonomous-workflow submission where tool-assessment methodology is central. |
| "designed for integration into a self-driving, Bayesian-optimization alloy-discovery loop feeding ultrasonic atomization and L-PBF" | Ambitious end-to-end workflow claim spanning dosing, autonomous experimentation, atomization, and printing, but the abstract does not distinguish what is already integrated from what is future architecture. This overreach is especially noticeable because autonomous AM loops are substantial contributions on their own (sojoodi2025integrationofcircular pages 2-3, adapa2025rapiddevelopmentof pages 1-2, adapa2025rapiddevelopmentof pages 18-19). | Recast to current scope: "designed for future integration into a Bayesian-optimization workflow for powder-feedstock screening prior to ultrasonic atomization and L-PBF." Only claim closed-loop autonomy if already demonstrated. |


*Table: This table identifies the abstract's most vulnerable claims from a mock-review standpoint and explains how to revise each one to sound evidence-based and symposium-appropriate. It is useful for tightening the 150-word abstract before submission.*

## Symposium Fit Assessment

The abstract's authors correctly identified this symposium as their secondary target. The following comparison confirms that assessment:

| Criterion | AM & Innovative Feedstock Processing for Multifunctional Materials | AI-Enabled Materials Processing | AI/ML/Data Informatics for Materials Discovery |
|---|---|---|---|
| Core topic match | Moderate: powder dosing hardware is feedstock-adjacent, but the abstract does not yet present a materials or process-property result; fit improves only if powder characterization and feedstock-processing data are foregrounded (fedina2022influenceofalsi10mg pages 1-2, zrodowski2021novelcoldcrucible pages 1-3) | Strong: the abstract centers on autonomous workflow integration, Bayesian optimization, and instrument automation, which align directly with AI-enabled processing themes (adapa2025rapiddevelopmentof pages 1-2, adapa2025rapiddevelopmentof pages 18-19) | Moderate: the discovery framing fits, but no actual ML model, data-informatics result, or closed-loop learning outcome is shown yet (adapa2025rapiddevelopmentof pages 1-2, adapa2025rapiddevelopmentof pages 18-19) |
| Materials results expected | Yes: this audience will expect powder/part characterization, feedstock–process–property relationships, or functionality/applications data (fedina2022influenceofalsi10mg pages 1-2, zrodowski2021novelcoldcrucible pages 1-3) | Accepts tool/workflow contributions: autonomous experimentation infrastructure and workflow-enabling hardware are credible contributions even before full materials optimization results (adapa2025rapiddevelopmentof pages 1-2, adapa2025rapiddevelopmentof pages 18-19) | Expects data/model outputs: stronger fit if the submission reports informatics, surrogate modeling, active learning performance, or decision logic beyond hardware description (adapa2025rapiddevelopmentof pages 1-2, adapa2025rapiddevelopmentof pages 18-19) |
| Audience interest in open-source hardware | Moderate: useful if tightly connected to powder handling, contamination control, and AM feedstock validation | High: autonomous-lab and accelerated-workflow audiences typically value modular, open, reproducible hardware platforms (adapa2025rapiddevelopmentof pages 1-2, adapa2025rapiddevelopmentof pages 18-19) | Moderate: interest exists, but usually as enabling infrastructure for data generation rather than the main contribution |
| Audience interest in Bayesian optimization / self-driving labs | Low-moderate: relevant, but secondary to feedstock synthesis, powder processing, and AM process/property content | High: this is a central attraction for the symposium (adapa2025rapiddevelopmentof pages 1-2, adapa2025rapiddevelopmentof pages 18-19) | High: strong interest if accompanied by actual learning, optimization, or informatics results (adapa2025rapiddevelopmentof pages 1-2, adapa2025rapiddevelopmentof pages 18-19) |
| Audience interest in powder characterization (PSD, flowability, contamination) | Very high: this is one of the clearest ways to make the abstract belong here (mostafaei2019effectofpowder pages 10-13, fedina2022influenceofalsi10mg pages 1-2, bałasz2024aninvestigationof pages 4-7, zrodowski2021novelcoldcrucible pages 1-3) | Moderate: useful supporting detail, but not necessarily the headline contribution | Low: usually peripheral unless linked to a data/modeling framework |
| Risk of scope mismatch | High: current abstract lacks magnetic/functional-material data, and does not yet show process-property relationships or powder-quality results expected by this audience (fedina2022influenceofalsi10mg pages 1-2, fedina2022influenceofalsi10mg pages 12-12) | Low: as written, the abstract already reads like an autonomous experimentation/instrumentation paper (adapa2025rapiddevelopmentof pages 1-2, adapa2025rapiddevelopmentof pages 18-19) | Moderate: scope is plausible, but absence of explicit ML outputs weakens the match |
| Overall recommendation | Submit only if revised to emphasize feedstock characterization, contamination control, L-PBF-relevant powder metrics, and ideally extension to magnetic/functional feedstocks | BEST FIT as currently written | Acceptable alternate if you foreground discovery workflow logic and planned/actual data use |
| Verdict | Viable only with substantial reframing toward powder characterization results and magnetic-material applicability | Strongest home for the present abstract | Secondary option, but weaker than AI-Enabled without clearer informatics results |


*Table: This table compares how well the current abstract fits the three candidate TMS 2027 symposia. It is useful for deciding whether to keep the feedstock symposium as a target or shift to the more natural AI-enabled processing venue.*

## Overall Assessment and Recommendation

**Symposium selection.** The "AI-Enabled Materials Processing: Integrating Accelerated Experimental Workflows and Processing-Aware Machine Learning" symposium is the stronger home for this abstract as currently written. The abstract's core contribution—an open-source instrument for autonomous alloy-discovery workflows—is fundamentally a workflow-enabling hardware paper, not a materials or process-property paper (adapa2025rapiddevelopmentof pages 1-2, adapa2025rapiddevelopmentof pages 18-19). The AI-Enabled symposium audience would value the Bayesian optimization integration, open-source philosophy, and instrument-automation aspects that are central to the abstract but peripheral to the feedstock symposium's focus.

**If submitting to the feedstock symposium regardless,** the abstract requires substantial reframing. The four reviewers converge on these critical gaps: (1) no magnetic or functional materials are tested or even planned, creating a fundamental scope mismatch with a symposium sponsored by the TMS Magnetic Materials Committee; (2) no powder characterization results (PSD, flowability, morphology, oxidation) are reported, despite this being central to the symposium's purpose (mostafaei2019effectofpowder pages 10-13, fedina2022influenceofalsi10mg pages 1-2, zrodowski2021novelcoldcrucible pages 1-3); (3) the agentic-AI/generative-CAD assessment sentence is off-topic and should be removed to recover word budget; and (4) the accuracy specification (±1 mg) is decontextualized—it needs to be linked to dose size and to downstream powder-quality or AM-property relevance.

**The abstract can be made viable for this symposium** by implementing the top 4–5 items in the punch-list: removing the AI-tools sentence, adding magnetic/functional material targets, broadening the "aerospace alloys" framing, adding powder-characterization metrics, and clarifying demonstrated vs. planned capabilities. These changes would shift the abstract's emphasis from "autonomous discovery instrument" to "innovative feedstock-processing tool for functional-material powder development," which is squarely within scope.

References

1. (mostafaei2019effectofpowder pages 10-13): Amir Mostafaei, Pierangeli Rodriguez De Vecchis, Ian Nettleship, and Markus Chmielus. Effect of powder size distribution on densification and microstructural evolution of binder-jet 3d-printed alloy 625. Materials & Design, 162:375-383, Jan 2019. URL: https://doi.org/10.1016/j.matdes.2018.11.051, doi:10.1016/j.matdes.2018.11.051. This article has 270 citations and is from a highest quality peer-reviewed journal.

2. (laitinen2021characterizationofasbuilt pages 9-10): Ville Laitinen, Alexei Sozinov, Andrey Saren, Markus Chmielus, and Kari Ullakko. Characterization of as-built and heat-treated ni-mn-ga magnetic shape memory alloy manufactured via laser powder bed fusion. Additive manufacturing, 39:101854, Mar 2021. URL: https://doi.org/10.1016/j.addma.2021.101854, doi:10.1016/j.addma.2021.101854. This article has 54 citations and is from a highest quality peer-reviewed journal.

3. (laitinen2021characterizationofasbuilt pages 1-2): Ville Laitinen, Alexei Sozinov, Andrey Saren, Markus Chmielus, and Kari Ullakko. Characterization of as-built and heat-treated ni-mn-ga magnetic shape memory alloy manufactured via laser powder bed fusion. Additive manufacturing, 39:101854, Mar 2021. URL: https://doi.org/10.1016/j.addma.2021.101854, doi:10.1016/j.addma.2021.101854. This article has 54 citations and is from a highest quality peer-reviewed journal.

4. (colorado2024exploringtheadvantages pages 15-15): Henry A. Colorado, Elkin I. Gutierrez-Velasquez, León D. Gil, and Italo Leite de Camargo. Exploring the advantages and applications of nanocomposites produced via vat photopolymerization in additive manufacturing: a review. Advanced Composites and Hybrid Materials, Dec 2024. URL: https://doi.org/10.1007/s42114-023-00808-z, doi:10.1007/s42114-023-00808-z. This article has 133 citations and is from a peer-reviewed journal.

5. (colorado2024exploringtheadvantages pages 14-15): Henry A. Colorado, Elkin I. Gutierrez-Velasquez, León D. Gil, and Italo Leite de Camargo. Exploring the advantages and applications of nanocomposites produced via vat photopolymerization in additive manufacturing: a review. Advanced Composites and Hybrid Materials, Dec 2024. URL: https://doi.org/10.1007/s42114-023-00808-z, doi:10.1007/s42114-023-00808-z. This article has 133 citations and is from a peer-reviewed journal.

6. (fedina2022influenceofalsi10mg pages 1-2): Tatiana Fedina, Filippo Belelli, Giorgia Lupi, Benedikt Brandau, Riccardo Casati, Raphael Berneth, Frank Brueckner, and Alexander F.H. Kaplan. Influence of alsi10mg powder aging on the material degradation and its processing in laser powder bed fusion. Nov 2022. URL: https://doi.org/10.1016/j.powtec.2022.118024, doi:10.1016/j.powtec.2022.118024. This article has 25 citations and is from a domain leading peer-reviewed journal.

7. (fedina2022influenceofalsi10mg pages 10-11): Tatiana Fedina, Filippo Belelli, Giorgia Lupi, Benedikt Brandau, Riccardo Casati, Raphael Berneth, Frank Brueckner, and Alexander F.H. Kaplan. Influence of alsi10mg powder aging on the material degradation and its processing in laser powder bed fusion. Nov 2022. URL: https://doi.org/10.1016/j.powtec.2022.118024, doi:10.1016/j.powtec.2022.118024. This article has 25 citations and is from a domain leading peer-reviewed journal.

8. (lupi2025microstructureandtensile pages 12-13): G. Lupi, L. Mariotti, A. Mistrini, J. Larsson, L. Patriarca, and R. Casati. Microstructure and tensile properties of tib2-reinforced al-2618 thin walls produced by laser powder bed fusion. Materials Characterization, 228:115372, Oct 2025. URL: https://doi.org/10.1016/j.matchar.2025.115372, doi:10.1016/j.matchar.2025.115372. This article has 5 citations and is from a peer-reviewed journal.

9. (zrodowski2021novelcoldcrucible pages 1-3): Łukasz Żrodowski, Rafał Wróblewski, Tomasz Choma, Bartosz Morończyk, Mateusz Ostrysz, Marcin Leonowicz, Wojciech Łacisz, Piotr Błyskun, Jan S. Wróbel, Grzegorz Cieślak, Bartłomiej Wysocki, Cezary Żrodowski, and Karolina Pomian. Novel cold crucible ultrasonic atomization powder production method for 3d printing. Materials, 14:2541, May 2021. URL: https://doi.org/10.3390/ma14102541, doi:10.3390/ma14102541. This article has 63 citations.

10. (sojoodi2025integrationofcircular pages 2-3): Mahyar Sojoodi, Alireza Behvar, Harsh Bajaj, Shiva Mohajerani, Saeedeh Vanaei, Nasrin Taheri Andani, Anwar Algamal, Fatemeh Ghasemibojd, Mahsa Beyk Khorasani, Ahu Celebi, and Mohammad Elahinia. Integration of circular economy into metal additive manufacturing: a review of ultrasonic plasma atomization for producing virgin and recycled niti powder. Shape Memory and Superelasticity, 12:5-45, Oct 2025. URL: https://doi.org/10.1007/s40830-025-00589-y, doi:10.1007/s40830-025-00589-y. This article has 2 citations.

11. (bałasz2024aninvestigationof pages 2-4): Błażej Bałasz, Łukasz Żurawski, Dorota Laskowska, Nataliya Muts, and Andriana Ivanushko. An investigation of the metal powder ultrasound atomisation process of 316l stainless steel. Materials, 17:5642, Nov 2024. URL: https://doi.org/10.3390/ma17225642, doi:10.3390/ma17225642. This article has 7 citations.

12. (adapa2025rapiddevelopmentof pages 1-2): Venkata Surya Karthik Adapa, Surya R. Kalidindi, and Christopher J. Saldana. Rapid development of metal additive manufacturing using artificial intelligence/machine learning and high-throughput material testing. Jul 2025. URL: https://doi.org/10.1146/annurev-matsci-080423-121436, doi:10.1146/annurev-matsci-080423-121436. This article has 14 citations and is from a domain leading peer-reviewed journal.

13. (xie2025anoverviewof pages 11-12): Tong Xie, Weidong Li, Gihan Velisa, Shuying Chen, Fanchao Meng, Peter K. Liaw, and Yang Tong. An overview of high‐throughput synthesis for advanced high‐entropy alloys. Materials Genome Engineering Advances, Feb 2025. URL: https://doi.org/10.1002/mgea.87, doi:10.1002/mgea.87. This article has 15 citations.

14. (fedina2022influenceofalsi10mg pages 12-12): Tatiana Fedina, Filippo Belelli, Giorgia Lupi, Benedikt Brandau, Riccardo Casati, Raphael Berneth, Frank Brueckner, and Alexander F.H. Kaplan. Influence of alsi10mg powder aging on the material degradation and its processing in laser powder bed fusion. Nov 2022. URL: https://doi.org/10.1016/j.powtec.2022.118024, doi:10.1016/j.powtec.2022.118024. This article has 25 citations and is from a domain leading peer-reviewed journal.

15. (adapa2025rapiddevelopmentof pages 18-19): Venkata Surya Karthik Adapa, Surya R. Kalidindi, and Christopher J. Saldana. Rapid development of metal additive manufacturing using artificial intelligence/machine learning and high-throughput material testing. Jul 2025. URL: https://doi.org/10.1146/annurev-matsci-080423-121436, doi:10.1146/annurev-matsci-080423-121436. This article has 14 citations and is from a domain leading peer-reviewed journal.

16. (bałasz2024aninvestigationof pages 4-7): Błażej Bałasz, Łukasz Żurawski, Dorota Laskowska, Nataliya Muts, and Andriana Ivanushko. An investigation of the metal powder ultrasound atomisation process of 316l stainless steel. Materials, 17:5642, Nov 2024. URL: https://doi.org/10.3390/ma17225642, doi:10.3390/ma17225642. This article has 7 citations.