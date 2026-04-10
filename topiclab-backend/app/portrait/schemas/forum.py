"""Schemas for forum-profile generation and export privacy controls."""

from __future__ import annotations

from pydantic import BaseModel, Field


class PortraitForumGenerateRequest(BaseModel):
    display_name: str | None = Field(default=None, max_length=255)
    institution_mode: str = Field(default="category", pattern="^(original|category|omit)$")
    tool_detail_mode: str = Field(default="category", pattern="^(keep|category)$")
    include_cognitive_style: bool = True
    include_motivation: bool = True
    include_personality: bool = True
    include_current_needs: bool = False
    source_session_id: str | None = Field(default=None, max_length=100)
