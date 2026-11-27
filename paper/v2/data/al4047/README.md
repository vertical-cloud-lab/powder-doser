# Al 4047 doses for the atomizer (30 Sep – 20 Oct 2026), for the paper

Ten closed-loop doses of Al 4047 powder, made in the lab's own ultrasonic atomizer, into an 8 g
atomizer charge and two atomizer cups of a composition spread (byu-vcl PR #232). Each was run by
the dose executor (`scripts/opt_dose_capture.py`, `--mode production`) with settings from the salt
optimization campaign (PR #166), and each has an `opt_trials` document in MongoDB and a JSON copy
on its source branch.

- `trials.csv`: one row per executor dose: settings, aim, firmware status, mass delivered over its
  own tare, and what happened. `source_ref` and `source_path` locate the JSON record
  (`git show <source_ref>:<source_path>`).
- `charges.csv`: the three charges or cups, with the powder each finally held, including the
  hand-driven steps that the agent ran between executor doses (reverse turns, stepwise doses,
  top-ups). Those steps are logged as `mode: "manual"` documents in the same MongoDB campaign
  (issue #186) and are described in the source READMEs:
  - [`data/opt/production-al4047-9fxeqt/README.md`](https://github.com/vertical-cloud-lab/powder-doser/blob/claude/issue-164-20260922-1928/data/opt/production-al4047-9fxeqt/README.md) (PR #166)
  - [`data/opt/production-al4047-atomizer-cups/README.md`](https://github.com/vertical-cloud-lab/powder-doser/blob/claude/issue-186-20261021-0134/data/opt/production-al4047-atomizer-cups/README.md) (issue #186)

Masses are as the source READMEs give them: each net figure carries about ±1–2 mg (balance creep
and re-taring). The 7.5 wt% and 15 wt% targets follow byu-vcl PR #232: powder / (cup + plug +
powder). The 7.5 wt% cup's plug mass (4.995 g) is that PR's computed value; the 15 wt% cup was
weighed with its plug.
