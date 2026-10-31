-- Contract terms for an investment committee: the working data behind the table.
-- Runs unchanged in sqlite3 (tests) and sql.js (the page).

CREATE TABLE projects (
  id          TEXT PRIMARY KEY,
  name        TEXT NOT NULL,
  technology  TEXT NOT NULL,
  country     TEXT NOT NULL,
  capacity_mw REAL NOT NULL
);

CREATE TABLE documents (
  id           TEXT PRIMARY KEY,
  project_id   TEXT NOT NULL REFERENCES projects(id),
  kind         TEXT NOT NULL CHECK (kind IN ('ppa_draft','ppa_execution','dd_summary','ic_paper')),
  version_date TEXT NOT NULL,           -- ISO date of the version
  words        INTEGER NOT NULL,
  pages        INTEGER NOT NULL
);

CREATE TABLE terms (
  id    TEXT PRIMARY KEY,
  ord   INTEGER NOT NULL,
  label TEXT NOT NULL
);

CREATE TABLE extractions (                -- one row per run, document and term
  run         INTEGER NOT NULL,
  document_id TEXT NOT NULL REFERENCES documents(id),
  term_id     TEXT NOT NULL REFERENCES terms(id),
  model       TEXT NOT NULL,
  run_at      TEXT NOT NULL,
  found       INTEGER NOT NULL,           -- 0/1
  value       TEXT,
  quote       TEXT,
  clause      TEXT,
  note        TEXT,
  verdict     TEXT,                       -- from the answer key: correct, missed, invented, wrong_value, quote_not_verbatim, faithful, not_faithful
  PRIMARY KEY (run, document_id, term_id)
);

CREATE TABLE checks (                     -- findings of the deterministic checks on run 1
  id          INTEGER PRIMARY KEY,
  check_name  TEXT NOT NULL,
  document_id TEXT NOT NULL,
  term_id     TEXT,
  message     TEXT NOT NULL
);

CREATE TABLE reviews (                    -- the analyst's decisions, append-only: one row per decision, never updated or deleted (R-94);
  document_id     TEXT NOT NULL REFERENCES documents(id),   -- the current decision on a term is its latest row per (document, version, term)
  document_sha256 TEXT NOT NULL,          -- the version decided on: sha256 of the document text, as the extraction record carries it
  term_id         TEXT NOT NULL REFERENCES terms(id),
  reviewer        TEXT NOT NULL,
  decided_at      TEXT NOT NULL,          -- ISO timestamp of the decision
  minutes         REAL NOT NULL,          -- minutes the term took the reviewer (generated in the seed, see build_db.py)
  outcome         TEXT NOT NULL CHECK (outcome IN ('confirmed','flagged')),  -- the two decisions the review screen offers
  note            TEXT                    -- the reviewer's note on a flag
);
CREATE INDEX reviews_current ON reviews (document_id, document_sha256, term_id, decided_at);

CREATE TABLE events (                     -- the project's path to the committee
  project_id TEXT NOT NULL REFERENCES projects(id),
  event      TEXT NOT NULL CHECK (event IN ('dataroom_received','terms_table_ready','terms_reviewed','dd_received','ic_paper_issued','ic_meeting')),
  at         TEXT NOT NULL,
  PRIMARY KEY (project_id, event)
);

CREATE TABLE baseline (                   -- the process before the prototype; see build_db.py for what is assumed
  metric      TEXT PRIMARY KEY,           -- minutes_per_contract, days_to_reviewed_table, discrepancies_per_paper, contracts_per_month
  value       REAL,                       -- NULL = not measured
  unit        TEXT NOT NULL,
  basis       TEXT NOT NULL CHECK (basis IN ('assumed','measured','not measured')),
  source      TEXT NOT NULL,
  measured_on TEXT
);

CREATE TABLE facts (                      -- the figures in the extracted values, typed by unit (tools/checks.py typed_facts)
  run         INTEGER NOT NULL,
  document_id TEXT NOT NULL REFERENCES documents(id),
  term_id     TEXT NOT NULL REFERENCES terms(id),
  unit        TEXT NOT NULL,              -- years, months, days, hours, eur, eur_per_mwh, percent, mw, mwh, kv, date
  value       TEXT NOT NULL,
  PRIMARY KEY (run, document_id, term_id, unit, value)
);
