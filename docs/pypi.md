<img src="https://raw.githubusercontent.com/nubifere/lifekeeper/main/docs/images/lockup.svg" alt="Lifekeeper" width="320">

Reclaim your data and start your digital self: everything about you in one place, on your own computer

Lifekeeper reads the exports you already have (phone photos, Telegram, WhatsApp, Instagram, Facebook, X, Google Takeout, Spotify, Netflix, Goodreads, LinkedIn, calendars, mood diaries and more) and writes one page of your life, year by year and month by month. It finds the people in your photos and the trips you took. Then you can ask questions about your life and get answers from your own records, with the records shown.

```
pipx install lifekeeper
lifekeeper path/to/your/exports --out my-life.html
lifekeeper-ask path/to/your/exports "When did I meet Leo?"
lifekeeper-app
```

Making the page sends nothing anywhere. Answers use no AI by default; you can choose a model on your own computer (Ollama) or Google Gemini with your own key.

![One year of the demo page, for a made-up person](https://raw.githubusercontent.com/nubifere/lifekeeper/main/docs/images/demo-page.png)

The method, the download guides for each service, and the double-click apps for Windows and Mac: https://github.com/nubifere/lifekeeper
