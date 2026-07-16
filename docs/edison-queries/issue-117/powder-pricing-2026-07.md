# Powder pricing snapshot — issue #117 (July 2026)

Web-sourced list prices (USD, small research quantities) for the powders discussed in
issue #117, gathered 2026-07-16. Institutional pricing is often lower; Sigma-Aldrich
hides prices behind login so third-party list prices are used where needed.

| Powder | CAS | Typical price | Per-gram | Sources |
|---|---|---|---|---|
| AIBN (2,2'-azobisisobutyronitrile) | 78-67-1 | $42–65 / 25 g; $89 / 100 g | ~$1–4/g | Matrix Scientific $42/25 g and $89/100 g (via ChemicalBook); P212121 $65/25 g; Chem-Impex $100/25 g |
| Grubbs catalyst, 2nd gen (G2) | 246047-72-3 | $62 / 100 mg; $220 / 1 g (Chem-Impex); $26–73 / 1 g (research suppliers: aablocks, AChemBlock, AK Scientific) | ~$25–225/g (Sigma typically higher) | Chem-Impex catalog; ChemicalBook price aggregator |
| Sodium cyanide | 143-33-9 | $144 / 25 g; $229 / 125 g; $380 / 500 g (Spectrum ACS) | ~$0.8–6/g | Lab Depot / Spectrum Chemical S1260; regulated item — quote/qualification usually required |
| Sodium chloride (test filler) | 7647-14-5 | ACS grade ~$30–60 / 500 g; food grade pennies | <$0.1/g | typical Fisher/Sigma catalog range (approximate) |

## Cost-per-dose and auger-loading implications

- At the 0.5–3 mg doses Phillip needs, even G2 at a conservative $225/g costs **< $0.70
  per dose**. Reagent cost per dispense is negligible for all four powders.
- The real cost driver is **hold-up volume**: powder loaded into the auger that isn't
  dispensed. A full ~100 mL auger of G2 (bulk density very roughly 0.5–0.7 g/cm³ →
  ~50–70 g) would tie up **$1.3k–16k** of catalyst depending on supplier. AIBN or NaCN
  at the same volume is only ~$50–400, and NaCl is negligible.
- This supports the reduced-inner-volume auger idea (thicker tube wall, same outer
  auger geometry) for expensive/limited powders: loading G2 a few hundred mg at a time
  (~$5–70) keeps at-risk inventory trivial.
