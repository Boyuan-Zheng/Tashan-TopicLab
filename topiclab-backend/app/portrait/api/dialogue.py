"""Portrait-domain router for the dialogue runtime."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.auth import get_current_user
from app.portrait.schemas.dialogue import DialogueMessageAppendRequest, DialogueSessionStartRequest
from app.portrait.services.dialogue_service import dialogue_service

router = APIRouter(prefix="/portrait/dialogue", tags=["portrait-dialogue"])


@router.post("/sessions")
async def start_dialogue_session(req: DialogueSessionStartRequest, user: dict = Depends(get_current_user)):
    return dialogue_service.start_session(req.actor_type, req.actor_id, int(user["sub"]))


@router.get("/sessions/{session_id}")
async def get_dialogue_session_status(session_id: str, user: dict = Depends(get_current_user)):
    return dialogue_service.get_session_status(session_id, int(user["sub"]))


@router.get("/sessions/{session_id}/messages")
async def list_dialogue_messages(session_id: str, user: dict = Depends(get_current_user)):
    return dialogue_service.list_messages(session_id, int(user["sub"]))


@router.post("/sessions/{session_id}/messages")
async def append_dialogue_message(
    session_id: str,
    req: DialogueMessageAppendRequest,
    user: dict = Depends(get_current_user),
):
    return await dialogue_service.append_message(
        session_id,
        req.role,
        req.content_text,
        req.content_json,
        req.source,
        int(user["sub"]),
        model=req.model,
        generate_reply=req.generate_reply,
    )


@router.get("/sessions/{session_id}/derived-state")
async def get_dialogue_derived_state(session_id: str, user: dict = Depends(get_current_user)):
    return dialogue_service.get_derived_state(session_id, int(user["sub"]))


@router.post("/sessions/{session_id}/close")
async def close_dialogue_session(session_id: str, user: dict = Depends(get_current_user)):
    return dialogue_service.close_session(session_id, int(user["sub"]))
