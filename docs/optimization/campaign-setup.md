# Optimization campaign: workflow and algorithm design (issue #164)

Design-only document — no campaign code exists yet. It answers the two questions issue
[#164](https://github.com/vertical-cloud-lab/powder-doser/issues/164) asks to settle
before code is written:

1. **The workflow** — which machine runs what, where the user types, where data lands,
   and how optimized parameters get reused for future dosing (§1).
2. **The optimization algorithm** — search space, objectives, constraints, the screening
   start prescribed by [PR #162](https://github.com/vertical-cloud-lab/powder-doser/pull/162),
   dose-amount policy, and what gets recorded per dose (§2).

> **Update 2026-09-22** — William answered §4's open questions in
> [issue #164](https://github.com/vertical-cloud-lab/powder-doser/issues/164):
> tap cadence **2 Hz**, target mass **0.5 g**, thresholds **180 s / 20 mg**
> confirmed, first powder **salt**, tuned baseline committed to PR #154
> (`d21d652`), Honegumi sample provided (`ax-platform==0.4.3`, SOBOL → SAASBO,
> existing-data attach). The answers are folded in below; §4 records them as
> locked decisions. Two additions on his request: §2.8 — τ_afterflow quantified
> as a function of mass rate during screening and saved per powder for the
> filters — and §5, the laptop runbook ("what do I need on my computer to run
> this manually").

> **Clarification, later the same day** — "run this manually" meant manually
> *starting* the loop, not hand-running doses: once launched, the campaign is
> automated end to end (ask → SSH dose → tell → record), and the operator
> supervises rather than operates. §1.2, §2.3, §3, §4 and §5 now say so; the
> interim hand-transcribed ask–tell mode a draft of §5.3 described is dropped.

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
  the dose, capture telemetry, take the settled final reading, write the trial document
  to the SD card **and** MongoDB, print one JSON result line back up the SSH pipe. It is
  fully non-interactive — it never chooses parameters, and every operator interaction
  lives in the laptop loop (§1.2).
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

**The only manual act that runs anything is starting the campaign** (William's
2026-09-22 clarification): once launched, the loop drives itself — ask, dose over
SSH, tell, record, next — with no per-dose typing. User input happens in two
places, both in front of William:

1. **Campaign launch (laptop terminal):**

   ```
   python scripts/opt_campaign.py --powder-id salt --target-g 0.5 \
       --budget 40 [--resume <campaign_id>] [--screen-only]
   ```

   `--powder-id` is the same required slug as #131 (reused consistently so Mongo
   queries pull a powder's whole history across characterization, battery, and
   optimization runs).

2. **Supervision, not operation (same terminal, hands at the rig when asked):**
   between doses the loop shows a short auto-continuing countdown — touch nothing
   and the next dose starts, recorded as "no spill"; press `s` to flag a spill on
   the dose just finished (§2.3), `p` to pause. It hard-blocks only at the §2.5
   cadence prompts (cup emptied back into the hopper, top-up), which genuinely
   need hands at the rig, and it parks itself if several consecutive countdowns
   pass untouched, so a walked-away session pauses rather than dosing unattended.
   Sessions stay supervised by design — operator at or near the rig, hand near
   `!`/power — but a clean session is: launch, cadence hands, watching.

Nothing is typed on the Zero beyond starting/attaching tmux, and nothing on the Pico
beyond what the scripts send.

### 1.3 Where data lands

Everything follows #131's write-local-first rule; Mongo is the queryable ledger.

| Store | Contents |
|---|---|
| `opt_campaigns` (Mongo) | One document per campaign: `campaign_id`, `powder_id`, target mass, search-space definition (boxes + categoricals), **frozen-parameter snapshot** (every `trickle_params` value not being searched — the hand-tuned baseline), firmware git SHA, Ax/Honegumi config, status, and the Ax experiment JSON snapshot (updated as the campaign runs). |
| `opt_trials` (Mongo) | One document per dose (§2.6 field list): parameters, outcomes, flags, per-poll telemetry rows (a dose is a few hundred rows — small enough to embed), session covariates. Written by the Zero at dose completion. |
| `dosing_profiles` (Mongo) | **The product.** One document per (powder, profile): the chosen parameter set, the frozen-parameter snapshot it rides on, provenance (`campaign_id`, date, firmware SHA), and validated performance (median/p95 \|error\|, median time, P(\|error\| ≤ 10 mg) from the §2.4 validation replicates). |
| `powder_models` (Mongo) | One document per `powder_id`: measured physical constants, starting with the §2.8 τ_afterflow fit (τ0, optional rate slope τ1, fit stats, rate range covered, source stop-event count, provenance). Profiles copy in the values they were validated with; future powders append here. |
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
range-finding + the screen (§2.4); the salt-tuned baseline
([#154 `d21d652`](https://github.com/vertical-cloud-lab/powder-doser/pull/154/commits/d21d652763afbd59d9fc42d58fdd127e54c75a8c))
sits inside every box and centers it.

| # | Parameter | Type | Placeholder box | Salt-tuned value | Firmware knob |
|---|---|---|---|---|---|
| 1 | Bulk taps | categorical {off, on @ 2 Hz} | — | off | new — port of `main_three_phase`'s per-phase `tap_on_ms`/`tap_off_ms` into the bulk phase |
| 2 | Trim (PI-phase) taps | categorical {off, on @ 2 Hz} | — | off | new — same machinery during the trickle |
| 3 | Bulk tilt | continuous | 15–40 plate ° | 30.0 | `BULK_TILT_DEG` |
| 4 | Trim tilt | continuous | 10–30 plate ° | 15.0 | `TRICKLE_TILT_DEG` |
| 5 | Tap tilt | continuous | 0–15 plate ° | 10.0 | `TAP_TILT_DEG` |
| 6 | Bulk RPM | continuous | 20–100 auger RPM (ceiling 109) | 55.0 | `BULK_RPM` |
| 7 | Bulk→trim threshold | continuous | 0.05–0.30 g remaining | 0.250 | `TRICKLE_START_REMAINING_G` |
| 8 | Trim tolerance band | continuous | 3–15 mg | 5.0 mg | `TOLERANCE_G` |

Per issue #164, the tap parameters are **on/off only** — the "on" cadence is fixed at
**2 Hz** (William, 2026-09-22): one solenoid cycle per 500 ms, keeping the firmware's
proven 60 ms energize pulse, i.e. `tap_on_ms=60 / tap_off_ms=440` (precedent was
60/150 ≈ 4.8 Hz in `main_three_phase`; #162's screen assumed 5 Hz — both superseded).
Cadence tapping exists as a flow aid for powders that will not feed from rotation
alone; salt flows fine, so the tuned baseline has both off, and the screen learns
whether "on" buys anything on a given powder. Two notes on the list:

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
  every trial is reproducible. The prerequisite is met: the tuned baseline is
  committed as [#154 `d21d652`](https://github.com/vertical-cloud-lab/powder-doser/pull/154/commits/d21d652763afbd59d9fc42d58fdd127e54c75a8c)
  (trickle tilt 15°, bulk tilt 30°, tap tilt 10°, threshold 0.25 g; the file's
  `GOAL_MASS_G = 0.75` was the bench goal — the campaign doses 0.5 g, §2.5). One
  value leaves the frozen set: `TAU_AFTERFLOW_S` becomes a measured per-powder
  quantity (§2.8) rather than the hardcoded 0.30 s guess.

### 2.2 Objectives

**minimize ( t_total , |error| )** — true multi-objective (no scalarization), so the
campaign's product is a Pareto front to pick from rather than a single blessed number.

- `t_total` — wall clock from dose start to the *settled final reading* (bulk + trickle
  + taps + final settle; end-to-end, per #162's formulation).
- `abs_error` — |settled final mass − target|, in mg, from the balance at rest.

Ax's multi-objective machinery needs reference thresholds — outcomes worse than these
contribute nothing to hypervolume. **Confirmed: t_total ≤ 180 s, |error| ≤ 20 mg**
(the tuned controller already beats 10 mg, so 20 mg is a generous outer fence). In the
campaign script these are `ObjectiveProperties(minimize=True, threshold=180.0)` /
`threshold=20.0`. Trials run sequentially (batch size 1) — the rig is serial hardware.

William's Honegumi sample (issue #164, 2026-09-22) fixes the template:
`ax-platform==0.4.3`, a two-step `GenerationStrategy` (SOBOL seed then
`Models.SAASBO` — fully Bayesian SAAS priors, which under a two-objective config
means qNEHVI acquisition over SAAS GPs), and the existing-data `attach_trial`
block, which is exactly the §2.4 screening warm start. Two implementation notes:
with the screening block attached there is little for SOBOL to do, so its
`num_trials` shrinks from the sample's 6 to 2 sanity probes; and SAAS fits are
NUTS-sampled, so `get_next_trial()` takes CPU minutes late in a campaign
(measured in §5) — acceptable at our dose cadence, with plain `Models.MOO`
(MAP GP + qNEHVI) as the drop-in fallback if it drags.

### 2.3 Constraints: no jams, no spills

Both are per-dose binary flags, not modeled objectives:

| Flag | Definition | Detection |
|---|---|---|
| `jam` | Dose could not proceed/finish: stall bail fired, tap nudge/cycle budget exhausted, or `DOSE_TIMEOUT_S` hit | Automatic — the firmware already raises all three |
| `spill` | Powder landed outside the cup | Operator keypress during the between-dose countdown (v1) — an untouched countdown records "no spill", so a clean dose needs no input (§1.2). Later: mass-balance discrepancy (revolutions × learned feed factor vs Δmass on balance) and/or the webcam; spilled powder is invisible to the balance, so the rig alone can't see it yet |

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

1. **Range-finding (about 5 operator-driven doses).** The one genuinely hands-on
   step, before any loop runs: bracket each continuous box by eye — tilt just
   above no-flow, just below spill/flood; confirm the RPM band. Sets the §2.1
   boxes. (Everything after this step is the automated loop, §1.2.)
2. **Screening (about 20 doses)** — the #162 §5 process, updated to this parameter
   list. Eight factors is too many for the original 2⁴⁻¹, so: **2⁸⁻⁴ resolution-IV
   fraction (16 corners) + 4 center points** ≈ 20 doses, one unattended-ish session.
   The two tap categoricals slot in natively as two-level factors (off/on). Same
   analysis and decision rules as #162 §5.3: main-effect and dispersion ranking (a
   factor inert on both gets fixed at its cheap level and dropped from the BO —
   each dropped dimension saves real doses), failure corners tighten the box, replicate
   scatter (from the centers) calibrates the GP noise, and **all screening doses are
   attached to Ax as existing data** (the `attach_trial` block in William's sample),
   so the BO starts warm instead of burning budget on random initialization.
   Screening has a second deliverable: its stop events are the dataset for the
   per-powder τ_afterflow fit (§2.8).
3. **BO phase (30–40 doses).** The Honegumi/Ax service loop exactly as William's
   sample shapes it (§2.2): sequential ask–tell, SAASBO after a short SOBOL step,
   screening data attached. Runs with τ_afterflow frozen at the §2.8 refit value.
4. **Pareto readout + profile pick.** Plot the feasible front (time vs |error|);
   William picks the operating point (or the knee by default).
5. **Validation (8–10 replicate doses)** at the picked point. Median/p95 |error|,
   median time, P(|error| ≤ 10 mg) get stamped into the `dosing_profiles` document —
   a profile is only marked `validated` after this block.

Total ≈ 65–75 doses per powder; at roughly 1–3 min a dose that is 3–5 supervised
sessions of 45–90 min.

### 2.5 Same amount every dose? Yes.

Issue #164 asks whether we need to dose different amounts to stay safe.
**Confirmed: one fixed target mass for the entire campaign — 0.5 g.** Reasons:

- **Comparability is the point.** `t_total` and `|error|` are only comparable across
  trials at a fixed target; varying the target makes it a context variable the GP must
  also model, which costs real doses and buys nothing in v1.
- **Safety doesn't come from varying the amount.** The risky events (overshoot, spill,
  jam) are bounded by the box limits, the firmware aborts, and supervision — none of
  which depend on target size. Varying the target would only vary exposure, not risk.
- **The target must comfortably exceed the bulk→trim threshold.** A dose with
  `target < threshold + anticipation` skips the bulk phase entirely (existing firmware
  behavior), which would make parameters 1/3/6 inert on those trials and corrupt the
  model. Rule: `target ≥ max(threshold box) + anticipation + margin`. The threshold
  box is capped at 0.30 g (it must contain the tuned 0.250 g); with anticipation
  0.05 g, the worst-case bulk halt is at 0.35 g remaining, so a 0.5 g target leaves
  every trial a real three-phase dose with at least 0.15 g dispensed in bulk.

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
- **Stop events (feeds §2.8):** one row per halt (bulk halt, trickle cutoff):
  rate-at-stop from the KF `r̂` and from the last-2 s poll slope (both #131
  definitions), at-stop mass estimate, settled mass, `afterflow_g`, and the
  `tau_afterflow_s` the dose executed with.
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

### 2.8 τ_afterflow — quantified during screening, saved per powder, used in the filters

The firmware's predictive cutoff halts the trickle when
`m̂ + r̂·τ_afterflow + k·σ ≥ goal − margin`; today `TAU_AFTERFLOW_S = 0.30` is a
hardcoded guess. [PR #131](https://github.com/vertical-cloud-lab/powder-doser/pull/131)'s
stop-response work showed the real value is a per-powder property: **afterflow ≈
τ × (flow at stop)** holds for every powder that flows (pooled over 37 battery stop
events: r = 0.95), with per-powder τ spanning 0.78–1.17 s and salt's dedicated stop
tests pooling to **τ = 0.83 ± 0.04 s** (n = 84) — well above the hardcoded 0.30. Per
William (issue #164, 2026-09-22), the campaign quantifies τ_afterflow **as a function
of mass rate, while the screening is happening**, and saves it per powder for the
filters:

- **Free data — no extra doses.** Every dose emits two stop events at very
  different rates: the bulk halt (high rate — `BULK_RPM` × feed factor, spread
  across the RPM/tilt box by the screen's own design) and the trickle cutoff (low
  rate, at or under `TRICKLE_MAX_RATE_GPS`). The Zero records each as a §2.6
  stop-event row: rate-at-stop (KF `r̂`, with the last-2 s poll slope as
  cross-check — the two #131 definitions), at-stop mass estimate, and
  `afterflow_g` = settled reading − at-stop estimate.
- **The fit.** At screening end (about 40 usable stop events spanning the rate
  range; jam/spill doses excluded), robust-fit the zero-intercept model
  `afterflow(ṁ) = τ0·ṁ + τ1·ṁ²` — equivalently τ(ṁ) = τ0 + τ1·ṁ, the
  "function of mass rate" asked for. If τ1 is insignificant (#131's pooled data
  says a single τ fits well), save the scalar τ0 alone.
- **Where it lives.** The `powder_models` document for that `powder_id` (§1.3),
  refreshed as later stop events accumulate; every trial records the value it
  executed with; the dosing profile copies the value it was validated with.
- **How it is used.** Screening itself runs the tuned baseline untouched
  (τ = 0.30 s — the value William's within-10 mg tuning was validated with;
  changing a frozen parameter mid-baseline would corrupt the screen). At BO
  start the refit τ̂ is frozen in and pushed per dose (`set tau_afterflow_s …`),
  and BO, validation, and production all run on it — a single scalar, so no
  firmware change beyond the knob push (a τ1 slope knob is the upgrade if the
  rate dependence turns out real). The screening → BO controller change is a
  §2.7-style v1 roughness; the 4 screening center points are re-dosed once under
  τ̂ (4 doses) so the warm-start data and the BO regime share an anchor.
- **Known bias, accepted in v1.** Settled-minus-at-stop deltas fold the balance
  lag into τ (#131's caveat: a shared 0.1–0.2 s inflation; the 2026-08-14 drop
  tests put τ_bal near 0.16 s while the firmware believes 0.7). The cutoff's
  margin + k·σ terms absorb constant offsets, and bench-plan test A1 (τ_bal
  measurement) is the clean-up path — the fit is re-runnable from stored
  stop-event rows once τ_bal is pinned.

---

## 3. The code (built 2026-09-22, this PR)

All six pieces exist; the table now points at them:

| Piece | Where it runs | What it is |
|---|---|---|
| [`trickle_tap/`](../../hardware/test-module/firmware/trickle_tap/) firmware additions | Pico | `BULK_TAP` / `TRICKLE_TAP` on/off knobs at the fixed 2 Hz cadence (`TAP_CADENCE_ON_MS=60 / TAP_CADENCE_OFF_MS=440`), cadence-tap machinery in both velocity mode and the PI loop (KF treats taps as noise); one machine-parseable `RESULT {json}` line per dose, aborts included (`res` reprints), with per-phase times, the settled scoring read (`FINAL_SETTLE_MS`), the §2.6 stop-event rows, and the params as executed; `OVERSHOOT_ABORT_G` guard. Sim-tested (`sim/test_trickle_tap.py`, 14 tests) |
| [`scripts/opt_dose_capture.py`](../../scripts/opt_dose_capture.py) | Pi Zero | Per-dose executor, fully non-interactive: probes/boots the runner, pushes `set` lines with echo verification (incl. `tau_afterflow_s`), doses, parses `RESULT`, pulls telemetry, spools to `data/opt/<campaign_id>/` + Mongo upload, one JSON summary line on stdout. SIGHUP-immune; same-uuid re-invocation (or `--fetch`) returns the stored result and never doses twice |
| [`scripts/opt_campaign.py`](../../scripts/opt_campaign.py) | Laptop | The §5.2 loop: pinned `ax-platform==0.4.3` SOBOL→SAASBO template (`--model moo` fallback), explicit 180 s / 20 mg thresholds, §2.4 screening block (2⁸⁻⁴ IV + 4 centers) attached as existing data, τ refit + re-centered anchors, per-trial SSH dose with fetch-on-reconnect, §1.2 countdown/park/cadence prompts, snapshots + `--resume`, `--screen-only`, `--simulate` (dry-run against the #124-derived sim plant), Pareto readout, `--validate-params` replicate blocks that write `dosing_profiles` |
| [`scripts/fit_tau_afterflow.py`](../../scripts/fit_tau_afterflow.py) | Laptop | §2.8 fit: robust median-ratio τ0, quadratic τ1 kept only when \|t\|>2 and n≥10; `powder_models` upsert + local cache; `--plot` diagnostic scatter |
| [`scripts/dose.py`](../../scripts/dose.py) | Pi Zero | §1.4 production dosing from the newest validated profile (Mongo → local cache fallback), full push of frozen snapshot + searched values + τ, logs `mode: "production"` |
| [`scripts/opt_common.py`](../../scripts/opt_common.py) | shared | Schema/helpers: search space, campaign↔firmware parameter translation, jam classification, §2.3 penalization, document builders, Mongo credential resolution (`$MONGODB_URI` → `$PI_MONGODB_URI` → `~/.config/powder-doser/env`), spool + lazy-pymongo upload (stdlib-only for the Zero) |
| [`scripts/check_mongo.py`](../../scripts/check_mongo.py) | anywhere | MongoDB preflight: reports which credential source resolved (never the URI itself), pings the cluster, lists the `powder_doser` collections |

Host-side tests: `scripts/tests/test_opt_dose_capture.py` (executor against a
canned fake-serial Pico). The loop itself dry-runs end to end with
`opt_campaign.py --simulate` — screening → τ fit → anchors → warm-started BO →
Pareto — with no hardware.

Remaining before the first rig dose: upload the updated `trickle_tap/` build to
its own `/trickle_tap` folder on the Pico, **not the root**, after agreeing a
handover with whoever holds the rig (§5.1 item 6; commands in the
[firmware README](../../hardware/test-module/firmware/trickle_tap/README.md)).
The Zero's `scripts/` is already a sparse checkout of this branch (§5.1 item
4, converted 2026-09-23), so it only needs `git pull --ff-only` there.

## 4. Decisions — locked 2026-09-22 (William, issue #164)

The §4 questions in the first draft of this doc are all answered:

1. **Tap "on" cadence: 2 Hz**, both bulk and PI phases (`tap_on_ms=60 /
   tap_off_ms=440`). Cadence tapping is a flow aid for powders that will not feed
   from rotation alone; salt baseline runs with both off.
2. **Tuned baseline: committed** —
   [#154 `d21d652`](https://github.com/vertical-cloud-lab/powder-doser/pull/154/commits/d21d652763afbd59d9fc42d58fdd127e54c75a8c)
   updates `trickle_params.py` with the values that worked well for salt. This is the
   §2.1 frozen snapshot and box center.
3. **Target mass: 0.5 g**, threshold box capped at 0.30 g (§2.5).
4. **Objective thresholds: 180 s / 20 mg** confirmed (§2.2).
5. **Honegumi sample: provided** — `ax-platform==0.4.3`, SOBOL → SAASBO
   `GenerationStrategy`, existing-data `attach_trial` block (§2.2; laptop-side
   verification in §5).
6. **First powder: salt** (`powder_id = "salt"`). Best-studied powder in the ledger:
   #131 gives it a feed factor near 0.113 g/rev, a measured τ_afterflow prior of
   0.83 s (§2.8), and the single-tap increment near 6.5 mg that floors the tolerance
   band box.
7. **New (this round): τ_afterflow** is quantified as a function of mass rate during
   screening and saved per powder for the filters (§2.8).
8. **Operating model (clarified later the same day): the loop is automated — only
   its start is manual.** William launches `opt_campaign.py` from his computer and
   supervises; there is no per-dose human transport layer and no interim
   hand-transcribed mode, so the §3 build-order scripts gate the first campaign
   dose (§5.3 spells out what the loop automates per trial).

---

## 5. Runbook: running this from your computer

"Manually" means what William meant (2026-09-22 clarification): you **start** the
optimization loop by hand from your computer; you never hand-run doses. Two parts:
what you can set up and verify **today** (§5.1 — all of it laptop-side, nothing
depends on unwritten code), and what a campaign session looks like — and automates
— once §3's scripts exist (§5.2–§5.3). There is no interim hand-transcribed mode:
the first campaign dose waits on the three §3 build-order pieces, which are
deliberately small.

The laptop-side stack was verified 2026-09-22 on a clean Linux machine with
**Python 3.12.3**: `pip install ax-platform==0.4.3` resolves to botorch 0.12.0,
gpytorch 1.13, torch 2.14.0, pyro-ppl 1.9.1, numpy 2.5.3, pandas 3.0.6, and
William's issue-#164 sample runs **unmodified** — 5 `attach_trial` rows accepted,
Sobol suggestions instant, SAASBO suggestions 37–47 s each (at 9 completed trials,
2-core CI runner; NUTS refits the model every ask, so expect low minutes per
suggestion late in a 60-trial campaign), Pareto readout and
`save_to_json_file()` both fine.

### 5.1 One-time setup

1. **Python 3.10–3.12 in a venv.** `ax-platform==0.4.3` is a 2024 pin — if the
   system Python is newer than 3.12, make a 3.12 environment
   (`conda create -n doser-opt python=3.12` or a python.org install). Then:

   ```bash
   python -m venv .venv
   source .venv/bin/activate        # Windows: .venv\Scripts\activate
   pip install ax-platform==0.4.3 pymongo
   ```

   Sizing: on Windows/macOS the default torch wheel is CPU-only and the install is
   about 1 GB. On Linux the default wheel bundles CUDA (5.8 GB measured!) — if the
   laptop is Linux without an NVIDIA GPU, run
   `pip install torch --index-url https://download.pytorch.org/whl/cpu` *first*,
   then the line above. No GPU is needed at this problem size.
2. **Smoke-test the optimizer** by running the issue-#164 sample exactly as pasted
   (`python honegumi_sample.py`). The 6 Sobol trials are instant; the 15 SAASBO
   trials cost 40 s to a few minutes each, so let it run 15–30 min (or shrink
   `range(21)`); it should end by printing nothing after
   `get_pareto_optimal_parameters()` — add a `print(pareto_results)` to see the
   front. If it completes, the whole Ax/BoTorch/torch stack is good.
3. **Tailscale path to the rig.** Install the Tailscale app, log into the tailnet,
   and confirm the Zero is visible (`tailscale status`), then
   `ssh <user>@<zero-hostname> echo ok`. Auth is Tailscale SSH via the tailnet
   ACLs — no key files; if it refuses, the ACL needs your device (admin change).
   This is the #131 path, so it likely already works from your machine.
4. **Repo in both places.** Laptop: clone the repo (campaign script + analysis run
   from it). Zero: **done 2026-09-23.** `~/powder-doser` is now a sparse
   checkout of this branch (seen at the PR tip on 2026-09-25), so update it
   with `git pull --ff-only`.  For the record, it was a plain copied tree,
   **not a git checkout**, and was converted in place over SSH with a
   sparse, blob-filtered checkout of `scripts/` alone (sequence verified
   end-to-end 2026-09-23 against a replica of the bench tree). This transfers
   about 80 KiB instead of the repo's full 134 MB — kind to the bench Wi-Fi —
   and only *adds* files: the tracked `scripts/` names and the on-device bench
   scripts are disjoint, `data/`, `handoff/`, and `preflight_*.json` are
   untracked, and everything else on the device sits outside the sparse pattern.
   No `-f` anywhere, so if any of that ever stops being true git refuses
   instead of overwriting:

   ```bash
   ssh <user>@<zero-hostname>
   cd ~/powder-doser
   git init
   git remote add origin https://github.com/vertical-cloud-lab/powder-doser.git
   git sparse-checkout set --no-cone '/scripts/'
   git fetch --depth 1 --filter=blob:none origin claude/issue-164-20260922-1928
   git checkout -t origin/claude/issue-164-20260922-1928
   git log --oneline -1     # expect the PR #166 tip
   ```

   Point it at the PR branch until #166 merges — `origin/main` does not have
   the campaign scripts yet. Afterwards switch once with
   `git fetch --depth 1 origin main && git checkout -t origin/main`; update
   with `git pull --ff-only` either way. `git status` on the Zero will list
   the bench artifacts as untracked (append `data/`, `handoff/`,
   `preflight_*.json` to `.git/info/exclude` to quiet them) and may list the
   device's older `docs/`/`hardware/` copies as modified — expected, and left
   untouched. Pico: see item 6. The §3 build goes to `/trickle_tap`, not the
   root.
5. **MongoDB.** Access is provisioned end-to-end; `opt_common.resolve_mongo_uri`
   looks for a connection string as `$MONGODB_URI`, then `$PI_MONGODB_URI`, then
   the #131 credential file `~/.config/powder-doser/env` — so per host:

   - **Zero: nothing to do.** The env file is in place (mode 600, holding the
     scoped Atlas user — readWrite on `powder_doser` only) and the campaign
     code reads it directly, so credentials survive the non-interactive SSH
     invocations `opt_campaign.py` makes (which read no rc files). `pymongo`
     lives only in `~/powder-doser-venv`, which the SSH executor now prefers
     (`--remote-python`, falling back to `python3`).
   - **Laptop:** export `MONGODB_URI` before a campaign (#131 convention: env
     var only — never in the shell history of a shared machine, never
     committed). Get the value from the Atlas console (Database Access) or
     reuse the Zero's scoped user; GitHub repo secrets cannot be read back out
     of the settings UI. This is optional — without it the laptop-side campaign
     mirror is skipped and the Zero still uploads every trial.
   - **CI / @claude sessions:** already wired. The workflow injects the repo
     secrets `MONGODB_URI` (admin-grade user), `PI_MONGODB_URI` (identical to
     the Zero's scoped user), and `MONGODB_USERNAME`/`MONGODB_PASSWORD`.

   Verify from any host with the preflight (it never prints the URI):

   ```bash
   python scripts/check_mongo.py                # laptop / CI
   ssh <zero> '~/powder-doser-venv/bin/python ~/powder-doser/scripts/check_mongo.py'
   ```

   The four campaign collections (`opt_campaigns`, `opt_trials`,
   `dosing_profiles`, `powder_models`) are created by the first write — no
   Atlas-side setup is needed. Atlas Network Access already admits both
   datacenter (CI) and residential (bench) IPs, so a new laptop IP is unlikely
   to need an allowlist change; if the preflight fails there anyway, that is
   the first thing to check.
6. **The rig is shared.** Other sessions load and run their own firmware on
   the same Pico through the same Zero: the #116/#131 battery runs, and other
   @claude jobs. So:

   - **Pico flash:** this build lives in `/trickle_tap`, never the root, and
     nothing is installed as `main.py`. The battery firmware at the root
     imports the root `config.py`/`main_three_phase.py`, and §3 changed
     `main_three_phase.py`, so a root upload would silently change their
     runs. Upload commands are in the
     [firmware README](../../hardware/test-module/firmware/trickle_tap/README.md).
   - **Executor guards** (`opt_dose_capture.py`, and `dose.py` through it):
     - Takes the same exclusive port lock as `mpremote` and the #116
       `portguard.sh`, and refuses if any other process has the port open.
       That includes the #116/#131 capture scripts, which don't lock.
     - Never sends Ctrl-C to a program it didn't start. It boots its runner
       only from an idle `>>>` prompt, after a clean raw-REPL soft reset, so
       no root module another session imported stays cached.
     - Doses only when `s` reports `firmware: <opt_common.FIRMWARE_ID>`.
     - Anything else ends the dose as `rig-busy`: nothing is dosed, it counts
       as an infra error, and the campaign stops so `--resume` can retry.
       `--takeover` is the operator's explicit override.
   - **People:** agree a handover before a campaign session, and while you
     own the rig leave a `~/RIG-NOTICE-<date>.txt` on the Zero (the #116
     convention). The guards cover machines, not people. For example, an
     unlocked capture script can still open the port in the middle of a dose.

### 5.2 A campaign session (once §3's scripts exist)

Rig on, balance on and warm, hopper loaded with the campaign powder, empty cup on
the pan; then from the laptop:

```bash
python scripts/opt_campaign.py --powder-id salt --target-g 0.5 --budget 40
```

Everything after that is automatic. The loop pauses for a human only at the
cup-empty / hopper-top-up cadence prompts (§2.5); between doses the §1.2 spill
countdown auto-continues and the campaign moves on by itself. `Ctrl-C`, laptop
sleep, or a dropped SSH session are all safe — each dose is atomic on the Zero
(§1.1), and `--resume <campaign_id>` picks up from the Mongo ledger + the Ax JSON
snapshot without re-dosing anything.

### 5.3 What the loop automates, per trial

`opt_campaign.py` is the sample's own ask–tell pattern pointed at the rig instead
of `branin_moo` — the transport layer is code, not the operator:

1. **Ask.** `ax_client.get_next_trial()` → one parameter set; the laptop mints a
   trial UUID.
2. **Dose.** One SSH invocation:
   `ssh <zero> python scripts/opt_dose_capture.py --trial <uuid> --params '<json>'`.
   The Zero pushes the `set` lines, runs `g 0.5`, captures telemetry and the
   settled reading, spools + uploads the trial document, and prints one JSON
   result line. If the pipe drops mid-dose the dose still completes and lands in
   spool/Mongo under that UUID, and the laptop fetches it on reconnect instead of
   re-dosing (§1.1).
3. **Check-in.** The §1.2 countdown — a keypress only to flag a spill or pause;
   the §2.5 cadence prompts block when due.
4. **Tell.** `complete_trial(...)` with the outcomes (penalized per §2.3 if the
   dose was flagged), then `ax_client.save_to_json_file(...)` plus a local CSV
   append — every trial, so a crash at any point loses nothing.

The experiment definition it carries is the sample's, with the real search space
and objectives swapped in:

```python
ax_client.create_experiment(
    name="salt_campaign",
    parameters=[
        {"name": "bulk_tap", "type": "choice", "is_ordered": False,
         "values": ["off", "2hz"]},
        {"name": "trim_tap", "type": "choice", "is_ordered": False,
         "values": ["off", "2hz"]},
        {"name": "bulk_tilt_deg", "type": "range", "bounds": [15.0, 40.0]},
        {"name": "trickle_tilt_deg", "type": "range", "bounds": [10.0, 30.0]},
        {"name": "tap_tilt_deg", "type": "range", "bounds": [0.0, 15.0]},
        {"name": "bulk_rpm", "type": "range", "bounds": [20.0, 100.0]},
        {"name": "trickle_start_remaining_g", "type": "range",
         "bounds": [0.05, 0.30]},
        {"name": "tolerance_g", "type": "range", "bounds": [0.003, 0.015]},
    ],
    objectives={
        "t_total_s": ObjectiveProperties(minimize=True, threshold=180.0),
        "abs_error_mg": ObjectiveProperties(minimize=True, threshold=20.0),
    },
)
```

(Thresholds passed explicitly — the 2026-09-22 verification run confirmed Ax
silently *infers* thresholds when they are omitted, which is not what we want
scoring hypervolume.)
