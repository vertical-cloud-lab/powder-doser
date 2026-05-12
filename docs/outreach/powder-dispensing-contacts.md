# Powder-Dispensing Outreach: Individuals and Organizations

This file catalogues individuals, academic groups, commercial vendors, and
open-source projects we could reach out to for help with **accurate, automated
powder dispensing** for chemistry and materials-science applications,
particularly multi-powder dosing for additive-manufacturing alloy discovery
(see [issue #10](https://github.com/vertical-cloud-lab/powder-doser/issues/10)
and the BYU NASA Space Grant proposal in
[issue #26](https://github.com/vertical-cloud-lab/powder-doser/issues/26)).

It is a living document — add entries as they come up and link the source so
later readers can follow the trail back.

## Sources surveyed

1. Accelerated Discovery forum thread,
   ["Accurate powder dispensing for chemistry and materials-science
   applications"](https://accelerated-discovery.org/t/accurate-powder-dispensing-for-chemistry-and-materials-science-applications/177)
   (May 2024 – July 2025), originated by @sgbaird. Participants and tools they
   mentioned are listed below as **[AD #N]**, where *N* is the post number in
   the thread.
2. [Pull request #29](https://github.com/vertical-cloud-lab/powder-doser/pull/29)
   — Edison Scientific `LITERATURE_HIGH` background notes covering the
   commercial and academic powder-dispensing landscape (`paper/background/01-…`
   and `paper/background/02-…`). Cited below as **[PR #29 — *file*]**.
3. The repository `README.md`, [`paper/main.tex`](../../paper/main.tex), and
   the POSE 2026 presentation linked from the README.
4. Public product pages and publications referenced from the above (only used
   to identify the relevant person/team, not transcribed in full).

Where a participant has not consented to be contacted publicly, only the
public handle / institutional affiliation is given here; please confirm the
preferred channel (email vs. forum thread vs. GitHub) before reaching out.

## A. Individuals — community participants and open-source builders

The following people have already engaged with this problem on a public
channel and are the highest-signal first contacts.

| Name / handle | Affiliation (if known) | Why reach out | Where to find them |
| --- | --- | --- | --- |
| **Sterling Baird** ([@sgbaird](https://github.com/sgbaird)) | BYU / Vertical Cloud Lab; maintainer of this repo | Originated the AD thread; using an Autotrickler v4 + A&D FX-120i with Pico-W control; survey author. | AD #1, #6, #8, #10, #11, #15, #20; repo maintainer |
| **@shijing** | — | Tagged in the opening post (AD #1) as a relevant contact; participated in related AD threads. | AD #1 |
| **@kthchow** (Kelvin T. H. Chow) | — | Posted the 3D-printed-spatula prototype (volume-calibrated scoops inspired by Cook *et al.*, *Nat. Protoc.* 2020) and a positive-displacement-pipette method after Alsenz *et al.* (*Powder Technol.* 2011); has hands-on data on accuracy/CV for sub-20 mg dosing. | AD #2, #3, #16 |
| **@loppe35** | — | Building a "low-budget automated dispensing module" using an auger + 20 g strain-gauge load cell salvaged from a jewellery scale; close to our concept, would benefit both ways from collaboration. | AD #4 |
| **@muon** | — | Working on partial-automation workflows where the bottleneck is *recovery* of powder after ball-milling / acoustic mixing (not just dispensing); has surveyed firearm-community trickler designs and powder-pipette repeatability. | AD #5, #7, #14 |
| **@mreish** | — | Demonstrated a relatively low-cost powder-dispensing platform (see Sterling's note + [YouTube demo](https://www.youtube.com/watch?v=7yBmL1Xw5Xg)). Explicitly invited by Sterling in AD #15 to "expand". | AD #15 |
| **Benji Maruyama** ([@benjimaruyama](https://accelerated-discovery.org/u/benjimaruyama)) | Air Force Research Laboratory (AFRL); ARES OS / self-driving-lab pioneer | Building a ceramics robot; explicitly asked the AD community for advice on Trajan/Mettler-Toledo, Chemspeed, Unchained Labs, Hamilton, Thermo Fisher (AD #19). Direct domain peer for our use case. | AD #19, #20 |
| **Filippos Tourlomousis** | Biological Lattice Industries / The Autonomous Project | Posted a ~\$100 automated powder dispenser for biopolymer formulation on [LinkedIn](https://www.linkedin.com/feed/update/urn:li:activity:7310752420093906945) (see AD #18); existence-proof of an extreme-low-cost design. | AD #18 (LinkedIn) |
| **Edward Mars** ([eamars](https://github.com/eamars)) | — | Maintainer of [OpenTrickler](https://github.com/eamars/OpenTrickler), the most mature open-source powder-trickler firmware/hardware project. | AD #6; GitHub |
| **Adam MacLean** (Autotrickler) | Autotrickler / `autotrickler.com` | Already supplied Sterling with Bluetooth-control instructions for the Autotrickler v4 (AD #6). Friendly commercial collaborator already in our network. | AD #6; product site |
| **Kenneth Vecchio** | UC San Diego, Department of Nanoengineering | PI of **HT-READ** (Charpagne *et al.*, *Acta Mater.* 2021; Vecchio group, 2021–2024) — the only published automated multi-powder + metal-AM integration to date (~50 alloy compositions / 24 h via custom ChemSpeed + 16-hopper ADF + DED). The group explicitly calls out manual powder handling as the largest remaining bottleneck — directly aligned with this project's gap. | [PR #29 — `01-…landscape.md`, `02-…academic-literature.md`] |
| **Marie-Agathe Charpagne** | University of Illinois Urbana-Champaign (formerly Vecchio lab) | First author on the HT-READ alloy-discovery paper(s); the conference-abstract thread on hopper-blend compositional fidelity is hers. | [PR #29 — `02-…academic-literature.md`] |
| **Tyler Bahr** | — | Author of the 2018 / 2020 studies that established the ±10 % tolerance and sub-10 mg performance degradation of pharma HTE dispensers — the de-facto benchmark we are trying to beat. | [PR #29 — `01-…landscape.md`] |
| **Tom Neirinck** | KU Leuven (alloy-discovery review in *Accounts of Materials Research* 2021, DOI [10.1021/accountsmr.1c00030](https://doi.org/10.1021/accountsmr.1c00030)) | Co-authored a recent review of automated alloy discovery covering powder-dosing constraints. | [PR #29 — `02-…academic-literature.md`] |
| **Andrew I. Cooper** | University of Liverpool, Materials Innovation Factory | PI behind **PowderBot** ([arXiv:2309.00544](https://arxiv.org/abs/2309.00544)) — mobile-robot solid dispensing. | AD #8; PR #29 |
| **Gerbrand Ceder** | UC Berkeley / LBNL | PI behind the **A-Lab** ([*Nature* 2023](https://www.nature.com/articles/s41586-023-06734-w)) — closed-loop inorganic synthesis with powder dispensing as a known bottleneck; SI and demo videos document their workarounds. | AD #8; PR #29 |
| **CMAC team / Alastair Florence (lead)** | University of Strathclyde, Centre for Continuous Manufacturing and Crystallisation (CMAC) | The pharma self-driving-lab community Sterling flagged for headway on sticky / static-charged powders ("CMAC Open Days 2025"). Worth attending Open Days or emailing directly. | AD #17 |

## B. Academic groups (additional, not already covered above)

These groups were surfaced through the PR #29 academic-literature notes
(`paper/background/02-powder-dispensing-academic-literature.md`) as
plausible technical collaborators on sub-gram, multi-powder, AM-feedstock-grade
dosing. They are listed by PI / first author of the most directly relevant
paper; consult the PR #29 references list for full citations.

- **Apurva Mehta / SLAC autonomous synthesis group** — combinatorial /
  high-throughput synthesis with powder feedstocks.
- **Helge Stein** (KIT) — high-throughput electrochemistry SDL, has dealt
  with sub-mg dosing of catalyst powders.
- **Alán Aspuru-Guzik group** (University of Toronto / Acceleration
  Consortium) — Self-Driving Labs umbrella; Acceleration Consortium has a
  general community channel relevant to powder handling.
- **Milad Abolhasani group** (NC State) — flow chemistry / autonomous
  materials, occasional powder-feed work.
- **Joshua Schrier group** (Fordham) — open-hardware autonomous chemistry;
  cited in PR #29 academic notes.

When emailing any of the above, please cite the specific paper that motivated
the contact (entries are in
`paper/background/02-powder-dispensing-academic-literature.md` in PR #29).

## C. Commercial vendors

Listed in approximate order of relevance to the < \$10 k multi-powder
metal-AM-grade gap that PR #29 identified. **MTI Corporation** was called
out in the issue's agent instructions and is included for completeness even
though it is more of a lab-equipment supplier than an automated-dosing
specialist.

| Vendor | Product line | Why relevant | Best contact route |
| --- | --- | --- | --- |
| **Mettler-Toledo** | Quantos QX1 / QX2 ("salt-shaker") solid dosing; CHRONECT robotic systems | The dominant pharma HTE dispenser; ±10 %, ~50–150 k\$, validated mostly on pharma powders. Benchmark to beat. | mettler-toledo.com → automation contact; AD #19 mentions Trajan/Mettler partnership. |
| **Chemspeed Technologies** | SWING / FLEX overhead gravimetric dispensers; the 16-hopper ADF used in HT-READ | Closest commercial analogue to the multi-powder workflow we want; HT-READ collaboration with Vecchio is documented. | chemspeed.com sales; UCSD HT-READ team can warm-intro. |
| **Unchained Labs** | Big Kahuna / Junior automated formulation | Mentioned in AD #19 by @benjimaruyama as a candidate; has a powder-dosing accessory. | unchainedlabs.com |
| **Hamilton Robotics** | Microlab STAR with solid-dispensing add-ons | AD #19 candidate; large installed base in pharma. | hamiltoncompany.com |
| **Thermo Fisher Scientific** | Various lab-automation lines | AD #19 candidate; broad portfolio, worth a scoping call. | thermofisher.com |
| **Trajan Scientific and Medical** | Distribution / OEM partner for Quantos in some regions | AD #19 candidate; named together with Mettler-Toledo. | trajanscimed.com |
| **MTI Corporation** (Richmond, CA) | Lab-scale powder feeders, glove-box-compatible vibratory and screw feeders, planetary mixers | Called out in this issue's agent instructions. Lower price point than the pharma HTE platforms; relevant as a component supplier (feeders, hoppers, micro-augers) we could integrate. | mtixtl.com — request a quote / engineering chat. |
| **Coperion K-Tron** | Loss-in-weight feeders (industrial, kg/h scale) | Industry leader for continuous LIW dosing; relevant only as a reference for control loops, not for our mass range. | coperion.com |
| **Schenck Process** | LIW feeders (industrial) | Same comment as Coperion. | schenckprocess.com |
| **Gericke** | LIW and volumetric feeders | Same comment. | gericke.net |
| **Brabender Technologie** | LIW feeders | Same comment. | brabender-technologie.com |
| **Movacolor** | Gravimetric micro-feeders for polymers | Smaller-mass LIW option than the above; some sub-gram capability. | movacolor.com |
| **Sartorius** | High-precision balances and Quantos competitors | Balance-side reference; useful for fast-response gravimetric feedback (cf. A&D FX-120i in AD #6). | sartorius.com |
| **Freeman Technology (FT4 Powder Rheometer)** | Flowability characterisation | *Not* a dispenser, but the de-facto powder-flowability instrument — useful for screening which feedstocks our doser can plausibly handle. | freemantech.co.uk |
| **A&D Weighing** (FX-120i, HR-100A) | High-precision lab balances with fast-response mode and RS-232 control | Already in Sterling's setup (AD #6, #10). | andinst.com; CE Products is the US reseller. |
| **CE Products Inc.** | US reseller of A&D balances + Autotrickler distribution | Already in our supply chain. | ceproducts.shop |
| **Autotrickler / Adam MacLean** | Autotrickler v4 trickler + scale combo | See entry in section A; already cooperated with Sterling on Bluetooth control. | autotrickler.com |
| **INSSTEK** | DED systems with **CVM** ("clogged vibration mechanism") and "blow-disk" powder feeders | Mentioned in AD #17 as a relevant DED-side powder-flow mechanism; potential reference for vibration-assisted flow. | insstek.com |
| **Emerald Cloud Lab** | Remote-operated lab incl. powder-handling instrumentation | Sterling pointed to their [instrumentation page](https://www.emeraldcloudlab.com/instrumentation/) in AD #11; useful design reference for the analytic-balance + dispensing workflow. | emeraldcloudlab.com |

## D. Open-source / community projects

| Project | Maintainer | Why relevant |
| --- | --- | --- |
| [**OpenTrickler**](https://github.com/eamars/OpenTrickler) | [@eamars](https://github.com/eamars) (Edward Mars) | Most mature open-source powder-trickler firmware + hardware. Direct prior art for an auger + load-cell architecture. (AD #6.) |
| [**ARES OS**](https://www.afrl.af.mil/) / **ARES-G** | Benji Maruyama (AFRL) | Self-driving-lab orchestration framework; the ceramics robot in AD #19 will likely run on or alongside ARES. |
| [**Acceleration Consortium**](https://acceleration.utoronto.ca/) | Aspuru-Guzik et al. | Hosts working groups and Slack channels where powder-handling comes up regularly. |
| [**A-Lab**](https://www.nature.com/articles/s41586-023-06734-w) (SI + videos) | Ceder group | Reference design for powder dispensing in closed-loop inorganic synthesis. |
| [**PowderBot**](https://arxiv.org/abs/2309.00544) | Cooper group | Mobile-robot powder-dispensing reference. |
| [**HT-READ**](https://doi.org/10.1016/j.actamat.2021.117196) | Vecchio group, UCSD | The closest published precedent to this project. |

## E. Suggested next actions

1. Post a short status update on the AD thread ([accelerated-discovery #177](https://accelerated-discovery.org/t/accurate-powder-dispensing-for-chemistry-and-materials-science-applications/177)) linking to this repository so existing participants (@kthchow, @loppe35, @muon, @mreish, @benjimaruyama, @shijing) can opt in.
2. Send a direct email to **Kenneth Vecchio / Marie-Agathe Charpagne** (UCSD / UIUC) referencing their HT-READ work and the manual-powder-handling bottleneck.
3. Request engineering-contact intros with **MTI Corporation** and **Chemspeed** for components / accessories (auger feeders, micro-hoppers, vibratory bowls).
4. Open a follow-up issue once the first round of replies comes in, summarising who is willing to collaborate and on what terms.
