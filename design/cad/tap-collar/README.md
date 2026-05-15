# Tap Collar (independent split-collar with vibration motor + solenoid mounts)

Parametric CAD for the tap collar requested in the issue
*Tap Collar Design*: a collar that sits rigidly around the auger and carries
an integrated **coin vibration motor** and **push/pull solenoid** to vibrate
and tap the auger so powder flows more reliably.

The piece is split into two independently-printed parts so the collar can
spin freely on the auger (which lets the motor and solenoid wiring stay
put) while a hardstop on the chassis-mounted plate keeps it from being
dragged all the way around with the auger and winding up the cabling.

![Assembly — front view](renders/assembly_front.png)

## How it works

```
                ┌──────────────┐               ← solenoid (mounts on +Z boss,
                │   solenoid   │                  plunger drops through the
                │ ─── plunger ─┘                  Ø6 hole in the collar wall
                ▼   ↓  Ø6 plunger clearance       to tap the auger directly)
              ╱  ╲  ╱  ╲
             │ M2 ⊙ ⊙ M2 │      ← solenoid top boss (Ø2.4 M2 mount holes)
              ─────┬─────
        ┌──┐  ╱        ╲   ┌──┐
        │  │ │  auger   │  │  │ ← M3 clamp screw (also the visual hardstop
   coin │  │ │   bore   │  ├──┤    "contact point": the two clamp ears
  motor │  │ │  Ø 25.5  │  │  │    swing into the +X column on the
        │  │  ╲        ╱   └──┘    mounting plate to arrest rotation)
        └──┘   ────────       ▲
        ↑                     │
       coin-motor pad         column on mount plate (+X)
       (Ø10 × 1 mm recess
        on -X tangent face)
        ─────────────────────────────
        │ ⊙ M3                  M3 ⊙ │  ← rectangular mounting plate
        └─────────────────────────────┘     (4 corner M3 mounting holes,
                                             same footprint as PR #47 bracket)
```

* The **mounting plate** (`mount_plate`) is the same rectangular flange and
  4-corner M3 mounting-hole pattern as the auger bracket from
  [PR #47](https://github.com/vertical-cloud-lab/powder-doser/pull/47),
  *with the circular collar replaced by a tall raised column on the +X
  end of the plate*.  The column extends up past the bore axis and reaches
  the elevation of the tap collar's clamp tabs so it can stop them from
  swinging through.  Its X position was chosen to leave ~6 mm of clear
  access to the +X corner mounting screws.
* The **tap collar** (`tap_collar`) reuses the bracket's bore (Ø 25.5 for
  the Ø 25 mm Archimedes auger of [PR #16](https://github.com/vertical-cloud-lab/powder-doser/pull/16)),
  collar OD (Ø 33.5), 2 mm clamp slot, and clamp-ear / clamp-screw
  geometry — but with the slot rotated 90° so it opens to the +X side.
  The two clamp ears double as the hardstop "**contact point**" called
  out on the drawing: as the auger drags the collar around, one clamp
  ear hits the mount-plate column (the other ear hits it on the return
  swing).  Each ear is 8 mm wide along X (vs. 3 mm on the bracket) so it
  reaches the column without needing a separate "stop arm" feature.
* The collar's clamp screw is intended to set the running fit of the
  collar on the auger (snug enough that the collar stays put axially;
  loose enough that the auger can rotate freely inside it), not to lock
  it onto the shaft.
* The **coin vibration motor** (Ø 10 × 3 mm adhesive coin-style motor, e.g.
  any "10 mm flat coin vibration motor") sits in a Ø 10.5 × 1 mm recess
  on a flat tangent pad on the **-X side** of the collar.  Adhere it
  with the motor's own foam-tape backing.
* The **push/pull solenoid** (small ~17 × 11 × 30 mm class with M2 screw
  mounts, e.g. JF-0530B / SDM-0530) sits on a flat boss on the **+Z**
  (top) side of the collar.  Two M2 clearance holes at 12 mm pitch along
  the auger axis hold the solenoid down; a Ø 6 plunger clearance hole
  drops straight through the collar wall so the plunger can hammer the
  auger directly from above.

The drawing called the motor / solenoid arrangement explicitly
"unspecified" — both are mounted around the OD as suggested in the
sketch, but rotating the boss and pad to taste is just a matter of
changing the angle in `cad_model.py`.

## Files

| File | What it is |
| --- | --- |
| [`cad_model.py`](cad_model.py) | Parametric CadQuery model.  Builds both parts.  Run it to (re)generate the STEPs and STLs. |
| [`mount_plate.step`](mount_plate.step) | STEP export of the mounting plate. |
| [`tap_collar.step`](tap_collar.step) | STEP export of the collar. |
| [`stl/mount_plate.stl`](stl/mount_plate.stl) | **Ready-to-print STL** of the mounting plate. |
| [`stl/tap_collar.stl`](stl/tap_collar.stl) | **Ready-to-print STL** of the collar. |
| [`render_views.py`](render_views.py) | Headless VTK render of iso/front/top/side views (per part + assembled pair). |
| [`renders/`](renders/) | PNG renders committed for the PR / README. |

## Key parameters (mm)

All parameters live at the top of [`cad_model.py`](cad_model.py).  The
shared geometry block is kept in lock-step with the bracket from PR #47.

| Parameter | Value | Notes |
| --- | --- | --- |
| `AUGER_OD` | 25.0 | Matches the Archimedes auger OD from [PR #16](https://github.com/vertical-cloud-lab/powder-doser/pull/16). |
| `BORE_CLEARANCE` | 0.5 | Diametral clearance — same free-running fit as the bracket. |
| `COLLAR_WALL` | 4.0 | Collar OD = 33.5 mm. |
| `PLATE_LENGTH × DEPTH × THICKNESS` | 60 × 12 × 14 | Identical to [PR #47](https://github.com/vertical-cloud-lab/powder-doser/pull/47); preserves the corner-hole pattern and the 29.25 mm bore-axis lift that clears the [PR #49](https://github.com/vertical-cloud-lab/powder-doser/pull/49) gear OD. |
| `MOUNT_HOLE_INSET_X` / `MOUNT_HOLE_D` | 6.0 / 3.4 | M3 corner mounting holes — same as the bracket. |
| `COLUMN_INNER_X / OUTER_X` | 10.0 / 16.0 | Hardstop column on +X.  The inboard face leaves a 1 mm rotational clearance to the resting clamp-tab outboard face; the outboard face leaves ~6 mm of access to the +X corner mount-screw heads. |
| `COLUMN_HEIGHT` | 39 | Reaches `COLLAR_TOP_Z + TC_TAB_H + 1` so the column overlaps the full clamp-tab Z range. |
| `CLAMP_GAP` / `CLAMP_SCREW_D` | 2.0 / 3.4 | Drawing callout slot width + M3 clearance through both ears. |
| `TC_TAB_W × H` | 8 × 7 | Clamp ears, widened along X (was 3 mm on the bracket) so they reach the +X column without needing a separate stop arm. |
| `TAB_COLLAR_OVERLAP` | 6.0 | How far the tab block sinks into the collar OD so the union forms a continuous solid. |
| `COIN_MOTOR_D` / `COIN_MOTOR_RECESS_DEPTH` | 10.0 / 1.0 | Adhesive Ø10 coin vibration motor; 1 mm shallow recess locates the motor on the side pad. |
| `SOLENOID_BOSS_W × DEPTH × PROUD` | 14 × 17 × 2 | Top boss for the solenoid; the 17 mm Y-extent (wider than `PLATE_DEPTH = 12`) leaves clear material between the central Ø6 plunger hole and the M2 mount holes. |
| `SOLENOID_SCREW_D / PITCH_Y` | 2.4 / 12.0 | M2 clearance, 12 mm pitch along the auger axis. |
| `SOLENOID_PLUNGER_D` | 6.0 | Plunger clearance hole through the full collar wall. |
| `FILLET_PLATE_COLUMN` / `FILLET_TAB_COLLAR` | 2.0 / 1.0 | Stress-relief / cosmetic blends. |

Defensive `assert`s catch parameter retunes that would push the
solenoid M2 mount holes through the central plunger hole, off the
boss footprint, or push the hardstop column through the corner mount
holes.

## Print orientation

Both parts print with the **plate / boss face down on the bed**, the same
as the bracket — bore axis ends up parallel to the bed and no internal
supports are needed inside the collar bore.

## Regenerating outputs

```sh
cd design/cad/tap-collar
python cad_model.py                  # writes *.step + stl/*.stl
xvfb-run -a python render_views.py   # iso/front/top/side PNGs in renders/
```
