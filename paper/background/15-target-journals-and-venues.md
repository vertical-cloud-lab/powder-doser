# 15 — Target journals & venues for the powder-doser paper

*Edison-driven venue scouting (Batch 1). Raw artifacts:
`edison_artifacts/venues_sdl_hardware.{answer,references}.md` and
`edison_artifacts/venues_generative_cad.{answer,references}.md`; runner:
`edison_run_venues.py`. Two parallel `LITERATURE_HIGH` queries — one framing the
work as an open-hardware self-driving-lab (SDL) instrument paper, one framing it
as a higher-impact generative-CAD contribution.*

The instrument is a low-cost, open-source multi-powder doser for autonomous
additive-manufacturing (AM) alloy/materials discovery, assuming the closed-loop
gravimetric calibration algorithm (with extensive calibration data), the auger
auto-change mechanism, and dispensing of up to 50 unique powders are all in
place, and that the CAD is produced via an LLM/code-based generative-CAD
pipeline.

## TL;DR recommendation

- **Primary target: Digital Discovery (RSC).** It is the single best fit under
  *both* framings. Its scope explicitly covers SDL instruments, lab automation,
  open hardware, and open software, and it offers a **Commit** article type for
  open-source hardware/software. It has already published the most directly
  analogous work: a pellet dispensomixer/distributor (Hernández-del-Valle 2024,
  `10.1039/d4dd00198b`), the open-hardware digital pipette Commit (Yoshikawa
  2026, `10.1039/d5dd00336a`), and democratizing-SDL work that includes the
  project's own author list (Pelkie/Baird 2025).
- **Companion reproducibility paper: HardwareX (Elsevier)** — purpose-built for
  open scientific hardware (build files, BOM, validation), no APC.
- **Companion software object: JOSS or SoftwareX** — citable DOI for the
  calibration/control package (software-only; not for the main paper).
- **High-impact / generative-CAD-leaning alternatives:** The International
  Journal of Advanced Manufacturing Technology (direct precedent for an
  LLM→OpenSCAD pipeline, Daareyni 2025), ASME *Journal of Mechanical Design* /
  *JCISE* (if a genuine design-method contribution is made), and *Additive
  Manufacturing* (if AM/alloy-discovery outcomes are the headline).
- **Stretch (only with a real discovery campaign):** Nature Communications,
  Science Advances, Matter, Cell Reports Physical Science. These desk-reject
  "excellent platform/hardware" papers; they need *new science enabled by* the
  platform.

## SDL / open-hardware framing — tiered shortlist

| Tier | Venue | Publisher | ~IF / CiteScore | Fit |
|---|---|---|---|---|
| Primary | **Digital Discovery** | RSC | IF ~6.2 | Best overall; Commit format + analogous SDL/open-hardware precedent. |
| Primary | **HardwareX** | Elsevier | CiteScore ~5.7 (no APC) | Purpose-built open-hardware venue; ideal companion. |
| Secondary | Review of Scientific Instruments | AIP | IF ~1.6 | Classic instrument paper; values calibration rigor; weak on openness. |
| Secondary | Additive Manufacturing | Elsevier | IF ~11 | Strong if reframed as AM-alloy-discovery-enabling, not hardware-per-se. |
| Secondary | Additive Manufacturing Letters | Elsevier | IF ~4.2 | Rapid, concise AM-forward letter. |
| Secondary | SoftwareX | Elsevier | IF ~3.4 (no APC) | Companion software metapaper only. |
| Stretch | Nature Communications / Science Advances / Matter | NPG / AAAS / Cell | IF ~12–17 | Only with a paradigm-shifting autonomous-discovery result. |
| Stretch | Cell Reports Physical Science / npj Comput. Materials / ACS Central Science | Cell / NPG / ACS | IF ~8–13 | Need a strong physical-science / computational story beyond hardware. |
| Fallback | Materials & Design | Elsevier | IF ~7.6 | Materials-processing framing with the calibration dataset as the offering. |
| Fallback | IEEE/ASME Trans. Mechatronics | IEEE/ASME | IF ~6.1 | If novelty is the auger auto-change mechanism + control. |
| Fallback | Journal of Open Hardware / JOSS / PLOS ONE | Ubiquity / Open Journals / PLOS | — | Archival / software-only / technically-sound fallback. |

## Generative-CAD framing — where the CAD angle can go higher-impact

The key trade-off: this is an **applied** hardware/SDL paper that *uses*
generative CAD as a design methodology, not a pure ML/graphics *methods* paper.

- **Would accept (applied-systems-friendly):** Digital Discovery, IJAMT, ASME
  JMD/JCISE, Additive Manufacturing, Advanced Engineering Informatics, Computers
  in Industry, Computer-Aided Design, Proceedings of the Design Society
  (ICED/DESIGN).
- **Would likely desk-reject an applied paper (methods-only):** ACM Transactions
  on Graphics / SIGGRAPH, CVPR, ICCV/ECCV, NeurIPS, ICML, ICLR — these publish
  generative CAD only when the core contribution is a new ML/vision/graphics
  method (e.g., BrepGen at TOG, CAD-Llama at CVPR, Text2CAD at NeurIPS, SkexGen
  at ICML). Suitable only if a standalone generative-CAD method is spun out.

| Rank | Venue | Publisher | ~IF / h5 | Accepts applied HW/SDL? |
|---:|---|---|---|---|
| 1 | Digital Discovery | RSC | IF ~6.2 | Yes (best fit) |
| 2 | Additive Manufacturing | Elsevier | IF ~11 | Partial (AM outcomes) |
| 3 | Int. J. Advanced Manufacturing Technology | Springer | IF ~3.4 | Yes (LLM→OpenSCAD precedent) |
| 4 | ASME Journal of Mechanical Design | ASME | IF ~3.3 | Partial (design-method) |
| 5 | ASME JCISE | ASME | IF ~3.1 | Partial (computational pipeline) |
| 6 | Computer-Aided Design | Elsevier | IF ~3.0 | Partial (CAD-method) |
| 7 | Advanced Engineering Informatics | Elsevier | IF ~8.0 | Yes (digital-thread) |
| 8 | Computers in Industry | Elsevier | IF ~10 | Yes (deployable system) |
| 9 | Proceedings of the Design Society | CUP / Design Society | proceedings | Yes (agentic CAD case study) |
| 13–18 | ACM TOG, CVPR, ICLR, NeurIPS, ICML, ICCV/ECCV | ACM / IEEE-CVF / etc. | very high | No (methods only) |

## Recommended strategy

1. **Flagship → Digital Discovery (RSC)**, foregrounding the open-hardware SDL
   multi-powder doser with the calibration dataset, and presenting generative
   CAD as the enabling design methodology.
2. **Companion → HardwareX** for full reproducible build documentation (free).
3. **Companion → JOSS / SoftwareX** for the calibration/control software DOI.
4. **If the CAD methodology is strong enough to stand alone**, spin out a
   dedicated generative-CAD method paper for IJAMT or ASME JMD/JCISE (or, only
   with a genuine ML advance, a TOG/CVPR/NeurIPS submission).
5. **If a real closed-loop alloy-discovery campaign lands**, escalate the
   science story to Nature Communications / Science Advances.

See notes **16** (editors), **17** (likely reviewers), and **18** (target
conferences) for the people and meetings attached to these venues, and note
**19** for the consolidated recommendation.
