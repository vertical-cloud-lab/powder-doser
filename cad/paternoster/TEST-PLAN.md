# Paternoster carousel: test plan

Each test lists the prediction from the CAD or the MuJoCo models ([sim/README.md](sim/README.md), [sim/AUGER-SIM.md](sim/AUGER-SIM.md)), so a build can confirm or refute it.
[`test/paternoster_rig.py`](test/paternoster_rig.py) runs the motion and logs to `runs/<date>.csv` (`--sim` for a dry run).

| # | Test | How | Pass / prediction |
|---|---|---|---|
| T0 | Fit | Build per ASSEMBLY.md; rotate a full lap by hand with all 12 gondolas loaded | No contact anywhere (`check_interference.py --sweep`: 0 clashes over a full module of travel in half-link steps) |
| T1 | Chain phase and tension | After step 6, measure each SA-1 pair's height difference round the loop; push the longest span with 10 N | Pairs level to 0.5 mm; 3-4 mm deflection |
| T2 | Gondola hang and pivot friction | Swing a loaded gondola 5 deg by hand, film it at 120 fps, read the decay | 2.5 Hz (model 2.54 Hz); stops inside about 1 s; rests within 0.5 deg of vertical (the bronze bushing's friction dead band) |
| T3 | Index repeatability | `repeat --moves 100`, dial indicator on the station gondola's floor | Comparable to v1/v2's T3; the encoder closes the loop, so expect chordal and chain-stretch error only |
| T4 | Swing at the station | `index` with the default profile (trapezoid, ramps = 0.394 s, 1.5 s per index), ADXL343 on the station gondola | Residual swing under 0.5 deg within 0.1 s of the stop (model: 0.07 deg, mu = 0; 0.03 s to settle with mu = 0.1). Repeat with a 1.0 s S-curve to see the difference (model: 9.7 deg) |
| T5 | Lap speed limit | Continuous laps of 20, 12, 10 and 8 s; watch the corners | Swing stays small and no gondola touches its neighbour at 10 s or slower (model: 10.2 mm minimum gap at 10 s; 37 deg swing at 6 s; a gondola flips at 4 s) |
| T6 | Station dock and tilt | `station --tilt 30/45/90` with a dial indicator on the front chain over the hold-down strip | Carriage docks without bumping the plate; chain rise at the station at most 0.5 mm, because the hold-down strip takes up to about 11 N (model). Actuator current stays well under the P16's 50 N |
| T6a | Dock magnet pull | Hang Sam's plate (with its steel tab) under the docked magnet; add weights until it lets go, with shims of 0, 0.15, 0.3, 0.5 and 1.0 mm under the tab | At least 10 N at 0.15 mm (model law 20 N/(1 + g/0.4 mm)^2 gives 10.6 N). Below 6 N at 0.15 mm, use the 5 kg P25/20 (Adafruit 3873) |
| T6b | Seek docking | Dock 20 times from random pinion phases, including a set phase with the teeth tip on tip, with and without the seek | With the seek every dock seats (P16 position reaches the dock value and the plate sits on the rim); without it, about half park 2 mm high (MuJoCo) |
| T6c | Auger torque and jam | Read the Tic's current while dosing salt and a fine powder at 30 and 60 rpm; then jam the auger by hand at 30 deg and 60 deg tilt | Running torque under 0.03 N·m at the auger (estimate). On a jam the motor stalls and the gear stays in mesh: no tooth jump, no plate lift (MuJoCo: the mesh holds to the 0.22 N·m stall at every tilt) |
| T6d | Backlash and runout | Dial indicator on the 44T gear's rim while turning it docked; feeler gauge in the mesh at four positions | Runout under 0.1 mm TIR; backlash 0.1-0.25 mm everywhere (32.25 mm centre distance; the magnet bends the plate up to 0.08 mm, FEA) |
| T7 | Dosing | `dose --tilt 15/30/45 --revs 2` into a tared vial (HX711 calibrated with a 20 g weight) | Dose per revolution highest around 15-30 deg and falling steeply past 60 deg (particle model: trend only, not mg). Nothing outside the funnel at 30 deg |
| T8 | Storage spill | Fill a module, dose at 30 deg with the post-dose sequence (hold 0.5 s, tilt back, reverse 1 auger revolution at rest), then run 50 full laps with the outlet open and a tray under the loop | No powder lost (leakage study: 0 proxy grains after a dose, a tilt-back and an index, and under 1.5-2 g vibration). This is the paternoster's main claim against v2, where each module turns over once per lap |
| T9 | Swap | Time a module change at the loading position; count tools | Two thumb screws, no tools, under a minute |
| T10 | Endurance | 2,000 indexes; inspect bushings, PTFE washers, SA-1 tabs and the chain | No wear marks on the shoulders, no loose nylocks, no tab bending |
