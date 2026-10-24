"""Memes are for light stories. Serious ones get the facts, straight.

Every storyboard sets headline.mood to "light" or "serious", and two checks
hold the line:

- A serious story uses only straight formats, the templates whose schema
  says "x-joke": false (a megathread, a thread of quotes, reminders).
- An article that reports harm to people, such as deaths, injuries,
  violence or a disaster, is serious whatever the storyboard says. HARM
  below catches the English words for it, and errs on the side of caution:
  "the bill died in committee" makes a story serious too. In other
  languages, the agent's judgement is all there is, so the prompt asks for
  it in every language.
"""
from __future__ import annotations

import re

from itsnews_common.article import Article
from itsnews_common.catalog import Template
from itsnews_common.grounding import plain

HARM = re.compile(
    r"\b("
    r"kill(?:s|ed|ing)?|dead|died|dies|dying|death|deaths|deadly|fatal(?:ly|ity|ities)?|"
    r"injur(?:y|ies|ed)|wounded|victims?|casualt(?:y|ies)|"
    r"murder(?:s|ed)?|shooting|stabb(?:ed|ing)|assault(?:s|ed)?|rape[ds]?|abuse[ds]?|"
    r"suicide|massacre|genocide|terror(?:ism|ist)?|war|airstrikes?|bombings?|hostages?|"
    r"earthquake|flood(?:s|ed|ing)?|wildfires?|hurricane|famine|epidemic|pandemic|outbreak|"
    r"evacuat(?:ed|ion)|missing persons?"
    r")\b",
    re.IGNORECASE,
)


def joke(template: Template) -> bool:
    return bool(template.schema.get("x-joke"))


def rules(storyboard: dict, article: Article, templates: dict[str, Template]) -> list[str]:
    """The mood checks, run after the shared shape and grounding checks."""
    headline = storyboard.get("headline")
    mood = headline.get("mood") if isinstance(headline, dict) else None
    harm = HARM.search(plain(article.source_text))
    straight = ", ".join(t.id for t in templates.values() if not joke(t))

    errors: list[str] = []
    if harm and mood != "serious":
        errors.append(
            f"$.headline.mood: the article mentions {harm.group(0)!r}, so this story is "
            f'serious. Set mood to "serious" and use only straight formats ({straight}).'
        )
    if mood != "serious" and not harm:
        return errors

    scenes = storyboard.get("scenes")
    for i, scene in enumerate(scenes if isinstance(scenes, list) else []):
        template = templates.get(scene.get("template")) if isinstance(scene, dict) else None
        if template is not None and joke(template):
            errors.append(
                f"$.scenes[{i}].template: {template.id!r} is a joke format, and this story "
                f"is serious. Use a straight format ({straight}) or drop the scene."
            )
    return errors
