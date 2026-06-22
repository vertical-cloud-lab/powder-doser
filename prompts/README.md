# prompts/

Reusable prompts for this project.

## `powder-doser-assembly-prompt.md`

A single, copy-pasteable CAD-generation prompt describing the **most recent
iteration** of the full Powder Doser assembly — every 3D-printed part with
full dimensions, tolerances, the off-the-shelf BOM, and the part-to-part
interaction rules.

It exists to **compare Copilot, CADSmith, and zoo.dev** (Text-to-CAD) on
identical input (issue #104): paste the same prompt into each tool and
compare the generated assemblies.

The dimensions were scraped from the live design history in this repo:
- PR #66 — dual-servo mounting plate + shortened baseplate
- PR #49 — geared / storage / threaded Archimedes auger + stepper pinion
- PR #51 — split tap collar + mount plate
- Issue #48 (comment 4513155870) — the four nozzle variants (v4 is standard)
- zoo.dev attachment `tap collar 3.zip` — most recent tap-collar geometry

Paste the whole file, or just the block between `=== BEGIN PROMPT ===` and
`=== END PROMPT ===` for the cleanest, tool-agnostic test.
