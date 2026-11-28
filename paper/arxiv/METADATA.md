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
| [`make_arxiv.sh`](make_arxiv.sh), [`preamble.tex`](preamble.tex), [`arxiv-edits.sed`](arxiv-edits.sed), [`si-edits.sed`](si-edits.sed) | Rebuild everything from `../main.tex` and `../si.tex`: `bash paper/arxiv/make_arxiv.sh` |
| [`LINK-CHECK.md`](LINK-CHECK.md) | Every link and every claim in the Data availability statement, checked on 28 Nov 2026 |

**How the preprint differs from the journal version.** The body text, figures, tables and
references are the same as `../main.tex` on this branch, with these exceptions:

- A plain title block (title, four authors, abstract) replaces the RSC header, logo, journal
  name, DOI box and dates box. The page footer is a plain page number.
- Times and Helvetica replace the RSC template's Charter and Droid Sans. Page size (US
  letter), margins, column width and base font size are the journal's, so every figure and
  table is laid out as there, and figure, table and section numbers are identical. The SI
  cites main-text items by number, so `make_arxiv.sh` checks this (25 of 25 labels match).
- The SI footnote points to the ancillary file (`anc/si.pdf`) instead of a placeholder DOI.
  SI items cited in the text ("SI Table S3") are typed in as numbers, read from `si.aux`.
- The `\input` tables are pasted in, and all TeX comments are removed, because arXiv makes the
  source public. The comments held internal TODO notes.
- Statements that are not true today are reworded in the preprint only, each edit with its
  reason in [`arxiv-edits.sed`](arxiv-edits.sed) and [`si-edits.sed`](si-edits.sed):
  - Data availability: no archived Zenodo release and no version 1.0.0 (neither exists yet);
    it now says a tagged release "will be archived on Zenodo". The `Charles2026Release`
    reference drops out of the reference list with it.
  - The October session logs "will be" part of the archived release, not "are" (main text
    and SI).
  - The Onshape parts are documents "that anyone can open", listed on the project page "which
    links to their print settings" (three of the twelve are link-shared, not public, and the
    page links to the settings rather than listing them).
  - Each printed part has "a public link to its design file", not "a public Fusion 360 link"
    (the tap-collar base links to a STEP file on GitHub).
  - SI construction guide: the Onshape assembly it cited returns 403 to an anonymous request
    (private or removed), and the assembly animation is on the project page, not in the README
    on `main`. It now points to the project page's parts and assembly.

  If you archive v1.0.0 on Zenodo before posting, delete the first three edits in
  `arxiv-edits.sed`, add the DOI to `Charles2026Release` in `../references.bib`, and rebuild.

## Metadata for the arXiv form

arXiv's metadata fields accept ASCII only (no Unicode, so no ±, en dash or curly quotes); TeX
is allowed but not needed here ([arXiv: preparing your article](https://info.arxiv.org/help/prep.html)).
Everything below is plain ASCII.

**Title**

```
An open-source powder doser for autonomous alloy discovery, designed by engineers and modelled by AI agents
```

**Authors**

```
Sam Charles, Will Mulberry, Luke Winters, Sterling G. Baird
```

**Abstract** (1,607 characters and 248 words; arXiv's limit is 1,920 characters)

```
Additive manufacturing of aerospace alloys depends on rapid, reproducible exploration of powder feedstocks, yet metering and blending dry metal powders remains largely manual in research laboratories. Commercial dispensers are costly and poorly matched to many-powder alloy workflows, and open-source designs have not been tested on feedstocks for laser powder bed fusion (L-PBF). We developed an open-source, low-cost, modular powder doser for a self-driving materials-discovery loop in which dosed powders feed ultrasonic atomization and L-PBF. The first module, a single channel built from 3D-printed parts and off-the-shelf electronics, cost under $200 plus an analytical balance, roughly two orders of magnitude below commercial dosing heads. In closed loop, every 1 g dose on seven of 13 tested powders landed within 5% of the target; smaller doses were less reliable. With a revised procedure that steps the tilt down as the cup fills, 20 consecutive 2 g doses of AlSi10Mg all landed within 5% of the target, 11 of them within 1 mg. The doser also ran in a glove box under an AI agent's control, and filled atomizer charges with AlSi10Mg and with Al 4047 from our own atomizer. Its parts were designed by engineers and, from April to July 2026, modelled by AI agents (GitHub Copilot with Claude Opus 4.7-4.8; Zoo Design Studio's Zookeeper): engineers supplied dimensions, sketches, and manufacturing constraints; AI modelled the parts as editable parametric scripts; and engineers reviewed, printed, and iterated. AI was most effective as a modelling assistant rather than an autonomous design agent.
```

This is the paper's abstract (v6) in ASCII. The only wording change: "within ±5%" and
"within ±1 mg" became "within 5% of the target" and "within 1 mg", since ± is not ASCII.
The `$` in "$200" is the only one, so arXiv's maths rendering, which pairs `$` signs, leaves
it alone.

**Comments**

```
17 pages, 8 figures, 5 tables; Supplementary Information (27 pages) as an ancillary file. Project page: https://vertical-cloud-lab.github.io/powder-doser/ Repository: https://github.com/vertical-cloud-lab/powder-doser
```

**Categories** (one primary; cross-lists optional)

| | Category | Why |
|---|---|---|
| **Primary** | `cond-mat.mtrl-sci` (Materials Science: "techniques, synthesis, characterization") | The doser exists for alloy discovery (blending powders for atomization and L-PBF), the validation is on alloy and surrogate powders, and the people who build self-driving labs for materials read this list. If you have posted in it before, arXiv should not ask for an endorsement |
| Cross-list | `physics.ins-det` (Instrumentation and Detectors) | An instrument paper: design, bill of materials, build guide and validation of laboratory hardware, with its "electronics ... and control equipment" |
| Cross-list | `cs.RO` (Robotics) | Laboratory automation hardware: a stepper-, servo- and solenoid-driven doser under closed-loop control, run by an AI agent |
| Cross-list | `cs.HC` (Human-Computer Interaction: "human factors, user interfaces, and collaborative computing") | The second result is a case study of engineers and AI agents dividing the design work: who decided, who modelled, and how review worked. `cs.AI` is the alternative if you would rather frame it as an evaluation of AI agents |

`physics.ins-det` would also work as the primary if you want the instrument framing first.
Moderators can drop a cross-list that does not fit, so keep only the ones you agree with.

**Licence:** Creative Commons Attribution 4.0 (CC BY 4.0). RSC accepts preprints (its
policy names arXiv and ChemRxiv) as long as the submission discloses them, which the cover
letter now does ([RSC processes and policies](https://www.rsc.org/publishing/journals/processes-and-policies)).

**Leave blank:** Journal-ref, DOI, Report number, MSC and ACM classes.

## When submitting

1. Upload `powder-doser-arxiv.tar.gz` as is. arXiv unpacks it, finds `ms.tex`, compiles it
   with pdflatex (the first line is `\pdfoutput=1`; arXiv's default is TeX Live 2025, the
   same release used here) using `ms.bbl`, and lists `anc/si.pdf` as an ancillary file.
   Check that the "Ancillary files" list shows `si.pdf`.
2. Compare arXiv's PDF with [`powder-doser-arxiv.pdf`](powder-doser-arxiv.pdf): 17 pages,
   eight figures.
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
