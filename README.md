# powder-excavator

[Presentation at POSE 2026](https://docs.google.com/presentation/d/1SZyMInTeK6V5QMu_9ptvdzXFou06gq9Mr7xBxdh9StA/edit?usp=sharing)

![Design sketch](powder-excavator-sketch.jpg)

## Design

The first physical-prototype design — a single-channel powder-doser
module that gets replicated `N` times around a shared collection cup —
lives in
[`design/cad/single-channel-module/`](design/cad/single-channel-module/).
It is the "Idea B" archetype from the architecture brainstorm
(`design/brainstorming.md` §2.2), packaging the
[`cad/auger/`](cad/auger/) Archimedes auger together with the
NEMA 11 / DRV8825 / JF-0530B / DRV8871 / ERM-coin / DRV2605L actuator
stack identified in
[`hardware/vibration-motor-and-solenoid.md`](hardware/vibration-motor-and-solenoid.md)
on a printable 80 × 80 × 342 mm frame. The folder ships printable STLs,
a full-assembly STEP, and a project plan / iteration roadmap for the
`AI design → printing → testing → feedback` loop.

A separate visualization of the §2.2 fan-in geometry (12 channels around
a shared cup) lives in
[`design/cad/inward-collection-cup/`](design/cad/inward-collection-cup/).

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
