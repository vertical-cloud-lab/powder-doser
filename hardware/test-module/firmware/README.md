# Test-module firmware (CircuitPython, Raspberry Pi Pico W)

This is the single-MCU firmware for the bench rig described in
[`hardware/test-module/README.md`](../README.md).  It exposes a tiny
serial REPL so a bench operator can fire any one of the four channels
(auger, vibration, tap, dispense-angle servo) independently, with every
runtime parameter exposed in a top-level `config.py`.

The firmware targets the **Raspberry Pi Pico W** (RP2040 + CYW43439).
Every pin we use sits in GP0..GP15, which is wired identically on the
plain Pico and the Pico W, so the same `code.py` runs on either board.

## Files

| File | Purpose |
|---|---|
| `code.py`   | Main loop + driver classes; CircuitPython auto-runs this on boot. |
| `config.py` | Pin map + every adjustable parameter.  Edit & save -> Pico W reloads. |

## Install

1. **Flash CircuitPython 9.x for the Pico W** (UF2 from
   [circuitpython.org/board/raspberry_pi_pico_w](https://circuitpython.org/board/raspberry_pi_pico_w/)).
   Hold `BOOTSEL`, plug in USB, drop the UF2 onto the `RPI-RP2` drive.
   The same image works for the plain Pico — just grab
   `raspberry_pi_pico` instead.
2. The Pico W re-enumerates as `CIRCUITPY`.  Copy this folder's
   `code.py` and `config.py` to the root.
3. Drop the following libraries from the
   [Adafruit CircuitPython library bundle](https://circuitpython.org/libraries)
   into `CIRCUITPY/lib/`:
   - `adafruit_bus_device/`
   - `adafruit_drv2605.mpy`
4. Open a serial terminal on the Pico's USB CDC port at any baud
   (CircuitPython ignores it):
   - macOS / Linux: `tio /dev/tty.usbmodem*` or
     `screen /dev/ttyACM0 115200`
   - Windows: any PuTTY-style terminal on the new COM port.

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

Saving the file causes CircuitPython to reload `code.py` automatically;
no re-flash needed.

## Pin map

Same as the schematic — see the "Pin / net table" section of the
[parent README](../README.md).  If you ever re-pin, the constants at the
top of `config.py` are the single source of truth on the firmware side
and `hardware/test-module/kicad/generate.py` is the single source of
truth on the schematic side; keep them in sync.

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
