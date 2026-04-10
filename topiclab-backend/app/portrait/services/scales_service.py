"""Portrait-domain scale runtime service."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from fastapi import HTTPException

from app.portrait.runtime.definitions_loader import definitions_loader
from app.portrait.services.scales_scoring import (
    SCORING_VERSION,
    build_result_summary,
    calculate_derived_scores,
    calculate_dimension_scores,
)
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


class ScalesService:
    """Read canonical definitions and manage scale runtime state."""

    def list_scales(self) -> dict[str, Any]:
        return definitions_loader.list_scales()

    def get_scale_definition(self, scale_id: str) -> dict[str, Any]:
        definition = definitions_loader.get_scale_definition(scale_id)
        if definition is None:
            raise HTTPException(status_code=404, detail={"code": "scale_not_found", "scale_id": scale_id})
        return definition

    def _required_question_ids(self, definition: dict[str, Any]) -> list[str]:
        return [question["id"] for question in definition["questions"] if question.get("required", True)]

    def _question_by_id(self, definition: dict[str, Any]) -> dict[str, dict[str, Any]]:
        return {question["id"]: question for question in definition["questions"]}

    def _get_session_row(self, db_session, session_id: str, user_id: int):
        row = scales_repository.get_session_row(db_session, session_id, user_id)
        if not row:
            raise HTTPException(status_code=404, detail={"code": "session_not_found", "session_id": session_id})
        return row

    def _load_answers(self, db_session, session_id: str) -> dict[str, float]:
        return scales_repository.load_answers(db_session, session_id)

    def _compute_session_state(self, db_session, session_row) -> dict[str, Any]:
        session_id = str(session_row[0])
        scale_id = str(session_row[2])
        definition = self.get_scale_definition(scale_id)
        answers = self._load_answers(db_session, session_id)
        required_question_ids = self._required_question_ids(definition)
        missing_question_ids = [question_id for question_id in required_question_ids if question_id not in answers]

        stored_status = str(session_row[3])
        if stored_status == "completed":
            status = "completed"
        elif stored_status == "abandoned":
            status = "abandoned"
        elif answers and not missing_question_ids:
            status = "ready_to_finalize"
        elif answers:
            status = "in_progress"
        else:
            status = "initialized"

        next_question = None
        if status not in {"completed", "abandoned"} and missing_question_ids:
            question_by_id = self._question_by_id(definition)
            next_question_id = missing_question_ids[0]
            question = question_by_id[next_question_id]
            next_question = {
                "id": question["id"],
                "text": question["text"],
                "dimension": question["dimension"],
                "reverse": bool(question.get("reverse", False)),
                "required": bool(question.get("required", True)),
            }

        if status == "completed":
            allowed_actions = ["read_result"]
        elif status == "abandoned":
            allowed_actions = []
        elif status == "ready_to_finalize":
            allowed_actions = ["answer", "answer_batch", "finalize", "abandon"]
        else:
            allowed_actions = ["answer", "answer_batch", "abandon"]

        return {
            "session": {
                "session_id": session_id,
                "scale_id": scale_id,
                "status": status,
                "actor_type": session_row[4],
                "actor_id": session_row[5],
                "definition_version": session_row[6],
                "scoring_version": session_row[7],
                "created_at": _to_iso(session_row[8]),
                "updated_at": _to_iso(session_row[9]),
                "completed_at": _to_iso(session_row[10]),
                "abandoned_at": _to_iso(session_row[11]),
            },
            "scale": {
                "scale_id": definition["scale_id"],
                "name": definition["name"],
                "question_count": len(definition["questions"]),
                "required_count": len(required_question_ids),
                "definition_version": definition["definition_version"],
            },
            "progress": {
                "answered_count": len(answers),
                "required_count": len(required_question_ids),
                "remaining_count": len(missing_question_ids),
                "missing_question_ids": missing_question_ids,
            },
            "answers": answers,
            "next_question": next_question,
            "allowed_actions": allowed_actions,
        }

    def _persist_session_status(self, db_session, session_id: str, user_id: int, state: dict[str, Any]) -> None:
        scales_repository.update_session_status(
            db_session,
            session_id=session_id,
            user_id=user_id,
            status=state["session"]["status"],
            updated_at=datetime.now(timezone.utc),
        )

    def _ensure_session_writable(self, state: dict[str, Any]) -> None:
        status = state["session"]["status"]
        if status == "completed":
            raise HTTPException(status_code=409, detail={"code": "session_completed", "session_id": state["session"]["session_id"]})
        if status == "abandoned":
            raise HTTPException(status_code=409, detail={"code": "session_abandoned", "session_id": state["session"]["session_id"]})

    def _validate_answer(self, definition: dict[str, Any], question_id: str, value: float) -> None:
        question_by_id = self._question_by_id(definition)
        if question_id not in question_by_id:
            raise HTTPException(status_code=400, detail={"code": "invalid_question_id", "question_id": question_id})
        if value < float(definition["min_val"]) or value > float(definition["max_val"]):
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "invalid_answer_value",
                    "question_id": question_id,
                    "value": value,
                    "min_val": definition["min_val"],
                    "max_val": definition["max_val"],
                },
            )

    def start_session(self, scale_id: str, actor_type: str | None, actor_id: str | None, user_id: int) -> dict[str, Any]:
        definition = self.get_scale_definition(scale_id)
        session_id = f"scs_{uuid4().hex[:16]}"
        now = datetime.now(timezone.utc)
        with get_db_session() as db_session:
            scales_repository.insert_session(
                db_session,
                session_id=session_id,
                user_id=user_id,
                scale_id=scale_id,
                actor_type=actor_type or "human",
                actor_id=actor_id,
                definition_version=definition["definition_version"],
                scoring_version=SCORING_VERSION,
                created_at=now,
            )
            row = self._get_session_row(db_session, session_id, user_id)
            state = self._compute_session_state(db_session, row)
            self._persist_session_status(db_session, session_id, user_id, state)
            return state

    def get_session_status(self, session_id: str, user_id: int) -> dict[str, Any]:
        with get_db_session() as db_session:
            row = self._get_session_row(db_session, session_id, user_id)
            state = self._compute_session_state(db_session, row)
            if state["session"]["status"] not in {"completed", "abandoned"}:
                self._persist_session_status(db_session, session_id, user_id, state)
            return state

    def answer_question(self, session_id: str, question_id: str, value: float, user_id: int) -> dict[str, Any]:
        with get_db_session() as db_session:
            row = self._get_session_row(db_session, session_id, user_id)
            state = self._compute_session_state(db_session, row)
            self._ensure_session_writable(state)
            definition = self.get_scale_definition(state["session"]["scale_id"])
            self._validate_answer(definition, question_id, value)
            scales_repository.upsert_answer(
                db_session,
                session_id=session_id,
                question_id=question_id,
                value=value,
                answered_at=datetime.now(timezone.utc),
            )
            row = self._get_session_row(db_session, session_id, user_id)
            new_state = self._compute_session_state(db_session, row)
            self._persist_session_status(db_session, session_id, user_id, new_state)
            new_state["accepted_answer"] = {"question_id": question_id, "value": value}
            return new_state

    def answer_batch(self, session_id: str, answers: dict[str, float], user_id: int) -> dict[str, Any]:
        with get_db_session() as db_session:
            row = self._get_session_row(db_session, session_id, user_id)
            state = self._compute_session_state(db_session, row)
            self._ensure_session_writable(state)
            definition = self.get_scale_definition(state["session"]["scale_id"])
            if not isinstance(answers, dict) or not answers:
                raise HTTPException(status_code=400, detail={"code": "empty_answers"})
            for question_id, value in answers.items():
                self._validate_answer(definition, question_id, float(value))
            now = datetime.now(timezone.utc)
            for question_id, value in answers.items():
                scales_repository.upsert_answer(
                    db_session,
                    session_id=session_id,
                    question_id=question_id,
                    value=float(value),
                    answered_at=now,
                )
            row = self._get_session_row(db_session, session_id, user_id)
            new_state = self._compute_session_state(db_session, row)
            self._persist_session_status(db_session, session_id, user_id, new_state)
            new_state["accepted_answers"] = {question_id: float(value) for question_id, value in answers.items()}
            return new_state

    def _serialize_result_row(self, row) -> dict[str, Any]:
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

    def finalize(self, session_id: str, user_id: int) -> dict[str, Any]:
        with get_db_session() as db_session:
            existing_result = scales_repository.get_result_row(db_session, session_id, user_id)
            if existing_result is not None:
                row = self._get_session_row(db_session, session_id, user_id)
                state = self._compute_session_state(db_session, row)
                return {"session": state["session"], "result": self._serialize_result_row(existing_result)}

            row = self._get_session_row(db_session, session_id, user_id)
            state = self._compute_session_state(db_session, row)
            if state["session"]["status"] == "abandoned":
                raise HTTPException(status_code=409, detail={"code": "session_abandoned", "session_id": session_id})
            if state["progress"]["missing_question_ids"]:
                raise HTTPException(
                    status_code=409,
                    detail={
                        "code": "session_not_ready",
                        "session_id": session_id,
                        "missing_question_ids": state["progress"]["missing_question_ids"],
                    },
                )

            definition = self.get_scale_definition(state["session"]["scale_id"])
            answers = state["answers"]
            dimension_scores = calculate_dimension_scores(definition, answers)
            derived_scores = calculate_derived_scores(definition["scale_id"], dimension_scores)
            result_summary = build_result_summary(definition["scale_id"], dimension_scores, derived_scores)
            completed_at = datetime.now(timezone.utc)
            scales_repository.insert_result(
                db_session,
                session_id=session_id,
                user_id=user_id,
                scale_id=definition["scale_id"],
                definition_version=definition["definition_version"],
                scoring_version=SCORING_VERSION,
                answers_json=_json_db_value(answers),
                dimension_scores_json=_json_db_value(dimension_scores),
                derived_scores_json=_json_db_value(derived_scores),
                result_summary_json=_json_db_value(result_summary),
                completed_at=completed_at,
            )
            scales_repository.update_session_status(
                db_session,
                session_id=session_id,
                user_id=user_id,
                status="completed",
                updated_at=completed_at,
                completed_at=completed_at,
            )
            result_row = scales_repository.get_result_row(db_session, session_id, user_id)
            session_row = self._get_session_row(db_session, session_id, user_id)
            new_state = self._compute_session_state(db_session, session_row)
            return {"session": new_state["session"], "result": self._serialize_result_row(result_row)}

    def get_result(self, session_id: str, user_id: int) -> dict[str, Any]:
        with get_db_session() as db_session:
            row = scales_repository.get_result_row(db_session, session_id, user_id)
            if row is None:
                raise HTTPException(status_code=404, detail={"code": "result_not_found", "session_id": session_id})
            return {"result": self._serialize_result_row(row)}

    def list_sessions(self, user_id: int) -> dict[str, Any]:
        with get_db_session() as db_session:
            rows = scales_repository.list_session_rows(db_session, user_id)
            sessions = []
            for row in rows:
                state = self._compute_session_state(db_session, row)
                sessions.append(
                    {
                        "session": state["session"],
                        "progress": state["progress"],
                        "allowed_actions": state["allowed_actions"],
                    }
                )
            return {"sessions": sessions}

    def abandon_session(self, session_id: str, user_id: int) -> dict[str, Any]:
        with get_db_session() as db_session:
            row = self._get_session_row(db_session, session_id, user_id)
            state = self._compute_session_state(db_session, row)
            if state["session"]["status"] == "completed":
                raise HTTPException(status_code=409, detail={"code": "session_completed", "session_id": session_id})
            abandoned_at = datetime.now(timezone.utc)
            scales_repository.update_session_status(
                db_session,
                session_id=session_id,
                user_id=user_id,
                status="abandoned",
                updated_at=abandoned_at,
                abandoned_at=abandoned_at,
            )
            row = self._get_session_row(db_session, session_id, user_id)
            return self._compute_session_state(db_session, row)


scales_service = ScalesService()
