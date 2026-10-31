"""Run the executable specification: spec/features/*.feature against the real
files (the recorded run, the data room, checks.py, the database).

Usage: python3 -I tools/spec_runner.py [--write]
With --write, the results are merged into spec/spec-results.json (the UI
features are added by tools/spec_runner.js). Exit 1 if any scenario failed.
"""
from __future__ import annotations

import ast
import hashlib
import json
import re
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build_db  # noqa: E402
import checks  # noqa: E402
import evaluate as ev  # noqa: E402
from gherkin import Steps, run  # noqa: E402

step = Steps()
KEY = json.loads((ROOT / "spec" / "answer-key.json").read_text())
TERMS = json.loads((ROOT / "spec" / "terms.json").read_text())["terms"]
CONTRACTS = ["havrebakke-ppa-v2-execution", "havrebakke-ppa-v1-draft", "olivos-solar-ppa-execution", "lichtung-offshore-ppa-execution"]


def load_run(n):
    return {p.stem: json.loads(p.read_text()) for p in (ROOT / "extractions" / "runs" / str(n)).glob("*.json")}


# ---------- extraction
@step(r"the recorded run 1")
def _(ctx): ctx["run"] = load_run(1)

@step(r"spec/terms.json defines exactly (\d+) terms, each with an id, a label and a definition")
def _(ctx, n):
    assert len(TERMS) == int(n), len(TERMS)
    assert all(t.get("id") and t.get("label") and t.get("ask") for t in TERMS)

@step(r"every record of run 1 holds those 12 terms in that order")
def _(ctx):
    for d, r in ctx["run"].items():
        assert list(r["terms"]) == [t["id"] for t in TERMS], d

@step(r"every term reported found has a value, a quote and a clause")
def _(ctx):
    for d, r in ctx["run"].items():
        for tid, t in r["terms"].items():
            if t.get("found"):
                assert t.get("value") and t.get("quote") and t.get("clause"), (d, tid)

@step(r'the term "([^"]+)" of "([^"]+)" is read')
def _(ctx, tid, doc): ctx["term"] = ctx["run"][doc]["terms"][tid]

@step(r"the term is not found")
def _(ctx): assert not ctx["term"]["found"], ctx["term"]

@step(r"the note says the document does not address it")
def _(ctx):
    n = (ctx["term"].get("note") or "").lower()
    assert "no curtailment" in n or "does not" in n or "not address" in n, n

@step(r'the note mentions "([^"]+)"')
def _(ctx, s): assert s in (ctx["term"].get("note") or ""), ctx["term"].get("note")

@step(r'the value contains "([^"]+)"')
def _(ctx, s): assert s in (ctx["term"].get("value") or ""), ctx["term"].get("value")

@step(r'the clause mentions "([^"]+)"')
def _(ctx, s): assert s in (ctx["term"].get("clause") or ""), ctx["term"].get("clause")

@step(r"every record of run 1 carries a model, a run time, a run number and a 64-character document hash")
def _(ctx):
    for d, r in ctx["run"].items():
        assert r.get("model") and r.get("run_at") and r.get("run") == 1 and len(r.get("source_sha256", "")) == 64, d

@step(r'the document hash of "([^"]+)" matches the SHA-256 of dataroom/([^ ]+)')
def _(ctx, doc, fname):
    h = hashlib.sha256((ROOT / "dataroom" / fname).read_text().encode()).hexdigest()
    assert ctx["run"][doc]["source_sha256"] == h

@step(r"the runs are numbered (\d+) to (\d+) with no gap")
def _(ctx, a, b):
    nums = sorted(int(p.name) for p in (ROOT / "extractions" / "runs").iterdir() if p.name.isdigit())
    assert nums == list(range(int(a), int(b) + 1)), nums


# ---------- evaluation
V2 = (ROOT / "dataroom" / "havrebakke-ppa-v2-execution.md").read_text()

@step(r'a key term present with facts "([^"]+)" and quote "([^"]+)"')
def _(ctx, facts, quote): ctx["key"] = {"present": True, "facts": facts.split(","), "quote": quote}

@step(r"a key term absent")
def _(ctx): ctx["key"] = {"present": False, "facts": []}

@step(r'the model answers found with value "([^"]+)" and that quote')
def _(ctx, value): ctx["got"] = {"found": True, "value": value, "quote": ctx["key"]["quote"]}

@step(r'the model answers found with value "([^"]+)" and quote "([^"]+)"')
def _(ctx, value, quote): ctx["got"] = {"found": True, "value": value, "quote": quote}

@step(r"the model answers not found")
def _(ctx): ctx["got"] = {"found": False, "value": None, "quote": None}

@step(r'the verdict is "([^"]+)"')
def _(ctx, v):
    ctx["verdict"] = ev.judge(ctx["key"], ctx["got"], V2)
    assert ctx["verdict"]["verdict"] == v, ctx["verdict"]

@step(r"the source is recorded as not matching the key")
def _(ctx): assert ctx["verdict"]["source_matches_key"] is False

@step(r"the recorded runs")
def _(ctx): ctx["report"] = ev.evaluate_all(KEY)

@step(r"run 1 scores (\d+) correct of (\d+)")
def _(ctx, c, n):
    s = ctx["report"]["run_summaries"][1]
    assert s.get("correct") == int(c) and sum(s.values()) == int(n), s

@step(r'the term "([^"]+)" of "([^"]+)" is correct in (\d+) of (\d+) runs')
def _(ctx, tid, doc, c, n):
    st = ctx["report"]["stability"][doc][tid]
    assert (st["correct"], st["runs"]) == (int(c), int(n)), st

@step(r'the paper "([^"]+)" is faithful on "([^"]+)" and "([^"]+)"')
def _(ctx, doc, a, b):
    t = ctx["report"]["documents"][doc]["terms"]
    assert t[a]["verdict"] == "faithful" and t[b]["verdict"] == "faithful", t


# ---------- checks
@step(r"the documents of the data room")
def _(ctx): ctx["docs"] = {p.stem: p.read_text() for p in (ROOT / "dataroom").glob("*.md")}

@step(r'tools/checks.py imports only "([^"]+)", "([^"]+)" and "([^"]+)"')
def _(ctx, a, b, c):
    tree = ast.parse((ROOT / "tools" / "checks.py").read_text())
    mods = sorted({n.name.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.Import) for n in node.names}
                  | {node.module.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module and node.module != "__future__"})
    assert mods == sorted([a, b, c]), mods

@step(r"the verbatim check raises no finding on any contract")
def _(ctx):
    for d in CONTRACTS:
        assert checks.quotes_verbatim(ctx["run"][d], ctx["docs"][d]) == [], d

@step(r'the quote of "([^"]+)" in "([^"]+)" is replaced by "([^"]+)"')
def _(ctx, tid, doc, q):
    rec = json.loads(json.dumps(ctx["run"][doc])); rec["terms"][tid]["quote"] = q; ctx["rec"] = rec; ctx["doc"] = doc

@step(r'the verbatim check raises a finding on "([^"]+)"')
def _(ctx, tid):
    f = checks.quotes_verbatim(ctx["rec"], ctx["docs"][ctx["doc"]])
    assert [x["term"] for x in f] == [tid], f

@step(r'the citation check on "([^"]+)" raises no finding')
def _(ctx, doc): assert checks.references_exist(ctx["run"][doc], ctx["docs"][doc]) == []

@step(r'the citation check on "([^"]+)" raises exactly one finding, on "([^"]+)", citing "([^"]+)"')
def _(ctx, doc, tid, ref):
    f = checks.references_exist(ctx["run"][doc], ctx["docs"][doc])
    assert {(x["term"], x["reference"]) for x in f} == {(tid, ref)}, f

@step(r'"([^"]+)" is checked against "([^"]+)"')
def _(ctx, paper, contract): ctx["findings"] = checks.paper_vs_contract(ctx["run"][paper], ctx["run"][contract])

@step(r'the findings are exactly "([^"]+)" (\w+) and "([^"]+)" (\w+)')
def _(ctx, t1, u1, t2, u2): assert {(f["term"], f["unit"]) for f in ctx["findings"]} == {(t1, u1), (t2, u2)}, ctx["findings"]

@step(r'the findings are exactly "([^"]+)" (\w+)')
def _(ctx, t1, u1): assert {(f["term"], f["unit"]) for f in ctx["findings"]} == {(t1, u1)}, ctx["findings"]

@step(r'the finding on "([^"]+)" says the paper states (\d+) and the contract (\d+)')
def _(ctx, tid, a, b):
    f = next(x for x in ctx["findings"] if x["term"] == tid)
    assert f["paper"] == [a] and f["contract"] == [b], f

@step(r'"([^"]+)" is compared with "([^"]+)"')
def _(ctx, a, b): ctx["diff"] = checks.version_diff(ctx["run"][a], ctx["run"][b], ctx["docs"].get(a), ctx["docs"].get(b))

@step(r'the changed terms include "([^"]+)", "([^"]+)", "([^"]+)", "([^"]+)" and "([^"]+)"')
def _(ctx, *ts):
    changed = {f["term"] for f in ctx["diff"]}
    assert set(ts) <= changed, changed

@step(r'"([^"]+)" is unchanged, because both versions state its figures')
def _(ctx, tid):
    changed = {f["term"] for f in ctx["diff"]}
    assert tid not in changed, changed
    # and the same term is a change when the documents are not consulted: the rule, not the data, removes it
    blind = {f["term"] for f in checks.version_diff(ctx["run"]["havrebakke-ppa-v1-draft"], ctx["run"]["havrebakke-ppa-v2-execution"])}
    assert tid in blind, blind

@step(r'"([^"]+)" and "([^"]+)" are unchanged')
def _(ctx, a, b):
    changed = {f["term"] for f in ctx["diff"]}
    assert a not in changed and b not in changed, changed

@step(r'the texts of "([^"]+)" and "([^"]+)" are diffed')
def _(ctx, a, b):
    d = checks.document_diff(ctx["docs"][a], ctx["docs"][b])
    ctx["a_text"] = " ".join(s for f in d for s in f["a"]); ctx["b_text"] = " ".join(s for f in d for s in f["b"])

@step(r'the draft side contains "([^"]+)" and "([^"]+)"')
def _(ctx, a, b): assert a in ctx["a_text"] and b in ctx["a_text"]

@step(r'the signed side contains "([^"]+)" and "([^"]+)"')
def _(ctx, a, b): assert a in ctx["b_text"] and b in ctx["b_text"]

@step(r'a record marks "([^"]+)" found without a quote')
def _(ctx, tid):
    rec = json.loads(json.dumps(ctx["run"]["havrebakke-ppa-v2-execution"])); rec["terms"][tid]["quote"] = None; ctx["rec"] = rec

@step(r'the shape check raises a finding on "([^"]+)"')
def _(ctx, tid): assert [f["term"] for f in checks.schema(ctx["rec"])] == [tid]


# ---------- measurement
@step(r"the database built from the schema and the seed")
def _(ctx):
    con = sqlite3.connect(":memory:")
    con.executescript((ROOT / "sql" / "schema.sql").read_text())
    con.executescript(build_db.seed_sql(build_db.build_rows()))
    ctx["con"] = con

@step(r"every run and document has (\d+) extraction rows")
def _(ctx, n):
    for run, doc, c in ctx["con"].execute("SELECT run, document_id, COUNT(*) FROM extractions GROUP BY 1, 2"):
        assert c == int(n), (run, doc, c)

@step(r'every baseline row has a basis of "([^"]+)", "([^"]+)" or "([^"]+)"')
def _(ctx, a, b, c):
    for (basis,) in ctx["con"].execute("SELECT basis FROM baseline"):
        assert basis in (a, b, c), basis

@step(r'the baseline "([^"]+)" is NULL with basis "([^"]+)"')
def _(ctx, metric, basis):
    row = ctx["con"].execute("SELECT value, basis FROM baseline WHERE metric=?", (metric,)).fetchone()
    assert row == (None, basis), row

@step(r'query "([^"]+)" runs')
def _(ctx, name):
    cur = ctx["con"].execute((ROOT / "sql" / "queries" / f"{name}.sql").read_text())
    ctx["cols"] = [c[0] for c in cur.description]; ctx["rows"] = cur.fetchall()

def _row(ctx, key_col, key):
    return next(dict(zip(ctx["cols"], r)) for r in ctx["rows"] if r[ctx["cols"].index(key_col)] == key)

@step(r"it returns (\d+) rows")
def _(ctx, n): assert len(ctx["rows"]) == int(n), len(ctx["rows"])

@step(r'the row "([^"]+)" has a negative change and basis "([^"]+)"')
def _(ctx, metric, basis):
    r = _row(ctx, "metric", metric); assert r["change"] < 0 and r["before_basis"] == basis, r

@step(r'the row "([^"]+)" has NULL before')
def _(ctx, metric): assert _row(ctx, "metric", metric)["before"] is None

@step(r'"([^"]+)" has ([\d.]+) days to committee')
def _(ctx, project, d): assert _row(ctx, "project", project)["days_to_committee"] == float(d)

@step(r'"([^"]+)" has NULL days to committee')
def _(ctx, project): assert _row(ctx, "project", project)["days_to_committee"] is None

@step(r'"([^"]+)" has curtailment cap (\d+) hours')
def _(ctx, doc, h): assert _row(ctx, "contract", doc)["curtailment_cap_hours"] == int(h)

@step(r'"([^"]+)" has NULL curtailment cap')
def _(ctx, doc): assert _row(ctx, "contract", doc)["curtailment_cap_hours"] is None

@step(r'"([^"]+)" has price ([\d.]+)')
def _(ctx, doc, p): assert _row(ctx, "contract", doc)["price_eur_per_mwh"] == float(p)


# ---------- continuous evaluation
@step(r"the evaluation reports a summary for every run directory")
def _(ctx):
    dirs = sorted(int(p.name) for p in (ROOT / "extractions" / "runs").iterdir() if p.name.isdigit())
    assert sorted(ctx["report"]["run_summaries"]) == dirs, (sorted(ctx["report"]["run_summaries"]), dirs)

@step(r"no run is left out of the stability count")
def _(ctx):
    n = len(ctx["report"]["runs"])
    for doc, terms in ctx["report"]["stability"].items():
        for tid, c in terms.items():
            assert c["runs"] == n, (doc, tid, c)

@step(r'"([^"]+)" of "([^"]+)" is wrong in every run')
def _(ctx, tid, doc): assert ctx["report"]["stability"][doc][tid]["correct"] == 0

@step(r'"([^"]+)" of "([^"]+)" is wrong in some runs')
def _(ctx, tid, doc):
    c = ctx["report"]["stability"][doc][tid]; assert 0 < c["correct"] < c["runs"], c

@step(r'the term definition of "([^"]+)" does not ask for the reference price fallback')
def _(ctx, tid):
    t = next(t for t in TERMS if t["id"] == tid)
    assert "reference price" not in t["ask"].lower(), t["ask"]

@step(r"at least (\d+) runs are recorded for the current model")
def _(ctx, n):
    models = {}
    for d in (ROOT / "extractions" / "runs").iterdir():
        if d.name.isdigit():
            for p in d.glob("*.json"):
                models.setdefault(json.loads(p.read_text())["model"], set()).add(int(d.name))
    assert max(len(v) for v in models.values()) >= int(n), models



# ---------- extraction, the raw reply
@step(r"the extractor writes the raw model reply to a file beside the record before it parses it")
def _(ctx):
    src = (ROOT / "tools" / "extract_terms.py").read_text()
    i, j = src.find('.raw.txt").write_text(raw)'), src.find("parse_reply(raw)", src.find("def main") if "def main" in src else 0)
    assert i > 0 and j > i, (i, j)


# ---------- evaluation, every run's score
@step(r"every recorded run has a score of correct terms out of (\d+)")
def _(ctx, n):
    for run, s in ctx["report"]["run_summaries"].items():
        assert sum(s.values()) == int(n) and "correct" in s, (run, s)

@step(r"the lowest and highest run scores are (\d+) and (\d+)")
def _(ctx, lo, hi):
    scores = sorted(s.get("correct", 0) for s in ctx["report"]["run_summaries"].values())
    assert (scores[0], scores[-1]) == (int(lo), int(hi)), scores


# ---------- measurement, the KPIs
@step(r'the columns include "([^"]+)", "([^"]+)" and "([^"]+)"')
def _(ctx, a, b, c): assert {a, b, c} <= set(ctx["cols"]), ctx["cols"]

@step(r'the columns include "([^"]+)" and "([^"]+)"')
def _(ctx, a, b): assert {a, b} <= set(ctx["cols"]), ctx["cols"]

@step(r'"([^"]+)" has (\d+) confirmed and (\d+) flagged')
def _(ctx, doc, c, f):
    r = _row(ctx, "document", doc); assert (r["confirmed"], r["flagged"]) == (int(c), int(f)), r

@step(r'a second decision "([^"]+)" is added on the term "([^"]+)" of "([^"]+)"')
def _(ctx, outcome, term, doc):
    con = ctx["con"]
    sha = con.execute("SELECT document_sha256 FROM reviews WHERE document_id=? AND term_id=? LIMIT 1", (doc, term)).fetchone()[0]
    con.execute("INSERT INTO reviews VALUES (?, ?, ?, 'analyst', '2026-12-01T10:00:00', 12.0, ?, 'second look')", (doc, sha, term, outcome))

@step(r'the reviews table holds (\d+) rows for the term "([^"]+)" of "([^"]+)"')
def _(ctx, n, term, doc):
    got = ctx["con"].execute("SELECT COUNT(*) FROM reviews WHERE document_id=? AND term_id=?", (doc, term)).fetchone()[0]
    assert got == int(n), got

@step(r'every review outcome is "([^"]+)" or "([^"]+)"')
def _(ctx, a, b):
    for (o,) in ctx["con"].execute("SELECT DISTINCT outcome FROM reviews"):
        assert o in (a, b), o

@step(r'the term "([^"]+)" has at least (\d+) check finding')
def _(ctx, term, n): assert _row(ctx, "term", term)["check_findings"] >= int(n)


# ---------- the data room
@step(r"every document in the data room carries the synthetic header line")
def _(ctx):
    import validate_synthetic as vs
    for p in (ROOT / "dataroom").glob("*.md"):
        assert vs.HEADER in p.read_text(), p.name

@step(r"the validator reports no failure on any document")
def _(ctx):
    import validate_synthetic as vs
    for doc in sorted(k for k in KEY if not k.startswith("_") and ("terms" in KEY[k] or "same_as" in KEY[k])):
        assert vs.check_doc(doc) == [], (doc, vs.check_doc(doc))

@step(r'the header line is removed from a copy of "([^"]+)"')
def _(ctx, doc):
    import tempfile, validate_synthetic as vs
    d = Path(tempfile.mkdtemp()); text = (ROOT / "dataroom" / f"{doc}.md").read_text()
    (d / f"{doc}.md").write_text(text.replace(vs.HEADER, "", 1)); ctx["copy"] = (d, doc)

@step(r'the validator reports "([^"]+)" for that copy')
def _(ctx, rule):
    import validate_synthetic as vs
    d, doc = ctx["copy"]; keep = vs.DATA
    try:
        vs.DATA = d; fails = vs.check_doc(doc)
    finally:
        vs.DATA = keep
    assert any(rule in f for f in fails), fails


# ---------- the page itself, read from its source
PAGE = (ROOT / "index.html").read_text()
SCRIPT = max(re.findall(r"<script>[\s\S]*?</script>", PAGE), key=len)  # the page script: the largest inline block, not the last (the counter follows it)

@step(r"index.html makes no request to a model API")
def _(ctx):
    for needle in ("api.anthropic.com", "x-api-key", "anthropic-version", "openai.com"):
        assert needle not in PAGE, needle

@step(r"index.html sends no data by POST, XMLHttpRequest or beacon")
def _(ctx):
    for needle in ("method: 'POST'", 'method: "POST"', "XMLHttpRequest", "sendBeacon"):
        assert needle not in SCRIPT, needle

@step(r"the print style for the committee pages sets the page size to A4 landscape")
def _(ctx): assert "@page{size:A4 landscape" in SCRIPT, "no landscape @page in the print style"

@step(r"the play-the-run control of the checks stands before the live-run control in the page")
def _(ctx):
    a, b = PAGE.find('id="play-checks"'), PAGE.find('id="run-checks"')
    assert 0 < a < b, (a, b)

@step(r'spec/wireframes holds exactly "([^"]+)", "([^"]+)", "([^"]+)" and "([^"]+)"')
def _(ctx, *names):
    have = sorted(p.stem for p in (ROOT / "spec" / "wireframes").glob("*.svg"))
    assert have == sorted(names), have

@step(r"every wireframe is an SVG with a description and no figures from the data")
def _(ctx):
    import re as _re
    for p in (ROOT / "spec" / "wireframes").glob("*.svg"):
        t = p.read_text()
        assert t.startswith("<svg") and 'aria-label="' in t, p.name
        assert not _re.search(r"EUR \d|54\.50|Havrebakke|Lichtung|Valdeolivos", t), p.name


PY_FEATURES = ["extraction", "evaluation", "checks", "measurement", "continuous_evaluation", "dataroom", "platform", "page"]


def main(argv):
    results = run([ROOT / "spec" / "features" / f"{n}.feature" for n in PY_FEATURES], step)
    for r in results:
        tag = {"passed": "PASS", "pending": "PEND"}.get(r["status"], "FAIL")
        print(f"{tag}  {r['file']} · {r['scenario']}" + (f"\n      at: {r['failed_step']}\n      {r['error']}" if r["status"] == "failed" else ""))
    passed = sum(r["status"] == "passed" for r in results); pending = sum(r["status"] == "pending" for r in results)
    print(f"\n{passed} passed, {pending} pending (specified, not built), {len(results) - passed - pending} failed of {len(results)} scenarios")
    if "--write" in argv:
        out = ROOT / "spec" / "spec-results.json"
        existing = json.loads(out.read_text()) if out.exists() else {"runs": {}}
        existing["runs"]["python"] = {"results": results}
        out.write_text(json.dumps(existing, indent=1, ensure_ascii=False))
    return 0 if passed + pending == len(results) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
