# Powder-Characterization Experts — Shortlist & Outreach Email Templates

> **Purpose.** Narrow the powder-properties contact catalogue down to the
> people who could *truly* help us **characterize powder for the dynamic
> (DEM / cohesive-frictional) models** behind the auger doser, and give a
> ready-to-send template email for each. Requested by @williamulbz in
> [PR #41](https://github.com/vertical-cloud-lab/powder-doser/pull/41):
> *"look at the contacts in `powder_properties_dem_calibration.answer.md`
> and `08-powder-properties-experts.md` and narrow it down to those who could
> truly be helpful in characterizing powder for our dynamic models. Refer to
> recent dosing tests in
> [#131](https://github.com/vertical-cloud-lab/powder-doser/pull/131) …
> create template emails reaching out to each of the various experts."*
>
> Source pools:
> [`08-powder-properties-experts.md`](08-powder-properties-experts.md) and
> [`edison_artifacts/powder_properties_dem_calibration.answer.md`](edison_artifacts/powder_properties_dem_calibration.answer.md).
> Companion lists:
> [`07-powder-dispensing-outreach-contacts.md`](07-powder-dispensing-outreach-contacts.md)
> (dispensing hardware).

## What we are actually characterizing (from #131)

The [#131](https://github.com/vertical-cloud-lab/powder-doser/pull/131)
`characterize.py` sweeps and the follow-up bench tests define the concrete
measurements the dynamic model has to reproduce and be calibrated against:

1. **Per-rotation vs tap-only yield as a function of tilt angle** — mass
   dispensed per auger revolution, and per single tap, swept across tilt
   angles including steep / near-vertical.
2. **Single-tap dispensed mass with a controlled starting condition** — rotate
   the auger to reset the powder sitting at the lip, then record the mass of
   each successive tap (avalanche-at-the-lip behavior), repeated at multiple
   angles.
3. **Rapid-dose overshoot / in-flight mass** — dispense fast (high tilt, fast
   RPM, tapping while rotating) to a 0.5 g target, cut all actuation, and
   measure the difference between the mass at stop and the settled mass. This
   in-flight + settling term is a direct macroscopic signature of flow
   energy / cohesion.
4. **Scale-noise floor and feedback rate** — the gravimetric noise band and
   sampling frequency that bound how tight closed-loop (MPC/PID) control can
   get ([#124](https://github.com/vertical-cloud-lab/powder-doser/issues/124)).
5. **Powders** — salt / xanthan / flour as cheap, safe surrogates spanning
   free-flowing → cohesive, standing in for the real targets: elemental and
   master-alloy precursors, AlSi10Mg, and stainless steel, dosed under inert
   atmosphere.

The dynamic-model goal (TMS 2027 abstract,
[#78](https://github.com/vertical-cloud-lab/powder-doser/pull/78)) is to
**infer effective cohesion and friction from these dosing curves** using DEM
with cohesive-frictional contact laws and measured particle-size
distributions, **validate against shear-cell and Hall-flow**, and link the
inferred properties to downstream spreadability and packing.

So "truly helpful for characterizing powder for our dynamic models" means
someone who can move the needle on at least one of: **(a)** getting the
particle-scale inputs right (PSD, contact parameters, cohesion model form);
**(b)** DEM of a screw/auger feeder specifically; **(c)** the inverse /
Bayesian calibration that turns dosing curves into cohesion + friction;
**(d)** the bench measurement (shear cell, dynamic rheometry, flowability)
the DEM is validated against.

## The shortlist (and why these, not the whole list)

Twelve entries, grouped by the role they play for the dynamic model. This is
deliberately narrower than
[`08-…md`](08-powder-properties-experts.md): the cuts are listed under
["Deliberately not on this shortlist"](#deliberately-not-on-this-shortlist).

| # | Contact | Role for the dynamic model | Closest lever |
|---|---|---|---|
| 1 | [Bilal El Kassem](#1-bilal-el-kassem) | Inverse calibration — auger dosing | DEM parameters calibrated from **auger dosing** bulk responses |
| 2 | [Hongyang Cheng (GrainLearning)](#2-hongyang-cheng--grainlearning) | Inverse calibration — method/tooling | Bayesian DEM calibration toolbox |
| 3 | [Marco Ramaioli](#3-marco-ramaioli) | Forward model — dosing cohesive powders | DEM + experiment of **dosing** cohesive powder |
| 4 | [Carl Wassgren](#4-carl-wassgren) | Calibration philosophy — feeders | When/how to calibrate contact params vs bulk tests; screw feeders |
| 5 | [Paul Cleary](#5-paul-cleary) | Forward model — screw/auger DEM | Canonical validated screw-conveyor DEM |
| 6 | [Vanessa Magnanimo & Stefan Luding](#6-vanessa-magnanimo--stefan-luding-twente) | Contact-law form — cohesion↔bulk | Cohesive-granular rheology micro→macro |
| 7 | [Thomas Weinhart (MercuryDPM)](#7-thomas-weinhart--mercurydpm) | Software — cohesive DEM + coarse-graining | Open DEM with cohesive laws; dosing co-author |
| 8 | [Fabio Ramos](#8-fabio-ramos) | Inverse — likelihood-free inference | BayesSim inference of friction from macro observations |
| 9 | [Krishna Kumar](#9-krishna-kumar) | Inverse — differentiable surrogates | GNN / differentiable-simulator inverse for granular flow |
| 10 | [Dietmar Schulze](#10-dietmar-schulze) | Validation — shear cell / yield locus | Ring shear tester; the cohesion the DEM is checked against |
| 11 | [Lorenzo Marchetti & Christopher Hulme-Smith](#11-lorenzo-marchetti--christopher-hulme-smith-kth) | Validation — which flow test for metal powder | 8-method flowability comparison (Hall jams on cohesive powder) |
| 12 | [Geoffroy Lumay & Filip Francqui (Granutools)](#12-geoffroy-lumay--filip-francqui-granutools) | Bench instruments — dynamic cohesion | GranuDrum cohesion used for DEM cross-checks |

### Deliberately *not* on this shortlist

Relevant to the broader project but **not** to characterizing powder for the
dynamic model, so held back to keep the ask sharp:

- **Spreadability / powder-bed metrology** (Snow, Reutzel, Haeri, Brika &
  Brailovski, NIST AM Powder Metrology Lab, BAM) — a *downstream* validation
  once the doser-derived properties exist; premature until we have inferred
  cohesion/friction to correlate.
- **Atomization / powder producers** (Iver Anderson, Emma White,
  Habibnejad-Korayem, Equispheres / Carpenter / 6K) — production-route
  provenance, not characterization of our surrogate powders.
- **Standards bodies & TMS symposium organizers** (ASTM B09/F42, MPIF,
  America Makes, symp. 075/059 slates) — venue/standards positioning, a
  separate abstract-feedback thread already noted in
  [`08-…md`](08-powder-properties-experts.md#suggested-next-actions).
- **Software-only / commercial-desk contacts** where an academic entry
  already covers the method (LIGGGHTS/Aspherix, YADE, Lethe, MFiX, Altair
  EDEM). Worth a support ticket when we pick a code, not a research-collab
  email now. MercuryDPM (#7) is kept because it doubles as a cohesive-DEM
  *and* dosing-co-author contact.
- **Redundant methodology co-authors** (Thoeni, Shuku, Fransen, Wilke,
  WaiChing Sun) — same GrainLearning / review lineage as #2 and #6; reach
  them through those groups rather than in parallel.
- **General flowability PIs** (Ghadiri, Hassanpour, Hare, Hrenya, Muzzio,
  Glasser, Schmidt, Bradley/Wolfson) — strong, but overlap the sharper
  metal-powder / cohesion picks (#10–#12); good second-wave contacts.

---

## How to use these templates

Each email below is a ready-to-send draft with placeholders in `[[ ]]`.
Before sending:

1. Fill the shared placeholders once: `[[Your name]]`, `[[role, e.g. undergraduate
   researcher]]`, `[[BYU Vertical Cloud Lab / advisor]]`, `[[link to repo or
   one-page project brief]]`, `[[link to TMS 2027 abstract]]`.
2. **Verify the address at the linked source page** — per the catalogue rule,
   no email addresses are invented here. Where the source only exposes a
   profile/contact page, the `To:` line says so; look up the current address
   there before sending.
3. Keep it short — one specific ask, one offer (co-authorship / acknowledgment
   / open data). All drafts already do this; trim further if needed.

**Shared signature block** (paste at the foot of any template):

```
Best regards,
[[Your name]]
[[role]], BYU Vertical Cloud Lab
Open-source auger powder doser for self-driving-lab alloy discovery
Repo/brief: [[link]]   ·   TMS 2027 abstract: [[link]]
```

---

## 1. Bilal El Kassem

**To:** no public direct email located — reach via RWTH Institute of General
Mechanics / the [KONA paper](https://www.jstage.jst.go.jp/article/kona/38/0/38_2021010/_html/-char/en)
corresponding-author details.
**Why him:** published the single closest precedent to our plan — a
semi-automated DEM parameter-calibration technique that matches simulated to
measured **bulk responses (angle of repose, bulk density, mass flow rate)
extracted from auger dosing experiments** — plus DoE studies of vertical
micro-auger dosing.
**Specifically can help with:** which bulk observables from our tilt/RPM/tap
sweeps are actually identifiable as DEM contact parameters, and how to avoid
the non-uniqueness traps in his calibration workflow.

> **Subject:** Calibrating DEM cohesion/friction from auger-dosing curves — a question on your KONA method
>
> Dear Dr. El Kassem,
>
> I'm [[Your name]], [[role]] at the BYU Vertical Cloud Lab. We're building an
> open-source auger powder doser for a self-driving lab that discovers metal
> alloys, and we're trying to do exactly what your KONA paper demonstrated:
> infer effective cohesion and friction by matching a cohesive-frictional DEM
> to bulk responses measured from dosing.
>
> Our bench data (surrogate powders now — salt, xanthan, flour — moving toward
> AlSi10Mg and stainless) gives per-revolution and per-tap dispensed mass
> across tilt angle, plus a settling/in-flight overshoot term when we stop at a
> target mass. Two questions where your experience would save us months:
>
> 1. Of those observables, which do you find genuinely *identifiable* for
>    contact parameters, and which are redundant or degenerate?
> 2. How did you handle parameter non-uniqueness (e.g. rolling friction vs
>    cohesion trading off) when calibrating from mass-flow data?
>
> Happy to share our data and calibration scripts, and to acknowledge or
> co-author as appropriate. Would a 30-minute call be possible?
>
> [[signature]]

(source: <https://www.jstage.jst.go.jp/article/kona/38/0/38_2021010/_html/-char/en>)

## 2. Hongyang Cheng / GrainLearning

**To:** via <https://people.utwente.nl/h.cheng> (institutional email listed on
profile) and GitHub [`GrainLearning/grainLearning`](https://github.com/GrainLearning/grainLearning).
**Why him:** lead developer of **GrainLearning**, the open-source Bayesian
uncertainty-quantification toolbox for calibrating DEM models — the closest
existing *tooling* match to our inverse-inference plan.
**Specifically can help with:** wiring our multi-task calibration (one task
per powder, shared information across powders) into an iterative-Bayesian-
filtering loop, and quantifying posterior uncertainty on the inferred
cohesion/friction.

> **Subject:** Using GrainLearning for multi-task DEM calibration from powder-dosing data
>
> Dear Dr. Cheng,
>
> I'm [[Your name]], [[role]] at the BYU Vertical Cloud Lab. We built an
> open-source auger doser and are framing its calibration as multi-objective,
> multi-task Bayesian optimization — each powder a related task — with the
> stretch goal of inferring effective cohesion and friction from the dosing
> curves via a cohesive-frictional DEM. GrainLearning looks like the natural
> engine for the inverse step.
>
> Before we commit the integration, could I ask:
>
> 1. Is iterative Bayesian filtering a good fit when the "experiment" is a
>    per-tap / per-revolution mass-flow curve rather than a stress–strain
>    response, and the forward model is a screw-feeder DEM?
> 2. Is there a supported pattern for sharing information across tasks
>    (powders) so we don't recalibrate each from scratch?
>
> Our data and code are open; we'd gladly contribute an auger-dosing example
> back to GrainLearning and acknowledge/collaborate as fits. Could we find 30
> minutes to talk?
>
> [[signature]]

(source: <https://people.utwente.nl/h.cheng>)

## 3. Marco Ramaioli

**To:** no public direct email located — reach via INRAE / Université
Paris-Saclay staff directory (paper: <https://arxiv.org/abs/1410.2886>).
**Why him:** co-author of *"Experiments and Discrete Element Simulation of the
Dosing of Cohesive Powders in a Simplified Geometry"* — the closest published
precedent for our screw-dosing-as-property-probe framing — and of pulse-
inertia micro-dosing of fine cohesive powders.
**Specifically can help with:** sanity-checking that dosing behavior really is
a sensitive-enough probe of cohesion to invert, and how simplified geometry vs
a real auger changes what you can identify.

> **Subject:** Dosing cohesive powders as a probe of cohesion — following your DEM+experiment study
>
> Dear Dr. Ramaioli,
>
> I'm [[Your name]], [[role]] at the BYU Vertical Cloud Lab. Your work
> experimentally and numerically studying the dosing of cohesive powders in a
> simplified geometry is the closest precedent I've found to what we're
> attempting: using an open-source auger doser's calibration curves as a
> compact probe of cohesion and friction, backed by a cohesive-frictional DEM.
>
> Two questions where your judgment would be invaluable:
>
> 1. In your experience, how sensitive is dosed mass (per revolution, per tap)
>    to cohesion for genuinely cohesive powders — sensitive enough to invert
>    reliably, or dominated by geometry?
> 2. What did the simplified geometry buy you in identifiability that a full
>    auger would lose?
>
> I'd be glad to share our bench data and to collaborate or acknowledge as
> appropriate. Might you have time for a short call?
>
> [[signature]]

(source: <https://arxiv.org/abs/1410.2886>)

## 4. Carl Wassgren

**To:** via Purdue profile (email listed) —
<https://engineering.purdue.edu/ME/People/ptProfile?resource_id=11579>.
**Why him:** co-author of the *Powder Technology* perspective on when and how
DEM contact parameters *should* be calibrated against macroscopic experiments,
with deep pharma screw-feeder DEM experience.
**Specifically can help with:** a reality check on our whole calibration
philosophy — whether inferring contact parameters from a feeder is sound or
whether we're overfitting an under-determined model.

> **Subject:** Is calibrating DEM contact parameters from an auger feeder sound? — re your Powder Technology perspective
>
> Dear Prof. Wassgren,
>
> I'm [[Your name]], [[role]] at the BYU Vertical Cloud Lab. We're building an
> open-source auger powder doser and exploring whether its calibration curves
> can be inverted, through a cohesive-frictional DEM, into effective cohesion
> and friction. Your perspective piece on calibrating and applying DEM for
> industrial bulk powder processes is exactly the caution we want before we
> over-invest.
>
> Candidly: is inferring contact parameters from feeder mass-flow data a sound
> idea, or an under-determined one? And from your pharma screw-feeder work,
> which validation experiment (shear cell? angle of repose? drum?) would you
> insist on pairing with the feeder data to keep the calibration honest?
>
> Our data and code are open and I'd value even a brief reply. Would a short
> call be possible?
>
> [[signature]]

(source: <https://engineering.purdue.edu/ME/People/ptProfile?resource_id=11579>)

## 5. Paul Cleary

**To:** via CSIRO staff page — <https://people.csiro.au/C/P/Paul-Cleary>.
**Why him:** co-author of the canonical validated DEM study of screw-conveyor
performance vs laboratory experiments (Owen & Cleary) — the reference for
forward-modeling an auger.
**Specifically can help with:** how to build an auger/screw DEM that actually
matches measured throughput, and which geometric/contact details dominate the
per-revolution yield we measure.

> **Subject:** Matching a screw/auger DEM to measured dosing throughput — building on Owen & Cleary
>
> Dear Dr. Cleary,
>
> I'm [[Your name]], [[role]] at the BYU Vertical Cloud Lab. We're modeling an
> open-source auger powder doser with DEM and validating against bench data —
> per-revolution and per-tap dispensed mass across tilt angle. Your validated
> screw-conveyor DEM study is our starting reference for the forward model.
>
> Where your experience would help most:
>
> 1. Which geometric and contact details most strongly set predicted
>    throughput, so we calibrate the parameters that matter?
> 2. Any pitfalls matching DEM to a small, cohesive, tilted, tapped auger as
>    opposed to a large horizontal conveyor?
>
> Data and code are open; glad to acknowledge or collaborate. Could we talk
> briefly?
>
> [[signature]]

(source: <https://people.csiro.au/C/P/Paul-Cleary>)

## 6. Vanessa Magnanimo & Stefan Luding (Twente)

**To:** via <https://people.utwente.nl/v.magnanimo> and
<https://people.utwente.nl/s.luding> (institutional emails on profiles).
**Why them:** cohesive-granular rheology mapping inter-particle friction and
cohesion (via Bond number) to macroscopic bulk response — and co-authors of
both GrainLearning and the Ramaioli cohesive-dosing study.
**Specifically can help with:** choosing the *form* of the cohesive-frictional
contact law and which dimensionless groups (Bond number, friction) our dosing
data can realistically constrain.

> **Subject:** Which cohesion/friction parameters can dosing data constrain? — a contact-law question
>
> Dear Prof. Magnanimo and Prof. Luding,
>
> I'm [[Your name]], [[role]] at the BYU Vertical Cloud Lab. We're inferring
> effective cohesion and friction for metal-precursor powders from an
> open-source auger doser's calibration curves, using a cohesive-frictional
> DEM. Your work relating particle friction and cohesion (Bond number) to bulk
> rheology — and your role in both GrainLearning and the cohesive-powder dosing
> study — puts you at the exact intersection we're working in.
>
> Our question is about model form: given only bulk dosing observables
> (per-revolution / per-tap mass vs tilt, plus a settling/overshoot term),
> which contact-law parameters or dimensionless groups are realistically
> identifiable, and which should we fix from independent measurement instead?
>
> Data and code are open; happy to collaborate or acknowledge. Might a short
> call work?
>
> [[signature]]

(source: <https://people.utwente.nl/v.magnanimo>)

## 7. Thomas Weinhart / MercuryDPM

**To:** via <https://people.utwente.nl/t.weinhart> and
<https://www.mercurydpm.org/>.
**Why him:** core developer of **MercuryDPM** (open-source DEM with built-in
cohesive contact laws and coarse-graining) and a co-author of the cohesive-
powder dosing study.
**Specifically can help with:** whether MercuryDPM's cohesive contact laws and
coarse-graining are the right open toolchain for a tilted, tapped auger, and
how to extract the bulk fields we measure from the simulation.

> **Subject:** MercuryDPM for a tilted, tapped auger doser — cohesive contact laws + coarse-graining
>
> Dear Dr. Weinhart,
>
> I'm [[Your name]], [[role]] at the BYU Vertical Cloud Lab. We're simulating
> an open-source auger powder doser with cohesive-frictional DEM to infer
> cohesion and friction from dosing curves, and MercuryDPM — with its cohesive
> contact models and coarse-graining tools, and your co-authorship on
> cohesive-powder dosing — looks like a strong open-source fit.
>
> Two practical questions:
>
> 1. Are MercuryDPM's cohesive contact laws appropriate for fine cohesive
>    metal powders in a tilted, tapped screw geometry?
> 2. What's the recommended way to coarse-grain the simulation into the bulk
>    observables we measure (per-revolution / per-tap mass, settling)?
>
> Everything on our side is open source; we'd gladly contribute an example
> back. Could we find time to talk?
>
> [[signature]]

(source: <https://people.utwente.nl/t.weinhart>)

## 8. Fabio Ramos

**To:** via <https://www.sydney.edu.au/engineering/about/our-people/academic-staff/fabio-ramos.html>.
**Why him:** co-author of *"Inferring the Material Properties of Granular Media
for Robotic Tasks"* (ICRA 2020) — likelihood-free Bayesian inference
(BayesSim) of DEM friction/restitution from macroscopic observations, the
closest robotics-side precedent for our inverse plan.
**Specifically can help with:** applying likelihood-free / simulation-based
inference so we don't need a tractable likelihood for the auger DEM, and
handling the sim-to-real gap between DEM and our bench scale.

> **Subject:** Likelihood-free inference of granular friction/cohesion from dosing data — building on BayesSim
>
> Dear Prof. Ramos,
>
> I'm [[Your name]], [[role]] at the BYU Vertical Cloud Lab. Your BayesSim work
> inferring granular contact parameters from macroscopic observations is the
> closest precedent I've found to what we want: inferring effective cohesion
> and friction from an auger doser's mass-flow curves, where the forward model
> (a screw-feeder DEM) has no tractable likelihood.
>
> Two questions:
>
> 1. Would you expect simulation-based / likelihood-free inference to work when
>    the observation is a per-tap / per-revolution mass-flow curve rather than
>    a static grain configuration?
> 2. How did you manage the sim-to-real gap between DEM and physical
>    measurement, which for us shows up as scale noise and settling?
>
> Our data and code are open; glad to collaborate or acknowledge. Could we
> talk briefly?
>
> [[signature]]

(source: <https://www.sydney.edu.au/engineering/about/our-people/academic-staff/fabio-ramos.html>)

## 9. Krishna Kumar

**To:** via <https://www.caee.utexas.edu/people/faculty/faculty-directory/kumar>.
**Why him:** graph-neural-network surrogates and differentiable-simulator
inverse analysis for granular flows — the learned-surrogate route to replacing
expensive DEM sweeps inside the calibration loop.
**Specifically can help with:** whether a differentiable / GNN surrogate can
make our multi-task inverse loop tractable, and how much training data a screw-
feeder surrogate would need.

> **Subject:** Differentiable / GNN surrogates for inverse calibration of an auger-dosing DEM
>
> Dear Prof. Kumar,
>
> I'm [[Your name]], [[role]] at the BYU Vertical Cloud Lab. We're inferring
> cohesion and friction for metal-precursor powders from an open-source auger
> doser, and the bottleneck is that each inverse step needs many expensive DEM
> runs. Your work on GNN surrogates and differentiable-simulator inverse
> analysis for granular flows looks like the way to make that loop tractable.
>
> Two questions:
>
> 1. Is a screw-feeder / dosing process a reasonable target for a differentiable
>    or GNN surrogate, or does the intermittent tapping break the assumptions?
> 2. Roughly how much DEM training data would you expect such a surrogate to
>    need before it's usable in an inverse loop?
>
> Data and code are open; happy to collaborate or acknowledge. Could we find a
> short call?
>
> [[signature]]

(source: <https://www.caee.utexas.edu/people/faculty/faculty-directory/kumar>)

## 10. Dietmar Schulze

**To:** via <https://www.dietmar-schulze.de/contact.html>.
**Why him:** developer of the Schulze Ring Shear Tester (the instrument behind
ASTM D6773) and author of *Powders and Bulk Solids* — the definitive reference
on yield-locus construction and cohesion determination, i.e. exactly the
quantity our DEM-inferred parameters must be validated against.
**Specifically can help with:** how to run and interpret shear-cell
measurements as ground truth for our inferred cohesion, and whether ring-shear
cohesion is even the right comparison for DEM contact-level cohesion.

> **Subject:** Shear-cell cohesion as ground truth for DEM-inferred parameters — a validation question
>
> Dear Dr. Schulze,
>
> I'm [[Your name]], [[role]] at the BYU Vertical Cloud Lab. We're inferring
> effective cohesion and friction for powders from an auger doser via DEM, and
> we plan to validate those inferred values against shear-cell measurements —
> which brings us straight to your ring shear tester and yield-locus method.
>
> Two questions before we invest in shear testing:
>
> 1. For fine, cohesive powders, what's the right way to compare a
>    macroscopic yield-locus cohesion against a DEM *contact-level* cohesion —
>    are they even the same quantity, or a calibratable proxy?
> 2. Any guidance on shear-testing small samples of hazardous alloy precursors
>    under inert atmosphere?
>
> Grateful for any pointers, and happy to acknowledge your input. Would a brief
> exchange be possible?
>
> [[signature]]

(source: <https://www.dietmar-schulze.de/contact.html>)

## 11. Lorenzo Marchetti & Christopher Hulme-Smith (KTH)

**To:** emails published with their paper — `lormar@kth.se`, `chrihs@kth.se`
(verify current at <https://doi.org/10.1016/j.powtec.2021.01.074>).
**Why them:** lead authors of the 8-method comparison of flowability tests on
11 steel/tool-steel powders, showing Hall/Carney funnels jam on cohesive
powders while shear-cell metrics capture stress-state-dependent flow — a
direct caveat for the abstract's Hall-flow validation leg.
**Specifically can help with:** which flow test to trust for our cohesive
metal powders, and whether our planned Hall-flow validation will simply fail
to flow for the fine precursors we care about.

> **Subject:** Which flowability test is meaningful for cohesive metal powders? — re your 8-method comparison
>
> Dear Dr. Marchetti and Dr. Hulme-Smith,
>
> I'm [[Your name]], [[role]] at the BYU Vertical Cloud Lab. We're building an
> auger doser and planning to validate DEM-inferred cohesion/friction against
> both Hall-flow and shear-cell measurements. Your 8-method comparison — where
> Hall/Carney funnels jam on cohesive powders while shear metrics stay
> informative — is a warning we'd rather heed before, not after, we set up the
> validation.
>
> Two questions:
>
> 1. For fine, cohesive metal precursors (moving toward AlSi10Mg and stainless),
>    which of your eight methods would you actually trust as a reference?
> 2. Is Hall flow worth keeping as a validation leg at all, or should we drop
>    it for these powders?
>
> Our data and code are open; glad to acknowledge or collaborate. Might you
> have time for a short reply or call?
>
> [[signature]]

(source: <https://doi.org/10.1016/j.powtec.2021.01.074>)

## 12. Geoffroy Lumay & Filip Francqui (Granutools)

**To:** via <https://www.granutools.com/contact> (Lumay also at University of
Liège GRASP lab).
**Why them:** GranuDrum rotating-drum cohesion metrics widely used for AM
powders and as DEM-calibration cross-checks; co-authors on
DEM-calibration-from-GranuDrum studies — an ideal dual academic/industry
bench-measurement contact.
**Specifically can help with:** a fast, dynamic cohesion measurement to
cross-check the doser-inferred values, complementary to (and quicker than) a
shear cell.

> **Subject:** GranuDrum cohesion as a cross-check for doser-inferred powder properties
>
> Dear Dr. Lumay and Mr. Francqui,
>
> I'm [[Your name]], [[role]] at the BYU Vertical Cloud Lab. We're inferring
> effective cohesion and friction for powders from an open-source auger doser,
> validated against shear-cell and Hall-flow. We'd also like a fast, dynamic
> cross-check, and GranuDrum — plus your published DEM-calibration-from-
> GranuDrum work — looks ideal.
>
> Two questions:
>
> 1. How well do GranuDrum cohesion indices correlate with the shear-cell
>    cohesion we plan to use as ground truth?
> 2. Could a GranuDrum measurement serve as an independent check on the
>    cohesion our doser+DEM infers for the same powder?
>
> Happy to share data and to explore a short evaluation or collaboration.
> Could we set up a brief call?
>
> [[signature]]

(source: <https://www.granutools.com/contact>)

---

## Suggested send order

1. **Start with the two closest methodological precedents:**
   [El Kassem](#1-bilal-el-kassem) (auger-dosing DEM calibration) and
   [Hongyang Cheng](#2-hongyang-cheng--grainlearning) (GrainLearning) — if
   either engages, much of the inverse plan de-risks at once.
2. **In parallel, one validation-side email:** [Marchetti / Hulme-Smith](#11-lorenzo-marchetti--christopher-hulme-smith-kth)
   or [Schulze](#10-dietmar-schulze), so the shear-cell / Hall-flow validation
   is grounded before we buy or borrow instruments.
3. **Then the forward-model and reality-check contacts** ([Ramaioli](#3-marco-ramaioli),
   [Wassgren](#4-carl-wassgren), [Cleary](#5-paul-cleary),
   [Weinhart](#7-thomas-weinhart--mercurydpm)) once we can show initial DEM
   results to react to.
4. **Hold the ML-inverse contacts** ([Ramos](#8-fabio-ramos),
   [Kumar](#9-krishna-kumar)) until DEM sweeps become the bottleneck — their
   value is in accelerating an already-working loop.

## See also

- [`08-powder-properties-experts.md`](08-powder-properties-experts.md) — the
  full powder-properties catalogue this shortlist is drawn from.
- [`07-powder-dispensing-outreach-contacts.md`](07-powder-dispensing-outreach-contacts.md)
  — dispensing-hardware outreach list.
- [#131](https://github.com/vertical-cloud-lab/powder-doser/pull/131) — the
  characterization sweeps (`characterize.py`) and tap / rapid-dose tests that
  define what the dynamic model must reproduce.
- [#78](https://github.com/vertical-cloud-lab/powder-doser/pull/78) — the TMS
  2027 abstract anchoring the dynamic-model goal.
