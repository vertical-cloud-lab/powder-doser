# DESIGN-LOG update tracker

Working record for bringing [`DESIGN-LOG.md`](../../DESIGN-LOG.md) up to date, kept so a
later session can pick up where an earlier one stopped. Update it in the same commit as
any change to the log.

## How to resume

1. Read this file, then the last few entries of `DESIGN-LOG.md` to match their style.
2. Take the next thread marked `todo` or `partial` in the table below, read its comments
   from the "covered to" date on, and draft entries in the existing format (ENTRY marker
   with `date=`, `pr=`, `sub=`; Trigger / Design / Rationale / image / Outcome).
3. Insert entries in date order, run `python3 tools/design_log/build_design_log.py`
   (then `--check`), check that new image URLs return HTTP 200, and commit.
   **Python (and Node) are blocked for `@claude` runs on this PR**, because the Claude
   app did not open it. Use the GNU awk port instead, which reproduces the Python
   output byte for byte (checked on 2026-11-17 against all 128 entries, including a
   rebuild from a copy with every anchor and generated block stripped):
   `LC_ALL=C gawk -f tools/design_log/build_design_log.awk DESIGN-LOG.md > /tmp/log.md && cp /tmp/log.md DESIGN-LOG.md`.
4. Mark the thread `done` (or `skipped`, with the reason) here and note the newest
   entry added under "Sessions".

Conventions for entries from June 2026 on (see "How to read this log" in the log):
people are "a team member" or "the AI agent (Claude/Copilot)", never names or handles;
images are only artifacts that already exist (SHA-pinned `raw.githubusercontent.com`
URLs for committed files, or the original `user-attachments` URL); write "about"
rather than a tilde; say "not reported" where the record is silent.

## Scope rules

- **In scope:** physical designs and their iterations (CAD, prints, assemblies),
  build changes, electronics, firmware and control methods, test methods and rig
  changes, simulations that inform the design, and design-tooling trials.
- **Out of scope:** manuscript and slide work (#97, #149, #150, #173, #174, #175,
  #184, #195, #209), onboarding docs (#198), and CI / workflow / `CLAUDE.md` PRs
  (#167–169, #182, #183, #187, #189, #192, #199, #201, #206–208, #212, #213) — unless
  one of them changed how parts are designed or made (e.g. `@claude-print` actually
  used to print doser parts).

## Sessions

| Date (UTC) | Session | Covered to | Entries | Notes |
| --- | --- | --- | --: | --- |
| 2026-06-06 | Copilot | 2026-05-28 | 97 | Original log (#73). |
| 2026-10-01 | Claude | 2026-10-01 | 128 | June–October entries e098–e128. |
| 2026-11-17 | Claude ([run](https://github.com/vertical-cloud-lab/powder-doser/actions/runs/44167457665)) | 2026-11-17 | 164 | 36 entries from five thread groups; multi-doser group still being drafted. Two new entries predate the old e128 (PCB v3 on 29 Sep, bulk-to-tap on 1 Oct), so the 1 Oct render is now e130. |

## Threads with activity since 2026-10-01

Status: `todo` · `drafting` · `done` · `skipped (reason)`.

| Group | Thread | Topic | Status |
| --- | --- | --- | --- |
| single-doser | PR #170 | Current-design render; re-render with Fusion parts | done (render v2, Onshape API assembly, fastener BOM/walkthrough) |
| single-doser | Issue #177 | Centering device | done (centering device v1, v2) |
| single-doser | Issue #191 | Manufacturing design reviews | done (review fixes; hinge-bolt nut inset) |
| single-doser | Issue #193 | Current CAD and print specs (10/2026) | done (Onshape recreations; print guidance v2) |
| single-doser | Issue #203 | New tap collar / solenoid setup | done (tapper concepts; solenoid bracket v1) |
| single-doser | main 8284d63, dfaf8ca, 046d099 (2 Oct) | Gerber for the single-doser PCB | done (Doser PCB v3; 8284d63/046d099 only add and delete a placeholder) |
| build-prints | PR #181 | New dosers: print plan, inventory, build order | done (mounting plate v1, v2; remote printing; 25-auger batch; build hardware) |
| build-prints | Issue #197 / PR #200 | Assembly prints with new files only | done (mounting plate v3) |
| multi-doser | Issue #128 | Multi-doser design (from 1 Oct) | drafting |
| multi-doser | PR #185 | Chain carousel v2, vertical twin-chain test rig | drafting |
| multi-doser | PR #188 | CalculiX FEA of carousel parts | drafting |
| multi-doser | Issue #202 | Linear actuator selection | drafting |
| multi-doser | Issue #204 | Fixed multi-auger design | drafting |
| multi-doser | PR #115 | BOM, carousel parts list and mechanism panel (from 1 Oct) | drafting |
| cad-tooling | Issue #171 | Fusion 360 agent mode | done (folded into the fsgen entry) |
| cad-tooling | Issue #172 / PR #176 | text-to-cad recreation, servos-above variant | done (text-to-cad recreation; servos-above v1, v2; native Onshape trees) |
| cad-tooling | PR #178 | fsgen: servos-above baseplate as an Onshape tree | done |
| cad-tooling | Issue #158 | Digital-twin environments (from 1 Oct) | skipped (literature only after 1 Oct; DEM moved to PR #180) |
| sim-powder | PR #180 | DEM digital twin, micro-auger geometry sweep | done (DEM twin; micro-auger sweep) |
| sim-powder | PR #196 | Physics-based simulation survey and runs | done (method survey; per-jar session plan) |
| sim-powder | Issue #163 | Powder property characterization (from 1 Oct) | done (flowability proxies) |
| sim-powder | PR #190 | Animated walkthroughs of powder-property tests | skipped (documentation, no adopted method) |
| sim-powder | PR #205 | In-house powder-property tests on the doser | done (in-house test concepts) |
| sim-powder | Issue #159 | Medical / drug-discovery applications | skipped (outreach and literature only) |
| control | PR #131 | Data collection (from 1 Oct) | done (folded into the replicate-validation entry) |
| control | PR #166 | Optimization campaign (after e127) | done (bulk-to-tap; validation; cutoff margin; fingerprint transfer) |
| control | PR #124 | Optimization problem (from 1 Oct) | skipped (ideas and literature, nothing built or run) |
| control | PR #154 | Trim method (after e125) | done (refill-tap endgame) |
| control | Issue #117 | University of Utah testing (from 1 Oct) | skipped (requirements questions for a co-dosing rig; no design yet) |
| control | Issue #179 | Optimization draft | skipped (paper draft) |
| control | Issue #186 | Dosing for atomizer runs | done (Al 4047 atomizer-cup dosing) |
| control | Issue #210 | Data assimilation project | skipped (data requests and literature; notes no temperature/RH logging) |
| control | Issue #144 | Usage instructions | done (print guidance v1) |

## Open items

- **Multi-doser group** (Issue #128 from 1 Oct, PR #185, PR #188, Issue #202, Issue #204,
  PR #115): drafting in this session; if the table above still says `drafting`, redo it.
  Issue #204 has many session branches (`claude/issue-204-*`) holding its renders.
- **New stand (fitted 2 Oct 2026):** back and side stand brackets, wood legs and a
  printed Base, designed only in a lab Onshape document. It is mentioned inside the
  Onshape-recreation and build-hardware entries but has no entry of its own. Sources:
  [PR #176 comment](https://github.com/vertical-cloud-lab/powder-doser/pull/176#issuecomment-6094125789)
  and a team member's 13 Oct explanation on PR #176.
- **Anchors moved once:** the old `#e128` (1 Oct render) is now `#e130`, because two
  entries dated earlier were added before it. Later updates should append only.
