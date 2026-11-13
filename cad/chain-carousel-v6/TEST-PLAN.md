# Chain test plan, v6 (v5 with Sam's 2026-11-10 changes)

What v6 has to answer, on top of v5's: **does the longer plate hold the auger in its two clips and let it pull straight off;
does the module rest on its own carriage's latch shelf at the station and come off with the bolt pushed back by hand; do the
lift P16-50s dock the EC on its hooks and do the guides' funnels and seats park it in the same place every time; and does the
third P16 swing the docked EC and module 0-90 deg with the hooks letting go and taking hold again cleanly?** v5's questions
(the balance, drafts, the dose) stand. Numbers in *italics* are predictions from the CAD checks ([`checks/`](checks)); v6's
station has not been simulated.

Run in order. T0-T3 are v2's chain tests, unchanged. Log with [`test/chain_rig.py`](test/chain_rig.py) (CSV under `runs/`;
`--sim` for a dry run) and post a summary in [#128](https://github.com/vertical-cloud-lab/powder-doser/issues/128).

| # | Test | Setup | Measure | Pass |
|---|---|---|---|---|
| T0 | **Fit, by hand** | Drive chain off, all 13 carriages and modules on, the EC parked | Turn the loop one lap by hand; feeler gauge at the corners; watch each latch follower pass over the NEMA 34 and ride the station's cam, and each module settle on its bolt's shelf | No contact or binding; every follower's tip clears the NEMA 34 (*about 7 mm*). *`check_interference.py --sweep`: 0 clashes over one module in 2-link steps* |
| T1-T3 | **Tension, drive torque, index repeatability** | As v2's [TEST-PLAN](../chain-carousel-v2/TEST-PLAN.md) | As v2 | As v2 |
| T4 | **Latch at the back and the rest shelf (v6)** | Carriage 1 at the station, carriage 2 half an index away; force gauge on module 2's cap end; dial indicator under module 1's keeper | The pull that moves a latched module; module 1's drop onto the shelf with its pin out; 100 h at the station with a full auger on the shelf (creep); the bolt pushed back 10 mm by hand | A latched module holds at least 10 N either way; module 1 drops 0.2 mm onto the shelf (*CAD*) and creeps less than 0.2 mm in 100 h; at 10 mm both the pin and the shelf clear the keeper and the module swings off its hinge pins |
| T4a | **Clips and the auger swap** | Carriage 4 at the side hatch | Pull the auger straight off clips 1 and 2 and snap a full one back in; the peak pull; the carriage's movement on its side tabs | Under 1 minute, no tools; the carriage moves under 1.2 mm; the clips don't whiten or crack after 50 swaps |
| T5 | **Tilt clearance, by hand (v6)** | Actuators disconnected; the EC docked by hand on its hooks and the bars | Swing module 1 and the EC 0-90 deg by hand; watch the hooks leave the bars and come back; the gap from the module's plate to the carriage's opening at 90 deg (*1 mm at its front edge*) | Nothing touches through 90 deg. *`--tilt`: 0 clashes from the rise through 90 deg* |
| T6 | **Lift, guides and the funnel seats (v6)** | `chain_rig.py station --tilt 0`, dial indicators on the EC's front face and on one end block; both lift LACs' pots logged | Do the two P16-50s track; does each shoe find its funnel when the frame is pushed 2-3 mm off line by hand before lowering; do the noses seat in the cone and the vee | The parked EC repeats within 0.05 mm over 20 cycles (*three-point seat: cone, vee, and the frame's weight*), including after the 2-3 mm push; the shoes never bind |
| T6a | **Printed dock and its magnets (v6)** | Plate on a bench; the EC's arm with its D44-N52 behind the cone, the vee and ball C; the plate's D42-N52 under each printed feature | Pull-off force against shim (0, 0.25, 0.5 mm); after 500 docks, the domes' height and ball C's dent in the flat | Note the pull: the magnets are about 6 mm apart, so expect less than v5's 3.6 N per seat. The simulations wanted about 8 N per seat (T6c). The domes lose less than 0.05 mm in 500 docks |
| T6b | Dock capture | Dock 20 times with the carriage put 0.5, 1 and 2 mm off its index | Seats, and the module lifts off its shelf, every time | Every time to 0.5 mm off |
| T6c | **Tilt to 90 deg (v6)** | `chain_rig.py station --tilt 30`, then 60 and 90; tilt LAC's pot logged; a protractor on the module | Angle vs the tilt P16's extension (*0 deg 130.7, 30 deg 103.2, 45 deg 87.6, 90 deg 46.1 mm*); does the dock stay seated; do the hooks take the bars back cleanly at 0 | Within 1 deg of `tilt_to_tilt_ext`; the dock never lifts; 50 cycles to 90 deg without a missed hook |
| T6d | **Seek, torque, jam** | As v5's T6c (the pinion turning through the last 3 mm, DRV8825 at 450 mA), jam at 0, 30 and 90 deg | Does the motor stall with the gear in mesh and the dock seated | No tooth jump, no ball lifting. v6's dock is still magnets only |
| T7 | **Outlet door** | Module 1 at the station; a feeler gauge across the exit; a strobe or video | The finger's contact point; the shutter's travel at the dock (*6 mm*, toward the plate); does it shut fully when the EC parks; the force on the push strip | Opens only in the dock's last 6 mm and shuts completely before the EC leaves the plate; push strip force 0.3-0.7 N (*0.27 N shut, 0.63 N open*). Then 100 dock cycles: no binding, no powder in the shutter's grooves |
| T8 | **Dosing onto the balance (v5)** | The HR-202i (or the lab's HR-100A) under the station on the granite paver, levelled and warmed up an hour; the beaker on its riser; the top door slid back | `chain_rig.py dose-to 0.050`, then 0.200 and 1.000 g, 10 each, salt then a metal powder; the stable reading with every door shut | Every dose lands in the beaker (nothing on the pan or the chamber floor); the stable dose within 5 % of target at 50 mg and 2 % at 1 g, with the auger's revs logged beside it; *the stream falls 148 mm from the exit to the rim* |
| T8a | **Balance with the carousel running** | Empty beaker, every door shut, then the top door open | Read the balance at 4 Hz for 10 min while: nothing moves; the chain indexes every 30 s; the station docks, tilts and undocks every 30 s | Drift and noise under 0.3 mg (doors shut) and under 1 mg (top door open). If not, the carousel's vibration reaches the balance through the bench: try the granite paver ([#146](https://github.com/vertical-cloud-lab/powder-doser/issues/146)), then a separate stand |
| T8b | **Fine powder in the open chamber** | A fine powder (silicon -325 mesh, AlSi10Mg); a black card on the chamber floor round the riser | Dose 20 x 50 mg; photograph the card | No grains outside the beaker. If they stray, shorten the fall (a taller riser and a smaller vessel) or add a chimney on the riser |
| T9 | **Transit, laps, endurance** | As v2's T8-T9, with the doors shut | Powder on a tray under the loop after 10 laps; 2000 index moves | Under 1 mg lost over 10 laps (the doors should make this 0); zero alarms; latches, rests and doors still work after 2000 moves |
| T10 | **Enclosure and drafts** | As v3's T10 | As v3 | As v3 |
| T11 | **Auger swap at the side hatch (item 7)** | Carriage 4 at the loading position, side hatch open; a force gauge on the auger; a dial indicator on carriage 4's outer face | Pull the auger straight off its plate: the peak pull; how far the carriage moves (the side tabs' feet); then clip a different auger in | The carriage moves no more than 1.2 mm (*the tabs' feet sit 1 mm outside the tongues*), so the chain carries almost none of the pull; the swap takes under 1 minute with no tools and the hatch shut afterwards. *`--swap`: 0 clashes through the whole pull* |


## What the results decide

- **T6c decides v6's tilt:** a third actuator and a pair of hooks, untried; if the hooks miss the bars on the way back, the
  EC can't be lowered.
- **T4 decides the rest shelf:** the module's whole weight on 3.5 mm of printed shelf while it waits at the station.
- **T6a and T6d decide the printed dock:** printed domes and a printed flat, held only by magnets.
- **T8 and T8a (v5's) still decide whether the balance reads true under the running carousel.**

## Logged columns

As v5, plus `tilt_ext_mm` (the tilt LAC's target).
