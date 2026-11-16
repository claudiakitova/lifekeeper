# Similar projects

Several projects cover parts of what this approach does. I haven't found one that covers all of it: one archive built from the data you already have, that you can correct, that is easy to read, and that answers questions with sources. This is what existed as of late 2026.

## Personal archive software (closest)

- [Timelinize](https://timelinize.com) (open source, AGPL-3.0, pre-1.0). Imports Google Takeout, phone backups, messages, photos and location history into one local timeline in SQLite, and links people across sources. It's the closest project to this one. It's a full app, and its data format still changes between versions.
- [Perkeep](https://perkeep.org) (open source). A storage system for a lifetime of personal data. The storage is solid, and it has few ready-made views.
- [HPI](https://github.com/karlicoss/HPI) and [Dogsheep](https://dogsheep.github.io) (open source). Libraries that turn personal exports into data you can query. They're aimed at programmers.
- [Immich](https://immich.app) and [PhotoPrism](https://www.photoprism.app) (open source). Self-hosted photo libraries. They handle photos only, and handle them very well.

## AI connected to your accounts

- Google Gemini's Personal Intelligence (beta from January 2026). Answers from your Gmail, Google Photos, and Search and YouTube history, with a switch for each source.
- ChatGPT and Claude connectors, and phone assistants with personal context.

These are convenient for recent things and aren't archives. See [Why not just connect an AI](why-not-just-connect-ai.md).

## Record-everything tools

- [screenpipe](https://screenpi.pe) (open source). Records your screen and audio locally and makes them searchable. It uses about 20 GB a month.
- Microsoft Recall (Windows). Takes snapshots of your screen activity.
- Rewind and Limitless were shut down in December 2025 after Meta bought Limitless.

These tools record from the day you install them, so they don't cover your past, and they record everything, not a chosen set.

## Chat with your documents

- [Khoj](https://khoj.dev), [AnythingLLM](https://anythingllm.com) and similar (open source). Search and chat over your notes and files with local or cloud models. They're useful for documents. They don't build a timeline, people or places, and they don't keep corrections.

## Life stories and legacy

- Storyworth and Remento (about $99): weekly prompts that become a printed book.
- HereAfter AI (about $50 a year) and StoryFile: recorded interviews you can "talk to" later.

These collect new stories through prompts. This approach starts from the records you already have.

## Dementia and reminiscence apps

- LifeBio Memory and other reminiscence apps, used mostly in care homes, with life stories typed in by hand. The research behind life story work is encouraging but modest (see [Memory loss](memory-loss.md)).

## Comparison

| | This approach | Personal archive apps | AI + accounts | Life story services |
|---|---|---|---|---|
| Starts from data you already have | ✓ | ✓ | partly | no |
| Works for decades, offline | ✓ | ✓ | no | partly |
| Your corrections stay | ✓ | no | no | ✓ (you write it) |
| Readable on a hard day | ✓ (a design rule) | no | no | ✓ |
| Answers with sources | ✓ | no | partly | no |
| Built with you by an AI agent | ✓ (skills) | no | no | no |
| Free and open | ✓ | ✓ | no | no |

These can be combined, for example a photo library for the photos and this approach for everything around them.
