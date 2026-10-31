# dem-liggghts-auger-short: smoke-test rerun of the PR #180 auger twin (dry vs cohesive)

## What it models and why it matters here
The rig's rotating-tube auger: the CAD `threaded-auger-final` geometry with its 12 mm cone and the core tip
inside the Ø3 mm exit, tilted 27.5° and turning at 60 rpm. This is case `rig_t27p5_r60` of the PR #180
LIGGGHTS twin. The run checks two things:
* that the twin can be regenerated and rerun from the #180 branch's scripts;
* how a Bond-number-about-5 SJKR cohesion changes the mass delivered in a partial revolution. Dosing per
  revolution, its pulsing and stalled increments are the dosing fingerprint that the paper relates to powder cohesion.

## Code and version
LIGGGHTS-PUBLIC 3.8.0, Debian/Ubuntu package `liggghts`, run serially (1 core, STL meshes).
`geometry.py` and `run_case.py` are copied unchanged from branch `claude/issue-158-20261010-0534` (`sim/dem/`).

## Setup
* **Geometry, grains, contacts, gravity and feed** are exactly those of `rig_t27p5_r60` (see `auger_short_*.json`
  and the generated decks `in.auger_short_*`):
  * bore 20.9 mm, core 7.96 mm, pitch 10.4 mm, 1.5 flight turns meshed, 12 mm cone to the Ø3 mm exit, core tip
    radius 0.43 mm;
  * about 28.9 k real-size salt grains prefilled (0.361/0.425/0.489 mm), plus a feed region at the top;
  * Hertz–Mindlin, E = 2×10⁵ Pa, ν = 0.3, e = 0.5, μ_pp = 0.5, μ_pw = 0.4, EPSD2 μ_roll = 0.3,
    dt = 2.06×10⁻⁵ s.
* **Changed for this smoke test:** `revs` 1.5 → 0.25, `stop_s` 0.6 → 0 (no afterflow phase), dumps every
  12.5 ms, `mesh_format` "stl" and `np` 1.
* **Schedule:** settle 0.12 s with the exit plugged, then the plug is removed and the auger turns for 0.25 s
  (90°). Grains crossing a counting disk below the exit are counted and deleted (`fix massflow/mesh`).
* **Cohesive variant:** the same, plus SJKR cohesion with k = 6000 J/m³ on all contacts (grain–grain and
  grain–auger). The pull-off Bond number is about 5 at this stiffness; see `../dem-liggghts-aor/README.md`.

## How to rerun
```
sudo apt-get install -y liggghts openmpi-bin
/tmp/venv-liggghts/bin/python run_case.py auger_short_dry.json --workdir /tmp/sims-scratch/dem-liggghts-auger-short/auger_short_dry
/tmp/venv-liggghts/bin/python run_case.py auger_short_coh.json --workdir /tmp/sims-scratch/dem-liggghts-auger-short/auger_short_coh
/tmp/venv-liggghts/bin/python figures.py      # auger_short.png, auger_short.gif/.mp4 (dry), result.json
```
(or `run.sh`, which does all three).

## Runtime
* Dry: 573 s wall clock (467 s CPU), 1 core.
* Cohesive: 482 s active wall clock (370 s CPU), 1 core. It was paused with SIGSTOP for 31 min while the shared
  runner was oversubscribed, so it shows 2352 s elapsed.
* About 29–30 k grains, 0.37 s of physical time (18 k steps).
* The rotating phase costs roughly 30 min per revolution on one core, as #180 reported.

## Result
![auger short](auger_short.png)

| variant | salt delivered in 0.25 rev (90°) after the exit opened | grains | as mg/rev (rough, see Limitations) | grains in the domain at the end |
|---|---|---|---|---|
| non-cohesive | **16.7 mg** | 182 | about 67 | 29 776 |
| cohesive, SJKR 6 kJ/m³ (Bo ≈ 5) | **0.13 mg** | 1 | about 0.5 | 30 015 |

* **The #180 twin regenerates and reruns from that branch's scripts.**
  * The non-cohesive quarter revolution gives 16.7 mg.
  * #180 reported 12 mg for the first quarter revolution of the same case, and 105 mg/rev (116 ± 20 after the
    first quarter) over 1.5 revolutions.
  * The difference is within the pulsed, per-quarter scatter #180 describes (its CV of a 15° nudge was 0.62).
* **With Bo ≈ 5 cohesion the auger stalls.** One grain left the exit in the first quarter revolution, against
  182 dry: a 99 % drop. The cohesive bed does not get through the 1.07 mm annulus (about 2.5 grain diameters)
  between the core tip and the Ø3 mm exit. Where exactly it arches was not inspected.
  * This matches #180's `micro_cohesive` case (SJKR 20 kJ/m³ "shuts everything down"). Here a 3× smaller
    cohesion energy density, Bo ≈ 5 instead of about 180, is already enough.
  * This is consistent with the rig's Si −325 mesh giving 0 mg/rev (#180).

Animation of the dry run (slice |y| < 1 mm through the auger axis, coloured by speed): [auger_short.gif](auger_short.gif), [auger_short.mp4](auger_short.mp4).

## Status
**Ran** (both variants, the full 0.25 revolution planned). It is a short smoke test, not a per-revolution calibration.

## Limitations
* **Short window.** A quarter revolution is not a per-revolution dose. #180 found strong pulsing within each
  revolution, so 0.25 rev values cannot be scaled to mg/rev with any accuracy.
* **One seed, no afterflow phase.**
* **Cohesion value.** k = 6000 J/m³ is illustrative (Bond number about 5 at the softened E), not calibrated
  to salt. Real dry salt is nearly cohesionless, and humid salt would need the capillary model (see `../dem-liggghts-capillary`).
* **Model limits inherited from #180:** spheres with rolling friction, E reduced, 1.5 flight turns meshed,
  and the rig's fill level not modelled.
