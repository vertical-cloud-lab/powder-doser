# Test-module firmware (MicroPython, Raspberry Pi Pico W)

This is the single-MCU firmware for the bench rig described in
[`hardware/test-module/README.md`](../README.md).  It runs on
**MicroPython** on a Pico W and exposes a tiny serial REPL so a bench
operator can fire any one of the four channels (auger, vibration, tap,
dispense-angle servo) independently, with every runtime parameter
exposed in a top-level `config.py`.

The firmware targets the **Raspberry Pi Pico W** (RP2040 + CYW43439).
Every pin we use sits in GP0..GP15, which is wired identically on the
plain Pico and the Pico W, so the same `main.py` runs on either board.

The editor / upload toolchain is **VS Code + the MicroPico extension**
([`paulober.pico-w-go` on the marketplace](https://marketplace.visualstudio.com/items?itemName=paulober.pico-w-go)).
MicroPico handles flashing the project to the Pico, opens a built-in
terminal that's already connected to the Pico's USB-CDC serial port,
and provides a one-click "Run current file on Pico" button — that's
the same terminal the keyboard-controlled test scripts in
[`tests/`](tests/) read keystrokes from.

## Files

| File | Purpose |
|---|---|
| `main.py`   | Main loop + driver classes; MicroPython auto-runs this on boot. |
| `config.py` | Pin map + every adjustable parameter.  Edit, re-upload via MicroPico, the Pico reboots and picks up the changes. |
| `drv2605.py`| Tiny in-tree MicroPython driver for the DRV2605L haptic chip (Adafruit's library is CircuitPython-only). |
| `tests/`    | Per-component bench scripts (`test_stepper.py`, `test_haptic.py`, `test_solenoid.py`, `test_servo.py`) — keyboard-driven, one channel at a time.  See [`tests/README.md`](tests/README.md). |

## One-time setup

1. **Flash MicroPython** on the Pico W.  Hold `BOOTSEL`, plug the USB
   cable in, and drop the latest Pico W UF2 from
   [micropython.org/download/RPI_PICO_W/](https://micropython.org/download/RPI_PICO_W/)
   onto the `RPI-RP2` drive.  The plain Pico uses the
   [`RPI_PICO`](https://micropython.org/download/RPI_PICO/) image
   instead — the firmware here is unchanged for both because we only
   use GP0..GP15.
2. **Install the MicroPico extension** in VS Code (search for
   "MicroPico" or use
   `code --install-extension paulober.pico-w-go`).  Open the
   `hardware/test-module/firmware/` folder as the workspace root.
3. **Configure the project** from the Command Palette: run
   `MicroPico: Configure project`.  This drops a `.micropico` /
   `.vscode/` config that points the extension at the right serial
   port.
4. **Upload the project** with `MicroPico: Upload project to Pico`.
   This copies `main.py`, `config.py`, `drv2605.py`, and the `tests/`
   folder onto the Pico's flash filesystem.  After the upload finishes
   MicroPico opens its terminal automatically; press the soft-reset
   button (`Ctrl+D` in the terminal) or unplug/replug to start
   `main.py`.

## Use

After boot the rig prints its current config and waits for commands.
Type `h` for the list:

```
h            show this help
s            print rig state / config
d            dispense (rotate auger STEPPER_DISPENSE_DEG)
r <deg>      rotate auger by <deg> (signed)
v            vibrate (single canned effect)
t            tap (TAP_COUNT solenoid pulses)
a <deg>      servo to <deg>
p <preset>   servo to named preset (horizontal/tilt/vertical/tip)
!            emergency stop -- de-energise everything
```

Examples:

```
> r 90            # auger rotates 90 deg in the configured direction
> r -45           # ...and 45 deg the other way
> a 30            # servo to 30 deg
> p vertical      # servo to the "vertical" preset (default 90 deg)
> t               # fire TAP_COUNT solenoid pulses
> v               # single haptic buzz
> d               # one full dispense cycle
> !               # de-energise everything (stepper, solenoid, haptic)
```

To exercise just one channel, open the matching script under `tests/`
and click MicroPico's **"Run current file on Pico"** — see
[`tests/README.md`](tests/README.md) for the full per-script keymap.

## Adjustable configurations

Every parameter the bench operator cares about lives in `config.py`.
Common knobs:

| Block | Parameter | Effect |
|---|---|---|
| Stepper  | `STEPPER_MICROSTEPS`     | DRV8825 1, 2, 4, 8, 16, 32 microstepping. |
| Stepper  | `STEPPER_SPEED_RPM`      | Step rate (5..240 is safe; the Pololu #3776 shunt regulator added across `VMOT`/`GND` clamps the back-EMF transients during deceleration). |
| Stepper  | `STEPPER_DIRECTION`      | Flip auger sense without re-wiring. |
| Stepper  | `STEPPER_DISPENSE_DEG`   | How much auger rotation per `d` command. |
| Vibration| `VIBRATION_EFFECT_ID`    | Pick from DRV2605L's 123-effect ROM. |
| Vibration| `VIBRATION_LIBRARY`      | 1 = ERM, 6 = LRA. |
| Vibration| `VIBRATION_DURATION_S`   | How long to hold the buzz. |
| Tap      | `TAP_COUNT`              | Pulses per `t` command. |
| Tap      | `TAP_ON_MS` / `TAP_OFF_MS` | Duty cycle of the solenoid. |
| Tap      | `TAP_PWM_DUTY`           | Holding-force PWM (0..1). |
| Servo    | `SERVO_MIN_PULSE_US` / `_MAX_PULSE_US` | Calibrate to the specific servo. |
| Servo    | `SERVO_SPEED_DEG_PER_S`  | Smoothness of `a`/`p` moves -- the firmware interpolates from the current angle to the target at this rate (deg/s) so the servo never slams.  Set to 0 to revert to instantaneous "snap" moves. |
| Servo    | `SERVO_UPDATE_HZ`        | Interpolation update rate; default 50 Hz matches the servo PWM frame. |
| Servo    | `SERVO_PRESETS`          | Add/rename `p <preset>` shortcuts. |

After editing `config.py`, re-run `MicroPico: Upload project to Pico`
(or just **right-click → "Upload file to Pico"** on the changed file)
and soft-reset.

## Pin map

Same as the schematic — see the "Pin / net table" section of the
[parent README](../README.md).  If you ever re-pin, the constants at
the top of `config.py` are the single source of truth on the firmware
side and `hardware/test-module/kicad/generate.py` is the single source
of truth on the schematic side; keep them in sync.

## Safety notes

* `!` issues an asynchronous "everything off" — it disables the
  DRV8825, drops both DRV8871 inputs, and stops the DRV2605L.  It does
  **not** cut motor power; for that, pull the 12 V barrel jack.
* The DRV8825 carrier needs its current-limit pot adjusted to the
  motor's per-phase current (≈ 0.67 A for the 11HS18-0674S — refer to
  Pololu's `Vref = I × 2 × R_sense` cheat-sheet) **before** the first
  `d` command, or the stepper will overheat.
* The 100 µF capacitor across the DRV8825's `VMOT` is mandatory per
  Pololu; it's shown as C3 on the schematic.
