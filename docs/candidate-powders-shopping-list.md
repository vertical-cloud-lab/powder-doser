# Shopping list — food-safe surrogate powders

Per the request on
[`#19`](https://github.com/vertical-cloud-lab/powder-doser/pull/19#issuecomment-4444335961),
this is a buy-list for the six food-/lab-safe surrogate powders
originally proposed earlier in that PR thread (kept in
[`candidate-powders.md`](candidate-powders.md) under
"Earlier surrogate-powder set"). They are *not* the project's
primary feedstocks — the metal targets are still Si / AlSi10Mg /
the digital-alloy-lab palette — but the surrogates remain useful
for cheap, ambient-air bring-up of the doser hardware while we wait
on inert-atmosphere capability and the custom Al crucibles.

## Quick summary

| # | Powder                              | Pack size | Indicative unit price (USD) | Vendor (primary) |
|---|-------------------------------------|-----------|-----------------------------|------------------|
| 1 | White (glutinous) rice flour        | 24 oz     | ~$5–8                       | Bob's Red Mill (Amazon) |
| 2 | Brown rice flour                    | 24 oz     | ~$5–8                       | Bob's Red Mill (Amazon) |
| 3 | Sodium alginate (food grade)        | 50 g      | ~$10–12                     | Modernist Pantry |
| 4 | Calcium lactate (food grade)        | 8 oz      | ~$12–13                     | Cape Crystal Brands |
| 5 | Carboxymethyl cellulose (CMC)       | 8 oz      | ~$11–12                     | Cape Crystal Brands |
| 6 | Xanthan gum                         | 8 oz      | ~$12–14                     | Bob's Red Mill (Amazon / Walmart / Target) |

Indicative single-pack subtotal: **~$55–67 USD** before tax/shipping.
Prices were spot-checked on 2026-05-12 and *will* drift; treat the
links as the source of truth, not the numbers.

A seventh "even-mass mix of all six" entry from the original list
does not need to be ordered — it is made by combining equal masses
of items 1–6 in the lab.

## Validated product links

### 1. White (glutinous) rice flour — Bob's Red Mill, 24 oz

- Standard (gluten-free) line: <https://www.amazon.com/Bobs-Red-Mill-Gluten-White/dp/B07V1YMGLY>
- Organic line (substitute if standard is out of stock):
  <https://www.amazon.com/Bobs-Red-Mill-Organic-White/dp/B07YQL5DDW>
- Typical Amazon price: ~$5–8 per 24 oz bag (fluctuates).

Rationale: baseline "easy-flow", near-spherical-ish starch granule
powder. One bag is plenty for early bring-up.

### 2. Brown rice flour — Bob's Red Mill, 24 oz

- Standard: <https://www.amazon.com/Bobs-Red-Mill-Brown-Flour/dp/B000KEJQ1A/>
- Organic (substitute): <https://www.amazon.com/Bobs-Red-Mill-Organic-Brown/dp/B0013J0GUY/>
- Typical Amazon price: ~$5–8 per 24 oz bag.

Rationale: similar size band to the white rice flour but with bran
fragments — introduces shape/size heterogeneity.

### 3. Sodium alginate — Modernist Pantry, 50 g (food-grade, E401)

- Vendor product page:
  <https://modernistpantry.com/products/sodium-alginate.html>
- Typical Modernist Pantry price: ~$11.99 / 50 g jar; 400 g
  "Kitchen Alchemy" size also listed on the same page if a larger
  order is preferred.
- Amazon alternative (different brand, larger pack):
  Pure Sodium Alginate, Molecular Gastronomy / Non-GMO,
  <https://www.amazon.com/Alginate-Molecular-Gastronomy-Non-GMO-Certified/dp/B013GARWFQ>

Rationale: fine, slightly hygroscopic biopolymer — moderate-cohesion
data point. 50 g is more than enough for surrogate testing; only
order the larger size if we plan to repeat-fill the hopper many
times.

### 4. Calcium lactate — Cape Crystal Brands, 8 oz (food grade)

- Vendor product page:
  <https://www.capecrystalbrands.com/products/calcium-lactate>
- Typical price: ~$12.95 / 8 oz pouch.
- Amazon alternative (different brand):
  Pure Calcium Lactate (Molecular Gastronomy),
  <https://www.amazon.com/Calcium-Lactate-Molecular-Gastronomy-Certified/dp/B00FT3CT66>

Rationale: crystalline / more angular particles — a useful contrast
to the rounded starch granules.

### 5. Carboxymethyl cellulose (CMC / "cellulose gum") — Cape Crystal Brands, 8 oz

- Vendor product page:
  <https://www.capecrystalbrands.com/products/carboxymethyl-cellulose-cmc-powder>
- Typical price: ~$11.95 / 8 oz pouch.
- Vendor offers 2 oz / 8 oz / 16 oz pack sizes; 8 oz is the
  recommended starting quantity.

Rationale: fibrous, strongly hygroscopic cellulose derivative —
highly cohesive, poor-flow regime endpoint. Will pick up moisture
fast in ambient air; store sealed with desiccant.

### 6. Xanthan gum — Bob's Red Mill, 8 oz

- Amazon: <https://www.amazon.com/Bobs-Red-Mill-Gluten-Xanthan/dp/B078T45FYD>
- Walmart: typically ~$13.98 / 8 oz pouch.
- Target: typically ~$13.39 / 8 oz pouch.

Rationale: very fine, very cohesive biopolymer — the
extreme-cohesion endpoint of the original surrogate set.

## Notes for ordering

- All six are food-grade and shippable to a normal lab address; no
  hazardous-materials handling is required.
- Quantities above are *one* of the smallest sensible retail pack
  size per powder. That is enough for repeated bench tests and the
  even-mass mix; do not bulk-order until we have evidence the doser
  geometry is stable.
- All six are hygroscopic to varying degrees (CMC and xanthan
  worst). On arrival, decant working portions into sealed jars with
  an indicating-desiccant sachet, and keep the original retail
  packaging double-bagged with desiccant in the same desiccator
  workflow described in
  [`candidate-powders.md`](candidate-powders.md#handling-and-storage).
- @swcharles — if the items / pack sizes look right, please go
  ahead and place the order; otherwise flag substitutions here
  before purchasing.

## Disclaimer on prices and links

Prices and stock state at retailers like Amazon, Walmart, and
Target change frequently. The numbers above were spot-checked on
**2026-05-12** and are intended only as ballpark figures for
budgeting. Always re-verify the live price on the linked product
page before placing the order, and substitute an equivalent
food-grade SKU from a different vendor if the linked one is out of
stock.
