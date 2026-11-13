"""Tællingen mod facit: fundne og oversete historier, støj og sammenhænge, pr. redaktion."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import evaluate as e  # noqa: E402

DESKS = ["F", "M"]
KEY = {
    "events": [
        {"id": "E1", "title": "Storm", "story_for": {"F": True, "M": True}},
        {"id": "E2", "title": "Skole", "story_for": {"F": True, "M": False}},
        {"id": "E3", "title": "Elpris", "story_for": {"F": False, "M": False}},
        {"id": "E4", "title": "Udbud", "story_for": {"F": False, "M": True}},
    ],
    "finds": {"D1": {"event": "E1"}, "D2": {"event": "E1"}, "D3": {"event": "E2"}, "D4": {"event": "E3"},
              "D5": {"event": "E4"}, "N1": {"event": None}},
    "links": [{"id": "L1", "from": "D2", "to": "A1", "event": "E1"}, {"id": "L2", "from": "D5", "to": "A2", "event": "E4"}],
}
RUN = {
    "threshold": 5,
    "coarse": {"D1": {"scores": {"F": 9, "M": 8}}, "D2": {"scores": {"F": 8, "M": 8}}, "D3": {"scores": {"F": 3, "M": 2}},
               "D4": {"scores": {"F": 6, "M": 3}}, "D5": {"scores": {"F": 1, "M": 4}}, "N1": {"scores": {"F": 5, "M": 1}}},
    "reads": {"D1": {"values": {"F": {"value": 9}, "M": {"value": 9}}}, "D2": {"values": {"F": {"value": 8}, "M": {"value": 7}}},
              "D4": {"values": {"F": {"value": 5}, "M": {"value": 2}}}, "N1": {"values": {"F": {"value": 6}, "M": {"value": 1}}}},
    "groups": [{"finds": ["D1", "D2"], "label": "Storm"}, {"finds": ["D4"], "label": "Elpris"}, {"finds": ["N1"], "label": "Cykelsti"}],
    "links": {"D2__A1": {"related": True}, "N1__A1": {"related": True}, "D1__A3": {"related": False}},
}


class PerDesk(unittest.TestCase):
    def setUp(self):
        self.r = e.evaluate(KEY, RUN, DESKS)

    def test_a_story_is_found_when_one_of_its_finds_is_in_a_proposal(self):
        self.assertEqual(self.r["desks"]["F"]["found"], ["E1"])
        self.assertEqual(self.r["desks"]["M"]["found"], ["E1"])

    def test_a_story_whose_finds_were_never_read_is_missed_and_says_so(self):
        self.assertEqual(self.r["desks"]["F"]["missed"], [{"event": "E2", "why": "aldrig læst i fuld tekst"}])
        self.assertEqual(self.r["desks"]["M"]["missed"], [{"event": "E4", "why": "aldrig læst i fuld tekst"}])

    def test_a_proposal_that_is_no_story_for_the_desk_is_noise(self):
        self.assertEqual([n["finds"] for n in self.r["desks"]["F"]["noise"]], [["D4"], ["N1"]])
        self.assertEqual(self.r["desks"]["M"]["noise"], [])

    def test_counts_add_up_to_the_key(self):
        c = self.r["desks"]["F"]["counts"]
        self.assertEqual(c, {"stories": 2, "proposed": 3, "found": 1, "missed": 1, "noise": 2})
        self.assertEqual(c["found"] + c["missed"], c["stories"])
        self.assertEqual(c["found"] + c["noise"], c["proposed"])


class Links(unittest.TestCase):
    def setUp(self):
        self.l = e.evaluate(KEY, RUN, DESKS)["links"]

    def test_a_planted_link_judged_related_is_found(self):
        self.assertEqual(self.l["found"], ["L1"])

    def test_a_planted_link_is_missed_with_its_reason_and_counted_once(self):
        self.assertEqual(self.l["missed"], [{"link": "L2", "why": "dagens fund blev aldrig læst i fuld tekst"}])

    def test_a_related_verdict_outside_the_key_is_a_wrong_proposal(self):
        self.assertEqual(self.l["wrong"], [{"from": "N1", "to": "A1"}])

    def test_counts(self):
        self.assertEqual(self.l["counts"], {"planted": 2, "found": 1, "missed": 1, "wrong": 1, "judged": 3})


class StoriesThatRestOnALink(unittest.TestCase):
    """En historie, der kun findes, når dagens fund ses sammen med et arkivdokument."""
    KEY2 = {"events": KEY["events"] + [{"id": "E5", "title": "Kommunen udskød", "story_for": {"F": True, "M": True},
                                        "via_links": ["L1"]},
                                       {"id": "E6", "title": "Samme entreprenør", "story_for": {"F": False, "M": True},
                                        "via_links": ["L2"]}],
            "finds": KEY["finds"], "links": KEY["links"]}

    def test_it_is_found_when_the_link_is_found_and_the_find_is_proposed(self):
        r = e.evaluate(self.KEY2, RUN, DESKS)
        self.assertIn("E5", r["desks"]["F"]["found"])
        self.assertIn("E5", r["desks"]["M"]["found"])

    def test_it_is_missed_when_the_link_is_missed(self):
        r = e.evaluate(self.KEY2, RUN, DESKS)
        self.assertIn({"event": "E6", "why": "sammenhængen blev ikke fundet"}, r["desks"]["M"]["missed"])


class Unverified(unittest.TestCase):
    def test_unverified_material_goes_to_verification_and_is_not_counted_as_a_proposal(self):
        run = {**RUN, "coarse": {**RUN["coarse"], "N1": {"scores": {"F": 5, "M": 1}, "unverified": True}}}
        r = e.evaluate(KEY, run, DESKS)
        self.assertEqual([n["finds"] for n in r["desks"]["F"]["noise"]], [["D4"]])
        self.assertEqual(r["desks"]["F"]["counts"]["proposed"], 2)


class UnverifiedStory(unittest.TestCase):
    def test_a_story_whose_only_source_is_unverified_says_it_waits_for_verification(self):
        run = {**RUN, "coarse": {**RUN["coarse"], "D4": {"scores": {"F": 6, "M": 3}, "unverified": True}}}
        key = {**KEY, "events": [ev if ev["id"] != "E3" else {**ev, "story_for": {"F": True, "M": False}} for ev in KEY["events"]]}
        r = e.evaluate(key, run, DESKS)
        self.assertIn({"event": "E3", "why": "ubekræftet kilde; ligger til verifikation"}, r["desks"]["F"]["missed"])


class Reading(unittest.TestCase):
    def test_how_many_were_read_and_how_often_the_two_numbers_differ(self):
        r = e.evaluate(KEY, RUN, DESKS)["reading"]
        self.assertEqual(r["documents"], 6)
        self.assertEqual(r["read"], 4)
        self.assertEqual(r["value_differs_from_coarse"], {"F": 2, "M": 3})


if __name__ == "__main__":
    unittest.main()
