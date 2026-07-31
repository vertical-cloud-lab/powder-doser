# Per-environment calibrations

One JSON file per environment, written by
`python -m characterization.analyze` and read by
`python -m characterization.selfcheck`.

Each file records what a **blank-auger** sweep measured in that
environment: the noise floor σ₀ and the LOD/LOQ it implies, the
settle-delay-vs-σ curve and its knee, any forbidden RPM bands, how often
the balance failed to flag stable, and the full per-condition table.
Crucially it also records the **criterion** used — read delay, stability
window, stability tolerance — because a settle time or a σ without the
criterion that produced it is not interpretable.

These are versioned deliberately. Vibration coupling is a property of
the room, the bench and the mounting, not of the doser, so a calibration
travels with the environment and has to be retaken when the rig moves
(the glovebox is the case that motivated this — see
[issue #139](https://github.com/vertical-cloud-lab/powder-doser/issues/139)).
Committing them means a controller's assumed noise floor is auditable
after the fact rather than remembered.

## Naming

`<environment>.json`, matching the `--environment` label passed to the
sweep: `bench.json`, `glovebox.json`, `fume-hood.json`.

## Files

- `example-mock-demo.json` — a complete example produced by the offline
  simulator (`--mock`), **not** by hardware. It exists so the schema and
  the self-check can be exercised before any real sweep is run; it has a
  structural resonance planted at 15 RPM. Do not treat its numbers as
  characterizing anything physical.

## Using one as a gate

```bash
python -m characterization.selfcheck --calibration calibration/bench.json \
    --rig-port /dev/ttyACM0 --balance-port /dev/ttyUSB0
```

Non-zero exit means the environment no longer reproduces its stored
calibration: do not dispense until a full sweep has been rerun.
