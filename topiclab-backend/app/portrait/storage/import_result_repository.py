"""Persistence helpers for import-result runtime."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import text


class ImportResultRepository:
    """Encapsulate SQL for imported external-AI outputs and parse runs."""

    def insert_import_result(
        self,
        db_session,
        *,
        import_id: str,
        user_id: int,
        handoff_id: str | None,
        source_type: str,
        payload_text: str | None,
        payload_json: str | None,
        status: str,
        created_at: datetime,
        updated_at: datetime,
    ) -> None:
        db_session.execute(
            text(
                """
                INSERT INTO portrait_import_results (
                    import_id, user_id, handoff_id, source_type, payload_text,
                    payload_json, status, created_at, updated_at
                )
                VALUES (
                    :import_id, :user_id, :handoff_id, :source_type, :payload_text,
                    :payload_json, :status, :created_at, :updated_at
                )
                """
            ),
            {
                "import_id": import_id,
                "user_id": user_id,
                "handoff_id": handoff_id,
                "source_type": source_type,
                "payload_text": payload_text,
                "payload_json": payload_json,
                "status": status,
                "created_at": created_at,
                "updated_at": updated_at,
            },
        )

    def get_import_row(self, db_session, import_id: str, user_id: int):
        return db_session.execute(
            text(
                """
                SELECT import_id, user_id, handoff_id, source_type, payload_text,
                       payload_json, status, created_at, updated_at
                FROM portrait_import_results
                WHERE import_id = :import_id AND user_id = :user_id
                LIMIT 1
                """
            ),
            {"import_id": import_id, "user_id": user_id},
        ).fetchone()

    def update_import_status(
        self,
        db_session,
        *,
        import_id: str,
        user_id: int,
        status: str,
        updated_at: datetime,
    ) -> None:
        db_session.execute(
            text(
                """
                UPDATE portrait_import_results
                SET status = :status,
                    updated_at = :updated_at
                WHERE import_id = :import_id AND user_id = :user_id
                """
            ),
            {
                "import_id": import_id,
                "user_id": user_id,
                "status": status,
                "updated_at": updated_at,
            },
        )

    def insert_parse_run(
        self,
        db_session,
        *,
        parse_run_id: str,
        import_id: str,
        parser_version: str,
        status: str,
        parsed_output_json: str | None,
        error_text: str | None,
        created_at: datetime,
    ) -> None:
        db_session.execute(
            text(
                """
                INSERT INTO portrait_import_parse_runs (
                    parse_run_id, import_id, parser_version, status,
                    parsed_output_json, error_text, created_at
                )
                VALUES (
                    :parse_run_id, :import_id, :parser_version, :status,
                    :parsed_output_json, :error_text, :created_at
                )
                """
            ),
            {
                "parse_run_id": parse_run_id,
                "import_id": import_id,
                "parser_version": parser_version,
                "status": status,
                "parsed_output_json": parsed_output_json,
                "error_text": error_text,
                "created_at": created_at,
            },
        )

    def get_latest_parse_run_row(self, db_session, import_id: str):
        return db_session.execute(
            text(
                """
                SELECT parse_run_id, import_id, parser_version, status,
                       parsed_output_json, error_text, created_at
                FROM portrait_import_parse_runs
                WHERE import_id = :import_id
                ORDER BY created_at DESC, id DESC
                LIMIT 1
                """
            ),
            {"import_id": import_id},
        ).fetchone()


import_result_repository = ImportResultRepository()
