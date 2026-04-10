"""Load canonical scale definitions from the portrait domain asset workspace."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


class ScaleDefinitionsLoader:
    """Read runtime definitions from the shared scales-runtime asset directory."""

    def __init__(self) -> None:
        self._definitions_dir = Path(__file__).resolve().parents[4] / "scales-runtime" / "definitions"

    @property
    def definitions_dir(self) -> Path:
        return self._definitions_dir

    @lru_cache(maxsize=1)
    def load_registry(self) -> dict[str, Any]:
        registry_path = self._definitions_dir / "registry.json"
        return json.loads(registry_path.read_text(encoding="utf-8"))

    @lru_cache(maxsize=8)
    def load_definition_file(self, filename: str) -> dict[str, Any]:
        definition_path = self._definitions_dir / filename
        return json.loads(definition_path.read_text(encoding="utf-8"))

    def list_scales(self) -> dict[str, Any]:
        registry = self.load_registry()
        return {"registry_version": registry["registry_version"], "list": registry["scales"]}

    def get_scale_definition(self, scale_id: str) -> dict[str, Any] | None:
        registry = self.load_registry()
        for item in registry["scales"]:
            if item["scale_id"] == scale_id:
                return self.load_definition_file(item["file"])
        return None


definitions_loader = ScaleDefinitionsLoader()
