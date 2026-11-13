#!/usr/bin/env bash
# Rebuild everything derived from the recorded runs: eval.json, checks.json, sql/seed.sql. Then the tests.
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -I tools/evaluate.py --write | tail -4
python3 -I tools/run_checks.py | head -8
python3 -I tools/build_db.py | tail -1
python3 -I tools/record_console.py
python3 -I tools/extract_terms.py --dry-run --only havrebakke-ppa-v2-execution > extractions/prompt-example.txt
python3 -I -m unittest discover -s tools/tests -t . 2>&1 | tail -1
python3 -I tools/spec_runner.py --write | tail -1
node tools/spec_runner.js --write | tail -1
python3 -I tools/wireframes.py
node tools/page_smoke.js
