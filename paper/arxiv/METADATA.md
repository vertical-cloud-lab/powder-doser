# arXiv submission: files and metadata (28 Nov 2026)

Prepared for Sterling to submit by Mon 30 Nov 2026. Nothing has been submitted. The Digital
Discovery submission comes later; the cover letter now discloses the preprint
(`../cover_letter/cover_letter.tex`, with a `[TODO]` for the arXiv identifier).

## Files in this folder

| File | What it is |
|---|---|
| [`powder-doser-arxiv.tar.gz`](powder-doser-arxiv.tar.gz) | **Upload this.** 22 MB (arXiv's limit is 50 MB), 22 files: `ms.tex`, `ms.bbl`, the 19 figure PDFs `ms.tex` includes (`figures/`), and the SI as `anc/si.pdf` |
| [`powder-doser-arxiv.pdf`](powder-doser-arxiv.pdf) | What the tarball compiles to: 17 pages. Built from the tarball alone in an empty directory with three pdflatex runs, no BibTeX, no `.bib` or `.bst`; no undefined references, citations or missing files |
| [`src/`](src/) | The tarball's contents, unpacked, for review |
| [`make_arxiv.sh`](make_arxiv.sh), [`preamble.tex`](preamble.tex), [`arxiv-edits.sed`](arxiv-edits.sed) | Rebuild everything from `../main.tex` and `../si.tex`: `bash paper/arxiv/make_arxiv.sh` |
| [`LINK-CHECK.md`](LINK-CHECK.md) | Every link and every claim in the Data availability statement, checked on 28 Nov 2026 |

**How the preprint differs from the journal version.** The body text, figures, tables and
references are the same as `../main.tex` on this branch, with these exceptions:

- A plain title block (title, four authors, abstract) replaces the RSC header, logo, journal
  name, DOI box and dates box. The page footer is a plain page number.
- Times and Helvetica replace the RSC template's Charter and Droid Sans. Page size (US
  letter), margins, column width and base font size are the journal's, so every figure and
  table is laid out exactly as there, and figure, table and section numbers are identical.
  The SI cites main-text items by number, so `make_arxiv.sh` checks this.
- The SI footnote points to the ancillary file (`anc/si.pdf`) instead of a placeholder DOI.
  SI items cited in the text ("SI Table S3") are typed in as numbers, read from `si.aux`.
- The `\input` tables are pasted in, and all TeX comments are removed, because arXiv makes the
  source public. The comments held internal TODO notes.
- Statements that are not true yet are reworded, in the preprint only
  ([`arxiv-edits.sed`](arxiv-edits.sed), each edit with its reason): the Data availability
  statement no longer claims an archived Zenodo release or a version 1.0.0, neither of which
  exists on 28 Nov 2026 (it now says a tagged release "will be archived on Zenodo"), and the
  October session logs "will be" part of the archived release rather than "are". If you
  archive v1.0.0 before posting, delete those edits, add the DOI to `Charles2026Release` in
  `../references.bib`, and rebuild. [`LINK-CHECK.md`](LINK-CHECK.md) lists every check.

`anc/si.pdf` is the journal SI (`../si.tex`, four-author title page, no journal branding)
with the same "will be part of the archived release" edit ([`si-edits.sed`](si-edits.sed)).

## Metadata for the arXiv form

**Title**

```
An open-source powder doser for autonomous alloy discovery, designed by engineers and modelled by AI agents
```

**Authors**

```
Sam Charles, Will Mulberry, Luke Winters, Sterling G. Baird
```

**Abstract** (plain text, 1,596 characters and 245 words; arXiv's limit is 1,920 characters)

```
Additive manufacturing of aerospace alloys depends on rapid, reproducible exploration of powder feedstocks, yet metering and blending dry metal powders remains largely manual in research laboratories. Commercial dispensers are costly and poorly matched to many-powder alloy workflows, and open-source designs have not been tested on feedstocks for laser powder bed fusion (L-PBF). We developed an open-source, low-cost, modular powder doser for a self-driving materials-discovery loop in which dosed powders feed ultrasonic atomization and L-PBF. The first module, a single channel built from 3D-printed parts and off-the-shelf electronics, cost under $200 plus an analytical balance, roughly two orders of magnitude below commercial dosing heads. In closed loop, every 1 g dose on seven of 13 tested powders landed within ±5% of the target; smaller doses were less reliable. With a revised procedure that steps the tilt down as the cup fills, 20 consecutive 2 g doses of AlSi10Mg all landed within ±5%, 11 of them within ±1 mg. The doser also ran in a glove box under an AI agent's control, and filled atomizer charges with AlSi10Mg and with Al 4047 from our own atomizer. Its parts were designed by engineers and, from April to July 2026, modelled by AI agents (GitHub Copilot with Claude Opus 4.7–4.8; Zoo Design Studio's Zookeeper): engineers supplied dimensions, sketches, and manufacturing constraints; AI modelled the parts as editable parametric scripts; and engineers reviewed, printed, and iterated. AI was most effective as a modelling assistant rather than an autonomous design agent.
```

It is the journal abstract (v6) with the LaTeX removed. The `$` in "$200" is the only one,
so arXiv's maths rendering, which pairs `$` signs, leaves it alone. The ±, – and ' are plain Unicode characters, not TeX.

**Comments**

```
17 pages, 8 figures, 5 tables. Supplementary Information (27 pages) is an ancillary file (anc/si.pdf). Design files, firmware, data and AI interaction records: https://github.com/vertical-cloud-lab/powder-doser ; project page: https://vertical-cloud-lab.github.io/powder-doser/
```

**Categories** (one primary, cross-lists optional)

| | Category | Why |
|---|---|---|
| **Primary** | `cond-mat.mtrl-sci` (Materials Science) | The doser exists for alloy discovery (blending powders for atomization and L-PBF), the validation is on alloy and surrogate powders, and the readers who build self-driving labs for materials browse this list. If you have posted here before, arXiv should not ask for an endorsement |
| Cross-list | `physics.ins-det` (Instrumentation and Detectors) | It is an instrument paper: design, bill of materials, build guide and validation of laboratory hardware |
| Cross-list | `cs.RO` (Robotics) | Laboratory automation hardware: a stepper-, servo- and solenoid-driven doser under closed-loop control, run by an AI agent |
| Cross-list | `cs.HC` (Human-Computer Interaction) | The second result is a case study of engineers and AI agents dividing the design work (who decided, who modelled, how review worked). `cs.AI` is the alternative if you would rather frame it as an evaluation of AI agents |

`physics.ins-det` would also work as the primary if you want the instrument framing first.
Moderators can drop a cross-list that does not fit, so keep only the ones you agree with.

**Licence:** Creative Commons Attribution 4.0 (CC BY 4.0). RSC accepts preprints (its
policy names arXiv and ChemRxiv) as long as the submission discloses them, which the cover
letter now does ([RSC processes and policies](https://www.rsc.org/publishing/journals/processes-and-policies)).

**Leave blank:** Journal-ref, DOI, Report number, MSC and ACM classes.

## When submitting

1. Upload `powder-doser-arxiv.tar.gz` as is. arXiv unpacks it, sees `ms.tex`, compiles it with
   pdflatex (the first line is `\pdfoutput=1`) using `ms.bbl`, and lists `anc/si.pdf` as an
   ancillary file. Check that the "Ancillary files" list shows `si.pdf`.
2. Compare arXiv's PDF with [`powder-doser-arxiv.pdf`](powder-doser-arxiv.pdf): 17 pages,
   eight figures. arXiv's TeX Live is not the one used here, so line breaks may differ slightly.
3. Paste the metadata above. Choose CC BY 4.0.
4. After it is announced, put the arXiv identifier in the cover letter (the `[TODO]` after "a
   preprint is on arXiv") and in `SUBMISSION-DECISIONS.md` item 15.

## Rebuilding

`bash paper/arxiv/make_arxiv.sh` rebuilds the journal SI and main text, regenerates `src/`,
the tarball and the PDF, and stops on any unresolved SI reference, missing figure, numbering
difference from the journal build, or warning in the clean-directory build. It needs pdflatex
and bibtex (TeX Live or MiKTeX), gawk, sed, tar and gzip. On this PR the session's guard does
not let an agent run repository scripts, so on 28 Nov the same commands were run step by
step instead; running the script once yourself confirms it reproduces the bundle.
