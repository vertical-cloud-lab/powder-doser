# 2026-08-20 -- end-of-day readiness check after the salt reload

Context: issue #116. After the silicon (-110/+200 mesh) battery, the operator
reloaded the auger with salt and stood the rig down for the day, asking that it
be left ready for demos.

This is a **readiness check, not a run**. Nothing was dispensed: no stepper,
servo or solenoid command was issued, and no `battery_runs` document was
created. The only write to hardware was a balance re-zero (an A&D `Z`, a
query/tare-class command that is safe with a loaded auger).

Lab clock is MDT; UTC in brackets.

## Summary

| Subsystem | State |
|---|---|
| Runner -> Pi (Tailscale) | online |
| Pi | up 1 day 7 h, root disk 10 % used, no tmux session, no capture process |
| Pi -> Pico | `/dev/ttyACM0`, `2e8a:0005 MicroPython Board in FS mode` |
| Pico firmware | all battery modules present and byte-identical to the repo |
| Pi host scripts | identical to the repo (`bench_frame.py` re-synced, see below) |
| Balance | reads normally; re-zeroed remotely from -1310.2 mg to 0.0 |
| Auger | loaded, **delivery end open**, salt visible at the lip |
| Tilt | parked at 0 deg, tube flat on the plate |
| Livestream | live, `23PlXoQgjPQ` |
| Vibration (DRV2605L) | still absent from the I2C bus (unchanged) |
| Room | settled to ~0.5-0.7 mg jitter; **fails the pre-run gate as of 16:42 MDT** |

## The delivery end is open

The single most expensive failure in this issue's history is a battery run
against a blocked outlet: the 2026-08-04 brown-rice-flour run and the
2026-08-05 carboxymethyl-cellulose attempt both burned bench time and, in the
first case, three sessions of interpretation. The operator's message this time
did not include the usual "and removed the tape", so it was worth looking.

Bench-camera frame at 16:34:41 MDT
(`frames/2026-08-20_end-of-day-salt-reloaded.png`, crop in
`frames/2026-08-20_end-of-day-delivery-end-open.png`):

* the **delivery end is open**, with granular material visible at the lip;
* the red tape visible in the wide frame is at the **rear cap end**, which is
  where the threaded storage cap lives -- that is the normal configuration and
  not the delivery-end tape;
* the tube is flat on the plate, i.e. tilt is genuinely parked at 0 deg.

This is visual evidence about the outlet only. It is **not** a feed check: only
`battery_preflight` establishes that the column actually conveys, and it
remains mandatory before a run.

## Balance

Queried directly over RS-232:

```
?TN -> TN,   HR-100A
?SN -> SN,6A7609446
?PT -> PT,+051.7388  g
Q   -> US,-001.3153  g
```

The -1.32 g was a **stale reference**, not a fault: `scale.zero()` tares
per block during a run, so the surviving reference was whatever the last
successful mid-run tare captured, and the beaker has since been emptied.

Note that the stored tare can no longer be used to reconstruct an absolute
gross mass on this balance: both `Z` (re-zero, which moves the zero point) and
`T` (tare, which sets `PT`) have been issued to it today, so `displayed + PT`
is not the vessel mass. If an absolute vessel mass is wanted, weigh the empty
beaker deliberately rather than deriving it.

`scripts/balance_zero.py` re-zeroed it remotely with the enclosure closed:

```
[balance] before re-zero: ST -1310.2 mg
[balance] sent A&D 'Z' (documented as 'Same as the RE-ZERO key')
[balance] first +0.20 mg   last +5.00 mg
```

Jitter fell across the session as the bench settled after the reload:

| lab clock | jitter | stable frames | note |
|---|---|---|---|
| 16:31 | 2.091 mg | 3 % | minutes after the auger was reloaded |
| 16:36 | 0.549 mg | 27 % | after the re-zero |
| 16:42 | 0.697 mg | 19 % | 240 s survey |
| 16:50 | 0.541 mg | 19 % | final read |

So ~0.5-0.7 mg is this room's settled floor at the end of a working day --
about 5x the 0.111 mg measured on a bare pan on a quiet morning, and the reason
the survey below still returns a fail.

Baseline creep is unchanged and remains the thing that limits block G: the
survey measured -1.8 mg/min, and the balance had walked +13.0 mg from its
re-zero eight minutes later.

## Environment survey, 16:42 MDT

`scripts/balance_environment_survey.py --settle 240`
(`data/2026-08-20_end-of-day-environment-survey-240s.csv`):

```
837 samples over 240 s, 159/837 stable (19 %)
sample-to-sample jitter 0.697 mg   -> DRAFTS
drift -1.8 mg/min over the longest quiet stretch (185 s)
1 mechanical step event(s) > 10 mg   (t=54.6 s, -11.0 mg)

      dur    median      p90    worst
       5s      5.90    10.10    15.00  BAD
      10s      7.90    12.30    15.00  BAD
      15s     10.30    14.10    16.30  BAD
      30s     12.90    15.00    19.20  BAD
      60s     14.20    16.30    21.40  BAD
     180s     20.20    23.10    23.10  BAD

VERDICT: even short trials are being disturbed.
```

This is a snapshot of a Thursday-afternoon polishing lab with somebody at the
bench, not a prediction about tomorrow morning. It is recorded so there is a
same-day comparison point, and because it is the reason the survey has to be
re-run immediately before any demo rather than trusted from the day before.

For reference, the same survey shape on runs that produced good data:

| | this check, 16:42 | silicon run, 15:41 | sodium sulfate, 13:16 |
|---|---|---|---|
| jitter | 0.697 mg | 1.59 mg | 2.12 mg |
| stable frames | 19 % | 4 % | 2 % |
| verdict | fail | fail | fail |

The verdict line has been a fail before every recent run. What matters
underneath it is the split: continuous jitter averages down inside a bracket,
whereas shocks and long-window creep do not. Both of those runs went ahead on
that reasoning and produced block C data with 4-15 % RSD.

## Software state

Pico firmware is byte-identical to the repo for every module the repo carries:

| module | bytes | sha256[:12] |
|---|---|---|
| `powder_battery.py` | 42480 | `a4b4b5eb06d1` |
| `battery_preflight.py` | 7107 | `e48c3a749bf3` |
| `battery_feed_diagnostic.py` | 7629 | `fa7185f96d15` |
| `balance_filter.py` | 15907 | `4d7a9560d48a` |
| `scale.py` | 9863 | `b5cdd5f6bf46` |

(`main_three_phase.py`, `config.py`, `servo.py`, `tic.py` and `drv2605.py` are
present on the Pico but live on other unmerged branches, so there is nothing on
this branch to compare them against.)

Host scripts on the Pi matched the repo except `bench_frame.py`, which was
still the pre-fix 9916-byte copy from before the `curl -L` / itag-fallback
repairs. It has been re-synced (11771 bytes, `50de15d125d9`). It runs on the
host rather than on the Pi, so the stale copy was a trap rather than an active
fault -- but it was a trap worth removing.

All nine test suites pass on this branch: battery sim, pre-flight, balance
filter, capture, bench-frame, run-log, and the three plotting suites.

## Before the next run

1. Empty the beaker if anything has accumulated, then leave the bench alone for
   two or three minutes. Every run this week shows the shock corrections
   clustering in the first ~2.5 minutes after the auger is handled.
2. `python scripts/balance_zero.py --check-only --settle 120` -- confirms the
   balance answers and shows the current jitter.
3. `python scripts/balance_environment_survey.py` -- the go/no-go, read the
   jitter/shock/creep split rather than only the verdict line.
4. `battery_preflight` -- the only thing that establishes the column conveys.
   Read its per-revolution list, not its average: on a freshly loaded auger the
   first revolutions are the delivery section charging, and the average
   understates the real feed factor (4.5x on silicon, 73x on CMC).
5. Then the battery. `blocks="ABCDE"` is ~15 min and is what the current
   balance behaviour supports; block G needs the 180 s survey row inside 5 mg,
   which in practice means the granite isolation.

## Still open

* **Block F (vibration)** is missing from every run in the dataset -- the
  DRV2605L is not on the I2C bus at all, so it is not wired in rather than
  failing. Needs one back-fill pass once the motor is attached.
* **Block G** is held back pending balance isolation (granite block on a
  compliant pad, with the doser platform decoupled from the balance's surface).
* **A 100 g class E2/F1 weight** is still not at the rig, so the HR-100A has not
  been calibrated since the move into the fume hood.
* **Nothing in this work is merged to `main`.** This is the 27th
  `claude/issue-116-*` branch; the battery firmware, capture script, balance
  tooling, run log and 14 battery runs (plus one aborted-preflight record) are
  all still branch-only, and every session re-pulls them by hand.
