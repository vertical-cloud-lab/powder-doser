Question: Find recent (2022-2025) peer-reviewed and arXiv academic publications on large-language-model and code-generation approaches to hardware design: LLM-based generation of HDL (Verilog/VHDL/Chisel), netlists, analog circuit code, and structured hardware description, plus agentic / multi-step design loops and self-repair. Cover landmark and representative systems (e.g., ChipGPT, ChipNeMo, VerilogEval, RTLLM, AutoChip, AnalogCoder, LaMAGIC, MAGE/agentic-EDA, GPT4AIGChip, self-debugging / self-verification loops) and the benchmarks used to evaluate them (functional correctness, synthesizability, pass@k). For each give: full citation, 3-5 sentence summary, and relevance to LLM-driven generation of microcontroller-centric control electronics and firmware for an open-hardware lab-automation device. Discuss capabilities and limitations (correctness, hallucination of parts or pins, verification, dataset scarcity). Aim for ~10-15 references.

# LLM-Based Code Generation for Hardware Design: A Literature Survey (2022–2025)

## 1. Introduction

The application of large language models (LLMs) to hardware description language (HDL) code generation has emerged as a rapidly growing research direction since 2022. This survey covers ~15 landmark and representative publications spanning Verilog/VHDL generation, analog circuit code synthesis, agentic design loops with self-repair, benchmarks, and domain-adapted models. For each work, a full citation, summary, and relevance assessment to LLM-driven generation of microcontroller-centric control electronics and firmware for open-hardware lab-automation devices is provided. A consolidated reference table is included below.

| Reference | Year | Category | Key Contribution | Benchmark / Evaluation | Key Metric / Result |
|---|---:|---|---|---|---|
| Chang et al., *ChipGPT* | 2023 | HDL Generation / Design-space Search | Introduces a four-stage, zero-code natural-language-to-hardware flow: prompt management, LLM Verilog generation, output correction/optimization, and post-generation search for better PPA. It emphasizes in-context learning rather than retraining and integrates LLM outputs into an EDA-like exploration loop. (chang2023chipgpthowfar pages 1-1, chang2023chipgpthowfar pages 8-9) | Natural-language chip logic tasks with PPA comparison against ChatGPT-style baselines; evaluates generated code quality and human correction burden. (chang2023chipgpthowfar pages 8-9) | Reports up to **47% area reduction** versus original ChatGPT under area-target optimization; human fixes are localized, often fewer than three lines per program. (chang2023chipgpthowfar pages 8-9) |
| Liu et al., *ChipNeMo* | 2023 | Domain Adaptation / Chip Design Assistant | Domain-adapts LLaMA2 for chip design via tokenizer augmentation, continued pretraining, instruction alignment, and retrieval. Targets engineering assistant chat, EDA script generation, and bug analysis rather than pure RTL generation, but is foundational for hardware-specialized LLMs. (liu2023chipnemodomainadaptedllms pages 1-2, liu2023chipnemodomainadaptedllms pages 2-3, liu2023chipnemodomainadaptedllms pages 13-14) | Evaluated on engineering-assistant QA, Python/Tcl EDA script generation, and bug summarization; uses retrieval-augmented and non-RAG settings. (liu2023chipnemodomainadaptedllms pages 1-2, liu2023chipnemodomainadaptedllms pages 5-7) | Uses about **24.1B DAPT tokens**; ChipNeMo-70B reportedly **outperforms GPT-4** on engineering assistant and EDA script generation, with script correctness above 70% and +18% improvement from added SFT on one setting. (liu2023chipnemodomainadaptedllms pages 1-2, liu2023chipnemodomainadaptedllms pages 2-3, liu2023chipnemodomainadaptedllms pages 13-14) |
| Liu et al., *VerilogEval* | 2023 | Benchmark | Establishes one of the first standard benchmarks for LLM-based Verilog generation, using HDLBits-derived problems and automatic evaluation via simulation against golden outputs. It made pass@k-style comparison reproducible across models and catalyzed later fine-tuning work. (pan2025asurveyof pages 6-8) | **156** Verilog problems from HDLBits; functional correctness checked with transient simulation against reference solutions. (pan2025asurveyof pages 6-8) | Standardizes **pass@k / functional correctness** evaluation for Verilog generation; later work builds directly on it. (pan2025asurveyof pages 6-8) |
| Lu et al., *RTLLM* | 2024 | Benchmark / RTL Generation | Proposes an open benchmark for natural-language-to-RTL generation with broader attention to design quality, not just correctness. Also introduces self-planning prompting as a simple but effective inference strategy. (zhong2024llm4edaemergingprogress pages 7-8) | Open benchmark with about **30 hand-crafted designs** and three progressive goals: syntax, functionality, and design quality. Syntax is checked by synthesis/netlist validity, functionality by testbenches, and quality by post-synthesis or implementation metrics. (zhong2024llm4edaemergingprogress pages 7-8) | Makes **syntax / functionality / design-quality** triage explicit; self-planning improves GPT-3.5 performance in the benchmark framework. (pan2025asurveyof pages 6-8, zhong2024llm4edaemergingprogress pages 7-8) |
| Blocklove et al., *AutoChip* / extended TODAES version | 2025 | Agentic / Self-repair | Presents a feedback-driven Verilog generation loop that compiles and simulates LLM outputs, ranks candidates, and iteratively repairs them using EDA feedback. It moves beyond one-shot prompting toward practical self-debugging. (blocklove2025automaticallyimprovingllmbased pages 3-5) | Uses VerilogEval tasks; compares zero-shot generation vs iterative feedback with full-context and succinct-context repair modes. Success is based on compilation and simulation outcomes. (blocklove2025automaticallyimprovingllmbased pages 3-5) | Best case yields **+5.8%** more successful designs than zero-shot and **34.2% lower cost**; mixed-model strategy cuts cost further while preserving gains. (blocklove2025automaticallyimprovingllmbased pages 3-5) |
| Zhao et al., *MAGE* | 2025 | Multi-agent RTL Generation | First open-source multi-agent RTL engine centered on diverse candidate sampling, ranking, debugging, and a state-checkpoint mechanism for targeted fixes. It shows how agent decomposition can dramatically improve RTL correctness. (ravindran2025surveyandbenchmarking pages 5-7, zhao2025mageamultiagent pages 4-5) | Evaluated on VerilogEval-Human and VerilogEval-V2 with Pass@1 as the main metric, using high-temperature candidate generation and mismatch-based ranking before debugging. (zhao2025mageamultiagent pages 4-5) | Achieves **94.8% Pass@1** on VerilogEval-Human and **95.7% Pass@1** on VerilogEval-V2 in the high-temperature setting. (zhao2025mageamultiagent pages 4-5) |
| Tsai et al., *RTLFixer* | 2024 | Agentic / Syntax Repair | Focuses specifically on fixing syntax errors in generated Verilog using Retrieval-Augmented Generation plus ReAct-style iterative reasoning and compiler feedback. It demonstrates that syntax repair alone can unlock large downstream gains in functional pass rates. (tsai2024rtlfixerautomaticallyfixing pages 1-2, tsai2024rtlfixerautomaticallyfixing pages 1-1) | Evaluated on VerilogEval-derived syntax-debug datasets and RTLLM; measures syntax-fix success and downstream VerilogEval pass@1 changes. (tsai2024rtlfixerautomaticallyfixing pages 1-2, tsai2024rtlfixerautomaticallyfixing pages 1-1) | Repairs about **98.5%** of syntax errors; improves pass@1 by **32.3%** on VerilogEval-Machine and **10.1%** on VerilogEval-Human; RTLLM syntax success improves from **73% to 93%**. (tsai2024rtlfixerautomaticallyfixing pages 1-2, tsai2024rtlfixerautomaticallyfixing pages 5-5) |
| Thakur et al., *VeriGen* | 2024 | HDL Generation / Fine-tuning | Fine-tunes CodeGen-family models on GitHub Verilog and textbook data, showing that small in-house domain models can be competitive with commercial APIs. Also releases open-source models and evaluation assets. (jha2025largelanguagemodels pages 6-7, thakur2024verigenalarge pages 19-22) | Evaluates syntactic and functional correctness using custom test suites and benchmark problems spanning basic to advanced modules. (jha2025largelanguagemodels pages 6-7, thakur2024verigenalarge pages 19-22) | Fine-tuned CodeGen-16B shows **41% improvement in syntactic correctness** over its pretrained counterpart and can slightly exceed GPT-3.5 on the authors’ evaluation. (jha2025largelanguagemodels pages 6-7) |
| Lai et al., *AnalogCoder* | 2025 | Analog / Agentic Code Generation | Introduces the first training-free LLM agent for analog circuit design by generating Python/PySpice code rather than direct low-level netlists. Combines prompt engineering, feedback-enhanced design flow, and a circuit tool library for reusable subcircuits. (lai2025analogcoderanalogcircuit pages 1-2, lai2025analogcoderanalogcircuit pages 2-4, lai2025analogcoderanalogcircuit pages 7-8) | Evaluated on a **24-task** analog benchmark with Pass@1 / Pass@5 and solved-task counts; includes basic and composite analog designs. (lai2025analogcoderanalogcircuit pages 2-4, lai2025analogcoderanalogcircuit pages 7-8) | Solves **20/24** tasks, outperforming plain GPT-4o (**15/24**) and other baselines; most successful designs complete within a few attempts. (lai2025analogcoderanalogcircuit pages 1-2, lai2025analogcoderanalogcircuit pages 2-4, lai2025analogcoderanalogcircuit pages 9-11) |
| Chang et al., *LaMAGIC* | 2024 | Analog Topology Generation | Uses supervised fine-tuning to cast analog topology generation as LM sequence generation over canonical graph/circuit formulations. It is notable for single-pass generation rather than many simulation-search iterations. (chang2024lamagiclanguagemodelbasedtopology pages 9-10, chang2024lamagiclanguagemodelbasedtopology pages 1-2, chang2024lamagiclanguagemodelbasedtopology pages 2-3) | Evaluates success rate under tolerance thresholds, including a strict **0.01** tolerance; compares multiple circuit encodings including adjacency-matrix-based forms. (chang2024lamagiclanguagemodelbasedtopology pages 9-10, chang2024lamagiclanguagemodelbasedtopology pages 6-8) | Reports up to **96% success rate** under strict tolerance 0.01; adjacency-matrix/float-style formulations improve effectiveness on complex circuits. (chang2024lamagiclanguagemodelbasedtopology pages 9-10, chang2024lamagiclanguagemodelbasedtopology pages 1-2) |
| Fu et al., *GPT4AIGChip* | 2023 | Accelerator Design / HLS | Develops a demo-augmented prompt-generation pipeline for AI accelerator generation, with module decomposition and in-context learning over HLS examples. It explicitly studies why generic LLMs fail on long, dependency-heavy HLS code and proposes hardware-aware prompt structuring. (fu2023gpt4aigchiptowardsnextgeneration pages 3-4, fu2023gpt4aigchiptowardsnextgeneration pages 1-1, fu2023gpt4aigchiptowardsnextgeneration pages 2-3) | Evaluated through ablations on prompt format and demo selection for HLS accelerator modules; uses Pass@10 and design comparisons under DSP/resource constraints. (fu2023gpt4aigchiptowardsnextgeneration pages 7-8) | Demo-augmented prompting improves **Pass@10 by 50%** over no-demo and **30%** over a high-level-description baseline on one reported module family. (fu2023gpt4aigchiptowardsnextgeneration pages 7-8) |
| Blocklove et al., *Chip-Chat* | 2023 | Conversational Hardware Design / Case Study | Demonstrates conversational co-design of an 8-bit accumulator-based microprocessor with an LLM, culminating in a tapeout. It is a landmark proof-of-concept for AI-assisted hardware co-architecture rather than benchmark-driven RTL generation. (paper_search result: Blocklove et al. 2023) | Real-world case study with SkyWater 130nm/TinyTapeout-style flow; evaluates whether conversational prompting can produce tapeout-ready HDL. | Reported as the **first wholly AI-written HDL sent to tapeout** for an **8-bit processor**. |
| Liu et al., *RTLCoder* | 2025 | Open-source RTL LLM | Presents a compact open-source **7B** RTL-focused model trained on a dedicated RTL dataset and optimized for local/private deployment. It targets practical use as a private engineering assistant. (paper_search result: Liu et al. 2025 RTLCoder) | Evaluated on representative RTL benchmarks including RTLLM and VerilogEval variants. | Reported to **outperform GPT-3.5** on representative RTL benchmarks; quantized 4-bit version can run locally with slight degradation. |
| Bhandari et al., *Masala-CHAI* | 2024 | Analog Dataset / SPICE Netlists | Builds a large-scale schematic-to-SPICE dataset and automated workflow for analog netlist generation from circuit images. Its main value is infrastructure: creating data needed for analog LLM fine-tuning and benchmarking. (paper_search result: Bhandari et al. 2024 Masala-CHAI) | Corpus built from **7,500** schematics across **10 textbooks**; benchmarks open and proprietary LLMs for schematic-to-netlist tasks. | Fine-tuned models used in agentic frameworks such as AnalogCoder show **46% Pass@1 improvement**; dataset is positioned as a key response to analog data scarcity. (paper_search result: Bhandari et al. 2024 Masala-CHAI) |
| Pinckney et al., *Revisiting VerilogEval* | 2025 | Benchmark Update / Evaluation | Updates VerilogEval with better prompt support, failure classification, and spec-to-RTL evaluation. It quantifies the rapid progress of both frontier and domain-specific models over one year. (paper_search result: Pinckney et al. 2025 Revisiting VerilogEval) | Improved VerilogEval v2 benchmark suite for specification-to-RTL and related tasks, with prompt-engineering support and failure analysis. | Reports **GPT-4o at 63% pass rate** on specification-to-RTL tasks; Llama3.1-405B reaches **58%**, and small domain models such as RTL-Coder 6.7B reach **34%**. (paper_search result: Pinckney et al. 2025 Revisiting VerilogEval) |
| Vungarala et al., *SPICEPilot* | 2024 | Analog / SPICE Code Generation | Provides a Python/PySpice dataset and framework for evaluating LLM generation of SPICE simulation code, highlighting that analog code generation remains knowledge-starved and error-prone. It is a useful complementary benchmark/infrastructure paper for analog control electronics generation. (paper_search result: Vungarala et al. 2024 SPICEPilot) | Benchmarks LLM generation of SPICE simulation scripts across different circuit configurations. | Main contribution is benchmark/dataset infrastructure rather than a headline SOTA score; explicitly documents the limitations of current LLMs for SPICE generation. |


*Table: This table summarizes ~15 landmark and representative 2023-2025 publications on LLM-based hardware and circuit generation, including RTL, benchmarks, agentic repair loops, analog design, and accelerator generation. It is useful as a compact map of systems, benchmarks, and headline results for comparing capabilities and limitations across the field.*

---

## 2. Individual Paper Summaries and Relevance

### 2.1 ChipGPT (Chang et al., 2023)

**Citation:** K. Chang, Y. Wang, H. Ren, M. Wang, S. Liang, Y. Han, H. Li, and X. Li, "ChipGPT: How Far Are We from Natural Language Hardware Design," *arXiv:2305.14019*, May 2023.

**Summary:** ChipGPT proposes a four-stage, zero-code logic design framework that uses in-context learning with GPT-3.5 to generate Verilog from natural-language specifications. A Prompt Manager formulates queries, an Output Manager corrects and optimizes the generated programs, and an Enumerative Search stage explores the resulting design space to select PPA-optimal candidates. The framework achieves up to 47% area reduction compared to raw ChatGPT outputs and requires only localized human corrections (fewer than three lines per program) (chang2023chipgpthowfar pages 1-1, chang2023chipgpthowfar pages 8-9). The authors emphasize that current LLMs lack awareness of PPA constraints and require post-processing to achieve synthesizable, optimized designs (chang2023chipgpthowfar pages 3-4).

**Relevance to open-hardware lab automation:** ChipGPT's natural-language-to-Verilog pipeline could be adapted for generating FPGA-based control logic (e.g., stepper motor drivers, sensor interfaces) for lab automation devices. However, the need for post-LLM PPA optimization and human correction limits fully autonomous generation.

### 2.2 ChipNeMo (Liu et al., 2023)

**Citation:** M. Liu et al., "ChipNeMo: Domain-Adapted LLMs for Chip Design," *arXiv:2311.00176*, Oct 2023.

**Summary:** ChipNeMo adapts LLaMA2 models (7B/13B/70B) for chip design through domain-adaptive tokenization, continued pretraining on approximately 24.1 billion tokens of proprietary chip-design data, instruction alignment, and retrieval-augmented generation (liu2023chipnemodomainadaptedllms pages 1-2, liu2023chipnemodomainadaptedllms pages 13-14). The largest model, ChipNeMo-70B, outperforms GPT-4 on engineering assistant chatbot and EDA script generation tasks, with script correctness above 70% and an 18% improvement from additional supervised fine-tuning (liu2023chipnemodomainadaptedllms pages 2-3). Domain-adaptive pretraining accounts for only ~1.5% of original pretraining compute cost (liu2023chipnemodomainadaptedllms pages 4-5).

**Relevance:** ChipNeMo's domain-adaptation methodology (DAPT + RAG) could be applied to adapt smaller open-source LLMs for microcontroller firmware generation, embedding knowledge of specific MCU peripherals, register maps, and EDA tool APIs relevant to lab-automation boards.

### 2.3 VerilogEval (Liu et al., 2023)

**Citation:** M. Liu, N. Pinckney, B. Khailany, and H. Ren, "VerilogEval: Evaluating Large Language Models for Verilog Code Generation," *arXiv:2309.07544*, Sep 2023.

**Summary:** VerilogEval establishes one of the first standardized benchmarks for evaluating LLM-based Verilog generation, comprising 156 problems derived from the HDLBits instructional website. Problems span combinational circuits to complex finite state machines, and functional correctness is assessed by comparing transient simulation outputs against golden reference solutions using the pass@k metric (pan2025asurveyof pages 6-8). The authors also demonstrate that supervised fine-tuning with LLM-generated synthetic problem-code pairs can improve Verilog generation capability.

**Relevance:** VerilogEval provides a directly applicable evaluation framework for assessing whether an LLM can generate the types of digital logic modules (counters, FSMs, SPI/I2C controllers) common in lab-automation control electronics.

### 2.4 RTLLM (Lu et al., 2024)

**Citation:** Y. Lu, S. Liu, Q. Zhang, and Z. Xie, "RTLLM: An Open-Source Benchmark for Design RTL Generation with Large Language Model," *ASP-DAC 2024*, pp. 722–727.

**Summary:** RTLLM provides an open-source RTL generation benchmark with approximately 30 hand-crafted designs that evaluates three progressive goals: syntax (verified by synthesis/netlist generation), functionality (tested with comprehensive testbenches), and design quality (assessed by post-synthesis PPA metrics) (zhong2024llm4edaemergingprogress pages 7-8). The work also introduces self-planning, a simple but effective prompt-engineering technique that significantly improves GPT-3.5 performance by having the model decompose the task before generating code (pan2025asurveyof pages 6-8).

**Relevance:** RTLLM's three-tier evaluation (syntax → function → quality) maps well to the needs of lab-automation hardware, where generated RTL must not only compile but also meet timing and resource constraints on low-cost FPGAs.

### 2.5 AutoChip / Extended Version (Blocklove et al., 2023/2025)

**Citation:** J. Blocklove, S. Thakur, B. Tan, H. Pearce, S. Garg, and R. Karri, "Automatically Improving LLM-based Verilog Generation Using EDA Tool Feedback," *ACM TODAES*, Mar 2025. doi:10.1145/3723876.

**Summary:** AutoChip is the first open-source, feedback-driven Verilog generation framework that iteratively compiles and simulates LLM outputs, feeds compiler and simulation errors back to the LLM, and ranks candidates by functional correctness (blocklove2025automaticallyimprovingllmbased pages 3-5). Evaluation on VerilogEval shows that EDA tool feedback with GPT-4o yields 5.8% more successful designs than zero-shot prompting, with a 34.2% decrease in cost. A mixed-model strategy (using smaller models for initial attempts and GPT-4o only for final refinement) achieves equivalent success at 89.6% lower cost than pure zero-shot GPT-4o (blocklove2025automaticallyimprovingllmbased pages 3-5).

**Relevance:** AutoChip's iterative compile→simulate→repair loop is directly applicable to generating and debugging microcontroller peripheral RTL or firmware C code for lab automation, as it leverages standard open-source toolchains (Icarus Verilog) that are accessible to open-hardware projects.

### 2.6 MAGE (Zhao et al., 2025)

**Citation:** Y. Zhao, H. Zhang, H. Huang, Z. Yu, and J. Zhao, "MAGE: A Multi-Agent Engine for Automated RTL Code Generation," *arXiv:2412.07822*, Dec 2025.

**Summary:** MAGE introduces the first open-source multi-agent system for RTL generation, featuring high-temperature candidate sampling to explore diverse code solutions, a mismatch-based ranking mechanism, and a Verilog-state checkpoint debugging system that enables early detection of functional errors with targeted repair feedback (zhao2025mageamultiagent pages 4-5). On VerilogEval-V2, MAGE achieves 95.7% Pass@1, surpassing Claude-3.5-sonnet by 23.3 percentage points (ravindran2025surveyandbenchmarking pages 5-7, zhao2025mageamultiagent pages 4-5). The multi-agent decomposition separates generation, verification, and debugging responsibilities across specialized LLM agents.

**Relevance:** MAGE's multi-agent architecture—with separate generation and verification agents—provides a blueprint for building automated design tools for lab-automation hardware, where a "generate → simulate → debug" loop could produce and validate SPI controllers, ADC interfaces, or motor-control state machines.

### 2.7 RTLFixer (Tsai et al., 2024)

**Citation:** Y.-D. Tsai, M. Liu, and H. Ren, "RTLFixer: Automatically Fixing RTL Syntax Errors with Large Language Model," *DAC 2024*, pp. 1–6. doi:10.1145/3649329.3657353.

**Summary:** RTLFixer targets the dominant error class in LLM-generated Verilog—syntax errors, which account for approximately 55% of all failures. It combines Retrieval-Augmented Generation with a compiler-error knowledge base and ReAct-style iterative reasoning to achieve a 98.5% syntax repair success rate on a 212-problem debugging dataset derived from VerilogEval (tsai2024rtlfixerautomaticallyfixing pages 1-2, tsai2024rtlfixerautomaticallyfixing pages 1-1). This translates to a 32.3% improvement in pass@1 on VerilogEval-Machine and 10.1% on VerilogEval-Human, and raises RTLLM syntax success from 73% to 93% (tsai2024rtlfixerautomaticallyfixing pages 5-5).

**Relevance:** Syntax repair is critical for non-expert users in open-hardware projects. RTLFixer's approach of mining compiler error messages and iteratively reasoning about fixes could be adapted to debug generated firmware (C/C++) or HDL for microcontroller-based lab instruments.

### 2.8 VeriGen (Thakur et al., 2024)

**Citation:** S. Thakur, B. Ahmad, H. Pearce, B. Tan, B. Dolan-Gavitt, R. Karri, and S. Garg, "VeriGen: A Large Language Model for Verilog Code Generation," *ACM TODAES*, vol. 29, no. 3, pp. 1–31, Apr 2024.

**Summary:** VeriGen fine-tunes CodeGen-family models on curated GitHub Verilog and textbook data, demonstrating that relatively small (up to 16B parameter) open-source models can match or slightly exceed GPT-3.5 in Verilog code generation (jha2025largelanguagemodels pages 6-7). Including textbook examples improves understanding of hardware constructs. The fine-tuned model shows a 41% improvement in syntactic correctness over its pretrained counterpart, though no model achieved full functional correctness across all benchmark problems (thakur2024verigenalarge pages 19-22).

**Relevance:** VeriGen's demonstration that small, locally deployable models can compete with commercial APIs is especially valuable for open-hardware communities that require private, low-cost generation of RTL for lab devices without relying on cloud services.

### 2.9 AnalogCoder (Lai et al., 2025)

**Citation:** Y. Lai, S. Lee, G. Chen, S. Poddar, M. Hu, D. Z. Pan, and P. Luo, "AnalogCoder: Analog Circuit Design via Training-Free Code Generation," *arXiv:2405.14918*, May 2025.

**Summary:** AnalogCoder is the first training-free LLM agent for analog circuit design, generating Python/PySpice code from natural-language specifications rather than direct netlists. It incorporates a feedback-enhanced design flow with domain-specific prompts and a circuit tool library that archives successful designs as reusable modular subcircuits (lai2025analogcoderanalogcircuit pages 1-2, lai2025analogcoderanalogcircuit pages 2-4). On a 24-task analog benchmark, AnalogCoder solved 20 tasks versus 15 for plain GPT-4o, with most successful designs completing within three attempts (lai2025analogcoderanalogcircuit pages 2-4, lai2025analogcoderanalogcircuit pages 9-11). Small discrepancies in component values can render circuits non-functional, underscoring the sensitivity of analog design (lai2025analogcoderanalogcircuit pages 8-9).

**Relevance:** AnalogCoder's Python-code-generation approach for analog circuits is highly relevant to lab-automation devices that require mixed-signal front-ends (e.g., sensor conditioning amplifiers, voltage references, LDOs). The tool library concept could be adapted to archive proven subcircuits for common lab instrument analog blocks.

### 2.10 LaMAGIC (Chang et al., 2024)

**Citation:** C.-C. Chang, Y. Shen, S. Fan, J. Li, S. Zhang, N. Cao, Y. Chen, and X. Zhang, "LaMAGIC: Language-Model-based Topology Generation for Analog Integrated Circuits," *arXiv:2407.18269*, Jul 2024.

**Summary:** LaMAGIC applies supervised fine-tuning to adapt a language model for single-pass analog circuit topology generation, representing circuits as canonical graph formulations compatible with autoregressive decoding. The adjacency-matrix-based formulation with floating-point inputs achieves up to 96% success rate under a strict tolerance of 0.01 for power-converter topology tasks (chang2024lamagiclanguagemodelbasedtopology pages 9-10, chang2024lamagiclanguagemodelbasedtopology pages 1-2). The successor work, LaMAGIC2, further improves success rates by 34% and reduces mean squared errors by 10× through a more compact formulation (chang2025lamagic2advancedcircuit pages 1-2).

**Relevance:** LaMAGIC's topology generation could assist in automatically synthesizing power converter or filter topologies for lab-automation power supplies, though the approach is currently limited to specific component families (capacitors, inductors, switches).

### 2.11 GPT4AIGChip (Fu et al., 2023)

**Citation:** Y. Fu, Y. Zhang, Z. Yu, S. Li, Z. Ye, C. Li, C. Wan, and Y. Lin, "GPT4AIGChip: Towards Next-Generation AI Accelerator Design Automation via Large Language Models," *ICCAD 2023*, pp. 1–9.

**Summary:** GPT4AIGChip develops a demo-augmented prompt-generation pipeline that leverages in-context learning to guide LLMs toward producing AI accelerator HLS implementations. It decouples hardware modules to avoid long-context dependencies and selects correlated demonstrations to improve generation quality, achieving a 50% improvement in Pass@10 over no-demo baselines (fu2023gpt4aigchiptowardsnextgeneration pages 3-4, fu2023gpt4aigchiptowardsnextgeneration pages 7-8). Key insights include that open-source models achieve 0% Pass@100 without fine-tuning on HLS tasks and that verification cost remains a substantial unaddressed bottleneck (fu2023gpt4aigchiptowardsnextgeneration pages 8-9, fu2023gpt4aigchiptowardsnextgeneration pages 2-3).

**Relevance:** The demo-augmented prompting strategy and modular decomposition are transferable to generating microcontroller firmware modules (e.g., DMA configurations, timer setups) where few annotated examples exist but in-context learning can be effective.

### 2.12 Chip-Chat (Blocklove et al., 2023)

**Citation:** J. Blocklove, S. Garg, R. Karri, and H. Pearce, "Chip-Chat: Challenges and Opportunities in Conversational Hardware Design," *MLCAD 2023*, pp. 1–6.

**Summary:** Chip-Chat demonstrates conversational co-design of an 8-bit accumulator-based microprocessor between a hardware engineer and ChatGPT-4, culminating in what the authors describe as the first wholly AI-written HDL sent to tapeout via a SkyWater 130nm shuttle (jha2025largelanguagemodels pages 6-7). The work highlights both the promise and the fragility of conversational hardware design: the engineer provides architectural guidance while the LLM generates all HDL code.

**Relevance:** This is a proof-of-concept directly relevant to open-hardware lab automation: an engineer could conversationally specify a simple MCU or peripheral controller and have the LLM generate all HDL, provided verification is robust.

### 2.13 RTLCoder (Liu et al., 2025)

**Citation:** S. Liu, W. Fang, Y. Lu, J. Wang, Q. Zhang, H. Zhang, and Z. Xie, "RTLCoder: Fully Open-Source and Efficient LLM-Assisted RTL Code Generation Technique," *IEEE TCAD*, vol. 44, pp. 1448–1461, Apr 2025.

**Summary:** RTLCoder is a 7B-parameter open-source LLM that outperforms GPT-3.5 on all representative RTL benchmarks and matches GPT-4 on VerilogEval-Machine through customized training on a curated RTL dataset. A 4-bit quantized version runs on a single laptop, enabling private, local deployment with only slight performance degradation (ravindran2025surveyandbenchmarking pages 5-7).

**Relevance:** RTLCoder's small footprint and open-source nature make it ideal for integration into open-hardware development workflows, where cloud API costs and data privacy are concerns.

### 2.14 Masala-CHAI (Bhandari et al., 2024)

**Citation:** J. Bhandari, V. Bhat, Y. He, S. Garg, H. Rahmani, and R. Karri, "Masala-CHAI: A Large-Scale SPICE Netlist Dataset for Analog Circuits by Harnessing AI," *arXiv:2411.14299*, Nov 2024.

**Summary:** Masala-CHAI builds a fully automated pipeline leveraging GPT-4 multimodal capabilities to generate SPICE netlists from circuit schematic images across 7,500 schematics spanning 10 textbooks. Models fine-tuned on the resulting corpus show a 46% improvement in Pass@1 when used within agentic frameworks such as AnalogCoder (firouzi2025chipmndllmsfor pages 3-4). The work directly addresses the persistent data-scarcity problem in analog circuit design.

**Relevance:** For lab-automation devices that require custom analog front-ends, Masala-CHAI's dataset and automated pipeline could enable fine-tuning of local models to generate SPICE netlists for sensor conditioning or power management circuits.

### 2.15 Revisiting VerilogEval (Pinckney et al., 2025)

**Citation:** N. Pinckney, C. Batten, M. Liu, H. Ren, and B. Khailany, "Revisiting VerilogEval: A Year of Improvements in Large-Language Models for Hardware Code Generation," *ACM TODAES*, Feb 2025. doi:10.1145/3718088.

**Summary:** This follow-up extends VerilogEval with specification-to-RTL tasks, automatic failure classification, and in-context learning support. It documents rapid model improvement: GPT-4o achieves 63% pass rate on specification-to-RTL tasks, Llama3.1-405B reaches 58%, and the small domain-specific RTL-Coder 6.7B achieves 34% (ravindran2025surveyandbenchmarking pages 5-7). The authors emphasize that prompt engineering remains crucial and varies widely across models and tasks.

**Relevance:** The updated benchmark provides a realistic assessment of current LLM capability for specification-driven RTL generation, directly applicable to evaluating whether LLMs can reliably generate the digital control logic needed in lab instruments.

---

## 3. Benchmarks and Evaluation Methodology

The field has converged on several evaluation paradigms:

- **Pass@k metrics:** Derived from software code generation (HumanEval), pass@k measures the probability that at least one of *k* generated candidates is functionally correct. VerilogEval and RTLLM both adopt this framework with *n* = 10–20 samples per problem (teng2025verirlboostingthe pages 6-7, pan2025asurveyof pages 6-8).

- **Three-tier evaluation (RTLLM):** Syntax correctness (compilation/synthesis), functional correctness (testbench simulation), and design quality (post-synthesis PPA) provide progressively more demanding evaluation levels (zhong2024llm4edaemergingprogress pages 7-8).

- **Waveform-level functional verification:** Used by MAGE's state-checkpoint mechanism and ProtocolLLM's timing-aware simulation pipeline to catch protocol-level misbehaviors invisible to syntax-only checking (zhao2025mageamultiagent pages 4-5, sheth2506protocolllmrtlbenchmark pages 1-2).

- **Analog circuit benchmarks:** AnalogCoder's 24-task benchmark evaluates requirement checks, operating-point verification, DC sweep correctness, and functional simulation (lai2025analogcoderanalogcircuit pages 26-28). LaMAGIC uses success rate under strict tolerance (0.01) against target specifications (chang2024lamagiclanguagemodelbasedtopology pages 9-10).

---

## 4. Capabilities and Limitations

### 4.1 Current Capabilities

Modern LLM-based systems can generate functionally correct Verilog for simple to moderate-complexity digital circuits, with state-of-the-art multi-agent systems reaching 95.7% Pass@1 on VerilogEval (zhao2025mageamultiagent pages 4-5). Domain-adapted models like ChipNeMo outperform general-purpose GPT-4 on chip-specific tasks when trained on even modest domain corpora (liu2023chipnemodomainadaptedllms pages 1-2). Feedback-driven repair loops (AutoChip, RTLFixer) substantially improve both syntax and functional correctness over single-shot generation (blocklove2025automaticallyimprovingllmbased pages 3-5, tsai2024rtlfixerautomaticallyfixing pages 1-2). For analog circuits, training-free agents like AnalogCoder can produce working PySpice designs for 20 out of 24 benchmark tasks (lai2025analogcoderanalogcircuit pages 2-4).

### 4.2 Hallucination of Parts, Pins, and Signals

LLMs are prone to generating unnecessary ports, hallucinating non-existent module interfaces, and producing variable type/size mismatches (sandal2401zeroshotrtlcode pages 3-4). Practical debugging of RTLLM benchmarks required fixing module-name mismatches, adding missing signals (e.g., `res_ready`), and correcting instantiation order—indicating that hallucinated or mismatched ports and signals are a real and recurring issue (ravindran2025surveyandbenchmarking pages 13-15). In analog contexts, even small discrepancies in component values can render circuits non-functional (lai2025analogcoderanalogcircuit pages 8-9).

### 4.3 Correctness and Specific Failure Modes

Detailed failure analysis reveals systematic error patterns in LLM-generated RTL (ravindran2025surveyandbenchmarking pages 15-16):

- **FSM mis-sequencing:** Incorrect ordering of start/active/done states leads to premature termination or extra clock cycles.
- **State-space oversimplification:** Collapsing required states skips timing gaps and induces premature transitions.
- **Handshake drift:** Ready/valid signals asserted one cycle early or late desynchronize modules and can produce deadlocks or stale outputs.
- **Blocking vs. non-blocking misuse:** Using `=` in sequential logic (or mixing with `<=`) induces race conditions and simulation/synthesis mismatches.
- **Moore/Mealy confusion:** Incorrect output classification produces combinational glitches.

For communication protocols (SPI, I2C, UART, AXI), most models fail to generate implementations that meet timing constraints, with complex protocols exposing deeper weaknesses (sheth2506protocolllmrtlbenchmark pages 5-6, sheth2506protocolllmrtlbenchmark pages 1-2).

### 4.4 Verification Gaps

LLMs lack deep understanding of formal verification, model checking, temporal logic, and SVA assertions, and cannot reliably detect subtle bugs such as clock-domain crossing errors, incorrect state transitions, or resource contention (abdollahi2024hardwaredesignand pages 47-48). Verification cost is highlighted as a substantial unaddressed bottleneck even in advanced systems like GPT4AIGChip (fu2023gpt4aigchiptowardsnextgeneration pages 8-9). Integration with simulation, synthesis, and formal tools remains essential and largely manual (abdollahi2024hardwaredesignand pages 38-39).

### 4.5 Dataset Scarcity

Verilog and VHDL constitute a minuscule fraction of LLM pretraining corpora. High-quality, annotated hardware design datasets are scarce, often proprietary, and heterogeneous (abdollahi2024hardwaredesignanda pages 39-41, abdollahi2024hardwaredesignand pages 38-39). The limited availability of well-annotated RTL code for instruction-tuning and fine-tuning is a critical bottleneck (sandal2401zeroshotrtlcode pages 3-4). Data augmentation efforts (ChipGPT-FT, RTLCoder-Data, Masala-CHAI) are beginning to address this gap but remain insufficient for complex designs (zhong2024llm4edaemergingprogress pages 7-8).

---

## 5. Relevance to Microcontroller-Centric Lab-Automation Devices

For an open-hardware lab-automation device built around a microcontroller (e.g., STM32, ESP32, or an FPGA soft-core), the surveyed works suggest the following opportunities and cautions:

**Opportunities:** (1) Natural-language-to-Verilog pipelines (ChipGPT, AutoChip) can generate peripheral controllers (SPI, I2C, PWM, ADC interfaces) from specifications, significantly lowering the barrier for non-expert designers. (2) Feedback-driven loops (AutoChip, MAGE, RTLFixer) can iteratively repair generated code using open-source simulators (Icarus Verilog, Verilator), fitting naturally into open-hardware CI/CD workflows. (3) AnalogCoder's Python/PySpice approach could automate design of analog conditioning circuits (amplifiers, filters, voltage references) common in lab instruments. (4) Small open-source models (RTLCoder at 7B parameters, VeriGen) can run locally, preserving IP privacy and eliminating API costs.

**Cautions:** (1) Protocol-level correctness for communication buses (SPI, I2C, UART) remains unreliable, with timing violations that pass syntax checks but fail waveform verification (sheth2506protocolllmrtlbenchmark pages 5-6, sheth2506protocolllmrtlbenchmark pages 1-2). (2) Hallucination of pin names, register addresses, and peripheral configurations is a concrete risk when targeting specific MCU families, as LLMs may confabulate non-existent registers or misremember pin mappings. (3) Analog component value hallucination can produce non-functional circuits, necessitating simulation-in-the-loop verification. (4) No existing system provides end-to-end verified generation from specification to manufactured PCB/FPGA bitstream without human oversight—verification remains the critical gap.

---

## 6. Conclusion

The field of LLM-driven hardware design has progressed rapidly from early proof-of-concept demonstrations (ChipGPT, Chip-Chat) to sophisticated multi-agent systems (MAGE) achieving >95% functional correctness on standard benchmarks. Domain adaptation (ChipNeMo), open benchmarks (VerilogEval, RTLLM), feedback-driven repair (AutoChip, RTLFixer), and analog-specific agents (AnalogCoder, LaMAGIC) collectively establish a rich ecosystem. However, significant challenges remain in correctness for complex protocols, verification integration, dataset scarcity, and hallucination of hardware-specific details—all of which are particularly consequential for safety-relevant lab-automation instrumentation where incorrect hardware behavior could damage samples or equipment.

References

1. (chang2023chipgpthowfar pages 1-1): Kaiyan Chang, Ying Wang, Haimeng Ren, Mengdi Wang, Shengwen Liang, Yinhe Han, Huawei Li, and Xiaowei Li. Chipgpt: how far are we from natural language hardware design. ArXiv, May 2023. URL: https://doi.org/10.48550/arxiv.2305.14019, doi:10.48550/arxiv.2305.14019. This article has 216 citations.

2. (chang2023chipgpthowfar pages 8-9): Kaiyan Chang, Ying Wang, Haimeng Ren, Mengdi Wang, Shengwen Liang, Yinhe Han, Huawei Li, and Xiaowei Li. Chipgpt: how far are we from natural language hardware design. ArXiv, May 2023. URL: https://doi.org/10.48550/arxiv.2305.14019, doi:10.48550/arxiv.2305.14019. This article has 216 citations.

3. (liu2023chipnemodomainadaptedllms pages 1-2): Mingjie Liu, Teodor-Dumitru Ene, Robert Kirby, Chris Cheng, Nathaniel Pinckney, Rongjian Liang, Jonah Alben, Himyanshu Anand, Sanmitra Banerjee, Ismet Bayraktaroglu, Bonita Bhaskaran, Bryan Catanzaro, Arjun Chaudhuri, Sharon Clay, Bill Dally, Laura Dang, Parikshit Deshpande, Siddhanth Dhodhi, Sameer Halepete, Eric Hill, Jiashang Hu, Sumit Jain, Ankit Jindal, Brucek Khailany, George Kokai, Kishor Kunal, Xiaowei Li, Charley Lind, Hao Liu, Stuart Oberman, Sujeet Omar, Ghasem Pasandi, Sreedhar Pratty, Jonathan Raiman, Ambar Sarkar, Zhengjiang Shao, Hanfei Sun, Pratik P Suthar, Varun Tej, Walker Turner, Kaizhe Xu, and Haoxing Ren. Chipnemo: domain-adapted llms for chip design. ArXiv, Oct 2023. URL: https://doi.org/10.48550/arxiv.2311.00176, doi:10.48550/arxiv.2311.00176. This article has 342 citations.

4. (liu2023chipnemodomainadaptedllms pages 2-3): Mingjie Liu, Teodor-Dumitru Ene, Robert Kirby, Chris Cheng, Nathaniel Pinckney, Rongjian Liang, Jonah Alben, Himyanshu Anand, Sanmitra Banerjee, Ismet Bayraktaroglu, Bonita Bhaskaran, Bryan Catanzaro, Arjun Chaudhuri, Sharon Clay, Bill Dally, Laura Dang, Parikshit Deshpande, Siddhanth Dhodhi, Sameer Halepete, Eric Hill, Jiashang Hu, Sumit Jain, Ankit Jindal, Brucek Khailany, George Kokai, Kishor Kunal, Xiaowei Li, Charley Lind, Hao Liu, Stuart Oberman, Sujeet Omar, Ghasem Pasandi, Sreedhar Pratty, Jonathan Raiman, Ambar Sarkar, Zhengjiang Shao, Hanfei Sun, Pratik P Suthar, Varun Tej, Walker Turner, Kaizhe Xu, and Haoxing Ren. Chipnemo: domain-adapted llms for chip design. ArXiv, Oct 2023. URL: https://doi.org/10.48550/arxiv.2311.00176, doi:10.48550/arxiv.2311.00176. This article has 342 citations.

5. (liu2023chipnemodomainadaptedllms pages 13-14): Mingjie Liu, Teodor-Dumitru Ene, Robert Kirby, Chris Cheng, Nathaniel Pinckney, Rongjian Liang, Jonah Alben, Himyanshu Anand, Sanmitra Banerjee, Ismet Bayraktaroglu, Bonita Bhaskaran, Bryan Catanzaro, Arjun Chaudhuri, Sharon Clay, Bill Dally, Laura Dang, Parikshit Deshpande, Siddhanth Dhodhi, Sameer Halepete, Eric Hill, Jiashang Hu, Sumit Jain, Ankit Jindal, Brucek Khailany, George Kokai, Kishor Kunal, Xiaowei Li, Charley Lind, Hao Liu, Stuart Oberman, Sujeet Omar, Ghasem Pasandi, Sreedhar Pratty, Jonathan Raiman, Ambar Sarkar, Zhengjiang Shao, Hanfei Sun, Pratik P Suthar, Varun Tej, Walker Turner, Kaizhe Xu, and Haoxing Ren. Chipnemo: domain-adapted llms for chip design. ArXiv, Oct 2023. URL: https://doi.org/10.48550/arxiv.2311.00176, doi:10.48550/arxiv.2311.00176. This article has 342 citations.

6. (liu2023chipnemodomainadaptedllms pages 5-7): Mingjie Liu, Teodor-Dumitru Ene, Robert Kirby, Chris Cheng, Nathaniel Pinckney, Rongjian Liang, Jonah Alben, Himyanshu Anand, Sanmitra Banerjee, Ismet Bayraktaroglu, Bonita Bhaskaran, Bryan Catanzaro, Arjun Chaudhuri, Sharon Clay, Bill Dally, Laura Dang, Parikshit Deshpande, Siddhanth Dhodhi, Sameer Halepete, Eric Hill, Jiashang Hu, Sumit Jain, Ankit Jindal, Brucek Khailany, George Kokai, Kishor Kunal, Xiaowei Li, Charley Lind, Hao Liu, Stuart Oberman, Sujeet Omar, Ghasem Pasandi, Sreedhar Pratty, Jonathan Raiman, Ambar Sarkar, Zhengjiang Shao, Hanfei Sun, Pratik P Suthar, Varun Tej, Walker Turner, Kaizhe Xu, and Haoxing Ren. Chipnemo: domain-adapted llms for chip design. ArXiv, Oct 2023. URL: https://doi.org/10.48550/arxiv.2311.00176, doi:10.48550/arxiv.2311.00176. This article has 342 citations.

7. (pan2025asurveyof pages 6-8): Jingyu Pan, Guanglei Zhou, Chen-Chia Chang, Isaac Jacobson, Jiang Hu, and Yiran Chen. A survey of research in large language models for electronic design automation. Feb 2025. URL: https://doi.org/10.1145/3715324, doi:10.1145/3715324. This article has 109 citations and is from a peer-reviewed journal.

8. (zhong2024llm4edaemergingprogress pages 7-8): Ruizhe Zhong, Xingbo Du, Shixiong Kai, Zhentao Tang, Siyuan Xu, Hui-Ling Zhen, Jianye Hao, Qiang Xu, Mingxuan Yuan, and Junchi Yan. Llm4eda: emerging progress in large language models for electronic design automation. Preprint, Jan 2024. URL: https://doi.org/10.48550/arxiv.2401.12224, doi:10.48550/arxiv.2401.12224. This article has 78 citations.

9. (blocklove2025automaticallyimprovingllmbased pages 3-5): Jason Blocklove, Shailja Thakur, Benjamin Tan, Hammond Pearce, Siddharth Garg, and Ramesh Karri. Automatically improving llm-based verilog generation using eda tool feedback. Mar 2025. URL: https://doi.org/10.1145/3723876, doi:10.1145/3723876. This article has 21 citations and is from a peer-reviewed journal.

10. (ravindran2025surveyandbenchmarking pages 5-7): Arun Ravindran, Aditya Patra, Vahid Babaey, and Suresh Purini. Survey and benchmarking of large language models for rtl code generation: techniques and open challenges. Unknown journal, Sep 2025. URL: https://doi.org/10.20944/preprints202509.1681.v1, doi:10.20944/preprints202509.1681.v1.

11. (zhao2025mageamultiagent pages 4-5): Yujie Zhao, Hejia Zhang, Hanxian Huang, Zhongming Yu, and Jishen Zhao. Mage: a multi-agent engine for automated rtl code generation. ArXiv, Dec 2025. URL: https://doi.org/10.48550/arxiv.2412.07822, doi:10.48550/arxiv.2412.07822. This article has 80 citations.

12. (tsai2024rtlfixerautomaticallyfixing pages 1-2): Yun-Da Tsai, Mingjie Liu, and Haoxing Ren. Rtlfixer: automatically fixing rtl syntax errors with large language model. Proceedings of the 61st ACM/IEEE Design Automation Conference, pages 1-6, Jun 2024. URL: https://doi.org/10.1145/3649329.3657353, doi:10.1145/3649329.3657353. This article has 229 citations.

13. (tsai2024rtlfixerautomaticallyfixing pages 1-1): Yun-Da Tsai, Mingjie Liu, and Haoxing Ren. Rtlfixer: automatically fixing rtl syntax errors with large language model. Proceedings of the 61st ACM/IEEE Design Automation Conference, pages 1-6, Jun 2024. URL: https://doi.org/10.1145/3649329.3657353, doi:10.1145/3649329.3657353. This article has 229 citations.

14. (tsai2024rtlfixerautomaticallyfixing pages 5-5): Yun-Da Tsai, Mingjie Liu, and Haoxing Ren. Rtlfixer: automatically fixing rtl syntax errors with large language model. Proceedings of the 61st ACM/IEEE Design Automation Conference, pages 1-6, Jun 2024. URL: https://doi.org/10.1145/3649329.3657353, doi:10.1145/3649329.3657353. This article has 229 citations.

15. (jha2025largelanguagemodels pages 6-7): C. Jha, Muhammad Hassan, Khushboo Qayyum, Sallar Ahmadi-Pour, Kangwei Xu, Ruidi Qiu, Jason Blocklove, Luca Collini, Andre Nakkab, Ulf Schlichtmann, Grace Li Zhang, Ramesh Karri, Bing Li, Siddharth Garg, and Rolf Drechsler. Large language models (llms) for verification, testing, and design. 2025 IEEE European Test Symposium (ETS), pages 1-10, May 2025. URL: https://doi.org/10.1109/ets63895.2025.11049311, doi:10.1109/ets63895.2025.11049311. This article has 13 citations.

16. (thakur2024verigenalarge pages 19-22): Shailja Thakur, Baleegh Ahmad, Hammond Pearce, Benjamin Tan, Brendan Dolan-Gavitt, Ramesh Karri, and Siddharth Garg. Verigen: a large language model for verilog code generation. Apr 2024. URL: https://doi.org/10.1145/3643681, doi:10.1145/3643681. This article has 598 citations and is from a peer-reviewed journal.

17. (lai2025analogcoderanalogcircuit pages 1-2): Yao Lai, Sungyoung Lee, Guojin Chen, Souradip Poddar, Mengkang Hu, David Z. Pan, and Ping Luo. Analogcoder: analog circuit design via training-free code generation. ArXiv, May 2025. URL: https://doi.org/10.48550/arxiv.2405.14918, doi:10.48550/arxiv.2405.14918. This article has 142 citations.

18. (lai2025analogcoderanalogcircuit pages 2-4): Yao Lai, Sungyoung Lee, Guojin Chen, Souradip Poddar, Mengkang Hu, David Z. Pan, and Ping Luo. Analogcoder: analog circuit design via training-free code generation. ArXiv, May 2025. URL: https://doi.org/10.48550/arxiv.2405.14918, doi:10.48550/arxiv.2405.14918. This article has 142 citations.

19. (lai2025analogcoderanalogcircuit pages 7-8): Yao Lai, Sungyoung Lee, Guojin Chen, Souradip Poddar, Mengkang Hu, David Z. Pan, and Ping Luo. Analogcoder: analog circuit design via training-free code generation. ArXiv, May 2025. URL: https://doi.org/10.48550/arxiv.2405.14918, doi:10.48550/arxiv.2405.14918. This article has 142 citations.

20. (lai2025analogcoderanalogcircuit pages 9-11): Yao Lai, Sungyoung Lee, Guojin Chen, Souradip Poddar, Mengkang Hu, David Z. Pan, and Ping Luo. Analogcoder: analog circuit design via training-free code generation. ArXiv, May 2025. URL: https://doi.org/10.48550/arxiv.2405.14918, doi:10.48550/arxiv.2405.14918. This article has 142 citations.

21. (chang2024lamagiclanguagemodelbasedtopology pages 9-10): Chen-Chia Chang, Yikang Shen, Shaoze Fan, Jing Li, Shun Zhang, Ningyuan Cao, Yiran Chen, and Xin Zhang. Lamagic: language-model-based topology generation for analog integrated circuits. ArXiv, Jul 2024. URL: https://doi.org/10.48550/arxiv.2407.18269, doi:10.48550/arxiv.2407.18269. This article has 70 citations.

22. (chang2024lamagiclanguagemodelbasedtopology pages 1-2): Chen-Chia Chang, Yikang Shen, Shaoze Fan, Jing Li, Shun Zhang, Ningyuan Cao, Yiran Chen, and Xin Zhang. Lamagic: language-model-based topology generation for analog integrated circuits. ArXiv, Jul 2024. URL: https://doi.org/10.48550/arxiv.2407.18269, doi:10.48550/arxiv.2407.18269. This article has 70 citations.

23. (chang2024lamagiclanguagemodelbasedtopology pages 2-3): Chen-Chia Chang, Yikang Shen, Shaoze Fan, Jing Li, Shun Zhang, Ningyuan Cao, Yiran Chen, and Xin Zhang. Lamagic: language-model-based topology generation for analog integrated circuits. ArXiv, Jul 2024. URL: https://doi.org/10.48550/arxiv.2407.18269, doi:10.48550/arxiv.2407.18269. This article has 70 citations.

24. (chang2024lamagiclanguagemodelbasedtopology pages 6-8): Chen-Chia Chang, Yikang Shen, Shaoze Fan, Jing Li, Shun Zhang, Ningyuan Cao, Yiran Chen, and Xin Zhang. Lamagic: language-model-based topology generation for analog integrated circuits. ArXiv, Jul 2024. URL: https://doi.org/10.48550/arxiv.2407.18269, doi:10.48550/arxiv.2407.18269. This article has 70 citations.

25. (fu2023gpt4aigchiptowardsnextgeneration pages 3-4): Yonggan Fu, Yongan Zhang, Zhongzhi Yu, Sixu Li, Zhifan Ye, Chaojian Li, Cheng Wan, and Yingyan Lin. Gpt4aigchip: towards next-generation ai accelerator design automation via large language models. 2023 IEEE/ACM International Conference on Computer Aided Design (ICCAD), pages 1-9, Sep 2023. URL: https://doi.org/10.48550/arxiv.2309.10730, doi:10.48550/arxiv.2309.10730. This article has 185 citations.

26. (fu2023gpt4aigchiptowardsnextgeneration pages 1-1): Yonggan Fu, Yongan Zhang, Zhongzhi Yu, Sixu Li, Zhifan Ye, Chaojian Li, Cheng Wan, and Yingyan Lin. Gpt4aigchip: towards next-generation ai accelerator design automation via large language models. 2023 IEEE/ACM International Conference on Computer Aided Design (ICCAD), pages 1-9, Sep 2023. URL: https://doi.org/10.48550/arxiv.2309.10730, doi:10.48550/arxiv.2309.10730. This article has 185 citations.

27. (fu2023gpt4aigchiptowardsnextgeneration pages 2-3): Yonggan Fu, Yongan Zhang, Zhongzhi Yu, Sixu Li, Zhifan Ye, Chaojian Li, Cheng Wan, and Yingyan Lin. Gpt4aigchip: towards next-generation ai accelerator design automation via large language models. 2023 IEEE/ACM International Conference on Computer Aided Design (ICCAD), pages 1-9, Sep 2023. URL: https://doi.org/10.48550/arxiv.2309.10730, doi:10.48550/arxiv.2309.10730. This article has 185 citations.

28. (fu2023gpt4aigchiptowardsnextgeneration pages 7-8): Yonggan Fu, Yongan Zhang, Zhongzhi Yu, Sixu Li, Zhifan Ye, Chaojian Li, Cheng Wan, and Yingyan Lin. Gpt4aigchip: towards next-generation ai accelerator design automation via large language models. 2023 IEEE/ACM International Conference on Computer Aided Design (ICCAD), pages 1-9, Sep 2023. URL: https://doi.org/10.48550/arxiv.2309.10730, doi:10.48550/arxiv.2309.10730. This article has 185 citations.

29. (chang2023chipgpthowfar pages 3-4): Kaiyan Chang, Ying Wang, Haimeng Ren, Mengdi Wang, Shengwen Liang, Yinhe Han, Huawei Li, and Xiaowei Li. Chipgpt: how far are we from natural language hardware design. ArXiv, May 2023. URL: https://doi.org/10.48550/arxiv.2305.14019, doi:10.48550/arxiv.2305.14019. This article has 216 citations.

30. (liu2023chipnemodomainadaptedllms pages 4-5): Mingjie Liu, Teodor-Dumitru Ene, Robert Kirby, Chris Cheng, Nathaniel Pinckney, Rongjian Liang, Jonah Alben, Himyanshu Anand, Sanmitra Banerjee, Ismet Bayraktaroglu, Bonita Bhaskaran, Bryan Catanzaro, Arjun Chaudhuri, Sharon Clay, Bill Dally, Laura Dang, Parikshit Deshpande, Siddhanth Dhodhi, Sameer Halepete, Eric Hill, Jiashang Hu, Sumit Jain, Ankit Jindal, Brucek Khailany, George Kokai, Kishor Kunal, Xiaowei Li, Charley Lind, Hao Liu, Stuart Oberman, Sujeet Omar, Ghasem Pasandi, Sreedhar Pratty, Jonathan Raiman, Ambar Sarkar, Zhengjiang Shao, Hanfei Sun, Pratik P Suthar, Varun Tej, Walker Turner, Kaizhe Xu, and Haoxing Ren. Chipnemo: domain-adapted llms for chip design. ArXiv, Oct 2023. URL: https://doi.org/10.48550/arxiv.2311.00176, doi:10.48550/arxiv.2311.00176. This article has 342 citations.

31. (lai2025analogcoderanalogcircuit pages 8-9): Yao Lai, Sungyoung Lee, Guojin Chen, Souradip Poddar, Mengkang Hu, David Z. Pan, and Ping Luo. Analogcoder: analog circuit design via training-free code generation. ArXiv, May 2025. URL: https://doi.org/10.48550/arxiv.2405.14918, doi:10.48550/arxiv.2405.14918. This article has 142 citations.

32. (chang2025lamagic2advancedcircuit pages 1-2): Chen-Chia Chang, Wan-Hsuan Lin, Yikang Shen, Yiran Chen, and Xin Zhang. Lamagic2: advanced circuit formulations for language model-based analog topology generation. ArXiv, Jun 2025. URL: https://doi.org/10.48550/arxiv.2506.10235, doi:10.48550/arxiv.2506.10235. This article has 5 citations.

33. (fu2023gpt4aigchiptowardsnextgeneration pages 8-9): Yonggan Fu, Yongan Zhang, Zhongzhi Yu, Sixu Li, Zhifan Ye, Chaojian Li, Cheng Wan, and Yingyan Lin. Gpt4aigchip: towards next-generation ai accelerator design automation via large language models. 2023 IEEE/ACM International Conference on Computer Aided Design (ICCAD), pages 1-9, Sep 2023. URL: https://doi.org/10.48550/arxiv.2309.10730, doi:10.48550/arxiv.2309.10730. This article has 185 citations.

34. (firouzi2025chipmndllmsfor pages 3-4): Farshad Firouzi, David Z. Pan, Jiaqi Gu, Bahar Farahani, Jayeeta Chaudhuri, Ziang Yin, Pingchuan Ma, Peter Domanski, and Krishnendu Chakrabarty. Chipmnd: llms for agile chip design. 2025 IEEE 43rd VLSI Test Symposium (VTS), pages 1-10, Apr 2025. URL: https://doi.org/10.1109/vts65138.2025.11022936, doi:10.1109/vts65138.2025.11022936. This article has 11 citations.

35. (teng2025verirlboostingthe pages 6-7): Fu Teng, Miao Pan, Xuhong Zhang, Zhezhi He, Yiyao Yang, Xinyi Chai, Mengnan Qi, Liqiang Lu, and Jianwei Yin. Verirl: boosting the llm-based verilog code generation via reinforcement learning. In 2025 IEEE/ACM International Conference On Computer Aided Design (ICCAD), 1-9. IEEE, Oct 2025. URL: https://doi.org/10.1109/iccad66269.2025.11241003, doi:10.1109/iccad66269.2025.11241003. This article has 4 citations.

36. (sheth2506protocolllmrtlbenchmark pages 1-2): Arnav Sheth, Ivaxi Sheth, and Mario Fritz. Protocolllm: rtl benchmark for systemverilog generation of communication protocols. ArXiv, Jun 2506. URL: https://doi.org/10.48550/arxiv.2506.07945, doi:10.48550/arxiv.2506.07945. This article has 2 citations.

37. (lai2025analogcoderanalogcircuit pages 26-28): Yao Lai, Sungyoung Lee, Guojin Chen, Souradip Poddar, Mengkang Hu, David Z. Pan, and Ping Luo. Analogcoder: analog circuit design via training-free code generation. ArXiv, May 2025. URL: https://doi.org/10.48550/arxiv.2405.14918, doi:10.48550/arxiv.2405.14918. This article has 142 citations.

38. (sandal2401zeroshotrtlcode pages 3-4): Selim Sandal and Ismail Akturk. Zero-shot rtl code generation with attention sink augmented large language models. ArXiv, Jan 2401. URL: https://doi.org/10.48550/arxiv.2401.08683, doi:10.48550/arxiv.2401.08683. This article has 9 citations.

39. (ravindran2025surveyandbenchmarking pages 13-15): Arun Ravindran, Aditya Patra, Vahid Babaey, and Suresh Purini. Survey and benchmarking of large language models for rtl code generation: techniques and open challenges. Unknown journal, Sep 2025. URL: https://doi.org/10.20944/preprints202509.1681.v1, doi:10.20944/preprints202509.1681.v1.

40. (ravindran2025surveyandbenchmarking pages 15-16): Arun Ravindran, Aditya Patra, Vahid Babaey, and Suresh Purini. Survey and benchmarking of large language models for rtl code generation: techniques and open challenges. Unknown journal, Sep 2025. URL: https://doi.org/10.20944/preprints202509.1681.v1, doi:10.20944/preprints202509.1681.v1.

41. (sheth2506protocolllmrtlbenchmark pages 5-6): Arnav Sheth, Ivaxi Sheth, and Mario Fritz. Protocolllm: rtl benchmark for systemverilog generation of communication protocols. ArXiv, Jun 2506. URL: https://doi.org/10.48550/arxiv.2506.07945, doi:10.48550/arxiv.2506.07945. This article has 2 citations.

42. (abdollahi2024hardwaredesignand pages 47-48): Meisam Abdollahi, Seyedeh Faegheh Yeganli, Mohammad (Amir) Baharloo, and Amirali Baniasadi. Hardware design and verification with large language models: a scoping review, challenges, and open issues. Electronics, 14:120, Dec 2024. URL: https://doi.org/10.3390/electronics14010120, doi:10.3390/electronics14010120. This article has 103 citations.

43. (abdollahi2024hardwaredesignand pages 38-39): Meisam Abdollahi, Seyedeh Faegheh Yeganli, Mohammad (Amir) Baharloo, and Amirali Baniasadi. Hardware design and verification with large language models: a scoping review, challenges, and open issues. Electronics, 14:120, Dec 2024. URL: https://doi.org/10.3390/electronics14010120, doi:10.3390/electronics14010120. This article has 103 citations.

44. (abdollahi2024hardwaredesignanda pages 39-41): Meisam Abdollahi, S. Faegheh Yeganli, Mohammad (Amir) Baharloo, and Amirali Baniasadi. Hardware design and verification with large language models: a literature survey, challenges, and open issues. Unknown journal, Nov 2024. URL: https://doi.org/10.20944/preprints202411.0156.v1, doi:10.20944/preprints202411.0156.v1.