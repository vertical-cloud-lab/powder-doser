# Commercial Powder Dispensing Solutions — Landscape

This document collects the commercial company / product landscape for powder
dispensing solutions, motivating the design of `powder-excavator`.

> A visual mosaic of representative product photos for every platform
> mentioned below is available in [`images/mosaic.png`](./images/mosaic.png)
> with a panel-by-panel caption in
> [`images/mosaic_caption.md`](./images/mosaic_caption.md); per-image
> source URLs are tracked in [`images/README.md`](./images/README.md) and
> [`images/_manifest.json`](./images/_manifest.json).


## Status

**All eleven Edison Scientific literature queries have now been fetched**
(five from the first batch + six from the second batch). The full
citation-backed answers are stored verbatim under
[`edison_results/`](./edison_results/) — one Markdown file per query,
plus the raw JSON response. The synthesis below references those files
and pulls out the most useful evidence-backed findings; consult the
per-query files for full tables and citations.

A second batch of six follow-up queries was added to fill the gaps
identified in the first synthesis — in particular **MTI** (both MTI
Corporation lab equipment and MTI Mixers industrial), Acrison / Hapman /
AZO / PSL / Matcon, mainstream liquid-handler powder modules (Hamilton,
Tecan, Zinsser, Gilson, Sartorius, CyBio, Anton Paar), acoustic / piezo
dry-powder microdispensers and the specific Quantos QX1/QX2 and Chemspeed
Powdernium product lines, and academic / open-source robotic dispensers.
A short summary of what those second-batch queries actually returned is in
[§ 6 below](#6-second-batch-findings-mti-bulk-vendors-liquid-handler-powder-modules-acousticpiezo-academicopen-source).

A **third pass** (July 2026) then web-searched for commercial solutions the
first two Edison batches missed and found eleven additional offerings — Sirius
Automation, GiroNEX, Unchained Labs Stuntman, Trajan/Axel Semrau CHRONECT XPR,
Labman Automation, XQ Instruments, Lambda Instruments, Mettler-Toledo XPR
auto-dosing, Harro Höfliger and Syntegon — plus two corrections to earlier
negative conclusions. See
[§ 7 below](#7-third-pass-additions--commercial-solutions-missed-in-batches-12).

| Tag (file) | Focus | Batch |
| --- | --- | --- |
| [`commercial-powder-dispensers-overview`](./edison_results/commercial-powder-dispensers-overview.md) | Cross-cutting landscape (lab + industrial) | 1 |
| [`lab-automated-powder-dispensing-companies`](./edison_results/lab-automated-powder-dispensing-companies.md) | Lab vendors and model names | 1 |
| [`powder-dosing-technology-comparison`](./edison_results/powder-dosing-technology-comparison.md) | Technology-by-technology comparison | 1 |
| [`industrial-powder-feeders-bulk-handling`](./edison_results/industrial-powder-feeders-bulk-handling.md) | Industrial / bulk vendors | 1 |
| [`micro-dose-mg-precision-dispensers`](./edison_results/micro-dose-mg-precision-dispensers.md) | mg / sub-mg precision instruments | 1 |
| [`mti-corporation-lab-powder-equipment`](./edison_results/mti-corporation-lab-powder-equipment.md) | MTI Corporation (mtixtl.com) lab/materials-research equipment | 2 |
| [`mti-mixers-industrial-powder-handling`](./edison_results/mti-mixers-industrial-powder-handling.md) | MTI Mixers / MTI Group industrial powder mixing & handling | 2 |
| [`industrial-bulk-vendors-acrison-hapman-azo-psl-matcon`](./edison_results/industrial-bulk-vendors-acrison-hapman-azo-psl-matcon.md) | Acrison, Hapman, AZO, PSL, Matcon model-level specs | 2 |
| [`lab-liquid-handlers-with-powder-modules`](./edison_results/lab-liquid-handlers-with-powder-modules.md) | Hamilton, Tecan, Zinsser, Gilson, Sartorius, CyBio, Anton Paar solid-dispensing modules | 2 |
| [`acoustic-piezo-capacitive-microdose-and-quantos-qx-chemspeed-powdernium`](./edison_results/acoustic-piezo-capacitive-microdose-and-quantos-qx-chemspeed-powdernium.md) | Acoustic / piezo dry-powder dispensers + Quantos QX1/QX2 + Chemspeed Powdernium / GDU specifics | 2 |
| [`academic-and-open-source-powder-dispensing-robots`](./edison_results/academic-and-open-source-powder-dispensing-robots.md) | Academic / open-source / self-driving-lab powder dispensing robots | 2 |

## Synthesis

> All numeric specs, model names and limitations below come from the
> retrieved Edison answers. Where a vendor or product was named in the
> original prompt but no datasheet evidence was returned, that is called
> out explicitly so the gap is visible rather than fabricated.

### 1. Bench-top / laboratory automated powder dispensers

The two best-evidenced commercial benchtop platforms for HTE-grade solid
dispensing are **Mettler Toledo Quantos** and **Chemspeed**:

- **Mettler Toledo Quantos** (e.g. QB5 with QH012-LNMP head; QX96 carousel
  on an XPE206 balance). Gravimetric dosing with a combined rotary +
  tapping action and an RFID-tagged dosing head that supports parameter
  learning. Comparative benchmarking exercised it at 2, 10, 50 and 20 mg
  targets; performance is balanced across many pharmaceutical powders but
  RSD degrades sharply below ~10 mg, and over-dispensing on coarse
  powders or timeouts on poor-flowing solids (e.g. potassium acetate,
  molecular sieves, ammonium acetate) are known failure modes. The
  CHRONECT integration adds a 32-position dosing-head rack with a 6-axis
  robotic arm; reported average dispense time ≈138 s.
- **Chemspeed** (SWING / FLEX / Crystal platforms, with the **GDU-S
  SWILE** piston-and-glass-capillary head and the **GDU-Pfd** hopper /
  auger / crescent-valve head). SWILE was demonstrated effective from
  **0.1 mg to 50 mg** and is favoured for sub- to low-mg dispensing of a
  wider powder range (including sticky/oily solids); GDU-Pfd uses a
  30 mL container with a typical ±10% tolerance setting and was tested
  down to 0.5 mg. Average dispense time ≈103 s; at a 2 mg target it
  beat CHRONECT/Quantos on speed (54 vs 141 s).
- **Unchained Labs / Freeslate**: present in HTE comparisons as an
  earlier-generation automated solid + liquid dispensing platform; cited
  per-dispense times >250 s, slower than current Mettler / Chemspeed
  systems. **Symyx** is identified as a classic combinatorial supplier
  but no model-level numeric specs were retrieved.
- **Zinsser Analytic Lissy, Gilson, Hamilton STAR, Sartorius, Analytik
  Jena CyBio, Anton Paar, Retsch / Verder, Plasmatreat, AutoDose**: named
  in the prompt but **no quantitative solid-dispensing datasheet
  evidence was returned**. They appear in the literature mostly as
  generic robotic-platform / liquid-handling vendors; product-specific
  brochures will be needed to fill these in.

### 2. Micro- / milligram-scale precision dispensers

- Among gravimetric dispensers, **Quantos** is well evidenced down to
  20 mg (with mean errors growing for many powders, e.g. Al₂O₃
  −6.00 ± 0.93 %, NaNO₂ −3.96 ± 2.40 %, pectin −5.87 ± 1.37 % at 20 mg;
  near-zero mean error for most powders at 200–1000 mg).
- **Chemspeed GDU-S SWILE** is the strongest evidenced low-/sub-mg
  performer (0.1–50 mg study range).
- A field-wide observation across several reviews is that **single-shot
  dispensing below ~10 mg is broadly difficult** for any commercial
  gravimetric / hopper system; SWILE-style positive-displacement and
  acoustic / piezo approaches are the main paths beyond that limit.
- Specific user-named products **Quantos QX1 / QX2** and a **"Hamilton STAR
  powder head"** were *not* substantiated in the retrieved Edison evidence —
  they may be marketing-only names or otherwise underdocumented in the
  literature. (**Chemspeed "Powdernium"** was originally in this list but the
  third pass confirmed it is a real gravimetric workstation — 0.05 mg–gram; see
  [§ 7](#7-third-pass-additions--commercial-solutions-missed-in-batches-12).)
- True acoustic / piezo dry-powder micro-dispensers were not found with
  vendor specs in the Edison evidence set (Labcyte Echo / Scienion
  systems are predominantly liquid-only); EDC Biosystems is the only
  vendor commonly cited for ng-scale dry-powder dosing of engineered
  particles.
- The Hou (2024) micro-feeder thesis provides a useful comparison row
  set: **MG2 Microdose** vibratory sieve at 0.36–0.54 g/h, **3P
  Innovation** piezo-vibration feeder at 3.6–1440 g/h, **LCI Circle
  Feeder MD-120** rotating-vane >32 g/h, **DEC µPTS** pressure-transfer
  at 3.6–450 g/h handling sub-µm/cohesive/wet powders, and **Vibra-Flow**
  <3.6 g/h.

### 3. Industrial bulk powder feeders and dispensing

The strongest evidence is for continuous **gravimetric loss-in-weight
(LIW) screw feeders**:

- **Coperion K-Tron** — KT16 (24 kg scale), KT20 / KT35 (90 kg scale);
  pharma study targets <3 % RSD and 99–101 % feeding accuracy;
  MT-12 / MT-20 micro feeders at 32–3540 g/h. Used in the **Lilly
  continuous direct-compression** platform.
- **Schenck Process / AccuRate**, **Brabender Technologie** — appear in
  the LIW comparison literature; specific model/capacity claims for
  these are sparser in the retrieved set.
- **GEA / Buck** — split-butterfly / containment valves for contained
  charging/discharging.
- **Glatt** — appears as a containment valve patentee.
- **Gericke** — GAC232 (tool size 8) at 160–3200 L/h; integrated with
  continuous mixing equipment.
- **Hosokawa Micron** — discussed for FIBC/IBC filling, discharge and
  contained transfer at concept level.
- **Acrison, Hapman, AZO, Powder Systems Limited (PSL), Matcon, MTI
  Mixers**: no primary model/capacity sources were retrieved; treat
  claims about these vendors as unconfirmed pending vendor datasheets.

### 4. Dispensing technologies compared

From `powder-dosing-technology-comparison.md`:

- **Gravimetric LIW feeders** — direct mass-flow control via load cells;
  a feeder-performance article cites achievable **±0.2 % of set rate
  over a 20:1 turndown**; main disturbances are refill events,
  cohesion, electrostatics and under-filled screws at high speed.
  Inherently automation-friendly because mass flow is already digitised.
- **Volumetric screw / auger feeders** — open-loop, no self-correction;
  reviews note rotating-groove volumetric devices can show **<1 %
  variation** under ideal conditions and reach 3–11 g/s, but accuracy
  degrades with bulk-density change, packing, humidity, electrostatics
  and headload variation.
- **Vibratory / piezo micro-feeders** — practical for some micro-feeding
  but limited at low rates with cohesive powders; commercial examples
  cover roughly 0.36–1440 g/h.
- **Acoustic / pneumatic micro-dispensers** — aspirate-and-dispense
  examples deliver 0.5–10 mg with ~1–2 mm tube diameters and ~2–10 kPa
  partial vacuum; few vendor specs were retrievable for true acoustic
  dry-powder ejection.
- **Quantos-style micro-dosing heads with tapping** — best evidenced
  from ~10 mg upward; powder/head matching matters more than nominal
  tolerance.
- **Robotic spatula / scoop systems** — represented by recent academic
  work (e.g. Jiang et al. 2023, dual-arm biomimetic dispensing); flexible
  on cohesive powders and powder variety, but slower per dispense than
  dedicated heads.

### 5. Gaps and opportunities for `powder-excavator`

The Edison-backed evidence highlights a consistent set of gaps in
commercial offerings that motivate this project:

1. **Sub-10 mg single-shot dispensing of cohesive powders** is poorly
   served by existing gravimetric heads; SWILE is the main credible
   option and is locked into the Chemspeed platform.
2. **Vendor-lock-in**: the well-evidenced lab platforms (Quantos,
   Chemspeed) are tightly coupled to proprietary balances, dosing heads
   and software; there is no widely-cited *open* hardware/software
   stack for HTE-grade solid dispensing.
3. **Cohesive / sticky / electrostatic / wet powders** repeatedly appear
   as failure modes across vendors. Closed-loop adaptive strategies
   (e.g. flow-aware dosing as in FLIP-style ML approaches) are mostly
   research prototypes today.
4. **Throughput gap between lab and industrial scales**: lab heads
   operate at mg/dispense × ~100 s/dispense; industrial LIW feeders
   start in the kg/h range. The g/min "kilo-lab" middle ground is
   under-served.
5. **Cross-platform integration**: most vendors expose limited APIs and
   few publish protocols suitable for autonomous / self-driving-lab
   orchestration; new entrants have a clear opening on
   automation-friendly integration.

### 6. Second-batch findings (MTI, bulk vendors, liquid-handler powder modules, acoustic/piezo, academic/open-source)

These six queries were specifically targeted at the gaps called out in
§ 1–§ 4. The dominant outcome is **negative evidence**: for most of the
vendor product families that motivated the queries, Edison's
literature-search tooling could not retrieve primary datasheets or
peer-reviewed quantitative specs — only project specifications,
patents, and indirect mentions. That is itself useful: it confirms that
specs for these instruments are not openly published in the academic
corpus and would have to be obtained from vendor PDFs or direct contact.

- **MTI Corporation (mtixtl.com) lab equipment**
  ([`mti-corporation-lab-powder-equipment`](./edison_results/mti-corporation-lab-powder-equipment.md)) —
  No vendor datasheets retrieved. Peer-reviewed papers do confirm
  recurring use of MTI hardware in battery / ceramics / additive
  research: the **MSK-SFM-3** desktop high-speed vibrating ball-mill
  mixer (and **MSK-SFM-3-F** SS variant) for dry milling of oxide /
  niobate / glass powders, and MTI as a supplier of graphite powder /
  Cu foil and the **BST8-WA** battery analyzer. Mechanism, dose ranges,
  glovebox compatibility, and pricing are not stated in the retrieved
  sources. The model line implied by the *AM-PD6* powder-dispensing
  station shown in our image set (panel "MTI Corp. powder station") is
  not substantiated by retrievable literature.
- **MTI Mixers / MTI Group industrial**
  ([`mti-mixers-industrial-powder-handling`](./edison_results/mti-mixers-industrial-powder-handling.md)) —
  No primary brochures retrieved. Edison did, however, give a useful
  **disambiguation**: at least three distinct "MTI" entities appear
  in the powder literature — MTI Corporation (mtixtl.com, lab/battery
  supplier), MTI Mixers (mtimixer.com, industrial mixers), and
  **Mischtechnik International (MTI) GmbH** (a separate German
  mixing-technology firm cited in powder-coating R&D for ~1 kg
  Premixer batches). Treat the three as different companies in any
  downstream reference.
- **Acrison / Hapman / AZO / PSL / Matcon**
  ([`industrial-bulk-vendors-acrison-hapman-azo-psl-matcon`](./edison_results/industrial-bulk-vendors-acrison-hapman-azo-psl-matcon.md)) —
  Only two model-level numeric specs were retrievable, both indirect:
  (i) an **Acrison-compatible volumetric auger feeder** in a project
  specification — 0.03–0.9 ft³/h (≈0.56–16.6 lb/h), ±2 % full-scale
  accuracy, 30:1 VFD turndown, 4–20 mA control; and (ii) **Matcon's
  IBC cone-valve discharge apparatus** from patent WO2021099805A1 —
  ≈200–500 mm body (typical 250 mm), <1 s lift, lockable lever for
  metered discharge, qualitative containment via multiple seals. No
  vendor-datasheet specs were retrievable for Hapman, AZO, or PSL.
  These remain on the "needs vendor PDF" list.
- **Liquid-handler powder modules (Hamilton, Tecan, Zinsser, Gilson, Sartorius, CyBio, Anton Paar)**
  ([`lab-liquid-handlers-with-powder-modules`](./edison_results/lab-liquid-handlers-with-powder-modules.md)) —
  Across all seven vendor ecosystems, the **only** powder-dispensing
  technology with retrievable mechanistic evidence as an on-deck or
  adjacent solids station was the **Mettler-Toledo Quantos** hopper /
  feeder with rotary tapping. No vendor-branded "powder head" was
  substantiated for Hamilton STAR/STARlet/Vantage, Tecan
  Fluent/Freedom EVO, Zinsser SpeedyDoser, Gilson PIPETMAX/GX-271,
  Sartorius Cubis II MCA, Analytik Jena CyBio, or Anton Paar; one
  retrieved paper explicitly flags Quantos integration on a *non-
  Hamilton* robotic platform as a feasibility precedent. **Practical
  takeaway:** if a current liquid-handler workflow needs solids,
  Quantos is still the de-facto add-on, regardless of which liquid
  robot sits next to it.
- **Acoustic / piezo / capacitive dry-powder + Quantos QX1/QX2 + Chemspeed Powdernium / GDU**
  ([`acoustic-piezo-capacitive-microdose-and-quantos-qx-chemspeed-powdernium`](./edison_results/acoustic-piezo-capacitive-microdose-and-quantos-qx-chemspeed-powdernium.md)) —
  No retrievable evidence for **dry-powder** acoustic dispensing on
  EDC Biosystems ATS Gen5/Gen6, Scienion sciDROP-PICO, or Labcyte/
  Beckman Echo — the available literature on these instruments is
  liquid-only (assays, compound dispensing). Likewise, **no vendor-
  datasheet specs** were retrievable *via Edison* for Quantos QX1 / QX2 or for
  Chemspeed *Powdernium* / GDU-V/Pfd/S/P variants beyond what is
  already summarised in § 1. At the time this suggested "Powdernium",
  "Quantos QX1/QX2", and "Hamilton STAR powder head" were marketing- or
  configuration-level names. **Update (batch 3):** vendor/trade-press
  sources subsequently confirmed **Powdernium** as a real gravimetric
  workstation (0.05 mg–gram) — see
  [§ 7](#7-third-pass-additions--commercial-solutions-missed-in-batches-12);
  Quantos QX1/QX2 and the Hamilton powder head remain unsubstantiated.
- **Academic / open-source robotic powder dispensing**
  ([`academic-and-open-source-powder-dispensing-robots`](./edison_results/academic-and-open-source-powder-dispensing-robots.md)) —
  The richest of the second-batch answers. Concrete systems include:
  the **Jiang et al. 2023** dual-arm biomimetic spatula dispenser
  (ABB YuMi + analytical balance, 20 mg–1 g, ~2 % error on
  non-challenging solids, fuzzy-logic shaking, code/models on
  GitHub/Zenodo, struggles with hygroscopic and compressible powders);
  the **Berkeley A-Lab** autonomous inorganic-synthesis platform
  using a central robot arm to dose powders into furnaces; and a
  family of FLIP-style flow-aware ML dosing controllers,
  ChemOS/Coscientist/ARES integrations, and emerging Opentrons /
  3D-printed open-hardware add-ons. Common conclusions across the
  academic corpus: open systems are slower than Quantos / Chemspeed
  per dispense, but cover a broader powder zoo, and almost
  universally cite **<10 mg dispensing** and **cohesive / hygroscopic
  powders** as the unsolved frontier — the same gaps identified in
  § 5 above.

#### Updated gaps after batch 2

Batch 2 mostly *strengthens* the gap analysis in § 5 rather than
closing it:

- **Vendor publication gap.** Even with targeted, vendor-specific
  Edison queries, datasheet-grade specs for Acrison, Hapman, AZO,
  PSL, MTI Mixers, MTI Corporation powder stations, Hamilton/Tecan/
  Gilson/Zinsser/Sartorius/CyBio/Anton Paar solid modules, Quantos
  QX1/QX2, and Chemspeed Powdernium/GDU variants are largely
  *not in the open literature*. Anyone designing against these
  systems will need the vendor PDFs in hand.
- **No on-deck powder head from the major liquid-handler OEMs.** Their
  documented strategy is to integrate Mettler-Toledo Quantos rather
  than ship a first-party powder dispenser — leaving a clear opening
  for an open / interoperable powder module that talks to liquid
  handlers natively.
- **"MTI" is genuinely ambiguous.** Disambiguating MTI Corporation
  vs MTI Mixers vs Mischtechnik International (MTI) GmbH should be
  done explicitly anywhere these vendors are cited.
- **Acoustic dry-powder dispensing remains a research aspiration**,
  not a commercially-substantiated capability — relevant prior art for
  any future `powder-excavator` direction targeting nano-/microparticle
  ejection.
- **The academic open-source corpus already provides credible reference
  designs** (Jiang 2023 spatula, A-Lab, FLIP) but none yet matches
  Quantos / Chemspeed on per-dispense speed at ≤10 mg — the natural
  benchmark for `powder-excavator`.


### 7. Third-pass additions — commercial solutions missed in batches 1–2

A third pass (July 2026, web/vendor-sourced rather than Edison, because the
"vendor publication gap" identified in § 6 means these systems are documented
on vendor and trade-press pages rather than in the peer-reviewed corpus)
surfaced eleven commercial powder-dispensing offerings that the first two
passes did not capture. Several come with hard, first-party specs, and two of
them **correct earlier negative conclusions** in this document.

**Bench-top / lab gravimetric dispensers (new):**

- **Sirius Automation** (siriusautomation.com) — a whole family of gravimetric
  powder-dispensing robots that the prior passes missed entirely:
  **LibraryDoser** (0.1 / 0.01 mg weighing on Mettler-Toledo analytical
  balances; up to 20 powder sources → 96 target vials/minitubes; ~20″ cube
  footprint, glovebox/hood-compatible; CSV in/out; 21 CFR Part 11-capable),
  plus **GraviTracPlus**, **EveriDoser**, **MultiTasker II**, and
  **MicroTasker**. Directly relevant open-vs-proprietary comparators.
  Sources: [LibraryDoser](https://siriusautomation.com/librarydoser/),
  [product line](https://siriusautomation.com/lab-automation-systems/).
- **GiroNEX Cube / Cube Plus** (gironex.com) — micro-gravimetric dispenser,
  **1 mg – 1 g** per capsule/vial at **> ±2 %** accuracy, **Sartorius** 5–6
  decimal-place weigh cells, interchangeable heads per powder behaviour,
  24-well dial plate, full **FDA 21 CFR Part 11** compliance; aimed at
  early-phase clinical-trial capsule/vial/syringe filling. Sources:
  [Cube](https://www.gironex.com/cube-range/gironexcube/),
  [Cube Plus](https://www.pharmtech.com/view/cube-plus-pharmaceutical-manufacturing).
- **Unchained Labs Stuntman + Solid Dispense Station** (unchainedlabs.com) —
  Unchained Labs appears in § 1 only as the *Freeslate* legacy platform; their
  **current** solid-dispensing product is the AI-driven **Stuntman** with a
  dedicated solid-dispense station: **sub-mg to gram** range, **±0.2 mg
  repeatability for dispenses under 1 mg**, adaptive per-powder flow-learning,
  classic hoppers (10/25/50/100 mL) and SV 4 mL-vial hoppers, handles
  free-flowing through chunky solids. Sources:
  [Powder dispense](https://www.unchainedlabs.com/powder-dispense/),
  [solid-dispense spec sheet (PDF)](https://www.unchainedlabs.com/wp-content/uploads/2021/12/10_solid_dispense_station_spec_sheet.pdf).
- **Trajan / Axel Semrau CHRONECT XPR powder-liquid workstation**
  (trajanscimed.com) — § 1 mentions "CHRONECT" only as a Quantos integration;
  the distinct commercial workstation is the **CHRONECT XPR**, built on a
  Mettler-Toledo **XPR** balance: **1 mg – several grams** powder,
  **10–60 s/component**, up to **32 dosing heads / powders + 6 liquids**, up to
  **288 samples** per run, with an optional liquid module (100 mg – 10 g
  solvent). Sources:
  [XPR powder-liquid workstation](https://chronect.trajanscimed.com/xpr-powder-liquid-workstation),
  [Mettler-Toledo datasheet](https://www.mt.com/us/en/home/library/datasheets/laboratory-weighing/ds-chronect-xpr-powder.html).
- **Mettler-Toledo XPR automatic dosing** (mt.com) — the current **XPR** balance
  + automatic-dosing-head line (distinct from the older Quantos branding) is the
  common engine under CHRONECT XPR, Labman MultiDose, Sirius, and GiroNEX
  integrations; worth listing as a first-party building block. Source:
  [Automated powder dispensing](https://www.mt.com/us/en/home/applications/Laboratory_weighing/automated-powder-dispensing.html).
- **XQ Instruments (Singapore)** — low-cost **volumetric** benchtop dispensers:
  **SDB-1** (5–250 mg/shot), **SDB-2** (20 mg – 50 g), **SDB-1A**
  (automation-ready), **SDH-1** handheld, and **PCD-1** crusher-dispenser;
  fast at **2.5–3.5 s/dose** (volumetric, so accuracy is bulk-density-dependent).
  Sources:
  [dispensing solutions](https://xqinstruments.com/dispensing-solutions/),
  [SDB-1 via MSE Supplies](https://www.msesupplies.com/products/xq-automated-sdb-1-benchtop-powder-dispenser-dosing-machine).
- **Lambda Instruments LAMBDA DOSER / Hi-DOSER** (lambda-instruments.com) — the
  system linked in this thread. A microprocessor-controlled **volumetric
  powder-pump** driven by a quartz-timed stepping motor (DOSER) or BLDC motor
  (Hi-DOSER): **50 mg/min – 250 g/min** (NaCl), interchangeable 0.2/1/3 L glass
  vessels, up to 27/99 programmable speed-time steps, **RS-232/485 + 0–10 V**
  remote control and PNet PC logging, handles free-flowing solids/granules up to
  ~4 mm, from **€2,199**. A rare openly-priced, integration-friendly continuous
  feeder in the lab-to-kilolab band called out as under-served in § 5.4.
  Source: [LAMBDA Powder Doser](https://www.lambda-instruments.com/powder-doser/).

**Custom / integrator and pharma (new):**

- **Labman Automation** (labmanautomation.com) — UK integrator building custom
  HTE powder-dispensing robots, entirely absent from prior passes despite being
  a major player: **MultiDose** (a cobot — Universal Robots UR3e — loading/
  unloading two Mettler-Toledo **XPR226DRQ** automatic balances), **ZPOW**
  (controlled-vibration dispensing to **±2 mg** into deep-well plates with a
  5-decimal weigh cell), a high-throughput **flux-weighing** system (~2000 cups /
  24 h, two-powder blends to ±0.5 g), and an **Automated XPR** cell with HEPA
  extraction. Sources:
  [MultiDose](https://labmanautomation.com/portfolio/custom-system/dual-multidose-powder-dispenser/),
  [ZPOW](https://labmanautomation.com/portfolio/custom-system/zpow-powder-dispensing/),
  [flux weighing](https://labmanautomation.com/portfolio/custom-system/high-throughput-powder-dispensing-flux-weighing-system/).
- **Harro Höfliger** (hoefliger.com) — pharma micro-to-macro dosing
  (vacuum-drum and membrane filling), verifies fill quantities **down to 5 mg**
  without changing machine speed, with integrated X-ray fill-quantity control;
  relevant industrial micro-dosing prior art alongside the § 3 bulk vendors.
  Source: [Dosing and filling](https://hoefliger.com/en/technologies/know-how/dosing-and-filling).
- **Syntegon** (ex-Bosch Packaging, syntegon.com) — capsule filling and
  **vacuum-wheel dosing** specialised for dry-powder inhalation (DPI) and API
  micro-doses; another industrial micro-dosing reference.
  Source: [Capsule filling](https://www.syntegon.com/solutions/pharma/capsule-filling-machine/).

**Two corrections to earlier conclusions:**

1. **Chemspeed "Powdernium" is a real product, not a marketing-only name.**
   §§ 2 and 6 concluded that "Powdernium" was likely a marketing/configuration
   label with no separate datasheet. Vendor and trade-press material now
   documents the **Powdernium workstation** performing **traceable gravimetric
   dispensing from 0.05 mg to gram quantities** (alongside the **SWING
   POWDERDOSE** GDU configuration). The earlier "marketing-only" characterisation
   should be treated as superseded for Powdernium (the **Quantos QX1/QX2** and
   **"Hamilton STAR powder head"** names remain unsubstantiated). Sources:
   [Chemspeed solid dispensing](https://www.chemspeed.com/example-solutions/automated-precision-solid-dispensing/),
   [Powdernium via trade press](https://scientistlive.com/content/20901).
2. **Unchained Labs is an active solid-dispensing vendor, not just a legacy
   Freeslate reference** — see the Stuntman entry above.

#### Updated gaps after batch 3

The third pass does not overturn the § 5 gap analysis, but it sharpens the
competitive picture:

- **The lab HTE market is more crowded than batches 1–2 implied.** Beyond
  Quantos and Chemspeed, at least Sirius Automation, GiroNEX, Unchained Labs
  (Stuntman), Trajan CHRONECT XPR, Labman, and XQ Instruments ship
  solid-dispensing products. Any `powder-excavator` positioning should
  benchmark against this fuller set, not just the two headline vendors.
- **Almost everyone converges on the same building block.** Sirius, GiroNEX
  (Sartorius), Trajan, and Labman all wrap a *third-party analytical balance +
  automatic dosing head* (predominantly Mettler-Toledo **XPR** / Quantos, or
  Sartorius) rather than shipping a first-party powder mechanism — reinforcing
  the § 6 "no on-deck powder head from the OEMs" observation and the opening for
  an **open, balance-agnostic powder head**.
- **The ≤ 1 mg frontier still isn't closed, but claims are creeping down.**
  Unchained Stuntman advertises ±0.2 mg repeatability under 1 mg and Chemspeed
  Powdernium claims 0.05 mg; these are vendor claims, not independent
  benchmarks, so the § 2 "single-shot < 10 mg is hard" caveat stands pending
  third-party validation.
- **Openly-priced, integration-friendly continuous feeders exist** (Lambda
  DOSER, €2,199; XQ volumetric heads) but are **volumetric** — accuracy is
  bulk-density/flow-dependent, which is exactly the closed-loop-gravimetric gap
  `powder-excavator` targets.

## Submitted Edison queries

See [`edison_queries.json`](./edison_queries.json) for the full prompts and
task IDs, and [`edison_results/`](./edison_results/) for the fetched
answers (Markdown + JSON, one pair per tag).

**First batch** (fetched, in `edison_results/`):

| Tag | Focus |
| --- | --- |
| `commercial-powder-dispensers-overview` | Cross-cutting landscape (lab + industrial) |
| `lab-automated-powder-dispensing-companies` | Lab vendors and model names |
| `powder-dosing-technology-comparison` | Technology comparison table |
| `industrial-powder-feeders-bulk-handling` | Industrial / bulk vendors |
| `micro-dose-mg-precision-dispensers` | mg / sub-mg precision instruments |

**Second batch** (fetched, in `edison_results/`; second-batch synthesis is in [§ 6 above](#6-second-batch-findings-mti-bulk-vendors-liquid-handler-powder-modules-acousticpiezo-academicopen-source)):

| Tag | Focus |
| --- | --- |
| `mti-corporation-lab-powder-equipment` | MTI Corporation (mtixtl.com) lab/materials-research powder equipment |
| `mti-mixers-industrial-powder-handling` | MTI Mixers / MTI Group industrial powder mixing & handling |
| `industrial-bulk-vendors-acrison-hapman-azo-psl-matcon` | Acrison, Hapman, AZO, PSL, Matcon model-level specs |
| `lab-liquid-handlers-with-powder-modules` | Hamilton, Tecan, Zinsser, Gilson, Sartorius, CyBio, Anton Paar solid-dispensing modules |
| `acoustic-piezo-capacitive-microdose-and-quantos-qx-chemspeed-powdernium` | Acoustic/piezo dry-powder dispensers + Quantos QX1/QX2 + Chemspeed Powdernium / GDU specifics |
| `academic-and-open-source-powder-dispensing-robots` | Academic / open-source / self-driving-lab powder dispensing robots |

> The original second-batch task IDs got stuck (`get_task` returned
> HTTP 500 / progress 99 %); the user rotated the API key and the
> queries were re-submitted. The resubmitted task IDs are recorded
> under a `resubmissions[]` field on each entry of
> [`edison_queries.json`](./edison_queries.json) (originals preserved),
> and all six completed successfully under the new key.

## Reproducing the fetch

All eleven tasks completed with `status=success` (the five first-batch
tasks under their original IDs; the six second-batch tasks under the
resubmitted IDs in `resubmissions[]`). They were re-fetched with:

```python
import json, os
from edison_client import EdisonClient

client = EdisonClient(api_key=os.environ["EDISON_API_KEY"])
with open("research/edison_queries.json") as f:
    records = json.load(f)

for r in records:
    task = client.get_task(r["task_id"])
    # task.formatted_answer holds the citation-backed Markdown answer
    print(r["tag"], task.status)
```
