## VLM Judge Review: single-channel-module v2

Below is an image-by-image critique of the attached files against the PR #35 review criteria. 

### 1. `single_channel_module_iso.png`
**(a) Describe view:** An isometric line drawing of the full v2 assembly. Shows the spine plate standing vertically on a flat cradle base with two large, floating side-plates (cradle cheeks) straddling its middle. At the bottom, a bearing collar holds a protruding vertical rod (auger rotor envelope). At the top, a stepper motor mounts on a bracket to the side, and a cartridge sits suspended in mid-air above the rotor.

**(b) Visible mechanical issues:**
*   **Cartridge floats:** The hopper/cartridge is suspended ~50 mm above the rotor top. It does not touch the rotor.
*   **Stepper floats:** The motor faceplate is drawn horizontally instead of vertically, and the stepper body itself floats ~25 mm above this faceplate. 
*   **Belt drive floats / won't reach:** The stepper's downward-pointing shaft tip ends at Z=303.5 mm, but the motor pulley and rotor pulley are at Z=230 mm. The belt is floating in mid-air between two shafts that don't reach it, and the two shafts (one pointing up, one pointing down from higher up) are not coplanar.
*   **Cradle cheeks overlap and float:** The cradle cheeks stick out ~110 mm in both +X and -X directions (forming large "wings") without connecting to anything outboard. Furthermore, their "feet" sit at Z=0..16 mm while the cradle base top is at Z=-2 mm; there is a 2 mm vertical air gap between them.
*   **Plunger is a puck:** The solenoid plunger is modeled as a Ã4 mm coin extruded along Z, rather than a rod extruded along the Y axis toward the rotor.

**(c) PR criteria flags:**
*   **S4 (Things not coupled / exploded view):** Cartridge gap, bracket gap, belt/shaft gap, cheek gap.
*   **S1 (Mechanically nonsensical):** Motor bracket faceplate is horizontal, not vertical; plunger modeled wrong axis.
*   **S3 (Unnecessary outboard plates):** Cradle cheeks extending 110 mm into empty space.
*   **B1 (Cartridge/throat under-specified):** The ~50 mm air gap means the hopper does not interface with the rotor at all.

**(d) Code-level fixes (`cad_model.py`):**
*   **Cartridge gap:** In `make_cartridge()`, change `auger_top_z = COLLAR_H + 10.0 + AUGER_LEN` to `auger_top_z = rotor_z0 + AUGER_LEN` (i.e. Z=-30+250=220) so the cartridge base seats directly on the rotor top cap.
*   **Motor bracket & belt:** In `make_motor_bracket()`, fix the face extrusion plane so it is vertical (e.g. `cq.Workplane("YZ").workplane(offset=motor_face_x)...`) and align its Z-center with the pulleys (Z=230) so the stepper shaft sits cleanly inside the motor pulley.
*   **Cradle cheeks & gap:** In `make_cradle_cheek()`, change `rect(CHEEK_H, CHEEK_W)` to use correct X/Y/Z assignments (should extrude along X, profile in YZ) and shift the `cradle_base` translation from `Z=-10` to `Z=0` (or drop the cheek feet to `Z=-10`) so they actually touch.
*   **Solenoid plunger:** In `make_solenoid()`, change the plunger workplane to `"XZ"` and extrude along `Y` so it correctly points at the rotor wall.

### 2. `single_channel_module_front.png`
**(a) Describe view:** An orthographic line render facing the spine (-X face of spine towards viewer, although standard front is -Y). Shows the spine plate edge-on, the cradle cheeks extending left and right, the bearing collar at the bottom, and the stepper bracket at the top.

**(b) Visible mechanical issues:**
*   **Bracket plates don't touch:** The motor bracket's foot attached to the spine ends at Z=287.5 mm, while the horizontal faceplate starts at Z=295 mm. There is a 7.5 mm physical gap between the two halves of the bracket.
*   **Stepper pointing wrong way:** The motor shaft points straight down alongside the spine rather than down its +Z axis parallel to the rotor. 

**(c) PR criteria flags:**
*   **S1 (Mechanically nonsensical):** Motor bracket has two plates that do not touch.
*   **S4 (Exploded view):** Bracket halves floating in air.

**(d) Code-level fixes (`cad_model.py`):**
*   **Bracket gap:** In `make_motor_bracket()`, rewrite the bracket geometry as a single solid sweep or a contiguous union (e.g., an L-shape drawn in the XZ plane and extruded along Y) rather than two independent sketches whose Z-coordinates have drifted apart.

### 3. `single_channel_module_side.png`
**(a) Describe view:** An orthographic render looking along the X-axis (side view). The spine is clearly visible with the bearing collar on the bottom right and the cradle arc-slot mechanism behind.

**(b) Visible mechanical issues:**
*   **ERM Pad in flow path:** The ERM coin vibration motor pad is centered on the rotor axis at `Z=-3..0`. Because the rotor is a hollow tube dispensing powder directly downward, placing the ERM on the rotor's vertical centerline obstructs the powder flow path as it exits the nozzle.
*   **Arc-slots off-axis:** The 6 detent holes in the cradle cheek appear offset from the M5 trunnion pivot center. 

**(c) PR criteria flags:**
*   **S2 (Parts obstruct flow):** ERM pad sits directly underneath the rotor exit nozzle.
*   **S1 (Mechanically nonsensical):** Arc slot detents don't match the pivot radius center.

**(d) Code-level fixes (`cad_model.py`):**
*   **ERM pad flow block:** In `make_bearing_collar()`, shift the ERM pad center off the rotor axis (e.g., `.center(rotor_x + 15, 0)`) so the coin sits on the collar's solid overhang, leaving the rotor exit clear. Update `make_erm()` to match.
*   **Arc-slot centering:** In `make_cradle_cheek()`, remove the `.workplane(centerOption="CenterOfBoundBox")` call right before `.pushPoints(pts)`. That call resets the local origin to the centroid of the face, breaking the world-coordinate trig calculations used to generate the arc `pts`.

### 4. `single_channel_module_top.png`
**(a) Describe view:** Top-down orthographic view showing the cradle base footprint, the spine thickness, the floating cartridge circle, and the horizontal stepper faceplate offset to the side.

**(b) Visible mechanical issues:**
*   Confirms the cartridge float/offset and the excessive X-width of the cradle cheeks. No new topological bugs, but highlights how thin the `CHEEK_T` (6 mm) is given its massive 220 mm X-dimension spanâit acts as a giant unbraced lever arm.

**(c) PR criteria flags:** S3 (wasteful plates), S1.

**(d) Code-level fixes:** Addressed in the Iso section (fix cheek dimensions).

### 5. `single_channel_module_sketch.png`
**(a) Describe view:** A 3-panel matplotlib dimensioned schematic with a side view, front view, and sectioned flow path.

**(b) Visible mechanical issues:**
*   This matches the README dimensions but papers over the CAD bugs (the schematic connects the motor bracket lines and correctly aligns the cartridge and rotor, whereas the code does not). 
*   However, the **ERM coin location** error is visible in the side panel: it shows the orange ERM box overlapping the rotor shaft footprint below the collar.

**(c) PR criteria flags:** S2 (flow obstructed).

**(d) Code-level fixes (`sketch_2d.py`):**
*   Update `AX_ROTOR - ERM_D/2` math to shift the coin outward, mirroring the CAD fix for the flow obstruction. 

### 6. `single_channel_module_powder_flow.png`
**(a) Describe view:** A standalone matplotlib cross-section showing powder flowing from a hopper down into a cup via a continuous numbered arrow.

**(b) Visible mechanical issues:**
*   The requested single continuous flow arrow with numbered nodes (1 through 5) is successfully implemented.
*   The 10 mm scale bar is successfully implemented. 
*   However, the cartridge gap (noted in the CAD) is visually "solved" here by a smooth line, but node 2 ("top loading slots") is drawn floating above the actual helix. 

**(c) PR criteria flags:** Solves S5 (numbered nodes continuous arrow) and S6/S8 (scale bar + generic cup).

**(d) Code-level fixes:** No python fix needed for the matplotlib rendering format, just ensure the CAD catches up to this intent.

### 7. `single_channel_module_tilt_sweep.png`
**(a) Describe view:** A 4-panel matplotlib schematic showing simplified module outlines pivoted around the trunnion at 0, 45, 75, and 90 degrees above a generic cup.

**(b) Visible mechanical issues:**
*   Successfully shows the module at the correct angles with 90Â° dashed as requested.
*   The 30 mm rotor protrusion correctly clears the cradle base up to 75Â°, proving the `ROTOR_BOTTOM_Z = -30` math works for the frame.

**(c) PR criteria flags:** Solves S6 (tilt sweep 0/45/90 + cup).

**(d) Code-level fixes:** None required.

---

### Top 5 must-fix items for v3

1. **Close the ~50 mm Cartridge/Rotor Air Gap:** The defining feature of the "Idea B" iteration was letting powder enter the top of the rotor. With the cartridge floating in CAD, you cannot 3D print or test this. (Fix `auger_top_z` in `cad_model.py`).
2. **Re-align the Stepper Motor Bracket and Faceplate:** The two halves of the motor bracket have a 7.5 mm gap, and the faceplate is horizontal instead of vertical. The stepper currently floats and its shaft points down at the wrong Z-height. Rewrite the bracket as a single continuous extrusion and match the stepper Z-height to the pulley Z-height.
3. **Move the ERM Coin out of the Flow Path:** The coin is centered directly under the rotor exit. Shift its X-coordinate outward by ~15 mm so powder dropping out of the auger doesn't pile up on top of the vibration motor.
4. **Fix the Solenoid Plunger Axis:** The plunger is drawn as a tiny puck extruded along Z. It must extrude along Y to bridge the gap between the solenoid body and the rotor wall through the collar window.
5. **Shrink the Cradle Cheeks & Fix Detent Origin:** The cheeks are incorrectly mapped (220 mm along X instead of Y), wasting massive amounts of filament on unsupported wings. Their arc-slot detent holes are also off-axis because `CenterOfBoundBox` overwrites the pivot origin. 

### False positives / things that look wrong but are actually fine

*   **Thin Cartridge Walls (2 mm):** This looks extremely thin next to the 8 mm spine, but 2 mm taper walls on a hopper are fully FDM-printable and save time.
*   **The Solenoid Window Through the Collar:** Having a hole cut straight through the collar body looks structurally sketchy, but because the solenoid wing is now gusseted back to the collar OD (a v2 addition), the remaining 22.5 mm walls are sufficiently strong in PETG. 
*   **Cartridge "Slip Fit" (No fasteners):** Relying on gravity to hold the cartridge on the rotor top cap seems loose, but for an un-pressurized benchtop powder hopper, this is standard design practice (it facilitates quick-swapping).

### Open questions for the human reviewer:
*   **Belt Tensioning:** The README notes tensioning relies on sliding the motor bracket via "slotted foot holes", but the code only generates 4 circular Ã3.4 clearance holes (`hole(3.4)`), not slots. Do you want actual slotted holes modeled in `cad_model.py` for v3, or is the intention to just drill them out manually post-print?
*   **Upper Rotor Bearing:** The README highlights the risk of rotor wobble given the single cantilevered 6805ZZ bearing. Since fixing the stepper bracket will consume space at the top of the spine anyway, should we pre-emptively model an upper 608ZZ bearing block before the v2.1 print?
*   **NEMA 11 Downward Orientation:** Even if the bracket faceplate is fixed to be vertical, is having the stepper mounted "upside down" (shaft pointing down at the pulley) the intended envelope constraint to keep the center-of-gravity low, or should it point up?