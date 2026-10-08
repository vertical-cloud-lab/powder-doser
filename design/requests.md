# Requests for the next iteration

Issue #36 explicitly invited a list of "extra help or any extra
resources" requests. Here is what would unblock the next pass.

## Hardware to put in the repo or stock at the lab

- **Nitrile O-rings, AS568 ~006–008 range** (Ø ≈ 14 × Ø ≈ 1.5 mm
  cross-section). Needed for the bayonet-plug cap's face seal.
  10-pack of each size from McMaster is fine.
- **Sheet of food-grade silicone, ~0.5–1.0 mm thickness.** Needed as
  the inter-disc gasket for the twist-shutter v2, and as raw stock for
  the slit-septum concept (§2.5) if we revisit it.
- **Micro torsion springs, music wire, ~Ø1.0 mm × ~5 mm coil OD,
  ~0.05 N·mm/°.** Backup for the spring-hatch flexure if PETG fatigue
  is a problem.
- **9 g micro-servo (SG90 or equivalent)** + matching 1.6 mm horn.
  This is the prototype mechanism-side driver for both the twist
  shutter and the bayonet plug. Three of them is enough for bench
  rigging.
- **A fixed reference printed channel cartridge** — the PR-#16 auger
  STL printed at production settings — so cap prototypes have
  something realistic to snap onto. The existing `cad/auger/` STL is
  fine; we just need one printed copy at the lab, dedicated to cap
  testing.

## Software / vendor-model access

- The current concepts only need the auger envelope, which I model as
  a Ø25 stub. If we want full assembly views, dropping in the
  PR-#16 STEP or STL of the auger (rather than the cylinder stub
  placeholder) into each `cad_model.py` would make the renders look
  like actual cartridges. Blocked on whether PR-#16 / PR-#35 lands first.

## Bench-test fixtures we will need

- A fixed-frequency vibration jig (any cheap massage-style ERM driver
  bolted to a 3D-printed clamp will do) with a way to hold the
  cartridge inverted.
- A 0.1 mg precision balance for the spill-mass measurements in the
  test plan (`cap-brainstorming.md` §3). The lab balance is fine.
- A stepper-driven cycle jig for the 100/1000-cycle durability runs.
  Can be a discarded NEMA 17 + a printed cam — straightforward, listed
  here only because we should agree on it before printing parts.

## Decisions I would like from a human reviewer before iterating

1. Of §2.1 / §2.2 / §2.3, which one(s) do we 3D-print first?
2. Should the receiver in the bayonet design be **bonded onto** the
   PR-#16 auger as a separate ring (current path), or **fused into**
   the auger SCAD model itself? The latter is a one-line edit but
   forecloses retrofit.
3. Are we OK with a per-cartridge plug (full C6) or a shared plug that
   cycles between cartridges of the same powder family (cheaper,
   weaker C6)?

Issue #36 says "I will choose, provide more input to move forward, and
refine" — these are the choices that would steer the next iteration.
