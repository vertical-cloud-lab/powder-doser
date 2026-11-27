"""The v11 walkthrough's chapters: narration (read by Piper, offline) and the pictures for each (paths from cad/chain-carousel-v11/).
Numbers come from the README, sim/README.md and the checks; keep them in step when those change."""

TITLE = "Multi-doser chain carousel v11 · PR #185"

CHAPTERS = [
    dict(title="What v11 is",
         text=("This is the multi-doser chain carousel, version eleven. Thirteen auger dosing modules ride on two roller chains in a "
               "vertical loop. One station, inside the loop, takes each module in turn, tilts it, and doses straight down into a beaker on "
               "an analytical balance. Version eleven follows the design notes of November twenty-fifth: the augers tilt all the way to ninety "
               "degrees, the keyed rail no longer lifts the module, the electronics carriage opens each outlet door itself, and the balance "
               "keeps its tall draft cage. Nothing has been built yet, so every number in this video is a prediction from the CAD and the "
               "simulations."),
         visuals=[dict(path="renders/v11/overview_v11.mp4", weight=2.0), dict(path="renders/rig_iso.png")]),
    dict(title="The frame and the chain loop",
         text=("The frame is twenty-twenty aluminium extrusion with quarter-inch aluminium side plates, tied together by ladder rungs. "
               "Four corner shafts each carry a pair of thirty-two tooth sprockets, so the front and back chains can't drift out of step. "
               "The chains are Nitro Chain's number thirty-five roller chain, about twenty-four dollars for a ten-foot roll, and every eighth "
               "link is an A-1 attachment link that a printed carriage bolts to. A NEMA thirty-four stepper drives one shaft through a short "
               "drive chain."),
         visuals=[dict(path="renders/steps/step_05.png"), dict(path="renders/steps/step_07.png"), dict(path="renders/v11/chain_nitro_v11.png"),
                  dict(path="renders/rig_back_iso.png")]),
    dict(title="A module",
         text=("Each module is the lab's mounting plate, carried on to the auger's cap so it supports the whole tube. The auger snaps into two "
               "clips and rests on a saddle under the cap. A printed T-bracket under the plate is the key that the station's rail catches. "
               "A spring-loaded shutter covers the three millimetre outlet, with a stainless rod up its spring that the station pulls to open "
               "it. The plate hangs on two hinge pins on its carriage's outer face, and a spring latch at its back end holds it, even upside "
               "down on the top run."),
         visuals=[dict(path="renders/steps/step_09.png"), dict(path="renders/rig_load.png"), dict(path="renders/rig_latch_closed.png")]),
    dict(title="Indexing into the station",
         text=("To dose, the NEMA thirty-four moves both chains eight links, one module. As the carriage arrives, a fixed cam draws its "
               "latch pin back, so the module is free to tilt inward. Its T-bracket slides straight into the electronics carriage's rail, "
               "whose flared ends only line it up. And a ramp at the front of the electronics carriage catches the door rod's head and draws "
               "it six millimetres, which slides the shutter off the outlet."),
         visuals=[dict(path="renders/v11/rail_v11.mp4", weight=1.6), dict(path="renders/v11/rail_profile_v11.mp4"), dict(path="renders/v11/door_v11.mp4")]),
    dict(title="How the gear meets the pinion",
         text=("The auger's forty-four tooth gear pokes up through the carriage's opening, and the electronics carriage holds a twenty-four "
               "tooth steel pinion on its NEMA eleven motor just above it. Nothing presses the two together. The thirty-four and a quarter "
               "millimetres between their axes is set by where two separate parts sit: the module, on its hinge pins and latch shelf, and the "
               "electronics carriage, on its guide seat and the actuator's pin. During every index the motor's driver is off, so the pinion is "
               "free: as the gear slides in from the side, its teeth roll the pinion round about fifty degrees, like a rack. A MuJoCo model "
               "with real tooth contact shows where this is fragile. In two of every twelve starting positions, and up to five near the "
               "ends of the tolerance range, a gear tooth lands on the tip of a pinion tooth. Nothing in version eleven can give, so the chain "
               "drives the two tips together and the index jams. The model also shows that the centre distance has only a seven tenths of a "
               "millimetre window: below thirty-four millimetres the teeth bind, and above thirty-four point seven two the contact ratio "
               "drops below one."),
         visuals=[dict(path="renders/rig_gear.png"), dict(path="renders/v11/mesh_entry_v11.mp4", weight=2.6), dict(path="sim/out/entry_outcomes.png"),
                  dict(path="sim/out/centre_distance_window.png")]),
    dict(title="What holds the mesh while it doses",
         text=("When the actuator pulls, the electronics carriage lifts off its seat, and after two tenths of a millimetre the lips under "
               "the T's head pick up the module. From then on the module, the T, the electronics carriage and the pinion turn about the hinge "
               "as one piece. The teeth's own separating force pushes the gear away from the pinion, but the T's head is already resting on "
               "the lips, so the gear has nowhere to go. That captured T is what replaces gravity, and it works the same at ninety degrees, "
               "where the module's weight acts along the auger and helps nothing. In the model, no tooth jumped in any tilt and dose cycle, "
               "at thirty or ninety degrees, with the solenoid tapping. When the auger's load was ramped up, the motor stalled before any "
               "tooth jumped, every time. The actuator needed under thirty newtons, well inside its rating."),
         visuals=[dict(path="renders/v11/mesh_hold_v11.mp4", weight=3.0)]),
    dict(title="Tilting to ninety degrees",
         text=("The longer carriages put the hinge seventy-three millimetres behind the front chain, so the module and the electronics "
               "carriage can swing all the way to ninety degrees. One Actuonix P16, with a hundred and fifty millimetre stroke, does it. It "
               "runs through a slot in the front side plate to a clevis under a new bar across the front posts. It is a hundred and thirty-nine "
               "millimetres out at rest and eight at ninety degrees, and its lever about the hinge never drops below thirty millimetres."),
         visuals=[dict(path="renders/v11/tilt90_v11.mp4", weight=2.0), dict(path="renders/rig_p16.png")]),
    dict(title="Dosing into the balance",
         text=("The solenoid now sits over clip one, in the first third of the auger, where taps move powder best. The outlet stays on the "
               "hinge axis at every tilt, so the dose always falls in the same place: thirty-three millimetres down, through a hole in a "
               "dosing lid set into the balance's draft cage, into a beaker on a printed pillar. After a dose the station holds for half a "
               "second, tilts back, sets the module on its shelf, and turns the auger back one revolution at rest, which the leakage study "
               "found clears the outlet without spilling."),
         visuals=[dict(path="renders/v11/solenoid_v11.mp4"), dict(path="renders/v11/balance_v11.mp4", weight=1.5), dict(path="renders/rig_drop.png")]),
    dict(title="Checks",
         text="",
         visuals=[]),
    dict(title="Printing and buying",
         text="",
         visuals=[]),
    dict(title="Next: a spring-loaded pinion",
         text=("The simulations point to one change above all: a spring. Put the NEMA eleven and its pinion on a small "
               "carrier that pivots in the electronics carriage, with a spring pressing the pinion into the gear with about six newtons, past "
               "a set-screw stop. Then the pinion always sits in tight mesh, whatever the tolerances. A tooth landing tip on tip lifts it "
               "instead of jamming, and a slow turn of the motor after the index, reversing once, drops it into the gap. In the model that "
               "took the jams from about one index in five to none, in two hundred and sixteen indexes over a millimetre and a half of "
               "tolerance. The preload stays above the mesh's separating force at the motor's stall, so the teeth stay engaged while it "
               "doses. It isn't in version eleven's CAD; it is the first change proposed for the next version. Thanks for watching."),
         visuals=[dict(path="renders/v11/spring_pinion_v12.png", weight=1.5), dict(path="sim/out/entry_outcomes.png")]),
]
