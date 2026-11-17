# Digital Discovery submission audit

> **Status, 10 Oct 2026 (same session).** Done in the manuscript: author spelling "Carl Robison" (B11, from Sterling's 21 Jun note on PR #103); AI-use statement in the RSC wording with tools and models (B6); a Safety subsection with hazard warnings (B1, hazards only: the precautions the team used still need a human); the seven broken references (B9); "A&D HR-100A" dropped from Fig. 1e (R6); -ise to -ize and PLA defined (R8); CRediT role names (R5). Also corrected, from the same 21 Jun note: S.G.B. is not on the DD Advisory Board, there is no NASA Space Grant funding (sentence removed), S.G.B.'s second affiliation (Acceleration Consortium, University of Toronto) is added, and the abstract links the repository. The cover letter (B10) is in `paper/cover_letter/`. Everything that needs a human is in [`SUBMISSION-DECISIONS.md`](SUBMISSION-DECISIONS.md).


This checks `paper/main.tex` and `paper/si.tex` (branch `copilot/draft-base-manuscript`, commit `345bbf0`) against the *Digital Discovery* (DD) author guidelines and the RSC policy pages they link to, as live on 10 October 2026.

The live guidelines page matches the saved copy in `paper/guidelines/` on every requirement (only links and the cover-artwork section moved). Status is one of Met, Partly met, Not met, Not applicable or Needs human. Line numbers refer to commit `345bbf0`. Sources are listed at the end.

---

## 1. Blocks submission

### B1. Safety and hazards: Not met

- **Requirement:** name the hazards of the powders, chemicals and device, and the precautions used, in the Experimental section.
- **Source:** RSC Author responsibilities: "Authors must highlight very clearly, in the experimental details, any hazards or risks associated with the reported work and include appropriate warnings." DD hardware editorial (Hein and Schrier 2024), criterion 4: "a discussion addressing the safety and hazards associated with the construction and operation of the hardware device is expected". DD guidelines: "Any unusual hazards about the chemicals, procedures or equipment should be clearly identified."
- **Evidence:** neither file mentions a hazard, PPE or precaution. The powders are listed at main.tex:232 and in Table 1 (main.tex:236-257), and AIBN and norbornene appear in the glove-box trial (main.tex:337). The repository's own notes say fine Al powders "are flammable" and leave "PPE / housekeeping" as an open question (`docs/candidate-powders.md`).
- **Fix:** add `\subsection{Safety}` to Experimental after main.tex:367. Cover these points:
  1. Gas-atomized AlSi10Mg and -325 mesh silicon are combustible metal dusts (supplier SDSs commonly class fine Si as a flammable solid, H228). The motors, solenoid and electrostatically charged PLA parts are possible ignition sources. State the quantities, ventilation, grounding or antistatic steps, clean-up and extinguisher used, and cite NFPA 484 and NFPA 652 or the institutional procedure followed.
  2. Barium chloride is toxic if swallowed and harmful if inhaled (H301, H332). State the fume hood, gloves, dedicated auger and hazardous-waste disposal.
  3. Fumed silica and the flours are respirable dusts.
  4. In the glove-box trial, AIBN is a self-reactive solid (H242) and norbornene is a flammable solid; say they were handled under the host laboratory's procedures.
  5. The gear mesh and tilt hinge are pinch points: power off before loading or clearing an auger.

  Take the hazard codes from the SDSs of the lots actually used. Add a one-line safety pointer at the start of the SI build guide (si.tex:86-89) and at the Fill step (si.tex:114-118).
- **Needs human:** only the team knows which precautions were actually taken.

### B2. Hardware licence: Not met

- **Requirement:** give the hardware a clear licence, preferably an open-source hardware licence such as CERN OHL. Software should preferably use MIT or Apache.
- **Source:** DD guidelines (Full papers): "a clear license should be provided for the materials and we have a strong preference for open-source hardware licenses, such as the CERN Open Hardware License." Hein and Schrier: "For software elements, we have a strong preference for permissive open source licenses, such as the MIT or Apache license."
- **Evidence:** the only licence is MIT, a software licence, in `LICENSE`. `README.md` has no licence section, and main.tex:407 says only "Hardware designs are released under an open license (see the repository)". Vendor files in `hardware/vendor-files/` carry their own MIT and CC BY-SA 3.0 licences, and the RSC template files are not relicensed (`paper/NOTICE`).
- **Fix:**
  - Add a CERN-OHL-2.0 licence for the hardware files (CAD source, STEP, STL, F3D and KiCad).
  - Keep MIT for the firmware and scripts, and choose a data licence (for example CC BY 4.0).
  - Add a README licence section that says what each licence covers and excludes `hardware/vendor-files/` and the RSC template files.
  - Name the licences in the Data availability statement (main.tex:407).
- **Needs human:** which variant to use (CERN-OHL-P, -W or -S), and which data licence.

### B3. Design files, board files and the design log are not on `main`: Partly met

- **Requirement:** all design files and code must be in a public, persistent repository that referees can reach during review, in editable formats.
- **Source:** DD guidelines: "Referees must have access to the code and data during the peer-review process." and "All design files and software code should be hosted in a public, persistent repository to ensure easy access and longevity. Authors should provide relevant files in an editable format." Hein and Schrier: "authors should provide editable Computed Aided Design (CAD) files in addition to finished 3d models".
- **Evidence:** outside `hardware/vendor-files/`, `main` holds only five CAD files. The following are missing from `main` and from this branch:
  - `DESIGN-LOG.md` (PR #74), cited at main.tex:188, 381 and 407.
  - `cad/full-assembly/` with the Fusion 360 STEP files and `BOM.md` (PR #170), cited at si.tex:133, 163 and 170.
  - `cad/auger-geared/`, cited at si.tex:207.
  - The AI-modelled bracket, tap collar, mounting plate, baseplate and servo gear. main.tex:357 says they are "in the repository", but they are spread over at least nine other branches.
  - The custom PCB layout and Gerbers, and the "wiring guide" (main.tex:360). Only candidate layouts exist, on other branches. The schematic is on `main`, at `hardware/kicad/`.

  In addition, si.tex:112 points to the schematic in `hardware/test-module/`. The Onshape document is still flagged private (main.tex:402, si.tex:82). The Fusion 360 links (si.tex:140-153) are shares from a BYU Autodesk account and are not persistent.
- **Fix:** before tagging a release:
  - Merge PR #74 and PR #170.
  - Copy the AI-modelled CAD (source, STL and renders) from its branches into `main`.
  - Add the files of the PCB actually built and a wiring diagram.
  - Export an `.f3d` and a STEP file of every Fusion part into the repository.
  - Make the Onshape document public.
  - Correct the paths at si.tex:112, 133, 163 and 207.

### B4. Zenodo DOIs and code version in the Data availability statement: Not met

- **Requirement:** the DAS must give DOIs for the archived version and for the latest (all-versions) record of the code, plus the version used.
- **Source:** DD guidelines: "DOIs for both the most recent and archived versions of the software or code referenced in the manuscript must be included in the DAS submitted at acceptance." RSC DAS template: "The code for [description of software] can be found at [URL to code location] with [DOI – see guidelines below for citing software and code]. The version of the code employed for this study is version [XXX]."
- **Evidence:** main.tex:407 says a release "was archived on Zenodo with a DOI", but no archive exists yet. The reference is a placeholder ("DOI to be assigned when the release is archived at submission", references.bib:3429-3435), printed as ref. 41. No version is given.
- **Fix:** after B2, B3 and B5, tag a release (for example v1.0.0), archive it through Zenodo's GitHub integration, and rewrite main.tex:407 as below. Format the reference using the RSC code-citation pattern: "[Name of code creators, format: A. Name, B. Name and C. Name], [Year], [Name of code repository / type of code], [DOI, or URL if not available – in the instance where code has been deposited in GitHub and Zenodo, as per the guidelines above, the Zenodo DOI is preferred for bibliographic references]". DD only requires the archive by acceptance, so if you wait, change "was archived" to "will be archived".

  Draft DAS, built from the RSC templates:

  > Data for this article, including the raw test-protocol records, the per-dose record, the design log and the AI interaction logs, are available at Zenodo at https://doi.org/10.5281/zenodo.[VERSION]. The code for the doser firmware, the parametric CAD models and the analysis scripts can be found at https://github.com/vertical-cloud-lab/powder-doser with DOI https://doi.org/10.5281/zenodo.[VERSION] (all versions: https://doi.org/10.5281/zenodo.[CONCEPT]). The version of the code employed for this study is version [v1.0.0]. Hardware design files are released under [CERN-OHL-x-2.0], code under the MIT licence and data under [CC BY 4.0]. The assembled design is also a public Onshape document (https://cad.onshape.com/documents/ae9f107d3972fc9d390e541f). The data supporting this article have also been included as part of the Supplementary Information. References cited in the SI are listed in this article's reference list.

### B5. AI interaction logs are not archived, and many have already expired: Partly met (urgent)

- **Requirement:** provide log files of the LLM inputs and outputs, with model identifiers and dates.
- **Source:** DD guidelines (LLM use for inference), which say authors "are required to": "Provide log files that include the inputs and outputs used in their study." and "Specify the model identifier and generation date when using commercial LLMs."
- **Evidence:**
  - main.tex:373 says "the complete prompt and response history (issues, pull-request threads, agent session logs, and Zoo Design Studio transcripts) is public in the repository".
  - Issue threads, pull-request threads and discussion #39 live on GitHub, not in the git tree, so a Zenodo snapshot will not contain them. The Zoo and CADSmith transcripts are only "on their branches" (si.tex:510-512).
  - On 10 October 2026 the GitHub API returned "410 Gone" for the Actions logs of runs from 20 May, 1 July and 11 July 2026, but still served logs from 15 July and 25 September. So the Copilot session logs (April to June, when the AI parts were modelled) are gone, and later logs expire after 90 days.
  - Model names and months are given (SI Table S11), which meets the second point as far as the records allow.
- **Fix:**
  - Download the remaining Actions logs now.
  - Export all issues, pull requests (with review comments) and discussions, for example with `gh api` to JSON plus a Markdown copy.
  - Collect the Zoo and CADSmith transcripts from their branches.
  - Put all of this in an `ai-logs/` folder of the release.
  - Reword main.tex:373 and si.tex:497-518 to say what is archived, and that GitHub deleted the session logs of agent runs before mid-July 2026 under its 90-day retention. Their prompts (issue and review text) and outputs (commits, renders and STLs) remain.

### B6. AI-use disclosure for writing, figures and references: Partly met

- **Requirement:** declare GenAI use in the cover letter. Describe how it was used, including prompts, in Experimental. Name the tools and specific models in the Acknowledgements.
- **Source:** RSC Author responsibilities, "Artificial Intelligence: disclosure and transparency": "If GenAI tools have been used when generating any part of the manuscript (for example when drafting text, translating content, formatting data, creating or editing figures, visualising results, refining code, or compiling references) this must be declared at submission within the cover letter. Authors should also include a statement within the Experimental/Materials and Methods section outlining how the tool was used, including prompts. Details of the AI tool such as the name and specific model or version (e.g., GPT-4 or Claude 3.5 Sonnet) should be included in the Acknowledgements section." The policy recommends this Acknowledgements statement, verbatim: "During the preparation of this manuscript/study, the author(s) used [tool name, version information] for the purposes of [description of use]. The authors have reviewed and edited the output and take full responsibility for the content of this publication."
- **Evidence:**
  - Experimental covers AI for CAD in detail (main.tex:372-373), but mentions writing only inside a commit count ("including those for firmware, analysis, and writing").
  - The Acknowledgements (main.tex:414) do disclose AI drafting and revision of the text. But they name only "Claude-family models", lack the responsibility sentence, and do not mention the Zoo Text-to-CAD API or Copilot code review, both listed in SI Table S11.
  - There is no cover letter yet (B10).
- **Fix:**
  1. Replace the AI sentences in main.tex:414 with this draft (models from SI Table S11):

     > During the preparation of this study and manuscript, the authors used the GitHub Copilot coding agent (GitHub; Claude Opus 4.7 and Opus 4.8 for most tagged requests, and Claude Haiku 4.5, Sonnet 4.6 and Fable 5 for a few; April to July 2026), Claude Sonnet 4.6 in a local Claude session (April 2026) and Claude Code (Anthropic; Claude Opus 4.8, Opus 5, Opus 5.5, Fable 5 and Fable 5.1; June to October 2026) for the purposes of writing CAD code, firmware, analysis and figure scripts, and drafting and revising the text of the manuscript and SI; Edison Scientific (Literature, Analysis and Precedent jobs) for literature searches, compiling references and mock reviews of designs, data and drafts; CADSmith, the Zoo Text-to-CAD API (kcl model 0.1.0) and Zoo Design Studio (Zookeeper agent) for text-to-CAD modelling; and GitHub Copilot code review for automatic pull-request reviews. The authors have reviewed and edited the output and take full responsibility for the content of this publication.

  2. Append this draft to main.tex:373 (confirm before use):

     > AI tools were also used to prepare this paper. Claude Code wrote the analysis and figure scripts and drafted and revised the text of the manuscript and SI, in response to team members' requests and review comments in the manuscript pull request (#97) and linked issues; the Copilot agent wrote early drafts of some documents. Edison Scientific ran literature searches and mock reviews of drafts, and each reference was checked against its DOI record (`paper/references_validation.md`). The prompts are those requests and comments, and the outputs are the agents' replies and commits, all archived with the release. The authors checked every reported number against the data and reviewed and edited all text.

  3. Declare the AI use in the cover letter (B10).

### B7. Comparison with existing alternatives: Partly met

- **Requirement:** compare the doser with commercial and do-it-yourself alternatives on at least capabilities, cost, adaptability and construction time, and say where it is the better or worse choice.
- **Source:** Hein and Schrier, criterion 2: "This comparison should encompass, at a minimum, an analysis of capabilities, cost, adaptability, and construction time". Hardware articles "must address four criteria".
- **Evidence:**
  - Cost is compared (main.tex:165, 177 and 346) and adaptability is argued (main.tex:346).
  - Printing time is given ("under 24 h", main.tex:346), but not assembly or wiring time.
  - There is no side-by-side comparison of accuracy, dose range or time per dose.
  - The price ranges have no direct source: "tens of thousands to several hundred thousand dollars" (main.tex:165) and "quoted at $30k--$300k" (main.tex:346).
  - Relevant sources are already in references.bib but uncited: Bahr2018Collaborative and Bahr2020Recent (commercial dispensing platforms), Jiang2023Autonomous, Radulov2025Flip, Takahashi2025Flexible and Valle2024Pellet.
- **Fix:** add a comparison table to the SI, with a sentence in Cost and accessibility (main.tex:344-346). Include 2-3 commercial systems and 2-3 robotic or open alternatives, with columns for dose range, accuracy, time per dose, powders handled, price, build time and licence. Give a source for each price and the doser's total build time (printing, assembly and wiring).

### B8. A minimal "hello world" first test: Partly met

- **Requirement:** a short first experiment that tells a builder whether the doser works.
- **Source:** Hein and Schrier, criterion 4: "Authors must provide a minimal "hello world" style example experiment to illustrate the device's capabilities, serving as an initial test for readers who have replicated the hardware."
- **Evidence:** the SI build guide ends with "run the firmware self-test (rotate, tap, tilt, tare, and read), then the test protocols listed in the main text" (si.tex:119-120), with no expected results.
- **Fix:** replace si.tex:119-120 with a short "First test" subsection with three steps:
  1. Load table salt and run protocol C at 22.5°. Expect about 146 mg per revolution (Table 1).
  2. Dose 1.000 g. Expect it to finish within ±50 mg in a few minutes.
  3. Give the firmware commands to run, and what to check if a step fails.

### B9. Reference list errors: Not met

- **Requirement:** complete references, with preprints cited by server, year, "preprint", identifier and DOI.
- **Source:** DD guidelines: "arXiv: The citation should include the author(s), the name of the preprint server, the year, the article number and the DOI." Example: "D. Carrascal, L. Fernandez and J. Ferrer, arXiv, 2009, preprint, arXiv:0904.1138, https://doi.org/10.48550/arXiv.0904.1138".
- **Evidence:** in the main.pdf reference list:
  - Ref. 30 prints "NEEDS MANUAL VERIFICATION: DOI returned non-404 but Crossref metadata unavailable." (Wu2021Deepcad, references.bib:3206).
  - Ref. 32 prints the journal as "Text" (Seff2021Vitruvion, references.bib:2643).
  - Refs. 5, 7, 34, 35 and 36 print only "ArXiv, year." with no identifier: Fei2024Alabos (:914), Baird2026Honegumi (:202), Alrashedy2025Generating (:52), Badagabettu2024Query2cad (:160) and Jansen2023Words (:1348).
  - All seven entries still carry the verification note.
- **Fix:**
  - Cite the published versions found on Crossref:
    - AlabOS: *Digital Discovery*, 2024, **3**, 2275-2288, DOI 10.1039/D4DD00129J.
    - Honegumi: *npj Comput. Mater.*, 2026, **12**, 296, DOI 10.1038/s41524-026-02156-0.
    - DeepCAD: ICCV 2021, pp. 6752-6762, DOI 10.1109/ICCV48922.2021.00670.
  - Cite the other four in the arXiv format: arXiv:2109.14124, 2410.05340, 2406.00144 and 2305.14874.
  - Delete the notes, rebuild, and re-read the list.

### B10. Cover letter: Not met

- **Requirement:** a cover letter addressed to the editor that states why the work matters. It is sent to the reviewers.
- **Source:** DD guidelines: "A cover letter, including a statement of the importance of the work", "Make sure you state the correct journal name", "Address your letter to the relevant Associate Editor or Executive Editor" and "Don't include preferred/non-preferred reviewers in your letter". Co-corresponding authors: "mention this in your comments to the editor and/or cover letter". The AI policy (B6) says GenAI use "must be declared at submission within the cover letter". Author responsibilities ask for "full disclosure ... at the time of submission" of any earlier posting.
- **Evidence:** there is no cover letter in the repository.
- **Fix:** write the letter. Cover:
  - the journal and article type (Full paper, hardware) and why the work matters;
  - the co-corresponding authors (S. Charles and S. G. Baird);
  - the AI-use declaration;
  - (no Advisory Board role to declare: S.G.B. is not on the DD Advisory Board, per his 21 Jun note on PR #103; the old Conflicts sentence saying he was has been removed);
  - public access for referees (repository, Zenodo DOI and Onshape document);
  - earlier public posting (the manuscript PDFs in the public repository, and any conference talk);
  - any related manuscripts under review.

  Keep reviewer names out of the letter.

### B11. Author name spelling: Needs human

- **Requirement:** every author name must be spelled correctly.
- **Source:** RSC Author responsibilities: "Please carefully check the spelling and format of all author names, affiliations and funding information."
- **Evidence:** the TODO at main.tex:120-121 notes that the name is "Carl Robinson" in the paper (main.tex:133, si.tex:24, references.bib:3430) but "Carl Robison" on GitHub.
- **Fix:** confirm the spelling with the author and update all four places.

---

## 2. Recommended

### R1. Show the application to accelerated discovery: Partly met

- **Source:** DD guidelines: "The application of hardware to accelerated discovery should be clearly demonstrated in the manuscript."
- **Evidence:** the case is argued (main.tex:163, 317) and shown qualitatively: the agent-run glove-box trial (main.tex:337) and an 8 g atomizer charge (main.tex:379). No dose is yet part of a closed discovery loop.
- **Fix:** report numbers for the September atomizer charges (target, delivered mass and time), and describe the network and agent interface as the route into a self-driving lab. Add a planner-driven run if one exists.

### R2. Comprehensive bill of materials and build guide: Partly met

- **Source:** DD guidelines: hardware papers "must include detailed supporting information, including a comprehensive bill of materials and a construction guide". Hein and Schrier: it "should enable a typical researcher—notionally a graduate student in chemistry, materials science, or biotechnology—to construct the device."
- **Evidence:**
  - Table S1 (si.tex:40-73) lumps the hardware into "Fasteners (M3), bulk capacitors", but Fig. S1 needs M2.5, M3 and M5 screws, locknuts and wood screws.
  - The PCB is excluded, with no breadboard parts listed, and the balance cable is missing.
  - Wiring is only a pointer to a schematic (si.tex:110-113).
  - There are no firmware-flashing steps, per-part print orientation or build time.
- **Fix:** list every purchased item with part numbers (fold in `cad/full-assembly/BOM.md`), the PCB or its breadboard alternative, and the cables. Add a wiring diagram or pin table, MicroPython flashing steps and per-part print settings to SI Section S2.

### R3. Measurement accuracy, test conditions and powder sources: Partly met

- **Source:** DD guidelines: "The accuracy of primary measurements should be stated." and "Sources of starting materials obtained need not be identified unless the compound is not widely available, or the source is critical for the experimental result."
- **Evidence:**
  - The balance is described only by its readability (0.1 mg, main.tex:177 and 357). Calibration, repeatability and linearity are not given.
  - No temperature or humidity is reported, although barium chloride caked from moisture (main.tex:246).
  - Most powders have no supplier, grade or particle size; only the silicon mesh sizes are given (main.tex:236). Flow depends on these properties.
- **Fix:** state the balance's repeatability and linearity, and how and when it was calibrated (main.tex:357). Report room temperature and humidity if they were logged. Add an SI table of powder supplier, catalogue number, grade and nominal particle size.

### R4. Cite the software used, with versions: Not met

- **Source:** RSC Experimental reporting: "If software was used for calculations and is generally available, it should be properly cited in the references." DD software format: "T. Bellander, M. Lewne and B. Brunekreef, GAUSSIAN 3 (Revision B.05), Gaussian Inc., Pittsburgh, PA, 2003."
- **Evidence:** CadQuery, OpenSCAD, KCL and Zoo Design Studio, CADSmith, Fusion 360, Onshape, KiCad, MicroPython and the Python analysis libraries are named (for example main.tex:193, 357, 360 and 407), but none is cited or given a version. ISO 8655-6 (main.tex:370) is also uncited.
- **Fix:** add versioned references at first mention, and cite ISO 8655-6.

### R5. Author contributions in CRediT terms: Partly met (Needs human)

- **Source:** DD guidelines: "We strongly recommend you use CRediT". RSC Author responsibilities point to the ICMJE criteria, under which every author drafts or critically reviews the work and approves the final version.
- **Evidence:** main.tex:394 uses roles that are not CRediT roles ("CAD review", "hardware fabrication"). Nobody is credited with formal analysis, data curation, visualization or project administration. Only S.C. and S.G.B. have a writing role.
- **Fix:** map the roles to CRediT (for example "CAD review" to Validation, and "hardware fabrication" to Investigation or Resources). Assign the missing roles. Add "writing – review & editing" for every author who reviewed the draft, and confirm that all authors approve the final version.

### R6. Figures: Partly met

- **Source:** DD guidelines: "Images should fit within either single column (8.3 cm) or double column (17.1 cm) width"; "TIFF files, with a resolution of 600 dpi or greater"; "Any text, numerical data or scale bars should be clearly legible"; "Figures including logos, trademarks or brands names ... should not be used."
- **Evidence:** widths are correct (main.tex:181, 197, 285, 305, 329 and 388). The problems:
  - In main.pdf, printed text in Figs. 3-5 is as small as 4.4-5.4 pt, and subscripts are 3.5 pt (pp. 8 and 10). The legend style is 5.8 pt (`make_data_figures.py`).
  - Figs. 1, 2 and 6 are drawn 13.8, 13.4 and 6.9 cm wide and then scaled up, so their photos and renders fall to about 470-500 dpi.
  - Fig. 1b shows a "METTLER TOLEDO" logo, and Fig. 1e names "A&D HR-100A".
  - The hand sketch in Fig. 6a cannot be read at 8.3 cm.
- **Fix:**
  - Make the smallest printed text at least 6 pt (7 pt is safer).
  - Draw each figure at its final width so photos and renders stay at 600 dpi or more.
  - Crop the logo out of Fig. 1b (do not use AI editing), and drop the brand name from Fig. 1e.
  - Enlarge Fig. 6a.
  - Supply separate TIFF or PDF figure files at revision.

### R7. Numbered notes instead of symbol footnotes: Partly met

- **Source:** DD guidelines: "Notes should be numbered using the same numbering system as the references." Symbol footnotes "refer to information such as authors' contributions or additional address information". Online resources take the form "Name of resource, URL, (accessed date)."
- **Evidence:** the in-text footnotes at main.tex:169 and 228 print as *, † and ‡. These are the same symbols already used for the corresponding authors and the SI note. The URLs at main.tex:228 and 352 have no access dates.
- **Fix:** turn the three footnotes into numbered notes ending "(accessed October 2026)".

### R8. Spelling, abbreviations and conclusions: Partly met

- **Source:** DD guidelines: "use one or the other consistently"; "If your abbreviations are non-standard, please include a definition the first time you use them."; "The conclusions should not summarise information already present in the article or abstract."
- **Evidence:**
  - Spelling is mixed. "characterised" (main.tex:312) and "summarised" (main.tex:325, twice at 370, 373) sit beside "characterizes" (main.tex:262), "summarizes" (si.tex:277, 383), "optimization" and "atomized".
  - PLA is not defined at first use (main.tex:177), and neither are CAD, STL or STEP.
  - The first paragraph of the Conclusions (main.tex:377) repeats the abstract.
- **Fix:** use one spelling style throughout, define these abbreviations at first use, and trim main.tex:377.

### R9. Help the DD data reviewer: Partly met

- **Source:** DD guidelines: a data reviewer "verifies that the code is functional and reproduces the reported findings. They also check if the data and/or code are appropriately presented and documented." Hein and Schrier: reviewers "should verify that the files are free of errors (e.g., mesh errors in STL files)".
- **Evidence:**
  - `README.md` is titled "powder-excavator", and its Paper section still describes a "bare-bones" template with `lipsum` text.
  - The analysis scripts (numpy, pandas, matplotlib, Pillow, trimesh, shapely) have no pinned environment.
  - There is no description of the CSV columns.
  - There is no `CITATION.cff` or `.zenodo.json`.
- **Fix:** rewrite the top of the README (name, licence, how to cite, and one command that rebuilds the data figures and SI tables). Add a pinned requirements file, a data dictionary, `CITATION.cff` and `.zenodo.json`. Check every released STL for mesh errors.

### R10. Upload package

- **Source:** DD guidelines: "If using the LaTeX template, please provide us with both the native files and a PDF file" and "a ZIP file containing up to 20 files can be uploaded."
- **Evidence:** compiling main.tex needs 13 graphics plus the `.tex`, `.bbl`, `rsc.bst` and `si.aux` files (the `xr` cross-references, main.tex:39-41), about 17 files in total. The SI needs 17 more. TODO comments remain in the source (main.tex:120-121, 188, 353-356, 400-406 and 410-413; si.tex:82).
- **Fix:** upload one ZIP of 20 files or fewer for the main text, and the SI as a PDF. Delete the TODO comments first.

### R11. Table of contents entry: Not met (due at revision)

- **Source:** DD guidelines: a TOC entry is "required, which should be submitted at the revision stage". The graphic should be at most "8 cm wide x 4 cm high", supplied as "TIFF files, with a resolution of 600 dpi or greater", and contain no logos. The text should be "1-2 sentences long, using a maximum of 250 characters".
- **Fix:** make an 8 x 4 cm graphic that is not a copy of a paper figure. Draft text (215 characters): "Printed parts, a $6 microcontroller and a lab balance dose powders for self-driving labs for under 1% of the price of a commercial dosing head; AI agents modelled the parts one at a time, and every prompt is public."

### R12. Suggested reviewers: Needs human

- **Source:** DD guidelines: "A list of preferred reviewers; should be entered in the manuscript submission system". RSC Author responsibilities: "Authors should not recommend reviewers with whom they have a conflict of interest, for example, a close collaborator or colleague." Reviewers "should not be at the same institute", and "Institutional email addresses should be provided".
- **Evidence:** the AI-scouted list (`paper/mock_review/inputs_r3/17-suggested-reviewers.md`) includes recent co-authors of S.G.B. (for example K. A. Brown on ref. 8; J. Schrier on the 2024 frugal-twin review).
- **Fix:** vet each name for recent co-authorship, institution and diversity, then enter about 4-6 names in ScholarOne with institutional e-mails.

### R13. AI in figures and images: Needs human

- **Source:** DD guidelines: "If using AI tools to help create figures, authors must confirm that the AI tool has been trained using fully licensed datasets and the terms of the licence to use the AI output allow commercial reuse." RSC Author responsibilities: "GenAI or AI-assisted tools must not be used to alter images". Where AI is part of the method, the Experimental section should give the tool's "name, version, and manufacturer".
- **Evidence:** Fig. 2 and SI Fig. S3 show AI-modelled geometry, and the captions say so (main.tex:198, si.tex:203-213). Coding agents wrote the plotting and rendering scripts (main.tex:414).
- **Fix:** decide whether the confirmation applies (it clearly does to Fig. 2 and to any AI-assisted TOC graphic). If it does, check the tools' terms and confirm in the cover letter. Confirm that no photo (Figs. 1b and 6a) was edited with AI. Add each tool's maker to main.tex:373.

### R14. Other decisions only the team can make: Needs human

- **Affiliation:** S.G.B. is listed at BYU Mechanical Engineering only because the notes were empty (`paper/review_2026-10-01/DECISIONS.md`, item 20). RSC asks for "the institution(s) where the majority of the research was conducted", plus all relevant affiliations.
- **Funding:** main.tex:414 names "a Utah NASA Space Grant Consortium undergraduate fellowship" without the holder or award number. RSC says "Declare all sources of funding", and the submission system asks for "Grant/award number".
- **Conflicts:** S.G.B. is not on the DD Advisory Board (his 21 Jun note on PR #103), so that sentence is gone and the statement now reads "There are no conflicts to declare." Still declare any free credits, early access or ties with Edison Scientific, Zoo, CADSmith, GitHub or Anthropic.
- **PCB:** say which board was on the tested rig. If an AI layout tool made it (main.tex:384 hints at this, and SI Table S11 leaves PCB tools out), disclose that.
- **Photo:** confirm who took Fig. 1b. If it was not an author, get permission.
- **Preprint:** RSC allows preprints ("e.g. ArXiv, ChemRxiv"), but they must be disclosed. The manuscript PDFs are already public in the repository.
- **At revision or acceptance:**
  - ORCID: "We require the submitting author to provide an ORCID iD when submitting a revised manuscript".
  - Choose whether to opt into transparent peer review.
  - Choose the open-access licence (CC BY or CC BY-NC).
  - Budget the £2,200 APC, and check for a BYU agreement.
- **Before submitting:** run the RSC submission checker.

---

## 3. Already met

| Requirement | Evidence |
|---|---|
| Full paper with no page limit ("there is no page limit for Full papers") | main.pdf is 14 pages: about 7,900 words of text, or 9,700 with captions and tables |
| Scope: "open-source scientific hardware advancing the digitalization of chemistry, materials science, or biotechnology" | Introduction, main.tex:163-169 |
| Short, searchable title | main.tex:130 |
| Abstract is one paragraph of "around 50 to 250 words" | 243 words, main.tex:135 |
| Introduction, Results and discussion, Experimental and Conclusions sections | main.tex:161, 171, 348, 375 |
| Two corresponding authors marked on the first page, with e-mails | main.tex:133, 153 |
| Conflicts of interest statement, before the Data availability statement ("There are no conflicts to declare" form) | main.tex:396-397 |
| Data availability statement placed "after the conflicts of interest statement and before any acknowledgements", with full URLs | main.tex:399-407 |
| References cited in the SI also appear in the main list, and the Data availability statement says so | main.tex:407; si.tex:467, 542-544 |
| SI is a single document with S-numbered sections, tables and figures; data are CSV files in the repository | si.tex |
| LLM model names and months recorded, with gaps stated | SI Table S11 |
| AI is not listed as an author, and AI-modelled geometry is labelled in the captions | main.tex:182, 198; si.tex:168-170, 207-209 |
| Figure widths of 8.3 or 17.1 cm, heights under 23.3 cm, error bars where needed | main.tex:181-388; Figs. 3a and 4 |
| Numbered Vancouver references listing all authors, and DOIs for all cited journal articles in the bib file | main.pdf pp. 13-14 |
| A bill of materials and a construction guide exist (to be completed, see R2) | si.tex:31-182 |
| Human or animal ethics, crystallographic data, industry code restrictions, LLM fine-tuning | Not applicable |

---

## Sources

All pages were fetched on 10 October 2026.

- DD author guidelines (live; matches the saved copy): https://www.rsc.org/publishing/publish-with-us/publish-a-journal-article/digital-discovery
- RSC Author responsibilities (AI disclosure, safety, authorship, conflicts, reviewers): https://www.rsc.org/publishing/journals/processes-and-policies/author-responsibilities
- RSC Guiding principles for AI (refers to Author responsibilities for publishing policy): https://www.rsc.org/publishing/journals/processes-and-policies/guiding-principles-for-artificial-intelligence
- RSC Data sharing (DAS templates, code citation): https://www.rsc.org/publishing/publish-with-us/publish-a-journal-article/data-sharing
- RSC Experimental reporting: https://www.rsc.org/publishing/publish-with-us/publish-a-journal-article/experimental-reporting
- RSC Preparing Supplementary Information: https://www.rsc.org/publishing/publish-with-us/publish-a-journal-article/preparing-supplementary-information
- RSC Processes and policies (ORCID, prior publication and preprints): https://www.rsc.org/publishing/journals/processes-and-policies
- RSC Licences, copyright and permissions: https://www.rsc.org/publishing/journals/processes-and-policies/licences-copyright-and-permissions
- RSC Assessment and review: https://www.rsc.org/publishing/publish-with-us/publish-a-journal-article/assessment-and-review
- RSC Article templates: https://www.rsc.org/publishing/publish-with-us/publish-a-journal-article/article-templates
- J. E. Hein and J. Schrier, "Guidelines for hardware-focused articles", *Digital Discovery*, 2024, 3, 447-448, https://doi.org/10.1039/D4DD90009J. pubs.rsc.org blocks automated requests, so it was read from the Internet Archive copy of the PDF: https://web.archive.org/web/20260501142642/https://pubs.rsc.org/en/content/articlepdf/2024/dd/d4dd90009j
- RSC submission checker: https://submission-checker.rsc.org
- CERN Open Hardware Licence: https://ohwr.org/project/cernohl/wikis/home
- Crossref records used in B9: https://api.crossref.org/works/10.1039/d4dd00129j, https://api.crossref.org/works/10.1038/s41524-026-02156-0 and https://api.crossref.org/works/10.1109/iccv48922.2021.00670
