# ngspice power-integrity simulation of the six Quilter-routed candidates

_Hands-on engineering note (not an Edison output). Answers @sgbaird's prompt on
PR [#76](https://github.com/vertical-cloud-lab/powder-doser/pull/76#issuecomment-4756046192):
"run with **ngspice** and any other recommended tools, as described either in
this PR or one of the other PRs", extending the `pcbnew` DRC/connectivity
evaluation in note [`22`](22-quilter-routed-candidate-evaluation.md) and
[`analyze_quilter_candidates.py`](starter_board/quilter_candidates/analyze_quilter_candidates.py)._

## Why a *power* simulation (and not a signal SPICE run)

Note `22` said plainly that "electrical simulation in the SPICE sense is not
meaningful here" for a **small-signal / analog** reading of the board — and that
is still true: these candidates are a digital control + motor-driver **carrier**
(RP2040 + pre-built buck / DRV8871 / DRV2605L / Tic / RS-232 modules), so there
is no op-amp / filter / analog signal chain whose transfer function SPICE would
solve. The electrically meaningful SPICE problem on a board like this is **power
delivery**, and note `22` itself flagged the concrete risk: Quilter routed
**every** net — including the +12 V input and the solenoid/stepper motor
rails — at **~6 mil (0.16 mm)**, ignoring the KiCad `Power` net-class width, so
the motor rails are thin. This note turns that qualitative warning into numbers
with ngspice.

The recommended tools across this PR / the notes are **ngspice** (here),
**KiCad ERC/DRC** (note [`14`](14-pcb-design-recommendations-for-powder-doser.md)
step 5 / note `22`: `pcbnew` DRC is done; ERC needs a *schematic*, which
Quilter's routed candidates do not contain — the generator schematic is already
ERC-clean via `kicad-cli sch export netlist`, see note `21`), and `kicad-cli`
renders (note `22`). So ngspice is the missing piece, applied below.

## Method (`simulate_power_ngspice.py`)

All numbers are reproducible with
[`quilter_candidates/simulate_power_ngspice.py`](starter_board/quilter_candidates/simulate_power_ngspice.py)
(`analysis_power_ngspice.json` is the captured run). For each candidate it:

1. **Extracts the real routed copper** of the +12 V and +5 V nets. Because
   Quilter exports ~½ its copper with `(net 0)` (the export quirk from note
   `22`), a per-net *label* filter misses the physical trace, so the script
   instead clusters **every** routed `Segment`'s endpoints into electrical
   nodes (a via or a through-hole pad shorts the layers, so clustering in X/Y
   merges them) and recovers each power net as the **connected component that
   contains its supply pad** (barrel jack `J1` for +12 V, buck `U1` output for
   +5 V). DRC is clean, so the components are net-isolated — the script
   **asserts** no foreign named net shares a component, and indeed
   `foreign_nets_on_copper` is empty for all six (an independent confirmation of
   the "no shorts" DRC result).
2. **Converts each segment to a resistor** `R = rho * L / (W * t)`
   (`rho_Cu = 1.724e-8` ohm*m, `t = 35 um` = 1 oz finished copper).
3. **Emits a SPICE deck** — a 12 V (or 5 V) source at the supply pad and a
   current sink at each load pad (representative worst-case currents below) —
   and **solves the resistor mesh with ngspice** (`.op`), reading back the
   node voltages → the IR drop from supply pad to every load pad.
4. Runs a **transient decoupling check** (`.tran`): a lumped 12 V → feed
   resistance → bulk-cap (`C_BULK = 100 uF`, `ESR = 0.5 ohm`, the `C3`
   electrolytic) → solenoid PWM pulse (`0.65 A`, 1 kHz), reporting the rail
   droop.
5. Reports the **IPC-2221 external-layer temperature rise** of the 6 mil power
   trace at the load current.

Representative load currents (`LOADS` in the script; bracketing figures, not
datasheet-exact): +12 V — DRV8871/solenoid `U4` 0.65 A (Adafruit 412 /
TAU0730TM ~12 V/18 Ω), Tic/stepper `U5` 1.0 A (current-limited coil rail),
buck input `U1` 0.30 A; +5 V — servo header `M3` 0.75 A (near-stall), Pico `U2`
0.15 A, RS-232 module `J2` 0.05 A.

> **Modelling caveats.** This is a DC/low-frequency *power* model: layers are
> merged in X/Y (via barrel resistance ≈ 1 mΩ ≪ trace, neglected), copper is at
> 20 °C (resistance rises ~0.4 %/°C when warm), and the load currents are fixed
> worst-case sinks rather than the real switching profiles. It is meant to rank
> the candidates' power routing and size the trace-width fix, not to certify a
> final board.

## Results

ngspice solved every candidate's +12 V and +5 V resistor mesh (all loads
reached, no floating nodes, no foreign-net shorts). Worst-case IR drop = the
largest supply-pad→load-pad voltage on the routed copper:

| candidate | +12 V worst IR drop | +5 V worst IR drop | solenoid-rail droop (`.tran`) | min rail V |
| --- | --- | --- | --- | --- |
| 1 | 436 mV (`U5` stepper) | 69 mV | 146 mV | 11.85 V |
| 2 | **524 mV** (`U4` solenoid) | 180 mV | **517 mV** | 11.48 V |
| 3 | 254 mV (`U5`) | 196 mV | 192 mV | 11.81 V |
| **4** | 357 mV (`U4`) | 117 mV | 355 mV | 11.64 V |
| **5** | **231 mV** (`U5`) | **43 mV** | **98 mV** | **11.90 V** |
| 6 | 492 mV (`U4`) | 179 mV | 487 mV | 11.51 V |

(The worst +5 V node is consistently `J2`, the RS-232 module in the far corner —
its 0.05 A over a long thin trace, a geometry effect, not a current effect.)

**Temperature rise (IPC-2221, identical across candidates because all power
copper is 6 mil / 1 oz):** **≈ 28 °C** at the 1.0 A stepper rail and **≈ 11 °C**
at the 0.65 A solenoid rail. This is the headline electrical finding and it is
**design-wide, not per-candidate**: a 28 °C rise on a 6 mil trace is the
quantified version of note `22`'s ampacity warning.

## What ngspice adds to the note-22 ranking

* **All six remain electrically sound for this low-power board.** The worst IR
  drop is 524 mV on a 12 V rail (4.4 %) and 196 mV on 5 V (3.9 %); the buck,
  DRV8871, and Tic all tolerate this, and the solenoid-rail droop stays above
  11.4 V. No candidate is *disqualified* on power integrity.
* **Power-integrity ranking: Candidate 5 is best** (lowest +12 V **and** +5 V
  drop, smallest solenoid droop, highest min-rail voltage), with Candidate 3
  second. Candidates **2 and 6 are weakest** (~0.5 V solenoid-rail droop).
* **This nuances — but does not overturn — note 22.** Note `22` recommended
  **Candidate 4** on *routing efficiency* (fewest vias + near-shortest copper);
  on *power integrity* Candidate 4 is only middling (357 mV) and Candidate 5
  leads. Because all six pass and the differences are small, the combined read
  is: **Candidate 4 if optimising via count / copper length (manufacturing
  cost/yield), Candidate 5 if optimising power integrity.** Candidate 3 is the
  best all-rounder (2nd-fewest vias, 2nd-best power, 0 silk overlaps).
* **The real action item is unchanged and now quantified:** the 6 mil power
  traces give a ~28 °C rise at 1 A. Before fab, **widen the +12 V / +5 V / motor
  nets to ≥0.5 mm in Quilter's own rules UI** (the KiCad `Power` net class does
  not transfer — see note `22`) and re-route; at 0.5 mm the same currents drop
  to a few °C. This is independent of which candidate is chosen.

## Reproduce

```bash
cd paper/background/starter_board/quilter_candidates
python3 simulate_power_ngspice.py                       # prints the table
python3 simulate_power_ngspice.py --json out.json       # machine-readable
python3 simulate_power_ngspice.py --decks decks/        # dump the ngspice .cir
```

Needs `ngspice` on `PATH` (`sudo apt-get install -y ngspice`) and
`kiutils`; with ngspice absent the script prints the generated decks and the
analytic bounds instead. It is **read-only** — it never modifies the candidate
board files.
