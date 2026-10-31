# Materials, vibration and heat

Asked for on [#188](https://github.com/vertical-cloud-lab/powder-doser/pull/188): material selection, vibration
tolerance (does the rig shake itself apart?), and heat buildup and transfer. These runs use the same models, designs and
commits as [RESULTS.md](RESULTS.md) (v3, v4 and the paternoster on #185). They add three new kinds of CalculiX analysis:
- heat transfer: DC3D10 elements with convection and radiation, coupled to an energy balance of the acrylic enclosure;
- forced response: `*STEADY STATE DYNAMICS`, by modal superposition;
- material substitution.

Nothing is built, so every number is a prediction. The detail is in [out/thermal/SUMMARY.md](out/thermal/SUMMARY.md),
[out/vibration/SUMMARY.md](out/vibration/SUMMARY.md) and [out/materials/SUMMARY.md](out/materials/SUMMARY.md). The code
is `cases/thermal.py`, `cases/vibration.py` and `cases/materials_study.py`.

**Checks against hand solutions** (added to `verify.py`):
- harmonic response: a cantilever under a 100 N harmonic tip load reads 0.0975 mm well below its first mode (static
  0.0983) and 2.365 mm at it (theory 2.386 at 2 % damping);
- heat: a pin fin's tip reaches 67.54 °C (fin equation 67.54);
- heat: a slab heated through its volume rises 23.39 K (q L^2 / 8k: 23.39).

## What to change

**Heat**

1. **Keep the NEMA 34's standstill current low.** Its loss is 2 I^2 R: about 50 W cold at the docs' 6.0 A and 0.7 Ω
   per phase, and 64 W once the winding is warm. v3 and v4 hang the motor inside their closed acrylic enclosures. With
   6.0 A held, v3's enclosure air settles at 39 °C:
   - the motor case reaches 83 °C, and so does the encoder on its rear end;
   - the back side plate reaches 75 °C at the motor;
   - the printed PETG parts screwed to that plate reach 54-65 °C: the hold-down 65 °C, the side tab 57 °C, the
     tensioner blocks 54 °C. PETG HF softens at 69 °C (HDT, 0.45 MPa).

   At 3 A (half current) it's 13.5 W: air 25.5 °C, motor 37 °C, those parts 30-33 °C. Closed-loop drivers of this kind
   adjust the current to the load, which with a balanced loop at standstill is small. (The CL-HSS86's manual says so;
   the CL86T's wasn't reachable from here.) Open-loop mode, or a holding current set to 100 %, gives the full 6.0 A at
   standstill.
   - Check the driver's mode and holding current through its RS232 tuning port.
   - Measure the motor's case after an hour holding at the station.
   - Check the E1000 encoder's temperature rating, since it sits on the motor's hottest end.

   v4 is similar: 63 W, air 35 °C, motor 76 °C, parts 48-56 °C. The paternoster's motor hangs outside in the room and
   reaches 75 °C at full current.
2. **The dock electromagnet cooks its own printed cup.** It dissipates 1.1 W for as long as the dock holds. In still
   air its PETG cup reaches 63 °C (66 °C at 25.5 °C enclosure air), within a few kelvin of PETG's HDT, under the
   magnet's sustained pull. On a fixed 5 V the warm coil also draws less current, so its pull falls to 72 % of cold:
   7.6 N instead of 10.6 N at the design gap.
   - With change 6 of RESULTS.md (the vee's magnet moved up), v3's dock still holds at every tilt and tap with the
     weaker pull. Its lowest contact force drops from 2.6 to 2.3 N. In fact, with that change the dock stays seated even
     with the electromagnet off (1.4 N), so the electromagnet only adds margin.
   - Fix: once it has pulled in, hold it at about half current (PWM, with the flyback diode it already has). That
     quarters its loss to about 0.3 W and its pull to about 2.6 N. Re-check the NEMA 11's mesh margin at that pull
     (station.py's `gear_capacity`). Or print the cup in PC or ASA, or seat the magnet in an aluminium cup.
   - The NEMA 11 next to it, at its 450 mA DRV8825 limit (1.4-1.5 W), stays at 39-43 °C. Disable it between doses
     anyway: a warm auger motor warms the powder and the air over the beaker.
3. **The balance shares the enclosure with the motor.** The HR-100A sits under the station, inside the acrylic. The
   enclosure air warms from the room's temperature to its steady value over about an hour after power-up: 3.5 K at
   half current, 17 K at full. A beaker brought in from the room is then colder than the air and reads heavy until it
   catches up. NIST's [GMP 10](https://www.nist.gov/document/gmp-10-weighing-operation-factors-20190506pdf) cites errors
   of up to 0.2 mg for a 4 °C difference between weights and the balance, two counts on the HR-100A.
   - Keep the motor's hold current low (change 1).
   - Let the rig warm up before taring or calibrating.
   - Keep the beakers inside the enclosure, or let them sit there a few minutes first.
   - If the motor has to run hot, put a baffle between the drive and the balance, or vent the drive end.
   - The station's own heat (2.4 W at the electronics carriage) rises away from the pan below it; the carriage's
     surfaces at 40-66 °C above the beaker are still a reason for change 2.
4. **Black-anodise or paint v3's and v4's back side plates.** Mill-finish 6061 radiates almost nothing (emissivity
   about 0.1, against 0.85 black). At half current a black plate runs the motor 2.5 K cooler and the printed parts on
   it 3-4 K cooler. At full current it's worth more.

**Vibration**

5. **Nothing shakes loose while the motor microsteps.** The torque ripple at the full-step rate (taken as 3 % of the
   holding torque, 0.4 N*m) drives each frame through its modes. At the worst speed each bolted joint's sideways load
   stays far below what friction holds, and a joint that doesn't slip can't self-loosen:

   VIBRATION_JOINTS_TABLE

   The side plates' T-nut screws come closest, at the frames' first sway mode. They would slip at a ripple of
   VIB_SLIP_MIN N*m, which full-stepping can produce, since every step is then an impulse. So:
   - keep microstepping on (the docs' 4000 pulses/rev);
   - keep the blue threadlocker on the T-nut screws;
   - don't cruise in the sway band (RESULTS.md change 15).

   Plate fatigue is no concern: the stress amplitude is VIB_PLATE_MAX MPa at most, against 6061-T6's 96 MPa endurance.
6. **Let the frame settle before reading the balance.** At 2 % damping the slowest sway mode (15-19 Hz) decays to
   0.1 % in 2.8-3.6 s after a stop, and in 5.7-7.2 s at 1 %. So wait 3-7 s, plus the HR-100A's own settling time, and
   keep the solenoid and the ERM off while it reads.
7. **The acrylic panels resonate inside the step-rate band** PANEL_SENTENCE Cast acrylic cracks from its screw holes
   under vibration or overtightening. Put rubber or nylon shoulder washers under the panel screws and don't overtighten
   them, or cut the panels from polycarbonate.
8. **The chain's vertical runs** (228.6 mm between sprockets, 80 N, carrying the carriages) have their first
   transverse mode at about 12.4 Hz. The 32T tooth-pass rate reaches that at 118 mm/s, above v3's and v4's 100 mm/s.
   The 114 mm horizontal runs sit at 25 Hz, out of reach.
9. The other things that work loose on machines like this are already covered:
   - the back 32T sprockets' set screws: Loctite 243 and a dimple, holding about 35 N*m against a 6 N*m jam share;
   - the bearings' nylon-insert nuts;
   - the A-1 tab screws in printed seats, which lose preload as the PETG creeps: RESULTS.md change 11 (a DIN 433
     washer, and a re-check after a week).

**Materials**

10. **PETG stays the right default** for the printed parts: tough, cheap ($20/kg), easy to print, low moisture. But
    no printed material fixes the parts that are short of strength. Across the layers, for a safety factor of 2:
    - v4's bridged latch would need 63 MPa;
    - the guide cradle at a retract stall, 51-53 MPa;
    - the electronics carriage at a P16 stall, 40-53 MPa.

    PETG gives 23 MPa across the layers and PAHT-CF about 47 MPa. PAHT-CF would lift the cradle and the electronics
    carriage to about 1.8 and v4's latch to 1.5. So those parts need the geometry changes in RESULTS.md, with a stronger
    material as a supplement.
11. **Print the parts on the back plate, and the electromagnet's cup, in ASA or PC** if the motor's hold current can't
    come down. ASA's HDT is 100 °C and PC's 117 °C, against PETG's 69 °C. Keep a part under sustained load 20 K or more
    below its HDT.
12. **Don't make v4's back plate steel to stiffen it.** Steel is 3x stiffer but also 2.9x heavier. In 1/4 in steel the
    plate weighs 8.5 kg instead of 2.9 kg, and the motor mode only rises from 50.6 to 59.7 Hz. The full-step rate
    still reaches that at 91 mm/s, inside v4's range. The two 2020 posts of RESULTS.md change 5 reach 68.6 Hz for
    about 0.4 kg. A steel plate also spreads the motor's heat worse: STEEL_THERMAL
13. **Static.** PETG and acrylic are insulators that charge when powder slides over them or someone wipes a panel.
    Charged powder clings to the module's printed walls, and a charged beaker, pan or nearby panel pulls on the
    balance. Options:
    - print the parts that touch powder (the outlet door, shutter and housing) in ESD-safe PETG, 10^6-10^9 ohm/sq;
    - ground the frame, the station and the balance to one point;
    - use an ionizer at the dose point.

    The project's own literature review
    ([docs/edison/multidoser-cap](../../docs/edison/multidoser-cap/literature.answer.md)) gives the same advice.
14. **The chain:** plain carbon-steel #35 needs oil, which collects powder and can reach the beakers. Nickel-plated or
    stainless #35 can run dry. Its lower rating doesn't matter at 80 N against a working load of about 2 kN.
15. **Moisture and cleaning.** Nylons (PAHT-CF, PA6-CF) take up water and lose about a third of their stiffness when
    wet, so dry them before printing. PC stress-crazes with IPA or acetone while under load. PETG, ASA and PET-CF are
    fine with IPA wipes.

## Heat in detail

The heat sources are copper losses (I^2 R). The motors turn too slowly for their iron losses to matter:
- the NEMA 34 at 25-100 % of its 6.0 A;
- the NEMA 11 at its 450 mA DRV8825 limit (I^2 R = 1.4 W cold);
- the dock electromagnet at 5 V and 0.22 A (1.1 W cold).

Each resistance rises 0.393 %/K and is iterated with its winding's temperature. The CL86T and the 48 V supply sit on the
electronics board outside the enclosure, so their losses don't count. The P16 at 20 % duty, the solenoid's 10 ms taps
and the ERM add a fraction of a watt.

Every exposed face sheds heat in two ways:
- natural convection, from laminar correlations iterated on each part's surface temperature;
- radiation: black paint 0.9, mill-finish 6061 0.10, black anodise 0.85, PETG 0.9.

Inside v3 and v4 the sinks are the enclosure's air and walls. The walls pass the heat to the room through 1.12 m^2 (v3)
or 1.44 m^2 (v4) of 3 mm acrylic, by convection and radiation outside, with no leakage, which would lower every rise.
The back side plate is modelled on its own, without the posts it's screwed to, which would carry some heat away, so the
plate temperatures are upper bounds.

THERMAL_TABLE

![v3: NEMA 34 at 6.0 A in its enclosure](out/thermal/chain-carousel-v3_motor_100.png)
![v3 electronics carriage: NEMA 11 and dock electromagnet](out/thermal/ec_v3_n11_em.png)

WARMUP_SENTENCE

## Vibration in detail

The excitation is a microstepped hybrid stepper's torque ripple. It acts at the full-step rate, four per electrical
cycle, from the detent torque and the torque curve's departure from a sine. Here that rate is f = v / 304.8 mm x 200,
one 32T turn per motor turn. The ripple's size isn't on the datasheet. 3 % of the 12 N*m holding torque (0.4 N*m) is
the nominal, and every result scales with it. The ripple acts on the stator. At these frequencies the loop's inertia,
about 37x the rotor's, holds the rotor still, so the same ripple goes out through the drive chain. The frame therefore
sees the jam's load pattern from frame.py, oscillating, at 0.4 N*m instead of 12.

The frames are frame.py's screw-pad models, feet held, at 2 % damping in every mode. Sideways forces on the side plates'
screws come from the shear stress in each screw pad times its area. The motor's screws carry its inertial force, the
drive chain's pull and the ripple torque.

VIBRATION_DETAIL

![FRF against chain speed](out/vibration/frf_vs_speed.png)

## Materials in detail

In a linear model of one material with applied loads, the stresses don't depend on its modulus. So each candidate's
safety factor is its strength over the FEA's peak, and its deflection scales with 1 / E. Where one part's stiffness
against another's decides the answer (v4's back plate under the motor), the FEA was rerun.

MATERIALS_TABLE

Sources:
- PETG HF: Bambu's TDS (as in materials.py).
- Heat deflection temperatures: Bambu's filament comparison table.
- PAHT-CF's strengths: Bambu's TDS V3.0 as quoted by a third-party review (check the current TDS).
- The others' across-layer strengths weren't in hand, so the table gives the strength each part needs instead.
- PETG's creep allowable is derated linearly from 8 MPa at 23 °C to zero at its HDT. That is a rule of thumb, not data.
