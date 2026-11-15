"""Score a recorded extraction run against spec/answer-key.json.

Usage: python3 -I tools/evaluate.py [--write]

Reads extractions/runs/<N>/<doc-id>.json (written by tools/extract_terms.py).
Run 1 is the run the page shows term by term; every run counts towards the
stability column (how many runs got each term right). Prints a table and,
with --write, stores extractions/eval.json for the page.

Rubric per term of a contract:
  correct             found as the key says, every fact of the key's value is
                      in the extracted value, the quote is verbatim in the
                      document and overlaps one of the key's quotes
  missed              key says present, extractor says not found
  invented            key says absent, extractor found something
  wrong_value         a fact of the key's value is missing from the extraction
  quote_not_verbatim  the extractor's quote is not in the document
A correct term also carries source_matches_key: whether the quote is one of
the sentences the key names, or another verbatim sentence of the document.
Facts are the dates and numbers of the key's value (or an explicit `facts`
list), number words included ("twelve", "thirty per cent"); section, clause
and annex numbers are references, not facts. A figure that carries a unit in
the key (12 years, EUR 2,000,000, 150 hours) must carry the same unit in the
answer: "12 months" does not satisfy "12 years". Words are left to the reader:
the page shows both texts side by side.

For the two committee papers (DD summary, IC key terms) the question is
different: did the extractor repeat what the paper says, including its
planted errors? `faithful` / `not_faithful` per planted error.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from checks import typed_facts  # noqa: E402

KEY_PATH = ROOT / "spec" / "answer-key.json"
DATA = ROOT / "dataroom"
EXTRACTIONS = ROOT / "extractions"
RUNS = EXTRACTIONS / "runs"
PRIMARY_RUN = 1
OVERLAP_WORDS = 6

MONTHS = "january|february|march|april|may|june|july|august|september|october|november|december"
DATE_RE = re.compile(rf"\b(\d{{1,2}} (?:{MONTHS}) \d{{4}})\b", re.I)
DAYMONTH_RE = re.compile(rf"\b(\d{{1,2}} (?:{MONTHS}))\b(?! \d{{4}})", re.I)
NUM_RE = re.compile(r"(?<![A-Za-z\d.])(\d[\d,]*(?:\.\d+)?)(?![A-Za-z\d])")
REF_RE = re.compile(r"\b(?:section|sections|clause|clauses|annex|annexes|schedule|part\s+[ivx]+|s\.|ss\.)\s*\d+(?:\.\d+)*(?:\s*(?:,|and|-|–|to)\s*\d+(?:\.\d+)*)*", re.I)
UNITS = {"zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
         "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16,
         "seventeen": 17, "eighteen": 18, "nineteen": 19}
TENS = {"twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90}
WORDNUM_RE = re.compile(r"\b(" + "|".join(TENS) + r")(?:[-\s](" + "|".join(k for k in UNITS if UNITS[k] and UNITS[k] < 10) + r"))?\b|\b(" + "|".join(UNITS) + r")\b", re.I)


def _norm_number(s: str) -> str:
    s = s.replace(",", "")
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return s


def facts_of(text: str | None) -> set[str]:
    """Dates and numbers in a text, normalised: '1 October 2027' → '1 october 2027', '1,750,000' → '1750000', '54.50' → '54.5'."""
    if not text:
        return set()
    facts: set[str] = set()
    rest = REF_RE.sub(" ", text)
    for m in DATE_RE.finditer(rest):
        facts.add(m.group(1).lower())
    rest = DATE_RE.sub(" ", rest)
    for m in DAYMONTH_RE.finditer(rest):
        facts.add(m.group(1).lower())
    rest = DAYMONTH_RE.sub(" ", rest)
    for m in NUM_RE.finditer(rest):
        facts.add(_norm_number(m.group(1)))
    for m in WORDNUM_RE.finditer(rest):
        if m.group(1):
            facts.add(str(TENS[m.group(1).lower()] + (UNITS[m.group(2).lower()] if m.group(2) else 0)))
        else:
            facts.add(str(UNITS[m.group(3).lower()]))
    return facts


def _date_satisfied(date_fact: str, got_value: str | None) -> bool:
    """'1 january 2029' also counts when the value says '1 January' and '2029' apart."""
    if not got_value:
        return False
    low = got_value.lower()
    day_month, year = date_fact.rsplit(" ", 1)
    return date_fact in low or (day_month in low and year in low)


def missing_facts(key_value: str | None, got_value: str | None) -> list[str]:
    return _missing(facts_of(key_value), got_value)


def _missing(key_facts: set[str], got_value: str | None) -> list[str]:
    got = facts_of(got_value)
    out = []
    for f in sorted(key_facts):
        if f in got:
            continue
        if DATE_RE.fullmatch(f) and _date_satisfied(f, got_value):
            continue
        if DAYMONTH_RE.fullmatch(f) and got_value and f in got_value.lower():
            continue
        out.append(f)
    return out


def _squash(s: str) -> str:
    return re.sub(r"\s+", " ", s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')).strip()


def in_document(quote: str | None, document: str) -> bool:
    return bool(quote) and _squash(quote) in _squash(document)


def _words(s: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", s.lower())


def overlaps(quote: str | None, key_quotes: list[str]) -> bool:
    """True when the quote shares a run of OVERLAP_WORDS words with one of the key's quotes."""
    if not quote:
        return False
    w = _words(quote)
    runs = {" ".join(w[i:i + OVERLAP_WORDS]) for i in range(max(0, len(w) - OVERLAP_WORDS + 1))}
    if len(w) < OVERLAP_WORDS:
        runs = {" ".join(w)}
    for kq in key_quotes:
        kw = _words(kq)
        kruns = {" ".join(kw[i:i + OVERLAP_WORDS]) for i in range(max(0, len(kw) - OVERLAP_WORDS + 1))}
        if len(kw) < OVERLAP_WORDS:
            kruns = {" ".join(kw)}
        if runs & kruns:
            return True
    return False


def key_quotes(entry: dict) -> list[str]:
    return [v for k, v in entry.items() if k == "quote" or k.startswith("quote_")]


def effective_key(key: dict, doc_id: str) -> dict:
    """The per-term ground truth for a contract, with `facts` filled in.

    A document with `same_as` + `differences` (the v1 draft) inherits the base
    document's terms and overlays the differing quotes; its facts for a
    differing term come from the overlaid quotes, since the key gives no prose
    value for them.
    """
    entry = key[doc_id]
    if "same_as" in entry:
        base = json.loads(json.dumps(key[entry["same_as"]]["terms"]))
        for term, diff in entry["differences"].items():
            t = base[term]
            for k, v in diff.items():
                if k == "present_partial":
                    t["present"] = True
                    continue
                t[k] = v
            t["value"] = None
            quoted = " ".join(v for k, v in diff.items() if k == "quote" or k.startswith("quote_"))
            t["facts"] = sorted(facts_of(quoted))
            t["typed"] = _typed_list(quoted)
            t["differs_from_base"] = True
        terms = base
    else:
        terms = json.loads(json.dumps(entry["terms"]))
    for t in terms.values():
        if "facts" not in t:
            t["facts"] = sorted(facts_of(t.get("value"))) if t.get("present", True) else []
        if "typed" not in t:
            t["typed"] = _typed_list(t.get("value")) if t.get("present", True) else []
    return terms


def _typed_list(text: str | None) -> list[list[str]]:
    """[[unit, value], …] from checks.typed_facts, so a figure is required with its unit."""
    return sorted([u, v] for u, vals in typed_facts(text).items() for v in vals)


def key_term_from_value(value: str, quote: str | None = None) -> dict:
    """A present key term built from a prose value, for tests and ad-hoc scoring."""
    return {"present": True, "value": value, "facts": sorted(facts_of(value)), "typed": _typed_list(value),
            "quote": quote or "Supply Period: twelve (12) years commencing on the Commercial Operation Date."}


def judge(key_term: dict, got: dict, document: str) -> dict:
    present = key_term.get("present", True)
    found = bool(got.get("found"))
    out = {"verdict": None, "missing_facts": [], "source_matches_key": None, "note": ""}
    if not present:
        out["verdict"] = "correct" if not found else "invented"
        return out
    if not found:
        out["verdict"] = "missed"
        return out
    missing = _missing(set(key_term.get("facts", [])), got.get("value"))
    got_typed = {(u, v) for u, vals in typed_facts(got.get("value")).items() for v in vals}
    missing_typed = [f"{v} {u}" for u, v in key_term.get("typed", [])
                     if (u, v) not in got_typed and not (u == "date" and _date_satisfied(v, got.get("value")))]
    if missing or missing_typed:
        out["verdict"] = "wrong_value"
        # a figure with its unit is one fact: "60 days" is not also listed as "60"
        typed_numbers = {t.split(" ", 1)[0] for t in missing_typed}
        out["missing_facts"] = sorted(set(m for m in missing if m not in typed_numbers) | set(missing_typed))
        return out
    if not in_document(got.get("quote"), document):
        out["verdict"] = "quote_not_verbatim"
        return out
    out["source_matches_key"] = overlaps(got.get("quote"), key_quotes(key_term))
    out["verdict"] = "correct"
    return out


def judge_paper(key_entry: dict, got: dict) -> dict:
    """For a committee paper: did the extraction repeat each planted error as the paper states it?"""
    res = {}
    for err in key_entry["planted_errors"]:
        term = got.get("terms", {}).get(err["term"], {})
        stated = facts_of(err["states"])
        res[err["term"]] = {
            "verdict": "faithful" if stated and stated <= facts_of(term.get("value")) else "not_faithful",
            "paper_states": err["states"],
            "truth": err["truth"],
            "extracted": term.get("value"),
        }
    return res


def run_numbers(names: list[str]) -> list[int]:
    return sorted(int(n) for n in names if n.isdigit())


def stability(runs: dict[int, dict]) -> dict:
    """Per document and term: how many runs judged it correct, and the verdict of each run in order."""
    out: dict = {}
    for n in sorted(runs):
        for doc_id, d in runs[n].items():
            for term_id, r in d.get("terms", {}).items():
                cell = out.setdefault(doc_id, {}).setdefault(term_id, {"correct": 0, "runs": 0, "verdicts": []})
                cell["runs"] += 1
                cell["verdicts"].append(r["verdict"])
                if r["verdict"] in ("correct", "faithful"):
                    cell["correct"] += 1
    return out


def evaluate_run(key: dict, run_dir: Path) -> dict:
    """Judge one run: {doc_id: {status, model, terms}}."""
    docs: dict = {}
    for doc_id, entry in key.items():
        if doc_id.startswith("_"):
            continue
        path = run_dir / f"{doc_id}.json"
        if not path.exists():
            docs[doc_id] = {"status": "no extraction recorded"}
            continue
        got = json.loads(path.read_text())
        document = (DATA / f"{doc_id}.md").read_text()
        if "planted_errors" in entry:
            docs[doc_id] = {"status": "paper", "model": got.get("model"), "terms": judge_paper(entry, got)}
            continue
        terms = effective_key(key, doc_id)
        res = {}
        for term_id, kt in terms.items():
            g = got.get("terms", {}).get(term_id, {"found": False})
            r = judge(kt, g, document)
            r.update({"expected": kt.get("value"), "expected_present": kt.get("present", True),
                      "extracted": g.get("value"), "extracted_quote": g.get("quote"), "extracted_note": g.get("note")})
            res[term_id] = r
        docs[doc_id] = {"status": "contract", "model": got.get("model"), "terms": res}
    return docs


def evaluate_all(key: dict) -> dict:
    numbers = run_numbers([d.name for d in RUNS.iterdir() if d.is_dir()]) if RUNS.exists() else []
    runs = {n: evaluate_run(key, RUNS / str(n)) for n in numbers}
    report = {"primary_run": PRIMARY_RUN, "runs": numbers, "documents": runs.get(PRIMARY_RUN, {}),
              "stability": stability(runs), "summary": {}, "run_summaries": {}}
    for n, docs in runs.items():
        counts: dict[str, int] = {}
        for d in docs.values():
            for r in d.get("terms", {}).values():
                if d["status"] == "contract":
                    counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
        report["run_summaries"][n] = counts
    report["summary"] = report["run_summaries"].get(PRIMARY_RUN, {})
    return report


def main(argv: list[str]) -> int:
    key = json.loads(KEY_PATH.read_text())
    report = evaluate_all(key)
    print(f"runs recorded: {report['runs']}  (table shows run {report['primary_run']})")
    for doc_id, d in report["documents"].items():
        print(f"\n{doc_id}  [{d['status']}]" + (f"  model={d.get('model')}" if d.get("model") else ""))
        for term_id, r in d.get("terms", {}).items():
            extra = f"  missing {r['missing_facts']}" if r.get("missing_facts") else ""
            if r.get("source_matches_key") is False:
                extra += "  (quote from another sentence)"
            print(f"  {r['verdict']:<18} {term_id}{extra}")
    print("\nsummary:", json.dumps(report["summary"]))
    if len(report["runs"]) > 1:
        print("per run:", json.dumps(report["run_summaries"]))
        print("\nunstable terms (not correct in every run):")
        for doc_id, terms in report["stability"].items():
            for term_id, c in terms.items():
                if c["correct"] < c["runs"]:
                    print(f"  {c['correct']}/{c['runs']}  {doc_id} / {term_id}  {c['verdicts']}")
    if "--write" in argv:
        (EXTRACTIONS / "eval.json").write_text(json.dumps(report, indent=1, ensure_ascii=False))
        print("wrote extractions/eval.json")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
