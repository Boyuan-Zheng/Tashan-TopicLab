"""Compatibility shim that re-exports the portrait-domain scales scoring."""

from app.portrait.services.scales_scoring import (
    SCORING_VERSION,
    build_result_summary,
    calculate_derived_scores,
    calculate_dimension_scores,
)

__all__ = [
    "SCORING_VERSION",
    "build_result_summary",
    "calculate_derived_scores",
    "calculate_dimension_scores",
]
