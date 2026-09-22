# Edison feedback: servo-pinion gear stripping (issue #65)

- Job type: LITERATURE_HIGH
- Task id: `765aef1c-eae6-4ced-86e3-eac48ebb8a13`
- Status: success

Query asked how best to stop the 3D-printed servo-pinion teeth from stripping on the MG996R-driven mounting-plate tilt gears (metal vs printed gears, PLA/PETG/nylon, mount-bracket rigidity, gear geometry). Full query text in `servo_gear_stripping_query.py`.

---

Question: I am designing the tilt mechanism for a benchtop automated powder-dosing instrument. A flat "mounting plate" carrying a powder auger is tilted up and down about a hinge by TWO hobby servos (TowerPro MG996R, ~10 kg-cm stall torque, plastic-gear standard version). Each servo drives a 20-tooth pinion that meshes with a 40-tooth gear band integrated directly into the mounting-plate hinge lobe, giving a 2:1 reduction. The gears are spur gears, 20 degree pressure angle, module ~0.91 mm (fine), tip diameter ~20 mm on the pinion and ~38 mm on the hinge gear, face width ~12 mm. Both the pinion and the hinge gear are 3D printed (FDM). The pinion is clamped to the MG996R 25-tooth output spline. The mechanism lifts a meaningful load: the mounting plate plus a powder auger that becomes significantly heavier when fully loaded, so the gears carry a substantial holding and lifting torque.

Observed failure: the mechanism worked fine during a one-day demo, but the NEXT day, after repeated actuation cycles, the TEETH ON THE SERVO PINION began to STRIP. It seems to be a wear/fatigue failure that develops with repeated use rather than a single overload event. Separately, the servo was only temporarily held in place (taped, not screwed) during testing, and when the operator pressed the motor down by hand the gears appeared to SKIP less - suggesting the printed motor mount may not be rigid enough, letting the pinion and gear separate radially under load so the teeth ride up and skip ("tooth jumping"/insufficient mesh).

Please give concrete, prioritized engineering recommendations on how to best eliminate this gear stripping. Specifically address:

1. Are METAL gears (e.g., a metal pinion, or upgrading to a metal-gear servo such as the MG996R metal-geartrain version, or a machined/POM gear) REQUIRED here, or can a well-designed 3D-printed gear survive this duty? Quantify roughly: for a printed spur gear at module ~0.9 mm, 20 mm pitch diameter, ~12 mm face width in PLA vs PETG vs nylon, what tooth-root bending stress / allowable torque can be expected, and how does that compare to the MG996R stall torque amplified through the spline?

2. Material: the printed parts are currently FDM. Compare PLA vs PETG vs PA (nylon) vs POM for small spur-gear teeth under repeated cyclic loading - which best resists tooth stripping / wear, and is switching from PLA to PETG (or nylon) likely sufficient, or is metal unavoidable?

3. Mount rigidity: would adding a BRACKET / second bearing support to the servo-mount so the motor cannot deflect (maintaining true center distance and full tooth engagement) meaningfully reduce skipping/stripping? How important is constraining center distance and preventing radial separation versus the absolute tooth strength? Best practices for rigidly mounting a hobby servo driving a load-bearing gear (screw-down vs tape, outboard bearing on the gear shaft, anti-backlash).

4. Geometry: would a coarser module (fewer, larger teeth), wider face width, larger pinion (more teeth, avoiding undercut on the 20T pinion), or a different reduction help the printed teeth survive? Any quick design changes with high payoff.

5. Any alternative to spur-gear drive for a low-speed, high-torque, intermittent tilt actuator at this scale that would be more robust (e.g., worm drive / self-locking, lever arm + linear actuator, larger servo, geared stepper) - briefly.

Prioritize the cheapest / fastest fixes first (material swap, mount bracket, geometry tweak) and clearly state when metal becomes necessary.


# Engineering Recommendations for Eliminating Gear Stripping in a Servo-Driven Tilt Mechanism

## 1. Diagnosis: Two Concurrent Failure Modes

The observed pinion tooth stripping is very likely the combined result of **two failure modes acting together**: (a) **insufficient mesh engagement** due to a compliant, non-rigid servo mount allowing radial separation of the gear pair under load, and (b) **marginal tooth-root bending strength** in a fine-pitch FDM-printed pinion operating near its fatigue limit. The fact that hand pressure on the motor visibly reduced skipping is strong evidence that the center-distance is growing under load, causing the teeth to ride up over each other ("tooth jumping") before they wear enough to strip outright. Once tooth tips begin to deform from partial-engagement impacts, progressive fatigue damage accumulates rapidly even when the mount is briefly corrected.

## 2. Quantitative Stress Assessment

Using the Lewis bending equation for the described pinion geometry (module *m* = 0.91 mm, 20 teeth, pitch diameter *d* = 18.2 mm, face width *b* = 12 mm, Lewis form factor *Y* ≈ 0.32 for 20T/20° pressure angle), and taking the MG996R stall torque of approximately 10 kg·cm (≈ 0.98 N·m), the tangential tooth force at stall is *Fₜ* = 2*T*/*d* ≈ 108 N. The resulting static tooth-root bending stress is:

σ ≈ *Fₜ* / (*b* · *m* · *Y*) ≈ 108 / (0.012 × 0.00091 × 0.32) ≈ **31 MPa**

Applying a modest dynamic/application factor of ~1.5 (to account for impact loading during tooth engagement, imperfect mesh geometry from FDM tolerances, and repeated cycling), the effective cyclic stress rises to approximately **46 MPa**. This must be compared against material allowable values, noting that FDM-printed parts exhibit significantly reduced strength relative to bulk material due to inter-layer bonding weaknesses, voids, and anisotropy (rahim2017theimprovementof pages 4-8, rahim2017theimprovementof pages 9-11).

The following table summarizes the stress-versus-strength comparison across candidate materials for both the current geometry and an improved geometry:

| Material / case | Bulk flexural strength (MPa) | Effective allowable for printed/cyclic duty (MPa) | Estimated Lewis bending stress at stall (MPa) | Safety factor vs 31 MPa static | Safety factor vs 46 MPa dynamic | Verdict |
|---|---:|---:|---|---:|---:|---|
| PLA, current geometry (m = 0.91, 20T, b = 12 mm) | ~60–80 | ~30–45 | ~31 static / ~46 with dynamics | ~1.0–1.45 | ~0.65–0.98 | Marginal to Fail |
| PETG, current geometry (m = 0.91, 20T, b = 12 mm) | ~45–60 | ~22–36 | ~31 static / ~46 with dynamics | ~0.71–1.16 | ~0.48–0.78 | Fail |
| PA12 nylon, current geometry (m = 0.91, 20T, b = 12 mm) | ~63 | ~38–44 | ~31 static / ~46 with dynamics | ~1.23–1.42 | ~0.83–0.96 | Best printed option, still marginal |
| POM / acetal, machined or molded (not typical FDM) | ~80–100 | ~60–80 | ~31 static / ~46 with dynamics | ~1.94–2.58 | ~1.30–1.74 | Pass |
| Brass / steel pinion | ~200–1000+ | ~200–1000+ | ~31 static / ~46 with dynamics | ~6.5–32+ | ~4.3–22+ | Strong Pass |
| Any better material, but upgraded geometry (m = 1.5 instead of 0.91, same torque, same 20T, same 12 mm face) | material-dependent | material-dependent | ~11 static / ~16 with dynamics | Allowable/11 | Allowable/16 | High-payoff geometry fix |
| Example: PA12 nylon with m = 1.5 | ~63 | ~38–44 | ~11 static / ~16 with dynamics | ~3.45–4.00 | ~2.38–2.75 | Pass |
| Example: PLA with m = 1.5 | ~60–80 | ~30–45 | ~11 static / ~16 with dynamics | ~2.73–4.09 | ~1.88–2.81 | Pass to Marginal |
| Example: PETG with m = 1.5 | ~45–60 | ~22–36 | ~11 static / ~16 with dynamics | ~2.00–3.27 | ~1.38–2.25 | Marginal to Pass |

| Assumptions used | Value |
|---|---|
| Servo stall torque | 0.98 N·m |
| Pinion pitch diameter | 18.2 mm |
| Tangential tooth load at stall | ~108 N |
| Lewis form factor, 20T, 20° PA | ~0.32 |
| Current stress formula | σ ≈ Ft / (b·m·Y) ≈ 31 MPa |
| Dynamic/application factor used for repeated load, compliance, imperfect mesh | ~1.5, giving ~46 MPa effective stress |
| Source basis for polymer strengths and wear ranking | ABS 60 MPa flexural, PEEK 130 MPa flexural, ULTEM 98.3 MPa flexural, PA12 ~63 MPa flexural; PLA generally stronger/stiffer than PETG; FDM parts derated by interlayer bonding, voids, and fatigue (pisula2021ananalysisof pages 4-6, hsueh2021effectofprinting pages 8-10, svetlana2021flexuralquasistaticand pages 6-8, rahim2017theimprovementof pages 4-8, rahim2017theimprovementof pages 9-11, pisula2021ananalysisof pages 12-15, pisula2021ananalysisof pages 15-18) |


*Table: This table compares estimated pinion tooth-root stress against practical allowable strength for likely gear materials in the current fine-pitch design. It shows why PETG is likely inadequate, PA12 is only marginal at the present geometry, and why either metal or a coarser module provides a much safer solution.*

## 3. Material Comparison: PLA vs. PETG vs. PA (Nylon) vs. POM vs. Metal

**PLA** (flexural strength ~60–80 MPa bulk) is stiff but brittle with poor fatigue resistance. At the current geometry, the static safety factor is barely above 1.0 after accounting for FDM derating, and the cyclic safety factor falls below 1.0 — consistent with the observed delayed fatigue-type stripping rather than instant overload (hsueh2021effectofprinting pages 2-3, hsueh2021effectofprinting pages 6-8, hsueh2021effectofprinting pages 8-10).

**PETG** (flexural strength ~45–60 MPa bulk) is more ductile than PLA but weaker. Switching from PLA to PETG would likely make the problem worse, not better, because the lower bending strength yields an even lower safety factor (bembenek2022researchonthe pages 7-8, hsueh2021effectofprinting pages 2-3). PETG is **not recommended** as a fix for this application.

**PA12 nylon** (flexural strength ~63 MPa, flexural modulus ~1472 MPa for FDM-printed specimens) offers the best combination of strength, toughness, and fatigue resistance among common FDM polymers. FDM-printed PA12 was found to be approximately four times more fatigue-resistant than PA6 and roughly three times stiffer, and its flexural modulus actually exceeded that of injection-molded PA12 by about 6.5% (svetlana2021flexuralquasistaticand pages 6-8, svetlana2021flexuralquasistaticand pages 3-4). This makes PA12 the best printed-material choice, though at the current fine module of 0.91 mm, it remains only marginally adequate under cyclic loading.

**POM/acetal** (flexural strength ~80–100 MPa, excellent wear resistance and dimensional stability) is a standard injection-molded gear material but is not readily printable by standard FDM. If a machined or injection-molded POM pinion is feasible, it provides substantially better tooth strength and wear performance. Studies of polymer gear wear show that material hardness stability under operating temperature is critical — materials that soften at moderate temperatures (even 60°C) can exhibit dramatic wear acceleration (pisula2021ananalysisof pages 15-18).

**Metal** (brass, steel): Even a simple brass pinion (yield strength >200 MPa) provides a safety factor exceeding 5 at the current geometry. A metal pinion is **required if the design must be reliable for production-level repeated cycling at this fine module and torque level**. Upgrading to the metal-geartrain version of the MG996R alone helps the internal servo gears but does not fix the external printed pinion; the external pinion itself should be metal or at minimum POM.

In fatigue testing of FDM-printed polymer spur gears, PEEK showed the best wear resistance with minimal topographical change, ABS showed moderate wear, and ULTEM 9085 exhibited the worst wear due to thermal softening at operating temperature (pisula2021ananalysisof pages 1-2, pisula2021ananalysisof pages 15-18). Dimensional instability from thermal expansion was also observed to affect tooth thickness and backlash during loaded operation (pisula2021ananalysisof pages 12-15).

## 4. Mount Rigidity: The Highest-Priority Fix

The single most impactful and cheapest fix is to **rigidly constrain the servo mount**. For spur gears at module 0.91 mm, the full tooth depth (addendum + dedendum) is only about 2.05 mm, meaning the working tooth engagement depth is roughly 0.91 mm. A center-distance increase of even 0.2–0.3 mm — easily possible with a taped or loosely held servo — can reduce the active engagement from full-depth to tip contact only, concentrating all force on the tooth tips and causing them to climb over each other. This directly explains why pressing the motor down by hand (restoring proper center distance) visibly reduced skipping.

**Best practices for the servo mount:**
- **Bolt the servo** into a rigid pocket or bracket using all four mounting ears with M3 screws into metal inserts or threaded standoffs — never tape.
- **Constrain the servo radially** by capturing it between walls or in a tight-fitting pocket so it cannot deflect away from the mating gear under the reaction force.
- If the bracket is itself printed, use thick walls (≥3 mm), gussets, and consider printing in PA12 or reinforcing with aluminum angle.
- Add a **second bearing or bushing support** on the outboard side of the hinge gear shaft so that the gear cannot deflect away from the pinion.
- Target a center-distance tolerance of ±0.05 mm (roughly ±5% of the module) — this requires the mount to be dimensionally accurate and rigid enough not to deflect under the ~108 N tangential tooth force.

## 5. Geometry Improvements: Coarser Module Is the Highest-Payoff Design Change

The current module of 0.91 mm is extremely fine for FDM-printed gears carrying load. Published experimental work on FDM polymer gears has used module 3.0 mm with 17–21 teeth (pisula2021ananalysisof pages 2-4) — over three times coarser than the current design. At module 0.91, each tooth is tiny (~2.9 mm circular pitch), FDM layer artifacts are proportionally large relative to the tooth profile, and each tooth root is a stress concentrator with very little cross-section.

**Increasing the module from 0.91 to 1.5 mm** (while maintaining 20 teeth on the pinion and 40 on the hinge gear) would:
- Increase pitch diameters to 30 mm (pinion) and 60 mm (gear), which may require modest envelope changes.
- **Reduce Lewis bending stress from ~31 MPa to ~11 MPa** (roughly proportional to 1/*m* since face width is held constant), bringing even PLA well within a safe margin (SF ≈ 3–4).
- Produce teeth that are much more accurately rendered by FDM (each tooth is ~4.7 mm pitch instead of ~2.9 mm).
- Provide better tolerance to small center-distance errors.

If the envelope cannot grow, a module of 1.25 mm would still roughly halve the stress. Alternatively, keeping the module at 0.91 but **increasing face width to 18 mm** reduces stress by about one-third.

Regarding tooth count: the current 20-tooth pinion does not suffer undercut with a standard 20° pressure angle (undercut limit is ~17 teeth for full-depth involute), so the tooth count itself is acceptable. However, more teeth (say 24–30) on the pinion with correspondingly more on the gear would increase the contact ratio and distribute load better, at the cost of a larger pitch diameter.

## 6. Print Orientation and Post-Processing

FDM-printed gear teeth are weakest when the layer boundaries run parallel to the tooth root fillet, as the inter-layer bond is the weakest direction. **Print the gear with the tooth face perpendicular to the build plate** (gear lying flat) so that layers stack along the tooth width, maximizing bending strength in the critical direction. Use 100% infill for the gear body. Raster angle of ±45° has been shown to provide good wear resistance in FDM polyamide parts (eyri2026enhancingtheperformance pages 14-14, eyri2026enhancingtheperformance pages 13-14). Annealing of PA12 or PA-CF parts after printing can improve interlayer bonding, glass transition temperature, and wear resistance.

## 7. Prioritized Recommendation Summary

The following table ranks all fixes by priority, starting with the cheapest and fastest:

| Priority rank | Fix Description | Category | Cost/Effort | Expected Impact | Implementation Notes |
|---:|---|---|---|---|---|
| 1 | Rigidly mount the servo with a screw-down bracket and positively constrain center distance | Mount | Low | High | Highest priority because operator pressure reduced skipping, strongly indicating radial separation under load. Replace tape with a bolted mount, add gussets or metal angle, and if possible provide a second support feature so the servo cannot rock. For module 0.91 gears, even small center-distance growth can reduce engagement enough to jump teeth (pisula2021ananalysisof pages 6-9, pisula2021ananalysisof pages 9-12, pisula2021ananalysisof pages 12-15). |
| 2 | Increase gear module from 0.91 mm to about 1.5 mm or larger | Geometry | Med | High | Biggest design-level payoff short of going metal. Lewis root stress scales roughly inversely with module, so moving from 0.91 to 1.5 mm cuts bending stress by about 40%; if the overall geometry is also enlarged with thicker roots and cleaner printing, practical survivability improves dramatically. Coarser teeth also print more accurately in FDM and are less sensitive to local defects (pisula2021ananalysisof pages 2-4, pisula2021ananalysisof pages 12-15). |
| 3 | Switch the printed pinion from PLA/PETG to PA12 nylon or PA-CF | Material | Low-Med | Med-High | Best printed-material upgrade. PA12 shows about 60 MPa tensile strength and about 63 MPa flexural strength with much better toughness and fatigue behavior than brittle PLA and weaker PETG; nylon also wears better in cyclic sliding contact. Dry the filament, print hot, use near-100% infill, and orient for maximum tooth-root continuity (svetlana2021flexuralquasistaticand pages 6-8, svetlana2021flexuralquasistaticand pages 3-4, eyri2026enhancingtheperformance pages 14-14, eyri2026enhancingtheperformance pages 13-14). |
| 4 | Increase face width from 12 mm to about 15–18 mm if packaging allows | Geometry | Low-Med | Med | Root stress scales roughly inversely with face width, so a 12 to 18 mm increase cuts nominal bending stress by about one-third. This will not cure tooth jumping from a flexible mount, but it meaningfully reduces pressure and wear once mesh is held correctly. Keep the width actually engaged across the full face by controlling parallelism and shaft alignment (pisula2021ananalysisof pages 9-12, pisula2021ananalysisof pages 12-15). |
| 5 | Replace the printed pinion with a machined POM/acetal or metal pinion (brass/steel) | Material | Med | High | This is the clearest way to eliminate pinion tooth stripping if the load is real and repeated. POM is a standard gear material with better wear and dimensional stability than FDM plastics; brass or steel gives a very large strength margin. If only one part goes hard, make it the small pinion first because it sees the highest cycle count and highest root stress. Verify the larger printed hinge gear can tolerate meshing with the harder pinion (pisula2021ananalysisof pages 15-18, pisula2021ananalysisof pages 1-2). |
| 6 | Upgrade to a metal-gear servo version of the MG996R or similar | Material | Low-Med | Med | Useful mainly because it improves the servo-side spline/output robustness and reduces local deformation where the printed pinion is clamped. It does not by itself fix an understrength printed pinion tooth or poor mesh geometry, but it removes one compliance and wear source near the output shaft. Prefer a servo with better real torque margin and better bearing support than low-cost clones if budget allows. |
| 7 | Change architecture: larger direct-drive servo, linear actuator plus lever, or worm drive | Architecture | High | High | Use when the mechanism must hold a heavy auger reliably for production use. A bigger servo can eliminate the small external pinion entirely; a linear actuator gives robust force transmission; a worm gear adds high reduction and possible self-locking so the actuator does not sit near stall while holding tilt. Best choice if repeated-duty reliability matters more than keeping the current compact spur-pinion concept. |


*Table: This table ranks the most practical engineering fixes for the stripping pinion problem, starting with the cheapest and fastest changes and ending with larger architecture changes. It is useful for deciding which modifications to try first and when a printed solution should give way to harder gear materials or a different actuator layout.*

## 8. Alternative Actuation Architectures (Brief)

If the spur-gear approach proves insufficiently robust even with improvements, several alternatives eliminate the vulnerable small printed pinion entirely:

- **Worm gear drive**: A worm on the servo shaft meshing with a worm wheel on the hinge provides high reduction (20:1–40:1) in a single stage and is inherently self-locking, eliminating holding torque on the servo. Small brass/steel worm sets are inexpensive.
- **Linear actuator + lever arm**: A micro linear actuator (e.g., Actuonix L12 or P16) pushing on a lever arm attached to the hinge converts linear force to rotary torque with no gear teeth to strip. Simple, robust, low cost (~$30–50).
- **Geared DC motor or stepper**: A NEMA 17 stepper with a planetary gearbox (e.g., 27:1 ratio) provides 5–15 N·m of holding torque directly on the hinge shaft, eliminating external gearing.
- **Larger direct-drive servo**: A 25–35 kg·cm servo (e.g., DS3225 or similar) coupled directly to the hinge axis via a horn and link may provide enough torque without any external gear reduction.

## 9. Conclusion

The stripping failure is primarily caused by **inadequate mesh engagement from a non-rigid mount** combined with **marginal bending strength at this fine module in FDM-printed plastic**. The recommended fix path is:

1. **Immediately**: Bolt down the servo rigidly (cost: negligible; impact: large).
2. **Short-term redesign**: Increase module to ≥1.5 mm and switch pinion material to PA12 nylon (cost: a spool of filament and reprinting; impact: large).
3. **If still marginal**: Replace the printed pinion with a machined POM or brass pinion (cost: ~$5–20; impact: definitive).
4. **For production reliability**: Consider an architecture change (linear actuator or worm drive) that eliminates the small loaded spur pinion entirely.

Metal gears are not strictly *required* if the module is increased sufficiently and mounting is correct, but at module 0.91 mm under this torque, **metal or POM for the pinion is strongly recommended** unless the geometry is made coarser. PETG should be avoided; PA12 nylon is the best printed alternative.


References

1. (rahim2017theimprovementof pages 4-8): Tuan Noraihan Azila Tuan Rahim, Abdul Manaf Abdullah, H. Akil, D. Mohamad, and Z. Rajion. The improvement of mechanical and thermal properties of polyamide 12 3d printed parts by fused deposition modelling. Express Polymer Letters, 11:963-982, Jan 2017. URL: https://doi.org/10.3144/expresspolymlett.2017.92, doi:10.3144/expresspolymlett.2017.92. This article has 131 citations and is from a peer-reviewed journal.

2. (rahim2017theimprovementof pages 9-11): Tuan Noraihan Azila Tuan Rahim, Abdul Manaf Abdullah, H. Akil, D. Mohamad, and Z. Rajion. The improvement of mechanical and thermal properties of polyamide 12 3d printed parts by fused deposition modelling. Express Polymer Letters, 11:963-982, Jan 2017. URL: https://doi.org/10.3144/expresspolymlett.2017.92, doi:10.3144/expresspolymlett.2017.92. This article has 131 citations and is from a peer-reviewed journal.

3. (pisula2021ananalysisof pages 4-6): Jadwiga Pisula, Grzegorz Budzik, Paweł Turek, and Mariusz Cieplak. An analysis of polymer gear wear in a spur gear train made using fdm and fff methods based on tooth surface topography assessment. Polymers, 13:1649, May 2021. URL: https://doi.org/10.3390/polym13101649, doi:10.3390/polym13101649. This article has 51 citations.

4. (hsueh2021effectofprinting pages 8-10): Ming-Hsien Hsueh, Chao-Jung Lai, Shi-Hao Wang, Yu-Shan Zeng, Chia-Hsin Hsieh, Chieh-Yu Pan, and Wen-Chen Huang. Effect of printing parameters on the thermal and mechanical properties of 3d-printed pla and petg, using fused deposition modeling. Polymers, 13:1758, May 2021. URL: https://doi.org/10.3390/polym13111758, doi:10.3390/polym13111758. This article has 430 citations.

5. (svetlana2021flexuralquasistaticand pages 6-8): Terekhina Svetlana, Tarasova Tatiana, Egorov Sergei, Skornyakov Innokentiy, Guillaumat Laurent, and Hattali Lamine. Flexural quasi-static and fatigue behaviours of fused filament deposited pa6 and pa12 polymers. The International Journal of Advanced Manufacturing Technology, 117(7-8):2041-2048, May 2021. URL: https://doi.org/10.1007/s00170-021-07223-y, doi:10.1007/s00170-021-07223-y. This article has 17 citations.

6. (pisula2021ananalysisof pages 12-15): Jadwiga Pisula, Grzegorz Budzik, Paweł Turek, and Mariusz Cieplak. An analysis of polymer gear wear in a spur gear train made using fdm and fff methods based on tooth surface topography assessment. Polymers, 13:1649, May 2021. URL: https://doi.org/10.3390/polym13101649, doi:10.3390/polym13101649. This article has 51 citations.

7. (pisula2021ananalysisof pages 15-18): Jadwiga Pisula, Grzegorz Budzik, Paweł Turek, and Mariusz Cieplak. An analysis of polymer gear wear in a spur gear train made using fdm and fff methods based on tooth surface topography assessment. Polymers, 13:1649, May 2021. URL: https://doi.org/10.3390/polym13101649, doi:10.3390/polym13101649. This article has 51 citations.

8. (hsueh2021effectofprinting pages 2-3): Ming-Hsien Hsueh, Chao-Jung Lai, Shi-Hao Wang, Yu-Shan Zeng, Chia-Hsin Hsieh, Chieh-Yu Pan, and Wen-Chen Huang. Effect of printing parameters on the thermal and mechanical properties of 3d-printed pla and petg, using fused deposition modeling. Polymers, 13:1758, May 2021. URL: https://doi.org/10.3390/polym13111758, doi:10.3390/polym13111758. This article has 430 citations.

9. (hsueh2021effectofprinting pages 6-8): Ming-Hsien Hsueh, Chao-Jung Lai, Shi-Hao Wang, Yu-Shan Zeng, Chia-Hsin Hsieh, Chieh-Yu Pan, and Wen-Chen Huang. Effect of printing parameters on the thermal and mechanical properties of 3d-printed pla and petg, using fused deposition modeling. Polymers, 13:1758, May 2021. URL: https://doi.org/10.3390/polym13111758, doi:10.3390/polym13111758. This article has 430 citations.

10. (bembenek2022researchonthe pages 7-8): Michał Bembenek, Łukasz Kowalski, and Agnieszka Kosoń-Schab. Research on the influence of processing parameters on the specific tensile strength of fdm additive manufactured pet-g and pla materials. Polymers, 14:2446, Jun 2022. URL: https://doi.org/10.3390/polym14122446, doi:10.3390/polym14122446. This article has 76 citations.

11. (svetlana2021flexuralquasistaticand pages 3-4): Terekhina Svetlana, Tarasova Tatiana, Egorov Sergei, Skornyakov Innokentiy, Guillaumat Laurent, and Hattali Lamine. Flexural quasi-static and fatigue behaviours of fused filament deposited pa6 and pa12 polymers. The International Journal of Advanced Manufacturing Technology, 117(7-8):2041-2048, May 2021. URL: https://doi.org/10.1007/s00170-021-07223-y, doi:10.1007/s00170-021-07223-y. This article has 17 citations.

12. (pisula2021ananalysisof pages 1-2): Jadwiga Pisula, Grzegorz Budzik, Paweł Turek, and Mariusz Cieplak. An analysis of polymer gear wear in a spur gear train made using fdm and fff methods based on tooth surface topography assessment. Polymers, 13:1649, May 2021. URL: https://doi.org/10.3390/polym13101649, doi:10.3390/polym13101649. This article has 51 citations.

13. (pisula2021ananalysisof pages 2-4): Jadwiga Pisula, Grzegorz Budzik, Paweł Turek, and Mariusz Cieplak. An analysis of polymer gear wear in a spur gear train made using fdm and fff methods based on tooth surface topography assessment. Polymers, 13:1649, May 2021. URL: https://doi.org/10.3390/polym13101649, doi:10.3390/polym13101649. This article has 51 citations.

14. (eyri2026enhancingtheperformance pages 14-14): Busra Eyri, Yusuf Yagci, N. Gamze Karsli, and Taner Yilmaz. Enhancing the performance of 3d‐printed polyamide composites through pre‐ and post‐processing methods. Polymer Composites, 47:10002-10017, Jan 2026. URL: https://doi.org/10.1002/pc.70872, doi:10.1002/pc.70872. This article has 0 citations and is from a peer-reviewed journal.

15. (eyri2026enhancingtheperformance pages 13-14): Busra Eyri, Yusuf Yagci, N. Gamze Karsli, and Taner Yilmaz. Enhancing the performance of 3d‐printed polyamide composites through pre‐ and post‐processing methods. Polymer Composites, 47:10002-10017, Jan 2026. URL: https://doi.org/10.1002/pc.70872, doi:10.1002/pc.70872. This article has 0 citations and is from a peer-reviewed journal.

16. (pisula2021ananalysisof pages 6-9): Jadwiga Pisula, Grzegorz Budzik, Paweł Turek, and Mariusz Cieplak. An analysis of polymer gear wear in a spur gear train made using fdm and fff methods based on tooth surface topography assessment. Polymers, 13:1649, May 2021. URL: https://doi.org/10.3390/polym13101649, doi:10.3390/polym13101649. This article has 51 citations.

17. (pisula2021ananalysisof pages 9-12): Jadwiga Pisula, Grzegorz Budzik, Paweł Turek, and Mariusz Cieplak. An analysis of polymer gear wear in a spur gear train made using fdm and fff methods based on tooth surface topography assessment. Polymers, 13:1649, May 2021. URL: https://doi.org/10.3390/polym13101649, doi:10.3390/polym13101649. This article has 51 citations.