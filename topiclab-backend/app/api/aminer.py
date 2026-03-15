"""Proxy for AMiner 开放平台限免 API. Uses AMINER_API_KEY from env."""

from __future__ import annotations

import os
from typing import Any

import httpx
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.http_client import get_shared_async_client

AMINER_BASE = "https://datacenter.aminer.cn/gateway/open_platform"
TIMEOUT = 20.0


def _get_aminer_token() -> str:
    token = (os.getenv("AMINER_API_KEY") or "").strip()
    if not token:
        raise HTTPException(
            status_code=503,
            detail="AMiner 代理未配置：请设置 AMINER_API_KEY",
        )
    return token


def _aminer_headers() -> dict[str, str]:
    return {
        "Authorization": _get_aminer_token(),
        "Content-Type": "application/json;charset=utf-8",
    }


router = APIRouter()


# ----- 数据查询类 -----


@router.get("/paper/search")
async def aminer_paper_search(
    title: str = Query(..., description="论文标题"),
    page: int = Query(0, ge=0, description="页码，从 0 开始"),
    size: int = Query(10, ge=1, le=20, description="每页条数，最大 20"),
) -> dict[str, Any]:
    """根据论文标题搜索论文 ID、标题、DOI。限免。"""
    url = f"{AMINER_BASE}/api/paper/search"
    params = {"title": title, "page": page, "size": size}
    headers = {"Authorization": _get_aminer_token()}
    try:
        client = get_shared_async_client("aminer")
        resp = await client.get(url, params=params, headers=headers, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=exc.response.status_code,
            detail=exc.response.text or "AMiner 论文搜索请求失败",
        ) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="无法连接 AMiner 服务") from exc


class ScholarSearchBody(BaseModel):
    name: str | None = Field(None, description="学者姓名")
    offset: int = Field(0, description="起始位置")
    org: str | None = Field(None, description="机构名")
    size: int = Field(10, ge=1, le=10, description="条数，最大 10")
    org_id: list[str] | None = Field(None, description="机构实体 ID 数组")


@router.post("/person/search")
async def aminer_person_search(body: ScholarSearchBody) -> dict[str, Any]:
    """根据学者名称搜索学者 ID、姓名、机构。限免。"""
    url = f"{AMINER_BASE}/api/person/search"
    payload = body.model_dump(exclude_none=True)
    try:
        client = get_shared_async_client("aminer")
        resp = await client.post(
            url, json=payload, headers=_aminer_headers(), timeout=TIMEOUT
        )
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=exc.response.status_code,
            detail=exc.response.text or "AMiner 学者搜索请求失败",
        ) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="无法连接 AMiner 服务") from exc


class PatentSearchBody(BaseModel):
    query: str = Field(..., description="查询字段，如专利标题、关键词等")
    page: int = Field(0, description="页数")
    size: int = Field(20, ge=1, description="每页条数")


@router.post("/patent/search")
async def aminer_patent_search(body: PatentSearchBody) -> dict[str, Any]:
    """根据专利名称搜索专利 ID、标题、专利号。限免。"""
    url = f"{AMINER_BASE}/api/patent/search"
    payload = body.model_dump()
    try:
        client = get_shared_async_client("aminer")
        resp = await client.post(
            url, json=payload, headers=_aminer_headers(), timeout=TIMEOUT
        )
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=exc.response.status_code,
            detail=exc.response.text or "AMiner 专利搜索请求失败",
        ) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="无法连接 AMiner 服务") from exc


class OrganizationSearchBody(BaseModel):
    orgs: list[str] | None = Field(None, description="机构名称列表")


@router.post("/organization/search")
async def aminer_organization_search(body: OrganizationSearchBody) -> dict[str, Any]:
    """根据名称关键词搜索机构 ID、名称。限免。"""
    url = f"{AMINER_BASE}/api/organization/search"
    payload = body.model_dump(exclude_none=True) or {}
    try:
        client = get_shared_async_client("aminer")
        resp = await client.post(
            url, json=payload, headers=_aminer_headers(), timeout=TIMEOUT
        )
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=exc.response.status_code,
            detail=exc.response.text or "AMiner 机构搜索请求失败",
        ) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="无法连接 AMiner 服务") from exc


class VenueSearchBody(BaseModel):
    name: str | None = Field(None, description="期刊名")


@router.post("/venue/search")
async def aminer_venue_search(body: VenueSearchBody) -> dict[str, Any]:
    """根据期刊名称搜索期刊 ID、标准名称。限免。"""
    url = f"{AMINER_BASE}/api/venue/search"
    payload = body.model_dump(exclude_none=True) or {}
    try:
        client = get_shared_async_client("aminer")
        resp = await client.post(
            url, json=payload, headers=_aminer_headers(), timeout=TIMEOUT
        )
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=exc.response.status_code,
            detail=exc.response.text or "AMiner 期刊搜索请求失败",
        ) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="无法连接 AMiner 服务") from exc


# ----- 数据获取类 -----


class PaperInfoBody(BaseModel):
    ids: list[str] = Field(..., min_length=1, max_length=100, description="论文 id 列表，最多 100")


@router.post("/paper/info")
async def aminer_paper_info(body: PaperInfoBody) -> dict[str, Any]:
    """根据论文 ID 列表获取标题、卷号、期刊、作者。限免。"""
    url = f"{AMINER_BASE}/api/paper/info"
    payload = body.model_dump()
    try:
        client = get_shared_async_client("aminer")
        resp = await client.post(
            url, json=payload, headers=_aminer_headers(), timeout=TIMEOUT
        )
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=exc.response.status_code,
            detail=exc.response.text or "AMiner 论文信息请求失败",
        ) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="无法连接 AMiner 服务") from exc


@router.get("/patent/info")
async def aminer_patent_info(
    id: str = Query(..., description="专利 ID"),
) -> dict[str, Any]:
    """根据专利 ID 获取标题、专利号、发明人、国家等。限免。"""
    url = f"{AMINER_BASE}/api/patent/info"
    params = {"id": id}
    headers = {"Authorization": _get_aminer_token()}
    try:
        client = get_shared_async_client("aminer")
        resp = await client.get(url, params=params, headers=headers, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=exc.response.status_code,
            detail=exc.response.text or "AMiner 专利信息请求失败",
        ) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="无法连接 AMiner 服务") from exc
