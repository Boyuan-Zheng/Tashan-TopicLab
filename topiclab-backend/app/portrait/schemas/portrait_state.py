"""Portrait-domain schemas for canonical portrait state runtime."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class PortraitStateUpdateRequest(BaseModel):
    source_type: Literal["manual", "dialogue_session", "scale_session", "import_result"]
    source_id: str | None = Field(default=None, max_length=100)
    state_patch_json: dict[str, Any] | None = None
    change_summary_json: dict[str, Any] | None = None
    observation_json: dict[str, Any] | None = None

    @model_validator(mode="after")
    def validate_payload(self) -> "PortraitStateUpdateRequest":
        if self.source_type == "manual":
            if not self.state_patch_json:
                raise ValueError("manual portrait updates require state_patch_json")
            return self
        if not self.source_id or not self.source_id.strip():
            raise ValueError("source_id is required for non-manual portrait updates")
        return self
