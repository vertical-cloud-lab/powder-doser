# Note 24 — Quilter run-2 candidate evaluation (2026-07-14 boards)

**Build note (not an Edison output).** Evaluation of the candidate boards
Quilter.ai returned for the **post-audit** `test_module_unplaced` trio
(110 × 110 mm, vendor-exact footprints, PR #100 scale integration — 15
footprints / 172 pads / 22 nets), routed with the reviewed settings from the
PR #76 checks: JLCPCB 4-layer *with power plane* (JLC04161H-7628), 10 mil /
6 mil rules, per-net power currents, bypass-cap assignments. Files committed
verbatim under
[`starter_board/quilter_candidates_run2/`](starter_board/quilter_candidates_run2/);
reproducible via `analyze_quilter_candidates_run2.py` and
`simulate_power_ngspice_run2.py` there.

**Candidate 4 is missing:** its attachment link in the PR comment was
malformed (`…/powder-doser/files//…`, returns *Not Found*), so five of the six
candidates are evaluated. It can be added to the comparison if re-uploaded.

> **⚠️ Superseded by the 2-servo design (2026-07-15).** @williamulbz's review
> ([PR #76](https://github.com/vertical-cloud-lab/powder-doser/pull/76#issuecomment-4983618810))
> flagged that these candidates predate the move to the **2-servo design**:
> they carry only one servo header. The generator now emits the second
> dispensing-angle servo `M4` (`SERVO_SIG2` on Pico GP2; note `21` top update
> block), so **do not fabricate these candidates** — re-upload the regenerated
> `test_module_unplaced` trio to Quilter (16 footprints / 23 nets) and set the
> `+5V` power-net current to **2000 mA** (two servos) in Quilter's rules UI.
> The evaluation methodology and per-candidate findings below remain valid for
> the boards as routed.

## What the reviewed settings fixed (vs. the run-1 boards of notes 22/23)

| run-1 finding (notes 22/23) | run 2 |
| --- | --- |
| every trace ~6 mil (0.16 mm), incl. power → ~28 °C IPC-2221 rise at the 1 A stepper rail | 10 mil (0.254 mm) global floor; **+12V and GND routed at 0.514 mm** — worst simulated temperature rise on a supply net is now **6.8 °C** (servo rail), and the +12 V rail sits at 1.6 °C |
| ~half the copper exported as `(net 0)` → ~199 solder-mask-sliver warnings | **gone** — every routed segment carries its real net; 0 no-net tracks, 0 mask warnings |
| 76–85 vias, 1069–1470 mm copper | **18–25 vias**, 874–1603 mm copper (the In1 GND plane + wider rules pay off) |
| worst +12 V IR drop 524 mV, solenoid rail droop to 11.48 V | worst +12 V IR drop **178 mV**; solenoid-rail transient droop ≤ 178 mV (rail stays ≥ 11.82 V) |

## Electrical / DRC results (all five candidates)

All five are **fully routed** — `pcbnew` (KiCad 7.0.11) unconnected-ratsnest
**0** — with **no trace-to-trace clearance or short-circuit errors** and no
foreign net sharing any power net's copper (independently re-confirmed by the
simulation's connected-component check).

| candidate | copper (mm) | vias | silk overlaps | bottom-side parts | worst +12V drop | worst +5V drop | sol.-rail droop | C1/C2/C3 → supply-pin distance |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | **1087** | 20 | 2 | 0 | 147 mV | 62 mV | 147 mV | 5.8 / **25.0** / 5.2 mm |
| 2 | 1203 | **19** | **0** | **9** ⚠ | 68 mV | 130 mV | 61 mV | 7.6 / 6.9 / 21.4 mm |
| 3 | 1603 | 20 | 7 | 0 | 178 mV | 109 mV | 170 mV | 17.9 / 18.2 / 36.0 mm |
| 5 | **874** | **18** | **0** | **10** ⚠ | 123 mV¹ | 69 mV | **35 mV** | 7.3 / 6.9 / 5.2 mm |
| **6** | 1363 | 25 | 3 | 0 | **71 mV** | 124 mV | 71 mV | **5.8 / 5.7 / 5.2 mm** |

¹ candidate 5's stepper (+12 V → Tic) drop is *through SR1's carrier* — see
finding 3.

ngspice model as in note 23 (segment → `R = ρL/(Wt)`, 1 oz copper, worst-case
loads: stepper 1.0 A, solenoid 0.65 A, buck 0.3 A, servo 0.75 A, Pico 0.15 A,
DRV2605L 0.25 A, RS-232 0.05 A; `.op` IR-drop + `.tran` solenoid-rail PWM
droop against the 100 µF bulk cap). The run-2 mesh builder additionally
splits segments at T-junctions and clusters nodes layer-aware (vias/THT pads
are the only layer bridges); run 1's endpoint-only mesh mis-reads these
boards.

**Every candidate passes power integrity** with large margin: worst IR drop
178 mV on 12 V (1.5 %), 130 mV on 5 V (2.6 %); the solenoid rail never droops
below 11.82 V.

## Findings

1. **Bottom-side placement disqualifies candidates 2 and 5 (practical, not
   electrical).** The stackup's placement settings allowed `BODY_DOWN`, and
   Quilter used it: candidate 2 puts 9 parts on B.Cu (`C1 C2 C3 M2 M3 SOL1 U3
   U4 U6` — including the RS-232 receptacle), candidate 5 puts 10 there
   (including the **barrel jack** and the buck). Every part on this board is a
   top-access THT module/receptacle; double-sided THT mounting was already
   ruled out (leads protrude into the opposite side, modules need top access).
   This was the flagged pre-run concern, and it materialised — a pity, since
   candidate 5 is otherwise the electrically best board (shortest copper,
   fewest vias, best droop).
2. **The In2.Cu "Power Layer 2" zone exported with `<no net>` (all
   candidates).** Its fill only touches no-net PTH pads (unused Pico/RS-232
   positions, Tic option holes, J1's switch lug) — that's the source of **all
   154 clearance + hole-clearance DRC errors per board**; there are no
   named-net violations. As exported it is dead copper that would tie those
   floating pins together (and to J1's switch lug) if fabricated. **Pre-fab
   fix (2 clicks in KiCad):** select the In2 zone → assign net `GND` → refill
   (giving a second GND plane, as run 1's boards had), or delete the zone.
   Either clears every DRC error; power distribution doesn't rely on it (all
   power is routed on F/B copper).
3. **Quilter used SR1's duplicate access holes as a jumper.** The shunt
   regulator's two VIN (+12 V) holes are duplicates of one node on the Pololu
   carrier. In every candidate Quilter routed them from different directions
   (KiCad-legal: same-net pads of one footprint count as connected), but only
   in **candidate 5** does the Tic's full 1 A stepper supply actually flow
   *through* the module's pour (remove SR1 and the stepper loses power); in
   the others the through-module link only closes a low-current stub. One
   more practicality strike against candidate 5.
4. **+5V and the drive nets came back at the 0.254 mm floor.** +12V/GND were
   widened to 0.514 mm (the 2000 mA rows worked), but +5V (servo, ~0.9 A →
   6.8 °C rise), `STP_A1..B2` (1 A coil limit → ~13 °C at continuous current)
   and `SOL_A/B` stayed at 10 mil — consistent with the +5V ↔ +3V3 current
   swap and the added drive-net rows not (fully) landing before the run.
   Acceptable for a prototype (stepper drive is chopped, so RMS is lower;
   solenoid is intermittent), but worth either re-running with the corrected
   rows or manually widening those nets in KiCad before fab.
5. **Placement quality separates the top-side candidates.** Candidate 6 is
   the only board that honours the bypass-cap intent — all three bulk caps
   land ≤ 5.8 mm from their assigned supply pins (C1→buck VIN, C2→Pico VSYS,
   C3→Tic VIN). Candidate 1 strands C2 25 mm from the Pico; candidate 3
   scatters all three (18–36 mm), crams every part into the right half of the
   board, and pays for it with the longest copper (1603 mm) and 7 silk
   overlaps.

## Recommendation

**Use candidate 6.** It is the best board among the three viable (all-top-side)
candidates: best +12 V IR drop (71 mV) and solenoid-rail droop (71 mV) of the
three, and the only candidate with all three bulk caps tight against their
supply pins — at the cost of ~276 mm more copper and 5 more vias than
candidate 1, which is noise at these currents.

- **Runner-up: candidate 1** (shortest viable copper, 20 vias) if minimum
  copper/via count is preferred — accepting C2 sitting 25 mm from the Pico.
- **Avoid candidate 3** (worst copper, worst IR drops, worst cap placement,
  7 silk overlaps).
- **Candidates 2 and 5 only if double-sided THT assembly were acceptable** —
  it isn't for this board (finding 1), which is unfortunate since 5 is the
  electrically strongest layout. If a re-run is possible, disabling
  bottom-side placement would likely let Quilter reproduce candidate-5-like
  quality on the top side.

**Before fab (any candidate):** apply finding 2 (In2 zone → GND, refill),
optionally widen +5V/`STP_*`/`SOL_*` per finding 4, and run *Update PCB from
Schematic* against the generator's `.kicad_sch` to restore the schematic
link, then a final DRC.

## Cross-references

- Note [`22`](22-quilter-routed-candidate-evaluation.md) — run-1 evaluation
  (method baseline; via/copper metrics).
- Note [`23`](23-ngspice-power-integrity-simulation.md) — run-1 ngspice model
  and load-current provenance.
- Note [`21`](21-starter-board-for-quilter-deeppcb.md) — the generator, the
  post-audit footprints, and the settings checklist this run used.
