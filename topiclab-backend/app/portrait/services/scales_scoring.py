"""Canonical scale scoring for the portrait-domain scale runtime."""

from __future__ import annotations

from typing import Any


SCORING_VERSION = "2026-04-10.v1"


def _question_map(definition: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {question["id"]: question for question in definition["questions"]}


def calculate_dimension_scores(definition: dict[str, Any], answers: dict[str, float]) -> dict[str, float]:
    question_by_id = _question_map(definition)
    max_val = float(definition["max_val"])
    scoring_mode = str(definition["scoring_mode"])
    scores: dict[str, float] = {}

    for dimension in definition["dimensions"]:
        values: list[float] = []
        for question_id in dimension["question_ids"]:
            if question_id not in answers:
                continue
            raw = float(answers[question_id])
            question = question_by_id[question_id]
            value = (max_val + 1 - raw) if question.get("reverse") else raw
            values.append(float(value))

        if not values:
            scores[dimension["id"]] = 0.0
            continue

        if scoring_mode == "average":
            scores[dimension["id"]] = round(sum(values) / len(values), 2)
        else:
            scores[dimension["id"]] = float(sum(values))

    return scores


def calculate_derived_scores(scale_id: str, dimension_scores: dict[str, float]) -> dict[str, Any]:
    if scale_id == "rcss":
        integration = float(dimension_scores.get("integration", 0.0))
        depth = float(dimension_scores.get("depth", 0.0))
        csi = integration - depth
        profile_type = "平衡型"
        if csi >= 17:
            profile_type = "强整合型"
        elif csi >= 8:
            profile_type = "倾向整合型"
        elif csi <= -17:
            profile_type = "强深度型"
        elif csi <= -8:
            profile_type = "倾向深度型"
        return {"I": integration, "D": depth, "CSI": csi, "type": profile_type}

    if scale_id == "ams":
        know = float(dimension_scores.get("know", 0.0))
        accomplishment = float(dimension_scores.get("accomplishment", 0.0))
        stimulation = float(dimension_scores.get("stimulation", 0.0))
        identified = float(dimension_scores.get("identified", 0.0))
        introjected = float(dimension_scores.get("introjected", 0.0))
        external = float(dimension_scores.get("external", 0.0))
        amotivation = float(dimension_scores.get("amotivation", 0.0))
        rai = (
            3 * know
            + 3 * accomplishment
            + 3 * stimulation
            + 2 * identified
            - introjected
            - 2 * external
            - 3 * amotivation
        )
        return {
            "intrinsicTotal": round(know + accomplishment + stimulation, 2),
            "extrinsicTotal": round(identified + introjected + external, 2),
            "RAI": round(rai, 2),
        }

    return {}


def build_result_summary(scale_id: str, dimension_scores: dict[str, float], derived_scores: dict[str, Any]) -> dict[str, Any]:
    if scale_id == "rcss":
        return {
            "type": derived_scores.get("type"),
            "CSI": derived_scores.get("CSI"),
            "dominant_dimension": "integration"
            if float(dimension_scores.get("integration", 0.0)) >= float(dimension_scores.get("depth", 0.0))
            else "depth",
        }

    if scale_id == "ams":
        return {
            "RAI": derived_scores.get("RAI"),
            "intrinsicTotal": derived_scores.get("intrinsicTotal"),
            "extrinsicTotal": derived_scores.get("extrinsicTotal"),
            "dominant_dimension": max(dimension_scores, key=dimension_scores.get) if dimension_scores else None,
        }

    if scale_id == "mini-ipip":
        return {
            "dominant_dimension": max(dimension_scores, key=dimension_scores.get) if dimension_scores else None,
        }

    return {}
