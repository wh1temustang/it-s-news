"""Turn a scene's validated data into what its template draws.

Most formats take their data as is. Quotes lose any quotation marks the
agent copied, since the templates add their own, and only a comment after
the first can be a reply.
"""
from __future__ import annotations

from typing import Callable


def _unquote(text: str) -> str:
    return text.strip().strip("\"'“”‘’").strip()


def change_my_mind(data: dict) -> dict:
    return {**data, "text": _unquote(data["text"])}


def thread(data: dict) -> dict:
    comments = [
        {**c, "text": _unquote(c["text"]), "reply": bool(c.get("reply")) and i > 0}
        for i, c in enumerate(data["comments"])
    ]
    return {**data, "comments": comments}


PREPARE: dict[str, Callable[[dict], dict]] = {
    "change-my-mind": change_my_mind,
    "thread": thread,
}


def prepare(template_id: str, data: dict) -> dict:
    return PREPARE.get(template_id, dict)(data)
