# Claims to spot-check — "why is the Kalman filter used in `trickle_tap`, and how does that avoid overshoot?"

Context: a benchtop gravimetric powder doser (auger + solenoid tapper + tilt servo +
A&D HR-100A balance, ~10.4 Hz frames). Target tolerance ±5 mg on doses of 0.3–2.0 g.
Overshoot is a hard **asymmetric** constraint: powder cannot be removed from the vial.

A project member asked why the Kalman filter is used during the low-rate trim
("trickle") stage, given an earlier write-up cautioning that a rate estimate becomes
meaningless at very low flow. The answer below was produced by instrumenting a
`bangbang_trim` dose on the calibrated digital twin (`diag_trickle_stages.py`,
uploaded; raw output uploaded as `diag_trickle_stages.txt`; 360 doses = 3 powders
× 2 contexts × 2 targets × 30 seeds, plus a 180-dose ablation grid).

**Please audit each numbered claim: is it supported by the uploaded code + numbers,
is the reasoning sound, and where is it wrong, overstated, or confounded?**
Be concrete — name the file/function/line and the specific correction.

---

## The controller under discussion

`bangbang_trim` (`bangbang.py`) = stage 1 max-rate "bang" halted a fixed 0.30 g guard
below target → stage 2 `trickle_tap()`: a rate-PI trickle at ~20° tilt whose cutoff
rule is

```
stop when   m_hat + r_hat * tau + k_sigma * sigma_pred  >=  target - margin
            tau = 0.30 s, k_sigma = 1.0,
            margin = 0.035 g + 0.06 * max(0, ff_hat - 0.30 g/rev)
```

→ stage 3 `tap_finish()` (`controllers.py`): auger off, tilt to horizontal, then
tap → 1.2 s settle → **stable** balance reading, repeated until within tolerance.

`m_hat`, `r_hat`, `sigma_pred` come from `MassRateLagKF`, a 3-state
(true mass, rate, balance internal reading) linear KF: the balance frame is
modelled as a measurement of the *lagged* internal state `b` (H = [0,0,1]),
`b' = (m-b)/tau_bal`, so `m_hat` is lag-free. R switches between
`QUIET_SD = 0.5 mg` and `NOISY_SD = 8 mg` keyed to the controller's own
actuation state; predict runs every 0.2 s tick, update only on a fresh balance tick.

## Measured numbers (360 doses, calibrated twin)

Cutoff decision budget (mg below target):

| term | value |
|---|---|
| fixed margin | 35.0 mg |
| `r_hat * tau` | 12.7 mg |
| `k_sigma * sigma` | 4.8 mg |
| **total stop-early budget** | **52.4 mg** |

`|m_hat − truth|` at cutoff: median 9.0 mg (signed median +0.9 mg).
KF rate-estimate scatter vs the twin's true rate during the trickle: sd 0.042 g/s,
i.e. ±12.4 mg of jitter on the `r_hat*tau` term, at a cutoff rate of 0.042 g/s
(18 auger rpm). Identified `ff_hat` at cutoff: median 0.113 g/rev (max 0.198).

Stage-by-stage (mg relative to target): cutoff est −47.6 / true −48.9 →
post-cutoff lip drain during the 1.2 s settle **+26.0 mg (p95 +52.4)** →
tap endgame entry −19.8 → 11 taps × ~1.2 mg → final −4.0 mg. 55 % within ±5 mg;
strict overshoot 22 %.

Ablations (nominal context, 15 seeds × 3 powders × 2 targets, shared seeds):

| variant | med signed (mg) | p95 | over % | ±5 mg % | med t (s) |
|---|---|---|---|---|---|
| as implemented | −2.6 | 15.3 | 31 | 61 | 43 |
| no `k*sigma` cushion | −0.6 | 15.3 | 47 | 58 | 36 |
| no fixed margin (KF terms only) | +26.4 | 49.4 | 94 | 8 | 25 |
| KF mass, but raw finite-diff rate | −3.8 | 9.4 | 21 | 61 | 84 |
| no KF (raw balance + finite-diff rate) | +18.6 | 133.8 | 76 | 14 | 16 |
| no KF and no margin | +53.7 | 133.8 | 100 | 1 | 16 |

---

## Claims

**C1 — Attribution.** "The Kalman filter is not what prevents overshoot; a
deliberate ~35 mg undershoot margin and a tap endgame that measures at rest are.
The KF's predictive term is only 12.7 mg of a 52.4 mg stop-early budget (24 %;
33 % including `k*sigma`)." Is decomposing a threshold rule into additive term
magnitudes a legitimate way to attribute *safety* responsibility, or does it
confuse term magnitude with counterfactual effect (the ablations are meant to
supply the counterfactual — do they)?

**C2 — One-signedness.** "All three terms (`margin`, `r_hat*tau`, `k*sigma`) are
one-signed: rate noise moves the stop point earlier or less-early, never past
target — so a bad rate estimate cannot flip the sign into an overshoot."
`r_hat` is clamped `>= 0` in `MassRateLagKF.update`. But the decision variable
also contains `m_hat`, whose error *is* two-signed (median |error| 9 mg). Is the
claim as stated defensible, or does it need to be restated as "the *rate* channel
is one-signed while the *mass* channel is not"? Is there a standard framing for
this (e.g. one-sided/asymmetric stopping rules, safety margins on a biased
estimator, first-crossing/optional-stopping bias)?

**C3 — "Self-correcting" uncertainty term.** "The `k*sigma` term is
self-correcting: when the scale has been noisy and the filter is unsure, sigma is
large and the halt fires earlier; when the filter is confident, it runs closer to
the line. The margin sizes itself to the current data quality."
**We suspect this is wrong as stated**: for a linear KF, P follows a deterministic
Riccati recursion that does not depend on the realized innovations, so
`sigma_pred` responds only to the *modelled* regime (R switched by the
controller's own actuation state) and to time since seeding / missed updates —
not to empirically observed noise. Please confirm or refute, and say what the
`k*sigma` term *actually* adapts to here. If it is effectively a near-constant
~5 mg addition to the margin, why does removing it change strict overshoot from
31 % to 47 % (see C5)? Would an innovation-based (adaptive/covariance-matching)
scheme, or a normalized-innovation-squared consistency test, be the right way to
get the behaviour we mistakenly claimed?

**C4 — Regime.** "The trickle is not in the regime the earlier write-up warned
about: at cutoff it runs at 0.042 g/s (18 rpm), ~4× above the ≤0.01 g/s regime
where 'rate' stops being a meaningful quantity for an avalanching powder;
below that the code hands over to taps, where no prediction is used." Bench data
(salt, auger stepped in 45° increments, n = 64) gave mean yield 6.4 mg per 45°
with sd 15.9 mg — i.e. per-increment scatter 2.5× the mean. At what flow rate
does a rate-based (continuum) description stop being defensible for such a
marked point process, and is 0.042 g/s comfortably inside it? Is there a
principled criterion (e.g. expected inter-avalanche interval vs filter time
constant / sampling period)?

**C5 — Ablation inference.** Three inferences drawn from the ablation table:
(a) "the fixed margin is the safety mechanism" (removing it → 94 % overshoot);
(b) "removing the KF is bad mainly because the *mass* channel loses lag
correction — the raw reading lags so the cutoff fires ~29 mg later", not because
the rate channel degrades; (c) "the filtered rate buys speed, not safety" —
substituting a deliberately crude rectified finite-difference rate is *safer*
(21 % vs 31 % overshoot, better p95) but nearly 2× slower, because rectified
noise biases that estimate high, which enlarges `r_hat*tau` and stops earlier.
Is (c) a sound inference, given that `r_hat` feeds **both** the cutoff rule and
the rate-PI feedback loop (`err = r_sp - r`) and the taper
`r_sp = (remaining - margin)/(2*tau)`, so the ablation is not a single-term
manipulation? How should we design a cleaner ablation (e.g. hold the trajectory
fixed and vary only the stopping statistic, or a common-random-numbers /
counterfactual-replay design)? Are 15 seeds × 6 cells enough to support these
comparisons, and what paired statistic would you use?

**C6 — Dominant post-cutoff uncertainty.** "The lip drain during the 1.2 s
post-cutoff settle (median +26 mg, p95 +52 mg at 20° tilt), not the rate
estimate, is the dominant post-cutoff uncertainty, and the 35 mg margin is
really sized against *drain*, not afterflow." Note this is a **twin-model**
quantity: `powder_sim.py` discharges the lip at `1.2*s^2*(1-2.2*coh)` per second
(s = sin(tilt)/sin 45°) plus a marked avalanche process, and the passive drain
law is provisional/uncalibrated. Bench data (2026-08-07, salt) showed settling
complete in 0.7–1.5 s with *no creep past ~2 s* after a halt, which arguably
contradicts a 25 %/s passive drain at 20°. How much of the write-up's causal
story survives if the real lip does not passively drain? What is the minimal
bench experiment that discriminates (we proposed: halt mid-trickle at 20°, hold,
log 10 s)? Is there published evidence on post-halt discharge from an inclined
auger lip / tube outlet?

**C7 — Overshoot taxonomy.** "Half the strict overshoots are ≤ a couple of mg
(a single tap slug crossing, median +1.4 mg — inside tolerance, just on the wrong
side of a strict `>target` test); the ones that matter (11 % of doses, median
+12.3 mg) all trace to the cutoff firing late, not to the rate estimate."
Is splitting the overshoot rate by handoff sign a fair diagnostic, and is
reporting a "strict overshoot" rate alongside a ±5 mg tolerance rate the right
pair of metrics for an asymmetric-constraint dosing problem? What does the
gravimetric-filling / loss-in-weight-feeder literature use?

**C8 — Recommendations.** Ranked list given: (1) add the bench-measured
speed-independent afterflow intercept `AF0 ≈ 15 mg` to the cutoff
(`pred = m_hat + AF0 + r_hat*tau`) — our stop-response regression on salt gave
`afterflow ≈ 14.7 mg + 0.30 s × flow` over 15–75 rpm; (2) tilt to horizontal
*before* the post-cutoff settle rather than after, to kill the drain before the
wait; (3) re-derive the margin per powder from the measured drain instead of a
flat 35 mg; (4) replace the rate-PI tail below ~0.02 g/s with
increment-and-measure (small auger angle steps at low tilt, decision taken at
rest). Are these the right priorities? What are we missing — and is (2) risky in
any way we have not considered (e.g. the tilt move itself releasing powder: a
one-off +25.4 mg release was observed on a 50°→60° move)?

**C9 — Dead code.** "The feed-factor-adaptive part of the margin
(`+0.06*max(0, ff-0.30)`) never fires: identified `ff_hat` at cutoff is 0.113 g/rev
median, 0.198 max, so the margin is effectively a hardcoded 35 mg with no powder
adaptation." Confirmed at 0 % of 360 doses. Any reason to keep the term with a
re-scaled threshold rather than delete it?

**C10 — Noise model.** "`NOISY_SD = 8 mg` is applied whenever anything actuates,
including at 18 rpm where the balance is far quieter than at 109 rpm; the filter
under-trusts a good scale precisely where it is good, which is why `|m_hat−truth|`
is 9 mg at cutoff." Is that attribution sound, or could the 9 mg equally come
from process-noise/model mismatch (`Q_discrete_white_noise(var=2e-4)` on the
mass/rate block, `1e-8` on the balance state, `RATE_TAU_S = 0.5`) or from the
input-model term `B = [0, a*ff, 0]`? What is the standard diagnostic to separate
those (innovation whiteness / NIS / NEES against the twin's ground truth), and
would an `R(rpm)` schedule from an empty-hopper vibration sweep be the right fix?

**C11 — Estimator/architecture sanity.** Independent of the claims above: is
`MassRateLagKF` a correct and sensible formulation (state = [m, r, b], H = [0,0,1],
`b` given ~zero process noise, rate clamped ≥0 post-update, R switched on
self-reported actuation, predict-every-tick/update-on-fresh-frame)? Specifically:
(i) is clamping a state after the Kalman update (rather than using a constrained
estimator, e.g. projection with covariance correction, or a truncated/one-sided
prior) a problem for the covariance and hence for `sigma_pred`? (ii) is giving
the balance-state row near-zero process noise numerically safe as P shrinks?
(iii) is the 3-state lag-deconvolution formulation the standard way to invert a
known instrument time constant, and are there better-conditioned alternatives?
(iv) does the fixed `tau_bal = 0.7 s` (twin value; our bench drop tests suggest
~0.16 s) materially change the conclusions above?

**C12 — Overall verdict.** Given all of the above: is the headline answer to the
project member — *"the KF is used in the trickle for rate feedback and a quiet,
lag-free decision variable, but the overshoot protection comes from the fixed
margin plus an at-rest tap endgame; the KF buys speed, not safety"* — correct,
partially correct, or misleading? What is the single most important correction?
