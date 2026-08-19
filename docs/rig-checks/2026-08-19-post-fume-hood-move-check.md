# Rig check after the move back into the fume hood — 2026-08-19

Requested by @swcharles on issue #116 after moving the powder doser back into
the fume hood and re-levelling the balance: verify the Raspberry Pi and Pico
connections, the livestream, and the rig's actuators.

All checks were read-only or no-powder. **No auger tube was loaded** (confirmed
from the bench camera), so no powder could be dispensed by the actuator tests.

## Summary

| Subsystem | Result |
|---|---|
| Runner -> Pi (Tailscale) | OK -- `rpi-zero2w-powder-doser` online |
| Pi health | OK -- fresh boot, root disk 10 % used, 35.9 degC |
| Pi -> Pico (USB) | OK -- `/dev/ttyACM0`, enumerated `2e8a:0005 MicroPython Board` |
| Firmware on Pico | OK -- `config`, `main_three_phase`, `scale`, `tic`, `servo`, `powder_battery`, `battery_preflight`, `battery_feed_diagnostic` all present |
| **Balance (A&D HR-100A)** | **FAIL -- no serial response at any tested setting; LCD blank** |
| Tilt servos | OK -- plate physically reached 0 / 45 / 90 deg, confirmed on camera |
| Stepper (Tic + auger drive) | OK -- accepted enable / speed / 360 deg rotate with no error |
| Solenoid (tap) | OK -- fired without error (mass effect unverifiable, balance down) |
| Vibration (DRV2605L) | Absent -- not on the I2C bus (unchanged; block F still skips) |
| Livestream | OK -- live and framing the rig |

## Balance failure detail

`main_three_phase.Scale().read_stable()` returned `None` for 10 consecutive
attempts. A raw UART probe (passive listen plus `Q` and `S` commands) returned
**zero bytes** at the configured 19200/8/N/1 and at seven other candidate
settings, including the A&D HR-A factory default 2400/7/E/1:

    19200 8/None/1 : passive=b'' active=b''
     2400 7/0/1    : passive=b'' active=b''
     2400 8/None/1 : passive=b'' active=b''
     9600 8/None/1 : passive=b'' active=b''
     9600 7/0/1    : passive=b'' active=b''
     4800 8/None/1 : passive=b'' active=b''
     1200 7/0/1    : passive=b'' active=b''
      600 7/0/1    : passive=b'' active=b''

Silence at every setting rules out a baud/parity change (e.g. the balance's
function settings reverting to factory defaults during the move). The bench
camera then showed the HR-100A's LCD as a uniform blank rectangle with no
digits and no annunciators, while the `SAMPLE` / `PRINT` / `RE-ZERO` button
legends immediately below it are legible in the same frame -- so the camera
resolves detail at that scale and digits would be visible if the display were
on.

Leading cause: **the balance is not powered on** (switch or mains adapter),
which the operator can settle in seconds at the bench. If the display turns out
to be lit, the next suspect is the RS-232 link (Waveshare Pico-2CH-RS232 module
or the DB9 lead) disturbed during the move.

Because the balance is the measurement instrument for every block of the
battery, **no battery run should be started until it reads.** The levelling
@swcharles performed also cannot be verified remotely until the balance is on.

## Tilt servo verification

The 2026-08-11 AlSi10Mg run was invalidated because the firmware sent tilt
commands that the plate never executed, and nothing in the firmware can detect
this (there is no plate encoder). The check therefore commands each tilt, holds
it, and confirms the plate position from the bench camera:

| Commanded tilt | Held (UTC) | Camera |
|---|---|---|
| 0 deg | 15:28:33 - 15:28:53 | plate horizontal |
| 90 deg | 15:28:53 - 15:29:35 | plate vertical |
| 45 deg | 15:29:35 - 15:30:16 | plate at intermediate angle |
| 0 deg | 15:30:16 - 15:30:36 | plate horizontal again |

Frames are in `frames/`. The servo repair from 2026-08-12 survived the move.

## Stepper readback limitation (unchanged)

`TicSerial.current_position()` returns `None` on this build, so the firmware
can confirm only that commands were accepted, never that the shaft turned. With
no auger loaded and the balance down there is no independent confirmation this
session; the camera remains the ground truth, as for tilt.

## Rig state left behind

Stepper stopped and de-energised, solenoid released, plate parked at tilt 0 deg,
haptic enable pin driven low. No tmux session or capture process was started.
Temporary scripts were removed from the Pi; nothing was installed on it.
