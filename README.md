# powder-excavator

![Design sketch](powder-excavator-sketch.jpg)

## Documentation

- [Programmatic and remote printing on the Bambu Lab H2D](docs/h2d-programmatic-access.md)
  — research notes on the cloud, LAN/Developer-Mode and Bambu Connect
  paths for sending sliced jobs to an H2D from code, with citations to
  the primary community and vendor sources. Runnable companions to the
  bringup checklist live in [`scripts/`](scripts): the Step 2
  reachability smoke test, the Step 3 upload-and-start dry run, and the
  Step 4 `bambulabs_api` wrapper.
- [Programmatic printing on the Bambu Lab A1 mini ("Thumbelina")](docs/a1-mini-programmatic-access.md)
  — the A1-mini instruction list: same bringup Steps 0–6 with the
  parameters adjusted for the single-extruder, Wi-Fi-only A1 mini
  (profiles, simplified CLI slicing recipe, AMS-lite payload note,
  scaled safety-envelope limits). Reuses the Step 2/4 `scripts/` files
  verbatim, plus a dedicated fill-in-the-placeholders send script,
  [`scripts/a1_mini_send_print.py`](scripts/a1_mini_send_print.py),
  for starting a print.

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
