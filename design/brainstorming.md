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

- **Number of powders:** up to 30 distinct feedstocks available simultaneously.
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

## 2. Architecture options

For each candidate the discussion flags benefits, pitfalls, and the
specific way it interacts with the autonomy and cross-contamination
requirements.

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
powder lives in its own hopper, fed by its own auger tube, dispensing
into a shared collection cup that sits on a single load cell.

- **Benefits:**
  - Zero cross-contamination by construction — powders never share a
    wetted surface.
  - Each channel can be tuned independently (pitch, RPM, vibration profile)
    for that powder's flowability.
  - Channels are embarrassingly parallel: a failed channel doesn't stop
    the others, and channels can dispense in any order, including in
    parallel for very different mass targets.
  - Cleanest path to the inert-atmosphere v2: the whole bank of channels
    sits inside one sealed enclosure with a single dispense aperture.
- **Pitfalls:**
  - **Footprint and BOM scale linearly with N.** At N = 30, that is 30
    NEMA-11 steppers, 30 DRV8825s, 30 hoppers, 30 augers. Mechanical
    packaging dominates; electronics cost is also non-trivial (~$20–$30
    per channel before the hopper/auger).
  - Powder-Pi I/O fan-out: 30 step/dir pairs is past what one Pi Zero 2 W
    + bonnet can host without an I²C/SPI GPIO expander or a
    daisy-chainable stepper bus (e.g. TMC stepper drivers on a shared
    UART, or stepper modules behind I²C expanders).
  - Per-channel calibration burden: each channel needs its own
    flow-rate vs. step-rate model. This is a software problem, not a
    hardware one, but it does scale with N.
  - Dead volume in each hopper: 30 × (refill threshold) of powder must
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
  - Cartridges are now a custom mechanical assembly that must be
    manufacturable in quantity (30 of them) and ideally hand-printable on
    the Bambu H2D used for the rest of the prototype.
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
  - Two motion axes instead of one (vs. the carousel), and a Z-engage
    axis on the head, so the gantry-itself BOM is higher than 2.3.
  - The dispense head now has to *travel over* the open tops of the
    other cartridges. Cartridges must be sealed (lidded, with a slit that
    closes) or the gantry must dispense outside the cartridge field —
    otherwise stray powder shed from the head will fall into the wrong
    cartridge.
  - Same shaft-engagement problem as 2.3.

### 2.5 Vibratory / piezo dispensing instead of an auger

Replace the auger with a vibratory trough or piezo-driven dispense
nozzle (one per powder). The vibration motor from #25 already exists;
the piezo variant would replace the DRV2605L + ERM with a piezo driver
and a stack actuator.

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

### 2.6 Pneumatic / aspirated transfer

A vacuum (or positive-pressure) system aspirates a fixed-volume slug of
powder from a source reservoir and delivers it into the collection cup,
analogously to a pipette.

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
- **Vibration coupling.** The vibration motor from #25 is for promoting
  flow at the auger / hopper interface. It must be mechanically isolated
  from the load cell under the collection cup, or the cell signal will be
  unusable during dispense. Architectures 2.3 and 2.4 make this easier
  (the dispense head is decoupled from the cup); 2.2 needs explicit
  isolation.
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
  (30 in 2.2, 1 + per-cartridge correction in 2.3/2.4, 1 in 2.7).

## 4. Recommendation and next steps

For the prototype phase the discussion converges on **architecture 2.2
(N parallel channels) as the v1 reference design**, with **architecture
2.3 (cartridge carousel) as the principal alternative** to evaluate in
parallel. The reasoning:

- 2.2 most directly satisfies the cross-contamination requirement
  without inventing a new mechanism, and it lets us reuse the #25
  actuator stack verbatim per channel; "scale by replication" is a
  conservative engineering choice when the per-unit design is already
  the open question being studied.
- 2.3 is the most attractive single-motor option and is the natural way
  to push BOM down in v2 once the per-channel dispense element is well
  understood; prototyping it in parallel (even at N = 3) protects
  against 2.2's footprint problem.
- 2.7 (shared self-cleaning auger) is intriguing but blocks on the
  unknown "is the cleaning good enough" question, so it should not be
  the v1 path.
- 2.4 (gantry), 2.5 (vibratory), and 2.6 (pneumatic) remain on the
  table as variants and as fallback strategies for specific powders
  that misbehave in the chosen v1 architecture.

Concrete follow-ups worth opening as their own issues:

1. A 1-channel mechanical prototype of 2.2 using the exact #25 BOM, to
   characterize the dispense element in isolation (flow rate vs. step
   rate, accuracy limit, vibration coupling, PSD preservation).
2. A 1-cartridge mechanical prototype of 2.3 focused only on the
   shaft-engagement clutch, since that is the part with the most
   unknowns.
3. A control-board capacity study: can a Pi Zero 2 W + bonnet host 30
   step/dir pairs (probably not directly), and what GPIO-expander or
   smart-stepper bus closes the gap?
4. A cross-contamination measurement protocol — independent of
   architecture — so the candidate designs can be compared
   quantitatively rather than argumentatively.
