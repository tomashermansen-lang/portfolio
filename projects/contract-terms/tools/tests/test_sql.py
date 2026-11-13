"""The schema, the generated seed and the three queries run in sqlite3 as they will in sql.js."""
import sqlite3
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import build_db  # noqa: E402


def connect():
    con = sqlite3.connect(":memory:")
    con.executescript((ROOT / "sql" / "schema.sql").read_text())
    con.executescript(build_db.seed_sql(build_db.build_rows()))
    return con


class Seed(unittest.TestCase):
    def setUp(self):
        self.con = connect()

    def test_every_run_has_twelve_terms_per_document(self):
        for run, doc, n in self.con.execute("SELECT run, document_id, COUNT(*) FROM extractions GROUP BY run, document_id"):
            self.assertEqual(n, 12, (run, doc))

    def test_verdicts_follow_the_evaluation(self):
        v = self.con.execute("SELECT verdict FROM extractions WHERE run=1 AND document_id='lichtung-offshore-ppa-execution' AND term_id='7_product_and_certificates'").fetchone()[0]
        self.assertEqual(v, "wrong_value")
        n = self.con.execute("SELECT COUNT(*) FROM extractions WHERE run=1 AND verdict='correct'").fetchone()[0]
        self.assertEqual(n, 46)

    def test_review_outcomes_follow_verdicts_and_checks(self):
        row = self.con.execute("SELECT outcome FROM reviews WHERE document_id='lichtung-offshore-ppa-execution' AND term_id='7_product_and_certificates'").fetchone()
        self.assertEqual(row[0], "flagged")  # wrong against the key
        row = self.con.execute("SELECT outcome FROM reviews WHERE document_id='havrebakke-ppa-v2-execution' AND term_id='3_supply_period'").fetchone()
        self.assertEqual(row[0], "flagged")  # the DD summary and IC paper disagree with the contract here
        row = self.con.execute("SELECT outcome FROM reviews WHERE document_id='olivos-solar-ppa-execution' AND term_id='5_price_and_indexation'").fetchone()
        self.assertEqual(row[0], "confirmed")
        self.assertEqual(self.con.execute("SELECT COUNT(*) FROM reviews WHERE outcome NOT IN ('confirmed','flagged')").fetchone()[0], 0)

    def test_review_log_is_append_only_and_the_latest_row_counts(self):
        # a second decision on the same term is a new row; both stay, and the queries read the later one
        doc, term = "olivos-solar-ppa-execution", "5_price_and_indexation"
        sha = self.con.execute("SELECT document_sha256 FROM reviews WHERE document_id=? AND term_id=?", (doc, term)).fetchone()[0]
        self.assertEqual(len(sha), 64)
        self.con.execute("INSERT INTO reviews VALUES (?, ?, ?, 'analyst', '2026-12-01T10:00:00', 12.0, 'flagged', 'second look')", (doc, sha, term))
        self.assertEqual(self.con.execute("SELECT COUNT(*) FROM reviews WHERE document_id=? AND term_id=?", (doc, term)).fetchone()[0], 2)
        cur = self.con.execute((ROOT / "sql" / "queries" / "1_review_effort_per_contract.sql").read_text())
        cols = [c[0] for c in cur.description]
        row = {r[cols.index("document")]: r for r in cur.fetchall()}[doc]
        self.assertEqual(row[cols.index("flagged")], 1)
        self.assertEqual(row[cols.index("terms")], 12)

    def test_checks_table_holds_the_three_paper_findings(self):
        n = self.con.execute("SELECT COUNT(*) FROM checks WHERE check_name='paper_vs_contract'").fetchone()[0]
        self.assertEqual(n, 3)


class Queries(unittest.TestCase):
    def setUp(self):
        self.con = connect()

    def run_query(self, name):
        cur = self.con.execute((ROOT / "sql" / "queries" / name).read_text())
        return [c[0] for c in cur.description], cur.fetchall()

    def test_effort_per_contract(self):
        cols, rows = self.run_query("1_review_effort_per_contract.sql")
        by = {r[cols.index("document")]: r for r in rows}
        self.assertEqual(len(rows), 4)
        self.assertEqual(by["lichtung-offshore-ppa-execution"][cols.index("flagged")], 3)  # two wrong against the key, one missing annex
        self.assertEqual(by["olivos-solar-ppa-execution"][cols.index("first_pass_pct")], 100)
        self.assertEqual(by["havrebakke-ppa-v2-execution"][cols.index("flagged")], 2)
        self.assertEqual(by["havrebakke-ppa-v1-draft"][cols.index("flagged")], 0)

    def test_cycle_time(self):
        cols, rows = self.run_query("2_cycle_time_to_committee.sql")
        self.assertEqual(len(rows), 3)
        by = {r[cols.index("project")]: r for r in rows}
        for r in rows:
            self.assertEqual(r[cols.index("days_to_reviewed_table")], 2.0)
        self.assertEqual(by["Havrebakke Wind Farm"][cols.index("days_to_committee")], 21.0)
        self.assertIsNone(by["Lichtung Offshore"][cols.index("days_to_committee")])

    def test_terms_that_need_a_human(self):
        cols, rows = self.run_query("3_terms_that_need_a_human.sql")
        self.assertEqual(len(rows), 12)
        by = {r[cols.index("ord")]: r for r in rows}
        runs = len([d for d in (ROOT / "extractions" / "runs").iterdir() if d.is_dir()])
        self.assertEqual(by[7][cols.index("runs")], runs)
        self.assertLess(by[7][cols.index("model_right_pct")], 100)   # Lichtung GoO number, wrong in most runs
        self.assertEqual(by[3][cols.index("model_right_pct")], 100)
        self.assertEqual(by[3][cols.index("check_findings")], 3)     # two papers disagree with the contract on the term
        self.assertEqual(rows[0][cols.index("ord")], 12)             # change in law: wrong in every run, sorts first


if __name__ == "__main__":
    unittest.main()


class BaselineAndFacts(unittest.TestCase):
    def setUp(self):
        self.con = connect()

    def run_query(self, name):
        cur = self.con.execute((ROOT / "sql" / "queries" / name).read_text())
        return [c[0] for c in cur.description], cur.fetchall()

    def test_baseline_rows_say_what_they_rest_on(self):
        rows = self.con.execute("SELECT metric, value, basis FROM baseline").fetchall()
        self.assertEqual({r[0] for r in rows}, {"minutes_per_contract", "days_to_reviewed_table", "discrepancies_per_paper", "contracts_processed"})
        self.assertEqual([r for r in rows if r[0] == "discrepancies_per_paper"][0][1:], (None, "not measured"))
        self.assertTrue(all(r[2] in ("assumed", "measured", "not measured") for r in rows))

    def test_against_baseline_has_a_row_per_metric_and_null_where_not_measured(self):
        cols, rows = self.run_query("4_time_saved_against_baseline.sql")
        by = {r[cols.index("metric")]: r for r in rows}
        self.assertEqual(len(rows), 4)
        self.assertLess(by["minutes_per_contract"][cols.index("change")], 0)   # fewer minutes
        self.assertIsNone(by["discrepancies_per_paper"][cols.index("before")])
        self.assertEqual(by["discrepancies_per_paper"][cols.index("after")], 1.5)   # 3 findings over 2 papers
        self.assertEqual(by["minutes_per_contract"][cols.index("before_basis")], "assumed")

    def test_facts_are_typed_from_run_1(self):
        v = self.con.execute("SELECT value FROM facts WHERE run=1 AND document_id='havrebakke-ppa-v2-execution' AND term_id='8_curtailment' AND unit='hours'").fetchall()
        self.assertIn(("150",), v)

    def test_portfolio_question_reads_across_contracts(self):
        cols, rows = self.run_query("5_a_portfolio_question.sql")
        by = {r[cols.index("contract")]: r for r in rows}
        self.assertEqual(len(rows), 4)
        self.assertEqual(by["havrebakke-ppa-v2-execution"][cols.index("curtailment_cap_hours")], 150)
        self.assertIsNone(by["havrebakke-ppa-v1-draft"][cols.index("curtailment_cap_hours")])       # no buyer curtailment in the draft
        self.assertIsNone(by["olivos-solar-ppa-execution"][cols.index("curtailment_cap_hours")])    # never mentioned
        self.assertEqual(by["lichtung-offshore-ppa-execution"][cols.index("supply_years")], 15)
        self.assertEqual(by["olivos-solar-ppa-execution"][cols.index("price_eur_per_mwh")], 38.75)
        self.assertEqual(by["havrebakke-ppa-v1-draft"][cols.index("price_eur_per_mwh")], 58.0)
