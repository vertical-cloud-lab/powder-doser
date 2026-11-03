# heldout-powders: can the simulations predict powders held out of Sam's 13-powder battery?

## What it models and why it matters here
Sterling asked on #196 whether the simulation results can help predict the behaviour of held-out powders
from the larger dataset Sam collected for his paper, and whether there are meaningful correlations. That dataset
is the #116 battery on `copilot/draft-base-manuscript` @ `963fdba`: 13 powders, each run through the same frozen
protocol. Battery protocol C (30 rpm, six single revolutions at each of 0, 22.5 and 45° tube tilt) ran on the
cone-exit auger, which is the geometry of the #180 DEM twin, so the twin can be run for other powders.

Every model below predicts each powder **without seeing its dosing data** (leave one powder out, LOPO). The
inputs are the #163 literature properties, which were not measured on the lab's lots. The simulation route is:

1. **The DEM path.** One line through contact-parameter space, from smooth grains through the #180 salt twin
   (μ = 0.5, μ<sub>roll</sub> = 0.3) to salt friction plus SJKR cohesion k = 0.75–9 kJ/m³. The grains are salt-sized
   (0.361/0.425/0.489 mm) at every point, so cohesion and friction are what change.
2. **The DEM angle of repose** (ISO 4324 apex method, the reduced test of `../dem-liggghts-aor`) at every path point.
   A powder's literature repose angle then gives its position on the path.
3. **The #180 twin** at protocol C conditions (30 rpm, 45° and 22.5°) at the path points. That gives the DEM's
   mg/rev at the powder's position, multiplied by the powder's particle density over salt's.

So each powder costs no new DEM run: the path is simulated once, and any new powder is placed on it by its
repose angle.

## Code and version
LIGGGHTS-PUBLIC 3.8.0 (Debian/Ubuntu package `liggghts`), serial, STL meshes. The twin's `geometry.py` and
`run_case.py` are copied unchanged from `../dem-liggghts-auger-short` (themselves unchanged from #180's
`sim/dem/`). Analysis: numpy, scipy, matplotlib.

## Setup
RESULTS_SETUP_TBD

## Result
RESULTS_TBD

## Status
STATUS_TBD

## Limitations
LIMITATIONS_TBD

## How to rerun
```
sudo apt-get install -y liggghts
python3 -m venv /tmp/venv && /tmp/venv/bin/pip install numpy scipy matplotlib imageio imageio-ffmpeg pillow
/tmp/venv/bin/python aor_path.py run P0 P1 k750 k1500 k2250 k3000 k4500 k6000 k7500 k9000   # about 1 min each
/tmp/venv/bin/python doser_path.py run d45_P1      # one case per process; 13-30 min each when 4 run at once
/tmp/venv/bin/python aor_path.py summarize && /tmp/venv/bin/python doser_path.py summarize
/tmp/venv/bin/python predict.py                    # LOPO comparison, correlations.md, predictions.json
/tmp/venv/bin/python figures.py                    # figures and the animation (reads the scratch dumps)
```
`python doser_path.py list` prints every case. Scratch output goes to `/tmp/sims-scratch/heldout-powders/`.
