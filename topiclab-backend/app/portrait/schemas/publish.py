"""Schemas for publishing portrait projections into twin runtime."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.portrait.schemas.forum import PortraitForumGenerateRequest


class PortraitPublishRequest(BaseModel):
    display_name: str | None = Field(default=None, max_length=255)
    visibility: str = Field(default="private", pattern="^(private|public)$")
    exposure: str = Field(default="brief", pattern="^(brief|full)$")
    source_session_id: str | None = Field(default=None, max_length=100)
    forum_options: PortraitForumGenerateRequest | None = None
