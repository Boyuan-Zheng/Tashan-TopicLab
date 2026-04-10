"""Portrait-domain canonical state and versioning runtime."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from fastapi import HTTPException

from app.portrait.schemas.portrait_state import PortraitStateUpdateRequest
from app.portrait.services.dialogue_runtime_service import dialogue_runtime_service
from app.portrait.storage.dialogue_repository import dialogue_repository
from app.portrait.storage.import_result_repository import import_result_repository
from app.portrait.storage.portrait_state_repository import portrait_state_repository
from app.portrait.storage.scales_repository import scales_repository
from app.storage.database.postgres_client import get_db_session


def _to_iso(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return value.isoformat()


def _json_db_value(value: Any) -> str:
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


def _deep_merge(base: Any, patch: Any) -> Any:
    if not isinstance(base, dict) or not isinstance(patch, dict):
        return patch
    merged = {**base}
    for key, value in patch.items():
        if key in merged:
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


class PortraitStateService:
    """Manage durable current portrait state, update events, and versions."""

    def _serialize_current_state_row(self, row) -> dict[str, Any]:
        return {
            "portrait_state_id": row[0],
            "user_id": row[1],
            "state_json": _json_db_load(row[2]) or {},
            "source_summary_json": _json_db_load(row[3]) or {},
            "updated_at": _to_iso(row[4]),
        }

    def _serialize_update_row(self, row) -> dict[str, Any]:
        return {
            "update_id": row[0],
            "user_id": row[1],
            "source_type": row[2],
            "source_id": row[3],
            "change_summary_json": _json_db_load(row[4]) or {},
            "created_at": _to_iso(row[5]),
        }

    def _serialize_version_row(self, row) -> dict[str, Any]:
        return {
            "version_id": row[0],
            "user_id": row[1],
            "portrait_state_id": row[2],
            "snapshot_json": _json_db_load(row[3]) or {},
            "created_at": _to_iso(row[4]),
        }

    def _serialize_observation_row(self, row) -> dict[str, Any]:
        return {
            "observation_id": row[0],
            "user_id": row[1],
            "source_type": row[2],
            "source_id": row[3],
            "observation_json": _json_db_load(row[4]) or {},
            "created_at": _to_iso(row[5]),
        }

    def _empty_current_state(self, user_id: int) -> dict[str, Any]:
        return {
            "portrait_state_id": None,
            "user_id": user_id,
            "state_json": {},
            "source_summary_json": {"latest_by_type": {}, "last_update": None},
            "updated_at": None,
        }

    def _get_current_state_or_empty(self, db_session, user_id: int) -> dict[str, Any]:
        row = portrait_state_repository.get_current_state_row(db_session, user_id)
        if not row:
            return self._empty_current_state(user_id)
        return self._serialize_current_state_row(row)

    def _serialize_dialogue_session(self, row) -> dict[str, Any]:
        return {
            "session_id": row[0],
            "user_id": row[1],
            "actor_type": row[2],
            "actor_id": row[3],
            "status": row[4],
            "created_at": _to_iso(row[5]),
            "updated_at": _to_iso(row[6]),
            "closed_at": _to_iso(row[7]),
        }

    def _serialize_scale_session(self, row) -> dict[str, Any]:
        return {
            "session_id": row[0],
            "user_id": row[1],
            "scale_id": row[2],
            "status": row[3],
            "actor_type": row[4],
            "actor_id": row[5],
            "definition_version": row[6],
            "scoring_version": row[7],
            "created_at": _to_iso(row[8]),
            "updated_at": _to_iso(row[9]),
            "completed_at": _to_iso(row[10]),
            "abandoned_at": _to_iso(row[11]),
        }

    def _serialize_scale_result(self, row) -> dict[str, Any]:
        return {
            "session_id": row[0],
            "scale_id": row[1],
            "definition_version": row[2],
            "scoring_version": row[3],
            "answers": _json_db_load(row[4]),
            "dimension_scores": _json_db_load(row[5]),
            "derived_scores": _json_db_load(row[6]),
            "result_summary": _json_db_load(row[7]),
            "completed_at": _to_iso(row[8]),
        }

    def _resolve_dialogue_update(self, db_session, session_id: str, user_id: int) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
        session_row = dialogue_repository.get_session_row(db_session, session_id, user_id)
        if not session_row:
            raise HTTPException(status_code=404, detail={"code": "dialogue_session_not_found", "session_id": session_id})

        message_rows = dialogue_repository.list_message_rows(db_session, session_id)
        messages = [
            {
                "message_id": row[0],
                "role": row[2],
                "content_text": row[3],
                "content_json": _json_db_load(row[4]),
                "source": row[5],
                "created_at": _to_iso(row[6]),
            }
            for row in message_rows
        ]
        state_row = dialogue_repository.get_state_row(db_session, session_id)
        if state_row:
            derived_state = _json_db_load(state_row[2]) or {}
        else:
            derived_state = dialogue_runtime_service.build_derived_state(messages, str(session_row[4]))

        session = self._serialize_dialogue_session(session_row)
        patch = {
            "dialogue": {
                "latest_session": {
                    "session_id": session["session_id"],
                    "status": session["status"],
                    "actor_type": session["actor_type"],
                    "actor_id": session["actor_id"],
                    "updated_at": session["updated_at"],
                    "derived_state": derived_state,
                }
            }
        }
        change_summary = {
            "source_type": "dialogue_session",
            "source_id": session_id,
            "status": session["status"],
            "message_count": derived_state.get("message_count", len(messages)),
            "actor_type": session["actor_type"],
            "actor_id": session["actor_id"],
        }
        observation = {
            "kind": "dialogue_state_materialized",
            "session_id": session_id,
            "summary": derived_state.get("summary", {}),
            "status": derived_state.get("status", session["status"]),
        }
        return patch, change_summary, observation

    def _resolve_scale_update(self, db_session, session_id: str, user_id: int) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
        session_row = scales_repository.get_session_row(db_session, session_id, user_id)
        if not session_row:
            raise HTTPException(status_code=404, detail={"code": "session_not_found", "session_id": session_id})

        result_row = scales_repository.get_result_row(db_session, session_id, user_id)
        if not result_row:
            raise HTTPException(status_code=409, detail={"code": "scale_result_not_found", "session_id": session_id})

        session = self._serialize_scale_session(session_row)
        result = self._serialize_scale_result(result_row)
        scale_id = str(result["scale_id"])
        patch = {
            "scales": {
                "latest_scale_id": scale_id,
                "latest_session_id": session_id,
                "results": {
                    scale_id: {
                        "session_id": session_id,
                        "definition_version": result["definition_version"],
                        "scoring_version": result["scoring_version"],
                        "dimension_scores": result["dimension_scores"],
                        "derived_scores": result["derived_scores"],
                        "result_summary": result["result_summary"],
                        "completed_at": result["completed_at"],
                    }
                },
            }
        }
        change_summary = {
            "source_type": "scale_session",
            "source_id": session_id,
            "scale_id": scale_id,
            "status": session["status"],
            "completed_at": result["completed_at"],
        }
        observation = {
            "kind": "scale_result_materialized",
            "session_id": session_id,
            "scale_id": scale_id,
            "derived_scores": result["derived_scores"],
        }
        return patch, change_summary, observation

    def _resolve_import_result_update(self, db_session, import_id: str, user_id: int) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
        import_row = import_result_repository.get_import_row(db_session, import_id, user_id)
        if not import_row:
            raise HTTPException(status_code=404, detail={"code": "portrait_import_result_not_found", "import_id": import_id})

        parse_row = import_result_repository.get_latest_parse_run_row(db_session, import_id)
        if not parse_row:
            raise HTTPException(status_code=409, detail={"code": "portrait_import_parse_not_found", "import_id": import_id})

        parsed_output = _json_db_load(parse_row[4]) or {}
        candidate_state_patch = parsed_output.get("candidate_state_patch")
        if not isinstance(candidate_state_patch, dict) or not candidate_state_patch:
            raise HTTPException(
                status_code=409,
                detail={"code": "portrait_import_parse_missing_patch", "import_id": import_id},
            )

        patch = {
            "imports": {
                "latest_import_id": import_id,
                "latest_parse_run_id": parse_row[0],
                "latest_parse_kind": parsed_output.get("parse_kind"),
                "results": {
                    import_id: {
                        "handoff_id": import_row[2],
                        "source_type": import_row[3],
                        "status": import_row[6],
                        "parsed_output": parsed_output,
                    }
                },
            }
        }
        patch = _deep_merge(patch, candidate_state_patch)
        change_summary = {
            "source_type": "import_result",
            "source_id": import_id,
            "handoff_id": import_row[2],
            "parse_run_id": parse_row[0],
            "parse_kind": parsed_output.get("parse_kind"),
        }
        observation = {
            "kind": "import_result_materialized",
            "import_id": import_id,
            "handoff_id": import_row[2],
            "parse_run_id": parse_row[0],
            "summary": parsed_output.get("summary", {}),
        }
        return patch, change_summary, observation

    def get_current_state(self, user_id: int) -> dict[str, Any]:
        with get_db_session() as db_session:
            current_state = self._get_current_state_or_empty(db_session, user_id)
            return {
                "current_state": current_state,
                "version_count": portrait_state_repository.count_version_rows(db_session, user_id),
                "update_count": portrait_state_repository.count_update_rows(db_session, user_id),
            }

    def list_versions(self, user_id: int) -> dict[str, Any]:
        with get_db_session() as db_session:
            rows = portrait_state_repository.list_version_rows(db_session, user_id)
            return {"versions": [self._serialize_version_row(row) for row in rows]}

    def get_version(self, version_id: str, user_id: int) -> dict[str, Any]:
        with get_db_session() as db_session:
            row = portrait_state_repository.get_version_row(db_session, version_id, user_id)
            if not row:
                raise HTTPException(status_code=404, detail={"code": "portrait_version_not_found", "version_id": version_id})
            return {"version": self._serialize_version_row(row)}

    def get_update(self, update_id: str, user_id: int) -> dict[str, Any]:
        with get_db_session() as db_session:
            row = portrait_state_repository.get_update_row(db_session, update_id, user_id)
            if not row:
                raise HTTPException(status_code=404, detail={"code": "portrait_update_not_found", "update_id": update_id})
            return {"update": self._serialize_update_row(row)}

    def list_observations(self, user_id: int) -> dict[str, Any]:
        with get_db_session() as db_session:
            rows = portrait_state_repository.list_observation_rows(db_session, user_id)
            return {"observations": [self._serialize_observation_row(row) for row in rows]}

    def apply_update(self, req: PortraitStateUpdateRequest, user_id: int) -> dict[str, Any]:
        update_id = f"pup_{uuid4().hex[:16]}"
        version_id = f"pvs_{uuid4().hex[:16]}"
        observation_id = f"pob_{uuid4().hex[:16]}"
        now = datetime.now(timezone.utc)

        with get_db_session() as db_session:
            current_state = self._get_current_state_or_empty(db_session, user_id)

            if req.source_type == "manual":
                patch = req.state_patch_json or {}
                change_summary = req.change_summary_json or {"source_type": "manual", "source_id": None}
                observation = req.observation_json
            elif req.source_type == "dialogue_session":
                patch, change_summary, observation = self._resolve_dialogue_update(db_session, str(req.source_id), user_id)
                if req.change_summary_json:
                    change_summary = _deep_merge(change_summary, req.change_summary_json)
                if req.observation_json:
                    observation = _deep_merge(observation, req.observation_json)
            elif req.source_type == "scale_session":
                patch, change_summary, observation = self._resolve_scale_update(db_session, str(req.source_id), user_id)
                if req.change_summary_json:
                    change_summary = _deep_merge(change_summary, req.change_summary_json)
                if req.observation_json:
                    observation = _deep_merge(observation, req.observation_json)
            elif req.source_type == "import_result":
                patch, change_summary, observation = self._resolve_import_result_update(db_session, str(req.source_id), user_id)
                if req.change_summary_json:
                    change_summary = _deep_merge(change_summary, req.change_summary_json)
                if req.observation_json:
                    observation = _deep_merge(observation, req.observation_json)
            else:
                raise HTTPException(status_code=400, detail={"code": "unsupported_portrait_update_source", "source_type": req.source_type})

            merged_state_json = _deep_merge(current_state["state_json"], patch)
            portrait_state_id = current_state["portrait_state_id"] or f"pst_{uuid4().hex[:16]}"
            source_summary = current_state["source_summary_json"] or {"latest_by_type": {}, "last_update": None}
            latest_by_type = dict(source_summary.get("latest_by_type") or {})
            latest_by_type[req.source_type] = req.source_id
            source_summary["latest_by_type"] = latest_by_type
            source_summary["last_update"] = {
                "update_id": update_id,
                "source_type": req.source_type,
                "source_id": req.source_id,
                "created_at": now.isoformat(),
            }

            portrait_state_repository.upsert_current_state(
                db_session,
                portrait_state_id=portrait_state_id,
                user_id=user_id,
                state_json=_json_db_value(merged_state_json),
                source_summary_json=_json_db_value(source_summary),
                updated_at=now,
            )
            portrait_state_repository.insert_update_event(
                db_session,
                update_id=update_id,
                user_id=user_id,
                source_type=req.source_type,
                source_id=req.source_id,
                change_summary_json=_json_db_value(change_summary),
                created_at=now,
            )
            portrait_state_repository.insert_version_snapshot(
                db_session,
                version_id=version_id,
                user_id=user_id,
                portrait_state_id=portrait_state_id,
                snapshot_json=_json_db_value(merged_state_json),
                created_at=now,
            )
            serialized_observation = None
            if observation is not None:
                portrait_state_repository.insert_observation(
                    db_session,
                    observation_id=observation_id,
                    user_id=user_id,
                    source_type=req.source_type,
                    source_id=req.source_id,
                    observation_json=_json_db_value(observation),
                    created_at=now,
                )
                observation_row = portrait_state_repository.list_observation_rows(db_session, user_id)[0]
                serialized_observation = self._serialize_observation_row(observation_row)

            current_row = portrait_state_repository.get_current_state_row(db_session, user_id)
            update_row = portrait_state_repository.get_update_row(db_session, update_id, user_id)
            version_row = portrait_state_repository.get_version_row(db_session, version_id, user_id)
            return {
                "current_state": self._serialize_current_state_row(current_row),
                "update": self._serialize_update_row(update_row),
                "version": self._serialize_version_row(version_row),
                "observation": serialized_observation,
            }


portrait_state_service = PortraitStateService()
