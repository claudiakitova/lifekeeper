# The approach

These are the ten steps I followed to build an archive of 20 years of my life, and the things that went wrong along the way.

## 1. Keep the originals untouched

Copy your exports into one folder (`data/`). Don't edit, rename or "clean" anything inside it. Everything else (titles, summaries, the timeline, search indexes) is made from these files and can be rebuilt at any time, so if something breaks you rebuild it and the source is still there.

## 2. Collect what you already have

You don't have to have kept a diary. Photos, chats, social media, Google Takeout, bank statements and health apps already cover years. [Start small](start-small.md) lists them in order of usefulness, and [Download your data](download-your-data/) has the steps.

## 3. Catalog everything

Give every file an entry in one catalog (a small database is enough): where it is, its type, its date, its size and a fingerprint of its contents. With a catalog, every later fact can point back to the file it came from, duplicates show up (the same bytes twice, or a Word file and its PDF), and you notice when something goes missing.

Process every folder. If you want to skip some as unimportant, list them with file counts first and decide on purpose. A skipped folder can turn out to hold the one scan you need.

## 4. Read what isn't text

Scans, photos of documents, voice messages and photos can't be searched until something reads them:

- Text in scans and photos of documents: OCR. Tesseract and EasyOCR run locally.
- Voice messages and recordings: transcription. Whisper runs locally if you have a graphics card.
- Photos: dates and places from the photo's own data (EXIF), and descriptions from a vision model, either local or a service you've chosen.

Machine reading makes mistakes. Names come out wrong, dates get guessed, and a model describing a photo invents details. Treat every machine reading as a draft. For medical, legal and money documents, check the reading against the original line by line.

## 5. Organize it into a few views

Files are hard to browse. These views are easier:

- a timeline: the events that mattered, oldest first, each with its sources
- people: one card per person, with every name they appear under (nicknames, spellings, accounts)
- places: homes and trips, from photo locations and travel records
- work: your real career, kept apart from your CV (see step 6)
- words: your diary, messages, posts and notes, searchable together
- health and money: lab results, documents, income by month, in plain units

Build each view from the catalog so it can be rebuilt.

## 6. Your account wins

Sources disagree. Decide once which source wins, and write the order down. The order I use:

1. What you say yourself
2. Original documents
3. Your own posts (written for others, usually careful)
4. Your diary
5. Your messages
6. Your AI chats (only the ones you wrote)
7. Your CV and LinkedIn

A CV comes last because it's written to sell you: titles get bigger, team sizes get rounder, gaps disappear. Keep a short "my real career" file in your own words and let it win over every CV.

## 7. Corrections live in their own layer

When you fix a title, merge two duplicate events or rename a person, write the fix into a separate corrections file, keyed to the original. Don't edit the derived data by hand. That way, re-importing an export or rebuilding the timeline applies your corrections again. If you edit the derived data directly, the next rebuild undoes your fix.

## 8. Review it page by page

Read every page the way you would on a bad day. [Readable on a hard day](readable-on-a-hard-day.md) has the checklist. When you find a mistake, fix it everywhere it appears, and record the fix as in step 7.

## 9. Ask, with sources

The most useful view is a question box: "When did I move to this city?", "What did I do in 2019?", "Who is Anna to me?" These rules keep the answers true:

- Answers come only from your records. The assistant searches first, then answers.
- Every sentence cites its sources. A paragraph that cites nothing isn't shown. Small local models invent whole stories, and this rule stops them.
- Check the numbers. Drop any sentence whose year or number isn't in the records it cites. That is where models invent the most.
- Give the model your checked facts first. Start every question from your timeline and your own career account, so raw search results can't override facts you've already confirmed.
- With a small model, do the searching for it. Small local models plan searches badly but write well from evidence. Run the searches yourself (timeline, people, search by meaning) and let the model only write.
- The same question should get the same answer. Use a low temperature and a fixed seed, and keep earlier answers until the data changes.

The [tool in this repository](../toolkit/lifekeeper/#ask-a-question) follows these rules for the records its page shows.

## 10. Make it last

- Back up in more than one place: an encrypted cloud copy that keeps old versions, plus a drive at home. See [Backup](backup.md).
- Test a restore. Until you've restored from a backup once, you don't know that it works.
- Use open formats: JSON, CSV, SQLite, PDF, plain text.
- Write down how to run everything, so you or someone you trust can do it later.

## What went wrong

Each of these cost me time. Check your own data for them.

- Other people's words. Telegram's "Saved Messages", forwarded posts and pasted texts are mostly other people's writing. Don't count them as your opinions or memories.
- Shared accounts. If family used your AI chat or streaming account, part of that history is theirs.
- Model misreadings. OCR and vision models turn your own name into strangers' names, misread places and guess dates. Keep a list of known misreadings and fix them everywhere at once.
- Broken text in Meta exports. Facebook and Instagram exports store text as UTF-8 read as Latin-1 ("ÐŸÑ€Ð¸Ð²ÐµÑ‚" instead of "Привет"). Re-encode it before reading.
- File dates. A file's date is when it was copied, not when the event happened. Use dates inside the content first, then photo data, and file dates last.
- Duplicates. Exports overlap: the same photo in three folders, a chat exported twice. Find them by content fingerprint and merge them on purpose.
- Other people's events. Your timeline is for your events, not your brother's, even when his fill your chats.
- Names in two alphabets. If you write in more than one language, search and match names in both ("Анна" and "Anna").
