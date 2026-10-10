# Generative-CAD Outreach Contacts

> **Scope.** Named individuals, organizations, communities, and funding
> programs the BYU Vertical Cloud Lab can realistically reach out to for
> collaboration, advice, or technical support on **agentic, code-based,
> manufacturability-aware generative CAD** for the powder-doser project.
>
> Resolves issue: *"Determine individuals and organizations we could reach
> out to for help with generative CAD."* Cross-references the generative-CAD
> background pillar in
> [`03-generative-cad-landscape.md`](03-generative-cad-landscape.md),
> [`04-generative-cad-academic-literature.md`](04-generative-cad-academic-literature.md),
> and the spatial-reasoning mitigation synthesis in
> [`05-llm-cad-spatial-reasoning-mitigation.md`](05-llm-cad-spatial-reasoning-mitigation.md);
> see also [PR #7](https://github.com/vertical-cloud-lab/powder-doser/pull/7),
> [PR #27](https://github.com/vertical-cloud-lab/powder-doser/pull/27), and
> [PR #29](https://github.com/vertical-cloud-lab/powder-doser/pull/29).

## Provenance

This file is a lightly-edited rendering of a single Edison Scientific
`LITERATURE_HIGH` (paperqa-class) query dispatched by
[`edison_run_outreach_contacts.py`](edison_run_outreach_contacts.py). The full
prompt is embedded verbatim in the runner; the raw response — including agent
state, contexts, references, cost, and token counts — is committed alongside
this note as
[`edison_artifacts/gencad_outreach_contacts.task.json`](edison_artifacts/gencad_outreach_contacts.task.json)
(plus `.answer.md` and `.references.md` siblings). The query returned
`status=success`.

**Verification policy.** The Edison prompt explicitly forbids fabricating
contact info: where no public personal email is listed in a paper's author-
contact section, the entry uses the lab/organization page or a public social
handle, and says so. Every entry below ends with a `(source: <full URL>)` tag
that points at the public page where the listed contact channel can be
verified by a human before any outreach is sent. **Verify each address /
handle on the source URL before contacting** — academic affiliations and
DevRel ownership change frequently.

**Inline citation keys** of the form `(authorYYYY... pages X-Y)` map to the
[References](#references) section at the bottom of this file, copied verbatim
from `edison_artifacts/gencad_outreach_contacts.references.md`.

## Quick-reference summary table

| Category | Name | Affiliation / Role | Why relevant (1 sentence) | Primary contact channel | Source URL |
|---|---|---|---|---|---|
| Academic CAD-LLM | Rundi Wu | Columbia University, DeepCAD co-author | Co-authored DeepCAD, one of the earliest influential transformer-style generative CAD papers for sequential CAD programs. (wu2021deepcadadeep pages 1-2) | `rundi@cs.columbia.edu` | https://doi.org/10.48550/arxiv.2105.09492 |
| Academic CAD-LLM | Changxi Zheng | Columbia University, DeepCAD senior author | Led the DeepCAD line of work on generative CAD representations and programmatic CAD modeling from human design sequences. (wu2021deepcadadeep pages 1-2) | `cxz@cs.columbia.edu` | https://doi.org/10.48550/arxiv.2105.09492 |
| Academic CAD-LLM | Haoyang Xie | Arizona State University, Text-to-CadQuery co-author | Created Text-to-CadQuery — directly aligned with the lab's need to generate CadQuery code from text using scalable LLMs. (xie2505texttocadqueryanew pages 1-3) | `hxie40@asu.edu` | https://doi.org/10.48550/arxiv.2505.06507 |
| Academic CAD-LLM | Feng Ju | Arizona State University, Text-to-CadQuery co-author | Co-authored Text-to-CadQuery; can advise on LLM fine-tuning and evaluation for executable CadQuery generation. (xie2505texttocadqueryanew pages 1-3) | `fengju@asu.edu` | https://doi.org/10.48550/arxiv.2505.06507 |
| Academic CAD-LLM | Danila Rukhovich | SnT, U. Luxembourg, CAD-Recode lead | CAD-Recode translates point clouds into executable Python CAD code — relevant for reverse-engineering and CAD-edit loops. (rukhovich2025cadrecodereverseengineering pages 1-2) | `danila.rukhovich@uni.lu` | https://doi.org/10.48550/arxiv.2412.14042 |
| Academic CAD-LLM | Djamila Aouada | SnT, U. Luxembourg, CAD-Recode senior author | Leads CAD-Recode work on LLM-mediated CAD reverse engineering, useful for scan-to-edit and model-repair workflows. (rukhovich2025cadrecodereverseengineering pages 1-2) | `djamila.aouada@uni.lu` | https://doi.org/10.48550/arxiv.2412.14042 |
| Academic CAD-LLM | Jesse Barkley | Carnegie Mellon University, CADSmith lead | CADSmith is multi-agent CAD generation with programmatic geometric validation — close match to an agentic manufacturability-aware loop. (barkley2603cadsmithmultiagentcad pages 1-2) | `jabarkle@andrew.cmu.edu` | https://doi.org/10.48550/arxiv.2603.26512 |
| Academic CAD-LLM | Amir Barati Farimani | Carnegie Mellon University, CADSmith senior author | Leads work on multi-agent validated CAD generation, a strong fit for assembly generation with automatic checking. (barkley2603cadsmithmultiagentcad pages 1-2) | `afariman@andrew.cmu.edu` | https://doi.org/10.48550/arxiv.2603.26512 |
| Academic CAD-LLM | Qian Yu | Beihang University, ArtiCAD corresponding author | ArtiCAD targets articulated CAD assembly design via multi-agent code generation — directly relevant for small mechanical assemblies. (shui2026articadarticulatedcad pages 1-3) | `qianyu@buaa.edu.cn` | https://doi.org/10.48550/arxiv.2604.10992 |
| Academic CAD-LLM | Ari Seff | Princeton University, SketchGraphs lead | SketchGraphs is a foundational large-scale dataset for relational geometry in CAD sketches, useful for constraint-aware generation/repair. (seff2020sketchgraphsalargescale pages 1-3) | `aseff@princeton.edu` | https://doi.org/10.48550/arxiv.2007.08506 |
| Academic CAD-LLM | Ryan P. Adams | Princeton University, SketchGraphs senior author | Helped establish one of the key parametric CAD sketch datasets that underpins newer CAD-LLM work. (seff2020sketchgraphsalargescale pages 1-3) | `rpa@princeton.edu` | https://doi.org/10.48550/arxiv.2007.08506 |
| Academic CAD-LLM | Karl D. D. Willis | Autodesk Research, Fusion 360 Gallery lead author | Fusion 360 Gallery is a major dataset/environment for programmatic CAD reconstruction — highly relevant for training and benchmarking. (willis2021fusion360gallery pages 1-2) | `karl.willis@autodesk.com` | https://doi.org/10.1145/3450626.3459818 |
| Academic CAD-LLM | Anna C. Doris | MIT, CAD-Coder lead author | CAD-Coder generates editable CadQuery from visual input — same MIT ecosystem as GenCAD; especially relevant for code-CAD pipelines. (doris2026cadcoderanopensource pages 1-2) | `adoris@mit.edu` | https://doi.org/10.48550/arxiv.2505.14646 |
| Academic CAD-LLM | Faez Ahmed | MIT, GenCAD/CAD-Coder PI | Multiple generative-engineering-design papers (GenCAD, CAD-Coder) spanning feasible CAD generation and design agents. (doris2026cadcoderanopensource pages 1-2) | No public direct email in cited contexts; reach via Anna Doris / MIT DECODE Lab | https://doi.org/10.48550/arxiv.2505.14646 |
| Academic CAD-LLM | Ahmed R. Sadik | Honda Research Institute Europe | Co-author on 2025 quantitative evaluation of LLM-generated 3D/CAD models and on the multi-agent "From Idea to CAD" line. (ocker2503fromideato pages 1-3, sadik2509humanintheloopquantitativeevaluation pages 1-2) | `ahmed.sadik@honda-ri.de` | https://doi.org/10.48550/arxiv.2509.07010 |
| Code-CAD OSS | Adam Urbanczyk | CadQuery maintainer | Core CadQuery maintainer; CadQuery is the most direct OSS target for the lab's LLM-written parametric hardware scripts. | GitHub: `adam-urbanczyk` | https://github.com/adam-urbanczyk |
| Code-CAD OSS | Jeremy Wright | CadQuery maintainer | Long-time CadQuery maintainer and contributor to the Pythonic CAD stack underlying many text-to-CAD papers. | GitHub: `jmwright` | https://github.com/jmwright |
| Code-CAD OSS | Roger Maitland | build123d creator/maintainer | Modern Python parametric CAD library considered alongside CadQuery for code-generation workflows. | GitHub: `gumyr` | https://github.com/gumyr |
| Code-CAD OSS | Marius Kintel | OpenSCAD core developer | OpenSCAD remains a durable text-based CAD backend for generated geometry and manufacturability checks. | GitHub: `kintel` | https://github.com/kintel |
| Code-CAD OSS | Yorik van Havre | FreeCAD core developer | Key FreeCAD developer; FreeCAD offers robust open-source CAD kernels and workbenches relevant for future CAD/CAM. | GitHub: `yorikvanhavre` | https://github.com/yorikvanhavre |
| Commercial | Jessie Frazelle | Zoo.dev / KittyCAD, CEO | Zoo.dev/KittyCAD is one of the few commercial efforts explicitly building text-to-CAD APIs and programmable CAD infrastructure. | GitHub: `jessfraz` · X: `@jessfraz` | https://github.com/jessfraz |
| Commercial | Karl D. D. Willis | Autodesk Research scientist | Closest industrial-scale path to programmatic CAD datasets, CAD-as-program thinking, and Fusion 360 integration. (willis2021fusion360gallery pages 1-2) | `karl.willis@autodesk.com` | https://doi.org/10.1145/3450626.3459818 |
| Commercial | Steve Baer | McNeel / Rhino developer engineering | McNeel is unusually open to community engagement around CAD scripting, geometry kernels, and Grasshopper/Rhino automation. | GitHub: `sbaer` · forum: discourse.mcneel.com | https://github.com/sbaer |
| Commercial | Nick Kallen | Plasticity, founder | Modern direct-modeling CAD tool with growing adoption among technical users doing code-heavy / generative workflows. | X: `@nickkallen` | https://x.com/nickkallen |
| Commercial | Zoo.dev DevRel | Zoo.dev / KittyCAD | Public developer documentation and API access; no individual DevRel email published — use Discord / GitHub issues. | https://zoo.dev/docs · https://discord.gg/zoo-dev | https://zoo.dev/ |
| SDL groups | Alán Aspuru-Guzik | U. Toronto / Acceleration Consortium, Director | Central leader of self-driving labs and autonomous experimentation; clear interest in agent-based scientific workflows. (tom2024selfdrivinglaboratoriesfor pages 86-87) | Acceleration Consortium contact page | https://acceleration.utoronto.ca/ |
| SDL groups | Sterling G. Baird | Acceleration Consortium, Research Scientist | Co-authored the major SDL review and works on practical autonomous materials discovery infrastructure. (tom2024selfdrivinglaboratoriesfor pages 91-92) | GitHub: `sgbaird` · Acceleration Consortium profile | https://acceleration.utoronto.ca/ |
| SDL groups | Andrew I. Cooper | U. Liverpool, Professor | Group is known for autonomous chemistry and mobile robot chemists — useful for end-to-end experimental orchestration ideas. | University profile / lab page | https://www.liverpool.ac.uk/chemistry/staff/andy-cooper/ |
| SDL groups | Lee Cronin | U. Glasgow / Chemify | Chemify is among the clearest examples of digitized, programmable chemistry workflows that can inspire hardware-control abstractions. | Lab/site contact page | https://chemify.io/ |
| SDL groups | Milad Abolhasani | NC State, Associate Professor | Leads autonomous flow chemistry and SDL work with strong engineering emphasis — useful for closed-loop architecture. (tom2024selfdrivinglaboratoriesfor pages 91-92) | Faculty page | https://cbe.ncsu.edu/people/mabolha/ |
| SDL groups | Joshua Schrier | Fordham University, Professor | Active in autonomous chemistry and AI-for-chemistry toolchains; good advisor for small academic-lab strategy and software architecture. | Faculty page | https://www.fordham.edu/academics/departments/chemistry/faculty-and-staff/joshua-schrier/ |
| SDL groups | Keith A. Brown | Boston University, Associate Professor | Brown Lab works on Bayesian self-driving experimentation for mechanics and materials — relevant to closed-loop optimization. | Lab page | https://brownlab.bu.edu/ |
| AM experts | Timothy W. Simpson | Penn State, Paul Morrow Prof.; CIMP-3D leader | Major figure in design for AM and digital design/manufacturing workflows, relevant for manufacturability-aware assembly generation. | Faculty page | https://www.me.psu.edu/department/directory-detail-g.aspx?q=tws8 |
| AM experts | Allison M. Beese | Penn State, Professor | Leading AM/mechanics researcher bridging materials, process constraints, and part performance in additive contexts. | Faculty page | https://www.matse.psu.edu/directory/allison-beese |
| AM experts | Tresa M. Pollock | UCSB, Alcoa Distinguished Professor | High-profile AM and alloy/process expert; valuable for the future L-PBF integration path. | Faculty page | https://www.materials.ucsb.edu/people/faculty/tresa-pollock |
| AM experts | Kenneth S. Vecchio | UCSD, Professor (MAE) | Leads HT-READ and high-throughput experimental alloy work with links to digital metallurgy and AM-oriented research. | Faculty page | https://mae.ucsd.edu/faculty/kenneth-vecchio |
| Communities | CadQuery Discord | CadQuery community server | Best cold-start venue for practical help on CadQuery APIs, OCC issues, exporters, and LLM-generated script debugging. | Public Discord invite (linked from docs) | https://cadquery.readthedocs.io/en/latest/ |
| Communities | build123d Discord | build123d community server | Good venue for rapid feedback on build123d syntax, assemblies, and Pythonic CAD agent tooling. | Public Discord invite (linked from docs) | https://build123d.readthedocs.io/en/latest/ |
| Communities | FreeCAD Forum | FreeCAD community forum | Strong place to ask about kernels, parametric workflows, and interoperability for future CAM/L-PBF paths. | Forum URL | https://forum.freecad.org/ |
| Communities | r/openscad | OpenSCAD subreddit | Useful for script-level CAD questions, printable geometry, and fast feedback from hobbyist and expert users. | Subreddit | https://www.reddit.com/r/openscad/ |
| Communities | Self-Driving Labs community | SDL practitioners' community | Good cold-post venue for lab orchestration, automation software, and agent-in-the-loop experimentation questions. | Community page / invite | https://selfdrivinglabs.org/ |
| Communities | ASME IDETC-CIE | ASME conference | Practical venue for design automation, CAD, and engineering AI work with publication and networking value. | Conference page | https://event.asme.org/IDETC-CIE |
| Communities | SCF | Symposium on Computational Fabrication | Highly relevant academic venue for geometry/fabrication workflows between CAD generation and manufacturing. | Conference page | https://www.compfab.org/ |
| Communities | CAD'25 | CAD Conference | Dedicated CAD conference where generative CAD, datasets, and engineering AI are realistic outreach targets. | Conference page | https://cad-conference.net/ |
| Funding | NSF DMREF | NSF program | Natural NSF home for autonomous alloy-discovery infrastructure linking design, materials, and manufacturing. | Program page | https://www.nsf.gov/funding/opportunities/dmref-designing-materials-revolutionize-engineer-our-future |
| Funding | NSF Future Manufacturing | NSF program | Strong fit for intelligent design-to-manufacturing workflows and academic cyber-physical manufacturing research. | Program page | https://new.nsf.gov/funding/opportunities/future-manufacturing-fm |
| Funding | ARPA-E DIFFERENTIATE | ARPA-E program | Relevant model for AI-assisted engineering design and optimization program framing. | Program page | https://arpa-e.energy.gov/technologies/programs/differentiate |
| Funding | America Makes | National AM innovation institute | Best practical U.S. manufacturing-institute contact for AM transition, industrial partners, and design-for-AM advice. | Contact / program page | https://www.americamakes.us/ |
| Funding | Acceleration Consortium | U. Toronto-led research/funding ecosystem | Natural partner for small academic teams building autonomous discovery infrastructure spanning agents, robotics, and materials. | Program / community page | https://acceleration.utoronto.ca/ |

---

## 1. Academic CAD-LLM / Generative-CAD Researchers

### Rundi Wu

Columbia University, PhD researcher. First author of **DeepCAD** (ICCV 2021), one of the earliest and most cited transformer-based generative CAD models, which represents shapes as sequences of CAD operations. Directly relevant for programmatic CAD representation design. Email: `rundi@cs.columbia.edu` (listed in paper header). (source: https://doi.org/10.48550/arxiv.2105.09492) (wu2021deepcadadeep pages 1-2)

### Changxi Zheng

Columbia University, Professor. Senior author and PI on the DeepCAD line of work. Email: `cxz@cs.columbia.edu` (listed in paper header). (source: https://doi.org/10.48550/arxiv.2105.09492) (wu2021deepcadadeep pages 1-2)

### Haoyang Xie

Arizona State University, School of Computing and Augmented Intelligence. First author of **Text-to-CadQuery**, which is directly aligned with the lab's need: fine-tuning LLMs to generate executable CadQuery Python code from natural language descriptions, with a 170K annotation dataset. GitHub repo: https://github.com/Text-to-CadQuery/Text-to-CadQuery. Email: `hxie40@asu.edu` (listed in paper header). (source: https://doi.org/10.48550/arxiv.2505.06507) (xie2505texttocadqueryanew pages 1-3)

### Feng Ju

Arizona State University. Co-author on Text-to-CadQuery; can advise on LLM fine-tuning and evaluation for CadQuery generation. Email: `fengju@asu.edu` (listed in paper header). (source: https://doi.org/10.48550/arxiv.2505.06507) (xie2505texttocadqueryanew pages 1-3)

### Danila Rukhovich

SnT, University of Luxembourg. First author of **CAD-Recode**, which translates point clouds into executable Python CAD code by fine-tuning an LLM decoder — relevant for scan-to-edit and model-repair workflows. Email: `danila.rukhovich@uni.lu` (listed in paper header). (source: https://doi.org/10.48550/arxiv.2412.14042) (rukhovich2025cadrecodereverseengineering pages 1-2)

### Djamila Aouada

SnT, University of Luxembourg, Professor. Senior author on CAD-Recode; leads LLM-mediated CAD reverse-engineering research. Email: `djamila.aouada@uni.lu` (listed in paper header). (source: https://doi.org/10.48550/arxiv.2412.14042) (rukhovich2025cadrecodereverseengineering pages 1-2)

### Jesse Barkley

Carnegie Mellon University, Department of Mechanical Engineering. First author of **CADSmith**, a multi-agent CAD generation pipeline with programmatic geometric validation — closely matching an agentic, manufacturability-aware design loop. Email: `jabarkle@andrew.cmu.edu` (listed in paper header). (source: https://doi.org/10.48550/arxiv.2603.26512) (barkley2603cadsmithmultiagentcad pages 1-2)

### Amir Barati Farimani

Carnegie Mellon University, Professor. Senior author on CADSmith; leads the lab where multi-agent validated CAD generation was developed. Email: `afariman@andrew.cmu.edu` (listed in paper header). (source: https://doi.org/10.48550/arxiv.2603.26512) (barkley2603cadsmithmultiagentcad pages 1-2)

### Qian Yu

Beihang University, School of Software. Corresponding author on **ArtiCAD**, which targets articulated CAD assembly design via multi-agent code generation — directly relevant for mechanical assemblies rather than single parts. Project page: https://shui-yuan.github.io/articad/. Email: `qianyu@buaa.edu.cn` (listed in paper header). (source: https://doi.org/10.48550/arxiv.2604.10992) (shui2026articadarticulatedcad pages 1-3)

### Ari Seff

Princeton University. First author of **SketchGraphs**, a foundational dataset of 15 million parametric CAD sketches with geometric constraints, useful for constraint-aware CAD generation and repair. Email: `aseff@princeton.edu` (listed in paper header). (source: https://doi.org/10.48550/arxiv.2007.08506) (seff2020sketchgraphsalargescale pages 1-3)

### Ryan P. Adams

Princeton University, Professor. Senior author on SketchGraphs and PI of the Laboratory for Intelligent Probabilistic Systems. Email: `rpa@princeton.edu` (listed in paper header). (source: https://doi.org/10.48550/arxiv.2007.08506) (seff2020sketchgraphsalargescale pages 1-3)

### Karl D. D. Willis

Autodesk Research, USA. Lead author of the **Fusion 360 Gallery** dataset and environment for programmatic CAD reconstruction from human design sequences (8,625 models), a key benchmark in the field. Email: `karl.willis@autodesk.com` (listed in paper header). (source: https://doi.org/10.1145/3450626.3459818) (willis2021fusion360gallery pages 1-2)

### Faez Ahmed

MIT, Department of Mechanical Engineering, Professor. PI on the **GenCAD** and **CAD-Coder** lines of work, spanning image-conditioned CAD generation, CadQuery code output, and agentic engineering design. No public direct email found in cited papers; reachable via group members (e.g., Anna Doris at `adoris@mit.edu`) and the MIT DECODE Lab page. (source: https://doi.org/10.48550/arxiv.2505.14646) (doris2026cadcoderanopensource pages 1-2)

### Anna C. Doris

MIT. First author of **CAD-Coder**, an open-source VLM fine-tuned to generate editable CadQuery code from images, with a 163K-pair dataset (GenCAD-Code). GitHub: https://github.com/anniedoris/CAD-Coder. Email: `adoris@mit.edu` (listed in paper header). (source: https://doi.org/10.48550/arxiv.2505.14646) (doris2026cadcoderanopensource pages 1-2)

### Ahmed R. Sadik

Honda Research Institute Europe, Offenbach, Germany. Corresponding author on a 2025 paper quantitatively evaluating LLM-generated 3D CAD models and co-author of "From Idea to CAD" (multi-agent collaborative design). Email: `ahmed.sadik@honda-ri.de` (listed in paper header). (source: https://doi.org/10.48550/arxiv.2509.07010) (sadik2509humanintheloopquantitativeevaluation pages 1-2)

---

## 2. Code-CAD / Programmatic-CAD Open-Source Maintainers

### Adam Urbanczyk

Core maintainer of **CadQuery**, the Python parametric CAD library that is the most common target for LLM-generated CAD code. CadQuery sits on top of OpenCASCADE (OCCT) and is explicitly used by Text-to-CadQuery, CAD-Recode, CADSmith, and many other papers listed above. GitHub: `adam-urbanczyk`. Discord: CadQuery has a Discord linked from its documentation. (source: https://github.com/CadQuery/cadquery)

### Jeremy Wright

Long-time CadQuery co-maintainer and contributor to the broader Pythonic CAD ecosystem. GitHub: `jmwright`. (source: https://github.com/jmwright)

### Roger Maitland

Creator and primary maintainer of **build123d**, a modern Python parametric CAD library that is increasingly considered alongside CadQuery for code-generation workflows, with a cleaner builder-pattern API. GitHub: `gumyr`. Discord: build123d has a Discord linked from its ReadTheDocs. (source: https://github.com/gumyr/build123d)

### Marius Kintel

Core developer of **OpenSCAD**, the original text-based CSG CAD tool that remains a durable backend for generated geometry. GitHub: `kintel`. (source: https://github.com/openscad/openscad)

### Yorik van Havre

Core developer of **FreeCAD**, a major open-source parametric CAD platform. FreeCAD's robust CAD kernel and workbenches are relevant for future CAD/CAM integration. GitHub: `yorikvanhavre`. Community forum: https://forum.freecad.org/. (source: https://github.com/yorikvanhavre)

---

## 3. Commercial Generative-Design / CAD-API Contacts

### Jessie Frazelle

CEO of **Zoo.dev** (formerly KittyCAD). Zoo.dev is one of the few companies explicitly building a text-to-CAD API and programmable CAD infrastructure, with an open-source geometry engine (KittyCAD engine). Highly relevant for API-driven CAD generation. GitHub: `jessfraz`. X/Twitter: `@jessfraz`. (source: https://github.com/jessfraz)

### Karl D. D. Willis

Autodesk Research (also listed in §1). Can connect to Autodesk's broader research group working on CAD-as-program, generative design, and the Fusion 360 ecosystem. Email: `karl.willis@autodesk.com` (listed in paper header). (source: https://doi.org/10.1145/3450626.3459818) (willis2021fusion360gallery pages 1-2)

### Steve Baer

Robert McNeel & Associates (**Rhino/Grasshopper**), developer relations and engineering lead. McNeel is notably open to developer engagement around CAD scripting (RhinoCommon, Grasshopper) and geometry kernels. GitHub: `sbaer`. Rhino developer forum: https://discourse.mcneel.com/. (source: https://github.com/sbaer)

### Nick Kallen

Founder of **Plasticity**, a modern direct-modeling CAD tool with growing adoption among technical users doing code-heavy and generative workflows. No public email found; reachable via X/Twitter: `@nickkallen`. (source: https://x.com/nickkallen)

### Zoo.dev developer relations

In addition to Jessie Frazelle personally, Zoo.dev maintains public developer documentation and API access at https://zoo.dev/docs. No individual DevRel email published; use their Discord or GitHub issues. (source: https://zoo.dev/)

---

## 4. Self-Driving-Lab / Agentic-Hardware Groups

### Alán Aspuru-Guzik

University of Toronto, Professor; Director of the **Acceleration Consortium**. Co-authored the landmark "Self-Driving Laboratories for Chemistry and Materials Science" review (Chemical Reviews, 2024) and leads multiple agent-based experimental automation efforts. Lab/consortium page: https://acceleration.utoronto.ca/. No public direct email found; reachable via the Acceleration Consortium contact page. (source: https://acceleration.utoronto.ca/) (tom2024selfdrivinglaboratoriesfor pages 86-87)

### Sterling G. Baird

Acceleration Consortium, Research Scientist. Co-authored the SDL review with Aspuru-Guzik and works on practical autonomous materials discovery infrastructure. GitHub: `sgbaird`. Reachable via Acceleration Consortium profile. (source: https://acceleration.utoronto.ca/) (tom2024selfdrivinglaboratoriesfor pages 91-92)

### Andrew I. Cooper

University of Liverpool, Professor. Known for mobile robot chemists and autonomous chemistry platforms. Lab page: https://www.liverpool.ac.uk/chemistry/staff/andy-cooper/. Contact via university page. (source: https://www.liverpool.ac.uk/chemistry/staff/andy-cooper/)

### Lee Cronin

University of Glasgow, Professor; co-founder of **Chemify**. Develops digitized, programmable chemistry workflows — a conceptual model for hardware-control abstractions in self-driving labs. Chemify site: https://chemify.io/. University page: https://www.gla.ac.uk/schools/chemistry/staff/leecronin/. (source: https://chemify.io/)

### Milad Abolhasani

North Carolina State University, Associate Professor, Department of Chemical and Biomolecular Engineering. Leads autonomous flow chemistry and Pareto-front mapping with self-driving catalysis labs. Faculty page: https://cbe.ncsu.edu/people/mabolha/. (source: https://cbe.ncsu.edu/people/mabolha/) (tom2024selfdrivinglaboratoriesfor pages 91-92)

### Joshua Schrier

Fordham University, Professor. Active in autonomous chemistry and AI-for-chemistry; a practical advisor for small academic-lab strategy and software architecture for SDLs. Faculty page: https://www.fordham.edu/academics/departments/chemistry/faculty-and-staff/joshua-schrier/. (source: https://www.fordham.edu/academics/departments/chemistry/faculty-and-staff/joshua-schrier/)

### Keith A. Brown

Boston University, Associate Professor. Leads the Brown Lab working on Bayesian self-driving experimentation for mechanics and materials, relevant to closed-loop optimization with physical hardware. Lab page: https://brownlab.bu.edu/. (source: https://brownlab.bu.edu/)

---

## 5. Additive-Manufacturing + Design-for-AM Experts

### Timothy W. Simpson

Penn State University, Paul Morrow Professor of Engineering Design and Manufacturing. Leads CIMP-3D and has extensive work on design for AM, topology optimization, and digital design/manufacturing integration. Faculty page: https://www.me.psu.edu/department/directory-detail-g.aspx?q=tws8. (source: https://www.me.psu.edu/department/directory-detail-g.aspx?q=tws8)

### Allison M. Beese

Penn State University, Professor. Bridges materials science, process constraints, and AM part performance — important for understanding manufacturability constraints in L-PBF. Faculty page: https://www.matse.psu.edu/directory/allison-beese. (source: https://www.matse.psu.edu/directory/allison-beese)

### Tresa M. Pollock

University of California, Santa Barbara, Alcoa Distinguished Professor. High-profile AM and alloy/process expert; valuable for L-PBF integration paths and alloy discovery collaborations. Faculty page: https://www.materials.ucsb.edu/people/faculty/tresa-pollock. (source: https://www.materials.ucsb.edu/people/faculty/tresa-pollock)

### Kenneth S. Vecchio

University of California, San Diego, Professor, MAE Department. Leads advanced materials and high-throughput experimental alloy work (HT-READ), with links to digital metallurgy and AM-oriented research. Faculty page: https://mae.ucsd.edu/faculty/kenneth-vecchio. (source: https://mae.ucsd.edu/faculty/kenneth-vecchio)

---

## 6. Communities, Discords, Forums, and Conferences

### CadQuery Discord

The primary real-time community for CadQuery users and developers. Best cold-start venue for help on CadQuery APIs, OpenCASCADE issues, exporters, and debugging LLM-generated scripts. Invite link available from the docs landing page. (source: https://cadquery.readthedocs.io/en/latest/)

### build123d Discord

Community server for build123d users. Good for rapid feedback on build123d syntax, assembly APIs, and Pythonic CAD agent tooling. Invite link available from the docs landing page. (source: https://build123d.readthedocs.io/en/latest/)

### FreeCAD Forum

Active community forum for FreeCAD users and developers; strong for questions about parametric workflows, kernels, and future CAM/L-PBF integration. (source: https://forum.freecad.org/)

### OpenSCAD subreddit (r/openscad)

Useful for script-level CAD questions, printable geometry feedback, and rapid community input. (source: https://www.reddit.com/r/openscad/)

### Self-Driving Labs community

Community site and resources for autonomous/self-driving laboratory practitioners, including a community Discord. (source: https://selfdrivinglabs.org/)

### ASME IDETC-CIE

The ASME International Design Engineering Technical Conferences and Computers and Information in Engineering Conference. Practical venue for presenting design automation, CAD, and engineering AI work with publication and networking value. (source: https://event.asme.org/IDETC-CIE)

### SCF (Symposium on Computational Fabrication)

Academic venue directly targeting geometry/fabrication workflows between CAD generation and manufacturing. (source: https://www.compfab.org/)

### CAD Conference (CAD'25)

Dedicated computer-aided design conference where generative CAD, datasets, and engineering AI presentations are well-received. (source: https://cad-conference.net/)

---

## 7. Funding Programs and Program Officers

### NSF DMREF (Designing Materials to Revolutionize and Engineer our Future)

One of the most natural NSF homes for autonomous alloy-discovery infrastructure linking design, materials, and manufacturing. Supports integrated computational/experimental materials research. (source: https://www.nsf.gov/funding/opportunities/dmref-designing-materials-revolutionize-engineer-our-future)

### NSF Future Manufacturing

Strong fit for intelligent design-to-manufacturing workflows and academic cyber-physical manufacturing research, especially for small teams building novel automation. (source: https://new.nsf.gov/funding/opportunities/future-manufacturing-fm)

### ARPA-E DIFFERENTIATE

ARPA-E program supporting AI-assisted engineering design and optimization. While broader than CAD, the program framing aligns well with agentic design-to-manufacturing workflows. (source: https://arpa-e.energy.gov/technologies/programs/differentiate)

### America Makes

The U.S. national additive manufacturing innovation institute. Best practical contact for AM transition, industrial partners, design-for-AM tooling, and workforce development. (source: https://www.americamakes.us/)

### Acceleration Consortium

University of Toronto-led research and funding ecosystem for autonomous scientific discovery. Natural partner for small academic teams building agent-driven discovery infrastructure spanning robotics, materials, and software. (source: https://acceleration.utoronto.ca/)

---

**Note on contact verification.** All individual email addresses listed above
were extracted directly from the author-contact sections of the cited
publications (`willis2021fusion360gallery pages 1-2`,
`sadik2509humanintheloopquantitativeevaluation pages 1-2`, etc.). GitHub
handles and community URLs are from the respective public project
repositories. For individuals where no personal email was located in the
retrieved documents, the lab/organization-level contact page is provided. **No
email addresses have been fabricated.** Verify current availability before
sending; academic affiliations and DevRel ownership change frequently.

## References

1. (wu2021deepcadadeep pages 1-2): Rundi Wu, Chang Xiao, and Changxi Zheng. *DeepCAD: a deep generative network for computer-aided design models.* 2021 IEEE/CVF International Conference on Computer Vision (ICCV), pages 6752-6762, May 2021. https://doi.org/10.48550/arxiv.2105.09492. 419 citations.

2. (xie2505texttocadqueryanew pages 1-3): Haoyang Xie and Feng Ju. *Text-to-CadQuery: a new paradigm for CAD generation with scalable large model capabilities.* arXiv, 2025. https://doi.org/10.48550/arxiv.2505.06507. 29 citations.

3. (rukhovich2025cadrecodereverseengineering pages 1-2): Danila Rukhovich, Elona Dupont, Dimitrios Mallis, Kseniya Cherenkova, Anis Kacem, and Djamila Aouada. *CAD-Recode: reverse engineering CAD code from point clouds.* arXiv, 2025. https://doi.org/10.48550/arxiv.2412.14042. 51 citations.

4. (barkley2603cadsmithmultiagentcad pages 1-2): Jesse Barkley, Rumi Loghmani, and A. Farimani. *CADSmith: multi-agent CAD generation with programmatic geometric validation.* arXiv. https://doi.org/10.48550/arxiv.2603.26512.

5. (shui2026articadarticulatedcad pages 1-3): Yuan Shui, Y. Guan, Zhan Zhang, Juncheng Hu, Jing Zhang, Dong Xu, and Qian Yu. *ArtiCAD: articulated CAD assembly design via multi-agent code generation.* arXiv. https://doi.org/10.48550/arxiv.2604.10992.

6. (seff2020sketchgraphsalargescale pages 1-3): Ari Seff, Yaniv Ovadia, Wenda Zhou, and Ryan P. Adams. *SketchGraphs: a large-scale dataset for modeling relational geometry in computer-aided design.* Preprint, Jan 2020. https://doi.org/10.48550/arxiv.2007.08506. 126 citations.

7. (willis2021fusion360gallery pages 1-2): Karl D. D. Willis, Yewen Pu, Jieliang Luo, Hang Chu, Tao Du, Joseph G. Lambourne, Armando Solar-Lezama, and Wojciech Matusik. *Fusion 360 Gallery.* ACM Transactions on Graphics, 40:1-24, Jul 2021. https://doi.org/10.1145/3450626.3459818. 340 citations.

8. (doris2026cadcoderanopensource pages 1-2): Anna C. Doris, Md Ferdous Alam, A. Nobari, and Faez Ahmed. *CAD-Coder: an open-source vision-language model for computer-aided design code generation.* arXiv, 2025. https://doi.org/10.48550/arxiv.2505.14646. 33 citations.

9. (ocker2503fromideato pages 1-3): Felix Ocker, Stefan Menzel, Ahmed Sadik, and Thiago Rios. *From idea to CAD: a language model-driven multi-agent system for collaborative design.* arXiv, 2025. https://doi.org/10.48550/arxiv.2503.04417. 24 citations.

10. (sadik2509humanintheloopquantitativeevaluation pages 1-2): Ahmed R. Sadik and M. Bujny. *Human-in-the-loop: quantitative evaluation of 3D models generation by large language models.* arXiv, 2025. https://doi.org/10.48550/arxiv.2509.07010. 2 citations.

11. (tom2024selfdrivinglaboratoriesfor pages 86-87, 91-92): Gary Tom, Stefan P. Schmid, Sterling G. Baird, Yang Cao, Kourosh Darvish, Han Hao, Stanley Lo, Sergio Pablo-García, Ella M. Rajaonson, Marta Skreta, Naruki Yoshikawa, Samantha Corapi, Gun Deniz Akkoc, Felix Strieth-Kalthoff, Martin Seifrid, and Alán Aspuru-Guzik. *Self-driving laboratories for chemistry and materials science.* Chemical Reviews, 124:9633-9732, Aug 2024. https://doi.org/10.1021/acs.chemrev.4c00055. 686 citations.
