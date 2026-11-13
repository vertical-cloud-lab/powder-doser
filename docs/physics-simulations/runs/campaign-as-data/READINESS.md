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
  * It was last used on 20 Oct, to dose Al 4047 into the atomizer cups (#186). By 21 Oct the auger tube was off
    the rig.
  * The campaign firmware and the Zero's checkout (`306bbee`) haven't changed since 15 Oct.
  * It is still the only working doser. None of the planned hardware changes (#202, #203, #204) has reached it.
* **A salt pilot (PLAN §5, step 1) needs only two purchases:** a humidity and temperature sensor, and a
  calibration weight for the balance. It does need:
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
| Campaign loop, executor and report (`opt_campaign.py`, `opt_dose_capture.py`, `opt_report.py`) | Work. Used for two salt campaigns (four sessions, 29 Sep to 15 Oct) and for production doses. They exist only on PR #166's branch, not on `main` | #166 at `d14a50d` |
| Campaign firmware (`/trickle_tap` on the Pico, id `trickle_tap/2026-10-15`) | Works, with the 15 Oct `MemoryError` fix. Bulk revolutions are still timed with a 1 s clock | [`main_three_phase.py` L1102](https://github.com/vertical-cloud-lab/powder-doser/blob/d14a50d/hardware/test-module/firmware/trickle_tap/main_three_phase.py#L1102) |
| Fingerprint firmware (`powder_battery.py`, blocks A–H, at the Pico's root) and its capture script (`scripts/powder_battery_capture.py`) | Only on Sam's #116 branch. The Zero's checkout is the #166 branch, sparse (`scripts/` only), so the capture script isn't on it. Block D still times its spin by counting poll intervals | [`powder_battery.py` L781–783](https://github.com/vertical-cloud-lab/powder-doser/blob/f754450/hardware/test-module/firmware/powder_battery.py#L781-L783) |
| The last salt campaign, `salt-margin-20261013T191339Z` | `paused`, not finished. On 15 Oct the feed fell from 35 to 7.5 mg/s, so the hopper was probably empty or caked. Four doses may need voiding, and there is no void command | [`run_20261015.md`](https://github.com/vertical-cloud-lab/powder-doser/blob/d14a50d/data/opt/salt-margin-20261013T191339Z/run_20261015.md) |
| Rig | Last used 20 Oct for the atomizer cups (Al 4047, #186). Plate at 0°, Pico back at its power-on `main.py`, and the rig notice says the rig is free. A stream frame from 21 Oct shows the auger tube off the rig, on the bench. It is still the only working doser: the 25 new dosers (#181) are being assembled and have two balances between them | Pi, read-only; [#186, 21 Oct](https://github.com/vertical-cloud-lab/powder-doser/issues/186#issuecomment-6305840509); [#181](https://github.com/vertical-cloud-lab/powder-doser/pull/181#issuecomment-6376552823) |
| Planned hardware changes | None has reached this rig. The new tap bracket (#203) is in Onshape but not printed. The multi-auger design (#204) exists only as renders. A linear actuator (#202) was recommended but not ordered. The 12–13 Nov prints (#200) are parts for the new dosers | [#203](https://github.com/vertical-cloud-lab/powder-doser/issues/203#issuecomment-6714762206), [#204](https://github.com/vertical-cloud-lab/powder-doser/issues/204#issuecomment-6838113787), [#202](https://github.com/vertical-cloud-lab/powder-doser/issues/202#issuecomment-6624329180) |
| Camera | On a separate camera Pi. On 20 Oct it froze for nearly 6 h during Wi-Fi drops. During an unattended run it is the only way to look at the plate | [#186](https://github.com/vertical-cloud-lab/powder-doser/issues/186#issuecomment-6305840509) |
| Temperature and RH | No sensor, and no code that reads one. The Pico is the only USB device on the Zero, and the header's I²C bus (`i2c-1`) isn't enabled. #210 uses outdoor readings from the Provo airport instead | Pi, read-only; code search on `main`, #166 and #116; [#210](https://github.com/vertical-cloud-lab/powder-doser/issues/210#issuecomment-6812206767) |
| Balance | On 13 Oct the pan read −24.7 g. Its zero still included powder that had since been emptied from the cup, and the balance ignores a tare below zero, so it needed a serial `Z`. The drift seen in the fume hood in August and September came from powder under a misaligned dust plate, and was fixed on 15 Sep. A check with a calibration weight was still owed then, because there was no weight in its box, and none is recorded since. The firmware assumes a 0.7 s lag; drop tests give 0.16 s | `run_20261013.md`; base paper; [#157](https://github.com/vertical-cloud-lab/powder-doser/issues/157#issuecomment-5685921132); `OUTLINE.md` §4.A9 |
| Taps | At the 15° tap tilt, the median release per tap fell from 1.2–1.7 mg (29 Sep, 6 Oct) to 0.26–0.33 mg (13 and 15 Oct). The cause was never found; the 15 Oct advice was to check the tube's lip and the hopper | [`run_20261015.md`](https://github.com/vertical-cloud-lab/powder-doser/blob/d14a50d/data/opt/salt-margin-20261013T191339Z/run_20261015.md) |
| #205 fixtures | Concept designs, plus a dimensioned drawing of the standard auger (13 Nov) for fixtures that take its place. Nothing printed or built yet. On 10 Nov William asked Sterling which tests to build first; no answer yet | #205 at `626da9b` |

## 2. Before the salt pilot

### 2.1 Code

| # | Change | Why | Where |
|---|---|---|---|
| C1 | Time the bulk spin with `ticks_ms`. Bump `FIRMWARE_ID` in `opt_common.py` with it, rerun the simulation tests, upload to `/trickle_tap` and check the sha256 | Each dose's mg/rev is off by a median 8 %, and by up to 25 % (run 34) | `main_three_phase.py` L1102 (`_now` is `time.time()`, whole seconds) |
| C2 | Protocol D: loop on the elapsed `ticks_diff`, not on `waited_ms += poll` | In August the auger turned 15–54 % further than commanded; #210 counted about 4.6 revolutions logged as 3. The pilot's speed-exponent check needs protocol D right | `powder_battery.py` L781–783 |
| C3 | One session runner on the laptop. It runs blocks A, C, D and E, then the screen, the BO and validation, then the closing protocol C and the salt reference. It stamps one `session_id` on every record, and hands the Pico's port between the battery capture and the executor | Today these are two firmware builds and two capture scripts on two branches. The battery capture takes no port lock (campaign-setup §5.1, item 6) | new; also bring both branches' scripts into the Zero's checkout |
| C4 | Fields on every dose and fingerprint record: `session_id`, `jar_id` and lot, `auger_id`, the hopper fill at the start and at every cup return, temperature and RH, and the `tau_bal` used | PLAN §3. The cup-return prompt already exists (`--cup-every`), but it only counts returns; it doesn't ask what the hopper holds | campaign document and prompts in `opt_campaign.py` |
| C5 | A hopper limit: pause, or prompt, before the hopper falls below its working fill (fill at the start minus powder in the cup) | On 15 Oct an empty hopper looked like a jam to the unattended loop. Four doses were spoiled and the campaign stopped | `opt_campaign.py` limits (§5.5) |
| C6 | Retry a missing telemetry pull, and upload every balance reading to MongoDB | 2 of the 60 salt doses had none. #210 (data assimilation) needs continuous readings at several tilts, and its `scale_raw` stream is empty | `opt_dose_capture.py` |
| C7 | Optional for the pilot: record the lip state at the tap hand-over | Tap release depends on it | firmware stop event |

The dose-range block (0.05, 0.5 and 5 g) needs no new code. `dose.py --target-g 0.05`, and the same with `5`, doses
the validated profile at other targets and logs those doses as production doses. Only the session id needs adding.

Before the first real session, dry-run the session runner without powder. The campaign half has a virtual plant
(`opt_campaign.py --simulate`), and the battery has its own simulation tests (`sim/test_powder_battery.py`).

### 2.2 Bench (about half a day)
1. **Auger.** On 21 Oct the auger tube was off the rig. Mount the salt auger and record which one it is
   (`auger_id`). Clean the outlet, and check the salt for caking. Then run the battery's one-minute feed check
   (`battery_preflight.py`), which tells a feeding auger from a blocked or empty one.
2. **Exit.** Measure the as-printed exit bore and the core-tip gap (`OUTLINE.md` §4.A1). In the DEM, moving the tip
   by 1 mm doubles delivery.
3. **Balance.**
   * Empty the cup, then zero the balance with the empty cup on the pan; use a serial `Z` if it reads below zero.
   * Check it with a calibration weight. One has to be bought or borrowed first (#157).
   * Run protocol A for the noise floor.
4. **Drawdown test (about 30 min).** At one fixed setting, for example 22.5° and 30 rpm, dose salt until the feed
   drops, logging the mass left in the hopper (`OUTLINE.md` §4.A10). This gives the hopper's working fill, which
   sets PLAN step 2's fixed mass and C5's limit. The 15 Oct collapse shows what happens below it.
5. **Temperature and RH sensor.** Wire an SHT4x or BME280 breakout to the Zero's I²C, or use a USB logger, for
   roughly $10–30. Failing that, put a standalone logger next to the doser and type its reading in at each prompt.
6. **Tapper.** Confirm the solenoid (an Adafruit 412) and its 12 V supply (`OUTLINE.md` §4.A1), and look at the
   tube's lip. Decide whether the new tap bracket (#203) goes on before the series. Tap release fell about
   fivefold in October, and protocol E and every dose's endgame depend on the tapper.

### 2.3 Decisions
These fix the session for every powder after the pilot, so they are hard to change later.

| # | Decision | Options and facts |
|---|---|---|
| D1 | Controller variant, which sets the screen | `three-stage`: 8 knobs; 16 corners, 4 centres and 2 baselines, the 22 doses PLAN assumes. `three-stage-margin`: 9 knobs; a powder with no three-stage campaign of its own gets 32 corners, so 38 screen doses. `bulk-tap`: 8 knobs, no PI trickle. On salt, the margin campaign's best doses were at a 0 mg margin |
| D2 | The box | The salt BO pushed against the 40° and 100 rpm edges. Should it be widened (for example to 45°, the fingerprint's top tilt) before it is frozen for all powders? |
| D3 | Fill mass and cup returns | Fill mass from the drawdown test. Returning the cup every 10 doses needs a person at the rig every 20–30 min; `--unattended` never empties the cup |
| D4 | Attended or unattended, and run from where | A CI job is capped at 180 min, so from CI a 5–6 h session is split over two or three jobs with `--resume`. The other option is a laptop at the bench |
| D5 | Screen target | 0.5 g for every powder, or scaled by bulk density (PLAN §8) |
| D6 | The paused margin campaign | Close it. Void `bo-013`, `bo-015`, `bo-017` and `bo-018` if they were starved doses |
| D7 | Balance lag τ<sub>bal</sub> | 0.7 s (datasheet) or 0.16 s (drop tests) (`OUTLINE.md` §4.A9). Afterflow τ includes it |
| D8 | The BO's objectives | Keep time and \|error\|, as on salt, or switch now to the planned one-sided error with a P(overshoot) limit and repeatability (`OUTLINE.md` §4.B1, #162). The multi-task GP pools the sessions, so every powder's BO should use the same ones |

### 2.4 People and rig time
* One rig day. Someone at the bench for the first hour (bench reset, fingerprint prompts) and at each cup return.
* Agree a handover with the rig's other users (the atomizer dosing in #186 has used it since the last campaign).
  Leave a `RIG-NOTICE` on the Zero while the session owns the rig, and give an estimated end time (#116). Log the
  session to MongoDB (#186). Leave the doser loaded with salt and demo-ready afterwards (#144).
* The doser's Pi also relays other sessions' browser tunnels (Onshape, full texts). Agree that none runs during a
  session. The Zero also dropped off the tailnet once, on 3 Nov, so a session driven over the tailnet should expect
  to need a `--resume`.
* Coordinate with the data-assimilation project (#210). A session supplies data it lacks: continuous readings at
  several tilts, and RH and temperature at the bench.

## 3. Before sessions on other powders
* **The #205 tier-1 tests:** heap angle of repose, bulk and tapped density, the tilting plate and size distribution
  from images. Each needs CAD, printing, a Pi script and a check against bought kit (#205's next steps 2–4). Until
  they exist, the bought ring stand, density cylinders and Hall/Carney kit can stand in.
* **Powder:**
  * At least 50 g per jar for a full session: priming takes 30–40 g (`OUTLINE.md` §4.A11), and an auger holds
    about 70 mL (#117). No record says how many grams of each powder the lab has.
  * The four §4.A3 campaign powders have to be in hand. AlSi10Mg (MSE Supplies, 15–45 µm) and the in-house Al 4047
    are. Nothing shows 316L in the lab, and whether to order it is still open (#184). One precursor is still to be
    chosen.
  * Al 4047 has chunks that clog the outlet, so sieve it before loading. Sieves are on order (byu-vcl#262).
* **Augers:** one per powder, as in Sam's battery, or a written cleaning rule. Record the `auger_id` either way.
* **Metal powders:**
  * The #141 guidelines:
    * an N95 at least, a half-face P100 preferred; glasses, nitrile gloves and a cotton lab coat;
    * ground yourself before handling Al or Mg powder, and switch the doser off while loading;
    * a Class D extinguisher or dry sand nearby; no compressed air; clean up with damp wipes.

    The written version is only on an unmerged branch.
  * A hazard review for combustible fines such as Al (`OUTLINE.md` §4.A11).
  * The balance drifted in the fume hood until 15 Sep (#157), so run protocol A before each session.
* **Firmware for powders that creep:** level the tube when a dose stops. With the auger stopped at 40°, Al 4047
  crept out at 1.8 mg in 30 s (#186).
* **A frozen rig.** None of the planned changes (#202, #203, #204) is on the rig yet. Decide whether they go on before
  the series or after it. A series has to run on one configuration, or repeat the salt reference after every
  change.
* **The #205 choice.** Sterling's answer on which tests to build first (asked on 10 Nov).

## 4. Can wait until after the pilot
* Generalize `extract.py` into the jar-session and dose tables (PLAN §4).
* The multi-task BO code and the DEM emulator.
* Merging #166 into `main`. Sessions can run from a pinned commit in the meantime.

## 5. Suggested order
1. Decisions D1–D8, in one meeting.
2. Code C1–C6, then a dry run of the session runner without powder.
3. Bench reset and drawdown test (about half a day).
4. The salt pilot session.
5. Meanwhile, build #205's tier 1 and get the powders.
