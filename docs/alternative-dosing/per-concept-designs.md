# Per-concept preliminary designs (alternatives A–H)

This doc takes the eight alternative-dosing concepts brainstormed in
[`brainstorm.md`](brainstorm.md), refines each into a printable
preliminary CAD design, and treats each individually with the same
pipeline used in PR #2 (cam-ramp scoop), PR #5 (bimodal trough), and
PR #16 (vertical Archimedes auger):

```
SCAD  →  STL  →  admesh manifold check
                 →  iso PNG
                 →  half-cutaway PNG
                 →  transparent rotating GIF (36 frames)
                 →  PrusaSlicer slice (MK3S+ profile, PETG, 0.2 mm,
                                       3 perimeters, 30 % gyroid,
                                       4 mm brim, supports on)
```

Driver: [`scripts/render_alternatives.py`](../../scripts/render_alternatives.py) —
re-runnable; mirrors PR #16's `cad/auger/render_print.sh` and PR #5's
`scripts/render_trough_spin.py`.

Composite previews of all eight:

| Composite | Preview |
| --- | --- |
| **2-D dispensing animations** (per-concept loading + dispensing motion, side view) | [`cad/alternatives/composite-animation.gif`](../../cad/alternatives/composite-animation.gif) |
| **Annotated explainer panels** (title + iso + cutaway + numbered parts + 3-step operation cycle, per concept) | [`cad/alternatives/composite-panel.png`](../../cad/alternatives/composite-panel.png) |
| Rotating GIF (transparent) | [`cad/alternatives/composite-spin.gif`](../../cad/alternatives/composite-spin.gif) |
| Cross-section tile | [`cad/alternatives/composite-cutaway.png`](../../cad/alternatives/composite-cutaway.png) |

Per-concept annotated panels (each one composes the existing iso + cutaway
render with a numbered key-parts list and a 3-step operation cycle so the
mechanism is readable without opening the SCAD source):

| Concept | Panel |
| --- | --- |
| A. Tap-driven sieve cup (passive)            | [`A-tap-sieve-panel.png`](../../cad/alternatives/A-tap-sieve-panel.png) |
| B. Pez-style chamber strip                   | [`B-pez-strip-panel.png`](../../cad/alternatives/B-pez-strip-panel.png) |
| C. Capillary dip + fixed wiper               | [`C-capillary-wiper-panel.png`](../../cad/alternatives/C-capillary-wiper-panel.png) |
| D. Brush / swab pickup + comb knock-off      | [`D-brush-comb-panel.png`](../../cad/alternatives/D-brush-comb-panel.png) |
| E. Salt-shaker oscillation                   | [`E-shaker-panel.png`](../../cad/alternatives/E-shaker-panel.png) |
| F. Passive auger (rack-and-pinion)           | [`F-passive-auger-panel.png`](../../cad/alternatives/F-passive-auger-panel.png) |
| G. ERM-augmented sieve (top pick)            | [`G-erm-sieve-panel.png`](../../cad/alternatives/G-erm-sieve-panel.png) |
| H. Solenoid-tapped sieve (closed-loop)       | [`H-solenoid-sieve-panel.png`](../../cad/alternatives/H-solenoid-sieve-panel.png) |

Re-render the panels with
[`scripts/annotate_alternatives.py`](../../scripts/annotate_alternatives.py)
(pure Pillow; no OpenSCAD invocation; rebuilds in <1 s).

Per-concept render report: [`cad/alternatives/render-report.txt`](../../cad/alternatives/render-report.txt) (admesh `bad_edges = 0` for every part, slice succeeded for every part).

---

## A — Tap-driven sieve cup (passive)

**Mechanism.** Mounts on the 3018-Pro V2 spindle clamp via a Ø 43 mm
boss with two opposed wrench-flats. The cup floor has a Ø 16 mm mesh
window backed by an annular Ø 20 mm strike pad; the gantry pecks the
cup downward against the printed tap anvil
([`cad/tap_anvil.scad`](../../cad/tap_anvil.scad)) and each impulse
dislodges a near-constant micro-dose through the mesh.

**Files.** SCAD: [`A_tap_sieve.scad`](../../cad/alternatives/A_tap_sieve.scad).
Renders: `A-tap-sieve.{stl,iso.png,cutaway.png,spin.gif}`.

**Print notes.** PETG, 0.2 mm layer, brim. The strike-pad annulus is
a small Ø 20 mm bottom contact — a 4 mm brim is mandatory for first-
layer adhesion. No supports needed (everything bridges < 8 mm).

---

## B — Pez-style positive-displacement chamber strip

**Mechanism.** A linear cartridge with eight Ø 4.5 × 5 mm chambers
along an 8 mm pitch. Each chamber is volumetrically loaded once
(slot-fill from a hopper + strike-off across the top), then advanced
under the gantry by a fixed bed pawl that drops into the sawtooth
notches on the +y edge of the strip. A small Ø 2 mm exit port at the
bottom of each chamber drops the powder into the receiving vial when
the pawl strikes the cap.

**Files.** SCAD: [`B_pez_strip.scad`](../../cad/alternatives/B_pez_strip.scad).
Renders: `B-pez-strip.{stl,iso.png,cutaway.png,spin.gif}`.

**Print notes.** Print *flat*, exit-ports facing up, so the eight
chambers print as round holes (no support). Single-piece; no fasteners.

---

## C — Capillary dip + fixed wiper (mini-SWILE / PowderPicking)

**Mechanism.** A spindle-mounted vertical rod ends in a Ø 3.5 mm × 12 mm
capillary tip with a Ø 1.4 mm bore. The gantry dips the tip into a
powder bed (cohesive fines pack into the capillary), then drags the
tip across the slot in the bed-mounted wiper post; the wiper strikes
off any external excess and leaves only the capillary plug. The plug
is ejected at the target by tapping or by a thin printed plunger
inside the bore.

**Files.** SCAD: [`C_capillary_wiper.scad`](../../cad/alternatives/C_capillary_wiper.scad)
(rod + companion wiper post in one source).
Renders: `C-capillary-wiper.{stl,iso.png,cutaway.png,spin.gif}`.

**Print notes.** Print rod tip-up so the capillary bore prints
vertically (cleanest inner surface). Wiper post prints flange-down,
no support.

---

## D — Brush / swab pickup + fixed comb knock-off

**Mechanism.** Spindle-mounted Ø 28 mm disc carries a 24-bristle ring
at r = 11 mm. Cohesive powder adheres between the bristles; a fixed
bed-mounted comb (12 teeth, 1.2 mm gap) strips the adhered powder
into the receiving vial when the gantry sweeps the disc through it.

**Files.** SCAD: [`D_brush_comb.scad`](../../cad/alternatives/D_brush_comb.scad).
Renders: `D-brush-comb.{stl,iso.png,cutaway.png,spin.gif}`.

**Print notes.** Bristles are Ø 0.8 × 6 mm printed pins — at 0.2 mm
layer height they print reliably with **no** support; for a stiffer
brush, replace with cyanoacrylate-glued bottlebrush fibre. Comb
prints upright (teeth-up).

---

## E — Salt-shaker oscillation

**Mechanism.** Closed cup with a multi-hole patterned floor (1 centre
hole + concentric rings of 6 / 12 / 18 holes, all Ø 1.2 mm). The
gantry shakes the cup in X-Y at ~5–20 Hz over the target vial; flow
rate is set by hole count × shake amplitude. Fully passive — no
electronics, no sieve cloth, no swappable mesh consumable.

**Files.** SCAD: [`E_shaker.scad`](../../cad/alternatives/E_shaker.scad).
Renders: `E-shaker.{stl,iso.png,cutaway.png,spin.gif}`.

**Print notes.** Print floor-down so the hole pattern is the first
layer (sharp edges). 1.2 mm holes print cleanly on a 0.4 mm nozzle.
PETG; no support.

---

## F — Passive auger via rack-and-pinion

**Mechanism.** Vertical Ø 16 mm tube with an internal Archimedes
helix (Ø 11 mm helix at 12 mm pitch, 1.6 mm fin thickness), keyed to
a 14-tooth Ø 18 mm pinion at the top. A *fixed* printed rack on the
bed engages the pinion when the gantry rapids the assembly
horizontally — linear gantry motion drives auger rotation passively,
so the spindle does not have to rotate. Bottom Ø 2.5 mm exit port.

Heavily inspired by PR #16's vertical Archimedes auger (same helix
parameters and flat-bottom-on-bed printing strategy).

**Files.** SCAD: [`F_passive_auger.scad`](../../cad/alternatives/F_passive_auger.scad).
Renders: `F-passive-auger.{stl,iso.png,cutaway.png,spin.gif}`.

**Print notes.** Print **vertically**, exit-port-down on the bed,
3+ perimeters, 4 mm brim, supports **on** (the top cap bridges the
pinion-to-tube annulus). Same orientation strategy as PR #16.

---

## G — ERM-augmented sieve cup (concept-A cup + 10 mm coin ERM)

**Mechanism.** Same cup body as concept A, plus a Ø 10.4 × 3.6 mm
pocket on the +x face for a 10 mm coin ERM motor and a 21 × 14 ×
5.5 mm pocket on the −x face for a CR2032 holder. A continuously-on
ERM gives bounded vibration that matches the published vibratory-
sieve-chute regime (Besenhard 2015 — mg-scale fills with a definable
amplitude window) far better than discrete tap impulses. The
vibration is gated by a small SPST switch wired in series with the
CR2032; no microcontroller required.

**Files.** SCAD: [`G_erm_sieve.scad`](../../cad/alternatives/G_erm_sieve.scad)
(self-contained, distinct from `cad/sieve_cup.scad` so the
alternatives pipeline doesn't have to special-case OpenSCAD's
`include` variable scoping).
Renders: `G-erm-sieve.{stl,iso.png,cutaway.png,spin.gif}`.

**Print notes.** Identical to concept A. ERM and CR2032 holder are
press-fit after printing; wire-relief notch is integrated into the
boss.

---

## H — Solenoid-tapped sieve, closed-loop

**Mechanism.** Concept A's cup body, but tapped horizontally by a
5 V push-pull solenoid (Ø 10 × 22 mm) clamped in a printed L-bracket
alongside the cup. An off-board microcontroller (e.g. Pi Pico) fires
the solenoid against an external 0.1 mg balance reading until the
target mass is reached — closed-loop gravimetric dosing, the
accuracy-maximising but most electronics-heavy of the eight.

**Files.** SCAD: [`H_solenoid_sieve.scad`](../../cad/alternatives/H_solenoid_sieve.scad)
(L-bracket; cup body imported from `A_tap_sieve.scad`).
Renders: `H-solenoid-sieve.{stl,iso.png,cutaway.png,spin.gif}`.

**Print notes.** L-bracket prints foot-down (no support); solenoid
clearance bore is horizontal so prints as a clean cylindrical bore
along Z.

---

## How to re-render

```bash
sudo apt-get install -y openscad admesh prusa-slicer xvfb
pip install pillow
python scripts/render_alternatives.py
```

Outputs are written next to the SCAD source under
[`cad/alternatives/`](../../cad/alternatives/), plus the two
composite previews and the [`render-report.txt`](../../cad/alternatives/render-report.txt)
log. Per-concept g-code is written to `${TMPDIR}/alt-slices/` so the
repository doesn't carry tens of MB of slice artifacts.
