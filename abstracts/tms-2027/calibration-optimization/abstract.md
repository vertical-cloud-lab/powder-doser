---
Meeting: TMS 2027 Annual Meeting & Exhibition (Orlando, FL)
Dates: March 14–18, 2027 (Orlando World Center Marriott)
Submission deadline: July 1, 2026
Format: abstract body limited to 150 words; submitted via ProgramMaster
(https://www.programmaster.org/TMS2027).
Focus: doser calibration as multi-objective, multi-task optimization across
many powder types (split from the original combined abstract; see
../README.md).
Target symposium (top-5 ranking from tms2027_symposium_organizers.csv;
rationale in ../README.md):
  1. AI-Enabled Materials Processing: Integrating Accelerated Experimental
     Workflows and Processing-Aware Machine Learning (Data-Driven and
     Computational Materials Design track) — primary
  2. AI/ML/Data Informatics for Materials Discovery: Bridging Experiment,
     Theory, and Modeling (Data-Driven and Computational Materials Design)
  3. Algorithms Development in Materials Science and Engineering (Data-Driven
     and Computational Materials Design)
  4. Artificial Intelligence Applications in Integrated Computational
     Materials Engineering (AI-ICME) (Data-Driven and Computational
     Materials Design)
  5. Powder Materials Processing and Fundamental Understanding (Materials
     Synthesis and Processing)
  Submit the abstract to only one symposium.
---

Title: Multi-Objective, Multi-Task Calibration of an Open-Source Powder Doser Across Diverse Metal Powders

Dispensed mass from a powder doser depends on both actuator settings and powder properties, making calibration across many feedstocks a significant experimental burden. We frame calibration of an open-source, auger-based powder doser—built for metering laser powder bed fusion (L-PBF) feedstocks—as a multi-objective, multi-task optimization problem. Stepper-driven auger rotation, solenoid tapping, vibration-motor agitation, and servo-controlled tilt define the parameter space; competing objectives include dose accuracy, repeatability, dispensing time, and minimum and maximum deliverable dose. Each powder—progressing from non-hazardous surrogates to L-PBF feedstocks such as AlSi10Mg, silicon, and stainless steel—constitutes a related task, motivating multi-task models that share information across powders to reduce per-powder calibration effort. We are developing a machine-learning calibration algorithm that maps commanded parameters to dispensed mass per powder, trained on gravimetric data from a systematic parameter sweep and targeting ±1 mg accuracy (±0.1 mg stretch). We discuss this calibration layer within a self-driving, Bayesian-optimization alloy-discovery loop.
