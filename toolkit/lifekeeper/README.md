# Lifekeeper

Lifekeeper reads a folder of exports and writes one HTML page: your years, month by month, with where you were, who you talked to, and what you listened to, watched, read and posted. Your own notes are shown first. It sends nothing anywhere.

## The app (Windows, Mac)

Download it from [Releases](https://github.com/claudiakitova/lifekeeper/releases), double-click it, choose your exports folder, and press "Make my page". The page is saved next to that folder as `my-life.html` and opens in your browser. After that you can ask questions in the same window.

The app is not signed. The first time, Windows says "Windows protected your PC" (choose **More info** → **Run anyway**), and a Mac asks you to right-click the app and choose **Open**.

## The script

Needs Python 3.10 or newer. Pillow is optional (`pip install pillow`); with it, Lifekeeper reads the dates and places stored inside photos.

```
python lifekeeper.py path/to/your/exports --out my-life.html
```

`python app.py` opens the same window as the app.

## What it reads

Put your exports in one folder, as they came. Zips can stay zipped. For step-by-step instructions see [Download your data](../../docs/download-your-data/), and for the full list of sources see [Sources](../../docs/sources.md).

| Export | What it gives |
|---|---|
| Photos (from the phone, Google Takeout, old folders) | Where you were, month by month |
| Google location history (Takeout, or the phone's Timeline export) | Places you visited |
| Telegram (`result.json`), WhatsApp (`.txt`), Messenger and Instagram (`message_1.json`) | Who you talked to, and when |
| Android texts (the "SMS Backup & Restore" app's `.xml`) | The same, by contact. Phone numbers are not shown on the page |
| Gmail (Takeout's `.mbox`, unzipped) | The people you wrote to (only mail you sent) |
| Facebook, Instagram and X posts | Your posts, with dates. Retweets are left out |
| Calendars (`.ics`), Google Keep | Appointments, trips, notes |
| LinkedIn (`Positions.csv`) | Jobs, marked as LinkedIn. Your own notes take priority |
| Spotify, YouTube, Netflix, Goodreads | What you listened to, watched and read |
| Google searches (Takeout's My Activity, as JSON) | What you looked up each month |
| ChatGPT (`conversations.json`) | What you asked about: titles and dates. If others used your account, some are theirs |
| A time tracker's CSV (aTimeLogger) | Hours by activity each month |
| A mood diary's CSV (Daylio, DailyBean) | Your mood each month, and what you wrote |
| Instagram stories, and your comments on Instagram and Facebook | What you shared and said, with dates |
| Flo's data download (JSON) | The days your periods started |
| `my_events.csv` | The main events, in your words |
| `my_homes.csv` | Where you lived, if Lifekeeper gets it wrong |

Lifekeeper looks for a photo's date in these places:
- the photo itself;
- Google's `.json` next to it;
- the export's own records (Instagram and Facebook remove dates from pictures but keep them in their JSON);
- the post number in an X archive's picture names;
- the date in the file name (`IMG_20190614…`, Telegram's `photo_12@15-07-2023…`).

A camera whose clock was never set writes Jan 1 of 1970, 1980 or 2000, or zeros. Lifekeeper doesn't trust those dates and takes the year from the folder's name.

These are left out, and counted at the end of the page:
- program and cache folders (`node_modules`, `thumbnails`, an archive viewer's `assets`)
- folders whose names start with a dot
- video thumbnails
- the made-up sample data in [`demo/exports`](../../demo/exports), unless you open that folder itself

This means you can point Lifekeeper at a big folder, even a whole copy of this project, without program images ending up on your page.

## Your own notes

Make a file called `my_events.csv` anywhere in the folder:

```
date,title,note
2019-09-02,Started an evening design course,Twice a week after work.
2021-03,Met Leo,
2024,Adopted a cat,
```

The date can be a day, a month or just a year. These lines are shown first in each month, and a line with only a year is shown with that year.

## Places and trips

Photos with a location, and Google location history, are named by the nearest town. The list of towns is from [GeoNames](https://www.geonames.org/) (CC BY 4.0): every place with more than 15,000 people. A spot far from any of them is shown as "near" a town, or as coordinates.

Lifekeeper then works out where home was each month: the town you were in across the most months of that year. Days somewhere else become trips, and the page lists them by month and in a Trips section at the end ("Lisbon, Sintra (Portugal), Aug 13–21, 2021, 9 days, 22 photos"). If a line in `my_events.csv` falls inside a trip, it becomes the trip's note.

If home is wrong (you moved a lot, or took few photos at home), say where you lived in `my_homes.csv`:

```
place,from,until
Berlin,2015,2019-08
Lisbon,2019-09,
```

Use the town name as the page shows it. An empty "until" means you still live there.

## If you have little data

Most people have photos, a chat app or two, and not much else. The page handles that:
- Scanned albums without dates show under a year if the year is in the file or folder name (`1985 summer.jpg`, a folder called `1985`). The rest are counted at the end, with instructions for dating them.
- Group chats show as groups, not as one person.
- Years with little data don't list their empty months.
- The page ends with the three sources that would add the most to it.

## Options

- `--me "Your Name"` tells it which messages are yours. It usually works this out (Telegram knows; in other chats, the person in every chat is you), but repeat `--me` for each spelling if it gets it wrong.
- `--json life.json` also saves what it found, for your own scripts.
- `--title "Anna's life"` changes the page title.

## People in your photos

An add-on finds the faces in your photos, groups the same person across photos, and lets you name each group once. Your page then shows who is in your photos each month ("in photos: Anna (12 photos)"), and Ask knows it too.

It runs on your computer with OpenCV's YuNet and SFace face models. They are downloaded once (about 37 MB) from OpenCV's own repository and checked against known fingerprints. No photo leaves your computer.

In the app: make your page, press **Find faces**, type a name under each group you know, and press **Update my page with these names**. Groups of strangers can be left out with **Not someone I know**.

With the script (needs `pip install "lifekeeper[faces]"`):

```
lifekeeper-faces scan path/to/your/exports         # find faces; can be stopped and resumed
lifekeeper-faces people path/to/your/exports       # a page with each group and its number
lifekeeper-faces name path/to/your/exports 3 Anna  # name group 3
lifekeeper-faces hide path/to/your/exports 7       # leave out group 7
```

What it finds and the names you give are kept in `lifekeeper-faces.sqlite3`, next to your exports folder (never inside it). Names belong to faces, so they stay when you scan new photos and the groups change. If one person ends up in two groups (as a child and as an adult, say), give both the same name and they become one person.

## Ask a question

Ask a question about your life and get an answer from your own records, with the records it used. The app has a box for it, with the same three choices as below. With the script:

```
python ask.py path/to/your/exports "When did I meet Leo?"
```

It reads the same folder of exports as the page and needs nothing else installed.

Three ways to use it:

### No AI

```
python ask.py path/to/your/exports "When did I meet Leo?"
```

Ask searches your records and shows the ones that match. No model is used and nothing leaves your computer.

```
Records that match (no AI was used):
  Mar 14, 2021 · my note · Met Leo: At Anna's birthday party.
  Mar 14, 2021 · person · Leo Hart: first message Mar 14, 2021, last message Aug 28, 2025, 1,122 messages
```

### A model on your own computer

Install [Ollama](https://ollama.com), get a model (`ollama pull gemma3`), and add `--ollama` with the model's name:

```
python ask.py path/to/your/exports "When did I meet Leo?" --ollama gemma3
```

The model writes a short answer from the records that were found. Nothing leaves your computer.

```
You met Leo on Mar 14, 2021, at Anna's birthday party [1].

From your records:
[1] Mar 14, 2021 · my note · Met Leo: At Anna's birthday party.
```

### Google Gemini

Get a free key at https://aistudio.google.com/apikey, put it in the `GEMINI_API_KEY` environment variable, and add `--gemini`. In the app, paste it into the box instead:

```
python ask.py path/to/your/exports "When did I meet Leo?" --gemini
```

This sends your question and the matching records (30 at most, one line each) to Google. Ask tells you how many each time. On Gemini's free tier, Google may use what you send to improve its models. Your files, photos and message texts are not sent.

To ask several questions, leave the question out and type them one per line.

If Google is busy, Ask tries twice more and then asks you to try again in a minute.

### How answers are checked

A model can invent things, so Ask doesn't show an answer it can't check:

- The search is done by Ask, on your computer. The model only writes from the records it is given.
- Every sentence has to cite a record. A sentence that cites nothing is left out.
- A sentence with a date or number that isn't in the records it cites is left out.
- If nothing is left, Ask says so and shows the matching records instead.
- Your own notes (`my_events.csv`) win when records disagree. LinkedIn loses to everything else.
- The same question gets the same answer where the model allows it (temperature 0, fixed seed).

These checks catch invented facts, not every mistake. A small local model can still combine real numbers into a wrong claim, so read the records listed under each answer. Larger models make fewer mistakes.

### What it knows

It knows what the page shows: your own notes, your posts, stories and comments, diary lines, period start days, calendar events, Keep notes, books, searches, AI chat titles, hours and moods by month, LinkedIn jobs, who you exchanged messages with and how many, where your photos were taken, places from your location history, and what you listened to and watched.

It doesn't read the text of your messages, documents or scans, so it can't answer "what did Anna say about the trip?". It can answer "when did I first talk to Anna?" and "who did I talk to most in 2020?".

### Options

- `--me "Your Name"` tells it which messages are yours, as for the page.
- `--records 50` searches out more records for each question (default: 30).
- `--gemini-model NAME` chooses another Gemini model.

## What it doesn't do

It doesn't read the text of documents, scans or messages, transcribe voice messages, or describe photos. Those are step 4 of [the approach](../../docs/approach.md).
