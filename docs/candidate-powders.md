# Candidate Powders for Metal-AM Feedstock Testing

This document tracks the powders we intend to use with the
powder-doser. The previous focus on food-grade flow-surrogates has
been deprioritised — per the discussion on
[`#19`](https://github.com/vertical-cloud-lab/powder-doser/pull/19),
we are jumping straight to the metal powders we actually care about
and accepting that early bring-up will happen in ambient air rather
than under inert atmosphere.

## Target metal powders

The primary references are the fine, gas-atomised feedstocks used in
laser powder-bed fusion (LPBF):

- Silicon (Si), high-purity elemental.
- AlSi10Mg, the Al–Si–Mg casting alloy.

Beyond these two anchor materials, the broader element palette we
intend to dispense is the 15-element set used by the BYU VCL
"digital alloy lab" effort. The canonical list of those 15 elements
is maintained in the (currently private) repository
[`vertical-cloud-lab/digital-alloy-lab-private`](https://github.com/vertical-cloud-lab/digital-alloy-lab-private);
this document should be updated with the explicit list once that
repository is made public or the list is otherwise cleared for
posting here.

In the meantime, expected entries are the common LPBF/HEA palette:
Al, Si, Ti, V, Cr, Mn, Fe, Co, Ni, Cu, Zn, Zr, Nb, Mo, plus one
additional element (W, Ta, or similar) — to be confirmed against the
private repo before any procurement.

## Handling and storage

The fine atomised feedstocks above are reactive and strongly
hygroscopic:

- Al-containing powders (Al, AlSi10Mg) are flammable at fine particle
  sizes and form a passivating oxide on contact with moist air.
- Si, Ti, Zr, Nb, and Ta fines are similarly sensitive to oxidation
  and moisture pickup.

The ideal handling environment is dry powder under an inert
atmosphere (Ar glovebox). That is not available to us yet — the
current estimate is roughly one to two months until we have an inert
working volume. Until then, the operating constraint is simply
*keep the powder dry*:

- Store stock bottles in a desiccator with fresh indicating
  desiccant; log each open/close.
- Transfer in short sessions; cap bottles between operations.
- Pre-dry hoppers, lines, and any printed parts that contact powder.
- Treat the doser hardware itself as a humidity-sensitive component
  during bring-up and bag it with desiccant when idle.
- Track ambient T/RH during every run so flow behaviour can be
  correlated with humidity exposure later.

When the inert volume is online, the same powders move into the
glovebox and the desiccator workflow is retired.

## Dispensing targets — custom Al crucibles

Dispensing is into a set of small, machined aluminium crucibles
sized for the digital-alloy-lab arc-melt / homogenisation workflow.
These are an in-house item rather than a stock catalogue part, so
they need to be machined in parallel with bring-up of the doser
itself. Open items:

- Finalise crucible geometry (inner diameter, depth, wall thickness,
  registration features for the doser stage).
- Material spec — wrought Al alloy; specific grade TBD by the
  digital-alloy-lab side.
- Quantity for the first batch (enough to cover one full
  15-element sweep plus spares).
- Machining route — manual mill vs. CNC, who runs the job, expected
  lead time.

Crucible drawings, when produced, should live alongside the rest of
the mechanical CAD in this repository (see `design/cad/`).

## Earlier surrogate-powder set (deprioritised)

The food- and laboratory-grade flow surrogates trialled in the
original "identify powders to use" issue
([`vertical-cloud-lab/powder-excavator#3`](https://github.com/vertical-cloud-lab/powder-excavator/issues/3))
— glutinous (white) rice flour, brown rice flour, sodium alginate,
calcium lactate, carboxymethyl cellulose (CMC), xanthan gum, and an
equal-mass mix of all six — are *not* the working set going forward.
They remain useful as cheap, safe stand-ins for purely mechanical
debug of the doser (e.g. characterising a new auger or hopper
geometry without burning real feedstock), and short videos of each
being handled are attached to that issue for reference. They should
not, however, drive design decisions about flow behaviour for the
actual metal powders listed above.

## Open questions

- Confirm the explicit 15-element list from the digital-alloy-lab
  side and replace the placeholder above.
- Confirm crucible geometry and material grade.
- Decide on a desiccator make/model and indicating-desiccant
  refresh cadence for the bring-up period.
- Decide on PPE / housekeeping for handling fine Al powder in air
  during the pre-inert window.
