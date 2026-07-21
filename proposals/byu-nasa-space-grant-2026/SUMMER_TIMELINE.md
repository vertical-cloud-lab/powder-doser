# Summer 2026 Detailed Timeline --- BYU NASA Space Grant Proposal

Companion to [`proposal.tex`](./proposal.tex). The proposal's
*Timeline & Deliverables* section commits to four high-level summer milestones
(M0--M4) followed by lighter follow-on work in Fall 2026 / Winter 2027. This
document breaks the **May--August 2026 summer block** down into week-by-week
milestones so the M0--M4 goals stay on track.

The summer block runs **Monday May 4, 2026 (Week 1) through Friday August 21, 2026
(Week 16)** --- 16 weeks, aligned with BYU's Spring/Summer terms. The paper is
**drafted in weeks 11--14 and submitted by the end of week 16** so it is in peer
review during the fall, per the proposal commitment.

## Milestone map

| Proposal milestone | Calendar | Weeks | Headline deliverable |
| ------------------ | -------- | ----- | -------------------- |
| **M0 -- Kickoff**            | May 2026                       | 1--2   | Frozen requirements; agentic CAD loop wired end-to-end; BOM ordered |
| **M1 -- Subsystem bring-up** | late May 2026                  | 3--4   | Single-channel module printing & dispensing on the Bambu H2D |
| **M2 -- 4-reservoir prototype** | June 2026                   | 5--8   | $\le 4$-reservoir prototype with bench-tested dispense accuracy |
| **M3 -- Full 30-channel envelope** | July 2026                | 9--12  | All 30 reservoirs integrated; direct printer control closed; cross-contamination data on 5--7 L-PBF powders |
| **M4 -- Summer soft completion** | August 2026                | 13--16 | v0.9 dispenser, open-source release candidate, paper drafted and submitted |

## Week-by-week milestones

### M0 --- Kickoff (May 2026)

- **Week 1 (May 4--8).** Freeze the v1 requirements doc (30 reservoirs,
  $\le\!250$ mL/blend, $\pm 1$ mg per-powder accuracy with a $\pm 0.1$ mg
  stretch, 5--7 representative L-PBF feedstock powders, ambient atmosphere with
  v2-ready inert hooks). Confirm the agentic CAD toolchain (GitHub Copilot
  agent mode, model roster, scriptable CAD environment, component-selection
  tooling) is wired end-to-end on a hello-world part. Open a project board
  with the M0--M4 milestones broken into the weekly items below.
- **Week 2 (May 11--15).** Finalize the BOM via the agentic component-selection
  loop (steppers, load cell + ADC, MCU, structural hardware, powder hoppers).
  Place all long-lead orders. Stand up the H2D print queue and confirm
  build-plate / filament inventory for the summer. Lock in the gravimetric
  test rig (analytical balance + tared catch cup) used for every accuracy
  measurement from M1 onward.

### M1 --- Single-channel bring-up (late May 2026)

- **Week 3 (May 18--22).** Drive the agentic loop to generate the
  single-channel dispensing module (auger or rotating-tube variant, informed
  by the POSE tube precedent). Print v0 on the H2D; smoke-test the motion
  system with a non-hazardous surrogate powder (e.g.\ xanthan gum or
  spherical glass beads).
- **Week 4 (May 25--29).** Add the load-cell feedback loop and dispense
  control firmware. First quantitative dispense-accuracy run on the
  surrogate: target repeatability $\pm 1$ mg over $\ge 50$ doses. Capture
  failure modes (bridging, blow-by, motor stall) and feed them back into the
  next agentic CAD revision.

### M2 --- 4-reservoir prototype (June 2026)

- **Week 5 (June 1--5).** Generate and print the multi-channel frame and
  manifold for the $\le\!4$-reservoir subset. Stand up the per-channel
  electronics fan-out (stepper drivers, load-cell multiplexing).
- **Week 6 (June 8--12).** First end-to-end 4-channel dispense: queued
  recipe in, four sequential gravimetric doses out. Tune the per-channel
  PID/dose-controller until each channel hits the $\pm 1$ mg target on the
  surrogate powder.
- **Week 7 (June 15--19).** Swap the surrogate for the **first real L-PBF
  feedstock powder** (Powder #1, e.g.\ a stainless or Ni-base superalloy).
  Re-tune for the heavier, more cohesive (clumping) flow. Run a 200-dose
  accuracy/repeatability sweep and a first cross-contamination check between
  channels.
- **Week 8 (June 22--26).** Add **Powder #2** (contrasting density / PSD).
  Repeat the 200-dose sweep and the channel-to-channel contamination check.
  Write up the M2 bench-test memo (data, plots, agentic-loop diary) ---
  this becomes the seed of the paper's results section.

### M3 --- Full 30-channel envelope (July 2026)

- **Week 9 (June 29--July 3).** Generate and print the full 30-reservoir
  frame; integrate the remaining channels in batches of $\sim 8$. Validate
  mechanical alignment and per-channel motion before any powder is loaded.
- **Week 10 (July 6--10).** Close the loop on **direct printer control**
  from the agent so a CAD revision can be re-printed without a human in the
  slicer. Run a self-contained agentic-loop demo (spec change $\rightarrow$
  CAD edit $\rightarrow$ slice $\rightarrow$ print $\rightarrow$ measure
  $\rightarrow$ next edit) and log it for the paper.
- **Week 11 (July 13--17).** Load **Powders #3--#5** into the full system.
  Run the full-system gravimetric accuracy sweep ($\ge\!500$ total doses
  across channels) and the formal cross-contamination protocol on all
  five powders. **Start drafting the paper's intro + methods in parallel.**
- **Week 12 (July 20--24).** Add the **stretch Powders #6--#7** if the M3
  schedule permits, otherwise hold at five and lock the dataset. Freeze the
  v0.9 hardware. **Paper: results + figures drafted.**

### M4 --- Soft completion + paper submission (August 2026)

- **Week 13 (July 27--31).** Code/firmware/CAD freeze for the
  open-source release candidate. Tag `v0.9` in the repository. **Paper:
  discussion + broader-impact sections drafted; internal review by Sterling.**
- **Week 14 (August 3--7).** Reproducibility pass: a second person follows
  the released docs to print and bring up a single channel from scratch.
  File the issues uncovered against `v1.0`. **Paper: revisions from
  Sterling's review folded in; pick target venue (e.g.\ HardwareX, *Review
  of Scientific Instruments*, or an AM/SDL-focused venue).**
- **Week 15 (August 10--14).** Final bench-test sweep on the v0.9 release
  candidate with all 5--7 powders for the paper's headline figures.
  **Paper: copy-edit pass + reference check; format for the target venue.**
- **Week 16 (August 17--21).** **Submit the paper** by Friday Aug 21. Cut
  the open-source release candidate (`v0.9.0`) with the paper's exact code
  and CAD revisions tagged. Hand off the Fall integration-test plan
  (ultrasonic atomization $\rightarrow$ L-PBF) so Fall 2026 work can start
  immediately.

## Buffers and risks

- **Slip buffer.** Weeks 8 and 12 are deliberately lighter so that delays in
  M2 (first real powder) or M3 (full 30-channel integration) can be absorbed
  without pushing the paper-submission week.
- **Long-lead parts.** Anything not in hand by the end of Week 2 should be
  re-spec'd to an in-stock alternative via the agentic component-selection
  loop --- the schedule cannot absorb a multi-week shipping delay later.
- **Powder availability.** Powders #3--#7 are needed by Week 11. Confirm
  the lab's powder inventory in Week 1 and order any gaps with M0.
- **Paper venue.** If the chosen venue requires a longer-form manuscript than
  drafted, the discussion section gets the extra page; the M3 dataset is the
  load-bearing contribution and is locked by Week 12.

## How this maps back to the proposal

This document is internal planning; the proposal narrative itself only commits
to the M0--M4 calendar bullets. The week-level milestones above are the
applicant's working schedule for hitting those commitments and are subject to
revision as the agentic CAD loop reveals what is and is not feasible.
