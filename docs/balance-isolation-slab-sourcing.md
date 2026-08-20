# Sourcing an isolation slab for the HR-100A balance

Buy-list and sizing note for [`#146`](https://github.com/vertical-cloud-lab/powder-doser/issues/146),
which follows point 4(d) of the environment survey in
[`#116`](https://github.com/vertical-cloud-lab/powder-doser/issues/116#issuecomment-5358891531).

Prices spot-checked 2026-08-20 and *will* drift; treat the links as the
source of truth, not the numbers.

**The whole buy, if you only read one line:** a
[Grizzly G9651](https://www.grizzly.com/products/grizzly-12-x-18-x-3-granite-surface-plate-no-ledge/g9651)
12 × 18 × 3 in granite surface plate ($69.95, ~29 kg) standing on four
7/8 in squares cut from one
[McMaster 8514K315](https://www.mcmaster.com/8514K315/) 4 × 4 × 1/2 in
sheet of 70 Shore OO super-cushioning polyurethane ($15.04) — **~$85
total**, against $1,575 for the factory anti-vibration table. Granite, not
marble; small pads, not a full sheet. Reasons for each of those below.

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

- Local fabricators — search "granite remnants" plus your city; many
  advertise [free leftovers](https://www.factoryplaza.com/free-remnants-granite-marble-quartz-leftover/)
- [RemnantSwap](https://www.remnantswap.com/) — remnant marketplace
- Habitat for Humanity ReStore
- Monument / headstone shops — granite offcuts, cheap by the piece

Ask specifically for a **sink cutout** or a **3 cm remnant**, and ask
them to flat-grind or at least chamfer the sawn edges. Trade-off: edges
may be raw, and the faces are not parallel to any spec (fine — the
balance has leveling feet and a bubble level).

### 2. Machinist granite surface plate — $40–100 ⭐ recommended buy

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

Also stocked by Shars, Penn Tool, Amazon and (usually cheaper, if a store
is nearby and has stock) Harbor Freight.

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

- **The recommended isolator is four small pads of highly damped
  polyurethane** — part number, price and pad sizing in the next section.
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

## The rubber layer — what to buy

**Buy [McMaster 8514K315](https://www.mcmaster.com/8514K315/) — Super-Cushioning
Polyurethane Rubber Sheet, 4" × 4" × 1/2" thick, 70 Shore OO, $15.04,
next-day** — and cut four ~7/8" squares out of it. One 4 × 4 in piece
yields sixteen, so the sweep and the spares come out of the same $15.

Before ordering, check the bin: this is the same material and thickness
the drop-tower program in
[`tensegrity-optimization`](https://github.com/vertical-cloud-lab/tensegrity-optimization)
already bought ([#88](https://github.com/vertical-cloud-lab/tensegrity-optimization/issues/88),
[PR #86](https://github.com/vertical-cloud-lab/tensegrity-optimization/pull/86)),
so **offcuts of the existing 1/2 in sheet make these pads for free.** Four
7/8 in squares is 3 in² — a rounding error against a 12 × 12 in sheet.

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
| **7/8"** | **17 %** | **2.1 mm** | **11 Hz** | **recommended** |
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

## Commissioning

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
5. `python scripts/balance_environment_survey.py` before and after, and
   compare against the pre-slab baseline: jitter 0.111 mg, creep
   −5.4 mg/min, 1 step event >10 mg per 10 min at +118 mg net.
   Because the room varies by an order of magnitude minute to minute,
   take several runs on each side rather than one.
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
