# Rig re-check, 2026-08-19 (balance switched on, tap collar cleared)

Follow-up to `2026-08-19-post-fume-hood-move-check.md`, after @swcharles
switched the balance on and freed the solenoid tap collar that had been
catching under the mounting plate.

Times below are MDT (lab local) unless marked UTC.

## Summary

| Subsystem | Result |
|---|---|
| Runner -> Pi (Tailscale) | OK |
| Pi -> Pico (`/dev/ttyACM0`) | OK, all firmware modules present |
| Tilt servos, plate motion | **OK, and the 0 deg pose is now genuinely flat** |
| Livestream | live, `rJcqtYHWhGM` |
| **A&D HR-100A balance** | **still silent on the serial link** |
| DRV2605L vibration driver | still absent from the I2C bus |

## Balance: powering it on did not restore the serial link

`AndScale.read_stable()` returned `None` 12/12 times.  A raw UART probe
(passive listen, then `Q`, then `S`) returned **zero bytes at all ten
candidate line settings**, including the configured 19200/8/N/1 and the
A&D HR-A factory default 2400/7/E/1:

    19200 8/N/1   2400 7/E/1   2400 8/N/1   9600 8/N/1   9600 7/E/1
     4800 8/N/1   1200 7/E/1    600 7/E/1  19200 7/E/1  38400 8/N/1

### The Pico side of the link is healthy

Reading GP13 (scale RX) as a GPIO with the RP2040's internal pull-down
engaged distinguishes "actively driven" from "floating":

| pin | role | pulldown reads high | pullup reads high |
|---|---|---|---|
| GP13 | scale RX from the RS-232 module | 50/50 | 50/50 |
| GP5 | Tic RX (known-good reference) | 50/50 | 50/50 |
| GP22 | unconnected control | 0/50 | 50/50 |
| GP21 | unconnected control | 0/50 | 50/50 |

GP13 is held high against the internal pull-down exactly like the
known-driven GP5, so the SP3232 transceiver is powered and driving the
Pico's RX line to idle mark.  The module's status LEDs are lit in
`frames/2026-08-19b_rs232-module-leds.png`, which agrees.

**This does not prove the balance is connected.**  An SP3232 receiver
whose RS-232 input is floating also outputs idle mark, so "module
powered" and "DB9 unplugged" look identical from the Pico.  What it does
rule out is a dead module, a dead Pico UART pin, or a missing 3V3 jumper.

### Where the fault must therefore be

Downstream of the transceiver: the DB9 / RS-232 cable to the balance, the
channel jumper, or the balance's own serial output.  `config.py` notes
that the Waveshare Pico-2CH-RS232 board carries **two** channels and only
the chosen one is jumpered out to GP12/GP13 -- a plausible casualty of the
move.

Bench checks, cheapest first:

1. Is the DB9 seated at *both* ends (balance RS-232 port and module)?
2. Is the jumpered channel still the channel the DB9 is plugged into?
3. Are the four TTL jumpers (TXD/RXD/3V3/GND) still seated on the module?
4. Balance function settings: `Sif` should be `bPS=5` (19200) / `btPr=2`
   (8/N) to match `config.py`, data format A&D standard, terminator CR LF.
   If it was factory-reset it will be at 2400/7/E/1 -- but the probe
   already covers that, so a settings drift alone cannot explain silence
   at every rate.
5. Press `PRINT` on the balance while a passive listen is running; if
   nothing arrives, the balance is not transmitting at all.

The bench camera cannot settle this: the balance LCD is viewed
off-axis through the fume-hood sash and reads as a uniform dark
rectangle whether or not it is lit (it looked identical in the 09:23
frame when the balance was confirmed off and in the 10:04 frame after it
was switched on).  Do not use the camera to judge balance power state.

**No battery run should start until the balance reads.**  It is the
measurement instrument for every block, and the re-levelling cannot be
verified remotely until then either.

## Tilt: working, and the 0 deg pose is now correct

Commanded tilt 0 -> 45 -> 90 -> 0 (plate 0 / 22.5 / 45 deg, 2:1 horn
gearing), holding 30 s at each, with frames pulled from the stream DVR:

| commanded | frame |
|---|---|
| 0 deg | `frames/2026-08-19b_tilt-000.png` (10:11:53) |
| 45 deg | `frames/2026-08-19b_tilt-045.png` (10:12:23) |
| 90 deg | `frames/2026-08-19b_tilt-090.png` (10:12:53) |
| parked 0 deg | `frames/2026-08-19b_tilt-000-parked.png` (10:13:45) |

The earlier check reported the plate reaching all three angles, which was
wrong about 0 deg: `frames/2026-08-19a_tilt-000-collar-caught.png` shows
the plate propped up at an angle rather than flat, which is the tap
collar fouling that @swcharles found.  The plate now sits flat on the
baseplate at 0 deg.  Lesson for this doc's checklist: at 0 deg, check the
plate is *flat against the baseplate*, not merely "less tilted than 45".

No auger was loaded (visible in every frame), so nothing could dispense.

## Livestream

Live: `rJcqtYHWhGM`, "powder doser stream picam-d1pr, 2026-08-19 UTC
15:16".  It started at 15:16 UTC rather than on the usual 03:00 / 11:00 /
19:00 rollover because the camera was re-plugged during the move, so it
is not where the rollover schedule would put it -- that is why it was
hard to find from the channel page.  The live edge is now real time to
within ~10 s (measured: live-edge frame stamped 10:09:57 fetched at
16:09:49-16:10:08 UTC), so DVR offsets no longer need the ~150 s padding
the young broadcast wanted earlier.

The formats on this broadcast are itags 91-95 (portrait, 720x1280 at
itag 95).  `scripts/bench_frame.py` defaults to itag 96, which does not
exist here and fails with "no manifest" -- pass `--itag 95`.

## State left

Stepper untouched and de-energised, solenoid untouched, plate parked at
tilt 0 deg, no tmux session or capture process started, temp scripts
removed from the Pi, nothing installed on it.
