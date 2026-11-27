# Data deposit for the optimization paper (not yet deposited)

*Additive Manufacturing* applies Elsevier's research-data **Option C**: the data must be deposited in a
repository and cited and linked in the article. This folder holds the metadata for that deposit. **Nothing
has been uploaded or published.** A Zenodo DOI is permanent, so Sterling decides when to publish (see the
repo's `CLAUDE.md`, "Zenodo"). Test on the sandbox first.

What to deposit (a zip of `paper/optimization/` at the submission commit, minus `mock_review*/inputs/` and
the meeting audio, which is not in the repo):

| Path | What |
|---|---|
| `data/opt_trials/` | All 125 dose records (MongoDB `opt_trials`, 29 Sep to 20 Oct 2026) with balance telemetry |
| `data/salt-*/`, `data/production-*/`, `data/powders/` | Campaign configurations, run notes, per-campaign records, the literature property tables |
| `analysis/` | The scripts and their outputs (`results/stats.json`, `gp_cv.json`, per-dose CSVs, SI tables) |
| `figures/` | Figure scripts and the figures |
| `main.tex`, `si.tex`, `refs.bib` | The manuscript source |

The firmware and campaign code that produced the records (`scripts/opt_campaign.py`, the
`trickle_tap` firmware) are on the #166 branch (`claude/issue-164-20260922-1928` at `d14a50d`). Either
merge it before the release, or include a copy of those files in the deposit.

[`zenodo_metadata.json`](zenodo_metadata.json) is the deposit's metadata in the Zenodo REST API's format.
Fill in the creators once the author list is agreed.
