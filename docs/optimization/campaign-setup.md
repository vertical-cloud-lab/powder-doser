# Optimization campaign: workflow and algorithm design (issue #164)

Design-only document — no campaign code exists yet. It answers the two questions issue
[#164](https://github.com/vertical-cloud-lab/powder-doser/issues/164) asks to settle
before code is written:

1. **The workflow** — which machine runs what, where the user types, where data lands,
   and how optimized parameters get reused for future dosing (§1).
2. **The optimization algorithm** — search space, objectives, constraints, the screening
   start prescribed by [PR #162](https://github.com/vertical-cloud-lab/powder-doser/pull/162),
   dose-amount policy, and what gets recorded per dose (§2).

It builds on four open threads:

| Thread | What it contributes here |
|---|---|
| [PR #154](https://github.com/vertical-cloud-lab/powder-doser/pull/154) trickle-tap firmware ([`hardware/test-module/firmware/trickle_tap/`](https://github.com/vertical-cloud-lab/powder-doser/tree/claude/issue-153-20260903-2040/hardware/test-module/firmware/trickle_tap)) | The controller being optimized — bulk → PI trickle → tap endgame, hand-tuned by William to well within 10 mg. Its [`trickle_params.py`](https://github.com/vertical-cloud-lab/powder-doser/blob/claude/issue-153-20260903-2040/hardware/test-module/firmware/trickle_tap/trickle_params.py) holds every knob, all settable live over the REPL (`set <key> <value>`). |
| [PR #162](https://github.com/vertical-cloud-lab/powder-doser/pull/162) optimization design doc ([`docs/optimization/README.md`](https://github.com/vertical-cloud-lab/powder-doser/blob/claude/issue-161-20260909-2256/docs/optimization/README.md)) | Problem formulation and the §5 screening DOE this campaign starts with (adapted in §2.4 to the issue #164 parameter list). |
| [PR #131](https://github.com/vertical-cloud-lab/powder-doser/pull/131) data collection ([`docs/characterization-data-collection.md`](https://github.com/vertical-cloud-lab/powder-doser/blob/claude/issue-130-20260721-1807/docs/characterization-data-collection.md)) | The proven remote-operation pattern: laptop → Tailscale SSH → Pi Zero (bench host, tmux) → USB serial → Pico; `powder_id` slug stamped on everything; MongoDB `powder_doser` DB with `MONGODB_URI` in an env file on the Zero; everything written to SD first so offline runs backfill later. |
| [PR #124](https://github.com/vertical-cloud-lab/powder-doser/pull/124) twin + benchmarks | The simulation twin the controller was ported from; useful for dry-running the campaign loop without hardware. |

---

## 1. The workflow

### 1.1 Four layers, four jobs

```
┌─────────────────┐   Tailscale SSH    ┌──────────────────┐   USB serial    ┌─────────────────┐
│  Laptop          │ ─────────────────▶│  Pi Zero          │ ──────────────▶│  Pico W          │
│  (optimizer)     │   one dose per     │  (executor)       │  set params,   │  (controller)    │
│                  │   request, JSON    │                   │  run dose,     │                  │
│  Ax / Honegumi   │   result back      │  dose-capture     │  RESULT line   │  trickle-tap     │
│  ask–tell loop,  │                    │  script: serial   │                │  firmware: KF,   │
│  campaign state, │                    │  bridge, local    │                │  PI, taps, hard  │
│  Pareto review   │                    │  spool, Mongo     │                │  safety aborts   │
└────────┬─────────┘                    │  upload           │                └────────┬────────┘
         │                             └─────────┬─────────┘                          │
         │ campaign + trial documents            │ trial documents,                   │ auger (Tic T500),
         │ (write-through, resumable)            │ telemetry                          │ tilt servos, tap
         ▼                                       ▼                                    │ solenoid, A&D
      ┌──────────────────────────────────────────────┐                                ▼ HR-100A balance
      │  MongoDB Atlas — powder_doser database        │                            the rig
      │  opt_campaigns · opt_trials · dosing_profiles │
      └──────────────────────────────────────────────┘
```

- **Pico W (real-time controller).** Runs the trickle-tap firmware exactly as in #154 —
  the KF, the PI loop, the tap endgame, and all hard safety (dose timeout, RPM cap,
  stall bail, emergency stop). Two small additions are needed (§3): the bulk-phase and
  PI-phase tap cadences as switchable knobs, and a machine-parseable `RESULT` line so
  the host does not scrape human-oriented REPL text.
- **Pi Zero (executor / bench host).** Exactly the role #131 established. Runs a thin
  per-dose script: push one parameter set over serial (`set k v` already exists), issue
  the dose, capture telemetry, take the settled final reading, prompt the operator for
  the spill check, write the trial document to the SD card **and** MongoDB, print one
  JSON result line back up the SSH pipe. It never chooses parameters.
- **Laptop (optimizer).** Runs the Honegumi-templated Ax loop: ask a parameter set →
  invoke the Zero over SSH → tell Ax the outcomes → repeat. This is the one deliberate
  departure from #131's "run everything on the Zero" pattern, and it is forced:
  Ax rides on BoTorch/PyTorch, which is not realistically installable or runnable on a
  512 MB Zero (piwheels has no torch for it). The split also matches how issue #164 is
  phrased — you sit at your computer, SSH reaches the rig.
- **MongoDB Atlas (ledger).** Same database (`powder_doser`) and connection conventions
  as #131. Three new collections (§1.3). The Zero uploads trial documents (it already
  has `MONGODB_URI` and egress); the laptop writes campaign-level documents and the
  final dosing profiles.

**Robustness to a dropped SSH session.** Each dose is atomic on the Zero: the dose
script finishes the dose, spools the result locally, and uploads to Mongo even if the
laptop vanishes mid-dose (the rig is never left running on a dead pipe — the Pico's
dose timeout and the script's own completion handle that). On reconnect the campaign
script finds the completed trial in Mongo/spool instead of re-dosing it, and the Ax
experiment is snapshotted to JSON after every trial, so a campaign resumes from where
it stopped — across SSH drops, laptop sleeps, or days between sessions.

### 1.2 Where the user types

All user input happens in two places, both in front of William:

1. **Campaign launch (laptop terminal):**

   ```
   python scripts/opt_campaign.py --powder-id xanthan --target-g 0.5 \
       --budget 40 [--resume <campaign_id>] [--screen-only]
   ```

   `--powder-id` is the same required slug as #131 (reused consistently so Mongo
   queries pull a powder's whole history across characterization, battery, and
   optimization runs).

2. **Operator prompts between doses (same terminal, relayed to hands at the rig):**
   confirm cup emptied / hopper topped up when the session protocol asks (§2.5), and
   answer the per-dose spill check (`spill? [y/N]`) — the one outcome the rig cannot
   yet sense itself (§2.3). Campaign sessions are supervised by design; the operator
   is at or near the rig.

Nothing is typed on the Zero beyond starting/attaching tmux, and nothing on the Pico
beyond what the scripts send.

### 1.3 Where data lands

Everything follows #131's write-local-first rule; Mongo is the queryable ledger.

| Store | Contents |
|---|---|
| `opt_campaigns` (Mongo) | One document per campaign: `campaign_id`, `powder_id`, target mass, search-space definition (boxes + categoricals), **frozen-parameter snapshot** (every `trickle_params` value not being searched — the hand-tuned baseline), firmware git SHA, Ax/Honegumi config, status, and the Ax experiment JSON snapshot (updated as the campaign runs). |
| `opt_trials` (Mongo) | One document per dose (§2.6 field list): parameters, outcomes, flags, per-poll telemetry rows (a dose is a few hundred rows — small enough to embed), session covariates. Written by the Zero at dose completion. |
| `dosing_profiles` (Mongo) | **The product.** One document per (powder, profile): the chosen parameter set, the frozen-parameter snapshot it rides on, provenance (`campaign_id`, date, firmware SHA), and validated performance (median/p95 |error|, median time, P(|error| ≤ 10 mg) from the §2.4 validation replicates). |
| Zero SD card | JSONL spool of every trial document + the raw telemetry CSV per dose (the existing `/trickle_log_NNN.csv` pulled off the Pico), under `data/opt/<campaign_id>/`. Offline-safe; backfill to Mongo later exactly as #131 does. |
| Laptop | Ax experiment snapshot JSON (also mirrored into the campaign document); analysis notebooks/plots. Interesting runs get committed to `data/` in the repo as before. |

### 1.4 Future dosing from saved profiles

The reuse path is a small CLI on the Zero (runnable over the same SSH):

```
python scripts/dose.py --powder-id xanthan --target-g 0.35
```

It looks up the newest validated `dosing_profiles` document for that `powder_id`
(falling back to a local profile cache synced at campaign end, so dosing works with no
internet), pushes the full parameter set — searched values *and* frozen snapshot — to
the Pico over `set`, runs the dose, and logs the result to `opt_trials` with a
`mode: "production"` stamp. Production doses therefore keep feeding the same ledger,
which is exactly the data a later contextual/multi-powder model (#162 §4.1) will want.
Profiles are validated at one target mass; dosing other targets with the same profile
is expected to work but is logged as such until we have data across targets.

---

## 2. The optimization algorithm

### 2.1 Search space — 8 parameters

Two categorical, six continuous. Boxes below are placeholders to be finalized by
range-finding + the screen (§2.4); the hand-tuned #154 values sit inside every box.

| # | Parameter | Type | Placeholder box | Firmware knob |
|---|---|---|---|---|
| 1 | Bulk taps | categorical {off, on} | on = fixed cadence (§4 Q1) | new — port of `main_three_phase`'s per-phase `tap_on_ms`/`tap_off_ms` into the bulk phase |
| 2 | Trim (PI-phase) taps | categorical {off, on} | on = fixed cadence (§4 Q1) | new — same machinery during the trickle |
| 3 | Bulk tilt | continuous | 15–40 plate ° | `BULK_TILT_DEG` |
| 4 | Trim tilt | continuous | 10–30 plate ° | `TRICKLE_TILT_DEG` |
| 5 | Tap tilt | continuous | 0–15 plate ° | `TAP_TILT_DEG` |
| 6 | Bulk RPM | continuous | 20–100 auger RPM (ceiling 109) | `BULK_RPM` |
| 7 | Bulk→trim threshold | continuous | 0.05–0.20 g remaining | `TRICKLE_START_REMAINING_G` |
| 8 | Trim tolerance band | continuous | 3–15 mg | `TOLERANCE_G` |

Per issue #164, the tap parameters are **on/off only** — the "on" frequency is a fixed
constant taken from William's tuned setup, not a search dimension (the firmware
precedent is `tap_on_ms=60 / tap_off_ms=150`, about 4.8 Hz, and #162's screen used
5 Hz; §4 Q1 confirms the value). Two notes on the list:

- **Trim tolerance band is safe to search** because |error| is scored against the
  *settled final reading*, not against "inside the band": widening the band directly
  costs the error objective, so the optimizer cannot game it — it just trades time
  against error along the Pareto front (this is #162 §4.3's "stopping band", which is
  legitimately a decision variable; the *spec* tolerance is not searched). Its floor
  is physical: a band tighter than the single-tap increment (about 6.5 mg mean on
  salt, per #154) cannot be reliably hit and will show up as tap-budget jams.
- **Everything else is frozen** at the hand-tuned values from William's #154 testing —
  PI gains, cutoff margin, k·σ, τ_bal, anticipation, settle times, tap budgets, KF
  noise levels. The frozen snapshot is recorded in the campaign document (§1.3) so
  every trial is reproducible. Prerequisite: export the tuned `trickle_params.py` (and
  any locally modified controller files) off the rig Pico and commit them, so the repo
  baseline *is* the rig baseline (§4 Q2).

### 2.2 Objectives

**minimize ( t_total , |error| )** — true multi-objective (no scalarization), so the
campaign's product is a Pareto front to pick from rather than a single blessed number.

- `t_total` — wall clock from dose start to the *settled final reading* (bulk + trickle
  + taps + final settle; end-to-end, per #162's formulation).
- `abs_error` — |settled final mass − target|, in mg, from the balance at rest.

Ax's multi-objective machinery (qNEHVI under the default Honegumi template) needs
reference thresholds — outcomes worse than these contribute nothing to hypervolume.
Proposed: **t_total ≤ 180 s, |error| ≤ 20 mg** (the tuned controller already beats
10 mg, so 20 mg is a generous outer fence; §4 Q4). Trials run sequentially
(batch size 1) — the rig is serial hardware.

### 2.3 Constraints: no jams, no spills

Both are per-dose binary flags, not modeled objectives:

| Flag | Definition | Detection |
|---|---|---|
| `jam` | Dose could not proceed/finish: stall bail fired, tap nudge/cycle budget exhausted, or `DOSE_TIMEOUT_S` hit | Automatic — the firmware already raises all three |
| `spill` | Powder landed outside the cup | Operator prompt after each dose (v1). Later: mass-balance discrepancy (revolutions × learned feed factor vs Δmass on balance) and/or the webcam; spilled powder is invisible to the balance, so the rig alone can't see it yet |

**Handling in the loop (v1, deliberately rough):** a flagged dose is fed back to Ax
with *penalized* objectives — `t_total` = the timeout ceiling, `abs_error` = the 20 mg
cap (or the true value if worse) — plus the flag stored in the trial document. This
teaches the surrogate that the region is bad without extra machinery (simply marking
the trial failed in Ax would *discard* the information and invite re-suggestion
nearby). Flagged doses are excluded when the feasible Pareto front is read out.
Upgrade path if the box still contains failure regions after screening: a proper
feasibility model (outcome-constrained / SafeOpt-style BO, per #162's synthesis).

**Safety independent of the optimizer** (BO never gets to be the safety system): the
box bounds themselves come from range-finding and the screen (tilt/RPM combinations
that spill or flood are cut out of the box, not left for penalties to discourage); the
firmware keeps its hard aborts (`DOSE_TIMEOUT_S`, `TRICKLE_RPM_CAP`, stall bail,
overshoot-abort if mass exceeds goal + guard); and campaign sessions are supervised
with a hand near `!` / power, as the #154 README already prescribes.

### 2.4 Campaign order — screening first, then BO

Per powder (no powder properties provided or modeled in v1 — each powder is an
independent campaign; the schema still stamps `powder_id` everywhere so later
cross-powder modeling needs no migration):

1. **Range-finding (about 5 manual doses).** Bracket each continuous box: tilt just
   above no-flow, just below spill/flood; confirm the RPM band. Sets the §2.1 boxes.
2. **Screening (about 20 doses)** — the #162 §5 process, updated to this parameter
   list. Eight factors is too many for the original 2⁴⁻¹, so: **2⁸⁻⁴ resolution-IV
   fraction (16 corners) + 4 center points** ≈ 20 doses, one unattended-ish session.
   The two tap categoricals slot in natively as two-level factors (off/on). Same
   analysis and decision rules as #162 §5.3: main-effect and dispersion ranking (a
   factor inert on both gets fixed at its cheap level and dropped from the BO —
   each dropped dimension saves real doses), failure corners tighten the box, replicate
   scatter (from the centers) calibrates the GP noise, and **all screening doses are
   attached to Ax as existing data** (a Honegumi template toggle), so the BO starts
   warm instead of burning budget on random initialization.
3. **BO phase (30–40 doses).** Honegumi-templated Ax service loop: multi-objective
   qNEHVI, sequential trials, categorical support, existing-data attach. Template
   selections: objective = multi, model = Default, task = single, custom threshold =
   yes, constraints = none (parameter-space), existing data = yes. (William to paste
   the Honegumi sample he generated — §4 Q5 — and we pin `ax-platform` to the version
   the template targets.)
4. **Pareto readout + profile pick.** Plot the feasible front (time vs |error|);
   William picks the operating point (or the knee by default).
5. **Validation (8–10 replicate doses)** at the picked point. Median/p95 |error|,
   median time, P(|error| ≤ 10 mg) get stamped into the `dosing_profiles` document —
   a profile is only marked `validated` after this block.

Total ≈ 65–75 doses per powder; at roughly 1–3 min a dose that is 3–5 supervised
sessions of 45–90 min.

### 2.5 Same amount every dose? Yes.

Issue #164 asks whether we need to dose different amounts to stay safe. Recommendation:
**one fixed target mass for the entire campaign — 0.5 g proposed** (§4 Q3). Reasons:

- **Comparability is the point.** `t_total` and `|error|` are only comparable across
  trials at a fixed target; varying the target makes it a context variable the GP must
  also model, which costs real doses and buys nothing in v1.
- **Safety doesn't come from varying the amount.** The risky events (overshoot, spill,
  jam) are bounded by the box limits, the firmware aborts, and supervision — none of
  which depend on target size. Varying the target would only vary exposure, not risk.
- **The target must comfortably exceed the bulk→trim threshold.** A dose with
  `target < threshold + anticipation` skips the bulk phase entirely (existing firmware
  behavior), which would make parameters 1/3/6 inert on those trials and corrupt the
  model. Rule: `target ≥ max(threshold box) + anticipation + margin`. With the
  proposed threshold box capped at 0.20 g and anticipation 0.05 g, a 0.5 g target
  keeps every trial three-phase. (Searching the threshold up to 0.30 g instead pushes
  the target to 1 g and doubles powder throughput per campaign — William's call, §4 Q3.)

**Session protocol** (the actual safety/consistency mechanics, per dose and per
session): auto-tare before every dose; empty the receiving cup back into the hopper on
a fixed cadence sized against the HR-100A's 102 g capacity and top up the hopper at the
same prompts (feed factor drifts with fill level); log doses-since-empty, hopper
top-up events, and recycle count as covariates (§2.6) so compaction/segregation drift
is diagnosable rather than mystery noise; one powder lot per campaign.

### 2.6 What gets recorded per dose

One `opt_trials` document per dose:

- **Identity:** `campaign_id`, `trial_index`, `powder_id`, `target_g`, `mode`
  (`screen` / `bo` / `validation` / `production`), UTC timestamps, operator, firmware
  git SHA + params-file hash.
- **Parameters:** the 8 searched values *as executed* (echoed back by the Pico, not
  just as commanded) — the frozen snapshot lives once in the campaign document.
- **Outcomes:** `t_bulk_s`, `t_trickle_s`, `t_tap_s`, `t_settle_s`, `t_total_s`;
  settled final mass; signed `error_mg`; `abs_error_mg`; overshoot flag; tap count and
  nudge count; learned feed factor at cutoff.
- **Flags:** `jam` (with reason code: stall / tap-budget / timeout), `spill`
  (operator answer), `aborted`.
- **Covariates:** doses since cup empty, hopper top-up marker, recycle count,
  cup mass before dose.
- **Telemetry:** the per-poll rows (existing 15-column trickle log schema), embedded.

On "relative" times and errors: with target, powder, and rig state fixed and logged,
the raw absolute values *are* the comparable record; normalized forms (s/g dosed,
error as % of target) are derived at analysis time, not stored as primary — storing
raw signed values also preserves the overshoot/undershoot asymmetry that matters for
this rig (dispensing is irreversible).

### 2.7 Why this counts as "rough" on purpose

v1 trades sophistication for dose budget and moving parts: penalties instead of a
feasibility GP; per-powder campaigns instead of contextual transfer; fixed target;
noise handled by Ax's inferred-noise GP plus center-point replicates rather than an
explicit heteroscedastic model. Each has a named upgrade path in #162's doc, and the
data schema is deliberately shaped so none of the upgrades requires re-collecting data.

---

## 3. Code that will need to exist (after this design is agreed)

| Piece | Where it runs | What it is |
|---|---|---|
| Tap-cadence knobs + `RESULT` line | Pico (`trickle_tap/`) | `BULK_TAP` / `TRICKLE_TAP` categorical knobs reusing the `Tap` driver + `main_three_phase` per-phase cadence pattern; one machine-parseable JSON result line per dose; overshoot-abort guard |
| `scripts/opt_dose_capture.py` | Pi Zero | Per-dose executor: params in over serial, dose, telemetry off, spill prompt, spool + Mongo upload, JSON line to stdout (patterned on #131's `characterize_capture.py`) |
| `scripts/opt_campaign.py` | Laptop | Honegumi/Ax ask–tell loop, SSH per trial, screening-block runner, penalization, snapshots, resume, Pareto readout |
| `scripts/dose.py` | Pi Zero | Production dosing from a saved profile (§1.4) |
| Schema/helpers module | shared | Trial/campaign/profile document builders + validation, so Zero and laptop write identical shapes |

Simulation tests will dry-run the campaign loop against the #124 twin (no hardware),
same pattern as `trickle_tap/sim/`.

## 4. Open questions for William

1. **Tap "on" cadence:** what fixed frequency (or on/off ms) is your tuned rig using
   for bulk and PI taps? (Firmware precedent is 60/150 ms ≈ 4.8 Hz.)
2. **Export the tuned baseline:** please pull your current `trickle_params.py` (and any
   locally modified files) off the rig Pico so the frozen snapshot in the campaign
   document matches the rig, and so the search boxes can be centered on your tuned
   values. This is the one hard prerequisite.
3. **Target mass:** 0.5 g with the threshold box capped at 0.20 g, or 1 g with the
   threshold searched to 0.30 g? (§2.5)
4. **Objective thresholds:** happy with 180 s / 20 mg as the hypervolume fence? (§2.2)
5. **Honegumi sample:** paste the generated sample code from the site into the issue so
   the campaign script pins the same `ax-platform` version and template shape.
6. **First powder:** which `powder_id` runs campaign #1?
