# 2026-09-01 — why block D over-turned, and why it got worse mid-August

Issue #151, following up the EDA in
[PR #97 comment 5417604002](https://github.com/vertical-cloud-lab/powder-doser/pull/97#issuecomment-5417604002)
(§7). The EDA found that block D's commanded "3 revolutions" were really 3.44
up to 2026-08-12 and 4.63 from 2026-08-20, inflating **mg/rev** by 15–54 %.
Both numbers reproduce exactly. This note establishes the mechanism, and
answers the question the EDA left open: **what changed in the gap?**

Reproduce with `python scripts/analyze_block_d_overturn.py`, which rebuilds
everything below from the tidy CSVs committed at `86f2642`.

![block D over-turn](https://github.com/vertical-cloud-lab/powder-doser/blob/a3cfbe2/docs/rig-checks/2026-09-01_block-d-overturn.png?raw=true)

## The defect

`hardware/test-module/firmware/powder_battery.py:690` (tip of
`claude/issue-116-20260821-1907`, `eb29aca`):

```python
self.stepper.run_at_rpm(rpm)          # velocity mode -- turns until told to stop
waited_ms = 0
while waited_ms < spin_ms:
    self._sleep_ms(self.speed_poll_ms)   # sleeps 250 ms
    waited_ms += self.speed_poll_ms      # charges itself 250 ms
    self.stepper.keep_alive()
    reading = self.scale.read()          # ... and then blocks on the balance
    self._emit("POLL", ...)
```

`waited_ms` is a *nominal* clock. The iteration also pays for a balance read
and a serial write, so real time runs ahead of it, and the auger — which is
in velocity mode for the whole loop and is only stopped in the `finally` —
turns for the real duration. `speed_revs` is what gets written to the CSV.

Block D is the only place this pattern appears: `waited_ms` occurs nowhere
else in the firmware. Blocks C, E and F drive the auger with
`rotate_degrees()`, a **positioned** move, so their revolution counts are
exact. That is what makes the block-C ↔ block-D cross-check in the EDA valid.

## What the data says

The loop count is fixed — `ceil(spin_ms / 250)` = 48 / 16 / 8 iterations at
15 / 45 / 90 RPM — and is identical in every run. Only the wall-clock per
iteration moved, and each POLL row carries `_elapsed_ms()`, so it is recorded:

| era | runs | loop period | 3 rev commanded → delivered | mg/rev inflated by |
|---|---|---|---|---|
| 2026-08-04 → 08-12 (`battery_version 1`) | 11 | **287 ms** | **3.44 rev** | 15 % |
| 2026-08-20 → 08-21 (`battery_version 2`) | 8 | **386 ms** | **4.63 rev** | 54 % |

It is a step, not a drift, and it is astonishingly tight: the median interval
is the same to the millisecond in every run and at all three speeds
(early 280–302 ms excluding the slips noted below, late 369–387 ms, n = 1311).

## Why 287 and 386

**Because the loop is quantised by the balance, not by the sleep.**

The A&D HR-100A delivers frames on a **~96 ms grid** — 95.6 ms measured
directly in the 2026-07-31 free-stream capture
(`data/scale-idle/2026-07-31_idle/maxrate_30s.log`), and the same quantum
shows up in the 2026-08-14 step-response captures. `scale.read()` drains,
sends `Q`, and then blocks until a whole frame parses, so a loop pass can only
ever end on a frame boundary. Every admissible loop period is a multiple of
~96 ms:

* `250 ms` sleep + work < 287 ms → the pass ends on the **3rd** frame: 287 ms
  (3 × 95.7), 3.44 rev.
* `250 ms` sleep + work > 287 ms → it ends on the **4th**: 386 ms (4 × 96.5),
  4.63 rev.

**The margin between those two outcomes is 37 ms.** That is the entire budget
for `keep_alive()`, `scale.read()` and `_emit()` on a 133 MHz MicroPython
target that is also streaming CSV over USB. The early runs were living inside
it — but only just: **16 of 759 early-era iterations (2.1 %) already slipped
to the 4-frame slot**, in ten of the eleven early runs. The
loop was never robustly at 287 ms; it was marginally at 287 ms. After 08-20
it slipped on every single pass.

That is the answer to "what happened": nothing dramatic. **A latent timing
race that had always been ~2 % marginal went 100 % marginal when the loop
body got a few tens of milliseconds heavier.**

## What was ruled out

Each of these was checked against committed evidence, and none of them is the
cause:

* **The balance did not get slower.** 31 independent captures in
  `docs/rig-checks/data/` — including per-run pre-roll surveys taken *minutes
  before* the 386 ms runs (`2026-08-20_sodium-sulfate-preroll-survey-240s.csv`,
  `2026-08-21_silicon-325-preroll-survey-240s.csv`) — all poll at **287 ms**,
  unchanged across the boundary. Those loops are `sleep_ms(180)` + one read
  (`scripts/balance_zero.py:120`), so the balance's `Q` round-trip is ~107 ms
  and constant on both sides of the move.
* **The serial link did not change.** The `META,config.SCALE_*` rows are
  byte-identical in the 08-12 and 08-20 runs: 19200 baud, 8 data bits, no
  parity, 1 stop.
* **`scale.py` did not change on the read path.** It was committed as found on
  the Pico at `af3bc0c`; the only subsequent edit was `zero()` switching `Z` →
  `T` with a 500 → 1500 ms settle (`ea333e0`). `read()`, `_readline()`,
  `_read_reading()` and `_drain()` are untouched.
* **`stepper.py` did not change.** Last edit 2026-07-09 (`d3a42d7`).
* **The block-D loop body did not change.** The `while` body is
  character-identical between `battery_version` 1 and 2; only the surrounding
  `before`/`after` reads became brackets.
* **The `RESPONSE`/`Cond` front-panel setting was not the cause.** It was
  *recommended* on 2026-08-19
  (`docs/rig-checks/2026-08-19-balance-draft-noise-shield-removed.md`, mitigation 3)
  and would have been an excellent suspect, but the pre-roll surveys above show
  the balance answering at its old rate throughout, so if it was ever set to
  `SLOW` it was not in effect during these runs.
* **It is not a sampling artefact.** Poll counts are exactly 48/16/8 per speed
  in both eras, so no iteration was dropped or added.

## What is left

The remaining cause is inside the Pico, and it is the one thing that *did*
change on 2026-08-20: **`battery_version 2`** (`8aa9ef3`). It adds
`import balance_filter` at module scope and holds per-trial bracket sample
buffers, and it demonstrably does much more balance work per trial — the gap
between block-D speed points grew from a median **2.58 s to 7.75 s**. More
live heap on a 264 KB target means MicroPython's allocator collects more often
and for longer, and the block-D loop allocates on every pass (`read()` builds
frames, `_emit()` builds a joined string). A few tens of milliseconds of extra
GC per pass is all it takes to cross a 37 ms margin.

A second, non-exclusive candidate is host-side USB CDC backpressure: `_emit()`
writes to the REPL, and `scripts/powder_battery_capture.py` was rewritten in
the same commit. Both are consistent with the evidence; neither can be
separated from the other without a bench measurement.

**This is testable on the rig in about a minute** — run block D alone under
`battery_version 1` and again under 2, on the same day, and compare the POLL
spacing. It is worth doing before round 2, because the fix below should be
verified to hold the loop at a fixed period rather than merely moving the
margin.

## Scope of the damage

* **Affected:** `mg/rev` for block D only, and anything derived from it —
  including the C1 panel in the candidate figure set, which the EDA had
  already flagged as unpublishable on taring/ordering grounds.
* **Not affected:** total mass, and mg/s over the reconstructed window, since
  the reconstruction uses the recorded timestamps. Blocks A, B, C, E and G are
  untouched — C and E use positioned moves.
* **Recoverable:** completely. Every affected trial's true duration is in the
  POLL stream; `docs/rig-checks/data/2026-09-01_block-d-poll-intervals.csv`
  carries the per-run, per-speed correction factor.

Independent confirmation, all three from the EDA and all three consistent with
the reconstruction: slug counts on the 15 RPM traces match the reconstructed
revolution count to within one slug; the block-C ↔ block-D ratio moves from
1.22× to 0.84×; and the independently-fitted speed exponent predicts 0.92× for
30 → 45 RPM.

It is also visible on video. The bench camera streams continuously and the
run documents carry per-block links back to 2026-08-04, so block D's three
spins should take **20.7 s** on an early run and **27.8 s** on a late one
against a nominal 18.0 s — and at 15 RPM (4 s/rev) the slugs are countable.
`docs/battery-runs/clips/wrf_D_speed.mp4` is the 2026-08-04 block D at 4×.

## The fix

Don't infer elapsed time — measure it, and prefer a positioned move so there
is nothing to infer. Applied to `powder_battery.py:684-690`:

```python
self.stepper.run_at_rpm(rpm)
t_spin = self._ticks_ms()
misses = 0
try:
    while _ticks_diff(self._ticks_ms(), t_spin) < spin_ms:
        self._sleep_ms(self.speed_poll_ms)
        ...
finally:
    self.stepper.stop()
    spun_ms = _ticks_diff(self._ticks_ms(), t_spin)
actual_revs = rpm / 60.0 * spun_ms / 1000.0
```

and emit `actual_revs` (or `spun_ms`) on the TRIAL row instead of the
constant `self.speed_revs`, so the normalisation can never again depend on an
assumption. That alone bounds the error at one poll interval — still up to
0.58 rev at 90 RPM — so for round 1 of round 2 the better primitive is the one
blocks C and E already use: `self.stepper.rotate_degrees(360.0 * self.speed_revs)`
at the set RPM, which makes the revolution count exact by construction. The
poll stream can be kept by polling from inside a positioned move, or dropped
at the two higher speeds, where the EDA showed the crest factor is aliased
anyway and the traces are not quotable.

Bump `battery_version` when this lands, so corrected runs are separable from
the 19 that need the correction factor applied.

## Files

* `scripts/analyze_block_d_overturn.py` — reproduces every number here.
* `docs/rig-checks/data/2026-09-01_block-d-poll-intervals.csv` — per run, per
  speed: measured loop period, delivered revolutions, correction factor.
* `docs/rig-checks/2026-09-01_block-d-overturn.png` — the figure above.
