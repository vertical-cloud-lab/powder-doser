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

## Results

**Pending** — to be filled in by the collecting session (doses, per-target
mean error, comparison against Block G's −291.5 mg and against the other
Block H powders: salt +3.5 / WRF −4.8 / xanthan +10 / CMC −12 mg per-target
means).
