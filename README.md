# powder-excavator

[Presentation at POSE 2026](https://docs.google.com/presentation/d/1SZyMInTeK6V5QMu_9ptvdzXFou06gq9Mr7xBxdh9StA/edit?usp=sharing)

![Design sketch](powder-excavator-sketch.jpg)

## Documentation

- [Programmatic and remote printing on the Bambu Lab H2D](docs/h2d-programmatic-access.md)
  — research notes on the cloud, LAN/Developer-Mode and Bambu Connect
  paths for sending sliced jobs to an H2D from code, with citations to
  the primary community and vendor sources.

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
