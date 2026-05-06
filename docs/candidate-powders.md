# Candidate Powders for Metal-AM Feedstock Surrogates

This document records the set of characteristic powders that have been
identified for use with the powder-excavator as low-cost, low-hazard
surrogates for the fine powders used in metal additive manufacturing
(AM) -- e.g. silicon (Si) and the aluminium--silicon casting alloy
AlSi10Mg, both of which are commonly processed by laser powder-bed
fusion (LPBF).

## Why surrogate powders?

Production metal-AM feedstocks (Si, AlSi10Mg, Ti--6Al--4V,
Inconel 718, ...) are typically gas-atomised, near-spherical particles
in the 15--45 µm range. They are expensive, can be reactive
(especially the fine Al- and Ti-based powders), and require inert
handling. For early bring-up, mechanical characterisation, and
demonstration of the powder-excavator hardware we instead want
powders that

* are food- or laboratory-grade and safe to handle in air,
* are inexpensive and widely available,
* span a useful range of particle sizes, shapes, cohesivities, and
  flow behaviours so that the excavator's response can be evaluated
  against more than one "class" of powder, and
* together bracket the rheology of real metal-AM feedstocks rather
  than match any single property exactly.

## Selected candidates

The following six powders were trialled in the issue thread that
motivated this list (vertical-cloud-lab/powder-excavator#3, comment by
@sgbaird) and are adopted as the initial reference set. A seventh
"sample" -- an even mix of all six -- was also trialled and is kept
as a deliberately heterogeneous control.

| # | Powder                              | Typical role / why it was chosen                                                                       |
|---|-------------------------------------|--------------------------------------------------------------------------------------------------------|
| 1 | White (glutinous) rice flour        | Free-flowing, near-spherical-ish starch granules; baseline "easy-flow" powder.                         |
| 2 | Brown rice flour                    | Similar size range to white rice flour but with bran fragments -- introduces shape/size heterogeneity. |
| 3 | Sodium alginate                     | Fine, slightly hygroscopic biopolymer powder; moderately cohesive.                                     |
| 4 | Calcium lactate                     | Crystalline, more angular particles; contrasts with the rounded starch granules.                       |
| 5 | Carboxymethyl cellulose (CMC)       | Fibrous, strongly hygroscopic cellulose derivative; highly cohesive, poor-flow regime.                 |
| 6 | Xanthan gum                         | Very fine, very cohesive biopolymer; an extreme-cohesion endpoint.                                     |
| 7 | Equal-mass mix of powders 1--6      | Heterogeneous mixture used as a stress test for segregation and flow behaviour.                        |

The set is intentionally ordered roughly from "free-flowing" (rice
flours) to "highly cohesive" (xanthan gum). Together they span the
range of flowability that gas-atomised metal-AM powders fall into in
practice (typically Geldart Group A--C behaviour at the relevant
particle sizes), without requiring any hazardous metal feedstock.

## Mapping to metal-AM powders

| Surrogate behaviour                         | Closest metal-AM analogue                                              |
|---------------------------------------------|------------------------------------------------------------------------|
| Free-flowing rounded granules (rice flours) | Well-atomised, sieved Si or AlSi10Mg in the 20--45 µm LPBF cut.        |
| Angular crystalline (calcium lactate)       | Recycled / partially sintered AlSi10Mg with irregular satellites.      |
| Fine cohesive biopolymers (CMC, xanthan)    | Sub-15 µm fines and humidity-affected Si / AlSi10Mg with poor spread.  |

These mappings are qualitative -- the surrogates are *not* intended
to reproduce the density, thermal, or optical properties of the metal
powders, only to provide a representative range of flow and packing
behaviours for the excavator to interact with.

## Reference videos

Short videos of each powder being handled by the excavator are
attached to issue
[vertical-cloud-lab/powder-excavator#3](https://github.com/vertical-cloud-lab/powder-excavator/issues/3).

## Future additions

If/when additional surrogates are required they should be added to
the table above together with the rationale for inclusion (size,
shape, cohesivity, or other property they help cover). Candidates
worth considering include cornstarch (very fine, cohesive),
granulated sugar (large, free-flowing crystalline), and glass beads
of a controlled size distribution (a true near-spherical reference).
