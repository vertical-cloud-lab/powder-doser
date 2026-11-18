# Figure captions (v2)

Edit the captions here. `build_figures.py` reads this file and puts each caption under its figure
in `figures.tex` and `figures.pdf`, in the preview images (`preview/*.png`) and in
`FIGURES-AND-TABLES.md`. Then run `python3 build_figures.py`.

- Each figure starts with a heading `## Fig. N Title`; the title is set in bold before the caption.
- The caption is all the text up to the next heading. Single line breaks are ignored, so each panel
  can sit on its own line.
- `#123` becomes a link to issue or pull request 123; `**bold**` works; write a literal asterisk as `\*`.
- Open with the takeaway (review of 11 Nov, G2).

## Main text

## Fig. 1 The doser

One printed auger tube is both the powder reservoir and the dosing screw; the doser turns, tilts and taps it over a cup on an analytical balance.
(a) The doser as tested in the second round (photographed 11 Sep 2026), with its main parts labelled; the auger tube is shown in section in (c).
(b) Exploded view of the current design, assembled in CAD from the team's parts (#170), with the 13 main parts numbered beside them as in the bill of materials (SI Fig. S4): the auger (19) and its screw-on cap (25); the tap collar (21), its solenoid (23) and the tap-collar base (15); the two brackets that hold the auger (20); the hinged mounting plate (9); the stepper motor (12) and its pinion (14), which turn the auger's 44-tooth gear; the two tilt servos (4) and their pinions (7); the baseplate (2); and the mounting board (1). Screws and nuts are numbered only in SI Fig. S4.
(c) Section through the tested auger and its screw-on cap, the team's Fusion 360 part: the flight fills only the outlet end, and the 44-tooth gear is on the outside of the tube.
(d) The fixed livestream camera's view of the cup after a 0.5 g NaCl dose (15 Sep 2026; 0.496 g delivered; #116).

## Fig. 2 AI agents and engineers, April to November 2026

AI agents modelled the first parts from text and drawings; from July the engineers redrew in conventional CAD the parts that were built and tested, and the agents moved on to running the tests and assembling the CAD.
(a) Key designs on one date axis, each joined to its date. Above the axis are the designs modelled by AI agents, each tagged with the agent (purple) and model (grey): the powder excavator (#2) and the first auger (#16), from the hackathon (the first auger is the 24 Apr OpenSCAD design, in section); the whole module from a single request (#35); the bracket the agent modelled from the team's dimensioned drawing (#46, #47), shown beside the drawing (grey frame; red arrow); the first tap collar and the collar after review (#51); the storage auger with its screw cap (#49); all 11 parts from one prompt through the Zoo Text-to-CAD API (#104, #110); and the team's parts assembled through the Onshape API (#170). Below the axis is the engineers' work, each design tagged with who made it (green) and the tool (grey); photographs are labelled as photographs: the hackathon sketch (#1), the first printed auger, the Fusion 360 auger, cap and 44-tooth gear that turned in every test (#120), the first dose in a glove box, by Sam with colleagues at the University of Utah (#117), the multi-doser carriage sketch and Onshape model (#128), and the doser as tested (#156). The hackathon (22–24 Apr) and the 13-powder test campaign (4 Aug–15 Sep) are shaded on the axis.
(b) When each agent and model was in use, on the same date axis. Claude Code ran locally at the hackathon and in GitHub Actions from 30 Jun; both are on one line. The engineers' conventional CAD is in green.

## Fig. 3 The original AI parts and what replaced them

Every AI-modelled part was reviewed, printed and tested, but the tested doser ran on later versions, and the parts have kept changing since: the agent revised the tap collar and the team then replaced it, and the team redrew the auger in Fusion 360. AI parts have purple frames, the team's grey; each image is tagged with who made it and in what.
(a) Tap collar to solenoid bracket: the first AI collar (15 May) and the collar after review (#51, by 10 Jun), the collar on the rig during the tests (11 Sep, #156), and Ethan's solenoid bracket, which mounts the solenoid on the plate without a collar so that an auger can be swapped without taking the tapper off (first version 7 Nov, Onshape, #203; photographed 17 Nov).
(b) Auger, in section: the first auger to be printed and tested, begun at the hackathon and shown as the agent's version of 13 May with the flight on a central shaft, run with NaCl on 14 May (#16); the agent's storage auger with 16:48 gears (16 Jun, #49); and Sam's Fusion 360 recreation of it with 20:44 gears (17 Jul, #120), which turned in every test.
(c) Bracket: the team's dimensioned drawing (#46) and the agent's model of it (#47), both 14 May, then the team's own versions: Sam's bolted split clamp (Fusion 360, Jul, #120), his open flexible C-clip, which was on the rig through the tests (from Aug), and Ethan's Onshape version of it on the current doser (#193, Oct).

## Fig. 4 How a dose runs

A person asks the AI agent for a dose in a GitHub comment; a three-phase controller on the doser's microcontroller then turns, tilts and taps the auger until the balance reads the target.
(a) A request and the agent's reply (8 g of AlSi10Mg for an atomizer charge, #166, 29 Sep 2026).
(b) The control loop: the balance is read after every step, and the controller acts on the mass still to go.
(c) One 1 g NaCl dose from the test campaign (12 Aug 2026), with its three phases shaded: bulk, fine and tap. A brace above the trace spans each phase, under the tube position in that phase (CAD renders of the current design at 45°, 22.5° and 0°); the fixed camera's stills before and after a 0.5 g salt dose (15 Sep 2026) are at either end. The green band is the ±5% acceptance limit. One image rather than subfigures: the lines from the braces join the tube positions to the trace.

## Fig. 5 Using the doser

Each powder has its own auger, filled once and stored loaded, so changing powder means swapping a tube.
(a) Filling an auger with salt through its open end, then capping it (29 Jul 2026).
(b) Fitting a filled auger to the doser, and (c) the doser ready over the cup, frames from the 30 Sep 2026 dose video: the powder falls through a paper funnel into an aluminium cup that stands in the glass beaker. The aluminium cup is part of the alloy workflow itself: the dose lands directly in the cup used for the next step in making the alloy, so the powder is never transferred.
(d) The eight augers of the food-safe set (seven powders), capped and labelled (17 Nov 2026), each with the mass one auger revolution delivered (\*at 22.5° tilt; Fig. 6a).

## Fig. 6 Open-loop delivery of 13 powders under one fixed set of settings

Ten powders moved, from 10 to 231 mg per auger revolution, and three delivered nothing measurable; one solenoid tap released up to 20 mg, and under continuous rotation the powder arrived in waves, one surge per auger revolution. Every panel was measured with the tube tilted at 22.5°.
(a) Mass per auger revolution at 22.5° tilt (protocol C; mean ± standard error of six revolutions; log axis).
(b) Mass released by one solenoid tap at 22.5° tilt (protocol E): mean ± standard deviation of eight taps, the spread to expect from a single tap, drawn only where the tap was resolved (mean more than twice its standard error, as in Table S1). Each row without a bar says why. For AlSi10Mg and the coarse silicon, the balance noise with nothing moving (standard deviation 29 and 20 mg) was far larger than a tap; a tap cannot remove powder, and their negative means (−1.9 and −3.5 mg) were that noise. For CMC, the two rice flours and the fine silicon, most single taps read 0.0–0.1 mg. Fumed silica's only run failed screening. Table S1 gives the standard errors.
(c) Mass against time while the auger turned continuously at 15 rpm (protocol D), for a representative selection of four powders, from the fastest (AlSi10Mg) to a slow one (CMC). The flow came in waves: AlSi10Mg and NaCl each arrived in surges of about 200 mg every 4 s, once per auger revolution, with little in between. Gridlines every 4 s mark the auger revolutions.

## Fig. 6B Open-loop delivery, with banded rows

The same as Fig. 6, with alternate rows shaded straight across (a) and (b), so that each powder can be followed from one panel to the other (17 Nov review).
(a) and (b) are butted together and share the powder names; a dashed line separates the three powders that delivered nothing. Data, error bars and panel (c) as in Fig. 6.

## Fig. 7 Closed-loop doses

Doses of 1 g landed within ±5% for every powder that delivered at least 26 mg per revolution; smaller doses missed more often, fast powders tending to overshoot and slow ones to fall short. The misses are largely a control problem, which we are actively working on, rather than a limit of the hardware. Error of every valid closed-loop dose from both test rounds; each marker is one dose. One row per powder, ordered by mass per revolution (fastest at the top). The green band is the acceptance limit: ±10% below 100 mg, ±5% at and above. Times per dose are in Table 3 and SI Fig. S3. One image rather than subfigures: the three panels share the powder axis.

## Fig. 7B Closed-loop dose error in milligrams

In milligrams the typical miss was smallest at 200 mg and largest at 1 g, the reverse of the percent view in Fig. 7: the median absolute error was 7.1 mg at 50 mg, 5.0 mg at 200 mg and 34.6 mg at 1 g.
Error (delivered minus target) of every valid closed-loop dose from both test rounds; each marker is one dose. Rows, order and shading as in Fig. 7.
The green bands are the acceptance limits, ±5 mg at 50 mg, ±10 mg at 200 mg and ±50 mg at 1 g, so the counts within the limit are the same as in Fig. 7.
The median error was −1.7, −4.5 and −34.6 mg. Doses beyond ±70 mg are arrows at the edge of the axis, with their values beside them: 4 at 200 mg and 15 at 1 g, nine of which (brown rice flour and the fine silicon) delivered nothing (−1000 mg).

## Fig. 7C Closed-loop dose error in milligrams, all targets together

On one milligram axis the three targets crowd each row, but the spread of the error clearly grows with the target: the middle half of the errors spans 16 mg at 50 mg, 32 mg at 200 mg and 298 mg at 1 g.
(a) Every valid closed-loop dose on one axis. Each powder row has three lanes: 50 mg (purple circles, top), 200 mg (teal squares, middle) and 1 g (dark diamonds, bottom), each with its own green limit band (±5, ±10 and ±50 mg). Filled markers are within that target's limit, open markers outside; the 19 doses beyond ±70 mg are arrows at the edge.
(b) Error by target as box plots, on a symmetric-log axis (linear within ±10 mg) so that a 5 mg miss and a 1000 mg miss show together. Every dose is drawn over its box, filled if it was within the limit; the boxes span the middle half of the errors, the whiskers reach the extremes, and the median is printed beside each box.

## Supporting information

## Fig. S1 Generative-CAD comparison

Asked for the whole doser at once, every tool returned parts that did not make a working assembly; one part at a time, with review, worked better.
(a–c) The same prompt (#104, 22 Jun 2026) given to the GitHub Copilot coding agent, CADSmith and the Zoo Text-to-CAD API, each rendered from the same viewpoint.
(d–f) The tap collar from the coding agent (first version and after review) and from Zoo Design Studio (third Zookeeper iteration).
(g, h) CADSmith's mounting plate and baseplate.
(i–l) The coding agent's four mounting-plate iterations: out-of-date input files led to a hole, then platforms, then a gap, until the correct files were supplied. Not yet reviewed; still one image.

## Fig. S2 Variation between revolutions

Most powders varied by 2–18% from one revolution to the next; white rice flour, at 37%, varied most. Revolution-to-revolution coefficient of variation against mass per revolution at 22.5° (old Fig. 3c, without the slow/fast shading). The same numbers are in Table S1, so this figure can also be dropped.

## Fig. S3 Time per dose

Larger doses took longer: for doses within the limit, the median was 52 s at 50 mg, 152 s at 200 mg and 185 s at 1 g. Time to finish each dose, by target mass; lines are the medians of the doses that finished within the acceptance limit (old Fig. 5d).

## Fig. S4 Every part of the doser

Every part of the current design, screws and nuts included, numbered as in the bill of materials; Fig. 1b labels only the 13 main parts (bold here).
Exploded view assembled in CAD from the team's parts (#170), with each number beside its part, and the bill of materials with the quantity of each part and whether it is printed, purchased or a fastener.
The 19 build steps (#170) and the new stand, with how its height is adjusted, are still to be added.
