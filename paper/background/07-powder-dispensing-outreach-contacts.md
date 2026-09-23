# Powder-Dispensing Outreach Contacts

> **Scope.** Named individuals, organizations, communities, and funding
> programs the BYU Vertical Cloud Lab can realistically reach out to for
> collaboration, advice, or technical support on **accurate, automated
> powder dispensing** for chemistry / materials-science / metal-AM
> applications.
>
> Resolves issue: *"Determine individuals and organizations we could reach
> out to for help with powder dispensing"*. Powder-dispensing counterpart
> of the generative-CAD outreach note `06-generative-cad-outreach-contacts.md`
> (PR #43); same per-entry format (one `### Name` H3 anchor per contact,
> closing `(source: <URL>)` tag, no fabricated emails).

## Provenance

- **Runner** — [`edison_run_powder_dispensing_outreach_contacts.py`](edison_run_powder_dispensing_outreach_contacts.py).
  Single Edison Scientific `LITERATURE_HIGH` task with the full prompt
  embedded verbatim. Re-run with
  `pip install edison_client && export EDISON_API_KEY=... && python paper/background/edison_run_powder_dispensing_outreach_contacts.py`
  (the runner also accepts `EDISON_PLATFORM_API_KEY`; never commit either
  value).
- **Raw artifacts** —
  [`edison_artifacts/powder_dispensing_outreach_contacts.task.json`](edison_artifacts/powder_dispensing_outreach_contacts.task.json)
  (full `TaskResponse.model_dump()`),
  [`.answer.md`](edison_artifacts/powder_dispensing_outreach_contacts.answer.md)
  (~60 k chars), and
  [`.references.md`](edison_artifacts/powder_dispensing_outreach_contacts.references.md).
  `status=success`.
- **Seed sources** explicitly listed in the prompt: the
  [accelerated-discovery.org thread on accurate powder dispensing](https://accelerated-discovery.org/t/accurate-powder-dispensing-for-chemistry-and-materials-science-applications/177);
  Cooper-group PowderBot ([arXiv 2309.00544](https://arxiv.org/abs/2309.00544));
  Ceder-group A-Lab ([Nature 624](https://www.nature.com/articles/s41586-023-06734-w));
  Vecchio-group HT-READ at UCSD; OpenTrickler
  ([github.com/eamars/OpenTrickler](https://github.com/eamars/OpenTrickler));
  Autotrickler v4 ([autotrickler.com](https://autotrickler.com/pages/autotrickler-v4));
  CMAC ([cmac.ac.uk](https://www.cmac.ac.uk/)); INSSTEK CVM doser; and
  commercial vendors including Mettler-Toledo, Chemspeed, Unchained Labs,
  Hamilton, Thermo Fisher, Trajan, MTI Corporation, Coperion K-Tron,
  Schenck, Gericke, Brabender, Movacolor, Sartorius, Freeman, A&D,
  CE Products, Emerald Cloud Lab.

## How to use this list

1. Each contact has its own H3 anchor (e.g. `#sterling-g-baird`,
   `#mti-corporation`) so links from issues / Slack / drafts resolve to a
   single named person or organization.
2. Each entry ends with `(source: <full URL>)` pointing at the public
   page where the listed channel can be verified before sending.
3. Where no public direct email was located, the entry says so explicitly
   and gives the best available lab / org / social fallback — no email
   addresses were fabricated, per the prompt's guardrail.
4. Entries flagged **[forum-only]** were carried over from the
   accelerated-discovery thread (post numbers in brackets, e.g. `[AD #4]`,
   reference [the original thread](https://accelerated-discovery.org/t/accurate-powder-dispensing-for-chemistry-and-materials-science-applications/177))
   when the Edison query could not independently confirm a public channel
   beyond the forum itself.
5. This is a living document — add entries with their public source URL as
   more candidates surface.

## Quick-reference index

| Category | Entries |
|---|---|
| [Forum / community participants](#1-forum--community-participants) | [Sterling G. Baird](#sterling-g-baird), [Andrew (`@shijing`) Lee](#andrew-shijing-lee), [Benji Maruyama](#benji-maruyama), [Matthew Reish](#matthew-reish), [Taylor D. Sparks](#taylor-d-sparks), [`@loppe35`](#loppe35), [`@muon`](#muon), [`@kthchow`](#kthchow), [Filippos Tourlomousis](#filippos-tourlomousis-forum) |
| [Academic PIs on automated powder dosing](#2-academic-pis-and-engineers-working-on-automated-powder-dosing) | [Gerbrand Ceder](#gerbrand-ceder), [Yan Zeng](#yan-zeng), [Andrew I. Cooper](#andrew-i-cooper), [Samantha Y. Chong](#samantha-y-chong), [Amy M. Lunt](#amy-m-lunt), [Filippos Tourlomousis](#filippos-tourlomousis) |
| [Academic AM / DED / L-PBF groups](#3-academic-am--ded--l-pbf-groups-with-powder-handling-experience) | [Kenneth S. Vecchio](#kenneth-s-vecchio), [Marie-Agathe Charpagne](#marie-agathe-charpagne), [Tim Simpson](#tim-simpson), [Allison M. Beese](#allison-m-beese), [Tresa M. Pollock](#tresa-m-pollock) |
| [Commercial powder-dosing vendors](#4-commercial-powder-dosing--feeding-vendors) | [Mettler-Toledo (Quantos / CHRONECT)](#mettler-toledo-quantos--chronect-product-lines), [Chemspeed Technologies](#chemspeed-technologies-swing--flex--overhead-gravimetric-dispenser), [MTI Corporation](#mti-corporation), [Freeman Technology / Micromeritics](#freeman-technology-micromeritics--ft4-powder-rheometer), [Sartorius](#sartorius), [Coperion K-Tron](#coperion-k-tron), [A&D Company](#ad-company-fx-120i--hr-100a-scales), [Unchained Labs](#unchained-labs), [Hamilton Company](#hamilton-company), [Thermo Fisher Scientific](#thermo-fisher-scientific), [Trajan Scientific and Medical](#trajan-scientific-and-medical), [Schenck Process](#schenck-process), [Gericke](#gericke), [Brabender Technologie](#brabender-technologie), [Movacolor](#movacolor), [Emerald Cloud Lab](#emerald-cloud-lab), [INSSTEK](#insstek-cvm-clogged-vibration-mechanism-doser), [CE Products](#ce-products) |
| [Open-source / DIY maintainers & communities](#5-open-source--diy-powder-dosing-maintainers-and-communities) | [Ran Tao (`@eamars`) / OpenTrickler](#ran-tao-github-eamars), [Adam McDonald / Area 419 / Autotrickler](#adam-mcdonald--area-419), [Matt Reish solid doser](#matt-reish-solid-doser-platform), [Accelerated-Discovery forum](#accelerated-discoveryorg-forum), [Acceleration Consortium SDL community channels](#self-driving-lab-community-channels) |
| [Adjacent SDL / agentic-hardware groups](#6-adjacent-self-driving-lab--agentic-hardware-groups) | [Alán Aspuru-Guzik](#alan-aspuru-guzik), [Lee Cronin](#lee-cronin), [Milad Abolhasani](#milad-abolhasani), [Jason E. Hein](#jason-e-hein), [Joshua Schrier](#joshua-schrier), [Keith A. Brown](#keith-a-brown), [Ben Blaiszik](#ben-blaiszik), [Ian T. Foster](#ian-t-foster) |
| [Conferences / workshops / funding](#7-conferences-workshops-and-funding--program-officers) | [TMS Annual Meeting](#tms-annual-meeting), [MRS Spring / Fall](#mrs-spring--fall-meetings), [Acceleration Consortium / Accelerate](#acceleration-consortium-meetings--accelerate-conference), [NSF DMREF](#nsf-dmref-designing-materials-to-revolutionize-and-engineer-our-future), [NSF Future Manufacturing](#nsf-future-manufacturing), [America Makes](#america-makes), [NASA Space Grant](#nasa-space-grant-program) |

---

## 1. Forum / community participants

### Sterling G. Baird

**Affiliation / role.** Director of Training and Programs, Acceleration
Consortium, University of Toronto; alumnus of Brigham Young University
(BS Applied Physics, MS Mechanical Engineering) and PhD Materials Science
& Engineering, University of Utah. Forum handle: `@sgbaird`.

**Why relevant.** Central organizer in the self-driving-lab community and
the participant who opened the accelerated-discovery powder-dispensing
thread \[AD #1, #6, #8, #10, #11, #15, #20]. Co-author of the "Frugal
Twin" review on low-cost SDLs and lead on Honegumi (Bayesian-optimization
front-end); has been demoing an Autotrickler v4 in the lab and tracking
the Mettler-Toledo and Chemspeed approaches. Ideal first point of contact
for open-science introductions and frugal/DIY automation strategy.

**Contact.** `sterling.baird@utoronto.ca` (corresponding-author block of
the Frugal-Twin review); GitHub [`@sgbaird`](https://github.com/sgbaird).

(source: <https://doi.org/10.1039/d3dd00223c>)

### Andrew (`@shijing`) Lee

**Affiliation / role.** Forum participant `@shijing` on
accelerated-discovery.org; graduate-student work on 3D-printed
calibrated-volume spatulas inspired by Cook et al. (*Nature Protocols*,
2020). **Note:** Edison's literature search returned a different "Shijing
Sun" (Toyota Research Institute) — that may or may not be the same
person; resolve before reaching out. [forum-only]

**Why relevant.** Direct hands-on experience with low-cost solid
dispensing into 8 × 30 mm vials in a glovebox, including the
static-charge / lighter-powder failure modes that any sub-\$10k design
must handle \[AD #2, #3].

**Contact.** No public direct email located; reachable via the
[accelerated-discovery thread](https://accelerated-discovery.org/t/accurate-powder-dispensing-for-chemistry-and-materials-science-applications/177).

(source: <https://accelerated-discovery.org/u/shijing>)

### Benji Maruyama

**Affiliation / role.** Air Force Research Laboratory, Materials &
Manufacturing Directorate, Wright-Patterson AFB, OH. Forum handle:
`@benjimaruyama`.

**Why relevant.** Co-author on the Frugal-Twin low-cost SDL review and
active in the accelerated-discovery community; explicitly asked for
commercial-vendor recommendations on a ceramics robot project that needs
powder dispensing \[AD #19]. DoD / AM-discovery community introductions.

**Contact.** No public direct email located in the cited literature;
reachable via AFRL public directory and the
[accelerated-discovery thread](https://accelerated-discovery.org/u/benjimaruyama).

(source: <https://doi.org/10.1039/d3dd00223c>)

### Matthew Reish

**Affiliation / role.** Forum participant `@mreish` on
accelerated-discovery.org; designer of a "solid doser" platform
demoed in a [YouTube video](https://www.youtube.com/watch?v=7yBmL1Xw5Xg)
\[AD #15].

**Why relevant.** Has a working low-cost powder-dispensing platform
that Sterling Baird specifically flagged as "compelling and relatively
low-cost". Closest direct peer for the sub-\$10k design constraint.

**Contact.** No public contact channel located beyond the forum handle;
reachable via accelerated-discovery direct message.

(source: <https://accelerated-discovery.org/t/accurate-powder-dispensing-for-chemistry-and-materials-science-applications/177>)

### Taylor D. Sparks

**Affiliation / role.** Professor, Department of Materials Science and
Engineering, University of Utah; Associate Editor, *Computational
Materials Science*.

**Why relevant.** Co-PI with Baird on the Frugal-Twin review and the
Honegumi tool; NSF CAREER awardee with active TMS / MRS involvement.
Practical contact for advice on low-cost academic-scale automation and
materials-discovery framing.

**Contact.** `sparks@eng.utah.edu` (corresponding-author block).

(source: <https://doi.org/10.1039/d3dd00223c>)

### `@loppe35`

**Affiliation / role.** Forum participant on accelerated-discovery.org;
builder of a low-budget auger-based salt dispenser using a 20 g
strain-gauge load cell harvested from a jewelry scale \[AD #4]. [forum-only]

**Why relevant.** Direct hands-on experience with the auger-vs-vertical-leak
tradeoff and hopper-flow-aid design that the powder-doser project also
has to solve.

**Contact.** No public contact channel located beyond the forum profile.

(source: <https://accelerated-discovery.org/u/loppe35>)

### `@muon`

**Affiliation / role.** Forum participant on accelerated-discovery.org
\[AD #5, #7, #14]. [forum-only]

**Why relevant.** Articulated the *recovery* problem (picking powder back
up after ball-milling / acoustic mixing), which is upstream of any
multi-dispense workflow and which Cooper-group PowderBot and Ceder
A-Lab only partly solve; directly relevant to the powder-doser scope.

**Contact.** No public contact channel located beyond the forum profile.

(source: <https://accelerated-discovery.org/u/muon>)

### `@kthchow`

**Affiliation / role.** Forum participant on accelerated-discovery.org;
referenced glass/plastic chemistry-grade augers and shared a build photo
\[AD #9, #12, #16]. [forum-only]

**Why relevant.** Practical know-how on stepper-driven chemistry-auger
hardware and microbalance selection (FX-120i vs. cheaper options) that
applies directly to the powder-doser prototype.

**Contact.** No public contact channel located beyond the forum profile.

(source: <https://accelerated-discovery.org/u/kthchow>)

### Filippos Tourlomousis [forum]

**Affiliation / role.** Researcher posting on LinkedIn and adjacent forums
on a ~\$100 automated powder dispenser for biopolymer formulation
\[AD #17].

**Why relevant.** Existing demo at exactly the sub-\$10k cost target the
powder-doser project is aiming for; lessons should transfer despite the
biopolymer-vs-metal-AM material change. See also
[§2 entry below](#filippos-tourlomousis) for the literature-side context.

**Contact.** Reachable via the [LinkedIn post](https://www.linkedin.com/feed/update/urn:li:activity:7310752420093906945)
referenced in [AD #17].

(source: <https://www.linkedin.com/feed/update/urn:li:activity:7310752420093906945>)

---

## 2. Academic PIs and engineers working on automated powder dosing

### Gerbrand Ceder

**Affiliation / role.** Professor, Department of Materials Science and
Engineering, UC Berkeley; Materials Sciences Division, Lawrence Berkeley
National Laboratory.

**Why relevant.** Co-PI of A-Lab — one of the most prominent autonomous
solid-state powder synthesis platforms. A-Lab automates powder dosing
using a Mettler-Toledo Quantos dispenser-balance, a central Mitsubishi
robot arm, and UR5e arms, processing ~3,500 powder samples via
solid-state synthesis. The most directly comparable academic system to
what the powder-doser project needs.

**Contact.** `gceder@berkeley.edu` (corresponding author).

(source: <https://doi.org/10.1038/s41586-023-06734-w>)

### Yan Zeng

**Affiliation / role.** Department of Chemistry and Biochemistry, Florida
State University; formerly Lawrence Berkeley National Laboratory.

**Why relevant.** Corresponding author on both the original A-Lab *Nature*
paper and the glovebox A-Lab extension for air-sensitive synthesis.
Directly relevant for robotic powder pipelines, precursor dispensing in
inert environments, and the practical integration challenges that show up
once you move beyond a single doser.

**Contact.** `zeng@chem.fsu.edu` (corresponding author).

(source: <https://doi.org/10.1038/s41586-023-06734-w>)

### Andrew I. Cooper

**Affiliation / role.** Professor, Department of Chemistry and Materials
Innovation Factory, University of Liverpool; Leverhulme Research Centre
for Functional Materials Design.

**Why relevant.** Co-corresponding author on Liverpool's modular
multi-robot solid-state workflow (Chemspeed FLEX LIQUIDOSE + KUKA mobile
robot + ABB YuMi) and on a bespoke solid-dosing device for robotic
process chemistry dispensing up to 20 g of powder — i.e. exactly the
multi-reservoir, robot-integrated dosing pattern the powder-doser
project is targeting.

**Contact.** `aicooper@liverpool.ac.uk` (corresponding author).

(source: <https://doi.org/10.1039/d3sc06206f>)

### Samantha Y. Chong

**Affiliation / role.** Department of Chemistry and Materials Innovation
Factory, University of Liverpool.

**Why relevant.** Co-corresponding author on the Liverpool solid-state
powder workflow; the right contact for hands-on orchestration of the
Chemspeed + robot + grinding/shaker PXRD-prep pipeline and the
ARChemist software stack.

**Contact.** `schong@liverpool.ac.uk` (corresponding author).

(source: <https://doi.org/10.1039/d3sc06206f>)

### Amy M. Lunt

**Affiliation / role.** Researcher, University of Liverpool; first
author on the modular multi-robot PXRD workflow.

**Why relevant.** First author on the Liverpool automated solid-state
powder workflow; highly relevant for the practical specifics of robotic
powder transfer, grinding-station design, Kapton-based mounting, and
multi-robot coordination.

**Contact.** No public direct email found; reachable via corresponding
authors Cooper or Chong at Liverpool.

(source: <https://doi.org/10.1039/d3sc06206f>)

### Filippos Tourlomousis

**Affiliation / role.** Researcher associated with a low-cost automated
powder dispenser for biopolymers; acknowledged in open-source rheometer
work.

**Why relevant.** Credited with developing a ~\$100 automated powder
dispenser for biopolymers — directly on the price/architecture trajectory
of the powder-doser project. Bridges the pharma/biopolymer and
materials-science powder-handling communities. See also the
[forum entry above](#filippos-tourlomousis-forum).

**Contact.** No public direct email found in the cited literature;
reachable via the open-source rheometer acknowledgments section.

(source: <https://doi.org/10.1038/s41598-024-76494-8>)

---

## 3. Academic AM / DED / L-PBF groups with powder-handling experience

### Kenneth S. Vecchio

**Affiliation / role.** Professor, University of California San Diego.

**Why relevant.** Built HT-READ (High-Throughput Rapid Experimental Alloy
Development), which *explicitly identifies manual powder weighing as the
bottleneck* and solves it with a ChemSpeed dosing system (up to 24 powder
sources, 0.01 g accuracy) plus a custom 16-hopper Alloy Development
Feeder (ADF) integrated with a Formalloy L221 DED unit — ~50 alloy
compositions per 24 h. The closest existing system to the powder-doser
project's multi-powder metal-AM goal.

**Contact.** `kvecchio@eng.ucsd.edu` (corresponding author).

(source: <https://doi.org/10.1016/j.actamat.2021.117352>)

### Marie-Agathe Charpagne

**Affiliation / role.** University of Illinois Urbana-Champaign.

**Why relevant.** Co-author on 2025 work using AM functionally graded
materials and high-throughput plasticity quantification — graded-alloy
discovery is the workflow that benefits most from precise multi-powder
blending across builds.

**Contact.** No public direct email found in cited context; reachable via
the UIUC Materials Science department page or corresponding authors
(`cmbean2@illinois.edu` / `jcstinv@illinois.edu`).

(source: <https://doi.org/10.1016/j.matdes.2025.114115>)

### Tim Simpson

**Affiliation / role.** Professor, Penn State University; co-director,
CIMP-3D (Center for Innovative Materials Processing through Direct
Digital Deposition).

**Why relevant.** Major figure in AM process/materials integration at one
of the leading university AM centers; strong connector for powder-feed
and multi-material AM infrastructure advice.

**Contact.** No public direct email found in cited context; reachable
via the CIMP-3D contact page and Penn State faculty directory.

(source: <https://www.cimp-3d.org/>)

### Allison M. Beese

**Affiliation / role.** Professor, Mechanical Engineering, Penn State
University.

**Why relevant.** Runs a leading metal-AM mechanics/materials group with
extensive experience in L-PBF feedstock and process–property
relationships relevant to powder-handling integration.

**Contact.** No public direct email found in cited context; reachable via
Penn State faculty page.

(source: <https://www.me.psu.edu/>)

### Tresa M. Pollock

**Affiliation / role.** Professor, Materials Department, University of
California Santa Barbara.

**Why relevant.** Leading authority on high-temperature alloys and metal
AM; useful for refractory / Ni / Ti alloy feedstock requirements and
integration into AM discovery workflows.

**Contact.** No public direct email found in cited context; reachable via
UCSB Materials Department faculty page.

(source: <https://www.materials.ucsb.edu/>)

---

## 4. Commercial powder-dosing / feeding vendors

### Mettler-Toledo (Quantos / CHRONECT product lines)

**Why relevant.** Quantos is the only dispenser explicitly named in the
A-Lab documentation for autonomous inorganic powder synthesis — the
single most directly relevant commercial contact for gravimetric powder
dosing in materials discovery. ±0.1 mg resolution, validated on pharma
powders.

**Contact.** Quote / sales-inquiry form on the Quantos product page;
ask for application-engineering contact for academic SDL integrations.

(source: <https://www.mt.com/us/en/home/products/Laboratory_Weighing_Solutions/Reagent-Dosing/quantos.html>)

### Chemspeed Technologies (SWING / FLEX / overhead gravimetric dispenser)

**Why relevant.** Chemspeed platforms appear in both the Liverpool
solid-state workflow (FLEX LIQUIDOSE) and the UCSD HT-READ system —
proven choice for multi-reservoir automated powder and liquid handling
in materials discovery.

**Contact.** Sales-inquiry form; ask for the academic / scientific-
applications team.

(source: <https://www.chemspeed.com/contact/>)

### MTI Corporation

**Why relevant.** Called out explicitly in the issue's agent instructions.
Many university AM labs buy feeders, micro-augers, powder-handling
components, furnaces, and labware from MTI for custom rigs under tight
budgets — their catalog includes parts directly applicable to a
sub-\$10k powder-handling system.

**Contact.** `sales@mtixtl.com`; contact page at
<https://www.mtixtl.com/contactus.aspx>.

(source: <https://www.mtixtl.com/contactus.aspx>)

### Freeman Technology (Micromeritics — FT4 Powder Rheometer)

**Why relevant.** Difficult AM powders most often fail because of
flowability rather than controller precision. The FT4 characterizes
flow, shear, and bulk properties needed to *select and validate* a
dispenser design for metal-AM feedstock.

**Contact.** Contact form on the Freeman / Micromeritics site.

(source: <https://www.micromeritics.com/contact-us/>)

### Sartorius

**Why relevant.** Sartorius balances and automated pipettors (rLine)
already appear in the A-Lab hardware stack; relevant for balance,
pipetting, and automation integration into a custom powder-dispensing
rig.

**Contact.** Contact form.

(source: <https://www.sartorius.com/en/company/contact>)

### Coperion K-Tron

**Why relevant.** One of the strongest industrial contacts for precision
gravimetric feeders, loss-in-weight systems, and difficult-powder
handling; their micro-feeder technology may translate into custom
lab-scale designs.

**Contact.** Contact page.

(source: <https://www.coperion.com/en/contact>)

### A&D Company (FX-120i / HR-100A scales)

**Why relevant.** A&D microbalances are common in DIY precision-dosing
communities (reloading, pharma) and anchor low-cost custom dispenser
builds — the FX-120i in particular is the reference scale for
OpenTrickler and Autotrickler builds, and was the scale recommended
on the accelerated-discovery thread \[AD #6, #9, #10].

**Contact.** Inquiry page.

(source: <https://www.aandd.jp/support/inquiry.html>)

### Unchained Labs

**Why relevant.** One of the four vendors Benji Maruyama specifically
listed when soliciting commercial-powder-dispensing advice for the
AFRL ceramics robot \[AD #19] — worth a comparison quote even though
their platform is primarily aimed at pharma HTE.

**Contact.** Sales / contact form on the corporate site.

(source: <https://www.unchainedlabs.com/contact/>)

### Hamilton Company

**Why relevant.** Listed by Maruyama \[AD #19]; pipetting / liquid-handling
heritage with a powder-dispensing module that some materials labs have
adapted. Worth a quote for the auxiliary liquid-dispense pieces of a
combined SDL.

**Contact.** Contact-us form.

(source: <https://www.hamiltoncompany.com/contact-us>)

### Thermo Fisher Scientific

**Why relevant.** Listed by Maruyama \[AD #19]; broad lab-automation and
balance portfolio that intersects powder workflows.

**Contact.** Contact-us page.

(source: <https://www.thermofisher.com/us/en/home/global/contact-us.html>)

### Trajan Scientific and Medical

**Why relevant.** Listed by Maruyama \[AD #19]; partners with
Mettler-Toledo on autosampling and is positioning into automated sample
preparation including powder.

**Contact.** Contact page.

(source: <https://www.trajanscimed.com/pages/contact-us>)

### Schenck Process

**Why relevant.** Industrial loss-in-weight and gravimetric feeders;
useful comparison point on the heavier end for understanding what scales
*down* into a lab module.

**Contact.** Regional contact form.

(source: <https://www.schenckprocess.com/contact>)

### Gericke

**Why relevant.** Industrial powder-feeding specialist (gravimetric and
volumetric loss-in-weight feeders) regularly cited in the AM
powder-handling literature.

**Contact.** Contact form.

(source: <https://www.gerickegroup.com/contact>)

### Brabender Technologie

**Why relevant.** Loss-in-weight feeder vendor with a strong installed
base in materials labs; relevant comparison for any custom auger
design.

**Contact.** Contact form.

(source: <https://www.brabender-technologie.com/en/contact/>)

### Movacolor

**Why relevant.** Gravimetric dosing units; comparison point on the
smaller-scale industrial side, especially for color-/additive-style
multi-channel dispense.

**Contact.** Contact form.

(source: <https://www.movacolor.com/contact/>)

### Emerald Cloud Lab

**Why relevant.** Cloud-lab provider with an analytical-balance + powder
workflow (the "0.1 mg / 220 g analytic balance" Sterling flagged on the
thread \[AD #11]); worth a conversation about how their internal powder
modules are designed and a potential validation partner once a prototype
exists.

**Contact.** Contact / sales form on the instrumentation site.

(source: <https://www.emeraldcloudlab.com/instrumentation/>)

### INSSTEK (CVM clogged-vibration-mechanism doser)

**Why relevant.** Vendor of the clogged-vibration-mechanism (CVM) powder
doser used on commercial DED machines; one of the few off-the-shelf
multi-powder dispensers specifically engineered for metal-AM feedstock
\[AD #16].

**Contact.** Inquiry page (Korea HQ + global distributors).

(source: <https://www.insstek.com/technology/cvm_powder>)

### CE Products

**Why relevant.** US distributor for the A&D FX-120i + AutoTrickler
ecosystem; useful for sourcing the scale + serial-comms hardware Sterling
described setting up via MicroPython on a Pico W \[AD #6, #10].

**Contact.** Contact page on the storefront.

(source: <https://ceproducts.shop/pages/contact>)

---

## 5. Open-source / DIY powder-dosing maintainers and communities

### Ran Tao (GitHub: `@eamars`)

**Affiliation / role.** Maintainer of the OpenTrickler project on GitHub.

**Why relevant.** OpenTrickler is one of the clearest open-source examples
of milligram-class automated powder dispensing hardware + software, with
a full BOM, firmware, and mechanical design files that a small lab can
study or adapt for metal-AM blending.

**Contact.** GitHub [`@eamars`](https://github.com/eamars) (issues /
discussions on the repo).

(source: <https://github.com/eamars/OpenTrickler>)

### Adam McDonald / Area 419

**Affiliation / role.** Founder, Area 419; creator of the AutoTrickler
system (now v4).

**Why relevant.** AutoTrickler is a mature, field-proven consumer
precision powder dispenser with strong practical know-how on
vibration/trickling and closed-loop weighing to ±0.02 grain (~1.3 mg).
Engineering lessons are directly transferable to metal-AM powder
handling, and Sterling already has a v4 set up in the lab \[AD #6].

**Contact.** Contact form on `autotrickler.com`.

(source: <https://autotrickler.com/pages/contact-us>)

### Matt Reish solid-doser platform

**Why relevant.** Demonstrated low-cost solid-doser shown in
[this YouTube clip](https://www.youtube.com/watch?v=7yBmL1Xw5Xg) and
flagged by Sterling Baird as the closest design-pattern reference for a
low-cost academic build \[AD #15]. See also
[Matthew Reish](#matthew-reish) in §1.

**Contact.** Video author channel; reachable via
accelerated-discovery DM.

(source: <https://www.youtube.com/watch?v=7yBmL1Xw5Xg>)

### Accelerated-Discovery.org forum

**Why relevant.** Hosts the canonical thread for this issue and is the
right venue for a "we built X, here's what we learned" status update
once the prototype is in hand. Useful for broad community outreach,
async technical discussion, and finding adjacent builders.

**Contact.** Thread + per-user direct messaging.

(source: <https://accelerated-discovery.org/t/accurate-powder-dispensing-for-chemistry-and-materials-science-applications/177>)

### Self-Driving-Lab community channels

**Why relevant.** The Acceleration Consortium maintains community
Slack/Discord channels and the accelerated-discovery.org forum where SDL
hardware builders congregate. The 2024 Accelerate conference's
"Democratizing Self-Driving Labs" workshop specifically featured
user-developed automation infrastructure.

**Contact.** Community links on the AC site.

(source: <https://accelerationconsortium.ai/>)

---

## 6. Adjacent self-driving-lab / agentic-hardware groups

### Alán Aspuru-Guzik

**Affiliation / role.** Professor of Chemistry and Computer Science,
University of Toronto; Director, Acceleration Consortium; Canada 150
Research Chair.

**Why relevant.** Central connector in the SDL ecosystem with direct
interest in democratized and distributed lab automation; the
Acceleration Consortium he directs is exactly the network for
introductions and framing a powder-dosing collaboration ask.

**Contact.** `alan@aspuru.com` (author contact block).

(source: <https://doi.org/10.1039/d3dd00223c>)

### Lee Cronin

**Affiliation / role.** Regius Professor of Chemistry, School of
Chemistry, University of Glasgow; founder and CEO of Chemify.

**Why relevant.** Major leader in digitized chemistry and modular
automation via the Chemputer platform; group has built bespoke
solid-dosing devices. Lessons on architecture, orchestration, and
open hardware transfer cleanly even though the platforms aren't
metal-powder focused.

**Contact.** `Lee.Cronin@glasgow.ac.uk`; lab site `www.croninlab.com`.

(source: <https://doi.org/10.1073/pnas.2511080123>)

### Milad Abolhasani

**Affiliation / role.** Professor, Department of Chemical and
Biomolecular Engineering, NC State University.

**Why relevant.** Strong SDL builder with practical experience turning
bottlenecks into modular automation; closed-loop fluidic-lab and
nanocrystal-synthesis work informs the modular subsystem design pattern
the powder-doser project also needs.

**Contact.** `abolhasani@ncsu.edu` (corresponding author).

(source: <https://doi.org/10.1021/acssuschemeng.4c02177>)

### Jason E. Hein

**Affiliation / role.** Professor, Department of Chemistry, University of
British Columbia.

**Why relevant.** Co-corresponding author on the 2024 *Science*
delocalized-asynchronous-discovery paper; useful for orchestration and
practical automated-chemistry integration discussions.

**Contact.** `jhein@chem.ubc.ca` (corresponding author).

(source: <https://doi.org/10.1126/science.adk9227>)

### Joshua Schrier

**Affiliation / role.** Professor, Department of Chemistry and
Biochemistry, Fordham University.

**Why relevant.** Co-author on the Frugal-Twin low-cost SDL review;
relevant for community advice on practical autonomous experimentation
and benchmarking strategies appropriate for smaller academic settings.

**Contact.** No public direct email found in cited context; reachable
via the Fordham Chemistry faculty directory.

(source: <https://www.fordham.edu/chemistry/>)

### Keith A. Brown

**Affiliation / role.** Professor, Boston University.

**Why relevant.** Co-author on the autonomous-discovery community
perspective paper; useful for hardware-centric SDL design and Bayesian
self-driving mechanics-lab know-how.

**Contact.** No public direct email found in cited context; reachable
via the BU faculty profile.

(source: <https://www.bu.edu/eng/profile/keith-a-brown/>)

### Ben Blaiszik

**Affiliation / role.** Argonne National Laboratory / University of
Chicago.

**Why relevant.** SDL infrastructure / data-and-automation contact;
relevant for connecting instrumentation, autonomy stacks, and
national-lab collaboration paths once a prototype exists.

**Contact.** No public direct email found in cited context; reachable
via Argonne staff directory.

(source: <https://www.anl.gov/profile/ben-blaiszik>)

### Ian T. Foster

**Affiliation / role.** Argonne National Laboratory / University of
Chicago.

**Why relevant.** Key figure in autonomous-experimentation infrastructure
and cloud/data systems; relevant once the powder-doser is tied into a
broader agentic workflow.

**Contact.** No public direct email found in cited context; reachable
via Argonne staff directory.

(source: <https://www.anl.gov/profile/ian-foster>)

---

## 7. Conferences, workshops, and funding / program officers

### TMS Annual Meeting

**Why relevant.** One of the most on-topic venues for metal-powder
handling, DED/L-PBF alloy development, and applied powder-feed systems
in AM; high-throughput-alloy-development and AM symposia are
regularly featured.

**Contact.** Conference contact page.

(source: <https://www.tms.org/AnnualMeeting>)

### MRS Spring / Fall meetings

**Why relevant.** MRS regularly hosts autonomous-materials-discovery and
AM symposia where a collaboration ask on powder dispensing is squarely
on-topic.

**Contact.** Meeting contact page.

(source: <https://www.mrs.org/meetings-events>)

### Acceleration Consortium meetings / Accelerate conference

**Why relevant.** Highly aligned with frugal/democratized SDL hardware;
the 2024 Accelerate conference featured a "Democratizing Self-Driving
Labs" workshop specifically showcasing user-developed automation
infrastructure.

**Contact.** General contact / event information.

(source: <https://accelerationconsortium.ai/>)

### NSF DMREF (Designing Materials to Revolutionize and Engineer our Future)

**Why relevant.** Natural funding home for powder-dispensing-enabled
alloy discovery tied to integrated computational–experimental loops;
program-officer contacts listed on the solicitation page.

**Contact.** Program page.

(source: <https://new.nsf.gov/funding/opportunities/dmref-designing-materials-revolutionize-engineer>)

### NSF Future Manufacturing

**Why relevant.** Strong fit for low-cost enabling hardware that closes a
manufacturing bottleneck and supports integrated autonomous
experimentation.

**Contact.** Program page.

(source: <https://new.nsf.gov/funding/opportunities/future-manufacturing>)

### America Makes

**Why relevant.** The National Additive Manufacturing Innovation
Institute; one of the most plausible external partners/funders for a
university-scale powder-handling + AM workflow integration concept.

**Contact.** Organization contact page.

(source: <https://www.americamakes.us/contact/>)

### NASA Space Grant program

**Why relevant.** The powder-doser project is at NASA-Space-Grant scale;
local Space Grant coordinators are the practical first contact for seed
funding and introductions tied to aerospace alloy discovery.

**Contact.** Program directory.

(source: <https://www.nasa.gov/learning-resources/national-space-grant-college-and-fellowship-projects/>)

---

## Suggested next actions

1. **Post a status update on AD #177** with a link to this file and the
   first prototype renders, asking the named participants (especially
   [`@mreish`](#matthew-reish), [`@loppe35`](#loppe35),
   [`@kthchow`](#kthchow), [`@muon`](#muon)) for feedback on the
   architecture and the recovery-after-milling problem.
2. **Email [Kenneth Vecchio](#kenneth-s-vecchio) and
   [Marie-Agathe Charpagne](#marie-agathe-charpagne)** to introduce the
   sub-\$10k multi-powder target and ask whether HT-READ's bottlenecks
   would benefit from a low-cost upstream module.
3. **Ask [MTI](#mti-corporation), [Chemspeed](#chemspeed-technologies-swing--flex--overhead-gravimetric-dispenser),
   and [Mettler-Toledo (Quantos)](#mettler-toledo-quantos--chronect-product-lines)
   for an engineering / scientific-applications contact** and a quote
   for the closest matching configuration; carbon-copy
   [Coperion K-Tron](#coperion-k-tron) and [Schenck Process](#schenck-process)
   on the industrial-scale comparison.
4. **Open a follow-up issue after the first replies** to log who
   responded, who passed, and what was learned about cost/accuracy
   tradeoffs for the powder classes the lab actually plans to handle.

## See also

- [`docs/outreach/powder-dispensing-contacts.md`](../../docs/outreach/powder-dispensing-contacts.md)
  — original repo-side index that now points back to this file.
- [`paper/background/06-generative-cad-outreach-contacts.md`](06-generative-cad-outreach-contacts.md)
  (PR #43) — sibling outreach note for the generative-CAD pillar,
  produced with the same Edison-backed workflow.
