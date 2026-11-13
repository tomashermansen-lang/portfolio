"""Tests for tools/evaluate.py — written before the implementation."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import evaluate as ev  # noqa: E402

KEY = json.loads((ROOT / "spec" / "answer-key.json").read_text())
V2_DOC = (ROOT / "dataroom" / "havrebakke-ppa-v2-execution.md").read_text()


class Facts(unittest.TestCase):
    def test_dates_and_numbers_from_key_value(self):
        facts = ev.facts_of("Target COD 1 October 2027; Longstop Date 31 March 2028; delay damages EUR 9,600 per day, capped at EUR 1,750,000.")
        self.assertIn("1 october 2027", facts)
        self.assertIn("31 march 2028", facts)
        self.assertIn("9600", facts)
        self.assertIn("1750000", facts)
        self.assertNotIn("1", facts)  # the day of a date is not a separate fact

    def test_letters_attached_to_digits_are_not_facts(self):
        self.assertEqual(ev.facts_of("P50 yield, DK1 zone, 48.0 MW"), {"48"})

    def test_decimal_normalised(self):
        self.assertEqual(ev.facts_of("EUR 54.50 per MWh"), {"54.5"})

    def test_words_in_parentheses_numbers(self):
        self.assertEqual(ev.facts_of("twelve (12) years"), {"12"})

    def test_missing_facts_reported(self):
        missing = ev.missing_facts("EUR 9,600 per day, cap EUR 1,750,000", "LDs of EUR 9600/day")
        self.assertEqual(missing, ["1750000"])


class MissingFactsNamedOnce(unittest.TestCase):
    def test_a_typed_fact_is_not_also_listed_as_a_bare_number(self):
        key = ev.key_term_from_value("notice of 60 days")
        got = {"found": True, "value": "notice must be given in writing", "quote": "x"}
        self.assertEqual(ev.judge(key, got, "x")["missing_facts"], ["60 days"])


class Source(unittest.TestCase):
    def test_quote_must_be_verbatim_in_document(self):
        self.assertTrue(ev.in_document("Supply Period: twelve (12) years commencing on the Commercial Operation Date.", V2_DOC))
        self.assertFalse(ev.in_document("Supply Period: twelve years commencing", V2_DOC))

    def test_overlap_with_key_quote(self):
        key = ["The Contract Price is the price per MWh set out in Annex 2 (Election Sheet).", "Contract Price: EUR 54.50 per MWh"]
        self.assertTrue(ev.overlaps("Contract Price: EUR 54.50 per MWh", key))
        self.assertTrue(ev.overlaps("…and the Contract Price is the price per MWh set out in Annex 2 (Election Sheet). Payment…", key))
        self.assertFalse(ev.overlaps("Longstop Date means 31 March 2028.", key))


class EffectiveKey(unittest.TestCase):
    def test_v1_inherits_v2_and_overlays_differences(self):
        k = ev.effective_key(KEY, "havrebakke-ppa-v1-draft")
        inherited = {kk: vv for kk, vv in k["2_facility"].items() if kk not in ("facts", "typed")}
        self.assertEqual(inherited, KEY["havrebakke-ppa-v2-execution"]["terms"]["2_facility"])
        self.assertIn("ten (10) years", k["3_supply_period"]["quote"])
        self.assertEqual(k["3_supply_period"]["facts"], ["10"])
        self.assertIn("58.00", k["5_price_and_indexation"]["quote_2"])
        self.assertTrue(k["8_curtailment"]["present"])

    def test_v2_facts_come_from_value(self):
        k = ev.effective_key(KEY, "havrebakke-ppa-v2-execution")
        self.assertIn("158000", k["6_volume_and_performance"]["facts"])


class Verdicts(unittest.TestCase):
    def term(self, found, value, quote):
        return {"found": found, "value": value, "quote": quote, "clause": "", "note": ""}

    def test_correct(self):
        key = {"present": True, "facts": ["12"], "quote": "Supply Period: twelve (12) years commencing on the Commercial Operation Date."}
        got = self.term(True, "12 years from COD", "Supply Period: twelve (12) years commencing on the Commercial Operation Date.")
        self.assertEqual(ev.judge(key, got, V2_DOC)["verdict"], "correct")

    def test_absent_term_correctly_not_found(self):
        key = {"present": False, "facts": []}
        self.assertEqual(ev.judge(key, self.term(False, None, None), "")["verdict"], "correct")

    def test_absent_term_invented(self):
        key = {"present": False, "facts": []}
        self.assertEqual(ev.judge(key, self.term(True, "Buyer may curtail", "x"), "")["verdict"], "invented")

    def test_present_term_missed(self):
        key = {"present": True, "facts": ["12"], "quote": "q"}
        self.assertEqual(ev.judge(key, self.term(False, None, None), "")["verdict"], "missed")

    def test_wrong_value(self):
        key = {"present": True, "facts": ["12"], "quote": "Supply Period: twelve (12) years commencing on the Commercial Operation Date."}
        got = self.term(True, "10 years", "Supply Period: twelve (12) years commencing on the Commercial Operation Date.")
        self.assertEqual(ev.judge(key, got, V2_DOC)["verdict"], "wrong_value")

    def test_quote_not_in_document(self):
        key = {"present": True, "facts": ["12"], "quote": "Supply Period: twelve (12) years commencing on the Commercial Operation Date."}
        got = self.term(True, "12 years", "Supply Period: twelve years.")
        self.assertEqual(ev.judge(key, got, V2_DOC)["verdict"], "quote_not_verbatim")



class PlantedErrors(unittest.TestCase):
    def test_paper_extraction_must_repeat_the_paper(self):
        key = KEY["havrebakke-ic-key-terms"]
        got = {"terms": {"3_supply_period": {"found": True, "value": "10 years from COD"},
                         "10_credit_support": {"found": True, "value": "Seller bank guarantee EUR 2,000,000"}}}
        res = ev.judge_paper(key, got)
        self.assertEqual(res["3_supply_period"]["verdict"], "faithful")
        self.assertEqual(res["10_credit_support"]["verdict"], "not_faithful")


if __name__ == "__main__":
    unittest.main()


class FactsRubricRound2(unittest.TestCase):
    """Added after the first recorded run: the rubric, not the model, failed these."""

    def test_number_words_count_as_facts(self):
        self.assertEqual(ev.facts_of("twelve years from COD"), {"12"})
        self.assertEqual(ev.facts_of("Fifteen years, ending 31 December 2043"), {"15", "31 december 2043"})
        self.assertEqual(ev.facts_of("Thirty per cent of the price; twenty-five hours"), {"30", "25"})
        self.assertEqual(ev.facts_of("six months of expected payments"), {"6"})

    def test_section_and_annex_references_are_not_facts(self):
        self.assertEqual(ev.facts_of("the allocation sits in section 17; see Annex 2 and s. 4.5 and Part II 9.2"), set())

    def test_date_fact_satisfied_when_day_month_and_year_are_split(self):
        self.assertEqual(ev.missing_facts("from 1 January 2029", "adjusted each 1 January from 2029"), [])
        self.assertEqual(ev.missing_facts("from 1 January 2029", "adjusted each 1 January from 2030"), ["1 january 2029"])


class FactsRubricRound3(unittest.TestCase):
    """Run 4 of 5: 'escalating on 1 January of each Contract Year' made '1' a bare fact."""

    def test_day_and_month_without_year_is_one_fact(self):
        self.assertEqual(ev.facts_of("on 1 January of each Contract Year"), {"1 january"})

    def test_day_month_fact_satisfied_by_a_full_date(self):
        self.assertEqual(ev.missing_facts("escalating on 1 January of each Contract Year", "From 1 January 2030 it rises 2% each year"), [])
        self.assertEqual(ev.missing_facts("on 1 January of each Contract Year", "From 1 April 2030"), ["1 january"])


class SourceRound2(unittest.TestCase):
    def test_verbatim_quote_from_another_sentence_is_correct_but_flagged(self):
        key = {"present": True, "facts": ["12"], "quote": "Supply Period: twelve (12) years commencing on the Commercial Operation Date."}
        got = {"found": True, "value": "12 years", "quote": "Longstop Date means 31 March 2028."}
        r = ev.judge(key, got, V2_DOC)
        self.assertEqual(r["verdict"], "correct")
        self.assertFalse(r["source_matches_key"])

    def test_source_flag_true_when_it_matches(self):
        key = {"present": True, "facts": ["12"], "quote": "Supply Period: twelve (12) years commencing on the Commercial Operation Date."}
        got = {"found": True, "value": "12 years", "quote": "Supply Period: twelve (12) years commencing on the Commercial Operation Date."}
        self.assertTrue(ev.judge(key, got, V2_DOC)["source_matches_key"])


class Runs(unittest.TestCase):
    def test_stability_counts_correct_per_term_across_runs(self):
        runs = {
            1: {"docA": {"terms": {"t1": {"verdict": "correct"}, "t2": {"verdict": "wrong_value"}}}},
            2: {"docA": {"terms": {"t1": {"verdict": "correct"}, "t2": {"verdict": "correct"}}}},
            3: {"docA": {"terms": {"t1": {"verdict": "missed"}, "t2": {"verdict": "correct"}}}},
        }
        s = ev.stability(runs)
        self.assertEqual(s["docA"]["t1"], {"correct": 2, "runs": 3, "verdicts": ["correct", "correct", "missed"]})
        self.assertEqual(s["docA"]["t2"]["correct"], 2)

    def test_run_dirs_are_numbered(self):
        self.assertEqual(ev.run_numbers(["1", "3", "x", "2"]), [1, 2, 3])


class UnitAwareFacts(unittest.TestCase):
    """A figure counts only with its unit: '12 months' does not satisfy a key that says '12 years'."""

    def test_unit_mismatch_is_a_missing_fact(self):
        key = ev.key_term_from_value("12 years from the Commercial Operation Date.")
        self.assertEqual(ev.judge(key, {"found": True, "value": "The Supply Period is 12 months from COD.", "quote": "Supply Period: twelve (12) years commencing on the Commercial Operation Date."}, V2_DOC)["verdict"], "wrong_value")
        self.assertEqual(ev.judge(key, {"found": True, "value": "The Supply Period is twelve years from COD.", "quote": "Supply Period: twelve (12) years commencing on the Commercial Operation Date."}, V2_DOC)["verdict"], "correct")

    def test_amount_needs_its_currency_unit(self):
        key = ev.key_term_from_value("Seller: bank guarantee of EUR 2,000,000 from Financial Close until 12 months after COD.")
        self.assertEqual(ev.judge(key, {"found": True, "value": "A guarantee of 2,000,000 for 12 months.", "quote": "x"}, "x")["verdict"], "wrong_value")

    def test_run_1_scores_unchanged_under_the_stricter_rule(self):
        report = ev.evaluate_all(KEY)
        self.assertEqual(report["run_summaries"][1], {"correct": 46, "wrong_value": 2})
