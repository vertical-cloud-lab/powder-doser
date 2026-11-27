# Edison mock review, round 2 (27 Nov 2026)

One Edison Scientific ANALYSIS task (`1fea381a-1bc8-4018-a5e3-4613e9acd287`, dispatched 2026-11-27 19:47
UTC, status `success`) on the rewrite of 27 Nov (main.pdf and si.pdf at commit `2cdf739`, plus OUTLINE.md,
SUBMISSION.md and the hardware paper's `main.tex` from PR #97). It acted as handling editor and three
reviewers, audited the statistics against the SI tables, and audited duplication against the hardware
paper. The prompt is in [`run_mock_review_r2.py`](run_mock_review_r2.py).

| File | What |
|---|---|
| `mock_review.answer.md` | Short verdict |
| `outputs/mock_peer_review_and_audit.md` | The full report: editor, three reviewers, statistics audit (§5), 30-item overlap inventory (§6), E0–E9 sufficiency (§7), 18 ranked revisions (§8) |
| `outputs/` | Every file the trajectory produced: the audit's Python, CSVs and figure, extracted text, the reproducibility bundle, memory log, notebook |
| `mock_review.task.json`, `mock_review.notebook.ipynb` | Full task record and notebook |
| `inputs/` | What was uploaded (the two PDFs are git-ignored) |

Headline: reject as a full research article now and rebuild; better fit as a Methods paper now. The main
salt statistics reproduce (medians, exact p = 0.004, the shifts, bootstrap intervals, screening table,
outcome counts and binomial bounds). Smallest defensible package: E0–E3 plus E5–E6, with a paired and
replicated sieved/unsieved Al 4047 comparison, a repeat-fill or repeat-day anchor, and one AM-facing
outcome; E4 (multi-task) and DEM inference are not prerequisites. What was done with each item is in
[`../OUTLINE.md`](../OUTLINE.md) §4c.
