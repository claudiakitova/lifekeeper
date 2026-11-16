# Skills for Claude Code

[Claude Code](https://claude.com/claude-code) is an AI agent that works in a folder on your computer: it reads files, writes scripts and runs them, with your approval. These skills give it the approach from this repository, so it can build and review your archive with you step by step.

| Skill | What it does |
|---|---|
| [build-your-archive](build-your-archive/SKILL.md) | From "I have some exports" to a catalog, a timeline, people, places, corrections and a backup |
| [review-your-archive](review-your-archive/SKILL.md) | Goes through your archive page by page with the [readable-on-a-hard-day](../docs/readable-on-a-hard-day.md) rules, and fixes what it finds |

## Using them

1. Make a folder for your archive, say `my-archive`, and put your exports in `my-archive/exports/`.
2. Copy this repository's `skills/` folder to `my-archive/.claude/skills/`.
3. Copy the two templates from `review-your-archive/` to `my-archive/` and start filling in `facts.md`: your name and its spellings, the people who matter, the order of authority.
4. Open Claude Code in `my-archive` and say "let's build my archive" or "review my archive".

## Before you start

Claude Code runs on Anthropic's servers, so whatever it reads is sent there. It doesn't need to read everything. Most steps run scripts on your computer and look only at counts and samples. Decide what it may open (photos, medical records, messages), tell it at the start, and write it in `facts.md`. The skills ask before sending anything to any other service, and before deleting or hiding anything.
