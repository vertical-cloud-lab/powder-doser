Top recommendation: **MT03: AI-Driven Workflows and Autonomous Platforms for Functional Material Design and Catalysis**. It is the cleanest fit because your repo shows a real closed-loop, Bayesian-optimization/self-driving-lab framing plus substantial, concrete work on AI-assisted hardware design for a powder-dosing module that feeds an ultrasonic-atomization → L-PBF workflow.

## Top 5 most-aligned symposia

### 1) **MT03: AI-Driven Workflows and Autonomous Platforms for Functional Material Design and Catalysis**
**Why this fits:** The scope explicitly calls for “data-efficient autonomous experimentation and closed-loop optimization,” “active learning and Bayesian optimization,” “human-in-the-loop strategies,” “infrastructure and orchestration of distributed autonomous research systems,” and “generative AI.” That lines up unusually well with your repo, which repeatedly frames the doser as part of the **BYU Vertical Cloud Lab self-driving / Bayesian-optimization workflow**, and documents an **AI design → printing → testing → feedback → AI design** loop for the hardware. The repo also ties validation to an **ultrasonic-atomization → L-PBF** pipeline and records concrete AI-CAD exploration with **GitHub Copilot agent mode, zoo.dev, and CADSmith**, rather than just talking about AI in the abstract.

**Organizers:**
- Don Futaba — National Institute of Advanced Industrial Science and Technology, Japan
- Rui Goncalves — Nanyang Technological University, Singapore
- Placidus Amama — Kansas State University, USA
- Karolina Laszczyk — Wroclaw University of Science and Technology, Poland

**Best angle to emphasize:**
Lead with the powder doser as an **AI-enabled hardware node in a closed-loop materials-discovery platform**. Emphasize the human-plus-agent CAD workflow, modular dosing hardware, planned gravimetric feedback control, and the fact that the device exists to support autonomous exploration of composition space for AM feedstocks.

### 2) **MT01: Leveraging Advances in AI for Materials Design and Autonomous Materials Science**
**Why this fits:** MT01 is broader than MT03, but it directly welcomes “multi-modal and generative AI,” “integration of AI/ML with experimental platforms, including synthesis, processing, and characterization,” and “closing the feedback loop between computation and experimentation.” Your repo has strong evidence for exactly that framing: the NASA proposal materials describe the doser need as grounded in a **self-driving-laboratory workflow**, and multiple issues/PRs document the use of **agentic/generative CAD tools** to design printable augers, brackets, sealing caps, mounting plates, and assemblies. The work is not just software-side either; the repo records real hardware targets such as **30 reservoirs, ≤250 mL/blend, ±1 mg per-powder accuracy with a ±0.1 mg stretch goal**, plus closed-loop gravimetric dispensing and modular electronics.

**Organizers:**
- Guoxiang (Emma) Hu — Georgia Institute of Technology, USA
- Mahshid Ahamdi — The University of Tennessee, Knoxville, USA
- Bin Ouyang — Florida State University, USA
- Dong-Hwa Seo — Korea Advanced Institute of Science and Technology, Republic of Korea

**Best angle to emphasize:**
Pitch the project as **autonomous materials-science infrastructure**, not just a feeder mechanism. Focus on how generative/agentic AI plus experimental hardware are being coupled to accelerate alloy/feedstock design cycles.

### 3) **MT04: Technologies for Informed and Accelerated Synthesis of Inorganic Materials**
**Why this fits:** MT04 is a strong home if you want to foreground the doser as an enabling **synthesis technology**. Its scope explicitly includes “automated synthesis workflows,” “high-throughput automatic testing platforms,” “combined computational-experimental synthesis approaches,” and “machine learning methods for materials synthesis.” In your repo, the doser is repeatedly framed as the practical bottleneck-removal tool for **multi-powder blending**, with concrete architecture work on **single-channel modular dosers scalable to 30+ powders**, gravimetric feedback, vibration/tapping subsystems, auger drive, and cross-contamination mitigation. That is a very plausible “informed and accelerated synthesis” story for inorganic/metal feedstock preparation.

**Organizers:**
- Yong-Jie Hu — Drexel University, USA
- Yan Zeng — Florida State University, USA
- Yuta Saito — Tohoku University, Japan
- Richard Otis — Proteus Space, USA

**Best angle to emphasize:**
Emphasize the doser as an **open-source, low-cost front end for accelerated inorganic feedstock synthesis and blend preparation**. Keep the AI-CAD story, but subordinate it to the experimental throughput / synthesis-enablement story.

### 4) **SF03: Intermetallics—From the Basics to Structure and Function**
**Why this fits:** SF03 is the best non-AI symposium if you want to lean into the downstream materials application. The scope explicitly welcomes “advanced processing techniques including additive manufacturing,” “computation and modeling studies and informatics approaches,” and applications in “aircraft” and other industries. Your repo and proposal materials repeatedly tie the doser to **AM aerospace alloys**, **L-PBF**, and feedstock preparation for compositionally varied metal powders; the background work also references multi-material/high-throughput metal AM and alloy-discovery literature. The risk is that the symposium is more materials-centric than hardware-centric, so the abstract would need to connect the doser tightly to **intermetallic/alloy processing studies**, not just device development.

**Organizers:**
- Florian Pyczak — Helmholtz-Zentrum Hereon, Germany
- Koji Hagihara — Nagoya Institute of Technology, Japan
- Petra Spörk-Erdely — Graz University of Technology, Austria
- Klaus-Dieter Liss — The University of Tennessee, Knoxville, USA

**Best angle to emphasize:**
Frame the doser as an **enabling feedstock-preparation platform for rapid exploration of intermetallic / alloy composition space in additive manufacturing**, especially for aerospace-relevant systems.

### 5) **SF01: Advances in Structural and Functional High-Entropy Materials—Synthesis, Processing and Performance**
**Why this fits:** SF01 is narrower than SF03, but it explicitly mentions **additive manufacturing**, **advanced processing**, and that **AI and high-throughput experimentation are accelerating the discovery of HEMs**. Your repo contains explicit background work on **multi-material/high-throughput metal AM (including HEAs)** and repeatedly positions the powder doser as a tool for rapidly preparing blends across many powders for autonomous alloy discovery. This is a good match if your near-term abstract can credibly center on **compositionally complex alloys / HEM feedstocks** rather than on the dispenser as a general platform.

**Organizers:**
- Punit Kumar — Nanyang Technological University, Singapore
- Irene Beyerlein — University of California, Santa Barbara, USA
- Judith MacManus-Driscoll — University of Cambridge, United Kingdom
- Le Wang — Pacific Northwest National Laboratory, USA

**Best angle to emphasize:**
Submit here only if you can make the story specifically about **high-entropy or compositionally complex alloy feedstock generation** for AM, with the doser presented as the enabling method.

## Secondary / honorable mentions

- **MT02: Accelerating Materials Science with Foundational Models**  
  Good fit for the **agentic / LLM / foundational-model** side of the CAD and workflow story, but less obviously matched to the physical powder-dosing hardware unless the abstract leans heavily into AI methods.

- **CH05: Automated, Intelligent and Autonomous Materials Characterization—From Single Techniques to Integrated Workflows**  
  Relevant because your repo includes **closed-loop gravimetric feedback**, measurement integration, and autonomous control ideas. Still, your center of gravity is synthesis/processing hardware rather than characterization.

- **EN09: Integrating AI and Computational Tools with High-Throughput Experimentation for Energy Materials Research**  
  Methodologically similar to your work, with explicit mention of autonomous experimentation and Bayesian optimization. I rank it lower because your concrete downstream application in the repo is **AM aerospace alloys**, not energy materials.

- **SF04: Materials and Devices in Extreme Environments—Accelerated Discovery and Development**  
  Could work if the abstract is pulled toward **aerospace/extreme-environment alloy development** and AI-enabled accelerated workflows. It is still a stretch unless you have repo-backed results on extreme-environment materials specifically.

## Practical ranking advice

If you want the **best odds of strong reviewer resonance based on what the repo actually documents**, I’d submit in this order:
1. **MT03**
2. **MT01**
3. **MT04**
4. **SF03**
5. **SF01**

My short version: **MT03** is the best target if the abstract centers on the doser as part of a self-driving materials workflow; **MT04** is the best target if you want to sell it as an experimental synthesis-enablement technology; **SF03/SF01** become stronger only if the abstract is anchored to specific alloy/intermetallic/high-entropy feedstock studies rather than to the platform itself.

**Limitations:** I based this ranking on the symposium scope text extracted from the official PDF and on the attached `repo_context.md`. I did not infer unrecorded experimental results; where the repo describes future validation, I treated that as future work and not as completed evidence.

- Parsed the symposium list directly from the attached MRS Fall 2026 Call for Abstracts PDF and ranked symposia by qualitative scope match rather than using any automated similarity score.
- Prioritized symposia that matched documented work in `repo_context.md` over symposia that matched only the broader aspirational application area.
- Ranked AI/autonomous-workflow symposia above alloy-specific symposia because the repo contains stronger concrete evidence for agentic CAD, modular doser design, and closed-loop workflow framing than for completed alloy-specific experimental results.
- Included SF03 and SF01 as top-5 options because the repo explicitly ties the doser to AM aerospace alloy discovery and L-PBF feedstock preparation, even though the project itself is a hardware platform rather than a completed alloy study.
- Demoted EN09 and CH05 to honorable mentions because their methodological overlap is real, but their domain emphasis (energy materials; characterization) is less central to the documented project than autonomous synthesis/workflow and AM alloy feedstock preparation.