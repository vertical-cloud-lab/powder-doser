# Literature: predicting grain size from powder flow data (issue #210)

Issue [#210](https://github.com/vertical-cloud-lab/powder-doser/issues/210) asked for an Edison
Scientific search for "work predicting grain size or grain size distributions based on data",
given the doser's particle flow data and the type of each powder. Two Edison tasks were run on
2026-11-14:

| task | Edison job | task id | answer |
|---|---|---|---|
| Review: inferring particle size or the particle size distribution (PSD) from flow or process data, and how to apply it to the doser's data | `job-futurehouse-paperqa3-high` (`LITERATURE_HIGH`) | `21cd07ad-ac83-4138-9c47-331aa68faaf2` | [`grain_size_from_flow.answer.md`](grain_size_from_flow.answer.md) |
| Precedent check: has anyone inferred particle size from gravimetric feeder or dispenser data? | `job-futurehouse-paperqa3-precedent` (`PRECEDENT`) | `50266324-3372-4acb-921c-37547a9512d4` | [`precedent.answer.md`](precedent.answer.md) |

The exact queries are in [`edison_grain_size.py`](edison_grain_size.py) and at the top of each
answer.

## What Edison found

- **Nobody has published this yet.** Neither task found a method that infers particle size or a
  PSD from a feeder's or dispenser's mass-versus-time data. Every feeder study measured the PSD
  separately (laser diffraction) and used it as an input to predict feeding, the opposite
  direction. In one, two lactose grades with nearly identical PSDs fed differently, so size can't
  be read off the feed factor alone (Jaspers et al. 2025).
- **Closest feeder work (PSD in, feeding behaviour out):** Bostijn et al. 2019 (PLS on 25
  descriptors of 15 powders, including dv50, predicting feed factor and its decay); the Rutgers
  dissertations of Wang 2016 and Li 2020 (Li logged 1 s mass flow for 14 materials, 4 screws and
  6 feed rates); Kobayashi et al. 2024 (feed-factor profile model with D10/D50/D90 as optional
  inputs); Fathollahi et al. 2020 and 2024 (feed-factor trends at 1 Hz used to diagnose
  densification and screw layering).
- **Methods that do recover size, from other signals:** acoustic emission of particle impacts
  (Buttle & Scruby 1990, mean diameter within 10 %; Zhang et al. 2019, single particles mostly
  within 12 %; Zheng et al. 2021, full PSD in pneumatic conveying, each size bin within 4.8 %).
  In geophysics, the sound of river bedload is inverted for its grain-size distribution by
  non-negative least squares (Petrut et al. 2018), and impact-plate signals for d50 (Barrière et
  al. 2015).
- **Physics linking flow to size:** the Beverloo discharge law, W = C ρ_b √g (D − k d)^(5/2),
  including tilted outlets (Sheldon & Durian 2010); clogging statistics against the
  outlet-to-grain ratio D/d (Zuriguel 2014; Thomas & Durian 2015; Gaida et al. 2026).
- **Machine learning from PSD to flowability:** Barjat et al. 2020 (support vector regression on
  the full size and shape distributions, R² of about 0.8 for the flow function coefficient
  FFc); Diaz et al. 2023 (flowability classes, AUC 0.823).
- **Bayesian calibration and data assimilation of granular models:** particle-filter and
  sequential quasi-Monte Carlo calibration of DEM parameters (Cheng et al. 2017, 2018), the
  open-source GrainLearning toolbox (Cheng et al. 2024), BayesSim (Matl et al. 2020), and FLIP
  for robotic powder weighing (Radulov et al. 2025). All of them fix the particle size rather
  than infer it, and several report more than one parameter set that fits. **No study has shown
  particle size to be identifiable from bulk flow data alone.** It is confounded with cohesion,
  friction, shape, density and moisture.

**What Edison recommends for your data:** combine several observables (mass per turn at each
speed and tilt, the statistics of the mass increments, stall and clog frequency against tilt,
mass per tap, outflow during holds, feed factor against fill level, and the Kalman filter's
innovations) in a Bayesian model with priors from each powder's identity. Measure the PSD of 5
to 10 of the 14 powders (laser diffraction or sieving) as ground truth, and validate by leaving
one powder out at a time. The precedent answer suggests a narrower target that is easier to
defend: one size statistic (median size, or fines content) across size fractions of the same
material.

## Notes on the answers (mine, not Edison's)

- **Your data already has one same-material size pair:** silicon −110/+200 mesh (roughly
  75–140 µm) and −325 mesh (under 45 µm). In the target-mass set the coarse cut dosed 1 g to
  within 0.5 mg, while the fine cut stalled after 0.8 mg. That is the design the precedent
  answer recommends, but with only two sizes. More sieve cuts of one powder would make a real
  test.
- **Grain-level shot noise is only measurable for coarse powders.** If grains arrive
  independently, the variance of the mass added in one reading interval is the grain mass times
  the mean mass added. In the 15 rpm single-dispense runs, one interval (0.39 s) adds about
  16 mg of salt or 23 mg of AlSi10Mg. For 0.4 mm salt grains (an assumption) the expected
  standard deviation is about 1 mg, above the balance's 0.1 mg step. For 30 µm AlSi10Mg (also
  assumed) it is about 0.03 mg, below it. For fine powders, any extra variance comes from clumps,
  avalanches, the auger's once-per-turn pulse and balance noise, so it measures agglomerates or
  cohesion rather than grains. Item 2 in section 5.2 of the review assumes the grain-level
  version without a citation; items 4 and 7 there are also uncited extrapolations.
- **Beverloo is a weak handle for an auger.** It describes gravity discharge through an
  orifice. An auger meters by volume: mass per turn is roughly the flight volume times the fill
  fraction times the bulk density, so size enters mainly through bulk density and fill. The
  precedent answer makes the same point. The review also cites Humby et al. 1998 that the size
  term only holds above about 500 µm, which excludes most of these powders.
- Section 3.2 of the review calls Diaz's MAPE = 0.173 result a "feed-factor regression". It is
  a regression of the flow function coefficient FFc (as the review's own table says), not of the
  feeder's feed factor.
- Wang 2016, Li 2020 and Engisch 2014 are Rutgers dissertations, although the reference lists
  label the first two "ArXiv".

## Files

- [`edison_grain_size.py`](edison_grain_size.py): submits, waits for and fetches both tasks.
- [`_task_id.json`](_task_id.json), [`_task_id_precedent.json`](_task_id_precedent.json): task
  ids, jobs and submit times.
- `<task>.answer.md`: each answer as returned. `<task>.references.md`: its reference list.
- `<task>.task.json`: the full verbose task record (agent steps, every evidence excerpt used,
  costs).
- `<task>_files/`: what each trajectory stored on Edison: `list_files.json`, and the evidence
  table the agent wrote (the `.txt` file).

**Not committed: each task's PaperQA document index.** Each trajectory also stored a Python
pickle of every paper it read (`pqa:docs:<task id>`): 95 MB for the review and 174 MB for the
precedent check. They are left out because they contain the full text of copyrighted papers
(the review's has 48 "All rights reserved" notices) and together would more than double the
size of this repo. Anyone with the lab's Edison key can fetch them with
`client.fetch_data_from_storage("<entry id>")`. Only unpickle them in a sandbox, because
unpickling runs code.

| task | entry id | size (bytes) | sha256 |
|---|---|---|---|
| `grain_size_from_flow` | `95bf8d4a-b01d-4edd-9130-9fc9fb16568f` | 95347082 | `a63f090b20291cce725980f311f3a5fc7b5d06454867bd0b022f666877757c65` |
| `precedent` | `97d9990c-ac63-43cc-b215-c0629b78e33d` | 173740907 | `8b801fd373ddcf12c6760bd7aeb0fa83b2214b1ff17828af4f78abdbb4bd75d8` |

The review's pickle, gzipped, was committed in `a3c5ac0` and removed in the next commit.
Squash-merge this branch to keep it out of `main`'s history. [`.gitignore`](.gitignore) keeps
pickles out of future commits.

## Re-running

`edison-client` 0.18 needs Python below 3.14. From the repo root, with
`EDISON_PLATFORM_API_KEY` set:

```bash
python3.13 -m venv /tmp/edison-venv && /tmp/edison-venv/bin/pip install edison-client
/tmp/edison-venv/bin/python data/assimilation/literature/edison_grain_size.py fetch            # both tasks
/tmp/edison-venv/bin/python data/assimilation/literature/edison_grain_size.py fetch precedent  # one task
```

`submit` skips a task whose `_task_id*.json` already exists; delete that file to send a new
query.
