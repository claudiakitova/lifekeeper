# Start small

Most people never kept a diary, but their phone and accounts hold years of dated records. This page lists what you probably have and gives a plan for the first week.

## What you already have

From the most useful to the least, for most people:

| Source | What it gives you | Effort |
|---|---|---|
| Phone photos | When and where you were, year by year: trips, homes, the people you were with | Copy them to a computer |
| Chats (Telegram, WhatsApp, Messenger) | Who you talked to and when, and life events you told friends about in your own words | One export per app (WhatsApp: per chat) |
| Google Takeout | Maps Timeline (places you visited), Calendar, YouTube and search history, Gmail | One request, then a download link by email |
| Social media (Instagram, Facebook, X) | Your posts, with dates | One request per account |
| Bank and payment statements | Where you lived, big purchases, jobs (salary deposits) | Download PDFs or CSVs |
| Health apps | Steps, sleep, cycle, mood, weight | Export in each app's settings |
| Documents | Diplomas, contracts, medical results, IDs | Scan with your phone |
| Work | LinkedIn export, CVs, certificates | One request. A CV is a sales version of your career, so treat it that way |

## A one-week plan

Day 1: request the slow exports. Google Takeout, Facebook and Instagram take hours to days to prepare, so request them first. ([How](download-your-data/))

Day 2: chats. Export Telegram from the desktop app (JSON format). Export your most important WhatsApp chats one by one.

Day 3: photos. Copy your phone's photos to the computer, folders and all. Don't rename anything.

Day 4: put it together. Make one folder, say `my-archive/exports/`, and unpack everything into it, one subfolder per source.

Day 5: first look. Run Lifekeeper on it:

```
python toolkit/lifekeeper/lifekeeper.py my-archive/exports --out my-archive/life.html
```

The page shows your years month by month: where you were, who you talked to most, what you posted. Empty months show you what's missing.

Days 6 and 7: fill the gaps. Scan the documents that matter most, and add the exports that arrived late.

## Small habits from now on

Each of these takes a few seconds:

- Write one line a day, in a mood app with a note field or in a notes app: what happened, who you saw.
- Photograph documents when you get them: results, contracts, receipts for big purchases.
- Name people. When a photo app asks "who is this?", answer.
- Write one note a year, at New Year, about what happened that year.
- Export twice a year. Put a reminder in your calendar.

## What not to worry about

- Gaps. Every archive has years with little data. The timeline shows them as they are.
- Mess. Duplicates, odd file names and half-finished exports get sorted out by the catalog.
- Being complete. Start with one source. A timeline from photos alone is already useful.
