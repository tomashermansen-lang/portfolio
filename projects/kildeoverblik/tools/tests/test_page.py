"""Siden omkring appen: kort, uden detaljeside, og uden tal skrevet i hånden."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HTML = (ROOT / "index.html").read_text(encoding="utf-8")


def prose(block_id: str) -> str:
    block = re.search(rf'<div class="doc" id="{block_id}">(.*?)\n      </div>', HTML, re.S).group(1)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", block)).strip()


class Page(unittest.TestCase):
    def test_the_text_outside_the_app_is_at_most_680_words(self):
        # 400 ord plus use casen, en fjerde knap og princippet om, at en ændring prøves og godkendes, som Tomas bad om 2026-11-11/12. Det, siden ikke kan vise, står i ansøgningen.
        words = len((prose("before") + " " + prose("after")).split())
        self.assertLessEqual(words, 680, f"{words} ord uden for appen")

    def test_the_use_case_is_described_before_the_prototype(self):
        self.assertLess(HTML.index('<section id="usecase">'), HTML.index('<section id="lead">'))
        self.assertLess(HTML.index('<section id="lead">'), HTML.index('<div class="stage" id="stage">'))

    def test_the_prototype_comes_first_with_a_short_lead_and_three_things_to_try(self):
        # 230 ord plus linjen om målene, flyttet op fra sit eget afsnit 2026-11-13; teksten uden for appen blev kortere af flytningen.
        self.assertLessEqual(len(prose("before").split()), 245)
        self.assertIn("tre kolonner", prose("before"), "læseren får at vide, hvad skærmen viser, før knapperne")
        lead = re.search(r'<div class="doc" id="before">(.*?)\n      </div>', HTML, re.S).group(1)
        self.assertEqual(lead.count("<li>"), 5)

    def test_what_the_run_showed_comes_before_how_it_is_built(self):
        order = re.findall(r'<section id="([a-z]+)"', HTML)
        self.assertLess(order.index("measure"), order.index("how"))

    def test_each_thing_to_try_is_a_button_that_takes_the_reader_there(self):
        import json
        data = json.loads((ROOT / "extractions" / "app-data.json").read_text(encoding="utf-8"))
        docs, groups = data["docs"], [g["gid"] for g in data["groups"]]
        lead = re.search(r'<div class="doc" id="before">(.*?)\n      </div>', HTML, re.S).group(1)
        self.assertEqual(len(re.findall(r'<li><button class="go" data-go="([^"]+)"', lead)), 5)
        self.assertIn("play=1", lead, "den første knap afspiller morgenen")
        self.assertRegex(prose("before"), r"[Kk]lik på en knap")
        self.assertNotIn("doc=", lead, "demoen begynder med det, der virker; den oversete kilde står ved testens resultat")
        gos = re.findall(r'<button class="go[^"]*" data-go="([^"]+)"', HTML)
        for go in gos:
            want = dict(part.split("=") for part in go.replace("&amp;", "&").split("&"))
            self.assertTrue(set(want) <= {"desk", "doc", "view", "sel", "play", "mark", "cycle", "tour", "cue"}, go)
            self.assertTrue("sel" not in want or want["sel"] in groups, go)
            self.assertTrue("doc" not in want or want["doc"] in docs, go)

    def test_several_desks_and_the_three_versions_are_shown_by_the_buttons_not_told_in_a_section(self):
        self.assertNotIn('<section id="desks">', HTML)
        lead = prose("before")
        self.assertIn("Forskellige redaktioner", lead)
        self.assertIn('data-go="desk=F&amp;cycle=1"', HTML, "knappen skifter selv mellem redaktionerne")
        self.assertIn('data-go="desk=F&amp;tour=udkast"', HTML, "knappen viser vejen fra forslaget til udkastet")
        self.assertIn("tre udgaver", lead)

    def test_method_and_goals_that_the_page_cannot_show_are_left_to_the_application(self):
        ids = re.findall(r'<section id="([a-z]+)"', HTML)
        self.assertEqual([i for i in ids if i in ("where", "value")], [])

    def test_the_two_examples_open_the_feedback_screen_and_say_what_each_leads_to(self):
        section = re.search(r'<section id="measure">(.*?)</section>', HTML, re.S).group(1)
        import json
        data = json.loads((ROOT / "extractions" / "app-data.json").read_text(encoding="utf-8"))
        reported = {a["find"] for a in data["actions"] if a["desk"] == "F" and a["action"] in ("missing", "dismiss")}
        marks = re.findall(r'data-go="desk=F&amp;view=feedback&amp;mark=([^"]+)"', section)
        self.assertEqual(len(marks), 2)
        for mark in marks:
            self.assertTrue(set(mark.split(",")) <= reported, mark)
        self.assertEqual(len(marks[1].split(",")), 2, "teksten siger to fravalg, så to bliver farvet")
        self.assertIn("udvikling", section)
        self.assertIn("konfigurering", section)
        self.assertNotIn("Løsning:", section)

    def test_the_feedback_section_states_as_a_principle_that_a_change_is_tested_and_approved_first(self):
        section = re.search(r'<section id="measure">(.*?)</section>', HTML, re.S).group(1)
        after_examples = section.split("</ul>")[-1]
        self.assertIn("gælder ikke med det samme", after_examples)
        self.assertIn("af redaktionen og platformejeren", after_examples)

    def test_how_it_works_says_who_does_what(self):
        section = re.search(r'<section id="how">(.*?)</section>', HTML, re.S).group(1)
        for who in ("by code", "by model", "by human"):
            self.assertIn(who, section)

    def test_the_reservation_stands_under_the_title_and_the_assumptions_section_is_gone(self):
        self.assertNotIn('<section id="scope">', HTML)
        meta = re.search(r'<p class="meta">(.*?)</p>', HTML, re.S).group(1)
        self.assertIn("eksempel på prototype med syntetiske data", meta)
        self.assertIn("Jeg har ikke arbejdet på en nyhedsredaktion, så ord, roller og arbejdsgang er antagelser.", meta)

    def test_the_goals_screen_is_the_fifth_place_to_start_and_has_no_section_of_its_own(self):
        # Tomas 2026-11-13: målene flyttes op til knapperne, så en læser med fem minutter ser dem.
        order = re.findall(r'<section id="([a-z]+)"', HTML)
        self.assertNotIn("goals", order)
        self.assertEqual(order[-1], "how")
        lead = re.search(r'<div class="doc" id="before">(.*?)\n      </div>', HTML, re.S).group(1)
        last = re.findall(r"<li>(.*?)</li>", lead, re.S)[-1]
        self.assertIn('data-go="desk=F&amp;view=maal&amp;tour=maal"', last, "knappen ruller selv skærmen igennem")
        self.assertIn("skitse", last, "skærmen er en mock-up, og det står ved knappen")
        self.assertEqual(HTML.count("view=maal"), 1)
        self.assertIn("Fem steder", prose("before"))

    def test_a_reader_moved_to_the_app_by_a_button_gets_a_way_back_to_the_text(self):
        self.assertRegex(HTML, r'<button class="back" id="back" hidden>[^<]*Tilbage til teksten</button>')

    def test_the_page_says_that_facts_are_extracted_once_and_reused(self):
        section = re.search(r'<section id="how">(.*?)</section>', HTML, re.S).group(1)
        self.assertIn("Fakta trækkes ud én gang og bruges i alle udgaver og hos alle redaktioner.", section)

    def test_the_step_about_the_code_check_has_a_button_to_where_it_can_be_tried(self):
        section = re.search(r'<section id="how">(.*?)</section>', HTML, re.S).group(1)
        self.assertIn('data-go="desk=F&amp;view=udkast&amp;cue=check"', section)

    def test_visits_and_button_clicks_are_counted_like_on_the_other_pages(self):
        self.assertIn('data-goatcounter="https://tomashermansen.goatcounter.com/count"', HTML)
        buttons = re.findall(r'<button class="go[^"]*"([^>]*)>', HTML)
        self.assertTrue(buttons)
        names = [re.search(r'data-goatcounter-click="(kildeoverblik-[a-z-]+)"', b) for b in buttons]
        self.assertTrue(all(names), "hver knap har et navn at tælle på")
        self.assertEqual(len({n.group(1) for n in names}), len(buttons), "navnene er forskellige")

    def test_the_page_credits_claude_code(self):
        self.assertIn("Claude Code", re.search(r'<p class="meta">(.*?)</p>', HTML, re.S).group(1))

    def test_a_narrow_screen_gets_the_app_scaled_down_with_a_note_and_a_hint_to_turn_the_phone(self):
        self.assertNotIn("narrow-img", HTML)
        self.assertNotRegex(HTML, r"@media[^{]*\{\s*\.stage\s*\{\s*display:\s*none", "appen skjules ikke på smalle skærme")
        self.assertIn('<div class="appfit" id="appfit">', HTML)
        self.assertRegex(HTML, r'<p class="hint" id="smallnote" hidden>[^<]*større skærm')
        self.assertRegex(HTML, r"@media[^{]*orientation: portrait[^{]*\{\s*\.turn\s*\{\s*display: block")

    def test_no_count_from_the_run_is_typed_into_the_text(self):
        text = prose("before") + " " + prose("after")
        self.assertIsNone(re.search(r"\b\d+ (af|forslag|fund|historier|sammenhænge)\b", text), "tal fra kørslen står i teksten")

    def test_the_page_uses_the_shared_stylesheet_and_navigation(self):
        self.assertIn('href="../../style.css', HTML)
        self.assertIn('class="nav__name"', HTML)
        self.assertIn('class="footer__inner"', HTML)


if __name__ == "__main__":
    unittest.main()
