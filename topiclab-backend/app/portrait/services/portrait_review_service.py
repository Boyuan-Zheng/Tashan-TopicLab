"""Build legacy-product-compatible review/update/history steps."""

from __future__ import annotations

from typing import Any

from app.portrait.runtime.block_protocol import actions_block, chart_block, choice_block, text_block, text_input_block


PROCESS_DIMENSIONS = [
    ("problem_definition", "问题定义"),
    ("literature", "文献整合"),
    ("design", "方案设计"),
    ("execution", "实验执行"),
    ("writing", "论文写作"),
    ("management", "项目管理"),
]


def _state_json(current_state: dict[str, Any] | None) -> dict[str, Any]:
    if not current_state:
        return {}
    return current_state.get("state_json") or {}


def _profile(current_state: dict[str, Any] | None) -> dict[str, Any]:
    return _state_json(current_state).get("profile") or {}


class PortraitReviewService:
    """Render old review/update/history product steps."""

    def _wrap_step(
        self,
        *,
        step_id: str,
        message: str,
        blocks: list[dict[str, Any]],
        input_kind: str,
        next_hint: str,
        policy_state: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return {
            "stage": "skill_policy",
            "input_kind": input_kind,
            "message": message,
            "payload": {
                "policy": {
                    "mode": "legacy_product",
                    "skill_id": "review-profile",
                    "step_id": step_id,
                    "policy_state": policy_state or {},
                },
                "blocks": blocks,
            },
            "next_hint": next_hint,
        }

    def build_review_step(self, *, current_state: dict[str, Any] | None) -> dict[str, Any]:
        return self.build_review_step_with_prelude(current_state=current_state, prepend_blocks=None)

    def build_review_step_with_prelude(
        self,
        *,
        current_state: dict[str, Any] | None,
        prepend_blocks: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        profile = _profile(current_state)
        basic = profile.get("basic_info") or {}
        capability = profile.get("capability") or {}
        needs = profile.get("current_needs") or {}
        inferred = profile.get("inferred_dimensions") or {}
        cognitive_style = inferred.get("cognitive_style") or {}
        motivation = inferred.get("motivation") or {}
        personality = inferred.get("personality") or {}
        interpretation = inferred.get("interpretation") or {}
        process = capability.get("process") or {}

        blocks: list[dict[str, Any]] = [
            *(prepend_blocks or []),
            text_block(
                "\n".join(
                    [
                        "以下是当前科研数字分身的审核视图。",
                        f"- 研究阶段：{basic.get('research_stage') or '未填写'}",
                        f"- 主要领域：{basic.get('primary_field') or '未填写'}",
                        f"- 方法范式：{basic.get('method_paradigm') or '未填写'}",
                        f"- 所在机构：{basic.get('institution') or '未填写'}",
                    ]
                )
            )
        ]

        process_values = [float((process.get(key) or {}).get("score") or 0) for key, _label in PROCESS_DIMENSIONS]
        if any(process_values):
            blocks.append(
                chart_block(
                    chart_type="radar",
                    title="科研流程能力（文字雷达）",
                    dimensions=[label for _key, label in PROCESS_DIMENSIONS],
                    values=process_values,
                    max_value=5,
                )
            )

        blocks.append(
            text_block(
                "\n".join(
                    [
                        "当前需求摘要：",
                        f"- 主要时间占用：{needs.get('major_time_occupation') or '未填写'}",
                        f"- 核心难点：{needs.get('pain_points') or '未填写'}",
                        f"- 最想改变：{needs.get('desired_change') or '未填写'}",
                    ]
                )
            )
        )

        if cognitive_style:
            blocks.append(
                text_block(
                    f"认知风格：CSI={cognitive_style.get('csi')}，类型={cognitive_style.get('type')}。"
                    f" {'（AI推断）' if inferred.get('source') == 'AI推断' else ''}"
                )
            )
        if motivation:
            blocks.append(
                chart_block(
                    chart_type="bar",
                    title="学术动机结构",
                    dimensions=["求知", "成就", "刺激", "认同", "内摄", "外部", "无动机"],
                    values=[
                        float(motivation.get("to_know") or 0),
                        float(motivation.get("toward_accomplishment") or 0),
                        float(motivation.get("to_experience_stimulation") or 0),
                        float(motivation.get("identified") or 0),
                        float(motivation.get("introjected") or 0),
                        float(motivation.get("external") or 0),
                        float(motivation.get("amotivation") or 0),
                    ],
                    max_value=7,
                )
            )
        if personality:
            blocks.append(
                chart_block(
                    chart_type="bar",
                    title="人格特征估计",
                    dimensions=["外向性", "宜人性", "尽责性", "神经质", "开放性"],
                    values=[
                        float(personality.get("extraversion") or 0),
                        float(personality.get("agreeableness") or 0),
                        float(personality.get("conscientiousness") or 0),
                        float(personality.get("neuroticism") or 0),
                        float(personality.get("openness") or 0),
                    ],
                    max_value=5,
                )
            )
        if interpretation:
            blocks.append(
                text_block(
                    "\n".join(
                        [
                            f"核心驱动：{interpretation.get('core_driver') or '未生成'}",
                            "潜在风险：",
                            *[f"- {item}" for item in interpretation.get("risks") or []],
                            "发展路径：",
                            *[f"- {item}" for item in interpretation.get("paths") or []],
                        ]
                    )
                )
            )

        options = [
            {"id": "confirm_review", "label": "确认画像", "description": "将当前画像标记为已审核。"},
            {"id": "update_basic_identity", "label": "修改基础身份", "description": "修改研究阶段、领域、机构等信息。"},
            {"id": "update_tech_capability", "label": "修改技术能力", "description": "修改技术栈或代表性产出。"},
            {"id": "update_process_ability", "label": "修改科研流程能力", "description": "修改 6 个流程能力评分。"},
            {"id": "update_current_needs", "label": "修改当前需求", "description": "修改时间占用、卡点和最想改变的事。"},
            {"id": "history", "label": "查看历史", "description": "查看会话、版本和事件历史。"},
            {"id": "scale:rcss", "label": "重新做 RCSS", "description": "用实测量表校准认知风格。"},
            {"id": "scale:ams", "label": "重新做 AMS", "description": "用实测量表校准学术动机。"},
            {"id": "scale:mini-ipip", "label": "重新做 Mini-IPIP", "description": "用实测量表校准人格特征。"},
            {"id": "prompt_handoff", "label": "生成外部提示词", "description": "交给外部 AI 继续补充画像。"},
            {"id": "forum:generate", "label": "生成论坛画像", "description": "生成一份论坛展示版公开画像草稿。"},
            {"id": "scientist:famous", "label": "匹配著名科学家", "description": "查看与你画像最接近的著名科学家。"},
            {"id": "scientist:field", "label": "推荐领域科学家", "description": "根据当前方向推荐值得关注的科学家。"},
            {"id": "export:structured", "label": "导出结构化画像", "description": "导出当前画像的 JSON 结构化版本。"},
            {"id": "export:profile_markdown", "label": "导出完整 Markdown", "description": "导出完整画像 markdown。"},
            {"id": "export:forum_markdown", "label": "导出论坛 Markdown", "description": "导出论坛展示版 markdown。"},
            {"id": "publish:brief", "label": "发布 brief twin", "description": "将当前画像以 brief 口径发布为 twin。"},
            {"id": "publish:full", "label": "发布 full twin", "description": "将当前画像以 full 口径发布为 twin。"},
            {"id": "reset_now", "label": "重置本次创建过程", "description": "结束并重置当前画像会话。"},
        ]
        blocks.append(
            actions_block(
                message="你可以确认当前画像，也可以继续修改、查看历史或重做某个量表。",
                buttons=[
                    {"id": "confirm_review", "label": "确认画像", "style": "primary"},
                    {"id": "update_basic_identity", "label": "修改画像", "style": "secondary"},
                    {"id": "history", "label": "查看历史", "style": "secondary"},
                ],
            )
        )
        blocks.append(choice_block(block_id="review_actions", question="你希望下一步做什么？", options=options))
        return self._wrap_step(
            step_id="review_summary",
            message="画像已生成，请审核当前内容。",
            blocks=blocks,
            input_kind="choice",
            next_hint="可确认、修改、查看历史，或重新进行某个量表。",
        )

    def build_history_step(self, *, history_payload: dict[str, Any]) -> dict[str, Any]:
        session = history_payload.get("session") or {}
        runtime_refs = history_payload.get("runtime_refs") or {}
        events = history_payload.get("events") or []
        versions = history_payload.get("versions") or []
        observations = history_payload.get("observations") or []
        blocks = [
            text_block(
                "\n".join(
                    [
                        f"会话历史：{session.get('session_id')}",
                        f"- 当前状态：{session.get('status')}",
                        f"- 当前阶段：{session.get('current_stage')}",
                        f"- runtime refs：{', '.join(sorted(runtime_refs.keys())) or '无'}",
                        f"- 事件数：{len(events)}",
                        f"- 版本数：{len(versions)}",
                        f"- observations：{len(observations)}",
                    ]
                )
            ),
            text_block(
                "最近事件：\n"
                + "\n".join(
                    [
                        f"- {item.get('event_type')} @ {item.get('created_at')}"
                        for item in events[:8]
                    ]
                )
            ),
            actions_block(
                message="历史查看完成后，你可以返回审核界面。",
                buttons=[{"id": "back_to_review", "label": "返回审核", "style": "primary"}],
            ),
            choice_block(
                block_id="history_actions",
                question="接下来要做什么？",
                options=[{"id": "back_to_review", "label": "返回审核"}],
            ),
        ]
        return self._wrap_step(
            step_id="history_view",
            message="这里是当前画像会话的历史摘要。",
            blocks=blocks,
            input_kind="choice",
            next_hint="返回审核界面，或使用单独的 history API 获取更完整数据。",
        )

    def build_update_basic_identity_step(self) -> dict[str, Any]:
        return self._wrap_step(
            step_id="update_basic_identity",
            message="请选择你想修改的基础身份字段。",
            blocks=[
                choice_block(
                    block_id="update_basic_identity",
                    question="请选择要修改的基础身份字段。",
                    options=[
                        {"id": "research_stage", "label": "研究阶段"},
                        {"id": "fields", "label": "学科领域 / 交叉方向"},
                        {"id": "method", "label": "方法范式"},
                        {"id": "institution", "label": "所在机构"},
                        {"id": "advisor_team", "label": "导师 / 团队方向"},
                        {"id": "academic_network", "label": "学术合作圈"},
                        {"id": "back_to_review", "label": "返回审核"},
                    ],
                )
            ],
            input_kind="choice",
            next_hint="选择要修改的字段。",
        )

    def build_update_process_select_step(self) -> dict[str, Any]:
        options = [{"id": key, "label": label} for key, label in PROCESS_DIMENSIONS]
        options.append({"id": "back_to_review", "label": "返回审核"})
        return self._wrap_step(
            step_id="update_process_select",
            message="请选择要修改的科研流程能力维度。",
            blocks=[choice_block(block_id="update_process_select", question="请选择要修改的科研流程能力维度。", options=options)],
            input_kind="choice",
            next_hint="选择一个流程能力维度。",
        )

    def build_update_needs_select_step(self) -> dict[str, Any]:
        return self._wrap_step(
            step_id="update_needs_select",
            message="请选择你想修改的当前需求字段。",
            blocks=[
                choice_block(
                    block_id="update_needs_select",
                    question="请选择要修改的当前需求字段。",
                    options=[
                        {"id": "major_time_occupation", "label": "主要时间占用"},
                        {"id": "pain_points", "label": "核心难点"},
                        {"id": "desired_change", "label": "最想改变的事"},
                        {"id": "back_to_review", "label": "返回审核"},
                    ],
                )
            ],
            input_kind="choice",
            next_hint="选择要修改的当前需求字段。",
        )

    def build_text_update_step(
        self,
        *,
        step_id: str,
        question: str,
        placeholder: str,
        policy_state: dict[str, Any],
    ) -> dict[str, Any]:
        return self._wrap_step(
            step_id=step_id,
            message=question,
            blocks=[text_input_block(block_id=step_id, question=question, placeholder=placeholder, multiline=True)],
            input_kind="text",
            next_hint="输入新的内容即可；若不需要此字段，可输入“跳过”。",
            policy_state=policy_state,
        )

    def build_process_rating_step(self, *, dimension_key: str) -> dict[str, Any]:
        label = dict(PROCESS_DIMENSIONS)[dimension_key]
        return self._wrap_step(
            step_id="update_process_rating",
            message=f"请为“{label}”重新评分（1-5）。",
            blocks=[
                choice_block(
                    block_id=f"update_process_rating_{dimension_key}",
                    question=f"请为“{label}”重新评分（1-5）。",
                    options=[{"id": str(index), "label": str(index)} for index in range(1, 6)],
                )
            ],
            input_kind="choice",
            next_hint="选择 1 到 5 的评分。",
            policy_state={"dimension_key": dimension_key},
        )

    def build_process_detail_step(self, *, dimension_key: str, score: float) -> dict[str, Any]:
        label = dict(PROCESS_DIMENSIONS)[dimension_key]
        return self._wrap_step(
            step_id="update_process_detail",
            message=f"请补充“{label}”的简要说明；如无可输入“跳过”。",
            blocks=[
                text_input_block(
                    block_id=f"update_process_detail_{dimension_key}",
                    question=f"请补充“{label}”的简要说明；如无可输入“跳过”。",
                    placeholder="例如：我在这个环节最擅长什么，或最想提升什么。",
                    multiline=True,
                )
            ],
            input_kind="text",
            next_hint="直接输入说明，或输入“跳过”。",
            policy_state={"dimension_key": dimension_key, "score": score},
        )


portrait_review_service = PortraitReviewService()
