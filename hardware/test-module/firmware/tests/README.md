# Per-component bench-test scripts

Each script here exercises a **single** component on the powder-doser
test module, using exactly the pin assignments in
[`../config.py`](../config.py) (which is also the contract the KiCad
schematic is generated from).  This lets you bring the bench rig up one
channel at a time and prove every wire and driver works in isolation
before running the full `code.py`.

The setup is unchanged from the main rig: a Raspberry Pi Pico W powered
from the Pololu D24V22F5 buck regulator (12 V → 5 V), with the same
DRV8825 / DRV2605L / DRV8871 / servo wiring.

| File | What it tests | Driver IC |
|---|---|---|
| [`test_stepper.py`](test_stepper.py)   | Auger stepper motor       | DRV8825 |
| [`test_haptic.py`](test_haptic.py)     | Vibration / haptic motor  | DRV2605L |
| [`test_solenoid.py`](test_solenoid.py) | Tap solenoid              | DRV8871 |
| [`test_servo.py`](test_servo.py)       | Dispensing-angle servo    | (direct PWM) |

## How to run one

CircuitPython only auto-runs `code.py` in the root of the `CIRCUITPY`
drive.  To bring up a single channel:

1. Copy this whole `tests/` folder to `CIRCUITPY/tests/` (the scripts
   import `tests._keypress`, so the folder layout has to be preserved).
2. Copy the test script you want as `code.py`:

   ```sh
   # macOS / Linux example
   cp tests/test_haptic.py /Volumes/CIRCUITPY/code.py
   ```

3. Open the Pico W's USB-serial port (`tio /dev/tty.usbmodem*`,
   `screen /dev/ttyACM0 115200`, PuTTY, etc.) and start pressing keys.

When you're done, copy the full `code.py` back to restore the
multi-channel REPL.

## Keyboard controls

Every script reads single keystrokes over USB-serial (no Enter
required) using `tests/_keypress.py`'s non-blocking helper.  The
primary action on each rig is always **spacebar** — e.g. press space
in `test_haptic.py` to fire the vibration motor, in `test_solenoid.py`
to click the solenoid once, in `test_stepper.py` to advance the auger,
and in `test_servo.py` to flip between two preset angles.  Each
script prints its full keymap on start; `h` re-prints it and `q` exits
cleanly.

## Adjustable variables

Each file exposes its tunables as `TEST_*` constants near the top
(initialised from `config.py` so the defaults match the main rig).
Edit any of them, save, and CircuitPython will reload the script
automatically.  Examples:

* `test_stepper.py`  — `DEFAULT_MOVE_DEG`, `SPEED_STEP_RPM`, `START_DIRECTION`
* `test_haptic.py`   — `TEST_EFFECT_ID`, `TEST_DURATION_S`, `TEST_EFFECT_SWEEP`
* `test_solenoid.py` — `TEST_ON_MS`, `TEST_OFF_MS`, `TEST_BURST_COUNT`, `TEST_DUTY`
* `test_servo.py`    — `TEST_ANGLE_A`, `TEST_ANGLE_B`, `TEST_STEP_DEG`, `TEST_SPEED_DEG_PER_S`

Pin numbers are intentionally **not** duplicated here — change them in
`config.py` and both the main firmware and every test script pick them
up.
