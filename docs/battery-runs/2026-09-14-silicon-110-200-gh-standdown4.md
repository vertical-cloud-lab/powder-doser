# 2026-09-14 (night) — silicon −110/+200 blocks G+H: attempt #4 stood down for rig contention, superseded by attempt #5

| | |
|---|---|
| Intended | Blocks `GH` (3 × 1 g + 3 × 50 mg + 3 × 200 mg) — the last missing cell of the powders × blocks coverage grid |
| Trigger | @swcharles, 19:46 MDT: *"it's now 7:45pm and there's no one in the lab. Try again."* — the empty-lab test of the evening window, after the [third stand-down](2026-09-14-silicon-110-200-gh-standdown3.md) concluded mornings were the reliable launch window |
| Outcome | **Not run in this session — and for a new reason.** Not the environment: mid-hold, the delivery path was made physically incapable of dispensing (PR #131 blocked-auger fixture, 19:55 MDT), and the rig became contested between three concurrent Claude sessions. When the operator confirmed the auger unblocked at 20:18 MDT, a fresh session (attempt #5) took the rig; this session yielded rather than compete for the serial port. |
| Dataset impact | **None** — no powder dispensed, no `battery_runs` document created (35 runs unchanged). This session never actuated anything: balance re-zero + read-only surveys only. |
| Balance | Re-zeroed at 19:58 MDT off a stale **−66.6 mg** tare (residue of the attempt-3 drift walk). Sample-to-sample jitter 0.059 mg — display floor. |
| Firmware | All 6 Pico modules verified byte-identical to the repo (on-device SHA-256) before the hold. |

## The hold — 5 windows, then the premise dissolved

Launch condition unchanged (the four accepted 2026-09-10 launches): 180 s
survey, end-to-end inside ±6 mg, peak-to-peak ≤ 6 mg, zero single-poll jumps
≥ 10 mg; marginal (≤ 9 mg) only with next-window confirmation.

| # | ends (UTC) | ends (MDT) | end-to-end (mg/180 s) | peak-to-peak (mg) | jumps ≥ 10 mg |
|---|---|---|---|---|---|
| 1 | 01:58:03 | 19:58 | +11.5 | 12.8 | 0 |
| 2 | 02:01:05 | 20:01 | −11.2 | **100.2** | **12** |
| 3 | 02:04:06 | 20:04 | −31.0 | 55.2 | 3 |
| 4 | 02:07:08 | 20:07 | −23.6 | 29.8 | 1 |
| 5 | 02:10:10 | 20:10 | +17.0 | 17.8 | 0 |

Window 2's jump cluster (t = 50–70 s, bidirectional ±37 mg ringing) and
window 3's step pairs are hands-on-bench signatures, not room noise — and the
comment record explains them precisely.

## What was actually happening (all times MDT)

| | |
|---|---|
| 19:46 | @swcharles pings #116 → this session (attempt #4) |
| 19:55 | **@williamulbz on PR #131: "I have set up a blocked auger so that no powder will dispense"** — asks for balance-noise characterization; a second session spawns. The physical install is happening at the bench during windows 2–4. |
| 19:58 | williamulbz tells the noise test to wait for this #116 session; a third (guard) session spawns |
| 20:01 | williamulbz: noise tests deferred until further notice — "requires some physical setup" |
| 20:10 | The 19:55 noise session (spawned before the wait instruction existed) takes the Pico port and starts its tap/RPM-ladder battery — gate window 6 finds `/dev/ttyACM0` busy |
| ~20:18 | The noise battery's host process ends (port observed free from 20:18; the session later completed `success`) |
| 20:15 | Bench camera: **lab dark, lights off** — the human part of the visit is over ([frame](../rig-checks/frames/2026-09-14-attempt4_bench-dark-2015.png)) |
| 20:18 | **@williamulbz on #116: "the lab is truly empty now. Try again. The powder is in place and the auger is no longer blocked"** → attempt #5 session spawns |
| 20:27 | Attempt #5 takes the rig (port-holder probe + its own gate). This session stands down and yields. |

So attempt #4's gate never measured an empty lab: windows 1–5 bracket a
teammate physically rebuilding the delivery path, and everything after
20:10 belonged to other sessions.

## What the two least-contaminated windows still say

Windows 1 and 5 (no shocks, bench untouched during the window) both show the
familiar smooth wave — swings of 12.8 and 17.8 mg with end-to-end drifts of
+11.5 and +17.0 mg/180 s. That is consistent with all three prior holds and
**does not** support "empty evening = launchable" on its own, but n = 2
windows wrapped around active bench work proves nothing either way. The
clean empty-lab verdict passes to attempt #5's gate, which runs with the
building in the same state and genuinely nobody present.

## Lessons for a shared rig (one rig, three robots)

1. **One session owns the rig at a time, and ownership follows the newest
   operator instruction.** The 20:18 comment superseded the 19:46 one — same
   task, updated hardware state — so the right move for the older session was
   to yield the port, not queue for it.
2. **Hardware state changes must be stated where the pending session can see
   them.** The blocked-auger install was announced on PR #131 while the #116
   session it invalidated was mid-hold. The 20:18 #116 comment did it right:
   full rig state ("powder is in place and the auger is no longer blocked")
   in the same thread as the request it re-arms.
3. **A gate hold cannot tell "room" from "colleague" without the comment
   record and the camera.** Window 2 alone looks like a catastrophic
   environment; with the PR #131 timeline it is simply an auger swap.
4. **Interrupted device-side scripts are a handoff hazard.** Killing the
   host-side `mpremote run` leaves the Pico script executing headless; the
   next session's port grab soft-interrupts it at an arbitrary point,
   potentially mid-actuation. Whoever takes the rig next should treat
   actuator state as unknown until their own init/teardown runs.

## Files

- `docs/rig-checks/data/2026-09-14-attempt4_silicon-110-200-preroll-survey{1..5}-180s.csv`
  — the five survey captures
- `docs/rig-checks/frames/2026-09-14-attempt4_silicon-110-200-gate-hold.png`
  — the hold figure (`scripts/plot_gate_hold.py`)
- `docs/rig-checks/frames/2026-09-14-attempt4_bench-dark-2015.png`
  — bench camera at 20:15:31 MDT: lab dark, rig on LED glow only
- `docs/battery-runs/RIG-STATE.md` — the blocked-auger state row this session
  added mid-hold, and the unblocked confirmation that superseded it
