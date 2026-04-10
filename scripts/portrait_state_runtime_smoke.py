#!/usr/bin/env python3
"""Standalone local smoke for the portrait state runtime."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import types
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import text


ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = ROOT / "topiclab-backend"


def _install_test_shims() -> None:
    fake_moderation = types.ModuleType("app.services.content_moderation")

    class ModerationDecision:
        def __init__(self, approved: bool = True, reason: str = "", suggestion: str = "", category: str = "normal"):
            self.approved = approved
            self.reason = reason
            self.suggestion = suggestion
            self.category = category

    async def moderate_post_content(content: str, *, scenario: str):
        _ = content, scenario
        return ModerationDecision()

    fake_moderation.ModerationDecision = ModerationDecision
    fake_moderation.moderate_post_content = moderate_post_content
    sys.modules["app.services.content_moderation"] = fake_moderation

    fake_oss = types.ModuleType("app.services.oss_upload")

    def get_signed_media_url(*args, **kwargs):
        _ = args, kwargs
        return "https://example.com/fake-media"

    async def upload_comment_media_to_oss(*args, **kwargs):
        _ = args, kwargs
        return {
            "url": "https://example.com/fake-media",
            "markdown": "![fake](https://example.com/fake-media)",
            "object_key": "fake-key",
            "content_type": "image/png",
            "media_type": "image",
            "width": 1,
            "height": 1,
            "size_bytes": 1,
        }

    fake_oss.get_signed_media_url = get_signed_media_url
    fake_oss.upload_comment_media_to_oss = upload_comment_media_to_oss
    sys.modules["app.services.oss_upload"] = fake_oss


def _register_and_login(client: TestClient) -> dict:
    from app.storage.database.postgres_client import get_db_session

    code = "123456"
    with get_db_session() as session:
        session.execute(
            text(
                """
                INSERT INTO verification_codes (phone, code, type, expires_at)
                VALUES (:phone, :code, 'register', :expires_at)
                """
            ),
            {
                "phone": "13800064001",
                "code": code,
                "expires_at": datetime.now(timezone.utc) + timedelta(minutes=5),
            },
        )

    response = client.post(
        "/auth/register",
        json={
            "phone": "13800064001",
            "code": code,
            "password": "password123",
            "username": "portrait-state-smoke",
        },
    )
    response.raise_for_status()
    return response.json()


def main() -> int:
    os.environ["TOPICLAB_TESTING"] = "1"
    database_path = Path(tempfile.mkdtemp(prefix="portrait-state-runtime-smoke-")) / "portrait_state_runtime.sqlite3"
    os.environ["DATABASE_URL"] = f"sqlite:///{database_path}"

    sys.path.insert(0, str(BACKEND_ROOT))
    _install_test_shims()

    import app.storage.database.postgres_client as postgres_client
    import app.api.auth as auth_router
    import app.api.dialogue as dialogue_router
    import app.api.scales as scales_router
    import app.api.portrait_state as portrait_state_router
    from app.portrait.services.dialogue_generation_service import dialogue_generation_service

    async def fake_generate_assistant_reply(messages, derived_state, *, model=None):
        _ = messages, derived_state
        return {
            "content": "好的，我们先从你的研究方向和工作风格开始。",
            "model": model or "fake-dialogue-model",
        }

    dialogue_generation_service.generate_assistant_reply = fake_generate_assistant_reply

    postgres_client.reset_db_state()
    postgres_client.init_auth_tables()

    app = FastAPI()
    app.include_router(auth_router.router, prefix="/auth", tags=["auth"])
    app.include_router(dialogue_router.router, prefix="/api/v1", tags=["portrait-dialogue-v1"])
    app.include_router(scales_router.router, prefix="/api/v1", tags=["scales-v1"])
    app.include_router(portrait_state_router.router, prefix="/api/v1", tags=["portrait-state-v1"])

    with TestClient(app) as client:
        auth = _register_and_login(client)
        headers = {"Authorization": f"Bearer {auth['token']}"}

        dialogue_start = client.post(
            "/api/v1/portrait/dialogue/sessions",
            headers=headers,
            json={"actor_type": "internal", "actor_id": "portrait-state-smoke"},
        ).json()
        dialogue_session_id = dialogue_start["session"]["session_id"]
        client.post(
            f"/api/v1/portrait/dialogue/sessions/{dialogue_session_id}/messages",
            headers=headers,
            json={"role": "user", "content_text": "我想先整理自己的研究方向和写作风格。", "source": "cli"},
        ).raise_for_status()
        dialogue_update = client.post(
            "/api/v1/portrait/state/updates",
            headers=headers,
            json={"source_type": "dialogue_session", "source_id": dialogue_session_id},
        ).json()

        scale_start = client.post(
            "/api/v1/scales/sessions",
            headers=headers,
            json={"scale_id": "rcss", "actor_type": "internal", "actor_id": "portrait-state-smoke"},
        ).json()
        scale_session_id = scale_start["session"]["session_id"]
        client.post(
            f"/api/v1/scales/sessions/{scale_session_id}/answer-batch",
            headers=headers,
            json={
                "answers": {
                    "A1": 7,
                    "A2": 7,
                    "A3": 7,
                    "A4": 7,
                    "B1": 1,
                    "B2": 1,
                    "B3": 1,
                    "B4": 1,
                }
            },
        ).raise_for_status()
        client.post(f"/api/v1/scales/sessions/{scale_session_id}/finalize", headers=headers).raise_for_status()
        scale_update = client.post(
            "/api/v1/portrait/state/updates",
            headers=headers,
            json={"source_type": "scale_session", "source_id": scale_session_id},
        ).json()

        current_payload = client.get("/api/v1/portrait/state/current", headers=headers).json()
        versions_payload = client.get("/api/v1/portrait/state/versions", headers=headers).json()
        observations_payload = client.get("/api/v1/portrait/state/observations", headers=headers).json()

    print(
        json.dumps(
            {
                "dialogue_update": {
                    "update_id": dialogue_update["update"]["update_id"],
                    "session_id": dialogue_session_id,
                },
                "scale_update": {
                    "update_id": scale_update["update"]["update_id"],
                    "session_id": scale_session_id,
                },
                "current_state": current_payload["current_state"],
                "version_count": current_payload["version_count"],
                "update_count": current_payload["update_count"],
                "versions": versions_payload["versions"],
                "observations": observations_payload["observations"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
