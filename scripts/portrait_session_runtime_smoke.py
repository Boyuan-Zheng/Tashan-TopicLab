#!/usr/bin/env python3
"""Standalone local smoke for the unified portrait session runtime."""

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
                "phone": "13800073001",
                "code": code,
                "expires_at": datetime.now(timezone.utc) + timedelta(minutes=5),
            },
        )

    response = client.post(
        "/auth/register",
        json={
            "phone": "13800073001",
            "code": code,
            "password": "password123",
            "username": "portrait-session-smoke",
        },
    )
    response.raise_for_status()
    return response.json()


def main() -> int:
    os.environ["TOPICLAB_TESTING"] = "1"
    database_path = Path(tempfile.mkdtemp(prefix="portrait-session-runtime-smoke-")) / "portrait_session_runtime.sqlite3"
    os.environ["DATABASE_URL"] = f"sqlite:///{database_path}"

    sys.path.insert(0, str(BACKEND_ROOT))
    _install_test_shims()

    import app.storage.database.postgres_client as postgres_client
    import app.api.auth as auth_router
    import app.api.portrait_session as portrait_session_router
    from app.portrait.services.dialogue_generation_service import dialogue_generation_service

    async def fake_generate_assistant_reply(messages, derived_state, *, model=None):
        _ = messages, derived_state
        return {
            "content": "好的，我已经了解了你的主线。请继续补充你最擅长的工作方式。",
            "model": model or "fake-dialogue-model",
        }

    dialogue_generation_service.generate_assistant_reply = fake_generate_assistant_reply

    postgres_client.reset_db_state()
    postgres_client.init_auth_tables()

    app = FastAPI()
    app.include_router(auth_router.router, prefix="/auth", tags=["auth"])
    app.include_router(portrait_session_router.router, prefix="/api/v1", tags=["portrait-session-v1"])

    with TestClient(app) as client:
        auth = _register_and_login(client)
        headers = {"Authorization": f"Bearer {auth['token']}"}

        start_payload = client.post(
            "/api/v1/portrait/sessions",
            headers=headers,
            json={"actor_type": "internal", "actor_id": "portrait-session-smoke"},
        ).json()
        session_id = start_payload["session"]["session_id"]

        respond_payload = client.post(
            f"/api/v1/portrait/sessions/{session_id}/respond",
            headers=headers,
            json={"text": "我主要在做 AI agent、科研工具开发和学术写作。"},
        ).json()

        scale_start_payload = client.post(
            f"/api/v1/portrait/sessions/{session_id}/respond",
            headers=headers,
            json={"choice": "scale:rcss"},
        ).json()

        scale_latest_payload = scale_start_payload
        for _ in range(8):
            scale_latest_payload = client.post(
                f"/api/v1/portrait/sessions/{session_id}/respond",
                headers=headers,
                json={"choice": 7},
            ).json()

        handoff_payload = client.post(
            f"/api/v1/portrait/sessions/{session_id}/respond",
            headers=headers,
            json={"choice": "prompt_handoff"},
        ).json()

        import_payload = client.post(
            f"/api/v1/portrait/sessions/{session_id}/respond",
            headers=headers,
            json={
                "external_text": "# Summary\n你在科研工具和 AI agent 上有长期积累。\n# Open Questions\n还需要确认组织协作风格。",
            },
        ).json()

        result_payload = client.get(
            f"/api/v1/portrait/sessions/{session_id}/result",
            headers=headers,
        ).json()

        confirm_payload = client.post(
            f"/api/v1/portrait/sessions/{session_id}/respond",
            headers=headers,
            json={"confirm": True},
        ).json()

    print(
        json.dumps(
            {
                "session": {
                    "session_id": session_id,
                    "start_stage": start_payload["stage"],
                    "scale_stage_after_start": scale_start_payload["stage"],
                    "stage_after_scale_finalize": scale_latest_payload["stage"],
                    "stage_after_import": import_payload["stage"],
                    "final_status": confirm_payload["status"],
                },
                "runtime_refs": respond_payload["runtime_refs"],
                "last_response": respond_payload["last_response"],
                "scale_last_response": scale_latest_payload["last_response"],
                "handoff": handoff_payload["last_response"]["handoff"],
                "import_result": import_payload["last_response"]["import_result"],
                "current_state": result_payload["result"]["current_state"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
