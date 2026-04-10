"""Persistence helpers for migrated legacy-kernel portrait sessions."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import text


class LegacyKernelSessionRepository:
    """Store old profile-helper session snapshots under the new portrait domain."""

    def upsert_session(
        self,
        db_session,
        *,
        portrait_session_id: str,
        legacy_session_id: str,
        user_id: int,
        snapshot_json: str,
        updated_at: datetime,
    ) -> None:
        db_session.execute(
            text(
                """
                INSERT INTO portrait_legacy_kernel_sessions (
                    portrait_session_id, legacy_session_id, user_id,
                    snapshot_json, created_at, updated_at
                )
                VALUES (
                    :portrait_session_id, :legacy_session_id, :user_id,
                    :snapshot_json, :updated_at, :updated_at
                )
                ON CONFLICT(portrait_session_id)
                DO UPDATE SET
                    legacy_session_id = EXCLUDED.legacy_session_id,
                    snapshot_json = EXCLUDED.snapshot_json,
                    updated_at = EXCLUDED.updated_at
                """
            ),
            {
                "portrait_session_id": portrait_session_id,
                "legacy_session_id": legacy_session_id,
                "user_id": user_id,
                "snapshot_json": snapshot_json,
                "updated_at": updated_at,
            },
        )

    def get_session_row(self, db_session, portrait_session_id: str, user_id: int):
        return db_session.execute(
            text(
                """
                SELECT portrait_session_id, legacy_session_id, user_id,
                       snapshot_json, created_at, updated_at
                FROM portrait_legacy_kernel_sessions
                WHERE portrait_session_id = :portrait_session_id
                  AND user_id = :user_id
                LIMIT 1
                """
            ),
            {
                "portrait_session_id": portrait_session_id,
                "user_id": user_id,
            },
        ).fetchone()


legacy_kernel_session_repository = LegacyKernelSessionRepository()
