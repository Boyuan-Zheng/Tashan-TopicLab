import json
import sys
import types
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import text


FIXTURES_DIR = Path(__file__).resolve().parents[2] / "scales-runtime" / "fixtures"


@pytest.fixture
def client(tmp_path, monkeypatch):
    database_path = tmp_path / "scales_runtime.sqlite3"
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
    import app.api.scales as scales_router

    postgres_client.reset_db_state()
    postgres_client.init_auth_tables()

    app = FastAPI()
    app.include_router(auth_router.router, prefix="/auth", tags=["auth"])
    app.include_router(scales_router.router, prefix="/api/v1", tags=["scales-v1"])

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


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES_DIR / name).read_text(encoding="utf-8"))


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_scales_list_and_get_definition(client):
    auth = register_and_login(client, phone="13800030001", username="scale-reader")
    headers = auth_headers(auth["token"])

    listing = client.get("/api/v1/scales", headers=headers)
    assert listing.status_code == 200, listing.text
    payload = listing.json()
    assert payload["registry_version"] == "2026-04-10.v1"
    assert [item["scale_id"] for item in payload["list"]] == ["rcss", "mini-ipip", "ams"]

    detail = client.get("/api/v1/scales/rcss", headers=headers)
    assert detail.status_code == 200, detail.text
    definition = detail.json()
    assert definition["scale_id"] == "rcss"
    assert len(definition["questions"]) == 8
    assert definition["derived_metrics"][0]["id"] == "csi"


@pytest.mark.parametrize(
    ("fixture_name", "scale_id", "phone"),
    [
        ("rcss-strong-integration.json", "rcss", "13800041001"),
        ("mini-ipip-reference.json", "mini-ipip", "13800041002"),
        ("ams-autonomous.json", "ams", "13800041003"),
    ],
)
def test_scale_runtime_closed_loop(client, fixture_name: str, scale_id: str, phone: str):
    auth = register_and_login(client, phone=phone, username=f"user-{scale_id}")
    headers = auth_headers(auth["token"])
    fixture = load_fixture(fixture_name)

    start = client.post(
        "/api/v1/scales/sessions",
        headers=headers,
        json={"scale_id": scale_id, "actor_type": "internal", "actor_id": f"fixture:{fixture_name}"},
    )
    assert start.status_code == 200, start.text
    start_payload = start.json()
    session_id = start_payload["session"]["session_id"]
    assert start_payload["session"]["status"] == "initialized"

    answer_items = list(fixture["answers"].items())
    first_question_id, first_value = answer_items[0]
    single = client.post(
        f"/api/v1/scales/sessions/{session_id}/answers",
        headers=headers,
        json={"question_id": first_question_id, "value": first_value},
    )
    assert single.status_code == 200, single.text
    assert single.json()["accepted_answer"]["question_id"] == first_question_id
    assert single.json()["session"]["status"] == "in_progress"

    remaining_answers = {question_id: value for question_id, value in answer_items[1:]}
    batch = client.post(
        f"/api/v1/scales/sessions/{session_id}/answer-batch",
        headers=headers,
        json={"answers": remaining_answers},
    )
    assert batch.status_code == 200, batch.text
    assert batch.json()["session"]["status"] == "ready_to_finalize"
    assert batch.json()["progress"]["remaining_count"] == 0

    finalize = client.post(f"/api/v1/scales/sessions/{session_id}/finalize", headers=headers)
    assert finalize.status_code == 200, finalize.text
    finalized = finalize.json()
    assert finalized["session"]["status"] == "completed"
    assert finalized["result"]["dimension_scores"] == fixture["expected"]["dimension_scores"]
    assert finalized["result"]["derived_scores"] == fixture["expected"]["derived_scores"]

    result = client.get(f"/api/v1/scales/sessions/{session_id}/result", headers=headers)
    assert result.status_code == 200, result.text
    assert result.json()["result"]["dimension_scores"] == fixture["expected"]["dimension_scores"]
    assert result.json()["result"]["derived_scores"] == fixture["expected"]["derived_scores"]

    sessions = client.get("/api/v1/scales/sessions", headers=headers)
    assert sessions.status_code == 200, sessions.text
    assert any(item["session"]["session_id"] == session_id for item in sessions.json()["sessions"])


def test_finalize_incomplete_session_returns_machine_readable_error(client):
    auth = register_and_login(client, phone="13800039999", username="scale-incomplete")
    headers = auth_headers(auth["token"])

    start = client.post(
        "/api/v1/scales/sessions",
        headers=headers,
        json={"scale_id": "rcss", "actor_type": "human"},
    )
    assert start.status_code == 200, start.text
    session_id = start.json()["session"]["session_id"]

    response = client.post(f"/api/v1/scales/sessions/{session_id}/finalize", headers=headers)
    assert response.status_code == 409, response.text
    detail = response.json()["detail"]
    assert detail["code"] == "session_not_ready"
    assert len(detail["missing_question_ids"]) == 8
