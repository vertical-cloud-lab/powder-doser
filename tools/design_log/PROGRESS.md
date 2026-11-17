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
| 2026-11-17 | Claude ([run](https://github.com/vertical-cloud-lab/powder-doser/actions/runs/44167457665)) | 2026-11-17 | 183 | 55 new entries (e128–e183 except e130) from 33 threads; all threads below are `done` or `skipped`. |

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
| multi-doser | Issue #128 | Multi-doser design (from 1 Oct) | done (roller-chain multi-doser v3: the team's compact carriage) |
| multi-doser | PR #185 | Chain carousel v2, vertical twin-chain test rig | done (chain carousel v1–v9, paternoster, shared station) |
| multi-doser | PR #188 | CalculiX FEA of carousel parts | done (CalculiX FEA) |
| multi-doser | Issue #202 | Linear actuator selection | done (actuator selection) |
| multi-doser | Issue #204 | Fixed multi-auger design | done (fixed multi-auger doser v1–v4) |
| multi-doser | PR #115 | BOM, carousel parts list and mechanism panel (from 1 Oct) | skipped (only parts purchasing since 1 Oct) |
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

## Next update

Start from comments after **2026-11-17 20:00 UTC**. Threads that were still moving then:

- PR #185: chain carousel v9 posted 17 Nov, no reply yet.
- Issue #204: fixed multi-auger doser v4, clevis-block holes dimensioned 17 Nov.
- PR #181 / PR #200: doser #1 assembly waiting on six bought parts; two augers printing
  on the H2D on 17 Nov.
- Issue #203: plate-mounted solenoid bracket v1, no print yet.
- Issue #191: hinge-bolt nut inset decided 10 Nov, no revised plate linked yet.
- Also re-run the inventory query for new threads
  (`gh api "repos/vertical-cloud-lab/powder-doser/issues?state=all&since=<date>"`) and the
  GraphQL branch query for `claude/issue-*` session branches that have no PR.

## Notes for reviewers

- **Anchors moved once:** the old `#e128` (1 Oct render) is now `#e130`, because two
  entries dated earlier (Doser PCB v3, bulk-to-tap) were added before it. Later updates
  should append only.
- **Naming:** PR #185's carousels keep the PR's own labels (chain carousel v1–v9). The
  team's compact electronics carriage of 8 Oct continues the older chain as roller-chain
  multi-doser v3. Doser PCB v3 is the 29 Sep Gerber, which the team still files as "V2".
- **No image:** entries for work that lives only in lab Onshape documents (centering
  device, solenoid bracket, review fixes, hinge-nut inset, PCB v3) have no render, since
  nothing was committed or attached.
- **Approximate time:** the stand entry's time of day comes from livestream frames.
- **Checks run (2026-11-17):** every image URL in the new entries returned HTTP 200, and
  every `issuecomment` link resolved to the issue or PR it names.
