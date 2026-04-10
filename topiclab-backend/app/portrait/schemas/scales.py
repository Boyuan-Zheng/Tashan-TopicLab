"""Portrait-domain schemas for the scale runtime API."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ScaleSessionStartRequest(BaseModel):
    scale_id: str = Field(..., min_length=1, max_length=64)
    actor_type: Literal["human", "agent", "internal"] = "human"
    actor_id: str | None = Field(default=None, max_length=255)


class SingleAnswerRequest(BaseModel):
    question_id: str = Field(..., min_length=1, max_length=64)
    value: float


class BatchAnswerRequest(BaseModel):
    answers: dict[str, float]
