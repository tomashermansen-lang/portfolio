# Requirements, in EARS form

Derived from the prototype. Every requirement is in one of the five EARS
patterns (Mavin et al., 2009): ubiquitous (shall), event-driven (When), state-driven
(While), unwanted behaviour (If … then), optional feature (Where). Each has an id;
the scenarios in `spec/features/` carry the ids they cover as tags, and
`spec/spec-results.json` records which scenarios passed on the last run. A
requirement that is specified and not built has a scenario tagged pending; the
traceability table shows it as pending, never as passed.

Two parts. Part A is the product: every requirement there belongs to a story in
`spec/stories.json`. Part B is the page you are reading, the exhibit that carries
the prototype: recordings in place of calls, notes to the reader, what the page
must and must not claim. Part B is not product scope; it is kept because the
page's tests need it. An id, once given, is never reused.

# Part A. The product

## 1. The table and its terms

- **R-01** The system shall define exactly twelve terms, each with an id, a label and a one-sentence definition, in one file (`spec/terms.json`) that is both the extractor's instruction and the page's column explanation.
- **R-02** The system shall present every term in the order of that file wherever the twelve are listed in full.

## 2. The data room

- **R-03** The system shall mark every synthetic document with the header line "Synthetic document, written to demonstrate a method. Fictional parties and figures. Not a real contract and not legal advice."
- **R-04** The system shall hold every contract document to its answer key: each keyed quote present verbatim, each forbidden word absent, no real company named, 5,000 to 6,500 words.
- **R-05** If a document fails any rule in R-04, then the validator shall report the document and the rule and exit non-zero.

## 3. Extraction (the model run)

- **R-06** When a document is extracted, the extractor shall send the whole document, one instruction and the twelve term definitions in a single prompt, and shall ask for one JSON object with the fields found, value, quote, clause and note per term.
- **R-07** When the model reports a term as found, the record shall contain a value, a quote and a clause for that term.
- **R-08** When the document does not address a term, the record shall mark the term not found, with a note saying so, and shall not fill the term from industry practice.
- **R-09** If a term is defined only by reference to a document that is not attached, then the record shall mark the term not found and the note shall quote the reference.
- **R-10** The extractor shall store with every record the model name, the time of the run, the run number and the SHA-256 of the document text.
- **R-11** When a run is started, the extractor shall store its records under a run number that no earlier run used.
- **R-12** The extractor shall keep the raw model reply beside the parsed record, so a parse failure can be read.

## 4. Evaluation against the key

- **R-14** When a run is scored, the evaluator shall judge every term of every contract as one of: correct, missed, invented, wrong_value, quote_not_verbatim.
- **R-15** The evaluator shall count a term as correct only when the key's figures (numbers, number words and dates) are all present in the model's value and the quoted sentence is in the document.
- **R-16** While the key marks a term absent, the evaluator shall count the term correct only when the model reported it not found.
- **R-17** When a quote is verbatim but is not one of the sentences the key names, the evaluator shall still count the term correct and shall record that the source differs from the key.
- **R-18** While more than one run is recorded, the evaluator shall count per term how many runs judged it correct, and the page shall show that count beside the term.
- **R-19** When a committee paper or a legal summary on file is scored, the evaluator shall judge whether the extraction repeated the paper's planted figures as the paper states them (faithful / not_faithful). This is evidence for the trial; the papers are not part of the product's steps.

## 5. Deterministic checks

- **R-20** The checks shall use the Python standard library only and no file access, so that one file runs unchanged on the desk and in the browser.
- **R-21** When a record marks a term found, the checks shall confirm the quoted sentence is in the document with whitespace and curly quotes normalised, and shall raise a finding if it is not.
- **R-22** When a note, clause or value cites a section, annex or part, the checks shall confirm that the cited clause exists in the document, and shall raise a finding naming the citation if it does not.
- **R-23** When a paper on file and the contract both state a figure for the same term and unit, the checks shall raise a finding if the paper's figure is not among the contract's. This check runs on the desk and in the handover's code fold, not in the product's check step.
- **R-24** When two versions of a contract are compared, the checks shall list every term whose figures differ by unit, and every term found in one version only.
- **R-25** When two versions of a contract are compared, the checks shall list the sentences that differ between the two documents without any model involved.
- **R-26** If a record lacks a term, or a found term lacks a value or quote, or a not-found term lacks a note, then the checks shall raise a shape finding for that term.

## 6. The review screen

- **R-27** When the analyst opens a contract, the screen shall list the twelve terms, each as its title on one line with its marks on the line beneath (finding, not found, changed, confirmed, flagged): terms with a finding first, then terms not found, then the rest; a decision shall not move a term.
- **R-28** When a term is selected, the screen shall show the model's answer, the source sentence, the clause, any note, every finding the checks raised on that term, and what changed since the draft.
- **R-29** When a term is selected, the screen shall highlight the source sentence inside the contract's own text and scroll it into view.
- **R-30** If the source sentence cannot be found in the document, then the screen shall say so instead of highlighting.
- **R-31** When a citation in the answer, clause or note is clicked, the screen shall scroll the document to that clause and mark it.
- **R-32** Where a cited clause does not exist in the document, the screen shall show the citation as missing.
- **R-33** When the analyst confirms a term or flags it for review, the screen shall record the decision for that contract and term, show it in the list, and move to the next term without a decision. The screen shall offer no other decision, and no figure shall change by hand.
- **R-34** When the analyst flags a term, the screen shall require a note saying what is wrong and where before recording the decision; the figure shall stay as the model read it.
- **R-35** While decisions exist for a contract, the status line shall show the number of findings, how many terms are reviewed, how many of those are flagged, and the minutes since the first decision.
- **R-37** When the analyst exports, the screen shall produce a CSV with term, answer, source sentence, clause, note, the review (confirmed, flagged or not reviewed) and the review note for every term.
- **R-38** When the final version is open, the screen shall mark the terms whose figures changed since the draft, with the figures before and after.
- **R-38a** While a contract exists in more than one version, the document pane shall offer the versions in a list, and when a version is chosen the pane shall show that version's text with that version's own sentence for the selected term marked, or say that the version does not state the term.

## 7. The committee pages

- **R-39** The committee pages shall open with a summary page: six headline figures, what needs the committee's attention, and page references.
- **R-39a** After the summary the pages shall present the twelve terms in order over as many landscape pages as their full answers need, at most four terms a page, each term with its number, label, the model's full answer and its clause, never a cut sentence.
- **R-39b** The last page shall hold the open points and the changes since the draft, or "one version on file" where the contract has no draft.
- **R-39c** The last page shall say that the listed changes are the figures that changed and that the text differs in N places, and shall never claim that everything else is unchanged.
- **R-40** The committee pages shall list as open points every citation that does not exist in the contract and every term the analyst flagged, each flagged term with the analyst's note.
- **R-40a** On the term pages a row shall carry a mark and a tint only when it deviates: "flagged" when the analyst flagged it, "not reviewed" when no decision is recorded yet; a confirmed row carries no mark. While any term is not reviewed, the first page shall say how many.
- **R-41** The committee pages shall state on every page the model, the run, the date, and how many terms were reviewed.
- **R-42** When the analyst records a decision, the committee pages shall update without a reload.
- **R-43** When the committee pages are printed, they shall print one page each in A4 landscape.
- **R-43a** When the analyst has reviewed every term of the loaded version, the figures shall leave the product in the format the financial model takes, one row per term with the figure, its unit and the reference of the sentence it came from, so that no figure is retyped into the model.

## 8. Measurement

- **R-44** The system shall keep the working data in a SQL database whose schema and seed run unchanged in sqlite3 on the desk and in SQLite in the browser.
- **R-45** The database shall hold a baseline table where every metric states its basis as assumed, measured or not measured, and the value is NULL where not measured.
- **R-46** The database shall hold the figures of every extracted value typed by unit, so the terms can be queried across contracts.
- **R-47** The measurement queries shall report effort per contract (confirmed, flagged, minutes), cycle time to the committee, the terms that need a person, the change against the baseline, and one portfolio question.
- **R-48** If a project has no committee document, then the cycle-time query shall report NULL for that project rather than an invented date.
- **R-49** Every before-figure and every measured figure shown in a business case shall carry its basis beside it: assumed, by rule, measured, or not metered.
- **R-49a** The page after the pilot shall be the business case again, version 2, in the same template as version 1 (the ask, why now, options, evidence, value, risks, out of scope) plus a decision rule: three criteria with a threshold each (terms read right on three real contracts, analyst minutes timed, data terms settled) and, per criterion, where the dry run stands.
- **R-49b** The recommendation of version 2 shall follow from the decision rule and never go beyond the measurements shown; while a criterion has no measurement, the page shall say "not measured · awaiting the pilot" and make no build recommendation.
- **R-49c** Every cell in the pilot's column of version 2 shall say "awaiting the pilot" until the pilot measures it, with any dry-run figure shown apart and marked generated or by rule.
- **R-49d** Version 2 shall state the dry-run status in its head and its foot.

## 9. Continuous evaluation

The score of one run says how the method did once. These requirements say how it
is kept honest after the first run, when the prompt, the term definitions, the
model or the documents change.

- **R-54** The answer key shall be versioned: every entry shall carry the date it was written or last changed, and the evaluation shall record which key version it scored against. The key shall have a named owner, the unit's product manager, who approves every change to it.
- **R-55** When the prompt template, the term definitions or the model change, the system shall record a new run and score it before the change is used for any document a reader sees.
- **R-56** When a run is scored against an earlier run on the same key, the evaluation shall report per term whether the verdict improved, regressed or stayed, and the change shall not be accepted while any term regressed from correct to another verdict without a written reason.
- **R-57** The system shall keep at least three recorded runs of the current prompt and model, so that stability per term is a count and not a single observation.
- **R-58** When a term is wrong in every recorded run, the system shall treat it as a definition or prompt defect and shall not treat it as model noise.
- **R-59** When a term is wrong in some runs and right in others, the system shall route it to a deterministic check or to the reviewer, not to a prompt change.
- **R-60** When a reviewer flags a term, the flag and its note shall become a candidate change to the answer key for that document, with the reviewer named and the date, so that the key grows from reviewed work.
- **R-60a** A reviewed contract shall enter the evaluation suite only after a person has written its key without the model's answer in front of them, and the key shall record who wrote it and when. A reviewer's confirmation of the model's answer shall never by itself become a key entry, so the model is never scored against its own output.
- **R-61** Before the method is used on a real contract, it shall have been scored on at least one real contract of comparable length with a key written by a person who read it, and the score shall be reported beside the synthetic score.
- **R-61a** The evaluation suite shall grow until it holds at least one keyed real contract for every contract form, counterparty type and language in the pipeline, and the evaluation report shall list the forms, types and languages that have no keyed contract yet.
- **R-62** While the method is in operation, a sample of extractions shall be re-read by a person each month, the share found wrong shall be recorded as the operational error rate, and the rate shall be shown beside the synthetic score wherever that score is shown.
- **R-63** The system shall record the cost of every run (tokens and price per document), so that cost per contract is reported beside minutes per contract.
- **R-63a** Where a term's value is words rather than figures (who may curtail, what happens on delay), a model may judge whether the extracted wording means the same as the key's; before any such judgment counts in a score, the judge shall have been calibrated on a sample against the judgments of a person who read the contract, and its agreement rate shall be reported beside the score.
- **R-64** The evaluation report shall show the results for every recorded run, never only the best one.

## 10. Cases and the five steps

- **R-65** The product shall open on a workbench that lists every case, one per project, with the documents on the case (the contract in its versions), the status of its key terms and its last activity.
- **R-65a** When a case is chosen on the workbench, the product shall open it; when an upload is started, the product shall pick a file from the data room and open a case on it.
- **R-65b** Inside a case the product shall show the five steps, load, analyse, check, review, committee pages, in that order and in one frame.
- **R-65c** Each step shall have one action of the product, enabled only when the step before it has run, and the status of every step shall be visible in the frame's bar.
- **R-65d** Each step from load to review shall carry a Next control beside its action, in the same place on every step, enabled once that step's action has run.
- **R-66** When the analyse action runs, the product shall show the run as its activity log, shall name the model, the run and the date, and shall then show the twelve terms with their answer and clause. A skip control shall end the display of the log at once.
- **R-67** When the check action runs, the product shall show the checks on the contract as the activity log (quotes verbatim, citations exist, changes since the draft), count the findings for the chosen contract, and every finding shall appear as a flag or a change mark on the analyst's list in the review step. The check of the papers on file against the contract runs on the desk, not in the product's check step.
- **R-70** The status of a case shall belong to the case, not to the session, and shall follow the contract version loaded on it: the workbench shall show, per case, not read, loaded, analysed, the number of findings, the number of terms reviewed, or pages ready, as far as the case has come.
- **R-70b** Choosing another version of the contract shall keep the case as one row and start its status again from loaded; switching between cases shall keep each one's state.

## 11. KPIs the pilot measures

Each figure the business case promises is a requirement here, with where it is
measured, where it is stored (`sql/schema.sql`) and where it is shown. The
prototype builds the shape; the pilot replaces the generated figures with
measured ones.

- **R-75** The system shall record analyst minutes per contract, timed from the load of the contract to the last decision on it, stored per term in the reviews table (minutes) and shown as the Value row "Analyst minutes" of business case v2 and in the effort query. Built in the prototype as fixed minutes per term (by rule); the timing is specified, not built.
- **R-76** The system shall record the days from the data room to a reviewed table, dated from the data-room event to the last decision, stored in the events table and shown as the Value row "Days to a table" of business case v2 and in the cycle-time query. Built in the prototype from the documents' own dates (assumed); the dating is specified, not built.
- **R-77** The system shall count per contract the terms confirmed as read and the terms flagged, from the reviews table, and show them in the effort query and in the "Why now" line of business case v2. Built in the prototype: the screen records the two decisions in the tab, the database holds a generated log.
- **R-78** The system shall count per contract the findings of each check, from the checks table, and show the count in the check step and in the query on the terms that need a person. Built in the prototype.
- **R-79** The system shall record the model cost per contract, tokens and price from the run record, stored with the extraction and shown as the Value row "Model cost" of business case v2. Specified, not built: the run records carry no token counts (see R-63).
- **R-80** The system shall record the operational error rate per month, the share of a re-read sample found wrong, stored in the baseline table with basis measured and shown in the Evidence table of business case v2 beside the synthetic score. Specified, not built (see R-62).
- **R-81** The system shall report the terms read right per run against the key, from the evaluation, and show it as the Evidence row "Terms read right" of business cases v1 and v2. Built in the prototype.

## 12. Technical requirements, and what is left to a solution architect

What the prototype has decided is a requirement. What it has not decided is
listed as an open decision with the constraint it must respect, for the
solution architect who joins at the pilot. Nothing here is built.

- **R-83** The solution shall send documents only to a model deployment whose terms security and legal have settled: no training on the data, a stated retention, a named region. Decided: the constraint. Open for the architect: the provider and the deployment (the firm's own cloud tenancy or a provider contract).
- **R-84** The solution shall read contracts from the firm's data room or document store through its existing access control, never by copying files out of it. Open for the architect: the integration.
- **R-84a** The solution shall put the cases, the extractions and the review log behind the firm's identity provider. Decided: access to a case, its extractions and its review log follows the person's access to the deal in the document system; a person without access to the deal does not see that the case exists. Open for the architect: the identity provider.
- **R-85** The solution shall keep every extraction, check result and review decision in a database the firm already operates, in the schema of `sql/schema.sql` or a migration of it. Open for the architect: the database, hosting and backup.
- **R-86** The solution shall pin the model version and the prompt version on every record, so a change in either is visible in the evaluation. Decided. Open for the architect: how model updates from the provider are received and gated.
- **R-87** The solution shall log every model call with its cost, and shall stop calling the model when a monthly cost ceiling set by the unit is reached. Decided: at the ceiling the analyst on the case is told that the contract waits for the next month or a raised ceiling, and reads it herself meanwhile; the unit's product manager is notified. Open for the architect: the alerting mechanism.
- **R-88** The solution shall return a read contract to the analyst within ten minutes of upload for a contract of up to 130 pages, and shall tell the analyst when it takes longer. Open for the architect: queueing and what runs in parallel.
- **R-89** The solution shall keep an audit trail of who confirmed or flagged which term, when, on which document version, readable without the application. Decided: the reviews table and the CSV export, kept as long as the firm keeps the committee material it fed. Open for the architect: the mechanism that enforces the retention.
- **R-90** The solution shall run the three contract checks and the evaluation in a standard runtime with no dependency beyond the standard library and SQL, so the firm can run them on any machine. Decided.

## 13. Intake, security, robustness and lifecycle

What a solution architect asks first, written as requirements after an external
review of the page (2026-10-31). Each says what is decided and what is left to the
architect, as section 12 does. Nothing here is built; R-92 and R-94 are shown by
the prototype.

- **R-91** When a contract is loaded, the system shall extract its text from PDF or DOCX, keep the page number of every sentence, and reject a document whose text layer is missing or whose annexes named in the body are not attached, naming them. Decided: the requirement. Open for the architect: the extraction tool.
- **R-92** While any term of the loaded version is not reviewed, the committee pages shall carry the word DRAFT on every page and shall not be printable or exportable. Decided; the prototype does it.
- **R-93** The solution shall send no more than the contract text and the twelve definitions to the model, and shall record per call what was sent. Decided. Open for the architect: where the record of what was sent is kept.
- **R-94** The review log shall be append-only: every decision is a new row with the document hash, the term, the reviewer, the time and the outcome; no row is updated or deleted, and the current decision is the latest row. Decided; the schema does it.
- **R-95** If a model call fails or its reply cannot be parsed, then the system shall retry once, and if it fails again shall mark the document "not read" on the case with the reason, visible to the analyst; no case shall silently lack a record. Decided.
- **R-96** When a document is re-read, the system shall record the new run and mark it current for that document version; earlier runs stay on file and are never shown as current. Decided.
- **R-97** When a contract contains text addressed to the model (an instruction, a request to ignore rules), the extractor shall treat it as contract text only, and the data room shall hold one document with such a planted instruction that the eval scores. Decided: the trap. Open for the architect: any provider-side filter.
- **R-98** Access to a case, its extractions and its review log shall follow the person's access to the deal in the document system; a person without access to the deal shall not see that the case exists. Decided, with R-84a. Open for the architect: the identity provider.
- **R-99** The system shall log every read of a review log or an export, with who and when, and the log shall be readable by the firm's audit function without the application. Decided. Open for the architect: where that log lives.
- **R-100** If the document system or the model is unavailable, then the case shall show which step cannot run and why, and the analyst shall still be able to open the last reviewed table. Decided.
- **R-101** The term definitions and the prompt template shall carry a version; when either changes, every extraction made with the earlier version shall be marked stale on its case until re-read, and rollback shall mean pinning the previous version. Decided. Open for the architect: how a provider's model update is received.
- **R-102** When the monthly cost ceiling is reached, the system shall stop calling the model, shall tell the analyst on the case that the contract waits for the next month or a raised ceiling, and shall notify the unit's product manager. Decided, with R-87. Open for the architect: the queue and the alerting mechanism.
- **R-103** The operational error rate shall have a named owner in the unit, the product manager; while it exceeds a threshold set in the business case, the committee pages shall carry a warning and the owner shall decide whether the method stays in use. Decided: the owner and the consequence. Open: the threshold, set in business case v2 from the pilot's figures.
- **R-104** The regression suite shall run before every release of the prompt, the definitions or the model, in the firm's pipeline; a regression from correct blocks the release until the product manager writes the reason in the release record. Decided. Open for the architect: the pipeline.
- **R-105** The handover shall say which scenarios carry over: the file-level scenarios (extraction, data room, scoring, checks, measurement, continuous evaluation) are the build's regression suite unchanged; the screen scenarios are rewritten against the house's test runner. Decided.
- **R-106** When a new version of a contract is loaded, the decisions on the earlier version shall be kept and shown as made on that version; on decommissioning, every case shall be exportable as one JSON file with its documents' hashes, extractions, checks and review log. Decided.

# Part B. This page, not the product

Requirements on the page you are reading, kept because its tests need them. They
are not product scope. The page is a public exhibit of the prototype: it carries
no key, calls no model and sends nothing to a server, so wherever the product would
call out, the page plays a recording and says so.

## B1. Recordings and what runs here

- **R-13** The page shall never call a model; it shall show recorded runs only, and wherever a run is replayed the note under the frame shall say so.
- **R-36** The page shall keep the analyst's decisions in the browser tab only; nothing shall be sent to a server.
- **R-50** The page shall show, for each thing it can run, the file that runs, as it is on disk.
- **R-51** Where a live run depends on a large download, the page shall offer a recording of the same run first and the live run as the option.
- **R-52** When a recording is replayed, the page shall say so on the first line and shall not claim that anything ran in the browser.
- **R-50a** The page shall show the scorer, `tools/evaluate.py`, as it is on disk in the eval fold, and shall replay its recorded run of scoring run 1 against the answer key; a live run of the same file in the browser shall print the same lines.

## B2. The prototype's frame on the page

- **R-65e** The worked example (steps one to three completed) shall be offered in the page's note under the frame, not inside the product.
- **R-66a** When the analyse action runs on the page, the activity log shall be the recorded run of the chosen contract, and the note under the frame shall say that the call is a recording and that no model is called from the page.
- **R-67a** When the check action runs on the page, the activity log shall be the recorded checks on the contract; the live run of all checks stays in the handover's code fold.
- **R-68** Inside the frame the prototype shall use only the product's own words: labels, statuses, the activity log, results, the review screen and the pages. Every sentence addressed to the page's reader, including that a run is a recording and where the code runs live, shall stand in a note under the frame that changes with the step.
- **R-70a** The state of the cases shall live in memory only and start again when the page is reloaded.
- **R-72** When the reader uses the start-over control under the frame, the prototype shall clear every case and every decision, and return to the workbench.

## B3. The page's chapters

- **R-69** The page shall place the handover before the chapter behind the case, with every fold closed by default, so the package takes one screen and the reader reaches the reasoning without scrolling through it.
- **R-69a** The handover shall hold the material a team builds from: the stories with their requirements and acceptance tests, the wireframes, the data, the eval with the key, the recorded runs and the score, the code that runs, what is left open, the files. The reasoning, what was assumed and decided, shall sit behind the case.
- **R-73** The handover shall list the stories from `spec/stories.json` as the product backlog derived from the prototype: each story names its epic, its phase (pilot or build) and its priority (must, should or could), and links to its requirements by R key and to its scenarios by S key, or says where they will be written.
- **R-73a** Each story shall show a prototype status derived from the last spec run: Shown when every linked scenario passed, Partly when some did, Not built otherwise.
- **R-73b** The stories table shall filter by phase, epic and prototype status, and sort by epic, priority or phase.
- **R-73c** Every requirement of Part A shall belong to at least one story, so the stories are the traceability; the page shall list any that does not.
- **R-73d** The discovery shall be closed above the table by a list of what it delivered, not by stories.
- **R-74** The wireframes in the handover shall be drawn by `tools/wireframes.py` for the screens the prototype has (the workbench, a step panel, the review screen, a committee page) and shall carry no data.
- **R-82** Every scenario shall carry a stable key, the tag `@S-nn`, given once in page order and never renumbered; the key is the scenario's identity, the name may change. Both runners shall carry the key into the results, and the page shall show it before the scenario name.
