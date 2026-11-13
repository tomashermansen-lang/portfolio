"""Record one extraction run: every document in dataroom/ → extractions/<doc-id>.json.

Usage (from a terminal that is logged in to the claude CLI):
  python3 tools/extract_terms.py [--model claude-sonnet-5-5] [--run N] [--only <doc-id>] [--dry-run]

The page never calls a model. Each run is recorded under extractions/runs/<N>/
(the next free number unless --run says otherwise), and tools/evaluate.py
scores run 1 for the table and every run for stability. The model name, date
and document hash are stored with each record.

The prompt asks for the twelve terms of spec/terms.json as JSON, with a
verbatim quote per term, and "found": false where the document is silent or
only refers to something not attached. The raw model reply is kept beside the
parsed record so a parse failure can be read.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TERMS = json.loads((ROOT / "spec" / "terms.json").read_text())["terms"]
DATA = ROOT / "dataroom"
RUNS = ROOT / "extractions" / "runs"
DEFAULT_MODEL = "claude-sonnet-5-5"

PROMPT = """You extract the key terms of a renewable energy contract for an investment committee table.

Read the document between the <document> tags and return ONE JSON object and nothing else: no prose, no code fence.

Shape:
{{
  "terms": {{
    "<term id>": {{
      "found": true | false,
      "value": "<one or two sentences stating the term with its numbers and dates, or null>",
      "quote": "<a sentence copied VERBATIM from the document that states the term, or null>",
      "clause": "<where in the document: Part, section number or annex, or null>",
      "note": "<why not found, or anything the reader must know, or empty string>"
    }},
    ...
  }}
}}

Rules:
1. The quote must be copied character for character from the document. Never paraphrase inside "quote".
2. If the document does not address a term, set "found": false, "value": null, "quote": null and say so in "note". Do not infer from industry practice.
3. If a term is only defined by reference to a document that is not attached (an annex marked to be agreed, a missing schedule), set "found": false and quote the reference in "note".
4. Read meaning, not headings: a term may sit under a different section title than its name.
5. Where a value is stated in an annex or election sheet rather than the body, take it from there and say where it is in "clause".
6. The twelve term ids and what each asks for:
{terms}

<document id="{doc_id}">
{document}
</document>"""


def build_prompt(doc_id: str, document: str) -> str:
    lines = "\n".join(f'- "{t["id"]}": {t["label"]}. {t["ask"]}' for t in TERMS)
    return PROMPT.format(terms=lines, doc_id=doc_id, document=document)


def parse_reply(raw: str) -> dict:
    """Accept a bare JSON object, or one wrapped in a code fence or prose."""
    s = raw.strip()
    m = re.search(r"\{.*\}", s, re.S)
    if not m:
        raise ValueError("no JSON object in reply")
    obj = json.loads(m.group(0))
    if "terms" not in obj:
        raise ValueError("reply has no 'terms'")
    return obj


def run_claude(prompt: str, model: str) -> str:
    cmd = ["claude", "-p", "--model", model, "--output-format", "json"]
    res = subprocess.run(cmd, input=prompt, capture_output=True, text=True, timeout=600)
    if res.returncode != 0:
        raise RuntimeError(f"claude exited {res.returncode}: {res.stderr.strip()[:500]}")
    envelope = json.loads(res.stdout)
    return envelope.get("result", "")


def next_run(existing: list[str]) -> int:
    nums = [int(n) for n in existing if n.isdigit()]
    return max(nums, default=0) + 1


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--run", type=int, help="run number; default: the next free one")
    ap.add_argument("--only", action="append", default=[])
    ap.add_argument("--dry-run", action="store_true", help="print the prompt for the first document and stop")
    a = ap.parse_args(argv)
    RUNS.mkdir(parents=True, exist_ok=True)
    run = a.run or next_run([d.name for d in RUNS.iterdir() if d.is_dir()])
    OUT = RUNS / str(run)
    if not a.dry_run:
        OUT.mkdir(exist_ok=True)
        print(f"run {run} → extractions/runs/{run}/")
    docs = sorted(DATA.glob("*.md"))
    if a.only:
        docs = [d for d in docs if d.stem in a.only]
    for path in docs:
        doc_id = path.stem
        document = path.read_text()
        prompt = build_prompt(doc_id, document)
        if a.dry_run:
            print(prompt)
            return 0
        print(f"{doc_id}: {len(document.split())} words → {a.model} …", flush=True)
        raw = run_claude(prompt, a.model)
        (OUT / f"{doc_id}.raw.txt").write_text(raw)
        try:
            obj = parse_reply(raw)
        except (ValueError, json.JSONDecodeError) as e:
            print(f"  parse failed: {e}; raw reply kept in extractions/{doc_id}.raw.txt")
            continue
        record = {
            "document_id": doc_id,
            "model": a.model,
            "run": run,
            "run_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
            "source_sha256": hashlib.sha256(document.encode()).hexdigest(),
            "terms": {t["id"]: obj["terms"].get(t["id"], {"found": False, "value": None, "quote": None, "clause": None, "note": "not in reply"}) for t in TERMS},
        }
        (OUT / f"{doc_id}.json").write_text(json.dumps(record, indent=1, ensure_ascii=False))
        found = sum(1 for t in record["terms"].values() if t.get("found"))
        print(f"  recorded {found}/12 found → extractions/runs/{run}/{doc_id}.json")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
