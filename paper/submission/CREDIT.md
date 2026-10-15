# CRediT author contributions: proposal and evidence (10 Oct 2026)

`main.tex` now carries the roles below. They replace the roles an AI agent wrote on 11 June,
before Carl, Gage or the test campaign had any recorded activity. Each author must confirm
their own roles before submission ([`HUMAN-TODOS.md`](HUMAN-TODOS.md), items G3 and A1).

The evidence is the GitHub record only. Printing, assembly, lab time, meetings and Slack are
not on GitHub, so a missing tick can mean "not recorded" rather than "not done". The author
list itself is still open ([`SUBMISSION-DECISIONS.md`](SUBMISSION-DECISIONS.md), item 1).

Roles use the 14 CRediT terms (<https://credit.niso.org>). ✓ = proposed; ? = plausible but
not shown by the record, so the author should say.

| Role | S.C. | W.M. | L.W. | C.R. | G.E. | S.G.B. |
|---|---|---|---|---|---|---|
| Conceptualization | ✓ | | | | ? | ✓ |
| Methodology | ✓ | ✓ | | | | ✓ |
| Software | | ✓ | ✓ | | | ✓ |
| Validation | ✓ | ✓ | | | | |
| Formal analysis | | ✓ | | | | ✓ |
| Investigation | ✓ | ✓ | ✓ | ✓ | ? | |
| Resources | | | ✓ | | | ✓ |
| Data curation | ✓ | | | | | |
| Writing – original draft | ✓ | | | | | ✓ |
| Writing – review & editing | ✓ | | | | | ✓ |
| Visualization | | | | | | ✓ |
| Supervision | | | | | | ✓ |
| Project administration | | | | | | ✓ |
| Funding acquisition | | | | | | ? |

## Evidence

**Sam Charles (S.C.).** Proposed the part-by-part approach (#46) and supplied the dimensioned
drawings the agents modelled from. Ran the bench campaign in #116 (66 of the 79 human comments
there since 1 August), posting and checking each run. Recreated the parts in Fusion 360 on
video (#120). Reviewed the draft on video (part 1, 1 October; notes in
`paper/review_2026-10-01/NOTES-part1.md`).

**Will Mulberry (W.M.).** Defined the dosing optimization problem and wrote the three-phase
controller the tests used (#123, #124, #131). Ran the optimization campaign and the atomizer
charges (#164, #166). Opened the glove-box trial (#117). Found the as-built gear ratio
(20:44) in the #124 review.

**Luke Winters (L.W.).** Tested AI tools for laying out the PCB (#87, #94, #95), and built the
platform (#113), the user interface (#122) and the balance feedback loop for demonstrations
(#99). Proposed the angled funnel (#143).

**Carl Robison (C.R.).** Hand-tested eight powders with videos in #116 (30 June to 9 July),
which later analyses cite.

**Gage Erickson (G.E.).** No issues, comments or commits in this repository. In `byu-vcl` he
sized a glove box for the doser and discussed auger capacity, and #163 credits him with the
angle-of-repose idea. The record does not show investigation on this paper's data, so he
should say what he did, or the team should move him to the Acknowledgements.

**Sterling G. Baird (S.G.B.).** Started the project at the April 2026 hackathon and directed
it throughout: 51 issues, 692 comments and 436 requests to the AI agents, which wrote the
firmware, analysis, figures and drafts at his direction (hence software, formal analysis,
visualization and writing – original draft, with the AI use declared separately). Supervised
the team and ran the project. Funding acquisition only if there is a funder to name
(SUBMISSION-DECISIONS item 6).

## Questions for the authors

1. **Writing – original draft.** The text was drafted by Claude Code at the team's request. The
   proposal credits S.C. and S.G.B., who directed and reviewed it. Should anyone else be
   credited, or should S.C. move to review & editing only?
2. **Writing – review & editing.** ICMJE requires every author to critically review the draft.
   Add this role for each author once they have reviewed the final version.
3. **Funding acquisition.** Drop it if the paper names no funder.
4. **Resources.** Who supplied the balance, printers and fume hoods? The proposal credits
   S.G.B. (lab) and L.W. (electronics).
