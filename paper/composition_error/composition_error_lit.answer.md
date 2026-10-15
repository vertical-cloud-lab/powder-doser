Question: We built an open-source, 3D-printed auger powder doser with closed-loop
gravimetric feedback from a 0.1 mg readability analytical balance. It doses
50 mg to 1 g (and larger) portions of elemental or pre-alloyed metal powders
(for example gas-atomized AlSi10Mg, crystalline silicon, and Al 4047 / Al-12Si)
to blend alloy feedstocks for an ultrasonic atomizer and for additive
manufacturing in an alloy-discovery workflow. Total blend batch sizes will
typically be 10 to 500 g. Our per-dose acceptance limits are +/-10 % of the
requested mass below 100 mg and +/-5 % at or above 100 mg. We want to state
how much composition error (atomic % or weight %) these limits allow and
whether that is acceptable for alloy development.

Question: What composition tolerances (in at% or wt%) are used or required
when blending elemental or pre-alloyed powders for alloy development and
additive manufacturing, and how accurately must the powders be weighed for
gram-to-hundreds-of-gram batches?

Please give quantitative values with citations (DOIs where possible) for:
1. In-situ alloying in additive manufacturing (laser powder bed fusion,
   directed energy deposition) from blended elemental or pre-alloyed powders
   (e.g. Al-Si, AlSi10Mg + Si, Al-Cu, Ti-6Al-4V, Ti-Nb, NiTi, CoCrFeMnNi,
   AlCoCrFeNi high-entropy alloys): the reported deviation between nominal
   blend composition and measured as-built composition, and how weighing
   error compares with other error sources (evaporation of Al, Mg, Mn,
   segregation, incomplete mixing or melting).
2. Combinatorial or high-throughput alloy discovery with powders (e.g.
   Moorehead et al. 2020 high-throughput synthesis of Mo-Nb-Ta-W by in-situ
   alloying in directed energy deposition; Vecchio et al. 2021 high-throughput
   rapid experimental alloy development, HT-READ; powder-blend or
   arc-melted libraries): the composition step size used (e.g. 1, 2, or
   5 at%) and the composition accuracy reported or considered acceptable.
3. Registered composition limits for AlSi10Mg and Al-Si alloys: EN AC-43000
   (EN 1706), ISO 3522, ASTM F3318 for AlSi10Mg powder bed fusion, Aluminum
   Association registrations such as A360 and 4047 (Al-12Si), and
   hypereutectic Al-Si (A390, Al-20Si, Al-50Si controlled-expansion alloys).
   What are the widths of the Si and Mg ranges in wt%, and what weighing
   accuracy does that imply when blending these alloys from powders?
4. Weighing practice for alloy batches of 1 to 500 g (arc melting,
   mechanical alloying, AM feedstock blending): typical balance readability
   and weighing tolerances reported (e.g. +/-0.1 mg, +/-1 mg, 0.01 wt%), and
   guidance from standards (e.g. USP <41> minimum weight, ISO/ASTM 52907
   feedstock specification).
5. The typical uncertainty of composition measurement by ICP-OES, XRF, and
   EDS (e.g. EDS about +/-0.5 to 1 at%), since that sets a floor on how
   precisely an as-made composition can be verified, and any published
   treatment of propagating component mass errors into at% or wt% errors.


# Composition tolerance for powder-blended alloy development

**Conclusion.** There is no general rule that every alloy powder must be weighed to a particular percentage of its own mass. The relevant quantity is the resulting error in the *final elemental composition*, which depends on batch size, the composition of each starting powder, and errors in all additions. Your ±10% limit below 100 mg and ±5% limit at or above 100 mg can be useful for **coarse alloy discovery**, particularly when a small addition is diluted into a large batch. They do **not**, by themselves, establish ±0.1 at% composition control, conformity to a registered alloy, or the chemistry of an atomized or printed product. Report achieved masses and calculated feedstock compositions separately from analytically measured product compositions. Published in-situ-alloying results demonstrate that powder transport and melting can cause errors much greater than balance readability. (moorehead2020highthroughputsynthesisof pages 9-13, chen2020areviewon pages 10-13)

## 1. What published alloy-development studies actually achieve

| Process and study | Designed versus measured composition, or composition resolution | Interpretation |
|---|---|---|
| **Elemental-powder DED, Mo–Nb–Ta–W**, Moorehead *et al.*, *Materials & Design* **187**, 108358 (2020), DOI **10.1016/j.matdes.2019.108358** | In the first iteration, Table A1 lists estimated incoming **Mo/Nb/Ta/W = 46/10/32/12 at%** for sample R1.1, versus **21/27/27/24 at%** measured by surface EDS. After powder-feed and retention-factor recalibration, the third iteration achieved target agreement within **±5 at%-points for Mo and W** and **±10 at%-points for Nb and Ta**. | These are errors in predicting *deposited* composition from hopper feed rates, **not errors in weighing a static blend**. The authors model individual feed rates and element-dependent retention. (moorehead2020highthroughputsynthesisof pages 22-24, moorehead2020highthroughputsynthesisof pages 9-13) |
| **Powder-blend DED**, reviewed by Chen *et al.*, *Materials* **13**, 3562 (2020), DOI **10.3390/ma13163562** | Reported Al in deposited AlCoCrFeNi was **10–15 at%**, versus **20 at% designed**: a **5–10 at%-point deficit**. A Ni–Cu example had a reported **4% composition error**; the review does not define whether that figure is relative or in percentage points. | Neither figure should be attributed to balance error. The review discusses powder segregation, unequal particle capture, evaporation and inadequate melting. For Ti–10%Nb it reports inhomogeneous mixing, contrasting with more homogeneous Ti–10%Cr; it gives no verified numerical as-built Ti–Nb error. (chen2020areviewon pages 10-13) |
| **Powder mixtures consolidated by HIP**, Zhao *et al.*, *Metallurgical and Materials Transactions A* **52**, 1159–1168 (2021), DOI **10.1007/s11661-021-06149-0** | Their 19-member Co–Fe–Ni library used selected **mass ratios**, not a uniform 1-, 2- or 5-at% grid. Table II gives, for example, designed **Fe:Co = 1:1** versus analyzed **Fe 51.6/Co 48.4 mass%**; designed equimass **Fe:Co:Ni = 1:1:1** versus analyzed **33.8/33.7/32.5 mass%**. The cell averages were characterized **semiquantitatively by EDS**. | A concrete example of designed-versus-observed library compositions; its measurements are not a certified universal weighing tolerance. (zhao2021highthroughputsynthesisand pages 2-4, zhao2021highthroughputsynthesisand pages 1-2) |
| **HT-READ powder-blend DED**, Vecchio *et al.*, *Acta Materialia* **221**, 117352 (2021), DOI **10.1016/j.actamat.2021.117352** | Sixteen pre-mixed Inconel-625-based compositions: additions reached **13 wt% Nb**, **13 wt% Mo**, or **19 wt% Cr** beyond the base composition. **Figure 2B plots targets against actual EDS measurements**, but the paper does not establish a uniform at%-step size or a single numerical acceptance tolerance from that plot. | The **22.5°** spacing of specimens is a *geometrical* spacing, not 22.5 at%. The authors explicitly favor accurately weighing and premixing each vial when composition fidelity across many elements is needed. (vecchio2021highthroughputrapidexperimental pages 4-7, vecchio2021highthroughputrapidexperimental pages 7-11, vecchio2021highthroughputrapidexperimental media 48ea5aa1) |
| **Elemental-powder DED, Mg–Cu–Y**, Thoma *et al.*, *Metals* **13**, 1317 (2023), DOI **10.3390/met13071317** | **595 nominal compositions at 3-at%-point intervals** were printed; actual composition was assayed by EDS for selected specimens and departures from nominal were noted. | **3 at% is library design spacing, not demonstrated accuracy**. Magnesium evaporation, substrate mixing and local inhomogeneity complicate the comparison. (thoma2023highthroughputsynthesisand pages 3-6, thoma2023highthroughputsynthesisand pages 6-9, thoma2023highthroughputsynthesisand pages 11-12) |

For LPBF specifically, Risse *et al.* processed **50 and 70 wt% nominal Si** materials using either elemental Al + Si or pre-alloyed AlSi50 + Si feedstocks; the blended and pre-alloyed routes gave similar reported material properties. This establishes that large, deliberately spaced Si-composition experiments can be informative, **not** that the resulting bulk Si concentration was controlled to 1 wt%-point: the retrieved compositional account does not provide a paired bulk nominal-versus-assayed Si value. *Materials* **16**, 657 (2023), DOI **10.3390/ma16020657**. As another feedstock-level comparison—not an as-built assay—Garmendia *et al.* targeted a **1 wt% Cu** treatment of AlSi10Mg powder and measured **0.97 ± 0.02 wt% Cu by XRF**; ASTM F3318-18 was used there for subsequent *heat treatment*. *Materialia* **9**, 100590 (2020), DOI **10.1016/j.mtla.2020.100590**. (risse2023microstructureandmechanical pages 2-4, risse2023microstructureandmechanical pages 4-6, garmendia2020microstructureandmechanical pages 2-3)

**Process errors should not be assigned to the scale.** Moorehead's as-deposited microstructure exhibited different local, phase-associated compositions even within one nominally equimolar alloy: for example, Nb was **23 ± 2 at% intracellular** versus **31 ± 2 at% intercellular** by EDS. Such local segregation is different from a bulk average. In elemental-blend DED, differing particle density and size can segregate powders before delivery; changing particle-size selection and sieving improved the reviewed Al–Cu and Fe–Cr–Ni cases. Preferential capture, substrate dilution, incomplete dissolution and evaporation require separate process controls and product assays. Reports of Mg, Al or Mn volatility do not justify assigning a single transferable percentage loss to every alloy or laser setting. (moorehead2020highthroughputsynthesisof pages 13-19, chen2020areviewon pages 10-13, moorehead2020highthroughputsynthesisof pages 9-13)

## 2. Composition specifications are not dispensing specifications

For **EN AC-43000 / EN 1706 AlSi10Mg**, reported limits are **Si 9.00–11.00 wt%**, a **2.00-wt%-point range**, and **Mg 0.20–0.45 wt%**, a **0.25-wt%-point range**. A powder independently assayed in one investigation contained **9.7 wt% Si and 0.35 wt% Mg**. The half-widths **about a midpoint target** are only **±1.00 wt%-point Si** and **±0.125 wt%-point Mg**, *before* allocating any allowance to starting-powder variation, mixing, atomization, analysis and printing. At 10 wt% Si these half-widths correspond to approximately **±10% relative Si concentration**; at a midpoint Mg concentration of 0.325 wt%, ±0.125 points corresponds to approximately **±38% relative Mg concentration**. They are permissible *product-composition windows*, not accuracy targets for an individual dispenser. (ortmann2024powderbedfusion pages 1-4, gersch2025influenceofthe pages 1-6)

**Do not equate different standards.** The cited AlSi10Mg experiment invokes **ASTM F3318-18 for heat treatments**, not as evidence that F3318 mandates ±5% powder weighing. **ISO/ASTM 52907** concerns methods of characterizing metal-powder feedstocks; it does not establish a universal blend-weighing percentage in the retrieved evidence. I could not verify primary registration-table ranges for **ISO 3522, AA 4047, A360 or A390** from the accessible sources, and would not transfer EN AC-43000's limits to them. Likewise, nominal labels such as **Al–20Si** or **AlSi50** identify intended composition, not a demonstrated registered tolerance. Obtain the applicable edition and product-form-specific registration before claiming compliance: 4047 filler/wrought product, A360/A390 castings, AM powder and as-built parts need not share a specification. (garmendia2020microstructureandmechanical pages 2-3, risse2023microstructureandmechanical pages 2-4, ortmann2024powderbedfusion pages 1-4, gibbons2024metalpowderfeedstock pages 5-7)

## 3. Convert your dose limits into final composition error

For powder portions with masses \(m_j\), and starting-powder element-\(i\) mass fractions \(c_{ij}\), calculate the predicted blend directly:

\[
 w_i=\frac{\sum_jm_jc_{ij}}{\sum_jm_j},\qquad
 x_i=\frac{\sum_jm_jc_{ij}/M_i}{\sum_k\sum_jm_jc_{kj}/M_k},
\]

where \(w_i\) is a **weight fraction**, \(x_i\) an **atomic fraction**, and \(M_i\) atomic mass. Enter *assayed or supplier-qualified compositions* for pre-alloyed powders rather than treating AlSi10Mg or 4047 as pure Al. Moorehead *et al.* use the analogous normalization of elemental powder **mass flow** to predict at%, then add empirical element-retention factors for the deposited alloy. The following numerical bounds are **mass-balance calculations for your stated acceptance limits**, not performance measurements of your apparatus. (moorehead2020highthroughputsynthesisof pages 9-13, ortmann2024powderbedfusion pages 1-4)

| Scenario | Dose / final nominal total | Dose tolerance | Resulting Si concentration | Worst nominal-to-blend shift (wt%-points) | Take-away |
|---|---:|---:|---:|---:|---|
| Pure Si minor addition | 50 mg / 10 g | ±10% = ±5 mg | 0.45025–0.54973 wt% (nominal 0.50000%) | −0.04975 / +0.04973 | A ±10% dose error becomes only about ±0.05 wt%-points in a 10 g blend. |
| Pure Si addition at acceptance-limit transition | 100 mg / 10 g | ±5% = ±5 mg | 0.95048–1.04948 wt% (nominal 1.00000%) | −0.04952 / +0.04948 | The same ±5 mg absolute error gives approximately ±0.05 wt%-points. |
| Major pure-Si addition | 1 g / 10 g | ±5% = ±50 mg | 9.5477–10.4478 wt% (nominal 10.0000%) | −0.4523 / +0.4478 | Adequate for broad alloy screening, but large relative to tight specification targeting; EN AC-43000 permits 9–11 wt% Si (2 wt%-point width) (ortmann2024powderbedfusion pages 1-4). |
| Pure Si addition to a larger batch | 1 g / 100 g | ±5% = ±50 mg | 0.95048–1.04948 wt% (nominal 1.00000%) | −0.04952 / +0.04948 | Composition error scales with dose fraction, not batch mass alone. |
| Trace pure-Si addition to a large batch | 50 mg / 500 g | ±10% = ±5 mg | 0.009000–0.011000 wt% (nominal 0.010000%) | approximately ±0.001000 | Small-dose acceptance is compatible with roughly 0.001 wt%-point resolution in a 500 g batch. |
| Pre-alloy adjustment: 10 g AlSi10Mg at 10 wt% Si + pure Si | 0.5 g / 10.5 g | ±5% = ±25 mg | 14.081–14.489 wt% (nominal 14.2857%) | −0.205 / +0.203 | Pre-alloy dilution reduces the final composition effect; useful for discovery-scale increments. |
| Calculation basis | Fixed mass of every component except the stated dose | — | Actual concentration = actual Si mass ÷ actual total mass × 100 | — | All values are original mass-balance calculations, not literature-reported dispenser precision or analytical uncertainty. |


*Table: Mass-balance examples translate the doser's acceptance limits into absolute Si composition shifts for 10–500 g blends. They show that the impact depends primarily on the constituent's fraction of the final batch.*

For perspective, **50 mg of pure Si in a 10 g batch is 0.500 wt% Si**. Its allowed ±5 mg error changes Si by approximately **±0.050 wt%-points**, not ±10 wt%-points. With Al and Si only, atomic masses Al ≈26.98 and Si ≈28.09 g mol⁻¹ make this approximately **±0.048 at%-points** near 0.5 wt% Si. By contrast, allowing a **1 g pure-Si dose in 10 g** to vary ±50 mg gives approximately **9.55–10.45 wt% Si** when the other 9 g is fixed: approximately **−0.45/+0.45 wt%-points**. If *both* the Si and Al portions have independent **opposite-sign ±5%** mass errors, the endpoints become approximately **9.10–10.90 wt% Si**. A midpoint-targeted EN AC-43000 Si blend would therefore have little remaining Si-composition margin in that deliberately conservative two-error case. These are feedstock calculations, not predictions of as-built Si. (ortmann2024powderbedfusion pages 1-4, moorehead2020highthroughputsynthesisof pages 9-13)

A useful general first-order rule for **one** imperfect dose is \(\Delta w_i\simeq(c_{ij}-w_i)\Delta m_j/M\), where \(M\) is total batch mass; its magnitude is at most \(|\Delta m_j|/M\) as a *fraction*, or \(100|\Delta m_j|/M\) in **wt%-points**. Thus a 5 mg deviation in a 10 g batch cannot by itself shift any element by more than **0.05 wt%-points**; the bound becomes **0.005** and **0.001 wt%-points** in 100 and 500 g batches. For many doses, compute their **signed worst-case sum** for a guaranteed envelope or propagate measured, approximately independent standard uncertainties in quadrature for a statistical interval; neither approach is justified by balance readability alone. If a batch requires repeated 1 g portions, their errors can add coherently—do not apply the single-dose example to the entire constituent. (moorehead2020highthroughputsynthesisof pages 9-13, moorehead2020highthroughputsynthesisof pages 5-9, alegria2025validationanduncertainty pages 9-13)

## 4. How accurately to weigh 1–500 g batches

**Set the target backwards from the desired composition increment.** If a 10 g, near-10-wt% Si experiment must keep *weighing's contribution* below **0.1 wt%-point**, a pure-Si addition with fixed balance-of-batch mass needs an error below approximately **11 mg**: \(\Delta w\simeq0.9\Delta m/10\,\mathrm g\). For a **0.01-wt%-point** weighing allocation it needs approximately **1.1 mg**. At **100 g**, these illustrative budgets are roughly **110 mg** and **11 mg**, respectively, assuming the other masses are controlled and starting-powder chemistry is known. The formula—not a generic ±0.1 mg rule—should be reapplied to Mg and each pre-alloyed component, with headroom reserved for composition drift during processing. A ±5% error on a 0.3 wt% pure-Mg addition contributes roughly **0.015 wt%-points** if the balance of the batch is fixed; it is small relative to the **0.25-wt%-point** EN Mg-window width but may matter if the target sits close to a limit. (ortmann2024powderbedfusion pages 1-4, moorehead2020highthroughputsynthesisof pages 9-13)

Analytical balances with **0.1 or 0.01 mg readability and up to approximately 500 g capacity** are documented; this is *display resolution*, not verified accuracy of a transfer into a mixer. A weighing guide's worked pharmaceutical **USP <41>** example found that a **0.01 mg-readability** balance failed its stated relative-repeatability criterion for a **10 mg** sample but passed for **50 mg**, illustrating why an instrument's actual repeated-weighing variability and minimum usable mass must be measured. **USP <41> is a pharmaceutical assay rule, not an alloy standard.** Validate repeatability, calibration, drift, static, powder retention on vessels, and mass *actually transferred*, particularly when multiple doses are pooled. Select a balance with sufficient **capacity for vessel plus the largest portion or entire batch**; a 0.1 mg-readability instrument is not intrinsically better if its capacity is too small for the operation. (scorer2015errorsassociatedwith pages 11-14, scorer2015errorsassociatedwith pages 14-17, scorer2015errorsassociatedwith pages 17-20)

An explicitly alloy-focused automated arc-melting **preprint** specifies dispensing accuracy **better than 1 at%** and uses balance-feedback pellet-plus-wire weighing; its calculated wire-segment increments correspond to approximately **0.16 at% for 1 cm³**, **0.03 at% for 5 cm³**, and **<0.01 at% for 25 cm³** under its equal-molar-density assumption. These are **projected feedstock increments**, not a measured as-melted composition uncertainty or a required AM standard. Vecchio's HT-READ procedure likewise weighed and premixed its constituent powders but did not state a universal ±0.1 mg or 0.01 wt% weighing requirement. (selvaraj2026alloybotondemandsynthesis pages 7-10, selvaraj2026alloybotondemandsynthesis pages 4-7, vecchio2021highthroughputrapidexperimental pages 7-11)

## 5. Measuring whether the *product* met its target

There is **no universal ±0.5–1 at% floor for EDS**, nor a single universal precision for ICP-OES or XRF. For example, the Moorehead EDS study reports local Mo/Nb/Ta/W values with **±2–3 at%-point** spreads in its cellular regions; that reflects, at least in part, **actual local segregation** rather than instrument error alone. EDS of several polished positions can test uniformity, but should not substitute unquestioningly for representative bulk chemistry. (moorehead2020highthroughputsynthesisof pages 13-19, zhao2021highthroughputsynthesisand pages 2-4)

As a quantitative bulk-assay example, an **interlaboratory ICP-AES** study of aluminum-alloy reference materials measured **EB-313 Si 0.329 versus certified 0.363 wt%** and **Mg 3.347 versus certified 3.40 wt%**; its reported interlaboratory standard deviations were **0.045 and 0.123 wt%-points**, respectively. A different material at much lower Mg content gave **0.0458 versus certified 0.045 wt%**, with reported standard deviation **0.0007 wt%-points**. These are **matrix-, concentration- and preparation-dependent demonstrations**, not instrument-wide detection floors; high-Si alloys also require validated dissolution. *Analytical Sciences* **34**, 719–724 (2018), DOI **10.2116/analsci.18sbp14**. (uemoto2018determinationofminor pages 3-5, uemoto2018determinationofminor pages 1-2)

In a commercial-alloy methods comparison, repeated **EDXRF** measurements had an average precision reported as **2s < 0.1 wt%**, whereas most XRF/spark-OES differences for minor components below 2 wt% were **<0.25 wt%-points**; Mg was an important exception, with substantial EDXRF bias in an Al–Mg alloy, and Si also posed method-specific difficulties. Therefore verify **Si and especially low-concentration Mg** against suitable alloy reference materials and, where the decision demands it, an appropriately validated bulk assay rather than assuming an XRF value is definitive. *Metals* **11**, 736 (2021), DOI **10.3390/met11050736**. (seidel2021comparisonofelemental pages 8-10, seidel2021comparisonofelemental pages 5-7)

**Practical claim:** state a *calculated allowable feedstock-composition error conditional on the batch recipe*, alongside independently measured dosing repeatability, achieved transferred masses and analytical product results. Your present dose criteria are defensible as **screening-oriented mass tolerances**, especially for small dopant fractions and 100–500 g batches; they cannot alone substantiate a universal final-alloy at% tolerance, fine-step combinatorial resolution or standards-compliant AlSi10Mg after atomization or AM. (ortmann2024powderbedfusion pages 1-4, moorehead2020highthroughputsynthesisof pages 22-24, vecchio2021highthroughputrapidexperimental pages 7-11, seidel2021comparisonofelemental pages 8-10)

References

1. (moorehead2020highthroughputsynthesisof pages 9-13): Michael Moorehead, Kaila Bertsch, Michael Niezgoda, Calvin Parkin, Mohamed Elbakhshwan, Kumar Sridharan, Chuan Zhang, Dan Thoma, and Adrien Couet. High-throughput synthesis of mo-nb-ta-w high-entropy alloys via additive manufacturing. Materials & Design, 187:108358, Feb 2020. URL: https://doi.org/10.1016/j.matdes.2019.108358, doi:10.1016/j.matdes.2019.108358. This article has 331 citations and is from a highest quality peer-reviewed journal.

2. (chen2020areviewon pages 10-13): Yitao Chen, Xinchang Zhang, Mohammad Masud Parvez, and Frank Liou. A review on metallic alloys fabrication using elemental powder blends by laser powder directed energy deposition process. Materials, 13:3562, Aug 2020. URL: https://doi.org/10.3390/ma13163562, doi:10.3390/ma13163562. This article has 79 citations.

3. (moorehead2020highthroughputsynthesisof pages 22-24): Michael Moorehead, Kaila Bertsch, Michael Niezgoda, Calvin Parkin, Mohamed Elbakhshwan, Kumar Sridharan, Chuan Zhang, Dan Thoma, and Adrien Couet. High-throughput synthesis of mo-nb-ta-w high-entropy alloys via additive manufacturing. Materials & Design, 187:108358, Feb 2020. URL: https://doi.org/10.1016/j.matdes.2019.108358, doi:10.1016/j.matdes.2019.108358. This article has 331 citations and is from a highest quality peer-reviewed journal.

4. (zhao2021highthroughputsynthesisand pages 2-4): Lei Zhao, Yuanxun Zhou, Hui Wang, Xuebin Chen, Lixia Yang, Lanting Zhang, Liang Jiang, Yunhai Jia, Xiaobo Chen, and Haizhou Wang. High-throughput synthesis and characterization of a combinatorial materials library in bulk alloys. Metallurgical and Materials Transactions A, 52:1159-1168, Feb 2021. URL: https://doi.org/10.1007/s11661-021-06149-0, doi:10.1007/s11661-021-06149-0. This article has 15 citations.

5. (zhao2021highthroughputsynthesisand pages 1-2): Lei Zhao, Yuanxun Zhou, Hui Wang, Xuebin Chen, Lixia Yang, Lanting Zhang, Liang Jiang, Yunhai Jia, Xiaobo Chen, and Haizhou Wang. High-throughput synthesis and characterization of a combinatorial materials library in bulk alloys. Metallurgical and Materials Transactions A, 52:1159-1168, Feb 2021. URL: https://doi.org/10.1007/s11661-021-06149-0, doi:10.1007/s11661-021-06149-0. This article has 15 citations.

6. (vecchio2021highthroughputrapidexperimental pages 4-7): Kenneth S. Vecchio, Olivia F. Dippo, Kevin R. Kaufmann, and Xiao Liu. High-throughput rapid experimental alloy development (ht-read). Acta Materialia, 221:117352, Dec 2021. URL: https://doi.org/10.1016/j.actamat.2021.117352, doi:10.1016/j.actamat.2021.117352. This article has 103 citations and is from a highest quality peer-reviewed journal.

7. (vecchio2021highthroughputrapidexperimental pages 7-11): Kenneth S. Vecchio, Olivia F. Dippo, Kevin R. Kaufmann, and Xiao Liu. High-throughput rapid experimental alloy development (ht-read). Acta Materialia, 221:117352, Dec 2021. URL: https://doi.org/10.1016/j.actamat.2021.117352, doi:10.1016/j.actamat.2021.117352. This article has 103 citations and is from a highest quality peer-reviewed journal.

8. (vecchio2021highthroughputrapidexperimental media 48ea5aa1): Kenneth S. Vecchio, Olivia F. Dippo, Kevin R. Kaufmann, and Xiao Liu. High-throughput rapid experimental alloy development (ht-read). Acta Materialia, 221:117352, Dec 2021. URL: https://doi.org/10.1016/j.actamat.2021.117352, doi:10.1016/j.actamat.2021.117352. This article has 103 citations and is from a highest quality peer-reviewed journal.

9. (thoma2023highthroughputsynthesisand pages 3-6): Dan J. Thoma, Janine T. Spethson, Carter S. Francis, Paul M. Voyles, and John H. Perepezko. High-throughput synthesis and characterization screening of mg-cu-y metallic glass. Metals, 13:1317, Jul 2023. URL: https://doi.org/10.3390/met13071317, doi:10.3390/met13071317. This article has 8 citations.

10. (thoma2023highthroughputsynthesisand pages 6-9): Dan J. Thoma, Janine T. Spethson, Carter S. Francis, Paul M. Voyles, and John H. Perepezko. High-throughput synthesis and characterization screening of mg-cu-y metallic glass. Metals, 13:1317, Jul 2023. URL: https://doi.org/10.3390/met13071317, doi:10.3390/met13071317. This article has 8 citations.

11. (thoma2023highthroughputsynthesisand pages 11-12): Dan J. Thoma, Janine T. Spethson, Carter S. Francis, Paul M. Voyles, and John H. Perepezko. High-throughput synthesis and characterization screening of mg-cu-y metallic glass. Metals, 13:1317, Jul 2023. URL: https://doi.org/10.3390/met13071317, doi:10.3390/met13071317. This article has 8 citations.

12. (risse2023microstructureandmechanical pages 2-4): Jan Henning Risse, Matthias Trempa, Florian Huber, Heinz Werner Höppel, Dominic Bartels, Michael Schmidt, Christian Reimann, and Jochen Friedrich. Microstructure and mechanical properties of hypereutectic al-high si alloys up to 70 wt.% si-content produced from pre-alloyed and blended powder via laser powder bed fusion. Materials, 16:657, Jan 2023. URL: https://doi.org/10.3390/ma16020657, doi:10.3390/ma16020657. This article has 21 citations.

13. (risse2023microstructureandmechanical pages 4-6): Jan Henning Risse, Matthias Trempa, Florian Huber, Heinz Werner Höppel, Dominic Bartels, Michael Schmidt, Christian Reimann, and Jochen Friedrich. Microstructure and mechanical properties of hypereutectic al-high si alloys up to 70 wt.% si-content produced from pre-alloyed and blended powder via laser powder bed fusion. Materials, 16:657, Jan 2023. URL: https://doi.org/10.3390/ma16020657, doi:10.3390/ma16020657. This article has 21 citations.

14. (garmendia2020microstructureandmechanical pages 2-3): X. Garmendia, S. Chalker, Matthew Bilton, C. Sutcliffe, and P. Chalker. Microstructure and mechanical properties of cu-modified alsi10mg fabricated by laser-powder bed fusion. Materialia, 9:100590, Mar 2020. URL: https://doi.org/10.1016/j.mtla.2020.100590, doi:10.1016/j.mtla.2020.100590. This article has 29 citations and is from a peer-reviewed journal.

15. (moorehead2020highthroughputsynthesisof pages 13-19): Michael Moorehead, Kaila Bertsch, Michael Niezgoda, Calvin Parkin, Mohamed Elbakhshwan, Kumar Sridharan, Chuan Zhang, Dan Thoma, and Adrien Couet. High-throughput synthesis of mo-nb-ta-w high-entropy alloys via additive manufacturing. Materials & Design, 187:108358, Feb 2020. URL: https://doi.org/10.1016/j.matdes.2019.108358, doi:10.1016/j.matdes.2019.108358. This article has 331 citations and is from a highest quality peer-reviewed journal.

16. (ortmann2024powderbedfusion pages 1-4): Robert Ortmann, Nele Kretzer, Tobias Grimm, and Jan T. Sehrt. Powder bed fusion of alsi10mg using an electron beam: processability, microstructure and mechanical properties. Sep 2023. URL: https://doi.org/10.21203/rs.3.rs-3303697/v1, doi:10.21203/rs.3.rs-3303697/v1.

17. (gersch2025influenceofthe pages 1-6): Sebastian Gersch, Ulf Noster, Carsten Schulz, and Jörg Bagdahn. Influence of the process-related surface structure of l-pbf manufactured components on residual stress measurement using the incremental hole drilling method. Applied Sciences, 15:9861, Sep 2025. URL: https://doi.org/10.3390/app15189861, doi:10.3390/app15189861. This article has 2 citations.

18. (gibbons2024metalpowderfeedstock pages 5-7): Duncan W. Gibbons, Preyin Govender, and Andre F. van der Merwe. Metal powder feedstock evaluation and management for powder bed fusion: a review of literature, standards, and practical guidelines. Progress in Additive Manufacturing, 9:805-833, Jul 2024. URL: https://doi.org/10.1007/s40964-023-00484-x, doi:10.1007/s40964-023-00484-x. This article has 52 citations and is from a peer-reviewed journal.

19. (moorehead2020highthroughputsynthesisof pages 5-9): Michael Moorehead, Kaila Bertsch, Michael Niezgoda, Calvin Parkin, Mohamed Elbakhshwan, Kumar Sridharan, Chuan Zhang, Dan Thoma, and Adrien Couet. High-throughput synthesis of mo-nb-ta-w high-entropy alloys via additive manufacturing. Materials & Design, 187:108358, Feb 2020. URL: https://doi.org/10.1016/j.matdes.2019.108358, doi:10.1016/j.matdes.2019.108358. This article has 331 citations and is from a highest quality peer-reviewed journal.

20. (alegria2025validationanduncertainty pages 9-13): Rodrigo Martínez-Peñuñuri, Alejandro Monserrat GarcÍa Alegria, Paulina Vázquez-Bustamante, Marcela Montoya-Blumenkron, Dayana Itzajara Estrada-Gonzalez, Ana María Avilés Figueroa, Trinidad Quizan-Plata, and Karla Denisse Murillo-Castillo. Validation and uncertainty estimation for multielement determination using icp-oes according to the astm e2941-14 standard. Journal of Chemical Metrology, Jun 2025. URL: https://doi.org/10.25135/jcm.112.2502.3435, doi:10.25135/jcm.112.2502.3435. This article has 5 citations.

21. (scorer2015errorsassociatedwith pages 11-14): T. Scorer, M. Perkin, and M. Buckley. Errors associated with weighing. Calibration in the Pharmaceutical Laboratory, pages 175-214, May 2015. URL: https://doi.org/10.1201/b14422-8, doi:10.1201/b14422-8. This article has 5 citations.

22. (scorer2015errorsassociatedwith pages 14-17): T. Scorer, M. Perkin, and M. Buckley. Errors associated with weighing. Calibration in the Pharmaceutical Laboratory, pages 175-214, May 2015. URL: https://doi.org/10.1201/b14422-8, doi:10.1201/b14422-8. This article has 5 citations.

23. (scorer2015errorsassociatedwith pages 17-20): T. Scorer, M. Perkin, and M. Buckley. Errors associated with weighing. Calibration in the Pharmaceutical Laboratory, pages 175-214, May 2015. URL: https://doi.org/10.1201/b14422-8, doi:10.1201/b14422-8. This article has 5 citations.

24. (selvaraj2026alloybotondemandsynthesis pages 7-10): Vignesh Selvaraj, Pakorn Boonpetch, Anagh Dutta, Ming En Pek, and Sebastian Alexander Kube. Alloybot: on-demand synthesis of bulk alloys by automatic arc-melting. Unknown journal, May 2026. URL: https://doi.org/10.21203/rs.3.rs-9761885/v1, doi:10.21203/rs.3.rs-9761885/v1.

25. (selvaraj2026alloybotondemandsynthesis pages 4-7): Vignesh Selvaraj, Pakorn Boonpetch, Anagh Dutta, Ming En Pek, and Sebastian Alexander Kube. Alloybot: on-demand synthesis of bulk alloys by automatic arc-melting. Unknown journal, May 2026. URL: https://doi.org/10.21203/rs.3.rs-9761885/v1, doi:10.21203/rs.3.rs-9761885/v1.

26. (uemoto2018determinationofminor pages 3-5): Michihisa Uemoto, Masanori Makino, Yuji Ota, Hiromi Sakaguchi, Yukari Shimizu, and Kazuhiro Sato. Determination of minor and trace metals in aluminum and aluminum alloys by icp-aes; evaluation of the uncertainty and limit of quantitation from interlaboratory testing. Analytical Sciences, 34:719-724, Jun 2018. URL: https://doi.org/10.2116/analsci.18sbp14, doi:10.2116/analsci.18sbp14. This article has 16 citations and is from a peer-reviewed journal.

27. (uemoto2018determinationofminor pages 1-2): Michihisa Uemoto, Masanori Makino, Yuji Ota, Hiromi Sakaguchi, Yukari Shimizu, and Kazuhiro Sato. Determination of minor and trace metals in aluminum and aluminum alloys by icp-aes; evaluation of the uncertainty and limit of quantitation from interlaboratory testing. Analytical Sciences, 34:719-724, Jun 2018. URL: https://doi.org/10.2116/analsci.18sbp14, doi:10.2116/analsci.18sbp14. This article has 16 citations and is from a peer-reviewed journal.

28. (seidel2021comparisonofelemental pages 8-10): Peter Seidel, Doreen Ebert, Robert Schinke, Robert Möckel, Simone Raatz, Madlen Chao, Elke Niederschlag, Thilo Kreschel, Richard Gloaguen, and Axel D. Renno. Comparison of elemental analysis techniques for the characterization of commercial alloys. Metals, 11:736, Apr 2021. URL: https://doi.org/10.3390/met11050736, doi:10.3390/met11050736. This article has 30 citations.

29. (seidel2021comparisonofelemental pages 5-7): Peter Seidel, Doreen Ebert, Robert Schinke, Robert Möckel, Simone Raatz, Madlen Chao, Elke Niederschlag, Thilo Kreschel, Richard Gloaguen, and Axel D. Renno. Comparison of elemental analysis techniques for the characterization of commercial alloys. Metals, 11:736, Apr 2021. URL: https://doi.org/10.3390/met11050736, doi:10.3390/met11050736. This article has 30 citations.
