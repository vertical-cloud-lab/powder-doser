# 2026-09-09 — Sodium alginate Block H (detached; results pending collection)

Small-target dosing (3 × 50 mg + 3 × 200 mg, frozen three-phase controller,
`dose_read_path=bracket`) on sodium alginate, in the EB B125 fume hood.
This is the Block H counterpart to the powder that did **worst on Block G**
(2026-08-05: mean −291.5 mg, all three 1 g doses `cycle-budget`). The
question Block H asks: do the target-scaled hand-over thresholds
(t1→target, t2→target/2) rescue a poorly-conveying powder, or does a
~4.5 mg/rev feed factor mean the fine/tap phases simply grind to timeout?

## Launch (this session)

| | |
|---|---|
| Run dir (on Pi) | `data/battery/20260909T185352Z_sodium-alginate/` |
| Launched | ~2026-09-09 18:54 UTC (12:54 MDT) |
| Mode | detached in tmux `alginate`; `--unattended`, no `--upload` |
| Blocks | H only (3 × 50 mg + 3 × 200 mg) |

### Pre-run gate — the best environment of the campaign

- **Balance check** (60 s): 100 % stable frames, sd 0.07 mg, peak-to-peak
  0.30 mg, sample-to-sample jitter 0.006 mg. Stale −2.68 g tare offset
  (bracket reads are differences, so it is subtracted as each dose's
  baseline).
- **Environment survey** (180 s): 100 % stable, jitter 0.008 mg, 0 drift,
  **0 shock events**, error 0.4–0.5 mg over any 180 s window — comfortably
  inside the ±5 mg dose band. First campaign run where the Block G/H gate
  passes with this much margin.
- **Pre-flight feed check** (5 × 360° @ 30 RPM, tilt 90°): **feed confirmed**,
  0.0227 g over 5 rev = 4.53 mg/rev, 10 taps → 0.0172 g. Consistent with the
  2026-08-05 pre-flight (3.52 mg/rev) — sodium alginate is a genuine but slow
  conveyor. Per-rev list 14.3 / 6.8 / 0 / 1.5 / 0.1 mg is the usual
  lip-dump-then-charge shape.

### Why detached

Sodium alginate delivers ~1–4 mg per fine cycle (2026-08-05), so a 50 mg
dose needs tens of fine cycles and a 200 mg dose is likely to reach the
~900 s per-dose timeout — up to ~90 min for six doses, well past the
launching job's 60-min GitHub token. Launched detached per the CLAUDE.md
liveness rule; the next `@claude` mention collects results (`--from-raw`
rebuilds everything from the flushed raw serial log if the run outlived
its tmux). Recovery note on the Pi at
`~/handoff/2026-09-09_sodium-alginate-blockh-RECOVERY.md`.

## Results (collected 2026-09-09 21:37 UTC by the next session)

The run outlived its launching job exactly as planned: `RUN,END,ok`,
`CAPTURE_EXIT=0`, **18:53:52 → 19:58:41 UTC (1 h 04 m 48 s)** — the
longest Block H of the campaign, and the duration *is* the finding.
Environment counters all zero (0 shocks, 0 retries, 0 unsettled
brackets). Uploaded as `_id 6aa1d1ab882690d556a9c132`; QC promoted
`unreviewed` → `ok`, `valid = true` (amendment in the run document).

| # | target | delivered | error | status | time | auger rev | taps | cycles |
|---|---|---|---|---|---|---|---|---|
| 0 | 50 mg | 22.2 mg | −27.8 | stalled | 561 s | 5.14 | 196 | fine:40 tap:98 |
| 1 | 50 mg | 38.7 mg | −11.3 | timeout | 902 s | 6.75 | 360 | fine:53 tap:180 |
| 2 | 50 mg | 30.3 mg | −19.7 | stalled | 405 s | 3.39 | 142 | fine:26 tap:71 |
| 3 | 200 mg | 133.3 mg | −66.7 | timeout | 905 s | 22.04 | 0 | fine:169 |
| 4 | 200 mg | 147.9 mg | −52.1 | timeout | 903 s | 17.49 | 84 | fine:139 tap:42 |
| 5 | 200 mg | 14.3 mg | −185.7 | stalled | 207 s | 4.75 | 0 | fine:38 |

Per-target: **50 mg mean −19.6 mg (−39 %), 0/3 ok · 200 mg mean
−101.5 mg (−51 %), 0/3 ok.** Total dispensed 0.387 g.

**The question the run asked is answered: no, the target-scaled
thresholds do not rescue a ~4.5 mg/rev powder.** Relative error gets
*worse* as the target shrinks toward the actuator quanta — 1 g (Block
G) −29 %, 200 mg −51 %, 50 mg −39 % — both small targets sit well
below the 1 g run's relative accuracy, and every dose ends `stalled`
or `timeout`.
The fine phase moves ~1 mg/cycle at this feed factor, so a 200 mg dose
needs more fine cycles than the ~900 s budget holds (H3 spun 22
revolutions for 133 mg — ~6 mg/rev at the fine-phase tilt, consistent
with block C), and the tap phase moves ~0.05–0.1 mg/tap (360 taps in
H1 bought ~20 mg), so it cannot close what fine hands it. Sodium
alginate stays the controller's worst case at every target.

Two caveats recorded with the promotion:

- **H5 is depletion, not a new failure mode** — it stalled at 14.3 mg
  after 207 s (vs H3/H4 grinding to the 900 s timeout) with ~0.64 g
  already dispensed through a slow conveyor; the column was running
  down by the sixth dose. The 200 mg mean is dominated by it; H3/H4's
  −52 to −67 mg is the better estimate of steady-state behaviour.
- The 50 mg point is nominally inside the old room's environmental
  uncertainty argument, but this run's survey (0.4 mg over 180 s, 0
  shocks) means the EB B125 hood does support it: the errors here are
  20–50× the environmental floor, so they are the powder, not the room.

Cross-powder Block H per-target means so far (mg): salt +2.8 / +4.2,
WRF −4.9 / −4.7, xanthan +2.9 / +17.8, CMC −22.6 / −2.2, **sodium
alginate −101.5 / −19.6** (each pair 200 mg / 50 mg). Alginate is an
order of magnitude off the rest of the set — same ranking Block G gave.
