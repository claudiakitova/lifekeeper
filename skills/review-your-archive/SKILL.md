---
name: review-your-archive
description: Review a personal life archive page by page so it reads well on a hard day and stays true to the originals; fix what's wrong in the corrections layer so fixes survive rebuilds. Use when the person says "review", "check this page", pastes something from their archive with "?" or "weird", or corrects a fact.
---

# Reviewing a life archive

Every page has to make sense at a glance on a bad day: readable, true to the originals, complete and in a sensible
order. And it has to stay that way: a fix that a rebuild would undo isn't a fix. The goal is good, not fast.

Before reviewing, read the person's `facts.md` (what's true about their life, the spellings, what isn't theirs) and
`decisions.md` (every decision they've already made; never undo one). Templates are next to this file.

## What they say, and what they mean

| They say | They mean |
|---|---|
| "review" | Check everything about it (wording, truth, format, order, duplicates) and fix it |
| "?" | Tell me what this is, then fix it if it's wrong |
| "format" | Fix how it reads: tables, line breaks, markup, junk, dates |
| "weird" | Something's off (labels, wording, layout or behavior). Find it all and fix it |
| "remove" (from a page) | Hide it through the corrections layer. The data stays |
| "delete" (files) | Move them to the Recycle Bin or Trash, after a yes, and update the catalog |

People who dictate get names misheard. Keep a list of their usual mishearings in `facts.md`.

## How to run a review

1. **Read `facts.md` and `decisions.md`.**
2. **Find suspects automatically.** Write or run a small check over the page's data: machine dates (2024-03-01),
   file names standing in for titles (IMG_2041), the person's name in the third person, doubled words, raw markup or
   broken characters, words from another language left in titles, duplicate entries. It gives suspects, not verdicts.
3. **Go page by page.** For each: look at it as they will, read every line, open several items, try every button and
   filter, and open the original behind anything that states a fact.
4. **Check against the originals,** never against a model's description of them.
5. **Fix it durably:** in the corrections layer, keyed to the original, and the same mistake everywhere it appears.
6. **Look again** after the fix, on the page itself.
7. **Write it down:** a dated line in `decisions.md` for every decision; new facts in `facts.md`.
8. **Report** (below).

## The rules

The full list is in `docs/readable-on-a-hard-day.md`. The ones that matter most:

- First person, plain words, one language per page, one spelling per name.
- A title says what the thing is; a file name never stands in. Two entries never look the same.
- Readable dates ("Apr 14, 2026"), thousands separators, money in the currency they think in.
- Things live where they belong; histories oldest first; empty things don't show.
- Long or personal text stays folded until they open it.
- Every fact checked against its original. Other people's words stay theirs. Medical, legal and money documents are
  checked line by line.

## Ask first, always

Deleting anything, hiding anything, treating data as not meaningful, sending anything to an outside service, and
changing system or security settings.

## Reporting

- Open with what's done, in a sentence or two.
- Then, short and grouped by page: what changed, described as they'll see it (quote the new wording), and what's open.
- Say plainly what failed or wasn't checked.
- Questions last: numbered, answerable in a word, each with your recommendation.
- No internal jargon (IDs, file paths) unless they need it to act.
