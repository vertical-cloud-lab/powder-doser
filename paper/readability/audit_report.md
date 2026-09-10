# Generated jargon / readability audit

Regenerate with `python paper/readability/jargon_audit.py`. The narrative interpretation of these numbers, with suggested rewrites, is in [`JARGON-AUDIT.md`](JARGON-AUDIT.md).

Corpus: 104 prose units, 5449 words, 234 sentences across `main.tex` and `si.tex`.

## 1. Section scoreboard

`Fog` is a Gunning-Fog style grade estimate (higher = denser); it is inflated by chemical names and part numbers, so compare sections against each other rather than against an absolute target.

| Section | Words | Mean sent. | Longest | Sent. >35w | Jargon/100w | Abstract nouns/100w | Fog |
|---|--:|--:|--:|--:|--:|--:|--:|
| Electronics and firmware | 73 | 24.3 | 43 | 1 | 8.2 | 1.4 | 15.2 |
| Dispensing performance | 697 | 25.8 | 89 | 7 | 7.2 | 5.6 | 24.3 |
| Bill of materials | 197 | 7.3 | 0 | 0 | 6.6 | 2.0 | 11.1 |
| Mechanical design and fabrication | 106 | 26.5 | 49 | 1 | 5.7 | 3.8 | 15.9 |
| Construction guide | 140 | 8.2 | 0 | 0 | 4.3 | 0.7 | 8.5 |
| Exit-nozzle variants | 71 | 8.9 | 0 | 0 | 4.2 | 2.8 | 11.6 |
| Abstract | 231 | 33.0 | 62 | 3 | 3.9 | 3.0 | 26.4 |
| AI design workflow and logging | 130 | 32.5 | 39 | 3 | 3.8 | 3.1 | 21.9 |
| Conclusions | 297 | 29.7 | 118 | 3 | 3.4 | 4.4 | 26.1 |
| Data availability | 64 | 21.3 | 0 | 0 | 3.1 | 6.2 | 16.7 |
| Platform overview | 492 | 30.8 | 60 | 7 | 2.8 | 2.4 | 19.3 |
| Generative AI as a CAD tool | 1053 | 30.1 | 72 | 14 | 2.7 | 5.9 | 22.7 |
| Introduction | 665 | 36.9 | 64 | 11 | 2.6 | 5.7 | 27.2 |
| Dispensing characterization protocol | 508 | 33.9 | 68 | 7 | 2.4 | 4.9 | 22.8 |
| Author contributions | 43 | 7.2 | 0 | 0 | 2.3 | 25.6 | 17.8 |
| Cost and accessibility | 106 | 26.5 | 37 | 2 | 1.9 | 3.8 | 22.7 |
| Acknowledgements | 89 | 29.7 | 65 | 1 | 1.1 | 0.0 | 17.7 |
| AI usage log | 99 | 9.0 | 0 | 0 | 1.0 | 4.0 | 13.5 |
| Design evolution | 369 | 26.4 | 45 | 4 | 0.8 | 4.6 | 21.5 |
| Conflicts of interest | 19 | 9.5 | 0 | 0 | 0.0 | 0.0 | 5.9 |

## 2. Longest sentences

64 sentences are >= 35 words; 20 are >= 50.

- **118 words**, 1 em-dashes &mdash; `paper/main.tex:287` (Conclusions, body): Ongoing work extends the platform to (1) a multi-powder doser arraying N printed channels around a shared collection cup (Fig. ), with a loaded subset of 8–12 powders and a path to...
- **89 words**, 2 em-dashes &mdash; `paper/main.tex:222` (Dispensing performance, body): The validation campaign now under way spans ten chemically and rheologically diverse powders (Table ): six low-hazard surrogates chosen to bracket the flowability range — from free...
- **74 words**, 0 em-dashes &mdash; `paper/main.tex:224` (Dispensing performance, body): The data shown are synthetic placeholders (watermarked in the figure) illustrating the analysis and presentation that the bench campaign will populate: (a) cumulative dispensed mas...
- **72 words**, 1 em-dashes &mdash; `paper/main.tex:214` (Generative AI as a CAD tool, body): The results were visually plausible but mechanically incoherent: the first tap collar was an unimplementable amalgamation of separate functions — interferences between features, in...
- **68 words**, 0 em-dashes &mdash; `paper/main.tex:277` (Dispensing characterization protocol, body): Per-powder calibration follows an on-device characterization sweep (also in the repository) that records per-rotation and per-tap mass yield at each tilt angle with repeats, balanc...
- **65 words**, 0 em-dashes &mdash; `paper/main.tex:306` (Acknowledgements, body): Generative AI tools were used extensively and deliberately as research objects and assistants in this work: GitHub Copilot coding agent (Claude-family models) generated CAD code, f...
- **64 words**, 2 em-dashes &mdash; `paper/main.tex:172` (Introduction, body): The objectives of this work are therefore: (1) deliver an open-source, low-cost, accurate single-powder dosing module suitable for SDL integration; (2) document and critically eval...
- **62 words**, 2 em-dashes &mdash; `paper/main.tex:135` (Abstract, abstract): Uniquely, the platform's mechanical parts were designed without conventional CAD software: every part was modelled through an agent-mediated programmatic-CAD workflow — large-langu...
- **60 words**, 0 em-dashes &mdash; `paper/main.tex:178` (Platform overview, body): The auger assembly rides on a hinged mounting plate whose tilt is set by a servo-driven gear sector, so the auger can be parked horizontally (no gravity feed, clean shutoff) and ti...
- **60 words**, 2 em-dashes &mdash; `paper/main.tex:218` (Generative AI as a CAD tool, body): Zoo Design Studio, evaluated last, was judged by the design team to be the best of the tools tried: its Zookeeper agent exhibited markedly stronger spatial reasoning, ran built-in ...
- **59 words**, 0 em-dashes &mdash; `paper/main.tex:214` (Generative AI as a CAD tool, body): Across the 97 logged design iterations, each entry records its trigger, rationale, and outcome (built-and-worked, built-with-issues, failed, or superseded), giving per-part provena...
- **59 words**, 0 em-dashes &mdash; `paper/main.tex:277` (Dispensing characterization protocol, body): Validation adapts the ISO 8655-6 gravimetric structure used for the open-hardware digital pipette to powder dosing: for each of the ten powders (Table ), n≥10 replicate doses at fo...
- **58 words**, 0 em-dashes &mdash; `paper/main.tex:275` (Dispensing characterization protocol, body): The terminal tolerance is predeclared per target mass and strictly tighter than the corresponding acceptance limit (half the limit by default; e.g. ±1 mg at the 20 mg target rather...
- **55 words**, 0 em-dashes &mdash; `paper/main.tex:275` (Dispensing characterization protocol, body): Both phase-exit thresholds and every per-phase parameter (tilt angle, rotation increment, step rate, taps per cycle, tap on/off times, settle time) are independently configurable p...
- **54 words**, 0 em-dashes &mdash; `paper/main.tex:170` (Introduction, body): No conventional interactive CAD package (e.g. SolidWorks or Fusion 360) was used at any point from project start to finish: the only graphical CAD environment opened was Zoo Design...

## 3. Acronyms

| Acronym | Uses | Status |
|---|--:|---|
| STL | 5 | never defined |
| GUI | 4 | never defined |
| CV | 2 | defined AFTER first use |
| PCB | 2 | never defined |
| CNC | 1 | never defined |
| CI | 1 | never defined |
| REPL | 1 | never defined |
| EMF | 1 | never defined |
| LLM | 9 | defined at first use |
| ERM | 8 | defined at first use |
| SDL | 6 | defined at first use |
| AM | 4 | defined at first use |
| KCL | 2 | defined at first use |

## 4. Lexicon hits

Severity 3 = a reader outside the subfield will not know it, or knows it to mean something else. 2 = guessable, gloss at first use. 1 = fine in Experimental/SI.

| Term | Hits | Sev | Category | Lines | Plain gloss |
|---|--:|--:|---|---|---|
| interferences | 4 | 3 | cad/software jargon | main:210, main:214 | two parts occupying the same space |
| glidant | 4 | 3 | powder-handling jargon | main:222, main:231, main:246 | flow aid |
| trickler | 3 | 3 | powder-handling jargon | main:222, main:231, main:244 | a commercial fine-powder dispenser |
| silent regressions | 2 | 3 | ai/ml jargon | main:170, main:216 | an unrelated feature quietly changing; 'regression' reads as curve fitting |
| KCL | 2 | 3 | cad/software jargon | main:205, main:266 | KittyCAD Language, Zoo's CAD scripting language |
| 100–200 mesh | 2 | 3 | powder-handling jargon | main:222, main:245 | sieve size; inconsistent with the um grade quoted for the other silicon |
| operating envelope | 2 | 3 | metrology / stats jargon | main:224 | the range of doses it can handle |
| primitives | 2 | 3 | cad/software jargon | main:269, main:275 | basic command |
| master-alloy | 1 | 3 | powder-handling jargon | main:164 | a concentrated pre-blended alloy |
| unit operation | 1 | 3 | powder-handling jargon | main:164 | process step |
| Loss-in-weight | 1 | 3 | powder-handling jargon | main:166 | feeders metered by watching the hopper lose weight |
| watertightness | 1 | 3 | cad/software jargon | main:216 | no holes in the 3D surface |
| single-body assertions | 1 | 3 | cad/software jargon | main:216 | a check that the part is one solid piece |
| ablations | 1 | 3 | ai/ml jargon | main:224 | leave-one-out comparison; to a materials reader 'ablation' means laser removal of material |
| feed-factor | 1 | 3 | powder-handling jargon | main:224 | mass delivered per auger turn |
| parity | 1 | 3 | metrology / stats jargon | main:224 | a plot of asked-for versus actually-delivered |
| wetted parts | 1 | 3 | business / vague | main:260 | the parts the powder touches |
| REPL | 1 | 3 | cad/software jargon | main:275 | interactive command prompt on the microcontroller |
| policy-parameter space | 1 | 3 | ai/ml jargon | main:287 | the set of tunable dosing settings |
| constraint-aware | 1 | 3 | ai/ml jargon | main:287 | respecting limits such as no-overshoot |
| gravimetric | 16 | 2 | powder-handling jargon | main:135, main:166, main:168, main:178, main:183, main:187, ... | weight-based |
| surrogate | 9 | 2 | powder-handling jargon | main:135, main:222, main:237, main:238, main:239, main:240, ... | stand-in powder |
| ERM | 8 | 2 | electronics jargon | main:178, main:183, main:187, main:198, main:266, main:275, ... | the off-balance motor used in phone vibrate |
| STLs | 5 | 2 | cad/software jargon | main:205, main:266, main:272, main:303, si:77 | the standard 3D-printable mesh file format |
| GUI | 4 | 2 | cad/software jargon | main:183, main:210, main:292, si:113 | point-and-click |
| bridging | 3 | 2 | powder-handling jargon | main:178, main:239, main:240 | powder arching over the opening and stopping |
| transceiver | 3 | 2 | electronics jargon | main:187, main:269, si:62 | signal-level converter |
| flowability | 3 | 2 | powder-handling jargon | main:222, main:224, main:287 | how freely a powder flows |
| terminal tolerance | 3 | 2 | metrology / stats jargon | main:275 | how close to target counts as done |
| comparators | 2 | 2 | ai/ml jargon | main:135, main:170 | tool we compared against |
| agent-mediated | 2 | 2 | ai/ml jargon | main:135, main:170 | done through an AI agent |
| dribble | 2 | 2 | powder-handling jargon | main:193, si:105 | powder trickling out after the dose ends |
| tolerancing | 2 | 2 | cad/software jargon | main:210, main:214 | assigning allowed dimensional error |
| amalgamation | 2 | 2 | business / vague | main:210, main:214 | mash-up |
| gas-atomized | 2 | 2 | powder-handling jargon | main:222, main:243 | made by spraying molten metal into droplets |
| predeclared | 2 | 2 | metrology / stats jargon | main:222, main:275 | fixed in advance |
| descriptors | 2 | 2 | ai/ml jargon | main:224, main:287 | measured property |
| H-bridge | 2 | 2 | electronics jargon | main:269, si:53 | a driver that can reverse the motor |
| PCBs | 2 | 2 | electronics jargon | main:287, main:297 | printed circuit board |
| gating | 1 | 2 | business / vague | main:164 | rate-limiting |
| form factor | 1 | 2 | business / vague | main:166 | size and shape |
| hallucinated | 1 | 2 | ai/ml jargon | main:170 | invented, non-existent |
| benchmark geometry | 1 | 2 | ai/ml jargon | main:170 | test shapes rather than real parts |
| kernel | 1 | 2 | cad/software jargon | main:205 | the geometry engine |
| stale input files | 1 | 2 | cad/software jargon | main:210 | out-of-date source files |
| upstream part files | 1 | 2 | cad/software jargon | main:210 | the files this part must mate with |
| compositional spatial reasoning | 1 | 2 | ai/ml jargon | main:214 | reasoning about how parts fit together |
| defect taxonomy | 1 | 2 | ai/ml jargon | main:214 | a classification of the faults found |
| CI | 1 | 2 | cad/software jargon | main:216 | continuous integration, the automated build service |
| three-view | 1 | 2 | cad/software jargon | main:216 | front/side/top |
| rheologically | 1 | 2 | powder-handling jargon | main:222 | flow-behaviour |
| tapped density | 1 | 2 | powder-handling jargon | main:224 | density after settling by tapping |
| pre-registered | 1 | 2 | metrology / stats jargon | main:224 | committed to in advance |
| fines | 1 | 2 | powder-handling jargon | main:244 | the finest particles |
| contextual | 1 | 2 | ai/ml jargon | main:287 | per-powder |
| buck regulator | 1 | 2 | electronics jargon | si:64 | step-down power supply |
| back-EMF | 1 | 2 | electronics jargon | si:65 | voltage kicked back by the motor |
| shunt regulator | 1 | 2 | electronics jargon | si:65 | clamp that dumps excess voltage |
| I2C | 10 | 1 | electronics jargon | main:178, main:187, main:269, main:275, si:55, si:62, ... | serial link |
| parametric | 9 | 1 | cad/software jargon | main:135, main:170, main:183, main:193, main:205, main:266, ... | dimension-driven |
| cohesive | 7 | 1 | powder-handling jargon | main:222, main:239, main:240, main:241, main:242, main:244, ... | sticky, clumping |
| text-to-CAD | 5 | 1 | ai/ml jargon | main:135, main:170, main:205, main:272, main:306 | type a description, get a 3D model |
| pull request | 5 | 1 | cad/software jargon | main:170, main:205, main:272, si:124 | a proposed, reviewable change |
| NEMA-11 | 5 | 1 | electronics jargon | main:178, main:183, main:266, si:50, si:85 | a standard motor frame size |
| programmatic-CAD | 4 | 1 | ai/ml jargon | main:135, main:170, main:210, main:292 | CAD written as code |
| ISO 8655 | 4 | 1 | metrology / stats jargon | main:135, main:224, main:277 | the pipette-accuracy standard |
| breakout | 3 | 1 | electronics jargon | si:53, si:55, si:62 | a small pre-wired module |
| division of labour | 2 | 1 | business / vague | main:170, main:216 | who did what |
| systematic error | 2 | 1 | metrology / stats jargon | main:224, main:277 | consistent offset from target |
| random error | 2 | 1 | metrology / stats jargon | main:224, main:277 | scatter between repeats |
| coefficient of variation | 2 | 1 | metrology / stats jargon | main:224, main:254 | relative scatter |
| plateau at | 1 | 1 | business / vague | main:216 | stop improving at |
| orthographic | 1 | 1 | cad/software jargon | main:272 | straight-on |
| isometric | 1 | 1 | cad/software jargon | main:272 | angled 3D |

## 5. Stacked hyphenated modifiers

- `part-by-part` (6x &mdash; main:135, main:170, main:210, main:214, main:281)
- `text-to-CAD` (5x &mdash; main:135, main:170, main:205, main:272, main:306)
- `large-language-model` (2x &mdash; main:135, main:170)
- `end-to-end` (2x &mdash; main:170)
- `off-the-shelf` (1x &mdash; main:135)
- `order-of-magnitude` (1x &mdash; main:164)
- `human-in-the-loop` (1x &mdash; main:164)
- `Loss-in-weight` (1x &mdash; main:166)
- `eccentric-rotating-mass` (1x &mdash; main:178)
- `fixed-dispense-point` (1x &mdash; main:193)
- `part-to-part` (1x &mdash; main:210)
- `built-and-worked` (1x &mdash; main:214)
- `built-with-issues` (1x &mdash; main:214)
- `requested-versus-measured` (1x &mdash; main:224)
- `two-orders-of-magnitude` (1x &mdash; main:260)
- `cross-contamination-free` (1x &mdash; main:260)
- `rotate-by-steps` (1x &mdash; main:269)
- `tilt-to-angle` (1x &mdash; main:269)
- `tap-to-target` (1x &mdash; main:275)
- `settle-and-read` (1x &mdash; main:275)
- `step-by-step` (1x &mdash; si:75)

## 6. Sentences with 2+ em-dash asides

14 sentences carry two or more em-dash asides; the 12 with the most are shown.

- 2 dashes, `paper/main.tex:135` (Abstract): Uniquely, the platform's mechanical parts were designed without conventional CAD software: every part was modelled through an agent-mediated programma...
- 2 dashes, `paper/main.tex:164` (Introduction): For autonomous alloy design by additive manufacturing (AM) — where candidate compositions are realized by blending elemental or master-alloy powders —...
- 2 dashes, `paper/main.tex:170` (Introduction): Throughout, the division of labour was explicit — the human team made the design decisions, supplied specifications and drawings, reviewed every outpu...
- 2 dashes, `paper/main.tex:170` (Introduction): Because the entire design history of this project — every prompt, every generated part, every review comment, and every failure — is preserved in a pu...
- 2 dashes, `paper/main.tex:172` (Introduction): The objectives of this work are therefore: (1) deliver an open-source, low-cost, accurate single-powder dosing module suitable for SDL integration; (2...
- 2 dashes, `paper/main.tex:193` (Design evolution): The third generation was a deliberate methodological pivot: rather than asking the AI tools to generate the whole module at once, each part — auger, g...
- 2 dashes, `paper/main.tex:193` (Design evolution): By the late stages, the AI's role had narrowed to modelling the parts — translating the drawings into parametric CAD and computing derived dimensions ...
- 2 dashes, `paper/main.tex:205` (Generative AI as a CAD tool): Two commercial text-to-CAD services, CADSmith and Zoo Design Studio — the latter pairing a code-based CAD kernel (KCL) with a conversational design ag...
- 2 dashes, `paper/main.tex:214` (Generative AI as a CAD tool): This mirrors the known weakness of current LLMs in compositional spatial reasoning and suggests that interface-first decomposition — standard practice...
- 2 dashes, `paper/main.tex:216` (Generative AI as a CAD tool): Automated self-checks (single-body assertions, watertightness, interface-dimension probes run in CI) caught a useful subset of defects cheaply, but sm...
- 2 dashes, `paper/main.tex:218` (Generative AI as a CAD tool): Zoo Design Studio, evaluated last, was judged by the design team to be the best of the tools tried: its Zookeeper agent exhibited markedly stronger sp...
- 2 dashes, `paper/main.tex:222` (Dispensing performance): The validation campaign now under way spans ten chemically and rheologically diverse powders (Table ): six low-hazard surrogates chosen to bracket the...

## 7. References a reader outside the repo cannot resolve

- **unanchored 'the repository'**: 20 hits &mdash; main:170, main:183, main:187, main:191, main:205, main:214, main:218, main:222, main:231, main:266, main:269, main:275, main:277, main:287, si:35, si:75, si:136
- **unanchored 'design log'**: 4 hits &mdash; main:170, main:183, main:191, main:303
- **repo file path**: 2 hits &mdash; main:183, si:112
- **bare issue/discussion number**: 2 hits &mdash; main:231, si:136
