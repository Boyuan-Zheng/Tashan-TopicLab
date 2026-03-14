"""AI-based content moderation for TopicLab posts."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass

import httpx


@dataclass(slots=True)
class ModerationDecision:
    approved: bool
    reason: str
    suggestion: str
    category: str


_SYSTEM_PROMPT = """
你是社区内容审核助手，需要审核用户准备发布的文本内容是否适合在讨论社区公开发送。

审核规则：
1. 拒绝明显违法违规、暴力威胁、仇恨歧视、骚扰辱骂、色情露骨、诈骗引流、恶意广告、明显侵犯隐私或人身安全的内容。
2. 拒绝要求模型协助实施违法、危险或明显不当行为的内容。
3. 正常讨论、学术争论、产品反馈、一般情绪表达默认应通过，不要过度拦截。
4. 如果只是语气偏激但不构成严重违规，可通过并在 suggestion 给出温和化建议。

返回要求：
- 只能返回 JSON
- 字段固定为：
  {
    "approved": true/false,
    "reason": "给用户看的简短中文原因，20字以内优先",
    "suggestion": "如被拒绝，给出可修改建议；通过时可为空",
    "category": "normal|abuse|violence|sexual|illegal|privacy|spam|other"
  }
""".strip()


def _required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"{name} is not set")
    return value


def _parse_decision(raw_content: str) -> ModerationDecision:
    text = raw_content.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if len(lines) >= 2:
            text = "\n".join(lines[1:])
        text = text.removesuffix("```").strip()

    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"内容审核返回了无法解析的 JSON: {raw_content}") from exc

    return ModerationDecision(
        approved=bool(payload.get("approved")),
        reason=str(payload.get("reason") or "").strip() or "内容需要调整",
        suggestion=str(payload.get("suggestion") or "").strip(),
        category=str(payload.get("category") or "other").strip() or "other",
    )


async def moderate_post_content(content: str, *, scenario: str) -> ModerationDecision:
    base_url = _required_env("AI_GENERATION_BASE_URL")
    api_key = _required_env("AI_GENERATION_API_KEY")
    model = _required_env("AI_GENERATION_MODEL")

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"场景: {scenario}\n"
                    "请审核下面这段用户文本是否适合发布。\n"
                    "用户文本开始：\n"
                    f"{content}\n"
                    "用户文本结束。"
                ),
            },
        ],
        "temperature": 0.1,
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{base_url.rstrip('/')}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        message = exc.response.text.strip() or str(exc)
        raise ValueError(f"内容审核调用失败: HTTP {exc.response.status_code}: {message}") from exc
    except httpx.HTTPError as exc:
        raise ValueError(f"内容审核网络请求失败: {exc}") from exc

    try:
        data = response.json()
        raw_content = data["choices"][0]["message"]["content"]
    except Exception as exc:
        raise ValueError(f"内容审核响应格式异常: {response.text}") from exc

    return _parse_decision(raw_content)
