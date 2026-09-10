# 2026-09-10 — AlSi10Mg blocks G+H: block parity for the flagship metal powder

Dose blocks G (3 × 1 g) + H (3 × 50 mg + 3 × 200 mg), frozen three-phase
controller, `dose_read_path=bracket`, on AlSi10Mg in the EB B125 fume
hood. Completes AlSi10Mg's block parity minus only F: its valid A–E run
is [2026-08-21](2026-08-21-alsi10mg.md), and its only prior dose data was
the invalidated no-tilt run of
[2026-08-11](2026-08-11-alsi10mg.md) — this run supersedes that gap with
a working tilt axis.

## Launch (session 20260910-1813)

| | |
|---|---|
| Run dir | `data/battery/20260910T194447Z_alsi10mg/` |
| Launched | **2026-09-10 19:44:47 UTC (13:44:47 MDT)** |
| Ended | **2026-09-10 19:59:47 UTC (13:59:47 MDT)** — 14 min 59 s (G 5:10, H 9:45) |
| Mode | detached in tmux `alsi10mg`; `--unattended`; upload runner-side after collection |
| Blocks | `GH` (9 doses) |
| Batch / operator | `metal-2026-08` / swcharles |
| MongoDB | `_id 6aa30ca184f38fe7b296e3e5`, QC promoted `unreviewed` → `ok`, `valid = true` |

### Pre-run gate — a 70-minute hold, then a clean launch

The bench was *not* ready when the operator commented (12:13 MDT). The
morning's network outage (~11:31–12:30 MDT, which froze the livestream
and dropped the doser Pi off the tailnet — no reboot, 6-day uptime) and
the barium chloride cleanup left the balance walking:

- 12:32 MDT survey: drift −12.1 mg/min, 2 shock events — freshly handled
  bench;
- eleven settle-and-survey rounds 12:32 → 13:44 (all CSVs committed under
  `docs/rig-checks/data/2026-09-10_alsi10mg-preroll-*`): shocks gone by
  12:48, then a large decaying negative drift (−16 → −8 → −3.5 →
  −2.6 mg/min end-to-end per window) consistent with the washed/damp-wiped
  vessel and handled enclosure equilibrating after the BaCl₂ toxic
  cleanup;
- **launch gate: +2.0 mg/min end-to-end, 0 shocks at 13:44** —
  comparable to the sodium sulfate launch condition (−1.6 mg/min) that
  morning.

**Pre-flight** (5 × 360° @ 30 RPM, tilt 90°): **feed confirmed**,
1.2603 g / 5 rev (252.0 mg/rev averaged). Per-revolution: **6.9, 111.5,
399.7, 322.2, 420.0 mg** — a charging transient then steady
≈380 mg/rev, i.e. a fresh, fully-loaded column and *not* the
first-revolution-discharge-then-dying-tail arching signature that
barium chloride showed three hours earlier. 10 taps → 63.5 mg
(6.35 mg/tap at 90°). The metal powder did **not** cake over three
weeks of storage — the contrast with BaCl₂ that
[the storage doc](../powder-storage-hygroscopicity.md) predicts.

Device-side environment counters for the run itself: **0 shock events,
0.0000 g shock mass, 0 retries, 0 unsettled brackets** — the patience
before launch bought a clean 15 minutes.

## Results

| # | block | target | delivered | error | status | time | auger rev | taps | cycles |
|---|---|---|---|---|---|---|---|---|---|
| 0 | G | 1.000 g | 0.9973 g | **−2.7 mg** | **ok** | 65 s | 3.08 | 0 | bulk:6 fine:10 |
| 1 | G | 1.000 g | 1.0094 g | +9.4 mg | overshoot | 53 s | 3.75 | 0 | bulk:7 fine:8 |
| 2 | G | 1.000 g | 0.9989 g | **−1.1 mg** | **ok** | 193 s | 2.50 | 92 | bulk:8 fine:5 tap:46 |
| 0 | H | 50 mg | 46.6 mg | **−3.4 mg** | **ok** | 51 s | 1.00 | 2 | fine:8 tap:1 |
| 1 | H | 50 mg | 68.1 mg | +18.1 mg | overshoot | 15 s | 0.25 | 0 | fine:2 |
| 2 | H | 50 mg | 99.7 mg | +49.7 mg | overshoot | 8 s | 0.92 | 0 | bulk:1 |
| 3 | H | 200 mg | 197.2 mg | **−2.8 mg** | **ok** | 31 s | 0.63 | 0 | fine:5 |
| 4 | H | 200 mg | 199.4 mg | **−0.6 mg** | **ok** | 214 s | 0.26 | 118 | bulk:1 fine:2 tap:59 |
| 5 | H | 200 mg | 202.6 mg | **+2.6 mg** | **ok** | 264 s | 0.89 | 134 | fine:7 tap:67 |

Per-target mean error: **1 g +1.9 mg (2/3 ok) · 200 mg −0.3 mg (3/3 ok)
· 50 mg +21.5 mg (1/3 ok)**. Total dispensed 3.82 g (≈5.1 g in the
vessel including pre-flight — **metal-powder waste stream**, not general
waste).

### The 200 mg triplet is the most accurate of the campaign

Mean −0.27 mg, worst single dose −2.8 mg, 3/3 inside the band. Every
other powder's 200 mg mean for comparison: salt +2.8, xanthan +2.9,
white rice flour −4.9, calcium lactate −6.9 (n=2), sodium sulfate
+10.8, CMC −22.6, sodium alginate −101.5. A dense free-flowing metal at
≈380 mg/rev turns out to be the controller's easiest 200 mg customer so
far.

### The tap phase converged on a metal powder — revising 2026-08-21

Doses G2, H4 and H5 all closed their final milligrams with long tap
phases (92 / 118 / 134 taps) and landed at −1.1 / −0.6 / +2.6 mg. The
2026-08-21 A–E run had recorded AlSi10Mg's tap quantum as **not
resolved** (−1.9 mg mean at 45° in an 88 mg no-actuation spread) and
flagged the gap as belonging to the bench, not the powder. Today
confirms that suspicion from the other side: with a charged lip and a
quiet room the solenoid demonstrably meters this powder (pre-flight
6.35 mg/tap at 90°), and phase 3 is not a dead end for it. The A–E
block E figure should eventually be re-measured on the quiet bench, but
the dose evidence already overturns the "taps do nothing on AlSi10Mg"
reading.

### The 50 mg doses are the quantum limit, same mechanism as sodium sulfate

At ≈380 mg/rev a single 45° fine increment carries ≈47 mg — the whole
target — and H2's one bulk revolution delivered ≈100 mg in 8 s. Doses
that happened to start with a full lip overshot immediately (H1 +18.1,
H2 +49.7, zero taps fired); the one that started lean (H0) crept in on
fine cycles and closed at −3.4 mg. Identical to sodium sulfate's 50 mg
failure (0/3, mean +28.9 mg), marginally better here (1/3).

Two campaign-level observations this sharpens:

1. **Absolute error is not monotonic in target.** Mean |error| runs 4.4
   → 2.0 → 23.7 mg at 1000 → 200 → 50 mg — the 200 mg target beats the
   1 g target in absolute terms, because 1 g doses admit an overshoot
   through the fine phase (G1: +9.4 mg with 0 taps) while 200 mg sits in
   the sweet spot where fine increments are small relative to target but
   the tap phase can still trim.
2. **The 50 mg target selects for *slow* powders.** The best 50 mg
   results in the campaign belong to white rice flour (−4.7 mg) and salt
   (+4.2 mg) — modest feed factors — while the three fastest feeders all
   overshoot (sulfate +28.9, AlSi10Mg +21.5, xanthan +17.8). One frozen
   feed geometry cannot serve a 20× target span at both ends: the
   controller's dose floor scales with the powder's per-increment
   quantum. That is the #97 transferability argument, measured from the
   target axis instead of the powder axis.

## Environment during the run

Nothing needed the artifact machinery: 0 shocks, 0 drift corrections,
0 retries, 0 unsettled brackets (`META,env.*` rows in the raw serial
log). The launch-gate hold — not software — is what made the ±5 mg
classifications trustworthy; the pre-launch drift bound at +2.0 mg/min
puts a ≤ ~9 mg worst-case bias on the longest (264 s) dose with known
sign, and no classification in the table is sensitive to it (the three
long doses landed −1.1, −0.6, +2.6 mg — if anything the true errors sit
slightly more negative).

## Also learned this session

- **The livestream froze at 11:30:41 MDT** when the ~11:31 network
  outage hit both stream-cam Pis; the frozen frame still answered
  `0 s behind live` from the 11:00 UTC broadcast, which is a trap for
  `bench_frame.py` users — check the burned-in overlay clock against
  wall time before trusting a "live" frame. A fresh broadcast at the
  19:00 UTC rollover recovered live frames.
- The doser Pi's 53-minute tailnet absence (11:37–12:30 MDT) was
  network-only — 6-day uptime, no reboot, no rig impact.

## Follow-ups

- **Empty the vessel before the next powder**: ≈5.1 g of AlSi10Mg —
  metal-powder waste.
- Block F still impossible (DRV2605L absent). AlSi10Mg is now complete
  through A–E + G + H.
- The remaining dose-campaign powders per the run log: brown rice flour
  (expect budget-limited stalls), silicon −110/+200 and −325, and the
  barium chloride re-run once the caked column is replaced with dry
  powder from sealed storage (see
  [the storage doc](../powder-storage-hygroscopicity.md)).

## Files

- `raw_serial_alsi10mg.log` — verbatim device record (`RUN,END,ok`,
  `META,park_tilt_deg,0.0`)
- `alsi10mg_preflight.log` — pre-flight gate evidence
- `alsi10mg_capture.log` — host capture log with per-cycle dose traces
- `trials/polls/doses/summary/timeline` CSVs + `run_alsi10mg.json`
  (QC amendment embedded)
- `alsi10mg_block_h.png` — dose accuracy vs target figure
- Preroll surveys: `docs/rig-checks/data/2026-09-10_alsi10mg-preroll-*.csv`
  (11 windows, 12:32 → 13:44 MDT)
