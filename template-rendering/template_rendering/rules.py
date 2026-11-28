"""Checks that only make sense for particular templates.

The shared checker (itsnews_common.storyboard) grounds every number
against the article. Games, scales and breakdowns need checks of their
own, because the generic walk cannot see across fields or measure how
text renders:

- Distractors. A quiz's wrong options are guesses, not facts, so the
  schema marks `options` x-ungrounded and this module enforces the
  distractor rule instead: a wrong option must not appear in the
  article, and must be a clearly distinct value in a wider range —
  within four times the nearest right answer (and at least a quarter
  of it) — far enough apart that the reader must know the ballpark,
  but still a plausible guess, never stated by the article.
- Spoilers. A game is where the answer is first revealed, so the
  headline, the dek, the game's question and its label must not state
  any of the game's answers.
- One game per page. A second game on the same page is a second test
  the reader didn't ask for.
- Scale bounds. A scale's min and max are display choices, so the
  shared checker does not ground them — but an axis that does not hold
  its own value and marks draws the value off the end. Explicit bounds
  must bracket the value and every mark.
- Breakdown totals. A breakdown's parts are shares of its total, so
  the total has to be above 0 and no part below 0, or the bars have
  nothing to be a fraction of.
- Voices. A voice needs exactly one of a verbatim quote and a grounded
  stance; the shared checker grounds both, this module enforces the
  either/or. A custom figure draws its own prop, shapes only — this
  module rejects text, scripts, links and any paint but the drawing
  classes, and the shared checker skips the drawing's coordinates
  (x-ungrounded) so they are never mistaken for article numbers.

The kind-conditional requirements also live here — the shared schema
validator has no if/then, so "answer is required for guess-number" and
"options and correct are required for quiz" are checked below, with
messages that name the missing field.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET

from itsnews_common import grounding
from itsnews_common.article import Article
from itsnews_common.catalog import Template

# A distractor must lie within this factor of the nearest right answer,
# on either side: far enough apart that the four options are clearly
# distinct values and the reader must know the ballpark, close enough
# that each is still a plausible guess — never a number the article states.
NEAR_MISS_FACTOR = 4.0


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
                "distractor must be within four times the nearest right answer "
                "(and at least a quarter of it). Pick a nearer miss."
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
                    "let the scale or list after the game be the payoff."
                )
    return errors


def _scale_errors(storyboard: dict) -> list[str]:
    """Explicit axis ends must hold the value and every mark."""
    errors: list[str] = []
    scenes = storyboard.get("scenes")
    if not isinstance(scenes, list):
        return errors
    for i, scene in enumerate(scenes):
        if not (isinstance(scene, dict) and scene.get("template") == "scale"
                and isinstance(scene.get("data"), dict)):
            continue
        data = scene["data"]
        path = f"$.scenes[{i}].data"
        lo, hi = data.get("min"), data.get("max")
        if _is_number(lo) and _is_number(hi) and not _value(lo) < _value(hi):
            errors.append(
                f"{path}.max: {hi} is not above the axis floor {lo}. "
                "The right end of the axis must be above the left end, "
                "or leave both out and the axis fits the value and the marks."
            )
            continue
        points = []
        if _is_number(data.get("value")):
            points.append(("value", _value(data["value"])))
        marks = data.get("marks")
        if isinstance(marks, list):
            for j, mark in enumerate(marks):
                if isinstance(mark, dict) and _is_number(mark.get("value")):
                    points.append((f"marks[{j}]", _value(mark["value"])))
        for name, point in points:
            if _is_number(lo) and point < _value(lo):
                errors.append(
                    f"{path}.{name}: {point:g} is below the axis floor "
                    f"{lo}. Widen min to hold it, or leave min out and "
                    "the axis fits the value and the marks."
                )
            if _is_number(hi) and point > _value(hi):
                errors.append(
                    f"{path}.{name}: {point:g} is above the axis ceiling "
                    f"{hi}. Widen max to hold it, or leave max out and "
                    "the axis fits the value and the marks."
                )
    return errors


def _breakdown_errors(storyboard: dict) -> list[str]:
    """A breakdown's parts are shares of its total."""
    errors: list[str] = []
    scenes = storyboard.get("scenes")
    if not isinstance(scenes, list):
        return errors
    for i, scene in enumerate(scenes):
        if not (isinstance(scene, dict) and scene.get("template") == "breakdown"
                and isinstance(scene.get("data"), dict)):
            continue
        data = scene["data"]
        path = f"$.scenes[{i}].data"
        total = data.get("total")
        if isinstance(total, dict) and _is_number(total.get("value")):
            if not _value(total["value"]) > 0:
                errors.append(
                    f"{path}.total.value: {total['value']} is not above 0. "
                    "A breakdown's parts are shares of its total, so the "
                    "total has to be above 0, or the bars have nothing to "
                    "be a fraction of."
                )
        parts = data.get("parts")
        if isinstance(parts, list):
            for j, part in enumerate(parts):
                if (isinstance(part, dict) and _is_number(part.get("value"))
                        and _value(part["value"]) < 0):
                    errors.append(
                        f"{path}.parts[{j}].value: {part['value']} is below 0. "
                        "A part of a total cannot be negative — give the "
                        "part's size as the article states it."
                    )
    return errors


def _voices_errors(storyboard: dict) -> list[str]:
    """Each voice says exactly one thing: a verbatim quote or one grounded line."""
    errors: list[str] = []
    scenes = storyboard.get("scenes")
    if not isinstance(scenes, list):
        return errors
    for i, scene in enumerate(scenes):
        if not (isinstance(scene, dict) and scene.get("template") == "voices"
                and isinstance(scene.get("data"), dict)):
            continue
        voices = scene["data"].get("voices")
        if not isinstance(voices, list):
            continue
        for j, voice in enumerate(voices):
            if not isinstance(voice, dict):
                continue
            path = f"$.scenes[{i}].data.voices[{j}]"
            has_quote = isinstance(voice.get("quote"), str) and voice["quote"] != ""
            has_stance = isinstance(voice.get("stance"), str) and voice["stance"] != ""
            if has_quote and has_stance:
                errors.append(
                    f"{path}: both a quote and a stance. Give one or the other — "
                    "a verbatim quote when the article quotes them, one grounded "
                    "line on where they stand when it does not."
                )
            elif not has_quote and not has_stance:
                errors.append(
                    f"{path}: neither a quote nor a stance. Every voice needs "
                    "one thing to say — a verbatim quote, or one grounded line "
                    "on where they stand."
                )
            is_custom = voice.get("character") == "custom"
            drawing = voice.get("drawing")
            has_drawing = isinstance(drawing, str) and drawing.strip() != ""
            if is_custom and not has_drawing:
                errors.append(
                    f"{path}: a custom figure needs a drawing. Draw the "
                    "prop that names the job — a stethoscope, a cap, a "
                    "toque — as SVG shapes, or pick the closest fixed "
                    "archetype instead."
                )
            elif has_drawing and not is_custom:
                errors.append(
                    f"{path}: a drawing on a {voice.get('character')} "
                    "figure. Only a custom figure draws its own prop — "
                    "a fixed archetype already has one."
                )
            elif has_drawing:
                errors += _drawing_errors(drawing, f"{path}.drawing")
    return errors


# A custom prop is shapes only. The allowlists below are the whole
# vocabulary a drawing may use: shape elements, geometry attributes,
# and the drawing classes in the voices stylesheet. Anything else —
# text, scripts, event handlers, links, paint of its own — is rejected,
# so nothing ungrounded can be painted into the picture. The shared
# checker cannot read words inside an image, so the rule has to live
# here, before render.
_DRAWING_TAGS = {"g", "path", "circle", "ellipse", "rect", "line",
                 "polyline", "polygon"}
_DRAWING_ATTRS = {"class", "d", "cx", "cy", "r", "rx", "ry", "x", "y",
                  "width", "height", "x1", "y1", "x2", "y2", "points",
                  "transform"}
_DRAWING_CLASSES = {"vc-prop", "vc-prop-line", "vc-tube", "vc-liquid",
                    "vc-detail"}


def _drawing_errors(drawing: str, path: str) -> list[str]:
    """A custom prop is shapes only: no words, no scripts, no links."""
    try:
        root = ET.fromstring("<svg>" + drawing + "</svg>")
    except ET.ParseError:
        return [f"{path}: not well-formed SVG shapes. Give the prop as "
                "plain SVG elements — <path>, <circle>, <rect> and the "
                "like — with no <svg> wrapper around them."]
    errors: list[str] = []
    shapes = 0
    for el in root.iter():
        if el is root:
            continue
        tag = el.tag.rsplit("}", 1)[-1]
        if tag == "svg":
            errors.append(
                f"{path}: a nested <svg> element. Give the prop's shapes "
                "directly — the template supplies the <svg> wrapper."
            )
            continue
        if tag not in _DRAWING_TAGS:
            errors.append(
                f"{path}: <{tag}> is not allowed in a drawing. Draw the "
                "prop with shapes only — path, circle, ellipse, rect, "
                "line, polyline, polygon — and no text, scripts or links."
            )
            continue
        shapes += 1
        for attr, value in el.attrib.items():
            name = attr.rsplit("}", 1)[-1]
            if name not in _DRAWING_ATTRS:
                errors.append(
                    f"{path}: the attribute {name} is not allowed in a "
                    "drawing. Colour the shapes with a class (vc-prop, "
                    "vc-prop-line, vc-tube, vc-liquid or vc-detail) and "
                    "keep the rest to geometry."
                )
            elif "url(" in value or "http" in value.lower():
                errors.append(
                    f"{path}: a link inside a drawing. Draw the prop "
                    "with shapes only — no links to anything outside "
                    "the page."
                )
        for cls in el.attrib.get("class", "").split():
            if cls not in _DRAWING_CLASSES:
                errors.append(
                    f"{path}: the class {cls} is not a drawing class. "
                    "Paint a custom prop with vc-prop, vc-prop-line, "
                    "vc-tube, vc-liquid or vc-detail."
                )
    if not shapes and not errors:
        errors.append(
            f"{path}: no shapes in the drawing. Draw the prop that "
            "names the job — a stethoscope, a cap, a toque."
        )
    return errors


def check(storyboard: dict, article: Article,
          templates: dict[str, Template]) -> list[str]:
    """The game, scale, breakdown and voices rules, run after the shared shape and grounding checks."""
    errors: list[str] = []
    errors += _scale_errors(storyboard)
    errors += _breakdown_errors(storyboard)
    errors += _voices_errors(storyboard)
    games = _game_scenes(storyboard)
    if not games:
        return errors
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
