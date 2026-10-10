# Chain test plan

What the rig has to answer before anyone builds a second station: **can a flat #35 chain loop on an HDPE deck move 12 loaded carriages and stop each one at the station repeatably, without shaking powder out?** Each test lists what to measure, how, and the pass mark. Numbers in *italics* are predictions from the model, so a result far from them means the model or the build is wrong.

Run the tests in order; T0–T2 take an afternoon and need no electronics beyond the driver. Log everything with [`test/chain_rig.py`](test/chain_rig.py) (CSV under `test/runs/`), commit the CSVs, and post a summary in [#128](https://github.com/vertical-cloud-lab/powder-doser/issues/128).

| # | Test | Setup | Measure | Pass |
|---|---|---|---|---|
| T0 | **Fit, by hand** | Motor disabled, all 12 carriages, module 1 on carriage 1 | Turn the drive sprocket one full lap by hand. Feeler gauge at the closest approach of neighbouring carriages on both wraps; watch every A-1 link go round both sprockets | No contact, no binding, no carriage lifts off its skids. *Closest approach on the straights: 6.2 mm* |
| T1 | **Tension and lateral sag** | Idler slider clamps loose, jack screw | Push the middle of the back span sideways with 5 N (force gauge); read the deflection with the dial indicator. Tighten the jack screw until it reads 3–4 mm, lock the clamps | Deflection stays within 3–4 mm after T6. Record the jack-screw turns |
| T2 | **Drag** | 11 carriages with a 250 g dummy (salt bag) + module 1 | Driver disabled: pull carriage 1 along the front span with the force gauge at constant slow speed; log the peak and the mean | *About 8 N mean (12 x 0.3 kg x 9.81 x mu 0.22). The NEMA 34 has more than 40x margin, so this is about wear and noise, not torque* |
| T3 | **Index repeatability (the key number)** | Homed (`chain_rig.py home`), dial indicator on a stand at the station touching carriage 1's inner wall along the travel | `chain_rig.py --ask repeat --moves 100`: out one module and back, read the dial after each return. Then `lap` x 5: read every carriage as it arrives | Return-to-station spread (max - min) under 0.5 mm. Per-carriage offsets on a lap are expected (chain pitch tolerance, about 1 mm over 96 pitches); they are fine if they repeat within 0.3 mm lap to lap, because software can store them |
| T4 | **Station push-up and hold-down** | Carriage 1 at the station; force gauge pushing up through the deck window on the mounting plate's free end; dial indicator on the hinge lugs | 0 to 30 N in 5 N steps, with and without the two hold-down blocks | Hinge-lug lift under 0.3 mm at 20 N with the hold-downs. Without them, the lift shows how much of the docking force the chain would otherwise carry (Aug 18 pitch, [12:41]) |
| T5 | **Transit vibration and powder** | ADXL345 on module 1's mounting plate near the outlet; auger filled with salt, outlet uncapped | 100 index moves at each of 25, 50 and 100 mm/s (250 mm/s² accel). Log peak and RMS acceleration per move; weigh the auger before and after each block | No powder loss (under 1 mg on the HR-100A) at the chosen speed. Pick the fastest profile that passes |
| T6 | **Endurance** | All 12 carriages loaded, 50 mm/s | `chain_rig.py endurance --moves 2000` (about 170 laps), unattended but in sight; stop on any driver alarm | Zero driver alarms (missed position), hall index edges stay within 0.3 mm of their first-lap step counts, motor and driver under 60 °C. Before and after: 20-pitch chain length with calipers (*190.50 mm new*; replace the chain at 3% stretch), depth of the wear track in the HDPE at 3 spots |
| T7 | **Wraps on video** | Phone slow-motion at both sprockets | Slow index round both ends | Skids don't catch on the deck holes (sensor holes, countersinks, window edges); A-1 tabs and screws clear the sprocket teeth |

## What the results decide

- **T3 sets the station's capture range.** If the return spread is under 0.5 mm, the kinematic couplings in the Aug 18 pitch need only a small lead-in. If it is several mm, the station needs a mechanical locator (a V-notch on the carriage and a spring plunger) before the couplings engage.
- **T4 says whether the hold-downs are enough** or whether the station needs a clamp that pulls the carriage down onto the deck.
- **T5 picks the transit speed** and puts a number on the "keep one end capped" question from the July 15 meeting.
- **T6 shows whether a flat chain sliding on HDPE lasts.** If the HDPE wears a groove fast, the fix is UHMW tape under the chain path or the oversized-roller C2042 chain discussed on July 31.

## Logged columns

`run, utc, cmd, module, target_steps, pos_steps, move_s, index_edge_steps, alarm, dial_mm`. A step is 1/4000 of a sprocket turn (CL86T DIP set to 4000 pulses/rev), 0.045 mm of chain; one module is 8/19 of a turn, 1684.2 steps. Targets are absolute and rounded, so the fraction never adds up.
