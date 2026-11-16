#!/usr/bin/env python3
"""Lifekeeper: turn a few common exports into one readable page about your life.

    python lifekeeper.py EXPORTS_FOLDER [--out life.html] [--json life.json] [--me "Your Name" ...]

It looks everywhere inside EXPORTS_FOLDER, including inside .zip files, for:
  - chats: Telegram Desktop (result.json), WhatsApp (.txt), Messenger and Instagram (message_1.json),
    Android text messages ("SMS Backup & Restore" .xml), and mail I sent (Gmail .mbox from Takeout, unzipped)
  - photos (.jpg .jpeg .png .heic .webp): date and place from Google Takeout's .json files next to them, from the
    photo's own data when Pillow is installed (pip install pillow), or else the date in the file name
  - Google location history: Takeout's "Semantic Location History" and the newer phone Timeline export
  - Google searches (Takeout's My Activity), ChatGPT conversations (conversations.json), a time tracker's CSV
    (aTimeLogger), and a mood diary's CSV (Daylio, DailyBean)
  - Instagram stories, comments I wrote on Instagram and Facebook, and period start days from Flo's data download
  - posts: Facebook and Instagram (JSON), X/Twitter (tweets.js; retweets are other people's words and are left out)
  - calendars (.ics), Google Keep notes (Takeout JSON), LinkedIn jobs (Positions.csv)
  - what I listened to, watched and read: Spotify streaming history, YouTube watch history (Takeout),
    Netflix viewing history (.csv), Goodreads (goodreads_library_export.csv)
  - my_events.csv: your own notes (date,title,note). They come first in every month: your account wins.

Nothing is sent anywhere; no network is used. Files it can't read are counted at the end of the page, never skipped silently.
"""
import argparse
import csv
import html
import io
import json
import math
import re
import sys
import warnings
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

try:  # installed with pip: part of the lifekeeper package
    from . import places
except ImportError:  # run as a script from this folder
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import places  # noqa: E402

try:
    from PIL import Image
    Image.MAX_IMAGE_PIXELS = None  # only a photo's header is read, never its pixels: a huge scan is no danger
except ImportError:  # dates still come from Takeout's .json files and from file names
    Image = None

PHOTO_TYPES = {".jpg", ".jpeg", ".png", ".heic", ".webp"}
SAMPLE_MARKER = ".lifekeeper-sample"  # the made-up demo data has this file: left out unless you open that folder itself
SKIP_DIRS = {"node_modules", "__pycache__", "site-packages", "venv", "$recycle.bin", "system volume information", "thumbs",
             "thumbnails", "cache", "assets"}  # program files, caches and an archive viewer's own icons (X's "assets"), not your
                                               # life; folders starting with "." are left out too
MONTH_NAMES = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
SHORT = [name[:3] for name in MONTH_NAMES]
CITIES = [  # enough to name the places most photos are taken; anything farther than 150 km from all of them shows as coordinates
    ("London", 51.51, -0.13), ("Paris", 48.86, 2.35), ("Berlin", 52.52, 13.40), ("Madrid", 40.42, -3.70), ("Barcelona", 41.39, 2.17),
    ("Rome", 41.90, 12.50), ("Milan", 45.46, 9.19), ("Lisbon", 38.72, -9.14), ("Porto", 41.15, -8.61), ("Amsterdam", 52.37, 4.90),
    ("Brussels", 50.85, 4.35), ("Vienna", 48.21, 16.37), ("Prague", 50.08, 14.44), ("Warsaw", 52.23, 21.01), ("Krakow", 50.06, 19.94),
    ("Budapest", 47.50, 19.04), ("Bucharest", 44.43, 26.10), ("Sofia", 42.70, 23.32), ("Belgrade", 44.79, 20.45), ("Zagreb", 45.81, 15.98),
    ("Athens", 37.98, 23.73), ("Thessaloniki", 40.64, 22.94), ("Istanbul", 41.01, 28.98), ("Ankara", 39.93, 32.86), ("Izmir", 38.42, 27.14),
    ("Antalya", 36.90, 30.71), ("Munich", 48.14, 11.58), ("Hamburg", 53.55, 9.99), ("Frankfurt", 50.11, 8.68), ("Cologne", 50.94, 6.96),
    ("Zurich", 47.38, 8.54), ("Geneva", 46.20, 6.14), ("Copenhagen", 55.68, 12.57), ("Stockholm", 59.33, 18.07), ("Oslo", 59.91, 10.75),
    ("Helsinki", 60.17, 24.94), ("Tallinn", 59.44, 24.75), ("Riga", 56.95, 24.11), ("Vilnius", 54.69, 25.28), ("Dublin", 53.35, -6.26),
    ("Edinburgh", 55.95, -3.19), ("Manchester", 53.48, -2.24), ("Venice", 45.44, 12.33), ("Florence", 43.77, 11.26), ("Naples", 40.85, 14.27),
    ("Nice", 43.70, 7.27), ("Marseille", 43.30, 5.37), ("Lyon", 45.76, 4.84), ("Valencia", 39.47, -0.38), ("Seville", 37.39, -5.98),
    ("Malaga", 36.72, -4.42), ("Podgorica", 42.43, 19.26), ("Budva", 42.29, 18.84), ("Tirana", 41.33, 19.82), ("Skopje", 42.00, 21.43),
    ("Chisinau", 47.01, 28.86), ("Kyiv", 50.45, 30.52), ("Lviv", 49.84, 24.03), ("Odesa", 46.48, 30.72), ("Minsk", 53.90, 27.56),
    ("Moscow", 55.76, 37.62), ("Saint Petersburg", 59.94, 30.31), ("Kazan", 55.79, 49.12), ("Sochi", 43.60, 39.73), ("Krasnodar", 45.04, 38.98),
    ("Rostov-on-Don", 47.24, 39.71), ("Novosibirsk", 55.03, 82.92), ("Yekaterinburg", 56.84, 60.61), ("Nizhny Novgorod", 56.33, 44.00),
    ("Samara", 53.20, 50.15), ("Saratov", 51.53, 46.03), ("Volgograd", 48.71, 44.51), ("Voronezh", 51.66, 39.20), ("Kaliningrad", 54.71, 20.51),
    ("Vladivostok", 43.12, 131.89), ("Irkutsk", 52.29, 104.28), ("Murmansk", 68.97, 33.07), ("Stavropol", 45.04, 41.97),
    ("Makhachkala", 42.98, 47.50), ("Tbilisi", 41.72, 44.79), ("Batumi", 41.64, 41.64), ("Yerevan", 40.18, 44.51), ("Baku", 40.41, 49.87),
    ("Almaty", 43.24, 76.89), ("Astana", 51.17, 71.45), ("Tashkent", 41.30, 69.24), ("Samarkand", 39.65, 66.96), ("Bishkek", 42.87, 74.59),
    ("Dushanbe", 38.56, 68.79), ("Dubai", 25.20, 55.27), ("Abu Dhabi", 24.45, 54.38), ("Doha", 25.29, 51.53), ("Tel Aviv", 32.09, 34.78),
    ("Jerusalem", 31.77, 35.21), ("Cairo", 30.04, 31.24), ("Amman", 31.95, 35.93), ("Beirut", 33.89, 35.50), ("Tehran", 35.69, 51.39),
    ("Delhi", 28.61, 77.21), ("Mumbai", 19.08, 72.88), ("Bangalore", 12.97, 77.59), ("Goa", 15.50, 73.83), ("Kathmandu", 27.72, 85.32),
    ("Colombo", 6.93, 79.86), ("Bangkok", 13.76, 100.50), ("Phuket", 7.88, 98.39), ("Chiang Mai", 18.79, 98.98), ("Ko Samui", 9.51, 100.01),
    ("Hanoi", 21.03, 105.85), ("Ho Chi Minh City", 10.82, 106.63), ("Kuala Lumpur", 3.14, 101.69), ("Singapore", 1.35, 103.82),
    ("Bali", -8.65, 115.22), ("Jakarta", -6.21, 106.85), ("Manila", 14.60, 120.98), ("Hong Kong", 22.32, 114.17), ("Taipei", 25.03, 121.57),
    ("Shanghai", 31.23, 121.47), ("Beijing", 39.90, 116.41), ("Seoul", 37.57, 126.98), ("Tokyo", 35.68, 139.69), ("Osaka", 34.69, 135.50),
    ("Kyoto", 35.01, 135.77),
    ("New York", 40.71, -74.01), ("Boston", 42.36, -71.06), ("Washington", 38.91, -77.04), ("Philadelphia", 39.95, -75.17),
    ("Miami", 25.76, -80.19), ("Orlando", 28.54, -81.38), ("Atlanta", 33.75, -84.39), ("Chicago", 41.88, -87.63), ("Toronto", 43.65, -79.38),
    ("Montreal", 45.50, -73.57), ("Vancouver", 49.28, -123.12), ("Seattle", 47.61, -122.33), ("San Francisco", 37.77, -122.42),
    ("Los Angeles", 34.05, -118.24), ("San Diego", 32.72, -117.16), ("Las Vegas", 36.17, -115.14), ("Denver", 39.74, -104.99),
    ("Austin", 30.27, -97.74), ("Houston", 29.76, -95.37), ("Dallas", 32.78, -96.80), ("Mexico City", 19.43, -99.13), ("Cancun", 21.16, -86.85),
    ("Havana", 23.11, -82.37), ("Bogota", 4.71, -74.07), ("Lima", -12.05, -77.04), ("Santiago", -33.45, -70.67), ("Buenos Aires", -34.60, -58.38),
    ("Sao Paulo", -23.55, -46.63), ("Rio de Janeiro", -22.91, -43.17), ("Cape Town", -33.92, 18.42), ("Johannesburg", -26.20, 28.05),
    ("Nairobi", -1.29, 36.82), ("Marrakesh", 31.63, -7.99), ("Casablanca", 33.57, -7.59), ("Tunis", 36.81, 10.18), ("Sydney", -33.87, 151.21),
    ("Melbourne", -37.81, 144.96), ("Auckland", -36.85, 174.76),
]


def distance_km(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2
    return 12742 * math.asin(math.sqrt(a))


def place_name(lat, lon):
    """"Berlin" within 40 km, "near Berlin" within 150 km, otherwise the coordinates."""
    if lat is None or lon is None or (abs(lat) < 0.01 and abs(lon) < 0.01):  # 0,0 means "no location"
        return None
    if places.town_at(lat, lon) is not None:
        return places.place_label(lat, lon)
    name, km = min(((city, distance_km(lat, lon, clat, clon)) for city, clat, clon in CITIES), key=lambda item: item[1])
    return name if km <= 40 else f"near {name}" if km <= 150 else f"{lat:.1f}°, {lon:.1f}°"


def readable(text):
    """Meta exports store UTF-8 text as if it were Latin-1 ("ÐŸÑ€Ð¸Ð²ÐµÑ‚" for "Привет"). Undo that when it applies."""
    try:
        return text.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return text


def day_of(value):
    """A date from a Unix timestamp (seconds or milliseconds) or an ISO string, as YYYY-MM-DD."""
    try:
        if isinstance(value, (int, float)) or (isinstance(value, str) and value.isdigit()):
            number = float(value)
            return datetime.fromtimestamp(number / 1000 if number > 1e11 else number, timezone.utc).strftime("%Y-%m-%d")
        if isinstance(value, str) and re.match(r"\d{4}-\d{2}-\d{2}", value):
            return value[:10]
    except (ValueError, OverflowError, OSError):
        pass
    return None


class Life:
    def __init__(self, me):
        self.me = {name.casefold() for name in me if name.strip()}
        self.photos = Counter()                 # month → photos
        self.photos_year = Counter()            # year → photos dated only by a year in their file or folder name
        self.places = defaultdict(Counter)      # month → place → photos taken there
        self.visits = defaultdict(Counter)      # month → place → visits in the location history
        self.sent = Counter()                   # month → messages I wrote
        self.talk = defaultdict(Counter)        # month → person → messages both ways
        self.people = {}                        # person → first day, last day, messages, mine
        self.posts = defaultdict(list)          # month → (day, where, text)
        self.notes = defaultdict(list)          # month → (day, title, note)
        self.work = defaultdict(list)           # month → (day, text) from LinkedIn: a sales version, shown below my own notes
        self.music = defaultdict(Counter)       # month → artist → minutes
        self.watched = defaultdict(Counter)     # month → show or channel → times
        self.books = defaultdict(list)          # month → (day, title, author)
        self.calendar = defaultdict(list)       # month → (day, event)
        self.kept = defaultdict(list)           # month → (day, note) from Google Keep
        self.searches = defaultdict(Counter)    # month → what I searched for → times
        self.asked = defaultdict(list)          # month → (day, title) of a conversation with an AI
        self.hours = defaultdict(Counter)       # month → activity → hours, from a time tracker
        self.moods = defaultdict(list)          # month → (day, mood) from a mood diary
        self.diary = defaultdict(list)          # month → (day, text) written in a mood diary
        self.stories = defaultdict(list)        # month → (day, caption) of my Instagram stories
        self.comments = defaultdict(list)       # month → (day, where, text) of comments I wrote
        self.periods = defaultdict(list)        # month → day a period started (Flo)
        self.read = Counter()                   # what was read
        self.skipped = Counter()                # why something wasn't
        self.media = {}                         # picture path in an export → the day its JSON gives it (Instagram, Facebook)
        self.photo_files = {}                   # photo, as its path inside the exports folder → its day ("" if only a year is known)
        self.readers = {}                       # path inside the exports folder → a function that returns the file's bytes
        self.photo_people = defaultdict(Counter)  # month → person → photos they're in (from the faces add-on)
        self.located = defaultdict(dict)        # town → {day: photos taken there that day} (a phone-only day counts 0)
        self.told_homes = []                    # (town, from, until) from my_homes.csv
        self.trips = []                         # trips away from home (places.trips)

    def message(self, day, person, mine):
        month = day[:7]
        if mine:
            self.sent[month] += 1
        if person:
            self.talk[month][person] += 1
            card = self.people.setdefault(person, {"first": day, "last": day, "messages": 0, "mine": 0})
            card["first"], card["last"] = min(card["first"], day), max(card["last"], day)
            card["messages"] += 1
            card["mine"] += bool(mine)

    def photo(self, day, lat=None, lon=None):
        self.photos[day[:7]] += 1
        place = place_name(lat, lon)
        if place:
            self.places[day[:7]][place] += 1
            self.locate(day, place, 1)

    def locate(self, day, place, photos=0):
        """A day spent in a town: for visits and trips. Only real towns, not "near ..." or coordinates."""
        if place and len(day) == 10 and not place.startswith("near ") and "°" not in place:
            self.located[place][day] = self.located[place].get(day, 0) + photos


# ---------- readers ----------

def telegram(life, data):
    info = data.get("personal_information") or {}
    owner = f"user{info['user_id']}" if info.get("user_id") else None
    if info.get("first_name"):
        life.me.add(f"{info.get('first_name', '')} {info.get('last_name', '')}".strip().casefold())
    chats = data["chats"]["list"] if isinstance(data.get("chats"), dict) else [data]
    if not owner and not life.me:  # the one who writes in every chat is the owner
        senders = Counter()
        for chat in chats:
            senders.update({message.get("from_id") for message in chat.get("messages", []) if message.get("from_id")})
        owner = senders.most_common(1)[0][0] if senders and len(chats) > 1 else None
    for chat in chats:
        kind = chat.get("type")
        person = chat.get("name") or "deleted account"
        if kind in ("private_group", "private_supergroup"):
            person += " (group)"
        elif kind != "personal_chat":
            person = None  # channels and public groups: only my own messages count
        for message in chat.get("messages", []):
            day = day_of(message.get("date"))
            if message.get("type") != "message" or not day:
                continue
            mine = (owner and message.get("from_id") == owner) or (message.get("from") or "").casefold() in life.me
            life.message(day, person, mine)
    life.read["Telegram chats"] += len(chats)


WHATSAPP = re.compile(r"^‎?\[?(\d{1,4})[./-](\d{1,2})[./-](\d{2,4}),?\s+(\d{1,2}):(\d{2})(?::\d{2})?\s*([AaPp]\.?\s?[Mm]\.?)?\]?\s*(?:[-–]\s*)?"
                      r"([^:]{1,60}?):\s")


def whatsapp_lines(text):
    """(day, sender) for every message line. The date order (day first or month first) is worked out from the file itself."""
    rows = [match.groups() for match in map(WHATSAPP.match, text.splitlines()) if match]
    if not rows:
        return []
    month_first = any(row[5] for row in rows) and not any(int(row[0]) > 12 for row in rows)
    if any(int(row[1]) > 12 for row in rows):
        month_first = True
    if any(int(row[0]) > 12 and len(row[0]) <= 2 for row in rows):
        month_first = False
    out = []
    for a, b, year, *_rest, sender in rows:
        if len(a) == 4:  # 2021-03-14 style
            year, month, day = a, b, year
        else:
            month, day = (a, b) if month_first else (b, a)
            year = ("20" + year) if len(year) == 2 else year
        try:
            out.append((datetime(int(year), int(month), int(day)).strftime("%Y-%m-%d"), sender.strip()))
        except ValueError:
            continue
    return out


CHAT_NAME = [  # how WhatsApp names an exported chat in different languages; the name of the chat is what's left
    re.compile(r"(?i)^(?:whatsapp[ -]?chat|chat de whatsapp|conversa do whatsapp|discussion whatsapp|chat whatsapp|czat whatsapp|"
               r"чат whatsapp)\s*(?:with|con|com|mit|avec|met|z|с|з|-)\s+(.+)$"),
    re.compile(r"(?i)^whatsapp chat\s*-\s*(.+)$"),
    re.compile(r"(?i)^(.+?)\s+ile whatsapp sohbeti$"),
]


def whatsapp_chat_name(name, senders, me):
    for text in (Path(name).stem, Path(name).parent.name):  # iPhone exports (_chat.txt) carry the name on the folder
        for pattern in CHAT_NAME:
            match = pattern.match(text.strip())
            if match:
                return match.group(1).strip()
    others = [sender for sender, _ in senders.most_common() if sender.casefold() not in me]
    return others[0] if others else Path(name).stem


def whatsapp(life, files):
    """All WhatsApp chats together: whoever writes in most of them is me (unless --me said so)."""
    parsed = [(name, whatsapp_lines(text)) for name, text in files]
    parsed = [(name, rows) for name, rows in parsed if rows]
    if not life.me:
        presence = Counter()
        for _, rows in parsed:
            presence.update({sender for _, sender in rows})
        if presence and len(parsed) > 1:
            life.me.add(presence.most_common(1)[0][0].casefold())
    for name, rows in parsed:
        senders = Counter(sender for _, sender in rows)
        others = [sender for sender in senders if sender.casefold() not in life.me]
        person = whatsapp_chat_name(name, senders, life.me)
        if len(others) >= (2 if life.me else 3):  # more than one other person writes: a group, not a person
            person += " (group)"
        for day, sender in rows:
            life.message(day, person, sender.casefold() in life.me)
        life.read["WhatsApp chats"] += 1


def location_history(life, data):
    found = 0
    for item in data.get("timelineObjects", []):  # Takeout's Semantic Location History
        visit = item.get("placeVisit")
        if not visit:
            continue
        place = visit.get("location", {})
        duration = visit.get("duration", {})
        day = day_of(duration.get("startTimestamp") or duration.get("startTimestampMs"))
        town = place_name((place.get("latitudeE7") or 0) / 1e7, (place.get("longitudeE7") or 0) / 1e7)
        name = place.get("name") or town
        if day and name:
            life.visits[day[:7]][name] += 1
            life.locate(day, town)
            found += 1
    for segment in data.get("semanticSegments", []):  # the newer Timeline export from the phone
        visit = segment.get("visit")
        day = day_of(segment.get("startTime"))
        latlng = ((visit or {}).get("topCandidate", {}).get("placeLocation", {}) or {}).get("latLng", "")
        numbers = re.findall(r"-?\d+(?:\.\d+)?", latlng)
        if day and len(numbers) == 2:
            name = place_name(float(numbers[0]), float(numbers[1]))
            if name:
                life.visits[day[:7]][name] += 1
                life.locate(day, name)
                found += 1
    if found:
        life.read["location history files"] += 1
    return found


def facebook_posts(life, items):
    count = 0
    for item in items:
        day = day_of(item.get("timestamp"))
        texts = [readable(part["post"]) for part in item.get("data", []) if isinstance(part, dict) and part.get("post")]
        if day and texts:
            life.posts[day[:7]].append((day, "Facebook", " ".join(texts)))
            count += 1
    life.read["Facebook posts"] += count


def instagram_posts(life, items):
    count = 0
    for item in items:
        media = item.get("media") or []
        day = day_of(item.get("creation_timestamp") or (media[0].get("creation_timestamp") if media else None))
        caption = readable(item.get("title") or (media[0].get("title") if media else "") or "")
        if day:
            life.posts[day[:7]].append((day, "Instagram", caption or "(a post without a caption)"))
            count += 1
    life.read["Instagram posts"] += count


def meta_threads(life, threads):
    """Messenger and Instagram chats (message_1.json in each chat's folder). Whoever is in every chat is me."""
    if not life.me:
        presence = Counter()
        for _, data in threads:
            presence.update({readable(p.get("name", "")) for p in data.get("participants", [])})
        if presence and len(threads) > 1:
            life.me.add(presence.most_common(1)[0][0].casefold())
    for name, data in threads:
        where = "Instagram chats" if "instagram" in name.lower() else "Messenger chats"
        people = [readable(p.get("name", "")) for p in data.get("participants", [])]
        others = [person for person in people if person.casefold() not in life.me]
        if len(people) == 2 and others:
            person = others[0]
        else:  # a group chat
            person = (readable(data.get("title") or "") or ", ".join(others[:3])) + " (group)"
        for message in data.get("messages", []):
            day = day_of(message.get("timestamp_ms"))
            if day:
                life.message(day, person, readable(message.get("sender_name", "")).casefold() in life.me)
        life.read[where] += 1


def twitter(life, text):
    """X/Twitter archive (data/tweets.js). Retweets are other people's words, so they're left out."""
    items = json.loads(text[text.index("=") + 1:])
    for item in items:
        tweet = item.get("tweet", item)
        words = tweet.get("full_text") or tweet.get("text") or ""
        try:
            day = datetime.strptime(tweet.get("created_at", ""), "%a %b %d %H:%M:%S %z %Y").strftime("%Y-%m-%d")
        except ValueError:
            continue
        if words.startswith("RT @"):
            life.read["retweets left out"] += 1
            continue
        life.posts[day[:7]].append((day, "X", html.unescape(words)))
        life.read["X posts"] += 1


def calendar_events(life, text):
    text = re.sub(r"\n[ \t]", "", re.sub(r"\r+\n", "\n", text))  # long lines are folded in .ics files
    for block in re.findall(r"BEGIN:VEVENT(.*?)END:VEVENT", text, re.S):
        start = re.search(r"^DTSTART[^:\n]*:(\d{4})(\d{2})(\d{2})", block, re.M)
        summary = re.search(r"^SUMMARY[^:\n]*:(.*)$", block, re.M)
        if start:
            day = f"{start.group(1)}-{start.group(2)}-{start.group(3)}"
            title = re.sub(r"\\([,;\\])", r"\1", summary.group(1).strip()).replace("\\n", " ") if summary else "(no title)"
            life.calendar[day[:7]].append((day, title))
            life.read["calendar events"] += 1


def spotify(life, items):
    for item in items:
        artist = item.get("master_metadata_album_artist_name") or item.get("artistName")
        day = day_of(item.get("ts") or (item.get("endTime") or "")[:10])
        minutes = (item.get("ms_played") or item.get("msPlayed") or 0) / 60000
        if artist and day and minutes >= 0.5:
            life.music[day[:7]][artist] += minutes
            life.read["songs played (Spotify)"] += 1


def youtube(life, items):
    """Google's "My Activity" files from Takeout: videos watched on YouTube, and what was searched for."""
    for item in items:
        title = str(item.get("title", ""))
        if title.startswith("Searched for ") and not item.get("details"):
            day = day_of(item.get("time"))
            if day:
                life.searches[day[:7]][" ".join(title[len("Searched for "):].split())[:120]] += 1
                life.read["searches"] += 1
            continue
        if item.get("details") or not item.get("subtitles") or not title.startswith("Watched"):
            continue  # ads, removed videos, pages visited
        day = day_of(item.get("time"))
        if day:
            life.watched[day[:7]][item["subtitles"][0].get("name", "YouTube")] += 1
            life.read["YouTube videos watched"] += 1


def netflix(life, text):
    for row in csv.DictReader(io.StringIO(text)):
        title = (row.get("Title") or "").split(":")[0].strip()  # "Dark: Season 1: Secrets" is Dark
        stamp = (row.get("Start Time") or row.get("Date") or "").strip()
        day = None
        if re.match(r"\d{4}-\d{2}-\d{2}", stamp):
            day = stamp[:10]
        elif re.fullmatch(r"\d{1,2}/\d{1,2}/\d{2,4}", stamp):  # the website's file: month/day/year
            month, date, year = stamp.split("/")
            day = f"{('20' + year) if len(year) == 2 else year}-{int(month):02d}-{int(date):02d}"
        elif re.fullmatch(r"\d{1,2}\.\d{1,2}\.\d{2,4}", stamp):  # day.month.year in many countries
            date, month, year = stamp.split(".")
            day = f"{('20' + year) if len(year) == 2 else year}-{int(month):02d}-{int(date):02d}"
        if title and day:
            life.watched[day[:7]][title] += 1
            life.read["Netflix titles watched"] += 1


def goodreads(life, text):
    for row in csv.DictReader(io.StringIO(text)):
        stamp = (row.get("Date Read") or "").strip().replace("/", "-")
        if re.match(r"\d{4}-\d{2}-\d{2}", stamp) and row.get("Title"):
            life.books[stamp[:7]].append((stamp[:10], row["Title"].strip(), (row.get("Author") or "").strip()))
            life.read["books read"] += 1


def linkedin_positions(life, text):
    def month_of(value):
        value = (value or "").strip()
        for pattern in ("%b %Y", "%Y"):
            try:
                return datetime.strptime(value, pattern).strftime("%Y-%m")
            except ValueError:
                continue
        return None
    for row in csv.DictReader(io.StringIO(text)):
        company, title = (row.get("Company Name") or "").strip(), (row.get("Title") or "").strip()
        started, finished = month_of(row.get("Started On")), month_of(row.get("Finished On"))
        if started and company:
            life.work[started].append((started, f"Started as {title} at {company}" if title else f"Started at {company}"))
        if finished and company:
            life.work[finished].append((finished, f"Left {company}"))
        if started or finished:
            life.read["LinkedIn positions"] += 1


def keep_note(life, data):
    if data.get("isTrashed"):
        return
    day = day_of(int(data.get("createdTimestampUsec", 0)) // 1000 or None)
    text = (data.get("title") or "").strip() or " ".join((data.get("textContent") or "").split())[:120]
    if not text and data.get("listContent"):
        text = ", ".join(item.get("text", "") for item in data["listContent"][:5])
    if day and text:
        life.kept[day[:7]].append((day, text))
        life.read["Keep notes"] += 1


def text_messages(life, data):
    """Android text messages saved by the "SMS Backup & Restore" app. Numbers never reach the page."""
    import xml.etree.ElementTree as ElementTree
    for _, element in ElementTree.iterparse(io.BytesIO(data)):
        if element.tag == "sms":
            day = day_of(element.get("date"))
            name = element.get("contact_name") or ""
            person = name if name and name != "(Unknown)" else "an unknown number"
            if day:
                life.message(day, person, element.get("type") == "2")
                life.read["text messages"] += 1
        element.clear()


def sent_mail(life, path):
    """Gmail from Google Takeout (an .mbox file). Only mail I sent: the people I wrote to, not newsletters."""
    import mailbox
    from email.utils import getaddresses, parsedate_to_datetime
    box = mailbox.mbox(path, create=False)
    try:
        for message in box:
            if "sent" not in (message.get("X-Gmail-Labels") or "").lower():
                continue
            try:
                day = parsedate_to_datetime(message["Date"]).strftime("%Y-%m-%d")
            except (TypeError, ValueError):
                continue
            for name, address in getaddresses(message.get_all("To", []) + message.get_all("Cc", [])):
                life.message(day, name.strip() or address, True)
            life.read["emails I sent"] += 1
    finally:
        box.close()


def instagram_stories(life, items):
    for item in items:
        day = day_of(item.get("creation_timestamp"))
        if day:
            life.stories[day[:7]].append((day, " ".join(readable(item.get("title") or "").split())))
            life.read["Instagram stories"] += 1


def instagram_comments(life, items):
    """Comments I wrote on Instagram posts and reels: string_map_data with Comment, Media Owner and Time."""
    for item in items:
        fields = item.get("string_map_data") or {}
        text = readable((fields.get("Comment") or {}).get("value") or "")
        day = day_of((fields.get("Time") or {}).get("timestamp"))
        owner = readable((fields.get("Media Owner") or {}).get("value") or "")
        if day and text.strip():
            life.comments[day[:7]].append((day, f"Instagram{', on ' + owner if owner else ''}", " ".join(text.split())))
            life.read["comments I wrote"] += 1


def facebook_comments(life, items):
    """Comments I wrote on Facebook (comments_v2)."""
    for item in items:
        day = day_of(item.get("timestamp"))
        texts = [readable((part.get("comment") or {}).get("comment") or "") for part in item.get("data", []) if isinstance(part, dict)]
        text = " ".join(" ".join(texts).split())
        if day and text:
            life.comments[day[:7]].append((day, "Facebook", text))
            life.read["comments I wrote"] += 1


def flo(life, data):
    """Flo's own data download: the day each period started."""
    for cycle in (data.get("operationalData") or {}).get("cycles") or []:
        day = day_of(str(cycle.get("period_start_date") or "")[:10])
        if day:
            life.periods[day[:7]].append(day)
            life.read["periods (Flo)"] += 1


def ai_chats(life, items):
    """A ChatGPT export (conversations.json): when each conversation started and what it was called.
    If other people used the account, some of these are theirs."""
    for item in items:
        day = day_of(item.get("create_time"))
        if day:
            life.asked[day[:7]].append((day, " ".join(str(item.get("title") or "(no title)").split())[:160]))
            life.read["AI chats"] += 1


def stamp_day(value):
    """The day in "2024-03-05 08:10", "2024.03.05", "Mar 5, 2024, 8:10 AM" or "05.03.2024 08:10"."""
    value = (value or "").strip()
    found = re.match(r"(\d{4})[-./](\d{1,2})[-./](\d{1,2})", value)
    if found:
        year, month, day = map(int, found.groups())
    else:
        found = re.match(r"([A-Za-z]{3})[a-z]*\.? (\d{1,2}), (\d{4})", value)
        if found and found.group(1).title() in SHORT:
            year, month, day = int(found.group(3)), SHORT.index(found.group(1).title()) + 1, int(found.group(2))
        else:
            found = re.match(r"(\d{1,2})\.(\d{1,2})\.(\d{4})", value)
            if not found:
                return None
            day, month, year = map(int, found.groups())
    try:
        return datetime(year, month, day).strftime("%Y-%m-%d")
    except ValueError:
        return None


def time_tracker(life, text):
    """A time tracker's CSV (aTimeLogger and similar): Activity type, Duration, From. The totals at the end have no date."""
    for row in csv.DictReader(io.StringIO(text)):
        day = stamp_day(row.get("From"))
        parts = re.findall(r"\d+", row.get("Duration") or "")
        activity = (row.get("Activity type") or "").strip()
        if day and activity and len(parts) >= 2:
            life.hours[day[:7]][activity] += int(parts[0]) + int(parts[1]) / 60 + (int(parts[2]) / 3600 if len(parts) > 2 else 0)
            life.read["time tracker entries"] += 1


def mood_diary(life, text):
    """A mood diary's CSV (Daylio, DailyBean and similar): a date, a mood, and sometimes a few words."""
    for row in csv.DictReader(io.StringIO(text)):
        row = {(key or "").strip().lower(): (value or "").strip() for key, value in row.items()}
        day = stamp_day(row.get("full_date") or row.get("date"))
        if not day or not row.get("mood"):
            continue
        life.moods[day[:7]].append((day, row["mood"]))
        words = " ".join(part for part in (row.get("note_title"), row.get("note") or row.get("short_diary") or row.get("diary")) if part)
        if words:
            life.diary[day[:7]].append((day, " ".join(words.split())))
        life.read["mood diary days"] += 1


def my_events(life, text):
    for row in csv.DictReader(io.StringIO(text)):
        day = (row.get("date") or "").strip()
        if re.fullmatch(r"\d{4}(-\d{2}(-\d{2})?)?", day) and (row.get("title") or "").strip():
            # "1977" stays a year: it shows with the year, not under January
            life.notes[day[:7]].append((day, row["title"].strip(), (row.get("note") or "").strip()))
            life.read["notes of my own"] += 1


def real_day(day):
    """The day if it can be a photo's date: cameras with an unset clock write "0000:00:00", and that isn't a year."""
    match = re.fullmatch(r"(\d{4})-(\d\d)-(\d\d)", day or "")
    if match and 1900 <= int(match.group(1)) <= datetime.now().year + 1 and 1 <= int(match.group(2)) <= 12 and 1 <= int(match.group(3)) <= 31:
        return day
    return None


CLOCK_DEFAULTS = {"1970-01-01", "1980-01-01", "2000-01-01"}  # the first day a camera's or phone's unset clock shows


def stored_day(day):
    """A date stored inside a photo or its .json: not real if it's a clock's starting day (214 photos of one 2008 camera
    all said Jan 1, 2000). Such a photo falls back to the year in its folder's name."""
    day = real_day(day)
    return None if day in CLOCK_DEFAULTS else day


def photo_info(name, data, sidecar):
    """(day, lat, lon) from Takeout's .json next to the photo, the photo's own data, or the date in its file name."""
    if sidecar:
        taken = (sidecar.get("photoTakenTime") or {}).get("timestamp")
        geo = sidecar.get("geoData") or {}
        day = stored_day(day_of(taken))
        if day:
            return day, geo.get("latitude"), geo.get("longitude")
    if Image is not None and data is not None:
        try:
            with warnings.catch_warnings(), Image.open(io.BytesIO(data)) as image:  # a damaged header is just "no date"
                warnings.simplefilter("ignore")
                exif = image.getexif()
                stamp = exif.get_ifd(0x8769).get(36867) or exif.get(306)
                gps = exif.get_ifd(0x8825)
                lat = lon = None
                if gps and 2 in gps and 4 in gps:
                    to_degrees = lambda parts: float(parts[0]) + float(parts[1]) / 60 + float(parts[2]) / 3600
                    lat = to_degrees(gps[2]) * (-1 if gps.get(1) == "S" else 1)
                    lon = to_degrees(gps[4]) * (-1 if gps.get(3) == "W" else 1)
                if stamp and re.match(r"\d{4}:\d{2}:\d{2}", str(stamp)) and stored_day(str(stamp)[:10].replace(":", "-")):
                    return str(stamp)[:10].replace(":", "-"), lat, lon
        except Exception:  # an unreadable picture still gets the date in its name
            pass
    base = Path(name).name
    match = re.search(r"@(\d\d)-(\d\d)-(\d{4})_\d\d-\d\d-\d\d", base)  # Telegram Desktop: photo_12@15-07-2023_12-02-58.jpg
    if match and real_day(f"{match.group(3)}-{match.group(2)}-{match.group(1)}"):
        return f"{match.group(3)}-{match.group(2)}-{match.group(1)}", None, None
    match = re.search(r"(?<!\d)((?:19|20)\d\d)[-_]?(0[1-9]|1[0-2])[-_]?(0[1-9]|[12]\d|3[01])(?!\d)", base)
    if match and real_day(f"{match.group(1)}-{match.group(2)}-{match.group(3)}"):
        return f"{match.group(1)}-{match.group(2)}-{match.group(3)}", None, None
    return None, None, None


def media_dates(data, found):
    """Instagram and Facebook date every picture in their JSON ({"uri": "media/posts/202101/1788….jpg", "creation_timestamp": …});
    a chat photo sits in a message with its own "timestamp_ms". Collect uri → day, so the pictures themselves get their dates."""
    stack = [(data, None)]
    while stack:
        item, inherited = stack.pop()
        if isinstance(item, dict):
            own = item.get("creation_timestamp") or item.get("timestamp_ms") or item.get("timestamp") or inherited
            uri = item.get("uri")
            if isinstance(uri, str) and Path(uri).suffix.lower() in PHOTO_TYPES and own:
                day = real_day(day_of(own))
                if day:
                    found.setdefault(uri.replace("\\", "/").lower().lstrip("./"), day)
            stack.extend((value, own) for value in item.values() if isinstance(value, (dict, list)))
        elif isinstance(item, list):
            stack.extend((value, inherited) for value in item if isinstance(value, (dict, list)))


def media_day(name, found):
    """The day an export's JSON gives this picture: its path ends with the JSON's uri ("…/media/posts/202101/1788….jpg")."""
    parts = name.replace("\\", "/").lower().split("/")
    for length in range(2, min(8, len(parts)) + 1):
        day = found.get("/".join(parts[-length:]))
        if day:
            return day
    return None


def tweet_media_day(name):
    """A picture from an X archive is named after its post ("1453…-AbC.jpg"), and a post number holds its time."""
    match = re.match(r"(\d{15,20})-", Path(name).name)
    if match and re.search(r"(?i)tweets?_media|direct_messages?(?:_group)?_media", name.replace("\\", "/")):
        stamp = ((int(match.group(1)) >> 22) + 1288834974657) / 1000
        return real_day(datetime.fromtimestamp(stamp, timezone.utc).strftime("%Y-%m-%d"))
    return None


COUNTER = re.compile(r"(?i)^(?:img|dsc|dscn|dscf|pxl|pict|scan|photo|image|mvi|vid|p)[-_ ]?\d+")  # camera numbers, not years
DECADE = re.compile(r"(?i)(?:19|20)\d0(?:s|’s|'s|-?е|-?ые|-?х)\b")


def year_in_name(name):
    """The year a photo was taken, from its file name or the nearest folder that names one ("1985 dacha.jpg",
    "Albums/1977"). Camera numbers (IMG_2019) and decades ("1980s") don't count as years."""
    parts = Path(name.replace("\\", "/")).parts
    for index, part in enumerate(reversed(parts[-6:])):  # the nearest folder with a year: "2008/November/Promo/photo.jpg"
        text = Path(part).stem if index == 0 else part
        if (index == 0 and COUNTER.match(text)) or DECADE.search(text) or re.search(r"[0-9a-fA-F]{16}", text) \
                or re.search(r"(?:19|20)\d\d\s*[-–]\s*(?:19|20)\d\d", text):
            continue  # a camera number, a decade, a hash ("e46141c79ac1903ee7b9…") or a span of years ("archive 2007-2011")
        # a year alone: not glued to other letters or digits, and not part of a date stamp like 2026-10
        match = re.search(r"(?<![0-9A-Za-z])(19\d\d|20\d\d)(?![-_.]?\d)(?![0-9A-Za-z])", text)
        if match and 1900 <= int(match.group(1)) <= datetime.now().year:
            return match.group(1)
    return None


# ---------- walking the folder (and the zips inside it) ----------

def entries(root, opened, left_out=None):
    """(name, read) for every file under root and inside every .zip there; read() returns the bytes. Zips go in `opened`.
    Program and cache folders, hidden folders and the made-up sample data (a folder with .lifekeeper-sample in it, unless it's
    the folder you opened) are left out and counted in `left_out`."""
    root = Path(root)
    left_out = left_out if left_out is not None else Counter()
    paths = sorted(root.rglob("*"))
    samples = {path.parent for path in paths if path.name == SAMPLE_MARKER and path.parent != root}

    def kept(folders, name):  # program, cache and hidden folders, and video thumbnails ("…mp4_thumb.jpg"), stay out
        if any(folder.startswith(".") or folder.lower() in SKIP_DIRS for folder in folders):
            left_out["files in program, cache or hidden folders"] += 1
            return False
        if name.lower().endswith("_thumb.jpg"):
            left_out["video thumbnails"] += 1
            return False
        return True

    for path in paths:
        if not path.is_file() or path.name == SAMPLE_MARKER:
            continue
        if not kept(path.relative_to(root).parts[:-1], path.name):
            continue
        if any(sample in path.parents for sample in samples):
            left_out["files of the made-up sample data"] += 1
            continue
        if path.suffix.lower() == ".zip":
            try:
                archive = zipfile.ZipFile(path)
            except zipfile.BadZipFile:
                yield str(path), None
                continue
            opened.append(archive)
            for member in sorted(archive.namelist()):
                if not member.endswith("/") and kept(member.split("/")[:-1], member.split("/")[-1]):
                    yield f"{path}/{member}", (lambda archive=archive, member=member: archive.read(member))
        else:
            yield str(path), (lambda path=path: path.read_bytes())


def build(root, me):
    opened = []
    try:
        return read_all(root, me, opened)
    finally:
        for archive in opened:
            archive.close()


def read_all(root, me, opened):
    life = Life(me)
    files = {name: read for name, read in entries(root, opened, life.skipped)}
    whatsapp_files, threads, photos = [], [], []
    for name, read in files.items():
        lower = name.lower()
        suffix = Path(lower).suffix
        base = Path(lower).name
        if read is None:
            life.skipped["damaged zip files"] += 1
            continue
        try:
            if suffix in PHOTO_TYPES:
                photos.append((name, read))  # read last: the exports' JSON can date them (Instagram, Facebook)
            elif suffix == ".txt" and ("whatsapp" in lower or lower.endswith("/_chat.txt") or lower.endswith("\\_chat.txt")):
                whatsapp_files.append((name, read().decode("utf-8", "replace")))
            elif base == "my_events.csv":
                my_events(life, read().decode("utf-8-sig", "replace"))
            elif base == "my_homes.csv":
                life.told_homes += places.read_homes(read().decode("utf-8-sig", "replace"))
            elif base in ("viewingactivity.csv", "netflixviewinghistory.csv"):
                netflix(life, read().decode("utf-8-sig", "replace"))
            elif base == "goodreads_library_export.csv":
                goodreads(life, read().decode("utf-8-sig", "replace"))
            elif base == "positions.csv":
                linkedin_positions(life, read().decode("utf-8-sig", "replace"))
            elif base in ("tweets.js", "tweet.js"):
                twitter(life, read().decode("utf-8", "replace"))
            elif suffix == ".ics":
                calendar_events(life, read().decode("utf-8", "replace"))
            elif suffix == ".csv":  # told apart by their first line
                text = read().decode("utf-8-sig", "replace")
                columns = {column.strip().strip('"').lower() for column in text.split("\n", 1)[0].split(",")}
                if {"activity type", "duration", "from"} <= columns:
                    time_tracker(life, text)
                elif "mood" in columns and columns & {"full_date", "date"}:
                    mood_diary(life, text)
            elif suffix == ".xml" and b"<smses" in read()[:2000]:
                text_messages(life, read())
            elif suffix == ".mbox":
                if Path(name).is_file():
                    sent_mail(life, name)
                else:
                    life.skipped["mailboxes inside zips (unzip them first)"] += 1
            elif suffix == ".json":
                data = json.loads(read().decode("utf-8", "replace"))
                first = data[0] if isinstance(data, list) and data and isinstance(data[0], dict) else {}
                if isinstance(data, dict) and ("photoTakenTime" in data or "geoData" in data):
                    continue  # a photo's own .json, read with the photo
                telegram_export = isinstance(data, dict) and (isinstance(data.get("chats"), dict) or (data.get("messages") and "type" in data))
                if not telegram_export:  # Telegram's photos carry their dates in their names; Meta's are dated in their JSON
                    media_dates(data, life.media)
                if isinstance(data, dict) and isinstance(data.get("ig_stories"), list):
                    instagram_stories(life, data["ig_stories"])
                    continue
                if isinstance(data, dict) and isinstance(data.get("comments_reels_comments"), list):
                    instagram_comments(life, data["comments_reels_comments"])
                    continue
                if isinstance(data, dict) and isinstance(data.get("comments_v2"), list):
                    facebook_comments(life, data["comments_v2"])
                    continue
                if isinstance(data, dict) and isinstance((data.get("operationalData") or {}).get("cycles"), list):
                    flo(life, data)
                    continue
                if "string_map_data" in first and "Comment" in (first.get("string_map_data") or {}):
                    instagram_comments(life, data)
                    continue
                if isinstance(data, dict) and "participants" in data and isinstance(data.get("messages"), list):
                    threads.append((name, data))
                elif isinstance(data, dict) and (isinstance(data.get("chats"), dict) or (data.get("messages") and "type" in data)):
                    telegram(life, data)
                elif isinstance(data, dict) and ("timelineObjects" in data or "semanticSegments" in data):
                    location_history(life, data)
                elif isinstance(data, dict) and "createdTimestampUsec" in data:
                    keep_note(life, data)
                elif "timestamp" in first and "data" in first:
                    facebook_posts(life, data)
                elif "media" in first:
                    instagram_posts(life, data)
                elif "ms_played" in first or "msPlayed" in first:
                    spotify(life, data)
                elif "header" in first and "time" in first:
                    youtube(life, data)
                elif "mapping" in first and "create_time" in first:
                    ai_chats(life, data)
        except (ValueError, OSError, zipfile.BadZipFile, KeyError, SyntaxError):
            life.skipped[f"unreadable {suffix or 'files'}"] += 1
    whatsapp(life, whatsapp_files)
    meta_threads(life, threads)
    life.readers = {photo_key(root, name): read for name, read in photos}
    for name, read in photos:
        key = photo_key(root, name)
        try:
            sidecar = None
            for candidate in (name + ".json", name + ".supplemental-metadata.json", re.sub(r"\.[^.]+$", ".json", name)):
                if candidate in files and candidate != name:
                    try:
                        sidecar = json.loads(files[candidate]())
                    except ValueError:
                        pass
                    break
            dated = bool(sidecar and (sidecar.get("photoTakenTime") or {}).get("timestamp"))
            known = None if dated else (media_day(name, life.media) or tweet_media_day(name))  # dated by its export's JSON or post number
            day, lat, lon = (known, None, None) if known else photo_info(name, read() if Image is not None and not dated else None, sidecar)
            if day:
                life.photo(day, lat, lon)
                life.photo_files[key] = day
                life.read["photos"] += 1
            elif year_in_name(name[len(str(Path(root))):]):  # a scanned album: "1977 wedding.jpg", a folder called "1985"
                life.photos_year[year_in_name(name[len(str(Path(root))):])] += 1
                life.photo_files[key] = year_in_name(name[len(str(Path(root))):])
                life.read["photos"] += 1
            else:
                life.skipped["photos without a date"] += 1
        except (ValueError, OSError, zipfile.BadZipFile, KeyError, SyntaxError):
            life.skipped["unreadable photos"] += 1
    people_in_photos(life, root)
    notes = sorted((day, title) for items in life.notes.values() for day, title, _ in items)
    life.trips = places.trips(life.located, life.told_homes, notes) if life.located else []
    life.read["trips"] = len(life.trips)
    return life


def photo_key(root, name):
    """A photo's path inside the exports folder, with "/" on every system, so the faces file works on Windows and Mac."""
    return name[len(str(Path(root))):].replace("\\", "/").lstrip("/")


def faces_file(root):
    """Where the faces add-on keeps what it found and the names you gave: next to the exports folder, never inside it."""
    return Path(root).resolve().parent / "lifekeeper-faces.sqlite3"


def people_in_photos(life, root):
    """Who is in which photos, if you've run the faces add-on and named people. Plain sqlite3: no add-on needed to read it."""
    path = faces_file(root)
    if not path.is_file():
        return
    import sqlite3
    from contextlib import closing
    try:
        with closing(sqlite3.connect(path)) as connection:
            group_names = {}
            for person, name, _ in connection.execute(
                    "SELECT f.person, n.name, count(*) FROM faces f JOIN names n ON n.face_id = f.id "
                    "GROUP BY f.person, n.name ORDER BY 3"):
                group_names[person] = name  # the most-voted name wins (last, in ascending order)
            seen = set()
            for photo, person in connection.execute("SELECT photo, person FROM faces WHERE person IS NOT NULL"):
                name, day = group_names.get(person), life.photo_files.get(photo)
                if name and day and len(day) >= 7 and (photo, name) not in seen:
                    seen.add((photo, name))
                    life.photo_people[day[:7]][name] += 1
    except sqlite3.Error:
        life.skipped["unreadable faces file"] += 1


# ---------- the page ----------

ORDER = ["photos", "Telegram chats", "WhatsApp chats", "Messenger chats", "Instagram chats", "text messages", "emails I sent",
         "location history files", "Facebook posts", "Instagram posts", "X posts", "retweets left out", "Instagram stories", "comments I wrote", "calendar events",
         "songs played (Spotify)", "YouTube videos watched", "Netflix titles watched", "books read", "Keep notes",
         "searches", "AI chats", "time tracker entries", "mood diary days", "periods (Flo)", "LinkedIn positions", "notes of my own"]


def counted(counter):
    """"252 photos, 1 WhatsApp chat": what was read, in a fixed order, singular when there's one."""
    items = sorted((item for item in counter.items() if item[1]), key=lambda item: ORDER.index(item[0]) if item[0] in ORDER else len(ORDER))
    return ", ".join(f"{count:,} " + (re.sub(r"\b(\w+?)s\b", r"\1", what, count=1) if count == 1 else what) for what, count in items)


def when(day):
    """"Mar 14, 2019", "Mar 2019" or "2019"."""
    parts = day.split("-")
    if len(parts) == 3:
        return f"{SHORT[int(parts[1]) - 1]} {int(parts[2])}, {parts[0]}"
    if len(parts) == 2:
        return f"{SHORT[int(parts[1]) - 1]} {parts[0]}"
    return day


def listed(counter, limit, unit):
    items = [f"{html.escape(name)} <span class=n>({count:,} {unit}{'' if count == 1 else 's'})</span>" for name, count in counter.most_common(limit)]
    return ", ".join(items)


def names(counter, limit):
    top = [html.escape(name) for name, _ in counter.most_common(limit)]
    return top[0] if len(top) == 1 else ", ".join(top[:-1]) + " and " + top[-1] if top else ""


def span(start, end):
    """"Aug 13–21, 2021", "Aug 28 – Sep 3, 2021", "Dec 30, 2021 – Jan 2, 2022", or one day."""
    a, b = datetime.fromisoformat(start), datetime.fromisoformat(end)
    if a == b:
        return when(start)
    if a.year != b.year:
        return f"{when(start)} – {when(end)}"
    if a.month != b.month:
        return f"{SHORT[a.month - 1]} {a.day} – {SHORT[b.month - 1]} {b.day}, {a.year}"
    return f"{SHORT[a.month - 1]} {a.day}–{b.day}, {a.year}"


def trip_text(trip):
    where = html.escape(", ".join(trip["places"][:5]) + (" and more" if len(trip["places"]) > 5 else ""))
    country = html.escape(", ".join(trip["countries"][:3]))
    note = f" · {html.escape(trip['note'])}" if trip["note"] else ""
    photos = f", {trip['photos']:,} photo{'' if trip['photos'] == 1 else 's'}" if trip["photos"] else ""
    return (f"{where}{f' <span class=n>({country})</span>' if country else ''}{note} "
            f"<span class=n>{span(trip['start'], trip['end'])}, {trip['days']} day{'' if trip['days'] == 1 else 's'}{photos}</span>")


def mood_line(days):
    """"3.8 on average (23 days)" for moods kept as numbers, "mostly good (23 days)" for moods kept as words."""
    values = [mood for _, mood in days]
    count = f"{len(values)} day{'' if len(values) == 1 else 's'}"
    try:
        numbers = [float(value.replace(",", ".")) for value in values]
    except ValueError:
        return f"mostly {html.escape(Counter(values).most_common(1)[0][0])} <span class=n>({count})</span>"
    return f"{sum(numbers) / len(numbers):.1f} on average <span class=n>({count})</span>"


def next_steps(life):
    """The three sources that would add most to this page, judged by what's missing from it."""
    has = lambda *keys: any(life.read.get(key) for key in keys)
    ideas = [
        (not life.notes, "<b>Your own notes.</b> Write <i>my_events.csv</i> with the 10–20 turning points of your life (moves, jobs, "
                         "people, births, losses). They are shown first in each month."),
        (not has("photos"), "<b>Your phone's photos.</b> Copy them as they are: they show where you were, month by month."),
        (not has("Telegram chats", "WhatsApp chats", "Messenger chats", "Instagram chats", "text messages"),
         "<b>Your chats.</b> Export WhatsApp or Telegram: they show who you talked to, and when."),
        (has("photos") and not life.places and not life.visits,
         "<b>Places.</b> Your photos have no locations: add Google Takeout's location history, or copy photos straight from the phone."),
        (not has("Facebook posts", "Instagram posts", "X posts", "Keep notes"), "<b>What you wrote.</b> Download your Facebook, "
                                                                                "Instagram or X posts, or your Google Keep notes."),
        (not life.music, "<b>Music.</b> Spotify's extended streaming history shows what you listened to each month."),
        (not life.calendar, "<b>Your calendar</b> (.ics): trips, birthdays and appointments."),
    ]
    return [text for missing, text in ideas if missing][:3]


def folded(label, items, first=""):
    """A line that opens on click: long or personal lists stay closed until asked for, with a glimpse of the first one."""
    glimpse = f" <span class=n>· {html.escape(first[:70])}{'…' if len(first) > 70 else ''}</span>" if first else ""
    return f"<details><summary><span class=k>{label}</span> {len(items)}{glimpse}</summary><ul>{''.join(items)}</ul></details>"


def render(life, title):
    months = sorted(set(life.photos) | set(life.places) | set(life.visits) | set(life.sent) | set(life.talk) | set(life.posts)
                    | set(life.notes) | set(life.work) | set(life.music) | set(life.watched) | set(life.books) | set(life.calendar)
                    | set(life.kept) | set(life.searches) | set(life.asked) | set(life.hours) | set(life.moods) | set(life.stories) | set(life.comments)
                    | set(life.periods) | set(life.photo_people))
    months = [month for month in months if re.fullmatch(r"\d{4}-\d{2}", month)]
    year_notes = {key: items for key, items in life.notes.items() if re.fullmatch(r"\d{4}", key)}  # "1977": known only by the year
    years = sorted({month[:4] for month in months} | set(year_notes) | set(life.photos_year))
    if not years:
        return None
    total_messages = sum(card["messages"] for card in life.people.values())
    summary = [f"{years[0]}–{years[-1]}" if len(years) > 1 else years[0]]
    photos = sum(life.photos.values()) + sum(life.photos_year.values())
    if photos:
        summary.append(f"{photos:,} photo{'s' if photos != 1 else ''}")
    if total_messages:
        groups = sum(1 for person in life.people if person.endswith(" (group)"))
        persons = len(life.people) - groups
        with_whom = ([f"with {persons:,} {'person' if persons == 1 else 'people'}"] if persons else []) + \
                    ([f"in {groups:,} group chat{'s' if groups != 1 else ''}"] if groups else [])
        summary.append(f"{total_messages:,} messages " + " and ".join(with_whom))
    posts = sum(len(items) for items in life.posts.values())
    if posts:
        summary.append(f"{posts:,} posts")
    notes = sum(len(items) for items in life.notes.values())
    if notes:
        summary.append(f"{notes:,} notes of my own")
    body = [f"<header><h1>{html.escape(title)}</h1><p class=sum>{' · '.join(summary)}</p>",
            "<nav>" + " ".join(f"<a href='#y{year}'>{year}</a>" for year in years) + (" <a href='#people'>people</a>" if life.people else "")
            + "</nav></header>"]
    for year in years:
        in_year = [month for month in months if month.startswith(year)]
        places, talk, music = Counter(), Counter(), Counter()
        for month in in_year:
            places.update(life.places.get(month) or life.visits.get(month) or Counter())  # photos first; the location history fills in
            talk.update(life.talk.get(month, Counter()))
            music.update(life.music.get(month, Counter()))
        line = []
        if places:
            line.append(f"Mostly in {names(places, 3)}.")
        if talk:
            line.append(f"Talked most with {names(talk, 3)}.")
        if music:
            line.append(f"Listened most to {names(music, 3)}.")
        year_posts = sum(len(life.posts.get(month, [])) for month in in_year)
        if year_posts:
            line.append(f"{year_posts:,} post{'s' if year_posts != 1 else ''}.")
        missing = [MONTH_NAMES[number - 1] for number in range(1, 13) if f"{year}-{number:02d}" not in in_year]
        if 0 < len(missing) <= 3 and year not in (years[0], years[-1]):  # gaps matter in a full year; in a sparse one they're noise
            line.append(f"Nothing from {' and '.join(missing) if len(missing) <= 2 else ', '.join(missing[:-1]) + ' and ' + missing[-1]}.")
        body.append(f"<section id='y{year}'><h2>{year}</h2>" + (f"<p class=year>{' '.join(line)}</p>" if line else ""))
        for day, note_title, note in year_notes.get(year, []):  # what's known only by the year comes first
            body.append(f"<p class=note><b>{html.escape(note_title)}</b>{(': ' + html.escape(note)) if note else ''}</p>")
        if life.photos_year.get(year):
            count = life.photos_year[year]
            body.append(f"<p><span class=k>photos</span> {count:,} <span class=n>(dated only by the year in their name)</span></p>")
        if not in_year:
            body.append("</section>")
            continue
        body.append("<table>")
        for month in in_year:
            cells = []
            for day, note_title, note in sorted(life.notes.get(month, [])):
                cells.append(f"<p class=note><b>{html.escape(note_title)}</b>{(': ' + html.escape(note)) if note else ''} <span class=n>{when(day)}</span></p>")
            for trip in (trip for trip in life.trips if trip["start"][:7] == month):
                cells.append(f"<p class=trip><span class=k>trip</span> {trip_text(trip)}</p>")
            for day, text in sorted(life.work.get(month, [])):
                cells.append(f"<p><span class=k>work</span> {html.escape(text)} <span class=n>(LinkedIn)</span></p>")
            if life.places.get(month):
                cells.append(f"<p><span class=k>where</span> {listed(life.places[month], 4, 'photo')}</p>")
            elif life.photos.get(month):
                cells.append(f"<p><span class=k>photos</span> {life.photos[month]:,}</p>")
            if life.visits.get(month):
                cells.append(f"<p><span class=k>visited</span> {html.escape(', '.join(name for name, _ in life.visits[month].most_common(6)))}</p>")
            if life.talk.get(month):
                cells.append(f"<p><span class=k>with</span> {listed(life.talk[month], 3, 'message')}</p>")
            if life.photo_people.get(month):
                cells.append(f"<p><span class=k>in photos</span> {listed(life.photo_people[month], 4, 'photo')}</p>")
            if life.music.get(month):
                cells.append(f"<p><span class=k>listened</span> {names(life.music[month], 3)}</p>")
            if life.watched.get(month):
                cells.append(f"<p><span class=k>watched</span> {names(life.watched[month], 3)}</p>")
            for day, book, author in sorted(life.books.get(month, [])):
                cells.append(f"<p><span class=k>read</span> {html.escape(book)}{(' <span class=n>by ' + html.escape(author) + '</span>') if author else ''}</p>")
            if life.hours.get(month):
                spent = ", ".join(f"{html.escape(activity)} <span class=n>({hours:,.0f} h)</span>"
                                  for activity, hours in life.hours[month].most_common(4) if hours >= 0.5)
                if spent:
                    cells.append(f"<p><span class=k>time</span> {spent}</p>")
            if life.moods.get(month):
                cells.append(f"<p><span class=k>mood</span> {mood_line(life.moods[month])}</p>")
            if life.periods.get(month):
                cells.append(f"<p><span class=k>period</span> {', '.join(when(day) for day in sorted(life.periods[month]))}</p>")
            if life.diary.get(month):
                diary = sorted(life.diary[month])
                cells.append(folded("diary", [f"<li><span class=n>{when(day)}</span> {html.escape(text[:600])}</li>"
                                              for day, text in diary], diary[0][1]))
            if life.calendar.get(month):
                events = sorted(life.calendar[month])
                cells.append(folded("calendar", [f"<li><span class=n>{when(day)}</span> {html.escape(event[:200])}</li>"
                                                 for day, event in events], events[0][1]))
            if life.kept.get(month):
                kept = sorted(life.kept[month])
                cells.append(folded("kept notes", [f"<li><span class=n>{when(day)}</span> {html.escape(text[:300])}</li>"
                                                   for day, text in kept], kept[0][1]))
            if life.stories.get(month):
                stories = sorted(life.stories[month])
                captions = [f"<li><span class=n>{when(day)}</span> {html.escape(text[:300])}</li>" for day, text in stories if text]
                if captions:
                    first = next(text for _, text in stories if text)
                    cells.append(folded(f"stories ({len(stories)})", captions, first))
                else:
                    cells.append(f"<p><span class=k>stories</span> {len(stories)}</p>")
            if life.comments.get(month):
                comments = sorted(life.comments[month])
                cells.append(folded("comments", [f"<li><span class=n>{when(day)} · {html.escape(where)}</span> {html.escape(text[:400])}</li>"
                                                 for day, where, text in comments], comments[0][2]))
            if life.searches.get(month):
                searched = life.searches[month].most_common(40)
                cells.append(folded("searched", [f"<li>{html.escape(query)}{f' <span class=n>({count})</span>' if count > 1 else ''}</li>"
                                                 for query, count in searched], searched[0][0]))
            if life.asked.get(month):
                asked = sorted(life.asked[month])
                cells.append(folded("asked AI", [f"<li><span class=n>{when(day)}</span> {html.escape(title)}</li>"
                                                 for day, title in asked], asked[0][1]))
            if life.posts.get(month):
                posts = sorted(life.posts[month])
                cells.append(folded("posts", [f"<li><span class=n>{when(day)} · {where}</span> {html.escape(text[:600])}</li>"
                                              for day, where, text in posts], posts[0][2]))
            body.append(f"<tr><th>{MONTH_NAMES[int(month[5:]) - 1]}</th><td>{''.join(cells)}</td></tr>")
        body.append("</table></section>")
    if life.people:
        rows = []
        for person, card in sorted(life.people.items(), key=lambda item: -item[1]["messages"])[:60]:
            by_year = Counter()
            for month, counts in life.talk.items():
                if counts.get(person):
                    by_year[month[:4]] += counts[person]
            rows.append(f"<tr><td>{html.escape(person)}</td><td>{when(card['first'])}</td><td>{when(card['last'])}</td>"
                        f"<td class=r>{card['messages']:,}</td><td>{by_year.most_common(1)[0][0] if by_year else ''}</td></tr>")
        body.append("<section id='people'><h2>People</h2><table class=people><tr><th>who</th><th>first</th><th>last</th>"
                    "<th class=r>messages</th><th>busiest year</th></tr>" + "".join(rows) + "</table></section>")
    if life.trips:
        rows = "".join(f"<tr><td>{span(trip['start'], trip['end'])}</td><td>{html.escape(', '.join(trip['places'][:6]))}"
                       f"{(' <span class=n>· ' + html.escape(trip['note']) + '</span>') if trip['note'] else ''}</td>"
                       f"<td class=r>{trip['days']}</td><td class=r>{trip['photos']:,}</td></tr>"
                       for trip in reversed(life.trips))
        body.append("<section id='trips'><h2>Trips</h2><table class=people><tr><th>when</th><th>where</th><th class=r>days</th>"
                    "<th class=r>photos</th></tr>" + rows + "</table></section>")
    undated = life.skipped.get("photos without a date", 0)
    if undated:
        body.append(f"<section id='undated'><h2>Photos without a date</h2><p>{undated:,} photo{'s have' if undated != 1 else ' has'} no date "
                    "inside and none in the name. Scanned albums are often like this. Add the year to the file or folder name "
                    "(for example <i>1985 summer.jpg</i>, or a folder called <i>1985</i>) and make the page again.</p></section>")
    hints = next_steps(life)
    if hints:
        body.append("<section id='next'><h2>What to add next</h2><ul>" + "".join(f"<li>{hint}</li>" for hint in hints) + "</ul>"
                    "<p class=n>How to download each one: docs/download-your-data in the Lifekeeper repository.</p></section>")
    read, skipped = counted(life.read), counted(life.skipped)
    body.append(f"<footer><p>Read: {read or 'nothing yet'}.{(' Not read: ' + skipped + '.') if skipped else ''}</p>"
                "<p>Made with Lifekeeper. Nothing left this computer.</p></footer>")
    return PAGE.replace("{title}", html.escape(title)).replace("{body}", "\n".join(body))


PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
:root { --ink: #1d1d1f; --soft: #6b6b70; --line: #e3e3e6; --bg: #fbfbfa; --accent: #2f5d50; }
@media (prefers-color-scheme: dark) { :root { --ink: #e9e9ea; --soft: #9a9aa0; --line: #2c2c30; --bg: #141416; --accent: #8fc2b3; } }
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--ink); font: 16px/1.5 system-ui, -apple-system, "Segoe UI", sans-serif; }
main { max-width: 860px; margin: 0 auto; padding: 24px 16px 48px; }
h1 { font-size: 26px; margin: 0 0 4px; } h2 { font-size: 21px; margin: 32px 0 4px; }
.sum, .year, .n, footer { color: var(--soft); } .sum { margin: 0 0 12px; } .year { margin: 0 0 8px; }
nav a { color: var(--accent); margin-right: 10px; text-decoration: none; white-space: nowrap; }
table { width: 100%; border-collapse: collapse; }
th, td { text-align: left; vertical-align: top; padding: 8px 8px 8px 0; border-top: 1px solid var(--line); }
th { width: 120px; font-weight: 600; } td p { margin: 0 0 4px; }
.k { display: inline-block; min-width: 56px; color: var(--soft); font-size: 14px; }
.note b { color: var(--accent); } .r { text-align: right; } .people th { width: auto; }
details summary { cursor: pointer; } details ul { margin: 6px 0 0; padding-left: 18px; } details li { margin-bottom: 6px; }
footer { margin-top: 40px; font-size: 14px; border-top: 1px solid var(--line); padding-top: 12px; }
@media (max-width: 560px) { th { width: 84px; } }
</style></head><body><main>
{body}
</main></body></html>
"""


def main():
    parser = argparse.ArgumentParser(description="Turn your exports into one readable page about your life. Nothing leaves this computer.")
    parser.add_argument("exports", help="the folder with your exports (zips are read as they are)")
    parser.add_argument("--out", default="life.html", help="the page to write (default: life.html)")
    parser.add_argument("--json", help="also write what was found as JSON")
    parser.add_argument("--me", action="append", default=[], help="your name as it appears in chats (repeat for each spelling)")
    parser.add_argument("--title", default="My life at a glance")
    args = parser.parse_args()
    if not Path(args.exports).is_dir():
        sys.exit(f"Not a folder: {args.exports}")
    life = build(args.exports, args.me)
    page = render(life, args.title)
    if page is None:
        sys.exit("Nothing with a date was found. Check that the folder holds your exports (see docs/download-your-data).")
    Path(args.out).write_text(page, encoding="utf-8")
    if args.json:
        Path(args.json).write_text(json.dumps({
            "photos": life.photos, "places": life.places, "visits": life.visits, "messages_i_wrote": life.sent, "talk": life.talk, "people": life.people,
            "posts": life.posts, "notes": life.notes, "work": life.work, "music_minutes": life.music, "watched": life.watched, "books": life.books,
            "calendar": life.calendar, "kept": life.kept, "searches": life.searches, "asked_ai": life.asked,
            "hours": life.hours, "moods": life.moods, "diary": life.diary, "stories": life.stories, "comments": life.comments,
            "periods": life.periods, "read": life.read, "not_read": life.skipped}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Wrote {args.out}. Read: {counted(life.read)}" + (f". Not read: {counted(life.skipped)}" if life.skipped else ""))


if __name__ == "__main__":
    main()
