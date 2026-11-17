# Template catalog

Pick templates by the **question a scene answers**, not by how they look.
Each template's schema (fields, limits, field descriptions) follows this catalog.

| Reader question | Template | Needs from the article | Skip when |
|---|---|---|---|
| What are the essentials? Where does each part stand? | `info-board` | 2+ short facts: cost, date, size, status… | the tiles would only restate the headline |
| Is one number the news? | `big-number` | 1–3 numbers that are headline-worthy on their own | there are 4+ numbers to show (use `info-board` or `bar-chart`) |
| How did we get here? What's next? | `timeline` | 2+ dated events, 3–5 is best | there is only one date, or the order of events is unclear |
| Where does it happen? | `map` | a specific place that matters to the story | the place is only a dateline or a company's headquarters |
| How do these compare in size? | `bar-chart` | 2+ values in the same unit, for the same time | the values use different units or come from different times |
| How has it changed over time? | `line-chart` | 3+ values of one measure at different times | the article gives only a start and an end (use `big-number` with `context`) |
| How do two sides differ? | `comparison` | two sides answering the same 2+ points | the sides don't answer the same questions |
| Why is it happening? What does it lead to? | `cause-effect` | 3+ linked steps, each one stated in the article | the links are your own inference |
| What did someone say that matters? | `quote` | a direct quote from a named speaker | the quote is filler ("We are pleased to announce…") |
| What does it feel like to touch? | `reactive` | one number or turn the reader should feel: a figure worth uncovering, a before and after to compare, or a value to fill up by holding | the number is small enough to just read, or the turn needs a chart's precision |
| What is the answer — can I guess it first? | `game` | a number or fact worth guessing: a total, a price, a count | the news is grave, or the story has no number or fact worth guessing |

If no row fits a question, leave the question out. Fewer, stronger scenes
beat a full page.

## Notes per template

**`info-board`**: the default "at a glance" scene. Values are fragments
("$48 million", "Closed"), never sentences. The value is the punch — a
number, a word, a few words (at most 6 Chinese characters; Chinese has no
word boundaries, so a longer Chinese value wraps mid-phrase on a phone).
The label carries the topic and may hold the fuller phrase the value
shortens: label "摩根士丹利：數據中心收入" / value "下調約一成", not
label "摩根士丹利預測" / value "數據中心收入下調約一成". Extra context
goes in `note`. Use `tone` only for things that
have a state (a road, a vote, a service): `good` for open, passed or
restored; `bad` for closed, rejected or halted; `pending` for under review,
awaited or in progress; `neutral` for anything else. The value must also say
the state in words, because colour alone doesn't reach every reader.

**`big-number`**: for when the number *is* the headline: a death toll, an
interest rate, a price, a vote count. The first number gets the largest
type. Use `context` for the comparison the article gives ("up from 2.9%"),
and `trend` only when the article says the number rose or fell.

**`timeline`**: oldest first. Mark the news itself `now` and anything
scheduled or expected `next`. Use the article's own dates ("Thursday",
"March 20", "2019"). If the article says "last week", so do you.

**`map`**: list the main place first; it gets the big pin. Add other places
only if they play a part (stops on a route, other affected towns). Set
`scope` when a single place needs surroundings to be recognisable: `city`
for a neighbourhood story, `region` or `country` for a town most readers
won't know. Coordinates come from your own knowledge, to two decimals.

**`bar-chart`**: same unit, same moment. Order the bars so the order means
something: largest first, or from most negative to most positive. Never
order them alphabetically. Negative values are drawn to the left of a centre
line, so use them for falls ("down 3%" becomes `-3`).

**`line-chart`**: one measure, three or more time points, oldest first. Only
the points the article gives; never interpolate a missing year. Put the
measure and its unit in `unit` ("Passengers, millions").

**`comparison`**: two sides, the same questions. Typical pairs: two options
(train against plane), before and after, two parties' positions. Lead with
the row that shows the biggest difference. Write "Not stated" when the
article gives one side's answer but not the other's.

**`cause-effect`**: a chain of three to five steps in which each step leads
to the next, ideally ending with what it means for the reader. Every link
must be something the article says, not something you conclude.

**`quote`**: one quote that carries the story: a decision, a warning, a
stance. Name the speaker as the article does, and give their `role` when it
explains why their words matter.

**`reactive`**: one scene the reader touches, for the number or turn that
lands harder felt than read. Pick the kind by what the reader does:
`scratch` hides one headline number under a foil the reader rubs away;
`wipe` puts a before and an after side by side with a draggable divider
between them, so the reader's own thumb reveals the change — both values
are article numbers; `hold` counts a value up while the reader presses
and holds, with a progress fill, and the readout never passes the article
number. The hold has a rate rule: a full hold takes `fill_seconds`
(default 3 seconds) whatever the size, so the rate is the target divided
by `fill_seconds` — a bigger number fills faster in absolute units. Give
a fast-moving number (a crash, a surge) the short end, 1.5–2 seconds, so
it feels urgent, and a slow-moving one about 4 seconds. When the fill
counts a change between two article numbers (the dollars lost from a peak
to where the price is now), give `from_value` and `to_value`: both are
article numbers, the page computes the difference, and the storyboard
holds only numbers the article states. At most one reactive scene per
page. Affordances over instructions: a reactive scene shows no helper
sentences — the gesture must be obvious from the shape alone (the foil,
the divider grip, the fill bar). Reactive is never the default: use one
only when it fits the story — a surprising number worth revealing
(`scratch`), a before-and-after contrast that *is* the story (`wipe`),
or a magnitude worth feeling in the hand (`hold`). Otherwise prefer a
static template. And never for serious, sad or grave news — no reactive
scenes on deaths, disasters, war or suffering, full stop: a foil over a
toll is the wrong tone.

**`game`**: a mini-game the reader plays, for the number or fact worth
guessing before reading it. Two kinds: `guess-number` gives the reader
a slider and one reveal button — they guess the article's number, then
the page states the answer and how close the guess was (exact, within
5% for a near miss, or far, with the difference), and they may try
again; `quiz` gives three or four options to pick from, and a question
may have more than one right answer — a price range has two ends — so
`correct` is a list and a right pick lights up every right answer. A
wrong option is a guess, not a fact: it must not appear in the article,
and it must be a near miss — within twice the nearest right answer (and
at least half of it) — so $85 is a fair distractor for a $70–78 range,
but $200 is not. A game is where the answer is first revealed: the
headline, the dek, the game's question and its label must not state any
of the answers — write them so the answer stays hidden until the
reveal, and let the big number or board after the game be the payoff.
The quiz has no reset: once answered it stays answered. Set `unit_after`
explicitly on every game: true when the unit goes after the number —
Chinese units (億美元, 萬億美元, 億加元, 萬噸, 厘米), so "1,087億美元" —
false when it goes before — "$", so "$78". A game without it fails the
check. The answers in
`answer` and `correct` are article numbers and are checked against it;
the slider's `min`, `max` and `step`, and the quiz's wrong options, are
design choices and are not checked as facts — the distractor rule above
is what keeps them honest. Use a game only when the story has a number
or fact worth guessing. If none comes to mind, leave the story without
a game — a dull game is worse than none, and a game is never owed just
to fill coverage. At most one game per page. The only exclusion is grave
news: no games on deaths, disasters, war or suffering, full stop.
Affordances over instructions: a game shows no helper sentences — the
slider and the buttons are the only cues, plus one-word buttons.

## Ordering

1. Lead with the scene that answers the main question.
2. Then context: *where* (`map`) and *when* (`timeline`).
3. Then reaction and consequence: `quote`, `cause-effect`.

When two scenes matter equally, use this order: `game`, `big-number`, `info-board`,
`bar-chart` or `line-chart`, `comparison`, `timeline`, `map`,
`cause-effect`, `quote`.

## Pairings that often work

These are starting points, not rules.

| Story | Scenes |
|---|---|
| Disaster or accident | `big-number` (the toll) + `map` + `timeline` |
| Policy decision | `info-board` + `cause-effect` + `quote` |
| Economic data release | `big-number` + `line-chart` |
| Election result | `bar-chart` + `map` |
| Company deal or results | `big-number` + `info-board` + `quote` |
| Conflict or negotiation | `timeline` + `map` + `comparison` |
| New transport link | `info-board` + `map` + `comparison` |
| Science finding | `info-board` + `cause-effect` + `quote` |
| Local pilot or trial | `big-number` + `bar-chart` + `quote` |
