# Per-component bench-test scripts (MicroPython)

Each script here exercises a **single** component on the powder-doser
test module, using exactly the pin assignments in
[`../config.py`](../config.py) (which is also the contract the KiCad
schematic is generated from).  This lets you bring the bench rig up one
channel at a time and prove every wire and driver works in isolation
before running the full `main.py`.

The setup is unchanged from the main rig: a Raspberry Pi Pico W powered
from the Pololu D24V22F5 buck regulator (12 V → 5 V), with the same
Tic T500 / DRV2605L / DRV8871 / servo wiring.

| File | What it tests | Driver IC |
|---|---|---|
| [`test_stepper.py`](test_stepper.py)   | Auger stepper motor       | Tic T500 (MP6500) |
| [`test_haptic.py`](test_haptic.py)     | Vibration / haptic motor  | DRV2605L |
| [`test_solenoid.py`](test_solenoid.py) | Tap solenoid              | DRV8871 |
| [`test_servo.py`](test_servo.py)       | Dual dispensing-angle servos | (direct PWM) |

## Running a single script from VS Code + MicroPico

The whole firmware folder targets **MicroPython** running on the Pico W,
edited and uploaded from VS Code via the
[**MicroPico** extension](https://marketplace.visualstudio.com/items?itemName=paulober.pico-w-go).
See the [parent `firmware/README.md`](../README.md) for the one-time
flash / extension install.

Once the firmware folder is uploaded to the Pico (MicroPico command:
**"MicroPico: Upload project to Pico"**), bringing up one channel takes
two clicks:

1. Open the test you want (e.g. `tests/test_haptic.py`).
2. Click **"Run current file on Pico"** in the status bar (or run the
   `MicroPico: Run current file on Pico` command from the palette).

MicroPico's built-in terminal is already wired to the Pico's USB-CDC
serial port, so it streams the script's output *and* feeds your
keystrokes into `sys.stdin` — that's all the keyboard-controls path
needs.  Press the script's quit key (`q`) to drop back to the REPL.

> Note: MicroPython auto-runs `main.py` on boot, **not** the test
> scripts — re-plugging the Pico will always start the multi-channel
> `main.py` REPL again, so there's no need to restore anything when
> you're done testing a single channel.

## Keyboard controls

Every script reads single keystrokes from MicroPico's terminal (no
Enter required) using the shared `tests/_keypress.py` helper, which
polls `sys.stdin` non-blockingly via `uselect.poll()`.  The primary
action on each rig is always **spacebar** — press space in
`test_haptic.py` to fire the vibration motor, in `test_solenoid.py` to
click the solenoid once, in `test_stepper.py` to advance the auger,
and in `test_servo.py` to flip both servos between two preset angles
(the two servos move in unison; servo 2 mirrors servo 1).  Each script
prints its full keymap on start; `h` re-prints it and `q` exits
cleanly.

## Adjustable variables

Each file exposes its tunables as `TEST_*` constants near the top
(initialised from `config.py` so the defaults match the main rig).
Edit any of them, save, and hit **"Run current file on Pico"** again —
MicroPico re-uploads and re-runs in under a second.  Examples:

* `test_stepper.py`  — `DEFAULT_MOVE_DEG`, `SPEED_STEP_RPM`, `START_DIRECTION`
* `test_haptic.py`   — `TEST_EFFECT_ID`, `TEST_DURATION_S`, `TEST_EFFECT_SWEEP`
* `test_solenoid.py` — `TEST_ON_MS`, `TEST_OFF_MS`, `TEST_BURST_COUNT`, `TEST_DUTY`
* `test_servo.py`    — `TEST_ANGLE_A`, `TEST_ANGLE_B`, `TEST_STEP_DEG`, `TEST_SPEED_DEG_PER_S`, `TEST_INVERT`

Pin numbers are intentionally **not** duplicated here — change them in
`config.py` and both the main firmware and every test script pick them
up.
