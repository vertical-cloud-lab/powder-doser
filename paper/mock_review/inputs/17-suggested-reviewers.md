# 17 — Suggested reviewers for the powder-doser paper

*Edison-driven reviewer scouting (Batch 2, query `likely_reviewers`). Raw
artifacts: `edison_artifacts/likely_reviewers.{answer,references}.md` and the
structured table `edison_artifacts/likely_reviewers.artifact-00.md`; runner:
`edison_run_editors_reviewers_conferences.py`. One `LITERATURE_HIGH` query
grounded in the Batch-1 venue shortlist (note **15**), under the #43
no-fabricated-contacts convention: each name carries a public verification URL
and DOI-linked representative work, and only publicly listed contact channels
are reproduced.*

The query returned **21 candidates across five sub-topics**. This note keeps the
full pool but flags conflicts of interest, so a cover letter can pull a balanced,
non-conflicted slate of ~8–12 suggested reviewers.

## Conflicts of interest to exclude

- **Sterling G. Baird (U. Utah)** — listed under (a) SDL/automation, but he is on
  this project's **author side** and sits on the *Digital Discovery* advisory
  board (note **16**). **Do not suggest as a reviewer.**
- Double-check any co-authorship within the last ~3–5 years for the remaining
  names before suggesting them; the Edison query was told to avoid identifiable
  conflicts but cannot see unpublished collaborations.

## Candidate pool by sub-topic

### (a) Self-driving labs / autonomous experimentation / lab automation
| Name | Affiliation | Overlap | Representative work (DOI) |
|---|---|---|---|
| **Milad Abolhasani** | NC State (Chem. & Biomol. Eng.) | SDLs, autonomous flow chemistry, MAPs, closed-loop | 10.1038/s44160-022-00231-0; 10.1038/s41467-024-45569-5 |
| **Benji Maruyama** | AFRL (Materials & Manufacturing) | Autonomous AM (ARES), Bayesian optimization | 10.1557/s43577-021-00051-1; 10.1039/d4dd00281d |
| **Keith A. Brown** | Boston U. (Mech. Eng.) | Autonomous experimentation, BO benchmarking | 10.1016/j.matt.2021.06.036; 10.1038/s41524-021-00656-9 |
| Joshua Schrier | Fordham U. (Chemistry) | Autonomous discovery, SDL software, informatics | 10.1039/d3dd00223c; arXiv:2304.11120 |
| ⚠ Sterling G. Baird | U. Utah | Low-cost SDLs, frugal twins, open SDL hardware | 10.1039/d3dd00223c — **author-side; exclude** |

### (b) Open-source scientific hardware / low-cost instrumentation
| Name | Affiliation | Overlap | Representative work (DOI) |
|---|---|---|---|
| **Joshua M. Pearce** | Western U. | Open-source hardware, distributed manufacturing (also HardwareX EiC) | 10.1016/j.ohx.2020.e00139 |
| **Richard W. Bowman** | U. Bath (Physics) | OpenFlexure, 3D-printed instrumentation, accessible automation | 10.1364/OE.384207 |
| Tobias Wenzel | U. Bath / EMBL *(affil. unverified)* | Open science hardware, accessible lab equipment | 10.1371/journal.pbio.3001931 |
| Vittorio Saggiomo | Wageningen U. *(dept. unverified)* | 3D-printed lab equipment, rapid prototyping | (check Scholar — *unverified*) |

*Note: Pearce is the most natural fit here but also the HardwareX EiC (note 16)
— suggest him as a reviewer only if HardwareX is not the submission target.*

### (c) Powder dosing / dispensing / flowability & metrology
| Name | Affiliation | Overlap | Representative work (DOI) |
|---|---|---|---|
| **Johannes G. Khinast** | TU Graz / RCPE | High-precision low-dose feeders, gravimetric dosing | 10.1208/s12249-020-01835-5; 10.1007/s12247-024-09858-2 |
| **Fernando J. Muzzio** | Rutgers (Chem. & Biochem. Eng.) | Powder flow, loss-in-weight feeder design space | 10.1007/s12247-019-09394-4 |
| Thomas De Beer | Ghent U. (Pharma PAT) | Feeding-behavior prediction, PAT, soft sensors | 10.1016/j.ijpharm.2018.12.066 |
| Abina M. Crean | University College Cork | Continuous powder feeding, difficult-to-feed materials | 10.1080/10837450.2017.1339197 |

*This is the sub-topic least covered by the venue shortlist's usual reviewer
pools, so including 1–2 of these pharma-feeding experts adds genuinely
independent metrology scrutiny of the closed-loop gravimetric calibration.*

### (d) AM of alloys / high-throughput & combinatorial alloy discovery
| Name | Affiliation | Overlap | Representative work (DOI) |
|---|---|---|---|
| **Wen Chen** | USC (prev. UMass Amherst) | HEA/MPEA AM, in-situ alloying of elemental powders, combinatorial AM | 10.1038/s41586-022-04914-8; 10.1038/s41467-025-67301-7 |
| **Dan J. Thoma** | U. Wisconsin–Madison (MSE) | DED multi-powder alloy discovery, ML-guided DED | 10.1016/j.msea.2023.145945 |
| Kenneth S. Vecchio | UC San Diego (NanoEng.) | High-throughput rapid experimental alloy dev (HT-READ) | 10.1016/j.actamat.2021.117352 |
| Raymundo Arroyave | Texas A&M (MSE) | High-throughput alloy/process design for AM, CALPHAD | arXiv:2304.04149 |
| Amit Bandyopadhyay | Washington State U. (MME) | Multi-material AM, DED, functionally graded alloys | 10.1016/j.mser.2018.04.001 |

### (e) LLM / AI / code-based generative CAD & design automation
| Name | Affiliation | Overlap | Representative work (DOI) |
|---|---|---|---|
| **Wojciech Matusik** | MIT CSAIL | Computational design/manufacturing, LLM-enabled CAD | 10.1162/99608f92.cc80fe30; 10.1162/99608f92.0705d8bd |
| **Adriana Schulz** | U. Washington (Allen School) | Parametric CAD, LLM-driven CAD languages | 10.1111/cgf.70250 |
| Faez Ahmed | MIT (Mech. Eng.) | AI for design, text-to-CAD, LLM CAD-code generation | (GenCAD; DOI *unverified*) |

## Recommended balanced slate (~10, non-conflicted)

Pick across sub-topics so each gets ≥1 reviewer and no single lab dominates:

1. **Milad Abolhasani** (a) — SDL/closed-loop authority.
2. **Benji Maruyama** (a/d) — bridges autonomous experimentation **and** AM.
3. **Keith A. Brown** (a) — autonomous experimentation / BO.
4. **Johannes Khinast** (c) — gravimetric dosing/feeder metrology.
5. **Fernando Muzzio** (c) — independent powder-flow scrutiny.
6. **Wen Chen** (d) — combinatorial AM alloy discovery.
7. **Dan Thoma** (d) — multi-powder DED alloy discovery (closest to the use case).
8. **Wojciech Matusik** (e) — LLM-enabled CAD.
9. **Adriana Schulz** (e) — programmatic/parametric CAD.
10. **Richard Bowman** (b) — open hardware (use if Pearce is the HardwareX EiC).

Swap in Joshua Pearce (b) for Bowman if the submission is **not** to HardwareX.

## Caveats

- Contact channels: only `wenchen@umass.edu` / `wchen001@usc.edu` (Wen Chen) and
  `abolhasani@ncsu.edu` (Abolhasani) were publicly listed; for everyone else the
  table gives ORCID/faculty/Scholar pages, not emails — do not guess addresses.
- Affiliations marked *unverified* (Wenzel, Saggiomo) and DOIs marked
  *unverified* (Ahmed's GenCAD) should be confirmed before use.

See note **15** (venues), **16** (editors), **18** (conferences), and **19**
(consolidated recommendation).
