## Overall verdict

**I would reject the present full-length research article, with encouragement to resubmit a narrower, substantially validated study.** The current contribution fits *Additive Manufacturing*’s new **Methods-paper category** better, although that route still requires stronger reproducibility and actual AM-feedstock validation.

I assessed the planned work rather than objecting to the deliberate placeholders. My complete report contains the handling-editor assessment; three simulated, expert-inspired reports using **Laura Cordova, Keith A. Brown and Johannes G. Khinast** as distinct disciplinary lenses; the statistics audit; a **30-item overlap inventory**; an E0–E9 sufficiency assessment; and **18 priority-ranked revisions**.

### Principal findings

- **The central salt comparison largely checks out.** I reproduce time medians of **245.15 s** for hand tuning and **78.40 s** for `bo-005`, a **3.127-fold** ratio, with exact two-sided Mann–Whitney **p = 0.004040**. The reported time-shift and bootstrap intervals also reproduce. These results compare settings in particular sessions; they do not establish BO’s superiority over simpler calibration strategies.
- **Figure 7b contradicts Section 3.6.** The displayed moisture/error panel reports **ρ = 0.35, n = 12**, while the text reports **ρ = 0.87, n = 9**. The supplied SI lacks the response vector and inclusion rule needed to adjudicate these analyses.
- **“No effect” of hand-over margin is unsupported.** The seven jointly successful corners reproduce **Wilcoxon p = 0.578125**, but margin is confounded with day/powder state, and the success-conditioned subset cannot establish equivalence.
- **Two displayed “ok” records fall outside their displayed final bands.** These require an explanation of controller termination versus settled-score classification. The **~55 mg useful-dose threshold** is extrapolated, not experimentally established.
- **The companion shares substantive evidence:** the **8 g/7.993 g AlSi10Mg dose**, Al 4047 obstruction/recovery observations, and the fixed-setting records reanalysed in Figure 7. I found no demonstrable whole-figure/table copying from the available source, but citation alone does not settle scientific redundancy. The apparently same cleared Al 4047 dose is reported at **about 25 mg/s** in the companion versus **30.7/~31 mg/s** here; estimator/window differences need reconciliation. This is an overlap-risk assessment, not a finding of misconduct.

### Smallest defensible experimental package

I recommend **E0–E3 + E5–E6**, strengthened with replicated paired sieved/unsieved measurements, repeat-fill/day checks, and one quantitative AM-facing outcome. **E4 and inverse DEM are not prerequisites** for a focused paper.

If the paper drops dose-range/reliable-minimum-mass claims, omitting the two eight-dose range blocks from each E1–E3 session reduces the planned executor count from **222 to 174**. Repeat fingerprints, state controls and application validation remain additional work. Completing all E0–E9 would not automatically validate every proposed claim—especially cross-powder cohesion inference from a salt-only E8 study.

## Deliverables

- [Complete peer-review panel and audit](/workspace/review_audit/mock_peer_review_and_audit.md)
- [Reproducibility bundle: executed Python, CSV tables, numerical results, source evidence and bibliography](/workspace/review_audit/audit_reproducibility_bundle.zip)
- [Validation and paired-corner audit figure](/workspace/review_audit/audit_overview.png)

**Analytical decisions**
- I retained the manuscript’s defined validation blocks and separately checked the two pre-restart doses; I used tie-aware exact permutations where needed.
- I distinguished confirmed discrepancies from rounding, unauditable claims and legitimate secondary analyses of shared records.
- I favored a narrower controlled contribution over mandatory completion of every planned research direction.