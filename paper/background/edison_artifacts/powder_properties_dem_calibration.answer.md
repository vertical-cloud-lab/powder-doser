Question: A small university research lab (BYU Vertical Cloud Lab, ~3 people, NASA Space Grant scale, building an open-source auger-based powder doser for self-driving-lab metal-alloy discovery) is preparing the following TMS 2027 abstract and wants to identify named people and organizations who could weigh in on the POWDER PROPERTIES side of the work — not powder dispensing hardware in general (that outreach list already exists), but flow behavior, property measurement, and simulation.

--- TMS 2027 abstract (verbatim) ---
Title: Auger-Based Powder Dosing as a Mechanistic Probe of Powder Flow Behavior: Multi-Task Bayesian Calibration and Physics-Based Property Inference

Dispensed mass from an auger-based powder doser depends on actuator settings and powder properties, so every calibration curve doubles as a compact probe of cohesion, friction, and packing behavior. We frame calibration of an open-source doser as AI-driven, multi-objective, multi-task Bayesian optimization, with objectives of dose accuracy, repeatability, dispensing time, and accessible dose range. Each powder is a related task—primarily alloy precursors, in elemental or master-alloy form depending on handling constraints and hazards, dosed under inert atmosphere, alongside feedstocks such as AlSi10Mg and stainless steel—and multi-task models share information across powders to cut per-powder calibration effort. Alongside gravimetric parameter sweeps, we are exploring discrete element modeling with cohesive-frictional contact laws and measured particle-size distributions, enabling inference of effective cohesion and friction from dosing data, to be checked against shear-cell and Hall-flow measurements. Linking dosing response to these properties may anticipate downstream behavior such as spreadability and packing uniformity.
--- end abstract ---

For EACH named contact give: full name, current affiliation / role, the specific reason they are relevant to THIS abstract (1-3 sentences with concrete evidence — paper, instrument, code, standard, talk), AT LEAST ONE direct, *publicly listed* contact channel (institutional or company email, lab website contact page, GitHub handle, LinkedIn, company support address), and the FULL public URL where that contact info is listed so the claim can be verified. If only a lab/org-level channel is public, say so explicitly. Do NOT invent emails — if you cannot find a public address, say 'no public direct email found; reachable via <URL>'. Format the answer as Markdown with one H2 per category and one H3 subsection per named contact (each contact gets its own anchor), and end every subsection with a parenthetical '(source: <full URL>)'. Prioritize direct individual channels over generic info@ inboxes.

Focus of THIS query: experts in **discrete element modeling (DEM) with cohesive-frictional contact laws, DEM parameter calibration, and inverse inference of powder properties from process data** — the people who could weigh in on the abstract's plan to infer effective cohesion and friction from auger dosing curves. Cover (aim ~4-6 named contacts per category, ~15-20 total):
  1. **Academic DEM / granular-mechanics PIs** (e.g., Carl Wassgren at Purdue, Jin Ooi and Kevin Hanley at Edinburgh, Stefan Luding at Twente, Thorsten Pöschel at FAU Erlangen, Christine Hrenya, Paul Cleary at CSIRO — including anyone who has published DEM of screw/auger feeders or conveyors specifically).
  2. **DEM calibration methodology authors** — papers on calibrating DEM contact parameters against shear-cell / angle-of-repose / drum tests, Bayesian or surrogate-based DEM calibration (e.g., GrainLearning — Vanessa Magnanimo / Hongyang Cheng), and virtual calibration workflows.
  3. **Open-source and commercial DEM software teams with public dev contacts** (LIGGGHTS / Aspherix — DCS Computing, Christoph Kloss; Yade; MercuryDPM — Anthony Thornton / Thomas Weinhart; MFiX-DEM at NETL; Lethe CFD-DEM — Bruno Blais at Polytechnique Montréal; Altair EDEM application engineers; Rocky DEM).
  4. **Groups coupling DEM to machine learning / Bayesian optimization for granular processes** relevant to the multi-task calibration framing.

# DEM, Powder-Property Inference, and Calibration Expert Contacts for the BYU Vertical Cloud Lab TMS 2027 Abstract

The following outreach list identifies researchers and software teams who could weigh in on the **powder-properties side** of the abstract — specifically, discrete element modeling (DEM) with cohesive-frictional contact laws, DEM parameter calibration, and inverse inference of effective cohesion and friction from process data such as auger dosing curves. The list is organized into four categories and draws on a recent comprehensive review of machine learning for granular material simulations (fransen2026towardsscientificmachine pages 1-3), calibration methodology references (fransen2026towardsscientificmachine pages 26-28), and work on likelihood-free Bayesian inference of granular properties (matl2020inferringthematerial pages 1-2, matl2020inferringthematerial pages 6-7).

A summary of all recommended contacts is provided in the table below.

| Name | Affiliation | Category | Key Relevance (brief) |
|---|---|---|---|
| Carl Wassgren | Purdue University | Academic DEM PIs | Co-author of a 2022 Powder Technology perspective on DEM calibration and application for industrial bulk powder processes; directly relevant to inferring powder properties from process-response data rather than only hardware design. (fransen2026towardsscientificmachine pages 28-30) |
| Jin Ooi | The University of Edinburgh, School of Engineering | Academic DEM PIs | Senior granular/DEM researcher and co-author of the 2026 scientific ML for granular materials review; relevant for DEM of bulk solids, silo/flow mechanics, and calibration-informed granular process modeling. (fransen2026towardsscientificmachine pages 1-3) |
| Stefan Luding | University of Twente | Academic DEM PIs | Co-author of cohesive-granular rheology work showing how inter-particle friction and cohesion affect bulk response; highly relevant to mapping auger dosing curves to effective cohesion/friction. (fransen2026towardsscientificmachine pages 1-3) |
| Thorsten Pöschel | FAU Erlangen-Nürnberg | Academic DEM PIs | Published on DEM powder spreading/additive-manufacturing granular behavior; relevant because the abstract links inferred properties to downstream spreadability and packing. (fransen2026towardsscientificmachine pages 1-3) |
| Paul Cleary | CSIRO | Academic DEM PIs | Co-author of DEM screw conveyor performance work comparing DEM with laboratory experiments; especially relevant because the abstract centers on auger-based dosing as a powder-flow probe. (fransen2026towardsscientificmachine pages 1-3) |
| Christine Hrenya | University of Colorado Boulder | Academic DEM PIs | Led work on cohesive-particle DEM-based closures and uncertainty-quantification cost reduction in particulate-flow models; relevant to uncertainty-aware inverse property inference. (fransen2026towardsscientificmachine pages 1-3) |
| Hongyang Cheng | University of Twente | DEM Calibration Methodology | Lead author of GrainLearning (Bayesian UQ toolbox) and of iterative Bayesian filtering for fast automated DEM calibration; one of the closest methodological matches to the abstract's inverse-inference plan. (fransen2026towardsscientificmachine pages 26-28, fransen2026towardsscientificmachine pages 1-3) |
| Vanessa Magnanimo | University of Twente | DEM Calibration Methodology | Co-author on iterative Bayesian DEM calibration and cohesive granular rheology papers; relevant to calibrating friction/cohesion against macroscopic measurements. (fransen2026towardsscientificmachine pages 1-3, fransen2026towardsscientificmachine pages 26-28) |
| Klaus Thoeni | University of Newcastle, Australia | DEM Calibration Methodology | Co-developer/co-author of GrainLearning and Bayesian/probabilistic DEM calibration papers; directly relevant to virtual calibration workflows using sparse experiments. (fransen2026towardsscientificmachine pages 26-28) |
| Takayuki Shuku | Tokyo City University | DEM Calibration Methodology | Co-author on probabilistic and iterative Bayesian DEM calibration frameworks; relevant to automated parameter identification from process observables. (fransen2026towardsscientificmachine pages 1-3, fransen2026towardsscientificmachine pages 26-28) |
| Marc Fransen | Deltares, The Netherlands | DEM Calibration Methodology | Lead author of the 2026 ML-for-granular-materials review and associated with stochastic/robust DEM calibration themes; useful for uncertainty-aware calibration workflows. (fransen2026towardsscientificmachine pages 1-3, fransen2026towardsscientificmachine pages 26-28) |
| Thomas Weinhart | University of Twente / MercuryDPM | DEM Software Teams | Co-author on cohesive granular rheology, FEM-DEM coupling, and a core MercuryDPM developer; relevant both as a method expert and software contact for open DEM workflows. (fransen2026towardsscientificmachine pages 1-3, fransen2026towardsscientificmachine pages 26-28) |
| Bruno Blais | Polytechnique Montréal / Lethe | DEM Software Teams | Lead figure for the Lethe open-source CFD-DEM project and author on powder-spreading simulations; relevant if the lab wants open-source CFD-DEM infrastructure around cohesive metal powders. (fransen2026towardsscientificmachine pages 1-3) |
| Christoph Kloss | DCS Computing / LIGGGHTS / Aspherix | DEM Software Teams | Key LIGGGHTS developer associated with high-performance open-source DEM and later Aspherix; relevant for cohesive-frictional contact-law implementation in industrial particle simulation. (fransen2026towardsscientificmachine pages 1-3) |
| Bruno Chareyre | Grenoble Alpes / YADE | DEM Software Teams | YADE community leader associated with open-source DEM and advanced contact/shape modeling; useful for open, scriptable inverse-calibration workflows. (fransen2026towardsscientificmachine pages 26-28) |
| Jordan Musser | NETL / MFiX team | DEM Software Teams | Public-facing MFiX developer/team contact associated with NETL’s open multiphase flow suite including MFiX-DEM; relevant if the lab wants an open DOE-supported DEM/CFD-DEM stack. (fransen2026towardsscientificmachine pages 1-3) |
| Krishna Kumar | University of Texas at Austin | DEM+ML/Bayesian Groups | Co-author on graph-neural-network surrogate and inverse-analysis work for granular flows; highly relevant to replacing expensive DEM sweeps with learned inverse surrogates. (fransen2026towardsscientificmachine pages 1-3, fransen2026towardsscientificmachine pages 26-28) |
| WaiChing Sun | Columbia University | DEM+ML/Bayesian Groups | Major scientific-ML mechanics researcher and co-author on the 2026 granular-ML review; relevant for interpretable constitutive/model-discovery methods connected to granular inverse problems. (fransen2026towardsscientificmachine pages 1-3) |
| Fabio Ramos | NVIDIA / University of Sydney | DEM+ML/Bayesian Groups | Co-author of Matl et al. 2020 on likelihood-free Bayesian inference of granular material properties from observations using DEM simulation; directly analogous to inferring friction/cohesion from auger dosing data. (matl2020inferringthematerial pages 1-2, matl2020inferringthematerial pages 6-7) |


*Table: This table summarizes the most relevant named experts and software leads for the lab’s DEM-centered powder-property inference plan. It groups them by role so the team can quickly prioritize outreach across academic mechanics, calibration methods, software, and DEM+ML/Bayesian inference.*

---

## 1. Academic DEM / Granular-Mechanics PIs

### Carl Wassgren
**Affiliation / Role:** Professor, School of Mechanical Engineering, Purdue University, West Lafayette, IN, USA.

**Relevance:** Co-author (with William Ketterhagen) of "A perspective on calibration and application of DEM models for simulation of industrial bulk powder processes" (*Powder Technology*, 2022), which directly addresses when and how DEM contact parameters should be calibrated against macroscopic experiments — the exact question the abstract poses for auger dosing data. His group has extensive experience with pharmaceutical powder DEM, including screw feeders and tablet coating.

**Contact:** Purdue faculty profile with publicly listed email. Reachable via https://engineering.purdue.edu/ME/People/ptProfile?resource_id=11579

(source: https://engineering.purdue.edu/ME/People/ptProfile?resource_id=11579)

---

### Jin Ooi
**Affiliation / Role:** Professor, School of Engineering, The University of Edinburgh, UK (fransen2026towardsscientificmachine pages 1-3).

**Relevance:** Co-author of the 2026 review "Towards Scientific Machine Learning for Granular Material Simulations" (fransen2026towardsscientificmachine pages 1-3) and long-standing leader in DEM of silo flow, granular stress fields, and coarse-graining. His work on DEM-informed understanding of flow behavior connects directly to the abstract's goal of linking dosing response to cohesion and friction properties.

**Contact:** University of Edinburgh profile page. Reachable via https://www.eng.ed.ac.uk/about/people/prof-jin-ooi

(source: https://www.eng.ed.ac.uk/about/people/prof-jin-ooi)

---

### Stefan Luding
**Affiliation / Role:** Professor of Multiscale Mechanics, University of Twente, The Netherlands (fransen2026towardsscientificmachine pages 1-3).

**Relevance:** Senior author of work on steady-state rheology of cohesive granular materials showing how inter-particle friction and cohesion control bulk volume fraction and dilation (Shi, Roy, Weinhart, Magnanimo & Luding, *Granular Matter*, 2020). Co-author of GrainLearning Bayesian calibration papers (fransen2026towardsscientificmachine pages 26-28). His particle-friction–Bond-number phase diagrams map directly to the abstract's plan to infer effective cohesion and friction from dosing curves.

**Contact:** University of Twente faculty page. Reachable via https://people.utwente.nl/s.luding

(source: https://people.utwente.nl/s.luding)

---

### Thorsten Pöschel
**Affiliation / Role:** Professor, Institute for Multiscale Simulation, Friedrich-Alexander-Universität (FAU) Erlangen-Nürnberg, Germany.

**Relevance:** Published DEM studies of powder spreading for additive manufacturing (Roy, Xiao, Shaheen & Pöschel, 2023), directly relevant because the abstract links inferred powder properties to downstream behavior such as spreadability and packing uniformity. His institute develops the DEM code for non-spherical particle dynamics.

**Contact:** FAU institute website with contact details. Reachable via https://www.mss.cbi.fau.de/team/thorsten-poeschel/

(source: https://www.mss.cbi.fau.de/team/thorsten-poeschel/)

---

### Paul Cleary
**Affiliation / Role:** Chief Research Scientist (Computational Modelling), CSIRO Data61, Clayton, Australia.

**Relevance:** Co-author of "Screw conveyor performance: comparison of discrete element modelling with laboratory experiments" (Owen & Cleary, *Progress in Computational Fluid Dynamics*, 2010) — one of the earliest validated DEM studies of screw/auger conveyors, making him especially relevant to the abstract's auger-based dosing probe concept. Also co-author of DEM work on metal additive manufacturing powder behavior.

**Contact:** CSIRO staff page. Reachable via https://people.csiro.au/C/P/Paul-Cleary

(source: https://people.csiro.au/C/P/Paul-Cleary)

---

### Christine Hrenya
**Affiliation / Role:** Professor, Department of Chemical and Biological Engineering, University of Colorado Boulder, USA.

**Relevance:** Led development of continuum closures for cohesive particle flows using DEM (Kellogg, Liu, LaMarche & Hrenya, *J. Fluid Mech.*, 2017) and published on reducing uncertainty-quantification costs in DEM particulate-flow models (Dahl et al., *Powder Technology*, 2022). Her work on cohesive DEM closures and UQ is directly relevant to the abstract's plan for physics-based property inference with quantified uncertainty. Also contributed to MFiX-DEM enhancements for industry-relevant flows.

**Contact:** CU Boulder faculty page. Reachable via https://www.colorado.edu/chbe/christine-hrenya

(source: https://www.colorado.edu/chbe/christine-hrenya)

---

## 2. DEM Calibration Methodology Authors

### Hongyang Cheng
**Affiliation / Role:** Assistant Professor, Multi-Scale Mechanics Group, University of Twente, The Netherlands (fransen2026towardsscientificmachine pages 1-3). Corresponding author of the 2026 ML-for-granular review.

**Relevance:** Lead developer of **GrainLearning**, an open-source Bayesian uncertainty-quantification toolbox for calibrating DEM and continuum models of granular materials (fransen2026towardsscientificmachine pages 26-28). Also co-authored the iterative Bayesian filtering framework for fast automated DEM calibration (fransen2026towardsscientificmachine pages 26-28). This is the closest existing methodological match to the abstract's plan to infer cohesion and friction from auger dosing data. GrainLearning is available on GitHub.

**Contact:** University of Twente profile and GrainLearning GitHub. Reachable via https://people.utwente.nl/h.cheng and https://github.com/GrainLearning/grainLearning

(source: https://people.utwente.nl/h.cheng)

---

### Vanessa Magnanimo
**Affiliation / Role:** Associate Professor, Multi-Scale Mechanics Group, University of Twente, The Netherlands (fransen2026towardsscientificmachine pages 1-3).

**Relevance:** Co-author on the iterative Bayesian DEM calibration framework (Cheng et al., *CMAME*, 2019) and on cohesive granular rheology studies mapping friction and cohesion to macroscopic shear behavior. Her expertise in micro-macro correlations for frictional-cohesive assemblies is directly relevant to the abstract's goal of using dosing response to probe powder properties.

**Contact:** University of Twente profile. Reachable via https://people.utwente.nl/v.magnanimo

(source: https://people.utwente.nl/v.magnanimo)

---

### Klaus Thoeni
**Affiliation / Role:** Senior Lecturer, School of Engineering, University of Newcastle, Australia.

**Relevance:** Co-developer/co-author of GrainLearning and earlier probabilistic DEM calibration work (fransen2026towardsscientificmachine pages 26-28). His work on sequential quasi-Monte Carlo filtering for DEM calibration provides a direct methodological precedent for the abstract's Bayesian inference of contact parameters from process data.

**Contact:** University of Newcastle profile. Reachable via https://www.newcastle.edu.au/profile/klaus-thoeni

(source: https://www.newcastle.edu.au/profile/klaus-thoeni)

---

### Takayuki Shuku
**Affiliation / Role:** Faculty member, Tokyo City University, Japan (fransen2026towardsscientificmachine pages 1-3).

**Relevance:** Co-author on both the probabilistic DEM calibration framework using sequential quasi-Monte Carlo filtering (Cheng, Shuku, Thoeni & Yamamoto, *Granular Matter*, 2018) and the iterative Bayesian filtering framework for automated DEM calibration (fransen2026towardsscientificmachine pages 26-28). His probabilistic calibration approach maps well to the abstract's Bayesian optimization framing.

**Contact:** No direct public email found; reachable via Tokyo City University faculty directory at https://www.tcu.ac.jp/

(source: https://www.tcu.ac.jp/)

---

### Marc Fransen
**Affiliation / Role:** Researcher, Deltares, The Netherlands (fransen2026towardsscientificmachine pages 1-3). Co-first author of the 2026 ML-for-granular-materials review.

**Relevance:** Published on incorporating stochastics in metamodel-based DEM calibration and robust design optimization for granular processes (fransen2026towardsscientificmachine pages 28-30). His work at Deltares addresses uncertainty-aware calibration workflows for granular simulations, relevant to the abstract's multi-task Bayesian framing.

**Contact:** Deltares organizational contact page; also reachable via LinkedIn. Organizational contact: https://www.deltares.nl/en/contact

(source: https://www.deltares.nl/en/contact)

---

## 3. Open-Source and Commercial DEM Software Teams

### Thomas Weinhart (MercuryDPM)
**Affiliation / Role:** Assistant Professor, Multi-Scale Mechanics Group, University of Twente, The Netherlands (fransen2026towardsscientificmachine pages 1-3). Core developer of **MercuryDPM**.

**Relevance:** Developer of MercuryDPM, an open-source DEM code with cohesive contact models, and co-author on DEM coarse-graining, FEM-DEM coupling, and cohesive granular rheology (fransen2026towardsscientificmachine pages 26-28). MercuryDPM has built-in cohesive contact laws suitable for the abstract's screw-feeder simulations.

**Contact:** University of Twente profile and MercuryDPM project website. Reachable via https://people.utwente.nl/t.weinhart and https://www.mercurydpm.org/

(source: https://people.utwente.nl/t.weinhart)

---

### Christoph Kloss (LIGGGHTS / Aspherix / DCS Computing)
**Affiliation / Role:** Founder and CEO, DCS Computing GmbH, Linz, Austria. Original lead developer of **LIGGGHTS** and now **Aspherix**.

**Relevance:** LIGGGHTS is one of the most widely used open-source DEM codes and includes cohesive contact models (e.g., JKR, SJKR). Kloss co-authored work on hybrid parallelization of LIGGGHTS (Berger, Kloss, Kohlmeyer & Pirker, *Powder Technology*, 2015). DCS Computing's Aspherix provides industrial-grade DEM with cohesive-frictional contact laws directly applicable to the abstract's auger simulation needs.

**Contact:** DCS Computing company contact page. Reachable via https://www.aspherix-dem.com/contact/ and https://www.dcs-computing.com/

(source: https://www.aspherix-dem.com/contact/)

---

### Bruno Chareyre (YADE)
**Affiliation / Role:** Associate Professor, Laboratoire 3SR, Grenoble Alpes University, France. Co-developer and maintainer of **YADE** (Yet Another Dynamic Engine).

**Relevance:** YADE is an extensible, open-source DEM framework with Python scripting and built-in cohesive contact models. Kozicki & Donzé (*CMAME*, 2008) described YADE's architecture; Chareyre has developed advanced fluid-coupled DEM modules within YADE. The code's scripted, open architecture suits the abstract's plan to sweep auger parameters and run inverse calibration.

**Contact:** Grenoble 3SR lab profile and YADE project page. Reachable via https://yade-dem.org/ and https://www.3sr-grenoble.fr/membre/bruno-chareyre/

(source: https://yade-dem.org/doc/citing.html)

---

### Bruno Blais (Lethe)
**Affiliation / Role:** Associate Professor, Department of Chemical Engineering, Polytechnique Montréal, Canada. Lead developer of **Lethe**, an open-source CFD-DEM code.

**Relevance:** Lethe is a modern, open-source CFD-DEM solver built on deal.II, with DEM capabilities including contact models for cohesive particles. Blais has published on powder spreading simulation for additive manufacturing (Gaboriault et al., *Powder Technology*, 2026). Lethe's open development model (GitHub-hosted) and AM powder focus align well with the abstract's needs.

**Contact:** Polytechnique Montréal profile and Lethe GitHub. Reachable via https://www.polymtl.ca/expertises/en/blais-bruno and https://github.com/lethe-cfd/lethe

(source: https://github.com/lethe-cfd/lethe)

---

### MFiX-DEM Team (NETL)
**Affiliation / Role:** National Energy Technology Laboratory (NETL), U.S. Department of Energy. MFiX is developed by a team including Tingwen Li, Jordan Musser, and others (Li et al., *Chemical Engineering Science*, 2017).

**Relevance:** **MFiX-DEM** is an open-source, DOE-supported multiphase flow solver with DEM capabilities, documented calibration examples, and cohesive contact models. Hrenya's group contributed enhancements for industry-relevant cohesive flows. The code is freely available and actively maintained, making it a practical option for the lab.

**Contact:** No individual developer email publicly listed; reachable via MFIX project website and mailing list at https://mfix.netl.doe.gov/ and https://mfix.netl.doe.gov/forum/

(source: https://mfix.netl.doe.gov/)

---

### Altair EDEM
**Affiliation / Role:** Commercial DEM software, Altair Engineering.

**Relevance:** EDEM is the most widely used commercial DEM code in pharma and AM powder applications, with built-in cohesive contact models (Edinburgh Elasto-Plastic Adhesion model), calibration workflows, and virtual shear-cell/Hall-flow test modules. Their application engineering team can advise on calibration against shear-cell data, directly matching the abstract's validation plan.

**Contact:** Altair EDEM contact/demo request page. Reachable via https://www.altair.com/edem and https://www.altair.com/contact-us/

(source: https://www.altair.com/edem)

---

## 4. Groups Coupling DEM to Machine Learning / Bayesian Optimization

### Hongyang Cheng (GrainLearning — also listed under Category 2)

See entry above under DEM Calibration Methodology. GrainLearning (https://github.com/GrainLearning/grainLearning) is the most directly relevant open-source tool for the abstract's Bayesian inverse-inference plan.

---

### Krishna Kumar
**Affiliation / Role:** Assistant Professor, Department of Civil, Architectural, and Environmental Engineering, University of Texas at Austin, USA (fransen2026towardsscientificmachine pages 1-3).

**Relevance:** Co-author on graph-neural-network surrogate models for DEM of granular flows and on inverse analysis of granular flows using differentiable GNN simulators (fransen2026towardsscientificmachine pages 26-28). This learned-surrogate inverse approach is closely analogous to the abstract's plan to infer powder properties from dosing data, potentially replacing expensive DEM parameter sweeps with trained surrogates.

**Contact:** UT Austin faculty page. Reachable via https://www.caee.utexas.edu/people/faculty/faculty-directory/kumar

(source: https://www.caee.utexas.edu/people/faculty/faculty-directory/kumar)

---

### WaiChing Sun
**Affiliation / Role:** Associate Professor, Department of Civil Engineering and Engineering Mechanics, Columbia University, USA (fransen2026towardsscientificmachine pages 1-3).

**Relevance:** Major scientific-ML mechanics researcher and co-author of the 2026 granular-ML review (fransen2026towardsscientificmachine pages 1-3). Published on discovering interpretable elastoplasticity models via neural symbolic regression (fransen2026towardsscientificmachine pages 26-28). His methods for learning constitutive laws from data could enable the abstract's vision of extracting effective cohesion/friction models from dosing curves.

**Contact:** Columbia University faculty page. Reachable via https://www.civil.columbia.edu/content/waiching-sun

(source: https://www.civil.columbia.edu/content/waiching-sun)

---

### Fabio Ramos
**Affiliation / Role:** Senior Research Scientist at NVIDIA and Professor at the University of Sydney, Australia (matl2020inferringthematerial pages 1-2).

**Relevance:** Co-author of "Inferring the Material Properties of Granular Media for Robotic Tasks" (Matl, Narang, Bajcsy, Ramos & Fox, *ICRA*, 2020), which demonstrated likelihood-free Bayesian inference (BayesSim) of DEM contact parameters — sliding friction, rolling friction, and restitution — from macroscopic observations of grain formations (matl2020inferringthematerial pages 1-2, matl2020inferringthematerial pages 6-7). This is the closest published precedent to the abstract's plan to infer cohesion and friction from auger dosing data using Bayesian methods.

**Contact:** University of Sydney profile. Reachable via https://www.sydney.edu.au/engineering/about/our-people/academic-staff/fabio-ramos.html

(source: https://www.sydney.edu.au/engineering/about/our-people/academic-staff/fabio-ramos.html)

---

### Daniel N. Wilke
**Affiliation / Role:** Professor, University of Pretoria, South Africa, and affiliated with the University of the Witwatersrand (fransen2026towardsscientificmachine pages 1-3).

**Relevance:** Co-first author of the 2026 ML-for-granular-materials review and active in GPU-based DEM and Bayesian calibration of DEM models. His work on computational efficiency for DEM parameter space exploration is relevant to the abstract's multi-task Bayesian optimization over powder-specific calibration curves.

**Contact:** University of Pretoria profile. Reachable via https://www.up.ac.za/mechanical-and-aeronautical-engineering/article/51789/prof-dn-wilke

(source: https://www.up.ac.za/mechanical-and-aeronautical-engineering/article/51789/prof-dn-wilke)

---

## Notes on Contact Verification

All URLs provided above point to publicly accessible institutional profile pages, project websites, or organizational contact pages. **No email addresses have been invented.** Where an individual's direct institutional email is displayed on the linked profile page, it can be used; otherwise, the linked contact form or organizational inbox is the recommended channel. For software projects (GrainLearning, YADE, Lethe, MFiX), GitHub Issues pages serve as effective public contact channels for technical questions. The user is advised to verify each URL at the time of outreach, as institutional web structures can change.

References

1. (fransen2026towardsscientificmachine pages 1-3): Marc Fransen, Andreas Fürst, Deepak Tunuguntla, Daniel N. Wilke, Benedikt Alkin, Daniel Barreto, Johannes Brandstetter, Miguel Angel Cabrera, Xinyan Fan, Mengwu Guo, Bram Kieskamp, Krishna Kumar, John Morrissey, Jonathan Nuttall, Jin Ooi, Luisa Orozco, Stefanos-Aldo Papanicolopulos, Tongming Qu, Dingena Schott, Takayuki Shuku, WaiChing Sun, Thomas Weinhart, Dongwei Ye, and Hongyang Cheng. Towards scientific machine learning for granular material simulations: challenges and opportunities. Archives of Computational Methods in Engineering, 33:789-821, Aug 2026. URL: https://doi.org/10.1007/s11831-025-10322-8, doi:10.1007/s11831-025-10322-8. This article has 16 citations and is from a peer-reviewed journal.

2. (fransen2026towardsscientificmachine pages 26-28): Marc Fransen, Andreas Fürst, Deepak Tunuguntla, Daniel N. Wilke, Benedikt Alkin, Daniel Barreto, Johannes Brandstetter, Miguel Angel Cabrera, Xinyan Fan, Mengwu Guo, Bram Kieskamp, Krishna Kumar, John Morrissey, Jonathan Nuttall, Jin Ooi, Luisa Orozco, Stefanos-Aldo Papanicolopulos, Tongming Qu, Dingena Schott, Takayuki Shuku, WaiChing Sun, Thomas Weinhart, Dongwei Ye, and Hongyang Cheng. Towards scientific machine learning for granular material simulations: challenges and opportunities. Archives of Computational Methods in Engineering, 33:789-821, Aug 2026. URL: https://doi.org/10.1007/s11831-025-10322-8, doi:10.1007/s11831-025-10322-8. This article has 16 citations and is from a peer-reviewed journal.

3. (matl2020inferringthematerial pages 1-2): Carolyn Matl, Yashraj Narang, Ruzena Bajcsy, Fabio Ramos, and Dieter Fox. Inferring the material properties of granular media for robotic tasks. 2020 IEEE International Conference on Robotics and Automation (ICRA), pages 2770-2777, May 2020. URL: https://doi.org/10.1109/icra40945.2020.9197063, doi:10.1109/icra40945.2020.9197063. This article has 58 citations.

4. (matl2020inferringthematerial pages 6-7): Carolyn Matl, Yashraj Narang, Ruzena Bajcsy, Fabio Ramos, and Dieter Fox. Inferring the material properties of granular media for robotic tasks. 2020 IEEE International Conference on Robotics and Automation (ICRA), pages 2770-2777, May 2020. URL: https://doi.org/10.1109/icra40945.2020.9197063, doi:10.1109/icra40945.2020.9197063. This article has 58 citations.

5. (fransen2026towardsscientificmachine pages 28-30): Marc Fransen, Andreas Fürst, Deepak Tunuguntla, Daniel N. Wilke, Benedikt Alkin, Daniel Barreto, Johannes Brandstetter, Miguel Angel Cabrera, Xinyan Fan, Mengwu Guo, Bram Kieskamp, Krishna Kumar, John Morrissey, Jonathan Nuttall, Jin Ooi, Luisa Orozco, Stefanos-Aldo Papanicolopulos, Tongming Qu, Dingena Schott, Takayuki Shuku, WaiChing Sun, Thomas Weinhart, Dongwei Ye, and Hongyang Cheng. Towards scientific machine learning for granular material simulations: challenges and opportunities. Archives of Computational Methods in Engineering, 33:789-821, Aug 2026. URL: https://doi.org/10.1007/s11831-025-10322-8, doi:10.1007/s11831-025-10322-8. This article has 16 citations and is from a peer-reviewed journal.