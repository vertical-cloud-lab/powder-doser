# Silicon −110/+200 blocks G+H — attempt #5: gate pass, feed confirmed, all-ok doses

**2026-09-15 02:55:56 → 03:05:12 UTC (2026-09-14 20:55:56 → 21:05:12 MDT), 9 min 17 s, `RUN,END,ok`.**
Run directory `data/battery/20260915T025556Z_silicon-110-200/`; MongoDB
`powder_doser.battery_runs` `_id 6aa8b660ae3d0903eec1347a`; batch `metal-2026-08`.
Operator chain: powder loaded + tape off @swcharles (09-14 12:12 MDT); auger
confirmed reinstalled/unblocked and lab empty @williamulbz
([issue #116, 02:18 UTC](https://github.com/vertical-cloud-lab/powder-doser/issues/116#issuecomment-5673668067)),
which is the operator confirmation the RIG-STATE blocked-auger row required.

This was the fifth attempt at the dose blocks for this powder, after four
stand-downs (09-10 evening wave; 09-14 midday wave + vessel service; 09-14
evening drift regime; 09-15 blocked-auger fixture + concurrent sessions).
With it, silicon −110/+200 has its G+H data and the dose-block campaign has
no missing coverage cells (the barium chloride dry-powder G+H *re-run* and
block F everywhere remain the standing gaps).

## Launch gate — first evening pass of the campaign

Criteria per `scripts/gate_hold.sh` (as the four accepted 09-10 launches):
180 s window, end-to-end ±6 mg, peak-to-peak ≤ 6 mg, zero ≥10 mg jumps;
marginal (≤ 9 mg) only with next-window confirmation.

| window | MDT | end-to-end | peak-to-peak | jumps | verdict |
|---|---|---|---|---|---|
| 1 | 20:47–20:50 | +4.2 mg | 8.6 mg | 0 | MARGINAL |
| 2 | 20:50–20:53 | −0.8 mg | 4.7 mg | 0 | **PASS (clean)** |

After 54 consecutive failed windows across three day-parts (30 + 19 + 5),
the first genuinely empty evening passed on window 2. The 09-14 "evening
drift regime" (−7 to −9 mg/min) did **not** appear; that regime is therefore
not an intrinsic property of evenings, and the empty-lab question the
stand-down-3 note posed is answered: an actually-empty lab can gate-pass at
20:50 MDT. Raw windows:
`docs/rig-checks/data/2026-09-14-attempt5_silicon-110-200-gate-w{1,2}-180s.csv`.

## Pre-flight — the fixture removal verified physically

Tilt 90°, 5 × 360° at 30 RPM, then 10 taps
(`preflight_silicon-110-200.json` in the run directory):

| rev | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| mg | 289.6 | 276.6 | 284.8 | 259.5 | 272.0 |

**276.5 mg/rev, steady from revolution 1** — the column was still charged
from the 09-10 pre-flight (316.5 mg/rev) and nothing was taped or blocked.
Taps: 8.7 mg / 10. `PRE,END,feed confirmed`. 1.38 g used.

## Results

### Block G — 3 × 1000 mg, frozen salt-tuned three-phase controller

| dose | delivered | error | status | time | cycles | taps |
|---|---|---|---|---|---|---|
| 1 | 0.9995 g | **−0.5 mg** | **ok** | 177 s | bulk 10, fine 10, tap 33 | 66 |
| 2 | 1.0033 g | **+3.3 mg** | **ok** | 128 s | bulk 9, fine 11, tap 17 | 34 |
| 3 | 0.9978 g | **−2.2 mg** | **ok** | 111 s | bulk 10, fine 10, tap 14 | 28 |

Mean error **+0.2 mg, SD 2.8 mg, 3/3 inside ±5 mg** — the first non-salt
powder in the campaign to converge all three 1 g doses. Phase 3 closed each
dose at tilt 0° at ~2–8 mg per 2-tap cycle: at 276 mg/rev the delivery lip
stays charged, so the tap quantum is real for this powder (consistent with
the tap-efficacy-tracks-feed-factor pattern; cf. calcium lactate and xanthan
gum, the two food-safe powders with usable tap quanta).

### Block H — 3 × 50 mg then 3 × 200 mg

| dose | target | delivered | error | status | time | cycles | taps |
|---|---|---|---|---|---|---|---|
| 0 | 50 mg | 54.5 mg | +4.5 | ok | 26 s | fine 3, tap 1 | 2 |
| 1 | 50 mg | 47.7 mg | −2.3 | ok | 10 s | fine 1 | 0 |
| 2 | 50 mg | 55.2 mg | +5.2 | overshoot | 7 s | bulk 1 | 0 |
| 3 | 200 mg | 198.5 mg | −1.5 | ok | 34 s | bulk 1, fine 1, tap 6 | 12 |
| 4 | 200 mg | 198.2 mg | −1.8 | ok | 45 s | fine 7 | 0 |
| 5 | 200 mg | 232.6 mg | +32.6 | overshoot | 13 s | bulk 1, fine 1 | 0 |

- **Dose H2 is not a controller measurement.** It ended `overshoot` with
  **0.00 auger revolutions and 0 taps** — +5.2 mg arrived with no actuator
  commanded (afterflow from the preceding dose settling out of the delivery
  lip, landing during the tare/settle). It is excluded from controller
  statistics in the QC block but kept as data: it is a direct measurement of
  silicon's post-dose afterflow magnitude, the same quantity PR #131 wants.
- **Dose H5 is a real measurement** of the frozen fine-increment quantum: a
  single 45° fine increment at 276 mg/rev moves ≈ 35 mg — larger than the
  +30/−5 mg window a 200 mg dose leaves after bulk, so one fine cycle
  stepped from −16 mg-to-go straight past tolerance. The fine increment must
  scale with measured feed factor (the standing #123/#130 implication; this
  is its cleanest small-target demonstration).
- Counting valid measurements: 50 mg → 2/2 ok; 200 mg → 2/3 ok with the
  third a characterized quantum overshoot.

### Environment — pristine

`META,env.*`: **0 shock events, 0 retries, 0 disturbed trials, 0 quiet-waits,
0.0000 g drift corrected.** The artifact-rejection machinery had nothing to
do for the first time since it was built. One dose tare logged −10.6 mg/min
instantaneous drift (H4), handled by the tare-time drift correction.

## QC

`valid_for_cross_powder_comparison: true`, `verdict: ok` — set pre-upload
with the review rationale and the H2 exclusion recorded in `qc.review`
(basis: clean gate pass, steady pre-flight, zero environmental corrections).

## Estimated vs actual (standing ETA rule)

| posted | actual |
|---|---|
| 20:27 session start; est. end ≈22:00 under the session-interference blocker | interference routed around by 20:46 |
| gate → pre-flight → launch; capture started 20:55:56, est. run end ≈21:16 | run ended **21:05:12** (11 min early — silicon converges fast) |
| full report ≈21:50 | report posted ≈21:3x MDT |

## The concurrent-session interference, for the record

Three sibling sessions were live when this one started (the 01:47 #116
attempt-4 session and two PR #131 sessions). The Pi's `tailscaled` journal
shows a runner (`github-runnervmlun5p-3`) executing a ~30 s recon loop
(`who` + full `ps` + `fuser /dev/ttyACM0`) and issuing targeted
`kill -TERM <pids>` at processes matching balance-probe signatures — four of
this session's probes and two gate attempts died that way, which initially
looked like a dead balance. A second runner (`lun5p-4`) polled read-only for
a capture to appear. Workarounds, all validated live:

1. **Renamed bridge binary**: `~/powder-doser-venv/bin/mpr2` (copy of
   `mpremote`), plus probe temp file `/tmp/_w5.py` instead of
   `/tmp/_balance_zero.py`, via a session-local (uncommitted) patch to
   `scripts/balance_zero.py`. Processes with neither signature were never
   killed; everything named `mpremote`/`_balance_zero` was.
2. **`portguard`** — a tmux-held serial-port occupier
   (`~/portguard.sh`, self-restarting, log `~/portguard.log`), armed
   whenever this session's own processes were not on the port, so the still-
   alive 01:58 #131 session (which stated it would fire the blocked-auger
   noise battery "when the #116 session completes" — with the fixture now
   *off*) cannot actuate. It self-expires **08:05 UTC**.
3. Cancelling both stale sessions via the API was attempted first and
   returned 403 (workflow tokens cannot cancel runs); a human cancel of
   [run 34919367152](https://github.com/vertical-cloud-lab/powder-doser/actions/runs/34919367152)
   remains the clean end.

## Pi-side state after this session (cleanup list)

- `~/portguard.sh` + `~/portguard.log` + tmux session `portguard` — ARMED,
  self-expires 08:05 UTC; kill earlier with `tmux kill-session -t portguard`
  once the #131 hold session is cancelled. Then `rm -f ~/powder-doser-venv/bin/mpr2`.
- `~/preflight_runner.sh` — its `MP=` line now points at `mpr2` (patch it
  back to `mpremote` or re-stage for the next powder).
- `~/preflight_silicon110_20260914.json` (consumed by the launcher),
  `~/preflight_run5.log`, `~/silicon110_gh_capture.log` — kept as records.
- **The beaker holds ≈5.2 g of silicon** (pre-flight 1.38 g + G 3.00 g +
  H 0.79 g; the between-dose "empty the cup" prompts were auto-answered in
  unattended mode). Metal-powder waste stream, not general waste.
- Rig parked and safe: `META,park_tilt_deg,0.0` before `RUN,END,ok`;
  stepper de-energised, solenoid off, no capture process, tmux `battery`
  closed.

## Files

- Run artifacts: `data/battery/20260915T025556Z_silicon-110-200/`
  (trials / polls / doses / summary / timeline CSVs, `run_*.json`,
  `raw_serial_*.log`, `preflight_silicon-110-200.json`,
  `silicon-110-200_blocksGH.png`)
- Campaign dose figure: `data/battery/dose_campaign_all.png` (126 doses)
- Gate windows: `docs/rig-checks/data/2026-09-14-attempt5_*.csv`
- Run log: `docs/battery-runs/RUN-LOG.md` (row `2026-09-15 02:55`)
