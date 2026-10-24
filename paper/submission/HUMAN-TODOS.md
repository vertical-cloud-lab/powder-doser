# Remaining human TODOs, with owners (10 Oct 2026)

Every item a person still has to do before the *Digital Discovery* submission, gathered from
the `TODO (human)` comments in `main.tex`, `si.tex` and `cover_letter/cover_letter.tex`, the
unanswered boxes in the three decisions files, and the open items in
[`GUIDELINES-AUDIT.md`](GUIDELINES-AUDIT.md). The dates match the plan in
[`SUBMISSION-PLAN.md`](SUBMISSION-PLAN.md).

**Owners.** S.C. = Sam Charles, W.M. = Will Mulberry, L.W. = Luke Winters,
S.G.B. = Sterling G. Baird, All = every author, Claude = `@claude` on PR #97 once the
answers are in.

**Bench data.** Sam ran the bench campaign in #116 (66 of the 79 human comments there since
1 August are his), so the bench items are his. Will ran the optimization campaign and the
atomizer charges (#166), so the atomizer numbers are his. No new bench data are needed for
the results themselves (Sterling, 1 Oct); the bench items below are a calibration statement,
a supplier table, a short "hello world" check, and facts about the tested rig.

**Blocks submission?** "Yes" means the journal requires it at submission or the paper says
something that is not yet true. "No" means it can wait for revision or is optional.

## Urgent (this weekend)

| # | TODO | Where | Owner | Due | Blocks? |
|---|---|---|---|---|---|
| U1 | Change the test Pi's password and update its repository secret; rotate the old database password if it still works. Both appear in public Actions artifacts. | SUBMISSION-DECISIONS item 9 | S.G.B. | 11 Oct | No, but security |
| U2 | Delete the affected runs' artifacts and logs from GitHub (redacted copies are in the draft release) | item 9 | S.G.B. | 11 Oct | No |

## Sterling (S.G.B.)

| # | TODO | Where | Due | Blocks? |
|---|---|---|---|---|
| G1 | **Corresponding-author line and affiliations.** Confirm the footnote: both corresponding authors under BYU Mechanical Engineering (with both e-mails), and the Acceleration Consortium as your second affiliation. Confirm Sam's address (`samuelwcharles@gmail.com` or the BYU student address). | `main.tex:132,152-153`; items 3, 4 | 14 Oct | Yes |
| G2 | Author list: six authors, or four (Sam, Will, Luke, Sterling) with Carl and Gage in the Acknowledgements. Settle before submission; RSC accepts later changes only in exceptional cases. | item 1; `main.tex:132` | 14 Oct | Yes |
| G3 | Confirm the CRediT roles proposed in `main.tex` (evidence in [`CREDIT.md`](CREDIT.md)), including "funding acquisition" for yourself if there is no funder | item 2; `main.tex:398-403` | 14 Oct | Yes |
| G4 | Licences: hardware (CERN-OHL-S/W/P or MIT), data (CC BY, CC0 or MIT); add the licence files | item 5; `main.tex:417` | 14 Oct | Yes (DD "strong preference") |
| G5 | Funding statement: "no specific grant" or funder plus grant number | item 6 | 14 Oct | Yes |
| G6 | Conflicts: any free credits or early access from Edison, Zoo, CADSmith, GitHub or Anthropic | item 14; cover letter | 14 Oct | Yes |
| G7 | Merge PR #74 (design log) and PR #170 (Fusion 360 STEP files); decide whether to copy the AI-modelled CAD onto `main` | item 10; `main.tex:409-416` | 23 Oct | Yes (paper says the repository holds them) |
| G8 | Make the Onshape document public (Share > Public, after deleting the "(superseded)" tabs) | `si.tex:82`; `main.tex:409` | 23 Oct | Yes (paper says it is public) |
| G9 | Confirm the collection: its exact title and the 13 Nov deadline, from the invitation or call. No public DD page lists it (checked 10 Oct). | cover letter | 14 Oct | Yes |
| G10 | Cover letter: addressee (Editor-in-Chief or Executive Editor; the Consortium tie), title line, signature | item 16; cover letter | 6 Nov | Yes |
| G11 | Vet 4-6 suggested reviewers (drop DD Associate Editors and recent co-authors) and collect institutional e-mails | item 16; GUIDELINES-AUDIT R12 | 6 Nov | Yes (entered in ScholarOne) |
| G12 | Preprint: ChemRxiv at submission or none | item 15 | 4 Nov | Yes (cover letter states it) |
| G13 | Zenodo: tag `v1.0.0`, archive it, add the version DOI to `Charles2026Release` (DD requires the DOIs by acceptance; the draft says archived at submission) | item 11; `main.tex:413` | 9 Nov | No (yes if the text keeps "at submission") |
| G14 | Fig. 1b shows a METTLER TOLEDO logo: blur, swap the photo, or leave it to the editor | item 8 | 23 Oct | No |
| G15 | Commercial comparison table and a "hello world" test in the SI (DD hardware editorial): yes or no | items 12, 13 | 14 Oct | Partly (editorial asks for both) |
| G16 | Confirm "Jacob" in the 24 July glove-box notes is Jacob J. Lessard | `main.tex:422-425` | 23 Oct | No |
| G17 | Name the hackathon (POSE 2026, UW Machine Agency) in §2.2, or leave it unnamed | `main.tex:188` | 23 Oct | No |
| G18 | AI-in-figures confirmation for Fig. 2 (tools trained on licensed data, output reusable commercially), and confirm no photo was edited with AI | GUIDELINES-AUDIT R13; cover letter | 6 Nov | Yes if it applies |
| G19 | ORCID for the submitting author, open-access licence (CC BY or CC BY-NC), £2,200 APC or a BYU agreement | GUIDELINES-AUDIT R14 | 6 Nov | ORCID at revision; APC at acceptance |
| G20 | Close PR #150 once you're happy with the SI table that replaces it | this session | 14 Oct | No |

## Sam (S.C.)

| # | TODO | Where | Due | Blocks? |
|---|---|---|---|---|
| S1 | **Video link:** share the 1 Oct meeting recording as an anyone-with-the-link URL, with no expiry and no password, and post it on PR #97 with a ping to `@claude` | MEETING-DECISIONS item 15; Sterling's 8 Oct comment | 14 Oct | No (corroborates answers already given) |
| S2 | Which Fusion 360 parts (plates, brackets, tap collar, servo pinions) were on the rig for the August and September tests | `main.tex:353-356`; MEETING-DECISIONS item 1 | 16 Oct | Yes (the abstract says "some") |
| S3 | Which tap collar was on the rig: the Zoo collar, the Fusion collar, or a change mid-campaign (dates) | DECISIONS item 4 | 16 Oct | Yes (Fig. 2b and Table 2 tell the Zoo story) |
| S4 | Check the measured flight (0.5 mm thick, 10.4 mm pitch) against a printed auger; you said you needed to | DECISIONS item 2; `main.tex` Fabrication | 16 Oct | Yes |
| S5 | Precautions actually used (PPE, fume hood, dust handling, storage) for the Safety subsection | item 7 | 16 Oct | Yes (RSC: hazards stated "very clearly") |
| S6 | Balance: repeatability and linearity (HR-100A datasheet), and when and how it was calibrated; room temperature and humidity if logged | GUIDELINES-AUDIT R3 | 16 Oct | No (recommended) |
| S7 | Powder sources: supplier, catalogue number, grade and nominal particle size for the 13 powders | GUIDELINES-AUDIT R3 | 16 Oct | No (recommended) |
| S8 | Who took the Fig. 1b photo (permission if not an author) | GUIDELINES-AUDIT R14 | 16 Oct | Yes if not an author |
| S9 | If G15 is yes: run the "hello world" check on salt (protocol C, then one 1.000 g dose) and post the numbers | item 13 | 26 Oct | Only if G15 is yes |
| S10 | Part-2 raw video review of the draft (§2.2 onward), as Sterling suggested | Sterling's 10 Oct comment | 30 Oct | No |
| S11 | Signature for the cover letter | cover letter | 6 Nov | Yes |

## Will (W.M.)

| # | TODO | Where | Due | Blocks? |
|---|---|---|---|---|
| W1 | Atomizer charges (#166): target, delivered mass and time for the 8 g AlSi10Mg and 8 g Al 4047 doses, so the Conclusions can give numbers | GUIDELINES-AUDIT R1; Conclusions | 23 Oct | No (strengthens "application to discovery") |

## Luke (L.W.)

| # | TODO | Where | Due | Blocks? |
|---|---|---|---|---|
| L1 | Put the board files of the PCB on the tested rig, and a wiring diagram or pin table, on `main` | item 10; GUIDELINES-AUDIT R2 | 23 Oct | Yes (paper says board files are in the repository) |
| L2 | Say which board was on the rig and whether an AI layout tool (DeepPCB, Quilter) made it, for the AI-use statement | GUIDELINES-AUDIT R14; #94, #95 | 23 Oct | Yes if an AI tool laid it out |

## Every author

| # | TODO | Where | Due | Blocks? |
|---|---|---|---|---|
| A1 | Read the final draft, confirm your own CRediT roles, and approve submission by e-mail (ICMJE: every author reviews and approves) | `main.tex` Author contributions | 4 Nov | Yes |

## Claude, once the answers are in

| # | TODO | Where | Due |
|---|---|---|---|
| C1 | Implement every answer above, rebuild both PDFs and the cover letter | all | 19-21 Oct |
| C2 | Full bill of materials with part numbers, cables and PCB; firmware-flashing steps; print settings | GUIDELINES-AUDIT R2 | 21 Oct |
| C3 | Cite the software with versions (CadQuery, OpenSCAD, KCL, KiCad, MicroPython, Python libraries) and ISO 8655-6 | R4 | 21 Oct |
| C4 | `CITATION.cff`, `.zenodo.json`, pinned `requirements.txt`, data dictionary, README "how to cite" | R9 | 23 Oct |
| C5 | Commercial comparison table and "hello world" section, if G15 is yes | items 12, 13 | 28 Oct |
| C6 | Figure text at 6-7 pt and photos at 600 dpi, if done now | item 17 | 30 Oct |
| C7 | Strip the `TODO` comments, build the upload ZIP (20 files or fewer), run the RSC submission checker | R10 | 10 Nov |
