# Edison literature review — carousel / turret / paternoster prior art

FutureHouse **Edison** high-effort literature task (`LITERATURE_HIGH`),
dispatched for PR #114 (comment 4801657791, @sgbaird: "Send an Edison query
related to this … High effort literature").

- **Task ID:** `499c6c09-0970-47f9-a7b7-a54ac9bfc090`
- **Status:** `success` (`has_successful_answer: true`)
- **Question:** survey of commercial / open-source / academic rotating
  carousel, turret, tray and paternoster indexing systems for a 50-auger
  vertical powder-doser magazine, with indexing/holding mechanisms and
  concrete recommendations.

## Files

| File | Contents |
|---|---|
| [`carousel-literature-review.md`](./carousel-literature-review.md) | The full formatted answer (survey + comparison table + recommendations + DOI references). |
| [`task_dump.json`](./task_dump.json) | Raw `get_task(...).model_dump()` artifact (query, answer, reasoning, status). |

## One-line summary

Recommended architecture: a **horizontal-axis drum carousel** (CNC
tool-changer style) driven by a stepper through a **self-locking worm
gear**, with **spring-clip auger retention**, **shot-pin station locking**,
and Arduino/Pi-class control — validated by open-source autosamplers
(RotoMate ~$550) and academic stepper-indexed carousels (Holst et al.
patch-clamp 40-pipette carousel; ETH COD carousel). Estimated prototype
BOM **$500–1,100**.

Key takeaways are folded into
[`../carousel-build-parts-list.md`](../carousel-build-parts-list.md) §11.
