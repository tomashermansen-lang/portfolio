"""Run tools/checks.py on the recorded run and write extractions/checks.json.

Usage: python3 -I tools/run_checks.py [--run N]

The page runs the same checks in the browser (Pyodide); this file is the
local run of them, used by the tests' fixtures and as the page's fallback
when Pyodide cannot load.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import checks  # noqa: E402

PAIRS = {
    "paper_vs_contract": [["havrebakke-ic-key-terms", "havrebakke-ppa-v2-execution"],
                          ["havrebakke-legal-dd-summary", "havrebakke-ppa-v2-execution"]],
    "version_diff": [["havrebakke-ppa-v1-draft", "havrebakke-ppa-v2-execution"]],
}


def main(argv: list[str]) -> int:
    run = argv[argv.index("--run") + 1] if "--run" in argv else "1"
    run_dir = ROOT / "extractions" / "runs" / run
    inputs = {
        "documents": {p.stem: p.read_text() for p in (ROOT / "dataroom").glob("*.md")},
        "extractions": {p.stem: json.loads(p.read_text()) for p in run_dir.glob("*.json")},
        "pairs": PAIRS,
        "reference_docs": ["havrebakke-ppa-v2-execution", "havrebakke-ppa-v1-draft", "olivos-solar-ppa-execution", "lichtung-offshore-ppa-execution"],
    }
    out = checks.run_all(inputs)
    out["run"] = int(run)
    (ROOT / "extractions" / "checks.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
    for name, findings in out.items():
        if name == "run":
            continue
        print(f"{name}: {len(findings)}")
        for f in findings[:12]:
            print("  ", f.get("message") or f.get("change"), "|", f.get("document") or f.get("paper_id") or f.get("a_id"), "/", f.get("term", ""))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
