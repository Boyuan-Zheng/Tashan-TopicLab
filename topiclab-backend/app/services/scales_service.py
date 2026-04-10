"""Compatibility shim that re-exports the portrait-domain scales service."""

from app.portrait.services.scales_service import ScalesService, scales_service

__all__ = ["ScalesService", "scales_service"]
