"""Derived portrait artifact persistence service."""

from __future__ import annotations

import json
from datetime import datetime, timezone
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


class PortraitArtifactService:
    """Manage durable artifact reads and writes."""

    def _serialize_row(self, row) -> dict[str, Any]:
        return {
            "artifact_id": row[0],
            "user_id": row[1],
            "portrait_state_id": row[2],
            "source_session_id": row[3],
            "artifact_kind": row[4],
            "format": row[5],
            "status": row[6],
            "title": row[7],
            "content_text": row[8],
            "content_json": _json_db_load(row[9]),
            "metadata_json": _json_db_load(row[10]) or {},
            "created_at": _to_iso(row[11]),
            "updated_at": _to_iso(row[12]),
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
                metadata_json=_json_db_value(metadata_json),
                created_at=now,
                updated_at=now,
            )
            row = portrait_artifact_repository.get_artifact_row(db_session, artifact_id, user_id)
            assert row is not None
            return self._serialize_row(row)

    def get_artifact(self, artifact_id: str, user_id: int) -> dict[str, Any]:
        with get_db_session() as db_session:
            row = portrait_artifact_repository.get_artifact_row(db_session, artifact_id, user_id)
            if not row:
                raise HTTPException(status_code=404, detail={"code": "portrait_artifact_not_found", "artifact_id": artifact_id})
            return {"artifact": self._serialize_row(row)}

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
