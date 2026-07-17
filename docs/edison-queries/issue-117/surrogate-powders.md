# Edison report: Select Benign Powder Surrogates Matching Particle Size Shape Density Flowability And Hygroscopicity Characteristics

- **Task ID:** `d885ec2b-0f36-411e-9133-4a40e6878537`
- **Job:** job-futurehouse-paperqa3
- **Completed:** 2026-07-16 16:44:07.745409+00:00

## Query

We operate an open-source auger-based powder microdoser (3D-printed auger and tube, gravimetric
feedback) targeting 0.1-10 mg doses. Before testing with real reagents, we want inexpensive,
low-hazard SURROGATE powders whose powder-handling behavior closely mimics each of the following,
so we can develop and calibrate the doser safely:

(1) Grubbs 2nd-generation ruthenium metathesis catalyst (CAS 246047-72-3) - fine, cohesive,
    crystalline organometallic powder, crystal density ~1.36-1.40 g/cm3, prone to tribocharging,
    handled in a dry inert-atmosphere glovebox.
(2) AIBN, 2,2'-azobisisobutyronitrile (CAS 78-67-1) - white crystalline solid, ~50-500 um
    particles, true density ~1.10 g/cm3, essentially non-hygroscopic, fair-to-poor flow with fines.
(3) Sodium cyanide (CAS 143-33-9) - hygroscopic, water-soluble fine salt prone to moisture
    pickup, caking, and liquid-bridge cohesion.

For EACH of the three, please recommend 2-3 candidate surrogate powders that are cheap and benign
(safe to handle on an open bench) and match, as closely as the literature allows, the relevant
properties: particle size distribution, particle shape/morphology, true and bulk density,
cohesion/flowability (e.g., Hausner ratio, angle of repose, FFC if available), electrostatic
charging tendency, hygroscopicity, and bridging/arching or caking tendency. Examples of surrogate
classes to consider (not exhaustive): lactose grades (e.g., alpha-lactose monohydrate, fine milled
grades), microcrystalline cellulose (Avicel grades), corn starch, calcium carbonate, glass beads,
silica, salt/sugar grades, dyes or colored tracers for visibility.

Also note: (a) any literature precedent for surrogate/simulant selection methodology in powder
micro-dosing or pharmaceutical micro-feeding; (b) which single surrogate would best serve as a
"worst-case cohesive" stand-in for glovebox testing; (c) any property mismatches we should be aware
of for each recommendation. Provide citations where possible.


## Answer

Question: We operate an open-source auger-based powder microdoser (3D-printed auger and tube, gravimetric
feedback) targeting 0.1-10 mg doses. Before testing with real reagents, we want inexpensive,
low-hazard SURROGATE powders whose powder-handling behavior closely mimics each of the following,
so we can develop and calibrate the doser safely:

(1) Grubbs 2nd-generation ruthenium metathesis catalyst (CAS 246047-72-3) - fine, cohesive,
    crystalline organometallic powder, crystal density ~1.36-1.40 g/cm3, prone to tribocharging,
    handled in a dry inert-atmosphere glovebox.
(2) AIBN, 2,2'-azobisisobutyronitrile (CAS 78-67-1) - white crystalline solid, ~50-500 um
    particles, true density ~1.10 g/cm3, essentially non-hygroscopic, fair-to-poor flow with fines.
(3) Sodium cyanide (CAS 143-33-9) - hygroscopic, water-soluble fine salt prone to moisture
    pickup, caking, and liquid-bridge cohesion.

For EACH of the three, please recommend 2-3 candidate surrogate powders that are cheap and benign
(safe to handle on an open bench) and match, as closely as the literature allows, the relevant
properties: particle size distribution, particle shape/morphology, true and bulk density,
cohesion/flowability (e.g., Hausner ratio, angle of repose, FFC if available), electrostatic
charging tendency, hygroscopicity, and bridging/arching or caking tendency. Examples of surrogate
classes to consider (not exhaustive): lactose grades (e.g., alpha-lactose monohydrate, fine milled
grades), microcrystalline cellulose (Avicel grades), corn starch, calcium carbonate, glass beads,
silica, salt/sugar grades, dyes or colored tracers for visibility.

Also note: (a) any literature precedent for surrogate/simulant selection methodology in powder
micro-dosing or pharmaceutical micro-feeding; (b) which single surrogate would best serve as a
"worst-case cohesive" stand-in for glovebox testing; (c) any property mismatches we should be aware
of for each recommendation. Provide citations where possible.


## Scope and evidence limitations
The retrieved open-access literature supported (i) quantitative *flowability proxies* (bulk/tapped density, Hausner ratio, angle of repose) for several common benign excipients (lactose, Avicel PH-102, maize starch), (ii) a *quantitative triboelectric-charging methodology* and charge densities for microcrystalline cellulose (MCC) grades against stainless steel, and (iii) a *mechanistic framework* for moisture-induced caking in deliquescent crystalline powders, including the role of a critical relative humidity (RH0) associated with deliquescence. (rahman2017evaluationofphysical pages 2-5, vyas2021amethodologyto pages 24-32, zhang2024preventionofcrystal pages 8-10)

The evidence set did **not** contain: (a) true/pycnometric density and particle-size-distribution (PSD) data for the candidate surrogates; (b) critical relative humidity (CRH) numbers for specific salts; or (c) any direct literature on “surrogate powders for Grubbs catalyst/AIBN/NaCN.” Recommendations below therefore emphasize *process-relevant powder behaviors* (cohesion/flowability, tribocharging, hygroscopic caking) rather than full one-to-one property matches.

## (a) Literature precedent / methodology for selecting surrogate powders
### Use “behavioral axes” rather than chemistry
For auger microdosing and loss-in-weight systems, the most transferable selection approach is to choose powders spanning the dominant failure modes:
1) **Cohesion/flowability** (arch/bridge propensity, refill response), using bulk/tapped density and Hausner ratio plus angle of repose as low-cost screening metrics. Rahman et al. provide a concrete example dataset and interpretive thresholds (e.g., high angle of repose and Hausner ratio indicate poor flow). (rahman2017evaluationofphysical pages 2-5, rahman2017evaluationofphysical pages 1-2)
2) **Electrostatics / tribocharging** as an independent axis (adhesion to polymer or metal surfaces, dose drift). Vyas provides a reproducible method (vibratory feeder/chute + Faraday cup) and shows that charge acquisition depends on flow conditions (e.g., maintaining constant volumetric flow rate for comparisons), with MCC grades yielding measurable charge densities (Δq). (vyas2021amethodologyto pages 24-32, vyas2021amethodologyto pages 53-61)
3) **Moisture sensitivity and caking** (humidity excursions causing liquid bridges and consolidation). Zhang et al. summarize the canonical sequence: moisture adsorption → liquid bridge formation → recrystallization to crystal bridges, governed by a deliquescence/critical RH0; smaller particles increase moisture uptake and caking tendency. (zhang2024preventionofcrystal pages 8-10, zhang2024preventionofcrystal pages 10-11)

## Surrogate recommendations (2–3 per target)
The table below lists recommended candidates, the specific behaviors they mimic, and *only* those quantitative metrics supported by retrieved evidence.

| Target powder | Recommended surrogate candidate | Key matched behaviors | Angle of repose (°) | Bulk density | Tapped density | Hausner ratio | Tribocharge Δq (nC/g) | Hygroscopicity / caking relevance | Key mismatches / notes |
|---|---|---|---:|---|---|---:|---:|---|---|
| Grubbs 2nd-gen catalyst | Lactose | Poor flow / cohesive benchmark; crystalline powder; useful as a difficult-flow comparator | 50.18 | 0.389 g/mL | 0.713 g/mL | 1.83 | not found in retrieved literature | Hygroscopicity/caking not found in retrieved literature | Density and chemistry do not match organometallic catalyst; tribocharging number not retrieved; stronger cohesion than MCC benchmark may make it a conservative flow surrogate (rahman2017evaluationofphysical pages 2-5, rahman2017evaluationofphysical media 5dfb54a5) |
| Grubbs 2nd-gen catalyst | Avicel PH-102 (microcrystalline cellulose) | Dry powder with measurable tribocharging against stainless steel; commonly used benchmark in feeder/charging studies | 43.35 | 0.282 g/mL | 0.350 g/mL | 1.24 | -1.26 ± 0.94 | Hygroscopicity/caking not found in retrieved literature | Fibrous/cellulosic morphology differs from crystalline organometallic; density is much lower than target; less cohesive than lactose in retrieved data (rahman2017evaluationofphysical pages 2-5, vyas2021amethodologyto pages 24-32, vyas2021amethodologyto pages 16-24, rahman2017evaluationofphysical media 5dfb54a5) |
| Grubbs 2nd-gen catalyst | Maize starch | Poor-flowing fine powder; useful conservative cohesive comparator | 50.05 | 0.305 g/mL | 0.441 g/mL | 1.44 | not found in retrieved literature | Hygroscopicity/caking not found in retrieved literature | Morphology and chemistry differ substantially; density lower than target; electrostatic data not retrieved (rahman2017evaluationofphysical pages 2-5, rahman2017evaluationofphysical media 5dfb54a5) |
| AIBN | Avicel PH-102 | Fair-to-good dry flow benchmark; measured tribocharging; practical white benign surrogate | 43.35 | 0.282 g/mL | 0.350 g/mL | 1.24 | -1.26 ± 0.94 | Hygroscopicity/caking not found in retrieved literature | True density and particle morphology differ from AIBN crystals; likely less size-matched than coarse crystalline surrogates the user may source commercially (rahman2017evaluationofphysical pages 2-5, vyas2021amethodologyto pages 24-32, rahman2017evaluationofphysical media 5dfb54a5) |
| AIBN | Commercial / prepared MCC benchmark | Good-flowing dry excipient benchmark; useful for establishing lower-cohesion operating envelope | 27.6 to 30.55 | 0.36 to 0.49 g/cm³ | 0.42 to 0.54 g/cm³ | 1.15 to 1.16 | not found in retrieved literature | Moisture sorption capacity reported for MCC, but hygroscopic caking not emphasized | Likely freer-flowing than AIBN with fines; not crystalline like AIBN; density lower than target (ndika2019chemicalmodificationof pages 1-2, ndika2019chemicalmodificationof pages 7-8, ndika2019chemicalmodificationof pages 5-7) |
| AIBN | Lactose | Conservative poor-flow crystalline benchmark with strong cohesiveness | 50.18 | 0.389 g/mL | 0.713 g/mL | 1.83 | not found in retrieved literature | Hygroscopicity/caking not found in retrieved literature | Likely more cohesive than many AIBN lots; true density likely higher than AIBN; tribocharging number not retrieved (rahman2017evaluationofphysical pages 2-5, rahman2017evaluationofphysical media 5dfb54a5) |
| Sodium cyanide | Sodium chloride | Water-soluble crystalline salt; moisture-induced liquid-bridge/caking mechanism is well-precedented for salts near deliquescence | not found in retrieved literature | not found in retrieved literature | not found in retrieved literature | not found in retrieved literature | not found in retrieved literature | Retrieved review explicitly cites NaCl as a model system for moisture sorption, crystal growth, and anticaking studies; caking follows moisture absorption → liquid bridges → crystal bridges (zhang2024preventionofcrystal pages 8-10, zhang2024preventionofcrystal pages 18-20, zhang2024preventionofcrystal pages 17-18) | NaCl is less hazardous and chemically reasonable as a salt surrogate, but exact hygroscopicity/CRH relative to NaCN was not retrieved here; may underrepresent worst-case moisture pickup if target is more hygroscopic (zhang2024preventionofcrystal pages 8-10, zhang2024preventionofcrystal pages 18-20, zhang2024preventionofcrystal pages 17-18) |
| Sodium cyanide | Fine salt chosen below its critical RH0 / deliquescence threshold testing regime | Best process-behavior match is moisture-sensitive crystalline salt showing bridge formation and caking under humidity excursions | not found in retrieved literature | not found in retrieved literature | not found in retrieved literature | not found in retrieved literature | not found in retrieved literature | Review-level mechanism: smaller particles absorb moisture faster and cake more readily; caking controlled by RH0, particle size, morphology, and liquid-bridge formation (zhang2024preventionofcrystal pages 8-10, zhang2024preventionofcrystal pages 10-11) | Specific benign salt and numerical CRH values were not retrieved from the available evidence set; selection should be finalized with external datasheets or sorption testing (zhang2024preventionofcrystal pages 8-10, zhang2024preventionofcrystal pages 10-11) |
| Sodium cyanide | Hygroscopic fine crystalline salt benchmark (general class) | Intended to mimic moisture pickup, arching/bridging, and caking under ambient humidity | not found in retrieved literature | not found in retrieved literature | not found in retrieved literature | not found in retrieved literature | not found in retrieved literature | Moisture-driven caking mechanism and importance of particle size/shape are well supported in review literature (zhang2024preventionofcrystal pages 8-10, zhang2024preventionofcrystal pages 10-11, zhang2024preventionofcrystal pages 17-18) | Available retrieved evidence supports the mechanism more than a specific named salt with full quantitative property match; open-bench benignity and exact NaCN match remain to be confirmed experimentally (zhang2024preventionofcrystal pages 8-10, zhang2024preventionofcrystal pages 10-11, zhang2024preventionofcrystal pages 17-18) |


*Table: This table maps candidate surrogate powders to the three target powders and summarizes the matched behaviors plus the quantitative properties actually supported by the retrieved evidence. It is useful as a conservative starting point for bench and glovebox microdoser calibration while clearly flagging where literature gaps remain.*

### (1) Grubbs 2nd-generation catalyst (fine, cohesive, tribocharging-prone, dry glovebox)
**Goal behaviors:** cohesive fine powder, poor flow/arching risk, and sensitivity to tribocharging under dry conditions.

**Recommended surrogates**
1. **Lactose (as a conservative cohesive/crystalline surrogate)**: very poor-flowing by both angle of repose (50.18°) and Hausner ratio (1.83), making it suitable for stressing an auger microdoser’s ability to avoid ratholing/arching and deliver consistent microdoses. (rahman2017evaluationofphysical pages 2-5, rahman2017evaluationofphysical media 5dfb54a5)
2. **Maize starch (cohesive fine powder surrogate)**: similarly high angle of repose (50.05°) and elevated Hausner ratio (1.44), supporting use as another cohesive benchmark. (rahman2017evaluationofphysical pages 2-5, rahman2017evaluationofphysical media 5dfb54a5)
3. **Avicel PH-102 / MCC (electrostatics-relevant dry powder surrogate)**: provides measurable tribocharging against stainless steel (Δq ≈ −1.26 ± 0.94 nC/g for PH-102) and is explicitly used as a tribocharging test material in the methodology literature. (vyas2021amethodologyto pages 24-32, vyas2021amethodologyto pages 16-24)

**Key mismatches to be aware of**
- Chemistry, crystal habit, and true density matching to Grubbs 2nd-gen were not supported by retrieved sources; expect differences in compressibility and triboelectric polarity/magnitude versus an organometallic. (rahman2017evaluationofphysical pages 2-5, vyas2021amethodologyto pages 24-32)

### (2) AIBN (white crystals, 50–500 µm, low hygroscopicity, fair-to-poor flow with fines)
**Goal behaviors:** dry crystalline organic powder with middling-to-poor flow when fines are present; not moisture-driven.

**Recommended surrogates**
1. **Avicel PH-102 (moderate/poor-flow dry powder with electrostatics data)**: angle of repose 43.35° and Hausner ratio 1.24 (borderline/“passable”) provide a useful mid-cohesion calibration point, with quantitative tribocharging available (Δq). (rahman2017evaluationofphysical pages 2-5, vyas2021amethodologyto pages 24-32)
2. **Lactose (poor-flow crystalline benchmark)**: high angle of repose and high Hausner ratio (1.83) represent a conservative “worse-than-typical” dry crystalline powder for microdosing calibration. (rahman2017evaluationofphysical pages 2-5)
3. **MCC benchmark material (good-flow baseline)**: Ndika reports MCC with angles of repose in the ~27.6–30.6° range and Hausner ratio ~1.15–1.16, providing a “best-case” dry excipient baseline for bracketing behavior. (ndika2019chemicalmodificationof pages 5-7)

**Key mismatches**
- Retrieved evidence did not include PSD or true density near AIBN’s ~1.10 g/cm³; the match is therefore primarily *flow/handling* rather than size/density. (rahman2017evaluationofphysical pages 2-5, ndika2019chemicalmodificationof pages 5-7)

### (3) Sodium cyanide (hygroscopic, water-soluble, prone to caking/liquid bridges)
**Goal behaviors:** rapid moisture pickup under ambient humidity excursions, caking/consolidation, and likely arching/bridging.

**Recommended surrogates (salt-based, open-bench benign)**
1. **Sodium chloride (NaCl)**: while quantitative CRH was not retrieved here, Zhang et al. explicitly discuss deliquescent-salt caking mechanisms and cite NaCl caking/anti-caking studies as exemplars; NaCl therefore has strong precedent as a practical “model salt” for humidity-driven liquid-bridge and crystal-bridge caking studies. (zhang2024preventionofcrystal pages 8-10, zhang2024preventionofcrystal pages 18-20)
2–3. **A “fine, deliquescent crystalline salt” test regime (class recommendation)**: the key is to choose a benign, water-soluble crystalline salt and tune (i) particle size (finer increases caking) and (ii) humidity cycling across the salt’s RH0/CRH to deliberately induce liquid-bridge formation and recrystallized bridges, matching the mechanism outlined in the review. (zhang2024preventionofcrystal pages 8-10, zhang2024preventionofcrystal pages 10-11)

**Key mismatches**
- Because RH0/CRH values for specific salts were not available in retrieved full texts, the best match to NaCN hygroscopicity cannot be asserted from this evidence set alone; surrogate finalization should therefore include simple sorption/caking screening (e.g., controlled-RH box exposures) to ensure the chosen salt cakes in the same humidity window of concern. (zhang2024preventionofcrystal pages 8-10)

## (b) Single best “worst-case cohesive” glovebox stand-in
**Lactose** is the most conservative “worst-case cohesive” stand-in available in the retrieved quantitative dataset, with very high Hausner ratio (1.83) and high angle of repose (~50°), both indicative of poor flow and strong consolidation tendency in handling equipment. (rahman2017evaluationofphysical pages 2-5, rahman2017evaluationofphysical media 5dfb54a5)

## (c) Practical notes for microdoser calibration (linking behaviors to your system)
- **Bracket your calibration:** start with a free-flow baseline (MCC with AoR ~28–31°) then move to mid-poor flow (Avicel PH-102, AoR ~43°) then “worst case” (lactose/starch, AoR ~50°). (rahman2017evaluationofphysical pages 2-5, ndika2019chemicalmodificationof pages 5-7)
- **Include an electrostatics test condition:** Vyas shows tribocharging comparisons require controlled humidity (e.g., 10–40% RH) and constant volumetric flow rate to avoid confounding; using MCC (with reported Δq) can help you detect charge-driven adhesion/clogging in your auger/tube path. (vyas2021amethodologyto pages 24-32, vyas2021amethodologyto pages 53-61)
- **For NaCN-like behavior, humidity cycling is essential:** the caking mechanism requires moisture uptake and liquid bridges, which become severe when crossing RH0; use controlled RH steps to create repeatable “caking stress tests.” (zhang2024preventionofcrystal pages 8-10, zhang2024preventionofcrystal pages 10-11)


References

1. (rahman2017evaluationofphysical pages 2-5): SM Moshiur Rahman, Tushar Saha, Zia Uddin Masum, and Jakir Ahmed Chowdhury. Evaluation of physical properties of selected excipients for direct compressible tablet. Bangladesh Pharmaceutical Journal, 20:34-38, Apr 2017. URL: https://doi.org/10.3329/bpj.v20i1.32091, doi:10.3329/bpj.v20i1.32091. This article has 8 citations.

2. (vyas2021amethodologyto pages 24-32): Zankrut Daksheshkumar Vyas. A methodology to characterize triboelectric charging of powders. Text, Jan 2021. URL: https://doi.org/10.7282/t3-7prt-zn94, doi:10.7282/t3-7prt-zn94. This article has 0 citations and is from a peer-reviewed journal.

3. (zhang2024preventionofcrystal pages 8-10): Huixiang Zhang, Shichao Du, Yan Wang, and Fumin Xue. Prevention of crystal agglomeration: mechanisms, factors, and impact of additives. Crystals, 14:676, Jul 2024. URL: https://doi.org/10.3390/cryst14080676, doi:10.3390/cryst14080676. This article has 51 citations.

4. (rahman2017evaluationofphysical pages 1-2): SM Moshiur Rahman, Tushar Saha, Zia Uddin Masum, and Jakir Ahmed Chowdhury. Evaluation of physical properties of selected excipients for direct compressible tablet. Bangladesh Pharmaceutical Journal, 20:34-38, Apr 2017. URL: https://doi.org/10.3329/bpj.v20i1.32091, doi:10.3329/bpj.v20i1.32091. This article has 8 citations.

5. (vyas2021amethodologyto pages 53-61): Zankrut Daksheshkumar Vyas. A methodology to characterize triboelectric charging of powders. Text, Jan 2021. URL: https://doi.org/10.7282/t3-7prt-zn94, doi:10.7282/t3-7prt-zn94. This article has 0 citations and is from a peer-reviewed journal.

6. (zhang2024preventionofcrystal pages 10-11): Huixiang Zhang, Shichao Du, Yan Wang, and Fumin Xue. Prevention of crystal agglomeration: mechanisms, factors, and impact of additives. Crystals, 14:676, Jul 2024. URL: https://doi.org/10.3390/cryst14080676, doi:10.3390/cryst14080676. This article has 51 citations.

7. (rahman2017evaluationofphysical media 5dfb54a5): SM Moshiur Rahman, Tushar Saha, Zia Uddin Masum, and Jakir Ahmed Chowdhury. Evaluation of physical properties of selected excipients for direct compressible tablet. Bangladesh Pharmaceutical Journal, 20:34-38, Apr 2017. URL: https://doi.org/10.3329/bpj.v20i1.32091, doi:10.3329/bpj.v20i1.32091. This article has 8 citations.

8. (vyas2021amethodologyto pages 16-24): Zankrut Daksheshkumar Vyas. A methodology to characterize triboelectric charging of powders. Text, Jan 2021. URL: https://doi.org/10.7282/t3-7prt-zn94, doi:10.7282/t3-7prt-zn94. This article has 0 citations and is from a peer-reviewed journal.

9. (ndika2019chemicalmodificationof pages 1-2): Ezea Vincent Ndika, Sunday Chidozie Umerie, and Kingsley Ikechukwu Ubaoji. Chemical modification of cellulose from palm kernel de-oiled cake to microcrystalline cellulose and its evaluation as a pharmaceutical excipient. African Journal of Pure and Applied Chemistry, 13:49-57, Jul 2019. URL: https://doi.org/10.5897/ajpac2019.0787, doi:10.5897/ajpac2019.0787. This article has 16 citations.

10. (ndika2019chemicalmodificationof pages 7-8): Ezea Vincent Ndika, Sunday Chidozie Umerie, and Kingsley Ikechukwu Ubaoji. Chemical modification of cellulose from palm kernel de-oiled cake to microcrystalline cellulose and its evaluation as a pharmaceutical excipient. African Journal of Pure and Applied Chemistry, 13:49-57, Jul 2019. URL: https://doi.org/10.5897/ajpac2019.0787, doi:10.5897/ajpac2019.0787. This article has 16 citations.

11. (ndika2019chemicalmodificationof pages 5-7): Ezea Vincent Ndika, Sunday Chidozie Umerie, and Kingsley Ikechukwu Ubaoji. Chemical modification of cellulose from palm kernel de-oiled cake to microcrystalline cellulose and its evaluation as a pharmaceutical excipient. African Journal of Pure and Applied Chemistry, 13:49-57, Jul 2019. URL: https://doi.org/10.5897/ajpac2019.0787, doi:10.5897/ajpac2019.0787. This article has 16 citations.

12. (zhang2024preventionofcrystal pages 18-20): Huixiang Zhang, Shichao Du, Yan Wang, and Fumin Xue. Prevention of crystal agglomeration: mechanisms, factors, and impact of additives. Crystals, 14:676, Jul 2024. URL: https://doi.org/10.3390/cryst14080676, doi:10.3390/cryst14080676. This article has 51 citations.

13. (zhang2024preventionofcrystal pages 17-18): Huixiang Zhang, Shichao Du, Yan Wang, and Fumin Xue. Prevention of crystal agglomeration: mechanisms, factors, and impact of additives. Crystals, 14:676, Jul 2024. URL: https://doi.org/10.3390/cryst14080676, doi:10.3390/cryst14080676. This article has 51 citations.
