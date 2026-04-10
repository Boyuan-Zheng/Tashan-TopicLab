"""Portrait-domain router for the scale runtime."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.auth import get_current_user
from app.portrait.schemas.scales import (
    BatchAnswerRequest,
    ScaleSessionStartRequest,
    SingleAnswerRequest,
)
from app.portrait.services.scales_service import scales_service

router = APIRouter(prefix="/scales", tags=["scales"])


@router.get("")
async def list_scales(user: dict = Depends(get_current_user)):
    _ = user
    return scales_service.list_scales()


@router.post("/sessions")
async def start_session(req: ScaleSessionStartRequest, user: dict = Depends(get_current_user)):
    return scales_service.start_session(req.scale_id, req.actor_type, req.actor_id, int(user["sub"]))


@router.get("/sessions/{session_id}")
async def get_session_status(session_id: str, user: dict = Depends(get_current_user)):
    return scales_service.get_session_status(session_id, int(user["sub"]))


@router.post("/sessions/{session_id}/answers")
async def answer_question(
    session_id: str,
    req: SingleAnswerRequest,
    user: dict = Depends(get_current_user),
):
    return scales_service.answer_question(session_id, req.question_id, req.value, int(user["sub"]))


@router.post("/sessions/{session_id}/answer-batch")
async def answer_batch(
    session_id: str,
    req: BatchAnswerRequest,
    user: dict = Depends(get_current_user),
):
    return scales_service.answer_batch(session_id, req.answers, int(user["sub"]))


@router.post("/sessions/{session_id}/finalize")
async def finalize_session(session_id: str, user: dict = Depends(get_current_user)):
    return scales_service.finalize(session_id, int(user["sub"]))


@router.get("/sessions/{session_id}/result")
async def get_result(session_id: str, user: dict = Depends(get_current_user)):
    return scales_service.get_result(session_id, int(user["sub"]))


@router.get("/sessions")
async def list_sessions(user: dict = Depends(get_current_user)):
    return scales_service.list_sessions(int(user["sub"]))


@router.post("/sessions/{session_id}/abandon")
async def abandon_session(session_id: str, user: dict = Depends(get_current_user)):
    return scales_service.abandon_session(session_id, int(user["sub"]))


@router.get("/{scale_id}")
async def get_scale(scale_id: str, user: dict = Depends(get_current_user)):
    _ = user
    return scales_service.get_scale_definition(scale_id)
