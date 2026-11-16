# Contributing

The most useful contributions are new sources for Lifekeeper, fixes for exports that changed format, and guides in more languages.

## Rules

- Don't share real personal data, yours or anyone else's. That means no exports, screenshots or examples from real accounts in issues or pull requests. Make up small examples instead, the way [`demo/make_demo.py`](demo/make_demo.py) and [`tests/`](tests/) do.
- Lifekeeper doesn't use the network. Don't add anything that does. Ask uses it only when the person chooses an online model.
- The core uses only the standard library and runs on plain Python 3.10+. Heavier parts (Pillow, the window, faces) are optional add-ons, and Lifekeeper must keep working without them.
- Pages use plain words, readable dates and no technical terms. See [Readable on a hard day](docs/readable-on-a-hard-day.md).
- Retweets, forwards and shared posts are other people's words. Leave them out or label them.

## Adding a source to Lifekeeper

1. Write a reader in [`toolkit/lifekeeper/lifekeeper.py`](toolkit/lifekeeper/lifekeeper.py) next to the others, and detect the format by file name or by structure in `read_all`.
2. Add a test in [`tests/test_page.py`](tests/test_page.py) with a tiny made-up file in the real format.
3. If it shows something new on the page, add it to the demo in [`demo/make_demo.py`](demo/make_demo.py) and run `python demo/make_demo.py`.
4. Add it to [docs/sources.md](docs/sources.md) and [toolkit/lifekeeper/README.md](toolkit/lifekeeper/README.md).
5. Run `python -m unittest discover -s tests`.

## Guides in other languages

Copy [`docs/download-your-data/README.md`](docs/download-your-data/README.md), translate it, save it in the same folder under the language's name (for example `es.md`), and link to it from the top of that README. Menu names should match what the apps show in that language.
