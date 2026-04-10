#!/usr/bin/env python3
"""Standalone local smoke for prompt handoff and import-result runtimes."""

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
                "phone": "13800074001",
                "code": code,
                "expires_at": datetime.now(timezone.utc) + timedelta(minutes=5),
            },
        )

    response = client.post(
        "/auth/register",
        json={
            "phone": "13800074001",
            "code": code,
            "password": "password123",
            "username": "prompt-import-smoke",
        },
    )
    response.raise_for_status()
    return response.json()


def main() -> int:
    os.environ["TOPICLAB_TESTING"] = "1"
    database_path = Path(tempfile.mkdtemp(prefix="prompt-import-runtime-smoke-")) / "prompt_import_runtime.sqlite3"
    os.environ["DATABASE_URL"] = f"sqlite:///{database_path}"

    sys.path.insert(0, str(BACKEND_ROOT))
    _install_test_shims()

    import app.storage.database.postgres_client as postgres_client
    import app.api.auth as auth_router
    import app.api.dialogue as dialogue_router
    import app.api.portrait_state as portrait_state_router
    import app.api.prompt_handoff as prompt_handoff_router
    import app.api.import_results as import_results_router

    postgres_client.reset_db_state()
    postgres_client.init_auth_tables()

    app = FastAPI()
    app.include_router(auth_router.router, prefix="/auth", tags=["auth"])
    app.include_router(dialogue_router.router, prefix="/api/v1", tags=["portrait-dialogue-v1"])
    app.include_router(portrait_state_router.router, prefix="/api/v1", tags=["portrait-state-v1"])
    app.include_router(prompt_handoff_router.router, prefix="/api/v1", tags=["portrait-prompt-handoffs-v1"])
    app.include_router(import_results_router.router, prefix="/api/v1", tags=["portrait-import-results-v1"])

    with TestClient(app) as client:
        auth = _register_and_login(client)
        headers = {"Authorization": f"Bearer {auth['token']}"}

        state_update = client.post(
            "/api/v1/portrait/state/updates",
            headers=headers,
            json={
                "source_type": "manual",
                "state_patch_json": {"identity": {"focus": "科研工作流与 AI agent"}},
                "change_summary_json": {"reason": "seed current portrait state"},
            },
        ).json()
        portrait_state_id = state_update["current_state"]["portrait_state_id"]

        handoff = client.post(
            "/api/v1/portrait/prompt-handoffs",
            headers=headers,
            json={
                "portrait_state_id": portrait_state_id,
                "note_text": "请生成适合提交给外部 AI 的综合画像提示词。",
            },
        ).json()
        handoff_id = handoff["handoff"]["handoff_id"]

        imported = client.post(
            "/api/v1/portrait/import-results",
            headers=headers,
            json={
                "handoff_id": handoff_id,
                "source_type": "external_ai_text",
                "payload_text": "# Summary\n你擅长科研工具与 AI agent。\n# Open Questions\n还需补充组织协作风格。",
            },
        ).json()
        import_id = imported["import_result"]["import_id"]

        parsed = client.post(
            f"/api/v1/portrait/import-results/{import_id}/parse",
            headers=headers,
        ).json()

        latest = client.get(
            f"/api/v1/portrait/import-results/{import_id}/parsed",
            headers=headers,
        ).json()

    print(
        json.dumps(
            {
                "portrait_state_id": portrait_state_id,
                "handoff": handoff,
                "import_result": imported,
                "parse_run": parsed["parse_run"],
                "latest_parsed": latest["parse_run"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
