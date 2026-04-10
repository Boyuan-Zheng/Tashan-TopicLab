from __future__ import annotations

import asyncio

import httpx


class _FakeResponse:
    def __init__(self, status_code: int, payload: dict | None = None):
        self.status_code = status_code
        self._payload = payload or {}
        self.request = httpx.Request("POST", "https://example.com/chat/completions")

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                f"upstream returned {self.status_code}",
                request=self.request,
                response=httpx.Response(self.status_code, request=self.request, json=self._payload),
            )


def test_post_ai_generation_chat_rotates_after_429(monkeypatch):
    from app.services import ai_generation_client as module

    monkeypatch.setenv("AI_GENERATION_BASE_URL", "https://example.com/v1")
    monkeypatch.setenv("AI_GENERATION_MODEL", "qwen3.5-plus")
    monkeypatch.setenv("AI_GENERATION_API_KEYS", "key-a,key-b,key-c")
    monkeypatch.delenv("AI_GENERATION_API_KEY", raising=False)

    class FakeClient:
        def __init__(self):
            self.calls: list[str] = []

        async def post(self, url, *, headers, json, timeout):
            _ = url, json, timeout
            self.calls.append(headers["Authorization"])
            if len(self.calls) == 1:
                return _FakeResponse(429, {"error": {"message": "rate limited"}})
            return _FakeResponse(
                200,
                {"choices": [{"message": {"content": "ok"}}]},
            )

    fake_client = FakeClient()
    monkeypatch.setattr(module, "get_shared_async_client", lambda _: fake_client)
    module._pool.reload()

    data, model = asyncio.run(
        module.post_ai_generation_chat({"messages": [{"role": "user", "content": "hi"}]})
    )

    assert model == "qwen3.5-plus"
    assert data["choices"][0]["message"]["content"] == "ok"
    assert fake_client.calls == ["Bearer key-a", "Bearer key-b"]


def test_post_ai_generation_chat_falls_back_to_single_key(monkeypatch):
    from app.services import ai_generation_client as module

    monkeypatch.setenv("AI_GENERATION_BASE_URL", "https://example.com/v1")
    monkeypatch.setenv("AI_GENERATION_MODEL", "qwen3.5-plus")
    monkeypatch.setenv("AI_GENERATION_API_KEY", "single-key")
    monkeypatch.delenv("AI_GENERATION_API_KEYS", raising=False)

    class FakeClient:
        async def post(self, url, *, headers, json, timeout):
            _ = url, json, timeout
            assert headers["Authorization"] == "Bearer single-key"
            return _FakeResponse(
                200,
                {"choices": [{"message": {"content": "ok"}}]},
            )

    monkeypatch.setattr(module, "get_shared_async_client", lambda _: FakeClient())
    module._pool.reload()

    data, model = asyncio.run(
        module.post_ai_generation_chat({"messages": [{"role": "user", "content": "hi"}]})
    )

    assert model == "qwen3.5-plus"
    assert data["choices"][0]["message"]["content"] == "ok"
