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
- zoo.dev export `tapCollar3.step` — most recent tap-collar geometry (a STEP
  export of the same model previously shared as `tap collar 3.zip`/STL;
  PR #105 comment 4771809554). Measured to verify §8 numbers only — this is a
  text-only prompt, so no file is pasted or attached.

Every part description also carries a short "why it matters" note (and §0.1 is
a how-it-works overview) so the generating tool understands the *function*
each feature serves, not just its dimensions.

Off-the-shelf part dimensions (§5) are transcribed from the component
datasheets (NEMA 11 11HS18-0674S, Tic T500, MG996R, Adafruit 412 /
TAU0730TM solenoid, Ø10 coin ERM, DRV2605L, DRV8871, RP2040 Pico, HX711) so
the prompt is self-contained — no internet lookup is needed, which also
sidesteps vendors that block automated searches.

Paste the whole file, or just the block between `=== BEGIN PROMPT ===` and
`=== END PROMPT ===` for the cleanest, tool-agnostic test.
