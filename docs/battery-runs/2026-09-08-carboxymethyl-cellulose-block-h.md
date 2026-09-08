# 2026-09-08 — Carboxymethyl cellulose Block H: misaligned run, then the re-aligned re-run

Two Block H runs (3 × 50 mg + 3 × 200 mg, frozen three-phase controller,
`dose_read_path=bracket`) on the same CMC auger, same day, in the EB B125
fume hood. Between them the operator discovered that **the doser outlet was
misaligned with the balance-enclosure hole** — the stream largely missed the
hole and piled up just behind it
([issue #156](https://github.com/vertical-cloud-lab/powder-doser/issues/156#issuecomment-5590508708))
— and re-aligned the doser and scale.

| | run 1 (misaligned) | run 2 (re-aligned) |
|---|---|---|
| directory | `data/battery/20260908T172730Z_carboxymethyl-cellulose/` | `data/battery/20260908T194201Z_carboxymethyl-cellulose/` |
| started (MDT) | 11:27:30 | 13:42:01 |
| elapsed | 1 h 20 m 37 s | 53 m 14 s |
| end state | `RUN,END,ok` | `RUN,END,ok` |
| MongoDB `_id` | `6aa0626bb0600af999bcc273` | `6aa0724d8fdca8d1acd72cce` |
| `qc.verdict` | `outlet-misaligned` | `ok` (with caveats below) |
| valid for comparison | **false** | **true** |

## Doses

Run 1 (misaligned — the balance saw only the fraction of the stream that fell
through the hole; "delivered" masses under-report actual dispensed powder by an
unknown factor, so none of these are accuracy measurements):

| # | target | delivered | error | status | time | auger rev | taps |
|---|---|---|---|---|---|---|---|
| 0 | 50 mg | 10.4 mg | −39.6 | stalled | 672 s | 2.39 | 330 |
| 1 | 50 mg | 22.9 mg | −27.1 | stalled | 868 s | 7.26 | 326 |
| 2 | 50 mg | 47.4 mg | −2.6 | ok | 622 s | 5.64 | 242 |
| 3 | 200 mg | 156.8 mg | −43.2 | timeout | 902 s | **18.14** | 72 |
| 4 | 200 mg | 196.0 mg | −4.0 | ok | 887 s | 10.69 | 254 |
| 5 | 200 mg | 195.4 mg | −4.6 | ok | 882 s | 11.19 | 264 |

Run 2 (re-aligned):

| # | target | delivered | error | status | time | auger rev | taps |
|---|---|---|---|---|---|---|---|
| 0 | 50 mg | 45.4 mg | **−4.6** | **ok** | 115 s | 1.18 | 56 |
| 1 | 50 mg | 50.2 mg | **+0.2** | **ok** | 211 s | 3.38 | 38 |
| 2 | 50 mg | 47.9 mg | **−2.1** | **ok** | 240 s | 3.57 | 66 |
| 3 | 200 mg | 195.5 mg | **−4.5** | **ok** | 818 s | 9.69 | 234 |
| 4 | 200 mg | 185.8 mg | −14.2 | timeout | 903 s | 11.78 | 240 |
| 5 | 200 mg | 151.0 mg | −49.0 | timeout | 903 s | 14.07 | 178 |

Per-target: 50 mg mean error **−2.2 mg, 3/3 `ok`** (the misaligned run managed
−23.1 mg, 1/3); 200 mg mean −22.6 mg, 1/3 `ok`.

## Findings

**1. The alignment effect is direct and quantified.** The misaligned run needed
18.1 revolutions to land 157 mg in the beaker (8.7 mg/rev apparent at the fine
tilt); the re-run's first 200 mg dose needed 9.7 revolutions for 195 mg
(20.2 mg/rev). Same auger, same powder, hours apart — the missing factor was
the powder that never reached the vessel. This retro-explains the morning
session's "~8 vs 26 mg/rev, suspected caking/moisture" flag: mostly alignment.
It is also the concrete argument for the operator's plan to **standardise the
doser↔scale geometry** (#156): outlet alignment is invisible to every sensor on
the rig and can silently scale all delivered-mass readings.

**2. The 200 mg triple in the re-run is feed-limited, not a controller
measurement.** Apparent feed fell monotonically across the run — 20.2 → 15.8 →
10.7 mg/rev over the three 200 mg doses — and the pre-run feed checks at 45°
read only 4.7 then 1.1 mg/rev (a fresh fill measured 26.3 mg/rev on
2026-08-05). The auger is running low (the misaligned run spent ~80 min
dispensing mostly onto the enclosure top) and/or the CMC has caked
(hygroscopic). The dose 4–5 timeouts are the delivery system starving, so the
200 mg errors are a lower bound on controller capability. **A refill + re-run
of the 200 mg triple is the natural completion step.**

**3. Actuation-correlated ±15 mg balance swings, at-rest quiet.** Pre-run the
balance sat at 0.078 mg jitter with 0 shocks, yet individual feed-check
revolutions read −15 to +20 mg bidirectionally. Mass cannot leave the pan, so
these are artifacts: candidates are charged CMC dust scattered around the
enclosure/hole by the misaligned run (the same triboelectric signature the
2026-09-04 xanthan-gum run showed intra-dose) and/or intermittent grain
bridging at the hole-edge ↔ beaker-rim gap. The same bidirectional swings are
visible inside the re-run's dose cycles (fine cycles reading −15 to +19 mg).
The bracketed dose reads still converged 4/6 doses, but per-cycle feedback was
noisy; a cleanup of the spilled dust before the next powder would be cheap
insurance.

**4. Drift** was −11.4 mg/min in the pre-run survey (elevated vs −2.6 mg/min
that morning; #157 tracks this). Documented as a limitation per the operator's
standing instruction; the 50 mg doses (115–240 s) sit mostly below the
timescale where it dominates.

## Environment / provenance

- Pre-run: balance re-zeroed (1.378 g of stray CMC sat in the beaker from the
  misaligned run); survey jitter 0.078 mg, 69 % stable frames, 0 shocks,
  drift −11.4 mg/min.
- Both runs uploaded to `powder_doser.battery_runs`; run 1 carries a dated
  amendment with the operator's #156 evidence, run 2 carries the QC caveats
  above.
- Figure: `carboxymethyl-cellulose_block_h.png` (Block H doses beside the
  2026-08-05 Block G 1 g doses).
