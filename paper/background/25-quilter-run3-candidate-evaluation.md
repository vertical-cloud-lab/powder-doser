# Note 25 — Quilter run-3 candidate evaluation (2026-07-15 boards, 2-servo design)

**Build note (not an Edison output).** Evaluation of the six candidate boards
Quilter.ai returned for the commit-`0683525` `test_module_unplaced` trio — the
first upload carrying the **second dispensing-angle servo** (`M4` on Pico GP2,
net `SERVO_SIG2`; PR #66 dual-servo hinge / PR #100 rev C — 16 footprints /
175 pads / 23 nets, 110 × 110 mm outline), routed with the reviewed settings
from the PR #76 checks (JLCPCB 4-layer *with power plane* JLC04161H-7628,
10 mil / 6 mil rules, per-net power currents, bypass-cap assignments). Files
committed verbatim under
[`starter_board/quilter_candidates_run3/`](starter_board/quilter_candidates_run3/);
reproducible via `analyze_quilter_candidates_run3.py` and
`simulate_power_ngspice_run3.py` there. Supersedes the run-2 boards of note
`24` (routed without M4 — do not fabricate those).

## Second-servo verification (the run's headline question)

**M4 is present and correctly routed on all six candidates.** Checked
explicitly, not inferred from the global ratsnest count:

* every candidate carries the `M4` 3-pin header footprint with its pads on
  exactly `+5V` / `GND` / `SERVO_SIG2`;
* a union-find over the routed `SERVO_SIG2` copper (segments + vias + pads)
  confirms one connected component reaching both the `M4` signal pad and the
  Pico's **GP2** pad (`U2` pad 4) — the pin PR #100 rev C assigns;
* `pcbnew` (KiCad 7.0.11) reports unconnected-ratsnest **0** on all six, so
  the +5 V and GND legs are complete too.

## Full parts audit vs. the electrical-design / scale-integration PRs

Per the request to re-verify nothing else is missing (after the second-servo
miss), each candidate's footprints and pad-to-net assignments were audited two
ways:

1. **Against the upload trio** (`../test_module_unplaced.kicad_pcb`, commit
   `0683525`): same 16 refs, same per-ref pad counts, same per-ref net sets on
   all six candidates — Quilter dropped/renamed nothing.
2. **Against PR #100 rev C** (`hardware/test-module/kicad/generate.py`
   `PLACEMENTS`, fetched from the PR head): the ref set
   `{C1–C3, J1, M1–M4, SOL1, SR1, U1–U6}` and every ref's net set match
   exactly, and all 23 nets are present — including the scale-integration
   nets (`SCALE_TX`/`SCALE_RX` on GP12/GP13, `U6` VCC on `+3V3`) and both
   servo nets (`SERVO_SIG` on GP15, `SERVO_SIG2` on GP2).

Known intentional deviation (from the note-21 physical-footprint audit, not a
miss): the DRV2605L's `EN` pin doesn't exist on the physical Adafruit breakout,
so `HAPT_EN` rides only IN/TRIG — at the net-set level the boards still match
PR #100 exactly.

## What this run fixed (vs. run 2, note 24)

| run-2 finding | run 3 |
| --- | --- |
| `+5V` routed at the 0.254 mm floor (the +5V↔+3V3 current swap) | **+5V now routed at 0.514 mm** alongside +12V and GND — the corrected Power Nets rows took effect |
| no second servo | M4 present + routed (above); the +5 V simulation now loads **two** near-stall servos (2 × 0.75 A + Pico 0.15 A) and every candidate still passes with ≤ 135 mV worst drop |
| C2 stranded 25 mm from the Pico on the recommended candidate | four of six candidates hold every bulk cap ≤ 8.2 mm from its supply pin |

Still present (systemic, same two pre-fab fixes as run 2):

* the **`<no net>` zone on `In2.Cu`** ("Power Layer 2") — the source of **all
  152 clearance + hole_clearance DRC errors on every candidate**; nothing
  electrical depends on it. Fix in KiCad before fab: select the In2 zone →
  assign net `GND` (or `PWR`) → refill, or delete it.
  **Applied for the recommended candidate 2 (2026-07-16):**
  [`fix_candidate2_in2_zone.py`](starter_board/quilter_candidates_run3/fix_candidate2_in2_zone.py)
  reassigns the zone to `GND` and refills it with `pcbnew`, writing the
  fixed board to
  [`candidate_2_fixed/`](starter_board/quilter_candidates_run3/candidate_2_fixed/)
  (the verbatim Quilter output in `candidate_2/` is untouched). Result
  (captured in `candidate_2_fixed/fix_report.json`): clearance +
  hole_clearance errors **152 → 0** (only the pre-existing 16 harmless
  lib-table notices and 4 cosmetic silk overlaps remain), unconnected
  ratsnest stays **0**, and `In2.Cu` becomes a second solid **GND plane**
  (~11,153 mm² fill, matching `In1.Cu`).
* the **drive nets (`STP_A1/A2/B1/B2`, `SOL_A/B`) and `+3V3` stayed at
  0.254 mm** — the added drive-net current rows didn't take effect this run
  either. At a *continuous* 1 A a 0.254 mm stepper-phase trace runs
  ~13 °C IPC-2221 rise (real chopped drive is lower); acceptable for a
  prototype, or widen those nets manually in KiCad / fix the rows on a re-run.

## Electrical / DRC results (all six candidates)

All six are **fully routed** (`pcbnew` unconnected-ratsnest **0**) with **no
trace-to-trace clearance or short-circuit errors** and no foreign net sharing
any power net's copper (independently re-confirmed by the simulation's
connected-component check). 4-layer `F.Cu / In1.Cu (solid GND plane) /
In2.Cu / B.Cu`.

| candidate | copper (mm) | vias | silk overlaps | bottom-side parts | worst +12V drop | worst +5V drop | sol.-rail droop | C1/C2/C3 → supply-pin (mm) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 1315 | 21 | 5 | 0 | 58 mV¹ | 71 mV | 17 mV | 5.3 / 5.6 / 5.2 |
| **2** | **939** | **19** | 4 | 0 | 73 mV | 107 mV | 43 mV | 5.2 / 8.2 / 5.2 |
| 3 | 1407 | 20 | 5 | 0 | 75 mV | 134 mV | 36 mV | 5.3 / **25.8** / 11.5 |
| 4 | 941 | 20 | 1 | **7** ⚠ | 45 mV | 31 mV | 24 mV | 5.2 / 4.4 / 4.8 |
| 5 | 1285 | 24 | **0** | **8** ⚠ | 138 mV | 44 mV | 38 mV | 4.7 / 4.4 / 4.7 |
| 6 | 902 | 23 | 8 | **7** ⚠ | 39 mV | 25 mV | 39 mV | 7.0 / 5.9 / 4.8 |

¹ candidate 1's +12 V distribution *depends on SR1's carrier* — see finding 2.

ngspice model as in notes 23/24 (segment → `R = ρL/(Wt)`, 1 oz copper,
worst-case loads: stepper 1.0 A, solenoid 0.65 A, buck 0.3 A, **servos
2 × 0.75 A**, Pico 0.15 A, DRV2605L 0.25 A, RS-232 module 0.05 A; `.op`
IR-drop + `.tran` solenoid-rail PWM droop against the 100 µF bulk cap). Worst
case anywhere: 138 mV on 12 V (1.1 %); the solenoid rail never leaves
11.957 V. Every candidate passes power integrity with wide margin.

## Findings

1. **Candidates 4, 5 and 6 are disqualified: bottom-side placement.** The
   `BODY_DOWN` placement setting triggered again — candidate 4 puts 7 parts on
   the bottom (incl. the Pico `U2` and both servo headers' driver breakouts),
   candidate 5 puts 8 there (incl. the barrel jack `J1` and buck `U1`),
   candidate 6 puts 7 there (incl. buck and Tic). Every part is a top-access
   THT module (receptacles, USB port, wire terminals), so double-sided
   mounting isn't buildable here. This was flagged before both runs; if a
   re-run is ever done, set the bottom layer's placement to *none*.
2. **Candidate 1 uses the shunt regulator as a jumper — disqualifying.** Its
   +12 V routing reaches the buck (`U1`), the Tic (`U5`) and both bulk caps
   **only through SR1's two duplicate access holes** (the Pololu carrier's
   internal pour): unplug SR1 and the stepper and the whole 5 V system lose
   power, and the full ~2 A supply current flows through the module's copper.
   Detected by the simulation's `module_internal_bridges` check run without
   same-footprint pad bridging; on candidates 2–6 the same check flags SR1
   only for the benign duplicate-hole stub, with **nothing stranded**.
3. **Candidates 2 and 3 are the clean top-side boards; 2 is better routed.**
   Candidate 2 has the shortest copper of the buildable boards (939 mm), the
   fewest vias of all six (19), every bulk cap ≤ 8.2 mm from its supply pin,
   and mid-pack IR drops. Candidate 3 is the weakest: longest copper
   (1407 mm), `C2` stranded 25.8 mm from the Pico's VSYS pin, and the worst
   +5 V drops (121/134 mV at the two servo headers).
4. **The reviewed power-net settings largely landed.** +12V, +5V and GND all
   routed at 0.514 mm (run 2 had +5V at the floor); worst supply-net
   IPC-2221 rise at the simulated currents is ~4.1 °C (stepper rail feed) and
   ~2.1 °C (each servo feed). Only the drive-net rows (`STP_*`, `SOL_*`)
   still didn't transfer (see above).

## Recommendation

**Use candidate 2.** It is the best routed of the three buildable (all
top-side) boards — shortest copper, fewest vias, honest +12 V distribution
that survives SR1 removal, good decoupling proximity, and comfortable margins
everywhere in the ngspice pass (worst rail drop 107 mV at the M4 servo header
= 2.1 % of 5 V). Runner-up: **candidate 1** *only if* its SR1 dependency is
manually rerouted in KiCad (a short 0.514 mm jumper from the J1 spur to the
C1/U1 cluster would fix it — but that's hand-editing Quilter output).
**Avoid 3** (stranded C2, worst +5 V drops); **4/5/6 are not buildable** as
returned (bottom-side THT modules).

Before ordering candidate 2: ~~assign the `In2.Cu` zone to `GND` and refill
(clears all 152 DRC errors and yields a second plane)~~ — **done**, use
[`candidate_2_fixed/test_module_unplaced.kicad_pcb`](starter_board/quilter_candidates_run3/candidate_2_fixed/test_module_unplaced.kicad_pcb)
(see the zone-fix block above). Remaining optional steps: widen the six
drive nets to ≥ 0.5 mm, run *Update PCB from Schematic* against the
generator's `.kicad_sch` (commit `0683525`), and re-run DRC + this folder's
two scripts as a final gate.
