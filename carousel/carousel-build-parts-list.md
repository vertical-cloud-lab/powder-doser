# 50-Auger Vertical Carousel — Buildable Parts List (DRAFT / NOT YET IN BOM)

> **Status: exploratory / not incorporated into [`BILL-OF-MATERIALS.md`](../BILL-OF-MATERIALS.md).**
> This is a "what would I actually buy to build one" parts list for the
> **vertically oriented** rotating magazine that stores and indexes **50 filled
> augers**, requested on PR #114 (comment 4801823301, @sgbaird) and tightened to
> the vertical design on comment 4802540746. Every part below is chosen for the
> vertical (horizontal-axis, Ferris-wheel / paternoster) geometry — see §0. It
> expands the drive
> recommendation in BOM §5.1/§5.2 into a *complete* build BOM (structure,
> bearing, indexing, sensing, control, safety) so it can be priced and
> sanity-checked **before** anything is promoted into the main BOM.
>
> Costs are rough order-of-magnitude (USD, 2026) for budgeting only.
> Where an exact part still needs a final click-through / sizing pass it is
> marked **[confirm]**. The companion Edison high-effort literature review
> of carousel/turret/paternoster prior art is in
> [`edison/carousel-literature-review.md`](./edison/carousel-literature-review.md)
> (task `499c6c09-0970-47f9-a7b7-a54ac9bfc090`); its key takeaways are
> summarised in §11 below.

---

## 0. Design assumptions

| Assumption | Value | Basis |
|---|---|---|
| Augers stored | 50 | request |
| Filled auger mass | ~0.2 kg each → **~10 kg** payload | BOM §5.1 / §6.3 (Ø25×250 mm "nozzle 4", ~66.8 mL) |
| Wheel pitch radius | ~0.20 m (≈0.42 m wheel Ø) | 50 pockets at ~26 mm spacing on a single vertical ring; *see note* |
| Indexing | one pocket → **bottom** dosing station at a time | request (servo + solenoid pulls the bottom auger straight down) |
| Worst-case shaft torque | **~5–12 N·m** (gravity imbalance of a part-emptied wheel + index accel) | BOM §5.1 torque budget; *vertical-specific note* |
| Hold requirement | must **not** back-drive on power loss (gravity will turn an unbalanced vertical wheel) | safety |

> **Orientation — vertical, by design** (@sgbaird, comment 4801844718). The
> magazine is a **vertically oriented carousel** (rotation axis horizontal;
> augers hang vertically, Ferris-wheel / paternoster style), **not** a
> horizontal turntable or a horizontal-axis drum. The dispense mechanism pulls
> one auger **in/out of the dispense position with a servo + solenoid**; a
> horizontal layout would have to present that in/out stroke radially and so
> would need a very large wheel diameter to fit 50 augers, whereas a vertical
> loop keeps the footprint small and presents the indexed auger at the bottom
> for a straight-down pull. See the schematic comparison in
> [`mechanism-panel/`](./mechanism-panel/README.md). This supersedes the
> Edison review's "horizontal drum" suggestion (see §11).
>
> **Geometry note.** 50 Ø25 mm augers on one ring at a sane pitch needs a
> ~0.42 m wheel; if that is too large, split into **two stacked rings of 25**
> on the same horizontal shaft, or a **double-helix paternoster** (carriers on a
> chain loop) to keep the footprint down. Both options keep the **vertical**
> orientation — they differ only in how the wheel is carried: **Option A**, a
> rigid wheel on a **horizontal through-shaft** (Ferris-wheel axle, §3 default),
> or **Option B**, a **paternoster chain loop** of carriers. A horizontal
> turntable/drum is explicitly **not** an option here (see §11).
>
> **Vertical-specific torque note.** A *full* wheel is roughly balanced, so the
> motor mostly fights inertia + bearing friction. The worst case is a
> **part-emptied** wheel: once augers have been dispensed from one arc, the
> remaining ~10 kg sits off-axis and gravity applies a standing moment about the
> horizontal shaft (up to ~payload × pitch radius ≈ 10 kg × 0.2 m ≈ **20 N·m at
> the rim** before reduction/counterweight). This is why the vertical build
> leans on a **counterweight** (§6 F4) to cancel most of that moment *and* a
> **self-locking worm reducer / power-off brake** (§2/§4/§5) so the wheel cannot
> creep or back-drive when stopped — neither of which a horizontal turntable
> would need.

---

## 1. Drive (motor + driver + power) — *verified against @sgbaird's datasheet*

The NEMA 34 below is the part @sgbaird attached the datasheet/STEP for
([`34HS59-6004D-E1000.STEP`](../34HS59-6004D-E1000.STEP) at repo root).
Specs confirmed from `34HS59-6004D-E1000_Full_Datasheet.pdf`: **12.0 N·m**
holding, **6.0 A/phase**, 0.53 Ω/phase, 4.80 mH/phase, 1.8° step, rotor
inertia **3600 g·cm²**, **5.5 kg**, NEMA 34 frame, **Ø14 mm** shaft,
dynamic radial load 75 N max @20 mm, axial 15 N max.

| # | Part | Representative P/N | Qty | ~USD | Notes |
|---|---|---|---|---|---|
| D1 | NEMA 34 closed-loop stepper, 12 N·m, 1000 PPR encoder | StepperOnline **34HS59-6004D-E1000** | 1 | 110 | The motor in the attached datasheet/STEP. Ø14 shaft. |
| D2 | Closed-loop stepper driver (NEMA 34) | StepperOnline **CL86T** (24–110 VDC, 0–8.2 A) | 1 | 55 | Reads the motor encoder; STEP/DIR/ENA input. |
| D3 | Motor PSU | Mean Well **LRS-350-48** (48 V, 7.3 A) | 1 | 35 | ≥6 A for the motor; 48–80 VDC band of the CL86T. |
| D4 | Logic PSU | Mean Well **LRS-50-12** (12 V) or reuse bench 12 V | 1 | 15 | MCU, sensors, brake. |
| D5 | 5 V regulator for MCU/sensors | Pololu **D24V22F5** | 1 | 8 | Same family already in BOM §10. |

**Radial-load caveat:** the bare motor shaft is rated only **75 N radial
@20 mm** — a 10 kg off-balance wheel hung directly on it would exceed that.
The wheel **must** ride on its own bearing (§3); the motor drives through a
coupling/gearbox and is **not** the structural axle.

---

## 2. Indexing & holding strategy (pick one)

| Option | Adds | Pros | Cons |
|---|---|---|---|
| **2a. Direct closed-loop + brake** | electromagnetic power-off brake (§5) | simplest; software-set 50 stations | brake needed for fail-safe hold |
| **2b. Self-locking worm reducer** | right-angle worm gearbox (§4) | back-drive-proof, multiplies torque, lets a smaller motor work | backlash; lower index speed |
| **2c. Geneva / detent index plate** | Geneva set or 50-hole plate + solenoid plunger | *positive geometric* lock, even unpowered | fixed 50-station geometry; extra mechanism |

Recommended: **2b (worm reducer) for the production wheel** (fail-safe hold
without a powered brake), with **2c detent plunger** added if a hard
mechanical lock at the dosing station is wanted. **2a** is fine for a first
bench prototype.

---

## 3. Rotation support — horizontal Ferris-wheel axle (**required**)

Because the carousel is **vertical** (rotation axis horizontal), the wheel is
carried like a **Ferris-wheel axle**: a horizontal through-shaft on **two
pillow-block bearings**, one each side of the wheel. This is the structural
load path — the motor only applies torque (its shaft is rated for just 75 N
radial, §1). A horizontal slewing-ring *turntable* bearing is **not** used
here (that suits a horizontal turntable, which we ruled out, §11).

| # | Part | Representative type / P/N | Qty | ~USD | Notes |
|---|---|---|---|---|---|
| B1 | **Horizontal main shaft** (the axle) | Ø20–25 mm precision shaft, keyed to the worm-gearbox/coupling output **[confirm dia.]** | 1 | 20 | Spans the wheel; sized for the ~20 N·m gravity moment + ~10 kg load, not just torque. |
| B2 | **Pillow-block bearings** (axle supports) | 2× UCP/UCF/SHF-type ball-bearing pillow blocks, bore = B1 **[confirm bore]** | 2 | 25 | One each side of the wheel; carry the wheel's weight + moment so the motor/gearbox sees torque only. |
| B3 | Shaft collars / locating rings | 2–4× clamp collars, bore = B1 | 4 | 8 | Axially locate the wheel and shaft against the bearings. |
| B4 | *(Paternoster Option B instead of B1–B3)* sprocket + chain loop | #25 or #35 ANSI roller chain + 2 sprockets + idlers on the same horizontal axle **[confirm]** | 1 set | 60 | For a vertical chain-loop carrier magazine instead of a rigid wheel. |

---

## 4. Drivetrain coupling / reduction

| # | Part | Representative P/N | Qty | ~USD | Notes |
|---|---|---|---|---|---|
| C1 | Flexible shaft coupling, 14 mm bore | Ruland / Lovejoy **L-075** class, 14 mm × {shaft} | 1 | 15 | If direct-drive (Option 2a). |
| C2 | Right-angle worm gearbox, NEMA 34 input, **40:1–60:1** | StepperOnline NEMA 34 worm gearbox (RV/WPA-class) **[confirm ratio]** | 1 | 70–120 | Option 2b; ≥40:1 is self-locking. ~12 N·m × ratio at output (de-rated). |
| C3 | Output hub / flange to wheel | machined or printed hub, key + grubscrews | 1 | 10 | Couples B3/gearbox to the wheel. |

---

## 5. Sensing, indexing detent & safety

| # | Part | Representative P/N | Qty | ~USD | Notes |
|---|---|---|---|---|---|
| S1 | Home/index proximity sensor | **LJ18A3-8-Z/BX** inductive NPN-NO, 8 mm, 6–36 V | 1 | 6 | Senses a metal tab once per revolution for homing. |
| S2 | *(alt)* optical slot / Hall + magnet home sensor | photo-interrupter or **A3144** Hall + magnet | 1 | 3 | Cheaper non-metal homing. |
| S3 | Detent plunger (Option 2c) | small **push/pull solenoid** (e.g. Adafruit 412, already in BOM) + 50-hole index plate | 1 | 10 | Drops into the index plate at each station for a positive lock. |
| S4 | Electromagnetic **power-off** brake (Option 2a) | 24 VDC spring-applied brake, ≥5 N·m, NEMA 34 rear-mount **[confirm]** | 1 | 40–90 | Holds the wheel when de-energised; release on power-up. |
| S5 | E-stop + limit/over-travel switch | NC mushroom E-stop + 1–2 microswitches | 1 set | 15 | Cuts motor power; safety on a 10 kg moving mass. |

---

## 6. Structure / frame

| # | Part | Representative P/N | Qty | ~USD | Notes |
|---|---|---|---|---|---|
| F1 | Aluminium extrusion frame | **2020 / 4040 V-slot** (OpenBuilds / 80-20), ~6–10 m total **[confirm cut list]** | 1 set | 60–120 | Rigid frame to carry the bearing + motor; vertical plane. |
| F2 | Corner brackets / gussets, T-nuts, M5 bolts | extrusion hardware kit | 1 set | 25 | — |
| F3 | Carousel wheel / pocket disc | 3D-printed (PLA/PETG) **or** laser-cut acrylic/Al, 50 pockets sized to Ø25 augers + retention | 1 | 20–60 | Fits the repo's FDM workflow; print in segments if >printer bed. |
| F4 | **Counterweight / balancing** mass | adjustable weights opposite the loaded arc (paternoster principle) | 1 set | 10 | Lets the motor fight inertia/friction, not a standing gravity moment. |
| F5 | Auger pocket retainers | printed clips / leaf-spring detents per pocket | 50 | 15 | **Critical for the vertical sweep:** augers ride upside-down over the top of the wheel, so each pocket must positively retain its auger against gravity yet release it for the bottom-station servo+solenoid pull. |

---

## 7. Control & wiring

| # | Part | Representative P/N | Qty | ~USD | Notes |
|---|---|---|---|---|---|
| E1 | Microcontroller | **Raspberry Pi Pico / Pico W** (already the bench host, BOM §2) | 1 | 6 | Emits STEP/DIR/ENA to the CL86T; reads S1 home + S5. |
| E2 | Logic-level / opto interface | opto-isolated breakout or transistor buffer for STEP/DIR | 1 | 5 | CL86T inputs are 5 V-tolerant opto; isolate from the 48 V side. |
| E3 | Brake/solenoid driver | MOSFET low-side driver + flyback diode (e.g. DRV8871 already in BOM, or a logic MOSFET) | 1 | 4 | Switches S3/S4. |
| E4 | Wiring, ferrules, drag chain, fuses | 18–22 AWG, inline fuse on 48 V, strain relief | 1 set | 25 | — |

---

## 8. Rough budget

| Block | ~USD |
|---|---|
| Drive (D1–D5) | ~220 |
| Bearing/axle (B1–B4) | ~55–115 |
| Coupling/reduction (C1–C3) | ~95–145 |
| Sensing/detent/safety (S1–S5) | ~75–135 |
| Frame (F1–F5) | ~130–230 |
| Control/wiring (E1–E4) | ~40 |
| **Total (excl. 50 augers & dosing heads)** | **~$680–$1,070** |

---

## 9. Buy-and-modify shortcut (alternative to building from parts)

Instead of assembling §3–§6 from scratch, buy a ready indexing stage and
bolt the auger pockets to it (see BOM §5.2 (B) for vendors):

- **Industrial rotary indexing table** (Weiss TC, CAMCO/Destaco, Sankyo) —
  globoidal-cam index + dwell + lock built in; rugged but heavy/$$$.
- **Used lab autosampler / fraction-collector carousel** (Gilson, Teledyne
  ISCO, Agilent/Thermo) — gut for its indexed wheel + home sensor + stepper,
  then **re-mount it on a horizontal axis** for the vertical magazine.
- **Pharmacy canister carousel** (ScriptPro/Parata) — closest functional
  analog (index 1-of-N canister to a chute).
- **Kardex/Hänel vertical lift module** (counterbalanced paternoster) — already
  a vertically oriented, counterweighted carrier loop; the closest match to the
  chosen orientation, worth studying for the retention + counterweight scheme.

These trade a higher unit cost / less customisation for far less mechanical
design and a proven hold/index mechanism.

---

## 10. Open items before promoting to the BOM

- **[confirm]** Final wheel diameter vs. single-ring/double-ring/paternoster
  choice (drives the axle length and frame).
- **[confirm]** Main shaft diameter + pillow-block bore/load rating for the
  ~10 kg payload **and the ~20 N·m gravity moment** of a part-emptied wheel.
- **[confirm]** Counterweight mass/travel needed to cancel the worst-case
  imbalance moment as augers are consumed.
- **[confirm]** Worm-gearbox ratio (40:1 vs 60:1) and exact NEMA 34 input flange.
- **[confirm]** Power-off brake torque/voltage and NEMA 34 rear-mount fit.
- **[confirm]** Bottom-station auger **release** mechanism: clip stiffness vs.
  the servo+solenoid pull force, so augers stay seated over the top yet release
  cleanly at the bottom.
- **[confirm]** Whether the CL86T's STEP/DIR can be driven straight from the
  Pico W 3.3 V via the opto input, or needs a level shifter.
- Fold in findings from the Edison literature review (see [`edison/`](./edison/))
  and the **vertical-design feedback** query (§12).

> Many representative P/Ns above (pillow blocks, worm gearbox, brake) are
> *category/representative* picks — the **browser tool was unavailable this
> session** (persistent "browser already in use" even after restarting the
> Playwright MCP server and clearing the profile lock), and
> `omc-stepperonline.com` returns HTTP 403 to automated fetchers, so exact
> SKUs for those items still need a final click-through before ordering. The
> motor/driver (D1/D2) **are** verified against the datasheet @sgbaird attached.

---

## 11. Edison literature review — key takeaways

Full report + raw task dump:
[`edison/carousel-literature-review.md`](./edison/carousel-literature-review.md),
[`edison/task_dump.json`](./edison/task_dump.json) (FutureHouse Edison
high-effort literature, task `499c6c09-0970-47f9-a7b7-a54ac9bfc090`,
`has_successful_answer: true`).

- **Edison suggested a horizontal-axis drum — but we are keeping the magazine
  *vertically oriented* (decision, @sgbaird, comment 4801844718).**
  The review's headline recommendation was a **CNC-tool-changer-style drum
  carousel** (rotation axis horizontal, augers parallel to the axis), which is
  mechanically tidy for storing many elongated cylinders. **We are not
  adopting it**: the dispense mechanism pulls a single auger **in and out of
  the dispense position with a servo + solenoid**, and on a horizontal
  (turntable / drum-end) layout that radial in/out stroke forces a very large
  wheel diameter to fit all 50 augers around the rim. A **vertical carousel**
  (rotation axis horizontal, augers hanging vertically — a Ferris-wheel /
  paternoster loop) keeps the footprint small, keeps every auger upright for
  gravity feed, and presents the indexed auger at the bottom where the
  servo + solenoid can pull it **straight down** into the dosing station. The
  drum is retained here only as *prior art*, not as the chosen architecture.
  See the schematic comparison in
  [`mechanism-panel/`](./mechanism-panel/README.md) (the "Vertical carousel
  (CHOSEN)" vs. "Horizontal carousel (rejected)" tiles).
- **Drive/hold:** stepper through a **self-locking worm reducer** (matches
  Option 2b) + a **spring-loaded shot pin** into a precision hole at the
  dosing station for a positive mechanical lock, plus **ball-detent
  plungers** around the periphery — corroborating §2/§5 here.
- **Auger retention:** **compliant leaf-/wire-spring clips** per pocket
  (as in the Holst et al. patch-clamp pipette carousel, which retained
  glass pipettes with 100% reliability over 444 presentations) — refines
  §6 F5.
- **Homing/control:** photoreflective or inductive home sensor + stepper
  step-counting; Arduino/Raspberry-Pi-class controller (validated by the
  open-source **RotoMate**, ~$550 Arduino autosampler, and the ETH **COD
  carousel**) — matches §5 S1/S2 and §7 E1.
- **Open-source / academic precedents to study** (purchasable or
  replicable): **RotoMate** (30-sample 3D-printed NMR autosampler, OSH),
  **Holst et al. 2019** patch-clamp 40-pipette carousel (9°/pipette,
  spring-clip retention), **COD carousel** (ETH, 1.8° bipolar stepper, PEEK
  tube ring), GC/HPLC autosampler & fraction-collector trays (Agilent,
  Teledyne ISCO, Gilson), and **CNC ATC drum magazines** (20–60+ tools).
- **Commercial to buy/modify:** Mettler-Toledo Quantos/XPR & Chronect dosing
  -head carousels, Chemspeed gantry-over-rack platforms, Kardex/Hänel
  vertical lift modules (counterbalanced paternosters), Weiss/DESTACO/CAMCO
  barrel-cam rotary index tables.
- **Budget cross-check:** the review's independent estimate is **$500–1,100**
  for a functional prototype — consistent with §8's ~$680–1,070.

*(Citations with DOIs are listed at the end of the full review.)*

---

## 12. Edison feedback query (vertical design — in flight)

A **non-blocking** FutureHouse Edison high-effort literature query was
dispatched this session (@sgbaird, comment 4802540746: "send a nonblocking
Edison query with the latest plan for feedback") to critique the vertical
build above and surface prior art / failure modes / improvements.

- **Task ID:** `11ddf6db-5baa-4e5f-a789-3d2d1d3195be` (`LITERATURE_HIGH`)
- **Status when dispatched:** queued / running — **fetch next session** and
  fold the feedback into §2–§7 and the §10 open items.
- **Asked specifically about the vertical geometry:** dominant torque/holding
  requirement for a horizontal-axis loaded wheel; retaining/releasing hanging
  augers at the bottom station; vertical-carousel / paternoster / vertical-lift
  precedents to study or buy-and-modify; and failure modes unique to a
  vertically oriented loaded carousel (imbalance as augers are consumed, shaft
  deflection, back-drive on power loss).

