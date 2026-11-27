MANUSCRIPT REVIEW AND NUMERICAL AUDIT

Start with mock_peer_review_and_audit.md.

Numerical reproduction: python reproduce_audit.py
Requires Python 3, numpy, pandas, scipy. The executed versions are recorded in audit_results.json.
The script reads si_extracted.txt and writes new results in reproduced/.
The source SI contains rounded observations. No unavailable raw telemetry is imputed.

Files:
- campaign1_tableS2.csv: all 60 campaign-1 and validation records
- campaign2_tableS4.csv: all 43 campaign-2 records
- validation_summary.csv, mann_whitney_comparisons.csv, paired_corners.csv
- dose_range_tableS3.csv, screening_effects.csv
- audit_results.json: intervals, tests, design check and power audit
- audit_overview.png: validation and paired-corner figure
- reproduction_stdout.txt: executed script output
- main_extracted.txt, si_extracted.txt: e14c reader text used in the audit
- journal_guide.txt, elsevier_ethics.txt, references.bib: saved web evidence and full citations
- input_sha256.json: hashes of all eight supplied documents

The reviewer reports are simulated expert-inspired perspectives, not opinions of the named people.
No synthetic planned manuscript data were treated as observations.
