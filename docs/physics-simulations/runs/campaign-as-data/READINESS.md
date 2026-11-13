# Before the first campaign session: what is ready and what isn't (13 Nov 2026)

William asked on #196 (13 Nov 2026) what has to be done before the session in [`PLAN.md`](PLAN.md) can run.
This note checks the plan against these sources:
* the campaign code and firmware on PR #166's branch (`d14a50d`);
* the fingerprint firmware on Sam's #116 branch (`f754450`);
* the paper outline (`ec30713`, §4.A);
* the run notes of the last salt campaign;
* a read-only look at the doser Pi on 13 Nov. Nothing on the Pi or the Pico was changed or opened.

## In short
* **The rig works and is free.**
  * The Pi Zero has been up for 3 weeks, the Pico is on USB, and nothing was running.
  * It was last used on 20 Oct, to dose Al 4047 into the atomizer cups (#186).
  * The campaign firmware and the Zero's checkout (`306bbee`) haven't changed since 15 Oct.
* **A salt pilot (PLAN §5, step 1) needs no new hardware except a humidity and temperature sensor.** It does need:
  * a bench reset;
  * two firmware timing fixes;
  * one script that runs the fingerprint and the campaign in the same session;
  * a few logging fields;
  * a handful of decisions. They fix the session's design for every later powder, so they have to be made before
    the first one.
* **The #205 tests aren't needed for the pilot.** The pilot asks one question: do campaign rates match a
  fingerprint taken in the same session? That needs only the doser. The #205 fixtures, of which none is built yet,
  are what gate sessions on the other powders.
* **Sessions on other powders also need these:**
  * enough powder in hand;
  * one auger per powder, or a cleaning rule;
  * the metal-powder handling rules;
  * a rig that stays the same for the whole series.

## 1. Where things stand (13 Nov)

| Part | State | Source |
|---|---|---|
| Campaign loop, executor and report (`opt_campaign.py`, `opt_dose_capture.py`, `opt_report.py`) | Work. Used for three salt campaign sessions and for production doses. They exist only on PR #166's branch, not on `main` | #166 at `d14a50d` |
| Campaign firmware (`/trickle_tap` on the Pico, id `trickle_tap/2026-10-15`) | Works, with the 15 Oct `MemoryError` fix. Bulk revolutions are still timed with a 1 s clock | [`main_three_phase.py` L1102](https://github.com/vertical-cloud-lab/powder-doser/blob/d14a50d/hardware/test-module/firmware/trickle_tap/main_three_phase.py#L1102) |
| Fingerprint firmware (`powder_battery.py`, blocks A–H, at the Pico's root) and its capture script (`scripts/powder_battery_capture.py`) | Only on Sam's #116 branch. The Zero's checkout is the #166 branch, sparse (`scripts/` only), so the capture script isn't on it. Block D still times its spin by counting poll intervals | [`powder_battery.py` L781–783](https://github.com/vertical-cloud-lab/powder-doser/blob/f754450/hardware/test-module/firmware/powder_battery.py#L781-L783) |
| The last salt campaign, `salt-margin-20261013T191339Z` | `paused`, not finished. On 15 Oct the feed fell from 35 to 7.5 mg/s, so the hopper was probably empty or caked. Four doses may need voiding, and there is no void command | [`run_20261015.md`](https://github.com/vertical-cloud-lab/powder-doser/blob/d14a50d/data/opt/salt-margin-20261013T191339Z/run_20261015.md) |
| Rig | Last used 20 Oct for the atomizer cups (Al 4047, #186). Plate at 0°, Pico back at its power-on `main.py`, and the rig notice says the rig is free | Pi, read-only |
| Temperature and RH | No sensor. The Zero has no I²C sensor bus enabled and no USB sensor; the Pico is the only USB device | Pi, read-only |
| Balance | Between October sessions the pan drifted to −24.7 g against its zero, and needed a serial `Z`. It has been noisier since the August move into the fume hood. The firmware assumes a 0.7 s lag; drop tests give 0.16 s | `run_20261013.md`; base paper; `OUTLINE.md` §4.A9 |
| Taps | At the 15° tap tilt, the median release per tap fell from 1.2–1.7 mg (29 Sep, 6 Oct) to 0.26–0.33 mg (13 and 15 Oct) | [`run_20261015.md`](https://github.com/vertical-cloud-lab/powder-doser/blob/d14a50d/data/opt/salt-margin-20261013T191339Z/run_20261015.md) |
| #205 fixtures | Concept designs only | #205 |

## 2. Before the salt pilot

### 2.1 Code

| # | Change | Why | Where |
|---|---|---|---|
| C1 | Time the bulk spin with `ticks_ms`. Bump `FIRMWARE_ID` in `opt_common.py` with it, rerun the simulation tests, upload to `/trickle_tap` and check the sha256 | Each dose's mg/rev is off by a median 8 %, and by up to 25 % (run 34) | `main_three_phase.py` L1102 (`_now` is `time.time()`, whole seconds) |
| C2 | Protocol D: loop on the elapsed `ticks_diff`, not on `waited_ms += poll` | In August the auger turned 15–54 % further than commanded. The pilot's speed-exponent check needs protocol D right | `powder_battery.py` L781–783 |
| C3 | One session runner on the laptop. It runs blocks A, C, D and E, then the screen, the BO and validation, then the closing protocol C and the salt reference. It stamps one `session_id` on every record, and hands the Pico's port between the battery capture and the executor | Today these are two firmware builds and two capture scripts on two branches. The battery capture takes no port lock (campaign-setup §5.1, item 6) | new; also bring both branches' scripts into the Zero's checkout |
| C4 | Fields on every dose and fingerprint record: `session_id`, `jar_id` and lot, `auger_id`, the hopper fill at the start and at every cup return, temperature and RH, and the `tau_bal` used | PLAN §3 | campaign document and prompts in `opt_campaign.py` |
| C5 | A hopper limit: pause, or prompt, before the hopper falls below its working fill (fill at the start minus powder in the cup) | On 15 Oct an empty hopper looked like a jam to the unattended loop. Four doses were spoiled and the campaign stopped | `opt_campaign.py` limits (§5.5) |
| C6 | Retry a missing telemetry pull | 2 of the 60 salt doses had none | `opt_dose_capture.py` |
| C7 | Optional for the pilot: record the lip state at the tap hand-over | Tap release depends on it | firmware stop event |

The dose-range block (0.05, 0.5 and 5 g) needs no new code. `dose.py --target-g 0.05`, and the same with `5`, doses
the validated profile at other targets and logs those doses as production doses. Only the session id needs adding.

Before the first real session, run the whole session against the virtual plant (`--simulate`). That checks the
runner without powder.

### 2.2 Bench (about half a day)
1. **Auger.** Take off the auger used for the atomizer cups, mount the salt auger and record which one it is
   (`auger_id`). Clean the outlet, and check the salt for caking.
2. **Exit.** Measure the as-printed exit bore and the core-tip gap (`OUTLINE.md` §4.A1). In the DEM, moving the tip
   by 1 mm doubles delivery.
3. **Balance.**
   * Empty the cup, then zero the balance with the empty cup on the pan; use a serial `Z` if it reads below zero.
   * Check it with a calibration weight.
   * Run protocol A for the noise floor.
4. **Drawdown test (about 30 min).** At one fixed setting, for example 22.5° and 30 rpm, dose salt until the feed
   drops, logging the mass left in the hopper (`OUTLINE.md` §4.A10). This gives the hopper's working fill, which
   sets PLAN step 2's fixed mass and C5's limit. The 15 Oct collapse shows what happens below it.
5. **Temperature and RH sensor.** Wire an SHT4x or BME280 breakout to the Zero's I²C, or use a USB logger, for
   roughly $10–30. Failing that, put a standalone logger next to the doser and type its reading in at each prompt.
6. **Tapper.** Confirm the solenoid and its voltage (`OUTLINE.md` §4.A1). Decide whether the new tap collar (#203)
   goes on before the series. Tap release fell about fivefold in October, and protocol E and every dose's endgame
   depend on the tapper.

### 2.3 Decisions
These fix the session for every powder after the pilot, so they are hard to change later.

| # | Decision | Options and facts |
|---|---|---|
| D1 | Controller variant and screen | The 8-knob three-stage variant (16 corners, 29 Sep) or the 9-knob margin variant (32 corners, 13 Oct). PLAN's 22-dose screen assumes 8 knobs |
| D2 | The box | The salt BO pushed against the 40° and 100 rpm edges. Should it be widened (for example to 45°, the fingerprint's top tilt) before it is frozen for all powders? |
| D3 | Fill mass and cup returns | Fill mass from the drawdown test. Returning the cup every 10 doses needs a person at the rig every 20–30 min; `--unattended` never empties the cup |
| D4 | Attended or unattended, and run from where | A CI job is capped at 180 min, so from CI a 5–6 h session is split over two or three jobs with `--resume`. The other option is a laptop at the bench |
| D5 | Screen target | 0.5 g for every powder, or scaled by bulk density (PLAN §8) |
| D6 | The paused margin campaign | Close it. Void `bo-013`, `bo-015`, `bo-017` and `bo-018` if they were starved doses |
| D7 | Balance lag τ<sub>bal</sub> | 0.7 s (datasheet) or 0.16 s (drop tests) (`OUTLINE.md` §4.A9). Afterflow τ includes it |

### 2.4 People and rig time
* One rig day. Someone at the bench for the first hour (bench reset, fingerprint prompts) and at each cup return.
* Agree a handover with the rig's other users (the atomizer dosing in #186 has used it since the last campaign).
  Leave a `RIG-NOTICE` on the Zero while the session owns the rig.

## 3. Before sessions on other powders
* **The #205 tier-1 tests:** heap angle of repose, bulk and tapped density, the tilting plate and size distribution
  from images. Each needs CAD, printing, a Pi script and a check against bought kit (#205's next steps 2–4). Until
  they exist, the bought ring stand, density cylinders and Hall/Carney kit can stand in.
* **Powder:** at least 50 g per jar for a full session (priming takes 30–40 g, `OUTLINE.md` §4.A11). The four
  §4.A3 campaign powders must be in hand: AlSi10Mg, 316L, sieved Al 4047 and one precursor. Sieves are on order
  (byu-vcl#262).
* **Augers:** one per powder, as in Sam's battery, or a written cleaning rule. Record the `auger_id` either way.
* **Metal powders:** the fume-hood handling rules (#141). The balance is noisier there (#157), so check protocol A
  before each session.
* **A frozen rig.** New prints (#197, #200), the tap collar (#203) and the multi-auger design (#204) are in
  progress. A series of sessions has to run on one configuration, or repeat the salt reference after every change.

## 4. Can wait until after the pilot
* Generalize `extract.py` into the jar-session and dose tables (PLAN §4).
* The multi-task BO code and the DEM emulator.
* Merging #166 into `main`. Sessions can run from a pinned commit in the meantime.

## 5. Suggested order
1. Decisions D1–D7, in one meeting.
2. Code C1–C6, then one whole session against the virtual plant.
3. Bench reset and drawdown test (about half a day).
4. The salt pilot session.
5. Meanwhile, build #205's tier 1 and get the powders.
