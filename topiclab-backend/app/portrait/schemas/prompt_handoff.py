"""Portrait-domain schemas for prompt handoff runtime."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator


class PromptHandoffCreateRequest(BaseModel):
    dialogue_session_id: str | None = Field(default=None, max_length=100)
    portrait_state_id: str | None = Field(default=None, max_length=100)
    prompt_kind: Literal["integrated_portrait", "ai_memory", "external_reflection"] = "integrated_portrait"
    note_text: str | None = Field(default=None, max_length=4000)

    @model_validator(mode="after")
    def validate_payload(self) -> "PromptHandoffCreateRequest":
        if self.dialogue_session_id or self.portrait_state_id or (self.note_text and self.note_text.strip()):
            return self
        raise ValueError("at least one of dialogue_session_id, portrait_state_id, or note_text must be provided")
