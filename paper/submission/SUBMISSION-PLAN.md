# Submission plan: *Digital Discovery*, New Hardware Developments collection, due Fri 13 Nov 2026

Target: **submit on Wed 11 Nov**, leaving two working days of buffer before the deadline.
Item codes (G1, S2, ...) are defined in [`HUMAN-TODOS.md`](HUMAN-TODOS.md). The package is:

| Part | File | State on 10 Oct |
|---|---|---|
| Manuscript | [`main.tex`](../main.tex) / [`main.pdf`](../main.pdf) (14 pp., abstract 247 words) | Complete draft; TODO comments remain |
| Supplementary Information | [`si.tex`](../si.tex) / [`si.pdf`](../si.pdf) (21 pp.) | Test-protocol table from PR #150 folded in (S9, Table S10) |
| Cover letter | [`cover_letter/cover_letter.pdf`](../cover_letter/cover_letter.pdf) | Names the collection; signatures, DOI and preprint status are red placeholders |
| CRediT statement | `main.tex`, Author contributions; evidence in [`CREDIT.md`](CREDIT.md) | Proposed; each author to confirm |
| Data and code availability | `main.tex`, Data availability | RSC template wording; licences and Zenodo DOI pending |
| ESI checklist | [`ESI-CHECKLIST.md`](ESI-CHECKLIST.md) | 18 items not yet met or partly met |
| Decisions | [`SUBMISSION-DECISIONS.md`](SUBMISSION-DECISIONS.md) | 20 questions, unanswered |

⚠️ **Confirm the collection first (G9).** On 10 Oct no public *Digital Discovery* page (the
journal home page, the news blog, the July 2026 newsletter) listed a "New Hardware
Developments" collection or a 13 Nov deadline. The open calls shown were the 2026 AI4X -
Accelerate Conference collection (closes 31 Oct) and General purpose models (closed 31 Aug).
If the collection came by invitation, its exact title belongs in the cover letter and in the
submission system's themed-collection field.

## Dated checklist

### Sun 11 Oct: security (Sterling)
- [ ] U1 Change the test Pi's password and its repository secret; rotate the old database password if it still works
- [ ] U2 Delete the exposed artifacts and logs from GitHub

### Wed 14 Oct: decisions (Sterling, Sam)
- [ ] G9 Confirm the collection's exact title and deadline
- [ ] G1 Corresponding-author line and affiliations; G2 author list; G3 CRediT roles
- [ ] G4 licences; G5 funding; G6 conflicts; G15 comparison table and "hello world": yes or no
- [ ] Answer the rest of [`SUBMISSION-DECISIONS.md`](SUBMISSION-DECISIONS.md) in the GitHub editor (items 1-6, 11-16), then ask `@claude` to implement
- [ ] S1 Sam posts the 1 Oct meeting video link (anyone with the link, no expiry, no password)
- [ ] G20 Close PR #150

### Fri 16 Oct: facts about the tested rig (Sam)
- [ ] S2 Which Fusion 360 parts were on the rig; S3 which tap collar
- [ ] S4 Flight thickness and pitch checked on a printed auger
- [ ] S5 Precautions used; S8 who took the Fig. 1b photo
- [ ] S6 Balance repeatability, linearity and calibration; S7 powder suppliers, grades and particle sizes

### Mon 19 Oct: implementation (Claude)
- [ ] C1 Implement every answer; rebuild `main.pdf`, `si.pdf` and the cover letter
- [ ] Post a summary of what changed on PR #97

### Fri 23 Oct: repository ready for referees (Sterling, Luke, Will, Claude)
- [ ] G7 Merge PR #74 (design log) and PR #170 (Fusion 360 STEP files)
- [ ] G8 Make the Onshape document public
- [ ] L1 PCB board files and wiring diagram on `main`; L2 which board, and whether an AI tool laid it out
- [ ] W1 Atomizer charge numbers (target, delivered, time)
- [ ] G14 Fig. 1b logo; G16 Jacob Lessard; G17 hackathon name
- [ ] C2 full BOM and build steps; C3 software citations; C4 `CITATION.cff`, `.zenodo.json`, `requirements.txt`, data dictionary, licence files

### Mon 26 Oct to Wed 28 Oct: optional additions
- [ ] S9 "Hello world" run on salt (if G15 is yes); C5 write it up with the comparison table
- [ ] Optional: one more Edison mock review of the full package (dispatch 26 Oct, fetch 28 Oct)

### Fri 30 Oct: frozen draft to all authors
- [ ] C6 Figure text at 6-7 pt and photos at 600 dpi (or defer to revision, item 17)
- [ ] Circulate `main.pdf`, `si.pdf` and the cover letter to all six authors
- [ ] S10 Sam's part-2 video review of the draft

### Wed 4 Nov: approvals
- [ ] A1 Every author confirms their CRediT roles and approves submission (keep the e-mails)
- [ ] Add "writing – review & editing" for every author who reviewed
- [ ] G12 Preprint decision

### Fri 6 Nov: submission details (Sterling, Sam)
- [ ] G10 Cover letter addressee and title line; S11 and Sterling's signatures
- [ ] G11 4-6 vetted reviewers with institutional e-mails
- [ ] G18 AI-in-figures confirmation; G19 ORCID, open-access licence (CC BY or CC BY-NC), APC or BYU agreement
- [ ] Submitting author creates or updates the RSC ScholarOne account with ORCID

### Mon 9 Nov: archive (Sterling, Claude)
- [ ] G13 Tag `v1.0.0`, archive it on Zenodo, put the version DOI into `Charles2026Release`; note the all-versions DOI too
- [ ] If posting a preprint, post it on ChemRxiv today (moderation takes about one to two working days)

### Tue 10 Nov: final build (Claude)
- [ ] C7 Strip the `TODO` comments; rebuild; build the upload ZIP of 20 files or fewer
- [ ] Run the RSC submission checker (<https://submission-checker.rsc.org>) and fix what it flags
- [ ] Final read of the cover letter: no red placeholders left

### Wed 11 Nov: submit (submitting author)
- [ ] Submit in ScholarOne (see the field list below), selecting the collection
- [ ] Post the confirmation e-mail's manuscript number on PR #97

### Thu 12 Nov - Fri 13 Nov: buffer
- [ ] Fix anything the editorial office returns; deadline Fri 13 Nov

## Submission-system fields

| Field | Value or source |
|---|---|
| Journal and article type | *Digital Discovery*, Full paper |
| Themed collection | The confirmed collection title (G9) |
| Title | `main.tex` title |
| Abstract | `main.tex` abstract (247 words; the limit is 250) |
| Authors, affiliations, e-mails, ORCID | `main.tex` author line and footnotes (G1, G2) |
| Corresponding authors | Sam Charles and Sterling G. Baird |
| Suggested reviewers | 4-6 names with institutional e-mails (G11); not in the cover letter |
| Funding | G5 |
| Conflicts of interest | "There are no conflicts to declare" unless G6 changes it |
| Data availability statement | Paste the `main.tex` statement |
| Files | Cover letter PDF; main-text ZIP (`main.tex`, `main.bbl`, `si.aux`, `rsc.bst`, `head_foot/` graphics, figure PDFs) plus `main.pdf`; `si.pdf` |
| Transparent peer review | Opt in or not (can be changed before acceptance) |
| Table-of-contents graphic | Due at revision, not now (item 18) |
