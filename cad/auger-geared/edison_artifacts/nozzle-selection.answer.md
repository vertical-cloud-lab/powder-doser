<!-- Edison task 03967deb-61c3-459d-80af-bcb3eddd7a49 via job-futurehouse-paperqa3-high -->

Question: We are designing a 3D-printed (FDM) metering auger for a low-cost benchtop
powder dispenser ("powder-doser"). The auger is a vertical hollow cylinder
(OD 25 mm, ID 21 mm) with an internal single-start Archimedean screw (central
shaft Ø8 mm, 10 mm-pitch helical fin, 2 mm fin thickness) that turns inside the
tube and pushes powder down to a conical exit funnel ending in a Ø3 mm exit
hole. The target dispensed media are ALLOY and MASTER-ALLOY METAL POWDERS
(e.g. gas- or water-atomised metal and intermetallic powders, including
master-alloy additions) used in combinatorial / formulation workflows, where we
need accurate, repeatable sub-gram (ideally tens-of-milligram) doses. These
powders span a range of particle size distributions (roughly d50 ~ 10-150 um),
densities (often 4-9 g/cm^3), morphologies (spherical atomised vs irregular),
and flowabilities (free-flowing to moderately cohesive, Hausner ratio ~ 1.1 to
~ 1.5), and some are abrasive.

We have prototyped FOUR candidate DISPENSING-END ("nozzle") geometries that
differ only in how the screw and central shaft terminate near the Ø3 mm exit;
everything above (tube, loading cap, helix pitch/thickness) is identical. The
four designs, exactly as enumerated by our team, are:

  1) A direct cutoff of the screw to a large open funnel leading to the nozzle
     exit. (The helical flight stops well above the exit; below it is just an
     open conical funnel down to the Ø3 mm hole, with no screw or shaft in the
     funnel region.)

  2) Continuing the screw until just before the nozzle exit (with a small
     funnel) WITHOUT shrinking the middle shaft. (The full-diameter Ø8 mm shaft
     and the flight run almost all the way down to a short funnel just above the
     exit hole.)

  3) A direct cutoff of the screw, positioned above a region where the central
     shaft shrinks (tapers) to a near-point at the exit. (The flight stops
     above the taper; the shaft then necks down to a tip, leaving an annular
     gap that widens toward the exit, but with no flight in the taper region.)

  4) Combining (2) and (3): continuing the screw as the middle shaft tapers
     down as well, so the flight follows the shrinking shaft down toward the
     exit.

Please conduct a thorough, high-effort literature review and then give a
reasoned recommendation. Specifically:

(A) Of the four geometries above, which is most likely to give the best
    metering performance -- highest dose accuracy and repeatability, lowest
    dribble / after-flow, least susceptibility to bridging, rat-holing, arching,
    or flooding (uncontrolled gravity flow) -- for the ALLOY / MASTER-ALLOY
    metal powders described? Rank or group the four if a single winner is not
    defensible, and explain the mechanism (e.g. how the screw-to-exit transition
    governs choke feeding vs flood feeding, how a tapered vs constant shaft and
    the annular discharge area affect the powder column and shear zone, and how
    each interacts with the dense, sometimes abrasive metal powder).

(B) Is there an ALTERNATIVE dispensing-end design, not in our list of four, that
    the literature suggests would meter dense metal/alloy powders better? For
    example: a choke / flood-feed transition or step change in flight depth near
    the discharge, a decreasing-pitch or tapered-flight ("compression") screw, a
    short discharge tube / land of a particular length-to-diameter ratio, an
    anti-dribble or shut-off feature, a tapered vs straight nozzle bore, an
    auger tip that protrudes into or stops short of the orifice, or other
    screw/loss-in-weight feeder discharge designs from the powder-handling,
    pharmaceutical / nutraceutical micro-feeder, additive-manufacturing
    metal-powder-dosing, or combinatorial-materials literature. Give concrete
    geometric parameters (pitch-to-diameter ratios, flight clearance, orifice
    and discharge-tube L/D, taper angles) where the literature provides them.

(C) Conversely, is it plausible that the choice among these four matters little
    for our regime -- i.e., that, for these powders and a Ø3 mm exit at low
    fill, dose accuracy is dominated by other factors (screw speed control,
    step resolution, percussive de-bridging / tapping, vibration agitation,
    powder conditioning / flow aids, ambient humidity, gravimetric closed-loop
    feedback) rather than by the exit geometry? If so, say so explicitly and
    cite the evidence, and identify which non-geometry factors dominate.

(D) What does the literature say specifically about screw / auger feeding and
    dosing of METAL and ALLOY powders (as opposed to pharmaceutical excipients
    or food powders) -- abrasion / wear of the screw and bore (relevant since
    ours is FDM plastic), the effect of high bulk density on torque and flow,
    segregation of multi-component master-alloy blends during augering, and any
    documented best practices or failure modes for the discharge / nozzle end.

Where the literature is sparse or absent for any of the above, please note that
explicitly and point to the most relevant adjacent prior art (e.g. volumetric
and loss-in-weight screw feeders for fine chemicals, lab-scale powder
micro-dispensers, metal-AM powder dosing, vibratory trickle chargers) along
with their key discharge-end design parameters.


Warning: no contexts were retrieved, so this answer is not grounded in evidence but is instead a direct response from the agent model.

Unfortunately, despite an exhaustive search using dozens of different query formulations across academic paper databases and patent repositories, no retrievable literature sources were found through the available search tools for this session. The system was unable to locate any papers or patents on screw feeder design, powder dispensing, auger dosing, metal powder feeding, or related topics. This appears to be a systemic search limitation rather than an absence of relevant literature, as substantial bodies of work exist on these topics.

Because no citable sources were retrieved, I cannot provide the fully literature-grounded analysis requested. However, I can offer the following engineering-principles-based guidance, which the user should verify against the primary literature recommended below.

**Key Recommendations (unverified against retrieved sources):**

**(A) Geometry Ranking:** Design 4 (continuing screw + tapering shaft) is expected to perform best for dense metal powders, followed by Design 2, then Design 3, then Design 1. The key principle is that maintaining positive volumetric displacement (active screw flight) all the way to the exit prevents both flooding (for free-flowing powders) and dribble/after-flow, while a tapering shaft provides progressive compression.

**(B) Alternatives:** A decreasing-pitch compression screw, a short discharge tube (L/D ~2-2.5) below the last flight for plug formation, and positioning the auger tip flush with the orifice are well-established design features in commercial loss-in-weight feeders.

**(C) Other Factors:** Gravimetric feedback, motor micro-stepping resolution, and vibration/tapping for bridge-breaking are likely co-dominant with or even more important than exit geometry for achieving tens-of-milligram accuracy.

**(D) Metal Powder Specifics:** Abrasive wear of FDM plastic is a major concern; nylon or CF-nylon and stainless steel bore liners are recommended. High bulk density increases flooding risk. Segregation of blends during screw transport favors dispensing components individually.

**Recommended Primary References:** Engisch & Muzzio (2012, 2015) on pharmaceutical auger filling; Tardos et al. on screw feeder flow models; Roberts & Owen (2003) on screw conveyor design; Jenike (1964) on hopper design; Vock et al. (2019) and Spierings et al. (2016) on metal powder characterization for AM.
