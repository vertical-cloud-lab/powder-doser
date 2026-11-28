# Where to run the standard tests, to check the in-house ones

The ten in-house tests in [`../README.md`](../README.md) each have a standard counterpart (ASTM, ISO
or USP). This page says where the lab can run those standard versions: at BYU, at the University
of Utah, elsewhere in Utah, or by shipping samples. It ends with a plan for a first round of checks.

- **Sources.** The labs' own web pages, read on 28 Nov 2026. Nobody has been asked for a quote yet.
- **Prices.** List prices as published, in USD, without shipping or tax. Euro prices are converted
  at 0.8975 EUR per USD, the rate #190 used.
- **Verified** means the item was read on the lab's own page. Anything else says what it was
  inferred from.
- **Every (lab, test) pair** is a row in [`labs.csv`](labs.csv): 146 rows, 57 labs, with links.

## In short

- **BYU has few of the standard instruments.** It has SEM at the EM Facility ($30–105/h) and soil
  sieving and moisture at the Environmental Analytical Lab ($30 and $8 a sample). For angle of
  repose, Hall/Carney flow, apparent and tap density and loss on drying, the standard route at BYU
  is the kit #190 priced: $436–911, plus $833–908 for an oven.
- **The University of Utah is the local lab for size and density.** Dry laser diffraction costs
  $9.10 a sample plus $64.40 a job (Sympatec HELOS/RODOS). He pycnometry is $56/h, BET $48/h and
  automated SEM particle analysis $69.30/h. No flow tester (shear cell, FT4, drum, Flodex) was found
  anywhere in Utah.
- **Micromeritics PTA is the only US commercial lab with a public price list.** Angle of repose $175,
  bulk and tap density $250, FT4 shear cell with wall friction $650, DVS $890, about 7 business
  days. It does not list Hall flow.
- **The rest are quote only.** Hall/Carney at LTI, NSL, IMR or EWI. Low-stress shear at Jenike &
  Johanson (2–3 weeks, as little as 50 g). Drum and uniaxial strength at Mercury Scientific. Charge
  at Fauske or DEKRA. Several instrument makers test samples free as a sales demo.
- **No lab runs a standard spreadability test.** ASTM F3522-22 is a guide, not a test method.
- **Plan:** three jars (salt, white rice flour, brown rice flour) to PTA, and all 13 jars through
  the Utah size and density tests. About $4,650–5,200 in lab fees and 4–5 weeks
  ([below](#recommended-plan)).

## Best option for each test

Bold is the route the plan uses. "Quote" means no published price. Numbers in parentheses are the
in-house tests each standard test checks.

| Standard test | BYU | University of Utah | Send out (price, turnaround) |
|---|---|---|---|
| Angle of repose: ISO 4324, ASTM D6393, USP <1174> (1) | None found. **Own ring stand and funnel, $35–60 (#190)** | None found | **PTA $175 a sample, about 7 business days.** Carr set (D6393): Measurlabs €662–850 + €97 an order, 3 weeks, 400 mL |
| Bulk and tapped density: ASTM B212, B329, B527, B703; USP <616>; ISO 3953 (2) | None found. **Own Class A cylinders, $60; Hall cup in the kit (#190)** | Fang group lists tap and apparent density (collaboration only) | **PTA "Bulk and Tap density USP" $250.** Metal-powder methods (B212, B329, B417, B527): LTI, NSL, quote |
| Hall and Carney flow: ASTM B213, B964; ISO 4490 (5) | **Own Hall/Carney kit, $341–791 (#190)** | Fang group lists "Flowability" (instrument not named) | LTI, NSL, IMR, EWI: quote. PTA does not list it |
| Sieving: ASTM B214 (4) | EAL soil sand fractions, 0.05–2 mm: $30 + $4 a sample, 4–7 business days. **Own sieves on order (byu-vcl#262)** | None found (Utah State's soil lab: $15 + $5) | PTA Ro-Tap $275. B214 at LTI, NSL: quote. Retsch: free demo |
| Laser diffraction: ASTM B822, ISO 13320 (4) | None confirmed | **PSSC, dry: $9.10 a sample (lab-assisted) + $64.40 a job** | PTA dry or wet $385. Free demos: Sympatec, Microtrac, HORIBA |
| Image-based size and shape: ISO 13322-1/-2, SEM (4) | **EM Facility SEM: $30–80/h for BYU users** | PSSC QICPIC (wet only) $19.80 a sample + job fee; Nanofab automated SEM-EDS $69.30/h | PTA static image analysis $650. PTL Morphologi 4-ID (1 g): quote |
| Shear cell flow function: ASTM D6128, D6773, D7891 (8) | None found | None found | **PTA FT4 shear cell + wall friction $650** (one FT4 test $315). Jenike & Johanson ring shear: quote, 2–3 weeks |
| Wall friction (3) | None found | None found | **In PTA's $650 package.** Jenike & Johanson, K-State Olathe: quote |
| FT4 dynamic flow (0, the fingerprint) | None found | None found | PTA $750 (every FT4 test, $1,595). PTL, K-State: quote |
| Rotating drum: GranuDrum (ASTM D8648), Revolution (7) | None found | None found | Mercury Scientific (Revolution), Granutools (Belgium): quote. NSL and LTI list an avalanche drum |
| Uniaxial unconfined yield strength (8) | None found | None found | Mercury Scientific Evolution UYS: quote |
| Flodex smallest orifice, USP <1174> (5) | None found | None found | PTL lists "flow through an orifice" (Flodex not named): quote |
| Moisture sorption, DVS (6) | None found | None found | **PTA $890.** PTL (1–100 g, 3–5 days), K-State, Surface Measurement Systems: quote |
| Loss on drying, USP <731> (6) | **Own oven, $833–908 (#190).** EAL moisture $8 + $4 (method not stated) | MCL TGA $66/h; Karl Fischer $106/h | PTA "percent heat loss" $150 |
| True density, He pycnometry: ASTM B923 (2 and 9, for packing fraction) | None confirmed | **MCL Anton Paar Ultrapyc 5000: $56/h**; mail-in 2–3 weeks | PTA $185. Measurlabs €131–359, 3 weeks |
| BET surface area (a DEM and ML input) | Chemical Engineering catalysis labs (collaboration) | MCL Micromeritics 3Flex: $48/h | PTA $335 |
| Powder charge, Faraday cup (10) | None found | None found | Fauske (pipe into a Faraday cup), DEKRA (based on ASTM D4470), Granutools GranuCharge: quote |
| Powder spreadability (9) | CREATE lab's powder-bed machines (collaboration) | None found | No standard test. Granutools' drum index as a proxy; Mercury Scientific SpreadStation: ask |

## Recommended plan

### Which jars

Three jars that span the doser's range, all cheap to buy in bulk and safe to ship. The mg/rev values
are the August runs at 45° ([`SAME_JAR.md`](https://github.com/vertical-cloud-lab/powder-doser/blob/e8811bd/docs/physics-simulations/runs/heldout-powders/SAME_JAR.md)).

| Jar | Why | mg/rev at 45° |
|---|---|---|
| Salt | Free-flowing and coarse (handbook d50 0.425 mm). The day's reference and the DEM twin's powder. Hygroscopic, so it also checks test 6 | 265 |
| White rice flour | At the flow / no-flow step | 37.1 |
| Brown rice flour | Cohesive: it barely leaves the doser | 0.2 |

- Use Si <44 µm (1.2 mg/rev) instead of brown rice flour if there is enough of it and its SDS
  allows shipping.
- AlSi10Mg (339 mg/rev), the AM campaign powder, goes to a metal-powder lab for Hall and Carney
  flow (step 3).
- Split each jar on the day it ships: one part for the in-house tests, one for the lab. Log RH and
  temperature. Ship in sealed containers with the SDS.

### Step 1: local tests on all 13 jars (weeks 1–3)

| Where | What | Cost | Checks test |
|---|---|---|---|
| U of U PSSC | Dry laser diffraction. One run a jar: 13 × $9.10 + $64.40 = $183. Three runs a jar: $419. One trip to Salt Lake City; email the lab first | $183–419 | 4; the PSD is also a DEM input |
| BYU EM Facility | SEM of the fine jars (Si <44 µm, fumed silica, the flours, the hydrocolloids). About 4 h at $30–80/h, plus $10 a coating run | $130–360 | 4, below its 20–30 µm limit |
| U of U MCL | He pycnometry. Assuming about 3 jars an hour, 13 jars take 4–5 h at $56/h; more if staff run it ($88/h) | about $225–280 | 2 and 9, as packing fractions |
| BYU, own kit (#190) | Ring-stand AoR, Hall/Carney with the 25 cm³ cup on the jars that flow, Class A cylinders for tap density, oven for loss on drying | $436–911, plus $833–908 for an oven, if not already bought | 1, 2, 5, 6, day to day |

### Step 2: the reference lab, three jars (weeks 1–4)

Send the three jars to Micromeritics PTA.

| Test | PTA code | Per jar | Three jars | Checks test |
|---|---|---|---|---|
| Angle of repose | Powder-09 | $175 | $525 | 1 |
| Bulk and tap density, USP | Density-08 | $250 | $750 | 2 |
| FT4 shear cell and wall friction | Powder-04 | $650 | $1,950 | 3, 8 |
| DVS, salt only | Vapor-01 | $890 | $890 | 6 |
| **Total** | | | **$4,115** | |

- List prices at normal priority, about 7 business days after the samples arrive. Add shipping,
  $80 to get the powder back, and 10 % for an A2LA report.
- Why PTA: it is the only US commercial lab with published per-test prices, and one shipment covers
  four checks. Its angle of repose plus bulk and tap density ($425) cost less than the Carr set at
  Measurlabs.
- Add BaCl₂·2H₂O to the DVS ($890) if test 6 needs a hydrate.

### Step 3: quotes for the rest, once the tier 2–3 fixtures exist

| Check | Ask | Checks test |
|---|---|---|
| Hall, Carney, B212 and B527 on AlSi10Mg in an accredited lab | LTI or NSL | 5, 2 |
| Shear and wall friction at the lowest stresses, on a PLA coupon | Jenike & Johanson | 3, 8 |
| Rotating drum; uniaxial strength | Mercury Scientific (Revolution, Evolution UYS); Granutools | 7, 8 |
| Smallest orifice that flows | PTL | 5 |
| Charge per mass | Fauske or DEKRA | 10 |
| Spreading | BYU CREATE lab, as a collaboration | 9 |

### Cost and time

| | Cost | Calendar |
|---|---|---|
| Step 1, Utah labs (kits not counted) | about $540–1,060 | weeks 1–3 |
| Step 2, PTA | $4,115 plus shipping | weeks 1–4 |
| **Steps 1 and 2** | **about $4,650–5,200** | **4–5 weeks** |
| Step 3 | quotes needed | 3–6 more weeks |

Week 1 goes on emails, a BYU purchase order for PTA, the U of U off-campus work authorization and
the SDSs. The timing after that comes from the labs' stated turnarounds.

### What to ask when booking

- **PTA.** How much powder each test needs (the price list doesn't say). The lowest consolidation
  stress the FT4 shear cell can run, since the doser works at tens to hundreds of Pa. The
  wall-friction coupon (material, roughness), and whether they can test ours (printed PLA, or the
  steel of test 3). The angle-of-repose method (ISO 4324 or USP <1174>) and base size. For USP
  <616>, the tapper's drop height and the volume at each tap count, so the whole curve compares
  with test 2. RH and temperature during each test.
- **PSSC.** Whether the dry disperser takes fine aluminium and silicon powders. Whether outside
  users can be trained to run it (the $5.10 rate needs 5 h of use in 2 months).
- **MCL.** Whether hydrates (BaCl₂·2H₂O) and hydrocolloids lose water under the helium purge.

## The labs

### At BYU (Provo)

Nothing at BYU was found for angle of repose, Hall/Carney flow, tap density, shear cells, the FT4,
drums, Flodex, DVS or Faraday cups. Physics and the Integrated Microfabrication Lab could not be
checked.

#### BYU Electron Microscopy Facility

- **Where:** A104 Eyring Science Center.
- **Tests:** SEM imaging on the Apreo, Verios and Helios SEM/FIB. It gives images only; we would
  measure the grains ourselves (ISO 13322-1 style).
- **Price:** BYU users $30/h (the first rate column, read as CMS, Engineering and Life Sciences)
  or $80/h (other BYU users, Apreo or Verios). Non-BYU users $105/h, plus $300/h if staff run it.
  Sputter coater $10 a run. The page is undated (©2026).
- **Turnaround, sample size:** not stated.
- **How:** trained users book in Calira. The PI first requests a billing project
  ([form](https://microscopy.byu.edu/new-or-edit-cm-project-form)). emlab@byu.edu, 801-422-9953.
- **Confidence:** verified on the [rates page](https://microscopy.byu.edu/services). The column
  headings are garbled in the page text, so confirm which BYU rate applies.

#### BYU Environmental Analytical Lab (Plant & Wildlife Sciences)

- **Where:** 4105 Life Sciences Building. Open to the public.
- **Tests:** soil sand fractions by sieving (1–2, 0.5–1, 0.25–0.5, 0.1–0.25 and 0.05–0.1 mm),
  $30 a sample. "% Moisture or solids as received", $8. Plus $4 preparation a sample; 25 % off for
  20 or more samples.
- **Turnaround:** 4–5 business days for small orders (notice of 15 Sep 2026); the FAQ says 5–7.
- **Sample:** one pint of soil; "For other materials ... please call".
- **How:** [submission form](https://pws.byu.edu/eal/sample-submission), eal@byu.edu.
- **Confidence:** verified on the [price list](https://pws.byu.edu/eal/price-lists). These are soil
  methods, not ASTM B214 or USP <731>. Ask whether they take other powders.

#### CREATE Lab (Mechanical Engineering)

- **Equipment:** a Concept Laser M2 powder-bed fusion machine (running 316L), an ExOne Innovent+
  binder jet, and a custom binder jet with automated powder handling. Its projects include
  powder-bed density monitoring and prewetting of spread powder.
- **For us:** a collaboration for test 9 (spreading) and for 316L. No service is offered and no
  powder test instruments are listed.
- **Confidence:** verified on the [equipment page](https://am.byu.edu/equipment), which names the
  contact.

#### Civil & Construction Engineering labs

Lists "Scales, weights, and sieves", "Specific gravity testing equipment", a triaxial shear
apparatus, "Soil friction testing equipment" and SEM, with no makes or models. Soil-scale methods;
collaboration only. Verified on the
[department page](https://cce.byu.edu/structural-geotechnical-materials-and-construction-research).

#### Chemical & Biological Engineering catalysis labs

The [catalysis page](https://cbe.byu.edu/Research/catalysis) lists BET and chemisorption. BYU
theses name a Micromeritics TriStar II and TriStar 3000 (inferred from search snippets).
Collaboration only.

#### ACERC combustion lab (old page)

A BYU page from about 2010–2011 lists "A Quantachrome helium micropycnometer" and "A Micromeritics
surface area analyzer". Its PI is now listed as retired, so the instruments may be gone
([page](http://acerc.byu.edu/Emily/Laboratories/laboratories.html)). Not verified as current.

#### Geological Sciences, Mineral Surface Chemistry Lab

"A surface-area analyzer", model not stated. Collaboration only. Verified on the
[facilities page](https://geology.byu.edu/research-facilities).

#### Chemistry & Biochemistry

The department lists "particle size analyzers" with no make, model or technique
([page](https://chem.byu.edu/department/research-facilities-and-instruments)). Not confirmed to be
laser diffraction.

### University of Utah (Salt Lake City, about an hour's drive)

Nothing at the U of U was found for angle of repose, sieving, shear cells, the FT4, drums, Flodex,
DVS or charge. One reading found that the Metal 3D Printing core (an Aconity MIDI) gives university
users priority, and that the College of Pharmacy lists no powder instruments (not rechecked).

#### EARTH Core Facility, Particle Size and Characterization Lab (PSSC)

- **Where:** Sutton Building room 205, Geology & Geophysics.
- **Tests:** laser diffraction on a Sympatec HELOS/KF, from just below 1 µm to 1600 µm, dry
  (RODOS/L) or wet (CUVETTE). Dynamic image analysis on a QICPIC, 3 µm to about 5 mm, with aspect
  ratio and sphericity; priced as wet dispersions only.
- **Price for BYU** (the "Non UofU Research" tier, which includes a 54 % surcharge), per sample,
  lab-assisted / trained: dry $9.10 / $5.10; wet $18.30 / $10.30; QICPIC $19.80 / $11.80. Plus a
  $64.40 cleaning fee per job, which also sets the minimum charge. For work after 1 Sep 2026.
  "Trained" means 5 or more hours of use in 2 months.
- **Turnaround, sample size:** not stated. Listed sample types include soils, powdered rocks, ash
  and coffee.
- **How:** email first; the lab does not follow up on billing forms sent without an email. The
  [contact page](https://earth.utah.edu/research_facilities/earth-core-facility/pssc/contact.php)
  names the manager.
- **Confidence:** verified on the
  [pricing](https://earth.utah.edu/research_facilities/earth-core-facility/pssc/pricing.php) and
  [instrument](https://earth.utah.edu/research_facilities/earth-core-facility/pssc/instrumentation.php)
  pages. No sieves. Whether it takes fine metal powders is not stated.

#### Materials Characterization Lab (MCL), Materials Science & Engineering

- **Where:** MCE 1325, 110 Central Campus Dr.
- **Off-campus rates per hour** (on-campus in parentheses), as of 5 Jul 2026, with a 15-minute
  minimum:

  | Instrument | Test | Rate |
  |---|---|---|
  | Anton Paar Ultrapyc 5000 | He pycnometry | $56 ($28) |
  | Micromeritics 3Flex | BET | $48 ($24), plus degasser $2 |
  | Metrohm 917 | Karl Fischer moisture | $106 ($53) |
  | TA Instruments SDT 650 | TGA mass loss | $66 ($33) |
  | Hitachi TM3030Plus with EDS | Tabletop SEM | $60 ($30) |
  | Operator | Assistance | $88 ($44) |

  A Beckman Coulter LS230 (wet laser diffraction) has an equipment page but no rate.
- **Turnaround:** mail-in, "We aim for a 2-3 week turnaround time". Student technicians run
  projects of fewer than 10 tests a month; for larger ones, contact the staff first.
- **How:** off-campus work authorization, then mail the samples with a typed sample list and SDSs
  ([process](https://mcl.mse.utah.edu/about/how-it-works/)). characterization.uofu@gmail.com.
- **Confidence:** verified on the [rates page](https://mcl.mse.utah.edu/lab-rates/). The same page
  says off-campus rates "will be double what is posted above", which is unclear. The university's
  billing table showed $43.12/h for pycnometry at an off-campus academic rate (read once, not
  rechecked). Confirm the rate before booking.

#### Utah Nanofab Electron Microscopy and Surface Analysis Lab (EMSAL)

- **Where:** SMBB room 2500, 36 S Wasatch Dr.
- **Tests:** "Automated particle morphology and elemental analysis using EDS" on the Quanta 600F
  ESEM and the Helios dbFIB.
- **Price** (off-campus academic, from 1 Jan 2026): Quanta 600F $69.30/h, JEOL IT200 $53.90/h.
  Professional tech support $110.88/h. A one-time $41.58 setup. Coating $43.12 a sample.
- **How:** off-campus work authorization, then the lab manager named on the private-companies page.
- **Confidence:** verified on the [particle analysis page](https://emsal.nanofab.utah.edu/particle-analysis/)
  and the [rates page](https://emsal.nanofab.utah.edu/?p=3368).

#### Crus Center, Materials Science & Engineering

A Hitachi S-4800 FESEM at $60/h on campus and $120/h commercial, and an MLA 650F automated
mineralogy SEM at $92/h commercial, as of 5 Jul 2026. Nothing else for powders. Verified on the
[rates page](https://cruscenter.mse.utah.edu/equipment-rates/).

#### Powder metallurgy group (Zak Fang)

The [group page](https://powder.metallurgy.utah.edu/facilities/index.php) lists "Flowability, BET,
Tap Density, Apparent Density, Particle Size Analyzer", a Micromeritics AccuPyc II 1340
pycnometer and a SALD-2300 particle size analyzer. The flowability instrument isn't named, so a
Hall funnel isn't confirmed. No outside service is stated, so this would be a collaboration.

### Elsewhere in Utah

No Utah company was found that sells powder flow testing (angle of repose, Hall flow, shear cells).

#### Utah State University Microscopy Core (Logan)

SEM (Quanta FEG 650 with EDS and EBSD) at $340/h for non-USU users, run by the facility manager,
with a 1 h minimum, from 1 Jul 2026. Verified on the
[rates page](https://research.usu.edu/microscopy/instrument-rates). It costs more than BYU's own SEM.

#### Utah State University Analytical Laboratories (Logan)

Soil sand sieving at $15 a 100 g sample plus $5 preparation; moisture $5. Undated, "Prices Subject
to Change Without Notice". Soil methods. Verified on the
[price list](https://www.usu.edu/analytical-laboratories/price-lists.php).

#### Utah State University Food Process Lab (Logan)

Water activity, open to "others with permission"; no fee stated. Verified on the
[lab page](https://qanr.usu.edu/facilities/food-process-lab.php).

#### Weber State University, College of Science Instrumentation (Ogden)

An SEM (Quanta 250 ESEM with EDS) and a TGA, each $60/h for outside academics and $100/h for
industry. No particle size or surface area instruments. Verified on the
[instrumentation page](https://www.weber.edu/science/instrumentation.html).

#### FLSmidth Minerals Testing & Research Center (Midvale)

- A commercial minerals lab. A Nov 2023
  [datasheet](https://prod.flsmidth.com/globalassets/frontify/2025/1/wemco_attritiontestingprograms_datasheet_en.pdf)
  prices an as-received size distribution at $150 (0.5 kg), bulk density at $50 and specific gravity
  at $50.
- A June 2024
  [brochure](https://prod.flsmidth.com/globalassets/frontify/2024/9/mtrc_mineralstestingresearchcenter_brochure_en.pdf)
  lists wet and dry sieves from 4 in to 10 µm, Malvern sizing and SEM-EDS.
- The datasheet adds that tests are "performed to ASTM standards" but the lab "is not a certified
  laboratory".
- It works mostly on ores, so ask whether it takes small powder jobs. Lab.SLC@FLSmidth.com.
  Verified from the company's PDFs.

#### Utah Department of Agriculture and Food laboratory

Water activity $22 and moisture $28 a sample, under the cannabis and hemp programs (fee schedule
updated 1 Jul 2026). Whether it takes other samples is not stated
([fee schedule](https://ag.utah.gov/administrative-services/fee-schedule/)).

Unverified Utah leads: Advanced Laboratories Inc. in Salt Lake City (an old price list showed bulk
density at $25; current status unknown) and IGES, a geotechnical lab (sieving likely, no test list
posted).

### Send-out labs with published prices

#### Micromeritics Particle Testing Authority (PTA), Norcross GA

- **Prices**, per sample, from the [price list](https://micromeritics.com/pta-price-list) (dated only
  "Copyright 2025"):

  | Test | Code | Price |
  |---|---|---|
  | Angle of repose | Powder-09 | $175 |
  | Bulk and tap density, USP (bulk only $178) | Density-08 | $250 |
  | Dry or wet sieving, Ro-Tap | PSA-14 | $275 |
  | Laser diffraction, Mastersizer, dry or wet, ISO 13320 | PSA-03, PSA-04 | $385 |
  | Static image analysis, size and shape | Morph-01 | $650 |
  | FT4 shear cell and wall friction, with report | Powder-04 | $650 |
  | FT4 dynamic flow: flowability, aeration, consolidation | Powder-02 | $750 |
  | FT4, every test | Powder-01 | $1,595 |
  | Any one FT4 test, no report | Powder-05 | $315 |
  | DVS vapor isotherm | Vapor-01 | $890 |
  | Percent heat loss (moisture) | PTA-104 | $150 |
  | He or N₂ pycnometry, ISO 12154 | Density-01 | $185 |
  | BET, N₂ multipoint, ISO 9277 | Physi-01 | $335 |

- **Not listed:** Hall/Carney, Flodex, uniaxial strength. SEM size and shape are sent out ("Call").
- **Turnaround:** "Typically within 7 business days". Priority 2–4 days (+50 %); rush (+200 %).
- **Extras:** $80 to return samples in the US; +10 % for cGMP, GLP or A2LA reports; no volume
  discount. Sample amounts are not stated.
- **How:** the [contact page](https://micromeritics.com/contact-us/).
- **Confidence:** verified on the price list on 28 Nov 2026.

#### Measurlabs (Helsinki, a network of partner labs)

- **Prices** per sample, excluding VAT, plus €97 an order:
  - ASTM D6393 Carr indices on a Hosokawa Powder Tester: €662–850, 3 weeks, 400 mL. Covers angle
    of repose, aerated and packed bulk density, compressibility, spatula angle and cohesiveness
    ([page](https://measurlabs.com/products/powder-flowability-measurement--astm-d6393)).
  - He pycnometry, ISO 12154: €131–359, 3 weeks, 1 g.
  - BET: €141–243.
  - Dry laser diffraction, ISO 13320: €72–287, 2 weeks.
  - SEM particle size: €571–921, 4 weeks.
  - Image analysis of size and shape: €278–399, 2 weeks.
- **Not found:** Hall/Carney, ISO 4324, shear cells or the FT4.
- **Confidence:** verified on the product pages. The D6393 and pycnometry pages were read twice;
  the others once.

### Send-out labs, quote only

#### Particle Technology Labs (PTL), Downers Grove IL

- **Tests:**
  - Flow:
    - The FT4.
    - Shear cell and wall friction on an Anton Paar MCR 302e.
    - "classic flowability approaches for angle of repose, tap density, bulk density, and flow
      through an orifice". It is the only lab found that names orifice flow; Flodex is not named.
  - Density: true density (AccuPyc II, UltraPyc 5000) and bulk and tapped density (Autotap).
  - Size and shape: laser diffraction (Mastersizer 3000, Sympatec HELOS) and static image analysis
    (Morphologi 4-ID).
  - Surface and moisture: BET on five instruments, and DVS on a ProUmid Vsorp Plus ("typically in
    3-5 days").
- **Sample:** FT4 work 1–1.5 L ideal, 450 mL minimum; laser diffraction 5–10 g; image analysis
  1 g; BET 2–5 g; DVS 1–100 g.
- **How:** [quote form](https://particletechlabs.com/quote-request-form/), 630-969-2703.
  ISO/IEC 17025 accredited (site footer).
- **Confidence:** verified on the
  [flowability](https://particletechlabs.com/analytical-testing/powder-flowability/) and other
  service pages.

#### Jenike & Johanson, Tyngsboro MA

- **Tests:** flow properties on a ring shear tester (cohesive strength, internal and wall friction,
  compressibility), angle of repose, and loose and tapped density. The lab pages don't name the
  tester. J&J is the Americas distributor of Schulze ring shear testers, so it is probably ASTM
  D6773 (inferred).
- **Price:** "The cost for testing a sample depends greatly on the type, number, and complexity of
  tests requested"; budgetary quotes on request.
- **Turnaround:** "within two to three weeks".
- **Sample:** 20 L for bench-scale tests; about 1.5 L for a pharmaceutical suite; as little as
  50 g for scarce material. An SDS and a Sample Return Form must arrive before testing starts.
- **How:** [consult an engineer](https://jenike.com/consult-an-engineer/), info@jenike.com.
- **Confidence:** verified on the [tests page](https://jenike.com/services/flow-properties), the
  [FAQ](https://jenike.com/knowledge-base/frequently-asked-question/) and the
  [sample page](https://jenike.com/sending-samples-to-jenike-johanson-usa-laboratories/). The best
  place to ask about stresses below 1 kPa and a PLA wall coupon.

#### Kansas State University Olathe, Bulk Solids Technology Center

- **Equipment:**
  - Shear testers: a Brookfield PFT and an FT4 (shear, wall friction, time consolidation).
  - A Hosokawa PT-X powder tester (angles of repose, Carr-type indices).
  - An UltraPyc 1200e pycnometer.
  - Ro-Tap and air-jet sieves.
  - A Morphologi G3 SE and an SEM.
  - VSA moisture sorption and humidity chambers.
- **Price, turnaround and sample size** are not stated.
- **How:** bulksolids@ksu.edu, 913-307-7314.
- **Confidence:** verified on the
  [test-lab page](https://olathe.k-state.edu/research/advanced-manufacturing-bulk-solids-technology-center/test-lab-powder-bulk-solid-material-testing-services/index.html)
  (updated 30 Jun 2026).

#### NSL Analytical, Cleveland OH

- **Tests:**
  - Flow: Hall (B213), Carney (B964) and an avalanche drum.
  - Density: apparent (B212, B417), tap (B527), bulk (D7481) and skeletal (B923).
  - Size: laser diffraction (ISO 13320, B822; Mastersizer 3000) and sieving (B214).
  - Also BET (B922) and SEM.
- **Turnaround:** "quick turnaround times", no number.
- **How:** [quote form](https://www.nslanalytical.com/contact/materials-testing-quote).
- **Confidence:** verified on the
  [service page](https://www.nslanalytical.com/testing-services/powder-characterization-services).

#### Laboratory Testing Inc. (LTI), Hatfield PA

- **Tests:** the widest metal-powder menu found.
  - Flow: Hall (B213, ISO 4490) and Carney (B964).
  - Density: apparent by Hall, Scott volumeter and Carney (B212, B329, B417); tap (B527, ISO 3953);
    skeletal (B923).
  - Size and shape: laser diffraction and dynamic image analysis on a Microtrac SYNC (B822,
    ISO 13322-2); sieving (B214, 20–800 µm).
  - Also BET (B922). Avalanche drum and SEM shape are "Informational purposes only".
- **How:** [quote form](https://labtesting.com/quote/).
- **Confidence:** verified on the
  [service page](https://www.labtesting.com/metal-powder-characterization/).

#### IMR Test Labs (Lansing NY)

Hall and Carney (B213, B964 per its FAQ), apparent and tap density, Microtrac laser diffraction,
sieving and He pycnometry. The powder site isn't stated. Quote via
[request form](https://imrtest.com/request-quote/). Verified ([page](https://imrtest.com/?p=2652)).

#### Westmoreland Mechanical Testing & Research (Pennsylvania)

Hall and Carney (B213, B964), apparent and tap density (B212, B417, B527), sieving (B214), laser
diffraction (B822). Seen in #190 on 28 Oct 2026; a bot check blocked a recheck
([page](https://wmtr.com/Powder-Characterization.HTML)).

#### EWI (Columbus OH)

He pycnometry, a Hall funnel and 25 cm³ cup (B213, B212), laser diffraction on a Beckman Coulter
LS 13 320 (B822) and SEM, per a [2021 brochure](https://ewi.org/wp-content/uploads/2021/01/METAL-POWDER-EVAL-FOR-AM.pdf)
(read once; its text did not extract on a recheck). Quote: info@ewi.org.

#### Element Materials Technology

Apparent, tap and skeletal density, sieving, shape and "Flow rate and powder behavior analysis",
under ISO/ASTM 52907, with no ASTM B numbers. Quote. Verified on the
[service page](https://www.element.com/materials-testing-services/additive-manufacturing-testing/powder-characterization-services).

#### Covalent (Sunnyvale CA)

Tap density per USP <616>, ASTM B527 and ISO 3953 on an Anton Paar Dual AutoTap, with Hausner
ratio and Carr index, "typically 5-7 business days" (read once, not rechecked). Also gas pycnometry, BET and
laser diffraction. The [quote form](https://covalent.com/get-a-quote/) lists these techniques.

#### Hosokawa Micron Powder Systems test center (Summit NJ)

Its [equipment page](https://www.hmicronpowder.com/applications/laboratory-equipment-and-particle-analysis/)
lists "Powder characteristics testing" and a Micron Powder Characteristics Tester, and says "Most of
the above options are available for testing and evaluation in our Summit, New Jersey Facility".
That the tester (PT-X) measures angle of repose and Carr indices was read once on its product page,
not rechecked. Quote: 908-273-6360.

#### Other contract labs

- **Intertek:** Hall flow (B213, B964), densities and sieving, from a search snippet; the site
  returned 403. Not verified.
- **Applied Technical Services (Marietta GA):** laser diffraction per ASTM B822 (#190). Quote.
- **Carpenter Additive (Athens AL):** an A2LA scope that expired on 31 Mar 2025 lists B822, B214,
  B213, B212, B417, B964 and B527. Testing for outside customers is not confirmed.
- **Eurofins EAG:** laser diffractometry (0.02–2000 µm), air-jet sieving and automated SEM image
  analysis. Quote.
- **"Solids Handling labs":** nothing found under that name. The bulk-solids labs found are J&J,
  K-State Olathe, Material Flow Solutions and Hosokawa. Equipment makers' test centers (Coperion,
  Schenck) run process trials, not flow-property tests (read once, not rechecked).

### Instrument makers' labs

The free demos are meant to sell instruments. They are useful as a second opinion, not as the
reference.

- **Mercury Scientific (Connecticut).** Paid packages on the
  [testing page](https://www.mercuryscientific.com/testing-services):
  - the Revolution rotating drum (drums take 10–500 cm³ of sample);
  - the Evolution UYS, which measures "unconfined yield strength" and a flow function in a
    "3 minute test".
  - Quote, with discounts above five samples. info@mercuryscientific.com.
  - A SpreadStation spreading analyzer is on its instrument menu but is not a test package: ask.
- **Granutools (Awans, Belgium).** Its [measurement service](https://www.granutools.com/en/measurements)
  runs in Belgium:
  - the GranuDrum, for which ASTM D8648-25 ("Standard Test Method for Determining Flowability Using
    GranuDrum") is the published method;
  - the GranuCharge, which drops powder from a vibrating tube into "a customized Faraday cup"
    (typically 50 mL);
  - tapped density.
  - You get a report with raw data and a 2-hour call. Quote.
- **Anton Paar QuantaTec (Boynton Beach FL).** BET, true and tapped density, and pre-purchase
  testing, from search excerpts only (the site returned 403). Not verified.
- **AMETEK Brookfield (Middleboro MA).** Trade press from 2012 and 2014 said the first three Powder
  Flow Tester samples were free and reported "within five business days". Its current site doesn't
  mention this, so ask whether it still runs. Not verified.
- **Retsch, via Verder Scientific (Newtown PA).** "free test sieving of your sample in our
  application laboratory": send a questionnaire, the sample and the SDS to the dealer
  ([page](https://www.retsch.com/applications/application-laboratory/questionnaire-sieving/)).
- **Microtrac.** Will "analyze your samples at no cost" on the CAMSIZER (dynamic image analysis) or
  SYNC, in labs in Germany, France, the USA and Japan
  ([page](https://www.microtrac.com/applications/application-laboratory/)).
- **Sympatec (Pennington NJ).** A "free of charge taster analysis" by laser diffraction or QICPIC,
  the same instruments as the U of U PSSC
  ([page](https://sympatec.com/en/in-good-hands/taster-analysis)).
- **HORIBA.** "complimentary sample analysis" with a formal lab report
  ([page](https://www.horiba.com/usa/scientific/products/particle-characterization/sample-analysis-by-application-experts/)).
- **Not offering tests:** Malvern Panalytical (Morphologi demo or quote only), Teledyne Hanson
  (Flodex) and Copley (read once, not rechecked).

### Sorption, charge, strength and spreading specialists

- **Surface Measurement Systems.** A DVS contract lab in London, with a North America office in
  Allentown PA. Quote. Verified
  ([page](https://surfacemeasurementsystems.com/contract-sorption-services/)).
- **ProUmid (Ulm), Hiden Isochema (UK), AQUALAB.** Vapor sorption contract analysis. Quote. Verified
  on their service pages (see `labs.csv`).
- **Fauske & Associates (Burr Ridge IL).** The closest match to test 10. Its "Powder Chargeability
  test" pours powder "down an inclined section of pipe" into "a Faraday cup", read with a coulomb
  meter. It also measures resistivity (ASTM D257) and charge decay. Quote: dust@fauske.com. Verified
  ([page](https://www.fauske.com/testing/combustible-dust-hazard-analysis)).
- **DEKRA Process Safety.** Measures powder chargeability "in general accordance with ASTM D4470"
  through steel, plastic or glass tubes, at ambient and low RH. Also volume resistivity and charge
  relaxation. Quote. Verified ([page](https://dekra.us/en/process-safety-tests)).
- **Material Flow Solutions (Gainesville FL).** An SSSpinTester-X for unconfined yield strength on
  samples "as small as 0.05 gram". From a trade directory; its own site was behind a bot check. Not
  verified.
- **Natoli Scientific (PA and MO).** Pharma listings name USP <616>, angle of repose, USP <1174>
  flow, the FT4, He pycnometry and sieving. Its own home page names no methods. Not verified.
- **Schwedes + Schulze (Germany).** Ring shear testing: flow function, wall friction and time
  consolidation. Whether it takes US samples is not stated.
- **Wolfson Centre, University of Greenwich (UK).** A spreadability instrument, used for
  consultancy (read once, not rechecked).
- **FILAB (France)** and **Purdue's MMRL** have Granutools drums. FILAB quotes within 24–48 h;
  Purdue doesn't say whether it takes outside samples.

## Gaps

- **Searches stopped early.** The web-search budget for this survey ran out at about 08:50 UTC
  on 28 Nov, so later checks were fetches of known pages. Not searched:
  - at BYU: Physics (electrometers), laser diffraction in Geological Sciences, DVS and Flodex;
  - papers by U of U and USU authors that name their instruments;
  - Utah pharmaceutical and supplement labs (USP <616>, <731>).
- **Quotes needed.** No published prices for Hall/Carney, drums, Flodex, uniaxial strength, charge
  or spreading. PTA doesn't state sample amounts.
- **To confirm by email:**
  - which BYU EM rate applies to us;
  - the MCL's off-campus academic rate ($56 posted, $43.12 in the billing table);
  - whether the PSSC disperses fine metal powders dry.
- **Read once, not rechecked:**
  - Covalent's tap-density details and the PT-X's measured properties at Hosokawa;
  - EWI's brochure and Mercury's SpreadStation;
  - the Wolfson Centre and FILAB pages;
  - the Nanofab industry rate and the Crus Center academic rate.
- **Not verified:** Brookfield's free testing, Anton Paar QuantaTec, Intertek, Carpenter's outside
  testing, Material Flow Solutions and Natoli.

Earlier costs and the in-house kit prices: #190,
[`README.md`](https://github.com/vertical-cloud-lab/powder-doser/blob/1e0d6f8/docs/powder-tests/README.md)
and [`costs.csv`](https://github.com/vertical-cloud-lab/powder-doser/blob/1e0d6f8/docs/powder-tests/costs.csv).
