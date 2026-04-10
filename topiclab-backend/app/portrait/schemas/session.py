"""Schemas for the unified portrait session orchestrator."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class PortraitSessionStartRequest(BaseModel):
    actor_type: Literal["human", "agent", "internal"] = "human"
    actor_id: str | None = Field(default=None, max_length=255)
    mode: Literal["default", "fast", "deep", "legacy_product"] = "default"
    resume_latest: bool = False


class PortraitSessionRespondRequest(BaseModel):
    choice: int | float | str | None = None
    text: str | None = Field(default=None, max_length=20000)
    external_text: str | None = Field(default=None, max_length=50000)
    external_json: dict[str, Any] | list[Any] | None = None
    confirm: bool = False

    @model_validator(mode="after")
    def validate_payload(self) -> "PortraitSessionRespondRequest":
        used = 0
        if self.choice is not None:
            used += 1
        if self.text and self.text.strip():
            used += 1
        if self.external_text and self.external_text.strip():
            used += 1
        if self.external_json is not None:
            used += 1
        if self.confirm:
            used += 1
        if used != 1:
            raise ValueError("exactly one response input family must be provided")
        return self
