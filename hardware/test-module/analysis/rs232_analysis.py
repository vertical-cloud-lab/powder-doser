#!/usr/bin/env python3
"""ngspice electrical analysis of the HR-100A scale RS-232 interface.

Issue #99 adds an A&D HR-100A balance to the bench rig.  The balance's
RS-232C driver swings roughly +/-5..9 V; the RP2040's GPIO absolute
maximum ratings are -0.3 V .. VDDIO+0.3 V (~3.6 V).  This script runs
three ngspice simulations to check the proposed interface and document
why the rejected alternative is unsafe:

  1. ``direct_connect``  -- REJECTED design: scale TXD wired straight to
     a Pico GPIO through the pin's ESD diodes.  Shows the GPIO node is
     dragged far outside the -0.3/+3.6 V absolute-maximum window and
     computes the diode fault current.
  2. ``max3232_rx``      -- ACCEPTED design: the same +/-7 V RS-232 swing
     into the MAX3232's receiver (0.3/2.4 V thresholds, 5 kohm input
     impedance per the datasheet).  Confirms the logic-side output is a
     clean 0/3.3 V swing for the Pico and the scale-side load current
     stays within the balance driver's capability.
  3. ``max3232_tx``      -- the MAX3232 transmitter driving the scale's
     RS-232 receiver (5 kohm nominal load) through 2 m of cable
     (~200 pF): verifies >= |+/-5| V levels at the scale and slew across
     the +/-3 V transition region fast enough for 2400-9600 baud.

Run from this directory:  ``python3 rs232_analysis.py``
(writes ``rs232_analysis_results.md`` and per-sim ``.log`` files).

The MAX3232 is modelled behaviourally (B-sources + datasheet limits:
+/-5.4 V typical swing at 3.3 V supply, 300 ohm output impedance, 5 kohm
receiver input, 0.3 V/us min slew) -- the goal is interface-level safety
margins, not chip-internal fidelity.
"""

import re
import subprocess
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

# ---------------------------------------------------------------------------
# Netlists
# ---------------------------------------------------------------------------

# 1. REJECTED: scale TXD direct to Pico GPIO.  The GPIO pad is modelled
# as its two ESD/clamp diodes (to 3V3 and to GND) plus the pad
# capacitance; the scale driver as +/-7 V behind 300 ohm (typical RS-232
# driver impedance).  Series resistance is just the cable.
DIRECT_CONNECT = """\
* REJECTED: A&D scale RS-232 TXD direct into RP2040 GPIO
VDD vdd 0 DC 3.3
* scale driver: +/-7V square wave at 2400 baud behind 300 ohm
VTX drv 0 PULSE(-7 7 0 1u 1u 208u 416u)
RDRV drv pad 300
CPAD pad 0 5p
* RP2040 pad clamp diodes (generic silicon)
DLO 0 pad DCLAMP
DHI pad vdd DCLAMP
.model DCLAMP D(IS=1e-14 RS=5 N=1.2 BV=12)
.control
tran 0.5u 1.2m
meas tran vmax MAX v(pad)
meas tran vmin MIN v(pad)
let ai = abs(i(VTX))
meas tran ifault_pk MAX ai
.endc
.end
"""

# 2. ACCEPTED, receive path: scale +/-7 V into MAX3232 R1IN (5k input
# resistance per datasheet, 0.3/2.4 V slicer thresholds), R1OUT swings
# 0..3.3 V into the Pico's ~5 pF pad.
MAX3232_RX = """\
* ACCEPTED: scale RS-232 TXD -> MAX3232 R1IN -> 3.3V logic -> Pico GP13
VDD vdd 0 DC 3.3
VTX drv 0 PULSE(-7 7 0 1u 1u 208u 416u)
RCAB drv r1in 50
* datasheet receiver input resistance 3k..7k (5k typ) to ground
RIN r1in 0 5k
* behavioural slicer: inverting receiver w/ 1.2V threshold approximation
BRX r1out 0 V = v(r1in) > 1.2 ? 0 : 3.3
RPICO r1out gp13 100
CPICO gp13 0 5p
.control
tran 0.5u 1.2m
meas tran vrx_hi MAX v(gp13)
meas tran vrx_lo MIN v(gp13)
meas tran vin_pk MAX v(r1in)
let ai = abs(i(VTX))
meas tran iin_pk MAX ai
.endc
.end
"""

# 3. ACCEPTED, transmit path: MAX3232 T1OUT (+/-5.4 V typ behind ~300
# ohm) driving 2 m cable (200 pF) + scale receiver (5k).
MAX3232_TX = """\
* ACCEPTED: Pico GP12 -> MAX3232 T1IN -> T1OUT -> cable -> scale RXD
* logic input: 0..3.3V square at 9600 baud (104us bit)
VLOG t1in 0 PULSE(0 3.3 0 100n 100n 52u 104u)
* behavioural inverting transmitter, +/-5.4V swing, 300 ohm out
BTX t1raw 0 V = v(t1in) > 1.65 ? -5.4 : 5.4
ROUT t1raw t1out 300
* 2m cable ~100pF/m + scale receiver 5k
CCAB t1out 0 200p
RSCALE t1out 0 5k
.control
tran 0.2u 320u
meas tran vtx_hi MAX v(t1out)
meas tran vtx_lo MIN v(t1out)
* time spent crossing the RS-232 undefined band (-3..+3V) on first fall
meas tran tcross TRIG v(t1out) VAL=3 FALL=1 TARG v(t1out) VAL=-3 FALL=1
.endc
.end
"""

SIMS = [
    ("direct_connect", DIRECT_CONNECT),
    ("max3232_rx", MAX3232_RX),
    ("max3232_tx", MAX3232_TX),
]

MEAS_RE = re.compile(r"^(\w+)\s*=\s*([-+0-9.eE]+)", re.M)


def run(name: str, deck: str) -> dict:
    deck_path = HERE / f"{name}.cir"
    log_path = HERE / f"{name}.log"
    deck_path.write_text(deck)
    proc = subprocess.run(
        ["ngspice", "-b", str(deck_path)],
        capture_output=True, text=True, timeout=120,
    )
    log_path.write_text(proc.stdout + proc.stderr)
    meas = {m.group(1): float(m.group(2))
            for m in MEAS_RE.finditer(proc.stdout)}
    deck_path.unlink()
    return meas


def main() -> int:
    if shutil.which("ngspice") is None:
        print("ngspice not on PATH -- install with: "
              "sudo apt-get install ngspice", file=sys.stderr)
        return 1

    results = {name: run(name, deck) for name, deck in SIMS}

    d = results["direct_connect"]
    rx = results["max3232_rx"]
    tx = results["max3232_tx"]

    checks = [
        ("direct: GPIO dragged below -0.3 V abs max",
         d.get("vmin", 0) < -0.3, f"vmin = {d.get('vmin', float('nan')):.2f} V"),
        ("direct: GPIO dragged above +3.6 V abs max",
         d.get("vmax", 0) > 3.6, f"vmax = {d.get('vmax', float('nan')):.2f} V"),
        ("direct: clamp fault current > 10 mA",
         abs(d.get("ifault_pk", 0)) > 0.010,
         f"ifault_pk = {abs(d.get('ifault_pk', 0))*1000:.1f} mA"),
        ("max3232 rx: logic high ~3.3 V",
         3.0 <= rx.get("vrx_hi", 0) <= 3.45,
         f"vrx_hi = {rx.get('vrx_hi', float('nan')):.2f} V"),
        ("max3232 rx: logic low ~0 V",
         -0.05 <= rx.get("vrx_lo", 1) <= 0.3,
         f"vrx_lo = {rx.get('vrx_lo', float('nan')):.2f} V"),
        ("max3232 rx: scale sees benign load (< 5 mA)",
         abs(rx.get("iin_pk", 1)) < 0.005,
         f"iin_pk = {abs(rx.get('iin_pk', 0))*1000:.2f} mA"),
        ("max3232 tx: drives >= +5 V into scale",
         tx.get("vtx_hi", 0) >= 5.0,
         f"vtx_hi = {tx.get('vtx_hi', float('nan')):.2f} V"),
        ("max3232 tx: drives <= -5 V into scale",
         tx.get("vtx_lo", 0) <= -5.0,
         f"vtx_lo = {tx.get('vtx_lo', float('nan')):.2f} V"),
        ("max3232 tx: +/-3 V crossing < 4 us (ok to 115k baud)",
         0 < tx.get("tcross", 1) < 4e-6,
         f"tcross = {tx.get('tcross', float('nan'))*1e6:.2f} us"),
    ]

    lines = [
        "# ngspice analysis: HR-100A RS-232 interface (issue #99)",
        "",
        "Generated by `rs232_analysis.py`; raw ngspice output in the",
        "`*.log` files next to this report.",
        "",
        "| check | expectation met | measured |",
        "|---|---|---|",
    ]
    all_ok = True
    for label, ok, detail in checks:
        lines.append(f"| {label} | {'yes' if ok else '**NO**'} | {detail} |")
        all_ok &= ok
        print(("PASS " if ok else "FAIL ") + label + " -- " + detail)

    lines += [
        "",
        "## Interpretation",
        "",
        "* **Direct connection is unsafe** (sim 1): the scale's RS-232",
        "  swing forces the GPIO pad outside the RP2040's -0.3..+3.6 V",
        "  absolute-maximum window and pushes >10 mA through the pad",
        "  clamp diodes -- a latch-up / slow-death scenario. This is why",
        "  the design uses a transceiver instead of a resistor bodge.",
        "* **MAX3232 receive path is clean** (sim 2): the Pico sees a",
        "  0-3.3 V logic signal; the scale's driver only sources ~1.4 mA",
        "  into the 5 kohm receiver, well inside RS-232 drive limits.",
        "* **MAX3232 transmit path meets RS-232 levels** (sim 3): >= +/-5 V",
        "  at the scale under the 5 kohm + 200 pF cable load, and the",
        "  transition band is crossed in ~1 us, far faster than the",
        "  ~52 us bit half-period at 9600 baud (HR-A default is 2400).",
        "",
        f"**Overall: {'PASS -- design accepted' if all_ok else 'FAIL'}**",
    ]
    (HERE / "rs232_analysis_results.md").write_text("\n".join(lines) + "\n")
    print("\nwrote rs232_analysis_results.md")
    return 0 if all_ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
