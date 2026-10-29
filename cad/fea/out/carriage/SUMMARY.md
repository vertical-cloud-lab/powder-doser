# Carriages and module joints, chain carousel v3 and v4 (CalculiX)

Source: `cases/carriage.py` (`python cases/carriage.py` runs every case; `hand` writes `hand_checks.json`; `table` prints the
raw table below). Geometry: v3 and v4 exported from #185 at `45e9740` (merged here as `b882c33`) by `export_design.py`.
Quadratic tets (C3D10), about 2.2 mm (2+ elements through the 4-5 mm walls; 0.9 mm at the lugs, 1 mm at the A-1 tabs),
up to 131k nodes; the latch bolt 0.8 mm, the side tab 1.2 mm.

## Results that matter

| part | design | load case | peak von Mises (MPa) | allowable (MPa) | SF | what moves |
|---|---|---|---|---|---|---|
| carriage | v3 | gravity, bottom run, creep E (module parked for days) | 0.68 | 8 (creep) | 11.8 | mid-span sag 0.39 mm, cap end of the auger 0.84 mm lower |
| carriage | v3 | gravity, top run (upside down, held by the latch), creep E, x1.27 loop peak | 1.70 | 8 (creep) | 4.7 | latch housing 0.84 mm, cap end 1.9 mm (plus the bolt's 0.4 mm slot play: 1 mm more at the cap) |
| carriage | v3 | gravity, vertical runs, creep E | 2.80 (lug's front end, the lug-rib notch, under the knuckle's 2.2 N thrust) | 8 (creep) | 2.9 | under 0.2 mm |
| carriage | v4 (latch housing bridged, see finding 1) | gravity, bottom run (module hanging on hinge + latch), creep E, x1.27 | 2.09 | 8 (creep) | 3.8 | latch 1.35 mm, cap end 3.1 mm lower (1.7 mm short-term) |
| carriage | v4 | gravity, vertical runs, creep E | 2.17 (opening's front corners) | 8 (creep) | 3.7 | under 0.1 mm |
| carriage | v3 | station: P16 stall, 50 N through the hinge, tongues in the hold-down lips | 16.1 in the lug-rib notch (x_c 41.5) | 23 across layers (34 along) | 1.4 (2.1 along the layers, the stress's direction) | lugs rise 0.94 mm after the 2 mm lip gap |
| carriage | v4 | the same | 10.7 at the front tongue's root corner | 23 | 2.2 | lugs rise 0.67-0.78 mm |
| carriage | v3 | loading position: 40 N auger pull at the latch, latch closed, tongues in the side tabs | 22.3 at the front tongue's root corner (outer face) | 23 (34 along) | 1.0 (1.5) | latch 5.6 mm, mid-span 4.5 mm, cap end 11.8 mm |
| carriage | v3 | the same, 40 N pulled at mid-plate (Sam x 50) | 19.5 | 23 | 1.2 | latch 3.5 mm |
| carriage | v4 (bridged) | 40 N auger pull at the latch | 29.8 at the bridge's corner on the -u strip | 23 (34) | 0.77 (0.88) | latch 9.8 mm, cap end 21.8 mm |
| carriage | v4 (bridged) | 40 N pulled at mid-plate | 17.9 | 23 | 1.3 | latch 5.5 mm |
| latch bolt (printed flat) | v3 | 40 N on its lap (the pull above) | 10.4 (hand 11.3) | 34 (along the layers) | 3.3 | tip 0.10 mm |
| latch bolt | v3 | module upside down x1.27 (2.9 N) | 0.79 | 34 | 43 | 0.007 mm |
| side tab lip | v3 | 25 N from the tongue (the front tab's share of a 40 N pull is 22 N) | 12.4 one mm off the root; 65 at the sharp root corner itself (singular) | 23 | 1.9 (none at the corner) | lip tip 0.34 mm |
| side tab foot | v4 | 25 N | 14.0; 87 at the sharp corner | 23 | 1.6 | foot tip 0.41 mm |
| hinge pins (5 mm 18-8) | both | 25 N per lug (P16 stall) | shear 1.3, bending 8.4 | 205 | 24 | hand |
| hinge lugs (bore bearing, tear-out) | both | 25 N per lug | bearing 2.3, tear-out 0.9 | 23 | 10 | hand: only 2.2 mm of each 4 mm lug is bore, the rest is the head's counterbore |
| v4 latch pin (4 mm steel) | v4 | 40 N pull | bending 15.5; keeper bearing 2.4 | 205 / 23 | 13 / 9 | hand |
| v3 keeper | v3 | 40 N pull | bearing 1.7, root shear 0.8 | 23 | 14 | hand |
| A-1 joint, M3 head on the printed seat | both | a snug 300 N clamp | 18 under the button head (16.4 mm^2) | 8 (creep) | 0.44 | hand: the clamp relaxes |

Hand checks of the FEA: the latch bolt's 10.4 MPa against a cantilever's 6Fa/(bh^2) = 11.3 MPa (-8 %); the side tab's
12.4 MPa (1 mm off the root) against 11.8 MPa (+5 %); the v3 carriage's 0.39 mm creep sag on the bottom run sits between
a beam pinned at both A-1 tabs (0.69 mm) and one clamped at both (0.16 mm), with I about 2000 mm^4 (plate + edge ribs,
holes averaged) and the tabs modelled as semi-rigid; the v3 40 N pull's 5.6 mm sits between the same beam pinned (8.6 mm)
and clamped (2.1 mm) at the tongues' side-tab contacts, 337 mm apart.

## Findings

1. **v4's latch housing is not attached to the carriage.** `parts4.latch_housing_v4` is unioned in `carriage_v4`, but it sits
   wholly inside the 51.6 mm opening (|u| 12.5-25.5 against the opening's 25.8) and touches nothing: the exported
   `carriage.step` has two solids, and the latch, the only thing that holds the module both ways, has nothing to hold it.
   The runs here bridge the housing's -u wall out over the -u side strip to the carriage's edge (u -33..-25, the housing's
   length). Even then the module's weight hangs on one 7.2 mm strip: the cap end ends up 1.7 mm (short-term) to 3.1 mm
   (creep, loop peak) lower than drawn, and a 40 N pull on the auger bends that strip 9.8 mm at the latch and peaks at
   30 MPa (SF 0.77). v4 needs its latch on a stiff member: a latch on each strip (two pins, one each side of the tube), or a
   deeper strip or rib under the housing, and a re-check.
2. **v3's hinge lugs sit in a 1 mm notch at each end** (inherited from v2's carriage): the edge rib is cut 18 mm for the
   lug (x_c 24-42) and the lug is 16 mm long (25-41), so at x_c 24-25 and 41-42 only the 6.5 x 5 mm strip beside the
   window carries the carriage's bending. A 50 N P16 stall at the station peaks there at 16 MPa (SF 1.4 against the
   across-layer 23 MPa, 2.1 against the along-layer 34 MPa); the module's thrust on a lug on the vertical runs peaks there
   too (SF 2.9 against the creep allowable). Make the rib cut 16 mm (or the lug 18 mm) so the lug merges into its rib.
3. **Pulling an auger off at the loading position goes through the closed latch into the middle of the carriage.** The side
   tabs catch only the tongues, 337 mm apart; the latch is 150 mm from the front one. 40 N bends a v3 carriage 5.6 mm at the
   latch (11.8 mm at the cap end) and stresses the front tongue's root to 22 MPa (SF 1.0 across layers, 1.5 along them);
   the latch bolt itself is fine (10 MPa, SF 3.3). Either catch the carriage near the module at the loading position (a stop
   under the latch housing, or a third tab), or release the latch before pulling, or keep the auger's grip on its plate
   well under 20 N.
4. **The side tabs' lip (v3) and foot (v4) meet their web in a sharp inside corner.** At 25 N the stress 1 mm from the corner
   is 12-14 MPa (SF 1.6-1.9 across layers), but the corner itself is a singular peak (65-87 MPa in the mesh), which is where
   a printed tab cracks. Fillet it (2 mm) or add a gusset. The tabs also catch only the tongue's -u 8 mm, which twists the
   tongue.
5. **Gravity is benign everywhere.** The lowest safety factor against PETG's creep allowable is 2.9 (v3 vertical runs, at
   finding 2's notch); sustained deflections are 0.4-0.8 mm (v3) and 1.1-1.4 mm (v4, on its one strip). The E-stop's
   0.68 m/s^2 is 7 % of g along the travel, covered by the vertical-run cases (1 g along the travel).
6. **The steel parts are far from their limits** (hinge pins, v4's latch pin: SF 13-24). The only marginal joint detail is the
   A-1 screw's head on the printed seat: a snug 300 N clamp presses 18 MPa into PETG, twice its creep allowable, so the
   clamp relaxes over days (the nylon-insert nut keeps the screw in, but the tab can then rock). Tighten to a light clamp,
   or use a thin washer (DIN 433, 6 mm OD fits the 6.4 mm counterbore: 15 MPa at 300 N), and check the screws after a week.

## Modelling assumptions that could change a conclusion

* The module is a rigid body; its weight and the hand and actuator loads are split statically between the hinge, the pads
  (v3) and the latch. The module's centre of mass (Sam x 107.4, beyond the plate's 103 mm end) puts nearly all of its weight
  on the latch or the pads and almost none on the hinge.
* Module mass from the exported STEP volumes (printed parts at 1.27 g/cm^3, steel 7.85) plus the v2 sim's auger 66.2 g,
  cap 5.4 g and 100 g of powder: 0.222 kg (v3), 0.213 kg (v4).
* A-1 tabs: rigid patches on the screw bore, the tab's footprint and the head seat. In the loop they are held in translation,
  with the bent tab's 6.0e4 N*mm/rad about u, held about w, and roll held at the front only. At the station and the loading
  position they are plain pins along u and x (the lips or side tabs take the radial load; the chain gives about 2.8 N/mm
  radially, ignored). Clamped A-1 joints would lower the loop deflections up to 2x; pinned would raise them about 1.7x.
* The lips and side tabs are fixed patches over their nominal overlap (no contact, no friction); the carriage is taken to
  have closed its 2 mm (lips) or 1 mm (v4 feet) gap already.
* The P16 stall's 50 N is all put through the hinge (the module blocked near it): an upper bound for the lugs and pins. With
  the module blocked at its cap end instead, part of it goes there.
* 40 N pull = 2 x loads.HAND_N; the auger's actual grip on Sam's plate was not measured. All stresses scale linearly.
* Printed PETG is linear elastic and isotropic (E 1810 short-term, 1000 creep); the allowables are the datasheet's across-layer
  strength (23 MPa) short-term and 8 MPa creep, along-layer (34 MPa) only where noted. Carriages print outer face down, so
  bending along the carriage is along its layers; the lugs and the side tabs' lips are loaded across theirs.
* v4 is analysed with the latch housing bridged to the -u strip (finding 1); the real v4 as drawn has no load path there.
* Large displacements (the 40 N pulls, 5-11 mm) are from a linear analysis; at those magnitudes it is a rating, not a prediction.

## Every case (raw)

The raw SF column uses the peak at singular corners (the side tabs' 0.27-0.36): read the table above for those.

| case | part | design | load case | max displacement (mm) | peak von Mises, supports excluded (MPa) | allowable (MPa) | SF | functional numbers |
|---|---|---|---|---|---|---|---|---|
| `v3_bottom` | carriage | v3 | bottom run, gravity (creep E) | 0.424 | 0.68 (raw 1.31, at [23.4, -11.3, 21.2]) | 8 | 11.83 | hinge lug -u dw -0.094 mm; latch housing mouth dw -0.398 mm; mid-span edge strips dw -0.393 mm; auger cap end dw from carriage bending -0.841 mm |
| `v3_down` | carriage | v3 | down run, gravity (creep E) | 0.412 | 2.80 (raw 2.80, at [25.5, -5.7, 25.6]) | 8 | 2.86 | hinge lug -u dw +0.019 mm; latch housing mouth dw +0.066 mm; mid-span edge strips dw -0.014 mm; auger cap end dw from carriage bending +0.192 mm |
| `v3_latch_bolt_pull` | latch bolt | v3 | keeper pushes the bolt's lap with 40.0 N | 0.099 | 10.36 (raw 14.87, at [105.5, -22.4, -12.6]) | 34 | 3.28 | bolt tip dz +0.098 mm; hand: 6 F a / (b h^2) at the mouth (MPa) 11.3 |
| `v3_latch_bolt_top_dyn` | latch bolt | v3 | keeper pushes the bolt's lap with 2.9 N | 0.007 | 0.79 (raw 1.30, at [105.5, -23.0, -12.6]) | 34 | 43.31 | bolt tip dz +0.007 mm; hand: 6 F a / (b h^2) at the mouth (MPa) 0.832 |
| `v3_pull` | carriage | v3 | loading: 40 N auger pull at Sam x 102 (latch closed), tongues in the side tabs | 5.920 | 22.29 (raw 22.29, at [-19.4, -11.3, -8.3]) | 23 | 1.03 | hinge lug -u dw +1.769 mm; latch housing mouth dw +5.641 mm; mid-span edge strips dw +4.521 mm; auger cap end dw from carriage bending +11.769 mm; side tabs reaction w (N) -40 |
| `v3_pull_x50` | carriage | v3 | loading: 40 N auger pull at Sam x 50 (latch closed), tongues in the side tabs | 3.587 | 19.52 (raw 19.52, at [-19.8, -11.0, -8.2]) | 23 | 1.18 | hinge lug -u dw +1.369 mm; latch housing mouth dw +3.490 mm; mid-span edge strips dw +2.997 mm; auger cap end dw from carriage bending +6.484 mm; side tabs reaction w (N) -40 |
| `v3_side_tab` | side tab | v3 | tongue pushes the lip with 25.0 N (auger pull) | 0.385 | 64.65 (raw 64.65, at [-21.0, -4.4, 5.5]) | 23 | 0.36 | lip tip dw +0.340 mm; von Mises 1 mm off the sharp root corner (MPa) 12.4; beam estimate 6 F a / (b h^2) at the root (MPa) 11.8 |
| `v3_station_p16` | carriage | v3 | station: P16 stall 50 N through the hinge, carriage in the hold-down lips | 1.218 | 16.13 (raw 16.13, at [-27.1, -6.3, 41.5]) | 23 | 1.43 | hinge lug -u dw +0.937 mm; latch housing mouth dw +0.969 mm; mid-span edge strips dw +0.902 mm; auger cap end dw from carriage bending +1.014 mm; von Mises in the lug-rib notches (MPa) 16.1; lips reaction w (N) -46.8 |
| `v3_top` | carriage | v3 | top run, gravity (creep E) | 0.802 | 1.33 (raw 2.41, at [-23.4, -11.3, 21.2]) | 8 | 5.99 | hinge lug -u dw +0.166 mm; latch housing mouth dw +0.658 mm; mid-span edge strips dw +0.395 mm; auger cap end dw from carriage bending +1.485 mm |
| `v3_top_dyn` | carriage | v3 | top run, gravity (creep E) | 1.020 | 1.70 (raw 3.07, at [-23.4, -11.3, 21.2]) | 8 | 4.71 | hinge lug -u dw +0.211 mm; latch housing mouth dw +0.838 mm; mid-span edge strips dw +0.502 mm; auger cap end dw from carriage bending +1.890 mm |
| `v3_up` | carriage | v3 | up run, gravity (creep E) | 0.411 | 2.71 (raw 2.71, at [-25.5, -5.7, 25.6]) | 8 | 2.95 | hinge lug -u dw -0.059 mm; latch housing mouth dw -0.095 mm; mid-span edge strips dw -0.017 mm; auger cap end dw from carriage bending -0.204 mm |
| `v4_bottom` | carriage | v4 | bottom run, gravity (creep E) | 1.131 | 1.64 (raw 2.88, at [-32.4, -11.3, 138.8]) | 8 | 4.88 | hinge lug -u dw -0.206 mm; latch housing mouth dw -1.056 mm; mid-span edge strips dw +0.152 mm; auger cap end dw from carriage bending -2.399 mm |
| `v4_bottom_dyn` | carriage | v4 | bottom run, gravity (creep E) | 1.439 | 2.09 (raw 3.66, at [-32.4, -11.3, 138.8]) | 8 | 3.83 | hinge lug -u dw -0.263 mm; latch housing mouth dw -1.345 mm; mid-span edge strips dw +0.193 mm; auger cap end dw from carriage bending -3.053 mm |
| `v4_down` | carriage | v4 | down run, gravity (creep E) | 0.420 | 2.15 (raw 2.15, at [24.9, -11.3, 19.9]) | 8 | 3.73 | hinge lug -u dw -0.013 mm; latch housing mouth dw -0.021 mm; mid-span edge strips dw +0.099 mm; auger cap end dw from carriage bending -0.067 mm |
| `v4_pull` | carriage | v4 | loading: 40 N auger pull at Sam x 102 (latch closed), tongues in the side tabs | 11.467 | 29.80 (raw 29.80, at [-32.4, -11.3, 138.8]) | 23 | 0.77 | hinge lug -u dw -2.289 mm; latch housing mouth dw -9.846 mm; mid-span edge strips dw -1.109 mm; auger cap end dw from carriage bending -21.755 mm; side tabs reaction w (N) 40.2 |
| `v4_pull_x50` | carriage | v4 | loading: 40 N auger pull at Sam x 50 (latch closed), tongues in the side tabs | 6.369 | 17.95 (raw 21.22, at [-19.7, -6.3, -8.0]) | 23 | 1.28 | hinge lug -u dw -1.481 mm; latch housing mouth dw -5.537 mm; mid-span edge strips dw -1.572 mm; auger cap end dw from carriage bending -11.536 mm; side tabs reaction w (N) 40.1 |
| `v4_side_tab` | side tab | v4 | tongue pushes the foot with 25.0 N (auger pull) | 0.456 | 86.51 (raw 86.51, at [-21.0, -12.3, 5.5]) | 23 | 0.27 | foot tip dw -0.409 mm; von Mises 1 mm off the sharp root corner (MPa) 14; beam estimate 6 F a / (b h^2) at the root (MPa) 11.8 |
| `v4_station_p16` | carriage | v4 | station: P16 stall 50 N through the hinge, carriage in the hold-down lips | 1.446 | 10.69 (raw 10.69, at [19.7, -11.3, -8.0]) | 23 | 2.15 | hinge lug -u dw +0.668 mm; latch housing mouth dw +0.753 mm; mid-span edge strips dw +1.304 mm; auger cap end dw from carriage bending +0.793 mm; lips reaction w (N) -47.1 |
| `v4_top` | carriage | v4 | top run, gravity (creep E) | 1.098 | 1.51 (raw 2.88, at [-32.4, -11.3, 138.8]) | 8 | 5.29 | hinge lug -u dw +0.208 mm; latch housing mouth dw +1.044 mm; mid-span edge strips dw -0.161 mm; auger cap end dw from carriage bending +2.368 mm |
| `v4_up` | carriage | v4 | up run, gravity (creep E) | 0.423 | 2.17 (raw 2.17, at [-24.9, -11.3, 19.9]) | 8 | 3.68 | hinge lug -u dw +0.037 mm; latch housing mouth dw +0.001 mm; mid-span edge strips dw -0.070 mm; auger cap end dw from carriage bending -0.014 mm |
