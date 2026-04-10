"""Deterministic parser for imported external-AI outputs."""

from __future__ import annotations

import re
from typing import Any


class ImportParseService:
    """Parse imported payloads into normalized candidate portrait updates."""

    parser_version = "portrait_import_v2"

    def _normalize_method(self, text_value: str) -> str | None:
        value = text_value.strip()
        if not value:
            return None
        mapping = [
            ("实验", "实验法"),
            ("理论", "理论推导"),
            ("计算", "计算建模"),
            ("建模", "计算建模"),
            ("数据", "数据驱动"),
            ("质性", "质性研究"),
            ("混合", "混合方法"),
        ]
        for keyword, normalized in mapping:
            if keyword in value:
                return normalized
        return value

    def _extract_labeled_answers(self, text_value: str) -> dict[str, str]:
        answers: dict[str, str] = {}
        current_key: str | None = None
        buffer: list[str] = []
        for raw_line in text_value.splitlines():
            line = raw_line.strip()
            match = re.match(r"^([A-F]\d+)[.、:：]?\s*(.*)$", line, re.IGNORECASE)
            if match:
                if current_key is not None:
                    answers[current_key] = "\n".join(buffer).strip()
                current_key = match.group(1).upper()
                first_value = match.group(2).strip()
                buffer = [first_value] if first_value else []
                continue
            if current_key is not None:
                if line:
                    buffer.append(line)
        if current_key is not None:
            answers[current_key] = "\n".join(buffer).strip()
        return answers

    def _parse_ai_memory_payload(self, text_value: str, *, source_type: str) -> dict[str, Any]:
        answers = self._extract_labeled_answers(text_value)
        basic_info: dict[str, Any] = {}
        current_needs: dict[str, Any] = {}

        if answers.get("A1"):
            basic_info["research_stage"] = answers["A1"]
        if answers.get("A2"):
            field_text = answers["A2"]
            field_parts = [part.strip() for part in re.split(r"[；;\n]+", field_text) if part.strip()]
            basic_info["primary_field"] = field_parts[0] if field_parts else field_text
            if len(field_parts) > 1:
                basic_info["secondary_field"] = field_parts[1]
            if len(field_parts) > 2:
                basic_info["cross_discipline"] = field_parts[2]
            elif "交叉" in field_text or "×" in field_text or "+" in field_text:
                basic_info["cross_discipline"] = field_text
            basic_info["field_statement"] = field_text
        if answers.get("A3"):
            normalized_method = self._normalize_method(answers["A3"])
            if normalized_method:
                basic_info["method_paradigm"] = normalized_method
                basic_info["method_statement"] = answers["A3"]
        if answers.get("A4"):
            basic_info["institution"] = answers["A4"]
        if answers.get("A5"):
            basic_info["advisor_team"] = answers["A5"]
        if answers.get("A6"):
            basic_info["academic_network"] = answers["A6"]

        if answers.get("C1"):
            current_needs["major_time_occupation"] = answers["C1"]
        if answers.get("C2"):
            current_needs["pain_points"] = answers["C2"]
        if answers.get("C3"):
            current_needs["desired_change"] = answers["C3"]

        candidate_state_patch: dict[str, Any] = {
            "imports": {
                "ai_memory": {
                    "source_type": source_type,
                    "structured_answers": answers,
                }
            }
        }
        if basic_info or current_needs:
            candidate_state_patch["profile"] = {}
            if basic_info:
                candidate_state_patch["profile"]["basic_info"] = basic_info
            if current_needs:
                candidate_state_patch["profile"]["current_needs"] = current_needs

        return {
            "parse_kind": "ai_memory_v2_outline",
            "source_type": source_type,
            "candidate_state_patch": candidate_state_patch,
            "summary": {
                "has_text": bool(text_value.strip()),
                "answer_codes": sorted(answers.keys()),
                "basic_info_fields": sorted(basic_info.keys()),
                "current_need_fields": sorted(current_needs.keys()),
            },
        }

    def parse_payload(
        self,
        *,
        source_type: str,
        payload_text: str | None,
        payload_json: Any,
        prompt_kind: str | None = None,
    ) -> dict[str, Any]:
        if payload_json is not None:
            candidate_patch = payload_json if isinstance(payload_json, dict) else {"external_payload": payload_json}
            return {
                "parse_kind": "json_passthrough",
                "source_type": source_type,
                "candidate_state_patch": candidate_patch,
                "summary": {
                    "has_json": True,
                    "has_text": bool(payload_text and payload_text.strip()),
                },
            }

        text_value = (payload_text or "").strip()
        if prompt_kind == "ai_memory":
            return self._parse_ai_memory_payload(text_value, source_type=source_type)

        lines = [line.strip() for line in text_value.splitlines()]
        non_empty_lines = [line for line in lines if line]
        headings = [
            line.lstrip("#").strip()
            for line in non_empty_lines
            if line.startswith("#") or line.endswith(":")
        ]
        preview = "\n".join(non_empty_lines[:6])[:1200]

        return {
            "parse_kind": "text_outline",
            "source_type": source_type,
            "candidate_state_patch": {
                "external_import": {
                    "source_type": source_type,
                    "text_summary": {
                        "preview": preview,
                        "line_count": len(lines),
                        "non_empty_line_count": len(non_empty_lines),
                        "headings": headings[:12],
                    },
                }
            },
            "summary": {
                "has_json": False,
                "has_text": bool(text_value),
                "line_count": len(lines),
                "non_empty_line_count": len(non_empty_lines),
                "headings": headings[:12],
            },
        }


import_parse_service = ImportParseService()
