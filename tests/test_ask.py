"""Ask finds the right records and shows only answers it can check. No model and no network are used here.

    python -m unittest discover -s tests
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "toolkit" / "lifekeeper"))
sys.path.insert(0, str(ROOT / "toolkit" / "lifekeeper"))
import ask  # noqa: E402
import lifekeeper  # noqa: E402


def meta(text):
    return text.encode("utf-8").decode("latin-1")


class Ask(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.folder = tempfile.TemporaryDirectory()
        root = Path(cls.folder.name)
        (root / "my_events.csv").write_text(
            "date,title,note\n"
            "2019-09-02,Started an evening design course,Twice a week after work.\n"
            "2021-03-14,Met Leo,At Anna's birthday party.\n"
            "2022-04,Moved to Lisbon,\n"
            "2023-06-18,Дедушке исполнилось 90,Собралась вся семья.\n", encoding="utf-8")
        posts = root / "facebook" / "your_activity_across_facebook" / "posts"
        posts.mkdir(parents=True)
        (posts / "your_posts__check_ins__photos_and_videos_1.json").write_text(json.dumps([
            {"timestamp": 1629115200, "data": [{"post": meta("Lisbon, you have my heart.")}]},
            {"timestamp": 1567425600, "data": [{"post": meta("First day of the course. Nervous.")}]}]), encoding="utf-8")
        (root / "goodreads_library_export.csv").write_text(
            "Title,Author,Date Read\nKlara and the Sun,Kazuo Ishiguro,2021/04/11\n", encoding="utf-8")
        (root / "result.json").write_text(json.dumps({
            "personal_information": {"user_id": 1, "first_name": "Mira", "last_name": "Novak"},
            "chats": {"list": [{"name": "Leo Hart", "type": "personal_chat", "messages": [
                {"id": 1, "type": "message", "date": "2021-03-15T10:00:00", "from": "Leo Hart", "from_id": "user2", "text": "hi"},
                {"id": 2, "type": "message", "date": "2021-03-15T10:01:00", "from": "Mira Novak", "from_id": "user1", "text": "hi"}]}]}}),
            encoding="utf-8")
        cls.found = ask.records(lifekeeper.build(str(root), []))

    @classmethod
    def tearDownClass(cls):
        cls.folder.cleanup()

    def test_records_cover_what_lite_reads(self):
        kinds = {record["kind"] for record in self.found}
        self.assertLessEqual({"my note", "Facebook post", "book read", "person", "messages"}, kinds)
        self.assertIn("Mar 14, 2021 · my note · Met Leo: At Anna's birthday party.", [ask.line(record) for record in self.found])

    def test_search_finds_by_words(self):
        first = ask.search(self.found, "When did I meet Leo?", limit=1)[0]
        self.assertEqual((first["kind"], first["day"]), ("my note", "2021-03-14"))  # "meet" finds "Met"
        moved = ask.search(self.found, "When did I move?", limit=1)[0]
        self.assertIn("Moved to Lisbon", moved["text"])  # "move" finds "Moved"

    def test_search_finds_by_year_and_month(self):
        in_2021 = ask.search(self.found, "What happened in 2021?")
        self.assertTrue(in_2021)
        self.assertEqual({record["day"][:4] for record in in_2021}, {"2021"})
        in_march = ask.search(self.found, "What did I do in March 2021?", limit=3)
        self.assertEqual({record["day"][:7] for record in in_march}, {"2021-03"})

    def test_search_in_russian(self):
        first = ask.search(self.found, "Когда дедушке исполнилось 90?", limit=1)[0]
        self.assertEqual(first["day"], "2023-06-18")

    def test_newer_sources_become_records(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "conversations.json").write_text(json.dumps([{"title": "Packing list for Lisbon", "create_time": 1628500000, "mapping": {}}]), encoding="utf-8")
            (root / "MyActivity.json").write_text(json.dumps([{"header": "Search", "title": "Searched for flights to lisbon", "time": "2021-08-01T10:00:00.000Z"}]), encoding="utf-8")
            (root / "timelogger.csv").write_text("Activity type,Duration,From,To,Comment,Tags\nWork,08:30,2021-08-03 09:00,2021-08-03 17:30,,\n", encoding="utf-8")
            (root / "daylio_export.csv").write_text("full_date,date,weekday,time,mood,activities,note_title,note\n2021-08-14,14 August,Saturday,21:00,rad,travel,,First evening in Lisbon.\n", encoding="utf-8")
            lines = [ask.line(record) for record in ask.records(lifekeeper.build(str(root), []))]
        self.assertIn("Aug 9, 2021 · AI chat · Packing list for Lisbon", lines)
        self.assertIn("Aug 2021 · searches · Searched for flights to lisbon", lines)
        self.assertIn("Aug 2021 · time · Time spent: Work (8 h)", lines)
        self.assertIn("Aug 14, 2021 · diary · First evening in Lisbon.", lines)
        self.assertIn("Aug 2021 · mood · Mood mostly rad (1 day)", lines)

    def test_feelings_find_moods_and_diaries(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "daylio_export.csv").write_text("full_date,date,weekday,time,mood,activities,note_title,note\n"
                                                    "2024-06-03,3 June,Monday,21:00,rad,work,,First day at Lumen. Everyone was kind.\n",
                                                    encoding="utf-8")
            found = ask.records(lifekeeper.build(str(root), []))
        kinds = {record["kind"] for record in ask.search(found, "How did I feel when I started at Lumen?")}
        self.assertEqual(kinds, {"diary", "mood"})

    def test_gemini_retries_when_busy(self):
        import io
        import urllib.error
        calls = []

        def busy_then_fine(request, timeout):
            calls.append(1)
            if len(calls) < 3:
                raise urllib.error.HTTPError(request.full_url, 503, "busy", {}, io.BytesIO(b'{"error": {"status": "UNAVAILABLE"}}'))
            return io.BytesIO(json.dumps({"candidates": [{"content": {"parts": [{"text": "ok"}]}}]}).encode())

        real = ask.urllib.request.urlopen
        ask.urllib.request.urlopen = busy_then_fine
        try:
            self.assertEqual(ask.gemini("s", "p", "key", waits=(0, 0)), "ok")
            calls.clear()
            ask.urllib.request.urlopen = lambda request, timeout: (_ for _ in ()).throw(
                urllib.error.HTTPError(request.full_url, 503, "busy", {}, io.BytesIO(b"{}")))
            with self.assertRaisesRegex(RuntimeError, "busy right now"):
                ask.gemini("s", "p", "key", waits=(0, 0))
        finally:
            ask.urllib.request.urlopen = real

    def test_nothing_matches(self):
        self.assertEqual(ask.search(self.found, "Did I ever go to Mars?"), [])
        self.assertEqual(ask.answer(self.found, "Did I ever go to Mars?"), "Nothing in your records matches that question.")

    def test_without_a_model_the_records_are_shown(self):
        shown = ask.answer(self.found, "When did I meet Leo?")
        self.assertTrue(shown.startswith("Records that match (no AI was used):"))
        self.assertIn("Met Leo: At Anna's birthday party.", shown)

    def chosen(self):
        return ask.search(self.found, "When did I meet Leo?")

    def number_of(self, text):
        return next(number for number, record in enumerate(self.chosen(), 1) if text in record["text"])

    def test_a_cited_sentence_is_kept_and_renumbered(self):
        note = self.number_of("Met Leo")
        text, sources = ask.checked(f"You met Leo on Mar 14, 2021, at Anna's birthday party [{note}].", self.chosen())
        self.assertEqual(text, "You met Leo on Mar 14, 2021, at Anna's birthday party [1].")
        self.assertEqual([record["text"] for record in sources], ["Met Leo: At Anna's birthday party."])

    def test_a_sentence_without_a_record_is_left_out(self):
        note = self.number_of("Met Leo")
        text, sources = ask.checked(f"You met Leo on Mar 14, 2021 [{note}]. It was love at first sight.", self.chosen())
        self.assertEqual(text, "You met Leo on Mar 14, 2021 [1].")
        self.assertEqual(len(sources), 1)

    def test_a_date_the_records_do_not_have_is_left_out(self):
        note = self.number_of("Met Leo")
        text, sources = ask.checked(f"You met Leo in 2019 [{note}].", self.chosen())
        self.assertEqual((text, sources), ("", []))

    def test_a_record_number_that_does_not_exist_is_left_out(self):
        text, _ = ask.checked("You met Leo at a party [99].", self.chosen())
        self.assertEqual(text, "")

    def test_citation_after_the_period_and_short_words(self):
        note = self.number_of("Met Leo")
        text, _ = ask.checked(f"You met Leo on Mar. 14, 2021. [{note}]", self.chosen())
        self.assertEqual(text, "You met Leo on Mar. 14, 2021 [1].")

    def test_answer_with_a_model(self):
        note = self.number_of("Met Leo")
        seen = {}

        def model(system, prompt):
            seen["system"], seen["prompt"] = system, prompt
            return f"You met Leo on Mar 14, 2021 [{note}]. You have been inseparable ever since."

        told = []
        shown = ask.answer(self.found, "When did I meet Leo?", model, note=told.append)
        self.assertEqual(shown, "You met Leo on Mar 14, 2021 [1].\n\nFrom your records:\n"
                                "[1] Mar 14, 2021 · my note · Met Leo: At Anna's birthday party.")
        self.assertIn("Question: When did I meet Leo?", seen["prompt"])
        self.assertIn(f"[{note}] Mar 14, 2021 · my note · Met Leo", seen["prompt"])
        self.assertEqual(told, [len(self.chosen())])  # the person is told how many records are sent

    def test_an_answer_that_cannot_be_checked_is_not_shown(self):
        shown = ask.answer(self.found, "When did I meet Leo?", lambda system, prompt: "You met Leo in Paris in 2015.")
        self.assertTrue(shown.startswith("The model's answer couldn't be checked against your records, so it isn't shown."))
        self.assertNotIn("Paris", shown)

    def test_the_model_says_the_records_do_not_say(self):
        shown = ask.answer(self.found, "When did I meet Leo?", lambda system, prompt: "The records don't say.")
        self.assertTrue(shown.startswith("Your records don't say. The closest ones:"))

    def test_gemini_request_keeps_the_key_out_of_the_text(self):
        request = ask.gemini_request("system text", "prompt text", "SECRET-KEY", "some-model")
        self.assertIn("/models/some-model:generateContent", request.full_url)
        self.assertNotIn("SECRET-KEY", request.full_url)
        self.assertNotIn(b"SECRET-KEY", request.data)
        self.assertEqual(request.get_header("X-goog-api-key"), "SECRET-KEY")
        body = json.loads(request.data)
        self.assertEqual(body["contents"][0]["parts"][0]["text"], "prompt text")
        self.assertEqual(body["generationConfig"]["temperature"], 0)


if __name__ == "__main__":
    unittest.main()
