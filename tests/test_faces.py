"""The faces add-on groups and names faces right. The faces here are made-up vectors, so no photos and no models are needed.

    python -m unittest discover -s tests
"""
import sys
import tempfile
from contextlib import closing
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "toolkit" / "lifekeeper"))
import faces  # noqa: E402

try:
    import numpy
except ImportError:  # the faces add-on isn't installed: these tests wait for it
    numpy = None


@unittest.skipIf(numpy is None, "the faces add-on (NumPy) isn't installed")
class Faces(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.root = Path(self.folder.name) / "exports"
        self.root.mkdir()

    def tearDown(self):
        self.folder.cleanup()

    def add(self, connection, photo, vector, score=0.9):
        vector = numpy.asarray(vector, dtype="float32")
        vector /= numpy.linalg.norm(vector)
        connection.execute("INSERT INTO faces(photo,x,y,w,h,score,embedding,crop) VALUES (?,0,0,100,100,?,?,?)",
                           (photo, score, vector.tobytes(), b"jpeg"))

    def test_group_name_hide(self):
        rng = numpy.random.default_rng(1)
        anna, leo, stranger = (rng.normal(size=128) for _ in range(3))
        with closing(faces.connect(self.root)) as connection:
            for n in range(4):
                self.add(connection, f"a{n}.jpg", anna + rng.normal(scale=0.15, size=128))
            for n in range(3):
                self.add(connection, f"l{n}.jpg", leo + rng.normal(scale=0.15, size=128))
            self.add(connection, "s.jpg", stranger)  # seen once: too few to show
            connection.commit()
        self.assertEqual(faces.group(self.root), 3)
        groups = faces.people(self.root)
        self.assertEqual([group["photos"] for group in groups], [4, 3])
        anna_group, leo_group = groups[0]["person"], groups[1]["person"]
        self.assertEqual(faces.name(self.root, anna_group, "Anna"), 4)
        faces.group(self.root)  # regrouping keeps the name: names belong to faces
        self.assertEqual([(group["name"], group["photos"]) for group in faces.people(self.root)][0], ("Anna", 4))
        self.assertEqual(faces.hide(self.root, leo_group), 3)
        self.assertEqual([group["name"] for group in faces.people(self.root)], ["Anna"])
        self.assertIn("Anna", faces.people_page(self.root))

    def test_one_person_in_two_groups_shows_once(self):
        rng = numpy.random.default_rng(2)
        young, older = rng.normal(size=128), rng.normal(size=128)  # far apart: two groups
        with closing(faces.connect(self.root)) as connection:
            for n in range(3):
                self.add(connection, f"y{n}.jpg", young + rng.normal(scale=0.1, size=128))
                self.add(connection, f"o{n}.jpg", older + rng.normal(scale=0.1, size=128))
            connection.commit()
        faces.group(self.root)
        first, second = faces.people(self.root)
        faces.name(self.root, first["person"], "Mom")
        faces.name(self.root, second["person"], "mom")
        merged = faces.people(self.root)
        self.assertEqual(len(merged), 1)
        self.assertEqual((merged[0]["photos"], len(merged[0]["persons"])), (6, 2))


if __name__ == "__main__":
    unittest.main()
