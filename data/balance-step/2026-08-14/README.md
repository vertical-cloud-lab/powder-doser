# Balance step response — known-mass drop tests (2026-08-14)

Bench test by @williamulbz (manual drops, no powder consumed), following the
τ_balance drop-weight outline in
[PR #124 comment](https://github.com/vertical-cloud-lab/powder-doser/pull/124#issuecomment-5297006017).
Raw CSVs attached to
[PR #131 comment](https://github.com/vertical-cloud-lab/powder-doser/pull/131#issuecomment-5298061787);
analyzed by `scripts/analyze_balance_step.py`.

## Files / naming

`balance_capture_<mass>g_<n><method>.csv` — raw ~5.2 Hz stream
(`D,<t_ms>,<mass_g>,<S|U>` rows, S = stable-flagged frame), one file per
condition, each holding ~10 drop / removal cycles of one known mass:

- `d` — drops from 5–10 mm
- `ad` — alternating drops: 5 low (5–10 mm) and 5 high (~20 mm), interleaved
- `l` — slow lay-down by hand (9 completed before time ran out; a 10th is
  truncated at stream end)

Operator notes: in the `ad` file two of the high drops bounced — visible in the
data as events with short/partial plateaus (see `events.csv` `partial` column).

## Headline results (see `summary.csv`, `events.csv`)

- **τ_bal ≈ 0.16 s** (pooled first-order fit over 28 clean drop steps:
  median 0.164 s, mean 0.166 s, sd 0.029 s). Mass-independent (2/5/10 g),
  height-independent (5–20 mm), and matched by gentle lay-downs (0.158 s) —
  the linear-filter assumption holds and impact does not contaminate τ.
- Response shape is a smooth S-ramp (FIR-like), total transition ~0.5–0.7 s;
  the first-order equivalent τ = 0.16 s fits with R² > 0.995 outside the
  impact frame.
- **Settle to ±2 mg: ~0.7–0.9 s** after step start.
- **Stable-flag (ST) latency: ~1.5–2.3 s** — waiting for ST costs ~1 s more
  than trusting the raw stream at the ±2 mg level.
- **Impact overshoot** (single ~0.2 s frame): tens of mg for 5–10 mm drops,
  up to ~270 mg for 20 mm drops; ~0–30 mg for lay-downs. Height-dependent →
  mechanical, not filter behavior.
- Quiet baseline noise: 0.13–0.42 mg per frame.
- Frame spacing ~192 ms (~5.2 Hz) despite a 60 ms poll — consistent with the
  balance's datum update at the factory `Spd` = 5/s setting.

Caveats: dead time is not separable (no independent marker of the physical
drop moment); removals are contaminated by the hand pressing the pan
(~2× load spikes) and are not analyzed as negative steps.
