# Chain carousel v5: the dose falls onto a real balance

v5 is [v4](../chain-carousel-v4/README.md), with one change of requirement. Sterling asked on 2026-11-04 ([PR #185](https://github.com/vertical-cloud-lab/powder-doser/pull/185)): "the multi-doser needs to be using a real scale". Sam asked for the same thing in his item 6 of 2026-10-29: "Model the scale and put it into the assembly ... that's an essential part of this project".
- **In v5 the dose falls straight into a beaker on an A&D HR-202i analytical balance**: 220 g × 0.1 mg, with a 51 g × 0.01 mg fine range.
- The balance stands on the bench under the station. It touches nothing of the doser.
- v5 keeps v4's augers outside the loop, its kinematic dock, outlet doors, pin latches, enclosure and side tabs.

Nothing is built. Every number here is a prediction from the CAD.

| v5 from the front: the HR-202i under the dose point, the lift bar on two P16s beside it | Module 1 at 30° over the beaker (section on the station's centre plane) |
|---|---|
| ![](renders/rig_balance_front.png) | ![](renders/rig_dose30_section.png) |

![The balance-dose cycle](renders/features/balance_dose.gif)

## What the earlier versions weighed on

| Version | What the dose lands on | Why it isn't a real balance |
|---|---|---|
| v2, paternoster | A vial in a cup on a **TAL221 100 g load cell** (a bar strain gauge on an HX711), under a D-cut funnel | A $10 load cell, and a funnel shared by every powder. byu-vcl#303's animation uses v2, so it shows this load cell |
| v3, v4 | The lab's **HR-100A**, drawn at the dose point as a ghost | It doesn't fit there. The EC's column (the guide cradle on its post, the P16 and the EC itself) stands inside the balance's breeze break. The frame's front base rail and station rails run through its footprint. v3 has 19 kinds of part in its way, v4 has 11 ([v4's checks/scale.json](../chain-carousel-v4/checks/scale.json)). Sam asked to see why in a GIF before anything changed, so neither version moved anything |
| **v5** | **A 25 mL beaker on a printed riser on the HR-202i's pan** | The station is rebuilt round the balance. [`checks/scale.json`](checks/scale.json) finds nothing in its way, parked, docked, at 30° or at 50° |

## The balance

**Which one.** The lab's documented 0.1 mg A&D balance is the HR-100A, 102 g × 0.1 mg ([byu-vcl#2](https://github.com/vertical-cloud-lab/byu-vcl/issues/2), "Set up the 0.1 mg scale"). The single doser runs on it today.

Sterling asked for "the one with the higher capacity that still has 0.1 mg resolution". The higher-capacity 0.1 mg A&D model this repo names is the **HR-202i**:
- It is in [`design/brainstorming.md`](../../design/brainstorming.md) §1, next to the FZ-523 and HR-300i, and in [#159](https://github.com/vertical-cloud-lab/powder-doser/issues/159).
- byu-vcl's vertical-lab animation already uses it, from round 5 of [byu-vcl PR 318](https://github.com/vertical-cloud-lab/byu-vcl/pull/318) on.

I found no record that the lab has bought one. Those threads list it as a candidate.

**v5 is drawn for the HR-202i, and the HR-100A fits in the same place.** The HR-100A was checked against the same station:
- The station parked: nothing in its way.
- At 30°: nothing in its way.
- The one change it needs: its base is taller than the HR-202i's display unit, so the front hatch door's bottom edge goes up from 58 to about 92 mm.
- With the HR-100A, the beaker stands straight on its pan. Its round breeze break has no side door.

**The HR-202i as modelled** ([`parts5.hr202i`](parts5.py)). The figures are from A&D's [HR-i instruction manual](https://www.aandd.jp/products/manual/balances/hr-i.pdf), p.60 "External Dimensions", which byu-vcl's `lab_models` also uses. Every figure in this table is printed on that drawing:

| | mm |
|---|---|
| Overall (with doors and the top door's grip) | 217 W × 442 D × 316 H |
| Body | 200 × 428 × 310 |
| Pan | dia. 90, its centre 163 behind the front edge (265 in front of the back), its top 50 above the bench |
| Weighing chamber, inside | 183 × 164.5, 250 high above the pan; the pan's centre 86.5 behind the front glass's inner face |
| Side doors (slide back) | 148.5 × 251 |
| Top door (slides back over the tower) | 164 × 148.5 |

**Checked against A&D's own documents (2026-11-04):**
- **Sources:** the manual's p.59-60, and A&D Japan's 1:1 DXF of the outline ([`gh_hr-i.dxf`](https://www.aandd.co.jp/cad_storage/balance/gh_hr-i.dxf)).
- **The manual's drawing:** every number byu-vcl's model used is printed on it.
- **From the DXF,** for what the drawing doesn't dimension:
  - The display section is 73 deep, its top rising from 28 to 50 mm.
  - The chamber's floor and the side doors' sills are at 40 mm; the ceiling is at about 299 mm.
  - The side doors' opening runs from 40 to 291 mm up.
  - Behind the chamber, the rear housing (276-428 mm behind the front) is only 244 mm tall, falling to 221 at the back.
  - The top door and both side doors slide straight back about 205 mm.

**Specs from the manual:**
- **Repeatability:** 0.1 mg (0.02 mg in the fine range).
- **Stabilization:** about 3.5 s.
- **Interface:** RS-232C only (D-sub 9; factory 2400 baud, 7 data bits, even parity, 1 stop bit, CR LF; `Q` sends the weight now). USB needs A&D's converter.
- **Other:** 7.9 kg, with a built-in under-hook.

**A&D has discontinued the HR-202i.**
- A&D Japan's [HR-i page](https://www.aandd.co.jp/products/weighing/balance/bal-analytical/hr/) says production has ended.
- MNM Scales lists it at $2,989, out of stock, "replaced by GH-202".
- A&D draws the GH and HR-i series from one outline file, so a GH-202 should stand in the same place. Check its height first.

The lab's HR-100A: 198 × 294 × 315 mm, pan dia. 90 with its top 86.5 mm up (HR-A/HR-AZ manual p.74).

**Its place in v5:**
- **Position:** the pan centre sits under the dose point (x 33.4, y 4.76). The display faces the front hatch, and the mechanism tower stands under the back of the station.
- **Front:** the display unit sticks 64 mm out of the enclosure's front panel. The panel's opening runs down to the bench, and a brush strip closes the gap round the balance.
- **Clearance over its top:**

  | Part | Height |
  |---|---|
  | Parked EC and the lift bar | 328 mm |
  | NEMA 34 | 332.5 mm |
  | Lowest passing module | 412.6 mm |
  | Balance top | 316 mm |

- **Isolation:** the balance stands on the bench, or on the lab's isolating granite paver ([#146](https://github.com/vertical-cloud-lab/powder-doser/issues/146)), inside the doser's U-shaped base. It never touches the frame, so the motors' vibration reaches it only through the bench.
- **Reading it:** the Pi reads it over RS-232 with A&D's `Q` command, as the single doser reads its HR-100A ([`test/chain_rig.py`](test/chain_rig.py)). The rig's dose command now reads the dose from the balance itself, not from auger turns.

## What changed from v4, and why

| Change | Why | How it works |
|---|---|---|
| **The carousel is 80 mm higher** (bottom run's pitch line 465 mm, was 385; top rail 831, was 751) | v4's parked EC hangs to 248 mm and its NEMA 34 to 252 mm, both under a 316 mm balance | Everything above the bench moved up together (`_DZ`), so the loop, the station geometry, the side plates and the enclosure are v4's, just higher |
| **The EC rides on a lift bar carried by two P16s beside the balance** (was one P16 under it, in a guide cradle on a post) | v4's whole column (the cradle, its post, the P16 and its base clevis) stood inside the chamber, 2-110 mm behind the dose point | An 8 mm steel bar runs along y through two saddles that replace EC v4's clevis, on the same axis as v4's clevis pin. Each end sits in a printed end block. Each block holds a P16's rod-end tab on a 4 × 16 mm shoulder screw in 2 mm slots (v4's lost motion), so the two P16s, on two LAC boards sent the same target, can stop anywhere without forcing the dock. The pins sit exactly where v4's were, so the rise (28 mm), the tilt (68.7 mm of stroke at 30°, 101.5 mm at 50°) and v4's simulated dock forces carry over |
| **Guided shoes replace the cradle** | Without the cradle, nothing would keep the EC square as it rises. v3/v4's simulations found it pivots and topples on its pin even with the cradle's walls | Each end block carries a 14 × 10 × 20 mm shoe in a 14.2 mm vertical slot. The guide is a printed block on a 2020 station post on each side base rail. The bar is clamped in the EC, so the EC can't turn while either shoe is in its slot. The slots end where the EC seats. From there the dock and the module's hinge carry it, and the tilt lifts the shoes clear. This is the fix the v3/v4 simulations asked for, a back guide for the rise, but outside the balance |
| **No front base cross rail, no station rails** | The balance stands where they were | The base is U-shaped: the side rails and the back rail. The front posts are tied by the front side plate and the top cross rail |
| **The latch rail hangs from a 2020 beam off the -y side** (was a post at y -14) | v4's latch-rail post stood inside the tower's footprint | A post on the -y base rail carries a 166 mm beam along y. The rail's pad sits on the beam's end, at the same height as v4's post top, so the latch and tube rest work as in v4 |
| **No funnel; the beaker on a printed riser** | Sam ruled out a funnel because it cross-contaminates. A beaker on the pan would sit 340 mm under the exit | A PETG riser, about 30 g and tared with the beaker, puts the beaker's rim at 282 mm. That is a 154 mm fall from the exit, which stays on the hinge axis at every tilt. The rim is 9 mm under the side doors' opening (291 mm), so the beaker clears it lifted 6 mm out of the riser's cup and comes out through a side door; the top door is under the station |
| **Front hatch 300 × 330 mm, opening down to the bench** (was 180 × 230) | A hand has to reach the balance's side doors, and the display sticks out under the door | The door's bottom edge is 58 mm up, over the display unit. Open the hatch, open the balance's -y side door, set the beaker on the riser, shut both |
| **Doors during a dose** | The chamber is the draft shield | Only the top door is open, slid back over the tower, while the module doses. The reading that counts is taken with every door shut |

## How it works: one dose

1. **Index.** Carriage 1 indexes to the station, as in v4. The rail opens its latch, and the module settles 0.5 mm onto the tube rest.
2. **Beaker in, tare.** Open the front hatch and the balance's -y side door, set the beaker on the riser, shut both, and tare.
3. **Top door back.** Slide the top door back by hand, or by an actuator still to be designed.
4. **Rise.** Both P16s lift the bar together, and the shoes keep the EC square in their guides. In the last 6 mm the EC's finger opens the outlet door. The arms reach round the auger, and the EC seats on the plate's dock, lifting the module off its rest.
5. **Tilt and dose.** Tilt to 30°: 68.7 mm of stroke, with the shoes clear of their slots. The auger turns, and the dose falls 154 mm into the beaker. The Pi polls the balance with `Q` and stops at the target (`chain_rig.py dose-to`).
6. **After the dose.** Hold 0.5 s, tilt back, reverse one turn at rest, and undock. The shoes drop back into their slots on lead-ins, and the outlet door shuts before the EC parks.
7. **Read.** Shut the top door and read the stable mass.
8. **Next module.** Index to the next module. The parked EC is 28 mm under its dock and 12 mm over the balance.

## Checks

OCC boolean volume between every pair; anything over 0.5 mm³ counts. By-design contacts are skipped by part key ([`check_interference.py`](check_interference.py)). The balance is in every check.

CHECKS_TABLE

## Check before building

1. **The HR-202i isn't confirmed as the lab's.** If the lab has only the HR-100A, use it: it fits in the same place (raise the hatch door's bottom to about 92 mm), and the beaker goes straight on its pan.
2. **Get the balance first; the HR-202i is discontinued.** Its replacement, the GH-202, shares its outline drawing, but caliper whichever arrives before printing the riser. The riser's height sets the 154 mm fall and the beaker's 3 mm clearance under the side door's opening.
3. **The 154 mm fall through the open top door.** It is about twice the single doser's fall through its AutoTrickler lid. Measure drift with the top door open and the station running (TEST-PLAN T8a), and how far a fine powder strays (T8b). If either is too much, shorten the fall with a taller riser and a smaller beaker, or add a printed chimney on the riser, one per powder like the beaker.
4. **Two P16s instead of one.** Check that both LACs track within the 2 mm lost motion over the whole stroke (T6): log both pots through a 0-101.5 mm sweep.
5. **The guides replace the cradle's Kelvin seat.**
   - The parked EC is now located by the shoes in their slots (about 0.1 mm of play) and the P16s' positions, not by three balls.
   - The slots' 2 mm lead-ins at the top hand the EC from the guides to the dock: in the last 2 mm the shoes can move ±2 mm, so the cone and vee, not the guides, decide where it seats.
   - If the guides and the dock don't line up within that, the EC will bind instead of seating. Shim the guides at assembly (T6), and docking still needs T6b's ±0.5 mm capture.
6. **v4's open items stand.**
   - Its dock has no coil, so it needs about 8 N of preload per ball (T6c).
   - The outlet door's finger overlap.
   - The springs.
   - The magnets.
7. **Height.** The rig is 860 mm tall in its enclosure, 80 mm more than v4. Byu-vcl's Kardex opening is 727.5 mm.

## Not done

- **Not re-simulated.** v4's MuJoCo models weren't re-run. The station's kinematics are v4's (the same pin positions), but the guide is new, and the bar and two P16s add mass to the EC.
- **Not regenerated:**
  - The step-by-step ASSEMBLY.md and its renders.
  - The full movie.
  - The STEP/STL/DXF exports.
  - The Bambu slices.

  The CAD source builds all of them (`build.py`, `docs.py`, `render.py`); this round shows v5 in its stills and the balance-dose GIF.
- **The balance's top door is opened by hand** in this design. A robot-served station needs a small actuator for it, or a lid with a hole like the single doser's.
- **Prices:**
  - The new printed parts are filament.
  - The second P16 and LAC are Actuonix's list prices.
  - The 8 mm bar and the brush strip are estimates.

## Files

| File | What |
|---|---|
| [`params.py`](params.py) | v4's numbers with v5's at the end: the HR-202i, the riser, the lift bar, the shoes and guides, the raise |
| [`parts5.py`](parts5.py) | The HR-202i (body, display, front glass, pan, both side doors, top door), the riser, the lift bar, the bar end blocks, the guides, the P16 shelves, EC v5 |
| [`layout.py`](layout.py) | v4's layout with v5's frame, station and scale |
| [`check_interference.py`](check_interference.py) | home, `--tilt`, `--sweep`, `--swap`, `--scale` (the HR-202i and the HR-100A) |
| [`render_balance.py`](render_balance.py) | v5's stills and the balance-dose clip |
| [`bom.py`](bom.py) / [`BOM.md`](BOM.md) | The BoM, with the balance, the second P16 and LAC, the bar and the new printed parts |
| [`TEST-PLAN.md`](TEST-PLAN.md) | v4's tests with T6 and T8 rewritten for the balance |
| [`test/chain_rig.py`](test/chain_rig.py) | v4's driver with two LACs and the HR-202i |

The renders are in [`renders/`](renders): `rig_iso`, `rig_balance_front`, `rig_lift_bar`, `rig_dose30_section`, `rig_parked_section`, `rig_hr100a` and `features/balance_dose`.

To re-run:

```
pip install cadquery vtk pillow imageio imageio-ffmpeg numpy
python check_interference.py && python check_interference.py --tilt && python check_interference.py --sweep --step 2 && python check_interference.py --scale
xvfb-run -a python render_balance.py
python docs.py        # BOM.md, bom.csv, ASSEMBLY.md (v4's step texts)
```
