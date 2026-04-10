"""Portrait-domain router for import-result runtime."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.auth import get_current_user
from app.portrait.schemas.import_results import ImportResultCreateRequest
from app.portrait.services.import_result_service import import_result_service

router = APIRouter(prefix="/portrait/import-results", tags=["portrait-import-results"])


@router.post("")
async def create_import_result(req: ImportResultCreateRequest, user: dict = Depends(get_current_user)):
    return import_result_service.create_import(req, int(user["sub"]))


@router.get("/{import_id}")
async def get_import_result(import_id: str, user: dict = Depends(get_current_user)):
    return import_result_service.get_import(import_id, int(user["sub"]))


@router.post("/{import_id}/parse")
async def parse_import_result(import_id: str, user: dict = Depends(get_current_user)):
    return import_result_service.parse_import(import_id, int(user["sub"]))


@router.get("/{import_id}/parsed")
async def get_import_result_parsed(import_id: str, user: dict = Depends(get_current_user)):
    return import_result_service.get_latest_parsed(import_id, int(user["sub"]))
