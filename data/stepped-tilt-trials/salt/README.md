# Salt: stepped-tilt trials (2026-11-18 to 2026-11-19)

The trials started with salt, at 1 g a trial. These are the five runs and the stall analysis, in the order they ran. Only the last run, with the old tube back on and the bulk at 80 rpm with taps, got doses out; the protocol it settled on is the one the other powders then ran.

| Started (UTC) | Run folder | Setup | Script version | Trials | Doses | Within ±1 mg | Median error | How it ended |
|---|---|---|---|---|---|---|---|---|
| 2026-11-18 06:45 | [`2026-11-18_salt_tilt-schedule`](2026-11-18_salt_tilt-schedule/) | 1 g; bulk 55 rpm, 60 → 40° | 18a, 18b | 4 | 0 | – | – | All 4 stalled in the bulk: the tube was full to the brim and the salt plugged at 60–40° |
| 2026-11-18 16:06 | [`2026-11-18_salt_tilt-schedule-50-30deg`](2026-11-18_salt_tilt-schedule-50-30deg/) | 1 g; bulk 50 → 30° | 18c | 4 | 0 | – | – | All 4 stalled: almost no salt reached the outlet at any angle |
| 2026-11-19 19:47 | [`2026-11-19_salt_tilt-schedule-new-auger`](2026-11-19_salt_tilt-schedule-new-auger/) | 1 g; new tube, bulk 60 → 40° | 19a | 4 | 0 | – | – | All 4 stalled: one 166 mg slug at 60°, then very little at any angle |
| 2026-11-19 | [`2026-11-19_why-stalls`](2026-11-19_why-stalls/) | Analysis only: summer vs November salt flow | – | – | – | – | – | Why the November trials stall when summer runs at the same angles didn't |
| 2026-11-19 20:41 | [`2026-11-19_salt_tilt-schedule-bulk-taps`](2026-11-19_salt_tilt-schedule-bulk-taps/) | 1 g; new tube, taps in the bulk (19c: in the fine stage too) | 19b, 19c | 5 | 0 | – | – | The taps got the salt moving, then the flow fell trial by trial and the tube stopped feeding |
| 2026-11-19 21:43 | [`2026-11-19_salt_tilt-schedule-old-auger-80rpm`](2026-11-19_salt_tilt-schedule-old-auger-80rpm/) | 1 g; old tube, bulk 80 rpm with taps | 19d | 27 | 24 | 3 | +7.4 mg | The tube ran dry: trial 25 stalled at 0.781 g, trials 26–27 got nothing |

*Script version* is the script's `SCRIPT_VERSION` without the leading `2026-11-`. *Doses* counts the trials that reached the target; *within ±1 mg* and the *median error* are over those doses.

Each run folder has a README with the full write-up. [All powders and the cross-powder figure](../README.md).
