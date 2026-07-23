# Powder-Properties Experts — Outreach Contacts

> **Scope.** Named individuals, organizations, software teams, standards
> bodies, and symposium organizers who could weigh in on the **powder
> properties** side of the powder-doser project — flow behavior,
> cohesion/friction measurement, DEM modeling and calibration, and metal-AM
> spreadability/packing — as distinct from the powder-*dispensing hardware*
> outreach list in
> [`07-powder-dispensing-outreach-contacts.md`](07-powder-dispensing-outreach-contacts.md).
>
> Requested in [PR #41](https://github.com/vertical-cloud-lab/powder-doser/pull/41)
> (sgbaird: *"run a set of follow-up Edison queries as well as your own
> searching based on the TMS abstract by Will ... people who could weigh in
> on powder properties specifically"*). Anchored to Will's TMS 2027 abstract
> ([PR #78](https://github.com/vertical-cloud-lab/powder-doser/pull/78),
> `abstracts/tms-2027/calibration-optimization/abstract.md`): *"Auger-Based
> Powder Dosing as a Mechanistic Probe of Powder Flow Behavior: Multi-Task
> Bayesian Calibration and Physics-Based Property Inference"* — inference of
> effective cohesion and friction from dosing data via DEM with
> cohesive-frictional contact laws, validated against shear-cell and
> Hall-flow measurements, with links to downstream spreadability and packing
> uniformity.

## Provenance

- **Runner** —
  [`edison_run_powder_properties_experts.py`](edison_run_powder_properties_experts.py).
  Three Edison Scientific `LITERATURE_HIGH` tasks (the abstract is embedded
  verbatim in every prompt), split into dispatch / wait / fetch phases so
  the task IDs are committed before the wait. Re-run with
  `pip install edison_client && export EDISON_API_KEY=... && python
  paper/background/edison_run_powder_properties_experts.py all`.
- **Raw artifacts** (all `status=success`, fetched 2026-07-23):
  - [`edison_artifacts/powder_properties_rheology_experts.answer.md`](edison_artifacts/powder_properties_rheology_experts.answer.md)
    (+ `.task.json`, `.references.md`) — rheology / flowability /
    cohesion-friction measurement.
  - [`edison_artifacts/powder_properties_dem_calibration.answer.md`](edison_artifacts/powder_properties_dem_calibration.answer.md)
    (+ `.task.json`, `.references.md`) — DEM, Bayesian calibration, inverse
    property inference.
  - [`edison_artifacts/powder_properties_am_spreadability.answer.md`](edison_artifacts/powder_properties_am_spreadability.answer.md)
    (+ `.task.json`, `.references.md`) — AM spreadability, packing,
    powder-bed metrology, standards.
  - Task IDs:
    [`edison_artifacts/powder_properties_experts._task_ids.json`](edison_artifacts/powder_properties_experts._task_ids.json).
- **Own searching** — entries marked **[own-search]** were added from
  direct web searching in the same session (auger-dosing DEM calibration
  literature, GrainLearning, cohesive-powder dosing groups, the Wolfson
  Centre) and from the TMS 2027 symposium catalog compiled in PR #78
  (`abstracts/tms-2027/tms2027_symposia.yaml`, organizers parsed from the
  official CFA flyers).

## How to use this list

1. Each contact has its own H3 anchor (e.g. `#hongyang-cheng`,
   `#dietmar-schulze`) so links from issues / Slack / drafts resolve to a
   single named person or organization.
2. Each entry ends with `(source: <full URL>)` pointing at the public page
   where the listed channel or claim can be verified before sending. No
   email addresses were fabricated; emails shown were published in
   open-access papers and should be re-verified before use.
3. People who already have an entry in
   [`07-powder-dispensing-outreach-contacts.md`](07-powder-dispensing-outreach-contacts.md)
   (e.g. Freeman Technology as a vendor) are listed here only where the
   powder-*properties* angle adds something; the 07 entry remains the
   dispensing-hardware contact record.
4. This is a living document — re-running the Edison runner regenerates the
   artifacts, and new candidates can be appended with their source URL.

## Quick-reference index

| Category | Entries |
|---|---|
| [Powder-mechanics / particle-technology PIs](#1-powder-mechanics--particle-technology-pis) | [Mojtaba Ghadiri](#mojtaba-ghadiri), [Ali Hassanpour](#ali-hassanpour), [Colin Hare](#colin-hare), [Christine M. Hrenya](#christine-m-hrenya), [Fernando J. Muzzio](#fernando-j-muzzio), [Benjamin J. Glasser](#benjamin-j-glasser), [Jochen Schmidt](#jochen-schmidt), [Mike Bradley / Wolfson Centre](#mike-bradley--wolfson-centre-for-bulk-solids-handling-technology), [Marco Ramaioli](#marco-ramaioli) |
| [Metal-AM feedstock flow-property authors](#2-metal-am-feedstock-flow-property-authors) | [Lorenzo Marchetti](#lorenzo-marchetti), [Christopher Hulme-Smith](#christopher-hulme-smith), [Adriaan B. Spierings](#adriaan-b-spierings), [Jose Alberto Muñiz-Lerma](#jose-alberto-muniz-lerma), [Mathieu Brochu](#mathieu-brochu), [Laura Cordova](#laura-cordova), [Paul R. Mort / Michael P. Sealy](#paul-r-mort--michael-p-sealy) |
| [DEM & Bayesian-calibration methodology](#3-dem--bayesian-calibration-methodology) | [Hongyang Cheng / GrainLearning](#hongyang-cheng--grainlearning), [Vanessa Magnanimo](#vanessa-magnanimo), [Stefan Luding](#stefan-luding), [Klaus Thoeni](#klaus-thoeni), [Takayuki Shuku](#takayuki-shuku), [Bilal El Kassem](#bilal-el-kassem), [Carl Wassgren](#carl-wassgren), [Jin Ooi](#jin-ooi), [Thorsten Pöschel](#thorsten-poschel), [Paul Cleary](#paul-cleary), [Marc Fransen](#marc-fransen), [Krishna Kumar](#krishna-kumar), [WaiChing Sun](#waiching-sun), [Fabio Ramos](#fabio-ramos), [Daniel N. Wilke](#daniel-n-wilke) |
| [DEM software teams](#4-dem-software-teams) | [Thomas Weinhart / MercuryDPM](#thomas-weinhart--mercurydpm), [Christoph Kloss / LIGGGHTS / Aspherix](#christoph-kloss--liggghts--aspherix), [Bruno Chareyre / YADE](#bruno-chareyre--yade), [Bruno Blais / Lethe](#bruno-blais--lethe), [MFiX-DEM team (NETL)](#mfix-dem-team-netl), [Altair EDEM](#altair-edem) |
| [Flow-characterization instrument makers](#5-flow-characterization-instrument-makers) | [Tim Freeman](#tim-freeman), [Geoffroy Lumay](#geoffroy-lumay), [Filip Francqui](#filip-francqui), [Dietmar Schulze](#dietmar-schulze) |
| [Spreadability & powder-bed metrology](#6-spreadability--powder-bed-metrology) | [Zackary Snow](#zackary-snow), [Edward Reutzel](#edward-reutzel), [Sina Haeri](#sina-haeri), [Brika & Brailovski](#salah-eddine-brika--vladimir-brailovski), [Justin Whiting](#justin-whiting), [Alkan Donmez](#alkan-donmez), [Edward J. Garboczi](#edward-j-garboczi), [John A. Slotwinski](#john-a-slotwinski), [Mohr & Hilgenberg (BAM)](#gunther-mohr--kai-hilgenberg-bam), [Iver E. Anderson](#iver-e-anderson), [Emma White](#emma-white), [Mahdi Habibnejad-Korayem](#mahdi-habibnejad-korayem), [AM powder producers](#am-powder-producers-equispheres--carpenter-additive--6k-additive) |
| [Standards bodies & TMS 2027 symposium organizers](#7-standards-bodies--tms-2027-symposium-organizers) | [ASTM B09](#astm-committee-b09-metal-powders), [ASTM F42 / AM CoE](#astm-f42--am-center-of-excellence), [MPIF](#mpif), [America Makes / ANSI AMSC](#america-makes--ansi-amsc), [TMS symposium 075 organizers](#tms-2027-symposium-075-powder-materials-processing-and-fundamental-understanding--organizers), [TMS symposium 059 organizers](#tms-2027-symposium-059-atomization--powder-metallurgy-honoring-iver-anderson--organizers) |

---

## 1. Powder-mechanics / particle-technology PIs

### Mojtaba Ghadiri

Professor Emeritus of Particle Technology, University of Leeds. Pioneer of
cohesive-powder rheometry and low-stress flowability measurement (Schulze
shear cell, raining-bed, Sevilla powder tester, ball indentation); his
"Rheometry of cohesive powder flow" work addresses exactly the inference of
cohesion and friction from bulk-scale tests. No public direct email found;
reachable via the Leeds School of Chemical and Process Engineering staff
directory.

(source: <https://eps.leeds.ac.uk/chemical-engineering>)

### Ali Hassanpour

Professor of Particle Technology, University of Leeds. Publishes on both
sides of the abstract's bridge: DEM of cohesive powders and flowability
(including temperature effects on aluminium powder flow) *and*
AM spreadability as a function of particle size and surface cohesiveness.
Reachable via the Leeds staff directory.

(source: <https://eps.leeds.ac.uk/chemical-engineering>)

### Colin Hare

Senior Lecturer in Particle Technology, Newcastle University (formerly
Surrey). Co-author on FT4-rheometer dynamics and low-stress powder
flowability studies; well placed to advise which validation metrics (shear
cell vs Hall funnel) are informative for cohesive metal powders. Reachable
via the Newcastle Engineering staff directory.

(source: <https://www.ncl.ac.uk/engineering/staff/>)

### Christine M. Hrenya

Professor, Chemical and Biological Engineering, CU Boulder. Bridges
micro-level cohesive-particle measurements to macro-level flow behavior
(cohesive DEM closures, *J. Fluid Mech.* 2017) and published on reducing
uncertainty-quantification cost in DEM particulate-flow models — relevant to
uncertainty-aware inverse property inference from dosing curves.

(source: <https://www.colorado.edu/chbe/christine-hrenya>)

### Fernando J. Muzzio

Distinguished Professor, Rutgers; co-director of C-SOPS. Leading figure in
powder feeding/mixing and multivariate powder characterization for
continuous manufacturing — the pharma analogue of "feeder response as a
probe of powder properties."

(source: <https://cbe.rutgers.edu/faculty>)

### Benjamin J. Glasser

Professor, Rutgers Chemical and Biochemical Engineering. Granular flow
regimes in industrial equipment (rotating drums, feed systems); complements
Muzzio on mechanistic interpretation of how actuator settings and powder
properties jointly set dispensed mass.

(source: <https://cbe.rutgers.edu/faculty>)

### Jochen Schmidt

Research group leader, Institute of Particle Technology (LFG), FAU
Erlangen-Nürnberg. Authored the review on dry powder coating in AM, which
compares Hall flow, shear-cell, and rheometer characterization of cohesive
AM feedstocks for dosing and spreading; flow-aid surface modification is a
practical lever if the lab's fine alloy precursors won't flow. Email
published in the open-access paper: `jochen.schmidt@fau.de`.

(source: <https://doi.org/10.3389/fceng.2022.995221>)

### Mike Bradley / Wolfson Centre for Bulk Solids Handling Technology

**[own-search]** Professor and Director, Wolfson Centre, University of
Greenwich — 50 years of industrial bulk-solids consultancy (hopper design,
feeder discharge consistency, caking, segregation). A practical short-course
/ consultancy route for the doser's hopper- and flow-design questions rather
than a co-authorship contact. Org channel: `wolfsoncentre@gre.ac.uk`.

(source: <https://www.gre.ac.uk/engsci/research/groups/wolfsoncentre>)

### Marco Ramaioli

**[own-search]** Senior Research Scientist (Directeur de recherche), INRAE /
Université Paris-Saclay (formerly Nestlé and University of Surrey).
Co-author of *"Experiments and Discrete Element Simulation of the Dosing of
Cohesive Powders in a Simplified Geometry"* (with Imole, Krijgsman,
Weinhart, Magnanimo, Chávez Montes, Luding) — the closest published
precedent for the abstract's screw-dosing-as-property-probe framing — and of
pulse-inertia micro-dosing of fine cohesive powders.

(source: <https://arxiv.org/abs/1410.2886>)

---

## 2. Metal-AM feedstock flow-property authors

### Lorenzo Marchetti

KTH Royal Institute of Technology, Materials Science and Engineering. Lead
author of the 8-method comparison of flowability tests on 11 steel/tool-steel
powders: Hall/Carney funnels jam on cohesive powders while shear-cell
metrics capture stress-state-dependent flow — a key caveat for the
abstract's Hall-flow validation leg. Email published with the paper:
`lormar@kth.se`.

(source: <https://doi.org/10.1016/j.powtec.2021.01.074>)

### Christopher Hulme-Smith

KTH Royal Institute of Technology; co-author of the Marchetti comparison and
broadly active in metal-powder characterization for AM. Email published with
the paper: `chrihs@kth.se`.

(source: <https://doi.org/10.1016/j.powtec.2021.01.074>)

### Adriaan B. Spierings

Inspire AG / ETH Zürich. Author of the seminal powder-flowability
characterization methodology for powder-bed metal AM (avalanche-angle
statistics for 21 Fe/Ni powders; 550+ citations) and a thesis-level
rotating-drum spreadability metric designed to be closer to SLM layering
than Hall flow. Email published with the paper: `spierings@inspire.ethz.ch`.

(source: <https://doi.org/10.1007/s40964-015-0001-4>)

### Jose Alberto Muñiz-Lerma

McGill University, REGAL Aluminum Research Center. Comprehensive AlSi7Mg
feedstock characterization including moisture sorption, surface energy, work
of cohesion, and powder rheology — directly relevant to the lab's AlSi10Mg
and fine elemental-powder handling. Email published with the paper:
`jose.muniz@mcgill.ca`.

(source: <https://doi.org/10.3390/ma11122386>)

### Mathieu Brochu

Professor, McGill Mining and Materials Engineering; corresponding author of
the AlSi7Mg study linking fines, moisture uptake, cohesion, and
spreadability. Email published with the paper: `mathieu.brochu@mcgill.ca`.

(source: <https://doi.org/10.3390/ma11122386>)

### Laura Cordova

University of Twente (MS3). Lead author of the highly cited thin-layer
spreadability and apparent-density study across IN718, Ti-6Al-4V, AlSi10Mg,
and Scalmalloy — tests whether conventional bulk flow measures miss
process-relevant layer-spreading behavior. Reachable via the Twente people
directory.

(source: <https://doi.org/10.1016/j.addma.2020.101082>)

### Paul R. Mort / Michael P. Sealy

Purdue University, Materials Engineering. Co-authors of the 2026 review on
powder characterization for in-space AM — fine, irregular, cohesive powders
under non-standard conditions, synthesizing characterization viability and
modeling; an unusually good match for a NASA-Space-Grant-scale project.
Corresponding email published with the paper: `msealy@purdue.edu`.

(source: <https://doi.org/10.1038/s44334-026-00071-2>)

---

## 3. DEM & Bayesian-calibration methodology

### Hongyang Cheng / GrainLearning

Assistant Professor, Multi-Scale Mechanics, University of Twente. Lead
developer of **GrainLearning**, the open-source Bayesian
uncertainty-quantification toolbox for calibrating DEM/continuum granular
models, and lead author of the iterative Bayesian filtering framework for
automated DEM calibration — the closest existing methodological match to the
abstract's plan to infer cohesion/friction from dosing data. GitHub:
[`GrainLearning/grainLearning`](https://github.com/GrainLearning/grainLearning).

(source: <https://people.utwente.nl/h.cheng>)

### Vanessa Magnanimo

Associate Professor, Multi-Scale Mechanics, University of Twente. Co-author
on iterative Bayesian DEM calibration and on cohesive granular rheology
mapping friction/cohesion to macroscopic shear response; also a co-author of
the cohesive-powder dosing paper with [Ramaioli](#marco-ramaioli).

(source: <https://people.utwente.nl/v.magnanimo>)

### Stefan Luding

Professor of Multiscale Mechanics, University of Twente. Senior author on
steady-state rheology of cohesive granular materials (friction–Bond-number
phase diagrams) and on the cohesive-powder dosing study; co-author of
GrainLearning papers.

(source: <https://people.utwente.nl/s.luding>)

### Klaus Thoeni

Senior Lecturer, University of Newcastle (Australia). GrainLearning
co-developer; sequential quasi-Monte-Carlo filtering for probabilistic DEM
calibration.

(source: <https://www.newcastle.edu.au/profile/klaus-thoeni>)

### Takayuki Shuku

Tokyo City University. Co-author of the probabilistic and iterative Bayesian
DEM-calibration frameworks. No direct public email found; reachable via the
university directory.

(source: <https://www.tcu.ac.jp/>)

### Bilal El Kassem

**[own-search]** RWTH Aachen (Institute of General Mechanics) / Bayer.
Published the most directly on-topic calibration precedent: a
semi-automated DEM parameter-calibration technique for powders based on bulk
responses (angle of repose, bulk density, mass flow rate) extracted from
**auger dosing experiments**, plus DoE/multivariate machine-design studies of
vertical micro-auger dosing.

(source: <https://www.jstage.jst.go.jp/article/kona/38/0/38_2021010/_html/-char/en>)

### Carl Wassgren

Professor, Mechanical Engineering, Purdue. Co-author of the *Powder
Technology* perspective on calibration and application of DEM models for
industrial bulk powder processes — when and how DEM contact parameters
should be calibrated against macroscopic experiments; deep pharma
screw-feeder DEM experience.

(source: <https://engineering.purdue.edu/ME/People/ptProfile?resource_id=11579>)

### Jin Ooi

Professor, University of Edinburgh. DEM of silo flow and bulk-solids
mechanics; co-author of the 2026 scientific-ML-for-granular-materials
review; long-time organizer of the DEM calibration community (and of
Edinburgh's commercial spin-off activity around EDEM).

(source: <https://www.eng.ed.ac.uk/about/people/prof-jin-ooi>)

### Thorsten Pöschel

Professor, Institute for Multiscale Simulation, FAU Erlangen-Nürnberg. DEM
of powder spreading for AM and non-spherical particle dynamics — connects
the calibration story to the spreadability claim.

(source: <https://www.mss.cbi.fau.de/team/thorsten-poeschel/>)

### Paul Cleary

Chief Research Scientist, CSIRO Data61. Co-author of the early validated DEM
study of screw-conveyor performance vs laboratory experiments (Owen &
Cleary) — the canonical auger-DEM validation reference.

(source: <https://people.csiro.au/C/P/Paul-Cleary>)

### Marc Fransen

Researcher, Deltares (NL); co-first author of the 2026
ML-for-granular-materials review; stochastic/metamodel-based DEM calibration
and robust design optimization.

(source: <https://www.deltares.nl/en/contact>)

### Krishna Kumar

Assistant Professor, UT Austin. Graph-neural-network surrogates and
differentiable-simulator inverse analysis for granular flows — the
learned-surrogate route to replacing expensive DEM sweeps in the inference
loop.

(source: <https://www.caee.utexas.edu/people/faculty/faculty-directory/kumar>)

### WaiChing Sun

Associate Professor, Columbia University. Scientific-ML mechanics;
interpretable constitutive-model discovery (neural symbolic regression)
applicable to extracting effective cohesion/friction models from dosing
curves.

(source: <https://www.civil.columbia.edu/content/waiching-sun>)

### Fabio Ramos

NVIDIA / University of Sydney. Co-author of *"Inferring the Material
Properties of Granular Media for Robotic Tasks"* (ICRA 2020) —
likelihood-free Bayesian inference (BayesSim) of DEM friction/restitution
parameters from macroscopic observations; the closest robotics-side
precedent for the abstract's inverse-inference plan.

(source: <https://www.sydney.edu.au/engineering/about/our-people/academic-staff/fabio-ramos.html>)

### Daniel N. Wilke

Professor, University of Pretoria. GPU-based DEM and Bayesian DEM
calibration; computational efficiency for DEM parameter-space exploration
relevant to multi-task calibration over many powders.

(source: <https://www.up.ac.za/mechanical-and-aeronautical-engineering/article/51789/prof-dn-wilke>)

---

## 4. DEM software teams

### Thomas Weinhart / MercuryDPM

Assistant Professor, University of Twente; core developer of
**MercuryDPM** (open-source DEM with built-in cohesive contact laws and
coarse-graining). Also a co-author of the cohesive-powder dosing study.

(source: <https://people.utwente.nl/t.weinhart>)

### Christoph Kloss / LIGGGHTS / Aspherix

Founder/CEO, DCS Computing (Linz). Original lead developer of LIGGGHTS
(open-source, JKR/SJKR cohesive models) and of the commercial Aspherix DEM.

(source: <https://www.aspherix-dem.com/contact/>)

### Bruno Chareyre / YADE

Associate Professor, Laboratoire 3SR, Grenoble Alpes; YADE maintainer.
Python-scripted open-source DEM well suited to parameter sweeps and inverse
calibration (YADE ships a GrainLearning Bayesian-calibration tutorial).

(source: <https://yade-dem.org/doc/BayesianCalibration.html>)

### Bruno Blais / Lethe

Associate Professor, Polytechnique Montréal. Lead developer of **Lethe**
(open-source CFD-DEM on deal.II) with published AM powder-spreading
simulation work. GitHub: [`lethe-cfd/lethe`](https://github.com/lethe-cfd/lethe).

(source: <https://www.polymtl.ca/expertises/en/blais-bruno>)

### MFiX-DEM team (NETL)

DOE-supported open-source multiphase/DEM suite with documented calibration
examples; public forum is the contact channel.

(source: <https://mfix.netl.doe.gov/>)

### Altair EDEM

The most widely used commercial DEM in pharma/AM powder work; ships the
Edinburgh Elasto-Plastic Adhesion cohesive model, calibration workflows, and
virtual shear-cell / Hall-flow test modules. Application-engineering contact
via the product page.

(source: <https://www.altair.com/edem>)

---

## 5. Flow-characterization instrument makers

*(Freeman Technology / Micromeritics also appears in
[`07-…md`](07-powder-dispensing-outreach-contacts.md#freeman-technology-micromeritics--ft4-powder-rheometer)
as a vendor; the entries here are the powder-properties application-science
contacts.)*

### Tim Freeman

Founder / Managing Director, Freeman Technology (Micromeritics); developer
of the FT4 Powder Rheometer, the reference instrument for dynamic + shear +
bulk powder-property measurement. No public personal email; contact via the
company page.

(source: <https://www.freemantech.co.uk/contact-us>)

### Geoffroy Lumay

Professor of Physics, University of Liège (GRASP lab); co-founder of
Granutools. Rotating-drum cohesion metrics (GranuDrum) widely used for AM
powders and for DEM-calibration cross-checks; ideal dual academic/industry
contact.

(source: <https://www.granutools.com/contact>)

### Filip Francqui

CEO / co-founder, Granutools. Practical application contact for dynamic and
cohesive-flow metrics complementary to shear-cell and Hall-funnel testing;
co-author on DEM-calibration-from-GranuDrum studies.

(source: <https://www.granutools.com/contact>)

### Dietmar Schulze

Developer of the Schulze Ring Shear Tester (the instrument behind ASTM
D6773) and author of *Powders and Bulk Solids* — the definitive reference on
yield-locus construction and cohesion determination, i.e., exactly what the
abstract's DEM-inferred parameters would be validated against.

(source: <https://www.dietmar-schulze.de/contact.html>)

---

## 6. Spreadability & powder-bed metrology

### Zackary Snow

Penn State ARL / CIMP-3D. First author of the foundational spreadability
metrics + feedstock-requirements paper for PBF (*Additive Manufacturing*
2019); found angle-of-repose thresholds predicting spreading failure — the
downstream quantity the abstract proposes to anticipate from dosing data.

(source: <https://www.arl.psu.edu/>)

### Edward Reutzel

Director, CIMP-3D, Penn State ARL; senior co-author with Snow on AM process
monitoring and powder-bed quality. Also already flagged in the dispensing
outreach note's Penn State entries (Simpson/Beese) — one intro email could
cover both threads.

(source: <https://www.arl.psu.edu/>)

### Sina Haeri

University of Strathclyde (formerly Edinburgh). Pioneered DEM of powder
spreading and blade-spreader geometry optimization with multi-sphere
realistic particle shapes; connects the same contact-law parameters the
abstract wants to infer to layer-quality outcomes. Email published with his
papers: `sina.haeri@strath.ac.uk`.

(source: <https://strathprints.strath.ac.uk/61535/>)

### Salah Eddine Brika & Vladimir Brailovski

École de technologie supérieure (ÉTS), Montréal. Built a spreading apparatus
measuring powder-bed density, surface uniformity, and spreading force vs
powder characteristics and recoating conditions — a ready-made validation
partner for the dosing→spreadability link.

(source: <https://doi.org/10.3390/jmmp7040135>)

### Justin Whiting

NIST Engineering Laboratory; AM Powder Metrology Laboratory (powder
spreading testbed). Co-author of *"A more efficient method for calibrating
DEM parameters for simulations of metallic powder used in additive
manufacturing"* (Granular Matter 2018) — NIST work sitting exactly at the
abstract's DEM-calibration × AM-powder intersection.

(source: <https://www.nist.gov/laboratories/tools-instruments/additive-manufacturing-powder-metrology-laboratory>)

### Alkan Donmez

NIST Engineering Laboratory; leads AM machine/process metrology, co-author
on the NIST DEM-calibration and PSD-vs-rheology studies (17-4 PH).
Reachable via the NIST staff directory.

(source: <https://www.nist.gov/people>)

### Edward J. Garboczi

NIST Applied Chemicals and Materials Division (Boulder). X-ray CT particle
shape/size analysis for AM powders and co-author of the metrology-needs
review — the measurement-science foundation for the PSDs feeding the
abstract's DEM.

(source: <https://www.nist.gov/people/edward-garboczi>)

### John A. Slotwinski

JHU Applied Physics Laboratory (ex-NIST). Co-author of NIST IR 7873 and the
JOM metrology-needs paper behind ASTM F3049; on record that best practice
combines shear, dynamic, and bulk measurements — the same multi-method
validation stance as the abstract. Email published with the paper:
`john.slotwinski@jhuapl.edu`.

(source: <https://doi.org/10.1007/s11837-014-1290-7>)

### Gunther Mohr & Kai Hilgenberg (BAM)

BAM Berlin / TU Berlin. Powder-layer emissivity, thermography/optical
tomography defect detection, and high-resolution in-situ surface-structure
analysis — the group most directly probing whether measurable powder-bed
states predict part quality. Reachable via BAM's contact page.

(source: <https://www.bam.de/Navigation/EN/Service/Contact/contact.html>)

### Iver E. Anderson

Ames National Laboratory (emeritus). The gas-atomization authority; can
weigh in on how production route, PSD, and surface chemistry set the
cohesion/friction the doser would probe. Honoree of TMS 2027 symposium 059
(see [below](#tms-2027-symposium-059-atomization--powder-metallurgy-honoring-iver-anderson--organizers)).

(source: <https://www.ameslab.gov/about/contact-us>)

### Emma White

Team leader, DECHEMA Forschungsinstitut (ex-Ames Lab); powder metallurgy,
gas atomization, and AM feedstock work with Anderson; co-organizer of TMS
2027 symposium 059.

(source: <https://www.tms.org/tms2027/downloads/flyers/TMS2027-CFA-Flyer-059.pdf>)

### Mahdi Habibnejad-Korayem

AP&C (GE Additive) / NRC Canada publications on plasma-atomized Ti-6Al-4V,
off-size powder utilization, and recoater-parameter effects on spreadability
— an industry-side reviewer for whether dosing-derived properties track
recoating performance.

(source: <https://nrc.canada.ca/en/corporate/contact-us>)

### AM powder producers (Equispheres / Carpenter Additive / 6K Additive)

Company-level contacts for production-side perspective on how powder-making
route sets morphology, PSD, flow, and reuse behavior: Equispheres
(<https://equispheres.com/contact/>), Carpenter Additive
(<https://www.carpenteradditive.com/contact>), 6K Additive
(<https://www.6kinc.com/contact/>). Useful if the lab wants to test whether
a dosing-derived calibration signature generalizes across production routes.

(source: <https://equispheres.com/contact/>)

---

## 7. Standards bodies & TMS 2027 symposium organizers

### ASTM Committee B09 (metal powders)

Governs the Hall flowmeter and apparent-density standards (B213, B212, B855)
the abstract cites for validation; B09 staff can clarify applicability of
Hall flow to fine, cohesive powders that jam the standard funnel.

(source: <https://www.astm.org/committee/b09>)

### ASTM F42 / AM Center of Excellence

F42.01 (test methods) is the standards forum for AM powder characterization
(F3049, ISO/ASTM 52907); the AM CoE runs round-robin metrology efforts a
dosing-derived proxy method could eventually be benchmarked in.

(source: <https://www.astm.org/committee-f42-additive-manufacturing-technologies.html>)

### MPIF

Metal Powder Industries Federation — PM-industry standards for Hall flow,
apparent/tap density referenced by ASTM F3049; practical test-method
guidance for alloy-precursor powders.

(source: <https://www.mpif.org/About-MPIF/Contact-Us.aspx>)

### America Makes / ANSI AMSC

The ANSI AMSC roadmap explicitly flagged spreadability ("PM2") as a
standards gap — useful context for positioning the abstract's
dosing-as-proxy idea.

(source: <https://www.americamakes.us/contact/>)

### TMS 2027 symposium 075 "Powder Materials Processing and Fundamental Understanding" — organizers

**[own-search]** This is the symposium Will's abstract is assigned to (per
PR #78); its organizers are, in effect, the powder-properties audience that
will judge the talk, and its scope explicitly welcomes powder modeling/
simulation and ML in powder materials science. Organizers (affiliations from
the PR #78 catalog): Elisa Torresani (San Diego State), Kathy Lu (UAB),
Eugene Olevsky (San Diego State), Diletta Giuntini (TU Eindhoven), Paul
Prichard (ORNL), Wenwu Xu (San Diego State), Bowen Li (Michigan Tech),
Charles Maniere (CNRS CRISMAT), Thomas Grippi (Toulouse CIRIMAT), Ma Qian
(RMIT — titanium powder metallurgy), Rajendra Bordia (Clemson). Reaching out
ahead of the meeting (e.g., to Torresani/Olevsky as lead organizers) is a
low-cost way to get powder-properties feedback on the exact framing.

(source: <https://www.tms.org/tms2027/downloads/flyers/TMS2027-CFA-Flyer-075.pdf>)

### TMS 2027 symposium 059 "Atomization & Powder Metallurgy" (honoring Iver Anderson) — organizers

**[own-search]** The alternate powder-community venue ranked #1 in PR #78's
earlier analysis for the powder-dosing abstract. Organizers: Emma White
(DECHEMA), Hani Henein (University of Alberta — impulse atomization, rapid
solidification), Jordan Tiarks (Ames National Laboratory — high-pressure gas
atomization). All three are strong powder-properties/production contacts
independent of the symposium itself.

(source: <https://www.tms.org/tms2027/downloads/flyers/TMS2027-CFA-Flyer-059.pdf>)

---

## Suggested next actions

1. **For the abstract itself:** ask 1-2 organizers of
   [symposium 075](#tms-2027-symposium-075-powder-materials-processing-and-fundamental-understanding--organizers)
   whether the dosing-as-mechanistic-probe framing lands, and send
   [Hongyang Cheng](#hongyang-cheng--grainlearning) and
   [Bilal El Kassem](#bilal-el-kassem) a short note — GrainLearning + the
   auger-dosing calibration papers are the two closest methodological
   precedents, and both groups are natural reviewers or collaborators.
2. **For the validation plan:** contact
   [Marchetti / Hulme-Smith](#lorenzo-marchetti) (which flow tests are
   meaningful for cohesive steel powders) and
   [Dietmar Schulze](#dietmar-schulze) or the
   [Wolfson Centre](#mike-bradley--wolfson-centre-for-bulk-solids-handling-technology)
   before buying/borrowing a shear cell.
3. **For the spreadability claim:** [Sina Haeri](#sina-haeri) (DEM side) and
   [Brika & Brailovski](#salah-eddine-brika--vladimir-brailovski) (rig side)
   are the two most direct partners for testing whether dosing-derived
   properties predict spreading outcomes; NIST's
   [AM Powder Metrology Lab](#justin-whiting) is the metrology-grade
   version of the same question.
4. **Cross-reference before emailing:** several targets (Penn State, Freeman
   Technology, Ames/Anderson, ASTM/America Makes) already have entries in
   [`07-powder-dispensing-outreach-contacts.md`](07-powder-dispensing-outreach-contacts.md)
   — combine the dispensing and properties asks into one email per
   institution.

## See also

- [`07-powder-dispensing-outreach-contacts.md`](07-powder-dispensing-outreach-contacts.md)
  — dispensing-hardware outreach list (this PR).
- [`06-generative-cad-outreach-contacts.md`](06-generative-cad-outreach-contacts.md)
  (PR #43) — generative-CAD outreach note, same Edison-backed workflow.
- PR [#78](https://github.com/vertical-cloud-lab/powder-doser/pull/78) —
  the TMS 2027 abstracts this note is anchored to, including the full
  106-symposium catalog (`abstracts/tms-2027/tms2027_symposia.yaml`) and
  organizer backgrounds.
