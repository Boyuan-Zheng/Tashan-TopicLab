"""Projection helpers that normalize canonical portrait state into product-facing views."""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException

from app.portrait.services.portrait_state_service import portrait_state_service


PROCESS_DIMENSIONS = [
    ("problem_definition", "问题定义"),
    ("literature", "文献整合"),
    ("design", "方案设计"),
    ("execution", "实验执行"),
    ("writing", "论文写作"),
    ("management", "项目管理"),
]


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _bullet_lines(items: list[str]) -> list[str]:
    return [f"- {item}" for item in items if item]


class PortraitProjectionService:
    """Build normalized product projections from canonical portrait state."""

    def _ensure_current_state(self, user_id: int) -> dict[str, Any]:
        payload = portrait_state_service.get_current_state(user_id)
        current_state = payload.get("current_state") or {}
        if not current_state.get("portrait_state_id"):
            raise HTTPException(status_code=404, detail={"code": "portrait_state_not_found"})
        return current_state

    def _effective_cognitive_style(self, state_json: dict[str, Any], profile: dict[str, Any]) -> dict[str, Any]:
        scale_result = (((state_json.get("scales") or {}).get("results") or {}).get("rcss") or {})
        if scale_result:
            dimension_scores = scale_result.get("dimension_scores") or {}
            derived_scores = scale_result.get("derived_scores") or {}
            return {
                "source": "scale:rcss",
                "integration": dimension_scores.get("integration"),
                "depth": dimension_scores.get("depth"),
                "csi": derived_scores.get("CSI"),
                "type": derived_scores.get("type"),
                "completed_at": scale_result.get("completed_at"),
            }
        inferred = ((profile.get("inferred_dimensions") or {}).get("cognitive_style") or {})
        return {"source": "inferred", **inferred}

    def _effective_motivation(self, state_json: dict[str, Any], profile: dict[str, Any]) -> dict[str, Any]:
        scale_result = (((state_json.get("scales") or {}).get("results") or {}).get("ams") or {})
        if scale_result:
            dimension_scores = scale_result.get("dimension_scores") or {}
            derived_scores = scale_result.get("derived_scores") or {}
            return {
                "source": "scale:ams",
                "to_know": dimension_scores.get("know"),
                "toward_accomplishment": dimension_scores.get("accomplishment"),
                "to_experience_stimulation": dimension_scores.get("stimulation"),
                "identified": dimension_scores.get("identified"),
                "introjected": dimension_scores.get("introjected"),
                "external": dimension_scores.get("external"),
                "amotivation": dimension_scores.get("amotivation"),
                "rai": derived_scores.get("RAI"),
                "intrinsic_total": derived_scores.get("intrinsicTotal"),
                "extrinsic_total": derived_scores.get("extrinsicTotal"),
                "completed_at": scale_result.get("completed_at"),
            }
        inferred = ((profile.get("inferred_dimensions") or {}).get("motivation") or {})
        return {"source": "inferred", **inferred}

    def _effective_personality(self, state_json: dict[str, Any], profile: dict[str, Any]) -> dict[str, Any]:
        scale_result = (((state_json.get("scales") or {}).get("results") or {}).get("mini-ipip") or {})
        if scale_result:
            dimension_scores = scale_result.get("dimension_scores") or {}
            return {
                "source": "scale:mini-ipip",
                "extraversion": dimension_scores.get("extraversion"),
                "agreeableness": dimension_scores.get("agreeableness"),
                "conscientiousness": dimension_scores.get("conscientiousness"),
                "neuroticism": dimension_scores.get("neuroticism"),
                "openness": dimension_scores.get("openness"),
                "completed_at": scale_result.get("completed_at"),
            }
        inferred = ((profile.get("inferred_dimensions") or {}).get("personality") or {})
        return {"source": "inferred", **inferred}

    def _dialogue_snapshot(self, state_json: dict[str, Any]) -> dict[str, Any]:
        latest_dialogue = (((state_json.get("dialogue") or {}).get("latest_session")) or {})
        derived_state = latest_dialogue.get("derived_state") or {}
        summary = derived_state.get("summary") or {}
        return {
            "session_id": latest_dialogue.get("session_id"),
            "status": latest_dialogue.get("status"),
            "actor_type": latest_dialogue.get("actor_type"),
            "actor_id": latest_dialogue.get("actor_id"),
            "message_count": derived_state.get("message_count"),
            "summary": summary,
        }

    def _render_profile_markdown(self, *, display_name: str, structured_profile: dict[str, Any]) -> str:
        basic_info = structured_profile.get("basic_info") or {}
        capability = structured_profile.get("capability") or {}
        current_needs = structured_profile.get("current_needs") or {}
        cognitive_style = structured_profile.get("cognitive_style") or {}
        motivation = structured_profile.get("motivation") or {}
        personality = structured_profile.get("personality") or {}
        interpretation = structured_profile.get("interpretation") or {}
        dialogue = structured_profile.get("dialogue") or {}

        lines = [f"# {display_name}", ""]

        identity_items = [
            f"研究阶段：{_clean_text(basic_info.get('research_stage')) or '未填写'}",
            f"一级领域：{_clean_text(basic_info.get('primary_field')) or '未填写'}",
            f"二级领域：{_clean_text(basic_info.get('secondary_field')) or '未填写'}",
            f"交叉方向：{_clean_text(basic_info.get('cross_discipline')) or '未填写'}",
            f"方法范式：{_clean_text(basic_info.get('method_paradigm') or basic_info.get('method_statement')) or '未填写'}",
            f"所在机构：{_clean_text(basic_info.get('institution')) or '未填写'}",
            f"导师/团队：{_clean_text(basic_info.get('advisor_team')) or '未填写'}",
            f"合作网络：{_clean_text(basic_info.get('academic_network')) or '未填写'}",
        ]
        lines += ["## Identity", "", *identity_items, ""]

        capability_lines = []
        if _clean_text(capability.get("tech_stack_text")):
            capability_lines.append(f"- 技术栈：{_clean_text(capability.get('tech_stack_text'))}")
        if _clean_text(capability.get("representative_outputs")):
            capability_lines.append(f"- 代表性产出：{_clean_text(capability.get('representative_outputs'))}")
        process = capability.get("process") or {}
        for key, label in PROCESS_DIMENSIONS:
            score = (process.get(key) or {}).get("score")
            description = _clean_text((process.get(key) or {}).get("description"))
            if score is None and not description:
                continue
            capability_lines.append(f"- {label}：{score if score is not None else '未评估'}；{description or '无补充说明'}")
        lines += ["## Capability", "", *(capability_lines or ["- 暂无能力数据"]), ""]

        current_needs_lines = [
            f"- 主要时间占用：{_clean_text(current_needs.get('major_time_occupation')) or '未填写'}",
            f"- 核心卡点：{_clean_text(current_needs.get('pain_points')) or '未填写'}",
            f"- 最想改变：{_clean_text(current_needs.get('desired_change')) or '未填写'}",
        ]
        lines += ["## Current Needs", "", *current_needs_lines, ""]

        cognitive_lines = [
            f"- 来源：{_clean_text(cognitive_style.get('source')) or 'unknown'}",
            f"- Integration：{cognitive_style.get('integration')}",
            f"- Depth：{cognitive_style.get('depth')}",
            f"- CSI：{cognitive_style.get('csi')}",
            f"- 类型：{_clean_text(cognitive_style.get('type')) or '未生成'}",
        ]
        lines += ["## Cognitive Style", "", *cognitive_lines, ""]

        motivation_lines = [
            f"- 来源：{_clean_text(motivation.get('source')) or 'unknown'}",
            f"- 求知：{motivation.get('to_know')}",
            f"- 成就：{motivation.get('toward_accomplishment')}",
            f"- 刺激：{motivation.get('to_experience_stimulation')}",
            f"- 认同：{motivation.get('identified')}",
            f"- 内摄：{motivation.get('introjected')}",
            f"- 外部：{motivation.get('external')}",
            f"- 无动机：{motivation.get('amotivation')}",
            f"- RAI：{motivation.get('rai')}",
        ]
        lines += ["## Motivation", "", *motivation_lines, ""]

        personality_lines = [
            f"- 来源：{_clean_text(personality.get('source')) or 'unknown'}",
            f"- 开放性：{personality.get('openness')}",
            f"- 尽责性：{personality.get('conscientiousness')}",
            f"- 外向性：{personality.get('extraversion')}",
            f"- 宜人性：{personality.get('agreeableness')}",
            f"- 神经质：{personality.get('neuroticism')}",
        ]
        lines += ["## Personality", "", *personality_lines, ""]

        interpretation_lines = [
            f"- 核心驱动：{_clean_text(interpretation.get('core_driver')) or '未生成'}",
            *[f"- 风险：{item}" for item in interpretation.get("risks") or []],
            *[f"- 路径：{item}" for item in interpretation.get("paths") or []],
        ]
        lines += ["## Interpretation", "", *(interpretation_lines or ["- 暂无综合解读"]), ""]

        dialogue_summary = dialogue.get("summary") or {}
        dialogue_lines = [
            f"- 最近对话 session：{_clean_text(dialogue.get('session_id')) or '无'}",
            f"- 消息数：{dialogue.get('message_count')}",
            f"- 摘要：{_clean_text(dialogue_summary.get('summary_text')) or _clean_text(dialogue_summary.get('self_summary')) or '无'}",
        ]
        lines += ["## Dialogue Snapshot", "", *dialogue_lines, ""]
        return "\n".join(lines).strip() + "\n"

    def build_projection(self, user_id: int, *, display_name: str | None = None) -> dict[str, Any]:
        current_state = self._ensure_current_state(user_id)
        state_json = current_state.get("state_json") or {}
        profile = state_json.get("profile") or {}
        basic_info = profile.get("basic_info") or {}
        capability = profile.get("capability") or {}
        current_needs = profile.get("current_needs") or {}
        interpretation = ((profile.get("inferred_dimensions") or {}).get("interpretation") or {})

        effective_name = _clean_text(display_name) or _clean_text(basic_info.get("display_name")) or "科研数字分身"
        structured_profile = {
            "display_name": effective_name,
            "basic_info": basic_info,
            "capability": capability,
            "current_needs": current_needs,
            "cognitive_style": self._effective_cognitive_style(state_json, profile),
            "motivation": self._effective_motivation(state_json, profile),
            "personality": self._effective_personality(state_json, profile),
            "interpretation": interpretation,
            "dialogue": self._dialogue_snapshot(state_json),
            "source_summary": current_state.get("source_summary_json") or {},
        }
        profile_markdown = self._render_profile_markdown(display_name=effective_name, structured_profile=structured_profile)
        return {
            "current_state": current_state,
            "portrait_state_id": current_state.get("portrait_state_id"),
            "structured_profile": structured_profile,
            "profile_markdown": profile_markdown,
        }


portrait_projection_service = PortraitProjectionService()
