# Hopper (auger tube) powder inventory

A running ledger of how much powder is in the rig's auger tube, so any
session (human or Claude) can answer "is there any salt left?" without
guessing. Update the ledger on every refill and every dose. When a run
stalls with "no flow", check the estimated remaining mass here first:
if plenty remains, the powder has **bridged** above the funnel (stir or
tap the tube) — the hopper is *not* empty.

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

At salt's measured ~0.17 g/rev (25° tilt), ~93 g is roughly **90×
1 g doses** — the tube will not run dry for a long time. Any "hopper
exhausted" verdict from a controller while this ledger shows tens of
grams remaining means bridging/starvation at the funnel, not true
emptiness (this exact misdiagnosis happened on the 2026-07-29 0.5 g
run: the PID stall logic declared "exhausted" at 0.4925 g with ~93 g
on board — the real cause was near-zero commanded RPM at 15° tilt plus
taps yielding nothing for coarse salt).
