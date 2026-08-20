You are adversarially reviewing a vibration-isolation design calculation for
a laboratory balance. Your job is to REFUTE the claims below wherever they
can be refuted, not to agree with them. For each claim state one of:
CORRECT / CORRECT-BUT-FOR-THE-WRONG-REASON / OVERSTATED / WRONG, give the
corrected number or form, and say whether the correction changes the
practical recommendation.

## The physical setup

A 12 x 18 x 3 in granite surface plate (Grizzly G9651, ~29 kg) sits on the
epoxy-resin deck of a chemical fume hood. On top of it sits an A&D HR-100A
analytical balance (198 W x 294 D x 315 H mm, 3.5 kg, 0.1 mg display
resolution, 100 g capacity). Total sprung mass ~32.5 kg. In one variant a
small 3D-printed powder-doser bridge with a tapper solenoid also sits on
the slab, so a disturbance source is INSIDE the isolated mass.

A 600 s bare-pan environment survey of the current (no-slab) installation
measured three things:
  * sample-to-sample jitter 0.111 mg -- at/below the 0.1 mg display
    resolution, i.e. nothing to win;
  * zero drift -5.4 mg/min -- thermal + load-cell creep, internal;
  * discrete mechanical STEP EVENTS: roughly 1 per 10 min, ~100 mg, leaving
    a permanent offset (+118 mg net over 600 s).
Only the step events motivate the slab. The acceptance criterion is
step-event rate and amplitude, NOT peak-to-peak noise.

The proposed isolator is McMaster-Carr "super-cushioning polyurethane"
(a Sorbothane-class high-loss viscoelastic PU), 70 Shore OO, supplied as
flat sheet stock in 1/4 in (6.35 mm) and 1/2 in (12.7 mm) thicknesses. The
design note assumes E ~ 0.7 MPa (70 Shore OO ~ 20-25 Shore A) and
tan delta ~ 0.5, and admits E is a +/-50% estimate.

## The claims to attack

**CLAIM 1 -- shape factor makes a full sheet useless.**
Using effective compression modulus E_c = E(1 + 2 S^2) with shape factor
S = loaded area / force-free (bulgeable) area, and for a square pad of side
a and thickness t, S = a/(4t):
  * full-area 305 x 457 x 6.35 mm sheet: S = 14.4, E_c = 290 MPa, stress
    325 N / 139385 mm^2 = 0.0023 MPa, strain 8e-6, deflection 5.1e-5 mm --
    i.e. effectively RIGID, no isolation at all;
  * four 22.2 x 22.2 x 12.7 mm pads (7/8 in squares): S = 0.437,
    E_c = 0.97 MPa, stress 80 N / 493 mm^2 = 0.162 MPa, strain 16.8%,
    deflection 2.13 mm.
Conclusion drawn: the SAME rubber is ~40,000x more compliant as four small
pads than as a full sheet, even though the sheet is the thicker pile of it;
"the sheet is a gasket, not a spring."
Attack: is E(1+2S^2) the right form? Gent & Lindley give E_c = E(1+2kS^2)
with a hardness-dependent k (~0.93 at 30 IRHD falling to ~0.54 at 75 IRHD) --
which k applies to a ~20 Shore A material, and does it matter? Does the
incompressible-rubber assumption break at S ~ 14, where the bulk modulus
correction 1/E_c* = 1/E_c + 1/K (K ~ 1-2 GPa) should cap E_c? Recompute the
sheet deflection with the correction. Does the qualitative conclusion
survive, and is the 40,000x ratio defensible or is it an artifact of an
extrapolated formula?

**CLAIM 2 -- bonded vs. unbonded interfaces.**
Gent-Lindley shape-factor stiffening is derived for rubber BONDED to rigid
platens. These pads are unbonded: granite resting on rubber resting on an
epoxy deck, held only by friction (rubber-on-stone, mu ~ 1). How much of the
stiffening survives at an unbonded interface at S = 0.44 and at S = 14? Is
the error in the same direction for both? Does surface roughness / partial
real contact area make the "full sheet is rigid" claim wrong in practice
(i.e. is the initial compliance of an unbonded sheet dominated by asperity
flattening rather than bulk compression, and does that matter for
steady-state vibration transmission vs. for a transient step)?

**CLAIM 3 -- inferring f0 from static deflection.**
The note sizes the isolator with f0 [Hz] ~ 15.76 / sqrt(delta [mm]) and
reports f0 ~ 11 Hz at delta = 2.1 mm. That identity assumes dynamic
stiffness equals static stiffness. For a high-loss viscoelastic PU with
tan delta ~ 0.5, what is the dynamic-to-static stiffness ratio at 10-100 Hz?
Sorbothane's own literature warns against static-deflection sizing. If the
ratio is 2-5x, the true f0 is sqrt(2) to sqrt(5) higher -- 15-24 Hz, not
11 Hz. Does that invalidate the pad sizing, and if so what pad geometry (or
what material) actually lands f0 where it needs to be? Also: is the constant
15.76 itself right (it is 1/(2*pi) * sqrt(g), g = 9810 mm/s^2)?

**CLAIM 4 -- is compliance even the right lever here?**
An isolator amplifies at f0 and does nothing below it. If the step events
come from door slams, footfalls, hood-sash motion and HVAC transmitted
through the building floor into the hood deck, where does that energy
actually sit spectrally? Published footfall fundamentals are ~1.5-2.5 Hz
with harmonics to ~10-20 Hz; door slams and equipment transients are
usually quoted at 10-60 Hz. If a meaningful fraction of the disturbance
energy sits at or below ~11 Hz, does inserting an 11 Hz isolator make the
balance WORSE than a rigid massive slab (transmissibility ~ 1 everywhere)?
Is the note's premise "mass alone does not help against base motion,
compliance is what makes the low-pass filter" correct? Separately: does
mass-loading a compliant fume-hood deck panel reduce the deck's own local
response (lowering its resonance and its broadband amplitude), so that mass
helps by a route that has nothing to do with the isolator? What do
generic-vibration-criteria (VC-A..VC-E) curves and metrology-lab guidance
say an analytical balance actually needs?

**CLAIM 5 -- the modes the note does not optimise.**
Shear stiffness is NOT shape-factor stiffened: k_h = G*A/t. Four 7/8 in
pads of G ~ E/3 ~ 0.23 MPa give k_h ~ 3.6e4 N/m and a horizontal mode near
5 Hz -- lower than the vertical mode and closer to footfall energy. There is
also a rocking mode set by pad spacing and the elevated CG of a 315 mm-tall
balance on a slab. For a precision balance, TILT is the sensitive DOF (it
redistributes load on the pan) and is exactly what produces a discrete step
offset. Are the horizontal and rocking modes the dominant practical problem,
and does optimising the vertical mode alone (the note's approach) therefore
solve the wrong problem? Would a full sheet, or wider-spaced/larger pads,
be better precisely because they raise rocking and horizontal stiffness?

**CLAIM 6 -- the actual recommendation.**
Given everything above, which is right for this application, where the
acceptance test is "fewer ~100 mg transient step offsets" and jitter is
already below the display resolution:
  (a) four small (7/8 in) high-loss PU pads, as the note recommends;
  (b) a full-area thin sheet;
  (c) no elastomer -- granite direct on the deck;
  (d) a few LARGER pads run at low strain (higher f0, lower rocking risk);
  (e) something else -- commercial moulded/bonded isolators, air mounts,
      double-yellow squash balls, a constrained-layer damped stack.
Give a SPECIFIC quantitative recommendation (pad dimensions, count,
placement, or a part class), predict the resulting vertical / horizontal /
rocking frequencies, and state the single measurement that would falsify it.

**CLAIM 7 -- the mechanism of a step event.**
A ~100 mg PERMANENT offset on a 100 g balance is 0.1% of capacity and does
not decay. That is not what steady-state vibration transmission produces --
it looks like something latching: stiction/micro-slip in the balance's own
feet or leveling screws, a shifted draft-shield seal, powder or a fibre
falling on the pan, temperature-gradient-induced tilt, or a genuine
mechanical shock large enough to move the load cell's flexure into a
different seating. Is an isolator the right fix for a LATCHING offset at
all, or does the elastomer -- which creeps, takes a set, and can micro-slip
under a heavy stone -- introduce a NEW latching mechanism of exactly this
kind? This is the question that most threatens the whole design; treat it
seriously and quantify if you can (e.g. what tilt angle produces a 100 mg
apparent load change on this balance geometry?).


## What to return (analysis job)

Recompute everything from scratch with code -- do not take the note's
arithmetic on trust. Specifically:

1. Rebuild the shape-factor table for square pads of side 1/2, 5/8, 3/4,
   7/8, 1, 1-1/4, 1-1/2, 2, 3 in and for full 12x12 and 12x18 in sheets, at
   both 1/4 in and 1/2 in thickness, computing S, E_c (with and without the
   bulk-modulus correction, K = 1.5 GPa), static stress, strain, deflection,
   and vertical f0. Sweep E over 0.35-1.4 MPa (the stated +/-50% band) and
   report how much the recommendation moves.
2. Compute horizontal (shear) and rocking natural frequencies for each pad
   layout, taking the composite CG as: 29 kg granite slab 76 mm thick, plus
   3.5 kg balance whose CG is ~40% of its 315 mm height above the slab
   surface. Report which mode is lowest in each case.
3. Compute damped transmissibility |T(f)| for zeta corresponding to
   tan delta = 0.5 (state the zeta = tan_delta/2 assumption and check it),
   for the pad and sheet cases, at 2, 5, 10, 20, 50, 100 Hz, and integrate
   against a plausible fume-hood/lab-floor disturbance PSD. Does the pad
   option reduce total transmitted RMS, or just move it around?
4. Quantify CLAIM 7: for an EMFR balance, estimate the tilt angle that
   produces a 100 mg apparent change at 100 g load (cos-error and
   off-centre/corner-load contributions), and compare against the tilt a
   32.5 kg mass on four PU pads would produce from differential creep or
   micro-slip of ~0.1 mm on one corner. Is the isolator itself capable of
   generating the artefact it is meant to remove?
5. Give a falsifiable acceptance test and the minimum number of 600 s
   survey runs needed to detect a change in a ~1-per-10-min step-event
   rate at reasonable power (it is a Poisson count -- do the power
   calculation).

Show the code and the tables. End with a clear verdict on each of the seven
claims and a single recommendation.
