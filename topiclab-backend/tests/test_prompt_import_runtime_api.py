import sys
import types
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import text


def _install_test_shims(monkeypatch):
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
    monkeypatch.setitem(sys.modules, "app.services.content_moderation", fake_moderation)

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
    monkeypatch.setitem(sys.modules, "app.services.oss_upload", fake_oss)


def _register_and_login(client: TestClient, *, phone: str, username: str, password: str = "password123") -> dict:
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
                "phone": phone,
                "code": code,
                "expires_at": datetime.now(timezone.utc) + timedelta(minutes=5),
            },
        )

    response = client.post(
        "/auth/register",
        json={
            "phone": phone,
            "code": code,
            "password": password,
            "username": username,
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_prompt_handoff_runtime_creates_artifact_and_can_cancel(tmp_path, monkeypatch):
    database_path = tmp_path / "portrait_prompt_handoff.sqlite3"
    monkeypatch.setenv("TOPICLAB_TESTING", "1")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database_path}")
    _install_test_shims(monkeypatch)

    import app.storage.database.postgres_client as postgres_client
    import app.api.auth as auth_router
    import app.api.dialogue as dialogue_router
    import app.api.portrait_state as portrait_state_router
    import app.api.prompt_handoff as prompt_handoff_router

    postgres_client.reset_db_state()
    postgres_client.init_auth_tables()

    app = FastAPI()
    app.include_router(auth_router.router, prefix="/auth", tags=["auth"])
    app.include_router(dialogue_router.router, prefix="/api/v1", tags=["portrait-dialogue-v1"])
    app.include_router(portrait_state_router.router, prefix="/api/v1", tags=["portrait-state-v1"])
    app.include_router(prompt_handoff_router.router, prefix="/api/v1", tags=["portrait-prompt-handoffs-v1"])

    with TestClient(app) as client:
        auth = _register_and_login(client, phone="13800072001", username="prompt-handoff-user")
        headers = _auth_headers(auth["token"])

        start = client.post(
            "/api/v1/portrait/dialogue/sessions",
            headers=headers,
            json={"actor_type": "internal", "actor_id": "prompt-handoff-user"},
        )
        assert start.status_code == 200, start.text
        session_id = start.json()["session"]["session_id"]

        send_user = client.post(
            f"/api/v1/portrait/dialogue/sessions/{session_id}/messages",
            headers=headers,
            json={"role": "user", "content_text": "我长期在做科研工作流和 AI agent 基础设施。", "source": "cli", "generate_reply": False},
        )
        assert send_user.status_code == 200, send_user.text

        send_assistant = client.post(
            f"/api/v1/portrait/dialogue/sessions/{session_id}/messages",
            headers=headers,
            json={"role": "assistant", "content_text": "明白，我们先提炼你的研究主线与工作风格。", "source": "runtime", "generate_reply": False},
        )
        assert send_assistant.status_code == 200, send_assistant.text

        state_update = client.post(
            "/api/v1/portrait/state/updates",
            headers=headers,
            json={
                "source_type": "manual",
                "state_patch_json": {"identity": {"focus": "科研工具与 agent 工作流"}},
                "change_summary_json": {"reason": "seed state for handoff"},
            },
        )
        assert state_update.status_code == 200, state_update.text
        portrait_state_id = state_update.json()["current_state"]["portrait_state_id"]

        create = client.post(
            "/api/v1/portrait/prompt-handoffs",
            headers=headers,
            json={
                "dialogue_session_id": session_id,
                "portrait_state_id": portrait_state_id,
                "note_text": "请输出适合粘贴到外部 AI 的综合画像提示词。",
            },
        )
        assert create.status_code == 200, create.text
        payload = create.json()
        handoff_id = payload["handoff"]["handoff_id"]
        assert payload["handoff"]["status"] == "ready"
        assert payload["artifacts"][0]["artifact_type"] == "prompt_text"
        assert "当前画像状态" in payload["artifacts"][0]["content_text"]
        assert "对话记录" in payload["artifacts"][0]["content_text"]

        listed = client.get("/api/v1/portrait/prompt-handoffs", headers=headers)
        assert listed.status_code == 200, listed.text
        assert len(listed.json()["handoffs"]) == 1

        fetched = client.get(f"/api/v1/portrait/prompt-handoffs/{handoff_id}", headers=headers)
        assert fetched.status_code == 200, fetched.text
        assert fetched.json()["handoff"]["handoff_id"] == handoff_id

        cancelled = client.post(f"/api/v1/portrait/prompt-handoffs/{handoff_id}/cancel", headers=headers)
        assert cancelled.status_code == 200, cancelled.text
        assert cancelled.json()["handoff"]["status"] == "cancelled"


def test_import_result_runtime_creates_and_parses_external_output(tmp_path, monkeypatch):
    database_path = tmp_path / "portrait_import_result.sqlite3"
    monkeypatch.setenv("TOPICLAB_TESTING", "1")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database_path}")
    _install_test_shims(monkeypatch)

    import app.storage.database.postgres_client as postgres_client
    import app.api.auth as auth_router
    import app.api.prompt_handoff as prompt_handoff_router
    import app.api.import_results as import_results_router

    postgres_client.reset_db_state()
    postgres_client.init_auth_tables()

    app = FastAPI()
    app.include_router(auth_router.router, prefix="/auth", tags=["auth"])
    app.include_router(prompt_handoff_router.router, prefix="/api/v1", tags=["portrait-prompt-handoffs-v1"])
    app.include_router(import_results_router.router, prefix="/api/v1", tags=["portrait-import-results-v1"])

    with TestClient(app) as client:
        auth = _register_and_login(client, phone="13800072002", username="import-result-user")
        headers = _auth_headers(auth["token"])

        handoff = client.post(
            "/api/v1/portrait/prompt-handoffs",
            headers=headers,
            json={"note_text": "请基于以下背景生成综合画像。"},
        )
        assert handoff.status_code == 200, handoff.text
        handoff_id = handoff.json()["handoff"]["handoff_id"]

        created = client.post(
            "/api/v1/portrait/import-results",
            headers=headers,
            json={
                "handoff_id": handoff_id,
                "source_type": "external_ai_text",
                "payload_text": "# Summary\n你在科研工具和 AI agent 上有长期积累。\n# Open Questions\n还需要确认组织协作风格。",
            },
        )
        assert created.status_code == 200, created.text
        import_id = created.json()["import_result"]["import_id"]
        assert created.json()["import_result"]["status"] == "uploaded"

        parsed = client.post(f"/api/v1/portrait/import-results/{import_id}/parse", headers=headers)
        assert parsed.status_code == 200, parsed.text
        parsed_payload = parsed.json()
        assert parsed_payload["import_result"]["status"] == "parsed"
        assert parsed_payload["parse_run"]["status"] == "parsed"
        assert parsed_payload["auto_applied_to_portrait_state"] is True
        assert parsed_payload["state_update"]["current_state"]["portrait_state_id"].startswith("pst_")
        assert parsed_payload["state_update"]["update"]["source_type"] == "import_result"
        assert parsed_payload["parse_run"]["parsed_output_json"]["parse_kind"] == "text_outline"
        assert parsed_payload["parse_run"]["parsed_output_json"]["candidate_state_patch"]["external_import"]["text_summary"]["line_count"] >= 2

        fetched = client.get(f"/api/v1/portrait/import-results/{import_id}", headers=headers)
        assert fetched.status_code == 200, fetched.text
        assert fetched.json()["latest_parse_run"]["parse_run_id"] == parsed_payload["parse_run"]["parse_run_id"]

        latest = client.get(f"/api/v1/portrait/import-results/{import_id}/parsed", headers=headers)
        assert latest.status_code == 200, latest.text
        assert latest.json()["parse_run"]["parsed_output_json"]["summary"]["has_text"] is True
