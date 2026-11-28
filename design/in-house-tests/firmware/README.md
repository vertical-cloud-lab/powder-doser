# Accessory Pico 2 W firmware

**Status: design, 2026-11-28. Tested only in simulation** (CPython, register-level fakes). It has not
run on a Pico yet. Pins and numbers follow [`../SPEC.md`](../SPEC.md) section 0.2.

The accessory Pico sits on the bench Pi 5's USB and runs the new parts for tests 2, 3, 5, 8, 9 and
10: two hobby servos, a Tic T500 stepper (cam tapper or linear stage), a second DRV8871 tapper, the
charge amplifier's reset relay, a limit/index input, the backlight and an I2C chain (NAU7802,
LSM6DSOX, SHT45, ADS1115). The doser's own Pico is untouched.

## Files

| File | On the Pico | What |
|---|---|---|
| `accessory_main.py` | as `main.py` | command loop, cooperative tasks, all command handlers |
| `config.py` | yes | pins, servo ranges, motor profiles, sensor settings |
| `protocol.py` | yes | line parser, JSON replies, command table (`help`) |
| `units.py` | yes | pure conversions: servo pulses, 1:2 table gear, Tic units, cam timing, tilt from gravity, CRC, ADC to charge |
| `sensors.py` | yes | NAU7802, LSM6DSOX, SHT45, ADS1115 drivers |
| `actuators.py` | yes | servo, DRV8871 tapper, backlight, Tic motor with profiles |
| `tic.py` | yes | the doser rig's Tic T500 driver (from `d14a50d`), with one fix (below) |
| `hw.py` | yes | builds the real hardware; a missing sensor is reported, not fatal |
| `compat.py` | yes | clock shim (MicroPython ticks or CPython time) |
| `sim_hw.py` | no | fake Pin/PWM/UART/I2C chips and a fake Tic, for tests and the bench simulator |
| `tests/` | no | pytest, 43 tests |

## Install

1. Flash MicroPython for the Pico 2 W (RP2350) from micropython.org (hold BOOTSEL, copy the UF2).
2. Copy the files (from this folder, with [`mpremote`](https://docs.micropython.org/en/latest/reference/mpremote.html)):
   ```bash
   mpremote cp config.py compat.py units.py protocol.py sensors.py actuators.py tic.py hw.py :
   mpremote cp accessory_main.py :main.py
   mpremote reset
   ```
   Optional, to save RAM and boot time: precompile the modules with `mpy-cross` (same MicroPython
   version), copy `accessory_main.mpy` under its own name, and use a two-line `main.py`:
   `import accessory_main` and `accessory_main.main()`.
3. Tic T500, once, in the Tic Control Center over USB: control mode *Serial / I2C / USB*, baud 9600,
   *command timeout* on (1000 ms; the firmware resets it every 500 ms while a move runs, so a hung
   Pico stops the motor). The firmware sets step mode, speed, acceleration and the current limit from
   the motor profile. Check the current once in the Control Center after `motor cam` and `motor stage`.
4. Check: `mpremote` terminal or `python -m bench.run status` on the Pi 5. The Pico prints a
   `{"ev": "boot", "missing": [...]}` line at start-up.

## Wiring

| Pico pin | GPIO | Goes to | Cable / notes |
|---|---|---|---|
| 1, 2 | GP0, GP1 | I2C0 SDA, SCL | STEMMA QT chain: SHT45 (0x44), LSM6DSOX (0x6A, on the tilt plate), NAU7802 (0x2A), charge-amp ADS1115 (0x48). 3V3 and GND from the Pico |
| 6 | GP4 | Tic RX | UART1 TX, TTL 3.3 V |
| 7 | GP5 | Tic TX | UART1 RX. Wire it: the firmware reads the position back; without it, moves end on an estimated time |
| 9 | GP6 | servo A signal | orifice gate, 9 g metal-gear servo. Servo power from a separate 5 V supply, common GND |
| 10 | GP7 | servo B signal | tilt table, 20 kg.cm servo through the 1:2 gear. Own 6 V, 3 A supply, common GND |
| 11 | GP8 | DRV8871 #2 IN1 | tapper solenoid (JF-0530B), PWM 20 kHz |
| 12 | GP9 | DRV8871 #2 IN2 | held low |
| 14 | GP10 | reed-relay driver | charge-amp PCB reset input; high = relay closed = C_f shorted |
| 15 | GP11 | aux input | stage profile: home limit switch (NO to GND, internal pull-up). Cam profile: TCRT5000 index output (low over the flag). One motor is connected at a time, so they share the pin |
| 16 | GP12 | backlight MOSFET gate | logic-level N-MOSFET, low side of the LED pad's 5 V |
| 31 | GP26 | spare | ADC0 |
| 3, 8, 13, 18, 38 | GND | all grounds | one star point with the servo and solenoid supplies |

GP11 serving both the limit switch and the cam index is a choice made here; SPEC 0.2 lists GP11 for
the limit switch and does not give the TCRT5000 a pin.

## Protocol

One command per line in, one JSON object per line out. Add `#<n>` anywhere to get `"id": n` back.

```text
> table 30 rate=0.5 stream=20 #7
< {"ok": true, "cmd": "table", "t": 81234, "id": 7, "from": 0.0, "target": 30.0, "rate": 0.5, "eta_s": 60.0}
< {"ev": "imu", "t": 81284, "deg": 0.02, "cmd_deg": 0.03, "jolt": 0.001}
  ...
< {"ev": "done", "t": 141290, "task": "table", "reason": "done", "cmd_deg": 30.0, "deg": 29.98}
```

- `t` is the Pico's millisecond clock. The bench stamps each line with its own receive time too.
- Errors: `{"ok": false, "cmd": "...", "err": "..."}`. Unknown commands and out-of-range values are errors.
- Long actions (ramps, moves, tap trains, streams) answer at once and run as tasks; each ends with a
  `done` event whose `reason` is `done`, `stopped`, `estop`, `replaced`, `jolt`, `limit`, `timeout`,
  `no_index`, `no_switch` or `error`. So `estop` and `stop` act immediately, mid-move.

## Commands

| Command | Does | Reply / events |
|---|---|---|
| `ping` | liveness | `pong`, `fw` |
| `help` | command list | `commands` |
| `status` | devices found, tasks, positions, relay, light, calibration | many fields |
| `estop` or `!` | end every task, halt and de-energise the stepper, tapper off, relay closed; servos hold | `stopped` |
| `stop [name]` | end tasks whose name starts with `name` (all by default) | `stopped` list |
| `gate open\|close\|<deg> [speed=]` | servo A, eased ramp (default 180 deg/s) | `eta_s`; `done` |
| `servo a\|b <deg> [speed=]` | raw servo move in servo degrees | `eta_s`; `done` |
| `table <deg> [rate=] [stream=Hz] [halt=g]` | table to `deg` (servo B = 2 x table) at a constant `rate` deg/s; IMU stream; optional stop on a jolt above `halt` g | `imu` events; `done` (`deg`, `cmd_deg`) |
| `table stop` | hold where it is | `deg`, `cmd_deg` |
| `imu [n=]` | plate angle from gravity (mean of n), raw axes | `deg`, `sd`, `a_g`, `g_dps`, `temp_c` |
| `imu zero [n=]` | set the angle offset with the table on its level stop (saved) | `offset_deg` |
| `imu stream <Hz> [s=]` | stream angle and jolt | `imu` events |
| `motor [cam\|stage]` | show or switch the stepper profile (idle only; sets the T500 current code) | `profile`, `current_code` |
| `cam home` | turn slowly to the index flag, zero there | `done` |
| `cam taps <n> [rate=]` | n drops at rate taps/min (2 lobes: rpm = rate / 2; 250/min = 125 rpm) | `turns`, `eta_s`; `done` with `index_turns`, `index_ok` |
| `stage home [speed=]` | fast to the switch, back off 2 mm, slow to the switch, zero, park at 1 mm | `done` |
| `stage move\|rel <mm> [speed=]` | absolute or relative move, 0 to 100 mm, 0.01-100 mm/s | `eta_s`; `done` |
| `stage speed <mm/s>` / `pos` / `stop` / `off` | default speed / position / halt / de-energise | |
| `tap <n> [rate=] [on=]` | solenoid taps; refuses more than 25 % coil on-time | `eta_s`; `done` |
| `lc read [n=]` / `lc tare` / `lc cal <g>` | load cell grams; tare; scale from a known mass (saved) | `g`, `sd_g`, `raw` |
| `lc rate <10\|20\|40\|80\|320>` / `lc stream <Hz> [s=]` | NAU7802 rate; stream | `lc` events (`g`, `raw`) |
| `env` / `env stream <Hz> [s=]` | SHT45 temperature and RH | `t_c`, `rh` |
| `q zero [ms=]` | close the reset relay for ms (default 500), then open: integrator starts at zero | `done` |
| `q short` | close the relay and keep it closed (idle state) | |
| `q read [n=]` / `q stream <Hz> [s=]` | ADS1115 AIN0-AIN1 volts and charge Q = -C_f V | `v`, `nc` |
| `q gain <6.144\|4.096\|...\|0.256>` / `q cf <nF>` | ADC range; which C_f is fitted (10 or 100 nF) | `full_scale_nc` |
| `light on\|off\|<0-100>` | backlight PWM (20 kHz) | `level` |
| `i2c` / `cal [show\|save\|clear]` | bus scan / calibration file `cal.json` | |

## Behaviour worth knowing

- **Servos are not driven at boot.** Their first command ramps from the assumed rest position (gate
  shut, table level), so a table left tilted by hand jumps once. Send `table 0 rate=5` first.
- **The table moves in steps of about 0.1 deg.** At 0.5 deg/s the ramp's set point changes by 0.01 deg
  per 20 ms update, below a hobby servo's deadband (1-5 us, 0.05-0.25 table deg). Log the IMU angle,
  not the commanded one; the bench does.
- **A slip's jolt reads as tilt.** 0.05 g along the slope looks like 2.9 deg to an accelerometer. The
  bench takes slip angles from a line fitted to the IMU ramp just before the event.
- **Home the cam with the carriage empty.** Homing lifts and drops the carriage; with a cylinder in it,
  that is one or two uncounted taps (about 2 % on bulk density in simulation).
- **Cam timing.** At 250 taps/min the 2-lobe cam turns at 125 rpm, 240 ms per drop. A 3.0 mm drop
  takes 24.7 ms of free fall; the snail's step (taken as 4 deg) clears the follower in 5.3 ms, so the
  carriage falls freely (`units.cam_timing`).
- **Stage resolution.** 8 mm lead, 1/8 step: 0.005 mm per microstep. 0.05-0.2 mm/s is 10-40
  microsteps/s. (SPEC 0.3's "6-24 motor steps/s" does not match its own 0.005 mm per microstep.)
- **Tic current codes round down** (T500 table, Tic user's guide section 6): 670 mA asks for code 5
  (634 mA, the NEMA 11), 1000 mA for code 8 (990 mA, the NEMA 17).
- **`tic.py` fix.** The rig's copy sends "Get variable" as 2 bytes; the Tic expects 3 (command, offset,
  length; user's guide section 9), so it never answers. That may be why the rig found position
  read-back unreliable. The copy here sends the length byte; the fake Tic in `sim_hw.py` insists on it.

## Tests

```bash
/tmp/venv/bin/python -m pytest -q tests      # 43 passed in about 0.3 s
```

`test_units_protocol.py` checks the conversions (servo pulses, gear, Tic codes and speeds, cam timing,
tilt with a rolled mount, Sensirion CRC, ADS1115 config words, charge full scale +-24 / +-240 nC) and
the Tic byte framing. `test_accessory.py` runs the real `Accessory` on the fakes: eased gate ramp,
table ramp at 0.5 deg/s with the IMU stream, halt on jolt, `imu zero` with a mounting offset, tap
timing and the duty limit, stage homing / moves / soft limits / estop mid-move, moves without Tic
read-back, cam homing and index counting, load-cell tare and calibration, SHT45, charge relay and
range, light, stream start and stop.

## Known gaps

- Never run on a Pico: `uselect` polling of USB stdin, PWM at 20 kHz on the RP2350, and I2C timing
  are untested on hardware. The NAU7802 start-up follows the datasheet's section 9.1 and SparkFun's
  library order.
- Servo end points, gate angles (`GATE_OPEN_DEG`, `GATE_CLOSED_DEG`) and `TABLE_ZERO_SERVO_DEG` must
  be set on the bench.
- The humidity boxes' SHT45s are on the Pi 5's own I2C bus (TCA9548A), not here (SPEC 6).
- No watchdog: a reset would re-run boot with the servos unpowered, which is the safe state.
