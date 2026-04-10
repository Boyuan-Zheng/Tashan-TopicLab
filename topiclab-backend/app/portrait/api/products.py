"""Routers for forum / scientist / export / publish portrait product surfaces."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse, Response

from app.api.auth import get_current_user
from app.portrait.schemas.forum import PortraitForumGenerateRequest
from app.portrait.schemas.publish import PortraitPublishRequest
from app.portrait.services.portrait_artifact_service import portrait_artifact_service
from app.portrait.services.portrait_export_service import portrait_export_service
from app.portrait.services.portrait_forum_service import portrait_forum_service
from app.portrait.services.portrait_publish_service import portrait_publish_service
from app.portrait.services.portrait_scientist_service import portrait_scientist_service

router = APIRouter(prefix="/portrait", tags=["portrait-products"])


@router.get("/artifacts")
async def list_portrait_artifacts(
    kind: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    user: dict = Depends(get_current_user),
):
    return portrait_artifact_service.list_artifacts(int(user["sub"]), artifact_kind=kind, limit=limit)


@router.get("/artifacts/{artifact_id}")
async def get_portrait_artifact(artifact_id: str, user: dict = Depends(get_current_user)):
    return portrait_artifact_service.get_artifact(artifact_id, int(user["sub"]))


@router.get("/artifacts/{artifact_id}/download")
async def download_portrait_artifact(artifact_id: str, user: dict = Depends(get_current_user)):
    asset = portrait_artifact_service.get_artifact_download(artifact_id, int(user["sub"]))
    return FileResponse(
        asset["path"],
        media_type=asset["content_type"],
        filename=asset["filename"],
        headers={"X-Portrait-Artifact-Id": asset["artifact"]["artifact_id"]},
    )


@router.post("/forum/generate")
async def generate_portrait_forum_profile(req: PortraitForumGenerateRequest, user: dict = Depends(get_current_user)):
    return portrait_forum_service.generate_forum_profile(
        user_id=int(user["sub"]),
        display_name=req.display_name or user.get("username"),
        institution_mode=req.institution_mode,
        tool_detail_mode=req.tool_detail_mode,
        include_cognitive_style=req.include_cognitive_style,
        include_motivation=req.include_motivation,
        include_personality=req.include_personality,
        include_current_needs=req.include_current_needs,
        source_session_id=req.source_session_id,
    )


@router.get("/scientists/famous")
async def get_portrait_famous_scientists(
    display_name: str | None = Query(default=None),
    source_session_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
):
    return await portrait_scientist_service.generate_famous_match(
        user_id=int(user["sub"]),
        display_name=display_name or user.get("username"),
        source_session_id=source_session_id,
    )


@router.get("/scientists/field")
async def get_portrait_field_scientists(
    display_name: str | None = Query(default=None),
    source_session_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
):
    return await portrait_scientist_service.generate_field_recommendations(
        user_id=int(user["sub"]),
        display_name=display_name or user.get("username"),
        source_session_id=source_session_id,
    )


@router.get("/export/structured")
async def export_portrait_structured(
    display_name: str | None = Query(default=None),
    source_session_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
):
    return portrait_export_service.export_structured(
        user_id=int(user["sub"]),
        display_name=display_name or user.get("username"),
        source_session_id=source_session_id,
    )


@router.get("/export/profile-markdown")
async def export_portrait_markdown(
    display_name: str | None = Query(default=None),
    source_session_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
):
    return portrait_export_service.export_profile_markdown(
        user_id=int(user["sub"]),
        display_name=display_name or user.get("username"),
        source_session_id=source_session_id,
    )


@router.post("/export/forum-markdown")
async def export_portrait_forum_markdown(req: PortraitForumGenerateRequest, user: dict = Depends(get_current_user)):
    return portrait_export_service.export_forum_markdown(
        user_id=int(user["sub"]),
        display_name=req.display_name or user.get("username"),
        source_session_id=req.source_session_id,
        institution_mode=req.institution_mode,
        tool_detail_mode=req.tool_detail_mode,
        include_cognitive_style=req.include_cognitive_style,
        include_motivation=req.include_motivation,
        include_personality=req.include_personality,
        include_current_needs=req.include_current_needs,
    )


@router.get("/export/profile-html")
async def export_portrait_html(
    display_name: str | None = Query(default=None),
    source_session_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
):
    return await portrait_export_service.export_profile_html(
        user_id=int(user["sub"]),
        display_name=display_name or user.get("username"),
        source_session_id=source_session_id,
    )


@router.get("/export/profile-pdf")
async def export_portrait_pdf(
    display_name: str | None = Query(default=None),
    source_session_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
):
    try:
        payload = await portrait_export_service.export_profile_pdf(
            user_id=int(user["sub"]),
            display_name=display_name or user.get("username"),
            source_session_id=source_session_id,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail={"code": "portrait_export_runtime_unavailable", "message": str(exc)}) from exc
    return Response(
        content=payload["media_bytes"],
        media_type=payload["media_type"],
        headers={
            "Content-Disposition": f'attachment; filename="{payload["filename"]}"',
            "X-Portrait-Artifact-Id": payload["artifact"]["artifact_id"],
        },
    )


@router.get("/export/profile-image")
async def export_portrait_image(
    display_name: str | None = Query(default=None),
    source_session_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
):
    try:
        payload = await portrait_export_service.export_profile_image(
            user_id=int(user["sub"]),
            display_name=display_name or user.get("username"),
            source_session_id=source_session_id,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail={"code": "portrait_export_runtime_unavailable", "message": str(exc)}) from exc
    return Response(
        content=payload["media_bytes"],
        media_type=payload["media_type"],
        headers={
            "Content-Disposition": f'attachment; filename="{payload["filename"]}"',
            "X-Portrait-Artifact-Id": payload["artifact"]["artifact_id"],
        },
    )


@router.post("/publish")
async def publish_portrait(req: PortraitPublishRequest, user: dict = Depends(get_current_user)):
    try:
        return portrait_publish_service.publish(
            user_id=int(user["sub"]),
            display_name=req.display_name or user.get("username"),
            visibility=req.visibility,
            exposure=req.exposure,
            source_session_id=req.source_session_id,
            forum_options=req.forum_options.model_dump(exclude_none=True) if req.forum_options else None,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
