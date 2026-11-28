"""The chapter for byu-vcl vertical-lab/longform.py's CHAPTERS, after "alloy4" (the powder, checked).

Written by build.py from powder-doser PR #190 (the clips at afccaf1).
Copy the clips in first (fetch.py), then paste BADGE_POWDER_DOSER and CHAPTER into longform.py,
and narration.json's lines into vertical-lab/narration.json.
"""
BADGE_POWDER_DOSER = "POWDER-DOSER'S OWN RENDER"

CHAPTER = dict(
    key='powdertests', title="The powder tests by the standards: powder-doser's renders",
    card=[
        "Eight standard tests of a powder's flow, density, size, moisture and strength, drawn by the powder-doser project at a bench, by hand. The lab model has no station for most of them. The lab's plan sieves by hand and takes the Hausner ratio in a cylinder; the twin models Hall flow, apparent density and ffc.",
        "Schematics, not vendor CAD. Every number on screen is illustrative, for 316L, AlSi10Mg or table salt, not the lab's own powders."],
    parts=[
        ('ext', 'ext/powder_tests/hall_flow.mp4', BADGE_POWDER_DOSER,
         "Hall and Carney flow (ASTM B213, B964), by hand: seconds for 50 g to run out. The twin's psd.flow() predicts both; the lab doesn't measure them",
         'Hall and Carney flow'),
        ('ext', 'ext/powder_tests/density.mp4', BADGE_POWDER_DOSER,
         "Apparent and tap density (ASTM B212, B527) give the Hausner ratio, which the lab's runs plan takes in a graduated cylinder within a week of a run",
         'Apparent and tap density, Hausner ratio'),
        ('ext', 'ext/powder_tests/angle_of_repose.mp4', BADGE_POWDER_DOSER,
         'Angle of repose (ISO 4324, USP <1174>), by hand: a cone on a fixed base, free-flowing then cohesive. Neither the lab nor the twin has it yet',
         'Angle of repose'),
        ('ext', 'ext/powder_tests/sieve.mp4', BADGE_POWDER_DOSER,
         "Sieve analysis (ASTM B214): five 8 in. sieves, 150 to 45 µm, 15 min on a tapping shaker. Chapter 3's cell splits the powder; this sizes it",
         'Sieve analysis'),
        ('ext', 'ext/powder_tests/laser_diffraction.mp4', BADGE_POWDER_DOSER,
         "Laser diffraction (ASTM B822, ISO 13320), drawn with a wet cell; tray E's Mastersizer disperses dry. The twin's psd.py models the same optics",
         'Laser diffraction'),
        ('ext', 'ext/powder_tests/moisture_lod.mp4', BADGE_POWDER_DOSER,
         'Moisture by loss on drying (USP <731>): weigh, dry at 105 °C, cool, reweigh to constant mass. Neither the lab nor the twin has it yet',
         'Moisture, loss on drying'),
        ('ext', 'ext/powder_tests/ft4_shear.mp4', BADGE_POWDER_DOSER,
         "FT4 shear cell (ASTM D7891): the yield locus and the flow function ffc. The twin estimates ffc from a Bond number; this is how it's measured",
         'FT4 shear cell'),
        ('ext', 'ext/powder_tests/ring_shear.mp4', BADGE_POWDER_DOSER,
         'Schulze ring shear tester (ASTM D6773): the same ffc, for a cohesive powder. Sent out at about $650 a sample; no station in the lab',
         'Ring shear tester')])
