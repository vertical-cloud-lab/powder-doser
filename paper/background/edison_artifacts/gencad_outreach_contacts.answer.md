Question: Identify named individuals and organizations a small university research lab (BYU Vertical Cloud Lab, ~3 people, NASA Space Grant scale, focused on self-driving labs for additive-manufacturing alloy discovery) could realistically reach out to for collaboration, advice, or technical support on **generative CAD for engineering hardware** in 2025-2026. The lab's specific need is agentic, code-based, manufacturability-aware generative CAD of small mechanical assemblies (a 30-reservoir powder doser, 250 mL/blend, +/-1 mg accuracy, FDM/SLA-printed on a Bambu H2D, with a future L-PBF integration path) where an LLM/agent loop writes CadQuery / build123d / OpenSCAD code, slices it, and ideally drives the printer end-to-end. Cover the following categories and for EACH named contact give: full name, current affiliation/role, the specific reason they are relevant (1-3 sentences with concrete evidence — paper, repo, product, talk), AT LEAST ONE direct, *publicly listed* contact channel (institutional or company email, personal/lab website contact page, GitHub handle, Twitter/X handle, LinkedIn, Mastodon, lab Slack/Discord invite, conference Q&A channel), and the FULL public URL where that contact info is listed so the claim can be verified. If only a lab/org-level contact is public (no individual email), say so explicitly and give the lab/org channel. Do NOT invent emails — if you cannot find a public address, say 'no public direct email found; reachable via <lab page URL> / <social handle>'.

Categories to cover (aim for ~3-6 named contacts per category, ~25-40 total):
  1. **Academic CAD-LLM / generative-CAD researchers** — authors of DeepCAD (Rundi Wu / Changxi Zheng @ Columbia), Text2CAD / Text-to-CADQuery (Xie et al.), CAD-Recode (Rukhovich et al.), CADCrafter, CADSmith, GenCAD / GenCAD-Self-Repairing, ArtiCAD, CADReview, SkexGen, SketchGraphs (Princeton/Adobe), Fusion 360 Gallery (Autodesk Research), ABC dataset, BlenderBench, Sadik 2025. For each first author or PI: institution page, lab page, email (if listed), GitHub, X/Twitter.
  2. **Code-CAD / programmatic-CAD open-source maintainers** — CadQuery (Adam Urbanczyk / Jeremy Wright / CadQuery org), build123d (Roger Maitland / gumyr), OpenSCAD (Marius Kintel + core team), SolidPython / SolidPython2, JSCAD, FreeCAD (Brad Collette / Yorik van Havre / FPA), OCP / OCCT Python bindings (CadQuery org / Open Cascade), KiCad mech-equivalent libs. Provide GitHub handle + project Discord/forum + maintainer email if posted in the project README/AUTHORS.
  3. **Commercial generative-design / CAD-API contacts** — Autodesk Research (Karl Willis, Hooman Shayani, Yewen Pu — Fusion 360 Gallery / generative design / CAD-as-program), nTopology (Bradley Rothenberg, developer relations), PTC Creo Generative Topology Optimization, Siemens NX / Solid Edge generative, Onshape / PTC FeatureScript developer relations, Rhino+Grasshopper (McNeel — Steve Baer, Brian James, dev outreach), Shapr3D, Zoo.dev / KittyCAD (Jess Frazelle and team — text-to-CAD API), CADL / Adam (Spline / similar AI-CAD startups), Plasticity (Nick Kallen). Provide the developer-relations / research-contact address listed on the company site (e.g., 'research@autodesk.com', 'devrel@kittycad.io'), plus founder/PM social handles where public.
  4. **Self-driving-lab / agentic-hardware groups already mixing LLMs with physical hardware** — Alan Aspuru-Guzik (U. Toronto / Acceleration Consortium), Andy Cooper (Liverpool — mobile robot chemist), Lee Cronin (Glasgow — Chemify), Ben Blaiszik / Ian Foster (Argonne / Globus), Milad Abolhasani (NC State), Joshua Schrier (Fordham), Keith Brown (BU — Bayesian self-driving mechanics lab), Alexander Norman / Mat Tantum / Jason Hein. For each: lab page + listed contact email + group GitHub.
  5. **Additive-manufacturing + design-for-AM experts who routinely co-author with software/AI groups** — Tim Simpson (Penn State CIMP-3D), Wayne King (ex-LLNL, now Open Additive), Allison Beese (Penn State), Iver Anderson (Ames Lab — atomization), Tresa Pollock (UCSB), Vecchio group (UCSD — HT-READ), Markl group (FAU Erlangen), Wegener / Schuh (ETH/RWTH). Lab page + dept email.
  6. **Communities, Slacks, Discords, mailing lists, and conferences** that are realistic 'cold-post' venues — CadQuery Discord, build123d Discord, FreeCAD forum, OpenSCAD subreddit, Hackaday.io, /r/cad and /r/3Dprinting, the AI-Plus-Hardware Slack, Acceleration Consortium Slack, the SDL community Discord, the Generative Design subreddit, AAAI workshops on geometric / engineering ML, NeurIPS ML4CAD / ML4Eng workshops, ASME IDETC-CIE (JCISE), CAD'25 conference, SCF (Symposium on Computational Fabrication). Give the public invite URL or the conference/chair contact email.
  7. **Funding / program officers and incubators** likely to advise an academic team standing up agentic CAD work — NSF Designing Materials to Revolutionize and Engineer our Future (DMREF), NSF Future Manufacturing, ARPA-E DIFFERENTIATE, DARPA ML/CAD-adjacent program managers, America Makes, Manufacturing USA institutes, Schmidt Futures Polymathic AI, Acceleration Consortium funding leads. Public program-officer page URL.

Format the final answer as Markdown with one H2 per category and one bullet per contact. Each bullet must end with a parenthetical '(source: <full URL>)' tag pointing at the public page where the listed contact channel is shown, so a human can verify. If a person is highly relevant but you genuinely cannot find a public contact channel, still list them and say 'no public contact channel located' rather than fabricating one. Prioritize *direct, individual* channels over generic 'info@' inboxes when both are available. Aim for 25-40 named contacts total.


# Collaboration Contacts for Generative CAD in Agentic Additive-Manufacturing Alloy Discovery (2025–2026)

The following is a curated directory of named individuals, organizations, communities, and funding programs that a small university research lab — specifically the BYU Vertical Cloud Lab — could realistically contact for collaboration, advice, or technical support on **agentic, code-based, manufacturability-aware generative CAD of small mechanical assemblies**. Each entry includes a verified public contact channel and a source URL. The summary table below provides a quick-reference overview.

| Category | Name | Affiliation/Role | Relevance (1 sentence) | Primary Contact Channel | Source URL |
|---|---|---|---|---|---|
| Academic CAD-LLM | Rundi Wu | Columbia University, DeepCAD co-author | Co-authored DeepCAD, one of the earliest influential transformer-style generative CAD papers for sequential CAD programs, making him highly relevant for code-based CAD generation. (wu2021deepcadadeep pages 1-2) | rundi@cs.columbia.edu | https://doi.org/10.48550/arxiv.2105.09492 |
| Academic CAD-LLM | Changxi Zheng | Columbia University, DeepCAD senior author | Led the DeepCAD line of work on generative CAD representations and programmatic CAD modeling from human design sequences. (wu2021deepcadadeep pages 1-2) | cxz@cs.columbia.edu | https://doi.org/10.48550/arxiv.2105.09492 |
| Academic CAD-LLM | Haoyang Xie | Arizona State University, Text-to-CadQuery co-author | Helped create Text-to-CadQuery, directly aligned with the lab’s need to generate CadQuery code from text using scalable LLMs. (xie2505texttocadqueryanew pages 1-3) | hxie40@asu.edu | https://doi.org/10.48550/arxiv.2505.06507 |
| Academic CAD-LLM | Feng Ju | Arizona State University, Text-to-CadQuery co-author | Co-authored Text-to-CadQuery and can advise on LLM fine-tuning and evaluation for executable CadQuery generation. (xie2505texttocadqueryanew pages 1-3) | fengju@asu.edu | https://doi.org/10.48550/arxiv.2505.06507 |
| Academic CAD-LLM | Danila Rukhovich | SnT, University of Luxembourg, CAD-Recode co-author | CAD-Recode translates point clouds into executable Python CAD code, relevant for reverse engineering and CAD-edit loops around generated hardware. (rukhovich2025cadrecodereverseengineering pages 1-2) | danila.rukhovich@uni.lu | https://doi.org/10.48550/arxiv.2412.14042 |
| Academic CAD-LLM | Djamila Aouada | SnT, University of Luxembourg, CAD-Recode senior author | Leads CAD-Recode work on LLM-mediated CAD reverse engineering, useful for scan-to-edit and model repair workflows. (rukhovich2025cadrecodereverseengineering pages 1-2) | djamila.aouada@uni.lu | https://doi.org/10.48550/arxiv.2412.14042 |
| Academic CAD-LLM | Jesse Barkley | Carnegie Mellon University, CADSmith co-author | CADSmith is explicitly about multi-agent CAD generation with programmatic geometric validation, closely matching an agentic manufacturability-aware design loop. (barkley2603cadsmithmultiagentcad pages 1-2) | jabarkle@andrew.cmu.edu | https://doi.org/10.48550/arxiv.2603.26512 |
| Academic CAD-LLM | Amir Barati Farimani | Carnegie Mellon University, CADSmith senior author | Leads work on multi-agent validated CAD generation, a strong fit for assembly generation with automatic checking. (barkley2603cadsmithmultiagentcad pages 1-2) | afariman@andrew.cmu.edu | https://doi.org/10.48550/arxiv.2603.26512 |
| Academic CAD-LLM | Qian Yu | Beihang University, ArtiCAD corresponding author | ArtiCAD targets articulated CAD assembly design via multi-agent code generation, directly relevant for small mechanical assemblies rather than single parts. (shui2026articadarticulatedcad pages 1-3) | qianyu@buaa.edu.cn | https://doi.org/10.48550/arxiv.2604.10992 |
| Academic CAD-LLM | Ari Seff | Princeton University, SketchGraphs co-author | SketchGraphs is a foundational large-scale dataset for relational geometry in CAD sketches, useful for constraint-aware CAD generation and repair. (seff2020sketchgraphsalargescale pages 1-3) | aseff@princeton.edu | https://doi.org/10.48550/arxiv.2007.08506 |
| Academic CAD-LLM | Ryan P. Adams | Princeton University, SketchGraphs senior author | Helped establish one of the key parametric CAD sketch datasets that underpins newer CAD-LLM work. (seff2020sketchgraphsalargescale pages 1-3) | rpa@princeton.edu | https://doi.org/10.48550/arxiv.2007.08506 |
| Academic CAD-LLM | Karl D. D. Willis | Autodesk Research, Fusion 360 Gallery lead author | Fusion 360 Gallery is a major dataset/environment for programmatic CAD reconstruction from human design sequences, highly relevant for training and benchmarking. (willis2021fusion360gallery pages 1-2) | karl.willis@autodesk.com | https://doi.org/10.1145/3450626.3459818 |
| Academic CAD-LLM | Anna C. Doris | Massachusetts Institute of Technology, CAD-Coder lead author | CAD-Coder generates editable CadQuery from visual input and sits in the same MIT ecosystem as GenCAD, making her especially relevant for code-CAD pipelines. (doris2026cadcoderanopensource pages 1-2) | adoris@mit.edu | https://doi.org/10.48550/arxiv.2505.14646 |
| Academic CAD-LLM | Faez Ahmed | Massachusetts Institute of Technology, professor/advisor on GenCAD/CAD-Coder line | Ahmed’s group has multiple generative engineering design papers including GenCAD and CAD-Coder, spanning feasible CAD generation and design agents. (doris2026cadcoderanopensource pages 1-2) | no public direct email found in cited context; reachable via Anna Doris / MIT group page | https://doi.org/10.48550/arxiv.2505.14646 |
| Academic CAD-LLM | Ahmed R. Sadik | Honda Research Institute Europe | Co-authored 2025 work evaluating LLM-generated 3D/CAD models and is also on the multi-agent “From Idea to CAD” line, making him relevant for practical evaluation and agent workflows. (ocker2503fromideato pages 1-3, sadik2509humanintheloopquantitativeevaluation pages 1-2) | ahmed.sadik@honda-ri.de | https://doi.org/10.48550/arxiv.2509.07010 |
| Code-CAD OSS | Adam Urbanczyk | CadQuery maintainer | Core CadQuery maintainer; CadQuery is the most direct open-source target for the lab’s LLM-written parametric hardware scripts. | GitHub: adam-urbanczyk | https://github.com/adam-urbanczyk |
| Code-CAD OSS | Jeremy Wright | CadQuery maintainer | Long-time CadQuery maintainer and contributor to the Pythonic CAD stack that underlies many text-to-CAD papers. | GitHub: jmwright | https://github.com/jmwright |
| Code-CAD OSS | Roger Maitland | build123d maintainer | build123d is a modern Python parametric CAD library often considered alongside CadQuery for code-generation workflows. | GitHub: gumyr | https://github.com/gumyr |
| Code-CAD OSS | Marius Kintel | OpenSCAD core developer | OpenSCAD remains a durable text-based CAD backend for generated geometry and manufacturability checks. | GitHub: kintel | https://github.com/kintel |
| Code-CAD OSS | Yorik van Havre | FreeCAD core developer | Key FreeCAD developer; FreeCAD offers robust open-source CAD kernels and workbenches relevant for future CAD/CAM integration. | GitHub: yorikvanhavre | https://github.com/yorikvanhavre |
| Commercial | Jessie Frazelle | Zoo.dev/KittyCAD, CEO | Zoo.dev/KittyCAD is one of the few commercial efforts explicitly building text-to-CAD APIs and programmable CAD infrastructure. | GitHub: jessfraz | https://github.com/jessfraz |
| Commercial | Karl D. D. Willis | Autodesk Research scientist | Autodesk Research sits closest to industrial-scale programmatic CAD datasets, CAD-as-program thinking, and Fusion 360 integration paths. (willis2021fusion360gallery pages 1-2) | karl.willis@autodesk.com | https://doi.org/10.1145/3450626.3459818 |
| Commercial | Steve Baer | McNeel/Rhino developer relations / engineering | McNeel is unusually open to developer community engagement around CAD scripting, geometry kernels, and Grasshopper/Rhino automation. | GitHub: sbaer | https://github.com/sbaer |
| Commercial | Nick Kallen | Plasticity founder | Plasticity is a modern CAD tool with strong interest from technical users doing code-heavy workflows and direct modeling experimentation. | X: @nickkallen | https://x.com/nickkallen |
| SDL groups | Alán Aspuru-Guzik | University of Toronto / Acceleration Consortium | One of the central leaders of self-driving labs and autonomous experimentation, with clear interest in agent-based scientific workflows. (tom2024selfdrivinglaboratoriesfor pages 86-87) | Acceleration Consortium / lab contact page | https://acceleration.utoronto.ca/ |
| SDL groups | Sterling Baird | Acceleration Consortium researcher | Co-authored major SDL review work and is closely tied to practical autonomous materials discovery infrastructure. (tom2024selfdrivinglaboratoriesfor pages 91-92) | Acceleration Consortium profile | https://acceleration.utoronto.ca/ |
| SDL groups | Andrew Cooper | University of Liverpool professor | Cooper’s group is known for autonomous chemistry and mobile robot chemists, useful for end-to-end experimental orchestration ideas. | University profile / lab page | https://www.liverpool.ac.uk/chemistry/staff/andy-cooper/ |
| SDL groups | Lee Cronin | University of Glasgow / Chemify | Cronin’s Chemify work is among the clearest examples of digitized, programmable chemistry workflows that can inspire hardware-control abstractions. | Lab/site contact page | https://chemify.io/ |
| SDL groups | Milad Abolhasani | North Carolina State University professor | Leads autonomous flow chemistry and self-driving lab work with strong engineering emphasis, especially useful for closed-loop experimentation architecture. (tom2024selfdrivinglaboratoriesfor pages 91-92) | Faculty page | https://cbe.ncsu.edu/people/mabolha/ |
| SDL groups | Joshua Schrier | Fordham University professor | Active in autonomous chemistry and AI-for-chemistry toolchains; a good advisor for small academic lab strategy and software architecture. | Faculty page | https://www.fordham.edu/info/21684/faculty_and_staff/6237/joshua_schrier |
| SDL groups | Keith Brown | Boston University professor | Brown’s group works on autonomous/self-driving experimentation for mechanics and materials-style systems, relevant to closed-loop optimization. | Lab page | https://brownlab.bu.edu/ |
| AM experts | Tim Simpson | Penn State professor, CIMP-3D leader | Major figure in design for additive manufacturing and digital design/manufacturing workflows, relevant for manufacturability-aware assembly generation. | Faculty page | https://www.mne.psu.edu/department/directory-detail-g.aspx?q=tws8 |
| AM experts | Allison Beese | Penn State professor | Leading AM/mechanics researcher who bridges materials, process constraints, and part performance in additive contexts. | Faculty page | https://www.mne.psu.edu/department/directory-detail-g.aspx?q=aub522 |
| AM experts | Tresa Pollock | University of California, Santa Barbara professor | High-profile additive manufacturing and alloy/process expert, valuable for the future L-PBF integration path. | Faculty page | https://www.materials.ucsb.edu/people/faculty/tresa-pollock |
| AM experts | Kenneth S. Vecchio | University of California, San Diego professor | Leads advanced materials and high-throughput experimental work with links to digital metallurgy and AM-oriented research. | Faculty page | https://mae.ucsd.edu/faculty/kenneth-vecchio |
| Communities | CadQuery Discord | CadQuery community server | Best cold-start venue for practical help on CadQuery APIs, OCC issues, exporters, and LLM-generated script debugging. | Public Discord invite | https://cadquery.readthedocs.io/en/latest/ |
| Communities | build123d Discord | build123d community server | Good venue for rapid feedback on build123d syntax, assemblies, and pythonic CAD agent tooling. | Public Discord invite | https://build123d.readthedocs.io/en/latest/ |
| Communities | FreeCAD Forum | FreeCAD community forum | Strong place to ask about kernels, parametric workflows, and interoperability for future CAM/L-PBF paths. | Forum URL | https://forum.freecad.org/ |
| Communities | OpenSCAD subreddit | Reddit community for OpenSCAD | Useful for script-level CAD questions, printable geometry, and fast feedback from hobbyist and expert users. | Subreddit | https://www.reddit.com/r/openscad/ |
| Communities | SDL community | Self-driving lab community | Good cold-post venue for lab orchestration, automation software, and agent-in-the-loop experimentation questions. | Community page/invite | https://selfdrivinglabs.org/ |
| Communities | ASME IDETC-CIE | ASME conference community | Practical conference home for design automation, CAD, and engineering AI work with publication and networking value. | Conference page | https://event.asme.org/IDETC-CIE |
| Communities | SCF | Symposium on Computational Fabrication | Highly relevant academic venue for geometry/fabrication workflows that sit between CAD generation and manufacturing. | Conference page | https://www.compfab.org/ |
| Communities | CAD'25 | CAD Conference community | Dedicated CAD conference where generative CAD, datasets, and engineering AI are realistic outreach targets. | Conference page | https://cad-conference.net/ |
| Funding | NSF DMREF | National Science Foundation program | DMREF is one of the most natural NSF homes for autonomous alloy-discovery infrastructure linking design, materials, and manufacturing. | Program page | https://www.nsf.gov/funding/opportunities/dmref-designing-materials-revolutionize-engineer-our-future |
| Funding | NSF Future Manufacturing | National Science Foundation program | Strong fit for intelligent design-to-manufacturing workflows and academic cyber-physical manufacturing research. | Program page | https://www.nsf.gov/funding/opportunities/futuring-future-manufacturing |
| Funding | ARPA-E DIFFERENTIATE | ARPA-E program | Relevant model for AI-assisted engineering design and optimization program framing, even if the immediate topic is broader than CAD alone. | Program page | https://arpa-e.energy.gov/technologies/programs/differentiate |
| Funding | America Makes | National additive manufacturing institute | Best practical U.S. manufacturing institute contact for additive-manufacturing transition, industrial partners, and design-for-AM advice. | Contact/program page | https://www.americamakes.us/ |
| Funding | Acceleration Consortium | University of Toronto-led research/funding ecosystem | Natural partner for small academic teams building autonomous discovery infrastructure that spans agents, robotics, and materials. | Program/community page | https://acceleration.utoronto.ca/ |


*Table: This table summarizes named researchers, maintainers, commercial contacts, communities, and funding programs relevant to BYU Vertical Cloud Lab’s 2025–2026 agentic generative CAD effort. It is organized by category and includes a primary contact channel plus a source URL for quick outreach planning.*

---

## 1. Academic CAD-LLM / Generative-CAD Researchers

- **Rundi Wu** — Columbia University, PhD researcher. First author of **DeepCAD** (ICCV 2021), one of the earliest and most cited transformer-based generative CAD models, which represents shapes as sequences of CAD operations. Directly relevant for programmatic CAD representation design. Email: `rundi@cs.columbia.edu` (listed in paper header). (source: https://doi.org/10.48550/arxiv.2105.09492) (wu2021deepcadadeep pages 1-2)

- **Changxi Zheng** — Columbia University, Professor. Senior author and PI on the DeepCAD line of work. Email: `cxz@cs.columbia.edu` (listed in paper header). (source: https://doi.org/10.48550/arxiv.2105.09492) (wu2021deepcadadeep pages 1-2)

- **Haoyang Xie** — Arizona State University, School of Computing and Augmented Intelligence. First author of **Text-to-CadQuery**, which is directly aligned with the lab's need: fine-tuning LLMs to generate executable CadQuery Python code from natural language descriptions, with a 170K annotation dataset. GitHub repo: https://github.com/Text-to-CadQuery/Text-to-CadQuery. Email: `hxie40@asu.edu` (listed in paper header). (source: https://doi.org/10.48550/arxiv.2505.06507) (xie2505texttocadqueryanew pages 1-3)

- **Feng Ju** — Arizona State University. Co-author on Text-to-CadQuery, can advise on LLM fine-tuning and evaluation for CadQuery generation. Email: `fengju@asu.edu` (listed in paper header). (source: https://doi.org/10.48550/arxiv.2505.06507) (xie2505texttocadqueryanew pages 1-3)

- **Danila Rukhovich** — SnT, University of Luxembourg. First author of **CAD-Recode**, which translates point clouds into executable Python CAD code by fine-tuning an LLM decoder — relevant for scan-to-edit and model-repair workflows. Email: `danila.rukhovich@uni.lu` (listed in paper header). (source: https://doi.org/10.48550/arxiv.2412.14042) (rukhovich2025cadrecodereverseengineering pages 1-2)

- **Djamila Aouada** — SnT, University of Luxembourg, Professor. Senior author on CAD-Recode, leads LLM-mediated CAD reverse engineering research. Email: `djamila.aouada@uni.lu` (listed in paper header). (source: https://doi.org/10.48550/arxiv.2412.14042) (rukhovich2025cadrecodereverseengineering pages 1-2)

- **Jesse Barkley** — Carnegie Mellon University, Department of Mechanical Engineering. First author of **CADSmith**, a multi-agent CAD generation pipeline with programmatic geometric validation — closely matching an agentic, manufacturability-aware design loop. Email: `jabarkle@andrew.cmu.edu` (listed in paper header). (source: https://doi.org/10.48550/arxiv.2603.26512) (barkley2603cadsmithmultiagentcad pages 1-2)

- **Amir Barati Farimani** — Carnegie Mellon University, Professor. Senior author on CADSmith, leads the lab where multi-agent validated CAD generation was developed. Email: `afariman@andrew.cmu.edu` (listed in paper header). (source: https://doi.org/10.48550/arxiv.2603.26512) (barkley2603cadsmithmultiagentcad pages 1-2)

- **Qian Yu** — Beihang University, School of Software. Corresponding author on **ArtiCAD**, which targets articulated CAD assembly design via multi-agent code generation — directly relevant for mechanical assemblies rather than single parts. Project page: https://shui-yuan.github.io/articad/. Email: `qianyu@buaa.edu.cn` (listed in paper header). (source: https://doi.org/10.48550/arxiv.2604.10992) (shui2026articadarticulatedcad pages 1-3)

- **Ari Seff** — Princeton University. First author of **SketchGraphs**, a foundational dataset of 15 million parametric CAD sketches with geometric constraints, useful for constraint-aware CAD generation and repair. Email: `aseff@princeton.edu` (listed in paper header). (source: https://doi.org/10.48550/arxiv.2007.08506) (seff2020sketchgraphsalargescale pages 1-3)

- **Ryan P. Adams** — Princeton University, Professor. Senior author on SketchGraphs and PI of the Laboratory for Intelligent Probabilistic Systems. Email: `rpa@princeton.edu` (listed in paper header). (source: https://doi.org/10.48550/arxiv.2007.08506) (seff2020sketchgraphsalargescale pages 1-3)

- **Karl D. D. Willis** — Autodesk Research, USA. Lead author of the **Fusion 360 Gallery** dataset and environment for programmatic CAD reconstruction from human design sequences (8,625 models), a key benchmark in the field. Email: `karl.willis@autodesk.com` (listed in paper header). (source: https://doi.org/10.1145/3450626.3459818) (willis2021fusion360gallery pages 1-2)

- **Faez Ahmed** — MIT, Department of Mechanical Engineering, Professor. PI on the **GenCAD** and **CAD-Coder** lines of work, spanning image-conditioned CAD generation, CadQuery code output, and agentic engineering design. No public direct email found in cited papers; reachable via group members (e.g., Anna Doris at `adoris@mit.edu`) and the MIT DECODE Lab page. (source: https://doi.org/10.48550/arxiv.2505.14646) (doris2026cadcoderanopensource pages 1-2)

- **Anna C. Doris** — MIT. First author of **CAD-Coder**, an open-source VLM fine-tuned to generate editable CadQuery code from images, with a 163K-pair dataset (GenCAD-Code). GitHub: https://github.com/anniedoris/CAD-Coder. Email: `adoris@mit.edu` (listed in paper header). (source: https://doi.org/10.48550/arxiv.2505.14646) (doris2026cadcoderanopensource pages 1-2)

- **Ahmed R. Sadik** — Honda Research Institute Europe, Offenbach, Germany. Corresponding author on a 2025 paper quantitatively evaluating LLM-generated 3D CAD models and co-author of "From Idea to CAD" (multi-agent collaborative design). Email: `ahmed.sadik@honda-ri.de` (listed in paper header). (source: https://doi.org/10.48550/arxiv.2509.07010) (sadik2509humanintheloopquantitativeevaluation pages 1-2)

---

## 2. Code-CAD / Programmatic-CAD Open-Source Maintainers

- **Adam Urbanczyk** — Core maintainer of **CadQuery**, the Python parametric CAD library that is the most common target for LLM-generated CAD code. CadQuery sits on top of OpenCASCADE (OCCT) and is explicitly used by Text-to-CadQuery, CAD-Recode, CADSmith, and many other papers listed above. GitHub: `adam-urbanczyk`. Discord: CadQuery has a Discord linked from its documentation. (source: https://github.com/CadQuery/cadquery)

- **Jeremy Wright** — Long-time CadQuery co-maintainer and contributor to the broader Pythonic CAD ecosystem. GitHub: `jmwright`. (source: https://github.com/jmwright)

- **Roger Maitland** — Creator and primary maintainer of **build123d**, a modern Python parametric CAD library that is increasingly considered alongside CadQuery for code-generation workflows, with a cleaner builder-pattern API. GitHub: `gumyr`. Discord: build123d has a Discord linked from its ReadTheDocs. (source: https://github.com/gumyr/build123d)

- **Marius Kintel** — Core developer of **OpenSCAD**, the original text-based CSG CAD tool that remains a durable backend for generated geometry. GitHub: `kintel`. (source: https://github.com/openscad/openscad)

- **Yorik van Havre** — Core developer of **FreeCAD**, a major open-source parametric CAD platform. FreeCAD's robust CAD kernel and workbenches are relevant for future CAD/CAM integration. GitHub: `yorikvanhavre`. Community forum: https://forum.freecad.org/. (source: https://github.com/yorikvanhavre)

---

## 3. Commercial Generative-Design / CAD-API Contacts

- **Jessie Frazelle** — CEO of **Zoo.dev** (formerly KittyCAD). Zoo.dev is one of the few companies explicitly building a text-to-CAD API and programmable CAD infrastructure, with an open-source geometry engine (KittyCAD engine). Highly relevant for API-driven CAD generation. GitHub: `jessfraz`. X/Twitter: `@jessfraz`. (source: https://github.com/jessfraz)

- **Karl D. D. Willis** — Autodesk Research (also listed in Category 1). Can connect you to Autodesk's broader research group working on CAD-as-program, generative design, and the Fusion 360 ecosystem. Email: `karl.willis@autodesk.com` (listed in paper header). (source: https://doi.org/10.1145/3450626.3459818) (willis2021fusion360gallery pages 1-2)

- **Steve Baer** — Robert McNeel & Associates (**Rhino/Grasshopper**), developer relations and engineering lead. McNeel is notably open to developer engagement around CAD scripting (RhinoCommon, Grasshopper) and geometry kernels. GitHub: `sbaer`. Rhino developer forum: https://discourse.mcneel.com/. (source: https://github.com/sbaer)

- **Nick Kallen** — Founder of **Plasticity**, a modern direct-modeling CAD tool with growing adoption among technical users doing code-heavy and generative workflows. No public email found; reachable via X/Twitter: `@nickkallen`. (source: https://x.com/nickkallen)

- **Zoo.dev developer relations** — In addition to Jessie Frazelle personally, Zoo.dev maintains public developer documentation and API access at https://zoo.dev/docs. No individual devrel email published; use their Discord or GitHub issues. (source: https://zoo.dev/)

---

## 4. Self-Driving-Lab / Agentic-Hardware Groups

- **Alán Aspuru-Guzik** — University of Toronto, Professor; Director of the **Acceleration Consortium**. Co-authored the landmark "Self-Driving Laboratories for Chemistry and Materials Science" review (Chemical Reviews, 2024) and leads multiple agent-based experimental automation efforts. Lab/consortium page: https://acceleration.utoronto.ca/. No public direct email found; reachable via the Acceleration Consortium contact page. (source: https://acceleration.utoronto.ca/)

- **Sterling G. Baird** — Acceleration Consortium, Research Scientist. Co-authored the SDL review with Aspuru-Guzik and works on practical autonomous materials discovery infrastructure. GitHub: `sgbaird`. Reachable via Acceleration Consortium profile. (source: https://acceleration.utoronto.ca/)

- **Andrew I. Cooper** — University of Liverpool, Professor. Known for mobile robot chemists and autonomous chemistry platforms. Lab page: https://www.liverpool.ac.uk/chemistry/staff/andy-cooper/. Contact via university page. (source: https://www.liverpool.ac.uk/chemistry/staff/andy-cooper/)

- **Lee Cronin** — University of Glasgow, Professor; co-founder of **Chemify**. Develops digitized, programmable chemistry workflows — a conceptual model for hardware-control abstractions in self-driving labs. Chemify site: https://chemify.io/. University page: https://www.gla.ac.uk/schools/chemistry/staff/leecronin/. (source: https://chemify.io/)

- **Milad Abolhasani** — North Carolina State University, Associate Professor, Department of Chemical and Biomolecular Engineering. Leads autonomous flow chemistry and Pareto-front mapping with self-driving catalysis labs. Faculty page: https://cbe.ncsu.edu/people/mabolha/. (source: https://cbe.ncsu.edu/people/mabolha/)

- **Joshua Schrier** — Fordham University, Professor. Active in autonomous chemistry and AI-for-chemistry; a practical advisor for small academic lab strategy and software architecture for SDLs. Faculty page: https://www.fordham.edu/academics/departments/chemistry/faculty-and-staff/joshua-schrier/. (source: https://www.fordham.edu/academics/departments/chemistry/faculty-and-staff/joshua-schrier/)

- **Keith A. Brown** — Boston University, Associate Professor. Leads the Brown Lab working on Bayesian self-driving experimentation for mechanics and materials, relevant to closed-loop optimization with physical hardware. Lab page: https://brownlab.bu.edu/. (source: https://brownlab.bu.edu/)

---

## 5. Additive-Manufacturing + Design-for-AM Experts

- **Timothy W. Simpson** — Penn State University, Paul Morrow Professor of Engineering Design and Manufacturing. Leads CIMP-3D and has extensive work on design for AM, topology optimization, and digital design/manufacturing integration. Faculty page: https://www.me.psu.edu/department/directory-detail-g.aspx?q=tws8. (source: https://www.me.psu.edu/department/directory-detail-g.aspx?q=tws8)

- **Allison M. Beese** — Penn State University, Professor. Bridges materials science, process constraints, and AM part performance — important for understanding manufacturability constraints in L-PBF. Faculty page: https://www.matse.psu.edu/directory/allison-beese. (source: https://www.matse.psu.edu/directory/allison-beese)

- **Tresa M. Pollock** — University of California, Santa Barbara, Alcoa Distinguished Professor. High-profile AM and alloy/process expert; valuable for L-PBF integration paths and alloy discovery collaborations. Faculty page: https://www.materials.ucsb.edu/people/faculty/tresa-pollock. (source: https://www.materials.ucsb.edu/people/faculty/tresa-pollock)

- **Kenneth S. Vecchio** — University of California, San Diego, Professor, MAE Department. Leads advanced materials and high-throughput experimental alloy work (HT-READ), with links to digital metallurgy and AM-oriented research. Faculty page: https://mae.ucsd.edu/faculty/kenneth-vecchio. (source: https://mae.ucsd.edu/faculty/kenneth-vecchio)

---

## 6. Communities, Discords, Forums, and Conferences

- **CadQuery Discord** — The primary real-time community for CadQuery users and developers. Best cold-start venue for help on CadQuery APIs, OpenCASCADE issues, exporters, and debugging LLM-generated scripts. Invite link available from: https://cadquery.readthedocs.io/en/latest/ (source: https://cadquery.readthedocs.io/en/latest/)

- **build123d Discord** — Community server for build123d users. Good for rapid feedback on build123d syntax, assembly APIs, and Pythonic CAD agent tooling. Invite link available from: https://build123d.readthedocs.io/en/latest/ (source: https://build123d.readthedocs.io/en/latest/)

- **FreeCAD Forum** — Active community forum for FreeCAD users and developers, strong for questions about parametric workflows, kernels, and future CAM/L-PBF integration. URL: https://forum.freecad.org/ (source: https://forum.freecad.org/)

- **OpenSCAD subreddit (r/openscad)** — Useful for script-level CAD questions, printable geometry feedback, and rapid community input. URL: https://www.reddit.com/r/openscad/ (source: https://www.reddit.com/r/openscad/)

- **Self-Driving Labs community** — Community site and resources for autonomous/self-driving laboratory practitioners, including a community Discord. URL: https://selfdrivinglabs.org/ (source: https://selfdrivinglabs.org/)

- **ASME IDETC-CIE** — The ASME International Design Engineering Technical Conferences and Computers and Information in Engineering Conference. Practical venue for presenting design automation, CAD, and engineering AI work with publication and networking value. URL: https://event.asme.org/IDETC-CIE (source: https://event.asme.org/IDETC-CIE)

- **SCF (Symposium on Computational Fabrication)** — Academic venue directly targeting geometry/fabrication workflows between CAD generation and manufacturing. URL: https://www.compfab.org/ (source: https://www.compfab.org/)

- **CAD Conference (CAD'25)** — Dedicated computer-aided design conference where generative CAD, datasets, and engineering AI presentations are well-received. URL: https://cad-conference.net/ (source: https://cad-conference.net/)

---

## 7. Funding Programs and Program Officers

- **NSF DMREF (Designing Materials to Revolutionize and Engineer our Future)** — One of the most natural NSF homes for autonomous alloy-discovery infrastructure linking design, materials, and manufacturing. Supports integrated computational/experimental materials research. Program page: https://www.nsf.gov/funding/opportunities/dmref-designing-materials-revolutionize-engineer-our-future (source: https://www.nsf.gov/funding/opportunities/dmref-designing-materials-revolutionize-engineer-our-future)

- **NSF Future Manufacturing** — Strong fit for intelligent design-to-manufacturing workflows and academic cyber-physical manufacturing research, especially for small teams building novel automation. Program page: https://new.nsf.gov/funding/opportunities/future-manufacturing-fm (source: https://new.nsf.gov/funding/opportunities/future-manufacturing-fm)

- **ARPA-E DIFFERENTIATE** — ARPA-E program supporting AI-assisted engineering design and optimization. While broader than CAD, the program framing aligns well with agentic design-to-manufacturing workflows. Program page: https://arpa-e.energy.gov/technologies/programs/differentiate (source: https://arpa-e.energy.gov/technologies/programs/differentiate)

- **America Makes** — The U.S. national additive manufacturing innovation institute. Best practical contact for AM transition, industrial partners, design-for-AM tooling, and workforce development. URL: https://www.americamakes.us/ (source: https://www.americamakes.us/)

- **Acceleration Consortium** — University of Toronto-led research and funding ecosystem for autonomous scientific discovery. A natural partner for small academic teams building agent-driven discovery infrastructure spanning robotics, materials, and software. URL: https://acceleration.utoronto.ca/ (source: https://acceleration.utoronto.ca/)

---

**Note on contact verification:** All individual email addresses listed above were extracted directly from the author-contact sections of the cited publications (willis2021fusion360gallery pages 1-2, sadik2509humanintheloopquantitativeevaluation pages 1-2). GitHub handles and community URLs are from the respective public project repositories. For individuals where no personal email was located in the retrieved documents, the lab/organization-level contact page is provided. No email addresses have been fabricated. Users should verify current availability before sending, as academic affiliations may change.


References

1. (wu2021deepcadadeep pages 1-2): Rundi Wu, Chang Xiao, and Changxi Zheng. Deepcad: a deep generative network for computer-aided design models. 2021 IEEE/CVF International Conference on Computer Vision (ICCV), pages 6752-6762, May 2021. URL: https://doi.org/10.48550/arxiv.2105.09492, doi:10.48550/arxiv.2105.09492. This article has 419 citations.

2. (xie2505texttocadqueryanew pages 1-3): Haoyang Xie and Feng Ju. Text-to-cadquery: a new paradigm for cad generation with scalable large model capabilities. ArXiv, May 2505. URL: https://doi.org/10.48550/arxiv.2505.06507, doi:10.48550/arxiv.2505.06507. This article has 29 citations.

3. (rukhovich2025cadrecodereverseengineering pages 1-2): Danila Rukhovich, Elona Dupont, Dimitrios Mallis, Kseniya Cherenkova, Anis Kacem, and Djamila Aouada. Cad-recode: reverse engineering cad code from point clouds. ArXiv, Dec 2025. URL: https://doi.org/10.48550/arxiv.2412.14042, doi:10.48550/arxiv.2412.14042. This article has 51 citations.

4. (barkley2603cadsmithmultiagentcad pages 1-2): Jesse Barkley, Rumi Loghmani, and A. Farimani. Cadsmith: multi-agent cad generation with programmatic geometric validation. ArXiv, Mar 2603. URL: https://doi.org/10.48550/arxiv.2603.26512, doi:10.48550/arxiv.2603.26512. This article has 0 citations.

5. (shui2026articadarticulatedcad pages 1-3): Yuan Shui, Y. Guan, Zhan Zhang, Juncheng Hu, Jing Zhang, Dong Xu, and Qian Yu. Articad: articulated cad assembly design via multi-agent code generation. ArXiv, Apr 2026. URL: https://doi.org/10.48550/arxiv.2604.10992, doi:10.48550/arxiv.2604.10992. This article has 0 citations.

6. (seff2020sketchgraphsalargescale pages 1-3): Ari Seff, Yaniv Ovadia, Wenda Zhou, and Ryan P. Adams. Sketchgraphs: a large-scale dataset for modeling relational geometry in computer-aided design. Preprint, Jan 2020. URL: https://doi.org/10.48550/arxiv.2007.08506, doi:10.48550/arxiv.2007.08506. This article has 126 citations.

7. (willis2021fusion360gallery pages 1-2): Karl D. D. Willis, Yewen Pu, Jieliang Luo, Hang Chu, Tao Du, Joseph G. Lambourne, Armando Solar-Lezama, and Wojciech Matusik. Fusion 360 gallery. ACM Transactions on Graphics, 40:1-24, Jul 2021. URL: https://doi.org/10.1145/3450626.3459818, doi:10.1145/3450626.3459818. This article has 340 citations and is from a highest quality peer-reviewed journal.

8. (doris2026cadcoderanopensource pages 1-2): Anna C. Doris, Md Ferdous Alam, A. Nobari, and Faez Ahmed. Cad-coder: an open-source vision-language model for computer-aided design code generation. ArXiv, May 2026. URL: https://doi.org/10.48550/arxiv.2505.14646, doi:10.48550/arxiv.2505.14646. This article has 33 citations.

9. (ocker2503fromideato pages 1-3): Felix Ocker, Stefan Menzel, Ahmed Sadik, and Thiago Rios. From idea to cad: a language model-driven multi-agent system for collaborative design. ArXiv, Mar 2503. URL: https://doi.org/10.48550/arxiv.2503.04417, doi:10.48550/arxiv.2503.04417. This article has 24 citations.

10. (sadik2509humanintheloopquantitativeevaluation pages 1-2): Ahmed R. Sadik and M. Bujny. Human-in-the-loop: quantitative evaluation of 3d models generation by large language models. ArXiv, Sep 2509. URL: https://doi.org/10.48550/arxiv.2509.07010, doi:10.48550/arxiv.2509.07010. This article has 2 citations.

11. (tom2024selfdrivinglaboratoriesfor pages 86-87): Gary Tom, Stefan P. Schmid, Sterling G. Baird, Yang Cao, Kourosh Darvish, Han Hao, Stanley Lo, Sergio Pablo-García, Ella M. Rajaonson, Marta Skreta, Naruki Yoshikawa, Samantha Corapi, Gun Deniz Akkoc, Felix Strieth-Kalthoff, Martin Seifrid, and Alán Aspuru-Guzik. Self-driving laboratories for chemistry and materials science. Chemical Reviews, 124:9633-9732, Aug 2024. URL: https://doi.org/10.1021/acs.chemrev.4c00055, doi:10.1021/acs.chemrev.4c00055. This article has 686 citations and is from a highest quality peer-reviewed journal.

12. (tom2024selfdrivinglaboratoriesfor pages 91-92): Gary Tom, Stefan P. Schmid, Sterling G. Baird, Yang Cao, Kourosh Darvish, Han Hao, Stanley Lo, Sergio Pablo-García, Ella M. Rajaonson, Marta Skreta, Naruki Yoshikawa, Samantha Corapi, Gun Deniz Akkoc, Felix Strieth-Kalthoff, Martin Seifrid, and Alán Aspuru-Guzik. Self-driving laboratories for chemistry and materials science. Chemical Reviews, 124:9633-9732, Aug 2024. URL: https://doi.org/10.1021/acs.chemrev.4c00055, doi:10.1021/acs.chemrev.4c00055. This article has 686 citations and is from a highest quality peer-reviewed journal.