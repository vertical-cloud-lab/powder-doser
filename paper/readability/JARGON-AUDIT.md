# Jargon audit — `paper/main.tex` and `paper/si.tex`

Where the manuscript is hardest to read, why, and what to do about it.

**This document changes nothing in the manuscript.** It is a findings list, ranked
by how much damage each problem does, with the exact line to edit and a suggested
plain-language replacement. Every count is reproducible:

```bash
python paper/readability/jargon_audit.py   # writes audit_report.{md,json}
```

Line numbers refer to `paper/main.tex` and `paper/si.tex` at the commit that added
this file. Re-run the script after any revision; the numbers below will move.

---

## The short version

| # | Where | Problem | Cost if unfixed |
|---|---|---|---|
| 1 | Abstract, `main.tex:135` | 229 words, mean 33 words/sentence, one 62-word sentence carrying two em-dash asides | The abstract is the only part most people read. It currently reads as the densest text in the paper |
| 2 | `main.tex:224`, `:216`, `:210` | Four words mean something **different** to this journal's readership: *ablation*, *regression*, *interference*, *primitives* | Silent mis-reading — worse than not understanding |
| 3 | `main.tex:287` | A 117-word sentence in Conclusions containing *policy-parameter space*, *contextual*, *constraint-aware* | The future-work paragraph, the one editors weigh for novelty, is the least legible in the paper |
| 4 | 8 acronyms | `STL`, `GUI`, `PCB`, `CI`, `REPL`, `CNC`, `EMF` never expanded; `KCL` looks defined but isn't | Reader stalls, and `GUI` appears in captions, which are read standalone |
| 5 | Throughout | Seven different names for "we didn't use normal CAD software" (14 uses) | Reads as hedging on the paper's headline methodological claim |
| 6 | `main.tex:222–277` | *target* means both a **powder** and a **mass** in the same section | Genuine ambiguity in the acceptance criteria |
| 7 | `main.tex:222`, `:231`, `:244–246` | *glidant*, *trickler*, *feed factor*, *100–200 mesh* (against `~45 µm` two rows up) | Powder-metrology reviewer (Khinast persona, round-2 mock review) will land here first |
| 8 | `main.tex:231`, `si.tex:136` | Bare `#116` / `#39`; 21 uses of "the repository" leaning on two anchors | Unresolvable for anyone without the repo open |

---

## 1. The abstract is the densest 229 words in the paper

Measured: **33.0 words/sentence** (paper mean 23.3), Fog 26.4, three sentences over
35 words. The worst is 62 words with two em-dash asides:

> Uniquely, the platform's mechanical parts were designed without conventional CAD
> software: every part was modelled through an **agent-mediated programmatic-CAD
> workflow**—large-language-model (LLM) coding agents authoring parametric CAD code
> under human review, with chat-driven text-to-CAD services evaluated as
> **comparators** and one (Zoo Design Studio) adopted late in the project—and the
> full design history, including failures, is preserved in a public
> version-controlled repository. — `main.tex:135`

Three separate claims (how parts were made, what else was tried, where the history
lives) are welded into one sentence, and the load-bearing noun phrase
*agent-mediated programmatic-CAD workflow* stacks three modifiers before the reader
reaches a concrete noun.

**Suggested rewrite** (three sentences, same content, no em-dashes, ~65 words):

> Unusually, no conventional CAD program was used to design the mechanical parts.
> Instead, large-language-model (LLM) coding agents wrote the CAD as code, which the
> team reviewed, printed and tested. Two chat-driven text-to-CAD services were tried
> alongside, and one of them (Zoo Design Studio) was adopted for the final parts. The
> complete design history, failures included, is public in a version-controlled
> repository.

Also in the abstract: *closed-loop gravimetric feedback* and *ISO 8655-inspired
gravimetric validation protocol* arrive before either term is explained. Gloss
`gravimetric` once on first use — "weight-based (gravimetric)" — and it can then run
free for the remaining 15 uses.

---

## 2. Words that mean something *else* to a Digital Discovery reader

These are the highest-severity findings, because the reader does not stop — they
carry on with the wrong meaning.

| Term | Line | What this paper means | What a DD reader hears |
|---|---|---|---|
| **ablations** | `main.tex:224` | "actuation ablations (auger only, +tap, +vibration)" — a leave-one-out comparison | *Laser ablation.* This is a materials journal |
| **silent regressions** | `main.tex:216` (paragraph heading), `:170` | An edit quietly changing an unrelated feature | *Regression analysis.* Curve fitting |
| **interferences** | `main.tex:210`, `:214` (4×) | Two solid bodies occupying the same space | Wave/signal interference |
| **primitives** | `main.tex:269`, `:275` | Low-level firmware commands | Primitive cells / primitive vectors |
| **parity** | `main.tex:224` | Requested-vs-measured plot | Parity as a symmetry operation |
| **unit operation** | `main.tex:164` | Process step | Chem-eng term of art; fine for some readers, opaque to CS/ML ones |

Fixes, in ascending order of effort:

- `main.tex:224` — "actuation **ablations** (auger only, +tap, +vibration)" →
  "actuation **comparisons** (auger alone, auger + tap, auger + vibration)".
  Nothing is lost; the ML sense of *ablation* is not needed anywhere in this paper.
- `main.tex:216` — paragraph heading "Trust, verification, and silent regressions."
  → "Trust, verification, and silent changes to parts we were not editing."
  The body sentence already explains the phenomenon; the heading should not rely on
  a software-engineering sense of *regression*.
- `main.tex:210` (Fig. 2 caption, first use) — gloss inline: "part-to-part
  interferences (features occupying the same space)". Later uses can stay bare.
- `main.tex:269` — "dose **primitives** (rotate-by-steps, tap-burst, …)" →
  "dose **commands**". Likewise `:275` "agitation primitive" → "agitation command".
- `main.tex:224` — "requested-versus-measured dose **parity**" → "a plot of
  requested against measured dose". Fig. 3(b) already says this in plain words.
- `main.tex:164` — "the gating unit operation" → "the step that limits the whole
  workflow".

---

## 3. Sentence architecture

**64 of 234 sentences are ≥35 words; 20 are ≥50.** The five worst:

| Words | Line | Section |
|--:|---|---|
| 117 | `main.tex:287` | Conclusions (future work) |
| 89 | `main.tex:222` | Dispensing performance |
| 74 | `main.tex:224` | Dispensing performance |
| 72 | `main.tex:214` | Generative AI as a CAD tool |
| 68 | `main.tex:277` | Dispensing characterization protocol |

Fourteen sentences carry **two or more em-dash asides**. Two dashes in one sentence
means the reader is holding a suspended clause while parsing a second one; this is
the mechanism behind most of the "dense" feeling, and it is cheap to fix by
promoting the aside to its own sentence.

### The 117-word sentence, `main.tex:287`

The future-work paragraph is one sentence with a four-item enumeration, and item (2)
contains the densest phrase in the manuscript:

> …the three-phase procedure's thresholds, angles, speeds, and tap schedules form a
> natural **policy-parameter space** for **contextual, constraint-aware** Bayesian
> optimization against the gravimetric loop…

Three pieces of reinforcement-learning / BO vocabulary in eleven words, none defined.
**Suggested rewrite:**

> (2) automatic per-powder calibration. This paper sets the thresholds, tilt angles,
> speeds and tap schedules by hand; together they define a search space that Bayesian
> optimization could tune for each powder, subject to the constraint that overshoot
> cannot be undone. A problem formulation is already documented in the repository.

More generally: break `:287` into one sentence per numbered stage. Editors read the
future-work paragraph carefully, and right now it is the least legible text in the
paper.

### Stacked hyphenated modifiers

21 distinct three-or-more-word hyphen chains. Most are fine and idiomatic
(`part-by-part`, `off-the-shelf`, `text-to-CAD`). Two are worth retiring:

- `cross-contamination-free disposable wetted parts` (`main.tex:260`) — four stacked
  modifiers plus process-engineering jargon. **`wetted parts` means "the parts the
  powder touches"** and nothing in the paper explains that. Suggested: "throw away
  and reprint the parts the powder touches, so channels never cross-contaminate".
- `eccentric-rotating-mass (ERM)` (`main.tex:178`) — correct, but add the everyday
  anchor on first use: "an eccentric-rotating-mass (ERM) motor, the type used to make
  a phone vibrate".

---

## 4. Acronyms

| Acronym | Uses | Status | Action |
|---|--:|---|---|
| `STL` | 5 | never expanded | "STL mesh files" on first use (`main.tex:205`) |
| `GUI` | 4 | never expanded, and **3 of 4 uses are in captions** | See §5 — drop the term entirely |
| `PCB` | 2 | never expanded | "printed circuit boards (PCBs)" at `main.tex:287` |
| `CI` | 1 | "continuous integration" is spelled out at `:205`, but never abbreviated; then `CI` appears at `:216` | Write "(CI)" at `:205` or spell it out at `:216` |
| `REPL` | 1 | never expanded | `main.tex:275`: "at the REPL" → "from the interactive prompt on the microcontroller" |
| `CNC` | 1 | never expanded | `main.tex:191` — low stakes, but expand |
| `EMF` | 1 | never expanded | `si.tex:65`, BOM only — acceptable |
| `KCL` | 2 | **pseudo-defined** | See below |
| `CV` | 2 | abbreviation used at `:224`, parenthetical definition at `:277` | Move to "coefficient of variation (CV)" at first use |

**`KCL` is the interesting one.** `main.tex:205` reads "a code-based CAD kernel
(KCL)", which has the *shape* of a definition — parenthesis after a noun phrase —
but the parenthesis holds the acronym, not its expansion. KCL is the KittyCAD
Language. A reader will believe they were told what it stands for and will not be
able to recall it. The automated check scores this as "defined at first use"; it is
the one place the script is wrong, and it is wrong in the same way a reader would be.

Correctly handled already: `LLM`, `SDL`, `AM`, `ERM` are all expanded at first use.
`LLM` is expanded **twice** (abstract `:135` and again at `:170`); drop the second.

---

## 5. Seven names for one idea

The paper's headline methodological claim — that no ordinary CAD program was used —
is made 14 times under seven different names:

| Phrasing | Uses | Where |
|---|--:|---|
| "conventional interactive CAD package" | 3 | body |
| "GUI CAD package" | 3 + 1 (SI) | **captions** |
| "conventional CAD software" | 2 | abstract, Conclusions |
| "graphical editor" | 2 | body |
| "traditional CAD" | 1 | Tool comparison |
| "graphical CAD environment" | 1 | body |
| "conventional CAD sessions" | 1 | Tool comparison |

Repeating a claim in seven wordings reads as hedging, and `GUI` — the one term that is
an undefined acronym — is the term used in the captions, which are read standalone
and out of order.

**Recommendation:** pick one. Expand once at `main.tex:170`
("conventional CAD software such as SolidWorks or Fusion 360"), then use
**"conventional CAD software"** everywhere, captions included. That deletes `GUI`
from the paper and makes the claim land as one claim rather than seven.

---

## 6. "Target" does two jobs in the same section

- **Powders**: "four **target** materials" (`:222`), "**Target** AM alloy powder",
  "**Target** powder; worst-case fines" (Table 1, `:243–245`)
- **Masses**: "four **target** masses spanning the envelope" (`:277`),
  "the 20 mg **target**" (`:275`), "**target** mass enters the controller" (Fig. 1d)

Both senses appear inside the acceptance-criteria discussion, where precision matters
most: "±10% below 100 mg (i.e. at the 50 and 20 mg targets)" sits ~40 words from
"target materials for the autonomous-AM application".

**Recommendation:** keep *target* for masses (it is standard metrology usage) and
rename the powder class to **"application powders"** — it is more informative than
*target* anyway, since the contrast being drawn is with the *surrogate* powders.
Touches `:222` and three Table 1 rows.

---

## 7. Powder-handling vocabulary

The round-2 mock review already flagged feeder specification as a reviewer
sticking point; a powder-metrology reviewer will read §Dispensing performance first,
and it is the **highest jargon-density section in the paper (6.9 hits/100 words)**.

| Term | Line | Fix |
|---|---|---|
| **glidant** | `:222`, `:231`, `:246` (4×) | First use: "a fumed-silica **flow aid (glidant)**". The gloss currently appears only in the last Table 1 column |
| **trickler** | `:222`, `:231`, `:244` | First use: "jammed a commercial powder **trickler** (a small vibratory dispenser)" |
| **feed factor** | `:224` | Already half-glossed as "mass-flow"; make it explicit: "mass delivered per auger revolution (the *feed factor*)" |
| **loss-in-weight feeders** | `:166` | "feeders that meter powder by continuously weighing the hopper as it empties" |
| **master-alloy powders** | `:164` | "pre-alloyed master powders" |
| **operating envelope** | `:224`, `:277` | "the range of dose masses the platform is designed to cover" |
| **rheologically diverse** | `:222` | "spanning a wide range of flow behaviour" |
| **gas-atomized** | `:222`, `:243` | Gloss once: "gas-atomized (spherical, made by spraying molten metal)" |

### One unit inconsistency worth fixing regardless of jargon

Table 1 gives the two silicon grades in **different unit systems**:

```
Silicon, fine   (~45 µm)          ← micrometres
Silicon, coarse (100–200 mesh)    ← US sieve mesh
```

These are the two rows a reader will most want to compare, and they cannot be
compared as written. Give both in µm with mesh in parentheses:
`Silicon, coarse (75–150 µm; 100–200 mesh)`.

---

## 8. References a reader outside the repo cannot resolve

- **`(issues #88/#116)`** in the Table 1 caption (`main.tex:231`) and
  **`discussion #39`** in the SI (`si.tex:136`). Bare issue numbers are meaningless
  in a published caption. Use full URLs, or cite the repository reference and give
  the issue number after it.
- **"the repository"** appears **21 times**. It is anchored twice — the footnote at
  `main.tex:170` and the Data availability statement at `:303` — and the other ~19
  uses, including three in standalone figure/table captions, assume the reader has
  already met the anchor. RSC style would have this as a numbered reference cited on
  first use in each section.
- **Repo-internal paths** (`DESIGN-LOG.md` at `main.tex:183`,
  `cad/auger-geared/nozzle-variants.scad` at `si.tex:112`) are good provenance and
  should stay, but should hang off a resolvable URL.

## 9. Brand-name density

22 distinct product/tool names appear in the main text. In Experimental and the BOM
this is correct and required. In **Results** it is not:

> Control electronics are a single Raspberry Pi Pico W microcontroller running
> MicroPython, with a **Tic T500** driver for the stepper, **DRV8871** for the
> solenoid, **DRV2605L** for the vibration motor, and a **MAX3232** transceiver for
> the balance's RS-232 interface… — `main.tex:187`

Four part numbers in one Results sentence, and **the identical list is repeated
verbatim in Experimental at `:269`**, so cutting it from Results loses nothing:

> A single \$6 Raspberry Pi Pico W microcontroller drives the stepper, solenoid and
> vibration motor and reads the balance; drivers, part numbers and the wiring guide
> are given in Experimental and SI Table S1.

---

## 10. Where the jargon is fine — do not "fix" these

The script flags them, but they should stay as they are:

- **Bill of materials (`si.tex`, 6.1 hits/100 w)** and **Electronics and firmware
  (`main.tex:269`, 6.8/100 w)** — `UART`, `I²C`, `H-bridge`, `buck regulator`,
  `back-EMF clamp` are exactly what a builder needs. This is the second-highest
  jargon density in the paper and it is correct.
- **Construction guide (`si.tex:79–99`)** — 8.2 words/sentence, Fog 8.5. The
  plainest and best-written prose in the submission. It is the model the Results
  section should imitate.
- **Author contributions (`main.tex:297`)** — 25.6 abstract nouns per 100 words, by
  far the highest in the paper. This is CRediT boilerplate and must stay verbatim.
- **`gravimetric` (16×), `cohesive`, `bridging`, `flowability`** — correct terms of
  art. Gloss on first use, then use freely.
- **`ISO 8655`, `coefficient of variation`, `systematic/random error`** — these are
  the standards vocabulary the validation protocol is deliberately borrowing;
  replacing them would weaken the claim.

---

## Gloss-at-first-use checklist

One-line additions, in reading order. This is the cheapest 80% of the fix.

| Line | Term | Suggested gloss |
|---|---|---|
| `main.tex:135` | gravimetric | weight-based (gravimetric) |
| `:164` | master-alloy powders | pre-alloyed master powders |
| `:164` | gating unit operation | the step that limits the whole workflow |
| `:166` | loss-in-weight feeders | metered by weighing the hopper as it empties |
| `:170` | conventional CAD software | such as SolidWorks or Fusion 360 |
| `:178` | ERM | the type of motor used to make a phone vibrate |
| `:205` | STL | STL mesh files |
| `:205` | KCL | KittyCAD Language, Zoo's CAD scripting language |
| `:205` | continuous integration | continuous integration (CI) |
| `:210` | interferences | features occupying the same space |
| `:216` | watertightness | no holes in the 3D surface |
| `:222` | trickler | a small vibratory dispenser |
| `:222` | glidant | flow aid |
| `:224` | feed factor | mass delivered per auger revolution |
| `:224` | operating envelope | the range of dose masses covered |
| `:275` | REPL | the interactive prompt on the microcontroller |
| `:287` | PCB | printed circuit board |

---

## Appendix — how the numbers were produced

`jargon_audit.py` strips LaTeX (unwrapping formatting commands, rendering inline math
as readable text, dropping citations and floats), segments the text by
`\section`/`\subsection`, and reports sentence-length distributions, acronym
first-use versus first-definition, hits against a curated lexicon of ~70 domain terms
tagged by severity and audience, stacked hyphenated modifiers, multi-em-dash
sentences, nominalization density, and repo-internal references. Vendor SKUs
(`Adafruit #412`) are excluded from the issue-number check; brand names that look
like acronyms (`XPR`, `TOLEDO`) are excluded from the acronym check.

Two caveats on the generated numbers:

1. **Fog is a comparison tool, not a target.** Chemical names, part numbers and
   polysyllabic terms of art inflate it. Compare sections against each other.
2. **The lexicon is a judgement call**, not a standard. Severity 3 means "a reader
   outside this subfield does not know the word, or knows it to mean something
   else". Disagreeing with an entry is a reason to edit `LEXICON` in the script, not
   to distrust the section-level counts.

Related: the plain-language poster draft (PR #103, "better poster" format) is the
natural source of glosses for the terms above — several of these rewrites can be
lifted straight from it.
