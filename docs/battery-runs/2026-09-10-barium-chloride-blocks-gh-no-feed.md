# 2026-09-10 — barium chloride blocks G+H: no feed, column arched

| | |
|---|---|
| Run dir | `data/battery/20260910T170858Z_barium-chloride/` |
| Window | 2026-09-10 **17:08:58 → 17:13:32 UTC** (11:08:58 → 11:13:32 MDT), 4 min 34 s (G 51 s · H 3:40) |
| Blocks | `GH` attempted (3 × 1 g + 3 × 50 mg + 3 × 200 mg), detached in tmux `bacl2`, `--unattended`, bracket read path |
| Batch / operator | `inorganic-2026-08` / swcharles |
| Mongo `_id` | `6aa2e65c2728f704c77c9274` |
| QC | **`valid_for_cross_powder_comparison = false`**, `verdict = arching-no-feed` (amended post-run, diagnostic evidence attached) |
| Prior data | Valid A–E run [2026-08-21](2026-08-21-barium-chloride.md): 190.8 mg/rev @45° steady state, tap quantum 2.13 mg @45° / <0.2 mg @0° |

Intended as the G+H completion of barium chloride's block parity (missing
only F), per the 2026-09-10 operator directive. It is instead a recorded
**material-state fault**: the powder arched over the auger intake and the
dose blocks measured a draining delivery section, not the controller.

## Pre-run gate (both passed)

- **Environment survey** (180 s, runner-side): 97 % stable frames, jitter
  0.016 mg, **0 shock events**, drift +0.6 mg/min → 180 s error
  1.9–2.1 mg — **inside the ±5 mg dose gate**, the first dose block
  launched with the gate passing rather than documented-over.
- **Pre-flight** (5 × 360° @ 30 RPM, tilt 90°): `feed confirmed`,
  0.6836 g / 5 rev (136.7 mg/rev averaged). Per-revolution:
  **365.7, 200.7, 28.2, 19.0, 70.0 mg** — first-revolution discharge then
  a dying tail. In hindsight this was the arching signature already
  visible (see the protocol doc's pre-flight section, updated from this
  run); the 5-rev total cleared the gate anyway. 10 taps → 37.9 mg.

## Results — all nine doses stalled

| # | block | target | delivered | error | status | time | auger rev | cycles |
|---|---|---|---|---|---|---|---|---|
| 0 | G | 1.000 g | 0.3453 g | −654.7 mg | stalled | 33 s | 25.67 | bulk:94 |
| 1 | G | 1.000 g | 0.1 mg | −999.9 mg | stalled | 9 s | 4.58 | bulk:15 |
| 2 | G | 1.000 g | 0.1 mg | −999.9 mg | stalled | 9 s | 4.58 | bulk:15 |
| 0 | H | 50 mg | 1.1 mg | −48.9 mg | stalled | 31 s | 0.63 | fine:5 |
| 1 | H | 50 mg | 1.8 mg | −48.2 mg | stalled | 58 s | 1.25 | fine:10 |
| 2 | H | 50 mg | 0.6 mg | −49.4 mg | stalled | 31 s | 0.63 | fine:5 |
| 3 | H | 200 mg | 0.8 mg | −199.2 mg | stalled | 35 s | 0.63 | bulk:1 fine:5 |
| 4 | H | 200 mg | 0.6 mg | −199.4 mg | stalled | 31 s | 0.63 | fine:5 |
| 5 | H | 200 mg | −0.4 mg | −200.4 mg | stalled | 31 s | 0.63 | fine:5 |

Dose G0 is the whole story in one trace: bulk opened at ~15 mg/s (the
charged flights emptying), decayed within 20 s to ~0.1 mg/poll, and the
stall detector ended it at 0.3453 g after 25.67 revolutions. Every
subsequent dose started with empty flights, moved 0–2 mg, and stalled in
its minimum cycle count. Zero taps ever fired (no dose got close enough
to a target for a tap phase). Device environment counters were clean
(0 shocks, 0 unsettled brackets) — the room was not a factor.

## Escalated feed diagnostic — `arching-responds-to-agitation`

`battery_feed_diagnostic` at tilt 90°, immediately after the run:

| step | delivered |
|---|---|
| 10 rev @ 60 RPM continuous | 0.6 mg |
| 10 rev @ 90 RPM continuous | 0.0 mg |
| 20 taps → 5 rev (round 0) | 0.2 mg → 0.4 mg |
| 20 taps → 5 rev (round 1) | **5.8 mg → 5.8 mg** |
| 20 taps → 5 rev (round 2) | 2.8 mg → 0.7 mg |

Rotation dead, taps productive, rotation *partially* recovering after
agitation (≈0.46 mg/rev — still ~400× below the powder's known
190.8 mg/rev) and then re-arching. That pattern separates the three
candidate faults:

- **Not an empty column** — 60 taps kept shaking material through, and
  rotation briefly conveyed after agitation.
- **Not a blocked outlet / rig fault** — mass reached the vessel whenever
  the arch was broken, and the same rig ran sodium sulfate G+H normally
  3.5 h earlier (tilt, stepper, balance all exercised).
- **Powder arched over the intake** — barium chloride is a hygroscopic
  salt and this column sat loaded for ~3 weeks since 2026-08-21; caking
  with moisture cycling is the expected failure mode.

## Operator actions before the re-run

1. **Unload the barium chloride and break up the caked material** (or
   replace with dry powder from a sealed container). Expect visible
   clumps.
2. Consider storing hygroscopic-salt augers sealed/desiccated between
   sessions; three weeks in a fume-hood airstream is what did this.
3. **Empty the vessel first**: it holds ≈1.05 g of barium chloride
   (0.68 g pre-flight + 0.35 g doses + 0.02 g diagnostic) — see safety.
4. Reload, remove the tape, comment — G+H is ~10–20 min at this powder's
   healthy feed rate.

## Safety

Barium chloride is acutely toxic (soluble Ba²⁺; toxic by ingestion and
inhalation). The vessel contents and any spill are **toxic waste**:
collect rather than brush out, damp-wipe rather than dry-sweep, dispose
through the hazardous stream in a sealed container — not general waste,
not the sink.

## Rig state after the session

Parked and safe: tilt 0° (battery park + diagnostic teardown both force
it), stepper stopped and disabled, solenoid off, no tmux session or
capture process. ≈1.05 g BaCl₂ in the vessel awaiting disposal.

## Files

- `raw_serial_barium-chloride.log` — verbatim device record (`RUN,END,ok`)
- `2026-09-10_barium-chloride_preflight.log` / `feed_diagnostic_barium-chloride.json` + `.log` — gate and diagnostic evidence
- `trials/polls/doses/summary/timeline` CSVs + `run_barium-chloride.json` (amendment embedded)
- Preroll survey: `docs/rig-checks/data/2026-09-10_barium-chloride-preroll-survey-180s.csv`
