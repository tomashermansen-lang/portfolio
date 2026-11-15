# Contract terms for an investment committee

A case built to show one method: take the revenue contract of a renewable
energy project, extract the terms an investment committee reads into a
table, show the source line beside every term, leave the field blank where
the contract is silent, and flag where the committee paper disagrees with
the contract.

Everything in `dataroom/` is fictional and says so in its header. The
documents were written for this case after reading the EFET / RE-Source
standard form, three public US power purchase agreements, and what
investors and lenders read (the data fold of the page names them); nothing
is copied from them. The real contracts are not part of this repository.

## Layout

```
dataroom/   six fictional documents, Markdown and PDF
spec/       synthetic-dataroom-spec.md (what the data room is), answer-key.json (ground truth), terms.json,
            requirements-ears.md (the requirements, with the KPIs the pilot measures), features/ (the executable
            specification, Gherkin; every scenario carries a stable @S-nn key), spec-results.json (its last run),
            stories.json (the stories of the handover,
            linked to R and S keys; every requirement is in a story),
            wireframes/ (the four screens of the prototype as drawn)
tools/      validate_synthetic.py (the data room must match the answer key), render_pdf.py,
            extract_terms.py (one recorded model run per call), evaluate.py (runs scored against the key),
            checks.py (deterministic checks; the same file runs in the browser), run_checks.py,
            build_db.py (sql/seed.sql from the runs), record_console.py (the console transcript the page can replay),
            refresh.sh (all of the derived files, then the tests), page_smoke.js (the page's script under node),
            gherkin.py + spec_runner.py and spec_runner.js (run the specification), wireframes.py
extractions/  runs/<N>/ one JSON per document per run; eval.json, checks.json, console-recording.json
sql/        schema.sql, seed.sql (generated), queries/ (the five measurements)
vendor/     sql.js 1.12.0 (sql-wasm.js + sql-wasm.wasm, MIT), served with the page
index.html  the page; Pyodide 0.27.5 is loaded from cdn.jsdelivr.net on demand
```

## The recorded run

The page never calls a model. One run is recorded and scored:

```
python3 tools/extract_terms.py --model claude-sonnet-5-5   # one run → extractions/runs/<N>/; repeat for stability
tools/refresh.sh                                            # eval.json, checks.json, sql/seed.sql, tests
```

## Check

```
python3 -I tools/validate_synthetic.py
```

Render a PDF (WeasyPrint):

```
DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib python3 tools/render_pdf.py dataroom/<doc>.md dataroom/<doc>.pdf
```

Note: the six records of run 1 were recorded before `extract_terms.py` stored the run number in the record; the field `run: 1` was added to them on 2026-10-29. Nothing else in a record is ever edited.
