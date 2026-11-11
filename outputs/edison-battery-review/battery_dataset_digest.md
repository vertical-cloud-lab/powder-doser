# Uniform powder test battery — consolidated dataset digest

Repository: vertical-cloud-lab/powder-doser  | Issue #116 | MongoDB collection `powder_doser.battery_runs`

Instrument: single-channel Archimedes-auger powder doser, A&D HR-100A analytical balance (0.1 mg), three-phase closed-loop controller with parameters FROZEN at salt-tuned values across every powder (bulk 55 RPM / tilt 90 with 0.12 g anticipation -> fine 45 deg increments at tilt 45 -> phase-3 solenoid tap trim at tilt 0, +/-5 mg tolerance).

Fixed test blocks per powder: A baseline (8 no-actuation reads @45), B static hold (15 s @0/45/90), C feed-factor (6x360 deg @30 RPM per tilt 0/45/90), D speed sweep (3 rev @15/45/90 RPM @45), E tap (8 single-tap trials @0 and 45, each with a 360 deg re-feed accounting), F vibration (SKIPPED all runs — DRV2605L unavailable/not attached), G three-phase closed-loop 3x1.000 g doses.


## Cross-powder summary (7 valid runs)

| Powder | feed mg/rev @0/45/90 | best RSD | speed trend 15->90 RPM (mg/rev) | tap mg @45 | mean 1 g dose error | dose statuses |
|---|---|---|---|---|---|---|
| calcium-lactate | 47.3 / 198.3 / 232.2 | 2.2% @45 | 190.4 -> 128.5 (-33%) | 20.36 | -26.5 mg | 3x stalled |
| xanthan-gum | 23.7 / 161.2 / 186.8 | 4.0% @90 | 233.3 -> 105.9 (-55%) | 13.61 | -32.9 mg | 3x stalled |
| carboxymethyl-cellulose | 2.6 / 26.3 / 9.3 (peaks @45!) | 9.1% @45 | 23.4 -> 28.8 (+23%) | 0.15 | -43.2 mg | 3x stalled |
| salt | 5.6 / 17.1* / 24.9* | 12.5% @0 | entangled w/ drift | 3.05 | +0.2 mg | 2 ok, 1 overshoot |
| white-rice-flour | 3.75 / 12.78 / 37.15 | 22% @45 | 19.1 -> 37.0 (+94%) | 0.11 | -138 mg | 3x cycle-budget |
| sodium-alginate | 0.75 / 9.58 / 10.87 | 8% @45 | 11.1 -> 13.0 (+17%) | 0.24 | -292 mg | 3x cycle-budget |
| brown-rice-flour | 0.30 / 0.25 / 0.20 (no tilt dep) | — (below res.) | 0/0/2.6 mg | 0.16 | stalled ~0 g | 3x stalled |

\* salt block-C feed factor is a LOWER BOUND — see drift note below.


## Closed-loop dose detail (block G, frozen salt-tuned controller)


**calcium-lactate**
- dose 1: 0.9846 g, err -15.4 mg, stalled, 265 s, cycles bulk:13;fine:16;tap:83, taps 166
- dose 2: 0.9654 g, err -34.6 mg, stalled, 263 s, cycles bulk:15;fine:16;tap:82, taps 164
- dose 3: 0.9705 g, err -29.5 mg, stalled, 215 s, cycles bulk:15;fine:16;tap:57, taps 114

**xanthan-gum**
- dose 1: 0.9564 g, err -43.6 mg, stalled, 174 s, cycles bulk:16;fine:16;tap:38, taps 76
- dose 2: 0.9699 g, err -30.1 mg, stalled, 199 s, cycles bulk:18;fine:18;tap:45, taps 90
- dose 3: 0.9750 g, err -25.0 mg, stalled, 193 s, cycles bulk:18;fine:18;tap:43, taps 86

**carboxymethyl-cellulose**
- dose 1: 0.9511 g, err -48.9 mg, stalled, 651 s, cycles bulk:53;fine:135;tap:33, taps 66
- dose 2: 0.9575 g, err -42.5 mg, stalled, 668 s, cycles bulk:51;fine:136;tap:39, taps 78
- dose 3: 0.9619 g, err -38.1 mg, stalled, 688 s, cycles bulk:56;fine:137;tap:46, taps 92

**salt**
- dose 1: 0.9953 g, err -4.7 mg, ok, 265 s, cycles bulk:16;fine:42;tap:35, taps 70
- dose 2: 0.9965 g, err -3.5 mg, ok, 204 s, cycles bulk:15;fine:39;tap:14, taps 28
- dose 3: 1.0088 g, err +8.8 mg, overshoot, 113 s, cycles bulk:14;fine:26;tap:0, taps 0

**white-rice-flour**
- dose 1: 0.8597 g, err -140.3 mg, cycle-budget, 822 s, cycles bulk:51;fine:200, taps 0
- dose 2: 0.8399 g, err -160.1 mg, cycle-budget, 825 s, cycles bulk:48;fine:200, taps 0
- dose 3: 0.8868 g, err -113.2 mg, cycle-budget, 818 s, cycles bulk:36;fine:200, taps 0

**sodium-alginate**
- dose 1: 0.7285 g, err -271.5 mg, cycle-budget, 836 s, cycles bulk:103;fine:200, taps 0
- dose 2: 0.6928 g, err -307.2 mg, cycle-budget, 840 s, cycles bulk:113;fine:200, taps 0
- dose 3: 0.7043 g, err -295.7 mg, cycle-budget, 843 s, cycles bulk:114;fine:200, taps 0

**brown-rice-flour**
- dose 1: 0.0018 g, err -998.2 mg, stalled, 6 s, cycles bulk:16, taps 0
- dose 2: 0.0008 g, err -999.2 mg, stalled, 8 s, cycles bulk:17, taps 0
- dose 3: 0.0000 g, err -1000.0 mg, stalled, 7 s, cycles bulk:14, taps 0

## Key analytical observations (to be validated/critiqued)

1. **Feed factor spans 3 orders of magnitude** on identical hardware with identical parameters: 232 mg/rev (calcium lactate @90) down to <0.3 mg/rev (brown rice flour, 72% of revolutions below the 0.1 mg balance resolution).

2. **Speed dependence separates flow regimes.** Mass PER REVOLUTION vs auger RPM (15->90 RPM, 6x):
   - Cohesive/free-flowing "filling-limited by time": mass/rev FALLS with speed — calcium lactate -33%, xanthan gum -55% (flights get less time to fill under gravity).
   - Cohesive "filling-limited by cohesion": mass/rev RISES with speed — white rice flour +94% (faster rotation fluidises, packs flights fuller).
   - Near-geometric metering: sodium alginate +17%, CMC +23% (mass/turn ~ independent of speed).

3. **Tap efficacy is a powder property that tracks feed factor**, not a fixed hardware limit. Solenoid tap (single 60 ms pulse @45 deg) moves 20.4 mg (Ca-lactate) / 13.6 mg (xanthan) for the two highest-feed powders, but <0.25 mg (indistinguishable from zero, RSD >180%) for the low-feed powders. Threshold ~100 mg/rev.

4. **Non-monotonic tilt for CMC**: feed factor peaks at 45 deg (26.3 mg/rev) and FALLS 2.8x at vertical (9.3 mg/rev, RSD 157%). Revolution-by-revolution at 90 deg: 39.0, 7.4, 4.0, 1.8, 1.4, 2.5 mg — first revolution discharges pre-charged flights, then feed collapses. Interpreted as arching over the vertical auger intake; tilting to 45 deg lets powder slump into the flights. Every other powder is monotonic or saturates above 45.

5. **Manual (hand) vs rig disagreement is bidirectional, so not a correctable offset.** Xanthan gum: operators saw "burst then clog when vertical"; rig shows 90 deg is fastest AND most repeatable. CMC: operators "prefer vertical"; rig shows 2.8x worse at vertical. Hypothesis: hand tests measure gravity-driven flowability; the rotating auger mechanically breaks arches, decoupling conveyed rate from static flowability. This is offered as the motivation for characterising powered conveying separately in the manuscript.

6. **Dose accuracy is UNCORRELATED with feed factor** and correlated with proximity to salt's properties. Under the frozen salt-tuned controller only salt lands on target (mean +0.2 mg, 2/3 within +/-5 mg); calcium lactate conveys 13x more than salt yet misses by 26 mg; sodium alginate conveys LESS than salt yet misses by 292 mg. Two failure modes: `cycle-budget` (bulk stops early on salt-tuned 0.12 g anticipation, fine can't close 0.38 g gap in 200 cycles) for slow powders; phase-3 `stalled` (fine oversteps 50 mg handover, phase-3 taps at tilt 0 where tap quantum collapses ~90x) for fast powders. This is presented as the core evidence that one frozen parameter set cannot serve all powders — motivating per-powder tuning (future work, issues #123/#130).

7. **Salt control is only marginally stable and DRIFTS within a single 17-min run.** Dose errors -4.7 -> -3.5 -> +8.8 mg (monotone); block C vs block E independently measure mg/rev at the same tilt/RPM ~5 min apart, agreeing to 0.74-1.12 for six powders but 2.68x for salt. So salt's block-C feed factor is reported as a lower bound and its block-D speed slope as uninterpretable. Cause unresolved (candidates: tap priming, tilt-change slumping).

8. **No powder avalanches through a stationary auger, even fully vertical** (block B = 0 at all tilts, all 7 powders). Flow is auger-gated, not gravity-gated — the auger acts as a meter, not a valve.

## Data provenance / QC
- 7 valid runs (`qc.valid_for_cross_powder_comparison=true`), batch `food-safe-2026-08`. 2 retracted brown-rice-flour runs (early no-conveyance, superseded by auger #2). Brown rice flour is the dataset lower bound — this geometry cannot convey it (confirmed across 2 augers + an operator hand test of 20 turns -> 0.0019 g).
- Independent corroboration by prior manual operator testing (@carl-robison) recorded in issue #116.
- Balance noise floor below 0.1 mg display resolution (block A deltas exactly 0.0000 g every run).

## Specific questions for Edison review (in the context of manuscript #97/#103, Digital Discovery hardware Full Paper)
1. Is the "frozen salt-tuned controller applied to all powders" framing sound as the paper's central argument for per-powder characterisation, and is it presented fairly (i.e. not strawmanning the controller)?
2. Are the flow-regime interpretations from the speed sweep (obs. 2) mechanistically defensible, or overreaching from n=3 revolutions per speed point?
3. Is the arching interpretation of CMC's non-monotonic tilt (obs. 4) adequately evidenced, and what additional measurement would confirm it?
4. The salt intra-run drift (obs. 7) undermines the control. How should this be handled in the manuscript — repeat run, caveat, or does it threaten the cross-powder comparison?
5. Which of these results are publication-quality figures for the DD paper vs. which need more replicates? The battery has n=1 run per powder (except brown rice flour).
6. What statistical treatment (error bars, RSD reporting, below-resolution handling) would reviewers expect, and are we handling below-balance-resolution values correctly (reported as upper bounds)?
7. Gaps: block F (vibration) missing entirely; real metal powders (AlSi10Mg, Si) not yet run. How much do these limit the current claims?
