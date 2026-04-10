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


def test_portrait_state_runtime_current_is_empty_by_default(tmp_path, monkeypatch):
    database_path = tmp_path / "portrait_state_runtime.sqlite3"
    monkeypatch.setenv("TOPICLAB_TESTING", "1")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database_path}")
    _install_test_shims(monkeypatch)

    import app.storage.database.postgres_client as postgres_client
    import app.api.auth as auth_router
    import app.api.portrait_state as portrait_state_router

    postgres_client.reset_db_state()
    postgres_client.init_auth_tables()

    app = FastAPI()
    app.include_router(auth_router.router, prefix="/auth", tags=["auth"])
    app.include_router(portrait_state_router.router, prefix="/api/v1", tags=["portrait-state-v1"])

    with TestClient(app) as client:
        auth = _register_and_login(client, phone="13800062001", username="portrait-state-empty")
        headers = _auth_headers(auth["token"])

        response = client.get("/api/v1/portrait/state/current", headers=headers)
        assert response.status_code == 200, response.text
        payload = response.json()
        assert payload["current_state"]["portrait_state_id"] is None
        assert payload["current_state"]["state_json"] == {}
        assert payload["version_count"] == 0
        assert payload["update_count"] == 0


def test_portrait_state_runtime_materializes_dialogue_session(tmp_path, monkeypatch):
    database_path = tmp_path / "portrait_state_dialogue.sqlite3"
    monkeypatch.setenv("TOPICLAB_TESTING", "1")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database_path}")
    _install_test_shims(monkeypatch)

    import app.storage.database.postgres_client as postgres_client
    import app.api.auth as auth_router
    import app.api.dialogue as dialogue_router
    import app.api.portrait_state as portrait_state_router
    from app.portrait.services.dialogue_generation_service import dialogue_generation_service

    async def fake_generate_assistant_reply(messages, derived_state, *, model=None):
        _ = messages, derived_state
        return {
            "content": "好的，我们先从你的研究主线和工作风格开始。",
            "model": model or "fake-dialogue-model",
        }

    monkeypatch.setattr(dialogue_generation_service, "generate_assistant_reply", fake_generate_assistant_reply)

    postgres_client.reset_db_state()
    postgres_client.init_auth_tables()

    app = FastAPI()
    app.include_router(auth_router.router, prefix="/auth", tags=["auth"])
    app.include_router(dialogue_router.router, prefix="/api/v1", tags=["portrait-dialogue-v1"])
    app.include_router(portrait_state_router.router, prefix="/api/v1", tags=["portrait-state-v1"])

    with TestClient(app) as client:
        auth = _register_and_login(client, phone="13800062002", username="portrait-state-dialogue")
        headers = _auth_headers(auth["token"])

        start = client.post(
            "/api/v1/portrait/dialogue/sessions",
            headers=headers,
            json={"actor_type": "internal", "actor_id": "portrait-state-dialogue"},
        )
        assert start.status_code == 200, start.text
        session_id = start.json()["session"]["session_id"]

        send = client.post(
            f"/api/v1/portrait/dialogue/sessions/{session_id}/messages",
            headers=headers,
            json={"role": "user", "content_text": "我主要在做科研工具开发和论文写作。", "source": "cli"},
        )
        assert send.status_code == 200, send.text

        update = client.post(
            "/api/v1/portrait/state/updates",
            headers=headers,
            json={"source_type": "dialogue_session", "source_id": session_id},
        )
        assert update.status_code == 200, update.text
        payload = update.json()
        assert payload["current_state"]["portrait_state_id"].startswith("pst_")
        assert payload["update"]["source_type"] == "dialogue_session"
        assert payload["version"]["version_id"].startswith("pvs_")
        assert payload["current_state"]["state_json"]["dialogue"]["latest_session"]["session_id"] == session_id
        assert payload["observation"]["observation_json"]["kind"] == "dialogue_state_materialized"

        current = client.get("/api/v1/portrait/state/current", headers=headers)
        assert current.status_code == 200, current.text
        current_payload = current.json()
        assert current_payload["version_count"] == 1
        assert current_payload["update_count"] == 1

        versions = client.get("/api/v1/portrait/state/versions", headers=headers)
        assert versions.status_code == 200, versions.text
        assert len(versions.json()["versions"]) == 1

        update_read = client.get(f"/api/v1/portrait/state/updates/{payload['update']['update_id']}", headers=headers)
        assert update_read.status_code == 200, update_read.text
        assert update_read.json()["update"]["update_id"] == payload["update"]["update_id"]

        observations = client.get("/api/v1/portrait/state/observations", headers=headers)
        assert observations.status_code == 200, observations.text
        assert len(observations.json()["observations"]) == 1


def test_portrait_state_runtime_materializes_scale_session(tmp_path, monkeypatch):
    database_path = tmp_path / "portrait_state_scale.sqlite3"
    monkeypatch.setenv("TOPICLAB_TESTING", "1")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database_path}")
    _install_test_shims(monkeypatch)

    import app.storage.database.postgres_client as postgres_client
    import app.api.auth as auth_router
    import app.api.scales as scales_router
    import app.api.portrait_state as portrait_state_router

    postgres_client.reset_db_state()
    postgres_client.init_auth_tables()

    app = FastAPI()
    app.include_router(auth_router.router, prefix="/auth", tags=["auth"])
    app.include_router(scales_router.router, prefix="/api/v1", tags=["scales-v1"])
    app.include_router(portrait_state_router.router, prefix="/api/v1", tags=["portrait-state-v1"])

    with TestClient(app) as client:
        auth = _register_and_login(client, phone="13800062003", username="portrait-state-scale")
        headers = _auth_headers(auth["token"])

        start = client.post(
            "/api/v1/scales/sessions",
            headers=headers,
            json={"scale_id": "rcss", "actor_type": "internal", "actor_id": "portrait-state-scale"},
        )
        assert start.status_code == 200, start.text
        session_id = start.json()["session"]["session_id"]

        answer_batch = client.post(
            f"/api/v1/scales/sessions/{session_id}/answer-batch",
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
        )
        assert answer_batch.status_code == 200, answer_batch.text

        finalize = client.post(f"/api/v1/scales/sessions/{session_id}/finalize", headers=headers)
        assert finalize.status_code == 200, finalize.text

        update = client.post(
            "/api/v1/portrait/state/updates",
            headers=headers,
            json={"source_type": "scale_session", "source_id": session_id},
        )
        assert update.status_code == 200, update.text
        payload = update.json()
        assert payload["current_state"]["state_json"]["scales"]["latest_scale_id"] == "rcss"
        assert payload["current_state"]["state_json"]["scales"]["results"]["rcss"]["derived_scores"]["CSI"] == 24.0
        assert payload["observation"]["observation_json"]["kind"] == "scale_result_materialized"

        version = client.get(f"/api/v1/portrait/state/versions/{payload['version']['version_id']}", headers=headers)
        assert version.status_code == 200, version.text
        assert version.json()["version"]["version_id"] == payload["version"]["version_id"]
