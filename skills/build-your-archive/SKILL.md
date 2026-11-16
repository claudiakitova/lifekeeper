---
name: build-your-archive
description: Build a personal life archive with the person, step by step, from the exports they already have (photos, chats, Google Takeout, social media, documents) to a catalog, a timeline, people, places, a corrections layer and an encrypted backup. Use when they say "let's build my archive", "I downloaded my data, what now", "add this export", or ask what's next.
---

# Building a life archive

The person wants one place that holds their life, that they can trust and read on a hard day. The approach is in
`docs/approach.md` of the Lifekeeper repository; this skill is how to carry it out with them. Read their `facts.md` and
`decisions.md` (templates in `../review-your-archive/`) before every session, and keep them up to date.

## Rules that always apply

- **Their originals are read-only.** Never edit, rename or move anything in `exports/`. Everything you make goes in
  `derived/` and can be rebuilt.
- **Ask before** deleting anything (deleting means the Recycle Bin or Trash, never permanently), hiding anything, or
  treating any data as "not meaningful". Process everything; list what you'd skip, with counts, and let them decide.
- **Nothing leaves their computer** without their yes for that specific job and service. Prefer local tools: Tesseract
  or EasyOCR for scans, Whisper for voice, local models for photos.
- **Look at as little as you need.** Work from counts, structures and a few samples. Ask before opening medical records,
  intimate photos or private messages in bulk.
- **Never print or copy secrets** (passwords, keys, tokens) and never put ID numbers, card numbers, phone numbers or home
  addresses into titles, summaries or the timeline.
- **Their account wins.** Order of authority: what they say, original documents, their posts, their diary, their messages,
  their AI chats, their CV. When sources disagree, follow that order; when it matters, ask.
- **Machine readings are drafts.** OCR, transcription and vision models misread names and invent details. Check medical,
  legal and money documents against the original line by line.
- **Back up before you write** a database or a corrections file: copy it to `<name>.before-<what>-<date>.<ext>`.
- **One correction fixes the mistake everywhere,** and goes in the corrections layer so it survives rebuilds.

## The order of work

### 1. Talk first
Ask, in a few short questions: what they hope to get from the archive; which languages they write in; what they
already have (phone, accounts, old drives, paper); what Claude may open; whether any online service may be used, and for
what. Write the answers in `facts.md` and `decisions.md`.

### 2. Set up
```
my-archive/
  exports/        their downloads, untouched
  derived/        catalog, timeline, people, places (rebuildable)
  corrections/    their fixes, keyed to originals (never rebuilt)
  facts.md  decisions.md
```

### 3. Get the data
Walk them through `docs/download-your-data/` one source at a time. Slow exports (Google Takeout, Meta) first. Keep a
checklist in `decisions.md`: requested, arrived, unpacked.

### 4. Survey each export before deciding anything
Count files by type and folder. Read the export's own structure (JSON keys, one sample of each kind). Work out whose
account it is, and which parts are other people's content: forwarded posts, saved texts, a shared account. Watch for
known traps: Meta's exports store text as UTF-8 read as Latin-1 (re-encode it); file dates are copy dates, not event
dates; the same photos sit in several folders.

### 5. First look
Run Lifekeeper (`toolkit/lifekeeper/lifekeeper.py exports --out derived/life.html`). Show them the page. The gaps and
surprises tell you where to go next.

### 6. Catalog everything
Write a small script that records every file in a SQLite catalog: path, type, size, content fingerprint (SHA-256), and
the best date (inside the content, then photo data, then the file date). Report duplicates by fingerprint and ask before
merging. Every later fact points back to a catalog entry.

### 7. Read what isn't text
Scans: OCR. Voice notes and recordings: transcription. Photos: date and place from the photo's data; descriptions only
if they want them and agree on the tool. Store each reading next to its file in the catalog, marked as machine-made.

### 8. Build the views
- **Timeline:** events that mattered, each with its date, a one-line title in their voice (first person), and its sources.
  Draft from posts, notes and chats; then go through every draft entry with them or against the sources.
- **People:** one card per person: the name they use, every alias and spelling, how they're related, first and last
  contact, sources.
- **Places:** homes and trips from photo locations and travel records.
- **Work:** their real career in their own words (`derived/my_career.json` or a page in `facts.md`), kept apart from
  CVs and LinkedIn, which are sales versions.
- Health, money, words: only if they want them, with the same care.

### 9. The corrections layer
Every fix they make (a wrong date, two entries that are one, a misread name) goes into `corrections/` keyed to the
original title or file fingerprint, and every build applies it last. Test it: rebuild, and check the fix is still there.

### 10. Review
Use the `review-your-archive` skill, page by page.

### 11. Back up
Set up `toolkit/backup/` with an encrypted rclone remote (`docs/backup.md`). Make sure the passwords are in their password
manager and on paper. Run a restore test with them, and write the restore steps down in plain words.

### 12. Ask (optional)
If they want to ask questions of their archive: search first, cite every sentence, show nothing that cites nothing,
check numbers against the cited sources, and start every question from their checked timeline and own career account.
See step 9 of `docs/approach.md`. For what the page shows, `toolkit/lifekeeper/ask.py` already does this.

## How to work with them

- Short answers, plain words, no jargon. One step at a time, and say what's next.
- Ask numbered questions they can answer in a word, each with your recommendation, and only the ones that are really theirs.
- When they correct a fact, add it to `facts.md` the same day; when they decide something, add it to `decisions.md`.
- Say plainly what failed or wasn't checked. Never claim a check that didn't happen.
