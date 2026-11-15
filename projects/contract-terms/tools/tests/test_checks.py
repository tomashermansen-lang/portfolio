"""Tests for tools/checks.py — the deterministic checks that also run in the browser.

The first tests read the recorded run (extractions/runs/1), per the
recorded-fixture rule; synthetic inputs come after.
"""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import checks  # noqa: E402

RUN1 = ROOT / "extractions" / "runs" / "1"


def load(doc_id):
    return json.loads((RUN1 / f"{doc_id}.json").read_text())


def doc(doc_id):
    return (ROOT / "dataroom" / f"{doc_id}.md").read_text()


class TypedFacts(unittest.TestCase):
    def test_units_from_prose(self):
        f = checks.typed_facts("ten (10) years from COD; EUR 2,500,000; 9 months; 150 hours; 48.0 MW; 158 GWh/yr; 30 % CPI; 60 kV; EUR 1.75m cap; EUR 250k; EUR 54.50/MWh; 1 Oct 2027; 10 Business Days")
        self.assertEqual(f["years"], {"10"})
        self.assertEqual(f["eur"], {"2500000", "1750000", "250000"})
        self.assertEqual(f["eur_per_mwh"], {"54.5"})
        self.assertEqual(f["months"], {"9"})
        self.assertEqual(f["hours"], {"150"})
        self.assertEqual(f["mw"], {"48"})
        self.assertEqual(f["mwh"], {"158000"})
        self.assertEqual(f["percent"], {"30"})
        self.assertEqual(f["kv"], {"60"})
        self.assertEqual(f["date"], {"1 october 2027"})
        self.assertEqual(f["business_days"], {"10"})
        self.assertNotIn("days", f)

    def test_number_words_and_per_cent(self):
        f = checks.typed_facts("twelve years; nine months; Thirty per cent; one hundred and fifty (150) hours")
        self.assertEqual(f["years"], {"12"})
        self.assertEqual(f["months"], {"9"})
        self.assertEqual(f["percent"], {"30"})
        self.assertEqual(f["hours"], {"150"})


class Twelfths(unittest.TestCase):
    def test_twelfths_of_a_year_are_months(self):
        self.assertEqual(checks.typed_facts("nine twelfths of the Expected Annual Production")["months"], {"9"})
        self.assertEqual(checks.typed_facts("six (6) twelfths of expected payments")["months"], {"6"})


class PaperVsContract(unittest.TestCase):
    def test_ic_paper_planted_errors_are_found_and_nothing_else(self):
        findings = checks.paper_vs_contract(load("havrebakke-ic-key-terms"), load("havrebakke-ppa-v2-execution"))
        flagged = {(f["term"], f["unit"]) for f in findings}
        self.assertEqual(flagged, {("3_supply_period", "years"), ("10_credit_support", "eur")})
        by_term = {f["term"]: f for f in findings}
        self.assertEqual(by_term["3_supply_period"]["paper"], ["10"])
        self.assertEqual(by_term["3_supply_period"]["contract"], ["12"])
        self.assertEqual(by_term["10_credit_support"]["paper"], ["2500000"])

    def test_dd_summary_planted_error_is_found_and_nothing_else(self):
        findings = checks.paper_vs_contract(load("havrebakke-legal-dd-summary"), load("havrebakke-ppa-v2-execution"))
        self.assertEqual([(f["term"], f["unit"]) for f in findings], [("3_supply_period", "years")])


class VersionDiff(unittest.TestCase):
    def test_v1_vs_v2_changes_are_the_five_negotiated_terms(self):
        diffs = checks.version_diff(load("havrebakke-ppa-v1-draft"), load("havrebakke-ppa-v2-execution"))
        changed = {d["term"] for d in diffs}
        negotiated = {"3_supply_period", "4_cod_and_delay", "5_price_and_indexation", "8_curtailment", "10_credit_support"}
        self.assertTrue(negotiated <= changed, changed)
        # extraction wording can add noise (run 1: v1 mentions "75% of P50", v2 does not); it must stay small
        self.assertLessEqual(len(changed - negotiated), 1, changed - negotiated)
        for untouched in ("1_parties_and_buyer_credit", "2_facility", "7_product_and_certificates", "9_delivery_point_and_balancing"):
            self.assertNotIn(untouched, changed)
        price = [d for d in diffs if d["term"] == "5_price_and_indexation" and d["unit"] == "eur_per_mwh"][0]
        self.assertEqual((price["a"], price["b"]), (["58"], ["54.5"]))

    def test_a_figure_the_model_dropped_but_the_contract_still_states_is_not_a_change(self):
        # run 1: the draft's wording mentions "75% of P50", the final's does not; both contracts state 75 per cent
        diffs = checks.version_diff(load("havrebakke-ppa-v1-draft"), load("havrebakke-ppa-v2-execution"),
                                    doc("havrebakke-ppa-v1-draft"), doc("havrebakke-ppa-v2-execution"))
        changed = {d["term"] for d in diffs}
        self.assertEqual(changed, {"3_supply_period", "4_cod_and_delay", "5_price_and_indexation", "8_curtailment", "10_credit_support"})
        self.assertNotIn("6_volume_and_performance", changed)

    def test_run_all_hands_the_documents_to_version_diff(self):
        inputs = {"documents": {k: doc(k) for k in ("havrebakke-ppa-v1-draft", "havrebakke-ppa-v2-execution")},
                  "extractions": {k: load(k) for k in ("havrebakke-ppa-v1-draft", "havrebakke-ppa-v2-execution")},
                  "pairs": {"version_diff": [["havrebakke-ppa-v1-draft", "havrebakke-ppa-v2-execution"]]}}
        out = checks.run_all(inputs)
        self.assertNotIn("6_volume_and_performance", {d["term"] for d in out["version_diff"]})

    def test_presence_change_is_a_diff(self):
        a = {"terms": {"x": {"found": False, "value": None}}}
        b = {"terms": {"x": {"found": True, "value": "150 hours"}}}
        d = checks.version_diff(a, b)
        self.assertEqual(d[0]["unit"], "found")


class DocumentDiff(unittest.TestCase):
    def test_v1_vs_v2_sentence_diff_shows_the_negotiated_changes(self):
        d = checks.document_diff(doc("havrebakke-ppa-v1-draft"), doc("havrebakke-ppa-v2-execution"))
        a_text = " ".join(s for f in d for s in f["a"])
        b_text = " ".join(s for f in d for s in f["b"])
        self.assertIn("ten (10) years", a_text)
        self.assertIn("twelve (12) years", b_text)
        self.assertIn("EUR 58.00", a_text)
        self.assertIn("EUR 54.50", b_text)
        self.assertNotIn("Guarantees of Origin issued in respect of the Metered Output shall be transferred", b_text)

    def test_identical_documents_have_no_diff(self):
        self.assertEqual(checks.document_diff("A. B.", "A. B."), [])


class QuotesVerbatim(unittest.TestCase):
    def test_every_quote_of_run_1_is_in_its_document(self):
        for doc_id in ("havrebakke-ppa-v2-execution", "olivos-solar-ppa-execution", "lichtung-offshore-ppa-execution"):
            self.assertEqual(checks.quotes_verbatim(load(doc_id), doc(doc_id)), [], doc_id)

    def test_a_paraphrased_quote_is_a_finding(self):
        ext = {"terms": {"3_supply_period": {"found": True, "value": "12 years", "quote": "Supply Period: twelve years commencing on COD."}}}
        f = checks.quotes_verbatim(ext, doc("havrebakke-ppa-v2-execution"))
        self.assertEqual(f[0]["term"], "3_supply_period")


class Schema(unittest.TestCase):
    def test_run_1_records_are_well_formed(self):
        for p in RUN1.glob("*.json"):
            self.assertEqual(checks.schema(json.loads(p.read_text())), [], p.name)

    def test_found_without_quote_and_not_found_without_note(self):
        ext = {"terms": {t: {"found": True, "value": "x", "quote": "q", "clause": "", "note": ""} for t in checks.TERM_IDS}}
        ext["terms"]["3_supply_period"] = {"found": True, "value": "x", "quote": None, "clause": "", "note": ""}
        ext["terms"]["8_curtailment"] = {"found": False, "value": None, "quote": None, "clause": "", "note": ""}
        problems = {f["term"]: f["message"] for f in checks.schema(ext)}
        self.assertIn("3_supply_period", problems)
        self.assertIn("8_curtailment", problems)


class RunAll(unittest.TestCase):
    def test_run_all_returns_findings_grouped_by_check(self):
        inputs = {
            "documents": {d: doc(d) for d in ("havrebakke-ppa-v2-execution", "havrebakke-ppa-v1-draft")},
            "extractions": {d: load(d) for d in ("havrebakke-ppa-v2-execution", "havrebakke-ppa-v1-draft", "havrebakke-ic-key-terms", "havrebakke-legal-dd-summary")},
            "pairs": {"paper_vs_contract": [["havrebakke-ic-key-terms", "havrebakke-ppa-v2-execution"], ["havrebakke-legal-dd-summary", "havrebakke-ppa-v2-execution"]],
                      "version_diff": [["havrebakke-ppa-v1-draft", "havrebakke-ppa-v2-execution"]]},
        }
        out = checks.run_all(inputs)
        self.assertEqual(set(out), {"schema", "quotes_verbatim", "references_exist", "paper_vs_contract", "version_diff", "document_diff"})
        self.assertTrue(out["document_diff"])
        self.assertEqual(len(out["paper_vs_contract"]), 3)
        self.assertEqual(out["schema"], [])

    def test_run_all_accepts_json_text(self):
        out = checks.run_all_json(json.dumps({"documents": {}, "extractions": {}, "pairs": {}}))
        self.assertEqual(json.loads(out)["schema"], [])


if __name__ == "__main__":
    unittest.main()


class TermIds(unittest.TestCase):
    def test_term_ids_match_spec(self):
        spec = json.loads((ROOT / "spec" / "terms.json").read_text())["terms"]
        self.assertEqual(checks.TERM_IDS, [t["id"] for t in spec])


class References(unittest.TestCase):
    """The model's notes and clause fields cite sections; a citation must point at a clause that exists."""

    def test_section_numbers_are_parsed_from_text(self):
        refs = checks.references_in("Related provisions: negative price hours (7.4); section 4.5; see s. 3.3 and Annex 2; sections 13.3 and 13.4; Part I, Supply Period")
        self.assertEqual(refs, {"7.4", "4.5", "3.3", "Annex 2", "13.3", "13.4", "Part I"})

    def test_amounts_and_dates_are_not_references(self):
        self.assertEqual(checks.references_in("EUR 54.50 per MWh from 1 January 2029; 48.0 MW; 97.5% availability"), set())

    def test_clause_index_of_a_document(self):
        idx = checks.clause_index(doc("olivos-solar-ppa-execution"))
        self.assertIn("7.4", idx)
        self.assertIn("17.3", idx)
        self.assertIn("Annex 2", idx)
        self.assertIn("Part I", idx)
        self.assertNotIn("99.9", idx)

    def test_run_1_notes_cite_only_existing_clauses(self):
        for doc_id in ("havrebakke-ppa-v2-execution", "havrebakke-ppa-v1-draft", "olivos-solar-ppa-execution"):
            self.assertEqual(checks.references_exist(load(doc_id), doc(doc_id)), [], doc_id)

    def test_lichtung_citation_of_the_missing_annex_is_the_only_finding(self):
        f = checks.references_exist(load("lichtung-offshore-ppa-execution"), doc("lichtung-offshore-ppa-execution"))
        self.assertEqual({(x["term"], x["reference"]) for x in f}, {("11_default_and_termination", "Annex 5")})

    def test_a_dangling_reference_is_a_finding(self):
        ext = {"terms": {"8_curtailment": {"found": False, "value": None, "quote": None, "clause": None, "note": "Not addressed; but see section 99.9 and Annex 7."}}}
        f = checks.references_exist(ext, doc("olivos-solar-ppa-execution"))
        self.assertEqual([x["reference"] for x in f], ["99.9", "Annex 7"])
        self.assertEqual(f[0]["term"], "8_curtailment")
