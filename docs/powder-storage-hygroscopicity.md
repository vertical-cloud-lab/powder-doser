# Powder storage: hygroscopicity, caking, and why the fume hood is not a dry box

Written 2026-09-10, the day barium chloride arched over the auger intake
after three weeks loaded in the fume-hood airstream
([run notes](battery-runs/2026-09-10-barium-chloride-blocks-gh-no-feed.md)).
This doc answers the operator questions that followed: *which of our
powders are hygroscopic, and is keeping them in a fume hood enough?*

## Three ways moisture ruins a powder here

Moisture damage is not one mechanism, and the fix differs by class:

1. **Bulk uptake (the gums and flours).** Polysaccharides and starches
   equilibrate with room air at roughly 8–15 % water by mass and track
   the room's relative humidity up and down. The powder does not
   visibly change; its cohesion, feed factor, and *actual delivered
   mass per gram of solids* do. This shifts measurements rather than
   killing runs.
2. **Caking of soluble crystalline salts (what killed barium
   chloride).** A soluble salt does not need to deliquesce to cake —
   ordinary **humidity cycling** is enough. Each RH upswing dissolves a
   microscopic film at grain contacts; each downswing recrystallizes it
   into solid salt bridges. Weeks of daily cycles weld the bed into a
   cohesive block that arches over the auger intake. This kills runs
   outright (`arching-no-feed`), and it is the failure mode a fume hood
   *accelerates*, because the hood ensures maximal exchange with
   unconditioned room air.
3. **Surface adsorption on metal powders.** Metals take up no bulk
   water, but additive-manufacturing practice treats moisture as a
   first-order enemy anyway: an adsorbed film degrades flowability and
   spreadability, grows the surface oxide/hydroxide over time, causes
   hydrogen porosity if the powder is later melted, and damp aluminium
   powder slowly evolves hydrogen. Storage consequence: sealed and dry,
   ideally the original bottle.

## Ranking of the campaign powders

| Powder | Class | Hygroscopic? | Dominant moisture risk | Storage priority |
|---|---|---|---|---|
| Xanthan gum | polysaccharide | **Yes — strongly** | bulk uptake, clumping | **seal + desiccate** |
| Sodium alginate | polysaccharide salt | **Yes — strongly** | bulk uptake, clumping | **seal + desiccate** |
| Carboxymethyl cellulose | cellulose ether | **Yes — strongly** | bulk uptake, clumping | **seal + desiccate** |
| Sodium sulfate | soluble salt | **Yes if anhydrous** — anhydrous Na₂SO₄ is literally a lab drying agent; below 32.4 °C it wants to hydrate toward the decahydrate (up to ~127 % mass gain at full hydration) | caking + mass gain | **seal + desiccate** |
| Barium chloride | soluble salt (dihydrate as supplied) | Moderately — the dihydrate is stable at ordinary RH, but it cakes readily via cycling; anhydrous BaCl₂ actively rehydrates | **caking (proven here, 2026-09-10)** | **seal + desiccate; break clumps before loading** |
| Fumed silica | SiO₂, ~200 m²/g surface | Surface-adsorbs strongly (hydrophilic grades) | flow/agent behaviour degrades | **seal + desiccate** |
| Calcium lactate | organic salt, usually pentahydrate | Moderately (anhydrous form strongly; check the label) | clumping | seal |
| White rice flour | starch | Moderately (equilibrium ~12–14 % water) | cohesion shift with RH history | seal |
| Brown rice flour | starch + bran lipids | Moderately (plus a separate rancidity clock on the bran oils) | cohesion shift | seal, keep cool |
| Salt (NaCl) | soluble salt | Barely — deliquesces only above ~75 % RH; cakes slowly via cycling | mild caking | seal is enough |
| AlSi10Mg | metal alloy (AM powder) | **No bulk uptake — but moisture-sensitive** per AM practice (flowability, oxide growth, H₂ porosity if melted, slow H₂ evolution when damp) | surface film | **seal + dry; original bottle preferred** |
| Silicon (−110/+200 and −325) | metalloid, passivated | No | none at bench timescales | seal for dust containment only |

The empirical anchor: after the *same* three weeks in the *same* hood,
barium chloride caked solid while salt dosed normally on 2026-09-03 and
the sodium sulfate column fed at the campaign record on 2026-09-10
(fresh-load caveat: the sulfate auger may have been topped up in the
interim, so treat that last point as suggestive rather than controlled).
Susceptibility is a property of the powder, which is why the table is
worth having.

## Is the fume hood enough? No — it is the opposite of a dry box

A fume hood is an **airflow machine**: it pulls unconditioned room air
across the work surface continuously. Nothing inside it is ever drier
than the room; the contents just equilibrate with ambient humidity
*faster*, and they get the full daily RH cycle that drives salt caking
(mechanism 2). Three weeks in that airstream is exactly what caked the
barium chloride. The hood is the right place to *handle* toxic and
respirable powders; it does nothing for *storage*, and storing things in
a working hood is discouraged anyway (clutter degrades containment).

What actually controls moisture, cheapest first:

1. **The threaded storage augers, capped and taped, are already sealed
   vessels** — that is their design intent. Keep the caps on and the
   delivery-end tape on between sessions, and minimise open time
   (consistent with the standing rule about not mixing long-exposed and
   sealed powder).
2. **An airtight tote + indicating silica gel + a cheap hygrometer
   card** makes a dry box that houses every auger at once. Recharge or
   swap the gel when the indicator turns. This is the "house many this
   way" solution: one bin, all powders, a few dollars.
3. A **desiccator cabinet or electronic dry cabinet** (~20–30 % RH
   setpoint) is the turnkey version if the tote gets tiresome.
4. **Metal powders**: original sealed bottles where possible; transfer
   to the auger close to the run. Long-term bulk storage under inert
   gas is the AM-lab gold standard but is overkill at our gram
   quantities.
5. **Toxics (barium chloride)**: where they *live* is an EHS/policy
   question, not a chemistry one — a sealed, desiccated container works
   in whatever cabinet EHS designates. Sealing does not conflict with
   safety storage.

Two Utah-specific notes: ambient RH here is low much of the year, which
is why we got away with open-ish storage this long — sealed storage is
cheap insurance rather than urgent remediation for most of the set (the
gums and the two cake-prone salts are the exceptions worth doing now).
And dry air makes electrostatic cling on insulating powders *worse*, so
"drier is always better" has a limit; sealed-at-ambient is the sweet
spot for the food-safe set.

## If we ever want numbers instead of a table

The bench can measure this directly: ~2 g of powder spread in the
vessel, 10–15 min of mass-vs-time on the HR-100A in a quiet window, per
powder. Strong absorbers (the gums, anhydrous sulfate) gain visibly at
0.1 mg resolution; silicon and salt stay flat. Worth doing as a
mini-block someday if storage policy needs defending with data — ask
and it can be scripted like the environment survey.
