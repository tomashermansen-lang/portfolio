"""Deterministic checks on a recorded extraction. Standard library only, no
file access: the same module runs under CPython (tools/run_checks.py, the
tests) and in the browser under Pyodide, where the page passes the fetched
documents and extraction records to run_all_json().

Checks:
  schema             every term present; found → value and quote; not found → note
  quotes_verbatim    every quote is in its document, character for character
                     (whitespace and curly quotes normalised)
  paper_vs_contract  a committee paper's extraction against the contract's:
                     for every unit (years, EUR, months, …) stated on both sides
                     of a term, the paper's values must be among the contract's
  version_diff       two versions of a contract: the units whose values differ
                     in the extractions, and terms found in one version only
  document_diff      the sentences that differ between the two documents
                     themselves (difflib), the model-free view of the same
  references_exist   every section, annex or part the model cites in a note,
                     a clause field or a value points at something that exists
                     in the document; a citation of a clause that is not there
                     is a finding (what the clause says is not checked)

What these cannot catch is stated as plainly: a wrong word, a wrong party
name, a wrong allocation of risk are not units. Those stay with the reader,
which is why the page shows the two texts side by side.
"""
from __future__ import annotations

import difflib
import json
import re

TERM_IDS = [
    "1_parties_and_buyer_credit", "2_facility", "3_supply_period", "4_cod_and_delay",
    "5_price_and_indexation", "6_volume_and_performance", "7_product_and_certificates",
    "8_curtailment", "9_delivery_point_and_balancing", "10_credit_support",
    "11_default_and_termination", "12_change_in_law_and_force_majeure",
]

UNITS = {"zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
         "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16,
         "seventeen": 17, "eighteen": 18, "nineteen": 19}
TENS = {"twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90}
MONTHS = {"jan": "january", "feb": "february", "mar": "march", "apr": "april", "may": "may", "jun": "june", "jul": "july",
          "aug": "august", "sep": "september", "sept": "september", "oct": "october", "nov": "november", "dec": "december"}

_WORDNUM = r"(?:(?:one hundred and )?(?:" + "|".join(TENS) + r")(?:[-\s](?:" + "|".join(k for k, v in UNITS.items() if 0 < v < 10) + r"))?|one hundred(?: and (?:" + "|".join(UNITS) + r"))?|" + "|".join(UNITS) + r")"
_NUM = r"(?:\d[\d,]*(?:\.\d+)?)"
# a number, in digits or words, optionally followed by its digits in brackets: "ten (10)", "one hundred and fifty (150)"
_QTY = rf"(?P<q>{_NUM}|{_WORDNUM})(?:\s*\(\s*(?P<qd>\d[\d,]*)\s*\))?"
_SCALE = r"(?P<scale>m|million|k|thousand|bn|billion)?"

DATE_RE = re.compile(r"\b(\d{1,2})\s+([A-Za-z]{3,9})\.?\s+(\d{4})\b")
EUR_RE = re.compile(rf"\bEUR\s*(?P<q>{_NUM})\s*{_SCALE}\b(?P<per>\s*(?:/|per)\s*MWh)?", re.I)
PERCENT_RE = re.compile(rf"\b{_QTY}\s*(?:%|per cent|percent)", re.I)
TWELFTHS_RE = re.compile(rf"\b{_QTY}\s*twelfths?\b", re.I)
QTY_UNIT_RE = re.compile(rf"\b{_QTY}\s*(?:(?:consecutive|calendar|aggregate|full|further)\s+)?(?P<unit>business days?|years?|months?|days?|hours?|GWh|MWh|MWp|MW(?:\s*AC)?|kV)\b(?!\s*/\s*MWh)", re.I)


def _words_to_int(s: str) -> int | None:
    s = s.lower().replace("-", " ")
    total = 0
    if s.startswith("one hundred"):
        total = 100
        s = s[len("one hundred"):].strip()
        if s.startswith("and "):
            s = s[4:]
    for w in s.split():
        if w in TENS:
            total += TENS[w]
        elif w in UNITS:
            total += UNITS[w]
        elif w:
            return None
    return total


def _norm(q: str, qd: str | None = None, scale: str | None = None) -> str | None:
    if qd:
        q = qd
    q = q.replace(",", "")
    try:
        v = float(q)
    except ValueError:
        n = _words_to_int(q)
        if n is None:
            return None
        v = float(n)
    s = (scale or "").lower()
    if s in ("m", "million"):
        v *= 1_000_000
    elif s in ("k", "thousand"):
        v *= 1_000
    elif s in ("bn", "billion"):
        v *= 1_000_000_000
    out = f"{v:.6f}".rstrip("0").rstrip(".")
    return out


def typed_facts(text: str | None) -> dict[str, set[str]]:
    """Quantities with their unit, normalised: {'years': {'10'}, 'eur': {'2500000'}, 'date': {'1 october 2027'}, …}."""
    facts: dict[str, set[str]] = {}
    if not text:
        return facts

    def add(unit: str, value: str | None):
        if value is not None:
            facts.setdefault(unit, set()).add(value)

    rest = text
    for m in DATE_RE.finditer(rest):
        mon = m.group(2).lower()
        full = MONTHS.get(mon, mon if mon in MONTHS.values() else None)
        if full:
            add("date", f"{int(m.group(1))} {full} {m.group(3)}")
    rest = DATE_RE.sub(" ", rest)
    for m in EUR_RE.finditer(rest):
        add("eur_per_mwh" if m.group("per") else "eur", _norm(m.group("q"), None, m.group("scale")))
    rest = EUR_RE.sub(" ", rest)
    for m in PERCENT_RE.finditer(rest):
        add("percent", _norm(m.group("q"), m.group("qd")))
    rest = PERCENT_RE.sub(" ", rest)
    for m in TWELFTHS_RE.finditer(rest):  # "nine twelfths of the annual production" is nine months of it
        add("months", _norm(m.group("q"), m.group("qd")))
    rest = TWELFTHS_RE.sub(" ", rest)
    for m in QTY_UNIT_RE.finditer(rest):
        unit = m.group("unit").lower()
        value = _norm(m.group("q"), m.group("qd"))
        if value is None:
            continue
        if unit.startswith("business"):
            add("business_days", value)
        elif unit in ("gwh",):
            add("mwh", _norm(str(float(value) * 1000)))
        elif unit == "mwh":
            add("mwh", value)
        elif unit.startswith("mw"):
            add("mw", value)
        elif unit == "kv":
            add("kv", value)
        else:
            add(unit.rstrip("s") + "s", value)
    return facts


REF_WORD_RE = re.compile(r"\b(?:sections?|ss?\.|clauses?|paragraphs?)\s+((?:\d+(?:\.\d+)*)(?:\s*(?:,|and|to|-|–|&)\s*\d+(?:\.\d+)*)*)", re.I)
REF_ANNEX_RE = re.compile(r"\b(Annex|Schedule|Appendix)\s+(\d+)\b", re.I)
REF_PART_RE = re.compile(r"\bPart\s+(I{1,3}|IV|V)\b")
REF_BARE_RE = re.compile(r"(?<![\w.,€$£%])(\d{1,2}\.\d{1,2}(?:\.\d{1,2})?)(?![\d%])(?!\s*(?:%|per\b|MW|GW|kV|million|m\b|bn\b|k\b))")
UNIT_BEFORE_RE = re.compile(r"(?:EUR|USD|GBP|DKK|€|\$|£)\s*$", re.I)


def references_in(text: str | None) -> set[str]:
    """Clause citations in free text: '7.4', '(4.5)', 'section 13.3 and 13.4', 'Annex 2', 'Part I'.
    Amounts, percentages and dates are left out by their units and their shape."""
    if not text:
        return set()
    refs: set[str] = set()
    for m in REF_WORD_RE.finditer(text):
        for n in re.findall(r"\d+(?:\.\d+)*", m.group(1)):
            refs.add(n)
    for m in REF_ANNEX_RE.finditer(text):
        refs.add(f"Annex {m.group(2)}")
    for m in REF_PART_RE.finditer(text):
        refs.add(f"Part {m.group(1)}")
    for m in REF_BARE_RE.finditer(text):
        if UNIT_BEFORE_RE.search(text[:m.start()]):
            continue
        n = m.group(1)
        first = int(n.split(".")[0])
        if 1 <= first <= 40:
            refs.add(n)
    return refs


def clause_index(document: str) -> set[str]:
    """Every clause number, section heading, annex and part a document actually has."""
    idx: set[str] = set()
    for line in document.splitlines():
        m = re.match(r"^\s*(\d+(?:\.\d+)*)\s+\S", line)
        if m:
            n = m.group(1); parts = n.split(".")
            for i in range(1, len(parts) + 1):
                idx.add(".".join(parts[:i]))
        m = re.match(r"^#+\s*(\d+)\.?\s+\S", line)
        if m:
            idx.add(m.group(1))
        m = re.match(r"^#+\s*(Annex|Schedule|Appendix)\s+(\d+)\b", line, re.I)
        if m:
            idx.add(f"Annex {m.group(2)}")
    for m in REF_PART_RE.finditer(document):
        idx.add(f"Part {m.group(1)}")
    return idx


def references_exist(extraction: dict, document: str) -> list[dict]:
    idx = clause_index(document)
    out = []
    for tid, t in extraction.get("terms", {}).items():
        for field in ("note", "clause", "value"):
            for ref in sorted(references_in(t.get(field)), key=lambda r: (r[0].isalpha(), [int(x) if x.isdigit() else 0 for x in re.split(r"[ .]", r)], r)):
                if ref not in idx:
                    out.append({"term": tid, "field": field, "reference": ref, "message": f"{field} cites {ref}, which is not in the document"})
    return out


def _squash(s: str) -> str:
    return re.sub(r"\s+", " ", s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')).strip()


def in_document(quote: str | None, document: str) -> bool:
    return bool(quote) and _squash(quote) in _squash(document)


def schema(extraction: dict) -> list[dict]:
    out = []
    terms = extraction.get("terms", {})
    for tid in TERM_IDS:
        t = terms.get(tid)
        if t is None:
            out.append({"term": tid, "message": "term missing from record"})
            continue
        if t.get("found"):
            if not t.get("value") or not t.get("quote"):
                out.append({"term": tid, "message": "found, but value or quote is empty"})
        elif not (t.get("note") or "").strip():
            out.append({"term": tid, "message": "not found, but no note says why"})
    return out


def quotes_verbatim(extraction: dict, document: str) -> list[dict]:
    out = []
    for tid, t in extraction.get("terms", {}).items():
        if t.get("found") and t.get("quote") and not in_document(t["quote"], document):
            out.append({"term": tid, "message": "quote is not in the document", "quote": t["quote"]})
    return out


def _term_ids(*records: dict) -> list[str]:
    seen = set(TERM_IDS)
    extra = sorted({t for r in records for t in r.get("terms", {})} - seen)
    return TERM_IDS + extra


def paper_vs_contract(paper: dict, contract: dict) -> list[dict]:
    out = []
    for tid in _term_ids(paper, contract):
        p = paper.get("terms", {}).get(tid, {})
        c = contract.get("terms", {}).get(tid, {})
        if not (p.get("found") and c.get("found")):
            continue
        pf, cf = typed_facts(p.get("value")), typed_facts(c.get("value"))
        for unit in sorted(set(pf) & set(cf)):
            if not pf[unit] <= cf[unit]:
                out.append({"term": tid, "unit": unit, "paper": sorted(pf[unit] - cf[unit]), "contract": sorted(cf[unit]),
                            "message": f"paper states {', '.join(sorted(pf[unit] - cf[unit]))} {unit}; contract says {', '.join(sorted(cf[unit]))}"})
    return out


def version_diff(a: dict, b: dict, a_text: str | None = None, b_text: str | None = None) -> list[dict]:
    """Differences between two extractions of two versions of a contract.

    Without the documents, every figure the two extractions state differently
    is listed, including a figure the model's wording mentioned in one version
    only. With the documents, a figure counts as changed only when the contract
    changed it: a figure dropped between the versions must be absent from the
    later text, a figure added must be absent from the earlier text. The
    typed facts of the whole document are the test, so a figure that stands
    elsewhere in the contract keeps a term unchanged."""
    out = []
    doc_a = typed_facts(a_text) if a_text else None
    doc_b = typed_facts(b_text) if b_text else None
    for tid in _term_ids(a, b):
        ta = a.get("terms", {}).get(tid, {})
        tb = b.get("terms", {}).get(tid, {})
        if bool(ta.get("found")) != bool(tb.get("found")):
            out.append({"term": tid, "unit": "found", "a": [str(bool(ta.get("found")))], "b": [str(bool(tb.get("found")))],
                        "message": "present in one version only"})
            continue
        fa, fb = typed_facts(ta.get("value")), typed_facts(tb.get("value"))
        for unit in sorted(set(fa) | set(fb)):
            va, vb = fa.get(unit, set()), fb.get(unit, set())
            if va == vb:
                continue
            if doc_a is not None and doc_b is not None:
                dropped = any(v not in doc_b.get(unit, set()) for v in va - vb)
                added = any(v not in doc_a.get(unit, set()) for v in vb - va)
                if not dropped and not added:
                    continue
            out.append({"term": tid, "unit": unit, "a": sorted(va), "b": sorted(vb),
                        "message": f"{unit}: {', '.join(sorted(va)) or '—'} → {', '.join(sorted(vb)) or '—'}"})
    return out


def _sentences(text: str) -> list[str]:
    body = re.sub(r"\s+", " ", text)
    return [s.strip() for s in re.split(r"(?<=[.;:])\s+(?=[A-Z0-9(\[])", body) if s.strip()]


def document_diff(a_text: str, b_text: str) -> list[dict]:
    """Sentences that changed between two versions of a document, no model involved."""
    sa, sb = _sentences(a_text), _sentences(b_text)
    out = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, sa, sb, autojunk=False).get_opcodes():
        if tag == "equal":
            continue
        out.append({"change": tag, "a": sa[i1:i2], "b": sb[j1:j2]})
    return out


def run_all(inputs: dict) -> dict:
    """inputs: {documents: {id: text}, extractions: {id: record}, pairs: {paper_vs_contract: [[paper, contract]], version_diff: [[a, b]]},
    reference_docs: [ids whose citations are checked against their own text; a committee paper cites the contract, not itself]}"""
    docs, exts, pairs = inputs.get("documents", {}), inputs.get("extractions", {}), inputs.get("pairs", {})
    out: dict = {"schema": [], "quotes_verbatim": [], "references_exist": [], "paper_vs_contract": [], "version_diff": [], "document_diff": []}
    ref_docs = inputs.get("reference_docs") or list(docs)
    for doc_id, ext in exts.items():
        out["schema"] += [dict(f, document=doc_id) for f in schema(ext)]
        if doc_id in docs:
            out["quotes_verbatim"] += [dict(f, document=doc_id) for f in quotes_verbatim(ext, docs[doc_id])]
        if doc_id in docs and doc_id in ref_docs:
            out["references_exist"] += [dict(f, document=doc_id) for f in references_exist(ext, docs[doc_id])]
    for paper, contract in pairs.get("paper_vs_contract", []):
        out["paper_vs_contract"] += [dict(f, paper_id=paper, contract_id=contract) for f in paper_vs_contract(exts[paper], exts[contract])]
    for a, b in pairs.get("version_diff", []):
        out["version_diff"] += [dict(f, a_id=a, b_id=b) for f in version_diff(exts[a], exts[b], docs.get(a), docs.get(b))]
        if a in docs and b in docs:
            out["document_diff"] += [dict(f, a_id=a, b_id=b) for f in document_diff(docs[a], docs[b])]
    return out


def run_all_json(text: str) -> str:
    return json.dumps(run_all(json.loads(text)), ensure_ascii=False)
