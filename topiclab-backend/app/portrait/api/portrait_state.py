"""Portrait-domain router for canonical portrait state runtime."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.auth import get_current_user
from app.portrait.schemas.portrait_state import PortraitStateUpdateRequest
from app.portrait.services.portrait_state_service import portrait_state_service

router = APIRouter(prefix="/portrait/state", tags=["portrait-state"])


@router.get("/current")
async def get_current_portrait_state(user: dict = Depends(get_current_user)):
    return portrait_state_service.get_current_state(int(user["sub"]))


@router.get("/versions")
async def list_portrait_versions(user: dict = Depends(get_current_user)):
    return portrait_state_service.list_versions(int(user["sub"]))


@router.get("/versions/{version_id}")
async def get_portrait_version(version_id: str, user: dict = Depends(get_current_user)):
    return portrait_state_service.get_version(version_id, int(user["sub"]))


@router.post("/updates")
async def apply_portrait_update(req: PortraitStateUpdateRequest, user: dict = Depends(get_current_user)):
    return portrait_state_service.apply_update(req, int(user["sub"]))


@router.get("/updates/{update_id}")
async def get_portrait_update(update_id: str, user: dict = Depends(get_current_user)):
    return portrait_state_service.get_update(update_id, int(user["sub"]))


@router.get("/observations")
async def list_portrait_observations(user: dict = Depends(get_current_user)):
    return portrait_state_service.list_observations(int(user["sub"]))
