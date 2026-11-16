#!/usr/bin/env python3
"""Makes demo/exports: the exports of Mira Novak, a person who doesn't exist (Berlin, 2019–2025).

    python demo/make_demo.py

Everything is invented and the same on every run. The exports copy the real formats closely: a Telegram Desktop export,
a WhatsApp chat, a Google Takeout zip (photos with their .json files, Semantic Location History), the newer phone
Timeline export, Facebook posts with Meta's broken text encoding, Instagram posts, and a my_events.csv of her own notes.
"""
import base64
import json
import random
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

OUT = Path(__file__).resolve().parent / "exports"
RNG = random.Random(42)
ME, ME_ID = "Mira Novak", "user1000001"
TINY_JPEG = base64.b64decode(  # a 1×1 picture: every demo photo is this one, so the demo is the same on every computer
    "/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAP//////////////////////////////////////////////////////////////////////////////////////"
    "wgALCAABAAEBAREA/8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAQABPxA=")
PLACES = {"Berlin": (52.52, 13.40), "Lisbon": (38.72, -9.14), "Istanbul": (41.01, 28.98), "Tokyo": (35.68, 139.69), "Krakow": (50.06, 19.94)}
TRIPS = [("2019-10-11", 4, "Krakow", 10), ("2021-08-13", 9, "Lisbon", 22), ("2022-07-02", 6, "Lisbon", 12),
         ("2023-05-19", 5, "Istanbul", 18), ("2025-04-05", 14, "Tokyo", 26)]
LINES_ME = ["See you at 7?", "Running late, sorry!", "How did it go?", "That's wonderful news", "I miss you", "Call me tonight?",
            "Just got home", "Look at this view", "Thank you, really", "Let's do Sunday", "I'm so tired today", "Haha, exactly"]
LINES_THEM = ["Sure!", "On my way", "It went well, I think", "Can't wait", "Miss you too", "Yes, after 8", "Sleep well",
              "So beautiful!", "Any time", "Sunday works", "Rest a bit", "Right?"]


def months(first, last):
    year, month = map(int, first.split("-"))
    while f"{year}-{month:02d}" <= last:
        yield year, month
        month += 1
        if month == 13:
            year, month = year + 1, 1


def moment(year, month):
    return datetime(year, month, RNG.randint(1, 28), RNG.randint(8, 23), RNG.randint(0, 59), RNG.randint(0, 59))


def telegram():
    people = [  # name, id, first month, last month, messages a month (low, high)
        ("Anna Berg", "user2000002", "2019-01", "2025-08", (8, 24)),
        ("Mom", "user2000003", "2019-01", "2025-08", (5, 14)),
        ("Leo Hart", "user2000004", "2021-03", "2025-08", (10, 18)),
        ("Daniel Ross", "user2000005", "2020-12", "2024-06", (2, 7)),
    ]
    chats, number = [], 1
    for name, user_id, first, last, (low, high) in people:
        messages = []
        for year, month in months(first, last):
            count = RNG.randint(low, high) * (3 if name == "Leo Hart" and f"{year}-{month:02d}" < "2022-04" else 1)  # new love talks more
            for _ in range(count):
                mine = RNG.random() < 0.5
                when = moment(year, month)
                if name == "Leo Hart" and (year, month) == (2021, 3):
                    when = when.replace(day=RNG.randint(14, 28))  # they met on March 14
                messages.append({"id": number, "type": "message", "date": when.isoformat(), "date_unixtime": str(int(when.replace(tzinfo=timezone.utc).timestamp())),
                                 "from": ME if mine else name, "from_id": ME_ID if mine else user_id,
                                 "text": RNG.choice(LINES_ME if mine else LINES_THEM)})
                number += 1
        chats.append({"name": name, "type": "personal_chat", "id": int(user_id[4:]), "messages": sorted(messages, key=lambda m: m["date"])})
    group = []
    for year, month in months("2019-06", "2023-12"):
        for _ in range(RNG.randint(3, 8)):
            who = RNG.choice([(ME, ME_ID), ("Anna Berg", "user2000002"), ("Kai", "user2000006"), ("Rosa", "user2000007")])
            when = moment(year, month)
            group.append({"id": number, "type": "message", "date": when.isoformat(), "date_unixtime": str(int(when.replace(tzinfo=timezone.utc).timestamp())),
                          "from": who[0], "from_id": who[1], "text": RNG.choice(["Chapter 5 tonight?", "Loved the ending", "Next book?"])})
            number += 1
    chats.append({"name": "Book club", "type": "private_group", "id": 3000001, "messages": sorted(group, key=lambda m: m["date"])})
    data = {"about": "Here is the data you requested.", "personal_information": {"user_id": 1000001, "first_name": "Mira", "last_name": "Novak"},
            "chats": {"about": "This page lists all chats from this export.", "list": chats}}
    path = OUT / "telegram" / "DataExport_2025-09-01" / "result.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8", newline="\n")


def whatsapp():
    lines = []
    for year, month in months("2020-03", "2025-08"):
        stamps = sorted(moment(year, month) for _ in range(RNG.randint(6, 18)))
        for when in stamps:
            mine = RNG.random() < 0.55
            text = RNG.choice(["Hi Grandpa! How are you feeling?", "Sending you a photo of the garden", "Love you"] if mine else
                              ["All good, the knee is better", "Lovely!", "Come visit soon", "Love you too, sweetheart"])
            lines.append(f"{when:%d.%m.%Y, %H:%M} - {ME if mine else 'Grandpa'}: {text}")
    path = OUT / "whatsapp" / "WhatsApp Chat with Grandpa.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def put(archive, name, data):
    """A zip member with a fixed date, so the demo zip is the same on every run."""
    info = zipfile.ZipInfo(name, date_time=(2025, 9, 1, 0, 0, 0))
    info.create_system = 3  # the same on Windows, Mac and Linux
    info.external_attr = 0o644 << 16
    info.compress_type = zipfile.ZIP_STORED  # stored, not compressed: compression differs between computers
    archive.writestr(info, data)


def picture():
    for _ in range(3):  # three draws per photo, kept so the rest of the made-up data stays as it was
        RNG.randint(60, 220)
    return TINY_JPEG


def takeout():
    shots = []
    for year, month in months("2019-01", "2025-08"):
        for _ in range(RNG.randint(1, 3)):
            shots.append((moment(year, month), "Berlin"))
    for start, days, city, count in TRIPS:
        first = datetime.fromisoformat(start)
        shots += [(first + timedelta(days=RNG.randint(0, days - 1), hours=RNG.randint(9, 20), minutes=RNG.randint(0, 59)), city)
                  for _ in range(count)]
    path = OUT / "takeout-20250901T000000Z-001.zip"
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        for when, city in sorted(shots):
            name = f"Takeout/Google Photos/Photos from {when.year}/IMG_{when:%Y%m%d_%H%M%S}.jpg"
            lat, lon = PLACES[city]
            put(archive, name, picture())
            put(archive, name + ".json", json.dumps({
                "title": name.rsplit("/", 1)[1], "photoTakenTime": {"timestamp": str(int(when.replace(tzinfo=timezone.utc).timestamp()))},
                "geoData": {"latitude": round(lat + RNG.uniform(-0.04, 0.04), 5), "longitude": round(lon + RNG.uniform(-0.04, 0.04), 5),
                            "altitude": 0.0}}, indent=1))
        visits = {"2021/2021_AUGUST.json": [("2021-08-14T10:12:00Z", "Belém Tower", 38.6916, -9.2160), ("2021-08-15T19:40:00Z", "LX Factory", 38.7036, -9.1784),
                                             ("2021-08-17T11:05:00Z", "Sintra", 38.7979, -9.3906)],
                  "2022/2022_JULY.json": [("2022-07-03T12:30:00Z", "Time Out Market", 38.7071, -9.1458), ("2022-07-05T09:15:00Z", "Cascais", 38.6979, -9.4215)],
                  "2023/2023_MAY.json": [("2023-05-20T10:00:00Z", "Galata Tower", 41.0256, 28.9742), ("2023-05-21T13:20:00Z", "Kadıköy Market", 40.9910, 29.0270),
                                          ("2023-05-22T16:45:00Z", "Princes' Islands", 40.8740, 29.0890)]}
        for name, items in visits.items():
            put(archive, f"Takeout/Location History (Timeline)/Semantic Location History/{name}", json.dumps({"timelineObjects": [
                {"placeVisit": {"location": {"latitudeE7": int(lat * 1e7), "longitudeE7": int(lon * 1e7), "name": place},
                                "duration": {"startTimestamp": start}}} for start, place, lat, lon in items]}, ensure_ascii=False, indent=1))
        keep = [("2021-08-10", "Lisbon list", "Belém, LX Factory, Sintra, pastéis de nata everywhere"),
                ("2022-03-20", "Moving checklist", "boxes, internet, change address, plants last"),
                ("2025-03-28", "Japan", "rail pass, Kyoto day trip, the teahouse Anna recommended")]
        for index, (day, title, text) in enumerate(keep):
            stamp = int(datetime.fromisoformat(day).replace(hour=19, tzinfo=timezone.utc).timestamp() * 1_000_000)
            put(archive, f"Takeout/Keep/note{index + 1}.json", json.dumps({"title": title, "textContent": text, "isTrashed": False,
                                                                                "createdTimestampUsec": stamp}, ensure_ascii=False))
    # the newer Timeline export comes from the phone itself, with coordinates and no place names
    segments = [{"startTime": f"2025-04-{day:02d}T10:00:00.000+09:00", "endTime": f"2025-04-{day:02d}T18:00:00.000+09:00",
                 "visit": {"topCandidate": {"placeLocation": {"latLng": f"{35.68 + RNG.uniform(-0.05, 0.05):.4f}°, {139.69 + RNG.uniform(-0.05, 0.05):.4f}°"}}}}
                for day in range(5, 18)]
    segments += [{"startTime": "2025-04-12T09:00:00.000+09:00", "visit": {"topCandidate": {"placeLocation": {"latLng": "34.9858°, 135.7588°"}}}}]  # a day in Kyoto
    (OUT / "Timeline.json").write_text(json.dumps({"semanticSegments": segments}, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")


def meta(text):
    """Meta's exports write UTF-8 as if it were Latin-1; the demo copies that, so the fix gets shown."""
    return text.encode("utf-8").decode("latin-1")


def social():
    posts = [("2019-03-02", "First day at the bookshop. Smells like paper and coffee."), ("2019-09-02", "Back to school: evening design course, twice a week."),
             ("2019-10-13", "Krakow in the fall is unreal."), ("2020-04-11", "Week four at home. Baking bread like everyone else."),
             ("2020-12-01", "I'm a designer now. Officially!"), ("2021-05-09", "С днём рождения, мама! Happy birthday, Mom."),
             ("2021-08-16", "Lisbon, you have my heart."), ("2022-04-02", "Boxes everywhere. New home, new chapter."),
             ("2023-06-18", "Grandpa turned 90 today. Four generations around one table."), ("2024-03-10", "Meet Pixel. She owns us now."),
             ("2025-04-15", "Two weeks in Japan, and I want to stay forever.")]
    facebook = [{"timestamp": int(datetime.fromisoformat(day).replace(hour=12, tzinfo=timezone.utc).timestamp()), "data": [{"post": meta(text)}],
                 "title": meta("Mira Novak updated her status.")} for day, text in posts]
    path = OUT / "facebook-mira" / "your_activity_across_facebook" / "posts" / "your_posts__check_ins__photos_and_videos_1.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(facebook, indent=1), encoding="utf-8", newline="\n")  # ASCII escapes, as Meta writes them
    captions = [("2021-08-14", "Pastéis de nata, day one of many"), ("2022-07-04", "Same city, one year later"), ("2023-05-21", "Ferry to Kadıköy"),
                ("2024-03-12", "Pixel's first sunbeam"), ("2025-04-08", "Cherry blossoms, finally"), ("2025-04-12", "Kyoto mornings")]
    instagram = [{"media": [{"uri": f"media/posts/{day[:7].replace('-', '')}/{index}.jpg",
                             "creation_timestamp": int(datetime.fromisoformat(day).replace(hour=15, tzinfo=timezone.utc).timestamp()),
                             "title": meta(text)}]} for index, (day, text) in enumerate(captions)]
    path = OUT / "instagram-mira" / "your_instagram_activity" / "content" / "posts_1.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(instagram, indent=1), encoding="utf-8", newline="\n")


def notes():
    (OUT / "my_events.csv").write_text("date,title,note\n"
                                       "2019-03-01,Started at the bookshop,The one on the corner of my street.\n"
                                       "2019-09-02,Started an evening design course,Twice a week after work.\n"
                                       "2020-12-01,First design job,Junior designer at a small studio.\n"
                                       "2021-03-14,Met Leo,At Anna's birthday party.\n"
                                       "2022-04-01,Moved in with Leo,The flat near the park.\n"
                                       "2023-06-18,Grandpa turned 90,The whole family came.\n"
                                       "2024-03-09,Adopted Pixel the cat,\n"
                                       "2025-04-05,Two weeks in Japan,Tokyo and a day in Kyoto.\n", encoding="utf-8", newline="\n")


def more():
    """Instagram messages, X, a calendar, Spotify, Netflix, Goodreads and LinkedIn."""
    messages = []
    for year, month in months("2023-02", "2025-08"):
        for _ in range(RNG.randint(2, 6)):
            when = moment(year, month)
            mine = RNG.random() < 0.5
            messages.append({"sender_name": meta(ME if mine else "Sofia Lind"), "timestamp_ms": int(when.replace(tzinfo=timezone.utc).timestamp() * 1000),
                             "content": meta(RNG.choice(["Coffee this week?", "Loved your story!", "Yes! Thursday?", "Pixel says hi"]))})
    thread = {"participants": [{"name": meta("Sofia Lind")}, {"name": meta(ME)}], "messages": sorted(messages, key=lambda m: -m["timestamp_ms"]),
              "title": meta("Sofia Lind"), "thread_path": "inbox/sofialind_1029384756"}
    path = OUT / "instagram-mira" / "your_instagram_activity" / "messages" / "inbox" / "sofialind_1029384756" / "message_1.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(thread, indent=1), encoding="utf-8", newline="\n")

    tweets = [("2019-05-04", "Shelving poetry today. Best part of the job."), ("2019-11-20", "RT @designweekly: 10 posters that changed design"),
              ("2020-03-28", "Day 14 of staying home. Learned to make sourdough. Learned to fail at sourdough."),
              ("2021-01-15", "First real client feedback: \"we love it, change everything\". Welcome to design."),
              ("2022-09-03", "RT @berlinevents: Museum night this Saturday"), ("2023-05-22", "Istanbul ferries are the best commute in the world."),
              ("2024-06-11", "Promotion! Still can't believe it.")]
    items = [{"tweet": {"created_at": datetime.fromisoformat(day).replace(hour=10, tzinfo=timezone.utc).strftime("%a %b %d %H:%M:%S +0000 %Y"),
                        "full_text": text, "id_str": str(1000 + index)}} for index, (day, text) in enumerate(tweets)]
    path = OUT / "twitter-mira" / "data" / "tweets.js"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("window.YTD.tweets.part0 = " + json.dumps(items, indent=1), encoding="utf-8", newline="\n")

    events = [("20190902", "Design course: first evening"), ("20200115", "Dentist"), ("20200313", "Anna's birthday"), ("20210313", "Anna's birthday party"),
              ("20210813", "Flight to Lisbon"), ("20220401", "Moving day"), ("20230519", "Flight to Istanbul"), ("20230618", "Grandpa's 90th"),
              ("20240309", "Pick up Pixel from the shelter"), ("20240611", "Review with the studio"), ("20250405", "Flight to Tokyo")]
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Demo//EN"]
    for index, (day, title) in enumerate(events):
        lines += ["BEGIN:VEVENT", f"UID:demo-{index}@example.com", f"DTSTART;VALUE=DATE:{day}", f"SUMMARY:{title.replace(',', chr(92) + ',')}", "END:VEVENT"]
    path = OUT / "calendar-mira" / "Mira Novak.ics"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\r\n".join(lines + ["END:VCALENDAR"]) + "\r\n", encoding="utf-8", newline="\n")

    eras = [("2019-01", "2020-12", ["Radiohead", "Björk", "Portishead"]), ("2021-01", "2022-12", ["Fleetwood Mac", "Tame Impala", "Radiohead"]),
            ("2023-01", "2025-03", ["Khruangbin", "Fleetwood Mac", "Nils Frahm"]), ("2025-04", "2025-08", ["Ryuichi Sakamoto", "Khruangbin", "Nils Frahm"])]
    plays = []
    for first, last, artists in eras:
        for year, month in months(first, last):
            for _ in range(4):
                artist = RNG.choices(artists, weights=[5, 3, 2])[0]
                plays.append({"ts": moment(year, month).strftime("%Y-%m-%dT%H:%M:%SZ"), "master_metadata_album_artist_name": artist,
                              "master_metadata_track_name": "a song", "ms_played": RNG.randint(90_000, 300_000)})
    path = OUT / "spotify-mira" / "Spotify Extended Streaming History" / "Streaming_History_Audio_2019-2025_0.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(plays, ensure_ascii=False), encoding="utf-8", newline="\n")

    path = OUT / "netflix-mira" / "CONTENT_INTERACTION" / "ViewingActivity.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    shows = [("2020-04-02", "Dark: Season 1: Secrets"), ("2020-04-03", "Dark: Season 1: Lies"), ("2020-04-09", "Dark: Season 2: Beginnings and Endings"),
             ("2021-06-12", "The Queen's Gambit: Limited Series: Openings"), ("2022-11-25", "Wednesday: Season 1: Wednesday's Child Is Full of Woe"),
             ("2024-01-20", "Shōgun: Season 1: Anjin"), ("2025-02-14", "Pachinko: Season 1: Chapter One")]
    path.write_text("Profile Name,Start Time,Duration,Title\n" + "".join(f"Mira,{day} 21:00:00,00:48:00,\"{title}\"\n" for day, title in shows), encoding="utf-8", newline="\n")

    (OUT / "goodreads_library_export.csv").write_text(
        "Book Id,Title,Author,Date Read,Exclusive Shelf\n"
        "1,The Design of Everyday Things,Don Norman,2019/10/02,read\n"
        "2,Station Eleven,Emily St. John Mandel,2020/05/17,read\n"
        "3,Klara and the Sun,Kazuo Ishiguro,2021/04/11,read\n"
        "4,Pachinko,Min Jin Lee,2023/02/26,read\n"
        "5,Tomorrow and Tomorrow and Tomorrow,Gabrielle Zevin,2024/08/03,read\n"
        "6,Kitchen,Banana Yoshimoto,2025/04/16,read\n"
        "7,Some book for later,Someone,,to-read\n", encoding="utf-8", newline="\n")

    path = OUT / "linkedin-mira" / "Positions.csv"  # her sales version: "Designer", where her own note says junior designer
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("Company Name,Title,Description,Location,Started On,Finished On\n"
                    "Lumen Studio,Senior Designer,,Berlin,Jun 2024,\n"
                    "Studio Kran,Designer,,Berlin,Dec 2020,May 2024\n"
                    "Corner Books,Bookseller,,Berlin,Mar 2019,Nov 2020\n", encoding="utf-8", newline="\n")


def newer():
    """Searches, AI chats, a time tracker and a mood diary. Their own dice, so the rest of the made-up data stays as it was."""
    dice = random.Random(7)
    searched = {"2021-03": ["birthday gift ideas for a friend", "how to stop overthinking a text"],
                "2021-08": ["flights berlin lisbon", "pastel de nata recipe", "lisbon tram 28 route", "flights berlin lisbon"],
                "2022-03": ["flats near the park berlin", "how to split rent fairly", "moving checklist"],
                "2024-03": ["kitten first week", "is my cat allowed cheese", "cat names"],
                "2024-06": ["senior designer salary berlin", "how to give notice politely"]}
    activity = [{"header": "Search", "title": f"Searched for {query}", "titleUrl": "https://www.google.com/search?q=" + query.replace(" ", "+"),
                 "time": f"{month}-{3 + 4 * number:02d}T19:{10 + number:02d}:00.000Z", "products": ["Search"], "activityControls": ["Web & App Activity"]}
                for month, queries in searched.items() for number, query in enumerate(queries)]
    path = OUT / "takeout-my-activity" / "Takeout" / "My Activity" / "Search" / "MyActivity.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(activity, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")

    chats = [("2023-02-11", "Explain color contrast rules simply"), ("2023-06-10", "Toast for a grandfather's 90th birthday"),
             ("2024-03-12", "What a new kitten needs"), ("2024-05-20", "Rewrite my portfolio intro"),
             ("2025-01-08", "Plan a week in Japan on a budget")]
    path = OUT / "chatgpt-mira" / "conversations.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps([{"title": title, "create_time": datetime.fromisoformat(day).replace(hour=18, tzinfo=timezone.utc).timestamp(),
                                 "mapping": {}} for day, title in chats], ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")

    rows = ["Activity type,Duration,From,To,Comment,Tags"]
    for year, month in months("2024-01", "2024-06"):
        for day in range(1, 29):
            for name, low, high in (("Work", 6, 9), ("Drawing", 0, 2), ("Reading", 0, 1)):
                hours = dice.randint(low, high) if (name != "Work" or day % 7 not in (6, 0)) else 0
                if hours:
                    rows.append(f"{name},{hours:02d}:{dice.choice((0, 15, 30, 45)):02d},{year}-{month:02d}-{day:02d} 09:00,{year}-{month:02d}-{day:02d} {9 + hours:02d}:00,,")
    (OUT / "timelogger-mira.csv").write_text("\n".join(rows) + "\n", encoding="utf-8", newline="\n")

    said = {"2024-03-09": "Brought Pixel home. She hid under the sofa for three hours.", "2024-04-03": "Long day. Drew for an hour and felt better.",
            "2024-05-27": "Last week at the studio. Cried a little, laughed more.", "2024-06-03": "First day at Lumen. Everyone was kind."}
    rows = ["full_date,date,weekday,time,mood,activities,note_title,note"]
    for year, month in months("2024-03", "2024-06"):
        for day in range(1, 29, 2):
            stamp = datetime(year, month, day)
            note = said.get(stamp.strftime("%Y-%m-%d"), "")
            mood = "rad" if note and "Cried" not in note else dice.choice(("good", "good", "good", "meh", "rad", "bad"))
            rows.append(f'{stamp:%Y-%m-%d},{stamp.day} {stamp:%B},{stamp:%A},21:30,{mood},,,"{note}"')
    (OUT / "daylio_export_mira.csv").write_text("\n".join(rows) + "\n", encoding="utf-8", newline="\n")


def marker():
    """A sign that this is made-up data: Lifekeeper leaves the folder out when someone opens a bigger folder around it
    (a whole downloaded copy of this project), so Mira's life never mixes into theirs. Opened on its own, it reads as usual."""
    (OUT / ".lifekeeper-sample").write_text("Made-up sample data (Mira Novak doesn't exist). Lifekeeper skips this folder unless "
                                         "you open it directly.\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    telegram()
    whatsapp()
    takeout()
    social()
    notes()
    more()
    newer()
    marker()
    print(f"Wrote the demo exports to {OUT}")
