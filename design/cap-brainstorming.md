# Channel-Sealing Cap — Brainstorming

This document is the discussion half of issue
**vertical-cloud-lab/powder-doser#36** ("Channel-Sealing Cap Design for
Modular Powder Dosing"). Three of the six concepts below are taken into
parametric CadQuery prototypes under `design/cad/` for 3D-printing and
bench testing; the other three are documented for completeness so we
don't re-litigate them later.

> [!NOTE]
> The downstream module geometry (auger drive, vibrator, solenoid,
> single-channel frame) is still in flux — see issue #34 and PR #35.
> Every cap concept here is **agnostic to that frame**: the only
> interface assumed is the bottom of a swappable channel cartridge,
> nominally the PR-#16 Archimedes auger envelope (Ø25 outer cylinder
> with a Ø3 mm coaxial exit hole). When the host frame stabilises, the
> cap mounting feature (Ø31 lip in the prototypes) is the one constant
> the host has to honour.

## 1. Why a cap, and what does it actually have to do?

The "switchable channels, fixed mechanism" idea (issue text, also #34
Idea C) is what gives this device its main path to scaling beyond ~12
powders without the per-channel motor budget exploding. But it only
works if a channel is **safe to handle outside the mechanism**:

- carry a loaded channel from cartridge storage to the mechanism
- snap it into place
- spin / tap / vibrate / tilt it (the existing R1–R3 actuator stack) to
  dispense
- pull it back out and return it to storage with whatever powder is
  left, all without spilling or cross-contaminating

So a cap has to satisfy, at minimum:

| # | Requirement | Source |
|---|---|---|
| C1 | Seals the Ø3 dispense exit with **no leak** under axial tilt 0–90° | issue #36, "tipped to various angles" |
| C2 | Survives the dispense-mode actuators on the *other* side: rotor at ~60–300 rpm, solenoid tap at ~5–20 Hz, ERM coin at ~150 Hz | brainstorming §2.2 / R1–R3 of PR-#35 |
| C3 | Opens and closes **without** the operator handling powder | issue #36, "automated" |
| C4 | Mechanism-side actuation budget = "small motor or small linkage", explicitly *not* a 6-axis arm | issue #36 |
| C5 | Per-channel cost ≪ per-mechanism cost (the whole point of swap-channels) | issue #36 / #34 Idea C |
| C6 | Wetted volume is **owned by one powder** — no shared seal surface that touches two powders | brainstorming R8 (cross-contamination) |
| C7 | Prints on hobbyist FDM, optional silicone/o-ring inserts | repo convention |

A subtle one: the seal surface is the **cap's** problem, not the
mechanism's. The mechanism only ever touches the *outside* of the cap
(the actuation tab, the bayonet ear, the cam lobe — whatever the chosen
concept exposes). That keeps cross-contamination contained to the cap +
channel that owns it (C6).

## 2. Six concepts

### 2.1  Twist shutter (rotating disc, two coaxial holes)

Two coaxial discs, each with a sector-shaped slot, stacked face-to-face.
Rotating the lower disc 60° lines its slot up with the upper disc's
slot → open. Rotating it back → closed. Same idea as a camera lens cap
or a darkroom shutter.

Pros
- Single rotational degree of freedom — easy to drive with one small
  servo or a passive cam tab on the mechanism (C4 satisfied by a tiny
  9 g servo or even a stepper-driven cam already on the dispense head).
- The seal surface is *flush*, so it can be kissed by the rotor without
  jamming — no protruding flap, no dead volume above the seal. Plays
  well with C2 (the rotor is right there).
- All the wetted geometry (both discs) lives on the cartridge → C6.

Cons
- Two flat printed faces sliding against each other tend to leak fines.
  Needs either a thin nitrile gasket between the discs or a press-fit
  with O-ring on the rotating disc.
- Sub-µm fines (the worry case for cross-contamination, C6) can wedge
  between the discs and prevent full closure. Mitigation: a 0.3 mm
  recessed gutter around the slot that catches stragglers.

Prototype: [`design/cad/sealing-cap-twist-shutter/`](cad/sealing-cap-twist-shutter/).

### 2.2  Spring-loaded auto-opening hatch

A hinged flap held closed by a small spring (or a printed-in compliant
flexure). Insertion into the dispense head pushes the flap open against
a stationary cam pin on the mechanism. Pulling the channel out lets the
flap snap shut. Closest analogue: a fuel-tank cap "flapper" or a
gravity-fed pellet-stove auger gate.

Pros
- **Zero added actuator** on the mechanism side — the act of seating the
  channel opens the cap. Strongest possible C4.
- Fail-safe: power loss → channel removed → cap closed. C1, C6.
- Cheap (one printed flap + one torsion spring or no spring at all if a
  PETG flexure is sized right).

Cons
- The flap intrudes into the powder column when open, so it must be
  parked **outside** the dispense cone — adds 8–12 mm of axial length
  to the cartridge.
- Spring force has to be high enough to overcome powder cake on the
  flap face (C2 — vibrating powder packs locally) but low enough that
  the cam pin can deflect it without bending the cartridge mount.
  Tuning required; that is exactly why this is a 3D-print-and-test
  candidate.

Prototype: [`design/cad/sealing-cap-spring-hatch/`](cad/sealing-cap-spring-hatch/).

### 2.3  Bayonet plug with O-ring face seal

A short male plug with two opposing ears engages a female bayonet
groove on the cartridge bottom. A 1.5 mm cross-section O-ring on the
plug face provides the powder seal. Quarter-turn locks/unlocks. Same
idea as a Luer-lock fitting or a coffee-bag valve.

Pros
- Most positive seal of the three (compressed elastomer vs. printed
  face). Best C1 under tilt and vibration.
- Plug is a separate consumable: drop it in a wash bin between powder
  changes, or print one per powder for permanent C6.
- Bayonet motion is the same primitive as the twist-shutter, so the
  same mechanism-side servo can drive both — possible code path for a
  single-mechanism design that supports either cap.

Cons
- Operator (or mechanism-side gripper) has to actually hold the plug
  while the cartridge twists. That is a real linkage, not "free" —
  pushes into C4's "small motor" budget but does not exceed it (a
  single linear solenoid with a magnet-tipped plunger handles plug
  retention).
- Plug occupies the dispense path while installed — has to be moved
  fully clear before dispensing, which is more travel than the other
  two designs.

Prototype: [`design/cad/sealing-cap-bayonet-plug/`](cad/sealing-cap-bayonet-plug/).

### 2.4  Sliding gate (NOT prototyped)

A flat slide pulled across the exit by a single linear actuator —
basically a guillotine. Mechanically the simplest of all six.

Why not prototyped first: shears powder at every open/close cycle.
For sticky powders (xanthan gum, the canonical test material — see
`POSE_tube_xanthan_gum.png`) this is a near-certain jam mode. Worth
revisiting only if we settle on free-flowing powders exclusively.

### 2.5  Silicone septum / slit (NOT prototyped)

A self-healing silicone disc with a cross-cut slit; the auger pokes
through to dispense, the slit closes when the auger withdraws. Same
principle as an HPLC injector port or a milk-bottle nipple.

Why not prototyped first: requires the **rotor** to translate axially
on every dispense (the auger has to penetrate and retract the slit each
time). Our R5/R3 architecture has the rotor on a fixed axial position
relative to the cartridge. Adopting this would force a redesign of the
auger drive; the issue says cap concepts can require "reasonable
addition/alteration" but adding axial travel to the spinning rotor is
non-trivial in our flex-coupler stack.

### 2.6  Magnetic plug (NOT prototyped)

A ferrous plug held in by a recessed neodymium magnet on the cartridge,
lifted out by a stronger magnet on the mechanism head. Cute, contactless
on the cartridge side.

Why not prototyped first: magnetic field leaks into the powder column
and will pick up any ferrous fines (steel-alloy candidate powders from
PR #19 are a near-certainty here). Hard violation of C6 in the very
contexts we care most about (metal AM feedstocks).

## 3. Recommended next step

Print one of each of §2.1, §2.2, §2.3, mounted on a stub of the PR-#16
auger envelope (the prototypes in `cad/` already include this stub for
exactly this reason), load with a known mass of xanthan gum, and run a
shake/tilt test:

1. Cap closed, invert, tap 20× — measured spill mass should be 0 g
   (C1).
2. Cap closed, mount in vibration jig at 150 Hz for 60 s, then invert —
   spill mass should be < 1 mg (C2).
3. Open / close 100 cycles, then re-run test 1 (durability of the seal
   feature against printed-PLA wear).

The winner of that bench test is what we promote into the next
iteration of the single-channel module (PR #35).
