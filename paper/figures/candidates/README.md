# Candidate manuscript figures — issue #116 round-1 powder battery

Options to choose between for the Digital Discovery manuscript (PR #97), built
from the round-1 uniform battery in issue #116. **Nothing here is wired into
`main.tex` yet** — pick the panels you want and they get promoted into
`paper/figures/make_figures.py` with the synthetic placeholders removed.

## Rebuilding

```bash
# 1. distil the raw run artifacts into tidy CSVs (only needed if runs are added)
python build_dataset.py /path/to/data/battery      # from a claude/issue-116-* branch

# 2. render every candidate
python make_candidate_figures.py                   # -> out/*.png
```

The tidy CSVs in `data/` are committed (272 kB) so step 2 works from this branch
alone; the raw per-run tree is ~37 MB and lives on the run branches.

## What the dataset actually contains

20 runs, 13 powders, blocks A–G. **14 runs are QC-valid** for cross-powder
comparison; the rest are excluded for a documented reason (servo fault, auger
under suspicion, environment stress test, unverified outlet).

| | Surrogate (food-safe) | Research-relevant |
|---|---|---|
| Powders | NaCl (control), calcium lactate, xanthan gum, CMC, sodium alginate, white rice flour, brown rice flour | AlSi10Mg, Si 110/200 mesh, Si −325 mesh, sodium sulfate, barium chloride, fumed silica |
| Feed factor measured | 6 of 7 | 4 of 6 |
| Closed-loop 1 g doses (block G) | 6 of 7 | 1 of 6 (Si −325, which stalls) |

Three facts constrain what can honestly be plotted:

1. **Feed factor spans >3 decades**, AlSi10Mg 231 mg/rev down to fumed silica
   ≤0.25 mg/rev at 45°, on one auger with one frozen parameter set.
2. **Three powders are censored, not small**: brown rice flour, Si −325 mesh
   and fumed silica conveyed nothing resolvable. They are plotted as upper
   bounds with arrows, never as small numbers.
3. **No research-relevant powder has a valid closed-loop dose.** Every run from
   2026-08-20 on held block G back because the post-fume-hood-move bench
   environment (14–42 mg over 180 s) exceeded the ±5 mg dose band. This is a
   bench limitation, not a powder result — see F2.

## The candidates

| # | Figure | Question it answers | Blocks used |
|---|---|---|---|
| **A1** | `A1_feed_vs_tilt.png` | How does conveyance vary with tilt, per powder, per track? | C |
| **A2** | `A2_feed_rank.png` | What is the full dynamic range of the module? | C |
| **A3** | `A3_tilt_sensitivity.png` | Which powders need gravity assist? | C |
| **B1** | `B1_rsd_vs_feed.png` | Is precision predictable from throughput? | C |
| **B2** | `B2_salt_repeats.png` | Is a run, or a revolution, the experimental unit? | C, E |
| **C1** | `C1_massrev_vs_rpm.png` | What does turning the auger faster buy? | D |
| **C2** | `C2_traces.png` | What does the flow look like in time? | D |
| **D1** | `D1_tap_quantum.png` | What is the finest increment the module can add? | A, E |
| **E1** | `E1_dose_error.png` | How accurate is a closed-loop 1 g dose? | G |
| **E2** | `E2_dose_cost.png` | What does a dose cost, and how does it end? | G |
| **E3** | `E3_phase_effort.png` | Where does the three-phase controller spend effort? | G |
| **F1** | `F1_operating_map.png` | Can two numbers predict whether a new powder is doseable? | C |
| **F2** | `F2_environment.png` | Why do the research powders have no dose data? | A, G |

## Recommendation

**Core figure (pick one of A1 / A2).** A2 is the stronger single panel: it puts
all 13 powders on one log axis, shows the censored powders honestly as bounds,
and makes the 3-decade range the headline. A1 carries more information (the
tilt dependence) and is the better choice if tilt control is being sold as a
design feature — the two are redundant with each other.

**Second figure: F1.** This is the most novel panel in the set. Feed factor and
revolution RSD both come out of block C — about two minutes of bench time — and
together they separate "readily doseable", "slow / fine only" and "not
doseable" without any prior knowledge of the powder. It is the figure that
turns a dispenser into a characterisation instrument, which is the argument
with the longest reach beyond this paper.

**Third figure: E1 + E2 as a two-panel.** This is the honest closed-loop
result: the frozen NaCl-tuned parameter set converges only on NaCl, and every
other powder either stalls or exhausts the fine budget. That is a real,
publishable negative result and it directly motivates the per-powder
auto-calibration framed as future work. E1 alone understates it; E2 shows that
"fast" can mean "stalled in 6 s".

**Fourth figure: C2.** The staircase traces are the most immediately legible
panel here — one slug per revolution, flat plateaus between — and they explain
mechanistically why the tap quantum matters and why RSD scales the way B1 shows.

**Supporting / SI: B2, F2.** B2 answers the round-2 Edison reviewer's central
structural criticism (that six revolutions inside a block are one fill, not six
preparations) and belongs wherever that criticism is addressed. F2 is the
limitations figure; it should accompany any statement about why the alloy
powders have no dose data.

**Probably cut: A3, C1, D1, E3, B1-as-a-main-panel.**

- **A3** is a derived ratio of A1; keep A1 instead.
- **C1** rests on n = 1 per speed with documented carry-over between speeds. The
  trend is interesting (most powders deliver *less* per turn as speed rises,
  i.e. the flights fill by time) but the data will not support a slope. Re-run
  with taring between speeds before publishing it.
- **D1** is a genuine finding — the tap quantum does **not** track the feed
  factor (barium chloride and calcium lactate have nearly identical feed
  factors and 10× different tap quanta) — but it survives on 6 of 13 powders
  because block E is the smallest signal in the battery. Strong SI panel, weak
  main panel.
- **E3** duplicates E2's story with less immediacy.
- **B1** has r² = 0.40; state the relationship in text rather than spending a
  main-text panel on it.

### Splitting general vs research-relevant

Every panel here is either faceted by track (A1), or encodes track by marker
shape and colour (A2, B1, D1, E1, E2, F1). Given that no research-relevant
powder has closed-loop dose data, the honest split for the manuscript is:

- **Main text, all-powder panels** (A2, F1, C2) — the range and the map are the
  contribution, and they need all 13 powders to be impressive.
- **Main text, surrogate-only** (E1/E2) — with an explicit sentence that the
  alloy powders were characterised open-loop only, and why (F2).
- **SI** — B2, D1, F2, and the full per-powder table.

## Caveats carried into every panel

- Feed factor is **collected** mass, not conveyed mass. Powder landing outside
  the beaker is a powder-dependent under-collection that sits underneath the
  whole table (raised in #116 on 2026-08-21). Report as "collected under this
  collection geometry".
- The 2026-08-06 NaCl run is excluded from pooled feed statistics: its block C
  and block E disagree by 2.68× on the same quantity. The gate (C/E ratio in
  0.74–1.12) is reproduced from `scripts/plot_powder_repeats.py` on the run
  branches so these figures pool exactly what the run log pools.
- The 2026-08-11 AlSi10Mg battery ran with the tilt servos dead (plate stuck at
  0°). Its doses are excluded from E1/E2/E3.
- Block E on fumed silica carries a documented solenoid-impulse artifact and is
  never read as a tap quantum.
