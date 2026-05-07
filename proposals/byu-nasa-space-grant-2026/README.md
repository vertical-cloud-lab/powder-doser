# BYU / Utah NASA Space Grant Consortium Fellowship --- 2026 Proposal

This directory contains the **3--5 page proposal narrative** for Sam Charles's
2026 Utah NASA Space Grant Consortium Fellowship application. It is currently
a **lorem-ipsum placeholder** so the formatting, length, and bibliography
plumbing can be reviewed before the real prose is written.

The proposal is framed around generative CAD work on the
[`powder-doser`](https://github.com/vertical-cloud-lab/powder-doser)
repository, situated within the larger vision of autonomous discovery of
additively manufactured aerospace alloys (where accurate dosing of many
distinct powders with different physical characteristics is a critical
enabling capability).

## Files

| File | Description |
| ---- | ----------- |
| `proposal.tex` | LaTeX source for the 3--5 page narrative (lorem ipsum). |
| `refs.bib` | BibTeX database (placeholder entries). |
| `nasa-26-application.pdf` | Official Utah NASA Space Grant 2026 application packet (downloaded from BYU College of Engineering). |
| `proposal.pdf` | Build artifact -- regenerate locally; not committed. |

## Building (MiKTeX)

The template is built with MiKTeX. Missing packages are pulled in
automatically when `[MPM]AutoInstall=1` is set (the MiKTeX default once
configured).

```sh
cd proposals/byu-nasa-space-grant-2026
latexmk -pdf proposal.tex
```

To clean up auxiliary files:

```sh
latexmk -C proposal.tex
```

## Scope of this issue

Per the originating issue, only the 3--5 page proposal narrative is in
scope here. The other application requirements (fellowship application form,
faculty letter of recommendation, second letter of recommendation, and
transcript) are handled separately.
