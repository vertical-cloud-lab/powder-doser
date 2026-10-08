# Edison Scientific artifacts — geared-auger design literature review

Submitted in response to [PR #51 comment 4546247154](https://github.com/vertical-cloud-lab/powder-doser/pull/51#issuecomment-4546247154):

> "send a high-effort edison scientific query asking about
> https://github.com/vertical-cloud-lab/powder-doser/issues/48#issuecomment-4513155870.
> Fetch this session, commit all artifacts, and summarize in your comment reply
> with a direct link to the edison md file" — @sgbaird

## Contents

| File | What it is |
|------|------------|
| [`geared-auger.task.json`](./geared-auger.task.json) | Task envelope — queue uuid, job name (`job-futurehouse-paperqa3-high`), endpoint, and the verbatim query string that was submitted. |
| [`geared-auger.answer.md`](./geared-auger.answer.md) | Final formatted answer from Edison (46 KB, ~310 lines, 5 sections + literature-gaps summary). Inline citations + a full numbered bibliography at the bottom. |
| [`geared-auger.references.md`](./geared-auger.references.md) | Notes that paperqa3-high returns its bibliography inside the formatted answer (no separate `references` field on the API response). |

## How it was run

```bash
cd cad/auger-geared
python3 edison_run.py                 # submit + poll to completion (≈45 min)
# or, to fetch an already-queued task:
python3 edison_run.py --fetch <uuid>
```

`edison_run.py` uses the `edison-client` SDK; the prompt is embedded
verbatim in source so future readers can trace exactly what was asked.

## Task details

- Task UUID: `5afb6d0d-8b38-436b-a23c-9184d1c28a83`
- Job: `JobNames.LITERATURE_HIGH` (`job-futurehouse-paperqa3-high`)
- Submitted: 2026-05-26 16:35 UTC
- Status at fetch: `success`, `has_successful_answer = true`
- Answer length: 46 196 characters of `formatted_answer` (markdown)

## Question asked

A verbatim re-statement of the design problem in
[issue #48 comment 4513155870](https://github.com/vertical-cloud-lab/powder-doser/issues/48#issuecomment-4513155870),
augmented with the specific engineering questions surfaced by the v1..v3
review cycle of this PR:

- **(a)** Design and analysis of FDM-printed spur gears for low-torque,
  low-RPM intermittent service (tooth form, pressure angle, face width,
  backlash, wear vs injection-moulded).
- **(b)** Parallel-axis offset drive of vertical metering augers /
  screw feeders — centre-distance / ratio choices, documented failure
  modes when driving a screw feeder through an external gear band.
- **(c)** Single-flight Archimedean screw feeders for cohesive powders
  (xanthan gum, flour, fine ceramic / metal powders) — pitch /
  fin-thickness / clearance / shaft-diameter rules as a function of
  particle d50 and Hausner ratio; comparative accuracy of rotation
  alone vs rotation + solenoid tap vs rotation + vibration motor.
- **(d)** NEMA 11 stepper selection for benchtop metering /
  autotrickler-class dispensers — torque, microstepping, closed-loop
  strategies, typical reductions for 28-32 mm steppers driving a
  vertical screw feeder.
- **(e)** Print-orientation / slicer-setting recommendations for a
  tall (≥180 mm) printed hollow auger with an internal helical fin
  printed without inner-fin support — vertical-single-piece vs
  segment-and-bond trade-offs.

See [`geared-auger.task.json`](./geared-auger.task.json) for the full,
verbatim prompt text.
