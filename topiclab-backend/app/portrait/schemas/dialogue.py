"""Portrait-domain schemas for the dialogue runtime API."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class DialogueSessionStartRequest(BaseModel):
    actor_type: Literal["human", "agent", "internal"] = "human"
    actor_id: str | None = Field(default=None, max_length=255)


class DialogueMessageAppendRequest(BaseModel):
    role: Literal["user", "assistant", "system"] = "user"
    content_text: str | None = Field(default=None, max_length=20000)
    content_json: dict[str, Any] | list[Any] | None = None
    source: str = Field(default="cli", min_length=1, max_length=64)
    model: str | None = Field(default=None, max_length=128)
    generate_reply: bool = True

    @model_validator(mode="after")
    def validate_payload(self) -> "DialogueMessageAppendRequest":
        if self.content_text and self.content_text.strip():
            return self
        if self.content_json is not None:
            return self
        raise ValueError("either content_text or content_json must be provided")
