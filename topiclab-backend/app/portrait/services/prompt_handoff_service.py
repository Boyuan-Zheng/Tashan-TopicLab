"""Portrait-domain runtime for generating prompt handoffs to external AI systems."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from fastapi import HTTPException

from app.portrait.runtime.ai_memory_prompt_loader import load_ai_memory_prompt
from app.portrait.schemas.prompt_handoff import PromptHandoffCreateRequest
from app.portrait.storage.dialogue_repository import dialogue_repository
from app.portrait.storage.portrait_state_repository import portrait_state_repository
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


class PromptHandoffService:
    """Create durable prompt handoffs from dialogue and portrait-state inputs."""

    def _serialize_handoff_row(self, row) -> dict[str, Any]:
        return {
            "handoff_id": row[0],
            "user_id": row[1],
            "dialogue_session_id": row[2],
            "portrait_state_id": row[3],
            "prompt_kind": row[4],
            "note_text": row[5],
            "status": row[6],
            "requested_at": _to_iso(row[7]),
            "completed_at": _to_iso(row[8]),
            "cancelled_at": _to_iso(row[9]),
        }

    def _serialize_artifact_row(self, row) -> dict[str, Any]:
        return {
            "artifact_id": row[0],
            "handoff_id": row[1],
            "artifact_type": row[2],
            "content_text": row[3],
            "content_json": _json_db_load(row[4]),
            "created_at": _to_iso(row[5]),
        }

    def _load_dialogue_context(self, db_session, session_id: str, user_id: int) -> dict[str, Any]:
        session_row = dialogue_repository.get_session_row(db_session, session_id, user_id)
        if not session_row:
            raise HTTPException(
                status_code=404,
                detail={"code": "dialogue_session_not_found", "session_id": session_id},
            )
        message_rows = dialogue_repository.list_message_rows(db_session, session_id)
        messages: list[dict[str, Any]] = []
        for row in message_rows:
            messages.append(
                {
                    "message_id": row[0],
                    "role": row[2],
                    "content_text": row[3],
                    "content_json": _json_db_load(row[4]),
                    "source": row[5],
                    "created_at": _to_iso(row[6]),
                }
            )
        return {
            "session_id": session_row[0],
            "actor_type": session_row[2],
            "actor_id": session_row[3],
            "status": session_row[4],
            "messages": messages,
        }

    def _load_portrait_state_context(self, db_session, portrait_state_id: str, user_id: int) -> dict[str, Any]:
        row = portrait_state_repository.get_current_state_by_id_row(db_session, portrait_state_id, user_id)
        if not row:
            raise HTTPException(
                status_code=404,
                detail={"code": "portrait_state_not_found", "portrait_state_id": portrait_state_id},
            )
        return {
            "portrait_state_id": row[0],
            "state_json": _json_db_load(row[2]) or {},
            "source_summary_json": _json_db_load(row[3]) or {},
            "updated_at": _to_iso(row[4]),
        }

    def _render_prompt_text(
        self,
        *,
        prompt_kind: str,
        note_text: str | None,
        dialogue_context: dict[str, Any] | None,
        portrait_state_context: dict[str, Any] | None,
    ) -> str:
        if prompt_kind == "ai_memory":
            return load_ai_memory_prompt()

        lines = [
            "你将协助生成一份可继续回贴到 TopicLab 画像系统的综合输出。",
            "",
            f"目标类型：{prompt_kind}",
            "",
            "请基于以下上下文输出：",
            "1. 一份结构化综合理解",
            "2. 一份可用于更新画像状态的候选 patch 建议",
            "3. 必要时指出信息缺口与下一步追问",
            "",
            "请避免编造没有证据支持的个人背景。",
            "",
        ]
        if note_text:
            lines.extend(
                [
                    "补充说明：",
                    note_text.strip(),
                    "",
                ]
            )
        if portrait_state_context:
            lines.extend(
                [
                    "当前画像状态：",
                    json.dumps(portrait_state_context["state_json"], ensure_ascii=False, indent=2),
                    "",
                ]
            )
        if dialogue_context:
            lines.extend(
                [
                    "对话记录：",
                ]
            )
            for message in dialogue_context["messages"]:
                if message["content_text"]:
                    content = message["content_text"]
                else:
                    content = json.dumps(message["content_json"], ensure_ascii=False)
                lines.append(f"- {message['role']}: {content}")
            lines.append("")
        lines.extend(
            [
                "请优先输出 JSON 与自然语言混合结果。",
                "建议至少包含：summary、candidate_state_patch、open_questions 三个字段。",
            ]
        )
        return "\n".join(lines).strip()

    def create_handoff(self, req: PromptHandoffCreateRequest, user_id: int) -> dict[str, Any]:
        handoff_id = f"phf_{uuid4().hex[:16]}"
        artifact_id = f"pha_{uuid4().hex[:16]}"
        now = datetime.now(timezone.utc)

        with get_db_session() as db_session:
            dialogue_context = None
            if req.dialogue_session_id:
                dialogue_context = self._load_dialogue_context(db_session, req.dialogue_session_id, user_id)

            portrait_state_context = None
            if req.portrait_state_id:
                portrait_state_context = self._load_portrait_state_context(db_session, req.portrait_state_id, user_id)

            prompt_text = self._render_prompt_text(
                prompt_kind=req.prompt_kind,
                note_text=req.note_text,
                dialogue_context=dialogue_context,
                portrait_state_context=portrait_state_context,
            )
            artifact_metadata = {
                "prompt_kind": req.prompt_kind,
                "dialogue_session_id": req.dialogue_session_id,
                "portrait_state_id": req.portrait_state_id,
                "has_note_text": bool(req.note_text and req.note_text.strip()),
                "message_count": len(dialogue_context["messages"]) if dialogue_context else 0,
            }

            prompt_handoff_repository.insert_handoff(
                db_session,
                handoff_id=handoff_id,
                user_id=user_id,
                dialogue_session_id=req.dialogue_session_id,
                portrait_state_id=req.portrait_state_id,
                prompt_kind=req.prompt_kind,
                note_text=req.note_text.strip() if req.note_text else None,
                status="ready",
                requested_at=now,
                completed_at=now,
            )
            prompt_handoff_repository.insert_artifact(
                db_session,
                artifact_id=artifact_id,
                handoff_id=handoff_id,
                artifact_type="prompt_text",
                content_text=prompt_text,
                content_json=_json_db_value(artifact_metadata),
                created_at=now,
            )

            handoff_row = prompt_handoff_repository.get_handoff_row(db_session, handoff_id, user_id)
            artifact_rows = prompt_handoff_repository.list_artifact_rows(db_session, handoff_id)
            return {
                "handoff": self._serialize_handoff_row(handoff_row),
                "artifacts": [self._serialize_artifact_row(row) for row in artifact_rows],
            }

    def list_handoffs(self, user_id: int) -> dict[str, Any]:
        with get_db_session() as db_session:
            rows = prompt_handoff_repository.list_handoff_rows(db_session, user_id)
            return {"handoffs": [self._serialize_handoff_row(row) for row in rows]}

    def get_handoff(self, handoff_id: str, user_id: int) -> dict[str, Any]:
        with get_db_session() as db_session:
            handoff_row = prompt_handoff_repository.get_handoff_row(db_session, handoff_id, user_id)
            if not handoff_row:
                raise HTTPException(
                    status_code=404,
                    detail={"code": "portrait_prompt_handoff_not_found", "handoff_id": handoff_id},
                )
            artifact_rows = prompt_handoff_repository.list_artifact_rows(db_session, handoff_id)
            return {
                "handoff": self._serialize_handoff_row(handoff_row),
                "artifacts": [self._serialize_artifact_row(row) for row in artifact_rows],
            }

    def cancel_handoff(self, handoff_id: str, user_id: int) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        with get_db_session() as db_session:
            handoff_row = prompt_handoff_repository.get_handoff_row(db_session, handoff_id, user_id)
            if not handoff_row:
                raise HTTPException(
                    status_code=404,
                    detail={"code": "portrait_prompt_handoff_not_found", "handoff_id": handoff_id},
                )
            prompt_handoff_repository.update_handoff_status(
                db_session,
                handoff_id=handoff_id,
                user_id=user_id,
                status="cancelled",
                cancelled_at=now,
            )
            updated_row = prompt_handoff_repository.get_handoff_row(db_session, handoff_id, user_id)
            artifact_rows = prompt_handoff_repository.list_artifact_rows(db_session, handoff_id)
            return {
                "handoff": self._serialize_handoff_row(updated_row),
                "artifacts": [self._serialize_artifact_row(row) for row in artifact_rows],
            }


prompt_handoff_service = PromptHandoffService()
