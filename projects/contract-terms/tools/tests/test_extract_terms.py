import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import extract_terms as ex  # noqa: E402


class Prompt(unittest.TestCase):
    def test_prompt_names_all_twelve_terms_and_the_document(self):
        p = ex.build_prompt("doc-x", "BODY TEXT")
        for t in ex.TERMS:
            self.assertIn(f'"{t["id"]}"', p)
        self.assertIn('<document id="doc-x">', p)
        self.assertIn("BODY TEXT", p)


class Parse(unittest.TestCase):
    def test_bare_json(self):
        self.assertEqual(ex.parse_reply('{"terms": {"a": {"found": false}}}')["terms"]["a"]["found"], False)

    def test_fenced_json(self):
        raw = 'Here you go:\n```json\n{"terms": {"a": {"found": true}}}\n```\n'
        self.assertTrue(ex.parse_reply(raw)["terms"]["a"]["found"])

    def test_no_terms_rejected(self):
        with self.assertRaises(ValueError):
            ex.parse_reply('{"x": 1}')


if __name__ == "__main__":
    unittest.main()


class RunNumber(unittest.TestCase):
    def test_next_run_is_one_more_than_the_highest(self):
        self.assertEqual(ex.next_run([]), 1)
        self.assertEqual(ex.next_run(["1", "2", "junk"]), 3)
