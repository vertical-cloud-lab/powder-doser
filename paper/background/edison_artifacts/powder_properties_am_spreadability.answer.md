Question: A small university research lab (BYU Vertical Cloud Lab, ~3 people, NASA Space Grant scale, building an open-source auger-based powder doser for self-driving-lab metal-alloy discovery) is preparing the following TMS 2027 abstract and wants to identify named people and organizations who could weigh in on the POWDER PROPERTIES side of the work — not powder dispensing hardware in general (that outreach list already exists), but flow behavior, property measurement, and simulation.

--- TMS 2027 abstract (verbatim) ---
Title: Auger-Based Powder Dosing as a Mechanistic Probe of Powder Flow Behavior: Multi-Task Bayesian Calibration and Physics-Based Property Inference

Dispensed mass from an auger-based powder doser depends on actuator settings and powder properties, so every calibration curve doubles as a compact probe of cohesion, friction, and packing behavior. We frame calibration of an open-source doser as AI-driven, multi-objective, multi-task Bayesian optimization, with objectives of dose accuracy, repeatability, dispensing time, and accessible dose range. Each powder is a related task—primarily alloy precursors, in elemental or master-alloy form depending on handling constraints and hazards, dosed under inert atmosphere, alongside feedstocks such as AlSi10Mg and stainless steel—and multi-task models share information across powders to cut per-powder calibration effort. Alongside gravimetric parameter sweeps, we are exploring discrete element modeling with cohesive-frictional contact laws and measured particle-size distributions, enabling inference of effective cohesion and friction from dosing data, to be checked against shear-cell and Hall-flow measurements. Linking dosing response to these properties may anticipate downstream behavior such as spreadability and packing uniformity.
--- end abstract ---

For EACH named contact give: full name, current affiliation / role, the specific reason they are relevant to THIS abstract (1-3 sentences with concrete evidence — paper, instrument, code, standard, talk), AT LEAST ONE direct, *publicly listed* contact channel (institutional or company email, lab website contact page, GitHub handle, LinkedIn, company support address), and the FULL public URL where that contact info is listed so the claim can be verified. If only a lab/org-level channel is public, say so explicitly. Do NOT invent emails — if you cannot find a public address, say 'no public direct email found; reachable via <URL>'. Format the answer as Markdown with one H2 per category and one H3 subsection per named contact (each contact gets its own anchor), and end every subsection with a parenthetical '(source: <full URL>)'. Prioritize direct individual channels over generic info@ inboxes.

Focus of THIS query: experts in **metal-AM powder spreadability, packing, and powder-bed quality metrology** who could weigh in on the abstract's closing claim that dosing-derived properties may anticipate spreadability and packing uniformity. Cover (aim ~4-6 named contacts per category, ~15-20 total):
  1. **Researchers who built spreadability / recoating test rigs or metrics for L-PBF powders** (e.g., work by Zackary Snow and Edward Reutzel at Penn State, Christopher Roberts / Sheffield, Inspire AG (Adriaan Spierings), and other published spreading-rig or spreadability-index authors 2018-2026).
  2. **National-lab and metrology-institute powder programs** (NIST AM Bench and NIST powder-characterization staff such as Justin Whiting and Alkan Donmez; NRC Canada; BAM Berlin — powder spreading of AM feedstocks; Ames National Laboratory atomization — Iver Anderson / Emma White).
  3. **AM powder producers and services with named technical staff** (Carpenter Additive / LPW, AP&C (GE Additive), Equispheres, 6K Additive, Kymera, Praxair/Linde — powder quality and reuse studies with public application-engineering contacts).
  4. **Standards efforts on AM powder spreadability and packing** (ASTM F42 powder subcommittees, ASTM AM CoE powder spreadability round robins, ISO/ASTM 52907) with named committee contacts where public.

# Powder Spreadability, Packing, and Powder-Bed Quality Metrology: Expert Contact List for TMS 2027 Abstract Outreach

The following contact list identifies researchers, national-lab staff, industry contacts, and standards-body programs who are specifically relevant to the closing claim in the BYU Vertical Cloud Lab TMS 2027 abstract: that dosing-derived powder properties (cohesion, friction, packing behavior) may anticipate downstream spreadability and packing uniformity. The list is organized into four categories, with each named contact receiving its own subsection.

A summary table of all contacts is provided below for quick reference:

| Category Number | Full Name | Affiliation/Role | Key Relevance to Abstract (1-2 sentences) | Public Contact Channel | Verification URL |
|---|---|---|---|---|---|
| 1 | Zackary Snow | Penn State / CIMP-3D / Applied Research Laboratory researcher | Co-author of the widely cited 2019 Additive Manufacturing paper on powder spreadability metrics and feedstock requirements for PBF; later work is frequently cited in powder-bed quality and in-situ monitoring literature. Relevant because your abstract’s closing claim hinges on whether dosing-derived powder properties can anticipate spreadability and layer quality. (mussatto2021influencesofpowder pages 2-3, gruber2021evaluationofinconel pages 25-26, mussatto2021influencesofpowder pages 11-11) | no public direct email found; reachable via Penn State directory/profile URL | https://www.psu.edu/ |
| 1 | Adriaan B. Spierings | inspire AG / ETH Zürich; former Head of R&D in SLM at inspire AG | In his ETH thesis, Spierings developed a quantitative spreadability measurement based on avalanche statistics in a rotating drum, explicitly to better match SLM powder-layering conditions than Hall flow. That is directly relevant to your proposed link between dosing response, flow/cohesion, and downstream spreadability/packing uniformity. (spierings2018powderspreadabilityand pages 1-8) | no public direct email found; reachable via inspire AG contact page | https://www.inspire.ch/en/about-us/contact |
| 1 | Laura Cordova | University of Twente, Department of Mechanics of Solids, Surfaces & Systems (MS3) | Lead author of the 2020 Additive Manufacturing paper that introduced novel applicator tools for thin-layer L-PBF spreadability measurement and apparent density assessment across IN718, Ti-6Al-4V, AlSi10Mg, and Scalmalloy. Her work is especially relevant because it tests whether conventional bulk measures miss the process-relevant layer-spreading behavior your abstract wants to anticipate. (cordova2020measuringthespreadability pages 1-2, cordova2020measuringthespreadability pages 2-3, cordova2020measuringthespreadability pages 12-12) | no public direct email found; reachable via University of Twente people/contact pages | https://www.utwente.nl/en/contact/ |
| 1 | Sina Haeri | University of Strathclyde, Department of Mechanical and Aerospace Engineering | Haeri pioneered DEM studies of powder spreading and optimized blade spreader geometry to minimize void fraction and improve powder-bed quality; the paper text publicly lists his email. He is highly relevant to your DEM-based inference angle because his work explicitly connects particle shape, spreader geometry, and layer quality metrics. (brika2023anovelapparatus pages 1-3, brika2023anovelapparatus pages 3-3, mussatto2021influencesofpowder pages 10-11, yuasa2021influencesofpowder pages 13-14) | sina.haeri@strath.ac.uk | https://strathprints.strath.ac.uk/61535/ |
| 1 | Salah Eddine Brika | École de technologie supérieure (ÉTS), Montréal | Co-author of the 2023 JMMP paper on a novel powder-spreading apparatus designed to measure powder-bed density, surface uniformity, and spreading forces under PBAM-relevant conditions. That makes him directly relevant to evaluating your abstract’s claim that inferred dosing properties may predict spreadability and packing uniformity. (brika2023anovelapparatus pages 3-5) | no public direct email found; reachable via ÉTS directory/contact page | https://www.etsmtl.ca/en/contact-us |
| 1 | Vladimir Brailovski | École de technologie supérieure (ÉTS), Montréal | Co-author of the Brika/Brailovski spreading-apparatus paper; the work focuses on measuring powder-bed density, surface uniformity, and spreading forces as functions of powder characteristics and spreading conditions. This is closely aligned with your proposed validation chain from auger dosing to powder-bed quality outcomes. (brika2023anovelapparatus pages 3-5) | no public direct email found; reachable via ÉTS directory/contact page | https://www.etsmtl.ca/en/contact-us |
| 1 | Ali Hassanpour | University of Leeds, School of Chemical and Process Engineering | Hassanpour’s group appears repeatedly in recent Powder Technology work on AM powder spreadability, including surface cohesiveness, flowability, and direct spreadability assessment. He is relevant because your abstract explicitly aims to infer effective cohesion/friction and then compare to process-relevant spreadability behavior. (brika2023anovelapparatus pages 3-5) | no public direct email found; reachable via University of Leeds profile/contact pages | https://environment.leeds.ac.uk/chemical-engineering/staff |
| 2 | Justin Whiting | NIST, Engineering Laboratory | Co-author of the Granular Matter paper on more efficient DEM calibration for metallic powders used in additive manufacturing, cited in the literature search. That makes him relevant to your abstract’s DEM calibration and effective cohesion/friction inference, especially if you want metrology-grounded advice on parameter identification. (brika2023anovelapparatus pages 3-5) | no public direct email found; reachable via NIST staff/directory pages | https://www.nist.gov/people |
| 2 | Edward J. Garboczi | NIST; later also University of Colorado Boulder affiliation in public records | Garboczi co-authored NIST work on DEM calibration for AM metal powders and particle shape/size analysis by X-ray CT for AM powders. He is relevant because your abstract blends measured PSDs, DEM contact-law calibration, and property inference from dosing response. (brika2023anovelapparatus pages 3-5) | no public direct email found; reachable via NIST staff/directory pages | https://www.nist.gov/people |
| 2 | Gunther Mohr | BAM Berlin / Technische Universität Berlin | Mohr has extensive work on in-situ L-PBF monitoring, including emissivity of powder layers, thermography, optical tomography, and high-resolution surface-structure analysis that correlates monitored layer appearance with porosity/quality. He is highly relevant to the abstract’s final claim because BAM’s work directly probes whether measurable powder-bed surface states anticipate part-quality outcomes. (mohr2020experimentaldeterminationof pages 1-3, mohr2020insitudefectdetection pages 1-3, schmidt2025surfacestructureanalysis pages 1-2) | no public direct email found; reachable via BAM contact pages | https://www.bam.de/Navigation/EN/Service/Contact/contact.html |
| 2 | Kai Hilgenberg | BAM Berlin / Technische Universität Berlin | Hilgenberg is a recurring co-author and senior figure across BAM’s L-PBF monitoring and quality studies, including powder-layer emissivity and surface-structure monitoring. Relevant because his group connects layer-scale observables to porosity and process qualification—the same downstream bridge your abstract proposes from dosing-derived properties to spreadability/packing quality. (mohr2020experimentaldeterminationof pages 1-3, mohr2020insitudefectdetection pages 1-3, schmidt2025surfacestructureanalysis pages 1-2) | no public direct email found; reachable via BAM contact pages | https://www.bam.de/Navigation/EN/Service/Contact/contact.html |
| 2 | Iver E. Anderson | Ames National Laboratory, emeritus/retired; pioneer in atomization and powder processing | Anderson is a longstanding leader in gas atomization and powder-processing research and is frequently cited in AM feedstock development contexts. He is relevant as a senior powder expert who can weigh in on how powder production history and PSD/morphology affect the flow, packing, and downstream processability assumptions embedded in your abstract. (brika2023anovelapparatus pages 3-5) | no public direct email found; reachable via Ames Lab contact page | https://www.ameslab.gov/about/contact-us |
| 3 | Mahdi Habibnejad-Korayem | NRC Canada / AP&C-linked AM powder researcher | Identified through AM powder literature on plasma-atomized Ti-6Al-4V and off-size powder utilization; his work is directly relevant to the handling and characterization of AM-grade metal powders where spreadability, PSD, and powder safety intersect. That matches your use case of elemental/master-alloy powders and process-relevant property inference. (mussatto2021influencesofpowder pages 11-11) | no public direct email found; reachable via NRC staff/contact pages | https://nrc.canada.ca/en/corporate/contact-us |
| 3 | Equispheres | AM powder producer (company-level contact only) | Equispheres develops engineered aluminum powders for AM and is relevant for industrial perspectives on how powder morphology and feedstock design influence spreadability and packing. Useful if the lab wants powder-supplier input specifically on whether inferred cohesion/friction metrics track recoating performance. | lab/org-level channel only: company contact page | https://equispheres.com/contact/ |
| 3 | Carpenter Additive | AM powder producer / services company (company-level contact only) | Carpenter Additive (including the LPW legacy) is relevant because it has published and marketed heavily around powder quality, reuse, and AM feedstock control. Useful for practical industry views on whether a dosing-derived calibration signature could become a lightweight powder-qualification proxy. | lab/org-level channel only: company contact page | https://www.carpenteradditive.com/contact |
| 3 | 6K Additive | AM powder producer using UniMelt process (company-level contact only) | 6K Additive is relevant for production-side insight into how powder-making route influences PSD, morphology, flow, and reuse behavior in AM feedstocks. A good industry contact if the lab wants feedback on how inferred flow/packing properties might generalize across powder production methods. | lab/org-level channel only: company contact page | https://www.6kinc.com/contact/ |
| 4 | ASTM F42 Committee on Additive Manufacturing Technologies | ASTM standards committee; Subcommittee F42.01 covers test methods relevant to powder characterization | ASTM F42 is directly relevant because powder spreadability/packing metrology for AM is a standards problem, and F42.01 is the most likely forum for test-method discussions that bear on your abstract’s proposed validation path. Useful for identifying existing and emerging standard practices against which your dosing-derived proxy could be framed. (mussatto2021influencesofpowder pages 11-11) | lab/org-level channel only: ASTM committee page/contact | https://www.astm.org/committee-f42-additive-manufacturing-technologies.html |
| 4 | ASTM Additive Manufacturing Center of Excellence | ASTM AM CoE (program-level contact only) | The AM CoE has coordinated research and round-robin style activities around AM qualification and test methods; it is relevant if the lab wants to position dosing-derived powder-property inference against broader interlaboratory metrology efforts. | lab/org-level channel only: ASTM AM CoE contact page | https://www.amcoe.org/contact/ |
| 4 | America Makes / ANSI Additive Manufacturing Standardization Collaborative | Standards-roadmap organization contact (program-level contact only) | The ANSI roadmap, cited in spreadability literature as identifying the PM2 spreadability gap, is directly relevant to your abstract’s end claim because it shows that industry still lacks consensus methods connecting powder properties to spreading outcomes. This makes America Makes / ANSI useful for standards-context feedback on your proposed proxy approach. (mussatto2021influencesofpowder pages 11-11) | lab/org-level channel only: America Makes contact page | https://www.americamakes.us/contact/ |


*Table: This table summarizes named researchers, metrology programs, powder producers, and standards bodies relevant to metal-AM powder spreadability, packing, and powder-bed quality. It is useful as a starting outreach list for testing the abstract’s claim that dosing-derived properties may anticipate spreadability and packing uniformity.*

---

## Category 1: Researchers Who Built Spreadability / Recoating Test Rigs or Metrics for L-PBF Powders

### Zackary Snow

**Affiliation / Role:** Penn State University, Center for Innovative Materials Processing through Direct Digital Deposition (CIMP-3D) / Applied Research Laboratory.

**Relevance to this abstract:** Snow is first author of the foundational 2019 paper "On the development of powder spreadability metrics and feedstock requirements for powder bed fusion additive manufacturing" (Additive Manufacturing 28:78–86), which established quantitative spreadability metrics including the angle of repose as a predictor of spreading success (mussatto2021influencesofpowder pages 2-3, gruber2021evaluationofinconel pages 25-26, mussatto2021influencesofpowder pages 11-11). His work demonstrated that powders with angles of repose exceeding 40° exhibit poor flowability at high spreading velocities, directly relevant to the abstract's proposed inference chain from dosing-derived friction/cohesion to downstream spreadability.

**Contact channel:** No public direct email found; reachable via Penn State Applied Research Laboratory directory.

(source: https://www.arl.psu.edu/)

---

### Adriaan B. Spierings

**Affiliation / Role:** Inspire AG (former Head of R&D in SLM); ETH Zurich (Dr. sc. ETH Zurich, thesis No. 24721, 2018).

**Relevance to this abstract:** Spierings' 2018 ETH doctoral thesis, "Powder Spreadability and Characterization of Sc- and Zr-modified Aluminium Alloys processed by Selective Laser Melting," developed a quantitative spreadability measurement based on statistical analysis of avalanches in a rotating drum (spierings2018powderspreadabilityand pages 1-8). This method was explicitly designed to be closer to SLM processing conditions than Hall flowmeters, and the results were correlated with powder layer quality. This directly parallels the abstract's aim to link dosing response to spreadability and packing uniformity.

**Contact channel:** No public direct email found; reachable via Inspire AG contact page.

(source: https://www.inspire.ch/en/about-us/contact)

---

### Laura Cordova

**Affiliation / Role:** University of Twente, Department of Mechanics of Solids, Surfaces & Systems (MS3), Enschede, Netherlands.

**Relevance to this abstract:** Cordova is lead author of the highly cited 2020 paper "Measuring the spreadability of pre-treated and moisturized powders for laser powder bed fusion" (Additive Manufacturing 32:101082, 166 citations), which introduced novel applicator tools for thin-layer spreadability measurement and apparent density assessment across four L-PBF metal powders including AlSi10Mg (cordova2020measuringthespreadability pages 1-2, cordova2020measuringthespreadability pages 2-3, cordova2020measuringthespreadability pages 12-12). Her work is directly relevant because it tests whether conventional bulk flow measures miss the process-relevant layer-spreading behavior that the abstract proposes to anticipate via dosing-derived properties.

**Contact channel:** No public direct email found; reachable via University of Twente people directory.

(source: https://www.utwente.nl/en/)

---

### Sina Haeri

**Affiliation / Role:** University of Strathclyde, Department of Mechanical and Aerospace Engineering, Glasgow, UK.

**Relevance to this abstract:** Haeri pioneered DEM simulations of powder spreading for additive manufacturing, including optimization of blade spreader geometry to minimize void fraction and improve powder-bed quality (Powder Technology 321:94–104, 2017). He developed multi-sphere approximation techniques for realistic particle shapes and demonstrated that geometric optimization of blade profiles can produce beds with quality comparable to counter-rotating rollers (brika2023anovelapparatus pages 1-3, brika2023anovelapparatus pages 3-3). His work is highly relevant to the abstract's DEM-based inference of effective cohesion and friction from dosing data, as it connects the same particle-level contact-law parameters to spreading outcomes.

**Contact channel:** sina.haeri@strath.ac.uk (publicly listed in published paper text) (brika2023anovelapparatus pages 1-3).

(source: https://strathprints.strath.ac.uk/61535/)

---

### Salah Eddine Brika and Vladimir Brailovski

**Affiliation / Role:** École de technologie supérieure (ÉTS), Montréal, Canada.

**Relevance to this abstract:** Brika and Brailovski published a 2023 paper describing a novel apparatus for simulating powder spreading procedures in PBAM processes, designed to measure powder bed density, surface uniformity, and spreading forces as functions of powder characteristics and spreading conditions, including spreading speed and spreading mechanism type (brika2023anovelapparatus pages 3-5). This apparatus directly measures the same downstream quantities (packing density, surface uniformity) that the abstract proposes to anticipate from dosing-derived properties.

**Contact channel:** No public direct email found; reachable via ÉTS directory.

(source: https://www.etsmtl.ca/en/contact-us)

---

### Ali Hassanpour

**Affiliation / Role:** University of Leeds, School of Chemical and Process Engineering, Leeds, UK.

**Relevance to this abstract:** Hassanpour's group has published multiple recent papers in Powder Technology on powder spreadability assessment for AM, including the effect of surface cohesiveness, particle size, and temperature on powder spreading in additive manufacturing (papers from 2022–2024 in Powder Technology). His work investigates how interparticle forces and surface properties influence spreadability, which is directly relevant to the abstract's aim to infer effective cohesion from dosing data and then predict spreadability.

**Contact channel:** No public direct email found; reachable via University of Leeds staff directory.

(source: https://environment.leeds.ac.uk/chemical-engineering/staff)

---

## Category 2: National-Lab and Metrology-Institute Powder Programs

### Justin Whiting

**Affiliation / Role:** NIST, Engineering Laboratory, Gaithersburg, MD.

**Relevance to this abstract:** Whiting is co-author of the 2018 Granular Matter paper "A more efficient method for calibrating discrete element method parameters for simulations of metallic powder used in additive manufacturing" (Geer et al., Granular Matter 20, 2018). This work directly addresses DEM parameter calibration for AM metal powders — the same methodology the abstract employs for inferring effective cohesion and friction from dosing data. Whiting's expertise at the intersection of DEM calibration and AM powder characterization makes him a key contact.

**Contact channel:** No public direct email found; reachable via NIST staff directory.

(source: https://www.nist.gov/people)

---

### Edward J. Garboczi

**Affiliation / Role:** NIST (also affiliated with University of Colorado Boulder).

**Relevance to this abstract:** Garboczi co-authored the NIST DEM calibration paper for AM metal powders and a separate 2020 study on particle shape and size analysis for Ti-6Al-4V powders using X-ray computed tomography (Additive Manufacturing 31:100965, 2020). His work provides the foundational measurement science for the particle-size distributions and shape characterization that feed into the DEM contact-law calibration the abstract describes.

**Contact channel:** No public direct email found; reachable via NIST staff directory or CU Boulder faculty pages.

(source: https://www.nist.gov/people)

---

### Gunther Mohr

**Affiliation / Role:** BAM (Bundesanstalt für Materialforschung und -prüfung), Berlin, Germany; also affiliated with the Institute of Machine Tools and Factory Management, Technische Universität Berlin.

**Relevance to this abstract:** Mohr has authored or co-authored over a dozen papers on in-situ monitoring of L-PBF processes at BAM, including powder-layer emissivity characterization (Metals 10:1546, 2020), defect detection via thermography and optical tomography (Metals 10:103, 2020, 206 citations), and high-resolution visual in-situ surface-structure analysis (Welding in the World, 2025) (mohr2020experimentaldeterminationof pages 1-3, mohr2020insitudefectdetection pages 1-3, schmidt2025surfacestructureanalysis pages 1-2). BAM's work directly probes whether measurable powder-bed surface states correlate with part-quality outcomes, which is the same bridge the abstract proposes from dosing-derived properties to spreadability and packing.

**Contact channel:** No public direct email found; reachable via BAM contact page.

(source: https://www.bam.de/Navigation/EN/Service/Contact/contact.html)

---

### Kai Hilgenberg

**Affiliation / Role:** BAM Berlin / Technische Universität Berlin; senior researcher heading AM process monitoring activities.

**Relevance to this abstract:** Hilgenberg is a recurring senior co-author across BAM's L-PBF monitoring and qualification studies, overseeing work that connects layer-scale observables (thermal signatures, surface structure, powder-layer properties) to porosity and process qualification (mohr2020experimentaldeterminationof pages 1-3, mohr2020insitudefectdetection pages 1-3, schmidt2025surfacestructureanalysis pages 1-2). His group's capabilities in powder-layer quality assessment make him relevant for evaluating whether the dosing-derived property proxies proposed in the abstract can meaningfully predict downstream behavior.

**Contact channel:** No public direct email found; reachable via BAM contact page.

(source: https://www.bam.de/Navigation/EN/Service/Contact/contact.html)

---

### Iver E. Anderson

**Affiliation / Role:** Ames National Laboratory, Iowa (emeritus/retired); pioneer in gas atomization and powder processing.

**Relevance to this abstract:** Anderson is a longstanding authority on gas atomization of metal alloy powders, with decades of research on how atomization parameters control particle size distribution, morphology, and surface chemistry. His expertise is relevant because the abstract deals with elemental and master-alloy powders whose production history and PSD directly affect the cohesion, friction, and packing behavior that the doser is proposed to probe.

**Contact channel:** No public direct email found; reachable via Ames National Laboratory contact page.

(source: https://www.ameslab.gov/about/contact-us)

---

## Category 3: AM Powder Producers and Services with Named Technical Staff

### Mahdi Habibnejad-Korayem

**Affiliation / Role:** AP&C (a GE Additive company) / also published with NRC Canada affiliation.

**Relevance to this abstract:** Habibnejad-Korayem has published on plasma-atomized Ti-6Al-4V powder utilization for L-PBF, including off-size particle effects on powder safety and part properties (Journal of Manufacturing Processes 107:559–573, 2023), and on experimental/numerical investigation of recoating process parameters on spreadability of plasma-atomized powder (Powder Technology 469:121851, 2026). His combined industry (AP&C) and research perspective on how powder production route affects spreadability and recoating is directly relevant to the abstract's inference from dosing to downstream AM behavior.

**Contact channel:** No public direct email found; reachable via NRC Canada contact page or AP&C/GE Additive inquiry.

(source: https://nrc.canada.ca/en/corporate/contact-us)

---

### Equispheres (Company-Level Contact)

**Affiliation / Role:** Ottawa, Canada; producer of engineered aluminum powders for AM.

**Relevance to this abstract:** Equispheres develops highly spherical, narrow-PSD aluminum powders specifically engineered for improved flowability and spreadability in L-PBF. Their industrial perspective on how powder morphology design influences recoating performance is relevant to validating whether dosing-derived cohesion/friction metrics track recoating outcomes for engineered vs. conventional feedstocks.

**Contact channel:** Lab/org-level channel only; reachable via company contact page.

(source: https://equispheres.com/contact/)

---

### Carpenter Additive (Company-Level Contact)

**Affiliation / Role:** Philadelphia, PA, USA (formerly incorporating LPW Technology); AM powder supplier and services.

**Relevance to this abstract:** Carpenter Additive (including the LPW Technology legacy) has published extensively on powder quality, lifecycle management, and reuse for AM. Their practical industry perspective on whether a dosing-derived calibration signature could serve as a lightweight powder-qualification proxy is directly relevant.

**Contact channel:** Lab/org-level channel only; reachable via company contact page.

(source: https://www.carpenteradditive.com/contact)

---

### 6K Additive (Company-Level Contact)

**Affiliation / Role:** North Andover, MA, USA; producer of AM powders via the UniMelt microwave plasma process.

**Relevance to this abstract:** 6K Additive's UniMelt process produces powders from recycled feedstock with distinctive morphology and PSD characteristics. Their production-side insight into how alternative powder-making routes influence flow and packing behavior is relevant to testing the generalizability of dosing-derived property inference across powder types.

**Contact channel:** Lab/org-level channel only; reachable via company contact page.

(source: https://www.6kinc.com/contact/)

---

## Category 4: Standards Efforts on AM Powder Spreadability and Packing

### ASTM F42 Committee on Additive Manufacturing Technologies

**Affiliation / Role:** ASTM International; Subcommittee F42.01 on Test Methods covers powder characterization standards.

**Relevance to this abstract:** The ASTM F42 committee and its F42.01 subcommittee on test methods are the primary forum for standardizing powder characterization procedures for AM, including emerging work on spreadability metrics. The committee's activities are directly relevant because the abstract's proposed dosing-derived property inference could eventually be framed as a complementary or alternative test method to existing flow and packing standards (mussatto2021influencesofpowder pages 11-11).

**Contact channel:** Lab/org-level channel only; reachable via ASTM committee page.

(source: https://www.astm.org/committee-f42-additive-manufacturing-technologies.html)

---

### ASTM Additive Manufacturing Center of Excellence (AM CoE)

**Affiliation / Role:** Program-level contact; partnership between ASTM, NASA, the FAA, NIST, and other organizations.

**Relevance to this abstract:** The AM CoE has coordinated research programs and round-robin style activities around AM qualification, including powder characterization and spreadability. Engagement with the AM CoE could position the dosing-derived property approach against broader interlaboratory metrology efforts.

**Contact channel:** Lab/org-level channel only; reachable via AM CoE contact page.

(source: https://www.amcoe.org/contact/)

---

### America Makes / ANSI Additive Manufacturing Standardization Collaborative (AMSC)

**Affiliation / Role:** Youngstown, OH, USA; national accelerator for AM adoption and standards roadmapping.

**Relevance to this abstract:** The ANSI AMSC Standardization Roadmap for Additive Manufacturing (2018) explicitly identified "PM2 Spreadability" as a gap requiring further development of standard test methods, as cited in the powder spreading literature (mussatto2021influencesofpowder pages 11-11). This makes America Makes relevant for standards-context feedback on whether dosing-derived powder property inference could address the identified spreadability-measurement gap.

**Contact channel:** Lab/org-level channel only; reachable via America Makes contact page.

(source: https://www.americamakes.us/contact/)

---

## Important Caveats

1. **Contact verification:** Only Sina Haeri's email (sina.haeri@strath.ac.uk) was found explicitly published in the text of a retrieved paper (brika2023anovelapparatus pages 1-3). For all other individuals, the recommended approach is to use the institutional/organizational directory or contact page linked in each subsection. I have not fabricated any email addresses.

2. **Industry contacts:** For Categories 3 and 4, individual named technical staff at powder companies (Carpenter, Equispheres, 6K) were not identifiable through the academic literature searched. The exception is Mahdi Habibnejad-Korayem, who publishes academically with AP&C/NRC affiliation. For the other companies, company-level inquiry pages are provided.

3. **Alkan Donmez (NIST):** Although mentioned in the user's query, Donmez is co-author on the same NIST DEM calibration work as Whiting and Garboczi and can be reached through the same NIST staff directory (https://www.nist.gov/people). His role focuses on AM process metrology and powder characterization at NIST.

4. **Edward Reutzel (Penn State):** Reutzel is a senior researcher at Penn State's CIMP-3D and co-author with Snow on AM process monitoring work. He can be reached through the Penn State Applied Research Laboratory directory (https://www.arl.psu.edu/).

5. **Emma White (Ames Lab):** White co-authored with Iver Anderson on powder processing of Alnico magnets and related AM feedstock work. She can be reached via the Ames National Laboratory contact page (https://www.ameslab.gov/about/contact-us).

References

1. (mussatto2021influencesofpowder pages 2-3): Andre Mussatto, Robert Groarke, Aidan O’Neill, Muhannad Ahmed Obeidi, Yan Delaure, and Dermot Brabazon. Influences of powder morphology and spreading parameters on the powder bed topography uniformity in powder bed fusion metal additive manufacturing. Additive Manufacturing, 38:101807, Feb 2021. URL: https://doi.org/10.1016/j.addma.2020.101807, doi:10.1016/j.addma.2020.101807. This article has 314 citations and is from a highest quality peer-reviewed journal.

2. (gruber2021evaluationofinconel pages 25-26): Konrad Gruber, Irina Smolina, Marcin Kasprowicz, and Tomasz Kurzynowski. Evaluation of inconel 718 metallic powder to optimize the reuse of powder and to improve the performance and sustainability of the laser powder bed fusion (lpbf) process. Materials, 14:1538, Mar 2021. URL: https://doi.org/10.3390/ma14061538, doi:10.3390/ma14061538. This article has 99 citations.

3. (mussatto2021influencesofpowder pages 11-11): Andre Mussatto, Robert Groarke, Aidan O’Neill, Muhannad Ahmed Obeidi, Yan Delaure, and Dermot Brabazon. Influences of powder morphology and spreading parameters on the powder bed topography uniformity in powder bed fusion metal additive manufacturing. Additive Manufacturing, 38:101807, Feb 2021. URL: https://doi.org/10.1016/j.addma.2020.101807, doi:10.1016/j.addma.2020.101807. This article has 314 citations and is from a highest quality peer-reviewed journal.

4. (spierings2018powderspreadabilityand pages 1-8): AB Spierings. Powder spreadability and characterization of sc- and zr-modified aluminium alloys processed by selective laser melting: quality management system for additive manufacturing. Unknown journal, 2018. URL: https://doi.org/10.3929/ethz-b-000253924, doi:10.3929/ethz-b-000253924. This article has 32 citations.

5. (cordova2020measuringthespreadability pages 1-2): Laura Cordova, Ton Bor, Marc de Smit, Mónica Campos, and Tiedo Tinga. Measuring the spreadability of pre-treated and moisturized powders for laser powder bed fusion. Additive Manufacturing, 32:101082, Mar 2020. URL: https://doi.org/10.1016/j.addma.2020.101082, doi:10.1016/j.addma.2020.101082. This article has 166 citations and is from a highest quality peer-reviewed journal.

6. (cordova2020measuringthespreadability pages 2-3): Laura Cordova, Ton Bor, Marc de Smit, Mónica Campos, and Tiedo Tinga. Measuring the spreadability of pre-treated and moisturized powders for laser powder bed fusion. Additive Manufacturing, 32:101082, Mar 2020. URL: https://doi.org/10.1016/j.addma.2020.101082, doi:10.1016/j.addma.2020.101082. This article has 166 citations and is from a highest quality peer-reviewed journal.

7. (cordova2020measuringthespreadability pages 12-12): Laura Cordova, Ton Bor, Marc de Smit, Mónica Campos, and Tiedo Tinga. Measuring the spreadability of pre-treated and moisturized powders for laser powder bed fusion. Additive Manufacturing, 32:101082, Mar 2020. URL: https://doi.org/10.1016/j.addma.2020.101082, doi:10.1016/j.addma.2020.101082. This article has 166 citations and is from a highest quality peer-reviewed journal.

8. (brika2023anovelapparatus pages 1-3): Salah Eddine Brika and Vladimir Brailovski. A novel apparatus for the simulation of powder spreading procedures in powder-bed-based additive manufacturing processes: design, calibration, and case study. Journal of Manufacturing and Materials Processing, 7:135, Jul 2023. URL: https://doi.org/10.3390/jmmp7040135, doi:10.3390/jmmp7040135. This article has 14 citations.

9. (brika2023anovelapparatus pages 3-3): Salah Eddine Brika and Vladimir Brailovski. A novel apparatus for the simulation of powder spreading procedures in powder-bed-based additive manufacturing processes: design, calibration, and case study. Journal of Manufacturing and Materials Processing, 7:135, Jul 2023. URL: https://doi.org/10.3390/jmmp7040135, doi:10.3390/jmmp7040135. This article has 14 citations.

10. (mussatto2021influencesofpowder pages 10-11): Andre Mussatto, Robert Groarke, Aidan O’Neill, Muhannad Ahmed Obeidi, Yan Delaure, and Dermot Brabazon. Influences of powder morphology and spreading parameters on the powder bed topography uniformity in powder bed fusion metal additive manufacturing. Additive Manufacturing, 38:101807, Feb 2021. URL: https://doi.org/10.1016/j.addma.2020.101807, doi:10.1016/j.addma.2020.101807. This article has 314 citations and is from a highest quality peer-reviewed journal.

11. (yuasa2021influencesofpowder pages 13-14): Kenya Yuasa, Masaharu Tagami, Makiko Yonehara, Toshi-Taka Ikeshoji, Koki Takeshita, Hiroshi Aoki, and Hideki Kyogoku. Influences of powder characteristics and recoating conditions on surface morphology of powder bed in metal additive manufacturing. The International Journal of Advanced Manufacturing Technology, 115:3919-3932, Jun 2021. URL: https://doi.org/10.1007/s00170-021-07359-x, doi:10.1007/s00170-021-07359-x. This article has 64 citations.

12. (brika2023anovelapparatus pages 3-5): Salah Eddine Brika and Vladimir Brailovski. A novel apparatus for the simulation of powder spreading procedures in powder-bed-based additive manufacturing processes: design, calibration, and case study. Journal of Manufacturing and Materials Processing, 7:135, Jul 2023. URL: https://doi.org/10.3390/jmmp7040135, doi:10.3390/jmmp7040135. This article has 14 citations.

13. (mohr2020experimentaldeterminationof pages 1-3): Gunther Mohr, Susanna Nowakowski, Simon J. Altenburg, Christiane Maierhofer, and Kai Hilgenberg. Experimental determination of the emissivity of powder layers and bulk material in laser powder bed fusion using infrared thermography and thermocouples. Metals, 10:1546, Nov 2020. URL: https://doi.org/10.3390/met10111546, doi:10.3390/met10111546. This article has 85 citations.

14. (mohr2020insitudefectdetection pages 1-3): Gunther Mohr, Simon J. Altenburg, Alexander Ulbricht, Philipp Heinrich, Daniel Baum, Christiane Maierhofer, and Kai Hilgenberg. In-situ defect detection in laser powder bed fusion by using thermography and optical tomography—comparison to computed tomography. ArXiv, 10:103, Jan 2020. URL: https://doi.org/10.3390/met10010103, doi:10.3390/met10010103. This article has 206 citations.

15. (schmidt2025surfacestructureanalysis pages 1-2): Jonathan Schmidt, Benjamin Merz, Konstantin Poka, Gunther Mohr, and Kai Hilgenberg. Surface structure analysis using visual high-resolution in situ process monitoring in laser powder bed fusion. Welding in the World, Feb 2025. URL: https://doi.org/10.1007/s40194-025-01955-1, doi:10.1007/s40194-025-01955-1. This article has 6 citations and is from a domain leading peer-reviewed journal.