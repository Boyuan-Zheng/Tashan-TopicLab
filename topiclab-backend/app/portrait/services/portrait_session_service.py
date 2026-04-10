"""Unified portrait session orchestrator service."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from fastapi import HTTPException

from app.portrait.legacy_kernel.bridge import legacy_kernel_bridge
from app.portrait.runtime.block_protocol import copyable_block, first_interactive_block, text_block
from app.portrait.schemas.import_results import ImportResultCreateRequest
from app.portrait.schemas.portrait_state import PortraitStateUpdateRequest
from app.portrait.schemas.prompt_handoff import PromptHandoffCreateRequest
from app.portrait.schemas.session import PortraitSessionRespondRequest, PortraitSessionStartRequest
from app.portrait.services.portrait_profile_inference_service import portrait_profile_inference_service
from app.portrait.services.portrait_review_service import PROCESS_DIMENSIONS, portrait_review_service
from app.portrait.services.dialogue_service import dialogue_service
from app.portrait.services.import_result_service import import_result_service
from app.portrait.services.portrait_export_service import portrait_export_service
from app.portrait.services.portrait_forum_service import portrait_forum_service
from app.portrait.services.portrait_orchestration_service import portrait_orchestration_service
from app.portrait.services.portrait_publish_service import portrait_publish_service
from app.portrait.services.portrait_scientist_service import portrait_scientist_service
from app.portrait.services.portrait_skill_policy_service import portrait_skill_policy_service
from app.portrait.services.portrait_state_service import portrait_state_service
from app.portrait.services.prompt_handoff_service import prompt_handoff_service
from app.portrait.services.scales_service import scales_service
from app.portrait.storage.portrait_session_repository import portrait_session_repository
from app.portrait.storage.portrait_state_repository import portrait_state_repository
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


class PortraitSessionService:
    """Top-level agent-facing portrait session orchestration."""

    def _serialize_session_row(self, row) -> dict[str, Any]:
        return {
            "session_id": row[0],
            "user_id": row[1],
            "actor_type": row[2],
            "actor_id": row[3],
            "mode": row[4],
            "status": row[5],
            "current_stage": row[6],
            "current_input_kind": row[7],
            "current_message": row[8],
            "current_payload_json": _json_db_load(row[9]) or {},
            "current_next_hint": row[10],
            "result_preview_json": _json_db_load(row[11]),
            "created_at": _to_iso(row[12]),
            "updated_at": _to_iso(row[13]),
            "closed_at": _to_iso(row[14]),
        }

    def _serialize_runtime_ref_row(self, row) -> dict[str, Any]:
        return {
            "session_id": row[0],
            "user_id": row[1],
            "ref_kind": row[2],
            "ref_value": row[3],
            "metadata_json": _json_db_load(row[4]),
            "created_at": _to_iso(row[5]),
            "updated_at": _to_iso(row[6]),
        }

    def _serialize_event_row(self, row) -> dict[str, Any]:
        return {
            "event_id": row[0],
            "session_id": row[1],
            "user_id": row[2],
            "event_type": row[3],
            "event_json": _json_db_load(row[4]) or {},
            "created_at": _to_iso(row[5]),
        }

    def _runtime_ref_map(self, rows) -> dict[str, dict[str, Any]]:
        result: dict[str, dict[str, Any]] = {}
        for row in rows:
            item = self._serialize_runtime_ref_row(row)
            result[item["ref_kind"]] = {
                "ref_value": item["ref_value"],
                "metadata_json": item["metadata_json"],
                "updated_at": item["updated_at"],
            }
        return result

    def _serialize_current_state_row(self, row) -> dict[str, Any]:
        return {
            "portrait_state_id": row[0],
            "user_id": row[1],
            "state_json": _json_db_load(row[2]) or {},
            "source_summary_json": _json_db_load(row[3]) or {},
            "updated_at": _to_iso(row[4]),
        }

    def _get_session_row(self, db_session, session_id: str, user_id: int):
        row = portrait_session_repository.get_session_row(db_session, session_id, user_id)
        if not row:
            raise HTTPException(
                status_code=404,
                detail={"code": "portrait_session_not_found", "session_id": session_id},
            )
        return row

    def _load_current_state(self, db_session, ref_map: dict[str, Any], user_id: int) -> dict[str, Any] | None:
        state_ref = ref_map.get("portrait_state")
        row = None
        if state_ref:
            row = portrait_state_repository.get_current_state_by_id_row(
                db_session,
                str(state_ref["ref_value"]),
                user_id,
            )
        if row is None:
            row = portrait_state_repository.get_current_state_row(db_session, user_id)
        if row is None:
            return None
        return self._serialize_current_state_row(row)

    def _load_runtime_refs(self, db_session, session_id: str) -> dict[str, dict[str, Any]]:
        return self._runtime_ref_map(portrait_session_repository.list_runtime_ref_rows(db_session, session_id))

    def _current_policy(self, session: dict[str, Any]) -> dict[str, Any] | None:
        payload = session.get("current_payload_json") or {}
        if not isinstance(payload, dict):
            return None
        policy = payload.get("policy")
        if isinstance(policy, dict):
            return policy
        return None

    def _is_product_choice(self, normalized_choice: str) -> bool:
        return normalized_choice in {
            "forum:generate",
            "scientist:famous",
            "scientist:field",
            "export:structured",
            "export:profile_markdown",
            "export:forum_markdown",
            "publish:brief",
            "publish:full",
        }

    def _build_legacy_bootstrap_step(self) -> dict[str, Any]:
        return {
            "stage": "legacy_kernel_bootstrap",
            "input_kind": "none",
            "message": "正在启动旧画像内核。",
            "payload": {
                "blocks": [
                    text_block("正在启动旧画像内核，并同步历史画像产品的 agent loop。"),
                ],
            },
            "next_hint": "稍候将自动进入旧画像采集对话。",
        }

    def _legacy_choice_to_text(self, choice_value: Any) -> str:
        normalized = str(choice_value).strip()
        mapping = {
            "ai_memory": "A",
            "direct": "B",
            "continue_dialogue": "继续",
            "prompt_handoff": "请生成一份给外部 AI 使用的画像提取提示词。",
            "forum:generate": "请基于当前科研数字分身生成论坛画像。",
            "confirm_review": "我确认当前画像，没有更多修改，请完成最终画像。",
            "back_to_review": "回到画像审阅。",
            "update_basic_identity": "我想修改基础身份信息。",
            "update_tech_capability": "我想修改技术栈与能力信息。",
            "update_process_ability": "我想修改科研流程能力。",
            "update_current_needs": "我想修改当前需求和卡点。",
            "research_stage": "我想修改研究阶段。",
            "fields": "我想修改研究领域。",
            "method": "我想修改研究方法范式。",
            "institution": "我想修改所在机构。",
            "advisor_team": "我想修改导师与团队信息。",
            "academic_network": "我想修改学术合作圈情况。",
            "major_time_occupation": "我想修改当前主要时间占用。",
            "pain_points": "我想修改当前核心难点。",
            "desired_change": "我想修改最想改变的事情。",
            "scale:rcss": "我想填写科研认知风格量表 RCSS。",
            "scale:ams": "我想填写学术动机量表 AMS。",
            "scale:mini_ipip": "我想填写人格量表 Mini-IPIP。",
            "scale:mini-ipip": "我想填写人格量表 Mini-IPIP。",
        }
        return mapping.get(normalized, normalized)

    def _normalize_legacy_request(self, req: PortraitSessionRespondRequest) -> dict[str, Any]:
        if req.choice is not None:
            normalized_choice = str(req.choice).strip()
            if normalized_choice == "reset_now":
                return {"action": "reset"}
            if normalized_choice in {
                "scientist:famous",
                "scientist:field",
                "export:structured",
                "export:profile_markdown",
                "export:forum_markdown",
                "publish:brief",
                "publish:full",
            }:
                return {"action": "product_choice", "choice": normalized_choice}
            return {
                "action": "bridge",
                "input_type": "choice",
                "value": normalized_choice,
                "user_message": self._legacy_choice_to_text(req.choice),
            }
        if req.text and req.text.strip():
            return {
                "action": "bridge",
                "input_type": "text",
                "value": req.text.strip(),
                "user_message": req.text.strip(),
            }
        if req.external_text and req.external_text.strip():
            return {
                "action": "bridge",
                "input_type": "external_text",
                "value": req.external_text.strip(),
                "user_message": req.external_text.strip(),
            }
        if req.external_json is not None:
            payload_text = json.dumps(req.external_json, ensure_ascii=False, indent=2)
            return {
                "action": "bridge",
                "input_type": "external_json",
                "value": req.external_json,
                "user_message": payload_text,
            }
        if req.confirm:
            return {
                "action": "bridge",
                "input_type": "confirm",
                "value": True,
                "user_message": "我确认当前画像，没有更多修改，请完成最终画像。",
            }
        raise HTTPException(
            status_code=400,
            detail={
                "code": "unsupported_portrait_session_input",
                "supported": ["choice", "text", "external_text", "external_json", "confirm"],
            },
        )

    def _product_ref_kind(self, normalized_choice: str) -> str:
        mapping = {
            "forum:generate": "forum_artifact",
            "scientist:famous": "scientist_famous_artifact",
            "scientist:field": "scientist_field_artifact",
            "export:structured": "export_structured_artifact",
            "export:profile_markdown": "export_profile_markdown_artifact",
            "export:forum_markdown": "export_forum_markdown_artifact",
            "publish:brief": "publish_brief_artifact",
            "publish:full": "publish_full_artifact",
        }
        return mapping[normalized_choice]

    def _product_result_blocks(self, normalized_choice: str, payload: dict[str, Any]) -> list[dict[str, Any]]:
        artifact = payload.get("artifact") or {}
        artifact_kind = str(artifact.get("artifact_kind") or "")
        artifact_id = str(artifact.get("artifact_id") or "")

        blocks: list[dict[str, Any]] = [
            text_block(
                "\n".join(
                    [
                        f"已完成动作：{normalized_choice}",
                        f"- artifact_kind：{artifact_kind or 'unknown'}",
                        f"- artifact_id：{artifact_id or 'unknown'}",
                    ]
                )
            )
        ]

        if normalized_choice == "forum:generate":
            blocks.append(copyable_block(title="论坛画像 Markdown", content=str(payload.get("forum_profile_markdown") or "")))
            return blocks

        if normalized_choice == "scientist:famous":
            match = payload.get("match") or {}
            top3 = match.get("top3") or []
            blocks.append(
                text_block(
                    "著名科学家匹配：\n"
                    + "\n".join(
                        [
                            f"- {item.get('name')}（{item.get('field') or '未知领域'}）：{item.get('similarity')}%"
                            for item in top3[:3]
                        ]
                    )
                )
            )
            return blocks

        if normalized_choice == "scientist:field":
            recommendations = payload.get("recommendations") or []
            blocks.append(
                text_block(
                    "领域科学家推荐：\n"
                    + "\n".join(
                        [
                            f"- {item.get('name')}：{item.get('field') or '未知领域'}；{item.get('reason') or '无说明'}"
                            for item in recommendations[:5]
                        ]
                    )
                )
            )
            return blocks

        if normalized_choice == "export:structured":
            blocks.append(
                copyable_block(
                    title="结构化画像 JSON",
                    content=json.dumps(payload.get("structured_profile") or {}, ensure_ascii=False, indent=2),
                )
            )
            return blocks

        if normalized_choice == "export:profile_markdown":
            blocks.append(copyable_block(title="完整画像 Markdown", content=str(payload.get("profile_markdown") or "")))
            return blocks

        if normalized_choice == "export:forum_markdown":
            blocks.append(copyable_block(title="论坛画像 Markdown", content=str(payload.get("forum_profile_markdown") or "")))
            return blocks

        if normalized_choice == "publish:brief" or normalized_choice == "publish:full":
            twin = payload.get("twin") or {}
            blocks.append(
                text_block(
                    "\n".join(
                        [
                            "画像已发布到 twin runtime。",
                            f"- twin_id：{twin.get('twin_id') or 'unknown'}",
                            f"- version：{twin.get('version') or 'unknown'}",
                            f"- exposure：{twin.get('exposure') or normalized_choice.split(':', 1)[1]}",
                        ]
                    )
                )
            )
            blocks.append(copyable_block(title="发布内容", content=str(payload.get("role_content") or "")))
            return blocks

        return blocks

    async def _respond_product_action(
        self,
        session_id: str,
        normalized_choice: str,
        user_id: int,
        session: dict[str, Any],
        ref_map: dict[str, Any],
        *,
        return_surface: str,
    ) -> dict[str, Any]:
        if normalized_choice == "forum:generate":
            product_payload = portrait_forum_service.generate_forum_profile(
                user_id=user_id,
                source_session_id=session_id,
            )
        elif normalized_choice == "scientist:famous":
            product_payload = await portrait_scientist_service.generate_famous_match(
                user_id=user_id,
                source_session_id=session_id,
            )
        elif normalized_choice == "scientist:field":
            product_payload = await portrait_scientist_service.generate_field_recommendations(
                user_id=user_id,
                source_session_id=session_id,
            )
        elif normalized_choice == "export:structured":
            product_payload = portrait_export_service.export_structured(
                user_id=user_id,
                source_session_id=session_id,
            )
        elif normalized_choice == "export:profile_markdown":
            product_payload = portrait_export_service.export_profile_markdown(
                user_id=user_id,
                source_session_id=session_id,
            )
        elif normalized_choice == "export:forum_markdown":
            product_payload = portrait_export_service.export_forum_markdown(
                user_id=user_id,
                source_session_id=session_id,
            )
        elif normalized_choice == "publish:brief":
            product_payload = portrait_publish_service.publish(
                user_id=user_id,
                exposure="brief",
                source_session_id=session_id,
            )
        elif normalized_choice == "publish:full":
            product_payload = portrait_publish_service.publish(
                user_id=user_id,
                exposure="full",
                source_session_id=session_id,
            )
        else:
            raise HTTPException(status_code=400, detail={"code": "unsupported_product_choice", "choice": normalized_choice})

        artifact = product_payload.get("artifact") or {}
        artifact_id = str(artifact.get("artifact_id") or "")
        blocks = self._product_result_blocks(normalized_choice, product_payload)

        with get_db_session() as db_session:
            current_state = self._load_current_state(db_session, ref_map, user_id)
            if artifact_id:
                self._link_runtime_ref(
                    db_session,
                    session_id=session_id,
                    user_id=user_id,
                    ref_kind=self._product_ref_kind(normalized_choice),
                    ref_value=artifact_id,
                    metadata_json={
                        "choice": normalized_choice,
                        "artifact_kind": artifact.get("artifact_kind"),
                    },
                )
            twin = product_payload.get("twin") or {}
            twin_id = str(twin.get("twin_id") or "")
            if twin_id:
                self._link_runtime_ref(
                    db_session,
                    session_id=session_id,
                    user_id=user_id,
                    ref_kind="published_twin",
                    ref_value=twin_id,
                    metadata_json={"choice": normalized_choice, "version": twin.get("version")},
                )

            if return_surface == "review":
                step = portrait_review_service.build_review_step_with_prelude(
                    current_state=current_state,
                    prepend_blocks=blocks,
                )
            else:
                step = portrait_orchestration_service.build_dialogue_followup_step(
                    generated_message=None,
                    current_state=current_state,
                    prepend_blocks=blocks,
                    message_override="系统已完成所选画像动作。你可以继续补充信息，或继续选择下一步动作。",
                )

            self._set_step(
                db_session,
                session_id=session_id,
                user_id=user_id,
                step=step,
                result_preview=session["result_preview_json"],
            )
            self._insert_event(
                db_session,
                session_id=session_id,
                user_id=user_id,
                event_type="portrait_product_action",
                event_json={
                    "choice": normalized_choice,
                    "artifact_id": artifact_id or None,
                    "artifact_kind": artifact.get("artifact_kind"),
                    "twin_id": twin_id or None,
                },
            )
            row = self._get_session_row(db_session, session_id, user_id)
            return self._build_response(
                db_session=db_session,
                session_row=row,
                user_id=user_id,
                last_response={
                    "input_type": "choice",
                    "choice": normalized_choice,
                    "product_action": product_payload,
                },
            )

    def _manual_portrait_state_update(
        self,
        *,
        user_id: int,
        skill_id: str,
        step_id: str,
        state_patch_json: dict[str, Any],
        source_label: str,
    ) -> dict[str, Any]:
        return portrait_state_service.apply_update(
            PortraitStateUpdateRequest(
                source_type="manual",
                state_patch_json=state_patch_json,
                change_summary_json={
                    "source_type": "manual",
                    "source_id": f"legacy_skill:{skill_id}:{step_id}",
                    "skill_id": skill_id,
                    "step_id": step_id,
                    "fields_written": sorted(state_patch_json.keys()),
                    "source_label": source_label,
                },
                observation_json={
                    "kind": "legacy_skill_answer",
                    "skill_id": skill_id,
                    "step_id": step_id,
                    "source_label": source_label,
                },
            ),
            user_id,
        )

    def _run_inference_update(self, *, user_id: int, current_state: dict[str, Any]) -> dict[str, Any]:
        inference = portrait_profile_inference_service.infer_from_current_state(current_state)
        state_update = portrait_state_service.apply_update(
            PortraitStateUpdateRequest(
                source_type="manual",
                state_patch_json=inference["state_patch_json"],
                change_summary_json=inference["change_summary_json"],
                observation_json=inference["observation_json"],
            ),
            user_id,
        )
        return {"state_update": state_update, "inference": inference}

    def _finalize_legacy_basic_info(
        self,
        *,
        db_session,
        session_id: str,
        user_id: int,
        current_state: dict[str, Any],
        last_response: dict[str, Any],
    ) -> dict[str, Any]:
        inference_payload = self._run_inference_update(user_id=user_id, current_state=current_state)
        inferred_state = inference_payload["state_update"]["current_state"]
        portrait_state_id = str(inferred_state["portrait_state_id"])
        self._link_runtime_ref(
            db_session,
            session_id=session_id,
            user_id=user_id,
            ref_kind="portrait_state",
            ref_value=portrait_state_id,
            metadata_json={"source": "legacy_skill_inference", "source_id": "infer-profile-dimensions"},
        )
        review_step = portrait_review_service.build_review_step(current_state=inferred_state)
        self._set_step(
            db_session,
            session_id=session_id,
            user_id=user_id,
            step=review_step,
            result_preview={"portrait_state_id": portrait_state_id, "source_type": "manual", "source_id": "infer-profile-dimensions"},
        )
        self._insert_event(
            db_session,
            session_id=session_id,
            user_id=user_id,
            event_type="legacy_skill_inferred",
            event_json=inference_payload["inference"]["summary"],
        )
        row = self._get_session_row(db_session, session_id, user_id)
        last_response = dict(last_response)
        last_response["inference"] = inference_payload["inference"]["summary"]
        last_response["state_update"] = inference_payload["state_update"]
        return self._build_response(
            db_session=db_session,
            session_row=row,
            user_id=user_id,
            last_response=last_response,
        )

    def _respond_legacy_kernel(
        self,
        *,
        session_id: str,
        user_id: int,
        session: dict[str, Any],
        user_message: str,
        input_type: str,
        input_value: Any,
    ) -> dict[str, Any]:
        bridge_result = legacy_kernel_bridge.run_turn(
            portrait_session_id=session_id,
            user_id=user_id,
            user_message=user_message,
            actor_type=session.get("actor_type"),
            actor_id=session.get("actor_id"),
        )
        state_update = bridge_result["state_update"]
        current_state = state_update["current_state"]
        portrait_state_id = str(current_state["portrait_state_id"])
        legacy_session_id = str(bridge_result["legacy_session_id"])
        now = datetime.now(timezone.utc)

        with get_db_session() as db_session:
            self._link_runtime_ref(
                db_session,
                session_id=session_id,
                user_id=user_id,
                ref_kind="legacy_kernel_session",
                ref_value=legacy_session_id,
                metadata_json={
                    "actor_type": session.get("actor_type"),
                    "actor_id": session.get("actor_id"),
                },
            )
            self._link_runtime_ref(
                db_session,
                session_id=session_id,
                user_id=user_id,
                ref_kind="portrait_state",
                ref_value=portrait_state_id,
                metadata_json={"source": "legacy_kernel", "source_id": legacy_session_id},
            )
            self._set_step(
                db_session,
                session_id=session_id,
                user_id=user_id,
                step=bridge_result["step"],
                status=str(bridge_result["status"]),
                result_preview=bridge_result["result_preview"],
                closed_at=now if str(bridge_result["status"]) == "completed" else None,
            )
            self._insert_event(
                db_session,
                session_id=session_id,
                user_id=user_id,
                event_type="legacy_kernel_turn",
                event_json={
                    "input_type": input_type,
                    "input_value": input_value,
                    "user_message": user_message,
                    "legacy_session_id": legacy_session_id,
                    "bridge_status": bridge_result["status"],
                    "portrait_state_id": portrait_state_id,
                },
            )
            row = self._get_session_row(db_session, session_id, user_id)
            return self._build_response(
                db_session=db_session,
                session_row=row,
                user_id=user_id,
                last_response={
                    "input_type": input_type,
                    "accepted_message": user_message,
                    "accepted_value": input_value,
                    "legacy_session_id": legacy_session_id,
                    "assistant_content": bridge_result["assistant_content"],
                    "state_update": state_update,
                    "bridge_status": bridge_result["status"],
                },
            )

    def _link_runtime_ref(
        self,
        db_session,
        *,
        session_id: str,
        user_id: int,
        ref_kind: str,
        ref_value: str,
        metadata_json: dict[str, Any] | None = None,
    ) -> None:
        portrait_session_repository.upsert_runtime_ref(
            db_session,
            session_id=session_id,
            user_id=user_id,
            ref_kind=ref_kind,
            ref_value=ref_value,
            metadata_json=_json_db_value(metadata_json),
            updated_at=datetime.now(timezone.utc),
        )
        self._insert_event(
            db_session,
            session_id=session_id,
            user_id=user_id,
            event_type="runtime_ref_linked",
            event_json={"ref_kind": ref_kind, "ref_value": ref_value, "metadata_json": metadata_json or {}},
        )

    def _set_step(
        self,
        db_session,
        *,
        session_id: str,
        user_id: int,
        step: dict[str, Any],
        status: str = "active",
        result_preview: dict[str, Any] | None = None,
        closed_at: datetime | None = None,
    ) -> None:
        portrait_session_repository.update_session_state(
            db_session,
            session_id=session_id,
            user_id=user_id,
            status=status,
            current_stage=str(step["stage"]),
            current_input_kind=str(step["input_kind"]),
            current_message=str(step["message"]),
            current_payload_json=_json_db_value(step.get("payload")),
            current_next_hint=step.get("next_hint"),
            result_preview_json=_json_db_value(result_preview),
            updated_at=datetime.now(timezone.utc),
            closed_at=closed_at,
        )

    def _build_response(
        self,
        *,
        db_session,
        session_row,
        user_id: int,
        last_response: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        session = self._serialize_session_row(session_row)
        payload = session["current_payload_json"] or {}
        blocks = payload.get("blocks") if isinstance(payload, dict) else None
        policy = payload.get("policy") if isinstance(payload, dict) else None
        ref_rows = portrait_session_repository.list_runtime_ref_rows(db_session, session["session_id"])
        runtime_refs = self._runtime_ref_map(ref_rows)
        current_state = self._load_current_state(db_session, runtime_refs, user_id)
        terminal_status = session["status"] in {"completed", "reset"}
        return {
            "session": session,
            "status": session["status"],
            "stage": session["current_stage"],
            "message": session["current_message"],
            "input_kind": session["current_input_kind"],
            "allowed_actions": ["status", "result", "history"] if terminal_status else ["respond", "status", "result", "history", "reset"],
            "payload": session["current_payload_json"] or {},
            "progress": {
                "event_count": portrait_session_repository.count_event_rows(db_session, session["session_id"]),
                "runtime_ref_count": len(runtime_refs),
            },
            "runtime_refs": runtime_refs,
            "result_preview": session["result_preview_json"],
            "next_hint": session["current_next_hint"],
            "current_state": current_state,
            "last_response": last_response,
            "blocks": blocks or [],
            "interactive_block": first_interactive_block(blocks or []),
            "policy": policy,
        }

    def _insert_event(self, db_session, *, session_id: str, user_id: int, event_type: str, event_json: dict[str, Any]) -> None:
        portrait_session_repository.insert_event(
            db_session,
            event_id=f"pse_{uuid4().hex[:16]}",
            session_id=session_id,
            user_id=user_id,
            event_type=event_type,
            event_json=_json_db_value(event_json) or "{}",
            created_at=datetime.now(timezone.utc),
        )

    def start_session(self, req: PortraitSessionStartRequest, user_id: int) -> dict[str, Any]:
        if req.mode == "legacy_product":
            if req.resume_latest:
                with get_db_session() as db_session:
                    latest = portrait_session_repository.get_latest_active_session_row(db_session, user_id)
                    if latest:
                        return self._build_response(db_session=db_session, session_row=latest, user_id=user_id)
            now = datetime.now(timezone.utc)
            session_id = f"pts_{uuid4().hex[:16]}"
            bootstrap_placeholder = self._build_legacy_bootstrap_step()
            with get_db_session() as db_session:
                portrait_session_repository.insert_session(
                    db_session,
                    session_id=session_id,
                    user_id=user_id,
                    actor_type=req.actor_type,
                    actor_id=req.actor_id,
                    mode=req.mode,
                    status="active",
                    current_stage=str(bootstrap_placeholder["stage"]),
                    current_input_kind=str(bootstrap_placeholder["input_kind"]),
                    current_message=str(bootstrap_placeholder["message"]),
                    current_payload_json=_json_db_value(bootstrap_placeholder.get("payload")),
                    current_next_hint=bootstrap_placeholder.get("next_hint"),
                    result_preview_json=None,
                    created_at=now,
                )
                self._insert_event(
                    db_session,
                    session_id=session_id,
                    user_id=user_id,
                    event_type="session_started",
                    event_json={
                        "actor_type": req.actor_type,
                        "actor_id": req.actor_id,
                        "mode": req.mode,
                    },
                )

            bootstrap_result = legacy_kernel_bridge.bootstrap(
                portrait_session_id=session_id,
                user_id=user_id,
                actor_type=req.actor_type,
                actor_id=req.actor_id,
            )
            portrait_state_id = str(bootstrap_result["state_update"]["current_state"]["portrait_state_id"])
            legacy_session_id = str(bootstrap_result["legacy_session_id"])
            with get_db_session() as db_session:
                self._link_runtime_ref(
                    db_session,
                    session_id=session_id,
                    user_id=user_id,
                    ref_kind="legacy_kernel_session",
                    ref_value=legacy_session_id,
                    metadata_json={
                        "actor_type": req.actor_type,
                        "actor_id": req.actor_id,
                    },
                )
                self._link_runtime_ref(
                    db_session,
                    session_id=session_id,
                    user_id=user_id,
                    ref_kind="portrait_state",
                    ref_value=portrait_state_id,
                    metadata_json={"source": "legacy_kernel", "source_id": legacy_session_id},
                )
                self._set_step(
                    db_session,
                    session_id=session_id,
                    user_id=user_id,
                    step=bootstrap_result["step"],
                    status=str(bootstrap_result["status"]),
                    result_preview=bootstrap_result["result_preview"],
                    closed_at=(datetime.now(timezone.utc) if str(bootstrap_result["status"]) == "completed" else None),
                )
                self._insert_event(
                    db_session,
                    session_id=session_id,
                    user_id=user_id,
                    event_type="legacy_kernel_bootstrap",
                    event_json={
                        "legacy_session_id": legacy_session_id,
                        "portrait_state_id": portrait_state_id,
                        "bridge_status": bootstrap_result["status"],
                    },
                )
                row = self._get_session_row(db_session, session_id, user_id)
                return self._build_response(
                    db_session=db_session,
                    session_row=row,
                    user_id=user_id,
                    last_response={
                        "input_type": "bootstrap",
                        "legacy_session_id": legacy_session_id,
                        "assistant_content": bootstrap_result["assistant_content"],
                        "state_update": bootstrap_result["state_update"],
                        "bridge_status": bootstrap_result["status"],
                    },
                )

        with get_db_session() as db_session:
            if req.resume_latest:
                latest = portrait_session_repository.get_latest_active_session_row(db_session, user_id)
                if latest:
                    return self._build_response(db_session=db_session, session_row=latest, user_id=user_id)

            now = datetime.now(timezone.utc)
            session_id = f"pts_{uuid4().hex[:16]}"
            step = portrait_orchestration_service.build_initial_step()
            portrait_session_repository.insert_session(
                db_session,
                session_id=session_id,
                user_id=user_id,
                actor_type=req.actor_type,
                actor_id=req.actor_id,
                mode=req.mode,
                status="active",
                current_stage=str(step["stage"]),
                current_input_kind=str(step["input_kind"]),
                current_message=str(step["message"]),
                current_payload_json=_json_db_value(step.get("payload")),
                current_next_hint=step.get("next_hint"),
                result_preview_json=None,
                created_at=now,
            )
            self._insert_event(
                db_session,
                session_id=session_id,
                user_id=user_id,
                event_type="session_started",
                event_json={
                    "actor_type": req.actor_type,
                    "actor_id": req.actor_id,
                    "mode": req.mode,
                },
            )
            row = self._get_session_row(db_session, session_id, user_id)
            return self._build_response(db_session=db_session, session_row=row, user_id=user_id)

    def get_status(self, session_id: str, user_id: int) -> dict[str, Any]:
        with get_db_session() as db_session:
            row = self._get_session_row(db_session, session_id, user_id)
            return self._build_response(db_session=db_session, session_row=row, user_id=user_id)

    def list_sessions(self, user_id: int, *, limit: int = 20) -> dict[str, Any]:
        with get_db_session() as db_session:
            rows = portrait_session_repository.list_session_rows(db_session, user_id, limit=limit)
            latest_active = portrait_session_repository.get_latest_active_session_row(db_session, user_id)
            items: list[dict[str, Any]] = []
            for row in rows:
                session = self._serialize_session_row(row)
                runtime_refs = self._load_runtime_refs(db_session, session["session_id"])
                items.append(
                    {
                        "session": session,
                        "runtime_ref_kinds": sorted(runtime_refs.keys()),
                        "current_portrait_state_id": (
                            runtime_refs.get("portrait_state", {}).get("ref_value")
                            if runtime_refs.get("portrait_state")
                            else None
                        ),
                    }
                )
            return {
                "count": len(items),
                "limit": limit,
                "current_active_session_id": (
                    self._serialize_session_row(latest_active)["session_id"] if latest_active is not None else None
                ),
                "sessions": items,
            }

    def get_result(self, session_id: str, user_id: int) -> dict[str, Any]:
        with get_db_session() as db_session:
            row = self._get_session_row(db_session, session_id, user_id)
            response = self._build_response(db_session=db_session, session_row=row, user_id=user_id)
            response["result"] = {
                "current_state": response["current_state"],
                "result_preview": response["result_preview"],
                "runtime_refs": response["runtime_refs"],
            }
            return response

    def get_history(self, session_id: str, user_id: int, *, limit: int = 20) -> dict[str, Any]:
        with get_db_session() as db_session:
            row = self._get_session_row(db_session, session_id, user_id)
            session = self._serialize_session_row(row)
            runtime_refs = self._load_runtime_refs(db_session, session_id)
            current_state = self._load_current_state(db_session, runtime_refs, user_id)
            event_rows = portrait_session_repository.list_event_rows(db_session, session_id, limit=limit)
            events = [self._serialize_event_row(item) for item in event_rows]
            versions = portrait_state_service.list_versions(user_id)["versions"]
            observations = portrait_state_service.list_observations(user_id)["observations"]
            portrait_state_id = current_state.get("portrait_state_id") if current_state else None
            if portrait_state_id:
                versions = [item for item in versions if item.get("portrait_state_id") == portrait_state_id]
            return {
                "session": session,
                "runtime_refs": runtime_refs,
                "current_state": current_state,
                "events": events,
                "versions": versions[:limit],
                "observations": observations[:limit],
            }

    def reset_session(self, session_id: str, user_id: int) -> dict[str, Any]:
        with get_db_session() as db_session:
            row = self._get_session_row(db_session, session_id, user_id)
            session = self._serialize_session_row(row)
            if session["status"] == "reset":
                return self._build_response(
                    db_session=db_session,
                    session_row=row,
                    user_id=user_id,
                    last_response={"input_type": "reset", "status": "already_reset"},
                )
            ref_map = self._load_runtime_refs(db_session, session_id)

        dialogue_ref = ref_map.get("dialogue_session")
        if dialogue_ref:
            try:
                dialogue_service.close_session(str(dialogue_ref["ref_value"]), user_id)
            except HTTPException:
                pass

        scale_ref = ref_map.get("scale_session")
        if scale_ref:
            try:
                scales_service.abandon_session(str(scale_ref["ref_value"]), user_id)
            except HTTPException:
                pass

        with get_db_session() as db_session:
            current_state = self._load_current_state(db_session, ref_map, user_id)
            step = portrait_orchestration_service.build_reset_step(current_state=current_state)
            now = datetime.now(timezone.utc)
            self._set_step(
                db_session,
                session_id=session_id,
                user_id=user_id,
                step=step,
                status="reset",
                result_preview=step.get("payload", {}).get("result_preview"),
                closed_at=now,
            )
            self._insert_event(
                db_session,
                session_id=session_id,
                user_id=user_id,
                event_type="session_reset",
                event_json={"dialogue_closed": dialogue_ref is not None, "scale_abandoned": scale_ref is not None},
            )
            row = self._get_session_row(db_session, session_id, user_id)
            return self._build_response(
                db_session=db_session,
                session_row=row,
                user_id=user_id,
                last_response={"input_type": "reset", "status": "reset"},
            )

    async def respond(self, session_id: str, req: PortraitSessionRespondRequest, user_id: int) -> dict[str, Any]:
        with get_db_session() as db_session:
            row = self._get_session_row(db_session, session_id, user_id)
            session = self._serialize_session_row(row)
            ref_map = self._load_runtime_refs(db_session, session_id)

        if session["mode"] == "legacy_product":
            if session["status"] == "completed":
                raise HTTPException(
                    status_code=409,
                    detail={"code": "portrait_session_completed", "session_id": session_id},
                )
            normalized = self._normalize_legacy_request(req)
            if normalized["action"] == "reset":
                return self.reset_session(session_id, user_id)
            if normalized["action"] == "product_choice":
                return await self._respond_product_action(
                    session_id,
                    str(normalized["choice"]),
                    user_id,
                    session,
                    ref_map,
                    return_surface="dialogue",
                )
            return self._respond_legacy_kernel(
                session_id=session_id,
                user_id=user_id,
                session=session,
                user_message=str(normalized["user_message"]),
                input_type=str(normalized["input_type"]),
                input_value=normalized["value"],
            )

        if req.choice is not None:
            return await self._respond_choice(session_id, req.choice, user_id)
        if req.text and req.text.strip():
            return await self._respond_text(session_id, req.text.strip(), user_id)
        if req.external_text and req.external_text.strip():
            return self._respond_external_import(session_id, payload_text=req.external_text.strip(), payload_json=None, user_id=user_id)
        if req.external_json is not None:
            return self._respond_external_import(session_id, payload_text=None, payload_json=req.external_json, user_id=user_id)
        if req.confirm:
            return self._respond_confirm(session_id, user_id)
        raise HTTPException(
            status_code=400,
            detail={
                "code": "unsupported_portrait_session_input",
                "supported": ["choice", "text", "external_text", "external_json", "confirm"],
            },
        )

    async def _respond_choice(self, session_id: str, choice_value: Any, user_id: int) -> dict[str, Any]:
        with get_db_session() as db_session:
            row = self._get_session_row(db_session, session_id, user_id)
            session = self._serialize_session_row(row)
            if session["status"] == "completed":
                raise HTTPException(
                    status_code=409,
                    detail={"code": "portrait_session_completed", "session_id": session_id},
                )
            ref_map = self._load_runtime_refs(db_session, session_id)
            policy = self._current_policy(session)

        if session["mode"] == "legacy_product" and policy:
            return await self._respond_policy_choice(session_id, choice_value, user_id, session, ref_map, policy)

        if session["current_stage"] == "scale_question":
            return self._respond_scale_choice(session_id, choice_value, user_id)

        normalized_choice = str(choice_value).strip()
        if normalized_choice == "continue_dialogue":
            with get_db_session() as db_session:
                step = portrait_orchestration_service.build_dialogue_followup_step(
                    generated_message=None,
                    current_state=self._load_current_state(db_session, ref_map, user_id),
                )
                self._set_step(db_session, session_id=session_id, user_id=user_id, step=step, result_preview=session["result_preview_json"])
                self._insert_event(
                    db_session,
                    session_id=session_id,
                    user_id=user_id,
                    event_type="respond_choice",
                    event_json={"choice": normalized_choice},
                )
                row = self._get_session_row(db_session, session_id, user_id)
                return self._build_response(
                    db_session=db_session,
                    session_row=row,
                    user_id=user_id,
                    last_response={"input_type": "choice", "choice": normalized_choice, "status": "continued"},
                )

        if normalized_choice.startswith("scale:"):
            scale_id = normalized_choice.split(":", 1)[1].strip()
            if not scale_id:
                raise HTTPException(status_code=400, detail={"code": "invalid_scale_choice", "choice": normalized_choice})
            return self._respond_start_scale(session_id, scale_id, user_id, session, ref_map)

        if normalized_choice == "prompt_handoff":
            return self._respond_prompt_handoff(session_id, user_id, session, ref_map)

        if self._is_product_choice(normalized_choice):
            return await self._respond_product_action(
                session_id,
                normalized_choice,
                user_id,
                session,
                ref_map,
                return_surface="dialogue",
            )

        raise HTTPException(
            status_code=400,
            detail={
                "code": "unsupported_portrait_session_choice",
                "choice": normalized_choice,
            },
        )

    async def _respond_text(self, session_id: str, text_value: str, user_id: int) -> dict[str, Any]:
        with get_db_session() as db_session:
            row = self._get_session_row(db_session, session_id, user_id)
            session = self._serialize_session_row(row)
            if session["status"] == "completed":
                raise HTTPException(
                    status_code=409,
                    detail={"code": "portrait_session_completed", "session_id": session_id},
                )
            ref_map = self._runtime_ref_map(portrait_session_repository.list_runtime_ref_rows(db_session, session_id))
            policy = self._current_policy(session)

        if session["mode"] == "legacy_product" and policy:
            if str(policy.get("step_id")) == "ai_memory_reply":
                return self._respond_external_import(
                    session_id,
                    payload_text=text_value,
                    payload_json=None,
                    user_id=user_id,
                )
            return self._respond_policy_text(session_id, text_value, user_id, session, ref_map, policy)

        dialogue_ref = ref_map.get("dialogue_session")
        if dialogue_ref:
            dialogue_session_id = str(dialogue_ref["ref_value"])
        else:
            dialogue_start = dialogue_service.start_session(
                actor_type=session["actor_type"],
                actor_id=session["actor_id"],
                user_id=user_id,
            )
            dialogue_session_id = str(dialogue_start["session"]["session_id"])
            with get_db_session() as db_session:
                self._link_runtime_ref(
                    db_session,
                    session_id=session_id,
                    user_id=user_id,
                    ref_kind="dialogue_session",
                    ref_value=dialogue_session_id,
                    metadata_json={
                        "actor_type": session["actor_type"],
                        "actor_id": session["actor_id"],
                    },
                )

        dialogue_payload = await dialogue_service.append_message(
            dialogue_session_id,
            "user",
            text_value,
            None,
            "portrait_session",
            user_id,
            generate_reply=True,
        )
        state_update = portrait_state_service.apply_update(
            PortraitStateUpdateRequest(
                source_type="dialogue_session",
                source_id=dialogue_session_id,
            ),
            user_id,
        )
        portrait_state_id = str(state_update["current_state"]["portrait_state_id"])

        followup = portrait_orchestration_service.build_dialogue_followup_step(
            generated_message=dialogue_payload.get("generated_message"),
            current_state=state_update["current_state"],
        )
        now = datetime.now(timezone.utc)

        with get_db_session() as db_session:
            self._link_runtime_ref(
                db_session,
                session_id=session_id,
                user_id=user_id,
                ref_kind="portrait_state",
                ref_value=portrait_state_id,
                metadata_json={"source": "dialogue_session", "source_id": dialogue_session_id},
            )
            self._set_step(
                db_session,
                session_id=session_id,
                user_id=user_id,
                step=followup,
                result_preview={
                    "portrait_state_id": portrait_state_id,
                    "source_type": "dialogue_session",
                    "source_id": dialogue_session_id,
                },
            )
            self._insert_event(
                db_session,
                session_id=session_id,
                user_id=user_id,
                event_type="respond_text",
                event_json={"text": text_value, "dialogue_session_id": dialogue_session_id},
            )
            self._insert_event(
                db_session,
                session_id=session_id,
                user_id=user_id,
                event_type="portrait_state_materialized",
                event_json={
                    "portrait_state_id": portrait_state_id,
                    "source_type": "dialogue_session",
                    "source_id": dialogue_session_id,
                },
            )
            row = self._get_session_row(db_session, session_id, user_id)
            return self._build_response(
                db_session=db_session,
                session_row=row,
                user_id=user_id,
                last_response={
                    "input_type": "text",
                    "accepted_message": dialogue_payload.get("accepted_message"),
                    "generated_message": dialogue_payload.get("generated_message"),
                    "generation_status": dialogue_payload.get("generation_status"),
                },
            )

    async def _respond_policy_choice(
        self,
        session_id: str,
        choice_value: Any,
        user_id: int,
        session: dict[str, Any],
        ref_map: dict[str, Any],
        policy: dict[str, Any],
    ) -> dict[str, Any]:
        normalized_choice = str(choice_value).strip()
        step_id = str(policy.get("step_id") or "")
        skill_id = str(policy.get("skill_id") or "collect-basic-info")
        policy_state = policy.get("policy_state") or {}

        if normalized_choice == "back_to_review":
            with get_db_session() as db_session:
                current_state = self._load_current_state(db_session, ref_map, user_id)
                step = portrait_review_service.build_review_step(current_state=current_state)
                self._set_step(
                    db_session,
                    session_id=session_id,
                    user_id=user_id,
                    step=step,
                    result_preview=session["result_preview_json"],
                )
                row = self._get_session_row(db_session, session_id, user_id)
                return self._build_response(
                    db_session=db_session,
                    session_row=row,
                    user_id=user_id,
                    last_response={"input_type": "choice", "choice": normalized_choice, "status": "returned_to_review"},
                )

        if step_id == "welcome_start_method":
            if normalized_choice == "ai_memory":
                handoff_payload = prompt_handoff_service.create_handoff(
                    PromptHandoffCreateRequest(
                        prompt_kind="ai_memory",
                        note_text="请根据你对我的真实长期记忆，尽量完整填写科研数字分身提取请求中的 A-F 模块。",
                    ),
                    user_id,
                )
                handoff = handoff_payload["handoff"]
                prompt_text = next(
                    (
                        item.get("content_text")
                        for item in handoff_payload["artifacts"]
                        if item.get("artifact_type") == "prompt_text"
                    ),
                    "",
                )
                with get_db_session() as db_session:
                    current_state = self._load_current_state(db_session, ref_map, user_id)
                    self._link_runtime_ref(
                        db_session,
                        session_id=session_id,
                        user_id=user_id,
                        ref_kind="prompt_handoff",
                        ref_value=str(handoff["handoff_id"]),
                        metadata_json={"prompt_kind": "ai_memory"},
                    )
                    step = portrait_skill_policy_service.build_ai_memory_import_step(
                        prompt_text=prompt_text,
                        handoff=handoff,
                        current_state=current_state,
                    )
                    self._set_step(
                        db_session,
                        session_id=session_id,
                        user_id=user_id,
                        step=step,
                        result_preview=session["result_preview_json"],
                    )
                    self._insert_event(
                        db_session,
                        session_id=session_id,
                        user_id=user_id,
                        event_type="legacy_skill_choice",
                        event_json={"skill_id": skill_id, "step_id": step_id, "choice": normalized_choice},
                    )
                    row = self._get_session_row(db_session, session_id, user_id)
                    return self._build_response(
                        db_session=db_session,
                        session_row=row,
                        user_id=user_id,
                        last_response={
                            "input_type": "choice",
                            "choice": normalized_choice,
                            "handoff": handoff,
                            "artifacts": handoff_payload["artifacts"],
                        },
                    )

            if normalized_choice == "direct":
                with get_db_session() as db_session:
                    current_state = self._load_current_state(db_session, ref_map, user_id)
                    step = portrait_skill_policy_service.next_basic_info_step(current_state=current_state)
                    if step is None:
                        # Release the current SQLite write transaction before the
                        # inference/state materialization path opens its own session.
                        db_session.commit()
                        return self._finalize_legacy_basic_info(
                            db_session=db_session,
                            session_id=session_id,
                            user_id=user_id,
                            current_state=current_state or {"state_json": {}},
                            last_response={"input_type": "choice", "choice": normalized_choice, "status": "basic_info_completed"},
                        )
                    self._set_step(
                        db_session,
                        session_id=session_id,
                        user_id=user_id,
                        step=step,
                        result_preview=session["result_preview_json"],
                    )
                    self._insert_event(
                        db_session,
                        session_id=session_id,
                        user_id=user_id,
                        event_type="legacy_skill_choice",
                        event_json={"skill_id": skill_id, "step_id": step_id, "choice": normalized_choice},
                    )
                    row = self._get_session_row(db_session, session_id, user_id)
                    return self._build_response(
                        db_session=db_session,
                        session_row=row,
                        user_id=user_id,
                        last_response={"input_type": "choice", "choice": normalized_choice, "status": "advanced"},
                    )

        if step_id in {"basic_research_stage", "update_basic_research_stage"}:
            state_update = self._manual_portrait_state_update(
                user_id=user_id,
                skill_id=skill_id,
                step_id=step_id,
                state_patch_json={"profile": {"basic_info": {"research_stage": normalized_choice}}},
                source_label="legacy_skill_basic_info" if step_id == "basic_research_stage" else "legacy_skill_update",
            )
            portrait_state_id = str(state_update["current_state"]["portrait_state_id"])
            with get_db_session() as db_session:
                self._link_runtime_ref(
                    db_session,
                    session_id=session_id,
                    user_id=user_id,
                    ref_kind="portrait_state",
                    ref_value=portrait_state_id,
                    metadata_json={"source": "manual", "step_id": step_id},
                )
                self._insert_event(
                    db_session,
                    session_id=session_id,
                    user_id=user_id,
                    event_type="legacy_skill_choice",
                    event_json={"skill_id": skill_id, "step_id": step_id, "choice": normalized_choice},
                )
                if step_id == "update_basic_research_stage":
                    db_session.commit()
                    return self._finalize_legacy_basic_info(
                        db_session=db_session,
                        session_id=session_id,
                        user_id=user_id,
                        current_state=state_update["current_state"],
                        last_response={"input_type": "choice", "choice": normalized_choice, "state_update": state_update, "status": "review_updated"},
                    )
                step = portrait_skill_policy_service.next_basic_info_step(current_state=state_update["current_state"])
                self._set_step(
                    db_session,
                    session_id=session_id,
                    user_id=user_id,
                    step=step,
                    result_preview={"portrait_state_id": portrait_state_id, "source_type": "manual", "step_id": step_id},
                )
                row = self._get_session_row(db_session, session_id, user_id)
                return self._build_response(
                    db_session=db_session,
                    session_row=row,
                    user_id=user_id,
                    last_response={
                        "input_type": "choice",
                        "choice": normalized_choice,
                        "state_update": state_update,
                    },
                )

        if step_id in {"basic_method_paradigm", "update_basic_method"}:
            state_update = self._manual_portrait_state_update(
                user_id=user_id,
                skill_id=skill_id,
                step_id=step_id,
                state_patch_json={"profile": {"basic_info": {"method_paradigm": normalized_choice}}},
                source_label="legacy_skill_basic_info" if step_id == "basic_method_paradigm" else "legacy_skill_update",
            )
            portrait_state_id = str(state_update["current_state"]["portrait_state_id"])
            with get_db_session() as db_session:
                self._link_runtime_ref(
                    db_session,
                    session_id=session_id,
                    user_id=user_id,
                    ref_kind="portrait_state",
                    ref_value=portrait_state_id,
                    metadata_json={"source": "manual", "step_id": step_id},
                )
                self._insert_event(
                    db_session,
                    session_id=session_id,
                    user_id=user_id,
                    event_type="legacy_skill_choice",
                    event_json={"skill_id": skill_id, "step_id": step_id, "choice": normalized_choice},
                )
                if step_id == "update_basic_method":
                    db_session.commit()
                    return self._finalize_legacy_basic_info(
                        db_session=db_session,
                        session_id=session_id,
                        user_id=user_id,
                        current_state=state_update["current_state"],
                        last_response={"input_type": "choice", "choice": normalized_choice, "state_update": state_update, "status": "review_updated"},
                    )
                step = portrait_skill_policy_service.next_basic_info_step(current_state=state_update["current_state"])
                self._set_step(
                    db_session,
                    session_id=session_id,
                    user_id=user_id,
                    step=step,
                    result_preview={"portrait_state_id": portrait_state_id, "source_type": "manual", "step_id": step_id},
                )
                row = self._get_session_row(db_session, session_id, user_id)
                return self._build_response(
                    db_session=db_session,
                    session_row=row,
                    user_id=user_id,
                    last_response={
                        "input_type": "choice",
                        "choice": normalized_choice,
                        "state_update": state_update,
                    },
                )

        if step_id == "needs_time_feeling":
            state_update = self._manual_portrait_state_update(
                user_id=user_id,
                skill_id=skill_id,
                step_id=step_id,
                state_patch_json={"profile": {"current_needs": {"time_feeling": "" if normalized_choice == "skip" else normalized_choice}}},
                source_label="legacy_skill_current_needs",
            )
            portrait_state_id = str(state_update["current_state"]["portrait_state_id"])
            with get_db_session() as db_session:
                self._link_runtime_ref(
                    db_session,
                    session_id=session_id,
                    user_id=user_id,
                    ref_kind="portrait_state",
                    ref_value=portrait_state_id,
                    metadata_json={"source": "manual", "step_id": step_id},
                )
                step = portrait_skill_policy_service.next_basic_info_step(current_state=state_update["current_state"])
                self._set_step(
                    db_session,
                    session_id=session_id,
                    user_id=user_id,
                    step=step,
                    result_preview={"portrait_state_id": portrait_state_id, "source_type": "manual", "step_id": step_id},
                )
                self._insert_event(
                    db_session,
                    session_id=session_id,
                    user_id=user_id,
                    event_type="legacy_skill_choice",
                    event_json={"skill_id": skill_id, "step_id": step_id, "choice": normalized_choice},
                )
                row = self._get_session_row(db_session, session_id, user_id)
                return self._build_response(
                    db_session=db_session,
                    session_row=row,
                    user_id=user_id,
                    last_response={"input_type": "choice", "choice": normalized_choice, "state_update": state_update},
                )

        if step_id == "needs_help_type":
            state_update = self._manual_portrait_state_update(
                user_id=user_id,
                skill_id=skill_id,
                step_id=step_id,
                state_patch_json={"profile": {"current_needs": {"desired_support": "" if normalized_choice == "skip" else normalized_choice}}},
                source_label="legacy_skill_current_needs",
            )
            portrait_state_id = str(state_update["current_state"]["portrait_state_id"])
            with get_db_session() as db_session:
                self._link_runtime_ref(
                    db_session,
                    session_id=session_id,
                    user_id=user_id,
                    ref_kind="portrait_state",
                    ref_value=portrait_state_id,
                    metadata_json={"source": "manual", "step_id": step_id},
                )
                step = portrait_skill_policy_service.next_basic_info_step(current_state=state_update["current_state"])
                self._set_step(
                    db_session,
                    session_id=session_id,
                    user_id=user_id,
                    step=step,
                    result_preview={"portrait_state_id": portrait_state_id, "source_type": "manual", "step_id": step_id},
                )
                self._insert_event(
                    db_session,
                    session_id=session_id,
                    user_id=user_id,
                    event_type="legacy_skill_choice",
                    event_json={"skill_id": skill_id, "step_id": step_id, "choice": normalized_choice},
                )
                row = self._get_session_row(db_session, session_id, user_id)
                return self._build_response(
                    db_session=db_session,
                    session_row=row,
                    user_id=user_id,
                    last_response={"input_type": "choice", "choice": normalized_choice, "state_update": state_update},
                )

        if step_id == "needs_desired_change":
            if normalized_choice == "其他":
                with get_db_session() as db_session:
                    step = portrait_skill_policy_service.build_basic_info_step(
                        "needs_desired_change_text",
                        current_state=self._load_current_state(db_session, ref_map, user_id),
                    )
                    self._set_step(
                        db_session,
                        session_id=session_id,
                        user_id=user_id,
                        step=step,
                        result_preview=session["result_preview_json"],
                    )
                    self._insert_event(
                        db_session,
                        session_id=session_id,
                        user_id=user_id,
                        event_type="legacy_skill_choice",
                        event_json={"skill_id": skill_id, "step_id": step_id, "choice": normalized_choice},
                    )
                    row = self._get_session_row(db_session, session_id, user_id)
                    return self._build_response(
                        db_session=db_session,
                        session_row=row,
                        user_id=user_id,
                        last_response={"input_type": "choice", "choice": normalized_choice, "status": "awaiting_text"},
                    )
            state_update = self._manual_portrait_state_update(
                user_id=user_id,
                skill_id=skill_id,
                step_id=step_id,
                state_patch_json={"profile": {"current_needs": {"desired_change": normalized_choice}}},
                source_label="legacy_skill_current_needs",
            )
            portrait_state_id = str(state_update["current_state"]["portrait_state_id"])
            with get_db_session() as db_session:
                self._link_runtime_ref(
                    db_session,
                    session_id=session_id,
                    user_id=user_id,
                    ref_kind="portrait_state",
                    ref_value=portrait_state_id,
                    metadata_json={"source": "manual", "step_id": step_id},
                )
                db_session.commit()
                return self._finalize_legacy_basic_info(
                    db_session=db_session,
                    session_id=session_id,
                    user_id=user_id,
                    current_state=state_update["current_state"],
                    last_response={"input_type": "choice", "choice": normalized_choice, "status": "basic_info_completed"},
                )

        if step_id == "process_rating":
            dimension_key = str(policy_state.get("dimension_key") or "")
            try:
                numeric_score = float(normalized_choice)
            except ValueError as exc:
                raise HTTPException(status_code=400, detail={"code": "invalid_process_rating_value", "choice": normalized_choice}) from exc
            state_update = self._manual_portrait_state_update(
                user_id=user_id,
                skill_id=skill_id,
                step_id=f"process_rating:{dimension_key}",
                state_patch_json={"profile": {"capability": {"process": {dimension_key: {"score": numeric_score}}}}},
                source_label="legacy_skill_process_ability",
            )
            portrait_state_id = str(state_update["current_state"]["portrait_state_id"])
            with get_db_session() as db_session:
                self._link_runtime_ref(
                    db_session,
                    session_id=session_id,
                    user_id=user_id,
                    ref_kind="portrait_state",
                    ref_value=portrait_state_id,
                    metadata_json={"source": "manual", "step_id": f'process_rating:{dimension_key}'},
                )
                step = portrait_skill_policy_service.build_basic_info_step(
                    f"process_detail:{dimension_key}",
                    current_state=state_update["current_state"],
                )
                self._set_step(
                    db_session,
                    session_id=session_id,
                    user_id=user_id,
                    step=step,
                    result_preview={"portrait_state_id": portrait_state_id, "source_type": "manual", "step_id": f'process_rating:{dimension_key}'},
                )
                self._insert_event(
                    db_session,
                    session_id=session_id,
                    user_id=user_id,
                    event_type="legacy_skill_choice",
                    event_json={"skill_id": skill_id, "step_id": f"process_rating:{dimension_key}", "choice": numeric_score},
                )
                row = self._get_session_row(db_session, session_id, user_id)
                return self._build_response(
                    db_session=db_session,
                    session_row=row,
                    user_id=user_id,
                    last_response={"input_type": "choice", "choice": numeric_score, "state_update": state_update},
                )

        if step_id == "review_summary":
            if normalized_choice == "confirm_review":
                review_update = self._manual_portrait_state_update(
                    user_id=user_id,
                    skill_id="review-profile",
                    step_id="confirm_review",
                    state_patch_json={"profile": {"meta": {"collection_stage": "review_done"}, "review": {"status": "confirmed"}}},
                    source_label="legacy_skill_review",
                )
                current_state = review_update["current_state"]
                portrait_state_id = str(current_state["portrait_state_id"])
                with get_db_session() as db_session:
                    self._insert_event(
                        db_session,
                        session_id=session_id,
                        user_id=user_id,
                        event_type="review_confirmed",
                        event_json={"portrait_state_id": portrait_state_id},
                    )
                    step = portrait_orchestration_service.build_completed_step(current_state=current_state)
                    self._set_step(
                        db_session,
                        session_id=session_id,
                        user_id=user_id,
                        step=step,
                        status="completed",
                        result_preview={"portrait_state_id": portrait_state_id, "source_type": "manual", "source_id": "review-profile"},
                        closed_at=datetime.now(timezone.utc),
                    )
                    row = self._get_session_row(db_session, session_id, user_id)
                    return self._build_response(
                        db_session=db_session,
                        session_row=row,
                        user_id=user_id,
                        last_response={"input_type": "choice", "choice": normalized_choice, "status": "review_done", "state_update": review_update},
                    )
            if normalized_choice == "update_basic_identity":
                step = portrait_review_service.build_update_basic_identity_step()
            elif normalized_choice == "update_tech_capability":
                step = portrait_review_service.build_text_update_step(
                    step_id="update_tech_capability",
                    question="请重新填写主要编程语言和科研工具，并大致说明熟练程度。",
                    placeholder="例如：Python（熟练）、MATLAB（入门）、fMRIPrep（日常使用）",
                    policy_state={},
                )
            elif normalized_choice == "update_process_ability":
                step = portrait_review_service.build_update_process_select_step()
            elif normalized_choice == "update_current_needs":
                step = portrait_review_service.build_update_needs_select_step()
            elif normalized_choice == "history":
                history_payload = self.get_history(session_id, user_id, limit=20)
                step = portrait_review_service.build_history_step(history_payload=history_payload)
            elif normalized_choice == "reset_now":
                return self.reset_session(session_id, user_id)
            elif normalized_choice.startswith("scale:"):
                scale_id = normalized_choice.split(":", 1)[1].strip()
                return self._respond_start_scale(session_id, scale_id, user_id, session, ref_map)
            elif normalized_choice == "prompt_handoff":
                return self._respond_prompt_handoff(session_id, user_id, session, ref_map)
            elif self._is_product_choice(normalized_choice):
                return await self._respond_product_action(
                    session_id,
                    normalized_choice,
                    user_id,
                    session,
                    ref_map,
                    return_surface="review",
                )
            else:
                raise HTTPException(
                    status_code=400,
                    detail={"code": "unsupported_review_choice", "choice": normalized_choice},
                )
            with get_db_session() as db_session:
                self._set_step(
                    db_session,
                    session_id=session_id,
                    user_id=user_id,
                    step=step,
                    result_preview=session["result_preview_json"],
                )
                self._insert_event(
                    db_session,
                    session_id=session_id,
                    user_id=user_id,
                    event_type="review_choice",
                    event_json={"choice": normalized_choice},
                )
                row = self._get_session_row(db_session, session_id, user_id)
                return self._build_response(
                    db_session=db_session,
                    session_row=row,
                    user_id=user_id,
                    last_response={"input_type": "choice", "choice": normalized_choice},
                )

        if step_id == "update_basic_identity":
            if normalized_choice == "back_to_review":
                with get_db_session() as db_session:
                    current_state = self._load_current_state(db_session, ref_map, user_id)
                    step = portrait_review_service.build_review_step(current_state=current_state)
                    self._set_step(db_session, session_id=session_id, user_id=user_id, step=step, result_preview=session["result_preview_json"])
                    row = self._get_session_row(db_session, session_id, user_id)
                    return self._build_response(db_session=db_session, session_row=row, user_id=user_id, last_response={"input_type": "choice", "choice": normalized_choice})
            with get_db_session() as db_session:
                current_state = self._load_current_state(db_session, ref_map, user_id)
                if normalized_choice == "research_stage":
                    step = portrait_skill_policy_service.build_basic_info_step("basic_research_stage", current_state=current_state)
                    step["payload"]["policy"]["skill_id"] = "update-profile"
                    step["payload"]["policy"]["step_id"] = "update_basic_research_stage"
                elif normalized_choice == "fields":
                    step = portrait_review_service.build_text_update_step(
                        step_id="update_basic_fields",
                        question="请重新填写一级领域、二级方向和交叉方向。",
                        placeholder="例如：认知科学；计算神经科学；交叉 AI 与脑科学",
                        policy_state={},
                    )
                elif normalized_choice == "method":
                    step = portrait_skill_policy_service.build_basic_info_step("basic_method_paradigm", current_state=current_state)
                    step["payload"]["policy"]["skill_id"] = "update-profile"
                    step["payload"]["policy"]["step_id"] = "update_basic_method"
                elif normalized_choice == "institution":
                    step = portrait_review_service.build_text_update_step(
                        step_id="update_basic_institution",
                        question="请重新填写所在机构。",
                        placeholder="例如：中国科学院国家天文台",
                        policy_state={},
                    )
                elif normalized_choice == "advisor_team":
                    step = portrait_review_service.build_text_update_step(
                        step_id="update_basic_advisor_team",
                        question="请重新填写导师姓名和团队方向。",
                        placeholder="例如：张教授，团队做计算神经科学；无导师可填“无”。",
                        policy_state={},
                    )
                elif normalized_choice == "academic_network":
                    step = portrait_review_service.build_text_update_step(
                        step_id="update_basic_academic_network",
                        question="请重新填写你的学术合作圈情况。",
                        placeholder="例如：实验室内部为主，也有跨机构合作。",
                        policy_state={},
                    )
                else:
                    raise HTTPException(status_code=400, detail={"code": "unsupported_update_basic_choice", "choice": normalized_choice})
                self._set_step(
                    db_session,
                    session_id=session_id,
                    user_id=user_id,
                    step=step,
                    result_preview=session["result_preview_json"],
                )
                row = self._get_session_row(db_session, session_id, user_id)
                return self._build_response(db_session=db_session, session_row=row, user_id=user_id, last_response={"input_type": "choice", "choice": normalized_choice})

        if step_id == "update_process_select":
            if normalized_choice == "back_to_review":
                with get_db_session() as db_session:
                    current_state = self._load_current_state(db_session, ref_map, user_id)
                    step = portrait_review_service.build_review_step(current_state=current_state)
                    self._set_step(db_session, session_id=session_id, user_id=user_id, step=step, result_preview=session["result_preview_json"])
                    row = self._get_session_row(db_session, session_id, user_id)
                    return self._build_response(db_session=db_session, session_row=row, user_id=user_id, last_response={"input_type": "choice", "choice": normalized_choice})
            if normalized_choice not in dict(PROCESS_DIMENSIONS):
                raise HTTPException(status_code=400, detail={"code": "unsupported_process_dimension", "choice": normalized_choice})
            step = portrait_review_service.build_process_rating_step(dimension_key=normalized_choice)
            with get_db_session() as db_session:
                self._set_step(db_session, session_id=session_id, user_id=user_id, step=step, result_preview=session["result_preview_json"])
                row = self._get_session_row(db_session, session_id, user_id)
                return self._build_response(db_session=db_session, session_row=row, user_id=user_id, last_response={"input_type": "choice", "choice": normalized_choice})

        if step_id == "update_process_rating":
            dimension_key = str(policy_state.get("dimension_key") or "")
            try:
                numeric_score = float(normalized_choice)
            except ValueError as exc:
                raise HTTPException(status_code=400, detail={"code": "invalid_process_update_rating", "choice": normalized_choice}) from exc
            with get_db_session() as db_session:
                step = portrait_review_service.build_process_detail_step(dimension_key=dimension_key, score=numeric_score)
                self._set_step(db_session, session_id=session_id, user_id=user_id, step=step, result_preview=session["result_preview_json"])
                row = self._get_session_row(db_session, session_id, user_id)
                return self._build_response(db_session=db_session, session_row=row, user_id=user_id, last_response={"input_type": "choice", "choice": numeric_score})

        if step_id == "update_needs_select":
            if normalized_choice == "back_to_review":
                with get_db_session() as db_session:
                    current_state = self._load_current_state(db_session, ref_map, user_id)
                    step = portrait_review_service.build_review_step(current_state=current_state)
                    self._set_step(db_session, session_id=session_id, user_id=user_id, step=step, result_preview=session["result_preview_json"])
                    row = self._get_session_row(db_session, session_id, user_id)
                    return self._build_response(db_session=db_session, session_row=row, user_id=user_id, last_response={"input_type": "choice", "choice": normalized_choice})
            question_map = {
                "major_time_occupation": ("update_needs_time_occupation", "请重新填写当前主要时间占用。", "例如：论文写作、数据分析、沟通协调。"),
                "pain_points": ("update_needs_pain_points", "请重新填写当前核心难点。", "例如：论文故事线组织困难。"),
                "desired_change": ("update_needs_desired_change", "请重新填写你最想改变的那件事。", "例如：希望提升论文推进效率。"),
            }
            if normalized_choice not in question_map:
                raise HTTPException(status_code=400, detail={"code": "unsupported_needs_update_choice", "choice": normalized_choice})
            step_id_text, question, placeholder = question_map[normalized_choice]
            step = portrait_review_service.build_text_update_step(
                step_id=step_id_text,
                question=question,
                placeholder=placeholder,
                policy_state={},
            )
            with get_db_session() as db_session:
                self._set_step(db_session, session_id=session_id, user_id=user_id, step=step, result_preview=session["result_preview_json"])
                row = self._get_session_row(db_session, session_id, user_id)
                return self._build_response(db_session=db_session, session_row=row, user_id=user_id, last_response={"input_type": "choice", "choice": normalized_choice})

        raise HTTPException(
            status_code=400,
            detail={
                "code": "unsupported_legacy_skill_choice",
                "choice": normalized_choice,
                "skill_id": skill_id,
                "step_id": step_id,
            },
        )

    def _respond_policy_text(
        self,
        session_id: str,
        text_value: str,
        user_id: int,
        session: dict[str, Any],
        ref_map: dict[str, Any],
        policy: dict[str, Any],
    ) -> dict[str, Any]:
        step_id = str(policy.get("step_id") or "")
        skill_id = str(policy.get("skill_id") or "collect-basic-info")
        policy_state = policy.get("policy_state") or {}
        normalized_text = text_value.strip()
        state_patch_json: dict[str, Any]
        source_label = "legacy_skill_basic_info"
        post_collection = True

        if step_id == "basic_primary_secondary_fields":
            state_patch_json = {"profile": {"basic_info": portrait_skill_policy_service.parse_field_statement(normalized_text)}}
        elif step_id == "basic_institution":
            state_patch_json = {"profile": {"basic_info": {"institution": normalized_text}}}
        elif step_id == "basic_advisor_team":
            state_patch_json = {"profile": {"basic_info": {"advisor_team": normalized_text}}}
        elif step_id == "basic_academic_network":
            state_patch_json = {"profile": {"basic_info": {"academic_network": normalized_text}}}
        elif step_id == "process_detail":
            dimension_key = str(policy_state.get("dimension_key") or "")
            state_patch_json = {
                "profile": {
                    "capability": {
                        "process": {
                            dimension_key: {
                                "note": "" if normalized_text == "跳过" else normalized_text,
                            }
                        }
                    }
                }
            }
            source_label = "legacy_skill_process_ability"
        elif step_id == "capability_tech_stack":
            state_patch_json = {"profile": {"capability": {"tech_stack_text": normalized_text}}}
            source_label = "legacy_skill_capability"
        elif step_id == "capability_outputs":
            state_patch_json = {
                "profile": {
                    "capability": {
                        "representative_outputs": "" if normalized_text == "跳过" else normalized_text,
                    }
                }
            }
            source_label = "legacy_skill_capability"
        elif step_id == "needs_time_occupation":
            state_patch_json = {"profile": {"current_needs": {"major_time_occupation": normalized_text}}}
            source_label = "legacy_skill_current_needs"
        elif step_id == "needs_pain_points":
            state_patch_json = {"profile": {"current_needs": {"pain_points": normalized_text}}}
            source_label = "legacy_skill_current_needs"
        elif step_id == "needs_desired_change_text":
            state_patch_json = {"profile": {"current_needs": {"desired_change": normalized_text}}}
            source_label = "legacy_skill_current_needs"
        elif step_id == "update_basic_fields":
            state_patch_json = {"profile": {"basic_info": portrait_skill_policy_service.parse_field_statement(normalized_text)}}
            source_label = "legacy_skill_update"
            post_collection = False
        elif step_id == "update_basic_institution":
            state_patch_json = {"profile": {"basic_info": {"institution": normalized_text}}}
            source_label = "legacy_skill_update"
            post_collection = False
        elif step_id == "update_basic_advisor_team":
            state_patch_json = {"profile": {"basic_info": {"advisor_team": normalized_text}}}
            source_label = "legacy_skill_update"
            post_collection = False
        elif step_id == "update_basic_academic_network":
            state_patch_json = {"profile": {"basic_info": {"academic_network": normalized_text}}}
            source_label = "legacy_skill_update"
            post_collection = False
        elif step_id == "update_tech_capability":
            state_patch_json = {"profile": {"capability": {"tech_stack_text": normalized_text}}}
            source_label = "legacy_skill_update"
            post_collection = False
        elif step_id == "update_needs_time_occupation":
            state_patch_json = {"profile": {"current_needs": {"major_time_occupation": normalized_text}}}
            source_label = "legacy_skill_update"
            post_collection = False
        elif step_id == "update_needs_pain_points":
            state_patch_json = {"profile": {"current_needs": {"pain_points": normalized_text}}}
            source_label = "legacy_skill_update"
            post_collection = False
        elif step_id == "update_needs_desired_change":
            state_patch_json = {"profile": {"current_needs": {"desired_change": normalized_text}}}
            source_label = "legacy_skill_update"
            post_collection = False
        elif step_id == "update_process_detail":
            dimension_key = str(policy_state.get("dimension_key") or "")
            score = float(policy_state.get("score") or 0)
            state_patch_json = {
                "profile": {
                    "capability": {
                        "process": {
                            dimension_key: {
                                "score": score,
                                "note": "" if normalized_text == "跳过" else normalized_text,
                            }
                        }
                    }
                }
            }
            source_label = "legacy_skill_update"
            post_collection = False
        else:
            raise HTTPException(
                status_code=400,
                detail={"code": "unsupported_legacy_skill_text", "skill_id": skill_id, "step_id": step_id},
            )

        state_update = self._manual_portrait_state_update(
            user_id=user_id,
            skill_id=skill_id,
            step_id=step_id,
            state_patch_json=state_patch_json,
            source_label=source_label,
        )
        portrait_state_id = str(state_update["current_state"]["portrait_state_id"])
        with get_db_session() as db_session:
            self._link_runtime_ref(
                db_session,
                session_id=session_id,
                user_id=user_id,
                ref_kind="portrait_state",
                ref_value=portrait_state_id,
                metadata_json={"source": "manual", "step_id": step_id},
            )
            self._insert_event(
                db_session,
                session_id=session_id,
                user_id=user_id,
                event_type="legacy_skill_text",
                event_json={"skill_id": skill_id, "step_id": step_id, "text": normalized_text},
            )
            if post_collection:
                next_step = portrait_skill_policy_service.next_basic_info_step(current_state=state_update["current_state"])
                if next_step is None:
                    db_session.commit()
                    return self._finalize_legacy_basic_info(
                        db_session=db_session,
                        session_id=session_id,
                        user_id=user_id,
                        current_state=state_update["current_state"],
                        last_response={"input_type": "text", "state_update": state_update, "status": "basic_info_completed"},
                    )
                self._set_step(
                    db_session,
                    session_id=session_id,
                    user_id=user_id,
                    step=next_step,
                    result_preview={"portrait_state_id": portrait_state_id, "source_type": "manual", "step_id": step_id},
                )
            else:
                db_session.commit()
                return self._finalize_legacy_basic_info(
                    db_session=db_session,
                    session_id=session_id,
                    user_id=user_id,
                    current_state=state_update["current_state"],
                    last_response={"input_type": "text", "state_update": state_update, "status": "review_updated"},
                )
            row = self._get_session_row(db_session, session_id, user_id)
            return self._build_response(
                db_session=db_session,
                session_row=row,
                user_id=user_id,
                last_response={"input_type": "text", "state_update": state_update},
            )

    def _respond_confirm(self, session_id: str, user_id: int) -> dict[str, Any]:
        with get_db_session() as db_session:
            row = self._get_session_row(db_session, session_id, user_id)
            session = self._serialize_session_row(row)
            if session["status"] == "completed":
                return self._build_response(
                    db_session=db_session,
                    session_row=row,
                    user_id=user_id,
                    last_response={"input_type": "confirm", "status": "already_completed"},
                )
            ref_map = self._runtime_ref_map(portrait_session_repository.list_runtime_ref_rows(db_session, session_id))

        dialogue_ref = ref_map.get("dialogue_session")
        if dialogue_ref:
            try:
                dialogue_service.close_session(str(dialogue_ref["ref_value"]), user_id)
            except HTTPException:
                pass

        with get_db_session() as db_session:
            current_state = self._load_current_state(db_session, ref_map, user_id)
            step = portrait_orchestration_service.build_completed_step(current_state=current_state)
            now = datetime.now(timezone.utc)
            self._set_step(
                db_session,
                session_id=session_id,
                user_id=user_id,
                step=step,
                status="completed",
                result_preview=step.get("payload", {}).get("result_preview"),
                closed_at=now,
            )
            self._insert_event(
                db_session,
                session_id=session_id,
                user_id=user_id,
                event_type="session_completed",
                event_json={"confirmed": True},
            )
            row = self._get_session_row(db_session, session_id, user_id)
            return self._build_response(
                db_session=db_session,
                session_row=row,
                user_id=user_id,
                last_response={"input_type": "confirm", "status": "completed"},
            )

    def _respond_start_scale(
        self,
        session_id: str,
        scale_id: str,
        user_id: int,
        session: dict[str, Any],
        ref_map: dict[str, Any],
    ) -> dict[str, Any]:
        scale_state = scales_service.start_session(scale_id, session["actor_type"], session["actor_id"], user_id)
        scale_session_id = str(scale_state["session"]["session_id"])
        step = portrait_orchestration_service.build_scale_question_step(scale_state=scale_state)
        with get_db_session() as db_session:
            self._link_runtime_ref(
                db_session,
                session_id=session_id,
                user_id=user_id,
                ref_kind="scale_session",
                ref_value=scale_session_id,
                metadata_json={"scale_id": scale_id},
            )
            self._set_step(
                db_session,
                session_id=session_id,
                user_id=user_id,
                step=step,
                result_preview=session["result_preview_json"],
            )
            self._insert_event(
                db_session,
                session_id=session_id,
                user_id=user_id,
                event_type="respond_choice",
                event_json={"choice": f"scale:{scale_id}", "scale_session_id": scale_session_id},
            )
            row = self._get_session_row(db_session, session_id, user_id)
            return self._build_response(
                db_session=db_session,
                session_row=row,
                user_id=user_id,
                last_response={
                    "input_type": "choice",
                    "choice": f"scale:{scale_id}",
                    "scale_session": scale_state["session"],
                },
            )

    def _respond_scale_choice(self, session_id: str, choice_value: Any, user_id: int) -> dict[str, Any]:
        try:
            numeric_value = float(choice_value)
        except (TypeError, ValueError) as exc:
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "invalid_scale_choice_value",
                    "choice": choice_value,
                    "expected": "numeric",
                },
            ) from exc
        with get_db_session() as db_session:
            row = self._get_session_row(db_session, session_id, user_id)
            session = self._serialize_session_row(row)
            ref_map = self._load_runtime_refs(db_session, session_id)
            scale_ref = ref_map.get("scale_session")
            if not scale_ref:
                raise HTTPException(status_code=409, detail={"code": "missing_scale_runtime_ref", "session_id": session_id})
            scale_session_id = str(scale_ref["ref_value"])

        scale_state = scales_service.get_session_status(scale_session_id, user_id)
        next_question = scale_state.get("next_question") or {}
        question_id = next_question.get("id")
        if not question_id:
            raise HTTPException(status_code=409, detail={"code": "scale_question_not_available", "session_id": session_id})

        answered_state = scales_service.answer_question(scale_session_id, str(question_id), numeric_value, user_id)
        with get_db_session() as db_session:
            if answered_state["session"]["status"] == "ready_to_finalize":
                finalized = scales_service.finalize(scale_session_id, user_id)
                state_update = portrait_state_service.apply_update(
                    PortraitStateUpdateRequest(source_type="scale_session", source_id=scale_session_id),
                    user_id,
                )
                portrait_state_id = str(state_update["current_state"]["portrait_state_id"])
                self._link_runtime_ref(
                    db_session,
                    session_id=session_id,
                    user_id=user_id,
                    ref_kind="portrait_state",
                    ref_value=portrait_state_id,
                    metadata_json={"source": "scale_session", "source_id": scale_session_id},
                )
                step = portrait_orchestration_service.build_scale_completed_step(
                    scale_result=finalized["result"],
                    current_state=state_update["current_state"],
                )
                self._set_step(
                    db_session,
                    session_id=session_id,
                    user_id=user_id,
                    step=step,
                    result_preview={
                        "portrait_state_id": portrait_state_id,
                        "source_type": "scale_session",
                        "source_id": scale_session_id,
                    },
                )
                self._insert_event(
                    db_session,
                    session_id=session_id,
                    user_id=user_id,
                    event_type="respond_choice",
                    event_json={"choice": numeric_value, "scale_session_id": scale_session_id, "question_id": question_id},
                )
                self._insert_event(
                    db_session,
                    session_id=session_id,
                    user_id=user_id,
                    event_type="portrait_state_materialized",
                    event_json={"portrait_state_id": portrait_state_id, "source_type": "scale_session", "source_id": scale_session_id},
                )
                row = self._get_session_row(db_session, session_id, user_id)
                return self._build_response(
                    db_session=db_session,
                    session_row=row,
                    user_id=user_id,
                    last_response={
                        "input_type": "choice",
                        "choice": numeric_value,
                        "accepted_scale_answer": {"question_id": question_id, "value": numeric_value},
                        "scale_finalize": finalized,
                    },
                )

            step = portrait_orchestration_service.build_scale_question_step(scale_state=answered_state)
            self._set_step(
                db_session,
                session_id=session_id,
                user_id=user_id,
                step=step,
                result_preview=session["result_preview_json"],
            )
            self._insert_event(
                db_session,
                session_id=session_id,
                user_id=user_id,
                event_type="respond_choice",
                event_json={"choice": numeric_value, "scale_session_id": scale_session_id, "question_id": question_id},
            )
            row = self._get_session_row(db_session, session_id, user_id)
            return self._build_response(
                db_session=db_session,
                session_row=row,
                user_id=user_id,
                last_response={
                    "input_type": "choice",
                    "choice": numeric_value,
                    "accepted_scale_answer": {"question_id": question_id, "value": numeric_value},
                },
            )

    def _respond_prompt_handoff(
        self,
        session_id: str,
        user_id: int,
        session: dict[str, Any],
        ref_map: dict[str, Any],
    ) -> dict[str, Any]:
        dialogue_ref = ref_map.get("dialogue_session")
        portrait_state_ref = ref_map.get("portrait_state")
        handoff_payload = prompt_handoff_service.create_handoff(
            PromptHandoffCreateRequest(
                dialogue_session_id=str(dialogue_ref["ref_value"]) if dialogue_ref else None,
                portrait_state_id=str(portrait_state_ref["ref_value"]) if portrait_state_ref else None,
                prompt_kind="integrated_portrait",
                note_text="请基于当前画像上下文输出可回贴到 TopicLab 的综合画像候选。",
            ),
            user_id,
        )
        handoff_id = str(handoff_payload["handoff"]["handoff_id"])
        with get_db_session() as db_session:
            current_state = self._load_current_state(db_session, ref_map, user_id)
            self._link_runtime_ref(
                db_session,
                session_id=session_id,
                user_id=user_id,
                ref_kind="prompt_handoff",
                ref_value=handoff_id,
                metadata_json={"prompt_kind": handoff_payload["handoff"]["prompt_kind"]},
            )
            step = portrait_orchestration_service.build_import_request_step(
                handoff=handoff_payload["handoff"],
                artifacts=handoff_payload["artifacts"],
                current_state=current_state,
            )
            self._set_step(
                db_session,
                session_id=session_id,
                user_id=user_id,
                step=step,
                result_preview=session["result_preview_json"],
            )
            self._insert_event(
                db_session,
                session_id=session_id,
                user_id=user_id,
                event_type="respond_choice",
                event_json={"choice": "prompt_handoff", "handoff_id": handoff_id},
            )
            row = self._get_session_row(db_session, session_id, user_id)
            return self._build_response(
                db_session=db_session,
                session_row=row,
                user_id=user_id,
                last_response={
                    "input_type": "choice",
                    "choice": "prompt_handoff",
                    "handoff": handoff_payload["handoff"],
                    "artifacts": handoff_payload["artifacts"],
                },
            )

    def _respond_external_import(
        self,
        session_id: str,
        *,
        payload_text: str | None,
        payload_json: Any,
        user_id: int,
    ) -> dict[str, Any]:
        with get_db_session() as db_session:
            row = self._get_session_row(db_session, session_id, user_id)
            session = self._serialize_session_row(row)
            if session["status"] == "completed":
                raise HTTPException(
                    status_code=409,
                    detail={"code": "portrait_session_completed", "session_id": session_id},
                )
            ref_map = self._load_runtime_refs(db_session, session_id)
            handoff_ref = ref_map.get("prompt_handoff")
            policy = self._current_policy(session)
            is_legacy_ai_memory = (
                session["mode"] == "legacy_product"
                and bool(policy)
                and str(policy.get("step_id")) == "ai_memory_reply"
            )
            if ((session["current_stage"] != "import_result") and not is_legacy_ai_memory) or not handoff_ref:
                raise HTTPException(
                    status_code=409,
                    detail={"code": "portrait_session_not_waiting_for_import", "session_id": session_id},
                )

        handoff_detail = prompt_handoff_service.get_handoff(str(handoff_ref["ref_value"]), user_id)
        handoff_prompt_kind = str(handoff_detail["handoff"]["prompt_kind"])
        imported = import_result_service.create_import(
            ImportResultCreateRequest(
                handoff_id=str(handoff_ref["ref_value"]),
                source_type="external_ai_json" if payload_json is not None else "external_ai_text",
                payload_text=payload_text,
                payload_json=payload_json,
            ),
            user_id,
        )
        parsed = import_result_service.parse_import(str(imported["import_result"]["import_id"]), user_id)
        current_state = parsed["state_update"]["current_state"]
        import_id = str(parsed["import_result"]["import_id"])

        with get_db_session() as db_session:
            self._link_runtime_ref(
                db_session,
                session_id=session_id,
                user_id=user_id,
                ref_kind="import_result",
                ref_value=import_id,
                metadata_json={"handoff_id": imported["import_result"].get("handoff_id")},
            )
            self._link_runtime_ref(
                db_session,
                session_id=session_id,
                user_id=user_id,
                ref_kind="portrait_state",
                ref_value=str(current_state["portrait_state_id"]),
                metadata_json={"source": "import_result", "source_id": import_id},
            )
            if handoff_prompt_kind == "ai_memory":
                step = portrait_skill_policy_service.next_basic_info_step(current_state=current_state)
            else:
                step = portrait_orchestration_service.build_import_followup_step(
                    import_result=parsed["import_result"],
                    parse_run=parsed["parse_run"],
                    current_state=current_state,
                )
            self._insert_event(
                db_session,
                session_id=session_id,
                user_id=user_id,
                event_type="respond_external_import",
                event_json={
                    "import_id": import_id,
                    "handoff_id": imported["import_result"].get("handoff_id"),
                    "prompt_kind": handoff_prompt_kind,
                },
            )
            if handoff_prompt_kind == "ai_memory" and step is None:
                db_session.commit()
                return self._finalize_legacy_basic_info(
                    db_session=db_session,
                    session_id=session_id,
                    user_id=user_id,
                    current_state=current_state,
                    last_response={
                        "input_type": "external_json" if payload_json is not None else "external_text",
                        "import_result": parsed["import_result"],
                        "parse_run": parsed["parse_run"],
                        "state_update": parsed.get("state_update"),
                        "status": "basic_info_completed",
                    },
                )
            self._set_step(
                db_session,
                session_id=session_id,
                user_id=user_id,
                step=step,
                result_preview={
                    "portrait_state_id": current_state["portrait_state_id"],
                    "source_type": "import_result",
                    "source_id": import_id,
                },
            )
            row = self._get_session_row(db_session, session_id, user_id)
            return self._build_response(
                db_session=db_session,
                session_row=row,
                user_id=user_id,
                last_response={
                    "input_type": "external_json" if payload_json is not None else "external_text",
                    "import_result": parsed["import_result"],
                    "parse_run": parsed["parse_run"],
                    "state_update": parsed.get("state_update"),
                },
            )


portrait_session_service = PortraitSessionService()
