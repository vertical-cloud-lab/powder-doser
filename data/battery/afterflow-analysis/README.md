# Afterflow recovered from the #116 uniform powder battery

Post-hoc extraction (2026-09-11, PR #131) answering: *can afterflow be measured
from the existing 7-powder battery data, and does the rate-at-stop vs afterflow
correlation seen on salt generalize?*

The battery never ran a dedicated stop-response protocol, but two of its blocks
recorded stop events with enough context to recover afterflow per powder:

| Source | Events/powder | What was used |
|---|---|---|
| Block G dose bulk halts | 3 | The frozen three-phase controller polls at ~250 ms while the auger runs continuously (55 rpm, tube vertical), halts at the anticipation threshold, then logs an explicit `+X g while settling` (0.8 s settle + stable weigh). That delta is afterflow; the at-halt mass comes from the halt-decision poll. |
| Block D speed trials | 3 | 3-rev continuous rotations at 15/45/90 rpm (tube tilt 45) stream ~290 ms `POLL` rows (real `t_ms`) until rotation end; the trial row's settled `after_g` lands ~2.1 s later. afterflow = settled − last poll (includes up to ~0.3 s of residual rotation delivery — see caveats). |

Flow at stop is reported two ways: `flow_mean_g_per_s` (dispensed mass /
active dispense time — matches the definition behind the 2026-08-07 salt
stop-response τ) and `flow_slope_g_per_s` (last ~2 s poll slope).

## Files

- `afterflow_from_battery.csv` — tidy per-stop-event table, all powders
- `signature_stats.csv` — per-powder dosing-signature metrics (block C feed
  factors, block D per-rev yields by rpm, block E tap yields, fine/tap cycle
  stats from the dose logs, 15-rpm slug-concentration metrics, dose outcomes)
- `battery_afterflow_correlation.png` — per-powder afterflow vs flow panels +
  fitted τ, with salt's dedicated stop tests (08-07 / 08-12 / 08-17) as the
  reference cloud
- `battery_dose_signatures.png` — per-powder 15-rpm delivery texture and the
  dose bulk ramp with its afterflow jump

Regenerate everything: `python3 scripts/analyze_battery_afterflow.py`

## Headline result

Afterflow = τ × (mean flow at stop) holds for **every powder that flows**,
with τ clustered tightly around one second despite feed factors spanning three
orders of magnitude (pooled over 37 stop events: r = 0.95, pooled τ = 1.07 s):

| powder | τ (s), zero-intercept fit, n=6 |
|---|---|
| CMC | 0.78 ± 0.09 |
| white rice flour | 0.84 ± 0.08 |
| sodium alginate | 0.85 ± 0.06 |
| salt (battery run) | 1.00 ± 0.07 |
| calcium lactate | 1.06 ± 0.04 |
| xanthan gum | 1.17 ± 0.16 |
| brown rice flour | no flow → no τ |

Salt's dedicated stop tests pool to τ = 0.83 ± 0.04 s (n = 84; individual
sessions span ≈0.6–1.1 s), bracketing the battery-derived salt value.

## Caveats

- n = 6 stop events per powder, heterogeneous conditions (2 tilts, 4 rpm), no
  randomization — per-powder τ is provisional at roughly ±0.2 s.
- Block-D points fold ≤0.3 s of end-of-rotation delivery into "afterflow"
  (small upward τ bias on those points; worst at 90 rpm where decel adds
  0.375 s).
- The balance filter (τ_bal ≈ 0.16 s from the 2026-08-14 drop tests) inflates
  all τ values by a shared ~0.1–0.2 s; cross-powder comparisons are
  unaffected.
- At low rpm on slug-mode powders, afterflow is set by slug phase at stop,
  not rate: the salt 15-rpm trial stopped mid-slug and returned a per-point τ
  of 2.5 s (the pooled-fit weighting keeps this from skewing τ). This is the
  same physics the 08-17 low-rpm salt battery mapped, and why phase-aware
  stopping matters below ~20 rpm.
- Each powder lived in its own printed auger (#116 protocol), so auger-print
  variation folds into "powder" differences.
