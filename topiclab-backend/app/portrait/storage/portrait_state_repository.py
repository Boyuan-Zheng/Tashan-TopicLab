"""Persistence helpers for canonical portrait state runtime."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import text


class PortraitStateRepository:
    """Encapsulate SQL for current portrait state, updates, versions, and observations."""

    def get_current_state_row(self, db_session, user_id: int):
        return db_session.execute(
            text(
                """
                SELECT portrait_state_id, user_id, state_json, source_summary_json, updated_at
                FROM portrait_current_states
                WHERE user_id = :user_id
                LIMIT 1
                """
            ),
            {"user_id": user_id},
        ).fetchone()

    def get_current_state_by_id_row(self, db_session, portrait_state_id: str, user_id: int):
        return db_session.execute(
            text(
                """
                SELECT portrait_state_id, user_id, state_json, source_summary_json, updated_at
                FROM portrait_current_states
                WHERE portrait_state_id = :portrait_state_id AND user_id = :user_id
                LIMIT 1
                """
            ),
            {"portrait_state_id": portrait_state_id, "user_id": user_id},
        ).fetchone()

    def upsert_current_state(
        self,
        db_session,
        *,
        portrait_state_id: str,
        user_id: int,
        state_json: str,
        source_summary_json: str,
        updated_at: datetime,
    ) -> None:
        db_session.execute(
            text(
                """
                INSERT INTO portrait_current_states (
                    portrait_state_id, user_id, state_json, source_summary_json, updated_at
                )
                VALUES (
                    :portrait_state_id, :user_id, :state_json, :source_summary_json, :updated_at
                )
                ON CONFLICT(user_id)
                DO UPDATE SET
                    portrait_state_id = EXCLUDED.portrait_state_id,
                    state_json = EXCLUDED.state_json,
                    source_summary_json = EXCLUDED.source_summary_json,
                    updated_at = EXCLUDED.updated_at
                """
            ),
            {
                "portrait_state_id": portrait_state_id,
                "user_id": user_id,
                "state_json": state_json,
                "source_summary_json": source_summary_json,
                "updated_at": updated_at,
            },
        )

    def insert_update_event(
        self,
        db_session,
        *,
        update_id: str,
        user_id: int,
        source_type: str,
        source_id: str | None,
        change_summary_json: str,
        created_at: datetime,
    ) -> None:
        db_session.execute(
            text(
                """
                INSERT INTO portrait_update_events (
                    update_id, user_id, source_type, source_id, change_summary_json, created_at
                )
                VALUES (
                    :update_id, :user_id, :source_type, :source_id, :change_summary_json, :created_at
                )
                """
            ),
            {
                "update_id": update_id,
                "user_id": user_id,
                "source_type": source_type,
                "source_id": source_id,
                "change_summary_json": change_summary_json,
                "created_at": created_at,
            },
        )

    def get_update_row(self, db_session, update_id: str, user_id: int):
        return db_session.execute(
            text(
                """
                SELECT update_id, user_id, source_type, source_id, change_summary_json, created_at
                FROM portrait_update_events
                WHERE update_id = :update_id AND user_id = :user_id
                LIMIT 1
                """
            ),
            {"update_id": update_id, "user_id": user_id},
        ).fetchone()

    def count_update_rows(self, db_session, user_id: int) -> int:
        row = db_session.execute(
            text(
                """
                SELECT COUNT(*) FROM portrait_update_events
                WHERE user_id = :user_id
                """
            ),
            {"user_id": user_id},
        ).fetchone()
        return int(row[0] if row else 0)

    def insert_version_snapshot(
        self,
        db_session,
        *,
        version_id: str,
        user_id: int,
        portrait_state_id: str,
        snapshot_json: str,
        created_at: datetime,
    ) -> None:
        db_session.execute(
            text(
                """
                INSERT INTO portrait_version_snapshots (
                    version_id, user_id, portrait_state_id, snapshot_json, created_at
                )
                VALUES (
                    :version_id, :user_id, :portrait_state_id, :snapshot_json, :created_at
                )
                """
            ),
            {
                "version_id": version_id,
                "user_id": user_id,
                "portrait_state_id": portrait_state_id,
                "snapshot_json": snapshot_json,
                "created_at": created_at,
            },
        )

    def list_version_rows(self, db_session, user_id: int):
        return db_session.execute(
            text(
                """
                SELECT version_id, user_id, portrait_state_id, snapshot_json, created_at
                FROM portrait_version_snapshots
                WHERE user_id = :user_id
                ORDER BY created_at DESC, id DESC
                """
            ),
            {"user_id": user_id},
        ).fetchall()

    def get_version_row(self, db_session, version_id: str, user_id: int):
        return db_session.execute(
            text(
                """
                SELECT version_id, user_id, portrait_state_id, snapshot_json, created_at
                FROM portrait_version_snapshots
                WHERE version_id = :version_id AND user_id = :user_id
                LIMIT 1
                """
            ),
            {"version_id": version_id, "user_id": user_id},
        ).fetchone()

    def count_version_rows(self, db_session, user_id: int) -> int:
        row = db_session.execute(
            text(
                """
                SELECT COUNT(*) FROM portrait_version_snapshots
                WHERE user_id = :user_id
                """
            ),
            {"user_id": user_id},
        ).fetchone()
        return int(row[0] if row else 0)

    def insert_observation(
        self,
        db_session,
        *,
        observation_id: str,
        user_id: int,
        source_type: str,
        source_id: str | None,
        observation_json: str,
        created_at: datetime,
    ) -> None:
        db_session.execute(
            text(
                """
                INSERT INTO portrait_observations (
                    observation_id, user_id, source_type, source_id, observation_json, created_at
                )
                VALUES (
                    :observation_id, :user_id, :source_type, :source_id, :observation_json, :created_at
                )
                """
            ),
            {
                "observation_id": observation_id,
                "user_id": user_id,
                "source_type": source_type,
                "source_id": source_id,
                "observation_json": observation_json,
                "created_at": created_at,
            },
        )

    def list_observation_rows(self, db_session, user_id: int):
        return db_session.execute(
            text(
                """
                SELECT observation_id, user_id, source_type, source_id, observation_json, created_at
                FROM portrait_observations
                WHERE user_id = :user_id
                ORDER BY created_at DESC, id DESC
                """
            ),
            {"user_id": user_id},
        ).fetchall()


portrait_state_repository = PortraitStateRepository()
