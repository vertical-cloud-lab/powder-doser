# Edison queries (2026-07-16 batch) — issue #117

Two Edison Scientific (PaperQA3) literature queries submitted 2026-07-16 and fetched 2026-07-17,
following up on powder-dosing discussions with the University of Utah (issue #117).

| Query | Task ID | Report | Table artifact |
|---|---|---|---|
| PLA compatibility with AIBN / Grubbs G2 / NaCN / NaCl + alternative printable materials & coatings | `5a322274-ea6a-44b9-af7d-3c67086b06e0` | [pla-compatibility.md](pla-compatibility.md) | [Material decision table](pla-compatibility-material-decision-table.md) |
| Cheap/benign surrogate powders matching G2, AIBN, and NaCN handling behavior | `d885ec2b-0f36-411e-9133-4a40e6878537` | [surrogate-powders.md](surrogate-powders.md) | [Surrogate candidate table](surrogate-powder-candidate-table.md) |

Supporting files:

- [task-ids-2026-07-16.json](task-ids-2026-07-16.json) — task IDs as submitted
- [surrogate-powders-query.md](surrogate-powders-query.md) — full query text for the surrogate query
- `*-task-metadata.json` — run status, duration, and usage stats per task

## Headline conclusions

- **PLA is not chemically reactive with any of the four powders** (per retrieved evidence), but it is
  operationally suboptimal for Grubbs G2 (moisture retention vs. a water-sensitive Ru catalyst) and
  NaCN (layer lines trap toxic residue; hard-to-validate decontamination).
- **Parylene C coating is the most evidence-supported upgrade path** for a printed powder path:
  chemically inert, moisture/gas barrier, established on 3D-printed substrates. PTFE sprays,
  silicone, and epoxy sealants lack direct literature support and would need in-house qualification.
- If reprinting, **polypropylene > PETG > PLA/nylon** for this service (engineering judgement);
  avoid uncoated SLA resin in the powder path due to leachables.
- **Surrogates:** lactose (worst-case cohesive stand-in, Hausner ~1.83, AoR ~50°) and maize starch
  for G2's cohesion; Avicel PH-102 MCC for tribocharging tests (measured Δq vs. steel) and as an
  AIBN-like mid-cohesion powder; NaCl with humidity cycling across its deliquescence point as the
  NaCN caking surrogate. Bracket calibration: free-flowing MCC (AoR ~28°) → PH-102 (~43°) →
  lactose/starch (~50°).
