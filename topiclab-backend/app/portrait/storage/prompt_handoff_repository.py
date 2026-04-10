"""Persistence helpers for prompt handoff runtime."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import text


class PromptHandoffRepository:
    """Encapsulate SQL for prompt handoffs and generated prompt artifacts."""

    def insert_handoff(
        self,
        db_session,
        *,
        handoff_id: str,
        user_id: int,
        dialogue_session_id: str | None,
        portrait_state_id: str | None,
        prompt_kind: str,
        note_text: str | None,
        status: str,
        requested_at: datetime,
        completed_at: datetime | None = None,
        cancelled_at: datetime | None = None,
    ) -> None:
        db_session.execute(
            text(
                """
                INSERT INTO portrait_prompt_handoffs (
                    handoff_id, user_id, dialogue_session_id, portrait_state_id,
                    prompt_kind, note_text, status, requested_at, completed_at, cancelled_at
                )
                VALUES (
                    :handoff_id, :user_id, :dialogue_session_id, :portrait_state_id,
                    :prompt_kind, :note_text, :status, :requested_at, :completed_at, :cancelled_at
                )
                """
            ),
            {
                "handoff_id": handoff_id,
                "user_id": user_id,
                "dialogue_session_id": dialogue_session_id,
                "portrait_state_id": portrait_state_id,
                "prompt_kind": prompt_kind,
                "note_text": note_text,
                "status": status,
                "requested_at": requested_at,
                "completed_at": completed_at,
                "cancelled_at": cancelled_at,
            },
        )

    def list_handoff_rows(self, db_session, user_id: int):
        return db_session.execute(
            text(
                """
                SELECT handoff_id, user_id, dialogue_session_id, portrait_state_id,
                       prompt_kind, note_text, status, requested_at, completed_at, cancelled_at
                FROM portrait_prompt_handoffs
                WHERE user_id = :user_id
                ORDER BY requested_at DESC, id DESC
                """
            ),
            {"user_id": user_id},
        ).fetchall()

    def get_handoff_row(self, db_session, handoff_id: str, user_id: int):
        return db_session.execute(
            text(
                """
                SELECT handoff_id, user_id, dialogue_session_id, portrait_state_id,
                       prompt_kind, note_text, status, requested_at, completed_at, cancelled_at
                FROM portrait_prompt_handoffs
                WHERE handoff_id = :handoff_id AND user_id = :user_id
                LIMIT 1
                """
            ),
            {"handoff_id": handoff_id, "user_id": user_id},
        ).fetchone()

    def update_handoff_status(
        self,
        db_session,
        *,
        handoff_id: str,
        user_id: int,
        status: str,
        completed_at: datetime | None = None,
        cancelled_at: datetime | None = None,
    ) -> None:
        db_session.execute(
            text(
                """
                UPDATE portrait_prompt_handoffs
                SET status = :status,
                    completed_at = COALESCE(:completed_at, completed_at),
                    cancelled_at = COALESCE(:cancelled_at, cancelled_at)
                WHERE handoff_id = :handoff_id AND user_id = :user_id
                """
            ),
            {
                "handoff_id": handoff_id,
                "user_id": user_id,
                "status": status,
                "completed_at": completed_at,
                "cancelled_at": cancelled_at,
            },
        )

    def insert_artifact(
        self,
        db_session,
        *,
        artifact_id: str,
        handoff_id: str,
        artifact_type: str,
        content_text: str | None,
        content_json: str | None,
        created_at: datetime,
    ) -> None:
        db_session.execute(
            text(
                """
                INSERT INTO portrait_prompt_artifacts (
                    artifact_id, handoff_id, artifact_type, content_text, content_json, created_at
                )
                VALUES (
                    :artifact_id, :handoff_id, :artifact_type, :content_text, :content_json, :created_at
                )
                """
            ),
            {
                "artifact_id": artifact_id,
                "handoff_id": handoff_id,
                "artifact_type": artifact_type,
                "content_text": content_text,
                "content_json": content_json,
                "created_at": created_at,
            },
        )

    def list_artifact_rows(self, db_session, handoff_id: str):
        return db_session.execute(
            text(
                """
                SELECT artifact_id, handoff_id, artifact_type, content_text, content_json, created_at
                FROM portrait_prompt_artifacts
                WHERE handoff_id = :handoff_id
                ORDER BY created_at ASC, id ASC
                """
            ),
            {"handoff_id": handoff_id},
        ).fetchall()


prompt_handoff_repository = PromptHandoffRepository()
