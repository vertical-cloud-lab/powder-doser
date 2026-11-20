# Purchased parts other than McMaster and Actuonix: model vs vendor (both carousels)

Checked 2026-10-27 in a headed Chromium that leaves through the doser Pi, with pointer moves and clicks
(`fetch_other.py`). Screenshots, page text, drawings and datasheets are in the git-ignored `files/<vendor>/` and
recorded with sha256 in `manifest_<vendor>.json`. "Before" is what `paternoster/` and `chain-carousel-v2/` modelled
until this audit. "Fixed" means the model now uses the vendor's number, and the code comment cites the source.
`compare/<key>.png` (`compare_other.py`) puts each model next to the vendor's drawing or photo: chain_rc35,
a1_cl35, sprocket_35bs32, sprocket_35bs15h, flange_sbsfl202, electromagnet_3872, pinion_ss1_20a, nema11_11hs18,
nema34_34hs59, extrusion_8020_2020, bracket_8020_14059, foot_lf020a, loadcell_tal221, solenoid_412, hall_us5881,
magnet_d42, bearing_6202 and vial_986546.

**Not reachable.** surpluscenter.com (sprockets 601139/601078/601077, flange bearing 600174) puts a Cloudflare
"verify you are human" check in front of the Pi's browser. Pointer clicks on it did not clear it, and the Wayback
Machine has no copy of those pages. So the makers' own tables stand in: Martin for 35BS32, Tritan (via
hvhindustrial.com) for 35BS15H, and the SBPFL202-10 table and drawing on usabearingsandbelts.com. Grainger's page
was blocked. StepperOnline's datasheet PDFs answer 403 to a plain request and did not download on a click, and its
STEPs need a login. KHK's 3D CAD needs an account, but its 2D sales drawing is public and was used.

**Vendor STEP.** None of these vendors offers CAD without an account (Adafruit_CAD_Parts has no 3872, 412 or 158).
The one vendor STEP on hand is StepperOnline's NEMA 34 file in `paternoster/reference/` (PR #115), which the
paternoster already draws. `vendor_other.nema34()` puts the same file in v2's stand-in frame, with the encoder lead
and plug that hang 150 mm out of the file cut off at the body, turned so the lead leaves toward +x as v2's stand-in
gland does. The boolean crop takes about 5 minutes on this runner, so it is cached as a BREP in the git-ignored
`files/stepperonline/`. v2's `nema34()` draws the STEP whenever that cache exists and the stand-in otherwise. The
cache was built on this runner on 2026-10-27. Every other part is built in `parts.py` from the drawing or table below.

| Part (vendor, PN) | Source used | Key dims, vendor (mm unless in) | Model before | Verdict | What changed |
|---|---|---|---|---|---|
| ANSI #35 chain, Nitro [RC35-1R-10FT](https://www.nitrochain.com/35-roller-chain-10ft) | Nitro dimension table (product page) | P 3/8; b1 3/16 (4.76); bushing d1 0.200 (5.08); pin d2 0.141 (3.58); plate h2 0.346 (8.79); T 0.050 (1.27); overall width L 0.488 (12.40) | plate height 9.0 (0.354); pins 11.81 long (paternoster), 10.81 (v2); **v2 drew the pins 5.0 mm** (its chain `PIN_D` was overridden by the hinge pin's `PIN_D = 5.0` later in params.py, so the bushings were 0.03 mm thick) | fixed | both `PLATE_H` 9.0 -> 8.79. Plain links' pins 12.40 long: paternoster `PIN_LEN_RC35` (the SA-1 link keeps McMaster's `PIN_LEN`), v2 `PIN_LEN`. v2 chain uses `CHAIN_PIN_D` 3.58 |
| #35 A-1 attachment link, Nitro [CL35-A1](https://www.nitrochain.com/35-a1-standard-attachment-connecting-link) (v2) | Nitro dimension table | G tab 0.312 (7.92); W centreline to tab end 0.562 (14.27); F to hole 0.375 (9.525); d4 0.133 (3.38); h4 0.250 (6.35); T 0.050 | 7.9, 14.3, 9.525, 3.38, 6.35 | match | none |
| Sprocket 35BS32-5/8, Surplus Center 601139 (Martin 35BS32 5/8) | Martin's table, quoted by [Tri-State Bearing](https://www.tristate-bearing.com/martin-35bs32-5-8-mar35bs325-8) | OD 4.032 in (102.4); PD 3.826 in (97.18); hub 2 in (50.8); LTB 7/8 in (22.2); keyway 3/16 x 3/32; 2 set screws 1/4-20 "on the centreline of a tooth" | OD 102.42, PD 97.13, hub 50.8, LTB 22.225, keyway 4.76 x 2.38; paternoster had 1 set screw | fixed (paternoster set screws) | paternoster `sprocket_32`: second set screw at 90 deg (as v2). The keyway sits on a tooth gap, 5.6 deg from Martin's tooth centreline: cosmetic, not changed |
| Sprocket 35BS15H-5/8, SC 601078, and -1/2, SC 601077 (v2 drive) | Tritan 35BS15H X 5/8 ([hvhindustrial](https://hvhindustrial.com/product/40338)) + the Grainger listing text in search results | OD 1.99 in; PD 1.804 in; hub 1-3/8 in (34.9); hub projection 0.582 in; LTB 3/4 in (19.05); keyway 3/16 x 3/32; set screws over the keyway and at 90 deg | hub 34.1 (1-11/32 in, from the BoM's earlier reading of Surplus Center's page); LTB 19.05 | match except hub (unverified) | none: Surplus Center's own hub figure could not be re-read. Tritan's is 0.8 mm larger |
| 2-bolt flange bearing SBSFL202-10 (= SBPFL202-10), SC 600174 | [USA Bearings & Belts SBPFL202-10](https://www.usabearingsandbelts.com/m7/SBPFL202-10--5-8-2-bolt-pressed-steel-flanged-bearing-unit-sbpfl202-10.html) table + drawing; listings in the search results (81 mm long, 63.5 mm bolts, 7.5 mm bolt hole) | a 3-3/16 (81.0); e 2-1/2 (63.5); B 2-5/16 (58.7); t 0.079 (2.0 sheet, x2 halves = 4.0 at the lobes); b 5/8 (15.9 dome to dome); S 9/32 (7.1 hole); L 0.8661 (22.0 inner ring) | L 81.5 over the lobes; T 3.0; insert 12.6 out / 9.6 in; domes 10.6 out / 8.6 in | fixed (ring position read off the drawing) | `BRG`: T 3.0 -> 4.0, OUT 12.6 -> 16.05, IN 9.6 -> 5.95, new DOME_OUT 9.95 / DOME_IN 5.95, lobe radius 9.0 -> 8.75. The bearing centre is one sheet above the mounting face, and the set-screw collar is outward. **Moves interfaces**, see below |
| Holding electromagnet P20/15, Adafruit [3872](https://www.adafruit.com/product/3872) | Adafruit Technical Details + its [diagram](https://cdn-shop.adafruit.com/product-files/3872/3872_diagram.png) | dia 20 x 15; centre pole dia 8; **M4 x 10 tapped hole in the back**; leads 270 | 20 x 15; ring mark 8.8-12.8; leads from the centre; no thread | fixed | `dock_magnet`: pole 8 / potting ring to 17, M4 x 10 (3.3 tap drill) in the back, leads beside it. The bracket can take an M4 screw instead of glue |
| Steel pinion KHK [SS1-20A](https://catalog.khkgears.us/item/spur-gears/spur-gears-ss/ss1-20a) | KHK catalog table + KHK 2D sales drawing (generated on khkgears.co.jp, no login) | m1, 20T, 20 deg, standard full depth; PD 20; OD 22; tooth depth 2.25; face 10; hub dia 16 x 10; total 20; **bore 5 H8**; M4 set screw 5 from the hub end; S45C, 37 g | 20-gon of 21.6 across, 10 wide, 5 bore (hub faced off by design) | fixed | `pinion_20t`: involute 20T m1 (OD 22, root 17.5), 10 wide, 5 bore (new `_spur_outline`). BoM text says "5 mm H7 bore": KHK says H8 |
| NEMA 11 11HS18-0674S, StepperOnline (doser's motor on Sam's carriage) | StepperOnline product page spec text (in the search results and the product page); PDF 403, STEP needs login | 28 x 28; body 45 (one reseller: 44.5); shaft dia 5 x 20; D-cut 15 long | 28 x 28 x 45; boss 22 x 1.5 (v2 21.8); shaft 5 x 20 round | fixed (D-cut) | `nema11_envelope`: 15 mm D-flat (0.5 deep, assumed). Boss and screw pattern not verifiable without the drawing |
| NEMA 34 34HS59-6004D-E1000 STEP (`paternoster/reference/`) | StepperOnline product page spec; drawing PDF 403 | frame 86; shaft dia 14 x 37, 25 keyed; "body length 175" | STEP: flange 86, bolt square 69.6 (4 x dia 6.5 holes), pilot 73 x 2.0, shaft 14 to z 36.5, body + encoder 169 | match, except length unresolved | v2: `nema34()` now draws this STEP (cropped, cached); stand-in `M34_PILOT_H` 1.6 -> 2.0. The page's 175 mm body length is 6 mm more than the STEP's 169: the drawing could not be fetched to settle it. The motor's own holes are 6.5 (`M34_HOLE_D` 5.5 stays: it is our plate's slot for the M5 screws) |
| 80/20 [20-2020](https://8020.net/20-2020.html) (paternoster) | 80/20 profile drawing (gallery image 2) + table | 20.00 sq; slot opening **5.26**; lips 1.50; slot 11.99 under the lips; core 7.32 (6.34 from a face); bore 4.19; webs 1.50; area 1.591 cm2 | Misumi slot 6: 6.2 opening, 1.8 lips, 11.0 x 6.1 slot, bore 4.2; rectangular cavities that met across the corner webs, so the profile was **5 separate solids** | fixed | `extrusion_2020`: 80/20 numbers; cavity walls run parallel to the 45 deg webs, so the profile is one solid (area 1.69 cm2) |
| 2020 extrusion, VEVOR 2020-100-10 (v2) | VEVOR product page | 20 x 20, centre hole dia 5, "European standard" | Misumi slot 6, bore 4.2, also 5 separate solids | fixed (bore; slot still Misumi's) | `extrusion_2020`: bore 5.0, cavity walls parallel to the webs (one solid) |
| Corner bracket 80/20 [14059](https://8020.net/14059.html) (paternoster) | 80/20 table + drawing | A = B = K = 18; F 3.0 legs; H 2.0; slots J 5.3 x G 7.0 at D 10.5 | solid wedge 20 x 20 x 18, legs 3.5, 5.5 holes at 12 | fixed | `corner_bracket` (paternoster): 18 legs, 3.0 thick, two 2.0 side walls, 5.3 x 7 slots at 10.5 |
| Corner bracket West3D NA0394 "like OpenBuilds" (v2) | West3D page (no dimensions); openbuildspartstore.com did not connect through the Pi | none published | 20 x 20 x 18, 3.5 legs | not verified | none |
| M5 drop-in T-nut West3D WES5240M5 | West3D page (no dimensions) | none published | 10 x 6 x 4 block | not verified | none. **80/20's 5.26 mm slot opening is narrower than the generic 6 mm slot these nuts are made for**: check the fit before ordering them for the paternoster, or use 80/20's own 20-series nuts |
| Leveling foot TNUTZ [LF-020-A](https://www.tnutz.com/product/lf-020-a/) | TNUTZ text + photo | M6 x 40 stud; dia 20 nylon base on a dia 10 ball end; hex nut | stud dia 5 (M5); pad dia 30 + hex | fixed (base height 9 read off the photo) | `leveling_foot`: dia 20 base, dia 10 ball, M6 stud, M6 jam nut under the rail. A 40 mm stud cannot sit at FOOT_H 15: the stud is cut to 21 (or raise FOOT_H) |
| Load cell SparkFun [SEN-14727](https://www.sparkfun.com/products/14727) (TAL221 100 g) | SparkFun spec ("47mm x 12mm x 6mm") + [TAL221 datasheet](https://cdn.sparkfun.com/assets/9/9/a/f/3/TAL221.pdf) drawing | 47 x 12 x 6; 2 x M3 tapped (fixed end) and 2 x dia 3.2 (free end), 6 apart across, 40 apart along; 20 mm binocular hole | 80 x 12.7 x 12.7 block (the TAL220's size) | fixed | `load_cell`: TAL221 bar, holes and binocular hole, on 3.35 mm spacers at both ends, so the stack is still 12.7. `LC_L` 80 -> 47 (both). **Moves interfaces**, see below |
| Push-pull solenoid Adafruit [412](https://www.adafruit.com/product/412) | Adafruit [drawing](https://cdn-shop.adafruit.com/product-files/412/412_C514-B_diagram.PDF) (TAU0730TM) | U-frame 17 x 14, 29.7 long; plunger dia 5 (tip 5 x 10); 51.9 overall; stroke 4.9; push end 15.4 out energised, 20.3 at rest | frame 15 x 12 x 32; plunger dia 4.5, 8 out | fixed (frame, plunger dia); protrusion kept | `solenoid_412`: 17 x 14 x 29.7 frame, dia 5 plunger. The plunger is still drawn 8 out. The real one stands 7.4 mm further out energised, so SOL_Z would have to drop that much for the tip to keep its place under the tube (not changed: it sits in Sam's carriage) |
| Hall switch US5881LUA, Adafruit [158](https://www.adafruit.com/product/158) | Adafruit dimensions + Melexis datasheet (US5881_rev007.pdf) | body 4.08 x 3.00 x 1.51; leads 1.27 pitch | 4.0 x 3.0 x 1.5 (v2); the paternoster draws a 12 x 16 holder envelope | fixed (v2) | v2 `hall_switch`: 4.08 x 3.00 x 1.51 |
| Disc magnet K&J [D42-N52](https://www.kjmagnetics.com/d42-n52-neodymium-disc-magnet) | K&J product page | 6.35 x 3.17 (+-0.1) | 6.35 x 3.18 | match | none |
| Ball bearing 6202-2RS (VXB) | [SKF 6202-2RSH](https://www.skf.com/group/products/rolling-bearings/ball-bearings/deep-groove-ball-bearings/productid-6202-2RSH) (ISO 15 x 35 x 11) | 15 x 35 x 11 | 15 x 35 x 11 | match | none |
| 20 mL vial Wheaton 986546 | pfstar.com + DWK/Sigma listings in the search results | OD 28 x **61 with the cap on** | 28 x 61, cap off | estimated | none. 61 mm is the capped height; the bare glass is a few mm shorter (not published). The mouth is then lower than drawn, and the D-funnel drop grows by that much |

## Interfaces that moved (for the lead)

* **Flange bearing (both).** `BRG["OUT"]` 12.6 -> 16.05 moves every insert-flush position out by 3.45 mm.
  * Paternoster: shaft ends `sh0` move 3.45 mm out each side, so the bottom shafts are 441.8 and 469.8 mm (BoM line
    6 says cut 435 + 463). The coupling (`c0`) and the motor move +3.45 mm in x. `MOTOR_STANDOFF` is 79.05 -> 82.5,
    so BoM line 18's 79 mm standoffs become 82.5 mm.
  * v2: `SHAFT_X0` -3.45 and `SHAFT_L` 402.9 -> 409.8 (BoM line 8 says cut 3 x 403 + 1 x 427; now 409.8 + 434.2).
    `X_DRV` +3.45 mm (drive chain plane, both 15T sprockets). The motor sprocket still sits on the 25 mm keyed part
    of the shaft (ring face at x 367.0, shaft end 372). `DRIVE_EXTRA` is unchanged.
  * `T` 3.0 -> 4.0 moves v2's bearing bolt heads 1 mm out (derived). The rear dome (5.95) still sits inside the
    6.35 plate's 49 mm hole.
* **Load cell (both), `LC_L` 80 -> 47.**
  * v2: `LC_Y0` is derived, so the fixed end moves 33 mm toward the vial and the free end stays at the cup arm.
    The 40 x 40 level wedge on the vial post (y -130..-90) now holds only the first 2 mm of the cell's fixed-end
    spacer. Move the post and wedge +33 mm in y, or lengthen the cup's arm by 33 mm and take 33 mm more off
    `LC_Y0`, so the fixed end stays on the wedge.
  * Paternoster: layout.py:411 hard-codes the fixed end at y -125, so the cell now ends at -78. The cup arm
    (-52..-12) no longer rests on it. Move the cell to -92 and the vial post (`VIAL_POST_Y` -120) to -87, or
    lengthen the arm.
  * Both: the layout's 12.7 mm stack height is unchanged (the TAL221's two 3.35 mm spacers). They are a new
    shop/printed item for the BoM: 7 x 12 x 3.35, two M3 holes.
* **Chain pin heads (paternoster).** The plain links' pins now stand 1.24 mm proud (Nitro L 0.488 in), so their ends
  are at x 6.20 from the chain plane. The gondola end plates start at `END_X0` 6.355: 0.16 mm of side clearance,
  down from 0.45. That is not an interference, but it is tight for chain side play. Consider `END_X0` +0.3.
  v2's pins also grew (10.81 -> 12.40). The tab hooks sit beside the tab, away from the pin heads, but run
  `check_interference.py` to confirm.
* **BoM text.** KHK SS1-20A's bore is 5 H8, not H7. Surplus Center's 35BS15H hub (1-11/32 in on the BoM) is 1-3/8 in
  on Tritan's page. The vial's 28 x 61 is with the cap.

## Not done or not verifiable

* Surplus Center's own spec tables (bot check). The maker's tables match the BoM's numbers except the 15T hub.
* StepperOnline drawings for the NEMA 11 and NEMA 34 (403 on request; the click did not download). So the NEMA 11
  boss height, the M2.5 pattern, the flat orientation and the NEMA 34's 169 vs 175 mm length are open.
* West3D's T-nut and bracket dimensions (none published), and the OpenBuilds page (no connection through the Pi).
* v2's NEMA 34 with the vendor STEP has not been through `check_interference.py`. The cropped body is the
  stand-in's envelope (86 square, 169 long, shaft 14 x 37), but the real flange, pilot and encoder may sit closer
  to neighbours than the stand-in did. The STEP is used only where `files/stepperonline/` holds the cache.
