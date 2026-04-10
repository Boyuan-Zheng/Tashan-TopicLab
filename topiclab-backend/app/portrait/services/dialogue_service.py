"""Portrait-domain dialogue runtime service."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from fastapi import HTTPException

from app.portrait.services.dialogue_generation_service import dialogue_generation_service
from app.portrait.services.dialogue_runtime_service import dialogue_runtime_service
from app.portrait.storage.dialogue_repository import dialogue_repository
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


class DialogueService:
    """Manage durable dialogue sessions and transcript state."""

    def _serialize_session(self, row) -> dict[str, Any]:
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

    def _serialize_message(self, row) -> dict[str, Any]:
        return {
            "message_id": row[0],
            "session_id": row[1],
            "role": row[2],
            "content_text": row[3],
            "content_json": _json_db_load(row[4]),
            "source": row[5],
            "created_at": _to_iso(row[6]),
        }

    def _get_session_row(self, db_session, session_id: str, user_id: int):
        row = dialogue_repository.get_session_row(db_session, session_id, user_id)
        if not row:
            raise HTTPException(status_code=404, detail={"code": "dialogue_session_not_found", "session_id": session_id})
        return row

    def _load_messages(self, db_session, session_id: str) -> list[dict[str, Any]]:
        rows = dialogue_repository.list_message_rows(db_session, session_id)
        return [self._serialize_message(row) for row in rows]

    def _load_or_build_derived_state(self, db_session, session_id: str, session_status: str) -> dict[str, Any]:
        state_row = dialogue_repository.get_state_row(db_session, session_id)
        if state_row:
            return _json_db_load(state_row[2]) or {}
        messages = self._load_messages(db_session, session_id)
        return dialogue_runtime_service.build_derived_state(messages, session_status)

    def _build_progress(self, messages: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "message_count": len(messages),
            "user_message_count": sum(1 for msg in messages if msg["role"] == "user"),
            "assistant_message_count": sum(1 for msg in messages if msg["role"] == "assistant"),
            "system_message_count": sum(1 for msg in messages if msg["role"] == "system"),
        }

    def _allowed_actions(self, status: str) -> list[str]:
        if status == "closed":
            return ["read_messages", "read_derived_state"]
        return ["append_message", "read_messages", "read_derived_state", "close"]

    def _build_message_payload(
        self,
        *,
        message_id: str,
        role: str,
        content_text: str | None,
        content_json: Any,
        source: str,
        created_at: datetime,
        model: str | None = None,
    ) -> dict[str, Any]:
        payload = {
            "message_id": message_id,
            "role": role,
            "content_text": content_text.strip() if isinstance(content_text, str) and content_text else content_text,
            "content_json": content_json,
            "source": source,
            "created_at": created_at.isoformat(),
        }
        if model:
            payload["model"] = model
        return payload

    def _materialize_state(self, db_session, session_row) -> dict[str, Any]:
        session = self._serialize_session(session_row)
        messages = self._load_messages(db_session, session["session_id"])
        derived_state = self._load_or_build_derived_state(db_session, session["session_id"], session["status"])
        return {
            "session": session,
            "progress": self._build_progress(messages),
            "derived_state": derived_state,
            "allowed_actions": self._allowed_actions(session["status"]),
        }

    def _persist_runtime_state(self, db_session, session_id: str, session_status: str) -> dict[str, Any]:
        messages = self._load_messages(db_session, session_id)
        derived_state = dialogue_runtime_service.build_derived_state(messages, session_status)
        now = datetime.now(timezone.utc)
        dialogue_repository.upsert_state(
            db_session,
            session_id=session_id,
            last_message_id=derived_state.get("last_message_id"),
            derived_state_json=_json_db_value(derived_state),
            updated_at=now,
        )
        return derived_state

    def _ensure_session_writable(self, session_row) -> None:
        status = str(session_row[4])
        if status == "closed":
            raise HTTPException(status_code=409, detail={"code": "dialogue_session_closed", "session_id": session_row[0]})

    def start_session(self, actor_type: str | None, actor_id: str | None, user_id: int) -> dict[str, Any]:
        session_id = f"dgs_{uuid4().hex[:16]}"
        now = datetime.now(timezone.utc)
        with get_db_session() as db_session:
            dialogue_repository.insert_session(
                db_session,
                session_id=session_id,
                user_id=user_id,
                actor_type=actor_type or "human",
                actor_id=actor_id,
                created_at=now,
            )
            derived_state = dialogue_runtime_service.build_derived_state([], "initialized")
            dialogue_repository.upsert_state(
                db_session,
                session_id=session_id,
                last_message_id=None,
                derived_state_json=_json_db_value(derived_state),
                updated_at=now,
            )
            row = self._get_session_row(db_session, session_id, user_id)
            return self._materialize_state(db_session, row)

    def get_session_status(self, session_id: str, user_id: int) -> dict[str, Any]:
        with get_db_session() as db_session:
            row = self._get_session_row(db_session, session_id, user_id)
            return self._materialize_state(db_session, row)

    def list_messages(self, session_id: str, user_id: int) -> dict[str, Any]:
        with get_db_session() as db_session:
            row = self._get_session_row(db_session, session_id, user_id)
            state = self._materialize_state(db_session, row)
            state["messages"] = self._load_messages(db_session, session_id)
            return state

    async def append_message(
        self,
        session_id: str,
        role: str,
        content_text: str | None,
        content_json: Any,
        source: str,
        user_id: int,
        *,
        model: str | None = None,
        generate_reply: bool = True,
    ) -> dict[str, Any]:
        accepted_content_text = content_text.strip() if content_text else None
        now = datetime.now(timezone.utc)
        accepted_message_id = f"dlgm_{uuid4().hex[:16]}"

        with get_db_session() as db_session:
            row = self._get_session_row(db_session, session_id, user_id)
            self._ensure_session_writable(row)
            dialogue_repository.insert_message(
                db_session,
                message_id=accepted_message_id,
                session_id=session_id,
                role=role,
                content_text=accepted_content_text,
                content_json=_json_db_value(content_json) if content_json is not None else None,
                source=source,
                created_at=now,
            )
            dialogue_repository.update_session_status(
                db_session,
                session_id=session_id,
                user_id=user_id,
                status="in_progress",
                updated_at=now,
            )
            derived_state = self._persist_runtime_state(db_session, session_id, "in_progress")
            row = self._get_session_row(db_session, session_id, user_id)
            state = self._materialize_state(db_session, row)
            state["accepted_message"] = self._build_message_payload(
                message_id=accepted_message_id,
                role=role,
                content_text=accepted_content_text,
                content_json=content_json,
                source=source,
                created_at=now,
            )
            state["derived_state"] = derived_state
            state["generation_status"] = "skipped"

        if role != "user" or not generate_reply:
            return state

        with get_db_session() as db_session:
            row = self._get_session_row(db_session, session_id, user_id)
            transcript = self._load_messages(db_session, session_id)
            current_derived_state = self._load_or_build_derived_state(db_session, session_id, str(row[4]))

        try:
            generated = await dialogue_generation_service.generate_assistant_reply(
                transcript,
                current_derived_state,
                model=model,
            )
        except Exception as exc:
            state["generation_status"] = "failed"
            state["generation_error"] = {
                "code": "dialogue_generation_failed",
                "message": str(exc),
            }
            return state

        assistant_now = datetime.now(timezone.utc)
        generated_message_id = f"dlgm_{uuid4().hex[:16]}"

        with get_db_session() as db_session:
            row = self._get_session_row(db_session, session_id, user_id)
            self._ensure_session_writable(row)
            dialogue_repository.insert_message(
                db_session,
                message_id=generated_message_id,
                session_id=session_id,
                role="assistant",
                content_text=generated["content"],
                content_json=None,
                source="runtime",
                created_at=assistant_now,
            )
            dialogue_repository.update_session_status(
                db_session,
                session_id=session_id,
                user_id=user_id,
                status="in_progress",
                updated_at=assistant_now,
            )
            derived_state = self._persist_runtime_state(db_session, session_id, "in_progress")
            row = self._get_session_row(db_session, session_id, user_id)
            state = self._materialize_state(db_session, row)
            state["accepted_message"] = self._build_message_payload(
                message_id=accepted_message_id,
                role=role,
                content_text=accepted_content_text,
                content_json=content_json,
                source=source,
                created_at=now,
            )
            state["generated_message"] = self._build_message_payload(
                message_id=generated_message_id,
                role="assistant",
                content_text=generated["content"],
                content_json=None,
                source="runtime",
                created_at=assistant_now,
                model=generated.get("model"),
            )
            state["derived_state"] = derived_state
            state["generation_status"] = "completed"
            return state

    def get_derived_state(self, session_id: str, user_id: int) -> dict[str, Any]:
        with get_db_session() as db_session:
            row = self._get_session_row(db_session, session_id, user_id)
            return {
                "session": self._serialize_session(row),
                "derived_state": self._load_or_build_derived_state(db_session, session_id, str(row[4])),
            }

    def close_session(self, session_id: str, user_id: int) -> dict[str, Any]:
        with get_db_session() as db_session:
            row = self._get_session_row(db_session, session_id, user_id)
            self._ensure_session_writable(row)
            now = datetime.now(timezone.utc)
            dialogue_repository.update_session_status(
                db_session,
                session_id=session_id,
                user_id=user_id,
                status="closed",
                updated_at=now,
                closed_at=now,
            )
            self._persist_runtime_state(db_session, session_id, "closed")
            row = self._get_session_row(db_session, session_id, user_id)
            return self._materialize_state(db_session, row)


dialogue_service = DialogueService()
