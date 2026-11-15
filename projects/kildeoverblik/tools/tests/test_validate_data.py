"""Reglerne for testdata: det, en maskine kan holde øje med, før en model ser noget."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import validate_data as v  # noqa: E402

WORLD = {"window": {"from": "06.00", "to": "09.00"}, "date": "2026-11-11",
         "desks": [{"id": "F"}, {"id": "M"}, {"id": "E"}],
         "source_types": ["Telegram", "Pressemeddelelse", "Offentligt dokument"]}


def find(**kw):
    base = {"id": "D-001", "time": "06.05", "source_type": "Telegram", "sender": "Nyhedsbureauet",
            "title": "Varsel", "text": "Varslet om stormflod er hævet til højeste niveau for natten til torsdag."}
    base.update(kw)
    return base


def data(finds=None, archive=None, key=None):
    finds = finds if finds is not None else [find()]
    key = key if key is not None else {
        "events": [{"id": "E01", "title": "Storm", "story_for": {"F": True, "M": True, "E": False}}],
        "finds": {"D-001": {"event": "E01"}}, "links": []}
    return {"world": WORLD, "finds": finds, "archive": archive or [], "key": key}


class Excerpt(unittest.TestCase):
    def test_short_text_is_its_own_excerpt(self):
        self.assertEqual(v.excerpt({"title": "T", "text": "Kort tekst."}), "Kort tekst.")

    def test_long_text_is_cut_at_a_word_and_never_longer_than_the_limit(self):
        text = "ord " * 200
        cut = v.excerpt({"title": "T", "text": text}, limit=50)
        self.assertLessEqual(len(cut), 50)
        self.assertTrue(text.startswith(cut))
        self.assertFalse(cut.endswith(" "))


class Finds(unittest.TestCase):
    def test_a_clean_set_has_no_problems(self):
        self.assertEqual(v.problems(data()), [])

    def test_two_finds_with_the_same_id(self):
        d = data(finds=[find(), find()])
        self.assertTrue(any("D-001" in p and "to gange" in p for p in v.problems(d)))

    def test_a_time_outside_the_morning(self):
        self.assertTrue(any("09.15" in p for p in v.problems(data(finds=[find(time="09.15")]))))

    def test_a_time_written_with_a_colon(self):
        self.assertTrue(any("06:05" in p for p in v.problems(data(finds=[find(time="06:05")]))))

    def test_an_unknown_source_type(self):
        self.assertTrue(any("Rygte" in p for p in v.problems(data(finds=[find(source_type="Rygte")]))))

    def test_an_empty_text(self):
        self.assertTrue(any("tekst" in p for p in v.problems(data(finds=[find(text=" ")]))))

    def test_an_archive_document_must_be_older_than_the_morning(self):
        arch = [{"id": "A-001", "date": "2026-11-11", "source_type": "Offentligt dokument",
                 "sender": "Kommunen", "title": "Dagsorden", "text": "Punkt 1."}]
        self.assertTrue(any("A-001" in p and "dato" in p for p in v.problems(data(archive=arch))))


class Key(unittest.TestCase):
    def test_every_find_of_the_morning_is_in_the_key(self):
        d = data(finds=[find(), find(id="D-002")])
        self.assertTrue(any("D-002" in p and "facit" in p for p in v.problems(d)))

    def test_the_key_points_at_an_event_that_exists(self):
        key = {"events": [], "finds": {"D-001": {"event": "E99"}}, "links": []}
        self.assertTrue(any("E99" in p for p in v.problems(data(key=key))))

    def test_noise_has_no_event(self):
        key = {"events": [], "finds": {"D-001": {"event": None}}, "links": []}
        self.assertEqual(v.problems(data(key=key)), [])

    def test_an_event_says_yes_or_no_for_every_desk(self):
        key = {"events": [{"id": "E01", "title": "Storm", "story_for": {"F": True}}],
               "finds": {"D-001": {"event": "E01"}}, "links": []}
        self.assertTrue(any("E01" in p and "M" in p for p in v.problems(data(key=key))))

    def test_an_event_without_finds(self):
        key = {"events": [{"id": "E01", "title": "Storm", "story_for": {"F": True, "M": True, "E": False}},
                          {"id": "E02", "title": "Tom", "story_for": {"F": False, "M": False, "E": False}}],
               "finds": {"D-001": {"event": "E01"}}, "links": []}
        self.assertTrue(any("E02" in p and "ingen fund" in p for p in v.problems(data(key=key))))

    def test_an_event_can_rest_on_a_link_instead_of_a_find(self):
        key = {"events": [{"id": "E01", "title": "Storm", "story_for": {"F": True, "M": True, "E": False}},
                          {"id": "E02", "title": "Kommunen udskød", "story_for": {"F": True, "M": True, "E": False},
                           "via_links": ["L1"]}],
               "finds": {"D-001": {"event": "E01"}},
               "links": [{"id": "L1", "from": "D-001", "to": "A-001", "event": "E01", "why": "samme dige"}]}
        arch = [{"id": "A-001", "date": "2026-11-06", "source_type": "Offentligt dokument",
                 "sender": "Kommunen", "title": "Dagsorden", "text": "Punkt 14."}]
        self.assertEqual(v.problems(data(archive=arch, key=key)), [])

    def test_an_event_resting_on_a_link_that_does_not_exist(self):
        key = {"events": [{"id": "E01", "title": "Storm", "story_for": {"F": True, "M": True, "E": False}},
                          {"id": "E02", "title": "Kommunen udskød", "story_for": {"F": True, "M": True, "E": False},
                           "via_links": ["L9"]}],
               "finds": {"D-001": {"event": "E01"}}, "links": []}
        self.assertTrue(any("E02" in p and "L9" in p for p in v.problems(data(key=key))))

    def test_a_link_joins_two_documents_that_exist(self):
        key = data()["key"]
        key["links"] = [{"id": "L1", "from": "D-001", "to": "A-404", "why": "samme dige"}]
        self.assertTrue(any("A-404" in p for p in v.problems(data(key=key))))


class Traps(unittest.TestCase):
    """En fælde er kun en fælde, hvis historien står i teksten og ikke i uddraget."""

    def test_a_buried_phrase_must_stand_in_the_text(self):
        key = data()["key"]
        key["finds"]["D-001"]["buried"] = "tre påbud"
        self.assertTrue(any("tre påbud" in p and "står ikke" in p for p in v.problems(data(key=key))))

    def test_a_buried_phrase_must_not_stand_in_the_excerpt(self):
        key = data()["key"]
        key["finds"]["D-001"]["buried"] = "højeste niveau"
        self.assertTrue(any("højeste niveau" in p and "uddraget" in p for p in v.problems(data(key=key))))

    def test_a_properly_buried_phrase_passes(self):
        long = "Punkt 12. Godkendelse af referat. " * 12 + "Kommunen har meddelt tre påbud."
        key = data()["key"]
        key["finds"]["D-001"]["buried"] = "tre påbud"
        self.assertEqual(v.problems(data(finds=[find(text=long)], key=key)), [])


class Facts(unittest.TestCase):
    """Facits fakta står ordret i deres kilde."""

    def test_a_quote_that_is_not_in_the_source(self):
        key = data()["key"]
        key["events"][0]["facts"] = [{"no": 1, "text": "Varslet er hævet", "find": "D-001",
                                      "quote": "hævet til næsthøjeste niveau"}]
        self.assertTrue(any("næsthøjeste" in p for p in v.problems(data(key=key))))

    def test_a_quote_that_is_in_the_source_passes(self):
        key = data()["key"]
        key["events"][0]["facts"] = [{"no": 1, "text": "Varslet er hævet", "find": "D-001",
                                      "quote": "hævet til højeste niveau"}]
        self.assertEqual(v.problems(data(key=key)), [])


if __name__ == "__main__":
    unittest.main()
