# Edison Analysis v3 — Longitudinal-tilt / pin-in-slot CAD review

**Task ID:** `7f85494a-ce97-4ebf-bea9-6ac2359014dd`  
**Submitted:** 2026-04-24  
**Files uploaded:** `assembly.png`, `assembly-end.png`, `assembly-side.png`, `README.md`,
`manuscript.tex`, `cad/README.md`, `repo-snapshot.zip` (cad/, docs/figures, docs/manuscript,
docs/edison)

---

Based on a quantitative analysis of the CadQuery model (`cad/excavator.py`) and your provided design documents, here is high-effort feedback across your five focus areas. I'm pushing back hard on the baseline geometry because the math shows it won't work as currently parameterized.

### 1. Mechanism viability under the gantry-only constraint

**The current cam-ramp baseline is critically flawed in two ways: it is statically unstable (an inverted pendulum) and kinematically uncontrollable (a snap-through singularity).**

*   **Fatal Flaw A: The Inverted Pendulum.** The README claims "gravity returns the trough... (a stable pendulum)". This is false for the current CAD parameters. The pivot pin is at `Y = -6.5 mm` (halfway down the trough). A full load of powder has a centroid at `Y = -5.52 mm` (higher up). Even worse, the two massive chamfered lips (`6×6×80 mm`) add 7.3 g of PETG *above* the rim. My calculation shows the combined loaded center of gravity is at `Y = -4.35 mm`, which is **2.15 mm ABOVE the pivot**. The trough is an inverted pendulum and will spontaneously flip open-side-down the moment the gantry moves.
*   **Fatal Flaw B: The Cam Singularity.** The cam ramp relies on a 16 mm lever arm (from pivot to the lip's outer edge) pushing against a 26.6° ramp. As the gantry pushes forward, the lip traces a circular arc. My kinematics model shows that at ~40° of tilt, the lever arm is nearly vertical. The sensitivity skyrockets to **86 degrees of tilt per mm of gantry travel**. This is a "snap-through" singularity; it is impossible to command a controlled metered pour with this geometry. Furthermore, the maximum vertical rise the lip can physically achieve is only ~9.5 mm, so the 20 mm `cam_ramp_rise` is wasted material.

**The Fix: The pin-in-slot variant (Panel E) is vastly superior and should be the baseline.**
The routed slot directly constrains the stem angle at every X coordinate. It eliminates the friction ambiguity, prevents the inverted pendulum from flipping during transport, and allows for a linear, programmable tilt schedule without the 86 deg/mm singularity. A compliant/spring-loaded lid is unnecessary complexity if the slot handles the kinematics.

### 2. Powder-handling realism

The longitudinal pivot / sideways tilt is a massive improvement over the end-over-end gondola (Edison v2 §3), as pouring over an 80 mm edge guarantees the powder won't bridge (arch spans for these powders are typically <10 mm).

*   **Retention:** For dozens-of-microns cohesive powders (TiO2, CaCO3), the FDM layer lines will act as anchor points. Vapour smoothing is mandatory to prevent a 10–20% hold-up mass. The "knock-to-debridge" oscillation (Edison v1 §6) is an excellent software-only feature, but it's much easier to execute with the pin-slot design (by coding a high-frequency zigzag into the slot path) than by trying to repeatedly ram a free-hanging bumper against a cam.
*   **Charging:** The brass pivot pin is already a perfect ground path. Lining the interior with copper tape (as you suggested) is the cheapest way to mitigate triboelectric charging on fine inorganics.
*   **Measurements:** You must measure dose CV (target ~10% to match Alsenz) and carryover mass (mg remaining after a knock cycle).

### 3. CAD geometry critique

Looking at `assembly-end.png` and `assembly-side.png`:

*   **Arm placement:** The arms drop from the gantry and end in a J-hook gripping the bosses. Because the pivot must be moved *up* toward the rim to fix the inverted pendulum, the arms will need to clear the trough's side walls as it rotates.
*   **Boss geometry:** The pivot bosses (`8 mm` diameter) sit on the end caps. The `arm_width` is also 8 mm. This is structurally fine, but the `pin_clearance` of `0.2 mm` diametral is too tight for FDM. It will fuse or bind. It needs to be 0.3–0.4 mm for a reliable sliding fit.
*   **Lip geometry:** The continuous `6×6 mm` chamfered lips run the full 80 mm length. As calculated above, they add 7.3 g of mass high above the pivot, ruining the pendulum stability. They are unnecessarily massive; a 2×2 mm lip would still provide a clean pour detachment point without destroying the mass distribution.

### 4. Closed-loop architecture and `dfm.py` shortfalls

The parametric pipeline (`cad/build.py` -> `dfm.py`) is a great start, but `dfm.py` is entirely missing the physics checks that would have caught the flaws above.

It currently checks 24 items (min wall, overhangs, basic slot/cam bounding boxes). **It falls short by only checking static geometry, not dynamic kinematics or statics.**

To fix the loop, `dfm.py` needs these automated checks added:
1.  **Pendulum stability:** `CG_loaded_y` must be < `pivot_y` (with a safety margin).
2.  **Cam sensitivity ceiling:** Calculate `d(theta)/d(X)` over the 0–45° range and fail if it exceeds ~15 deg/mm.
3.  **Cam rise utilization:** Check if `cam_ramp_rise` > `max_achievable_rise`.
4.  **Pin-slot friction:** Estimate the normal force on the peg based on the maximum curvature of the slot path.

### 5. Three concrete next experiments

Ranked by information value to derisk the design:

1.  **The "Pendulum Flip" and Pin-Slot Engagement Test.** Print the trough (with adjusted 2×2 mm lips), the arms, and a laser-cut or 3D-printed slot board (Panel E). Load it with 20 g of powder. Confirm that the slot prevents the inverted-pendulum flip during rapid X-transport, and verify that pure X-motion successfully walks the peg through the slot to achieve a 60°+ tilt without binding.
2.  **The Strike-Off vs. J-Curve Plunge Bake-off.** Print the bed-edge strike-off bar. Using a cohesive powder (e.g., TiO2 or flour), script the J-curve plunge. Scoop 30 times with the strike-off bar and 30 times without. Weigh each dose on a standard laboratory balance. If the strike-off doesn't cut the CV down to the ~10% range, the volumetric concept is dead for cohesive powders.
3.  **Carryover / Holdup Mass Test.** After the 30-scoop run, measure the mass of powder permanently retained in the trough. Test the software "knock" (oscillating the gantry rapidly in X while the peg is in a detent in the slot) to see if it meaningfully reduces the holdup mass compared to a single smooth pour.

---

**Discretionary Analytical Decisions:**
*   Computed trough mass properties assuming PETG with a density of 1.27 g/cm³ and a typical inorganic powder bulk density of 1.0 g/cm³.
*   Modelled the loaded center of gravity (CG) by treating the powder volume as a uniform solid half-disk (CG at 4r/3π from the flat edge) and the shell as a thin-walled half-cylinder.
*   Analysed the cam kinematics using small-angle geometric approximations of the lever arm's arc, defining the sensitivity singularity mathematically as the point where the tangent to the arc becomes vertical.
*   Selected 0.3–0.4 mm as the target FDM pin clearance based on standard desktop 3D printing tolerances rather than precision machining tolerances.
*   Assumed the pin-slot stem would be long enough to decouple minor Z-axis arc errors, modelling the mechanism as a rigid kinematic constraint.
