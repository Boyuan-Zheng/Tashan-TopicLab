"""Legacy-product-compatible skill policy for portrait-session orchestration."""

from __future__ import annotations

import re
from typing import Any

from app.portrait.runtime.block_protocol import choice_block, copyable_block, rating_block, text_block, text_input_block
from app.portrait.runtime.definitions_loader import definitions_loader


PROCESS_DIMENSIONS = [
    ("problem_definition", "问题定义能力"),
    ("literature", "文献整合能力"),
    ("design", "方案设计能力"),
    ("execution", "实验执行能力"),
    ("writing", "论文写作能力"),
    ("management", "项目管理能力"),
]


def _state_json(current_state: dict[str, Any] | None) -> dict[str, Any]:
    if not current_state:
        return {}
    return current_state.get("state_json") or {}


def _profile(current_state: dict[str, Any] | None) -> dict[str, Any]:
    return _state_json(current_state).get("profile") or {}


def _profile_basic_info(current_state: dict[str, Any] | None) -> dict[str, Any]:
    return _profile(current_state).get("basic_info") or {}


def _profile_capability(current_state: dict[str, Any] | None) -> dict[str, Any]:
    return _profile(current_state).get("capability") or {}


def _profile_current_needs(current_state: dict[str, Any] | None) -> dict[str, Any]:
    return _profile(current_state).get("current_needs") or {}


class PortraitSkillPolicyService:
    """Encode the old portrait-product skill policy above durable runtimes."""

    research_stage_options = [
        {"id": "博士生", "label": "博士生"},
        {"id": "博士后", "label": "博士后"},
        {"id": "青年教师", "label": "青年教师 / 助理教授 / 讲师"},
        {"id": "独立PI", "label": "独立 PI / 教授 / 研究员"},
        {"id": "其他", "label": "其他"},
    ]

    method_options = [
        {"id": "实验法", "label": "实验法"},
        {"id": "理论推导", "label": "理论推导"},
        {"id": "计算建模", "label": "计算建模"},
        {"id": "数据驱动", "label": "数据驱动"},
        {"id": "质性研究", "label": "质性研究"},
        {"id": "混合方法", "label": "混合方法"},
        {"id": "其他", "label": "其他"},
    ]

    need_feeling_options = [
        {"id": "充实", "label": "充实"},
        {"id": "疲惫", "label": "疲惫"},
        {"id": "混乱", "label": "混乱"},
        {"id": "其他", "label": "其他"},
        {"id": "skip", "label": "跳过"},
    ]

    help_type_options = [
        {"id": "方法支持", "label": "方法支持"},
        {"id": "资源支持", "label": "资源支持"},
        {"id": "情绪支持", "label": "情绪支持"},
        {"id": "其他", "label": "其他"},
        {"id": "skip", "label": "跳过"},
    ]

    desired_change_options = [
        {"id": "科研进展提速", "label": "科研进展提速"},
        {"id": "写作发表突破", "label": "写作发表突破"},
        {"id": "时间管理改善", "label": "时间管理改善"},
        {"id": "某项技能提升", "label": "某项技能提升"},
        {"id": "人际关系/合作", "label": "人际关系 / 合作"},
        {"id": "其他", "label": "其他"},
    ]

    def _wrap_policy_step(
        self,
        *,
        step_id: str,
        skill_id: str,
        input_kind: str,
        message: str,
        blocks: list[dict[str, Any]],
        next_hint: str,
        policy_state: dict[str, Any] | None = None,
        payload_extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload = {
            "policy": {
                "mode": "legacy_product",
                "skill_id": skill_id,
                "step_id": step_id,
                "policy_state": policy_state or {},
            },
            "blocks": blocks,
        }
        if payload_extra:
            payload.update(payload_extra)
        return {
            "stage": "skill_policy",
            "input_kind": input_kind,
            "message": message,
            "payload": payload,
            "next_hint": next_hint,
        }

    def _preview_payload(self, current_state: dict[str, Any] | None) -> dict[str, Any] | None:
        if not current_state:
            return None
        return {
            "portrait_state_id": current_state.get("portrait_state_id"),
            "keys": sorted((_state_json(current_state) or {}).keys()),
        }

    def build_welcome_step(self) -> dict[str, Any]:
        privacy_notice = (
            "你好！欢迎使用他山数字分身系统。\n\n"
            "在开始建立画像之前，请先知悉：你提供的信息只用于构建和更新你的数字分身，"
            "不会向第三方泄露，也不会用于模型训练。你可以自行决定数字分身是否公开。"
        )
        question = (
            "在开始逐项填写之前，想先问一下：你平时有没有使用过带记忆功能的 AI 工具？"
        )
        blocks = [
            text_block(privacy_notice),
            choice_block(
                block_id="start_method",
                question=question,
                options=[
                    {
                        "id": "ai_memory",
                        "label": "A. 有，先从 AI 记忆中提取信息",
                        "description": "先生成一段提示词，发给你平时使用的 AI，再把回复粘贴回来。",
                    },
                    {
                        "id": "direct",
                        "label": "B. 没有，或者不需要，直接开始填写",
                        "description": "直接通过对话逐项采集基础信息。",
                    },
                ],
            ),
        ]
        return self._wrap_policy_step(
            step_id="welcome_start_method",
            skill_id="collect-basic-info",
            input_kind="choice",
            message=question,
            blocks=blocks,
            next_hint="请选择从 AI 记忆开始，或直接开始填写。",
        )

    def build_ai_memory_import_step(
        self,
        *,
        prompt_text: str,
        handoff: dict[str, Any],
        current_state: dict[str, Any] | None,
    ) -> dict[str, Any]:
        blocks = [
            text_block("好的。请把下面这段提示词发给你常用的 AI，然后把它的完整回复粘贴回来。"),
            copyable_block(title="AI 记忆提取提示词", content=prompt_text),
            text_input_block(
                block_id="ai_memory_reply",
                question="请将外部 AI 的完整回复粘贴到这里。",
                placeholder="粘贴外部 AI 的完整回答，系统会自动解析并写入当前画像。",
                multiline=True,
            ),
        ]
        return self._wrap_policy_step(
            step_id="ai_memory_reply",
            skill_id="generate-ai-memory-prompt",
            input_kind="text",
            message="系统已生成 AI 记忆提取提示词，请在拿到回复后直接粘贴回来。",
            blocks=blocks,
            next_hint="把外部 AI 的完整回复粘贴回来即可。",
            payload_extra={
                "handoff": handoff,
                "prompt_text": prompt_text,
                "result_preview": self._preview_payload(current_state),
            },
        )

    def build_basic_info_step(self, step_id: str, *, current_state: dict[str, Any] | None) -> dict[str, Any]:
        preview = self._preview_payload(current_state)

        if step_id == "basic_research_stage":
            question = "你目前处于哪个研究阶段？"
            blocks = [choice_block(block_id=step_id, question=question, options=self.research_stage_options)]
            return self._wrap_policy_step(
                step_id=step_id,
                skill_id="collect-basic-info",
                input_kind="choice",
                message=question,
                blocks=blocks,
                next_hint="请选择最接近你的当前研究阶段。",
                payload_extra={"result_preview": preview},
            )

        if step_id == "basic_primary_secondary_fields":
            question = "你的主要研究领域是什么？请写明一级学科、具体方向，如有交叉方向也请提及。"
            blocks = [
                text_input_block(
                    block_id=step_id,
                    question=question,
                    placeholder="例如：认知科学；计算神经科学；交叉 AI 与脑科学",
                    multiline=True,
                )
            ]
            return self._wrap_policy_step(
                step_id=step_id,
                skill_id="collect-basic-info",
                input_kind="text",
                message=question,
                blocks=blocks,
                next_hint="直接输入一段文字即可。",
                payload_extra={"result_preview": preview},
            )

        if step_id == "basic_method_paradigm":
            question = "你主要采用哪种研究方法？"
            blocks = [choice_block(block_id=step_id, question=question, options=self.method_options)]
            return self._wrap_policy_step(
                step_id=step_id,
                skill_id="collect-basic-info",
                input_kind="choice",
                message=question,
                blocks=blocks,
                next_hint="请选择最主要的方法范式。",
                payload_extra={"result_preview": preview},
            )

        if step_id == "basic_institution":
            question = "你所在的机构名称是什么？"
            blocks = [
                text_input_block(
                    block_id=step_id,
                    question=question,
                    placeholder="例如：北京大学物理学院 / 中国科学院国家天文台",
                    multiline=False,
                )
            ]
            return self._wrap_policy_step(
                step_id=step_id,
                skill_id="collect-basic-info",
                input_kind="text",
                message=question,
                blocks=blocks,
                next_hint="填写机构名即可。",
                payload_extra={"result_preview": preview},
            )

        if step_id == "basic_advisor_team":
            question = "你的导师姓名是什么？所在实验室/团队的主要研究方向是？"
            blocks = [
                text_input_block(
                    block_id=step_id,
                    question=question,
                    placeholder="例如：张教授，团队主要做计算神经科学；不确定或无导师可填“无”。",
                    multiline=True,
                )
            ]
            return self._wrap_policy_step(
                step_id=step_id,
                skill_id="collect-basic-info",
                input_kind="text",
                message=question,
                blocks=blocks,
                next_hint="请描述导师和团队方向；没有的话填“无”。",
                payload_extra={"result_preview": preview},
            )

        if step_id == "basic_academic_network":
            question = "你目前的学术合作圈大概是什么情况？"
            blocks = [
                text_input_block(
                    block_id=step_id,
                    question=question,
                    placeholder="例如：实验室内部为主，也有跨机构合作；或主要独立工作。",
                    multiline=True,
                )
            ]
            return self._wrap_policy_step(
                step_id=step_id,
                skill_id="collect-basic-info",
                input_kind="text",
                message=question,
                blocks=blocks,
                next_hint="请尽量描述当前合作圈和跨机构/跨学科情况。",
                payload_extra={"result_preview": preview},
            )

        if step_id.startswith("process_rating:"):
            dimension_key = step_id.split(":", 1)[1]
            label = dict(PROCESS_DIMENSIONS)[dimension_key]
            question = f"接下来请为“{label}”打分（1=非常薄弱，5=非常强）。"
            blocks = [
                rating_block(
                    block_id=step_id,
                    question=question,
                    min_val=1,
                    max_val=5,
                    min_label="1（非常薄弱）",
                    max_label="5（非常强）",
                )
            ]
            return self._wrap_policy_step(
                step_id="process_rating",
                skill_id="collect-basic-info",
                input_kind="choice",
                message=question,
                blocks=blocks,
                next_hint="请选择 1 到 5 的评分。",
                policy_state={"dimension_key": dimension_key},
                payload_extra={"result_preview": preview},
            )

        if step_id.startswith("process_detail:"):
            dimension_key = step_id.split(":", 1)[1]
            label = dict(PROCESS_DIMENSIONS)[dimension_key]
            question = f"有没有你在“{label}”上特别擅长或特别想提升的具体方面？如无可输入“跳过”。"
            blocks = [
                text_input_block(
                    block_id=step_id,
                    question=question,
                    placeholder="例如：我比较擅长文献梳理，但希望提升问题定义的聚焦能力；如无可输入“跳过”。",
                    multiline=True,
                )
            ]
            return self._wrap_policy_step(
                step_id="process_detail",
                skill_id="collect-basic-info",
                input_kind="text",
                message=question,
                blocks=blocks,
                next_hint="可补充说明，或输入“跳过”。",
                policy_state={"dimension_key": dimension_key},
                payload_extra={"result_preview": preview},
            )

        if step_id == "capability_tech_stack":
            question = "请列举你主要使用的编程语言和科研工具，并大致说明熟练程度。"
            blocks = [
                text_input_block(
                    block_id=step_id,
                    question=question,
                    placeholder="例如：Python（熟练）、MATLAB（入门）、fMRIPrep（日常使用）",
                    multiline=True,
                )
            ]
            return self._wrap_policy_step(
                step_id=step_id,
                skill_id="collect-basic-info",
                input_kind="text",
                message=question,
                blocks=blocks,
                next_hint="请按“工具（熟练度）”方式列举即可。",
                payload_extra={"result_preview": preview},
            )

        if step_id == "capability_outputs":
            question = "如果有的话，请简述你的代表性学术产出，比如已发表论文、开源项目、工具包等。"
            blocks = [
                text_input_block(
                    block_id=step_id,
                    question=question,
                    placeholder="可填写论文、项目、代码仓库；如暂时没有可输入“跳过”。",
                    multiline=True,
                )
            ]
            return self._wrap_policy_step(
                step_id=step_id,
                skill_id="collect-basic-info",
                input_kind="text",
                message=question,
                blocks=blocks,
                next_hint="此字段可选，没有可输入“跳过”。",
                payload_extra={"result_preview": preview},
            )

        if step_id == "needs_time_occupation":
            question = "你现在每天/每周花费最多精力的事情是什么？可以列举 1–3 件。"
            blocks = [
                text_input_block(
                    block_id=step_id,
                    question=question,
                    placeholder="例如：论文写作、数据分析、组会沟通。",
                    multiline=True,
                )
            ]
            return self._wrap_policy_step(
                step_id=step_id,
                skill_id="collect-basic-info",
                input_kind="text",
                message=question,
                blocks=blocks,
                next_hint="可直接列举 1 到 3 件主要事项。",
                payload_extra={"result_preview": preview},
            )

        if step_id == "needs_time_feeling":
            question = "做这些事情时，你的整体感受更接近哪一种？"
            blocks = [choice_block(block_id=step_id, question=question, options=self.need_feeling_options)]
            return self._wrap_policy_step(
                step_id=step_id,
                skill_id="collect-basic-info",
                input_kind="choice",
                message=question,
                blocks=blocks,
                next_hint="可选感受类型，不想回答可跳过。",
                payload_extra={"result_preview": preview},
            )

        if step_id == "needs_pain_points":
            question = "你目前遇到的最大卡点或困扰是什么？哪件事让你感觉推不动？"
            blocks = [
                text_input_block(
                    block_id=step_id,
                    question=question,
                    placeholder="例如：论文故事线组织困难、实验推进慢、合作沟通卡住。",
                    multiline=True,
                )
            ]
            return self._wrap_policy_step(
                step_id=step_id,
                skill_id="collect-basic-info",
                input_kind="text",
                message=question,
                blocks=blocks,
                next_hint="请描述最核心的一个或几个卡点。",
                payload_extra={"result_preview": preview},
            )

        if step_id == "needs_help_type":
            question = "针对这个困难，你更希望获得哪类帮助？"
            blocks = [choice_block(block_id=step_id, question=question, options=self.help_type_options)]
            return self._wrap_policy_step(
                step_id=step_id,
                skill_id="collect-basic-info",
                input_kind="choice",
                message=question,
                blocks=blocks,
                next_hint="可选方法、资源、情绪支持等；不想回答可跳过。",
                payload_extra={"result_preview": preview},
            )

        if step_id == "needs_desired_change":
            question = "如果现在有一件事可以改变，让你接下来三个月更顺，你最想改变什么？"
            blocks = [choice_block(block_id=step_id, question=question, options=self.desired_change_options)]
            return self._wrap_policy_step(
                step_id=step_id,
                skill_id="collect-basic-info",
                input_kind="choice",
                message=question,
                blocks=blocks,
                next_hint="请选择最贴近的一项；如为其他，会在下一步补充。",
                payload_extra={"result_preview": preview},
            )

        if step_id == "needs_desired_change_text":
            question = "请描述你最想改变的那件事。"
            blocks = [
                text_input_block(
                    block_id=step_id,
                    question=question,
                    placeholder="例如：希望把论文写作和实验推进节奏真正稳定下来。",
                    multiline=True,
                )
            ]
            return self._wrap_policy_step(
                step_id=step_id,
                skill_id="collect-basic-info",
                input_kind="text",
                message=question,
                blocks=blocks,
                next_hint="直接输入你最想改变的事。",
                payload_extra={"result_preview": preview},
            )

        raise ValueError(f"unsupported basic info step: {step_id}")

    def next_basic_info_step(self, *, current_state: dict[str, Any] | None) -> dict[str, Any] | None:
        basic_info = _profile_basic_info(current_state)
        capability = _profile_capability(current_state)
        current_needs = _profile_current_needs(current_state)
        process = capability.get("process") or {}

        if not basic_info.get("research_stage"):
            return self.build_basic_info_step("basic_research_stage", current_state=current_state)
        if not basic_info.get("primary_field"):
            return self.build_basic_info_step("basic_primary_secondary_fields", current_state=current_state)
        if not basic_info.get("method_paradigm"):
            return self.build_basic_info_step("basic_method_paradigm", current_state=current_state)
        if not basic_info.get("institution"):
            return self.build_basic_info_step("basic_institution", current_state=current_state)
        if "advisor_team" not in basic_info:
            return self.build_basic_info_step("basic_advisor_team", current_state=current_state)
        if not basic_info.get("academic_network"):
            return self.build_basic_info_step("basic_academic_network", current_state=current_state)

        for dimension_key, _label in PROCESS_DIMENSIONS:
            item = process.get(dimension_key) or {}
            if item.get("score") in (None, ""):
                return self.build_basic_info_step(f"process_rating:{dimension_key}", current_state=current_state)
            if "note" not in item:
                return self.build_basic_info_step(f"process_detail:{dimension_key}", current_state=current_state)

        if "tech_stack_text" not in capability:
            return self.build_basic_info_step("capability_tech_stack", current_state=current_state)
        if "representative_outputs" not in capability:
            return self.build_basic_info_step("capability_outputs", current_state=current_state)

        if "major_time_occupation" not in current_needs:
            return self.build_basic_info_step("needs_time_occupation", current_state=current_state)
        if "time_feeling" not in current_needs:
            return self.build_basic_info_step("needs_time_feeling", current_state=current_state)
        if "pain_points" not in current_needs:
            return self.build_basic_info_step("needs_pain_points", current_state=current_state)
        if "desired_support" not in current_needs:
            return self.build_basic_info_step("needs_help_type", current_state=current_state)
        if "desired_change" not in current_needs:
            return self.build_basic_info_step("needs_desired_change", current_state=current_state)

        return None

    def is_basic_info_complete(self, *, current_state: dict[str, Any] | None) -> bool:
        return self.next_basic_info_step(current_state=current_state) is None

    def parse_field_statement(self, text_value: str) -> dict[str, Any]:
        cleaned = text_value.strip()
        parts = [part.strip() for part in re.split(r"[；;\n]+", cleaned) if part.strip()]
        primary_field = parts[0] if parts else cleaned
        secondary_field = parts[1] if len(parts) > 1 else None
        cross_discipline = parts[2] if len(parts) > 2 else None
        if cross_discipline is None and ("交叉" in cleaned or "×" in cleaned or "+" in cleaned):
            cross_discipline = cleaned
        result = {
            "primary_field": primary_field,
            "field_statement": cleaned,
        }
        if secondary_field is not None:
            result["secondary_field"] = secondary_field
        if cross_discipline is not None:
            result["cross_discipline"] = cross_discipline
        return result


portrait_skill_policy_service = PortraitSkillPolicyService()
