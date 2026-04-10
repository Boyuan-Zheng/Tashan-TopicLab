"""Scientist matching and recommendations above canonical portrait projections."""

from __future__ import annotations

import json
import math
from typing import Any

from app.portrait.runtime.scientists_reference import load_scientists
from app.portrait.services.portrait_artifact_service import portrait_artifact_service
from app.portrait.services.portrait_projection_service import portrait_projection_service
from app.services.ai_generation_client import post_ai_generation_chat


def _score(value: Any, default: float) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def _normalized_distance(a: float, b: float, scale: float) -> float:
    return ((a - b) / scale) ** 2


class PortraitScientistService:
    """Provide famous-scientist matching and field recommendations."""

    def __init__(self) -> None:
        self._scientists = load_scientists()

    def _personality_distance(self, user_p: dict[str, Any], scientist: dict[str, Any]) -> float:
        dims = ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]
        values = []
        for dim in dims:
            user_value = _score(user_p.get(dim), 3.0) / 5.0
            scientist_value = _score(scientist.get(dim), 3.0) / 5.0
            values.append((user_value - scientist_value) ** 2)
        return math.sqrt(sum(values) / len(values))

    def _projection_metrics(self, projection: dict[str, Any]) -> tuple[dict[str, Any], float, float]:
        structured_profile = projection["structured_profile"]
        cognitive_style = structured_profile.get("cognitive_style") or {}
        motivation = structured_profile.get("motivation") or {}
        personality = structured_profile.get("personality") or {}
        user_csi = _score(cognitive_style.get("csi"), 0.0)
        user_rai = _score(motivation.get("rai"), 25.0)
        return personality, user_csi, user_rai

    def build_famous_match(self, projection: dict[str, Any]) -> dict[str, Any]:
        personality, user_csi, user_rai = self._projection_metrics(projection)
        scored: list[dict[str, Any]] = []
        for scientist in self._scientists:
            distance = math.sqrt(
                0.4 * _normalized_distance(user_csi, _score(scientist.get("csi"), 0.0), 48.0)
                + 0.4 * _normalized_distance(user_rai, _score(scientist.get("rai"), 25.0), 80.0)
                + 0.2 * (self._personality_distance(personality, scientist) ** 2)
            )
            similarity = max(0, round((1 - distance) * 100))
            scored.append({**scientist, "_distance": distance, "similarity": similarity})

        scored.sort(key=lambda item: item["_distance"])
        top3 = [
            {
                "name": item["name"],
                "name_en": item.get("name_en"),
                "field": item.get("field"),
                "era": item.get("era"),
                "similarity": item["similarity"],
                "reason": item.get("match_reason_template"),
                "signature": item.get("signature"),
                "csi": item.get("csi"),
                "rai": item.get("rai"),
            }
            for item in scored[:3]
        ]
        top_names = {item["name"] for item in top3}
        scatter_data = [
            {
                "name": item["name"],
                "name_en": item.get("name_en"),
                "csi": item.get("csi"),
                "rai": item.get("rai"),
                "is_top3": item["name"] in top_names,
            }
            for item in self._scientists
        ]
        return {
            "top3": top3,
            "scatter_data": scatter_data,
            "user_point": {"csi": user_csi, "rai": user_rai},
        }

    async def _llm_field_recommendations(self, structured_profile: dict[str, Any]) -> list[dict[str, Any]]:
        basic_info = structured_profile.get("basic_info") or {}
        field_text = " / ".join(
            item
            for item in [
                str(basic_info.get("primary_field") or "").strip(),
                str(basic_info.get("secondary_field") or "").strip(),
                str(basic_info.get("cross_discipline") or "").strip(),
            ]
            if item
        )
        method = str(basic_info.get("method_paradigm") or basic_info.get("method_statement") or "").strip()
        if not field_text:
            return []

        payload = {
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "你是一个学术推荐助手。请根据用户的研究方向，推荐 3-5 位与之相关的当代活跃科学家。"
                        "输出纯 JSON 数组，每项包含 name、name_en、institution、field、reason。"
                    ),
                },
                {
                    "role": "user",
                    "content": f"研究领域：{field_text}\n研究方法：{method or '未注明'}",
                },
            ],
            "temperature": 0.4,
        }
        data, model = await post_ai_generation_chat(
            payload,
            timeout=60.0,
            client_name="portrait-field-recommendation",
        )
        raw_content = str(data["choices"][0]["message"]["content"] or "").strip()
        if raw_content.startswith("```"):
            raw_content = raw_content.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        parsed = json.loads(raw_content)
        if not isinstance(parsed, list):
            return []
        for item in parsed:
            if isinstance(item, dict):
                item.setdefault("source", f"llm:{model}")
        return [item for item in parsed if isinstance(item, dict)]

    def _fallback_field_recommendations(self, structured_profile: dict[str, Any]) -> list[dict[str, Any]]:
        basic_info = structured_profile.get("basic_info") or {}
        query = " ".join(
            item.lower()
            for item in [
                str(basic_info.get("primary_field") or ""),
                str(basic_info.get("secondary_field") or ""),
                str(basic_info.get("cross_discipline") or ""),
                str(basic_info.get("method_paradigm") or ""),
            ]
            if item
        )
        if not query:
            return []
        scored: list[tuple[int, dict[str, Any]]] = []
        for scientist in self._scientists:
            haystack = " ".join(
                [
                    str(scientist.get("field") or "").lower(),
                    str(scientist.get("signature") or "").lower(),
                ]
            )
            score = sum(1 for token in query.split() if token and token in haystack)
            if score > 0:
                scored.append((score, scientist))
        scored.sort(key=lambda item: (-item[0], str(item[1].get("name") or "")))
        return [
            {
                "name": scientist["name"],
                "name_en": scientist.get("name_en"),
                "institution": "",
                "field": scientist.get("field"),
                "reason": scientist.get("signature"),
                "source": "fallback_reference",
            }
            for _score_value, scientist in scored[:5]
        ]

    async def generate_famous_match(self, *, user_id: int, display_name: str | None = None, source_session_id: str | None = None) -> dict[str, Any]:
        projection = portrait_projection_service.build_projection(user_id, display_name=display_name)
        result = self.build_famous_match(projection)
        artifact = portrait_artifact_service.record_artifact(
            user_id=user_id,
            portrait_state_id=projection["portrait_state_id"],
            source_session_id=source_session_id,
            artifact_kind="scientist_famous_match",
            format="json",
            title=f"{projection['structured_profile']['display_name']} scientist match",
            content_json=result,
        )
        return {"projection": projection, "match": result, "artifact": artifact}

    async def generate_field_recommendations(self, *, user_id: int, display_name: str | None = None, source_session_id: str | None = None) -> dict[str, Any]:
        projection = portrait_projection_service.build_projection(user_id, display_name=display_name)
        structured_profile = projection["structured_profile"]
        try:
            recommendations = await self._llm_field_recommendations(structured_profile)
        except Exception:
            recommendations = []
        if not recommendations:
            recommendations = self._fallback_field_recommendations(structured_profile)
        artifact = portrait_artifact_service.record_artifact(
            user_id=user_id,
            portrait_state_id=projection["portrait_state_id"],
            source_session_id=source_session_id,
            artifact_kind="scientist_field_recommendations",
            format="json",
            title=f"{projection['structured_profile']['display_name']} field scientists",
            content_json={"recommendations": recommendations},
        )
        return {"projection": projection, "recommendations": recommendations, "artifact": artifact}


portrait_scientist_service = PortraitScientistService()
