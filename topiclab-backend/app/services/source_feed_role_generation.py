"""Generate 4 discussion roles from topic using AI_GENERATION_MODEL."""

from __future__ import annotations

import json
import os
import re
from typing import Any

import httpx

_NUM_ROLES = 4

_SYSTEM_PROMPT = (
    "你是讨论角色设计专家。根据话题内容，生成 4 个互补的讨论角色。"
    "每个角色需有独特视角，能从不同维度贡献讨论。"
    "输出严格为 JSON 数组，每个元素格式："
    '{"name": "英文slug如industry_analyst", "label": "中文显示名", "description": "一句话描述", "role_content": "Markdown格式的角色定义，包含## Identity、## Expertise、## Thinking Style 三部分"}'
    "name 仅用英文、数字、下划线；label 为中文；role_content 为完整 role.md 正文，不含一级标题（如 # Industry Analyst）。"
)

_USER_PROMPT_TEMPLATE = """请基于以下话题，生成 4 个讨论角色。

话题标题：{title}

话题正文：
{body}

要求：4 个角色视角互补，覆盖技术、产业、研究、治理等不同维度。输出 JSON 数组。"""


def _required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"{name} is not set")
    return value


def _safe_text(value: Any, *, fallback: str = "") -> str:
    text = str(value or "").strip()
    return text or fallback


def _slugify(name: str) -> str:
    """Convert to valid expert name slug: alphanumeric + underscore."""
    s = re.sub(r"[^a-zA-Z0-9_]", "_", name)
    return s.strip("_").lower() or "expert"


def _parse_json_array(raw: str) -> list[dict]:
    """Extract JSON array from model output, handling markdown fences."""
    content = raw.strip()
    if content.startswith("```"):
        lines = content.splitlines()
        if len(lines) > 1 and lines[0].strip().startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        content = "\n".join(lines)
    try:
        data = json.loads(content)
        return data if isinstance(data, list) else []
    except Exception:
        return []


async def generate_roles_from_topic(
    topic_title: str,
    topic_body: str,
    *,
    article: dict[str, Any] | None = None,
) -> list[dict[str, str]]:
    """Generate 4 role definitions from topic using AI_GENERATION_MODEL.

    Returns list of {"name", "label", "description", "role_content"}.
    Falls back to empty list if env not configured or generation fails.
    """
    try:
        base_url = _required_env("AI_GENERATION_BASE_URL")
        api_key = _required_env("AI_GENERATION_API_KEY")
        model = _required_env("AI_GENERATION_MODEL")
    except ValueError:
        return []

    title = _safe_text(topic_title, fallback="未命名话题")
    body = _safe_text(topic_body, fallback="")
    if article:
        desc = _safe_text(article.get("description"), fallback="")
        if desc and len(body) < 200:
            body = f"{body}\n\n原文摘要：{desc}".strip()

    user_prompt = _USER_PROMPT_TEMPLATE.format(title=title, body=body[:8000])

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.3,
    }
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{base_url.rstrip('/')}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
        response.raise_for_status()
        data = response.json()
        raw_content = str(data["choices"][0]["message"]["content"])
        parsed = _parse_json_array(raw_content)
    except Exception:
        return []

    result: list[dict[str, str]] = []
    seen_names: set[str] = set()
    for i, item in enumerate(parsed[: _NUM_ROLES]):
        if not isinstance(item, dict):
            continue
        raw_name = _safe_text(item.get("name") or item.get("id"), fallback=f"role_{i+1}")
        name = _slugify(raw_name)
        if not name or name in seen_names:
            name = f"role_{i+1}" if f"role_{i+1}" not in seen_names else f"role_{i}_{hash(raw_name) % 10000}"
        seen_names.add(name)

        label = _safe_text(item.get("label"), fallback=name)
        description = _safe_text(item.get("description"), fallback=label)
        role_content = _safe_text(item.get("role_content"), fallback=description)

        if not role_content:
            role_content = f"# {label}\n\n## Identity\n\n{description}\n\n## Expertise\n\n- {description}\n\n## Thinking Style\n\n- 从本领域视角出发，提供有洞见的观点"

        result.append({
            "name": name,
            "label": label,
            "description": description,
            "role_content": role_content,
        })

    return result[: _NUM_ROLES]
