# Cover letter (draft, not sent)

Draft for when the paper is submitted. Nothing in it has been sent to anyone. Placeholders are in
**[brackets]**. Check the editor's name and the reviewer slate against the journal site on the day of
submission (board read 2026-11-27).

---

[Date]

Professor A. T. Clare
Editor-in-Chief, *Additive Manufacturing*
Department of Mechanical Engineering, The University of British Columbia

Dear Professor Clare,

We submit the manuscript "Per-powder Bayesian calibration of an auger doser for alloy feedstock
preparation, and dosing records as a probe of powder flow" for consideration as a full-length research
article in *Additive Manufacturing*.

Alloy development for powder bed fusion and directed energy deposition starts by weighing many feedstock
powders, and an automated doser has to be recalibrated whenever the powder changes. The manuscript treats
that calibration as multi-objective Bayesian optimization and shows what the calibration records reveal
about the feedstock:

- On salt, an unattended campaign found settings that dosed 0.5 g three times faster than hand-tuned
  settings, with less than half their error, in eight repeat doses. The best single screening dose did not
  repeat, which shows why a model-based recommendation and a validation block are needed.
- A second campaign shows the main obstacle to unattended calibration: the powder's response drifted
  between and within sessions. The manuscript states what has to be recorded and modelled as a result.
- Applied unchanged to metal feedstock, the settings dosed gas-atomized AlSi10Mg within 0.1%. With the
  laboratory's own unsieved Al 4047, the same settings fed an order of magnitude more slowly and stalled
  until oversized particles were removed. The dose record alone flagged the feedstock problem.
- **[Multi-task calibration across N metal feedstocks, and same-lot shear-cell, Hall-flow and particle-size
  measurements compared with the dosing response.]**

The work fits the journal's interest in feedstock preparation and in the automation and control of AM
workflows. All firmware, analysis code, dose records and simulation inputs are open. The data are archived
at **[Zenodo DOI]**.

Related work by the same group: the doser's hardware, its design with generative AI tools, and its
response to 13 powders at fixed settings are described in a companion manuscript **[Charles et al.,
status and venue at submission]**. The present manuscript does not repeat that paper's figures or results.
It cites them and uses its fixed-setting records only for the new property correlations of Section 3.6.
The two papers are not parts of one study, and each stands on its own. **[If the companion paper is
under review, attach it for the editor.]**

Professor Nathan B. Crane, an Associate Editor of the journal, is in the same department at Brigham Young
University as several of the authors. We ask that he not handle the manuscript.

Suggested reviewers (no co-authorship with any author in the last five years, to be confirmed by each
author):

- **[Johannes G. Khinast]**, Graz University of Technology / RCPE: gravimetric low-dose feeding and feeder
  metrology.
- **[Laura Cordova]**, **[affiliation]**: AM feedstock and spreadability.
- **[Hongyang Cheng]**, University of Twente: Bayesian calibration of DEM parameters.
- **[Keith A. Brown]**, Boston University: autonomous experimentation and Bayesian optimization.
- **[Dan J. Thoma]**, University of Wisconsin–Madison: multi-powder DED for alloy discovery.

The manuscript has not been published and is not under consideration elsewhere, and no preprint has been
posted. All authors approved the submission. The authors used Claude Code (Anthropic) and Edison
Scientific in preparing the manuscript and the analysis code, as stated in the declaration before the
references.

Sincerely,

Sterling G. Baird, on behalf of all authors
Department of Mechanical Engineering, Brigham Young University, Provo, UT, USA
**[e-mail address of the corresponding author, as on the title page]**
