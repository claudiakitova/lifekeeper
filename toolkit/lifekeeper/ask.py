#!/usr/bin/env python3
"""Ask: answer a question about your life from your own records, and show the records it used.

    python ask.py EXPORTS "When did I meet Leo?"                   # shows the matching records: no AI, nothing leaves this computer
    python ask.py EXPORTS "When did I meet Leo?" --ollama gemma3   # a written answer from a model running on this computer
    python ask.py EXPORTS "When did I meet Leo?" --gemini          # a written answer from Google Gemini (key in GEMINI_API_KEY)
    python ask.py EXPORTS --gemini                                 # keep asking, one question per line

It reads the same exports as Lifekeeper. The search is done here, on this computer. A model only writes the answer from
the records that were found, and every sentence has to point to a record: a sentence with no record behind it, or with a date
or number that its records don't contain, is left out. Standard library only.
"""
import argparse
import json
import math
import os
import re
import sys
import time
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path

try:  # installed with pip: part of the lifekeeper package
    from . import lifekeeper
except ImportError:  # run as a script from this folder
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import lifekeeper  # noqa: E402

GEMINI_MODEL = "gemini-3.6-flash"
NO_ANSWER = "The records don't say."

SYSTEM = (
    "You answer a question about a person's life using only the numbered records below.\n"
    "- Use nothing that is not in the records.\n"
    "- End every sentence with the numbers of the records it relies on, in square brackets, like [3] or [2][5].\n"
    "- Copy dates and numbers exactly as the records give them. Do not calculate, count or estimate.\n"
    "- Records of the kind \"my note\" are the person's own account. They win when records disagree. "
    "LinkedIn is a sales version and loses to everything else. Records of the kinds \"mood\" and \"diary\" say how "
    "the person felt; \"messages\" give how many messages they exchanged with each person that month.\n"
    f"- If the records do not answer the question, reply with exactly: {NO_ANSWER}\n"
    "- Address the person as \"you\". Be brief: one to four sentences. Answer in the language of the question."
)

# The person's own account comes first when records are otherwise equal.
KINDS = ["my note", "diary", "Facebook post", "Instagram post", "X post", "Instagram story", "comment", "calendar", "LinkedIn", "book read", "Keep note", "AI chat",
         "person", "messages", "photos", "location history", "period", "mood", "time", "searches", "music", "watched"]


# ---------- records ----------

def top(counter, limit, unit=""):
    return ", ".join(f"{name} ({count:,}{unit})" for name, count in counter.most_common(limit))


def records(life):
    """Everything Lifekeeper found, as dated one-line records: {"day", "kind", "text"}."""
    out = []

    def add(day, kind, text):
        text = " ".join(str(text).split())
        if day and text:
            out.append({"day": day, "kind": kind, "text": text})

    for items in life.notes.values():
        for day, title, note in items:
            add(day, "my note", f"{title}: {note}" if note else title)
    for items in life.posts.values():
        for day, where, text in items:
            add(day, f"{where} post", text)
    for items in life.work.values():
        for day, text in items:
            add(day, "LinkedIn", text)
    for items in life.calendar.values():
        for day, title in items:
            add(day, "calendar", title)
    for items in life.kept.values():
        for day, text in items:
            add(day, "Keep note", text)
    for items in life.books.values():
        for day, title, author in items:
            add(day, "book read", f"{title} by {author}" if author else title)
    for items in life.diary.values():
        for day, text in items:
            add(day, "diary", text)
    for items in life.stories.values():
        for day, caption in items:
            if caption:
                add(day, "Instagram story", caption)
    for items in life.comments.values():
        for day, where, text in items:
            add(day, "comment", f"{where}: {text}")
    for items in life.periods.values():
        for day in items:
            add(day, "period", "Period started")
    for items in life.asked.values():
        for day, title in items:
            add(day, "AI chat", title)
    for month, queries in life.searches.items():
        add(month, "searches", "Searched for " + "; ".join(query for query, _ in queries.most_common(12)))
    for month, activities in life.hours.items():
        add(month, "time", "Time spent: " + ", ".join(f"{name} ({hours:,.0f} h)" for name, hours in activities.most_common(6) if hours >= 0.5))
    for month, days in life.moods.items():
        add(month, "mood", re.sub(r"<[^>]+>", "", "Mood " + lifekeeper.mood_line(days)))
    for person, card in life.people.items():
        add(card["first"], "person", f"{person}: first message {lifekeeper.when(card['first'])}, last message "
                                     f"{lifekeeper.when(card['last'])}, {card['messages']:,} messages")
    for month, people in life.talk.items():
        add(month, "messages", "Messages with " + top(people, 6))
    for month, count in life.photos.items():
        places = life.places.get(month)
        add(month, "photos", f"{count:,} photo{'' if count == 1 else 's'}" + (", taken in " + top(places, 5) if places else ""))
    for year, count in life.photos_year.items():
        add(str(year), "photos", f"{count:,} photo{'' if count == 1 else 's'} dated only by the year in their name")
    for month, places in life.visits.items():
        add(month, "location history", "Visited " + top(places, 8))
    for month, artists in life.music.items():
        add(month, "music", "Listened most to " + ", ".join(name for name, _ in artists.most_common(4)))
    for month, shows in life.watched.items():
        add(month, "watched", "Watched " + ", ".join(name for name, _ in shows.most_common(5)))
    out.sort(key=lambda record: (record["day"], KINDS.index(record["kind"]) if record["kind"] in KINDS else len(KINDS)))
    return out


def line(record):
    return f"{lifekeeper.when(record['day'])} · {record['kind']} · {record['text']}"


# ---------- search ----------

WORD = re.compile(r"[^\W_]+")
STOP = set("""a an the and or but of in on at to for with by from as is are was were be been am do did does have has had i me my
mine you your we our us it its this that these those what when where who whom whose which how why about any ever there then than
so not no yes if into over out up down all some more most much many can could would should will shall
я мне меня мой моя моё мои ты вы он она оно мы они что когда где кто как почему зачем и или но в во на с со по о об к ко у за из
от до для это этот эта эти был была было были ли же не да бы то""".split())
SAME = {"met": "meet", "went": "go", "gone": "go", "bought": "buy", "began": "begin", "got": "get", "left": "leave", "saw": "see",
        "seen": "see", "took": "take", "wrote": "write", "read": "read", "ate": "eat", "ran": "run", "flew": "fly", "made": "make"}
MONTHS = {name: number for number, names in enumerate(
    ["january jan январь января", "february feb февраль февраля", "march mar март марта", "april apr апрель апреля", "may май мая",
     "june jun июнь июня", "july jul июль июля", "august aug август августа", "september sep sept сентябрь сентября",
     "october oct октябрь октября", "november nov ноябрь ноября", "december dec декабрь декабря"], 1) for name in names.split()}


def stem(word):
    """A rough base form, so "moved", "moves" and "moving" find "move", and Russian endings matter less."""
    word = SAME.get(word, word)
    if not word.isascii():
        return word[:5] if len(word) > 5 else word
    if len(word) > 4:
        for ending in ("ing", "ed", "es"):
            if word.endswith(ending) and len(word) - len(ending) >= 3:
                word = word[:-len(ending)]
                break
        else:
            if word.endswith("s") and not word.endswith("ss"):
                word = word[:-1]
    if len(word) > 3 and word.endswith("e"):
        word = word[:-1]
    return word


FEELINGS = {stem(word) for word in """feel felt feeling feelings mood moods happy happier sad sadder upset anxious worried stressed
calm tired lonely angry glad proud scared excited nervous настроение чувствовала чувствовал чувство грустно радостно""".split()}


TOPICS = {stem(word): topic for group, topic in (  # a question's everyday words → the words its records use
    ("talk talked talking chat chatted text texted message messaged wrote write friend friends", ("messag", "person")),
    ("listen listened listening music song songs band bands", ("listen", "music")),
    ("watch watched watching show shows series film films movie movies", ("watch",)),
    ("work worked working job jobs hours busy", ("tim", "work", "linkedin")),
    ("search searched google googled", ("search",)),
    ("photo photos picture pictures travel travelled traveled trip trips", ("photo", "visit", "location")),
) for word in group.split()}


def words(text):
    return [stem(word) for word in (found.casefold() for found in WORD.findall(text)) if word not in STOP and not word.isdigit()]


def dates_in(question):
    lowered = question.casefold()
    years = set(re.findall(r"\b(?:19|20)\d{2}\b", lowered))
    months = {MONTHS[word] for word in WORD.findall(lowered) if word in MONTHS and word != "may"}
    if re.search(r"\b(?:in|of|last|this|next|since|until|before|after)\s+may\b", lowered):
        months.add(5)
    return years, months


def search(found, question, limit=30):
    """The records that best match the question: by its words, and by any year or month it names."""
    years, months = dates_in(question)
    asked = [word for word in words(question) if word not in {stem(name) for name in MONTHS}]
    if any(word in FEELINGS for word in asked):  # "how did I feel" is answered by moods and diaries
        asked += ["mood", "diary"]
    asked += [extra for word in list(asked) for extra in TOPICS.get(word, ())]  # everyday words find the records' own words
    texts = [words(f"{record['kind']} {record['text']}") for record in found]
    in_how_many = Counter(word for text in texts for word in set(text))
    average = (sum(map(len, texts)) / len(texts)) if texts else 1
    scored = []
    for record, text in zip(found, texts):
        counts = Counter(text)
        score = 0.0
        for word in asked:
            if counts[word]:
                rarity = math.log(1 + (len(found) - in_how_many[word] + 0.5) / (in_how_many[word] + 0.5))
                score += rarity * counts[word] * 2.2 / (counts[word] + 1.2 * (0.25 + 0.75 * len(text) / average))
        dated = bool(years or months)
        in_year = record["day"][:4] in years
        in_month = len(record["day"]) >= 7 and int(record["day"][5:7]) in months
        on_date = dated and (not years or in_year) and (not months or in_month)
        if score > 0:  # the question's words come first; a matching date lifts them, a wrong date sinks them
            score = score * (1.0 if not dated or on_date else 0.2) + (5.0 if on_date else 0.0)
        elif on_date:  # only the date matches: these fill the rest, the person's own notes first
            score = 1.0
        if score > 0:
            kind = KINDS.index(record["kind"]) if record["kind"] in KINDS else len(KINDS)
            scored.append((-score, kind, record["day"], len(scored), record))
    scored.sort(key=lambda item: item[:4])
    return sorted((item[4] for item in scored[:limit]), key=lambda record: record["day"])


# ---------- models ----------

def gemini_request(system, prompt, key, model=GEMINI_MODEL):
    body = {"systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0, "seed": 1}}
    return urllib.request.Request(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                                  data=json.dumps(body).encode("utf-8"),
                                  headers={"Content-Type": "application/json", "x-goog-api-key": key})


def gemini(system, prompt, key, model=GEMINI_MODEL, waits=(3, 8)):
    for wait in (*waits, None):  # Google answers 500 or 503 when it's busy: try again a little later
        try:
            with urllib.request.urlopen(gemini_request(system, prompt, key, model), timeout=120) as response:
                data = json.load(response)
            break
        except urllib.error.HTTPError as error:
            if error.code in (500, 503) and wait is not None:
                time.sleep(wait)
                continue
            gemini_error(error, model)
        except urllib.error.URLError as error:
            raise RuntimeError(f"Couldn't reach Gemini: {error.reason}") from None
    candidates = data.get("candidates") or [{}]
    return "".join(part.get("text", "") for part in (candidates[0].get("content") or {}).get("parts", []))


def gemini_error(error, model):
    """Google's error, in plain words."""
    detail = error.read().decode("utf-8", "replace")
    if "API key not valid" in detail or "API_KEY_INVALID" in detail:
        raise RuntimeError("That Gemini API key didn't work. Check GEMINI_API_KEY.") from None
    if error.code == 429:
        raise RuntimeError("Gemini's limit was reached. Wait a minute and try again.") from None
    if error.code == 404:
        raise RuntimeError(f"Gemini doesn't know the model \"{model}\". Choose another with --gemini-model.") from None
    if error.code in (500, 503):
        raise RuntimeError("Gemini is busy right now. Try again in a minute.") from None
    raise RuntimeError(f"Gemini returned an error ({error.code}).") from None


def ollama(system, prompt, model, host="http://localhost:11434"):
    body = {"model": model, "stream": False, "options": {"temperature": 0, "seed": 1},
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}]}
    request = urllib.request.Request(f"{host}/api/chat", data=json.dumps(body).encode("utf-8"), headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=600) as response:
            return json.load(response).get("message", {}).get("content", "")
    except urllib.error.HTTPError as error:
        if error.code == 404:
            raise RuntimeError(f"Ollama doesn't have the model \"{model}\". Get it with: ollama pull {model}") from None
        try:
            detail = json.loads(error.read().decode("utf-8", "replace")).get("error", "")
        except ValueError:
            detail = ""
        raise RuntimeError(f"Ollama returned an error ({error.code})" + (f": {detail[:300]}" if detail else ".")) from None
    except urllib.error.URLError:
        raise RuntimeError("Ollama isn't running on this computer. Start it, or install it from ollama.com.") from None


# ---------- answers ----------

SHORT_WORDS = {"st", "mr", "mrs", "ms", "dr", "vs", "etc", "jan", "feb", "mar", "apr", "jun", "jul", "aug", "sep", "sept", "oct", "nov", "dec"}


def sentences(text):
    text = re.sub(r"([.!?])\s*((?:\[\d+\])+)", r" \2\1", " ".join(text.split()))  # "party. [2]" → "party [2]."
    out, start = [], 0
    for match in re.finditer(r"[.!?]\s+", text):
        before = text[start:match.start()]
        last = re.findall(r"[^\W\d_]+$", before)
        if last and (last[0].casefold() in SHORT_WORDS or len(last[0]) == 1):
            continue
        out.append(text[start:match.end()].strip())
        start = match.end()
    if text[start:].strip():
        out.append(text[start:].strip())
    return out


def numbers(text):
    return {int(found.replace(",", "")) for found in re.findall(r"\d[\d,]*", text) if found.replace(",", "")}


def checked(answer, chosen):
    """Keep only the sentences that cite records and whose dates and numbers are in those records.
    Returns the answer with its citations renumbered from 1, and the records it used, in that order."""
    kept, used = [], []
    for sentence in sentences(answer):
        cited = [int(number) for number in re.findall(r"\[(\d+)\]", sentence)]
        cited = [number for number in cited if 1 <= number <= len(chosen)]
        if not cited:
            continue
        evidence = " ".join(line(chosen[number - 1]) + " " + chosen[number - 1]["day"].replace("-", " ") for number in cited)
        if numbers(re.sub(r"\[\d+\]", "", sentence)) - numbers(evidence):
            continue
        for number in cited:
            if number not in used:
                used.append(number)
        kept.append(re.sub(r"\[(\d+)\]", lambda m: f"[{used.index(int(m.group(1))) + 1}]" if int(m.group(1)) in used else "", sentence))
    return " ".join(kept), [chosen[number - 1] for number in used]


def answer(found, question, write=None, limit=30, note=None):
    """The answer as text. `write(system, prompt)` is the model; without one, the matching records are shown as they are."""
    chosen = search(found, question, limit)
    if not chosen:
        return "Nothing in your records matches that question."
    listed = "\n".join(f"  {line(record)}" for record in chosen)
    if write is None:
        return f"Records that match (no AI was used):\n{listed}"
    if note:
        note(len(chosen))
    prompt = "Records:\n" + "\n".join(f"[{number}] {line(record)}" for number, record in enumerate(chosen, 1)) + f"\n\nQuestion: {question}"
    written = write(SYSTEM, prompt).strip()
    closest = "\n".join(f"  {line(record)}" for record in search(found, question, 10))
    if written.rstrip(".").casefold() == NO_ANSWER.rstrip(".").casefold():
        return f"Your records don't say. The closest ones:\n{closest}"
    text, sources = checked(written, chosen)
    if not text:
        return f"The model's answer couldn't be checked against your records, so it isn't shown. The records that match:\n{closest}"
    return text + "\n\nFrom your records:\n" + "\n".join(f"[{number}] {line(record)}" for number, record in enumerate(sources, 1))


def main():
    parser = argparse.ArgumentParser(description="Ask a question about your life and get an answer from your own records, with the records it used.")
    parser.add_argument("exports", help="the folder with your exports (the same one Lifekeeper reads)")
    parser.add_argument("question", nargs="?", help="your question; leave it out to ask several, one per line")
    parser.add_argument("--ollama", metavar="MODEL", help="write the answer with a model on this computer, through Ollama (nothing leaves the computer)")
    parser.add_argument("--gemini", action="store_true", help="write the answer with Google Gemini: the question and the matching records are sent to Google")
    parser.add_argument("--gemini-model", default=GEMINI_MODEL, help=f"which Gemini model (default: {GEMINI_MODEL})")
    parser.add_argument("--me", action="append", default=[], help="your name as it appears in chats (repeat for each spelling)")
    parser.add_argument("--records", type=int, default=30, help="how many records to search out for each question (default: 30)")
    args = parser.parse_args()
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    if not Path(args.exports).is_dir():
        sys.exit(f"Not a folder: {args.exports}")
    if args.ollama and args.gemini:
        sys.exit("Choose one: --ollama or --gemini.")

    write = note = None
    if args.gemini:
        key = os.environ.get("GEMINI_API_KEY", "").strip()
        if not key:
            sys.exit("Put your Gemini API key in GEMINI_API_KEY first. A free key: https://aistudio.google.com/apikey")
        write = lambda system, prompt: gemini(system, prompt, key, args.gemini_model)  # noqa: E731
        note = lambda count: print(f"(Sending your question and {count} records to Google Gemini.)", file=sys.stderr)  # noqa: E731
    elif args.ollama:
        write = lambda system, prompt: ollama(system, prompt, args.ollama)  # noqa: E731

    found = records(lifekeeper.build(args.exports, args.me))
    if not found:
        sys.exit("Nothing with a date was found. Check that the folder holds your exports (see docs/download-your-data).")

    def reply(question):
        try:
            print(answer(found, question, write, args.records, note))
        except RuntimeError as error:
            print(error, file=sys.stderr)
            return False
        return True

    if args.question:
        sys.exit(0 if reply(args.question) else 1)
    print(f"{len(found):,} records read. Ask a question, or press Enter to stop.")
    while True:
        try:
            question = input("\nAsk: ").strip()
        except EOFError:
            break
        if not question:
            break
        reply(question)


if __name__ == "__main__":
    main()
