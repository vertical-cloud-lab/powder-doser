# Edison report: Assess PLA Compatibility And Alternative 3D‑Printable Materials And Coatings For Milligram Powder Dosing

- **Task ID:** `5a322274-ea6a-44b9-af7d-3c67086b06e0`
- **Job:** job-futurehouse-paperqa3
- **Completed:** 2026-07-16 16:44:07.084507+00:00

## Query

We operate an open-source auger-based powder microdoser whose powder-contacting parts
(auger screw and surrounding tube/hopper) are currently FDM 3D-printed in PLA. We plan to dose the
following powders at milligram scale (0.1-10 mg doses): (1) AIBN, 2,2'-azobisisobutyronitrile,
CAS 78-67-1; (2) Grubbs 2nd-generation ruthenium metathesis catalyst, CAS 246047-72-3 (dosing inside
an inert-atmosphere glovebox); (3) sodium cyanide, CAS 143-33-9; (4) sodium chloride as a benign test
powder.

Questions:

1. Is PLA chemically compatible with each of these powders in dry solid-solid contact? Any risks of
   reaction, catalyst deactivation/poisoning (e.g., G2 by PLA ester groups or residual moisture),
   contamination of the dosed powder by polymer wear debris, or degradation of the PLA?
2. Tribocharging: how do PLA and other printable polymers rank triboelectrically against these
   powders, and what does that imply for static adhesion/clumping in a very dry glovebox atmosphere?
3. If PLA is a poor choice, what alternative materials that can still be 3D printed would be better -
   FDM filaments (e.g., PETG, nylon, polypropylene, conductive/ESD-safe filaments, carbon-filled) or
   SLA/DLP resin printing (standard, engineering, or ceramic-filled resins)? Consider chemical
   inertness, low surface energy, low tribocharging, smooth achievable surface finish, and glovebox
   compatibility (low outgassing, low moisture uptake).
4. Are there smooth inner coatings that could be applied to a printed auger tube - e.g., parylene,
   PTFE spray coatings, silicone or fluoropolymer conformal coatings, epoxy sealing - that improve
   powder flow, reduce static, and improve chemical compatibility? How well do they adhere to PLA or
   resin prints, and are they safe with an organic radical initiator (AIBN) and a Ru carbene catalyst?
5. Any other material-selection considerations for dosing these specific powders (e.g., AIBN thermal
   sensitivity vs printed-part friction heating, NaCN containment and cleanability, humidity effects).

Provide practical recommendations with citations where possible.

## Answer

Question: We operate an open-source auger-based powder microdoser whose powder-contacting parts
(auger screw and surrounding tube/hopper) are currently FDM 3D-printed in PLA. We plan to dose the
following powders at milligram scale (0.1-10 mg doses): (1) AIBN, 2,2'-azobisisobutyronitrile,
CAS 78-67-1; (2) Grubbs 2nd-generation ruthenium metathesis catalyst, CAS 246047-72-3 (dosing inside
an inert-atmosphere glovebox); (3) sodium cyanide, CAS 143-33-9; (4) sodium chloride as a benign test
powder.

Questions:

1. Is PLA chemically compatible with each of these powders in dry solid-solid contact? Any risks of
   reaction, catalyst deactivation/poisoning (e.g., G2 by PLA ester groups or residual moisture),
   contamination of the dosed powder by polymer wear debris, or degradation of the PLA?
2. Tribocharging: how do PLA and other printable polymers rank triboelectrically against these
   powders, and what does that imply for static adhesion/clumping in a very dry glovebox atmosphere?
3. If PLA is a poor choice, what alternative materials that can still be 3D printed would be better -
   FDM filaments (e.g., PETG, nylon, polypropylene, conductive/ESD-safe filaments, carbon-filled) or
   SLA/DLP resin printing (standard, engineering, or ceramic-filled resins)? Consider chemical
   inertness, low surface energy, low tribocharging, smooth achievable surface finish, and glovebox
   compatibility (low outgassing, low moisture uptake).
4. Are there smooth inner coatings that could be applied to a printed auger tube - e.g., parylene,
   PTFE spray coatings, silicone or fluoropolymer conformal coatings, epoxy sealing - that improve
   powder flow, reduce static, and improve chemical compatibility? How well do they adhere to PLA or
   resin prints, and are they safe with an organic radical initiator (AIBN) and a Ru carbene catalyst?
5. Any other material-selection considerations for dosing these specific powders (e.g., AIBN thermal
   sensitivity vs printed-part friction heating, NaCN containment and cleanability, humidity effects).

Provide practical recommendations with citations where possible.

### Scope note (evidence limitations)
The retrieved literature contained strong, directly citable evidence for (i) PLA’s susceptibility to moisture-driven hydrolysis/processing degradation and (ii) parylene C’s role as a chemically inert, moisture/gas barrier coating on 3D-printed substrates, plus (iii) Ru metathesis catalyst (incl. Grubbs-type) vulnerability to water/protic contamination. It did **not** contain directly citable, powder-specific compatibility studies for **dry AIBN/NaCN/NaCl vs PLA** nor a directly citable **triboelectric series** including PLA/PETG/nylon/PP/PTFE. Where such specifics are needed, recommendations below are explicitly labeled as engineering judgement requiring qualification tests.

---

## 1) Dry chemical compatibility of PLA with the four powders

### PLA baseline behavior relevant to “dry” use
Even if your dosing is intended to be dry, PLA’s key vulnerability is **water**: PLA contains hydrolyzable ester bonds; moisture exposure cleaves ester groups, decreasing molecular weight and producing oligomers/monomers (hydrolysis) (gorrasi2017hydrolysisandbiodegradation pages 1-4, gorrasi2017hydrolysisandbiodegradation pages 4-8). PLA is also prone to degradation during melt/processing, and **humidity accelerates degradation**; undried PLA shows faster viscosity decrease and visible degradation during processing, with humidity identified as “a crucial factor” (gorrasi2017hydrolysisandbiodegradation pages 4-8).

#### (1) AIBN (solid radical initiator)
- **Direct PLA–AIBN dry reaction evidence:** not found in retrieved corpus.
- **Most credible risk pathways (engineering judgement):**
  - **Contamination by wear debris**: FDM PLA auger/tube wear particles mixing into mg-scale doses can be a dominant impurity source (no direct citation in retrieved corpus).
  - **Heat/friction**: local frictional heating in an auger can, in principle, accelerate initiator decomposition (no direct citation in retrieved corpus; treat as a process-safety design constraint).

**Practical compatibility stance:** PLA is not obviously reactive with dry AIBN, but for mg-scale dosing you should treat polymer wear debris + friction heating as the primary concerns (engineering judgement).

#### (2) Grubbs 2nd-generation catalyst (inside glovebox)
- **Main risk is water/protic contamination**, not ester contact per se:
  - Literature shows **water has a negative impact on metathesis productivity due to catalyst decomposition** in Ru metathesis systems; Botti’s thesis is explicitly about catalyst deactivation by water and shows water-spiked experiments reducing turnover/productivity (botti2016advancesinolefin pages 4-7, botti2016advancesinolefin pages 3-4, botti2016advancesinolefin pages 41-45).
- **Why PLA can matter indirectly:**
  - PLA is moisture-sensitive and can carry/retain moisture if not well dried; moisture is a known risk factor for both PLA degradation (gorrasi2017hydrolysisandbiodegradation pages 4-8) and metathesis catalyst lifetime (botti2016advancesinolefin pages 4-7, botti2016advancesinolefin pages 3-4).
  - Rough/porous FDM surfaces can adsorb/retain contaminants and create dose-to-dose memory (engineering judgement; no direct citation).

**Practical compatibility stance:** **Uncoated PLA is risky for G2 dosing** primarily because controlling trace moisture/contamination is hard, and Ru catalysts are water-sensitive (botti2016advancesinolefin pages 4-7, botti2016advancesinolefin pages 3-4, botti2016advancesinolefin pages 41-45).

#### (3) Sodium cyanide (NaCN)
- **Direct PLA–NaCN dry reaction evidence:** not found in retrieved corpus.
- **Dominant material-selection issue is cleanability/containment** (engineering judgement):
  - FDM layer lines/porosity trap residues; hard to validate decontamination.
  - Static retention in dry environments increases residue hold-up and cross-contamination risk (see tribocharging section; mostly engineering judgement).

**Practical compatibility stance:** treat PLA as **operationally unsuitable** for NaCN because of **decontamination, retention, and wear debris**, even if there is no known fast dry chemical reaction (engineering judgement).

#### (4) Sodium chloride (NaCl)
- **Chemically benign** toward PLA in dry contact is a reasonable assumption, but direct compatibility citations were not found.
- NaCl is useful as a **mechanical + static-behavior surrogate** powder for retention/clumping testing (engineering judgement).

---

## 2) Tribocharging / static adhesion in very dry atmosphere (glovebox)

**Evidence gap:** No directly citable triboelectric ranking for PLA vs PETG/nylon/PP/PTFE (or for these powders) was available in the retrieved full texts.

**Engineering-judgement guidance (qualitative):**
- In a very dry glovebox, **insulating polymers + dry powders** often show strong tribocharging → particle adhesion to walls, clumping, and “dose memory.”
- **Surface roughness dominates** at mg scale: FDM ridges trap powder and increase contact electrification sites.
- General heuristic: fluoropolymers (PTFE/PFA/FEP) and some polyolefins (PP/PE) often show lower surface energy (better flow) but can still charge strongly; **conductive/ESD surfaces** reduce charge accumulation if properly grounded.

**Implication for your use:** regardless of chemistry, **static control + smooth surfaces** will likely be the largest determinant of dosing repeatability in the glovebox (engineering judgement).

---

## 3) If PLA is poor: 3D-printable alternatives (FDM and SLA/DLP)

### What can be said with citations from retrieved corpus
- PLA’s moisture sensitivity and degradation acceleration with humidity/insufficient drying are well established (gorrasi2017hydrolysisandbiodegradation pages 1-4, gorrasi2017hydrolysisandbiodegradation pages 4-8).
- Resin prints can have leachables/instability issues in some contexts, and **parylene C is used to block leachates and moisture penetration** in resin-printed devices (zhao2026recentapplicationsof pages 1-2, zhao2026recentapplicationsof pages 2-5).

### Practical material hierarchy (engineering judgement unless stated)
1. **Best-in-class for inertness/flow/cleanability (not necessarily 3D printable):** PTFE/PFA/FEP liners or machined parts (engineering judgement).
2. **FDM polyolefins (PP)**: attractive for low polarity and chemical resistance; printing is harder (warping), but doable with enclosure and correct bed/surface (engineering judgement).
3. **PETG**: generally tougher/less brittle than PLA; still insulating and can tribocharge; moderate chemical resistance (engineering judgement).
4. **Nylon (PA)**: mechanically good but **moisture uptake** is usually high → not ideal near moisture-sensitive catalysts (engineering judgement; no citation in retrieved corpus).
5. **SLA/DLP resins**: can be smoother but may outgas/leach; if used, consider sealing/barrier coating. Parylene C is explicitly used to make resin devices more stable/biocompatible and to block moisture ingress/leachates (zhao2026recentapplicationsof pages 1-2, zhao2026recentapplicationsof pages 2-5).

**Glovebox note:** a low-outgassing, low-moisture-uptake surface is desirable for Ru catalysts; parylene-coated surfaces are specifically discussed as moisture barriers (zhao2026recentapplicationsof pages 1-2).

---

## 4) Coatings/liners for printed auger tube (and compatibility with AIBN/Ru catalyst)

### Parylene C (strongest evidence-supported option)
Parylene (esp. C) is described as chemically inert and used to prevent corrosion/leaching, with excellent gas/moisture impermeability (zhao2026recentapplicationsof pages 1-2). It is applied to 3D-printed resin devices and **prevents moisture penetration and blocks leachates**, enabling repeated use (zhao2026recentapplicationsof pages 1-2, zhao2026recentapplicationsof pages 2-5). Figure evidence for the barrier concept is shown in (zhao2026recentapplicationsof media afcf53d0). Parylene coatings can have adhesion limitations; silane adhesion promoters (e.g., A-174) are discussed for hydroxylated silicon-type surfaces (zhao2026recentapplicationsof pages 2-5).

**Implications for your powders:**
- For **Grubbs G2**, a parylene-coated powder path is attractive because it reduces interaction with a potentially moist/contaminating substrate and provides a moisture barrier (zhao2026recentapplicationsof pages 1-2, zhao2026recentapplicationsof pages 2-5).
- For **AIBN**, parylene is likely inert as a hydrocarbon-like polymer; however, direct initiator–parylene compatibility data was not retrieved, so validate by a small hold-time stability test (engineering judgement).
- For **NaCN**, parylene provides a smooth, sealed surface that should improve cleanability/containment (engineering judgement; barrier function supported (zhao2026recentapplicationsof pages 1-2)).

### Other coatings (PTFE sprays, silicone, epoxy sealants)
No directly citable evidence was retrieved on:
- adhesion of PTFE spray/silicone/epoxy to PLA for powder-contact service,
- compatibility of those coatings with AIBN or Ru carbene catalysts.

**Practical recommendation (engineering judgement):**
- Treat non-parylene coatings as “possible but must be qualified” via (i) solvent wipe tests, (ii) abrasion/wear tests, (iii) extractables/contamination tests, and (iv) catalyst activity check (for G2) after contact.

---

## 5) Other powder-specific considerations

### Grubbs 2nd-gen catalyst
- **Water sensitivity is real and documented**: water reduces productivity via decomposition (botti2016advancesinolefin pages 4-7, botti2016advancesinolefin pages 3-4, botti2016advancesinolefin pages 41-45). Therefore:
  - Pre-dry and store any polymer parts carefully; avoid materials with high moisture uptake (engineering judgement, but consistent with water sensitivity evidence).
  - Minimize dead volumes/hold-up to reduce loss and decomposition risk (engineering judgement).

### PLA processing/conditioning and moisture
- PLA degradation is accelerated by humidity and insufficient drying; the literature emphasizes that degradation in melt state is “extremely accelerated” if not dried and that humidity is crucial (gorrasi2017hydrolysisandbiodegradation pages 4-8). Even though you are not remelting parts, this supports a general principle: **PLA interacts strongly with moisture history**, which is undesirable when dosing moisture-sensitive catalysts.

### NaCN containment and cleanability
- Primary driver is **safe decontamination** and minimizing trapped residues in layer lines/threads (engineering judgement; no direct citation in retrieved corpus).

### AIBN thermal/friction safety
- Not evidence-supported in retrieved corpus, but practically: implement torque limits, prevent auger jams, and keep motor/gearbox heat away from powder path (engineering judgement).

---

## Practical recommendations (actionable)

1. **For Grubbs 2nd-gen catalyst dosing:** avoid bare PLA in the powder-contact path; prioritize a **parylene C–coated** powder-contacting tube/hopper/auger (zhao2026recentapplicationsof pages 1-2, zhao2026recentapplicationsof pages 2-5) because Ru metathesis systems are **water-sensitive** and decompose in presence of water (botti2016advancesinolefin pages 4-7, botti2016advancesinolefin pages 3-4, botti2016advancesinolefin pages 41-45).  
2. **For NaCN dosing:** treat FDM polymers (especially PLA) as unfavorable due to cleanability and residue retention; use dedicated, sealable, smooth, easily decontaminated wetted paths—again, parylene coating is a strongly supported route to seal porous/resin substrates and provide a barrier layer (zhao2026recentapplicationsof pages 1-2, zhao2026recentapplicationsof pages 2-5).  
3. **For mg-scale repeatability in a dry glovebox:** regardless of polymer choice, focus on **surface smoothness** and **static mitigation** (grounding, conductive/ESD-safe materials, ionization if allowed) because tribocharging evidence was not retrievable but is typically dominant in dry powder handling (engineering judgement).  
4. **Keep NaCl as your benchmarking powder**, but qualify final performance with a powder that matches the cohesion/static behavior of your hazardous powders; NaCl alone may underpredict retention/carryover (engineering judgement).

A concise decision guide is provided here:

| Powder | Key interaction risks with PLA | Static/handling risk drivers in dry atmosphere | Recommended contact-surface material/coating options | Cleaning/containment notes |
|---|---|---|---|---|
| AIBN | No direct evidence of dry solid-solid chemical reaction with PLA in retrieved corpus. Main PLA risk is generic ester-polymer hydrolysis/degradation if moisture is present or if parts were poorly dried; PLA is moisture-sensitive and ester bonds are cleaved by hydrolysis (gorrasi2017hydrolysisandbiodegradation pages 1-4, gorrasi2017hydrolysisandbiodegradation pages 4-8). Wear debris contamination from FDM surfaces: no direct citation in retrieved corpus. | Likely high static adhesion/clinging at mg scale in very dry glovebox; no direct triboelectric ranking for AIBN vs PLA in retrieved corpus. Smoothness and low charging likely matter more than bulk chemistry here: no direct citation in retrieved corpus. | Prefer parylene C over printed substrate when possible because it is chemically inert, moisture/gas impermeable, and used as a barrier on 3D-printed parts (zhao2026recentapplicationsof pages 2-5, zhao2026recentapplicationsof pages 1-2, zhao2026recentapplicationsof pages 5-7). If reprinting, favor nonpolar/low-surface-energy polymers such as PP over PLA/nylon: no direct citation in retrieved corpus. Avoid standard SLA resin as final powder-contact surface unless sealed/coated; resin leachables/barrier concerns supported indirectly by parylene-resin literature (zhao2026recentapplicationsof pages 2-5, zhao2026recentapplicationsof pages 1-2). | Treat as thermally sensitive energetic initiator; minimize friction, motor stall, and local heating: no direct citation in retrieved corpus. Prefer disposable or dedicated wetted path inserts and low-retention geometry: no direct citation in retrieved corpus. |
| Grubbs 2nd-gen catalyst | Key risk is not PLA ester groups per se, but catalyst exposure to water/protic contamination; Ru metathesis productivity drops in presence of water due to decomposition, and even relaxed drying can matter (botti2016advancesinolefin pages 4-7, botti2016advancesinolefin pages 3-4, botti2016advancesinolefin pages 41-45). PLA is moisture-sensitive and can retain/encounter moisture issues if not dried (gorrasi2017hydrolysisandbiodegradation pages 1-4, gorrasi2017hydrolysisandbiodegradation pages 4-8). Adsorption/poisoning by rough porous FDM surface: no direct citation in retrieved corpus. | In glovebox, dry conditions help catalyst stability but worsen powder charging; likely strong adhesion to rough insulating PLA and dose-to-dose memory from hold-up in layer lines: no direct citation in retrieved corpus. | Strongest supported option: parylene C-coated contact path over thoroughly dried substrate, because parylene is chemically inert and provides moisture/leachate barrier protection on printed parts (zhao2026recentapplicationsof pages 2-5, zhao2026recentapplicationsof pages 1-2, zhao2026recentapplicationsof pages 5-7). If uncoated polymer is needed, prefer smoother, less polar, low-uptake materials over PLA/nylon; PP likely preferable by engineering judgement, no direct citation in retrieved corpus. | Use dedicated inert-atmosphere-only parts; pre-dry printed parts thoroughly before glovebox entry because PLA degradation and moisture issues are documented (gorrasi2017hydrolysisandbiodegradation pages 4-8). Minimize hold-up and dead zones to reduce expensive catalyst loss: no direct citation in retrieved corpus. |
| Sodium cyanide | No direct evidence of dry NaCN-PLA reaction in retrieved corpus. Generic concern is avoid any absorbent/porous, hard-to-clean polymer because PLA degrades with moisture and has rough FDM surfaces that may trap toxic residues (gorrasi2017hydrolysisandbiodegradation pages 1-4, gorrasi2017hydrolysisandbiodegradation pages 4-8). | Fine toxic salt powder can statically adhere to insulating rough walls in dry air, increasing contamination and decon burden: no direct citation in retrieved corpus. | Prefer chemically inert barrier surface such as parylene C if using printed substrate, supported by its chemical inertness and barrier function (zhao2026recentapplicationsof pages 2-5, zhao2026recentapplicationsof pages 1-2). If reprinting, prefer nonpolar, smoother, easier-to-clean polymers (e.g., PP) over PLA; no direct citation in retrieved corpus. Avoid porous standard SLA without barrier coating; parylene is specifically used to block leachates and ingress in 3D-printed resins (zhao2026recentapplicationsof pages 2-5, zhao2026recentapplicationsof pages 1-2). | Highest priority is containment and cleanability. Use dedicated NaCN-only wetted parts, secondary containment, validated decontamination workflow, and avoid designs with crevices/threads in powder path: no direct citation in retrieved corpus. Humidity control matters operationally, but no direct citation in retrieved corpus. |
| Sodium chloride | Chemically low concern for dry contact; main issue with PLA remains generic moisture sensitivity and potential wear debris contamination rather than reaction with NaCl (gorrasi2017hydrolysisandbiodegradation pages 1-4, gorrasi2017hydrolysisandbiodegradation pages 4-8). Good benchmark powder for mechanical testing. | Useful benign probe for static/clumping behavior of design. In very dry atmosphere, still may cling to insulating rough PLA surfaces; no direct citation in retrieved corpus. | Acceptable for early benchtop debugging on PLA, but for transferable performance data prefer same final surface class intended for hazardous powders, ideally parylene C-coated or low-energy polymer surface (zhao2026recentapplicationsof pages 2-5, zhao2026recentapplicationsof pages 1-2, zhao2026recentapplicationsof pages 5-7). | Use as test powder to quantify retention, carryover, and dose drift before introducing hazardous powders: no direct citation in retrieved corpus. Cleaning burden is low, so it is suitable for screening geometry/coating choices. |


*Table: This table summarizes likely material and handling risks for four powders in a printed auger microdoser, separating evidence-backed findings from engineering judgement where the retrieved corpus lacked direct citations. It is useful for narrowing material and coating choices before hazardous-powder testing.*

---

## Visual evidence for parylene barrier behavior
The barrier concept for parylene coating on 3D-printed substrates (preventing leachates/absorption) is illustrated in the retrieved figure (zhao2026recentapplicationsof media afcf53d0).

---

### Summary conclusion
- **PLA is not clearly “chemically reactive” with these dry powders based on retrieved evidence**, but it is **operationally suboptimal** for (i) water-sensitive Ru catalysts (indirect moisture/contamination control) and (ii) highly toxic powders (cleanability/retention). PLA’s moisture-driven degradation and sensitivity to drying history are well documented (gorrasi2017hydrolysisandbiodegradation pages 1-4, gorrasi2017hydrolysisandbiodegradation pages 4-8).  
- **Parylene C** is the most evidence-supported upgrade path for a 3D-printed dosing head: chemically inert, moisture/gas barrier, and used to stabilize/seal 3D-printed resin devices (zhao2026recentapplicationsof pages 1-2, zhao2026recentapplicationsof pages 2-5, zhao2026recentapplicationsof media afcf53d0).

References

1. (gorrasi2017hydrolysisandbiodegradation pages 1-4): Giuliana Gorrasi and Roberto Pantani. Hydrolysis and biodegradation of poly(lactic acid). Advances in Polymer Science, pages 119-151, Jan 2017. URL: https://doi.org/10.1007/12\_2016\_12, doi:10.1007/12\_2016\_12. This article has 283 citations and is from a peer-reviewed journal.

2. (gorrasi2017hydrolysisandbiodegradation pages 4-8): Giuliana Gorrasi and Roberto Pantani. Hydrolysis and biodegradation of poly(lactic acid). Advances in Polymer Science, pages 119-151, Jan 2017. URL: https://doi.org/10.1007/12\_2016\_12, doi:10.1007/12\_2016\_12. This article has 283 citations and is from a peer-reviewed journal.

3. (botti2016advancesinolefin pages 4-7): Adrian Botti. Advances in olefin metathesis: water sensitivity and catalyst synthesis. ArXiv, Sep 2016. URL: https://doi.org/10.20381/ruor-5416, doi:10.20381/ruor-5416. This article has 0 citations.

4. (botti2016advancesinolefin pages 3-4): Adrian Botti. Advances in olefin metathesis: water sensitivity and catalyst synthesis. ArXiv, Sep 2016. URL: https://doi.org/10.20381/ruor-5416, doi:10.20381/ruor-5416. This article has 0 citations.

5. (botti2016advancesinolefin pages 41-45): Adrian Botti. Advances in olefin metathesis: water sensitivity and catalyst synthesis. ArXiv, Sep 2016. URL: https://doi.org/10.20381/ruor-5416, doi:10.20381/ruor-5416. This article has 0 citations.

6. (zhao2026recentapplicationsof pages 1-2): He Zhao, ·. B. J. Venton, Parylene · Microfluidic, Immunoassay · Pyrolyzed, Neurotransmitter · Lig, and B. Venton. Recent applications of parylene and pyrolyzed parylene in sensors and devices: a review. Analytical and Bioanalytical Chemistry, 418:499-512, Oct 2026. URL: https://doi.org/10.1007/s00216-025-06150-1, doi:10.1007/s00216-025-06150-1. This article has 2 citations and is from a peer-reviewed journal.

7. (zhao2026recentapplicationsof pages 2-5): He Zhao, ·. B. J. Venton, Parylene · Microfluidic, Immunoassay · Pyrolyzed, Neurotransmitter · Lig, and B. Venton. Recent applications of parylene and pyrolyzed parylene in sensors and devices: a review. Analytical and Bioanalytical Chemistry, 418:499-512, Oct 2026. URL: https://doi.org/10.1007/s00216-025-06150-1, doi:10.1007/s00216-025-06150-1. This article has 2 citations and is from a peer-reviewed journal.

8. (zhao2026recentapplicationsof media afcf53d0): He Zhao, ·. B. J. Venton, Parylene · Microfluidic, Immunoassay · Pyrolyzed, Neurotransmitter · Lig, and B. Venton. Recent applications of parylene and pyrolyzed parylene in sensors and devices: a review. Analytical and Bioanalytical Chemistry, 418:499-512, Oct 2026. URL: https://doi.org/10.1007/s00216-025-06150-1, doi:10.1007/s00216-025-06150-1. This article has 2 citations and is from a peer-reviewed journal.

9. (zhao2026recentapplicationsof pages 5-7): He Zhao, ·. B. J. Venton, Parylene · Microfluidic, Immunoassay · Pyrolyzed, Neurotransmitter · Lig, and B. Venton. Recent applications of parylene and pyrolyzed parylene in sensors and devices: a review. Analytical and Bioanalytical Chemistry, 418:499-512, Oct 2026. URL: https://doi.org/10.1007/s00216-025-06150-1, doi:10.1007/s00216-025-06150-1. This article has 2 citations and is from a peer-reviewed journal.
