Question: ## System context

We are designing a **multi-doser carousel** for an open-source autonomous
powder-dosing instrument (metal powders for laser powder-bed fusion, plus
organic/ceramic powders; particles tens of microns, cohesive, hygroscopic,
sometimes triboelectrically charged).

Each *dosing module* is a cylindrical cartridge holding a powder reservoir and
an Archimedes auger. The auger tube ends in a small **dispensing outlet
(nozzle) on the cylindrical side or front face of the module**, roughly 5-15 mm
across. Modules are carried on a **roller-chain carousel** (steel roller chain
with custom 3D-printed carrier links). A robotic arm picks a module off the
chain, mounts it to a dosing station (stepper drives the auger; a solenoid taps
it; a servo tilts it), then returns it to the chain.

## The specific problem

Because each module simply hangs/sits on a chain carrier, **we cannot guarantee
its rotational orientation about its own long axis**. When the module returns to
the carousel it may be at any clock angle. We want a **front cap / closure over
the dispensing outlet** that:

1. Keeps powder in (and, ideally, air/moisture out) while the module sits in
   storage on the carousel, possibly for days.
2. Opens automatically when the module is docked at the dosing station, and
   re-closes automatically when it is undocked -- **with no electrical
   connection, no wiring, and no dedicated actuator on the module itself**
   (the module is a passive, hot-swappable consumable).
3. Is **insensitive to the module's rotational orientation**: the opening
   action must work when the module is approached/engaged from an arbitrary
   clock angle, OR the mechanism must self-index the module to a known angle
   during docking.
4. Is manufacturable by FDM/SLA 3D printing plus stock springs/O-rings, and
   does not shed particulates or trap powder in a way that causes
   cross-contamination between powders.

One idea already on the table: a **spring-loaded iris/aperture diaphragm with a
ratchet**, so continued rotation in one direction opens it and reversing
slightly lets it snap closed.

## What we want from you

Focus on the **powder-science and engineering evidence** relevant to choosing
among these closures:

1. What does the literature say about **powder leakage, rat-holing and flooding
   at auger/screw-feeder outlets** when the outlet is unsealed vs. sealed, and
   about "flushing"/uncontrolled discharge of aerated fine powders on
   uncapping?
2. Evidence on **contamination and particle shedding from sliding/rubbing
   closures** (iris blades, sliding shutters) with fine metal powders --
   including galling, wear debris, and powder ingress into mechanism clearances.
3. What sealing performance (moisture ingress, oxygen ingress) is actually
   achievable with **elastomeric self-closing valves (duckbill, slit septa,
   umbrella)** versus rigid caps with O-rings, and how does that compare to
   what's needed for hygroscopic / oxygen-sensitive metal powders (Ti-6Al-4V,
   AlSi10Mg) over multi-day storage?
4. Published work on **split butterfly valves / dry-disconnect containment
   valves** for powder transfer (containment performance, residual powder on
   the "passive" face, cleanability) and whether a scaled-down 3D-printed
   analogue is credible.
5. Any literature or standards on **triboelectric charging and adhesion of fine
   powders on polymer closure surfaces**, and material choices (ESD-safe
   filaments, PTFE, coated surfaces) that mitigate it.
6. Quantitative guidance on **how much residual powder remains on a
   contamination-critical mating face** after a dry-disconnect operation, and
   what that implies for cross-contamination between different alloy powders.

Cite specific papers, standards, and measured numbers wherever possible, and
finish with concrete, testable recommendations for a bench experiment that
would discriminate between an iris-type closure, an elastomeric self-closing
valve, and a rigid orientation-indexed cap.


# Powder-Science and Engineering Evidence for Dispensing Closure Selection on a Multi-Doser Carousel

## 1. Powder Leakage, Rat-Holing, and Flooding at Auger Outlets

The closure must address two complementary failure modes. First, **static leakage**: when the module sits idle on the carousel, gravity and vibration can dislodge powder through any gap at the outlet. Second, **flooding/flushing**: if the powder bed becomes aerated during handling, removal of a cap or opening of a closure can trigger a sudden, liquid-like discharge.

Ogata's review of powder floodability establishes that fine powders below approximately 40 µm diameter are especially flood-prone (ogata2019areviewrecent pages 9-11). According to the Geldart classification, Group A particles (easily fluidized, typical of many AM metal powders in the 20–63 µm range at high density) exhibit "remarkable flooding tendency," while Group C particles (very fine, highly cohesive) are less flood-prone due to strong cohesion but are difficult to control by other means (ogata2019areviewrecent pages 11-12, ogata2019areviewrecent pages 8-9). The mechanism involves interstitial air pressure: when the void fraction and trapped air pressure are high, opening an orifice allows fluid-pressure-driven discharge of powder in a spouting or flushing event (ogata2019areviewrecent pages 9-11). This is particularly concerning for a closure that is opened rapidly (e.g., a spring-loaded iris snapping open), since the sudden pressure release could trigger a powder burst.

In auger/screw feeder systems, cohesive powders below approximately 50–100 µm are dominated by van der Waals forces, electrostatic forces, and capillary forces between particles, leading to agglomeration, adhesion to walls, and flow inconsistency (fathollahi2020performanceevaluationof pages 1-2). Screw feeders for such powders require agitators to prevent rat-holing and arching in the hopper section (hou2024developmentofa pages 1-5, dai2011biomassgranularscrew pages 1-2). These problems are relevant to the closure design because an unsealed auger outlet, even if the auger itself provides some mechanical seal, does not prevent powder from settling into and past the flight clearances during idle storage.

**Design implication**: Any closure that opens suddenly (iris snapping open, spring-loaded cap releasing) risks triggering a flood event with aerated fine powders. A slow, controlled opening or a design that keeps the outlet occluded by the auger flights until positive rotation begins is preferred.

## 2. Contamination and Particle Shedding from Sliding/Rubbing Closures

No published study was found that specifically examines iris diaphragm closures used with fine metal powders. However, the tribology of 3D-printed polymers sliding against metal surfaces has been studied. Maydanshahi et al. (2024) measured wear coefficients for 3D-printed PEEK sliding against steel ranging from 1.418 × 10⁻⁵ under mild conditions to 2.089 × 10⁻¹ under severe wear, with a transition from fretting wear to adhesive wear as loads increase (maydanshahi2024theanisotropicmechanical pages 1-2, maydanshahi2024theanisotropicmechanical pages 14-16, maydanshahi2024theanisotropicmechanical pages 10-13). Critically, the wear mechanism generates submicron polymer debris that forms transfer films on the metal counter-surface (maydanshahi2024theanisotropicmechanical pages 14-16, maydanshahi2024theanisotropicmechanical pages 13-14). For an iris diaphragm, each open/close cycle involves blade-on-blade or blade-on-frame sliding contact. If metal powder particles are present in the clearances, they act as third-body abrasives, accelerating wear and generating mixed metal-polymer debris.

For this application, the concern is twofold: (a) the closure mechanism itself sheds polymer or metal wear particles that contaminate the powder, and (b) fine metal powder particles (~20–50 µm) become trapped between sliding iris blades, are ground or deformed, and are subsequently released as contamination when the module is next used with a different powder. The lap joints and pivots of an iris mechanism offer numerous crevices that are extremely difficult to clean or inspect.

**Design implication**: Iris-type closures with multiple sliding contacts are the highest-risk option for cross-contamination and wear debris generation. If pursued, all sliding surfaces must be isolated from the powder stream, and the blade material should be selected for low wear and low adhesion (e.g., PTFE-coated or glass-filled polymer).

## 3. Sealing Performance: Elastomeric vs. Rigid Closures and Sensitivity of Target Powders

### 3.1 Powder Sensitivity Establishes the Barrier Requirement

The retrieved literature provides strong quantitative evidence that the target metal powders are highly sensitive to moisture and oxygen exposure:

- **AlSi10Mg** is the most susceptible alloy. Cordova et al. (2020) found that moisturized AlSi10Mg powder (conditioned at 50 °C, 80% RH for 72 h) reached approximately 0.437% average moisture content—roughly six times its initial value—with considerable decreases in spreadability and relative density (cordova2020measuringthespreadability pages 5-6, cordova2020measuringthespreadability pages 10-11). Fedina et al. (2022) showed that AlSi10Mg powder oxygen content rose from 0.067 wt% (virgin) to 0.257 wt% after 96 h of aging in ambient atmosphere, and that the moisture-driven oxide layer growth cannot be reversed by drying alone (fedina2022influenceofalsi10mg pages 1-2, fedina2022influenceofalsi10mg pages 4-5). This oxygen increase doubled the porosity of printed parts from 3.16% (virgin) to 6.5% (aged 96 h) (fedina2022influenceofalsi10mg pages 1-2).

- **Ti-6Al-4V** is less moisture-sensitive owing to its spherical morphology, but oxygen content is tightly specification-constrained. Virgin Ti-6Al-4V Grade 23 powder was measured at 0.107 wt% O, with the qualification limit at 0.13 wt% for Grade 23 (ELI) and 0.20 wt% for Grade 5 (koushik2023effectiveti6al4vpowder pages 2-4). Reported oxygen pickup rates range from 0.000645 wt% per reuse cycle to 0.011 wt% per cycle depending on the system, meaning that the margin to specification can be consumed within 2–10 handling exposures (koushik2023effectiveti6al4vpowder pages 2-4).

- Fine particle fractions dramatically increase moisture sorption. Muñiz-Lerma et al. (2018) demonstrated via DVS that AlSi7Mg powder with a fine fraction (D50 ≈ 31 µm) showed significantly larger vapor sorption than coarser cuts (D50 ≈ 63–70 µm). Sieving out the fines reduced the degree of vapor sorption substantially (munizlerma2018acomprehensiveapproach pages 5-8, munizlerma2018acomprehensiveapproach pages 1-3).

### 3.2 Elastomeric vs. Rigid Barrier

No direct measurements of duckbill or slit-septum valve oxygen/moisture transmission rates for powder protection were found. However, available polymer barrier data indicate that elastomeric and flexible polymer pathways are orders of magnitude more permeable than rigid closures. Reinas et al. (2016) showed that seal regions in thermosealed packages can contribute up to three times the moisture transfer rate of the film itself, illustrating that small seal paths can dominate package-level ingress. Flexible polymer barriers such as SEBS/PP blends have been measured at oxygen permeability of ~1487 cc/m²/24 h and water permeability of ~0.098 g/h·m², values that would be entirely inadequate for protecting AlSi10Mg over multi-day storage (abidin2024enhancingpolytetrafluoroethylene(ptfe) pages 2-3).

A rigid cap with an elastomeric O-ring offers a fundamentally different sealing architecture: the O-ring is compressed between two rigid surfaces to create a narrow, highly compressed seal path. The total diffusion area and path length are far more favorable than a slit or duckbill valve where the entire closure face is thin elastomer.

**Design implication**: For AlSi10Mg and other oxidation-sensitive alloys, an elastomeric self-closing valve (duckbill, slit septum) is unlikely to provide adequate barrier performance over multi-day storage. A rigid cap with a compressed O-ring is strongly preferred.

## 4. Split Butterfly Valves / Dry-Disconnect Containment Valves

The pharmaceutical industry's split butterfly valve (SBV) is the gold standard for contained powder transfer, with performance typically validated to the ISPE SMEPAC (Standardized Measurement of Equipment Particulate Airborne Concentration) protocol. Key references on containment performance (Bässler & Lehmann, 2013; Eherts & Wilkins, 2005) were not obtainable for this review. However, the operating principle is well established: two interlocking half-discs seal against each other, creating a "clean" break with minimal residual powder on the exposed passive face.

A 3D-printed analogue at the 5–15 mm scale is mechanically credible in principle—the geometry of two interlocking disc halves can be reproduced by SLA printing with adequate tolerances. However, several caveats apply: (1) Pharma-grade SBVs are precision-machined from stainless steel and achieve sub-microgram residual powder levels on the passive face; 3D-printed polymer surfaces have significantly higher roughness (Ra typically 5–50 µm for FDM, 2–10 µm for SLA) and will retain more powder. (2) At 5–15 mm scale, the mechanism complexity of a true SBV may be impractical; a simplified "split cap" with two mating flat faces may be more appropriate. (3) The SBV approach inherently solves the orientation problem if the docking station provides one half of the valve and the module provides the other.

**Design implication**: A miniaturized split-cap concept borrowing the face-to-face mating principle from pharmaceutical SBVs is attractive for this application, but the residual powder on 3D-printed polymer surfaces will be substantially higher than on machined stainless steel. Testing of residual contamination on printed surfaces is essential.

## 5. Triboelectric Charging and Adhesion on Polymer Closure Surfaces

Fine powders with particle sizes below 50–100 µm experience significant interparticle forces including van der Waals, electrostatic, and capillary forces (fathollahi2020performanceevaluationof pages 1-2). These same forces govern powder adhesion to closure surfaces. PTFE and fluoro-polymer coatings offer the lowest surface energy among common polymers, resulting in minimal wetting and reduced adhesion (abidin2024enhancingpolytetrafluoroethylene(ptfe) pages 2-3). Abidin et al. (2024) demonstrated that PTFE-coated substrates can achieve contact angles above 146° (abidin2024enhancingpolytetrafluoroethylene(ptfe) pages 2-3).

For the triboelectric series, metal powders (Ti, Al alloys, stainless steel) generally charge positively when contacted with most polymers. Standard FDM filaments (PLA, ABS, PETG, nylon) sit at various positions in the triboelectric series; nylon is strongly positive-charging, while PTFE is extremely negative-charging. Contact between metal particles and these polymers generates charge separation, with the result that particles can become strongly attracted to the surface. ESD-safe (carbon-filled or conductive-filler) polymer filaments reduce surface resistivity (typically to 10³–10⁶ Ω/sq), allowing charge to dissipate and reducing electrostatic adhesion.

Muñiz-Lerma et al. (2018) showed that the fine particle fraction dominates moisture uptake and cohesion behavior in AlSi7Mg powders; when fines below ~48 µm were removed by sieving, moisture sorption and inter-particle cohesion dropped substantially (munizlerma2018acomprehensiveapproach pages 5-8, munizlerma2018acomprehensiveapproach pages 1-3). This implies that the closure surface material is most critical for powders with a significant fine fraction.

**Design implication**: Powder-contact surfaces on the closure should be PTFE-lined, PTFE-coated, or made from an ESD-safe low-surface-energy polymer. Generic PLA or ABS should be avoided for powder-contact surfaces. If FDM printing is used for the closure body, lining or coating the sealing face with a PTFE sheet or spray-applied PTFE is recommended.

## 6. Residual Powder and Cross-Contamination

No quantitative papers measuring residual powder mass on a contamination-critical mating face after a dry-disconnect operation in the context of AM powder handling were found. This is an acknowledged gap; cross-contamination in multi-material AM is recognized as a concern but sparsely quantified. The pharmaceutical industry's approach—SMEPAC testing with gravimetric and particle-count measurements—provides the methodological framework for quantifying this in the AM context.

The criticality of cross-contamination depends on the alloy system. Mixing even small amounts of one alloy powder (e.g., a few milligrams of Ti-6Al-4V) into another (e.g., AlSi10Mg) can produce intermetallic inclusions, embrittlement, or porosity in the printed part. Given that the dispensing outlet is 5–15 mm across, even a monolayer of residual particles (~0.05 mg/cm² for 30 µm particles at ~50% packing) across the mating face would represent a measurable contamination source over many docking cycles.

**Design implication**: Minimizing the mating face area and ensuring it can be wiped or blown clean before each new powder contact is essential. The closure design should favor flat, smooth, easily inspectable surfaces over complex multi-blade mechanisms with hidden crevices.

## Summary Comparison of Closure Concepts

The following table synthesizes the evidence-based comparison of the three closure types under consideration:

| Closure Type | Key Pro | Key Con | Measured Leakage or Barrier Data | Contamination Risk | Powder Compatibility Notes | Maintenance/Cleanability observations | Literature Sources |
|---|---|---|---|---|---|---|---|
| Iris / ratchet sliding diaphragm | Can be made passive and auto-opening; orientation-independent opening is plausible; hard stop can give repeatable open area | Multiple rubbing interfaces and clearances at blade overlaps; powder can intrude into joints; wear debris/galling risk rises with metal-on-metal or powder-abrasive contacts; mechanically complex | No direct closure-leakage data found. For fine cohesive powders, unsealed/aerated outlets can flush or flood when interstitial air pressure and void fraction are high; fine powders <40 µm are especially flood-prone. This argues that any non-hermetic iris with blade clearances is vulnerable to both leakage and sudden discharge if powder becomes aerated (ogata2019areviewrecent pages 11-12, ogata2019areviewrecent pages 9-11, ogata2019areviewrecent pages 8-9). | Highest of the three concepts: residual powder can lodge in blade overlaps and be released later; rubbing contacts can generate wear debris; powder contamination in machine-element contacts is a known wear accelerator (ogata2019areviewrecent pages 11-12, ogata2019areviewrecent pages 9-11). | Poor fit for highly cohesive, hygroscopic, or tribo-prone metal powders unless all powder-wetted sliding parts are isolated from the powder path. Fine Al- and Ti-based powders are sensitive to oxidation/moisture pickup and to handling contamination (fedina2022influenceofalsi10mg pages 1-2, leung2019theeffectof pages 1-5). | Hardest to inspect and clean because contamination can hide in lap joints, pivots, and springs; likely to need periodic disassembly or replacement of wear parts. | (ogata2019areviewrecent pages 11-12, ogata2019areviewrecent pages 9-11, ogata2019areviewrecent pages 8-9, leung2019theeffectof pages 1-5) |
| Elastomeric self-closing valve (duckbill / slit septum / umbrella) | Passive self-closing; orientation-insensitive; simple geometry; no internal sliding blades, so less hard-particle abrasion from rubbing joints | Best suited to fluids, not cohesive powders; slit can trap powder and hold it open; elastomer is permeable to O2/H2O compared with rigid caps; tribo/adhesion and permanent set may worsen sealing over time | Direct valve data not found in retrieved set. Available barrier data show polymer/seal regions can dominate ingress: thermoseals allowed up to 3× the moisture transfer of the film itself, showing small seal paths can control package barrier (reinas2016). Retrieved polymer data show oxygen permeability can be very high in flexible polymers (e.g. SEBS/PP reported 1486.6 cc/m²/24 h after ageing) and water permeability 0.098 g/h·m², illustrating that elastomeric/polymeric barriers are orders weaker than rigid metal caps unless diffusion path is very small (abidin2024enhancingpolytetrafluoroethylene(ptfe) pages 2-3). | Moderate to high: residual powder can remain embedded in slit lips; opening by probe/docking pin can wipe powder onto the mating feature; less wear debris than iris, but more retained residue on soft surfaces. | Weak choice for very fine cohesive metal powders and hygroscopic powders: AlSi10Mg showed strong moisture sensitivity, reaching ~0.437% moisture after 72 h at 50 °C/80% RH and about 6× initial moisture; Ti-6Al-4V showed much lower moisture pickup. A permeable elastomer seal is therefore especially risky for Al alloys over multi-day storage (cordova2020measuringthespreadability pages 5-6, cordova2020measuringthespreadability pages 10-11). | Easier to replace than an iris, but difficult to certify as clean because residue can remain inside slits or under umbrella lips; elastomer ageing and compression set require periodic swap-out. | (cordova2020measuringthespreadability pages 5-6, cordova2020measuringthespreadability pages 10-11, abidin2024enhancingpolytetrafluoroethylene(ptfe) pages 2-3) |
| Rigid cap with O-ring, ideally orientation-indexed during docking | Best achievable barrier with simple manufacturable parts; can isolate powder from moving mechanism; least particle shedding if cap and seat do not rub through powder; compatible with self-indexing docking features | Requires either orientation-insensitive docking geometry or a self-indexing feature; needs reliable cap-actuation linkage; O-ring can still leak if powder contaminates the seat | Strongest evidence-based option for barrier control. Metal AM powders pick up harmful moisture/oxygen during storage/handling: AlSi10Mg moisturized powder reached ~0.437% moisture after 72 h at 50 °C/80% RH and oxygen in aged AlSi10Mg increased from 0.067 wt% (virgin) to 0.257–0.274 wt% after 96 h ageing; aged powder produced 6.5% porosity vs 3.16% for virgin. Ti-6Al-4V Grade 23 virgin powder reported 0.107 wt% O, with qualification limit about 0.13 wt% and reported pickup rates from 0.000645% to 0.011 wt% per cycle. These numbers strongly favor the lowest-permeability closure possible (cordova2020measuringthespreadability pages 5-6, fedina2022influenceofalsi10mg pages 1-2, fedina2022influenceofalsi10mg pages 4-5, koushik2023effectiveti6al4vpowder pages 2-4). | Lowest if the sealing land is narrow, shielded, and wiped outside the powder stream; residual powder is mainly on one flat mating face rather than inside a mechanism. Still vulnerable if powder lands on the O-ring groove or face during closing. | Best fit for cohesive, hygroscopic, oxidation-sensitive powders. Especially recommended for AlSi10Mg and other oxidation/moisture-sensitive alloys; also suitable for tribo-prone powders if powder-wetted surfaces are metal or low-surface-energy liners rather than generic polymers (cordova2020measuringthespreadability pages 5-6, fedina2022influenceofalsi10mg pages 1-2, abidin2024enhancingpolytetrafluoroethylene(ptfe) pages 2-3). | Easiest to inspect, clean, and validate: one seat, one cap face, one O-ring groove. Replacement parts are simple. Can be designed so all rubbing/locking actions are outside the powder path. | (cordova2020measuringthespreadability pages 5-6, fedina2022influenceofalsi10mg pages 1-2, fedina2022influenceofalsi10mg pages 4-5, koushik2023effectiveti6al4vpowder pages 2-4, abidin2024enhancingpolytetrafluoroethylene(ptfe) pages 2-3) |


*Table: This table compares iris, elastomeric, and rigid-cap closure concepts against the powder-science evidence retrieved so far. It emphasizes measured moisture/oxygen pickup in AM metal powders and the likely contamination pathways most relevant to closure selection.*

## Recommended Bench Experiment Protocol

Based on the evidence reviewed above, the following bench experiments are recommended to discriminate between the iris-type closure, elastomeric self-closing valve, and rigid orientation-indexed cap:

| Test Name | Test Objective | Powder(s) Used | Setup | Measured Outcome | Pass/Fail Criteria | Duration |
|---|---|---|---|---|---|---|
| Storage vibration leakage test | Compare passive powder retention and closure robustness during carousel-like storage and transport vibration | AlSi10Mg 20–63 µm; Ti-6Al-4V 15–45 µm; optional placebo cohesive surrogate such as fused silica/lactose blend for shakedown | Fill each module to a fixed mass and headspace; orient nozzle downward, sideways, and upward in separate runs; mount 6 replicates/closure on a shaker with random vibration plus periodic 5–15 g taps; place each module over pre-weighed collection foil and inside a secondary tray; test before and after 24 h at 40–60% RH | Mass leaked (mg), number of visible leakage events, post-test actuation success/failure | Pass if median leaked mass <1 mg/24 h in every orientation and no catastrophic dump event; fail if any single event >10 mg or closure jams on first opening (ogata2019areviewrecent pages 11-12, ogata2019areviewrecent pages 9-11, hou2024developmentofa pages 1-5, bascone2020hybridmechanisticempiricalapproach pages 1-4) | 24 h per condition |
| Multi-day moisture/oxygen ingress test | Determine whether closure barrier is good enough for oxidation/moisture-sensitive powders in carousel storage | AlSi10Mg primary; Ti-6Al-4V secondary | Pre-dry and inert-fill cartridges; store at 25 °C/50% RH and an accelerated condition of 40–50 °C/80% RH; sample powder at 0, 24, 72, and 96 h; measure moisture by TGA/Karl Fischer if available and oxygen by inert gas fusion or equivalent; compare against open-nozzle and hermetic metal-cap controls | Moisture pickup (ppm or wt%), oxygen increase (wt%), change in Hall/Carney flow or spreadability | Pass for AlSi10Mg only if ingress stays well below literature-sensitive region and no significant flow degradation; strong preference if ΔO2 is near measurement noise and moisture increase is far below the ~0.437% moisture seen in severe exposure; fail if clear upward drift approaches known degradation regimes (cordova2020measuringthespreadability pages 5-6, fedina2022influenceofalsi10mg pages 1-2, cordova2020measuringthespreadability pages 10-11, fedina2022influenceofalsi10mg pages 4-5, koushik2023effectiveti6al4vpowder pages 2-4, leung2019theeffectof pages 1-5, munizlerma2018acomprehensiveapproach pages 5-8) | 4 days |
| Residual powder on mating face after 50 cycles | Quantify contamination left on closure and dock mating faces after repeated open/close operations | AlSi10Mg dyed with trace fluorescent tag if allowed; otherwise Ti-6Al-4V or inert stainless surrogate for image analysis | Run 50 dock/open/dispense/close/undock cycles with fixed small dose and identical tapping/tilt profile; after cycle 50, swab or tape-lift the closure face, dock face, and any indexing feature; weigh recovered residue and image fluorescence/particle counts under microscope | Residual mass on passive face (mg), particle count/mm², residue map area (%) | Pass if median passive-face residue is below analytical balance noise or predefined cross-contamination budget; fail if residue accumulates monotonically or concentrates in crevices, especially blade overlaps or elastomer slits (ogata2019areviewrecent pages 11-12, abidin2024enhancingpolytetrafluoroethylene(ptfe) pages 2-3, munizlerma2018acomprehensiveapproach pages 5-8) | 1 day |
| Wear debris generation test | Detect closure-generated particulates from sliding/rubbing contacts and powder intrusion | Empty-run first; then AlSi10Mg or Ti-6Al-4V for loaded run | Cycle each closure 200 times in a clean enclosure; collect debris on black witness plates and adhesive tabs near outlet and mechanism; inspect by microscopy; if possible separate polymer/metal wear from powder by FTIR/EDS or morphology; compare empty vs powder-loaded cycling | Debris count, maximum particle size, debris mass, mechanism drag torque change | Pass if empty-run debris is negligible and loaded-run adds no closure-derived particles above background; fail if polymer smear, flakes, or metal galling debris appear or actuation torque rises markedly with cycling (maydanshahi2024theanisotropicmechanical pages 1-2, maydanshahi2024theanisotropicmechanical pages 14-16, maydanshahi2024theanisotropicmechanical pages 10-13, maydanshahi2024theanisotropicmechanical pages 13-14) | 100–200 cycles |
| Uncapping flood/flush challenge | Measure risk of sudden uncontrolled discharge when opening after aeration, tilt, and tapping | AlSi10Mg; Ti-6Al-4V; optional very flood-prone fine surrogate <40 µm | Condition filled cartridges by 30 min side storage, then prescribed tilt history and 20 standardized taps; open closure over a high-speed camera and analytical balance without auger motion; repeat for three nozzle orientations and after 1 h rest vs immediate opening | Burst mass in first 1 s, peak discharge rate, visible spout/flushing event, time to stable no-flow | Pass if first-second burst is near zero and no spouting event occurs; fail if opening alone releases a measurable slug or liquid-like flush, especially in fine/aerated states (ogata2019areviewrecent pages 11-12, ogata2019areviewrecent pages 9-11, ogata2019areviewrecent pages 8-9, dai2011biomassgranularscrew pages 1-2) | 1–2 days |
| Triboelectric adhesion / clean release test | Compare how strongly powders stick to closure materials and whether residue self-clears on opening/closing | AlSi10Mg, Ti-6Al-4V, and one organic cohesive powder if relevant | Prepare witness coupons matching each closure’s powder-contact material/finish: printed polymer, ESD polymer, PTFE-lined, stainless, coated stainless; expose to identical powder contact plus 20 rub/open-close events at 20%, 50%, and 80% RH; invert and lightly tap with fixed energy; image retained powder | Retained mass per area, image-covered area %, decay after tapping, RH sensitivity | Pass if retained residue is minimal and largely removed by one standardized tap/open event; expected better performance for low-surface-energy PTFE-like or metal surfaces; fail if residue persists in slits, texture valleys, or printed layer lines (abidin2024enhancingpolytetrafluoroethylene(ptfe) pages 2-3, fathollahi2020performanceevaluationof pages 1-2, munizlerma2018acomprehensiveapproach pages 5-8, munizlerma2018acomprehensiveapproach pages 1-3) | 1–2 days |
| Integrated ranking run | Produce a single decision metric across all three closure concepts | Best-performing two powders from above | Run the same 3 modules/closure through the full sequence: 24 h storage vibration, 50 cycles, 200-cycle wear, then accelerated storage; score each closure on leakage, ingress, residue, debris, and actuation reliability with weighted criteria | Weighted score; rank order; confidence intervals across replicates | Select closure only if it wins on barrier plus contamination, not just convenience; default fail if any catastrophic mode appears even once (cordova2020measuringthespreadability pages 5-6, fedina2022influenceofalsi10mg pages 4-5, ogata2019areviewrecent pages 11-12, maydanshahi2024theanisotropicmechanical pages 1-2) | 1 week |


*Table: This table gives a specific, testable bench protocol to discriminate among iris, elastomeric, and rigid indexed caps. It emphasizes the failure modes most strongly supported by the retrieved powder-flow, oxidation, adhesion, and wear evidence.*

## Conclusions and Recommendations

Based on the powder-science evidence reviewed:

1. **The rigid orientation-indexed cap with O-ring is the strongest candidate.** It offers the best barrier against moisture and oxygen ingress—critical given that AlSi10Mg oxygen content can rise from 0.067 to 0.257 wt% in 96 hours of unprotected ambient exposure, doubling part porosity (fedina2022influenceofalsi10mg pages 1-2, fedina2022influenceofalsi10mg pages 4-5), and that Ti-6Al-4V has only ~0.023 wt% margin from virgin to Grade 23 specification (koushik2023effectiveti6al4vpowder pages 2-4). It also presents the simplest surface for cleaning and inspection to prevent cross-contamination.

2. **The iris/ratchet closure is the highest-risk option** due to wear debris generation (3D-printed polymer wear coefficients reach 10⁻¹ under severe conditions, with adhesive transfer and submicron debris (maydanshahi2024theanisotropicmechanical pages 1-2, maydanshahi2024theanisotropicmechanical pages 10-13)), powder ingress into mechanism clearances, and the difficulty of cleaning multi-blade lap joints. It should be considered only if the orientation-insensitivity requirement cannot be solved by a self-indexing docking feature.

3. **The elastomeric self-closing valve is inadequate for multi-day storage of oxidation-sensitive powders** unless backed by a secondary rigid barrier. The high oxygen and moisture permeability of elastomers, combined with the demonstrated sensitivity of AlSi10Mg (6× moisture increase in 72 h at elevated humidity (cordova2020measuringthespreadability pages 5-6, cordova2020measuringthespreadability pages 10-11)), makes this a poor choice for the stated storage scenario.

4. **The orientation problem is best solved at the docking station rather than the closure.** A conical or self-centering dock feature can index the module to a known rotational position, allowing a simple rigid cap to be lifted or rotated off by a fixed mechanism at the station. This avoids imposing orientation-insensitivity requirements on the seal itself.

5. **Material selection for all powder-contact surfaces should favor PTFE-coated or low-surface-energy, ESD-safe polymers** to minimize triboelectric adhesion and residual powder retention (abidin2024enhancingpolytetrafluoroethylene(ptfe) pages 2-3, munizlerma2018acomprehensiveapproach pages 5-8).

6. **Flooding risk on uncapping must be tested explicitly.** Fine powders below 40 µm in the Geldart Group A/C range are prone to sudden flushing when interstitial air pressure is released (ogata2019areviewrecent pages 11-12, ogata2019areviewrecent pages 9-11). Any closure design should be tested with the uncapping flood challenge described in the bench protocol.

### Literature Gaps Identified

Several topics yielded limited retrievable literature: (a) quantitative residual powder data after dry-disconnect operations in the AM context; (b) direct measurements of duckbill/slit-septum valve barrier performance with powder loads; (c) iris diaphragm wear specifically with metal AM powders; (d) ISPE/SMEPAC containment performance data for miniaturized split valves. The recommended bench experiments above are designed to fill these gaps with directly applicable data for this instrument.


References

1. (ogata2019areviewrecent pages 9-11): Koichiro Ogata. A review: recent progress on evaluation of flowability and floodability of powder. KONA Powder and Particle Journal, 36:33-49, Jan 2019. URL: https://doi.org/10.14356/kona.2019002, doi:10.14356/kona.2019002. This article has 23 citations and is from a peer-reviewed journal.

2. (ogata2019areviewrecent pages 11-12): Koichiro Ogata. A review: recent progress on evaluation of flowability and floodability of powder. KONA Powder and Particle Journal, 36:33-49, Jan 2019. URL: https://doi.org/10.14356/kona.2019002, doi:10.14356/kona.2019002. This article has 23 citations and is from a peer-reviewed journal.

3. (ogata2019areviewrecent pages 8-9): Koichiro Ogata. A review: recent progress on evaluation of flowability and floodability of powder. KONA Powder and Particle Journal, 36:33-49, Jan 2019. URL: https://doi.org/10.14356/kona.2019002, doi:10.14356/kona.2019002. This article has 23 citations and is from a peer-reviewed journal.

4. (fathollahi2020performanceevaluationof pages 1-2): Sara Fathollahi, Stephan Sacher, M. Sebastian Escotet-Espinoza, James DiNunzio, and Johannes G. Khinast. Performance evaluation of a high-precision low-dose powder feeder. AAPS PharmSciTech, Nov 2020. URL: https://doi.org/10.1208/s12249-020-01835-5, doi:10.1208/s12249-020-01835-5. This article has 25 citations and is from a peer-reviewed journal.

5. (hou2024developmentofa pages 1-5): Development of a micro-feeder for cohesive pharmaceutical powders This article has 2 citations.

6. (dai2011biomassgranularscrew pages 1-2): Jianjun Dai and John R. Grace. Biomass granular screw feeding: an experimental investigation. Biomass & Bioenergy, 35:942-955, Feb 2011. URL: https://doi.org/10.1016/j.biombioe.2010.11.026, doi:10.1016/j.biombioe.2010.11.026. This article has 96 citations and is from a domain leading peer-reviewed journal.

7. (maydanshahi2024theanisotropicmechanical pages 1-2): Mohammad Reza Maydanshahi, Mohammad Reza Najari, Tom Slatter, and Mahdi Mohammadpour. The anisotropic mechanical and tribological behaviors of additively manufactured (material extrusion) implant-grade polyether ether ketone (peek). Lubricants, 12:347, Oct 2024. URL: https://doi.org/10.3390/lubricants12100347, doi:10.3390/lubricants12100347. This article has 11 citations.

8. (maydanshahi2024theanisotropicmechanical pages 14-16): Mohammad Reza Maydanshahi, Mohammad Reza Najari, Tom Slatter, and Mahdi Mohammadpour. The anisotropic mechanical and tribological behaviors of additively manufactured (material extrusion) implant-grade polyether ether ketone (peek). Lubricants, 12:347, Oct 2024. URL: https://doi.org/10.3390/lubricants12100347, doi:10.3390/lubricants12100347. This article has 11 citations.

9. (maydanshahi2024theanisotropicmechanical pages 10-13): Mohammad Reza Maydanshahi, Mohammad Reza Najari, Tom Slatter, and Mahdi Mohammadpour. The anisotropic mechanical and tribological behaviors of additively manufactured (material extrusion) implant-grade polyether ether ketone (peek). Lubricants, 12:347, Oct 2024. URL: https://doi.org/10.3390/lubricants12100347, doi:10.3390/lubricants12100347. This article has 11 citations.

10. (maydanshahi2024theanisotropicmechanical pages 13-14): Mohammad Reza Maydanshahi, Mohammad Reza Najari, Tom Slatter, and Mahdi Mohammadpour. The anisotropic mechanical and tribological behaviors of additively manufactured (material extrusion) implant-grade polyether ether ketone (peek). Lubricants, 12:347, Oct 2024. URL: https://doi.org/10.3390/lubricants12100347, doi:10.3390/lubricants12100347. This article has 11 citations.

11. (cordova2020measuringthespreadability pages 5-6): Laura Cordova, Ton Bor, Marc de Smit, Mónica Campos, and Tiedo Tinga. Measuring the spreadability of pre-treated and moisturized powders for laser powder bed fusion. Additive Manufacturing, 32:101082, Mar 2020. URL: https://doi.org/10.1016/j.addma.2020.101082, doi:10.1016/j.addma.2020.101082. This article has 167 citations and is from a highest quality peer-reviewed journal.

12. (cordova2020measuringthespreadability pages 10-11): Laura Cordova, Ton Bor, Marc de Smit, Mónica Campos, and Tiedo Tinga. Measuring the spreadability of pre-treated and moisturized powders for laser powder bed fusion. Additive Manufacturing, 32:101082, Mar 2020. URL: https://doi.org/10.1016/j.addma.2020.101082, doi:10.1016/j.addma.2020.101082. This article has 167 citations and is from a highest quality peer-reviewed journal.

13. (fedina2022influenceofalsi10mg pages 1-2): Tatiana Fedina, Filippo Belelli, Giorgia Lupi, Benedikt Brandau, Riccardo Casati, Raphael Berneth, Frank Brueckner, and Alexander F.H. Kaplan. Influence of alsi10mg powder aging on the material degradation and its processing in laser powder bed fusion. Nov 2022. URL: https://doi.org/10.1016/j.powtec.2022.118024, doi:10.1016/j.powtec.2022.118024. This article has 26 citations and is from a domain leading peer-reviewed journal.

14. (fedina2022influenceofalsi10mg pages 4-5): Tatiana Fedina, Filippo Belelli, Giorgia Lupi, Benedikt Brandau, Riccardo Casati, Raphael Berneth, Frank Brueckner, and Alexander F.H. Kaplan. Influence of alsi10mg powder aging on the material degradation and its processing in laser powder bed fusion. Nov 2022. URL: https://doi.org/10.1016/j.powtec.2022.118024, doi:10.1016/j.powtec.2022.118024. This article has 26 citations and is from a domain leading peer-reviewed journal.

15. (koushik2023effectiveti6al4vpowder pages 2-4): Tejas Koushik, Haopeng Shen, Wen Hao Kan, Mu Gao, Junlan Yi, Chao Ma, Samuel Chao Voon Lim, Louis Ngai Sum Chiu, and Aijun Huang. Effective ti-6al-4v powder recycling in lpbf additive manufacturing considering powder history. Sustainability, 15:15582, Nov 2023. URL: https://doi.org/10.3390/su152115582, doi:10.3390/su152115582. This article has 29 citations.

16. (munizlerma2018acomprehensiveapproach pages 5-8): Jose Alberto Muñiz-Lerma, Amy Nommeots-Nomm, Kristian Edmund Waters, and Mathieu Brochu. A comprehensive approach to powder feedstock characterization for powder bed fusion additive manufacturing: a case study on alsi7mg. Materials, 11:2386, Nov 2018. URL: https://doi.org/10.3390/ma11122386, doi:10.3390/ma11122386. This article has 165 citations.

17. (munizlerma2018acomprehensiveapproach pages 1-3): Jose Alberto Muñiz-Lerma, Amy Nommeots-Nomm, Kristian Edmund Waters, and Mathieu Brochu. A comprehensive approach to powder feedstock characterization for powder bed fusion additive manufacturing: a case study on alsi7mg. Materials, 11:2386, Nov 2018. URL: https://doi.org/10.3390/ma11122386, doi:10.3390/ma11122386. This article has 165 citations.

18. (abidin2024enhancingpolytetrafluoroethylene(ptfe) pages 2-3): Noraziani Zainal Abidin, Haslaniza Hashim, Saiful Irwan Zubairi, Mohamad Yusof Maskat, Noorain Purhanudin, Rozidawati Awang, Jarinah Mohd Ali, and Harisun Yaakob. Enhancing polytetrafluoroethylene (ptfe) coated film for food processing: unveiling surface transformations through oxygenated plasma treatment and parameter optimization using response surface methodology. PLOS ONE, 19:e0303931, May 2024. URL: https://doi.org/10.1371/journal.pone.0303931, doi:10.1371/journal.pone.0303931. This article has 8 citations and is from a peer-reviewed journal.

19. (leung2019theeffectof pages 1-5): Chu Lun Alex Leung, Sebastian Marussi, Michael Towrie, Robert C. Atwood, Philip J. Withers, and Peter D. Lee. The effect of powder oxidation on defect formation in laser additive manufacturing. Acta Materialia, 166:294-305, Mar 2019. URL: https://doi.org/10.1016/j.actamat.2018.12.027, doi:10.1016/j.actamat.2018.12.027. This article has 425 citations and is from a highest quality peer-reviewed journal.

20. (bascone2020hybridmechanisticempiricalapproach pages 1-4): Davide Bascone, Federico Galvanin, Nilay Shah, and Salvador Garcia-Munoz. Hybrid mechanistic-empirical approach to the modeling of twin screw feeders for continuous tablet manufacturing. Industrial & Engineering Chemistry Research, 59:6650-6661, Mar 2020. URL: https://doi.org/10.1021/acs.iecr.0c00420, doi:10.1021/acs.iecr.0c00420. This article has 16 citations and is from a peer-reviewed journal.