"""Bridge the migrated old portrait kernel into the new portrait session runtime."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any

from app.portrait.legacy_kernel import agent as legacy_agent
from app.portrait.legacy_kernel import sessions as legacy_sessions
from app.portrait.legacy_kernel.profile_parser import parse_profile
from app.portrait.runtime.block_protocol import copyable_block, text_block, text_input_block
from app.portrait.schemas.portrait_state import PortraitStateUpdateRequest
from app.portrait.services.portrait_state_service import portrait_state_service
from app.portrait.storage.legacy_kernel_session_repository import legacy_kernel_session_repository
from app.storage.database.postgres_client import get_db_session


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


def _clean_text(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if text.startswith("`") and text.endswith("`") and len(text) >= 2:
        text = text[1:-1].strip()
    if text in {"[姓名/标识]", "姓名/标识"}:
        return ""
    if text.startswith("<!--"):
        return ""
    if "|" in text and "`" in text:
        return ""
    return text


def _clean_identity_value(value: Any, *, reject_labels: tuple[str, ...] = ()) -> str:
    text = _clean_text(value)
    if not text:
        return ""
    markdown_label_match = re.match(r"^- \*\*([^*]+)\*\*[：:]\s*(.*)$", text)
    if markdown_label_match:
        current_label = markdown_label_match.group(1).strip()
        remainder = _clean_text(markdown_label_match.group(2))
        if current_label in reject_labels:
            return ""
        if not remainder:
            return ""
        text = remainder
    for label in reject_labels:
        if label in text and "**" in text:
            return ""
    return text


def _split_lines(value: Any) -> list[str]:
    text = str(value or "").strip()
    if not text:
        return []
    items: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("- "):
            line = line[2:].strip()
        items.append(line)
    return items


def _flatten_time_occupation(items: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for item in items:
        title = _clean_text(item.get("item"))
        desc = _clean_text(item.get("desc"))
        feeling = _clean_text(item.get("feeling"))
        if title and desc:
            text = f"{title}：{desc}"
        else:
            text = title or desc
        if text and feeling:
            text = f"{text}（{feeling}）"
        if text:
            parts.append(text)
    return "；".join(parts)


def _flatten_pain_points(items: list[dict[str, Any]]) -> tuple[str, str]:
    pain_parts: list[str] = []
    help_parts: list[str] = []
    for item in items:
        issue = _clean_text(item.get("issue"))
        detail = _clean_text(item.get("detail"))
        help_type = _clean_text(item.get("help_type"))
        if issue and detail:
            pain_parts.append(f"{issue}：{detail}")
        elif issue or detail:
            pain_parts.append(issue or detail)
        if help_type:
            help_parts.append(help_type)
    dedup_help = list(dict.fromkeys(help_parts))
    return "；".join(pain_parts), "；".join(dedup_help)


def _flatten_tech_stack(items: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for item in items:
        tech = _clean_text(item.get("tech"))
        level = _clean_text(item.get("level"))
        if not tech:
            continue
        parts.append(f"{tech}（{level}）" if level else tech)
    return "；".join(parts)


def _canonical_profile_from_legacy(parsed: dict[str, Any]) -> dict[str, Any]:
    identity = parsed.get("identity") or {}
    capability = parsed.get("capability") or {}
    needs = parsed.get("needs") or {}
    cognitive_style = parsed.get("cognitive_style") or {}
    motivation = parsed.get("motivation") or {}
    personality = parsed.get("personality") or {}
    interpretation = parsed.get("interpretation") or {}

    current_needs_items = needs.get("time_occupation") or []
    pain_points_items = needs.get("pain_points") or []
    pain_points_text, desired_support_text = _flatten_pain_points(pain_points_items)

    profile: dict[str, Any] = {
        "meta": {
            "display_name": _clean_text(parsed.get("name")),
            "collection_stage": _clean_text((parsed.get("meta") or {}).get("stage")),
            "data_source": _clean_text((parsed.get("meta") or {}).get("source")),
            "created_at": _clean_text((parsed.get("meta") or {}).get("created_at")),
            "updated_at": _clean_text((parsed.get("meta") or {}).get("updated_at")),
            "source_label": "legacy_kernel",
        },
        "basic_info": {
            "research_stage": _clean_identity_value(identity.get("research_stage")),
            "primary_field": _clean_identity_value(identity.get("primary_field"), reject_labels=("二级领域", "交叉方向", "方法范式", "所在机构", "学术网络")),
            "secondary_field": _clean_identity_value(identity.get("secondary_field"), reject_labels=("交叉方向", "方法范式", "所在机构", "学术网络")),
            "cross_discipline": _clean_identity_value(identity.get("cross_field"), reject_labels=("方法范式", "所在机构", "学术网络")),
            "field_statement": "；".join(
                [item for item in [
                    _clean_identity_value(identity.get("primary_field"), reject_labels=("二级领域", "交叉方向", "方法范式", "所在机构", "学术网络")),
                    _clean_identity_value(identity.get("secondary_field"), reject_labels=("交叉方向", "方法范式", "所在机构", "学术网络")),
                    _clean_identity_value(identity.get("cross_field"), reject_labels=("方法范式", "所在机构", "学术网络")),
                ] if item]
            ),
            "method_paradigm": _clean_identity_value(identity.get("method"), reject_labels=("所在机构", "学术网络")),
            "institution": _clean_identity_value(identity.get("institution"), reject_labels=("学术网络",)),
            "academic_network": _clean_identity_value(identity.get("network")),
        },
        "capability": {
            "tech_stack_text": _flatten_tech_stack(capability.get("tech_stack") or []),
            "representative_outputs": _clean_text(capability.get("outputs")),
            "process": {
                key: {
                    "score": value.get("score"),
                    "note": _clean_text(value.get("description")),
                }
                for key, value in (capability.get("process") or {}).items()
                if isinstance(value, dict)
            },
        },
        "current_needs": {
            "major_time_occupation": _flatten_time_occupation(current_needs_items),
            "time_feeling": "；".join(
                list(
                    dict.fromkeys(
                        [
                            _clean_text(item.get("feeling"))
                            for item in current_needs_items
                            if _clean_text(item.get("feeling"))
                        ]
                    )
                )
            ),
            "pain_points": pain_points_text,
            "desired_support": desired_support_text,
            "desired_change": _clean_text(needs.get("want_to_change")),
        },
    }

    inferred_dimensions: dict[str, Any] = {}
    if cognitive_style:
        inferred_dimensions["cognitive_style"] = {
            "source": _clean_text(cognitive_style.get("source")),
            "integration": cognitive_style.get("integration"),
            "depth": cognitive_style.get("depth"),
            "csi": cognitive_style.get("csi"),
            "type": _clean_text(cognitive_style.get("type")),
        }
    if motivation:
        dims = motivation.get("dimensions") or {}
        inferred_dimensions["motivation"] = {
            "source": _clean_text(motivation.get("source")),
            "to_know": dims.get("know"),
            "toward_accomplishment": dims.get("accomplishment"),
            "to_experience_stimulation": dims.get("stimulation"),
            "identified": dims.get("identified"),
            "introjected": dims.get("introjected"),
            "external": dims.get("external"),
            "amotivation": dims.get("amotivation"),
            "rai": motivation.get("rai"),
        }
    if personality:
        levels: dict[str, Any] = {}
        personality_payload: dict[str, Any] = {"source": _clean_text(personality.get("source"))}
        for key in ("extraversion", "agreeableness", "conscientiousness", "neuroticism", "openness"):
            value = personality.get(key)
            if isinstance(value, dict):
                personality_payload[key] = value.get("score")
                if value.get("level"):
                    levels[key] = value.get("level")
        if levels:
            personality_payload["levels"] = levels
        if len(personality_payload) > 1:
            inferred_dimensions["personality"] = personality_payload
    interpretation_payload = {
        "core_driver": _clean_text(interpretation.get("core_driver")),
        "risks": _split_lines(interpretation.get("risks")),
        "paths": _split_lines(interpretation.get("path")),
    }
    if any(interpretation_payload.values()):
        inferred_dimensions["interpretation"] = interpretation_payload
    if inferred_dimensions:
        profile["inferred_dimensions"] = inferred_dimensions
    return profile


def _extract_copyables(assistant_content: str, session_snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    for match in re.finditer(r"```(?:[a-zA-Z0-9_-]+)?\n(.*?)```", assistant_content, flags=re.DOTALL):
        content = match.group(1).strip()
        if not content:
            continue
        title = "可复制内容"
        if "科研数字分身信息提取请求" in content:
            title = "AI 记忆提取提示词"
        blocks.append(copyable_block(title=title, content=content))
    forum_profile = str(session_snapshot.get("forum_profile") or "").strip()
    if forum_profile:
        blocks.append(copyable_block(title="当前论坛画像 Markdown", content=forum_profile))
    return blocks


class _LegacyKernelSessionAdapter:
    def __init__(self, portrait_session_id: str, user_id: int) -> None:
        self._portrait_session_id = portrait_session_id
        self._user_id = user_id

    def load_session(self, session_id: str | None, user_id: int | str | None) -> dict[str, Any] | None:
        _ = session_id, user_id
        with get_db_session() as db_session:
            row = legacy_kernel_session_repository.get_session_row(
                db_session,
                self._portrait_session_id,
                self._user_id,
            )
            if not row:
                return None
            snapshot = _json_db_load(row[3]) or {}
            return snapshot if isinstance(snapshot, dict) else None

    def save_session(self, session: dict[str, Any]) -> None:
        with get_db_session() as db_session:
            legacy_kernel_session_repository.upsert_session(
                db_session,
                portrait_session_id=self._portrait_session_id,
                legacy_session_id=str(session.get("session_id") or ""),
                user_id=self._user_id,
                snapshot_json=_json_db_value(session),
                updated_at=datetime.now(timezone.utc),
            )


class LegacyKernelBridge:
    """Execute the migrated old portrait kernel behind the unified session API."""

    def _sync_snapshot_to_state(
        self,
        *,
        portrait_session_id: str,
        legacy_session_id: str,
        user_id: int,
        session_snapshot: dict[str, Any],
    ) -> dict[str, Any]:
        profile_markdown = str(session_snapshot.get("profile") or "")
        forum_profile = str(session_snapshot.get("forum_profile") or "")
        parsed_profile = parse_profile(profile_markdown) if profile_markdown.strip() else {}
        profile_payload = _canonical_profile_from_legacy(parsed_profile) if parsed_profile else {}

        state_patch: dict[str, Any] = {
            "legacy_kernel": {
                "portrait_session_id": portrait_session_id,
                "legacy_session_id": legacy_session_id,
                "profile_markdown": profile_markdown,
                "forum_profile_markdown": forum_profile,
                "scales": session_snapshot.get("scales") or {},
                "message_count": len(session_snapshot.get("messages") or []),
                "profile_path": session_snapshot.get("profile_path"),
                "forum_profile_path": session_snapshot.get("forum_profile_path"),
            }
        }
        if profile_payload:
            state_patch["profile"] = profile_payload

        state_update = portrait_state_service.apply_update(
            PortraitStateUpdateRequest(
                source_type="manual",
                state_patch_json=state_patch,
                change_summary_json={
                    "source_type": "manual",
                    "source_id": legacy_session_id,
                    "source_label": "legacy_kernel",
                    "portrait_session_id": portrait_session_id,
                },
                observation_json={
                    "kind": "legacy_kernel_sync",
                    "legacy_session_id": legacy_session_id,
                    "collection_stage": ((parsed_profile.get("meta") or {}).get("stage") if parsed_profile else None),
                    "display_name": (parsed_profile.get("name") if parsed_profile else None),
                },
            ),
            user_id,
        )
        return {
            "state_update": state_update,
            "parsed_profile": parsed_profile,
        }

    def _build_step(
        self,
        *,
        assistant_content: str,
        session_snapshot: dict[str, Any],
        parsed_profile: dict[str, Any],
    ) -> dict[str, Any]:
        blocks = [text_block(assistant_content)]
        blocks.extend(_extract_copyables(assistant_content, session_snapshot))
        blocks.append(
            text_input_block(
                block_id="legacy_kernel_reply",
                question="请继续回答上面的问题，或直接说明你接下来想做什么。",
                placeholder="例如：A / B / 博士后 / 查看画像 / 生成论坛画像 / 我想填量表",
                multiline=True,
            )
        )
        meta = parsed_profile.get("meta") or {}
        completion = parsed_profile.get("completion") or {}
        return {
            "stage": _clean_text(meta.get("stage")) or "legacy_kernel",
            "input_kind": "text",
            "message": assistant_content,
            "payload": {
                "blocks": blocks,
                "legacy_kernel": {
                    "completion": completion,
                    "display_name": parsed_profile.get("name"),
                    "has_forum_profile": bool(str(session_snapshot.get("forum_profile") or "").strip()),
                },
            },
            "next_hint": "直接用自然语言继续回答即可；旧画像内核会自行决定下一步 skill。",
        }

    def run_turn(
        self,
        *,
        portrait_session_id: str,
        user_id: int,
        user_message: str,
        actor_type: str | None = None,
        actor_id: str | None = None,
        model: str | None = None,
    ) -> dict[str, Any]:
        adapter = _LegacyKernelSessionAdapter(portrait_session_id, user_id)
        with legacy_sessions.use_runtime_adapter(adapter):
            legacy_session_id, legacy_session = legacy_sessions.get_or_create(user_id=user_id)
            if actor_type:
                legacy_session["actor_type"] = actor_type
            if actor_id:
                legacy_session["actor_id"] = actor_id
            chunks = list(legacy_agent.run_agent(user_message, legacy_session, stream=False, model=model))
            assistant_content = "".join(chunks).strip()
            adapter.save_session(legacy_session)

        sync_payload = self._sync_snapshot_to_state(
            portrait_session_id=portrait_session_id,
            legacy_session_id=legacy_session_id,
            user_id=user_id,
            session_snapshot=legacy_session,
        )
        parsed_profile = sync_payload["parsed_profile"]
        step = self._build_step(
            assistant_content=assistant_content or "旧画像内核本轮未返回正文，请继续描述你当前的情况。",
            session_snapshot=legacy_session,
            parsed_profile=parsed_profile,
        )
        collection_stage = _clean_text((parsed_profile.get("meta") or {}).get("stage")) if parsed_profile else ""
        return {
            "legacy_session_id": legacy_session_id,
            "assistant_content": assistant_content,
            "session_snapshot": legacy_session,
            "state_update": sync_payload["state_update"],
            "parsed_profile": parsed_profile,
            "step": step,
            "status": "completed" if collection_stage == "review_done" else "active",
            "result_preview": {
                "portrait_state_id": sync_payload["state_update"]["current_state"]["portrait_state_id"],
                "source_type": "legacy_kernel",
                "source_id": legacy_session_id,
            },
        }

    def bootstrap(
        self,
        *,
        portrait_session_id: str,
        user_id: int,
        actor_type: str | None = None,
        actor_id: str | None = None,
        model: str | None = None,
    ) -> dict[str, Any]:
        return self.run_turn(
            portrait_session_id=portrait_session_id,
            user_id=user_id,
            user_message="帮我开始建立科研数字分身。",
            actor_type=actor_type,
            actor_id=actor_id,
            model=model,
        )


legacy_kernel_bridge = LegacyKernelBridge()
