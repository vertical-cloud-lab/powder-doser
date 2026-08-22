# Sourcing an isolation slab for the HR-100A balance

Buy-list and sizing note for [`#146`](https://github.com/vertical-cloud-lab/powder-doser/issues/146),
which follows point 4(d) of the environment survey in
[`#116`](https://github.com/vertical-cloud-lab/powder-doser/issues/116#issuecomment-5358891531).

Prices spot-checked 2026-08-20 and *will* drift; treat the links as the
source of truth, not the numbers.

**The whole buy, if you only read one line:** get ~30 kg of granite —
free-to-$50 as a 3 cm sink cutout from any of the eight Utah County
fabricators listed below, or
[Grizzly G9651](https://www.grizzly.com/products/grizzly-12-x-18-x-3-granite-surface-plate-no-ledge/g9651)
12 × 18 × 3 in ($69.95 + ~$30–60 shipping, ~29 kg, verified in stock
2026-08-22) if nobody local answers in 48 h. **Buy nothing else.** The
rubber comes out of the tensegrity drop-tower stock, and whether it
belongs under the slab at all is the open question this hardware exists to
settle — see the four-arm comparison below. Granite, not marble; reasons
for that one below too.

**What changed, and why the buy shrank.** The first draft of this note
recommended granite *plus* four 7/8 in polyurethane pads as a single
purchase. An Edison adversarial re-analysis
([`outputs/isolator-spotcheck/`](../outputs/isolator-spotcheck/)) then
argued the pads are the wrong lever — that a ~100 mg *permanent* offset is
a tilt-latching event rather than steady-state vibration transmission, and
that soft corner pads make the tilt degrees of freedom *worse* while
adding a creep path that can manufacture the very artifact being chased.
The shape-factor arithmetic that motivated pads-over-sheet survived
review; its relevance did not. Neither position is settled from the
armchair, so the slab is now bought on its own and the pads become a
**measured comparison** rather than an assumption.

## What the slab is actually for

The 600 s bare-pan survey separated three effects. Only one of them is a
slab problem:

| effect | measured | does a slab fix it? |
|---|---|---|
| draft / continuous vibration (jitter) | 0.111 mg sample-to-sample — *below* the 0.1 mg display resolution | **No.** Already at the noise floor; nothing to win. |
| zero creep | −5.4 mg/min | **No.** Thermal equilibration and load-cell creep, internal to the balance. |
| mechanical step events | ~1 per 10 min, ~100 mg, permanent offset | **Yes.** This is the entire justification. |

So the acceptance test is *step-event rate and amplitude*, not
peak-to-peak. Expect jitter and creep to be unchanged afterwards — that
is not a failed installation.

## Sizing constraints

HR-100A, from the [HR-A / HR-AZ manual](https://weighing.andonline.com/wp-content/uploads/2024/01/HR-A_HR-AZ_Manual_02.pdf)
§21 (specifications) and §22 (external dimensions):

| | |
|---|---|
| external dimensions | **198 (W) × 294 (D) × 315 (H) mm** |
| net weight | **approx. 3.5 kg** |
| weighing pan | Ø 90 mm |
| breeze break | 183 × 148.5 × 251 mm |

Manual §3-1, *Before Use*: *"Install the balance in a stable place
avoiding vibration and shock… The weighing table should be solid and
free from vibration, drafts and as level as possible."*

Derived targets:

- **Slab mass ≥ 20 kg** — ≥ 5× the balance's 3.5 kg. For a force injected
  into the top surface, peak acceleration goes as 1/m_total, so 3.5 kg →
  32 kg is a ~9× reduction. 25–35 kg is the sweet spot; past that you are
  paying in fume-hood deck load and in not being able to lift it.
- **Thickness ≥ 30 mm.** Thin tiles have low-frequency bending modes and
  ring. 50–75 mm is better.
- **Plan area** must cover the balance's 198 × 294 mm footprint with
  margin — and see the height/straddle problem below, which is the part
  that is easy to get wrong.

## The straddle problem — read before ordering

In the current rig the doser platform **already bridges over the
balance** on four legs that land on the fume-hood deck, and the balance
sits directly on that same deck. Clearance between the top of the breeze
break and the underside of the platform is small. Putting a 50–75 mm slab
under the balance alone raises it into the platform.

Two ways out:

- **Option A — one slab carries everything** (balance *and* the four
  bridge legs). No height re-engineering, relative geometry preserved,
  and it still addresses the identified disturbance, which is external
  (doors, footfalls, benchwork) rather than self-generated. Needs a
  larger plan area. **Start here** — it is the reversible experiment.
- **Option B — balance on its own slab, bridge legs on the deck.** Better
  ultimate isolation, because the tapper solenoid and the steppers then
  have no rigid path into the weighing mass. Costs a re-print of the
  bridge legs, ~50–75 mm taller.

**Measure before ordering:** the outer leg-to-leg footprint of the doser
platform. From the bench photo it is roughly 265 mm across, but that is a
perspective estimate, not a caliper. If it is ≤ 280 × 430 mm, a 12" × 18"
plate carries the whole assembly (Option A); otherwise go 18" × 18".

## Granite or marble?

**Granite.** Not close, and the deciding reason is chemical, not mechanical:

| | granite | marble |
|---|---|---|
| mineralogy | quartz + feldspar (silicate) | recrystallised calcite (CaCO₃) |
| Mohs hardness | 6–7 | 3–4 |
| acid resistance | inert to everything in a fume hood | **etches in any acid, including vapour** |
| porosity | low | higher; stains and absorbs |
| Young's modulus | ~50–70 GPa | ~40–70 GPa, more variable |
| density | 2.65–2.75 g/cm³ | 2.6–2.7 g/cm³ |

For a mass-plus-isolator stack the two are interchangeable *dynamically* —
at 30 kg the slab is a rigid body well below 1 kHz either way, and the
internal damping of both stones is negligible next to the elastomer under
them (that layer is where all the damping comes from; see below). What
separates them is that this slab lives in a fume hood: calcite marble is
attacked by acid vapour and is soft enough to scar from a dropped vial,
whereas granite is the material machinist surface plates are made from
precisely because it is hard, non-porous, non-magnetic, and dimensionally
stable. Buy marble only if a free remnant of it turns up and the hood is
known to be acid-free.

(Note the trade names lie: "black granite" surface plates are usually
diabase/gabbro, and much commercial "black marble" is limestone. Test
with a drop of vinegar on a hidden edge — fizzing means carbonate, i.e.
marble, i.e. pick the other one.)

## Options, cheapest first

Calculated masses use ρ = 2.75 g/cm³ for granite, 2.3 for concrete.
Vendor-listed weights are often *shipping* weights and run high.

### 1. Countertop remnant or sink cutout — free to ~$50

The cheapest good answer, if you are willing to make phone calls. Stone
fabricators generate sink cutouts continuously and mostly treat them as
waste. A typical 3 cm cutout is ~483 × 838 mm → **~33 kg**, which is
almost exactly the target mass, and one face is already polished and
sealed.

Ask specifically for a **sink cutout** or a **3 cm remnant** — 3 cm, not
2 cm, because 30 mm is exactly the thickness floor above and a 2 cm
cutout is under it. Ask them to flat-grind or at least chamfer the sawn
edges. Trade-off: edges may be raw, and the faces are not parallel to any
spec (fine — the balance has leveling feet and a bubble level).

#### Utah County call list, verified 2026-08-22

Pulled from the Pi (campus IP) against each fabricator's own site, so the
numbers are theirs rather than a directory's. Nearest first:

| where | address / phone | why this one |
|---|---|---|
| **Habitat for Humanity ReStore** | [340 S. Orem Blvd, Orem 84058](https://www.habitatuc.org/restore/) · 801-344-8527 | Donated countertop offcuts turn up constantly; walk in and look. Cheapest realistic path, and no phone tag. |
| **Rock Solid Granite** | [1161 W 780 N, Orem 84057](https://fablocator.com/fabricators/ut/orem/rock-solid-granite-countertops) · (801) 225-0812 | Runs a **searchable remnant inventory** (slabzone.com) — the only one here with published stock. Inventory page is JS-rendered, so browse it in a browser. |
| **Big Mountain Countertops** | [317 N Main, Orem 84057](https://www.bigmountaincountertops.com/) · 801-225-6521 | 25+ years, walk-in shop on Main. |
| **Little Stone Countertops** | [1452 S State St, Provo 84606](https://www.littlestonecountertops.com/) · — | Closest to campus. |
| **Cobble Creek Countertops** | Utah County · [801-618-7699](https://www.cobblecreekcountertops.com/area/utah-county) | Site explicitly advertises in-house sink cutouts, i.e. they generate exactly this offcut. |
| **Granite Countertops Utah** | SL + Utah County · [(801) 376-3856](https://granitecountertopsutah.com/) | Same — sink cutouts called out as standard work. |
| **Quality Granite Utah** | [801-800-1244](https://qualitygraniteutah.com/) | |
| **Accent Countertops** | [801-269-0701](https://accentcountertops.com/quartz-marble-granite-remnants-nevada-utah/) | Has a formal, priced **remnant program** rather than ad-hoc scrap. |

The ask on the phone is one sentence: *"Do you have a 3 cm granite sink
cutout or remnant, roughly 12 × 18 inches or larger, that I could buy or
take off your hands?"* Say it is going under a lab balance, not into a
kitchen — cosmetic rejects are perfect and they know it.

Also checked and **not** worth the trip:

- **KSL Classifieds** ([classifieds.ksl.com](https://classifieds.ksl.com/search/keyword/surface%20plate))
  — searched today for surface plate / granite plate / granite remnant /
  granite scrap. The only precision plate listed statewide is a Starrett
  **36 × 60 grade A with stand in Provo at $4,000** — roughly 600 kg and
  two orders of magnitude past what this needs. Everything else is
  countertop scrap in Ogden/Logan at $30–45. Worth re-checking later; the
  right listing does occasionally appear.
- **Home Depot and Lowe's do not sell granite slabs**, only fabricated
  countertops and samples. What they do have same-day in Orem/Provo is
  concrete step stones — that is option 3 below, and it is a legitimate
  way to start this week. Both sites blocked every automated request, so
  **step-stone stock is unverified and needs a human to check.**
- [RemnantSwap](https://www.remnantswap.com/) — national remnant
  marketplace, thin in Utah.
- **BYU Surplus** ([surplus.byu.edu](https://surplus.byu.edu/)) — worth a
  standing watch; retired metrology gear passes through, and a lab
  surface plate would be free-to-cheap. Not something to wait on.

### 2. Machinist granite surface plate — $40–100 ⭐ the no-phone-calls option

The "just order it and be done" option, and what a surface plate *is* for
is exactly this job: a lapped, dead-flat, sealed, non-magnetic reference
mass with parallel faces and finished edges. Grade B tool-room plates:

| Grizzly p/n | size | calc. mass | listed wt. | price |
|---|---|---|---|---|
| [G9649](https://www.grizzly.com/products/grizzly-9-x-12-x-2-granite-surface-plate-no-ledge/g9649) | 9 × 12 × 2 in | ~9.8 kg | — | $39.95 |
| [**G9651**](https://www.grizzly.com/products/grizzly-12-x-18-x-3-granite-surface-plate-no-ledge/g9651) | **12 × 18 × 3 in** | **~29 kg** | 79 lb | **$69.95** |
| [G9653](https://www.grizzly.com/products/grizzly-18-x-18-x-3-granite-surface-plate-no-ledge/g9653) | 18 × 18 × 3 in | ~44 kg | 120 lb | $79.95 |
| [G9654](https://www.grizzly.com/products/grizzly-18-x-24-x-3-granite-surface-plate-no-ledge/g9654) | 18 × 24 × 3 in | ~58 kg | 154 lb | $99.95 |

**G9651 (12 × 18 × 3) is the pick.** 305 × 457 mm gives generous margin
on the 198 × 294 mm balance, ~29 kg is in the sweet spot, and it is one
person's lift. Buy G9653 instead only if the measured bridge footprint
exceeds 280 mm across. Avoid G9649 — 229 × 305 mm is essentially the
balance footprint with no margin, and 9.8 kg is under the mass target.

All four re-verified 2026-08-22 from the Pi: prices unchanged, all
`schema.org/InStock`. **Shipping is not free and is not in the sticker
price** — G9651 is a ~79 lb shipment, so budget roughly another $30–60 to
Utah and treat the delivered cost as ~$100–130. (G9649's record shows
`IsFreight: false`, i.e. parcel; the larger three pages carry both flags
across the several SKUs on them, so which applies is not resolvable by
scraping — get the real number from the cart before committing.) That gap
is most of the reason to make two local phone calls first.

Cross-shopping, same date: Shars grade A 12 × 18 runs ~$123 (a finer grade
than this needs), Zoro lists comparable plates at $98–138, and Amazon's
results for the search are mostly either angle plates or four-figure
Starrett inspection stock. **Harbor Freight no longer carries granite
surface plates at all** — its own site search returns "Sorry, no items
found", so the once-standard "just grab one locally at HF" answer is dead.

### 3. Stacked concrete step stones — ~$10

If you want to test the hypothesis this week for the price of lunch.
[Pavestone 12 × 12 × 1.5 in](https://www.homedepot.com/p/Pavestone-12-in-x-12-in-x-1-5-in-Rustic-Blend-Square-Concrete-Step-Stone-71218-0/202843017)
is ~$2–4 and ~8 kg each; **three stacked = ~24 kg**.

Not granite, and that is fine — concrete has *higher* internal damping
than granite. Interleave a thin neoprene or rubber sheet between layers
and the stack becomes a constrained-layer damper, which kills ring modes
better than a monolithic slab does. (That interleaving is *inside the
mass*, where the layer is fully confined and carries no isolation duty —
it is not the same thing as stacking isolator pads, which the rubber
section below rules out.) Two caveats: seal or bag it, because
raw concrete is dusty and porous and this lives in a fume hood with
powders; and shim it, because step stones are not flat.

### 4. Marble/granite pastry board — $40–60

E.g. [16 × 20 × 0.7 in, ~10 kg](https://www.amazon.com/Adolif-Granite-Cutting-Marble-Kitchen/dp/B0DJP8LYM7),
usually with rubber feet fitted. Sealed and finished, but **too thin and
too light to use alone**. Useful as a finished top plate over stacked
pavers (option 3).

### For reference — the thing we are avoiding

[A&D AD-1671](https://www.aandd.jp/products/peripheral/ad1671.html), the
factory anti-vibration table for exactly this balance family: **~$1,575**.
Options 1–3 target the same failure mode for 1–5 % of that.

## The isolation layer matters as much as the mass

A slab set down hard on the deck is a rigid path. Mass alone helps, but
the compliance under it is what makes a low-pass filter.

Resonance of the sprung mass: **f₀ [Hz] ≈ 15.76 / √(δ [mm])**, where δ is
the static deflection of the isolators under the full load.
Transmissibility above resonance is ≈ 1/((f/f₀)² − 1):

| δ | f₀ | at 20 Hz | at 50 Hz | at 100 Hz |
|---|---|---|---|---|
| 3 mm | 9.1 Hz | −12 dB | −29 dB | −42 dB |
| **5 mm** | **7.0 Hz** | **−17 dB** | **−34 dB** | **−46 dB** |
| 10 mm | 5.0 Hz | −23 dB | −40 dB | −52 dB |

Door slams and footfalls put most of their energy in 10–60 Hz, so
δ ≈ 5–10 mm (f₀ ≈ 5–7 Hz) is the target. Softer is monotonically better
*for attenuation* — what bounds it from above is stability, not physics
of the filter: see the foam warning below.

That is the target, not the achievable number. 5 mm of static deflection
from a solid elastomer needs ~25 mm of stock at a sane 20 % strain, and a
25 mm-tall pad narrow enough to reach that strain under only 8 kg per
corner is taller than it is wide — i.e. it buckles. The practical
operating point with sheet stock is **δ ≈ 2–3 mm, f₀ ≈ 9–11 Hz**, which is
the sizing worked out two sections below. Commercial 7 Hz tables get the
extra octave from moulded hemispherical or bonded-stud isolators, not from
flat pads.

- **The candidate isolator is four small pads of highly damped
  polyurethane** — sizing in the next section. Whether it beats a bare
  slab is the open question the four-arm comparison below exists to
  answer; the sections that follow size the pads, they do not justify
  fitting them.
- **4 × double-yellow squash balls**, one per corner, are the standard
  cheap alternative, and there is a
  [printable cup/foot for them](https://www.printables.com/model/62634-anti-vibration-squash-ball-feet-for-stone-concrete).
  Under ~8 kg per corner they deflect a few mm, landing near the target.
  Downside: they are a *pressure vessel*, so they slowly leak and stiffen,
  and there is no way to know where in that drift you are.
- **Do not** use soft open-cell foam alone. Large deflection under a tall
  centre of gravity gives a rocking mode at 1–3 Hz — right where footfall
  energy lives — and the balance will settle slowly after every load.
- Note the flip side of the equation: **near f₀ the slab amplifies.**
  Lossy isolators cap that peak at ~2–3×; steel springs would not. This is
  the single strongest argument for a high-loss elastomer here, and it is
  sharper for Option A than the table above suggests — with the doser
  bridge on the same slab, the tapper solenoid excites f₀ *from inside the
  isolated mass* on every dose.

## The rubber layer — borrow it, don't buy it

**Do not order rubber.** Everything the comparison below needs already
exists in the drop-tower stock in
[`tensegrity-optimization`](https://github.com/vertical-cloud-lab/tensegrity-optimization)
([#88](https://github.com/vertical-cloud-lab/tensegrity-optimization/issues/88),
[PR #86](https://github.com/vertical-cloud-lab/tensegrity-optimization/pull/86)):
the same 70 Shore OO super-cushioning polyurethane, in 12 × 12 in sheets.
Four 7/8 in pads is 3 in² — a rounding error against a 12 × 12 sheet, and
easy to lop off an edge. Borrow, test, and only then decide whether any of
it is worth owning.

**One handling rule that constrains the running order:** cutting pads out
of a sheet destroys that sheet as a full-area mat. If both a 1/4 in and a
1/2 in sheet are available, use the **1/4 in as the mat** and cut pads
from the **1/2 in** — no conflict. With only one sheet, **run the mat arm
before cutting**, and take the pads from one edge so what remains is still
contiguous. The arm order below is built around this.

If it later turns out pads are worth owning, the reference part is
[McMaster 8514K315](https://www.mcmaster.com/8514K315/) — 4" × 4" × 1/2",
70 Shore OO, $15.04, one piece yields sixteen pads. Prices below are kept
for that decision, not for this week.

### Prices — the whole family, verified 2026-08-20

Same material throughout; only size, thickness and durometer change. The
`8514K3xx` / `8514K5xx` numbers are the stocked ones (**next-day**); the
otherwise-identical `8514K5x` / `8514K6x` listings quote **2–3 weeks**,
which is worth knowing because `8514K63` — the number chosen in #88 — is
currently one of the slow ones and `8514K521` is the same 1/4 in 70 OO
sheet at the same $56.01, shipping tomorrow.

| part | size | thickness | durometer | price | ships |
|---|---|---|---|---|---|
| [**8514K315**](https://www.mcmaster.com/8514K315/) | **4" × 4"** | **1/2"** | **70 OO** | **$15.04** | **next day** |
| [8514K313](https://www.mcmaster.com/8514K313/) | 4" × 4" | 1/4" | 70 OO | $11.43 | next day |
| [8514K314](https://www.mcmaster.com/8514K314/) | 4" × 4" | 3/8" | 70 OO | $12.62 | next day |
| [8514K215](https://www.mcmaster.com/8514K215/) | 4" × 4" | 1/2" | 50 OO | $15.04 | next day |
| [8514K115](https://www.mcmaster.com/8514K115/) | 4" × 4" | 1/2" | 40 OO | $15.04 | next day |
| [8514K521](https://www.mcmaster.com/8514K521/) | 12" × 12" | 1/4" | 70 OO | $56.01 | next day |
| [8514K515](https://www.mcmaster.com/8514K515/) | 12" × 12" | 1/2" | 70 OO | $105.60 | next day |
| [8514K518](https://www.mcmaster.com/8514K518/) | 12" × 12" | 1" | 70 OO | $194.49 | next day |
| [8514K2](https://www.mcmaster.com/8514K2/) | sample pack | — | 30/40/50/60/70 OO | $11.01 / 5 | next day |

The 4 × 4 in pieces are the right buy by a wide margin: the pads need ~3 in²
and the 12 × 12 in sheets cost 7× more for area that gets thrown away.
Durometer is the one axis worth hedging — $45 buys 40, 50 and 70 OO in
1/2 in and turns the sizing calculation below into a measurement.

### Why this material and not neoprene, cork, or a stall mat

McMaster's "super-cushioning polyurethane" is a viscoelastic PU in the
Sorbothane class — loss factor tan δ ≈ 0.5, against ≈ 0.05–0.1 for
neoprene or EPDM. Three reasons that matters here:

1. **The resonance peak is the risk, not the roll-off.** Any isolator
   amplifies near f₀. At tan δ ≈ 0.5 the peak is ~2.2×; a lightly damped
   rubber pad peaks at 5–10× and rings for many cycles after every door
   slam and every tapper pulse. A balance that has to settle to 0.1 mg
   cannot afford ring-down.
2. **It has already been qualified for repeated shock in this lab.** The
   40-drop sweep in
   [`drop-test-pu-configs-analysis.md`](https://github.com/vertical-cloud-lab/tensegrity-optimization/blob/copilot/add-drop-test-protocol-again/docs/drop-test-pu-configs-analysis.md)
   ran 5.5 m/s impacts on the 1/4 in and 1/2 in sheets and found **no
   bedding-in trend** and input CV 1.4–1.8 %, where the felt it replaced
   compacted monotonically. Under a static 32 kg the duty is trivial by
   comparison, so the creep/compression-set question is settled for us.
3. **The specific failure mode it fixed there is the one we care about
   here.** Felt's problem was not the low-frequency peak but added
   high-frequency spike content (raw CH5 26.2 % FS on 1/4 in PU and 6.2 %
   on 1/2 in, vs 91 % on worn felt) — i.e. damping, not compliance, was
   the discriminator. The ~100 mg step events are short-duration
   disturbances too.

Be clear about what that program does *not* license: its arrangement
ranking was **withdrawn** after an Edison adversarial re-analysis (task
`d9092c5a`) found the transmissibility baseline wrong, and the standing
verdict there is "the sweep cannot decide." What survives is material
behaviour — durability, no compaction, high loss — which is all this
application needs.

**One transferable result does carry over, and it is a hard constraint:**
the earlier paired test found the two sheets *stacked* toggled between two
stiffness states drop to drop, traced to seating at the sheet-to-sheet
interface, and a single sheet removed it. A bistable interface under this
slab would present as an occasional discrete offset — indistinguishable
from the very step events the slab is meant to remove. So: **one layer of
rubber, cut clean, seated once. Never a stack.**

### Pads, not a sheet — this is the part that is easy to get wrong

The instinct is to lay a 12 × 12 in sheet under the slab. That does almost
nothing, because a thin elastomer layer that is wide compared to its
thickness cannot bulge sideways, and a rubber that cannot bulge cannot
compress. The correction is the shape factor S (loaded area ÷ free-to-bulge
area), with effective compression modulus E_c ≈ E(1 + 2S²):

| layout under the 12 × 18 in slab | S | E_c | static deflection | f₀ |
|---|---|---|---|---|
| full-area 1/4 in sheet | ~14 | ~300 MPa | ~0.00005 mm | ≈ rigid — **no isolation at all** |
| four 7/8 in × 7/8 in × 1/2 in pads | 0.44 | ~0.97 MPa | ~2.1 mm | ~11 Hz |

Same rubber, ~40 000× difference in compliance — and the sheet is the
*thicker* pile of it. The
full sheet is a gasket that hides deck roughness; only the small pads are
a spring.

### Pad sizing

Assumptions: 29 kg slab (G9651) + 3.5 kg balance ≈ 32.5 kg → ~80 N per pad
on four pads; 1/2 in (12.7 mm) stock; 70 Shore OO ≈ 20–25 Shore A →
E ≈ 0.7 MPa; square pad of side *a*, S = a/4t, δ = (F/a²)·t/E_c.

| pad side *a* | static strain | δ | f₀ | verdict |
|---|---|---|---|---|
| 1 1/2" | 3.7 % | 0.47 mm | 23 Hz | too stiff — barely better than bare deck |
| 1 1/4" | 6.4 % | 0.81 mm | 18 Hz | still stiff |
| 1" | 12 % | 1.50 mm | 13 Hz | conservative start |
| **7/8"** | **17 %** | **2.1 mm** | **11 Hz** | **the size arm B tests** |
| 3/4" | 25 % | 3.1 mm | 8.9 Hz | best attenuation; at the long-term strain limit |
| 5/8" | 38 % | — | — | over-strained; will creep and go non-linear |

7/8 in sits at ~17 % static strain, inside the 10–20 % band elastomer
isolators are designed around, and lands f₀ at ~11 Hz. Go to 3/4 in only
if the measured step events survive and you accept 25 % strain (re-check
pad height annually).

Honest accounting of what that buys, since the undamped table earlier in
this note is optimistic for a lossy material — at ζ ≈ 0.25 the roll-off is
closer to 6 dB/octave than 12:

| | at 20 Hz | at 50 Hz | at 100 Hz | peak at f₀ |
|---|---|---|---|---|
| undamped model, f₀ = 11 Hz | −7 dB | −26 dB | −38 dB | ∞ |
| **with tan δ ≈ 0.5 (real)** | **−5 dB** | **−18 dB** | **−25 dB** | **2.2×** |

That trade — giving up ~13 dB up high to cap the resonance at 2.2× — is
the right one for a balance, and it is the whole reason for choosing this
rubber over a cheaper one.

**E for 70 Shore OO is a ±50 % estimate**, so treat the table as a
starting point, not a specification. It is directly checkable: measure
pad height with calipers unloaded and loaded, and read f₀ back off
f₀ ≈ 15.76/√δ. If δ comes in under 1 mm, trim the pads smaller; over
3 mm, cut them larger. That is the same "tune pad area empirically"
conclusion the drop-test work reached.

### Cutting and installing

- Cut with a fresh utility knife against a steel rule on a sacrificial
  board, several light passes. Wipe the blade with soapy water — this
  material grabs. Cut all four pads from one region of the sheet so
  thickness is matched.
- Place the pads inset ~10–15 % of the span from each corner, not right at
  the edges — an overhanging slab corner is a lever on a soft pad.
- **Nothing goes between the balance and the stone.** The balance's own
  feet couple it rigidly to the mass; that is the point of the mass. Rubber
  belongs only between stone and deck.
- If the hood deck is visibly uneven, three pads instead of four is
  kinematically determinate and self-levelling — scale to 1" squares to
  keep the same strain (107 N per pad). Only do this if the loaded
  footprint is well inside the triangle; with the doser bridge on the slab
  it usually is not, so four is the default.
- Pads are not bonded. If the assembly ever needs to be nudged, lift it —
  dragging it will roll the pads under and change δ.

## Fume-hood specifics

- Check the deck's load rating with EHS before adding ~30 kg. Epoxy-resin
  tops handle far more, but the conversation is cheap.
- Raising equipment ~50 mm off the work surface is *recommended*
  practice for airflow under it, so the slab is a small win there.
- Do not let the taller assembly block the rear baffle slots, and keep it
  ≥ 150 mm behind the sash plane.
- Sealed granite is chemically fine. Raw concrete is not — bag or seal it.

## The four-arm comparison — settle it by measurement

The note above contains a genuine, unresolved disagreement: shape-factor
mechanics says small pads are the only real spring and a full sheet is a
gasket; the Edison re-analysis says compliance is the wrong lever entirely
and pads make the sensitive (tilt) degrees of freedom worse. Both
arguments are coherent. Neither is going to win on paper. So the granite
gets bought once and then carries **four configurations**, and the rubber
is borrowed rather than bought precisely because it might turn out to be
the wrong answer.

### The arms, in running order

| arm | build | what it isolates |
|---|---|---|
| **A0** | balance on the hood deck exactly as today | contemporaneous baseline |
| **A** | balance on granite, granite **flat on the deck** | mass loading alone — no new degrees of freedom |
| **C** | balance on granite, granite on the **full sheet** | the "gasket" case: contact conformity without a soft mode |
| **B** | balance on granite, granite on **four 7/8 in pads** | the compliance case |
| **A′** | rebuild of A, unchanged | day-to-day reproducibility — the control on the controls |

Order is not arbitrary. C precedes B because the pads are cut from the mat
(above). A′ closes the loop: if A and A′ disagree, building activity
changed underneath the experiment and *no* comparison in the set is
trustworthy. Without A′ there is no way to tell a real 1.4× from a quiet
week.

**A0 must be re-measured, not looked up.** The existing baseline — jitter
0.111 mg, creep −5.4 mg/min, ~1 step event per 10 min — came from a single
600 s run on a different day. Re-using it as the control silently assumes
the room is stationary, which is the one thing this whole exercise
suspects is false.

### What each model predicts — write this down before running

| arm | shape-factor / transmissibility model | tilt-latching model (Edison) |
|---|---|---|
| **A** granite direct | modest gain: injected force sees 32.5 kg instead of 3.5 kg | **largest gain** — mass-loads a compliant deck panel and adds nothing that can latch |
| **C** granite + full sheet | **≈ A, within noise** — S ≈ 14 makes it ~30 000× stiffer than pads, so it is not a spring | possibly better than A — conforms to deck roughness, kills three-point rock |
| **B** granite + four pads | **best** — f₀ ≈ 11 Hz, roll-off above ~15 Hz | **worst, and worsening** — new ~5 Hz horizontal and ~9–12 Hz rocking modes, plus differential creep → slow tilt drift |

**The sharp test is C vs A.** "A full sheet does essentially nothing" is
the shape-factor argument's most falsifiable claim, and it is cheap to
check. If C beats A by more than the confidence interval, the compliance
framing is wrong about *why* — the mechanism would then be contact and
seating (a conforming layer removing a bistable three-point contact),
which is a latching story, not a transmissibility story. That single
comparison discriminates between the two models better than B does,
because B confounds compliance with two new modes at once.

### How long each arm has to run — this is the part that bites

At the measured ~6 events/hour, **the default 600 s survey expects one
event.** One count against one count cannot resolve a 5× improvement; it
cannot reliably resolve a 100× one. Running the survey before and after
and comparing the printed step counts — which is what the commissioning
step below used to say — is not a weak test, it is no test.

`python scripts/step_event_rate.py --power` prints the sizing. At α = 0.05
and 80 % power, against a 6/h baseline:

| to detect | events/arm | hours/arm | 4 arms |
|---|---|---|---|
| 10× reduction | 8 | 1.4 | 6 h |
| 4× reduction | 16 | 2.6 | 10 h |
| 2× reduction | 46 | 7.6 | 31 h |
| 1.5× reduction | 117 | 19.4 | 78 h |

Zero events is worth more than the table suggests — by the rule of three,
**0 events in 2 h already rules out anything worse than a 4× reduction**
at 95 %.

Two practical settings follow:

- **Screening pass, ~2 h/arm (10 h total, one working day).** Answers
  "did anything change by 4× or more?" Enough to kill an arm.
- **The real pass, 24 h/arm (5 days including A′).** ~144 events per arm,
  resolves down to ~1.4×, and — the reason 24 and not 8 — **each arm then
  spans a full diurnal cycle.** The disturbance source is building
  activity: doors, footfalls, the polishing machines. It varies by an
  order of magnitude between 2 pm and 2 am. Any arm shorter than 24 h
  confounds the configuration with the time of day it happened to be
  tested, and 8 h arms run back-to-back confound it maximally.

### Running it

The capture is unattended and read-only (the survey sends only the A&D
`Q` query), so this is overnight work, not bench time. Take it in **hourly
chunks** rather than one 24 h call — a USB hiccup then costs an hour
instead of a day, and the per-hour counts are what the diurnal check
needs:

```bash
ARM=A-granite-direct
mkdir -p runs/$ARM
for h in $(seq -w 0 23); do
  python scripts/balance_environment_survey.py --settle 3600 \
      --csv runs/$ARM/$h.csv
done
```

Then, from the repo root:

```bash
python scripts/step_event_rate.py \
    runs/A0-bare-deck runs/A-granite-direct \
    runs/C-granite-mat runs/B-granite-pads runs/A2-granite-direct-repeat
```

It pools every CSV per arm, counts step events with the *same* detector
the survey uses (>10 mg in one poll, ringing inside 2 s coalesced), and
compares each arm to the reference with the **exact conditional Poisson
test** — the binomial test on how the pooled count splits. That exactness
matters: at n = 3 events a normal approximation is not merely imprecise,
it is wrong, and these arms will genuinely produce single-digit counts if
anything works.

### Keep these constant, or the comparison means nothing

- **Nothing else changes between arms.** Same pan, same breeze break
  state, same sash height, same nothing-else-on-the-deck. Write down
  anything that did change.
- **Let each rebuild sit 12 h before the capture starts.** A cold 30 kg
  stone makes drift *worse* for hours while it equilibrates, and elastomer
  takes a set over its first hours under load. Both settle; neither
  settles instantly.
- **Re-level after every rebuild**, and record the bubble position *at the
  start and the end* of each arm. This is nearly free and it is the most
  direct evidence available for or against the tilt-latching mechanism: if
  the bubble has migrated after 24 h on pads but not after 24 h on bare
  granite, the creep-tilt story is caught in the act.
- **Arm B only — caliper all four pads** at 0 h, 1 h and 24 h, free height
  vs loaded. δ ≈ 2 mm confirms f₀ ≈ 11 Hz as designed; δ < 1 mm means the
  pads are too big and the stack is effectively rigid. Growth in the
  *corner-to-corner spread* is exactly the differential-creep failure mode
  Edison predicts — measure it rather than argue about it.
- **Arm C — record the coverage fraction.** A 12 × 12 sheet under a
  12 × 18 plate leaves ~3 in overhanging each end; centre it under the
  balance's own footprint and note it, because "full sheet" means
  something different at 60 % coverage.
- Re-run the external 100 g calibration after each move (manual §8-1).
  See the note below — the rig does not yet have a suitable weight.
- **Option A rigs only** — after B, time a few doses to a stable reading.
  With the doser bridge on the same slab the tapper now excites the
  isolator mode from inside the isolated mass; a large increase in settle
  time is a real cost even if the step-event count improves.

### Two gaps to close before this can run

1. **`scripts/balance_environment_survey.py` is not in this repository.**
   It exists only at `~/powder-doser/scripts/` on the Pi, in a directory
   that is not a git checkout — no remote, no history, one SD card. The
   instrument for this entire experiment is currently one power failure
   away from gone. It should be committed (with `balance_zero.py`, which
   it imports) before anything else here happens.
2. **No calibration weight.** Step 5 of every rebuild wants an OIML/ASTM
   class E2 or F1 100 g weight and the rig does not have one. One likely
   shipped with the balance — worth looking in the case before buying.

## Commissioning a single install

Use this when installing without running the comparison — e.g. once an arm
has won.

1. Install, then **let it sit overnight before judging.** A cold ~30 kg
   stone is a thermal mass; it will make drift *worse* for the first
   several hours while it equilibrates with the hood. Elastomer pads also
   take a set over their first hours under load, so this settles both.
2. **Measure the pads** with calipers, free height vs loaded height, and
   record δ per corner. This is the only direct check that the isolator is
   doing anything: δ ≈ 2 mm means f₀ ≈ 11 Hz as designed, δ < 1 mm means
   the pads are too big and the stack is nearly rigid. Corner-to-corner
   spread also flags an uneven deck.
3. Re-level the balance on the slab (leveling feet + bubble level).
4. Re-run the external 100 g calibration — manual §8-1 calls for
   calibration after the balance is moved. Still needs an OIML/ASTM
   class E2 or F1 100 g weight, which the rig does not yet have.
5. `python scripts/balance_environment_survey.py` for a go/no-go on jitter
   and creep, which a single 600 s run *can* answer. It cannot answer
   whether the step events improved — see the sizing table above — so if
   that is the question, run the comparison, not this.
6. **Option A only — re-check settle time after a tap.** With the doser
   bridge on the same slab, the tapper now excites the ~11 Hz isolator
   mode from inside the isolated mass. Time a few doses to stable reading
   against the pre-slab figure. A modest increase is the expected cost of
   the compliance; a large one, or visible oscillation in the reading,
   means the pads are too soft — cut a fresh set one size larger (they are
   $15 for sixteen).

**Success looks like:** step-event rate and amplitude down, jitter
unchanged, creep unchanged, settle-time after tapping not materially
worse.

---

## Where this note stands

Settled: granite over marble; ~25–35 kg of it; ≥ 30 mm thick; buy it local
if a fabricator answers, Grizzly G9651 otherwise. The straddle geometry
still needs a caliper on the doser bridge before any plate is ordered.

Open, and deliberately left open: whether anything belongs *between* the
stone and the deck. The shape-factor case for small pads and the
tilt-latching case against them are both in this note, unreconciled, and
the four-arm comparison is how they get reconciled. Borrow the rubber, run
the arms, and let the counts decide.
