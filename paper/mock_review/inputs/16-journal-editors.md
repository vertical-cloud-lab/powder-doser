# 16 — Journal editors for the powder-doser paper

*Edison-driven editor scouting (Batch 2, query `journal_editors`). Raw
artifacts: `edison_artifacts/journal_editors.{answer,references}.md` and the
structured table `edison_artifacts/journal_editors.artifact-00.md`; runner:
`edison_run_editors_reviewers_conferences.py`. One `LITERATURE_HIGH` query
grounded in the Batch-1 venue shortlist (note **15**), under the #43
no-fabricated-contacts convention: every named editor carries a public,
verifiable source URL and no guessed email addresses.*

This note lists the editors who would plausibly **steer** a submission at each
shortlisted venue and who could be **requested as the handling editor**. Roles
flagged *verify at journal page* below were inferred from the retrieved
literature rather than directly confirmed in-source — re-check the editorial-
board page (linked) before naming anyone in a cover letter.

## TL;DR — who to request

- **Digital Discovery (RSC) [primary venue]:** the natural handling editor is
  **Alán Aspuru-Guzik** (Editor-in-Chief, U. Toronto) — AI-for-materials and
  self-driving labs. Advisory-board members **Connor Coley** (MIT), **Jason
  Hein** (UBC), and **Keith Brown** (BU) are all topical, but **Sterling Baird**
  (Acceleration Consortium / UBC) sits on the same board *and* is on this
  project's author side — a conflict to avoid requesting (and to keep off the
  reviewer slate; see note **17**).
- **HardwareX (companion):** **Joshua Pearce** (Founding EiC, Western U.) is the
  ideal handling editor for the open-hardware reproducibility paper.
- **Generative-CAD-leaning alternative:** **Wei Chen** (EiC, *ASME J. Mech.
  Design*, Northwestern) for a design-method framing, or **Andrew Y.C. Nee**
  (EiC, *IJAMT*, NUS) for the LLM→OpenSCAD pipeline framing.

## Editors by venue

### Digital Discovery (RSC) — primary
| Editor | Role | Institution | Why they fit |
|---|---|---|---|
| **Alán Aspuru-Guzik** | Editor-in-Chief *(confirmed)* | U. Toronto | AI for chemistry/materials, self-driving labs, Bayesian optimization — strongest topical fit; best handling-editor request. |
| Connor W. Coley | Advisory Board *(verify)* | MIT | Autonomous experimentation, ML for discovery, lab automation. |
| Jason Hein | Advisory Board *(verify)* | UBC | Automation infrastructure, data workflows, SDL ecosystem. |
| Keith A. Brown | Advisory Board *(verify)* | Boston U. | Autonomous materials research, robotics/automation. |
| ⚠ Sterling G. Baird | Advisory Board *(verify)* | Acceleration Consortium / UBC | Low-cost/open SDL infrastructure — **author-side conflict; do not request.** |

Source (all rows): <https://pubs.rsc.org/en/journals/journalissues/dd#!editorialboard>

### HardwareX (Elsevier) — companion (reproducible build)
| Editor | Role | Institution | Why they fit |
|---|---|---|---|
| **Joshua M. Pearce** | Founding Editor-in-Chief *(confirmed)* | Western U. | Open-source scientific hardware, distributed manufacturing, low-cost lab tools — ideal fit. |
| Todd Duncombe | Co-Editor-in-Chief *(verify)* | unverified | Open hardware / lab instrumentation. |

Source: <https://www.sciencedirect.com/journal/hardwarex/about/editorial-board>

### Higher-impact / generative-CAD-leaning alternatives
| Journal | Editor | Role | Institution | Why they fit |
|---|---|---|---|---|
| **ASME J. Mechanical Design** | **Wei Chen** | EiC *(verify)* | Northwestern | Data-driven & generative design, AI for design — best fit for the gen-CAD contribution. |
| ASME JCISE | Yan Wang | EiC *(verify)* | Georgia Tech | Computational engineering, AI/ML, digital twins, manufacturing informatics. |
| ASME JCISE | Ying Liu | Associate Editor *(confirmed)* | Cardiff U. | Intelligent manufacturing & design/manufacturing informatics — a plausible handling AE. |
| **IJAMT** (Springer) | **Andrew Y.C. Nee** | EiC *(verify)* | NUS | Advanced manufacturing, CAD/CAM, intelligent manufacturing — matches the LLM→OpenSCAD precedent. |
| Additive Manufacturing | Ryan Wicker | EiC *(verify)* | UT El Paso | AM systems/processes — for an AM-feedstock/alloy-discovery framing. |

Sources: ASME JMD <https://asmedigitalcollection.asme.org/mechanicaldesign/pages/editorial-board>;
JCISE <https://asmedigitalcollection.asme.org/computingengineering/pages/editorial-board>;
IJAMT <https://link.springer.com/journal/170/editors>;
Additive Manufacturing <https://www.sciencedirect.com/journal/additive-manufacturing/about/editorial-board>

### Stretch / physical-science venues
| Journal | Editor | Role | Institution | Why they fit |
|---|---|---|---|---|
| Cell Reports Physical Science | Luke Batchelor | Senior Editor *(verify)* | Cell Press | Physical-science remit spanning materials/energy methods. |
| Cell Reports Physical Science | Andrew Bissette | Senior Editor *(verify)* | Cell Press | Cross-cutting platform/methods papers in materials/automation. |
| npj Computational Materials | Long-Qing Chen | Editor-in-Chief *(confirmed)* | Penn State | Computational materials, ICME, theory-guided design. |
| npj Computational Materials | Lidong Chen | Co-EiC *(confirmed)* | SICCAS | Materials design/discovery, high-throughput framing. |

Sources: CRPS <https://www.cell.com/cell-reports-physical-science/editors>;
npj Comput. Mater. <https://www.nature.com/npjcompumats/editors>

## Caveats

- No personal email addresses are listed; request handling editors through the
  journal submission system, not by guessed email.
- Roles marked *verify* should be re-confirmed on the linked editorial-board page
  immediately before submission — board rosters rotate.
- The Baird advisory-board overlap at Digital Discovery is the one hard
  constraint: it is an asset for venue fit but means he must be excluded both as
  a requested handling editor and as a suggested reviewer (note **17**).

See note **15** (venues), **17** (suggested reviewers), **18** (conferences), and
**19** (consolidated recommendation).
