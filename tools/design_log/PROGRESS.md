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
| 2026-11-17 | Claude ([run](https://github.com/vertical-cloud-lab/powder-doser/actions/runs/44167457665)) | in progress | — | Inventory of Oct–Nov threads below; drafting in parallel by thread group. |

## Threads with activity since 2026-10-01

Status: `todo` · `drafting` · `done` · `skipped (reason)`.

| Group | Thread | Topic | Status |
| --- | --- | --- | --- |
| single-doser | PR #170 | Current-design render; re-render with Fusion parts | drafting |
| single-doser | Issue #177 | Centering device | drafting |
| single-doser | Issue #191 | Manufacturing design reviews | drafting |
| single-doser | Issue #193 | Current CAD and print specs (10/2026) | drafting |
| single-doser | Issue #203 | New tap collar / solenoid setup | drafting |
| single-doser | main 8284d63, dfaf8ca, 046d099 (2 Oct) | Gerber for the single-doser PCB | drafting |
| build-prints | PR #181 | New dosers: print plan, inventory, build order | drafting |
| build-prints | Issue #197 / PR #200 | Assembly prints with new files only | drafting |
| multi-doser | Issue #128 | Multi-doser design (from 1 Oct) | drafting |
| multi-doser | PR #185 | Chain carousel v2, vertical twin-chain test rig | drafting |
| multi-doser | PR #188 | CalculiX FEA of carousel parts | drafting |
| multi-doser | Issue #202 | Linear actuator selection | drafting |
| multi-doser | Issue #204 | Fixed multi-auger design | drafting |
| multi-doser | PR #115 | BOM, carousel parts list and mechanism panel (from 1 Oct) | drafting |
| cad-tooling | Issue #171 | Fusion 360 agent mode | drafting |
| cad-tooling | Issue #172 / PR #176 | text-to-cad recreation, servos-above variant | drafting |
| cad-tooling | PR #178 | fsgen: servos-above baseplate as an Onshape tree | drafting |
| cad-tooling | Issue #158 | Digital-twin environments (from 1 Oct) | drafting |
| sim-powder | PR #180 | DEM digital twin, micro-auger geometry sweep | drafting |
| sim-powder | PR #196 | Physics-based simulation survey and runs | drafting |
| sim-powder | Issue #163 | Powder property characterization (from 1 Oct) | drafting |
| sim-powder | PR #190 | Animated walkthroughs of powder-property tests | drafting |
| sim-powder | PR #205 | In-house powder-property tests on the doser | drafting |
| sim-powder | Issue #159 | Medical / drug-discovery applications | drafting |
| control | PR #131 | Data collection (from 1 Oct) | drafting |
| control | PR #166 | Optimization campaign (after e127) | drafting |
| control | PR #124 | Optimization problem (from 1 Oct) | drafting |
| control | PR #154 | Trim method (after e125) | drafting |
| control | Issue #117 | University of Utah testing (from 1 Oct) | drafting |
| control | Issue #179 | Optimization draft | drafting |
| control | Issue #186 | Dosing for atomizer runs | drafting |
| control | Issue #210 | Data assimilation project | drafting |
| control | Issue #144 | Usage instructions | drafting |
