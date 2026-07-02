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
| [`test_servo.py`](test_servo.py)       | Dispensing-angle servo    | (direct PWM) |
| [`test_scale.py`](test_scale.py)       | A&D HR-100A balance link  | Waveshare 2CH-RS232 |
| [`test_scale_contact.py`](test_scale_contact.py) | *Is the scale talking at all?* (no keypress) | Waveshare 2CH-RS232 |

## Scale won't respond? Run `test_scale_contact.py` first

If `w` (weigh) or `g <grams>` (dose) get **no reaction**, the Pico and
the balance are almost certainly not talking yet.  Run
[`test_scale_contact.py`](test_scale_contact.py) before anything else:
it needs **no keypresses**, opens the scale UART, listens, sends one
`Q`, and prints a `PASS` / `PARTIAL` / `FAIL` verdict with a focused
wiring/serial checklist.  On anything but a clean `PASS` it then
**re-opens the UART at each known serial preset** (HR-A factory
2400 7E1, AutoTrickler 19200 8N1) and probes again, so a balance whose
settings were changed for another system is identified — and the exact
`config.py` values to use printed — in the same run.  Even on a
completely dead link it finishes in about **8 seconds** (2 s listen +
five 1 s polls), plus ~5 s per scanned preset (worst case ~15 s total)
— if it seems to run much longer than that, the Pico is running a
pre-fix copy of
`scale.py`/`test_scale_contact.py` that opened the UART *blocking*
(each silent read stalled ~1 s, stretching the probe to ~5 minutes);
re-upload the project (**MicroPico: Upload project to Pico**).

The most common silent-link cause is a **swapped TX/RX pair** — the
scale's TX must reach the Pico's RX and vice-versa (this is exactly what
stalled the AC training-lab RS-232 bring-up,
[ac-dev-lab#20](https://github.com/AccelerationConsortium/ac-dev-lab/issues/20),
for weeks).  Its `probe_contact()` core is unit-tested under CPython in
[`../sim/test_dosing_sim.py`](../sim/test_dosing_sim.py).

### `FAIL` with the wiring checked?  Check the balance's own serial settings

There is **no RS-232 on/off switch** on the A&D HR-A series — the port
is always live, and at factory settings (2400 baud / 7 data bits / even
parity / 1 stop, A&D standard format) the balance answers the probe's
`Q` with **no menu changes at all** (per the
[HR-A/HR-AZ manual](https://weighing.andonline.com/wp-content/uploads/2024/01/HR-A_HR-AZ_Manual_02.pdf),
§10/§17).  But those settings live in non-volatile memory, so a balance
that was ever configured for another system keeps that configuration.
The concrete case for this bench: the **AutoTrickler**.  Its
[official setup instructions](https://autotrickler.weebly.com/uploads/6/3/4/4/63444023/printable_a_d_trickler.pdf)
change the A&D balance to **19200 baud, 8N1** (`Sif` → `bPS = 5`,
`btPr = 2`), plus `dout Prt = 5`, display refresh `SPd = 2`,
`RESPONSE = FAST`, and units GN/g — all stored in the scale, "and will
never change unless you perform a factory reset".  A baud/parity
mismatch makes the balance discard the Pico's `Q` **silently** — the
factory `erCd 0` setting suppresses error replies — and in key mode it
never transmits on its own, so the probe sees zero bytes: a `FAIL`
indistinguishable from a cut wire.  (`RESPONSE = FAST` and `SPd` only
affect filtering/refresh and are harmless to us; the serial items are
the link-killers.)

`test_scale_contact.py` now checks this automatically: after a `FAIL`
or `PARTIAL` at `config.py`'s settings it re-probes at each known
preset and, on an answer, prints the exact `SCALE_*` values to put in
`config.py` (or the balance keys to press to restore factory).  For an
AutoTrickler-configured balance you can simply keep its settings and
set `SCALE_BAUD = 19200`, `SCALE_BITS = 8`, `SCALE_PARITY = 0` — the
A&D command protocol is identical at any baud, and 19200 is actually
nicer for closed-loop dosing (a frame takes ~1 ms on the wire instead
of ~80 ms).

Checking takes ~30 seconds on the balance (looking changes nothing):

1. Hold **SAMPLE** until `bASFnc` appears, then release.
2. Tap **SAMPLE** repeatedly until `5if` (serial interface) shows, then
   press **PRINT** to enter the class.
3. **SAMPLE** steps through the items; confirm `bp5 2` (2400 baud) and
   `btpr 0` (7 bits, even parity), plus `Crlf 0` (CR LF) and `type 0`
   (A&D standard format) — these must match `config.py`'s
   `SCALE_BAUD/BITS/PARITY/STOP`.
4. To fix a value: **RE-ZERO** cycles the parameter, **PRINT** stores it
   (and jumps to the next class); **CAL** exits back to weighing mode.
5. If holding SAMPLE won't open the menu, the function-table lock is
   set: turn the display off, hold **PRINT** + **SAMPLE** and press
   **ON:OFF** (`p5` shows), press **PRINT**, select the first switch
   with **SAMPLE**, set it to `1` with **RE-ZERO**, store with
   **PRINT**.

Two balance-side tests bypass the Pico's transmit direction entirely:
pressing **PRINT** on a *stable* display transmits one frame (key mode
is the factory default), and setting `dout` / `prt 3` (stream mode)
transmits frames continuously.  If the probe still reports `FAIL` while
the balance is streaming, the scale→Pico path is broken in hardware and
no setting can explain it; garbled bytes (`PARTIAL`) instead prove a
format mismatch — fix `5if` as above (and set `prt` back to `0`
afterwards).  Do **not** initialize the balance (manual §9-2) just to
reset the serial settings — initialization also wipes calibration.


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
and in `test_servo.py` to flip between two preset angles.  Each script
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
* `test_servo.py`    — `TEST_ANGLE_A`, `TEST_ANGLE_B`, `TEST_STEP_DEG`, `TEST_SPEED_DEG_PER_S`

Pin numbers are intentionally **not** duplicated here — change them in
`config.py` and both the main firmware and every test script pick them
up.
