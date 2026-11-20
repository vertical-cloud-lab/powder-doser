# Hopper (auger tube) powder inventory

A running ledger of how much powder is in the rig's auger tube, so any
session (human or Claude) can answer "is there any salt left?" without
guessing. Update the ledger on every refill and every dose. When a run
stalls with "no flow", check the estimated remaining mass here first:
if plenty remains, the powder has **bridged** above the funnel (stir or
tap the tube) — the hopper is *not* empty.

The ledger's running total is an *estimate* accumulated from doses. The
ground truth is to put the tube on a scale and subtract the empty-auger
tare (see below).

## Container geometry (basis for estimates)

The powder container is the rotating auger tube itself
([`cad/auger/archimedes-auger.scad`](../cad/auger/archimedes-auger.scad),
v5/v6 hollow design — no internal helix):

- Inner bore: ID 21 mm (r = 1.05 cm), cross-section **3.46 cm²**
- Straight section: z = 12 mm (top of exit funnel) to z = 244 mm
  (underside of top cap) → 232 mm of bore
- Funnel interior (frustum, 12 mm tall, r 1.5 → 10 mm): ≈ 1.5 cm³
- **Full usable capacity ≈ 82 cm³** (matches the SCAD header's
  "Capacity ≈ 80 cm³ usable")
- Rule of thumb: **1 cm of bore height ≈ 3.5 cm³ ≈ 4.2 g of salt**

## Empty-auger tare mass: **56.716 g**

Reported by @williamulbz, 2026-07-31. Whenever the auger tube is weighed
with powder inside, subtract this to get the powder mass:

```
powder mass (g) = total weighed mass (g) − 56.716 g
```

This is the **authoritative** way to know how much powder is on board —
it beats the geometric estimate below, which carries ±10 % uncertainty
from bulk density and fill height. If a weighed value is ever available,
prefer it and add a ledger row recording both the total and the derived
powder mass.

Handy anchors (using the 1.2 g/cm³ / 4.2 g-per-cm-of-bore rules below):

| Tube state | Powder | Expected total on the scale |
|---|---|---|
| Empty | 0 g | **56.7 g** |
| Full to ~1 cm below brim (as refilled 2026-07-29) | ≈ 93 g | ≈ 150 g |
| Refilled 2026-07-31 | ≈ 53.3 g | **110 g (weighed)** |
| **Weighed 2026-07-31 after refill** | **≈ 53.3 g** | **110 g (measured)** |
| Full capacity (≈ 82 cm³) | ≈ 98 g | ≈ 155 g |

This is not hypothetical: the first weighing (2026-07-31, 110 g total →
53.3 g salt) came back **32 g below** the running estimate of 85.7 g, so
the ledger was reset from it. Weigh the tube on every refill — a
one-second measurement removes an error the running total cannot detect
on its own.

## Salt bulk-density assumption

Poured (untapped) bulk density of granulated NaCl: **≈ 1.2 g/cm³**
(typical published range 1.1–1.3). The salt currently loaded behaves
coarse/free-flowing (measured feed factor ~0.17 g/rev @ 25° tilt,
2026-07-28), consistent with granulated grade.

## Ledger

| When (UTC) | Event | Est. in tube after |
|---|---|---|
| 2026-07-29 ~23:00 | Refilled with salt to ~1 cm below the brim (@swcharles). Fill ≈ 22–23 cm of bore + funnel ≈ **78 cm³** → **≈ 93 g** (range 85–105 g given density/fill-level uncertainty) | ≈ 93 g |
| 2026-07-29 23:20 | PID dose 0.5 g → 0.4925 g + trim to **0.5014 g** dispensed ([logs](../data/pid-dose/2026-07-29_salt/pid_dose_run3_0p5_salt.log)) | ≈ 92.5 g |
| 2026-07-30 17:25 | Three-phase dose 0.5 g, attempt 1: **0.5237 g** dispensed (+23.7 mg overshoot — phase 3's 15° rotation dumped a 25 mg clump; [log](../data/three-phase/2026-07-30_salt/three_phase_0p5_0730.log)) | ≈ 92.0 g |
| 2026-07-30 17:28 | Three-phase dose 0.5 g, attempt 2: **0.4973 g** dispensed (−2.7 mg; bulk+fine hit 0.497 in 19 s, phase 3 added nothing in 98 s; [log](../data/three-phase/2026-07-30_salt/three_phase_0p5_0730_r2.log)) | ≈ 91.5 g |
| 2026-07-30 20:44 | Tap-efficacy check after the electronics repair: 5 bursts × 3 pulses, auger stationary → **0.0034 g** ([log](../data/pid-dose/2026-07-30_salt/tap_efficacy_check.log)) | ≈ 91.5 g |
| 2026-07-30 20:45 | "Normal conditions" experiment, stock PID @ defaults, 1 g × 3 replicates: **1.0631 + 1.0715 + 1.0358 g** dispensed (all overshoot; [rep 1](../data/pid-dose/2026-07-30_salt/pid_normal_run1_salt.log)) | ≈ 88.3 g |
| 2026-07-30 20:53 | Slow-tail diagnostic run (5 rpm cap below 0.2 g to go): **1.0355 g** dispensed ([log](../data/pid-dose/2026-07-30_salt/pid_slowtail_run4_salt.log)) | ≈ 87.3 g |
| 2026-07-31 16:06 | Single-tap characterization: 12 trials (4 tilts × 3 reps), each 1 priming revolution + 10 single taps → **1.575 g** dispensed total ([data](../data/tap-characterization/2026-07-31_salt/)) | ≈ 85.7 g (est.) |
| 2026-07-31 ~16:50 | **Refilled and weighed** by @williamulbz: tube + salt = **110 g** → 110 − 56.716 = **53.3 g of salt**. This *weighing* replaces the running estimate, which had drifted high (85.7 g estimated vs 53.3 g actual — the 2026-07-29 geometric fill estimate of ≈ 93 g was the optimistic end of its 85–105 g band, and the pre-refill contents were correspondingly lower than booked). | **53.3 g (weighed)** |
| 2026-07-31 17:03 | Steep-angle safety probe (plate held 5 s at 25–72°, no auger/taps): **0.0 g** — no free-pour at any tilt ([log](../data/tap-characterization/2026-07-31_salt_angles/steep_angle_safety_probe.log)) | ≈ 53.3 g |
| 2026-07-31 17:05 | Wide-angle single-tap characterization: 24 trials (8 tilts 0–70° × 3 reps), each 1 priming revolution + 10 single taps → **3.634 g** dispensed total ([data](../data/tap-characterization/2026-07-31_salt_angles/)) | ≈ 49.7 g |
| 2026-08-07 (before 19:30) | **Refilled** by @williamulbz; total tube+salt mass estimated **≈ 120 g** — *not weighable*: it exceeds the scale's 102 g capacity, so this is an estimate, not a weighed anchor → 120 − 56.716 ≈ **63.3 g** (±10 g given the eyeball total) | ≈ 63.3 g (est.) |
| 2026-08-07 19:30 | Rapid-dispense stop-response characterization: 10 trials (25–70° tilt × 2 reps), 55 rpm + tap-while-rotating to first 0.5 g reading then all-stop → **6.30 g** dispensed total incl. one 25 mg tilt-move release ([data](../data/stop-response/2026-08-07_salt/)) | ≈ 57.0 g (est.) |
| 2026-08-12 23:16 | **Refilled and weighed** by @williamulbz: tube + salt = **127.98 g** → 127.98 − 56.716 = **71.26 g of salt**. Above the scale's 102 g capacity, so this is a bench-scale weighing, not from the doser's balance. | **71.26 g (weighed)** |
| 2026-08-12 23:16 | Afterflow battery (C6–C8/B4), **interrupted at operator request** after 18 of 55 planned trials (all C6, tilt 40/55/70° × halt 0.3/0.6 g, tap-while-rotating) → **≈ 10.16 g** dispensed total (cum 9.42 g at trial 18 start + ~0.74 g into trial 18 when stopped); [partial log](../data/afterflow/2026-08-12_salt/afterflow_battery_partial_salt.log). Hardware then disconnected by @williamulbz for manual reset. | ≈ 61.1 g (est.) |
| 2026-08-13 00:36 | Afterflow battery **restart (attempt 2)** after the operator reset — no refill (continued from the depleted tube). All **58 trials** (C6/C7/C8/B4/B5) completed cleanly, no brownout → **30.835 g** dispensed total ([log](../data/afterflow/2026-08-12_salt/afterflow_battery_salt.log)). NB: the cup read a standing **63.5 g** pre-tare at session start (anomalous — flagged for a bench check); dispensed tracking is unaffected (tare each trial), and the cap was tightened to 33 g so absolute pan load stayed < ~99 g of the balance's 102 g range. | ≈ 30.3 g (est.) |
| 2026-08-13 18:00 | **Phase-resolved afterflow** battery (42 trials: Test A slug-periodicity 2 scans + Test B afterflow-vs-halt-phase 40 trials, 55/70° tilt) plus setup/smoke moves. No hardware tare used (the A&D `Z` halts Q-replies with a loaded pan — see below); absolute cup mass rose ≈ 2.44 → 9.13 g over Test A+B, and with the earlier failed v1 pass + smoke moves the session removed **≈ 9.1 g** from the tube ([data](../data/afterflow-phase/2026-08-13_salt/)). | ≈ 21 g (est.) |
| 2026-08-17 17:05 | **KF bang-bang stop-accuracy battery** (24 trials, auger-only, targets 0.1–2.0 g, tilt 55°, 55/90 rpm) → **19.29 g** dispensed ([data](../data/kf-bangbang/2026-08-17_salt/)). NB: flow held at ~0.13 g/s all session, ~3× the depleted-tube 0.04 g/s of 2026-08-12, so the tube was very likely **refilled** by the bench team between 08-13 and 08-17 — unlogged and unweighed, so the running total below is not trustworthy. **Please weigh the tube (bench scale) and post the number**; the ledger should be reset from it. | ≈ 2 g (est., almost certainly wrong — refill suspected) |
| 2026-08-17 19:50 | **Low-rpm stop battery + quantum-vs-tilt** (PR #124 tests): 20 stop trials (5/10/15/25 rpm × 5 reps, 55°) + 108 × 20° increments at 10 rpm (15/35/55°) + 8 stop trials at 25° + 7 matched-revolution flow checks → **13.364 g** dispensed ([data](../data/lowrpm-quantum/2026-08-17_salt/)). Flow at 55° was only ~0.026 g/s vs ~0.13 g/s in the morning KF session, and the first flow check delivered ~0 g/rev (priming needed) — consistent with a substantially depleted tube. **Still needs a bench weighing to reset the ledger.** | ≈ 0 g?? (est. meaningless — weigh the tube) |
| 2026-11-18 06:45 | 30 × 1 g stepped-tilt trials for @XZaitzeff ([PR #131](https://github.com/vertical-cloud-lab/powder-doser/pull/131)): **stopped after 4 stalled trials**. The tube had been refilled to the brim since 08-17 (unlogged, not weighed), and the full tube plugs at the requested 60–40° bulk angles. A 0° priming spin, angle probes and the partial trials put **≈ 1.6 g** into the beaker ([data](../data/three-phase/2026-11-18_salt_tilt-schedule/)). | unknown (refilled since 08-17; weigh the tube) |
| 2026-11-18 16:06 | Rerun of the 30 × 1 g trials with the bulk at 50 → 30° for @XZaitzeff ([PR #131](https://github.com/vertical-cloud-lab/powder-doser/pull/131)): **stopped after 4 stalled trials**, 0.0 mg each. A 40 s priming spin at 0° gave 1.6 mg (0.542 g at 06:48) and a probe gave 9.2 mg from 2.75 revs at 30° (90 mg at 06:53). The auger turns on camera, so almost no salt reaches the outlet: the tube may be nearly empty, or the salt is stuck above the auger. **≈ 0.011 g** into the beaker ([data](../data/three-phase/2026-11-18_salt_tilt-schedule-50-30deg/)). | unknown, possibly near empty (check and weigh the tube) |
| 2026-11-19 19:47 | **New auger tube** installed by the bench team (fill not weighed; the new tube's empty mass is not known, so the 56.716 g tare above may not apply). Rerun of the 30 × 1 g trials with the bulk at 60 → 40° for @XZaitzeff ([PR #131](https://github.com/vertical-cloud-lab/powder-doser/pull/131)): **stopped after 4 stalled trials**. One 166 mg slug at 60°, then 1–15 mg per 2.75 revs at 30–60° in a flow probe (65 mg in all, against 515 mg from the old tube on 11-18) and 0.147 g from a 0° priming spin. **≈ 0.443 g** into the beaker ([data](../data/three-phase/2026-11-19_salt_tilt-schedule-new-auger/)). | unknown (new tube; please weigh it, with its empty mass) |
| 2026-11-19 20:41 | Rerun of the 30 × 1 g trials on the new tube **with taps during the bulk** (one 60 ms tap per 300 ms, the summer rate), bulk at 60 → 40°, for @XZaitzeff ([PR #131](https://github.com/vertical-cloud-lab/powder-doser/pull/131)). Launch 1 (bulk taps): 0.755 and 0.759 g, both stalled in the tap-free fine stage. Launch 2 (fine-stage taps too): 0.848 g (dose timeout), 0.289 g, 0.000 g, then stopped. A tapped priming check gave 8.3 mg from 27.5 revs at 0° (147 mg from 22.5 revs at 19:52 without taps). Flow per revolution fell from ≈ 11 mg to ≈ 0 as ≈ 3.1 g came out of this tube, so it may hold little more salt that can reach the outlet. **≈ 2.662 g** into the beaker (balance 0.4429 → 3.1051 g; ≈ 3.10 g from the new tube in all) ([data](../data/three-phase/2026-11-19_salt_tilt-schedule-bulk-taps/)). | unknown (new tube; please weigh it, with its empty mass) |
| 2026-11-19 21:43 | **Old tube back on** (put back by @XZaitzeff; not weighed, and whether it was refilled since 11-18 isn't logged). Rerun of the 30 × 1 g trials with taps during the bulk and the **bulk at 80 rpm** (script 2026-11-19d), for @XZaitzeff ([PR #131](https://github.com/vertical-cloud-lab/powder-doser/pull/131)). Trials 1–24 each dosed 1 g (3 within ±1 mg, the rest 1.5–58.3 mg over), then the tube stopped feeding: trial 25 stalled at 0.781 g and trials 26–27 got nothing. The bench camera shows the lower tube paler at the end, so it most likely ran dry. **25.159 g** into the beaker (balance 3.1784 → 28.3375 g; the beaker now holds ≈ 28.3 g) ([data](../data/three-phase/2026-11-19_salt_tilt-schedule-old-auger-80rpm/)). | likely empty (please weigh: the old tube's empty mass is 56.716 g) |
| 2026-11-19 22:43 | **AlSi10Mg in the tube** (loaded by the bench team after the 22:04 salt run; which tube, and how much, wasn't logged). 30 × 2 g trials on the salt protocol (script 2026-11-19e) for @XZaitzeff ([PR #131](https://github.com/vertical-cloud-lab/powder-doser/pull/131)): trial 1 primed the tube, trials 2–17 each dosed 2 g (9 within ±1 mg, the rest 2.3–41.3 mg over), trial 18 stalled at 1.353 g and trials 19–20 got nothing; the run stopped itself at 23:11. The bench camera shows the lower tube paler at the end, so it most likely ran dry. **33.495 g** of AlSi10Mg into the beaker (balance 0.0000 → 33.4948 g; the beaker was emptied and the balance re-zeroed after the salt run) ([data](../data/three-phase/2026-11-19_alsi10mg_tilt-schedule-2g/)). | likely empty (please weigh the tube before refilling) |
| 2026-11-20 02:08 | **AlSi10Mg refilled** by @XZaitzeff (amount not posted; the beaker was not emptied, so the balance still read 33.495 g). Trials 21–26 of the 30 × 2 g run (script 2026-11-20a, [PR #131](https://github.com/vertical-cloud-lab/powder-doser/pull/131)): trial 21 primed the tube, trials 22–25 each dosed 2 g (−0.6, +1.6, −0.1, +11.6 mg), and in trial 26 the balance went over range (OL, display E) at 43.11 g, which stopped the run at 02:13. With this beaker on the pan the 102 g balance tops out at about 43.1 g displayed. **At least 9.6 g** of AlSi10Mg into the beaker (balance 33.495 → 43.115 g when it went over range), and probably up to about 11 g, since the camera shows powder still falling as the display stalled; the beaker now holds about 43–45 g ([data](../data/three-phase/2026-11-19_alsi10mg_tilt-schedule-2g/#trials-2130-after-the-refill-2026-11-20)). | still feeding at 02:13 (refill amount unknown); **the beaker must be emptied before the next run** |
| 2026-11-20 03:05 | **Calcium lactate in the tube** (loaded by @XZaitzeff after the AlSi10Mg run; which tube, and how much, wasn't posted; the beaker had been emptied: the balance read 0.068 g). 2 g trials on the same protocol (script 2026-11-20b, [PR #131](https://github.com/vertical-cloud-lab/powder-doser/pull/131)): a static-tilt pour probe first (auger still, no taps) dropped 11–44 mg on each tilt step up to 60°, 105 mg in all; then trials 1–18 each dosed 2 g (1 within ±1 mg, 17 over by 4.0–115.1 mg, median +46.5 mg) and the launch stopped itself on its cup cap at 03:24 (with this beaker the balance goes over range at about 43 g displayed). **36.973 g** of calcium lactate into the beaker (balance 0.0683 → 37.0411 g, of which 0.104 g from the probe) ([data](../data/three-phase/2026-11-20_calcium-lactate_tilt-schedule-2g/)). | still feeding normally at trial 18 (fill amount unknown); **the beaker must be emptied before the next run** |
| 2026-11-20 17:34 | **Barium chloride in the tube** (loaded by @XZaitzeff in place of the calcium lactate; which tube, and how much, wasn't posted; the beaker had been emptied: the balance read −0.0318 g). 1.5 g trials on the same protocol (script 2026-11-20c, [PR #131](https://github.com/vertical-cloud-lab/powder-doser/pull/131)): the static-tilt pour probe (auger still, no taps) dropped nothing at 30–60°; launch 1 stalled trials 1 and 2 in the bulk and stopped itself; a 0° priming spin (36.7 rev) and the 2.75-rev flow probe at 30–60° (22 rev) gave nothing; launch 2 stalled trials 1 and 2 again and stopped. **About 0.003 g** into the beaker in about 113 auger revolutions (balance at 0°: −0.0332 g at 17:34:40, −0.0303 g at 17:41:47), with the tube turning on camera ([data](../data/three-phase/2026-11-20_barium-chloride_tilt-schedule-1p5g/)). | **not feeding at all** (fill amount unknown): check the outlet and the powder at the bench before the next run |
| 2026-11-20 18:04 | **Sodium sulfate in the tube** (its own tube, put on by @XZaitzeff in place of the barium chloride one; how much went in wasn't posted; the balance read 0.0003 g). 1.5 g trials on the same protocol (script 2026-11-20d, [PR #131](https://github.com/vertical-cloud-lab/powder-doser/pull/131)): the static-tilt pour probe (auger still, no taps) dropped nothing at 30–60°; trials 1–23 each dosed in 11–13 s at about 0.4 g/s, all ending in the bulk stage (final error −0.1 to +254.9 mg, median +65.5 mg; 1 within ±1 mg), and the launch stopped itself on its cup cap at 18:15. **36.546 g** of sodium sulfate into the beaker (balance 0.0008 → 36.5464 g) in 134.7 auger revolutions ([data](../data/three-phase/2026-11-20_sodium-sulfate_tilt-schedule-1p5g/)). | still feeding at full rate at trial 23 (fill amount unknown); **the beaker must be emptied before the next run** |
| 2026-11-20 18:59 | **Xanthan gum in the tube** (its own tube, put on by @XZaitzeff in place of the sodium sulfate one; how much went in wasn't posted; the beaker had been emptied: the balance read 0.0223 g). 2 g trials on the same protocol (script 2026-11-20e, [PR #131](https://github.com/vertical-cloud-lab/powder-doser/pull/131)): the static-tilt pour probe (auger still, no taps) dropped 88 mg on the tilt steps up to 60°; trials 1–18 each dosed 2 g with no priming (3 within ±1 mg, 9 within ±5 mg, median +5.0 mg, range −0.3 to +62.9 mg; 10 reached the tap stage, 8 ended in the fine stage), and the launch stopped itself on its cup cap at 19:20. **36.401 g** of xanthan gum into the beaker (balance 0.0223 → 36.4238 g, of which 0.088 g from the probe) in 458 auger revolutions ([data](../data/three-phase/2026-11-20_xanthan-gum_tilt-schedule-2g/)). | still feeding at full rate at trial 18 (fill amount unknown); **the beaker must be emptied before the next run** |

At salt's measured ~0.17 g/rev (25° tilt), ~93 g is roughly **90×
1 g doses** — the tube will not run dry for a long time. Any "hopper
exhausted" verdict from a controller while this ledger shows tens of
grams remaining means bridging/starvation at the funnel, not true
emptiness (this exact misdiagnosis happened on the 2026-07-29 0.5 g
run: the PID stall logic declared "exhausted" at 0.4925 g with ~93 g
on board — the real cause was near-zero commanded RPM at 15° tilt plus
taps yielding nothing for coarse salt).
