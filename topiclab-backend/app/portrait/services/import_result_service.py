"""Portrait-domain runtime for storing and parsing imported external outputs."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from fastapi import HTTPException

from app.portrait.schemas.portrait_state import PortraitStateUpdateRequest
from app.portrait.schemas.import_results import ImportResultCreateRequest
from app.portrait.services.import_parse_service import import_parse_service
from app.portrait.services.portrait_state_service import portrait_state_service
from app.portrait.storage.import_result_repository import import_result_repository
from app.portrait.storage.prompt_handoff_repository import prompt_handoff_repository
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


class ImportResultService:
    """Store imported AI outputs and deterministic parse runs."""

    def _serialize_import_row(self, row) -> dict[str, Any]:
        return {
            "import_id": row[0],
            "user_id": row[1],
            "handoff_id": row[2],
            "source_type": row[3],
            "payload_text": row[4],
            "payload_json": _json_db_load(row[5]),
            "status": row[6],
            "created_at": _to_iso(row[7]),
            "updated_at": _to_iso(row[8]),
        }

    def _serialize_parse_row(self, row) -> dict[str, Any]:
        return {
            "parse_run_id": row[0],
            "import_id": row[1],
            "parser_version": row[2],
            "status": row[3],
            "parsed_output_json": _json_db_load(row[4]),
            "error_text": row[5],
            "created_at": _to_iso(row[6]),
        }

    def create_import(self, req: ImportResultCreateRequest, user_id: int) -> dict[str, Any]:
        import_id = f"pir_{uuid4().hex[:16]}"
        now = datetime.now(timezone.utc)

        with get_db_session() as db_session:
            if req.handoff_id:
                handoff_row = prompt_handoff_repository.get_handoff_row(db_session, req.handoff_id, user_id)
                if not handoff_row:
                    raise HTTPException(
                        status_code=404,
                        detail={"code": "portrait_prompt_handoff_not_found", "handoff_id": req.handoff_id},
                    )

            import_result_repository.insert_import_result(
                db_session,
                import_id=import_id,
                user_id=user_id,
                handoff_id=req.handoff_id,
                source_type=req.source_type,
                payload_text=req.payload_text,
                payload_json=_json_db_value(req.payload_json),
                status="uploaded",
                created_at=now,
                updated_at=now,
            )
            row = import_result_repository.get_import_row(db_session, import_id, user_id)
            return {"import_result": self._serialize_import_row(row)}

    def get_import(self, import_id: str, user_id: int) -> dict[str, Any]:
        with get_db_session() as db_session:
            row = import_result_repository.get_import_row(db_session, import_id, user_id)
            if not row:
                raise HTTPException(
                    status_code=404,
                    detail={"code": "portrait_import_result_not_found", "import_id": import_id},
                )
            latest_parse = import_result_repository.get_latest_parse_run_row(db_session, import_id)
            return {
                "import_result": self._serialize_import_row(row),
                "latest_parse_run": self._serialize_parse_row(latest_parse) if latest_parse else None,
            }

    def parse_import(self, import_id: str, user_id: int) -> dict[str, Any]:
        parse_run_id = f"ppr_{uuid4().hex[:16]}"
        now = datetime.now(timezone.utc)

        with get_db_session() as db_session:
            row = import_result_repository.get_import_row(db_session, import_id, user_id)
            if not row:
                raise HTTPException(
                    status_code=404,
                    detail={"code": "portrait_import_result_not_found", "import_id": import_id},
                )
            prompt_kind = None
            if row[2]:
                handoff_row = prompt_handoff_repository.get_handoff_row(db_session, str(row[2]), user_id)
                if handoff_row:
                    prompt_kind = handoff_row[4]
            parsed_output = import_parse_service.parse_payload(
                source_type=row[3],
                payload_text=row[4],
                payload_json=_json_db_load(row[5]),
                prompt_kind=prompt_kind,
            )
            import_result_repository.insert_parse_run(
                db_session,
                parse_run_id=parse_run_id,
                import_id=import_id,
                parser_version=import_parse_service.parser_version,
                status="parsed",
                parsed_output_json=_json_db_value(parsed_output),
                error_text=None,
                created_at=now,
            )
            import_result_repository.update_import_status(
                db_session,
                import_id=import_id,
                user_id=user_id,
                status="parsed",
                updated_at=now,
            )
            # The later portrait_state materialization opens its own DB session.
            # Commit here so the new parse run is visible across sessions.
            db_session.commit()
            updated_row = import_result_repository.get_import_row(db_session, import_id, user_id)
            parse_row = import_result_repository.get_latest_parse_run_row(db_session, import_id)
            state_update = portrait_state_service.apply_update(
                PortraitStateUpdateRequest(
                    source_type="import_result",
                    source_id=import_id,
                ),
                user_id,
            )
            return {
                "import_result": self._serialize_import_row(updated_row),
                "parse_run": self._serialize_parse_row(parse_row),
                "state_update": state_update,
                "auto_applied_to_portrait_state": True,
            }

    def get_latest_parsed(self, import_id: str, user_id: int) -> dict[str, Any]:
        with get_db_session() as db_session:
            row = import_result_repository.get_import_row(db_session, import_id, user_id)
            if not row:
                raise HTTPException(
                    status_code=404,
                    detail={"code": "portrait_import_result_not_found", "import_id": import_id},
                )
            parse_row = import_result_repository.get_latest_parse_run_row(db_session, import_id)
            if not parse_row:
                raise HTTPException(
                    status_code=404,
                    detail={"code": "portrait_import_parse_not_found", "import_id": import_id},
                )
            return {
                "import_result": self._serialize_import_row(row),
                "parse_run": self._serialize_parse_row(parse_row),
            }


import_result_service = ImportResultService()
