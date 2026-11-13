# it's news

**News you get in seconds, not minutes.**

The easiest way to try it: paste this link into Muse and ask it for a daily
news brief — it will find today's news and render it as a visual page.

https://github.com/wh1temustang/it-s-news

It turns the day's news into a visual, single-file page. No setup needed —
or clone the repo and open any `.html` file in an `examples/` folder.

## Three ways to read the news

- **Template rendering** — the whole story on one page: info boards, maps,
  charts, timelines. [Example](template-rendering/examples/night-train.html) ·
  [how it works](template-rendering/)

<p align="center">
  <img src="docs/images/template-rendering.png" width="400" alt="A template-rendered page for the night train story: the headline, an info board with the journey time, nights, fares and ticket date, and a map with four numbered stops from Vienna to Barcelona.">
</p>
<p align="center"><sub>An info board and a map for the night train story.</sub></p>

- **Animated explainer** *(prototype)* — one idea per click, a few pages of
  vector animation. [Example](animated-explainer/examples/night-train.html) ·
  [design](animated-explainer/)

<p align="center">
  <img src="docs/images/animated-explainer.gif" width="720" alt="An animated explainer asks &quot;Isn't flying faster?&quot;. The train's 14 h 35 min bar bends onto a 24-hour clock that runs from 7:40 pm to 10:15 am, then the plane's 142 kg of CO2 is measured out in blocks of the train's 18 kg: 142 ÷ 18 ≈ 7.9.">
</p>
<p align="center"><sub><i>Isn't flying faster?</i> The explainer answers with the article's own numbers.</sub></p>

- **Meme rendering** — the story as a post, in meme formats readers already
  know. [Example](meme-rendering/examples/self-checkout.html) ·
  [how it works](meme-rendering/)

<p align="center">
  <img src="docs/images/meme-rendering.png" width="400" alt="A meme-rendered post for a supermarket story: a distracted meme with the chain eyeing staffed tills over its self-checkout machines, three stonks panels for 31%, 4 minutes and 5%, and an expanding brain for the rollout.">
</p>
<p align="center"><sub>Distracted, stonks and expanding brain for a supermarket story.</sub></p>

They mix and match: an edition is templates by default, one deep story may
carry an animated explainer, and a number worth feeling may get a reactive
scene — scratch to reveal it, wipe from before to after, or press and hold
to fill it up. [Reactive example](template-rendering/examples/reactive-rain.html) ·
[mixed example edition](template-rendering/examples/edition.html)

<p align="center">
  <img src="docs/images/reactive.gif" width="480" alt="A reactive scene in action: a foil is rubbed away to reveal 84 mm, a divider wipes from the old 61 mm record to 84 mm, and holding fills the river's rise to 2 metres.">
</p>
<p align="center"><sub>Scratch, wipe and hold for the Willow Creek rain story.</sub></p>

## Playful, never made up

- **Every number and quote** must come from the article. The check rejects
  anything else, and the agent fixes its storyboard until it passes.
- **One file, no network.** Each page is a single self-contained HTML file,
  in light and dark themes.
- **Any language.** The words the page adds itself — headings, labels,
  credits — live in a labels file. Swap it for another language's file and
  the same story renders in that language.

## Render it yourself

```bash
git clone https://github.com/wh1temustang/it-s-news.git
cd it-s-news/template-rendering
python3 -m venv .venv && .venv/bin/pip install -e ../common -e .
.venv/bin/python -m template_rendering gallery   # every template on one page
```

See each approach's README for details, or ask a coding agent working in
this repo to "present this article". The
[daily-edition](daily-edition/) skill renders a whole morning edition from
your newsletters.

Everything here is public — never commit credentials or personal data. Got
another way to make news quick to take in? Add an approach, following
[AGENTS.md](AGENTS.md#adding-an-approach).

## License

MIT. See [LICENSE](LICENSE).
