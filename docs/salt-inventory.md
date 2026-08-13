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

At salt's measured ~0.17 g/rev (25° tilt), ~93 g is roughly **90×
1 g doses** — the tube will not run dry for a long time. Any "hopper
exhausted" verdict from a controller while this ledger shows tens of
grams remaining means bridging/starvation at the funnel, not true
emptiness (this exact misdiagnosis happened on the 2026-07-29 0.5 g
run: the PID stall logic declared "exhausted" at 0.4925 g with ~93 g
on board — the real cause was near-zero commanded RPM at 15° tilt plus
taps yielding nothing for coarse salt).
