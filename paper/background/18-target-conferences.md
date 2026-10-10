# 18 — Target conferences for the powder-doser paper

*Edison-driven conference scouting (Batch 2, query `target_conferences`). Raw
artifacts: `edison_artifacts/target_conferences.{answer,references}.md` and the
structured table `edison_artifacts/target_conferences.artifact-00.md`; runner:
`edison_run_editors_reviewers_conferences.py`. One `LITERATURE_HIGH` query
grounded in the Batch-1 venue shortlist (note **15**).*

The instrument spans two communities — the **SDL / materials-acceleration** side
and the **generative-CAD** side — so the conference roadmap is split by which
story leads. Submission formats and recurrence below were summarized from the
retrieved evidence; several editions are documented one-off, so re-check the
official page for the next cycle's dates before committing.

## TL;DR — where to present

- **Best near-term venue: the Accelerate Conference** (Acceleration Consortium,
  U. Toronto). It is the single best audience for an open-hardware SDL doser —
  the community already values low-cost, user-built automation, and it welcomes
  system demos rather than only algorithmic novelty.
- **Best archival AM venue:** the **Solid Freeform Fabrication (SFF) Symposium**
  (UT Austin) — full proceedings paper, accepts apparatus/calibration-rich work.
- **Best archival design-automation venue (gen-CAD half):** **ASME IDETC/CIE**
  (DAC + CIE tracks) — archival full papers for the LLM/code-based CAD pipeline.
- **Open-hardware dissemination:** **GOSH** for users/contributors and
  documentation feedback (not a conventional archival paper).

## Best-fit tier
| Venue | Organizer | Timing / location | Format | Why it fits |
|---|---|---|---|---|
| **Accelerate Conference** | Acceleration Consortium, U. Toronto | Annual; recent Toronto/Vancouver; summer–fall | Abstract / poster / demo / workshop; mostly non-archival | Single best SDL audience; values low-cost open automation and live demos. **Best near-term target.** |
| **Faraday Discussions** (data-driven discovery / AI-for-materials themes) | RSC | Topic-dependent; UK + intl. | Pre-submitted paper + oral discussion; archival | Excellent for a polished SDL systems story (closed-loop calibration); aligns with the *Digital Discovery* / RSC audience. |
| **MRS Fall Meeting** | Materials Research Society | Annual; late Nov/Dec; Boston | Abstract talks/posters; mostly non-archival | Strong for the alloy-discovery + SDL angle via an autonomous-experimentation / materials-acceleration symposium. |
| **SFF Symposium** | UT Austin | Annual; August; Austin | Full paper in proceedings; archival | Best AM venue for a detailed engineering paper — powder handling, dosing precision, feedstock prep, calibration. |
| **Shaping the Future of Self-Driving Autonomous Labs Workshop** | ORNL / DOE-lab ecosystem | Documented Nov 2024, Denver; recurrence *unverified* | Talks/panels/breakouts; non-archival | Outstanding for collaborators and national-lab visibility; instrumentation/interoperability/standards focus matches the doser. |

## Strong tier
| Venue | Organizer | Format | Why it fits |
|---|---|---|---|
| **TMS Annual Meeting** | TMS | Abstract; some proceedings/special issues | Very strong alloy-discovery/metallurgy audience if the doser is framed as enabling compositional exploration for powder AM. |
| MRS Spring Meeting | Materials Research Society | Abstract; mostly non-archival | Like MRS Fall; good if a spring symposium on autonomous experimentation / digital manufacturing exists. |
| **ASME IDETC/CIE** (DAC + CIE) | ASME | Full archival proceedings paper | **Best archival venue for the generative-CAD half** — LLM/code-based pipeline, parametric generation, reproducible design automation. |
| AIChE Annual Meeting | AIChE | Abstract; mostly non-archival | Good if framed as a dosing/dispensing or process-control / autonomous-experimentation module. |
| AI4Mat Workshop @ NeurIPS | AI4Mat community (NeurIPS) | Non-archival (OpenReview); tools/findings tracks | Good only if foregrounding autonomous-discovery / data-benchmark or the gen-CAD-AI pipeline; friendlier to tools than most ML venues. |
| AI4Mat Workshop @ ICLR | AI4Mat community (ICLR) | Non-archival (OpenReview) | As above; slightly easier for interdisciplinary tool papers. |
| **GOSH** (Gathering for Open Science Hardware) | Global OSH community | Unconference / hands-on sessions; non-archival | Excellent for the open-hardware dissemination mission, documentation feedback, and finding users/contributors. |
| ASTM ICAM | ASTM International | Abstract; proceedings vary | Good for reliable powder delivery / standardizable AM feedstock framing; weak for the gen-CAD story. |
| RAPID + TCT | SME / TCT | Abstract; mostly non-archival | Exposure to AM practitioners and machine developers; less archival/discovery-centric than SFF. |

## Stretch tier (gen-CAD / ML methods only)
| Venue | Format | Why it's a stretch |
|---|---|---|
| CVPR Workshops (3D/CAD generation) | Workshop paper / extended abstract | Only for clear technical novelty in LLM→parametric-CAD; the hardware won't be the draw. |
| SIGGRAPH / ACM TOG | Full archival technical paper | Only if the gen-CAD component is a standalone contribution (new CAD representations, B-rep generation). |
| NeurIPS (main) | Full archival paper | Only if the core novelty is an ML method/benchmark, not the doser. |
| ICML Workshops (AI4Science) | Non-archival workshop paper | Side venue for the AI/design methodology, not the apparatus paper. |
| ICLR (main) | Full archival paper | Only if the LLM/code-based CAD pipeline becomes the dominant ML contribution. |
| GRC on Combinatorial & High-Throughput Materials Science | Application-based; posters; no proceedings | Scientifically strong for alloy discovery, but not a citable paper; best for relationship-building once results mature. |

## Recommended roadmap

1. **Now / near-term:** submit an abstract + live demo to the **Accelerate
   Conference** — fastest, best-matched feedback from the SDL community.
2. **AM engineering depth:** target an archival **SFF Symposium** paper for the
   powder-handling/calibration engineering.
3. **Gen-CAD half:** if the LLM/code-based CAD pipeline is strong enough to stand
   alone, submit an archival **ASME IDETC/CIE (DAC/CIE)** paper.
4. **Dissemination:** present at **GOSH** for adoption, contributors, and
   open-documentation best practices.
5. **Escalate** to Faraday Discussions / MRS / TMS once a real closed-loop
   alloy-discovery result is in hand; treat the ML main conferences (NeurIPS /
   ICLR / SIGGRAPH) as stretch side-channels only for a spun-out methods paper.

## Caveats

- Several editions (ORNL SDL workshop, some AI4Mat/GOSH cycles) are documented as
  one-off or irregular — confirm the next cycle on the official page.
- "Archival" status varies by track and year (especially the ML workshops and
  ASTM ICAM); verify before relying on a citable proceedings paper.

See note **15** (venues), **16** (editors), **17** (suggested reviewers), and
**19** (consolidated recommendation).
