#!/usr/bin/env python3
"""Faces in your photos: find them, group the same person across photos, and name each group once.

    lifekeeper-faces scan   EXPORTS          # find faces in every photo (zips included); can be stopped and resumed
    lifekeeper-faces people EXPORTS          # write a page with each group's faces and its number
    lifekeeper-faces name   EXPORTS 3 Anna   # name group 3; the next page you make shows Anna in your photos
    lifekeeper-faces hide   EXPORTS 7        # leave out a group (strangers in the background)

Everything runs on this computer with OpenCV's YuNet (finding faces) and SFace (recognizing them). No photo leaves it.
The two models (about 37 MB) are downloaded once from OpenCV's own repository and checked against known fingerprints.
What it finds and the names you give are kept in lifekeeper-faces.sqlite3, next to your exports folder (never inside it).
Needs OpenCV, NumPy and Pillow, which come with pipx install lifekeeper (from a copy of the repo: pip install opencv-python-headless numpy pillow).
"""
import argparse
import hashlib
import html
import io
import os
import sqlite3
import sys
import time
import urllib.request
from contextlib import closing
from pathlib import Path

try:  # installed with pip: part of the lifekeeper package
    from . import lifekeeper
except ImportError:  # run as a script from this folder
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import lifekeeper  # noqa: E402

MODELS = {
    "face_detection_yunet_2023mar.onnx": (
        "https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx",
        "8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4"),
    "face_recognition_sface_2021dec.onnx": (
        "https://github.com/opencv/opencv_zoo/raw/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx",
        "0ba9fbfa01b5270c96627c4ef784da859931e02f04419c829e83484087c34e79"),
}
DETECT_SIZE = 1280   # photos are shrunk to this before looking for faces
MIN_FACE = 40        # pixels at that size; smaller faces are too blurry to recognize
SAME_PERSON = 0.45   # how alike two faces must be to count as one person (SFace's own threshold, 0.363, merges people)
MIN_GROUP = 3        # a group needs this many faces to be shown, unless you've named it


def model_folder():
    base = os.environ.get("LOCALAPPDATA") or os.environ.get("XDG_CACHE_HOME") or str(Path.home() / ".cache")
    return Path(base) / "lifekeeper" / "models"


def models():
    """The two model files, downloaded once and checked."""
    folder = model_folder()
    folder.mkdir(parents=True, exist_ok=True)
    paths = []
    for name, (url, fingerprint) in MODELS.items():
        path = folder / name
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != fingerprint:
            print(f"Downloading {name} from OpenCV's repository…", flush=True)
            with urllib.request.urlopen(url, timeout=300) as response:
                data = response.read()
            if hashlib.sha256(data).hexdigest() != fingerprint:
                raise RuntimeError(f"{name} didn't match its known fingerprint, so it wasn't used.")
            path.write_bytes(data)
        paths.append(path)
    return paths


def connect(root):
    connection = sqlite3.connect(lifekeeper.faces_file(root), timeout=60)
    connection.executescript("""
        CREATE TABLE IF NOT EXISTS faces(id INTEGER PRIMARY KEY, photo TEXT NOT NULL, x INTEGER, y INTEGER, w INTEGER, h INTEGER,
                                         score REAL, embedding BLOB NOT NULL, crop BLOB NOT NULL, person INTEGER);
        CREATE INDEX IF NOT EXISTS faces_photo ON faces(photo);
        CREATE INDEX IF NOT EXISTS faces_person ON faces(person);
        CREATE TABLE IF NOT EXISTS scanned(photo TEXT PRIMARY KEY, faces INTEGER NOT NULL, at TEXT);
        CREATE TABLE IF NOT EXISTS names(face_id INTEGER PRIMARY KEY, name TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS hidden(face_id INTEGER PRIMARY KEY);
    """)
    return connection


def scan(root, me=(), progress=print, limit=None):
    """Find and describe the faces in every photo not scanned yet, then regroup. Returns (photos scanned, faces found)."""
    try:
        import cv2
        import numpy
        from PIL import Image, ImageOps
    except ImportError:
        raise RuntimeError("Finding faces needs OpenCV and NumPy: pip install opencv-python-headless numpy pillow") from None
    try:
        import pillow_heif  # iPhone photos (.heic), if the reader for them is installed
        pillow_heif.register_heif_opener()
    except ImportError:
        pass
    detector_file, recognizer_file = models()
    detector = cv2.FaceDetectorYN.create(str(detector_file), "", (320, 320), 0.8, 0.3, 5000)
    recognizer = cv2.FaceRecognizerSF.create(str(recognizer_file), "")
    opened = []
    try:
        life = lifekeeper.read_all(root, list(me), opened)
        with closing(connect(root)) as connection:
            done = {row[0] for row in connection.execute("SELECT photo FROM scanned")}
            todo = sorted(photo for photo in life.photo_files if photo not in done)[:limit]
            progress(f"{len(todo):,} photos to look at ({len(done):,} done before)")
            started, found = time.time(), 0
            for number, photo in enumerate(todo, 1):
                faces = 0
                try:
                    picture = ImageOps.exif_transpose(Image.open(io.BytesIO(life.readers[photo]()))).convert("RGB")
                    picture.thumbnail((DETECT_SIZE, DETECT_SIZE))
                    image = cv2.cvtColor(numpy.asarray(picture), cv2.COLOR_RGB2BGR)
                    detector.setInputSize((image.shape[1], image.shape[0]))
                    _, detections = detector.detect(image)
                    for detection in detections if detections is not None else []:
                        x, y, w, h = (int(value) for value in detection[:4])
                        if min(w, h) < MIN_FACE:
                            continue
                        embedding = recognizer.feature(recognizer.alignCrop(image, detection)).flatten().astype("float32")
                        embedding /= numpy.linalg.norm(embedding) or 1
                        pad = int(0.25 * max(w, h))
                        crop = picture.crop((max(0, x - pad), max(0, y - pad), min(picture.width, x + w + pad), min(picture.height, y + h + pad)))
                        crop.thumbnail((128, 128))
                        buffer = io.BytesIO()
                        crop.save(buffer, "JPEG", quality=82)
                        connection.execute("INSERT INTO faces(photo,x,y,w,h,score,embedding,crop) VALUES (?,?,?,?,?,?,?,?)",
                                           (photo, x, y, w, h, float(detection[-1]), embedding.tobytes(), buffer.getvalue()))
                        faces += 1
                except Exception:  # a broken or unusual picture: counted as scanned with no faces, the rest go on
                    pass
                connection.execute("INSERT OR REPLACE INTO scanned VALUES (?,?,datetime('now'))", (photo, faces))
                found += faces
                if number % 100 == 0:
                    connection.commit()
                    progress(f"{number:,} of {len(todo):,} photos · {found:,} faces · {number / (time.time() - started):.1f} photos a second")
            connection.commit()
    finally:
        for archive in opened:
            archive.close()
    group(root)
    return len(todo), found


def group(root):
    """Each face joins the most alike group if it's close enough, or starts a new one. Clearer faces go first, so they
    shape the groups. Names stay with faces, so they carry over to the new groups."""
    import numpy
    with closing(connect(root)) as connection:
        rows = connection.execute("SELECT id, embedding FROM faces ORDER BY score * w DESC").fetchall()
        if not rows:
            return 0
        centers, sizes, assignment = [], [], {}
        for face, blob in rows:
            vector = numpy.frombuffer(blob, dtype="float32")
            if centers:
                similarity = numpy.stack(centers) @ vector
                best = int(similarity.argmax())
                if similarity[best] >= SAME_PERSON:
                    sizes[best] += 1
                    center = centers[best] * (sizes[best] - 1) + vector
                    centers[best] = center / numpy.linalg.norm(center)
                    assignment[face] = best
                    continue
            centers.append(vector.copy())
            sizes.append(1)
            assignment[face] = len(centers) - 1
        connection.executemany("UPDATE faces SET person=? WHERE id=?", [(person, face) for face, person in assignment.items()])
        connection.commit()
        return len(centers)


def people(root):
    """Groups worth showing, named ones first, then the biggest: [{person, persons, name, photos, faces}]."""
    with closing(connect(root)) as connection:
        names = dict(connection.execute("SELECT face_id, name FROM names"))
        hidden = {row[0] for row in connection.execute("SELECT face_id FROM hidden")}
        groups = {}
        for face, person, photo in connection.execute("SELECT id, person, photo FROM faces WHERE person IS NOT NULL ORDER BY score * w DESC"):
            entry = groups.setdefault(person, {"person": person, "faces": [], "photos": set(), "votes": {}, "hidden": False})
            entry["faces"].append(face)
            entry["photos"].add(photo)
            if face in names:
                entry["votes"][names[face]] = entry["votes"].get(names[face], 0) + 1
            entry["hidden"] |= face in hidden
    result, by_name = [], {}
    for entry in sorted(groups.values(), key=lambda entry: -len(entry["photos"])):
        name = max(entry["votes"], key=entry["votes"].get) if entry["votes"] else ""
        if entry["hidden"] or (len(entry["faces"]) < MIN_GROUP and not name):
            continue
        same = by_name.get(name.casefold()) if name else None
        if same:  # one person whose face was split into several groups: one entry
            same["persons"].append(entry["person"])
            same["photo_set"] |= entry["photos"]
            continue
        item = {"person": entry["person"], "persons": [entry["person"]], "name": name, "photo_set": set(entry["photos"]),
                "faces": entry["faces"][:8]}
        result.append(item)
        if name:
            by_name[name.casefold()] = item
    for item in result:
        item["photos"] = len(item.pop("photo_set"))
    result.sort(key=lambda item: (not item["name"], -item["photos"]))
    return result


def name(root, person, new_name):
    """Name every face in a group. An empty name clears it."""
    with closing(connect(root)) as connection:
        faces = [row[0] for row in connection.execute("SELECT id FROM faces WHERE person=?", (int(person),))]
        if new_name.strip():
            connection.executemany("INSERT OR REPLACE INTO names VALUES (?,?)", [(face, new_name.strip()) for face in faces])
        else:
            connection.executemany("DELETE FROM names WHERE face_id=?", [(face,) for face in faces])
        connection.commit()
    return len(faces)


def hide(root, person):
    with closing(connect(root)) as connection:
        faces = [row[0] for row in connection.execute("SELECT id FROM faces WHERE person=?", (int(person),))]
        connection.executemany("INSERT OR IGNORE INTO hidden VALUES (?)", [(face,) for face in faces])
        connection.commit()
    return len(faces)


def crops(root, faces):
    """face id → JPEG bytes of the face."""
    if not faces:
        return {}
    with closing(connect(root)) as connection:
        marks = ",".join("?" * len(faces))
        return dict(connection.execute(f"SELECT id, crop FROM faces WHERE id IN ({marks})", list(faces)))


def people_page(root):
    """One page with every group: its number, its name if it has one, and its clearest faces."""
    import base64
    groups = people(root)
    pictures = crops(root, [face for item in groups for face in item["faces"]])
    rows = []
    for item in groups:
        faces = "".join(f'<img src="data:image/jpeg;base64,{base64.b64encode(pictures[face]).decode()}" alt="">'
                        for face in item["faces"] if face in pictures)
        title = html.escape(item["name"]) if item["name"] else f"Group {item['person']}"
        rows.append(f"<section><h2>{title} <span>{item['photos']:,} photo{'' if item['photos'] == 1 else 's'} · group {item['person']}</span></h2>"
                    f"<div>{faces}</div></section>")
    return ("<!doctype html><meta charset=utf-8><title>People in your photos</title><style>"
            "body{font:15px/1.5 system-ui,sans-serif;max-width:900px;margin:40px auto;padding:0 20px;color:#1d1d1f;background:#f6f5f2}"
            "h1{font-size:26px}h2{font-size:17px;margin:24px 0 8px}h2 span{color:#6e6e73;font-weight:400;font-size:14px}"
            "img{width:84px;height:84px;object-fit:cover;border-radius:10px;margin:0 6px 6px 0}p{color:#6e6e73}"
            "@media(prefers-color-scheme:dark){body{background:#141416;color:#f2f2ef}}</style>"
            "<h1>People in your photos</h1><p>Name a group with <b>lifekeeper-faces name EXPORTS NUMBER NAME</b>, or in the app. "
            "Groups of strangers can be left out with <b>lifekeeper-faces hide EXPORTS NUMBER</b>.</p>" + "".join(rows))


def main():
    parser = argparse.ArgumentParser(description="Find, group and name the faces in your photos. Nothing leaves this computer.")
    parser.add_argument("command", choices=["scan", "people", "name", "hide"])
    parser.add_argument("exports", help="the folder with your exports")
    parser.add_argument("group", nargs="?", type=int, help="the group's number (for name and hide)")
    parser.add_argument("new_name", nargs="?", default="", help="the name (for name); leave it out to clear a name")
    parser.add_argument("--out", default=None, help="where to write the people page (default: next to the exports folder)")
    args = parser.parse_args()
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    if not Path(args.exports).is_dir():
        sys.exit(f"Not a folder: {args.exports}")
    try:
        if args.command == "scan":
            photos, found = scan(args.exports)
            print(f"Looked at {photos:,} photos and found {found:,} faces. Next: lifekeeper-faces people {args.exports}")
        elif args.command == "people":
            out = Path(args.out) if args.out else Path(args.exports).resolve().parent / "people-in-photos.html"
            out.write_text(people_page(args.exports), encoding="utf-8")
            print(f"Wrote {out}")
        elif args.command in ("name", "hide"):
            if args.group is None:
                sys.exit("Which group? Its number is on the people page.")
            count = name(args.exports, args.group, args.new_name) if args.command == "name" else hide(args.exports, args.group)
            print(f"{'Named' if args.command == 'name' else 'Left out'} {count:,} faces.")
    except RuntimeError as error:
        sys.exit(str(error))


if __name__ == "__main__":
    main()
