The main fix is simple: stop trying to make this a 3-panel synthetic placeholder and make it a compact performance figure that actually proves the hardware works. Right now `fig3_dispense.pdf` is visually clean but scientifically thin. In `make_figures.py`, `fig3()` builds three fully synthetic panels from random generators (`make_figures.py:288–337`), and the caption explicitly says so (`caption_fig3_dispense.md:3`). In the compiled manuscript, this file renders as the dispensing figure on p. 7 of `main.pdf` and is cited as the figure that should demonstrate calibration, closed-loop accuracy, and the coarse-then-trickle rationale. The surrounding text on p. 6–7 of `main.pdf` also promises specific targets and methods that the current figure does not show: `±5%` accuracy above `100 mg`, `±10%` at `20 mg`, per-dose times under `30 s`, `n ≥ 10` replicates, A&D `HR-100A` balance read over `RS-232`, median-of-5 filtering, and a `90%` coarse-to-trickle switch. The figure should be redesigned around those claims.

One quick numbering note: the source file is `fig3_dispense.pdf`, but in the compiled `main.pdf` the dispensing characterization appears as **Fig. 4**, while **Fig. 3** is the generative-AI CAD figure on p. 5. I’m treating the file under review as the dispensing figure regardless of that mismatch.

## What is wrong with the current figure

1. **It does not support the manuscript’s claims.**
   The current panels are:
   - cumulative mass vs time,
   - requested vs measured parity,
   - CV vs rpm,
   all generated synthetically in `make_figures.py:293–334`. None shows the `30 s` target, the `90%` switch point, replicate spread, actuation ablations, or the balance noise floor promised in the text.

2. **Panel (c) is the weakest panel and should be replaced.**
   The CV curves are generated from `cv = 0.6 + 0.035 * rpm + noise` with no powder dependence except color (`make_figures.py:326–330`). So all four powders have nearly the same monotonic increase. That means the panel is not measuring powder-specific behavior at all. It also fails to justify “coarse-then-trickle”; it only says “higher rpm worse,” which is too crude.

3. **Panel (b) is the wrong view for the main accuracy claim.**
   A parity plot on log-log axes makes the `±10%` band hard to read. Reviewers will ask “how much error at the low-mass end?” A direct error plot answers that faster.

4. **The figure is under-annotated.**
   There is no mention in-panel of the controller logic described in `main.pdf` p. 7: coarse mode to `90%` target, then trickle mode with tap/vibration bursts and quiet windows `≥0.5 s`.

5. **The synthetic watermark is doing too much.**
   The diagonal “SYNTHETIC DATA” watermark from `make_figures.py:66–81` dominates all three panels. It’s fine as a stopgap, but it makes the figure feel like a draft slide, not a paper figure.

## Prioritized redesign

### Priority 1: Replace the current 3-panel story with a 4-panel performance story

This is the best tradeoff between rigor and implementability. Keep it double-column. Use a `2 × 2` layout, not `1 × 3`.

### Proposed panel layout

**(a) Open-loop calibration: mass-flow rate vs auger speed**  
Replace current panel (a).

- Plot **steady-state mass-flow rate (g s⁻¹)** on y-axis vs **auger speed (rpm)** on x-axis.
- One series per powder, with mean ± SD from replicate runs.
- Add a fitted slope in the linear operating range for each powder.
- Mark the rpm chosen for coarse mode if a single default is used.

Why this is better:
- It turns raw “mass vs time” traces into the calibration actually used by the controller.
- It supports the sentence in `main.pdf` p. 6 that panel (a) “establish[es] per-powder mass-flow calibrations.”

What it needs:
- **New bench data.**
- Likely available code hooks or future inputs may live near branch-tree paths such as `hardware/test-module/firmware/dosing.py`, `hardware/test-module/firmware/scale.py`, `hardware/test-module/analysis/rs232_analysis.py`, and `cad/auger-geared/capacity/auger_capacity_table.csv` from `all_branches_file_tree.txt`.

**(b) Representative closed-loop dose trace with controller annotations**  
New panel.

- Plot **measured mass vs time** for one large target and one small target, ideally stacked in the same panel or as two subtraces.
- Draw:
  - target mass line,
  - `±10%` band for the small-dose example,
  - vertical line at the `90%` coarse-to-trickle switch,
  - symbols or rug marks for tap/vibration bursts,
  - a shaded “quiet window” after actuation.
- Annotate “coarse” and “trickle” regions directly.

Why this is better:
- It directly visualizes the controller described in `main.pdf` p. 7.
- It makes the hardware behavior legible instead of implied.

What it needs:
- **New bench data.**
- Very likely compatible with branch-tree paths `hardware/test-module/firmware/dosing.py`, `hardware/test-module/firmware/sim/sim_rig.py`, and `hardware/test-module/firmware/sim/test_dosing_sim.py` if those contain event timing or controller structure.

**(c) Closed-loop accuracy: absolute or relative error vs requested mass**  
Replace current panel (b).

- Plot **relative error (%)** or **absolute error (mg)** vs **requested mass** on a log x-axis.
- Draw the acceptance limits from the text:
  - `±10%` from `20–100 mg`,
  - `±5%` above `100 mg`.
- Show each powder as a separate color.
- If actuation ablations exist, encode them as marker shapes.

Why this is better:
- It makes the manuscript’s actual performance criterion visible.
- It is much easier to read than a parity plot with a narrow diagonal band.

What it needs:
- **New bench data.**
- This should become the central panel of the figure.

**(d) Per-dose time vs requested mass**  
New panel.

- Plot **time to target (s)** vs **requested mass**.
- Draw a horizontal line at `30 s` because `main.pdf` p. 6 states “per-dose times under 30 s.”
- Optional inset: fraction of time spent in coarse vs trickle mode.

Why this is better:
- It tests a manuscript claim that the current figure completely ignores.
- Hardware papers need throughput, not just accuracy.

What it needs:
- **New bench data.**

## Priority 2: If space allows, add one more panel or inset

If you can afford a fifth small panel or inset, the most valuable addition is:

**Balance noise floor under actuation**
- Histogram, violin, or box plot of mass readings during:
  - idle,
  - vibration only,
  - tap only,
  - active dispensing.
- This directly supports the statement on p. 6 of `main.pdf` that the campaign will report “balance noise under idle and actuated conditions.”

This would likely require **new bench data**, but it is a high-value reviewer-facing panel because it proves the gravimetric loop is not fantasy.

## What to remove

1. **Remove current panel (c) entirely.**
   It is synthetic, powder-nonspecific, and weakly connected to the controller narrative.

2. **Remove the log-log parity plot unless moved to SI.**
   If you really want parity, keep it as SI. In the main text, an error-vs-target plot is better.

3. **Remove or shrink the full-panel watermark.**
   For any remaining placeholder stage, use a small top-right stamp: `PLACEHOLDER — synthetic until bench campaign complete`.

## What can be implemented now with existing assets vs what needs new data

### Implementable now with existing files

Using `make_figures.py` alone:
- Change layout from `1 × 3` to `2 × 2` or `2 × 3`.
- Replace giant diagonal watermark with a corner badge.
- Increase text size and move legend outside data region.
- Add grayscale-safe linestyles and marker shapes.
- Add controller annotations framework to panel templates.
- Reserve space for `30 s`, `±5%`, `±10%`, and `90%` switch guides so the design is ready when data arrive.

### Needs new bench data

- Any publishable replacement for current synthetic traces.
- Calibration curves.
- Dose error distribution across target masses.
- Time-to-target.
- Balance noise floor.
- Actuation ablations.

I cannot recommend keeping any of the current synthetic curves for submission because `caption_fig3_dispense.md` explicitly says they are placeholders and `make_figures.py` confirms they are generated from RNG-driven mock functions.

## Specific code-level improvements to the current figure if you need an interim revision

Grounded in `make_figures.py`:

- `make_figures.py:289–291`: change from `plt.subplots(1, 3, figsize=(DOUBLE_COL_IN, 2.1))` to a taller `2 × 2` layout.
- `make_figures.py:302`: remove the in-panel legend from (a). Put a shared legend above or below the figure.
- `make_figures.py:316–318`: replace the current diagonal parity tolerance band with horizontal acceptance thresholds on an error plot.
- `make_figures.py:324–334`: replace the entire CV-vs-rpm panel.
- `make_figures.py:66–81`: reduce watermark size and opacity, or move to a corner label.
- Add per-panel subtitles that state the metric, not just axes.

## Tightened caption draft

This version assumes the recommended 4-panel redesign:

**Dispensing characterization of the single-channel auger doser on four powders spanning the study flowability range: glass beads (70–110 μm), Al₂O₃ (~50 μm), gas-atomized 316L (15–45 μm), and xanthan gum. Dispensed mass was measured on an A&D HR-100A analytical balance (0.1 mg readability) over RS-232; the closed-loop controller used continuous coarse dosing to 90% of the target, followed by trickle steps with tap/vibration assistance and balance reads accepted only in quiet windows ≥0.5 s after actuation (Methods §3.4). Points and lines show mean values over n ≥ 10 replicates; error bars or shaded bands denote ±1 SD. (a) Open-loop mass-flow calibration versus auger speed for each powder, used to set coarse-mode feed rates. (b) Representative closed-loop dose traces showing the coarse-to-trickle transition and final settling to the target mass. (c) Closed-loop dose error versus requested mass; dashed acceptance limits indicate ±10% from 20–100 mg and ±5% above 100 mg. (d) Time to target versus requested mass; the horizontal guide marks the 30 s throughput target. Controller logic and analysis were specified by the human researchers; firmware implementation was assisted by LLM coding agents and reviewed by the human researchers.**

That last sentence is worth keeping because `pr97_comments.md:23–36` explicitly asks the manuscript to signpost HUMAN vs AI contributions, while also stating that no GUI CAD package was used and the project relied on programmatic CAD plus, late in the project, Zoo Design Studio with its Zookeeper agent. This figure is not a CAD figure, but the attribution convention should still be consistent.

## Short prioritized action list

- **1. Replace current panel (c)** with a time-to-target panel or a controller-trace panel. Current CV-vs-rpm is the least defensible panel.
- **2. Replace parity panel (b)** with error-vs-requested-mass and draw the manuscript’s actual acceptance limits (`±10%`, `±5%`).
- **3. Convert panel (a)** from raw cumulative mass traces to calibration curves used by the controller.
- **4. Add direct controller annotations**: `90%` switch, trickle phase, tap/vibration events, quiet windows.
- **5. Move synthetic status to a small corner label** and stop using the dominant diagonal watermark.
- **6. Revise the caption** to name the powders, the A&D `HR-100A` analytical balance, `n ≥ 10`, and the explicit throughput/accuracy targets.

- Used the compiled `main.pdf` as the authority for what claims the figure must support, even though the source file is named `fig3_dispense.pdf` and renders as Fig. 4 in the PDF.
- Prioritized a `2 × 2` redesign over a `2 × 3` redesign to keep the figure implementable in a double-column RSC layout.
- Recommended replacing the parity plot with an error-vs-target plot because the manuscript’s acceptance criteria are threshold-based (`±5%`, `±10%`) rather than identity-line-based.
- Recommended dropping the synthetic CV-vs-rpm panel because the source code shows it is powder-independent apart from color and therefore not informative.
- Treated branch-tree paths such as `hardware/test-module/firmware/dosing.py`, `scale.py`, `sim/sim_rig.py`, and `rs232_analysis.py` as plausible implementation/data sources only because they appear in `all_branches_file_tree.txt`; I did not claim their contents without access to those files.