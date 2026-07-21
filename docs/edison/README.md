# Edison Scientific raw responses

This directory holds the **verbatim** answers returned by the
[Edison Scientific](https://edisonscientific.com/) tasks submitted from PR #2
of this repository, archived here for provenance so future readers can see
exactly what the model said before any of it was paraphrased into the
`README.md` or `docs/manuscript/main.tex`.

| File | Edison `task_id` | `job_name` | Status |
|---|---|---|---|
| `literature-high-powder-dispensing.md` | `86968176-9927-43b4-aa09-e7e4f86855be` | `job-futurehouse-paperqa3-high` | success |
| `analysis-v1-pre-ferris-wheel.md` | `faeecd89-ea28-403b-94f3-c8402a79e78a` | `job-futurehouse-data-analysis-crow-high` | success — superseded by v2 |
| `analysis-v2-corrected-gondola.md` | `844f6123-36b7-4e61-a0f6-c2e357f804b0` | `job-futurehouse-data-analysis-crow-high` | success |
| _generative-CAD lit-review (resubmitted)_ | `f5a27ed3-8530-4102-9e31-5af9bbe9b0e0` | `job-futurehouse-paperqa3-high` | submitted, polling |
| _gantry-only analysis iter 1 of 3_ | `d6e32c46-2774-4477-a060-9993ef51ab10` | `job-futurehouse-data-analysis-crow-high` | submitted, polling |

A previous generative-CAD literature query (`task_id`
`524e7e92-a326-440a-b6fd-f6eb220d9019`) was sent to the **wrong endpoint**
(`api.platform.futurehouse.org`) and ended up cancelled; it has been
resubmitted at the correct Edison endpoint (`f5a27ed3-…`). Iterations 2 and
3 of the gantry-only analysis cycle are queued behind iter 1 because each
iteration's prompt builds on the prior iteration's verbatim answer.

## Submitting / polling tasks

All Edison traffic must go through `https://api.platform.edisonscientific.com`
(the `api.platform.futurehouse.org` endpoint is a different cluster).
`scripts/edison_submit.py` pins the SDK's `service_uri` to the Edison host
and exposes three subcommands:

```bash
export EDISON_API_KEY=...                              # provided by Edison
python scripts/edison_submit.py submit-cad-litreview   # paperqa3-high
python scripts/edison_submit.py submit-analysis 1      # data-analysis-crow-high
python scripts/edison_submit.py poll <task_id>         # status + answer
```

The script embeds the design-context files (README, manuscript, prior
analyses, CadQuery model, DFM checks) inline as fenced code blocks rather
than using `upload_file`, because the chunked-upload endpoint currently 404s
on the Edison cluster.

## How the feedback was applied

The two analysis tasks identified two design-blocking issues with the
"ferris-wheel gondola" geometry that PR #2 had landed:

1. **Kinematic impossibility of push-to-tilt with a fixed sawtooth tooth**
   (`analysis-v2-corrected-gondola.md` §1). The pivot pin translates purely
   horizontally while the tooth is fixed in space; the trough's hooked end-lip
   sits at a fixed radius from the pin, so the pin-to-tooth distance must
   change as the gantry moves in X — i.e. the lip has to plunge through the
   solid tooth. Resolved in the present PR by **replacing the sawtooth +
   hook with a smooth inclined cam track** that the trough's end bumper
   slides up.
2. **Trapped-volume / arching of cohesive powder in an end-over-end tilt**
   (`analysis-v2-corrected-gondola.md` §3). At 45 ° end-over-end tilt, the
   semicircular cross-section + vertical end cap form a 90 ° V-pocket that
   retains 7–26 % of the dose for cohesive powders, and the powder must
   bottleneck through a ~13 mm spill point that is well below typical arching
   diameters. Resolved by **switching the pivot axis from transverse to
   longitudinal** (axis parallel to the trough's long axis L), so the trough
   tilts **sideways** and pours over the full 80 mm long edge where arching
   is impossible.

Two further items from the v1 review (still useful even though the geometry
has since changed) were also adopted:

- The **strike-off bar** is promoted from "optional variation" to a
  baseline-required feature (`analysis-v1-…` §3, `analysis-v2-…` §4); without
  it, dose CV will sit in the 15–30 % range, well above the 10 % CV baseline
  established by Alsenz's positive-displacement-pipette method.
- The **knock / oscillate-against-the-cam** behaviour for breaking bridged
  powder (`analysis-v1-…` §6) and **J-curve plunge trajectory** to avoid
  flat-blunt compaction during the dip step (`analysis-v1-…` §2) are added to
  the README as part of the standard motion sequence.

The literature-high task was used to expand the prior-art and benchmarking
sections of `docs/manuscript/main.tex` with peer-reviewed
references (Bahr ETC 2018, Bahr 2020, Jiang/Cooper PowderBot 2023, Szymanski
A-Lab 2023, Tom et al. *Chemical Reviews* 2024, Yang & Evans 2007, Carruthers
2025, Lunt 2023/2024, Hernandez del Valle 2024, Doloi 2025) and standardised
flowability descriptors (Carr index, Hausner ratio, Freeman FT4).
