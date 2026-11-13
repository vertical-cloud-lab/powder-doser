Question: ## System context

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


Yes. # Prior-art review and design recommendation

## Executive conclusion

The strongest architecture is **not a miniature camera iris**. It is a two-stage passive interface:

1. a **360°-capture, asymmetric helical lead-in** on the station that rotates the freely supported cartridge into one unique clock angle; then
2. a **spring-closed axial slide gate or face shutter**, opened by the last few millimetres of docking through a station-side annular push ring or cam.

This separates the two difficult functions—angular indexing and powder sealing—and leaves only one broad wiping surface and one static O-ring exposed to powder. A second strong option is a truly coaxial, mating-opened **poppet/non-spill valve**, which eliminates angular indexing if the powder outlet can be moved to the cartridge axis. For the highest containment, a miniature paired-disc/split-butterfly interface is attractive but difficult to manufacture and clean at 5–15 mm.

| Mechanism / prior-art example | Orientation handling | Consumable-side actuator | Fine cohesive powder suitability | Lab 3D-printability | Dominant failure |
|---|---|---|---|---|---|
| Asymmetric helical self-indexer + spring axial shutter | **Actively indexes**: station lead-in helix/chamfer rotates cartridge into one keyed angle during insertion | **No**; passive spring + station geometry | **High** if shutter is simple, wiped, and O-ring sealed | **High**; helical cam, shutter, spring, O-ring are printable/stock | Powder on helix or key can stop full indexing; torque may be too low if cartridge is draggy |
| Annular push-ring poppet, inspired by CPC **NS4/NS6** and other non-spill QDs | **Orientation-agnostic** if station pushes a full 360° ring around nozzle | **No**; mating station depresses poppet/ring | **Med-High** for short travel and smooth seats; better than slit valves for metals | **Med**; poppet and cage printable, but sealing faces/tolerances matter | Powder packs on seat/poppet stem; incomplete reseal or increased opening force |
| Split butterfly / contained transfer: **GEA BUCK**, **ChargePoint AseptiSafe**, **Matcon Cone Valve** | Usually needs **predefined angular docking** or a large mating interface; not rotation-tolerant at small nozzle scale | **No on consumable**, but station/container half is an active mating component | **Very High** for containment and cross-contamination control | **Low** at 5–15 mm nozzle scale; geometry and sealing are hard to miniaturize | Too bulky/complex for cartridge nose; dead volume and cleaning burden |
| Cross-slit / duckbill self-seal; needle-free slit-valve and capless-filler analogs, **Ford Easy Fuel** | **Orientation-agnostic** | **No**; opens by probe pressure | **Low-Med**; good for liquids, poor for dry cohesive powders unless purge/anti-bridge features added | **Low-Med**; requires elastomer molding more than FDM/SLA | Powder wedges slit lips open, moisture traps in slit, tribocharged fines cling |
| Umbrella valve | **Orientation-agnostic** | **No**; opens by central pressure differential or probe | **Low** for dry powder discharge | **Low-Med**; elastomer part usually molded | Low cracking consistency with powder; back-side powder accumulation prevents reseal |
| Spring sliding shutter over outlet | **Orientation-agnostic** if opened by annular station ring; otherwise keyed | **No**; station cam/pin/ring slides shutter | **High** if wiping geometry and minimal pocketing are used | **High** | Rails can pack with powder; wear debris from sliding polymer surfaces |
| Rotary shutter cap (twist-to-open by station cam) | **Needs indexing** unless driven by annular friction ring or symmetric cam | **No**; relative motion from station | **Med-High** with short rotation and positive stop | **High** | Powder in bearing track increases torque; accidental partial-open state |
| Camera iris diaphragm | Usually **orientation-agnostic to station access**, but internal blades do not solve cartridge indexing | **No** if station drives outer ring; spring-return possible | **Low** for fine cohesive metal powder | **Med** for demonstration, **Low** for durable use | Blade gaps leak, blades jam/abrade, trapped fines cause cross-contamination |
| Flexible sleeve iris / sphincter valve | **Orientation-agnostic** | **No**; external collar compresses elastomer sleeve | **Med** for larger bulk solids, **Low-Med** at 5–15 mm with tens-of-microns cohesive powder | **Low-Med**; sleeve likely needs silicone/TPU molding | Sleeve fatigue, powder smearing in folds, cleaning and material compatibility |
| Kinematic couplings / Hirth / spindle / robot tool interfaces: Maxwell/Kelvin KCs, **ISO 7388 BT**, **ISO 12164 HSK**, **ATI QC series**, **SCHUNK SWS** | Mostly **do not actively rotate from arbitrary clock angle**; they **repeatably locate once pre-aligned**. KCs give exact constraint and repeatability but need the intended contacts to engage; AM versions are preload/friction sensitive (penny2019precisionassemblyof pages 1-2, penny2019precisionassemblyof pages 2-4, penny2019precisionassemblyof pages 5-6, penny2019precisionassemblyof pages 6-7, penny2019precisionassemblyof pages 7-8) | N/A as closure; used for docking/indexing, not valve actuation | **High** as docking locators, not as seals | **Med-High** for polymer/metal KC prototypes; literature shows AM KCs are feasible with preload and roughness limits (penny2019precisionassemblyof pages 1-2, penny2019precisionassemblyof pages 2-4, penny2019precisionassemblyof pages 6-7) | Mis-engagement if not pre-indexed; rough AM surfaces, friction, and plastic deformation reduce capture margin and cleanliness (penny2019precisionassemblyof pages 5-6, penny2019precisionassemblyof pages 6-7, penny2019precisionassemblyof pages 7-8) |


*Table: This table compares passive closure and docking concepts for the multi-doser cartridge against the key design criteria: orientation handling, whether the consumable needs its own actuator, suitability for cohesive powder, printability, and dominant failure mode. It highlights why simple shutters with active self-indexing are generally more promising than irises or slit valves.*

## 1. Rotation-agnostic and self-indexing docking

### Kinematic couplings: Maxwell, Kelvin, and quasi-kinematic variants

A Maxwell coupling uses three balls against three V-grooves; a Kelvin coupling uses ball/cone, ball/V, and ball/flat contacts. They provide deterministic six-degree-of-freedom location after the intended contacts have entered their capture regions. They **do not normally rotate a cartridge through an arbitrary clock angle**: a Maxwell pattern has three equivalent angular registrations if symmetric, while an asymmetric pattern simply fails to engage when grossly misoriented. They are therefore final locators, not wide-capture rotary indexers.

Penny and Hart’s *Precision Engineering* paper, DOI **10.1016/j.precisioneng.2019.04.011**, is especially relevant because it demonstrates integral SLA, FFF, SLM, and binder-jetted Maxwell couplings. Polymer versions repeated to approximately 3.2–16.6 μm under controlled preload, but printed asperities plastically deform, friction affects repeatability, and decreasing clearance trades accuracy against failure to engage. Thus a printed kinematic coupling is suitable behind a coarse self-indexer, but its exposed point contacts should not be placed in the powder plume. (penny2019precisionassemblyof pages 1-2, penny2019precisionassemblyof pages 2-4, penny2019precisionassemblyof pages 5-6, penny2019precisionassemblyof pages 6-7, penny2019precisionassemblyof pages 7-8)

**Assessment:** (a) keyed and repeatable, but not arbitrary-angle active indexing; (b) no cartridge actuator, although external preload is required; (c) acceptable only outside the powder path; (d) demonstrably printable; (e) powder on a groove or high friction can prevent complete seating.

### Hirth and curvic face couplings

A **Hirth coupling** has radial face serrations; a **Curvic coupling** uses curved radial teeth. Read Croccolo et al., “On Hirth Ring Couplings: Design Principles Including the Effect of Friction,” *Actuators* 7, 79 (2018), DOI **10.3390/act7040079**. The teeth convert a small angular error into tangential motion as axial preload is applied, but a conventional N-tooth ring has N equivalent registrations and only a limited tooth-pitch capture range. It therefore snaps to the nearest tooth, not to one absolute nozzle angle. One unique angle requires an omitted tooth, unequal tooth sectors, or a separate master key. A low-tooth-count asymmetric face cam can actively rotate the cartridge, but that is a custom indexing cam rather than a standard Hirth interface.

**Assessment:** (a) corrects small phase errors and discretely indexes, but is not uniquely self-indexing over 360° unless made asymmetric; (b) passive; (c) poor if teeth see powder; (d) coarse teeth are SLA/FDM printable; (e) fines packed between face teeth cause false seating and angular error.

### Helical lead-ins and pin-in-slot indexers

The mechanism that actually meets the requirement is an **asymmetric funnel plus helical/ramped keyway**. A station follower first enters a broad annular capture feature; axial insertion then forces relative rotation until one cartridge key reaches a single axial dwell. Use two opposed followers and complementary ramps to avoid cocking, but make one terminal geometry asymmetric so there is only one final state. The cartridge must remain rotationally compliant during this phase; only after indexing should a Maxwell/Kelvin seat or taper clamp it.

This is closely analogous to bayonet mounts, breech-lock closures, Geneva-entry cams, and lead-in keys used by automated tool and cartridge changers. Unlike Hirth teeth, the ramp can provide essentially 360° capture if it is continuous. It is also much more tolerant of FDM/SLA tolerances than fine face splines.

**Assessment:** (a) actively rotates to a unique angle; (b) no onboard actuator—the robot’s axial insertion supplies work; (c) good if the track is shielded and self-draining; (d) excellent; (e) indexing fails if cartridge rotational drag or powder-packed-track torque exceeds the ramp-generated torque.

### Ball-detent holders, machine-tool tapers, and robot tool changers

* **ISO 7388-1/-2** steep-taper tooling (SK/BT families) and **ASME B5.50** CAT tooling use a taper, flange, pull stud, and drive keys. **ISO 12164** HSK uses a hollow taper and face contact with an expanding internal gripper. These accurately seat and transmit torque, but spindle orientation and drive-key alignment are provided beforehand. They do not pick an arbitrary clock angle and rotate the tool into it.
* Ball-detent quick-change holders and locking-ball sleeves accommodate axial insertion and retain a male shank. Unless the interface is rotationally symmetric, their key still requires pre-alignment; the balls themselves do not establish a unique clock angle.
* **ATI Industrial Automation QC-series** robot tool changers use a pneumatically driven locking mechanism with locking balls and tapered alignment features. **SCHUNK SWS** changers similarly lock a tool-side plate to a master side. They tolerate translational and modest angular approach error, but the robot presents a substantially pre-oriented tool. Their pneumatic actuator is on the reusable master side, which is a useful architectural precedent even though the interfaces do not rotate a tool through arbitrary roll.

**Assessment:** (a) final alignment/locking, not active arbitrary-roll correction; (b) station/master-side actuation only is feasible; (c) robust outside the powder zone; (d) simplified tapers and ball locks are printable, precision versions are not; (e) they solve repeatable locking rather than initial rotational ambiguity.

## 2. Self-closing valves opened by the mating fitting

### Double-shutoff non-spill couplings

Commercial examples include **CPC/Colder NS4 and NS6**, **CPC PMC12**, **Stäubli CBI**, **Parker NSI**, and **CEJN 607** families. In the representative architecture, each half contains a spring-loaded poppet. As the halves couple, opposed stems depress both poppets; disconnecting lets both springs close before the seals separate. Many employ keyed latches, but the valve itself is coaxial and rotationally insensitive.

For this instrument, copy the architecture rather than use a liquid coupling unchanged: put a broad, short-stroke mushroom poppet or sliding sleeve in the cartridge and have a 360° station push-ring depress it. Use a soft replaceable face seal, no exposed stem bearing in the powder stream, and a conical or flush interior that drains toward the outlet.

**Assessment:** (a) coaxial version is orientation-independent; (b) only a spring on the cartridge, with opening work supplied by mating; (c) medium-to-high after enlarging clearances and removing liquid-style narrow annuli; (d) printable cage/body plus stock spring and O-ring; (e) a few grains on the elastomer seat can hold the poppet open.

### Needle-free medical connectors and swabable septa

Representative devices include **BD SmartSite**, **ICU Medical MicroClave/Clave**, and **B. Braun Caresite**. A male luer compresses or displaces a normally closed elastomeric slit/septum; elasticity restores closure after withdrawal. The flush external face is intended to be swabbed.

**Assessment:** (a) fully orientation-independent; (b) passive; (c) poor for dry cohesive powder because grains lodge in the slit and the narrow opening promotes bridging; (d) housing is printable, but the slit elastomer requires molding or a purchased insert; (e) slit wedging produces leakage and retained cross-contaminant. This family is better as an environmental secondary seal than as the primary dispensing gate.

### Keg couplers and capless fuel fillers

**Micro Matic D-system/Sankey keg couplers** depress a spring-loaded keg valve while the coupler body supplies the mechanical load. **Ford Easy Fuel** capless fillers, introduced on production vehicles in the late 2000s, use spring-loaded internal flaps opened by a correctly sized fuel nozzle; equivalent systems are sold by other automakers. Both prove that insertion alone can open nested passive closures and that withdrawal can reseal them.

**Assessment:** (a) coaxial and clock-angle independent; (b) passive moving side; (c) a broad flap is more powder-tolerant than a slit but needs a steep, self-cleaning seat; (d) very printable; (e) a side-hinged flap creates a powder-catching hinge pocket and asymmetrical discharge.

### Contained powder-transfer valves

Concrete industrial references are:

* **GEA BUCK Valve**—two mating valve halves for high-containment powder transfer; docking joins the halves before the discs are opened so exposed contaminated surfaces remain controlled.
* **ChargePoint AseptiSafe Bio** and **ChargePoint PharmaSafe**—split butterfly valve systems with active and passive halves for contained/aseptic transfer.
* **Getinge DPTE-BetaBag/Alpha port** systems—docking and transfer interfaces in which a disposable/passive component mates to a reusable port.
* **Matcon Cone Valve**—a cone inside an IBC is raised from its seat at the discharge station; the annular opening promotes mass flow and the cone closes when actuation is removed.
* Dry-disconnect families from **TODO**, **MannTek**, and **Emco Wheaton**—paired valves open only after coupling and close before separation, primarily for fluids rather than powders.

These are the closest contamination-control analogues. Split butterflies retain powder-facing surfaces inside the joined interface, while the Matcon cone avoids a narrow side hinge and provides an annular discharge. However, all are large compared with a 5–15 mm auger outlet.

**Assessment:** (a) normally indexed by docking geometry rather than arbitrary-roll tolerant; a circular mini-cone could be independent of roll; (b) passive container side is possible, with station-side lift/rotation; (c) excellent in principle; (d) difficult at nozzle scale, particularly elastomer overmolding and paired-disc synchronization; (e) excessive part count, dead volume, and cleaning burden.

## 3. Iris and aperture mechanisms

### Camera iris diaphragms

Standard photographic irises use overlapping thin blades pinned to a fixed plate and driven together by a rotating actuator ring. A torsion spring can bias the ring closed; a ratchet or Geneva stop can hold selected apertures. Printable examples reproduce this geometry, but their usefulness demonstrates kinematics—not powder-service durability.

For tens-of-microns metal powder, the closure is intrinsically problematic:

* overlapping blades do not form a hermetic seal;
* fines enter pin slots and blade laps;
* particles trapped between blades increase torque and can buckle printed blades;
* repeated sliding generates polymer or metal wear particulate;
* every overlap is a cross-contamination crevice;
* a ratchet adds teeth and a pawl that can also pack with powder.

A spring return does not cure any of these issues; it may instead snap abrasive grains across the blade surfaces. A ratchet is also unnecessary if the station can hold the actuation ring open during docking and release it on withdrawal.

**Assessment:** (a) the external drive ring can be engaged from any clock angle through a friction collar, but the iris does not orient a side nozzle; (b) passive spring return is possible; (c) low; (d) demonstrator is easy, reliable powder valve is difficult; (e) leakage and jamming at blade overlaps.

### Flexible-sleeve iris/sphincter valves

Industrial **iris valves** for bulk bags and drums use a flexible fabric or elastomer sleeve whose circumference is twisted or constricted. Examples are sold by **Mucon** and **Kemutec** for bulk-solids flow control. These have fewer hard sliding interfaces than camera irises and conform around irregular solids.

At 5–15 mm, however, a sleeve scaled to fine cohesive powder has a very small bore, severe fold curvature, and a large powder-contact area. Hygroscopic powder smears into the folds, and the twisted sleeve is not a reliable moisture barrier unless a second seal is provided.

**Assessment:** (a) rotationally symmetric; (b) external collar can operate it passively; (c) medium for coarse bulk solids, low-to-medium here; (d) body printable but sleeve should be molded silicone/TPU or fabric; (e) fold retention, fatigue, and incomplete cleanout.

## 4. Passive seals, shutters, and plugs

### Duckbill and cross-slit valves

Commercial elastomer suppliers **Vernay**, **Minivalve**, and **Da/Pro Rubber** offer duckbill, umbrella, and cross-slit check valves. Duckbills open under differential pressure; cross-slits open around an inserted probe. Both are compact and insensitive to clock angle.

For gravity/auger-discharged cohesive powder, available pressure is low and irregular. A duckbill can bridge shut; a probe-opened cross-slit avoids pressure dependence but traps grains in its lips. Neither should be the sole moisture seal after abrasive metal powder has cycled through it.

**Assessment:** (a) orientation-independent; (b) passive; (c) low-to-medium; (d) purchased silicone insert preferred; (e) grains prevent full lip closure.

### Umbrella valves

An umbrella valve seals an annular seat with a flexible central stem and lifts under pressure. It is excellent for low-cost gas/liquid check service but provides the wrong flow geometry for powder: solids collect beneath the umbrella and around the stem.

**Assessment:** (a) orientation-independent; (b) passive; (c) low; (d) housing printable, elastomer purchased/molded; (e) a retained powder bed prevents reseating.

### Spring-energized sliding shutter

This is the most favorable simple closure. A flat or slightly cylindrical gate slides across the outlet under a compression or constant-force spring. During docking, a fixed cam, wedge, or annular push collar retracts the gate; withdrawal releases it. The final closing motion can wipe across a replaceable UHMWPE/PTFE lip or O-ring land. Put rails and spring on the clean side, provide through-open drain slots rather than blind pockets, and make the gate removable without tools.

**Assessment:** (a) fully orientation-independent with a circumferential push collar, or usable after self-indexing with a local cam; (b) no powered module actuator; (c) high if bearing surfaces are shielded; (d) excellent; (e) powder can pack into guide rails or become pinched across the sealing land.

### Rotary shutters and press-fit plugs

A rotary shutter places holes in two discs into or out of register. It is easily printed and can be driven by a station pin in a circumferential cam slot. A spring can bias it closed, but the annular bearing and overlapping faces retain powder. A click-in plug or tethered snap cap gives a superior static seal but ordinarily needs a manipulator to remove and replace it; a docking socket could capture the plug, but retention errors make it less fail-safe.

**Assessment:** (a) rotary shutters need an annular drive or prior indexing; plugs can be coaxial; (b) passive relative-motion operation is possible; (c) medium-high for shutters, high while a plug is correctly seated; (d) excellent; (e) rotary-track packing or failure to recapture/reseat the plug.

## 5. Relative-motion-only opening in automated instruments

Pipette systems from **Opentrons**, **Hamilton**, and **Tecan** provide the relevant design pattern rather than a directly reusable sealed powder part. Pipette tips are attached by axial interference or locking features and released by a station/pipette-side ejector sleeve. Reagent cartridges in analytical instruments similarly use insertion ramps, puncture pins, sliding septum openers, foil piercers, and compliant snap latches. The consumable contains only molded geometry and, at most, an elastic return feature.

For the dosing cartridge, the direct translation is:

1. robot inserts cartridge into an oversized funnel;
2. an annular follower engages regardless of clock angle;
3. a helical slot converts insertion into indexing rotation;
4. a keyed dwell and coarse kinematic seat establish the final pose;
5. only then does a station pin or push ring move the shutter;
6. on withdrawal, the shutter spring closes before the indexing key disengages.

That sequence gives a valuable **close-before-release interlock**. A compliant bistable latch can reduce holding force, but a monostable spring-closed gate is safer: loss of docking force always closes it.

## Ranked shortlist

### 1. Asymmetric helical self-indexer plus spring-closed axial shutter

**Why first:** It directly handles a side outlet at an arbitrary initial clock angle, uses only docking motion, is easy to print, permits a broad wiped sealing land, and keeps precision locating features separate from powder sealing.

**Prototype details:** 360° coarse capture funnel; two opposed helical followers; one asymmetric terminal key; 30–45° ramp angle after friction testing; replaceable polished shutter insert; compression spring; radial O-ring or flat silicone face gasket; drain-through guide geometry. Allow the cartridge to rotate freely until the final seat engages.

**Read first:** Penny & Hart, DOI **10.1016/j.precisioneng.2019.04.011**, for printable final locating interfaces and preload/roughness limits; Croccolo et al., DOI **10.3390/act7040079**, for face-tooth indexing and friction. Printed contact surfaces deform initially and then stabilize, so a controlled break-in cycle and consistent preload are appropriate. (penny2019precisionassemblyof pages 5-6, penny2019precisionassemblyof pages 6-7)

### 2. Coaxial annular push-ring poppet patterned after non-spill QDs

**Why second:** If the dispensing path can terminate on the cartridge axis, it is inherently insensitive to roll. Mating opens it and a stock spring closes it before separation. It has fewer powder traps than an iris.

**Read/inspect first:** **CPC NS4/NS6**, **Stäubli CBI**, **Parker NSI**, and **CEJN 607** cutaways. Do not copy their liquid-scale stem clearances; use a short, broad poppet with the guide and spring on the clean side.

### 3. Miniature paired-disc/split-butterfly or lifting-cone interface

**Why third:** This offers the best containment and cross-contamination logic where toxic/reactive powders justify complexity. A circular lifting cone can be roll-independent; a split butterfly usually requires indexed docking.

**Read/inspect first:** **GEA BUCK Valve**, **ChargePoint AseptiSafe Bio/PharmaSafe**, and **Matcon Cone Valve**. Use these as architectural references, not scale copies. The likely limiting issue is reliable elastomer sealing and cleanability at a 5–15 mm bore.

## Final disposition of the iris proposal

A ratcheted, spring-return iris is mechanically feasible but should rank below all three shortlisted approaches. It combines the worst powder-service features—multiple blade gaps, sliding abrasive contacts, inaccessible overlap crevices, and a powder-exposed ratchet—without producing a true moisture seal. If retained for experimentation, omit the ratchet, let the station hold a spring-return actuator ring open, and place a separate elastomer cap or shutter upstream for storage sealing. The iris should regulate flow, not serve as the primary containment closure.

References

1. (penny2019precisionassemblyof pages 1-2): Ryan W. Penny and A. John Hart. Precision assembly of additively manufactured components using integral kinematic couplings. Precision Engineering, 60:104-115, Nov 2019. URL: https://doi.org/10.1016/j.precisioneng.2019.04.011, doi:10.1016/j.precisioneng.2019.04.011. This article has 13 citations.

2. (penny2019precisionassemblyof pages 2-4): Ryan W. Penny and A. John Hart. Precision assembly of additively manufactured components using integral kinematic couplings. Precision Engineering, 60:104-115, Nov 2019. URL: https://doi.org/10.1016/j.precisioneng.2019.04.011, doi:10.1016/j.precisioneng.2019.04.011. This article has 13 citations.

3. (penny2019precisionassemblyof pages 5-6): Ryan W. Penny and A. John Hart. Precision assembly of additively manufactured components using integral kinematic couplings. Precision Engineering, 60:104-115, Nov 2019. URL: https://doi.org/10.1016/j.precisioneng.2019.04.011, doi:10.1016/j.precisioneng.2019.04.011. This article has 13 citations.

4. (penny2019precisionassemblyof pages 6-7): Ryan W. Penny and A. John Hart. Precision assembly of additively manufactured components using integral kinematic couplings. Precision Engineering, 60:104-115, Nov 2019. URL: https://doi.org/10.1016/j.precisioneng.2019.04.011, doi:10.1016/j.precisioneng.2019.04.011. This article has 13 citations.

5. (penny2019precisionassemblyof pages 7-8): Ryan W. Penny and A. John Hart. Precision assembly of additively manufactured components using integral kinematic couplings. Precision Engineering, 60:104-115, Nov 2019. URL: https://doi.org/10.1016/j.precisioneng.2019.04.011, doi:10.1016/j.precisioneng.2019.04.011. This article has 13 citations.