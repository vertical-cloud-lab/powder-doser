# Powders excluded from further battery testing

Operator decision by @swcharles on issue #116, 2026-09-10: the dose-block
campaign (blocks G+H) does **not** re-test powders already established as
non-dispensers. This file is the durable record of that decision, so the
dataset and the manuscript can state *why* these powders are absent from
later blocks rather than leaving the gap to be rediscovered.

| Powder | Basis for exclusion | Data that establishes it |
|---|---|---|
| **Brown rice flour** | Cannot be conveyed by this auger geometry: ≤0.3 mg/rev at every tilt, 72 % of revolutions below balance resolution, hand-crank control agrees (0.095 mg/rev), second independently printed auger reproduces it. | Valid A–E+G run [2026-08-05](2026-08-05-brown-rice-flour-auger2.md) (`conveying-slowly`, 3 × 1 g stalled); two superseded 2026-08-04 runs; operator hand test. |
| **Fumed silica** | Non-dispensing in its 2026-08-21 battery attempt — the extreme cohesion end of the dataset. | Run `20260821T182705Z_fumed-silica` and its [run notes](2026-08-21-fumed-silica.md). |

Related but **not** excluded:

- **Silicon −325 mesh** — also effectively non-dispensing (≤0.12 mg/rev),
  but deliberately re-tested on 2026-09-10 at the operator's request as
  the dose-block lower bound; its stalled G+H doses replicated the
  2026-08-21 result and are recorded valid
  ([notes](2026-09-10-silicon-325-blocks-gh.md)). No further re-tests are
  planned unless the powder or geometry changes.
- **Barium chloride** — stalled all nine G+H doses on 2026-09-10, but as a
  *material-state fault* (hygroscopic caking after ~3 weeks loaded,
  `arching-no-feed`, excluded from comparison), not an intrinsic
  inability. It stays **in** the campaign and needs a re-run with
  dried/broken-up powder
  ([notes](2026-09-10-barium-chloride-blocks-gh-no-feed.md)).

If any excluded powder is ever revisited (different auger geometry, wider
bore, granulated grade), start a fresh run rather than amending these; the
exclusions above are statements about *this* geometry and powder state.
