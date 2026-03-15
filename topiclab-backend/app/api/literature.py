"""Proxy for IC literature API (学术). Uses same INFORMATION_COLLECTION_BASE_URL as source-feed."""

from __future__ import annotations

import os
from typing import Any

import httpx
from fastapi import APIRouter, HTTPException, Query

from app.services.http_client import get_shared_async_client


def _get_ic_base_url() -> str:
    return os.getenv("INFORMATION_COLLECTION_BASE_URL", "http://ic.nexus.tashan.ac.cn").rstrip("/")


def _get_literature_token() -> str | None:
    raw = (os.getenv("LITERATURE_SHARED_TOKEN") or "").strip()
    return raw or None


router = APIRouter()


@router.get("/recent")
async def get_literature_recent(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    category: str | None = Query(default=None),
    tag: str | None = Query(default=None),
    published_day_from: str | None = Query(default=None),
    published_day_to: str | None = Query(default=None),
) -> dict[str, Any]:
    """Proxy GET to IC /api/v1/literature/recent (学术 recent 列表)."""
    base = _get_ic_base_url()
    url = f"{base}/api/v1/literature/recent"
    params: dict[str, Any] = {"limit": limit, "offset": offset}
    if category:
        params["category"] = category
    if tag:
        params["tag"] = tag
    if published_day_from:
        params["published_day_from"] = published_day_from
    if published_day_to:
        params["published_day_to"] = published_day_to
    headers: dict[str, str] = {}
    token = _get_literature_token()
    if token:
        headers["x-ingest-token"] = token
    try:
        client = get_shared_async_client("literature")
        response = await client.get(url, params=params, headers=headers, timeout=15.0)
        response.raise_for_status()
        payload = response.json()
        # IC 返回 { ok, data: { list, limit, offset } }，对前端只返回 data 内容
        if isinstance(payload.get("data"), dict):
            return payload["data"]
        return payload
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail="上游学术服务请求失败") from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="无法连接学术服务") from exc
