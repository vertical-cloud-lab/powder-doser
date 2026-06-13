Question: Find recent (2018-2025) peer-reviewed and arXiv academic publications on machine-learning, reinforcement-learning, and optimization-based methods for PCB and chip physical design — specifically component placement and routing. Cover: (a) deep-RL and learning-based macro/component placement (e.g., Google Nature 2021 chip placement and its critiques/reproductions such as Cheng et al. 'The False Dawn' and Stronger Baselines), (b) analog and PCB placement automation, (c) learning-based and classical autorouting / detailed routing for PCBs (DeepPCB and related), (d) DRC-aware and manufacturability-aware placement/routing, and (e) benchmarks and metrics used to evaluate them. For each paper give: full citation, 3-5 sentence summary, and relevance to automatically generating manufacturable PCBs for low-cost open-hardware motor / sensor control boards. Highlight reported quantitative results (wirelength, congestion, DRC violations, runtime) and known limitations. Aim for ~10-15 references.

# Machine-Learning, Reinforcement-Learning, and Optimization-Based Methods for PCB and Chip Physical Design: A Literature Review (2018–2025)

## 1. Introduction

This review surveys recent academic publications on machine-learning (ML), reinforcement-learning (RL), and optimization-based approaches to automated physical design of printed circuit boards (PCBs) and integrated circuits (ICs), with emphasis on component placement, routing, design-rule compliance, and their relevance to automatically generating manufacturable PCBs for low-cost open-hardware motor/sensor control boards. The following summary table provides a consolidated overview of the 14 key references reviewed, followed by detailed per-paper summaries organized by topic.

| Reference | Category | Method Type | Key Quantitative Results | Known Limitations |
|---|---|---|---|---|
| Mirhoseini et al., *Nature* 2021 | Chip Placement | Deep RL / graph policy | Reported as achieving placements comparable or superior to human floorplans in under 6 hours; widely cited as the first high-profile end-to-end RL chip macro placement result, but exact quantitative values were not available in the retrieved evidence here. Later assessments indicate its proxy objective emphasized wirelength, density, and congestion rather than full post-route manufacturability. | Reproducibility controversy; code/data initially incomplete; later critiques questioned dependence on pretraining, convergence, proxy-vs-final-PPA mismatch, and compute requirements (cheng2025anupdatedassessment pages 1-2, cheng2025anupdatedassessment pages 2-3) |
| Cheng et al., ISPD 2023 | Chip Placement / Benchmarking | Reproduction + stronger baselines (SA, RePlAce, CMP) | CT training runtimes: 32.31 h (Ariane-NG45), 50.51 h (BlackParrot-NG45), 81.23 h (MemPool-NG45). CMP/RePlAce ran in minutes to a few hours; SA beat CT on proxy cost in all ICCAD04 cases and on HPWL in 16/17 cases; on modern benchmarks SA beat CT on proxy cost in 4/5 and on routed wirelength in 5/6 cases. RePlAce won 3/6 routed-wirelength comparisons and 2/6 total-power comparisons in head-to-heads. Ariane final CT proxy example: WL 0.0913, density 0.5290, congestion 0.9017 (cheng2023assessmentofreinforcement pages 10-11, cheng2023assessmentofreinforcement pages 9-10) | CT consumed far more compute than classical baselines; benefits depend on pretraining and initial placements; proxy-cost wins did not consistently translate to routed QoR wins (cheng2023assessmentofreinforcement pages 10-11, cheng2023assessmentofreinforcement pages 9-10) |
| Cheng et al., *IEEE TCAD* 2025 | Chip Placement / Critique | Updated assessment; SA+RL comparison | Improved SA baseline achieved up to 26% better proxy cost within the same runtime while using one-quarter of the resources versus prior SA. On CT-Ariane-X4 (532 macros, TSMC 7nm), SA beat AlphaChip in both post-detailed-placement HPWL and CT proxy cost. Pretrained CT showed a large return jump by ~50 h but only ~4% improvement over the next 125 h (cheng2025anupdatedassessment pages 2-3, cheng2025anupdatedassessment pages 12-13) | Weak correlation between CT proxy and final post-route PPA; instability and dataset-diversity sensitivity in pretraining; no independent full reproduction of original Nature-level claims noted in the evidence (cheng2025anupdatedassessment pages 12-13) |
| Lai et al., ChiPFormer 2023 | Chip Placement | Offline RL / decision transformer | Claimed 10× runtime reduction and strong transfer to unseen circuits in the abstract. On ICCAD04 mixed-size placement, example HPWLs included ibm01 16.70×10^7, ibm10 230.39×10^7, ibm18 370.36×10^7, with tabled relative improvements such as -26.82%, -16.00%, and -7.14%; overlap was often 0.00% on many macro-placement cases. Evaluated on two RTX3090 GPUs (lai2023chipformertransferablechip pages 15-17, lai2023chipformertransferablechip pages 18-20) | Runtime curves shown, but explicit wall-clock numbers were not in retrieved evidence. As an offline-learning method, quality depends on offline data and subsequent finetuning; still relies on downstream legalizers/placers for full flow closure (lai2023chipformertransferablechip pages 15-17, lai2023chipformertransferablechip pages 18-20) |
| Cheng & Yan, DeepPlace / DeepPR 2021 | Chip Placement + Routing | Deep RL + GNN/CNN + DREAMPlace | DeepPlace beat sequential RL and often DREAMPlace on total wirelength: e.g., adaptec1 80,117,232 vs 86,675,688 (sequential) vs 83,749,616 (DREAMPlace); bigblue4 951,984,128 vs 1,039,976,064. DeepPR also improved final routed wirelength over a separate placement-then-routing pipeline; example benchmark pairs included 5298 vs 6077 and 63,560 vs 79,573. Reported ~4× total-runtime speedup over RePlAce (cheng2021onjointlearning pages 7-9, cheng2021onjointlearning pages 9-12) | Moderate macro-count scalability only; overfitting after too much pretraining; macro size/shape and richer human constraints not fully modeled; DREAMPlace baseline sometimes failed congestion checks due to macro overlap assumptions (cheng2021onjointlearning pages 7-9, cheng2021onjointlearning pages 9-12) |
| Lin et al., DREAMPlace 2.0 2020 | Chip Placement | GPU-accelerated analytical placement | Matched RePlAce wirelength closely while cutting runtime: adaptec1 total runtime 84 s vs 118 s for RePlAce in CPU comparison; overall 1.3× speedup over RePlAce on 40 CPU threads and ~14× speedup with GPU. Nesterov optimizer delivered similar quality to Adam but ~2× faster in GP; SGD with momentum was ~1.2% worse in wirelength (lin2020dreamplace2.0opensource pages 3-4, lin2020dreamplace2.0opensource pages 2-3) | Primarily wirelength-oriented analytical placement, not a full manufacturability-aware PCB solution by itself; routability/DRC must be handled by downstream stages or extensions (lin2020dreamplace2.0opensource pages 3-4, lin2020dreamplace2.0opensource pages 2-3) |
| Liu et al., DATE 2021 | DRC-/Routability-Aware Placement | Deep-learning congestion predictor integrated into placer | On modified ISPD2015, achieved up to 9.05% congestion-rate reduction and 5.30% routed-wirelength reduction versus DREAMPlace; one statement reports 18.68% congestion reduction versus NTUplace4dr. Runtime was ~4× slower than DREAMPlace but ~23× faster than NTUplace4dr; gradient computation for congestion penalty consumed 46.10% of runtime (liu2021globalplacementwith pages 4-4) | Not a full PCB-specific method; adds runtime overhead versus plain DREAMPlace; some components of the routability term are non-differentiable/discretized (liu2021globalplacementwith pages 4-4) |
| Oh et al., 2022 | Chip Placement | Bayesian optimization | Proposed Bayesian optimization over sequence pairs for fixed-outline macro placement and argued better sample efficiency than RL for expensive objectives. The retrieved evidence confirms competitive performance claims but did not provide usable numeric HPWL/runtime tables. | Evidence retrieved here lacked benchmark numbers; practical scalability for very large mixed-size industrial blocks remains less documented in the available excerpts (lai2023chipformertransferablechip pages 18-20) |
| Crocker, 2021 | PCB Placement | Deep RL with physical constraints | Demonstrated physically valid PCB ring placements after 2 million episodes using a 10×10×2 action space and 5-layer TCNN policy. In example outputs, the agent successfully generated manufacturable 8- and 12-component ring boards with no overlap or edge overhangs and complete routability for the restricted ring domain (crocker2021physicallyconstrainedpcb pages 41-49) | Proof-of-concept only for restricted ring placements; encoder trained up to 10 components degraded beyond ~12 components; true-routing reward is computationally prohibitive in general PCB placement; learned rewards showed reward hacking (crocker2021physicallyconstrainedpcb pages 41-49) |
| Murphy, 2020 | PCB Placement | NN fitness / routability predictor | Built a dataset of >75,000 placed PCB designs from six boards and showed neural predictors beat HPWL/crossing heuristics for routability estimation. Multi-board absolute-routability model reached MAE 0.0182 overall; per-board MAEs included 0.0112, 0.0235, 0.0130, 0.0318, 0.0118. For a novel board, MAE was initially 0.2205 but fine-tuning with 25–50 examples reduced it to ~0.0128/0.0123 (murphy2020neuralnetworkfitness pages 36-40, murphy2020neuralnetworkfitness pages 1-5, murphy2020neuralnetworkfitness pages 40-48) | Relative ranking on novel boards improved less than absolute calibration; only six boards in the dataset; still a surrogate fitness, not a full placer/router or guaranteed DRC-clean flow (murphy2020neuralnetworkfitness pages 36-40, murphy2020neuralnetworkfitness pages 40-48, murphy2020neuralnetworkfitness pages 16-20) |
| Li et al., FanoutNet 2023 | PCB Routing / Fanout | Deep RL (PPO) + multi-constraint router | Achieved 100% routability on all listed open-source and industrial PCB cases. Open-source averages: 25 vias, 1,160 mm wirelength, 50 s runtime; industrial averages: 270 vias, WL 433 (table units), 245 min runtime. The paper states average wirelength improved by 6.8% over prior methods and inference ran in seconds after training (li2023fanoutnetaneuralized pages 7-8, li2023fanoutnetaneuralized pages 6-7, li2023fanoutnetaneuralized pages 1-2) | Focuses on fanout/pre-routing, not full end-to-end PCB autorouting; training cost is substantial; some cases increased via count or WL relative to one baseline despite better final routability (li2023fanoutnetaneuralized pages 4-6, li2023fanoutnetaneuralized pages 6-7) |
| Liao et al., JMD 2020 | Routing (PCB/IC global routing) | Deep RL / DQN | On 40 test routing problems, DQN achieved lower wirelength than A* in 80% (γ=1), 90% (γ=0.95), 97.5% (γ=0.9), and 95% (γ=0.8) of cases; with γ=0.9, all 40 problems had non-negative WL improvement over A*. DQN solutions had zero overflow in all cases, while A* occasionally had positive overflow; A*-based burn-in memory improved results, boosting better-than-A* cases from 57.5% to 80% (liao2020adeepreinforcement pages 9-11, liao2020adeepreinforcement pages 11-13) | Mostly tested on generated grid-routing problems rather than full manufacturable PCB boards; sequential two-pin formulation limits direct extension to richer multi-pin industrial routing; scaling and dataset availability remain open issues (liao2020adeepreinforcement pages 11-13) |
| Huang et al., Ranking Cost 2021 | Routing | Evolution-based optimization + learned ranking/cost maps | On 64×64 maps with obstacles, success rate improved to 0.32 with average length 358.5 versus Seq A*(200) at 0.26 and 367.5; on 16×16 and 32×32 maps, Ranking Cost often reached 1.0 success. Runtime was 38.3 s/map versus 41.5 s/map for Seq A*(200) and 0.8 s/map for Seq A*(5), trading more search for better solutions (huang2021rankingcostbuilding pages 7-9) | Grid-map benchmark abstraction, not direct fab-ready PCB routing; per-task learning adds overhead; more evidence needed on real PCB DRC/manufacturability constraints (huang2021rankingcostbuilding pages 7-9) |
| Merrill, 2021 | PCB Placement + Routing | Classical optimization (SA placer + A* rip-up/reroute) | Implemented a simulated-annealing placer with HPWL, congestion, and overlap terms plus a grid-based A* iterative rip-up-and-reroute router run for 20 iterations. Reported qualitative implementation facts include ~4× speedup when using laser vias over through-hole vias in routing experiments (merrill2021hungryforfully pages 85-89) | Prioritized completion over strict DRC-clean routing; evidence retrieved did not include systematic wirelength/routability benchmark tables; more of a prototype flow than a peer-reviewed industrial-grade PCB CAD benchmark paper (merrill2021hungryforfully pages 85-89) |


*Table: This table summarizes 14 key papers on ML, RL, and optimization methods for chip and PCB physical design, emphasizing quantitative results, method type, and practical limitations. It is useful for quickly comparing which approaches are most relevant to manufacturable PCB generation versus chip-oriented placement research.*

---

## 2. Deep-RL and Learning-Based Macro/Component Placement

### 2.1 Mirhoseini et al., "A Graph Placement Methodology for Fast Chip Design," *Nature*, 2021

**Citation:** A. Mirhoseini, A. Goldie, M. Yazgan, et al., "A graph placement methodology for fast chip design," *Nature*, vol. 594, pp. 207–212, Jun. 2021. doi:10.1038/s41586-021-03544-w.

**Summary:** This landmark paper introduced a deep RL approach using a graph neural network (GNN) policy to sequentially place chip macros on a gridded canvas, optimizing a proxy cost combining wirelength, density, and congestion. The method was reported to generate chip floorplans comparable or superior to those of human experts in under six hours. Standard cells were subsequently placed using a force-directed method. The work demonstrated transfer learning across chip blocks, with pre-training accelerating convergence on new designs. It catalyzed extensive follow-up research and debate.

**Relevance to open-hardware PCBs:** The sequential placement paradigm and GNN-based netlist encoding are directly transferable to PCB component placement, though PCBs involve mixed through-hole/SMD components, multi-layer routing constraints, and different scale considerations. The proxy-cost formulation (wirelength + density + congestion) provides a template for PCB-specific reward shaping. However, subsequent independent assessments have raised significant concerns about reproducibility, compute cost, and the gap between proxy and final post-route quality (cheng2025anupdatedassessment pages 1-2, cheng2025anupdatedassessment pages 2-3).

### 2.2 Cheng et al., "Assessment of Reinforcement Learning for Macro Placement," ISPD 2023

**Citation:** C.-K. Cheng, A. B. Kahng, S. Kundu, Y. Wang, and Z. Wang, "Assessment of reinforcement learning for macro placement," in *Proc. Int. Symp. Physical Design (ISPD)*, pp. 158–166, Mar. 2023. doi:10.1145/3569052.3578926.

**Summary:** This paper provides an open, transparent reimplementation and evaluation of Google's Circuit Training (CT). The authors benchmarked CT against simulated annealing (SA), RePlAce, commercial CMP, and AutoDMP on both ICCAD04 and modern NG45 testcases. CT training required 32–81 hours on eight NVIDIA V100 GPUs, whereas CMP and RePlAce completed in minutes to hours. SA outperformed CT on proxy cost in all ICCAD04 cases and on HPWL in 16 of 17 ICCAD04 cases; on modern benchmarks SA beat CT on routed wirelength in 5 of 6 cases (cheng2023assessmentofreinforcement pages 10-11, cheng2023assessmentofreinforcement pages 9-10). All evaluation flows and scripts were released publicly via the MacroPlacement GitHub repository.

**Relevance:** The public benchmarks and evaluation methodology established here could be adapted for PCB placement assessment. The finding that classical SA baselines often beat RL with far less compute is particularly relevant for resource-constrained open-hardware projects.

### 2.3 Cheng et al., "An Updated Assessment of Reinforcement Learning for Macro Placement," *IEEE TCAD*, 2025

**Citation:** C.-K. Cheng, A. B. Kahng, S. Kundu, Y. Wang, and Z. Wang, "An updated assessment of reinforcement learning for macro placement," *IEEE Trans. CAD*, pp. 1–1, Jan. 2025. doi:10.1109/tcad.2025.3644293.

**Summary:** This extended assessment tests the latest "AlphaChip" checkpoint released by Google, alongside the authors' strengthened SA baseline (multi-threaded, "go-with-the-winners" metaheuristic). The improved SA achieved up to 26% better proxy cost within the same runtime while using one-quarter of the resources. On CT-Ariane-X4 (532 macros, TSMC 7nm), SA outperformed AlphaChip in both post-detailed-placement HPWL and CT proxy cost. Pre-training showed diminishing returns after an initial jump at ~50 hours, with only ~4% further improvement over the next 125 hours. Critically, the authors found weak correlation between CT's proxy objective and final post-route PPA metrics (cheng2025anupdatedassessment pages 12-13, cheng2025anupdatedassessment pages 2-3).

**Relevance:** The proxy-vs-PPA gap is a cautionary finding for PCB design, where final manufacturability (DRC compliance, impedance matching, thermal behavior) matters more than any single proxy. The observation that strengthened classical methods remain competitive suggests that for modest-complexity PCBs (motor/sensor control boards), well-tuned SA may suffice.

### 2.4 Lai et al., "ChiPFormer: Transferable Chip Placement via Offline Decision Transformer," arXiv 2023

**Citation:** Y. Lai, J. Liu, Z. Tang, B. Wang, J. Hao, and P. Luo, "ChiPFormer: Transferable chip placement via offline decision transformer," *arXiv:2306.14744*, Jun. 2023. doi:10.48550/arxiv.2306.14744.

**Summary:** ChiPFormer casts chip placement as an offline RL problem and uses a decision transformer trained on fixed offline placement data to learn transferable policies across chip circuits. The method claims 10× runtime reduction compared to online RL approaches and demonstrated HPWL improvements of up to 26.82% on ICCAD04 benchmarks (e.g., ibm01: 16.70×10^7). It achieves near-zero overlap on many macro placement cases and supports efficient fine-tuning for unseen circuits in minutes rather than hours (lai2023chipformertransferablechip pages 15-17, lai2023chipformertransferablechip pages 18-20).

**Relevance:** The offline learning and fast fine-tuning paradigm is attractive for PCB design, where generating training data from existing board designs is feasible. Transfer across board families (e.g., multiple motor controller variants) could amortize training cost.

### 2.5 Cheng & Yan, "On Joint Learning for Solving Placement and Routing in Chip Design," arXiv 2021

**Citation:** R. Cheng and J. Yan, "On joint learning for solving placement and routing in chip design," *arXiv:2111.00234*, Jan. 2021. doi:10.48550/arxiv.2111.00234.

**Summary:** DeepPlace/DeepPR uses PPO-based RL with GCN and CNN embeddings to jointly optimize macro placement and routing. On ISPD-2005 benchmarks, DeepPlace achieved lower wirelengths than a sequential RL placer (e.g., adaptec1: 80.1M vs. 86.7M) and often outperformed DREAMPlace (83.7M), with approximately 4× runtime speedup over RePlAce. The joint placement+routing variant (DeepPR) significantly improved final routed wirelength compared to a separate pipeline, and the authors demonstrated that HPWL is a poor proxy for routed wirelength (cheng2021onjointlearning pages 7-9, cheng2021onjointlearning pages 9-12).

**Relevance:** The joint optimization insight is critical for PCBs: placement quality cannot be evaluated solely by wirelength; the routing completion rate and signal integrity matter. However, the method was limited to moderate macro counts and did not handle real physical constraints.

---

## 3. GPU-Accelerated Analytical Placement

### 3.1 Lin et al., "DREAMPlace 2.0: Open-Source GPU-Accelerated Global and Detailed Placement," CSTIC 2020

**Citation:** Y. Lin, D. Z. Pan, H. Ren, and B. Khailany, "DREAMPlace 2.0: Open-source GPU-accelerated global and detailed placement for large-scale VLSI designs," in *Proc. CSTIC*, pp. 1–4, Jun. 2020. doi:10.1109/cstic49141.2020.9282573.

**Summary:** DREAMPlace reframes VLSI placement as a differentiable optimization problem solved using deep-learning toolkits (PyTorch) with GPU acceleration. It matched RePlAce's HPWL quality on ISPD 2005 benchmarks (e.g., adaptec1: 73.19 vs. 73.23 HPWL) while achieving approximately 14× speedup over RePlAce on 40 CPU threads when using GPU, and 1.3× speedup in CPU-only mode. The Nesterov optimizer was ~2× faster than Adam at equivalent quality (lin2020dreamplace2.0opensource pages 3-4, lin2020dreamplace2.0opensource pages 2-3).

**Relevance:** DREAMPlace's open-source, GPU-accelerated framework is the most directly adaptable platform for PCB placement research. Its differentiable formulation allows integration of custom objectives (thermal, EMC, DRC) as additional loss terms, making it a promising foundation for PCB placement automation in open-hardware projects.

---

## 4. DRC-Aware and Routability-Aware Placement

### 4.1 Liu et al., "Global Placement with Deep Learning-Enabled Explicit Routability Optimization," DATE 2021

**Citation:** S. Liu, Q. Sun, P. Liao, Y. Lin, and B. Yu, "Global placement with deep learning-enabled explicit routability optimization," in *Proc. DATE*, pp. 1821–1824, Feb. 2021. doi:10.23919/date51398.2021.9473959.

**Summary:** This work integrates a fully convolutional network congestion predictor into DREAMPlace to produce routability-aware placements. On modified ISPD2015 benchmarks, it achieved up to 9.05% reduction in congestion rate and 5.30% reduction in routed wirelength compared to DREAMPlace. Runtime was approximately 4× slower than base DREAMPlace but 23× faster than NTUplace4dr, with congestion gradient computation consuming 46.1% of total runtime (liu2021globalplacementwith pages 4-4).

**Relevance:** This approach directly addresses the gap between placement optimization and post-route DRC compliance. For PCB design, analogous congestion/DRC predictors could be trained on PCB routing data to shift DRC checking earlier in the design flow, reducing manual iteration cycles for motor/sensor control boards.

---

## 5. PCB-Specific Placement and Automation

### 5.1 Crocker, "Physically Constrained PCB Placement Using Deep Reinforcement Learning," 2021

**Citation:** P. Crocker, "Physically constrained PCB placement using deep reinforcement learning," Master's thesis, 2021.

**Summary:** This thesis adapts the Mirhoseini et al. RL paradigm to PCB component placement with physical validity constraints (no overlap, no edge overhang). Using a 10×10 grid discretization, 5-layer TCNN policy, and 2 million training episodes, the system successfully generated valid ring placements for 8- and 12-component boards with complete routability. The agent considered component rotation and maintained physical validity throughout placement. However, the approach was limited to ring topologies where true routing reward could be computed in real time (crocker2021physicallyconstrainedpcb pages 41-49).

**Limitations:** The encoder degraded beyond ~12 components; the 200-option action space (10×10 grid × 2 rotations) would scale to 160,000+ for realistic boards; learned reward models were vulnerable to reward hacking in out-of-distribution placements (crocker2021physicallyconstrainedpcb pages 41-49).

**Relevance:** This is one of the few works directly targeting physically verified PCB placements with RL. The ring-placement restriction is a realistic subset for certain sensor boards, but the scalability limitations must be overcome for general motor controller PCBs.

### 5.2 Murphy, "Neural Network Fitness Function for Optimization-Based Approaches to PCB Design Automation," 2020

**Citation:** J. R. Murphy, "Neural network fitness function for optimization-based approaches to PCB design automation," Master's thesis, 2020.

**Summary:** Murphy developed CNN-based routability predictors trained on a dataset of >75,000 placed PCB designs from six boards, using routability (routing completion rate) as the label. The multi-board model achieved MAE of 0.0182 for absolute routability prediction, with per-board MAEs ranging from 0.0112 to 0.0318. For a novel board, fine-tuning with just 25 examples reduced MAE from 0.2205 to ~0.0128. The study demonstrated that neural predictors substantially outperform traditional HPWL and crossing heuristics as placement fitness functions (murphy2020neuralnetworkfitness pages 36-40, murphy2020neuralnetworkfitness pages 1-5, murphy2020neuralnetworkfitness pages 40-48, murphy2020neuralnetworkfitness pages 16-20).

**Relevance:** This is directly applicable to PCB placement optimization for open-hardware boards. The fine-tuning approach with minimal data is practical for custom board families. The main gap is that relative ranking accuracy on novel boards improved less than absolute calibration, and the work was not integrated into a complete automated placement loop.

### 5.3 Merrill, "Hungry for Fully Automated Design of Embedded Systems?" 2021

**Citation:** D. J. Merrill, "Hungry for fully automated design of embedded systems?" Master's thesis, 2021.

**Summary:** This work implements a full automated PCB design pipeline using simulated annealing for placement (with HPWL, congestion, and overlap penalties) and grid-based A* iterative rip-up-and-reroute for routing (20 iterations). The framework is open-source and integrates with KiCad/EAGLE. Laser vias provided approximately 4× speedup over through-hole vias in routing. The SA placer transitioned objective weights from HPWL/congestion to overlap resolution during annealing (merrill2021hungryforfully pages 85-89).

**Relevance:** This is the most complete open-source end-to-end PCB automation system in the review and is directly applicable to low-cost open-hardware boards. However, it prioritizes layout-vs-schematic completion over strict DRC cleanliness, meaning post-processing may be needed for manufacturing.

---

## 6. Learning-Based and Classical Autorouting for PCBs

### 6.1 Li et al., "FanoutNet: A Neuralized PCB Fanout Automation Method Using Deep Reinforcement Learning," AAAI 2023

**Citation:** H. Li, J. Zhang, N. Xu, and M. Liu, "FanoutNet: A neuralized PCB fanout automation method using deep reinforcement learning," in *Proc. AAAI Conf. AI*, vol. 37, pp. 8554–8561, Jun. 2023. doi:10.1609/aaai.v37i7.26030.

**Summary:** FanoutNet is the first automated PCB fanout method, using PPO-trained policy and value networks with CNN + attention encoders, combined with a multi-constraint router (MCR) for verification. It achieved 100% routability on all tested open-source and industrial PCB cases, with average wirelength improved by 6.8% over prior methods. Open-source benchmarks: average 25 vias, 1,160 mm wirelength, 50 s runtime; industrial cases: average 270 vias, 245 min runtime. Inference after training was completed in seconds (li2023fanoutnetaneuralized pages 7-8, li2023fanoutnetaneuralized pages 6-7, li2023fanoutnetaneuralized pages 1-2).

**Relevance:** FanoutNet directly addresses a critical PCB routing bottleneck (BGA/QFP fanout) that appears in motor controller boards with microcontrollers. The 100% routability achievement is particularly valuable for ensuring manufacturability.

### 6.2 Liao et al., "A Deep Reinforcement Learning Approach for Global Routing," *J. Mech. Design*, 2020

**Citation:** H. Liao, W. Zhang, X. Dong, B. Poczos, K. Shimada, and L. B. Kara, "A deep reinforcement learning approach for global routing," *J. Mech. Design*, vol. 142, no. 6, Nov. 2020. doi:10.1115/1.4045044.

**Summary:** This work formulates global routing as a DQN-based RL problem, demonstrating superiority over sequential A* on parameterized grid routing problems. With optimized discount factor (γ = 0.9), the DQN router achieved lower wirelength than A* in 97.5% of 40 test problems, with zero overflow in all cases (versus occasional positive overflow for A*). The work also developed a parameterized routing problem generator for training data creation (liao2020adeepreinforcement pages 9-11, liao2020adeepreinforcement pages 11-13).

**Relevance:** The conjoint optimization mechanism (considering downstream nets when routing current nets) is valuable for PCB routing where net interactions are critical. The problem generator concept could be adapted to create PCB-specific training instances. The main limitation is that experiments used abstract grid worlds rather than real PCB geometries.

### 6.3 Huang et al., "Ranking Cost: Building An Efficient and Scalable Circuit Routing Planner with Evolution-Based Optimization," arXiv 2021

**Citation:** S. Huang, B. Wang, D. Li, J. Hao, T. Chen, and J. Zhu, "Ranking cost: Building an efficient and scalable circuit routing planner with evolution-based optimization," *arXiv:2110.03939*, Oct. 2021. doi:10.48550/arxiv.2110.03939.

**Summary:** Ranking Cost uses OpenAI-ES to jointly learn net routing order and cost maps for A*-based sequential routing. On 64×64 grid maps with obstacles (10 net pairs), it achieved 32% success rate with average length 358.5, versus 26% and 367.5 for Seq A*(200). On simpler maps (16×16, 4 pairs), Ranking Cost achieved 100% success versus 96% for exhaustively sampled A*. Runtime was 38.3 s/map, acceptable given the quality gains (huang2021rankingcostbuilding pages 7-9).

**Relevance:** The learned net-ordering strategy is directly applicable to PCB autorouting, where routing order significantly affects completion rate. The evolution-based approach avoids the sample-inefficiency issues of policy-gradient RL.

---

## 7. Benchmarks and Metrics

Across the reviewed literature, the following benchmarks and metrics are predominantly used:

- **ISPD 2005/2015/2019 benchmarks**: Standard for evaluating VLSI placement and routing quality (HPWL, congestion, routed wirelength, DRC violations) (lin2020dreamplace2.0opensource pages 3-4, liu2021globalplacementwith pages 4-4).
- **ICCAD 2004 benchmarks**: Commonly used for mixed-size placement evaluation (lai2023chipformertransferablechip pages 15-17, cheng2023assessmentofreinforcement pages 10-11).
- **MacroPlacement GitHub (Cheng et al.)**: Open testcases on modern process nodes (NG45, TSMC 7nm) with full evaluation scripts (cheng2025anupdatedassessment pages 1-2, cheng2025anupdatedassessment pages 2-3).
- **Industrial PCB benchmarks**: Used by FanoutNet (11 open-source + 5 industrial cases) and Murphy (6 boards) (li2023fanoutnetaneuralized pages 7-8, murphy2020neuralnetworkfitness pages 1-5).
- **Primary metrics**: Half-perimeter wirelength (HPWL), routed wirelength, congestion rate, routability/completion rate, DRC violation count, via count, and wall-clock runtime.

No widely adopted, standardized PCB placement/routing benchmark suite analogous to ISPD contests exists for PCBs, which remains a significant gap in the field.

---

## 8. Key Findings and Implications for Open-Hardware PCB Automation

**RL-based chip placement methods have shown promise but face practical barriers.** Google's Circuit Training approach, while influential, was shown by independent assessment to underperform strengthened SA baselines on most benchmarks while consuming orders of magnitude more compute (cheng2023assessmentofreinforcement pages 10-11, cheng2023assessmentofreinforcement pages 9-10, cheng2025anupdatedassessment pages 12-13). The proxy-cost objective used by CT correlates weakly with final post-route PPA, a critical concern for manufacturable PCB design (cheng2025anupdatedassessment pages 12-13).

**GPU-accelerated analytical placement (DREAMPlace) offers the most practical foundation.** With ~14× speedup and matching wirelength quality, DREAMPlace's open-source, differentiable framework is extensible to PCB-specific objectives (lin2020dreamplace2.0opensource pages 3-4).

**PCB-specific methods remain in early stages.** Crocker's RL-based PCB placement was limited to ~12-component ring topologies (crocker2021physicallyconstrainedpcb pages 41-49); Murphy's NN fitness predictor showed promising routability estimation but was not integrated into a full design loop (murphy2020neuralnetworkfitness pages 36-40); and Merrill's SA-based pipeline is the most complete open-source system but lacks DRC guarantees (merrill2021hungryforfully pages 85-89).

**FanoutNet represents a practical advance in PCB routing automation**, achieving 100% routability on industrial cases with 6.8% wirelength improvement (li2023fanoutnetaneuralized pages 1-2).

**For low-cost motor/sensor control boards** (typically 50–200 components, 2–4 layers), the most practical near-term approach would combine: (1) SA or DREAMPlace-derived placement with PCB-specific constraints, (2) Murphy-style NN routability prediction as a fitness function, (3) A*-based rip-up-and-reroute or FanoutNet-style RL fanout for routing, and (4) explicit DRC checking in the optimization loop rather than relying on proxy costs alone. The absence of standardized PCB benchmarks remains a critical gap that limits reproducible comparison of methods.

References

1. (cheng2025anupdatedassessment pages 1-2): Chung-Kuan Cheng, Andrew B. Kahng, Sayak Kundu, Yucheng Wang, and Zhiang Wang. An updated assessment of reinforcement learning for macro placement. IEEE Transactions on Computer-Aided Design of Integrated Circuits and Systems, pages 1-1, Jan 2025. URL: https://doi.org/10.1109/tcad.2025.3644293, doi:10.1109/tcad.2025.3644293. This article has 45 citations and is from a domain leading peer-reviewed journal.

2. (cheng2025anupdatedassessment pages 2-3): Chung-Kuan Cheng, Andrew B. Kahng, Sayak Kundu, Yucheng Wang, and Zhiang Wang. An updated assessment of reinforcement learning for macro placement. IEEE Transactions on Computer-Aided Design of Integrated Circuits and Systems, pages 1-1, Jan 2025. URL: https://doi.org/10.1109/tcad.2025.3644293, doi:10.1109/tcad.2025.3644293. This article has 45 citations and is from a domain leading peer-reviewed journal.

3. (cheng2023assessmentofreinforcement pages 10-11): Chung-Kuan Cheng, Andrew B. Kahng, Sayak Kundu, Yucheng Wang, and Zhiang Wang. Assessment of reinforcement learning for macro placement. Proceedings of the 2023 International Symposium on Physical Design, pages 158-166, Mar 2023. URL: https://doi.org/10.1145/3569052.3578926, doi:10.1145/3569052.3578926. This article has 70 citations.

4. (cheng2023assessmentofreinforcement pages 9-10): Chung-Kuan Cheng, Andrew B. Kahng, Sayak Kundu, Yucheng Wang, and Zhiang Wang. Assessment of reinforcement learning for macro placement. Proceedings of the 2023 International Symposium on Physical Design, pages 158-166, Mar 2023. URL: https://doi.org/10.1145/3569052.3578926, doi:10.1145/3569052.3578926. This article has 70 citations.

5. (cheng2025anupdatedassessment pages 12-13): Chung-Kuan Cheng, Andrew B. Kahng, Sayak Kundu, Yucheng Wang, and Zhiang Wang. An updated assessment of reinforcement learning for macro placement. IEEE Transactions on Computer-Aided Design of Integrated Circuits and Systems, pages 1-1, Jan 2025. URL: https://doi.org/10.1109/tcad.2025.3644293, doi:10.1109/tcad.2025.3644293. This article has 45 citations and is from a domain leading peer-reviewed journal.

6. (lai2023chipformertransferablechip pages 15-17): Yao Lai, Jinxin Liu, Zhentao Tang, Bin Wang, Jianye Hao, and Ping Luo. Chipformer: transferable chip placement via offline decision transformer. ArXiv, Jun 2023. URL: https://doi.org/10.48550/arxiv.2306.14744, doi:10.48550/arxiv.2306.14744. This article has 120 citations.

7. (lai2023chipformertransferablechip pages 18-20): Yao Lai, Jinxin Liu, Zhentao Tang, Bin Wang, Jianye Hao, and Ping Luo. Chipformer: transferable chip placement via offline decision transformer. ArXiv, Jun 2023. URL: https://doi.org/10.48550/arxiv.2306.14744, doi:10.48550/arxiv.2306.14744. This article has 120 citations.

8. (cheng2021onjointlearning pages 7-9): Ruoyu Cheng and Junchi Yan. On joint learning for solving placement and routing in chip design. Preprint, Jan 2021. URL: https://doi.org/10.48550/arxiv.2111.00234, doi:10.48550/arxiv.2111.00234. This article has 163 citations.

9. (cheng2021onjointlearning pages 9-12): Ruoyu Cheng and Junchi Yan. On joint learning for solving placement and routing in chip design. Preprint, Jan 2021. URL: https://doi.org/10.48550/arxiv.2111.00234, doi:10.48550/arxiv.2111.00234. This article has 163 citations.

10. (lin2020dreamplace2.0opensource pages 3-4): Yibo Lin, David Z. Pan, Haoxing Ren, and Brucek Khailany. Dreamplace 2.0: open-source gpu-accelerated global and detailed placement for large-scale vlsi designs. 2020 China Semiconductor Technology International Conference (CSTIC), pages 1-4, Jun 2020. URL: https://doi.org/10.1109/cstic49141.2020.9282573, doi:10.1109/cstic49141.2020.9282573. This article has 31 citations.

11. (lin2020dreamplace2.0opensource pages 2-3): Yibo Lin, David Z. Pan, Haoxing Ren, and Brucek Khailany. Dreamplace 2.0: open-source gpu-accelerated global and detailed placement for large-scale vlsi designs. 2020 China Semiconductor Technology International Conference (CSTIC), pages 1-4, Jun 2020. URL: https://doi.org/10.1109/cstic49141.2020.9282573, doi:10.1109/cstic49141.2020.9282573. This article has 31 citations.

12. (liu2021globalplacementwith pages 4-4): Siting Liu, Qi Sun, Peiyu Liao, Yibo Lin, and Bei Yu. Global placement with deep learning-enabled explicit routability optimization. 2021 Design, Automation & Test in Europe Conference & Exhibition (DATE), pages 1821-1824, Feb 2021. URL: https://doi.org/10.23919/date51398.2021.9473959, doi:10.23919/date51398.2021.9473959. This article has 79 citations.

13. (crocker2021physicallyconstrainedpcb pages 41-49): P Crocker. Physically constrained pcb placement using deep reinforcement learning. Unknown journal, 2021.

14. (murphy2020neuralnetworkfitness pages 36-40): JR Murphy. Neural network fitness function for optimization-based approaches to pcb design automation. Unknown journal, 2020.

15. (murphy2020neuralnetworkfitness pages 1-5): JR Murphy. Neural network fitness function for optimization-based approaches to pcb design automation. Unknown journal, 2020.

16. (murphy2020neuralnetworkfitness pages 40-48): JR Murphy. Neural network fitness function for optimization-based approaches to pcb design automation. Unknown journal, 2020.

17. (murphy2020neuralnetworkfitness pages 16-20): JR Murphy. Neural network fitness function for optimization-based approaches to pcb design automation. Unknown journal, 2020.

18. (li2023fanoutnetaneuralized pages 7-8): Haiyun Li, Jixin Zhang, Ning Xu, and Mingyu Liu. Fanoutnet: a neuralized pcb fanout automation method using deep reinforcement learning. Proceedings of the AAAI Conference on Artificial Intelligence, 37:8554-8561, Jun 2023. URL: https://doi.org/10.1609/aaai.v37i7.26030, doi:10.1609/aaai.v37i7.26030. This article has 15 citations and is from a domain leading peer-reviewed journal.

19. (li2023fanoutnetaneuralized pages 6-7): Haiyun Li, Jixin Zhang, Ning Xu, and Mingyu Liu. Fanoutnet: a neuralized pcb fanout automation method using deep reinforcement learning. Proceedings of the AAAI Conference on Artificial Intelligence, 37:8554-8561, Jun 2023. URL: https://doi.org/10.1609/aaai.v37i7.26030, doi:10.1609/aaai.v37i7.26030. This article has 15 citations and is from a domain leading peer-reviewed journal.

20. (li2023fanoutnetaneuralized pages 1-2): Haiyun Li, Jixin Zhang, Ning Xu, and Mingyu Liu. Fanoutnet: a neuralized pcb fanout automation method using deep reinforcement learning. Proceedings of the AAAI Conference on Artificial Intelligence, 37:8554-8561, Jun 2023. URL: https://doi.org/10.1609/aaai.v37i7.26030, doi:10.1609/aaai.v37i7.26030. This article has 15 citations and is from a domain leading peer-reviewed journal.

21. (li2023fanoutnetaneuralized pages 4-6): Haiyun Li, Jixin Zhang, Ning Xu, and Mingyu Liu. Fanoutnet: a neuralized pcb fanout automation method using deep reinforcement learning. Proceedings of the AAAI Conference on Artificial Intelligence, 37:8554-8561, Jun 2023. URL: https://doi.org/10.1609/aaai.v37i7.26030, doi:10.1609/aaai.v37i7.26030. This article has 15 citations and is from a domain leading peer-reviewed journal.

22. (liao2020adeepreinforcement pages 9-11): Haiguang Liao, Wentai Zhang, Xuliang Dong, Barnabas Poczos, Kenji Shimada, and Levent Burak Kara. A deep reinforcement learning approach for global routing. Nov 2020. URL: https://doi.org/10.1115/1.4045044, doi:10.1115/1.4045044. This article has 145 citations and is from a domain leading peer-reviewed journal.

23. (liao2020adeepreinforcement pages 11-13): Haiguang Liao, Wentai Zhang, Xuliang Dong, Barnabas Poczos, Kenji Shimada, and Levent Burak Kara. A deep reinforcement learning approach for global routing. Nov 2020. URL: https://doi.org/10.1115/1.4045044, doi:10.1115/1.4045044. This article has 145 citations and is from a domain leading peer-reviewed journal.

24. (huang2021rankingcostbuilding pages 7-9): Shiyu Huang, Bin Wang, Dong Li, Jianye Hao, Ting Chen, and Jun Zhu. Ranking cost: building an efficient and scalable circuit routing planner with evolution-based optimization. Preprint, Jan 2021. URL: https://doi.org/10.48550/arxiv.2110.03939, doi:10.48550/arxiv.2110.03939. This article has 4 citations.

25. (merrill2021hungryforfully pages 85-89): DJ Merrill. Hungry for fully automated design of embedded systems? Unknown journal, 2021.