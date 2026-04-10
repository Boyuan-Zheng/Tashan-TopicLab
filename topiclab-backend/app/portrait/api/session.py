"""Portrait-domain router for unified portrait sessions."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.auth import get_current_user
from app.portrait.schemas.session import PortraitSessionRespondRequest, PortraitSessionStartRequest
from app.portrait.services.portrait_session_service import portrait_session_service

router = APIRouter(prefix="/portrait/sessions", tags=["portrait-sessions"])


@router.get("")
async def list_portrait_sessions(
    limit: int = Query(default=20, ge=1, le=100),
    user: dict = Depends(get_current_user),
):
    return portrait_session_service.list_sessions(int(user["sub"]), limit=limit)


@router.post("")
async def start_portrait_session(req: PortraitSessionStartRequest, user: dict = Depends(get_current_user)):
    return portrait_session_service.start_session(req, int(user["sub"]))


@router.get("/{session_id}")
async def get_portrait_session_status(session_id: str, user: dict = Depends(get_current_user)):
    return portrait_session_service.get_status(session_id, int(user["sub"]))


@router.get("/{session_id}/history")
async def get_portrait_session_history(
    session_id: str,
    limit: int = Query(default=20, ge=1, le=100),
    user: dict = Depends(get_current_user),
):
    return portrait_session_service.get_history(session_id, int(user["sub"]), limit=limit)


@router.post("/{session_id}/respond")
async def respond_portrait_session(
    session_id: str,
    req: PortraitSessionRespondRequest,
    user: dict = Depends(get_current_user),
):
    return await portrait_session_service.respond(session_id, req, int(user["sub"]))


@router.get("/{session_id}/result")
async def get_portrait_session_result(session_id: str, user: dict = Depends(get_current_user)):
    return portrait_session_service.get_result(session_id, int(user["sub"]))


@router.post("/{session_id}/reset")
async def reset_portrait_session(session_id: str, user: dict = Depends(get_current_user)):
    return portrait_session_service.reset_session(session_id, int(user["sub"]))
