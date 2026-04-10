"""Small summary helpers for the portrait dialogue runtime."""

from __future__ import annotations

from typing import Any


def _trim(value: str | None, limit: int = 160) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    if len(stripped) <= limit:
        return stripped
    return f"{stripped[: limit - 3]}..."


def build_dialogue_summary(messages: list[dict[str, Any]]) -> dict[str, Any]:
    """Build a lightweight summary from the current transcript.

    This is intentionally conservative in the first batch. It does not attempt
    to replace true LLM summarization. It only provides enough normalized shape
    for durable runtime state and later orchestration.
    """

    user_messages = [msg for msg in messages if msg.get("role") == "user"]
    assistant_messages = [msg for msg in messages if msg.get("role") == "assistant"]

    first_user_text = next((msg.get("content_text") for msg in user_messages if msg.get("content_text")), None)
    last_user_text = next((msg.get("content_text") for msg in reversed(user_messages) if msg.get("content_text")), None)
    last_assistant_text = next(
        (msg.get("content_text") for msg in reversed(assistant_messages) if msg.get("content_text")),
        None,
    )

    return {
        "first_user_message": _trim(first_user_text),
        "last_user_message": _trim(last_user_text),
        "last_assistant_message": _trim(last_assistant_text),
        "user_message_count": len(user_messages),
        "assistant_message_count": len(assistant_messages),
    }
