"""Most people have little data. Four made-up people with the little most people have, and what their pages must show.

    python -m unittest discover -s tests
"""
import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "toolkit" / "lifekeeper"))
import lifekeeper  # noqa: E402

PICTURE = b"\xff\xd8\xff\xe0 not a real picture"


class LittleData(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.root = Path(self.folder.name) / "photos-2026-10"  # named the way docs/collecting.md suggests: the date isn't a photo date

    def tearDown(self):
        self.folder.cleanup()

    def write(self, name, data):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(data, bytes):
            path.write_bytes(data)
        else:
            path.write_text(data, encoding="utf-8", newline="")

    def page(self):
        life = lifekeeper.build(self.root, [])
        return life, lifekeeper.render(life, "My life at a glance")

    def test_phone_photos_only(self):
        start = datetime(2023, 1, 1)
        for day in range(0, 400, 9):
            when = start + timedelta(days=day)
            self.write(f"DCIM/Camera/PXL_{when:%Y%m%d}_120000.jpg", PICTURE)
        life, page = self.page()
        self.assertEqual(life.read["photos"], 45)
        self.assertIn("<h2>2023</h2>", page)
        self.assertNotIn("href='#people'", page)  # no chats: no link to an empty people section
        self.assertIn("What to add next", page)
        self.assertIn("Your own notes", page)  # the first suggestion: only you can add these
        self.assertIn("Your chats", page)

    def test_scanned_album_and_notes_by_year(self):
        for index in range(5):
            self.write(f"scans/Scan_{index:04d}.jpg", PICTURE)  # no date anywhere
        self.write("scans/1977 wedding.jpg", PICTURE)
        self.write("scans/1985/beach.jpg", PICTURE)
        self.write("scans/1980s/old.jpg", PICTURE)  # a decade isn't a year
        self.write("scans/IMG_2019.jpg", PICTURE)  # a camera number isn't a year
        self.write("my_events.csv", "date,title,note\n1955,I was born,\n1977,We got married,\n")
        life, page = self.page()
        self.assertEqual(dict(life.photos_year), {"1977": 1, "1985": 1})
        self.assertEqual(life.skipped["photos without a date"], 7)
        self.assertIn("Photos without a date", page)
        self.assertNotIn("2026", page.split("<footer>")[0])  # the folder's export date never becomes a photo date
        section = page.split("<section id='y1977'>")[1].split("</section>")[0]
        self.assertIn("We got married", section)
        self.assertNotIn("January", section)  # a year-only note isn't a January note

    def test_one_family_group_chat_in_spanish(self):
        start = datetime(2024, 1, 1, 9)
        lines = [f"{start + timedelta(hours=7 * n):%d/%m/%y, %H:%M} - {['Mamá', 'Papá', 'Ana', 'Tío Luis'][n % 4]}: hola" for n in range(300)]
        self.write("Chat de WhatsApp con Familia.txt", "\n".join(lines))
        life, page = self.page()
        self.assertIn("Familia (group)", life.people)
        self.assertIn("in 1 group chat", page)
        self.assertNotIn("1 people", page)

    def test_the_app_saves_next_to_the_exports_not_inside(self):
        import app
        self.write("my_events.csv", "date,title,note\n2020-05,Moved to Berlin,\n")
        out, life = app.make_page(self.root, "")
        self.assertEqual(out.parent, self.root.parent)  # the originals' folder stays untouched
        self.assertIn("Moved to Berlin", out.read_text(encoding="utf-8"))

    def test_posts_only(self):
        posts = [{"timestamp": int(datetime(2018 + n % 6, 1 + n % 12, 5, tzinfo=timezone.utc).timestamp()),
                  "data": [{"post": f"post number {n}"}]} for n in range(20)]
        self.write("facebook/your_posts_1.json", json.dumps(posts))
        life, page = self.page()
        self.assertEqual(life.read["Facebook posts"], 20)
        self.assertIn("· post number", page)  # a glimpse of the post without opening it
        self.assertNotIn("Nothing from", page)  # sparse years don't list empty months


if __name__ == "__main__":
    unittest.main()
