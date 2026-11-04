# precedent (job-futurehouse-paperqa3-precedent)

## System context

We are designing a **multi-doser carousel** for an open-source autonomous
powder-dosing instrument (metal powders for laser powder-bed fusion, plus
organic/ceramic powders; particles tens of microns, cohesive, hygroscopic,
sometimes triboelectrically charged).

Each *dosing module* is a cylindrical cartridge holding a powder reservoir and
an Archimedes auger. The auger tube ends in a small **dispensing outlet
(nozzle) on the cylindrical side or front face of the module**, roughly 5-15 mm
across. Modules are carried on a **roller-chain carousel** (steel roller chain
with custom 3D-printed carrier links). A robotic arm picks a module off the
chain, mounts it to a dosing station (stepper drives the auger; a solenoid taps
it; a servo tilts it), then returns it to the chain.

## The specific problem

Because each module simply hangs/sits on a chain carrier, **we cannot guarantee
its rotational orientation about its own long axis**. When the module returns to
the carousel it may be at any clock angle. We want a **front cap / closure over
the dispensing outlet** that:

1. Keeps powder in (and, ideally, air/moisture out) while the module sits in
   storage on the carousel, possibly for days.
2. Opens automatically when the module is docked at the dosing station, and
   re-closes automatically when it is undocked -- **with no electrical
   connection, no wiring, and no dedicated actuator on the module itself**
   (the module is a passive, hot-swappable consumable).
3. Is **insensitive to the module's rotational orientation**: the opening
   action must work when the module is approached/engaged from an arbitrary
   clock angle, OR the mechanism must self-index the module to a known angle
   during docking.
4. Is manufacturable by FDM/SLA 3D printing plus stock springs/O-rings, and
   does not shed particulates or trap powder in a way that causes
   cross-contamination between powders.

One idea already on the table: a **spring-loaded iris/aperture diaphragm with a
ratchet**, so continued rotation in one direction opens it and reversing
slightly lets it snap closed.

## What we want from you

Find **real, existing mechanisms and prior art** (patents, commercial products,
standard components, published mechanism designs) that solve this or a closely
analogous problem. For each, give the concrete identifier (patent number,
product/part number, manufacturer, standard) and explain the mechanism.

Please deliberately cover these families, and add any we have missed:

1. **Rotation-agnostic / self-indexing docking**: kinematic couplings, Hirth /
   curvic couplings, ratcheting or lead-in helical chamfers that rotate a part
   into a keyed orientation as it seats, ball-detent quick-change tool holders,
   ISO/BT/HSK spindle tool interfaces, and robot tool changers (ATI, Schunk).
   Which of these actively *rotate* the part into alignment vs. merely tolerate
   arbitrary orientation?
2. **Self-closing valves opened by the mating fitting**: dry-break / clean-break
   couplings, non-spill quick disconnects (CPC, Colder, Staubli), needle-free
   medical connectors and self-sealing swabable valve septa, keg couplers, IBC
   / dry-disconnect powder valves (e.g. GEA Buck valve, Matcon cone valve, split
   butterfly valves such as ChargePoint AseptiSafe / Getinge), and capless
   automotive fuel-filler necks (Ford Easy Fuel and equivalents).
3. **Iris / aperture diaphragms**: camera iris diaphragms, iris dampers /
   valves, sphincter and iris-type powder or bulk-solids valves, 3D-printable
   iris mechanisms, and any ratcheted or spring-return iris designs. What are
   their known failure modes with fine powders (blade gaps, jamming, wear
   particulate)?
4. **Passive orientation-independent seals**: duckbill and slit (cross-slit)
   valves, umbrella valves, self-sealing septa, spring-energised sliding
   shutters, rotary-shutter caps, and press-fit "click-in" plugs.
5. **Mechanisms where a fixed external feature opens a closure through relative
   motion alone** (cam ramps, pin-in-slot, compliant bistable latches), as used
   in pipette tip ejectors, cartridge-based analytical instruments, and
   automated-lab consumables (e.g. Opentrons, Hamilton, Tecan consumables).

For each candidate, state: (a) how orientation-dependence is handled, (b)
whether it needs an actuator on the moving/consumable side, (c) suitability for
fine cohesive metal powder, (d) 3D-printability at lab scale, and (e) the
strongest reason it might fail in this application. End with a ranked shortlist
of the three most promising approaches and the specific parts or patents we
should read first.


---

# literature (job-futurehouse-paperqa3-high)

## System context

We are designing a **multi-doser carousel** for an open-source autonomous
powder-dosing instrument (metal powders for laser powder-bed fusion, plus
organic/ceramic powders; particles tens of microns, cohesive, hygroscopic,
sometimes triboelectrically charged).

Each *dosing module* is a cylindrical cartridge holding a powder reservoir and
an Archimedes auger. The auger tube ends in a small **dispensing outlet
(nozzle) on the cylindrical side or front face of the module**, roughly 5-15 mm
across. Modules are carried on a **roller-chain carousel** (steel roller chain
with custom 3D-printed carrier links). A robotic arm picks a module off the
chain, mounts it to a dosing station (stepper drives the auger; a solenoid taps
it; a servo tilts it), then returns it to the chain.

## The specific problem

Because each module simply hangs/sits on a chain carrier, **we cannot guarantee
its rotational orientation about its own long axis**. When the module returns to
the carousel it may be at any clock angle. We want a **front cap / closure over
the dispensing outlet** that:

1. Keeps powder in (and, ideally, air/moisture out) while the module sits in
   storage on the carousel, possibly for days.
2. Opens automatically when the module is docked at the dosing station, and
   re-closes automatically when it is undocked -- **with no electrical
   connection, no wiring, and no dedicated actuator on the module itself**
   (the module is a passive, hot-swappable consumable).
3. Is **insensitive to the module's rotational orientation**: the opening
   action must work when the module is approached/engaged from an arbitrary
   clock angle, OR the mechanism must self-index the module to a known angle
   during docking.
4. Is manufacturable by FDM/SLA 3D printing plus stock springs/O-rings, and
   does not shed particulates or trap powder in a way that causes
   cross-contamination between powders.

One idea already on the table: a **spring-loaded iris/aperture diaphragm with a
ratchet**, so continued rotation in one direction opens it and reversing
slightly lets it snap closed.

## What we want from you

Focus on the **powder-science and engineering evidence** relevant to choosing
among these closures:

1. What does the literature say about **powder leakage, rat-holing and flooding
   at auger/screw-feeder outlets** when the outlet is unsealed vs. sealed, and
   about "flushing"/uncontrolled discharge of aerated fine powders on
   uncapping?
2. Evidence on **contamination and particle shedding from sliding/rubbing
   closures** (iris blades, sliding shutters) with fine metal powders --
   including galling, wear debris, and powder ingress into mechanism clearances.
3. What sealing performance (moisture ingress, oxygen ingress) is actually
   achievable with **elastomeric self-closing valves (duckbill, slit septa,
   umbrella)** versus rigid caps with O-rings, and how does that compare to
   what's needed for hygroscopic / oxygen-sensitive metal powders (Ti-6Al-4V,
   AlSi10Mg) over multi-day storage?
4. Published work on **split butterfly valves / dry-disconnect containment
   valves** for powder transfer (containment performance, residual powder on
   the "passive" face, cleanability) and whether a scaled-down 3D-printed
   analogue is credible.
5. Any literature or standards on **triboelectric charging and adhesion of fine
   powders on polymer closure surfaces**, and material choices (ESD-safe
   filaments, PTFE, coated surfaces) that mitigate it.
6. Quantitative guidance on **how much residual powder remains on a
   contamination-critical mating face** after a dry-disconnect operation, and
   what that implies for cross-contamination between different alloy powders.

Cite specific papers, standards, and measured numbers wherever possible, and
finish with concrete, testable recommendations for a bench experiment that
would discriminate between an iris-type closure, an elastomeric self-closing
valve, and a rigid orientation-indexed cap.
