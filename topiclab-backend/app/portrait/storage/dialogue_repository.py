"""Persistence helpers for the portrait-domain dialogue runtime."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import text


class DialogueRepository:
    """Encapsulate SQL for portrait dialogue session persistence."""

    def get_session_row(self, db_session, session_id: str, user_id: int):
        return db_session.execute(
            text(
                """
                SELECT session_id, user_id, actor_type, actor_id, status,
                       created_at, updated_at, closed_at
                FROM portrait_dialogue_sessions
                WHERE session_id = :session_id AND user_id = :user_id
                LIMIT 1
                """
            ),
            {"session_id": session_id, "user_id": user_id},
        ).fetchone()

    def insert_session(
        self,
        db_session,
        *,
        session_id: str,
        user_id: int,
        actor_type: str,
        actor_id: str | None,
        created_at: datetime,
    ) -> None:
        db_session.execute(
            text(
                """
                INSERT INTO portrait_dialogue_sessions (
                    session_id, user_id, actor_type, actor_id, status,
                    created_at, updated_at
                )
                VALUES (
                    :session_id, :user_id, :actor_type, :actor_id, 'initialized',
                    :created_at, :updated_at
                )
                """
            ),
            {
                "session_id": session_id,
                "user_id": user_id,
                "actor_type": actor_type,
                "actor_id": actor_id,
                "created_at": created_at,
                "updated_at": created_at,
            },
        )

    def update_session_status(
        self,
        db_session,
        *,
        session_id: str,
        user_id: int,
        status: str,
        updated_at: datetime,
        closed_at: datetime | None = None,
    ) -> None:
        db_session.execute(
            text(
                """
                UPDATE portrait_dialogue_sessions
                SET status = :status,
                    updated_at = :updated_at,
                    closed_at = COALESCE(:closed_at, closed_at)
                WHERE session_id = :session_id AND user_id = :user_id
                """
            ),
            {
                "session_id": session_id,
                "user_id": user_id,
                "status": status,
                "updated_at": updated_at,
                "closed_at": closed_at,
            },
        )

    def list_message_rows(self, db_session, session_id: str):
        return db_session.execute(
            text(
                """
                SELECT message_id, session_id, role, content_text, content_json, source, created_at
                FROM portrait_dialogue_messages
                WHERE session_id = :session_id
                ORDER BY created_at ASC, id ASC
                """
            ),
            {"session_id": session_id},
        ).fetchall()

    def insert_message(
        self,
        db_session,
        *,
        message_id: str,
        session_id: str,
        role: str,
        content_text: str | None,
        content_json: str | None,
        source: str,
        created_at: datetime,
    ) -> None:
        db_session.execute(
            text(
                """
                INSERT INTO portrait_dialogue_messages (
                    message_id, session_id, role, content_text, content_json, source, created_at
                )
                VALUES (
                    :message_id, :session_id, :role, :content_text, :content_json, :source, :created_at
                )
                """
            ),
            {
                "message_id": message_id,
                "session_id": session_id,
                "role": role,
                "content_text": content_text,
                "content_json": content_json,
                "source": source,
                "created_at": created_at,
            },
        )

    def get_state_row(self, db_session, session_id: str):
        return db_session.execute(
            text(
                """
                SELECT session_id, last_message_id, derived_state_json, updated_at
                FROM portrait_dialogue_states
                WHERE session_id = :session_id
                LIMIT 1
                """
            ),
            {"session_id": session_id},
        ).fetchone()

    def upsert_state(
        self,
        db_session,
        *,
        session_id: str,
        last_message_id: str | None,
        derived_state_json: str,
        updated_at: datetime,
    ) -> None:
        db_session.execute(
            text(
                """
                INSERT INTO portrait_dialogue_states (
                    session_id, last_message_id, derived_state_json, updated_at
                )
                VALUES (
                    :session_id, :last_message_id, :derived_state_json, :updated_at
                )
                ON CONFLICT(session_id)
                DO UPDATE SET
                    last_message_id = EXCLUDED.last_message_id,
                    derived_state_json = EXCLUDED.derived_state_json,
                    updated_at = EXCLUDED.updated_at
                """
            ),
            {
                "session_id": session_id,
                "last_message_id": last_message_id,
                "derived_state_json": derived_state_json,
                "updated_at": updated_at,
            },
        )


dialogue_repository = DialogueRepository()
