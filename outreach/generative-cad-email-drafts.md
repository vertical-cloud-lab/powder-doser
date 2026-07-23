# Generative-CAD outreach — email drafts (July 2026)

Draft first-contact emails for the three shortlisted contacts from
[`paper/background/06-generative-cad-outreach-contacts.md`](../paper/background/06-generative-cad-outreach-contacts.md),
per the shortlist in
[PR #43](https://github.com/vertical-cloud-lab/powder-doser/pull/43#issuecomment-4500344330).

## Routing notes (read before sending)

- **Sender: Luke Winters** (`lbwinters`). Cc **Sterling Baird** on every email.
  Per Sterling's earlier note, cross-cc Sam Charles and William Mulberry as
  applicable so everyone stays in the loop.
- **Run each draft past Sterling on Slack before sending.**
- Sterling is **fully at BYU** — do not mention the Acceleration Consortium as
  an affiliation.
- Recipient addresses below were taken from the author-contact sections of the
  cited papers (see the contacts file). **Re-verify each address at its source
  URL before sending.**
- **Jessie Frazelle:** no public personal email. Use the address from the lab
  Slack thread
  ([link](https://verticalcloudlabbyu.slack.com/archives/C0B3CGGV4VC/p1779293517201589?thread_ts=1778701701.547399&cid=C0B3CGGV4VC));
  if it bounces, tell Sterling. Note Sterling already sent Jessie a short
  LinkedIn message on 20 May 2026 referencing
  [PR #7](https://github.com/vertical-cloud-lab/powder-doser/pull/7#issuecomment-4482605596) —
  the draft below acknowledges that.
- **Adam Urbanczyk:** no public email either. Send the draft as a direct
  message / post via the [CadQuery Discord](https://cadquery.readthedocs.io/en/latest/)
  or open a GitHub Discussion on
  [CadQuery/cadquery](https://github.com/CadQuery/cadquery) — the text works
  unchanged in either channel.

---

## 1. Jesse Barkley (cc Amir Barati Farimani) — feedback on our CADSmith usage

**To:** Jesse Barkley `<jabarkle@andrew.cmu.edu>`
**Cc:** Amir Barati Farimani `<afariman@andrew.cmu.edu>`; Sterling Baird
**Subject:** Feedback conversation on our use of CADSmith for an open-source powder-dosing device (BYU)

Hi Jesse,

I'm Luke Winters, a researcher in Dr. Sterling Baird's Vertical Cloud Lab at
Brigham Young University (cc'd). We're building an open-source, auger-fed
powder doser for metal-AM powder handling
(https://github.com/vertical-cloud-lab/powder-doser), and we generate most of
our CAD with LLM/agentic pipelines — which is how we found CADSmith
(arXiv:2603.26512).

We've been running CADSmith on real parts, not just reading the paper. We
drove our two printable plates through the Planner→Coder→Executor→Judge loop:
both converged on iteration 0 (3 LLM calls each, 45–67 s), with volumes within
0.5–1.1 % of our hand-authored CadQuery references. The converged STEPs, Judge
three-view renders, generated CadQuery, and full logs are committed here:
https://github.com/vertical-cloud-lab/powder-doser/pull/59

To get it running we made three small patches we'd be happy to upstream:
raising the coder `max_tokens` from 4096 to 16000, concatenating all `"text"`
content blocks instead of reading only `content[0].text`, and updating the
Judge's retired model pin.

Where we hit the tool's current edge: our device is a ten-printed-part
assembly with interaction constraints (gear mesh, running fits, a deliberate
3 mm solenoid interference for the hammer-tap), and CADSmith is single-part
oriented — so we kept a hand-authored CadQuery assembly with programmatic
interference checks as the source of truth
(https://github.com/vertical-cloud-lab/powder-doser/pull/112). We also built a
single self-contained spec prompt to compare CADSmith, GitHub Copilot, and
zoo.dev Text-to-CAD on identical input
(https://github.com/vertical-cloud-lab/powder-doser/pull/105).

Would you (and Prof. Farimani, if interested) be open to a 30-minute call to
give us feedback on how we're using CADSmith, and to talk about
assembly-level generation and validation? We're glad to share all run logs and
renders beforehand.

Best,
Luke Winters
Vertical Cloud Lab (PI: Dr. Sterling Baird), Brigham Young University
https://github.com/vertical-cloud-lab/powder-doser

---

## 2. Adam Urbanczyk — recommendations on LLM-generated CadQuery

**To:** Adam Urbanczyk (via CadQuery Discord DM or a GitHub Discussion on `CadQuery/cadquery` — no public email; see routing notes)
**Cc (if sent as email):** Sterling Baird
**Subject:** Advice on LLM-generated CadQuery for an open-source lab-hardware project (BYU)

Hi Adam,

I'm Luke Winters, a researcher in Dr. Sterling Baird's Vertical Cloud Lab at
Brigham Young University. We're building an open-source, auger-fed powder
doser for metal-AM powder handling
(https://github.com/vertical-cloud-lab/powder-doser), and CadQuery is our
primary CAD medium — with the twist that most of the code is LLM-generated and
then human-reviewed.

Concretely, our full parametric assembly lives in CadQuery: a `params.py`
single source of truth for every dimension, helpers for involute spur
gears/rings, helical Archimedes screws, and printable single-start threads,
and an `interference_report()` that gates the build on ten spec rules — bore
openness, gear mesh without jam, running fits, and one deliberate 3 mm
solenoid interference
(https://github.com/vertical-cloud-lab/powder-doser/pull/112). Individual
parts (split shaft-collar brackets, a tap collar, hinged mounting plates) were
authored the same way, and we've adopted OCP CAD Viewer as our local authoring
loop (https://github.com/vertical-cloud-lab/powder-doser/pull/70).

We'd love a conversation — a short call or async here on Discord, whichever
you prefer — about:

1. Your recommendations for making LLM-written CadQuery robust: is there an
   API subset or idiom set you'd steer code generators toward, and which OCCT
   failure modes do you see people hit most?
2. Feedback on our current usage (the interference-gated assembly above) —
   anything that looks fragile or unidiomatic to you?
3. Whether the failure/success patterns we've logged from LLM-generated
   CadQuery would be useful to the project, e.g. as docs or examples we could
   contribute back.

Thanks for maintaining CadQuery — it's been the backbone of this project.

Best,
Luke Winters
Vertical Cloud Lab (PI: Dr. Sterling Baird), Brigham Young University
https://github.com/vertical-cloud-lab/powder-doser

---

## 3. Jessie Frazelle — academic collaboration on design for automated metal 3D printing

**To:** Jessie Frazelle (address from the lab Slack thread — see routing notes; if it bounces, tell Sterling)
**Cc:** Sterling Baird
**Subject:** Academic collaboration: Zoo tools for design-for-automated metal 3D printing (BYU)

Hi Jessie,

I'm Luke Winters, a researcher in Dr. Sterling Baird's Vertical Cloud Lab at
Brigham Young University — Sterling sent you a short LinkedIn note about this
in May, and I'm following up with the specifics.

We're building an open-source, auger-fed powder doser for automated metal 3D
printing workflows (https://github.com/vertical-cloud-lab/powder-doser), and
Zoo's tools are already load-bearing in it:

- We drove the **Text-to-CAD API** part-by-part over our full engineering
  spec: all eleven printed parts generated via `ai/text-to-cad?kcl=true`,
  committed as native KCL + STEP with bounding-box manifests verified against
  the spec (https://github.com/vertical-cloud-lab/powder-doser/pull/110).
- We're paying **Zoo Design Studio** subscribers (unlimited plan) and wrote up
  a ZDS best-practices note plus a cleaned transcript of one of our editing
  sessions (https://github.com/vertical-cloud-lab/powder-doser/pull/93).
- We maintain a head-to-head benchmark prompt comparing zoo.dev, CADSmith, and
  GitHub Copilot on the identical assembly spec
  (https://github.com/vertical-cloud-lab/powder-doser/pull/105), and we
  hand-edit KCL directly for some parts
  (https://github.com/vertical-cloud-lab/powder-doser/pull/66).

We'd like to explore an academic research collaboration around design for
automated metal 3D printing — powder dosing and handling specifically. Ideas
we'd bring to a call: benchmarking and hardening Text-to-CAD on
manufacturability-constrained parts (we have specs, ground-truth CAD, and
printed hardware to test against), KCL as a target language for design agents,
and a case study in the hardware paper we're preparing for *Digital
Discovery*. There may also be a fit with our NASA Space Grant work on
additive-manufacturing alloy workflows.

Would you have 30 minutes for a call in the next few weeks? Happy to send a
short deck or just walk through the repo live.

Best,
Luke Winters
Vertical Cloud Lab (PI: Dr. Sterling Baird), Brigham Young University
https://github.com/vertical-cloud-lab/powder-doser
