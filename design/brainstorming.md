# Powder doser — design brainstorming

This document is the written output of the brainstorming session called for
in [issue #29][i29]: an exploration of *architecture-level* design
possibilities for the powder doser, with the benefits and pitfalls of each.
No sketches or CAD are produced here — those are deferred to follow-up
issues once one or two architectures are chosen for prototyping.

[i29]: https://github.com/vertical-cloud-lab/powder-doser/issues/29

## 1. Requirements recap

The targets are pulled from the BYU NASA Space Grant 2026 proposal (issue
[#27][i27]) and the actuator/electronics selection (issue [#25][i25]):

- **Number of powders:** the proposal cites up to 30 distinct feedstocks
  available to the doser, but a *single* aerospace alloy realistically
  draws on only ~8–10 metal powders. Per Will's review of an earlier draft
  of this document, the autonomy budget already includes a per-campaign
  human touch (refill), and that same touch can swap which subset of
  powders is currently loaded. The architecture therefore does **not** have
  to host all 30 powders simultaneously — designs sized for ~8–12 active
  reservoirs with off-line cartridge/hopper storage for the rest are in
  scope and should be preferred where they materially shrink BOM or
  footprint.
- **Per-blend volume:** ≤ 250 mL of mixed powder per dispense cycle.
- **Per-powder accuracy:** ±1 wt% baseline, ±0.1 wt% stretch goal.
- **Powder family:** L-PBF metal feedstocks (representative candidates: 316L,
  Ti-6Al-4V, IN718) plus, opportunistically, organic/ceramic powders such as
  the xanthan gum used in early POSE testing.
- **Particle-size preservation:** PSD verified by laser diffraction
  pre- vs. post-dose; the dispenser must not appreciably grind, classify, or
  segregate the feedstock.
- **Cross-contamination:** quantified on three representative L-PBF powders;
  must be low enough to be acceptable for downstream alloy-discovery work.
- **Atmosphere:** ambient air for v1; inert-atmosphere enclosure deferred to
  v2 but should not be designed *out* of the v1 architecture.
- **Autonomy:** the doser sits inside an autonomous AM-alloy discovery loop
  feeding ultrasonic atomization → L-PBF, so a human should *not* have to
  swap, clean, or re-tare hardware between blends. A human refilling
  reservoirs once per campaign is acceptable; a human touching the
  dispense path between blends is not.
- **Driver hardware already chosen** (#25): NEMA 11 bipolar stepper on a
  Pololu DRV8825 carrier for the auger drive, JF-0530B solenoid on an
  Adafruit DRV8871, and an ERM/LRA vibration actuator on a DRV2605L, all
  hosted on a Raspberry Pi Zero 2 W via an Adafruit Perma-Proto Bonnet.

[i25]: https://github.com/vertical-cloud-lab/powder-doser/pull/25
[i27]: https://github.com/vertical-cloud-lab/powder-doser/pull/27

The combination of "30 powders" and "no human in the loop between blends"
is what makes this hard: any architecture in which the dispense path is
shared between powders must either tolerate cross-contamination, clean
itself between powders, or physically swap the contaminated parts.

## 1a. Per-channel mechanism stack (Sterling, PR thread)

Independent of architecture, Sterling has called out on the PR thread
that **every powder station should carry all three of the actuators
already selected in #25**, used in combination rather than as
alternatives:

1. **Auger** rotated by the NEMA 11 stepper, for bulk dispense rate.
2. **Tapping** via the JF-0530B solenoid, for breaking initial bridges
   and for the last-few-percent trim dispenses.
3. **Vibration** via the ERM/LRA on the DRV2605L, for sustained flow
   promotion at the auger-tube interface.

Different powders behave very differently — some flow well under
vibration alone, others need percussive taps to start, others need the
auger to do all the work — and the controller is expected to mix and
match these mechanisms per powder. A **fourth, possibly manual,
auger-angle adjustment** is also on Sterling's wish list (some powders
dispense more cleanly off-vertical), so the architecture should at
least not preclude tilting the dispense element.

Two related dispense mechanisms are explicitly **out of scope** per
that same comment:

- **Air-displacement / pneumatic transfer** — safety risk with reactive
  metal powders, plus concerns about over- or under-shooting the
  collection cup. This rules out architecture 2.6 below as a primary
  path; it remains catalogued only for completeness.
- **Mechanical scraping for de-clumping** — the strategy is to prevent
  clumps upstream (manual lump-breaking before loading, room-level
  industrial dehumidifier, inert atmosphere where possible) rather
  than to break them up inside the dispenser.

## 2. Architecture options

For each candidate the discussion flags benefits, pitfalls, and the
specific way it interacts with the autonomy and cross-contamination
requirements. Per §1a, every architecture below assumes the
auger / tap / vibrate triplet is present at each dispense site; the
architectures differ in *how many* dispense sites exist and in
whether any hardware is shared between powders.

### 2.1 Manual single-tube swap (status-quo / strawman — rejected)

A single auger + tube + reservoir; the operator pulls the assembly,
brushes/vacuums it, and reloads with the next powder.

- **Benefits:** simplest mechanically; only one of every actuator from #25
  needs to exist; trivial to validate in isolation.
- **Pitfalls:** breaks the autonomy requirement outright. Listed only as a
  baseline to compare the other options against and to make explicit why
  it is being rejected for the autonomous-loop use case.

### 2.2 N parallel dispense channels — one reservoir + auger per powder

The "obvious" answer: replicate the #25 actuator stack `N` times. Each
powder lives in its own hopper, fed by its own auger tube. The cleanest
physical layout is a fan or ring of channels with their tube outlets
all aimed at a single shared collection cup on a load cell directly
below — i.e. the cup is stationary and the channels surround it. With
~30 mm-diameter tubes, ~12 channels fit on a ~150 mm pitch circle aimed
inward at a ~40 mm-radius cup, so the §1 "loaded subset of ~8–12"
sizing comfortably fits this geometry; supporting all 30 simultaneously
would require either two stacked rings or a much larger cup. As a
variant of this same architecture, the cup + load cell can instead be
moved on a gantry or carousel under each channel in turn (similar to
2.3/2.4 but with the *cup* moving instead of the dispense head); that
removes the fan-in geometry constraint at the cost of motion on the
weighing side, which is the noisier place to put it.

- **Benefits:**
  - Zero cross-contamination by construction — powders never share a
    wetted surface.
  - Channels are embarrassingly parallel: a failed channel doesn't stop
    the others, and channels can dispense in any order, including in
    parallel for very different mass targets. (Per-channel tunability
    of pitch / RPM / vibration profile is *not* unique to 2.2 — 2.3
    and 2.4 can also tune those parameters per cartridge in software,
    Will noted on an earlier draft — so it isn't called out as a
    benefit here.)
  - Cleanest path to the inert-atmosphere v2: the whole bank of channels
    sits inside one sealed enclosure with a single dispense aperture.
- **Pitfalls:**
  - **Footprint and BOM scale linearly with N.** Even at the §1
    "loaded subset" of ~8–12, that is 8–12 NEMA-11 steppers, 8–12
    DRV8825s, 8–12 hoppers, 8–12 augers; at the full 30 it doubles
    again. Mechanical packaging dominates; electronics cost is also
    non-trivial (~$20–$30 per channel before the hopper/auger).
  - Pi I/O fan-out: even 12 step/dir pairs is past what one Pi Zero 2 W
    + bonnet can host without an I²C/SPI GPIO expander or a
    daisy-chainable stepper bus (e.g. TMC stepper drivers on a shared
    UART, or stepper modules behind I²C expanders); 30 makes this
    mandatory.
  - Per-channel calibration burden: each channel needs its own
    flow-rate vs. step-rate model. This is a software problem, not a
    hardware one, but it does scale with N.
  - Dead volume in each hopper: N × (refill threshold) of powder must
    sit on the bench at all times.

This is the option that most cleanly satisfies the requirements as
written, and is the recommended starting point for the prototype.

### 2.3 Carousel of cartridges sharing one dispense head

A single auger/dispense head stays fixed above the collection cup; a
rotating carousel of `N` cartridges (each cartridge = hopper + integrated
auger flight) indexes the next powder under the head, which engages and
drives that cartridge's flight via a flexible coupler or splined shaft.

- **Benefits:**
  - Only **one** stepper, driver, vibration motor, and solenoid — the
    BOM no longer scales with N.
  - Cross-contamination is again zero, because each cartridge contains
    its *own* wetted surfaces (hopper walls + auger flight); the shared
    motor never touches powder.
  - Cartridges become the natural unit of refill and storage: a swappable,
    sealed cartridge can be loaded off-line, weighed, and verified before
    being inserted.
  - Indexing is a single rotational degree of freedom, which is mechanically
    cheap and easy to home/index repeatably (a second small stepper or a
    geared servo with a hall-effect or optical index sensor).
- **Pitfalls:**
  - The shaft-engagement coupling is the hard part: it must transmit
    torque, self-align after every index move, and not generate or
    accumulate powder on the engagement faces. A magnetic / Oldham /
    spring-loaded dog clutch are all candidates and all need prototyping.
  - Cartridges are now a custom mechanical assembly that has to be
    produced in quantity (one per loaded powder, plus spares for
    off-line refills). Will pointed out on an earlier draft that since
    the auger tubes themselves are 3D-printable on the Bambu H2D, full
    cartridges built around those same tubes should print on the same
    machine without much trouble — so this is a fixturing / repeatable-
    geometry task rather than a manufacturing risk.
  - Carousel diameter scales with cartridge cross-section × 30 — at any
    reasonable cartridge size the carousel is large (rough cocktail-napkin
    estimate: a 60 mm-diameter cartridge × 30 → roughly a 600 mm
    pitch-circle carousel). This may push the design toward two stacked
    smaller carousels of 15 each, or toward 2.4.
  - Refill ergonomics: rotating the desired cartridge into a "refill
    position" is straightforward, but the operator now has to know how the
    indexing software sees the carousel.

### 2.4 X-Y / linear gantry over a static cartridge array

A grid (e.g. 5 × 6 = 30) of cartridges, each with its own auger flight
but no motor. A single drive head on an X-Y gantry parks over the
selected cartridge, descends, engages the flight, dispenses, retracts,
and moves to the next one. Variant: a single linear axis over a 1 × 30
strip of cartridges.

- **Benefits:**
  - Same one-motor BOM win as 2.3, with a more compact footprint per
    cartridge (cartridges can be packed tightly because they don't need
    to share an axis of rotation).
  - X-Y gantry mechanics are extremely well understood — every Bambu
    printer in the lab is one — so the motion stage can crib heavily
    from off-the-shelf 3D-printer kinematics.
  - Cartridges can be added, removed, or re-arranged without re-balancing
    a rotating assembly.
- **Pitfalls:**
  - In the X-Y *grid* sub-variant, the dispense head has to *travel
    over* the open tops of other cartridges, so cartridges must be
    sealed (lidded with a self-closing slit) or the gantry must
    dispense outside the cartridge field — otherwise stray powder shed
    from the head will fall into the wrong cartridge. The **1 × N
    linear sub-variant collapses this problem**: with the cartridges in
    a single row and the cup parked off the end of the row, the
    drive-head travel path no longer crosses any cartridge mouth, and
    the architecture reduces to a single motion axis plus the same
    shaft-engagement clutch as 2.3 (Will's note on the original draft).
  - Two motion axes plus a Z-engage axis on the head in the grid
    sub-variant, so its BOM is higher than 2.3; the 1 × N sub-variant
    is closer to 2.3 in BOM.
  - Same shaft-engagement problem as 2.3.

### 2.5 Vibratory / piezo dispensing instead of an auger

Replace the auger with a vibratory trough or piezo-driven dispense
nozzle (one per powder). The vibration motor from #25 already exists;
the piezo variant would replace the DRV2605L + ERM with a piezo driver
and a stack actuator. *(Note: this is the auger-less variant; the
default per-channel mechanism stack from §1a still keeps vibration as a
flow aid alongside the auger in the other architectures.)* On Will's
review of the original draft, the pitfalls below — particularly
powder-dependent throughput and sensitivity to powder height/humidity/
tribocharging — were judged to make this option a poor fit for the
varied L-PBF feedstock list, so it is kept catalogued but not
recommended as a v1 path.

- **Benefits:**
  - No rotating wetted parts at all → very low risk of grinding the
    powder or altering the PSD.
  - Mechanically the simplest possible dispense element — well-suited to
    being mass-produced 30 times for an option-2.2-style channel bank.
  - Naturally bidirectional in throughput: macro-dose with steady
    excitation, then trim with single-pulse "tap" dispenses for the last
    few percent of mass.
- **Pitfalls:**
  - Throughput is powder-dependent and can be very low for cohesive
    metal powders (Ti-6Al-4V is notorious here). Hitting 250 mL of total
    blend in a tractable time may be a stretch for some feedstocks.
  - Dispense rate is exquisitely sensitive to powder height in the
    trough, humidity, and tribocharging. Closed-loop control on a load
    cell partially absorbs this, but it's a real risk to accuracy.
  - Doesn't eliminate the cross-contamination problem on its own — it
    has to be combined with one of the per-powder-channel architectures
    above.

### 2.6 Pneumatic / aspirated transfer (out of scope per §1a)

A vacuum (or positive-pressure) system aspirates a fixed-volume slug of
powder from a source reservoir and delivers it into the collection cup,
analogously to a pipette. **Sterling has explicitly ruled this out** in
the PR thread on safety and reliability grounds (reactive-metal-powder
hazard plus the risk of overshooting or missing the collection cup); it
is documented here for completeness only.

- **Benefits:**
  - The source reservoirs never have to move; the only moving thing is
    the aspirator tip on a gantry, similar to a liquid-handling robot.
  - Volumetric metering by displacement is very repeatable for free-
    flowing powders.
- **Pitfalls:**
  - The aspirator tip is a *shared* wetted surface. To stay
    cross-contamination-clean it has to be either disposable (same
    autonomy problem as 2.1) or rigorously self-cleaned between
    powders (blow-down, ultrasonic bath, etc.) — neither of which is
    cheap.
  - Filtering vacuum exhaust to keep metal powder out of the pump and
    out of the room is a non-trivial safety problem, especially for
    reactive feedstocks like Ti-6Al-4V.
  - Inert-atmosphere v2 becomes much harder because the system now
    actively moves gas through the powder.

### 2.7 Hybrid: per-powder hopper feeding a shared, self-cleaning auger

A bank of N powder hoppers (no auger of their own) gravity- or
vibratorily-feeds a *single* augered dispense tube. Between powders, a
purge cycle flushes residual powder from the auger into a waste port,
optionally followed by a brush, blow-down, or ultrasonic clean.

- **Benefits:**
  - Splits the difference on BOM: N hoppers + N feed valves + 1 motor +
    1 auger.
  - Reservoirs are simple — just hoppers with a closable bottom — and
    can be larger (deeper) than in 2.3/2.4 for the same footprint.
- **Pitfalls:**
  - The cleaning step is the entire ballgame and we have no evidence yet
    that any cleaning method gets the auger flight clean enough to hit
    the cross-contamination spec on Ti-6Al-4V → IN718 transitions, where
    even sub-percent contamination is a real metallurgical concern.
  - Purge powder is wasted feedstock. For 30 powders × many blends per
    campaign, this can become significant for expensive alloys.
  - Verification of "clean enough" is itself a hard problem and probably
    requires an in-line sensor (e.g. XRF, LIBS) or destructive sampling.

## 3. Cross-cutting concerns (independent of architecture)

These apply to whichever architecture is picked and so don't drive the
top-level choice, but they constrain it.

- **Mass measurement.** A single load cell under the collection cup is
  the simplest closed-loop signal and works for every architecture
  above. Resolution requirement: ±0.1 wt% of 250 mL of, say, IN718
  (≈ 2 kg/L) is ≈ 0.5 g, which is easy. ±0.1 wt% of an individual 1-mL
  trace addition is ≈ 2 mg, which requires a high-resolution cell and
  serious vibration isolation.

  Sterling's PR-thread comment narrows this further with a concrete
  per-build mass envelope. Given the two L-PBF machines targeted
  downstream (Mastrex MX-120 ≈ 220 g/build, Aconity MIDI ≈ 440 g/build,
  both at 3× hopper fill of apparent-density powder) and the upstream
  graphite-crucible volumes for the induction furnace (225 cm³ and
  400 cm³), a single dose campaign is expected to be in the
  **~100–1000 g** range, while occasional rare-earth or trace
  additions will be in the **single-mg-to-gram** range. No single
  A&D balance covers both ends with sub-mg resolution; in the A&D
  family the candidates the team is currently weighing are:

  - **FZ-523** — 520 g capacity, 1 mg resolution: covers a full
    MX-120 / MIDI dose cycle in one shot, but isn't fine enough for
    individual trace additions.
  - **HR-202i** — 220 g / 0.1 mg, with a 51 g / 0.01 mg fine mode:
    enough for an MX-120 build envelope and excellent for trace
    additions, but light on capacity for MIDI.
  - **HR-300i** — 320 g / 0.2 mg: a single-balance compromise that
    *almost* covers the MIDI build envelope.

  The most likely outcome is a **two-station weighing setup** — one
  high-resolution balance (e.g. HR-202i, or the existing HR-100A) for
  trace and small additions on a thin Al-foil "inner inner" crucible,
  plus a higher-capacity balance (e.g. FZ-523 or FZ-2202) for the
  large Al crucible, Al shot, and bulk additions. The architecture
  choice in §2 should therefore not assume a *single* cup / load-cell
  position; whichever option is built needs to either (a) deliver
  cleanly into either of two cups at different weighing stations, or
  (b) be replicated in a small-station and large-station variant.
  This pushes mildly in favor of architectures where the cup can move
  (the cup-on-gantry variant of 2.2, or 2.3/2.4 with two parking
  positions for the head) over those that hardwire one cup beneath
  the dispense field.
- **Electrical grounding of the collection vessel.** Per Sterling's PR
  comment, the aluminum crucible / vial that catches the dispensed
  powder will be **grounded** (copper tape, conductive cup support, or
  similar; possibly even biased) to control electrostatic effects that
  otherwise dominate the behavior of fine metal powders falling into
  a small target. The cup-support fixture must therefore include an
  intentional, low-resistance ground path. Critically, that path must
  be made through a flexible, low-stiffness link (thin wire braid or
  conductive foam) so that it does **not** add a parasitic spring path
  to the load cell and bias the weighing — the same constraint as the
  vibration-isolation bullet, just applied to the electrical bond.
- **Vibration coupling.** The vibration motor from #25 is for promoting
  flow at the auger / hopper interface. It must be mechanically isolated
  from the load cell under the collection cup, or the cell signal will be
  unusable during dispense. This applies equally to all of 2.2, 2.3, and
  2.4 — Will pointed out on an earlier draft that there's no a-priori
  reason 2.3/2.4 can decouple the dispense head from the cup but 2.2
  cannot, so the previous wording singling out 2.2 has been removed. In
  every case the practical fix is the same: rubber/silicone vibration
  isolators between the dispense-side structure and the cup support, and
  blanking out load-cell samples while the vibration motor is energized.
- **Powder safety.** Reactive metal powders (Ti, Al) are a fire and
  inhalation hazard. The architecture must accommodate (a) sealed
  hoppers, (b) a dust-tight enclosure around the dispense path, and (c)
  inerting in v2. Architectures 2.2 and 2.3 enclose most cleanly;
  2.6 is the worst.
- **Refill workflow.** "Minimal human intervention" is a *per-blend*
  goal, not a *per-campaign* goal. The architecture should make
  reservoir refill safe and unambiguous (e.g. swappable cartridges in
  2.3/2.4, lidded hoppers in 2.2). Each reservoir should carry an ID
  (printed barcode, RFID, or just a slot index) so the controller can
  cross-check that "powder X is actually in slot Y" before dispensing.
- **Calibration data.** Whatever architecture wins, every powder × every
  channel needs a flow-rate model. The repository already plans for a
  Python software stack (#25); this is where that model lives. The
  architecture choice mostly affects how many independent models exist
  (N in 2.2, 1 + per-cartridge correction in 2.3/2.4, 1 in 2.7,
  where N is the §1 "loaded subset" of ~8–12 rather than 30).

## 4. Recommendation and next steps

Folding in the PR-thread feedback shifts the recommendation. With the §1
clarification that only ~8–12 powders need to be loaded at a time
(the rest are swapped at refill), 2.2's footprint pitfall is much
less severe; with §1a's auger + tap + vibrate triplet baked in at every
station, 2.2 and 2.3 are mechanically more similar than the original
draft suggested; and with Will's note that the 1 × N variant of 2.4
collapses to a single motion axis with no dispense-over-cartridges
problem, **the 1 × N linear variant of 2.4 should also be carried as a
serious candidate** alongside 2.3 — the difference between "rotating
carousel of cartridges past a fixed head" and "fixed row of cartridges
with a head sliding past" is small enough that the same shaft-engagement
prototype answers both.

The current ranking is therefore:

- **2.2 (N parallel channels) as the v1 reference design**, sized for
  the §1 loaded subset (~8–12 channels) rather than the full 30, with
  every channel carrying the §1a auger + tap + vibrate triplet. Most
  directly satisfies the cross-contamination requirement and reuses
  the #25 actuator stack verbatim per channel.
- **2.3 (cartridge carousel) and the 1 × N variant of 2.4 as the
  principal single-motor alternatives**, to be prototyped together
  since they share the cartridge + clutch design.
- **2.5 (vibratory-only)**: deprioritized per Will's review; powder-
  dependent throughput and humidity/tribocharging sensitivity make it
  a poor fit for the L-PBF feedstock list. Note that vibration is
  still present at every dispense site as part of the §1a triplet —
  this option is just rejected as the *primary* dispense element.
- **2.6 (pneumatic)**: out of scope per Sterling's PR comment
  (reactive-powder safety, plus targeting risk).
- **2.7 (shared self-cleaning auger)**: blocked on the unknown "is
  the cleaning good enough" question and so should not be the v1
  path.

Concrete follow-ups worth opening as their own issues:

1. A 1-channel mechanical prototype of 2.2 using the exact #25 BOM
   *plus* electrical grounding of the cup per §3, to characterize the
   dispense element in isolation (flow rate vs. step rate, accuracy
   limit, vibration coupling, PSD preservation, electrostatic
   behavior with and without grounding).
2. A 1-cartridge prototype of 2.3 / 1 × N 2.4 focused only on the
   shaft-engagement clutch and on the cartridge as a printable unit,
   since that is the part with the most unknowns.
3. A control-board capacity study: a Pi Zero 2 W + bonnet probably
   can't host 8–12 step/dir pairs directly, let alone 30, so what
   GPIO-expander or smart-stepper bus closes the gap?
4. A cross-contamination measurement protocol — independent of
   architecture — so the candidate designs can be compared
   quantitatively rather than argumentatively.
5. A weighing-station design study against Sterling's per-build mass
   envelope (~100–1000 g typical, with single-mg trace additions),
   sizing one or two A&D balances (FZ-523 / HR-202i / HR-300i /
   existing HR-100A) and deciding whether the doser delivers into a
   single cup or hands off between two stations.
