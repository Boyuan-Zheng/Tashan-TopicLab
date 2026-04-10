"""Derived portrait artifact persistence service."""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import HTTPException

from app.portrait.storage.portrait_artifact_repository import portrait_artifact_repository
from app.storage.database.postgres_client import get_db_session


def _to_iso(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return value.isoformat()


def _json_db_value(value: Any) -> str | None:
    if value is None:
        return None
    return json.dumps(value, ensure_ascii=False)


def _json_db_load(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, (bytes, bytearray)):
        value = value.decode("utf-8")
    if isinstance(value, str):
        return json.loads(value)
    return value


def _artifact_storage_dir() -> Path:
    configured = os.getenv("PORTRAIT_ARTIFACT_STORAGE_DIR", "").strip()
    if configured:
        base = Path(configured)
    else:
        base = Path(__file__).resolve().parents[3] / "storage" / "portrait_artifacts"
    base.mkdir(parents=True, exist_ok=True)
    return base


def _sanitize_filename(value: str, fallback: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", (value or "").strip()).strip(".-")
    return cleaned or fallback


def _safe_download_filename(artifact_id: str, file_name: str | None, fallback_suffix: str = ".bin") -> str:
    candidate = (file_name or "").strip()
    if candidate:
        return _sanitize_filename(candidate, f"{artifact_id}{fallback_suffix}")
    return f"{artifact_id}{fallback_suffix}"


class PortraitArtifactService:
    """Manage durable artifact reads and writes."""

    def _serialize_row(self, row) -> dict[str, Any]:
        artifact_id = row[0]
        artifact_path = row[11]
        return {
            "artifact_id": artifact_id,
            "user_id": row[1],
            "portrait_state_id": row[2],
            "source_session_id": row[3],
            "artifact_kind": row[4],
            "format": row[5],
            "status": row[6],
            "title": row[7],
            "content_text": row[8],
            "content_json": _json_db_load(row[9]),
            "artifact_filename": row[10],
            "artifact_content_type": row[12],
            "artifact_size": int(row[13] or 0),
            "download_url": f"/api/v1/portrait/artifacts/{artifact_id}/download" if artifact_path else None,
            "binary_available": bool(artifact_path),
            "metadata_json": _json_db_load(row[14]) or {},
            "created_at": _to_iso(row[15]),
            "updated_at": _to_iso(row[16]),
        }

    def _insert_artifact_row(
        self,
        *,
        artifact_id: str,
        user_id: int,
        artifact_kind: str,
        format: str,
        status: str,
        title: str | None,
        portrait_state_id: str | None,
        source_session_id: str | None,
        content_text: str | None,
        content_json: Any,
        artifact_filename: str | None,
        artifact_path: str | None,
        artifact_content_type: str | None,
        artifact_size: int,
        metadata_json: Any,
    ) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        with get_db_session() as db_session:
            portrait_artifact_repository.insert_artifact(
                db_session,
                artifact_id=artifact_id,
                user_id=user_id,
                portrait_state_id=portrait_state_id,
                source_session_id=source_session_id,
                artifact_kind=artifact_kind,
                format=format,
                status=status,
                title=title,
                content_text=content_text,
                content_json=_json_db_value(content_json),
                artifact_filename=artifact_filename,
                artifact_path=artifact_path,
                artifact_content_type=artifact_content_type,
                artifact_size=max(0, int(artifact_size)),
                metadata_json=_json_db_value(metadata_json),
                created_at=now,
                updated_at=now,
            )
            row = portrait_artifact_repository.get_artifact_row(db_session, artifact_id, user_id)
            assert row is not None
            return self._serialize_row(row)

    def _persist_binary_payload(
        self,
        *,
        artifact_id: str,
        user_id: int,
        file_name: str | None,
        content_type: str | None,
        payload: bytes,
    ) -> dict[str, Any]:
        safe_name = _safe_download_filename(artifact_id, file_name)
        user_dir = _artifact_storage_dir() / f"user-{user_id}"
        user_dir.mkdir(parents=True, exist_ok=True)
        target = user_dir / f"{artifact_id}-{safe_name}"
        target.write_bytes(payload)
        return {
            "filename": safe_name,
            "path": str(target),
            "content_type": (content_type or "application/octet-stream").strip() or "application/octet-stream",
            "size": len(payload),
        }

    def record_artifact(
        self,
        *,
        user_id: int,
        artifact_kind: str,
        format: str,
        status: str = "ready",
        title: str | None = None,
        portrait_state_id: str | None = None,
        source_session_id: str | None = None,
        content_text: str | None = None,
        content_json: Any = None,
        metadata_json: Any = None,
    ) -> dict[str, Any]:
        artifact_id = f"par_{uuid4().hex[:16]}"
        return self._insert_artifact_row(
            artifact_id=artifact_id,
            user_id=user_id,
            portrait_state_id=portrait_state_id,
            source_session_id=source_session_id,
            artifact_kind=artifact_kind,
            format=format,
            status=status,
            title=title,
            content_text=content_text,
            content_json=content_json,
            artifact_filename=None,
            artifact_path=None,
            artifact_content_type=None,
            artifact_size=0,
            metadata_json=metadata_json,
        )

    def record_binary_artifact(
        self,
        *,
        user_id: int,
        artifact_kind: str,
        title: str | None,
        file_name: str | None,
        content_type: str | None,
        payload: bytes,
        format: str = "binary",
        status: str = "ready",
        portrait_state_id: str | None = None,
        source_session_id: str | None = None,
        metadata_json: Any = None,
    ) -> dict[str, Any]:
        artifact_id = f"par_{uuid4().hex[:16]}"
        persisted = self._persist_binary_payload(
            artifact_id=artifact_id,
            user_id=user_id,
            file_name=file_name,
            content_type=content_type,
            payload=payload,
        )
        return self._insert_artifact_row(
            artifact_id=artifact_id,
            user_id=user_id,
            portrait_state_id=portrait_state_id,
            source_session_id=source_session_id,
            artifact_kind=artifact_kind,
            format=format,
            status=status,
            title=title,
            content_text=None,
            content_json=None,
            artifact_filename=persisted["filename"],
            artifact_path=persisted["path"],
            artifact_content_type=persisted["content_type"],
            artifact_size=persisted["size"],
            metadata_json=metadata_json,
        )

    def get_artifact(self, artifact_id: str, user_id: int) -> dict[str, Any]:
        with get_db_session() as db_session:
            row = portrait_artifact_repository.get_artifact_row(db_session, artifact_id, user_id)
            if not row:
                raise HTTPException(status_code=404, detail={"code": "portrait_artifact_not_found", "artifact_id": artifact_id})
            return {"artifact": self._serialize_row(row)}

    def get_artifact_download(self, artifact_id: str, user_id: int) -> dict[str, Any]:
        with get_db_session() as db_session:
            row = portrait_artifact_repository.get_artifact_row(db_session, artifact_id, user_id)
            if not row:
                raise HTTPException(status_code=404, detail={"code": "portrait_artifact_not_found", "artifact_id": artifact_id})
            artifact_path = row[11]
            if not artifact_path:
                raise HTTPException(
                    status_code=404,
                    detail={"code": "portrait_artifact_binary_unavailable", "artifact_id": artifact_id},
                )
            resolved = Path(str(artifact_path))
            if not resolved.exists():
                raise HTTPException(
                    status_code=404,
                    detail={"code": "portrait_artifact_file_missing", "artifact_id": artifact_id},
                )
            return {
                "path": str(resolved),
                "filename": row[10] or f"{artifact_id}.bin",
                "content_type": row[12] or "application/octet-stream",
                "artifact_size": int(row[13] or resolved.stat().st_size),
                "artifact": self._serialize_row(row),
            }

    def list_artifacts(self, user_id: int, *, artifact_kind: str | None = None, limit: int = 20) -> dict[str, Any]:
        with get_db_session() as db_session:
            rows = portrait_artifact_repository.list_artifact_rows(
                db_session,
                user_id,
                artifact_kind=artifact_kind,
                limit=limit,
            )
            return {"artifacts": [self._serialize_row(row) for row in rows]}


portrait_artifact_service = PortraitArtifactService()
