# TMS 2027 abstract: submitted and revised

**Meeting:** TMS 2027, 14–18 March 2027. Symposium 075, "Powder Materials Processing and Fundamental
Understanding" (assignment taken from the PR #78 catalog; not yet confirmed against Will's TMS record).

**Title (as submitted):** Auger-Based Powder Dosing as a Mechanistic Probe of Powder Flow Behavior:
Multi-Task Bayesian Calibration and Physics-Based Property Inference

## Revised abstract (2026-10-28, 222 words)

Revised with Sterling and Will for use in the optimization paper (#179, PR #184). Passes
`cringe-filter lint --context paper` (v0.2.0) with 0 findings.

AI-guided alloy design needs small, accurate blends of many different feedstock powders, and an automated powder doser has to be recalibrated each time the powder changes. We frame that recalibration as multi-objective Bayesian optimization (BO) of an open-source auger doser, with dose accuracy, repeatability, dispensing time and accessible dose range as objectives. On table salt, a 42-dose BO campaign found settings that hit a 0.5 g target in 8 of 8 validation doses with a median error of 1.8 mg in 78 s, against 245 s for hand-tuned settings. We have also dosed AlSi10Mg, Al 4047 and two size fractions of Si. Across a 13-powder set, delivered mass spanned a 24-fold range and ranked with literature angle of repose. Because dispensed mass depends on both the actuator settings and the powder, each calibration curve is also a compact probe of cohesion, friction and packing. We therefore treat each powder as a related task, so that a multi-task model can share information across powders and reduce the calibration effort for each new one. In parallel, discrete element simulations with cohesive-frictional contacts and measured particle-size distributions are being developed to infer effective cohesion and friction from dosing data, to be checked against shear-cell and Hall-flow measurements. If dosing response tracks these properties, it may also anticipate downstream behavior such as spreadability and packing uniformity.

### Sources for the numbers

- 42-dose salt campaign, `bo-005` validated 8/8 at 0.5 g, median |error| 1.83 mg, median time 78.4 s:
  [`../data/salt-20260929T014732Z/validation_20261006.md`](../data/salt-20260929T014732Z/validation_20261006.md).
- 245 s hand-tuned baseline, 24-fold delivery range, ranking with literature angle of repose
  (ρ = −0.84): [`../OUTLINE.md`](../OUTLINE.md) §2.
- Powders named: AlSi10Mg and both Si fractions are in the 13-powder set
  ([`../data/powders/versatility_data.csv`](../data/powders/versatility_data.csv)); Al 4047 is one
  production dose in air. 630 bronze has not been dosed yet; Al 6063 is unconfirmed, so neither is named.

### What changed from the submitted version

- Opens with the motivation (alloy design needs many powder blends; the doser is recalibrated for every
  powder). The "calibration curve as a probe" claim moves later, as the reason to treat powders as tasks.
- Adds one sentence with the salt BO result.
- Replaces the run-on precursor sentence with the powders actually dosed.
- Drops inert atmosphere and stainless steel, which haven't been done yet. Add them back as plans if wanted.

## Submitted abstract (from #179)

Dispensed mass from an auger-based powder doser depends on actuator settings and powder properties, so
every calibration curve doubles as a compact probe of cohesion, friction, and packing behavior. We frame
calibration of an open-source doser as AI-driven, multi-objective, multi-task Bayesian optimization, with
objectives of dose accuracy, repeatability, dispensing time, and accessible dose range. Each powder is a
related task—primarily alloy precursors, in elemental or master-alloy form depending on handling
constraints and hazards, dosed under inert atmosphere, alongside feedstocks such as AlSi10Mg and stainless
steel—and multi-task models share information across powders to cut per-powder calibration effort.
Alongside gravimetric parameter sweeps, we are exploring discrete element modeling with cohesive-frictional
contact laws and measured particle-size distributions, enabling inference of effective cohesion and
friction from dosing data, to be checked against shear-cell and Hall-flow measurements. Linking dosing
response to these properties may anticipate downstream behavior such as spreadability and packing
uniformity.

Session transcript: [`session-2026-10-28.md`](session-2026-10-28.md).
Transcript of the recording of the same meeting (49 min, corrected Whisper large-v3):
[`../meetings/2026-10-28-sterling-will.md`](../meetings/2026-10-28-sterling-will.md).
