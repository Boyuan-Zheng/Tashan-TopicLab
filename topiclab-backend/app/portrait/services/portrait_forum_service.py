"""Generate public-facing forum profile projections from canonical portrait state."""

from __future__ import annotations

from typing import Any

from app.portrait.services.portrait_artifact_service import portrait_artifact_service
from app.portrait.services.portrait_projection_service import portrait_projection_service


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _tool_categories(text_value: str) -> list[str]:
    normalized = _clean_text(text_value)
    if not normalized:
        return []
    categories: list[str] = []
    mapping = {
        "Python": "编程与数据分析",
        "PyTorch": "机器学习框架",
        "JAX": "机器学习框架",
        "MATLAB": "科学计算工具",
        "R": "统计分析工具",
        "MNE": "神经数据分析工具",
        "SPM": "神经影像分析工具",
    }
    for key, category in mapping.items():
        if key.lower() in normalized.lower() and category not in categories:
            categories.append(category)
    return categories


class PortraitForumService:
    """Build the forum-twin projection with privacy gating."""

    def _build_identity_paragraph(self, structured_profile: dict[str, Any], *, institution_mode: str) -> str:
        basic_info = structured_profile.get("basic_info") or {}
        stage = _clean_text(basic_info.get("research_stage")) or "研究者"
        fields = " / ".join(
            item
            for item in [
                _clean_text(basic_info.get("primary_field")),
                _clean_text(basic_info.get("secondary_field")),
            ]
            if item
        )
        cross = _clean_text(basic_info.get("cross_discipline"))
        method = _clean_text(basic_info.get("method_paradigm") or basic_info.get("method_statement"))
        institution = _clean_text(basic_info.get("institution"))
        if institution_mode == "category" and institution:
            institution = "研究机构"
        if institution_mode == "omit":
            institution = ""

        parts = [f"这位智能体当前以 {stage} 身份开展工作。"]
        if fields:
            parts.append(f"主要聚焦于 {fields}。")
        if cross:
            parts.append(f"同时保有 {cross} 的交叉视角。")
        if method:
            parts.append(f"其常用的方法范式是 {method}。")
        if institution:
            parts.append(f"当前工作背景可概括为 {institution}。")
        return " ".join(parts)

    def _build_expertise(self, structured_profile: dict[str, Any], *, tool_detail_mode: str) -> list[str]:
        basic_info = structured_profile.get("basic_info") or {}
        capability = structured_profile.get("capability") or {}
        process = capability.get("process") or {}
        items: list[str] = []

        for value in [
            _clean_text(basic_info.get("primary_field")),
            _clean_text(basic_info.get("secondary_field")),
            _clean_text(basic_info.get("cross_discipline")),
        ]:
            if value and value not in items:
                items.append(value)

        tech_stack_text = _clean_text(capability.get("tech_stack_text"))
        if tech_stack_text:
            if tool_detail_mode == "category":
                items.extend(category for category in _tool_categories(tech_stack_text) if category not in items)
            else:
                items.append(f"工具栈：{tech_stack_text}")

        for key, label in [
            ("problem_definition", "问题定义"),
            ("literature", "文献整合"),
            ("design", "方案设计"),
            ("execution", "实验执行"),
            ("writing", "论文写作"),
            ("management", "项目管理"),
        ]:
            score = float((process.get(key) or {}).get("score") or 0)
            if score >= 4:
                items.append(f"{label}能力较强")

        outputs = _clean_text(capability.get("representative_outputs"))
        if outputs:
            items.append(f"代表性产出：{outputs}")

        unique_items: list[str] = []
        for item in items:
            normalized = item.strip()
            if normalized and normalized not in unique_items:
                unique_items.append(normalized)
        return unique_items[:10]

    def _build_thinking_style(
        self,
        structured_profile: dict[str, Any],
        *,
        include_cognitive_style: bool,
        include_motivation: bool,
        include_personality: bool,
    ) -> list[str]:
        cognitive_style = structured_profile.get("cognitive_style") or {}
        motivation = structured_profile.get("motivation") or {}
        personality = structured_profile.get("personality") or {}
        interpretation = structured_profile.get("interpretation") or {}

        items: list[str] = []
        if include_cognitive_style and _clean_text(cognitive_style.get("type")):
            items.append(f"认知风格更接近{_clean_text(cognitive_style.get('type'))}")
        if include_cognitive_style and cognitive_style.get("csi") is not None:
            items.append(f"在整合与深挖之间的取向指数约为 {cognitive_style.get('csi')}")
        if include_motivation and motivation.get("rai") is not None:
            items.append(f"整体自主驱动程度较高（RAI 约 {motivation.get('rai')}）")
        if include_personality and personality.get("openness") is not None:
            items.append(f"对新方法与新议题保持较高开放性（约 {personality.get('openness')} / 5）")
        core_driver = _clean_text(interpretation.get("core_driver"))
        if core_driver:
            items.append(core_driver)
        risks = interpretation.get("risks") or []
        if risks:
            items.append(f"需要注意的潜在风险包括：{risks[0]}")
        return items[:7]

    def _build_discussion_style(
        self,
        structured_profile: dict[str, Any],
        *,
        include_personality: bool,
        include_current_needs: bool,
    ) -> list[str]:
        cognitive_style = structured_profile.get("cognitive_style") or {}
        personality = structured_profile.get("personality") or {}
        current_needs = structured_profile.get("current_needs") or {}
        interpretation = structured_profile.get("interpretation") or {}

        items: list[str] = []
        if _clean_text(cognitive_style.get("type")):
            items.append(f"讨论时常从{_clean_text(cognitive_style.get('type'))}的角度组织问题")
        if include_personality and personality.get("conscientiousness") is not None:
            items.append(f"在结构化表达与执行推进上较为重视秩序（尽责性约 {personality.get('conscientiousness')} / 5）")
        if include_personality and personality.get("agreeableness") is not None:
            items.append(f"合作语境下的配合度约为 {personality.get('agreeableness')} / 5")
        if include_current_needs and _clean_text(current_needs.get("pain_points")):
            items.append(f"当前讨论中可能会更多围绕“{_clean_text(current_needs.get('pain_points'))}”寻求支持")
        paths = interpretation.get("paths") or []
        if paths:
            items.append(f"更适合围绕下一步路径而不是抽象评价来展开交流：{paths[0]}")
        return items[:7]

    def generate_forum_profile(
        self,
        *,
        user_id: int,
        display_name: str | None = None,
        institution_mode: str = "category",
        tool_detail_mode: str = "category",
        include_cognitive_style: bool = True,
        include_motivation: bool = True,
        include_personality: bool = True,
        include_current_needs: bool = False,
        source_session_id: str | None = None,
    ) -> dict[str, Any]:
        projection = portrait_projection_service.build_projection(user_id, display_name=display_name)
        structured_profile = projection["structured_profile"]
        effective_name = structured_profile["display_name"]
        identity = self._build_identity_paragraph(structured_profile, institution_mode=institution_mode)
        expertise = self._build_expertise(structured_profile, tool_detail_mode=tool_detail_mode)
        thinking_style = self._build_thinking_style(
            structured_profile,
            include_cognitive_style=include_cognitive_style,
            include_motivation=include_motivation,
            include_personality=include_personality,
        )
        discussion_style = self._build_discussion_style(
            structured_profile,
            include_personality=include_personality,
            include_current_needs=include_current_needs,
        )

        markdown_lines = [
            f"# {effective_name}",
            "",
            "## Identity",
            "",
            identity,
            "",
            "## Expertise",
            "",
        ]
        markdown_lines.extend([f"- {item}" for item in expertise] if expertise else ["- 暂无足够数据"])
        markdown_lines.extend(
            [
                "",
                "## Thinking Style",
                "",
            ]
        )
        markdown_lines.extend([f"- {item}" for item in thinking_style] if thinking_style else ["- 暂无足够数据"])
        markdown_lines.extend(
            [
                "",
                "## Discussion Style",
                "",
            ]
        )
        markdown_lines.extend([f"- {item}" for item in discussion_style] if discussion_style else ["- 暂无足够数据"])
        markdown_lines.append("")
        forum_markdown = "\n".join(markdown_lines).strip() + "\n"
        artifact = portrait_artifact_service.record_artifact(
            user_id=user_id,
            portrait_state_id=projection["portrait_state_id"],
            source_session_id=source_session_id,
            artifact_kind="forum_profile_markdown",
            format="markdown",
            title=f"{effective_name} forum profile",
            content_text=forum_markdown,
            metadata_json={
                "institution_mode": institution_mode,
                "tool_detail_mode": tool_detail_mode,
                "include_cognitive_style": include_cognitive_style,
                "include_motivation": include_motivation,
                "include_personality": include_personality,
                "include_current_needs": include_current_needs,
            },
        )
        return {
            "projection": projection,
            "forum_profile_markdown": forum_markdown,
            "artifact": artifact,
        }


portrait_forum_service = PortraitForumService()
