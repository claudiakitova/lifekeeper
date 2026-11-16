# Sources

Every source I know of, how to get it, and what it gives you, grouped by what it tells you about your life. The last column shows whether [Lifekeeper](../toolkit/lifekeeper/) reads it today.

## Where you were

| Source | How to get it | What it gives | Read |
|---|---|---|---|
| Phone photos | Copy from the phone; iCloud.com; Google Takeout → Photos | Date and place of every photo: homes, trips, and who is in them (faces add-on) | ✓ (place from the photo's data with Pillow, or from Takeout's .json files) |
| Google location history | Takeout → Location History; or Google Maps → Your Timeline → export (phone) | Places visited, by day | ✓ both formats |
| Calendars | Google Calendar → Settings → Export; Apple Calendar → File → Export (.ics) | Appointments, trips, birthdays | ✓ |
| Travel bookings | Airline and booking site accounts, or the confirmation emails | Flights, hotels, dates | not yet |
| Uber, Bolt, taxi apps | Privacy settings → download your data | Trips around the city | not yet |
| Strava, Garmin, fitness trackers | Export activities (GPX, CSV) | Runs, walks, hikes with routes | not yet |
| Visas, tickets, travel documents | Your files and scans | Trips and the dates you crossed borders | not yet |

## Who you talked to

| Source | How to get it | What it gives | Read |
|---|---|---|---|
| Telegram | Desktop app → Settings → Advanced → Export (JSON) | Every chat, with dates | ✓ |
| WhatsApp | Each chat → Export chat | One chat per file | ✓ |
| Messenger, Instagram messages | Meta's "Download your information" (JSON) | Chats from Facebook and Instagram | ✓ |
| Text messages (Android) | The "SMS Backup & Restore" app (XML) | Texts, by contact | ✓ |
| Text messages (iPhone) | An iPhone backup read with a tool such as iMazing | iMessage and SMS | not yet |
| Email | Google Takeout → Mail (.mbox); Outlook → export (.pst) | The people you wrote to, and when | ✓ Gmail, sent mail only |
| Signal | No full export; its backups are encrypted | Nothing you can open | not yet |
| VK, Viber, Discord, Slack | Each service's data download | Chats and posts | not yet |
| Contacts | Google Contacts or iCloud → export (.vcf) | Names, birthdays | not yet |
| Screenshots of chats | Chats you no longer have can be typed back in from screenshots, with a model's help | Conversations that were lost | not yet |

## What you wrote

| Source | How to get it | What it gives | Read |
|---|---|---|---|
| Facebook, Instagram posts, stories and comments | "Download your information" (JSON) | Posts, stories and your comments, with dates | ✓ |
| X / Twitter | Settings → Your account → Download an archive | Tweets (retweets are left out because they're other people's words) | ✓ |
| Notes | Google Keep (Takeout) | Lists and notes with dates | ✓ |
| Diaries and notes apps | Day One (JSON), Notion (Markdown), Evernote (ENEX), Apple Notes (with an exporter app) | Diary entries and notes | not yet |
| Mood diaries | DailyBean, Daylio and similar: export in each app (CSV) | A mood and a few words for each day | ✓ |
| Your own documents | Word and Excel files with notes, lists and plans | Notes you kept outside any app | not yet |
| Blogs, essays, articles | Your blog's export, or saved pages | Long writing | not yet |
| AI chats | ChatGPT → Settings → Data controls → Export | What you asked about, in your words (check that every chat is yours) | ✓ titles and dates |
| Search history | Google Takeout → My Activity → Search (choose JSON) | What you looked up, and when | ✓ |

## Music, films, books

| Source | How to get it | What it gives | Read |
|---|---|---|---|
| Spotify | Account → Privacy → request "Extended streaming history" | What you listened to, month by month | ✓ |
| YouTube | Google Takeout → YouTube → history | Channels you watched | ✓ |
| Netflix | Account → Download your personal information; or Viewing activity → Download all | Series and films | ✓ |
| Goodreads | My Books → Import and export → Export library | Books read, with dates | ✓ |
| Apple Music, Kindle, Letterboxd | Each service's privacy or export page | Listening, highlights, films | not yet |
| TV trackers | MyShows, Trakt, TV Time: export in each app | Series you watched, by episode | not yet |
| Courses | Course materials, notes and certificates | What you learned, and when | not yet |
| Hobbies | Patterns, drafts, scripts, photos of what you made | What you made in your free time | not yet |

## Work and money

| Source | How to get it | What it gives | Read |
|---|---|---|---|
| LinkedIn | Settings → Data privacy → Get a copy of your data | Jobs and dates. Like a CV, it's a sales version, so your own notes take priority | ✓ |
| CVs, contracts, payslips | Your files, scanned if on paper | Real titles, dates, pay | not yet |
| Work files | Projects, presentations, papers, a dissertation, job applications | What you actually worked on | not yet |
| Job search | Notion or spreadsheet trackers, applications, cover letters | Where you applied, and what happened | not yet |
| Time trackers | aTimeLogger, Toggl and similar: export (CSV) | How you spent your hours | ✓ aTimeLogger |
| Bank and card statements | Online banking (CSV or PDF) | Where you lived, big purchases, income | not yet |
| Tax and pension documents | Your tax office or pension fund's website (PDF) | Income and jobs by year, as the state recorded them | not yet |
| Budgets and spending spreadsheets | Your own files | What you earned and spent, in your categories | not yet |
| Amazon and shops | Privacy requests, order history | What you bought, and when | not yet |
| Marketplaces you sell on | Avito, eBay and similar: your listings and photos | What you sold, and when | not yet |

## Health

| Source | How to get it | What it gives | Read |
|---|---|---|---|
| Apple Health, Samsung Health, Google Fit | Export in each app | Steps, sleep, weight, heart rate | not yet |
| Patient portals and lab results | Download PDFs; some portals export standard records (FHIR) | Diagnoses, results, medications | not yet |
| Medical imaging | Ask the clinic for the files (DICOM) or the report | Scans such as X-rays and mammograms, with dates | not yet |
| Dental records | Ask your dentist for the treatment plan and images | Treatments and dates | not yet |
| Vaccination certificates | Your health service's app or website (PDF) | Vaccines and dates | not yet |
| Flo | Settings → Request my data (JSON) | When each period started | ✓ |
| Other cycle and food apps | Clue, FatSecret, MyFitnessPal: export in each app's settings | Daily patterns | not yet |
| Genetic tests | 23andMe, Genotek and similar: download the raw data and the reports | Risk markers. Keep them private and offline | not yet |

## Things only you have

| Source | How to get it | What it gives | Read |
|---|---|---|---|
| Your own notes | Write `my_events.csv` | The main events, in your words. Lifekeeper shows them first in each month | ✓ |
| Where you lived | Write `my_homes.csv` | Home for each period, so trips are found correctly | ✓ |
| Paper | Scan with your phone | Diplomas, letters, medical and legal papers | not yet (needs OCR) |
| Old phones, drives, cameras | Copy them whole | Years that were never exported | ✓ photos |
| Voice memos, recordings, home videos | Copy the files; digitize old tapes | Voices, meetings, conversations | not yet (needs transcription) |
| Family albums | Scan, and write who is in each photo | Childhood, parents, grandparents | ✓ (dates from file names) |

## What to add to Lifekeeper next

My order, by how many people have the source and how much it adds: iPhone messages, Apple Health, Day One and Notion, bank statements (CSV), contacts' birthdays, and Strava routes. To add one, see [CONTRIBUTING](../CONTRIBUTING.md).

## Credits

Town names and locations are from [GeoNames](https://www.geonames.org/), licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Lifekeeper keeps a shortened copy: places with more than 15,000 people, with name, location, country and population.
