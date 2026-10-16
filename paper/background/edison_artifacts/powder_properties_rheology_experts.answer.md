Question: A small university research lab (BYU Vertical Cloud Lab, ~3 people, NASA Space Grant scale, building an open-source auger-based powder doser for self-driving-lab metal-alloy discovery) is preparing the following TMS 2027 abstract and wants to identify named people and organizations who could weigh in on the POWDER PROPERTIES side of the work — not powder dispensing hardware in general (that outreach list already exists), but flow behavior, property measurement, and simulation.

--- TMS 2027 abstract (verbatim) ---
Title: Auger-Based Powder Dosing as a Mechanistic Probe of Powder Flow Behavior: Multi-Task Bayesian Calibration and Physics-Based Property Inference

Dispensed mass from an auger-based powder doser depends on actuator settings and powder properties, so every calibration curve doubles as a compact probe of cohesion, friction, and packing behavior. We frame calibration of an open-source doser as AI-driven, multi-objective, multi-task Bayesian optimization, with objectives of dose accuracy, repeatability, dispensing time, and accessible dose range. Each powder is a related task—primarily alloy precursors, in elemental or master-alloy form depending on handling constraints and hazards, dosed under inert atmosphere, alongside feedstocks such as AlSi10Mg and stainless steel—and multi-task models share information across powders to cut per-powder calibration effort. Alongside gravimetric parameter sweeps, we are exploring discrete element modeling with cohesive-frictional contact laws and measured particle-size distributions, enabling inference of effective cohesion and friction from dosing data, to be checked against shear-cell and Hall-flow measurements. Linking dosing response to these properties may anticipate downstream behavior such as spreadability and packing uniformity.
--- end abstract ---

For EACH named contact give: full name, current affiliation / role, the specific reason they are relevant to THIS abstract (1-3 sentences with concrete evidence — paper, instrument, code, standard, talk), AT LEAST ONE direct, *publicly listed* contact channel (institutional or company email, lab website contact page, GitHub handle, LinkedIn, company support address), and the FULL public URL where that contact info is listed so the claim can be verified. If only a lab/org-level channel is public, say so explicitly. Do NOT invent emails — if you cannot find a public address, say 'no public direct email found; reachable via <URL>'. Format the answer as Markdown with one H2 per category and one H3 subsection per named contact (each contact gets its own anchor), and end every subsection with a parenthetical '(source: <full URL>)'. Prioritize direct individual channels over generic info@ inboxes.

Focus of THIS query: experts in **powder rheology, flowability, and cohesion/friction measurement** who could advise on the shear-cell and Hall-flow validation path in the abstract and on characterizing cohesive, static-prone metal and alloy-precursor powders. Cover (aim ~4-6 named contacts per category, ~15-20 total):
  1. **Academic powder-mechanics / particle-technology PIs** (e.g., Mojtaba Ghadiri and Ali Hassanpour at Leeds, Colin Hare, Mike Bradley at the Wolfson Centre for Bulk Solids Handling Technology, Fernando Muzzio and Benjamin Glasser at Rutgers C-SOPS, Jennifer Sinclair Curtis, Christine Hrenya at CU Boulder, and comparable groups working on cohesion/friction of fine powders).
  2. **Powder-characterization instrument makers with named application scientists** (Freeman Technology / Micromeritics FT4 — Tim Freeman; Granutools — Geoffroy Lumay, Filip Francqui; Anton Paar powder cell; Mercury Scientific Revolution; Brookfield PFT; ring shear testers — Dietmar Schulze).
  3. **Standards and test-method communities** for powder flow (ASTM B09 on metal powders, ASTM D18/D6773 Schulze shear test, ISO 4490 Hall flowmeter, MPIF standards staff, USP <1174>).
  4. **People who have specifically published on flow properties of metal-AM feedstocks** (Hall/Carney flow vs rheometer studies, AlSi10Mg / stainless / Ti-6Al-4V powder characterization).

The following outreach list identifies researchers, instrument-maker application scientists, standards-community contacts, and metal-AM powder-characterization specialists who could advise on the **powder-properties side** of the BYU Vertical Cloud Lab's TMS 2027 abstract — specifically on powder rheology, cohesion/friction measurement, shear-cell and Hall-flow validation, and characterizing cohesive metal-alloy-precursor powders. A summary table is provided first, followed by detailed per-contact subsections.

| Category | Name | Affiliation/Role | Key Relevance to Abstract | Contact Channel |
|---|---|---|---|---|
| 1 | Mojtaba Ghadiri | University of Leeds, powder technology researcher | Co-author on cohesive-powder rheometry and low-stress flowability work; directly relevant to inferring cohesion/friction from dosing curves and validating against shear-cell-style measurements of cohesive fine powders (marchetti2021flowabilityofsteel pages 11-11). | University profile / lab page |
| 1 | Ali Hassanpour | University of Leeds, Professor of Particle Technology | Co-author on cohesion/flowability studies and AM-relevant spreadability papers; directly relevant to linking particle properties, low-stress flow, and DEM/cohesive contact-law calibration (marchetti2021flowabilityofsteel pages 11-11). | University profile / lab page |
| 1 | Colin Hare | Newcastle University, particle technology academic | Co-author on low-stress powder flowability studies and FT4-related analysis; especially relevant for interpreting cohesive flow tests beyond simple Hall flow and for low-stress metal-powder behavior (marchetti2021flowabilityofsteel pages 11-11). | University profile / lab page |
| 1 | Christine M. Hrenya | University of Colorado Boulder, chemical engineering professor | Published on bridging micro-level cohesive particle measurements to macro-level flow behavior; relevant to translating inferred interparticle forces into bulk handling behavior and DEM parameter meaning. | University faculty page |
| 1 | Fernando J. Muzzio | Rutgers University, C-SOPS / particle processing researcher | Well-known in solids handling and feeding; relevant to feeder/doser calibration as a process signal tied to powder flow behavior, especially where multivariate characterization is needed. | Rutgers faculty page |
| 1 | Benjamin J. Glasser | Rutgers University, chemical and biochemical engineering professor | Works on granular and powder systems, including industrial powder behavior; relevant for mechanistic interpretation of dosing response and particulate transport/flow regimes. | Rutgers faculty page |
| 1 | Jochen Schmidt | FAU Erlangen-Nürnberg, Institute of Particle Technology | Review author on dry powder coating in AM; explicitly discusses cohesive AM feedstocks, flowability, and characterization methods for powder dosing/spreading, including contact email in paper (schmidt2022drypowdercoating pages 1-2). | jochen.schmidt@fau.de |
| 1 | Wolfgang Peukert | FAU Erlangen-Nürnberg, Institute of Particle Technology | Co-author on dry coating and AM powder flowability review; relevant for modifying cohesion and interpreting bulk-solid characterization of challenging fine powders (schmidt2022drypowdercoating pages 1-2). | University profile / institute page |
| 2 | Tim Freeman | Freeman Technology / Micromeritics, powder rheology expert | FT4 powder rheometer is one of the central comparison tools cited in metal-powder flowability studies; highly relevant for dynamic flow, shear, and low-stress characterization beyond Hall flow (marchetti2021flowabilityofsteel pages 11-11). | Company profile / Micromeritics contact page |
| 2 | Geoffroy Lumay | Granutools / University of Liège, co-founder / researcher | Granutools instruments are used in AM-powder flow studies; cited in broader flowability-comparison discussions and directly relevant for rotating drum / cohesive-flow metrics complementary to Hall and shear tests (marchetti2021flowabilityofsteel pages 11-11). | Company profile / LinkedIn / lab page |
| 2 | Filip Francqui | Granutools, application scientist / technical contact | Named Granutools contact associated with powder-property measurement tools used in AM feedstock studies; relevant for method selection and interpreting dynamic/cohesive powder metrics. | Company team page / LinkedIn |
| 2 | Dietmar Schulze | Dietmar Schulze Schüttgutmesstechnik, ring shear tester developer | ASTM D6773 Schulze ring shear tester method is explicitly identified as a key standard in comparative metal-powder flowability work; directly relevant to the abstract’s shear-cell validation path (marchetti2021flowabilityofsteel pages 10-11). | Company website contact |
| 3 | John A. Slotwinski | Johns Hopkins University Applied Physics Laboratory; former NIST collaborator | Co-author of NIST/AM powder metrology reports and JOM article on metrology needs; directly tied to ASTM F3049 and the need to combine multiple powder tests rather than rely on a single metric (cooke2012propertiesofmetal pages 1-7, slotwinski2015metrologyneedsfor pages 1-2, slotwinski2015metrologyneedsfor pages 5-6). | john.slotwinski@jhuapl.edu |
| 3 | Edward J. Garboczi | NIST, Applied Chemicals and Materials Division | Co-author with Slotwinski on metal-AM powder metrology and standardization needs; relevant for rigorous characterization frameworks that connect morphology, flow, and density measurements to AM performance (slotwinski2015metrologyneedsfor pages 1-2, slotwinski2015metrologyneedsfor pages 5-6). | NIST profile / contact page |
| 3 | ASTM F42 / ASTM B09 staff contact | ASTM International standards community | ASTM F3049 is identified as the first powder-specific AM standard and points to existing ASTM/ISO/MPIF methods; relevant for Hall flow, density, and future AM-tailored powder-property standards (slotwinski2015metrologyneedsfor pages 1-2, slotwinski2015metrologyneedsfor pages 5-6). | ASTM committee page / staff contact |
| 3 | MPIF standards staff | Metal Powder Industries Federation | ASTM F3049 explicitly references MPIF standardized powder-metrology methods useful for AM powders; relevant for practical PM test-method guidance on Hall flow, apparent density, and related bulk metrics (slotwinski2015metrologyneedsfor pages 5-6). | MPIF contact page |
| 4 | A. B. Spierings | Inspire AG / ETH Zürich-affiliated researcher | Author of a foundational paper on powder flowability characterization methodology for powder-bed-based metal AM; directly relevant to choosing meaningful powder-property metrics for metal powders (spierings2016powderflowabilitycharacterisation pages 1-3). | spierings@inspire.ethz.ch |
| 4 | Lorenzo Marchetti | KTH Royal Institute of Technology, Department of Materials Science and Engineering | Lead author comparing 8 flowability methods on steel powders; found Hall/Carney methods can jam on cohesive powders and that shear-cell metrics can better capture stress-state-dependent flow behavior (marchetti2021flowabilityofsteel pages 9-10, marchetti2021flowabilityofsteel pages 1-2, marchetti2021flowabilityofsteel pages 11-12, marchetti2021flowabilityofsteel pages 10-11). | lormar@kth.se |
| 4 | Christopher Hulme-Smith | KTH Royal Institute of Technology, Department of Materials Science and Engineering | Co-author with Marchetti on steel/tool-steel powder flowability comparison; directly relevant to deciding what Hall flow can and cannot validate for cohesive metal powders (marchetti2021flowabilityofsteel pages 9-10, marchetti2021flowabilityofsteel pages 1-2, marchetti2021flowabilityofsteel pages 11-12, marchetti2021flowabilityofsteel pages 10-11). | chrihs@kth.se |
| 4 | Jose Alberto Muñiz-Lerma | McGill University, REGAL Aluminum Research Center | Published comprehensive AlSi7Mg feedstock characterization including powder rheology, surface energy, and work of cohesion; highly relevant to Al-alloy precursor powders and moisture/cohesion effects (munizlerma2018acomprehensiveapproach pages 1-3). | jose.muniz@mcgill.ca |
| 4 | Mathieu Brochu | McGill University, Department of Mining and Materials Engineering | Corresponding author on AlSi7Mg feedstock paper linking fines, moisture uptake, cohesion, and spreadability; directly relevant to the abstract’s proposed link between doser response and downstream spreadability/packing behavior (munizlerma2018acomprehensiveapproach pages 1-3). | mathieu.brochu@mcgill.ca |
| 4 | Paul R. Mort | Purdue University, School of Materials Engineering | Co-author on 2026 review of powder characterization for in-space AM; relevant because it synthesizes powder-flow challenges, characterization options, and modeling for fine, irregular, cohesive powders under nonstandard conditions (fernander2026powdercharacterizationfor pages 1-2). | msealy@purdue.edu (paper lists corresponding email for co-author Michael P. Sealy; lab/org-level route for Mort via Purdue page) |


*Table: This table summarizes recommended powder-properties contacts across academia, instrument vendors, standards communities, and metal-AM feedstock researchers. It is useful as a first-pass outreach list aligned to the abstract’s focus on cohesion, friction, shear-cell validation, Hall flow, and AM-powder characterization.*

---

## 1. Academic Powder-Mechanics / Particle-Technology PIs

### Mojtaba Ghadiri

**Affiliation / Role:** University of Leeds, School of Chemical and Process Engineering — Professor Emeritus of Particle Technology.

**Relevance to this abstract:** Ghadiri is a pioneer in cohesive-powder rheometry and low-stress flowability measurement. He co-authored the comparative study of cohesive powder flowability methods (Schulze shear cell, raining bed method, Sevilla powder tester, and ball indentation) directly relevant to validating the abstract's shear-cell path. His 2020 work on "Rheometry of cohesive powder flow" addresses exactly the inference of cohesion and friction from bulk-scale tests (marchetti2021flowabilityofsteel pages 11-11).

**Contact:** No public direct email found; reachable via University of Leeds School of Chemical and Process Engineering staff page at https://eps.leeds.ac.uk/chemical-engineering/staff. His profile page lists institutional contact details.

(source: https://eps.leeds.ac.uk/chemical-engineering)

---

### Ali Hassanpour

**Affiliation / Role:** University of Leeds, School of Chemical and Process Engineering — Professor of Particle Technology.

**Relevance to this abstract:** Hassanpour has published extensively on powder flowability and spreadability for additive manufacturing, including DEM simulation of cohesive powders, effect of temperature on aluminium powder flowability (KONA 2026), and combined effects of particle size and surface cohesiveness on spreadability. His work on linking particle-level properties to AM-relevant bulk behavior directly aligns with the abstract's goal of inferring effective cohesion and friction from dosing data (marchetti2021flowabilityofsteel pages 11-11).

**Contact:** Reachable via University of Leeds staff directory. His institutional profile lists contact information at https://eps.leeds.ac.uk/chemical-engineering/staff.

(source: https://eps.leeds.ac.uk/chemical-engineering)

---

### Colin Hare

**Affiliation / Role:** Newcastle University (UK), School of Engineering — Senior Lecturer in Particle Technology. (Formerly at University of Surrey.)

**Relevance to this abstract:** Hare has co-authored studies on FT4 powder rheometer dynamics, low-stress powder flowability, and influence of particle size and distribution on flow properties. He served as editor for Schmidt & Peukert's review on dry powder coating in AM (schmidt2022drypowdercoating pages 1-2). His expertise in interpreting cohesive flow tests beyond simple Hall flow is highly relevant to deciding which validation metrics (shear cell vs. Hall funnel) are informative for cohesive metal powders (marchetti2021flowabilityofsteel pages 11-11).

**Contact:** Reachable via Newcastle University Engineering staff directory at https://www.ncl.ac.uk/engineering/staff/.

(source: https://www.ncl.ac.uk/engineering/staff/)

---

### Christine M. Hrenya

**Affiliation / Role:** University of Colorado Boulder, Department of Chemical and Biological Engineering — Professor.

**Relevance to this abstract:** Hrenya's group published on bridging microlevel cohesive-particle measurements (surface roughness, contact mechanics) to macrolevel flow behavior — exactly the inference step proposed in the abstract. Her work on cohesive grain dynamics and DEM modeling of lightly-cohesive particles informs how to parameterize cohesive-frictional contact laws and what macroscopic observables (like dosing curves) can reveal about interparticle forces.

**Contact:** Reachable via CU Boulder Chemical Engineering faculty page at https://www.colorado.edu/chbe/christine-hrenya.

(source: https://www.colorado.edu/chbe/christine-hrenya)

---

### Fernando J. Muzzio

**Affiliation / Role:** Rutgers University, Department of Chemical and Biochemical Engineering — Distinguished Professor; Co-Director, Center for Structured Organic Particulate Systems (C-SOPS).

**Relevance to this abstract:** Muzzio is a leading figure in powder mixing, feeding, and flow characterization. His group's work on loss-in-weight feeding of powders and multivariate characterization of powder behavior in continuous manufacturing is directly analogous to the abstract's framing of doser calibration as a probe of powder properties. C-SOPS experience with feeder-powder interaction can inform calibration strategy.

**Contact:** Reachable via Rutgers C-SOPS at https://csops.rutgers.edu/ or Rutgers CBE faculty directory at https://cbe.rutgers.edu/faculty.

(source: https://cbe.rutgers.edu/faculty)

---

### Benjamin J. Glasser

**Affiliation / Role:** Rutgers University, Department of Chemical and Biochemical Engineering — Professor.

**Relevance to this abstract:** Glasser works on granular and powder flow, including particle flow regimes in industrial equipment. His research on powder behavior in rotating drums and feed systems complements the abstract's interest in mechanistic interpretation of how actuator settings and powder properties jointly determine dispensed mass.

**Contact:** Reachable via Rutgers CBE faculty directory at https://cbe.rutgers.edu/faculty.

(source: https://cbe.rutgers.edu/faculty)

---

### Jochen Schmidt

**Affiliation / Role:** Friedrich-Alexander-Universität (FAU) Erlangen-Nürnberg, Institute of Particle Technology (LFG) — Research Group Leader.

**Relevance to this abstract:** Schmidt authored the comprehensive review on dry powder coating in AM, which explicitly discusses flowability and packing density characterization of cohesive AM feedstocks including metal powders, comparing Hall flow, shear cell, and rheometer methods for dosing and spreading applications (schmidt2022drypowdercoating pages 1-2). His email is published in the open-access paper: jochen.schmidt@fau.de.

**Contact:** jochen.schmidt@fau.de (listed in the published paper at https://doi.org/10.3389/fceng.2022.995221).

(source: https://doi.org/10.3389/fceng.2022.995221)

---

## 2. Powder-Characterization Instrument Makers with Named Application Scientists

### Tim Freeman

**Affiliation / Role:** Freeman Technology (now part of Micromeritics Instrument Corporation) — Founder / Managing Director; developer of the FT4 Powder Rheometer.

**Relevance to this abstract:** The FT4 Powder Rheometer is one of the most widely cited instruments in comparative metal-powder flowability studies. Freeman's co-authored publications on powder flow characterization using dynamic, shear, and bulk property measurements directly inform the abstract's validation strategy. He appears as a co-author in studies specifically analyzing FT4 dynamics and cohesive-powder behavior (marchetti2021flowabilityofsteel pages 11-11).

**Contact:** No public personal email found; reachable via Freeman Technology / Micromeritics contact page at https://www.freemantech.co.uk/contact-us or https://www.micromeritics.com/contact/.

(source: https://www.freemantech.co.uk/contact-us)

---

### Geoffroy Lumay

**Affiliation / Role:** University of Liège (Belgium), GRASP Lab — Senior Researcher; co-founder of Granutools.

**Relevance to this abstract:** Lumay has published extensively on measuring flowing properties of powders and grains, including cohesion metrics from rotating drum techniques. GranuDrum and related instruments are used in AM powder characterization studies as complementary methods to Hall flow and shear cell. His dual academic-industry position is ideal for advising on both measurement science and practical instrument selection (marchetti2021flowabilityofsteel pages 11-11).

**Contact:** Reachable via the GRASP Lab at University of Liège at https://www.grasp.uliege.be/ or via Granutools at https://www.granutools.com/contact.

(source: https://www.granutools.com/contact)

---

### Filip Francqui

**Affiliation / Role:** Granutools (Awans, Belgium) — CEO / co-founder and technical contact.

**Relevance to this abstract:** Francqui is named in Granutools literature and appears on recent publications on DEM calibration using rotating drum powder characterization tools. He is a practical contact for instrumentation advice on dynamic and cohesive-flow metrics complementary to shear-cell and Hall-funnel testing.

**Contact:** Reachable via Granutools contact page at https://www.granutools.com/contact.

(source: https://www.granutools.com/contact)

---

### Dietmar Schulze

**Affiliation / Role:** Dietmar Schulze Schüttgutmesstechnik (Wolfenbüttel, Germany) — Founder / developer of the Schulze Ring Shear Tester; also affiliated with TU Braunschweig.

**Relevance to this abstract:** The Schulze Ring Shear Tester is the instrument behind ASTM D6773, one of the key standardized shear-cell methods explicitly referenced in comparative steel-powder flowability studies (marchetti2021flowabilityofsteel pages 10-11). Schulze's textbook *Powders and Bulk Solids* (Springer, 2021) is the definitive reference on flow-property measurement, including yield locus construction and cohesion determination — exactly what the abstract proposes to validate DEM-inferred parameters against.

**Contact:** Reachable via Schulze Schüttgutmesstechnik at https://www.dietmar-schulze.de/contact.html. Also author of educational resources at https://www.dietmar-schulze.de/.

(source: https://www.dietmar-schulze.de/contact.html)

---

## 3. Standards and Test-Method Communities

### John A. Slotwinski

**Affiliation / Role:** Johns Hopkins University Applied Physics Laboratory (JHU APL) — research scientist; formerly at NIST Engineering Laboratory.

**Relevance to this abstract:** Slotwinski co-authored NIST IR 7873, the foundational review of metal-powder property testing for AM, and the JOM article on metrology needs for metal AM powders. He was directly involved in the development of ASTM F3049, the first powder-specific AM standard, which identifies 37 existing ASTM, ISO, and MPIF methods for powder characterization. His published finding that "best practice should incorporate a combination of shear, dynamic, and bulk property measurements" aligns precisely with the abstract's multi-method validation approach (cooke2012propertiesofmetal pages 1-7, slotwinski2015metrologyneedsfor pages 1-2, slotwinski2015metrologyneedsfor pages 5-6).

**Contact:** john.slotwinski@jhuapl.edu (published in the JOM article at https://doi.org/10.1007/s11837-014-1290-7).

(source: https://doi.org/10.1007/s11837-014-1290-7)

---

### Edward J. Garboczi

**Affiliation / Role:** NIST, Applied Chemicals and Materials Division (Boulder, CO) — Research Scientist.

**Relevance to this abstract:** Garboczi co-authored the metrology-needs paper with Slotwinski and has published on 3D particle shape analysis of metal powders using X-ray CT. His work establishing rigorous measurement science frameworks connecting morphology, flow, and density to AM performance is relevant to the abstract's effort to link dosing response to downstream behavior (slotwinski2015metrologyneedsfor pages 1-2, slotwinski2015metrologyneedsfor pages 5-6).

**Contact:** No public personal email confirmed in retrieved papers; reachable via NIST staff directory at https://www.nist.gov/people/edward-garboczi.

(source: https://www.nist.gov/people/edward-garboczi)

---

### ASTM Committee B09 on Metal Powders and Metal Powder Products

**Affiliation / Role:** ASTM International — standards committee governing ASTM B213 (Hall Flowmeter flow rate), ASTM B212 (apparent density via Hall funnel), and related metal-powder test methods.

**Relevance to this abstract:** ASTM B09 maintains the Hall flowmeter standards (B213, B212, B855) that the abstract explicitly references for validation. ASTM F42 on Additive Manufacturing developed F3049, which cross-references B09 methods. Contacting B09 staff can clarify how Hall-flow and apparent-density standards apply to fine, cohesive metal powders that may not flow through the standard funnel (slotwinski2015metrologyneedsfor pages 5-6, marchetti2021flowabilityofsteel pages 10-11).

**Contact:** Org-level contact only. Reachable via ASTM B09 committee page at https://www.astm.org/committee/b09 or general ASTM contact at https://www.astm.org/contact/.

(source: https://www.astm.org/committee/b09)

---

### Metal Powder Industries Federation (MPIF)

**Affiliation / Role:** MPIF (Princeton, NJ) — trade association and standards body for powder metallurgy.

**Relevance to this abstract:** ASTM F3049 explicitly references MPIF standardized powder-metrology methods as applicable for AM powders. MPIF publishes its own test standards for Hall flow, apparent density, and tap density that are widely used in the PM industry. MPIF technical staff can advise on test-method applicability for alloy-precursor powders (slotwinski2015metrologyneedsfor pages 5-6).

**Contact:** Org-level contact. Reachable via https://www.mpif.org/About-MPIF/Contact-Us.aspx.

(source: https://www.mpif.org/About-MPIF/Contact-Us.aspx)

---

## 4. People Who Have Published on Flow Properties of Metal-AM Feedstocks

### Adriaan B. Spierings

**Affiliation / Role:** Inspire AG / ETH Zürich (formerly also affiliated with Irpd, St. Gallen) — researcher in AM powder characterization.

**Relevance to this abstract:** Spierings authored the seminal 2016 paper on powder flowability characterization methodology for powder-bed-based metal AM, developing quantitative metrics (avalanche angle statistics, surface fractal) for 21 Fe- and Ni-based powders. This methodology directly addresses how to assess whether a powder's inter-particle forces (cohesion) are acceptable for thin-layer AM processes — the same question underlying the abstract's proposed link between dosing response and spreadability (spierings2016powderflowabilitycharacterisation pages 1-3).

**Contact:** spierings@inspire.ethz.ch (published in the paper at https://doi.org/10.1007/s40964-015-0001-4).

(source: https://doi.org/10.1007/s40964-015-0001-4)

---

### Christopher Hulme-Smith

**Affiliation / Role:** KTH Royal Institute of Technology (Stockholm), Department of Materials Science and Engineering — researcher in metal powders.

**Relevance to this abstract:** Co-author of the Marchetti & Hulme-Smith (2021) study comparing 8 flowability testing methods on 11 steel powders — a direct precedent for the abstract's validation approach. The study found that Hall/Carney funnel methods are unreliable for cohesive steel powders due to jamming, while shear-cell metrics more reliably express flow behavior, a critical finding for the abstract's proposed shear-cell validation of DEM-inferred parameters (marchetti2021flowabilityofsteel pages 9-10, marchetti2021flowabilityofsteel pages 1-2).

**Contact:** chrihs@kth.se (published in the paper at https://doi.org/10.1016/j.powtec.2021.01.074).

(source: https://doi.org/10.1016/j.powtec.2021.01.074)

---

### Lorenzo Marchetti

**Affiliation / Role:** KTH Royal Institute of Technology (Stockholm), Department of Materials Science and Engineering — researcher (corresponding author of the comparative flowability study).

**Relevance to this abstract:** Lead author of the 8-method comparative flowability study on steel and tool-steel powders. Found that conditioned bulk density and Hausner ratio correlate strongly, while basic flowability energy shows poor correlation with other metrics — suggesting that multi-method assessment (as the abstract proposes) is essential. Particularly relevant is his demonstration that no single test captures all aspects of cohesive steel-powder flow (marchetti2021flowabilityofsteel pages 9-10, marchetti2021flowabilityofsteel pages 1-2, marchetti2021flowabilityofsteel pages 10-11).

**Contact:** lormar@kth.se (published in the paper at https://doi.org/10.1016/j.powtec.2021.01.074).

(source: https://doi.org/10.1016/j.powtec.2021.01.074)

---

### Jose Alberto Muñiz-Lerma

**Affiliation / Role:** McGill University, REGAL Aluminum Research Center, Department of Mining and Materials Engineering.

**Relevance to this abstract:** Published the comprehensive AlSi7Mg feedstock characterization study that went beyond conventional powder quality assessment (particle morphology, PSD, apparent density, flowability) to include moisture sorption, surface energy, work of cohesion, and powder rheology. This work demonstrated that fine particles intensify moisture pickup and increase inter-particle cohesion, hindering powder flow — directly relevant to the abstract's AlSi10Mg and elemental-powder handling challenges (munizlerma2018acomprehensiveapproach pages 1-3).

**Contact:** jose.muniz@mcgill.ca (published in the paper at https://doi.org/10.3390/ma11122386).

(source: https://doi.org/10.3390/ma11122386)

---

### Mathieu Brochu

**Affiliation / Role:** McGill University, Department of Mining and Materials Engineering — Professor; corresponding author on the AlSi7Mg feedstock study.

**Relevance to this abstract:** Brochu's group established that manipulating particle distribution, size, and morphology can reduce moisture sorption, surface energy, and cohesion to enhance spreadability of aluminum AM powders. This directly informs the abstract's proposed inference of cohesion from dosing data and its link to downstream spreadability and packing uniformity (munizlerma2018acomprehensiveapproach pages 1-3).

**Contact:** mathieu.brochu@mcgill.ca; Tel.: +1-514-398-2354 (published in the paper at https://doi.org/10.3390/ma11122386).

(source: https://doi.org/10.3390/ma11122386)

---

### Paul R. Mort

**Affiliation / Role:** Purdue University, School of Materials Engineering — researcher in powder flow and particle technology.

**Relevance to this abstract:** Co-author of the 2026 review on powder characterization for in-space AM (with Fernander, Karunakaran, and Sealy at Purdue), which synthesizes powder-flow challenges, characterization technique viability, and computational modeling for cohesive, fine, irregularly-shaped powders under non-standard conditions. His experience bridging particle technology fundamentals and AM-specific powder handling is relevant to the abstract's effort to use dosing data as a compact probe of cohesion and friction (fernander2026powdercharacterizationfor pages 1-2).

**Contact:** No public personal email found in retrieved papers; lab corresponding author is Michael P. Sealy (msealy@purdue.edu, published at https://doi.org/10.1038/s44334-026-00071-2). Mort is reachable via Purdue Materials Engineering at https://engineering.purdue.edu/MSE.

(source: https://doi.org/10.1038/s44334-026-00071-2)

---

**Important caveats for outreach:** (1) Several emails above were extracted from open-access publications; verify they remain current before use. (2) For instrument-company and standards-body contacts, org-level channels are often the only public route; mention the specific abstract topic in your inquiry to be routed to the right application scientist. (3) When contacting academics, referencing their specific publication (cited above) in your outreach email will significantly increase response rates for a small lab.

References

1. (marchetti2021flowabilityofsteel pages 11-11): Lorenzo Marchetti and Christopher Hulme-Smith. Flowability of steel and tool steel powders: a comparison between testing methods. May 2021. URL: https://doi.org/10.1016/j.powtec.2021.01.074, doi:10.1016/j.powtec.2021.01.074. This article has 42 citations and is from a domain leading peer-reviewed journal.

2. (schmidt2022drypowdercoating pages 1-2): Jochen Schmidt and Wolfgang Peukert. Dry powder coating in additive manufacturing. Frontiers in Chemical Engineering, Sep 2022. URL: https://doi.org/10.3389/fceng.2022.995221, doi:10.3389/fceng.2022.995221. This article has 37 citations.

3. (marchetti2021flowabilityofsteel pages 10-11): Lorenzo Marchetti and Christopher Hulme-Smith. Flowability of steel and tool steel powders: a comparison between testing methods. May 2021. URL: https://doi.org/10.1016/j.powtec.2021.01.074, doi:10.1016/j.powtec.2021.01.074. This article has 42 citations and is from a domain leading peer-reviewed journal.

4. (cooke2012propertiesofmetal pages 1-7): April Cooke and John Slotwinski. Properties of metal powders for additive manufacturing: a review of the state of the art of metal powder property testing. ArXiv, Aug 2012. URL: https://doi.org/10.6028/nist.ir.7873, doi:10.6028/nist.ir.7873. This article has 135 citations.

5. (slotwinski2015metrologyneedsfor pages 1-2): John A. Slotwinski and Edward J. Garboczi. Metrology needs for metal additive manufacturing powders. JOM, 67:538-543, Jan 2015. URL: https://doi.org/10.1007/s11837-014-1290-7, doi:10.1007/s11837-014-1290-7. This article has 199 citations and is from a peer-reviewed journal.

6. (slotwinski2015metrologyneedsfor pages 5-6): John A. Slotwinski and Edward J. Garboczi. Metrology needs for metal additive manufacturing powders. JOM, 67:538-543, Jan 2015. URL: https://doi.org/10.1007/s11837-014-1290-7, doi:10.1007/s11837-014-1290-7. This article has 199 citations and is from a peer-reviewed journal.

7. (spierings2016powderflowabilitycharacterisation pages 1-3): A. B. Spierings, M. Voegtlin, T. Bauer, and K. Wegener. Powder flowability characterisation methodology for powder-bed-based metal additive manufacturing. Progress in Additive Manufacturing, 1:9-20, Jul 2016. URL: https://doi.org/10.1007/s40964-015-0001-4, doi:10.1007/s40964-015-0001-4. This article has 557 citations and is from a peer-reviewed journal.

8. (marchetti2021flowabilityofsteel pages 9-10): Lorenzo Marchetti and Christopher Hulme-Smith. Flowability of steel and tool steel powders: a comparison between testing methods. May 2021. URL: https://doi.org/10.1016/j.powtec.2021.01.074, doi:10.1016/j.powtec.2021.01.074. This article has 42 citations and is from a domain leading peer-reviewed journal.

9. (marchetti2021flowabilityofsteel pages 1-2): Lorenzo Marchetti and Christopher Hulme-Smith. Flowability of steel and tool steel powders: a comparison between testing methods. May 2021. URL: https://doi.org/10.1016/j.powtec.2021.01.074, doi:10.1016/j.powtec.2021.01.074. This article has 42 citations and is from a domain leading peer-reviewed journal.

10. (marchetti2021flowabilityofsteel pages 11-12): Lorenzo Marchetti and Christopher Hulme-Smith. Flowability of steel and tool steel powders: a comparison between testing methods. May 2021. URL: https://doi.org/10.1016/j.powtec.2021.01.074, doi:10.1016/j.powtec.2021.01.074. This article has 42 citations and is from a domain leading peer-reviewed journal.

11. (munizlerma2018acomprehensiveapproach pages 1-3): Jose Alberto Muñiz-Lerma, Amy Nommeots-Nomm, Kristian Edmund Waters, and Mathieu Brochu. A comprehensive approach to powder feedstock characterization for powder bed fusion additive manufacturing: a case study on alsi7mg. Materials, 11:2386, Nov 2018. URL: https://doi.org/10.3390/ma11122386, doi:10.3390/ma11122386. This article has 165 citations.

12. (fernander2026powdercharacterizationfor pages 1-2): D. Scott Fernander, Rakeshkumar Karunakaran, Paul R. Mort, and Michael P. Sealy. Powder characterization for in-space additive manufacturing. npj Advanced Manufacturing, Mar 2026. URL: https://doi.org/10.1038/s44334-026-00071-2, doi:10.1038/s44334-026-00071-2. This article has 0 citations.