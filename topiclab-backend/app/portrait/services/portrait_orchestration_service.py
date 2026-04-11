"""Orchestration helpers for the unified portrait session runtime."""

from __future__ import annotations

from typing import Any

from app.portrait.runtime.block_protocol import actions_block, choice_block, copyable_block, rating_block, text_block, text_input_block
from app.portrait.runtime.definitions_loader import definitions_loader


class PortraitOrchestrationService:
    """Build normalized next-step instructions above slice runtimes."""

    def _action_options(self) -> list[dict[str, str]]:
        options = [
            {
                "choice": "continue_dialogue",
                "label": "继续补充",
                "description": "继续输入新的自我介绍、工作方式或长期目标。",
            }
        ]
        for item in definitions_loader.list_scales()["list"]:
            options.append(
                {
                    "choice": f"scale:{item['scale_id']}",
                    "label": f"开始量表 {item['name']}",
                    "description": f"进入 {item['scale_id']} 的统一会话答题路径。",
                }
            )
        options.extend(
            [
                {
                    "choice": "forum:generate",
                    "label": "生成论坛画像",
                    "description": "按论坛公开展示口径生成一份对外画像草稿。",
                },
                {
                    "choice": "scientist:famous",
                    "label": "匹配著名科学家",
                    "description": "给出与你当前画像最接近的著名科学家匹配结果。",
                },
                {
                    "choice": "scientist:field",
                    "label": "推荐领域科学家",
                    "description": "根据当前研究方向推荐可参考的领域科学家。",
                },
                {
                    "choice": "export:structured",
                    "label": "导出结构化画像",
                    "description": "导出 JSON 结构化画像。",
                },
                {
                    "choice": "export:profile_markdown",
                    "label": "导出完整 Markdown",
                    "description": "导出完整画像 markdown。",
                },
                {
                    "choice": "export:forum_markdown",
                    "label": "导出论坛 Markdown",
                    "description": "导出论坛展示版 markdown。",
                },
                {
                    "choice": "publish:brief",
                    "label": "发布 brief twin",
                    "description": "将当前画像以 brief 口径发布进 twin runtime。",
                },
                {
                    "choice": "publish:full",
                    "label": "发布 full twin",
                    "description": "将当前画像以 full 口径发布进 twin runtime。",
                },
            ]
        )
        return options

    def build_initial_step(self) -> dict[str, Any]:
        question = "请先用一段文字介绍你当前最重要的研究主题、工作方式和长期目标。"
        return {
            "stage": "dialogue",
            "input_kind": "text",
            "message": question,
            "payload": {
                "prompt_kind": "self_introduction",
                "suggested_topics": [
                    "正在做的核心方向",
                    "最擅长的工作方式",
                    "希望系统进一步了解的部分",
                ],
                "blocks": [
                    text_input_block(
                        block_id="dialogue_intro",
                        question=question,
                        placeholder="例如：我目前主要做什么研究、常用什么工作方式、接下来三年最想突破什么。",
                        multiline=True,
                    )
                ],
            },
            "next_hint": "直接输入一段文字即可，系统会继续追问并更新当前画像状态。",
        }

    def build_dialogue_followup_step(
        self,
        *,
        generated_message: dict[str, Any] | None,
        current_state: dict[str, Any] | None,
        prepend_blocks: list[dict[str, Any]] | None = None,
        message_override: str | None = None,
    ) -> dict[str, Any]:
        preview = None
        if current_state:
            preview = {
                "portrait_state_id": current_state.get("portrait_state_id"),
                "keys": sorted((current_state.get("state_json") or {}).keys()),
            }
        message_text = (
            message_override
            or (
                generated_message.get("content_text")
                if generated_message and generated_message.get("content_text")
                else "系统已记录你的输入，请继续补充。"
            )
        )
        return {
            "stage": "dialogue",
            "input_kind": "text_or_choice",
            "message": message_text,
            "payload": {
                "last_generated_message": generated_message,
                "result_preview": preview,
                "next_options": self._action_options(),
                "blocks": [
                    *(prepend_blocks or []),
                    text_block(message_text),
                    text_input_block(
                        block_id="dialogue_followup",
                        question="请继续补充与你的研究主题、工作方式、长期目标或当前困难相关的信息。",
                        placeholder="继续输入一段文字，系统会继续更新画像并追问。",
                        multiline=True,
                    ),
                    actions_block(
                        message="如果当前信息已经足够，你也可以先去做量表或执行后续画像动作。",
                        buttons=[
                            {"id": item["choice"], "label": item["label"], "style": "secondary"}
                            for item in self._action_options()
                        ],
                    ),
                ],
            },
            "next_hint": "继续输入文字即可；如需切到其他动作，可用 choice 选择量表或后续画像动作。",
        }

    def build_scale_question_step(self, *, scale_state: dict[str, Any]) -> dict[str, Any]:
        next_question = scale_state.get("next_question") or {}
        scale = scale_state.get("scale") or {}
        return {
            "stage": "scale_question",
            "input_kind": "choice",
            "message": next_question.get("text") or "请继续完成量表答题。",
            "payload": {
                "scale": scale,
                "session": scale_state.get("session"),
                "progress": scale_state.get("progress"),
                "next_question": next_question,
                "value_range": {
                    "min": 1,
                    "max": 7,
                },
                "blocks": [
                    rating_block(
                        block_id=str(next_question.get("id") or scale_state.get("session", {}).get("session_id") or "scale_question"),
                        question=next_question.get("text") or "请继续完成量表答题。",
                        min_val=1,
                        max_val=7,
                        min_label="1",
                        max_label="7",
                    )
                ],
            },
            "next_hint": "使用 choice 提交当前题目的选项值。通常是 1 到 7 之间的数字。",
        }

    def build_scale_completed_step(
        self,
        *,
        scale_result: dict[str, Any],
        current_state: dict[str, Any] | None,
    ) -> dict[str, Any]:
        preview = None
        if current_state:
            preview = {
                "portrait_state_id": current_state.get("portrait_state_id"),
                "keys": sorted((current_state.get("state_json") or {}).keys()),
            }
        return {
            "stage": "dialogue",
            "input_kind": "text_or_choice",
            "message": "量表结果已写入当前画像状态。优先继续补充文字；如果当前信息已经足够，也可以选择下一步动作。",
            "payload": {
                "scale_result": scale_result,
                "result_preview": preview,
                "next_options": self._action_options(),
                "blocks": [
                    text_block("量表结果已写入当前画像状态。"),
                    choice_block(
                        block_id="post_scale_actions",
                        question="你希望下一步做什么？",
                        options=self._action_options(),
                    ),
                ],
            },
            "next_hint": "你可以继续输入文字，或继续做别的量表和后续画像动作。",
        }

    def build_import_request_step(
        self,
        *,
        handoff: dict[str, Any],
        artifacts: list[dict[str, Any]],
        current_state: dict[str, Any] | None,
    ) -> dict[str, Any]:
        prompt_text = None
        for item in artifacts:
            if item.get("artifact_type") == "prompt_text":
                prompt_text = item.get("content_text")
                break
        preview = None
        if current_state:
            preview = {
                "portrait_state_id": current_state.get("portrait_state_id"),
                "keys": sorted((current_state.get("state_json") or {}).keys()),
            }
        return {
            "stage": "import_result",
            "input_kind": "external_text_or_json",
            "message": "系统已生成画像补充提纲。请优先把它当作继续访谈当前智能体的内部提纲；整理出补充结果后直接粘贴回来。",
            "payload": {
                "handoff": handoff,
                "artifacts": artifacts,
                "prompt_text": prompt_text,
                "result_preview": preview,
                "blocks": [
                    text_block(
                        "系统已生成画像补充提纲。默认请先把它当作你自己的访谈提纲，继续向当前智能体追问并整理补充结果；"
                        "只有在确实需要时，才把它发给外部 AI。"
                    ),
                    copyable_block(title="画像补充提纲", content=prompt_text or ""),
                    text_input_block(
                        block_id="import_result",
                        question="请把整理后的补充结果直接粘贴回来。",
                        placeholder="可直接粘贴 markdown、自然语言，或改用 external_json 提交结构化结果。",
                        multiline=True,
                    ),
                ],
            },
            "next_hint": "使用 external_text 或 external_json 提交补充结果；只有确实需要时再把提纲发给外部 AI。",
        }

    def build_import_followup_step(
        self,
        *,
        import_result: dict[str, Any],
        parse_run: dict[str, Any],
        current_state: dict[str, Any] | None,
    ) -> dict[str, Any]:
        preview = None
        if current_state:
            preview = {
                "portrait_state_id": current_state.get("portrait_state_id"),
                "keys": sorted((current_state.get("state_json") or {}).keys()),
            }
        return {
            "stage": "dialogue",
            "input_kind": "text_or_choice",
            "message": "补充结果已导入并更新当前画像。请优先继续直接补充文字，或再选择下一步动作。",
            "payload": {
                "import_result": import_result,
                "parse_run": parse_run,
                "result_preview": preview,
                "next_options": self._action_options(),
                "blocks": [
                    text_block("外部结果已导入并更新当前画像。"),
                    choice_block(
                        block_id="post_import_actions",
                        question="你希望下一步做什么？",
                        options=self._action_options(),
                    ),
                ],
            },
            "next_hint": "你可以继续输入文字，或继续做量表和后续画像动作。",
        }

    def build_completed_step(self, *, current_state: dict[str, Any] | None) -> dict[str, Any]:
        return {
            "stage": "completed",
            "input_kind": "none",
            "message": "当前画像会话已完成，你现在可以查看结果。",
            "payload": {
                "result_preview": (
                    {
                        "portrait_state_id": current_state.get("portrait_state_id"),
                        "keys": sorted((current_state.get("state_json") or {}).keys()),
                    }
                    if current_state
                    else None
                ),
                "blocks": [
                    actions_block(
                        message="当前画像会话已完成。",
                        buttons=[{"id": "result", "label": "查看结果", "style": "primary"}],
                    )
                ],
            },
            "next_hint": "使用 result 读取当前画像状态。",
        }

    def build_reset_step(self, *, current_state: dict[str, Any] | None) -> dict[str, Any]:
        return {
            "stage": "reset",
            "input_kind": "none",
            "message": "当前画像创建会话已重置。你可以重新开始一个新的画像会话。",
            "payload": {
                "result_preview": (
                    {
                        "portrait_state_id": current_state.get("portrait_state_id"),
                        "keys": sorted((current_state.get("state_json") or {}).keys()),
                    }
                    if current_state
                    else None
                ),
                "blocks": [
                    actions_block(
                        message="当前画像创建会话已重置。",
                        buttons=[{"id": "start", "label": "重新开始", "style": "primary"}],
                    )
                ],
            },
            "next_hint": "使用 start 开启新的会话，或使用 history 查看之前的过程与结果。",
        }


portrait_orchestration_service = PortraitOrchestrationService()
