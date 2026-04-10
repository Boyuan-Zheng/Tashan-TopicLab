"""Portrait-domain router for prompt handoff runtime."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.auth import get_current_user
from app.portrait.schemas.prompt_handoff import PromptHandoffCreateRequest
from app.portrait.services.prompt_handoff_service import prompt_handoff_service

router = APIRouter(prefix="/portrait/prompt-handoffs", tags=["portrait-prompt-handoffs"])


@router.post("")
async def create_prompt_handoff(req: PromptHandoffCreateRequest, user: dict = Depends(get_current_user)):
    return prompt_handoff_service.create_handoff(req, int(user["sub"]))


@router.get("")
async def list_prompt_handoffs(user: dict = Depends(get_current_user)):
    return prompt_handoff_service.list_handoffs(int(user["sub"]))


@router.get("/{handoff_id}")
async def get_prompt_handoff(handoff_id: str, user: dict = Depends(get_current_user)):
    return prompt_handoff_service.get_handoff(handoff_id, int(user["sub"]))


@router.post("/{handoff_id}/cancel")
async def cancel_prompt_handoff(handoff_id: str, user: dict = Depends(get_current_user)):
    return prompt_handoff_service.cancel_handoff(handoff_id, int(user["sub"]))
