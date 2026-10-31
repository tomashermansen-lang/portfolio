"""Record the console transcript of the checks, the scorer and the queries, run
on the desk, so the page can replay it for a reader whose network blocks
WebAssembly.

Usage: python3 -I tools/record_console.py   →  extractions/console-recording.json

The transcript is produced by running the same calls the page runs: the
functions of tools/checks.py on run 1, tools/evaluate.py scoring run 1 against
the answer key (and every run for stability), and the SQL queries on the
built database. Nothing is typed by hand; each line carries the time it
took, so the replay keeps the rhythm of the run. The browser's live runs
print the same lines (see runEvalInBrowser in index.html), so a reader can
compare the two.
"""
from __future__ import annotations

import datetime as dt
import json
import platform
import sqlite3
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build_db  # noqa: E402
import checks  # noqa: E402
import evaluate  # noqa: E402

PAIRS = {"paper_vs_contract": [["havrebakke-ic-key-terms", "havrebakke-ppa-v2-execution"], ["havrebakke-legal-dd-summary", "havrebakke-ppa-v2-execution"]],
         "version_diff": [["havrebakke-ppa-v1-draft", "havrebakke-ppa-v2-execution"]]}
CALLS = [
    ('schema(inputs["extractions"]["havrebakke-ppa-v2-execution"])', "findings"),
    ('quotes_verbatim(inputs["extractions"]["havrebakke-ppa-v2-execution"], inputs["documents"]["havrebakke-ppa-v2-execution"])', "findings"),
    ('typed_facts(inputs["extractions"]["havrebakke-ic-key-terms"]["terms"]["10_credit_support"]["value"])', "raw"),
    ('typed_facts(inputs["extractions"]["havrebakke-ppa-v2-execution"]["terms"]["10_credit_support"]["value"])', "raw"),
    ('paper_vs_contract(inputs["extractions"]["havrebakke-ic-key-terms"], inputs["extractions"]["havrebakke-ppa-v2-execution"])', "list"),
    ('paper_vs_contract(inputs["extractions"]["havrebakke-legal-dd-summary"], inputs["extractions"]["havrebakke-ppa-v2-execution"])', "list"),
    ('version_diff(inputs["extractions"]["havrebakke-ppa-v1-draft"], inputs["extractions"]["havrebakke-ppa-v2-execution"], inputs["documents"]["havrebakke-ppa-v1-draft"], inputs["documents"]["havrebakke-ppa-v2-execution"])', "list"),
    ('len(document_diff(inputs["documents"]["havrebakke-ppa-v1-draft"], inputs["documents"]["havrebakke-ppa-v2-execution"]))', "raw"),
    ('references_in(inputs["extractions"]["olivos-solar-ppa-execution"]["terms"]["8_curtailment"]["note"])', "raw"),
    ('references_exist(inputs["extractions"]["olivos-solar-ppa-execution"], inputs["documents"]["olivos-solar-ppa-execution"])', "findings"),
]


def python_transcript() -> list[dict]:
    lines: list[dict] = []
    t_all = time.perf_counter()
    def add(cls, text, ms=0): lines.append({"cls": cls, "text": text, "ms": round(ms)})
    add("sys", f"recorded on the desk, {dt.date.today().isoformat()} · CPython {platform.python_version()} · the same calls the browser makes")
    docs = {p.stem: p.read_text() for p in (ROOT / "dataroom").glob("*.md") if not p.stem.startswith("havrebakke-ic") and not p.stem.startswith("havrebakke-legal")}
    for k in sorted(docs): add("sys", f"read dataroom/{k}.md · {len(docs[k].split()):,} words")
    exts = {p.stem: json.loads(p.read_text()) for p in (ROOT / "extractions" / "runs" / "1").glob("*.json")}
    add("sys", f"extraction records from run 1: {', '.join(sorted(exts))}")
    add("sys", f"exec tools/checks.py · {len((ROOT / 'tools' / 'checks.py').read_text().splitlines())} lines")
    inputs = {"documents": docs, "extractions": exts, "pairs": PAIRS, "reference_docs": sorted(docs)}
    add("in", "import json; inputs = json.loads(_inputs_json)")
    ns = {"inputs": inputs, "json": json, **{k: getattr(checks, k) for k in dir(checks) if not k.startswith("_")}}
    for src, kind in CALLS:
        t = time.perf_counter()
        v = eval(src, ns)  # the recorded call, as the page shows it
        out = json.loads(json.dumps(v, default=sorted, ensure_ascii=False))
        ms = (time.perf_counter() - t) * 1000
        add("in", src)
        if kind == "list":
            add("out", "\n".join(f"{{term: {f['term']}, {f['message']}}}" for f in out) if out else "[]", ms)
        elif kind == "findings":
            add("out", json.dumps(out) if out else "[]  (no findings)", ms)
        else:
            add("out", json.dumps(out, ensure_ascii=False), ms)
    t = time.perf_counter()
    result = checks.run_all(inputs)
    ms = (time.perf_counter() - t) * 1000
    add("in", "run_all_json(_inputs_json)")
    add("out", "{" + ", ".join(f"{k}: {len(v)}" for k, v in result.items()) + f"}}  · {(time.perf_counter() - t_all):.2f} s on the desk", ms)
    return lines


def _doc_lines(doc: dict) -> str:
    """One line per term, as evaluate.main prints them; the browser prints the same."""
    out = []
    for term_id, r in doc.get("terms", {}).items():
        extra = ""
        if r.get("missing_facts"):
            extra += f"  missing {json.dumps(r['missing_facts'], ensure_ascii=False)}"
        if r.get("source_matches_key") is False:
            extra += "  (quote from another sentence)"
        if "paper_states" in r:
            extra += f"  paper states {r['paper_states']}; the contract says {r['truth']}"
        out.append(f"  {r['verdict']:<18} {term_id}{extra}")
    return "\n".join(out)


def evaluate_transcript() -> list[dict]:
    lines: list[dict] = []
    t_all = time.perf_counter()
    def add(cls, text, ms=0): lines.append({"cls": cls, "text": text, "ms": round(ms)})
    add("sys", f"recorded on the desk, {dt.date.today().isoformat()} · CPython {platform.python_version()} · the same calls the browser makes")
    key = json.loads(evaluate.KEY_PATH.read_text())
    doc_ids = [d for d in key if not d.startswith("_")]
    add("sys", f"read spec/answer-key.json · {len(doc_ids)} documents keyed: {', '.join(doc_ids)}")
    for d in doc_ids:
        add("sys", f"read dataroom/{d}.md · {len((evaluate.DATA / f'{d}.md').read_text().split()):,} words")
    numbers = evaluate.run_numbers([p.name for p in evaluate.RUNS.iterdir() if p.is_dir()])
    add("sys", f"extraction records: runs {', '.join(str(n) for n in numbers)}, one file per document and run")
    add("sys", f"exec tools/evaluate.py · {len((ROOT / 'tools' / 'evaluate.py').read_text().splitlines())} lines; it imports typed_facts from tools/checks.py")
    add("in", 'key = json.loads(KEY_PATH.read_text()); docs = evaluate_run(key, RUNS / "1")')
    t = time.perf_counter()
    docs = evaluate.evaluate_run(key, evaluate.RUNS / "1")
    ms = (time.perf_counter() - t) * 1000
    add("out", f"{len(docs)} documents judged · " + ", ".join(f"{d}: {v['status']}" for d, v in docs.items()), ms)
    for d, v in docs.items():
        add("in", f'docs["{d}"]["terms"]')
        add("out", _doc_lines(v) or "  (no extraction recorded)")
    add("in", "stability({n: evaluate_run(key, RUNS / str(n)) for n in run_numbers})")
    t = time.perf_counter()
    runs = {n: evaluate.evaluate_run(key, evaluate.RUNS / str(n)) for n in numbers}
    stab = evaluate.stability(runs)
    ms = (time.perf_counter() - t) * 1000
    unstable = [f"  {c['correct']}/{c['runs']}  {d} / {term}  {json.dumps(c['verdicts'])}" for d, terms in stab.items() for term, c in terms.items() if c["correct"] < c["runs"]]
    add("out", f"{len(numbers)} runs · terms not correct in every run:\n" + ("\n".join(unstable) if unstable else "  none"), ms)
    counts: dict[str, int] = {}
    for v in docs.values():
        if v["status"] == "contract":
            for r in v["terms"].values():
                counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
    add("in", "summary of run 1, contracts only")
    add("out", json.dumps(counts) + f"  · {(time.perf_counter() - t_all):.2f} s on the desk")
    return lines


def sql_transcript() -> tuple[list[dict], dict]:
    lines: list[dict] = []
    def add(cls, text, ms=0): lines.append({"cls": cls, "text": text, "ms": round(ms)})
    schema = (ROOT / "sql" / "schema.sql").read_text()
    seed = (ROOT / "sql" / "seed.sql").read_text()
    add("sys", f"recorded on the desk, {dt.date.today().isoformat()} · sqlite3 {sqlite3.sqlite_version} · the same statements the browser runs")
    con = sqlite3.connect(":memory:")
    t = time.perf_counter()
    add("in", f"-- sql/schema.sql · {schema.count('CREATE TABLE')} CREATE TABLE"); con.executescript(schema)
    add("in", f"-- sql/seed.sql · {seed.count('INSERT INTO')} INSERT INTO"); con.executescript(seed)
    counts = con.execute("SELECT 'extractions', COUNT(*) FROM extractions UNION ALL SELECT 'reviews', COUNT(*) FROM reviews UNION ALL SELECT 'checks', COUNT(*) FROM checks UNION ALL SELECT 'events', COUNT(*) FROM events").fetchall()
    add("out", "database in memory · " + ", ".join(f"{a} {b}" for a, b in counts) + f" · {(time.perf_counter() - t):.2f} s", (time.perf_counter() - t) * 1000)
    results = {}
    for qp in sorted((ROOT / "sql" / "queries").glob("*.sql")):
        text = qp.read_text().strip()
        t = time.perf_counter()
        cur = con.execute(text)
        cols = [c[0] for c in cur.description]; rows = cur.fetchall()
        us = (time.perf_counter() - t) * 1e6
        add("in", text)
        add("out", f"{len(rows)} rows · {' | '.join(cols)} · {us:.0f} µs", us / 1000)
        results[qp.stem] = {"columns": cols, "values": [list(r) for r in rows]}
    return lines, results


def main() -> int:
    py = python_transcript()
    ev = evaluate_transcript()
    sq, results = sql_transcript()
    out = {"recorded_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "python": py, "evaluate": ev, "sql": sq, "sql_results": results}
    (ROOT / "extractions" / "console-recording.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
    print(f"python: {len(py)} lines · evaluate: {len(ev)} lines · sql: {len(sq)} lines · wrote extractions/console-recording.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
