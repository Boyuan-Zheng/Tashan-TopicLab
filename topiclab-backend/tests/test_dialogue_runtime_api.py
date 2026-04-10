import sys
import types
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import text


@pytest.fixture
def client(tmp_path, monkeypatch):
    database_path = tmp_path / "dialogue_runtime.sqlite3"
    monkeypatch.setenv("TOPICLAB_TESTING", "1")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database_path}")

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

    monkeypatch.setattr(
        dialogue_generation_service,
        "generate_assistant_reply",
        fake_generate_assistant_reply,
    )

    postgres_client.reset_db_state()
    postgres_client.init_auth_tables()

    app = FastAPI()
    app.include_router(auth_router.router, prefix="/auth", tags=["auth"])
    app.include_router(dialogue_router.router, prefix="/api/v1", tags=["portrait-dialogue-v1"])

    with TestClient(app) as test_client:
        yield test_client

    postgres_client.reset_db_state()


def register_and_login(client, *, phone: str, username: str, password: str = "password123") -> dict:
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

    register = client.post(
        "/auth/register",
        json={
            "phone": phone,
            "code": code,
            "password": password,
            "username": username,
        },
    )
    assert register.status_code == 200, register.text
    return register.json()


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_dialogue_runtime_closed_loop(client):
    auth = register_and_login(client, phone="13800052001", username="dialogue-user")
    headers = auth_headers(auth["token"])

    start = client.post(
        "/api/v1/portrait/dialogue/sessions",
        headers=headers,
        json={"actor_type": "internal", "actor_id": "fixture:dialogue"},
    )
    assert start.status_code == 200, start.text
    start_payload = start.json()
    session_id = start_payload["session"]["session_id"]
    assert start_payload["session"]["status"] == "initialized"
    assert start_payload["progress"]["message_count"] == 0

    status = client.get(f"/api/v1/portrait/dialogue/sessions/{session_id}", headers=headers)
    assert status.status_code == 200, status.text
    assert status.json()["session"]["session_id"] == session_id

    user_message = client.post(
        f"/api/v1/portrait/dialogue/sessions/{session_id}/messages",
        headers=headers,
        json={"role": "user", "content_text": "我想生成一份科研画像", "source": "cli", "generate_reply": False},
    )
    assert user_message.status_code == 200, user_message.text
    user_payload = user_message.json()
    assert user_payload["session"]["status"] == "in_progress"
    assert user_payload["derived_state"]["has_user_input"] is True
    assert user_payload["accepted_message"]["role"] == "user"

    assistant_message = client.post(
        f"/api/v1/portrait/dialogue/sessions/{session_id}/messages",
        headers=headers,
        json={"role": "assistant", "content_text": "好的，我们先从你的研究背景开始。", "source": "runtime", "generate_reply": False},
    )
    assert assistant_message.status_code == 200, assistant_message.text
    assistant_payload = assistant_message.json()
    assert assistant_payload["derived_state"]["has_assistant_output"] is True

    messages = client.get(f"/api/v1/portrait/dialogue/sessions/{session_id}/messages", headers=headers)
    assert messages.status_code == 200, messages.text
    messages_payload = messages.json()
    assert len(messages_payload["messages"]) == 2
    assert messages_payload["progress"]["user_message_count"] == 1
    assert messages_payload["progress"]["assistant_message_count"] == 1

    derived = client.get(f"/api/v1/portrait/dialogue/sessions/{session_id}/derived-state", headers=headers)
    assert derived.status_code == 200, derived.text
    derived_payload = derived.json()
    assert derived_payload["derived_state"]["message_count"] == 2
    assert derived_payload["derived_state"]["summary"]["last_user_message"] == "我想生成一份科研画像"

    close = client.post(f"/api/v1/portrait/dialogue/sessions/{session_id}/close", headers=headers)
    assert close.status_code == 200, close.text
    close_payload = close.json()
    assert close_payload["session"]["status"] == "closed"


def test_dialogue_append_after_close_returns_machine_readable_error(client):
    auth = register_and_login(client, phone="13800052002", username="dialogue-closed")
    headers = auth_headers(auth["token"])

    start = client.post(
        "/api/v1/portrait/dialogue/sessions",
        headers=headers,
        json={"actor_type": "human"},
    )
    assert start.status_code == 200, start.text
    session_id = start.json()["session"]["session_id"]

    close = client.post(f"/api/v1/portrait/dialogue/sessions/{session_id}/close", headers=headers)
    assert close.status_code == 200, close.text

    response = client.post(
        f"/api/v1/portrait/dialogue/sessions/{session_id}/messages",
        headers=headers,
        json={"role": "user", "content_text": "还能继续吗？", "source": "cli", "generate_reply": False},
    )
    assert response.status_code == 409, response.text
    detail = response.json()["detail"]
    assert detail["code"] == "dialogue_session_closed"


def test_dialogue_user_message_can_trigger_generated_assistant_reply(client):
    auth = register_and_login(client, phone="13800052003", username="dialogue-autogen")
    headers = auth_headers(auth["token"])

    start = client.post(
        "/api/v1/portrait/dialogue/sessions",
        headers=headers,
        json={"actor_type": "internal", "actor_id": "fixture:dialogue-generation"},
    )
    assert start.status_code == 200, start.text
    session_id = start.json()["session"]["session_id"]

    response = client.post(
        f"/api/v1/portrait/dialogue/sessions/{session_id}/messages",
        headers=headers,
        json={"role": "user", "content_text": "我长期做的是计算生物学和科研工具开发。", "source": "cli"},
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["generation_status"] == "completed"
    assert payload["generated_message"]["role"] == "assistant"
    assert payload["generated_message"]["source"] == "runtime"
    assert payload["generated_message"]["model"] == "fake-dialogue-model"
    assert payload["derived_state"]["has_assistant_output"] is True

    messages = client.get(f"/api/v1/portrait/dialogue/sessions/{session_id}/messages", headers=headers)
    assert messages.status_code == 200, messages.text
    messages_payload = messages.json()
    assert len(messages_payload["messages"]) == 2
    assert messages_payload["progress"]["user_message_count"] == 1
    assert messages_payload["progress"]["assistant_message_count"] == 1


def test_dialogue_generation_failure_is_returned_without_losing_user_message(client, monkeypatch):
    auth = register_and_login(client, phone="13800052004", username="dialogue-generation-failure")
    headers = auth_headers(auth["token"])

    start = client.post(
        "/api/v1/portrait/dialogue/sessions",
        headers=headers,
        json={"actor_type": "internal", "actor_id": "fixture:dialogue-generation-failure"},
    )
    assert start.status_code == 200, start.text
    session_id = start.json()["session"]["session_id"]

    from app.portrait.services.dialogue_generation_service import dialogue_generation_service

    async def failing_generate_assistant_reply(messages, derived_state, *, model=None):
        _ = messages, derived_state, model
        raise ValueError("AI_GENERATION_MODEL is not set")

    monkeypatch.setattr(
        dialogue_generation_service,
        "generate_assistant_reply",
        failing_generate_assistant_reply,
    )

    response = client.post(
        f"/api/v1/portrait/dialogue/sessions/{session_id}/messages",
        headers=headers,
        json={"role": "user", "content_text": "我最近主要在做学术写作和工具开发。", "source": "cli"},
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["generation_status"] == "failed"
    assert payload["generation_error"]["code"] == "dialogue_generation_failed"
    assert payload["accepted_message"]["role"] == "user"
    assert payload["derived_state"]["has_user_input"] is True
    assert payload["derived_state"]["has_assistant_output"] is False

    messages = client.get(f"/api/v1/portrait/dialogue/sessions/{session_id}/messages", headers=headers)
    assert messages.status_code == 200, messages.text
    messages_payload = messages.json()
    assert len(messages_payload["messages"]) == 1
    assert messages_payload["messages"][0]["role"] == "user"
