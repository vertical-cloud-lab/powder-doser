# Chain carousel v11: 0-90° with the station inside the loop, a straight rail, the door opened by the EC

**v11 is a variation on [v10](../chain-carousel-v10/README.md)** (the station inside the loop, Sam's favourite so far), and so on
[v7](../chain-carousel-v7/README.md), which stays the main version. It follows Sam's notes of 2026-11-25
([PR #185](https://github.com/vertical-cloud-lab/powder-doser/pull/185)):

> If the base plates need to be a bit longer, i.e. to give some more room for the rotation in the front, then go ahead and do that.
> The auger can move a bit as well to get the hinge closer to the plate, or the holes in the plate can be bigger ... The augers still
> need to be able to go up to 90 degrees. I was assuming this would mean punch a hole through the metal plate so the linear actuator
> has some more room ... I'm still confused about how the T rail thing works. Give me a profile view. Why is there a ramp? ... for the
> cap: ... [the EC] can extend all the way down to the dispensing end of the auger ... so it can directly open it ... move the
> solenoid up to the first third of the auger ... scale it to fit the scale with the higher draft cage (with the beaker sitting on a
> cylindrical pillar) ... Find a cheap but still good quality chain online, link it here, and apply those dimensions ... just make an
> open door for the scale ... no need to include wires in the model unless it changes.

Nothing is built. Every number here is a prediction from the CAD.

**Onshape (public):** [Multi-doser chain carousel, test rig v11](https://cad.onshape.com/documents/868943ea72f58c7a9d6e421e/w/b69337d1a5f8ee47f70e6908/e/951aa82be5a4c3bfe1ed5b08)
(ids in [`onshape/onshape_document.json`](onshape/onshape_document.json); 11 API calls in [`onshape/api_calls.jsonl`](onshape/api_calls.jsonl):
10 for the import, 1 to confirm it is public). It was imported from `step/chain_carousel_rig_v11.step` by
[`onshape/onshape_build.py`](onshape/onshape_build.py). Earlier versions:
[v10](https://cad.onshape.com/documents/99bd983c585992043f2eff96/w/7b5725dc5dfb7fe370fa0c71/e/56a319b93daf812d262f5eab),
[v9](https://cad.onshape.com/documents/9aadc21a931d5337ff05de71/w/1dea03d63eb704d060d84c2a/e/caa98ea728a9da9006767590),
[v8](https://cad.onshape.com/documents/a093aef97b81fce9ce0f322f/w/7b029051ee0ec62ff198253f/e/7518535395874b79077ff86b),
[v7 (main)](https://cad.onshape.com/documents/291664f38c67a4672a86f025/w/e67d1b706aa4b873fa8c68e8/e/4802634f69ef3323004d7bf6).

![Overview](renders/v11/overview_v11.gif)

## What changed, and why

| # | Sam asked | v11 | How it works | Clip |
|---|---|---|---|---|
| 1 | "The augers still need to be able to go up to 90 degrees ... If the base plates need to be a bit longer, i.e. to give some more room for the rotation in the front, then go ahead" | **The carriages are 40 mm longer** (the chains 345 mm apart instead of 305; each carriage 391 mm over its tongues) and **the hinge is 40 mm further back** (73 mm behind the front chain's centre plane, v10: 33) | On the plate's side everything near the hinge swings forward as the module tilts. In v10 the EC's front reached the front chain's A-1 link at 70°. With the hinge 73 mm back, the module and the EC stand clear at 90°: the nearest approaches are the EC to the carriage's opening edge (2.5 mm), and the solenoid to the carriage (2.5 mm) and its front tab's locknut (3.7 mm) | [tilt90](renders/v11/tilt90_v11.gif) |
| 1 | "punch a hole through the metal plate so the linear actuator has some more room. If this requires new mounts (i.e. a new bar of 8020 across the outside, or just a 3D-printed mount) then design those" | **A P16-150 (back from v10's P16-100), its base outside the front side plate, through a 22 × 68 mm slot in the plate.** Its rear tab sits in a printed clevis under a **new 2020 bar across the front posts' front faces** (z 620-640, in front of the top bearings) | 0-90° takes 131 mm of travel, more than a P16-100 has. Laid out numerically, no base position inside the front plate gets the module to 90°: the line of pull runs over centre, or the actuator hits the top sprocket. With the base pin 26 mm in front of the plate, the P16-150 runs from 139.2 mm out (rest) to 8.3 mm out (90°). That leaves 10.8 mm short of full extension and 8.3 mm over full retraction, with a lever about the hinge of 30 mm or more. The front acrylic panel moves out to 30 mm standoffs to clear the bar and the P16's housing | [tilt90](renders/v11/tilt90_v11.gif) |
| 2 | "Why is there a ramp? I was assuming each carriage would just move straight through it ... not lifting if it's not necessary" and "The auger can move a bit as well to get the hinge closer to the plate, or the holes in the plate can be bigger to accommodate the mounting plate" | **No lift.** The rail's lips are level; its ends only flare (2.5 mm sideways and toward the loop, 1.5 mm toward the plate, over 8 mm) to steer a T that arrives a little off line. **The hinge sits 5 mm nearer the carriage plate**, so the mounting plate sinks into the carriage's opening. **The pinion is 24T** (KHK SS1-24 class, v2-v10: 20T) | v10 lifted every module 4° only to bring its 44T gear up to the pinion while keeping the pinion over the passing carriages. With the hinge 5 mm nearer the carriage, the gear pokes 5 mm past the carriage at rest, and a 24T pinion (centre distance 34.25 mm) meets it there. At rest each module sits on its own carriage, its T 0.2 mm over the lips; the lips take it only when the P16 pulls. A 20T pinion would put the NEMA 11's body 0.25 mm off the passing plates; the 24T puts it 2.25 mm off | [rail profile](renders/v11/rail_profile_v11.gif), [rail](renders/v11/rail_v11.gif) |
| 3 | "if the electronics carriage is already taking up space on the inside, I think it can extend all the way down to the dispensing end of the auger ... so it can directly open it ... Maybe that part can have a ramp ... Keep this part as simple as possible" | **The EC reaches forward over the outlet.** Each shutter (v10's) carries a 1.5 mm stainless rod up its spring's axis and out through the housing's cap to a small printed head. **The EC's front is a ramp slot** whose two wedge lips catch the head and draw it 6 mm toward the loop as the module arrives | No cable, sleeve or guide (v10 had all three). The door is fully open within 7 mm of the station and shut again 16.5 mm out. It is still v4's door: the shutter opens toward the plate, so it stays out of the falling dose | [door](renders/v11/door_v11.gif), [rail profile](renders/v11/rail_profile_v11.gif) (part 3) |
| 4 | "move the solenoid up to the first third of the auger. That's where we get the most effective taps" | **The solenoid sits over clip 1**, 32 mm behind the exit: 13 % of the auger's length (v10: over clip 2, 156 mm, 62 %) | It stands in a collar in the EC's spine, plunger toward the plate, 1.2 mm off it where clip 1 holds the tube. It turns with the module, so it taps the same spot at every tilt | [solenoid](renders/v11/solenoid_v11.gif) |
| 5 | "scale it to fit the scale with the higher draft cage (with the beaker sitting on a cylindrical pillar). This means that smaller scales could work on a block without the draft cage, but the draft cage would also be fine" | **The balance keeps its tall draft cage and stands on the bench** (v7's model, its cage 315 mm tall like the lab's HR-100A). **The carousel is 98.5 mm lower** (the bottom run at z 366.5, v10: 465), so the passing 44T gears clear the cage's top by 4 mm. **The beaker sits on a cylindrical pillar** (a printed 40 mm tube) inside the cage; a **dosing lid** with a 24 mm hole replaces the top door | The exit is 33 mm over the beaker's rim (v10 had no cage: 18): 27 mm down to the cage's top (the gear's 23 mm radius and its 4 mm clearance), then the lid and 3 mm under it. A smaller balance can stand on a block with its cage off: the beaker on its pan can then come up to 14 mm under the exit, under the passing tubes. The pillar and beaker take about half of the HR-100A's 102 g | [balance](renders/v11/balance_v11.gif) |
| 6 | "Find a cheap but still good quality chain online, link it here, and apply those dimensions to the chain in the model" | **[Nitro Chain RC35-1R-10FT](https://www.nitrochain.com/35-roller-chain-10ft), $23.53 per 10 ft roll** (N2 series: heat treated, pre-lubricated, ANSI B29.1; read 2026-11-26), with Nitro's [CL35-A1](https://www.nitrochain.com/35-a1-standard-attachment-connecting-link) links ($2.55) and [CL35](https://www.nitrochain.com/35-standard-connecting-link) connecting links ($0.79) | The model already matched Nitro's published numbers (pitch, bushing, inner width, pin, h2, T, width over the pins). Two things were missing and are now drawn: the 0.518 in width over a connecting link (the A-1 links the carriages bolt to), and the plates' waist (0.75 × h2, scaled off Nitro's drawing, which doesn't give it; v2-v10 drew it shallower). U.S. Tsubaki's RS35 is the premium alternative, at about 4.7 times the price | [chain](renders/v11/chain_nitro_v11.png) |
| 7 | "for this version, just make an open door for the scale to go into--don't make the whole enclosure for the scale" | **The front acrylic panel has an open doorway, 240 × 330 mm from the bench up**, that the balance slides through. No bay window, no weighing chamber, no granite block | The balance's display sticks out through the doorway; its own cage is its draft shield | [balance](renders/v11/balance_v11.gif) |
| 8 | "no need to include wires in the model unless it changes. Just keep a hole in the plate so the wires can get out and run down" | **No wires drawn.** The 20 mm grommet hole stays in the front side plate, under the P16's slot | The bundle runs as in v10, along the EC's arm and the P16, out through the grommet | |

| 0-90° with one P16-150 ([MP4](renders/v11/tilt90_v11.mp4)) | The door, opened by the EC's front ramp ([MP4](renders/v11/door_v11.mp4)) |
|---|---|
| ![](renders/v11/tilt90_v11.gif) | ![](renders/v11/door_v11.gif) |

| The rail in 3D: straight in, the gear meets the pinion at rest ([MP4](renders/v11/rail_v11.mp4)) | The solenoid over clip 1 ([MP4](renders/v11/solenoid_v11.mp4)) |
|---|---|
| ![](renders/v11/rail_v11.gif) | ![](renders/v11/solenoid_v11.gif) |

**The balance with its tall cage, the pillar and the dosing lid** ([MP4](renders/v11/balance_v11.mp4)):

![](renders/v11/balance_v11.gif)

## How the rail works, in profile (Sam's question)

True sections of the CAD ([`rail_profile.py`](rail_profile.py), [MP4](renders/v11/rail_profile_v11.mp4)), with the inside of the
loop at the top:

![](renders/v11/rail_profile_v11.gif)

1. **Along the travel, through a lip and the T's head.** The module arrives from the right, the way the machine runs. The T's head
   enters the slot's flared mouth and runs along level lips. Nothing lifts it.
2. **Across the travel, at the station.** The T's head sits under the EC's ceiling and over the two lips, its stem between them,
   0.3 mm clear each side. At rest the head is 0.2 mm over the lips: the module rests on its own carriage (hinge pins and latch
   shelf), and the lips pick it up only when the P16 pulls the EC.
3. **The door ramp, through the door rod.** This is the one ramp that moves something. Its lips catch the rod's head and draw it
   6 mm toward the loop, which slides the shutter off the exit.

**Why v10 had a ramp.** In v10 the gear's tip was level with the carriage's inner face at rest. The pinion has to sit over the
passing carriages, so the gear couldn't reach it without the module turning 4°. That is what the ramps did. v11 moves the hinge
5 mm nearer the carriage instead, so the gear meets the pinion at rest. The ramps were only there for the mesh, so they're gone;
the flares stay for alignment.

## 90°: what stopped v10, and what v11 changes

| | v10 | v11 |
|---|---|---|
| Hinge behind the front chain's centre plane | 33 mm | **73 mm** (carriages 40 mm longer) |
| First contact | 70°: the EC's front at the station carriage's front A-1 link | **none at 0-90°** |
| Actuator | P16-100, base on the front side plate's inner face | **P16-150, base outside the front side plate, through a slot** |
| Travel for the range | 88 mm for 4-65° | **131 mm for 0-90°** |

**The P16-150's extension and lever** (`layout.p16_11_ext`, `layout.p16_11_lever`; the table in [`test/chain_rig.py`](test/chain_rig.py)):

| Tilt | 0° (rest) | 10° | 20° | 30° | 40° | 50° | 60° | 70° | 80° | 90° |
|---|---|---|---|---|---|---|---|---|---|---|
| P16 out, of 150 mm | 139.2 | 123.5 | 106.8 | 89.6 | 72.4 | 55.6 | 40.1 | 26.4 | 15.6 | 8.3 |
| Its lever about the hinge, mm | 87 | 93 | 97 | 99 | 98 | 93 | 84 | 71 | 53 | 30 |

The module and the EC at 90° (by a minimum-distance check on the CAD): the EC passes the station carriage's extended opening by
2.5 mm, and the solenoid passes the carriage by 2.5 mm and its front tab's locknut by 3.7 mm. The mounting plate runs 0.8 mm
inside the opening's sides, as in v4-v10.

## Auger-to-beaker height

| From the auger's exit | Single doser | v7 | v9 | v10 | **v11** |
|---|---|---|---|---|---|
| to the beaker's rim | about 85 mm (±15) | 154 mm | 32 mm | 18 mm | **33 mm** |
| to the beaker's floor | about 153 mm | 201 mm | 80 mm | 67 mm | **82 mm** |
| the balance | HR-100A, cage on | cage on, beaker on a riser | cage off, on a block | cage off, on a block | **tall cage on, on the bench; beaker on a pillar** |
| what sets it | | the cage's lid under the EC | the EC's door finger | the auger's tube and the deck | the passing gears over the cage's top, and the cage's top frame |

With a smaller balance on a block and its cage off, v11 can bring the rim to 14 mm under the exit: the tube passes 12.5 mm under
the exit, with 1.5 mm to spare.

## One dose

1. **Index.** The NEMA 34 moves both chains 8 links, with the NEMA 11 left free.
   - The latch cam pulls the arriving module's pin.
   - The T slides straight into the rail, and the 44T gear slides into mesh with the 24T pinion from the side.
   - The EC's front ramp draws the door's rod 6 mm and opens the outlet.
2. **Pull up.** The P16 retracts from 139.2 mm, and the EC and the module turn about the hinge to the dose angle (30° by default:
   89.6 mm out). The EC's shoe lifts out of its seat.
3. **Dose.** The NEMA 11 turns the auger; the solenoid taps the plate over clip 1. The dose falls 33 mm from the exit through the
   lid's hole into the beaker on its pillar. The exit is on the hinge axis, so it doesn't move with the tilt.
4. **Back.**
   - Hold 0.5 s, then the P16 extends fully: the module sets down on its carriage, and the shoe re-seats.
   - Reverse the auger one turn at rest (the leakage study).
5. **Next index.** The T slides out of the rail's far end, the door shuts, and the latch closes behind it.

## Checks

These are OCC boolean overlaps between parts; anything over 0.5 mm³ counts as a clash. By-design contacts are skipped by part key
(v11's are at the end of SKIP in [`check_interference.py`](check_interference.py)). The balance, its pillar and the beaker are in
every check.

| Check | What moves | Result |
|---|---|---|
| Home ([`checks/home.json`](checks/home.json)) | Every pair of the 829 instances | **0** |
| `--tilt11` ([`tilt_a.json`](checks/tilt_a.json), [`tilt_c.json`](checks/tilt_c.json), [`tilt_b.json`](checks/tilt_b.json)) | Module 1, the EC and the P16 (its body swings on its base pin, its rod slides) at 0, 10, 20 ... 80, 85 and 90° against everything else | **0 at every angle** |
| [`sweep_station.py`](sweep_station.py) ([`checks/sweep_station.json`](checks/sweep_station.json)) | Every carriage and module within 2.2 modules of the station, over one module of travel in 1-link steps (9 poses), each door opened by the EC's ramp as it passes, against the EC, the P16 and its bar, the guide, the beam, the balance, the pillar and the beaker | **0** |

The first runs found and fixed these:
- the P16's housing on the top-front bearing's tensioner block (25 mm³): the P16's plane moved from world y −33 to −31;
- the ladder's upper rungs and their brackets in the back side plate, and the lower rungs' brackets on the posts' foot brackets
  (the lower carousel brought the back plate's edge down): the rungs moved to z 86 and 214;
- the latch cam's foot in the back hold-down (1,096 mm³; with the hinge 5 mm nearer the carriage the cam came 5 mm nearer): its web
  and foot moved beside the hold-down;
- the T-bracket's foot 1 mm into the rail block (313 mm³): the rail's underside moved to 1 mm over the passing feet;
- the EC's guide hanger across the B− shaft (80 mm³): the station beam moved from y −60 to −56;
- the front bar's screws drawn head-inward, into the front panel;
- at 90° the EC passed the station carriage's opening edge by only 0.5 mm: the opening now runs 2 mm further forward.

## Cost

**$2,083.31, or $1,941.92 without test gear** ([BOM.md](BOM.md)). v10 was $2,352.10 ($2,210.71): $268.79 less. Lines marked
estimate add up to $473.94.
- **Removed:** v10's granite block, the bay window and the weighing chamber (two of v10's six acrylic sheets, the cement, the bay
  door's hinges), the door cables, the P16-100 and its bracket's inserts, half of the M2 screws and inserts (the cable guides').
- **Added:**
  - the P16-150 ($90, back from v7-v9);
  - a second 72 in shaft bar (the shafts are 40 mm longer);
  - the 24T pinion (estimated);
  - the front bar's screws and T-nuts, the P16's printed clevis;
  - the door rods (estimated) and their printed heads;
  - the beaker's pillar and the dosing lid (from an acrylic offcut);
  - two spare Nitro CL35 connecting links.
- **The same:** the NEMA 11, the solenoid, the one LAC, the balance (the lab's), the enclosure's other panels, the wiring lines.

## Check before building

1. **The P16-150 through the front plate (TEST-PLAN T6).** Print the clevis and check that the P16 swings freely through the slot
   over 0-90° and that the 30 mm lever at 90° holds the module and EC still (the module's weight is nearly over the hinge there).
2. **The gear meets the pinion at rest, from the side (T6a).** Every index slides a 44T gear into mesh with the stationary pinion
   over its last 11 mm, as in v10, but now every passing module's gear meshes as it goes by. Leave the NEMA 11 free while the chain
   moves. With the hinge 5 mm nearer the carriage, the mesh depth at rest is set by the hinge pins and the latch shelf, not the rail;
   measure the centre distance at rest and at 30°: the T's 0.2 mm gap opens it by about 0.3 mm once the lips take the module.
3. **The door rod (T8a).** Check that the door's spring (0.3-0.6 N) shuts it against the rod's friction in the cap's hole, upside
   down on the top run too, and that the head stays on its rod (glued) after 1000 passes through the ramp.
4. **The solenoid over clip 1 (T8d):** check that its taps move powder better than v10's over clip 2, as Sam expects.
5. **The tall cage under the carousel (T8c):** the passing gears clear the cage's top frame by 4 mm. Measure the lab's balance:
   if its cage is taller than 315 mm, raise the carousel by the difference (Z_RUN). The pillar plus the beaker weighs about 50 g.
6. **Reprints:** every carriage (40 mm longer, the opening longer, the lugs 5 mm shorter), every plate (no motor relief), every
   door (the rod and head), the latch cam. The shafts are 40 mm longer, so they need two 72 in bars.
7. v10's open items stand: the latch spring, and which balance the lab uses.

## Not done

- **Not simulated:** the station's dynamics, and the gear's sideways engagement (a tooth-contact model, as in
  [`../gear-mesh/`](../gear-mesh/README.md), would be the next study). The checks are static poses.
- **Not rerun:** `--swap` and `--latch`. The side hatch is v10's, and the home check and station sweep cover the latch cam.
- **Not regenerated:** the stills, the step-by-step ASSEMBLY renders and the Bambu slices. The STLs are exported. The 391 mm
  carriage needs the H2D's bed diagonal (it fits to about 400 mm at 66 mm wide); I haven't sliced it.
- **Prices:** the 24T pinion, the door rods, the 30 mm standoffs and the M5 × 35 screws are estimates.

## Files

| File | What |
|---|---|
| [`params.py`](params.py) | v10's numbers with v11's at the end; the base changes at the top (`CHAIN_L` 345, `HINGE_X` 73, `HINGE_RAISE11` 5, `Z_RUN` 366.5) and the chain's (`PIN_LEN_CL`, `PLATE_WAIST`) |
| [`parts11.py`](parts11.py) | The T-bracket and the straight rail, the door rod, head and ramp, EC v11 and the 24T pinion, the P16's clevis, carriage v11, the plate's additions, the tall-cage balance and its lid, the pillar, the latch cam |
| [`parts.py`](parts.py) | v2's builders; the chain links drawn to Nitro's RC35 (waisted plates, straight connecting-link plates, 0.518 in over a connecting link) |
| [`layout.py`](layout.py) | v10's layout with v11's station (`_station_v11`, `ec11_frame`, `p16_11_ext`, `p16_11_lever`, `p16_slot11_z`), the balance on the bench and the front doorway |
| [`check_interference.py`](check_interference.py), [`sweep_station.py`](sweep_station.py) | Home, `--tilt11`, station sweep |
| [`explain11.py`](explain11.py), [`rail_profile.py`](rail_profile.py), [`chain_nitro.py`](chain_nitro.py) | The clips in `renders/v11/` (GIF + MP4 each), the rail's profile view, the chain figure |
| [`build.py`](build.py) | STEP assembly and components, the printed parts' STLs (`ec11.stl`, `t_bracket.stl`, `door_head11.stl`, `p16_bracket11.stl`, `guide11.stl`, `latch_rail11.stl`, `pillar11.stl`, `mounting_plate_v11.stl`, `carriage.stl`), the DXFs |
| [`bom.py`](bom.py) / [`BOM.md`](BOM.md) | The BoM |
| [`TEST-PLAN.md`](TEST-PLAN.md) | v10's tests with the station's rewritten for v11 |
| [`test/chain_rig.py`](test/chain_rig.py) | The Pi driver: one P16-150 (0-90°, `P16_TABLE` from `layout.p16_11_ext`), the 24T pinion's ratio |

To re-run:

```
pip install cadquery vtk pillow imageio imageio-ffmpeg numpy matplotlib
python check_interference.py && python check_interference.py --tilt11 && python sweep_station.py
xvfb-run -a python explain11.py overview tilt90 rail door solenoid balance
python rail_profile.py && python chain_nitro.py && python build.py && python bom.py
```
