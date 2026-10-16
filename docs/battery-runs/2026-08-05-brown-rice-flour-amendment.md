# Amendment — brown rice flour, both 2026-08-04 runs

Applies to
[run 1](2026-08-04-brown-rice-flour.md)
(`20260804T204316Z_brown-rice-flour`) and
[run 2](2026-08-04-brown-rice-flour-rerun.md)
(`20260804T224937Z_brown-rice-flour`). Recorded 2026-08-05 from bench
evidence supplied by @swcharles in
[issue #116](https://github.com/vertical-cloud-lab/powder-doser/issues/116).

No measured value changes. What changes is the *cause* the two runs were
attributed to, and both original attributions were wrong.

## What the operator established

1. **The delivery-end tape was off during run 1**, confirmed from the bench
   camera video. Run 1 had been condemned as `suspect-no-feed` on the theory
   that a taped outlet explained the exact-zero rotation; that theory is
   withdrawn.
2. **The auger tube rotates with the drive coupler in all trials.** The
   re-run notes had flagged the coupler as "the single unverified link in the
   chain" and declined to call the result cohesion because of it. It is now
   verified.
3. **An off-rig hand test reproduces the result.** On 2026-08-05, with the
   balance zeroed, 20 full rotations of the loaded auger turned by hand over
   the dish delivered **0.0019 g** — 0.095 mg/rev, with no coupler, no cap,
   and no drive train in the loop.

That hand test is the control the re-run notes asked for, and it answers the
question they posed ("if it does not come out by hand either, it is the
powder, and the zero is real") in the direction of the measurement being
sound.

## Feed factor in context (tilt 90°, mg per 360° revolution)

| Powder | mg/rev | Source |
|---|---|---|
| White rice flour | 37.15 | battery block C |
| Sodium alginate | 3.52 | pre-flight, 2026-08-05 |
| **Brown rice flour, rig** | **0.03–0.075** | feed diagnostic, run 2 |
| **Brown rice flour, by hand** | **0.095** | operator, 2026-08-05 |

The rig and the hand agree to within a factor of ~2, three orders of
magnitude below white rice flour. Whatever is stopping this flour is not in
the drive train.

## What is still open, and why the runs stay excluded

Two hypotheses survive: the **powder** (cohesion/clumping, consistent with
@carl-robison's manual finding that "simple twisting actions fail to shift its
internal structure") and **this particular auger print** (a malformed flight
or bore would produce the same near-zero conveyance, and would not generalise
to the augers the other powders are running in).

The hand test does not separate those two — it used the same auger. So both
runs keep `valid_for_cross_powder_comparison = false`, with the verdict
changed from `suspect-no-feed` / `cohesive-no-flow` to
**`no-conveyance-auger-suspect`**: the measurement is trustworthy, the
attribution is not yet.

@swcharles is transferring the same flour into a freshly printed auger for a
re-test. If the new auger conveys, the two runs above are an auger-print
artefact. If it does not, brown rice flour's near-zero feed factor is a real
and publishable result for this geometry, and both runs can be promoted to
valid.

## How this was applied

Via [`scripts/amend_battery_run.py`](../../scripts/amend_battery_run.py), which
appends a dated, attributed entry to the run document's `amendments` list,
records the previous QC values alongside the new ones, and pushes the same
change to MongoDB so the committed artefact and the database stay identical.
Measured arrays (`trials`, `polls`, `doses`) are never touched.

```bash
python scripts/amend_battery_run.py \
    data/battery/20260804T204316Z_brown-rice-flour/run_brown-rice-flour.json \
    --author swcharles --evidence-file evidence.json \
    --summary "..." --set-verdict no-conveyance-auger-suspect \
    --set-valid false --push
```
