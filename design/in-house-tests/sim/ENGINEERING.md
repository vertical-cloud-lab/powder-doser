# Engineering checks of the ten test apparatuses: FEA, CFD and theory in one page

**Status: computed, not measured (2026-11-28).** Nothing here has been built. The details, validation
and sources are in [`fea/`](fea/README.md) (structures and electrostatics; CalculiX, gmsh, scikit-fem),
[`cfd/`](cfd/README.md) (own Navier-Stokes and transport solvers, validated against Ghia et al. 1982 and
exact diffusion and pipe-flow solutions) and [`theory/`](theory/README.md) (the equation set, expected
signals and uncertainty budgets). Geometry is the CAD worker's parts as exported on 2026-11-28; each
result file records the STEP it used (sha256), and the CAD was still changing during the runs.

## Checks

| Test | Check | Result (computed) | Margin | Design action |
|---|---|---|---|---|
| 1 | AoR line fit, 3 pours (theory) | SE 0.7° dry, 2.2° cohesive on Ø20 | cohesive misses ±2° | Ø30 pedestal for coarse or cohesive powders; 5-9 pours for cohesive |
| 1 | Air drag on grains reaching the heap, 12 mm (CFD) | 98-100 % of free-fall speed in the stream, all powders | pass | none; the DEM can ignore air |
| 1, 5, 10 | Tripod tipping, test 5 holder as drawn (FEA g) | TRI_T5 | TRI_T5M | TRI_T5A |
| 1, 5, 10 | Tripod, test 10 payload on 160 mm legs (FEA g) | TRI_T10 | TRI_T10M | TRI_T10A |
| 2 | Poured cone on the column (theory) | reading the apex biases ρ_bulk by 5-8 % | fails | volume from the silhouette of revolution; calibrate the bore at two heights |
| 2 | Tapper impact (FEA e) | TAP_IMP | TAP_IMPM | TAP_IMPA |
| 2 | Tapper stress and fatigue (FEA e) | TAP_FAT | TAP_FATM | TAP_FATA |
| 3 | Servo step jolts at the ring (FEA a) | 0.3-1.1 g for 0.045-0.135° steps done in 2-10 ms | needs under 0.01-0.02 g (0.2-0.4° early slip): fails 15-50× | worm or lead-screw drive (Tic T500 is free); log IMU and reject peaks over 0.02 g |
| 3 | Plate modes (FEA a) | 35.6 Hz (one-sided drive through a 6 mm arm), torsion 268 Hz (218 Hz at E 2.3 GPa) | torsion 7 % above the ERM's 150-250 Hz | gear on both lugs, 12 mm arms; no ERM or tapper during test 3 |
| 3 | Plate sag, level, full payload (FEA a) | 0.29 mm tip, all rotation; ring site vs IMU 0.007° | 300× on ±2° | none |
| 3 | Lid-less ring on the plate (theory) | friction carries 0.1-0.4 g of the 0.73 g ring | ring sits on the plate | lids of 3 g or more, or a 0.8 mm wall; 1.0 mm shims for d90 over 0.25 mm |
| 4 | Counting statistics (theory) | number d50 ±2 % needs 1300-6500 grains; volume d50 needs 2900-570,000 | 2000 is too few | count 4000 or more; volume percentiles from sieving or laser diffraction; field at 1× is 6.29 × 4.71 mm |
| 5 | Air counter-flow at the orifice (CFD) | flow cut over 5 % below d50 55-185 µm, over 20 % below 28-91 µm | Si-325, AlSi10Mg, CMC below Beverloo by 3-44 % | fit Beverloo with the air term below d50 100 µm |
| 5 | Fill and heel (theory) | a 5 g fill leaves a 0.9-3.2 g heel, 4-23 balance samples at Ø6 | too short at Ø6 | 60° conical insert, or 15 g for discs of 4 mm and up |
| 6 | Box to set point after closing (CFD) | 95 / 99 % at 6.3 / 10.6 min in still air, 2.3 / 4.0 min with the fan | over 100× on 24 h | wait 30 min before timing |
| 6 | 2 g hygroscopic sample (CFD) | half-time 1.2 h, set by the box (powder alone 2.6 min); 0.3-0.6 h with the fan | kinetics box-limited | 25 mm fan under the shelf, always on at reduced power; 0.5 g for kinetics |
| 6 | Sensor vs sample RH (CFD), temperature (theory, CFD) | SHT45 reads 10.5 % RH high at 1 h (still), 2.5-6 % (fan); 1 K reads 1.9-4.9 % RH low; fan heat 0.5-1.2 K | fails at 1 K | sensor on the shelf near the dish; isothermal to ±0.1 K; log T at the sample; add NaNO₃ and KI boxes around NaCl's 75.3 % |
| 7 | Drum shaft sag, twist, tooth at NEMA 11 stall (FEA b) | 0.6-3 µm, 0.05-0.08°, root 5.0-5.5 MPa (Lewis 2.6) | 2.7-3.0 on 15 MPa fatigue; 10× on 0.5° | add a 0.3 mm root fillet to `gear_profile` (now a sharp corner) |
| 7 | Drum runout (FEA b, geometric) | about 0.2 mm TIR from print tolerances; elastic part 1 % of it | check on build | dial-gauge the drum; face the flange square |
| 7 | Regimes and end walls (theory) | Fr 2×10⁻⁵ to 9×10⁻³ at 1-20 rpm; 15 mm depth adds +0.9 to +3.7° | | add 30 and 60 rpm; 30 fps below 5 rpm; 300 s for cohesive powders |
| 8 | Mould parting line (FEA c) | the mould deforms by nm, but the rings' 0.25 mm radial clearance lets the halves slide 0.5 mm apart under 0.21 N | fails | snug rings: `mould_ring` ID 30.0, or a split collar with a clamp screw |
| 8 | Frame vs load cell vs sample (FEA c) | platen 0.9, base + column 4.4-6.7, TAL221 9-35 (estimate) µm/N; sample at failure 1300-38,000 µm/N | platen travel is 97-99.9 % the sample's | none; measure the machine compliance on a steel dummy |
| 8 | Does a column stand (theory) | 40 mm PLA mould: only ff_c under 1.5 stands; the 100 g cell is at full scale at 2 kPa | fails for most powders | PTFE liner, H 20-30 mm, consolidate off the cell or use a 500 g cell |
| 9 | Blade gap under spreading (FEA d) | BLADE_ROW | over 100× | none |
| 9 | Guide-rod sag along the stroke (FEA d) | about 5 µm | 2.5-5 % of the gap | gap screws riding on the bed rails, or set the gap at mid-stroke |
| 9 | Gap vs powder (theory) | a 0.20 mm gap is at least 2.5 × d50 for only 3 of 12 battery powders | fails for 9 | gap of about 2.5 × d50; 1.5 mm of gap-screw travel; feed 1.5 × the layer mass |
| 10 | Shielding of outside charge (FEA f) | cup sees 11 % of a charge at the outlet with the printed lid, 0.74 % with a grounded lid | 15-38× better grounded | metal tape on the lid, bonded to the can |
| 10 | Charge capacity (FEA f) | 100 nC on the floor gives about 6 MV/m in air (breakdown 3) | fails above about 49 nC | at most 40-50 nC a reading; spread the powder; 100 nF range |
| 10 | Read-out time (FEA f) | counted to 99 % once 30 mm below the rim, 65 ms after leaving the outlet | 30× on the 2 s wait | read only with no powder in the top 30 mm |
| 10 | Fines escaping the cup (CFD) | CFD_FC | CFD_FCM | CFD_FCA |
| 10 | Printed funnel (FEA f) | charge of grains stuck on it counted at 23-55 %, mass not weighed | error | conductive grounded funnel, or none |
| 10 | Feedback capacitor (theory) | 10¹¹ Ω across C_f loses 18 % over a 200 s dose; C0G absorption leaves 5 % | fails | 10¹³ Ω or more; polystyrene or PTFE C_f; start on 100 nF |

## Design changes, in order of importance

PRIORITIES

## Found in the CAD (for the CAD worker)

CADLIST

## Limits

- Every number is computed. Material data are handbook or assumed (PLA fatigue limit 15 MPa, servo
  stiffness, TAL221 compliance, printed solid fraction, part masses), as stated in each README.
- The FEA is linear and static or modal; contact, backlash, bolt preload and print anisotropy are not
  modelled. The impact uses a spring-mass and Hertz model with FEA stiffnesses.
- The CFD is laminar and 2D or axisymmetric except the 3D still-air humidity box; the fan jet uses an
  effective viscosity. The theory uses class-level properties for the battery powders.
- Check each design action against the build: these models size the fixtures, they do not replace a
  first measurement.
