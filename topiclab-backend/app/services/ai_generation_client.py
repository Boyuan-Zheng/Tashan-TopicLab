"""Shared AI-generation client with optional multi-key rotation."""

from __future__ import annotations

import asyncio
import os
import threading
import time
from dataclasses import dataclass

import httpx

from app.services.http_client import get_shared_async_client

_RATE_LIMIT_COOLDOWN = int(os.getenv("LLM_RATE_LIMIT_COOLDOWN_SECONDS", "60"))


def _required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"{name} is not set")
    return value


def _load_api_keys() -> list[str]:
    multi = os.getenv("AI_GENERATION_API_KEYS", "").strip()
    if multi:
        keys = [item.strip() for item in multi.split(",") if item.strip()]
        if keys:
            return keys
    single = os.getenv("AI_GENERATION_API_KEY", "").strip()
    return [single] if single else []


class _KeyPool:
    """Thread-safe key pool with round-robin rotation and 429 cooldowns."""

    def __init__(self, keys: list[str]) -> None:
        self._keys = keys
        self._idx = 0
        self._limited: dict[int, float] = {}
        self._lock = threading.Lock()

    def reload(self) -> None:
        with self._lock:
            self._keys = _load_api_keys()
            self._idx = 0
            self._limited = {}

    def reserve(self) -> tuple[str | None, float]:
        """Return the next usable key and optional wait seconds."""
        with self._lock:
            if not self._keys:
                return None, 0.0

            now = time.monotonic()
            total = len(self._keys)
            for _ in range(total):
                idx = self._idx % total
                self._idx += 1
                limited_until = self._limited.get(idx)
                if limited_until is None or now >= limited_until:
                    self._limited.pop(idx, None)
                    return self._keys[idx], 0.0

            best_idx = min(self._limited, key=lambda item: self._limited[item])
            wait_seconds = max(0.0, self._limited[best_idx] - now)
            return self._keys[best_idx], wait_seconds

    def mark_rate_limited(self, key: str) -> None:
        with self._lock:
            try:
                idx = self._keys.index(key)
            except ValueError:
                return
            self._limited[idx] = time.monotonic() + _RATE_LIMIT_COOLDOWN

    @property
    def size(self) -> int:
        return len(self._keys)


_pool = _KeyPool(_load_api_keys())


@dataclass
class AIGenerationRuntimeConfig:
    base_url: str
    model: str
    key_count: int
    using_multi_key_rotation: bool


def get_ai_generation_runtime_config(*, model: str | None = None) -> AIGenerationRuntimeConfig:
    base_url = _required_env("AI_GENERATION_BASE_URL")
    selected_model = (model or _required_env("AI_GENERATION_MODEL")).strip()
    _pool.reload()
    return AIGenerationRuntimeConfig(
        base_url=base_url,
        model=selected_model,
        key_count=_pool.size,
        using_multi_key_rotation=_pool.size > 1,
    )


async def post_ai_generation_chat(
    payload: dict,
    *,
    model: str | None = None,
    timeout: float = 60.0,
    client_name: str = "ai-generation",
) -> tuple[dict, str]:
    """Call OpenAI-compatible chat completions with optional key rotation."""
    runtime = get_ai_generation_runtime_config(model=model)
    if runtime.key_count < 1:
        raise ValueError("AI_GENERATION_API_KEY or AI_GENERATION_API_KEYS is not set")

    client = get_shared_async_client(client_name)
    attempts = runtime.key_count if runtime.using_multi_key_rotation else 1
    last_error: Exception | None = None

    for _ in range(attempts):
        api_key, wait_seconds = _pool.reserve()
        if not api_key:
            raise ValueError("AI_GENERATION_API_KEY or AI_GENERATION_API_KEYS is not set")
        if wait_seconds > 0:
            await asyncio.sleep(wait_seconds)

        response = await client.post(
            f"{runtime.base_url.rstrip('/')}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={**payload, "model": runtime.model},
            timeout=timeout,
        )

        if response.status_code == 429 and runtime.using_multi_key_rotation:
            _pool.mark_rate_limited(api_key)
            last_error = httpx.HTTPStatusError(
                "Rate limit from AI generation upstream",
                request=response.request,
                response=response,
            )
            continue

        response.raise_for_status()
        return response.json(), runtime.model

    assert last_error is not None
    raise last_error


def post_ai_generation_chat_sync(
    payload: dict,
    *,
    model: str | None = None,
    timeout: float = 60.0,
) -> tuple[dict, str]:
    """Sync variant for runtimes that cannot safely reuse the async shared client."""
    runtime = get_ai_generation_runtime_config(model=model)
    if runtime.key_count < 1:
        raise ValueError("AI_GENERATION_API_KEY or AI_GENERATION_API_KEYS is not set")

    attempts = runtime.key_count if runtime.using_multi_key_rotation else 1
    last_error: Exception | None = None

    for _ in range(attempts):
        api_key, wait_seconds = _pool.reserve()
        if not api_key:
            raise ValueError("AI_GENERATION_API_KEY or AI_GENERATION_API_KEYS is not set")
        if wait_seconds > 0:
            time.sleep(wait_seconds)

        with httpx.Client(timeout=timeout) as client:
            response = client.post(
                f"{runtime.base_url.rstrip('/')}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={**payload, "model": runtime.model},
            )

        if response.status_code == 429 and runtime.using_multi_key_rotation:
            _pool.mark_rate_limited(api_key)
            last_error = httpx.HTTPStatusError(
                "Rate limit from AI generation upstream",
                request=response.request,
                response=response,
            )
            continue

        response.raise_for_status()
        return response.json(), runtime.model

    assert last_error is not None
    raise last_error
