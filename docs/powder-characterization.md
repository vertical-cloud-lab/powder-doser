# Powder property characterization plan

Issue [#163](https://github.com/vertical-cloud-lab/powder-doser/issues/163).
This document lists the material properties we need to determine for every
powder that has run (or will run) on the doser, why each one is needed, and
how to measure it with equipment we either have or can get cheaply.

## Why characterize at all

The Edison optimization review commissioned for issue #161
([`docs/optimization/edison_artifacts/optimization_review.answer.md`](https://github.com/vertical-cloud-lab/powder-doser/blob/b068e44/docs/optimization/edison_artifacts/optimization_review.answer.md),
PR #162) makes powder characterization a prerequisite of the optimization
campaign, for four distinct reasons:

1. **Context variables for transferable optimization (§4.5, §6.3).** The
   recommended campaign is contextual Bayesian optimization in which powder
   properties — Hausner ratio, d50, bulk density — enter the Gaussian-process
   model as context variables. That is what lets a campaign tuned on one
   powder warm-start the next one instead of starting from scratch. Without
   the property vector, every powder is a brand-new 50–100-trial campaign.
2. **Setting achievable tolerances (§5.4).** The reachable dosing-error floor
   shifts with flowability: free-flowing powders (Hausner ratio near 1.0–1.1)
   permit tight tolerance bands, cohesive ones (HR > 1.4) need wider bands,
   slower trim, and anti-bridging measures. "Any optimizer must be informed
   of these material-dependent limits to avoid setting unachievable targets."
3. **Predicting the feed regime (§3c, §5.2).** In the loss-in-weight feeder
   literature the feed factor (mass per revolution) and the usable operating
   range are predictable from conditioned bulk density. Our battery data
   spans three orders of magnitude in feed factor; bulk density and particle
   size are the leading candidates to explain that spread.
4. **It is step 2 of the pre-optimization protocol (§6.1).** "Characterize
   the powder: measure Hausner ratio, particle size distribution, bulk/tapped
   density, and angle of repose. Record these as context variables."

The battery campaign in issue #116 supplies the *response* side (feed factor,
tap quantum, tilt/speed sensitivity, dose error) for 12 powders under one
frozen parameter set. What is missing is the *predictor* side — the intrinsic
material properties those responses should be regressed against. Two concrete
examples of questions blocked on this data:

- The tap-quantum split (organics tap at 8–10 % of a revolution, inorganic
  salts at 0.5–1 %; n = 4) is currently labeled "composition", but density
  and particle shape are confounded with chemistry. Property data turns the
  hypothesis into a testable regression.
- The silicon pair (−110/+200 vs −325 mesh, a 250× conveying difference from
  particle size alone) is our only controlled property experiment. Measured
  PSDs for all powders make every pair a partially controlled comparison.

## Powders in scope

All 12 powders from the issue #116 uniform battery campaign, plus every
future powder before its first battery run (the 15-element digital-alloy-lab
palette in [`candidate-powders.md`](candidate-powders.md) will inherit this
checklist as an intake form).

| # | `powder_id` | Batch | Battery status (issue #116) |
|---|---|---|---|
| 1 | `salt` | food-safe-2026-08 | Control powder; only one that doses inside ±5 mg; showed 2.7× intra-run feed-factor drift |
| 2 | `white-rice-flour` | food-safe-2026-08 | Conveys slowly (12.8 mg/rev @45°), doses miss by −138 mg |
| 3 | `brown-rice-flour` | food-safe-2026-08 | Essentially does not convey (0.25 mg/rev); excluded from further dose runs |
| 4 | `sodium-alginate` | food-safe-2026-08 | Lowest conveying of the dosing set, −292 mg mean dose error |
| 5 | `calcium-lactate` | food-safe-2026-08 | Fast (198 mg/rev), large tap quantum (20.4 mg/tap) |
| 6 | `carboxymethyl-cellulose` | food-safe-2026-08 | Slow, cohesive, tap-responsive by hand |
| 7 | `xanthan-gum` | food-safe-2026-08 | Fast (161 mg/rev), strong negative RPM dependence (−55 %) |
| 8 | `sodium-sulfate` | metal-2026-08 | Very fast (243.6 mg/rev @90°); anhydrous — aggressive hydrator (up to +127 % mass) |
| 9 | `silicon-110-200` | metal-2026-08 | 75–150 µm cut; 302 mg/rev @90°; first non-salt powder to pass all 1 g doses |
| 10 | `silicon-325` | metal-2026-08 | < 44 µm cut of the same element; essentially does not convey — the controlled particle-size contrast |
| 11 | `alsi10mg` | metal-2026-08 | Gas-atomized spherical alloy; highest feed factor (338.9 mg/rev @90°); visible spread/dusting outside the vessel |
| 12 | `barium-chloride` | metal-2026-08 | A–E valid; G+H excluded — column caked/arched via humidity cycling; dried-powder re-run owed. ⚠ toxic (soluble Ba²⁺) |

(Fumed silica was considered and excluded before testing — see
`docs/battery-runs/skipped-powders.md` on the campaign branches.)

## Properties to determine

### Tier 1 — required for every powder (the BO context vector)

These are the four properties the Edison review names explicitly, plus the
two cheap derived indices and the moisture state that issue #116 proved we
cannot ignore.

| Property | Units | Method (standard) | Equipment | What it feeds |
|---|---|---|---|---|
| Bulk (poured) density ρ_bulk | g/mL | Pour known mass into graduated cylinder, read volume (USP <616> method 1; ASTM B212 for metals) | 25–100 mL class-A graduated cylinder + the lab balance | Feed-factor prediction (mass/rev = fill fraction × flight volume × ρ_bulk); BO context variable |
| Tapped density ρ_tap | g/mL | Tap the same cylinder to constant volume — fixed tap count, e.g. 500 then 750 taps (USP <616>; ASTM B527) | Same cylinder; manual tapping or a printed jig | Input to Hausner/Carr below |
| **Hausner ratio** HR = ρ_tap/ρ_bulk | — | Derived, no extra work | — | The primary flowability context variable; sets expected tolerance floor (§5.4) |
| Carr compressibility index = 100 × (ρ_tap − ρ_bulk)/ρ_tap | % | Derived | — | Redundant with HR but standard in the literature; free to report |
| Particle size distribution (d10 / d50 / d90, span) | µm | Sieve stack for > 45 µm fractions (ASTM B214 for metals); laser diffraction if we can get access; supplier CoA where it exists (AlSi10Mg, Si cuts) | Sieve set (e.g. 45 / 63 / 90 / 125 / 150 / 250 µm) + balance | d50 is a named BO context variable; explains the silicon 250× result |
| Angle of repose | ° | Fixed-funnel onto a flat base, measure heap angle (ISO 4324; ASTM C1444) | Funnel + stand + calipers or a photo with scale | Secondary flowability measure; cheap cross-check on HR |
| Moisture content / hydration state | % w/w | Loss on drying: oven at material-safe temperature to constant mass, or halogen moisture analyzer. For hydrates (BaCl₂·2H₂O, calcium lactate hydrate, Na₂SO₄) record the *hydration state* explicitly, not just free moisture | Drying oven + balance (or moisture analyzer) | Caking/arching risk (proven on barium chloride); explains intra-run drift; defines "as-received" vs "dried" states |

Every Tier-1 property should be measured **in triplicate**, with ambient
temperature and relative humidity recorded alongside, and — for the
hygroscopic powders — in two states: as-received (or as-stored) and after
desiccation, since that is the state difference that killed the barium
chloride dose runs.

### Tier 2 — strongly recommended where applicable

| Property | Method | Applies to | Why |
|---|---|---|---|
| True (skeletal) density ρ_true | Handbook/CoA value for pure compounds; gas pycnometry only if unknown | All (literature lookup is enough for most) | Converts ρ_bulk into packing fraction; needed to de-confound the tap-quantum "organics vs salts" split (mass-based quanta on materials of very different density) |
| Particle shape / morphology | Optical microscopy with scale bar (SEM if accessible); classify sphericity/aspect ratio, note bran fragments, fibers, dendrites | All; highest value for AlSi10Mg (spherical) vs silicon (angular crushed) vs CMC (fibrous) | Shape drives flow at equal size; gas-atomized vs crushed is the biggest shape contrast in the set |
| Water sorption tendency | Simple gravimetric uptake: expose a weighed thin layer to ambient lab air, log mass vs time (the balance can do this unattended) | Xanthan, CMC, alginate, sodium sulfate, barium chloride, flours | Ranks caking risk; sets allowable open-air exposure time per powder; formal DVS only if a collaborator has one |
| Flow function coefficient (FFC) | Ring shear cell (Schulze) or FT4 — **outsource/collaborate only**; do not buy | Priority: the metal batch + xanthan as the cohesive extreme | The review names FFC alongside HR as the flowability axis optimal parameters shift with (§5); HR + angle of repose are our in-house proxies until then |
| Electrostatic charging tendency | Qualitative tier first (clinging to PTFE/printed parts, spread pattern on the cage); Faraday-cup measurement only if it becomes a suspect | AlSi10Mg (observed spread), silicon −325, xanthan | §5 lists electrostatics among the error-floor mechanisms; AlSi10Mg's spillage pattern is our observed symptom |

### Tier 3 — metadata and safety (record once per lot)

| Item | Source |
|---|---|
| Supplier, product/lot number, grade, date opened | Packaging / purchase records ([`candidate-powders-shopping-list.md`](candidate-powders-shopping-list.md)) |
| Storage history: desiccator in/out log, exposure events | Lab log (already required by [`candidate-powders.md`](candidate-powders.md#handling-and-storage)) |
| Hazard data: combustible-dust properties (MIE/Kst class) for Si and AlSi10Mg from SDS/literature; toxicity + waste stream (BaCl₂ → hazardous, sealed container); PPE requirements | SDS; existing practice in issue #116 (half-mask respirator, metal-powder waste stream) |
| CoA particle size / chemistry where the supplier provides it | Supplier CoA (AlSi10Mg, silicon cuts) |

### Rig-derived properties (already measured — keep them as responses)

The battery already measures, per powder: feed factor vs tilt (0/45/90°),
feed factor vs RPM (15–90), pulsation, single-tap quantum + RSD, avalanche
behavior (block B: none of the 12 discharges through a stationary auger),
and closed-loop dose error under the frozen salt-tuned controller. These are
the *outputs* the Tier-1/2 properties should predict; they do not substitute
for the intrinsic measurements, because they are convolved with this auger
geometry, fill level, and the room.

## Per-powder specifics

Handbook true densities are starting values — verify hydration state and lot
CoA before treating them as data.

| Powder | ρ_true (handbook, g/cm³) | Expected flow class | Moisture/hydration risk | Powder-specific notes |
|---|---|---|---|---|
| Salt | 2.17 | Free-flowing granular | Low, but caking on humidity cycling is classic | Highest-value extra: moisture + RH correlation, to explain the 2.7× intra-run feed-factor drift in the 08-06 control run |
| White rice flour | ≈1.5 (starch) | Cohesive fine | Moderate (equilibrium moisture ≈10–13 %) | Standard flour moisture method applies |
| Brown rice flour | ≈1.5 | Very cohesive | Moderate | Characterize even though dosing is excluded — it anchors the non-conveying end of every regression |
| Sodium alginate | ≈1.6 (verify) | Cohesive fine | High (hygroscopic biopolymer) | Only a 50 g jar — use a 10–25 mL cylinder and small aliquots |
| Calcium lactate | ≈1.5 (verify) | Free-flowing crystalline | **Hydrate** — commercial material is typically the pentahydrate; confirm state | Large tap quantum makes it a key point for the quantum-vs-density regression |
| Carboxymethyl cellulose | ≈1.6 | Very cohesive, fibrous | **High** — worst of the food set with xanthan | Fibrous shape worth documenting under the microscope |
| Xanthan gum | ≈1.5 | Very cohesive, very fine | **High** | Cohesive extreme of the set; candidate for the FFC short list |
| Sodium sulfate | 2.66 (anhydrous) | Free-flowing crystalline | **Extreme** — it is a drying agent; hydrates toward decahydrate (up to +127 % mass) | Measure moisture immediately before/after any run; as-received vs exposed states essential |
| Silicon −110/+200 | 2.33 | Free-flowing angular | Low (surface oxidation only) | Verify the actual PSD inside the 75–150 µm nominal cut by sieve; ⚠ combustible dust — record MIE/Kst class from SDS |
| Silicon −325 | 2.33 | Cohesive fine | Low | The PSD (< 44 µm nominal) *is* the experiment — measure it properly; same dust hazard |
| AlSi10Mg | ≈2.67 | Very free-flowing spherical | Low; oxide passivation in moist air | Pull the supplier CoA PSD + chemistry; document sphericity; note charging/spread; ⚠ combustible dust |
| Barium chloride | 3.86 anhydrous / 3.10 dihydrate | Free-flowing crystalline *when dry* | **High in practice** — humidity cycling caked and arched the column | Characterize the **dried** powder (density, PSD, moisture) *before* the owed G+H re-run so the re-run is interpretable; ⚠ toxic — hazardous waste stream, no dry sweeping |

## Protocol and data home

- **When:** before the optimization campaign starts (Edison §6.1 sequence),
  and for barium chloride before its dose re-run. New powders get the
  Tier-1 sheet before their first battery run.
- **Replicates:** n = 3 per property per state; report mean ± SD.
- **States:** as-received/as-stored for all; plus post-desiccation for the
  high-moisture-risk rows above.
- **Environment:** record T and RH at measurement time (same habit as the
  battery runs).
- **Sample budget:** bulk/tapped density in a small cylinder needs 5–20 g
  per replicate depending on ρ_bulk (reusable); mind the scarce lots
  (sodium alginate 50 g) and the metal powders.
- **Data home:** one row per powder × state in
  `data/powder-properties/powder_properties.csv`, keyed by the same
  `powder_id` used in the `battery_runs` MongoDB collection and the
  `data/battery/` directories, so property vectors join cleanly onto the
  campaign responses. Per-lot metadata (Tier 3) in a sibling
  `powder_lots.csv`. Raw worksheets/photos under
  `data/powder-properties/<powder_id>/`.
- **Equipment to acquire (cheap):** class-A graduated cylinders (10, 25,
  100 mL), powder funnel + stand, sieve set spanning 45–250 µm, indicating
  desiccant (already planned), hygrometer at the characterization bench.
  A drying oven or halogen moisture analyzer is the only non-trivial item;
  shear cell and pycnometer are explicitly out of scope (outsource or use
  proxies/literature).

## What this unlocks, concretely

1. The contextual-BO campaign of PR #162 §6.3 gets its context vector
   (HR, d50, ρ_bulk at minimum) for all 12 powders.
2. Tolerance bands per powder can be set from flowability class instead of
   discovered by failed doses (§5.4).
3. Feed factor vs conditioned bulk density regression across three decades
   of feed factor — the strongest external-validity claim available to the
   paper.
4. The tap-quantum composition hypothesis becomes testable (density- and
   shape-corrected).
5. Moisture states stop being a silent confounder: the barium chloride
   caking, the sodium sulfate hydration risk, and salt's intra-run drift
   all become checkable against measured numbers.

## Open questions

- Do we have access (department/collaborator) to laser diffraction, SEM, or
  a shear cell? Each upgrades a Tier-1/2 proxy to a reference method but
  none blocks starting.
- Supplier CoAs for AlSi10Mg and the two silicon cuts — who has the
  paperwork?
- Safe drying temperatures per powder for loss-on-drying (biopolymers
  degrade; BaCl₂·2H₂O releases its water stepwise) — set per-powder before
  the first oven run.
- Should tapped density use a printed tapping jig driven by the spare
  solenoid for repeatability? Nice-to-have; the manual USP method is fine
  for comparability and should be the default.
