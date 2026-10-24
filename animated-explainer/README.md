# Animated explainer

One of the [it's news](../README.md) approaches: tell a news story as a few
pages of vector animation the reader clicks through, one idea at a time.

**Status: prototype.** There is one hand-built example,
[examples/night-train.html](examples/night-train.html), to settle the look
and feel. The pipeline that would make pages like it from any article (agent,
checker, renderer, tests) isn't written yet. Its planned design is
[below](#how-it-would-work).

## Try the example

Open [examples/night-train.html](examples/night-train.html) in a browser.
Click, tap or press → to play the next step, and ← to go back. The dots
jump to a page, and on a phone a swipe works too. The page is one
self-contained file that loads nothing from the network.

It tells the fictional night train story, the same article that template
rendering uses in its example ([examples/night-train.md](examples/night-train.md)).
"Read it as text", under the screen, gives the same story as text.

## Length

Each scene is one page, and each click plays the next step on the page. A
page fills its dot under the screen as its steps play. An explainer shows **at
most 5 pages** by default:

- The script's `max_pages` sets the limit for a story.
- `?pages=N` in the address overrides it, for example
  `night-train.html?pages=9` for the whole example.
- Every scene has a `rank`, where 1 is the page to keep if only one fits. The
  limit keeps the best-ranked scenes and plays them in story order.

The example script has 9 scenes. At the default 5 it plays the title, the
route, "Isn't flying faster?", CO2 and the risks, in 14 steps. The fares,
demand, timeline and closing dates wait for a higher limit.

## How it differs from template rendering

| | [Template rendering](../template-rendering/) | Animated explainer |
|---|---|---|
| The reader | scans a page of finished visuals | sees one idea at a time, at their own pace |
| Each visual | appears complete | is built step by step on screen |
| Numbers | shown as the article gives them | shown, and any number the article only implies is worked out on screen |
| Best for | a quick overview | a story with a "but wait" in it |

## Design principles

- **One idea per step.** Each click adds one thing: a city, a bar, a block
  of squares. The heading stays the reader's question. The caption under it
  says what just changed.
- **Start from the reader's doubt.** "Isn't flying faster?" first shows the
  plane winning, then the two facts that turn it around: door to door, the
  flight takes about five and a half hours, and the train's hours fall
  overnight.
- **Transform, don't cut.** The train's 14 h 35 min bar bends into an arc on
  a 24-hour clock. The reader watches the same time land between 7:40 pm and
  10:15 am.
- **Show the working.** A number the article doesn't state, such as a ratio,
  appears with its sum: 142 ÷ 18 ≈ 7.9. The train's 18 kg block is stamped
  across the plane's 142 kg until the squares run out, and the 2021 passenger
  figure is stacked against 2025's.
- **Colour keeps its meaning.** The train is teal, the plane red, the route
  and key dates gold, warnings orange, from start to finish.
- **Silent.** Short on-screen titles stand in for narration, so it works
  with the sound off. Every step also has a text version for screen readers.

## How it would work

```
 article.md ──► AI agent ──► script.json ──► check ──► render ──► explainer.html
                  ▲                            │
                  └── fix what check reports ◄─┘
```

The split is the same as in template rendering. An AI agent makes the
editorial choices: which questions to answer, which scene kinds answer them
and what each step shows. Plain code does everything that should come out the
same every time.

- **The script** is JSON, and the example already runs on it: see
  `<script type="application/json" id="explainer">` in the page. A script is
  a list of scenes and a `max_pages` limit. Each scene has a `kind`, a
  `rank`, the reader `question` it answers, a `why` for reviewers, and its
  `beats`. A beat names the move it plays (`do`), its `caption` and, when a
  figure needs one, its `source`. `{train:14 h 35 min}` in a caption colours
  text by role.
- **The agent** would rank every scene it writes, so one script serves any
  length, and put the scene that answers its one-sentence summary first.
- **Scene kinds** are this approach's templates. Each draws one kind of
  picture and offers a few moves:

  | Kind | What it shows | Moves |
  |---|---|---|
  | `title` | the news in one line, with a track drawn between two places | `show` |
  | `route` | a map, with the route drawing itself stop by stop | `start`, `travel`, `hotspot`, `quote` |
  | `race` | durations as bars on a time axis; a bar can fold onto a 24-hour clock | `show`, `extend`, `clock`, `quote` |
  | `units` | two amounts counted in squares; the smaller measures the larger | `fill`, `measure` |
  | `bars` | a few values as columns | `grow` |
  | `trend` | a line over time; the first value stacked up to the last | `start`, `rise`, `measure` |
  | `timeline` | dated events from past to future, with chips or icons beneath | `reveal` |
  | `end` | the dates or facts a reader can act on | `show` |

- **The check** would hold scripts to the same rules as template rendering:
  every figure and quote comes from the article, word for word for quotes,
  and every caption stays inside its length budget. On top of that, code
  recomputes each worked-out number (`math`) and rejects one that is wrong,
  and checks that ranks are unique.
- **The renderer** would be a Python package that writes one self-contained
  HTML file with the animation engine inlined, as in the example. The output
  would be deterministic, with no timestamps, randomness or network access.

## Open questions

- Should the pipeline share the fact checker and map data with template
  rendering, or copy them so each approach stays independent?
- Should there be an autoplay mode next to click-to-advance, and narration
  later (recorded, or the browser's speech)?
- Is exporting a video (MP4) for social media worth adding?

## Map data

The map comes from [Natural Earth](https://www.naturalearthdata.com/) and is
in the public domain. [tools/cut_map.py](tools/cut_map.py) cuts the area
around the route out of template rendering's `world.json`.
