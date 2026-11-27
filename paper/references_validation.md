# Reference validation: cited entries

- Date: 2026-11-27
- Scope: the 44 keys cited in `paper/main.tex` and `paper/si.tex` (`paper/cover_letter/cover_letter.tex` cites none). Uncited entries in `references.bib` were not checked or changed.
- Method: every DOI was fetched from the Crossref REST API (`api.crossref.org/works/<DOI>`). The 6 DOIs Crossref does not hold (5 arXiv, 1 Texas ScholarWorks) were fetched from DataCite. Compared: title (case- and punctuation-insensitive, Crossref subtitle included), every author's surname and given name, year, journal or proceedings title, volume, issue, pages or article number. Corrections, errata and retractions were checked in `updated-by`, `update-to` and `relation`. Preprints were searched in Crossref (`query.bibliographic`) for a published version, and the arXiv API was checked for journal references. URLs of `@misc` entries were checked with `curl -sIL` (the YouTube playlist also through YouTube's oEmbed endpoint). The result was run through BibTeX with `rsc.bst`: no warnings.
- Formatting applied to all 40 cited DOI entries (not counted as fixes): authors rewritten as "Surname, Given and ..." from the Crossref/DataCite author records (same names as before except Jansen2023Words), initials spaced (`M.O.` to `M. O.`, which BibTeX had abbreviated to "M."), accents written as LaTeX (`{\'a}`), acronyms and formulas in titles braced, en dash written as `--`. Old "NEEDS MANUAL VERIFICATION" notes were removed from the 4 entries that carried them.
- Counts (44 cited keys):
  - verified, metadata unchanged: 14
  - fixed: 26 (5 with a corrected field, including 2 preprints switched to the published version; 21 that only gained the missing issue number)
  - DOI added: 0 (every cited article and proceedings entry already had one)
  - flagged: 5 (overlaps with the other groups)
  - non-DOI `@misc` entries checked: 4, no dead links

| Key | DOI | Status | Change or reason |
|---|---|---|---|
| Abolhasani2023Rise | 10.1038/s44160-022-00231-0 | fixed | number added: 6 |
| Alrashedy2025Generating | 10.48550/arXiv.2410.05340 (DataCite) | fixed | year 2025 to 2024 (DataCite publicationYear; arXiv v1 2024-10-07, v2 2025-02-28). No published version in Crossref |
| Alsenz2011Powderpicking | 10.1016/j.powtec.2011.02.014 | fixed | number added: 1-3 |
| Badagabettu2024Query2cad | 10.48550/arXiv.2406.00144 (DataCite) | verified | No published version in Crossref. Third author written "Barati Farimani, Amir", as in his publisher records in Crossref (the arXiv record splits it "Farimani, Amir Barati") |
| Baird2026Honegumi | 10.1038/s41524-026-02156-0 | fixed | number added: 1 |
| Besenhard2015Accuracy | 10.1016/j.ejpb.2015.04.037 | verified | Formatting only (initials M. O., S. M., J. G. now print) |
| Besenhard2017Micro | 10.1016/j.ijpharm.2016.12.029 | fixed | number added: 1-2 |
| Canty2025Science | 10.1038/s41467-025-59231-1 | fixed | number added: 1 |
| Charles2026Release | none | non-DOI, flagged | github.com/vertical-cloud-lab/powder-doser answers 200. The note "DOI to be assigned when the release is archived at submission" prints in the reference list: add the Zenodo DOI before submission. Unchanged |
| Chen2020Elemental | 10.3390/ma13163562 | verified | Formatting only |
| Chianrabutra2014Powder | 10.26153/tsw/15662 (DataCite) | verified | Title, authors and year match DataCite; DataCite has no proceedings title or pages, so the booktitle could not be checked. Old note removed; initials B. G. now print |
| Engisch2012Method | 10.1016/j.powtec.2012.05.058 | verified | Formatting only |
| Engisch2015Feedrate | 10.1016/j.powtec.2015.06.001 | verified | Formatting only |
| Faulhammer2014Dose | 10.1016/j.ijpharm.2014.07.050 | fixed | number added: 1-2 |
| Fei2024Alabos | 10.1039/D4DD00129J | fixed | number added: 11 |
| FusionPlaylist | none | non-DOI, flagged | Playlist URL answers 200 and oEmbed confirms a public playlist, but its YouTube title is "Powder Doser" (BYU Vertical Cloud Lab channel), not "Human redesign of AI-made parts" as in the entry. Unchanged |
| Guzik2023Decade | 10.1039/d3dd90001k | fixed | number added: 1 |
| Hanson2018Control | 10.1016/j.powtec.2018.03.027 | verified | Formatting only |
| Hohlbein2022Open | 10.1038/s41592-022-01602-3 | fixed | number added: 9 |
| Jansen2023Words | 10.48550/arXiv.2305.14874 to 10.18653/v1/2023.findings-emnlp.864 | fixed, preprint to published | `@misc` (arXiv) to `@inproceedings`: Findings of the Association for Computational Linguistics: EMNLP 2023, pp. 12972-12990, 2023; url added; author "Peter Alexander" to "Peter" (Crossref and DataCite) |
| Li2018Combinatorial | 10.1557/jmr.2018.214 | fixed | number added: 19 |
| Maffettone2023What | 10.48550/arxiv.2304.11120 to 10.1039/d3dd00143a | fixed, preprint to published | doi and url switched from arXiv to the Digital Discovery article (journal, volume, pages, year and all 19 authors already matched it); number 6 added; old note removed |
| Mooraj2024Additive | 10.1038/s43246-024-00452-0 | fixed | number added: 1 |
| Moorehead2020Throughput | 10.1016/j.matdes.2019.108358 | verified | Formatting only |
| Nelaturu2024Multi | 10.1016/j.msea.2023.145945 | verified | Formatting only |
| NoteRepository | none | non-DOI | github.com/vertical-cloud-lab/powder-doser answers 200. Unchanged |
| Pearce2020Economic | 10.1016/j.ohx.2020.e00139 | verified, flagged | Crossref lists an erratum: 10.1016/j.ohx.2021.e00235, "Erratum regarding previously published articles" (HardwareX 10, e00235, 2021), one notice covering 12 HardwareX articles |
| Rios2023Text | 10.1109/ssci52147.2023.10371898 | verified | Formatting only |
| Seff2021Vitruvion | 10.48550/arXiv.2109.14124 (DataCite) | verified, flagged | arXiv journal reference "ICLR 2022"; the ICLR version has no Crossref record, so the arXiv entry was kept |
| Seifrid2022Autonomous | 10.1021/acs.accounts.2c00220 | fixed | number added: 17. "Morgan Chan" now parsed as the surname (printed "Z. M. Chan" before) |
| Stirling2022Hardops | 10.1080/0951192x.2022.2028188 | fixed | number added: 12 |
| Subbaraman2024Duckbot | 10.1371/journal.pone.0296717 | fixed | number added: 1 |
| Szymanski2023Autonomous | 10.1038/s41586-023-06734-w | fixed, flagged | number added: 7990; old note removed. Crossref lists an Author Correction: 10.1038/s41586-025-09992-y (Nature 650, E1, 19 Jan 2026) |
| TextToCad | none | non-DOI | github.com/earthtojake/text-to-cad answers 200. Unchanged |
| Tom2024Self | 10.1021/acs.chemrev.4c00055 | fixed | number added: 16; old note removed |
| Vasquez2020Jubilee | 10.1145/3313831.3376425 | verified | Formatting only ("Tran O'Leary" now parsed as the surname; printed "J. T. O'Leary" before) |
| Vecchio2021Throughput | 10.1016/j.actamat.2021.117352 | verified | Formatting only |
| Wenzel2023Open | 10.1371/journal.pbio.3001931 | fixed | number added: 1 |
| Willis2021Fusion | 10.1145/3450626.3459818 | fixed | title "Fusion 360 gallery" to "Fusion 360 Gallery: a dataset and environment for programmatic CAD construction from human design sequences" (Crossref title plus subtitle); number 4 added |
| Wu2021Deepcad | 10.1109/ICCV48922.2021.00670 | fixed | booktitle "Proceedings of the IEEE/CVF International Conference on Computer Vision (ICCV)" to "2021 IEEE/CVF International Conference on Computer Vision (ICCV)" |
| Xu2024Brepgen | 10.1145/3658129 | fixed | number added: 4 |
| Yang2007Metering | 10.1016/j.powtec.2007.04.004 | fixed | number added: 1 (initials J. R. G. now print) |
| Yoshikawa2023Pipette | 10.1039/d3dd00115f | fixed | number added: 6 |
| Yoshikawa2026Commit | 10.1039/d5dd00336a | fixed | number added: 1 |
