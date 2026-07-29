# Merge Strategy for `powder-doser` (issue #137)

**Snapshot date:** 2026-07-29.
**Data basis:** full GitHub API download (133 issues/PRs, 1,197 issue comments, 292 inline PR review
comments, 130 PR reviews — including "hidden"/collapsed ones), all 64 remote branches fetched and
diffed against `main` (165 commits, 213 files). Machine-readable companions in this directory:
[`inventory.md`](inventory.md), [`branch-git-state.json`](branch-git-state.json),
[`tree-main.txt`](tree-main.txt).

---

## 1. Executive summary

- **38 open PRs.** 28 merge git-clean into `main` today; 10 conflict, and in 9 of those the *only*
  conflict is `README.md` (every branch appended its own section to the same README). The 10th
  (`#76`) conflicts only on two `paper/background/` READMEs.
- The real blockers are not git conflicts. They are: (a) **duplicate/competing directories**
  (#49/#68, #53/#55, #57/#63/#66, #61/#100, #107/#110/#112, #131/#136 pairs write to the same
  paths); (b) **huge regenerable binaries** (an 83 MB STEP on #66, 13–27 MB STEPs on #49/#107,
  ~42 MB of meshes on #110); (c) **unresolved reviewer feedback** on a handful of branches; and
  (d) a three-way **`paper/background/` numbering collision** (three PRs all claim note `15-`).
- **Verdict distribution:** 5 merge-now, 16 refresh-then-merge, 4 merge-subset, 7 park, 6 close.
  Plus 5 orphan `claude/issue-*` branches worth turning into PRs, 2 orphan branches to delete, and
  2 closed PRs with salvageable content (#83, #103).
- Recommended approach: **six merge waves** (§4), each executable by pasting the corresponding
  `@claude` prompt from §6 onto the relevant PR, plus three one-time repo-hygiene actions (§5)
  that eliminate the classes of conflict rather than resolving them one at a time.

## 2. Why PRs stopped merging (root-cause patterns)

1. **README-as-index anti-pattern.** `main`'s README is a 342-line append-log; nearly every branch
   adds its own section, so any two branches conflict with each other and with `main`. Fix once
   (§5.1) and 9 of the 10 conflicting PRs become trivial.
2. **Regenerable exports committed to git.** STEP/STL/GLB/OBJ files that a committed script can
   regenerate are the bulk of several PRs (repo is already 383 MB). A stated size policy (§5.2)
   unblocks #49, #66, #107, #110 without losing provenance.
3. **Experiments and products share namespaces.** Tool-comparison experiments (zoo.dev vs CADsmith
   vs Copilot) were pointed at the *same* output directories as the production design, so the
   experiment arms collide with each other. Namespacing convention in §5.3.
4. **Sessions that never opened a PR.** Nine `claude/issue-*` branches hold finished docs/data
   with no PR — work that is invisible unless someone remembers the branch name.
5. **No "definition of merged".** Long-running PRs (#7, #76, #97, #124, #131) became living
   workspaces; nothing was ever declared done. The waves below split "archive the record now"
   from "keep iterating".

## 3. One-by-one assessment

Verdict key: **MERGE-NOW** (mergeable as-is or after a trivial rebase) · **REFRESH** =
refresh-then-merge (bounded checklist, then merge) · **SUBSET** = merge after pruning listed
content · **PARK** (keep open, do not merge yet — blocked on humans/hardware/decision) ·
**CLOSE** (superseded or abandoned; close with a pointer).

### 3.1 Open PRs

| PR | Branch | Verdict | Key facts / required actions |
|----|--------|---------|------------------------------|
| #7 meta-CAD tools | `copilot/explore-meta-tools-for-cad` | **SUBSET** | Tool-evaluation docs/scoreboard/scripts under `cad/meta-tools/` are durable and repeatedly cited; the Zoo-generated `design/cad/full-system-*` geometry (incl. 5.5 MB `.bin`) is stale (Zoo subscription cancelled 2026-07-17) and superseded by later design lineage. Merge evaluations; drop geometry + logs; fix 2026-04-24 inline nits. |
| #11 commercial dispensing landscape | `copilot/search-commercial-powder-dispensing-solutions` | **REFRESH** | 51-platform landscape + 40-image mosaic, actively extended at sgbaird's request through 2026-07-21. Only README conflict + provenance nits (bare-domain `source_page` entries, Acrison model label, EDC ng-scale contradiction). |
| #23 Bambu H2D/A1-mini programmatic printing | `copilot/programmatic-access-bambu-h2d` | **REFRESH** | Most hardware-validated PR in the repo (first successful programmatic A1-mini print 2026-07-27); lab members use it from the branch URL. Only README conflict. Merge promptly — it gains commits almost daily. |
| #33 commercial quote survey | `copilot/get-quotes-for-powder-dosing` | **MERGE-NOW** | 4 files, +238 lines, conflict-free; only bot nits outstanding (remove an @-mention, spelling consistency — fine post-merge). |
| #35 single-channel module CAD | `copilot/modular-single-channel-powder-doser-design` | **PARK** | v2/v3 were judged mechanically broken by swcharles; v4 (2026-05-13) was never human-reviewed. Also carries two ~4.5 MB base64 Edison payloads. Blocked on human re-review, not on an agent. |
| #37 channel-sealing caps | `copilot/design-channel-sealing-cap` | **PARK** | swcharles's "try each of them again" is outstanding; last commit is literally "Changes before error encountered" (crashed session). A manual rubber-stopper workaround exists. |
| #41 powder-dispensing outreach contacts | `copilot/determine-helpful-individuals-organizations` | **REFRESH** | sgbaird bumped it three times and told the team to use it. Needs rebase, cross-link fixes to #43, and a numbering decision vs #76. |
| #43 generative-CAD outreach contacts | `copilot/determine-helpful-contacts` | **REFRESH** | Actively driving real outreach (sgbaird posted final email wording 2026-07-27 — not yet in the committed drafts; his 07-21 "who has been contacted already" tracking ask is unmet). `06-` collides with main's existing `06-` note. |
| #45 electrical/software brainstorm + satellite PCB | `copilot/brainstorming-electrical-software-systems` | **CLOSE** | sgbaird 2026-07-21: "Not sure if we need this PR anymore, superseded by #76?" — nobody disagreed. Cherry-pick the brainstorm MD into #76/main only if wanted. |
| #47 auger bracket (part-by-part) | `copilot/part-by-part-powder-doser` | **PARK** | All feedback addressed, but PR #112's assembly re-implements the bracket; merging both creates two sources of truth. Blocked on the standalone-parts vs #112-assembly decision. |
| #49 geared auger family | `copilot/add-new-auger-design` | **SUBSET** | Provenance for the physically printed auger family. Must fix the **nozzle-1/2 file swap** (Sam: "the actual files it gave are swapped") and drop/LFS three 13.7–20.4 MB regenerable STEPs. **Merge before #68** (reverse order produces add/add conflicts on 29 files). |
| #51 tap collar | `copilot/design-tap-collar` | **REFRESH** | Printed and "work great"; the 2026-06-10 solenoid-reorientation fix was committed but never human-verified. Verify, rebase, merge; then refresh #66's vendored copy. |
| #53 auger bracket via zoo.dev | `copilot/design-bracket-for-auger` | **CLOSE** | The zoo.dev experiment it was opened for was never actually run (hand-authored OpenSCAD); geometry superseded by #47's bracket; collides file-for-file with #55. |
| #55 auger bracket via CADsmith | `copilot/design-simple-bracket-cadsmith` | **PARK** | Also not real CADsmith output; swcharles's "complete the original tasks" ask unmet. Keep only if the CADsmith run is actually performed (pattern proven in #59), in a namespaced dir. |
| #57 mounting plate assembly v1 | `copilot/design-mounting-plate-for-powder-doser` | **CLOSE** | Literal git ancestor of #66 — every commit is contained in #66. Close with a pointer. |
| #59 mounting plate via CADsmith | `copilot/design-mounting-plate-cadsmith` | **PARK** | Geometry obsolete (linear actuator abandoned), but this is the only real end-to-end CADsmith run (incl. upstream patches) — keep as the experiment record; optionally extract `run_cadsmith.py` + artifacts later. |
| #61 test-module electronics v1 | `copilot/set-up-test-module-electronics` | **CLOSE** (after salvage) | Superseded by #100 except two commits (continuous-rotation `g [rpm]` + haptic RTP, 2026-06-23) that #100 lacks — port those onto #100 first (keymap conflict: `g` = dose there). |
| #63 mounting plate (offset hinge) | `copilot/design-mounting-plate` | **CLOSE** | Zero discussion ever; contradicts the adopted hinge-axis invariant; superseded by #57→#66 lineage. |
| #66 dual-servo mounting plate | `copilot/add-servo-angle-control` | **REFRESH** | The design that physically exists (poster + built hardware). Blockers: williamulbz's 2026-06-29 gear-module ask is unanswered (ambiguous vs the 06-27 recut — needs his decision), and `assembly/full_assembly.step` is **83 MB** (near GitHub's hard limit) + a 13 MB plate STEP — prune before merge. Closes #57/#63 alongside. |
| #68 auger exit-path fix | `copilot/fix-geared-auger-exit-hole` | **REFRESH** (after #49) | Its output STL is **byte-identical to `Auger4.stl` on main** ("Main Design") — this branch is the only parametric source of the production auger. All reviewer asks addressed. Merge right after #49; update the README it never touched. |
| #70 OCP CAD Viewer assessment | `copilot/explore-ocp-cad-viewer-extension` | **MERGE-NOW** | Docs-only, 2 files, conflict-free, zero objections in 2.5 months. |
| #74 DESIGN-LOG record of designs | `copilot/record-of-designs` | **REFRESH** | sgbaird's asks all done ("nice"); log stops 2026-05-28 — needs a 2-month catch-up (Tic bring-up, dual-servo, scale loop, PCB campaign) and two README conflict fixes (three-way with #76 on `edison_artifacts/README.md`). |
| #76 generative PCB campaign | `copilot/literature-search-generative-pcb-design` | **REFRESH** | Core paper material, active 2026-07-29. Must be closed out with reality: williamulbz's hand-designed EasyEDA board was ordered 2026-07-28 (sgbaird's ask to commit its source files is **still open**), and the branch's JLCPCB kit must be marked superseded/do-not-order. Two README add/add conflicts. |
| #78 conference abstracts | `abstracts/utah-ai-2026` | **MERGE-NOW** | ~15 review rounds, every ask applied, merge-clean. Deadlines passed → this is the archival record of what was submitted. |
| #81 auger capacity model | `copilot/measuring-auger-volume` | **REFRESH** | Validated <1% vs STL, answers the still-live 250 mL sizing question, but constants reference #49's branch — land after #49/#68 and re-run `--validate`. |
| #86 battery power options | `copilot/battery-power-possibilities` | **REFRESH** | 1 file, +49 lines. Record the real outcome (Tripp Lite UPS ordered 2026-06-15) and renumber (three PRs claim `15-`). |
| #91 journal/venue scouting | `copilot/determine-journals-editors-reviewers` | **MERGE-NOW** | Completed sgbaird's fetch-summarize-report ask same-day (2026-07-29); merge-clean; its notes `15–20` should win the numbering race — merge first among `paper/background/` PRs. |
| #93 Zoo Design Studio notes | `copilot/zoo-design-studio-multi-doser` | **REFRESH** | Content complete, sgbaird positive; renumber `15-`/`23-` after #91 lands; the swcharles/williamulbz read he requested never happened (note it, don't block on it). |
| #97 Digital Discovery manuscript | `copilot/draft-base-manuscript` | **PARK** | The canonical, actively-worked manuscript workspace (Edison fetch in flight; sgbaird carrying #103's work back over). Not mergeable until real bench data replaces the watermarked synthetic figures; also a 5.6 MB `mock_review.task.json` to prune. Keep open as workspace. |
| #100 closed-loop scale dosing | `copilot/integrate-scale-feedback-loop` | **REFRESH** | **Highest-value merge in the repo.** Bench-validated firmware ("first tests of our main function are working", demo videos). main's 2-file `hardware/test-module` snapshot is an older broken cut — branch wins the add/add. Port #61's two salvage commits, move the root transcript file, close out 8 Copilot inline comments. |
| #105 comparison prompt | `copilot/powder-doser-prompt-iteration` | **MERGE-NOW** | The canonical prompt behind the whole #106–#112 experiment; both sgbaird asks addressed same-day; conflict-free. |
| #107 spec assembly (Copilot arm) | `copilot/design-powder-dispensing-system` | **SUBSET** | De facto reference geometry (sgbaird directed #115's filament calc at it; matched Sam's hand calc). Prune ~50 MB of regenerable STEPs (26.6 MB assembly + 8–9 MB parts), keep the canonical `cad/powder-doser-assembly/` path. |
| #110 spec assembly (zoo.dev arm) | `copilot/design-powder-dispensing-system-again` | **SUBSET** | KCL sources + prompts + manifests are the irreplaceable zoo.dev record; OBJ/GLB/STEP meshes (~42 MB) are regenerable. Re-path to `cad/powder-doser-assembly-zoo/`. |
| #112 spec assembly (2nd CadQuery arm) | `copilot/design-powder-dispensing-system-another-one` | **REFRESH** | Lean (5.8 MB), good hygiene, but it was supposed to be the CADsmith arm and isn't — flag to sgbaird; re-path to `cad/powder-doser-assembly-cadquery-alt/` (or re-run with CADsmith). |
| #115 bill of materials | `copilot/vertical-cloud-labpowder-doser-114-bill-of-materia` | **REFRESH** | The team literally purchased hardware from this document (parts arriving 2026-07-28). README conflict; move the 7.75 MB vendor STEP off repo root into `hardware/vendor-files/`; record final ordering decisions. |
| #124 optimization problem definition | `claude/issue-123-20260707-1841` | **PARK** | Healthy live research hub (williamulbz, sgbaird, XZaitzeff active). `main_three_phase.py` imports modules that exist only on #100's branch — must merge #100 first; control-direction decision (MPC vs rate-PI) deliberately open. |
| #131 data collection for optimization | `claude/issue-130-20260721-1807` | **REFRESH** | Canonical data-collection line: real PID dose telemetry committed 2026-07-29; commit-hash links cited across issues. Answer sgbaird's 07-24 material-labeling ask; decide on 4.5k-line raw logs; note the angle-sweep run is still outstanding. |
| #136 characterization sweep (Copilot fork) | `copilot/add-on-device-characterization-sweep` | **CLOSE** | Zero original work — a ping-workaround fork of #131 whose one Claude run errored; #131 has since advanced past it. Close + delete branch. |

### 3.2 Closed-but-unmerged PRs

| PR | Disposition | Notes |
|----|-------------|-------|
| #5 bimodal compliant mechanism | LEAVE | Design direction abandoned; branch is the archive (incl. 14 Edison reports). |
| #13 alternative dosing concepts | LEAVE | Vertical auger won; brainstorm + Edison critique stay on the branch. |
| #18 Marp wrap-up deck | LEAVE (don't delete branch) | sgbaird deferred "another few months"; the Pages deploy builds **from this branch**. |
| #79 Copilot responder Action | LEAVE | Superseded by claude.yml; branch already deleted. |
| #83 flux.ai probe | **SALVAGE** | Cherry-pick the two `paper/background/` files (they record *why* Flux was rejected), then delete branch. |
| #89 issue-87 test workflow | LEAVE | Branch already deleted; context lives in comments. |
| #103 manuscript duplicate | **SALVAGE** | sgbaird 2026-07-29: "Carrying work back over to #97." Port `paper/conference_poster/` + the no-placeholder/Fig-1a fixes into #97, then delete branch. |

### 3.3 Orphan branches (no PR — invisible work)

| Branch | Disposition | Contents |
|--------|-------------|----------|
| `claude/issue-117-20260702-2152` | **OPEN-PR** (combined) | Edison reports: AIBN, Grubbs G2, NaCN dosing properties. |
| `claude/issue-117-20260716-1601` | SALVAGE into combined PR | Keep `powder-pricing-2026-07.md` only. |
| `claude/issue-117-20260716-1642` | **DELETE** | Fully superseded by `…0717-0919`. |
| `claude/issue-117-20260717-0919` | **OPEN-PR** (combined) | PLA-compatibility + surrogate-powders Edison results — most valuable of the four. |
| `claude/issue-121-20260702-2151` | **OPEN-PR** | `BUILD-INSTRUCTIONS.md` — swcharles explicitly plans to edit it with real build experience. |
| `claude/issue-126-20260709-1827` | **OPEN-PR** | Scale data-streaming design; sgbaird 07-26: ready to explore now that Tailscale+MongoDB exist. Add an as-built caveat vs #131. |
| `claude/issue-127-20260715-1610` | **OPEN-PR** | Tailscale remote-access setup doc — the human-facing procedure exists nowhere on main. |
| `claude/issue-130-20260721-1909` | **DELETE** | Fully superseded by PR #131's branch. |
| `claude/issue-132-20260723-2140` | **OPEN-PR** | Pi Wi-Fi/NetworkManager change record — exactly what CLAUDE.md requires to be in-repo. |

### 3.4 Open issues with no PR (context for prioritization)

Candidates to close as overtaken: #3, #4, #12, #17, #64, #88 (fold into #116), #101 (event passed),
#102 (module working in #100), #113, #119, #135. Good agent-run candidates: #84 (ESD/grounding
Edison query), #87 (systematize circuit verification), #121/#126 (via the orphan branches above),
#128 (multi-doser concept CAD). Hardware/human-blocked: #109, #116, #120, #125, #129, #134.
Active tracking hubs: #72, #92, #94, #95, #117, #122, #132, #133.

## 4. Merge waves (recommended order)

Order matters: #91 claims `paper/background/` numbering; #49 must precede #68; #100 must precede
#124's eventual merge; #107 claims the canonical assembly path before #110/#112 re-path.

- **Wave 0 — one-time hygiene (unlocks everything):** README de-confliction, binary policy,
  namespace convention, numbering registry (§5). ~1 agent session.
- **Wave 1 — clean + complete (no conflicts, feedback done):** #91 → #78 → #105 → #70 → #33.
  These five can land the same day.
- **Wave 2 — production hardware lineage:** #49 (subset) → #68 → #51 → #66 (prune 83 MB STEP;
  needs williamulbz's gear-module answer) → close #57, #63.
- **Wave 3 — firmware and data:** port #61 salvage commits onto #100 → merge #100 → close #61 →
  merge #131 → close #136 (+ delete its branch and `claude/issue-130-20260721-1909`).
- **Wave 4 — research/docs corpus:** #115 → #11 → #23 → #41 → #43 → #86 → #93 (renumbered after
  #91) → #74 (with 2-month catch-up) → #76 (with EasyEDA close-out) → #81 (after #49/#68) →
  #7 (subset).
- **Wave 5 — experiment archive:** #107 (subset, canonical path) → #110 (re-pathed) → #112
  (re-pathed, pending sgbaird's CADsmith-arm call) → close #53 → decide #55/#59 (park or extract).
- **Wave 6 — orphan salvage:** combined issue-117 PR; PRs from issue-121/126/127/132 branches;
  cherry-pick #83's two files and #103's poster into #97; delete the two dead branches.
- **Deliberately parked (do not merge, do not close):** #97 (until real bench data), #124 (until
  #100 merges + control-direction decision), #35 (until human re-review of v4), #37, #47, #55, #59.

## 5. One-time repo hygiene (Wave 0)

1. **Kill the README conflict machine.** Shrink `README.md` to a short overview + a table of
   pointers, and move the append-log content into `docs/` pages. Nine of ten conflicting PRs then
   rebase trivially (their README hunk becomes a one-line pointer). Prompt in §6.1.
2. **Binary/export policy.** Adopt: no regenerable export >5 MB in git; `exports/step/`, `*.glb`,
   `*.obj` gitignored when a committed script regenerates them; README documents the regen command;
   vendor STEPs live in `hardware/vendor-files/`. Consider `git lfs` if large one-of-a-kind assets
   must stay. Prompt in §6.1.
3. **`paper/background/` numbering registry.** Main has 01–06 + 14; #91 wants 15–20, #76 wants
   07–14 (colliding with main's 14), #86/#93 both want 15, #41/#43 want 06–08. Add
   `paper/background/README.md` with an authoritative claimed-numbers table; every future note
   claims the next free slot there. Prompt in §6.1.
4. **Experiment namespace convention.** Tool-comparison arms live in
   `cad/<thing>-<tool>/` (e.g. `-zoo`, `-cadsmith`); the adopted design owns the bare path.

## 6. Specific Claude prompts

Copy-paste these as `@claude` comments at the indicated points. They assume the repo's existing
workflow (issue/PR comment → Claude Action). Where a prompt says "close X", a maintainer click is
still needed if Claude lacks permission — the prompt has Claude prepare the closing comment.

### 6.1 Wave 0 — one-time hygiene (post on a fresh issue)

> @claude Restructure the repository to eliminate our recurring merge blockers, in one PR:
> 1. Shrink README.md to a ~60-line overview: project summary, one hero image, and a pointer table
>    (Design → docs/design-index.md, Hardware → docs/hardware-index.md, Research →
>    paper/background/README.md, Operations → docs/operations-index.md). Move every existing README
>    section verbatim into the appropriate docs/ page — do not lose content. Future PRs must add
>    one pointer line, not a section.
> 2. Add a "Repository conventions" section to CLAUDE.md: (a) never commit regenerable exports
>    >5 MB (STEP/STL/GLB/OBJ) — gitignore them and document the regeneration command in the
>    directory README; (b) vendor part models go in hardware/vendor-files/; (c) tool-comparison
>    experiments use suffixed dirs (cad/<part>-zoo/, cad/<part>-cadsmith/) — the adopted design
>    owns the bare path; (d) every agent session that produces commits must end with an open PR —
>    never leave work on a branch without one; (e) paper/background/ note numbers must be claimed
>    in paper/background/README.md's registry table before use.
> 3. Create that paper/background/README.md registry: list existing notes 01–06 and 14, and
>    reserve: 07–13 → PR #76, 15–20 → PR #91, 21 → PR #86, 22–23 → PR #93, next-free → PR #41/#43
>    renumbers. Open a PR titled "chore: README de-confliction + repo conventions".

### 6.2 Wave 1 — clean merges (post on each PR)

On **#91**, **#78**, **#105**, **#70**, **#33** (individually):

> @claude This PR was assessed as merge-ready (issue #137). Rebase onto latest main, confirm the
> merge is conflict-free, mark ready-for-review if draft, verify no file >5 MB and no secrets in
> any committed artifact, and post a one-paragraph merge summary (what lands where, which issue it
> closes). Do not add new content.

### 6.3 Wave 2 — hardware lineage

On **#49**:

> @claude Prepare this PR for merge per issue #137: (1) fix the nozzle Type 1/Type 2 file swap Sam
> reported on 2026-05-28 — swap the file contents (or names) so files match the documented
> definitions, and note the fix in the README; (2) delete the three 13–20 MB regenerable STEP files
> under exports/storage-auger/step/ (keep stl_to_step.py + provenance JSONs, document the regen
> command); (3) add the consolidated per-version dimension list swcharles requested on 2026-06-18;
> (4) rebase onto main. Reply listing anything you could not resolve. This PR must merge BEFORE #68.

On **#68** (after #49 merges):

> @claude #49 has merged. Rebase this branch onto main and confirm the 29 shared cad/auger-geared/
> files resolve cleanly (this branch's exit-path-fixed versions win). Update cad/auger-geared/
> README.md to document the exit-path fix (taper + phase-continuous fin), and add a provenance note
> linking main's root Auger4.stl to archimedes-auger-geared.scad (they are byte-identical — this
> branch is its source). Regenerate renders, then report merge-readiness.

On **#51**:

> @claude Rebase onto main and regenerate STEP/STL/renders. Then post a short verification report
> of the 2026-06-10 solenoid reorientation (plunger axis perpendicular to auger, 3.0 mm extended
> interference) with a cross-section render, and tag @swcharles and @williamulbz asking for a
> print-test sign-off — that fix was never human-verified. Note that issue #64 (solenoid impulse)
> may still change this mount.

On **#66**:

> @claude Prepare for merge per issue #137: (1) delete assembly/full_assembly.step (83 MB) and
> step/mounting_plate.step (13 MB) — gitignore them, keep the Onshape links as the heavy-viewing
> path, and document the regeneration command; (2) reply to @williamulbz's 2026-06-29 gear-teeth
> comment with the analysis: the 06-27 recut already increased module 0.908→1.298 (+43%); going
> 15–30% above 1.298 at the fixed 27.25 mm center distance requires a <14-tooth pinion, which the
> digital twin rejected — ask him to confirm whether the recut satisfies his ask or whether we
> change center distance / go PA6-CF; (3) evaluate integrating his zoo-made countersunk servo
> pinion STL from 2026-06-10 or record why not; (4) refresh the vendored imported-parts/ snapshots
> from the merged heads of #49 and #51; (5) rebase, re-run digital_twin.py, recommit the report.
> Also draft closing comments for #57 (every commit is contained here) and #63 (superseded, zero
> review activity).

### 6.4 Wave 3 — firmware and data

On **#100**:

> @claude Prepare the bench-validated firmware for merge per issue #137: (1) rebase onto main;
> for the hardware/test-module/firmware/main.py add/add conflict, take THIS branch's 585-line
> version (main's 425-line copy is an older snapshot with no unique delta — verify that claim with
> a diff before discarding); (2) port the continuous-rotation + haptic-RTP feature from #61's
> commits a385b23/959fa76, remapping its 'g [rpm]' key since 'g' means dose-grams here; (3) move
> the root-level 2026-07-07 session transcript into hardware/test-module/docs/ or delete it;
> (4) address the 8 Copilot inline review comments from 2026-06-14 — especially the hash()-derived
> non-reproducible UUIDs in generate.py and dosing.py's read_stable() returning a possibly-unstable
> reading on timeout; (5) document how main.py relates to #124's main_three_phase.py. Then post a
> merge summary and a draft closing comment for #61 pointing here as successor.

On **#131**:

> @claude Prepare for merge per issue #137: (1) merge origin/main into this branch (8 commits,
> workflow-only); (2) address sgbaird's 2026-07-24 ask — edit the earlier dose-run comments with
> "EDIT: material was …" labels, and add a materials table to
> docs/characterization-data-collection.md; (3) post the final report for the 2026-07-29 PID runs
> (plots are committed but were never surfaced in a comment); (4) either delete the 4,500-line raw
> .log files (CSVs + MongoDB carry the data) or justify keeping them; (5) state explicitly that the
> issue-#130 angle-sweep characterization run is still outstanding so the issue stays open after
> merge. Also draft a closing comment for #136 (a ping-workaround fork with zero unique commits)
> and note that branches copilot/add-on-device-characterization-sweep and
> claude/issue-130-20260721-1909 can be deleted.

### 6.5 Wave 4 — research/docs corpus (representative prompts)

On **#115**:

> @claude Prepare for merge: rebase and resolve the README.md conflict (keep a one-line pointer per
> the new README convention); move 34HS59-6004D-E1000.STEP from repo root to hardware/vendor-files/;
> append a "Final ordering decisions" section recording what was actually purchased per the thread
> (HR-100A via ceproducts, AD-1671 table, Sam's 262 g filament figure vs the 266 g estimate,
> DigiKey items pending as of 2026-07-28); mark ready-for-review.

On **#76**:

> @claude Close out this campaign for merge per issue #137: (1) resolve the two paper/background
> README add/add conflicts by merging main's CAD-pillar listings with this branch's PCB-pillar
> listings (coordinate with #74, which touches edison_artifacts/README.md too); (2) the board that
> was ACTUALLY ordered on 2026-07-28 is williamulbz's hand-designed EasyEDA board — ask him to
> attach the EasyEDA source (sgbaird's open 07-21/07-29 request), commit it under hardware/, and
> add a lessons-learned note recording swcharles's 07-17 physical findings (USB clearance, redundant
> connectors, mirrored Waveshare footprint) and marking the candidate_2_fixed JLCPCB kit as
> superseded — do-not-order; (3) renumber this branch's note 14 (main already has a different 14)
> per the registry; (4) resolve the four Copilot inline nits. Report anything blocked on humans.

On **#74**:

> @claude Refresh the DESIGN-LOG for merge: resolve the two README conflicts; then append entries
> for 2026-05-29 → today from the actual record — #61 Tic/dual-servo iterations, #66 dual-servo
> hinge + gear recut, #100 scale-feedback bring-up and bench debugging, #124 three-phase controller,
> #76 starter-board/Quilter rounds, the hand-designed EasyEDA board and PCB order, and the #131 PID
> dose runs — and re-run tools/design_log/build_design_log.py. Verify the 112 SHA-pinned image URLs
> still resolve; mirror any that point at branches slated for deletion.

On **#43** (and analogously #41, #86, #93, #11, #23, #81, #7):

> @claude Prepare for merge: renumber 06-generative-cad-outreach-contacts.md to the next free slot
> in the paper/background registry (main already has a 06-) and fix inbound links including from
> #41; update outreach/generative-cad-email-drafts.md to sgbaird's final 2026-07-27 wording and add
> the YouTube-video link + powder-doser photo he requested; add the "contacted so far" status table
> he asked for on 07-21 (include the 2026-05-20 Frazelle LinkedIn message); rebase and mark ready.

### 6.6 Wave 5 — experiment archive

On **#107**:

> @claude Prepare for merge as the canonical assembly per issue #137: gitignore exports/step/ and
> delete the committed 26.6 MB assembly STEP and >5 MB part STEPs (code, SPEC.md, README, PNGs
> stay; document `xvfb-run -a python3 build.py` as the regen path); rebase; mark ready. Note in the
> README that this is the Copilot/CadQuery arm of the #105 comparison and that #110/#112 hold the
> other arms in suffixed directories.

On **#110** / **#112**:

> @claude Re-path this experiment arm so it can coexist with #107 (which keeps
> cad/powder-doser-assembly/): move everything to cad/powder-doser-assembly-zoo/ [#112:
> cad/powder-doser-assembly-cadquery-alt/], fix internal links, drop regenerable OBJ/GLB meshes
> (keep KCL sources, prompts, manifests, renders) [#112: keep as-is, it's already lean], rebase,
> and mark ready. [#112 additionally: flag to @sgbaird that this arm was implemented in plain
> CadQuery rather than CADsmith as issue #111 requested — ask whether to archive it as-is or re-run
> with CADsmith.]

### 6.7 Wave 6 — orphan salvage (post on the issues)

On **issue #117**:

> @claude Three of your past sessions left finished work on branches without PRs. Create ONE PR
> from a new branch that combines: docs/edison-queries/issue-117/ from
> claude/issue-117-20260702-2152 (AIBN/Grubbs-G2/NaCN reports), the full contents of
> claude/issue-117-20260717-0919 (PLA-compatibility + surrogate-powders results), and just
> powder-pricing-2026-07.md from claude/issue-117-20260716-1601. Skip the PENDING marker file
> (obsolete) and skip claude/issue-117-20260716-1642 entirely (superseded — note it can be
> deleted).

On **issues #121, #126, #127, #132** (individually, adjusting branch name):

> @claude Open a PR from branch claude/issue-121-20260702-2151 (BUILD-INSTRUCTIONS.md). Rebase it
> onto current main first, add a header noting the as-built state it describes and the date, and
> in the PR body invite @swcharles to edit with real build experience as he planned.

On **#97** (salvage from #103 and #83):

> @claude Port the content sgbaird said to carry over from closed PR #103: cherry-pick
> paper/conference_poster/ and the no-placeholder/Fig-1a-legibility revisions onto this branch.
> Also cherry-pick the two paper/background flux.ai files from closed PR #83's branch (they record
> why Flux was rejected; claim a registry number). Then confirm both Edison tasks dispatched on
> 2026-07-29 have been fetched and their artifacts committed per CLAUDE.md. Do NOT touch the
> synthetic-data figures — those wait for real bench data.

### 6.8 Standing prompt for any future "stuck" PR

> @claude Assess this PR for merge-readiness: list every unresolved reviewer ask (check inline
> review comments via the API, not just the conversation), test-merge against main and enumerate
> conflicts, flag any file >5 MB or regenerable export, check whether another open PR touches the
> same paths, and finish with a verdict — MERGE-NOW / REFRESH (with checklist) / PARK (with what
> it's blocked on) / CLOSE (with why) — plus the exact @claude prompt a maintainer should post next.

## 7. What NOT to merge (explicit keep-out list)

- **#35, #37** — geometry judged broken/unreviewed; blocked on human re-review, not agent work.
- **#45, #53, #57, #61, #63, #136** — superseded; close with pointers (salvage noted above first).
- **#97, #124** — active workspaces; merging would freeze live collaboration and (for #97) publish
  synthetic-data figures; (for #124) land firmware with imports that only exist on #100's branch.
- **#5, #13, #18 branches** — abandoned directions; keep as archives (and #18's branch hosts the
  Pages deploy — do not delete).
- Multi-MB regenerable exports anywhere (83 MB STEP on #66, 26.6 MB on #107, ~42 MB meshes on
  #110, 13–20 MB on #49, 4.5 MB base64 task payloads on #35, 5.6 MB on #97) — prune before merge,
  regenerate from committed scripts.
