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
| `tic.py`    | Tiny in-tree MicroPython driver for the Pololu Tic T500 stepper controller (TTL-serial command protocol). |
| `scale.py`  | Tiny in-tree driver for the A&D HR-100A balance (A&D standard RS-232 protocol: `Q`/`S`/`Z` commands, `ST,`/`US,`/`OL,` frames).  Import-safe under CPython for the simulation tests. |
| `dosing.py` | Closed-loop dose controller (issue #99): coarse auger fill with online grams-per-rev learning, fine solenoid-tap trim against the scale.  Hardware-agnostic; unit-tested in `sim/`. |
| `sim/`      | CPython simulation of the rig + unit tests for the dose loop — run `python3 sim/test_dosing_sim.py` from this folder, no hardware needed. |
| `tests/`    | Per-component bench scripts (`test_stepper.py`, `test_haptic.py`, `test_solenoid.py`, `test_servo.py`, `test_scale.py`, plus the no-keypress `test_scale_contact.py` scale-link diagnostic) — one channel at a time.  See [`tests/README.md`](tests/README.md). |
| `BENCH_DEBUG.md` | Debugging the rig with a local agent: `mpremote` command loop for Claude Code, the stacked RS-232 isolation test, and the Tailscale-SSH remote-bench setup. |

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
   This copies `main.py`, `config.py`, `drv2605.py`, `tic.py`,
   `scale.py`, `dosing.py`, and the `tests/` folder onto the Pico's
   flash filesystem.  After the upload finishes MicroPico opens its
   terminal automatically; press the soft-reset button (`Ctrl+D` in the
   terminal) or unplug/replug to start `main.py`.

   > **Upload the *whole project*, not just `main.py`.**  MicroPico's
   > green ▶ "Run" button only streams `main.py` into RAM; the `import
   > config` / `import scale` / `import dosing` lines still load from
   > whatever copies are on flash.  If you ran an older `config.py` you
   > will see `AttributeError: 'module' object has no attribute
   > 'SCALE_UART_ID'` at boot — re-run **Upload project to Pico** (which
   > pushes every module) and soft-reset.  As of the latest firmware a
   > stale/missing scale config no longer crashes the rig; it just
   > disables the scale + dosing and prints how to fix it, so the other
   > channels stay usable.

   > Before the first run, connect the **Tic T500** to your computer
   > over USB and use the **Tic Control Center** to set its *Control
   > mode* to "Serial / I²C / USB", set the *current limit* to the
   > motor's rating (670 mA for the 11HS18-0674S; never above the Tic
   > T500's 1500 mA continuous limit), and set the *Command timeout* to
   > 0 (disabled).  The firmware pushes step mode / speed / acceleration
   > over serial on boot, but the current limit and control mode are
   > one-time USB settings.

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
w            weigh (read the scale once)
z            re-zero (tare) the scale
g <grams>    closed-loop dose to <grams> (auger + tap trim)
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
> w               # one weighing datum from the HR-100A
> z               # tare the balance (with the empty cup on the pan)
> g 0.5           # dispense 0.500 g closed-loop against the scale
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
| Stepper  | `STEPPER_MICROSTEPS`     | Tic T500 microstepping (1, 2, 4, 8 — the MP6500 driver's full range). Pushed to the Tic over serial on boot. |
| Stepper  | `STEPPER_SPEED_RPM`      | Auger speed; the firmware converts it to the Tic's max-speed setting (the Pololu #3776 shunt regulator across `VIN`/`GND` clamps the back-EMF transients during deceleration). |
| Stepper  | `STEPPER_ACCEL_REV_PER_S2` | Acceleration/deceleration ramp the Tic's motion planner uses. |
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
| Scale    | `SCALE_BAUD` / `SCALE_BITS` / `SCALE_PARITY` / `SCALE_STOP` | Must mirror the balance's RS-232 function settings (HR-A default: 2400 7E1). |
| Dosing   | `DOSE_TOLERANCE_G`       | Stop band around the target mass (default ±5 mg). |
| Dosing   | `DOSE_COARSE_FRACTION` / `DOSE_COARSE_HEADROOM_G` | How much of the dose the auger handles before the tap trim takes over. |
| Dosing   | `DOSE_GRAMS_PER_REV`     | First-guess auger throughput; the loop learns the real value from the scale during each dose. |
| Dosing   | `DOSE_SETTLE_MS`         | Wait after each actuation before trusting the scale (HR-A needs ~1.5 s). |

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

* `!` issues an asynchronous "everything off" — it de-energises the
  Tic T500 stepper, drops both DRV8871 inputs, and stops the DRV2605L.
  It does **not** cut motor power; for that, pull the 12 V barrel jack.
* Set the Tic T500's current limit to the motor's per-phase current
  (≈ 0.67 A for the 11HS18-0674S) in the **Tic Control Center** over USB
  **before** the first `d` command, or the stepper will overheat.  The
  Tic has no `V_REF` pot — the limit is a software setting (and is
  enforced by the driver's on-chip current sensing).
* The 100 µF capacitor across the Tic's `VIN` is recommended for the
  12 V motor rail; it's shown as C3 on the schematic.
