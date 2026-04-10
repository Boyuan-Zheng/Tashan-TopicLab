"""Persistence helpers for derived portrait artifacts."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import text


class PortraitArtifactRepository:
    """Encapsulate SQL for persisted portrait artifacts."""

    def insert_artifact(
        self,
        db_session,
        *,
        artifact_id: str,
        user_id: int,
        portrait_state_id: str | None,
        source_session_id: str | None,
        artifact_kind: str,
        format: str,
        status: str,
        title: str | None,
        content_text: str | None,
        content_json: str | None,
        artifact_filename: str | None,
        artifact_path: str | None,
        artifact_content_type: str | None,
        artifact_size: int,
        metadata_json: str | None,
        created_at: datetime,
        updated_at: datetime,
    ) -> None:
        db_session.execute(
            text(
                """
                INSERT INTO portrait_artifacts (
                    artifact_id, user_id, portrait_state_id, source_session_id,
                    artifact_kind, format, status, title,
                    content_text, content_json,
                    artifact_filename, artifact_path, artifact_content_type, artifact_size,
                    metadata_json,
                    created_at, updated_at
                )
                VALUES (
                    :artifact_id, :user_id, :portrait_state_id, :source_session_id,
                    :artifact_kind, :format, :status, :title,
                    :content_text, :content_json,
                    :artifact_filename, :artifact_path, :artifact_content_type, :artifact_size,
                    :metadata_json,
                    :created_at, :updated_at
                )
                """
            ),
            {
                "artifact_id": artifact_id,
                "user_id": user_id,
                "portrait_state_id": portrait_state_id,
                "source_session_id": source_session_id,
                "artifact_kind": artifact_kind,
                "format": format,
                "status": status,
                "title": title,
                "content_text": content_text,
                "content_json": content_json,
                "artifact_filename": artifact_filename,
                "artifact_path": artifact_path,
                "artifact_content_type": artifact_content_type,
                "artifact_size": artifact_size,
                "metadata_json": metadata_json,
                "created_at": created_at,
                "updated_at": updated_at,
            },
        )

    def get_artifact_row(self, db_session, artifact_id: str, user_id: int):
        return db_session.execute(
            text(
                """
                SELECT artifact_id, user_id, portrait_state_id, source_session_id,
                       artifact_kind, format, status, title,
                       content_text, content_json,
                       artifact_filename, artifact_path, artifact_content_type, artifact_size,
                       metadata_json,
                       created_at, updated_at
                FROM portrait_artifacts
                WHERE artifact_id = :artifact_id AND user_id = :user_id
                LIMIT 1
                """
            ),
            {"artifact_id": artifact_id, "user_id": user_id},
        ).fetchone()

    def list_artifact_rows(self, db_session, user_id: int, *, artifact_kind: str | None = None, limit: int = 20):
        if artifact_kind:
            return db_session.execute(
                text(
                    """
                    SELECT artifact_id, user_id, portrait_state_id, source_session_id,
                           artifact_kind, format, status, title,
                           content_text, content_json,
                           artifact_filename, artifact_path, artifact_content_type, artifact_size,
                           metadata_json,
                           created_at, updated_at
                    FROM portrait_artifacts
                    WHERE user_id = :user_id AND artifact_kind = :artifact_kind
                    ORDER BY created_at DESC, id DESC
                    LIMIT :limit
                    """
                ),
                {"user_id": user_id, "artifact_kind": artifact_kind, "limit": limit},
            ).fetchall()
        return db_session.execute(
            text(
                """
                SELECT artifact_id, user_id, portrait_state_id, source_session_id,
                       artifact_kind, format, status, title,
                       content_text, content_json,
                       artifact_filename, artifact_path, artifact_content_type, artifact_size,
                       metadata_json,
                       created_at, updated_at
                FROM portrait_artifacts
                WHERE user_id = :user_id
                ORDER BY created_at DESC, id DESC
                LIMIT :limit
                """
            ),
            {"user_id": user_id, "limit": limit},
        ).fetchall()


portrait_artifact_repository = PortraitArtifactRepository()
