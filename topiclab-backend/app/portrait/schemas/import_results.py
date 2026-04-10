"""Portrait-domain schemas for import-result runtime."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class ImportResultCreateRequest(BaseModel):
    handoff_id: str | None = Field(default=None, max_length=100)
    source_type: Literal["external_ai_text", "external_ai_json", "manual"] = "external_ai_text"
    payload_text: str | None = Field(default=None, max_length=50000)
    payload_json: dict[str, Any] | list[Any] | None = None

    @model_validator(mode="after")
    def validate_payload(self) -> "ImportResultCreateRequest":
        if self.payload_text and self.payload_text.strip():
            return self
        if self.payload_json is not None:
            return self
        raise ValueError("either payload_text or payload_json must be provided")
