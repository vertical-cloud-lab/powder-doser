# Powder-doser digital twin

A fast, dependency-free (stdlib-only) reduced-order simulator of the doser —
`hopper → auger → tube-lip reservoir → free fall → vial on balance` — for
prototyping dosing control policies (three-phase, rate-PID, MPC) and dry-running
Bayesian-optimization campaigns before touching hardware. Requested in
[PR #124](https://github.com/vertical-cloud-lab/powder-doser/pull/124); the
physics-engine / DEM route for a higher-fidelity twin is covered by separate
Edison queries in `../edison/`.

## Files

| File | What |
|---|---|
| `powder_sim.py` | The twin: `PowderDoserSim`, `Powder`, `Context`, `POWDERS` library |
| `test_powder_sim.py` | 23 sanity checks (`python test_powder_sim.py`) |
| `demo_digital_twin.py` | Runs the firmware's three-phase policy on the twin and renders the demo plots |
| `demo_dose_profiles.png` / `demo_behaviors.png` | Rendered demo output |

## What it models

State compartments: hopper mass, a **lip reservoir** of loose powder at the tube
exit, in-flight (falling) mass, and vial mass. All units match the firmware
(`main_three_phase.py`): grams, seconds, plate degrees (0 = horizontal,
45 = rig "vertical"), auger RPM/degrees.

* **Auger conveying** — mass per revolution (the loss-in-weight "feed factor")
  scales with hopper fill (starved screw < ~30 % fill, with pulsating discharge),
  tilt, cohesion, and tap-densification; multiplicative flow noise on top.
* **The lip reservoir is the interaction hub** (bench observations from the
  thread): rotation replenishes it, taps and gravity drain it. A tap right after
  a rotation therefore ejects more than repeated taps, and everything ejects
  more at steeper tilt.
* **Taps** — eject a tilt/cohesion-dependent fraction of the lip in discrete
  clumps (Poisson-quantized for cohesive powders), compact the powder, clear
  hopper arches, and shake the balance.
* **Context variables** — humidity × exposure time drives moisture uptake →
  effective cohesion (temperature mildly offsets it); hopper fill evolves as
  powder is consumed. These are the BO context vector.
* **Cohesive failure modes** — arching/rat-holing that stops the feed until a
  tap (or luck) clears it.
* **Balance** — first-order settling (configurable integration time), 0.1 mg
  quantization, sub-mg noise floor at rest, ~8 mg noise while actuators shake
  the frame, A&D-style stable flag, and a free-fall delay so in-flight powder
  is invisible to the controller.
* **Outputs** — `read_balance()` (what the controller sees),
  `dose_rate_g_per_s` (true instantaneous rate, for rate-PID/MPC experiments),
  `telemetry()` (full state for logging/plots).
* **Vibration motor** — modelled (`set_vibration_duty`) even though the current
  firmware omits it, so its value can be explored in sim first.

## Quick start

```python
from powder_sim import PowderDoserSim, Context, POWDERS

sim = PowderDoserSim(POWDERS["salt"],
                     Context(humidity_pct_rh=45.0, hopper_fill_frac=0.7),
                     seed=1)
sim.set_tilt_deg(45.0)          # plate degrees, same as firmware angle_deg
sim.set_auger_rpm(55.0)         # auger RPM, same as firmware rotation_rpm
while sim.read_balance()[0] < 1.5:
    sim.step(0.25)              # advance wall-clock seconds
sim.set_auger_rpm(0.0)
sim.set_tilt_deg(0.0)
for _ in range(10):
    sim.tap()
    sim.step(0.6)
grams, stable = sim.read_balance()
```

Same-seed runs are bit-identical, so BO/controller experiments are reproducible;
vary the seed to model run-to-run powder stochasticity.

## Calibration status

All coefficients are plausible-order guesses, loosely anchored to the salt
behavior visible in the PR #124 videos (a few hundred mg per auger rev, taps
worth ~1–30 mg depending on tilt). The powder library (`POWDERS`) is a starting
point, not data. Before trusting the twin quantitatively, fit per powder from a
short bench script: feed factor vs fill (weigh N revolutions at several fills),
per-tap yield vs tilt, and lip drainage vs tilt — the same measurements the
Layer-3 feed-factor estimator needs anyway.

## Demo

`python demo_digital_twin.py` reruns a host-side mimic of the three-phase
firmware policy (default parameters) on three powder/context cases and renders
the twin's behavior curves. Note the untuned bulk phase **overshoots on a fast
powder** (balance lag + in-flight mass) — exactly the failure mode the
no-overshoot constraint in the BO formulation must prevent, now reproducible
in software.
