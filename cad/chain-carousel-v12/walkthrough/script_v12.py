"""The v12 walkthrough's chapters: narration (read by Piper, offline) and the pictures for each (paths from cad/chain-carousel-v12/;
"../" reaches the other designs). Numbers come from the README, sim/README.md and the checks; keep them in step when those change.
{STALL0} etc. are filled from sim/out/cycle.json by make_walkthrough.py."""

TITLE = "Multi-doser chain carousel v12 · PR #185"

CHAPTERS = [
    dict(title="What v12 is",
         text=("This is the multi-doser chain carousel, version twelve. Thirteen auger dosing modules ride on two roller chains in a "
               "vertical loop, and one station, inside the loop, takes each module in turn, tilts it, and doses into a beaker on an "
               "analytical balance. Version twelve is version eleven with one change at the station: the small stepper motor that turns "
               "each auger, and its pinion, now ride on a spring-loaded cradle. A hall switch on the cradle tells the controller when the "
               "pinion is resting on the gear's tips, the controller turns it slowly until it drops into mesh, and the electronics carriage "
               "now rests on two guide seats instead of one. Nothing has been built yet, so every number in this video is a prediction "
               "from the CAD and the simulations."),
         visuals=[dict(path="renders/v12/overview_v12.mp4", weight=2.0), dict(path="renders/rig_iso.png")]),
    dict(title="The frame, the chain and a module",
         text=("The frame, the chain loop and the modules are version eleven's. Twenty-twenty extrusion and quarter-inch aluminium side "
               "plates carry four corner shafts with thirty-two tooth sprockets, and two number thirty-five chains with an attachment link "
               "every eighth pitch. Each module is the lab's mounting plate carried on to the auger's cap, with a printed T-bracket under "
               "it, a spring-loaded outlet door, and a latch that holds it upside down on the top run. One more version twelve fix is here: "
               "the outlet door's spring tower is now bored out, and the shutter has a round boss the door's rod presses into. In version "
               "eleven the rod had nowhere to go."),
         visuals=[dict(path="renders/steps/step_05.png"), dict(path="renders/steps/step_07.png"), dict(path="renders/steps/step_09.png"),
                  dict(path="renders/rig_load.png")]),
    dict(title="Why version eleven needed a change",
         text=("In version eleven, each index slides the next module's forty-four tooth gear sideways into mesh with a twenty-four tooth "
               "pinion that was bolted to the electronics carriage. When a gear tooth landed on the tip of a pinion tooth, nothing could "
               "give: the module rests on its own carriage and the electronics carriage on its actuator. In the MuJoCo model, with real "
               "tooth contact, about one index in four jammed, with the chain driving the tips together at over a hundred newtons."),
         visuals=[dict(path="../chain-carousel-v11/renders/v11/mesh_entry_v11.mp4", weight=1.5)]),
    dict(title="The spring-loaded cradle",
         text=("Version twelve hangs the motor and its pinion on a printed cradle. The cradle pivots on two three millimetre dowels, on "
               "the side the gears arrive from, level with the pinion. A spring over the motor, about one newton per millimetre, presses the "
               "pinion into the gear with six newtons, and an M3 set screw stops it point four millimetres past tight mesh when no gear is "
               "there. A US5881 hall switch on the cradle's lug sits just below a magnet in the electronics carriage. The real spring is "
               "McMaster's 9657K284: nought point nine eight newtons per millimetre, nineteen millimetres long."),
         visuals=[dict(path="renders/v12/cradle_v12.mp4", start=0.0, end=8.0), dict(path="renders/rig_cradle.png")]),
    dict(title="A tooth on a tooth: lift, switch, seek",
         text=("Now the worst arrival. A gear tooth lands on a pinion tooth's tip. Instead of jamming, the gear pushes the pinion up about "
               "two millimetres against the spring, and the hall switch slides under its magnet: lifted. After every index the controller "
               "turns the pinion slowly forward and then back, a quarter turn per second for a fifth of a second each way, so the auger ends "
               "where it started. The pinion drops into the next gap and the switch reads seated. If it still reads lifted, a second try "
               "runs the other way round, and if that fails too, the controller backs the chain off three millimetres and indexes again."),
         visuals=[dict(path="renders/v12/mesh_entry_v12.mp4", weight=2.0), dict(path="renders/v12/cradle_v12.mp4", start=8.0)]),
    dict(title="What the simulations found",
         text=("The same MuJoCo model, rebuilt round the cradle, ran five hundred and four indexes over the same tolerance stack, from half a "
               "millimetre too near to a millimetre too far, and three clevis stiffnesses. None jammed. With the design as drawn, one in "
               "four arrivals landed on the gear's tips, and the first seek cleared every one of them. The switch's reading after the seek "
               "was right every time. The peak chain force fell from over a hundred newtons to nineteen. The one case that needed more was "
               "dry teeth, with no PTFE lubricant: five arrivals in twelve stayed on the tips through both seeks, every one read as lifted, "
               "and backing off and re-indexing {DRY_CLEARED}."),
         visuals=[dict(path="sim/out/entry_outcomes.png")]),
    dict(title="What holds the mesh while it doses",
         text=("While it doses, the actuator pulls the electronics carriage, the cradle and the module up about the hinge together, and the "
               "spring keeps the pinion in tight mesh at every angle, up to ninety degrees, where the module's weight no longer helps. Over "
               "the hold cycles no tooth jumped. One thing changed from what we expected: the spring's reaction, about six newtons, is "
               "twice the electronics carriage's weight, so with a module in mesh it lifts the carriage off its guide seats, and the "
               "rail's lips under the module's T-bracket hold it instead."),
         visuals=[dict(path="renders/v12/mesh_hold_v12.mp4", weight=2.0)]),
    dict(title="Stall torque against what the auger needs",
         text=("The cost of a preloaded mesh is friction. When the auger's load is ramped up until something gives, the motor stalls "
               "first at every angle, at {STALL_RANGE} newton millimetres on the auger, against version eleven's seventy-seven to ninety, and "
               "against the five to thirty the auger is estimated to need. Putting the pivot ten millimetres nearer the gear would recover "
               "about {PIVOT_GAIN} percent of that, at the cost of an occasional second seek; a four newton spring would do the same."),
         visuals=[dict(path="sim/out/stall_vs_tilt.png")]),
    dict(title="The second seat",
         text=("Version eleven's electronics carriage rested on the actuator's pin and one guide shoe, both on the actuator's side, so between "
               "modules it could roll on the clevis's play. Version twelve adds a second shoe on the far side of the module, in a second funnel "
               "seat on a second twenty-twenty beam across the loop. Between modules, with the loosest clevis, it rolls a quarter of a degree "
               "instead of one and a third, which keeps the motor a millimetre over the passing plates instead of six tenths."),
         visuals=[dict(path="renders/v12/seats_v12.mp4", weight=1.5), dict(path="renders/rig_seats.png")]),
    dict(title="Checks",
         text=("Every part was checked against every other in solid geometry, with anything over half a cubic millimetre counted as a "
               "clash: the home pose, the cradle over its whole travel at rest and tilted, the tilt from zero to ninety degrees, a module of "
               "chain travel through the station, the swap at the side hatch, the latch cam and the outlet doors. {CHECKS} The checks also "
               "found three things in version eleven's drawings that were hidden by skipped pairs: no slot for the actuator's rod-end tab, "
               "the motor's shaft running into the rail block, and the door spring buried in a solid tower. All three are fixed."),
         visuals=[dict(path="renders/rig_cradle_lifted.png"), dict(path="renders/rig_tilt90.png")]),
    dict(title="Printing and buying",
         text=("Every printed part was sliced in Bambu Studio, in PETG, on the H2D's left nozzle or the A1 mini. {PRINT} The bill of materials "
               "comes to {BOM_TOTAL} dollars, {BOM_DELTA} dollars more than version eleven: the dowels, the spring and the set screw were read "
               "from McMaster's tables through the lab's Raspberry Pi, logged out."),
         visuals=[dict(path="../print/chain-carousel-v12/plates.png")]),
    dict(title="Before building",
         text=("Before building, three things to check. Set the stop with module one in mesh, so the pinion drops point four millimetres "
               "when the module leaves. Set the hall switch so it reads lifted between six tenths and one millimetre of lift. And keep the "
               "teeth lubricated with dry PTFE: in the model, dry teeth were the one case the seek couldn't clear on its own. The design "
               "files, the simulations and this video's sources are on GitHub, and the model is public in Onshape."),
         visuals=[dict(path="renders/rig_cradle.png")]),
]
