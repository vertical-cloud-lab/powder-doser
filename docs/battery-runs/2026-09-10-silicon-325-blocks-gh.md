# 2026-09-10 — silicon −325 mesh blocks G+H: the dose-block lower bound, replicated

| | |
|---|---|
| Run dir | `data/battery/20260910T212920Z_silicon-325/` |
| Window | 2026-09-10 **21:29:20 → 21:33:25 UTC** (15:29:20 → 15:33:25 MDT), 4 min 05 s (G 28 s · H 3:33) |
| Blocks | `GH` (3 × 1 g + 3 × 50 mg + 3 × 200 mg), detached in tmux `si325`, `--unattended`, bracket read path |
| Batch / operator | `metal-2026-08` / swcharles |
| Mongo `_id` | `6aa3228e10a8006a37fbb5c2` |
| QC | **`valid_for_cross_powder_comparison = true`**, `verdict = conveying-slowly` (amended post-run — see below) |
| Prior data | Valid A–E+G run [2026-08-21](2026-08-21-silicon-325.md): ≤1.2 mg/rev at every tilt, 3 × 1 g stalled |

Fourth dose-block run of the 2026-09-10 campaign (after sodium sulfate G+H
3/3 ok, barium chloride arching-no-feed, AlSi10Mg 6/9 ok). The operator
reloaded the −325 mesh silicon knowing it "doesn't dispense much" and asked
for the re-try; this run turns that expectation into the campaign's
replicated lower bound: **0/9 doses, 18.0 auger revolutions, 1.6 mg net**.

## Pre-run gate

- **Environment survey** (180 s, runner-side): **100 % stable frames**,
  jitter 0.009 mg (display floor), **0 shock events**, drift +0.6 mg/min →
  worst 180 s error **2.1 mg** — inside the ±5 mg dose gate. The cleanest
  gate pass of the dose campaign; the balance carried a stale −5.07 g tare
  from the emptied AlSi10Mg vessel and was re-zeroed first.
- **Pre-flight** (5 × 360° @ 30 RPM, tilt 90°): `empty-or-blocked` —
  every revolution exactly 0.0000 g, but **10 taps → 2.4 mg**. Taps
  conveying is the discriminator against a taped/blocked outlet (the taped
  CMC attempt of 2026-08-05 gave a hard zero through 60 taps), so this was
  escalated rather than aborted.
- **Escalated feed diagnostic** (`battery_feed_diagnostic`, tilt 90°):

  | step | delivered |
  |---|---|
  | 10 rev @ 60 RPM continuous | 0.0 mg |
  | 10 rev @ 90 RPM continuous | 2.5 mg |
  | 20 taps → 5 rev (round 0) | 4.5 mg → 0.7 mg |
  | 20 taps → 5 rev (round 1) | 4.4 mg → 0.6 mg |
  | 20 taps → 5 rev (round 2) | 2.9 mg → 0.4 mg |

  Rotation ≤0.12 mg/rev before **and** after 60 taps of agitation
  (11.8 mg); automated verdict `mechanical-no-feed`. That verdict was
  **overridden to powder cohesion** on three grounds: (1) it reproduces
  the 2026-08-21 silicon −325 signature on a freshly loaded auger;
  (2) taps convey, so the delivery path is open; (3) AlSi10Mg fed at
  ~380 mg/rev on this same rig 100 minutes earlier
  (`20260910T194447Z_alsi10mg`), so every rig-side explanation is
  excluded same-day. Unlike barium chloride this morning, agitation does
  **not** wake rotation up even briefly — this is not an arch that breaks,
  it is a powder that never fills the flights.

## Results — all nine doses stalled at zero

| # | block | target | delivered | error | status | time | auger rev | cycles |
|---|---|---|---|---|---|---|---|---|
| 0 | G | 1.000 g | 0.9 mg | −999.1 mg | stalled | 11 s | 4.58 | bulk:17 |
| 1 | G | 1.000 g | 0.0 mg | −1000.0 mg | stalled | 9 s | 4.58 | bulk:17 |
| 2 | G | 1.000 g | 0.0 mg | −1000.0 mg | stalled | 9 s | 4.58 | bulk:16 |
| 0 | H | 50 mg | 0.0 mg | −50.0 mg | stalled | 31 s | 0.63 | fine:5 |
| 1 | H | 50 mg | −0.1 mg | −50.1 mg | stalled | 35 s | 0.63 | bulk:1 fine:5 |
| 2 | H | 50 mg | −0.0 mg | −50.0 mg | stalled | 31 s | 0.63 | fine:5 |
| 3 | H | 200 mg | 0.0 mg | −200.0 mg | stalled | 31 s | 0.63 | fine:5 |
| 4 | H | 200 mg | 0.0 mg | −200.0 mg | stalled | 31 s | 0.63 | fine:5 |
| 5 | H | 200 mg | 0.8 mg | −199.2 mg | stalled | 52 s | 1.13 | fine:9 |

Zero taps fired on any dose (no dose ever got near enough to a target for a
tap phase). Device environment counters: **0 shock events, 0.0000 g shock
mass, 0 unsettled brackets** — the room contributed nothing, so the zeros
are measurements, not noise. The three sub-milligram non-zeros (0.9, −0.1,
0.8 mg) are at the read floor and consistent with isolated fines.

## Interpretation

- **The dose campaign now has both anchors on the same day, same rig, same
  frozen controller**: sodium sulfate went 3/3 inside ±5 mg at 462 mg/rev
  in the morning; silicon −325 went 0/9 at ≤0.12 mg/rev in the afternoon.
  Feed factor, not controller behaviour, is what a dose inherits.
- **This is the first replicated dose-block measurement on a
  non-conveying powder.** The 2026-08-21 run's three 1 g stalls
  (0.0/1.6/0.4 mg in 6–7 s) are reproduced three weeks later on a fresh
  load: 0.9/0.0/0.0 mg in 9–11 s. n = 2 independent runs agree — the
  first entry in the dataset that answers the Edison review's
  "one battery run per powder" critique for dose behaviour.
- **Size, isolated, decides dispensability**: silicon −110/+200 conveys
  302 mg/rev; the same element at −325 mesh cannot feed a single 50 mg
  dose. The A–E contrast from August now extends through the dose blocks.
- Barium chloride vs silicon −325 is the useful *fault taxonomy* pair:
  both stall every dose, but BaCl₂ (a caked hygroscopic salt) partially
  wakes up after agitation and is recorded **excluded** (material-state
  fault, `arching-no-feed`), while silicon −325 is agitation-immune,
  reproducible across three weeks, and recorded **valid**
  (`conveying-slowly` — the powder's genuine property).

## QC

Recorded `valid_for_cross_powder_comparison = true`, verdict
`conveying-slowly`, by post-run amendment (provenance preserved in the run
document; the diagnostic is embedded under `preflight.diagnostic`). The
stalled doses are the comparable result for this powder, per the
brown-rice-flour precedent (stalled G inside a valid run).

## Follow-ups

- **Vessel holds ≈20 mg of silicon** (pre-flight 2.4 mg + diagnostic
  16.0 mg + doses 1.6 mg) — metal-powder waste, not general waste, when
  emptied.
- **Silicon −110/+200 is now the only metal powder missing its G+H** (its
  valid A–E run is 2026-08-20). Barium chloride still needs its re-run
  with dried/broken-up powder.
- Block F still impossible on every run (DRV2605L absent from the I²C
  bus); granite isolation still pending.
- Fumed silica and brown rice flour are **excluded from further battery
  testing** by operator decision (2026-09-10) — see
  [skipped-powders.md](skipped-powders.md).
