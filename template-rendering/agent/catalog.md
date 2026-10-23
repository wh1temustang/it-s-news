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

If no row fits a question, leave the question out. Fewer, stronger scenes
beat a full page.

## Notes per template

**`info-board`**: the default "at a glance" scene. Values are fragments
("$48 million", "Closed"), never sentences. Use `tone` only for things that
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

## Ordering

1. Lead with the scene that answers the main question.
2. Then context: *where* (`map`) and *when* (`timeline`).
3. Then reaction and consequence: `quote`, `cause-effect`.

When two scenes matter equally, use this order: `big-number`, `info-board`,
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
