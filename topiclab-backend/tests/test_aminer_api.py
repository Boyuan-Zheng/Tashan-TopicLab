"""Tests for AMiner proxy API: 503 when unconfigured, proxy success with mock upstream, concurrency."""

import asyncio
import time
from unittest.mock import MagicMock

import httpx
import pytest

import app.api.aminer as aminer_module


def _fake_aminer_response(json_data: dict | None = None, status_code: int = 200):
    data = json_data or {"success": True, "data": [], "total": 0}
    resp = MagicMock()
    resp.status_code = status_code
    resp.text = "ok"
    resp.raise_for_status = MagicMock()
    resp.json = MagicMock(return_value=data)
    return resp


class FakeAminerClient:
    """Mock upstream AMiner: get/post return success JSON; optional delay for concurrency test."""

    def __init__(self, delay: float = 0.0):
        self.delay = delay

    async def get(self, *args, **kwargs):
        if self.delay > 0:
            await asyncio.sleep(self.delay)
        return _fake_aminer_response()

    async def post(self, *args, **kwargs):
        if self.delay > 0:
            await asyncio.sleep(self.delay)
        return _fake_aminer_response()


@pytest.fixture
def aminer_client(monkeypatch):
    """TestClient with AMiner proxy; upstream mocked, no real AMiner call."""
    monkeypatch.setenv("AMINER_API_KEY", "test-key")
    monkeypatch.setattr(
        aminer_module,
        "get_shared_async_client",
        lambda name: FakeAminerClient(),
    )
    from main import app
    from fastapi.testclient import TestClient
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


def test_aminer_proxy_503_when_key_missing(monkeypatch):
    """When proxy has no key (or forced 503), client receives 503."""
    from fastapi import HTTPException

    def raise_503():
        raise HTTPException(status_code=503, detail="AMiner 代理未配置：请设置 AMINER_API_KEY")

    monkeypatch.setattr(aminer_module, "_get_aminer_token", raise_503)
    import main as main_module
    from fastapi.testclient import TestClient
    with TestClient(main_module.app) as client:
        r = client.get("/aminer/paper/search?title=test&page=0&size=10")
    assert r.status_code == 503, f"Expected 503, got {r.status_code}: {r.text}"
    detail = (r.json().get("detail") if r.headers.get("content-type", "").startswith("application/json") else None) or r.text
    assert "AMINER" in detail or "AMINER_API_KEY" in detail


def test_aminer_paper_search_proxy(aminer_client):
    r = aminer_client.get("/aminer/paper/search?title=Attention&page=0&size=5")
    assert r.status_code == 200
    body = r.json()
    assert "data" in body or "total" in body or "success" in body


def test_aminer_person_search_proxy(aminer_client):
    r = aminer_client.post(
        "/aminer/person/search",
        json={"name": "王曙", "size": 5},
    )
    assert r.status_code == 200
    body = r.json()
    assert "data" in body or "total" in body or "success" in body


def test_aminer_patent_search_proxy(aminer_client):
    r = aminer_client.post(
        "/aminer/patent/search",
        json={"query": "Si02", "page": 0, "size": 10},
    )
    assert r.status_code == 200


def test_aminer_organization_search_proxy(aminer_client):
    r = aminer_client.post(
        "/aminer/organization/search",
        json={"orgs": ["清华大学"]},
    )
    assert r.status_code == 200


def test_aminer_venue_search_proxy(aminer_client):
    r = aminer_client.post(
        "/aminer/venue/search",
        json={"name": "The Lancet"},
    )
    assert r.status_code == 200


def test_aminer_paper_info_proxy(aminer_client):
    r = aminer_client.post(
        "/aminer/paper/info",
        json={"ids": ["5ce2c5a5ced107d4c61c839b"]},
    )
    assert r.status_code == 200


def test_aminer_patent_info_proxy(aminer_client):
    r = aminer_client.get(
        "/aminer/patent/info?id=63370927667297566c3fb14f"
    )
    assert r.status_code == 200


def test_aminer_api_v1_prefix(aminer_client):
    r = aminer_client.get(
        "/api/v1/aminer/paper/search?title=test&page=0&size=10"
    )
    assert r.status_code == 200


def test_aminer_proxy_upstream_4xx_propagates(monkeypatch):
    monkeypatch.setenv("AMINER_API_KEY", "test-key")

    class Client404:
        async def get(self, *a, **k):
            raise httpx.HTTPStatusError("404", request=MagicMock(), response=MagicMock(status_code=404, text="Not Found"))
        async def post(self, *a, **k):
            raise httpx.HTTPStatusError("404", request=MagicMock(), response=MagicMock(status_code=404, text="Not Found"))

    monkeypatch.setattr(aminer_module, "get_shared_async_client", lambda _: Client404())
    from main import app
    from fastapi.testclient import TestClient
    with TestClient(app) as client:
        r = client.get("/aminer/paper/search?title=x&page=0&size=10")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_aminer_proxy_concurrency(monkeypatch):
    """Fire N concurrent requests; mock upstream has delay. Assert all 200 and elapsed << N*delay (parallel)."""
    monkeypatch.setenv("AMINER_API_KEY", "test-key")
    delay_per_request = 0.05
    concurrency = 20
    monkeypatch.setattr(
        aminer_module,
        "get_shared_async_client",
        lambda name: FakeAminerClient(delay=delay_per_request),
    )
    from main import app

    # ASGITransport requires full URL when using client.get(url)
    base = "http://testserver"
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        timeout=30.0,
        base_url=base,
    ) as client:
        t0 = time.perf_counter()
        tasks = [
            client.get("/aminer/paper/search", params={"title": "test", "page": 0, "size": 10})
            for _ in range(concurrency)
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        elapsed = time.perf_counter() - t0

    errors = [r for r in results if isinstance(r, Exception)]
    if errors:
        raise AssertionError(f"Concurrency test had {len(errors)} errors; first: {errors[0]}")
    statuses = [r.status_code for r in results]
    assert all(s == 200 for s in statuses), f"Not all 200: {statuses}"

    # If fully serial: ~ concurrency * delay_per_request; if parallel: ~ delay_per_request (plus overhead)
    serial_time = concurrency * delay_per_request
    assert elapsed < serial_time * 0.6, (
        f"Concurrent requests took {elapsed:.3f}s; if serial would be ~{serial_time:.2f}s. "
        "Expected parallel handling."
    )
    # Effective parallelism: (concurrency * single_request_delay) / elapsed
    effective_parallel = (concurrency * delay_per_request) / elapsed if elapsed > 0 else 0
    # Serial would be ~1s; we expect << 1s → proxy handles concurrency (httpx shared client + async)
    print(f"\nAminer proxy concurrency: {concurrency} requests in {elapsed:.3f}s (~{effective_parallel:.1f}x parallel)")
