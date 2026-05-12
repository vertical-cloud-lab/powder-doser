Question: Find recent (2021-2025) peer-reviewed and arXiv academic publications on generative CAD, AI-assisted CAD, LLM-based CAD code generation, parametric/programmatic CAD, and learning-based shape generation for engineering design. Cover capabilities (text-to-CAD, sketch-to-CAD, constraint-aware generation, design-for-AM, B-rep generation, CSG / feature-tree generation, agentic design loops) and limitations (manufacturability, parametric editability, accuracy, evaluation benchmarks, hallucination of features, lack of standard datasets). For each paper give: full citation, 3-5 sentence summary, and relevance to building a Python/code-based generative CAD pipeline for an open-source powder-dosing device. Include landmark datasets/benchmarks (DeepCAD, Fusion 360 Gallery, ABC dataset, SketchGraphs, Text2CAD). Aim for ~10-15 references.

# Literature Review: Generative CAD, AI-Assisted CAD, and LLM-Based Code Generation for Engineering Design (2021–2025)

## 1. Introduction

This review surveys recent (2021–2025) peer-reviewed and arXiv publications on generative CAD, AI-assisted CAD, and LLM-based CAD code generation, with an emphasis on capabilities and limitations relevant to building a Python/code-based generative CAD pipeline for an open-source powder-dosing device. The review is organized into five thematic sections: (A) landmark datasets and benchmarks, (B) text-to-CAD and LLM-based code generation, (C) B-rep and geometry-centric generation, (D) agentic design frameworks, and (E) constraint-aware generation and limitations. A summary table follows.

| Paper (short citation) | Year | Category | Key Contribution | Relevance to Python/Code-Based Generative CAD Pipeline for Powder-Dosing Device |
|---|---:|---|---|---|
| Wu et al., **DeepCAD** | 2021 | Dataset/Benchmark; Parametric CAD Generation | Introduced the first Transformer-based generative model for CAD command sequences and released a large public dataset of **178,238** CAD models with construction histories. DeepCAD established the sketch/extrude-sequence paradigm that many later text-to-CAD and reverse-engineering systems build on. (wu2021deepcadadeep pages 1-2, alam2409gencadimageconditionedcomputeraided pages 5-7) | Foundational training/evaluation resource for a pipeline that emits editable procedural steps rather than meshes. Useful if the powder-dosing device pipeline targets sequence generation first, then execution in CadQuery/FreeCAD. |
| Willis et al., **Fusion 360 Gallery** | 2021 | Dataset/Benchmark; Programmatic CAD Reconstruction | Released **8,625** human-designed sketch-and-extrude CAD programs and the **Fusion 360 Gym** environment for sequential CAD reconstruction. It is one of the few benchmarks with realistic human modeling programs rather than purely synthetic geometry. (willis2021fusion360gallery pages 2-3, heidari2025geometricdeeplearning pages 16-17) | Valuable for evaluating human-like program structure and step ordering for real mechanical parts. Good benchmark for whether generated CAD for a dosing hopper, auger mount, or bracket looks like engineer-authored feature history rather than only matching geometry. |
| Koch et al., **ABC Dataset** | 2019 | Dataset/Benchmark; B-rep/Geometry Learning | Built a very large corpus of **1M+ CAD models** with parametrized curves and surfaces for geometric deep learning. ABC is excellent for surface, patch, differential-geometry, and reconstruction tasks, though its native construction history is hard to use directly. (heidari2025geometricdeeplearning pages 5-6, alam2409gencadimageconditionedcomputeraided pages 3-5) | Strong pretraining source for shape priors, B-rep geometry understanding, and retrieval, but less directly useful for code-generation than DeepCAD/Fusion360. Helpful if the pipeline later adds B-rep validation or geometry retrieval for reusable feeder subcomponents. |
| Seff et al., **SketchGraphs** | 2020 | Dataset/Benchmark; Constraint-Aware Sketch Modeling | Provided **15M** parametric CAD sketches with geometric constraints and relational structure. It underpins learning for sketch autocomplete, constraint inference, and sketch-sequence reasoning. (heidari2025geometricdeeplearning pages 5-6) | Highly relevant for the front end of a parametric device workflow: flange outlines, slot patterns, fastener hole layouts, and mating sketches. Particularly useful if the pipeline should preserve constraints like concentricity, symmetry, and equal spacing for manufacturable sheet/printed parts. |
| Khan et al., **Text2CAD** | 2024 | Text-to-CAD; Dataset/Benchmark | Established a major text-to-CAD benchmark pairing natural-language prompts with DeepCAD-style CAD sequences at roughly **170K**-scale. It connected language supervision to parametric sequence generation and became a standard baseline/reference for later LLM-based CAD work. (xie2505texttocadqueryanew pages 1-3, dong2025histcadgeometricallyconstrained pages 12-12) | Important benchmark if the goal is promptable design variants such as “larger dosing chamber,” “add inspection window,” or “mount for NEMA 17 motor.” A good starting point for fine-tuning models that map engineering requirements into executable parametric histories. |
| Rukhovich et al., **CAD-Recode** | 2025 | Reverse Engineering; LLM Code Generation | Translates point clouds directly into executable **CadQuery Python** using a lightweight point-cloud projector plus a fine-tuned **Qwen2-1.5B** decoder. Trained on up to **1M** procedurally generated programs, it reports strong DeepCAD/Fusion360 performance (e.g., IoU up to **92.0** on DeepCAD and **87.8** on Fusion360). (rukhovich2025cadrecodereverseengineering pages 4-6, rukhovich2025cadrecodereverseengineering pages 7-8, rukhovich2025cadrecodereverseengineering pages 2-3) | Extremely relevant if the device pipeline should ingest scans/meshes of legacy parts or hand-built prototypes and recover editable Python CAD. Also demonstrates a practical architecture for “geometry encoder + code LLM decoder” that could be reused for reverse-engineering existing powder-dosing assemblies. |
| Xu et al., **BrepGen** | 2024 | B-rep Generation | Proposed a diffusion model that directly generates B-rep CAD solids using a hierarchical tree over **faces, edges, and vertices** with structured latent geometry. It supports richer surfaces than sketch-extrude-only methods, but reported failure modes include missing faces, self-intersections, and non-watertight outputs. (xu2024brepgenabrep pages 3-4, xu2024brepgenabrep pages 9-11, xu2024brepgenabrep pages 2-3) | Useful if the pipeline eventually needs higher-fidelity B-rep solids for downstream CAD/CAM interoperability. For an open-source dosing device, it is more relevant as a future geometry-validation or completion module than as the first choice for editable code generation. |
| Guan et al., **CAD-Coder** | 2025 | Text-to-CAD; LLM Code Generation | Reformulated text-to-CAD as direct **CadQuery script generation**, adding chain-of-thought planning plus **GRPO** reinforcement learning with geometric and format rewards. Released a large text–CadQuery–3D dataset (**110K** triplets) and emphasized executable validation and richer modeling vocabulary compared with low-level command sequences. (guan2025cadcodertexttocadgeneration pages 1-3, guan2025cadcodertexttocadgeneration pages 16-17) | One of the most directly applicable papers for a Python-native pipeline. Its reward design is especially relevant for enforcing geometry correctness on parts like dosing funnels, rotating discs, brackets, and housings while still keeping the output editable as code. |
| Xie & Ju, **Text-to-CadQuery** | 2025 | Text-to-CAD; LLM Code Generation | Showed that generating **CadQuery code directly** is often simpler and more scalable than generating custom CAD tokens first. By augmenting Text2CAD with about **170K** text–CadQuery pairs, the authors improved exact-match and Chamfer metrics and leveraged standard code-LLMs instead of training bespoke CAD-only decoders from scratch. (xie2505texttocadqueryanew pages 1-3) | Probably the cleanest template for building a practical open-source pipeline: use natural language, output Python code, execute, validate, and iterate. Especially attractive for a repository-centered engineering workflow where generated parts are version-controlled alongside BOM and test scripts. |
| Li et al., **CAD-Llama** | 2025 | LLM Code Gen; Parametric CAD | Adapted pretrained LLMs to generate parametric CAD using **Structured Parametric CAD Code (SPCC)** and hierarchical semantic annotations, plus adaptive pretraining and instruction tuning. The paper argues that LLMs need CAD-specific structure to reason over geometry and modeling intent. (daareyni2025generativeaimeets pages 1-2) | Relevant for representing the dosing device in a structured intermediate language before final CadQuery emission. The SPCC idea is useful for separating semantics (“hopper,” “mounting flange,” “dispense outlet”) from low-level geometry generation. |
| Daareyni et al., **Generative AI meets CAD** | 2025 | AI-Assisted CAD; Manufacturing-Oriented Review/System | Presented a multimodal GPT-4o-assisted CAD workflow with text, image, and voice inputs and a **closed feedback loop** for iterative refinement. The paper also synthesizes strengths and weaknesses of LLM-driven CAD, citing evaluation metrics, solver-assisted geometry, and design-to-manufacturing implications. (daareyni2025generativeaimeets pages 1-2) | Especially relevant for a real device project because it frames CAD generation as part of a manufacturing workflow, not just a graphics task. Useful for scoping limitations: prompt ambiguity, need for solver/tool support, and the importance of iterative correction before fabrication. |
| Ocker et al., **From Idea to CAD** | 2025 | Agentic Design; Multi-Agent CAD | Proposed a **VLM-driven multi-agent system** with requirement, CAD-engineering, and vision-based QA agents that generate parametric CAD from sketches/text and then iteratively validate with the user. The system uses code-based CAD tooling and addresses missing information via chat-mediated clarification loops. (ocker2503fromideato pages 1-3) | Strong blueprint for an agentic loop around a powder-dosing device: one agent gathers requirements, another writes CadQuery, another renders/inspects geometry, and a validator asks for missing tolerances, capacity, or motor constraints. Useful when the design task is ambiguous and multi-step. |
| Schüpbach et al., **From Text to Design** | 2025 | Agentic Design; DfAM | Evaluated multiple LLMs and multi-step agent workflows for automated CAD generation and found that **automated visual feedback** improved performance, especially with multimodal models. Demonstrated an end-to-end case study involving topology optimization and additive manufacturing, while highlighting limitations such as hallucination, poor spatial reasoning, prompt sensitivity, and lack of standard benchmarks. (schupbach2025fromtextto pages 1-2) | Very relevant for a development loop that renders generated device parts, checks them visually, and revises code automatically. Also a warning that an open-source pipeline should include explicit DfAM and engineering checks, not trust raw LLM output. |
| Dong et al., **HistCAD** | 2025 | Constraint-Aware CAD; Dataset/Benchmark | Introduced a history-based, geometrically constrained CAD representation with explicit sketch constraints, feature operations, and boundary references, plus a **Constraint-Aware Editability Benchmark**. The work emphasizes that executable geometry alone is insufficient; models must remain editable and constraint-preserving after parameter changes. (dong2025histcadgeometricallyconstrained pages 10-12, dong2025histcadgeometricallyconstrained pages 2-3, dong2025histcadgeometricallyconstrained pages 12-12) | Highly relevant for a reusable product-development pipeline where dimensions will change often: powder volume, funnel angle, screw pitch housing, and mounting patterns. HistCAD’s editability focus is directly aligned with maintaining a robust parametric codebase instead of generating one-off shapes. |
| Heidari & Iosifidis, **Geometric Deep Learning for CAD: A Survey** | 2025 | Survey | Comprehensive survey of CAD-oriented geometric deep learning across synthesis, retrieval, reconstruction, datasets, and benchmarks. It highlights strengths and gaps of datasets such as ABC, SketchGraphs, and Fusion 360 Gallery and notes persistent scarcity of large labeled parametric/B-rep data. (heidari2025geometricdeeplearning pages 5-6, heidari2025geometricdeeplearning pages 16-17) | Useful as a map of the design space when choosing between sequence generation, B-rep generation, sketch modeling, or multimodal retrieval for the dosing-device stack. It also helps justify benchmark choices and exposes current gaps in standard evaluation, manufacturability, and interoperability. |


*Table: This table summarizes 15 influential datasets, methods, and surveys spanning generative CAD, LLM-based CAD code generation, B-rep modeling, and agentic design workflows. It is designed to help identify which works are most actionable for building a Python/CadQuery-based generative CAD pipeline for an open-source powder-dosing device.*

---

## 2. Landmark Datasets and Benchmarks

### 2.1 DeepCAD
**Wu, R., Xiao, C., and Zheng, C. "DeepCAD: A Deep Generative Network for Computer-Aided Design Models." ICCV 2021, pp. 6752–6762.**

DeepCAD introduced the first deep generative model that outputs CAD designs as sequences of sketch-and-extrude operations rather than discretized shapes, alongside a publicly released dataset of 178,238 CAD models with construction sequences (wu2021deepcadadeep pages 1-2). The architecture draws an analogy between CAD operations and natural language, proposing a Transformer-based autoencoder that embeds CAD models into a latent space and decodes latent vectors into CAD command sequences. Each command encodes a type (Line, Arc, Circle, Extrude) and up to 16 continuous/discrete parameters, normalized and quantized into 256 bins (alam2409gencadimageconditionedcomputeraided pages 5-7, xie2505texttocadqueryanew pages 12-15). DeepCAD established the standard benchmark used by nearly all subsequent text-to-CAD and reverse-engineering methods. **Relevance**: The DeepCAD dataset and representation format are the de facto standard for training and evaluating parametric CAD generation models. A powder-dosing pipeline could use DeepCAD-format sequences as an intermediate representation or for pretraining before fine-tuning on domain-specific parts.

### 2.2 Fusion 360 Gallery
**Willis, K.D.D., et al. "Fusion 360 Gallery." ACM Transactions on Graphics, 40(4):1–24, 2021.**

The Fusion 360 Gallery provides 8,625 human-designed CAD programs using a sketch-and-extrude DSL, along with the Fusion 360 Gym interactive environment that returns geometric state after each modeling step (willis2021fusion360gallery pages 2-3). It is notable as one of the few benchmarks with realistic human modeling programs rather than purely synthetic geometry. The authors benchmark neurally guided search for programmatic CAD reconstruction, reporting correct recovery for 67.5% of test designs within 100 interactions (willis2021fusion360gallery pages 2-3, heidari2025geometricdeeplearning pages 16-17). **Relevance**: The Fusion 360 Gallery is valuable for evaluating whether generated CAD code produces human-like feature histories, critical for maintainability of an open-source device.

### 2.3 ABC Dataset
**Koch, S., et al. "ABC: A Big CAD Model Dataset for Geometric Deep Learning." CVPR 2019, pp. 9593–9603.**

The ABC dataset contains over one million high-quality CAD models with explicitly parametrized curves and surfaces, providing ground truth for surface normals, patch segmentation, geometric feature detection, and shape reconstruction (heidari2025geometricdeeplearning pages 5-6, alam2409gencadimageconditionedcomputeraided pages 3-5). However, its construction history is accessible only via the Onshape API in a proprietary format, limiting its use for direct sequence-based generation (willis2021fusion360gallery pages 2-3). **Relevance**: ABC serves primarily as a geometry pretraining resource and B-rep validation corpus rather than a direct source for code-generation training.

### 2.4 SketchGraphs
**Seff, A., et al. "SketchGraphs: A Large-Scale Dataset for Modeling Relational Geometry in Computer-Aided Design." arXiv:2007.08506, 2020.**

SketchGraphs provides 15 million parametric CAD sketches with geometric constraints and relational structure extracted from Onshape, supporting tasks like sketch autocomplete, constraint inference, and relational geometry modeling (heidari2025geometricdeeplearning pages 5-6). **Relevance**: Highly relevant for the parametric sketch front-end of a device pipeline, where flange outlines, hole patterns, and mating features must preserve constraints such as concentricity, symmetry, and equal spacing.

### 2.5 Text2CAD
**Khan, M.S., et al. "Text2CAD: Generating Sequential CAD Designs from Beginner-to-Expert Level Text Prompts." NeurIPS 2024, pp. 7552–7579.**

Text2CAD paired natural-language prompts with DeepCAD-style command sequences at approximately 170,000-model scale, establishing the standard text-to-CAD benchmark (xie2505texttocadqueryanew pages 1-3, xie2505texttocadqueryanew pages 3-4). Multiple subsequent systems (Text-to-CadQuery, CAD-Coder, CAD-Llama) build on or augment this dataset. **Relevance**: A critical benchmark for any pipeline that accepts natural-language specifications such as "create a hopper with 45° walls and a 10mm outlet" and maps them to executable parametric code.

---

## 3. Text-to-CAD and LLM-Based Code Generation

### 3.1 Text-to-CadQuery
**Xie, H. and Ju, F. "Text-to-CadQuery: A New Paradigm for CAD Generation with Scalable Large Model Capabilities." arXiv:2505.06507, 2025.**

This work proposes generating CadQuery Python code directly from text, bypassing intermediate task-specific command sequences (xie2505texttocadqueryanew pages 1-3). By augmenting Text2CAD with ~170,000 CadQuery annotations and fine-tuning six open-source LLMs (124M to 7B parameters), the authors achieve a top-1 exact match of 69.3% and a 48.6% reduction in Chamfer Distance. The key insight is that pretrained LLMs already excel at Python generation and spatial reasoning, making CadQuery a natural output format that scales with model size (xie2505texttocadqueryanew pages 1-3). **Relevance**: This is arguably the cleanest template for a practical open-source pipeline: natural language in, Python code out, execute, validate, iterate. Ideal for a version-controlled engineering workflow.

### 3.2 CAD-Coder
**Guan, Y., et al. "CAD-Coder: Text-to-CAD Generation with Chain-of-Thought and Geometric Reward." arXiv:2505.19713, 2025.**

CAD-Coder reformulates text-to-CAD as CadQuery script generation and introduces a two-stage pipeline: supervised fine-tuning on 110K text–CadQuery–3D model triplets, followed by reinforcement learning with Group Reward Policy Optimization (GRPO) guided by a geometric reward (Chamfer Distance) and a format reward (guan2025cadcodertexttocadgeneration pages 1-3). A chain-of-thought planning process improves reasoning about complex geometric relationships. **Relevance**: The geometric reward and RL-based refinement loop are directly applicable to enforcing dimensional correctness on powder-dosing components—funnels, discs, brackets—while keeping output editable as Python code.

### 3.3 CAD-Llama
**Li, J., et al. "CAD-Llama: Leveraging Large Language Models for Computer-Aided Design Parametric 3D Model Generation." CVPR 2025, pp. 18563–18573.**

CAD-Llama develops a Structured Parametric CAD Code (SPCC) format with hierarchical semantic descriptions, adaptive pretraining, and instruction tuning to equip LLMs with spatial knowledge inherent in parametric sequences (daareyni2025generativeaimeets pages 1-2). The framework significantly outperforms prior autoregressive methods and LLM baselines on text-to-CAD tasks. **Relevance**: The SPCC representation is useful for separating high-level design semantics ("hopper body," "outlet tube," "mounting flange") from low-level geometry, improving both interpretability and prompt engineering for domain-specific parts.

### 3.4 CAD-Recode
**Rukhovich, D., et al. "CAD-Recode: Reverse Engineering CAD Code from Point Clouds." arXiv:2412.14042, 2025.**

CAD-Recode combines a lightweight point-cloud projector with a fine-tuned Qwen2-1.5B LLM decoder to translate point clouds into executable CadQuery Python code (rukhovich2025cadrecodereverseengineering pages 4-6, rukhovich2025cadrecodereverseengineering pages 1-2). Trained on up to 1M procedurally generated programs, it achieves IoU of 92.0 on DeepCAD and 87.8 on Fusion360 (rukhovich2025cadrecodereverseengineering pages 7-8). The output code is interpretable by off-the-shelf LLMs, enabling downstream editing and CAD-specific question answering. A refactoring step using GPT-4o generates interactive parameter sliders for editing (rukhovich2025cadrecodereverseengineering pages 20-21). **Relevance**: Directly applicable if the device pipeline should ingest scans or meshes of legacy parts and recover editable Python CAD. Demonstrates a practical "geometry encoder + code LLM decoder" architecture reusable for reverse-engineering existing powder-dosing assemblies.

---

## 4. B-rep and Geometry-Centric Generation

### 4.1 BrepGen
**Xu, X., et al. "BrepGen: A B-rep Generative Diffusion Model with Structured Latent Geometry." ACM Transactions on Graphics, 43(4):1–14, 2024.**

BrepGen represents B-rep CAD solids as a hierarchical tree with root, face, edge, and vertex levels, encoding both topology (via node duplication) and geometry (bounding boxes + VAE-compressed shape features) in a unified latent structure (xu2024brepgenabrep pages 3-4, xu2024brepgenabrep pages 2-3). Transformer-based diffusion models sequentially denoise node features, with duplicated nodes merged to recover B-rep connectivity. BrepGen supports free-form and doubly-curved surfaces beyond sketch-and-extrude and enables applications like CAD autocomplete and design interpolation (xu2024brepgenabrep pages 9-11). Common failure modes include missing faces, self-intersections, and non-watertight outputs (xu2024brepgenabrep pages 9-11). **Relevance**: BrepGen is more relevant as a downstream geometry-validation or completion module than as the primary code-generation engine for an open-source device, but its hierarchical representation could inform how generated CadQuery code is validated for topological correctness.

---

## 5. Agentic Design Frameworks

### 5.1 From Idea to CAD
**Ocker, F., et al. "From Idea to CAD: A Language Model-Driven Multi-Agent System for Collaborative Design." arXiv:2503.04417, 2025.**

This work presents a VLM-driven multi-agent system with specialized agents for requirements engineering, CAD code generation (using CadQuery), and vision-based quality assurance, connected through an iterative validation loop with the user (ocker2503fromideato pages 1-3). The system can detect missing information and prompt clarification, mitigating VLM spatial-reasoning limitations through visual self-feedback. Ablation studies demonstrate benefits of the multi-agent architecture over naive single-LLM use. **Relevance**: Provides a strong blueprint for an agentic loop around a powder-dosing device: one agent gathers requirements (powder type, dose volume, motor torque), another writes CadQuery, another renders and inspects geometry, and a validator checks for missing tolerances or constraints.

### 5.2 From Text to Design
**Schüpbach, A., et al. "From Text to Design: A Framework to Leverage LLM Agents for Automated CAD Generation." Proceedings of the Design Society, 5:1893–1902, 2025.**

This peer-reviewed paper evaluates five LLMs across four agent workflows for CAD generation and finds that automated visual feedback outperforms other approaches, particularly with multimodal models like ChatGPT-4o (schupbach2025fromtextto pages 1-2). A case study demonstrates end-to-end topology optimization and additive manufacturing with minimal human input. Key limitations identified include hallucination, poor spatial reasoning, prompt dependency, and the absence of standardized evaluation benchmarks. **Relevance**: Directly applicable for a development loop that renders generated device parts, checks them visually, and revises code automatically. The DfAM case study is particularly informative for powder-dosing components intended for 3D printing.

---

## 6. Constraint-Aware Generation, Limitations, and Manufacturing Considerations

### 6.1 HistCAD
**Dong, X., et al. "HistCAD: Geometrically Constrained Parametric History-based CAD Dataset." arXiv:2602.19171, 2025.**

HistCAD introduces a constraint-aware parametric representation that explicitly encodes 19 sketch constraint types, feature operations, and boundary references, along with a Constraint-Aware Editability Benchmark with three diagnostic metrics: Editability Rate (ER), Constraint-Preserving Parameter Change Success Rate (cPCSR), and Overall Editability Score (OES) (dong2025histcadgeometricallyconstrained pages 10-12, dong2025histcadgeometricallyconstrained pages 2-3). The dataset unifies 170,236 academic and industrial CAD sequences. Experiments show that many models achieve valid geometry (high ER) but fail to preserve constraints after parameter edits (low cPCSR), with industrial data proving particularly challenging (OES at 64.00%) (dong2025histcadgeometricallyconstrained pages 10-12). **Relevance**: Highly relevant for a reusable product-development pipeline where dimensions will change often (powder volume, funnel angle, housing size). HistCAD's editability focus is directly aligned with maintaining a robust parametric codebase.

### 6.2 Generative AI Meets CAD
**Daareyni, A., et al. "Generative AI Meets CAD: Enhancing Engineering Design to Manufacturing Processes with Large Language Models." International Journal of Advanced Manufacturing Technology, 2025.**

This paper presents a multimodal GPT-4o-assisted CAD framework with text, image, and voice inputs and a closed feedback loop for iterative refinement, explicitly targeting the design-to-manufacturing pipeline (daareyni2025generativeaimeets pages 1-2). It synthesizes strengths and limitations of LLM-driven CAD, including: the need for solver-assisted geometry computation (offloading precise math to constraint solvers), evaluation metrics like parsing rate and intersection-over-union, prompt ambiguity, and the importance of iterative correction before fabrication. **Relevance**: Especially relevant for a real device project because it frames CAD generation as part of a manufacturing workflow, highlighting practical barriers to shipping AI-generated parts.

### 6.3 Geometric Deep Learning for CAD: A Survey
**Heidari, N. and Iosifidis, A. "Geometric Deep Learning for Computer-Aided Design: A Survey." IEEE Access, 13:119305–119334, 2025.**

This comprehensive survey covers learning-based methods across CAD similarity analysis, retrieval, 2D/3D synthesis, and generation from point clouds and images, alongside a complete list of benchmark datasets and their characteristics (heidari2025geometricdeeplearning pages 5-6, heidari2025geometricdeeplearning pages 16-17). It highlights persistent scarcity of large labeled parametric/B-rep data and the limitations of current B-rep datasets. **Relevance**: Serves as a roadmap for choosing between sequence generation, B-rep generation, sketch modeling, or multimodal retrieval for the dosing-device pipeline, and exposes current gaps in standardized evaluation for manufacturability and interoperability.

---

## 7. Cross-Cutting Limitations

Several recurring limitations emerge across this literature:

1. **Parametric editability**: Most generative models produce valid geometry but fail to preserve design intent when parameters are changed. HistCAD demonstrates that constraint-preserving editability rates remain low, especially for industrial parts (dong2025histcadgeometricallyconstrained pages 10-12, dong2025histcadgeometricallyconstrained pages 2-3).

2. **Manufacturability and DfAM**: Current text-to-CAD systems do not natively enforce additive manufacturing constraints (wall thickness, overhang angles, support requirements). Schüpbach et al. demonstrate a promising DfAM case study but note that manufacturing checks require explicit engineering validation loops (schupbach2025fromtextto pages 1-2).

3. **Hallucination and spatial reasoning**: LLMs frequently produce locally coherent but globally inconsistent geometry (e.g., a handle inside a cup), and struggle with tasks requiring complex mathematical computation like involute gears (fan2025caddesignerconceptualdesign pages 8-9).

4. **Dataset limitations**: Existing datasets are limited in operation diversity (mostly sketch+extrude), scale for industrial complexity, and quality of text annotations (often LLM-generated rather than human-authored) (xie2505texttocadqueryanew pages 3-4, dong2025histcadgeometricallyconstrained pages 12-12).

5. **Evaluation benchmarks**: The field lacks standardized benchmarks for functional evaluation, constraint preservation, and manufacturing feasibility. Metrics remain dominated by Chamfer Distance and IoU, which capture geometric similarity but not engineering correctness (dong2025histcadgeometricallyconstrained pages 10-12, schupbach2025fromtextto pages 1-2).

6. **Accuracy on complex parts**: Performance degrades significantly on parts requiring non-extrusion features (revolutions, fillets, sweeps, lofts), with most systems limited to sketch-extrude primitives (rukhovich2025cadrecodereverseengineering pages 7-8, fan2025caddesignerconceptualdesign pages 8-9).

---

## 8. Implications for a Python/Code-Based Generative CAD Pipeline for an Open-Source Powder-Dosing Device

Based on this review, the most actionable architecture for an open-source powder-dosing device pipeline would combine:

- **CadQuery as the output representation**, following Text-to-CadQuery and CAD-Coder, which enables direct Python execution, version control, and parametric editing (xie2505texttocadqueryanew pages 1-3, guan2025cadcodertexttocadgeneration pages 1-3).
- **A fine-tuned code LLM** (e.g., Qwen-based or CodeLlama-based) trained on text–CadQuery pairs, potentially augmented with domain-specific examples of hoppers, auger housings, and mounting brackets (xie2505texttocadqueryanew pages 1-3, rukhovich2025cadrecodereverseengineering pages 4-6).
- **An agentic framework** with requirements extraction, code generation, visual rendering feedback, and constraint validation agents, following the architectures of Ocker et al. and Schüpbach et al. (ocker2503fromideato pages 1-3, schupbach2025fromtextto pages 1-2).
- **Explicit manufacturing constraints** embedded in the validation loop (wall thickness, overhang checking, tolerance verification), as current models do not natively enforce DfAM rules (schupbach2025fromtextto pages 1-2).
- **HistCAD-style editability testing** to ensure generated parts remain parametrically editable when dimensions change across powder-dosing variants (dong2025histcadgeometricallyconstrained pages 10-12).

The primary open challenges for such a pipeline are: (1) ensuring constraint-preserving editability across design variants, (2) enforcing manufacturing feasibility for 3D-printed or machined components, (3) handling complex features beyond sketch-extrude that may be needed for auger geometry or rotational parts, and (4) establishing domain-specific evaluation benchmarks that go beyond geometric similarity to capture functional requirements like dosing accuracy, assembly fit, and material compatibility.

References

1. (wu2021deepcadadeep pages 1-2): Rundi Wu, Chang Xiao, and Changxi Zheng. Deepcad: a deep generative network for computer-aided design models. 2021 IEEE/CVF International Conference on Computer Vision (ICCV), pages 6752-6762, May 2021. URL: https://doi.org/10.48550/arxiv.2105.09492, doi:10.48550/arxiv.2105.09492. This article has 409 citations.

2. (alam2409gencadimageconditionedcomputeraided pages 5-7): Md Ferdous Alam and Faez Ahmed. Gencad: image-conditioned computer-aided design generation with transformer-based contrastive representation and diffusion priors. Trans. Mach. Learn. Res., Sep 2409. URL: https://doi.org/10.48550/arxiv.2409.16294, doi:10.48550/arxiv.2409.16294. This article has 41 citations.

3. (willis2021fusion360gallery pages 2-3): Karl D. D. Willis, Yewen Pu, Jieliang Luo, Hang Chu, Tao Du, Joseph G. Lambourne, Armando Solar-Lezama, and Wojciech Matusik. Fusion 360 gallery. ACM Transactions on Graphics, 40:1-24, Jul 2021. URL: https://doi.org/10.1145/3450626.3459818, doi:10.1145/3450626.3459818. This article has 336 citations and is from a highest quality peer-reviewed journal.

4. (heidari2025geometricdeeplearning pages 16-17): Negar Heidari and Alexandros Iosifidis. Geometric deep learning for computer-aided design: a survey. IEEE Access, 13:119305-119334, Feb 2025. URL: https://doi.org/10.48550/arxiv.2402.17695, doi:10.48550/arxiv.2402.17695. This article has 47 citations and is from a peer-reviewed journal.

5. (heidari2025geometricdeeplearning pages 5-6): Negar Heidari and Alexandros Iosifidis. Geometric deep learning for computer-aided design: a survey. IEEE Access, 13:119305-119334, Feb 2025. URL: https://doi.org/10.48550/arxiv.2402.17695, doi:10.48550/arxiv.2402.17695. This article has 47 citations and is from a peer-reviewed journal.

6. (alam2409gencadimageconditionedcomputeraided pages 3-5): Md Ferdous Alam and Faez Ahmed. Gencad: image-conditioned computer-aided design generation with transformer-based contrastive representation and diffusion priors. Trans. Mach. Learn. Res., Sep 2409. URL: https://doi.org/10.48550/arxiv.2409.16294, doi:10.48550/arxiv.2409.16294. This article has 41 citations.

7. (xie2505texttocadqueryanew pages 1-3): Haoyang Xie and Feng Ju. Text-to-cadquery: a new paradigm for cad generation with scalable large model capabilities. ArXiv, May 2505. URL: https://doi.org/10.48550/arxiv.2505.06507, doi:10.48550/arxiv.2505.06507. This article has 29 citations.

8. (dong2025histcadgeometricallyconstrained pages 12-12): X Dong, C Li, C Han, P Zheng, J Jing, and Y Song. Histcad: geometrically constrained parametric history-based cad dataset. ArXiv, 2025. URL: https://doi.org/10.48550/arxiv.2602.19171, doi:10.48550/arxiv.2602.19171.

9. (rukhovich2025cadrecodereverseengineering pages 4-6): Danila Rukhovich, Elona Dupont, Dimitrios Mallis, Kseniya Cherenkova, Anis Kacem, and Djamila Aouada. Cad-recode: reverse engineering cad code from point clouds. ArXiv, Dec 2025. URL: https://doi.org/10.48550/arxiv.2412.14042, doi:10.48550/arxiv.2412.14042. This article has 48 citations.

10. (rukhovich2025cadrecodereverseengineering pages 7-8): Danila Rukhovich, Elona Dupont, Dimitrios Mallis, Kseniya Cherenkova, Anis Kacem, and Djamila Aouada. Cad-recode: reverse engineering cad code from point clouds. ArXiv, Dec 2025. URL: https://doi.org/10.48550/arxiv.2412.14042, doi:10.48550/arxiv.2412.14042. This article has 48 citations.

11. (rukhovich2025cadrecodereverseengineering pages 2-3): Danila Rukhovich, Elona Dupont, Dimitrios Mallis, Kseniya Cherenkova, Anis Kacem, and Djamila Aouada. Cad-recode: reverse engineering cad code from point clouds. ArXiv, Dec 2025. URL: https://doi.org/10.48550/arxiv.2412.14042, doi:10.48550/arxiv.2412.14042. This article has 48 citations.

12. (xu2024brepgenabrep pages 3-4): Xiang Xu, Joseph Lambourne, Pradeep Jayaraman, Zhengqing Wang, Karl Willis, and Yasutaka Furukawa. Brepgen: a b-rep generative diffusion model with structured latent geometry. ACM Transactions on Graphics, 43:1-14, Jul 2024. URL: https://doi.org/10.1145/3658129, doi:10.1145/3658129. This article has 137 citations and is from a highest quality peer-reviewed journal.

13. (xu2024brepgenabrep pages 9-11): Xiang Xu, Joseph Lambourne, Pradeep Jayaraman, Zhengqing Wang, Karl Willis, and Yasutaka Furukawa. Brepgen: a b-rep generative diffusion model with structured latent geometry. ACM Transactions on Graphics, 43:1-14, Jul 2024. URL: https://doi.org/10.1145/3658129, doi:10.1145/3658129. This article has 137 citations and is from a highest quality peer-reviewed journal.

14. (xu2024brepgenabrep pages 2-3): Xiang Xu, Joseph Lambourne, Pradeep Jayaraman, Zhengqing Wang, Karl Willis, and Yasutaka Furukawa. Brepgen: a b-rep generative diffusion model with structured latent geometry. ACM Transactions on Graphics, 43:1-14, Jul 2024. URL: https://doi.org/10.1145/3658129, doi:10.1145/3658129. This article has 137 citations and is from a highest quality peer-reviewed journal.

15. (guan2025cadcodertexttocadgeneration pages 1-3): Yandong Guan, Xilin Wang, Xingxi Ming, Jing Zhang, Dong Xu, and Qian Yu. Cad-coder: text-to-cad generation with chain-of-thought and geometric reward. ArXiv, May 2025. URL: https://doi.org/10.48550/arxiv.2505.19713, doi:10.48550/arxiv.2505.19713. This article has 15 citations.

16. (guan2025cadcodertexttocadgeneration pages 16-17): Yandong Guan, Xilin Wang, Xingxi Ming, Jing Zhang, Dong Xu, and Qian Yu. Cad-coder: text-to-cad generation with chain-of-thought and geometric reward. ArXiv, May 2025. URL: https://doi.org/10.48550/arxiv.2505.19713, doi:10.48550/arxiv.2505.19713. This article has 15 citations.

17. (daareyni2025generativeaimeets pages 1-2): Amirmohammad Daareyni, Antti Martikkala, Hossein Mokhtarian, and Iñigo Flores Ituarte. Generative ai meets cad: enhancing engineering design to manufacturing processes with large language models. The International Journal of Advanced Manufacturing Technology, Jun 2025. URL: https://doi.org/10.1007/s00170-025-15830-2, doi:10.1007/s00170-025-15830-2. This article has 24 citations.

18. (ocker2503fromideato pages 1-3): Felix Ocker, Stefan Menzel, Ahmed Sadik, and Thiago Rios. From idea to cad: a language model-driven multi-agent system for collaborative design. ArXiv, Mar 2503. URL: https://doi.org/10.48550/arxiv.2503.04417, doi:10.48550/arxiv.2503.04417. This article has 23 citations.

19. (schupbach2025fromtextto pages 1-2): Aurel Schüpbach, Raul San Miguel, Julian Ferchow, and Mirko Meboldt. From text to design: a framework to leverage llm agents for automated cad generation. Proceedings of the Design Society, 5:1893-1902, Aug 2025. URL: https://doi.org/10.1017/pds.2025.10203, doi:10.1017/pds.2025.10203. This article has 4 citations and is from a peer-reviewed journal.

20. (dong2025histcadgeometricallyconstrained pages 10-12): X Dong, C Li, C Han, P Zheng, J Jing, and Y Song. Histcad: geometrically constrained parametric history-based cad dataset. ArXiv, 2025. URL: https://doi.org/10.48550/arxiv.2602.19171, doi:10.48550/arxiv.2602.19171.

21. (dong2025histcadgeometricallyconstrained pages 2-3): X Dong, C Li, C Han, P Zheng, J Jing, and Y Song. Histcad: geometrically constrained parametric history-based cad dataset. ArXiv, 2025. URL: https://doi.org/10.48550/arxiv.2602.19171, doi:10.48550/arxiv.2602.19171.

22. (xie2505texttocadqueryanew pages 12-15): Haoyang Xie and Feng Ju. Text-to-cadquery: a new paradigm for cad generation with scalable large model capabilities. ArXiv, May 2505. URL: https://doi.org/10.48550/arxiv.2505.06507, doi:10.48550/arxiv.2505.06507. This article has 29 citations.

23. (xie2505texttocadqueryanew pages 3-4): Haoyang Xie and Feng Ju. Text-to-cadquery: a new paradigm for cad generation with scalable large model capabilities. ArXiv, May 2505. URL: https://doi.org/10.48550/arxiv.2505.06507, doi:10.48550/arxiv.2505.06507. This article has 29 citations.

24. (rukhovich2025cadrecodereverseengineering pages 1-2): Danila Rukhovich, Elona Dupont, Dimitrios Mallis, Kseniya Cherenkova, Anis Kacem, and Djamila Aouada. Cad-recode: reverse engineering cad code from point clouds. ArXiv, Dec 2025. URL: https://doi.org/10.48550/arxiv.2412.14042, doi:10.48550/arxiv.2412.14042. This article has 48 citations.

25. (rukhovich2025cadrecodereverseengineering pages 20-21): Danila Rukhovich, Elona Dupont, Dimitrios Mallis, Kseniya Cherenkova, Anis Kacem, and Djamila Aouada. Cad-recode: reverse engineering cad code from point clouds. ArXiv, Dec 2025. URL: https://doi.org/10.48550/arxiv.2412.14042, doi:10.48550/arxiv.2412.14042. This article has 48 citations.

26. (fan2025caddesignerconceptualdesign pages 8-9): Fengxiao Fan, Jingzhe Ni, Xiaolong Yin, Sirui Wang, Xingyu Lu, Qiang Zou, Ruofeng Tong, Min Tang, and Peng Du. Caddesigner: conceptual design of cad models based on general-purpose agent. ArXiv, Aug 2025. URL: https://doi.org/10.48550/arxiv.2508.01031, doi:10.48550/arxiv.2508.01031. This article has 3 citations.