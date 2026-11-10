# Draft: BO campaigns that also collect training data for the simulation and the ML models

William asked on #196 (10 Nov 2026): would it work to collect dosing data while running BO campaigns on all the
powders, and use it for the simulation and ML predictions? This is a draft of what that would look like. It builds
on the salt check in [`README.md`](README.md) (run 34), on run 33 ([`../ml-property-dose/`](../ml-property-dose/)),
on the in-house tests of [#205](https://github.com/vertical-cloud-lab/powder-doser/pull/205) and on the plan in
[`OUTLINE.md`](https://github.com/vertical-cloud-lab/powder-doser/blob/ec30713/paper/optimization/OUTLINE.md#L90)
§4. Nothing here has been run.

## In short
* **Yes, if each campaign is run as a "session" on one jar, with fixed blocks around the BO.** The BO doses alone
  aren't enough. Each powder gets its own settings, and the salt check shows that campaign numbers drift with the
  day and with the hopper's fill.
* **A session, in order** (about 5–6 h, half of it unattended, so about one jar per rig day):
  1. the #205 property tests on the same jar;
  2. a fixed opening fingerprint;
  3. a fixed 22-dose screen, the same settings for every powder;
  4. the BO;
  5. validation repeats;
  6. a short closing fingerprint;
  7. a same-day salt reference.
* **Each part feeds a different model:**
  * the fingerprint and the #205 tests feed the property predictor;
  * the screen feeds the forward dose-outcome model;
  * the BO and validation doses feed the multi-task GP;
  * everything feeds the DEM, as calibration targets and checks.
* **A few logging fixes come first:** bulk revolutions from a millisecond clock, the hopper's fill, RH and
  temperature, and jar and auger IDs on every dose.
* **What it can and can't fix.** More doses per powder won't fix what limits the property predictor today: the
  handbook labels and the 12 powders. More jars with measured labels will. So the campaign sessions should go to
  powders chosen to add information (§5). Every other jar should still get the cheap part: fingerprint plus #205
  tests.

## 1. What each part of a session gives the models

| Part of the session | Same settings for every powder? | Property predictor (run 33) | Forward dose-outcome model | Multi-task BO (§4.B2) | DEM (runs 32, q10) |
|---|---|---|---|---|---|
| #205 tests (AoR, densities, wall friction, PSD) | yes | **labels** (inverse) and **inputs** (forward) | inputs | task descriptors | inputs (PSD, wall friction) and held-out checks |
| Opening fingerprint (protocols C, D, E) | yes | **inputs** (inverse) | inputs | task descriptors | calibration targets (stage 3 of Edison q2) |
| Screen (22 fixed doses) | yes | extra inputs: rate at 15° and 40°, 20 and 100 rpm | **training data**: properties → time, error, flow at 22 settings | warm start | checks across tilt × rpm |
| BO doses (14–20) | no | per-session rate surface, afterflow, taps | – | **training data** (the task's own doses) | checks near the optimum |
| Validation repeats (8, plus a dose-range block) | no | repeatability | P(\|error\| ≤ tol) at the recommendation | noise level | – |
| Closing fingerprint (protocol C, 22.5° and 45°) | yes | drift within the session | – | – | – |
| Same-day salt reference | yes | drift between days | – | – | – |

What run 34 adds to this table:
* **The screen is the part of a campaign that compares across powders.** On salt, 11 of 14 BO doses went to one
  corner of the box, so BO doses describe each powder near its own optimum.
* **Campaign rates don't stand in for the fingerprint.** They differed from August's by −16 % and had a speed
  exponent of 0.58 against 0.78. The opening and closing blocks are what tie a session's campaign numbers to its
  fingerprint.
* **Campaign doses add numbers the fingerprint barely measures.** These include the tilt × rpm interaction,
  afterflow and tap release, and repeatability at fixed settings. They are candidates for the "second observable"
  that runs 29 and 33 say the property predictor needs to separate friction from cohesion.

## 2. One session per jar

| Step | What | Time | Powder |
|---|---|---|---|
| 0 | Weigh the jar; log lot, RH and temperature; note the auger and exit (§4.A1) | 5 min | – |
| 1 | #205 tests: heap AoR, bulk and tapped density, tilting plate, PSD from images (tier 1), more if built | 2–2.5 h for tiers 1–2 (#205), mostly hands-on | 10–15 g, mostly returned |
| 2 | Load the hopper to a **fixed mass** (the same for every jar) and log it | 10 min | priming needs 30–40 g (§4.A11) |
| 3 | **Opening fingerprint:** protocol C (6 revolutions at 0, 22.5 and 45°, 30 rpm), D (15, 45, 90 rpm), E (taps after a refeed revolution) | 15–20 min | 3–5 g |
| 4 | **Screen:** the same 22 settings and the same target (0.5 g) for every powder: the 16 corners of the 2⁸⁻⁴ design, 4 centres and the 2 hand-tuned baseline doses | about 1 h, unattended | 11 g into the cup |
| 5 | **BO** (single-task now, multi-task later) | 0.5–1 h, unattended | 7–10 g |
| 6 | **Validation:** 8 repeats at the recommendation, plus a dose-range block at 0.05, 0.5 and 5 g (§4.A4). The 5 g dose has a long bulk phase, which gives a steady-state rate | 0.75–1 h, unattended | 10 g |
| 7 | **Closing fingerprint:** protocol C at 22.5° and 45° only | 5 min | 2 g |
| 8 | Weigh what is left in the hopper; empty and clean | 15 min | – |
| 9 | **Same-day salt reference:** protocol C on the salt jar (§4.A5) | 15 min | salt |

* **Return the cup to the hopper every 10 doses** and log it. In the salt campaign the cup kept everything (up to
  30 g), and the misfit fell about 8 % per 10 g. The trial documents already have `recycle_count` and
  `doses_since_cup_empty` fields for this; both stayed at 0 for salt.
* **Powders that barely convey** (under 50 mg/rev at 45° in Sam's battery: CMC, sodium alginate, both rice
  flours, Si −325 mesh and fumed silica) get steps 0–3 and 8 first. Run a campaign on one only if a few doses at
  the screen's settings finish inside the time cap; the box stops at 40°, where these deliver even less. Their low
  or zero flow is a censored result, as run 33 treats it.
* **The screen's box should stay fixed** across powders for the data's sake, even where a powder's own BO wants
  a different box. If a powder needs a wider box, add its extra doses as BO doses, not screen doses.

## 3. What every dose should log

Most of it is already in the trial document ([`opt_common.build_trial_doc`](https://github.com/vertical-cloud-lab/powder-doser/blob/d14a50d/scripts/opt_common.py#L434-L486)).
Changes:

| Field | Why | Where |
|---|---|---|
| **Bulk spin time from `ticks_ms`**, and the auger's step count | Bulk revolutions come from `time.time()`, which has 1 s resolution on the Pico. That puts mg/rev off by a median 8 % and up to 25 % (run 34) | `main_three_phase.py`, `_run_phase_continuous` |
| `session_id`, `jar_id` / lot, `auger_id` | Ties each dose to its fingerprint, tests and hardware | `opt_campaign.py` campaign document |
| Hopper fill at the session start, and every cup return | Fill level moved the feed factor 1.5–1.8× between sessions (#140) | operator prompt in `opt_campaign.py` |
| RH and temperature | Salt changes above 75 % RH (run 27); the logging is owed (§4.A10) | Pi sensor |
| The balance lag actually used | Afterflow τ includes it, and 0.7 s vs 0.16 s is unresolved (§4.A9) | already in `parameters_executed`; pin it down |
| Telemetry on every dose | 2 of 60 salt doses had none | treat a missing pull as an executor error and retry |
| Whether the lip was dry before the tap endgame (mass in the last trim second) | Tap release depends on it | firmware stop event |

## 4. From logs to training tables

`extract.py` already turns one campaign's trial documents into one row per dose. Generalized, it would build two
tables:

**Jar-session table** (one row per jar per session). This is the table run 33 trains on.
* **IDs:** jar, lot, date, RH, temperature, auger, fill.
* **Properties from #205:** AoR, bulk and tapped density, Hausner ratio, wall friction, d10, d50, d90, aspect ratio.
* **Fingerprint, opening and closing:**
  * mg/rev at 0, 22.5 and 45°, speed exponent, mg per tap, hold;
  * the change between opening and closing.
* **From the campaign:**
  * rate-surface coefficients (level, tilt, speed, tilt × speed) with their errors;
  * afterflow τ;
  * tap release and the fraction of taps with no release;
  * stall fraction.
* **Outcomes:**
  * time and error at each of the 22 screen settings (a fixed-length vector);
  * the recommended settings;
  * median time and P(\|error\| ≤ tolerance) at the recommendation.

**Dose table** (one row per dose): session id, the eight settings, outcomes, and the per-phase numbers of run 34.
This is the multi-task GP's training data.

Rules carried over from run 33:
* **Split by jar, never by dose.** Leave one jar out, and nest every choice inside the fold.
* **Repeats are replicates.** Revolutions and repeats within a session go into a row's mean and its standard
  error, not into extra rows.
* **No-flow outcomes are censored values**, not zeros.

## 5. Which powders, in what order

1. **Salt pilot** (one session). This settles whether campaign rates match the fingerprint when both run in the
   same session. If they match within the per-dose repeatability (6.5–8.7 %), campaign doses can extend that
   session's fingerprint. If not, the difference comes from the method, and campaign doses stay dose-outcome data
   only.
2. **The §4.A3 campaign powders:** AlSi10Mg, 316L, sieved Al 4047 and one elemental precursor. These are already
   planned as full campaigns; run each as a session.
3. **Powders that change one thing at a time,** from run 33 and #205:
   * sieved salt fractions (size only);
   * salt dry and above 75 % RH (moisture only);
   * AlSi10Mg dried, humid, sieved and reused (§4.A8);
   * a spherical and an irregular grade of one alloy (shape only).

   These give the property predictor its most informative rows, and the multi-task BO its closest pairs of tasks.
4. **The battery jars that convey** (7 of 13 at 45°): a session if there is enough powder (at least 50 g),
   otherwise steps 0–4 only (fingerprint plus screen).
5. **Every other jar:** steps 0–3 (tests plus fingerprint), to reach the 25–30 jars run 33 calls for.

That is about 15–20 full sessions and 25–30 jars with tests and fingerprints.

## 6. Cost

| | per jar | 15–20 full sessions | 25–30 jars, tests + fingerprint only |
|---|---|---|---|
| Rig time | 5–6 h (about 3 h unattended) | 3–4 weeks at one session per rig day | 2.5–3 h each |
| Hands-on time | 2.5–3 h | – | 2.5–3 h each |
| Powder | at least 50 g (priming 30–40 g, §4.A11); most of it comes back | – | 15–20 g, plus the priming fill |

* **Salt's campaign as a yardstick.** It took 2.3 h for 42 doses on 29 Sep, unattended, plus 45 min for 18
  validation doses on 6 Oct. That is 153 min of dosing in all.
* **Later campaigns should be shorter.** If the multi-task GP works, each new powder needs 20–25 BO doses instead
  of 42 (Edison q10's target). Its keep-or-drop line is at least 25 % fewer doses than single-task BO.
* **The schedule fits the outline.** Single-task campaigns are already planned for Nov–Jan (§4.D). Turning them
  into sessions adds about 1 h of fixed blocks to each.

## 7. How we'll know it works

| Check | When | Go if |
|---|---|---|
| Campaign rates match the same session's fingerprint | salt pilot | 22.5° bulk rate within 10 % of protocol C, and speed exponents within 0.1 |
| Drift within a session is small | every session | closing fingerprint within 10 % of opening; otherwise flag the session |
| Campaign numbers help the property predictor | after about 15 jar-sessions | leave-one-jar-out error for AoR (or wall friction) drops by at least 10 % when campaign features are added to the fingerprint (run 33's protocol) |
| The screen predicts dose outcomes across powders | after about 10 sessions | the forward model beats "the nearest powder's outcomes" on held-out jars |
| Multi-task BO saves doses | after the four §4.A3 campaigns | at least 25 % fewer doses than single-task BO (§4.B3 benchmark) |
| The DEM twin, calibrated on a session's fingerprint, predicts its screen | after the emulator (q10 gate 1) | screen mg/rev at 15° and 40°, 20 and 100 rpm within the twin's stated discrepancy |

If the property predictor gains nothing from campaign features, sessions still pay for themselves through the
multi-task BO. The paper needs those campaigns either way (§4.A3).

## 8. Open questions for the bench
* Do the jars hold 50 g? If not, which powders get a full session?
* Can the cup be emptied back into the hopper without stopping the campaign, and is that worth the powder's wear?
* Is there a temperature and humidity sensor near the doser that the Pi can read?
* Should the screen's target stay at 0.5 g for all powders, or scale with bulk density so that each dose moves the
  same volume?
