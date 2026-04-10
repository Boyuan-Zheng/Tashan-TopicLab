"""Derived runtime-state helpers for the portrait dialogue runtime."""

from __future__ import annotations

from typing import Any

from app.portrait.services.dialogue_summary_service import build_dialogue_summary


class DialogueRuntimeService:
    """Build deterministic dialogue runtime state from transcript rows."""

    def build_derived_state(self, messages: list[dict[str, Any]], session_status: str) -> dict[str, Any]:
        message_count = len(messages)
        last_message = messages[-1] if messages else None
        summary = build_dialogue_summary(messages)

        return {
            "status": session_status,
            "message_count": message_count,
            "last_message_id": last_message.get("message_id") if last_message else None,
            "last_role": last_message.get("role") if last_message else None,
            "has_user_input": summary["user_message_count"] > 0,
            "has_assistant_output": summary["assistant_message_count"] > 0,
            "summary": summary,
        }


dialogue_runtime_service = DialogueRuntimeService()
