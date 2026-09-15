# Block D speed traces: does per-revolution slugging survive at 45/90 RPM?

Post-hoc extraction (2026-09-15, PR #131 request) from the #116 uniform
battery's Block D: 3 commanded revolutions of continuous rotation at
15 / 45 / 90 RPM, tube tilt 45 deg (non-vertical), ~3.5 Hz scale polls
streamed during rotation. Asked because the 2026-07-30 PID sessions on
salt showed delivery arriving as ~one-revolution slugs that defeat a
continuous-flow controller near the endpoint.

Seven QC-valid runs (one per powder); the two retracted no-feed
brown-rice-flour runs are excluded automatically.

| File | Contents |
|---|---|
| `speed_45rpm_traces.png` | the 45 RPM dispensing trace per powder, revolution boundaries + settled mass marked |
| `speed_rpm_comparison.png` | 15 vs 45 vs 90 RPM per powder on a revolutions-completed axis |
| `slug_metrics.csv` | per (powder, rpm): streamed/settled mg, actual revolutions, `ramp_dev` ("slug index": max deviation from a straight ramp / total; 3-step staircase ~0.17, smooth < 0.05), `burstiness` (max single-poll increment / uniform expectation) |

Regenerate with:

```bash
python scripts/plot_battery_speed_traces.py data/battery/speed-analysis data/battery/2026*/
```

## Headline result

Per-revolution slugging **attenuates but does not disappear** at 45 RPM,
and the effect is powder-specific:

- The strongest 15 RPM staircases — white rice flour (slug index 0.197,
  i.e. essentially a pure 3-step staircase), CMC (0.134), salt (0.098) —
  roughly halve at 45 RPM (0.095 / 0.076 / 0.086). Inflections at
  revolution boundaries are still visible in the 45 RPM traces.
- Xanthan gum does **not** improve (0.057 → 0.055 → 0.070): its
  lumpiness is aperiodic clump release, not rev-synchronous, so speed
  does nothing for it.
- Calcium lactate was already comparatively smooth at 15 RPM (0.067).
- Brown rice flour conveys nothing at any speed (metrics suppressed).

## Caveats (why the smoothing is only partly a powder property)

1. **Arrival-side merging.** At 45 RPM the revolution period (1.33 s)
   approaches the ~1 s lip-to-cup transport/afterflow spread measured in
   the 2026-08-07 stop-response tests, so consecutive slugs genuinely
   merge in flight before landing. Real at the balance — which is what a
   controller sees — but the *release* at the lip stays quantized per
   revolution.
2. **Instrument floor at 90 RPM.** ~2.3 polls/rev plus the balance's
   ~0.5–1 s step response cannot resolve per-rev structure, so the low
   90 RPM slug indices overstate smoothness. `burstiness` is even more
   sampling-biased (per-poll integration time differs 6x across speeds);
   compare it within a speed, not across speeds.
3. **Speed costs feed for some powders.** Settled mg/rev 15 → 45 RPM:
   salt 43.8 → 17.1 (−61 %), xanthan 202 → 109 (−46 %), calcium lactate
   165 → 131 (−21 %); but white rice flour 16.5 → 21.0 (+27 %) and CMC
   20.1 → 26.6 (+32 %). Same sign pattern as the known Block D speed
   dependence.
4. One tilt only (45 deg), one fill state per powder, n=1 segment per
   speed — Block D was a screening block, not a designed experiment.
