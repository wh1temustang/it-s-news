# Template catalog

Pick templates by the **question a scene answers**, not by how they look.
Each template's schema (fields, limits, field descriptions) follows this catalog.

| Reader question | Template | Needs from the article | Skip when |
|---|---|---|---|
| How did we get here? What's next? | `timeline` | 2+ dated events, 3–5 is best | there is only one date, or the order of events is unclear |
| Where does it happen? | `map` | a specific place that matters to the story | the place is only a dateline or a company's headquarters |
| How do these compare in size? | `bar-chart` | 2+ values in the same unit, for the same time | the values use different units or come from different times |
| How has it changed over time? | `line-chart` | 3+ values of one measure at different times | the article gives only a start and an end (use `list` for the two values) |
| How do two sides differ? | `comparison` | two sides answering the same 2+ points, each named with their role | the sides don't answer the same questions |
| Why is it happening? What does it lead to? | `cause-effect` | 3+ linked steps, each one stated in the article | the links are your own inference |
| What did someone say that matters? | `quote` | a direct quote from a named speaker | the quote is filler ("We are pleased to announce…") |
| What does it feel like to touch? | `reactive` | one number or turn the reader should feel: a figure worth uncovering, a before and after to compare, or a value to fill up by holding | the number is small enough to just read, or the turn needs a chart's precision |
| What is the answer — can I guess it first? | `game` | a number or fact worth guessing: a total, a price, a count | the news is grave, or the story has no number or fact worth guessing |
| Where does this number stand? | `scale` | one headline number plus 1–4 reference points from the article: a previous value, a threshold, a target | the article gives no reference point (the number goes in the `list` as one row) |
| How does it work, step by step? | `flow` | 3–5 ordered stages of a process, with no dates | the stages have dates (use `timeline`) or the article states each step causing the next (use `cause-effect`) |
| What's in it? Where does it go? | `breakdown` | one total plus 2–6 named parts, all in the same unit | the parts aren't shares of one total (use `bar-chart`) |
| What are the essentials, in order? | `list` | 2+ short facts: cost, date, size, status… | the rows would only restate the headline |

If no row fits a question, leave the question out. Fewer, stronger scenes
beat a full page.

**Background first.** A template can only show what the article gives it.
Before matching questions to templates, check the article gives a
first-time reader the background the story needs (prompt.md step 2): what a
named law, organisation or acronym is, who a named person is. If it does
not, ask the writer for more background first. A comparison of two people
the reader cannot place, or a list about a law the reader has never heard
of, is a thin page — and no template fixes that.

## Notes per template

**`list`**: the fallback for loose essentials — the same facts a board
used to tile, shown as full-width rows in reading order, most important
first. The value is the punch — a number, a word, a few words — and the
label carries the topic, holding the fuller phrase when the value
shortens it. Extra context goes in `note`. Rows read top to bottom, so
the order means something: lead with the fact the story turns on.
With the list carrying the facts, the headline can stay simple: it
names the topic in plain words, no numbers — the numbers live in the
list, the scale or the game below, and the dek doesn't restate them
either. A `note` must add a fact the value does not carry. If it only
restates the value in longer words, leave the note out — the row reads
cleaner without it.

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
article gives one side's answer but not the other's. Name each side with
their role as well as their name, when it fits the label — a bare name
tells the reader nothing about who is speaking. Each row must give both
sides their own content for that point: a cell that only restates a side's
position from another row is not an answer to the point.

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
reveal, and let the scale or list after the game be the payoff.
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

**`scale`**: one figure on an axis with the reference points the article
states, so the reader sees where it stands instead of just what it is.
A number earns a scale only when the article gives it reference points —
without them it is one row in the `list`, never a scene of its own. The
value and every mark are article numbers; `min` and `max` are display
choices, not facts — leave them out and the axis fits the value and the
marks. When the scale has a `unit`, it is printed after every number —
the value, each mark and both axis ends — so no number on the axis reads
bare. Pick marks the reader can tell apart: a previous value, a
threshold, a target. When two marks sit close together their labels
crowd, so pick the ones that read apart.

**`flow`**: a process in order, with no dates. Use it for how something
works, how it unfolds, what happens next — a procedure, a mechanism, a
run of stages. Each step is one short phrase from the article, titled
with the stage's name. When the stages have dates, that is a `timeline`;
when the article states each step causing the next, that is a
`cause-effect`; when the steps are only loosely related facts, that is
a `list`.

**`breakdown`**: one total with its named parts — where the money goes,
what a deal is made of. The parts are shares of the one total, largest
first, all in the same unit; the bars are sized against the total, not
against each other. When the values are peers being compared rather
than shares of a whole, that is a `bar-chart`. Articles round figures,
so the parts need not sum exactly to the total.

## Ordering

1. Lead with the scene that answers the main question.
2. Then context: *where* (`map`) and *when* (`timeline`).
3. Then reaction and consequence: `quote`, `cause-effect`.

When two scenes matter equally, use this order: `game`, `scale`, `flow`,
`breakdown`, `list`,
`bar-chart` or `line-chart`, `comparison`, `timeline`, `map`,
`cause-effect`, `quote`.

## Pairings that often work

These are starting points, not rules.

| Story | Scenes |
|---|---|
| Disaster or accident | `list` (the toll) + `map` + `timeline` |
| Policy decision | `breakdown` + `cause-effect` + `quote` |
| Economic data release | `scale` + `line-chart` |
| Process or mechanism | `flow` + `quote` |
| Election result | `bar-chart` + `map` |
| Company deal or results | `scale` + `list` + `quote` |
| Conflict or negotiation | `timeline` + `map` + `comparison` |
| New transport link | `list` + `map` + `comparison` |
| Science finding | `list` + `cause-effect` + `quote` |
| Local pilot or trial | `scale` + `bar-chart` + `quote` |
