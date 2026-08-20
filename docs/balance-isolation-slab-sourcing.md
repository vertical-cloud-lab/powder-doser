# Sourcing an isolation slab for the HR-100A balance

Buy-list and sizing note for [`#146`](https://github.com/vertical-cloud-lab/powder-doser/issues/146),
which follows point 4(d) of the environment survey in
[`#116`](https://github.com/vertical-cloud-lab/powder-doser/issues/116#issuecomment-5358891531).

Prices spot-checked 2026-08-20 and *will* drift; treat the links as the
source of truth, not the numbers.

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
better than a monolithic slab does. Two caveats: seal or bag it, because
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

- **4 × double-yellow squash balls**, one per corner — the standard cheap
  isolator, and there is a
  [printable cup/foot for them](https://www.printables.com/model/62634-anti-vibration-squash-ball-feet-for-stone-concrete).
  Under ~8 kg per corner they deflect a few mm, landing near the target.
- **Sorbothane hemispheres or pucks**, ~50–70 durometer, sized so static
  deflection is 10–20 % of thickness. Commercial anti-vibration tables
  use 7 Hz Sorbothane isolators, i.e. the same number.
- **Do not** use soft open-cell foam alone. Large deflection under a tall
  centre of gravity gives a rocking mode at 1–3 Hz — right where footfall
  energy lives — and the balance will settle slowly after every load.
- Note the flip side of the equation: **near f₀ the slab amplifies.**
  Lossy isolators (squash balls, Sorbothane) cap that peak at ~2–4×;
  steel springs would not.

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
   several hours while it equilibrates with the hood.
2. Re-level the balance on the slab (leveling feet + bubble level).
3. Re-run the external 100 g calibration — manual §8-1 calls for
   calibration after the balance is moved. Still needs an OIML/ASTM
   class E2 or F1 100 g weight, which the rig does not yet have.
4. `python scripts/balance_environment_survey.py` before and after, and
   compare against the pre-slab baseline: jitter 0.111 mg, creep
   −5.4 mg/min, 1 step event >10 mg per 10 min at +118 mg net.
   Because the room varies by an order of magnitude minute to minute,
   take several runs on each side rather than one.

**Success looks like:** step-event rate and amplitude down, jitter
unchanged, creep unchanged.
