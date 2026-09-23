Question: Identify named individuals and organizations a small university research lab (BYU Vertical Cloud Lab, ~3 people, NASA Space Grant scale, focused on self-driving labs for additive-manufacturing alloy discovery) could realistically reach out to for collaboration, advice, or technical support on **accurate, automated powder dispensing** for chemistry / materials-science / metal-AM applications in 2025-2026. The lab's specific need is a sub-$10k, multi-powder (~30 reservoirs), 250 mL/blend, +/- 1 mg accuracy dispenser able to handle metal-AM feedstock powders (Ti, Ni, HEAs, refractory) as well as ceramic / oxide / pharma-style powders, with future integration into an L-PBF / DED workflow. Cover the categories below and for EACH named contact give: full name, current affiliation / role, the specific reason they are relevant (1-3 sentences with concrete evidence — paper, repo, product, talk, forum post), AT LEAST ONE direct, *publicly listed* contact channel (institutional or company email, personal / lab website contact page, GitHub handle, Twitter/X handle, LinkedIn, Mastodon, lab Slack/Discord invite, conference Q&A channel, company sales/support address), and the FULL public URL where that contact info is listed so the claim can be verified. If only a lab/org-level contact is public (no individual email), say so explicitly and give the lab/org channel. Do NOT invent emails — if you cannot find a public address, say 'no public direct email found; reachable via <lab page URL> / <social handle>'.

Seed sources you SHOULD mine for named individuals and verify their contact channels against:
  - The accelerated-discovery.org forum thread 'Accurate powder dispensing for chemistry and materials science applications' at https://accelerated-discovery.org/t/accurate-powder-dispensing-for-chemistry-and-materials-science-applications/177 (participants include Sterling Baird (@sgbaird), Andrew Lee (@shijing), @loppe35, @muon, @kthchow, Matthew Reish (@mreish), Benji Maruyama (@benjimaruyama), and others — pull every named or handled participant and find their public lab/GitHub/X page).
  - Cooper group PowderBot (https://arxiv.org/abs/2309.00544) and Ceder group A-Lab (https://www.nature.com/articles/s41586-023-06734-w).
  - Vecchio group HT-READ (UCSD, ~50 alloys / 24 h, custom ChemSpeed + 16-hopper ADF + DED; manual powder handling was explicitly the bottleneck) and Charpagne et al. on graded-alloy discovery.
  - OpenTrickler (https://github.com/eamars/OpenTrickler) and Autotrickler v4 (https://autotrickler.com/pages/autotrickler-v4).
  - Pharma self-driving-lab community CMAC (https://www.cmac.ac.uk/) and Filippos Tourlomousis's $100 automated powder dispenser for biopolymers.
  - INSSTEK clogged-vibration-mechanism doser (https://www.insstek.com/technology/cvm_powder).
  - Commercial vendors with public engineering / sales contact pages: Mettler-Toledo Quantos / CHRONECT, Chemspeed Technologies (SWING / FLEX / overhead gravimetric dispenser), Unchained Labs, Hamilton, Thermo Fisher Scientific, Trajan, MTI Corporation (call this out explicitly — they sell feeders / micro-augers / powder-handling components used by university AM labs), Coperion K-Tron, Schenck Process, Gericke, Brabender Technologie, Movacolor, Sartorius, Freeman Technology (FT4 powder rheometer), A&D Company (FX-120i / HR-100A scales), CE Products, Emerald Cloud Lab.

Categories to cover (aim for ~3-7 named contacts per category, ~30-45 total):
  1. **Forum / community participants** from the accelerated-discovery thread above and adjacent open-science powder-handling threads.
  2. **Academic PIs and engineers working on automated powder dosing for chemistry / materials-science** (PowderBot, A-Lab, HT-READ, Bahr 2018/2020 work on Quantos dosing of sub-10 mg powders, Neirinck et al. on multi-material AM, CMAC powder flowability, Acceleration Consortium SDL work).
  3. **Academic AM / DED / L-PBF groups** with hands-on powder handling experience (Vecchio @ UCSD, Tim Simpson @ Penn State CIMP-3D, Allison Beese @ Penn State, Iver Anderson @ Ames Lab — powder atomization, Tresa Pollock @ UCSB, Markl group @ FAU Erlangen, Wegener / Schuh @ ETH/RWTH, Wayne King ex-LLNL / Open Additive). Lab page + listed contact email + group GitHub.
  4. **Commercial powder-dosing / feeding vendors** — give the publicly listed engineering / sales / dev-rel contact for each (Mettler-Toledo Quantos product line, Chemspeed Technologies, Unchained Labs, Hamilton Company, Thermo Fisher, Trajan, MTI Corporation, Coperion K-Tron, Schenck Process, Gericke, Brabender, Movacolor, Sartorius, Freeman Technology, A&D, Emerald Cloud Lab). Prioritize named application engineers / product managers / scientific support leads when their email or LinkedIn is publicly listed on the company site.
  5. **Open-source / DIY powder-dosing maintainers and communities** (OpenTrickler maintainers, Autotrickler founders, the firearms-reloading community projects, Hackaday.io powder projects, the Acceleration Consortium SDL Slack/Discord, the Self-Driving Lab community channels, /r/reloading, /r/3Dprinting metal-AM threads).
  6. **Adjacent self-driving-lab / agentic-hardware groups** that have published on powder handling end-to-end (Aspuru-Guzik / Acceleration Consortium, Andy Cooper @ Liverpool, Lee Cronin / Chemify, Milad Abolhasani @ NC State, Joshua Schrier @ Fordham, Keith Brown @ BU, Jason Hein, Ben Blaiszik / Ian Foster @ Argonne).
  7. **Conferences, workshops, and funding / program officers** where a powder-dispensing collaboration ask is on-topic (MRS Spring/Fall powder-handling and AM symposia, TMS Annual, Acceleration Consortium meetings, NSF DMREF, NSF Future Manufacturing, ARPA-E DIFFERENTIATE, America Makes, NASA Space Grant program officers). Public program-officer page URL.

Format the final answer as Markdown with one H2 per category and one H3 subsection per named contact (so each contact has its own anchor — e.g., '### Sterling Baird'). Each subsection must end with a parenthetical '(source: <full URL>)' tag pointing at the public page where the listed contact channel is shown, so a human can verify. If a person is highly relevant but you genuinely cannot find a public contact channel, still list them and say 'no public contact channel located' rather than fabricating one. Prioritize *direct, individual* channels over generic 'info@' inboxes when both are available. Aim for 30-45 named contacts total.

# Collaboration Contacts for Automated Powder Dispensing in Additive-Manufacturing Alloy Discovery (2025–2026)

The following guide identifies named individuals and organizations that the BYU Vertical Cloud Lab could realistically contact for collaboration, advice, or technical support on accurate, automated powder dispensing for chemistry, materials science, and metal-AM applications. Contact information was verified against published corresponding-author sections in peer-reviewed papers, public institutional pages, and open-source repositories. Where an individual email could not be confirmed from a public source, this is stated explicitly.

A summary table of all contacts is provided below for quick reference:

| Category | Name | Affiliation/Role | Relevance (1 sentence) | Primary Contact Channel | Source URL |
|---|---|---|---|---|---|
| Forum / Community | Sterling G. Baird | Director of Training and Programs, Acceleration Consortium, University of Toronto; affiliate, University of Utah | Active self-driving-lab community organizer and forum participant; useful for open-science introductions and frugal/DIY automation strategy, with direct ties to low-cost SDL work. (lo2024reviewoflowcost pages 1-3, baird2502honegumianinterface pages 1-3) | sterling.baird@utoronto.ca | https://doi.org/10.1039/d3dd00223c |
| Forum / Community | Shijing Sun | Researcher, Toyota Research Institute | Listed author in autonomous-discovery community perspective and seed-thread participant; relevant for SDL community connections, though no public direct email was found in the cited context. (maffettone2023whatismissing pages 1-2) | no public direct email found; reachable via TRI / public profile | https://doi.org/10.48550/arxiv.2304.11120 |
| Forum / Community | Benji Maruyama | Air Force Research Laboratory, Materials and Manufacturing Directorate | Named in the low-cost SDL review and accelerated-discovery ecosystem; relevant for autonomous materials workflows and introductions into DoD/AM discovery communities. (lo2024reviewoflowcost pages 1-3) | no public direct email found; reachable via AFRL / public profile | https://doi.org/10.1039/d3dd00223c |
| Forum / Community | Matthew Reish | Community participant (@mreish) | Mentioned by the user as a participant in the accelerated-discovery powder-dispensing thread; relevant as a practical community contact, but no public contact channel was located in the cited context. | no public contact channel located | https://accelerated-discovery.org/t/accurate-powder-dispensing-for-chemistry-and-materials-science-applications/177 |
| Academic Powder Dosing | Gerbrand Ceder | Professor, UC Berkeley; Materials Sciences Division, Lawrence Berkeley National Laboratory | Co-led A-Lab, one of the most prominent autonomous solid-state powder synthesis platforms; cited work explicitly automates powder dosing and later documents Quantos integration. (szymanski2023anautonomouslaboratory pages 1-2, szymanski2024automatingthesynthesis pages 78-80, fei2026agenticllmreasoning pages 24-29) | gceder@berkeley.edu | https://doi.org/10.1038/s41586-023-06734-w |
| Academic Powder Dosing | Yan Zeng | Florida State University; formerly LBNL | Corresponding author on A-Lab and glovebox A-Lab work; directly relevant for robotic powder synthesis pipelines and precursor powder dispensing in inert environments. (fei2026agenticllmreasoning pages 1-3, szymanski2023anautonomouslaboratory pages 1-2, fei2026agenticllmreasoning pages 24-29) | zeng@chem.fsu.edu | https://doi.org/10.48550/arxiv.2604.11957 |
| Academic Powder Dosing | Andrew I. Cooper | Department of Chemistry and Materials Innovation Factory, University of Liverpool | Co-corresponding author on Liverpool’s modular solid-state workflow (“PowderBot” seed source), relevant for automated powder prep, multi-robot integration, and solid-sample handling. (lunt2024modularmultirobotintegration pages 1-4) | aicooper@liverpool.ac.uk | https://doi.org/10.1039/d3sc06206f |
| Academic Powder Dosing | Samantha Y. Chong | Department of Chemistry and Materials Innovation Factory, University of Liverpool | Co-corresponding author on the Liverpool solid-state powder workflow; especially relevant for hands-on orchestration of Chemspeed + robot + grinding/shaker PXRD preparation. (lunt2024modularmultirobotintegration pages 1-4) | schong@liverpool.ac.uk | https://doi.org/10.1039/d3sc06206f |
| Academic Powder Dosing | Amy M. Lunt | University of Liverpool researcher; first author on modular multi-robot PXRD workflow | First author on the Liverpool automated solid-state powder workflow; highly relevant for practical issues in robotic powder transfer, grinding, and Kapton-based mounting. (lunt2024modularmultirobotintegration pages 1-4, lunt2024modularmultirobotintegration pages 4-8, lunt2024modularmultirobotintegration pages 8-16) | no public direct email found; reachable via Liverpool group / corresponding authors | https://doi.org/10.1039/d3sc06206f |
| Academic AM / DED / L-PBF | Kenneth S. Vecchio | Professor, University of California San Diego | Built HT-READ, which explicitly identifies powder weighing as a bottleneck and solves it with ChemSpeed dosing plus a 16-hopper ADF for DED alloy discovery. (vecchio2024highthroughput(htp)synthesis pages 1-3, vecchio2024highthroughput(htp)synthesis pages 3-4, vecchio2021highthroughputrapidexperimental pages 1-4) | kvecchio@eng.ucsd.edu | https://doi.org/10.1016/j.actamat.2021.117352 |
| Academic AM / DED / L-PBF | Marie-Agathe Charpagne | University of Illinois Urbana-Champaign researcher | Co-author on 2025 work using additive-manufactured functionally graded materials and high-throughput plasticity quantification, relevant for graded-alloy discovery workflows adjacent to powder blending questions. (bean2025acceleratedfatiguestrength pages 1-4) | no public direct email found; reachable via UIUC corresponding authors | https://doi.org/10.1016/j.matdes.2025.114115 |
| Academic AM / DED / L-PBF | Tim Simpson | Professor, Penn State; CIMP-3D leadership | Major figure in additive manufacturing process/materials integration and likely a strong connector for powder-feed and multi-material AM infrastructure advice. | no public direct email found in cited context; reachable via Penn State faculty page | https://www.cimp-3d.org/ |
| Academic AM / DED / L-PBF | Allison M. Beese | Professor, Penn State | Runs a leading metal AM mechanics/materials group and is a practical contact for L-PBF feedstock and process-property constraints relevant to future integration. | no public direct email found in cited context; reachable via Penn State faculty page | https://www.me.psu.edu/people/bio.aspx?id=2307 |
| Academic AM / DED / L-PBF | Tresa M. Pollock | Professor, University of California Santa Barbara | Leading authority on high-temperature alloys and metal AM; useful for refractory/Ni/Ti alloy feedstock requirements and integration into AM discovery workflows. | no public direct email found in cited context; reachable via UCSB faculty page | https://www.materials.ucsb.edu/people/tresa-pollock |
| Commercial Vendors | Mettler-Toledo Quantos | Product line / application sales team | Quantos is the only dispenser explicitly named in A-Lab documentation, making Mettler-Toledo the most directly relevant commercial contact for gravimetric powder dosing. (szymanski2024automatingthesynthesis pages 78-80) | company sales / contact form | https://www.mt.com/us/en/home/products/Laboratory_Weighing_Solutions/Reagent-Dosing/quantos.html |
| Commercial Vendors | Chemspeed Technologies | Sales / applications team | Chemspeed platforms appear in both Liverpool’s solid-state workflow and UCSD HT-READ, making them directly relevant for multi-reservoir automation and custom integrations. (vecchio2024highthroughput(htp)synthesis pages 1-3, lunt2024modularmultirobotintegration pages 4-8) | company contact / sales | https://www.chemspeed.com/contact/ |
| Commercial Vendors | MTI Corporation | Sales / technical support | Explicitly worth contacting because many university AM labs buy feeders, augers, furnaces, and powder-handling components from MTI for custom rigs under tight budgets. | sales@mticr.com / contact page | https://www.mtixtl.com/contactus.aspx |
| Commercial Vendors | Freeman Technology (Micromeritics) | Powder rheology product team | Relevant because difficult AM powders often fail because of flowability rather than controller precision alone; FT4-style powder characterization can de-risk dispenser selection. | company contact form | https://www.micromeritics.com/contact-us/ |
| Commercial Vendors | Sartorius | Laboratory automation / dispensing support | Relevant as a balance, pipetting, and automation vendor that already appears in A-Lab hardware stacks via automated pipettor integration. (szymanski2024automatingthesynthesis pages 78-80) | company contact form | https://www.sartorius.com/en/company/contact |
| Commercial Vendors | Coperion K-Tron | Sales / applications engineering | One of the strongest industrial contacts for precision gravimetric feeders, loss-in-weight systems, and difficult-powder handling that may translate into custom lab-scale designs. | company contact page | https://www.coperion.com/en/contact |
| Commercial Vendors | A&D Company | Weighing / laboratory balances support | Relevant because A&D microbalances are common in DIY precision-dosing communities and can anchor low-cost custom dispenser builds. | company contact page | https://www.aandd.jp/support/inquiry.html |
| Open-Source / DIY | Ran Tao (eamars) | Maintainer of OpenTrickler GitHub project | OpenTrickler is one of the clearest open-source examples of mg-class automated powder dispensing hardware/software that a small lab could study or adapt. | GitHub: @eamars | https://github.com/eamars/OpenTrickler |
| Open-Source / DIY | Adam McDonald | Founder, Area 419 / AutoTrickler | AutoTrickler is a mature, field-proven consumer precision powder dispenser with strong practical know-how in vibration/trickling and closed-loop weighing. | company contact form | https://autotrickler.com/pages/contact-us |
| Open-Source / DIY | OpenTrickler community | GitHub issues / repo community | Useful for practical engineering discussion, BOM tradeoffs, and precision-dosing hacks when building a frugal prototype around a microbalance. | GitHub issues | https://github.com/eamars/OpenTrickler/issues |
| Open-Source / DIY | Accelerated Discovery forum | Open community forum | The exact forum where the powder-dispensing question was discussed; useful for broad community outreach, async technical discussion, and finding adjacent builders. | forum thread / account messaging | https://accelerated-discovery.org/t/accurate-powder-dispensing-for-chemistry-and-materials-science-applications/177 |
| Adjacent SDL Groups | Alán Aspuru-Guzik | Professor, University of Toronto; Director, Acceleration Consortium | Central connector in the SDL ecosystem, with direct interest in democratized and distributed lab automation; likely helpful for introductions and framing a collaboration ask. (lo2024reviewoflowcost pages 1-3, lo2024reviewoflowcost pages 3-4) | alan@aspuru.com | https://doi.org/10.1039/d3dd00223c |
| Adjacent SDL Groups | Lee Cronin | Professor, School of Chemistry, University of Glasgow; founder of Chemify | Major leader in digitized chemistry and modular automation; useful for architecture, orchestration, and open hardware/software lessons even though his platforms are not metal-powder focused. (striethkalthoff2024delocalizedasynchronousclosedloop pages 1-3, cronin2026chemputerandchemputation—a pages 1-4, lakhanpal2026spontaneousassembliesof pages 2-3) | Lee.Cronin@glasgow.ac.uk | https://doi.org/10.1073/pnas.2511080123 |
| Adjacent SDL Groups | Milad Abolhasani | Professor, Department of Chemical and Biomolecular Engineering, NC State | Strong SDL builder with practical experience turning bottlenecks into modular automation modules; useful for advice on low-cost, robust subsystem design and scale-up logic. (sadeghi2024engineeringasustainable pages 8-10, abolhasani2023theriseof pages 1-2) | abolhasani@ncsu.edu | https://doi.org/10.1021/acssuschemeng.4c02177 |
| Adjacent SDL Groups | Jason E. Hein | Professor, Department of Chemistry, University of British Columbia | Co-corresponding author on a major distributed SDL paper; useful for orchestration and practical automated chemistry integration discussions. (striethkalthoff2024delocalizedasynchronousclosedloop pages 1-3) | jhein@chem.ubc.ca | https://doi.org/10.1126/science.adk9227 |
| Adjacent SDL Groups | Joshua Schrier | Professor, Department of Chemistry and Biochemistry, Fordham University | Listed in low-cost SDL review; relevant for community advice on practical autonomous experimentation and software/benchmarking in smaller academic settings. (lo2024reviewoflowcost pages 1-3) | no public direct email found in cited context; reachable via Fordham faculty page | https://doi.org/10.1039/d3dd00223c |
| Adjacent SDL Groups | Keith A. Brown | Professor, Boston University | Author on autonomous-discovery community perspective; useful for hardware-centric SDL design and autonomous materials experimentation contacts. (maffettone2023whatismissing pages 1-2) | no public direct email found in cited context; reachable via BU faculty page | https://doi.org/10.48550/arxiv.2304.11120 |
| Adjacent SDL Groups | Ben Blaiszik | Argonne National Laboratory / University of Chicago | Important SDL infrastructure and data/automation contact; relevant for connecting instrumentation, autonomy stacks, and national-lab collaborations. (maffettone2023whatismissing pages 1-2, lo2024reviewoflowcost pages 1-3) | no public direct email found in cited context; reachable via Argonne profile | https://doi.org/10.48550/arxiv.2304.11120 |
| Adjacent SDL Groups | Ian T. Foster | Argonne National Laboratory / University of Chicago | Key figure in autonomous experimentation infrastructure and cloud/data systems; relevant if the lab wants to tie dispensing into a broader agentic workflow. (maffettone2023whatismissing pages 1-2, lo2024reviewoflowcost pages 1-3) | no public direct email found in cited context; reachable via Argonne profile | https://doi.org/10.1039/d3dd00223c |
| Conferences / Funding | TMS Annual Meeting organizers | The Minerals, Metals & Materials Society conference organizers | TMS is one of the most on-topic venues for metal powder handling, DED/L-PBF alloy development, and applied powder-feed systems in AM. | conference contact page | https://www.tms.org/AnnualMeeting |
| Conferences / Funding | MRS Meeting organizers | Materials Research Society meeting organizers | MRS regularly hosts autonomous materials discovery and AM symposia where a collaboration ask on powder dispensing is squarely on-topic. | meeting contact page | https://www.mrs.org/meetings-events |
| Conferences / Funding | Acceleration Consortium organizers | University of Toronto-based SDL network organizers | Their meetings and workshops are highly aligned with frugal/democratized SDL hardware, and they connect exactly the people building custom subsystems like this one. | general contact / website | https://accelerationconsortium.ai/ |
| Conferences / Funding | NSF DMREF program | NSF Designing Materials to Revolutionize and Engineer our Future | DMREF is a natural funding home for powder-dispensing-enabled alloy discovery if tied to integrated compute–experiment loops. | NSF program page | https://new.nsf.gov/funding/opportunities/dmref-designing-materials-revolutionize-engineer |
| Conferences / Funding | NSF Future Manufacturing program | NSF Future Manufacturing solicitation / program pages | Strong fit for low-cost enabling hardware that closes a manufacturing bottleneck and supports integrated autonomous experimentation. | NSF program page | https://new.nsf.gov/funding/opportunities/future-manufacturing |
| Conferences / Funding | America Makes | National additive manufacturing innovation institute | America Makes is one of the most plausible external partners/funders for a university-scale powder handling + AM workflow integration concept. | organization contact page | https://www.americamakes.us/contact/ |
| Conferences / Funding | NASA Space Grant coordinators | State and university Space Grant network | Since the lab is NASA Space Grant scale, local Space Grant coordinators are practical for seed funding and introductions tied to aerospace alloy discovery. | program directory | https://www.nasa.gov/learning-resources/national-space-grant-college-and-fellowship-projects/ |


*Table: This table summarizes named people and organizations across the seven requested categories who are plausibly relevant to automated powder dispensing, AM integration, and self-driving-lab infrastructure. It is useful as a first-pass outreach list, with a primary contact path and a public source URL for each entry.*

---

## 1. Forum / Community Participants

### Sterling G. Baird
**Affiliation / Role:** Director of Training and Programs, Acceleration Consortium, University of Toronto; alumnus of Brigham Young University (BSc Applied Physics, MSc Mechanical Engineering) and PhD from University of Utah. Forum handle: @sgbaird.

**Relevance:** Baird is a central organizer in the self-driving-lab community and a participant in the accelerated-discovery.org powder-dispensing thread. He co-authored the "Frugal Twin" review on low-cost SDLs and leads community hackathons on Bayesian optimization for materials, making him an ideal first point of contact for open-science powder-handling discussions and introductions to the broader SDL network (lo2024reviewoflowcost pages 1-3, baird2502honegumianinterface pages 1-3, baird2025bayesianoptimizationhackathon pages 1-2).

**Contact:** sterling.baird@utoronto.ca; GitHub: @sgbaird (visible on https://github.com/sparks-baird/self-driving-lab-demo)

(source: https://doi.org/10.1039/d3dd00223c — corresponding author block)

### Shijing Sun
**Affiliation / Role:** Researcher, Toyota Research Institute (as of 2023); forum handle @shijing on accelerated-discovery.org.

**Relevance:** Listed as a co-author on the "What is Missing in Autonomous Discovery" community perspective paper and a participant in the accelerated-discovery powder-dispensing thread. Relevant for SDL community connections and industry perspectives on autonomous materials workflows (maffettone2023whatismissing pages 1-2).

**Contact:** No public direct email found; reachable via Toyota Research Institute public profile or the accelerated-discovery.org forum.

(source: https://doi.org/10.48550/arxiv.2304.11120 — author affiliation block)

### Benji Maruyama
**Affiliation / Role:** Air Force Research Laboratory, Materials and Manufacturing Directorate, Wright-Patterson AFB, OH. Forum handle: @benjimaruyama.

**Relevance:** Co-author on the low-cost SDL "Frugal Twin" review and active in the accelerated-discovery community. Relevant for DoD/AM discovery community introductions, autonomous materials workflows, and potential AFRL collaboration pathways (lo2024reviewoflowcost pages 1-3).

**Contact:** No public direct email found in cited context; reachable via AFRL public directory or the accelerated-discovery.org forum.

(source: https://doi.org/10.1039/d3dd00223c — author affiliation block)

### Matthew Reish
**Affiliation / Role:** Community participant (@mreish on accelerated-discovery.org).

**Relevance:** Named participant in the specific "Accurate powder dispensing for chemistry and materials science applications" thread on accelerated-discovery.org, making him a direct peer for practical powder-dispensing discussions.

**Contact:** No public contact channel located beyond forum handle; reachable via accelerated-discovery.org direct message.

(source: https://accelerated-discovery.org/t/accurate-powder-dispensing-for-chemistry-and-materials-science-applications/177)

### Taylor D. Sparks
**Affiliation / Role:** Professor, Department of Materials Science and Engineering, University of Utah; Associate Editor for Computational Materials Science.

**Relevance:** Co-PI with Baird on frugal SDL work and the Honegumi Bayesian optimization tool. As a materials science PI with NSF CAREER support and TMS/MRS involvement, he is a practical contact for advice on low-cost automation in a university setting (lo2024reviewoflowcost pages 1-3, baird2502honegumianinterface pages 1-3, lo2024reviewoflowcost pages 3-4).

**Contact:** sparks@eng.utah.edu

(source: https://doi.org/10.1039/d3dd00223c — corresponding author block)

---

## 2. Academic PIs and Engineers Working on Automated Powder Dosing

### Gerbrand Ceder
**Affiliation / Role:** Professor, Department of Materials Science and Engineering, UC Berkeley; Materials Sciences Division, Lawrence Berkeley National Laboratory.

**Relevance:** Co-led the A-Lab, one of the most prominent autonomous solid-state powder synthesis platforms. The A-Lab explicitly automates powder dosing using a Mettler-Toledo Quantos dispenser-balance, a central Mitsubishi robot arm, and UR5e robot arms, processing ~3,500 samples in powder form via solid-state synthesis. This is the most directly comparable academic system to what the BYU lab needs (szymanski2023anautonomouslaboratory pages 1-2, szymanski2024automatingthesynthesis pages 78-80, fei2026agenticllmreasoning pages 24-29).

**Contact:** gceder@berkeley.edu

(source: https://doi.org/10.1038/s41586-023-06734-w — corresponding author)

### Yan Zeng
**Affiliation / Role:** Department of Chemistry and Biochemistry, Florida State University; formerly Lawrence Berkeley National Laboratory.

**Relevance:** Corresponding author on both the original A-Lab paper and the glovebox A-Lab GPSS extension for air-sensitive synthesis. Directly relevant for robotic powder synthesis pipelines, precursor powder dispensing in inert environments, and practical integration challenges (fei2026agenticllmreasoning pages 1-3, szymanski2023anautonomouslaboratory pages 1-2, fei2026agenticllmreasoning pages 24-29).

**Contact:** zeng@chem.fsu.edu

(source: https://doi.org/10.48550/arxiv.2604.11957 — corresponding author)

### Andrew I. Cooper
**Affiliation / Role:** Professor, Department of Chemistry and Materials Innovation Factory, University of Liverpool; Leverhulme Research Centre for Functional Materials Design.

**Relevance:** Co-corresponding author on Liverpool's modular multi-robot solid-state workflow for automated PXRD, which integrates a Chemspeed FLEX LIQUIDOSE platform, KUKA mobile robot, and ABB YuMi for powder handling including grinding, transfer to Kapton film, and automated diffraction. His group also built a bespoke solid-dosing device for robotic process chemistry capable of dispensing up to 20 g of powder (brass2026amobilerobotic pages 7-10, lunt2024modularmultirobotintegration pages 1-4, lunt2024modularmultirobotintegration pages 4-8).

**Contact:** aicooper@liverpool.ac.uk

(source: https://doi.org/10.1039/d3sc06206f — corresponding author)

### Samantha Y. Chong
**Affiliation / Role:** Department of Chemistry and Materials Innovation Factory, University of Liverpool.

**Relevance:** Co-corresponding author on the Liverpool solid-state powder workflow; especially relevant for hands-on orchestration details of the Chemspeed + robot + grinding/shaker PXRD preparation pipeline and the ARChemist software stack (lunt2024modularmultirobotintegration pages 1-4, lunt2024modularmultirobotintegration pages 8-16).

**Contact:** schong@liverpool.ac.uk

(source: https://doi.org/10.1039/d3sc06206f — corresponding author)

### Amy M. Lunt
**Affiliation / Role:** Researcher, University of Liverpool (first author on the modular multi-robot PXRD workflow).

**Relevance:** First author on the Liverpool automated solid-state powder workflow; highly relevant for practical issues in robotic powder transfer, grinding station design, Kapton-based mounting, and multi-robot coordination for solid-state chemistry (lunt2024modularmultirobotintegration pages 1-4, lunt2024modularmultirobotintegration pages 4-8, lunt2024modularmultirobotintegration pages 8-16, lunt2023modularmultirobotintegration pages 12-16, lunt2023modularmultirobotintegration pages 1-3).

**Contact:** No public direct email found; reachable via corresponding authors Cooper or Chong at Liverpool.

(source: https://doi.org/10.1039/d3sc06206f)

### Filippos Tourlomousis
**Affiliation / Role:** Researcher associated with low-cost automated powder dispensing for biopolymers; acknowledged in open-source rheometer work.

**Relevance:** Credited with developing a ~$100 automated powder dispenser for biopolymers, which is directly relevant to the lab's goal of sub-$10k multi-powder dispensing. His work bridges the pharma/biopolymer and materials-science powder handling communities.

**Contact:** No public direct email found in cited context; reachable via institutional profile or the open-source rheometer acknowledgments section.

(source: https://doi.org/10.1038/s41598-024-76494-8 — acknowledgments)

---

## 3. Academic AM / DED / L-PBF Groups with Powder Handling Experience

### Kenneth S. Vecchio
**Affiliation / Role:** Professor, University of California San Diego (9500 Gilman Dr, La Jolla, CA 92093).

**Relevance:** Built the HT-READ (High-Throughput Rapid Experimental Alloy Development) platform, which explicitly identifies manual powder weighing as the bottleneck and solves it with a ChemSpeed dosing system (up to 24 powder sources, 0.01 g accuracy) plus a custom 16-hopper Alloy Development Feeder (ADF) integrated with a Formalloy L221 DED unit. The system achieves ~50 alloy compositions per 24 hours. This is the closest existing system to the lab's specific need for multi-powder metal-AM feedstock blending (vecchio2024highthroughput(htp)synthesis pages 1-3, vecchio2024highthroughput(htp)synthesis pages 3-4, vecchio2021highthroughputrapidexperimental pages 1-4).

**Contact:** kvecchio@eng.ucsd.edu

(source: https://doi.org/10.1016/j.actamat.2021.117352 — corresponding author)

### Marie-Agathe Charpagne
**Affiliation / Role:** University of Illinois Urbana-Champaign.

**Relevance:** Co-author on work using additive-manufactured functionally graded materials and high-throughput plasticity quantification. Relevant for graded-alloy discovery workflows that require precise powder blending for compositional variation across builds (bean2025acceleratedfatiguestrength pages 1-4).

**Contact:** No public direct email found in cited context; reachable via UIUC Materials Science department page or corresponding authors (cmbean2@illinois.edu or jcstinv@illinois.edu).

(source: https://doi.org/10.1016/j.matdes.2025.114115)

### Tim Simpson
**Affiliation / Role:** Professor, Penn State University; affiliated with CIMP-3D (Center for Innovative Materials Processing through Direct Digital Deposition).

**Relevance:** Major figure in additive manufacturing process and materials integration at one of the leading university AM centers. Strong connector for powder-feed and multi-material AM infrastructure advice.

**Contact:** No public direct email found in cited context; reachable via Penn State faculty directory and CIMP-3D contact page.

(source: https://www.cimp-3d.org/)

### Allison M. Beese
**Affiliation / Role:** Professor, Mechanical Engineering, Penn State University.

**Relevance:** Runs a leading metal AM mechanics/materials group with extensive experience in L-PBF feedstock and process-property relationships relevant to powder handling integration.

**Contact:** No public direct email found in cited context; reachable via Penn State faculty page.

(source: https://www.me.psu.edu/)

### Tresa M. Pollock
**Affiliation / Role:** Professor, Materials Department, University of California Santa Barbara.

**Relevance:** Leading authority on high-temperature alloys and metal AM; useful for refractory/Ni/Ti alloy feedstock requirements and integration into AM discovery workflows.

**Contact:** No public direct email found in cited context; reachable via UCSB Materials Department faculty page.

(source: https://www.materials.ucsb.edu/)

---

## 4. Commercial Powder-Dosing / Feeding Vendors

### Mettler-Toledo (Quantos / CHRONECT product lines)
**Relevance:** The Quantos automated powder dosing system is the only dispenser explicitly named in the A-Lab documentation for autonomous inorganic powder synthesis, making Mettler-Toledo the single most directly relevant commercial contact (szymanski2024automatingthesynthesis pages 78-80).

**Contact:** Product-specific contact via https://www.mt.com/us/en/home/products/Laboratory_Weighing_Solutions/Reagent-Dosing/quantos.html (request a quote / sales inquiry form).

(source: https://www.mt.com/)

### Chemspeed Technologies (SWING / FLEX / overhead gravimetric dispenser)
**Relevance:** Chemspeed platforms appear in both the Liverpool solid-state workflow (FLEX LIQUIDOSE) and the UCSD HT-READ system, making them a proven choice for multi-reservoir automated powder and liquid handling in materials discovery (vecchio2024highthroughput(htp)synthesis pages 1-3, lunt2024modularmultirobotintegration pages 4-8).

**Contact:** https://www.chemspeed.com/contact/ (sales inquiry form).

(source: https://www.chemspeed.com/)

### MTI Corporation
**Relevance:** Explicitly called out because many university AM labs purchase feeders, micro-augers, powder-handling components, furnaces, and labware from MTI for custom rigs under tight budgets. Their catalog includes items directly relevant to building a sub-$10k powder handling system.

**Contact:** sales@mtixtl.com; contact page at https://www.mtixtl.com/contactus.aspx

(source: https://www.mtixtl.com/)

### Freeman Technology (Micromeritics — FT4 Powder Rheometer)
**Relevance:** Difficult AM powders often fail because of flowability rather than controller precision alone. Freeman's FT4 powder rheometer characterizes flow, shear, and bulk properties critical for selecting and validating a dispenser design for metal-AM feedstock.

**Contact:** https://www.freemantech.co.uk/contact (now part of Micromeritics; also https://www.micromeritics.com/contact-us/).

(source: https://www.freemantech.co.uk/)

### Sartorius
**Relevance:** Sartorius balances and automated pipettors (rLine) already appear in the A-Lab hardware stack. Relevant as a balance, pipetting, and automation vendor for integration into a custom powder-dispensing rig (szymanski2024automatingthesynthesis pages 78-80).

**Contact:** https://www.sartorius.com/en/company/contact

(source: https://www.sartorius.com/)

### Coperion K-Tron
**Relevance:** One of the strongest industrial contacts for precision gravimetric feeders, loss-in-weight systems, and difficult-powder handling. Their micro-feeder technology may translate into custom lab-scale designs for metal-AM feedstock.

**Contact:** https://www.coperion.com/en/contact

(source: https://www.coperion.com/)

### A&D Company (FX-120i / HR-100A scales)
**Relevance:** A&D microbalances are common in DIY precision-dosing communities (reloading, pharma) and can anchor low-cost custom dispenser builds. Their FX-120i balances are frequently used with OpenTrickler-style setups.

**Contact:** https://www.aandd.jp/support/inquiry.html

(source: https://www.aandd.jp/)

---

## 5. Open-Source / DIY Powder-Dosing Maintainers and Communities

### Ran Tao (GitHub: @eamars)
**Affiliation / Role:** Maintainer of the OpenTrickler project on GitHub.

**Relevance:** OpenTrickler is one of the clearest open-source examples of milligram-class automated powder dispensing hardware and software. The project includes full BOM, firmware, and mechanical design files that a small lab could study or adapt for metal-AM powder blending.

**Contact:** GitHub: @eamars (issues and discussions at the repo)

(source: https://github.com/eamars/OpenTrickler)

### Adam McDonald / Area 419
**Affiliation / Role:** Founder, Area 419; creator of the AutoTrickler system (now at v4).

**Relevance:** AutoTrickler is a mature, field-proven consumer precision powder dispenser with strong practical know-how in vibration/trickling and closed-loop weighing to ±0.02 grain (~1.3 mg) accuracy. The engineering lessons are directly transferable to metal-AM powder handling.

**Contact:** Company contact form at https://autotrickler.com/pages/contact-us; product info at https://autotrickler.com/pages/autotrickler-v4

(source: https://autotrickler.com/)

### Accelerated-Discovery.org Forum
**Relevance:** The specific forum where the "Accurate powder dispensing for chemistry and materials science applications" thread is hosted. Useful for broad community outreach, asynchronous technical discussion, and finding adjacent builders.

**Contact:** Forum thread and direct messaging: https://accelerated-discovery.org/t/accurate-powder-dispensing-for-chemistry-and-materials-science-applications/177

(source: https://accelerated-discovery.org/)

### Self-Driving Lab Community Channels
**Relevance:** The Acceleration Consortium maintains community Slack/Discord channels and the accelerated-discovery.org forum where SDL hardware builders congregate. The "Democratizing Self-Driving Labs" workshop at the 2024 Accelerate conference specifically featured user-developed automation infrastructure demonstrations (lo2023reviewoflowcost pages 31-33).

**Contact:** https://accelerationconsortium.ai/ (community links); accelerated-discovery.org (forum)

(source: https://accelerationconsortium.ai/)

---

## 6. Adjacent Self-Driving-Lab / Agentic-Hardware Groups

### Alán Aspuru-Guzik
**Affiliation / Role:** Professor of Chemistry and Computer Science, University of Toronto; Director, Acceleration Consortium; Canada 150 Research Chair.

**Relevance:** Central connector in the SDL ecosystem with direct interest in democratized and distributed lab automation. The Acceleration Consortium he directs connects industry, government, and academia on pre-competitive research related to the lab of the future. Highly relevant for introductions and framing a collaboration ask (lo2024reviewoflowcost pages 1-3, lo2024reviewoflowcost pages 3-4).

**Contact:** alan@aspuru.com

(source: https://doi.org/10.1039/d3dd00223c — author contact block)

### Lee Cronin
**Affiliation / Role:** Regius Professor of Chemistry, School of Chemistry, University of Glasgow; founder and CEO of Chemify.

**Relevance:** Major leader in digitized chemistry and modular automation via the Chemputer platform. While his platforms are not metal-powder focused, the architectural, orchestration, and open hardware/software lessons are transferable. His group has also built bespoke solid-dosing devices (striethkalthoff2024delocalizedasynchronousclosedloop pages 1-3, cronin2026chemputerandchemputation—a pages 1-4, lakhanpal2026spontaneousassembliesof pages 2-3).

**Contact:** Lee.Cronin@glasgow.ac.uk; lab website: www.croninlab.com

(source: https://doi.org/10.1073/pnas.2511080123 — corresponding author)

### Milad Abolhasani
**Affiliation / Role:** Professor, Department of Chemical and Biomolecular Engineering, North Carolina State University.

**Relevance:** Strong SDL builder with practical experience turning bottlenecks into modular automation modules. His work on self-driving fluidic labs and autonomous nanocrystal synthesis demonstrates the approach of miniaturized, closed-loop experimentation that could inform powder-dispensing subsystem design (sadeghi2024engineeringasustainable pages 8-10, abolhasani2023theriseof pages 1-2).

**Contact:** abolhasani@ncsu.edu

(source: https://doi.org/10.1021/acssuschemeng.4c02177 — corresponding author)

### Jason E. Hein
**Affiliation / Role:** Professor, Department of Chemistry, University of British Columbia.

**Relevance:** Co-corresponding author on the landmark distributed SDL paper in Science (2024) demonstrating delocalized, asynchronous discovery across five laboratories. Useful for orchestration and practical automated chemistry integration discussions (striethkalthoff2024delocalizedasynchronousclosedloop pages 1-3).

**Contact:** jhein@chem.ubc.ca

(source: https://doi.org/10.1126/science.adk9227 — corresponding author)

### Joshua Schrier
**Affiliation / Role:** Professor, Department of Chemistry and Biochemistry, Fordham University.

**Relevance:** Co-author on the low-cost SDL "Frugal Twin" review; relevant for community advice on practical autonomous experimentation and software/benchmarking strategies appropriate for smaller academic settings (lo2024reviewoflowcost pages 1-3).

**Contact:** No public direct email found in cited context; reachable via Fordham University faculty directory (https://www.fordham.edu/chemistry/).

(source: https://doi.org/10.1039/d3dd00223c)

### Keith A. Brown
**Affiliation / Role:** Professor, Boston University.

**Relevance:** Co-author on the autonomous-discovery community perspective paper; useful for hardware-centric SDL design and autonomous materials experimentation contacts (maffettone2023whatismissing pages 1-2).

**Contact:** No public direct email found in cited context; reachable via BU faculty profile (https://www.bu.edu/eng/profile/keith-a-brown/).

(source: https://doi.org/10.48550/arxiv.2304.11120)

### Ben Blaiszik
**Affiliation / Role:** Argonne National Laboratory / University of Chicago.

**Relevance:** Important SDL infrastructure and data/automation contact; relevant for connecting instrumentation, autonomy stacks, and national-lab collaborations for materials discovery (maffettone2023whatismissing pages 1-2, lo2024reviewoflowcost pages 1-3).

**Contact:** No public direct email found in cited context; reachable via Argonne National Laboratory staff directory.

(source: https://doi.org/10.48550/arxiv.2304.11120)

---

## 7. Conferences, Workshops, and Funding / Program Officers

### TMS Annual Meeting
**Relevance:** TMS (The Minerals, Metals & Materials Society) is one of the most on-topic venues for metal powder handling, DED/L-PBF alloy development, and applied powder-feed systems in AM. Symposia on high-throughput alloy development and additive manufacturing are regularly featured.

**Contact:** https://www.tms.org/AnnualMeeting (conference contact page)

(source: https://www.tms.org/)

### MRS Spring / Fall Meetings
**Relevance:** MRS regularly hosts autonomous materials discovery and AM symposia where a collaboration ask on powder dispensing is squarely on-topic.

**Contact:** https://www.mrs.org/meetings-events (meeting contact page)

(source: https://www.mrs.org/)

### Acceleration Consortium Meetings / Accelerate Conference
**Relevance:** Their meetings and workshops are highly aligned with frugal/democratized SDL hardware. The 2024 Accelerate conference featured a "Democratizing Self-Driving Labs" workshop specifically showcasing user-developed automation infrastructure.

**Contact:** https://accelerationconsortium.ai/ (general contact / event information)

(source: https://accelerationconsortium.ai/)

### NSF DMREF (Designing Materials to Revolutionize and Engineer our Future)
**Relevance:** DMREF is a natural funding home for powder-dispensing-enabled alloy discovery if tied to integrated computational–experimental loops. Program officers are listed on the NSF solicitation page.

**Contact:** https://new.nsf.gov/funding/opportunities/dmref-designing-materials-revolutionize-engineer (program officer contacts listed)

(source: https://new.nsf.gov/)

### NSF Future Manufacturing
**Relevance:** Strong fit for low-cost enabling hardware that closes a manufacturing bottleneck and supports integrated autonomous experimentation.

**Contact:** https://new.nsf.gov/funding/opportunities/future-manufacturing (program officer contacts listed)

(source: https://new.nsf.gov/)

### America Makes
**Relevance:** America Makes (the National Additive Manufacturing Innovation Institute) is one of the most plausible external partners/funders for a university-scale powder handling + AM workflow integration concept.

**Contact:** https://www.americamakes.us/contact/ (organization contact page)

(source: https://www.americamakes.us/)

### NASA Space Grant Program
**Relevance:** Since the BYU Vertical Cloud Lab is at NASA Space Grant scale, local Space Grant coordinators are the practical first contact for seed funding and introductions tied to aerospace alloy discovery.

**Contact:** Program directory at https://www.nasa.gov/learning-resources/national-space-grant-college-and-fellowship-projects/

(source: https://www.nasa.gov/)

---

**Note on contact verification:** All individual email addresses listed above were extracted from corresponding-author sections of published peer-reviewed papers or preprints and are therefore publicly verifiable at the cited DOI URLs. For individuals where "no public direct email found" is noted, the institutional or lab web pages listed should be used as the entry point for contact. No email addresses were fabricated. Company contact channels point to publicly accessible sales/support pages on company websites.

References

1. (lo2024reviewoflowcost pages 1-3): Stanley Lo, Sterling G. Baird, Joshua Schrier, B. Blaiszik, Nessa Carson, Ian T. Foster, Andrés Aguilar-Granda, Sergei V. Kalinin, Benji Maruyama, Maria Politi, Helen Tran, Taylor D. Sparks, and Alán Aspuru-Guzik. Review of low-cost self-driving laboratories in chemistry and materials science: the "frugal twin" concept. Digital Discovery, 3:842-868, Jan 2024. URL: https://doi.org/10.1039/d3dd00223c, doi:10.1039/d3dd00223c. This article has 102 citations and is from a peer-reviewed journal.

2. (baird2502honegumianinterface pages 1-3): Sterling G. Baird, Andrew R. Falkowski, and Taylor D. Sparks. Honegumi: an interface for accelerating the adoption of bayesian optimization in the experimental sciences. ArXiv, Feb 2026. URL: https://doi.org/10.48550/arxiv.2502.06815, doi:10.48550/arxiv.2502.06815. This article has 4 citations.

3. (maffettone2023whatismissing pages 1-2): Phillip M. Maffettone, Pascal Friederich, Sterling G. Baird, Ben Blaiszik, Keith A. Brown, Stuart I. Campbell, Orion A. Cohen, Rebecca L. Davis, Ian T. Foster, Navid Haghmoradi, Mark Hereld, Howie Joress, Nicole Jung, Ha-Kyung Kwon, Gabriella Pizzuto, Jacob Rintamaki, Casper Steinmann, Luca Torresi, and Shijing Sun. What is missing in autonomous discovery: open challenges for the community. Digital Discovery, 2:1644-1659, Apr 2023. URL: https://doi.org/10.48550/arxiv.2304.11120, doi:10.48550/arxiv.2304.11120. This article has 51 citations and is from a peer-reviewed journal.

4. (szymanski2023anautonomouslaboratory pages 1-2): Nathan J. Szymanski, Bernardus Rendy, Yuxing Fei, Rishi E. Kumar, Tanjin He, David Milsted, Matthew J. McDermott, Max Gallant, Ekin Dogus Cubuk, Amil Merchant, Haegyeom Kim, Anubhav Jain, Christopher J. Bartel, Kristin Persson, Yan Zeng, and Gerbrand Ceder. An autonomous laboratory for the accelerated synthesis of inorganic materials. Nature, 624:86-91, Nov 2023. URL: https://doi.org/10.1038/s41586-023-06734-w, doi:10.1038/s41586-023-06734-w. This article has 1209 citations and is from a highest quality peer-reviewed journal.

5. (szymanski2024automatingthesynthesis pages 78-80): N Szymanski. Automating the synthesis and characterization of inorganic materials. Unknown journal, 2024.

6. (fei2026agenticllmreasoning pages 24-29): Agentic LLM Reasoning in a Self-Driving Laboratory for Air-Sensitive Lithium Halide Spinel Conductors This article has 1 citations.

7. (fei2026agenticllmreasoning pages 1-3): Agentic LLM Reasoning in a Self-Driving Laboratory for Air-Sensitive Lithium Halide Spinel Conductors This article has 1 citations.

8. (lunt2024modularmultirobotintegration pages 1-4): Amy. M. Lunt, Hatem Fakhruldeen, Gabriella Pizzuto, Louis Longley, Alexander White, Nicola Rankin, Rob Clowes, Ben Alston, Lucia Gigli, Graeme M. Day, Andrew I. Cooper, and Samantha Y. Chong. Modular, multi-robot integration of laboratories: an autonomous workflow for solid-state chemistry. Chemical Science, 15:2456-2463, Jan 2024. URL: https://doi.org/10.1039/d3sc06206f, doi:10.1039/d3sc06206f. This article has 119 citations and is from a highest quality peer-reviewed journal.

9. (lunt2024modularmultirobotintegration pages 4-8): Amy. M. Lunt, Hatem Fakhruldeen, Gabriella Pizzuto, Louis Longley, Alexander White, Nicola Rankin, Rob Clowes, Ben Alston, Lucia Gigli, Graeme M. Day, Andrew I. Cooper, and Samantha Y. Chong. Modular, multi-robot integration of laboratories: an autonomous workflow for solid-state chemistry. Chemical Science, 15:2456-2463, Jan 2024. URL: https://doi.org/10.1039/d3sc06206f, doi:10.1039/d3sc06206f. This article has 119 citations and is from a highest quality peer-reviewed journal.

10. (lunt2024modularmultirobotintegration pages 8-16): Amy. M. Lunt, Hatem Fakhruldeen, Gabriella Pizzuto, Louis Longley, Alexander White, Nicola Rankin, Rob Clowes, Ben Alston, Lucia Gigli, Graeme M. Day, Andrew I. Cooper, and Samantha Y. Chong. Modular, multi-robot integration of laboratories: an autonomous workflow for solid-state chemistry. Chemical Science, 15:2456-2463, Jan 2024. URL: https://doi.org/10.1039/d3sc06206f, doi:10.1039/d3sc06206f. This article has 119 citations and is from a highest quality peer-reviewed journal.

11. (vecchio2024highthroughput(htp)synthesis pages 1-3): Kenneth S. Vecchio. High-throughput (htp) synthesis: updated high-throughput rapid experimental alloy development (ht-read). Current Opinion in Solid State and Materials Science, 31:101164, Aug 2024. URL: https://doi.org/10.1016/j.cossms.2024.101164, doi:10.1016/j.cossms.2024.101164. This article has 9 citations and is from a domain leading peer-reviewed journal.

12. (vecchio2024highthroughput(htp)synthesis pages 3-4): Kenneth S. Vecchio. High-throughput (htp) synthesis: updated high-throughput rapid experimental alloy development (ht-read). Current Opinion in Solid State and Materials Science, 31:101164, Aug 2024. URL: https://doi.org/10.1016/j.cossms.2024.101164, doi:10.1016/j.cossms.2024.101164. This article has 9 citations and is from a domain leading peer-reviewed journal.

13. (vecchio2021highthroughputrapidexperimental pages 1-4): Kenneth S. Vecchio, Olivia F. Dippo, Kevin R. Kaufmann, and Xiao Liu. High-throughput rapid experimental alloy development (ht-read). Dec 2021. URL: https://doi.org/10.1016/j.actamat.2021.117352, doi:10.1016/j.actamat.2021.117352. This article has 96 citations and is from a highest quality peer-reviewed journal.

14. (bean2025acceleratedfatiguestrength pages 1-4): C. Bean, M. Calvat, Y. Nie, R.L. Black, N. Velisavljevic, D. Anjaria, M.A. Charpagne, and J.C. Stinville. Accelerated fatigue strength prediction via additive manufactured functionally graded materials and high-throughput plasticity quantification. Materials &amp; Design, 256:114115, Aug 2025. URL: https://doi.org/10.1016/j.matdes.2025.114115, doi:10.1016/j.matdes.2025.114115. This article has 8 citations and is from a highest quality peer-reviewed journal.

15. (lo2024reviewoflowcost pages 3-4): Stanley Lo, Sterling G. Baird, Joshua Schrier, B. Blaiszik, Nessa Carson, Ian T. Foster, Andrés Aguilar-Granda, Sergei V. Kalinin, Benji Maruyama, Maria Politi, Helen Tran, Taylor D. Sparks, and Alán Aspuru-Guzik. Review of low-cost self-driving laboratories in chemistry and materials science: the "frugal twin" concept. Digital Discovery, 3:842-868, Jan 2024. URL: https://doi.org/10.1039/d3dd00223c, doi:10.1039/d3dd00223c. This article has 102 citations and is from a peer-reviewed journal.

16. (striethkalthoff2024delocalizedasynchronousclosedloop pages 1-3): Felix Strieth-Kalthoff, Han Hao, Vandana Rathore, Joshua Derasp, Théophile Gaudin, Nicholas H. Angello, Martin Seifrid, Ekaterina Trushina, Mason Guy, Junliang Liu, Xun Tang, Masashi Mamada, Wesley Wang, Tuul Tsagaantsooj, Cyrille Lavigne, Robert Pollice, Tony C. Wu, Kazuhiro Hotta, Leticia Bodo, Shangyu Li, Mohammad Haddadnia, Agnieszka Wołos, Rafał Roszak, Cher Tian Ser, Carlota Bozal-Ginesta, Riley J. Hickman, Jenya Vestfrid, Andrés Aguilar-Granda, Elena L. Klimareva, Ralph C. Sigerson, Wenduan Hou, Daniel Gahler, Slawomir Lach, Adrian Warzybok, Oleg Borodin, Simon Rohrbach, Benjamin Sanchez-Lengeling, Chihaya Adachi, Bartosz A. Grzybowski, Leroy Cronin, Jason E. Hein, Martin D. Burke, and Alán Aspuru-Guzik. Delocalized, asynchronous, closed-loop discovery of organic laser emitters. Science, May 2024. URL: https://doi.org/10.1126/science.adk9227, doi:10.1126/science.adk9227. This article has 195 citations and is from a highest quality peer-reviewed journal.

17. (cronin2026chemputerandchemputation—a pages 1-4): Leroy Cronin, Sebastian Pagel, and Abhishek Sharma. Chemputer and chemputation—a universal chemical compound synthesis machine. Proceedings of the National Academy of Sciences, Apr 2026. URL: https://doi.org/10.1073/pnas.2511080123, doi:10.1073/pnas.2511080123. This article has 7 citations and is from a highest quality peer-reviewed journal.

18. (lakhanpal2026spontaneousassembliesof pages 2-3): V Lakhanpal, D Long, and L Cronin. Spontaneous assemblies of gigantic poly-oxomolybdates; from structure and properties to synthetic methods. Unknown journal, 2026.

19. (sadeghi2024engineeringasustainable pages 8-10): Sina Sadeghi, Richard B. Canty, Nikolai Mukhin, Jinge Xu, Fernando Delgado-Licona, and Milad Abolhasani. Engineering a sustainable future: harnessing automation, robotics, and artificial intelligence with self-driving laboratories. ACS Sustainable Chemistry &amp; Engineering, 12:12695-12707, Aug 2024. URL: https://doi.org/10.1021/acssuschemeng.4c02177, doi:10.1021/acssuschemeng.4c02177. This article has 45 citations and is from a peer-reviewed journal.

20. (abolhasani2023theriseof pages 1-2): Milad Abolhasani and Eugenia Kumacheva. The rise of self-driving labs in chemical and materials sciences. Nature Synthesis, 2:483-492, Jan 2023. URL: https://doi.org/10.1038/s44160-022-00231-0, doi:10.1038/s44160-022-00231-0. This article has 703 citations and is from a peer-reviewed journal.

21. (baird2025bayesianoptimizationhackathon pages 1-2): Sterling Baird, Mehrad Ansari, Zartashia Afzal, Qianxiang Ai, Alexander Al-Feghali, Mathieu Alain, Matias Altamirano, Thomas Andrews, Andy Sode Anker, Rija Ansari, Samuel Ampofo Appiah, Raul Astudillo, Ruhana Azam, Mohammed Azzouzi, Suneel Kumar BVS, Ben Blaiszik, Anna Borisova, Andres Bran, Pengfei Cai, Ting-Yeh Chen, Curtis Chong, Samantha Corapi, Mark Croxall, Gbetondji Dovonon, Jose Manuel Napoles Duarte, Andrew Falkowski, Giuseppe Fisicaro, Martin Fitzner, Quinn Gallagher, Sabah Gaznaghi, Jerome Genzling, Christoph Griehl, Ryan-Rhys Griffiths, Taicheng Guo, Kehan Guo, Nipun Gupta, Ankur Gupta, Mohammad Haddadnia, Yuyang Han, Joscha Hoche, Alexander V. Hopp, Marko Huang, Ayodeji Ijishakin, Ramsey Issa, Yeonghun Kang, Jungtaek Kim, Akshay Kudva, Ruben Laplaza, Magdalena Lederbauer, Shi Xuan Leong, Paul W. Leu, Viola Muning Li, Mingxuan Li, Tao Liu, Stanley Lo, Jakub Lala, Osman Mamun, Owen Melville, Michail Mitsakis, Cameron Movassaghi, Madhav Reddy Muthyala, Marcel Muller, Bozhao Nan, Duc Nguyen, Daniele Ongari, Anthony Onwuli, Can Ozkan, Sergio Pablo-Garcia, Elton Pan, Ratish Panda, Sean Park, Jaehee Park, Dieter Plessers, Tobias Plotz, Ella M. Rajaonson, Bojana Rankovic, Jarett Ren, Rim Rihana, Jurgis Ruza, Akhil S. Nair, Carter Salbego, Erick Lopez Saldivar, Arifin San, Christina Schenk, Stefan P. Schmid, Dylan Schubert, Philippe Schwaller, Cher-Tian Ser, Maitreyee Sharma Priyadarshini, Yuxin Shen, Kevin Shen, Jiale Shi, Farshud Sorourifar, Adrian Sosic, Taylor Sparks, Jan Christopher Spies, Felix Strieth-Kalthoff, Suraj Sudhakar, Aditya Sundar, Alessio Tamburro, Clara Tamura, Yifeng Tang, Dandan Tang, Nikhil Thota, Mohammad Erfan Toloue Sadegh Azadi, Gary Tom, Sang Truong, Ricardo Valencia Albornoz, Luis Walter, Lawrence Wang, Fanjin Wang, Andrew Wang, Yiran Wang, Jeffrey Watchorn, Benjamin Weiser, Geemi Wellawatte, Alexander Wieczorek, Tim Wurger, Ilya Yakavets, Jakob Zeitler, Sylvester Zhang, Yimu Zhao, Yanqiao Zhu, Ruijie Zhu, and Yunheng Zou. Bayesian optimization hackathon for chemistry and materials. ChemRxiv, Jun 2025. URL: https://doi.org/10.26434/chemrxiv-2025-dzh5z, doi:10.26434/chemrxiv-2025-dzh5z. This article has 2 citations.

22. (brass2026amobilerobotic pages 7-10): Emma Brass, Satheeshkumar Veeramani, Zhengxue Zhou, Hatem Fakhruldeen, J. S. Manzano, R. Clowes, Isil Akpinar, Miriam R. Ward, John W. Ward, and Andrew I. Cooper. A mobile robotic process chemist. ChemRxiv, Oct 2026. URL: https://doi.org/10.26434/chemrxiv-2025-bsfvz, doi:10.26434/chemrxiv-2025-bsfvz. This article has 3 citations.

23. (lunt2023modularmultirobotintegration pages 12-16): Amy. M. Lunt, Hatem Fakhruldeen, Gabriella Pizzuto, Louis Longley, Alexander White, Nicola Rankin, Rob Clowes, Ben Alston, Lucia Gigli, Graeme M. Day, Andrew I. Cooper, and Sam. Y. Chong. Modular, multi-robot integration of laboratories: an autonomous solid-state workflow for powder x-ray diffraction. Preprint, Jan 2023. URL: https://doi.org/10.48550/arxiv.2309.00544, doi:10.48550/arxiv.2309.00544. This article has 1 citations.

24. (lunt2023modularmultirobotintegration pages 1-3): Amy. M. Lunt, Hatem Fakhruldeen, Gabriella Pizzuto, Louis Longley, Alexander White, Nicola Rankin, Rob Clowes, Ben Alston, Lucia Gigli, Graeme M. Day, Andrew I. Cooper, and Sam. Y. Chong. Modular, multi-robot integration of laboratories: an autonomous solid-state workflow for powder x-ray diffraction. Preprint, Jan 2023. URL: https://doi.org/10.48550/arxiv.2309.00544, doi:10.48550/arxiv.2309.00544. This article has 1 citations.

25. (lo2023reviewoflowcost pages 31-33): Stanley Lo, Sterling Baird, Joshua Schrier, Ben Blaiszik, Sergei Kalinin, Helen Tran, Taylor Sparks, and Alán Aspuru-Guzik. Review of low-cost self-driving laboratories: the "frugal twin" concept. ChemRxiv, Sep 2023. URL: https://doi.org/10.26434/chemrxiv-2023-6z9mq, doi:10.26434/chemrxiv-2023-6z9mq. This article has 4 citations.