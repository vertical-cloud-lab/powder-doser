# q1_heap_and_drum

Edison `job-futurehouse-paperqa3-high`, task `8ec69cd3-7fa4-4087-8f4a-2db155fa479a`, dispatched 2026-11-28T08:43:58Z.

## Query

Context: we run an open-source, 3D-printed (PLA) auger powder doser for self-driving labs in alloy discovery for additive manufacturing. A 25 mm OD tube with a 21 mm bore and a helical flight ends in a 3 mm outlet; a NEMA 11 stepper turns it at 1-109 rpm, servos tilt it 0-90 degrees, a solenoid taps it, and doses fall onto a 0.1 mg analytical balance. We record a dosing fingerprint (mass per revolution vs tilt and speed, mass per tap, afterflow, no-flow fraction) on 13 powders (NaCl, gas-atomized AlSi10Mg, silicon, rice flours, xanthan gum, carboxymethyl cellulose, BaCl2 dihydrate, fumed silica and others) and calibrate a LIGGGHTS DEM twin. Property labels from handbooks limit our models (angle-of-repose ranges 6-16 degrees wide), so we are designing ten small in-house tests built around the doser, each using a few grams and run on the same jar and day as the fingerprint: (1) heap angle of repose on a 20 mm fixed pedestal on the balance, photographed in silhouette; (2) bulk and tapped density in a 10 mL Class A cylinder filled by the auger and tapped by a cam drop of 3 mm at 250 taps/min, column height read by camera; (3) a servo tilting plate with an IMU: wall friction of a 25 mm powder-filled ring at 70-450 Pa on PLA, stainless steel and glass, and the start angle of 1-5 mm powder layers; (4) particle size and shape from backlit images with a Raspberry Pi HQ camera and a 0.12-1.8x zoom lens; (5) a 25 mm cup with 1-6 mm orifice discs and a servo gate emptying onto the balance (Beverloo fit, smallest orifice that flows, with and without taps); (6) humidity chambers held by saturated salt solutions (MgCl2, Mg(NO3)2, NaCl, KCl, silica gel) with SHT45 sensors, weighing uptake and dosing before and after; (7) a 40 mm by 15 mm rotating drum driven by the doser's stepper, 1-20 rpm; (8) unconfined yield strength of a 20 mm by 40 mm column from a split mould after 0.2-2 kPa consolidation, crushed by a lead-screw platen on a 100 g load cell; (9) a blade spreading a 0.1-0.2 mm layer over a 100 x 30 mm coupon at 10-100 mm/s; (10) a Faraday cup (aluminium cup in a grounded can) with a femtoamp op-amp charge amplifier under the doser outlet. For tests (1) and (7): what does the literature report on (a) fixed-base (pedestal) angle-of-repose tests compared with ISO 4324 funnel pouring, the lifting cylinder and the tilting box: the effect of base diameter relative to particle size (how many particle diameters before the angle stops depending on base size), pour height and rate, feeding from a screw instead of a funnel, image analysis of heap profiles versus the apex formula, repeatability (standard deviation over repeat pours) and inter-method differences; (b) small rotating drums (GranuDrum 84 mm, Revolution Powder Analyzer, and drums under 50 mm): the effect of drum diameter, depth and end-wall friction on the dynamic angle and avalanche statistics, the Froude-number regimes, the cohesive index definitions, and how many particle diameters a drum must span; (c) DEM studies that simulated these exact tests for calibration and how well the calibrated parameters transferred to other flows. Give numbers for table salt, gas-atomized metal AM powders (AlSi10Mg, 316L, Ti-6Al-4V) and fine cohesive powders.

## Answer

Question: Context: we run an open-source, 3D-printed (PLA) auger powder doser for self-driving labs in alloy discovery for additive manufacturing. A 25 mm OD tube with a 21 mm bore and a helical flight ends in a 3 mm outlet; a NEMA 11 stepper turns it at 1-109 rpm, servos tilt it 0-90 degrees, a solenoid taps it, and doses fall onto a 0.1 mg analytical balance. We record a dosing fingerprint (mass per revolution vs tilt and speed, mass per tap, afterflow, no-flow fraction) on 13 powders (NaCl, gas-atomized AlSi10Mg, silicon, rice flours, xanthan gum, carboxymethyl cellulose, BaCl2 dihydrate, fumed silica and others) and calibrate a LIGGGHTS DEM twin. Property labels from handbooks limit our models (angle-of-repose ranges 6-16 degrees wide), so we are designing ten small in-house tests built around the doser, each using a few grams and run on the same jar and day as the fingerprint: (1) heap angle of repose on a 20 mm fixed pedestal on the balance, photographed in silhouette; (2) bulk and tapped density in a 10 mL Class A cylinder filled by the auger and tapped by a cam drop of 3 mm at 250 taps/min, column height read by camera; (3) a servo tilting plate with an IMU: wall friction of a 25 mm powder-filled ring at 70-450 Pa on PLA, stainless steel and glass, and the start angle of 1-5 mm powder layers; (4) particle size and shape from backlit images with a Raspberry Pi HQ camera and a 0.12-1.8x zoom lens; (5) a 25 mm cup with 1-6 mm orifice discs and a servo gate emptying onto the balance (Beverloo fit, smallest orifice that flows, with and without taps); (6) humidity chambers held by saturated salt solutions (MgCl2, Mg(NO3)2, NaCl, KCl, silica gel) with SHT45 sensors, weighing uptake and dosing before and after; (7) a 40 mm by 15 mm rotating drum driven by the doser's stepper, 1-20 rpm; (8) unconfined yield strength of a 20 mm by 40 mm column from a split mould after 0.2-2 kPa consolidation, crushed by a lead-screw platen on a 100 g load cell; (9) a blade spreading a 0.1-0.2 mm layer over a 100 x 30 mm coupon at 10-100 mm/s; (10) a Faraday cup (aluminium cup in a grounded can) with a femtoamp op-amp charge amplifier under the doser outlet. For tests (1) and (7): what does the literature report on (a) fixed-base (pedestal) angle-of-repose tests compared with ISO 4324 funnel pouring, the lifting cylinder and the tilting box: the effect of base diameter relative to particle size (how many particle diameters before the angle stops depending on base size), pour height and rate, feeding from a screw instead of a funnel, image analysis of heap profiles versus the apex formula, repeatability (standard deviation over repeat pours) and inter-method differences; (b) small rotating drums (GranuDrum 84 mm, Revolution Powder Analyzer, and drums under 50 mm): the effect of drum diameter, depth and end-wall friction on the dynamic angle and avalanche statistics, the Froude-number regimes, the cohesive index definitions, and how many particle diameters a drum must span; (c) DEM studies that simulated these exact tests for calibration and how well the calibrated parameters transferred to other flows. Give numbers for table salt, gas-atomized metal AM powders (AlSi10Mg, 316L, Ti-6Al-4V) and fine cohesive powders.

## Literature Review: Fixed-Base Angle of Repose and Small Rotating Drum Tests for Powder Characterization

### 1(a). Fixed-Base (Pedestal) Angle of Repose Tests

#### Effect of Base Diameter Relative to Particle Size

The measured angle of repose on a fixed pedestal depends on the ratio of the base diameter (D_B) to the median particle diameter (D_50). Kajiyama et al. (2024) showed that the angle of repose tends to decrease as base width increases, following a power-function relationship; at D_B/D_50 ≈ 100 the angle was still measurably dependent on base size for their silica sands (kajiyama2024fundamentalstudyon pages 6-7). This implies that for the user's 20 mm pedestal and typical AM powders (D_50 ≈ 30–45 µm), the ratio D_B/D_50 ≈ 440–670 is comfortably in the size-independent regime. However, for coarse table salt (D_50 ≈ 300–500 µm) the ratio drops to 40–67, approaching the range where base-size effects become non-negligible. No universal threshold has been established in the literature, but the available data suggest that D_B/D_50 > 100–200 is a practical criterion for base-size independence.

#### Effect of Pour Height and Pour Rate

Madrid et al. (2022) demonstrated that increasing drop height decreases the fixed-base angle of repose nonlinearly for wood pellets. Below approximately 60–80 mm, the sensitivity was about 0.13° per mm of additional height; above 120 mm the angle stabilized near 23° (madrid2022determinationofthe pages 5-8). The physical explanation is that particles released from greater height acquire more kinetic energy before striking the pile, causing them to spread farther horizontally. The base material also matters substantially: a pellet-on-pellet base produced an angle approximately 10° greater than a stainless-steel base at comparable drop heights, because greater particle-to-base friction dissipates more impact energy (madrid2022determinationofthe pages 8-10). Pour rate has received less systematic study, but Hegde et al. (1985) emphasized that angle measurements are highly method-dependent and require rigidly defined conditions, including flow rate (hegde1985studiesofpowder pages 1-2).

#### Feeding from a Screw vs. a Funnel

No direct experimental comparison between auger/screw feeding and funnel pouring for angle-of-repose tests was identified in the retrieved literature. The ISO 4324 and ASTM C1444 standards specify funnel pouring with defined orifice diameter and height. A screw feeder delivers powder at a more continuous and controllable mass flow rate than gravity discharge from a funnel, which may reduce impact energy variability. However, the intermittent and pulsatile nature of auger delivery (especially at low rpm) could introduce periodic disturbances to the heap surface. Users employing auger feeding should therefore characterize and report the mass flow rate and ensure it falls within the low-energy regime where the angle is insensitive to feed rate.

#### Image Analysis of Heap Profiles vs. Apex Height-Diameter Formula

The classical formula θ = arctan(2H/D_base) assumes a perfect cone with apex centered over the base. Kajiyama et al. (2024) showed that the apex is often not centered, making single-direction observation insufficient; their 3D two-camera image analysis measured angles in 360 directions around the circumference, with the resulting mean angle (θ_2D) differing from the simple height-based estimate by only 0.04–0.08° for well-behaved silica sands (kajiyama2024fundamentalstudyon pages 5-6). However, Müller et al. (2021) noted that for cohesive or broadly graded materials, heap profiles are often non-conical, exhibiting convex curvature or segregation-induced shoulders. In such cases, linear regression on the heap profile captures the local steepest slope more accurately than the apex formula, while nonlinear fitting may be more robust when profiles are highly irregular (muller2021algorithmforthe pages 8-8). For silhouette-based measurement on a 20 mm pedestal, fitting a straight line to the heap profile between ~20% and ~80% of the heap height is recommended over using the apex formula alone.

#### Repeatability (Standard Deviation)

Duverger et al. (2024) provide the most comprehensive repeatability data from a DEM round-robin study. In a plane-strain lifting-cylinder configuration with 400 experimental samples, the mean angle of repose was 41.4° with a standard deviation of 1.28° (min 38.3°, max 46.3°). In the axisymmetric configuration with 50 samples, the mean was 35.3° with SD = 0.9° (min 33.3°, max 37.3°) (duverger2024investigationtechniquesand pages 29-31). DEM clump simulations over 100 samples reproduced these with SD ≈ 0.8–1.14°. Liu et al. (2005) reported ±0.5° accuracy for video-based rotating-drum angle measurements (liu2005experimentalstudyof pages 1-2). For AM powders, Muñiz-Lerma et al. (2018) reported static AoR standard deviations of ±3–4° for AlSi7Mg powders (munizlerma2018acomprehensiveapproach pages 8-11), while Brocksieper et al. (2026) reported GranuDrum avalanche-angle SDs of ±1.67° (316L), ±2.54° (Alloy 718), and ±1.90° (AlSi10Mg) (brocksieper2026investigationofflowability pages 4-5).

#### Inter-Method Differences

Duverger et al. (2024) found that the axisymmetric (conical heap) configuration gave an AoR approximately 6° lower than the plane-strain (wedge) configuration for the same granular material when using the JGS apex-based measurement method (41.4° vs. 35.3°). Using their more rigorous full-surface measurement method, the difference reduced to approximately 1% between configurations (duverger2024investigationtechniquesand pages 29-31). Chukwu and Akande's earlier comparison of apparatus types reported inter-method differences of approximately ±1–9° for agricultural materials (suman2013developmentandtesting pages 18-22). These findings confirm that inter-method differences can be substantial—on the order of 5–10°—and that the measurement protocol must be reported alongside the angle value.

---

### 1(b). Small Rotating Drums

#### Commercial Instruments: GranuDrum and Revolution Powder Analyzer

The **GranuDrum** (Granutools, Belgium) has an inner diameter of 84 mm and a depth (axial width) of 20 mm, with transparent coated-glass sidewalls. Total volume is ~110 mL; typical loading is 55 cm³ (50% fill). Images are acquired by CCD camera every 0.5–0.6 s, typically 50–100 images per speed step, at rotation speeds from 2 to 60 rpm (sande2024ontheinherent pages 4-5, preudhomme2021effectofcohesive pages 1-4, katagiri2026statisticalvariabilityof pages 4-6).

The **Revolution Powder Analyzer** (Mercury Scientific) has an inner drum radius of 25 mm (diameter 50 mm) and a width of 35 mm. It operates typically at 0.6 rpm in the avalanche regime, recording break energy, rest energy, and avalanche energy over ~150 avalanche events (sani2026efficientdemcalibration pages 2-4).

The user's proposed 40 mm diameter × 15 mm depth drum is intermediate between these two commercial instruments.

#### Cohesive Index Definitions

The GranuDrum **cohesive index (CI)** is computed from temporal fluctuations of the powder–air interface. For each horizontal position x along the interface, the standard deviation σ(x) of the interface position over time is calculated. CI is the mean of σ(x) averaged over the usable interface width: CI = (1/D_crop) Σ_x σ(x) (khazem2025flowabilityofgranular pages 7-10). CI is near zero for free-flowing powders and increases with cohesion. The GranuDrum also reports the **dynamic angle of repose** as the angle between a linear fit of the powder surface and the horizontal (preudhomme2021effectofcohesive pages 1-4, preudhomme2021effectofcohesivea pages 1-4).

Katagiri et al. (2026) demonstrated that the coefficient of variation (CV) of the dynamic angle of repose ranged from 0.095 to 0.186 for a cohesive metal powder, requiring 21–189 images for 3% relative precision at 1σ–3σ confidence. A contour-length-based irregularity index R had CV < 0.03 and required only 1–2 images, suggesting superior statistical stability (katagiri2026statisticalvariabilityof pages 4-6).

#### Effect of Drum Diameter on Dynamic Angle and Avalanche Statistics

Liu et al. (2005) tested glass beads (3 and 5 mm diameter) in drums of 200, 300, and 500 mm diameter. Increasing drum diameter generally produced slightly smaller upper and lower angles of repose. For 3 mm beads at filling degree 0.4: the lower angle decreased from ~27.3° (200 mm drum) to ~25.7° (500 mm drum), while the upper angle decreased from ~30.2° to ~27.0° (liu2005experimentalstudyof pages 2-4). The difference between upper and lower angles (Δθ) increased with d/D, indicating that finite drum-size effects preferentially amplify the upper angle.

Orozco et al. (2020) found via DEM that at fixed Froude number, smaller drums exhibit greater wall slip, reducing particle feed to the free surface and producing a less curved free surface. Their simulations spanned D/d ratios from 18.75 to 125 particle diameters, with the smallest ratio (18.75d) showing clear finite-size effects (orozco2020rheologyandscaling pages 29-32, orozco2020rheologyandscaling pages 5-9).

Wang et al. (2026) confirmed that normalized flowing-layer thickness follows a power law with rotation speed, but the exponent changes from 0.17 to 0.68 as D/d increases, demonstrating a measurable size-ratio effect that saturates at sufficiently large D/d (wang2026dryandcohesive pages 1-3, wang2026dryandcohesive pages 3-4).

#### Effect of Drum Depth and End-Wall Friction

Pol et al. (2025) provided the most direct treatment of end-wall effects in cohesive drums. They introduced two dimensionless characteristic lengths: λ_W = W/max(d, l_c) for axial width and λ_R = R/max(d, l_c) for radial dimension, where l_c is the **cohesive length** at which gravity balances cohesive stress. When W >> l_c, end-wall effects are weak and the surface is planar with continuous flow. When W ~ l_c, end walls become important, the surface becomes concave, and flow becomes intermittent with repeated avalanches. When R ~ l_c, the surface can become entirely convex with material rolling along the drum body (pol2025cohesivegranularmaterial pages 16-18, pol2025cohesivegranularmaterial pages 1-3, pol2025cohesivegranularmaterial pages 3-5). For the GranuDrum (20 mm depth), van der Sande et al. (2024) noted a wall-friction criterion that drum depth should exceed 6.4 mean particle radii (3.2 mean particle diameters) (sande2024ontheinherent pages 4-5). For fine AM powders (d ~ 30 µm), the GranuDrum's 20 mm depth represents ~667 particle diameters—well above this minimum.

#### Minimum Drum Size in Particle Diameters

No universal minimum has been established. The literature suggests:
- **Non-cohesive powders**: D/d > 40–100 is needed to minimize finite-size effects on angle measurements (liu2005experimentalstudyof pages 2-4, orozco2020rheologyandscaling pages 5-9). Santomaso et al. (2003) used D/d ~ 1000 and treated the material as a continuum (santomaso2003investigationofthe pages 3-4).
- **Cohesive powders**: The relevant length scale is the cohesive length l_c, not the particle diameter alone. The drum dimensions must exceed l_c, which can be much larger than d for strongly cohesive materials (pol2025cohesivegranularmaterial pages 16-18).
- For the user's 40 mm drum with ~30 µm AM powders, D/d ≈ 1300, which is well into the size-independent regime for non-cohesive behavior. For cohesive fine powders (e.g., fumed silica), l_c may approach millimeters, making the 40 mm drum potentially marginal.

#### Froude Number Regimes

The Froude number Fr = ω²R/g governs flow regime transitions:
- **Slumping** (Fr < ~10⁻⁴): Discrete avalanches separated by rest periods (liu2005experimentalstudyof pages 1-2).
- **Rolling** (Fr ~ 10⁻⁴ to ~10⁻²): Continuous thin surface flow with nearly flat surface (santomaso2003investigationofthe pages 3-4, wang2026dryandcohesive pages 1-3).
- **Cascading** (Fr ~ 10⁻² to ~10⁻¹): S-shaped curved surface, rapid flow. Wang et al. (2026) reported the onset at tan β₀ ≈ 0.58 (≈30°) (wang2026dryandcohesive pages 1-3). Santomaso et al. (2003) observed rolling-to-cascading at Fr ≈ 10⁻³–8×10⁻³ for 337.5 µm glass beads (santomaso2003investigationofthe pages 3-4).
- **Cataracting** (Fr ~ 0.1–1): Particles become ballistic. Santomaso et al. (2003) observed cataracting at Fr ≈ 0.59 (santomaso2003investigationofthe pages 3-4).

Orozco et al. (2020) showed that Froude number alone is insufficient for scaling; their combined parameter ϒ = Fr^(1/4)(R/d)^(1/2)J (incorporating filling degree J) provided better collapse of flow variables across drum sizes (orozco2020rheologyandscaling pages 29-32). For the user's 40 mm drum at 1–20 rpm, Fr ranges from ~2×10⁻⁵ to ~9×10⁻³, spanning the slumping-to-rolling transition.

---

### 1(c). DEM Calibration and Parameter Transferability

#### DEM Simulations of AoR Tests

Roessler and Katterfeld (2019) calibrated LIGGGHTS DEM models of cohesive bulk materials using a simple lifting-cylinder angle-of-repose test with the simplified JKR model. They identified rolling friction, sliding friction, and cohesion energy density as the principal controlling parameters. Convex bending of the material column during the test was independent of lifting velocity and cylinder size, suggesting some robustness of calibration features (roessler2019demparametercalibration pages 10-11).

Duverger et al. (2024) compared DEM clump models and convex potential-particle models against 400 experimental AoR measurements. Clump models predicted AoR within ~4–8% of experiments (38.1° vs. 41.4° in plane strain; 33.9° vs. 35.3° in axisymmetric), while convex potential particles underestimated by ~16% (34.8° and 29.7°, respectively). The standard deviation of the DEM predictions (0.78–1.61°) was comparable to experiments (0.9–1.28°) (duverger2024investigationtechniquesand pages 29-31). They also found that AoR depends on sample size (number of particles), with an asymptotic difference of ~1.19° between plane-strain and axisymmetric configurations for large systems (duverger2024investigationtechniquesand pages 34-35, duverger2024investigationtechniquesand pages 35-36).

#### DEM Calibration Using Rotating Drums for AM Powders

Sani et al. (2026) calibrated DEM models for Inconel 718 and Ti-6Al-4V using the Revolution Powder Analyzer (50 mm diameter drum). They used Froude-number scaling to reduce the simulated drum radius by 5× while preserving dynamic similarity. Calibrated parameters were: Inconel 718—particle friction 0.76, rolling friction 0.08, surface energy 0.16 mJ/m²; Ti-6Al-4V—friction 0.78, rolling friction 0.14, surface energy 0.015 mJ/m². Simulated vs. experimental energy differences were 0.04–0.42% for Inconel 718 and 0.25–3.83% for Ti-6Al-4V (sani2026efficientdemcalibration pages 8-10). The scaling validation showed a linear relationship between bulk-energy responses and drum radius across tested scaling factors (sani2026efficientdemcalibration pages 12-13).

#### Transferability of Calibrated Parameters

The literature consistently cautions that DEM parameters calibrated on one test may not transfer reliably to other flow configurations:

- Marigo and Stitt (2015) emphasized that angle-of-repose calibration is non-unique: multiple parameter combinations can produce the same pile angle but fail in rotating-drum or dynamic-impact scenarios (marigo2015discreteelementmethod pages 3-5).
- Lupo et al. (2021) found that bulk calibration using AoR and unconfined yield strength could not simultaneously satisfy both tests with a single parameter set for cohesive SLS powders, recommending direct measurement of surface energy over phenomenological fitting (lupo2021calibrationofdem pages 2-3, lupo2021calibrationofdem pages 1-2).
- Sani et al. (2026) explicitly stated that future work is needed to verify whether rotating-drum-calibrated parameters transfer to recoating/spreading dynamics (sani2026efficientdemcalibration pages 1-2, sani2026efficientdemcalibration pages 12-13).
- Avrampos and Vosniakos (2024) noted that combining angle-of-avalanche and angle-of-repose tests improves confidence in parameter adequacy, as they probe different force balances (avrampos2024astudyon pages 9-10).

The emerging consensus is that multi-test calibration (e.g., AoR + rotating drum + spreading) is necessary, and that parameters should be validated in the target process rather than assumed transferable.

---

### Numerical Data for Specific Powders

#### Gas-Atomized Metal AM Powders

| Powder | Static AoR (°) | GranuDrum Avalanche Angle (°) | Dynamic AoR Range (°) | Source |
|--------|----------------|-------------------------------|----------------------|--------|
| 316L SS | — | 36.0 ± 1.7 | Lowest CI across speeds | Brocksieper et al. 2026 |
| AlSi10Mg | — | 39.2 ± 1.9 | — | Brocksieper et al. 2026 |
| Alloy 718 | — | 45.5 ± 2.5 | — | Brocksieper et al. 2026 |
| AlSi7Mg (Powder B, coarse spherical) | 26 ± 3 | — | 26–36 (2–20 rpm) | Muñiz-Lerma et al. 2018 |
| AlSi7Mg (Powder C, fine irregular) | 39 ± 4 | — | 35–38 (2–20 rpm) | Muñiz-Lerma et al. 2018 |
| Ti-6Al-4V (GA, spherical) | 27.1 | 33.4 (avalanche) | — | Mehrabi et al. 2023 |
| Ti-6Al-4V (HDH, irregular) | 37.6 | 46.5 (avalanche) | — | Mehrabi et al. 2023 |

(brocksieper2026investigationofflowability pages 4-5, munizlerma2018acomprehensiveapproach pages 8-11, mehrabi2023aninvestigationof pages 4-6)

#### Table Salt (NaCl)

Sea salt samples showed kinetic angles of repose ranging from 42.5° to 53.5° (rough surface) and static angles from 16° to 66° depending heavily on surface material (smiechowska2021selectedqualitycharacteristics pages 4-5). Hegde et al. (1985) measured both static and dynamic AoR for NaCl sieve fractions (125–425 µm) and noted that dynamic AoR was larger than static AoR, contrary to the usual expectation; exact numerical values were presented in figures rather than tables (hegde1985studiesofpowder pages 1-2, hegde1985studiesofpowder pages 2-3). Handbook values for granular NaCl (table salt, ~300–600 µm) typically range from 32° to 40° for the static funnel method.

#### Fine Cohesive Powders

Macho et al. (2020) reported AoR > 40° for flour samples using fixed-base funnel methods, indicating poor flowability, while glass beads with high circularity had significantly lower AoR (muller2021algorithmforthe pages 8-8). For the user's materials: fumed silica is extremely cohesive (AoR typically > 50°, often unmeasurable by funnel methods); xanthan gum and carboxymethyl cellulose are similarly cohesive with reported AoR values of 45–55° in the food powder literature.

---

### Summary and Recommendations for the User's Setup

1. **20 mm pedestal AoR**: For AM powders (D_50 ~ 30–45 µm), the D_B/D_50 ratio of ~440–670 is well above the ~100 threshold where base-size effects diminish (kajiyama2024fundamentalstudyon pages 6-7). For NaCl (~300 µm), D_B/D_50 ≈ 67, which is marginal. Silhouette image analysis with profile fitting is preferable to the apex formula for non-conical heaps (muller2021algorithmforthe pages 8-8).

2. **40 mm × 15 mm rotating drum**: This is smaller than the GranuDrum (84 mm × 20 mm) and comparable to the RPA (50 mm × 35 mm). For AM powders, D/d ≈ 1300, well above finite-size thresholds. For cohesive powders, the cohesive length l_c becomes the relevant scale; the 15 mm depth may be marginal for strongly cohesive materials where l_c approaches several mm (pol2025cohesivegranularmaterial pages 16-18). End-wall friction from the transparent viewing windows should be characterized, as it can alter flow regime transitions. At 1–20 rpm, the drum operates in the slumping-to-rolling transition (Fr ~ 2×10⁻⁵ to 9×10⁻³).

3. **DEM calibration**: Using both the heap AoR and the rotating drum simultaneously for calibration is strongly recommended, as single-test calibration is non-unique (marigo2015discreteelementmethod pages 3-5, lupo2021calibrationofdem pages 2-3). Transfer to spreading or hopper discharge should be validated independently (sani2026efficientdemcalibration pages 1-2). The LIGGGHTS simplified JKR model with rolling friction, sliding friction, and cohesion energy density as calibration parameters is a well-established approach (roessler2019demparametercalibration pages 10-11). Froude-number scaling enables computational cost reduction when simulating the rotating drum (sani2026efficientdemcalibration pages 8-10, sani2026efficientdemcalibration pages 2-4).

References

1. (kajiyama2024fundamentalstudyon pages 6-7): Shintaro Kajiyama, Yukio Nakata, and Hitoshi Nakase. Fundamental study on the effect of grain size distribution on angle of repose. E3S Web of Conferences, 544:01007, Jan 2024. URL: https://doi.org/10.1051/e3sconf/202454401007, doi:10.1051/e3sconf/202454401007. This article has 7 citations and is from a peer-reviewed journal.

2. (madrid2022determinationofthe pages 5-8): Marcos A. Madrid, José M. Fuentes, Francisco Ayuga, and Eutiquio Gallego. Determination of the angle of repose and coefficient of rolling friction for wood pellets. Agronomy, 12:424, Feb 2022. URL: https://doi.org/10.3390/agronomy12020424, doi:10.3390/agronomy12020424. This article has 27 citations and is from a peer-reviewed journal.

3. (madrid2022determinationofthe pages 8-10): Marcos A. Madrid, José M. Fuentes, Francisco Ayuga, and Eutiquio Gallego. Determination of the angle of repose and coefficient of rolling friction for wood pellets. Agronomy, 12:424, Feb 2022. URL: https://doi.org/10.3390/agronomy12020424, doi:10.3390/agronomy12020424. This article has 27 citations and is from a peer-reviewed journal.

4. (hegde1985studiesofpowder pages 1-2): Ramachandra P. Hegde, J.L. Rheingold, S. Welch, and C.T. Rhodes. Studies of powder flow using a recording powder flowmeter and measurement of the dynamic angle of repose. Journal of pharmaceutical sciences, 74 1:11-5, Jan 1985. URL: https://doi.org/10.1002/jps.2600740104, doi:10.1002/jps.2600740104. This article has 47 citations and is from a domain leading peer-reviewed journal.

5. (kajiyama2024fundamentalstudyon pages 5-6): Shintaro Kajiyama, Yukio Nakata, and Hitoshi Nakase. Fundamental study on the effect of grain size distribution on angle of repose. E3S Web of Conferences, 544:01007, Jan 2024. URL: https://doi.org/10.1051/e3sconf/202454401007, doi:10.1051/e3sconf/202454401007. This article has 7 citations and is from a peer-reviewed journal.

6. (muller2021algorithmforthe pages 8-8): Dominik Müller, Eric Fimbinger, and Clemens Brand. Algorithm for the determination of the angle of repose in bulk material analysis. Powder Technology, 383:598-605, May 2021. URL: https://doi.org/10.1016/j.powtec.2021.01.010, doi:10.1016/j.powtec.2021.01.010. This article has 113 citations and is from a domain leading peer-reviewed journal.

7. (duverger2024investigationtechniquesand pages 29-31): Sacha Duverger, Vasileios Angelidakis, Sadegh Nadimi, Stefano Utili, Stéphane Bonelli, Pierre Philippe, and Jérôme Duriez. Investigation techniques and physical aspects of the angle of repose of granular matter. Granular Matter, 26:1-26, Jan 2024. URL: https://doi.org/10.1007/s10035-023-01378-z, doi:10.1007/s10035-023-01378-z. This article has 21 citations and is from a peer-reviewed journal.

8. (liu2005experimentalstudyof pages 1-2): Xiao Yan Liu, E. Specht, and J. Mellmann. Experimental study of the lower and upper angles of repose of granular materials in rotating drums. Powder Technology, 154:125-131, Jul 2005. URL: https://doi.org/10.1016/j.powtec.2005.04.040, doi:10.1016/j.powtec.2005.04.040. This article has 186 citations and is from a domain leading peer-reviewed journal.

9. (munizlerma2018acomprehensiveapproach pages 8-11): Jose Alberto Muñiz-Lerma, Amy Nommeots-Nomm, Kristian Edmund Waters, and Mathieu Brochu. A comprehensive approach to powder feedstock characterization for powder bed fusion additive manufacturing: a case study on alsi7mg. Materials, 11:2386, Nov 2018. URL: https://doi.org/10.3390/ma11122386, doi:10.3390/ma11122386. This article has 173 citations.

10. (brocksieper2026investigationofflowability pages 4-5): Tim Robert Brocksieper, Tobias Grimm, and Jan T. Sehrt. Investigation of flowability and spreadability of metal powders for powder bed fusion additive manufacturing. Progress in Additive Manufacturing, 11:6661-6673, Apr 2026. URL: https://doi.org/10.1007/s40964-026-01690-z, doi:10.1007/s40964-026-01690-z. This article has 4 citations and is from a peer-reviewed journal.

11. (suman2013developmentandtesting pages 18-22): R SUMAN. Development and testing of an apparatus for digital measurement of the angle of repose of granular materials. Unknown journal, 2013.

12. (sande2024ontheinherent pages 4-5): P. Christian van der Sande, Kaiqiao Wu, Rens Kamphorst, Evert C. Wagner, Gabrie M. H. Meesters, and J. Ruud van Ommen. On the inherent correlation between the fluidization and flow properties of cohesive powders. AIChE Journal, Dec 2024. URL: https://doi.org/10.1002/aic.18706, doi:10.1002/aic.18706. This article has 17 citations and is from a peer-reviewed journal.

13. (preudhomme2021effectofcohesive pages 1-4): N Preud'Homme, E Opsomer, F Francqui, and A Neveu. Effect of cohesive forces on granular flows in rotating drum: linking experiments and simulations. Unknown journal, 2021.

14. (katagiri2026statisticalvariabilityof pages 4-6): Jun Katagiri, Masahiro Kusano, and Makoto Watanabe. Statistical variability of image-derived observables in rotating-drum tests of a cohesive metal powder: dynamic angle of repose versus contour-length statistics. Powders, 5:27, Jul 2026. URL: https://doi.org/10.3390/powders5030027, doi:10.3390/powders5030027. This article has 0 citations.

15. (sani2026efficientdemcalibration pages 2-4): Negar Sani, Johannes Quist, Sofia Kazi, Gowtham Soundarapandiyan, Gustav Kettil, Laura Cordova, Eduard Hryha, and Fredrik Edelvik. Efficient dem calibration of am powders using a rotating drum through froude number scaling. Progress in Additive Manufacturing, 11:5411-5425, Apr 2026. URL: https://doi.org/10.1007/s40964-026-01627-6, doi:10.1007/s40964-026-01627-6. This article has 2 citations and is from a peer-reviewed journal.

16. (khazem2025flowabilityofgranular pages 7-10): Reem Khazem, Julien Colin, Joel Casalinho, John Pachón-Morales, and François Puel. Flowability of granular materials in a rotating drum: investigation of relevant flow descriptors. Powder Technology, 464:121231, Oct 2025. URL: https://doi.org/10.1016/j.powtec.2025.121231, doi:10.1016/j.powtec.2025.121231. This article has 7 citations and is from a domain leading peer-reviewed journal.

17. (preudhomme2021effectofcohesivea pages 1-4): N Preud'Homme, E Opsomer, F Francqui, and A Neveu. Effect of cohesive forces on granular flows in rotating drum: linking experiments and simulations. Unknown journal, 2021.

18. (liu2005experimentalstudyof pages 2-4): Xiao Yan Liu, E. Specht, and J. Mellmann. Experimental study of the lower and upper angles of repose of granular materials in rotating drums. Powder Technology, 154:125-131, Jul 2005. URL: https://doi.org/10.1016/j.powtec.2005.04.040, doi:10.1016/j.powtec.2005.04.040. This article has 186 citations and is from a domain leading peer-reviewed journal.

19. (orozco2020rheologyandscaling pages 29-32): Luisa Fernanda Orozco, Jean-Yves Delenne, Philippe Sornay, and Farhang Radjai. Rheology and scaling behavior of cascading granular flows in rotating drums. Journal of Rheology, 64:915-931, Jul 2020. URL: https://doi.org/10.1122/1.5143023, doi:10.1122/1.5143023. This article has 32 citations and is from a domain leading peer-reviewed journal.

20. (orozco2020rheologyandscaling pages 5-9): Luisa Fernanda Orozco, Jean-Yves Delenne, Philippe Sornay, and Farhang Radjai. Rheology and scaling behavior of cascading granular flows in rotating drums. Journal of Rheology, 64:915-931, Jul 2020. URL: https://doi.org/10.1122/1.5143023, doi:10.1122/1.5143023. This article has 32 citations and is from a domain leading peer-reviewed journal.

21. (wang2026dryandcohesive pages 1-3): Zhongrong Wang, Annan Zhou, Teng Man, Wantao Ding, and Herbert Huppert. Dry and cohesive granular flows in a rotating drum: flow dynamics and scaling behaviours. Journal of Fluid Mechanics, Jun 2026. URL: https://doi.org/10.1017/jfm.2026.11716, doi:10.1017/jfm.2026.11716. This article has 2 citations and is from a highest quality peer-reviewed journal.

22. (wang2026dryandcohesive pages 3-4): Zhongrong Wang, Annan Zhou, Teng Man, Wantao Ding, and Herbert Huppert. Dry and cohesive granular flows in a rotating drum: flow dynamics and scaling behaviours. Journal of Fluid Mechanics, Jun 2026. URL: https://doi.org/10.1017/jfm.2026.11716, doi:10.1017/jfm.2026.11716. This article has 2 citations and is from a highest quality peer-reviewed journal.

23. (pol2025cohesivegranularmaterial pages 16-18): Antonio Pol, Riccardo Artoni, and Patrick Richard. Cohesive granular material in a rotating drum: flow regimes and size effects. Journal of Fluid Mechanics, Mar 2025. URL: https://doi.org/10.1017/jfm.2025.26, doi:10.1017/jfm.2025.26. This article has 15 citations and is from a highest quality peer-reviewed journal.

24. (pol2025cohesivegranularmaterial pages 1-3): Antonio Pol, Riccardo Artoni, and Patrick Richard. Cohesive granular material in a rotating drum: flow regimes and size effects. Journal of Fluid Mechanics, Mar 2025. URL: https://doi.org/10.1017/jfm.2025.26, doi:10.1017/jfm.2025.26. This article has 15 citations and is from a highest quality peer-reviewed journal.

25. (pol2025cohesivegranularmaterial pages 3-5): Antonio Pol, Riccardo Artoni, and Patrick Richard. Cohesive granular material in a rotating drum: flow regimes and size effects. Journal of Fluid Mechanics, Mar 2025. URL: https://doi.org/10.1017/jfm.2025.26, doi:10.1017/jfm.2025.26. This article has 15 citations and is from a highest quality peer-reviewed journal.

26. (santomaso2003investigationofthe pages 3-4): A.C. Santomaso, Y.L. Ding, J.R. Lickiss, and D.W. York. Investigation of the granular behaviour in a rotating drum operated over a wide range of rotational speed. Chemical Engineering Research & Design, 81:936-945, Sep 2003. URL: https://doi.org/10.1205/026387603322482176, doi:10.1205/026387603322482176. This article has 79 citations and is from a peer-reviewed journal.

27. (roessler2019demparametercalibration pages 10-11): Thomas Roessler and André Katterfeld. Dem parameter calibration of cohesive bulk materials using a simple angle of repose test. Aug 2019. URL: https://doi.org/10.1016/j.partic.2018.08.005, doi:10.1016/j.partic.2018.08.005. This article has 214 citations and is from a peer-reviewed journal.

28. (duverger2024investigationtechniquesand pages 34-35): Sacha Duverger, Vasileios Angelidakis, Sadegh Nadimi, Stefano Utili, Stéphane Bonelli, Pierre Philippe, and Jérôme Duriez. Investigation techniques and physical aspects of the angle of repose of granular matter. Granular Matter, 26:1-26, Jan 2024. URL: https://doi.org/10.1007/s10035-023-01378-z, doi:10.1007/s10035-023-01378-z. This article has 21 citations and is from a peer-reviewed journal.

29. (duverger2024investigationtechniquesand pages 35-36): Sacha Duverger, Vasileios Angelidakis, Sadegh Nadimi, Stefano Utili, Stéphane Bonelli, Pierre Philippe, and Jérôme Duriez. Investigation techniques and physical aspects of the angle of repose of granular matter. Granular Matter, 26:1-26, Jan 2024. URL: https://doi.org/10.1007/s10035-023-01378-z, doi:10.1007/s10035-023-01378-z. This article has 21 citations and is from a peer-reviewed journal.

30. (sani2026efficientdemcalibration pages 8-10): Negar Sani, Johannes Quist, Sofia Kazi, Gowtham Soundarapandiyan, Gustav Kettil, Laura Cordova, Eduard Hryha, and Fredrik Edelvik. Efficient dem calibration of am powders using a rotating drum through froude number scaling. Progress in Additive Manufacturing, 11:5411-5425, Apr 2026. URL: https://doi.org/10.1007/s40964-026-01627-6, doi:10.1007/s40964-026-01627-6. This article has 2 citations and is from a peer-reviewed journal.

31. (sani2026efficientdemcalibration pages 12-13): Negar Sani, Johannes Quist, Sofia Kazi, Gowtham Soundarapandiyan, Gustav Kettil, Laura Cordova, Eduard Hryha, and Fredrik Edelvik. Efficient dem calibration of am powders using a rotating drum through froude number scaling. Progress in Additive Manufacturing, 11:5411-5425, Apr 2026. URL: https://doi.org/10.1007/s40964-026-01627-6, doi:10.1007/s40964-026-01627-6. This article has 2 citations and is from a peer-reviewed journal.

32. (marigo2015discreteelementmethod pages 3-5): Michele Marigo and Edmund Hugh Stitt. Discrete element method (dem) for industrial applications: comments on calibration and validation for the modelling of cylindrical pellets. Kona Powder and Particle Journal, 32:236-252, Jan 2015. URL: https://doi.org/10.14356/kona.2015016, doi:10.14356/kona.2015016. This article has 361 citations and is from a peer-reviewed journal.

33. (lupo2021calibrationofdem pages 2-3): Marco Lupo, Diego Barletta, Daniele Sofia, and Massimo Poletto. Calibration of dem for cohesive particles in the sls powder spreading process. Processes, 9:1715, Sep 2021. URL: https://doi.org/10.3390/pr9101715, doi:10.3390/pr9101715. This article has 16 citations.

34. (lupo2021calibrationofdem pages 1-2): Marco Lupo, Diego Barletta, Daniele Sofia, and Massimo Poletto. Calibration of dem for cohesive particles in the sls powder spreading process. Processes, 9:1715, Sep 2021. URL: https://doi.org/10.3390/pr9101715, doi:10.3390/pr9101715. This article has 16 citations.

35. (sani2026efficientdemcalibration pages 1-2): Negar Sani, Johannes Quist, Sofia Kazi, Gowtham Soundarapandiyan, Gustav Kettil, Laura Cordova, Eduard Hryha, and Fredrik Edelvik. Efficient dem calibration of am powders using a rotating drum through froude number scaling. Progress in Additive Manufacturing, 11:5411-5425, Apr 2026. URL: https://doi.org/10.1007/s40964-026-01627-6, doi:10.1007/s40964-026-01627-6. This article has 2 citations and is from a peer-reviewed journal.

36. (avrampos2024astudyon pages 9-10): Panagiotis Avrampos and George-Christopher Vosniakos. A study on powder spreading quality in powder bed fusion processes using discrete element method simulation. Journal of Manufacturing and Materials Processing, 8:101, May 2024. URL: https://doi.org/10.3390/jmmp8030101, doi:10.3390/jmmp8030101. This article has 10 citations.

37. (mehrabi2023aninvestigationof pages 4-6): Mozhdeh Mehrabi, Jabbar Gardy, Fatemeh A. Talebi, Amin Farshchi, Ali Hassanpour, and Andrew E. Bayly. An investigation of the effect of powder flowability on the powder spreading in additive manufacturing. Powder Technology, 413:117997, Jan 2023. URL: https://doi.org/10.1016/j.powtec.2022.117997, doi:10.1016/j.powtec.2022.117997. This article has 90 citations and is from a domain leading peer-reviewed journal.

38. (smiechowska2021selectedqualitycharacteristics pages 4-5): Maria Smiechowska, M. Ruszkowska, and Oliwia Olender. Selected quality characteristics of sea salt important during transport and storage. TransNav, the International Journal on Marine Navigation and Safety of Sea Transportation, 15:659-665, Jan 2021. URL: https://doi.org/10.12716/1001.15.03.21, doi:10.12716/1001.15.03.21. This article has 3 citations.

39. (hegde1985studiesofpowder pages 2-3): Ramachandra P. Hegde, J.L. Rheingold, S. Welch, and C.T. Rhodes. Studies of powder flow using a recording powder flowmeter and measurement of the dynamic angle of repose. Journal of pharmaceutical sciences, 74 1:11-5, Jan 1985. URL: https://doi.org/10.1002/jps.2600740104, doi:10.1002/jps.2600740104. This article has 47 citations and is from a domain leading peer-reviewed journal.
