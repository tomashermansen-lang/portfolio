"""Validate the synthetic data room against spec/answer-key.json.

Usage: python3 -I tools/validate_synthetic.py [doc-id ...]

For each PPA document: every `quote*` must appear verbatim; every
`forbidden_words` entry must be absent (case-sensitive as written);
the synthetic header line must be present; the word count must sit in
5,000–6,500; no real company names from the denylist. For the v1 draft:
its own quotes present, the v2-only quotes absent. Exit 1 on any failure.
"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KEY = json.loads((ROOT / "spec" / "answer-key.json").read_text())
DATA = ROOT / "dataroom"
HEADER = "Synthetic document, written to demonstrate a method."
DENY = ["Ørsted", "Orsted", "Vestas", "Siemens", "TenneT", "Energinet", "Nord Pool",
        "EPEX", "Iberdrola", "BASF", "Vattenfall", "RWE", "EDF", "Statkraft",
        "Copenhagen Infrastructure", "CIP ", "Kromann", "Plesner", "Bech-Bruun",
        "Gorrissen", "Danske Bank", "Nordea", "Moody", "Standard & Poor", "Fitch"]
WORDS = (5000, 6500)


def quotes(term):
    return [v for k, v in term.items() if k.startswith("quote")]


def check_doc(doc_id):
    fails = []
    path = DATA / f"{doc_id}.md"
    if not path.exists():
        return [f"{doc_id}: file missing"]
    text = path.read_text()
    if HEADER not in text:
        fails.append("header line missing")
    n = len(text.split())
    if doc_id.endswith(("execution", "draft")) and not (WORDS[0] <= n <= WORDS[1]):
        fails.append(f"word count {n} outside {WORDS}")
    for name in DENY:
        if name in text:
            fails.append(f"real name present: {name!r}")
    entry = KEY[doc_id]
    if "same_as" in entry:
        base = KEY[entry["same_as"]]["terms"]
        diffs = entry["differences"]
        for tid, term in base.items():
            d = diffs.get(tid, {})
            for k, v in term.items():
                if not k.startswith("quote"):
                    continue
                if k in d:
                    if d[k] not in text:
                        fails.append(f"{tid}.{k} (v1 variant) missing: {d[k][:60]!r}")
                    if v != d[k] and v in text:
                        fails.append(f"{tid}.{k} v2 text must be absent: {v[:60]!r}")
                elif d.get("note", "").startswith("v1 has NO") and k == "quote":
                    if v in text:
                        fails.append(f"{tid}.{k} v2-only text must be absent: {v[:60]!r}")
                elif v not in text:
                    fails.append(f"{tid}.{k} missing: {v[:60]!r}")
        for bad in ("Thirty per cent (30%) of the Contract Price", "Deemed Delivered Electricity",
                    "one hundred and fifty (150) hours"):
            if bad in text:
                fails.append(f"v2-only phrase present in v1: {bad!r}")
        return [f"{doc_id}: {f}" for f in fails]
    for tid, term in entry["terms"].items():
        for q in quotes(term):
            if q not in text:
                fails.append(f"{tid} missing quote: {q[:70]!r}")
        for w in term.get("forbidden_words", []):
            if w in text:
                fails.append(f"{tid} forbidden word present: {w!r}")
    return [f"{doc_id}: {f}" for f in fails]


if __name__ == "__main__":
    ids = sys.argv[1:] or [k for k in KEY if not k.startswith("_") and "terms" in KEY[k] or "same_as" in KEY.get(k, {})]
    all_fails = []
    for doc_id in ids:
        f = check_doc(doc_id)
        print(f"{doc_id}: {'PASS' if not f else 'FAIL'}")
        for line in f:
            print("  -", line)
        all_fails += f
    sys.exit(1 if all_fails else 0)
