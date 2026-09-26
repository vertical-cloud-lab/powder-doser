# Low-rpm stop battery + quantum vs tilt -- salt

## Flow checks (1 rev @ 1rev@30rpm@55deg, fill/stationarity index)

| block | label | g/rev |
|---|---|---|
| 1 | D_pre | 0.0006 |
| 2 | D_pre | 0.0426 |
| 3 | D_pre | 0.0821 |
| 4 | D_pre | 0.0517 |
| 5 | D_pre | 0.0531 |
| 6 | D_post | 0.1054 |
| 90 | D2_pre | 0.0328 |

first 0.0006 -> last 0.0328 g/rev (ratio 54.67); mean 0.0526, sd 0.0338 (CV 64%)

## Stop battery at tilt 25 deg (n=8)

| rpm | n | afterflow mean +/- sem (mg) | sd (mg) | flow at halt (g/s) | ff (g/rev) |
|---|---|---|---|---|---|
| 5 | 2 | 18.9 +/- 16.5 | 23.4 | 0.0168 | 0.1816 |
| 10 | 2 | 2.0 +/- 1.0 | 1.5 | 0.0133 | 0.0779 |
| 15 | 2 | 13.2 +/- 13.4 | 19.0 | 0.0147 | 0.0608 |
| 25 | 2 | 1.1 +/- 4.2 | 5.9 | 0.0203 | 0.0458 |

OLS afterflow(mg) = AF0 + tau * flow(g/s):  **AF0 = 25.3 +/- 32.2 mg**, tau = -1.013 +/- 1.955 s (as mg per g/s: -1013), R2 = 0.04, n = 8

restricted to rpm <= 15 (n=6): AF0 = -8.5 +/- 65.7 mg, tau = 1.331 +/- 4.373 s, R2 = 0.02

slowest-rpm afterflow (the direct AF0 probe): 18.9 +/- 16.5 mg (n=2)

## Stop battery at tilt 55 deg (n=20)

| rpm | n | afterflow mean +/- sem (mg) | sd (mg) | flow at halt (g/s) | ff (g/rev) |
|---|---|---|---|---|---|
| 5 | 5 | -7.9 +/- 2.7 | 6.1 | 0.0282 | 0.3492 |
| 10 | 5 | 8.9 +/- 1.6 | 3.6 | 0.0319 | 0.1940 |
| 15 | 5 | 4.4 +/- 3.7 | 8.3 | 0.0167 | 0.0708 |
| 25 | 5 | 8.8 +/- 3.7 | 8.3 | 0.0264 | 0.0624 |

OLS afterflow(mg) = AF0 + tau * flow(g/s):  **AF0 = 6.6 +/- 7.3 mg**, tau = -0.117 +/- 0.271 s (as mg per g/s: -117), R2 = 0.01, n = 20

restricted to rpm <= 15 (n=15): AF0 = 3.5 +/- 7.8 mg, tau = -0.068 +/- 0.289 s, R2 = 0.00

slowest-rpm afterflow (the direct AF0 probe): -7.9 +/- 2.7 mg (n=5)

## Does AF0 scale with tilt?

| tilt | AF0 (mg) | tau (s) | R2 | n |
|---|---|---|---|---|
| 25 | 25.3 +/- 32.2 | -1.013 +/- 1.955 | 0.04 | 8 |
| 55 | 6.6 +/- 7.3 | -0.117 +/- 0.271 | 0.01 | 20 |

## Quantum vs tilt at trim speed (10.0 rpm, 20.0 deg increments, weighed at rest)

| tilt | n | mean yield (mg) | sd (mg) | CV | mg/deg | sd mg/deg | min..max (mg) | implied g/rev |
|---|---|---|---|---|---|---|---|---|
| 15 | 36 | 6.48 | 36.38 | 561% | 0.324 | 1.819 | -81.0..65.2 | 0.1167 |
| 35 | 36 | 6.96 | 31.24 | 449% | 0.348 | 1.562 | -56.5..63.8 | 0.1253 |
| 55 | 36 | 5.62 | 27.50 | 490% | 0.281 | 1.375 | -56.3..62.2 | 0.1011 |

## Diagnostics -- is the per-increment scatter real powder?

A yield is a DIFFERENCE of two consecutive weighs, so reading
noise e appears as +e then -e: independent true yields give a
lag-1 autocorrelation of 0, pure reading noise gives -0.5, and
the sd of the sum of k consecutive increments grows as sqrt(k)
only if the increments are independent.

| tilt | n | lag-1 acf | sd(1 incr) | sd(sum of 18) | sqrt(18)*sd if independent |
|---|---|---|---|---|---|
| 15 | 36 | -0.54 | 36.4 mg | 26.8 mg | 154.4 mg |
| 35 | 36 | -0.56 | 31.2 mg | 9.8 mg | 132.5 mg |
| 55 | 36 | -0.48 | 27.5 mg | 2.4 mg | 116.7 mg |

Static noise stream (servo home, nothing actuating): sd 0.39 mg, p2p 1.50 mg, n=79

Consecutive at-rest weighs with NO powder moved between them (settled of trial N -> base of trial N+1, ~1.4 s apart, servo re-tilt in between): mean -0.02 mg, sd 0.18 mg, p2p 0.80 mg, n=22 -- the balance itself is quiet.

## Afterflow decomposition (step at de-energise vs tail)

| tilt | rpm | n | step at de-energise (mg) | settling tail (mg) | total afterflow (mg) |
|---|---|---|---|---|---|
| 25 | 5 | 2 | +0.5 +/- 6.1 | +18.4 +/- 17.3 | +18.9 +/- 23.4 |
| 25 | 10 | 2 | +0.4 +/- 1.8 | +1.7 +/- 3.3 | +2.0 +/- 1.5 |
| 25 | 15 | 2 | +0.8 +/- 1.1 | +12.4 +/- 17.8 | +13.2 +/- 19.0 |
| 25 | 25 | 2 | +3.5 +/- 2.5 | -2.4 +/- 8.4 | +1.1 +/- 5.9 |
| 55 | 5 | 5 | +5.3 +/- 6.8 | -13.2 +/- 11.4 | -7.9 +/- 6.1 |
| 55 | 10 | 5 | +2.9 +/- 2.1 | +6.0 +/- 4.4 | +8.9 +/- 3.6 |
| 55 | 15 | 5 | +1.6 +/- 1.4 | +2.8 +/- 9.1 | +4.4 +/- 8.3 |
| 55 | 25 | 5 | +5.0 +/- 6.9 | +3.8 +/- 6.0 | +8.8 +/- 8.3 |

## Is delivery angle-metered or time-metered?

| tilt | rpm | n | flow = dispensed/t_move (g/s) | ff = dispensed/rev (g/rev) |
|---|---|---|---|---|
| 25 | 5 | 2 | 0.0132 +/- 0.0034 | 0.1816 +/- 0.0113 |
| 25 | 10 | 2 | 0.0127 +/- 0.0003 | 0.0779 +/- 0.0016 |
| 25 | 15 | 2 | 0.0147 +/- 0.0001 | 0.0608 +/- 0.0006 |
| 25 | 25 | 2 | 0.0180 +/- 0.0009 | 0.0458 +/- 0.0022 |

tilt 25: across a 5x rpm range the per-rpm MEAN flow spans only 1.41x (0.0127-0.0180 g/s, OLS slope 0.00026 +/- 0.00007 g/s per rpm) while mean g/rev spans 3.96x (0.0458-0.1816, ~1/rpm) -- delivery is set by auger-ON TIME, not by angle.
| 55 | 5 | 5 | 0.0288 +/- 0.0021 | 0.3492 +/- 0.0249 |
| 55 | 10 | 5 | 0.0316 +/- 0.0057 | 0.1940 +/- 0.0348 |
| 55 | 15 | 5 | 0.0171 +/- 0.0042 | 0.0708 +/- 0.0175 |
| 55 | 25 | 5 | 0.0245 +/- 0.0038 | 0.0624 +/- 0.0097 |

tilt 55: across a 5x rpm range the per-rpm MEAN flow spans only 1.85x (0.0171-0.0316 g/s, OLS slope -0.00034 +/- 0.00047 g/s per rpm) while mean g/rev spans 5.59x (0.0624-0.3492, ~1/rpm) -- delivery is set by auger-ON TIME, not by angle.
