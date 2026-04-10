"""OpenAI-compatible sync adapter for the migrated portrait legacy kernel."""

from __future__ import annotations

import os
from types import SimpleNamespace
from typing import Any

from app.services.ai_generation_client import get_ai_generation_runtime_config, post_ai_generation_chat_sync


def _wrap_tool_calls(raw_tool_calls: list[dict[str, Any]] | None) -> list[Any]:
    wrapped: list[Any] = []
    for item in raw_tool_calls or []:
        function = item.get("function") or {}
        wrapped.append(
            SimpleNamespace(
                id=item.get("id") or "",
                type=item.get("type") or "function",
                function=SimpleNamespace(
                    name=function.get("name") or "",
                    arguments=function.get("arguments") or "{}",
                ),
            )
        )
    return wrapped


def _wrap_response(data: dict[str, Any]) -> Any:
    choices = data.get("choices") or []
    if not choices:
        raise ValueError("legacy kernel LLM client received empty choices")
    message = (choices[0] or {}).get("message") or {}
    return SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(
                    content=message.get("content"),
                    tool_calls=_wrap_tool_calls(message.get("tool_calls")),
                )
            )
        ]
    )


class _LegacyChatCompletions:
    def create(
        self,
        *,
        model: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
    ) -> Any:
        payload: dict[str, Any] = {"messages": messages}
        if tools is not None:
            payload["tools"] = tools
        if tool_choice is not None:
            payload["tool_choice"] = tool_choice
        data, _selected_model = post_ai_generation_chat_sync(
            payload,
            model=model,
            timeout=90.0,
        )
        return _wrap_response(data)


class _LegacyChatNamespace:
    def __init__(self) -> None:
        self.completions = _LegacyChatCompletions()


class LegacyKernelClient:
    def __init__(self) -> None:
        self.chat = _LegacyChatNamespace()


def create_client(base_url: str | None = None, api_key: str | None = None) -> LegacyKernelClient | None:
    """Create sync-compatible client for the old profile-helper agent loop."""
    try:
        runtime = get_ai_generation_runtime_config()
    except ValueError:
        runtime = None

    if runtime is None and not (base_url and api_key):
        return None
    return LegacyKernelClient()


def get_default_model() -> str:
    """Return the default model configured for AI generation."""
    try:
        return get_ai_generation_runtime_config().model
    except ValueError:
        return os.getenv("AI_GENERATION_MODEL", "").strip()
