"""Checks that only make sense for the game template.

The shared checker (itsnews_common.storyboard) grounds every number
against the article. Games need three checks of their own, because the
generic walk cannot see across fields:

- Distractors. A quiz's wrong options are guesses, not facts, so the
  schema marks `options` x-ungrounded and this module enforces the
  distractor rule instead: a wrong option must not appear in the
  article, and must be a near miss — within twice the nearest right
  answer (and at least half of it) — close enough that a reader could
  plausibly guess it, but never stated by the article.
- Spoilers. A game is where the answer is first revealed, so the
  headline, the dek, the game's question and its label must not state
  any of the game's answers.
- One game per page. A second game on the same page is a second test
  the reader didn't ask for.

The kind-conditional requirements also live here — the shared schema
validator has no if/then, so "answer is required for guess-number" and
"options and correct are required for quiz" are checked below, with
messages that name the missing field.
"""
from __future__ import annotations

from itsnews_common import grounding
from itsnews_common.article import Article
from itsnews_common.catalog import Template

# A distractor must lie within this factor of the nearest right answer,
# on either side: close enough to be a plausible guess, far enough from
# nothing the article says.
NEAR_MISS_FACTOR = 2.0


def _numbers(text) -> set[float]:
    """The numbers a string states, as floats."""
    if not isinstance(text, str):
        return set()
    out: set[float] = set()
    for token in grounding.numbers_in(grounding.plain(text)):
        try:
            out.add(round(float(token.replace(",", "")), 9))
        except ValueError:
            continue
    return out


def _is_number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _value(number) -> float:
    return round(float(number), 9)


def _game_scenes(storyboard: dict) -> list[tuple[int, dict]]:
    scenes = storyboard.get("scenes")
    if not isinstance(scenes, list):
        return []
    return [(i, s) for i, s in enumerate(scenes)
            if isinstance(s, dict) and s.get("template") == "game"
            and isinstance(s.get("data"), dict)]


def _kind_errors(data: dict, path: str) -> list[str]:
    """The fields each kind needs, and the ranges they must satisfy."""
    errors: list[str] = []
    kind = data.get("kind")
    if kind == "guess-number":
        for field in ("answer", "max"):
            if field not in data:
                errors.append(
                    f"{path}.{field}: missing — a guess-number game needs it. "
                    "Give the article number the reader guesses (answer) "
                    "and the slider's ceiling (max)."
                )
        if _is_number(data.get("answer")) and _is_number(data.get("max")):
            lo = data.get("min", 0)
            answer, hi = _value(data["answer"]), _value(data["max"])
            if _is_number(lo):
                if not _value(lo) < hi:
                    errors.append(
                        f"{path}.max: {data['max']} is not above the slider's "
                        f"floor {lo}. The ceiling must be above the floor."
                    )
                elif not _value(lo) <= answer <= hi:
                    errors.append(
                        f"{path}.answer: {data['answer']} is outside the "
                        f"slider's range {lo} to {data['max']}. The reader "
                        "must be able to reach the answer."
                    )
        if "step" in data and _is_number(data["step"]) and data["step"] <= 0:
            errors.append(
                f"{path}.step: {data['step']} is not positive. Give a step "
                "above 0, or leave it out and the template picks one."
            )
    elif kind == "quiz":
        for field in ("options", "correct"):
            if field not in data:
                errors.append(
                    f"{path}.{field}: missing — a quiz needs it. Give the "
                    "options to pick from (options) and the right answers "
                    "(correct, as a list — a question may have more than one)."
                )
    return errors


def _distractor_errors(data: dict, source: grounding.Source, path: str) -> list[str]:
    """Every wrong option must be a plausible guess, never a stated fact."""
    errors: list[str] = []
    options = data.get("options")
    correct = data.get("correct")
    if not isinstance(options, list) or not isinstance(correct, list):
        return errors
    numbers = [o for o in options if _is_number(o)]
    if len(set(map(_value, numbers))) != len(numbers):
        errors.append(
            f"{path}.options: two options are the same number. Each option "
            "must be different, or the reader cannot tell them apart."
        )
    right = {_value(c) for c in correct if _is_number(c)}
    if not right:
        return errors
    given = {_value(o) for o in numbers}
    missing = sorted(c for c in right if c not in given)
    if missing:
        errors.append(
            f"{path}.correct: {', '.join(f'{c:g}' for c in missing)} "
            "is not among the options. Every value in `correct` must "
            "also be an option, or the reader can never pick it."
        )
    if all(_value(o) in right for o in numbers):
        errors.append(
            f"{path}.options: every option is a right answer, so there is "
            "nothing to guess. Give at least one wrong option."
        )
    for i, opt in enumerate(options):
        if not _is_number(opt):
            continue
        value = _value(opt)
        if value in right:
            continue
        if source.has_number(value):
            errors.append(
                f"{path}.options[{i}]: {opt} is in the article, so it is not "
                "a wrong answer — a distractor must be a guess the article "
                "never states. Pick a number the article does not give."
            )
            continue
        nearest = min(right, key=lambda c: abs(c - value))
        if abs(nearest) == 0:
            near = abs(value) <= 2
        else:
            near = (abs(nearest) / NEAR_MISS_FACTOR <= abs(value)
                    <= abs(nearest) * NEAR_MISS_FACTOR)
        if not near:
            errors.append(
                f"{path}.options[{i}]: {opt} is too far from the right "
                f"answer ({nearest:g}) to be a plausible guess — a "
                "distractor must be within twice the nearest right answer "
                "(and at least half of it). Pick a nearer miss."
            )
    return errors


def _spoiler_errors(storyboard: dict, games: list[tuple[int, dict]]) -> list[str]:
    """The game is where the answer is first revealed."""
    errors: list[str] = []
    headline = storyboard.get("headline")
    head_spots: list[tuple[str, object]] = []
    if isinstance(headline, dict):
        head_spots.append(("$.headline.title", headline.get("title")))
        head_spots.append(("$.headline.dek", headline.get("dek")))
    for i, scene in games:
        data = scene["data"]
        answers: set[float] = set()
        if _is_number(data.get("answer")):
            answers.add(_value(data["answer"]))
        correct = data.get("correct")
        if isinstance(correct, list):
            answers |= {_value(c) for c in correct if _is_number(c)}
        if not answers:
            continue
        spots = list(head_spots)
        spots.append((f"$.scenes[{i}].question", scene.get("question")))
        spots.append((f"$.scenes[{i}].data.label", data.get("label")))
        for where, text in spots:
            stated = _numbers(text) & answers
            if stated:
                shown = ", ".join(f"{v:g}" for v in sorted(stated))
                errors.append(
                    f"{where}: it states the game's answer ({shown}) before "
                    "the reader gets to play. A game is where the answer is "
                    "first revealed — write the headline, dek, question and "
                    "label so the answer stays hidden until the reveal, and "
                    "let the big number or board after the game be the payoff."
                )
    return errors


def check(storyboard: dict, article: Article,
          templates: dict[str, Template]) -> list[str]:
    """The game rules, run after the shared shape and grounding checks."""
    games = _game_scenes(storyboard)
    if not games:
        return []
    errors: list[str] = []
    if len(games) > 1:
        errors.append(
            f"$.scenes[{games[1][0]}].template: a second game on the same "
            "page. At most one game per page — one test the reader plays, "
            "then the story goes back to showing."
        )
    source = grounding.Source(article)
    for i, scene in games:
        path = f"$.scenes[{i}].data"
        data = scene["data"]
        errors += _kind_errors(data, path)
        if data.get("kind") == "quiz":
            errors += _distractor_errors(data, source, path)
    errors += _spoiler_errors(storyboard, games)
    return errors
