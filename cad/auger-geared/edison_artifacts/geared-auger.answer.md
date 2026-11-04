<!-- Edison task 5afb6d0d-8b38-436b-a23c-9184d1c28a83 via job-futurehouse-paperqa3-high -->

Question: We are designing a 3D-printed metering auger for a low-cost benchtop powder
dispenser ("powder-doser"). The auger is a vertical hollow cylinder (OD 25 mm,
ID 21 mm, length 250 mm) with an internal Archimedean screw (Ø8 mm central
shaft, 10 mm-pitch single-start helical fin, 2 mm fin thickness) and a conical
exit funnel + Ø3 mm exit hole at the bottom. The original design (PR #16) is
driven directly by an M3 spindle that screws into a boss above a top loading
cap.

The v2 ask (issue #48, comment 4513155870) was to add an EXTERNAL spur-gear
band wrapped around the auger about one-third of the way from the dispensing
end, so the auger can be rotated by a NEMA 11 stepper motor mounted alongside
the auger (parallel-axis offset drive). The external gear-band must not
interfere with the internal Archimedean screw, the bore, the exit funnel, or
the top cap loading slots. The print-and-test cycle produced two specific
failure modes that motivate this query:

1. (v1) Building the gear band as `linear_extrude(spur_gear_2d(...))` with
   spur_gear_2d returning a filled root-circle disc sealed the auger bore at
   the gear-band's axial slice, turning a hollow metering tube into a closed
   cup. v2 fixed this by making spur_gear_2d optionally return an annular
   2-D shape (root-circle minus bore circle), so the bore stays open through
   the gear's axial slice.
2. (v1) Choosing a Z_p/Z_g pair that minimised gear-band radius produced a
   centre distance C = 21 mm at module m = 1 mm. With the auger OR = 12.5 mm
   and the NEMA 11 frame extending 14.1 mm from its shaft axis, the motor
   body would have intersected the auger tube by 5.6 mm. v2 fixed this by
   picking Z_p = 16, Z_g = 48, m = 1.0 -> C = 32 mm, leaving a 5.4 mm radial
   air gap between the auger OD and the motor body face.
3. (v2) An over-aggressive copy of the PR #16 v5 file (which had previously
   removed the central shaft + helix to avoid stringing during a single H2D
   FDM test print) left the geared auger with an empty bore and no
   Archimedean lift; v3 re-introduced the v4.1-era shaft + helix sweep as a
   single linear_extrude with proportional twist so the helical surface is
   continuous from the funnel mouth through the gear-band z-range up to the
   underside of the top cap.

Please conduct a thorough literature review covering, with explicit citations:

(a) Design and analysis of plastic 3D-printed spur gears for low-torque,
    low-RPM intermittent service (e.g. PLA / PETG, module 0.5-2 mm, FDM 0.4
    mm nozzle). What tooth-form choices (full-depth vs stub, profile-shift,
    addendum modification, fillet radius), pressure angles, face widths, and
    backlash budgets does the literature recommend for printed gears in this
    size class? How does the literature characterise wear and dimensional
    drift versus injection-moulded counterparts?

(b) Parallel-axis offset drive of vertical metering augers / screw feeders.
    What centre-distance, gear-ratio, and reduction-stage choices appear in
    the powder-handling, pharmaceutical-feeder, and additive-manufacturing-
    powder-dosing literature for the 0.01-10 g/s dosing regime? Are there
    published failure modes specific to driving a screw feeder through an
    external gear band (e.g. gear-induced vibration coupling into bridging
    or rat-holing of cohesive powders, eccentric loading on the screw
    spindle bearing)?

(c) Single-flight Archimedean screw feeders for cohesive powders (xanthan
    gum, flour, fine ceramic / metal powders). What design rules exist for
    pitch, fin thickness, flight clearance, and shaft diameter as a function
    of particle d50 and Hausner ratio? What is the published evidence on the
    relative metering accuracy of (i) screw rotation alone vs (ii) screw
    rotation + percussive de-bridging (solenoid tap) vs (iii) screw +
    vibration-motor agitation, for sub-gram dosing accuracy?

(d) NEMA 11 (28 mm frame) stepper motor selection for benchtop metering /
    autotrickler-class powder dispensers. What torque, microstepping, and
    closed-loop strategies appear in the published literature for accurate
    sub-gram metering, and what gear reductions are typical for the 28-32 mm
    stepper class driving a vertical screw feeder?

(e) Print-orientation and slicer-setting recommendations for a tall (>= 180
    mm) printed hollow auger with an internal helical fin printed without
    inner-fin support material -- specifically, the trade-off between
    printing the auger vertically (long unsupported helical bridges at the
    fin's inner edge) vs printing in segments and bonding/threading them.

Where the literature is sparse, please note that explicitly and identify
relevant adjacent prior art (vending dispensers, salt cellars, lab-scale
mass-flow controllers, etc.) along with their key design parameters.


# Literature Review: 3D-Printed Gear-Driven Metering Auger for a Low-Cost Benchtop Powder Dispenser

## (a) Design and Analysis of 3D-Printed Spur Gears for Low-Torque, Low-RPM Service

### Tooth Form, Pressure Angle, and Geometry

The dominant tooth form in the FDM-printed gear literature is the standard full-depth involute profile. Hasan et al. (2024) designed module-1 spur gears following ISO 6336, with addendum 1.0 mm, dedendum 1.25 mm, tooth thickness 1.57 mm, and tip/root clearance of 0.25 mm (hasan2024technicalassessmentof pages 6-9). Pisula et al. (2021) generated involute profiles per ISO 53:1998 using a rack-profile approach with addendum coefficient 1.0, dedendum coefficient 1.25, and a root-radius coefficient of 0.200, with no profile shift applied (pisula2021ananalysisof pages 2-4). Zhang (2020) used module-2, 30-tooth gears with a contact ratio of 1.65 and tooth thickness of 3.14 mm (zhang2020intelligentmanufacturingapplied pages 42-46). Across these studies, a 20° pressure angle is the standard choice for FDM spur gears. One exception is Bezzini et al. (2026), who adopted a 25° pressure angle at module 1.2 for a compact 3D-printed compound planetary gearbox intended for wearable robotics, where the increased pressure angle reduces tooth bending stress at the expense of higher radial bearing loads (bezzini2026designandexamination pages 3-4).

No published study was found that explicitly recommends profile-shift coefficients or addendum modification specifically for FDM-printed polymer gears. However, the relevant standards—ISO 6336 for load capacity and VDI 2736 for thermoplastic gear design—are consistently referenced as the baseline for polymer gear calculation (hasan2024technicalassessmentof pages 27-30). The absence of FDM-specific profile-shift guidance represents a notable gap; designers are advised to use VDI 2736 as a starting point and add empirical compensation for print shrinkage and surface roughness.

### Backlash Budgets and Face Widths

Reported backlash values for FDM gears cluster in the 0.18–0.20 mm range. Zhang (2020) specified a nominal backlash of 0.18 mm (zhang2020intelligentmanufacturingapplied pages 42-46), while Pisula et al. (2021) assumed a circumferential backlash of 0.20 mm (normal backlash 0.188 mm) (pisula2021ananalysisof pages 2-4). Netto (2022) used a clearance/backlash of 0.2 mm for screw-extruder gearing (netto2022developmentofan pages 100-103). Face widths ranged from 10 mm (Hasan et al. 2024, Agca & Tunalioglu 2024) to 15 mm (Zhang 2020) (hasan2024technicalassessmentof pages 6-9, agca2024experimentalinvestigationof pages 2-5, zhang2020intelligentmanufacturingapplied pages 42-46). For the described powder-doser gear band at module 1.0, a face width of 6–10 mm and a backlash allowance of 0.2–0.3 mm appear consistent with the literature, given the additional dimensional variability introduced by FDM.

### Dimensional Accuracy and Quality Class

FDM-printed gears exhibit significantly lower dimensional precision than injection-moulded counterparts. Zhang (2020) inspected FDM nylon gears on a Klingenberg ZPK 260 gear measuring machine and reported a quality class of DIN 12 (BS D), which is substantially coarser than injection-moulded polymer gears that routinely achieve DIN 9–10 (zhang2020intelligentmanufacturingapplied pages 42-46). Measurable "bottom shrinkage" (peeling at the build plate interface) was observed during printing, and shrinkage factors of 0.5–3% are typical for FDM parts depending on material (zhang2020intelligentmanufacturingapplied pages 114-118, karalus2026researchanddesign pages 17-21). No established precision or wear-limit standards exist specifically for 3D-printed gears (hasan2024technicalassessmentof pages 4-6). Higher infill percentage was identified as the single most influential factor for gear performance and rigidity, directly affecting backlash stability (zhang2020intelligentmanufacturingapplied pages 114-118).

### Wear Versus Injection-Moulded Counterparts

FDM-printed gears consistently show shorter service life than injection-moulded equivalents under identical test conditions. Hasan et al. (2024) tested at 1.5 Nm and 1500 rpm and found virgin PLA (vPLA) gears lasted 11.82 × 10⁵ cycles versus 16.52 × 10⁵ for injection-moulded PLA and 20.25 × 10⁵ for injection-moulded nylon—a roughly 28% and 42% deficit, respectively (hasan2024technicalassessmentof pages 19-21). Recycled PLA performed worst at 7.33 × 10⁵ cycles. One comparative synthesis noted that injection-moulded POM achieved approximately 2 million rotations, far exceeding any FDM material (agca2024experimentalinvestigationof pages 2-5). Among FDM materials, PETG has been reported as having the highest wear resistance in some studies, with PLA showing approximately 12% better durability than ABS (hasan2024technicalassessmentof pages 4-6). PEEK printed by FDM showed the best abrasive-wear resistance among tested materials (pisula2021ananalysisof pages 2-4). The primary failure mode for FDM gears is tooth bending followed by fracture, preceded by increases in temperature and noise (hasan2024technicalassessmentof pages 19-21). Wear initiates at the outer shell of the printed part and progresses inward toward lower-density infill regions (agca2024experimentalinvestigationof pages 2-5).

The following table summarises the key published design parameters:

| Study | Gear / material context | Module | Pressure angle | Backlash / clearance reported | Face width | Tooth-form / profile notes | Wear / durability vs injection-moulded reference |
|---|---|---:|---:|---|---:|---|---|
| Hasan 2024 | FDM spur gears in recycled PLA, blended PLA, virgin PLA; compared with IM-PLA and IM-nylon | 1.0 | 20° | Tip/root clearance 0.25 mm reported; no explicit backlash value given | 10 mm | ISO 6336-based spur gear; addendum 1.0 mm, dedendum 1.25 mm, tooth thickness 1.57 mm | IM gears outperformed printed gears: at 1.5 Nm and 1500 rpm, service life was rPLA 7.33×10^5 cycles, blend 10.48×10^5, vPLA 11.82×10^5, IM-PLA 16.52×10^5, IM-nylon 20.25×10^5; printed PLA had comparable hardness but generally worse wear/life than IM references (hasan2024technicalassessmentof pages 6-9, hasan2024technicalassessmentof pages 21-24, hasan2024technicalassessmentof pages 19-21) |
| Pisula 2021 | FDM/FFF involute spur gears in ABS, ULTEM 9085, PEEK | 3.0 | 20° | Circumferential backlash 0.20 mm; normal backlash 0.188 mm | 14 mm (driving), 12 mm (driven) | Rack-profile involute per ISO 53:1998; no profile shift; addendum coeff. 1.0, dedendum coeff. 1.25, root-radius coeff. 0.20 | No IM comparator in the reported test; among printed polymers, PEEK had best wear resistance/dimensional stability, ABS worst (pisula2021ananalysisof pages 2-4) |
| Zhang 2020 | 3D-printed nylon spur gears; one injection-moulded reference included | 2.0 | 20° | Nominal backlash 0.18 mm | 15 mm | 30 teeth, tooth thickness 3.14 mm, contact ratio 1.65; gears inspected to DIN 12 quality class; performance strongly affected by infill and print parameters | Nylon 618 compared favorably to IM gear at low-medium torque; FDM parts showed shrinkage/“bottom shrinkage” and need conservative tolerance allowance; higher infill improved rigidity and backlash stability (zhang2020intelligentmanufacturingapplied pages 114-118, zhang2020intelligentmanufacturingapplied pages 42-46) |
| Agca 2024 | FDM spur gears in PLA, PETG, ABS with varied shell thickness and infill | 6.0 | 20° | Not reported | 10 mm | Geometry generated in CAD; study focused on shell thickness and infill effects rather than tooth modifications | Literature synthesis in the paper notes printed PLA gears can exceed 300,000 rotations at 100% infill, but injection-moulded POM cited at ~2 million turns; printed gear wear initiates at shell and progresses inward (agca2024experimentalinvestigationof pages 2-5, agca2024experimentalinvestigationof pages 1-2) |
| Bezzini 2026 | 3D-printed compound planetary gearbox (not spur pair, but relevant polymer AM gearing benchmark) | 1.2 | 25° | Not reported | Not reported in excerpt | Planetary stages: ring A 48 / planet A 16 / sun A 16; ring B 45 / planet B 13; design driven by printability and packaging constraints | No IM wear comparison reported; useful mainly as evidence that 25° pressure angle and ~module-1.2 gearing are used in compact 3D-printed polymer transmissions (bezzini2026designandexamination pages 3-4) |


*Table: This table summarizes reported gear geometry and performance parameters from key studies on 3D-printed polymer gears. It is useful for benchmarking module, pressure angle, backlash, and expected wear performance when selecting a spur-gear band for a low-torque printed auger.*

### Practical Recommendations for the Described Gear Band

For the powder-doser's external spur-gear band (module 1.0, Z_g = 48), the literature supports: a 20° pressure angle full-depth involute per ISO 6336 / VDI 2736, 100% infill at the gear teeth with 0.3 mm or finer layer height, a backlash allowance of ≥0.2 mm to account for FDM dimensional scatter, PETG as the preferred material for low-torque intermittent service given its superior wear resistance and lower warping tendency (hasan2024technicalassessmentof pages 4-6, karalus2026researchanddesign pages 21-25), and printing the gear teeth with their axis vertical (faces on the XY plane) to maximise tooth-profile fidelity (hasan2024technicalassessmentof pages 6-9).

---

## (b) Parallel-Axis Offset Drive of Vertical Metering Augers

### Literature on Gear-Driven Screw Feeders

The published literature on driving a vertical screw feeder through an external gear band is sparse. The closest directly documented example is the vertical loss-in-weight feeder prototype by El Kassem et al. (2021), which employed parallel-axis drives for both auger and stirrer. The stirrer was driven via a toothed-pulley transmission with a 1:2 ratio, while the auger was coupled through a rigid Torx-type coupling. A gear train with 55-tooth and 15-tooth gears (approximately 3.67:1 ratio) linked the auger to three whisk-type stirrers, yielding roughly 733 rpm on the stirrer when the auger ran at 200 rpm (kassem2021designofa pages 15-16). The auger shaft was supported by two deep-groove ball bearings for combined axial and radial loads, and small auger geometries (3–10 mm OD) with a conical profile were used to improve dosing accuracy (kassem2021designofa pages 4-6). Servomotors with 0.5 Nm standstill torque at 48 V were used (kassem2021designofa pages 4-4).

### Documented Failure Modes

El Kassem et al. (2021) reported two critical failure modes directly relevant to the described powder-doser design. First, high vibrations from the rigid screw coupling transmitted through the gear train to the load cell, causing repeatable weight-peak variability in dosing measurements. The authors recommended replacing the rigid coupling with an elastomer polymer coupling to ensure centricity, damp vibrations, and provide backlash-free torque transmission (kassem2021designofa pages 15-16). Second, stalling of the stirrer when processing micronized paracetamol (a highly cohesive powder), as the 0.5 Nm motor torque was insufficient to overcome cohesive blocking forces (kassem2021designofa pages 15-16). These observations confirm the risk of gear-induced vibration coupling into powder bridging and the need for sufficient torque margin when driving through an external gear band.

### Adjacent Prior Art: Toner Cartridge Augers

The closest mass-produced analogue of an externally gear-driven auger is the laser-printer toner cartridge. In Brother's image-forming apparatus (EP1927897B1), feed augers and return augers are rotationally driven via gear portions provided at the end of rotating shafts, which mesh with a drive motor's gear train in the printer main body. Intermediate gears transmit torque through the cartridge-body interface to internal agitators and toner-conveying screws (EP1927897B1 pages 16-17, EP1927897B1 pages 15-16, EP1927897B1 pages 11-12). This architecture—external gear engagement on an auger shaft driving internal helical transport—is directly analogous to the described powder-doser design, though at much smaller powder volumes and with injection-moulded gears rather than printed ones.

### Centre-Distance and Motor-Clearance Considerations

No published formula or standard was found that specifically addresses centre-distance selection for an external gear band on a metering auger. The design constraint identified in the user's v2 fix—ensuring the motor body does not intersect the auger tube—is a packaging problem that depends on the motor frame dimension, the auger OD, and the gear centre distance C = m(Z_p + Z_g)/2. The v2 solution of Z_p = 16, Z_g = 48, m = 1.0 (C = 32 mm) providing a 5.4 mm radial clearance is consistent with the general approach of using a higher gear ratio to increase centre distance, which also provides beneficial speed reduction for the auger.

---

## (c) Single-Flight Archimedean Screw Feeders for Cohesive Powders

### Design Rules for Screw Geometry

The review literature on screw feeders identifies the key geometric parameters as screw diameter (D), shaft diameter (d), pitch (P), flight thickness, and radial clearance to the housing. Hou (2024) provides the theoretical mass flow relationship: ṁ_p = F·ρ·V·C, where V = P·ω, and F depends on (D² − d²), with correction factors for inclination (C) and filling coefficient (φ) (hou2024developmentofa pages 97-101). A practical guideline states that pitch should exceed one-half the flight height to avoid logging (hou2024developmentofa pages 97-101).

Minglani et al. (2020) reviewed experimental findings showing that the pitch-to-blade-diameter ratio (P/D_B) strongly affects throughput for cohesive materials, with higher ratios generally increasing capacity (minglani2020areviewof pages 4-6). Tip (flight) clearance increases volumetric efficiency but also increases specific power requirements (minglani2020areviewof pages 4-6, minglani2020areviewof pages 6-7). For DEM validation work, Minglani et al. (2021) used a screw with D_B = 30 mm, shaft D_S = 14 mm (d/D ≈ 0.47), pitch = 30 mm (P/D = 1.0), blade thickness 1 mm, and casing clearance approximately 1 mm (minglani2021analysisofflow pages 2-3). The experimental feeder used D = 88 mm with a shaft diameter of 44 mm (d/D = 0.5), also with P/D = 1.0 and approximately 1 mm clearance (minglani2021analysisofflow pages 2-3).

For the described auger (Ø8 mm shaft inside Ø21 mm bore, d/D = 0.38, with 10 mm pitch giving P/D ≈ 0.48 relative to the bore), the pitch-to-diameter ratio is lower than typical industrial values (0.5–1.0), which may limit throughput but is appropriate for metering small quantities. The 2 mm fin thickness is thick relative to the 1 mm used in DEM studies but suitable for FDM printing resolution.

### Screw Profiles for Cohesive Materials

For cohesive and sticky powders, Malm (2021) identifies several screw geometries: helix types for low-to-medium density powders, centre-shaft designs that provide better mechanical stability (relevant to the described design), full-flight screws that block "shooting" (uncontrolled flow), and double-concave screws specifically for very cohesive, sticky powders (malm2021evaluatingtheoreticaland pages 34-39). Shaftless screws are recommended for sticky or high-moisture cohesive powders because they reduce clogging, though they sacrifice mechanical stability (hou2024developmentofa pages 97-101). Flow aids—including vibrators, agitators, and air injectors—are commonly incorporated to improve screw fill efficiency and feed-rate consistency (hou2024developmentofa pages 97-101).

### Flowability Characterisation

While the Hausner ratio is a standard bulk flowability metric (ratio of tapped to poured density), no explicit lookup table mapping Hausner ratio to screw-geometry recommendations was found in the literature. Instead, more sophisticated characterisation is recommended: Clayton (2019) demonstrated that FT4 powder rheometer metrics (Flow Rate Index and Specific Energy) predicted volumetric feed rate in screw feeders with R² = 0.95, outperforming simple bulk density measures (clayton2019anintroductionto pages 28-31). Li (2020) found that conditioned bulk density (cBD) strongly correlated with maximum achievable feed rate ("feed factor") for a given screw type, enabling prediction without extensive feeder trials (li2020predictiveperformanceof pages 36-40). Malm (2021) describes compressibility, permeability, wall friction, and shear-cell-derived parameters (cohesion, unconfined yield stress, Flow Function) as the properties that should inform geometric and operational choices (malm2021evaluatingtheoreticaland pages 28-34).

### Metering Accuracy: Screw Alone vs. Percussive vs. Vibration

**Screw rotation alone** is a volumetric metering method whose accuracy is fundamentally limited by variability in powder packing density and is sensitive to humidity, electrostatics, and batch-to-batch particle-size differences (yang2007meteringanddispensing pages 4-6). Auger feeders show an increased tendency to clog as they become miniaturised (yang2007meteringanddispensing pages 9-10). Typical small-screw delivery rates span 2 × 10⁻⁸ to 2 × 10⁻⁴ m³/h (yang2007meteringanddispensing pages 6-7). For sub-gram accuracy, pure volumetric screw feeding is generally insufficient without gravimetric feedback.

**Vibration-assisted dispensing** controls flow by breaking arches and domes in cohesive powders. Yang & Evans (2007) note that flow rate in lateral vibration is controlled by interruption of downward particle motion at the wall, and that flow rate is inversely proportional to vibration amplitude (yang2007meteringanddispensing pages 9-10). Ultrasonic vibratory approaches have achieved flow rates down to 10 μg/s and individual doses of tungsten carbide powder as small as 50 μg (yang2007meteringanddispensing pages 9-10). The Xcelodose system uses a screen that prevents gravity flow and applies controlled vibrations to reduce interparticle friction and cause discharge, with dose uniformity depending on particle size, bridging tendency, and applied taps (pinzon2012modellingofdosator pages 34-38).

**Percussive de-bridging** (solenoid taps) was not explicitly studied as a standalone technique in any recovered paper. However, the concept is implicit in Yang & Evans' (2007) discussion of "attack waveform" methods that break domes, and in the Xcelodose system's use of controlled taps to initiate flow through a restrictive orifice (pinzon2012modellingofdosator pages 34-38). Hopper vibration amplitude strongly affects screw feeder feed-rate variation, suggesting that even low-amplitude percussive impulses can significantly alter flow behaviour (yang2007meteringanddispensing pages 6-7).

**Gravimetric hybrid approaches** consistently emerge as the preferred solution for sub-gram accuracy. A powder-pipette robot dispensed 5–25 mg gravimetrically with less than 2% error, and a resonant-frequency balance device measured doses below 100 μg with approximately 3% standard-deviation error (yang2007meteringanddispensing pages 10-12). Combined volumetric–gravimetric systems, where a screw or piston feeder is paired with a weighing sensor for closed-loop control, offer the volumetric convenience with gravimetric accuracy (yang2007meteringanddispensing pages 4-6, fathollahi2020performanceevaluationof pages 1-2).

---

## (d) NEMA 11 Stepper Motor Selection for Benchtop Powder Metering

### Literature Landscape

No published paper was found that specifically evaluates NEMA 11 (28 mm frame) stepper motors for powder metering or autotrickler applications. The literature on stepper-driven powder feeders predominantly uses NEMA 17 (42 mm frame) motors. Drotman (2015) used a NEMA 17 stepper with an A4988 driver to directly drive a pellet-feed auger (L = 129 mm, pitch = 11.56 mm, Ø6.35 mm), noting the importance of current limiting and heatsinking (drotman2015designofa pages 19-27). The autotrickler community (precision ammunition reloading) is active but publishes primarily in forums and open-source repositories rather than peer-reviewed literature.

### Microstepping and Torque Trade-offs

Benasso (2018) provides a detailed analysis of microstepping trade-offs directly applicable to NEMA 11 motor selection. A 200-step/rev motor at 32× microstepping yields 6400 steps/rev and 0.00368 mm/step resolution in a filament-drive context, but holding torque is reduced by approximately 95% (e.g., from ~500 mN·m to ~25 mN·m per microstep) (benasso2018artifactsinfdm pages 66-71). If the load torque exceeds the incremental torque of a microstep, multiple microsteps accumulate before motion occurs, producing slip and oscillation. The solution proposed is to use a lighter pancake motor with a gear reduction: a 400-step motor with a 3:1 gear (Titan-style) reduces the required microstepping from 32× to 8×, yields an effective resolution of 9600 steps/rev (0.00254 mm/step), and divides the load torque by the gear ratio (benasso2018artifactsinfdm pages 66-71). This directly supports the powder-doser's 3:1 gear ratio (Z_p = 16, Z_g = 48) as appropriate for a NEMA 11 motor driving a metering auger.

### Motor Sizing and Torque Requirements

El Kassem et al. (2021) used servomotors with 0.5 Nm standstill torque for a vertical loss-in-weight feeder with 3–10 mm OD augers, and found this torque was insufficient to overcome blocking forces from micronized paracetamol (kassem2021designofa pages 4-4, kassem2021designofa pages 15-16). Typical NEMA 11 stepper motors provide 50–100 mN·m holding torque (roughly 5–10 N·cm). With a 3:1 gear reduction, the effective torque at the auger becomes 150–300 mN·m, which should be adequate for the low-torque regime of the described 8 mm shaft / 21 mm bore auger with free-flowing to moderately cohesive powders, but may be marginal for highly cohesive materials.

### Closed-Loop Strategies

For precision powder metering, the literature strongly favours gravimetric closed-loop control. Loss-in-weight (LiW) systems continuously monitor the mass on a scale and adjust motor speed to maintain a target feed rate, switching to volumetric mode only during hopper refill (li2020predictiveperformanceof pages 36-40, malm2021evaluatingtheoreticaland pages 34-39). The weighing platform used by El Kassem et al. (2021) had 15 kg capacity with 20 mg resolution and 80 mg half-load linearity deviation; cable routing and vibration isolation from the motor were critical design constraints (kassem2021designofa pages 4-4). Dual-stage feed-drive concepts (coarse stepper + fine piezo actuator with encoder feedback) have achieved positioning errors below 1 μm in machine-tool applications, suggesting a potential architecture for ultra-precise powder metering (chasti2021novelmachinetool pages 63-68).

---

## (e) Print Orientation and Slicer Settings for a Tall Hollow Auger with Internal Helical Fin

### Vertical Printing: Bridging and Overhang Constraints

Printing the auger vertically (long axis parallel to the Z axis) keeps the circular cross-section in the XY plane, which is ideal for maintaining cylindrical wall concentricity and gear-tooth profile accuracy at the gear-band slice. However, the internal helical fin presents an overhang challenge. Jackson et al. (2022) report overhang limits of 45° from vertical for large-scale material extrusion (BAAM) and note that exceeding overhang limits causes poor build quality or failure (jackson2022additivemanufacturingdesign pages 25-28). For desktop FDM with a 0.4 mm nozzle, community experience suggests overhang limits of approximately 45–60° for PLA and PETG. The helical fin's angle depends on the pitch-to-diameter ratio; for the described auger (10 mm pitch, ~21 mm bore), the helix angle at the bore wall is arctan(P / πD) ≈ arctan(10 / π × 21) ≈ 8.6° from horizontal, meaning the fin's inner edge presents a nearly horizontal overhang—well beyond typical unsupported-overhang limits.

Bridging distances measured experimentally include 1.85 inches (47 mm) for CF-ABS with a 0.3-inch nozzle and 2.25 inches (57 mm) with a 0.2-inch nozzle (jackson2022additivemanufacturingdesign pages 34-36). For the described auger's internal fin spanning from the Ø8 mm shaft to the Ø21 mm bore wall, the unsupported bridge span at the fin's inner edge is approximately 6.5 mm—well within typical bridging limits if the fin is treated as a bridge between the shaft and the wall. However, the helical progression means each layer's fin position rotates, creating a continuously shifting bridge that may sag without support.

### Material Considerations

PLA has low warping tendency and can be printed without a heated bed but is brittle under cyclic loading. PETG offers better dimensional stability, layer adhesion, and minimal warping, though it can cause stringing (karalus2026researchanddesign pages 21-25). Shrinkage factors range from 0.5% to 3% depending on material and cooling conditions; rapid cooling causes warping, particularly problematic for tall parts (karalus2026researchanddesign pages 17-21). For a 250 mm tall auger, even 1% axial shrinkage represents 2.5 mm of dimensional error in overall length.

### Segmented Printing and Bonding

Jackson et al. (2022) recommend that holes and cavities are "best oriented with their cross-section in the horizontal plane or should be eliminated from the print and then added in a post-process" (jackson2022additivemanufacturingdesign pages 25-28). This supports printing the auger in segments—for example, 3–4 sections of 60–85 mm each—with threaded, pinned, or adhesive-bonded joints. Wall thicknesses should be even multiples of bead width to minimise starts/stops and defects (jackson2022additivemanufacturingdesign pages 34-36). Heat treatment or tensioning rods can improve interlaminar bond strength in assembled parts (jackson2022additivemanufacturingdesign pages 25-28). For the gear-band region specifically, printing it as a separate ring and press-fitting or bonding it to the auger tube would allow the gear teeth to be printed with their faces in the XY plane for maximum tooth-profile fidelity, similar to Hasan et al.'s horizontal gear printing approach (hasan2024technicalassessmentof pages 6-9).

### Support-Free Strategies

The literature on support-free 3D printing of complex internal geometries includes continuous spiral deposition paths, multi-axis robotic FDM for changing deposition orientation, self-supporting infill patterns, and algorithmic hollowing methods (hergel2019extrusionbasedceramicsprinting pages 11-11). Adaptive support generation algorithms that monitor drift and modify support geometry in real time, and dissolvable/snappable support structures, are available in advanced systems (WO2026039919A1 pages 33-35). For the described auger printed on a conventional 3-axis FDM printer, the most practical approach is to print vertically with the internal fin modelled as a continuous helical sweep and accept some fin-edge sag, or to use soluble support material (e.g., PVA with PETG) to maintain fin geometry. The v3 fix of re-introducing the shaft + helix as a single linear_extrude with proportional twist is geometrically sound for slicer interpretation, as it ensures a continuous helical surface that the slicer can decompose into printable layers.

---

## Summary of Literature Gaps

Several areas relevant to the described design have limited or no direct published coverage:

1. **NEMA 11-specific powder metering**: No peer-reviewed study specifically evaluates NEMA 11 steppers for autotrickler-class dispensers. The open-source reloading/autotrickler community has practical experience but publishes primarily outside academic channels.

2. **External gear band on a metering auger**: Outside of toner cartridge patent art, no study was found that analyses the specific mechanics and failure modes of an external spur-gear band wrapped around a metering auger body. The toner cartridge analogy (EP1927897B1 pages 16-17, EP1927897B1 pages 15-16) provides the closest mass-produced precedent.

3. **Direct controlled comparison of screw vs. tap vs. vibration for sub-gram dosing**: While individual dispensing modalities are well-characterised, no single study provides a head-to-head comparison of these three approaches under controlled conditions with the same cohesive powder.

4. **Hausner-ratio-to-screw-geometry lookup tables**: The literature uses more sophisticated rheological metrics (FT4 flow energy, conditioned bulk density, shear-cell parameters) rather than simple Hausner ratio for predicting screw feeder performance (clayton2019anintroductionto pages 28-31, li2020predictiveperformanceof pages 36-40).

5. **FDM-specific profile-shift and fillet-radius recommendations**: Existing gear standards (VDI 2736, ISO 6336) provide the computational framework, but no study has systematically optimised profile shift or fillet geometry specifically to compensate for FDM dimensional variability and layer-line stress concentrators.

References

1. (hasan2024technicalassessmentof pages 6-9): Mohammad Raquibul Hasan, Ian J. Davies, Alokesh Pramanik, Michele John, and Wahidul K. Biswas. Technical assessment of 3d-printed spur gears produced from recycled pla. Unknown journal, Nov 2024. URL: https://doi.org/10.21203/rs.3.rs-5284212/v1, doi:10.21203/rs.3.rs-5284212/v1.

2. (pisula2021ananalysisof pages 2-4): Jadwiga Pisula, Grzegorz Budzik, Paweł Turek, and Mariusz Cieplak. An analysis of polymer gear wear in a spur gear train made using fdm and fff methods based on tooth surface topography assessment. Polymers, 13:1649, May 2021. URL: https://doi.org/10.3390/polym13101649, doi:10.3390/polym13101649. This article has 51 citations.

3. (zhang2020intelligentmanufacturingapplied pages 42-46): Y Zhang. Intelligent manufacturing applied to additive manufactured polymer gears. Unknown journal, 2020.

4. (bezzini2026designandexamination pages 3-4): Riccardo Bezzini, Giulia Bassani, Carlo Alberto Avizzano, and Alessandro Filippeschi. Design and examination of compound planetary gearboxes to investigate the impact of 3d-printed embedded bearings for assistive exoskeletons actuators. Journal of Mechanical Design, Apr 2026. URL: https://doi.org/10.1115/1.4071656, doi:10.1115/1.4071656. This article has 0 citations and is from a domain leading peer-reviewed journal.

5. (hasan2024technicalassessmentof pages 27-30): Mohammad Raquibul Hasan, Ian J. Davies, Alokesh Pramanik, Michele John, and Wahidul K. Biswas. Technical assessment of 3d-printed spur gears produced from recycled pla. Unknown journal, Nov 2024. URL: https://doi.org/10.21203/rs.3.rs-5284212/v1, doi:10.21203/rs.3.rs-5284212/v1.

6. (netto2022developmentofan pages 100-103): Joaquim Manoel Justino Netto. Development of an innovative additive manufacturing equipment containing a co-rotating twin screw extrusion unit. ArXiv, 2022. URL: https://doi.org/10.11606/t.18.2022.tde-26012023-181116, doi:10.11606/t.18.2022.tde-26012023-181116. This article has 2 citations.

7. (agca2024experimentalinvestigationof pages 2-5): Bekir Volkan AGCA and Mert Safak TUNALIOGLU. Experimental investigation of the wear of some polymer gear wheels produced by three-dimensional printer on the variation of fill percentage and shell thickness. The Eurasia Proceedings of Science Technology Engineering and Mathematics, 31:52-63, Dec 2024. URL: https://doi.org/10.55549/epstem.1593219, doi:10.55549/epstem.1593219. This article has 3 citations.

8. (zhang2020intelligentmanufacturingapplied pages 114-118): Y Zhang. Intelligent manufacturing applied to additive manufactured polymer gears. Unknown journal, 2020.

9. (karalus2026researchanddesign pages 17-21): JR Karalus. Research and design of a 3d printed torque wrench. Unknown journal, 2026.

10. (hasan2024technicalassessmentof pages 4-6): Mohammad Raquibul Hasan, Ian J. Davies, Alokesh Pramanik, Michele John, and Wahidul K. Biswas. Technical assessment of 3d-printed spur gears produced from recycled pla. Unknown journal, Nov 2024. URL: https://doi.org/10.21203/rs.3.rs-5284212/v1, doi:10.21203/rs.3.rs-5284212/v1.

11. (hasan2024technicalassessmentof pages 19-21): Mohammad Raquibul Hasan, Ian J. Davies, Alokesh Pramanik, Michele John, and Wahidul K. Biswas. Technical assessment of 3d-printed spur gears produced from recycled pla. Unknown journal, Nov 2024. URL: https://doi.org/10.21203/rs.3.rs-5284212/v1, doi:10.21203/rs.3.rs-5284212/v1.

12. (hasan2024technicalassessmentof pages 21-24): Mohammad Raquibul Hasan, Ian J. Davies, Alokesh Pramanik, Michele John, and Wahidul K. Biswas. Technical assessment of 3d-printed spur gears produced from recycled pla. Unknown journal, Nov 2024. URL: https://doi.org/10.21203/rs.3.rs-5284212/v1, doi:10.21203/rs.3.rs-5284212/v1.

13. (agca2024experimentalinvestigationof pages 1-2): Bekir Volkan AGCA and Mert Safak TUNALIOGLU. Experimental investigation of the wear of some polymer gear wheels produced by three-dimensional printer on the variation of fill percentage and shell thickness. The Eurasia Proceedings of Science Technology Engineering and Mathematics, 31:52-63, Dec 2024. URL: https://doi.org/10.55549/epstem.1593219, doi:10.55549/epstem.1593219. This article has 3 citations.

14. (karalus2026researchanddesign pages 21-25): JR Karalus. Research and design of a 3d printed torque wrench. Unknown journal, 2026.

15. (kassem2021designofa pages 15-16): Bilal El Kassem, Thomas Brinz, Vahid Jenkouk, Yousef Heider, and Bernd Markert. Design of a vertical loss-in-weight feeder prototype with experimental proof of concept validation. Apr 2021. URL: https://doi.org/10.1080/10837450.2021.1901915, doi:10.1080/10837450.2021.1901915. This article has 3 citations and is from a peer-reviewed journal.

16. (kassem2021designofa pages 4-6): Bilal El Kassem, Thomas Brinz, Vahid Jenkouk, Yousef Heider, and Bernd Markert. Design of a vertical loss-in-weight feeder prototype with experimental proof of concept validation. Apr 2021. URL: https://doi.org/10.1080/10837450.2021.1901915, doi:10.1080/10837450.2021.1901915. This article has 3 citations and is from a peer-reviewed journal.

17. (kassem2021designofa pages 4-4): Bilal El Kassem, Thomas Brinz, Vahid Jenkouk, Yousef Heider, and Bernd Markert. Design of a vertical loss-in-weight feeder prototype with experimental proof of concept validation. Apr 2021. URL: https://doi.org/10.1080/10837450.2021.1901915, doi:10.1080/10837450.2021.1901915. This article has 3 citations and is from a peer-reviewed journal.

18. (EP1927897B1 pages 16-17): Shougo c/o Brother Kogyo Kabushika Kaisha Sato. Image forming apparatus and developing agent cartridge. Patent (EP,US,AT,DE), 2010.

19. (EP1927897B1 pages 15-16): Shougo c/o Brother Kogyo Kabushika Kaisha Sato. Image forming apparatus and developing agent cartridge. Patent (EP,US,AT,DE), 2010.

20. (EP1927897B1 pages 11-12): Shougo c/o Brother Kogyo Kabushika Kaisha Sato. Image forming apparatus and developing agent cartridge. Patent (EP,US,AT,DE), 2010.

21. (hou2024developmentofa pages 97-101): Development of a micro-feeder for cohesive pharmaceutical powders This article has 2 citations.

22. (minglani2020areviewof pages 4-6): Dheeraj Minglani, Abhishek Sharma, Harsh Pandey, Ram Dayal, Jyeshtharaj B. Joshi, and Shankar Subramaniam. A review of granular flow in screw feeders and conveyors. Powder Technology, 366:369-381, Apr 2020. URL: https://doi.org/10.1016/j.powtec.2020.02.066, doi:10.1016/j.powtec.2020.02.066. This article has 106 citations and is from a domain leading peer-reviewed journal.

23. (minglani2020areviewof pages 6-7): Dheeraj Minglani, Abhishek Sharma, Harsh Pandey, Ram Dayal, Jyeshtharaj B. Joshi, and Shankar Subramaniam. A review of granular flow in screw feeders and conveyors. Powder Technology, 366:369-381, Apr 2020. URL: https://doi.org/10.1016/j.powtec.2020.02.066, doi:10.1016/j.powtec.2020.02.066. This article has 106 citations and is from a domain leading peer-reviewed journal.

24. (minglani2021analysisofflow pages 2-3): Dheeraj Minglani, Abhishek Sharma, Harsh Pandey, Ram Dayal, and Jyeshtharaj B. Joshi. Analysis of flow behavior of size distributed spherical particles in screw feeder. Powder Technology, 382:1-22, Apr 2021. URL: https://doi.org/10.1016/j.powtec.2020.12.041, doi:10.1016/j.powtec.2020.12.041. This article has 25 citations and is from a domain leading peer-reviewed journal.

25. (malm2021evaluatingtheoreticaland pages 34-39): H Malm. Evaluating theoretical and empirical models to forecast feeding capacities of bulk materials. Unknown journal, 2021.

26. (clayton2019anintroductionto pages 28-31): Jamie Clayton. An introduction to powder characterization. Handbook of Pharmaceutical Wet Granulation, pages 569-613, Jan 2019. URL: https://doi.org/10.1016/b978-0-12-810460-6.00021-x, doi:10.1016/b978-0-12-810460-6.00021-x. This article has 38 citations.

27. (li2020predictiveperformanceof pages 36-40): Tianyi Li. Predictive performance of loss-in-weight feeders for continuous powder-based manufacturing. ArXiv, Jan 2020. URL: https://doi.org/10.7282/t3-6tgx-8f63, doi:10.7282/t3-6tgx-8f63. This article has 2 citations.

28. (malm2021evaluatingtheoreticaland pages 28-34): H Malm. Evaluating theoretical and empirical models to forecast feeding capacities of bulk materials. Unknown journal, 2021.

29. (yang2007meteringanddispensing pages 4-6): Shoufeng Yang and Jrg Evans. Metering and dispensing of powder; the quest for new solid freeforming techniques. Powder Technology, 178:56-72, Sep 2007. URL: https://doi.org/10.1016/j.powtec.2007.04.004, doi:10.1016/j.powtec.2007.04.004. This article has 201 citations and is from a domain leading peer-reviewed journal.

30. (yang2007meteringanddispensing pages 9-10): Shoufeng Yang and Jrg Evans. Metering and dispensing of powder; the quest for new solid freeforming techniques. Powder Technology, 178:56-72, Sep 2007. URL: https://doi.org/10.1016/j.powtec.2007.04.004, doi:10.1016/j.powtec.2007.04.004. This article has 201 citations and is from a domain leading peer-reviewed journal.

31. (yang2007meteringanddispensing pages 6-7): Shoufeng Yang and Jrg Evans. Metering and dispensing of powder; the quest for new solid freeforming techniques. Powder Technology, 178:56-72, Sep 2007. URL: https://doi.org/10.1016/j.powtec.2007.04.004, doi:10.1016/j.powtec.2007.04.004. This article has 201 citations and is from a domain leading peer-reviewed journal.

32. (pinzon2012modellingofdosator pages 34-38): OA Angulo Pinzon. Modelling of dosator filling and discharge. Unknown journal, 2012.

33. (yang2007meteringanddispensing pages 10-12): Shoufeng Yang and Jrg Evans. Metering and dispensing of powder; the quest for new solid freeforming techniques. Powder Technology, 178:56-72, Sep 2007. URL: https://doi.org/10.1016/j.powtec.2007.04.004, doi:10.1016/j.powtec.2007.04.004. This article has 201 citations and is from a domain leading peer-reviewed journal.

34. (fathollahi2020performanceevaluationof pages 1-2): Sara Fathollahi, Stephan Sacher, M. Sebastian Escotet-Espinoza, James DiNunzio, and Johannes G. Khinast. Performance evaluation of a high-precision low-dose powder feeder. AAPS PharmSciTech, Nov 2020. URL: https://doi.org/10.1208/s12249-020-01835-5, doi:10.1208/s12249-020-01835-5. This article has 25 citations and is from a peer-reviewed journal.

35. (drotman2015designofa pages 19-27): DTJ Drotman. Design of a screw extruder for additive manufacturing. Unknown journal, 2015.

36. (benasso2018artifactsinfdm pages 66-71): F Benasso. Artifacts in fdm 3d printing, extrusion inconsistency problem and weight reduction. Unknown journal, 2018.

37. (chasti2021novelmachinetool pages 63-68): BS Chasti. Novel machine tool feed drive design for high dynamic stiffness and ultra-low vibration. Unknown journal, 2021.

38. (jackson2022additivemanufacturingdesign pages 25-28): Amiee Jackson, Celeste Atkins, Abby Barnes, Vidya Kishore, Brian Post, Christopher Hershey, Michael Borish, Halil Tekinalp, Alex Roschli, Phillip Chesser, Tyler Smith, Pum Kim, Vlastimil Kunc, Lonnie Love, David Snowberg, and Scott Carron. Additive manufacturing design guidelines for wind industry. ArXiv, Dec 2022. URL: https://doi.org/10.2172/1906578, doi:10.2172/1906578. This article has 1 citations.

39. (jackson2022additivemanufacturingdesign pages 34-36): Amiee Jackson, Celeste Atkins, Abby Barnes, Vidya Kishore, Brian Post, Christopher Hershey, Michael Borish, Halil Tekinalp, Alex Roschli, Phillip Chesser, Tyler Smith, Pum Kim, Vlastimil Kunc, Lonnie Love, David Snowberg, and Scott Carron. Additive manufacturing design guidelines for wind industry. ArXiv, Dec 2022. URL: https://doi.org/10.2172/1906578, doi:10.2172/1906578. This article has 1 citations.

40. (hergel2019extrusionbasedceramicsprinting pages 11-11): Jean Hergel, Kevin Hinz, Sylvain Lefebvre, and Bernhard Thomaszewski. Extrusion-based ceramics printing with strictly-continuous deposition. ACM Transactions on Graphics (TOG), 38:1-11, Nov 2019. URL: https://doi.org/10.1145/3355089.3356509, doi:10.1145/3355089.3356509. This article has 43 citations.

41. (WO2026039919A1 pages 33-35): Madison Carolyn FEEHAN. Methods and systems for 3d printing of objects. Patent (WO), 2026.
