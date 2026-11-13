"""Samlingen af data og kørsel til den ene fil, appen læser. Ingen tal i appen er skrevet i hånden."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import assemble as a  # noqa: E402

WORLD = {"threshold": 5, "desks": [{"id": "F", "name": "Formiddagsblad", "rules": []}, {"id": "M", "name": "Morgenavis", "rules": []}]}
DOCS = {
    "D1": {"id": "D1", "time": "06.05", "title": "Varsel", "text": "Varslet er hævet til højeste niveau for natten."},
    "D2": {"id": "D2", "time": "06.45", "title": "Beredskab", "text": "Beredskabet frygter digebrud ved Nørrevang Strand. 300 boliger."},
    "D3": {"id": "D3", "time": "07.10", "title": "Lotto", "text": "En gevinst på 42 mio. kr. er ikke hentet."},
    "A1": {"id": "A1", "date": "2026-11-06", "title": "Dagsorden", "text": "Kommunen har meddelt tre påbud om diget ved Nørrevang Strand."},
}
RUN = {
    "threshold": 5,
    "coarse": {"D1": {"scores": {"F": 8, "M": 8}}, "D2": {"scores": {"F": 7, "M": 7}}, "D3": {"scores": {"F": 6, "M": 2}}},
    "reads": {
        "D1": {"facts": [{"text": "Varslet er hævet.", "quote": "hævet til højeste niveau"}], "values": {"F": {"value": 9}, "M": {"value": 9}}},
        "D2": {"facts": [{"text": "Beredskabet frygter digebrud.", "quote": "frygter digebrud ved Nørrevang Strand", "statement": True},
                         {"text": "Opdigtet.", "quote": "står ikke i kilden"}], "values": {"F": {"value": 8}, "M": {"value": 7}}},
        "D3": {"facts": [{"text": "42 mio. er ikke hentet.", "quote": "42 mio. kr. er ikke hentet"}], "values": {"F": {"value": 7}, "M": {"value": 2}}},
    },
    "groups": [{"finds": ["D1", "D2"], "label": "Stormflod"}, {"finds": ["D3"], "label": "Lotto"}],
    "links": {"D2__A1": {"related": True, "why": "Samme dige.", "facts": [{"text": "Tre påbud.", "quote": "tre påbud om diget"}]}},
    "candidates": [{"from": "D2", "to": "A1", "shared": "Nørrevang Strand"}],
    "drafts": {"F_G01": {"angle": "Stormflod i nat", "web": [{"s": "Varslet er hævet.", "facts": [1]}, {"s": "Vandet når 4 meter.", "facts": [1]},
                                                             {"s": "Uden fakta.", "facts": []}],
                         "notification": {"s": "Varslet er hævet.", "facts": [1]}, "audio": [{"s": "Varslet er hævet.", "facts": [1]}]}},
}


class Groups(unittest.TestCase):
    def setUp(self):
        self.g = a.build_groups(RUN, DOCS, WORLD)

    def test_groups_get_stable_ids_in_the_order_of_the_run(self):
        self.assertEqual([g["gid"] for g in self.g], ["G01", "G02"])

    def test_a_group_appears_when_its_first_find_arrives(self):
        self.assertEqual(self.g[0]["first_time"], "06.05")

    def test_the_value_for_a_desk_is_the_highest_among_its_finds(self):
        self.assertEqual(self.g[0]["values"], {"F": 9, "M": 9})
        self.assertEqual(self.g[1]["values"], {"F": 7, "M": 2})

    def test_facts_are_numbered_across_the_group_with_their_source(self):
        self.assertEqual([(f["no"], f["find"]) for f in self.g[0]["facts"]], [(1, "D1"), (2, "D2"), (3, "D2"), (4, "A1")])

    def test_a_quote_that_is_not_in_its_source_is_marked(self):
        self.assertEqual([f["quote_ok"] for f in self.g[0]["facts"]], [True, True, False, True])

    def test_a_fact_from_the_archive_carries_its_link(self):
        fact = self.g[0]["facts"][3]
        self.assertEqual((fact["via_link"], fact["available_from"]), ("D2__A1", "06.46"))

    def test_links_are_listed_on_the_group_with_who_shared_what(self):
        self.assertEqual(self.g[0]["links"], [{"from": "D2", "to": "A1", "shared": "Nørrevang Strand", "related": True,
                                               "why": "Samme dige.", "time": "06.46"}])


class SameArchiveDocumentFromTwoFinds(unittest.TestCase):
    """Modellen læser arkivdokumentet én gang pr. fund, der peger på det. Samme citat er samme faktum."""

    def setUp(self):
        import copy
        run = copy.deepcopy(RUN)
        run["links"]["D1__A1"] = {"related": True, "why": "Tidlig.", "facts": [{"text": "Tre påbud.", "quote": "tre påbud om diget"}]}
        run["links"]["D2__A1"]["facts"] = [{"text": "Tre påbud.", "quote": "meddelt tre påbud om diget"},
                                           {"text": "Kommunen har meddelt.", "quote": "Kommunen har meddelt"}]
        run["candidates"].append({"from": "D1", "to": "A1", "shared": "Nørrevang Strand"})
        run["drafts"]["F_G01"]["web"] = [{"s": "Tre påbud.", "facts": [5]}, {"s": "Meddelt.", "facts": [5, 6]}]
        self.groups = a.build_groups(run, DOCS, WORLD)
        self.drafts = a.build_drafts(run, self.groups)

    def test_the_same_quote_from_the_same_archive_document_is_one_fact(self):
        self.assertEqual([(f["no"], f["find"], f.get("via_link")) for f in self.groups[0]["facts"]],
                         [(1, "D1", None), (2, "D2", None), (3, "D2", None), (4, "A1", "D1__A1"), (5, "A1", "D2__A1")])

    def test_a_quote_inside_another_is_the_same_passage_and_the_longer_quote_is_kept(self):
        self.assertEqual(self.groups[0]["facts"][3]["quote"], "meddelt tre påbud om diget")

    def test_sentences_in_the_drafts_follow_the_fact_to_its_new_number(self):
        self.assertEqual([s["facts"] for s in self.drafts["F_G01"]["web"]], [[4], [4, 5]])


class QuoteFromTheHeadline(unittest.TestCase):
    def test_a_quote_that_stands_in_the_title_of_the_source_is_in_the_source(self):
        import copy
        run = copy.deepcopy(RUN)
        run["reads"]["D3"]["facts"] = [{"text": "Lotto.", "quote": "Lotto"}]
        self.assertTrue(a.build_groups(run, DOCS, WORLD)[1]["facts"][0]["quote_ok"])

class Drafts(unittest.TestCase):
    def test_each_sentence_carries_the_problems_code_can_find(self):
        groups = a.build_groups(RUN, DOCS, WORLD)
        d = a.build_drafts(RUN, groups)["F_G01"]
        self.assertEqual(d["web"][0]["problems"], [])
        self.assertTrue(any("4" in p for p in d["web"][1]["problems"]))
        self.assertTrue(d["web"][2]["problems"])
        self.assertEqual(d["notification"]["length"], len("Varslet er hævet."))


class Timeline(unittest.TestCase):
    def test_one_minute_later(self):
        self.assertEqual(a.plus_minutes("06.59", 1), "07.00")


if __name__ == "__main__":
    unittest.main()
