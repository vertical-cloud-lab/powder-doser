# Auger-doser screen for LPBF spreading

**Recommendation:** Use two *screening* values—a gravity-assisted volumetric feed index and a low-speed interruption fraction—alongside a same-session commercial AlSi10Mg reference. I would not call either a validated laser powder bed fusion (LPBF) spreadability measurement. The auger tests a different shear geometry from a recoater.

[Full report and methods](./analysis/report.md) · [Reproducible Python](./analysis/analysis.py) · [Per-powder feature table](./analysis/feature_table.csv) · [Correlation table](./analysis/correlations.csv) · [Resolution figure](./analysis/resolution_and_tilt.png) · [Production comparison](./analysis/production_comparison.png)

## 1. Resolution

I analyzed **14 quality-control-valid A–E runs**, comprising 252 block-C single revolutions. I excluded later G/H-only runs from these statistics. For stable salt repeatability I additionally excluded the documented under-filled 2026-08-06 run; including it changes salt’s between-day coefficient of variation (CV) at 90° from **9.9%** to **74.8%**. There are only **two** comparable salt days and no other powder with two valid A–E runs.

| Measurement | Result |
|:--|:--|
| Balance baseline, four runs with populated nonzero noise fields | Median stable-read `sigma_g` **6.6 mg**; baseline-difference standard deviation **2.9–28.9 mg** across runs; median absolute `drift_g` **5.55 mg**; nonzero shock in **17/32** baseline actions. Earlier missing/zero noise fields are not evidence of a noiseless balance. |
| Block-C reading quality | **2/252** revolutions flagged shock; **60/252** marked unsettled. Observed turn-to-turn CV contains both balance error and real transport variation; these data cannot reliably separate them. |
| AlSi10Mg FF at 0° / 45° / 90° | **48.9 / 231.0 / 338.9 mg/rev**; within-run CV **33.9% / 13.5% / 4.45%**. Removing one flagged 90° shock reduces the last CV to **2.75%**. |
| Salt FF at 0° / 45° / 90°, two well-charged days | **36.2 / 160.9 / 247.8 mg/rev**; pooled within-run CV **21.1% / 12.7% / 10.2%**; between-day CV of six-turn means **7.2% / 12.7% / 9.9%**, very uncertain with two days. |
| Continuous block-D, three-turn mass-versus-time slope | Median fit \(R^2\): **0.982 / 0.978 / 0.899** at 15 / 45 / 90 rpm. The fitted slopes correspond to just **0.78 / 0.75 / 0.59** times endpoint mass/3, respectively: startup, lag, short windows and correlated polls introduce bias. Fit *post-prime fixed-speed* segments, not arbitrary full traces. |
| Salt, repeated short bulk trials at 40°, 100 rpm, 2-Hz taps | Nine identical-setting stop-mass/time rates: mean **0.0376 g/s**, CV **29%**. Early cutoff, priming and afterflow make this a warning about bulk-trial variability, not a calibrated turn-level error estimate. |

For **two independent batches on the same day**, equal stationary per-turn CV \(c\), \(n\) effective independent revolutions *per batch*, two-sided \(\alpha=0.05\) and 80% power, the optimistic normal-approximation minimum detectable fractional difference is \(\mathrm{MDD}(n)\simeq3.96c/\sqrt n\). Correlated revolutions, reference/loading drift and systematic errors worsen it; polls are **not** independent revolutions.

| CV source | MDD with six turns | Turns per batch for 3% / 5% / 10% difference |
|:--|--:|:--|
| AlSi10Mg, 0° | 54.8% | 2,002 / 721 / 181 |
| AlSi10Mg, 45° | 21.8% | 316 / 114 / 29 |
| **AlSi10Mg, 90°** | **7.2%** | **35 / 13 / 4** |
| Salt, 45° | 20.5% | 280 / 101 / 26 |
| **Salt, 90°** | **16.5%** | **181 / 66 / 17** |

The large-turn extrapolations are design calculations, **not demonstrated precision**. A single unpaired run on each of two days would have an approximate **39%** MDD from salt’s 90° between-day CV alone. Same-session referencing may cancel some day effects, but two comparable salt days cannot quantify how much.

## 2. Which features look useful?

FF is single-turn feed factor. Volumetric FF90 divides mg/rev by literature bulk density in g/mL to obtain µL/rev; actual batch density should replace literature density in routine use. The *interruption fraction* below counts streamed 15-rpm, 45° block-D poll increments below **2 mg per poll** after priming; it is noise- and polling-rate-dependent. A nonconveying powder is **censored**, not a zero-valued flowing powder.

| Powder | FF0 / FF45 / FF90, mg/rev | Volumetric FF90, µL/rev | Interruption fraction | AoR, degrees |
|:--|:--|--:|--:|--:|
| Salt | 36 / 161 / 248 | 208 | 0.26 | 32 |
| Sodium alginate | 0.8 / 9.6 / 10.9 | 20 | 0.96 | 42 |
| Silicon 110–200 | 57 / 211 / 302 | 242 | 0.19 | 36 |
| **Commercial AlSi10Mg** | **49 / 231 / 339** | **251** | **0.13** | **30** |
| Brown rice flour; silicon-325 | Nonconveying | Censored | Censored | 47; 43 |

All 10 conveying powders, including the remaining food and chemical powders, are in the linked CSV. Fumed silica failed outlet-verification quality control; its apparent FF is not a valid cohesion anchor.

| Feature versus **class-typical literature** property | Spearman \(\rho\) vs AoR | \(\rho\) vs Hausner ratio | \(n\) |
|:--|--:|--:|--:|
| Mass FF90 | **−0.77** | −0.50 | 10 |
| Volumetric FF90 | −0.46 | +0.05 | 10 |
| FF90/FF0, where FF0 resolves | +0.23 | +0.12 | 8 |
| 15→90-rpm feed-factor change at 45° | +0.83 | +0.27 | 10 |
| Per-revolution RSD at 90° | +0.35 | −0.13 | 10 |
| Low-speed interruption fraction | **+0.76** | +0.21 | 10 |
| Rate median absolute deviation / mean; priming delay | −0.57; +0.28 | −0.14; +0.28 | 10 |
| Revolution-frequency spectral share | −0.49 | −0.78 | 10 |

I favor **90° feed and interruption**: they both associate with AoR but are less redundant with one another (\(\rho=-0.66\)) than speed slope and interruption (\(\rho=+0.87\)). Volumetric normalization is useful for comparing filling *volume*, but its AoR correlation is weaker than mass FF90. Spontaneous B discharge and E tap quanta are often zero, shock-contaminated or unresolved on the noisy metal bench. The spectral estimate has only about three 15-rpm cycles. None is ready as a third acceptance criterion. Hausner associations are inconsistent; literature values are class estimates rather than measurements on these lots. Multiple unadjusted exploratory correlations across only 10 heterogeneous powders cannot establish LPBF predictive validity.

## 3. Al 4047 versus AlSi10Mg, matched bulk settings

Both comparable bulk phases used **40°, 100 rpm and 2-Hz taps**. Post-prime AlSi10Mg’s mass trace has a **0.236 g/s** slope over 30–58 s; its nonoverlapping 2-s rates average **0.226 g/s**, CV **0.15**. The clogged Al 4047 continuation delivered **4.173 g in 368.84 s**, or **0.0113 g/s** overall—about **20-fold slower**—with an early logged 2-s-rate CV **0.32**. It stopped at the shallow 10° trickle setting; 15° tapping scarcely helped. A separate variable-speed top-up required no-flow-triggered rpm boosts. Both powders have *zero fully stopped* 2-s windows in the selected early fixed-speed windows: the salient signature is sustained depressed throughput and failure at shallow tilt, not simply more zero windows.

**A trustworthy long-time decay constant is unavailable.** The initial ~100-s Al 4047 trial lost telemetry to a firmware `MemoryError`; the ~369-s continuation retains only its first ~30 s of streamed observations. An exploratory fit to that beginning gives \(\tau\sim28\) s with log-rate \(R^2=0.68\), but the later endpoint rate contradicts a single exponential. Observed oversize chunks lodged in the tube, progressive restriction and shallow-angle failure point to **mechanical jamming**; persistent poor flow *after* sieving, cleaning and controlling fill would instead strengthen an intrinsic-cohesion hypothesis. That intervention has not yet been tested.

## 4. Proposed per-batch procedure and two numbers

**Before instrument time:** sieve to the intended LPBF upper-size cut, document retained oversize mass and images, and dry/cool under a validated alloy-safe protocol. Drying is **outside** the ~15-minute instrument budget. Measure *lot* bulk density; standardize hopper fill to **30 g if it fits**, otherwise a fixed fill height. Clean and verify the outlet. Run a separately timed, sieved commercial AlSi10Mg reference **in the same session**, at the same fill and conditions.

1. Collect eight motor-off baseline reads and a 15-s hold at 90°. Provisionally stop for inspection if baseline-difference SD exceeds **10 mg** or shocks persist. Prime at 45°/30 rpm until slopes of consecutive three-turn segments differ by <10%; if it takes >30 turns or conveys nothing, inspect/reprime and record **nonconveyance**, not FF = 0.
2. With **taps off**, measure **two six-turn sets each at 45° and 90°**, 30 rpm, with stable before/after reads. Add three turns at 0° only as a tilt diagnostic. Record shocks and unsettled reads. Run six continuous revolutions at **45°, 15 rpm**, sampling mass; score post-prime fixed-speed intervals. Do not infer a 90-rpm revolution spectrum from the 2.5–4-Hz balance stream.
3. If time permits, refill/reprime once and report the two results separately. Omit routine tap testing from the short panel; four paired refill-and-tap checks at 45° can be a diagnostic when needed. A full A–E battery can already take ~13–15 minutes, so this shortened panel—not full A–E plus replicates—is the **~15-minute-per-sample instrument target**, excluding offline conditioning and the separately timed reference.

Define two dimensionless readouts relative to reference \(R\):

\[
V_g=\frac{FF_{90,\mathrm{batch}}/\rho_{b,\mathrm{batch}}}{FF_{90,R}/\rho_{b,R}},\qquad
I_{\mathrm{stop}}=\frac1N\sum_{i=1}^{N}\mathbf1\!\left[\Delta m_i<\max\{2\,\mathrm{mg},3\sigma_{\Delta m}\}\right],\quad
\Delta I=I_{\mathrm{stop,batch}}-I_{\mathrm{stop},R}.
\]

Here \(\sigma_{\Delta m}\) is a **same-session, motor-off poll-difference noise** estimate; calibrate the threshold to this sensor. \(V_g\) is a gravity-assisted volumetric flow proxy; \(I_{\mathrm{stop}}\) is a dynamic interruption/cohesion proxy, analogous in *purpose*, not calibration or mechanics, to a rotating-drum cohesive index. For six effective 90° turns the FF component has an optimistic **~7% AlSi10Mg or ~17% salt MDD**; the independent reference adds uncertainty. There is **no experimentally established resolution** for \(I_{\mathrm{stop}}\): at best, 24 independent one-second windows per powder with control fraction 0.13 imply an MDD of **~0.27 absolute fraction**. Serial correlation and variable read noise make it worse.

**Provisional hold/inspect flag:** \(V_g<0.8\), or \(\Delta I>0.30\), or no conveyance / >30 prime turns. Repeat against the same-day reference before judging a batch; near-threshold results are *indeterminate*. Validate cutoffs against actual spread coupons, layer density, streaks and LPBF outcomes from future **sieved aluminium-alloy lots**. Sieving/direct spreading is indispensable: an auger may reveal a chunk-induced jam or intermittent low throughput, but cannot reliably detect rare oversize recoater streaks, thin-layer low density from fines, agglomerate smearing or blade/roller-specific shear failures.

### Discretionary analytical decisions
- I retained only valid A–E measurements for battery statistics and treated invalid outlets and nonconveyors as censored; I separately excluded the documented under-filled salt run from normal repeatability.
- I used observed single-turn CV for conservative *within-run* planning rather than subtracting poorly characterized balance noise, and I labeled the independence-based power calculations optimistic.
- I chose FF90 plus low-speed interruption over speed slope or spectral/tap measures to cover gravity-assisted throughput and a less-redundant stopping mode; I used lot density for the proposed operational volumetric index.
- I did not assign Al 4047 a long-time decay constant because the relevant streamed observations were lost or truncated.
