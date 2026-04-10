#!/usr/bin/env python3
"""Standalone local smoke for the portrait dialogue runtime.

This script creates a minimal FastAPI app with only the auth and dialogue
routers, registers a temporary user in a temporary SQLite database, then runs
one full dialogue-session skeleton loop:

- start session
- append user message
- append assistant message
- read transcript
- read derived state
- close session

It exists to validate the durable dialogue runtime skeleton before wiring later
generation behavior and CLI command surfaces into it.
"""

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
                "phone": "13800043001",
                "code": code,
                "expires_at": datetime.now(timezone.utc) + timedelta(minutes=5),
            },
        )

    response = client.post(
        "/auth/register",
        json={
            "phone": "13800043001",
            "code": code,
            "password": "password123",
            "username": "dialogue-smoke",
        },
    )
    response.raise_for_status()
    return response.json()


def main() -> int:
    os.environ["TOPICLAB_TESTING"] = "1"
    database_path = Path(tempfile.mkdtemp(prefix="dialogue-runtime-smoke-")) / "dialogue_runtime.sqlite3"
    os.environ["DATABASE_URL"] = f"sqlite:///{database_path}"

    sys.path.insert(0, str(BACKEND_ROOT))
    _install_test_shims()

    import app.storage.database.postgres_client as postgres_client
    import app.api.auth as auth_router
    import app.api.dialogue as dialogue_router
    from app.portrait.services.dialogue_generation_service import dialogue_generation_service

    async def fake_generate_assistant_reply(messages, derived_state, *, model=None):
        _ = messages, derived_state
        return {
            "content": "好的，我们先从你的研究主线开始。你最近最投入的研究问题是什么？",
            "model": model or "fake-dialogue-model",
        }

    dialogue_generation_service.generate_assistant_reply = fake_generate_assistant_reply

    postgres_client.reset_db_state()
    postgres_client.init_auth_tables()

    app = FastAPI()
    app.include_router(auth_router.router, prefix="/auth", tags=["auth"])
    app.include_router(dialogue_router.router, prefix="/api/v1", tags=["portrait-dialogue-v1"])

    with TestClient(app) as client:
        auth = _register_and_login(client)
        headers = {"Authorization": f"Bearer {auth['token']}"}

        start_payload = client.post(
            "/api/v1/portrait/dialogue/sessions",
            headers=headers,
            json={"actor_type": "internal", "actor_id": "dialogue-smoke"},
        ).json()
        session_id = start_payload["session"]["session_id"]

        user_payload = client.post(
            f"/api/v1/portrait/dialogue/sessions/{session_id}/messages",
            headers=headers,
            json={"role": "user", "content_text": "我想先整理我的研究兴趣和工作风格。", "source": "cli"},
        ).json()

        messages_payload = client.get(
            f"/api/v1/portrait/dialogue/sessions/{session_id}/messages",
            headers=headers,
        ).json()

        derived_payload = client.get(
            f"/api/v1/portrait/dialogue/sessions/{session_id}/derived-state",
            headers=headers,
        ).json()

        close_payload = client.post(
            f"/api/v1/portrait/dialogue/sessions/{session_id}/close",
            headers=headers,
        ).json()

    print(
        json.dumps(
            {
                "session": {
                    "session_id": session_id,
                    "start_status": start_payload["session"]["status"],
                    "close_status": close_payload["session"]["status"],
                },
                "accepted_messages": [
                    user_payload["accepted_message"],
                    user_payload["generated_message"],
                ],
                "progress": messages_payload["progress"],
                "derived_state": derived_payload["derived_state"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
