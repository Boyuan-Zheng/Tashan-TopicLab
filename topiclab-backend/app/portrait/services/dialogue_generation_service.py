"""Model-backed assistant generation for portrait dialogue runtime."""

from __future__ import annotations

import json
from typing import Any

from app.services.ai_generation_client import post_ai_generation_chat


_SYSTEM_PROMPT = """
你是「他山画像系统」的综合画像对话助手。

目标：
- 通过多轮中文对话，帮助用户逐步形成科研/认知画像
- 既要推进信息采集，也要逐步形成阶段性的综合理解

规则：
1. 每次回复尽量聚焦一个最有价值的问题，不要一次问多个问题。
2. 可以先用 1-3 句总结你当前理解，再问下一个问题。
3. 不要编造用户没有明确给出的事实；如果是推断，请明确说“我当前推测/理解是”。
4. 如果信息明显不足，优先提问；如果信息已经有一定积累，可以给出阶段性的画像草稿片段。
5. 语气专业、温和、简洁，不空泛，不说套话。
6. 直接输出给用户看的正文，不要输出 JSON，不要输出 Markdown 代码块。
""".strip()

def _strip_fenced_block(raw: str) -> str:
    text = raw.strip()
    if not text.startswith("```"):
        return text
    lines = text.splitlines()
    if len(lines) > 1 and lines[0].strip().startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()


def _render_message_content(message: dict[str, Any]) -> str:
    content_text = str(message.get("content_text") or "").strip()
    if content_text:
        return content_text
    content_json = message.get("content_json")
    if content_json is not None:
        try:
            return json.dumps(content_json, ensure_ascii=False)
        except Exception:
            return str(content_json)
    return ""


def _build_context_prompt(derived_state: dict[str, Any]) -> str:
    summary = derived_state.get("summary") or {}
    compact = {
        "status": derived_state.get("status"),
        "message_count": derived_state.get("message_count"),
        "has_user_input": derived_state.get("has_user_input"),
        "has_assistant_output": derived_state.get("has_assistant_output"),
        "summary": summary,
    }
    return (
        "下面是当前对话运行时摘要，请将其当作辅助上下文，而不是必须逐字复述的内容：\n"
        f"{json.dumps(compact, ensure_ascii=False)}"
    )


def _build_chat_messages(messages: list[dict[str, Any]]) -> list[dict[str, str]]:
    chat_messages: list[dict[str, str]] = []
    for message in messages[-16:]:
        role = str(message.get("role") or "user").strip() or "user"
        content = _render_message_content(message)
        if not content:
            continue
        if role not in {"user", "assistant", "system"}:
            role = "user"
        chat_messages.append({"role": role, "content": content})
    return chat_messages


class DialogueGenerationService:
    """Generate assistant replies for the portrait dialogue runtime."""

    async def generate_assistant_reply(
        self,
        messages: list[dict[str, Any]],
        derived_state: dict[str, Any],
        *,
        model: str | None = None,
    ) -> dict[str, str]:
        payload = {
            "messages": [
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "system", "content": _build_context_prompt(derived_state)},
                *_build_chat_messages(messages),
            ],
            "temperature": 0.4,
        }

        data, selected_model = await post_ai_generation_chat(
            payload,
            model=model,
            timeout=60.0,
            client_name="portrait-dialogue-generation",
        )
        raw_content = str(data["choices"][0]["message"]["content"] or "")
        content = _strip_fenced_block(raw_content).strip()
        if not content:
            raise ValueError("dialogue generation returned empty content")

        return {
            "content": content,
            "model": selected_model,
        }


dialogue_generation_service = DialogueGenerationService()
