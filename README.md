# powder-excavator

[Presentation at POSE 2026](https://docs.google.com/presentation/d/1SZyMInTeK6V5QMu_9ptvdzXFou06gq9Mr7xBxdh9StA/edit?usp=sharing)

![Design sketch](powder-excavator-sketch.jpg)

## Paper

A bare-bones LaTeX template in the Digital Discovery (Royal Society of
Chemistry) submission style is available in [`paper/`](paper). It is built on
the official RSC "Paper" article template (two-column, 9 pt Times,
`natbib`/`rsc.bst` bibliography, RSC running headers/footers) and uses
`lipsum` placeholder text. A pre-built PDF is committed alongside it at
[`paper/main.pdf`](paper/main.pdf).

To rebuild the PDF locally you need a TeX Live installation that includes
`latexmk` plus the standard packages used by the template (`natbib`,
`mhchem`, `balance`, `caption`, `fancyhdr`, `lastpage`, `lipsum`,
`url`, `times`/`mathptmx`, `extsizes`). On Debian/Ubuntu these are provided
by `texlive-latex-recommended`, `texlive-latex-extra`,
`texlive-fonts-recommended`, `texlive-science`, and `latexmk`. Only the
RSC-specific assets (`rsc.bst`, `rsc.bib`, `headers/`) are vendored in
`paper/`; all other packages are taken from the system TeX distribution.

```sh
cd paper
latexmk -pdf main.tex
```

## Outreach

A running list of individuals, academic groups, commercial vendors, and
open-source projects we could reach out to for help with accurate, automated
powder dispensing is kept in
[`paper/background/07-powder-dispensing-outreach-contacts.md`](paper/background/07-powder-dispensing-outreach-contacts.md)
(Edison-backed; per-entry `### Name` anchors and verifiable `(source: <URL>)`
tags). The synthesis is produced by
[`paper/background/edison_run_powder_dispensing_outreach_contacts.py`](paper/background/edison_run_powder_dispensing_outreach_contacts.py),
with raw artifacts under
[`paper/background/edison_artifacts/`](paper/background/edison_artifacts/),
and is compiled from the accelerated-discovery forum thread on [accurate
powder dispensing for chemistry and
materials-science applications](https://accelerated-discovery.org/t/accurate-powder-dispensing-for-chemistry-and-materials-science-applications/177),
the background notes in
[#29](https://github.com/vertical-cloud-lab/powder-doser/pull/29), and other
references throughout this repository. Same workflow as the generative-CAD
outreach note in [#43](https://github.com/vertical-cloud-lab/powder-doser/pull/43).

A companion list of **powder-properties** experts (flowability and
cohesion/friction measurement, DEM modeling and Bayesian calibration, AM
spreadability and powder-bed metrology) — anchored to the TMS 2027
calibration-optimization abstract from
[#78](https://github.com/vertical-cloud-lab/powder-doser/pull/78) — is kept
in
[`paper/background/08-powder-properties-experts.md`](paper/background/08-powder-properties-experts.md),
produced by
[`paper/background/edison_run_powder_properties_experts.py`](paper/background/edison_run_powder_properties_experts.py)
(three Edison `LITERATURE_HIGH` tasks plus direct web searching; raw
artifacts under the same
[`paper/background/edison_artifacts/`](paper/background/edison_artifacts/)
directory).
