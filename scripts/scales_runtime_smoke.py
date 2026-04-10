#!/usr/bin/env python3
"""Standalone local smoke for the scale runtime without topiclab-cli.

This script creates a minimal FastAPI app with only the auth and scales routers,
registers a temporary user in a temporary SQLite database, then runs one full
RCSS session:

- list scales
- read one definition
- start session
- answer all questions
- finalize
- fetch result

It exists to validate the standalone runtime closure before wiring the same
contract into TopicLab-CLI.
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
FIXTURE_PATH = ROOT / "scales-runtime" / "fixtures" / "rcss-strong-integration.json"


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
                "phone": "13800042001",
                "code": code,
                "expires_at": datetime.now(timezone.utc) + timedelta(minutes=5),
            },
        )

    response = client.post(
        "/auth/register",
        json={
            "phone": "13800042001",
            "code": code,
            "password": "password123",
            "username": "scale-smoke",
        },
    )
    response.raise_for_status()
    return response.json()


def main() -> int:
    os.environ["TOPICLAB_TESTING"] = "1"
    database_path = Path(tempfile.mkdtemp(prefix="scales-runtime-smoke-")) / "scales_runtime.sqlite3"
    os.environ["DATABASE_URL"] = f"sqlite:///{database_path}"

    sys.path.insert(0, str(BACKEND_ROOT))
    _install_test_shims()

    import app.storage.database.postgres_client as postgres_client
    import app.api.auth as auth_router
    import app.api.scales as scales_router

    postgres_client.reset_db_state()
    postgres_client.init_auth_tables()

    app = FastAPI()
    app.include_router(auth_router.router, prefix="/auth", tags=["auth"])
    app.include_router(scales_router.router, prefix="/api/v1", tags=["scales-v1"])

    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    with TestClient(app) as client:
        auth = _register_and_login(client)
        headers = {"Authorization": f"Bearer {auth['token']}"}

        list_payload = client.get("/api/v1/scales", headers=headers).json()
        definition_payload = client.get(f"/api/v1/scales/{fixture['scale_id']}", headers=headers).json()
        start_payload = client.post(
            "/api/v1/scales/sessions",
            headers=headers,
            json={"scale_id": fixture["scale_id"], "actor_type": "internal", "actor_id": "standalone-smoke"},
        ).json()
        session_id = start_payload["session"]["session_id"]
        batch_payload = client.post(
            f"/api/v1/scales/sessions/{session_id}/answer-batch",
            headers=headers,
            json={"answers": fixture["answers"]},
        ).json()
        finalize_payload = client.post(
            f"/api/v1/scales/sessions/{session_id}/finalize",
            headers=headers,
        ).json()
        result_payload = client.get(
            f"/api/v1/scales/sessions/{session_id}/result",
            headers=headers,
        ).json()

    print(
        json.dumps(
            {
                "list": list_payload,
                "definition": {
                    "scale_id": definition_payload["scale_id"],
                    "question_count": len(definition_payload["questions"]),
                    "definition_version": definition_payload["definition_version"],
                },
                "session": {
                    "session_id": session_id,
                    "status_after_answers": batch_payload["session"]["status"],
                    "status_after_finalize": finalize_payload["session"]["status"],
                },
                "result": result_payload["result"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
