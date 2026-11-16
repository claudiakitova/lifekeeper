"""Where you've been: photo and phone locations named as towns, grouped into visits, and visits away from home into trips.

Towns come from GeoNames (geonames.org, CC BY 4.0): every place with more than 15,000 people, in cities.tsv.gz next to
this file. A location takes the name of the town that best explains it: a big city 15 km away beats a small suburb 3 km
away, but a real town of its own isn't swallowed by a city 30 km off.

Home is worked out for each month from where most of your located days are around it. You can say where you lived in
my_homes.csv (place,from,until), and that wins.
"""
import csv
import gzip
import io
import math
from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path

GAP_DAYS = 4          # more days than this between two days in one town starts a new visit
SEARCH_KM = 60        # towns farther than this don't name a location ("near ..." up to NEAR_KM)
NEAR_KM = 150
_towns, _grid = [], defaultdict(list)


def load():
    if _towns:
        return
    path = Path(__file__).with_name("cities.tsv.gz")
    if not path.is_file():
        return
    for line in gzip.decompress(path.read_bytes()).decode("utf-8").splitlines():
        name, lat, lon, country, people = line.split("\t")
        town = (name, float(lat), float(lon), country, int(people))
        _grid[(math.floor(town[1]), math.floor(town[2]))].append(len(_towns))
        _towns.append(town)


def distance_km(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2
    return 12742 * math.asin(math.sqrt(min(1.0, a)))


def town_at(lat, lon):
    """(town, country, km) for a location, or None if no town is within NEAR_KM (or the list is missing)."""
    load()
    if not _towns:
        return None
    reach = 2 if abs(lat) < 60 else 4  # degrees of longitude shrink toward the poles
    best, nearest = None, None
    for dlat in (-1, 0, 1, 2) if NEAR_KM > 111 else (-1, 0, 1):
        for dlon in range(-reach, reach + 1):
            for index in _grid.get((math.floor(lat) + dlat, math.floor(lon) + dlon), ()):
                name, tlat, tlon, country, people = _towns[index]
                km = distance_km(lat, lon, tlat, tlon)
                if nearest is None or km < nearest[2]:
                    nearest = (name, country, km)
                if km <= SEARCH_KM:
                    pull = people / (km + 2) ** 2  # the town that best explains the spot: big and close
                    if best is None or pull > best[0]:
                        best = (pull, name, country, km)
    if best:
        return best[1], best[2], best[3]
    if nearest and nearest[2] <= NEAR_KM:
        return nearest
    return None


def place_label(lat, lon):
    """What the page calls a location: "Lisbon", "near Évora", or coordinates far from any town."""
    found = town_at(lat, lon)
    if found is None:
        return f"{lat:.1f}°, {lon:.1f}°"
    name, _, km = found
    return name if km <= SEARCH_KM else f"near {name}"


def country_of(place):
    load()
    for name, _, _, country, _ in _towns:
        if name == place:
            return country
    return ""


def visits(days_by_place):
    """{place: {day: photos}} → [{place, start, end, days, photos}]: one place's days, split where more than GAP_DAYS
    pass, or where every day in between was spent only somewhere else."""
    places_on = defaultdict(set)
    for place, by_day in days_by_place.items():
        for day in by_day:
            places_on[day].add(place)

    def away_between(place, first, last):
        day = date.fromisoformat(first)
        while (day := day + timedelta(days=1)) < date.fromisoformat(last):
            there = places_on.get(day.isoformat(), set())
            if there and place not in there:
                return True
        return False

    result = []
    for place, by_day in days_by_place.items():
        ordered = sorted(by_day)
        start = previous = ordered[0]
        photos = 0
        for day in ordered + [None]:
            if day is not None and day == start:
                photos += by_day[day]
                continue
            if day is not None and (date.fromisoformat(day) - date.fromisoformat(previous)).days <= GAP_DAYS \
                    and not away_between(place, previous, day):
                photos += by_day[day]
                previous = day
                continue
            result.append({"place": place, "start": start, "end": previous, "photos": photos,
                           "days": (date.fromisoformat(previous) - date.fromisoformat(start)).days + 1})
            if day is not None:
                start = previous = day
                photos = by_day[day]
    return sorted(result, key=lambda visit: visit["start"])


def homes(days_by_place, told=()):
    """month → home town. What you wrote in my_homes.csv wins. Otherwise home is the town you were in across the most
    months of the year around it (a two-week trip has many days but only one month), then the one with more days."""
    per_month = defaultdict(Counter)
    for place, by_day in days_by_place.items():
        for day in by_day:
            per_month[day[:7]][place] += 1
    months = sorted(per_month)
    result = {}
    for month in months:
        year, number = int(month[:4]), int(month[5:7])
        present, days = Counter(), Counter()
        for shift in range(-6, 7):
            y, m = divmod(number - 1 + shift, 12)
            seen = per_month.get(f"{year + y}-{m + 1:02d}", {})
            present.update(seen.keys())
            days.update(seen)
        if present:
            result[month] = max(present, key=lambda place: (present[place], days[place]))
    for place, start, end in told:
        last = end[:7] if len(end) >= 7 else (end + "-12" if end else "9999-12")
        for month in months:
            if start[:7] <= month <= last:
                result[month] = place
    return result


def trips(days_by_place, told_homes=(), notes=()):
    """Visits away from home, joined into trips when one starts within GAP_DAYS of the last one's end.
    notes: (day, text) of your own; one that falls inside a trip describes it."""
    home = homes(days_by_place, told_homes)
    away = [visit for visit in visits(days_by_place) if home.get(visit["start"][:7]) != visit["place"]]
    journeys = []
    for visit in away:
        if journeys and (date.fromisoformat(visit["start"]) - date.fromisoformat(journeys[-1]["end"])).days <= GAP_DAYS:
            journey = journeys[-1]
            journey["end"] = max(journey["end"], visit["end"])
            journey["visits"].append(visit)
        else:
            journeys.append({"start": visit["start"], "end": visit["end"], "visits": [visit]})
    for journey in journeys:
        places = list(dict.fromkeys(visit["place"] for visit in journey["visits"]))
        countries = list(dict.fromkeys(filter(None, (country_of(place) for place in places))))
        journey.update(places=places, countries=countries, photos=sum(visit["photos"] for visit in journey["visits"]),
                       days=(date.fromisoformat(journey["end"]) - date.fromisoformat(journey["start"])).days + 1,
                       note=next((text for day, text in notes if len(day) == 10 and journey["start"] <= day <= journey["end"]), ""))
    return journeys


def read_homes(text):
    """my_homes.csv: place,from,until (until can be empty: you still live there). Dates as 2019, 2019-05 or 2019-05-01."""
    told = []
    for row in csv.DictReader(io.StringIO(text)):
        place, start, end = ((row.get(key) or "").strip() for key in ("place", "from", "until"))
        if place and start:
            told.append((place, start, end))
    return told
