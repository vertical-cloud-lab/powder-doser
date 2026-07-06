# Scale-integration report — A&D HR-100A closed-loop dosing (issue #99)

This is the findings / design-iteration report requested in
[issue #99](https://github.com/vertical-cloud-lab/powder-doser/issues/99):
the bench rig from PR #61 now dispenses a user-entered mass of powder
under closed-loop feedback from an A&D HR-100A analytical balance
(102 g × 0.1 mg) — auger (stepper) for the coarse fill, tap solenoid
for the fine trim.

## 1. What was reviewed first

* **PR #61** wiring + firmware: single Pico W (GP0..GP15 only), Tic
  T500 stepper on UART1 (GP4/GP5), DRV8871 solenoid (GP10/GP11),
  DRV2605L on I2C0 (GP0/GP1), servo (GP15), DRV2605L EN (GP14).
  Free resources: **UART0 and GP12/GP13** — exactly one full hardware
  UART left, which the scale takes.
* **Scale interfacing prior art**: the AC training-lab AutoTrickler v4
  work ([ac-dev-lab#113](https://github.com/AccelerationConsortium/ac-dev-lab/issues/113),
  [picow/autotrickler-scale](https://github.com/AccelerationConsortium/ac-dev-lab/tree/e85dd45e19480068f9e8323dad1a6294dabe8075/src/ac_training_lab/picow/autotrickler-scale))
  polls an A&D balance with `Q\r\n` over a UART and strips the
  `ST,`/`US,` prefixes.  The HR-A series manual (§15/§17) documents the
  same A&D standard format and the RS-232C electrical interface.

## 2. Implementation options considered

| option | verdict | why |
|---|---|---|
| Scale TXD/RXD direct to Pico GPIO | **rejected** | RS-232 swings ±5..9 V; RP2040 absolute max is −0.3..+3.6 V. ngspice (sim 1) shows the pad dragged to −0.98 / +4.2 V with ~20 mA through the clamp diodes — slow-death/latch-up territory. |
| Resistor divider + clamp diodes | **rejected** | Handles RX only (no TX to the scale: `Q`-polling and re-zero need TX), fails the negative excursions, and the thresholds end up marginal at 2400 baud over 2 m of cable. Not worth saving $5. |
| **MAX3232 transceiver breakout on UART0 (GP12/GP13), powered from 3V3** | **accepted** | Bidirectional, datasheet-supported at 3.3 V (charge pump makes the ±RS-232 rails), one part, zero changes to the existing channels. |
| USB host (Pico) to the scale's USB option | rejected | RP2040 USB host + CDC for a niche adapter is far more software risk than a UART, and the team's scale has the RS-232C option installed. |

The chosen design adds exactly two parts (U6 MAX3232 breakout, J2
Molex 43645 receptacle) and two Pico pins; every PR #61 net is
untouched.  The breadboard stays half-size — flagged previously as a
concern — because U6 is a 10-pin breakout and J2 is a pigtail.

> **Update (maintainer request):** the bench now standardises on the
> off-the-shelf **Waveshare Pico-2CH-RS232 module** (U6) in place of the
> discrete MAX3232 + Molex receptacle.  Its **SP3232EEN** is the same
> RS-232 ↔ logic transceiver class analysed below, so the ngspice
> findings carry over unchanged.  Two practical differences:
> 1. **Power it from `+3V3`, not VSYS/5 V.**  The module's `RXD` (and the
>    rest of the TTL side) follows `VCC`; 3.3 V keeps `RXD` inside the
>    RP2040's 3.6 V max while the charge pump still makes the ±RS-232 rails.
> 2. **The TTL header is labelled from the Pico's point of view**, so it
>    wires *straight across* with no crossover: `GP12 → U6 TXD`,
>    `GP13 ← U6 RXD`.  The module's native channel pins (`TXD0/RXD0` →
>    GP0/GP1, `TXD1/RXD1` → GP4/GP5) both collide with rig peripherals, so
>    mount it on its own breadboard and jumper the chosen channel out to
>    GP12/GP13.  The remaining crossover is in the DB9 cable to the scale.
>
> `config.py`, `hardware/test-module/README.md`, the KiCad schematic
> (`U6 = Waveshare_2CH_RS232`), and the `tests/` diagnostics were updated
> accordingly; the `SCALE_232_TX`/`SCALE_232_RX` nets and the J2 Molex are
> gone (now internal to the module).

## 3. Electrical analysis (ngspice)

Following the PySpice/ngspice smoke-test approach recommended in
`paper/background/14-recommendations-electrical.md`, the interface is
checked by `analysis/rs232_analysis.py`; full numbers in
`analysis/rs232_analysis_results.md`.  Summary (all 9 checks pass):

* **Sim 1 (rejected direct connection)**: GPIO node −0.98 V / +4.20 V
  (outside −0.3..+3.6 V abs max), ~20 mA peak fault current through the
  pad clamps → confirms the transceiver is mandatory, not optional.
* **Sim 2 (MAX3232 receive)**: Pico-side logic is a clean 0 / 3.32 V;
  the balance's driver sources only ~1.4 mA into the 5 kΩ receiver.
* **Sim 3 (MAX3232 transmit)**: ±5.09 V at the scale under a 5 kΩ +
  200 pF (2 m cable) load — above the ±5 V RS-232 minimum — and the
  ±3 V undefined band is crossed in ~0.08 µs, ample for 2400–9600 baud.

Power budget: the MAX3232 draws ~1 mA quiescent from `+3V3` (Pico's
on-board regulator, ~300 mA capable, currently feeding only the
DRV2605L logic) — no rail changes needed.

## 4. Control strategy and software iterations

The dose loop lives in `firmware/dosing.py` (hardware-agnostic), the
A&D protocol in `firmware/scale.py`, both exercised by the *same code*
on the Pico and in the CPython simulation (`firmware/sim/`), which
models auger lag (in-flight powder), tap transfer with ±50 % jitter,
scale settling (US→ST), and real A&D ASCII framing.

| iteration | problem found (by simulation) | fix | verification |
|---|---|---|---|
| 1 | Initial two-phase loop (fixed 360° coarse steps to 90 %, then taps) worked only for the nominal case. | — baseline | 13/14 unit tests passing |
| 2 | **Overshoot on small doses** (0.25 g): the 45° minimum coarse step outran the remaining headroom. | Coarse step hard-capped so no single step can cross the target; switch to fine phase early when the floor would overshoot. | `test_dose_various_targets` 0.25 g case green |
| 3 | **Fine-phase stall** (0.05 g): taps only deliver powder already at the tube lip; once empty, the loop tapped to its budget and timed out. | Stall detection: ≥3 bursts gaining <0.2 mg → auger nudge to re-feed the lip. | 0.05 g case progressed, exposed iteration 4 |
| 4 | **Nudge overshoot**: the fixed 15° nudge delivered ~21 mg when 5 mg remained. | Nudge sized from remaining mass (≤½ of what's missing), floor of one full motor step. | all 14 unit tests green |
| 5 | **Robustness sweep failures** (72-case sweep over 0.2–1.5 g/rev powders, 10–40 % in-flight fraction, 0.05–5 g targets): (a) wrong `DOSE_GRAMS_PER_REV` config caused coarse overshoot when powder ran denser than configured; (b) %-based headroom made 5 g doses burn the entire 200-tap budget. | (a) throughput is now **learned online** from the scale after every increment (config is just the first guess, derated 3× for the first probe); (b) coarse headroom capped at `DOSE_COARSE_HEADROOM_G` (50 mg) absolute. | 72/72 sweep cases converge to ±5 mg; worst case 169 s (simulated wall-clock) |

Final state: **14/14 unit tests, 72/72 robustness sweep** (run with
`python3 sim/test_dosing_sim.py` from `firmware/`).

Failure handling on the rig: dead scale → `scale-error` result (rig
stays alive); empty hopper / jam → `no-flow` abort; tap/timeout budgets
bound every dose; `!` still e-stops everything.

## 5. Schematic verification

* `kicad/generate.py` regenerates the schematic; the new
  `test_module_review.png` render multiplies stroke widths ×4 for
  visual review.  A first-pass vision review caught J2's value text
  colliding with its TXD pin label (fixed by re-baselining the symbol's
  pin grid).
* The exported KiCad netlist was checked programmatically:
  `SCALE_TX = U2.16(GP12) ↔ U6.3(T1IN)`,
  `SCALE_RX = U2.17(GP13) ↔ U6.4(R1OUT)`,
  `SCALE_232_TX = U6.5(T1OUT) ↔ J2.2(RXD)`,
  `SCALE_232_RX = U6.6(R1IN) ↔ J2.1(TXD)`, with U6 on `+3V3`/`GND` and
  J2.3 on `GND` — i.e. both cross-overs (logic and RS-232) are right.

## 6. Bench bring-up fixes (PR #100 thread)

Bugs found only once real hardware entered the loop, in the order the
bench hit them:

| # | bench symptom | root cause | fix |
|---|---|---|---|
| 1 | `AttributeError: 'module' object has no attribute 'SCALE_UART_ID'` at boot | Stale pre-RS-232 `config.py` on the Pico's flash (MicroPico ▶ Run streams only `main.py`). | `Rig._bring_up_scale()` degrades gracefully with a re-upload hint; scale/dosing disabled instead of crashing the REPL (`eab86f2`). |
| 2 | `AttributeError: 'function' object has no attribute '_poll'` on the first REPL poll | CPython function-attribute caching idiom; MicroPython function objects reject attribute assignment. | Poll object moved to a module-level global; CPython regression test pins `__dict__` empty (`6fa6ae1`). |
| 3 | `test_scale_contact.py` (and `w`/`g`) appear to **run forever** on a silent link | The scale UART was opened **blocking** (`timeout=1000 ms`) while every driver wait loop counts time via its own 20–50 ms sleeps — each silent `readline()` stalled ~1 s but the counter advanced 20 ms, stretching the "2 s + 5 polls" probe to ~5 minutes and a single `read_stable()` to ~8. | `scale.open_uart()` opens the UART **non-blocking** (`timeout=0`, single point of truth for `main.py` and both bench tests); `AndScale._readline()` buffers partial lines so non-blocking reads can't tear the ~80 ms A&D frames; `read_stable()` charges only the time actually waited.  CPython regression tests cover the `timeout=0` contract, torn-frame reassembly (driver + passive listen), and a bounded-probe-time assertion. |
| 4 | (found by code inspection while fixing #3, before the balance ever answered) | **Parity translation inverted**: config encodes parity 0/1/2 = none/odd/even, but the `SCALE_PARITY - 1` translation handed `machine.UART` a `1` — which MicroPython defines as **odd** (`None`/0/1 = none/**even**/odd).  The UART therefore ran 7**O**1 against the balance's 7**E**1: the HR-A discards every `Q` as a parity error and every reply arrives corrupted, so the link stays dead on a perfect harness. | `scale.open_uart()` maps config → machine explicitly (`{0: None, 1: 1, 2: 0}`); unit-tested against the HR-A default (must land as machine-even = 0). |
| 5 | Contact probe reports `FAIL` (zero bytes) with the wiring buzzed out | The bench balance previously served an **AutoTrickler**, whose [official setup guide](https://autotrickler.weebly.com/uploads/6/3/4/4/63444023/printable_a_d_trickler.pdf) reconfigures the A&D scale to **19200 baud 8N1** (`Sif bPS=5`, `btPr=2`; plus `dout Prt=5`, `SPd=2`, `RESPONSE=FAST`) — stored in non-volatile memory.  At mismatched baud the balance discards `Q` silently (`erCd 0`) and key mode never transmits unprompted: zero bytes both ways, indistinguishable from a cut wire. | `test_scale_contact.py` auto-scans the known serial presets after a `FAIL`/`PARTIAL` and prints which side to change (`config.py` `SCALE_*` values vs. balance keys); presets + scan logic unit-tested under CPython.  The same preset also boots the balance in **grains** (primary unit GN), so `dosing.py` now refuses non-gram readings instead of treating grains as grams (a 15.4× under-dose). |

The common thread of #2–#4: the CPython simulation can't catch
semantics where MicroPython's `machine` layer *behaves* differently
(blocking reads, function attributes) — those contracts are now pinned
by explicit unit tests instead of by assumption.

Status 2026-07-06: the bench reports the preset scan silent at *every*
baud, which exonerates the balance's serial settings and pins the fault
in hardware.  `test_scale_contact.py` gained a `STACKED` isolation mode
(module plugged directly onto the Pico, zero jumpers; probes both
Waveshare channels × both presets in one run), and
`firmware/BENCH_DEBUG.md` documents the on-bench agent loop
(Claude Code + `mpremote`) plus the Tailscale-SSH remote-bench setup for
iterating without the comment-thread round-trip.

## 7. Exact next steps (bench)

1. Order the new BOM lines: MAX3232 breakout (SparkFun BOB-11189 or
   equivalent), Molex Micro-Fit 3.0 4-pos receptacle 43645-0400 +
   43030 crimps (or a pre-crimped pigtail), and the RS-232 cable for
   the HR-100A's installed connector option.
2. On the balance, confirm the RS-232 function settings and mirror
   them in `config.py` (`SCALE_BAUD`/`SCALE_BITS`/`SCALE_PARITY`/
   `SCALE_STOP`; HR-A default 2400 7E1, A&D standard format).
3. Buzz out the scale harness with a meter (idle scale TXD sits at
   −5..−9 V → identifies the TX pin), then wire per assembly step 8 in
   the README.
4. Upload the firmware folder (now incl. `scale.py`, `dosing.py`) via
   MicroPico; run `tests/test_scale.py` standalone first: `w` should
   return `ST,…` frames; `r` raw-dumps if framing looks wrong.
5. Calibrate: run `g 0.5` with the demo powder; if the coarse phase
   feels slow/fast, set `DOSE_GRAMS_PER_REV` to the learned value the
   log prints, and tune `DOSE_SETTLE_MS` against the balance's actual
   settling time.
6. For the conference demo: tare with the cup on the pan (`z`), then
   `g <grams>` per request.  `DOSE_TOLERANCE_G` (5 mg) can be lowered
   towards the scale's 0.1 mg floor once the draft shield situation at
   the booth is known.
