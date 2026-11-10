# Readability / jargon audit

Tooling and findings for keeping the manuscript readable to a *Digital Discovery*
audience, which spans chemistry, materials, ML and instrumentation — so a term that
is unremarkable in one of those fields is jargon in the other three.

| File | What it is |
|---|---|
| [`JARGON-AUDIT.md`](JARGON-AUDIT.md) | **Start here.** Ranked findings with line numbers, quotes and suggested plain-language rewrites |
| [`jargon_audit.py`](jargon_audit.py) | The checker that produces the numbers those findings rest on |
| `audit_report.md` | Generated. Section scoreboard, longest sentences, acronyms, lexicon hits |
| `audit_report.json` | Generated. Same data, machine-readable |

```bash
python paper/readability/jargon_audit.py    # regenerates both audit_report.* files
```

Nothing here modifies `main.tex` or `si.tex`. Re-run after each manuscript revision;
if you disagree with a flagged term, edit `LEXICON` in the script rather than
ignoring the section-level counts.
