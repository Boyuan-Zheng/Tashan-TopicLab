"""Persistence helpers for the unified portrait session orchestrator."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import text


class PortraitSessionRepository:
    """Encapsulate SQL for top-level portrait session orchestration tables."""

    def insert_session(
        self,
        db_session,
        *,
        session_id: str,
        user_id: int,
        actor_type: str,
        actor_id: str | None,
        mode: str,
        status: str,
        current_stage: str,
        current_input_kind: str,
        current_message: str,
        current_payload_json: str | None,
        current_next_hint: str | None,
        result_preview_json: str | None,
        created_at: datetime,
    ) -> None:
        db_session.execute(
            text(
                """
                INSERT INTO portrait_sessions (
                    session_id, user_id, actor_type, actor_id, mode, status,
                    current_stage, current_input_kind, current_message,
                    current_payload_json, current_next_hint, result_preview_json,
                    created_at, updated_at
                )
                VALUES (
                    :session_id, :user_id, :actor_type, :actor_id, :mode, :status,
                    :current_stage, :current_input_kind, :current_message,
                    :current_payload_json, :current_next_hint, :result_preview_json,
                    :created_at, :updated_at
                )
                """
            ),
            {
                "session_id": session_id,
                "user_id": user_id,
                "actor_type": actor_type,
                "actor_id": actor_id,
                "mode": mode,
                "status": status,
                "current_stage": current_stage,
                "current_input_kind": current_input_kind,
                "current_message": current_message,
                "current_payload_json": current_payload_json,
                "current_next_hint": current_next_hint,
                "result_preview_json": result_preview_json,
                "created_at": created_at,
                "updated_at": created_at,
            },
        )

    def get_session_row(self, db_session, session_id: str, user_id: int):
        return db_session.execute(
            text(
                """
                SELECT session_id, user_id, actor_type, actor_id, mode, status,
                       current_stage, current_input_kind, current_message,
                       current_payload_json, current_next_hint, result_preview_json,
                       created_at, updated_at, closed_at
                FROM portrait_sessions
                WHERE session_id = :session_id AND user_id = :user_id
                LIMIT 1
                """
            ),
            {"session_id": session_id, "user_id": user_id},
        ).fetchone()

    def get_latest_active_session_row(self, db_session, user_id: int):
        return db_session.execute(
            text(
                """
                SELECT session_id, user_id, actor_type, actor_id, mode, status,
                       current_stage, current_input_kind, current_message,
                       current_payload_json, current_next_hint, result_preview_json,
                       created_at, updated_at, closed_at
                FROM portrait_sessions
                WHERE user_id = :user_id
                  AND status IN ('active', 'initialized')
                ORDER BY updated_at DESC, id DESC
                LIMIT 1
                """
            ),
            {"user_id": user_id},
        ).fetchone()

    def list_session_rows(self, db_session, user_id: int, *, limit: int):
        return db_session.execute(
            text(
                """
                SELECT session_id, user_id, actor_type, actor_id, mode, status,
                       current_stage, current_input_kind, current_message,
                       current_payload_json, current_next_hint, result_preview_json,
                       created_at, updated_at, closed_at
                FROM portrait_sessions
                WHERE user_id = :user_id
                ORDER BY updated_at DESC, id DESC
                LIMIT :limit
                """
            ),
            {"user_id": user_id, "limit": limit},
        ).fetchall()

    def update_session_state(
        self,
        db_session,
        *,
        session_id: str,
        user_id: int,
        status: str,
        current_stage: str,
        current_input_kind: str,
        current_message: str,
        current_payload_json: str | None,
        current_next_hint: str | None,
        result_preview_json: str | None,
        updated_at: datetime,
        closed_at: datetime | None = None,
    ) -> None:
        db_session.execute(
            text(
                """
                UPDATE portrait_sessions
                SET status = :status,
                    current_stage = :current_stage,
                    current_input_kind = :current_input_kind,
                    current_message = :current_message,
                    current_payload_json = :current_payload_json,
                    current_next_hint = :current_next_hint,
                    result_preview_json = :result_preview_json,
                    updated_at = :updated_at,
                    closed_at = COALESCE(:closed_at, closed_at)
                WHERE session_id = :session_id AND user_id = :user_id
                """
            ),
            {
                "session_id": session_id,
                "user_id": user_id,
                "status": status,
                "current_stage": current_stage,
                "current_input_kind": current_input_kind,
                "current_message": current_message,
                "current_payload_json": current_payload_json,
                "current_next_hint": current_next_hint,
                "result_preview_json": result_preview_json,
                "updated_at": updated_at,
                "closed_at": closed_at,
            },
        )

    def upsert_runtime_ref(
        self,
        db_session,
        *,
        session_id: str,
        user_id: int,
        ref_kind: str,
        ref_value: str,
        metadata_json: str | None,
        updated_at: datetime,
    ) -> None:
        db_session.execute(
            text(
                """
                INSERT INTO portrait_session_runtime_refs (
                    session_id, user_id, ref_kind, ref_value, metadata_json, created_at, updated_at
                )
                VALUES (
                    :session_id, :user_id, :ref_kind, :ref_value, :metadata_json, :updated_at, :updated_at
                )
                ON CONFLICT(session_id, ref_kind)
                DO UPDATE SET
                    ref_value = EXCLUDED.ref_value,
                    metadata_json = EXCLUDED.metadata_json,
                    updated_at = EXCLUDED.updated_at
                """
            ),
            {
                "session_id": session_id,
                "user_id": user_id,
                "ref_kind": ref_kind,
                "ref_value": ref_value,
                "metadata_json": metadata_json,
                "updated_at": updated_at,
            },
        )

    def list_runtime_ref_rows(self, db_session, session_id: str):
        return db_session.execute(
            text(
                """
                SELECT session_id, user_id, ref_kind, ref_value, metadata_json, created_at, updated_at
                FROM portrait_session_runtime_refs
                WHERE session_id = :session_id
                ORDER BY created_at ASC, id ASC
                """
            ),
            {"session_id": session_id},
        ).fetchall()

    def insert_event(
        self,
        db_session,
        *,
        event_id: str,
        session_id: str,
        user_id: int,
        event_type: str,
        event_json: str,
        created_at: datetime,
    ) -> None:
        db_session.execute(
            text(
                """
                INSERT INTO portrait_session_events (
                    event_id, session_id, user_id, event_type, event_json, created_at
                )
                VALUES (
                    :event_id, :session_id, :user_id, :event_type, :event_json, :created_at
                )
                """
            ),
            {
                "event_id": event_id,
                "session_id": session_id,
                "user_id": user_id,
                "event_type": event_type,
                "event_json": event_json,
                "created_at": created_at,
            },
        )

    def count_event_rows(self, db_session, session_id: str) -> int:
        row = db_session.execute(
            text(
                """
                SELECT COUNT(*)
                FROM portrait_session_events
                WHERE session_id = :session_id
                """
            ),
            {"session_id": session_id},
        ).fetchone()
        return int(row[0] if row else 0)

    def list_event_rows(self, db_session, session_id: str, *, limit: int):
        return db_session.execute(
            text(
                """
                SELECT event_id, session_id, user_id, event_type, event_json, created_at
                FROM portrait_session_events
                WHERE session_id = :session_id
                ORDER BY created_at DESC, id DESC
                LIMIT :limit
                """
            ),
            {"session_id": session_id, "limit": limit},
        ).fetchall()


portrait_session_repository = PortraitSessionRepository()
