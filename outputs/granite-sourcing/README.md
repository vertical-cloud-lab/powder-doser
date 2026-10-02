# Granite slab sourcing survey — 2026-08-22

Raw data behind the "Where to buy it" tables in
[`docs/balance-isolation-slab-sourcing.md`](../../docs/balance-isolation-slab-sourcing.md).

| file | what it is |
|---|---|
| `survey-2026-08-22.json` | canonical run of `scripts/granite_sourcing_survey.py all` |
| `raw-survey.json` | the five exploratory passes that preceded it, kept for the negative results (which vendors block, and how) |

Collected from the powder-doser Pi over Tailscale so requests came from the
BYU campus IP rather than a GitHub Actions datacenter block. Unauthenticated
public pages only, ~1 request per 2.5 s, no logins and no carts.

## Headline results

* **Grizzly**, verified in stock, prices unchanged from the 2026-08-20 check:
  G9649 $39.95 (26 lb), **G9651 $69.95**, G9653 $79.95, G9654 $99.95. Shipping
  is extra and not scrapeable — see the doc.
* **Shars** grade A 12 × 18 is $123.45, grade AA $114.39 — finer grades than
  this application needs, and dearer.
* **Harbor Freight no longer sells granite surface plates.** Its own search
  says "Sorry, no items found". Any older advice to grab one there is stale.
* **Utah County fabricators**: eight sites reachable, addresses and phone
  numbers extracted from the businesses' own pages. Rock Solid Granite (Orem)
  is the only one publishing a searchable remnant inventory.
* **KSL Classifieds**: nothing suitably sized statewide today. The one
  precision plate listed is a Starrett 36 × 60 grade A in Provo at $4,000.

## Which vendors block automation, as of this date

Useful to know before re-running: Home Depot, Lowe's and Harbor Freight
(PerimeterX) refuse every request including their own JSON APIs; Shars and MSC
sit behind AWS WAF and 202 on *search* while serving *product* pages fine;
Grizzly, Zoro, Amazon, Walmart, KSL and all the small fabricator sites are
open. DuckDuckGo HTML returns 202 and Mojeek serves a captcha, so local
business discovery was done with a search API from the runner instead.

One non-obvious failure mode: the Pi's `requests` has no brotli decoder, so
`Accept-Encoding: br` yields HTTP 200 full of binary garbage and every price
regex silently matches nothing. It reads as a parser bug. It is not.
