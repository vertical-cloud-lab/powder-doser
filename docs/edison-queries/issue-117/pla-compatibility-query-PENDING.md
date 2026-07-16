# PENDING Edison query — PLA compatibility with issue #117 powders

**Status:** NOT YET SUBMITTED. The `EDISON_PLATFORM_API_KEY` secret resolved to an
empty string in the GitHub Actions run on 2026-07-16 (run 29513737970), so the query
below could not be submitted. Once the secret is restored, a follow-up `@claude`
comment should submit this query (low-effort `LITERATURE` job), poll in the
foreground per CLAUDE.md, fetch all artifacts, and commit the report alongside this
file (then delete/replace this PENDING file).

Requested in: https://github.com/vertical-cloud-lab/powder-doser/issues/117
(trigger comment by @sgbaird, 2026-07-16)

## Query text

We operate an open-source auger-based powder microdoser whose powder-contacting parts
(auger screw and surrounding tube/hopper) are currently FDM 3D-printed in PLA. We plan to dose the
following powders at milligram scale (0.1-10 mg doses): (1) AIBN, 2,2'-azobisisobutyronitrile,
CAS 78-67-1; (2) Grubbs 2nd-generation ruthenium metathesis catalyst, CAS 246047-72-3 (dosing inside
an inert-atmosphere glovebox); (3) sodium cyanide, CAS 143-33-9; (4) sodium chloride as a benign test
powder.

Questions:

1. Is PLA chemically compatible with each of these powders in dry solid-solid contact? Any risks of
   reaction, catalyst deactivation/poisoning (e.g., G2 by PLA ester groups or residual moisture),
   contamination of the dosed powder by polymer wear debris, or degradation of the PLA?
2. Tribocharging: how do PLA and other printable polymers rank triboelectrically against these
   powders, and what does that imply for static adhesion/clumping in a very dry glovebox atmosphere?
3. If PLA is a poor choice, what alternative materials that can still be 3D printed would be better -
   FDM filaments (e.g., PETG, nylon, polypropylene, conductive/ESD-safe filaments, carbon-filled) or
   SLA/DLP resin printing (standard, engineering, or ceramic-filled resins)? Consider chemical
   inertness, low surface energy, low tribocharging, smooth achievable surface finish, and glovebox
   compatibility (low outgassing, low moisture uptake).
4. Are there smooth inner coatings that could be applied to a printed auger tube - e.g., parylene,
   PTFE spray coatings, silicone or fluoropolymer conformal coatings, epoxy sealing - that improve
   powder flow, reduce static, and improve chemical compatibility? How well do they adhere to PLA or
   resin prints, and are they safe with an organic radical initiator (AIBN) and a Ru carbene catalyst?
5. Any other material-selection considerations for dosing these specific powders (e.g., AIBN thermal
   sensitivity vs printed-part friction heating, NaCN containment and cleanability, humidity effects).

Provide practical recommendations with citations where possible.
