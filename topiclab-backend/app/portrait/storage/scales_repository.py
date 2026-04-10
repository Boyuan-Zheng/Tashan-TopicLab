"""Persistence helpers for the portrait-domain scale runtime."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import text


class ScalesRepository:
    """Encapsulate SQL for scale session and result persistence."""

    def get_session_row(self, db_session, session_id: str, user_id: int):
        return db_session.execute(
            text(
                """
                SELECT session_id, user_id, scale_id, status, actor_type, actor_id,
                       definition_version, scoring_version, created_at, updated_at,
                       completed_at, abandoned_at
                FROM scale_sessions
                WHERE session_id = :session_id AND user_id = :user_id
                LIMIT 1
                """
            ),
            {"session_id": session_id, "user_id": user_id},
        ).fetchone()

    def list_session_rows(self, db_session, user_id: int):
        return db_session.execute(
            text(
                """
                SELECT session_id, user_id, scale_id, status, actor_type, actor_id,
                       definition_version, scoring_version, created_at, updated_at,
                       completed_at, abandoned_at
                FROM scale_sessions
                WHERE user_id = :user_id
                ORDER BY updated_at DESC
                """
            ),
            {"user_id": user_id},
        ).fetchall()

    def insert_session(
        self,
        db_session,
        *,
        session_id: str,
        user_id: int,
        scale_id: str,
        actor_type: str,
        actor_id: str | None,
        definition_version: str,
        scoring_version: str,
        created_at: datetime,
    ) -> None:
        db_session.execute(
            text(
                """
                INSERT INTO scale_sessions (
                    session_id, user_id, scale_id, status, actor_type, actor_id,
                    definition_version, scoring_version, created_at, updated_at
                )
                VALUES (
                    :session_id, :user_id, :scale_id, 'initialized', :actor_type, :actor_id,
                    :definition_version, :scoring_version, :created_at, :updated_at
                )
                """
            ),
            {
                "session_id": session_id,
                "user_id": user_id,
                "scale_id": scale_id,
                "actor_type": actor_type,
                "actor_id": actor_id,
                "definition_version": definition_version,
                "scoring_version": scoring_version,
                "created_at": created_at,
                "updated_at": created_at,
            },
        )

    def update_session_status(
        self,
        db_session,
        *,
        session_id: str,
        user_id: int | None,
        status: str,
        updated_at: datetime,
        completed_at: datetime | None = None,
        abandoned_at: datetime | None = None,
    ) -> None:
        params: dict[str, Any] = {
            "session_id": session_id,
            "status": status,
            "updated_at": updated_at,
            "completed_at": completed_at,
            "abandoned_at": abandoned_at,
        }
        if user_id is None:
            where_clause = "WHERE session_id = :session_id"
        else:
            where_clause = "WHERE session_id = :session_id AND user_id = :user_id"
            params["user_id"] = user_id
        db_session.execute(
            text(
                f"""
                UPDATE scale_sessions
                SET status = :status,
                    updated_at = :updated_at,
                    completed_at = COALESCE(:completed_at, completed_at),
                    abandoned_at = COALESCE(:abandoned_at, abandoned_at)
                {where_clause}
                """
            ),
            params,
        )

    def load_answers(self, db_session, session_id: str) -> dict[str, float]:
        rows = db_session.execute(
            text(
                """
                SELECT question_id, value
                FROM scale_session_answers
                WHERE session_id = :session_id
                ORDER BY question_id
                """
            ),
            {"session_id": session_id},
        ).fetchall()
        return {str(row[0]): float(row[1]) for row in rows}

    def upsert_answer(
        self,
        db_session,
        *,
        session_id: str,
        question_id: str,
        value: float,
        answered_at: datetime,
    ) -> None:
        db_session.execute(
            text(
                """
                INSERT INTO scale_session_answers (
                    session_id, question_id, value, answered_at
                )
                VALUES (
                    :session_id, :question_id, :value, :answered_at
                )
                ON CONFLICT(session_id, question_id)
                DO UPDATE SET
                    value = EXCLUDED.value,
                    answered_at = EXCLUDED.answered_at
                """
            ),
            {
                "session_id": session_id,
                "question_id": question_id,
                "value": value,
                "answered_at": answered_at,
            },
        )

    def get_result_row(self, db_session, session_id: str, user_id: int):
        return db_session.execute(
            text(
                """
                SELECT session_id, scale_id, definition_version, scoring_version,
                       answers_json, dimension_scores_json, derived_scores_json,
                       result_summary_json, completed_at
                FROM scale_results
                WHERE session_id = :session_id AND user_id = :user_id
                LIMIT 1
                """
            ),
            {"session_id": session_id, "user_id": user_id},
        ).fetchone()

    def insert_result(
        self,
        db_session,
        *,
        session_id: str,
        user_id: int,
        scale_id: str,
        definition_version: str,
        scoring_version: str,
        answers_json: str,
        dimension_scores_json: str,
        derived_scores_json: str,
        result_summary_json: str,
        completed_at: datetime,
    ) -> None:
        db_session.execute(
            text(
                """
                INSERT INTO scale_results (
                    session_id, user_id, scale_id, definition_version, scoring_version,
                    answers_json, dimension_scores_json, derived_scores_json, result_summary_json, completed_at
                )
                VALUES (
                    :session_id, :user_id, :scale_id, :definition_version, :scoring_version,
                    :answers_json, :dimension_scores_json, :derived_scores_json, :result_summary_json, :completed_at
                )
                """
            ),
            {
                "session_id": session_id,
                "user_id": user_id,
                "scale_id": scale_id,
                "definition_version": definition_version,
                "scoring_version": scoring_version,
                "answers_json": answers_json,
                "dimension_scores_json": dimension_scores_json,
                "derived_scores_json": derived_scores_json,
                "result_summary_json": result_summary_json,
                "completed_at": completed_at,
            },
        )


scales_repository = ScalesRepository()
