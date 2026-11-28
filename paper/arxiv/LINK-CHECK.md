# Links and availability claims, checked 28 Nov 2026

Checked from a GitHub Actions runner without signing in anywhere, against `main` at
`8fc099f` and this branch. "Fixed in the preprint" means [`arxiv-edits.sed`](arxiv-edits.sed)
or [`si-edits.sed`](si-edits.sed) rewords it for arXiv only; the journal text is unchanged.

## Links

| Link | Result | Verdict |
|---|---|---|
| Repository, https://github.com/vertical-cloud-lab/powder-doser | 200 to an anonymous request; API visibility "public" | OK |
| Project page, https://vertical-cloud-lab.github.io/powder-doser/ | 200; identical to `docs/index.html` on `main` | OK |
| 40 DOIs of the 44 cited references | all registered (doi.org handle API) | OK (some publishers return 403 to scripts, which is normal) |
| URLs in the cited references | all resolve | OK |
| SI: Onshape assembly `cad.onshape.com/documents/ae9f107d3972fc9d390e541f` | API 403, "does not exist, or you do not have permission" | **Not readable by the public.** Fixed in the preprint (points to the project page's public assembly instead); the journal SI still needs the document made public or the link changed |
| SI Table of parts: 11 Fusion 360 share links (`a360.co/...`) | all redirect to 11 different Autodesk share pages | Resolve. Whether each viewer still shows its part cannot be checked without a browser; 8 match the shares PR #170 downloaded STEP files from on 1 Oct. **Worth clicking through once** |
| SI Table of parts: tap-collar base STEP, `blob/debe299/design/cad/tap-collar/mount_plate.step` | 200 | OK as a permalink; the file is not on `main` (PR #51's branch) |
| Reference `TextToCad` (GitHub) | 200 | OK |
| Reference `FusionPlaylist` (YouTube) | 200, 53 videos | Exists, but YouTube titles it "Powder Doser", not the reference's "Human redesign of AI-made parts" |
| Reference `Charles2026Release` (Zenodo) | no DOI or URL; prints "DOI to be assigned when the release is archived at submission" | **Placeholder.** Dropped from the preprint with the Zenodo sentence |
| ESI footnote, "See DOI: 00.0000/00000000" | none | **Placeholder** (RSC template). Replaced in the preprint by the pointer to `anc/si.pdf` |

Every issue, pull request and discussion number the paper cites exists and is the type the
text says.

## The Data availability statement

| Claim | Verdict | Evidence |
|---|---|---|
| Data are in the repository | **Partly** | Public, but none of the listed data is on `main`. Tidy datasets, per-dose record, stepped-tilt and atomizer records are on this branch (PR #97). The raw run folders (`data/battery/`, 37 runs) are only on branch `claude/issue-116-20260915-1622`, which has no pull request. The design log (`DESIGN-LOG.md`) is only on draft PR #74 |
| "and in its archived release on Zenodo" | **False** | No record on zenodo.org (the upload was tested on the sandbox only). Fixed in the preprint |
| "The version of the code employed for this study is version 1.0.0" | **False** | No tags; the only release is an unpublished draft. Fixed in the preprint |
| Code: firmware, analysis and figure scripts, CAD source | **Partly** | Firmware and the OpenSCAD auger are on `main`. The figure scripts are on this branch only. The CadQuery and KCL sources for the doser parts are only on PR branches (#47, #49, #51, #53, #57, #66, #110) |
| Fusion 360 STEP and STL files, renders | **Partly** | Only on PR #170 (8 STEP files, 2 STL files, 26 renders) |
| Animated assembly guide | True | On `main` (`docs/static/videos/assembly_steps.mp4`, shown on the project page) |
| KiCad schematics and board files | **Partly** | The schematic is on `main` (`hardware/kicad/`). No board file (`.kicad_pcb`) is on `main` or this branch; boards exist only on draft PRs #45 and #76 |
| "public Onshape documents, listed with their print settings on the project page" | **Partly** | All 12 documents the page lists open for an anonymous client, but Onshape marks 3 as link-shared rather than public (Auger, Flexible bracket, Doser with new solenoid setup), and the page links to the print settings in issue #193 rather than listing them. Fixed in the preprint |
| "each printed part tested has a public Fusion 360 link" | **False for one part** | The tap-collar base (AI-modelled) links to a STEP file on GitHub. Fixed in the preprint ("a public link to its design file") |
| Scripts in `paper/v2/` and `paper/figures/data/` | **Only on this branch** | 0 files under either on `main`; 166 and 40 here |
| "released under the open licenses stated in the repository" | **Partly** | The only licence is MIT (`LICENSE`). No hardware or data licence yet (SUBMISSION-DECISIONS item 5) |
| AI prompt and response logs | **Partly** | Issue and PR threads are public. The raw Actions and Claude session logs are only in the unpublished draft release. Preprint text says they "will be" part of the archived release |
| References cited in the SI are in the main reference list | True | Every SI citation key is also cited in the main text |

## Also on the SI's pages

- `cad/full-assembly/BOM.md` and `.../fusion-step/` (SI Sections S1 and S2) are only on PR #170.
- `cad/auger-geared/` (SI auger section) is only on PRs #49, #68 and #81.
- The SI says the AI-modelled originals are in `cad/`. On `main`, `cad/` holds only the
  OpenSCAD auger and the excavator concept; the originals are on PRs #47, #49, #51, #53 and #66.

## What would make the statement true as written

Merging PR #97 (this paper), #74 (design log) and #170 (Fusion files and BOM) into `main`, and
putting the raw run folders from `claude/issue-116-20260915-1622` on `main`, makes every
"in the repository" claim true on the default branch, which is where readers will look.
Making the three link-shared Onshape documents public, and the SI's assembly document (or
pointing the journal SI at the public assembly on the project page), settles the Onshape
claims. Tagging v1.0.0 and archiving it on Zenodo settles the release claims; then the first
three edits in `arxiv-edits.sed` can go.

## Not checked

- Whether the 11 Autodesk viewers display their parts: every share page returns the same
  JavaScript shell to a script, with no part data and no error text.
- Whether Onshape's 403 for `ae9f107d...` means private or deleted: Onshape gives the same
  message for both.
