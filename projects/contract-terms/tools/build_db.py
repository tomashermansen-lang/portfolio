"""Build sql/seed.sql from the recorded runs, the evaluation and the checks.

Usage: python3 -I tools/build_db.py        (after evaluate.py --write and run_checks.py)

Everything in the seed comes from files in this folder except the review
log and the committee events, which are generated here with fixed rules so
the metrics on the page have something to count:

  review log   one row per term of run 1 for each contract, with the two
               decisions the screen offers: confirmed when the answer-key
               verdict is correct and no check fired on the term; flagged
               otherwise (a wrong verdict, or a paper-vs-contract, verbatim,
               citation or schema finding; a draft-vs-execution difference is
               information, not a flag); minutes: 3 for a confirmed term,
               12 for a flagged one, with a small deterministic spread
  baseline     the process before the prototype, as ASSUMPTIONS: four hours of
               analyst time per contract, five days from data room to a reviewed
               table, no discrepancy ever recorded between paper and contract
               (nobody checked), no tool in use. The first weeks in the seat
               replace them with measurements; the rows say "assumed" until then.
  facts        the figures in run 1's values, typed by unit with
               tools/checks.py typed_facts, so the terms can be queried across
               contracts (query 5)
  events       data room received = the execution version's date, terms table
               +1 day, reviewed +2; for Havrebakke the DD summary and the IC
               paper carry their own dates (4 and 18 June 2026) and the IC
               meeting is the paper's date. The other two projects have no
               committee documents in the data room, so their cycle time to
               committee is NULL, not invented.

The page says this in the same words. The numbers are an illustration of
what the queries measure, not a measurement.
"""
from __future__ import annotations

import datetime as dt
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KEY = json.loads((ROOT / "spec" / "answer-key.json").read_text())
TERMS = json.loads((ROOT / "spec" / "terms.json").read_text())["terms"]

PROJECTS = {
    "havrebakke": ("Havrebakke Wind Farm", "onshore wind", "Denmark", 48.0),
    "olivos": ("Valdeolivos Solar", "solar PV", "Spain", 75.0),
    "lichtung": ("Lichtung Offshore", "offshore wind", "Germany", 300.0),
}
DOCS = {  # id: (project, kind, version_date, pages)
    "havrebakke-ppa-v1-draft": ("havrebakke", "ppa_draft", "2026-03-12", 15),
    "havrebakke-ppa-v2-execution": ("havrebakke", "ppa_execution", "2026-05-28", 15),
    "havrebakke-legal-dd-summary": ("havrebakke", "dd_summary", "2026-06-04", 2),
    "havrebakke-ic-key-terms": ("havrebakke", "ic_paper", "2026-06-18", 2),
    "olivos-solar-ppa-execution": ("olivos", "ppa_execution", "2026-02-14", 14),
    "lichtung-offshore-ppa-execution": ("lichtung", "ppa_execution", "2025-11-03", 14),
}
MINUTES = {"confirmed": 3.0, "flagged": 12.0}
EVENT_OFFSETS = [("dataroom_received", 0), ("terms_table_ready", 1), ("terms_reviewed", 2)]
FLAGGING_CHECKS = ("paper_vs_contract", "quotes_verbatim", "references_exist", "schema")


def q(v) -> str:
    if v is None:
        return "NULL"
    if isinstance(v, (int, float)):
        return str(v)
    return "'" + str(v).replace("'", "''") + "'"


def build_rows() -> dict[str, list[tuple]]:
    rows: dict[str, list[tuple]] = {k: [] for k in ("projects", "documents", "terms", "extractions", "checks", "reviews", "events", "baseline", "facts")}
    for pid, (name, tech, country, mw) in PROJECTS.items():
        rows["projects"].append((pid, name, tech, country, mw))
    for did, (pid, kind, date, pages) in DOCS.items():
        words = len((ROOT / "dataroom" / f"{did}.md").read_text().split())
        rows["documents"].append((did, pid, kind, date, words, pages))
    for i, t in enumerate(TERMS, 1):
        rows["terms"].append((t["id"], i, t["label"]))

    eval_report = json.loads((ROOT / "extractions" / "eval.json").read_text())
    runs_dir = ROOT / "extractions" / "runs"
    verdicts: dict[tuple, str] = {}
    shas: dict[str, str] = {}  # document id -> sha256 of its text, from the extraction records
    # verdict per (run, doc, term): re-judge every run through evaluate's own functions
    sys.path.insert(0, str(ROOT / "tools"))
    import evaluate as ev  # noqa: E402
    for n in eval_report["runs"]:
        judged = ev.evaluate_run(KEY, runs_dir / str(n))
        for did, d in judged.items():
            for tid, r in d.get("terms", {}).items():
                verdicts[(n, did, tid)] = r["verdict"]
        for p in sorted((runs_dir / str(n)).glob("*.json")):
            rec = json.loads(p.read_text())
            shas[rec["document_id"]] = rec["source_sha256"]
            for tid, t in rec["terms"].items():
                rows["extractions"].append((n, rec["document_id"], tid, rec["model"], rec["run_at"], 1 if t.get("found") else 0,
                                            t.get("value"), t.get("quote"), t.get("clause"), t.get("note"), verdicts.get((n, rec["document_id"], tid))))

    checks = json.loads((ROOT / "extractions" / "checks.json").read_text())
    flagged: set[tuple] = set()
    cid = 0
    for name, findings in checks.items():
        if name in ("run", "document_diff"):
            continue
        for f in findings:
            cid += 1
            doc = f.get("document") or f.get("paper_id") or f.get("a_id")
            rows["checks"].append((cid, name, doc, f.get("term"), f["message"]))
            if f.get("term") and name in FLAGGING_CHECKS:
                flagged.add((doc, f["term"]))
                if f.get("contract_id"):
                    flagged.add((f["contract_id"], f["term"]))

    primary = eval_report["primary_run"]
    for did, (pid, kind, date, _) in DOCS.items():
        if kind not in ("ppa_execution", "ppa_draft"):
            continue
        day = dt.date.fromisoformat(date) + dt.timedelta(days=2)
        for i, t in enumerate(TERMS):
            v = verdicts.get((primary, did, t["id"]), "correct")
            outcome = "flagged" if (did, t["id"]) in flagged or v != "correct" else "confirmed"
            minutes = MINUTES[outcome] + (i % 3) * 0.5
            rows["reviews"].append((did, shas[did], t["id"], "analyst", f"{day.isoformat()}T{9 + i // 2:02d}:{(i % 2) * 30:02d}:00", minutes, outcome, None))
    for did, (pid, kind, date, _) in DOCS.items():
        if kind == "ppa_execution":
            base = dt.date.fromisoformat(date)
            for event, off in EVENT_OFFSETS:
                rows["events"].append((pid, event, (base + dt.timedelta(days=off)).isoformat()))
        elif kind == "dd_summary":
            rows["events"].append((pid, "dd_received", date))
        elif kind == "ic_paper":
            rows["events"].append((pid, "ic_paper_issued", date))
            rows["events"].append((pid, "ic_meeting", date))
    rows["baseline"] = [
        ("minutes_per_contract", 240.0, "minutes", "assumed", "a careful analyst, about four hours per contract; to be replaced by a time log on the pilot's three contracts", None),
        ("days_to_reviewed_table", 5.0, "days", "assumed", "from data room to a table the team trusts; to be replaced by the dates in the last twelve cases", None),
        ("discrepancies_per_paper", None, "findings per committee paper", "not measured", "no record exists of a paper disagreeing with its contract, because no one compared them", None),
        ("contracts_processed", 0.0, "contracts", "measured", "no tool in use before the prototype; counts document versions put through the method, not contracts per month", None),
    ]
    import checks  # noqa: E402
    for p in sorted((runs_dir / str(primary)).glob("*.json")):
        rec = json.loads(p.read_text())
        for tid, t in rec["terms"].items():
            if not t.get("found"):
                continue
            for unit, values in checks.typed_facts(t.get("value")).items():
                for v in sorted(values):
                    rows["facts"].append((primary, rec["document_id"], tid, unit, v))
    return rows


def seed_sql(rows: dict[str, list[tuple]]) -> str:
    out = ["-- GENERATED by tools/build_db.py from extractions/ and spec/. Do not edit."]
    for table, rs in rows.items():
        for r in rs:
            out.append(f"INSERT INTO {table} VALUES ({', '.join(q(v) for v in r)});")
    return "\n".join(out) + "\n"


def main() -> int:
    rows = build_rows()
    seed = seed_sql(rows)
    (ROOT / "sql" / "seed.sql").write_text(seed)
    con = sqlite3.connect(":memory:")
    con.executescript((ROOT / "sql" / "schema.sql").read_text())
    con.executescript(seed)
    metrics = {}
    for qp in sorted((ROOT / "sql" / "queries").glob("*.sql")):
        cur = con.execute(qp.read_text())
        cols = [c[0] for c in cur.description]
        values = [list(r) for r in cur.fetchall()]
        metrics[qp.stem] = {"columns": cols, "values": values}
        print(f"\n{qp.name}\n  " + " | ".join(cols))
        for row in values:
            print("  " + " | ".join(str(v) for v in row))
    (ROOT / "extractions" / "metrics.json").write_text(json.dumps(metrics, indent=1, ensure_ascii=False))
    print(f"\nwrote sql/seed.sql ({sum(len(r) for r in rows.values())} rows) and extractions/metrics.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
