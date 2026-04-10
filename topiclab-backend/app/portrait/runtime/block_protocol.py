"""Helpers for the portrait-domain block/UI response contract."""

from __future__ import annotations

from typing import Any

INTERACTIVE_BLOCK_TYPES = {"choice", "text_input", "rating"}


def text_block(content: str) -> dict[str, Any]:
    return {"type": "text", "content": content}


def choice_block(
    *,
    block_id: str,
    question: str,
    options: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "type": "choice",
        "id": block_id,
        "question": question,
        "options": options,
    }


def text_input_block(
    *,
    block_id: str,
    question: str,
    placeholder: str = "",
    multiline: bool = True,
) -> dict[str, Any]:
    return {
        "type": "text_input",
        "id": block_id,
        "question": question,
        "placeholder": placeholder,
        "multiline": multiline,
    }


def rating_block(
    *,
    block_id: str,
    question: str,
    min_val: int,
    max_val: int,
    min_label: str = "",
    max_label: str = "",
) -> dict[str, Any]:
    return {
        "type": "rating",
        "id": block_id,
        "question": question,
        "min_val": min_val,
        "max_val": max_val,
        "min_label": min_label,
        "max_label": max_label,
    }


def chart_block(
    *,
    chart_type: str,
    title: str,
    dimensions: list[str],
    values: list[int | float],
    max_value: int | float,
) -> dict[str, Any]:
    return {
        "type": "chart",
        "chart_type": chart_type,
        "title": title,
        "dimensions": dimensions,
        "values": values,
        "max_value": max_value,
    }


def copyable_block(*, title: str, content: str) -> dict[str, Any]:
    return {
        "type": "copyable",
        "title": title,
        "content": content,
    }


def actions_block(*, message: str, buttons: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "type": "actions",
        "message": message,
        "buttons": buttons,
    }


def first_interactive_block(blocks: list[dict[str, Any]] | None) -> dict[str, Any] | None:
    for block in blocks or []:
        if block.get("type") in INTERACTIVE_BLOCK_TYPES:
            return block
    return None
