# Generative-CAD outreach — email drafts (July 2026)

Short first-contact emails for the three shortlisted contacts from
[`paper/background/06-generative-cad-outreach-contacts.md`](../paper/background/06-generative-cad-outreach-contacts.md),
per the shortlist in
[PR #43](https://github.com/vertical-cloud-lab/powder-doser/pull/43#issuecomment-4500344330).
Reviewed by Edison Scientific
([review](./edison_artifacts/gencad_outreach_draft_review.answer.md)); its
feedback is incorporated below.

## Routing notes (read before sending)

- **Sender: Luke Winters** (`lbwinters`). Cc **Sterling Baird** on every email.
  Cross-cc Sam Charles and William Mulberry as applicable.
- **Run each draft past Sterling on Slack before sending.**
- Sterling is **fully at BYU** — do not mention the Acceleration Consortium.
- Re-verify recipient addresses at their source URLs (see the contacts file)
  before sending.
- **Jessie Frazelle:** no public personal email. Use the address from the lab
  Slack thread
  ([link](https://verticalcloudlabbyu.slack.com/archives/C0B3CGGV4VC/p1779293517201589?thread_ts=1778701701.547399&cid=C0B3CGGV4VC));
  if it bounces, tell Sterling. Sterling already sent Jessie a LinkedIn note on
  20 May 2026 — the draft mentions it once, without pressing for a reply.
- **Adam Urbanczyk:** no public email. Per Edison's review, prefer a **Discord
  DM** on the CadQuery Discord (no subject line; sign off simply as "Luke, BYU
  Vertical Cloud Lab"). If using a public GitHub Discussion on
  [CadQuery/cadquery](https://github.com/CadQuery/cadquery) instead, drop the
  call request and ask the technical question asynchronously so community
  members can weigh in too.
  - **Discord server:** the CadQuery community lives on a server named
    **"Python OCP CAD"** (not "CadQuery", which is why it's hard to find).
    Permanent invite, verified valid 23 Jul 2026 via Discord's public invite
    API (~1,580 members, lands in the `#cadquery` channel):
    <https://discord.com/invite/Bj9AQPsCfx> (posted by maintainer Jeremy
    Wright in [CadQuery/cadquery#1680](https://github.com/CadQuery/cadquery/issues/1680)).
    Adam's exact Discord username is not published anywhere; after joining,
    search the member list for "adam". If he isn't findable there, don't wait —
    use GitHub instead.
  - **GitHub (reliable):** he is active as
    [@adam-urbanczyk](https://github.com/adam-urbanczyk) (reviewing CadQuery
    PRs as recently as 19 Jul 2026). Best public channel: open a
    [GitHub Discussion](https://github.com/CadQuery/cadquery/discussions) with
    the async version of the draft. `info@cadquery.org` (from the CadQuery
    README) reaches the core maintainers by email, though it's framed for
    consulting inquiries.
  - **LinkedIn:** profile at
    <https://www.linkedin.com/in/adam-urba%C5%84czyk-82511251> (Adam
    Urbańczyk, ASML, Netherlands) matches his FOSDEM bio (applied physicist,
    PhD TU Eindhoven, algorithms engineer at a Dutch semiconductor equipment
    vendor). Fine as a fallback connect-with-note, but he's far more active on
    GitHub.

---

## 1. Jesse Barkley (cc Amir Barati Farimani) — compare notes on CADSmith

**To:** Jesse Barkley `<jabarkle@andrew.cmu.edu>`
**Cc:** Amir Barati Farimani `<afariman@andrew.cmu.edu>`; Sterling Baird
**Subject:** CADSmith on BYU powder-doser parts

Hi Jesse,

I'm Luke Winters, a researcher in Dr. Sterling Baird's Vertical Cloud Lab at
BYU (cc'd). We build an open-source powder doser for metal-AM workflows
(https://github.com/vertical-cloud-lab/powder-doser), generating most of our
CAD with LLM pipelines — which led us to CADSmith.

We've run CADSmith on real parts: two of our printed plates converged on the
first iteration, within ~1 % of our hand-authored CadQuery references by
volume (https://github.com/vertical-cloud-lab/powder-doser/pull/59).

Would you and Prof. Farimani be open to a 30-minute call to compare notes on
our CADSmith results and assembly-level generation?

Best,
Luke Winters
Vertical Cloud Lab (PI: Dr. Sterling Baird), Brigham Young University

---

## 2. Adam Urbanczyk — robust LLM-generated CadQuery

**To:** Adam Urbanczyk (Discord DM preferred — see routing notes)
**Subject / Discussion title (not needed for a DM):** Robust LLM-generated CadQuery: advice from a BYU project

Hi Adam,

I'm Luke Winters from Dr. Sterling Baird's Vertical Cloud Lab at BYU. CadQuery
is the backbone of our open-source powder doser
(https://github.com/vertical-cloud-lab/powder-doser): most of our CadQuery
code is LLM-generated and human-reviewed, including a parametric assembly
gated by programmatic interference checks
(https://github.com/vertical-cloud-lab/powder-doser/pull/112).

Would you be open to a short call or async exchange about making LLM-written
CadQuery more robust — particularly the API idioms generators should favor
and common OCCT failure modes?

Thanks for maintaining CadQuery — it's been essential to this work.

Best,
Luke, BYU Vertical Cloud Lab

---

## 3. Jessie Frazelle — Zoo Text-to-CAD for metal-printing research

**To:** Jessie Frazelle (address from the lab Slack thread — see routing notes)
**Cc:** Sterling Baird
**Subject:** Zoo Text-to-CAD for BYU metal-printing research

Hi Jessie,

I'm Luke Winters from Dr. Sterling Baird's Vertical Cloud Lab at BYU —
Sterling mentioned this in a short LinkedIn note in May. We build an
open-source powder doser for automated metal 3D printing
(https://github.com/vertical-cloud-lab/powder-doser), and we used Zoo's
Text-to-CAD API to generate KCL and STEP files for all eleven printed parts
(https://github.com/vertical-cloud-lab/powder-doser/pull/110).

We'd like to see whether there is a useful fit for an academic collaboration
on design for automated metal 3D printing. One possible project is
benchmarking Text-to-CAD on manufacturability-constrained parts; we have
specifications, reference CAD, and printed hardware for evaluation.

Would you be open to a 30-minute call in the next few weeks?

Best,
Luke Winters
Vertical Cloud Lab (PI: Dr. Sterling Baird), Brigham Young University
