# Baseplate and auger on the H2D, black PLA (2026-11-13): sent at 06:25:24 UTC

[Joshua at 06:08 UTC](https://github.com/vertical-cloud-lab/powder-doser/pull/200#issuecomment-6845617257), with
`@claude-print`: "re-run last ping. Print immediatly. Note the nozzles have been replaced." The
last ping was [his 04:39 request](https://github.com/vertical-cloud-lab/powder-doser/pull/200#issuecomment-6844173130):
print what was left of Clayton's list on the H2D in black PLA, without the stand brackets or wood
legs. The [04:39 run](https://github.com/vertical-cloud-lab/powder-doser/actions/runs/43366921258)
had sliced the baseplate and the auger onto one plate
([`../2026-11-13-h2d-doser-parts/`](../2026-11-13-h2d-doser-parts/)) and held the Send because
the H2D's right nozzle still read 0.6 mm. It, and the run watching the A1 mini, were cancelled at
06:07 UTC.

**Outcome:** the right nozzle was set to 0.4 mm on the printer at 06:18–06:19 UTC, while this
run was posting its first frame. Both nozzles then read 0.4 mm, the plate was empty, nobody
replied, and the plate was sent at 06:25:24 UTC. See [Progress](#progress) for how it went.

## The first frame, 06:16:36 UTC

![H2D, Printer Preview still at 06:16:36 UTC](h2d-frame-20261113T061636Z.png)

- Committed and posted at the top of the tracking comment at 06:18:56 UTC, before any other prep.
- *BYU VCL H2D - Théoden*, online and idle. The last job, *aurora_camera_mounts_zero_hq_H2D*,
  showed 100 %, layer 556/556, *Finished*. Left nozzle 28 °C, right nozzle 30 °C with a 30 °C
  target, bed 25 °C, chamber 27 °C ([Device page](device-page-h2d-20261113T061636Z.png)).
- HMS: only *"Please clean and lubricate the X-axis linear rail, YZ-axis linear rods, and the
  extruder lift linear rail."* ([HMS tab](hms-20261113T061814Z.png)). No faults.
- AMS 2 Pro (left nozzle): A1 empty, A2 black PLA, A3 white PLA, A4 light-blue PLA. AMS HT (right
  nozzle) empty; external spool unknown.
- **Read of the plate: empty.** Mean luma 83/255 (with the letterbox bars). The textured PEI plate
  with its printed logo outline, and the toolhead at the top right. The blue part past the bed's
  back edge is outside the chamber.

## The nozzles

| UTC | Left | Right |
|---|---|---|
| 06:17:43 ([dialog](printer-parts-20261113T061743Z.png)) | 0.4 mm hardened steel, standard flow | **0.6 mm hardened steel, TPU high flow** |
| 06:19:58 ([dialog](printer-parts-20261113T061958Z.png)) | 0.4 mm hardened steel, standard flow | **0.4 mm hardened steel, standard flow** |
| 06:24:00 ([dialog](printer-parts-20261113T062400Z.png)) | 0.4 mm hardened steel, standard flow | 0.4 mm hardened steel, standard flow |

- Read from Studio's *Printer Parts* dialog, which shows what the printer reports. *Refresh* was
  never pressed.
- The 06:17:43 read held the Send under CLAUDE.md (every installed nozzle must be 0.2 or 0.4 mm),
  and the tracking comment said so at 06:18:56. Someone at the printer set the right hotend to
  0.4 mm standard flow before 06:19:58. The 0.6 mm TPU high-flow reading had been there since at
  least 11-04.
- The slice is for the left nozzle only (`filament_map = 1`, `nozzle_diameter = 0.4,0.4`). Its
  `nozzle_volume_type` is `Standard,TPU High Flow`, from when it was sliced, but the right nozzle
  isn't used, and the Send dialog raised no mismatch.

## The wait and the Send

- **06:20:50, a second frame** ([live view](h2d-live-20261113T062050Z.png),
  [Device page](device-page-h2d-20261113T062050Z.png)), posted at 06:21:32. The bed was lower and
  the toolhead had moved since 06:16:36, and a hand showed at the bottom right, past the bed's
  edge. The plate was still empty. The run treated it as a new frame and waited 90 s from 06:21:32,
  to 06:23:02.
- **06:22:16, the file opened in Studio:** *Slice ok*, 5 h 26 min, 160.71 g, the filament on the
  left nozzle. Not re-sliced: the plate G-code is the committed file's (MD5
  `744a58793916bd43ce7dbd456284821f`).
- **06:22:46, Send dialog** set up, then closed to take the last frame from the Device page.
- **06:23:55 and 06:24:22, final frames:** plate empty, the two identical (MAE 0.04/255), so
  nothing was moving.

![H2D at 06:24:22 UTC, just before Send](h2d-live-20261113T062422Z.png)

- **06:24:33, Send dialog again** ([screenshot](send-dialog-20261113T062456Z.png)):
  - *BYU VCL H2D - Théoden*, "Bambu Lab H2D 0.4/0.4mm", PEI plate;
  - left nozzle: PLA from **A2** (black). The dialog defaulted to A3 (white PLA) both times;
  - timelapse **off**, auto bed levelling **on**, flow dynamics calibration **on**, nozzle offset
    calibration **off** (the default; one nozzle prints).
- **06:25:24, Send,** after a last thread check: no comment from anyone but the bots since the
  06:08 request. Studio uploaded it ("Sending print job with LAN acceleration") and showed it on
  the printer by 06:25:49: layer 0/1250, finish estimated at 11:50
  ([Device page](device-page-h2d-sent-20261113T062601Z.png)).

## Progress

| UTC | |
|---|---|
| 06:25:24 | Send |
| 06:27–06:37 | Heating, homing, calibration |
| 06:37:17 | Layer 1 (881 s in the slice: the baseplate's whole footprint) |
| 06:52:54 | Layer 2, 6 % ([Device page](device-page-h2d-layer2-20261113T065254Z.png)) |
| 07:37:37 | Layer 22, 19 % |
| 07:46–08:00 | Layer 26, the slab's first top-surface layer (14 min, as in the slice) |
| 08:23:18 | Layer 30, 32 % |
| 09:10:16 | Layer 143, 46 %, finish estimate 12:03 |
| 09:31:21 | Layer 204, 53 % |

![The start, 06:27 to 06:52 UTC](watch/start-montage-0627-0652.jpg)

*06:27, 06:31, 06:35 (top); 06:37, 06:44, 06:52 (bottom).*

- The watcher ([`monitor.jsonl`](watch/monitor.jsonl)) read the Device page every 10 s by OCR,
  saved camera frames, and polled the thread every minute. Selected frames are in
  [`watch/`](watch/).
- No HMS fault, dialog or reply during the print.

## The A1 mini's plate (read only)

The gears-flat plate on the A1 mini
([`../2026-11-13-a1mini-doser-parts-gears-flat/`](../2026-11-13-a1mini-doser-parts-gears-flat/README.md))
was sent at 04:31:39 UTC by run [43364415428](https://github.com/vertical-cloud-lab/powder-doser/actions/runs/43364415428),
which was cancelled at 06:07:48 while watching it. This run looked in on it, read only:

| UTC | |
|---|---|
| 06:16:19 | 32 %, nozzle 219/220 °C, bed 64/65 °C ([Device page](a1mini-device-page-20261113T061619Z.png)) |
| 07:39:25 | Layer 189/541, 62 % ([Device page](a1mini-device-page-20261113T073925Z.png)) |
| 09:09:46 | Layer 498/541, 94 %, finish estimate 09:26 ([Device page](a1mini-device-page-20261113T090946Z.png)) |
| 09:32:07 | **100 %, layer 541/541, *Finished*,** cooling, no HMS alert ([Device page](a1mini-device-page-20261113T093207Z.png)) |

Its camera, which had given no picture since 11-12, played at 09:32:29:

![A1 mini camera at 09:32:29 UTC](a1mini-cam-finished-20261113T093229Z.jpg)

The tap collar, the two C-clips and the three pinions are on the plate, flat and whole, with no
spaghetti. The mounting plate is at the left edge, partly out of frame. The red box and the room
are outside the printer. Nobody has checked the parts off the plate yet.
